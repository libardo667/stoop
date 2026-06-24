# How a Stoop ought to run on hardware — working draft

> **Status: draft, pre-build.** This is the plan for [major 05](../prune/majors/05-esp32-embodiment.md),
> not built yet. It's written to bring to people (e.g. the CTRL-H exploit workshop) and say *"here's the
> shape — poke it."* The **open questions at the bottom are the real ask.**
>
> **Provenance:** drafted by the AI collaborator from the keeper's questions, reviewed by the keeper. The
> diagnosis and wording here are the model's; the direction and the veto are Levi's. (Seams showing, on
> purpose.)

## The one thing to get straight first

**The Python in this repo does not run on the board.** CPython doesn't run on a microcontroller. So the
hardware build is *not* "copy the script onto the ESP32 and run it" — it's a **reimplementation behind
the same behavior contract**, in a language the chip can run. The repo stays the **executable
specification**: the thing that defines exactly what "correct" means, so the port is a translation job
rather than a redesign. That's why the logic is kept pure and storage sits behind an interface.

## The role the board plays

An ESP32 Stoop is a small, always-on device (USB or battery powered) that does four things, with **no
internet uplink, no cloud, and no credentials stored off-device**:

1. **Becomes its own Wi-Fi access point** (SoftAP mode), broadcasting the SSID — which *is* the signage
   (`take-a-story-leave-a-story`). Its built-in radio; nobody's home network involved.
2. **Runs a catch-all DNS server** — the captive-portal trick (see below).
3. **Runs a tiny HTTP server** — the same routes and behavior as today: the Exchange (`/entries`,
   `/second`), the Murmur (`/murmur`), the keeper surface (`/admin/*`), the portal page.
4. **Persists entries to flash** (LittleFS) instead of `data/entries.json` — the same `Store` contract,
   a different backend, inside a byte budget.

## What carries over vs. what gets rewritten

| Carries over (the *spec / shape*) | Gets rewritten (the *plumbing*) |
|---|---|
| The behavior contract (routes, status codes, the gate rules) | The HTTP server itself (no `http.server`) |
| The data model: an `Entry` is text + ts + seconds, no author | The storage backend → LittleFS |
| The pure logic: `decay` scoring, `murmur` derivation, `themes` | The Wi-Fi AP + catch-all DNS (captive portal) |
| The forgetting policy (capacity → evict least-kept, archive) | The auth primitive (`hmac` isn't standard on-device) |
| The guard rules (length cap, body ceiling, rate limit) | The concurrency model (likely single-threaded) |

The split is cheap **by design**: the store is already behind an interface, the logic is already pure,
and capacity is **one swappable predicate** — on the laptop it's an entry count (`MAX_ENTRIES`); on the
board it becomes "bytes used on the LittleFS partition." Same scoring, same eviction, same archive
intent.

## Two ways to build it (decision pending — workshop input wanted)

- **MicroPython** — Python *on* the chip. Closest to the current code in spirit, but **not** copy-paste:
  no `http.server`, no `dataclasses`, no `hmac` (hand-roll a constant-time compare), single-threaded, and
  tight RAM on an ESP32-**C3** especially. You'd reimplement the serve loop over raw sockets; the *shape*
  of the pure modules ports across.
- **C++ (Arduino-ESP32 / ESP-IDF)** — the lineage the banned-books-lightbulb used (it was built on
  Tasmota, which is C). A bigger language jump, more code, but the **most battle-tested captive-portal
  support** (`WiFi.softAP` + `DNSServer` + a web server + `LittleFS`). Here the Python is purely the
  reference you port against.

Either path keeps this repo as the spec. Which to pick is a real open question (below).

## The captive portal, concretely

This is what makes "join the wifi and the page just appears":

1. The board's DNS server answers **every** domain lookup with its own IP (a DNS catch-all — legitimate
   here: it's *your* network, no internet behind it).
2. A phone joining any open Wi-Fi automatically hits a known check URL (`captive.apple.com`,
   `connectivitycheck.gstatic.com`, …) to detect a login wall.
3. Because DNS resolves everything to the board, that check lands on the board's HTTP server, which
   redirects it to the portal → the phone pops its "sign in to network" mini-browser showing **this
   Stoop, and only this Stoop.**

This is [minor 30](../prune/minors/30-ssid-as-signage.md) (SSID-as-signage + auto-pop). It's
**hardware-only** — there's no faithful way to test the auto-pop on a laptop, which is why it's deferred
to the device.

## Persistence and the byte budget

Entries are tiny (≤ 280 chars), so the *content* fits easily — the banned-books project squeezed ~2MB
of books into LittleFS; a Stoop holds short text. The byte budget mostly governs **how many entries**
the forgetting engine keeps before it composts the least-kept one (the capacity predicate, swapped from
count to bytes). Open question: **flash wear** — every leave/evict is a small write, and flash has finite
write cycles; LittleFS does wear-leveling, but it's worth a sanity check at this write rate.

## The keeper, on an open AP

The keeper is **just another client on the box's Wi-Fi who knows the key.** They join the open AP like
any passerby, open `http://<box>/admin`, enter the key, and prune. The key is **provisioned into the
firmware's config** (the hardware analog of today's `STOOP_KEEPER_KEY` env var), so admin is live from
boot. The `/admin` page is reachable by anyone; only the *actions* are gated — same as today.

**Honest tradeoff (a good one to hand the security folks):** on an *open* AP, when the keeper submits the
key it crosses the air in **cleartext** — sniffable by anyone listening on that radio while the keeper
acts. Worst case, a sniffer could prune entries or reskin the box: annoying, bounded, not catastrophic,
which is why the [threat model](THREAT_MODEL.md) accepts it for a low-stakes community object (and why
the box stores nothing private in the first place). If you wanted to close it, the moves are roughly: a
WPA-protected "keeper" SSID, admin only over USB/serial, or TLS (which fights the captive-portal flow —
see [decision 0001](decisions/0001-serve-http-not-https.md)).

## Power, siting, resilience (later, but worth noting)

- **Power:** USB battery pack, a small LiPo, or harvested/solar for a truly unattended box. Runtime vs.
  size is a real constraint for "hang it on a pole."
- **Resilience:** entries and settings survive power loss (they're on flash). A reboot brings the box
  back as itself.
- **Updates:** OTA is in the major 05 acceptance criteria — no recovering the box from a pole to reflash.
- **Disguise:** the literal smart-*bulb* enclosure (the article's stealth move) is an aesthetic choice
  for later, sourced separately — a bare ESP32-C3 dev board is the sane starting target.

## Open questions for the workshop — the actual "halp"

1. **MicroPython vs. C/ESP-IDF** for a captive-portal + LittleFS box — what would *you* reach for, and
   why?
2. **Keeper auth on an open AP** — how would you authenticate the keeper without killing the
   zero-friction captive-portal UX for everyone else?
3. **Captive-portal auto-pop in 2026** — known gotchas across current iOS / Android? (HSTS, the way each
   OS probes, walled-garden detection changing.)
4. **Local salvage** — best place around PDX to harvest or source an ESP32-C3 in person? (Prefer
   salvaged/local over a big online order.)
5. **Flash wear** — at a few small writes per visitor, is LittleFS wear a real concern for a box meant to
   live outside for months, or a non-issue at this scale?
6. **Power** for an unattended outdoor box — just a big USB battery, or is solar + LiPo worth it?

## See also

- [major 05 — ESP32 embodiment](../prune/majors/05-esp32-embodiment.md) (the work item this plans)
- [minor 30 — SSID-as-signage + captive portal](../prune/minors/30-ssid-as-signage.md)
- [THREAT_MODEL.md](THREAT_MODEL.md) · [decision 0001 — HTTP not HTTPS](decisions/0001-serve-http-not-https.md)
