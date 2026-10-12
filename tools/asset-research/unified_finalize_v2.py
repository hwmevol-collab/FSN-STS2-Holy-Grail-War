from unified_common import *
import shutil
from unified_report import report

qa=read(S/'Reports/SEMANTIC_DATA_QA.json')
stable=read(S/'Reports/SEMANTIC_STABILITY.json')
selection=read(S/'Reports/SELECTION_EXPORT_ACTUAL_QA.json')
summary=read(S/'Metadata/SEMANTIC_FINAL_SUMMARY.json')
assert qa['status']=='PASS' and all(qa['checks'].values())
assert summary['semantic_catalog_revision']=='v2'
assert stable['status']=='PASS' and selection['status']=='PASS' and selection['semantic_revision']=='v2'
log=read(S/'Reports/UI_ACTION_LOG.json');checks=log['checks']
labels=[x for x in checks if x['action']=='v2_source_local_label']
assert labels and 'Other' in labels[-1]['text'] and '具体人物身份与跨源归一仍待按需确认' in labels[-1]['text']
assert {x['query'] for x in checks if x['action']=='v2_major_entity_regression'}=={'Rin','Lancer'}
assert any(x['action']=='v2_selection_export' and '921B504052A77F97CD9A6C10' in x['href'] for x in checks)
assert any(x['action']=='v2_final_workbench' and '4' in x['basket'] for x in checks)
ui=read(S/'Reports/BROWSER_ACTUAL_QA.json')
ui['prior_v1_acceptance']={'timestamp':ui['timestamp'],'database_sha256':ui['database_sha256'],'selection_export':ui['selection_export'],'query_set':ui['query_set'],'verified_actions':ui['verified_actions']}
ui.update(timestamp=now(),semantic_revision='v2',database_sha256=qa['database_sha256'],html_sha256=sha(S/'index.html'),selection_export=selection['selection_export'])
ui['verified_actions']=sorted(set(ui['verified_actions']+[x['action'] for x in checks if x['action'].startswith('v2_')]))
ui['revision_regression']='V2 changes only 72 source-local dictionary label classifications. All IDs, source evidence and relations are retained. Real UI verified the qualified Other label, Lancer and Rin coverage, the existing four-item basket and a new v2 export. Full v2 database QA passed.'
ui['UI_fixes_verified'].append('Unresolved FHA dictionary speaker labels visibly marked Other with identity/unification qualification')
ui['screenshots'].append(str(Path(r'C:\Users\Murasame\Documents\Codex\2026-10-07\files-pasted-by-the-user-unified\outputs\semantic-source-label-v2.png')))
dump(S/'Reports/BROWSER_ACTUAL_QA.json',ui)
qa['previous_browser_report_at_QA_start']=qa['browser_actual_QA']
qa['browser_actual_QA']=ui;qa['browser_report_refreshed_after_ui_regression']=True
dump(S/'Reports/SEMANTIC_DATA_QA.json',qa)
marker=report()
assert marker['status']=='FSN_MASTER_ASSET_LIBRARY_COMPLETE_FOR_MOD_DEVELOPMENT' and marker['semantic_revision']=='v2'
dump(S/'Revisions/REVISION_LEDGER.json',{'current':'v2','frozen_revisions':['v1','v2'],'v1_superseded_by':'v2','v2_reason':'72 unresolved FHA dictionary speaker labels corrected to Other / source_local_speaker_label. All 152 entity IDs, source evidence, aliases and relations preserved.','classification_history':str(S/'Metadata/ENTITY_CLASSIFICATION_HISTORY.json'),'timestamp':now()})
pending=S/'Reports/SEMANTIC_PENDING_ACCEPTANCE.json'
if pending.exists():dump(pending,{'status':'RESOLVED','resolved_by':'v2 PASS','final_marker':str(L/'FSN_MASTER_ASSET_LIBRARY_COMPLETE_FOR_MOD_DEVELOPMENT.json'),'timestamp':now()})
out=Path(r'C:\Users\Murasame\Documents\Codex\2026-10-07\files-pasted-by-the-user-unified\outputs')
for path in [L/'Reports/FSN_SEMANTIC_CATALOG_USAGE.md',L/'Reports/UNIFIED_FSN_SEMANTIC_CATALOG_REPORT.md',L/'FSN_MASTER_ASSET_LIBRARY_COMPLETE_FOR_MOD_DEVELOPMENT.json',S/'Exports/MOD_SELECTION_MANIFEST.json',S/'Reports/SEMANTIC_DATA_QA.json',S/'Reports/SEMANTIC_STABILITY.json',S/'Reports/BROWSER_ACTUAL_QA.json',S/'Reports/SELECTION_EXPORT_ACTUAL_QA.json',S/'Metadata/SEMANTIC_FINAL_SUMMARY.json',S/'Metadata/ENTITY_CLASSIFICATION_HISTORY.json']:
    shutil.copy2(path,out/path.name)
print('FINAL V2 CLOSURE COMPLETE')
