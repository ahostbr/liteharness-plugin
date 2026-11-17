import test from 'node:test'
import assert from 'node:assert/strict'
import { resolve, dirname } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'
import { readFileSync } from 'node:fs'

// Test the shipped modules themselves, also usable against the installed cache.
const plugin = process.env.LITEHARNESS_PLUGIN_ROOT || resolve(dirname(fileURLToPath(import.meta.url)), '..')
const fleet = await import(pathToFileURL(resolve(plugin, 'hooks/mods/fleet.mjs')))
const { register } = await import(pathToFileURL(resolve(plugin, 'hooks/register.mjs')))
// Claude Code refuses Code Mode while any plugin hook registers one of these events.
const CODE_MODE_BLOCKERS = ['tool.call', 'tool.check', 'tool.judge', 'tool.run', 'agent.offer', 'agent.spawn', 'session.send',
  ...['PreToolUse', 'PermissionRequest', 'PermissionDenied', 'PostToolUse', 'PostToolUseFailure', 'TaskCreated', 'TaskCompleted',
    'Elicitation', 'ElicitationResult', 'WorktreeCreate'].map(name => 'classic.' + name)]

function registeredNames() {
  const names = []
  register(name => { names.push(name); return { catch() { return this } } }, {})
  return names
}
test('native Agent() calls are not hooked: no agent.spawn guard and no other Code Mode blocker is registered', () => {
  const names = registeredNames()
  assert.ok(names.includes('session.start'), 'fleet lifecycle still registers')
  for (const blocker of CODE_MODE_BLOCKERS) assert.ok(!names.includes(blocker), blocker)
  assert.equal(fleet.spawnDenial, undefined)
})
test('shipped skill has no native Agent examples or default-headless dispatch', () => {
  const skill = readFileSync(resolve(plugin, 'skills/ls-liteharness/SKILL.md'), 'utf8')
  assert.doesNotMatch(skill, /Agent\(\{|ALWAYS headless PTY by default|Default is always headless|For Agent\(\) sub-agents/)
  assert.match(skill, /Fleet builders, scouts and critics always launch as visible/)
})
test('the leader-resume safeguard survives launch-policy edits; the dropped close rule stays dropped', () => {
  const skill = readFileSync(resolve(plugin, 'skills/ls-liteharness/SKILL.md'), 'utf8')
  assert.ok(skill.includes('Only the leader resumes the same named seat after its process is gone:'))
  // The owner dropped "close a terminal only when the human asks" everywhere (2026-11-12). The command stays documented.
  assert.ok(skill.includes('liteharness pty-kill <agent-id>'))
  for (const dropped of ['only when the human asks', 'when the human explicitly asks', '**Closing terminals:**']) {
    assert.ok(!skill.includes(dropped), dropped)
  }
})
test('adjacent fleet snapshot validation and redaction stay functional', () => {
  const snapshot = fleet.fleetSnapshot(JSON.stringify({ schemaVersion: 1, sampledAt: 1, agents: [{ name: 'Seat\nName' }],
    tasks: [], warnings: [], agentCount: 1, taskCount: 0 }))
  assert.equal(snapshot.agents[0].name, 'Seat Name')
  assert.throws(() => fleet.fleetSnapshot('{}'), /Invalid fleet snapshot/)
})
