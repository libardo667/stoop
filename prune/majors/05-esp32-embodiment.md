# Port Stoop onto an ESP32: open AP, captive portal, LittleFS, OTA

## Problem

Stoop is meant to hang on a pole, not live on a laptop. The embodiment is an ESP32-class device
broadcasting its own open Wi-Fi AP, serving the portal via captive-portal redirect, persisting entries
to LittleFS within a tight byte budget, and updatable over OTA — no cloud, no stored credentials (the
ethos of the article that started this).

## Proposed Solution

Implement the firmware target behind the same behavior contract built on the laptop:

- Open AP + DNS catch-all so any request triggers the captive portal.
- A LittleFS-backed implementation of the store interface from major `01`, inside the capacity ceiling
  from major `02`.
- An OTA update path.

Spike the captive-portal-across-phone-OSes and LittleFS-budget unknowns during major `01` (via minor
`30`) so this is a swap, not a discovery.

## Files Affected

- `firmware/` — ESP32 sketch/build (AP, captive DNS, HTTP, OTA)
- `firmware/store_littlefs.*` — the store interface on LittleFS
- [`docs/HARDWARE.md`](../../docs/HARDWARE.md) — **draft plan written** (the role, the carries-over-vs-rewritten
  split, MicroPython-vs-C, captive portal, keeper-on-open-AP, and open questions for the hackerspace).
  Board choice / flashing / capacity budget get filled in as the build happens.

## Acceptance Criteria

- [ ] Device broadcasts an open AP whose name is the configured SSID; connecting auto-pops the portal on
      common phones.
- [ ] Entries persist across power cycles on LittleFS within the byte ceiling.
- [ ] Exchange, Murmur, decay, and keeper surface behave as on the laptop.
- [ ] OTA update works; no cloud dependency; no credentials stored on device.

## Risks & Rollback

Risk: captive-portal behavior varies or is blocked across phone OSes; the LittleFS budget proves too
tight. Mitigation: spike both early (minor `30`); the SSID name alone is a working fallback invitation.
Risk: bricking during flashing/OTA. Mitigation: document a recovery flash; keep OTA images small.
Rollback: the laptop build remains the reference deployment.
