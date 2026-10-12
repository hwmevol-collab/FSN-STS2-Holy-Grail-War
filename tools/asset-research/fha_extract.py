"""Isolated FHA extraction, archive entry checks, preserved per-container history."""
from common import *
from verify_xp3 import index
from fha_prepare import ROOT,FHA,FW
import subprocess,zlib,re,traceback,sys
ARC=W/'tools/arc_unpacker/arc_unpacker.exe'
def payload(p,e):
    pieces=[]
    with p.open('rb') as f:
        for flag,off,orig,comp in e['segments']:
            f.seek(off);b=f.read(comp if flag&7 else orig);b=zlib.decompress(b) if flag&7 else b
            assert len(b)==orig;pieces.append(b)
    return b''.join(pieces)
def safe_path(out,name,i,used):
    path=pathlib.PurePosixPath(name.replace('\\','/'))
    unsafe=path.is_absolute() or '..' in path.parts or any(len(c)>180 or re.search(r'[<>:"|?*]',c) or c.endswith((' ','.')) for c in path.parts)
    target=out/path if not unsafe else out/'__mapped_names'/f'entry_{i:06d}.bin'
    if str(target).casefold() in used:target=out/'__duplicate_names'/f'entry_{i:06d}{path.suffix[:12]}'
    used.add(str(target).casefold());assert target.resolve().is_relative_to(out.resolve());return target
def run():
    stage=FW/'staging';stage.mkdir(parents=True,exist_ok=True)
    tpm=next(ROOT.rglob('cxdec.tpm'));shutil.copy2(tpm,stage/'cxdec.tpm')
    inventory=json.loads((FHA/'Metadata/SOURCE_INVENTORY.json').read_text('utf-8'));rows=[];logs=[]
    only=set(sys.argv[1:])
    if only:
        rows=[json.loads(s) for s in (FHA/'Metadata/RAW_ASSETS.jsonl').open(encoding='utf-8') if json.loads(s)['source_container']!='Loose' and pathlib.Path(json.loads(s)['source_container']).name not in only]
        logs=[x for x in json.loads((FHA/'Metadata/EXTRACTION_LOG.json').read_text('utf-8')) if pathlib.Path(x['source_container']).name not in only]
    for n,r in enumerate(inventory):
        if r['extension']!='.xp3':continue
        if only and r['filename'] not in only:continue
        p=pathlib.Path(r['absolute_path']);out=FHA/'RawExtracted/XP3'/p.name;out.mkdir(parents=True,exist_ok=True)
        log=dict(source=str(p),source_container=r['relative_path'],kind='XP3',status='failed',start_time=now());errors=[]
        try:
            es=index(p);samples=es[:8]
            plain=sum((zlib.adler32(payload(p,e))&0xffffffff)==e['adler32'] for e in samples)
            plugin='noop' if plain==len(samples) else 'fha'
            staged=stage/f'container_{n:03d}.xp3'
            if not staged.exists():shutil.copy2(p,staged)
            decodeout=FW/'decoded'/plugin/p.name;decodeout.mkdir(parents=True,exist_ok=True)
            cmd=[str(ARC),'--dec=kirikiri/xp3','--plugin='+plugin,'--numeric-file-names','--no-recurse','--no-color','-t=2','-v=1','-o='+str(decodeout),str(staged)]
            logfile=FW/(p.name+'.log')
            # Reuse a complete earlier decode, but never publish solely on its exit code.
            outputs=[f for f in decodeout.rglob('*') if f.is_file()]
            if len(outputs)!=len(es):
                with logfile.open('w',encoding='utf-8') as f:proc=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,cwd=ARC.parent,timeout=3600)
                code=proc.returncode
            else:code=0
            outputs={int(f.name):f for f in decodeout.rglob('*') if f.is_file() and f.name.isdigit()}
            used=set();verified=0;recovered=0;checksum_modes=collections.Counter()
            for i,e in enumerate(es):
                raw=None;f=outputs.get(i);b=f.read_bytes() if f else b''
                post=(zlib.adler32(b)&0xffffffff)==e['adler32'] and len(b)==e['size'];mode='decrypted_payload'
                if not post:
                    raw=payload(p,e);pre=(zlib.adler32(raw)&0xffffffff)==e['adler32']
                    if pre and (not e['flags']&0x80000000 or signature(raw[:64],pathlib.Path(e['source_logical_path']).suffix)!='UNKNOWN'):
                        b=raw;post=True;mode='unfiltered_payload';recovered+=1
                    elif pre and len(b)==e['size']:post=True;mode='pre_filter_checksum'
                if not post:errors.append(dict(entry=i,path=e['source_logical_path'],reason='size/checksum mismatch'))
                else:verified+=1
                target=safe_path(out,e['source_logical_path'],i,used);target.parent.mkdir(parents=True,exist_ok=True)
                if not target.exists():target.write_bytes(b)
                else:
                    if target.read_bytes()!=b:
                        # Only repair a previously failed FHA extraction; existing FSN never enters this path.
                        assert target.resolve().is_relative_to((FHA/'RawExtracted/XP3').resolve())
                        log.setdefault('repaired_previous_output',[]).append(dict(path=str(target),previous_sha256=sha(target)))
                        target.write_bytes(b)
                e.update(source_version='HollowAtaraxia',source_container=r['relative_path'],entry_index=i,extracted_path=str(target),sha256=hashlib.sha256(b).hexdigest(),detected_format=signature(b[:64],pathlib.Path(e['source_logical_path']).suffix),adler32_verified=post,adler32_mode=mode,physical_name_mapped=target.relative_to(out).as_posix()!=e['source_logical_path'],decrypt_method='CXDEC FHA' if plugin=='fha' else 'XP3 unencrypted')
                rows.append(e);checksum_modes[mode]+=1
            log.update(command=subprocess.list2cmdline(cmd),tool='arc_unpacker v0.11',plugin=plugin,exit_code=code,expected_entries=len(es),verified_entries=verified,files_extracted=len(es),bytes_extracted=sum(e['size'] for e in es),unfiltered_recovered=recovered,checksum_modes=dict(checksum_modes),status='success' if not errors and verified==len(es) else 'partial',errors=errors)
        except Exception as exc:
            log.update(errors=[repr(exc)],traceback=traceback.format_exc(),notes='Unknown XP3 extension container retained for separate audited adapter')
        log['end_time']=now();logs.append(log);jsonwrite(FHA/'Metadata/EXTRACTION_LOG.json',logs)
        print('EXTRACT',p.name,log['status'],log.get('files_extracted',0),flush=True)
    # Preserve every loose file, including unknown archives, saves, signatures, and docs.
    for r in inventory:
        if r['detected_format']=='XP3':continue
        p=pathlib.Path(r['absolute_path']);target=FHA/'RawExtracted/Loose'/r['relative_path'];target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():shutil.copy2(p,target)
        assert sha(target)==r['sha256']
        rows.append(dict(source_version='HollowAtaraxia',source_container='Loose',source_logical_path=r['relative_path'],extracted_path=str(target),size=r['size'],sha256=r['sha256'],detected_format=r['detected_format'],decrypt_method='',entry_index=''))
    with (FHA/'Metadata/RAW_ASSETS.jsonl').open('w',encoding='utf-8') as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    csvwrite(FHA/'Metadata/EXTRACTION_LOG.csv',logs,['source','source_container','kind','tool','plugin','command','start_time','end_time','exit_code','expected_entries','verified_entries','files_extracted','bytes_extracted','status','errors'])
    print('RAW ASSETS',len(rows),flush=True)
if __name__=='__main__':run()
