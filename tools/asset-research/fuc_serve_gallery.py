from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
if __name__=='__main__':ThreadingHTTPServer(('127.0.0.1',8986),partial(SimpleHTTPRequestHandler,directory='E:/FSN_MASTER_ASSET_LIBRARY')).serve_forever()
