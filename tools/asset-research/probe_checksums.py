from common import *
import zlib
rows=[json.loads(s) for s in (L/'Original/Metadata/XP3_ENTRIES.jsonl').open(encoding='utf-8')]
out=[]
for container in sorted(set(r['source_container'] for r in rows)):
    e=next(r for r in rows if r['source_container']==container and r['entry_index']>=1)
    with (SOURCES['Original']/container).open('rb') as f:
        parts=[]
        for flag,offset,orig,comp in e['segments']:
            f.seek(offset);b=f.read(comp if flag&7 else orig);parts.append(zlib.decompress(b) if flag&7 else b)
    raw=b''.join(parts);simple=raw.translate(bytes(x^0x36 for x in range(256)));decoded=pathlib.Path(e['extracted_path']).read_bytes()
    out.append(dict(container=container,file=e['source_logical_path'],expected=e['adler32'],raw=zlib.adler32(raw)&0xffffffff,simple_xor=zlib.adler32(simple)&0xffffffff,fsn=zlib.adler32(decoded)&0xffffffff,raw_head=raw[:32].hex(),decoded_head=decoded[:32].hex()))
jsonwrite(W/'reports/XP3_CHECKSUM_PROBE.json',out)
print(json.dumps(out,ensure_ascii=True,indent=2))
