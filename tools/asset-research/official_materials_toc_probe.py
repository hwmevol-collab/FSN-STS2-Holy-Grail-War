from official_materials import *
from PIL import Image
tools=readjson(W/'tools/official-tesseract/TOOLS_MANIFEST.json');ex=readjson(M/'EXTRACTION_RESULTS.json')
def run(bid):
    saved=R/'OCR/Raw/TOC'/bid
    if saved.with_suffix('.evidence.json').exists() and all(saved.with_suffix('.'+ext).exists() for ext in ['txt','tsv','hocr']):
        return bid,saved.with_suffix('.txt').read_text(encoding='utf-8')
    scan=next(r for r in ex if r['book_id']==bid and r['container_copy'] and r['source_id']!='SRC0155')
    filename='fsmc_001.jpg' if bid=='SIDE' else {'CM_I':'fcm-am_002.jpg','CM_II':'fcm-cm_002.jpg','CM_III':'fcm-wm_002.jpg','CM_IV':'fcm-em_002.jpg','CM_V':'fcm-hm_002.jpg'}[bid]
    p=next(pathlib.Path(scan['extracted_root']).rglob(filename));dest=R/'OCR/Raw/TOC';dest.mkdir(parents=True,exist_ok=True)
    with Image.open(p) as im:
        im=im.convert('RGB');bbox=(0,int(im.height*.50),im.width,im.height) if bid!='SIDE' else (0,0,im.width,im.height);roi=im.crop(bbox);roi.save(T/(bid+'_toc.png'));preview=roi.copy();preview.thumbnail((2000,2000));preview.save(T/(bid+'_toc_review.png'))
    base=dest/bid;cmd=[tools['executable'],str(T/(bid+'_toc.png')),str(base),'--tessdata-dir',tools['tessdata'],'-l','jpn+eng','--oem','1','--psm','6','txt','tsv','hocr'];proc=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',timeout=120)
    writejson(dest/(bid+'.evidence.json'),{'book_id':bid,'source_file':str(p),'roi_original_bbox':bbox,'command':cmd,'exit_code':proc.returncode,'stderr':proc.stderr,'scope':'TOC supplementary OCR; source never changed'})
    return bid,(base.with_suffix('.txt')).read_text(encoding='utf-8')
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    for r in pool.map(run,BOOKS):print(r[0],r[1],flush=True)
