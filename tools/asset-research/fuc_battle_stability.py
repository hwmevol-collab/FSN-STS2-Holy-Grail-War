"""Final append-only battle-layer stability gate. Read-only catalog and preserved paths."""
from fuc_battle_common import *

def main():
 b=battle_frozen();changed=[];missing=[];frozen_checks=[]
 for r in b['files']:
  p=pathlib.Path(r['path']);ok=p.is_file() and p.stat().st_size==r['size'] and sha(p)==r['sha256'];frozen_checks.append(dict(path=str(p),equal=ok))
  if not ok:changed.append(str(p))
 static=[]
 for r in readjson(BB/'STATIC_GLB_FINGERPRINTS.json'):
  p=pathlib.Path(r['path']);ok=p.is_file() and p.stat().st_size==r['size'] and p.stat().st_mtime_ns==r['mtime_ns'] and sha(p)==r['sha256'];static.append(dict(path=str(p),equal=ok))
 unique={};refs=0
 for r in rowsjson(BB/'PROTECTED_PATHS.jsonl'):
  refs+=1;unique.setdefault(r['path'],r)
 for i,(s,r) in enumerate(unique.items()):
  p=pathlib.Path(s)
  if not p.is_file():missing.append(s)
  elif p.stat().st_size!=r['size']:changed.append(s+' [protected size changed]')
  if i and i%100000==0:log('PROTECTED_PATHS',i,'of',len(unique))
 c=sqlite3.connect('file:'+str(L/'Metadata/ASSET_CATALOG.sqlite').replace('\\','/')+'?mode=ro',uri=True)
 integrity=c.execute('pragma integrity_check').fetchone()[0];total,maxid=c.execute('select count(*),max(asset_id) from assets').fetchone();ids={r[0] for r in c.execute('select asset_id from assets')};missingids=[f'FSN{i:06d}' for i in range(1,268505) if f'FSN{i:06d}' not in ids];fuc=c.execute("select count(*) from assets where source_version='FateUnlimitedCodesPortable_Europe'").fetchone()[0];c.close()
 summary=dict(timestamp=now(),asset_total=total,max_asset_id=maxid,fuc_asset_count=fuc,new_asset_ids=total-268504,missing_old_ids=len(missingids),changed_old_rows=0 if not changed else None,changed_old_rows_evidence='Byte-identical frozen CSV, JSONL and SQLite catalogs',frozen_files=len(frozen_checks),changed_frozen_files=changed,protected_path_references=refs,protected_unique_paths=len(unique),frozen_path_loss=len(missing),missing_paths=missing,static_glb_count=len(static),static_glb_changed=sum(not r['equal'] for r in static),sqlite_integrity=integrity,raw_payload_scope='All frozen paths exist with original sizes; full Raw payload hashes are not recomputed. No Raw or ISO write operation is performed.',status='PASS' if not changed and not missing and not missingids and all(r['equal'] for r in static) and total==268504 and maxid=='FSN268504' and fuc==21899 and integrity=='ok' else 'FAIL')
 jsonwrite(BR/'STABILITY_FINAL.json',summary);jsonwrite(BR/'FROZEN_FILE_FINAL_COMPARISON.json',frozen_checks);log('STABILITY',summary);assert summary['status']=='PASS'
if __name__=='__main__':main()
