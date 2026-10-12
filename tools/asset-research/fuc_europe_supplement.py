from fuc_common import *
from fuc_europe_index import EU
def run():
    md=EU/'Metadata';rows=rowsjson(md/'ASSETS.jsonl');primary={(r['source_container'],r['source_logical_path']):r for r in rows if r['asset_kind']=='fpk_payload'};byparent=collections.defaultdict(list);groups=collections.defaultdict(list)
    for r in rows:
        groups[r['source_container']].append(r)
        if r['parent_asset_id']:byparent[r['parent_asset_id']].append(r)
    for filename,pathfield,containerfield in [('CHARACTER_ASSET_MAP.csv','asset_name','container'),('FONT_INDEX.csv','source',None)]:
        rs=readrows(md/filename)
        for r in rs:
            match=primary.get((r.get(containerfield,''),r[pathfield])) if containerfield else next((a for a in rows if a['source_logical_path']==r[pathfield] and a['asset_kind'] in {'iso_file','fpk_payload'}),None)
            r['asset_id']=match['asset_id'] if match else '';r['model_id']=match['model_id'] if match else ''
        csvwrite(md/filename,rs)
    effects=[];stages=[]
    for r in rows:
        if r['asset_kind']!='fpk_payload':continue
        candidates=groups[r['source_container']]
        if r['source_logical_path'].startswith('eft/'):
            effects.append(dict(asset_id=r['asset_id'],effect_resource=r['source_logical_path'],source_container=r['source_container'],physical_path=r['extracted_path'],sha256=r['sha256'],detected_format=r['detected_format'],co_container_textures=';'.join(a['asset_id'] for a in candidates if a['category']=='Textures'),co_container_models=';'.join(a['asset_id'] for a in candidates if a['model_id'] and a['asset_kind']=='fpk_payload'),co_container_motion=';'.join(a['asset_id'] for a in candidates if a['asset_kind']=='mot_clip'),co_container_audio=';'.join(a['asset_id'] for a in candidates if a['category']=='Audio'),trigger_move='',character='unknown',association_status='CO_CONTAINER_CANDIDATES_ONLY',notes='All raw VFX components retained. Shared container is documented as a candidate association, not a proven timing/trigger/sound binding; BAM/TUV/MIL/PAR/FAN/AMO semantics remain unknown.'))
        if r['source_logical_path'].startswith(('stg/','stage/')):stages.append(dict(asset_id=r['asset_id'],stage_code=r['source_logical_path'].split('/')[1],resource=r['source_logical_path'],source_container=r['source_container'],physical_path=r['extracted_path'],sha256=r['sha256'],model_id=r['model_id'],working_path=r['converted_path'],child_texture_assets=';'.join(a['asset_id'] for a in byparent[r['asset_id']] if a['category']=='Textures'),stage_name='unknown',evidence='Actual internal stage code/path; no guessed location name'))
    csvwrite(md/'EFFECT_INDEX.csv',effects);csvwrite(md/'STAGE_INDEX.csv',stages)
    bones=readrows(md/'SOURCE_BONE_INDEX.csv');modelids=collections.defaultdict(list)
    for r in rows:
        if r['asset_kind']=='fpk_payload' and r['model_id']:modelids[r['sha256']].append(r['asset_id'])
    weapons=[]
    for b in bones:
        if re.search(r'(?i)(weapon|sword)',b['source_name']):weapons.append(dict(model_id='GMO_'+b['model_sha256'][:16],asset_ids=';'.join(modelids[b['model_sha256']]),source_subobject_name=b['source_name'],source_bone_ordinal=b['source_bone_ordinal'],glb_node_id=b['glb_node_id'],weapon_name='unknown',status='EXPLICIT_SOURCE_WEAPON_OR_SWORD_SUBOBJECT_CANDIDATE',evidence='Literal weapon/Sword name in actual GMO chunk; no Excalibur/GaeBolg/Fate identity inferred. Complete parent GMO and GLB contain the component.'))
    csvwrite(md/'WEAPON_MODEL_INDEX.csv',weapons,['model_id','asset_ids','source_subobject_name','source_bone_ordinal','glb_node_id','weapon_name','status','evidence'])
    for b in bones:b['model_id']='GMO_'+b['model_sha256'][:16];b['asset_ids']=';'.join(modelids[b['model_sha256']])
    csvwrite(md/'SOURCE_BONE_INDEX.csv',bones)
    unknown=[];clusters=collections.defaultdict(list)
    for r in rows:
        if r['asset_kind'] not in {'iso_file','fpk_payload'} or not r['size'] or (r['detected_format']!='UNKNOWN' and not r['conversion_status'].startswith('unresolved')):continue
        sample=pathlib.Path(r['extracted_path']).open('rb').read(65536);freq=collections.Counter(sample);ent=-sum(v/len(sample)*math.log2(v/len(sample)) for v in freq.values()) if sample else 0
        u=dict(asset_id=r['asset_id'],asset=r['source_logical_path'],container=r['source_container'],path=r['extracted_path'],size=r['size'],sha256=r['sha256'],magic=sample[:16].hex(),first_64_bytes=sample[:64].hex(),entropy=ent,probable_format=r['extension'],cluster=r['extension']+':'+sample[:4].hex(),status='UNKNOWN_COMPLETE_BYTES_PRESERVED',notes='Not ignored. MOT channels and PPHD/PBD audio are decoded and excluded from this unresolved-format list; their remaining binding limitations are documented separately.');unknown.append(u);clusters[u['cluster']].append(u)
    csvwrite(md/'FUC_UNKNOWN_FORMATS.csv',unknown);csvwrite(md/'UNKNOWN_CLUSTERS.csv',sorted([dict(cluster=k,count=len(rs),bytes=sum(r['size'] for r in rs),example=rs[0]['asset']) for k,rs in clusters.items()],key=lambda x:x['bytes'],reverse=True))
    from fuc_europe_integrate import append_csv_exact,STAGE
    combined_unknown=[dict(r,file=r['path'],source_container=r['container'],first_64_bytes_hex=r['first_64_bytes']) for r in unknown]
    append_csv_exact(BACK/'Metadata/UNKNOWN_FORMATS.csv',STAGE/'UNKNOWN_FORMATS.csv',combined_unknown);os.replace(STAGE/'UNKNOWN_FORMATS.csv',L/'Metadata/UNKNOWN_FORMATS.csv')
    # SHA comparisons include all Europe image/audio logical views, original payload and Working Copy.
    old=collections.defaultdict(list);db=sqlite3.connect(f'file:{(BACK/"Metadata/ASSET_CATALOG.sqlite").as_posix()}?mode=ro',uri=True)
    for aid,v,h,wh in db.execute('SELECT asset_id,source_version,sha256,working_sha256 FROM assets'):
        if h:old[h].append((aid,v,'preservation'))
        if wh and wh!=h:old[wh].append((aid,v,'working'))
    oldgmo=db.execute("SELECT COUNT(*) FROM assets WHERE lower(detected_format)='gmo'").fetchone()[0];db.close();comparisons=[];compared=0
    for r in rows:
        if r['category'] not in {'Textures','Image','Audio'} and r['detected_format']!='GMO':continue
        if not r['size']:continue
        compared+=1;seen=set()
        for h,side in [(r['sha256'],'preservation'),(r['working_sha256'],'working')]:
            for aid,v,kind in old.get(h,[]):
                if aid in seen:continue
                seen.add(aid);comparisons.append(dict(fuc_asset_id=r['asset_id'],fuc_source=r['source_logical_path'],fuc_container=r['source_container'],fuc_sha256=h,other_asset_id=aid,other_source=v,relation='exact_payload',evidence='Exact SHA256 of '+side+' equals existing '+kind+'; equality does not establish a character/action semantic label'))
        if r['detected_format']=='GMO' and oldgmo==0:comparisons.append(dict(fuc_asset_id=r['asset_id'],fuc_source=r['source_logical_path'],fuc_container=r['source_container'],fuc_sha256=r['sha256'],other_asset_id='',other_source='Original/Remastered/HollowAtaraxia',relation='FUC_unique',evidence='Format inventory: previous three sources contain no GMO models. No claim that analogous visual designs never exist in other formats.'))
    csvwrite(md/'FSN_VS_FUC.csv',comparisons,['fuc_asset_id','fuc_source','fuc_container','fuc_sha256','other_asset_id','other_source','relation','evidence']);shutil.copy2(md/'FSN_VS_FUC.csv',L/'Metadata/FSN_VS_FUC.csv')
    jsonwrite(md/'CROSS_SOURCE_SUMMARY.json',dict(existing_catalog_rows=246605,logical_image_audio_model_assets_compared=compared,exact_payload_relations=sum(r['relation']=='exact_payload' for r in comparisons),FUC_unique_GMO_rows=sum(r['relation']=='FUC_unique' for r in comparisons),perceptual_or_pcm_similarity='Not asserted; SHA comparison does not prove or disprove visual/audio resemblance'))
    refs=readrows(FW/'Japan_Recovery/FUC_TEXTURE_EXTERNAL_REFERENCE.csv')
    for r in refs:r['notes']='Audited USA/EU external HD reference only. Europe source verified, but no local runtime texture-hash match has been established. No external upscale image copied into preservation.'
    csvwrite(md/'FUC_TEXTURE_EXTERNAL_REFERENCE.csv',refs);csvwrite(md/'FUC_TEXTURE_EXTERNAL_MAPPING.csv',[],['asset_id','game_texture','texture_hash','external_category','external_name','evidence_source','confidence','notes'])
    audit=readjson(FW/'Japan_Recovery/TOOLS_AUDIT.json');audit['source_version']='FateUnlimitedCodesPortable_Europe';audit['ppsspp']=readjson(STAGE_ROOT/'Executable/DECRYPT_EVIDENCE.json');audit['ppsspp']['official_download']='https://www.ppsspp.org/files/1_20_4/ppsspp_win.zip';audit['ppsspp']['download_sha256']=sha(W/'tools/ppsspp-isolated/ppsspp_win_1.20.4.zip');audit['recomp_audit']['eboot']='Actual complete Europe ISO hash matches documented NPEH00007 1.01 input; official PPSSPP dump ELF independently hashed and locally indexed.';audit['motion_parser']=dict(reference='https://github.com/NicholasMoser/GNTool',commit=subprocess.check_output(['git','-C',str(W/'repos/fuc-gntool-reference'),'rev-parse','HEAD']).decode().strip(),files=['BoneAnimation.java','Coordinate.java','TrackFlag.java'],adaptation='Local bounded big-endian channel reader; float32/high16 byte-exact coordinate roundtrips; no Naruto names or animation semantics reused',limitations='FUC bone binding, interpolation, rotation interpretation, FAN/AMO and VFX timing remain unverified');audit['fpk_audit']['validation']='All 542 archives / all 6558 entries independently decoded with strict PRS or literal branch; exact declared length and SHA256 compared to extracted bytes.';audit['noesis']['custom_bone_export_attempt']='Experimental Python .fba/.fsnbones export did not produce the registered JSON format in CLI mode; not used. Bounded original GMO chunk walker and exact GLB bone names used instead; bN ordinal mapping remains explicitly provisional.'
    audit['vgmstream']=dict(version='r2117',official_source='https://github.com/vgmstream/vgmstream/releases/tag/r2117',header_format_source='https://github.com/vgmstream/vgmstream/blob/r2117/src/meta/pphd.c',VAG_note='FFmpeg VAG version-4 stereo assumption was rejected; vgmstream mono metadata/sample counts used for every VAG',PPHD='17 empty PPVA slots kept; 1961 active streams across 43 banks, 1623 unique payload+sample-rate Working Copies')
    jsonwrite(md/'TOOLS_AUDIT.json',audit);jsonwrite(L/'Reports/FUC_TOOLS_AUDIT.json',audit)
    for name in ['MODEL_SUMMARY.json','AUDIO_SUMMARY.json','TEXTURE_SUMMARY.json']:
        s=readjson(md/name);s['status']='FORMAL_EUROPE_SOURCE_INTEGRATED';s.pop('stage_status',None)
        if name=='MODEL_SUMMARY.json':s.update(original_gmo_transform_bone_rows=len(bones),weighted_skin_bone_rows=2642,full_skeleton_preserved=True)
        jsonwrite(md/name,s)
    sheets=readrows(BACK/'Metadata/CONTACT_SHEETS.csv');missing_sheets=[r['contact_sheet'] for r in sheets if not pathlib.Path(r['contact_sheet']).is_file()];oldreports=[r['path'] for r in readjson(BACK/'BASELINE.json')['files'] if pathlib.Path(r['path']).is_relative_to(L/'Reports') and sha(r['path'])!=r['sha256']]
    assert not missing_sheets and not oldreports
    state=readjson(L/'Reports/FUC_STABILITY_VERIFICATION.json');state.update(old_contact_sheet_path_loss=0,old_contact_sheet_rows_preserved=len(sheets),old_report_file_hash_changes=oldreports);jsonwrite(L/'Reports/FUC_STABILITY_VERIFICATION.json',state);jsonwrite(md/'STABILITY_VERIFICATION.json',state)
    scripts=[p for p in (W/'scripts').glob('fuc_*.py')]+[W/'scripts/FUC_ASSETS.ps1',W/'scripts/fuc_europe_decrypt.ps1'];csvwrite(md/'REPRODUCIBILITY_MANIFEST.csv',[dict(path=str(p),size=p.stat().st_size,sha256=sha(p)) for p in scripts if p.exists()])
    summary=dict(effect_resources=len(effects),stage_resources=len(stages),stage_codes=sorted({r['stage_code'] for r in stages}),weapon_subobject_candidates=len(weapons),unknown_resources=len(unknown),unknown_bytes=sum(r['size'] for r in unknown),external_reference_hashes=len(refs),verified_external_mappings=0,raw_character_codes=sorted({r['character_code'] for r in rows if r['character_code']}),named_character_roster_verified=False,source_version='FateUnlimitedCodesPortable_Europe');jsonwrite(md/'SEMANTIC_COVERAGE_SUMMARY.json',summary);log('EUROPE SUPPLEMENT',summary)
if __name__=='__main__':run()
