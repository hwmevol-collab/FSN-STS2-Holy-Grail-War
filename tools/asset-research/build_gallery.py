from common import *
from PIL import Image,ImageDraw,ImageFont
import math,re,urllib.parse
def rel(p):return pathlib.Path(p).relative_to(L).as_posix() if p else ''
def build():
    rows=[json.loads(s) for s in (L/'Metadata/ASSET_CATALOG.jsonl').open(encoding='utf-8')];gallery=L/'Gallery';groupdir=gallery/'contact_sheets';groupdir.mkdir(parents=True,exist_ok=True)
    versions=['Original','Remastered'];cats=sorted(set(r['category'] for r in rows));routes=sorted(set(r['route'] for r in rows));containers=sorted(set(r['source_container'] for r in rows));formats=sorted(set(r['detected_format'] for r in rows));status=collections.Counter(r['conversion_status'] for r in rows)
    # Compact arrays and local <script src> work with file:// without a server or fetch/CORS.
    with (gallery/'catalog.js').open('w',encoding='utf-8') as f:
        f.write('window.FSN_META='+json.dumps({'versions':versions,'categories':cats,'routes':routes,'containers':containers,'formats':formats,'count':len(rows)},ensure_ascii=False)+';\nwindow.FSN_ASSETS=[\n')
        for i,r in enumerate(rows):
            value=[r['asset_id'],versions.index(r['source_version']),containers.index(r['source_container']),rel(r['extracted_path']),rel(r['converted_path']),cats.index(r['category']),routes.index(r['route']),formats.index(r['detected_format']),r['width'],r['height'],round(float(r['duration']),2) if r['duration'] else '',pathlib.Path(r['thumbnail_path']).name if r['thumbnail_path'] else '',r['conversion_status'],r['locale'],r['script_mapping']]
            f.write(json.dumps(value,ensure_ascii=False,separators=(',',':'))+(',' if i+1<len(rows) else '')+'\n')
        f.write('];')
    shutil.copy2(W/'scripts/gallery.html',gallery/'index.html')
    groups=collections.defaultdict(list)
    for r in rows:
        if not r['thumbnail_path']:continue
        key=(r['source_version'],r['source_container'],r['route'],str(pathlib.PurePosixPath(r['source_logical_path']).parent),f"{r['width']}x{r['height']}")
        groups[key].append(r)
    try:font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',14);titlefont=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',19)
    except OSError:font=titlefont=ImageFont.load_default()
    sheet_rows=[];n=0
    for key,items in sorted(groups.items()):
        folder=groupdir/key[0]/re.sub(r'[^a-zA-Z0-9_.-]','_',key[1].replace('/','__'));folder.mkdir(parents=True,exist_ok=True)
        for page,start in enumerate(range(0,len(items),30),1):
            part=items[start:start+30];digest=hashlib.sha256('|'.join(key).encode('utf-8')).hexdigest()[:12];target=folder/(digest+f'_{page:04d}.jpg')
            if not target.exists():
                sheet=Image.new('RGB',(1280,64+math.ceil(len(part)/5)*224),'#f2f3f5');draw=ImageDraw.Draw(sheet);draw.text((18,12),' / '.join(key)[:150],font=titlefont,fill='#151821');draw.text((18,38),f'Page {page} · {start+1}–{start+len(part)} / {len(items)}',font=font,fill='#444b55')
                for i,r in enumerate(part):
                    x=(i%5)*256;y=64+(i//5)*224
                    # Checkerboard keeps transparent artwork visible without flattening working PNGs.
                    for bx in range(0,240,16):
                        for by in range(0,176,16):draw.rectangle((x+8+bx,y+by,x+8+bx+15,y+by+15),fill='#d7dbe1' if (bx//16+by//16)%2 else '#ffffff')
                    with Image.open(r['thumbnail_path']) as img:
                        img=img.convert('RGBA');img.thumbnail((240,176));sheet.paste(img,(x+8+(240-img.width)//2,y+(176-img.height)//2),img)
                    draw.text((x+8,y+181),r['asset_id'],font=font,fill='#151821');draw.text((x+8,y+200),r['filename'][:25],font=font,fill='#444b55')
                sheet.save(target,quality=85)
            sheet_rows.append(dict(contact_sheet=str(target),source_version=key[0],container=key[1],route=key[2],directory=key[3],dimensions=key[4],page=page,asset_ids=';'.join(r['asset_id'] for r in part)))
            n+=1
            if n%100==0:print('CONTACT_SHEETS',n,flush=True)
    csvwrite(L/'Metadata/CONTACT_SHEETS.csv',sheet_rows)
    lines=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>FSN Contact Sheets</title><style>body{font:16px system-ui;max-width:1200px;margin:30px auto}img{max-width:100%;height:auto}summary{cursor:pointer;padding:10px}a{color:#164e9c}</style><h1>FSN Contact Sheets</h1><p>每张图标注资产编号和文件名。完整筛选请打开 <a href="index.html">素材浏览器</a>。</p>']
    import html
    for k,items in __import__('itertools').groupby(sheet_rows,key=lambda r:(r['source_version'],r['container'])):
        lines.append('<details><summary>'+html.escape(' / '.join(k))+'</summary>')
        for r in items:
            href=urllib.parse.quote(pathlib.Path(r['contact_sheet']).relative_to(gallery).as_posix());lines.append('<div><a href="'+href+'">'+html.escape(r['route']+' / '+r['directory']+' / '+r['dimensions']+' / '+str(r['page']))+'</a></div>')
        lines.append('</details>')
    lines.append('</html>');(gallery/'contact_sheets.html').write_text('\n'.join(lines),encoding='utf-8')
    jsonwrite(W/'reports/GALLERY_SUMMARY.json',{'logical_images':sum(bool(r['thumbnail_path']) for r in rows),'unique_thumbnails':len({r['thumbnail_path'] for r in rows if r['thumbnail_path']}),'contact_sheets':len(sheet_rows),'groups':len(groups),'catalog_js_bytes':(gallery/'catalog.js').stat().st_size})
    print('GALLERY DONE',len(sheet_rows),flush=True)
if __name__=='__main__':build()
