#!/usr/bin/env python
"""Pre-commit guard: block catalog changes that forget the version bump.

If a commit stages changes under any cache-affecting directory (skills/,
agents/, commands/, hooks/) but the plugin versions in the release manifests are
identical to HEAD, Claude Code and Codex plugin caches can keep serving the old
catalog. This guard fails the commit with instructions instead.

Exit codes: 0 = ok (bumped, or no catalog change), 1 = missing bump.
"""
import subprocess
import sys
import re

CATALOG_DIRS = ("skills/", "agents/", "commands/", "hooks/")
RELEASE_MANIFESTS = (
    ".claude-plugin/plugin.json",
    ".codex-plugin/plugin.json",
)
VERSION_RE = re.compile(r'"version"\s*:\s*"(\d+\.\d+\.\d+)"')


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], capture_output=True, text=True
    ).stdout


def staged_files() -> list[str]:
    out = _git("diff", "--cached", "--name-only")
    return [line.strip() for line in out.splitlines() if line.strip()]


def version_in(ref: str) -> str | None:
    # ref like "HEAD:path" or ":path" (staged/index)
    text = _git("show", ref)
    m = VERSION_RE.search(text)
    return m.group(1) if m else None


def main() -> int:
    files = staged_files()
    touched = [f for f in files if any(f.startswith(d) for d in CATALOG_DIRS)]
    if not touched:
        return 0

    unbumped = []
    for manifest in RELEASE_MANIFESTS:
        head_v = version_in(f"HEAD:{manifest}")
        if head_v is None:
            # No HEAD version (first commit / new file) — nothing to compare.
            continue
        staged_v = version_in(f":{manifest}")  # version in the index
        if staged_v is None or staged_v == head_v:
            unbumped.append((manifest, head_v))

    if not unbumped:
        return 0  # version was bumped — good

    first_manifest, first_version = unbumped[0]
    manifest_list = ", ".join(manifest for manifest, _ in unbumped)
    sys.stderr.write(
        "\n[liteharness pre-commit] BLOCKED: catalog changed but version not bumped.\n"
        f"  Staged catalog files: {len(touched)} (e.g. {touched[0]})\n"
        f"  Version still {first_version} in {first_manifest}.\n"
        f"  Unbumped release manifests: {manifest_list}\n\n"
        "  Plugin caches only rebuild on a version change.\n"
        "  Run this, then re-stage and commit:\n"
        "      python scripts/bump_version.py\n"
        "      git add .claude-plugin/marketplace.json .claude-plugin/plugin.json .codex-plugin/plugin.json\n\n"
        "  (Bypass only if you know the cache is unaffected: git commit --no-verify)\n"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
