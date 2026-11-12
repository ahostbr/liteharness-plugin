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
| 3 — Deep | Worker + thinker(s); a separate visible named reviewer ONLY when the user's own words on the card ask for a review | Half a day |

There is **no time limit**. Expected durations are alerts for the orchestrator,
not deadlines or permission to expand scope. At every tier check the current
human intent before merging. An explicitly requested separate review still applies
at any tier. Run focused affected checks, not full suites by habit.

## Named persistent fleet seats

A name identifies one agent and its durable conversation. Follow-up work returns
to that same named seat. Message a live seat by inbox; resume it only after its
process is gone: `liteharness spawn --split --resume <Name>`.
Never replace a seat under a fresh name. Every fresh fleet spawn
has an explicit `--cwd <repo root>`; `liteharness names --list` shows the saved
identity, conversation and cwd.



## Merge and human-look gate

Worktree edits, tests and commits are reversible and autonomous within the agreed
scope. Review gates the merge, not an own-worktree commit. Before each merge,
compare the current human words/requirements against the diff and evidence:
one-line intent check for process tiers 1–2; full intent gate for tier 3.
Required review and intent approval are distinct gates. Release approval, the final
develop → master PR, follows the HITL mode: with HITL ON the human approves and merges it;
with HITL OFF (fully autonomous) no human gates it and the orchestrator completes it once
the per-merge intent checks have passed.
A merged candidate remains **reviewing** until the human has seen the result (HITL ON);
APPROVE, candidate-ready, a successful merge or model judgement is not Done. With HITL OFF
(fully autonomous) there is no human look: the orchestrator completes the card once review,
validation and the per-merge intent checks have passed.
Editor restart/rebuild, deletions, downloads, VRAM loads, external side effects
and public pushes retain their separate approval gates. Autonomy/HITL mode never
bypasses a required merge intent gate; only HITL ON adds the human-look completion condition.

Native throwaway extraction/scout helpers may handle a bounded non-fleet lookup.
They never replace a required visible named fleet thinker, worker or reviewer.
Fleet collaboration always uses the inbox, never native in-process messages.
Outside the app, use named harness sessions; do not invent visibility or substitute
native ephemeral agents for a required independent fleet review.
