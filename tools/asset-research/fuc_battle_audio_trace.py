"""Capture original SAS key-on calls and the selected voice record/payload at entry."""
from fuc_battle_function_probe import wait,snap
from fuc_battle_debugger import *
import time,struct

def main():
 d=BattleDebugger();out=BR/'AudioKeyOnPayload';out.mkdir(exist_ok=True);active=set();rows=[];addr=0x0894a1ac
 try:
  d.pause();d.call('input.buttons.send',buttons={'triangle':False});d.resume();time.sleep(.7);d.pause()
  d.call('input.buttons.send',buttons={'triangle':True})
  for i in range(3):
   d.call('cpu.breakpoint.add',address=addr,enabled=True);active.add(addr);d.resume();rr=wait(d,addr,time.monotonic()+15)
   j=snap(d,rr,out,f'{i:03d}_entry',actor=0x09c09700);slot=rr['a0'];assert 0<=slot<32
   record=0x08a142b4+slot*0x68;rb=d.read(record,0x68);(out/f'{i:03d}_voice_record.bin').write_bytes(rb);ptr,size=struct.unpack_from('<2I',rb,0x20);assert 0<size<1000000
   payload=out/f'{i:03d}_adpcm.bin';d.dump(ptr,size,payload)
   j['sas']=dict(slot=slot,voice_record=hex(record),payload_pointer=hex(ptr),size=size,sha256=sha(payload));jsonwrite(out/f'{i:03d}_entry.json',j)
   d.call('cpu.breakpoint.remove',address=addr);active.remove(addr);ra=rr['ra'];d.call('cpu.breakpoint.add',address=ra,enabled=True);active.add(ra);d.resume();post=wait(d,ra,time.monotonic()+15);jsonwrite(out/f'{i:03d}_return.json',post);d.call('cpu.breakpoint.remove',address=ra);active.remove(ra)
   rows.append(dict(sample=i,**j['sas'],actor=j['actor'],return_value=post['v0']));print(json.dumps(rows[-1]),flush=True)
 finally:
  jsonwrite(out/'AUDIO_KEYON_SUMMARY.json',rows);d.pause();d.call('input.buttons.send',buttons={'triangle':False})
  for bp in active:d.call('cpu.breakpoint.remove',address=bp)
  d.close()
if __name__=='__main__':main()
