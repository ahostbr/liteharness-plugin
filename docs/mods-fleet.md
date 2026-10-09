# Fleet pane and local seat commands

This feature extends the existing LiteHarness Claude Code mod (Claude Code
2.1.287+). It is not an alternate plugin or a replacement for Python hooks.

## Behavior

- `/tick`: refresh a read-only fleet/board snapshot and open the fleet pane.
  This does **not** tick intent criteria, confirm human acceptance, or change
  task statuses. Snapshot counts distinguish displayed rows from total rows.
- `/handoff`: persist a bounded, session-scoped provenance snapshot. This is
  not a model-authored narrative handoff. Missing inbox/context integration
  must be labeled unavailable, never represented as verified empty mail.
- `/compact-seat`: persist that snapshot before explicitly scheduling native
  compaction through the existing compaction lifecycle. Command dispatch does
  not submit a Claude prompt or start a normal turn; native compaction may use
  model capacity. Persistence failure must prevent compaction.

Commands use `immediate: true` so they can execute while Claude is working.
Compaction itself must wait for an idle turn. No automatic compaction is added.

## Boundaries

`hooks/mods/fleet.mjs` contains only pure snapshot parsing and spawn-brief
validation. Mods API-bearing helpers and event registrations belong in the
existing `hooks/register.mjs`: Claude's static analyzer cannot pass `$` to an
imported helper. Lifecycle events are composed once, not registered twice.

The snapshot adapter is `python -m liteharness.mod_fleet` in the LiteHarness
Python distribution. It reads the existing agent presence registry using
`discover`'s 600-second heartbeat/known-owner PID rules. It opens the LiteSuite
kanban database with SQLite `mode=ro` and `query_only=ON`; it does not create a
missing database or mutate tasks. Existing `LITESUITE_STATE_HOME` selects board
state. At most 100 agents and 100 non-done cards are displayed. Missing readers,
missing database, and unreadable presence records are explicit failures or
warnings, not a fabricated empty healthy board.

## Spawn contract

The installed 2.1.287 `agent.spawn` event exposes no harness tier property.
Therefore the explicit tier is represented by exactly one canonical brief line:

```text
Agent-Tier: worker
```

Accepted tiers: orchestrator, leader, worker, thinker, reviewer. The caller must
also supply one of the explicit `[1m]` Opus IDs from the existing launch alias
catalog: `claude-opus-5-5[1m]`, `claude-opus-5[1m]`,
`claude-opus-4-8[1m]`, or `claude-opus-4-6[1m]`. The absolute `cwd` must match
the current session scope; both paths are resolved with `fs.stat(resolve:true)`
and must resolve to the same non-link directory. Dot segments, aliases,
`inherit`, omitted fields, and relative directories are refused. A fork ignores
a requested model, so its parent must already match that explicit model.
The host remains responsible for model availability. This validates declared
metadata, **not trusted identity or privilege assignment**; injected prompt
prose cannot confer authority. Validation is not spawn authorization, and does
not override the common deny floor or merge/human gates.

## Integration and validation limits

The shared entrypoint composes inbox/context snapshots from ModsB and this
feature's pure helpers. The tool guard mod (ModsC) was removed;
this plugin installs no tool guard. Replace the standalone
`fleetInboxSnapshot()` null seam with ModsB's same-file `inboxSnapshot()`:
`{ schemaVersion, sessionId, agentId, enabled, status, pendingIds,
acceptedIds, lastAcceptedAt, paneId }`. Accepted means entered/queued, **not
processed**. Derive availability from a matching session identity and explicit
status, rather than asserting availability unconditionally. Standalone D saves
`inbox:null, inboxAvailable:false` and reports this limitation. This feature
introduces no tool-call handler. Manifest/hooks wiring and all four plugin
version sites are coordinated by the leader, not independently bumped here.

Fixtures inject process replies, storage, clocks, and compaction results. No
real agents are spawned by tests. Node pure-rule tests are not a substitute
for `claude plugin test`, an installed runtime proof, or the human's final look.

Official source contracts: Claude Code docs `plugins/mods/{create,reference,
api,interface,test}.md`; generated declarations for Claude Code 2.1.287 take
precedence over older GitHub copies. The foundation already schedules native
compaction with `clock.after` outside the 10-second UI event budget and guards
job identity across clear/resume. Preserve that lifecycle.
