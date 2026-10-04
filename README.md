# LiteHarness Plugin — Claude Code and Codex surfaces

Native **Claude Code marketplace plugin** delivering the LiteHarness skills + agents catalog: 60+ skills, 91 agents (49 polymathic thinkers), and 27 hooks. Spawn, coordinate, and review AI coding agents across **Claude Code, Codex, Copilot, Pi, Kilo, OpenCode** — all from one harness.

## Shared native payload and separate Python delivery

LiteHarness ships in two repos that work together, not duplicates:

| Repo                                                                                        | What it is                                                                                                                                                                    | Install command                                                                                 |
| ------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| **[ahostbr/liteharness-plugin](https://github.com/ahostbr/liteharness-plugin)** (this repo) | Native Claude Code marketplace plugin — same skills + agents catalog, delivered via Claude's plugin system                                                                    | `/plugin marketplace add ahostbr/liteharness-plugin && /plugin install liteharness@liteharness` |
| **[ahostbr/liteharness](https://github.com/ahostbr/liteharness)**                           | Python runtime engine + universal installer for opt-in catalog installation across supported CLIs | `pip install liteharness`                                                                       |

Claude and Codex native manifests refer to this shared repository payload. The Python package is a separately versioned runtime/catalog and may contain held or ahead skills; do not assume byte-for-byte parity. Codex has `.codex-plugin/plugin.json` and `.agents/plugins/marketplace.json`; marketplace publication/synchronization needs its own source-ref evidence. A local manifest does not prove remote sync. Claude Mods, when present, are Claude-only; Codex does not gain that runtime from a shared directory. A plugin update does not install the companion Python telemetry reader.

## What You Get

- **60+ skills** under `liteharness:ls-*` namespace — arch, debug, ls-sentinel (legacy slug), vault, conversation-lookup, plan-w-quizmaster, librarian, and more
- **91 agents** — 49 polymathic thinkers (Feynman, Carmack, Shannon, Linus, Lovelace, etc.), 14 thinker lenses, 9 pentest analysts, 9 PRD-workflow agents, 5 specialists, plus meta/mp/test agents
- **27 hooks** — SessionStart registration, PostToolUse inbox polling, lifecycle events
- **Multi-CLI orchestration** — see and control agents across every major coding CLI
- **Inter-agent messaging** — agents talk to each other via Maildir inbox
- **5-tier hierarchy** — orchestrator, leader, worker, thinker, reviewer
- **Headless spawning** — ConPTY daemon for invisible background agents
- **Deterministic naming** — every agent gets a memorable two-word name from its UUID

## Install

```bash
# 1. Install the Python runtime
pip install liteharness

# 2. Install this plugin in Claude Code
/plugin marketplace add ahostbr/liteharness-plugin
/plugin install liteharness@liteharness
```

Both are required: this plugin provides the skills + agents Claude sees, while `pip install liteharness` provides the underlying CLI (`liteharness spawn`, `liteharness send`, `liteharness discover`, etc.) the skills call.

## Usage

```bash
# Spawn a background agent
liteharness spawn --pty --cwd <repo-root> --tier worker --model <chosen-model> --name "Worker" --prompt "fix the flaky test"

# See who's online
liteharness discover

# Send a message
liteharness send <agent-id> "try approach B" --from <your-id>

# Check your inbox
liteharness check
```

In Claude Code, invoke skills directly:

```
/ls-init-liteharness                # Choose your orchestrator name and interview
/arch                               # Load canonical architecture index
/library list                       # List the full skill+agent catalog
/plan-w-quizmaster <task>           # Structured planning with quizmaster
/vault search <query>               # Search Obsidian vault RAG
/conversation-lookup <query>        # Search past conversations (BM25/semantic/hybrid)
```

## Skills (selection — 60+ total)

| Skill                                | Purpose                                            |
| ------------------------------------ | -------------------------------------------------- |
| `liteharness:ls-sentinel`            | Primary orchestrator protocol                      |
| `liteharness:ls-arch`                | Load canonical LiteSuite architecture index        |
| `liteharness:ls-library`             | Catalog of all skills + agents + commands          |
| `liteharness:ls-vault`               | Obsidian vault commands (note/daily/search/import) |
| `liteharness:ls-conversation-lookup` | RAG over every past conversation                   |
| `liteharness:ls-plan-w-quizmaster`   | Plan with Ultimate Quizzer methodology             |
| `liteharness:ls-librarian`           | Workspace knowledge curation (Eratosthenes)        |
| `liteharness:ls-spawnteam`           | Spawn a Claude Code agent team                     |
| `liteharness:ls-train`               | Autonomous agent/skill training loop               |

Run `/library list` for the complete catalog.

## Agents (91 total)

49 polymathic thinkers + specialists + pentest + thinker lenses + workflow agents:

| Category            | Examples                                                                                                                                                                                                                                     |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Polymathic (49)** | `polymathic-feynman`, `polymathic-carmack`, `polymathic-shannon`, `polymathic-linus`, `polymathic-lovelace`, `polymathic-jobs`, `polymathic-bezos`, `polymathic-thiel`, `polymathic-knuth`, `polymathic-davinci`, `polymathic-einstein`, ... |
| **Specialists**     | `specialist-doc-writer`, `specialist-librarian`, `specialist-perf-optimizer`, `specialist-security-auditor`, `specialist-test-generator`                                                                                                     |
| **Pentest (9)**     | `pentest-pre-recon`, `pentest-recon`, `pentest-injection`, `pentest-xss`, `pentest-auth`, `pentest-authz`, `pentest-ssrf`, `pentest-evasion`, `pentest-report`                                                                               |
| **Thinkers**        | `thinker-skeptic`, `thinker-red-team`, `thinker-blue-team`, `thinker-systems`, `thinker-pragmatist`, ...                                                                                                                                     |
| **Workflow**        | `meta-agent`, `meta-challenger`, `mp-builder`, `mp-validator`, `prd-*` (executor/reviewer/validator/primer/...)                                                                                                                              |

See `agents/` directory for the full list.

## Releasing — bump the version on EVERY catalog change

The Claude Code CLI caches an installed plugin under
`~/.claude/plugins/cache/liteharness/liteharness/<version>/` and **only rebuilds
that cache when the version string changes.** Codex plugin installs also use the
`.codex-plugin/plugin.json` version as their release/cache boundary. If you edit
`skills/`, `agents/`, `commands/`, or `hooks/` but leave the version alone, the
cache freezes and the CLI keeps serving the OLD catalog forever (the classic "my
renamed skills still show the old names" bug).

Release preparation requires a version bump for catalog changes. Reversible candidate commits are not release authorization: the release owner bumps after review/intent gates. Never push a candidate or bypass active hooks; report a local commit/version-gate conflict to the leader.

```bash
python scripts/bump_version.py          # patch (default): 1.0.1 -> 1.0.2
python scripts/bump_version.py minor    # 1.0.1 -> 1.1.0
python scripts/bump_version.py --set 2.0.0
# Release owner stages the reviewed files, commits and pushes only after final release GO
```

`scripts/bump_version.py` updates `.claude-plugin/marketplace.json`,
`.claude-plugin/plugin.json`, and `.codex-plugin/plugin.json` together.

Then refresh the cache in Claude Code:

```
/plugin marketplace update liteharness
/plugin update liteharness@liteharness
```

This is **enforced by a pre-commit hook** (`.githooks/pre-commit` →
`scripts/check_version_bump.py`). Staging a catalog change without a version
bump blocks the commit. Enable the hook once per clone:

```bash
git config core.hooksPath .githooks
```

Do not bypass active privacy/version hooks. Report a blocked candidate commit; the release owner resolves the gate explicitly.

## Requirements

- Claude Code CLI
- Python 3.10+ (for `pip install liteharness`)
- Windows 10+ (for headed mode / UIAutomation). Headless PTY works on any OS.

## License

MIT
