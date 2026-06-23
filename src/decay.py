"""The forgetting policy — pure, deterministic, no I/O.

The mirror image of `prune/pick.py`. There, staleness earns *refuge*: the most
neglected work item gets the best odds of being picked for attention. Here,
staleness-without-love earns the *compost*: an entry's keep-worthiness erodes with
age, and the least keep-worthy is what the box forgets when it runs out of room.
Community attention (a "second") restores life; a fuller box forgets faster.
"""

from __future__ import annotations

from dataclasses import dataclass

from .store import Entry


@dataclass(frozen=True)
class DecayWeights:
    """The proportion knobs. Tunable on purpose — the keeper's call (major 02)."""

    age_horizon_seconds: float  # with no pressure, recency reaches 0 at this age
    pressure_squeeze: float     # 0..1: how much a full box shortens that horizon
    w_recency: float            # weight on freshness
    w_seconds: float            # weight on each "this one stays"


def keep_score(entry: Entry, now: float, pressure: float, w: DecayWeights) -> float:
    """How worth keeping an entry is right now. Higher = safer.

    `recency` falls linearly from 1 (just left) to 0 (aged past the horizon).
    `pressure` (0..1, how full the box is) squeezes the horizon so a crammed box
    forgets faster than an empty one. Each `second` adds a flat boost — the only
    thing a passerby can do to hold a story here.
    """
    pressure = min(1.0, max(0.0, pressure))
    horizon = max(1.0, w.age_horizon_seconds * (1.0 - w.pressure_squeeze * pressure))
    age = max(0.0, now - entry.ts)
    recency = max(0.0, 1.0 - age / horizon)
    return w.w_recency * recency + w.w_seconds * entry.seconds


def pick_eviction(entries: "list[Entry]", now: float, pressure: float, w: DecayWeights) -> Entry:
    """The least keep-worthy entry: lowest score, ties broken by oldest then id.

    Deterministic for a fixed clock, so the forgetting is testable.
    """
    return min(entries, key=lambda e: (keep_score(e, now, pressure, w), e.ts, e.id))
