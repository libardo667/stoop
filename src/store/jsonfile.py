from __future__ import annotations

import json
import os
import tempfile
import threading
import time
import uuid

from .base import Entry, Store


class JsonFileStore(Store):
    """Laptop-era store: entries persisted as a JSON file on disk.

    Writes are atomic (temp file + os.replace) so a crash mid-write can't corrupt
    the box. This is the reference behavior the ESP32/LittleFS store (major 05)
    must reproduce.
    """

    def __init__(self, path: str):
        self._path = path
        self._lock = threading.Lock()
        self._entries: "list[Entry]" = []
        self._load()

    def _load(self) -> None:
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                rows = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            rows = []
        self._entries = [Entry(**row) for row in rows]

    def _persist(self) -> None:
        directory = os.path.dirname(self._path) or "."
        os.makedirs(directory, exist_ok=True)
        rows = [e.to_dict() for e in self._entries]
        fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(rows, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self._path)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    def add(self, text: str) -> Entry:
        with self._lock:
            entry = Entry(id=uuid.uuid4().hex, text=text, ts=time.time())
            self._entries.append(entry)
            self._persist()
            return entry

    def list(self) -> "list[Entry]":
        with self._lock:
            return list(reversed(self._entries))
