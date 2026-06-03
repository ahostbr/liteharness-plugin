# Convergence Signals

Mission completion is not a feeling. The Orchestrator declares done only when stop codons, signal-absence, and deployment gate all align.

## Signal 1: Stop Codons

Every issue must contain explicit done conditions at creation time. Before closing or merging, check that the stop codons are true:

- acceptance criteria satisfied
- required validation run or blocker documented
- no unrelated scope expansion
- discovered work filed and linked
- review verdict is APPROVE
- PR links to issue
- final issue comment summarizes what shipped and what remains

If stop codons are missing, the Leader or Orchestrator adds them before dispatch continues.

## Signal 2: Signal-Absence

The system is converging when the new-issue discovery rate drops below the closure rate for the current mission.

Track per cycle:

- issues closed
- issues opened from discovered work
- reopened issues
- reviewer REQUEST-CHANGES count
- reviewer BLOCK count
- unresolved blockers

If discovery rate is greater than closure rate for 3 or more cycles, scope is expanding instead of converging.

## Signal 3: Deployment Gate

The artifact must exist outside the codebase in the form appropriate to the project.

Examples:

- web app: CI passes and preview or production deployment is live
- desktop app: binary built, signed when required, and smoke-tested
- library: package built, tests pass, publish or release artifact prepared
- CLI: executable built, help command works, release artifact prepared
- documentation: rendered docs site/page updated and links verified

The Orchestrator sets the deployment gate per mission during intake. Leaders inherit the gate and add domain-local gates when needed.

## Scope-Creep Circuit Breaker

If discovery rate exceeds closure rate for 3 or more cycles:

- In supervised mode, pause expansion and ask the human to triage, descope, or approve new scope.
- In fully_autonomous mode, auto-descope noncritical follow-ups, preserve only work needed for the PRD stop codons, and comment the decision on the issue.

Do not keep dispatching new work into an expanding mission without an explicit convergence decision.

## Mission Completion

The Orchestrator may declare mission complete only when:

- all required stop codons pass,
- signal-absence indicates closure outruns discovery,
- deployment gate is satisfied,
- no BLOCK verdict remains unresolved,
- budget is within the mission policy or approved override,
- all follow-up work is either closed, linked, or intentionally deferred.

Completion creates a final GitHub Issue comment with shipped scope, PR links, validation evidence, deferred issues, budget summary, and remaining risks.
