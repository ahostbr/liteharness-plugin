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


def test_the_dropped_close_rule_is_in_no_delivered_prompt_or_skill():
    """The owner dropped "close a terminal only when the human asks" everywhere (2026-11-12).

    This used to require the opposite: one "Fleet lifecycle safety" block, with that sentence,
    in each of seven prompt files. A copy of older text over these files would bring the rule
    back without anyone deciding to, which is how a prompt change was lost once already.
    """
    paths = sorted((ROOT / "prompts").rglob("*.md"))
    paths += [ROOT / "skills" / name for name in (
        "ls-init-liteharness/skill-template.md", "ls-liteharness/SKILL.md", "ls-sentinel/SKILL.md")]
    assert len(paths) > 50  # Positive domain control: not an empty search.
    dropped = ("**Fleet lifecycle safety:**", "Close a terminal only when the human explicitly asks.",
               "close only when the human asks", "or self-retire")
    violations = [(str(path.relative_to(ROOT)), phrase) for path in paths
                  for phrase in dropped if phrase in path.read_text(encoding="utf-8")]
    assert not violations, violations


def test_removed_instruction_detector_positive_and_negative_controls():
    assert REMOVED.search("Use liteharness retire <id>")
    assert REMOVED.search("Run liteharness ack-idle --handoff saved.md")
    assert REMOVED.search("/exit is blocked")
    assert not REMOVED.search("Pattern retirement describes superseded evidence.")
