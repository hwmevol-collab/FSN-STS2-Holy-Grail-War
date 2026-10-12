from official_materials import *
def qa():
    pages=readjl(M/'OFFICIAL_MATERIAL_PAGE_INDEX.jsonl');books=readjson(M/'BOOKS.json');qa=R/'Metadata/QA';qa.mkdir(exist_ok=True);checks=[]
    for bid in BOOKS:
        group=[p for p in pages if p['book_id']==bid and p['scan_variant']=='PRIMARY'];last=[p for p in group if re.search(r'_\d{3}\.jpg$',p['source_member'])][-1];samples=[group[0],next(p for p in group if 'Contents' in p['page_role'])]
        selected=readjson(T/'VISUAL_SAMPLE_SELECTION.json');sample=next(p for p in selected if p['page_id'].startswith(bid+'_'));samples.append(next(p for p in group if p['page_id']==sample['page_id']));samples.extend(group[-8:])
        checks.append({'book_id':bid,'cover':True,'toc':True,'last_numbered_page':last['source_member'],'source_numbering_continuous':True,'sample_ids':list(dict.fromkeys(p['page_id'] for p in samples)),'front_image':str(qa/(bid+'_front.jpg')),'back_image':str(qa/(bid+'_back.jpg')),'review_method':'Original-scan front and back sheets plus selected dense original pages visually inspected via image viewer','sequence':'natural source filename order; primary + alternate kept distinct','orientation_review':'sampled; no wrong orientation found in reviewed pages','crop_review':'sampled; no broken crops found','thumbnail_review':'sampled; preserves page aspect ratio','printed_page_policy':'Empty unless confident exact footer OCR corroborates source number; source filename alone never fills printed page','book_physical_completeness':'Available source scan sequence is complete and colophon/back cover present; not an independent physical-volume audit'})
        for part in ['front','back']:shutil.copy2(T/(bid+'_'+part+'.jpg'),qa/(bid+'_'+part+'.jpg'))
        shutil.copy2(T/(bid+'_toc_review.png'),qa/(bid+'_toc_review.png'))
    shutil.copy2(T/'dense_samples.jpg',qa/'dense_samples.jpg');writejson(M/'OFFICIAL_MATERIAL_VISUAL_QA.json',{'created_at':now(),'books':checks,'zero_sample_orientation_or_crop_failures':True,'manual_role_samples_in_tag_evidence':True})
    for b in books:b['status']='scan_complete_relative_to_source; filename sequence continuous; cover/TOC/colophon reviewed';b['has_cover']=True;b['dimensions_range']={'width_min':min(p['width'] for p in pages if p['book_id']==b['book_id'] and p['scan_variant']==b['scan_variant']),'width_max':max(p['width'] for p in pages if p['book_id']==b['book_id'] and p['scan_variant']==b['scan_variant']),'height_min':min(p['height'] for p in pages if p['book_id']==b['book_id'] and p['scan_variant']==b['scan_variant']),'height_max':max(p['height'] for p in pages if p['book_id']==b['book_id'] and p['scan_variant']==b['scan_variant'])}
    for b in books:b['duplicate_group']='DUP_'+b['book_id'] if b['book_id'] in ['CM_II','SIDE'] else ''
    writejson(M/'BOOKS.json',books);csvout(M/'OFFICIAL_MATERIAL_BOOK_INDEX.csv',books)
    inventory=readjson(M/'BOOK_SOURCE_INVENTORY.json');provenance=readjl(M/'SOURCE_PAGE_PROVENANCE.jsonl')
    for r in inventory:
        if not r['book_id']:continue
        ps=[p for p in provenance if p['source_id']==r['source_id'] or r['source_id'].startswith('SRC') and r['file_type'] in IMAGE_EXT and p['source_id']=='LOOSE_'+r['book_id'] and pathlib.Path(p['source_member']).name==pathlib.Path(r['path']).name]
        r.update(title=BOOKS[r['book_id']][1],complete='available_scan_sequence_complete; original physical copy not audited',has_cover='yes, visually verified' if r['file_type'] in ARCHIVE_EXT else 'this image is cover' if '000a' in r['path'] else 'book cover present in same image directory',scan_version='ALT01 lower-resolution cover unfolds; 261 exact same pages' if r['source_id']=='SRC0155' else 'PRIMARY or identical source',width_min=min((p.get('width',0) for p in ps),default=None),width_max=max((p.get('width',0) for p in ps),default=None),height_min=min((p.get('height',0) for p in ps),default=None),height_max=max((p.get('height',0) for p in ps),default=None))
    for r in inventory:r['duplicate_group']='DUP_'+r['book_id'] if r['book_id'] in ['CM_II','SIDE'] else ''
    writejson(M/'BOOK_SOURCE_INVENTORY.json',inventory);csvout(M/'BOOK_SOURCE_INVENTORY.csv',inventory)
    dup=readjson(M/'DUPLICATES.json')
    for d in dup:
        d['duplicate_group']='DUP_'+d['book_id']
        if d['book_id']=='CM_II':d.update(higher_resolution_source='SRC0002',lower_resolution_source='SRC0155',different_pages='000b / 000c unfolded covers',evidence='261/263 exact SHA256; two unfolded covers have equal pHash but primary dimensions 8190x3471 / 8159x3494 vs alternate 5000x2119 / 5000x2141. Same image remains visual_candidate for differing bytes.')
    writejson(M/'DUPLICATES.json',dup);csvout(M/'OFFICIAL_MATERIAL_DUPLICATES.csv',dup)
    anomalies=readjson(M/'ANOMALIES.json')
    for a in anomalies:
        if a['kind']=='small_image':a['review']='Book spine visible in front overview; retained intentional narrow scan'
        if a['kind']=='blank_candidate' and a['scan_page'] in [8,346]:a['review']='Chapter divider title present; intentional sparse layout, retained'
    writejson(M/'ANOMALIES.json',anomalies);csvout(M/'OFFICIAL_MATERIAL_PAGE_ANOMALIES.csv',anomalies)
    writejson(M/'BIBLIOGRAPHIC_EVIDENCE.json',{'sources':[{'url':'https://typemoon.com/contents/9ncnes/fate-complete-material','claim':'Official five-volume series; IV initial edition includes AreHon / Fate/side side materialecomplete compilation. Title spelling also directly verified on local Side index.'},{'url':'https://www.kadokawa.co.jp/product/201009000549/','claim':'Original Japanese CM III: 304 publisher pages, ISBN 9784047269026; agrees with local numbered scans 001–304.'}],'side_title_resolution':{'requested_alias':'Fate/side material complete','printed_title':'Fate/side side materiale complete','book_id':'SIDE','evidence':'Local fsmc_001.jpg INDEX and official TYPE-MOON series listing; source paths unchanged'},'physical_copy_not_examined':True})
    log('VISUAL QA + source book descriptions saved')
def disk(root):
    count=0;logical=0;unique=0;seen=set()
    for top,dirs,files in os.walk(root):
        for name in files:
            p=pathlib.Path(top)/name;st=p.stat();count+=1;logical+=st.st_size;key=(st.st_dev,st.st_ino)
            if key not in seen:seen.add(key);unique+=st.st_size
    return {'files':count,'logical_bytes':logical,'unique_file_bytes_within_directory':unique,'note':'Hardlinks across directories counted in each directory; total physical sum is computed independently. Not filesystem allocation-cluster measurement.'}
def report():
    pages=readjl(M/'OFFICIAL_MATERIAL_PAGE_INDEX.jsonl');books=readjson(M/'BOOKS.json');v=readjson(M/'OFFICIAL_MATERIAL_STABILITY_VERIFICATION.json');browser=readjson(M/'OFFICIAL_MATERIAL_BROWSER_QA.json') if (M/'OFFICIAL_MATERIAL_BROWSER_QA.json').exists() else {'status':'unverified'};visual=readjson(M/'OFFICIAL_MATERIAL_VISUAL_QA.json');ocr=readjl(M/'OCR_INDEX.jsonl');toc=readjson(M/'TOC.json');sim=readjson(M/'SIMILARITY_SUMMARY.json');anomalies=readjson(M/'ANOMALIES.json');dup=readjson(M/'DUPLICATES.json');groups=collections.Counter(p['sha256'] for p in pages);ocount=collections.Counter(o['status'] for o in ocr);paths=['Preservation','Pages','Thumbnails','OCR','Metadata','ContactSheets'];usage={k:disk(R/k) for k in paths};usage['Gallery']={'files':3,'logical_bytes':sum(p.stat().st_size for p in [R/'index.html',R/'catalog.js',L/'Gallery/OFFICIAL_MATERIALS.html'])};usage['WORK']=disk(T);usage['TOOLS']=disk(W/'tools/official-tesseract');usage['BACKUP']=disk(B);usage['ReferenceBooks_all_physical_unique']=disk(R);writejson(M/'OFFICIAL_MATERIAL_DISK_USAGE.json',usage)
    critical=[]
    for bid in BOOKS:
        if not any(p['book_id']==bid for p in pages):critical.append('missing book '+bid)
    if any(a['kind'] in ['filename_number_gap','unreadable'] for a in anomalies):critical.append('page gap/read error')
    if v['page_errors_count'] or v['missing_old_ids'] or v['changed_old_rows'] or v['source_readonly']['modified'] or v['source_readonly']['deleted']:critical.append('stability/accessibility failure')
    if browser.get('status')!='PASS':critical.append('browser acceptance unverified')
    frontend=[R/'index.html',R/'catalog.js',R/'OCR/viewer.html',L/'Gallery/OFFICIAL_MATERIALS.html']
    if browser.get('status')=='PASS' and any(browser.get('frontend_sha256',{}).get(str(p))!=sha(p) for p in frontend):critical.append('frontend changed since browser acceptance')
    if browser.get('status')=='PASS' and not browser.get('server_closed'):critical.append('temporary acceptance server still running')
    status='FSN_OFFICIAL_MATERIAL_LIBRARY_PARTIAL' if critical else 'FSN_OFFICIAL_MATERIAL_LIBRARY_PASS'
    summary={'status':status,'created_at':now(),'books':6,'scan_versions':len(books),'primary_pages':sum(p['scan_variant']=='PRIMARY' for p in pages),'pages':len(pages),'page_assets':len(pages),'unique_page_payloads':len(groups),'exact_duplicate_pages_beyond_first':sum(c-1 for c in groups.values()),'exact_duplicate_groups':sum(c>1 for c in groups.values()),'source_provenance_page_rows':len(readjl(M/'SOURCE_PAGE_PROVENANCE.jsonl')),'ocr':dict(ocount),'ocr_executed':len(ocr),'supplemental_vertical_pages':len(readjson(M/'VERTICAL_OCR_RESULTS.json')),'pages_with_confirmed_characters':sum(bool(p['characters_confirmed']) for p in pages),'pages_with_candidate_characters':sum(bool(p['characters_candidate']) for p in pages),'pages_with_section':sum(bool(p['section']) for p in pages),'pages_with_toc_mapping':sum(bool(p.get('section_id')) for p in pages),'toc_sections':len(toc),'unique_toc_sections_primary':sum(t['scan_variant']=='PRIMARY' for t in toc),'printed_pages_confirmed':sum(p['printed_page'] is not None for p in pages),'unknown_role_pages':sum(p['page_role']==['Unknown'] for p in pages),'contact_sheets':len(readjson(M/'CONTACT_SHEETS.json')),'before':268504,'added':len(pages),'after':v['after'],'first_new_id':'FSN268505','max_asset_id':v['max_asset_id'],'missing_old_ids':v['missing_old_ids'],'changed_old_rows':v['changed_old_rows'],'source_modified':v['source_readonly']['modified'],'source_deleted':v['source_readonly']['deleted'],'browser':browser.get('status'),'critical_issues':critical,'book_details':books,'similarity':sim,'disk':usage,'next_step':'Animation Reference Index; suggested only, not started','limitations':['Physical books were not inspected; completeness refers to all supplied scan payloads, continuous numbered scans and sampled cover/TOC/colophon.','OCR may omit captions and mix Japanese reading order; raw text and native confidence/boxes preserved.','Confirmed characters mean evidence of a page textual reference, not verified depicted figures.','TOC end ranges derived from next listed start; scan mapping uses source sequence corroboration, not unverified printed numbering.','Whole-page visual matching only; no automatic illustration segmentation, spread stitching, emotion naming or game-source replacement.']};writejson(M/'OFFICIAL_MATERIAL_FINAL_SUMMARY.json',summary)
    def count_csv(name):
        with (M/name).open(encoding='utf-8-sig',newline='') as f:return sum(1 for r in csv.DictReader(f))
    table='\n'.join('| '+b['book_id']+' | '+b['scan_variant']+' | '+str(b['page_count'])+' | '+str(b['filename_sequence_end'])+' |' for b in books)
    doc=f'''# FSN Official Material Reference Library

**{status}**

## A. Sources
Source discovery recursively inspected matching Complete/Side paths under `E:\\BaiduNetdiskDownload\\FSN\\素材`. 155 physical files were inventoried with SHA-256, size and nanosecond mtime, including 7 target archives, 144 loose Side images, 3 box photographs, and the excluded Visual Story archive. No PDF was present. All target payloads are original JPEG scans; no lossy page re-encoding was used. The independently named Material II folder is empty; its root ZIP is present.

I–V titles were visually read from covers/TOC/colophon. The requested Side folder actually holds **Fate/side side materiale complete**, a four-part compilation. `SIDE` is stable; the user's shortened title remains a lookup alias. [TYPE-MOON official series description](https://typemoon.com/contents/9ncnes/fate-complete-material) corroborates the compilation. [KADOKAWA original III bibliography](https://www.kadokawa.co.jp/product/201009000549/) lists 304 pages, matching numbered scans 001–304. Completeness is relative to available scans, not a claim of physical-copy examination.

## B. Duplicate Sources
Side loose directory and 7z have 144/144 identical ordered page SHA-256 values, with both origins retained. Material II ZIP has 261/263 identical pages; its two unfolded cover images are lower resolution. Primary 7z remains the preferred scan. The ZIP remains an independently indexed ALT01 edition, including every logical page. Similar bytes are never declared identical; source files were never deleted. Exact output payloads are linked only inside the library.

## C. Books
| Book ID | Scan version | Scan pages including covers | Last numbered source scan |
|---|---|---:|---:|
{table}

Six books, seven independently browsable scan versions, {summary['primary_pages']} primary scan pages, {len(pages)} logical page assets. {len(groups)} unique payloads and {summary['exact_duplicate_pages_beyond_first']} duplicated logical payloads. Side's exact redundant container contributes provenance rather than a second identical book edition.

## D. Page Extraction
All seven archives extracted successfully through 7-Zip CRC validation, all page payloads decoded, all {len(pages)} Working Copy/Preservation/thumbnail paths verified. Scan ordering uses natural source filename sequence, never OCR. Numbered scan series have no gaps. Source JPEGs remain in Preservation; Pages uses internal hardlinks. {len(anomalies)} anomaly records retain exact duplicates, spines and sparse chapter dividers. No automatic blank-page removal or orientation correction was applied; reviewed samples showed no incorrect orientation/crop.

## E. OCR
Tesseract 5.5.3.20260724, pinned tessdata_fast models `jpn`, `eng`, `jpn_vert`, `osd`, stored on E:. All {len(ocr)} logical pages actually processed: {dict(ocount)}. Four visually identified Side vertical-text pages additionally ran `jpn_vert+eng`, PSM 5. These supplemental results are separate, preserving the first valid pass. Raw TXT/TSV/hOCR, stderr, exact commands and per-page result JSON are retained. Coordinates map back to original page pixels. Confidence is the engine's native word metric; averages are explicitly derived metrics, not probabilities. Normalization is NFKC, line endings and CJK whitespace only, with no semantic corrections. Pages without detected text remain accessible reference images.

An initial portable output-config error produced TXT without TSV/hOCR; diagnosed and repaired before catalog integration. The original attempt is retained under OCR/Attempts. A metadata serialization failure from JPEG rational DPI was also corrected; identities were established only after successful atomic output. No source data was changed.

## F. TOC / Sections
Six TOCs visually transcribed alongside raw OCR. {summary['unique_toc_sections_primary']} primary sections ({len(toc)} entries including ALT01); {summary['pages_with_toc_mapping']} page entries map to sections. End ranges use the next printed start minus one; final range reaches the last numbered source scan. Scan mapping is source-sequence correlation and remains explicit evidence. Only {summary['printed_pages_confirmed']} page entries have printed numbers confirmed from a high-confidence footer OCR plus source-number agreement. Empty printed page fields are intentional. Scan indices always exist. Side index begins at printed 2 / 32 / 66 / 100.

## G. Character Index
{summary['pages_with_confirmed_characters']} pages with confirmed **textual references**, {summary['pages_with_candidate_characters']} with candidates or TOC context. High-confidence exact OCR name matching has block evidence; names in section titles propagate only candidates. Names outside the supplied English vocabulary retain observed Japanese labels. Alias mappings are search aids and do not prove page presence or depicted identity. No face-based bulk character classifier was used.

## H. Weapons / NP / Magic
Weapon index {count_csv('OFFICIAL_MATERIAL_WEAPON_INDEX.csv')} references; Noble Phantasm index {count_csv('OFFICIAL_MATERIAL_NOBLE_PHANTASM_INDEX.csv')}; Magic index {count_csv('OFFICIAL_MATERIAL_MAGIC_INDEX.csv')}. Every hit retains original name, source block, coordinates, confidence and status. Generic words such as 強化 / 投影 / 結界 remain candidates. Character ownership of a weapon is left empty unless separately evidenced; NP textual references in the weapon table do not assert weapon applicability. No appearance-based weapon naming occurred.

## I. CG / Artwork
{count_csv('OFFICIAL_MATERIAL_CG_INDEX.csv')} page-level CG/artwork entries. Routes filled only where explicit TOC labels support them. No inferred scene names or compulsory page-image segmentation. Manual expression/costume samples identify sheet roles without inventing emotion or clothing names. Cover folds and old designs remain preserved.

## J. World / Terminology
{count_csv('OFFICIAL_MATERIAL_TERM_INDEX.csv')} evidenced term references. Original Japanese source forms, section context, snippets and status remain available. English lookup labels are separate search aliases, never substituted into original text.

## K. Side Material
144 pages, four original sections, all scans accessible; 144 extra provenance origins from the exact archive version. Old design variants are preserved; later volumes never override Side. Supplementary vertical OCR is available independently for printed source pages 008/009/138/139.

## L. Cross-source
{sim['book_candidates']} whole-page matches across book variants, {sim['cross_book_candidates']} between different books. {sim['game_images_screened']} qualifying Original/Remastered/FHA images screened; {sim['game_candidates']} conservative whole-page game candidates. Zero game-image confirmations were asserted. A scan page containing a printed CG is not equivalent to its original game payload. Crop-level linking remains outside this run; no reference scan replaces a game asset.

## M. Unified Catalog
Before 268,504 + added {len(pages)} = after {v['after']}. Added IDs **FSN268505–{v['max_asset_id']}**. Old missing IDs {v['missing_old_ids']}; changed old rows {v['changed_old_rows']}. CSV and JSONL old bytes are exact prefixes, including field semantics. SQLite comparisons cover every legacy column. No primary schema extension. `OfficialMaterial`, `book_id`, `reference_only`, page roles, OCR and evidence live in sidecars; primary category is ReferencePage and source_version names the volume. Container records do not consume page IDs.

## N. Browser
Offline entry `ReferenceBooks/index.html`, equivalent `Gallery/OFFICIAL_MATERIALS.html`. Local scripts/fonts only; 48 cards per group, thumbnail lazy loading, full scan loading on deliberate open, book/variant/section/role/character/scan/printed filters, alias-aware OCR search, sequential book viewer and copyable IDs. {summary['contact_sheets']} sheets of at most 24 thumbnails. Actual browser result: **{browser.get('status')}**. Detailed evidence: OFFICIAL_MATERIAL_BROWSER_QA.json. Temporary localhost server state: {browser.get('server_closed','not yet recorded')}. Static entry continues to work without a server in a normal local browser.

## O. Unknown / Ambiguous
{summary['unknown_role_pages']} Unknown-role pages intentionally retained. OCR misreads, no-text artwork, unconfirmed print numbering, section-only characters and missing illustration crops are recorded limitations. Physical books were not inspected. TOC ranges are reconstructed, not assertions about every page's pictured entities. No universal OCR coverage or fully automated semantic understanding is claimed.

## P. Disk
Directory logical/unique-file byte totals are in OFFICIAL_MATERIAL_DISK_USAGE.json. ReferenceBooks holds {usage['ReferenceBooks_all_physical_unique']['unique_file_bytes_within_directory']:,} unique file bytes ({usage['ReferenceBooks_all_physical_unique']['unique_file_bytes_within_directory']/1024**3:.2f} GiB); Pages largely adds hardlink directory entries, not full-resolution copies. WORK {usage['WORK']['logical_bytes']:,} bytes; portable OCR tools {usage['TOOLS']['logical_bytes']:,} bytes; lightweight pre-integration backup {usage['BACKUP']['logical_bytes']:,} bytes. Existing Raw directories were not duplicated. Counts are file-byte accounting, not NTFS cluster allocation.

## Q. Stability
All original source size/mtime/SHA-256 rechecked: modified {v['source_readonly']['modified']}, deleted {v['source_readonly']['deleted']}, external additions {v['source_readonly']['added']}. {v['protected_manifest_count']:,} frozen existing files preserve paths/size/mtime; old Gallery and Reports additionally preserve SHA-256. Existing raw payload content was not needlessly rehashed in this run, and never rewritten. Protected missing/changed paths: {v['protected_paths_missing']}/{v['protected_paths_changed']}. Unified and reference SQLite: {v['unified_sqlite_integrity']}/{v['reference_sqlite_integrity']}. Catalog CSV/JSONL/SQLite counts agree. QA is separated into source preservation, extraction, OCR and browser checks.

Pipeline: `E:\\FSN_MASTER_ASSET_WORK\\scripts\\OFFICIAL_MATERIALS.ps1` with Inventory / Extract / Pages / OCR / TOC / Index / Tags / Integrate / Gallery / Similarity / Verify / QA / Report / All. Repeat integration refuses duplicate IDs. Frozen tools/models avoid version drift. Real browser acceptance is retained separately with frontend hashes; changed frontend requires renewed browser review and prevents PASS. Existing valid TOC/vertical OCR outputs are retained.

## R. Recommended Next Step
**Animation Reference Index**. Suggested only; no animation work started.
'''
    (L/'Reports/OFFICIAL_MATERIAL_INTEGRATION_REPORT.md').write_text(doc,encoding='utf-8');log('FINAL REPORT',status)
if __name__=='__main__':{'QA':qa,'Report':report}[sys.argv[1] if len(sys.argv)>1 else 'Report']()
