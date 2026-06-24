"""The keeper gate. Local-only, secret-gated, no credential stored off-device.

The secret is read from the STOOP_KEEPER_KEY environment variable — never the
repo, never disk. If it's unset, the keeper surface is disabled (fail closed):
an un-configured box has no admin, rather than a default-password admin. The key
travels in the `X-Keeper-Key` header over the local link; see docs/THREAT_MODEL.md
for why cleartext-on-a-local-link is acceptable for this device.
"""

from __future__ import annotations

import hmac
import os

ENV_KEY = "STOOP_KEEPER_KEY"


def keeper_key() -> "str | None":
    return os.environ.get(ENV_KEY) or None


def authorized(provided: "str | None") -> bool:
    key = keeper_key()
    if not key or not provided:
        return False
    return hmac.compare_digest(provided, key)
