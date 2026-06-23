#!/usr/bin/env python3
"""pick.py — an egalitarian, staleness-weighted picker for a prune backlog.

Part of the prune harness. Recency bias quietly turns any backlog into a monoculture:
whatever is loudest and most recent gets worked on, and the long tail rots. This tool
pools the *actionable* work items from one or more prune ledgers, weights the draw by
how long each has gone untouched (the most-neglected item gets the best odds — a refugia
mechanism for forgotten work), and nominates a shortlist. Draw N, you pick one. The draw
is a nomination, never a mandate.

A "ledger" is any directory holding `majors/` and/or `minors/` — either directly (a
standalone prune repo) or under a `prune/` subdir (a project that vendors the harness).
With no --root it picks from the current directory; add --root to pool across several
projects. Pooling tilts naturally toward whichever has the bigger backlog.

    cd my-project && python3 /path/to/prune/pick.py         # 3 nominations from ./ (or ./prune/)
    python3 pick.py --root ../worldweaver --root ../the-stable   # pool across projects
    python3 pick.py --kind minor -n 5                        # bounded items, bigger shortlist
    python3 pick.py --list                                   # whole eligible pool, stalest first
    python3 pick.py --all                                    # bypass the eligibility filter
    python3 pick.py --seed 7                                 # reproducible draw

Eligibility (skipped with --all): pointer-stubs (canonical elsewhere), parked /
revisit-later / parked-behind-a-dependency, and done / graduated items. Each nomination
prints its staleness, status line, and any "Depends On", so a blocked draw is vetoable at
a glance.
"""
import argparse
import os
import random
import re
import subprocess
import time
from dataclasses import dataclass
from os.path import abspath, basename, dirname, getmtime, isdir, join

# --- eligibility heuristics (tuned to prune's banner conventions; --all bypasses) ---
STUB = re.compile(r"canonical in\b|Shared cognitive substrate|Full spec\s*[-=]*>", re.I)
PARKED = re.compile(r"\bPARKED\b|REVISIT-LATER|REVISIT \(parked|held loosely.{0,40}\bPARK\b|parked behind|parked \d{4}|⏳", re.I)
DONE = re.compile(r"graduated into VISION|superseded by|\bSTATUS:?\s*\**\s*(DONE|COMPLETE|RESOLVED|SHIPPED|ARCHIVED)\b|✅", re.I)
# --- extraction ---
TITLE = re.compile(r"^#\s+(.+)")
STATUS = re.compile(r"^\s*[>\-*]*\s*\**\s*(?:STATUS|Status)\b\W*(.+)", re.M)
BANNER = re.compile(r"^\s*>\s*(?:⏳\s*)?\**\s*(.+)", re.M)
DEPENDS = re.compile(r"Depends[- ]On\W*(.+)", re.I)


@dataclass
class Item:
    repo: str
    kind: str          # "major" | "minor"
    num: int
    path: str
    title: str
    status: str
    depends: str
    ts: int            # last-commit epoch (staleness)
    eligible: bool = True
    reason: str = "active"

    @property
    def tag(self):
        return f"{self.repo} {'M' if self.kind == 'major' else 'm'}{self.num}"

    @property
    def days(self):
        return max(0, int((time.time() - self.ts) / 86400))


def read_head(path, n=30):
    try:
        with open(path, encoding="utf-8") as f:
            return "".join(f.readline() for _ in range(n))
    except OSError:
        return ""


def first(rx, text, default="—"):
    m = rx.search(text)
    if not m:
        return default
    s = re.sub(r"[*_`]", "", m.group(1))          # drop markdown emphasis / code marks
    return re.sub(r"\s+", " ", s).strip(" -:.")


def last_touched(path):
    """git last-commit epoch for one file, with an mtime fallback."""
    try:
        out = subprocess.run(
            ["git", "-C", dirname(path), "log", "-1", "--format=%ct", "--", basename(path)],
            capture_output=True, text=True, timeout=10,
        ).stdout.strip()
        if out:
            return int(out)
    except (OSError, subprocess.SubprocessError, ValueError):
        pass
    try:
        return int(getmtime(path))
    except OSError:
        return int(time.time())


def classify(head):
    if STUB.search(head):
        return False, "pointer-stub"
    if PARKED.search(head):
        return False, "parked/blocked"
    if DONE.search(head):
        return False, "done/graduated"
    return True, "active"


def resolve_ledger(root):
    """Return (label, ledger_dir) for a root, or None. Handles both layouts."""
    root = abspath(root.rstrip("/" + os.sep))
    for cand in (root, join(root, "prune")):
        if isdir(join(cand, "majors")) or isdir(join(cand, "minors")):
            label = basename(dirname(cand)) if basename(cand) == "prune" else basename(cand)
            return label, cand
    return None


def load(label, ledger, kinds):
    items = []
    for kind in kinds:
        d = join(ledger, kind + "s")
        if not isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            m = re.match(r"(\d+)-(.+)\.md$", fn)
            if not m:
                continue
            path = join(d, fn)
            head = read_head(path)
            ok, why = classify(head)
            items.append(Item(
                repo=label, kind=kind, num=int(m.group(1)), path=path,
                title=first(TITLE, head, m.group(2).replace("-", " ")),
                status=first(STATUS, head, first(BANNER, head, "—"))[:90],
                depends=first(DEPENDS, head, ""),
                ts=last_touched(path), eligible=ok, reason=why,
            ))
    return items


def wsample(items, k):
    """Weighted sample WITHOUT replacement; weight = staleness in days (+1)."""
    items = list(items)
    weights = [it.days + 1 for it in items]
    out = []
    for _ in range(min(k, len(items))):
        i = random.choices(range(len(items)), weights=weights, k=1)[0]
        out.append(items.pop(i))
        weights.pop(i)
    return out


def show(it, idx=None):
    print(f"{f'  [{idx}] ' if idx else '  → '}{it.tag:<16} {it.title[:58]:<58} · {it.days}d idle")
    line = f"        {it.reason if it.reason != 'active' else 'status'}: {it.status[:70]}"
    if it.depends:
        line += f"   ⚠ depends: {it.depends[:46]}"
    print(line)


def main():
    ap = argparse.ArgumentParser(description="Egalitarian, staleness-weighted picker for a prune backlog.")
    ap.add_argument("--root", action="append", default=[], metavar="PATH",
                    help="a ledger root (repeatable); default: this script's repo")
    ap.add_argument("-n", "--num", type=int, default=3, help="shortlist size (default 3)")
    ap.add_argument("--kind", choices=["major", "minor", "both"], default="both", help="default both")
    ap.add_argument("--all", action="store_true", help="ignore the eligibility filter")
    ap.add_argument("--list", action="store_true", help="just list the eligible pool, stalest first")
    ap.add_argument("--seed", type=int, help="reproducible draw")
    args = ap.parse_args()

    if args.seed is not None:
        random.seed(args.seed)
    kinds = ["major", "minor"] if args.kind == "both" else [args.kind]
    roots = args.root or [os.getcwd()]

    items, used = [], []
    for r in roots:
        res = resolve_ledger(r)
        if not res:
            print(f"  (skipped {r}: no majors/ or minors/ found)")
            continue
        label, ledger = res
        items += load(label, ledger, kinds)
        used.append(label)

    pool = items if args.all else [it for it in items if it.eligible]
    counts = " · ".join(f"{lbl} {sum(1 for it in pool if it.repo == lbl)}" for lbl in used)

    if not pool:
        print("nothing in the pool — try --all, or point --root at a prune ledger.")
        return

    if args.list:
        print(f"\n📋  eligible pool — {len(pool)} items ({counts}), stalest first\n")
        for it in sorted(pool, key=lambda x: -x.days):
            show(it)
        return

    shortlist = wsample(pool, args.num)
    pick = random.choices(shortlist, weights=[it.days + 1 for it in shortlist], k=1)[0]
    print(f"\n🎲  prune-pick — drew {len(shortlist)} of {len(pool)} eligible ({counts})\n")
    for i, it in enumerate(shortlist, 1):
        show(it, i)
    print()
    show(pick)
    print(f"      {pick.path}\n")


if __name__ == "__main__":
    main()
