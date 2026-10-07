"""Strict pairing with immutable approved OSS fba17c7c40a83584283418c6499467a1a8805196.

The shared fixture validates 0.4.5 policy hashes against the published reference,
not its parent. No installation or live installed-package fallback occurs.
"""
import importlib.metadata
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location('guard_release', Path(__file__).resolve().parents[1] / 'hooks/mods/guard_backend.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def distribution(root, version='0.4.5'):
    return SimpleNamespace(version=version, locate_file=lambda name: root / Path(name).name)


def test_exact_release_source_loads_and_preserves_deny(release_source, monkeypatch):
    monkeypatch.setattr(guard.importlib.metadata, 'distribution', lambda name: distribution(release_source))
    gate = guard.load_gate()
    assert gate._load_floor().__file__ == str(release_source / 'deny_floor.py')
    result = gate.decide({'tool_name': 'Bash', 'tool_input': {'command': 'rm -rf ~'}, 'cwd': str(release_source)})
    assert result['hookSpecificOutput']['permissionDecision'] == 'deny'


@pytest.mark.parametrize('version', ['0.4.3', '0.4.4', '0.4.6', '0.4.5+unknown', 'unknown'])
def test_unreviewed_versions_refused_even_with_exact_source(release_source, monkeypatch, version):
    monkeypatch.setattr(guard.importlib.metadata, 'distribution', lambda name: distribution(release_source, version))
    with pytest.raises(ValueError, match='Unverified installed policy version'):
        guard.load_gate()


@pytest.mark.parametrize('name', ['deny_gate.py', 'deny_floor.py'])
def test_exact_version_does_not_accept_changed_source(release_source, monkeypatch, name):
    path = release_source / name
    path.write_bytes(path.read_bytes() + b'\n# changed source\n')
    monkeypatch.setattr(guard.importlib.metadata, 'distribution', lambda name: distribution(release_source))
    with pytest.raises(ValueError, match='Unverified installed policy source'):
        guard.load_gate()


def test_absent_distribution_refused(monkeypatch):
    def absent(name):
        raise importlib.metadata.PackageNotFoundError(name)
    monkeypatch.setattr(guard.importlib.metadata, 'distribution', absent)
    with pytest.raises(importlib.metadata.PackageNotFoundError):
        guard.load_gate()
