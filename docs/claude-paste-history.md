# Native pasted-image history (T0318 source checkpoint)

**Rollout defaults OFF.** `LITEHARNESS_PASTE_PANE=1` opts this feature in only
when the host independently permits mods. This source change does not set that
variable, enable host rollout, install anything, start a session, or prove live
pixels. The existing Python extraction / LiteSuite history half must be present.

## One artifact, two consumers

The pane reads only `<session.cwd>/.litesuite/theater/pastes/.history.json` and
its generated `assets/<sha256>.<ext>` files. It never reads Claude transcripts,
prompt text, clipboard, credentials, remote images or the Bridge token.
`prompt.submit` has no image data and is deliberately not used. The Python hook
owns extraction, dedupe, history retention and publication; the native mod owns
only display state. No image/manifest writes or deletions occur here.

The imported `hooks/mods/paste-schema.mjs` is pure. API-bearing helpers remain
in `hooks/register.mjs`, as the host analyzer requires. Single session.start/end
registrations and the existing 15-second polling timer are reused; no extra
lifecycle or timer is registered. Session.measure also refreshes, with idle
polling picking up the Python Stop fallback if it publishes after measure.
Refreshes serialize; lifecycle generation and identity checks discard delayed
old-session reads. Clear/resume wait for a new identity; exit stops the timer.

The manifest is bounded to 256 KiB and 256 unique generated entries, each <=5 MiB,
with aggregate <=256 MiB. JSON, filenames, sizes and resolved local paths are
validated. Only eight visible assets are statted per page, with Newer/Older
controls exposing the full history. Filesystem calls have host event budgets,
not a new hard disk-I/O timeout. Manifest errors clear previews and report
unavailability, not success; subsequent refresh retries. Resolution and stat
are best-effort time-of-check checks, not open file handles held through paint.
Concurrent filesystem mutation can still replace a file after validation.

## Native host limits / user control

Claude Code 2.1.287's generated ImageSource supports PNG file previews, not JPEG,
GIF or WebP files. PNGs draw from `{ file, format: 'png' }`, with an ordinal alt
label. JPEG/GIF/WebP entries remain in history and receive explicit **unsupported
native preview; retained in LiteSuite** text. No decoder/dependency was added and
all-format native thumbnails are **not** claimed. Image is terminal-only;
Desktop receives an honest explanation rather than blank Image elements.

Automatic opening does not steal focus. The host may hold an unrequested pane
until the terminal is wide enough. `/pastes` explicitly opens it and requests
focus. Hide and the person's close/Esc persist dismissal for the current session,
including newly arriving images; polling does not fight that choice. `/pastes`
reopens on request. History persists via the extractor's project-local manifest,
not module variables; a module reload can reread it. No retention cleanup occurs.

This is not security approval or permission handling. Existing deny-floor,
Python hooks, stream forwarding, cache band, compact and downstream UI behavior
remain in place. B/D wiring is integrated separately, not merged in this worker
branch; the tool guard mod (C) was removed. No manifest/version/settings/installed-plugin
changes are made.

## Evidence tiers

Generated types were inspected from a scratch host artifact whose first line is
`Written by Claude Code 2.1.287`. That establishes the current declared API
contract, not runtime behavior. The public 2.1.277 reference is not current-host
proof. Exact local provenance/hash lives in the task's scratch evidence, not in
this public document.

`tests/paste-history.test.ts` ships Claude test-host fixtures for PNG tree,
turn/poll persistence, opt-out and Desktop truthfulness. If `claude plugin test`
refuses because native rollout is served off, preserve that refusal: never
force-enable the host for a fixture run. `tests/paste-history-source.test.mjs`
is the bounded Node fallback: it imports the actual entrypoint, substitutes
in-memory API boundaries, and exercises controls, newest-first manifest reads,
pagination, opt-out, missing/invalid/path-escaped artifacts, lifecycle races and
reload recovery. This fallback is **not** the host analyzer, real element
validation, filesystem integration or terminal paint. It does not replace the
shipped host fixtures or live acceptance.

Whole T0318 remains open until leader-authorized visible image/persistence proof
on both selected surfaces and a human look. Source/fixture checks alone do not
prove Claude append timing, actual thumbnail pixels, narrow-terminal placement,
user input paths or persistence in a running seat. Installation, activation,
release and visible probes remain separately gated.
