"""The Murmur — an ambient portrait of the block, derived from the live entries.

Weather, not a feed. Pure and cheap (no deps, no AI) so it runs on the ESP32:

- **what the block keeps saying** — document frequency across entries (a word
  counts once per entry, so one repetitive note can't dominate the block's voice);
- **what the block chose to hold** — the most-kept (most-seconded) story;
- **how long things rest here** — the age of the oldest and newest entries.

The prose is composed in the view layer (the device just serves these numbers);
this stays pure derivation, so it's testable to the word.
"""

from __future__ import annotations

import re
from collections import Counter

from .store import Entry

_WORD = re.compile(r"[a-z][a-z']{2,}")

# Compact stopword set — kept small for the device payload.
STOPWORDS = frozenset(
    """
    a an and are as at be been but by for from had has have he her his how i if in
    is it its just like me my no not of on or our out she so some that the their them
    then there they this to too up us was we were what when which who will with you your
    """.split()
)


def _words(text: str) -> "set[str]":
    """The distinct, meaningful words in one entry (for document frequency)."""
    return {w.strip("'") for w in _WORD.findall(text.lower())} - STOPWORDS


def derive(entries: "list[Entry]", now: float, *, max_threads: int = 7, hold_preview: int = 140) -> dict:
    if not entries:
        return {"count": 0, "threads": [], "holding": None, "oldest_age": None, "newest_age": None}

    df: "Counter[str]" = Counter()
    for e in entries:
        df.update(_words(e.text))
    # "Recurring" = said across more than one entry; that's what the block *keeps* saying.
    threads = [[word, n] for word, n in df.most_common() if n >= 2][:max_threads]

    most_kept = max(entries, key=lambda e: e.seconds)
    holding = None
    if most_kept.seconds > 0:
        text = most_kept.text
        if len(text) > hold_preview:
            text = text[: hold_preview - 1].rstrip() + "…"
        holding = {"text": text, "seconds": most_kept.seconds}

    ts_values = [e.ts for e in entries]
    return {
        "count": len(entries),
        "threads": threads,
        "holding": holding,
        "oldest_age": now - min(ts_values),
        "newest_age": now - max(ts_values),
    }
