import { expect, mock, test } from 'claude-code/testing'
import { fleetSnapshot, spawnDenial } from '../hooks/mods/fleet.mjs'

const VALID = { prompt: 'Task brief', model: 'claude-opus-5-5[1m]', cwd: '/workspace', fork: false, parentModel: 'claude-opus-5-5[1m]' }

test('native Agent runs for any model and no role line; a cwd outside the session directory is refused', () => {
  for (const model of [undefined, 'opus', 'sonnet', 'haiku', 'fable', 'claude-opus-5-5', 'claude-sonnet-5-5', 'claude-haiku-5-5',
    'claude-opus-5-5[1m]', 'claude-fable-5-1[1m]', 'inherit', 'gpt-5']) {
    expect(spawnDenial({ ...VALID, model }, VALID.cwd)).toBeNull()
  }
  for (const prompt of ['', 'Agent-Tier: unknown', 'Agent-Tier: worker\nAgent-Tier: leader']) {
    expect(spawnDenial({ ...VALID, prompt }, VALID.cwd)).toBeNull()
  }
  expect(spawnDenial({ ...VALID, fork: true, parentModel: 'gpt-5' }, VALID.cwd)).toBeNull()
  expect(spawnDenial({ ...VALID, cwd: '/workspace/.claude/worktrees/agent-x' }, '/workspace')).toBeNull()
  for (const cwd of ['', '.', 'relative/path', 'C:relative', '/workspace\n', '/workspace/../other']) {
    expect(spawnDenial({ ...VALID, cwd }, cwd)).toMatch(/cwd must be the session/)
  }
  for (const cwd of ['/other', '/workspace-evil', '/workspace-evil/x']) {
    expect(spawnDenial({ ...VALID, cwd }, '/workspace')).toMatch(/cwd must be the session/)
  }
})

test('fleet snapshot is bounded, counted and display-safe', () => {
  const row = { schemaVersion: 1, sampledAt: 1000, agentCount: 102, taskCount: 1,
    agents: Array.from({ length: 102 }, () => ({ name: 'seat\u001b[31m', tier: 'worker' })),
    tasks: [{ id: 'T1', title: 'task', status: 'building', assignee: 'seat', tier: 2 }], warnings: [] }
  const result = fleetSnapshot(JSON.stringify(row))
  expect(result.agents.length).toBe(100)
  expect(result.agentCount).toBe(102)
  expect(result.agents[0].name).toBe('seat [31m')
  expect(result.tasks[0].tier).toBe('2')
  expect(() => fleetSnapshot('{}')).toThrow()
  expect(() => fleetSnapshot(JSON.stringify({ ...row, agentCount: 0 }))).toThrow()
})

function boundaries(on) {
  const clock = mock.clock(on, { now: 1000 })
  mock.env(on, { HOME: '/test-home' })
  const saved = new Map()
  const commands = []
  let compactCalls = 0
  on('session.id', () => ({ value: 'seat' }))
  on('session.cwd', () => ({ value: '/workspace' }))
  on('session.model', () => ({ value: 'claude-opus-5-5[1m]' }))
  on('session.usage', () => ({ value: null }))
  on('store.get', ($, e) => ({ value: saved.get(e.key) }))
  on('store.set', ($, e) => { saved.set(e.key, e.value); return { value: undefined } })
  on('fs.write', () => ({ value: undefined }))
  on('command.register', ($, e) => { commands.push(e); return { value: undefined } })
  on('process.run', () => ({ value: { exitCode: 0, stdout: JSON.stringify({ schemaVersion: 1, sampledAt: 1000,
    agentCount: 1, taskCount: 1, agents: [{ name: 'seat', tier: 'worker' }],
    tasks: [{ id: 'T1', title: 'task', status: 'building', tier: 2 }], warnings: [] }), stderr: '' } }))
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('ui.toast', () => ({ value: undefined }))
  on('session.start', () => ({ cwd: '/workspace' }))
  on('session.compact', () => { compactCalls++; return { messages: [], tokensBefore: 1000, tokensAfter: 100 } })
  return { clock, saved, commands, compactCalls: () => compactCalls }
}

test('immediate commands save provenance then schedule native compact without a prompt', async ($, on) => {
  const f = boundaries(on)
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/workspace' })
  expect(f.commands.map(c => [c.name, c.immediate])).toEqual([['tick', true], ['handoff', true], ['compact-seat', true]])
  expect((await $.command.run({ command: 'tick', args: '' })).text).toMatch(/1 live seats, 1 active cards/)
  await $.command.run({ command: 'handoff', args: '' })
  expect(f.saved.get('handoff.v1.seat').inboxAvailable).toBe(false)
  expect(f.saved.get('handoff.v1.seat').narrative).toBe(false)
  await $.command.run({ command: 'compact-seat', args: '' })
  expect(f.compactCalls()).toBe(0)
  await f.clock.settle()
  expect(f.compactCalls()).toBe(1)
})
