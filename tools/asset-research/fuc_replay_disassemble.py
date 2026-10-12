from fuc_replay_common import *
import capstone,argparse
def main():
    p=argparse.ArgumentParser();p.add_argument('start',type=lambda s:int(s,0));p.add_argument('end',type=lambda s:int(s,0));p.add_argument('--snapshot');a=p.parse_args();battle_frozen()
    if a.snapshot:b=(BR/'Snapshots'/a.snapshot/'user_ram.bin').read_bytes();start=a.start-0x08800000
    else:b=(W/'fuc/Europe/Executable/EBOOT_DECRYPTED.bin').read_bytes();start=a.start-0x08804000+0x54
    code=b[start:start+a.end-a.start]
    cs=capstone.Cs(capstone.CS_ARCH_MIPS,capstone.CS_MODE_MIPS32|capstone.CS_MODE_LITTLE_ENDIAN);cs.skipdata=True
    s='\n'.join(f'{i.address:08x}: {i.mnemonic:8s} {i.op_str}' for i in cs.disasm(code,a.start));out=BR/f'Static/{a.start:08x}_{a.end:08x}{"_runtime_"+a.snapshot if a.snapshot else ""}.txt';out.parent.mkdir(exist_ok=True);out.write_text(s,encoding='utf-8');print(s)
if __name__=='__main__':main()
