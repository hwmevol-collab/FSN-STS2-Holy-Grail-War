from common import *
import argparse
def run(verify=False):
    rows=[]; errors=[]; stats={}; started=now()
    for ver,root in SOURCES.items():
        files=sorted(root.rglob('*')); files=[p for p in files if p.is_file()]
        for i,p in enumerate(files):
            try:
                st=p.stat()
                with p.open('rb') as f:b=f.read(64)
                rows.append(dict(source_version=ver,absolute_path=str(p),relative_path=p.relative_to(root).as_posix(),filename=p.name,extension=p.suffix.lower(),size=st.st_size,sha256=sha(p),modified_time=datetime.datetime.fromtimestamp(st.st_mtime,datetime.timezone.utc).isoformat(),magic_bytes=b.hex(),detected_format=signature(b,p.suffix)))
            except Exception as e:errors.append(dict(path=str(p),error=repr(e)))
            if i%25==0:print(ver,i+1,'/',len(files),p.name,flush=True)
        subset=[r for r in rows if r['source_version']==ver]
        stats[ver]={'file_count':len(subset),'size':sum(r['size'] for r in subset),'extensions':dict(collections.Counter(r['extension'] for r in subset)),'containers':sum(r['detected_format'] in ['XP3','FPD'] or r['extension'] in ['.bin','.dat'] for r in subset)}
    if verify:
        old=json.loads((L/'Metadata/SOURCE_INVENTORY.json').read_text(encoding='utf-8'))
        a={r['absolute_path']:r for r in old};b={r['absolute_path']:r for r in rows}
        differences=[{'file':p,'before':a.get(p,{}).get('sha256'),'after':b.get(p,{}).get('sha256'),'modified_before':a.get(p,{}).get('modified_time'),'modified_after':b.get(p,{}).get('modified_time')} for p in a.keys()|b.keys() if a.get(p,{}).get('sha256')!=b.get(p,{}).get('sha256') or a.get(p,{}).get('modified_time')!=b.get(p,{}).get('modified_time')]
        jsonwrite(L/'Reports/SOURCE_READONLY_VERIFICATION.json',{'started':started,'ended':now(),'files_checked':len(rows),'differences':differences,'errors':errors,'pass':not differences and not errors});print('SOURCE_VERIFY',len(differences),len(errors),flush=True)
        if differences or errors:raise RuntimeError('Source baseline changed or unreadable; existing library refresh stopped')
    else:
        jsonwrite(L/'Metadata/SOURCE_INVENTORY.json',rows);csvwrite(L/'Metadata/SOURCE_INVENTORY.csv',rows)
        jsonwrite(L/'Reports/SOURCE_BASELINE.json',{'started':started,'ended':now(),'sources':stats,'disk_free_start':shutil.disk_usage('E:/').free,'errors':errors})
    print(json.dumps(stats),flush=True)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true');run(parser.parse_args().verify)
