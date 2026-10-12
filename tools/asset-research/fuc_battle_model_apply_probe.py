"""Capture a natural SDK matrix application and its complete input/output. Read-only RAM."""
from fuc_battle_function_probe import wait,regs
from fuc_battle_debugger import *
import argparse,struct,time

def snapshot(d,model,out,label):
 b=d.read(model,0x340);(out/f'{label}_model.bin').write_bytes(b)
 u=lambda o:struct.unpack_from('<I',b,o)[0]
 n=u(0x58);sdk=u(0x38);assert 0<n<256
 sh=d.read(sdk,0x40);ptrs=struct.unpack('<'+'I'*n,d.read(struct.unpack_from('<I',sh,0x18)[0],4*n))
 d.dump(u(0x5c),n*0x140,out/f'{label}_runtime_nodes.bin')
 (out/f'{label}_sdk_nodes.bin').write_bytes(b''.join(d.read(p,0x180) for p in ptrs))
 r=dict(model=hex(model),sdk=hex(sdk),node_count=n,path=cstring(d,u(0x34)+0x10),sdk_nodes=[hex(x) for x in ptrs],flags=hex(u(0)))
 jsonwrite(out/f'{label}.json',r)
 return r

def main():
 p=argparse.ArgumentParser();p.add_argument('--model',type=lambda s:int(s,0),required=True);p.add_argument('--folder',required=True);p.add_argument('--count',type=int,default=3);p.add_argument('--button',default='triangle');p.add_argument('--seconds',type=int,default=25);a=p.parse_args();out=BR/a.folder;out.mkdir(parents=True,exist_ok=True);d=BattleDebugger();active=set();rows=[];addr=0x08877378
 try:
  d.pause()
  for bp in d.call('cpu.breakpoint.list').get('breakpoints',[]):d.call('cpu.breakpoint.remove',address=bp['address'])
  d.call('input.buttons.send',buttons={a.button:True})
  for i in range(a.count):
   d.call('cpu.breakpoint.add',address=addr,enabled=True,condition=f'a0==0x{a.model:x}');active.add(addr);d.resume();rr=wait(d,addr,time.monotonic()+a.seconds)
   pre=snapshot(d,a.model,out,f'{i:03d}_entry');pre['registers']=rr;jsonwrite(out/f'{i:03d}_entry.json',pre)
   ra=rr['ra'];d.call('cpu.breakpoint.remove',address=addr);active.remove(addr);d.call('cpu.breakpoint.add',address=ra,enabled=True);active.add(ra);d.resume();ret=wait(d,ra,time.monotonic()+a.seconds)
   post=snapshot(d,a.model,out,f'{i:03d}_post');post['registers']=ret;jsonwrite(out/f'{i:03d}_post.json',post)
   d.call('cpu.breakpoint.remove',address=ra);active.remove(ra);rows.append(dict(sample=i,path=pre['path'],entry=hex(addr),caller=hex(ra)));print(json.dumps(rows[-1]),flush=True)
 finally:
  jsonwrite(out/'MODEL_APPLY_SUMMARY.json',rows);d.pause();d.call('input.buttons.send',buttons={a.button:False})
  for bp in active:d.call('cpu.breakpoint.remove',address=bp)
  d.close()
if __name__=='__main__':main()
