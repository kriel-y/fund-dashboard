"""Fund Proxy — same-origin proxy for eastmoney APIs.
Serves static files AND proxies fund/index API requests.
"""
import http.server, urllib.request, json, re, os

DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(DIR)

class PX(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        m = re.match(r'^/api/fund/(\d+)$', self.path)
        if m:
            return self._proxy_fund(m.group(1))
        if self.path == '/api/index':
            return self._proxy_index()
        self._serve_file()

    def _proxy_fund(self, code):
        url = f'https://api.fund.eastmoney.com/f10/lsjz?callback=jQuery&fundCode={code}&pageIndex=1&pageSize=5'
        try:
            req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0','Referer':'https://fund.eastmoney.com/'})
            data = urllib.request.urlopen(req, timeout=15).read()
            self._ok('application/javascript; charset=utf-8', data)
        except Exception as e:
            self._fail(f'fund/{code}: {e}')

    def _proxy_index(self):
        url = 'https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&fields=f2,f3,f4,f12,f14&secids=1.000001,0.399001,0.399006,1.000688,1.000300,0.399933'
        try:
            data = urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=15).read()
            self._ok('application/json; charset=utf-8', data)
        except Exception as e:
            self._fail(f'index: {e}')

    def _serve_file(self):
        fpath = '.' + self.path.split('?')[0]
        if fpath == './': fpath = './index.html'
        if os.path.isfile(fpath):
            ctype = 'text/html; charset=utf-8'
            if fpath.endswith('.js'): ctype = 'application/javascript'
            elif fpath.endswith('.css'): ctype = 'text/css'
            elif fpath.endswith('.json'): ctype = 'application/json'
            with open(fpath, 'rb') as f:
                self._ok(ctype, f.read())
        else:
            self._send(404, b'Not found')

    def _ok(self, ctype, data):
        self._send(200, data, ctype)

    def _fail(self, msg):
        self._send(502, json.dumps({'error': msg}).encode())

    def _send(self, code, data, ctype='text/plain'):
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.end_headers()

if __name__ == '__main__':
    http.server.HTTPServer(('0.0.0.0', 8899), PX).serve_forever()
