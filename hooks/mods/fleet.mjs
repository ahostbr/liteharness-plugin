// Pure data/brief rules only. All Mods API calls belong in register.mjs.
export const FLEET_PANE = 'liteharness-fleet'
export const FLEET_LIMIT = 100
const clean = value => String(value ?? '').replace(/[\x00-\x1f\x7f-\x9f]/g, ' ').slice(0, 512)

export function fleetSnapshot(text) {
  const row = JSON.parse(text)
  if (row?.schemaVersion !== 1 || !Number.isSafeInteger(row.sampledAt) || row.sampledAt < 0 || row.sampledAt > 8_640_000_000_000_000 ||
      !Array.isArray(row.agents) || !Array.isArray(row.tasks) || !Array.isArray(row.warnings) ||
      !Number.isSafeInteger(row.agentCount) || row.agentCount < row.agents.length ||
      !Number.isSafeInteger(row.taskCount) || row.taskCount < row.tasks.length) {
    throw new Error('Invalid fleet snapshot')
  }
  return { sampledAt: row.sampledAt, agentCount: row.agentCount, taskCount: row.taskCount,
    agents: row.agents.slice(0, FLEET_LIMIT).map(a => ({
      agent_id: clean(a.agent_id), name: clean(a.name), tier: clean(a.tier), model: clean(a.model), cwd: clean(a.cwd),
    })),
    tasks: row.tasks.slice(0, FLEET_LIMIT).map(t => ({
      id: clean(t.id), title: clean(t.title), status: clean(t.status), assignee: clean(t.assignee), tier: clean(t.tier),
    })), warnings: row.warnings.slice(0, 10).map(clean) }
}

export function normalizedCwd(value) {
  if (typeof value !== 'string' || !value || /[\x00-\x1f]/.test(value)) return null
  const windows = /^[A-Za-z]:[\\/]/.test(value) || /^\\\\[^\\]+\\[^\\]+/.test(value)
  if (!windows && !/^\/(?!\/)/.test(value)) return null
  const path = windows ? value.replace(/\\/g, '/').toLowerCase() : value
  if (path.split('/').some(part => part === '.' || part === '..')) return null
  return path.replace(/\/+$/, '') || '/'
}

export function spawnDenial(e, ownedCwd) {
  // Agent() is not a fleet launcher. Neither aliases nor resolved model IDs,
  // brief metadata, forks or cwd changes can turn it into a visible split.
  // Quote for PowerShell; never interpolate the untrusted requested cwd/brief.
  const cwd = normalizedCwd(ownedCwd) && !/[\x7f-\x9f]/.test(ownedCwd)
    ? ownedCwd : '<absolute-owned-worktree>'
  const quotedCwd = "'" + cwd.replace(/['\u2018\u2019\u201a\u201b]/g, quote => quote + quote) + "'"
  const model = typeof e?.model === 'string' ? JSON.stringify(clean(e.model)) : '(not supplied)'
  return 'Agent() subagents are disabled by fleet policy. Builders, scouts and critics must be visible named splits; do not retry Agent() with different tier/model fields. ' +
    'PowerShell scout command (replace the name and brief placeholders): ' +
    'liteharness spawn --split --cli claude --tier scout --model \'claude-sonnet-5-5[1m]\' --cwd ' + quotedCwd +
    ' --name \'<fresh-task-seat>\' --cognitive feynman --prompt \'I am here to <purpose>. Task-id: <card>. Read-only scout: <brief>\'. ' +
    'Use --tier critic with Sonnet 5.5 for critics; grunt builders use --tier builder --model \'claude-haiku-5-5[1m]\' and a task-appropriate cognitive method. ' +
    'If cwd is a placeholder, replace it with the absolute owned worktree. ' +
    'Observed agent.spawn model: ' + model + '.'
}
