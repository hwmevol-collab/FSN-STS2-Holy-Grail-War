"""Watch existing eft model wrapper flags; capture actual code accesses without RAM writes."""
from fuc_battle_debugger import *
import time,argparse
def main():
 p=argparse.ArgumentParser();p.add_argument('--button',default='triangle');p.add_argument('--count',type=int,default=3);p.add_argument('--seconds',type=int,default=30);p.add_argument('--folder',default='EffectFlagWatch');a=p.parse_args();out=BR/a.folder;out.mkdir(parents=True,exist_ok=True);d=BattleDebugger();models=[x for x in readjson(BR/'Snapshots/PracticeInitial/OBJECT_MAP.json')['models'] if x.get('path','').startswith('eft/')];addresses=[int(x['address'],16) for x in models];active=[];rows=[]
 try:
  d.pause()
  for bp in d.call('cpu.breakpoint.list').get('breakpoints',[]):d.call('cpu.breakpoint.remove',address=bp['address'])
  for bp in d.call('memory.breakpoint.list').get('breakpoints',[]):d.call('memory.breakpoint.remove',address=bp['address'],size=bp['size'])
  before={addr:int.from_bytes(d.read(addr,4),'little') for addr in addresses}
  for addr in addresses:d.call('memory.breakpoint.add',address=addr,size=4,read=False,write=True,change=True,enabled=True,log=False);active.append(addr)
  for i in range(a.count):
   d.resume()
   if i==0:d.send('input.buttons.press',button=a.button,duration=15)
   end=time.monotonic()+a.seconds
   while time.monotonic()<end:
    status=d.call('cpu.status')
    if status.get('stepping'):break
    time.sleep(.1)
   else:rows.append(dict(status='no_write_observed',seconds=a.seconds));break
   rr=regs(d);changes=[]
   for m,addr in zip(models,addresses):
    v=int.from_bytes(d.read(addr,4),'little')
    if v!=before[addr]:changes.append(dict(address=hex(addr),path=m['path'],before=hex(before[addr]),after=hex(v)));before[addr]=v
   row=dict(status=status,registers=rr,changes=changes);jsonwrite(out/f'{i:03d}.json',row);d.dump(rr['pc']-64,256,out/f'{i:03d}_code.bin');d.dump(0x09c09700,0x800,out/f'{i:03d}_lan_character.bin');rows.append(row);print(json.dumps(dict(sample=i,pc=hex(rr['pc']),changes=changes)),flush=True)
  jsonwrite(out/'SUMMARY.json',rows)
 finally:
  d.pause()
  for addr in active:
   try:d.call('memory.breakpoint.remove',address=addr,size=4)
   except RuntimeError:pass
  d.close()
if __name__=='__main__':main()
