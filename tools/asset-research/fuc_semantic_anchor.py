"""One selector stop only: semantic pointers and arguments, no pose tracing."""
from fuc_semantic_debugger import *
import argparse,struct,time
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--button',required=True);ap.add_argument('--direction');ap.add_argument('--bank-return',action='store_true');ap.add_argument('--folder',required=True);a=ap.parse_args();out=SW/'Anchors'/a.folder;assert not out.exists();out.mkdir(parents=True)
    d=SemanticDebugger();bp=0x08886410;result={}
    try:
        d.pause();assert not d.call('cpu.breakpoint.list').get('breakpoints')
        d.call('cpu.breakpoint.add',address=bp,enabled=True)
        pressed={a.button:True}
        if a.direction:pressed[a.direction]=True
        d.call('input.buttons.send',buttons=pressed);d.resume();deadline=time.monotonic()+20
        while time.monotonic()<deadline:
            status=d.call('cpu.status')
            if status.get('stepping'):
                if status['pc']!=bp:raise RuntimeError(status)
                rr=regs(d);result=dict(registers={k:rr[k] for k in ['pc','ra','a0','a1','a2','a3','s0','s1','s2','s3','s4','s5','f12']},timestamp=now(),cpu=status,button=a.button,direction=a.direction,requested_clip=rr['a1'],ram_writes=0,scope='selector arguments and semantic source pointers only')
                for reg,size in [('a0',0x100),('s0',0x80),('s1',0x80),('s2',0x100),('s5',0x100)]:
                    addr=rr[reg];data=d.read(addr,size);(out/(reg+'.bin')).write_bytes(data);result[reg]=dict(address=hex(addr),words=list(struct.unpack('<'+'I'*(size//4),data)))
                context=(out/'s5.bin').read_bytes();actor=struct.unpack_from('<I',context,0x14)[0]
                if 0x08800000<actor<0x09fff000:
                    ab=d.read(actor,0x800);(out/'actor.bin').write_bytes(ab);model=struct.unpack_from('<I',ab,0x3c)[0]
                    cb=d.read(actor+0x14d0,0xd0);(out/'command_fields.bin').write_bytes(cb);result['command_fields']={hex(o):hex(struct.unpack_from('<I',cb,o-0x14d0)[0]) for o in range(0x14d0,0x15a0,4)}
                    mb=d.read(model,0x38);resource=struct.unpack_from('<I',mb,0x34)[0];name=d.read(resource+0x10,64).split(b'\0')[0].decode('ascii','replace');result.update(model_path=name,model=hex(model),actor=hex(actor),character_id=struct.unpack_from('<I',ab,0xc)[0])
                    tb=(out/'s2.bin').read_bytes();sourcebase=struct.unpack_from('<I',tb,4)[0];result.update(source_base=hex(sourcebase),source_file_offset=rr['s0']-sourcebase+32,state_id=struct.unpack_from('<I',tb,0x38)[0])
                    code=name.split('/')[1]
                    from fuc_semantic_payload_probe import payload
                    sr,sb=payload('chr/'+code+'/0000.seq');runtime=d.read(sourcebase,len(sb)-32);(out/'character_seq_runtime.bin').write_bytes(runtime);result['seq_source']=dict(path=sr['physical_path'],sha256=sr['sha256'],runtime_source_header_removed=32,different_words=[hex(o+32) for o in range(0,len(runtime)-3,4) if runtime[o:o+4]!=sb[o+32:o+36]])
                if a.bank_return:
                    ret=rr['ra'];d.call('cpu.breakpoint.remove',address=bp);d.call('cpu.breakpoint.add',address=ret,enabled=True);d.resume();finish=time.monotonic()+20
                    while time.monotonic()<finish:
                        st=d.call('cpu.status')
                        if st.get('stepping'):
                            assert st['pc']==ret;break
                        time.sleep(.01)
                    else:raise TimeoutError('selector return')
                    after=regs(d);pb=d.read(rr['a0'],0x38);(out/'player_after.bin').write_bytes(pb);U=lambda x,o:struct.unpack_from('<I',x,o)[0]
                    banks=list(struct.unpack('<'+'I'*U(pb,0x30),d.read(U(pb,0x2c),U(pb,0x30)*4)));bi=after['v0'];assert 0<=bi<len(banks)
                    h=d.read(banks[bi],16);(out/'selected_bank_header.bin').write_bytes(h);base,count=struct.unpack_from('<HH',h,4);tab=d.read(U(h,8),count*4);(out/'selected_bank_table.bin').write_bytes(tab);relative=[x-banks[bi] if x else 0 for x in struct.unpack('<'+'I'*count,tab)]
                    matches=[]
                    for logical in {x['source_name'] for x in readrows(EU/'Metadata/ANIMATION_INDEX.csv')}:
                        if not logical.startswith('chr/'+code+'/') or not logical.endswith('.mot'):continue
                        sr,raw=payload(logical)
                        if len(raw)==U(h,12) and struct.unpack_from('>I',raw,4)[0]==count and list(struct.unpack_from('>'+'I'*count,raw,16))==relative:matches.append(dict(name=logical,source=sr['physical_path'],sha256=sr['sha256']))
                    result['selector_return']=dict(return_address=hex(ret),bank_index=bi,bank_pointer=hex(banks[bi]),bank_base_clip=base,bank_clip_count=count,clip_number=U(pb,0x1c),clip_pointer=hex(U(pb,0x18)),selected_offset=relative[rr['a1']-base],source_matches=matches,normalization='existing bank verification rule: runtime pointer table relative offsets vs preserved big-endian source offsets',ram_writes=0)
                    assert U(pb,0x1c)==rr['a1'] and U(pb,0x18)==banks[bi]+relative[rr['a1']-base] and matches
                    d.call('cpu.breakpoint.remove',address=ret)
                print(json.dumps({k:v for k,v in result.items() if k not in ['a0','s0','s1','s2','s5','command_fields']}),flush=True);break
            time.sleep(.01)
        else:raise TimeoutError('One semantic selector stop')
    finally:
        d.pause();released={a.button:False}
        if a.direction:released[a.direction]=False
        d.call('input.buttons.send',buttons=released)
        for pending in d.call('cpu.breakpoint.list').get('breakpoints',[]):
            if pending['address'] in (bp,result.get('registers',{}).get('ra')):d.call('cpu.breakpoint.remove',address=pending['address'])
        result['cleanup']=d.call('cpu.breakpoint.list');jsonwrite(out/'ANCHOR.json',result);d.close()
if __name__=='__main__':main()
