from common import *
import traceback
def run():
    root=SOURCES['Remastered']/'obb/pack';logs=[];failures=[]
    meta=L/'Remastered/Metadata/DAT_ENTRIES.jsonl'
    with meta.open('w',encoding='utf-8') as entries:
        for source in sorted(root.glob('*.dat')):
            started=now();out=L/'Remastered/RawExtracted/DAT'/source.name;out.mkdir(parents=True,exist_ok=True)
            index=root/('fileinfo_'+source.stem+'.txt');count=total=0;errors=[];seen={}
            command=f'extract_dat.py {source} --index {index}'
            try:
                lines=index.read_text(encoding='utf-8-sig').splitlines()
                with source.open('rb') as f:
                    for num,line in enumerate(lines,1):
                        if not line.strip():continue
                        fields=line.split('::');name,ext,container,offset,size,md5=fields[:6];offset=int(offset);size=int(size)
                        if container!=source.name:raise ValueError('Index names a different container: '+container)
                        logical=name+'.'+ext;safe=logical.replace('\\','/');rel=pathlib.PurePosixPath(safe)
                        if rel.is_absolute() or '..' in rel.parts:raise ValueError('Unsafe archive path '+logical)
                        target=out/rel
                        # Preserve repeated logical names rather than letting a dictionary overwrite entries.
                        if safe.casefold() in seen:target=out/'__duplicate_entries'/str(num)/rel
                        seen[safe.casefold()]=num
                        if offset<0 or offset+size>source.stat().st_size:raise ValueError('Entry outside source bounds')
                        f.seek(offset);data=f.read(size)
                        actual_md5=hashlib.md5(data).hexdigest();digest=hashlib.sha256(data).hexdigest()
                        if actual_md5!=md5.lower():errors.append(f'{num}:{logical}:MD5 mismatch {actual_md5} expected {md5}')
                        target.parent.mkdir(parents=True,exist_ok=True)
                        if not target.exists():target.write_bytes(data)
                        elif sha(target)!=digest:raise ValueError('Existing output differs '+str(target))
                        row=dict(source_version='Remastered',source_container='obb/pack/'+source.name,source_logical_path=logical,extracted_path=str(target),index_file=str(index),index_line=num,offset=offset,size=size,sha256=digest,expected_md5=md5,actual_md5=actual_md5,index_fields=fields[6:],detected_format=signature(data[:64],'.'+ext))
                        entries.write(json.dumps(row,ensure_ascii=False)+'\n');count+=1;total+=size
                        if count%5000==0:print(source.name,count,'/',len(lines),flush=True)
                status='success' if not errors else 'partial'
            except Exception as e:errors.append(traceback.format_exc());status='partial' if count else 'failed'
            row=dict(source=str(source),kind='DAT',tool='FSNr_tools/scripts/unpack.py adapted streaming, validated entries',command=command,start_time=started,end_time=now(),exit_code=0 if status=='success' else 1,files_extracted=count,bytes_extracted=total,status=status,warnings=';'.join(errors[:20]),errors=len(errors))
            logs.append(row)
            if errors:failures.append(dict(source=str(source),tool=row['tool'],command=command,exit_code=1,stderr='\n'.join(errors),probable_reason='Index/data mismatch or extraction error',next_action='Inspect preserved entry and index'))
            jsonwrite(W/'logs'/('DAT_'+source.name+'.json'),row);print('DONE',source.name,count,status,flush=True)
    jsonwrite(W/'reports/DAT_LOG.json',logs);jsonwrite(W/'reports/DAT_FAILURES.json',failures)
if __name__=='__main__':run()
