# Show finished results — canvas display

Inside a supported LiteSuite session, show the final artifact the human should
see: a render, screenshot, generated model, video or report screenshot. Present
once per result. Keep logs, diffs, command output, status and work in progress in
replies or Theater, not result tiles. Read `canvas action=help` for the active
host's full contract before displaying anything.

Use the canvas tool or the authenticated Agent Bridge routes:

- `present` (`POST /canvas/present`): display an image/video/model result tile.
- `center` (`POST /canvas/center`): replace the center with a model;
  `kind=brain` restores the brain.
- `background` (`POST /canvas/background`): use a dimmed image/video behind panes;
  `kind=default` restores the grid.
- `state` (`GET /canvas/state`): inspect the display before replacing a human pin.
- `clear` (`POST /canvas/clear`, `what=all|presented|center|background`): remove your
  display when appropriate; center/background change what the human is seeing.

Give exactly one absolute local `path` or HTTP(S) `url`, never a relative path or
`file://`. Models must be GLB or self-contained glTF; convert unsupported model
formats to GLB rather than repeatedly trying a refused format. Use Theater for
pages and questions, not page-kind canvas tiles; displayed pages must be dark.

## When the app/bridge is unavailable

A standalone CLI does not acquire canvas tools just because this document ships.
Do not invent a visible pane or claim that the human saw an artifact. Report its
actual local path or URL through the leader, state that display is unavailable,
and retain the human-look completion gate until the human has seen the result.
No private actor name, machine-specific root or hardcoded bridge credential is
required. Use the current session's authenticated host connection when present.
