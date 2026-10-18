import test from 'node:test'
import assert from 'node:assert/strict'
import { resolve, dirname } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'
import { mkdtempSync, writeFileSync, readFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { execFileSync } from 'node:child_process'

// Test the shipped modules themselves, also usable against the installed cache.
const plugin = process.env.LITEHARNESS_PLUGIN_ROOT || resolve(dirname(fileURLToPath(import.meta.url)), '..')
const { spawnDenial, fleetSnapshot } = await import(pathToFileURL(resolve(plugin, 'hooks/mods/fleet.mjs')))
const { register } = await import(pathToFileURL(resolve(plugin, 'hooks/register.mjs')))
const owned = 'C:/workspace/Task worktree'
const complete = { prompt: 'Agent-Tier: thinker\nTask-id: T0596', cwd: owned }
function denied(event, cwd = owned) {
  const reason = spawnDenial(event, cwd)
  assert.equal(typeof reason, 'string')
  assert.match(reason, /Agent\(\) subagents are disabled by fleet policy/)
  assert.match(reason, /do not retry Agent\(\)/)
  assert.match(reason, /liteharness spawn --split --cli claude --tier scout/)
  assert.match(reason, /--model 'claude-sonnet-5-5\[1m\]'/)
  assert.match(reason, /--tier builder --model 'claude-haiku-5-5\[1m\]'/)
  assert.doesNotMatch(reason, /requires exactly one Agent-Tier|aliases and inherit are refused/)
  return reason
}

for (const model of [undefined, 'inherit', 'sonnet', 'opus', 'haiku', 'fable',
  'claude-opus-5-5[1m]', 'claude-opus-5[1m]', 'claude-opus-4-8[1m]', 'claude-opus-4-6[1m]',
  'claude-sonnet-5-5[1m]', 'claude-haiku-5-5[1m]']) {
  test(`closed for tool alias or full model ${model}`, () => {
    const reason = denied({ ...complete, model })
    assert.ok(reason.endsWith('Observed agent.spawn model: ' + (model === undefined ? '(not supplied)' : JSON.stringify(model)) + '.'))
  })
}
test('missing, malformed, forked and forged brief metadata cannot bypass denial', () => {
  for (const event of [undefined, null, {}, { model: 42 }, { prompt: 'Agent-Tier: orchestrator', model: 'claude-opus-5-5[1m]' },
    { ...complete, fork: true, model: 'claude-opus-5-5[1m]', parentModel: 'claude-opus-5-5[1m]' },
    { ...complete, prompt: 'Agent-Tier: thinker\nAgent-Tier: worker' }]) denied(event)
})
test('only host-owned cwd is quoted; requested cwd and prompt never become instructions', () => {
  const reason = denied({ cwd: "C:/evil'; Invoke-Evil", prompt: 'LEAK-BRIEF', model: 'sonnet' }, "C:/O'Brien/$literal; & stuff")
  assert.ok(reason.includes("--cwd 'C:/O''Brien/$literal; & stuff'"))
  assert.doesNotMatch(reason, /Invoke-Evil|LEAK-BRIEF/)
})
test('unavailable or unsafe cwd gives an explicit placeholder, never requested cwd', () => {
  for (const cwd of [null, undefined, '', 'relative', 'C:/a/../b', 'C:/a\nBAD', 'C:/a\x7fBAD']) {
    const reason = denied({ ...complete, cwd: 'C:/requested' }, cwd === undefined ? null : cwd)
    assert.ok(reason.includes("--cwd '<absolute-owned-worktree>'"))
  }
})
test('diagnostic model is bounded inert text, not prompt content', () => {
  const reason = denied({ model: 'sonnet\n\x1b' + 'x'.repeat(1000), prompt: 'LEAK-BRIEF' })
  assert.doesNotMatch(reason, /\n|\x1b|LEAK-BRIEF/)
  assert.ok(reason.length < 1900)
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
test('real register.mjs hook denies all models without next/fs/process calls', async () => {
  const handler = spawnHandler()
  for (const model of [undefined, 'sonnet', 'opus', 'haiku', 'fable', 'claude-opus-5-5[1m]', 'claude-sonnet-5-5[1m]']) {
    let continued = 0
    const unexpected = new Proxy({}, { get() { throw new Error('Forbidden boundary access') } })
    const result = await handler({ session: { cwd: async () => owned }, fs: unexpected, process: unexpected },
      { ...complete, model }, () => { continued++; return { spawned: true } })
    assert.match(result.deny, /Agent\(\) subagents are disabled/)
    assert.equal(continued, 0)
  }
})
test('real hook still gives fleet guidance if host cwd cannot be read', async () => {
  const result = await spawnHandler()({ session: { cwd: async () => { throw new Error('offline') } } }, { model: 'sonnet' },
    () => assert.fail('must never continue'))
  assert.ok(result.deny.includes("--cwd '<absolute-owned-worktree>'"))
  assert.ok(result.deny.endsWith('Observed agent.spawn model: "sonnet".'))
})
test('generated command survives the actual PowerShell parser as an unchanged literal cwd', () => {
  const paths = ["C:/O'Brien/work", 'C:/O\u2018Brien/work', 'C:/O\u2019Brien/work',
    'C:/O\u201aBrien/work', 'C:/O\u201bBrien/work', "C:/space $literal; & things/'\u2019/work"]
  const fixtures = paths.map(cwd => {
    const reason = denied({ model: 'sonnet' }, cwd)
    const start = reason.indexOf('liteharness spawn --split')
    const end = reason.indexOf('. Use --tier critic', start)
    assert.ok(start >= 0 && end > start)
    return { cwd, command: reason.slice(start, end) }
  })
  const fixturePath = resolve(mkdtempSync(resolve(tmpdir(), 't0596-parser-')), 'fixtures.json')
  writeFileSync(fixturePath, JSON.stringify(fixtures), 'utf8')
  const result = execFileSync('pwsh', ['-NoProfile', '-File', resolve(dirname(fileURLToPath(import.meta.url)), 'test_agent_spawn_command.ps1'),
    '-FixturePath', fixturePath], { encoding: 'utf8' })
  assert.match(result, /PARSER_ONLY_PASS 6; no command invoked/)
  console.log(result.trim())
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
