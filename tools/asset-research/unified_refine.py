"""Finalize derived presentation from existing explicit evidence; source metadata stays untouched."""
from unified_common import *
from unified_build import Build
def refine(revision=None):
    b=Build(revision or read(S/'Metadata/SEMANTIC_FINAL_SUMMARY.json')['semantic_catalog_revision'])
    b.skipped.update(read(S/'Metadata/SEMANTIC_FINAL_SUMMARY.json').get('skipped',{}))
    # Unresolved voice-dictionary captions do not establish independent character identities.
    label_changes=[]
    for entity in b.c.execute("select * from entities where created_from like '%CHARACTER_VOICE_CODES.csv#%' and entity_type='Character'").fetchall():
        label_changes.append({'entity_id':entity['entity_id'],'label':entity['preferred_label'],'old_type':entity['entity_type'],'new_type':'Other','old_scope':entity['scope'],'new_scope':'FSN_DIRECT_EXTENSION','revision':b.revision,'reason':'Source-local voice dictionary label; independent character identity and alias unification are unresolved.'})
        b.c.execute("update entities set entity_type='Other',scope='FSN_DIRECT_EXTENSION',status='source_local_speaker_label',notes=? where entity_id=?",('FHA source-local speaker label. Specific individual identity and alias unification remain unresolved; original dictionary and stable ID retained.',entity['entity_id']))
    if label_changes:
        history_path=S/'Metadata/ENTITY_CLASSIFICATION_HISTORY.json'
        history=read(history_path) if history_path.exists() else []
        existing={x['entity_id']+':'+x['revision'] for x in history}
        history.extend(x for x in label_changes if x['entity_id']+':'+x['revision'] not in existing)
        dump(history_path,history)
    manual=S/'Metadata/MANUAL_REVIEW_ADDITIONS.jsonl'
    if manual.exists():
        for line in manual.read_text(encoding='utf-8-sig').splitlines():
            if not line.strip():continue
            r=json.loads(line)
            if r.get('revision')!=b.revision:continue
            if r.get('decision') not in ('confirmed_manual','rejected') or not r.get('reviewer') or not r.get('raw_text'):raise ValueError('Manual review requires explicit decision, reviewer, raw_text and revision.')
            subject=b.c.execute('select * from source_subjects where semantic_subject_id=?',(r['semantic_subject_id'],)).fetchone()
            if not subject:raise ValueError('Manual review subject is not registered.')
            ev=b.ev(manual,r['review_id'],r,subject['source_version'],'manual_review',r['decision'],raw=r['raw_text'],notes='Explicit on-demand manual review; previous evidence retained.')
            if r['decision']=='rejected':
                rid=r['relation_id'];old=b.c.execute('select 1 from relations where relation_id=?',(rid,)).fetchone()
                if not old:raise ValueError('Rejected relation not found.')
                b.c.execute('insert or ignore into relation_evidence values(?,?)',(rid,ev));b.c.execute('update relations set status=? where relation_id=?',('rejected',rid));b.c.execute('insert or ignore into relation_history values(?,?,?,?,?)',(ident('HIS',rid,b.revision,ev,'rejected'),rid,b.revision,'rejected',ev))
            else:
                if r.get('predicate') not in ('depicted_in','appears_in'):raise ValueError('Manual visual confirmation requires depicted_in / appears_in; no invented game mechanics.')
                b.relation(r['entity_id'],r['predicate'],subject['semantic_subject_id'],ev,'confirmed_manual',r['raw_text'])
    # Source-observed spellings take precedence over a previous index's derived canonical label.
    for r in rows(O/'OFFICIAL_MATERIAL_ENTITY_ALIASES.csv'):
        if not json.loads(r['source_pages']) or r['status']=='search_alias_only':continue
        eid=b.resolve(r['entity'])
        if not eid:continue
        b.c.execute('update entities set preferred_label=?,preferred_language=?,notes=? where entity_id=?',(r['alias'],'ja' if any(ord(c)>127 for c in r['alias']) else 'en','Display spelling observed in local official source; previous canonical/search labels retained as aliases.',eid))
    for r in rows(F/'SemanticMapping/FUC_CHARACTER_CODE_MAP.csv'):
        eid=b.resolve(r['internal_code'])
        if eid:b.c.execute('update entities set preferred_label=?,preferred_language=?,notes=? where entity_id=?',(r['display_name'],'en','Display spelling from frozen FUC '+r['display_name_source']+'; original evidence scope retained.',eid))
    p=L/'Metadata/SCRIPT_INDEX.csv';routes={}
    for r in rows(p):
        if not r['route'] or r['route'].lower()=='unknown':continue
        if r['route'] not in routes:
            eid=b.entity(r['route'],'Route',p,'route:'+r['route']);ev=b.ev(p,'route:'+r['route'],r,r['source_version'],'script_reference','source_route_index',raw=r['route'])
            b.alias(eid,r['route'],ev,p,'source_route_index','source_spelling');routes[r['route']]=eid
        a=b.c.execute("select semantic_subject_id from source_subjects where subject_type='asset' and native_id=? and source_version=?",(r['script_id'],r['source_version'])).fetchone()
        if a:
            ev=b.ev(p,'route:'+r['script_id'],r,r['source_version'],'script_reference','source_route_index',raw=r['route'])
            b.relation(routes[r['route']],'has_route_script',a[0],ev,'source_route_index','Existing route field; no route inferred from character name.')
    for path,version in [(F/'ANIMATION_MODEL_BINDING_CANDIDATES.csv','FateUnlimitedCodesPortable_Europe'),(O/'OFFICIAL_MATERIAL_VISUAL_SIMILARITY.csv','OfficialMaterial')]:
        for r in rows(path):
            native=r.get('page_a',r.get('animation_id',''))
            subject=b.c.execute('select semantic_subject_id from source_subjects where native_id=? limit 1',(native,)).fetchone()
            b.review(path,ident('ROW',r),r,version,r.get('status','candidate'),subject[0] if subject else None,reason=r.get('evidence','Existing source candidate; not promoted.'))
    p=F/'SemanticMapping/FUC_MOVE_SOUND_MAP.csv'
    for r in rows(p):
        if r['classification']!='Voice' or r['request_status']!='confirmed_runtime':continue
        eid=b.resolve(r['character']);subject=b.c.execute("select * from source_subjects where subject_type='asset' and native_id=?",(r['audio_asset'],)).fetchone()
        if eid and subject:
            ev=b.ev(p,r['move_id']+':observed_voice',r,'FateUnlimitedCodesPortable_Europe','runtime_confirmed',r['request_status'],notes=r['classification_status']+'; alternatives stay unknown.')
            b.relation(eid,'has_observed_voice_sample',subject['semantic_subject_id'],ev,r['request_status'],r['notes'])
            b.c.execute('insert or ignore into entity_asset_links values(?,?,?,?,?,?,?,?,?,?)',(ident('LNK',eid,r['audio_asset'],ev,'voice'),eid,r['audio_asset'],'voice',r['request_status'],ev,'FateUnlimitedCodesPortable_Europe',subject['payload'],r['notes'],subject['semantic_subject_id']))
    # Aggregate status only from an explicitly stronger existing source record; retain every candidate row/history.
    for r in b.c.execute('select r.relation_id,r.status,r.best_evidence_grade,e.status as evidence_status,e.semantic_strength,e.evidence_id from relations r join relation_evidence re on re.relation_id=r.relation_id join evidence e on e.evidence_id=re.evidence_id where e.semantic_strength>r.best_evidence_grade and e.status in (\'confirmed_runtime\',\'confirmed_manual\',\'confirmed_ui\',\'confirmed_exact_hash\')').fetchall():
        b.c.execute('update relations set status=?,best_evidence_grade=?,notes=notes||? where relation_id=?',(r['evidence_status'],r['semantic_strength'],'; stronger direct source evidence attached; previous candidate evidence/history retained.',r['relation_id']))
    # Direct-source evidence may share a relation with a previously indexed path candidate.
    for r in b.c.execute("select r.relation_id,r.status,e.status as evidence_status,e.semantic_strength from relations r join relation_evidence re on re.relation_id=r.relation_id join evidence e on e.evidence_id=re.evidence_id where r.status like '%candidate%' and e.status='confirmed_runtime' and e.semantic_strength=5").fetchall():
        b.c.execute('update relations set status=?,notes=notes||? where relation_id=?',(r['evidence_status'],'; confirmed only by attached direct runtime evidence; original path candidate retained.',r['relation_id']))
    b.c.commit();b.usage();b.finish(incremental=True)
if __name__=='__main__':
    import sys
    refine(sys.argv[1] if len(sys.argv)>1 else None)
