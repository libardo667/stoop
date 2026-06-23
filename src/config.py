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

# Laptop store location (gitignored). The ESP32 store (major 05) satisfies the
# same Store contract against LittleFS instead of a file.
DATA_FILE = "data/entries.json"

# Static assets for the captive portal.
WEB_DIR = "web"
