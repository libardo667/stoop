# prune/ — the work-item ledger (Stoop)

Stoop's work-item harness: intended changes written down *before* they're built, reviewed against a
rubric frozen ahead of the work, and kept with their evidence. `majors/` hold large arcs; `minors/`
hold bounded changes; `harness/` holds the method (operating model, quality gates, the pruning
playbook). Item shapes live in [`majors/MAJOR_SCHEMA.md`](majors/MAJOR_SCHEMA.md) and
[`minors/MINOR_SCHEMA.md`](minors/MINOR_SCHEMA.md).

This is an instance of the reusable **[prune](https://github.com/libardo667/prune)** kit, vendored into
this repo (no nested `.git`) so Stoop's own anchors live alongside the method.

## Project anchors

- [`VISION.md`](VISION.md) — what Stoop is and is not.
- [`ROADMAP.md`](ROADMAP.md) — current state, guardrails, and the major/minor queues in execution order.

## How the record works here

`history/` is a **local, append-only archive** (gitignored), mirroring the work-item structure one level
down (`history/majors/`, `history/minors/`). Shipped or retired items — and entries the forgetting
engine evicts — move there with their evidence, never silently deleted. Live `majors/` and `minors/`
stay honest about what's actually open; read each item's own status for where it stands.

## Provenance — seams showing

These items are written by the operating AI instance in working session with the keeper (Levi), who
sets direction and holds the veto. Kept as worked, corrections and all.

## See also

- [`harness/`](harness/) — the operating model, quality gates, and pruning playbook this ledger runs on.
  Start at [`harness/00-ADOPTION_GUIDE.md`](harness/00-ADOPTION_GUIDE.md).
- **prune** — the same harness shipped empty, as a reusable scaffold for any project.
