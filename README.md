# Stoop

A neighborhood gift-exchange you hang on a pole: an open Wi-Fi dead-drop where a passerby takes a story
and leaves a story — and the box slowly becomes a portrait of the block. Offline, no cloud, no accounts.
The digital cousin of the Little Free Library, the puzzle exchange, and the sidewalk notice board.

Software-first (runs on a laptop now), bound for an ESP32 later.

- **What it is and isn't:** [`prune/VISION.md`](prune/VISION.md)
- **What's being built, in order:** [`prune/ROADMAP.md`](prune/ROADMAP.md)
- **How work is tracked:** [`prune/`](prune/) — an instance of the [prune](https://github.com/libardo667/prune) work-item harness.

## Run it

No dependencies, no build step — just Python 3.8+ (standard library only).

```bash
# Run the box (serves on http://<this-device-ip>:8080)
python3 -m src.server

# Test
python3 -m unittest discover -t . -s tests
```

Open `http://localhost:8080` on the same machine, or `http://<laptop-LAN-ip>:8080`
from a phone on the same Wi-Fi — the closest laptop-era stand-in for joining the
box's own network. Contents persist to `data/entries.json` (gitignored).

Reaching it from a phone (and the firewall / VPN / WSL2 gotchas, across OSs):
[`docs/RUNNING.md`](docs/RUNNING.md).

## "Not secure"?

The browser says "Not secure" because a Stoop serves plain **HTTP — on purpose**. It's an open,
anonymous, no-accounts community board with nothing secret on the wire; HTTPS would break the
captive-portal flow and burden the device for no real gain. What "secure" actually means here, and which
seams matter, is written down: [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md) and
[decision 0001](docs/decisions/0001-serve-http-not-https.md).

## License & spirit

[MIT](LICENSE) — take it, fork it, hang your own. If you build a Stoop, theme it, or improve the
firmware, that's the whole idea. Made in Portland; meant to spread.

**Status: software v1 complete** (majors 01–04, minors 31–32) — the Exchange (take a story, leave a
story), the forgetting engine (the box stays small and full, composting the least-kept entry; tap
**keep** to hold one), the Murmur (a second tab: the weather of the block), the keeper surface + theming
(one codebase becomes a story-box, rock-box, or glowing phosphor tips-terminal; a local secret-gated
[`/admin`](web/admin.html) console prunes and re-themes), and the full guard layer (length cap, body
ceiling, connection timeout, per-client throttle). Every seam in the
[threat model](docs/THREAT_MODEL.md) is closed. The only remaining major — and the natural pause for a
hardware build — is [major 05, the ESP32 embodiment](prune/majors/05-esp32-embodiment.md).

### Make it your own (keeper)

Set a secret, run, and visit `/admin`:

```bash
STOOP_KEEPER_KEY="your-secret" python3 -m src.server   # then open /admin
```

Pick a **theme** (story / rocks / tips) and a **skin** (paper / phosphor), or set a custom prompt. With
no key set, the keeper surface is disabled — an un-configured box has no admin, by design.
