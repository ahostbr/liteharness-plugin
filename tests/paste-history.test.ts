// Native host fixtures. No real disk reads, model turn, install or pixel proof.
import { expect, mock, test } from 'claude-code/testing'

const png = 'a'.repeat(64) + '.png'
const gif = 'b'.repeat(64) + '.gif'
const root = '/work/.litesuite/theater/pastes'
const PANE = { plugin: 'liteharness', component: 'Pane', surface: 'terminal', requestId: 'liteharness-pastes',
  viewport: { columns: 160, rows: 40 }, props: { title: 'Pasted images', isFocused: false, bodyColumns: 40,
    placement: 'dock', scroll: { offset: 0, bodyRows: 24 }, view: {} } } as const

function fixture(on, enabled = true) {
  const clock = mock.clock(on, { now: 100_000 })
  mock.env(on, { HOME: '/test-home', ...(enabled ? { LITEHARNESS_PASTE_PANE: '1' } : {}) })
  mock.store(on)
  let entries = [{ file: png, bytes: 68 }]
  let reads = 0, opens = 0
  const panes: any[] = []
  on('session.id', () => ({ value: 'seat' }))
  on('session.cwd', () => ({ value: '/work' }))
  on('session.surfaces', () => ({ value: ['terminal'] }))
  on('session.usage', () => ({ value: null }))
  on('fs.write', () => ({ value: undefined }))
  on('fs.exists', () => ({ value: true }))
  on('fs.stat', ($, e) => ({ value: { kind: e.path === root ? 'dir' : 'file', isLink: false,
    size: e.path.endsWith('.history.json') ? 200 : 68, realPath: e.path } }))
  on('fs.read', () => { reads++; return { value: JSON.stringify({ entries }) } })
  on('command.register', () => ({ value: undefined }))
  on('ui.panes', () => ({ value: panes }))
  on('ui.open', ($, e) => { opens++; panes.push({ ...e, isShown: true, isFocused: false, isPlaced: true }); return { value: { isPlaced: true } } })
  on('ui.close', ($, e) => { const i = panes.findIndex(p => p.id === e.id); if (i >= 0) panes.splice(i, 1); return { value: undefined } })
  on('ui.render', () => ({ type: 'Text', props: {}, children: ['other mod'] }))
  on('session.start', () => ({ cwd: '/work' }))
  on('session.measure', () => ({ changed: [] }))
  return { clock, panes, reads: () => reads, opens: () => opens, set: value => { entries = value } }
}

test('native PNG thumbnail survives turns and polling; non-PNG truthfully retained', async ($, on) => {
  const f = fixture(on)
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/work' })
  const ui = await $.ui.mount(PANE)
  expect((await ui.find({ type: 'Image' }))?.props.source).toEqual({ file: root + '/assets/' + png, format: 'png' })
  await $.session.measure({ context: { tokens: 0, window: 200000, percent: 0 }, rateLimits: [], changed: ['context'] })
  await f.clock.advance(15_000)
  expect(f.opens()).toBe(1)
  f.set([{ file: gif, bytes: 68 }, { file: png, bytes: 68 }])
  await f.clock.advance(15_000)
  expect(await ui.find({ type: 'Text', text: /GIF preview unsupported.*retained/ })).toBeDefined()
  await ui.press({ key: 'pastes-hide' })
  await f.clock.advance(15_000)
  expect(f.panes.length).toBe(0)
  await ui.unmount()
})

test('off defaults preserve other rendering without reading history', async ($, on) => {
  const f = fixture(on, false)
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/work' })
  const ui = await $.ui.mount(PANE)
  expect(await ui.find({ type: 'Text', text: /other mod/ })).toBeDefined()
  expect(f.reads()).toBe(0)
  expect(f.opens()).toBe(0)
  await ui.unmount()
})

test('Desktop receives honest explanation, never an Image element', async ($, on) => {
  fixture(on)
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/work' })
  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect(await ui.find({ type: 'Text', text: /terminal-only/ })).toBeDefined()
  expect(await ui.find({ type: 'Image' })).toBeUndefined()
  await ui.unmount()
})
