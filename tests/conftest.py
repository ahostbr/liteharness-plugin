"""Shared corrected canonical-source fixture; no installed-package fallback."""
import hashlib
import os
import subprocess
from pathlib import Path

import pytest

RELEASE_COMMIT = 'd3ba9a8f59fb7b10279be54980f2385d193273d1'
RELEASE_PARENT = '1ea9c5ab9e293da09dceb78bf3ac51bfe5a74f4c'
EXPECTED = {
    'deny_gate.py': '15e98aea4ac8154d028aadc2e375e18892d202a95794b9fbe82ef59706d3cd79',
    'deny_floor.py': 'c60d0fee461c3a4bfcfae928c624e4c64ffbbefc7a5d9103851f03fb22704046',
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
