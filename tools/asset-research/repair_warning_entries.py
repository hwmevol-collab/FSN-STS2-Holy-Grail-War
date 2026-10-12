from common import *
import zlib
def run():
    path=L/'Original/Metadata/XP3_ENTRIES.jsonl';rows=[json.loads(s) for s in path.open(encoding='utf-8')];updates={}
    for r in rows:
        if not r['physical_name_mapped']:continue
        parts=[]
        with (SOURCES['Original']/r['source_container']).open('rb') as f:
            for flag,offset,orig,comp in r['segments']:
                f.seek(offset);data=f.read(comp if flag&7 else orig);parts.append(zlib.decompress(data) if flag&7 else data)
        data=b''.join(parts)
        # These intentionally unencrypted metadata entries were never passed through the runtime filter.
        if not data.startswith(b'Warning:') or zlib.adler32(data)&0xffffffff!=r['adler32']:raise ValueError('Unexpected long-name entry')
        p=pathlib.Path(r['extracted_path'])
        if p.read_bytes()!=data:
            saved=W/'staging/resolved_first_attempts'/r['source_container']/p.name;saved.parent.mkdir(parents=True,exist_ok=True)
            if not saved.exists():shutil.copy2(p,saved)
            p.write_bytes(data)
        r.update(sha256=hashlib.sha256(data).hexdigest(),adler32_actual=r['adler32'],adler32_matches=True,adler32_verified=True,adler32_mode='plaintext_warning_metadata',detected_format='TEXT_CANDIDATE');updates[str(p)]=r
    with path.open('w',encoding='utf-8') as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    basepath=W/'reports/BASE_ASSETS.jsonl';base=[json.loads(s) for s in basepath.open(encoding='utf-8')]
    for r in base:
        if r['extracted_path'] in updates:
            u=updates[r['extracted_path']];r['sha256']=u['sha256'];r['detected_format']=u['detected_format'];r['notes']='Unencrypted oversized archive warning recovered with logical-name mapping'
    with basepath.open('w',encoding='utf-8') as f:
        for r in base:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    print('RECOVERED_WARNING_ENTRIES',len(updates),flush=True)
if __name__=='__main__':run()
