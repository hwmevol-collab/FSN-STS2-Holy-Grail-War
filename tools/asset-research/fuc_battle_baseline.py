from fuc_battle_common import *
def main():
    if (BB/'BASELINE.json').exists():log('EXISTING BATTLE BASELINE',battle_frozen()['created_at']);return
    BB.mkdir(parents=True,exist_ok=True);BR.mkdir(parents=True,exist_ok=True);BMD.mkdir(parents=True,exist_ok=True)
    golden=readjson(AMD/'FUC_ANIMATION_VALIDATION_SUMMARY.json');assert golden['status']=='FUC_ANIMATION_RUNTIME_VALIDATION_PASS'
    assert golden['validated_models']==3 and golden['validated_animations']==9
    db=sqlite3.connect((L/'Metadata/ASSET_CATALOG.sqlite').as_uri()+'?mode=ro',uri=True)
    total,maxid=db.execute('select count(*),max(asset_id) from assets').fetchone();counts=dict(db.execute('select source_version,count(*) from assets group by source_version'));assert total==268504 and maxid=='FSN268504';assert db.execute('pragma integrity_check').fetchone()[0]=='ok';db.close()
    selected=list((L/'Metadata').glob('*'))+list((EU/'Metadata').rglob('*'))+list((L/'Gallery').glob('*.html'))+list((L/'Gallery').glob('*.js'))+list((L/'Gallery').glob('*.json'))
    selected+=[L/'Reports/FUC_ANIMATION_VALIDATION_REPORT.md']
    selected+=list((EU/'Converted/AnimatedModels').rglob('*'))
    selected+=list((L/'Gallery/animation_previews').glob('*'))
    selected+=[p for p in (W/'scripts').glob('fuc*.py') if p.name.startswith(('fuc_anim_','fuc_motion_','fuc_source_bones'))]
    selected+=[W/'scripts/fuc_anim_launch.ps1',W/'scripts/fuc_anim_gltf_validate.cjs']
    files=[]
    for p in selected:
        if not p.is_file() or p.is_relative_to(BMD):continue
        root=L if p.is_relative_to(L) else W;rel=p.relative_to(root);dest=BB/('Library' if root==L else 'Work')/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        if p.name=='ASSET_CATALOG.sqlite':assert not pathlib.Path(str(p)+'-wal').exists() or pathlib.Path(str(p)+'-wal').stat().st_size==0
        shutil.copy2(p,dest);h=sha(p);assert h==sha(dest)
        rowcount=''
        if p.suffix=='.csv':
            with p.open(encoding='utf-8-sig',newline='') as f:rowcount=max(0,sum(1 for _ in csv.reader(f))-1)
        elif p.suffix=='.jsonl':
            with p.open(encoding='utf-8') as f:rowcount=sum(1 for _ in f)
        files.append(dict(path=str(p),backup=str(dest),size=p.stat().st_size,sha256=h,row_count=rowcount,mtime_ns=p.stat().st_mtime_ns))
    # Existing manifest already reflects the unchanged 268504 catalog. No raw copies.
    source_manifest=AB/'PROTECTED_PATHS.jsonl';dest=BB/'PROTECTED_PATHS.jsonl';shutil.copy2(source_manifest,dest);assert sha(dest)==sha(source_manifest)
    models=readrows(EU/'Metadata/MODEL_INDEX.csv');static=[];seen=set()
    for r in models:
        path=r['working_path']
        if not path or path in seen:continue
        seen.add(path);p=pathlib.Path(path);s=p.stat();static.append(dict(path=path,size=s.st_size,sha256=sha(p),mtime_ns=s.st_mtime_ns))
    assert len(static)==341
    jsonwrite(BB/'STATIC_GLB_FINGERPRINTS.json',static)
    baseline=dict(created_at=now(),status='FROZEN_BATTLE_RUNTIME_GOLDEN_BASELINE',asset_total=total,max_asset_id=maxid,source_counts=counts,golden=dict(models=3,clips=9,max_runtime_matrix_error=golden['controlled_runtime']['max_local_world_matrix_error'],max_threejs_matrix_error=golden['playback']['max_matrix_error'],runtime_failures=0,viewer_missing_nodes=0),files=files,backup_files=len(files),backup_bytes=sum(r['size'] for r in files),static_glb_count=341,protected_path_records=624836,protected_manifest_sha256=sha(dest),source_identity=readjson(EU/'Metadata/SOURCE_IDENTITY.json'),policy='Critical Metadata, Golden animated GLBs/viewer/scripts and Gallery only. No RawExtracted or ISO copied. No asset allocation.')
    jsonwrite(BB/'BASELINE.json',baseline);jsonwrite(L/'Reports/FUC_BATTLE_RUNTIME_PRE_BASELINE.json',baseline);log('BATTLE BASELINE',dict(files=len(files),bytes=baseline['backup_bytes'],models=3,clips=9,assets=total))
if __name__=='__main__':main()
