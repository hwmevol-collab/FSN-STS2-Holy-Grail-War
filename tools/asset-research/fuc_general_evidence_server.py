"""Local evidence receiver, isolated from the immutable Golden Playback directory."""
from fuc_general_common import *
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import urllib.parse
import argparse
args=argparse.ArgumentParser();args.add_argument('--folder',default='Playback');arg=args.parse_args();root=(BR/arg.folder).resolve();assert root.is_relative_to(BR.resolve());root.mkdir(parents=True,exist_ok=True)
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**k):super().__init__(*a,directory=str(L),**k)
 def reply(self,code,msg):
  self.send_response(code);self.send_header('Access-Control-Allow-Origin','http://127.0.0.1:8986');self.send_header('Access-Control-Allow-Methods','POST, OPTIONS');self.send_header('Access-Control-Allow-Headers','Content-Type');self.end_headers();self.wfile.write(msg.encode())
 def do_OPTIONS(self):self.reply(200,'ok')
 def do_POST(self):
  q=urllib.parse.urlparse(self.path);name=urllib.parse.parse_qs(q.query).get('name',[''])[0];size=int(self.headers.get('Content-Length','0'))
  if q.path!='/evidence' or not re.fullmatch(r'[a-zA-Z0-9_-]+\.(json|webm)',name) or not 0<size<30*1024*1024:return self.reply(400,'invalid')
  p=root/name
  if p.exists():return self.reply(409,'existing preserved')
  p.write_bytes(self.rfile.read(size));self.reply(200,'saved')
 def log_message(self,*a):pass
if __name__=='__main__':battle_frozen();ThreadingHTTPServer(('127.0.0.1',8998),Handler).serve_forever()
