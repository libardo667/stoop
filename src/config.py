"""Small, frozen knobs for the laptop build.

Most of this becomes keeper-configurable per box in major 04 (prompt/theming).
For now they are plain constants so major 01 stays minimal.
"""

# Where the box listens. 0.0.0.0 so a phone on the same network can reach it
# via the laptop's LAN IP — the closest laptop-era analog to "join the AP".
HOST = "0.0.0.0"
PORT = 8080

# The framing question. The prompt makes the box (major 04 will let a keeper
# swap this to turn a story-box into a rock-box or a tips-box).
PROMPT = "Tell the block a story."

# The network name is the signage (minor 30 / major 05). Carried here now so the
# whole project already knows its own invitation.
SSID = "take-a-story-leave-a-story"

# Brevity breeds charm and starves abuse. Major 32 tightens the guards; this is
# the floor.
ENTRY_MAX_LEN = 280

# Hard ceiling on a request body, enforced before reading it into memory. A box
# on a pole must not let a stranger OOM it with a giant POST. Generous headroom
# over a 280-char entry's JSON envelope (even with multibyte UTF-8), nothing more.
MAX_BODY_BYTES = 4096

# --- the forgetting engine (major 02) ---
# The box is small and always full, so leaving something pushes the least-loved
# thing out. (Entry-count ceiling here; the ESP32 store swaps in a byte budget.)
MAX_ENTRIES = 50

# Decay weights — the proportion is meant to be tuned (see src/decay.py).
DECAY_AGE_HORIZON_SECONDS = 14 * 24 * 60 * 60  # recency fades to 0 over ~2 weeks
DECAY_PRESSURE_SQUEEZE = 0.6                    # a full box forgets ~2.5x faster
DECAY_W_RECENCY = 1.0                           # freshness weight
DECAY_W_SECONDS = 0.5                           # each "keep" ~ half a fresh entry

# Evicted entries compost here: append-only, local, gitignored under prune/history/.
ARCHIVE_FILE = "prune/history/evicted-entries.jsonl"

# Laptop store location (gitignored). The ESP32 store (major 05) satisfies the
# same Store contract against LittleFS instead of a file.
DATA_FILE = "data/entries.json"

# Static assets for the captive portal.
WEB_DIR = "web"
