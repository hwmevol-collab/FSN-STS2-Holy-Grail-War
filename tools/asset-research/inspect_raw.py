from common import *
counts=collections.Counter();heads=collections.Counter();samples={};fcd=collections.Counter();fcd_samples={};total=0
for ver in ['Original','Remastered']:
    root=L/ver/'RawExtracted'
    for p in root.rglob('*'):
        if not p.is_file() or (ver=='Remastered' and 'EPK' in p.relative_to(root).parts[:1]):continue
        with p.open('rb') as f:b=f.read(64)
        fmt=signature(b,p.suffix);counts[(ver,p.suffix.lower(),fmt)]+=1;total+=p.stat().st_size
        k=(ver,p.suffix.lower(),fmt);samples.setdefault(k,dict(path=str(p),size=p.stat().st_size,head=b.hex()))
        if fmt=='UNKNOWN':heads[(ver,p.suffix.lower(),b[:8].hex())]+=1
        if fmt=='FCD':
            k=(b[:8].hex(),int.from_bytes(b[8:12],'big'),b[12:16].hex());fcd[k]+=1;fcd_samples.setdefault(k,str(p))
data={'counts':[dict(source_version=k[0],extension=k[1],format=k[2],count=v,example=samples[k]) for k,v in counts.most_common()],'unknown_heads':[dict(key=k,count=v) for k,v in heads.most_common()],'fcd_headers':[dict(key=k,count=v,example=fcd_samples[k]) for k,v in fcd.most_common()],'raw_logical_bytes':total}
jsonwrite(W/'reports/RAW_INSPECTION.json',data)
print(json.dumps(data,ensure_ascii=True,indent=2))
