// Deterministic pure-rule fallback; NOT a Claude Mods host/runtime receipt.
import assert from 'node:assert/strict'
import { fleetSnapshot, spawnDenial } from '../hooks/mods/fleet.mjs'
const valid = { prompt: 'Agent-Tier: worker\n', model: 'claude-opus-5-5[1m]', cwd: '/workspace', parentModel: 'claude-opus-5-5[1m]' }
for (const model of [undefined, 'opus', 'sonnet', 'haiku', 'fable', 'inherit', 'claude-opus-5-5[1m]', 'claude-sonnet-5-5[1m]', 'claude-haiku-5-5[1m]']) {
  const denial = spawnDenial({ ...valid, model }, valid.cwd)
  assert.match(denial, /Agent\(\) subagents are disabled by fleet policy/)
  assert.match(denial, /liteharness spawn --split/)
}
for (const prompt of ['', 'Agent-Tier: unknown', 'Agent-Tier: worker\nAgent-Tier: leader']) assert.match(spawnDenial({ ...valid, prompt }, valid.cwd), /disabled by fleet policy/)
for (const cwd of ['', '.', 'relative/path', 'C:relative', '/workspace\n']) assert.match(spawnDenial({ ...valid, cwd }, cwd), /<absolute-owned-worktree>/)
for (const cwd of ['/workspace', 'C:\\workspace', '\\\\server\\share\\work']) assert.match(spawnDenial({ ...valid, cwd }, cwd), /disabled by fleet policy/)
assert.match(spawnDenial({ ...valid, fork: true }, '/workspace'), /disabled by fleet policy/)
assert.match(spawnDenial({ ...valid, cwd: '/other' }, '/workspace'), /--cwd '\/workspace'/)
assert.match(spawnDenial(undefined), /disabled by fleet policy/)
const row = { schemaVersion: 1, sampledAt: 1000, agentCount: 102, taskCount: 1,
  agents: Array.from({ length: 102 }, () => ({ name: 'seat\u001b[31m', tier: 'worker' })),
  tasks: [{ id: 'T1', title: 'task', status: 'building', assignee: 'seat', tier: 2 }], warnings: [] }
const snapshot = fleetSnapshot(JSON.stringify(row))
assert.equal(snapshot.agents.length, 100)
assert.equal(snapshot.agentCount, 102)
assert.equal(snapshot.agents[0].name, 'seat [31m')
assert.equal(snapshot.tasks[0].tier, '2')
assert.throws(() => fleetSnapshot('{}'))
assert.throws(() => fleetSnapshot(JSON.stringify({ ...row, agentCount: 0 })))
console.log('fleet pure-rule assertions passed (no Mods host, no spawning)')
