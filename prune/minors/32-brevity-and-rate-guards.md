# Brevity and rate guards

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
- [ ] Rapid repeated posts from one connection are throttled.
- [ ] Limits are config with conservative defaults.

## Notes

The body ceiling + timeout shipped early because the first on-device thinking ("close the seam before
the street") surfaced resource exhaustion as the genuinely-open risk. See
[`docs/THREAT_MODEL.md`](../../docs/THREAT_MODEL.md). The remaining work is the rate/throttle layer.
