from fuc_common import *
from fuc_europe_index import EU
from fuc_europe_integrate import STAGE,append_csv_exact
from PIL import Image,ImageDraw,ImageFont
import html,urllib.parse
def rel(p):return pathlib.Path(p).relative_to(L).as_posix() if p else ''
def run():
    md=EU/'Metadata';marker=md/'GALLERY_COMMIT.json'
    if marker.exists() and os.environ.get('FUC_GALLERY_REGENERATE')!='1':log('Gallery already appended',readjson(marker));return
    assert (md/'INTEGRATION_COMMIT.json').exists();rows=rowsjson(md/'ASSETS.jsonl');g=L/'Gallery';oldjs=(BACK/'Gallery/catalog.js').read_text('utf-8');meta=json.loads(re.search(r'window.FSN_META=(.*?);\s*window.FSN_ASSETS',oldjs,re.S)[1]);before=meta['count']
    for k,f in [('versions','source_version'),('categories','category'),('routes','route'),('containers','source_container'),('formats','detected_format'),('characters','character')]:meta[k]+=sorted({r[f] for r in rows}-set(meta[k]))
    meta['count']=before+len(rows);indexes={k:{v:i for i,v in enumerate(meta[k])} for k in ['versions','categories','routes','containers','formats','characters']};body=oldjs.split('window.FSN_ASSETS=',1)[1].rstrip();assert body.endswith('];');body=body[:-2].rstrip()
    with (STAGE/'catalog.js').open('w',encoding='utf-8') as f:
        f.write('window.FSN_META='+json.dumps(meta,ensure_ascii=False)+';\nwindow.FSN_ASSETS='+body+',\n')
        for i,r in enumerate(rows):
            extra={k:r.get(k,'') for k in ['asset_kind','model_id','mesh_count','bone_count','animation_count','texture_count','metadata_path','animation_id']};extra.update(display_name=r['source_logical_path'].split('/')[-1],metadata_path=rel(extra['metadata_path']) if extra['metadata_path'] else '')
            if r['asset_kind']=='mot_clip':extra['display_name']='motion_'+r['source_logical_path'].split('/')[-1]+' · '+r['source_logical_path'].split('#')[0].split('/')[-1]
            if r['asset_kind']=='embedded_tim2_picture':extra['display_name']='TIM2 '+r['source_logical_path'].split('#')[1]+' · '+r['source_logical_path'].split('#')[0].split('/')[-1]
            a=[r['asset_id'],indexes['versions'][r['source_version']],indexes['containers'][r['source_container']],rel(r['extracted_path']),rel(r['converted_path']),indexes['categories'][r['category']],indexes['routes'][r['route']],indexes['formats'][r['detected_format']],r['width'],r['height'],round(float(r['duration']),3) if r['duration'] else '',pathlib.Path(r['thumbnail_path']).name if r['thumbnail_path'] else '',r['conversion_status'],r['locale'],r['script_mapping'],indexes['characters'][r['character']],r['source_logical_path'],extra]
            f.write(json.dumps(a,ensure_ascii=False,separators=(',',':'))+(',' if i+1<len(rows) else '')+'\n')
        f.write('];')
    page=(BACK/'Gallery/index.html').read_text('utf-8');page=page.replace('Original / REMASTERED / HollowAtaraxia ·','Original / REMASTERED / HollowAtaraxia / FUC Europe ·');page=page.replace('</header>','<a href="../Reports/FUC_INTEGRATION_REPORT.md">FUC Europe 集成报告</a></header>');page=page.replace('const name=a[3].split(\'/\').pop();',"const name=a[17]?.display_name||a[3].split('/').pop();")
    page=page.replace('const working=a[4]||a[3];',"if(a[17]){const d=a[17];if(d.model_id)text(body,'div','meta',`模型 ${d.model_id} · 网格 ${d.mesh_count||0} · 骨骼 ${d.bone_count||0} · 动画 ${d.animation_count||0} · 纹理 ${d.texture_count||0}`);if(d.animation_id)text(body,'div','meta',d.animation_id+' · 通道已解码，骨骼绑定及播放未验证');if(d.metadata_path){const a=document.createElement('a');a.href=pathLink(d.metadata_path);a.textContent='模型与骨骼资料';body.append(a);}}const working=window.FSN_PREVIEWS?.[a[0]]||a[4]||a[3];")
    page=page.replace('<script src="catalog.js"></script>','<script src="catalog.js"></script><script src="preview_map.js"></script>')
    page=page.replace("$('loading').remove();filter();","const initialParams=new URL(location.href).searchParams;if(initialParams.has('asset'))$('query').value=initialParams.get('asset');$('loading').remove();filter();")
    (STAGE/'index.html').write_text(page,encoding='utf-8');preview=g/'preview_map.js'
    if not preview.exists():preview.write_text('window.FSN_PREVIEWS={};',encoding='utf-8')
    groups=collections.defaultdict(list)
    for r in rows:
        if r['thumbnail_path']:groups[(r['source_container'],r['category'])].append(r)
    sheets=[];font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',14);heading=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
    for key,items in sorted(groups.items()):
        digest=hashlib.sha256('|'.join(key).encode()).hexdigest()[:16];folder=g/'contact_sheets/FateUnlimitedCodesPortable_Europe'/digest;folder.mkdir(parents=True,exist_ok=True)
        for n,start in enumerate(range(0,len(items),30),1):
            part=items[start:start+30];target=folder/f'{n:04d}.jpg'
            if not target.exists():
                sheet=Image.new('RGB',(1280,64+math.ceil(len(part)/5)*224),'#f2f3f5');draw=ImageDraw.Draw(sheet);draw.text((18,12),'FUC Europe / '+key[0],font=heading,fill='#151821');draw.text((18,38),f'{key[1]} / Page {n}',font=font,fill='#444')
                for i,r in enumerate(part):
                    x=i%5*256;y=64+i//5*224
                    for bx in range(0,240,16):
                        for by in range(0,176,16):draw.rectangle((x+8+bx,y+by,x+23+bx,y+15+by),fill='#d7dbe1' if (bx//16+by//16)%2 else '#fff')
                    with Image.open(r['thumbnail_path']) as im:im=im.convert('RGBA');im.thumbnail((240,176));sheet.paste(im,(x+8+(240-im.width)//2,y+(176-im.height)//2),im)
                    draw.text((x+8,y+181),r['asset_id'],font=font,fill='#151821');draw.text((x+8,y+201),r['source_logical_path'].split('/')[-1][:25],font=font,fill='#444')
                sheet.save(target,quality=85)
            sheets.append(dict(contact_sheet=str(target),source_version='FateUnlimitedCodesPortable_Europe',container=key[0],route='Unknown',directory=key[1],dimensions='Mixed',page=n,asset_ids=';'.join(r['asset_id'] for r in part)))
    csvwrite(md/'CONTACT_SHEETS.csv',sheets);append_csv_exact(BACK/'Metadata/CONTACT_SHEETS.csv',STAGE/'CONTACT_SHEETS.csv',sheets)
    addition='<section><h2>FateUnlimitedCodesPortable_Europe</h2>'+''.join('<div><a href="'+urllib.parse.quote(pathlib.Path(s['contact_sheet']).relative_to(g).as_posix())+'">'+html.escape(s['container']+' / '+str(s['page']))+'</a></div>' for s in sheets)+'</section>'
    old=(BACK/'Gallery/contact_sheets.html').read_text('utf-8');(STAGE/'contact_sheets.html').write_text(old.replace('</html>',addition+'</html>'),encoding='utf-8')
    for name in ['catalog.js','index.html','contact_sheets.html']:os.replace(STAGE/name,g/name)
    os.replace(STAGE/'CONTACT_SHEETS.csv',L/'Metadata/CONTACT_SHEETS.csv');summary=dict(before=before,added=len(rows),after=meta['count'],old_gallery_array_changes=0,new_contact_sheets=len(sheets),new_image_logical_rows=sum(bool(r['thumbnail_path']) for r in rows),versions=meta['versions'],runtime_browser_verification='PENDING');jsonwrite(marker,summary);log('EUROPE GALLERY',summary)
if __name__=='__main__':run()
