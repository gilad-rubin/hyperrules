"""Zero-dependency server for the audience-builder demo.

Endpoints:
  GET  /              -> the single-page UI (renders from /api/schema)
  GET  /api/schema    -> the traced config (the form's shape; nothing hardcoded)
  GET  /api/data      -> sample companies + people for the live preview
  POST /api/preview   -> evaluate the two condition trees -> matching records

Run:  python3 app.py   (then open http://localhost:8765)
"""
from __future__ import annotations

import datetime
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import hyperrules
from hyperrules import matches

import config
from hp import trace_schema

# Extend the engine with a "contains" operator (the engine is just a dict of
# operators -> functions, so this is a one-liner, not a fork).
hyperrules.engine.OPERATORS["contains"] = lambda actual, value: bool(actual) and str(value).lower() in str(actual).lower()

SCHEMA = trace_schema(config.audience, title="Audience name")
HERE = os.path.dirname(os.path.abspath(__file__))


def _resolve_today(node: dict) -> dict:
    """Replace the relative value "today" with an actual ISO date before eval."""
    if "combinator" in node:
        return {"combinator": node["combinator"], "conditions": [_resolve_today(c) for c in node.get("conditions", node.get("rules", []))]}
    value = node.get("value")
    if value == "today":
        value = datetime.date.today().isoformat()
    return {"field": node.get("field"), "operator": node.get("operator"), "value": value}


def _matches(tree: dict, records: list, name_key: str) -> list:
    if not tree or not tree.get("conditions", tree.get("rules")):
        return [r[name_key] for r in records]  # an empty condition matches everything
    resolved = _resolve_today(tree)
    out = []
    for record in records:
        try:
            if matches(resolved, record):
                out.append(record[name_key])
        except Exception:
            pass  # a half-typed rule shouldn't crash the preview
    return out


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body, ctype: str = "application/json") -> None:
        data = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            with open(os.path.join(HERE, "index.html"), "rb") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
        elif self.path == "/api/schema":
            self._send(200, SCHEMA)
        elif self.path == "/api/data":
            self._send(200, {"companies": config.COMPANIES, "people": config.PEOPLE})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path == "/api/preview":
            length = int(self.headers.get("Content-Length", 0) or 0)
            payload = json.loads(self.rfile.read(length) or b"{}")
            self._send(200, {
                "companies": _matches(payload.get("companies"), config.COMPANIES, "company_name"),
                "people": _matches(payload.get("people"), config.PEOPLE, "full_name"),
            })
        else:
            self._send(404, {"error": "not found"})

    def log_message(self, *args) -> None:  # quiet
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8765"))
    print("Audience builder demo -> http://localhost:%d" % port)
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
