"""Audited static Molebox adapter; never executes or edits source binaries.
Sources: sudachen/Molebox Include/stbinfo.h Core/src/svfs.cpp MxbPack/src/packager.cpp,
sudachen/xternal libhash/src/ndes.c (fixed commits in WORK/fha manifests).
"""
from common import *
from fha_prepare import ROOT,FHA,FW
import numpy as np,re,zlib,sys
from Crypto.Cipher import Blowfish
NDES_SOURCE=W/'repos/xternal_fha/libhash/src/ndes.c'
ROTOR=np.array([int(x) for x in re.search(r'static uint8_t rotor\[\] =\s*\{(.*?)\}',NDES_SOURCE.read_text(),re.S)[1].replace('\n','').split(',')],dtype=np.uint8)
def schedule(key):
    k=[];i=11
    while True:
        for j in range(3):k.append(key[i]);i=(i+1)%15
        k.append(key[i]);i=(i+9)%15
        if i==12:break
        k.extend(key[i:i+3]);i=(i+2+9)%15
    assert len(k)==60
    return k
def ndes_ecb(data,key):
    a=np.frombuffer(data,dtype=np.uint8).copy().reshape(-1,8);k=schedule(key);i=0
    for _ in range(8):
        for j in range(4):a[:,j+4]^=ROTOR[a[:,j]^k[i]];i+=1
        a[:,1]^=ROTOR[a[:,4]^k[i]];i+=1
        a[:,2]^=ROTOR[a[:,4]^a[:,5]]
        a[:,3]^=ROTOR[a[:,6]^k[i]];i+=1
        a[:,0]^=ROTOR[a[:,7]^k[i]];i+=1
    for j in range(4):a[:,j+4]^=ROTOR[a[:,j]^k[i]];i+=1
    return a.tobytes()
def bf_ecb(data,key):
    swap=lambda b:np.frombuffer(b,dtype='<u4').byteswap().tobytes()
    return swap(Blowfish.new(key[:15],Blowfish.MODE_ECB).decrypt(swap(data)))
def cbc(data,key,alg=ndes_ecb):
    plain=np.frombuffer(alg(data,key),dtype=np.uint8)
    return np.bitwise_xor(plain,np.frombuffer(b'\x00'*8+data[:-8],dtype=np.uint8)).tobytes()
def probe():
    p=next(ROOT.rglob('FateFD.exe'));b=p.read_bytes();overlay=102400;key=b[overlay+8+368:overlay+8+384]
    for alg in [ndes_ecb,bf_ecb]:
        print(alg.__name__,'quick_default',alg(bytes.fromhex('15d93054dc3ad1cd'),hashlib.md5(b'password').digest()),flush=True)
    stb=cbc(b[overlay+8:overlay+8+368],key)+key+cbc(b[overlay+8+384:overlay+8+496],key)
    print('STB',struct.unpack('<28I',stb[:112]),flush=True);cat=struct.unpack_from('<I',stb,444)[0];print('CAT',cat,flush=True)
    (FW/'STB_DECRYPTED.bin').write_bytes(stb)
    off,n,crc=struct.unpack_from('<III',stb,32)
    core=cbc(b[off:off+n],key);expected=struct.unpack_from('<I',core)[0]
    out=bytearray();i=4
    while len(out)<expected:
        if core[i]==0x80:out.append(core[i+1]);i+=2
        elif core[i]==0:
            n=core[i+1]+1;i+=2;out.extend(core[i:i+n]);i+=n
        else:
            code=struct.unpack_from('<H',core,i)[0];i+=2;l=code&15;dist=(code>>4)+15
            out.extend(out[len(out)-dist:len(out)-dist+l])
    assert len(out)==expected
    (FW/'MOLEBOX_CORE.bin').write_bytes(out)
    print('CORE',len(out),out[:64].hex(),flush=True)
    extraoff,extracount=struct.unpack_from('<II',stb,100)
    dest=FW/'FateFD_extra.dec.bin'
    if not dest.exists():
        with dest.open('wb') as f:
            for pos in range(extraoff,extraoff+extracount,8*1024*1024):
                end=min(pos+8*1024*1024,extraoff+extracount);f.write(ndes_ecb(b[pos:end],key))
            f.write(b[extraoff+extracount:])
    print('EXTRA',dest.stat().st_size,dest.open('rb').read(64).hex(),flush=True)
    ca=np.frombuffer(bytes(out),dtype=np.uint8);seed=ca[:-34].copy();valid=np.ones(len(seed),dtype=bool)
    for j in range(33):
        decoded=ca[j+1:j+1+len(seed)]^seed
        valid &= ((decoded>=48)&(decoded<=57))|((decoded>=65)&(decoded<=70)) if j<32 else decoded==0
        seed=(seed>>1)|((seed<<7)&255)
    candidates=[b'7233DA04FCF24B388408701CB1F874F3']
    strings=[]
    for pos in range(60000,105000):
        seed=int(ca[pos]);s=bytearray()
        for v in ca[pos+1:pos+250]:
            d=int(v)^seed;seed=((seed>>1)|(seed<<7))&255
            if d==0:
                if len(s)>=6:strings.append((pos,bytes(s)))
                break
            if not (32<=d<=126 or d in (9,10,13)):break
            s.append(d)
    jsonwrite(FW/'CORE_XOR_STRINGS.json',[(p,s.decode()) for p,s in strings])
    candidates.extend(s for p,s in strings)
    for pos in np.where(valid)[0]:
        seed=int(ca[pos]);s=bytearray()
        for v in ca[pos+1:pos+33]:s.append(int(v)^seed);seed=((seed>>1)|(seed<<7))&255
        print('KEY_STRING',pos,s.decode(),flush=True);candidates.append(bytes(s))
    for s in candidates:
        k=hashlib.md5(s).digest()
        for alg in [ndes_ecb,bf_ecb]:
            head=alg(b[cat:cat+8],k);count,crc=struct.unpack('<II',head)
            if 0<count<65536 and cat>count:
                plain=cbc(b[cat-count:cat],k,alg)
                print('CAT_CRC',hex(zlib.crc32(plain)),hex(crc),'BYTES',repr(plain[:800]),flush=True)
                if zlib.crc32(plain)==crc:(FW/'MOLEBOX_CATALOG.bin').write_bytes(plain);jsonwrite(FW/'MOLEBOX_CATALOG_KEY.json',dict(string=s.decode(),algorithm=alg.__name__))
    k=hashlib.md5(candidates[0]).digest()
    for alg in [ndes_ecb,bf_ecb]:
        head=alg(b[cat:cat+8],k);print('CAT_HDR',alg.__name__,head.hex(),struct.unpack('<II',head),flush=True)
        count,crc=struct.unpack('<II',head)
        if 0<count<65536 and cat>count:
            plain=cbc(b[cat-count:cat],k,alg)
            print('CAT_CRC',hex(zlib.crc32(plain)),hex(crc),'BYTES',repr(plain[:800]),flush=True)
            if zlib.crc32(plain)==crc:(FW/'MOLEBOX_CATALOG.bin').write_bytes(plain)
CRC16_TABLE=[]
for i in range(256):
    for _ in range(8):i=(i>>1)^(0xa001 if i&1 else 0)
    CRC16_TABLE.append(i)
def crc16(b):
    n=0;t=CRC16_TABLE
    for x in b:n=(n>>8)^t[(n^x)&255]
    return n

def extract_package(path,start,key,container):
    from fha_extract import safe_path
    used=set();rows=[];errors=[];verified=0;blocks_checked=0
    with path.open('rb') as f:
        f.seek(start);data=f.read(16)
        off=struct.unpack_from('<I',data)[0]+start if ndes_ecb(data[4:12],key)==b'QUICKBOX' else start
        f.seek(off);h=cbc(f.read(48),key);tree_size,root,back,crc=struct.unpack_from('<4I',h,4)
        base=off-back
        assert 0<tree_size<128*2**20 and base>=0
        f.seek(off-tree_size);tree=cbc(f.read(tree_size),key)
        assert zlib.crc32(tree)==crc,'Directory CRC mismatch'
        jsonwrite(FW/(path.name+'.molebox_header.json'),dict(source=str(path),offset=off,base=base,tree_size=tree_size,root=root,tree_crc32=crc))
        out=FHA/'RawExtracted/Molebox'/container
        def walk(pos,parent=''):
            nameptr,namelen=struct.unpack_from('<II',tree,pos+8)
            flags,size,count=struct.unpack_from('<III',tree,pos+40)
            sign=tree[pos+20:pos+36].hex()
            name=tree[nameptr:nameptr+namelen*2].decode('utf-16-le') if nameptr and not flags&1 else '__hidden_name_'+sign
            if flags&0x80000000:
                prefix=parent+'/'+name if pos!=root else ''
                for child in struct.unpack_from('<'+'I'*count,tree,pos+52):walk(child,prefix)
                return
            logical=(parent+'/'+name).lstrip('/');target=safe_path(out,logical,len(rows),used);target.parent.mkdir(parents=True,exist_ok=True)
            blocks=[struct.unpack_from('<HHHHI',tree,pos+52+i*12) for i in range(count)]
            nonlocal verified,blocks_checked
            total=0;bad=[];digest=hashlib.sha256();head=b''
            temp=target.with_name(target.name+'.partial')
            with temp.open('wb') as dst:
                for k in range(0,len(blocks),128):
                    group=blocks[k:k+128];raw=[]
                    for ps,rs,fl,cr,bo in group:
                        f.seek(base+bo);raw.append(f.read(ps))
                    joined=b''.join(b[:len(b)//8*8] for b,block in zip(raw,group) if block[2]&4)
                    decrypted=ndes_ecb(joined,key) if joined else b'';at=0
                    for j,(ps,rs,fl,cr,bo) in enumerate(group):
                        b=raw[j]
                        if fl&4:
                            n=len(b)//8*8;d=decrypted[at:at+n];at+=n
                            b=np.bitwise_xor(np.frombuffer(d,dtype=np.uint8),np.frombuffer(b'\0'*8+b[:n-8],dtype=np.uint8)).tobytes()+b[n:]
                        if fl&2:b=zlib.decompress(b)
                        b=b[:rs];actual=crc16(b);blocks_checked+=1
                        if len(b)!=rs or actual!=cr:bad.append(dict(block=k+j,expected_crc16=cr,actual_crc16=actual))
                        if not head:head=b[:64]
                        digest.update(b);total+=len(b);dst.write(b)
            if total!=size:bad.append(dict(reason='File size mismatch',expected=size,actual=total))
            temp.replace(target);fmt=signature(head,pathlib.Path(logical).suffix)
            if fmt=='XP3' and not target.suffix:
                p=target.with_suffix('.xp3');target.rename(p);target=p;logical+='.xp3'
            if bad:errors.append(dict(path=logical,errors=bad))
            else:verified+=1
            rows.append(dict(source_version='HollowAtaraxia',source_container=container,source_logical_path=logical,extracted_path=str(target),size=total,sha256=digest.hexdigest(),detected_format=fmt,decrypt_method='Molebox NewDES CBC; directory CRC32 and block CRC16',entry_index=len(rows),name_recovery='UTF16 directory' if nameptr and not flags&1 else 'hidden filename hash retained',container_entry_verified=not bad))
            print('MOLEBOX_FILE',container,logical,total,'verified',not bad,flush=True)
        walk(root)
    return rows,dict(source=str(path),source_container=container,kind='Molebox/NewDES',tool='audited fha_molebox.py',command='python fha_molebox.py --extract '+path.name,expected_entries=len(rows),files_extracted=len(rows),verified_entries=verified,blocks_verified=blocks_checked,status='partial' if errors else 'success',errors=errors)

def extract_all():
    if not (FW/'MOLEBOX_CATALOG.bin').exists():probe()
    c=(FW/'MOLEBOX_CATALOG.bin').read_bytes();pt,pc,mt,mc=struct.unpack_from('<4I',c);key=c[mt+8:mt+24]
    old=[json.loads(s) for s in (FHA/'Metadata/RAW_ASSETS.jsonl').open(encoding='utf-8')]
    logs=json.loads((FHA/'Metadata/EXTRACTION_LOG.json').read_text('utf-8'))
    only=set(sys.argv[2:]);specs=[(next(ROOT.rglob(n)),0,n) for n in ['language_SChinese.xp3','voice.xp3','voice2.xp3'] if not only or n in only]
    exe=next(ROOT.rglob('FateFD.exe'));offset=struct.unpack_from('<I',c,pt)[0]
    if not only or 'FateFD.exe' in only:specs.append((exe,offset,'FateFD.exe/default'))
    for p,start,name in specs:
        rs,log=extract_package(p,start,key,name);old=[r for r in old if r['source_container']!=name];old.extend(rs)
        logs=[x for x in logs if pathlib.Path(x['source_container']).name!=p.name or x.get('kind') not in ('XP3','Molebox/NewDES')]
        logs.append(log);jsonwrite(FHA/'Metadata/EXTRACTION_LOG.json',logs)
        with (FHA/'Metadata/RAW_ASSETS.jsonl').open('w',encoding='utf-8') as f:
            for r in old:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    jsonwrite(FHA/'Metadata/MOLEBOX_EXTRACTION.json',[x for x in logs if x['kind']=='Molebox/NewDES'])
if __name__=='__main__':extract_all() if '--extract' in sys.argv else probe()
