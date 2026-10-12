"""Loopback audit viewer. Evidence goes only into the new FinalFreeze workspace."""
from fuc_final_audit import L,WORK
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse,parse_qs
import re
ROOT=WORK/'BrowserEvidence';ROOT.mkdir(parents=True,exist_ok=True)
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**k):super().__init__(*a,directory=str(L),**k)
    def do_POST(self):
        q=urlparse(self.path);name=parse_qs(q.query).get('name',[''])[0];size=int(self.headers.get('Content-Length',0));p=ROOT/name
        if q.path!='/evidence' or not re.fullmatch(r'[A-Za-z0-9_-]+\.json',name) or not 0<size<30*1024*1024:self.send_error(400);return
        if p.exists():self.send_error(409);return
        p.write_bytes(self.rfile.read(size));self.send_response(200);self.end_headers();self.wfile.write(b'saved')
    def log_message(self,*a):pass
ThreadingHTTPServer(('127.0.0.1',9006),Handler).serve_forever()
