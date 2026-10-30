"""Synthetic smoke only. Never merged into application development Compose."""
import json
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer


class Fixture(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_POST(self):
        data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        for line in data.get("logs", []):
            print(line, flush=True)
        if "trace" in data:
            req = urllib.request.Request(
                "http://alloy:4318/v1/traces", json.dumps(data["trace"]).encode(),
                {"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                assert response.status == 200
        result = {}
        for method, path in data.get("proxy", []):
            req = urllib.request.Request("http://docker-socket-proxy:2375" + path, method=method)
            try:
                with urllib.request.urlopen(req, timeout=5) as response:
                    result[method + " " + path] = response.status
            except urllib.error.HTTPError as error:
                result[method + " " + path] = error.code
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())


HTTPServer(("0.0.0.0", 8080), Fixture).serve_forever()
