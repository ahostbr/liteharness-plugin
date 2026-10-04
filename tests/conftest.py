"""Shared corrected canonical-source fixture; no installed-package fallback."""
import hashlib
import os
import subprocess
from pathlib import Path

import pytest

RELEASE_COMMIT = '21369da5521b8d7888ca9507da7eca5455ef2a8f'
RELEASE_PARENT = '351dd25383461ee0d118d5a4d241e35412ac7ecb'
EXPECTED = {
    'deny_gate.py': '15e98aea4ac8154d028aadc2e375e18892d202a95794b9fbe82ef59706d3cd79',
    'deny_floor.py': '7703738d2d6b1919a440e45543b4016e099eb8b136ef939a7014cfe07315d60e',
}


@pytest.fixture
def release_source(tmp_path):
    configured = os.environ.get('LITEHARNESS_TEST_POLICY_REPO')
    if not configured:
        pytest.skip('explicit local immutable release-source repo required')
    repo = Path(configured)

    def git(*args):
        return subprocess.run(['git', *args], cwd=repo, capture_output=True, check=True).stdout

    assert git('rev-parse', RELEASE_COMMIT + '^').decode().strip() == RELEASE_PARENT
    assert b'version = "0.4.4"' in git('show', RELEASE_COMMIT + ':pyproject.toml')
    for name, digest in EXPECTED.items():
        source = git('show', RELEASE_COMMIT + ':liteharness/' + name)
        assert source == git('show', RELEASE_PARENT + ':liteharness/' + name)
        assert hashlib.sha256(source.replace(b'\r\n', b'\n')).hexdigest() == digest
        (tmp_path / name).write_bytes(source)
    return tmp_path
