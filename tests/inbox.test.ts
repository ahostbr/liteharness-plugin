// Claude's own plugin test host. External processes/maildir are fixtures only.
import { expect, mock, test } from 'claude-code/testing'

const PANE = { plugin: 'liteharness', component: 'Pane', requestId: 'liteharness-inbox',
  surface: 'terminal', viewport: { columns: 160, rows: 40 },
  props: { title: 'Inbox', isFocused: true, bodyColumns: 40, placement: 'dock',
    scroll: { offset: 0, bodyRows: 20 }, view: {} } } as const

function fixture(on, { enabled = true, fail = false } = {}) {
  const clock = mock.clock(on, { now: 100_000 })
  mock.env(on, { HOME: '/fixture', LITEHARNESS_NATIVE_INBOX: enabled ? '1' : '', LITEHARNESS_AGENT_ID: 'seat' })
  const saved = new Map<string, any>()
  const actions: string[] = []
  let messages = [{ id: 'm1', from: 'leader', to: 'seat', body: 'fixture message',
    type: 'TASK', priority: 'normal', receipt: 'm1.json' }]
  on('session.id', () => ({ value: 'session' }))
  on('session.usage', () => ({ value: { context: {}, rateLimits: [] } }))
  on('store.get', ($, e) => ({ value: saved.get(e.key) }))
  on('store.set', ($, e) => { saved.set(e.key, e.value); return { value: undefined } })
  on('fs.write', () => ({ value: undefined }))
  on('process.run', ($, e) => {
    const action = e.argv[3]
    actions.push(action)
    if (fail) return { value: { exitCode: 1, stdout: '{}', stderr: '' } }
    if (action === 'ack') messages = []
    return { value: { exitCode: 0, stdout: JSON.stringify({ schemaVersion: 1,
      sessionId: 'session', agentId: 'seat', blocked: 0,
      messages: action === 'poll' ? messages : [] }), stderr: '' } }
  })
  on('session.start', () => ({ cwd: '/fixture' }))
  on('session.end', () => ({ sessionId: 'session' }))
  on('prompt.submit', ($, e) => ({ text: e.text, context: e.context, origin: e.origin }))
  on('prompt.context', ($, e) => ({ blocks: e.blocks }))
  return { clock, saved, actions }
}

test('native inbox attaches accepted prompt context and keeps first context blocks', async ($, on) => {
  const f = fixture(on)
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/fixture' })
  const result = await $.prompt.submit({ text: 'fixture user entry' })
  expect(result.context?.join('\n')).toMatch(/fixture message/)
  expect(f.actions.includes('ack')).toBe(true)
  expect(f.saved.get('inbox.v1.session').accepted[0].id).toBe('m1')
  const context = await $.prompt.context({ blocks: [{ name: 'existing', text: 'keep' }] })
  expect(context.blocks[0].text).toBe('keep')
  expect(context.blocks.at(-1)?.text).toMatch(/fixture message/)
})

test('native inbox pane displays accepted-not-processed distinction on both surfaces', async ($, on) => {
  fixture(on)
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/fixture' })
  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ ...PANE, surface })
    expect(await ui.find({ type: 'Text', text: /fixture message/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /not processed/ })).toBeDefined()
    await ui.unmount()
  }
})

test('legacy default makes no native adapter call', async ($, on) => {
  const f = fixture(on, { enabled: false })
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/fixture' })
  await f.clock.advance(5000)
  expect(f.actions).toEqual([])
})
