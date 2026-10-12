from fuc_semantic_common import *
def main():
    b=semantic_frozen();changed=[]
    for r in b['files']:
        p=pathlib.Path(r['path'])
        if not p.is_file() or p.stat().st_size!=r['size'] or sha(p)!=r['sha256']:changed.append(str(p))
    unique={};refs=0;missing=[];sizechanged=[]
    for r in rowsjson(W/'backups/fuc-battle-runtime-pre/PROTECTED_PATHS.jsonl'):
        refs+=1;unique.setdefault(r['path'],r)
    for i,(s,r) in enumerate(unique.items()):
        p=pathlib.Path(s)
        if not p.is_file():missing.append(s)
        elif p.stat().st_size!=r['size']:sizechanged.append(s)
        if i and i%100000==0:log('PROTECTED_PATHS',i,'of',len(unique))
    c=sqlite3.connect('file:'+str(L/'Metadata/ASSET_CATALOG.sqlite').replace('\\','/')+'?mode=ro',uri=True)
    integrity=c.execute('pragma integrity_check').fetchone()[0];total,maxid=c.execute('select count(*),max(asset_id) from assets').fetchone();ids={r[0] for r in c.execute('select asset_id from assets')};missingids=[f'FSN{i:06d}' for i in range(1,268505) if f'FSN{i:06d}' not in ids];fuc=c.execute("select count(*) from assets where source_version='FateUnlimitedCodesPortable_Europe'").fetchone()[0];c.close()
    s=dict(timestamp=now(),asset_total=total,max_asset_id=maxid,fuc_asset_count=fuc,new_asset_ids=total-268504,missing_old_ids=len(missingids),changed_old_rows=0 if not changed else None,changed_old_rows_evidence='Frozen CSV / JSONL / SQLite byte hashes',frozen_files=len(b['files']),changed_frozen_files=changed,protected_path_references=refs,protected_unique_paths=len(unique),missing_paths=missing,changed_protected_sizes=sizechanged,static_glb_count=341,sqlite_integrity=integrity,raw_payload_scope='Every inherited preserved path rechecked for existence and size; Raw hashes not recomputed; no source writes',status='PASS' if not changed and not missing and not sizechanged and not missingids and total==268504 and maxid=='FSN268504' and fuc==21899 and integrity=='ok' else 'FAIL')
    jsonwrite(SW/'STABILITY_FINAL.json',s);log('SEMANTIC STABILITY',s);assert s['status']=='PASS'
if __name__=='__main__':main()
