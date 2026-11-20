"""Tiny stdlib-only HTTP server for the Knot web UI.

Endpoints:
  GET  /            the single-page UI (web/index.html)
  GET  /api/graph  whole graph as JSON {nodes, edges}
  GET  /api/stats  node/relationship counts
  GET  /api/ask?q=...   ask the graph, returns {answer, cypher, paths}
  POST /api/remember    JSON {kind, props} or {kind: note, text, about}
"""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from . import ask as ask_mod
from . import remember as rem
from .db import KnotDB
from .schema import seed as seed_graph

HERE = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(HERE, "..", "web")


class Handler(BaseHTTPRequestHandler):
    db_path = None

    def log_message(self, *args):
        pass  # keep the demo output clean

    def _send_json(self, payload, status=200):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path, content_type):
        with open(path, "rb") as fh:
            body = fh.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            self._send_file(os.path.join(WEB_DIR, "index.html"),
                            "text/html; charset=utf-8")
            return
        with KnotDB(self.db_path) as db:
            if parsed.path == "/api/graph":
                self._send_json(ask_mod.export_graph(db))
            elif parsed.path == "/api/stats":
                self._send_json(ask_mod.stats(db))
            elif parsed.path == "/api/ask":
                q = parse_qs(parsed.query).get("q", [""])[0]
                self._send_json(ask_mod.ask(db, q))
            else:
                self._send_json({"error": "not found"}, status=404)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/remember":
            self._send_json({"error": "not found"}, status=404)
            return
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length) or b"{}")
        kind = payload.get("kind", "")
        try:
            with KnotDB(self.db_path) as db:
                if kind == "note":
                    rem.remember_note(db, payload["text"],
                                      payload.get("about_label"),
                                      payload.get("about"))
                    self._send_json({"ok": True, "saved": payload["text"]})
                else:
                    props = payload.get("props", {})
                    rem.remember_node(db, kind.capitalize(), props)
                    self._send_json({"ok": True, "saved": props})
        except (ValueError, KeyError) as exc:
            self._send_json({"ok": False, "error": str(exc)}, status=400)


def serve(db_path, port=8765):
    Handler.db_path = db_path
    with KnotDB(db_path) as db:
        seed_graph(db)
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Knot is live at http://127.0.0.1:{port}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
