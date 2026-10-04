import assert from 'node:assert/strict'
import { test } from 'node:test'
import { register, evaluateGuard } from '../hooks/register.mjs'
import { guardPayload, guardReply, permissionResult } from '../hooks/mods/guards.mjs'

const clean = { protocol: 1, deny: null, allowOwnWrite: false, command: null }
function fixture(reply = clean) {
  const hooks = new Map()
  const registrations = []
  register((name, matcher, handler) => {
    if (typeof matcher === 'function') { handler = matcher; matcher = {} }
    assert.ok(!registrations.some(r => r.name === name &&
      JSON.stringify(r.matcher) === JSON.stringify(matcher)), 'duplicate event+matcher')
    const registration = { name, matcher, handler, catchHandler: null }
    registrations.push(registration)
    // Select the sole unfiltered tool handler, not unrelated matched commands.
    if (name === 'tool.call' || name === 'tool.check') {
      assert.deepEqual(matcher, {})
      assert.ok(!hooks.has(name), 'one authoritative tool handler')
      hooks.set(name, async ($, event, next) => {
        try { return await handler($, event, next) }
        catch (error) {
          if (!registration.catchHandler) throw error
          return registration.catchHandler($, event, error)
        }
      })
    }
    const handle = { catch(fn) {
      registration.catchHandler = fn
      if (name === 'tool.call' || name === 'tool.check') hooks.set(name + '.catch', fn)
      return handle
    } }
    return handle
  }, {})
  const calls = []
  const $ = { session: { cwd: async () => '/owned', id: async () => 'seat' },
    plugin: { root: '/plugin' }, process: { run: async (argv, init) => {
      calls.push({ argv, init })
      return { exitCode: 0, stdout: JSON.stringify(reply), stderr: '' }
    } } }
  return { $, hooks, calls }
}

test('normalization uses trusted session context, not tool cwd as session', () => {
  const p = guardPayload({ tool: 'Bash', command: 'echo x', cwd: '/spoof', tool_use_id: 'call', agentId: 'sub' }, '/real', 'seat')
  assert.equal(p.cwd, '/real')
  assert.equal(p.tool_input.cwd, '/spoof')
  assert.equal(p.tool_input.agentId, undefined)
  assert.throws(() => guardPayload({ tool: 'Bash', input: [] }, '/real', 'seat', 'check'))
})

test('backend protocol rejects failed, truncated, ambiguous results', () => {
  for (const result of [{ exitCode: 1, stdout: '{}' }, { exitCode: 0, stdout: '{' },
    { exitCode: 0, stdout: JSON.stringify({ ...clean, protocol: 2 }) },
    { exitCode: 0, stdout: JSON.stringify({ ...clean, deny: 'floor', allowOwnWrite: true }) }]) {
    assert.throws(() => guardReply(result))
  }
})

test('shipped call hook floor deny never calls downstream', async () => {
  const f = fixture({ ...clean, deny: 'floor' })
  const result = await f.hooks.get('tool.call')(f.$, { tool: 'Bash', command: 'danger' }, () => assert.fail('ran tool'))
  assert.deepEqual(result, { deny: 'floor' })
  assert.deepEqual(f.calls[0].argv, ['python', '/plugin/hooks/mods/guard_backend.py'])
  assert.equal(JSON.parse(f.calls[0].init.stdin).tool_input.command, 'danger')
  assert.equal(f.calls[0].init.timeoutMs, 15000)
})

test('shipped call hook rewrites copied frozen event, retaining envelope', async () => {
  const f = fixture({ ...clean, command: 'safe body-file invocation' })
  const original = Object.freeze({ tool: 'Bash', command: 'inline', tool_use_id: 'call', agentId: 'sub' })
  let seen
  let downstreamCalls = 0
  await f.hooks.get('tool.call')(f.$, original, e => {
    downstreamCalls++
    assert.equal(f.calls.length, 1, 'authoritative backend completed before downstream')
    seen = e
    return { result: 'ok' }
  })
  assert.equal(downstreamCalls, 1)
  assert.equal(seen.command, 'safe body-file invocation')
  assert.equal(seen.agentId, 'sub')
  assert.equal(seen.tool_use_id, 'call')
  assert.equal(original.command, 'inline')
})

test('runner exceptions and timeouts deny both hooks without next', async () => {
  const f = fixture()
  f.$.process.run = async () => { throw new Error('timeout') }
  const never = () => assert.fail('next called')
  assert.ok((await f.hooks.get('tool.call')(f.$, { tool: 'Bash', command: 'x' }, never)).deny)
  assert.equal((await f.hooks.get('tool.check')(f.$, { tool: 'Write', input: { file_path: '/owned/a' } }, never)).decision, 'deny')
  assert.ok((await f.hooks.get('tool.call.catch')()).deny)
  assert.equal((await f.hooks.get('tool.check.catch')()).decision, 'deny')
})

test('fresh check permits proven file writes but preserves deny and rule ask', async () => {
  const f = fixture({ ...clean, allowOwnWrite: true })
  const e = { tool: 'Write', input: { file_path: '/owned/a' } }
  const hook = f.hooks.get('tool.check')
  assert.equal((await hook(f.$, e, async () => ({ decision: 'ask' }))).decision, 'allow')
  assert.equal((await hook(f.$, e, async () => ({ decision: 'deny' }))).decision, 'deny')
  assert.equal((await hook(f.$, e, async () => ({ decision: 'ask', rule: 'Write(*)' }))).decision, 'ask')
  assert.equal(f.calls.length, 3)
  assert.equal(JSON.parse(f.calls[0].init.stdin).kind, 'check')
})

test('permission floor result dominates proof and unknown decisions unchanged', () => {
  assert.equal(permissionResult({ decision: 'allow' }, { ...clean, deny: 'floor' }).decision, 'deny')
  assert.equal(permissionResult({ decision: 'unknown' }, { ...clean, allowOwnWrite: true }).decision, 'unknown')
})

test('shipped guards refuse floor and malformed replies before any downstream effect', async () => {
  for (const reply of [{ ...clean, deny: 'floor' }, {}, { ...clean, deny: false }]) {
    const f = fixture(reply)
    let effects = 0
    const next = async () => { effects++; return { decision: 'allow' } }
    assert.ok((await f.hooks.get('tool.call')(f.$, { tool: 'Bash', command: 'x' }, next)).deny)
    assert.equal((await f.hooks.get('tool.check')(f.$, { tool: 'Write', input: { file_path: '/owned/a' } }, next)).decision, 'deny')
    assert.equal(effects, 0, 'catch must not mask a downstream effect')
    assert.equal(f.calls.length, 2)
  }
})

test('injected registration catch uses shipped refusals for downstream failure', async () => {
  const f = fixture()
  let effects = 0
  const next = async () => {
    assert.equal(f.calls.length, effects + 1, 'floor checked first')
    effects++
    throw new Error('downstream failed')
  }
  assert.match((await f.hooks.get('tool.call')(f.$, { tool: 'Bash', command: 'x' }, next)).deny, /failed or timed out/)
  assert.equal((await f.hooks.get('tool.check')(f.$, { tool: 'Write', input: { file_path: '/owned/a' } }, next)).decision, 'deny')
  assert.equal(effects, 2)
})

test('helper never passes submitted command as subprocess argv', async () => {
  const f = fixture()
  await evaluateGuard(f.$, { tool: 'Bash', command: 'malicious --argv' })
  assert.ok(!f.calls[0].argv.includes('malicious --argv'))
})
