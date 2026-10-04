"""Shared corrected canonical-source fixture; no installed-package fallback."""
import hashlib
import os
import subprocess
from pathlib import Path

import pytest

RELEASE_COMMIT = '93148ae69e8b8a28334f075c4b1fcdd7c1ce79ff'
RELEASE_PARENT = '23ceb4368e6c1e4c47dfc3b70a0b4793ed86b82e'
EXPECTED = {
    'deny_gate.py': '15e98aea4ac8154d028aadc2e375e18892d202a95794b9fbe82ef59706d3cd79',
    'deny_floor.py': '063f2197eaca6ab765a7dbf384db76a6ab33b9175b70f611645f9c510f259f47',
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
