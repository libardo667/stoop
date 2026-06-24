# Threat model — what "secure" means for a Stoop

A Stoop is an open, anonymous community bulletin board that anyone nearby can walk up to. Its security
is not about secrecy — it has no secrets. It is about three things: **not harming the visitor**, **not
being usable as a weapon**, and **not falling over when a stranger pokes it**. This doc names the assets,
the non-assets, and the actual seams — so "is it secure?" has a concrete answer instead of a reflex.

## What we are (and aren't) protecting

- **Asset:** the recent, public, anonymous text the block has left. It is *meant to be read by anyone*.
- **Non-asset — confidentiality of the channel.** There is no login, no account, no private payload.
  This is why the box serves plain HTTP and the "Not secure" label is expected — see
  [decision 0001](decisions/0001-serve-http-not-https.md). The channel is **not** the threat.
- **Non-asset — identity.** A Stoop deliberately stores *no* author: an entry is text + timestamp + an
  opaque id, nothing that says who. Keeping it that way is itself a security property (nothing to leak,
  nothing to subpoena, nothing to dox).

## The seams

| Seam | Threat | Status |
|---|---|---|
| **Stored XSS** | A visitor leaves `<script>`/markup as an "entry" that runs in the next reader's browser. | ✅ **Closed.** The portal renders every entry with `textContent`, never `innerHTML` (`web/app.js`). Markup is shown as literal text; it cannot execute. |
| **Identity leakage** | The box records who left what (IP, MAC, author). | ✅ **Closed by design.** Entries carry no author; server logs are method+path only, never client identity. *Keep it this way — do not add request-identifying logs.* |
| **Path traversal** | A crafted URL reads arbitrary files off the device. | ✅ **Closed.** Static files are served from a hardcoded path→file whitelist (`STATIC` in `src/server.py`), never a filesystem join on user input. |
| **Resource exhaustion (oversized body)** | A giant POST is read into memory and OOMs a tiny device. | ✅ **Closed.** Bodies over `MAX_BODY_BYTES` are rejected `413` *before* allocation; a stalled client is dropped via the handler `timeout` (`src/server.py`). |
| **Flooding / spam** | A firehose of entries drowns the block or fills the box. | ✅ **Closed.** The box stays bounded and forgets (major `02`), and public posts are rate-limited per client (`429`) by an in-memory sliding window keyed on the transient connection address — no identity stored (minor `32`, `src/ratelimit.py`). |
| **Keeper-admin exposure** | The prune/settings surface becomes an attack surface on a public node. | ✅ **Closed (major 04).** Admin verbs (`/admin/*`) are **secret-gated and fail closed**: the key is read from the `STOOP_KEEPER_KEY` env var (never the repo, never disk), and an un-configured box has *no* admin rather than a default-password one. The key travels in a header over the local link in cleartext — acceptable here for the same reason entries are (local, no remote attacker in the model); it is never stored off-device. |
| **Malicious/abusive content** | Someone leaves something hateful or harmful (not code — words). | ⚠️ **By design, social + bounded.** No content pipeline (a non-goal). Bounded by brevity, text-only, decay (it ages out), and the keeper as janitor. This is the same way a wooden free library is "moderated." |

## Posture summary

As of v1, every seam in the table above is **closed**: untrusted content can't execute, can't read the
filesystem, can't OOM the device, can't be traced to a person; the keeper surface fails closed; and the
content firehose is bounded both ways — the box forgets (`02`) and throttles (`32`). The remaining
"⚠️" rows are *by-design social bounds* (abusive words, handled like a wooden free library — short,
anonymous, ages out, prunable), not unguarded holes. When someone asks "but it's not HTTPS?", the answer
is [decision 0001](decisions/0001-serve-http-not-https.md): for this device, the padlock is not the seam.

## A note for anyone hanging one

This is a thing you put in public, under your name in spirit if not in data. It will, eventually, catch
something ugly — that's true of every free library and notice board too. The defenses here are designed
to keep that *bounded and transient* (short, anonymous, ages out, prunable) rather than to promise it
can't happen. Hang it somewhere you'd be glad to tend.
