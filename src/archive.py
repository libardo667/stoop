"""Where forgotten entries go. Nothing the box composts is truly destroyed.

Append-only JSON-lines under `prune/history/` (local, gitignored) — the same
"retire without erasing" ethos the prune harness runs on. The live box stays an
honest snapshot of the recent block; the full record lives here, locally.
"""

from __future__ import annotations

import json
import os
import time

from .store import Entry


class JsonlArchive:
    def __init__(self, path: str):
        self._path = path

    def record(self, entry: Entry, reason: str = "composted", at: "float | None" = None) -> None:
        os.makedirs(os.path.dirname(self._path) or ".", exist_ok=True)
        row = {**entry.to_dict(), "evicted_at": time.time() if at is None else at, "reason": reason}
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
