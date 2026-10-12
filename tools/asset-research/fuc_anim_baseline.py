from fuc_anim_common import *
def run():
    if (AB/'BASELINE.json').exists():
        log('Animation baseline already frozen',frozen());return
    # An interrupted read-only snapshot may be resumed while no completed marker exists.
    AB.mkdir(parents=True,exist_ok=True);AW.mkdir(parents=True,exist_ok=True);AMD.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(f'file:{(L/"Metadata/ASSET_CATALOG.sqlite").as_posix()}?mode=ro',uri=True)
    counts=dict(db.execute('SELECT source_version,COUNT(*) FROM assets GROUP BY source_version'));total=sum(counts.values());maxid=db.execute('SELECT MAX(asset_id) FROM assets').fetchone()[0]
    assert total==268504 and counts['FateUnlimitedCodesPortable_Europe']==21899 and maxid=='FSN268504'
    assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    files=[];selected=list((L/'Metadata').glob('*'))+list((EU/'Metadata').rglob('*'))+list((L/'Gallery').glob('*.html'))+list((L/'Gallery').glob('*.js'))+list((L/'Gallery').glob('*.json'))
    for p in selected:
        if not p.is_file() or p.is_relative_to(AMD):continue
        rel=p.relative_to(L);target=AB/rel;target.parent.mkdir(parents=True,exist_ok=True)
        if p.name=='ASSET_CATALOG.sqlite':
            wal=pathlib.Path(str(p)+'-wal');assert not wal.exists() or wal.stat().st_size==0,'Active SQLite WAL requires a separate consistent snapshot'
        # Physical copy preserves the exact database bytes; sqlite.backup rewrites its header.
        shutil.copy2(p,target)
        h=sha(p);assert h==sha(target),(p,'Snapshot hash differs')
        files.append(dict(path=str(p),backup=str(target),size=p.stat().st_size,sha256=h,mtime_ns=p.stat().st_mtime_ns))
    protected=AB/'PROTECTED_PATHS.jsonl';count=0;missing=[]
    with protected.open('w',encoding='utf-8') as f:
        for aid,raw,work,thumb,rh,wh in db.execute('SELECT asset_id,extracted_path,converted_path,thumbnail_path,sha256,working_sha256 FROM assets'):
            for kind,p,h in [('raw',raw,rh),('working',work,wh),('thumbnail',thumb,'')]:
                if not p:continue
                q=pathlib.Path(p)
                if not q.is_file():missing.append(dict(asset_id=aid,kind=kind,path=p));continue
                st=q.stat();f.write(json.dumps(dict(asset_id=aid,kind=kind,path=p,size=st.st_size,mtime_ns=st.st_mtime_ns,declared_sha256=h),ensure_ascii=False)+'\n');count+=1
    db.close();assert not missing,missing[:5]
    identity=readjson(EU/'Metadata/SOURCE_IDENTITY.json');assert sha(identity['source'])==identity['sha256']
    baseline=dict(created_at=now(),status='FROZEN_ANIMATION_PRE_VALIDATION',asset_total=total,fuc_asset_count=counts['FateUnlimitedCodesPortable_Europe'],max_asset_id=maxid,source_counts=counts,files=files,backup_bytes=sum(r['size'] for r in files),protected_path_records=count,protected_manifest_sha256=sha(protected),source_identity=identity,disk_E=dict(zip(['total','used','free'],shutil.disk_usage('E:/'))),policy='Only key Metadata and Gallery code snapshots. No RawExtracted copied. No asset allocation, extraction or existing payload modification.')
    jsonwrite(AB/'BASELINE.json',baseline);jsonwrite(L/'Reports/FUC_ANIMATION_PRE_BASELINE.json',baseline);log('ANIMATION BASELINE FROZEN',dict(asset_total=total,fuc_asset_count=counts['FateUnlimitedCodesPortable_Europe'],max_asset_id=maxid,files=len(files),backup_bytes=baseline['backup_bytes'],protected_path_records=count))
if __name__=='__main__':run()
