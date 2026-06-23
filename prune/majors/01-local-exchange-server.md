# Build the local Exchange server: take a story, leave a story, in a browser

## Problem

There is no code yet. Stoop's core — an anonymous, asynchronous take-one/leave-one exchange — has to
exist and feel good in a real browser before any hardware question matters. Nothing downstream (the
Murmur, the forgetting engine, the port) can be built or judged until this loop is real.

## Proposed Solution

Stand up one small local server that serves a captive-portal-friendly web app over HTTP on the LAN.
Choose the stack in this item and freeze it (bias: a minimal server + a no-build or light-build front
end so it ports cleanly to a constrained device later). Implement:

- A **storage abstraction** — an `Entry` is short text + timestamp + an opaque local id, with no author
  identity — behind an interface, so the laptop store and the later LittleFS store are swappable.
- `GET /` — the portal: render current entries (the Exchange).
- `POST /entries` — leave an entry (server-side length cap, text-only).
- The **reciprocity nudge** in the UI (took one → leave one), enforced socially, not technically.

Decide and document the canonical setup / run / test commands (the adoption guide's command-surface
step), and record them in the top-level `README.md`.

## Files Affected

- (stack TBD in this item) e.g. `src/server.*`, `src/store/` (interface + laptop impl), `web/index.html`,
  `web/app.*`, `web/style.css`
- `README.md` — canonical run/test commands
- `prune/ROADMAP.md` — mark `01` in progress / shipped

## Acceptance Criteria

- [ ] From a phone on the same network, a visitor can load the portal, read existing entries, and post a
      new one — no account, no app.
- [ ] Entries are text-only and length-capped server-side.
- [ ] Storage sits behind an interface with at least one working (laptop) implementation; no portal code
      talks to a store directly.
- [ ] Canonical setup/run/test commands are documented and stable.
- [ ] No cloud calls, no stored credentials.

## Risks & Rollback

Risk: choosing a stack that's pleasant on a laptop but hostile to the ESP32 port. Mitigation: keep the
front end dependency-light and the store behind an interface; spike the captive-portal assumption
(minor `30`) early. Rollback: greenfield — revert the branch; nothing depends on it yet.
