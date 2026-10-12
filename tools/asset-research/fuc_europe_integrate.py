from fuc_common import *
from fuc_europe_index import EU,EXTRA
STAGE=FW/'Europe/integration_stage'
def append_csv_exact(src,dst,rows):
    shutil.copy2(src,dst)
    with src.open(encoding='utf-8-sig',newline='') as f:fields=next(csv.reader(f))
    with dst.open('a',encoding='utf-8',newline='') as f:csv.DictWriter(f,fieldnames=fields,extrasaction='ignore').writerows(rows)
def run():
    md=EU/'Metadata';marker=md/'INTEGRATION_COMMIT.json'
    if marker.exists():log('Already integrated; no duplicate IDs',readjson(marker));return
    new=rowsjson(md/'ASSETS.jsonl');baseline=readjson(BACK/'BASELINE.json');assert baseline['total_assets']==246605
    assert all(r['asset_id']==f'FSN{246605+i:06d}' and r['source_version']=='FateUnlimitedCodesPortable_Europe' for i,r in enumerate(new,1))
    for rel in ['Metadata/ASSET_CATALOG.csv','Metadata/ASSET_CATALOG.jsonl','Metadata/ASSET_CATALOG.sqlite','Gallery/catalog.js','Gallery/index.html']:assert sha(L/rel)==sha(BACK/rel),'Unexpected existing catalog change '+rel
    STAGE.mkdir(parents=True,exist_ok=True)
    oldlinks=readrows(BACK/'Metadata/HARDLINKS.csv');canon={r['sha256']:r['canonical_path'] for r in oldlinks};oldhashes=set(canon);newlinks=[];groups=collections.defaultdict(list)
    for r in new:groups[r['sha256']].append(r)
    for h,rs in groups.items():
        first=rs[0];source=pathlib.Path(first['extracted_path']);target=pathlib.Path(canon[h]) if h in canon else L/'Canonical/FateUnlimitedCodesPortable_Europe'/(h+(source.suffix if len(source.suffix)<15 else '.bin'))
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():os.link(source,target)
        assert target.stat().st_size==first['size']
        if h not in canon:newlinks.append(dict(sha256=h,canonical_path=str(target),raw_reference=str(source),method='NTFS hardlink within output library',reference_count=len(rs)));canon[h]=str(target)
        for r in rs:r['canonical_path']=str(target);r['duplicate_group']='SHA256:'+h if len(rs)>1 or h in oldhashes else ''
    with (BACK/'Metadata/ASSET_CATALOG.csv').open(encoding='utf-8-sig',newline='') as f:legacy=next(csv.reader(f))
    fields=legacy+[k for k in EXTRA if k not in legacy]
    shutil.copy2(BACK/'Metadata/ASSET_CATALOG.jsonl',STAGE/'ASSET_CATALOG.jsonl')
    with (STAGE/'ASSET_CATALOG.jsonl').open('a',encoding='utf-8') as f:
        for r in new:f.write(json.dumps({k:r.get(k,'') for k in fields},ensure_ascii=False)+'\n')
    with (BACK/'Metadata/ASSET_CATALOG.csv').open(encoding='utf-8-sig',newline='') as f,(STAGE/'ASSET_CATALOG.csv').open('w',encoding='utf-8-sig',newline='') as out:
        rd=csv.DictReader(f);wr=csv.DictWriter(out,fieldnames=fields,extrasaction='ignore');wr.writeheader()
        for r in rd:wr.writerow(r)
        for r in new:wr.writerow(r)
    stageddb=STAGE/'ASSET_CATALOG.sqlite';shutil.copy2(BACK/'Metadata/ASSET_CATALOG.sqlite',stageddb);db=sqlite3.connect(stageddb)
    for k in fields:
        if k not in legacy:db.execute('ALTER TABLE assets ADD COLUMN "'+k+'" TEXT')
    db.executemany('INSERT INTO assets ('+','.join('"'+k+'"' for k in fields)+') VALUES ('+','.join('?' for k in fields)+')',[tuple(int(r.get(k,'')) if isinstance(r.get(k,''),bool) else r.get(k,'') for k in fields) for r in new]);db.commit()
    db.execute('ATTACH DATABASE ? AS pre',(str(BACK/'Metadata/ASSET_CATALOG.sqlite'),));missing=db.execute('SELECT COUNT(*) FROM pre.assets p LEFT JOIN main.assets n USING(asset_id) WHERE n.asset_id IS NULL').fetchone()[0];changed=db.execute('SELECT COUNT(*) FROM pre.assets p JOIN main.assets n USING(asset_id) WHERE '+' OR '.join('n."'+k+'" IS NOT p."'+k+'"' for k in legacy)).fetchone()[0];count=db.execute('SELECT COUNT(*) FROM main.assets').fetchone()[0]
    assert missing==changed==0 and count==246605+len(new) and db.execute('PRAGMA main.integrity_check').fetchone()[0]=='ok';db.close()
    refs=[dict(script_id=r['parent_asset_id'],source_version=r['source_version'],route='Unknown',scene='',locale='Europe',line=r.get('embedded_offset',''),command='embedded_asset',reference_type=r['asset_kind'],reference_name=r['source_logical_path'],target_asset_id=r['asset_id'],target_path=r['extracted_path'],resolution_status='verified_source_parent_payload') for r in new if r['parent_asset_id']]
    append_csv_exact(BACK/'Metadata/ASSET_REFERENCES.csv',STAGE/'ASSET_REFERENCES.csv',refs)
    voices=readrows(md/'FUC_VOICE_INDEX.csv');vrows=[dict(voice_file=r['source'],asset_id=r['voice_asset'],speaker='',route='Unknown',scene='',dialogue='',locale='Europe',duration=r['duration'],working_path=r['working_path'],dialogue_mapping_count=0,notes=r['evidence']) for r in voices]
    append_csv_exact(BACK/'Metadata/VOICE_INDEX.csv',STAGE/'VOICE_INDEX.csv',vrows);append_csv_exact(BACK/'Metadata/HARDLINKS.csv',STAGE/'HARDLINKS.csv',newlinks)
    jsonwrite(STAGE/'FUC_SCHEMA_EXTENSION.json',dict(source_version='FateUnlimitedCodesPortable_Europe',legacy_fields_preserved=legacy,optional_fields_added=[k for k in fields if k not in legacy],Japan_recovery_formally_integrated=False,animation_status='Full MOT channel bytes/curves decoded; runtime binding unverified'))
    files=['ASSET_CATALOG.csv','ASSET_CATALOG.jsonl','ASSET_CATALOG.sqlite','ASSET_REFERENCES.csv','VOICE_INDEX.csv','HARDLINKS.csv','FUC_SCHEMA_EXTENSION.json']
    journal=dict(status='STAGED_VALIDATED',before=246605,added=len(new),after=count,missing_old_ids=missing,changed_old_rows=changed,source_version='FateUnlimitedCodesPortable_Europe',files=files,source_counts={**baseline['source_counts'],'FateUnlimitedCodesPortable_Europe':len(new)},created_at=now());jsonwrite(md/'INTEGRATION_JOURNAL.json',journal)
    for name in files:os.replace(STAGE/name,L/'Metadata'/name)
    writejsonl(md/'ASSETS.jsonl',new);csvwrite(EU/'Converted/WORKING_COPY_INDEX.csv',[dict(asset_id=r['asset_id'],source_logical_path=r['source_logical_path'],working_path=r['converted_path'],status=r['conversion_status']) for r in new]);journal.update(status='COMMITTED',completed_at=now(),new_canonical_objects=len(newlinks),new_asset_references=len(refs));jsonwrite(marker,journal);log('EUROPE INTEGRATED',journal)
if __name__=='__main__':run()
