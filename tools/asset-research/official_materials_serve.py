from official_materials import *
import http.server,socketserver
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(L),**kwargs)
    def log_message(self,fmt,*args):
        with (W/'logs/official_material_http.txt').open('a',encoding='utf-8') as f:f.write(now()+' '+fmt%args+'\n')
with socketserver.ThreadingTCPServer(('127.0.0.1',0),Handler) as server:
    port=server.server_address[1];writejson(T/'HTTP_SERVER.json',{'pid':os.getpid(),'port':port,'url':f'http://127.0.0.1:{port}/ReferenceBooks/index.html','bind':'127.0.0.1','root':str(L),'temporary':True,'created_at':now()});log('Serving',port);server.serve_forever()
