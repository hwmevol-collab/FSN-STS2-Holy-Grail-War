from common import *
from catalog_base import IMAGE,AUDIO,VIDEO
import concurrent.futures,subprocess,io,re,math,traceback,threading
import zlib
from PIL import Image
import imagehash,mutagen
from fcd_decoder import decrypt
FFPROBE='D:/DDplay/ffmpeg/ffprobe.exe'
OUT=L/'Converted/Objects';THUMBS=L/'Gallery/thumbnails';OUT.mkdir(parents=True,exist_ok=True);THUMBS.mkdir(parents=True,exist_ok=True)
TEXT_EXT={'.ks','.tjs','.ksc','.ksd','.last','.txt','.ini','.json','.xml','.csv','.cfg','.conf','.config','.list','.fcf','.sli','.tl','.gut','.vert','.frag','.md5','.log','.dat','.asd'}
def decode_text(data,r):
    ext=r['extension'];ver=r['source_version'];loc=r['locale'];encoding='';note=''
    if data.startswith(b'\xfe\xfe'):
        # GARbro KiriKiri/CryptAlgorithms.cs DecryptScript, upstream commit recorded.
        if len(data)<5 or data[2]>2 or data[3:5]!=b'\xff\xfe':raise ValueError('Unknown KiriKiri text envelope')
        mode=data[2];payload=data[5:]
        if mode==2:
            packed,unpacked=struct.unpack('<QQ',payload[:16]);plain=zlib.decompress(payload[16:])
            if len(plain)!=unpacked:raise ValueError('Compressed KiriKiri text size mismatch')
            return plain.decode('utf-16-le'),'KiriKiri-zlib-UTF16LE','GARbro type 2; decompressed length verified'
        chars=struct.unpack('<'+'H'*(len(payload)//2),payload);out=[]
        for c in chars:
            if mode==1:c=((c&0xaaaa)>>1)|((c&0x5555)<<1);out.append(c)
            elif c>=0x20:out.append(c^(((c&0xfe)<<8)^1))
        plain=struct.pack('<'+'H'*len(out),*out)
        return plain.decode('utf-16-le'),f'KiriKiri-type{mode}-UTF16LE','GARbro decoded copy; raw bytes retained'
    if data[:2] in [b'\xff\xfe',b'\xfe\xff']:return data.decode('utf-16'),'utf-16','BOM'
    if data.startswith(b'\xef\xbb\xbf'):return data.decode('utf-8-sig'),'utf-8-sig','BOM'
    try:return data.decode('utf-8'),'utf-8','Strict UTF-8 validation'
    except UnicodeError:pass
    if b'\x00' in data[:4096]:raise ValueError('Binary content, no trusted text encoding')
    # Locale evidence determines ties among these code pages; never replace undecodable bytes.
    candidates=['cp932','gbk','big5']
    if 'patchtw' in r['source_container'].lower():candidates=['big5','cp932','gbk']
    if 'patchsc' in r['source_container'].lower():candidates=['gbk','cp932','big5']
    if 'patchtc' in r['source_container'].lower():candidates=['big5','cp932','gbk']
    for enc in candidates:
        try:
            text=data.decode(enc)
            if text.encode(enc)==data:return text,enc,'Strict round trip; language review required where ambiguous'
        except UnicodeError:pass
    raise ValueError('No strict round-trip text decoding')
def convert(r):
    digest=r['sha256'];p=pathlib.Path(r['extracted_path']);fmt=r['detected_format'];ext=r['extension'];result={'sha256':digest,'conversion_status':'preserved','converted_path':'','error':''}
    try:
        if fmt in IMAGE:
            working=p
            if fmt=='TLG':working=OUT/(digest+'.png')
            with Image.open(working) as img:
                img.load();alpha='A' in img.getbands() or 'transparency' in img.info
                result.update(width=img.width,height=img.height,alpha=alpha,detected_format=fmt,conversion_status='native_png' if fmt=='PNG' else 'converted_png')
                dst=OUT/(digest+'.png')
                if fmt=='PNG':dst=p
                elif fmt!='TLG' and not dst.exists():img.convert('RGBA' if alpha else 'RGB').save(dst,compress_level=3)
                result['converted_path']=str(dst)
                # Hash the decoded pixels, keeping source-byte hashes separate.
                result['phash']=str(imagehash.phash(img));result['dhash']=str(imagehash.dhash(img))
                thumb=THUMBS/(digest+'.webp')
                if not thumb.exists():
                    preview=img.convert('RGBA');preview.thumbnail((240,180));preview.save(thumb,format='WEBP',quality=78)
                result['thumbnail_path']=str(thumb)
        elif fmt=='FCD':
            data,info=decrypt(p.read_bytes());dst=OUT/(digest+'.ogg')
            if not dst.exists():dst.write_bytes(data)
            result.update(info,converted_path=str(dst),conversion_status='decrypted_ogg',working_sha256=hashlib.sha256(data).hexdigest())
        elif fmt in AUDIO and ext!='.ogv':
            media=mutagen.File(p)
            if media is None:raise ValueError('Audio parser did not recognize stream')
            result.update(duration=media.info.length,sample_rate=getattr(media.info,'sample_rate',''),channels=getattr(media.info,'channels',''),bitrate=getattr(media.info,'bitrate',''),codec=media.__class__.__name__,converted_path=str(p),conversion_status='native_audio')
        elif ext=='.epk':
            result.update(converted_path=r['converted_path'],decrypted_path=r['decrypted_path'],text_encoding=r['text_encoding'],conversion_status=r['conversion_status'],detected_format='EPK_ENCRYPTED')
        elif fmt in VIDEO or ext in {'.ogv','.mpg','.mpeg','.wmv','.avi','.mp4','.mkv','.m4v'}:
            proc=subprocess.run([FFPROBE,'-v','error','-show_format','-show_streams','-of','json',str(p)],capture_output=True,timeout=90)
            if proc.returncode:raise ValueError(proc.stderr.decode('utf-8',errors='replace'))
            data=json.loads(proc.stdout);vs=[s for s in data['streams'] if s['codec_type']=='video'];au=[s for s in data['streams'] if s['codec_type']=='audio']
            result.update(duration=float(data.get('format',{}).get('duration',0)),width=vs[0].get('width','') if vs else '',height=vs[0].get('height','') if vs else '',fps=vs[0].get('avg_frame_rate','') if vs else '',codec=vs[0].get('codec_name','') if vs else '',audio_tracks=len(au),converted_path=str(p),conversion_status='native_video',streams=data['streams'])
        elif fmt.startswith('TEXT') or ext in TEXT_EXT:
            if p.name=='unins000.dat' and p.open('rb').read(24).startswith(b'Inno Setup Uninstall Log'):
                result.update(detected_format='INNO_UNINSTALL_LOG',conversion_status='preserved_installer_metadata');return result
            data=p.read_bytes();text,enc,note=decode_text(data,r)
            # A few root .dat files are version text; all binary root files remain preserved.
            if '\x00' in text and ext!='.fcf':raise ValueError('Decoded text contains NUL')
            if '\x00' in text:note+='; FCF NUL characters preserved in UTF-8 copy'
            dst=OUT/(digest+'.txt')
            if not dst.exists():dst.write_text(text,encoding='utf-8')
            result.update(converted_path=str(dst),text_encoding=enc,conversion_status='utf8_text',detected_format='TEXT',encoding_note=note)
            if ext=='.tl':
                json.loads(text);result['detected_format']='TIMELINE_JSON'
            elif ext=='.gut':result['detected_format']='GUI_XML' if text.lstrip().startswith('<?xml') else 'EMPTY_TEXT'
        elif fmt=='UNKNOWN':result['conversion_status']='unresolved_preserved'
    except Exception as e:
        result.update(conversion_status='failed_preserved',error=repr(e))
    return result
def run():
    rows=[json.loads(s) for s in (W/'reports/BASE_ASSETS.jsonl').open(encoding='utf-8')];groups={}
    for r in rows:groups.setdefault(r['sha256'],r)
    # Decode TLG using the audited upstream decoder before Pillow conversion/validation.
    tlgs=[r for r in groups.values() if r['detected_format']=='TLG' and not (OUT/(r['sha256']+'.png')).exists()]
    if tlgs:
        stage=W/'staging/TLG';stage.mkdir(parents=True,exist_ok=True)
        for r in tlgs:
            p=stage/(r['sha256']+'.tlg')
            if not p.exists():os.link(r['extracted_path'],p)
        cmd=[str(W/'tools/arc_unpacker/arc_unpacker.exe'),'--dec=kirikiri/tlg','--no-recurse','--no-color','-v=1','-t=2','-o='+str(OUT),str(stage)]
        with (W/'logs/TLG_conversion.log').open('w',encoding='utf-8') as f:proc=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,cwd=str(W/'tools/arc_unpacker'))
        jsonwrite(W/'reports/TLG_CONVERSION.json',{'command':subprocess.list2cmdline(cmd),'exit_code':proc.returncode,'input':len(tlgs),'output':sum((OUT/(r['sha256']+'.png')).exists() for r in tlgs)})
        print('TLG',len(tlgs),'exit',proc.returncode,flush=True)
    cache=W/'reports/CONVERSION_RESULTS.jsonl';done={}
    if cache.exists():
        for line in cache.open(encoding='utf-8'):
            r=json.loads(line)
            if r['conversion_status']!='failed_preserved':done[r['sha256']]=r
    work=[r for h,r in groups.items() if h not in done]
    with cache.open('a',encoding='utf-8') as f,concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for i,result in enumerate(pool.map(convert,work)):
            f.write(json.dumps(result,ensure_ascii=False)+'\n')
            if i%500==0:f.flush();print('CONVERT',i+1,'/',len(work),result['conversion_status'],'free GiB',round(shutil.disk_usage('E:/').free/2**30,1),flush=True)
            if shutil.disk_usage('E:/').free<4*2**30:raise RuntimeError('Disk reserve reached; preserve current outputs, reassess estimate')
    print('CONVERT DONE',len(work),flush=True)
if __name__=='__main__':run()
