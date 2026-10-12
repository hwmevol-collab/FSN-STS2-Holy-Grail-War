"""Supplemental vertical OCR for visually identified Side vertical text pages."""
from official_materials import *
from PIL import Image
def run():
    if (M/'VERTICAL_OCR_RESULTS.json').exists():log('Supplemental vertical OCR already preserved');return
    pages=readjl(M/'OFFICIAL_MATERIAL_PAGE_INDEX.jsonl');tools=readjson(W/'tools/official-tesseract/TOOLS_MANIFEST.json');raw=R/'OCR/Raw/Vertical';norm=R/'OCR/Normalized/Vertical';raw.mkdir(parents=True,exist_ok=True);norm.mkdir(parents=True,exist_ok=True);results=[];blocks=[]
    for p in pages:
        if p['book_id']!='SIDE' or not any(p['source_member'].endswith('_'+n+'.jpg') for n in ['008','009','138','139']):continue
        pid=p['page_id'];inp=T/(pid+'_vertical.png');base=raw/pid
        with Image.open(p['page_path']) as im:im=im.convert('RGB');orig=im.size;im.thumbnail((2800,2800));size=im.size;im.save(inp)
        cmd=[tools['executable'],str(inp),str(base),'--tessdata-dir',tools['tessdata'],'-l','jpn_vert+eng','--oem','1','--psm','5','txt','tsv','hocr'];proc=subprocess.run(cmd,capture_output=True,encoding='utf-8',errors='replace',timeout=150);text=base.with_suffix('.txt').read_text(encoding='utf-8') if base.with_suffix('.txt').exists() else '';base.with_suffix('.stderr.txt').write_text(proc.stderr,encoding='utf-8');normalized=unicodedata.normalize('NFKC',text);(norm/(pid+'.txt')).write_text(normalized,encoding='utf-8');scale=(orig[0]/size[0],orig[1]/size[1]);words=[]
        with base.with_suffix('.tsv').open(encoding='utf-8',newline='') as f:
            for w in csv.DictReader(f,delimiter='\t'):
                if w['level']=='5' and w['text'].strip():words.append({'page_id':pid,'engine_pass':'vertical_supplemental','x':round(int(w['left'])*scale[0],2),'y':round(int(w['top'])*scale[1],2),'width':round(int(w['width'])*scale[0],2),'height':round(int(w['height'])*scale[1],2),'text':w['text'],'confidence':float(w['conf']),'coordinate_space':'original_page_pixels'})
        result={'page_id':pid,'tool':'Tesseract','language':'jpn_vert+eng','raw_text_path':str(base.with_suffix('.txt')),'raw_tsv_path':str(base.with_suffix('.tsv')),'normalized_text_path':str(norm/(pid+'.txt')),'status':'executed_supplemental' if not proc.returncode else 'failed','command':cmd,'confidence':sum(w['confidence'] for w in words)/len(words) if words else None,'word_count':len(words),'automatic_primary_text_replacement':False,'evidence':'Vertical text columns visually verified on Side 008/009/138/139. Preserve both passes.'};writejson(base.with_suffix('.result.json'),result);results.append(result);blocks.extend(words);inp.unlink()
    writejson(M/'VERTICAL_OCR_RESULTS.json',results);writejl(M/'VERTICAL_OCR_BLOCKS.jsonl',blocks);log('VERTICAL OCR',len(results))
if __name__=='__main__':run()
