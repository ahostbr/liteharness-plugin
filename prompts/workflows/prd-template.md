# PRD Template

Use this template when turning thin intent into a GitHub Issue PRD or when decomposing the Orchestrator's master PRD into leader-owned sub-issue PRDs. Keep requirements testable. Encode stop codons at creation time so agents know exactly when to stop.

## Title

`<verb> <product/work area> <outcome>`

Examples:

- Bootstrap app from PRD
- Add password reset flow
- Build billing settings page

## Problem Statement

Describe the user-visible problem, business/mission need, or system gap. State why this matters now.

## Target Users

List the humans, agents, systems, or operators affected by the work. Include primary and secondary users when relevant.

## Requirements

Number every requirement. Each requirement must be observable or testable.

1. The system shall ...
2. The user can ...
3. The agent must ...

Avoid vague requirements such as "make it better" unless they are paired with measurable acceptance criteria.

## Acceptance Criteria / Stop Codons

Stop codons are explicit done conditions. Agents must check them before declaring DONE.

- Functional behavior exists and matches the requirement.
- Relevant tests, lint, build, or manual validation passed, or the blocker is named.
- GitHub Issue has progress evidence and final summary comments.
- Pull request links back to the issue.
- Discovered work is filed as linked follow-up issues.
- No unrelated files or scope expansions are included.
- Reviewer verdict is APPROVE before merge.

Add project-specific stop codons here:

- `<condition>`
- `<condition>`

## Technical Constraints

Name constraints that matter to implementation:

- existing architecture boundaries
- required libraries or forbidden dependencies
- performance targets
- accessibility targets
- security/privacy rules
- database, migration, or deployment constraints
- supported platforms

## Out of Scope

State what this issue will not do. Out-of-scope entries prevent silent expansion and should become follow-up issue candidates when still valuable.

## Success Metrics

Define what success looks like after shipping:

- user-facing behavior
- test/build signal
- performance or reliability signal
- operational signal
- adoption or usage signal when available

## Open Questions

List unresolved decisions. Mark each question with an owner and whether it blocks work.

| Question | Owner | Blocks? |
| -------- | ----- | ------- |
|          |       | yes/no  |

## Follow-Up Issue Candidates

List useful work discovered during PRD creation that should not be pulled into the current issue.

- `<candidate>` — reason / parent link

## Leader Decomposition Notes

When Leaders create sub-issues from a master PRD, preserve:

- parent issue link
- domain boundary
- file/package ownership boundary if known
- required interfaces with other domains
- local acceptance criteria
- reviewer risk profile
- expected deployment gate
