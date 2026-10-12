"""Read-only natural-game breakpoint trace. No injected function calls or RAM writes."""
from fuc_anim_debugger import *
import struct,sys
FUNCS={0x088833b4:'model_constructor',0x088869d8:'resource_loader',0x08886580:'motion_attach',0x08886410:'clip_select'}
def regs(d):
    r=d.call('cpu.getAllRegs');return {n:v for c in r['categories'] for n,v in zip(c['registerNames'],c['uintValues'])}
def cstring(d,p):
    if not 0x08800000<=p<0x0a000000:return None
    return d.read(p,128).split(b'\0')[0].decode('ascii','replace')
def main():
    folder=AW/'Runtime/Natural';folder=folder/sys.argv[2] if len(sys.argv)>2 else folder;folder.mkdir(parents=True,exist_ok=True)
    d=Debugger();d.pause()
    active=[0x08886410] if len(sys.argv)>2 else list(FUNCS)
    for a in active:d.call('cpu.breakpoint.add',address=a,enabled=True)
    d.resume();deadline=time.monotonic()+float(sys.argv[1] if len(sys.argv)>1 else 600);n=max([int(p.stem.split('_')[1]) for p in folder.glob('trace_*.json')]+[-1])+1
    try:
        while time.monotonic()<deadline:
            s=d.call('cpu.status')
            if not s.get('stepping'):time.sleep(.15);continue
            if s['pc'] not in FUNCS:log('UNEXPECTED STOP',s);break
            rr=regs(d);item=dict(timestamp=now(),kind=FUNCS[s['pc']],pc=hex(s['pc']),registers=rr,scope='natural unmodified game execution; read-only breakpoints')
            if s['pc'] in [0x088833b4,0x088869d8]:item['path']=cstring(d,rr['a0'])
            if s['pc'] in [0x08886580,0x08886410]:
                item['player_address']=hex(rr['a0']);pb=d.read(rr['a0'],0x38);item['player_words']=list(struct.unpack('<14I',pb));(folder/f'trace_{n:04d}_player.bin').write_bytes(pb)
                if s['pc']==0x08886580:
                    item['bank_address']=hex(rr['a3']);d.dump(rr['a3'],0x100,folder/f'trace_{n:04d}_bank.bin')
            jsonwrite(folder/f'trace_{n:04d}.json',item)
            log('NATURAL TRACE',{k:v for k,v in item.items() if k!='registers'})
            n+=1
            if len(sys.argv)>2 and n>=30:break
            d.resume()
    finally:
        d.pause()
        for a in active:
            try:d.call('cpu.breakpoint.remove',address=a)
            except RuntimeError:pass
        if len(sys.argv)<=2:d.resume()
        d.close();log('TRACE CLOSED',n)
if __name__=='__main__':main()
