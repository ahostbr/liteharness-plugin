#!/usr/bin/env python
"""Release gate: every version declaration in the repo must agree.

WHY THIS EXISTS, with the incident attached. Release 1.0.13 (8507c9f) bumped
`.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` and MISSED
`.codex-plugin/plugin.json`, which stayed at 1.0.12. That state was PUBLISHED, so
the plugin has been disagreeing with itself about its own version ever since. It
was found by accident while preparing 1.0.14, not by any check.

WHY check_version_bump.py DID NOT CATCH IT -- it asks a different question:
  * it compares each manifest to ITS OWN HEAD ("did you bump?"), never the
    manifests to EACH OTHER ("do you agree?"). Bumping .claude-plugin 13->14 and
    .codex-plugin 12->13 passes it while leaving them inconsistent.
  * its RELEASE_MANIFESTS tuple omits `.claude-plugin/marketplace.json` entirely,
    even though its own failure message tells you to `git add` that file -- and
    marketplace.json declares the version TWICE.
  * it is a pre-commit hook enabled by `git config core.hooksPath .githooks`,
    ONCE PER CLONE. A fresh clone has it blank, so the guard is inert by default
    and its silence is indistinguishable from a pass.
This gate is complementary, not a replacement: bump-ness and agreement are
different properties.

🔴 DISCOVERY, NOT A FILE LIST. The sites are found by walking every tracked JSON
structurally, at any nesting depth. A hardcoded list is exactly the defect this
exists to catch -- and it would have missed `/plugins[0]/version`, the second
declaration inside marketplace.json.

Usage:
    python scripts/check_version_consistency.py              # the working tree
    python scripts/check_version_consistency.py --ref <sha>  # any commit, read-only

Exit: 0 all declarations agree · 1 they disagree · 2 nothing found (vacuous, not a pass)
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def _git(*args: str) -> str:
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    return r.stdout


def _tracked_json(ref: str | None) -> list[str]:
    if ref:
        out = _git("ls-tree", "-r", "--name-only", ref)
    else:
        out = _git("ls-files")
    return [f for f in out.splitlines() if f.strip().endswith(".json")]


def _read(path: str, ref: str | None) -> str | None:
    if ref:
        r = subprocess.run(["git", "show", f"{ref}:{path}"],
                           capture_output=True, text=True)
        return r.stdout if r.returncode == 0 else None
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return None


def _walk(node, path=""):
    """Yield (json_path, value) for every "version" key at ANY depth."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "version" and isinstance(v, str):
                yield (path + "/version", v)
            else:
                yield from _walk(v, path + "/" + str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk(v, path + "[%d]" % i)


def collect(ref: str | None) -> list[tuple[str, str, str]]:
    sites: list[tuple[str, str, str]] = []
    for f in _tracked_json(ref):
        text = _read(f, ref)
        if text is None:
            continue
        try:
            doc = json.loads(text)
        except ValueError:
            continue  # a malformed JSON is check_pii/format's problem, not ours
        for jpath, val in _walk(doc):
            if SEMVER.match(val):
                sites.append((f, jpath, val))
    return sites


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default=None,
                    help="git ref to check instead of the working tree")
    a = ap.parse_args()

    sites = collect(a.ref)
    where = a.ref or "working tree"

    if not sites:
        # A gate that finds nothing must not report success -- that is the
        # vacuous-pass shape this repo has been bitten by repeatedly.
        print("VERSION GATE: found NO version declarations in %s." % where)
        print("  That is not a pass. Either the manifests moved or this gate is "
              "looking in the wrong place.")
        return 2

    distinct = sorted({v for _, _, v in sites})
    for f, jpath, val in sorted(sites):
        print("  %-38s %-22s %s" % (f, jpath, val))
    print()

    if len(distinct) == 1:
        print("VERSION GATE: OK — %d declaration(s) across %d file(s), all %s (%s)."
              % (len(sites), len({f for f, _, _ in sites}), distinct[0], where))
        return 0

    print("VERSION GATE: FAILED — %d DIFFERENT versions declared: %s"
          % (len(distinct), ", ".join(distinct)))
    for d in distinct:
        owners = [f + jpath for f, jpath, v in sites if v == d]
        print("    %-10s <- %s" % (d, ", ".join(sorted(owners))))
    print()
    print("  A release cannot ship manifests that disagree about its own version.")
    print("  Fix: set every site to the same value (scripts/bump_version.py), then re-run.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
