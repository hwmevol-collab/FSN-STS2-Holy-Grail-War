from fuc_semantic_common import *
import capstone,argparse
b=ELF.read_bytes()
shoff=struct.unpack_from('<I',b,32)[0];sections=[struct.unpack_from('<10I',b,shoff+i*40) for i in range(struct.unpack_from('<H',b,48)[0])]
def offset(va):
    for h in sections:
        if h[1]!=8 and h[3]<=va<h[3]+h[5]:return h[4]+va-h[3]
    raise ValueError(hex(va))
def address(off):
    for h in sections:
        if h[1]!=8 and h[4]<=off<h[4]+h[5]:return h[3]+off-h[4]
    return None
def disasm(start,end):
    c=capstone.Cs(capstone.CS_ARCH_MIPS,capstone.CS_MODE_MIPS32|capstone.CS_MODE_LITTLE_ENDIAN);c.skipdata=True
    return '\n'.join(f'{i.address:08x}: {i.mnemonic:8s} {i.op_str}' for i in c.disasm(b[offset(start):offset(start)+end-start],start))
def main():
    p=argparse.ArgumentParser();p.add_argument('mode');p.add_argument('values',nargs='*');a=p.parse_args();semantic_frozen();out=SW/'Static';out.mkdir(exist_ok=True)
    if a.mode=='disasm':
        start,end=map(lambda s:int(s,0),a.values);s=disasm(start,end);(out/f'{start:08x}_{end:08x}.txt').write_text(s,'utf-8');print(s)
    elif a.mode=='strings':
        start,end=map(lambda s:int(s,0),a.values)
        for m in re.finditer(rb'[\x20-\x7e]{3,}',b[start:end]):
            o=start+m.start();print(hex(o),hex(address(o) or 0),repr(m[0].decode()))
    elif a.mode=='refs':
        target=int(a.values[0],0);ptr=struct.pack('<I',target);print('POINTERS',[(hex(i),hex(address(i) or 0)) for i in range(0,len(b)-3,4) if b[i:i+4]==ptr])
        hi=((target+0x8000)>>16)&0xffff;low=target&0xffff
        for h in sections:
            if not h[2]&4:continue
            for o in range(h[4],h[4]+h[5]-3,4):
                w=struct.unpack_from('<I',b,o)[0]
                if w>>26==15 and w&0xffff==hi:
                    reg=(w>>16)&31
                    for j in range(o+4,min(o+80,h[4]+h[5]-3),4):
                        v=struct.unpack_from('<I',b,j)[0]
                        if v&0xffff==low and (v>>21)&31==reg:print('CODE',hex(address(o)),hex(address(j)),hex(w),hex(v))
    elif a.mode=='words':
        start,end=map(lambda s:int(s,0),a.values)
        for va in range(start,end,16):print(hex(va),' '.join(f'{x:08x}' for x in struct.unpack_from('<4I',b,offset(va))))
if __name__=='__main__':main()
