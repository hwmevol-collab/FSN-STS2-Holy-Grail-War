from common import *
import pefile,io,traceback
from PIL import Image
import imagehash
def run():
    rows=[json.loads(s) for s in (W/'reports/BASE_ASSETS.jsonl').open(encoding='utf-8')];fields=json.loads((W/'reports/CATALOG_FIELDS.json').read_text('utf-8'));new=[];report=[];prepared=[];types={1:'CURSOR',2:'BITMAP',3:'ICON',4:'MENU',5:'DIALOG',6:'STRING',7:'FONTDIR',8:'FONT',9:'ACCELERATOR',10:'RCDATA',11:'MESSAGETABLE',12:'GROUP_CURSOR',14:'GROUP_ICON',16:'VERSION',24:'MANIFEST'}
    for asset in [r for r in rows if r['detected_format']=='PE' and r['source_container']=='Loose']:
        p=pathlib.Path(asset['extracted_path']);count=0;errors=[]
        try:
            pe=pefile.PE(str(p));entries=getattr(getattr(pe,'DIRECTORY_ENTRY_RESOURCE',None),'entries',[])
            for typ in entries:
                typeid=typ.id;name=str(typ.name) if typ.name else types.get(typeid,str(typeid))
                for item in typ.directory.entries:
                    itemname=str(item.name) if item.name else str(item.id)
                    for lang in item.directory.entries:
                        e=lang.data.struct;data=pe.get_data(e.OffsetToData,e.Size);logical=f'{p.name}/{name}/{itemname}/{lang.id}.bin';out=L/asset['source_version']/'RawExtracted/PE'/logical;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(data);digest=hashlib.sha256(data).hexdigest()
                        r={k:'' for k in fields};r.update(asset_id=f'FSN{len(rows)+len(new)+1:06d}',source_version=asset['source_version'],source_container='PE:'+asset['source_logical_path'],source_logical_path=logical,extracted_path=str(out),filename=out.name,extension='.bin',detected_format=signature(data[:64]),category='Icons' if typeid in {1,3,14} else 'Metadata',route='System',locale=str(lang.id),character='unknown',size=len(data),sha256=digest,conversion_status='preserved',notes=f'PE resource type {name}; code page {e.CodePage}; raw payload preserved')
                        cv={'sha256':digest,'detected_format':r['detected_format'],'conversion_status':'preserved','converted_path':''}
                        try:
                            if typeid==3:
                                if data.startswith(b'\x89PNG'):img=Image.open(io.BytesIO(data))
                                else:
                                    width,height=struct.unpack('<ii',data[4:12]);height//=2;planes,bit=struct.unpack('<HH',data[12:16]);ico=struct.pack('<HHH',0,1,1)+struct.pack('<BBBBHHII',width%256,height%256,0,0,planes,bit,len(data),22)+data;img=Image.open(io.BytesIO(ico))
                                img.load();target=L/'Converted/Objects'/(digest+'.png');target.parent.mkdir(parents=True,exist_ok=True);img.convert('RGBA').save(target);thumb=L/'Gallery/thumbnails'/(digest+'.webp');thumb.parent.mkdir(parents=True,exist_ok=True);preview=img.convert('RGBA');preview.thumbnail((240,180));preview.save(thumb,'WEBP',quality=78)
                                cv.update(detected_format='PE_RESOURCE_ICON',conversion_status='converted_png',converted_path=str(target),thumbnail_path=str(thumb),width=img.width,height=img.height,alpha=True,phash=str(imagehash.phash(img)),dhash=str(imagehash.dhash(img)))
                            elif typeid==24:
                                text=data.decode('utf-8-sig').rstrip('\x00');target=L/'Converted/Objects'/(digest+'.txt');target.write_text(text,encoding='utf-8');cv.update(detected_format='MANIFEST_XML',conversion_status='utf8_text',converted_path=str(target),text_encoding='utf-8-sig')
                        except Exception as exc:cv['error']='Resource conversion: '+repr(exc)
                        new.append(r);prepared.append(cv);count+=1
            report.append(dict(file=str(p),machine=pe.FILE_HEADER.Machine,resources=count,resource_types=[str(t.name) if t.name else types.get(t.id,str(t.id)) for t in entries],overlay_offset=pe.get_overlay_data_start_offset(),errors=errors));pe.close()
        except Exception as exc:report.append(dict(file=str(p),resources=count,errors=[repr(exc)]))
        print('PE',p.name,count,flush=True)
    with (W/'reports/BASE_ASSETS.jsonl').open('a',encoding='utf-8') as f:
        for r in new:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    with (W/'reports/PE_CONVERSION_RESULTS.jsonl').open('w',encoding='utf-8') as f:
        for r in prepared:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    jsonwrite(L/'Metadata/PE_RESOURCE_INDEX.json',report);csvwrite(L/'Metadata/PE_RESOURCE_INDEX.csv',[dict(file=r['file'],resources=r['resources'],resource_types=';'.join(r.get('resource_types',[])),overlay_offset=r.get('overlay_offset'),errors=';'.join(r['errors'])) for r in report]);print('PE DONE',len(new),flush=True)
if __name__=='__main__':run()
