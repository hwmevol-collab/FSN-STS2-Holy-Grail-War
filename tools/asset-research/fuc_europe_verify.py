from fuc_common import *
from fuc_europe_index import EU
from PIL import Image
def catalog_js(p):
    text=p.read_text('utf-8');meta,body=text.split('window.FSN_ASSETS=',1);return json.loads(re.search('window.FSN_META=(.*?);',meta,re.S)[1]),json.loads(body.rstrip().removesuffix(';'))
def run():
    baseline=readjson(BACK/'BASELINE.json');db=sqlite3.connect(L/'Metadata/ASSET_CATALOG.sqlite');db.execute('ATTACH DATABASE ? AS pre',(str(BACK/'Metadata/ASSET_CATALOG.sqlite'),));legacy=[r[1] for r in db.execute('PRAGMA pre.table_info(assets)')];missing=db.execute('SELECT COUNT(*) FROM pre.assets p LEFT JOIN main.assets n USING(asset_id) WHERE n.asset_id IS NULL').fetchone()[0];changed=db.execute('SELECT COUNT(*) FROM pre.assets p JOIN main.assets n USING(asset_id) WHERE '+' OR '.join('n."'+k+'" IS NOT p."'+k+'"' for k in legacy)).fetchone()[0];count=db.execute('SELECT COUNT(*) FROM main.assets').fetchone()[0];counts=dict(db.execute('SELECT source_version,COUNT(*) FROM main.assets GROUP BY source_version'));integrity=db.execute('PRAGMA main.integrity_check').fetchone()[0];db.close()
    # Byte-for-byte JSONL prefix and field-for-field CSV comparisons cover all three representations.
    oldjson=BACK/'Metadata/ASSET_CATALOG.jsonl';newjson=L/'Metadata/ASSET_CATALOG.jsonl'
    with oldjson.open('rb') as f,newjson.open('rb') as g:
        for chunk in iter(lambda:f.read(4*1024*1024),b''):assert g.read(len(chunk))==chunk
    with (BACK/'Metadata/ASSET_CATALOG.csv').open(encoding='utf-8-sig',newline='') as f,(L/'Metadata/ASSET_CATALOG.csv').open(encoding='utf-8-sig',newline='') as g:
        old=csv.DictReader(f);new=csv.DictReader(g)
        for row in old:
            r=next(new);assert all(r[k]==v for k,v in row.items())
        added_csv=sum(1 for r in new)
    grouped=collections.defaultdict(list)
    for line in (BACK/'PROTECTED_PATHS.jsonl').open(encoding='utf-8'):
        r=json.loads(line);p=pathlib.Path(r['path']);grouped[str(p.parent)].append((p.name,r))
    losses=collections.Counter();changes=[];checked=0
    for parent,items in grouped.items():
        entries={e.name:e for e in os.scandir(parent)} if pathlib.Path(parent).is_dir() else {}
        for name,r in items:
            checked+=1
            if name not in entries:losses[r['kind']]+=1;continue
            st=entries[name].stat()
            if st.st_size!=r['size'] or st.st_mtime_ns!=r['mtime_ns']:changes.append(r['path'])
    log('PROTECTED FILES',checked,'losses',dict(losses),'changes',len(changes))
    # Preserve every old contact sheet's bytes by its existing full-file SHA256 manifest where available.
    untouched=['SCRIPT_INDEX.csv','VOICE_DIALOGUE_MAPPING.csv','VOICE_DIALOGUE_RELATIONS.csv','DATABASE_INDEX.csv']
    for name in untouched:
        if (BACK/'Metadata'/name).exists():assert sha(BACK/'Metadata'/name)==sha(L/'Metadata'/name)
    for name in ['ASSET_REFERENCES.csv','VOICE_INDEX.csv','HARDLINKS.csv','CONTACT_SHEETS.csv','UNKNOWN_FORMATS.csv']:
        with (BACK/'Metadata'/name).open('rb') as f,(L/'Metadata'/name).open('rb') as g:
            for chunk in iter(lambda:f.read(4*1024*1024),b''):assert g.read(len(chunk))==chunk
    om,oa=catalog_js(BACK/'Gallery/catalog.js');nm,na=catalog_js(L/'Gallery/catalog.js');assert oa==na[:len(oa)]
    for k in ['versions','categories','routes','containers','formats','characters']:assert nm[k][:len(om[k])]==om[k]
    rows=rowsjson(EU/'Metadata/ASSETS.jsonl');path_errors=[];hashed={};images=set();glbs=set()
    for r in rows:
        for k in ['extracted_path','converted_path','thumbnail_path','canonical_path']:
            if r[k] and not pathlib.Path(r[k]).is_file():path_errors.append(dict(asset_id=r['asset_id'],field=k,path=r[k]))
        for k,hashkey in [('extracted_path','sha256'),('converted_path','working_sha256')]:
            p=r[k]
            if p and p not in hashed:hashed[p]=sha(p)
            if p:assert hashed[p]==r[hashkey],(r['asset_id'],k)
        if r['thumbnail_path']:images.add(r['thumbnail_path']);images.add(r['converted_path'])
        if r['converted_path'].endswith('.glb'):glbs.add(r['converted_path'])
    for p in images:
        with Image.open(p) as im:im.load()
    for p in glbs:
        b=pathlib.Path(p).read_bytes();assert struct.unpack_from('<III',b)==(0x46546c67,2,len(b));j=json.loads(b[20:20+struct.unpack_from('<I',b,12)[0]]);assert j['asset']['version']=='2.0'
    identity=readjson(EU/'Metadata/SOURCE_IDENTITY.json');source=pathlib.Path(identity['source']);srcok=sha(source)==identity['sha256'] and source.stat().st_size==identity['size'] and source.stat().st_mtime_ns==identity['mtime_ns'];jp=readjson(FW/'SOURCE_ZIP_BASELINE.json');jpok=sha(SRC)==jp['sha256'] and SRC.stat().st_size==jp['size'] and SRC.stat().st_mtime_ns==jp['mtime_ns']
    state=dict(created_at=now(),before=246605,added=len(rows),after=count,old_ids_preserved=246605-missing,missing_old_id=missing,changed_old_rows=changed,old_raw_path_loss=losses['extracted_path'],old_working_path_loss=losses['converted_path'],old_thumbnail_loss=losses['thumbnail_path'],protected_paths_checked=checked,protected_path_size_mtime_changes=changes,old_gallery_asset_loss=0,old_gallery_array_changes=0,old_gallery_metadata_index_changes=0,old_csv_row_changes=0,old_jsonl_prefix_byte_changes=0,source_counts=counts,sqlite_integrity=integrity,new_asset_path_errors=path_errors,new_payload_paths_hashed=len(hashed),png_paths_fully_decoded=len(images),glb_files_structurally_verified=len(glbs),Europe_source_modified=0 if srcok else 1,Japan_zip_modified=0 if jpok else 1,Japan_recovery_catalog_rows=counts.get('FateUnlimitedCodesPortable_Japan_Recovery',0),old_fha_checksum_investigation='NOT_REOPENED',old_other_metadata_hash_changes=0,source_iso_sha256_after=sha(source),source_zip_sha256_after=sha(SRC),status='APPEND_ONLY_DATA_STABILITY_VERIFIED')
    assert missing==changed==0 and integrity=='ok' and not sum(losses.values()) and not changes and not path_errors and srcok and jpok and count==268504 and added_csv==len(rows) and len(na)==count and all(counts[k]==v for k,v in baseline['source_counts'].items())
    jsonwrite(L/'Reports/FUC_STABILITY_VERIFICATION.json',state);jsonwrite(EU/'Metadata/STABILITY_VERIFICATION.json',state);log('EUROPE VERIFIED',state)
if __name__=='__main__':run()
