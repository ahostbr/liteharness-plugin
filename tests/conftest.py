"""Immutable exported 0.4.6 source fixture; no Git or installed-package fallback."""
import hashlib
import json
import os
from pathlib import Path

import pytest

RELEASE_COMMIT = '4b56fcc37daea090dbd950dcc297ebf795d5b130'
EXPECTED = {
    'deny_gate.py': '15e98aea4ac8154d028aadc2e375e18892d202a95794b9fbe82ef59706d3cd79',
    'deny_floor.py': 'c60d0fee461c3a4bfcfae928c624e4c64ffbbefc7a5d9103851f03fb22704046',
}


@pytest.fixture
def release_source(tmp_path):
    configured = os.environ.get('LITEHARNESS_TEST_POLICY_SOURCE')
    if not configured:
        pytest.skip('explicit immutable exported release-source artifact required')
    root = Path(configured)
    assert not (root / '.git').exists(), 'use a frozen source export, not a live checkout'
    receipt = json.loads((root / 'EXPORT-RECEIPT.json').read_text(encoding='utf-8'))
    assert receipt['source_commit'] == RELEASE_COMMIT
    metadata = (root / 'pyproject.toml').read_bytes()
    assert hashlib.sha256(metadata).hexdigest() == receipt['files']['pyproject.toml']['sha256_raw']
    assert b'version = "0.4.6"' in metadata
    for name, digest in EXPECTED.items():
        relative = 'liteharness/' + name
        source = (root / relative).read_bytes()
        assert hashlib.sha256(source).hexdigest() == receipt['files'][relative]['sha256_raw']
        assert hashlib.sha256(source.replace(b'\r\n', b'\n')).hexdigest() == digest
        (tmp_path / name).write_bytes(source)
    return tmp_path
