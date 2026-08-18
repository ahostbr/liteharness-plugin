#!/usr/bin/env python
"""Pre-commit guard: block catalog changes that forget the version bump.

If a commit stages changes under any cache-affecting directory (skills/,
agents/, commands/, hooks/) but the plugin versions in the release manifests are
identical to the LAST PUBLISHED release, Claude Code and Codex plugin caches can
keep serving the old catalog. This guard fails the commit with instructions.

The baseline is the last PUBLISHED release, NOT the previous commit. Publishing
this plugin IS a push to the tracking branch -- there is no CI and no separate
release artifact, and `/plugin marketplace update` pulls from that ref -- so the
upstream ref is the publish point. Baselining on HEAD instead made every
intermediate commit of a multi-commit release fail, and the only way to green it
was to bump again: the gate teaching you to publish a phantom version. Measured
on the 1.0.14 release, which it blocked at 9a8fc31.

  baseline order: --baseline REF > @{upstream} > origin/main > HEAD (degraded)

Exit codes: 0 = ok (bumped, or no catalog change), 1 = missing bump.
"""
import argparse
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


def _rev_parse(ref: str) -> str | None:
    out = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", ref],
        capture_output=True, text=True,
    )
    return out.stdout.strip() or None


def resolve_baseline(explicit: str | None) -> tuple[str, bool]:
    """Return (ref, is_publish_point) for the version baseline."""
    if explicit:
        return explicit, True
    for ref in ("@{upstream}", "origin/main"):
        if _rev_parse(ref):
            return ref, True
    # No publish point knowable (no remote, or a fresh repo). Fall back to HEAD:
    # that can only OVER-block, never under-block, which is the safe direction
    # for a gate -- but say so, because over-blocking is the original defect.
    return "HEAD", False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", default=None,
                    help="ref of the last published release "
                         "(default: @{upstream}, else origin/main, else HEAD)")
    args = ap.parse_args()
    baseline, published = resolve_baseline(args.baseline)

    files = staged_files()
    touched = [f for f in files if any(f.startswith(d) for d in CATALOG_DIRS)]
    if not touched:
        return 0

    unbumped = []
    for manifest in RELEASE_MANIFESTS:
        base_v = version_in(f"{baseline}:{manifest}")
        if base_v is None:
            # Manifest absent at the baseline (first commit / new file).
            continue
        staged_v = version_in(f":{manifest}")  # version in the index
        if staged_v is None or staged_v == base_v:
            unbumped.append((manifest, base_v))

    if not unbumped:
        return 0  # version was bumped — good

    first_manifest, first_version = unbumped[0]
    baseline_sha = (_rev_parse(baseline) or "?")[:7]
    if not published:
        sys.stderr.write(
            "\n[liteharness pre-commit] WARNING: no publish point found "
            "(@{upstream} / origin/main); baselining on HEAD, which "
            "over-blocks intermediate release commits.\n"
        )
    manifest_list = ", ".join(manifest for manifest, _ in unbumped)
    sys.stderr.write(
        "\n[liteharness pre-commit] BLOCKED: catalog changed but version not bumped.\n"
        f"  Staged catalog files: {len(touched)} (e.g. {touched[0]})\n"
        f"  Version still {first_version} in {first_manifest},\n"
        f"    unchanged since baseline {baseline} ({baseline_sha}).\n"
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
