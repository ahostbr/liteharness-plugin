# Changelog

User-facing changes are grouped by version using [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Historical source landing dates below are not reconstructed publication timestamps.

## [1.0.24] — Unreleased

### Fixed
- Native `Agent()` subagents are deliberately closed. The refusal explains the
  visible named `liteharness spawn --split` path instead of teaching tier/model
  retries; scouts/critics use Sonnet 5.5 and grunt builders use Haiku 5.5 unless
  the task explicitly selects another model.
- Preserve human-only terminal closure and leader-owned named resume instructions
  while removing contradictory native-Agent/default-headless examples.
- Preserve literal owned worktree paths in the PowerShell launch example,
  including smart single quotation marks. Parser-backed checks invoke no command.
- The deliberately removed native tool guard stays removed. No installation,
  active-session reload, or publication is implied by this source candidate.

## [1.0.22] — Unreleased

### Removed
- The native tool guard mod: its backend and front half in `hooks/mods/`, its
  `tool.call` / `tool.check` hook-up in `hooks/register.mjs`, its document and its
  tests. The plugin no longer pins a package version or policy hashes. The fleet,
  usage, paste-history and inbox mods are unchanged. The mod documents no longer
  describe a guard that runs first.

## [1.0.21] — Unreleased

### Changed
- Remove active `retire` / `ack-idle` directives from canonical role prompts,
  generated wrappers and mirrored orchestration skills. Close terminals only on
  explicit human instruction; preserve cognitive method bodies, named-seat identity
  and unrelated host safeguards. The 1.0.20 entry below is historical guidance.
- Already-running seats retain their old preambles until they start again.
  Publication does not rewrite live sessions or authorize any restart or reload.
- Pair the guard with package **0.4.6** and the exact verified LF-normalized policy
  hashes. Other package versions or altered source bytes refuse; no guard bypass
  or installed-cache patch is included.
- Synchronize Theater shared-pane/tab-reuse and Original/Turbo speech-capability
  guidance from the selected package catalog. Live host behavior and audible effects
  remain unverified; existing hook runtime files and public identities are retained.

## [1.0.20] — Historical source entry

Candidate changes relative to the published 1.0.19 source. No publication date is assigned.

### Changed
- **Cooperative retirement guidance.** Role preambles, generated wrappers and bundled
  orchestration skills now direct the spawning leader to `liteharness retire <agent-id>`
  and the retiring seat to `liteharness ack-idle --handoff <path>`. Explicit spawner-only
  force is not an automatic fallback; refusal stops the workflow. Persistent names,
  host-specific first-run identity and unconfirmed-leaf reporting remain explicit.
  This requires the paired package and compatible bridge, not raw live-seat pane close.
- **`ls-tts` guidance follows the selected LiteSuite voice backend.** Concise spoken replies
  preserve the selected voice and saved engine controls. Edge fallback is reserved for a
  definitive Voice API connection refusal, rather than replacing the app's selected voice.
  [Source landed 2026-10-04](https://github.com/ahostbr/liteharness/commit/49dd6da115a7233c94b5075decd0c11e65f726ce).
- **Per-line emotion and queue guidance.** Instructions document nested emotion fields,
  engine-specific controls, validation limits and applied/ignored response reports. Accepted
  or queued speech is not proof of audible completion; queued playback can use a subsequently
  selected engine. This requires the matching deployed Voice API; older-deployment behavior
  and audible effects remain unverified. The neighboring `speak.py` helper remains Edge-only.
  [Final guidance landed 2026-10-05](https://github.com/ahostbr/liteharness/commit/9623e40fc0cfc051eae5861bdb2f18af7d53bc35).
- **Explicit package pairing for native guards.** This plugin candidate requires package
  **0.4.5** and the verified canonical policy bytes from
  [the immutable package candidate](https://github.com/ahostbr/liteharness/commit/fba17c7c40a83584283418c6499467a1a8805196).
  Missing distributions, altered policy bytes and other versions, including 0.4.4, fail closed.
  The underlying policy hashes are unchanged from the published package reference; this is
  a deliberate compatibility binding, not a newly invented security guarantee.

### Compatibility and verification
- Portable identity, lifecycle safeguards, public-content wording, native-hook resources and
  independent plugin support are retained from the published baseline. They are not relisted
  as new features. The plugin is not a wholesale replacement with the smaller package catalog.
- Source and synthetic guard validation do not prove current installed package/plugin pairing,
  Claude-host activation, voice-server parity, latency or audible playback. Publication and
  local installation remain separate operations.

## [1.0.19] — 2026-10-04 (historical source landing)

Backfilled from the [published source baseline](https://github.com/ahostbr/liteharness-plugin/tree/605b5f8c007d5775f8fd3d382c9a5c7cc97435f5).
The date records that commit's landing, not a registry or marketplace publication event.

### Fixed
- Canonical bounded read-only Git exemptions are retained in the paired command-policy floor.
- Release payload reconciliation preserves existing conversation evidence, supervised-consult,
  Theater and source-clause guidance rather than discarding newer catalog capabilities.

### Notes
- These baseline capabilities already occur in 1.0.19; their appearance in another repository's
  history does not make them new 1.0.20 changes. Historical installed-cache state is not used
  as the publication baseline.

## Changelog maintenance

Compare final content against the actual published baseline before grouping changes. Reuse
reviewed evidence and avoid duplicate merge/checkpoint bullets. Record actual source landing
commits separately from evidenced publication dates. New versions remain **Unreleased** without
a date until publication is approved and evidenced. Package and plugin versions are independent;
matching version strings alone do not prove matching payloads, installation or runtime behavior.
