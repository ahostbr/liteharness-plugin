"""Regenerate role wrappers without changing any polymath METHOD body.

Standalone preambles are the public source of role glue. Existing public pure
METHOD files locate the unchanged bundle suffix, including methods without a
POLYMATHIC heading. No personal orchestrator sources are read. Run from any cwd;
use --check in validation.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TIERS = {"leader": "leaders", "worker": "workers", "thinker": "thinkers", "reviewer": "reviewers"}


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
    wrapper = raw[:-len(method)].decode("utf-8").replace("\r\n", "\n")
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
    body = body.replace(f"# {role.upper()} ROLE —", f"# {title} —")
    body = body.replace("your assigned polymathic cognitive architecture (composed separately)", f"{name}'s cognitive architecture")
    body = body.replace("your assigned polymath", name)
    # METHOD is appended as original bytes, including its original final newline.
    return (prefix + "\n\n" + body.rstrip("\n") + "\n\n").encode("utf-8") + method


def lifecycle_span(raw: bytes) -> tuple[int, int]:
    """Locate one public lifecycle paragraph, preserving all surrounding bytes."""
    marker = b"**Fleet lifecycle safety:**"
    if raw.count(marker) != 1:
        raise ValueError("expected one fleet lifecycle safety block")
    start = raw.index(marker)
    ending = re.search(rb"\r?\n\r?\n", raw[start:])
    if ending is None:
        raise ValueError("lifecycle block has no paragraph boundary")
    return start, start + ending.start()


def render_orchestrator(raw: bytes, source: bytes) -> bytes:
    """Project only lifecycle glue, never the personalized/template architecture."""
    start, end = lifecycle_span(raw)
    source_start, source_end = lifecycle_span(source)
    block = source[source_start:source_end].replace(b"\r\n", b"\n")
    if raw[end:end + 2] == b"\r\n":
        block = block.replace(b"\n", b"\r\n")
    return raw[:start] + block + raw[end:]


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
    path = architecture_root / "orchestrator" / "default.md"
    old = path.read_bytes()
    source = (root / "prompts" / "orchestrator-role.md").read_bytes()
    new = render_orchestrator(old, source)
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
