from common import *
from fha_prepare import FHA,FW,BACK
import convert_assets as cv
from catalog_base import IMAGE,AUDIO,VIDEO,classify
import concurrent.futures,subprocess,re
import gettext

def convert_fha(r):
    p=pathlib.Path(r['extracted_path']);fmt=r['detected_format'];ext=r['extension'];h=r['sha256']
    if fmt=='KIRIKIRI_ENCRYPTED_TEXT' or ext in {'.po','.kep'}:
        q=dict(r);q['extension']='.txt';return cv.convert(q)
    if ext=='.mo':
        with p.open('rb') as f:g=gettext.GNUTranslations(f)
        dest=cv.OUT/(h+'.json');dest.write_text(json.dumps({str(k):v for k,v in g._catalog.items()},ensure_ascii=False,indent=2),encoding='utf-8')
        return dict(sha256=h,converted_path=str(dest),conversion_status='decoded_gettext',detected_format='GETTEXT_MO',text_encoding='GNU gettext catalog',error='')
    if ext=='.log' and b'\0' in p.open('rb').read(4096):
        # KiriKiri hardware logs mix readable ASCII and binary exception records.
        import base64
        raw=p.read_bytes();strings=re.findall(rb'[\x20-\x7e\r\n\t]{6,}',raw);dest=cv.OUT/(h+'.txt')
        dest.write_text('KiriKiri hardware exception log: readable spans; raw binary retained\n\n'+'\n'.join(s.decode('ascii') for s in strings),encoding='utf-8')
        return dict(sha256=h,converted_path=str(dest),conversion_status='indexed_binary_log',detected_format='KIRIKIRI_EXCEPTION_LOG',text_encoding='ASCII spans',error='')
    if fmt in {'OTF','TTF','TTC'}:return dict(sha256=h,converted_path=str(p),conversion_status='native_font',error='')
    result=cv.convert(r)
    if result['conversion_status']=='native_video' and fmt=='MPEG':
        dst=cv.OUT/(h+'.mp4')
        if not dst.exists():
            cmd=['D:/DDplay/ffmpeg/ffmpeg.exe','-v','error','-nostdin','-i',str(p),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(dst)]
            proc=subprocess.run(cmd,capture_output=True,timeout=900)
            if proc.returncode:raise ValueError(proc.stderr.decode('utf-8','replace'))
        result.update(converted_path=str(dst),conversion_status='converted_browser_video',working_sha256=sha(dst))
    return result
def run():
    rows=[json.loads(s) for s in (FHA/'Metadata/RAW_ASSETS.jsonl').open(encoding='utf-8')]
    old=[json.loads(s) for s in (BACK/'Metadata/ASSET_CATALOG.jsonl').open(encoding='utf-8')]
    fields=list(old[0]);maxid=max(int(r['asset_id'][3:]) for r in old);oldby={}
    for r in old:oldby.setdefault(r['sha256'],r)
    for i,r in enumerate(rows,maxid+1):
        p=pathlib.PurePosixPath(r['source_logical_path']);r.update(asset_id=f'FSN{i:06d}',filename=p.name,extension=p.suffix.lower(),route='Unknown',locale='zh-Hans' if 'chinese' in r['source_container'].lower() else 'Unknown',character='unknown',conversion_status='pending',notes='')
        r['category']=classify(r)
        if '/hanafuda/' in r['source_logical_path'].lower():r['notes']='Mini-game hanafuda path evidence'
        for f in fields:r.setdefault(f,'')
    groups={}
    for r in rows:groups.setdefault(r['sha256'],r)
    tlgs=[r for h,r in groups.items() if r['detected_format']=='TLG' and h not in oldby and not (cv.OUT/(h+'.png')).exists()]
    if tlgs:
        stage=FW/'tlg_batches'/hashlib.sha256(''.join(sorted(r['sha256'] for r in tlgs)).encode()).hexdigest()[:16];stage.mkdir(parents=True,exist_ok=True)
        for r in tlgs:
            p=stage/(r['sha256']+'.tlg')
            if not p.exists():os.link(r['extracted_path'],p)
        cmd=[str(W/'tools/arc_unpacker/arc_unpacker.exe'),'--dec=kirikiri/tlg','--no-recurse','--no-color','-v=1','-t=2','-o='+str(cv.OUT),str(stage)]
        with (FW/'TLG_CONVERSION.log').open('w',encoding='utf-8') as f:proc=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,cwd=W/'tools/arc_unpacker')
        jsonwrite(FHA/'Metadata/TLG_CONVERSION.json',dict(command=subprocess.list2cmdline(cmd),exit_code=proc.returncode,input=len(tlgs),output=sum((cv.OUT/(r['sha256']+'.png')).exists() for r in tlgs)))
        print('FHA TLG',len(tlgs),flush=True)
    results={};cache=FW/'conversion_results.jsonl'
    if cache.exists():results={r['sha256']:r for r in map(json.loads,cache.open(encoding='utf-8')) if r['conversion_status'] not in {'failed_preserved','preserved','unresolved_preserved','native_video'}}
    reused=0
    for h,r in groups.items():
        if h in oldby and oldby[h]['conversion_status'] not in {'failed_preserved','pending','unresolved_preserved'}:
            o=oldby[h];keys=['conversion_status','converted_path','thumbnail_path','width','height','alpha','duration','sample_rate','channels','codec','bitrate','fps','audio_tracks','phash','dhash','text_encoding','decrypted_path','encoding_note']
            results[h]={k:o[k] for k in keys};results[h]['sha256']=h;reused+=1
    work=[r for h,r in groups.items() if h not in results]
    with cache.open('a',encoding='utf-8') as f,concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for i,r in enumerate(pool.map(convert_fha,work)):
            results[r['sha256']]=r;f.write(json.dumps(r,ensure_ascii=False)+'\n')
            if i%500==0:f.flush();print('FHA CONVERT',i+1,'/',len(work),r['conversion_status'],flush=True)
            assert shutil.disk_usage('E:/').free>4*2**30
    for r in rows:
        result=results[r['sha256']];r.update({k:v for k,v in result.items() if k!='sha256' and k!='streams'})
        if r['conversion_status']=='utf8_text' and r['category']=='Unknown':r['category']='Metadata'
        if r['text_encoding'] in {'utf-16','KiriKiri-zlib-UTF16LE','KiriKiri-type1-UTF16LE'} and r['source_container']!='Loose':r['locale']='zh-Hans' if 'language_SChinese' in r['source_container'] or pathlib.Path(r['source_container']).name.startswith('patch') else 'ja'
        if r['extension']=='.fcf':r['category']='Database'
        if r['extension']=='.ksd':r['category']='SaveAssets'
        if r['extension']=='.pdf':r.update(detected_format='PDF',category='Metadata',conversion_status='native_document',converted_path=r['extracted_path'])
        if r['extension']=='.torrent':r.update(detected_format='BITTORRENT_BENCODE',category='Metadata',conversion_status='preserved_metadata',notes='Distribution metadata; all bytes retained')
        if r['extension']=='.sig':r.update(detected_format='XP3_SIGNATURE_SIDECAR',category='Metadata',conversion_status='preserved_metadata',notes='Archive signature sidecar; all bytes retained')
        if r['detected_format']=='PE':r['conversion_status']='native_binary';r['category']='Metadata'
        if r['detected_format']=='XP3':r.update(conversion_status='expanded_container_preserved',category='Metadata',notes='Nested XP3 expanded separately; full original container bytes retained')
        if r['source_container']=='Loose' and r['filename'] in {'language_SChinese.xp3','voice.xp3','voice2.xp3'}:r.update(detected_format='MOLEBOX_NEWDES_QUICKBOX',conversion_status='expanded_container_preserved',category='Metadata',notes='Molebox and nested XP3 expanded with independent integrity checks')
        if r['extension'] in {'.po','.mo'}:r['category']='Database';r['locale']='zh-Hans'
        for f in fields:r.setdefault(f,'')
    with (FHA/'Metadata/ASSETS.jsonl').open('w',encoding='utf-8') as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    csvwrite(FHA/'Converted/WORKING_COPY_INDEX.csv',[dict(asset_id=r['asset_id'],logical_path=r['source_logical_path'],source_container=r['source_container'],working_path=r['converted_path'],status=r['conversion_status']) for r in rows])
    summary=dict(logical_assets=len(rows),unique_payloads=len(groups),exact_duplicate_records=len(rows)-len(groups),reused_existing_payloads=reused,formats=dict(collections.Counter(r['detected_format'] for r in rows)),categories=dict(collections.Counter(r['category'] for r in rows)),conversion_status=dict(collections.Counter(r['conversion_status'] for r in rows)),failures=[{k:r[k] for k in ['asset_id','source_container','source_logical_path','detected_format','error']} for r in rows if r['conversion_status']=='failed_preserved'])
    jsonwrite(FHA/'Metadata/CONVERSION_SUMMARY.json',summary);print('FHA CONVERT DONE',len(rows),summary['conversion_status'],flush=True)
if __name__=='__main__':run()
