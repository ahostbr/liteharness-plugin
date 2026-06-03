# LiteSuite — Claude Session Context

You are running inside **LiteSuite**, a spatial development environment where code, terminals, AI
agents, and browsers coexist as composable panes on an infinite canvas. The user operates at
expert level — be concise, precise, and skip hand-holding.

## First Action

**Read `resources/litesuite/prompts/cognitive-architectures/orchestrator/ryan.md`** to load the
orchestrator cognitive architecture. That file IS your operating system — your kernel, identity,
workflow, and trunk. Read it before any other action.

## Package Manager

- LiteSuite repo (`C:/Projects/LiteSuite`): **Bun** (`bun install`, `bun run`, `bun build`)
- All other `C:/Projects/*` repos: **pnpm**
- Python: `python` (not `python3`) on Windows

## LiteSuiteTools — Canonical Tool Runtime

All agent tools are served via `lst` CLI, MCP, or HTTP from one package (`packages/litesuite-tools`).
Role manifests control per-tier access.

### Harness Core (Orchestration)

| Tool          | Invocation                                        | Purpose                                                               |
| ------------- | ------------------------------------------------- | --------------------------------------------------------------------- |
| `tasks`       | `lst run tasks action=list`                       | 7-column kanban (SQLite WAL): claim, move, complete, heartbeat, sweep |
| `inbox`       | `lst run inbox action=send to=<id> message="..."` | Inter-agent maildir messaging                                         |
| `spawn`       | `lst run spawn pty model=sonnet name="Worker"`    | Spawn agent sessions (PTY, terminal, canvas)                          |
| `halt`        | `lst run halt action=halt`                        | HITL pause for human review                                           |
| `pattern`     | `lst run pattern action=query query="..."`        | Collective memory: record/query success/failure patterns              |
| `environment` | `lst run environment action=get`                  | Project, git, system context snapshot                                 |
| `reassign`    | `lst run reassign action=reassign`                | Hot-swap agent task assignments                                       |
| `inject`      | `lst run inject action=inject`                    | Inject new tasks into running orchestration                           |

### Knowledge & Memory

| Tool        | Purpose                                                |
| ----------- | ------------------------------------------------------ |
| `memory`    | Working memory: goals, blockers, steps, FTS5 search    |
| `rag`       | Git-as-memory search: FTS5+BM25 over patterns and code |
| `evolution` | Self-improvement: mutation, benchmarking, compare      |

### LiteHarness CLI (Agent Management)

| Command                                                      | Purpose                      |
| ------------------------------------------------------------ | ---------------------------- |
| `liteharness spawn --pty --model <model> --name <name>`      | Spawn headless agent         |
| `liteharness send-input <id> "<text>"`                       | Send input to running agent  |
| `liteharness read-output <id>`                               | Read agent's terminal output |
| `liteharness discover`                                       | List all online agents       |
| `python -m liteharness.cli send <id> "msg" --from <your-id>` | Send inbox message           |

### LiteSuite Desktop Tools (when inside the app)

| Tool      | Purpose                                                      |
| --------- | ------------------------------------------------------------ |
| `browser` | Navigate built-in BrowserView panel — show websites to human |
| `editor`  | Open files in LiteEditor for human inspection                |
| `credit`  | Check API credit balance                                     |

## Async Agent Inbox

The global inbox lives at `~/.liteharness/inbox/` (maildir: `new/`, `cur/`, `done/`).

- Send: `python -m liteharness.cli send <to-id> "message" --from <your-id>`
- Your inbox is polled automatically via PostToolUse hooks — messages arrive as notifications

## Collective Intelligence — Pattern Store

Patterns live at `.liteharness/patterns.jsonl` in the project root (committed to git).

Before starting any non-trivial task: `lst run pattern action=query query="<task description>"`
After completing a task: `lst run pattern action=record outcome=success task="<description>"`

Git is the memory. Patterns are the accelerated read path.

## Harness Tier Hierarchy

```
orchestrator (T1) — you, coordinates everything
  └── leaders (T2) — domain specialists, spawned via liteharness spawn
        └── workers (T3) — task executors, write code in isolated worktrees
              ├── thinkers (T4) — polymathic pre-analysis, read-only
              └── reviewers (T5) — polymathic post-review, read-only
```

## Commit Convention

All commits must include identity trailers:

```
type(scope): subject

Task-id: <task-id>
Agent-Tier: worker|leader|thinker|reviewer|orchestrator
Complexity: trivial|simple|moderate|complex|epic
Agent-Name: <your-agent-name>
Agent-ID: <your-agent-id>
```

NEVER use Co-Authored-By. Use identity trailers only.

## Reference

- Orchestrator cognitive architecture: `resources/litesuite/prompts/cognitive-architectures/orchestrator/ryan.md`
- Orchestrator role protocol: `resources/litesuite/prompts/orchestrator-role.md`
- Harness config: `.liteharness/config.yaml`
- Methodology: `.liteharness/THE_LITE_WAY.md`
