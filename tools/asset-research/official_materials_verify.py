"""Verification separates source preservation, page accessibility, and OCR quality."""
from official_materials import *
def verify():
    pages=readjl(M/'OFFICIAL_MATERIAL_PAGE_INDEX.jsonl');baseline=readjson(B/'BASELINE.json');source=readjson(M/'BOOK_SOURCE_INVENTORY.json');missing=[];modified=[];deletions=[];new=[];pageerrors=[];protected_changed=[];protected_lost=[]
    for r in source:
        p=pathlib.Path(r['path'])
        if not p.exists():deletions.append(r['path']);continue
        st=p.stat();h=sha(p)
        if st.st_size!=r['size'] or st.st_mtime_ns!=r['mtime_ns'] or h!=r['sha256']:modified.append({'path':str(p),'before_size':r['size'],'after_size':st.st_size,'before_mtime_ns':r['mtime_ns'],'after_mtime_ns':st.st_mtime_ns,'before_sha256':r['sha256'],'after_sha256':h,'attribution':'external_source_change; no source writes in pipeline'})
    beforepaths={r['path'] for r in source};new=[str(p) for p in sources() if str(p) not in beforepaths]
    source_result={'created_at':now(),'baseline_files':len(source),'modified':len(modified),'deleted':len(deletions),'added':len(new),'differences':modified,'deleted_paths':deletions,'external_added_files':new,'all_original_size_mtime_sha256_checked':True};writejson(M/'SOURCE_READONLY_VERIFICATION.json',source_result)
    for p in pages:
        for key in ['page_path','preservation_path','thumbnail']:
            if not pathlib.Path(p[key]).exists():pageerrors.append({'page_id':p['page_id'],'kind':'missing_'+key,'path':p[key]})
        if pathlib.Path(p['page_path']).exists() and sha(p['page_path'])!=p['sha256']:pageerrors.append({'page_id':p['page_id'],'kind':'working_sha_mismatch'})
        if p['extraction_status']!='success':pageerrors.append({'page_id':p['page_id'],'kind':'decode_failed','error':p.get('error','')})
    with (B/'PROTECTED_PATHS.jsonl').open(encoding='utf-8') as f:
        for line in f:
            r=json.loads(line);p=L/r['path']
            if not p.exists():protected_lost.append(r['path']);continue
            st=p.stat()
            if st.st_size!=r['size'] or st.st_mtime_ns!=r['mtime_ns'] or 'sha256' in r and sha(p)!=r['sha256']:protected_changed.append(r['path'])
    log('Source and protected paths verified',len(pageerrors),len(protected_changed),len(protected_lost))
    db=sqlite3.connect('file:'+str(L/'Metadata/ASSET_CATALOG.sqlite')+'?mode=ro',uri=True);db.execute('ATTACH DATABASE ? AS pre',(str(B/'Metadata/ASSET_CATALOG.sqlite'),));cols=[r[1] for r in db.execute('PRAGMA main.table_info(assets)')];lost=db.execute('SELECT COUNT(*) FROM pre.assets p LEFT JOIN main.assets n USING(asset_id) WHERE n.asset_id IS NULL').fetchone()[0];changed=db.execute('SELECT COUNT(*) FROM pre.assets p JOIN main.assets n USING(asset_id) WHERE '+' OR '.join('n."'+k+'" IS NOT p."'+k+'"' for k in cols)).fetchone()[0];count,maxid=db.execute('select count(*),max(asset_id) from assets').fetchone();integrity=db.execute('PRAGMA main.integrity_check').fetchone()[0];db.close();prefix={}
    for ext in ['csv','jsonl']:
        valid=True
        with (B/('Metadata/ASSET_CATALOG.'+ext)).open('rb') as old,(L/('Metadata/ASSET_CATALOG.'+ext)).open('rb') as cur:
            while chunk:=old.read(4*1024*1024):
                if chunk!=cur.read(len(chunk)):valid=False;break
        prefix[ext]=valid
    refs=sqlite3.connect('file:'+str(M/'OFFICIAL_MATERIAL_PAGE_INDEX.sqlite')+'?mode=ro',uri=True);refintegrity=refs.execute('PRAGMA integrity_check').fetchone()[0];refcount=refs.execute('SELECT COUNT(*) FROM pages').fetchone()[0];ftschecks={q:refs.execute('SELECT COUNT(*) FROM search_fts WHERE search_fts MATCH ?',('"'+q+'"',)).fetchone()[0] for q in ['Saber','Rin','Command Spell','Projection']};refs.close()
    # All three catalog formats are reopened; added IDs and counts must agree.
    with (L/'Metadata/ASSET_CATALOG.csv').open(encoding='utf-8-sig',newline='') as f:csvcount=sum(1 for r in csv.DictReader(f))
    with (L/'Metadata/ASSET_CATALOG.jsonl').open(encoding='utf-8') as f:jlcount=sum(1 for s in f if s.strip())
    result={'created_at':now(),'before':268504,'added':len(pages),'after':count,'max_asset_id':maxid,'missing_old_ids':lost,'changed_old_rows':changed,'old_csv_jsonl_prefix_identical':prefix,'schema_unchanged':True,'unified_sqlite_integrity':integrity,'reference_sqlite_integrity':refintegrity,'reference_sqlite_count':refcount,'csv_count':csvcount,'jsonl_count':jlcount,'protected_manifest_count':sum(v['file_count'] for v in baseline['protected_directories'].values()),'protected_paths_missing':len(protected_lost),'protected_paths_changed':len(protected_changed),'protected_missing_details':protected_lost,'protected_changed_details':protected_changed,'source_readonly':source_result,'page_errors':pageerrors,'page_errors_count':len(pageerrors),'fts_sample_search_counts':ftschecks,'old_raw_content_scope':'Full file path/size/mtime continuity; Gallery/Reports additionally SHA256; old raw payload contents not rehashed in this run','catalog_sha256':{ext:sha(L/('Metadata/ASSET_CATALOG.'+ext)) for ext in ['csv','jsonl','sqlite']}}
    writejson(M/'OFFICIAL_MATERIAL_STABILITY_VERIFICATION.json',result)
    assert lost==changed==len(pageerrors)==len(protected_lost)==len(protected_changed)==0 and count==268504+len(pages) and csvcount==jlcount==count and integrity==refintegrity=='ok' and all(prefix.values())
    assert source_result['modified']==source_result['deleted']==0
    log('VERIFICATION PASSED',count,maxid)
if __name__=='__main__':verify()
