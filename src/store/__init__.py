"""Storage contract + the laptop-era implementation.

Nothing outside this package should know *how* entries are stored. The portal
talks to the `Store` interface only, so the ESP32/LittleFS store (major 05) and
the forgetting engine (major 02) slot in behind the same shape.
"""

from .base import Entry, Store
from .jsonfile import JsonFileStore

__all__ = ["Entry", "Store", "JsonFileStore"]
