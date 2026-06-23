# Brevity and rate guards

## Problem

On an open, anonymous node, the cheapest abuse is volume and length. Brevity and simple throttles starve
most of it before any decay or keeper logic is needed.

## Proposed Solution

A server-side entry length cap (text-only) and simple per-connection / time-window throttles on `POST` —
no identity required. Tunable, with conservative defaults.

## Files Affected

- `src/server.*` (validation + throttle)
- tests

## Acceptance Criteria

- [ ] Entries exceeding the length cap, or non-text payloads, are rejected server-side.
- [ ] Rapid repeated posts from one connection are throttled.
- [ ] Limits are config with conservative defaults.
