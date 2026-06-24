# The Murmur: an ambient portrait of what the block is saying

> **Status: Shipped (2026-06-23).** `src/murmur.py` (pure derivation), `GET /murmur`, and a second
> "murmur" tab in the portal. Reads as weather: what the block *keeps* saying (document frequency),
> what it's *holding onto* (most-kept entry), and how long things have rested here. No deps, no AI —
> cheap enough for the device. 25 tests green.

## Problem

The Exchange shows individual entries; it doesn't show the *block*. The payoff a wooden box can't
deliver — "what's this corner been talking about lately" — needs a second, ambient face. Without it,
Stoop is a nicer guestbook, not a mirror of the street.

## Proposed Solution

Add a Murmur view computed from the live (post-decay) entries: a slow-moving, weather-like portrait
rather than a feed. Start simple and local-cheap (it must run on the ESP32): recurring words/themes, the
rhythm of activity, recent texture — composed so it reads as "about this place," not as analytics. No
external services, no AI; pure local computation over the current entry set. Surface it as a second
tab/route in the portal.

## Files Affected

- `src/murmur.*` — derivation over current entries (read-time, cheap)
- `web/` — the Murmur route/view
- tests for the derivation

## Acceptance Criteria

- [x] A second view renders a portrait derived only from current entries, computed locally.
- [x] It updates as entries come and go (and as decay turns the set over).
- [x] It reads as *about the neighborhood*, not as a dashboard, to a lay visitor.
- [x] Cheap enough to run within the ESP32 budget (no heavy deps).

## Risks & Rollback

Risk: a word-frequency portrait feels like a cliché word cloud. Mitigation: design the presentation
deliberately (the phosphor pass, minor `31`, helps); iterate on feel before adding cleverness. Rollback:
hide the route; the Exchange stands alone.
