from official_materials import *
def relative(p):return pathlib.Path(p).relative_to(R).as_posix()
def run():
    pages=readjl(M/'OFFICIAL_MATERIAL_PAGE_INDEX.jsonl');ocridx={r['page_id']:r for r in readjl(M/'OCR_INDEX.jsonl')};evidence=readjl(M/'TAG_EVIDENCE.jsonl');provenance=readjl(M/'SOURCE_PAGE_PROVENANCE.jsonl');payload=[];ev=collections.defaultdict(list);prov=collections.defaultdict(list)
    for e in evidence:ev[e['page_id']].append(e)
    for e in provenance:prov[e['page_id']].append(e)
    (M/'Pages').mkdir(exist_ok=True)
    vertical={v['page_id']:v for v in readjson(M/'VERTICAL_OCR_RESULTS.json')}
    for p in pages:
        o=ocridx[p['page_id']];text=pathlib.Path(o['normalized_text_path']).read_text(encoding='utf-8');v=vertical.get(p['page_id']);supp=pathlib.Path(v['normalized_text_path']).read_text(encoding='utf-8') if v else '';item={**p,'page_path':relative(p['page_path']),'thumbnail':relative(p['thumbnail']),'ocr_path':relative(o['normalized_text_path']),'raw_ocr_path':relative(o['raw_text_path']),'text':text,'vertical_text':supp,'vertical_ocr_path':relative(v['normalized_text_path']) if v else ''};item['search_text']=' '.join(str(p.get(k,'')) for k in ['page_asset_id','page_id','book_title','printed_page','printed_page_label','section','characters_confirmed','characters_candidate','keywords'])+' '+text+' '+supp;item['search_text']=unicodedata.normalize('NFKC',item['search_text']).lower();payload.append(item);writejson(M/'Pages'/(p['page_id']+'.json'),{'page':p,'ocr':o,'supplemental_vertical_ocr':v,'provenance':prov[p['page_id']],'tag_evidence':ev[p['page_id']]})
    sheets=readjson(M/'CONTACT_SHEETS.json')
    for s in sheets:s['path']=relative(s['path'])
    data={'pages':payload,'sheets':sheets,'toc':readjson(M/'TOC.json'),'aliases':readjson(M/'ALIASES.json')};(R/'catalog.js').write_text('window.OFFICIAL_MATERIALS='+json.dumps(data,ensure_ascii=False)+';',encoding='utf-8')
    template=(W/'scripts/official_materials_browser.html').read_text(encoding='utf-8');(R/'index.html').write_text(template.replace('<!--BASE-->',''),encoding='utf-8');(L/'Gallery/OFFICIAL_MATERIALS.html').write_text(template.replace('<!--BASE-->','<base href="../ReferenceBooks/">'),encoding='utf-8');shutil.copy2(W/'scripts/official_materials_ocr_reader.html',R/'OCR/viewer.html')
    writejson(T/'DESIGN_PLAN.json',{'subject':'FSN official printed references; search-first offline study library','palette':{'ink':'#21384b','muted':'#526778','paper':'#edf2f6','surface':'#ffffff','line':'#bdcad6','accent':'#793d58'},'type':'Georgia display; installed Segoe UI / Yu Gothic UI / Microsoft YaHei; no internet font','layout':'Six actual cover scans identify books; left filters and ordered page grid; full-page sequential viewer','principles':['Covers carry book identity','Scan and printed numbering distinct','Evidence uncertainty remains visible','48 cards; thumbnail lazy loading; full images on deliberate open'],'review_against_brief':'Database marketing hero/CTA recommendation rejected as poor fit. Retained contrast/focus/responsive guidance and designed around actual shelf and scan navigation.'})
    log('GALLERY generated',len(payload),'page records')
if __name__=='__main__':run()
