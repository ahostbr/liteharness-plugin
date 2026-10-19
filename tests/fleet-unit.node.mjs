// Deterministic pure-rule fallback; NOT a Claude Mods host/runtime receipt.
import assert from 'node:assert/strict'
import { fleetSnapshot, spawnDenial } from '../hooks/mods/fleet.mjs'
const valid = { prompt: 'no tier line', model: 'claude-opus-5-5[1m]', cwd: '/workspace', parentModel: 'claude-opus-5-5[1m]' }
// Allowed: any model value at all (the host passes its own enum or nothing; fable included); no Agent-Tier/Agent-Role line.
for (const model of [undefined, null, 'sonnet', 'haiku', 'opus', 'claude-sonnet-5-5', 'claude-haiku-5-5', 'claude-opus-5-5',
  'claude-sonnet-5-5[1m]', 'claude-haiku-5-5[1m]', 'claude-opus-5-5[1m]', 'fable', 'claude-fable-5-1[1m]', 'inherit', 'gpt-5', '']) {
  assert.equal(spawnDenial({ ...valid, model }, valid.cwd), null, 'allowed model ' + model)
}
for (const prompt of [undefined, '', 'Agent-Tier: unknown', 'Agent-Tier: worker\nAgent-Tier: leader']) assert.equal(spawnDenial({ ...valid, prompt }, valid.cwd), null)
assert.equal(spawnDenial({ model: undefined, prompt: undefined, cwd: undefined }, valid.cwd), null, 'host call with no model and no cwd')
assert.equal(spawnDenial({ ...valid, fork: true, parentModel: 'gpt-5' }, valid.cwd), null)
assert.equal(spawnDenial({ ...valid, cwd: 'C:\\Workspace\\' }, 'c:/workspace'), null, 'same Windows directory, other spelling')
// The session directory or anything inside it runs (isolation:"worktree" lives under the repo); the rest is refused.
assert.equal(spawnDenial({ ...valid, cwd: '/workspace/.claude/worktrees/agent-x' }, '/workspace'), null)
assert.equal(spawnDenial({ ...valid, cwd: 'C:\\Repo\\.claude\\worktrees\\X' }, 'c:/repo/'), null)
for (const [cwd, owned] of [['/workspace-evil', '/workspace'], ['/workspace2/x', '/workspace'], ['/Workspace/x', '/workspace'],
  ['C:/repo-evil', 'C:/repo'], ['C:/repo-evil/x', 'c:\\repo'], ['C:/', 'C:/repo']]) {
  assert.match(spawnDenial({ ...valid, cwd }, owned), /cwd must be the session's own directory or inside it/, cwd)
}
for (const cwd of ['/other', 'relative/path', 'C:relative', '/workspace/../other']) assert.match(spawnDenial({ ...valid, cwd }, valid.cwd), /cwd must be the session/)
for (const owned of [null, undefined, '', '.', 'relative/path', '/workspace\n']) assert.match(spawnDenial({ ...valid, cwd: undefined }, owned), /cwd must be the session/)
assert.match(spawnDenial(undefined), /cwd must be the session/)
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
