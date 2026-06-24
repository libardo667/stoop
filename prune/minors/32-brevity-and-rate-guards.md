# Brevity and rate guards

> **Status: Shipped (2026-06-24).** Length cap (01) + body ceiling/timeout (hardening) +
> `src/ratelimit.py`: a per-client sliding-window throttle on public posts, keyed on the transient
> connection address in memory only (never logged/persisted). Keeper actions are exempt. This closes the
> last open software seam — v1's content-firehose guards are complete.

## Problem

On an open, anonymous node, the cheapest abuse is volume and length. Brevity and simple throttles starve
most of it before any decay or keeper logic is needed.

## Proposed Solution

A server-side entry length cap (text-only), a hard request-body ceiling enforced *before* the body is
read into memory, a connection timeout, and simple per-connection / time-window throttles on `POST` — no
identity required. Tunable, with conservative defaults.

## Files Affected

- `src/server.*` (validation, body ceiling, timeout, throttle)
- `src/config.py` (`ENTRY_MAX_LEN`, `MAX_BODY_BYTES`)
- tests

## Acceptance Criteria

- [x] Entries exceeding the length cap, or non-text payloads, are rejected server-side. *(landed in 01)*
- [x] Oversized request bodies are rejected (`413`) before allocation; a stalled client can't pin a
      worker thread (handler `timeout`). *(landed during street-readiness hardening, 2026-06-23)*
- [x] Rapid repeated posts from one connection are throttled (`429`). *(2026-06-24)*
- [x] Limits are config with conservative defaults (`RATE_MAX_POSTS` / `RATE_WINDOW_SECONDS`,
      `MAX_BODY_BYTES`, `ENTRY_MAX_LEN`).

## Notes

The body ceiling + timeout shipped early because the first on-device thinking ("close the seam before
the street") surfaced resource exhaustion as the genuinely-open risk. See
[`docs/THREAT_MODEL.md`](../../docs/THREAT_MODEL.md). The throttle (`src/ratelimit.py`) is keyed on the
transient connection IP held in memory only — no identity stored, nothing logged or persisted. Set
`RATE_MAX_POSTS <= 0` to disable for a fully open box.
