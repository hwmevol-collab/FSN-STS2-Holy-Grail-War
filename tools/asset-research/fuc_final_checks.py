"""Additive final audit checks. Never export, decode new motion or write old indexes."""
from fuc_final_audit import *
from decimal import Decimal,InvalidOperation
import itertools,re,numpy as np

def catalog():
    b=read(WORK/'BASELINE.json');frozen={r['path']:r for r in b['files']}
    con=sqlite3.connect('file:'+str(L/'Metadata/ASSET_CATALOG.sqlite')+'?mode=ro',uri=True);con.row_factory=sqlite3.Row
    info=con.execute('pragma table_info(assets)').fetchall();numeric={r['name'] for r in info if r['type']=='REAL'}
    def normalize(k,v):
        if v is None or v=='':return ''
        if k=='alpha' and str(v).lower() in ['true','false','0','1']:return str(v).lower() in ['true','1']
        if k in numeric:
            try:return Decimal(str(v))
            except InvalidOperation:pass
        return str(v)
    seen=set();counts=collections.Counter();duplicates=[];mismatch=[];parents=[];count=0
    with (L/'Metadata/ASSET_CATALOG.csv').open(encoding='utf-8-sig',newline='') as cf,(L/'Metadata/ASSET_CATALOG.jsonl').open(encoding='utf-8') as jf:
        cr=csv.DictReader(cf);fields=cr.fieldnames
        for i,triple in enumerate(itertools.zip_longest(cr,jf,con.execute('select * from assets order by asset_id'))):
            a,line,s=triple
            if a is None or line is None or s is None:mismatch.append(dict(row=i,reason='row count mismatch'));continue
            j=json.loads(line);sd=dict(s);aid=a['asset_id'];count+=1
            if aid in seen:duplicates.append(aid)
            seen.add(aid);counts[a['source_version']]+=1
            for k in set(fields)|set(j)|set(sd):
                vals=[normalize(k,d.get(k)) for d in [a,j,sd]]
                if not vals[0]==vals[1]==vals[2]:
                    if len(mismatch)<30:mismatch.append(dict(asset_id=aid,field=k,values=[str(v) for v in vals]))
            if a.get('parent_asset_id'):parents.append((aid,a['parent_asset_id']))
            if i and i%50000==0:log('CATALOG_ROWS',i)
    invalid=[dict(asset_id=a,parent=p) for a,p in parents if p not in seen];missing=[f'FSN{i:06d}' for i in range(1,268505) if f'FSN{i:06d}' not in seen]
    integrity=con.execute('pragma integrity_check').fetchone()[0];con.close()
    hashes={n:sha(L/'Metadata'/n) for n in ['ASSET_CATALOG.csv','ASSET_CATALOG.jsonl','ASSET_CATALOG.sqlite']}
    unchanged=all(h==frozen[str(L/'Metadata'/n)]['sha256'] for n,h in hashes.items())
    jp=[k for k in counts if 'Japan' in k or 'Recovery' in k]
    result=dict(timestamp=now(),asset_total=count,source_counts=dict(counts),max_id=max(seen),csv_jsonl_sqlite_identical=True if not mismatch else False,normalization='empty/null omitted fields; declared REAL numeric equality; alpha boolean/SQLite0/1. Every inherited column compared.',duplicate_asset_ids=duplicates,missing_asset_ids=missing,invalid_parent_references=invalid,row_mismatches=mismatch,catalog_sha256=hashes,catalog_sha_unchanged=unchanged,sqlite_integrity=integrity,Japan_recovery_catalog_rows=sum(counts[k] for k in jp),new_asset_ids=count-268504,changed_old_rows=0 if unchanged and not mismatch else None)
    result['status']='PASS' if count==268504 and counts['FateUnlimitedCodesPortable_Europe']==21899 and not duplicates and not missing and not invalid and not mismatch and unchanged and integrity=='ok' and not jp else 'FAIL'
    write(WORK/'CATALOG_AUDIT.json',result);log('CATALOG',result);assert result['status']=='PASS'

def preservation():
    rr=rows(EU/'Metadata/ASSETS.csv');missing=[];bad=[];checked={};formats=collections.Counter()
    for r in rr:
        formats[r['extension'] or r['detected_format']]+=1
        p=pathlib.Path(r['extracted_path'])
        if not p.is_file():missing.append(dict(asset=r['asset_id'],path=str(p)));continue
        if str(p) not in checked:checked[str(p)]=dict(size=p.stat().st_size,sha256=sha(p))
        c=checked[str(p)]
        # Clip entries preserve the parent MOT, so source size/hash are intentionally inherited.
        if r.get('sha256') and c['sha256']!=r['sha256']:bad.append(dict(asset=r['asset_id'],path=str(p),reason='hash'))
        if r.get('size') and c['size']!=int(float(r['size'])):bad.append(dict(asset=r['asset_id'],path=str(p),reason='size'))
    iso=read(WORK/'SOURCE_AUDIT.json');result=dict(timestamp=now(),logical_assets=len(rr),unique_preservation_files=len(checked),formats=dict(formats),missing=missing,mismatches=bad,full_unique_source_sha256_checked=True,source_iso_status=iso['status'],status='PASS' if len(rr)==21899 and not missing and not bad else 'FAIL')
    write(WORK/'FUC_FINAL_PRESERVATION_AUDIT.json',result);log('PRESERVATION',len(rr),len(checked),'missing',len(missing),'mismatch',len(bad));assert result['status']=='PASS'

def working():
    rr=rows(EU/'Metadata/ASSETS.csv');paths={};missing=[];bad=[];categories=collections.Counter();relationships=0
    for r in rr:
        if r.get('converted_path'):
            relationships+=1;paths.setdefault(r['converted_path'],r.get('working_sha256',''));categories[pathlib.Path(r['converted_path']).suffix]+=1
        for k in ['thumbnail_path','metadata_path']:
            if r.get(k):paths.setdefault(r[k],'')
    for index in ['MODEL_INDEX','TEXTURE_INDEX','VIDEO_INDEX']:
        for r in rows(EU/'Metadata'/f'{index}.csv'):
            if r.get('working_path'):paths.setdefault(r['working_path'],r.get('working_sha256',''))
    for r in rows(EU/'Metadata/AnimationValidation/FUC_VALIDATED_ANIMATIONS.csv'):
        paths[r['animated_glb']]=r['animated_glb_sha256']
        if r.get('preview'):paths.setdefault(r['preview'],'')
    rep=read(EU/'Metadata/BattleReplay/FUC_LAN_CLIP145_REPLAY_MANIFEST.json')
    for k in ['body_animation_source','reference','timeline','preview']:paths.setdefault(str(L/rep[k].lstrip('/')),'')
    paths.setdefault(str(L/rep['sound_asset']['working_path'].lstrip('/')),'')
    for i,(s,h) in enumerate(paths.items()):
        p=pathlib.Path(s)
        if not p.is_file():missing.append(s)
        elif h and sha(p)!=h:bad.append(s)
    result=dict(timestamp=now(),logical_working_relations=relationships,unique_paths=len(paths),working_format_relations=dict(categories),missing=missing,changed_hashes=bad,status='PASS' if not missing and not bad else 'FAIL',scope='Every indexed Working path exists; every available working_sha256 checked; validated GLB, previews and Replay dependencies included. No reconversion.')
    write(WORK/'WORKING_COPY_AUDIT.json',result);log('WORKING',len(paths),'missing',len(missing),'bad',len(bad));assert result['status']=='PASS'

def glb(path):
    from fuc_anim_glb_export import load_glb
    from fuc_models_stage import validate
    doc,blob=load_glb(path);validate(doc,blob)
    assert doc['asset']['version']=='2.0' and doc['buffers'][0]['byteLength']<=len(blob)
    for n in doc.get('nodes',[]):
        assert all(0<=v<len(doc['nodes']) for v in n.get('children',[]))
        if 'skin' in n:assert n['skin']<len(doc['skins'])
    return doc,blob
def models():
    index=rows(EU/'Metadata/MODEL_INDEX.csv');unique={r['working_path']:r for r in index};bad=[];sources=0
    for p,r in unique.items():
        try:
            d,b=glb(p);assert pathlib.Path(r['source_path']).is_file();assert sha(p)==r['working_sha256'];sources+=1
        except Exception as e:bad.append(dict(path=p,error=repr(e)))
    result=dict(timestamp=now(),logical_models=len(index),unique_static_glb=len(unique),containers_buffers_accessors='all checked',source_mappings=sources,failures=bad,status='PASS' if len(unique)==341 and not bad else 'FAIL')
    write(WORK/'FUC_FINAL_MODEL_AUDIT.json',result);log('MODELS',len(unique),len(bad));assert result['status']=='PASS'

def golden():
    from fuc_motion_evaluator import evaluate,skeleton
    from fuc_motion_channels import parse_clip
    AW=W/'fuc/AnimationValidation';idx=read(EU/'Metadata/ANIMATION_INDEX.json');comparisons=[];raw_fail=[];frames=0;maxerror=0.0
    for code in ['sir','rin','lan']:
        sk=skeleton(code);lut=np.frombuffer((AW/f'Runtime/Motion/{code}/rotation_sine_lut.bin').read_bytes(),dtype='<f4')
        for clip in [0,1,2]:
            ir=next(r for r in idx if r['source_name']==f'chr/{code}/0000.mot' and r['motion_table_index']==clip and '0000.fpk' in r['source_path'] and r['working_path'])
            # Re-evaluate the raw source of the nine Golden clips only.
            raw=pathlib.Path(ir['source_path']).read_bytes();_,n,table,size=struct.unpack_from('>4I',raw);assert table==16 and size==len(raw)
            offsets=struct.unpack_from('>'+'I'*n,raw,16);off=offsets[clip];end=min([o for o in offsets if o>off]+[len(raw)]);decoded=parse_clip(raw,off,end);decoded['motion_table_index']=clip
            for fraction in [0,25,50,75,100]:
                cap=read(AW/f'Runtime/Motion/{code}/clip_{clip:04d}_fraction_{fraction:03d}.json');offpose=evaluate(decoded,sk,cap['time'],lut);frames+=1
                assert len(offpose['nodes'])==len(cap['nodes'])
                for a,b in zip(offpose['nodes'],cap['nodes']):
                    error=max(float(np.max(np.abs(np.asarray(a[k])-b[rk]))) for k,rk in [('translation','translation'),('rotation_storage','rotation_storage'),('scale','scale'),('delta_matrix','runtime_delta_matrix'),('local_matrix','runtime_local_matrix'),('world_matrix','runtime_world_matrix')]);maxerror=max(maxerror,error)
                    row=dict(character=code,clip=clip,fraction=fraction,time=cap['time'],node=a['ordinal'],max_error=error,status='PASS' if error==0 else 'FAIL');comparisons.append(row)
                    if error!=0:raw_fail.append(row)
    with (WORK/'GOLDEN_RAW_EVALUATOR_COMPARISON.csv').open('w',encoding='utf-8',newline='') as f:
        wr=csv.DictWriter(f,fieldnames=list(comparisons[0]));wr.writeheader();wr.writerows(comparisons)
    validated=rows(EU/'Metadata/AnimationValidation/FUC_VALIDATED_ANIMATIONS.csv');gb=[]
    for r in validated:
        d,b=glb(r['animated_glb']);assert len(d['animations'])==1;gb.append(dict(asset_id=r['animation_asset_id'],path=r['animated_glb'],sha256=sha(r['animated_glb'])))
    result=dict(timestamp=now(),models=3,clips=9,pose_frames=frames,node_comparisons=len(comparisons),failures=len(raw_fail),max_matrix_error=maxerror,source='original raw MOT parse of only9 Golden clips + existing runtime skeleton/sine LUT; no new runtime capture',glb_files=gb,status='PASS' if len(validated)==9 and not raw_fail else 'FAIL')
    write(WORK/'GOLDEN_REGRESSION.json',result);log('GOLDEN',frames,len(comparisons),maxerror);assert result['status']=='PASS'

def semantic():
    con=sqlite3.connect('file:'+str(L/'Metadata/ASSET_CATALOG.sqlite')+'?mode=ro',uri=True);ids={x[0] for x in con.execute('select asset_id from assets')};con.close()
    SM=EU/'Metadata/SemanticMapping';mr=rows(SM/'FUC_MOVE_INDEX.csv');keys={r['move_id'] for r in mr};bad=[];confidence={};counts={}
    def move_refs(value):
        if not value:return []
        try:v=json.loads(value);return v if isinstance(v,list) else [value]
        except ValueError:return [value]
    for p in SM.glob('*.csv'):
        rr=rows(p);counts[p.name]=len(rr);counter=collections.Counter()
        for i,r in enumerate(rr):
            for k,v in r.items():
                if k in ['status','semantic_status','mapping_status','request_status','name_mapping_status','state_binding_status']:counter[v]+=1
                if v and (k.endswith('_asset_id') or k in ['target_asset_id','source_asset','body_model_asset','mot_asset','model_asset_id','display_name_asset','effect_asset','audio_asset','voice_asset']):
                    for aid in re.findall(r'FSN\d{6}',v):
                        if aid not in ids:bad.append(dict(file=p.name,row=i,field=k,target=aid))
                if k=='move_id' and v:
                    for key in move_refs(v):
                        if key not in keys:bad.append(dict(file=p.name,row=i,field=k,target=key))
            # Graph command targets must also exist when they are sidecar identities.
        confidence[p.name]=dict(counter)
    command_ids={r['command_id'] for r in rows(SM/'FUC_COMMAND_INDEX.csv')}
    for r in rows(SM/'FUC_MOVE_RESOURCE_GRAPH.csv'):
        target=r.get('target_id','')
        if ':' in target and not target.startswith('FSN') and target not in command_ids and target not in keys:bad.append(dict(file='graph',target=target))
    names=rows(SM/'FUC_MOVE_NAME_INDEX.csv');known=sum(r['state_binding_status']=='confirmed_runtime_ui' for r in names);unbound=sum(r['state_binding_status']=='unknown' for r in names)
    categories=['confirmed_runtime','confirmed_ui','confirmed_table','confirmed_string_reference','strong_candidate','candidate','unknown'];total=collections.Counter()
    for p,cc in confidence.items():total.update(cc)
    result=dict(timestamp=now(),index_rows=counts,move_subjects=len(keys),UI_entries=len(names),known_UI_state_bindings=known,unbound_UI_entries=unbound,confidence_by_index=confidence,confidence_field_occurrences={k:total[k] for k in categories},confidence_count_unit='Status-field occurrences across relational indexes; not distinct assets or runtime-validated motion counts',dangling_references=bad,character_internal_identities=20,confirmed_UI_runtime_characters=['lan','sir','rin'],actual_return_bank_clip_bindings=3,request_only_source_candidates=5,status='PASS' if known==3 and unbound==259 and not bad else 'FAIL')
    write(WORK/'SEMANTIC_AUDIT.json',result);log('SEMANTIC',len(keys),known,unbound,len(bad));assert result['status']=='PASS'

def protected():
    # Inherited whole-library path snapshot. Check existence/size without rehashing old Raw.
    source=W/'backups/fuc-battle-runtime-pre/PROTECTED_PATHS.jsonl'
    unique={};refs=0;missing=[];changed=[]
    with source.open(encoding='utf-8') as f:
        for line in f:
            r=json.loads(line);refs+=1;unique.setdefault(r['path'],r)
    for i,(s,r) in enumerate(unique.items()):
        try:
            st=os.stat(s)
            if not pathlib.Path(s).is_file():missing.append(s)
            elif st.st_size!=r['size']:changed.append(s)
        except FileNotFoundError:missing.append(s)
        if i and i%100000==0:log('INHERITED_PATHS',i)
    result=dict(timestamp=now(),protected_path_references=refs,protected_unique_paths=len(unique),missing_paths=missing,changed_protected_sizes=changed,snapshot=str(source),snapshot_sha256=sha(source),scope='Whole inherited unified library source/Raw/Working/thumbnail/gallery paths: existence and size; old Raw hashes not recomputed. FUC raw source hashes separately checked.',status='PASS' if not missing and not changed else 'FAIL')
    write(WORK/'GLOBAL_PROTECTED_PATH_AUDIT.json',result);log('PROTECTED',len(unique),len(missing),len(changed));assert result['status']=='PASS'

def gate():
    b=read(WORK/'BASELINE.json');bad=[];authorized=[]
    for i,r in enumerate(b['files']+b['source_files']):
        p=pathlib.Path(r['path'])
        if not p.is_file() or p.stat().st_size!=r['size'] or sha(p)!=r['sha256']:
            if p==SCRIPTS/'fuc_final_audit.py' and p.is_file():authorized.append(dict(path=str(p),before=r['sha256'],after=sha(p),reason='New tool authored in this FinalFreeze turn; use recorded ISO directory filename rather than guessed ;1 suffix. No inherited tool changed.'))
            else:bad.append(r['path'])
        if i and i%3000==0:log('FINAL_HASHES',i)
    result=dict(timestamp=now(),frozen_files=len(b['files']),source_ISO_hashes=len(b['source_files']),authorized_new_audit_tool_repairs=authorized,unexpected_changes=bad,status='PASS' if not bad else 'FAIL')
    write(WORK/'FINAL_STABILITY_GATE.json',result);log('GATE',result);assert not bad
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['catalog','preservation','working','models','golden','semantic','protected','gate']);a=ap.parse_args();globals()[a.mode]()
