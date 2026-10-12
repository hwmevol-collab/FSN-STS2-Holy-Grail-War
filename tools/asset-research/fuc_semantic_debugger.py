from fuc_semantic_common import *
from fuc_anim_debugger import Debugger
import argparse,time,base64
class SemanticDebugger(Debugger):
    def __init__(self):semantic_frozen();super().__init__()
    def record(self,kind,value):
        safe=dict(value)
        for k in ['base64','buffer','uri']:
            if k in safe and isinstance(safe[k],str) and len(safe[k])>200:
                raw=base64.b64decode(safe[k].split(',',1)[-1]);safe[k]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        p=SW/'Debugger/SESSION.jsonl';p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('a',encoding='utf-8') as f:f.write(json.dumps(dict(timestamp=now(),kind=kind,data=safe),ensure_ascii=False)+'\n')
    def screenshot(self,path):
        self.pause();r=self.call('gpu.buffer.screenshot',type='uri')
        raw=base64.b64decode(r['uri'].split(',',1)[1]);p=pathlib.Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);return str(p)
def regs(d):
    r=d.call('cpu.getAllRegs');return {n:v for c in r['categories'] for n,v in zip(c['registerNames'],c['uintValues'])}
def main():
    p=argparse.ArgumentParser();p.add_argument('action');p.add_argument('args',nargs='*');p.add_argument('--hold',type=float,default=.1);p.add_argument('--settle',type=float,default=.3);a=p.parse_args();d=SemanticDebugger()
    try:
        if a.action=='buttons':
            for button in a.args:
                d.pause();d.call('input.buttons.send',buttons={button:True});d.resume();time.sleep(a.hold);d.pause();d.call('input.buttons.send',buttons={button:False});d.resume();time.sleep(a.settle)
            d.pause()
        elif a.action=='status':print(json.dumps(d.call('game.status')));print(json.dumps(d.call('cpu.status')))
        elif a.action=='resume':d.resume()
        elif a.action=='pause':d.pause()
        elif a.action=='advance':d.resume();time.sleep(min(60,float(a.args[0])));d.pause()
        elif a.action=='screenshot':print(d.screenshot(SW/'UI'/a.args[0]))
        elif a.action=='dump':d.pause();d.dump(int(a.args[0],0),int(a.args[1],0),SW/'Snapshots'/a.args[2])
        else:print(json.dumps(d.call(a.action,**json.loads(a.args[0] if a.args else '{}'))))
    finally:d.close()
if __name__=='__main__':main()
