# Decision Record

## Metadata

- Date: 2026-06-23
- Status: accepted
- Owner: Levi Banks
- Related Items: minor `32` (guards), major `04` (keeper admin), major `05` (ESP32 embodiment)

## Decision

A Stoop serves plain **HTTP, not HTTPS**. The browser's "Not secure" label is the *expected and correct*
state for this class of device, and is addressed by honest framing (the captive portal + page copy), not
by certificates.

## Context

The first phone test of the laptop build surfaced the browser's grey "Not secure" warning, and the
reasonable question: close that seam before putting a box on the street. A written position is needed
because (a) it *looks* like an oversight, and (b) other people are meant to run these and will ask the
same thing. The reflex — "insecure label, add HTTPS" — is wrong for an open, anonymous, no-accounts
community device, and acting on it would make the box worse.

## Options Considered

1. **Plain HTTP.** *(chosen)*
2. **Self-signed HTTPS.** A certificate the box generates itself.
3. **Real CA HTTPS (e.g. Let's Encrypt).** A certificate from a public authority.

## Tradeoffs

- Benefits (HTTP):
  - Keeps the captive-portal auto-pop working — phones detect open networks and open the portal **over
    HTTP**; that is the mechanism the whole ESP32 deployment (major `05`) depends on.
  - Preserves the ESP32 budget — no TLS handshake CPU/memory cost on a 4MB device.
  - Honest: a grey "Not secure" whisper, not a red full-page interstitial scream.
- Costs (HTTP):
  - The browser shows "Not secure." Accepted — there is no confidential payload for TLS to protect: a
    Stoop has no accounts, no logins, no personal data; its entries are *public by design*.
- Why not self-signed HTTPS:
  - Replaces the mild grey label with a full-page `NET::ERR_CERT_AUTHORITY_INVALID` interstitial users
    must actively click through — strictly scarier, for a box meant to feel inviting.
  - Still breaks captive-portal detection and still costs the device crypto overhead.
- Why not real CA HTTPS:
  - Impossible for the target: a box on a pole has no public domain name and no inbound internet path
    for a CA to validate. There is nothing to issue a cert *for*.

## Outcome and Consequences

- **Architecture:** the captive portal stays functional; no TLS stack on the device; the laptop build
  and the ESP32 build share the same plain-HTTP shape.
- **Developer workflow:** none added — run `python3 -m src.server`, ignore the grey label by design.
- **Runtime behavior:** entries travel in cleartext over a local link. This is acceptable because the
  asset is *public community text*, not secrets. See [`../THREAT_MODEL.md`](../THREAT_MODEL.md) for what
  "secure" actually means here and which seams matter.
- **Future flexibility:** if a *hosted hub* with a real public domain ever exists (an internet-facing
  aggregator, not a box on a pole), TLS **there** is a separate decision for a different component — it
  does not change the on-device posture.

## Rollback Trigger

Revisit if a Stoop ever transmits something genuinely confidential over the wire — e.g. keeper
credentials authenticated from a remote network. The keeper admin surface (major `04`) is deliberately
**local-only and secret-gated** specifically so this trigger stays un-pulled.
