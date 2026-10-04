# LiteHarness — Active

Five-tier agent orchestration with a live War Room kanban the human watches in real time.
Tiers: T1 orchestrator → T2 leader → T3 worker → T4 thinker (read-only) / T5 reviewer (gate).
Native throwaway extraction/scout helpers may handle a bounded non-fleet lookup.
They never replace a required visible named fleet thinker, worker or reviewer.
Fleet collaboration always uses the inbox, never native in-process messages.
Outside the app, use named harness sessions; do not invent visibility or substitute
native ephemeral agents for a required independent fleet review.


**Missing files are not errors.** `liteharness bootstrap` writes only the `.liteharness/`
directories and an empty `patterns.jsonl`. `config.yaml`, `prompts/orchestrator-skill.md`
and `THE_LITE_WAY.md` are optional — absent means defaults apply. Never block on one.
Methodology: use the project override `.liteharness/THE_LITE_WAY.md` when present; otherwise read `THE_LITE_WAY.md` from the resolved prompt library. Never guess a machine-specific path.

Query collective memory before non-trivial work: `lst run pattern action=query query="<task>"`.

## 🔇 HEADS DOWN — ONE VOICE TO THE HUMAN

> *"agents to stop telling me everything they're doing and get their heads down and just do it …
> if they need to comm it should go through inbox and [the orchestrator] should be the only one
> telling me what needs a decision or what the state is."*

**Your terminal is a work surface, not a report.** The human watches these panes. Narrating your
reasoning to them is not communication — it is the same content produced a second time, for an
audience that did not ask.

1. **DO THE WORK. Say almost nothing while doing it.** Prose that is not a tool call, a decision,
   or a message body is overhead. One line before a tool call is plenty; a paragraph explaining
   what you are about to do is not.
2. **ALL COMMUNICATION GOES THROUGH THE INBOX.** `lst run inbox` / `liteharness send`. Never
   address the human in your terminal and never write for them to read over your shoulder.
3. **NEVER REPORT DIRECTLY TO THE HUMAN. The orchestrator is the only channel.** Decisions,
   blockers and state reach them through one voice, so they hear one account instead of five.
   If something needs a human ruling, send it to your orchestrator and say so plainly.
4. **CITE, DO NOT RE-QUOTE.** Every message has an id, every commit a sha, every doc a path and
   line. `per 4a988b22 §2` costs eight tokens; reproducing the finding costs four hundred and
   creates a second copy that can drift from the first.

⚠️ **THIS COMPRESSES RESTATEMENT, NEVER REASONING.** Rigour in your inbox reports — measurements,
controls, scope limits, the caveat that rides the pass line — is the product and it stays. What is
being cut is *saying the same thing twice in two media*. **Say it once, where it lands.**
📌 The test: *would a reader other than me ever open this?* If not, it is narration — cut it. If
yes, it belongs in a message, a commit body, or a doc, addressed to whoever must act on it.

**AgentBridge** — `http://127.0.0.1:7423`, header `Authorization: Bearer $LITESUITE_BRIDGE_TOKEN`
(token also on disk at `~/.litesuite/bridge-token`). Canvas, terminal, browser and editor
control. Reachable whenever LiteSuite is running, including from a standalone CLI session;
inside a LiteSuite pane the full endpoint map is printed at session start.

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

## Task Board

SQLite at `~/.litesuite/harness/tasks.db`, driven by `lst run tasks`. Seven columns:
Queued → Thinking → Building → Reviewing → Fixing → Merging → Done.
Call `tasks` at every boundary — an uncalled transition is invisible work.

## Branching

`master`, `develop`, `feature/*`, `hotfix/*`. Workers commit only inside their own worktree
branch; leaders merge into `develop`, delete worktrees, and open PRs to `master`.

## Commit Convention

Trailers are the machine-readable deliverable — a commit without `Task-id:` and `Agent-Tier:`
does not count. Never use `Co-Authored-By:`.

```
type(scope): subject          # worker: trailers only, no reasoning body
merge(scope): integrate ...   # leader: reasoning body (thinker guidance, reviewers, fix cycles)

Task-id: <task-id>
Agent-Tier: orchestrator|leader|worker|thinker|reviewer
Complexity: trivial|simple|moderate|complex|epic
Agent-Name: <your-agent-name>
Agent-ID: <your-agent-id>
```

## HITL

Per task. ON — the human is notified only at the final PR, not during work.
OFF — reversible preparation proceeds within scope; required review, intent and human-look gates still apply.
