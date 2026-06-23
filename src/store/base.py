from __future__ import annotations

import abc
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Entry:
    """One thing left on the stoop.

    Text + when, and an opaque local id. That is the whole record — there is no
    author, no identity, nothing that says who. (A deliberate non-goal.)
    """

    id: str
    text: str
    ts: float  # unix seconds, minted by the store at add() time

    def to_dict(self) -> dict:
        return asdict(self)


class Store(abc.ABC):
    """The behavior contract every store must satisfy.

    The laptop JSON store, the future LittleFS store (major 05), and whatever
    the forgetting engine (major 02) wraps around them all answer to this shape.
    """

    @abc.abstractmethod
    def add(self, text: str) -> Entry:
        """Mint and persist an Entry from already-validated text; return it."""

    @abc.abstractmethod
    def list(self) -> "list[Entry]":
        """All current entries, most-recent-first."""
