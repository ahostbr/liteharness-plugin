"""Focused negative proofs for autoapproval's authoritative identity boundary."""
import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location('guard_identity', Path(__file__).resolve().parents[1] / 'hooks/mods/guard_backend.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def setup_registry(tmp_path, monkeypatch):
    agents = tmp_path / 'agents'
    agents.mkdir()
    now = datetime.now(timezone.utc).timestamp()
    parent = SimpleNamespace(pid=42, name=lambda: 'claude.exe', create_time=lambda: now - 10)
    monkeypatch.setitem(sys.modules, 'psutil', SimpleNamespace(Process=lambda pid: parent))
    record = {'agent_id': 'seat', 'session_pid': 42, 'cli': 'claude-code',
              'registration_source': 'takeover', 'registered_at': datetime.fromtimestamp(now - 5, timezone.utc).isoformat(),
              'cwd': str(tmp_path)}
    file = agents / 'seat.json'
    file.write_text(json.dumps(record))
    return parent, record, file


def test_current_parent_binding_and_spoofed_session(tmp_path, monkeypatch):
    parent, record, file = setup_registry(tmp_path, monkeypatch)
    assert guard.assignment_record('seat', tmp_path) == record
    assert guard.assignment_record('spoof', tmp_path) is None
    parent.name = lambda: 'python.exe'
    assert guard.assignment_record('seat', tmp_path) is None


@pytest.mark.parametrize('change', [{'session_pid': 123}, {'status': 'offline'},
                                   {'registration_source': 'startup'}, {'cli': 'codex'},
                                   {'registered_at': '2000-01-01T00:00:00+00:00'}])
def test_stale_or_non_authoritative_registration(tmp_path, monkeypatch, change):
    _, record, file = setup_registry(tmp_path, monkeypatch)
    file.write_text(json.dumps({**record, **change}))
    assert guard.assignment_record('seat', tmp_path) is None


def test_duplicate_owner_is_ambiguous(tmp_path, monkeypatch):
    _, record, file = setup_registry(tmp_path, monkeypatch)
    file.with_name('duplicate.json').write_text(json.dumps({**record, 'agent_id': 'other'}))
    assert guard.assignment_record('seat', tmp_path) is None


def test_spoofed_cwd_does_not_earn_ownership(tmp_path, monkeypatch):
    owned = tmp_path / 'owned'
    spoof = tmp_path / 'spoof'
    owned.mkdir()
    spoof.mkdir()
    monkeypatch.setattr(guard, 'assignment_record', lambda sid, home: {'cwd': str(owned)})
    p = {'tool_name': 'Write', 'session_id': 'seat', 'cwd': str(spoof), 'tool_input': {'file_path': 'new.py'}}
    assert not guard.own_write(p, tmp_path)


def test_reparse_components_refuse_before_git(tmp_path, monkeypatch):
    monkeypatch.setattr(guard, 'assignment_record', lambda sid, home: {'cwd': str(tmp_path)})
    monkeypatch.setattr(guard, 'is_reparse', lambda path: path == tmp_path)
    p = {'tool_name': 'Write', 'session_id': 'seat', 'cwd': str(tmp_path), 'tool_input': {'file_path': 'new.py'}}
    assert not guard.own_write(p, tmp_path)


def test_real_symlink_scan_no_follow(tmp_path):
    target = tmp_path / 'tree'
    target.mkdir()
    outside = tmp_path / 'outside'
    outside.mkdir()
    link = target / 'linked'
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip('host lacks symlink creation privilege; reparse fixture tested separately')
    assert 'contains' in guard.junction_refusal('git worktree remove --force tree', tmp_path)
    assert outside.exists()


def test_git_option_force_alias_not_skipped(tmp_path):
    with pytest.raises(ValueError):
        guard.junction_refusal('git -C other worktree remove -ff tree', tmp_path)
