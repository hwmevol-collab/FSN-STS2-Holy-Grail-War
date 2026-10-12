from common import *
from PIL import Image, ImageDraw

# Adapted from pinned krkrz/krkrz visual/PrerenderedFont.{h,cpp}.
# Each glyph retains its code point and original metrics. No outline font is invented.
def decode(data, version, offset, count):
    out=bytearray();pos=offset
    while len(out)<count:
        if pos>=len(data):raise ValueError('Glyph bitmap exceeds source bytes')
        value=data[pos];pos+=1
        if (version==0 and value==0x41) or (version==1 and value>=0x41):
            if not out:raise ValueError('RLE without previous pixel')
            if version==0:
                if pos>=len(data):raise ValueError('Missing RLE length')
                length=data[pos];pos+=1
            else:length=value-0x40
            if len(out)+length>count:raise ValueError('RLE exceeds glyph dimensions')
            out.extend([out[-1]]*length)
        else:
            if value>64:raise ValueError('Unexpected glyph coverage range')
            out.append(value)
    return bytes(round(v*255/64) for v in out),pos-offset

def run():
    rows=[json.loads(s) for s in (W/'reports/BASE_ASSETS.jsonl').open(encoding='utf-8')]
    output=[];updates=[]
    for r in rows:
        if r['extension']!='.tft':continue
        data=pathlib.Path(r['extracted_path']).read_bytes()
        if data[:22]!=b'TVP pre-rendered font\x1a' or data[23]!=2 or data[22] not in (0,1):raise ValueError('Unexpected TFT header')
        version=data[22];count,ch_offset,index_offset=struct.unpack_from('<III',data,24)
        if ch_offset+count*2>len(data) or index_offset+count*20>len(data):raise ValueError('TFT indices out of range')
        root=L/'Converted/FontAtlases'/r['sha256'];root.mkdir(parents=True,exist_ok=True)
        metrics=[];pages=[];atlas=Image.new('RGBA',(2048,2048));x=y=2;rowh=0;page=0
        def save_page():
            dst=root/f'atlas_{page:03d}.png';atlas.save(dst,compress_level=3);pages.append(str(dst))
        for i in range(count):
            cp=struct.unpack_from('<H',data,ch_offset+i*2)[0]
            off,width,height,ox,oy,ix,iy,inc,res=struct.unpack_from('<IHHhhhhhH',data,index_offset+i*20)
            if width>512 or height>512:raise ValueError('Unexpected TFT glyph dimensions')
            raw,packed=decode(data,version,off,width*height)
            if x+width+2>2048:x=2;y+=rowh+2;rowh=0
            if y+height+2>2048:save_page();page+=1;atlas=Image.new('RGBA',(2048,2048));x=y=2;rowh=0
            if width and height:
                glyph=Image.new('RGBA',(width,height),(255,255,255,255));glyph.putalpha(Image.frombytes('L',(width,height),raw));atlas.paste(glyph,(x,y))
            metrics.append(dict(index=i,codepoint=f'U+{cp:04X}',character=chr(cp),source_offset=off,compressed_bytes=packed,width=width,height=height,origin_x=ox,origin_y=oy,inc_x=ix,inc_y=iy,inc=inc,reserved=res,atlas=f'atlas_{page:03d}.png',atlas_x=x,atlas_y=y))
            x+=width+2;rowh=max(rowh,height)
        save_page();csvwrite(root/'GLYPH_METRICS.csv',metrics)
        info=dict(asset_id=r['asset_id'],source=r['extracted_path'],version=version,glyphs=count,pages=pages,metrics=str(root/'GLYPH_METRICS.csv'),method='Pinned KiriKiri RLE; 0..64 coverage expanded to PNG alpha; original byte data retained')
        jsonwrite(root/'FONT_ATLAS.json',info);output.append(info)
        updates.append(dict(sha256=r['sha256'],detected_format='KIRIKIRI_PRERENDERED_FONT',conversion_status='font_atlas_png',converted_path=str(root/'FONT_ATLAS.json'),notes=f'{count} glyphs decoded; PNG atlases and GLYPH_METRICS.csv linked by FONT_ATLAS.json',error=''))
        # A readable sample with common Japanese/Latin glyphs, separate from raw preservation.
        preview=Image.new('RGB',(900,210),'#171c28');draw=ImageDraw.Draw(preview);lookup={m['character']:m for m in metrics}
        for row,text in enumerate(['Fate stay night 0123456789','セイバー 遠坂凛 アーチャー','衛宮士郎 間桐桜 聖杯戦争']):
            px=20
            for char in text:
                m=lookup.get(char)
                if not m:px+=20;continue
                with Image.open(root/m['atlas']) as source:g=source.crop((m['atlas_x'],m['atlas_y'],m['atlas_x']+m['width'],m['atlas_y']+m['height']))
                preview.paste(g,(px,18+row*62),g);px+=max(m['inc'],m['width'],12)+4
        preview.save(root/'PREVIEW.png');print('TFT',r['filename'],'glyphs',count,'pages',len(pages),flush=True)
    with (W/'reports/CONVERSION_RESULTS.jsonl').open('a',encoding='utf-8') as f:
        for r in updates:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    jsonwrite(L/'Reports/TFT_FONT_QA.json',output)
    print('TFT DONE',len(output),flush=True)
if __name__=='__main__':run()
