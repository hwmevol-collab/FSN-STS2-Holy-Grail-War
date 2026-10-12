from common import *
import ctypes,re,traceback
def setup():
    dll=ctypes.CDLL(str(W/'tools/epk_bridge.dll'))
    dll.fsn_epk_init.argtypes=[ctypes.c_void_p,ctypes.c_int];dll.fsn_epk_transform.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_int]
    key=(W/'repos/FSNr_raw/keys/SomeKey.bin').read_bytes();assert dll.fsn_epk_init(key,len(key))==0
    return dll
def dec(dll,data,key):
    if len(data)<48:raise ValueError('Too small for EPK envelope')
    body=data[:-48];length=int.from_bytes(data[-32:-28],'big')
    if length>len(body):raise ValueError('EPK length out of bounds')
    expected=hashlib.md5(body+b'8FE9D249BD2689BB4B70F5AE88A9E645').digest()
    if expected!=data[-16:]:raise ValueError('Encrypted envelope MD5 failed')
    b=ctypes.create_string_buffer(body,len(body)+16);k=key.encode('utf-8');assert dll.fsn_epk_transform(b,len(body),k,len(k),0)==0
    result=b.raw[:length]
    # Upstream handles trailing <8 bytes as unchanged bytes. Confirm exact round trip.
    rb=ctypes.create_string_buffer(b.raw[:len(body)],len(body)+16);assert dll.fsn_epk_transform(rb,len(body),k,len(k),1)==0
    if rb.raw[:len(body)]!=body:raise ValueError('Decrypt/encrypt round trip differs')
    return result
def run():
    dll=setup();root=L/'Remastered/RawExtracted';epks=sorted(p for p in root.rglob('*.epk') if 'EPK' not in p.relative_to(root).parts[:1]);rows=[]
    name_map={}
    for p in root.rglob('*.ks'):
        name=p.stem;bits=int.from_bytes(hashlib.md5(name.encode('utf-8')).digest(),'big');h=''.join('0123456789abcdefghijklmnopqrstuvwxyz'[(bits<<i>>128)&31] for i in range(3,131,5));name_map[h]=name
    for n,p in enumerate(epks):
        rel=p.relative_to(root);out=root/'EPK/Decrypted'/rel;txt=root/'EPK/Text'/rel.with_suffix('.txt');enc=root/'EPK/Encrypted'/rel
        m=re.search(r'/locale/([^/]+)/',p.as_posix());locale=m.group(1) if m else 'ja';mapped=name_map.get(p.stem,p.stem);error='';success=False;encoding='';readable=False
        try:
            enc.parent.mkdir(parents=True,exist_ok=True)
            if not enc.exists():os.link(p,enc)
            result=dec(dll,p.read_bytes(),p.stem);out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(result)
            # UTF-8 is the actual Remastered DAT table encoding. Preserve binary outputs separately.
            try:
                text=result.decode('utf-8-sig');encoding='utf-8';readable='\x00' not in text and (text.startswith('DAT') or text.startswith('FDT') or '::' in text)
                if readable:txt.parent.mkdir(parents=True,exist_ok=True);txt.write_text(text,encoding='utf-8')
            except UnicodeError:pass
            success=True
        except Exception as e:error=repr(e)
        rows.append(dict(source=str(p),relative_path=rel.as_posix(),locale=locale,script_mapping=mapped,decrypt_success=success,readable_text=readable,encoding=encoding,decrypted_path=str(out) if success else '',text_path=str(txt) if readable else '',sha256=sha(out) if success else '',error=error,preservation='Encrypted view uses hardlink to per-container raw'))
        if n%200==0:print('EPK',n+1,'/',len(epks),'success',sum(r['decrypt_success'] for r in rows),'readable',sum(r['readable_text'] for r in rows),flush=True)
    jsonwrite(L/'Remastered/Metadata/EPK_INDEX.json',rows);csvwrite(L/'Metadata/EPK_INDEX.csv',rows)
    print('EPK DONE',len(rows),collections.Counter((r['decrypt_success'],r['readable_text']) for r in rows),flush=True)
if __name__=='__main__':run()
