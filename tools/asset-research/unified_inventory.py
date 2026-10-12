from unified_common import *
import shutil
PROTECTED = ['Metadata','Original','Remastered','HollowAtaraxia','FateUnlimitedCodesPortable_Europe','ReferenceBooks','AnimationReferences','Gallery','Reports']
def metadata_files():
    out=set()
    for root in [L/'Metadata',O,A,F,L/'HollowAtaraxia/Metadata',L/'Reports']:
        for p in root.iterdir():
            if p.is_file() and p.suffix.lower() in ('.csv','.json','.jsonl','.sqlite','.md'):out.add(p)
    for sub in ['SemanticMapping','AnimationValidation','BattleRuntimeMapping','BattleGeneralization','BattleReplay','FinalFreeze']:
        out.update(p for p in (F/sub).iterdir() if p.is_file())
    return sorted(out)
def inventory():
    W.mkdir(parents=True,exist_ok=True);B.mkdir(parents=True,exist_ok=True)
    baseline=L/'Reports/UNIFIED_SEMANTIC_PRE_BASELINE.json'
    if baseline.exists():
        print('Baseline already frozen:',baseline,flush=True);return read(baseline)
    c=ro(L/'Metadata/ASSET_CATALOG.sqlite')
    total,maxid=c.execute('select count(*),max(asset_id) from assets').fetchone()
    counts=dict(c.execute('select source_version,count(*) from assets group by source_version'))
    integrity=c.execute('pragma integrity_check').fetchall()
    schema=c.execute("select sql from sqlite_master where name='assets'").fetchone()[0];c.close()
    assert total==270798 and maxid=='FSN270798' and integrity==[('ok',)],(total,maxid,integrity)
    cats={}
    for ext in ['csv','jsonl','sqlite']:
        p=L/f'Metadata/ASSET_CATALOG.{ext}'
        count=total
        if ext=='csv':
            with p.open(encoding='utf-8-sig',newline='') as f:r=csv.DictReader(f);fields=r.fieldnames;count=sum(1 for _ in r)
        elif ext=='jsonl':
            with p.open(encoding='utf-8-sig') as f:first=json.loads(next(f));fields=list(first);count=1+sum(1 for line in f if line.strip())
        else:fields=schema
        assert count==total
        cats[ext]={'sha256':sha(p),'row_count':count,'schema':fields,'size':p.stat().st_size}
    shots=sum(1 for _ in rows(A/'ANIMATION_SHOT_INDEX.csv'));pages=sum(1 for _ in rows(O/'OFFICIAL_MATERIAL_PAGE_INDEX.csv'))
    subs=sum(1 for _ in rows(A/'ANIMATION_SUBTITLE_LINES.csv'))
    frozen=read(F/'FUC_FINAL_MANIFEST.json')
    assert shots==67499 and pages==1957 and subs==106006
    assert frozen['research_status']=='FUC_RESEARCH_PHASE_COMPLETE_FOR_MOD_DEVELOPMENT',frozen['research_status']
    records=[]
    with (B/'PROTECTED_FILES.jsonl').open('w',encoding='utf-8') as f:
        for name in PROTECTED:
            print('Freezing directory',name,flush=True)
            for root,dirs,files in os.walk(L/name,followlinks=False):
                dirs[:]=[d for d in dirs if not (Path(root)/d).is_symlink()]
                for filename in files:
                    p=Path(root)/filename;st=p.stat();f.write(js({'path':str(p),'size':st.st_size,'mtime_ns':st.st_mtime_ns})+'\n')
    for p in metadata_files():
        rel=p.relative_to(L);target=B/'MetadataBackup'/rel;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,target)
        records.append({'path':str(p),'size':p.stat().st_size,'sha256':sha(p),'backup':str(target)})
    obj={'status':'FROZEN','timestamp':now(),'asset_total':total,'max_id':maxid,'catalog':cats,'sqlite_integrity':'ok','source_version_counts':counts,'animation_shot_count':shots,'subtitle_line_count':subs,'official_page_count':pages,'fuc_final_marker':frozen['research_status'],'fuc_frozen':True,'metadata_files':records,'protected_inventory':str(B/'PROTECTED_FILES.jsonl'),'protected_inventory_sha256':sha(B/'PROTECTED_FILES.jsonl'),'media_copied':False}
    dump(B/'BASELINE.json',obj);dump(baseline,obj);print('BASELINE FROZEN',total,shots,pages,flush=True);return obj
def verify():
    b=read(B/'BASELINE.json');errors=[];n=0
    for r in b['metadata_files']:
        if not Path(r['path']).exists() or sha(r['path'])!=r['sha256']:errors.append({'type':'metadata_hash_changed','path':r['path']})
    with Path(b['protected_inventory']).open(encoding='utf-8') as f:
        for line in f:
            r=json.loads(line);p=Path(r['path']);n+=1
            if not p.exists():errors.append({'type':'removed','path':str(p)});continue
            st=p.stat()
            if st.st_size!=r['size'] or st.st_mtime_ns!=r['mtime_ns']:errors.append({'type':'size_or_mtime_changed','path':str(p)})
    result={'timestamp':now(),'status':'PASS' if not errors else 'FAIL','catalog_hashes_unchanged':not errors,'protected_files_checked':n,'metadata_hashes_checked':len(b['metadata_files']),'errors':errors,'new_FSN_IDs':0,'verification_boundary':'All baseline files size+mtime checked; frozen metadata SHA256 checked. Media were not rehashed.'}
    dump(S/'Reports/SEMANTIC_STABILITY.json',result);print(js({k:v for k,v in result.items() if k!='errors'}),flush=True);assert not errors,errors[:5];return result
if __name__=='__main__':
    import sys
    verify() if 'Verify' in sys.argv else inventory()
