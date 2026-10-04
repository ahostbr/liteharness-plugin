"""CPU-only tests for public role glue; no installs, hooks or live registry."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("role_wrappers", ROOT / "scripts" / "generate_role_wrappers.py")
assert spec and spec.loader
wrappers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wrappers)


class RoleWrapperTests(unittest.TestCase):
    def test_all_shipped_methods_are_preserved_and_render_is_idempotent(self):
        count = 0
        for role, directory in wrappers.TIERS.items():
            preamble = (ROOT / "prompts" / "preambles" / f"{role}-preamble.md").read_text(encoding="utf-8")
            for path in (ROOT / "prompts" / "cognitive-architectures" / directory).glob("*.md"):
                with self.subTest(path=path):
                    raw = path.read_bytes()
                    pure = (ROOT / "prompts" / "cognitive-architectures" / "pure" / path.name).read_bytes()
                    rendered = wrappers.render_bundle(raw, pure, preamble, role)
                    self.assertEqual(wrappers.method_slice(raw, pure), wrappers.method_slice(rendered, pure))
                    self.assertEqual(rendered, wrappers.render_bundle(rendered, pure, preamble, role))
                    self.assertIn(b"METHOD FILE", rendered)
                    self.assertNotIn(b"your assigned polymath", rendered[:-len(wrappers.method_slice(rendered, pure))])
                    count += 1
        self.assertEqual(count, 42)

    def test_headingless_crlf_method_is_preserved(self):
        method = b'> A quote\r\n\r\n## The Kernel\r\n\r\nMethod body.\r\n'
        pure = b'<!-- pure -->\r\n\r\n' + method
        raw = b'> **METHOD FILE - VOID CLAUSE.**\r\n\r\n# POLYMATHIC EXAMPLE - Worker Mode\r\n\r\nOld role.\r\n\r\n' + method
        preamble = '<!-- role -->\n\n# WORKER ROLE — Worker Mode\n\nyour assigned polymath\n'
        rendered = wrappers.render_bundle(raw, pure, preamble, 'worker')
        self.assertTrue(rendered.endswith(method))
        self.assertIn(b'# POLYMATHIC EXAMPLE', rendered)
        self.assertIn(b'Example', rendered)

    def test_mismatched_method_and_missing_void_clause_fail_closed(self):
        with self.assertRaisesRegex(ValueError, 'does not match'):
            wrappers.method_slice(b'wrong body', b'<!-- pure -->\nmethod')
        with self.assertRaisesRegex(ValueError, 'void clause'):
            wrappers.render_bundle(b'method', b'<!-- pure -->\nmethod', '<!-- role -->\nrole', 'worker')

    def test_check_detects_stale_wrappers_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for role, tier in wrappers.TIERS.items():
                preamble_path = root / 'prompts' / 'preambles' / f'{role}-preamble.md'
                preamble_path.parent.mkdir(parents=True, exist_ok=True)
                preamble_path.write_text(f'<!-- role -->\n\n# {role.upper()} ROLE — {role.title()} Mode\n\nNew role.\n', encoding='utf-8')
                pure = root / 'prompts' / 'cognitive-architectures' / 'pure' / f'{role}.md'
                pure.parent.mkdir(parents=True, exist_ok=True)
                pure.write_bytes(b'<!-- pure -->\n\nmethod\n')
                bundle = root / 'prompts' / 'cognitive-architectures' / tier / f'{role}.md'
                bundle.parent.mkdir(parents=True, exist_ok=True)
                bundle.write_bytes(f'> **METHOD FILE - VOID CLAUSE.**\n\n# POLYMATHIC EXAMPLE — {role.title()} Mode\n\nOld role.\n\nmethod\n'.encode())
            before = {p: p.read_bytes() for p in root.rglob('*.md')}
            self.assertEqual(len(wrappers.generate(root, check=True)), 4)
            self.assertEqual(before, {p: p.read_bytes() for p in root.rglob('*.md')})
            self.assertEqual(len(wrappers.generate(root)), 4)
            self.assertEqual(wrappers.generate(root, check=True), [])
            self.assertEqual(wrappers.generate(root), [])


if __name__ == '__main__':
    unittest.main()
