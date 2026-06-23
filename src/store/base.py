from __future__ import annotations

import abc
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Entry:
    """One thing left on the stoop.

    Text + when + an opaque local id, plus `seconds`: a tally of anonymous "this
    one stays" signals. There is no author, nothing that says who (a deliberate
    non-goal). `seconds` is the only social signal, and it can only *extend* an
    entry's life, never end it.
    """

    id: str
    text: str
    ts: float  # unix seconds, set when the entry is left
    seconds: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


class Store(abc.ABC):
    """The behavior contract every store must satisfy.

    The laptop JSON store and the future LittleFS store (major 05) both answer to
    this shape; the forgetting engine (major 02) drives it through `count`,
    `remove`, and `update`. Storage is dumb here — the *policy* of what to forget
    lives in `decay.py`, orchestrated by `box.py`.
    """

    @abc.abstractmethod
    def add(self, text: str, ts: "float | None" = None) -> Entry:
        """Mint and persist an Entry from already-validated text; return it.
        `ts` defaults to now; callers (the Box) pass it explicitly so a clock can
        be injected for deterministic tests."""

    @abc.abstractmethod
    def list(self) -> "list[Entry]":
        """All current entries, most-recent-first."""

    @abc.abstractmethod
    def get(self, entry_id: str) -> "Entry | None":
        """One entry by id, or None."""

    @abc.abstractmethod
    def remove(self, entry_id: str) -> "Entry | None":
        """Remove and return the entry, or None if it was already gone."""

    @abc.abstractmethod
    def update(self, entry: Entry) -> None:
        """Persist a changed entry in place (matched by id). No-op if absent."""

    @abc.abstractmethod
    def count(self) -> int:
        """How many entries are currently held."""
