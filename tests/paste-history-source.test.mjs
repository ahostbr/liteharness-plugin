// Bounded Node fallback: actual shipped registration, in-memory API only.
// This is not Claude's analyzer/element host and not terminal paint proof.
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { absolutePath, historyEntries, within, imageGeometry } from '../hooks/mods/paste-schema.mjs'

const png = 'a'.repeat(64) + '.png'
const gif = 'b'.repeat(64) + '.gif'
const root = '/work/.litesuite/theater/pastes'
let serial = 0
async function fixture({ enabled = true, entries = [{ file: png, bytes: 68 }], surfaces = ['terminal'] } = {}) {
  const { register } = await import('../hooks/register.mjs?fixture=' + serial++)
  const registrations = []
  const timers = []
  const panes = []
  const calls = { reads: 0, stats: 0, opens: 0, writes: 0, commands: [], toasts: [] }
  let sid = 'seat', cwd = '/work', text = JSON.stringify({ entries }), exists = true
  let badAsset = false, badManifest = false, delayedRead = null, statFailure = false
  const element = type => props => ({ type, props, children: props.children || [] })
  const $ = {
    session: { id: async () => sid, cwd: async () => cwd, surfaces: async () => surfaces,
      usage: async () => null },
    env: { get: async key => key === 'LITEHARNESS_PASTE_PANE' ? enabled ? '1' : undefined : key === 'HOME' ? '/home' : undefined },
    clock: { now: async () => 1000, every: (ms, fn) => { const job = { ms, fn, cancelled: false, cancel() { this.cancelled = true } }; timers.push(job); return job } },
    store: { get: async () => undefined, set: async () => {} },
    command: { register: async spec => calls.commands.push(spec) },
    fs: {
      exists: async () => exists,
      read: async () => { calls.reads++; if (delayedRead) await delayedRead; return text },
      write: async () => { calls.writes++ },
      stat: async path => { calls.stats++; if (statFailure) throw new Error('private error'); return {
        kind: path === root ? 'dir' : 'file', isLink: false,
        size: path.endsWith('.history.json') ? text.length : 68,
        realPath: badAsset && path.includes('/assets/') ? '/outside/image.png' :
          badManifest && path.endsWith('.history.json') ? '/outside/manifest' : path,
      } },
    },
    ui: { invalidate: () => {}, panes: async () => panes,
      open: async spec => { calls.opens++; panes.push(spec); return { isPlaced: true } },
      close: async ({ id }) => { const i = panes.findIndex(p => p.id === id); if (i >= 0) panes.splice(i, 1) },
      toast: async text => calls.toasts.push(text),
      resolve: () => Object.fromEntries(['Box', 'Text', 'Button', 'Image'].map(type => [type, element(type)])),
    },
  }
  register((event, matcher, handler) => {
    if (typeof matcher === 'function') { handler = matcher; matcher = {} }
    assert.ok(!registrations.some(r => r.event === event &&
      JSON.stringify(r.matcher) === JSON.stringify(matcher)), 'duplicate event+matcher')
    const registration = { event, matcher, handler, catchHandler: null }
    registrations.push(registration)
    const handle = { catch(fn) { registration.catchHandler = fn; return handle } }
    return handle
  }, {})
  const next = async () => ({ type: 'Text', props: {}, children: ['downstream'] })
  async function fire(event, input = {}) {
    // Keep the existing fleet fixture's wrapping order; a broad Pane handler
    // must delegate, not independently overwrite a specific pane's result.
    let dispatch = next
    for (const hook of registrations.filter(h => h.event === event && Object.entries(h.matcher).every(([k, v]) => input[k] === v))) {
      const downstream = dispatch
      dispatch = async e => {
        try { return await hook.handler($, e, downstream) }
        catch (error) {
          if (!hook.catchHandler) throw error
          return hook.catchHandler($, e, error)
        }
      }
    }
    return dispatch(Object.freeze(input))
  }
  const render = () => fire('ui.render', { component: 'Pane', requestId: 'liteharness-pastes', surface: 'terminal', props: { bodyColumns: 30 } })
  return { calls, registrations, timers, panes, fire, render,
    poll: () => timers.at(-1).fn(),
    setEntries: value => { text = JSON.stringify({ entries: value }) },
    setRaw: value => { text = value }, setExists: value => { exists = value },
    setBadAsset: () => { badAsset = true }, setBadManifest: () => { badManifest = true },
    setFailure: () => { statFailure = true },
    identity: (id, dir = '/work') => { sid = id; cwd = dir },
    delay: promise => { delayedRead = promise },
  }
}
function flatten(tree) { return [tree, ...(tree.children || []).filter(x => typeof x === 'object' && x).flatMap(flatten)] }
function images(tree) { return flatten(tree).filter(e => e.type === 'Image') }
function text(tree) { return flatten(tree).flatMap(e => e.children.filter(x => typeof x === 'string')).join(' ') }
function button(tree, key) { return flatten(tree).find(e => e.props?.key === key).props.onPress() }

test('pure paths, schema, size and geometry reject untrusted values', () => {
  assert.equal(absolutePath('relative'), null)
  assert.equal(absolutePath('/work/../secret'), null)
  assert.equal(absolutePath('C:\\work'), 'C:/work')
  assert.equal(within('/work', '/worker/x'), false)
  assert.equal(within('/work', '/work/x'), true)
  assert.throws(() => historyEntries('{'))
  assert.throws(() => historyEntries(JSON.stringify({ entries: [{ file: '../x.png', bytes: 1 }] })))
  assert.throws(() => historyEntries(JSON.stringify({ entries: [{ file: png, bytes: 0 }] })))
  assert.throws(() => historyEntries(JSON.stringify({ entries: [{ file: png, bytes: 6 * 1024 * 1024 }] })))
  assert.throws(() => historyEntries(JSON.stringify({ entries: Array(257).fill({ file: png, bytes: 1 }) })))
  assert.throws(() => historyEntries(JSON.stringify({ entries: [{ file: png, bytes: 1 }, { file: png, bytes: 1 }] })))
  assert.deepEqual(imageGeometry(999), { columns: 40, rows: 8 })
})

test('off by default has zero history IO/UI/commands; shared lifecycle stays single', async () => {
  const f = await fixture({ enabled: false })
  await f.fire('session.start')
  await f.poll()
  assert.equal(f.calls.reads, 0)
  assert.equal(f.calls.stats, 0)
  assert.equal(f.calls.opens, 0)
  // Paste stays off; the independently composed fleet commands remain available.
  assert.deepEqual(f.calls.commands.map(command => command.name), ['tick', 'handoff', 'compact-seat'])
  assert.equal(f.registrations.filter(h => h.event === 'session.start').length, 1)
  assert.equal(f.registrations.filter(h => h.event === 'session.end').length, 1)
  assert.equal(text(await f.render()), 'downstream')
})

test('PNG file thumbnail persists across turns, adds newest, no duplicate panes', async () => {
  const f = await fixture()
  await f.fire('session.start')
  assert.equal(images(await f.render())[0].props.source.file, root + '/assets/' + png)
  await f.fire('session.measure')
  await f.poll()
  assert.equal(f.calls.opens, 1)
  f.setEntries([{ file: gif, bytes: 68 }, { file: png, bytes: 68 }])
  await f.poll()
  const tree = await f.render()
  assert.equal(images(tree).length, 1)
  assert.match(text(tree), /GIF preview unsupported.*retained/)
  assert.deepEqual(f.calls.commands.map(command => command.name), ['tick', 'handoff', 'compact-seat', 'pastes'])
})

test('user hide survives polls/new images; explicit command reopens', async () => {
  const f = await fixture()
  await f.fire('session.start')
  await button(await f.render(), 'pastes-hide')
  f.setEntries([{ file: gif, bytes: 68 }, { file: png, bytes: 68 }])
  await f.poll()
  assert.equal(f.panes.length, 0)
  await f.fire('command.run', { command: 'pastes' })
  assert.equal(f.panes.length, 1)
  await f.fire('ui.close', { id: 'liteharness-pastes', origin: { kind: 'person' } })
  f.panes.length = 0
  await f.poll()
  assert.equal(f.panes.length, 0)
})

test('desktop has no native images or automatic pane, unrelated panes pass through', async () => {
  const f = await fixture({ surfaces: ['desktop'] })
  await f.fire('session.start')
  assert.equal(f.calls.opens, 0)
  const tree = await f.fire('ui.render', { component: 'Pane', requestId: 'liteharness-pastes', surface: 'desktop' })
  assert.equal(images(tree).length, 0)
  assert.match(text(tree), /terminal-only/)
  const other = await f.fire('ui.render', { component: 'Pane', requestId: 'other', surface: 'terminal' })
  assert.equal(text(other), 'downstream')
})

for (const failure of ['manifest', 'asset', 'malformed', 'stat']) {
  test('fails closed without deleting files: ' + failure, async () => {
    const f = await fixture()
    if (failure === 'manifest') f.setBadManifest()
    if (failure === 'asset') f.setBadAsset()
    if (failure === 'malformed') f.setRaw('{bad private text')
    if (failure === 'stat') f.setFailure()
    await f.fire('session.start')
    assert.equal(f.calls.opens, 0)
    assert.equal(images(await f.render()).length, 0)
    assert.match(text(await f.render()), /unavailable|awaits/)
  })
}

test('bounded visible page previews all history through controls', async () => {
  const list = Array.from({ length: 17 }, (_, i) => ({ file: i.toString(16).padStart(64, '0') + '.png', bytes: 68 }))
  const f = await fixture({ entries: list })
  await f.fire('session.start')
  assert.equal(images(await f.render()).length, 8)
  assert.equal(f.calls.stats, 10) // root, manifest, 8 visible assets
  await button(await f.render(), 'pastes-next')
  assert.equal(images(await f.render())[0].props.source.file, root + '/assets/' + list[8].file)
  await button(await f.render(), 'pastes-next')
  assert.equal(images(await f.render()).length, 1)
})

test('end/clear/resume suppress late read and old identity, exit cancels poll', async () => {
  const f = await fixture()
  await f.fire('session.start')
  let release
  f.delay(new Promise(resolve => { release = resolve }))
  const pending = f.poll()
  await new Promise(resolve => setImmediate(resolve))
  await f.fire('session.end', { reason: 'clear', sessionId: 'seat' })
  f.identity('next')
  release()
  await pending
  assert.equal(images(await f.render()).length, 0)
  f.delay(null)
  await f.poll()
  assert.equal(images(await f.render()).length, 1)
  f.identity('other', '/other')
  assert.equal(images(await f.render()).length, 0)
  await f.fire('session.end', { reason: 'prompt_input_exit', sessionId: 'other' })
  assert.equal(f.timers.at(-1).cancelled, true)
})

test('reload restores from extractor manifest, missing file stays unknown', async () => {
  const first = await fixture()
  await first.fire('session.start')
  const reloaded = await fixture()
  await reloaded.fire('session.start')
  assert.equal(images(await reloaded.render()).length, 1)
  reloaded.setExists(false)
  await reloaded.poll()
  assert.equal(images(await reloaded.render()).length, 0)
})
