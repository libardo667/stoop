from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import config
from .store import JsonFileStore

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Path -> (filename in web/, content type). The whole static surface, by name,
# so there's no path-traversal foot-gun on a box that lives in public.
STATIC = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "application/javascript; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
}


def validate_text(raw) -> str:
    """Gatekeep an incoming entry. Text-only, non-empty, length-capped.

    Raises ValueError with a human reason. (Major 32 layers throttles on top.)
    """
    if not isinstance(raw, str):
        raise ValueError("missing text")
    text = raw.strip()
    if not text:
        raise ValueError("say something first")
    if len(text) > config.ENTRY_MAX_LEN:
        raise ValueError(f"too long (max {config.ENTRY_MAX_LEN} characters)")
    return text


class Handler(BaseHTTPRequestHandler):
    server_version = "Stoop/0.1"
    store: JsonFileStore  # set as a class attr on the server's handler

    # --- response helpers ---

    def _send_json(self, obj, status: int = 200) -> None:
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, name: str, ctype: str) -> None:
        try:
            with open(os.path.join(ROOT, config.WEB_DIR, name), "rb") as f:
                body = f.read()
        except FileNotFoundError:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # --- routes ---

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/entries":
            entries = [e.to_dict() for e in self.store.list()]
            self._send_json({"prompt": config.PROMPT, "entries": entries})
            return
        if path in STATIC:
            self._send_file(*STATIC[path])
            return
        self.send_error(404)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/entries":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length).decode("utf-8") if length else ""
        ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip()

        text = None
        if ctype == "application/json":
            try:
                text = (json.loads(raw) or {}).get("text")
            except json.JSONDecodeError:
                text = None
        else:  # x-www-form-urlencoded fallback (works from a plain <form> too)
            vals = parse_qs(raw).get("text")
            text = vals[0] if vals else None

        try:
            clean = validate_text(text)
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=400)
            return

        entry = self.store.add(clean)
        self._send_json(entry.to_dict(), status=201)

    def log_message(self, fmt, *args) -> None:  # noqa: ARG002 - stdlib signature
        # One quiet line per request instead of the noisy default.
        print(f"  {self.command} {self.path}")


def make_server():
    """Build the server and its store. Returned separately so tests can drive
    the store directly without a socket."""
    store = JsonFileStore(os.path.join(ROOT, config.DATA_FILE))
    httpd = ThreadingHTTPServer((config.HOST, config.PORT), Handler)
    Handler.store = store
    return httpd, store


def main() -> None:
    httpd, _ = make_server()
    host, port = httpd.server_address
    shown = host if host not in ("0.0.0.0", "") else "<this-device-ip>"
    print(f"the stoop is open on http://{shown}:{port}")
    print(f"  (network name for later, on hardware: {config.SSID})")
    print("  Ctrl-C to close the box.\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nclosing the stoop.")
        httpd.shutdown()


if __name__ == "__main__":
    main()
