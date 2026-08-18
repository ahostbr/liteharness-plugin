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

Why this was fixed in code rather than documented in a runbook: the gate's own
remediation text tells you to run bump_version.py. Under the old HEAD baseline
that advice publishes a phantom version -- the gate instructing you to corrupt
the very thing it exists to protect. The only other escape was --no-verify,
which drops check_pii.py on a PUBLIC repo. A runbook would have had to bless one
of those two as normal practice. That is a logic defect, not a doc defect.

The comparison is ORDERED, not inequality: the staged version must be GREATER
than the published one. A downgrade satisfying a "did it change?" check is the
gate reporting success about the exact event it exists to prevent -- every
installed cache silently reverts and /plugin update says it worked. Deliberate
reverts remain possible via --allow-downgrade, which is argv-only BY DESIGN: no
env var, no config key, no default can supply it, because the entire value of
the hatch is that a human chose it at the moment of the downgrade. When it is
used the gate still says so, loudly, naming both versions.

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


def _ver(text: str) -> tuple[int, ...]:
    """1.0.10 > 1.0.9 -- lexically it is not. VERSION_RE guarantees d+.d+.d+."""
    return tuple(int(part) for part in text.split("."))


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
    ap.add_argument("--allow-downgrade", action="store_true",
                    help="permit a version DECREASE; must be typed deliberately "
                         "(argv only -- no env var or config can supply it)")
    args = ap.parse_args()
    baseline, published = resolve_baseline(args.baseline)

    files = staged_files()
    touched = [f for f in files if any(f.startswith(d) for d in CATALOG_DIRS)]
    if not touched:
        return 0

    unbumped = []
    downgrades = []
    for manifest in RELEASE_MANIFESTS:
        base_v = version_in(f"{baseline}:{manifest}")
        if base_v is None:
            # Manifest absent at the baseline (first commit / new file).
            continue
        staged_v = version_in(f":{manifest}")  # version in the index
        if staged_v is None or staged_v == base_v:
            unbumped.append((manifest, base_v))
        elif _ver(staged_v) < _ver(base_v):
            downgrades.append((manifest, base_v, staged_v))

    if downgrades:
        listed = "; ".join(
            f"{m}: {b} -> {st}" for m, b, st in downgrades
        )
        if not args.allow_downgrade:
            sys.stderr.write(
                "\n[liteharness pre-commit] BLOCKED: version DOWNGRADE.\n"
                f"  {listed}\n"
                f"  Baseline {baseline} ({(_rev_parse(baseline) or '?')[:7]}) is "
                "the last PUBLISHED release.\n\n"
                "  Publishing a lower version makes every installed cache revert\n"
                "  to an older catalog, while /plugin update reports success.\n"
                "  If the revert is deliberate, say so explicitly:\n"
                "      python scripts/check_version_bump.py --allow-downgrade\n"
            )
            return 1
        sys.stderr.write(
            "\n[liteharness pre-commit] DOWNGRADE ALLOWED by --allow-downgrade.\n"
            f"  {listed}\n"
            "  Every installed cache will revert to the older catalog.\n"
        )

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
