"""Paired plugin onboarding against the explicitly selected owned Python preview.

Fixtures simulate confirmed interview answers, not live interactive host proof.
No registration, watcher, bridge, model, or installed-home actions are executed.
"""
import importlib.util
import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PYTHON_ROOT = Path(os.environ['T0322_PAIRED_OSS_ROOT'])
spec = importlib.util.spec_from_file_location('paired_prompts', PYTHON_ROOT / 'liteharness/prompts.py')
prompts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prompts)


class FirstRunIdentityTests(unittest.TestCase):
    def test_entry_asks_and_records_chosen_name_for_both_hosts(self):
        skill = (ROOT / 'skills/ls-init-liteharness/SKILL.md').read_text(encoding='utf-8')
        entry = skill.split('### Phase 1:', 1)[0]
        self.assertIn('ask what to **name the orchestrator**', entry)
        self.assertIn('Both Claude and Codex follow this ask-and-record step', entry)
        self.assertIn('orchestrator_name: <chosen agent name>', entry)
        self.assertIn('identity_cli: <normalized active CLI>', entry)
        self.assertIn('Keep existing profile content', entry)
        self.assertIn('stop with', entry)
        self.assertNotRegex(skill, r"resolve_orchestrator_target as t;[^\n]*cli=")
        self.assertIn("verify_orchestrator_identity as v; ok,d = v('<NAME>', cli='<ACTIVE-CLI>')", skill)
        self.assertIn('Codex: `$<slug>`', skill)
        bootstrap = (ROOT / 'skills/ls-sentinel/SKILL.md').read_text(encoding='utf-8')
        self.assertNotIn('--cli claude-code', bootstrap)
        self.assertIn('--cli <active-cli>', bootstrap)
        self.assertIn('Record the chosen orchestrator name and active CLI', bootstrap)

    def test_confirmed_answers_persist_and_load_with_actual_paired_api(self):
        for cli, directory in [('claude-code', '.claude'), ('codex-cli', '.agents')]:
            with self.subTest(cli=cli), tempfile.TemporaryDirectory() as temporary:
                home = Path(temporary)
                environment = {'HOME': str(home), 'USERPROFILE': str(home),
                               'LITEHARNESS_USER_PROMPTS_DIR': str(home / '.liteharness/prompts'),
                               'LITEHARNESS_PROMPTS_DIR': str(ROOT / 'prompts')}
                with patch.object(Path, 'home', return_value=home), patch.dict(os.environ, environment):
                    # Confirmed first-run answer, deliberately distinct from human.
                    name = 'Harbor Guide'
                    normalized = prompts.identity_cli(cli)
                    profile = home / '.liteharness/profile.md'
                    profile.parent.mkdir(parents=True)
                    profile.write_text('user_trunk: preserve this answer\n', encoding='utf-8')
                    entry = (ROOT / 'skills/ls-init-liteharness/SKILL.md').read_text(encoding='utf-8').split('<!-- FIRST-RUN-IDENTITY:START -->')[1].split('<!-- FIRST-RUN-IDENTITY:END -->')[0]
                    code = entry.split('```python', 1)[1].rsplit('```', 1)[0]
                    exec(compile(code, 'shipped-first-run-contract', 'exec'), {'NAME': name, 'ACTIVE_CLI': cli, 'PROJECT_ROOT': home})
                    recorded = profile.read_text(encoding='utf-8')
                    self.assertIn('user_trunk: preserve this answer', recorded)
                    self.assertIn('orchestrator_name: Harbor Guide', recorded)
                    self.assertIn(f'identity_cli: {cli}', recorded)
                    target, _ = prompts.resolve_orchestrator_target(name)
                    template = (ROOT / 'prompts/cognitive-architectures/orchestrator/default.md').read_text(encoding='utf-8')
                    values = {slot[2:-2]: 'Confirmed user answer' for slot in prompts.unfilled_slots(prompts.strip_template_scaffolding(template))}
                    values.update(ORCHESTRATOR_NAME=name, TITLE=name)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(prompts.render_architecture(template, values), encoding='utf-8')
                    skill_path, _ = prompts.resolve_skill_target(name, cli=cli)
                    self.assertEqual(skill_path, home / directory / 'skills/harbor-guide/SKILL.md')
                    skill_template = (ROOT / 'skills/ls-init-liteharness/skill-template.md').read_text(encoding='utf-8')
                    skill = prompts.render_architecture(skill_template, {'ORCHESTRATOR_NAME': name, 'ORCHESTRATOR_SLUG': 'harbor-guide', 'CLI_NAME': normalized})
                    skill_path.parent.mkdir(parents=True)
                    skill_path.write_text(skill, encoding='utf-8')
                    self.assertEqual(prompts.resolve_cognitive_file(name, 'orchestrator'), target)
                    self.assertTrue(prompts.verify_orchestrator_identity(name, cli=cli)[0])
                    self.assertIn(f'--cli {cli}', skill)
                    self.assertIn('--name "Harbor Guide"', skill)
                    self.assertIn('harbor-guide.md', skill)
                    self.assertFalse(prompts.verify_orchestrator_identity(name, cli='codex-cli' if cli == 'claude-code' else 'claude-code')[0])

    def test_shipped_entry_preserves_choices_but_old_api_fails_closed(self):
        from types import SimpleNamespace
        import sys
        entry = (ROOT / 'skills/ls-init-liteharness/SKILL.md').read_text(encoding='utf-8').split('<!-- FIRST-RUN-IDENTITY:START -->')[1].split('<!-- FIRST-RUN-IDENTITY:END -->')[0]
        code = entry.split('```python', 1)[1].rsplit('```', 1)[0]
        old_api = SimpleNamespace(resolve_skill_target=lambda name: None, verify_orchestrator_identity=lambda name: None)
        package = SimpleNamespace(prompts=old_api)
        with tempfile.TemporaryDirectory() as temporary, patch.dict(sys.modules, {'liteharness': package}):
            root = Path(temporary)
            profile = root / '.liteharness/profile.md'
            profile.parent.mkdir()
            profile.write_text('user_trunk: keep\norchestrator_name: old\nidentity_cli: old\n', encoding='utf-8')
            with self.assertRaisesRegex(RuntimeError, 'too old'):
                exec(compile(code, 'shipped-first-run-contract', 'exec'), {'NAME': 'Harbor Guide', 'ACTIVE_CLI': 'codex-cli', 'PROJECT_ROOT': root})
            recorded = profile.read_text(encoding='utf-8')
            self.assertIn('user_trunk: keep', recorded)
            self.assertIn('orchestrator_name: Harbor Guide', recorded)
            self.assertIn('identity_cli: codex-cli', recorded)
            self.assertNotIn(': old', recorded)
            self.assertEqual(len(list(root.rglob('*SKILL.md'))), 0)

    def test_all_four_versions_and_neutral_touched_text(self):
        spec = importlib.util.spec_from_file_location('versions', ROOT / 'scripts/check_version_consistency.py')
        versions = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(versions)
        with patch.object(versions, '_git', return_value='\n'.join(['.claude-plugin/plugin.json', '.claude-plugin/marketplace.json', '.codex-plugin/plugin.json'])), patch.object(versions, '_read', side_effect=lambda path, ref: (ROOT / path).read_text(encoding='utf-8')):
            sites = versions.collect(None)
        self.assertEqual(len(sites), 4)
        self.assertEqual({value for _, _, value in sites}, {'1.0.19'})
        cache = (ROOT / 'docs/claude-cache-band.md').read_text(encoding='utf-8')
        self.assertIn('**1.0.19** is the local integration candidate', cache)
        self.assertNotIn('remains unchanged at all four', cache)
        actor = bytes.fromhex('73656e74696e656c').decode()
        human = bytes.fromhex('7279616e').decode()
        for path in ('docs/claude-cache-band.md', 'docs/mods-fleet.md', 'skills/ls-local-batch-agent/run_batch.py'):
            text = (ROOT / path).read_text(encoding='utf-8')
            self.assertNotRegex(text, r'(?i)\b(?:' + actor + '|' + human + r')\b')


if __name__ == '__main__':
    unittest.main()
