from official_materials import *
from PIL import Image,ImageDraw,ImageFont
rows=readjl(M/'OFFICIAL_MATERIAL_PAGE_INDEX.jsonl');selection={'CM_I':[241,264,4],'CM_II':[5,255,6],'CM_III':[20,135,5],'CM_IV':[6,339,12],'CM_V':[12,342,5],'SIDE':[5,8,6]};font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20);records=[]
for bid,nums in selection.items():
    canvas=Image.new('RGB',(1800,1060),'#edf2f6');draw=ImageDraw.Draw(canvas)
    for i,num in enumerate(nums):
        p=next(p for p in rows if p['book_id']==bid and p['scan_variant']=='PRIMARY' and p.get('filename_page_hint')==num)
        with Image.open(p['page_path']) as im:im=im.convert('RGB');im.thumbnail((580,995));canvas.paste(im,(i*600+(600-im.width)//2,0))
        draw.text((i*600+10,1005),p['page_id']+' / source '+str(num),font=font,fill='#21384b')
        records.append({'book_id':bid,'page_id':p['page_id'],'sample_scope':['character/design reference','dense text','dense images'][i],'role_limit':'I artwork / III character profile are nearest character references; no standalone design sheet asserted' if bid in ['CM_I','CM_III'] and i==0 else ''})
    canvas.save(M/'QA'/(bid+'_role_samples.jpg'),quality=94)
writejson(M/'QA/ADDITIONAL_VISUAL_SAMPLES.json',records)
