from fuc_battle_common import *
from fuc_anim_debugger import Debugger
class BattleDebugger(Debugger):
    def __init__(self):battle_frozen();super().__init__()
    def record(self,kind,value):
        safe=dict(value)
        import base64
        for k in ['base64','buffer','uri']:
            if k in safe and isinstance(safe[k],str) and len(safe[k])>200:
                raw=base64.b64decode(safe[k].split(',',1)[-1]);safe[k]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),content='binary saved separately by caller')
        p=BR/'Debugger/SESSION.jsonl';p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('a',encoding='utf-8') as f:f.write(json.dumps(dict(timestamp=now(),kind=kind,data=safe),ensure_ascii=False)+'\n')
def regs(d):
    r=d.call('cpu.getAllRegs');return {n:v for c in r['categories'] for n,v in zip(c['registerNames'],c['uintValues'])}
def cstring(d,p,n=128):
    if not 0x08800000<=p<0x0a000000:return None
    return d.read(p,n).split(b'\0')[0].decode('ascii','replace')
