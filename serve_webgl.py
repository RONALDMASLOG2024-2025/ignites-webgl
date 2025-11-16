#!/usr/bin/env python3
"""
Simple static file server that correctly serves pre-compressed Unity WebGL files
(.gz) with the `Content-Encoding: gzip` header and proper Content-Type values.

Usage:
    python serve_webgl.py 8000

Then open http://localhost:8000/

This handler intentionally keeps things small and dependency-free. It supports
HEAD and GET requests. It does not implement byte-range requests; if you need
range support for very large files, use a production server or a more advanced
Python server library.
"""

import http.server
import socketserver
import sys
import os
import urllib.parse
import mimetypes
import shutil

PORT = 8000

class GzipRequestHandler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        """Serve a file, adding Content-Encoding for .gz files and correct Content-Type."""
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            for index in ("index.html", "index.htm"):
                index_path = os.path.join(path, index)
                if os.path.exists(index_path):
                    path = index_path
                    break
        if not os.path.exists(path):
            return self.send_error(404, "File not found")

        # If the file is a .gz file, we will serve it as-is and set Content-Encoding: gzip
        gz = path.endswith('.gz')
        # Decide the content type based on the original filename (strip the .gz)
        content_type, _ = mimetypes.guess_type(path[:-3] if gz else path)
        if content_type is None:
            # Some Unity files need explicit types
            if path.endswith('.wasm.gz') or path.endswith('.wasm'):
                content_type = 'application/wasm'
            elif path.endswith('.js.gz') or path.endswith('.js') or path.endswith('.framework.js.gz'):
                content_type = 'application/javascript'
            elif path.endswith('.data.gz') or path.endswith('.data'):
                content_type = 'application/octet-stream'
            else:
                content_type = 'application/octet-stream'

        try:
            f = open(path, 'rb')
        except OSError:
            return self.send_error(404, "File not found")

        self.send_response(200)
        self.send_header('Content-Type', content_type)
        if gz:
            self.send_header('Content-Encoding', 'gzip')
        fs = os.fstat(f.fileno())
        self.send_header('Content-Length', str(fs[6]))
        self.send_header('Last-Modified', self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f

    # Optional: make logging a little cleaner
    def log_message(self, format, *args):
        sys.stdout.write("[web] %s - - [%s] %s\n" % (self.client_address[0], self.log_date_time_string(), format%args))


if __name__ == '__main__':
    if len(sys.argv) > 1:
        try:
            PORT = int(sys.argv[1])
        except ValueError:
            print('Port must be an integer')
            sys.exit(1)
    os.chdir(os.path.dirname(os.path.abspath(__file__)) or '.')
    handler = GzipRequestHandler
    with socketserver.TCPServer(('0.0.0.0', PORT), handler) as httpd:
        print(f"Serving Webignites on http://0.0.0.0:{PORT} (press CTRL+C to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\nShutting down')
            httpd.server_close()
