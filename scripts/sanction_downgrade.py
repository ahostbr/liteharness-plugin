#!/usr/bin/env python
"""Sanction exactly ONE version downgrade, deliberately, by hand.

check_version_bump.py refuses a version DECREASE, because publishing a lower
version makes every installed plugin cache revert to an older catalog while
`/plugin update` reports success.

A deliberate revert is still possible, but it must be an act, not a setting.
Git passes NO arguments to the pre-commit hook, so --allow-downgrade cannot
reach the gate through `git commit`; and the ruling forbids an env var or a
config key, because anything a script can set once and forget stops being a
decision. So the sanction is a one-shot marker a human writes on purpose:

    python scripts/sanction_downgrade.py --from 1.0.14 --to 1.0.12 \
        --reason "1.0.14 shipped a broken skills tree; reverting while we fix"

Properties, each load-bearing:
  * written to the GIT DIR, never the worktree -- it cannot be staged,
    committed or shipped, and no .gitignore rule has to be trusted
  * ONE-SHOT: the gate deletes it on use, so it cannot become a standing bypass
  * PAIR-BOUND: it sanctions one transition, not downgrades in general; a
    stale marker for a different pair refuses
  * FAIL-CLOSED: absence blocks. Deleting this script or the marker makes
    downgrades harder, never easier.
"""
import argparse
import os
import re
import subprocess
import sys

VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
MARKER_NAME = "ALLOW_DOWNGRADE_ONCE"


def _ver(text):
    return tuple(int(part) for part in text.split("."))


def marker_path():
    out = subprocess.run(
        ["git", "rev-parse", "--git-dir"], capture_output=True, text=True
    ).stdout.strip()
    if not out:
        sys.stderr.write("not inside a git repository\n")
        raise SystemExit(2)
    return os.path.join(out, MARKER_NAME)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--from", dest="from_v", required=True,
                    help="the CURRENTLY PUBLISHED version being left")
    ap.add_argument("--to", dest="to_v", required=True,
                    help="the LOWER version being published instead")
    ap.add_argument("--reason", required=True,
                    help="why; printed by the gate when the sanction is used")
    args = ap.parse_args()

    for label, value in (("--from", args.from_v), ("--to", args.to_v)):
        if not VERSION_RE.match(value):
            sys.stderr.write(f"{label}: {value!r} is not a d.d.d version\n")
            return 2
    if _ver(args.to_v) >= _ver(args.from_v):
        sys.stderr.write(
            f"{args.from_v} -> {args.to_v} is not a downgrade; nothing to sanction.\n"
            "  (A forward bump needs no sanction -- just commit it.)\n"
        )
        return 2
    if not args.reason.strip():
        sys.stderr.write("--reason must not be empty\n")
        return 2

    path = marker_path()
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(f"{args.from_v} -> {args.to_v}\n{args.reason.strip()}\n")

    sys.stderr.write(
        f"\n[sanction] ONE downgrade authorised: {args.from_v} -> {args.to_v}\n"
        f"  reason: {args.reason.strip()}\n"
        f"  marker: {path}\n"
        "  It is consumed by the next commit that stages exactly this transition.\n"
        "  Any other pair still blocks, and it does not survive being used.\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
