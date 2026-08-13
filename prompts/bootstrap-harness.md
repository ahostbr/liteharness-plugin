# LiteHarness — Active

Five-tier agent orchestration with a live War Room kanban the human watches in real time.
Tiers: T1 orchestrator → T2 leader → T3 worker → T4 thinker (read-only) / T5 reviewer (gate).
Scouts are throwaway Haiku sub-agents any tier may dispatch.

**Missing files are not errors.** `liteharness bootstrap` writes only the `.liteharness/`
directories and an empty `patterns.jsonl`. `config.yaml`, `prompts/orchestrator-skill.md`
and `THE_LITE_WAY.md` are optional — absent means defaults apply. Never block on one.
Methodology, first that exists: `.liteharness/THE_LITE_WAY.md` → `resources/litesuite/THE_LITE_WAY.md` → skip.

Query collective memory before non-trivial work: `lst run pattern action=query query="<task>"`.

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
