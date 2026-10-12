from unified_common import *
q=read(S/'Reports/SEMANTIC_DATA_QA.json');u=read(S/'Reports/BROWSER_ACTUAL_QA.json');m=read(L/'FSN_MASTER_ASSET_LIBRARY_COMPLETE_FOR_MOD_DEVELOPMENT.json')
a=ro(DB);b=ro(S/'Revisions/v2/FSN_SEMANTIC.sqlite')
assert a.execute('select entity_id,entity_type from entities order by entity_id').fetchall()==b.execute('select entity_id,entity_type from entities order by entity_id').fetchall()
assert q['database_sha256']==u['database_sha256']==m['database_sha256']
assert m['semantic_revision']=='v2'
assert b.execute('select 1 from revisions where revision=?',('v2',)).fetchone()
print('DELIVERABLE READBACK PASS')
print('QA checks:',len(q['checks']),'source paths:',q['source_paths_checked'])
a.close();b.close()
