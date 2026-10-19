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
// The host's Agent tool passes its own enum (sonnet|opus|haiku|fable) or nothing; the guard never judges a model.
const MODELS = ['sonnet', 'haiku', 'opus', 'fable', 'claude-sonnet-5-5', 'claude-haiku-5-5', 'claude-opus-5-5',
  'claude-sonnet-5-5[1m]', 'claude-haiku-5-5[1m]', 'claude-opus-5-5[1m]', 'claude-fable-5-1', 'claude-fable-5-1[1m]',
  'inherit', 'gpt-5', 'Sonnet', '', 42]

for (const model of [undefined, null, ...MODELS]) {
  test(`Agent() runs for model ${model === undefined ? '(not supplied)' : JSON.stringify(model)}`, () => {
    assert.equal(spawnDenial({ model, prompt: 'no tier line at all' }, owned), null)
    assert.equal(spawnDenial({ model, cwd: owned }, owned), null)
    assert.equal(spawnDenial({ model, fork: true, parentModel: 'whatever' }, owned), null)
  })
}
test('no Agent-Tier or Agent-Role line is required, whatever the brief says', () => {
  assert.equal(spawnDenial({ prompt: 'Agent-Tier: unknown\nAgent-Tier: worker' }, owned), null)
  assert.equal(spawnDenial({}, owned), null)
})
test('cwd check: the session directory or anything inside it passes (isolation:"worktree" lives under the repo)', () => {
  assert.equal(spawnDenial({ cwd: 'C:\\workspace\\TASK WORKTREE\\' }, owned), null)
  assert.equal(spawnDenial({ cwd: owned + '/.claude/worktrees/agent-x' }, owned), null)
  assert.equal(spawnDenial({ cwd: 'C:\\workspace\\task worktree\\.claude\\worktrees\\Agent-X' }, owned), null)
  assert.equal(spawnDenial({ cwd: '/repo/.claude/worktrees/x' }, '/repo'), null)
  assert.equal(spawnDenial({ cwd: '/repo/.claude/worktrees/x' }, '/repo/'), null)
})
test('cwd check: foreign, sibling-prefix, parent, relative, dot-segment and unreadable cwd are refused', () => {
  for (const cwd of ['C:/other', 'C:/workspace', 'C:/workspace/Task worktree-evil', 'C:/workspace/Task worktree-evil/x',
    'C:/workspace/Task worktreeX', 'relative', 'C:/workspace/Task worktree/../x', 'C:/workspace/Task worktree/x/../../y',
    'C:/workspace/Task worktree\nBAD']) {
    assert.match(spawnDenial({ cwd }, owned), /Agent\(\) cwd must be the session's own directory or inside it/, cwd)
  }
  assert.match(spawnDenial({ cwd: '/repo-evil' }, '/repo'), /cwd must be/)
  assert.match(spawnDenial({ cwd: '/repo2/x' }, '/repo'), /cwd must be/)
  assert.match(spawnDenial({ cwd: '/Repo/x' }, '/repo'), /cwd must be/, 'POSIX paths are case-sensitive')
  for (const ownedCwd of [null, undefined, '', 'relative', 'C:/a/../b']) {
    assert.match(spawnDenial({}, ownedCwd), /Agent\(\) cwd must be/)
  }
  assert.match(spawnDenial(undefined, undefined), /Agent\(\) cwd must be/)
})
test('refusal text is inert: the requested cwd and the brief never appear in it', () => {
  const reason = spawnDenial({ cwd: "C:/evil'; Invoke-Evil\n\x1b", prompt: 'LEAK-BRIEF', model: 'sonnet\n\x1b' + 'x'.repeat(1000) }, owned)
  assert.doesNotMatch(reason, /Invoke-Evil|LEAK-BRIEF|\n|\x1b/)
  assert.ok(reason.length < 200)
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
  for (const model of [undefined, ...MODELS]) {
    const event = { model, prompt: 'plain subagent brief' }
    let continued = null
    const unexpected = new Proxy({}, { get() { throw new Error('Forbidden boundary access') } })
    const result = await handler({ session: { cwd: async () => owned }, fs: unexpected, process: unexpected },
      event, e => { continued = e; return { spawned: true } })
    assert.deepEqual(result, { spawned: true })
    assert.equal(continued, event)
  }
})
test('real register.mjs hook continues a worktree inside the session and denies a foreign or sibling-prefix cwd', async () => {
  const handler = spawnHandler()
  const inside = { model: 'sonnet', cwd: owned + '/.claude/worktrees/agent-x' }
  assert.equal(await handler({ session: { cwd: async () => owned } }, inside, e => e), inside)
  for (const event of [{ model: 'sonnet', cwd: 'C:/other' }, { model: 'fable', cwd: owned + '-evil' }]) {
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
