"""The stoop itself — a bounded, self-forgetting set of entries.

`leave()` adds, then forgets back down to capacity. `read()` returns newest-first.
`second()` buys an entry more life. The store is dumb storage; the forgetting
*policy* is pure in `decay.py`; this is the thin orchestration that ties them with
a clock — so an empty hand on the street always finds the box full, fresh, and
bounded, with no one deleting anything by hand.
"""

from __future__ import annotations

import time

from .decay import DecayWeights, pick_eviction
from .store import Entry, Store


class Box:
    def __init__(
        self,
        store: Store,
        *,
        capacity: int,
        weights: DecayWeights,
        archive=None,
        clock=time.time,
    ):
        self._store = store
        self._capacity = capacity
        self._weights = weights
        self._archive = archive
        self._clock = clock

    def read(self) -> "list[Entry]":
        return self._store.list()

    def leave(self, text: str) -> Entry:
        """Add already-validated text, then compost down to capacity."""
        entry = self._store.add(text, ts=self._clock())
        self._forget()
        return entry

    def second(self, entry_id: str) -> "Entry | None":
        """Record one anonymous 'this one stays'. Returns the updated entry, or
        None if it's already gone."""
        current = self._store.get(entry_id)
        if current is None:
            return None
        bumped = Entry(id=current.id, text=current.text, ts=current.ts, seconds=current.seconds + 1)
        self._store.update(bumped)
        return bumped

    def _forget(self) -> None:
        # `count() > capacity` is the laptop predicate; the LittleFS store (major
        # 05) swaps it for a byte budget while reusing the same scoring/eviction.
        while self._store.count() > self._capacity:
            now = self._clock()
            pressure = self._store.count() / self._capacity if self._capacity else 1.0
            victim = pick_eviction(self._store.list(), now, pressure, self._weights)
            removed = self._store.remove(victim.id)
            if removed is None:
                break  # nothing to remove — avoid spinning
            if self._archive is not None:
                self._archive.record(removed, reason="composted", at=now)
