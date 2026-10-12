from common import *

def run():
    with (L/'Metadata/UNKNOWN_FORMATS.csv').open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    groups=collections.defaultdict(list)
    for r in rows:groups[r['probable_format']].append(r)
    details=[];samples=[]
    for fmt,items in groups.items():
        ordered=sorted(items,key=lambda r:int(r['size']))
        for r in [ordered[0],ordered[len(ordered)//2],ordered[-1]]:
            data=pathlib.Path(r['file']).read_bytes();head=data[:112]
            samples.append(dict(format=fmt,file=r['file'],bytes=len(data),magic=head[:4].decode('ascii','replace'),header_hex=head.hex(),header_u32le=[struct.unpack_from('<I',head,i)[0] for i in range(0,len(head)-3,4)],related_plain_ui_path=str(pathlib.Path(r['file']).with_suffix('.gut')) if fmt=='GUTC_COMPILED_UI' else '',related_plain_ui_bytes=pathlib.Path(r['file']).with_suffix('.gut').stat().st_size if fmt=='GUTC_COMPILED_UI' and pathlib.Path(r['file']).with_suffix('.gut').exists() else None))
        details.append(dict(format=fmt,count=len(items),unique_sha256=len(set(r['sha256'] for r in items)),total_bytes=sum(int(r['size']) for r in items),min_bytes=int(ordered[0]['size']),max_bytes=int(ordered[-1]['size']),header_magic=collections.Counter(r['first_64_bytes_hex'][:8] for r in items)))
    jsonwrite(L/'Reports/UNKNOWN_RESEARCH.json',dict(scope='Read-only investigation of preserved outputs, not game source',groups=details,samples=samples,status='Format families identified; field semantics unresolved, no fabricated conversion',upstream_search='Official FSNr_tools/FatePackageManager/archived Decompiler and KiriKiri/GARbro references audited. TFT identified and fully decoded; no verified FTPR/GUTC decoder found in these references.'))
    print('UNKNOWN_RESEARCH',len(rows),'families',len(groups),flush=True)
if __name__=='__main__':run()
