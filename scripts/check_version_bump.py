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
import os
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


MARKER_NAME = "ALLOW_DOWNGRADE_ONCE"


def read_sanction():
    """One-shot downgrade marker written by scripts/sanction_downgrade.py.

    Lives in the GIT DIR so it can never be staged, committed or shipped.
    Returns (from, to, reason, path) or None. Anything malformed returns
    None -- an unreadable sanction is not a sanction (fail-closed).
    """
    git_dir = _git("rev-parse", "--git-dir").strip()
    if not git_dir:
        return None
    path = os.path.join(git_dir, MARKER_NAME)
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except OSError:
        return None
    first = text.splitlines()[0] if text.splitlines() else ''
    m = re.match(r"\s*(\d+\.\d+\.\d+)\s*->\s*(\d+\.\d+\.\d+)\s*$", first)
    if not m:
        return None
    reason = "\n".join(text.splitlines()[1:]).strip()
    return m.group(1), m.group(2), reason, path


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
        listed = "; ".join(f"{m}: {b} -> {st}" for m, b, st in downgrades)
        pairs = sorted({(b, st) for _, b, st in downgrades})
        sanction = read_sanction()
        base_sha = (_rev_parse(baseline) or '?')[:7]

        if args.allow_downgrade:
            sys.stderr.write(
                "\n[liteharness] DOWNGRADE ALLOWED by --allow-downgrade.\n"
                f"  {listed}\n"
                "  Every installed cache will revert to the older catalog.\n"
            )
        elif sanction is None:
            sys.stderr.write(
                "\n[liteharness pre-commit] BLOCKED: version DOWNGRADE, unsanctioned.\n"
                f"  {listed}\n"
                f"  Baseline {baseline} ({base_sha}) is the last PUBLISHED release.\n\n"
                "  Publishing a lower version makes every installed cache revert to an\n"
                "  older catalog, while /plugin update reports success.\n\n"
                "  If this revert is deliberate, authorise this ONE transition:\n"
                f"      python scripts/sanction_downgrade.py --from {pairs[0][0]} "
                f"--to {pairs[0][1]} --reason \"...\"\n"
            )
            return 1
        elif len(pairs) != 1 or (sanction[0], sanction[1]) != pairs[0]:
            held = f"{sanction[0]} -> {sanction[1]}"
            staged = "; ".join(f"{b} -> {st}" for b, st in pairs)
            sys.stderr.write(
                "\n[liteharness pre-commit] BLOCKED: the sanction does not match.\n"
                f"  marker authorises : {held}\n"
                f"  staged transition : {staged}\n\n"
                "  A sanction covers ONE transition, not downgrades in general.\n"
                "  Re-run scripts/sanction_downgrade.py for the pair you mean.\n"
            )
            return 1
        else:
            try:
                os.remove(sanction[3])
                consumed = True
            except OSError:
                consumed = False
            sys.stderr.write(
                "\n[liteharness pre-commit] DOWNGRADE SANCTIONED and allowed.\n"
                f"  {listed}\n"
                f"  reason: {sanction[2]}\n"
                "  Every installed cache will revert to the older catalog.\n"
                f"  marker consumed: {consumed} (one-shot; the next downgrade blocks again)\n"
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
