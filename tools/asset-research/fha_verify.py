"""Post-commit preservation/readback audit. Never writes any game source."""
from fha_prepare import *
import concurrent.futures, sqlite3, re, subprocess, time

def readcsv(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def verify_source():
    inventory=json.loads((FHA/'Metadata/SOURCE_INVENTORY.json').read_text('utf-8'))
    expected={r['absolute_path']:r for r in inventory};actual={str(p):p for p in ROOT.rglob('*') if p.is_file()}
    deleted=sorted(set(expected)-set(actual));added=sorted(set(actual)-set(expected));modified=[]
    for p in sorted(set(expected)&set(actual)):
        st=actual[p].stat();r=expected[p];h=sha(actual[p])
        if st.st_size!=r['size'] or st.st_mtime_ns!=r['mtime_ns'] or h!=r['sha256']:modified.append(p)
    source=dict(verified_at=now(),source_files=len(actual),modified_source_files=len(modified),deleted_source_files=len(deleted),added_source_files=len(added),modified=modified,deleted=deleted,added=added,method='Full SHA-256, size, nanosecond mtime against initial inventory')
    jsonwrite(FHA/'Metadata/SOURCE_READ_ONLY_VERIFICATION.json',source);assert not(modified or deleted or added),source
    return source

def prefix_csv(old, new):
    with old.open(encoding='utf-8-sig', newline='') as a, new.open(encoding='utf-8-sig', newline='') as b:
        ra, rb = csv.DictReader(a), csv.DictReader(b)
        assert set(ra.fieldnames) <= set(rb.fieldnames), str(new)
        count=0
        for row in ra:
            other=next(rb, None)
            assert other is not None and all(other[k]==v for k,v in row.items()), (str(new),count)
            count+=1
        return dict(old_rows_preserved=count,added_rows=sum(1 for _ in rb),lost_rows=0)

def run():
    start=time.monotonic();baseline=json.loads((BACK/'BASELINE.json').read_text('utf-8'))
    old=[json.loads(s) for s in (BACK/'Metadata/ASSET_CATALOG.jsonl').open(encoding='utf-8')]
    new=[json.loads(s) for s in (FHA/'Metadata/ASSETS.jsonl').open(encoding='utf-8')]
    db=sqlite3.connect(f'file:{(L/"Metadata/ASSET_CATALOG.sqlite").as_posix()}?mode=ro',uri=True)
    db.execute('ATTACH DATABASE ? AS pre',(str(BACK/'Metadata/ASSET_CATALOG.sqlite'),))
    fields=[r[1] for r in db.execute('PRAGMA pre.table_info(assets)')]
    missing=db.execute('SELECT COUNT(*) FROM pre.assets p LEFT JOIN main.assets n USING(asset_id) WHERE n.asset_id IS NULL').fetchone()[0]
    changed=db.execute('SELECT COUNT(*) FROM pre.assets p JOIN main.assets n USING(asset_id) WHERE '+' OR '.join('n."'+k+'" IS NOT p."'+k+'"' for k in fields)).fetchone()[0]
    counts=dict(db.execute('SELECT source_version,COUNT(*) FROM assets GROUP BY source_version'))
    integrity=db.execute('PRAGMA main.integrity_check').fetchone()[0];db.close()
    assert missing==changed==0 and integrity=='ok'
    assert all(counts[k]==v for k,v in baseline['source_counts'].items())
    assert sum(counts.values())==baseline['total_assets']+len(new)
    # Old JSONL is retained literally, not just reconstructed with equivalent values.
    with (BACK/'Metadata/ASSET_CATALOG.jsonl').open('rb') as a,(L/'Metadata/ASSET_CATALOG.jsonl').open('rb') as b:
        while block:=a.read(8*1024*1024):assert b.read(len(block))==block
    indexes={}
    for name in ['ASSET_CATALOG.csv','ASSET_REFERENCES.csv','SCRIPT_INDEX.csv','VOICE_INDEX.csv','VOICE_DIALOGUE_MAPPING.csv','DATABASE_INDEX.csv','HARDLINKS.csv','UNKNOWN_FORMATS.csv','CONTACT_SHEETS.csv']:
        indexes[name]=prefix_csv(BACK/'Metadata'/name,L/'Metadata'/name)
    oldjs=(BACK/'Gallery/catalog.js').read_text('utf-8');newjs=(L/'Gallery/catalog.js').read_text('utf-8')
    oldarrays=[x.rstrip(',') for x in oldjs.splitlines() if x.startswith('["FSN')]
    newarrays=[x.rstrip(',') for x in newjs.splitlines() if x.startswith('["FSN')]
    assert oldarrays==newarrays[:len(oldarrays)] and len(newarrays)==sum(counts.values())
    oldmeta=baseline['gallery_meta'];newmeta=json.loads(re.search(r'window.FSN_META=(.*?);\s*window.FSN_ASSETS',newjs,re.S)[1])
    for k in ['versions','categories','routes','containers','formats']:assert newmeta[k][:len(oldmeta[k])]==oldmeta[k]
    if '--reuse-readback' in sys.argv:
        result=json.loads((L/'Reports/FHA_STABILITY_VERIFICATION.json').read_text('utf-8'));assert result['status']=='PASS'
        result.update(full_readback_verified_at=result.get('full_readback_verified_at',result['verified_at']),verified_at=now(),indexes=indexes,source_counts=counts,source_read_only=verify_source(),metadata_revision_rechecked=True,readback_reuse_reason='Only FHA semantic index fields and Gallery labels changed since complete payload readback; no media writes')
        jsonwrite(L/'Reports/FHA_STABILITY_VERIFICATION.json',result);print('FHA FINAL METADATA AND SOURCE PASS',flush=True);return
    paths=collections.defaultdict(set);hashes={};conflicts=[]
    for kind,rows in [('old',old),('fha',new)]:
        for r in rows:
            for field in ['extracted_path','converted_path','thumbnail_path','canonical_path','decrypted_path']:
                if r.get(field):paths[kind+'_'+field].add(r[field])
            for field,hfield in [('extracted_path','sha256'),('converted_path','working_sha256')]:
                p,h=r.get(field),r.get(hfield)
                if p and h:
                    if p in hashes and hashes[p]!=h:conflicts.append(p)
                    hashes[p]=h
    for kind,p in [('old_contact_sheets',BACK/'Metadata/CONTACT_SHEETS.csv'),('fha_contact_sheets',FHA/'Metadata/CONTACT_SHEETS.csv')]:
        for r in readcsv(p):paths[kind].add(r['contact_sheet'])
    assert not conflicts,conflicts
    missingpaths={k:[p for p in ps if not pathlib.Path(p).is_file()] for k,ps in paths.items()}
    assert not any(missingpaths.values()),missingpaths
    unique={};size_errors=[]
    for r in old+new:
        if pathlib.Path(r['extracted_path']).stat().st_size!=int(r['size']):size_errors.append(r['asset_id'])
    assert not size_errors,size_errors
    for p,h in hashes.items():
        st=os.stat(p);key=(st.st_dev,st.st_ino)
        if key in unique:assert unique[key][1]==h,(p,h,unique[key])
        else:unique[key]=(p,h,st.st_size,st.st_mtime_ns)
    cache=sqlite3.connect(FW/'READBACK_HASH_CACHE.sqlite');cache.execute('CREATE TABLE IF NOT EXISTS hashes (path TEXT PRIMARY KEY,size INTEGER,mtime INTEGER,sha256 TEXT)')
    cached={p:(size,mtime,h) for p,size,mtime,h in cache.execute('SELECT path,size,mtime,sha256 FROM hashes')};fail=[];pending=[];reused=0
    for p,h,size,mtime in unique.values():
        if cached.get(p)==(size,mtime,h):reused+=1
        else:pending.append((p,h,size,mtime))
    def check(row):
        p,h,size,mtime=row;actual=sha(pathlib.Path(p));return p,size,mtime,actual,h
    print('READBACK unique files',len(unique),'cached',reused,'pending',len(pending),flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for i,(p,size,mtime,actual,expected) in enumerate(pool.map(check,pending),1):
            cache.execute('INSERT OR REPLACE INTO hashes VALUES (?,?,?,?)',(p,size,mtime,actual))
            if actual!=expected:fail.append(dict(path=p,expected=expected,actual=actual))
            if i%10000==0:cache.commit();print('READBACK',i,'/',len(pending),round(time.monotonic()-start,1),'s',flush=True)
    cache.commit();cache.close();assert not fail,fail
    source=verify_source()
    result=dict(verified_at=now(),elapsed_seconds=round(time.monotonic()-start,2),status='PASS',before=baseline['total_assets'],added=len(new),after=sum(counts.values()),source_counts=counts,old_ids=len(old),old_ids_preserved=len(old)-missing,missing_old_ids=missing,changed_old_rows=changed,old_jsonl_literal_prefix_preserved=True,sqlite_integrity=integrity,indexes=indexes,old_gallery_assets_preserved=len(oldarrays),old_gallery_asset_loss=0,old_gallery_array_changes=0,path_counts={k:len(v) for k,v in paths.items()},missing_paths={k:len(v) for k,v in missingpaths.items()},size_errors=0,sha256_readback_unique_file_ids=len(unique),sha256_readback_logical_paths=len(hashes),sha256_errors=len(fail),source_read_only=source)
    jsonwrite(L/'Reports/FHA_STABILITY_VERIFICATION.json',result);print('FHA STABILITY PASS',json.dumps(counts),flush=True)

if __name__=='__main__':run()
