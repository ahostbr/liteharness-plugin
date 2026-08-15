# LiteHarness — Active

Five-tier agent orchestration with a live War Room kanban the human watches in real time.
Tiers: T1 orchestrator → T2 leader → T3 worker → T4 thinker (read-only) / T5 reviewer (gate).
Scouts are throwaway Haiku sub-agents any tier may dispatch.

**Missing files are not errors.** `liteharness bootstrap` writes only the `.liteharness/`
directories and an empty `patterns.jsonl`. `config.yaml`, `prompts/orchestrator-skill.md`
and `THE_LITE_WAY.md` are optional — absent means defaults apply. Never block on one.
Methodology, first that exists: `.liteharness/THE_LITE_WAY.md` → `resources/litesuite/THE_LITE_WAY.md` → skip.

Query collective memory before non-trivial work: `lst run pattern action=query query="<task>"`.

## 🔇 HEADS DOWN — ONE VOICE TO THE HUMAN (RULING, Ryan 2026-08-15)

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
OFF — the orchestrator sends a polymathic PR reviewer and auto-decides.
