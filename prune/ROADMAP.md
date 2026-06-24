# Roadmap

## Current State

- Product status: **Software v1 complete.** Majors `01`–`04` plus minors `31`–`32` shipped — the
  Exchange, the forgetting engine, the Murmur, the keeper surface + theming, and the full guard layer
  (length cap, body ceiling, timeout, per-client throttle). The box is bounded, has its two faces, wears
  any of several themes/skins by a keeper's config, self-tends, and resists a flood. Every seam in the
  threat model is closed. **The only remaining major is `05` (ESP32) — the natural pause point for the
  hackerspace, since it wants hardware in hand.**
- Architecture status: Stack locked — Python stdlib `http.server` + one hand-written page, zero
  dependencies, no build step. Storage sits behind a `Store` interface (`src/store/`); the forgetting
  *policy* is pure in `src/decay.py`, orchestrated by `src/box.py` — so the ESP32 LittleFS store (05)
  slots in behind the same shape by swapping the capacity predicate to a byte budget.
- Top risks:
  - Abuse on an open, anonymous, public node with no cloud and no moderator-on-call. This is *the*
    design problem, not a side issue.
  - The laptop→ESP32 port: captive-portal quirks across phone OSes and the LittleFS byte budget could
    invalidate laptop-era assumptions if the hardware unknowns are deferred too long.

## Guardrails

1. Constraints are the product. No feature may quietly assume the cloud, accounts, identity, or
   unbounded storage. If it needs those, it belongs to a different project.
2. Abuse-resistance is a design property (capacity, brevity, text-only, decay, keeper pruning), never a
   content-moderation pipeline.
3. Keep storage and behavior portable from day one so the ESP32 port is a swap, not a rewrite. Prove the
   hard hardware assumptions early enough to matter.
4. Text-first and short. Brevity starves abuse and breeds charm.

## Major Queue

1. ~~`01` — Local Exchange server: the take-a-story / leave-a-story core, served to a browser.~~ **Shipped.**
2. ~~`02` — The forgetting engine: capacity + age + reader-signal decay (the memory logic, in proportion).~~ **Shipped.**
3. ~~`03` — The Murmur view: the ambient portrait of the block.~~ **Shipped.**
4. ~~`04` — Keeper surface + prompt/theming: pruning, and the prompt-makes-the-box system.~~ **Shipped** (incl. minor `31`, phosphor).
5. `05` — ESP32 embodiment: open AP, captive portal, LittleFS persistence, OTA. **← next (needs hardware)**

## Minor Queue

1. `30` — SSID-as-signage + captive-portal auto-pop.
2. ~~`31` — Phosphor pass: the retro-terminal aesthetic for the portal.~~ **Shipped** (as a skin, with major `04`).
3. ~~`32` — Brevity & rate guards: length caps, body ceiling, timeout, per-client throttle.~~ **Shipped.**

## Recommended Execution Order

1. `01` — the loop has to exist and feel good in a browser before anything else can be judged.
2. `02` — forgetting is what makes it a Stoop and not a guestbook; build it early, it shapes storage.
3. `03` — the Murmur is the payoff face; it needs `01`+`02`'s data.
4. `04` — theming + keeper pruning once there's something to tend.
5. `05` — port last, but spike the captive-portal + LittleFS unknowns during `01` (via minor `30`) so
   the port isn't a surprise.

## Notes

- Hardware is not on the critical path until `05`. A bare ESP32-C3 dev board (~$5–8, ordered online) is
  the sane target; the literal flashable smart *bulb* from the inspiring article is an aesthetic/stealth
  choice, sourced separately and later.
- Minors `30`–`32` can ride alongside the majors; `31` (phosphor) is the low-stakes joy reward and pairs
  with the retro-terminal aesthetic from the original brainstorm.
