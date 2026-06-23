# Keeper surface and prompt-as-theme: one codebase, many boxes

## Problem

A Stoop needs a tender — someone to remove the rare bad entry (janitor, not censor) — and the concept's
range ("show us your rock" vs stories vs local tips) depends on the *prompt* being configurable. Without
a keeper surface there's no local control; without theming, every box is a story-box.

## Proposed Solution

- A minimal, **local-only keeper surface** (no cloud, no account) to remove an entry and adjust
  settings, gated by a locally-set secret — no credential stored off-device.
- A **prompt/theme config** that sets the framing question, the SSID name, and light copy/aesthetic, so
  the same code is a story-box, rock-box, or tips-box by config alone.

## Files Affected

- `src/admin.*` — local keeper routes (remove entry, settings)
- `src/config.*` — prompt / theme / SSID config
- `web/` — themed copy + the admin view

## Acceptance Criteria

- [ ] Keeper can remove an entry and change settings locally, gated by a locally-set secret; no
      credential leaves the device.
- [ ] Changing one config turns the box into a different-prompt box (framing, SSID, copy) with no code
      change.
- [ ] With no keeper action, the box still self-tends via the forgetting engine.

## Risks & Rollback

Risk: the admin surface becomes an attack surface on a public node. Mitigation: local-only,
secret-gated, minimal verbs (remove / settings), no destructive bulk operations. Rollback: ship
read-only with decay-only self-tending; theming is independent and can land on its own.
