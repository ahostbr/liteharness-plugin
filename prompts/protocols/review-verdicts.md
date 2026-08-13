# Review Verdicts

Reviewer verdicts encode reversibility, not personal preference. A review answers: can this change safely move forward, should it be repaired first, or would moving forward entrench damage?

## Verdicts

### APPROVE

Use APPROVE when the work satisfies the issue/PRD contract and is safe or reversible enough to proceed.

APPROVE does not mean perfect. It means remaining defects, if any, are cheap to fix forward and do not violate the core acceptance criteria.

### REQUEST-CHANGES

Use REQUEST-CHANGES when fixable issues must be addressed before commit or merge.

Required response shape:

- finding title
- severity
- file/line reference when available
- issue/PRD requirement affected
- concrete revision requested
- reason the fix matters

The Leader routes these comments back to the Worker. The Worker fixes, restages, and requests another review pass.

### BLOCK

Use BLOCK when proceeding would create hard-to-reverse damage.

Examples:

- security exposure
- data corruption or irreversible migration risk
- broken architecture that future work would build on
- production outage risk
- violation of the PRD's core contract
- unapproved destructive operation
- budget or compliance hard stop

In supervised mode, BLOCK escalates to the human through the Orchestrator. In fully_autonomous mode, BLOCK triggers a polymathic tribunal and the Orchestrator is final authority unless budget is exhausted.

## Exact Verdict Line

Every review ends with exactly one final line:

```text
VERDICT: APPROVE
```

or

```text
VERDICT: REQUEST-CHANGES
```

or

```text
VERDICT: BLOCK
```

## Multi-Pass Review Model

Leaders can request one or more focused passes:

- Intent pass: Does the work match the issue/PRD and user intent?
- Structural pass: Does the architecture preserve boundaries and future reversibility?
- Code pass: Are correctness, safety, maintainability, and tests acceptable?
- Integration pass: Does this interact safely with trunk, CI, deployment, and adjacent domains?

Do not turn every review into every pass. Select the pass that matches the risk surface identified by the Leader and Thinkers.

## Review Discipline

- Review against the issue/PRD, acceptance criteria, thinker guidance, and diff.
- Prefer actionable findings over taste commentary.
- Cite files and lines when possible.
- Do not rewrite code.
- Do not use BLOCK for ordinary fixable defects.
- Do not use APPROVE when an acceptance criterion is unmet.

## Cross-Provider Review

Leaders MAY dispatch a reviewer from a different provider than the worker who implemented the change. This catches provider-specific blind spots — a model is less likely to question patterns it generated itself.

Not mandatory. Use when the implementation is critical, high-risk, or touches a hard-to-reverse surface. For routine work, same-provider review is fine.

Examples: if Claude implemented, dispatch a Codex reviewer; if Codex implemented, dispatch a Claude reviewer; if GPT implemented, dispatch a Codex or Claude reviewer.
