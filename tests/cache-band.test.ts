import { expect, mock, test } from 'claude-code/testing'
import { snapshot, cacheEstimate, restoredRequest } from '../hooks/mods/usage-schema.mjs'

const BAND = {
  plugin: 'liteharness', component: 'AbovePrompt', surface: 'terminal', requestId: 'band',
  viewport: { columns: 100, rows: 30 },
  props: { hasSurvey: false, isWorking: false, maxRows: 4, bodyColumns: 100,
    scroll: { offset: 0, bodyRows: 4 }, view: {} },
} as const

// All external boundaries are in-memory stubs in the installed Claude test host.
function fixture(on, options: { missingUsage?: boolean; saved?: any; failWrite?: boolean; compactSkip?: boolean; compactError?: boolean; refusal?: boolean; failed?: boolean; throws?: boolean; delayEnd?: boolean; delayCompact?: boolean } = {}) {
  const clock = mock.clock(on, { now: 100_000 })
  mock.env(on, { HOME: '/test-home' })
  const saved = new Map<string, any>()
  if (options.saved) saved.set('usage.v1.seat', options.saved)
  const files = new Map<string, any>()
  const toasts: string[] = []
  let sid = 'seat'
  let compactCalls = 0
  let context = { tokens: 1000, window: 200000, percent: 0.5 }
  let compactStarted
  const compactBegun = new Promise<void>(resolve => { compactStarted = resolve })
  let compactRelease
  const compactGate = new Promise<void>(resolve => { compactRelease = resolve })
  let identityFailure = false
  let endWriting = false
  let announceEnd
  const endStarted = new Promise<void>(resolve => { announceEnd = resolve })
  let releaseEnd
  const endGate = new Promise<void>(resolve => { releaseEnd = resolve })
  on('session.id', () => identityFailure ? { deny: 'identity unavailable' } : ({ value: sid }))
  on('session.usage', () => options.missingUsage ? { deny: 'not available' } :
    { value: { startedAt: 1000, context, rateLimits: [] } })
  on('store.get', ($, e) => ({ value: saved.get(e.key) }))
  on('store.set', ($, e) => { saved.set(e.key, e.value); return { value: undefined } })
  on('fs.write', async ($, e) => {
    const data = JSON.parse(e.text)
    if (options.delayEnd && !data.active) { endWriting = true; announceEnd(); await endGate }
    if (options.failWrite) return { deny: 'write unavailable' }
    files.set(e.path, JSON.parse(e.text)); return { value: undefined }
  })
  on('session.start', () => ({ cwd: '/work' }))
  on('session.end', () => ({ sessionId: sid }))
  on('session.measure', () => ({ changed: [] }))
  on('session.compact', async () => {
    compactCalls += 1
    compactStarted()
    if (options.delayCompact) await compactGate
    if (options.compactError) return { deny: 'compact unavailable' }
    return options.compactSkip ? { skip: 'busy' } : { messages: [], tokensBefore: 1000, tokensAfter: 100 }
  })
  on('ui.toast', ($, e) => { toasts.push(e.text); return { value: undefined } })
  on('ui.render', () => ({ type: 'Text', props: {}, children: ['other mod'] }))
  on('turn.step', async function* ($, e) {
    yield { kind: 'text', index: 0, text: 'ok' }
    if (options.throws) throw new Error('network failure')
    return { turnId: e.turnId, index: e.index, answer: 'ok', toolUses: [],
      stopReason: options.failed ? null : options.refusal ? 'refusal' : 'end_turn',
      usage: options.failed ? null : { input_tokens: 10, output_tokens: 1,
        cache_read_input_tokens: 0, cache_creation_input_tokens: 0, model: 'test' } }
  })
  return { clock, saved, files, toasts, compactBegun, releaseCompact: () => compactRelease(), setContext: (value) => { context = value }, endStarted, endWriting: () => endWriting, releaseEnd: () => releaseEnd(), failIdentity: () => { identityFailure = true }, changeId: (value: string) => { sid = value }, compactCalls: () => compactCalls }
}

async function start($) {
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/work' })
}

async function request($, agentId?: string) {
  const stream = $.turn.step({ turnId: 'turn', index: 0, model: 'test', messageCount: 1, ...(agentId ? { agentId } : {}) })
  const chunks: unknown[] = []
  let result = await stream.next()
  while (!result.done) { chunks.push(result.value); result = await stream.next() }
  return { chunks, result: result.value }
}

test('numeric schema rejects cross-session and future restoration', () => {
  const saved = snapshot('seat', 1000, null, 500)
  expect(restoredRequest(saved, 'other', 1000)).toBe(null)
  expect(restoredRequest(saved, 'seat', 100)).toBe(null)
  expect(cacheEstimate(0, 3_600_000).state).toBe('cold')
  expect(snapshot('seat', 1000, null, null).context.percent).toBe(null)
})

test('start/render/idle never warm; main success preserves stream and ages countdown', async ($, on) => {
  const f = fixture(on)
  await start($)
  expect(f.saved.get('usage.v1.seat').cache.state).toBe('unknown')
  const ui = await $.ui.mount(BAND)
  expect(await ui.find({ type: 'Text', text: /other mod/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /Context 0.5%.*unknown/ })).toBeDefined()
  const r = await request($)
  expect(r.chunks).toEqual([{ kind: 'text', index: 0, text: 'ok' }])
  expect(r.result.answer).toBe('ok')
  expect(f.saved.get('usage.v1.seat').cache.lastRequestAt).toBe(100_000)
  await f.clock.advance(15_000)
  expect(f.saved.get('usage.v1.seat').cache.remainingMs).toBe(3_585_000)
  expect(f.files.size).toBe(1)
  await f.clock.advance(3_585_000)
  expect(f.saved.get('usage.v1.seat').cache.state).toBe('cold')
  await ui.unmount()
})

test('failed response and subagent response never warm main cache', async ($, on) => {
  const f = fixture(on, { failed: true })
  await start($)
  await request($)
  expect(f.saved.get('usage.v1.seat').cache.lastRequestAt).toBe(null)
})

test('subagent success never warms main session', async ($, on) => {
  const f = fixture(on)
  await start($)
  await request($, 'agent')
  expect(f.saved.get('usage.v1.seat').cache.lastRequestAt).toBe(null)
})

test('reload restores identity scoped timestamp; identity change starts unknown', async ($, on) => {
  const f = fixture(on, { saved: snapshot('seat', 50_000, null, 40_000) })
  await start($)
  expect(f.saved.get('usage.v1.seat').cache.lastRequestAt).toBe(40_000)
  f.changeId('other')
  await f.clock.advance(15_000)
  expect(f.saved.get('usage.v1.other').cache.state).toBe('unknown')
})

test('missing usage and failed file publish remain visible without false warming', async ($, on) => {
  const f = fixture(on, { missingUsage: true, failWrite: true })
  await start($)
  const ui = await $.ui.mount(BAND)
  expect(await ui.find({ type: 'Text', text: /Context unknown.*Telemetry unavailable/ })).toBeDefined()
  expect(f.saved.get('usage.v1.seat').usageAvailable).toBe(false)
  await ui.unmount()
})

test('compact is explicit, refreshes usage and reports a skip', async ($, on) => {
  const f = fixture(on, { compactSkip: true })
  await start($)
  const ui = await $.ui.mount(BAND)
  await ui.press({ key: 'liteharness-compact' })
  await f.clock.settle()
  expect(f.compactCalls()).toBe(1)
  expect(f.toasts).toEqual(['Compact skipped: busy'])
  expect(f.saved.get('usage.v1.seat').cache.state).toBe('unknown')
  await ui.unmount()
})

test('refusal does not warm even with usage', async ($, on) => {
  const f = fixture(on, { refusal: true })
  await start($)
  const r = await request($)
  expect(r.result.stopReason).toBe('refusal')
  expect(f.saved.get('usage.v1.seat').cache.lastRequestAt).toBe(null)
})

test('throwing request keeps timestamp unknown', async ($, on) => {
  const f = fixture(on, { throws: true })
  await start($)
  try { await request($) } catch { /* Engine test host may surface the request exception. */ }
  expect(f.saved.get('usage.v1.seat').cache.lastRequestAt).toBe(null)
})

test('clear/resume keep timer alive, identity isolated, exit cancels it', async ($, on) => {
  const f = fixture(on)
  await start($)
  await request($)
  await $.session.end({ reason: 'clear' })
  expect(f.saved.get('usage.v1.seat').active).toBe(false)
  f.changeId('cleared')
  await f.clock.advance(15_000)
  expect(f.saved.get('usage.v1.cleared').cache.state).toBe('unknown')
  await $.session.end({ reason: 'resume' })
  f.changeId('resumed')
  await f.clock.advance(15_000)
  expect(f.saved.get('usage.v1.resumed').active).toBe(true)
  await $.session.end({ reason: 'prompt_input_exit' })
  await f.clock.advance(15_000)
  expect(f.saved.get('usage.v1.resumed').active).toBe(false)
})

test('compact refuses active turn and reports failure when idle', async ($, on) => {
  const f = fixture(on, { compactError: true })
  await start($)
  const busy = await $.ui.mount({ ...BAND, props: { ...BAND.props, isWorking: true } })
  await busy.press({ key: 'liteharness-compact' })
  expect(f.compactCalls()).toBe(0)
  await busy.unmount()
  const idle = await $.ui.mount({ ...BAND, surface: 'desktop' })
  await idle.press({ key: 'liteharness-compact' })
  await f.clock.settle()
  expect(f.compactCalls()).toBe(1)
  expect(f.toasts[1]).toMatch(/Compaction failed/)
  await idle.unmount()
})

test('last two warm minutes are amber and cold is not', async ($, on) => {
  const f = fixture(on)
  await start($)
  await request($)
  await f.clock.advance(3_465_000)
  const ui = await $.ui.mount(BAND)
  expect((await ui.find({ type: 'Text', text: /Cache estimate/ }))?.props.color).toBeUndefined()
  await f.clock.advance(15_000)
  expect((await ui.find({ type: 'Text', text: /Cache estimate/ }))?.props.color).toBe('yellow')
  await f.clock.advance(120_000)
  expect((await ui.find({ type: 'Text', text: /Cache estimate cold/ }))?.props.color).toBeUndefined()
  await ui.unmount()
})

test('delayed inactive write and queued tick cannot revive exited seat', async ($, on) => {
  const f = fixture(on, { delayEnd: true })
  await start($)
  const ending = $.session.end({ reason: 'prompt_input_exit', sessionId: 'seat' })
  await f.endStarted
  expect(f.endWriting()).toBe(true)
  const queued = $.session.measure({ changed: [] })
  await f.clock.advance(15_000)
  f.releaseEnd()
  await ending
  await queued
  await f.clock.advance(30_000)
  expect(f.saved.get('usage.v1.seat').active).toBe(false)
  expect([...f.files.values()][0].active).toBe(false)
})

test('end identity failure still cancels timer and suppresses later samples', async ($, on) => {
  const f = fixture(on)
  await start($)
  const initial = f.saved.get('usage.v1.seat').sampledAt
  f.failIdentity()
  await $.session.end({ reason: 'prompt_input_exit', sessionId: 'seat' })
  f.changeId('new')
  await f.clock.advance(30_000)
  expect(f.saved.get('usage.v1.seat').sampledAt).toBe(initial)
  expect(f.saved.has('usage.v1.new')).toBe(false)
})

test('clear does not reactivate old ID while waiting for replacement', async ($, on) => {
  const f = fixture(on)
  await start($)
  await $.session.end({ reason: 'clear', sessionId: 'seat' })
  await f.clock.advance(15_000)
  expect(f.saved.get('usage.v1.seat').active).toBe(false)
  f.changeId('new')
  await f.clock.advance(15_000)
  expect(f.saved.get('usage.v1.new').active).toBe(true)
})

test('compact press returns before 30s native completion and publishes engine metrics', async ($, on) => {
  const f = fixture(on, { delayCompact: true })
  await start($)
  const ui = await $.ui.mount(BAND)
  const pressedAt = f.clock.now()
  await ui.press({ key: 'liteharness-compact' })
  // Completion gate is still unresolved: the press must not own its lifetime.
  expect(f.clock.now() - pressedAt).toBe(0)
  expect((await ui.find({ key: 'liteharness-compact' }))?.props.label).toBe('Compacting…')
  const job = f.clock.settle()
  await f.compactBegun
  const elapsed = f.clock.advance(30_000)
  f.setContext({ tokens: 400, window: 200000, percent: 0.2 })
  f.releaseCompact()
  await job
  await elapsed
  expect((await ui.find({ key: 'liteharness-compact' }))?.props.label).toBe('Compact')
  expect(f.saved.get('usage.v1.seat').context.percent).toBe(0.2)
  expect([...f.files.values()][0].context.tokens).toBe(400)
  await ui.unmount()
})

test('long native compact error resets busy and preserves honest unknown usage', async ($, on) => {
  const f = fixture(on, { delayCompact: true, compactError: true })
  await start($)
  const ui = await $.ui.mount(BAND)
  await ui.press({ key: 'liteharness-compact' })
  const job = f.clock.settle()
  await f.compactBegun
  const elapsed = f.clock.advance(30_000)
  f.setContext({ window: 200000 })
  f.releaseCompact()
  await job
  await elapsed
  expect((await ui.find({ key: 'liteharness-compact' }))?.props.label).toBe('Compact')
  expect(f.toasts[0]).toMatch(/Compaction failed/)
  expect(f.saved.get('usage.v1.seat').context.percent).toBe(null)
  expect([...f.files.values()][0].context.tokens).toBe(null)
  await ui.unmount()
})

test('double press while compact dispatch pending schedules only once', async ($, on) => {
  const f = fixture(on)
  await start($)
  const ui = await $.ui.mount(BAND)
  await ui.press({ key: 'liteharness-compact' })
  await ui.press({ key: 'liteharness-compact' })
  await f.clock.settle()
  expect(f.compactCalls()).toBe(1)
  expect((await ui.find({ key: 'liteharness-compact' }))?.props.label).toBe('Compact')
  await ui.unmount()
})

test('ending session cancels pending compact dispatch and resets busy', async ($, on) => {
  const f = fixture(on)
  await start($)
  const ui = await $.ui.mount(BAND)
  await ui.press({ key: 'liteharness-compact' })
  await $.session.end({ reason: 'clear', sessionId: 'seat' })
  await f.clock.settle()
  expect(f.compactCalls()).toBe(0)
  expect((await ui.find({ key: 'liteharness-compact' }))?.props.label).toBe('Compact')
  await ui.unmount()
})

test('old compact completing after resume cannot sample or reset replacement session', async ($, on) => {
  const f = fixture(on, { delayCompact: true })
  await start($)
  const ui = await $.ui.mount(BAND)
  await ui.press({ key: 'liteharness-compact' })
  const job = f.clock.settle()
  await f.compactBegun
  await $.session.end({ reason: 'resume', sessionId: 'seat' })
  expect((await ui.find({ key: 'liteharness-compact' }))?.props.label).toBe('Compact')
  f.changeId('replacement')
  await $.session.measure({ changed: [] })
  const replacementSample = f.saved.get('usage.v1.replacement')
  f.setContext({ tokens: 999, window: 200000, percent: 99 })
  f.releaseCompact()
  await job
  expect(f.saved.get('usage.v1.replacement')).toEqual(replacementSample)
  expect(f.saved.get('usage.v1.seat').active).toBe(false)
  await ui.unmount()
})
