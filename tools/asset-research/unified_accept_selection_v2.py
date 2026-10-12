from unified_common import *
import shutil

p=S/'Exports/MOD_SELECTION_MANIFEST_SELECTION-921B504052A77F97CD9A6C10.json'
m=read(p)
expected=['FSN206832','FSN258247','ANI-FSN270475-V1-P000004849261','CM_III_0121']
assert m['semantic_revision']=='v2' and m['media_copied'] is False
assert [x['source_id'] for x in m['selections']]==expected
assert [x['source_type'] for x in m['selections']]==['asset','asset','shot','page']
c=ro(DB);c.row_factory=sqlite3.Row
for x in m['selections']:
    assert Path(x['source_path']).is_file()
    assert x['reason'] and x['notes'] and x['evidence_ids']
    assert c.execute('select 1 from entities where entity_id=?',(x['entity']['entity_id'],)).fetchone()
    assert c.execute('select 1 from source_subjects where semantic_subject_id=? and native_id=?',(x['semantic_subject_id'],x['source_id'])).fetchone()
    assert c.execute('select 1 from relations where relation_id=?',(x['relation_id'],)).fetchone()
    for ev in x['evidence']:
        actual=c.execute('select * from evidence where evidence_id=?',(ev['evidence_id'],)).fetchone()
        assert dict(actual)==ev
        assert ev['source_locator'] and ev['provenance'] and Path(ev['source_path']).is_file()
shot=m['selections'][2];page=m['selections'][3]
assert shot['media_asset_id']=='FSN270475' and shot['timecode']=='01:20:49.261'
assert shot['end_timecode']=='01:21:31.053' and shot['source_sha256'] and shot['helper_command']
assert page['page_asset_id']=='FSN269424'
assert m['selections'][1]['evidence_grade']['original_status']=='confirmed_runtime'
assert any(x['original_status']=='confirmed_runtime' for x in m['selections'][1]['evidence'])
c.close()
latest=S/'Exports/MOD_SELECTION_MANIFEST.json';shutil.copy2(p,latest)
dump(S/'Reports/SELECTION_EXPORT_ACTUAL_QA.json',{'status':'PASS','timestamp':now(),'semantic_revision':'v2','origin':'Actual in-app browser UI export','selection_export':str(p),'latest_alias':str(latest),'latest_alias_created':'Copied verified immutable UI export; current service was started before the automatic alias-writing change. Future launcher starts use automatic alias writing.','media_copied':False,'source_ids':expected,'types':['image','FUC validated animation','shot','official page'],'paths_and_evidence_resolve':True,'raw_database_evidence_matches':True})
print('V2 ACTUAL SELECTION EXPORT PASS')
