from animation_common import *
import http.server, urllib.parse, secrets, argparse, threading, webbrowser
from animation_play import launch
TOKEN=secrets.token_urlsafe(32)
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(L),**kwargs)
    def do_GET(self):
        if self.path=='/api/config':
            b=json.dumps({'token':TOKEN}).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
        super().do_GET()
    def do_POST(self):
        if self.path!='/api/open' or self.headers.get('X-Animation-Token')!=TOKEN:self.send_error(403);return
        if self.headers.get('Origin') not in [None,'http://'+self.headers.get('Host','')]:self.send_error(403);return
        try:
            length=int(self.headers.get('Content-Length','0'));assert 0<length<4096;data=json.loads(self.rfile.read(length));result=launch(shot_id=data['shot_id']);b=json.dumps(result).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
        except Exception as e:self.send_error(400,str(e))
    def log_message(self,*args):pass
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8776);p.add_argument('--open-browser',action='store_true');a=p.parse_args();server=http.server.ThreadingHTTPServer(('127.0.0.1',a.port),Handler);url=f'http://127.0.0.1:{a.port}/AnimationReferences/index.html';log('Local browser',url)
    if a.open_browser:threading.Timer(.2,lambda:webbrowser.open(url)).start()
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
