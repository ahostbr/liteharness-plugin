"""Regenerate role wrappers without changing any polymath METHOD body.

Standalone preambles are the public source of role glue. Existing public pure
METHOD files locate the unchanged bundle suffix, including methods without a
POLYMATHIC heading. No personal orchestrator sources are read. Run from any cwd;
use --check in validation.

The orchestrator template (cognitive-architectures/orchestrator/default.md) is
maintained by hand and is not touched here. This script used to copy one
"Fleet lifecycle safety" paragraph into it from orchestrator-role.md; that
paragraph was dropped from the doctrine (2026-11-12), so there is nothing left
to project.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TIERS = {"leader": "leaders", "worker": "workers", "thinker": "thinkers", "reviewer": "reviewers"}

# The leader and worker bundles carry a shorter browser line than their standalone
# preambles. LiteSuite's generator, which writes the same files from its own templates,
# keeps the two wordings distinct on purpose (its T0556 note), and its text is the
# reference for this repo. So a bundle rendered from a preamble gets the bundle wording
# back: (wording in the standalone preamble, wording in the bundle).
BUNDLE_WORDING: dict[str, tuple[str, str]] = {
    "leader": (
        '{"url": ...}` to display (each page is a TAB of your one agent browser pane, never a new\n'
        "  pane per page; `newPane=true` only when a separate pane is asked for), `/browser/*` endpoints (screenshot, javascript,\n",
        '{"url": ...}` to display, `/browser/*` endpoints (screenshot, javascript,\n',
    ),
    "worker": (
        "- Use `browser` tool to show websites to the human via the built-in BrowserView: `create` opens a TAB in your one agent browser pane (per workspace/thread) and `new_tab` adds another; `newPane=true` only when a separate pane is asked for\n",
        "- Use `browser` tool to show websites to the human via the built-in BrowserView\n",
    ),
}


def method_slice(raw: bytes, pure: bytes) -> bytes:
    _, separator, method = pure.partition(b"-->")
    if not separator:
        raise ValueError("pure METHOD has no generated header")
    method = method.lstrip(b"\r\n")
    if not method or not raw.endswith(method):
        raise ValueError("bundle METHOD does not match its public pure source")
    return raw[-len(method):]


def render_bundle(raw: bytes, pure: bytes, preamble: str, role: str) -> bytes:
    method = method_slice(raw, pure)
    head = raw[:-len(method)]
    wrapper = head.decode("utf-8").replace("\r\n", "\n")
    # Keep the existing METHOD-only void clause, including the polymath name.
    prefix, separator, old = wrapper.partition("\n\n# ")
    if not separator or "METHOD FILE" not in prefix or "VOID CLAUSE" not in prefix:
        raise ValueError("bundle has no METHOD-only void clause")
    heading = re.fullmatch(r"POLYMATHIC (.+?) [—-] .+ Mode", old.splitlines()[0])
    if not heading:
        raise ValueError("bundle has no role heading")
    title = "POLYMATHIC " + heading[1]
    name = heading[1].title()
    _, separator, body = preamble.partition("-->\n")
    if not separator:
        raise ValueError("preamble has no generated header")
    body = body.lstrip("\n")
    if role in BUNDLE_WORDING:
        standalone, bundled = BUNDLE_WORDING[role]
        if body.count(standalone) > 1:
            raise ValueError(f"{role} preamble has its browser line more than once")
        body = body.replace(standalone, bundled)
    body = body.replace(f"# {role.upper()} ROLE —", f"# {title} —")
    body = body.replace("your assigned polymathic cognitive architecture (composed separately)", f"{name}'s cognitive architecture")
    body = body.replace("your assigned polymath", name)
    rendered = prefix + "\n\n" + body.rstrip("\n") + "\n\n"
    # A checkout with CRLF line endings keeps them: the wrapper is written the way the file
    # already is, or every bundle would read as stale on such a checkout.
    if b"\r\n" in head:
        rendered = rendered.replace("\n", "\r\n")
    # METHOD is appended as original bytes, including its original final newline.
    return rendered.encode("utf-8") + method


def generate(root: Path, *, check: bool = False) -> list[Path]:
    changes = []
    architecture_root = root / "prompts" / "cognitive-architectures"
    for role, directory in TIERS.items():
        preamble = (root / "prompts" / "preambles" / f"{role}-preamble.md").read_text(encoding="utf-8")
        bundles = sorted((architecture_root / directory).glob("*.md"))
        if not bundles:
            raise ValueError(f"no {role} bundles found")
        for path in bundles:
            old = path.read_bytes()
            pure = (architecture_root / "pure" / path.name).read_bytes()
            new = render_bundle(old, pure, preamble, role)
            if method_slice(new, pure) != method_slice(old, pure):
                raise AssertionError("METHOD changed")
            if new != old:
                changes.append(path)
                if not check:
                    path.write_bytes(new)
    return changes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail when generated wrappers are stale; write nothing")
    args = parser.parse_args()
    changes = generate(ROOT, check=args.check)
    for path in changes:
        print(path.relative_to(ROOT).as_posix())
    print(f"role wrappers: {len(changes)} {'stale' if args.check else 'updated'}")
    return int(args.check and bool(changes))


if __name__ == "__main__":
    raise SystemExit(main())
