import test from 'node:test'
import assert from 'node:assert/strict'
import { resolve, dirname } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'
import { readFileSync } from 'node:fs'

// Test the shipped modules themselves, also usable against the installed cache.
const plugin = process.env.LITEHARNESS_PLUGIN_ROOT || resolve(dirname(fileURLToPath(import.meta.url)), '..')
const { spawnDenial, fleetSnapshot } = await import(pathToFileURL(resolve(plugin, 'hooks/mods/fleet.mjs')))
const { register } = await import(pathToFileURL(resolve(plugin, 'hooks/register.mjs')))
const owned = 'C:/workspace/Task worktree'
const ALLOWED = ['sonnet', 'haiku', 'opus', 'claude-sonnet-5-5', 'claude-haiku-5-5', 'claude-opus-5-5',
  'claude-sonnet-5-5[1m]', 'claude-haiku-5-5[1m]', 'claude-opus-5-5[1m]']
const REFUSED = ['inherit', 'fable', 'gpt-5', 'claude-opus-4-6[1m]', 'Sonnet', '', 'sonnet ', 42]

for (const model of [undefined, ...ALLOWED]) {
  test(`Agent() runs for model ${model === undefined ? '(not supplied)' : model}`, () => {
    assert.equal(spawnDenial({ model, prompt: 'no tier line at all' }, owned), null)
    assert.equal(spawnDenial({ model, cwd: owned }, owned), null)
  })
}
test('model null (tool omitted it) runs; no Agent-Tier or Agent-Role line is required', () => {
  assert.equal(spawnDenial({ model: null }, owned), null)
  assert.equal(spawnDenial({ prompt: 'Agent-Tier: unknown\nAgent-Tier: worker' }, owned), null)
  assert.equal(spawnDenial({}, owned), null)
})
for (const model of REFUSED) {
  test(`non-Claude model ${JSON.stringify(model)} is still refused`, () => {
    const reason = spawnDenial({ model }, owned)
    assert.match(reason, /Agent\(\) model must be sonnet, haiku or opus/)
    assert.doesNotMatch(reason, /disabled by fleet policy|liteharness spawn --split/)
  })
}
test('a fork is judged by its parent model as well', () => {
  assert.equal(spawnDenial({ fork: true, parentModel: 'claude-opus-5-5[1m]' }, owned), null)
  assert.match(spawnDenial({ fork: true, parentModel: 'gpt-5' }, owned), /Agent\(\) model must be/)
})
test('cwd check: own directory passes, foreign, relative, dot-segment and unreadable cwd are refused', () => {
  assert.equal(spawnDenial({ model: 'sonnet', cwd: 'C:\\workspace\\TASK WORKTREE\\' }, owned), null)
  for (const cwd of ['C:/other', 'relative', 'C:/workspace/Task worktree/../x', 'C:/workspace/Task worktree\nBAD']) {
    assert.match(spawnDenial({ model: 'sonnet', cwd }, owned), /Agent\(\) cwd must be the session's own directory/)
  }
  for (const ownedCwd of [null, undefined, '', 'relative', 'C:/a/../b']) {
    assert.match(spawnDenial({ model: 'sonnet' }, ownedCwd), /Agent\(\) cwd must be/)
  }
  assert.match(spawnDenial(undefined, undefined), /Agent\(\) cwd must be/)
})
test('refusal text is bounded inert text; the requested cwd and prompt never appear in it', () => {
  const reason = spawnDenial({ model: 'sonnet\n\x1b' + 'x'.repeat(1000), prompt: 'LEAK-BRIEF' }, owned)
  assert.doesNotMatch(reason, /\n|\x1b|LEAK-BRIEF/)
  assert.ok(reason.length < 700)
  assert.doesNotMatch(spawnDenial({ model: 'sonnet', cwd: "C:/evil'; Invoke-Evil", prompt: 'LEAK-BRIEF' }, owned), /Invoke-Evil|LEAK-BRIEF/)
})
function spawnHandler() {
  const handlers = []
  register((event, ...args) => {
    if (event === 'agent.spawn') handlers.push(args.at(-1))
    return { catch() { return this } }
  }, {})
  assert.equal(handlers.length, 1)
  return handlers[0]
}
test('real register.mjs hook continues an allowed Agent() call without fs/process access', async () => {
  const handler = spawnHandler()
  for (const model of [undefined, ...ALLOWED]) {
    const event = { model, prompt: 'plain subagent brief' }
    let continued = null
    const unexpected = new Proxy({}, { get() { throw new Error('Forbidden boundary access') } })
    const result = await handler({ session: { cwd: async () => owned }, fs: unexpected, process: unexpected },
      event, e => { continued = e; return { spawned: true } })
    assert.deepEqual(result, { spawned: true })
    assert.equal(continued, event)
  }
})
test('real register.mjs hook denies a non-Claude model or foreign cwd and never continues', async () => {
  const handler = spawnHandler()
  for (const event of [{ model: 'fable' }, { model: 'inherit' }, { model: 'sonnet', cwd: 'C:/other' }]) {
    const result = await handler({ session: { cwd: async () => owned } }, event, () => assert.fail('must never continue'))
    assert.equal(typeof result.deny, 'string')
  }
})
test('real hook refuses (not crashes, not allows) if the host cwd cannot be read', async () => {
  const result = await spawnHandler()({ session: { cwd: async () => { throw new Error('offline') } } }, { model: 'sonnet' },
    () => assert.fail('must never continue'))
  assert.match(result.deny, /Agent\(\) cwd must be/)
})
test('shipped skill has no native Agent examples or default-headless dispatch', () => {
  const skill = readFileSync(resolve(plugin, 'skills/ls-liteharness/SKILL.md'), 'utf8')
  assert.doesNotMatch(skill, /Agent\(\{|ALWAYS headless PTY by default|Default is always headless|For Agent\(\) sub-agents/)
  assert.match(skill, /Fleet builders, scouts and critics always launch as visible/)
})
test('human-close and leader-resume safeguards survive launch-policy edits', () => {
  const skill = readFileSync(resolve(plugin, 'skills/ls-liteharness/SKILL.md'), 'utf8')
  for (const safeguard of ['liteharness pty-kill <agent-id>                      # close only when the human asks',
    '**Closing terminals:** Close a terminal only when the human explicitly asks.',
    'Only the leader resumes the same named seat after its process is gone:',
    '| "close that terminal" | `liteharness pty-kill <id>` when the human explicitly asks |']) assert.ok(skill.includes(safeguard))
})
test('withdrawn tool guard is not registered; actual fleet lifecycle still is', () => {
  const names = []
  register(name => { names.push(name); return { catch() { return this } } }, {})
  assert.ok(names.includes('agent.spawn') && names.includes('session.start'))
  assert.ok(!names.includes('tool.call') && !names.includes('tool.check'))
})
test('adjacent fleet snapshot validation and redaction stay functional', () => {
  const snapshot = fleetSnapshot(JSON.stringify({ schemaVersion: 1, sampledAt: 1, agents: [{ name: 'Seat\nName' }],
    tasks: [], warnings: [], agentCount: 1, taskCount: 0 }))
  assert.equal(snapshot.agents[0].name, 'Seat Name')
  assert.throws(() => fleetSnapshot('{}'), /Invalid fleet snapshot/)
})
