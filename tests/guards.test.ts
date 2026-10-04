import { expect, test } from 'claude-code/testing'

// Native-host fixtures: no subprocess or submitted tool command runs. The
// rollout-disabled host currently prevents executing these tests locally.
function fixture(on, reply, options: { fail?: boolean; decision?: string } = {}) {
  let ran = 0
  const queries: any[] = []
  on('session.cwd', () => ({ value: '/owned' }))
  on('session.id', () => ({ value: 'seat' }))
  on('process.run', ($, e) => {
    queries.push(JSON.parse(e.init.stdin))
    if (options.fail) return { deny: 'runner unavailable' }
    return { value: { exitCode: 0, stdout: JSON.stringify(reply), stderr: '' } }
  })
  on('tool.call', ($, e) => { ran += 1; return { result: 'fixture executed' } })
  on('tool.check', () => ({ decision: options.decision || 'ask' }))
  return { queries, ran: () => ran }
}

const clean = { protocol: 1, deny: null, allowOwnWrite: false, command: null }

test('guard floor blocks engine tool call before fixture execution', async ($, on) => {
  const f = fixture(on, { ...clean, deny: 'floor' })
  const result = await $.tool.call({ tool: 'Bash', command: 'fixture command' })
  expect(result.deny).toBe('floor')
  expect(f.ran()).toBe(0)
  expect(f.queries[0].cwd).toBe('/owned')
})

test('runner failure is refusal not downstream execution', async ($, on) => {
  const f = fixture(on, clean, { fail: true })
  const result = await $.tool.call({ tool: 'Bash', command: 'fixture command' })
  expect(result.deny).toMatch(/guard unavailable/)
  expect(f.ran()).toBe(0)
})

test('ownership proof can allow ask but never override deny', async ($, on) => {
  fixture(on, { ...clean, allowOwnWrite: true }, { decision: 'deny' })
  const result = await $.tool.check({ tool: 'Write', input: { file_path: '/owned/a' } })
  expect(result.decision).toBe('deny')
})
