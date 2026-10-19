// Executes the shipped entrypoint with injected API boundaries.
// This is NOT the Claude Mods host and performs no process, fs or spawn effects.
import assert from 'node:assert/strict'

const registrations = new Map()
const files = new Map()
const timers = []
const commands = []
const toasts = []
const elements = Object.fromEntries(['Box', 'Text', 'Button'].map(type => [type, props => ({ type, ...props })]))
let processFailure = false
let persistenceFailure = false
let sid = 'seat'
let compactCalls = 0
let forwarded = 0
let statCalls = 0
let blockNextIdentity = false
let identityEntered
let releaseIdentity
const $ = {
  session: { id: async () => {
    if (blockNextIdentity) {
      blockNextIdentity = false
      identityEntered()
      await new Promise(resolve => { releaseIdentity = resolve })
    }
    return sid
  }, cwd: async () => '/workspace', model: async () => 'claude-opus-5-5[1m]',
    usage: async () => ({ startedAt: 0, context: { percent: 10, tokens: 20000, window: 200000 } }),
    compact: async () => { compactCalls++; return { messages: [], tokensBefore: 20000, tokensAfter: 2000 } } },
  clock: { now: async () => 1000, every: () => ({ cancel() {} }),
    after: (delay, callback) => { const timer = { callback, cancelled: false, cancel() { this.cancelled = true } }; timers.push(timer); return timer } },
  env: { get: async () => '/home' },
  store: { get: async key => files.get(key), set: async (key, value) => {
    if (persistenceFailure && key.startsWith('handoff.')) throw new Error('store unavailable')
    files.set(key, value)
  } },
  fs: { write: async () => {}, stat: async () => { statCalls++; return { kind: 'dir', isLink: false, realPath: '/workspace' } } },
  process: { run: async argv => {
    assert.deepEqual(argv, ['python', '-m', 'liteharness.mod_fleet'])
    if (processFailure) return { exitCode: 1, stdout: '', stderr: 'unavailable' }
    return { exitCode: 0, stdout: JSON.stringify({ schemaVersion: 1, sampledAt: 1000, agentCount: 1, taskCount: 1,
      agents: [{ name: 'seat', tier: 'worker', model: 'claude-opus-5-5[1m]' }],
      tasks: [{ id: 'T1', title: 'task', status: 'building', tier: '2' }], warnings: [] }) }
  } },
  command: { register: async command => commands.push(command) },
  ui: { invalidate() {}, toast: async text => toasts.push(text), open: async () => ({ isPlaced: true }), resolve: () => elements },
  // Any accidental turn/model dispatch fails loudly.
  prompt: { submit: () => { throw new Error('unexpected Claude turn') } },
  model: { complete: () => { throw new Error('unexpected model request') } },
}
const { register } = await import('../hooks/register.mjs')
register((name, matcher, hook) => {
  if (typeof matcher === 'function') { hook = matcher; matcher = {} }
  const key = name + JSON.stringify(matcher)
  assert.equal(registrations.has(key), false, 'duplicate event+matcher')
  const registration = { name, matcher, hook, catchHandler: null }
  registrations.set(key, registration)
  const handle = { catch(fn) { registration.catchHandler = fn; return handle } }
  return handle
})
async function fire(name, event = {}) {
  const matched = [...registrations.values()].filter(r => r.name === name && Object.entries(r.matcher).every(([k, v]) => event[k] === v))
  // Paste adds a broad Pane middleware which passes unrelated panes through.
  // Keep the single-handler contract for all other exercised event shapes.
  const fleetPane = name === 'ui.render' && event.component === 'Pane' && event.requestId === 'liteharness-fleet'
  assert.equal(matched.length, fleetPane ? 2 : 1, 'expected composed handlers for fixture event')
  let next = async e => { forwarded++; return e }
  for (const registration of matched) {
    const downstream = next
    next = async e => {
      try { return await registration.hook($, e, downstream) }
      catch (error) {
        if (!registration.catchHandler) throw error
        return registration.catchHandler($, e, error)
      }
    }
  }
  return next(event)
}
async function settle() { while (timers.length) { const timer = timers.shift(); if (!timer.cancelled) await timer.callback() } }
function text(tree) { return (tree.children || []).map(child => typeof child === 'string' ? child : text(child)).join('\n') }

await fire('session.start', { cwd: '/workspace' })
assert.deepEqual(commands.map(c => c.name), ['tick', 'handoff', 'compact-seat'])
assert.ok(commands.every(c => c.immediate === true))
assert.match((await fire('command.run', { command: 'tick' })).text, /1 live seats, 1 active cards/)
const pane = await fire('ui.render', { component: 'Pane', requestId: 'liteharness-fleet' })
assert.match(text(pane), /FLEET/)
assert.match(text(pane), /T1/)
await fire('command.run', { command: 'handoff' })
assert.equal(files.get('handoff.v1.seat').narrative, false)
assert.equal(files.get('handoff.v1.seat').inboxAvailable, false)
assert.equal(files.get('handoff.v1.seat').inbox.available, false)
assert.equal(files.get('handoff.v1.seat').inbox.sessionId, null)
assert.match(files.get('handoff.v1.seat').inbox.availabilityReason, /disabled or unavailable/)
assert.match(files.get('handoff.v1.seat').inbox.deliveryMeaning, /not processed/)
assert.equal(files.get('handoff.v1.seat').inbox.peerAuthority, false)
assert.equal(compactCalls, 0)
await fire('command.run', { command: 'compact-seat' })
assert.equal(compactCalls, 0, 'compaction runs outside command event')
await settle()
assert.equal(compactCalls, 1)
persistenceFailure = true
assert.match((await fire('command.run', { command: 'compact-seat' })).text, /not scheduled/)
await settle()
assert.equal(compactCalls, 1, 'failed handoff prevents compact')
persistenceFailure = false
await fire('turn.start', {})
assert.match((await fire('command.run', { command: 'compact-seat' })).text, /active turn/)
await fire('turn.complete', {})
processFailure = true
assert.match((await fire('command.run', { command: 'tick' })).text, /failed/)
assert.match(text(await fire('ui.render', { component: 'Pane', requestId: 'liteharness-fleet' })), /previous snapshot/)
processFailure = false
const validSpawn = { prompt: 'no tier line', model: 'claude-opus-5-5[1m]', cwd: '/workspace', parentModel: 'claude-opus-5-5[1m]', fork: false }
const beforeSpawnForwarded = forwarded
const beforeSpawnStats = statCalls
// Allowed Agent() calls reach the host's continuation unchanged: any model (fable included) or none, no role line.
const allowedModels = [undefined, 'opus', 'sonnet', 'haiku', 'claude-opus-5-5', 'claude-sonnet-5-5', 'claude-haiku-5-5',
  'claude-opus-5-5[1m]', 'claude-sonnet-5-5[1m]', 'claude-haiku-5-5[1m]', 'fable', 'claude-fable-5-1[1m]', 'inherit', 'gpt-5']
for (const model of allowedModels) {
  const event = { ...validSpawn, model }
  assert.equal(await fire('agent.spawn', event), event, 'allowed spawn must continue with its own event: ' + model)
}
assert.equal(forwarded, beforeSpawnForwarded + allowedModels.length, 'every allowed Agent() call continues exactly once')
// isolation:"worktree" lives under the session's repo: a cwd inside the session directory also continues.
const inside = { ...validSpawn, model: 'sonnet', cwd: '/workspace/.claude/worktrees/agent-x' }
assert.equal(await fire('agent.spawn', inside), inside, 'a worktree inside the session directory must continue')
const afterInside = forwarded
// Refused calls get a deny and never continue.
const beforeRefused = afterInside
for (const cwd of ['/other', '/workspace-evil', '/workspace-evil/x', '/workspace/../other']) {
  for (const model of [undefined, 'sonnet', 'fable']) {
    assert.match((await fire('agent.spawn', { ...validSpawn, model, cwd })).deny, /cwd must be the session/, cwd)
  }
}
assert.equal(forwarded, beforeRefused, 'a refused Agent() call must not continue')
assert.equal(statCalls, beforeSpawnStats, 'the guard does not inspect requested filesystem paths')
// A turn starts while the final native-dispatch identity read is awaiting.
await fire('command.run', { command: 'compact-seat' })
const entered = new Promise(resolve => { identityEntered = resolve })
blockNextIdentity = true
const racedDispatch = settle()
await entered
await fire('turn.start', {})
releaseIdentity()
await racedDispatch
assert.equal(compactCalls, 1, 'turn during final identity read must prevent native compact')
await fire('turn.complete', {})
await fire('command.run', { command: 'compact-seat' })
await fire('session.end', { reason: 'other', sessionId: sid })
await settle()
assert.equal(compactCalls, 1, 'session end cancels pending compact')
console.log('Shipped entrypoint fixture checks passed; no real spawning, no Claude host/runtime proof.')
