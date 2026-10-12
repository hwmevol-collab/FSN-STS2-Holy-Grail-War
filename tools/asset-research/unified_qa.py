from unified_common import *
from unified_server import search,details,manifest
import time, collections, re
def shuffled_seed_replay(c):
    import unified_build as module,random
    m=sqlite3.connect(':memory:');m.row_factory=sqlite3.Row;m.executescript(module.SCHEMA)
    for table in ['revisions','entities','evidence','aliases','cross_source_links']:
        if table=='evidence':records=c.execute('select * from evidence where evidence_id in (select evidence_id from aliases)').fetchall()
        elif table=='cross_source_links':records=c.execute('select * from cross_source_links where evidence_id in (select evidence_id from aliases)').fetchall()
        else:records=c.execute('select * from '+table).fetchall()
        if records:m.executemany('insert into '+table+' values('+','.join('?'*len(records[0]))+')',[tuple(r) for r in records])
    b=object.__new__(module.Build);b.c=m;b.revision=read(S/'Metadata/SEMANTIC_FINAL_SUMMARY.json')['semantic_catalog_revision'];b.registry=read(S/'Metadata/IMMUTABLE_ID_REGISTRY.json');b.entities={};b.lookup=collections.defaultdict(set);b.source_codes={}
    for r in m.execute('select entity_id,normalized_alias from aliases'):b.lookup[r['normalized_alias']].add(r['entity_id'])
    before=set(tuple(r) for r in m.execute('select entity_id,entity_type from entities'))
    original=module.rows
    def shuffled(p):
        data=list(original(p));random.Random(731).shuffle(data);yield from data
    try:module.rows=shuffled;b.seeds();after=set(tuple(r) for r in m.execute('select entity_id,entity_type from entities'))
    finally:module.rows=original;m.close()
    return before==after
def qa():
    print('Checking semantic database integrity',flush=True);c=ro(DB);c.row_factory=sqlite3.Row;checks={}
    c.execute('pragma cache_size=-262144');c.execute('pragma temp_store=MEMORY')
    checks['integrity_check']=c.execute('pragma integrity_check').fetchone()[0]=='ok'
    checks['foreign_key_check_empty']=not c.execute('pragma foreign_key_check').fetchall()
    print('Checking native reference resolution and provenance',flush=True)
    main=ro(L/'Metadata/ASSET_CATALOG.sqlite');native=set(x[0] for x in main.execute('select asset_id from assets'));main.close()
    shots=set(r['shot_id'] for r in rows(A/'ANIMATION_SHOT_INDEX.csv'));pages={r['page_id']:r['page_asset_id'] for r in rows(O/'OFFICIAL_MATERIAL_PAGE_INDEX.csv')};moves={r['move_id'] for r in rows(F/'SemanticMapping/FUC_MOVE_INDEX.csv')}
    checks['asset_links_no_dangling']=all(r[0] in native for r in c.execute('select asset_id from entity_asset_links'))
    checks['shot_links_no_dangling']=all(r[0] in shots and r[1] in native for r in c.execute('select shot_id,media_asset_id from entity_shot_links'))
    checks['page_links_no_dangling']=all(pages.get(r[0])==r[1] and r[1] in native for r in c.execute('select page_id,page_asset_id from entity_page_links'))
    checks['FUC_move_subjects_no_dangling']=all(r[0] in moves for r in c.execute("select native_id from source_subjects where subject_type='fuc_move'"))
    checks['no_unproven_relations']=c.execute('select count(*) from relations where evidence_count=0').fetchone()[0]==0
    checks['evidence_original_grades_retained']=c.execute("select count(*) from evidence where original_status!=status or original_evidence_type='' or provenance='' or source_locator='' or source_path=''").fetchone()[0]==0
    checks['mentions_never_depictions']=c.execute("select count(*) from relations r join relation_evidence re on re.relation_id=r.relation_id join evidence e on e.evidence_id=re.evidence_id where r.predicate in ('depicted_in','appears_in') and e.evidence_type in ('subtitle_exact','source_text_alias','official_page_text','source_text_exact')").fetchone()[0]==0
    checks['candidate_evidence_strength_never_promoted']=c.execute("select count(*) from evidence where original_status like '%candidate%' and semantic_strength>1").fetchone()[0]==0
    checks['strength_preserves_runtime_vs_table']=c.execute("select count(*) from evidence where evidence_type='runtime_confirmed' and status='confirmed_runtime' and semantic_strength!=5").fetchone()[0]==0 and c.execute("select count(*) from evidence where evidence_type='table_confirmed' and status='confirmed_table' and semantic_strength!=3").fetchone()[0]==0
    checks['normalization_preserves_kana_and_accents']=norm('Gáe Bolg')==norm('Gae Bolg') and norm('Ｌａｎｃｅｒ')==norm('Lancer') and norm('ゲイ')!=norm('ケイ')
    registry=read(S/'Metadata/IMMUTABLE_ID_REGISTRY.json');checks['entity_registry_ids_resolve']=all(c.execute('select 1 from entities where entity_id=?',(v,)).fetchone() for v in registry['entity_keys'].values())
    checks['opaque_ids_not_ordered_names']=all(re.fullmatch('ENT-[0-9A-F]{24}',r[0]) for r in c.execute('select entity_id from entities'))
    checks['unresolved_FHA_speaker_labels_not_characters']=c.execute("select count(*) from entities where created_from like '%CHARACTER_VOICE_CODES.csv#%' and entity_type='Character'").fetchone()[0]==0
    checks['FHA_speaker_labels_scoped_and_qualified']=c.execute("select count(*) from entities where status='source_local_speaker_label' and (entity_type!='Other' or scope!='FSN_DIRECT_EXTENSION')").fetchone()[0]==0
    previous=S/'Revisions/v1/Database/FSN_SEMANTIC.sqlite'
    if not previous.exists():previous=S/'Revisions/v1/FSN_SEMANTIC.sqlite'
    if previous.exists():
        old=ro(previous);checks['all_v1_entity_ids_preserved']=set(r[0] for r in old.execute('select entity_id from entities'))<=set(r[0] for r in c.execute('select entity_id from entities'));old.close()
    print('Replaying entity seeds in shuffled order against immutable registry',flush=True)
    checks['shuffled_entity_seed_replay_stable']=shuffled_seed_replay(c)
    gold={}
    for q in ['Saber','Rin','Lancer','Archer','Sakura','Rin + Jewel','Lancer + Gae Bolg','Archer + Projection','Saber + Avalon','遠坂凛','ランサー','ゲイ・ボルク','宝石','投影','Avalon','lan:state:145','FSN248770']:
        t=time.perf_counter();d=search(c,{'q':[q]});gold[q]={'entity_ids':[e['entity_id'] for e in d['entities']],'total':d['total'],'elapsed_ms':round((time.perf_counter()-t)*1000,1),'coverage':d['coverage']};checks['search_'+q]=bool(d['results'])
    for q in ['Lancer','Rin','Saber','Archer']:
        d=search(c,{'q':[q]});coverage=list(d['coverage'].values())[0];checks['cross_source_'+q]=sum(n>0 for n in coverage.values())>=3
    for q in ['Rin + Jewel','Lancer + Gae Bolg','Archer + Projection','Saber + Avalon']:
        d=search(c,{'q':[q],'mode':['shared']});checks['shared_query_'+q]=len(d['entities'])>=2
    for f in FAMILIES:
        d=search(c,{'q':['Lancer'],'source':[f]});checks['source_filter_'+f]=all(r['source_family']==f for r in d['results'])
    for sc in ['FSN_CORE','FSN_DIRECT_EXTENSION','PARODY_COMEDY','FATE_RELATED_REFERENCE']:
        d=search(c,{'q':['Lancer'],'scope':[sc]});checks['scope_filter_'+sc]=all(r['scope']==sc for r in d['results'])
    for status,display in [('confirmed','Confirmed'),('mention','Mention Only'),('candidate',None)]:
        d=search(c,{'q':['Lancer'],'status':[status]});checks['status_filter_'+status]=bool(d['results']) and all(r['display_status']==display if display else 'Candidate' in r['display_status'] for r in d['results'])
    checks['golden_state145_unnamed']=bool(c.execute("select 1 from source_subjects where native_id='lan:state:145' and subject_type='fuc_move' and json_extract(payload,'$.display_name')=''" ).fetchone())
    checks['Rin_Gand_Shot_bound']=bool(c.execute("select 1 from entities e join relations r on r.subject_entity_id=e.entity_id join source_subjects s on r.object_subject_id=s.semantic_subject_id where e.entity_type='Move' and e.preferred_label='Gand Shot' and s.native_id='rin:state:159'").fetchone())
    checks['Lancer_equipment_runtime']=bool(c.execute("select 1 from relations r join source_subjects s on r.object_subject_id=s.semantic_subject_id where r.predicate='has_equipment_model' and s.native_id='FSN248770' and r.status='confirmed_runtime'").fetchone())
    gae=search(c,{'q':['Gae Bolg']})['entities'];ids=[e['entity_id'] for e in gae]
    checks['no_invented_Gae_Bolg_equipment_identity']=not ids or c.execute("select count(*) from relations where subject_entity_id in ("+','.join('?'*len(ids))+") and object_id='FSN248770' and predicate!='mentioned_in'",ids).fetchone()[0]==0
    samples=[]
    for params in [{'q':['Rin'],'kind':['asset'],'source':['HollowAtaraxia'],'usage':['card_art']},{'q':['Lancer'],'kind':['asset'],'usage':['battle_animation'],'status':['confirmed']},{'q':['Lancer'],'kind':['shot']},{'q':['Rin'],'kind':['page']}]:
        d=search(c,params);checks['selection_'+str(len(samples))]=bool(d['results'])
        if d['results']:r=d['results'][0];samples.append({'relation_id':r['relation_id'],'subject_id':r['semantic_subject_id'],'usage_type':params.get('usage',['lore_reference'])[0]})
    obj=manifest(c,samples) if samples else {};checks['selection_manifest_four_kinds']=len(samples)==4 and len(obj['selections'])==4 and obj['media_copied'] is False and all(s['source_path'] and s['evidence_ids'] for s in obj['selections'])
    checks['all_source_families_have_evidence']=set(r[0] for r in c.execute('select distinct source_family from evidence'))==set(FAMILIES)
    print('Checking all referenced thumbnail / working source paths',flush=True)
    missing=[];checked=0
    for r in c.execute("select distinct s.semantic_subject_id,s.source_path,s.thumbnail from relations r join source_subjects s on s.semantic_subject_id=r.object_subject_id where r.subject_entity_id is not null"):
        for field in ['source_path','thumbnail']:
            if r[field]:
                checked+=1
                if not Path(r[field]).is_file():missing.append({'subject_id':r['semantic_subject_id'],'field':field,'path':r[field]})
    checks['entity_result_source_paths_resolve']=not missing
    ui_path=S/'Reports/BROWSER_ACTUAL_QA.json';ui=read(ui_path) if ui_path.exists() else {'status':'PENDING'}
    result={'status':'PASS' if all(checks.values()) else 'FAIL','timestamp':now(),'checks':checks,'searches':gold,'source_paths_checked':checked,'missing_paths':missing,'database_sha256':sha(DB),'browser_actual_QA':ui,'counts':{t:c.execute('select count(*) from '+t).fetchone()[0] for t in ['entities','aliases','relations','evidence','source_subjects','review_queue','usage_candidates']}}
    dump(S/'Reports/SEMANTIC_DATA_QA.json',result)
    if obj:dump(S/'Exports/MOD_SELECTION_MANIFEST_DATA_QA.json',obj)
    c.close();print(js({'status':result['status'],'failed':[k for k,v in checks.items() if not v],'counts':result['counts']}),flush=True);return result
if __name__=='__main__':
    import sys
    sys.exit(0 if qa()['status']=='PASS' else 1)
