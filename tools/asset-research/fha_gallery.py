"""FHA-only contact sheets and appended compact Gallery catalog."""
from common import *
from fha_prepare import FHA,FW,BACK
from fha_integrate import append_csv,STAGE
from build_gallery import rel
from PIL import Image,ImageDraw,ImageFont
import math,re,html,urllib.parse,itertools
def run():
    marker=FHA/'Metadata/GALLERY_COMMIT.json'
    if marker.exists():print('Gallery already committed; no duplicate append');return
    rows=[json.loads(s) for s in (FHA/'Metadata/ASSETS.jsonl').open(encoding='utf-8')];g=L/'Gallery'
    oldjs=(BACK/'Gallery/catalog.js').read_text('utf-8');prefix=re.search(r'window.FSN_META=(.*?);\s*window.FSN_ASSETS',oldjs,re.S);meta=json.loads(prefix[1]);oldcount=meta['count']
    for k,field in [('versions','source_version'),('categories','category'),('routes','route'),('containers','source_container'),('formats','detected_format')]:
        meta[k]+=sorted({r[field] for r in rows}-set(meta[k]))
    meta['characters']=sorted({'unknown'}|{r['character'] for r in rows});meta['count']=oldcount+len(rows)
    indexes={k:{v:i for i,v in enumerate(meta[k])} for k in ('versions','categories','routes','containers','formats','characters')}
    body=oldjs[oldjs.index('window.FSN_ASSETS=')+len('window.FSN_ASSETS='):];assert body.rstrip().endswith('];');body=body.rstrip()[:-2].rstrip();assert not body.endswith(',')
    STAGE.mkdir(parents=True,exist_ok=True)
    with (STAGE/'catalog.js').open('w',encoding='utf-8') as f:
        f.write('window.FSN_META='+json.dumps(meta,ensure_ascii=False)+';\nwindow.FSN_ASSETS='+body+',\n')
        for i,r in enumerate(rows):
            a=[r['asset_id'],indexes['versions'][r['source_version']],indexes['containers'][r['source_container']],rel(r['extracted_path']),rel(r['converted_path']),indexes['categories'][r['category']],indexes['routes'][r['route']],indexes['formats'][r['detected_format']],r['width'],r['height'],round(float(r['duration']),2) if r['duration'] else '',pathlib.Path(r['thumbnail_path']).name if r['thumbnail_path'] else '',r['conversion_status'],r['locale'],r['script_mapping'],indexes['characters'][r['character']],' / '.join(x for x in [r.get('scene'),r.get('day'),r.get('time_slot')] if x)]
            f.write(json.dumps(a,ensure_ascii=False,separators=(',',':'))+(',' if i+1<len(rows) else '')+'\n')
        f.write('];')
    # Existing compact arrays must remain byte-identical (apart from a final delimiter).
    oldarrays=[s.rstrip(',') for s in oldjs.splitlines() if s.startswith('["FSN')]
    arrays=[s.rstrip(',') for s in (STAGE/'catalog.js').read_text('utf-8').splitlines() if s.startswith('["FSN')]
    assert arrays[:oldcount]==oldarrays and len(arrays)==meta['count']
    page=(BACK/'Gallery/index.html').read_text('utf-8')
    page=page.replace('原版与 REMASTERED ·','Original / REMASTERED / HollowAtaraxia ·')
    page=page.replace('</header>','<a href="../Reports/FHA_INTEGRATION_REPORT.md">FHA 集成报告</a></header>',1)
    page=page.replace('<div><label for="category">','<div><label for="character">人物</label><select id="character"></select></div><div><label for="category">',1)
    page=page.replace("['format',7]","['format',7],['character',15]")
    page=page.replace("a[col]===Number(v)","(a[col]??(col===15?M.characters.indexOf('unknown'):a[col]))===Number(v)")
    page=page.replace("a[0]+' '+a[3]+' '+a[14]","a[0]+' '+a[3]+' '+a[14]+' '+(a[15]!=null?M.characters[a[15]]:'')+' '+(a[16]||'')")
    page=page.replace("(ogg|wav|mp3|flac)","(ogg|opus|wav|mp3|flac)")
    page=page.replace("options('version',M.versions);","options('version',M.versions);options('character',M.characters);")
    page=page.replace("'container','resolution','minwidth'","'container','character','resolution','minwidth'")
    page=page.replace("const working=a[4]||a[3];","if(a[15]!=null&&M.characters[a[15]]!=='unknown')text(body,'div','meta',M.characters[a[15]]);if(a[16])text(body,'div','meta',a[16]);const working=a[4]||a[3];")
    (STAGE/'index.html').write_text(page,encoding='utf-8')
    groups=collections.defaultdict(list)
    for r in rows:
        if r['thumbnail_path']:
            k=('HollowAtaraxia',r['source_container'],r['route'],str(pathlib.PurePosixPath(r['source_logical_path']).parent),f"{r['width']}x{r['height']}");groups[k].append(r)
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',14);titlefont=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',19);sheets=[]
    for key,items in sorted(groups.items()):
        folder=g/'contact_sheets/HollowAtaraxia'/re.sub(r'[^a-zA-Z0-9_.-]','_',key[1].replace('/','__'));folder.mkdir(parents=True,exist_ok=True)
        for n,start in enumerate(range(0,len(items),30),1):
            part=items[start:start+30];digest=hashlib.sha256('|'.join(key).encode()).hexdigest()[:12];target=folder/(digest+f'_{n:04d}.jpg')
            if not target.exists():
                sheet=Image.new('RGB',(1280,64+math.ceil(len(part)/5)*224),'#f2f3f5');draw=ImageDraw.Draw(sheet);draw.text((18,12),' / '.join(key)[:150],font=titlefont,fill='#151821');draw.text((18,38),f'Page {n} · {start+1}–{start+len(part)} / {len(items)}',font=font,fill='#444b55')
                for i,r in enumerate(part):
                    x=(i%5)*256;y=64+(i//5)*224
                    for bx in range(0,240,16):
                        for by in range(0,176,16):draw.rectangle((x+8+bx,y+by,x+8+bx+15,y+by+15),fill='#d7dbe1' if (bx//16+by//16)%2 else '#fff')
                    with Image.open(r['thumbnail_path']) as img:
                        img=img.convert('RGBA');img.thumbnail((240,176));sheet.paste(img,(x+8+(240-img.width)//2,y+(176-img.height)//2),img)
                    draw.text((x+8,y+181),r['asset_id'],font=font,fill='#151821');draw.text((x+8,y+200),r['filename'][:25],font=font,fill='#444b55')
                sheet.save(target,quality=85)
            sheets.append(dict(contact_sheet=str(target),source_version='HollowAtaraxia',container=key[1],route=key[2],directory=key[3],dimensions=key[4],page=n,asset_ids=';'.join(r['asset_id'] for r in part)))
            if len(sheets)%300==0:print('FHA CONTACT SHEETS',len(sheets),flush=True)
    csvwrite(FHA/'Metadata/CONTACT_SHEETS.csv',sheets);append_csv(STAGE/'CONTACT_SHEETS.csv',BACK/'Metadata/CONTACT_SHEETS.csv',sheets)
    oldhtml=(BACK/'Gallery/contact_sheets.html').read_text('utf-8');addition=[]
    for k,rs in itertools.groupby(sheets,key=lambda r:r['container']):
        addition.append('<details><summary>HollowAtaraxia / '+html.escape(k)+'</summary>')
        for r in rs:
            href=urllib.parse.quote(pathlib.Path(r['contact_sheet']).relative_to(g).as_posix());addition.append('<div><a href="'+href+'">'+html.escape(r['route']+' / '+r['directory']+' / '+r['dimensions']+' / '+str(r['page']))+'</a></div>')
        addition.append('</details>')
    (STAGE/'contact_sheets.html').write_text(oldhtml.replace('</html>','\n'.join(addition)+'\n</html>'),encoding='utf-8')
    for name in ('catalog.js','index.html','contact_sheets.html'):os.replace(STAGE/name,g/name)
    os.replace(STAGE/'CONTACT_SHEETS.csv',L/'Metadata/CONTACT_SHEETS.csv')
    oldthumbs=set()
    for s in (BACK/'Metadata/ASSET_CATALOG.jsonl').open(encoding='utf-8'):
        r=json.loads(s)
        if r['thumbnail_path']:oldthumbs.add(r['thumbnail_path'])
    summary=dict(before=oldcount,added=len(rows),after=meta['count'],old_gallery_array_changes=0,new_contact_sheets=len(sheets),new_unique_thumbnails=len({r['thumbnail_path'] for r in rows if r['thumbnail_path']}-oldthumbs),logical_images=sum(bool(r['thumbnail_path']) for r in rows),catalog_js_bytes=(g/'catalog.js').stat().st_size,character_filter=True,opus_playback=True,completed_at=now())
    jsonwrite(marker,summary);print('FHA GALLERY DONE',summary,flush=True)
if __name__=='__main__':run()
