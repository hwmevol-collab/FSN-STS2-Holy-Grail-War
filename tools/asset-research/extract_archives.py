from common import *
import subprocess, re, traceback, argparse
ARC=W/'tools/arc_unpacker/arc_unpacker.exe'
DOTNET=pathlib.Path('E:/BaiduNetdiskDownload/FSN/.tools/dotnet/dotnet.exe')
def run(kind):
    inventory=json.loads((L/'Metadata/SOURCE_INVENTORY.json').read_text('utf-8'));logs=[];failures=[]
    if kind=='XP3':selected=[r for r in inventory if r['source_version']=='Original' and r['detected_format']=='XP3']
    else:selected=[r for r in inventory if r['source_version']=='Remastered' and (r['detected_format']=='FPD' or r['extension']=='.bin')]
    for r in selected:
        p=pathlib.Path(r['absolute_path']);started=now();logfile=W/'logs'/(kind+'_'+p.name+'.log');out=L/r['source_version']/'RawExtracted'
        if kind=='XP3':
            stage=W/'staging'/p.name;shutil.copy2(p,stage)
            # Isolate every archive and retain all output file encodings.
            out=out/p.name;out.mkdir(parents=True,exist_ok=True)
            cmd=[str(ARC),'--dec=kirikiri/xp3','--plugin=fsn','--no-recurse','--no-color','--rename','-t=2','-v=2','-o='+str(out),str(stage)]
        else:
            out=out/('BIN' if p.suffix.lower()=='.bin' else 'ROOT_FPD')/p.name;out.mkdir(parents=True,exist_ok=True)
            cmd=[str(DOTNET),str(W/'tools/fpm/fpm.dll'),str(p),str(out)]
        try:
            if kind=='FPD' and r['detected_format']!='FPD':
                # An explicit attempt identifies the ten-byte all-zero file as a marker, not a container.
                if r['size']==10 and bytes.fromhex(r['magic_bytes'])==b'\x00'*10:
                    logfile.write_text('Inspected all 10 bytes: zero-filled marker, no FPD header or payload.',encoding='utf-8');status='non_container_marker';code=0
                else:raise ValueError('Not FPD format')
            else:
                with logfile.open('w',encoding='utf-8') as lf:
                    proc=subprocess.run(cmd,stdout=lf,stderr=subprocess.STDOUT,cwd=str(W/'tools/arc_unpacker') if kind=='XP3' else str(W),timeout=3600)
                code=proc.returncode;status='success' if code==0 else 'failed'
            if kind=='XP3':
                folders=list(out.iterdir())
                if len(folders)==1 and folders[0].is_dir():
                    nest=folders[0]
                    for item in list(nest.iterdir()):shutil.move(str(item),str(out/item.name))
                    nest.rmdir()
                if stage.is_file() and stage.parent.resolve()==(W/'staging').resolve():stage.unlink()
            files=[f for f in out.rglob('*') if f.is_file()];count=len(files);size=sum(f.stat().st_size for f in files)
            msg=logfile.read_text('utf-8',errors='replace')
            errors='\n'.join(line for line in msg.splitlines() if re.search(r'error|failed|corrupt|unsupported',line,re.I))
            if errors and status=='success':status='partial'
            if count==0 and status=='success':status='failed';errors+='\nNo files extracted'
        except Exception:
            errors=traceback.format_exc();count=size=0;code=1;status='failed';logfile.write_text(errors,encoding='utf-8')
        row=dict(source=str(p),source_container=r['relative_path'],kind=kind,tool='arc_unpacker v0.11' if kind=='XP3' else 'FatePackageManager net9 compatibility build',command=subprocess.list2cmdline(cmd),start_time=started,end_time=now(),exit_code=code,files_extracted=count,bytes_extracted=size,status=status,warnings=errors[:4000],errors=len(errors.splitlines()) if errors else 0)
        logs.append(row)
        if status in ['failed','partial']:failures.append(dict(source=str(p),tool=row['tool'],command=row['command'],exit_code=code,stderr=errors,probable_reason='See full per-container log',next_action='Inspect format/decryption and retained files'))
        jsonwrite(W/'reports'/(kind+'_LOG.json'),logs);jsonwrite(W/'reports'/(kind+'_FAILURES.json'),failures)
        print(kind,p.name,status,count,size,flush=True)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('kind',choices=['XP3','FPD']);run(parser.parse_args().kind)
