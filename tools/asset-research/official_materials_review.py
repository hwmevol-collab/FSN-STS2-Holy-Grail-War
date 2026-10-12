from official_materials import *
from PIL import Image,ImageDraw,ImageFont
ex=readjson(M/'EXTRACTION_RESULTS.json');font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15)
for bid in BOOKS:
    scan=next(r for r in ex if r['book_id']==bid and r['container_copy'] and r['source_id']!='SRC0155');files=sorted([p for p in pathlib.Path(scan['extracted_root']).rglob('*') if p.suffix.lower() in IMAGE_EXT],key=natural)
    for part,selection in [('front',files[:17]),('back',files[-8:])]:
        canvas=Image.new('RGB',(1600,math.ceil(len(selection)/4)*370),'#e8edf2');draw=ImageDraw.Draw(canvas)
        for i,p in enumerate(selection):
            with Image.open(p) as im:im=im.convert('RGB');im.thumbnail((380,338));canvas.paste(im,(i%4*400+(400-im.width)//2,i//4*370))
            draw.text((i%4*400+8,i//4*370+343),p.name,fill='#102338',font=font)
        canvas.save(T/(bid+'_'+part+'.jpg'),quality=90)
    print(bid,files[0].name,files[-1].name)
