"""Security selfreview regressions exercising the shipped bridge."""
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location('guard_regressions', Path(__file__).resolve().parents[1] / 'hooks/mods/guard_backend.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def payload(**changes):
    return {'protocol': 1, 'kind': 'call', 'session_id': 'seat', 'cwd': str(Path.cwd()),
            'tool_name': 'Bash', 'tool_input': {'command': 'git status'}, **changes}


@pytest.mark.parametrize('bad', [{}, [], False, '', {'hookSpecificOutput': {}},
                                {'hookSpecificOutput': {'permissionDecision': 'deny', 'permissionDecisionReason': None}}])
def test_malformed_floor_never_falls_through(bad):
    gate = SimpleNamespace(decide=lambda p: bad)
    with pytest.raises(ValueError):
        guard.decide(payload(), gate=gate, ownership=lambda p: pytest.fail('proof ran'))


@pytest.mark.parametrize('command', ["git worktree 'remove' --force tree", "git 'worktree' remove --force tree", "'git' worktree remove '--force' tree"])
def test_quoted_force_invocations_are_scanned(tmp_path, monkeypatch, command):
    target = tmp_path / 'tree'
    target.mkdir()
    child = target / 'junction'
    child.mkdir()
    original = guard.is_reparse
    monkeypatch.setattr(guard, 'is_reparse', lambda p: p == child or original(p))
    assert 'contains' in guard.junction_refusal(command, tmp_path)


@pytest.mark.parametrize('option', ['--for', '--forc', "'--for'", '"--forc"'])
def test_force_prefix_refused_before_reparse_target_or_execution(tmp_path, monkeypatch, option):
    target = tmp_path / 'tree'
    target.mkdir()
    child = target / 'junction'
    child.mkdir()
    monkeypatch.setattr(guard, 'is_reparse', lambda p: p == child)
    monkeypatch.setattr(guard.subprocess, 'run', lambda *a, **kw: pytest.fail('submitted removal executed'))
    gate = SimpleNamespace(decide=lambda p: None)
    with pytest.raises(ValueError, match='Unsupported worktree removal option'):
        guard.decide(payload(cwd=str(tmp_path), tool_input={'command': f'git worktree remove {option} tree'}), gate=gate)
    assert target.is_dir() and child.is_dir()


@pytest.mark.parametrize('command', [
    'git -C other worktree remove --for tree',
    'git -c core.worktree=other worktree remove --forc tree',
    "git 'worktree' remove --for tree",
    "git worktree 'remove' --forc tree",
    'git worktree remove -ff tree',
])
def test_global_options_and_other_force_variants_never_skip_guard(tmp_path, command):
    with pytest.raises(ValueError):
        guard.junction_refusal(command, tmp_path)


def test_plain_nonforce_remove_preserves_permission_path(tmp_path):
    assert guard.junction_refusal('git worktree remove missing', tmp_path) is None
    # -- ends options: a literal force-looking pathname is not a force request.
    assert guard.junction_refusal('git worktree remove -- --for', tmp_path) is None


def test_compiles_verified_bytes_and_binds_exact_floor(monkeypatch, tmp_path, release_source):
    candidate = SimpleNamespace(version='0.4.6',
                                locate_file=lambda name: release_source / Path(name).name)
    monkeypatch.setattr(guard.importlib.metadata, 'distribution', lambda name: candidate)
    # Any SourceFileLoader entry would potentially trust a .pyc. It must not run.
    monkeypatch.setattr(importlib.util, 'spec_from_file_location', lambda *a, **kw: pytest.fail('source loader used'))
    poisoned = SimpleNamespace(refusal=lambda *a, **kw: None)
    monkeypatch.setitem(sys.modules, 'liteharness_deny_floor', poisoned)
    gate = guard.load_gate()
    assert gate._load_floor() is not poisoned
    assert gate.decide(payload(tool_input={'command': 'rm -rf ~'}, cwd=str(tmp_path)))['hookSpecificOutput']['permissionDecision'] == 'deny'


def test_hardlink_target_withholds_own_write(tmp_path, monkeypatch):
    root = tmp_path / 'worker'
    root.mkdir()
    (root / '.git').write_text('gitdir: /fixture')
    outside = tmp_path / 'outside.txt'
    outside.write_text('private')
    (root / 'inside.txt').hardlink_to(outside)
    monkeypatch.setattr(guard, 'assignment_record', lambda sid, home: {'cwd': str(root)})
    monkeypatch.setattr(guard, 'git_query', lambda args, cwd: 'work/seat\n' if args[0] == 'branch' else f'worktree {root.as_posix()}\nbranch refs/heads/work/seat\n\n')
    assert not guard.own_write(payload(tool_name='Edit', cwd=str(root), tool_input={'file_path': 'inside.txt'}), tmp_path)
    assert outside.read_text() == 'private'


def test_helper_cannot_resolve_from_target_or_relative_path(tmp_path, monkeypatch):
    suffix = '.exe' if os.name == 'nt' else ''
    (tmp_path / ('git' + suffix)).write_text('not executable')
    monkeypatch.setenv('PATH', '.' + os.pathsep + str(tmp_path))
    with pytest.raises(ValueError):
        guard.trusted_helper('git', tmp_path)


def test_git_query_removes_relocation_env(tmp_path, monkeypatch):
    monkeypatch.setenv('GIT_WORK_TREE', '/spoof')
    monkeypatch.setenv('GIT_CONFIG_COUNT', '1')
    monkeypatch.setattr(guard, 'trusted_helper', lambda name, forbidden: '/trusted/git')
    seen = {}
    def run(argv, **kwargs):
        seen.update(kwargs)
        assert argv == ['/trusted/git', 'branch', '--show-current']
        return SimpleNamespace(stdout='work/seat')
    monkeypatch.setattr(guard.subprocess, 'run', run)
    assert guard.git_query(['branch', '--show-current'], tmp_path) == 'work/seat'
    assert 'GIT_WORK_TREE' not in seen['env'] and 'GIT_CONFIG_COUNT' not in seen['env']
