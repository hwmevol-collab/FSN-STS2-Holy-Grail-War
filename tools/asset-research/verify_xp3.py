from common import *
import zlib,io,traceback
def chunks(data):
    cur=io.BytesIO(data)
    while cur.tell()<len(data):
        typ=cur.read(4);n=struct.unpack('<Q',cur.read(8))[0];b=cur.read(n)
        if len(b)!=n:raise ValueError('Truncated chunk')
        yield typ,b
def index(p):
    with p.open('rb') as f:
        f.seek(11);offset=struct.unpack('<Q',f.read(8))[0]
        if struct.unpack('<I',f.read(4))[0]==1:f.seek(offset+9);offset=struct.unpack('<Q',f.read(8))[0]
        f.seek(offset);flag=f.read(1)[0];compressed=struct.unpack('<Q',f.read(8))[0]
        if flag:expected=struct.unpack('<Q',f.read(8))[0]
        data=f.read(compressed);data=zlib.decompress(data) if flag else data
    entries=[]
    for typ,b in chunks(data):
        if typ!=b'File':raise ValueError('Unexpected '+repr(typ))
        e={}
        for sub,c in chunks(b):
            if sub==b'info':
                flags,original,compressed,n=struct.unpack('<IQQH',c[:22]);e.update(flags=flags,size=original,compressed_size=compressed,source_logical_path=c[22:22+2*n].decode('utf-16-le'))
            elif sub==b'segm':e['segments']=[struct.unpack('<IQQQ',c[i:i+28]) for i in range(0,len(c),28)]
            elif sub==b'adlr':e['adler32']=struct.unpack('<I',c)[0]
            elif sub==b'time':e['timestamp_raw']=c.hex()
        entries.append(e)
    return entries
def run():
    inv=json.loads((L/'Metadata/SOURCE_INVENTORY.json').read_text('utf-8'));rows=[];logs=[]
    for r in inv:
        if r['source_version']!='Original' or r['detected_format']!='XP3':continue
        p=pathlib.Path(r['absolute_path']);es=index(p);out=L/'Original/RawExtracted'/p.name;recovered=0;errors=[];adler_bad=0
        with p.open('rb') as f:
            for i,e in enumerate(es):
                logical=e['source_logical_path'];target=out/logical;invalid=any(len(c)>240 for c in pathlib.PurePosixPath(logical).parts)
                if invalid:target=out/'__long_names'/f'entry_{i:06d}.txt'
                if not target.exists():
                    pieces=[]
                    for flag,offset,orig,comp in e['segments']:
                        f.seek(offset);b=f.read(comp if flag&7 else orig);pieces.append(zlib.decompress(b) if flag&7 else b)
                    b=bytearray(b''.join(pieces))
                    if not (invalid and b.startswith(b'Warning:')):
                        b=bytearray(bytes(b).translate(bytes(x^0x36 for x in range(256))))
                        if len(b)>0x2ea29:b[0x2ea29]^=3
                        if len(b)>0x13:b[0x13]^=1
                    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b);recovered+=1
                b=target.read_bytes();actual=zlib.adler32(b)&0xffffffff
                if len(b)!=e['size']:errors.append(logical+': size mismatch')
                mode='decrypted_payload';verified=actual==e['adler32']
                if not verified:
                    parts=[]
                    for flag,offset,orig,comp in e['segments']:
                        f.seek(offset);raw=f.read(comp if flag&7 else orig);parts.append(zlib.decompress(raw) if flag&7 else raw)
                    raw=b''.join(parts);verified=(zlib.adler32(raw)&0xffffffff)==e['adler32'];mode='pre_filter_encrypted_payload'
                    if not verified:adler_bad+=1;errors.append(logical+': Adler32 matches neither pre-filter nor post-filter payload')
                e.update(source_version='Original',source_container=r['relative_path'],entry_index=i,extracted_path=str(target),sha256=hashlib.sha256(b).hexdigest(),adler32_actual=actual,adler32_matches=actual==e['adler32'],adler32_verified=verified,adler32_mode=mode,detected_format=signature(b[:64],pathlib.Path(logical).suffix),physical_name_mapped=invalid)
                rows.append(e)
        logs.append(dict(source=str(p),expected_entries=len(es),verified_entries=len(es)-len(errors),recovered_entries=recovered,adler32_mismatch=adler_bad,errors=errors));print('XP3_VERIFY',p.name,len(es),'recovered',recovered,'adler_bad',adler_bad,flush=True)
    with (L/'Original/Metadata/XP3_ENTRIES.jsonl').open('w',encoding='utf-8') as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    jsonwrite(L/'Original/Metadata/XP3_VERIFICATION.json',logs)
if __name__=='__main__':run()
