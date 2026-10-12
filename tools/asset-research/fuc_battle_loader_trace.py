"""Natural FAN/AMO resource entry/return capture; breakpoints only, no game RAM writes."""
from fuc_battle_debugger import *
import argparse,time,struct
ENTRY=0x088869d8
def main():
    p=argparse.ArgumentParser();p.add_argument('--seconds',type=float,default=600);p.add_argument('--flags',default='(a1 & 0x5000) != 0');p.add_argument('--folder',default='LoaderTrace');a=p.parse_args()
    out=BR/a.folder;out.mkdir(parents=True,exist_ok=True);d=BattleDebugger();active=set();pending=None;n=len(list(out.glob('entry_*.json')));deadline=time.monotonic()+a.seconds
    try:
        d.pause();d.call('cpu.breakpoint.add',address=ENTRY,enabled=True,condition=a.flags);active.add(ENTRY);d.resume()
        while time.monotonic()<deadline:
            s=d.call('cpu.status')
            if not s.get('stepping'):time.sleep(.2);continue
            rr=regs(d)
            if s['pc']==ENTRY:
                pending=dict(timestamp=now(),path=cstring(d,rr['a0']),flags=hex(rr['a1']),caller_return=hex(rr['ra']),registers=rr,scope='natural execution; original European ISO; read-only breakpoint')
                jsonwrite(out/f'entry_{n:04d}.json',pending);d.call('cpu.breakpoint.remove',address=ENTRY);active.remove(ENTRY)
                d.call('cpu.breakpoint.add',address=rr['ra'],enabled=True);active.add(rr['ra']);d.resume()
            elif pending and s['pc']==int(pending['caller_return'],16):
                ret=rr['v0'];pending['return_registers']=rr;pending['resource']=hex(ret)
                if 0x08800000<=ret<0x0a000000:
                    raw=d.read(ret,0x4c);(out/f'resource_{n:04d}.bin').write_bytes(raw);pending['resource_words']=list(struct.unpack('<19I',raw));pending['resource_name']=raw[16:48].split(b'\0')[0].decode('ascii','replace');payload=struct.unpack_from('<I',raw,0x34)[0];pending['payload']=hex(payload)
                    if 0x08800000<=payload<0x0a000000:(out/f'payload_{n:04d}.bin').write_bytes(d.read(payload,512))
                jsonwrite(out/f'entry_{n:04d}.json',pending);print(json.dumps({k:v for k,v in pending.items() if k not in ('registers','return_registers','resource_words')},ensure_ascii=False),flush=True)
                d.call('cpu.breakpoint.remove',address=s['pc']);active.remove(s['pc']);pending=None;n+=1;d.call('cpu.breakpoint.add',address=ENTRY,enabled=True,condition=a.flags);active.add(ENTRY);d.resume()
            else:print('Unexpected stop '+json.dumps(s),flush=True);break
    finally:
        d.pause()
        for addr in active:
            try:d.call('cpu.breakpoint.remove',address=addr)
            except RuntimeError:pass
        d.resume();d.close();print('Loader trace closed',n,flush=True)
if __name__=='__main__':main()
