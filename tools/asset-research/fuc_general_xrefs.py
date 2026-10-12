"""Find direct MIPS J/JAL references to a scoped runtime function in the preserved ELF."""
from fuc_general_common import *
import argparse
def main():
 p=argparse.ArgumentParser();p.add_argument('targets',nargs='+',type=lambda x:int(x,0));a=p.parse_args();battle_frozen();b=(W/'fuc/Europe/Executable/EBOOT_DECRYPTED.bin').read_bytes();rows=[]
 shoff=struct.unpack_from('<I',b,32)[0];num=struct.unpack_from('<H',b,48)[0]
 for i in range(num):
  h=struct.unpack_from('<10I',b,shoff+i*40)
  if not h[2]&4:continue
  for o in range(h[4],h[4]+h[5]-3,4):
   v=struct.unpack_from('<I',b,o)[0];va=o-h[4]+h[3]
   if v>>26 in (2,3):
    dest=((va+4)&0xf0000000)|((v&0x3ffffff)<<2)
    if dest in a.targets:rows.append(dict(caller=hex(va),target=hex(dest),kind='jal' if v>>26==3 else 'j',elf_offset=hex(o),executable_section=True))
 out=BR/'Static'/('xrefs_exec_'+'_'.join(f'{x:08x}' for x in a.targets)+'.json');jsonwrite(out,rows);print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
