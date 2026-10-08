"""Delivered operating prompts must not activate the removed close protocol.

Historical release notes are deliberately outside this active-instruction domain.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
REMOVED = re.compile(r"liteharness\s+(?:retire|ack-idle)\b|/exit.{0,30}blocked", re.I)


def test_delivered_active_prompts_have_no_removed_protocol():
    paths = sorted((ROOT / "prompts").rglob("*.md"))
    paths += [ROOT / "skills" / name for name in (
        "ls-init-liteharness/skill-template.md", "ls-liteharness/SKILL.md", "ls-sentinel/SKILL.md")]
    assert len(paths) > 50  # Positive domain control: not an empty search.
    violations = [str(path.relative_to(ROOT)) for path in paths
                  if REMOVED.search(path.read_text(encoding="utf-8"))]
    assert not violations, violations


def test_canonical_lifecycle_sources_require_human_close_request():
    paths = [ROOT / "prompts" / name for name in (
        "THE_LITE_WAY.md", "bootstrap-harness.md", "orchestrator-role.md",
        "preambles/leader-preamble.md", "preambles/worker-preamble.md",
        "preambles/thinker-preamble.md", "preambles/reviewer-preamble.md")]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert text.count("**Fleet lifecycle safety:**") == 1, path
        assert "Close a terminal only when the human explicitly asks." in text, path


def test_removed_instruction_detector_positive_and_negative_controls():
    assert REMOVED.search("Use liteharness retire <id>")
    assert REMOVED.search("Run liteharness ack-idle --handoff saved.md")
    assert REMOVED.search("/exit is blocked")
    assert not REMOVED.search("Pattern retirement describes superseded evidence.")
