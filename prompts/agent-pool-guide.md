## Agent Pool Guide

When selecting thinkers or reviewers, choose agents based on the task type.
Use conventional commit keywords as a guide for task classification:

### Task Type → Pool Mapping

| Commit Type             | Task Category        | Recommended Pool   |
| ----------------------- | -------------------- | ------------------ |
| feat:, refactor:, perf: | Code & Architecture  | code_architecture  |
| fix:, test:, ci:        | Code & Architecture  | code_architecture  |
| docs:, style:           | Strategy & Reasoning | strategy_reasoning |
| chore:, build:          | Strategy & Reasoning | strategy_reasoning |

### Available Agents

#### Code & Architecture Pool

{{CODE_ARCHITECTURE_TABLE}}

#### Strategy & Reasoning Pool

{{STRATEGY_REASONING_TABLE}}

#### Review Pool

{{REVIEW_TABLE}}

#### Design Patterns Pool

{{PATTERNS_TABLE}}

Discuss between orchestrator and leader to select the most appropriate agents
for the task at hand, considering the task type and agent expertise.
