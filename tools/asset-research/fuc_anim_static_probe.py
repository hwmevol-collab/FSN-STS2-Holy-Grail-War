from fuc_anim_common import *
from elftools.elf.elffile import ELFFile
import capstone
def run():
    frozen();source=W/'fuc/Europe/Executable/EBOOT_DECRYPTED.bin';b=source.read_bytes();assert hashlib.sha256(b).hexdigest()=='33e8240519a232be40be503f17a23c2dfd5a361177ffb925de444df95dbe6ba7'
    with source.open('rb') as f:
        e=ELFFile(f);sections=[dict(name=s.name,address=s['sh_addr'],offset=s['sh_offset'],size=s['sh_size']) for s in e.iter_sections()];textsec=e.get_section_by_name('.text');code=textsec.data();base=textsec['sh_addr']
    strings=[]
    for m in re.finditer(rb'[ -~]{3,}',b):
        value=m.group().decode('ascii')
        if re.search(r'(?i)\.mot|\.gmo|motion|animation|skeleton|quaternion|bone|\.amo|\.fan|slerp',value):
            s=next((s for s in sections if s['offset']<=m.start()<s['offset']+s['size'] and s['address']),None)
            if s:strings.append(dict(address=s['address']+m.start()-s['offset'],address_hex=hex(s['address']+m.start()-s['offset']),file_offset=m.start(),text=value))
    cs=capstone.Cs(capstone.CS_ARCH_MIPS,capstone.CS_MODE_MIPS32|capstone.CS_MODE_LITTLE_ENDIAN);cs.skipdata=True
    disas=list(cs.disasm(code,base));lookup={x.address:x for x in disas};refs=[]
    targets={r['address']:r for r in strings}
    # Pair actual LUI with nearby addiu/ori of its register; retain candidate labels only.
    for x in disas:
        if x.mnemonic!='lui':continue
        reg,hi=x.op_str.split(', ');hi=int(hi,0)&65535
        for delta in range(4,32,4):
            q=lookup.get(x.address+delta)
            if q is None:continue
            p=q.op_str.split(', ')
            if q.mnemonic in {'addiu','ori'} and len(p)==3 and p[1]==reg:
                try:lo=int(p[2],0);addr=(hi<<16)+(lo if q.mnemonic=='addiu' else (lo&65535))
                except ValueError:continue
                if addr in targets:refs.append(dict(instruction=hex(x.address),finish_instruction=hex(q.address),target=hex(addr),string=targets[addr]['text'],evidence='ELF immediate address pair; containing function role candidate'))
    out=AW/'Static';out.mkdir(parents=True,exist_ok=True)
    (out/'EBOOT_MIPS_DISASSEMBLY.txt').write_text('\n'.join(f'{x.address:08x}: {x.bytes.hex():8s} {x.mnemonic:9s} {x.op_str}' for x in disas),encoding='utf-8')
    csvwrite(out/'ANIMATION_STRING_XREFS.csv',refs,['instruction','finish_instruction','target','string','evidence']);jsonwrite(out/'ELF_LAYOUT.json',dict(source=str(source),sha256=sha(source),sections=sections,strings=strings,xref_count=len(refs),decoder='capstone; VFPU unsupported words may appear as .byte; runtime PPSSPP disassembly is needed for exact VFPU semantics'))
    log('ELF STRINGS',strings);log('ELF XREFS',refs)
if __name__=='__main__':run()
