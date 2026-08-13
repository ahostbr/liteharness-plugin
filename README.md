# LiteHarness Plugin — Multi-CLI Agent Orchestration for Claude Code

Native **Claude Code marketplace plugin** delivering the LiteHarness skills + agents catalog: 60+ skills, 91 agents (49 polymathic thinkers), and 27 hooks. Spawn, coordinate, and review AI coding agents across **Claude Code, Codex, Copilot, Pi, Kilo, OpenCode** — all from one harness.

## Two-flavor delivery — Claude vs. everything else

LiteHarness ships in two repos that work together, not duplicates:

| Repo                                                                                        | What it is                                                                                                                                                                    | Install command                                                                                 |
| ------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| **[ahostbr/liteharness-plugin](https://github.com/ahostbr/liteharness-plugin)** (this repo) | Native Claude Code marketplace plugin — same skills + agents catalog, delivered via Claude's plugin system                                                                    | `/plugin marketplace add ahostbr/liteharness-plugin && /plugin install liteharness@liteharness` |
| **[ahostbr/liteharness](https://github.com/ahostbr/liteharness)**                           | Python runtime engine + universal installer for **all CLIs without a native plugin system** (Codex, Copilot, Pi, OpenCode, Gemini, Cursor, Continue, Antigravity, Crush, ...) | `pip install liteharness`                                                                       |

The skills + agents catalog is **the same content** — only the delivery mechanism differs. Claude users get this plugin (native). Every other CLI installs the catalog via the `liteharness` pip package's universal installer (opt-in per CLI through the LiteSuite setup wizard).

## What You Get

- **60+ skills** under `liteharness:ls-*` namespace — arch, debug, sentinel, vault, conversation-lookup, plan-w-quizmaster, librarian, and more
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
liteharness spawn --pty --model sonnet --name "Worker" --prompt "fix the flaky test"

# See who's online
liteharness discover

# Send a message
liteharness send <agent-id> "try approach B" --from <your-id>

# Check your inbox
liteharness check
```

In Claude Code, invoke skills directly:

```
/sentinel load                      # Reload state after compaction
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

So the rule is: **any catalog change → bump the version.**

```bash
python scripts/bump_version.py          # patch (default): 1.0.1 -> 1.0.2
python scripts/bump_version.py minor    # 1.0.1 -> 1.1.0
python scripts/bump_version.py --set 2.0.0
git add -A && git commit && git push
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

(Bypass only when you're certain the cache is unaffected: `git commit --no-verify`.)

## Requirements

- Claude Code CLI
- Python 3.10+ (for `pip install liteharness`)
- Windows 10+ (for headed mode / UIAutomation). Headless PTY works on any OS.

## License

MIT
