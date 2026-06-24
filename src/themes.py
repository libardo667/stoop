"""Themes and skins — the prompt makes the box.

A **theme** is content: the framing question, the copy, the noun, the SSID. A
**skin** is aesthetic: which palette/treatment the portal wears. They're
orthogonal — a rock-box can be paper or phosphor — and both are pure data, so the
same firmware is a story-box, a rock-box, or a glowing tips-terminal by a keeper's
config alone (major 04), with the phosphor look as a built-in skin (minor 31).
"""

from __future__ import annotations

THEMES = {
    "stoop": {
        "title": "the stoop",
        "tab_exchange": "stoop",
        "tab_murmur": "murmur",
        "prompt": "Tell the block a story.",
        "placeholder": "leave a story for the block…",
        "leave_label": "leave it on the stoop",
        "nudge": "Took one? Leave one.",
        "hint_exchange": "This stoop only holds so much. Leave a story and the "
        "least-kept one drifts off — tap keep to hold one here a while longer.",
        "hint_murmur": "The murmur is the weather of the block — what it keeps "
        "saying, what it holds onto.",
        "noun_singular": "story",
        "noun_plural": "stories",
        "footer": "made by humans, for the block · no accounts · forgets on purpose",
        "ssid": "take-a-story-leave-a-story",
    },
    "rocks": {
        "title": "show us your rock",
        "tab_exchange": "rocks",
        "tab_murmur": "murmur",
        "prompt": "Show the block a rock you found.",
        "placeholder": "describe your rock — where, when, why it's great…",
        "leave_label": "leave it on the ledge",
        "nudge": "Saw a rock? Show one.",
        "hint_exchange": "Only so many rocks fit on the ledge. A new one nudges the "
        "least-kept rock off — tap keep to hold a favorite.",
        "hint_murmur": "The murmur is the weather of the ledge — what the block "
        "keeps finding, what it holds onto.",
        "noun_singular": "rock",
        "noun_plural": "rocks",
        "footer": "made by humans, for the block · no accounts · rocks rotate",
        "ssid": "show-us-your-rock",
    },
    "tips": {
        "title": "tips for the block",
        "tab_exchange": "tips",
        "tab_murmur": "murmur",
        "prompt": "Leave the block a local tip.",
        "placeholder": "a little neighborhood wisdom…",
        "leave_label": "leave a tip",
        "nudge": "Got a tip? Leave one.",
        "hint_exchange": "The board only holds so many. A new tip pushes the "
        "least-kept one off — tap keep to pin a good one.",
        "hint_murmur": "The murmur is the weather of the board — what the block "
        "keeps passing along, what it holds onto.",
        "noun_singular": "tip",
        "noun_plural": "tips",
        "footer": "made by humans, for the block · no accounts · tips fade",
        "ssid": "tips-for-the-block",
    },
}

SKINS = {"paper", "phosphor"}

DEFAULT_THEME = "stoop"
DEFAULT_SKIN = "paper"


def theme_names() -> "list[str]":
    return sorted(THEMES)


def skin_names() -> "list[str]":
    return sorted(SKINS)


def resolve(theme: str, skin: str, prompt: "str | None" = None) -> dict:
    """The client-facing bundle: a content theme, the chosen skin, and an optional
    keeper prompt override. Unknown names fall back to the defaults."""
    bundle = dict(THEMES.get(theme, THEMES[DEFAULT_THEME]))
    bundle["skin"] = skin if skin in SKINS else DEFAULT_SKIN
    if prompt:
        bundle["prompt"] = prompt
    return bundle
