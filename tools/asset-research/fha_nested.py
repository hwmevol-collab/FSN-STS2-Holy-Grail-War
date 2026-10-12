"""Nested XP3 extraction with checked filter selection and isolated history."""
from common import *
from fha_prepare import ROOT,FHA,FW
from fha_extract import safe_path,payload,ARC
from verify_xp3 import index
import subprocess,zlib

def extract(p,container):
    es=index(p);samples=[e for e in es if e['flags']&0x80000000][:8]
    plain=all((zlib.adler32(payload(p,e))&0xffffffff)==e['adler32'] for e in samples)
    plugin='noop' if plain else 'fha'
    stage=FW/'nested_staging';stage.mkdir(parents=True,exist_ok=True)
    shutil.copy2(FHA/'RawExtracted/Molebox/FateFD.exe/default/cxdec.tpm',stage/'cxdec.tpm')
    staged=stage/(hashlib.sha256(container.encode()).hexdigest()[:16]+'.xp3')
    if not staged.exists():os.link(p,staged)
    decode=FW/'nested_decoded_inner_tpm'/hashlib.sha256(container.encode()).hexdigest()[:16];decode.mkdir(parents=True,exist_ok=True)
    out=FHA/'RawExtracted/NestedXP3'/container;out.mkdir(parents=True,exist_ok=True)
    cmd=[str(ARC),'--dec=kirikiri/xp3','--plugin='+plugin,'--numeric-file-names','--no-recurse','--no-color','-t=2','-v=1','-o='+str(decode),str(staged)]
    if len([f for f in decode.rglob('*') if f.is_file()])!=len(es):
        with (FW/(staged.stem+'.nested.log')).open('w',encoding='utf-8') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,cwd=ARC.parent,timeout=7200)
        code=r.returncode
    else:code=0
    outputs={int(f.name):f for f in decode.rglob('*') if f.is_file() and f.name.isdigit()}
    used=set();rows=[];bad=[];verified=0
    for i,e in enumerate(es):
        f=outputs.get(i);b=f.read_bytes() if f else b'';ok=len(b)==e['size'] and (zlib.adler32(b)&0xffffffff)==e['adler32'];mode='decrypted_payload'
        if not ok:
            raw=payload(p,e)
            if not e['flags']&0x80000000:b=raw;mode='unfiltered_payload'
            if (zlib.adler32(raw)&0xffffffff)==e['adler32']:
                if not e['flags']&0x80000000:b=raw
                ok=len(b)==e['size'];mode='pre_filter_checksum' if e['flags']&0x80000000 else 'unfiltered_payload'
        if ok:verified+=1
        else:bad.append(dict(entry=i,path=e['source_logical_path'],reason='Adler32 or size mismatch'))
        target=safe_path(out,e['source_logical_path'],i,used);target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():target.write_bytes(b)
        else:
            if target.read_bytes()!=b:
                assert target.resolve().is_relative_to((FHA/'RawExtracted/NestedXP3').resolve())
                target.write_bytes(b)
        e.update(source_version='HollowAtaraxia',source_container=container,entry_index=i,extracted_path=str(target),sha256=hashlib.sha256(b).hexdigest(),detected_format=signature(b[:64],pathlib.Path(e['source_logical_path']).suffix),adler32_verified=ok,adler32_mode=mode,decrypt_method='CXDEC FHA' if plugin=='fha' else 'XP3 unencrypted')
        rows.append(e)
    log=dict(source=str(p),source_container=container,kind='Nested XP3',tool='arc_unpacker v0.11',plugin=plugin,command=subprocess.list2cmdline(cmd),exit_code=code,expected_entries=len(es),verified_entries=verified,files_extracted=len(es),status='success' if not bad else 'partial',errors=bad)
    print('NESTED',container,len(es),plugin,log['status'],len(bad),flush=True)
    return rows,log

def run():
    rows=[json.loads(s) for s in (FHA/'Metadata/RAW_ASSETS.jsonl').open(encoding='utf-8')]
    specs=[(pathlib.Path(r['extracted_path']),r['source_container']+'/inner.xp3') for r in rows if r['detected_format']=='XP3' and r.get('decrypt_method','').startswith('Molebox') and r['source_container']!='FateFD.exe/extra']
    extra=FW/'FateFD_embedded.xp3';dest=FHA/'RawExtracted/Molebox/FateFD.exe/extra/FateFD_embedded.xp3';dest.parent.mkdir(parents=True,exist_ok=True)
    if not dest.exists():os.link(extra,dest)
    specs.append((dest,'FateFD.exe/extra/inner.xp3'))
    if not any(r['extracted_path']==str(dest) for r in rows):rows.append(dict(source_version='HollowAtaraxia',source_container='FateFD.exe/extra',source_logical_path=dest.name,extracted_path=str(dest),size=dest.stat().st_size,sha256=sha(dest),detected_format='XP3',decrypt_method='Molebox NewDES ECB extra area; KiriKiri XP3 signature at offset 4608'))
    names={c for p,c in specs};rows=[r for r in rows if r['source_container'] not in names]
    logs=[x for x in json.loads((FHA/'Metadata/EXTRACTION_LOG.json').read_text('utf-8')) if x['source_container'] not in names]
    for p,c in specs:
        rs,log=extract(p,c);rows.extend(rs);logs.append(log)
        jsonwrite(FHA/'Metadata/EXTRACTION_LOG.json',logs)
        with (FHA/'Metadata/RAW_ASSETS.jsonl').open('w',encoding='utf-8') as f:
            for r in rows:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    print('ALL_RAW',len(rows),flush=True)
if __name__=='__main__':run()
