"""Append-only integration; old rows and Gallery array indexes are immutable.
Build and validate staged indexes from the frozen backup before atomic replacement.
"""
from common import *
from fha_prepare import FHA,FW,BACK
from fha_index import EXTRA
import sqlite3,re,math
STAGE=FW/'integration_stage'
def readcsv(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def append_csv(dest,source,additional):
    dest.parent.mkdir(parents=True,exist_ok=True)
    with source.open(encoding='utf-8-sig',newline='') as src:
        reader=csv.DictReader(src);fields=reader.fieldnames
        with dest.open('w',encoding='utf-8-sig',newline='') as out:
            w=csv.DictWriter(out,fieldnames=fields,extrasaction='ignore');w.writeheader()
            for r in reader:w.writerow(r)
            for r in additional:w.writerow(r)
    return fields
def run():
    marker=FHA/'Metadata/INTEGRATION_COMMIT.json'
    if marker.exists():print('Integration already committed; verify only, no repeated append');return
    new=[json.loads(s) for s in (FHA/'Metadata/ASSETS.jsonl').open(encoding='utf-8')]
    baseline=json.loads((BACK/'BASELINE.json').read_text('utf-8'));maxnum=int(baseline['max_asset_id'][3:]);assert all(r['asset_id']==f'FSN{maxnum+i:06d}' for i,r in enumerate(new,1))
    # No index writer may have modified the real old catalog while FHA was prepared.
    for rel in ['Metadata/ASSET_CATALOG.csv','Metadata/ASSET_CATALOG.jsonl','Metadata/ASSET_CATALOG.sqlite','Gallery/catalog.js','Gallery/index.html']:
        assert sha(L/rel)==sha(BACK/rel),'Unexpected external modification: '+rel
    hardlinks=readcsv(BACK/'Metadata/HARDLINKS.csv');canon={r['sha256']:r['canonical_path'] for r in hardlinks};groups=collections.defaultdict(list)
    for r in new:groups[r['sha256']].append(r)
    added_links=[]
    for i,(h,rs) in enumerate(groups.items()):
        first=rs[0];p=pathlib.Path(first['extracted_path']);target=pathlib.Path(canon[h]) if h in canon else L/'Canonical'/first['category']/(h+(p.suffix if len(p.suffix)<15 else '.bin'))
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():os.link(p,target)
        assert target.stat().st_size==first['size']
        if h not in canon:
            added_links.append(dict(sha256=h,canonical_path=str(target),raw_reference=str(p),method='NTFS hardlink within output library',reference_count=len(rs)));canon[h]=str(target)
        for r in rs:r['canonical_path']=str(target);r['duplicate_group']='SHA256:'+h if len(rs)>1 else ''
        if i%10000==0:print('FHA CANONICAL',i,'/',len(groups),flush=True)
    oldh={r['sha256'] for r in hardlinks}
    for r in new:
        if r['sha256'] in oldh:r['duplicate_group']='SHA256:'+r['sha256']
        if r.get('adler32_verified') is False:r['notes']=(r.get('notes','')+'; CHECKSUM_EXCEPTION: preserved bytes; see extraction evidence').strip('; ')
    STAGE.mkdir(parents=True,exist_ok=True)
    oldfirst=json.loads(next((BACK/'Metadata/ASSET_CATALOG.jsonl').open(encoding='utf-8')));legacy=list(oldfirst);fields=legacy+[k for k in EXTRA if k not in legacy]
    staged=STAGE/'ASSET_CATALOG.jsonl';shutil.copy2(BACK/'Metadata/ASSET_CATALOG.jsonl',staged)
    with staged.open('a',encoding='utf-8') as f:
        for r in new:f.write(json.dumps({k:r.get(k,'') for k in fields},ensure_ascii=False)+'\n')
    with (BACK/'Metadata/ASSET_CATALOG.csv').open(encoding='utf-8-sig',newline='') as src,(STAGE/'ASSET_CATALOG.csv').open('w',encoding='utf-8-sig',newline='') as dst:
        rd=csv.DictReader(src);assert rd.fieldnames==legacy;wr=csv.DictWriter(dst,fieldnames=fields,extrasaction='ignore');wr.writeheader()
        for r in rd:wr.writerow(r)
        for r in new:wr.writerow(r)
    stageddb=STAGE/'ASSET_CATALOG.sqlite';shutil.copy2(BACK/'Metadata/ASSET_CATALOG.sqlite',stageddb);db=sqlite3.connect(stageddb)
    for k in fields:
        if k not in legacy:db.execute('ALTER TABLE assets ADD COLUMN "'+k+'" TEXT')
    db.executemany('INSERT INTO assets ('+','.join('"'+k+'"' for k in fields)+') VALUES ('+','.join('?' for _ in fields)+')',[tuple(int(r.get(k,'')) if isinstance(r.get(k,''),bool) else r.get(k,'') for k in fields) for r in new]);db.commit()
    db.execute('ATTACH DATABASE ? AS pre',(str(BACK/'Metadata/ASSET_CATALOG.sqlite'),));count=db.execute('SELECT COUNT(*) FROM assets').fetchone()[0]
    missing=db.execute('SELECT COUNT(*) FROM pre.assets p LEFT JOIN main.assets n USING(asset_id) WHERE n.asset_id IS NULL').fetchone()[0]
    changed=db.execute('SELECT COUNT(*) FROM pre.assets p JOIN main.assets n USING(asset_id) WHERE '+' OR '.join('n."'+k+'" IS NOT p."'+k+'"' for k in legacy)).fetchone()[0]
    assert missing==0 and changed==0 and count==baseline['total_assets']+len(new)
    assert db.execute('SELECT COUNT(DISTINCT asset_id) FROM assets').fetchone()[0]==count
    assert db.execute('PRAGMA main.integrity_check').fetchone()[0]=='ok';db.close()
    staged_files=['ASSET_CATALOG.csv','ASSET_CATALOG.jsonl','ASSET_CATALOG.sqlite']
    indexes={'ASSET_REFERENCES.csv':'ASSET_REFERENCES.csv','SCRIPT_INDEX.csv':'SCRIPT_INDEX.csv','VOICE_INDEX.csv':'VOICE_INDEX.csv','VOICE_DIALOGUE_MAPPING.csv':'VOICE_DIALOGUE_RELATIONS.csv','DATABASE_INDEX.csv':'DATABASE_INDEX.csv'}
    for dest,source in indexes.items():append_csv(STAGE/dest,BACK/'Metadata'/dest,readcsv(FHA/'Metadata'/source));staged_files.append(dest)
    # A compatible relation alias includes both old FSN and new FHA mappings.
    shutil.copy2(STAGE/'VOICE_DIALOGUE_MAPPING.csv',STAGE/'VOICE_DIALOGUE_RELATIONS.csv');staged_files.append('VOICE_DIALOGUE_RELATIONS.csv')
    append_csv(STAGE/'HARDLINKS.csv',BACK/'Metadata/HARDLINKS.csv',added_links);staged_files.append('HARDLINKS.csv')
    shutil.copy2(FHA/'Metadata/FSN_VS_FHA.csv',STAGE/'FSN_VS_FHA.csv');staged_files.append('FSN_VS_FHA.csv')
    # Unknown rows from existing Remastered stay untouched, with new FHA exceptions appended.
    unknown=[]
    for r in new:
        if r['detected_format']=='UNKNOWN' or r['conversion_status'] in {'unresolved_preserved','failed_preserved'}:
            p=pathlib.Path(r['extracted_path']);b=p.open('rb').read(65536);c=collections.Counter(b);ent=-sum((v/len(b))*math.log2(v/len(b)) for v in c.values()) if b else 0
            unknown.append(dict(file=str(p),path=str(p),asset_id=r['asset_id'],source_container=r['source_container'],size=r['size'],sha256=r['sha256'],first_64_bytes_hex=b[:64].hex(),first_64_bytes=b[:64].hex(),magic=b[:16].hex(),probable_format=r['detected_format'],entropy=ent,status=r['conversion_status'],notes=r.get('error','')))
    csvwrite(FHA/'Metadata/UNKNOWN_FORMATS.csv',unknown,['path','asset_id','source_container','size','sha256','magic','first_64_bytes','entropy','probable_format','status','notes'])
    csvwrite(FHA/'Metadata/UNKNOWN_CLUSTERS.csv',[],['magic','count','bytes','example'])
    append_csv(STAGE/'UNKNOWN_FORMATS.csv',BACK/'Metadata/UNKNOWN_FORMATS.csv',unknown);staged_files.append('UNKNOWN_FORMATS.csv')
    jsonwrite(STAGE/'FHA_SCHEMA_EXTENSION.json',dict(legacy_fields_preserved=legacy,optional_fields_added=EXTRA,missing_old_jsonl_fields='Interpret absent optional FHA fields as empty',source_version='HollowAtaraxia',voice_relations='VOICE_DIALOGUE_MAPPING.csv and compatible VOICE_DIALOGUE_RELATIONS.csv'))
    staged_files.append('FHA_SCHEMA_EXTENSION.json')
    journal=dict(status='STAGED_VALIDATED',created_at=now(),before=baseline['total_assets'],added=len(new),after=count,missing_old_ids=missing,changed_old_rows=changed,files=staged_files)
    jsonwrite(FHA/'Metadata/INTEGRATION_JOURNAL.json',journal)
    # Atomic file replacements occur only after complete staged validation.
    for name in staged_files:os.replace(STAGE/name,L/'Metadata'/name)
    with (FHA/'Metadata/ASSETS.jsonl').open('w',encoding='utf-8') as f:
        for r in new:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    csvwrite(FHA/'Converted/WORKING_COPY_INDEX.csv',[dict(asset_id=r['asset_id'],logical_path=r['source_logical_path'],source_container=r['source_container'],working_path=r['converted_path'],status=r['conversion_status']) for r in new])
    journal.update(status='COMMITTED',completed_at=now(),new_canonical_objects=len(added_links),canonical_payload_physical_growth=0,unknown_formats=len(unknown));jsonwrite(marker,journal)
    print('INTEGRATED',count,'old row changes',changed,'missing',missing,flush=True)
if __name__=='__main__':run()
