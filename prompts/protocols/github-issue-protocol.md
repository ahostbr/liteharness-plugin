# GitHub Issue Protocol

This workflow is the durable spine of LiteHarness mission execution. GitHub Issues are the source of truth for product intent, PRD content, task state, audit history, and the Issue -> PR -> next Issue loop. LiteHarness inbox messages are transport. GitHub comments are memory.

## Canonical Loop

1. Human intent arrives at the Orchestrator.
2. The Orchestrator creates or updates the canonical GitHub Issue.
3. If this is a new app and no repository exists, create the empty Git repository first, then create Issue #1: "Bootstrap app from PRD".
4. The issue body receives the PRD/spec, acceptance criteria, constraints, out-of-scope boundaries, success metrics, and open questions.
5. The Orchestrator decomposes the issue into leader-owned domains.
6. Leaders claim issue clusters, create visible subtasks, consult Thinkers when needed, and dispatch Workers in isolated worktrees.
7. Workers claim assigned items, implement within the stated boundary, stage changes, and wait for review.
8. Reviewers inspect against the issue/PRD and return APPROVE, REQUEST-CHANGES, or BLOCK.
9. Approved work becomes a pull request linked to the issue.
10. Merge/close creates or selects the next issue.
11. The loop continues until convergence or human intervention.

## Issue Lifecycle

Use this state machine unless a project explicitly defines a stricter one:

```text
backlog -> todo -> in_progress -> in_review -> done
                                      |          |
                                      v          v
                                   blocked   cancelled
```

`done` and `cancelled` are terminal. `blocked` is actionable only when the blocking condition is named and an owner exists.

## Mandatory Stop Codons

These gates are non-negotiable before any Worker declares DONE, any Reviewer returns APPROVE, or any Leader/Orchestrator closes a PR or issue:

- E2E Playwright tests pass with `--bail=1`.
- The project's configured typecheck command passes.
- The project's configured lint command passes.

Workers must include evidence for all three gates in their DONE report. Reviewers must verify that evidence in every PR review. Leaders and the Orchestrator must keep the issue or PR open when any gate is missing, failing, or undocumented.

If a project genuinely cannot run one of these commands yet, the agent must file or comment an explicit blocker with the reason, owner, and remediation issue. Absence of the command is not silent approval.

## Atomic Checkout

Every issue or subtask must be claimed before work starts.

- One active owner per issue, subtask, branch/worktree, or file-domain boundary.
- A claim succeeds only when the item is unassigned, assigned to the same run, or explicitly reclaimed as stale by the Leader.
- A claim conflict is a 409-equivalent signal. Do not race, retry blindly, or work around it.
- On conflict, pick another item, ask the Leader for reassignment, or wait for stale ownership to be cleared.
- Ownership must include the agent id, run/session id, branch/worktree, and timestamp when the storage layer supports it.

## Discovered Work

Agents must not silently broaden scope.

- If discovered work is required for the assigned acceptance criteria, file it as a linked issue/comment and ask the Leader to pull it into the current cluster.
- If discovered work is adjacent, speculative, or future-facing, file a follow-up issue and keep the current item converging.
- Include reproduction evidence, affected files, expected impact, and parent issue link.
- The Leader triages discovered work. Workers do not self-authorize scope expansion.

## Durable Comments

Use GitHub comments for task-linked audit history:

- PRD interpretation and updates
- dispatch records
- progress reports
- blocker reports
- discovered work
- review verdicts
- merge decisions
- closure summary

LiteHarness inbox is for live routing and wakeups. The GitHub thread is where future agents should be able to reconstruct what happened.

## Commander's Intent

Every task brief carries two levels of purpose plus a shipped definition:

- What: the immediate task or subtask.
- Why: the Leader's domain objective.
- Shipped: the Orchestrator's mission intent and acceptance boundary.

This lets Workers make local decisions without stealing strategy from Leaders or the Orchestrator.

## Andon Cord

Any tier may halt downstream work on a branch when continuing would amplify damage.

Use the andon cord for:

- security exposure
- data loss or corruption risk
- destructive operations without approval
- repeated test failure with unclear cause
- cross-domain contract conflict
- reviewer BLOCK
- budget hard stop

The halt must be commented on the issue with the reason, blast radius, current owner, and the next decision needed.
