"""Read-only audit of frozen FUC assets; new results only in FinalFreeze."""
import argparse,collections,csv,hashlib,io,json,os,pathlib,sqlite3,struct,time,datetime
L=pathlib.Path('E:/FSN_MASTER_ASSET_LIBRARY');W=pathlib.Path('E:/FSN_MASTER_ASSET_WORK');EU=L/'FateUnlimitedCodesPortable_Europe'
WORK=W/'fuc/FinalFreeze';MD=EU/'Metadata/FinalFreeze';SCRIPTS=W/'scripts'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(p):return json.loads(pathlib.Path(p).read_text('utf-8-sig'))
def write(p,x):p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2),'utf-8')
def rows(p):
    with pathlib.Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def sha(p):
    h=hashlib.sha256()
    with pathlib.Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()
def snap(p):return dict(path=str(p),size=p.stat().st_size,sha256=sha(p))
def log(*x):print(*x,flush=True)
def baseline():
    dst=L/'Reports/FUC_FINAL_FREEZE_PRE_BASELINE.json'
    assert not dst.exists(),'Do not replace the original final-freeze baseline'
    src=read(EU/'Metadata/SOURCE_IDENTITY.json');paths=set()
    roots=[L/'Metadata',EU/'Metadata',EU/'Converted/Models',EU/'Converted/AnimatedModels',EU/'Converted/BattleScenes']
    for root in roots:paths.update(p for p in root.rglob('*') if p.is_file())
    paths.update(p for p in (L/'Reports').glob('FUC*') if p.is_file())
    paths.update(p for p in (L/'Gallery').iterdir() if p.is_file())
    paths.update(p for p in SCRIPTS.glob('fuc*.*') if p.is_file())
    paths.update(p for p in SCRIPTS.glob('FUC*.*') if p.is_file())
    # Existing evidence, not a new trace: controlled Golden frames and same-Episode sources.
    for root in [W/'fuc/AnimationValidation/Runtime',W/'fuc/AnimationValidation/Playback',W/'fuc/BattleReplay/Episode08']:
        if root.exists():paths.update(p for p in root.rglob('*') if p.is_file())
    for root in [W/'fuc/BattleReplay/ViewerAcceptanceFinalV3',W/'fuc/BattleReplay/GoldenRegression']:
        if root.exists():paths.update(p for p in root.rglob('*') if p.is_file())
    anim=rows(EU/'Metadata/AnimationValidation/FUC_VALIDATED_ANIMATIONS.csv')
    for r in anim:
        for k in ['animated_glb','preview']:
            if r.get(k):paths.add(pathlib.Path(r[k]))
    replay=read(EU/'Metadata/BattleReplay/FUC_LAN_CLIP145_REPLAY_MANIFEST.json')
    if replay.get('preview'):paths.add(L/replay['preview'].lstrip('/'))
    source_hashes=[]
    for key in ['source','preservation_iso_path']:
        p=pathlib.Path(src[key]);x=snap(p);assert x['size']==src['size'] and x['sha256']==src['sha256'];source_hashes.append(x)
    con=sqlite3.connect('file:'+str(L/'Metadata/ASSET_CATALOG.sqlite')+'?mode=ro',uri=True)
    counts=dict(con.execute('select source_version,count(*) from assets group by source_version'));total,maxid=con.execute('select count(*),max(asset_id) from assets').fetchone();integ=con.execute('pragma integrity_check').fetchone()[0];con.close()
    assert total==268504 and counts.get('FateUnlimitedCodesPortable_Europe')==21899 and maxid=='FSN268504' and integ=='ok'
    files=[]
    for i,p in enumerate(sorted(paths)):
        files.append(snap(p))
        if i and i%500==0:log('FREEZE_HASHES',i)
    b=dict(timestamp=now(),asset_total=total,source_counts=counts,max_asset_id=maxid,sqlite_integrity=integ,source=src,source_files=source_hashes,files=files,scope='Existing major Metadata, Catalog, static/validated/replay GLB/viewers, Gallery pages, FUC scripts and Golden captures. No Raw copy.')
    write(dst,b);write(WORK/'BASELINE.json',b);log('BASELINE',len(files),len(source_hashes),total)
def inspect():
    chosen=['MODEL_SUMMARY','TEXTURE_SUMMARY','AUDIO_SUMMARY','SOUND_BANK_SUMMARY','VIDEO_SUMMARY','MOTION_SUMMARY','GAME_DATA_SUMMARY','RESULT_SUMMARY','FPK_EXTRACTION_SUMMARY','JAPAN_RECOVERY_COMPARISON_SUMMARY','TOOLS_AUDIT']
    def compact(x):
        if isinstance(x,list):return {'length':len(x),'first':compact(x[0]) if x else None}
        if isinstance(x,dict):return {k:compact(v) for k,v in x.items()}
        return x
    for n in chosen:
        p=EU/'Metadata'/f'{n}.json'
        if p.exists():log(n,json.dumps(compact(read(p)),ensure_ascii=False))
    for directory in [EU/'Metadata/AnimationValidation',EU/'Metadata/BattleReplay',EU/'Converted/AnimatedModels/viewer',EU/'Converted/BattleScenes/lan_clip145']:
        log('FILES',str(directory),[p.name for p in directory.iterdir() if p.is_file()])
    for n in ['FUC_AUDIO_INDEX','VIDEO_INDEX','TEXTURE_INDEX','ASSETS','FUC_UNKNOWN_FORMATS']:
        rr=rows(EU/'Metadata'/f'{n}.csv');log('INDEX',n,'count',len(rr),'fields',list(rr[0]) if rr else [],'first',rr[0] if rr else {})
def source():
    import pycdlib
    from fuc_iso import sfo
    identity=read(EU/'Metadata/SOURCE_IDENTITY.json');p=pathlib.Path(identity['source']);cd=pycdlib.PyCdlib();cd.open(str(p));buf=io.BytesIO();iso_name=next(r['iso_path'] for r in rows(EU/'Metadata/SOURCE_INVENTORY.csv') if r['logical_path']=='PSP_GAME/PARAM.SFO');cd.get_file_from_iso_fp(buf,iso_path=iso_name);params=sfo(buf.getvalue());cd.close()
    checked=[snap(pathlib.Path(identity[k])) for k in ['source','preservation_iso_path']]
    assert all(x['sha256']==identity['sha256'] and x['size']==identity['size'] for x in checked)
    assert params==identity['PARAM_SFO'] and params['DISC_ID']=='NPEH00007' and params['DISC_VERSION']=='1.01'
    japan_roots=[p for p in [W/'fuc/Japan_Recovery',L/'FateUnlimitedCodesPortable'] if p.exists()]
    result=dict(timestamp=now(),status='PASS',source_version='FateUnlimitedCodesPortable_Europe',files=checked,PARAM_SFO=params,source_unchanged=True,Japan_Recovery=dict(truncated=True,official_source=False,asset_ids=0,preserved_roots=[str(p) for p in japan_roots],action='preserve separately; no reintegration, repair or deletion'))
    write(WORK/'SOURCE_AUDIT.json',result);log('SOURCE',params['DISC_ID'],params['DISC_VERSION'],'SHA PASS')
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['baseline','inspect','source']);a=ap.parse_args();globals()[a.mode]()
