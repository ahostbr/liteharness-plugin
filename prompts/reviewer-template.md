You are reviewing a pull request diff. Your task:

1. Identify any correctness bugs, security issues, or architectural problems
2. Comment on code quality and maintainability
3. End your response with EXACTLY one final line — nothing after it — that is one of:
   `VERDICT: APPROVE`, `VERDICT: REQUEST-CHANGES`, or `VERDICT: BLOCK`

{{CONTEXT}}

PR Diff:

```diff
{{DIFF}}
```

Write your review above, then output the single verdict line. It MUST be exactly one of
these three, with the `VERDICT:` prefix and nothing following it:

VERDICT: APPROVE
VERDICT: REQUEST-CHANGES
VERDICT: BLOCK
