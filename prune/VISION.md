# Vision

## One-Sentence Pitch

A neighborhood gift-exchange you hang on a pole: an open Wi-Fi dead-drop where a passerby takes a
story and leaves a story, and the box slowly becomes a portrait of the block.

## What This Is

Stoop is a small, offline-first, no-cloud, no-accounts node that serves a captive-portal web app over
its own open Wi-Fi network. It is the digital cousin of the Little Free Library, the puzzle exchange,
the neighborhood notice board — running the same quiet operating system those objects do (anonymous,
asynchronous, local, low-stakes), plus the one thing a wooden box can't do: it remembers, and it can
reflect what it has heard back to the street.

Two faces:

- **The Exchange** — *take a story, leave a story.* Reciprocity is the soul of the object; the
  interface nudges it without enforcing it.
- **The Murmur** — *what the block's talking about.* An ambient, slow-moving portrait that emerges from
  the exchanges. Weather, not a feed.

The contents are deliberately finite. A small box that's always full means leaving something pushes
something else out: the library forgets. Forgetting is a feature, not a failure — it's what keeps the
box an honest snapshot of the *recent* street and what bounds abuse without a moderator.

It is keeper-themeable: the same firmware is a story-box on one pole, a "show us your rock" box on
another, a local-tips box on a third. The prompt makes the box.

Software-first: it runs as a local server on a laptop today, ported to an ESP32 (open AP + captive
portal + LittleFS) once the behavior feels right.

## Primary User

- **The passerby** — someone on a Portland sidewalk with a phone and thirty idle seconds. No app, no
  account, no signup. They join an open network whose *name is the invitation*, read what's here, and
  maybe leave something.
- **The keeper** — whoever hangs and tends a Stoop. Sets the prompt/theme, quietly prunes the rare bad
  entry (janitor, not censor), and otherwise lets the block fill it.

## Core Interaction Model

1. A phone sees an open SSID — e.g. `take-a-story-leave-a-story` — in its Wi-Fi list. The SSID *is* the
   signage.
2. Connecting triggers a captive portal: the box's web app, served entirely locally.
3. The passerby reads the current contents (the Exchange) and the ambient portrait (the Murmur).
4. Leaving something is short, text-first, anonymous. The etiquette nudges reciprocity ("you took one —
   leave one?").
5. Capacity is bounded; age + scarcity + a light reader signal decide what stays and what composts. The
   box is always an honest snapshot of the recent street.

## Architecture Direction

- Keep:
  - The constraints themselves as the design center: small, offline, anonymous, capacity-bounded. They
    are the muse, not the obstacle.
- Evolve:
  - From a laptop dev server (fast iteration, real browser) to ESP32 firmware (open AP, captive portal,
    LittleFS persistence, OTA), with the same app behavior behind a portable storage contract.
- Add:
  - The Exchange loop, the Murmur view, the forgetting/decay engine, the keeper admin surface, and the
    prompt/theming system.

## Non-Goals

- Not a social network. No identity, no accounts, no follows, no DMs.
- No cloud, no remote server, no sensitive credentials stored on the device.
- Not permanent archival — it forgets on purpose; it is not a record to preserve.
- Not global. A Stoop is local to a pole; its reach is a sidewalk, not the internet.
- No moderation-at-scale apparatus; abuse is bounded by design constraints (capacity, brevity,
  text-only, decay, keeper pruning), not by a content pipeline.
- Not AI-centric. (A deliberate step away from the rest of the workspace.)

## Success Criteria

1. A stranger can join, read, and leave something in under a minute, on a phone, with zero instructions
   beyond the SSID name.
2. The box runs fully offline with no cloud dependency and no stored credentials.
3. Contents turn over on their own: an unattended Stoop stays full, fresh, and bounded without the
   keeper deleting anything by hand.
4. The Murmur view is legibly *about this block* — a returning visitor recognizes the neighborhood in
   it.
5. The same codebase reskins to a different prompt (stories → rocks → tips) by keeper config alone.
6. The whole thing ports onto a sub-$10 ESP32-class board within the capacity budget.
