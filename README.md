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

**Status:** major 01 (the local Exchange — take a story, leave a story) is in. Next:
[major 02, the forgetting engine](prune/majors/02-the-forgetting-engine.md).
