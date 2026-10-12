"""Capture a bounded natural entry/return chain, never invoking or patching game functions."""
from fuc_battle_debugger import *
import argparse,time,struct
def u32(b,o=0):return struct.unpack_from('<I',b,o)[0]
def snap(d,rr,out,label,character=False,effect=False,actor=0):
    result={'registers':rr,'timestamp':now(),'cpu':d.call('cpu.status')}
    for reg in ['a0','a1','a2','a3','t0','t1']:
        addr=rr[reg]
        if 0x08800000<=addr<0x09fff800:
            size=0x800 if reg=='a0' and character else 0x100
            b=d.read(addr,size);(out/f'{label}_{reg}.bin').write_bytes(b);result[reg]={'address':hex(addr),'size':size,'words':list(struct.unpack('<'+'I'*(size//4),b))[:64]}
            if reg=='a0' and character:
                model=u32(b,0x3c)
                if 0x08800000<=model<0x0a000000:
                    mb=d.read(model,0x340);(out/f'{label}_body_model.bin').write_bytes(mb);result['body_model']=hex(model);resource=u32(mb,0x34)
                    result['model_path']=cstring(d,resource+0x10)
                    n=u32(mb,0x58);nodes=u32(mb,0x5c);sdk=u32(mb,0x38)
                    if 0<n<1000:
                        d.dump(nodes,n*0x140,out/f'{label}_runtime_nodes.bin');result['node_count']=n
                        sb=d.read(sdk,0x40);(out/f'{label}_sdk_header.bin').write_bytes(sb);ptrs=struct.unpack('<'+'I'*n,d.read(u32(sb,0x18),n*4));result['sdk_nodes']=[hex(x) for x in ptrs];(out/f'{label}_sdk_nodes.bin').write_bytes(b''.join(d.read(x,0x180) for x in ptrs))
                        nt=u32(sb,0x34)
                        if 0<nt<256:d.dump(u32(sb,0x24),nt*0x14,out/f'{label}_sdk_texture_table.bin');result['texture_count']=nt
                        remap=u32(mb,0x48);rc=struct.unpack('<h',d.read(remap,2))[0];result['remap']=list(struct.unpack('<'+'h'*(rc+1),d.read(remap,(rc+1)*2)))
                    fan=u32(b,0x1c0)
                    if 0x08800000<=fan<0x09fff800:d.dump(fan,512,out/f'{label}_fan_payload.bin');result['fan_payload']=hex(fan)
    if effect:
        from fuc_battle_effect_capture import effect_snapshot
        result['effect_snapshot']=effect_snapshot(d,rr['a0'],out,label)
    if actor:
        cb=d.read(actor,0x800);(out/f'{label}_actor.bin').write_bytes(cb);body,player=struct.unpack_from('<2I',cb,0x3c);pb=d.read(player,0x100);(out/f'{label}_actor_player.bin').write_bytes(pb)
        result['actor']=dict(pointer=hex(actor),body=hex(body),player=hex(player),model_path=cstring(d,u32(d.read(body,0x38),0x34)+0x10),clip_index=u32(pb,0x1c),time=struct.unpack_from('<f',pb,8)[0],delta_time=struct.unpack_from('<f',pb,12)[0],current_clip=hex(u32(pb,0x18)))
    jsonwrite(out/f'{label}.json',result);return result
def wait(d,addr,deadline):
    while time.monotonic()<deadline:
        s=d.call('cpu.status')
        if s.get('stepping'):
            if s['pc']!=addr:raise ValueError(('unexpected stop',s))
            return regs(d)
        time.sleep(.1)
    raise TimeoutError(hex(addr))
def main():
    p=argparse.ArgumentParser();p.add_argument('address',type=lambda s:int(s,0));p.add_argument('--condition',default='');p.add_argument('--count',type=int,default=1);p.add_argument('--seconds',type=int,default=60);p.add_argument('--character',action='store_true');p.add_argument('--effect',action='store_true');p.add_argument('--actor',type=lambda x:int(x,0),default=0);p.add_argument('--until-end',action='store_true');p.add_argument('--folder',required=True);p.add_argument('--button');a=p.parse_args();out=BR/a.folder;out.mkdir(parents=True,exist_ok=True);d=BattleDebugger();active=set();summary=[]
    try:
        d.pause()
        existing=d.call('cpu.breakpoint.list')
        for bp in existing.get('breakpoints',[]):d.call('cpu.breakpoint.remove',address=bp['address'])
        for i in range(a.count):
            d.call('cpu.breakpoint.add',address=a.address,enabled=True,condition=a.condition);active.add(a.address)
            # Hold through the natural breakpoint; release explicitly in finally.
            if a.button:d.call('input.buttons.send',buttons={a.button:True})
            d.resume()
            rr=wait(d,a.address,time.monotonic()+a.seconds)
            entry=snap(d,rr,out,f'{i:03d}_entry',a.character,a.effect,a.actor);ra=rr['ra'];d.call('cpu.breakpoint.remove',address=a.address);active.remove(a.address);d.call('cpu.breakpoint.add',address=ra,enabled=True);active.add(ra);d.resume();postrr=wait(d,ra,time.monotonic()+a.seconds)
            # a0 may be clobbered on return; preserve captured owner for the result memory snapshot.
            rawpost=postrr.copy();postrr['a0']=rr['a0'];post=snap(d,postrr,out,f'{i:03d}_post',a.character,a.effect,a.actor);post['actual_return_registers']=rawpost;jsonwrite(out/f'{i:03d}_post.json',post)
            d.call('cpu.breakpoint.remove',address=ra);active.remove(ra);summary.append({'entry':hex(a.address),'return':hex(ra),'owner':hex(rr['a0']),'model_path':entry.get('model_path'),'sample':i});print(json.dumps(summary[-1]),flush=True)
            if a.until_end and a.effect and post['effect_snapshot']['state']>=0xf0:break
        jsonwrite(out/'PROBE_SUMMARY.json',summary)
    finally:
        jsonwrite(out/'PROBE_SUMMARY.json',summary)
        d.pause()
        if a.button:d.call('input.buttons.send',buttons={a.button:False})
        for addr in active:
            try:d.call('cpu.breakpoint.remove',address=addr)
            except RuntimeError:pass
        d.close()
if __name__=='__main__':main()
