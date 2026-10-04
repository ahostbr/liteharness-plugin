# The Lite Way

Think before building. Verify against the human's actual intent before shipping.

## Per-card process and thinking

Role rank is not the card's process tier. At intake ask the human to choose both
process tier and thinking level; thinking is a separate choice informed by usage,
credits and any active model/thinking floor. Pass both choices with the trunk.

| Process tier | Team and merge review | Expected duration (alert only) |
|---|---|---|
| 1 — Quick | One seat builds/self-reviews; leader reads diff | 30 minutes |
| 2 — Standard | One seat thinks/builds/self-reviews; leader reviews diff, at most one fix round | 2 hours |
| 3 — Deep | Worker + thinker(s) + separate visible named reviewer with VERDICT | Half a day |

There is **no time limit**. Expected durations are alerts for the orchestrator,
not deadlines or permission to expand scope. At every tier check the current
human intent before merging. An explicitly requested separate review still applies
at any tier. Run focused affected checks, not full suites by habit.

## Named persistent fleet seats

A name identifies one agent and its durable conversation. Follow-up work returns
to that same named seat. Message a live seat by inbox; resume it only after its
process is gone: `liteharness spawn --split --resume <Name>`.
Never replace a seat under a fresh name or self-retire. Every fresh fleet spawn
has an explicit `--cwd <repo root>`; `liteharness names --list` shows the saved
identity, conversation and cwd. Lifecycle changes require the leader/orchestrator.

**Fleet lifecycle safety:** Never close a fleet seat by leafId or paneId. Until
that lifecycle path is corrected, the only permitted close is an explicitly
authorized `DELETE /pty/<sessionId>` after a fresh `GET /pty/list` proves an
exact `harnessAgentId` match to the intended named seat. A guessed/stale session,
leaf or pane is not an identity check. Never self-retire.


## Merge and human-look gate

Worktree edits, tests and commits are reversible and autonomous within the agreed
scope. Review gates the merge, not an own-worktree commit. Before each merge,
compare the current human words/requirements against the diff and evidence:
one-line intent check for process tiers 1–2; full intent gate for tier 3.
Required review, intent approval and release approval are distinct gates.
A merged candidate remains **reviewing** until the human has seen the result;
APPROVE, candidate-ready, a successful merge or model judgement is not Done.
Editor restart/rebuild, deletions, downloads, VRAM loads, external side effects
and public pushes retain their separate approval gates. Autonomy/HITL mode never
bypasses a required merge intent gate or human-look completion condition.

Native throwaway extraction/scout helpers may handle a bounded non-fleet lookup.
They never replace a required visible named fleet thinker, worker or reviewer.
Fleet collaboration always uses the inbox, never native in-process messages.
Outside the app, use named harness sessions; do not invent visibility or substitute
native ephemeral agents for a required independent fleet review.
