# SSID-as-signage and captive-portal auto-pop

## Problem

Discovery has to be zero-instruction: the only "sign" is the Wi-Fi network name, and the portal should
appear on its own when a phone connects. This assumption underpins majors `01` and `05` and should be
validated early.

## Proposed Solution

Make the SSID configurable and treat it as primary signage (e.g. `take-a-story-leave-a-story`).
Implement/verify captive-portal auto-pop: on the laptop dev build via a DNS/redirect shim where
feasible, and as the real mechanism on the ESP32. Spike behavior across iOS and Android to de-risk
major `05`, and record findings.

## Files Affected

- `src/config.*` (SSID) and captive-redirect handling
- `docs/captive-portal-notes.md` (findings across phone OSes)

## Acceptance Criteria

- [ ] SSID is configurable and surfaced as the invitation.
- [ ] Connecting auto-pops the portal on at least iOS and Android (with documented behavior/limits).
