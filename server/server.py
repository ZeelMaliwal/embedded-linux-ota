#!/usr/bin/env python3
"""minimal OTA update server. serves manifests and firmware images.
for production you'd want auth, rate limiting, device tracking, etc."""

import http.server
import json
import os
import sys

SERVE_DIR = os.environ.get('OTA_DIR', './updates')

class OTAHandler(http.server.SimpleHTTPHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=SERVE_DIR, **kwargs)

    def do_GET(self):
        # log requests
        print(f"[{self.client_address[0]}] GET {self.path}")
        super().do_GET()

    def do_POST(self):
        # endpoint for devices to report status
        if self.path == '/api/status':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
                print(f"device status: {data}")
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"ok": true}')
            except json.JSONDecodeError:
                self.send_response(400)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    os.makedirs(SERVE_DIR, exist_ok=True)

    with http.server.HTTPServer(('', port), OTAHandler) as httpd:
        print(f"serving updates from {SERVE_DIR} on :{port}")
        httpd.serve_forever()
