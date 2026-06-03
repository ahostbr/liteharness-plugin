#!/usr/bin/env python
"""Bump the LiteHarness plugin version across all plugin manifests.

The Claude Code CLI caches an installed plugin under
`~/.claude/plugins/cache/<mp>/<plugin>/<version>/` and only rebuilds that
cache when the *version string* changes. If you edit skills/agents/commands/
hooks but leave the version untouched, the cache freezes and the CLI keeps
serving the OLD catalog forever. This script is the canonical way to release a
catalog change: it bumps the version in both manifests so `/plugin update`
invalidates the cache.

Usage:
    python scripts/bump_version.py            # patch  (1.0.1 -> 1.0.2)
    python scripts/bump_version.py patch
    python scripts/bump_version.py minor      # 1.0.1 -> 1.1.0
    python scripts/bump_version.py major      # 1.0.1 -> 2.0.0
    python scripts/bump_version.py --set 1.4.0
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFESTS = [
    ROOT / ".claude-plugin" / "marketplace.json",
    ROOT / ".claude-plugin" / "plugin.json",
    ROOT / ".codex-plugin" / "plugin.json",
]
SOURCE_OF_TRUTH = ROOT / ".claude-plugin" / "plugin.json"
VERSION_RE = re.compile(r'("version"\s*:\s*")(\d+)\.(\d+)\.(\d+)(")')


def current_version() -> tuple[int, int, int]:
    text = SOURCE_OF_TRUTH.read_text(encoding="utf-8")
    m = VERSION_RE.search(text)
    if not m:
        sys.exit(f"ERROR: no semver version found in {SOURCE_OF_TRUTH}")
    return int(m.group(2)), int(m.group(3)), int(m.group(4))


def compute_new(cur: tuple[int, int, int], args: list[str]) -> tuple[int, int, int]:
    if "--set" in args:
        val = args[args.index("--set") + 1]
        parts = val.split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            sys.exit(f"ERROR: --set expects X.Y.Z, got {val!r}")
        return tuple(int(p) for p in parts)  # type: ignore[return-value]
    bump = next((a for a in args if a in ("major", "minor", "patch")), "patch")
    major, minor, patch = cur
    if bump == "major":
        return major + 1, 0, 0
    if bump == "minor":
        return major, minor + 1, 0
    return major, minor, patch + 1


def main() -> None:
    args = sys.argv[1:]
    cur = current_version()
    new = compute_new(cur, args)
    new_str = ".".join(str(n) for n in new)
    for mf in MANIFESTS:
        text = mf.read_text(encoding="utf-8")
        text, n = VERSION_RE.subn(rf'\g<1>{new_str}\g<5>', text)
        mf.write_text(text, encoding="utf-8")
        print(f"  {mf.relative_to(ROOT)}: {n} version field(s) -> {new_str}")
    cur_str = ".".join(str(n) for n in cur)
    print(f"Bumped {cur_str} -> {new_str}. Commit, push, then run:")
    print("  /plugin marketplace update liteharness")
    print("  /plugin update liteharness@liteharness")


if __name__ == "__main__":
    main()
