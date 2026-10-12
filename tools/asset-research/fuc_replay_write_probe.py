from fuc_replay_debugger import *
from fuc_replay_function_probe import snap
import argparse,time
p=argparse.ArgumentParser();p.add_argument('destination',type=lambda x:int(x,0));p.add_argument('--size',type=lambda x:int(x,0),default=64);p.add_argument('--actor',type=lambda x:int(x,0),default=0);p.add_argument('--button');p.add_argument('--count',type=int,default=3);p.add_argument('--seconds',type=int,default=12);p.add_argument('--folder',required=True);a=p.parse_args();out=BR/a.folder;out.mkdir(parents=True,exist_ok=True);d=BattleDebugger();rows=[]
try:
 d.pause();d.call('memory.breakpoint.add',address=a.destination,size=a.size,read=False,write=True,change=False,enabled=True,log=False)
 if a.button:d.call('input.buttons.send',buttons={a.button:True})
 for i in range(a.count):
  d.resume();end=time.monotonic()+a.seconds
  while time.monotonic()<end:
   status=d.call('cpu.status')
   if status.get('stepping'):break
   time.sleep(.1)
  else:rows.append({'status':'not_observed'});break
  rr=regs(d);r=snap(d,rr,out,f'{i:03d}',actor=a.actor);d.dump(a.destination,a.size,out/f'{i:03d}_destination.bin');d.dump(rr['sp'],512,out/f'{i:03d}_stack.bin');rows.append(dict(pc=hex(rr['pc']),ra=hex(rr['ra'])));print(rows[-1],flush=True)
finally:
 d.pause()
 if a.button:d.call('input.buttons.send',buttons={a.button:False})
 d.call('memory.breakpoint.remove',address=a.destination,size=a.size);jsonwrite(out/'SUMMARY.json',rows);d.close()
