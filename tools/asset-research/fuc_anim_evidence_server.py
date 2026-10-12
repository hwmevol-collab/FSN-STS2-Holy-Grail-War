"""Loopback-only receiver for diagnostic viewer evidence and previews."""
from fuc_anim_common import *
from http.server import SimpleHTTPRequestHandler,HTTPServer
import urllib.parse
root=AW/'Playback';root.mkdir(parents=True,exist_ok=True)
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(L),**kwargs)
    def reply(self,code,msg):
        self.send_response(code);self.send_header('Access-Control-Allow-Origin','http://127.0.0.1:8986');self.send_header('Access-Control-Allow-Methods','POST, OPTIONS');self.send_header('Access-Control-Allow-Headers','Content-Type');self.end_headers();self.wfile.write(msg.encode())
    def do_OPTIONS(self):self.reply(200,'ok')
    def do_POST(self):
        q=urllib.parse.urlparse(self.path);name=urllib.parse.parse_qs(q.query).get('name',[''])[0];size=int(self.headers.get('Content-Length','0'))
        if q.path!='/evidence' or not re.fullmatch(r'[a-zA-Z0-9_-]+\.(json|webm)',name) or not 0<size<30*1024*1024:return self.reply(400,'invalid evidence')
        data=self.rfile.read(size);target=root/name
        if target.exists():return self.reply(409,'existing evidence preserved')
        target.write_bytes(data);log('EVIDENCE SAVED',name,size);self.reply(200,'saved')
    def log_message(self,*a):pass
if __name__=='__main__':log('EVIDENCE SERVER','127.0.0.1:8998');HTTPServer(('127.0.0.1',8998),Handler).serve_forever()
