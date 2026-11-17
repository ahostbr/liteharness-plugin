// Deterministic pure-rule fallback; NOT a Claude Mods host/runtime receipt.
import assert from 'node:assert/strict'
import { fleetSnapshot } from '../hooks/mods/fleet.mjs'
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
