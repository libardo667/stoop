# The forgetting engine: capacity, age, and reader signal decide what stays

> **Status: Shipped (2026-06-23).** `src/decay.py` (pure scoring), `src/box.py` (orchestration),
> `src/archive.py` (compost). Capacity is an entry count (`MAX_ENTRIES`) on the laptop; the LittleFS
> store (major 05) swaps that predicate for a byte budget while reusing the same scoring/eviction.
> `/second` endpoint + a "keep" affordance in the portal. 19 tests green.

## Problem

A guestbook that only grows is not a Stoop. The magic of the physical exchanges — and the thing that
bounds abuse without a moderator — is that the box is small and always full, so leaving something pushes
something else out. Without deliberate forgetting, storage grows unbounded (fatal on the ESP32) and the
contents stop being a snapshot of the *recent* block. The keeper's call: a combination of the memory
ideas, in proportion — not any one alone.

## Proposed Solution

Add an eviction/decay layer over the store from major `01`, combining three forces with tunable weights:

- **Scarcity / capacity** — a hard byte/entry ceiling (the ESP32 budget made a virtue). At capacity,
  leaving evicts.
- **Age / compost** — entries fade with time unless refreshed.
- **Reader signal ("seconding")** — a lightweight, anonymous "this one stays" affordance that buys an
  entry more life. The only social signal, deliberately minimal, and it can only *extend* life, never
  delete.

Eviction picks the lowest-scoring entry (oldest, least-seconded), reusing the spirit of the kit's
`pick.py` staleness weighting. Weights are config so the proportion is tunable. Evicted entries move to
the local `history/` archive — never silently destroyed.

## Files Affected

- `src/store/` — capacity + scoring + eviction
- `src/decay.*` — the scoring/compost policy and weight config
- `prune/history/` — convention for archiving evicted entries locally
- tests for eviction ordering and capacity invariants

## Acceptance Criteria

- [x] Total storage never exceeds a configured ceiling; posting at capacity evicts the lowest-scoring
      entry.
- [x] Entry score combines age, capacity pressure, and seconds, with tunable weights.
- [x] An unattended instance stays full, fresh, and bounded with no manual deletion.
- [x] Evicted entries are archived locally, not destroyed.
- [x] Decay behavior is covered by deterministic tests.

## Risks & Rollback

Risk: tuning that feels arbitrary or churns good entries. Mitigation: weights are config, defaults
conservative, deterministic tests pin behavior. Risk: "seconding" becomes a brigading vector.
Mitigation: it can only extend life, with a capped effect. Rollback: disable the decay layer
(capacity-only) without touching the store interface.
