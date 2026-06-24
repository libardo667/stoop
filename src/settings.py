"""Keeper-adjustable runtime settings: which theme, which skin, an optional custom
prompt. Persisted locally (gitignored) so a keeper's choices survive a restart.
Defaults come from config; nothing here ever leaves the device.
"""

from __future__ import annotations

import json
import os
import tempfile
import threading

from . import config, themes


class Settings:
    def __init__(self, path: str):
        self._path = path
        self._lock = threading.Lock()
        self._data = {"theme": config.DEFAULT_THEME, "skin": config.DEFAULT_SKIN, "prompt": None}
        self._load()

    def _load(self) -> None:
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                disk = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            disk = {}
        if isinstance(disk, dict):
            for key in ("theme", "skin", "prompt"):
                if key in disk:
                    self._data[key] = disk[key]
        # Never trust disk past validation — fall back if a name is unknown.
        if self._data["theme"] not in themes.THEMES:
            self._data["theme"] = config.DEFAULT_THEME
        if self._data["skin"] not in themes.SKINS:
            self._data["skin"] = config.DEFAULT_SKIN

    def _persist(self) -> None:
        directory = os.path.dirname(self._path) or "."
        os.makedirs(directory, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self._path)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    def get(self) -> dict:
        with self._lock:
            return dict(self._data)

    def update(self, changes: dict) -> dict:
        """Apply a partial change (any of theme/skin/prompt). Validates names and
        prompt length; raises ValueError on bad input. Returns the new settings."""
        with self._lock:
            if "theme" in changes:
                if changes["theme"] not in themes.THEMES:
                    raise ValueError("unknown theme")
                self._data["theme"] = changes["theme"]
            if "skin" in changes:
                if changes["skin"] not in themes.SKINS:
                    raise ValueError("unknown skin")
                self._data["skin"] = changes["skin"]
            if "prompt" in changes:
                prompt = changes["prompt"]
                if prompt is None or not str(prompt).strip():
                    self._data["prompt"] = None
                else:
                    prompt = str(prompt).strip()
                    if len(prompt) > config.ENTRY_MAX_LEN:
                        raise ValueError("prompt too long")
                    self._data["prompt"] = prompt
            self._persist()
            return dict(self._data)

    def resolved(self) -> dict:
        d = self.get()
        return themes.resolve(d["theme"], d["skin"], d["prompt"])
