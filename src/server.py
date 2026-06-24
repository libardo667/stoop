from __future__ import annotations

import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import config, murmur
from .archive import JsonlArchive
from .box import Box
from .decay import DecayWeights
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
    box: Box  # set as a class attr on the server's handler

    # Drop a connection that goes quiet mid-request, so a slow/stalled client
    # (deliberate or not) can't hold a worker thread open indefinitely.
    timeout = 15

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

    def _read_body(self) -> "str | None":
        """Read the request body within the size cap. Returns the decoded text,
        or None if rejected (an error response was already sent)."""
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            self._send_json({"error": "bad request"}, status=400)
            return None
        if length < 0 or length > config.MAX_BODY_BYTES:
            # Reject before allocating: never read an oversized body into memory.
            self._send_json({"error": "too much at once"}, status=413)
            return None
        # errors="replace": a malformed-UTF-8 body becomes harmless text rather
        # than crashing the handler.
        return self.rfile.read(length).decode("utf-8", errors="replace") if length else ""

    def _field(self, raw: str, name: str):
        """Pull one field from a JSON or x-www-form-urlencoded body."""
        ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip()
        if ctype == "application/json":
            try:
                data = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                return None
            return data.get(name) if isinstance(data, dict) else None
        vals = parse_qs(raw).get(name)
        return vals[0] if vals else None

    # --- routes ---

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/entries":
            entries = [e.to_dict() for e in self.box.read()]
            self._send_json({"prompt": config.PROMPT, "entries": entries})
            return
        if path == "/murmur":
            self._send_json(murmur.derive(self.box.read(), time.time()))
            return
        if path in STATIC:
            self._send_file(*STATIC[path])
            return
        self.send_error(404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path not in ("/entries", "/second"):
            self.send_error(404)
            return
        raw = self._read_body()
        if raw is None:
            return

        if path == "/entries":
            try:
                clean = validate_text(self._field(raw, "text"))
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=400)
                return
            entry = self.box.leave(clean)
            self._send_json(entry.to_dict(), status=201)
        else:  # /second — buy an entry more life
            entry_id = self._field(raw, "id")
            updated = self.box.second(entry_id) if isinstance(entry_id, str) else None
            if updated is None:
                self._send_json({"error": "no such entry"}, status=404)
            else:
                self._send_json(updated.to_dict(), status=200)

    def log_message(self, fmt, *args) -> None:  # noqa: ARG002 - stdlib signature
        # One quiet line per request instead of the noisy default.
        print(f"  {self.command} {self.path}")


def build_box() -> Box:
    """Wire the store, the decay weights, and the compost archive into a Box."""
    store = JsonFileStore(os.path.join(ROOT, config.DATA_FILE))
    archive = JsonlArchive(os.path.join(ROOT, config.ARCHIVE_FILE))
    weights = DecayWeights(
        age_horizon_seconds=config.DECAY_AGE_HORIZON_SECONDS,
        pressure_squeeze=config.DECAY_PRESSURE_SQUEEZE,
        w_recency=config.DECAY_W_RECENCY,
        w_seconds=config.DECAY_W_SECONDS,
    )
    return Box(store, capacity=config.MAX_ENTRIES, weights=weights, archive=archive)


def make_server():
    """Build the server and its Box. Returned separately so tests can drive the
    Box directly without a socket."""
    box = build_box()
    httpd = ThreadingHTTPServer((config.HOST, config.PORT), Handler)
    Handler.box = box
    return httpd, box


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
