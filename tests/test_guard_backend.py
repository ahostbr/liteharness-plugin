"""Focused Mods bridge tests: no submitted command is ever executed."""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

BACKEND = Path(__file__).resolve().parents[1] / 'hooks/mods/guard_backend.py'
spec = importlib.util.spec_from_file_location('guard_backend', BACKEND)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def payload(command='git status', **changes):
    return {'protocol': 1, 'kind': 'call', 'session_id': 'seat', 'cwd': str(BACKEND.parent),
            'tool_name': 'Bash', 'tool_input': {'command': command}, **changes}


def gate(reason=None):
    return SimpleNamespace(decide=lambda p: None if reason is None else {
        'hookSpecificOutput': {'permissionDecision': 'deny', 'permissionDecisionReason': reason}})


def test_floor_precedes_census_rewrite_and_ownership():
    def forbidden(*args):
        raise AssertionError('side effect before floor')
    result = guard.decide(payload('liteharness send peer "`code`"'), gate('floor'),
                          census=forbidden, writer=forbidden, ownership=forbidden)
    assert result == guard.reply('floor')


@pytest.mark.parametrize('command', ['bun run test', 'npx vitest run', 'python -m pytest',
                                    'npm test', 'playwright test', 'cargo test'])
def test_full_suites_refused(command, monkeypatch):
    monkeypatch.delenv('LITEHARNESS_ALLOW_FULL_SUITE', raising=False)
    assert 'no full' in guard.suite_refusal(command, lambda: [])


@pytest.mark.parametrize('command', ['python -m pytest tests/test_guard_backend.py',
                                    'npx vitest run tests/guard.test.ts', 'git status',
                                    'echo "vitest"', 'git commit -m "pytest"'])
def test_scoped_or_prose(command, monkeypatch):
    monkeypatch.delenv('LITEHARNESS_ALLOW_FULL_SUITE', raising=False)
    assert guard.suite_refusal(command, lambda: []) is None


def test_runner_collision_and_failure(monkeypatch):
    monkeypatch.delenv('LITEHARNESS_ALLOW_FULL_SUITE', raising=False)
    assert 'another' in guard.suite_refusal('npx vitest run tests/guard.test.ts', lambda: ['123'])
    def broken():
        raise TimeoutError('census failed')
    with pytest.raises(TimeoutError):
        guard.suite_refusal('npx vitest run tests/guard.test.ts', broken)


def test_escape_hatch_only_suite_not_floor(monkeypatch):
    monkeypatch.setenv('LITEHARNESS_ALLOW_FULL_SUITE', '1')
    assert guard.suite_refusal('npm test', lambda: ['123']) is None
    assert guard.decide(payload('npm test'), gate('floor'))['deny'] == 'floor'


@pytest.mark.parametrize('command,body', [
    ('liteharness send peer "literal `code` $VALUE" --from seat', 'literal `code` $VALUE'),
    ('lst run inbox action=send to=peer from_id=seat message="literal `code` $VALUE"', 'literal `code` $VALUE'),
])
def test_lossless_rewrite_plan(command, body):
    plan = guard.inbox_plan(command)
    assert plan[0] == body
    assert '--from' in plan[1] + plan[2]
    writes = []
    result = guard.decide(payload(command), gate(), writer=lambda p: writes.append(p) or 'safe invocation')
    assert result['command'] == 'safe invocation'
    assert writes == [plan]
    assert guard.decide(payload(command, kind='check'), gate())['deny']


@pytest.mark.parametrize('command', [
    'liteharness send peer "`code`"; echo extra',
    'liteharness send peer "`code`" extra',
    'lst run inbox action=send to=peer message="`code`" payload={}',
    'liteharness send peer "`code`" --body-file existing.txt',
])
def test_unsupported_inbox_fails_closed(command):
    with pytest.raises(ValueError):
        guard.decide(payload(command), gate())


def test_actual_body_file_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(guard.Path, 'home', lambda: tmp_path)
    plan = guard.inbox_plan('liteharness send peer "`code` café $VALUE"')
    rewritten = guard.save_body(plan)
    stored = next((tmp_path / '.liteharness/mods/inbox-bodies').glob('*.txt'))
    assert stored.read_text(encoding='utf-8') == '`code` café $VALUE'
    assert '--body-file' in rewritten and '`code`' not in rewritten


def test_forced_remove_scans_and_never_executes(tmp_path, monkeypatch):
    target = tmp_path / 'tree'
    target.mkdir()
    (target / 'ordinary.txt').write_text('safe')
    command = 'git worktree remove --force tree'
    assert guard.junction_refusal(command, tmp_path) is None
    original = guard.is_reparse
    monkeypatch.setattr(guard, 'is_reparse', lambda p: p.name == 'ordinary.txt' or original(p))
    assert 'contains' in guard.junction_refusal(command, tmp_path)
    assert target.exists()


def test_forced_remove_unsupported_alias_denied(tmp_path):
    with pytest.raises(ValueError):
        guard.junction_refusal('echo x && git worktree remove --force tree', tmp_path)


def test_own_write_containment_and_git_membership(tmp_path, monkeypatch):
    root = tmp_path / 'worker'
    root.mkdir()
    (root / '.git').write_text('gitdir: /fixture')
    monkeypatch.setattr(guard, 'assignment_record', lambda sid, home: {'cwd': str(root)})
    def git(argv, cwd):
        return 'work/seat\n' if argv[0] == 'branch' else f'worktree {root.as_posix()}\nbranch refs/heads/work/seat\n\n'
    monkeypatch.setattr(guard, 'git_query', git)
    p = payload(tool_name='Write', cwd=str(root), tool_input={'file_path': 'src/new.py'})
    assert guard.own_write(p, tmp_path)
    for target in ['../outside.py', '.git/config', 'jobs.json::$DATA', 'trailing.', '.claude/settings.json']:
        assert not guard.own_write({**p, 'tool_input': {'file_path': target}}, tmp_path)
    monkeypatch.setattr(guard, 'assignment_record', lambda sid, home: None)
    assert not guard.own_write(p, tmp_path)


def test_ownership_absent_preserves_normal_path():
    def absent(p):
        raise FileNotFoundError()
    result = guard.decide(payload(tool_name='Write', tool_input={'file_path': 'safe.py'}), gate(), ownership=absent)
    assert result == guard.reply()


@pytest.mark.parametrize('raw', ['{}', '{broken', json.dumps(payload(tool_input=[])),
                                json.dumps(payload(tool_input={'command': 42}))])
def test_cli_protocol_failures_are_deny_not_crash(raw):
    result = subprocess.run([sys.executable, str(BACKEND)], input=raw, text=True,
                            capture_output=True, timeout=10)
    assert result.returncode == 0
    assert json.loads(result.stdout)['deny']


def test_authoritative_floor_parity_for_examples(tmp_path, monkeypatch, release_source):
    # Actual immutable corrected canonical bytes, never an old install relabeled.
    candidate = SimpleNamespace(version='0.4.4',
                                locate_file=lambda name: release_source / Path(name).name)
    monkeypatch.setattr(guard.importlib.metadata, 'distribution', lambda name: candidate)
    real = guard.load_gate()
    for command in ['git status', 'rm -rf ~', 'echo hello', 'git worktree remove --force missing']:
        p = payload(command, cwd=str(tmp_path))
        existing = real.decide(p)
        result = guard.decide(p, real)
        if existing:
            assert result['deny'] == existing['hookSpecificOutput']['permissionDecisionReason']
        elif command.startswith('git worktree remove'):
            assert result['deny']
        else:
            assert result['deny'] is None
