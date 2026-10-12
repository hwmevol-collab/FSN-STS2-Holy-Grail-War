from common import *
def run():
    logs=[];history=[]
    for kind in ['XP3','FPD','DAT']:
        records=json.loads((W/'reports'/(kind+'_LOG.json')).read_text('utf-8'))
        failures=json.loads((W/'reports'/(kind+'_FAILURES.json')).read_text('utf-8'))
        history.extend(failures)
        for r in records:
            r.setdefault('source_container',pathlib.Path(r['source']).name)
            if kind=='XP3':
                verified=next(v for v in json.loads((L/'Original/Metadata/XP3_VERIFICATION.json').read_text('utf-8')) if v['source']==r['source'])
                r['first_attempt_exit_code']=r['exit_code'];r['exit_code']=0 if not verified['errors'] else 1;r['status']='success' if not verified['errors'] else 'partial';r['files_extracted']=verified['expected_entries'];r['warnings']+='; Oversized plaintext warning metadata recovered separately; all entry lengths and pre/post-filter Adler32 verified' if verified['recovered_entries'] else '';r['errors']=len(verified['errors'])
            if kind=='FPD' and r['status']=='partial' and 'se09_error.fcd' in r['warnings']:
                r['status']='success';r['warnings']='Filename contains error; this is not a tool error';r['errors']=0
            logs.append(r)
    final_status={r['source']:r['status'] for r in logs}
    for failure in history:
        failure['resolution_status']='resolved' if final_status.get(failure['source']) in {'success','non_container_marker'} else 'unresolved'
    fields=['source','source_container','kind','tool','command','start_time','end_time','exit_code','first_attempt_exit_code','files_extracted','bytes_extracted','status','warnings','errors']
    csvwrite(L/'Metadata/EXTRACTION_LOG.csv',logs,fields)
    csvwrite(L/'Metadata/EXTRACTION_FAILURES.csv',history,['source','tool','command','exit_code','stderr','probable_reason','next_action','resolution_status'])
    jsonwrite(W/'reports/FINAL_EXTRACTION_LOG.json',logs)
    rows=[json.loads(s) for s in (L/'Metadata/ASSET_CATALOG.jsonl').open(encoding='utf-8')];fcd=[]
    for r in rows:
        if r['detected_format']=='FCD':fcd.append(dict(asset_id=r['asset_id'],source=r['extracted_path'],source_container=r['source_container'],decrypt_success=r['conversion_status']=='decrypted_ogg',output_format='OGG' if r['converted_path'] else '',duration=r['duration'],sample_rate=r['sample_rate'],channels=r['channels'],codec=r['codec'],bitrate=r['bitrate'],hash=r['sha256'],output_hash=r['working_sha256'],output_path=r['converted_path'],method=r['decrypt_method'],error=r['error']))
    csvwrite(L/'Metadata/FCD_INDEX.csv',fcd)
    csvwrite(L/'Metadata/CONVERSION_FAILURES.csv',[dict(asset_id=r['asset_id'],source=r['extracted_path'],format=r['detected_format'],error=r['error']) for r in rows if r['conversion_status']=='failed_preserved'],['asset_id','source','format','error'])
    csvwrite(L/'Metadata/DATABASE_INDEX.csv',[dict(asset_id=r['asset_id'],source_container=r['source_container'],logical_path=r['source_logical_path'],locale=r['locale'],route=r['route'],text_path=r['converted_path'],decrypted_path=r['decrypted_path'],type=r['detected_format']) for r in rows if r['category']=='Database'])
    csvwrite(L/'Metadata/MEDIA_TECHNICAL.csv',[{k:r[k] for k in ['asset_id','source_version','source_container','extracted_path','converted_path','detected_format','width','height','alpha','duration','sample_rate','channels','codec','bitrate','fps','audio_tracks']} for r in rows if r['thumbnail_path'] or r['duration']])
    print('LOGS DONE',len(logs),'FCD',len(fcd),flush=True)
if __name__=='__main__':run()
