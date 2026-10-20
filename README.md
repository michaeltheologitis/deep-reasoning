# Design docs and as-builts

Every design doc and as-built document of michaeltheologitis/deep-reasoning, at its final version. They never go on `main`: a task's design and as-built are written on its development branch and archived here once its pull requests merge.

The first commit took each file's newest version across the old `design/*`, `as-built/*` and `ci/fork-live` branches; the merge after it records each of those branches' tips as a parent, so every commit an older link names is still here. A second merge does the same for the deleted code branches (task-48-browser, task-57-recap, the v1-* branches, ux-round, the Scout experiments and others), whose work is on `main`.

## Designs

- **c1** · [C1 · Sub-agent sessions nested in the chat — design](docs/design/c1-nested-subagent-sessions.md) (from `design/c1`)
- **c2** · [C2 · App header panels, agent commands and an option picker (design)](docs/design/c2-header-panels-and-menus.md) (from `design/c2`)
- **c3** · [C3 · Desktop launcher: the agent-server's source and a first-launch setup (design)](docs/design/c3-launcher.md) (from `design/c3`)
- **d1** · [D1 · `dr-acp` — design](docs/design/d1-dr-acp.md) (from `as-built/d2-r2`)
- **d2** · [D2 · Library store — design](docs/design/d2-library-store.md) (from `as-built/d3-r2`)
- **d3** · [D3 · Decompositions panel — design](docs/design/d3-decompositions-panel.md) (from `design/d3-v9`)
- **d4** · [D4 · Custom tools — design](docs/design/d4-custom-tools.md) (from `design/d4-v6`)
- **d5** · [D5 · Desktop app: build, install and launch — design](docs/design/d5-desktop-app.md) (from `design/d5-v3`)
- **s1** · [S1 · ACP sub-agent sessions in the agent-server — design](docs/design/s1-acp-subagent-sessions.md) (from `design/s1`)
- **s2** · [S2 · Agent commands, options and App panels in the agent-server: design](docs/design/s2-agent-surfaces.md) (from `design/s2`)
- **task-41** · [TASK-41 · The replay spec reads once — design](docs/design/task-41-replay-race.md) (from `design/task-41`)
- **task-48** · [TASK-48 · Run in the browser on localhost — design](docs/design/task-48-browser.md) (from `design/task-48`)
- **task-57** · [TASK-57 · A fresh run is given the conversation — design](docs/design/task-57-recap.md) (from `design/task-57`)
- **task-64** · [TASK-64 · The launcher's page refuses other host names (DNS rebinding) — design](docs/design/task-64-host-check.md) (from `design/task-64`)
- **task-65** · [TASK-65 · UX round — design](docs/design/task-65-ux-round.md) (from `design/ux-round`)
- **task-66** · [TASK-66 · The launcher's uvx starts: PyPI pinned to a time, and offline from uv's cache — design](docs/design/task-66-uv-pins.md) (from `design/task-66`)
- **task-69** · [TASK-69 · After a Stop, the next message is sent alone — design](docs/design/task-69-stop.md) (from `design/task-69`)

## As-builts

- **c1** · [C1 · Sub-agent sessions nested in the chat, as built (r3)](as_built/c1-nested-subagent-sessions.md) (from `as-built/c1-r3`)
- **c2** · [C2 · App header panels, agent commands and an option picker, as built](as_built/c2-header-panels-and-menus.md) (from `as-built/c2-r3`)
- **c3** · [C3 · Desktop launcher: the agent-server's source and a first-launch setup, as built](as_built/c3-launcher.md) (from `as-built/c3-r2`)
- **d1** · [D1 · `dr-acp`, as built](as_built/d1-dr-acp.md) (from `as-built/d2-r2`)
- **d2** · [D2 · Library store, as built](as_built/d2-library-store.md) (from `as-built/d2-r2`)
- **d3** · [D3 · Decompositions panel, as built](as_built/d3-decompositions-panel.md) (from `as-built/d3-r2`)
- **d4** · [D4 · Custom tools and MCP servers, as built](as_built/d4-custom-tools.md) (from `as-built/d4-r4`)
- **d5** · [D5 · Desktop app: build, install and launch, as built](as_built/d5-desktop-app.md) (from `as-built/d5`)
- **s1** · [S1 · ACP sub-agent sessions in the agent-server, as built](as_built/s1-acp-subagent-sessions.md) (from `design/s1`)
- **s2** · [S2 · Agent commands, options and App panels in the agent-server, as built](as_built/s2-agent-surfaces.md) (from `design/s2`)
- **task-41** · [TASK-41 · The replay spec settles — as built](as_built/task-41-replay-race.md) (from `as-built/task-41`)
- **task-48** · [TASK-48 · Run in the browser on localhost — as built](as_built/task-48-browser.md) (from `as-built/task-48`)
- **task-57** · [TASK-57 · As built: a fresh run is given the conversation](as_built/task-57-recap.md) (from `as-built/task-57`)
- **task-64** · [TASK-64 · As built: the launcher's page refuses other host names](as_built/task-64-host-check.md) (from `as-built/task-64`)
- **task-65** · [TASK-65 · As built: the UX round](as_built/task-65-ux-round.md) (from `as-built/task-65`)
- **task-66** · [TASK-66 · As built: the launcher's uvx starts, pinned to a PyPI time and offline from uv's cache](as_built/task-66-uv-pins.md) (from `as-built/task-66`)
- **task-67** · [TASK-67 · As built: both forks synced with upstream, and what the sync changed in the app](as_built/task-67-upstream-sync.md) (written on `design-docs`; no design doc)
- **task-69** · [TASK-69 · As built: after a Stop, the next message is sent alone](as_built/task-69-stop.md) (from `as-built/task-69`)
