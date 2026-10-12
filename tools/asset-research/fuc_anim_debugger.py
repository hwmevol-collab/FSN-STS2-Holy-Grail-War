"""Local PPSSPP debugger client with saved requests, events and memory dumps."""
from fuc_anim_common import *
import websocket,time,base64,argparse
class Debugger:
    def __init__(self):
        frozen();self.seq=0;self.events=[]
        self.ws=websocket.create_connection('ws://127.0.0.1:8991/debugger',subprotocols=['debugger.ppsspp.org'],timeout=3,origin='http://127.0.0.1:8991')
        self.version=self.call('version',name='FUCAnimationValidation',version='1.0')
        self.record('identity',self.version)
    def record(self,kind,value):
        safe=dict(value)
        for k in ['base64','buffer','uri']:
            if k in safe and isinstance(safe[k],str) and len(safe[k])>200:
                raw=base64.b64decode(safe[k].split(',',1)[-1]);safe[k]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),content='binary persisted separately by caller')
        p=AW/'Debugger/SESSION.jsonl';p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('a',encoding='utf-8') as f:f.write(json.dumps(dict(timestamp=now(),kind=kind,data=safe),ensure_ascii=False)+'\n')
    def send(self,event,**args):
        self.seq+=1;req=dict(event=event,ticket=self.seq,**args);self.record('request',req);self.ws.send(json.dumps(req));return self.seq
    def call(self,event,timeout=15,**args):
        ticket=self.send(event,**args);deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            self.ws.settimeout(min(2,max(.1,deadline-time.monotonic())))
            try:r=json.loads(self.ws.recv())
            except websocket.WebSocketTimeoutException:continue
            self.record('response' if r.get('ticket')==ticket else 'broadcast',r)
            if r.get('ticket')==ticket:
                if r['event']=='error':raise RuntimeError(r)
                return r
            self.events.append(r)
            if event in {'cpu.stepping','cpu.stepInto','cpu.stepOver','cpu.stepOut','cpu.runUntil'} and r.get('event')=='cpu.stepping':return r
            if event=='cpu.resume' and r.get('event')=='cpu.resume':return r
        raise TimeoutError(event)
    def pause(self):
        status=self.call('cpu.status')
        if not status.get('stepping',False):self.call('cpu.stepping')
        return self.call('cpu.status')
    def resume(self):self.send('cpu.resume')
    def read(self,address,size):return base64.b64decode(self.call('memory.read',address=address,size=size,replacements=False)['base64'])
    def dump(self,address,size,path):
        path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('wb') as f:
            for offset in range(0,size,1024*1024):f.write(self.read(address+offset,min(1024*1024,size-offset)))
        jsonwrite(str(path)+'.json',dict(address=address,address_hex=hex(address),size=size,sha256=sha(path),cpu_status=self.call('cpu.status'),game_status=self.call('game.status'),version=self.version))
    def screenshot(self,path):
        self.pause()
        try:r=self.call('gpu.buffer.screenshot',type='uri')
        except RuntimeError:r=self.call('gpu.buffer.renderColor',type='uri')
        jsonwrite(AW/'Debugger/LAST_SCREENSHOT_RESPONSE_KEYS.json',{k:(len(v) if isinstance(v,str) else v) for k,v in r.items()})
        raw=base64.b64decode(r['uri'].split(',',1)[1]);assert raw.startswith(b'\x89PNG');path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw);return str(path)
    def close(self):self.ws.close()
def run():
    p=argparse.ArgumentParser();p.add_argument('event');p.add_argument('--params',default='{}');p.add_argument('--dump');p.add_argument('--size',type=lambda x:int(x,0),default=0x1800000);p.add_argument('--address',type=lambda x:int(x,0),default=0x08800000);p.add_argument('--screenshot');a=p.parse_args();d=Debugger()
    try:
        if a.event=='dump':d.pause();d.dump(a.address,a.size,a.dump);log('RAM DUMP',a.dump)
        elif a.event=='screenshot':log('SCREENSHOT',d.screenshot(a.screenshot))
        else:log('RESPONSE',d.call(a.event,**json.loads(a.params)))
    finally:d.close()
if __name__=='__main__':run()
