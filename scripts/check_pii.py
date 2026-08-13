#!/usr/bin/env python
"""Pre-commit PII / machine-path guard for the public liteharness-plugin.

Blocks a commit (or `--all` scan) that introduces the author's machine paths,
personal emails, Discord IDs, or private project codenames into tracked files.
This is the gate that makes the 2026-06 privacy scrub stick: even if the
/library catalog is regenerated, a username path can never be committed.

Does NOT block brand/identity that is intentionally public: the author's name
(Ryan / Ryan Devlin attribution), the Marlee Rose / Carly dedication, or public
product names (LiteSuite, LiteEditor, LiteSpeak, ...). Those are the brand.

Usage:
  python scripts/check_pii.py          # scan STAGED files (pre-commit)
  python scripts/check_pii.py --all    # scan all tracked text files (CI/manual)
"""
import sys, subprocess, re, hashlib
from pathlib import Path

# A real user home — capture the user segment so we can allow documented
# placeholders (TestUser, <username>, ...) while blocking actual people's homes.
#
# Assembled from a fragment rather than written out, because the literal form of this
# pattern IS an instance of what it detects: with "/c/Users/" spelled inline, the guard
# matched its own source and blocked the repo. The previous design hid that behind a
# self-exemption; the exemption is gone, so the regex has to be honest instead. Splitting
# the segment out is the whole fix - nothing else changes about the match.
_USERS = "Users"
USERNAME_RE = re.compile(
    r"(?:C:[\\/]" + _USERS + r"[\\/]|/c/" + _USERS + r"/)([^\\/\s\"'<>]+)", re.I
)
PLACEHOLDER_USERS = {
    "testuser", "user", "username", "youruser", "you", "youruser",
    "example", "name", "me", "yourname", "public", "default",
}

# STRUCTURAL patterns — shapes, not secrets. Safe to publish literally.
PATTERNS = [
    ("private drive", re.compile(r"E:[\\/]SAS", re.I)),
]

# EXACT identifiers, stored as SHA-256 of the lowercased token.
#
# 🔴 WHY HASHES AND NOT LITERALS. This file used to carry the Discord user IDs, both
# personal email locals and both private codenames as regex alternations - and it is
# TRACKED IN A PUBLIC REPO and copied into every LiteSuite installer. The guard written to
# keep personal identifiers out of public artifacts was itself the single most concentrated
# disclosure of them in the tree. It even had to exempt itself from its own scan
# (`if Path(rel).name == "check_pii.py": continue`, commented "the guard holds the denylist
# literals") - and a rule that must exempt its own enforcer is telling you the design is
# wrong, not that the exemption is needed.
#
# ⭐ Found by a virgin-Sandbox sweep for the raw IDs, which flagged this file. The scanner
# was the only thing on the box still carrying them after the private skills were excluded.
#
# A hash cannot be reversed into the identifier but still matches it exactly, so the guard
# keeps working and the self-exemption is gone: this file is now scanned like any other.
# To add an identifier: python -c "import hashlib;print(hashlib.sha256(b'<lowercased>').hexdigest())"
SECRET_TOKEN_SHA256 = {
    "9c90049b1de0a64d3a6409106783e088035da1a06a51426abcccf36555ac09fb": "discord id",
    "d8d06e03342377d4739d9ead355d566bda7b1935de149d26336413b927e9de9a": "discord id",
    "c6b6f3a7c04332b8abbe6f60244f7c50de433d253fae241ca42f4ec5a93dd77e": "personal email",
    "5c91ccd0905dac433a3fdbb29d8cc28d343ea46e8a05728a9f266fb2a1d4433a": "personal email",
    "37f6bddc5f0b52f2cee65666ee032a1bb7f56f3edf9e32b264024248939bbc9f": "private codename",
}

# Candidate tokens pulled from each line and hash-compared. Deliberately broad: a missed
# token is a missed detection, and the cost of an extra hash is nothing.
_NUMERIC = re.compile(r"\b\d{15,22}\b")            # Discord snowflakes
_EMAIL_LOCAL = re.compile(r"\b([A-Za-z0-9._%+-]{3,})@")
_WORD = re.compile(r"[A-Za-z][A-Za-z0-9]{3,}")


def secret_tokens_in(line: str):
    """Yield (label, token) for every hashed identifier appearing in `line`."""
    cands = set()
    cands.update(_NUMERIC.findall(line))
    cands.update(_EMAIL_LOCAL.findall(line))
    words = _WORD.findall(line)
    cands.update(words)
    # Bigrams, so multi-word codenames are still caught.
    cands.update(f"{a} {b}" for a, b in zip(words, words[1:]))
    for c in cands:
        h = hashlib.sha256(c.lower().encode()).hexdigest()
        label = SECRET_TOKEN_SHA256.get(h)
        if label:
            yield label, c

TEXT_EXT = {".md", ".py", ".ps1", ".sh", ".js", ".mjs", ".ts", ".tsx", ".json",
            ".yaml", ".yml", ".txt", ".bat", ".cjs", ".cmd"}
# Third-party license files legitimately carry their own authors' emails.
ALLOW_SUBSTR = ("/canvas-fonts/",)

def _git(args):
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout.splitlines()

def files_to_scan():
    if "--all" in sys.argv:
        return [l for l in _git(["ls-files"]) if l.strip()]
    return [l for l in _git(["diff", "--cached", "--name-only", "--diff-filter=ACM"]) if l.strip()]

def main():
    hits = []
    scanned = 0
    for rel in files_to_scan():
        if Path(rel).suffix.lower() not in TEXT_EXT:
            continue
        if any(s in ("/" + rel) for s in ALLOW_SUBSTR):
            continue
        p = Path(rel)
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue
        scanned += 1
        for i, line in enumerate(text.splitlines(), 1):
            for m in USERNAME_RE.finditer(line):
                if m.group(1).lower() not in PLACEHOLDER_USERS:
                    hits.append((rel, i, "username path", line.strip()[:120]))
                    break
            for label, pat in PATTERNS:
                if pat.search(line):
                    hits.append((rel, i, label, line.strip()[:120]))
            for label, tok in secret_tokens_in(line):
                hits.append((rel, i, label, line.strip()[:120]))
    if hits:
        print("BLOCKED: personal/machine data must not enter the public plugin:")
        for rel, i, label, snip in hits:
            print(f"  {rel}:{i}  [{label}]  {snip}")
        print("\nFix: use ~ or ${CLAUDE_SKILL_DIR} for paths; remove the data; then re-commit.")
        print("(Brand is allowed — author name, Marlee/Carly dedication, and product names are NOT blocked.)")
        return 1
    if scanned == 0:
        print("check_pii: NOTHING SCANNED (0 text files). That is not a pass - it is a")
        print("           broken instrument reporting success over an empty set.")
        return 2
    print(f"check_pii: clean ({scanned} text files scanned)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
