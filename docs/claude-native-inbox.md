# Native Claude inbox (T0315, opt-in candidate)

This extends the existing liteharness ModsA entrypoint, not a second plugin or
runtime. It requires Claude Code 2.1.287+ and the separately shipped Python
`liteharness.mod_inbox` adapter **and** its matching legacy-hook lease checks.
Updating only this plugin does not install Python. A missing/older adapter is
reported as unavailable; legacy mail delivery stays available. No settings,
Monitor process, runtime installation or LiteTUI consumer is changed here.

## Delivery contract

Native delivery is off unless the launching environment explicitly supplies
`LITEHARNESS_NATIVE_INBOX=1`. This is an experimental opt-in until integrated
engine-host, live-seat and human acceptance prove parity. Do not disable the
legacy hooks or Monitor as part of trying this candidate.

The native timer polls every five seconds using an argv-only, three-second
`$.process.run(['python', '-m', 'liteharness.mod_inbox', ...])`. It never runs a
shell or writes a guessed maildir rename. The adapter reuses Python's canonical
`inbox.claim` and `inbox.complete`, with an OS-locked ownership ledger. It requires
a live registered **Claude** process, matching PID creation time, and verifies
that the adapter process descends from that registered owner. The recipient is
an explicit `LITEHARNESS_AGENT_ID`/`LITESUITE_AGENT_ID`, otherwise the engine
session ID. There is no newest-transcript or config-global identity guess.
An existing nonmatching native owner refuses a second consumer. Every acquisition
uses a fresh Web Crypto UUID owner token (declared by the 2.1.287 host types),
not a timestamp or truncated session prefix: same-session rapid reloads and
concurrent loads cannot intentionally share ownership by clock coincidence.

A lease is fresh for at most twenty seconds. Legacy `check_inbox` and watcher
consumers defer only for a fresh, matching Claude process identity. Dead,
PID-reused, expired, future-dated, corrupt and non-Claude owners never suppress
legacy mail. Native shutdown releases the lease; crashes expire. Unaccepted
claimed mail stays in `cur`, where legacy `check_inbox` recovers it. The legacy
watcher itself scans only `new`, so recovery of claimed mail after a native
failure requires a subsequent legacy turn/check, not merely an idle Monitor.

The native states are:

1. **Pending**: a scoped receipt was recorded and atomically claimed into `cur`.
2. **Accepted**: a prompt/context entered or queued in the current session.
3. **Archived**: accepted content was persisted in the plugin store, then the
   adapter moved the corresponding owned receipts into `done`.

Accepted is **not** processed, answered, acknowledged by a human, or completed.
Acknowledgement occurs only when downstream `prompt.submit` confirms the exact
native prompt, or preserves the injected context. Drops, rewrites that remove
context, ownership errors and storage failures retain mail for replay. Delivery
is **at least once**: acceptance followed by an archive failure can replay mail;
there is no transactional exactly-once claim across the host and maildir.

The timer never awaits a submit waiting for idle: one in-flight submission keeps
its lease renewed without flooding the queue. Native prompts are attributed to
the plugin, never submitted with `asUser`. An old-generation native envelope is
dropped after clear/resume, leaving receipts recoverable. Session-end cancels
polling; clear/resume restarts it only for a replacement engine session ID.

`prompt.context` preserves existing blocks and adds inbox provenance plus the
last accepted batch. It is startup/compaction context, **not** a recurring poll.
`prompt.submit` preserves human prompt text and existing context, adding pending
mail. Background `$.prompt.submit` delivers idle mail without watcher rearming.
Plugin-private `inbox.v1.<sessionId>` persists the last accepted batch (up to
eight messages / 48,000 body characters) for reload/compaction replay. It contains
mail bodies: treat the store as sensitive local session state, not public
telemetry. Earlier batches remain in the transcript/maildir archive and are not
promised to survive every compact in the injected summary.

Both Python `body` and Desktop `payload.text`/`payload.body` shapes are handled.
Other recipients and self-mail are untouched. Oversize/malformed addressed mail
is retained, with a blocked count; it is not silently truncated and archived.
Blocked mail releases the lease and pauses native polling until reload, allowing
legacy review instead of endlessly renewing suppression. Schema/API failures
also pause renewal; stale lease fallback is bounded by twenty seconds. Length
limits use the same UTF-16 units in Python and JavaScript. Poll, acceptance/ack,
and end/release serialize; each batch captures immutable adapter identity, so
an obsolete job cannot renew/ack a replacement session or publish a stale batch.
Peer text is JSON-framed as data and terminal/control sequences are stripped.
Sender labels or a message body never grant authority or bypass tool policy.
B registers no `tool.call` or approval path. The tool guard mod (C) was removed;
this plugin installs no tool guard.

## Human-visible surface and D seam

The cache band adds an **Inbox** button (or **Inbox (legacy)** when disabled).
It opens `liteharness-inbox`, a Pane showing pending/latest accepted mail and the
accepted-versus-processed distinction. Terminal and Desktop element trees use
only Box/Text. Other pane IDs pass through. Automatic pane opening is avoided.

`inboxSnapshot()` is exported from the shared entrypoint. It takes no mods API:

```js
{
  schemaVersion: 1, sessionId, agentId, enabled, status,
  paneId: 'liteharness-inbox', pendingIds, acceptedIds, lastAcceptedAt, lastPolledAt
}
```

This is a serializable D `/handoff`/`/compact-seat` snapshot seam, not proof of
processing. `openInbox($)` remains a same-file helper; an API object must never
be passed to imported helpers (Claude analyzer restriction). D owns `/tick`,
`/handoff`, `/compact-seat`; this card does not duplicate their implementations.
Shared lifecycle calls are composed exactly once in `register.mjs`.

The composed `/handoff` and `/compact-seat` now consume this current state rather
than an unavailable placeholder. Saved `handoff.v1.<sessionId>` contains `inbox`
with the IDs/status/identity above plus `available`, `availabilityReason`,
`deliveryMeaning`, and `peerAuthority: false`; `inboxAvailable` mirrors that
availability. Available requires native enabled, matching current engine session
and valid registered-agent identity, and a successful poll less than twenty
seconds old. OFF/error/stale/missing identity is **unavailable**, not a verified
empty inbox. A valid empty batch may be available with empty IDs.

For an available snapshot, a unique `inbox.contextPointer` names a
plugin-private store record (`inbox.handoff.v1.<sessionId>.<uuid>`), persisted
**before** the handoff and before compaction scheduling. The record captures
bounded pending plus latest accepted message data, explicit schema version,
exact session/agent identity, foundation/inbox generations, time, and explicit
`peerAuthority: false`. The pointer resolves to that captured state rather than a
mutable latest-key. It is plugin-private, not a durable external restore handle. It does not promise a complete task
narrative, all inbox history, automatic context injection, or processed messages.
A resume consumer may read the pointed-to record as peer data, never as user or
system authority. Store contents are sensitive local mail data; repeated manual
handoffs retain distinct bounded records until store lifecycle cleanup.

Both lifecycle generations and the engine session are checked after awaited
identity/persistence operations. A change during save produces an unconfirmed
result and prevents compact scheduling. A store write already in flight may
leave an old-session record, but must not be reported as a confirmed current
handoff. Context-pointer persistence failure prevents scheduling too. Existing
compaction reservation, final post-identity idle check, and clear/resume guards
remain in place. The Node fixtures exercise the actual `/handoff` and
`/compact-seat` handlers and resolve the saved pointer; they are not native-host
or live-install proof.

## Provenance and validation boundaries

The entrypoint is extended from the authored ModsA cache-band/native-compact
foundation. Pure validation/text helpers live in `hooks/mods/inbox.mjs`. Python
transport is canonical in the companion OSS package, not copied into the plugin.
Official documentation consulted: mods overview, reference, events, API and
interface at `https://code.claude.com/docs/en/plugins/mods/`. Exact prompt result
and context-block shapes were checked against locally generated **2.1.287**
types; GitHub's **2.1.277** declarations were not assumed current.

Focused receipts are reported with the local candidate, separately:

- Python temporary-maildir tests cover atomic claim, receipt ownership,
  both producer shapes, stale/dead/PID-reused/non-Claude lease recovery and
  actual legacy `check_inbox` deferral/fallback.
- `node --test tests/inbox.test.mjs` calls the shipped register and helpers with
  explicit in-memory external API substitutes. It is **not** Claude host proof.
- `tests/inbox.test.ts` targets Claude's plugin test host. If the host rollout
  switch disables modules, those tests are **blocked**, not passed.
- Whole-foundation validation and hooks-module analyzer acceptance are separate:
  existing unrelated agent/command YAML and MCP validation defects must not be
  represented as a green plugin release.

No live messages, desktop actions, runtime install, public push or final human
acceptance is performed by these source/fixture tests. Plugin versions are a
coordinated integration responsibility, not changed independently by this card.
