from fuc_common import *
from PIL import Image
import concurrent.futures
ROOT=STAGE_ROOT
def extract_tm2():
    rows=readjson(ROOT/'FPK_EXTRACTED_INDEX.json');out=[];failed=[]
    for r in rows:
        if not r['name'].endswith('.ttd') or not r['size']:continue
        raw=pathlib.Path(r['physical_path']).read_bytes();start=0;num=0
        while True:
            offset=raw.find(b'TIM2',start)
            if offset<0:break
            start=offset+4
            try:
                assert offset+64<=len(raw);version,fmt,n=struct.unpack_from('<BBH',raw,offset+4);assert version==4 and fmt in (0,1) and 1<=n<=128
                pos=offset+(128 if fmt==1 else 16);pictures=[]
                for i in range(n):
                    total,pal,img,head,colors,pictype,mip,clut,itype,width,height=struct.unpack_from('<IIIHHBBBBHH',raw,pos)
                    assert total>=head+pal+img and head>=48 and pos+total<=len(raw) and 0<width<=4096 and 0<height<=4096
                    pictures.append(dict(picture_index=i,picture_offset=pos-offset,total_size=total,palette_bytes=pal,image_bytes=img,header_size=head,palette_entries=colors,picture_format=pictype,mip_levels=mip,clut_type=clut,image_type=itype,width=width,height=height));pos+=total
                payload=raw[offset:pos];h=hashlib.sha256(payload).hexdigest();p=ROOT/'TextureRaw'/f'{h}.tm2';p.parent.mkdir(exist_ok=True)
                if not p.exists():p.write_bytes(payload)
                for item in pictures:out.append(dict(parent_container=r['container'],parent_name=r['name'],parent_sha256=r['sha256'],embedded_offset=offset,embedded_index=num,texture_sha256=h,raw_path=str(p),source_status=r['source_status'],swizzle_information='TIM2 format and GS headers retained verbatim; no additional PSP swizzle assumption',**item))
                num+=1;start=pos
            except Exception as e:failed.append(dict(parent_name=r['name'],parent_container=r['container'],offset=offset,error=str(e)))
        if not num:failed.append(dict(parent_name=r['name'],parent_container=r['container'],offset='',error='No validated TIM2 payload found'))
    jsonwrite(ROOT/'TEXTURE_RAW_INDEX.json',out);jsonwrite(ROOT/'TEXTURE_PARSE_FAILURES.json',failed);return out
def convert(row):
    h=row['texture_sha256'];dst=ROOT/'Textures'/f'{h}.png';dst.parent.mkdir(exist_ok=True)
    x=dict(texture_sha256=h,status='FAILED',working_path='')
    try:
        cached=FW/'source_diagnostic/Textures'/f'{h}.png'
        if ROOT!=FW/'source_diagnostic' and cached.exists() and not dst.exists():os.link(cached,dst)
        if not dst.exists():
            p=subprocess.run([str(W/'tools/noesis-fuc/Noesis64.exe'),'?cmode',row['raw_path'],str(dst)],capture_output=True,timeout=45)
            assert p.returncode==0 and dst.is_file(),'Noesis image conversion failed'
        with Image.open(dst) as im:im.load();x.update(status='CONVERTED_PNG',working_path=str(dst),width=im.width,height=im.height,mode=im.mode,alpha='A' in im.getbands(),working_sha256=sha(dst))
    except Exception as e:x['error']=str(e)
    return x
def run():
    rows=extract_tm2();unique={r['texture_sha256']:r for r in rows};done={};log('TIM2 pictures',len(rows),'unique files',len(unique))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for i,x in enumerate(pool.map(convert,unique.values())):
            done[x['texture_sha256']]=x
            if i%100==0:log('Texture conversion',i+1,'/',len(unique))
    index=[dict(r,**{k:v for k,v in done[r['texture_sha256']].items() if k not in r}) for r in rows]
    csvwrite(ROOT/'TEXTURE_INDEX.csv',index);jsonwrite(ROOT/'TEXTURE_INDEX.json',index)
    summary=dict(logical_texture_pictures=len(rows),unique_tim2_files=len(unique),converted_unique_png=sum(x['status']=='CONVERTED_PNG' for x in done.values()),failed_unique_png=sum(x['status']=='FAILED' for x in done.values()),parse_failures=len(readjson(ROOT/'TEXTURE_PARSE_FAILURES.json')),multiple_picture_files=len({r['texture_sha256'] for r in rows if r['picture_index']>0}),status='WORK_ONLY_NOT_INTEGRATED')
    jsonwrite(ROOT/'TEXTURE_SUMMARY.json',summary);log('TEXTURES SUMMARY',summary)
if __name__=='__main__':run()
