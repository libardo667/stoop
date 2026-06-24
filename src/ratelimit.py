"""A tiny per-client throttle — the last of the content-firehose guards (minor 32).

No identity is stored: the key is the transient connection address, held in memory
only, never logged and never persisted (see docs/THREAT_MODEL.md). It keeps a flood
of posts from one source from drowning the block, without any content pipeline.

A sliding-window log: cheap, deterministic, and ESP32-friendly. Set max_events <= 0
to disable (a fully open box).
"""

from __future__ import annotations

import threading
import time


class RateLimiter:
    def __init__(self, max_events: int, window_seconds: float, *, clock=time.time, max_keys: int = 1024):
        self._max = max_events
        self._window = window_seconds
        self._clock = clock
        self._max_keys = max_keys
        self._hits: "dict[str, list[float]]" = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        """True if this key may act now; records the event. False if it's over the
        limit in the current window."""
        if self._max <= 0:
            return True  # disabled
        now = self._clock()
        cutoff = now - self._window
        with self._lock:
            recent = [t for t in self._hits.get(key, ()) if t > cutoff]
            if len(recent) >= self._max:
                self._hits[key] = recent  # keep it pruned even when denying
                return False
            recent.append(now)
            self._hits[key] = recent
            if len(self._hits) > self._max_keys:
                self._sweep(cutoff)
            return True

    def _sweep(self, cutoff: float) -> None:
        """Drop keys with no recent activity, so a long-lived box doesn't leak
        memory tracking IPs that came once and left."""
        live: "dict[str, list[float]]" = {}
        for key, timestamps in self._hits.items():
            kept = [t for t in timestamps if t > cutoff]
            if kept:
                live[key] = kept
        self._hits = live
