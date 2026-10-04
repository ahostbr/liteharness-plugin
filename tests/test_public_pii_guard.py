"""Guard controls use encoded private tokens, never republish the denylist."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / 'scripts/check_pii.py'
spec = importlib.util.spec_from_file_location('public_guard', GUARD)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
ACTOR = bytes.fromhex('73656e74696e656c').decode()
HUMAN = bytes.fromhex('7279616e').decode()
AUTHOR = HUMAN.title() + ' Devlin'


class PublicGuardTests(unittest.TestCase):
    def test_actor_prose_code_path_case_and_binary_are_findings(self):
        for text in ('ask ' + ACTOR, 'actor = "' + ACTOR + '"', ACTOR.upper(), 'human=' + HUMAN):
            self.assertTrue(guard.scan_text(text), text)
        self.assertTrue(guard.scan_file('payload.bin', b'\0' + ACTOR.encode()))
        self.assertTrue(guard.scan_text('C:' + '/Projects/private'))
        self.assertTrue(guard.scan_text('C:' + '\\Users\\RealPerson\\notes'))
        self.assertFalse(guard.scan_text('C:' + '/Users/TestUser/notes'))

    def test_legal_file_field_and_exact_author_not_blanket(self):
        self.assertFalse(guard.scan_file('.codex-plugin/plugin.json', json.dumps({'author': {'name': AUTHOR}}).encode()))
        self.assertTrue(guard.scan_file('.codex-plugin/plugin.json', json.dumps({'actor': AUTHOR}).encode()))
        self.assertTrue(guard.scan_file('.codex-plugin/plugin.json', json.dumps({'author': {'name': ACTOR}}).encode()))
        self.assertTrue(guard.scan_file('other.json', json.dumps({'author': {'name': AUTHOR}}).encode()))
        self.assertFalse(guard.scan_file('LICENSE', ('Copyright (c) 2026 ' + AUTHOR).encode()))
        self.assertTrue(guard.scan_file('LICENSE', ('Copyright (c) 2026 ' + AUTHOR + '\nAsk ' + ACTOR).encode()))
        self.assertTrue(guard.scan_file('notes.md', ('Copyright (c) 2026 ' + AUTHOR).encode()))
        attribution = 'authors = [{ name = "' + AUTHOR + '", email = "' + HUMAN + '@litesuite.dev" }]\n'
        self.assertTrue(guard.scan_file('pyproject.toml', attribution.encode()))
        self.assertFalse(guard.scan_file('pyproject.toml', ('[project]\n' + attribution).encode()))

    def test_duplicate_keys_rejected_even_if_last_value_is_clean(self):
        payloads = (
            '{"actor":' + json.dumps(ACTOR) + ',"actor":"public"}',
            '{"author":{"name":' + json.dumps(ACTOR) + ',"name":' + json.dumps(AUTHOR) + '}}',
            '{"author":{"name":' + json.dumps(AUTHOR) + '},"author":{"name":"public"}}',
            '{"clean":1,"clean":2}',
        )
        for path in guard.LEGAL_FIELDS:
            for payload in payloads:
                with self.subTest(path=path, payload=payload):
                    hits = guard.scan_file(path, payload.encode())
                    self.assertIn((1, 'invalid or duplicate-key legal metadata'), hits)

    def test_numeric_scalars_and_raw_number_residue_are_scanned(self):
        # Synthetic private identifier tests numeric coverage without publishing
        # a real identifier. Exponent spelling also proves raw bytes are kept.
        from unittest.mock import patch
        identifier = '123456789'
        with patch.dict(guard.DENIED, {guard.digest(identifier): 'private numeric identifier'}):
            for path in guard.LEGAL_FIELDS:
                for payload in ('{"id":' + identifier + '}',
                                '{"items":[true,null,' + identifier + ']}',
                                '{"id":' + identifier + 'e0}'):
                    with self.subTest(path=path, payload=payload):
                        self.assertIn((1, 'private numeric identifier'), guard.scan_file(path, payload.encode()))

    def test_exact_legal_spans_only_and_original_line_numbers(self):
        payload = '{\n"author":{"name":' + json.dumps(AUTHOR) + '},\n"actor":' + json.dumps(ACTOR) + '\n}'
        self.assertIn((3, 'private orchestrator identity'), guard.scan_file('.codex-plugin/plugin.json', payload.encode()))
        self.assertTrue(guard.scan_file('.codex-plugin/plugin.json', json.dumps({'author.name': AUTHOR}).encode()))
        self.assertTrue(guard.scan_file('.codex-plugin/plugin.json', json.dumps({'author': {'name': AUTHOR + ' extra'}}).encode()))
        # Every non-approved raw string remains; escaped strings are also decoded.
        escaped = ''.join('\\u%04x' % ord(char) for char in ACTOR)
        self.assertTrue(guard.scan_file('.codex-plugin/plugin.json', ('{"actor":"' + escaped + '"}').encode()))
        self.assertTrue(guard.scan_file('.codex-plugin/plugin.json', ('{"' + escaped + '":true}').encode()))
        self.assertTrue(guard.scan_file('.codex-plugin/plugin.json', b'{"clean":'))

    def test_all_approved_legal_fields_and_nonstring_controls(self):
        payloads = {
            '.claude-plugin/plugin.json': {'author': {'name': AUTHOR}, 'clean': [False, None, 42]},
            '.codex-plugin/plugin.json': {'author': {'name': AUTHOR}, 'interface': {'developerName': AUTHOR}},
            '.claude-plugin/marketplace.json': {'owner': {'name': AUTHOR}, 'plugins': [{'author': {'name': AUTHOR}}]},
        }
        for path, payload in payloads.items():
            with self.subTest(path=path):
                self.assertFalse(guard.scan_file(path, json.dumps(payload).encode()))

    def test_stable_identifiers_do_not_exempt_private_actors(self):
        self.assertFalse(guard.scan_text('name: ls-' + ACTOR))
        self.assertTrue(guard.scan_text('name: ls-' + ACTOR + '-private'))
        self.assertFalse(guard.scan_text('/v1/' + ACTOR + '/assistant-message'))
        self.assertTrue(guard.scan_text('actor=' + ACTOR))
        handle = bytes.fromhex('61686f73746272').decode()
        self.assertFalse(guard.scan_text('https://github.com/' + handle + '/liteharness'))
        self.assertTrue(guard.scan_text('https://github.com/' + handle + '/unknown-private-repo'))
        self.assertTrue(guard.scan_text('author=' + handle))

    def test_index_bytes_not_worktree_and_zero_or_unknown_input_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(['git', 'init', '-q', str(root)], check=True, capture_output=True)
            def run(*args):
                return subprocess.run([sys.executable, str(GUARD), *args], cwd=root, capture_output=True, text=True)
            self.assertNotEqual(run().returncode, 0)
            self.assertNotEqual(run('--alll').returncode, 0)
            path = root / 'notes.md'
            path.write_text('Ask ' + ACTOR, encoding='utf-8')
            subprocess.run(['git', 'add', 'notes.md'], cwd=root, check=True)
            path.write_text('Clean public prose', encoding='utf-8')
            self.assertEqual(run().returncode, 1)
            subprocess.run(['git', 'add', 'notes.md'], cwd=root, check=True)
            path.write_text('Ask ' + ACTOR, encoding='utf-8')
            self.assertEqual(run().returncode, 0)
            self.assertEqual(run('--all').returncode, 1)


if __name__ == '__main__':
    unittest.main()
