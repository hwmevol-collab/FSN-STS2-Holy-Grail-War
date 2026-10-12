from fuc_semantic_common import *
def main():
    if (SB/'BASELINE.json').exists():
        log('EXISTING SEMANTIC BASELINE',semantic_frozen()['created_at']);return
    db=sqlite3.connect('file:'+str(L/'Metadata/ASSET_CATALOG.sqlite').replace('\\','/')+'?mode=ro',uri=True)
    total,maxid=db.execute('select count(*),max(asset_id) from assets').fetchone()
    counts=dict(db.execute('select source_version,count(*) from assets group by source_version'))
    integrity=db.execute('pragma integrity_check').fetchone()[0];db.close()
    assert total==268504 and maxid=='FSN268504' and integrity=='ok'
    assert counts['FateUnlimitedCodesPortable_Europe']==21899
    frozen_files=set(p for root in [L/'Metadata',EU/'Metadata'] for p in root.rglob('*') if p.is_file())
    frozen_files.update(p for p in (L/'Gallery').glob('*') if p.is_file())
    frozen_files.update(p for p in (L/'Reports').glob('FUC*') if p.is_file())
    frozen_files.update(p for p in (W/'scripts').glob('fuc*') if p.is_file() and not p.name.startswith('fuc_semantic_'))
    frozen_files.update(pathlib.Path(r['path']) for r in readjson(W/'backups/fuc-battle-runtime-pre/STATIC_GLB_FINGERPRINTS.json'))
    frozen_files.update(p for root in [EU/'Converted/AnimatedModels',EU/'Converted/BattleScenes'] for p in root.rglob('*') if p.is_file())
    selected={'MODEL_INDEX.csv','ANIMATION_INDEX.csv','CHARACTER_ASSET_MAP.csv','FUC_GAME_DATA_INDEX.csv','FUC_AUDIO_INDEX.csv','FUC_VOICE_INDEX.csv','EFFECT_INDEX.csv','STAGE_INDEX.csv','FUC_LAN_CLIP145_FULL_BATTLE_REPLAY_REPORT.md'}
    SB.mkdir(parents=True,exist_ok=True);SW.mkdir(parents=True,exist_ok=True)
    files=[];backup_bytes=0
    for p in sorted(frozen_files):
        s=p.stat();h=sha(p);backup=''
        if p.name in selected or (p.is_relative_to(EU/'Metadata') and len(p.relative_to(EU/'Metadata').parts)>1 and s.st_size<20_000_000):
            dest=SB/'Library'/p.relative_to(L);dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(p,dest);assert sha(dest)==h;backup=str(dest);backup_bytes+=s.st_size
        files.append(dict(path=str(p),size=s.st_size,mtime_ns=s.st_mtime_ns,sha256=h,backup=backup))
    prior=readjson(W/'fuc/BattleReplay/STABILITY_FINAL.json');assert prior['status']=='PASS'
    summary=dict(created_at=now(),asset_total=total,max_asset_id=maxid,source_counts=counts,sqlite_integrity=integrity,files=files,frozen_file_count=len(files),backup_bytes=backup_bytes,new_asset_ids=0,prior_stability=prior,policy='Hash all existing metadata/gallery/golden outputs; copy critical metadata only. No Raw, ISO or large materials copied. Runtime remains CLOSED FOR MOD DEVELOPMENT.')
    jsonwrite(SB/'BASELINE.json',summary);jsonwrite(L/'Reports/FUC_SEMANTIC_MAPPING_PRE_BASELINE.json',summary)
    log('SEMANTIC BASELINE',dict(assets=total,files=len(files),backup_bytes=backup_bytes))
if __name__=='__main__':main()
