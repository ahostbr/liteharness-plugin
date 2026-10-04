# Claude cache/context band (T0314)

This source mod is part of the existing `liteharness` plugin. It requires Claude
Code **2.1.287+**. It draws an AbovePrompt band in terminal and Desktop Claude
seats, reads `$.session.usage()` for context percentage, and offers a **Compact**
button. Hosts without mod drawing still publish telemetry. No LiteTUI maildir or
Python settings hook is replaced. Installation, release and live acceptance are
separate steps; this change does not perform them.

## What the timer means

**Cache estimate** is an assumed one-hour TTL, not provider cache-expiry evidence
and not a promise of cache hits. `lastRequestAt` is the clock at initiation of a
main-loop `turn.step`, recorded only after that request returns usage and a
successful stop reason. A long request therefore consumes part of the hour
before the countdown appears. Subagent/fork requests, failed/interrupted requests,
refusals, session opening, renders and usage polls never start or refresh it.
The stream chunks and final request result pass through unchanged.

A successful response without usage is conservatively unknown. No transcript
history is mined to infer earlier requests. Unknown is not cold and missing
context is not zero. The button invokes `$.session.compact()` only when pressed,
refuses a currently working turn, and reports skips/failures. Pressing it schedules native compaction through `$.clock.after(0, callback)` and returns without awaiting the native job; the background callback refreshes metrics and resets the busy label on completion or error. Native compaction can exceed the 10-second ui.press budget. A real disposable-seat press exposed a timeout at 10 seconds even though native compact completed around 30 seconds; this is why the work is now scheduled outside the press event. Busy/job state prevents duplicate pending presses; session end cancels a not-yet-dispatched compact and resets the label. Completion checks job generation and session identity before refreshing, so an old compact completing after clear/resume cannot mutate replacement-session telemetry or reset a newer job. The documented timer callback runs outside the press event and is cancelled on module reload. Engine usage may legitimately omit tokens/percent just after compact; those remain unknown, never fabricated from the compact token count. There is no
percentage threshold or automatic compact. The final two minutes of a warm estimate are amber (yellow terminal color); cold/unknown are not amber.

## Machine-readable retrieval

Per session, the mod saves plugin-private `$.store` key `usage.v1.<sessionId>` for
reload recovery and writes numeric JSON to
`~/.liteharness/mods/usage/<sessionId>.json`. The home directory comes from
`USERPROFILE`, then `HOME`. Session IDs must match
`^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$`; arbitrary paths are refused.

An external orchestrator tick can use the companion Python package reader:

```sh
python -m liteharness.mod_usage --session SESSION_ID
python -m liteharness.mod_usage --all
```

The Python reader ships separately with the Python package: a plugin-only update
does not install it. A consumer without that reader may read the file directly
but must validate schema/identity and handle missing/partial JSON. `$.store` alone
is **not** claimed to be externally readable. Neither route requires transcript
access, screenshots, Bridge credentials, or a model turn.

Schema version 1 (null means unavailable):

```json
{
  "schemaVersion": 1,
  "source": "claude-code-mod",
  "sessionId": "seat",
  "sampledAt": 1700000000000,
  "usageObservedAt": 1700000000000,
  "usageAvailable": true,
  "sessionStartedAt": null,
  "active": true,
  "context": { "tokens": 1000, "window": 200000, "percent": 0.5 },
  "cache": {
    "estimated": true,
    "basis": "successful-main-turn-step-start",
    "ttlMs": 3600000,
    "lastRequestAt": 1699999990000,
    "expiresAt": 1700003590000,
    "remainingMs": 3590000,
    "state": "warm"
  }
}
```

All timestamps are epoch milliseconds. `usageObservedAt` is the time usage was
sampled, not model cache time. `sessionStartedAt` is populated only when the API
provides a valid numeric `startedAt`. Only explicitly whitelisted context
numbers are copied. No prompts, transcript, cwd, costs, secrets or environment
values are published. Warm/cold/unknown describes the estimate, never authority
to spend, wake a seat, compact, or approve a tool.

Sampling occurs at start/reload, successful requests, session.measure, compact
completion and every **15 seconds** while idle. Refreshes serialize to prevent an
older poll overwriting a newer request. Renders derive countdown from the clock
but never change lastRequestAt. The band preserves downstream mods' drawing.
Changing session identity loads only that session's key. `/clear` and `/resume`
keep identity polling because session.start does not fire for those actions;
exit cancels the timer before any awaited publication, even when the final sample fails. A lifecycle generation guard drops queued callbacks from the ended generation; clear/resume cannot republish the ended identity as active while awaiting replacement. Reload cancels host timers and restores persisted state.

`$.fs.write` is **not atomic**. The reader limits a file to 64 KiB, validates
identity/schema/numeric bounds, discards extra fields and reports `missing`,
`unavailable`, `stale`, `ended`, or `ok` with `metrics`. A failed publication is
visible in the band. An external reader cannot see that in-memory error; an old
file becomes stale rather than being trusted as fresh. A sample older than
60 seconds is stale. Remaining time is recalculated at read time, not trusted
from saved remainingMs. Stale/ended data remains distinguishable even if its
estimated timer is warm.

`--all` stats candidate filenames and selects the newest **256** by mtime with a
deterministic session-ID tiebreaker, then reads only those. The response reports
`truncated` and `candidates`; incomplete discovery must not be interpreted as
an absent seat. `--session` bypasses that discovery cap. Files older than 24 hours
are omitted from discovery (mtime and valid sample age), but never deleted.
This is a **discoverability filter**, not disk retention. Physical file count and
plugin store growth are not bounded; explicit maintenance/pruning is follow-up
work, not an automatic deletion in this card. Metadata enumeration scales with
file count even though body reads and selection memory are bounded.

## Shared extension seams

- `hooks/hooks.json` contains one `modules: ["./register.mjs"]` entry alongside
  unchanged Python hook entries.
- `hooks/register.mjs` owns API-bearing code and the single unmatched
  session.start/session.end registrations. B/D/E add explicit same-file lifecycle
  helper calls there; they must not register duplicate unmatched lifecycle hooks.
- `hooks/mods/usage-schema.mjs` exports pure snapshot/countdown/identity helpers.
  Imported helpers must **not** take `$`: Claude's static analyzer permits passing
  it only to top-level helpers in the same entrypoint file.
- New features use unique event matchers and preserve downstream AbovePrompt
  content. Shared register edits are applied serially by the leader.
- A has **no tool.call, tool.check, tool approval, model.complete or process API**.
  Any future tool.call path must execute the real deny-floor first. Origin
  PreToolUse has an observation hook, not deny_gate; this mod makes no security
  parity claim and does not fabricate a security floor.

## Packaging and versions

The plugin source already supplies `.claude-plugin/plugin.json`,
`.claude-plugin/marketplace.json` and `.codex-plugin/plugin.json`. Version
**1.0.19** is the local integration candidate at all four declaration sites (marketplace root and
plugin entry, Claude manifest, Codex manifest). Existing `scripts/bump_version.py`,
`check_version_bump.py`, and `check_version_consistency.py` govern releases.
The Python package's `pyproject.toml` version **0.4.3** is independent. No duplicate
catalog manifest, marketplace, packaging generator, or source version is added.
The companion reader is a normal `liteharness` Python module. Coordinated release
and installed-seat validation require separate approval.

## Evidence and limits

Claude 2.1.287's installed `claude plugin test` host exercises real registration,
render/mount/press, generator and timer machinery with stubbed external calls;
these are fixture tests, not installed-seat proof. The public TypeScript reference
currently says **2.1.277**. Exact generated types require loading a scratch plugin
in the installed build, reserved for the leader's separately scheduled probe.

Use an explicit manifest target for plugin validation. `claude plugin validate .`
selects this repository's **marketplace** and can report success without analyzing
mods. Explicit plugin-manifest validation reports clean A hooks but four existing
origin diagnostics: YAML frontmatter in `agents/pentest-pre-recon.md`,
`commands/loadnow.md`, `commands/savenow.md`; and `.mcp.json`'s URL server missing
`type`. An archive of origin reproduces those diagnostics. They are not fixed by
A and do not prove whole-plugin unloadability. A minimal manifest/hooks/mods
artifact validates successfully; that proves only the A bundle's static contract,
not every plugin component or live usability.
