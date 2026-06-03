# LiteHarness — Active

This project is running under [LiteHarness](https://litesuite.dev) — a five-tier
AI agent orchestration system with a live War Room kanban board.

## Tier Hierarchy

| Tier | Role                  | Default Model | Context |
| ---- | --------------------- | ------------- | ------- |
| T1   | Orchestrator          | Opus 4.6      | 1M      |
| T2   | Leader                | Sonnet 4.6    | 1M      |
| T3   | Worker                | Sonnet 4.6    | 1M      |
| T4   | Thinker (polymathic)  | Opus 4.6      | 1M      |
| T5   | Reviewer (polymathic) | Opus 4.6      | 1M      |
| —    | Scout                 | Haiku 4.5     | 200K    |

## Required Reading

- **Methodology:** `.liteharness/THE_LITE_WAY.md` (or `resources/litesuite/THE_LITE_WAY.md`)
- **Harness config:** `.liteharness/config.yaml`
- **Orchestrator skill:** `.liteharness/prompts/orchestrator-skill.md`
- **Collective patterns:** `.liteharness/patterns.jsonl`

## Session Start Protocol

1. Read `.liteharness/config.yaml` for harness configuration and model template.
2. Load `.liteharness/prompts/orchestrator-skill.md` as your operating instruction.
3. Check `.liteharness/patterns.jsonl` for relevant past patterns before acting.
4. Use `lst run <tool>` for task management, messaging, and agent spawning. Inside LiteSuite, the AgentBridge HTTP API at `127.0.0.1:7423` provides canvas, terminal, and browser control (token: `~/.litesuite/bridge-token`).

## Ultracode Status-Line Marker

Claude Code does **not** expose the **ultracode** effort mode to child processes — it reports `xhigh` in the status-line JSON and the `CLAUDE_EFFORT` env, and sets no flag. The only entity that knows ultracode is on is **you** (the agent — via the "Ultracode is on / off" system reminder). Leave a breadcrumb so the status line can render the `ultra` badge, and keep it in sync whenever the state changes:

- **Ultracode ON:** `mkdir -p ~/.claude/ultracode && date +%s > ~/.claude/ultracode/"$CLAUDE_CODE_SESSION_ID"`
- **Ultracode OFF:** `rm -f ~/.claude/ultracode/"$CLAUDE_CODE_SESSION_ID"`

Session-keyed (`$CLAUDE_CODE_SESSION_ID`) — orphans from ended sessions are harmless. One-line housekeeping; it powers the purple `ultra` badge (vs plain `xhigh`).

## Task Board

Tasks are stored in SQLite (`~/.litesuite/harness/tasks.db`), managed via `lst run tasks`.

**7 kanban columns** (visible in War Room):
Queued → Thinking → Building → Reviewing → Fixing → Merging → Done

Every agent MUST call `tasks` at task boundaries — the human watches the kanban in real-time.

## Branching

4-branch flow: `master`, `develop`, `features/*`, `hotfix/*`

- Workers operate in isolated git worktrees on feature branches
- Leaders merge worktrees into develop and delete them
- Leaders create PRs (develop → master)

## Commit Convention

**Worker commits** — conventional + trailers only:

```
type(scope): subject

Task-id: <task-id>
Agent-Tier: worker
Complexity: trivial|simple|moderate|complex|epic
Agent-Name: <your-agent-name>
Agent-ID: <your-agent-id>
```

**Leader merge commits** — full reasoning body:

```
merge(scope): integrate <components>

Thinker guidance: <what polymaths advised>
Reviewers: <who reviewed, verdicts>
Fix cycles: <count>

Task-id: <task-id>
Agent-Tier: leader
Complexity: <complexity>
Agent-Name: <your-agent-name>
Agent-ID: <your-agent-id>
```

Commits without `Task-id:` and `Agent-tier:` trailers will not be recognized
by the worker monitor as valid deliverables.

## HITL (Human-in-the-Loop)

Toggleable per task. When ON, human is notified only at the final PR — not during work.
When OFF, orchestrator sends a polymathic PR reviewer and auto-decides.
