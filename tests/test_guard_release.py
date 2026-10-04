"""Strict same-release pin tests against the authorized immutable OSS Git source.

Set LITEHARNESS_TEST_POLICY_REPO to a local clone containing the corrected
93148ae69e8b8a28334f075c4b1fcdd7c1ce79ff freeze, parent
23ceb4368e6c1e4c47dfc3b70a0b4793ed86b82e. The shared conftest fixture checks
actual canonical bytes and hashes. No installation or wheel execution occurs.
"""
import importlib.metadata
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location('guard_release', Path(__file__).resolve().parents[1] / 'hooks/mods/guard_backend.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def distribution(root, version='0.4.4'):
    return SimpleNamespace(version=version, locate_file=lambda name: root / Path(name).name)


def test_exact_release_source_loads_and_preserves_deny(release_source, monkeypatch):
    monkeypatch.setattr(guard.importlib.metadata, 'distribution', lambda name: distribution(release_source))
    gate = guard.load_gate()
    assert gate._load_floor().__file__ == str(release_source / 'deny_floor.py')
    result = gate.decide({'tool_name': 'Bash', 'tool_input': {'command': 'rm -rf ~'}, 'cwd': str(release_source)})
    assert result['hookSpecificOutput']['permissionDecision'] == 'deny'


@pytest.mark.parametrize('version', ['0.4.3', '0.4.5', '0.4.4+unknown', 'unknown'])
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
