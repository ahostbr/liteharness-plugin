# Claude Mods guards — local candidate

## Contract

The single `tool.call` guard and the approval-path `tool.check` guard live in
`hooks/register.mjs`. Both invoke the same-file `evaluateGuard` helper before
allowing downstream behavior. Other plugin features must compose after that
call, never introduce an earlier unguarded short-circuit. Imported
`hooks/mods/guards.mjs` helpers are pure: they cannot receive the privileged `$`.
The analyzer recognizes all API calls in the entrypoint.

The bridge launches `python <plugin-root>/hooks/mods/guard_backend.py` using
`$.process.run` argv and JSON stdin, **without a shell**. The target command is
only data. It is never passed as subprocess argv or evaluated by the backend.
The backend's subprocesses are fixed, read-only process-census and Git queries.
Missing runner, timeout, incomplete output, bad protocol, unsupported execution
fields, and policy-loader failure refuse the tool. Hook `.catch` handlers also
return explicit refusal on engine errors/timeouts.

The process timeout is 15 seconds. Official API documentation states awaiting a
Mods API call does not count against the event execution budget; this is not a
custom promise that can silently outlive the hook. Cancellation/timeout may
leave a completed body file, but never invokes the target command.

## Authoritative floor and provenance

The backend locates the installed `liteharness` distribution using Python
stdlib metadata, including editable-install `direct_url.json`. No personal
filesystem location is shipped. It compiles the verified source bytes directly
for both gate and floor, binds the gate's loader to that exact floor object,
and calls the existing `decide`, avoiding package imports, stale `sys.modules`
policy objects and unverified bytecode caches. Only `None` means no floor refusal;
malformed results, including falsey objects, fail closed.

This candidate accepts package version **0.4.5** only, bound to immutable OSS
**fba17c7c40a83584283418c6499467a1a8805196** and the LF-normalized policy
SHA256s below. The policy bytes match the published 0.4.4 reference
**d3ba9a8f59fb7b10279be54980f2385d193273d1**; the candidate's parent is not
assumed to contain that divergent release overlay. Earlier 0.4.4 construction
receipts below remain historical. Package source binding and synthetic tests
are not proof of an installed package/plugin or Claude-host activation.

- `deny_gate.py`: `15e98aea4ac8154d028aadc2e375e18892d202a95794b9fbe82ef59706d3cd79`
- `deny_floor.py`: `c60d0fee461c3a4bfcfae928c624e4c64ffbbefc7a5d9103851f03fb22704046`

Different/missing sources fail closed; a future floor release requires an
explicitly reviewed compatibility update. Existing Python hooks are **not
removed or disabled**. A broken floor in this bridge is always a denial, stricter
than the legacy gate's class-limited crash fallback. Settings hooks remain
independent protection when Mods are unavailable.

The suite-classification patterns were ported from the existing operator
`no_full_suite.py` (raw source SHA256
`4d072dfaebe0b37c2899723e12568f7b93a425d2b6d0fe26e47b628a472c276f`).
Classification preserves its command-head/segment rules, explicit file
selection, and host-environment `LITEHARNESS_ALLOW_FULL_SUITE=1` escape hatch.
The escape hatch never disables the deny floor. Process-census failures now
refuse rather than pretending there are no runners. This is not a general
shell parser: aliases, wrappers, and advanced heredocs remain outside measured
classification parity. Keeping Python hooks is mandatory, not a parity claim.

## Additional guards

- Git worktree-removal candidates are classified before force-option filtering.
  Supported forced removal must have a simple literal command with one target
  and explicit `--force` or `-f`; unique long prefixes such as `--for`/`--forc`,
  unknown options and global-option command shapes refuse conservatively.
  Ordinary quoted words are recognized; `--` ends option parsing. A simple
  non-force removal retains the normal permission path.
  The target's existing ancestors and every scanned descendant must have no
  symlink/junction/reparse point. An unreadable/missing target, unsupported
  syntax, or more than 10,000 entries refuses. A clean scan **does not approve a
  deletion**: normal permissions still run. No actual removal is performed by
  the bridge or tests.
- Inline inbox bodies with backticks are rewritten only for a bounded literal
  `liteharness send` syntax or `lst run inbox action=send` with known text fields.
  Bodies are written as UTF-8 to exclusive temporary files, then the command is
  replaced with a `liteharness send --body-file` invocation. Recipient, sender,
  and type are retained. Ambiguous bodies/flags, payload objects, shell joiners,
  quoted escapes, and multiline shell arguments refuse rather than silently
  dropping text. Original shell-expanded intent cannot be inferred: text inside
  the recognized quoted body is deliberately treated literally.
- Body files contain message text. They are local, not committed, and not
  automatically deleted. Retention/privacy maintenance is follow-up work, not
  an implicit deletion in a guard. The directory is checked for reparse points
  before and after creation.

## Rule 5a approval proof

Only built-in file-write tools are eligible. Shell commands are never
auto-approved by this feature. The trusted current Mods session/cwd APIs are
used rather than a tool-supplied `cwd`. The backend requires exactly one explicit
Claude takeover registration belonging to its actual parent Claude process,
with a registration timestamp no older than that process's creation time and
identity matching the current session. Missing `psutil`, ambiguous/stale records,
and insufficient session evidence mean **no automatic approval**.

The registered cwd must match the actual session cwd; that root must be a Git
worktree (`.git` file, not the main checkout directory), listed with its current
branch in `git worktree list --porcelain`. Every existing path component must be
free of links/reparse points. The target must remain within the canonical root;
Windows ADS/trailing-space/dot aliases and `.git`, `.claude`, `.liteharness`
metadata and existing multiply-linked files do not qualify. No branch-name
convention grants authority. Read-only helper executables resolve only from
absolute host PATH entries outside the target worktree and without reparse
components; Git relocation/config-injection environment fields are removed.
The interpreter and host-owned executable-search environment remain deployment
trust boundaries, not defenses against a compromised host installation.

`tool.check` makes a fresh policy/proof query. It only changes a downstream
unruled `ask` to `allow`; an existing `deny` or rule-backed `ask` is preserved.
Deletes, merges, downloads, public pushes and arbitrary shell writes gain no
approval. Host registration/filesystem integrity is a trust boundary, not a
sandbox against malicious code already running as the user. Filesystem checks
cannot eliminate the race between permission checking and the eventual tool
write/removal; that residual must be handled at the executor boundary.

## Validation and limitations

Foundation: authored plugin **fd3808af08919601cfd8024ef41ad600bcb5a4fb**.
Official documentation verified: Mods overview/reference/events/API pages for
Claude **2.1.287**; public TypeScript reference advertises **2.1.277** and is not
claimed as generated installed-build types.

Focused receipts during construction:

- Combined 1.0.20 candidate, paired with immutable package
  **fba17c7c40a83584283418c6499467a1a8805196**: eight focused Python files
  (the four guard files below, role-wrapper generation, public privacy, privacy
  regressions and first-run identity) reported **125 passed, 71 subtests passed**,
  child exit 0. All four plugin version declarations are 1.0.20. The selected
  package is read from its owned local source; guard distribution metadata and
  first-run homes are isolated fixtures, not installation or live closure proof.
  Generated-wrapper checks cover 42 unchanged METHOD bodies plus the bounded
  default lifecycle template, with zero stale wrappers. The earlier attempt
  stopped collection because the explicit paired-source environment was absent;
  it is not counted as a pass.

- `python -m pytest tests/test_guard_backend.py tests/test_guard_identity.py tests/test_guard_regressions.py tests/test_guard_release.py -q`:
  **72 passed**, exit 0, after the corrected 93148ae 0.4.4 pin update, including actual body-file
  roundtrip, actual symlink scan, force-prefix refusal with reparse target/no
  execution, quoted removal/global options, falsey malformed floor, verified-byte
  binding, hardlinks, unsafe helper search and Git environment regressions.
  Release tests use `LITEHARNESS_TEST_POLICY_REPO` pointing to a local clone of
  the immutable authorized commit. Shared `tests/conftest.py` supplies actual
  freeze/parent-verified canonical bytes to release, backend and cache-binding
  regressions; no fixture disguises the older installed source as the correction.
  Unknown versions (including 0.4.3), changed source under exact 0.4.4 metadata,
  and absent distributions are refused.
  Distribution metadata is an explicit fixture, not proof of a live 0.4.4
  installation. No installation was performed; the operator interpreter still
  reports 0.4.3 and the production bridge correctly rejects that older version.
- `node --test tests/guards.test.mjs`: **8 passed**, exit 0, exercising shipped
  entrypoint registration, refusal, rewrite and permission handlers with
  explicit external-boundary fixtures. Not a Claude engine-host receipt.
- `node --check hooks/register.mjs`, Git diff whitespace check: passed.
- Python Ruff was unavailable (`No module named ruff`); no dependency installed.
- Explicit Claude plugin-manifest validation recognizes guard hooks and process
  API calls without Mods diagnostics. Whole-plugin validation exits 1 on four
  pre-existing foundation diagnostics: three YAML frontmatter parse errors and
  MCP URL server missing `type`. No unrelated source changes are made here.
- Installed `claude plugin test` cannot run: rollout switch is served **off** in
  this process. No switch override, live setting change, restart, or installation
  was attempted. Real Mods runtime behavior remains **UNVERIFIED**.

The corrected packet verification receipt SHA256 is
`44d063d9cd825e3dbfe4657abe4aa015fc34977f94d996612a0812da002ed4c0`.
Raw focused output hashes: Python
`310be92b610bf976c33c3f633e07497c22ea38fbd2565da15d433d7a9263a288`,
Node `6cf9f3d8e242a47dfcdb1891dbc946bcf2b53b075f97ee119e3329172c4d2bdb`.
Both process exits were persisted before console output; checks-manifest SHA256
`f8dd0cfe9f984b2a1d7fe59e0bb539d53d8f1e86a11bcb3d15847d7cbcb51fce`.
Local immutable receipts are under `.agents/T0316-receipts/corrected-93148ae/`.
These focused passes do **not** claim the canonical suite is all green: the T0313
review packet reports 62 baseline failures with no new failed IDs. This worker
neither reran those broader suites nor changed their policies/tests.

The local candidate must remain reviewing until the separate reviewer and
the project owner's final look. Shared manifest/version bumps are leader-owned integration
work; this feature does not mutate those sites independently. Public release
privacy audit and explicit push authority remain required.
