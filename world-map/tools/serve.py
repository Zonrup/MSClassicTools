"""Local dev server for the world map that never lets the browser use stale files.

    python world-map/tools/serve.py [port]      (default port 8765)

Python's plain `http.server` sends no cache headers, so browsers guess and keep reusing
old copies of js/css/data on a normal reload. This sends `Cache-Control: no-cache`, which
makes the browser check every file on each load (unchanged files still come back as a
quick 304), so a plain reload always shows your latest edits.
"""
import functools
import http.server
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # world-map/


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    handler = functools.partial(NoCacheHandler, directory=str(ROOT))
    with http.server.ThreadingHTTPServer(("", port), handler) as httpd:
        print(f"Serving {ROOT.name}/ at http://localhost:{port} (no-cache)")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
