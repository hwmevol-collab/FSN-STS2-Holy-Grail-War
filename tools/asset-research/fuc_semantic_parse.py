"""Read existing source bytes only. No animation, pose or audio algorithms."""
from fuc_semantic_common import *
from fuc_semantic_payload_probe import payload
from fuc_semantic_static import b as elf_bytes,offset

def u(b,o):return struct.unpack_from('<I',b,o)[0]
def cstr(va):return elf_bytes[offset(va):].split(b'\0',1)[0].decode('ascii')
def roster():
    return [dict(character_id=i,internal_code=cstr(u(elf_bytes,offset(0x089ba55c)+4*i)),internal_name=cstr(u(elf_bytes,offset(0x089ba670)+4*i)),code_pointer=hex(u(elf_bytes,offset(0x089ba55c)+4*i)),name_pointer=hex(u(elf_bytes,offset(0x089ba670)+4*i))) for i in range(20)]

def assignments(b):
    found={}
    for o in range(0,len(b)-16,4):
        if u(b,o)==0x00700809 and u(b,o+8)==0x3f and u(b,o+4) in (0x3e8,0x3ec,0x3f0,0x3f8,0x3fc):
            key=hex(u(b,o+4));value=u(b,o+12);assert value<len(b)
            assert key not in found, (key,found.get(key),hex(o))
            found[key]=dict(assignment_offset=o,table_offset=value)
    return found

def normal_table(b,start):
    rows=[];o=start
    while u(b,o)&0xffff!=0xffff:
        assert o+24<=len(b) and len(rows)<256
        w=list(struct.unpack_from('<6I',b,o));rows.append(dict(source_offset=o,input_source=w[0]&0xffff,eligibility=w[0]>>16,direction_any=w[1],button_all=w[2],state_flags_any=w[3],state_flags_excluded=w[4],state_id=w[5],raw_words=w));o+=24
    return rows

def command_program(b,start):
    out=[];o=start;fixed={0:2,1:3,2:4,3:4,4:4,5:6,7:2,8:2,9:2,10:4,11:3,12:1,13:2,14:2,15:2,16:2,17:2,18:3,19:3,24:1}
    for _ in range(1024):
        op=u(b,o)
        if op==6:n=2+u(b,o+4)
        elif op==20:
            p=o+4
            while True:
                w=u(b,p);p+=4
                if not (w&0xff000000) or not all(w&m for m in (0xff0000,0xff00,0xff)):break
                assert p-o<4096
            n=(p-o)//4
        elif op==21:n=u(b,o+4);assert n>=2
        elif op in fixed:n=fixed[op]
        else:raise ValueError(f'unknown command opcode {op} at {o:x}')
        assert o+n*4<=len(b) and n<4096
        w=list(struct.unpack_from('<'+'I'*n,b,o));out.append(dict(offset=o,opcode=op,words=w));o+=n*4
        if op==24:return out
    raise ValueError('program limit')

def special_table(b,start):
    ptrs=[]
    for o in range(start,min(len(b),start+72*4),4):
        p=u(b,o)
        if p==0xffffffff:break
        assert p<len(b) and p%4==0;ptrs.append(p)
    else:raise ValueError('missing command pointer sentinel')
    return [dict(index=i,pointer_slot=start+4*i,source_offset=p,instructions=command_program(b,p)) for i,p in enumerate(ptrs)]

glyph={0:' ',**{i:chr(i+34) for i in range(1,29)},29:'@',**{i:chr(i+35) for i in range(30,56)},**{i:chr(i+35) for i in range(56,61)},**{i:chr(i+36) for i in range(61,91)},0x7c:'↓',0x7d:'←',0x7e:'→',0x84:' or ',0x86:'[L]',0x87:'[M]',0x88:'[H]'}
def text_records(b):
    out=[]
    for o in range(0,len(b)-60,16):
        if u(b,o+32)!=0x20061106:continue
        kind,total=struct.unpack_from('<HH',b,o+36);length=u(b,o+40);rel=u(b,o+44)
        if kind!=1 or rel!=56 or length%2 or total!=56+length or o+total>len(b):continue
        raw=b[o:o+32].split(b'\0',1)[0]
        if not raw or any(c<0x20 or c>0x7e for c in raw):continue
        codes=list(struct.unpack_from('<'+'H'*(length//2),b,o+56));unknown=sorted(set(codes)-set(glyph))
        out.append(dict(key=raw.decode('ascii'),record_offset=o,text_offset=o+56,byte_length=length,glyph_ids=codes,text=''.join(glyph.get(c,f'<glyph:{c:04x}>') for c in codes),unknown_glyphs=unknown))
    return out

def main():
    semantic_frozen();root=SW/'Parsed';root.mkdir(exist_ok=True);allchars=[];fail=[]
    for cr in roster():
        code=cr['internal_code']
        try:
            sr,b=payload('chr/'+code+'/0000.seq');a=assignments(b)
            cr.update(source=sr['physical_path'],sha256=sr['sha256'],assignments=a,normal_commands=normal_table(b,a['0x3e8']['table_offset']) if '0x3e8' in a else [],command_programs=special_table(b,a['0x3f0']['table_offset']) if '0x3f0' in a else [])
        except Exception as e:cr['parse_error']=repr(e);fail.append(dict(code=code,error=repr(e)))
        allchars.append(cr)
    jsonwrite(root/'CHARACTER_COMMANDS.json',allchars);jsonwrite(root/'PARSE_FAILURES.json',fail)
    sr,b=payload('2d/game/0000.seq');texts=text_records(b);jsonwrite(root/'MOVE_UI_TEXT.json',dict(source=sr,texts=texts))
    print('ROSTER',len(allchars),'NORMAL',sum(len(x.get('normal_commands',[])) for x in allchars),'PROGRAMS',sum(len(x.get('command_programs',[])) for x in allchars),'FAILURES',fail)
    groups=collections.defaultdict(list)
    for r in texts:
        if r['key'].endswith('_waza'):groups[r['key']].append(r)
    print('MOVE TEXT GROUPS',dict((k,len(v)) for k,v in groups.items()))
    for c in ('lan','sir','rin'):
        cr=next(x for x in allchars if x['internal_code']==c)
        for p in cr.get('command_programs',[]):
            if any(x['opcode'] in (0,1) and x['words'][1] in (145,155,159) for x in p['instructions']):print(c,p)
    print('UI SAMPLE',[(x['key'],hex(x['record_offset']),x['text']) for x in texts if x['key'] in ('lan_waza','sir_waza','rin_waza')][:8])
if __name__=='__main__':main()
