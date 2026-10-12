from fuc_common import *
from fuc_fpk_probe import directory
def strict_prs(raw,expected):
    ip=0;bits=0;flag=0;out=bytearray()
    def get(n):
        nonlocal ip,bits,flag
        v=0
        for _ in range(n):
            if bits==0:flag=raw[ip];ip+=1;bits=8
            v=(v<<1)|((flag>>7)&1);flag=(flag<<1)&255;bits-=1
        return v
    while len(out)<expected and ip<len(raw):
        if get(1):out.append(raw[ip]);ip+=1
        else:
            if get(1)==0:
                length=get(2)+2;pos=raw[ip]-256;ip+=1
            else:
                pos=(raw[ip]<<8)|raw[ip+1];ip+=2;length=pos&7;pos=(pos-65536)>>3
                if length==0:length=raw[ip]+1;ip+=1
                else:length+=2
            pos+=len(out)
            assert 0<=pos<len(out),'PRS backreference outside output'
            for _ in range(length):out.append(out[pos]);pos+=1
        assert len(out)<=expected,'PRS output overrun'
    assert len(out)==expected,'PRS produced fewer bytes than declared'
    return out
def run():
    root=STAGE_ROOT;records=[];containers=[];outroot=root/'FPKExtracted';logroot=root/'tool_logs';logroot.mkdir(exist_ok=True)
    rs=readjson(root/'PARTIAL_ISO_FILESYSTEM_INVENTORY.json');fpk=[r for r in rs if r['logical_path'].endswith('.fpk') and r['complete_extent']]
    for i,r in enumerate(fpk):
        p=pathlib.Path(r['physical_path']);es=directory(p);dst=outroot/r['logical_path'];marker=dst/'EXTRACTED_VERIFIED.json';sourcehash=sha(p)
        if not marker.exists():
            if any(e['name']!=e['safe_name'] or e['compressed_size']==e['uncompressed_size'] for e in es):
                raw=p.read_bytes()
                for e in es:
                    q=dst/e['safe_name'];q.parent.mkdir(parents=True,exist_ok=True)
                    payload=raw[e['offset']:e['offset']+e['compressed_size']]
                    q.write_bytes(payload if e['compressed_size']==e['uncompressed_size'] else strict_prs(payload,e['uncompressed_size']))
                (logroot/(f'{i:04d}.log')).write_text('Strict PRS adapter used: root-prefixed names or raw entries (compressed_size == uncompressed_size). Original names retained in index; output path rooted safely within WORK.\n')
            else:
                proc=subprocess.run(['E:/BaiduNetdiskDownload/FSN/.tools/dotnet/dotnet.exe',str(W/'tools/fuc-fpkcodes/FPKCodes.dll'),'-e',str(p),str(dst)],capture_output=True,timeout=120)
                (logroot/(f'{i:04d}.log')).write_bytes(proc.stdout+b'\n'+proc.stderr)
                assert proc.returncode==0,(p,proc.returncode)
        assert sha(p)==sourcehash
        for e in es:
            q=dst/e['safe_name'];assert q.is_file() and q.stat().st_size==e['uncompressed_size']
            b=q.open('rb').read(64)
            records.append(dict(container=r['logical_path'],container_sha256=sourcehash,physical_path=str(q),source_status=r.get('source_status','COMPLETE_EXTENT_FROM_UNVERIFIED_ROM_PREFIX'),size=q.stat().st_size,sha256=sha(q),magic=b[:16].hex(),first_64_bytes=b.hex(),**e))
        # An independent strict translation verifies small and largest entries in every FPK.
        # It requires the decompressor to actually fill the declared output (upstream zero-initializes it).
        samples={0,max(range(len(es)),key=lambda j:es[j]['uncompressed_size']),len(es)-1}
        raw=p.read_bytes()
        for j in sorted(samples):
            e=es[j];payload=raw[e['offset']:e['offset']+e['compressed_size']]
            if e['compressed_size']!=e['uncompressed_size']:payload=strict_prs(payload,e['uncompressed_size'])
            assert hashlib.sha256(payload).hexdigest()==sha(dst/e['safe_name'])
        jsonwrite(marker,dict(source_sha256=sourcehash,declared_entries=len(es),extracted_entries=len(es),strict_prs_crosschecked_entry_indices=sorted(samples)))
        containers.append(dict(container=r['logical_path'],declared_entries=len(es),extracted_entries=len(es),strict_crosschecks=len(samples),status=r.get('source_status','EXTRACTED_WORK_ONLY_UNVERIFIED_ROM'),source_sha256=sourcehash))
        if i%25==0:log('FPK extracted',i+1,'/',len(fpk),'payloads',len(records))
    csvwrite(root/'FPK_EXTRACTED_INDEX.csv',records);jsonwrite(root/'FPK_EXTRACTED_INDEX.json',records);jsonwrite(root/'FPK_EXTRACTION_SUMMARY.json',dict(container_count=len(fpk),declared_entries=len(records),extracted_entries=len(records),strict_prs_crosschecked_entries=sum(r['strict_crosschecks'] for r in containers),source_container_changes=0,containers=containers,extensions=dict(collections.Counter(pathlib.Path(r['name']).suffix for r in records)),magic_clusters=dict(collections.Counter(r['magic'][:16] for r in records))))
    log('FPK COMPLETE WORK RECOVERY',len(fpk),len(records))
if __name__=='__main__':run()
