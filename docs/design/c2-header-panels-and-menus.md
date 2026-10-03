# C2 · App header panels, agent commands and an option picker (design)

**TASK-7** · System Designer · code lands in the Canvas fork
[michaeltheologitis/OpenHands](https://github.com/michaeltheologitis/OpenHands), task branch `feat/agent-surfaces`,
cut from its `deep-reasoning` branch · against the approved spec
[TASK-1](https://app.notion.com/p/3ed62fb22237814ab425c81b3844f012) (C2 in full; D3, which mounts in C2's panel;
S2; D1's slash-command and namespace bullets; §4's E11 and the test layers; the dated notes at its end).
**Pinned against:** Canvas fork `deep-reasoning` at `02b7ac7` (upstream `1ff45c2` plus the ASE commit, which touches
only `AGENTS.md` and `CLAUDE.md`, so every `file:line` below is upstream's) · S2's design at deep-reasoning `9e32261`
(`docs/design/s2-agent-surfaces.md`, §7 above all) · D1's design at deep-reasoning `f281109` (§5) · SDK fork
`deep-reasoning` at `91430aa` (the agent-server's App-backend bridge and the TypeScript client 1.50.1 it ships) ·
upstream Canvas `main` at `a8c8fb3` (three commits past the fork's base; one touches the chat input, §9).

**Matches the build at `64b5a8b`** (v2): `feat/agent-surfaces` in the draft pull request
[michaeltheologitis/OpenHands#3](https://github.com/michaeltheologitis/OpenHands/pull/3) against the fork's branch
`wiring/dr-1` (head `9881d24`). C2's own commits are nine: PR 1 `20b90cb`, `1828cec`, `a5436be`; PR 2 `4caaecc`,
`82ff26a` and the test `86c00b5`; PR 3 `baddd10`, `db3b4b9`; and `70ce577`, a fix to PR 2's and PR 3's reading of
the agent-server's errors (§3.2 B2). The merges `c08ded0` and `64b5a8b` bring in `wiring/dr-1` and add no hunk of
their own: C3's launcher (`feat/launcher-agent-server-source` at `22272d9`), `config/defaults.json` naming the SDK
fork's commit `cef3b24` (tag `dr-1`) as the agent-server's source, `@openhands/typescript-client` pinned to the `dr-1`
release tarball, the client-pin guard reading that pin (`32bc76e`) and a `specs` input on `mock-llm-e2e.yml`
(`9881d24`). `ba4d883`, below C2's commits, is `deep-reasoning`'s fork-only copy of C3's live workflow, identical to
the file `22272d9` adds. So `git diff 9881d24..64b5a8b`, PR #3's diff, is C2 alone. Line numbers cited from the built
code are at `64b5a8b`; v1's are upstream's, as before.

## Gate B: what to read

**About 50 minutes, in this order.** The codebase stays closed. The Gate B set is this doc, C2's as-built document
(`as_built/c2-header-panels-and-menus.md` on deep-reasoning's branch `as-built/c2`, the Cartographer's) and the runs
below. Everything after §3 is kept whole as the reference D3, D5 and the PR split build against (Michael: don't force
compression); Gate B does not need it, except §7 and §10.

| # | Read | What it gives you | Minutes |
|---|---|---|---|
| 1 | This section and the v2 revision line below it | where the proof is, three rulings, and which sentences of v1 changed | 12 |
| 2 | §1 | what C2 changes, and why (unchanged but for PR 3's status) | 5 |
| 3 | §3.1 | the departures from the spec: item 1 approved on 2026-10-03, item 2 replaced by the size below, items 14 and 15 new | 4 |
| 4 | §3.2 | what the build changed, each with its reason and the test that pins it | 12 |
| 5 | §7 | the contract D3 builds against; §7.2's search and §7.4's ingress changed | 4 |
| 6 | §10 | E11 and the live tier, as run | 3 |
| 7 | Open the runs below | that they are green at `64b5a8b` | 2 |
| 8 | `as_built/c2-header-panels-and-menus.md` | what exists and its divergences, as the Cartographer read them | 8 |

**Three things to rule on.**

1. **Size.** The spec estimated C2 at ≈1.1k lines with tests and ≈3.5 h at Gate C (slot ≈350, slash menu ≈100,
   option picker ≈150, home-screen preview ≈100, tests ≈400); v1 at ≈2.1k and ≈5.5 h, PR 3 included (§3.1 item 2).
   The build is **6,955 lines added and 167 removed** in 89 files at `64b5a8b` (6,297 non-blank added): 2,635 of
   code, 3,982 of tests, 170 of translations (ten keys in upstream's 15 languages) and 168 of upstream's `specs/`
   documents and e2e guide, which upstream's `AGENTS.md` asks of a behaviour change. By PR: PR 1 3,122, PR 2 2,799,
   PR 3 996, `70ce577` 50. At ≈300 lines an hour Gate C reads it in about 23 h, four times v1's estimate and six and
   a half times the spec's: code 3.8 times the spec's ≈700, tests ten times its ≈400. §3.2 B20 has the table. The
   build recorded no reason for the growth; the reading there is this design's. The Scout and the Refactorer, after
   Gate B, are where it shrinks.
2. **The live tier is not a real task against a real model.** The workspace defines the live tier as a real task
   against real services, its outcome asserted. The spec's §4 layer 5 gives C2's live evidence as "its end-to-end
   tests, Playwright written as tests that assert behaviour", and §10 reads that as upstream's mock-LLM suite: the real
   stack (the `dr-1` agent-server installed from the SDK fork, automation, the built frontend, the ingress, Chromium),
   with openhands-sdk's `TestLLM` as the model and the scripted mock ACP agent (Appendix C) as the agent. No paid
   model runs, and dr-acp is not behind it: dr-acp's commands and namespace through the same agent-server are S2's
   live tier (deep-reasoning run 37147707860, on gpt-6-luna), and through Canvas they are D5's E12, which owns
   Canvas's real-model end to end. Ruling asked: accept §10's live tier as C2's, knowing it departs from the
   workspace's definition, or ask for a C2 run with dr-acp and a real model before D5.
3. **What a failed live option set says** (§3.2 B3). A 422 shows the agent's own sentence, as designed. Any other
   failure now toasts the client's raw error text: for the agent-server's 504 (the agent did not answer in 30 s) or
   500 (an agent's internal error), `HTTP request failed (504 Gateway Timeout): {"detail":"Internal Server
   Error","exception":"504: …"}`; before `70ce577` it toasted "Internal Server Error". The choices: (a) as built; (b)
   the same text, but through upstream's `retrieveAxiosErrorMessage`, which is what the model picker in the same
   composer shows for its failures through upstream's global mutation toast: identical for a 5xx, upstream's own
   sentences for a client timeout or a lost connection; one line; (c) one generic sentence of ours for every non-422
   failure: a new key in 15 languages and a test. **Recommended: (b)**: the two pickers in one composer then fail
   alike, at the cost of one line; the raw text names the status, and a 5xx on a set means an agent that hung or
   crashed. Nothing changes in code until Michael rules.

**Approved, now built:** the empty first controls event (the Conductor's ruling, carried at S2's Gate B and approved
by Michael). The newest event is the state, so a conversation shows an empty slash menu until the agent's commands
arrive (§3.2 B4). Pinned by `use-agent-controls.test.tsx › useConversationAgentControls › shows no agent commands
after an empty first report until the agent's menu arrives` (`86c00b5`).

**The evidence.** Both runs are at `64b5a8b`, the branch's head.

- **CI**, upstream's `ci.yml`, [run 37153648487](https://github.com/michaeltheologitis/OpenHands/actions/runs/37153648487), green:
  - **test-and-build (ubuntu)**, 14 min 6 s: `npm ci`; `npm run lint` (typecheck, eslint and prettier: 0 errors and
    379 warnings, all upstream's `shadcn/no-arbitrary-values` rule, three of them on C2's lines in
    `chat-input-agent-options.tsx`); `npm test` (vitest: 776 files passed and 1 skipped; **8,254 tests passed**, 1
    skipped, 7 todo; C2's 109 new test definitions, in 26 files, among them); `npm run build`; `npm run build:lib`;
    `npm pack --dry-run`.
  - **test-and-build (windows)**: `npm ci` and `npm run build` only. Upstream's matrix skips lint, tests and the
    library build there, so no C2 test runs on Windows.
  - **prepare-test-matrix**, green. **live-e2e**, upstream's real-model job, skipped: it runs only on
    `workflow_dispatch` or a push to `main` (`ci.yml:83–86`).
  - Also green on PR #3: the PR-title workflow ([run 37153647601](https://github.com/michaeltheologitis/OpenHands/actions/runs/37153647601): the conventional-title lint and its label).
- **Live tier**, as §10 defines it: the fork's `mock-llm-e2e.yml` dispatched on `feat/agent-surfaces` with its `specs`
  input naming C2's two specs and nothing else,
  [run 37153648974](https://github.com/michaeltheologitis/OpenHands/actions/runs/37153648974): **7 of 7 passed**
  (1.8 min; the job 3 min 43 s). The stack is the one `bin/agent-canvas.mjs` starts, so the agent-server is installed
  from `config/defaults.json` `sources`, the SDK fork at `cef3b24` (tag `dr-1`); each spec's `beforeAll` asserts that
  `/server_info` lists `canvas_conversation_panels_v1` or `acp_session_controls_v1`, which upstream's 1.50.1 does not.
  The model is the mock LLM server; the ACP agent is `mock-acp-server.py --session-controls`; no key, no paid model.
  The seven, each named for what it asserts:
  - `tests/e2e/mock-llm/canvas-extensions/mock-llm-canvas-extension-panels.spec.ts › App header panels ›`
    1. `the App's button follows Show panel and opens one right-hand panel for the conversation`: the App's button
       is the last of the top-right group, right after Show panel, and shows the manifest's icon; it opens the
       panel, whose tab is mounted with this conversation's id; Show panel closes the panel, and reopening it hides
       the drawer; Show overview closes it, and reopening it closes the overview; a page selects another tab of its
       panel through `surface.selectTab` (CX-001, CX-002).
    2. `a tab unpinned from the ⋯ menu stays unpinned after a reload, while the panel itself starts closed` (CX-003).
    3. `switching conversation with the panel open remounts it for the other conversation`, and for the first again
       on going back (CX-002).
    4. `on a narrow window the button opens the panel as a page of its own`: at 800 px, the page
       `/conversations/<id>/panel/demo-panel/demo`, mounted with the conversation's id, and its back button.
    5. `disabling the App removes its button and closes its panel`.
  - `tests/e2e/mock-llm/conversations/mock-llm-acp-session-controls.spec.ts › ACP agent commands and options ›`
    6. `the home screen previews the agent, and the picked profile reaches it before the first prompt`: the home row
       shows `Profile: fast` and `/` lists `/summarize`, not `/compare`; picking `thorough` lists `/summarize` and
       `/compare` with its hint `‹what to compare›`; sending `/compare a b` posts `acp_config_options:
       {"profile": "thorough"}`, and the agent's reply reads `profile=thorough` (E11's first three claims; ASC-001,
       ASC-002).
    7. `in the started conversation the profile is fixed and the agent offers no commands, after a reload too`: from
       the WebSocket, then after a reload from the REST search (E11's fourth claim and the spec's third falsifier;
       ASC-001).
- **The whole mock-LLM suite is not green, and none of its failures is C2's.** A run of all 79 tests at `64b5a8b`,
  [run 37153914745](https://github.com/michaeltheologitis/OpenHands/actions/runs/37153914745), is red; it is PR #3's
  one red check. It fails six of upstream's tests: automation lifecycle step 2 (create an automation and dispatch a
  run; it failed its retry too), agent-server conversation step 3 (run a conversation with the mock LLM), image upload,
  files tab step 2 (start a conversation and attach workspace metadata), the onboarding happy path, and same-model
  profile identity. The fork's base fails the same six:
  [run 37149694708](https://github.com/michaeltheologitis/OpenHands/actions/runs/37149694708) on `deep-reasoning` at
  `ba4d883`, with upstream's own agent-server 1.50.1 from PyPI and without C2's seven (72 tests). Five of the six also
  failed in the build's full run at `86c00b5`
  ([37152465164](https://github.com/michaeltheologitis/OpenHands/actions/runs/37152465164)), where files tab step 2
  passed, so that one is intermittent; PR #3's description names those five. C2's seven passed in both full runs.

**Which tests carry which property.** Each test's name states the property it pins. Paths are from the fork's root;
`›` separates `describe` blocks; `[…]` is an `it.each`; "Live" names the seven above by number.

*PR 1 · App header panels*

| Property | Tests |
|---|---|
| **The spec's falsifier: an App panel and the drawer are never open together** (CX-001; E11) | **Live:** 1. `__tests__/stores/conversation-store.test.ts › App header panels › keeps one right-hand panel after $steps.0.0 then $steps.1.0` [7 sequences: panel then drawer, drawer then panel, overview then panel, panel then overview, panel A then panel B, panel then closing the drawer, drawer then panel then closing it; the rule is checked after every step], `› opening a panel clears the drawer's toggled flag so the composer does not reopen it`, `› starts with no App panel open`; `__tests__/components/features/conversation/conversation-main.test.tsx › ConversationMain - App header panels › shows an open App panel in the drawer's column, keeping the drawer's content mounted but hidden`, `› leaves the column closed for a panel that is not registered` |
| **The spec's falsifier: an App page never mounts with the wrong conversation** (CX-002; E11) | **Live:** 1, 3, 4. `__tests__/components/features/conversation/conversation-app-panel.test.tsx › ConversationAppPanel › mounts the selected tab with the conversation's id, its path and its surface`, `› remounts the tab with the new conversation's id when the conversation changes`, `› disposes the old tab's mount before mounting the newly selected one`; `__tests__/components/features/conversation/conversation-app-panel-mobile-page.test.tsx › ConversationAppPanelMobilePage › shows the route's panel with its tabs and the selected tab's page for the conversation` |
| **The header button** | **Live:** 1, 4. `__tests__/components/features/conversation/conversation-app-panel-toggle.test.tsx › ConversationAppPanelToggles › renders no button on a Cloud backend`, `› renders no button for an App whose panel has no registered tab`, `› renders one button per registered panel, in panel order`, `› opens and closes its panel, with the tooltip and pressed state following`, `› navigates to the panel's page on a narrow window instead of opening the column`, `› shows the panel's icon, fetched with the session key`, `› draws the default glyph without fetching when the panel has no icon`, `› keeps the default glyph when the agent-server cannot serve the icon`; `src/api/canvas-extensions-service.test.ts › CanvasExtensionsService › fetches a panel icon as an authenticated blob from the captured backend` |
| **The panel: its tab row, the ⋯ menu, a page that selects a tab, a page that fails** | **Live:** 1, 2. `…/conversation-app-panel.test.tsx › ConversationAppPanel › is a region named after the panel, with its tabs in manifest order`, `› closes the panel when its selected tab is clicked`, `› opens and pins tabs from the ⋯ menu`, `› lets the page select another tab of its panel through surface.selectTab`, `› shows the unavailable state when a tab's mount rejects, and recovers on another tab` |
| **Each panel's selected tab and pins are kept per conversation; whether it is open is session-only** (CX-003) | **Live:** 2. `__tests__/hooks/use-conversation-app-panel-tabs.test.ts › useConversationAppPanelTabs › falls back to the first pinned tab when the stored one is gone, without writing`, `› unpinning the selected tab selects the next pinned one and hides it`, `› keeps an unpinned tab visible while it is selected`, `› keeps the selection and pins per conversation and per panel`, `› ignores a tab the panel does not have, with a warning`; `__tests__/conversation-local-storage.test.ts › conversation localStorage utilities › appPanelTabs › round-trips each panel's selected tab and unpinned tabs`, `› sanitizes a stored $stored` [6 malformed shapes], `› writes one panel's state without dropping another panel's` |
| **Only declared registrations; an agent-server without panels does not fail the App** (CX-004) | **Live:** 5. `src/components/features/canvas-extensions/canvas-extensions-runtime.test.tsx › CanvasExtensionsRuntimeProvider › conversation panels › lists a panel with its registered tabs in manifest order, paths without the leading slash`, `› fails activation when an App registers %s` [a panel's own id, an undeclared id], `› refuses tab registrations without failing the App on an agent-server without panels`, `› removes an App's panels when it is disabled`, `› re-activates an App whose manifest panels change`; `src/components/features/canvas-extensions/canvas-extension-card.test.tsx › CanvasExtensionCard › lists the App's header panels by title with their count`, `› says why an App's panels are missing on an agent-server without panels`, `› shows the App's activation error` |
| **The narrow-window page** | **Live:** 4. `…/conversation-app-panel-mobile-page.test.tsx › ConversationAppPanelMobilePage › returns to the conversation with the back button`, `› shows the unavailable state once the App is active without that panel` |
| **Feature detection, and the 60 s budget of an App's requests** | `__tests__/api/agent-server-compatibility-bundled-pin.test.ts › localAgentServerHasCapability › is true when the active local agent-server advertises the capability`, `› is false when the agent-server %s` [lists other capabilities, lists no capabilities], `› is false on a Cloud backend even with a cached local server_info`, `› is false when the cached server_info belongs to another local backend`; `src/api/canvas-extensions-service.test.ts › CanvasExtensionsService › gives an App's agent-server requests a minute, more than an App backend start takes` |

*PR 2 · Agent commands and the option picker*

| Property | Tests |
|---|---|
| **E11: the home screen's preview lists the agent's commands, and changing an option changes them** | **Live:** 6. `__tests__/hooks/query/use-acp-session-preview.test.tsx › useHomeAgentControls › previews the launch agent with the start's workspace, and again for each pick and workspace`, `› shows a pick in flight until its preview settles`; `__tests__/components/features/home/home-chat-launcher.test.tsx › HomeChatLauncher › ACP agent controls › shows the previewed agent's commands and starts with the values its preview accepted` |
| **E11: the started run uses the chosen value, and a start sends only values a preview accepted** (ASC-002) | **Live:** 6 (the start's body and the agent's reply). `use-acp-session-preview.test.tsx › useHomeAgentControls › starts only with option ids and select values the last accepted preview reported`, `› does not send values picked for another launch agent`, `› keeps the last accepted controls and start values when the agent refuses a pick, and says why`; `__tests__/api/agent-server-conversation-service.test.ts › AgentServerConversationService › ACP session controls › sends picked option values with the start, and an otherwise identical body without them`, `› previews with the body %s would start with, less its first message and user` [a profile launch, an agent_settings launch], `› gives the preview the agent-server's start-up time` |
| **The spec's falsifier and E11: the menu never offers a command the agent no longer lists; the newest report is the state** (ASC-001) | **Live:** 7 (live, then from the REST search). `__tests__/hooks/chat/use-agent-controls.test.tsx › useConversationAgentControls › offers the newest report's commands and its options except the model`, `› shows no agent commands after an empty first report until the agent's menu arrives`; `__tests__/hooks/query/use-latest-acp-session-controls.test.tsx › useLatestAcpSessionControls › searches the conversation's newest controls event by its module-qualified kind`, `› %s` [an older searched event loses to the live one, a newer searched event wins over the live one], `› keeps the newest of several live events`, `› is null when the conversation has no controls event`, `› ignores live events loaded for another conversation`, `› issues no search and reads nothing while disabled`; `__tests__/hooks/chat/use-slash-command.test.ts › useSlashCommand › agent commands › lists the agent's commands between the built-ins and the skills, with their input hints`, `› drops an item whose command repeats an earlier one, keeping the earlier`, `› replaces the agent's commands with each new report`, `› lists the agent's commands before the skills have loaded`, `› inserts the agent command's name followed by a space`; `src/api/event-service/event-service.api.test.ts › EventService › searchEvents › filters a local search by event kind`, `› filters a cloud search by event kind in the query string` |
| **The picker, which never offers the model** (ASC-003) | **Live:** 6, 7 (the fixed pill). `__tests__/components/features/chat/components/chat-input-agent-options.test.tsx › ChatInputAgentOptions › renders no row when the agent offers no options`, `› shows each option as a pill naming the option and its current value`, `› lists the values under a header per group, and choosing one sets it`, `› shows a value in flight with a spinner, and takes no other pick meanwhile`, `› shows an option with one value as fixed, with the option's description as its tooltip`, `› explains a fixed option without a description in Canvas's words`, `› disables the pickers while the composer is disabled`, `› shows the agent's sentence for a value it refused`; `use-acp-session-preview.test.tsx › useHomeAgentControls › offers the agent's select options except the model, and no boolean`; `__tests__/components/features/chat/slash-command-menu.test.tsx › SlashCommandMenu - agent commands › shows an agent command's input hint in its row, and no hint for commands without input` |
| **A live set, and what its failure says** (§3.2 B2, B3) | `use-agent-controls.test.tsx › useConversationAgentControls › sets a pick live, showing it in flight until the agent answers`, `› shows the agent's own sentence when it refuses a pick`, `› never shows a 5xx answer's placeholder detail as the agent's sentence` (it asserts the raw text of ruling 3's option (a)); `agent-server-conversation-service.test.ts › … › ACP session controls › sets a live option through the conversation client`; `agent-server-compatibility-bundled-pin.test.ts › getSdkHttpErrorDetail › reads the agent-server's detail sentence from an SDK HTTP error`, `› is null for %s` [a validation error list, a body without detail, a 5xx answer whose detail is the agent-server's placeholder, an error that is not an SDK HTTP error] |
| **Only where the agent-server supports them** (ASC-004) | `use-agent-controls.test.tsx › useConversationAgentControls › has no controls, and searches nothing, for %s` [an OpenHands conversation, an agent-server without acp_session_controls_v1, a Cloud backend]; `use-acp-session-preview.test.tsx › useHomeAgentControls › previews nothing when %s` [the agent-server lacks acp_session_controls_v1, the launch agent is not ACP], `› shows no commands and no picker, and starts with no values, when the preview answers %i` [400, 429, 501, 502, 504]; `home-chat-launcher.test.tsx › … › ACP agent controls › previews nothing and starts with an unchanged request without the agent-server capability`; `agent-server-conversation-service.test.ts › … › ACP session controls › refuses previews and live sets on a Cloud backend` |
| **A refused start value has its own banner; the controls event never renders or exports** | `__tests__/components/chat/error-message-banner.test.tsx › heads a refused start-time option with its title and shows the agent's sentence`; `__tests__/utils/acp-error-codes.test.ts › maps a refused start-time option value to its own header`; `__tests__/components/conversation-events/chat/event-content-helpers/should-render-event.test.ts › shouldRenderEvent - ACP session controls › never renders the agent's commands and options report`; `src/utils/transcript-export/index.test.ts › leaves the agent's commands and options reports out of the export` |

*PR 3 · App backend frames*

| Property | Tests |
|---|---|
| **An App's backend session is revoked only when its last frame closes** (CX-005) | `src/extensions/app-backend-session-keeper.test.ts › acquireAppBackendSession › mints one session per App on its ingress with the session key, shared by every lease`, `› revokes the session at the last release and not before`, `› refreshes the session a minute before it expires, and stops after the last release`, `› never refreshes sooner than its floor, however short the session`, `› tells every live lease of the App when a refresh fails`, `› keeps Apps apart: each has its own session`, `› leaves nothing behind when the acquisition is abandoned before the session exists`; `src/extensions/mount-app-backend-frame.test.ts › mountAppBackendFrame › keeps one session for two frames of the App and revokes it when the last one closes` |
| **The frame, and each failure reported once** (§6.2; §3.2 B2, B13) | `mount-app-backend-frame.test.ts › mountAppBackendFrame › appends a sandboxed frame of the App's backend to the container, at the page's path`, `› removes its frame and releases the session when disposed`, `› leaves nothing behind when disposed while the session is being minted`, `› keeps its frame in the container through session refreshes, and when one fails adds the notice beside it`, `› reports %s once, with a notice in the container, for %s` [unsupported-backend for a Cloud backend; no-ingress for an agent-server without an App ingress; not-ready for a backend that is not running, a 503 whose reason is under `exception`; no-ingress for an ingress the agent-server lacks, likewise; session-refused for a refused session, a 421]; `canvas-extensions-runtime.test.tsx › CanvasExtensionsRuntimeProvider › gives each App a frame mounter bound to that App and its backend` |

**Not pinned by any test:** the drawer's real terminal keeping its session behind an App panel (a stand-in for the
drawer's content is pinned as never unmounted; §11 item 5); the overview's hover peek with an App panel open (§3.1
item 7) and an App panel on an archived conversation (§3.1 item 6), both read; the selected tab clicked on the
narrow-window page (§3.2 B9, read); the empty first controls event end to end (the end-to-end start sends a value,
which the mock agent answers with a single event, S2's §3.2 B4; the unit test above crosses it); any browser run of an
App backend frame (§6.4: D3's and D5's); and `getSdkHttpServerErrorReason` on its own (the frame tests reach it
through `not-ready` and `no-ingress`). Mutation testing on the diff did not run (§3.2 B18). §4.9, §5.8 and §6.4 map
every test file.

**Revisions** (newest first; the Gate B reader approved the previous version, so each line says which sentences to
stop trusting):
- 2026-10-03 · v2 · brought in line with the build at `64b5a8b`, after Proof Green. Stop trusting: §1.2's and §6's
  "proposed" for PR 3 (approved as a scope addition on 2026-10-03); §3.1 items 2 and 13 (B20, B15); §4.4's spinner and
  activation-failure sentence for the panel body (B7); §4.7's and §5.7's file lists; §4.8's MSW mock mode (B6); §4.9's,
  §5.8's and §6.4's test tables and their mutation-testing line (now as built, B17, B18); §5.1's
  `getSdkHttpErrorDetail` (B2); §5.3's search kind and failure toast (B1, B3); §5.4's error statuses and the preview's
  workspace mode (B5, B10); §5.6's "only when `controls.options` is non-empty" (B11); §6.2 step 4 and §6.3's failed
  refresh (B2, B13); §7.2's search URL (B1); §7.4's and §11 item 1's "no launcher sets the ingress" (C3's default, now
  merged); §8 item 1 (done in S2); §9's client-pin row (B16); §10's live tier (B19); §11 items 2 to 5; Appendix A.1,
  A.2, A.6, A.7, A.8, A.10 and A.11 where a signature or its comment changed (each such line carries `// v2:`);
  Appendix C's timing of the first commands. Renumbered: v1's §3 is §3.1, and every "§3 item N" now reads "§3.1 item
  N". Added without changing earlier sentences: the "Matches the build" paragraph and this Gate B section; §3.1's
  notes and items 14 and 15; §3.2; notes in §1.3, §2 decisions M and N, §4.1, §4.3, §4.5, §5.5, §7.3, §7.4, §8 item
  2, §9's order paragraph and §10's E11 table; §11 items 6 to 8. Every signature block still parses as TypeScript,
  one field per line. Every change is listed, with its reason, in §3.2.
- 2026-10-02 · v1 · first full-depth version.

**Where this file lives, and why nothing trips over it.** `docs/design/c2-header-panels-and-menus.md` on
deep-reasoning's branch `design/c2`. That branch holds only documents: no docs site, no `pyproject.toml`, no test
runner, no package, so nothing collects, builds or ships this file. No design document goes into the fork: its pull
requests carry code, tests, translations and upstream's own product specs (`specs/*.md`, which upstream keeps
beside the code and tags with `// @spec` ids; §4.9, §5.8), in upstream's layout. The PR split leaves this file
behind.

**Reading guide.** Gate B: the section above. §3.1 lists every departure from the approved spec, §3.2 every change
the build made. D3's designer: §7 is the contract D3 builds against; read §6 with it, because it is how a panel page
reaches its own backend. The Conductor: §3, §9 (the client pin and the PR split) and §11 (open items). The PR
splitter: the "Matches the build" paragraph, §3.2 B16 and §9. The Implementer, the Cartographer and the Refactorer
read everything; Appendix A is the signature reference, Appendix B the new translation keys, Appendix C the
end-to-end agent's flags.

---

## 1 · What C2 changes, and why

### 1.1 What Canvas does today

- **The header's top-right group** is three buttons: `ConversationGitActionsToggle`, `ConversationOverviewToggle`
  ("Show overview") and `RightPanelToggle` ("Show panel") (`conversation-name-with-status.tsx:149–153`).
- **Show panel opens the drawer**, a resizable column beside the chat (`conversation-main.tsx:103–134`): a tab row
  (`ConversationTabs`, Files, Commits, Task list, Planner, Terminal, Browser, Usage, `conversation-tabs.tsx:86–155`)
  with a ⋯ menu that opens or pins each tab (`conversation-tabs-context-menu.tsx:91–154`), above the selected tab's
  content (`TAB_CONFIG`, `conversation-tab-content.tsx:20–28`). Its width is shared state from
  `useResizablePanels` (chat 30–80 %, so the column is 20–70 %). Open or closed is session-only, in the Zustand
  `useConversationStore` (`isRightPanelShown`, `hasRightPanelToggled`, `conversation-store.ts:115–153`); the selected
  tab and the unpinned tabs are kept per conversation in the `conversation-state-<id>` localStorage blob
  (`conversation-local-storage.ts:37–76`). Clicking the selected tab closes the drawer
  (`use-select-conversation-tab.ts:47–57`). On a narrow window (≤ 1024 px) the drawer is the page
  `/conversations/:id/panel` instead (`right-panel-toggle.tsx:45–56`, `routes.ts:121–124`).
- **Show overview** opens a column inside the chat area and closes the drawer; opening the drawer closes the
  overview (`conversation-overview-toggle.tsx:53–57, 90–108`). So "one right-hand panel at a time" already holds
  between those two, by an effect and by the toggle's own handler.
- **Canvas Apps** (`canvas-extensions-runtime.tsx`) mount only as left-rail routes: `registerPage(id, mount)` admits
  only ids the manifest declares under `contributes.pages` (`:57–82, 182–202`), and a page mounts through
  `mount({container, path, navigate})` (`types/canvas-extension.ts:51–60`). Upstream's own product spec plans the
  rest as "Slice 4: conversation surfaces … Add extension tabs/panels, then host-owned header/footer/badge slots …
  per-conversation lifecycle context" (`specs/canvas-extensions.md`, "Delivery plan"). C2 is a first cut of that
  slice.
- **The slash menu** (`use-slash-command.ts:57–82`) lists `BUILT_IN_COMMANDS` and the workspace's skills; it knows
  nothing of what an ACP agent offers. **The only agent control** in the message box is the ACP model picker
  (`chat-input-model.tsx`), driven by `switch_acp_model`.
- **The home screen** (`home-chat-launcher.tsx:92–230`) creates the conversation with the first message as its
  `initial_message`, so the ACP session does not exist until the first prompt is already on its way.

### 1.2 What C2 adds

Three generic surfaces, each an upstream-shaped pull request on `feat/agent-surfaces`. Nothing in them names
deep_reasoner or reads `_meta`.

| PR | What it delivers | Consumes | Consumed by |
|---|---|---|---|
| **1 · App header panels** | An App's `contributes.conversation_panels` gives each panel a button at the end of the header's top-right group, after Show panel. It opens the drawer's column with the App's tabs in the tab row and a ⋯ menu that opens and pins them; each tab is an App page mounted with the conversation's id. One right-hand panel at a time, by the store's own actions. A narrow window gets a page per panel. | S2 PR 2 (the manifest key, the icon route, `canvas_conversation_panels_v1`) | D3's Show decompositions |
| **2 · Agent commands and an option picker** | The agent's slash commands join the slash menu, with their input hints; a row above the message input shows the agent's config options (except the model) as pickers. On the home screen both come from S2's preview, and the chosen values go with the new conversation; in a conversation they come from the newest `ACPSessionControlsEvent`, and a pick is set live. | S2 PR 1 (`acp_session_controls_v1`, the preview, the set route, the event, the client) | D1's decomposition commands and namespace option; any ACP agent with commands or options (Claude Code's own slash commands among them) |
| **3 · App backend frames** (§6; proposed in v1, approved by Michael on 2026-10-03 as a scope addition) | `host.appBackend.mountFrame(container, {path, title})`: the App's own backend, served through the agent-server's App ingress, in a sandboxed frame whose session the host keeps alive. | the agent-server's existing App-backend bridge (`canvas_app_backend_bridge_v1`); the TypeScript client's existing `CanvasExtensionsClient` | D3's pages, to reach D2's Library API |

PR 3 exists because the spec's D3 says the Library API is reached "bridged by the agent-server under
`/app-backends/dr-library`", and that bridge is reachable only through a separate browser origin with a cookie
session a page cannot bootstrap without the session key (§6.1). Without it, D3 has no way to write to its backend.
*(v2: the spec's "Scope additions approved, 2026-10-03" (1) adds it to C2.)*

### 1.3 The flows, end to end

```text
App header panel (PR 1)
  agent-server (S2 PR 2): GET /api/canvas-extensions/installed → manifest.contributes.conversation_panels
  runtime: activate(host) → host.registerPage(<tab id>, mount)  — admitted because the manifest declares the tab
  header: [Git] [ⓘ Show overview] [▥ Show panel] [◇ Show <panel title>] ← one button per registered panel
  click ◇ → store.openAppPanel("<app>/<panel>")  (closes the drawer and the overview in the same set)
  column: the App's tab row + ⋯ ; body: mount({container, path, navigate, conversationId, surface})
  switch conversation → dispose, then mount with the new conversationId; click Show panel → panel closes

Agent commands and options (PR 2), home screen
  active agent profile is ACP, local agent-server has acp_session_controls_v1
  POST /api/acp/preview  (the start body Canvas would send, + acp_config_options the user picked)
     → {available_commands, config_options}         ← picker row + slash menu
  pick "Namespace: course_advisor" → preview again with {namespace: course_advisor} → that namespace's commands
  send → POST /api/conversations (same body + acp_config_options) → S2 applies them before the first prompt

Agent commands and options (PR 2), in a conversation
  newest ACPSessionControlsEvent (WebSocket, else one REST search by its module-qualified kind) → picker row + slash menu
  pick → POST /api/conversations/{id}/acp/config-options → the next event carries the agent's new state
  dr-acp: the first prompt clears its commands and narrows the namespace to one value → menu empty, pill fixed
```

---

## 2 · Decisions

The spec's seven expensive-to-reverse decisions in §2 stand. These are the next layer down.

| # | Decision | Why | Rejected |
|---|---|---|---|
| A | **One right-hand column with two kinds of content: the drawer's tabs or one App panel.** `isRightPanelShown` keeps its meaning ("the drawer is shown"); a new `activeAppPanel` key says which App panel is shown; the store's actions keep at most one of drawer, App panel and overview open (§4.2). | "One right-hand panel at a time" then holds by construction, in the only writer. Every existing caller that opens the drawer (`RightPanelToggle`, `useSelectConversationTab`, `canvas-ui.ts`'s agent `open_tab`, the mobile drawer page, `useChatInputLogic`) goes through `setIsRightPanelShown(true)`, which now also closes an App panel, so none of them changes. The column, its width and its resize handle are the drawer's own, which is what "opens the way Show panel does" means. | App tabs inside the drawer's tab union (upstream's Slice-4 note: "namespaced runtime IDs"): it touches every consumer of `ConversationTab` (the sanitizer, `TAB_CONFIG`, the ⋯ menu, `canvas-ui.ts`) and puts an App's tabs among Files and Terminal, which is Q4's option (a) that Michael's answer replaced with a button of its own. A second column beside the drawer: two right-hand panels at once, against the spec and the falsifier. |
| B | **A panel tab is an App page registered under the tab's id**, with `host.registerPage(<tab id>, mount)`; the mount context gains `conversationId` and a `surface` saying where the page is; the host API stays version `"1"`. | S2's decision F already makes tab ids contribution ids, unique across pages, panels and tabs. Reusing `registerPage` keeps one registration API and one mount signature; an App can hand the same mount function to a page and a tab. The context gains fields; nothing is removed or retyped, so every v1 App keeps working. | A `registerPanel(panelId, {tabs})` call: a second registration path for the same thing. A version bump to `"2"`: nothing breaks, so nothing needs it. |
| C | **The drawer's content stays mounted (hidden) while an App panel shows; an App tab is mounted only while it is visible.** | Today the drawer's content stays mounted while the drawer is closed (`conversation-main.tsx:109–133` only narrows the column), so the terminal keeps its session. Unmounting it whenever an App panel opens would be a behaviour change upstream would rightly refuse. An App tab, by contrast, gets a clean lifecycle: mounted on show, disposed on hide (§7.3). | Keeping App tabs mounted while hidden: Apps would run invisible, against a container of zero size, and a conversation switch would have to be pushed into a live page. |
| D | **Per conversation: each panel's selected tab and unpinned tabs, in the existing `conversation-state-<id>` blob under a new key. Session-only: which panel is open.** | Exactly the drawer's split (§1.1), so the same muscle memory applies; the blob already has a sanitizer that runs on every read, which the new key joins. | A global (not per-conversation) pin set: differs from the drawer for no reason. |
| E | **A narrow window gets a page per panel**, `/conversations/:id/panel/:extensionName/:panelId`, like the drawer's `/panel`. | The desktop column does not exist on a narrow window (`conversation-main.tsx:109`); the drawer solved the same problem with a route. | A full-screen overlay: a second narrow-window pattern. |
| F | **Every new surface is gated by an agent-server capability**, read from the cached `/server_info` of the local backend: `canvas_conversation_panels_v1` (PR 1), `acp_session_controls_v1` (PR 2), `canvas_app_backend_bridge_v1` (PR 3). On an agent-server without panels, an App's attempt to register an undeclared tab id is refused **without failing the App's activation**, and the Apps page says why. | Upstream's own precedent (`profile_secret_scope_v1`, `profile-field-support.ts:46–53`). A version floor would break on every fork tag (S2's decision H). Without the non-fatal refusal, an App with panels installed on an older agent-server (which drops the key) would lose its route pages too. | Raising `compatibility.minimumAgentServer`: no released upstream agent-server has these, so the floor would lock Canvas to our fork; the capability makes the old-server path a tested branch instead. |
| G | **Agent controls are a prop, `agentControls`, computed by the owner of each composer**: `HomeChatLauncher` (preview) and `InteractiveChatBox` (conversation). `CustomChatInput` passes them to the slash menu and the picker row. | The two sources need different context (the home launcher owns the pending workspace and the values; the conversation owns its id), and the shared input stays context-free. Upstream's review guide prefers named hooks and feature modules over branches in shared code. | Hooks inside `CustomChatInput` that branch on "home or conversation": the shared input would read the home launcher's local state through a store it does not own. |
| H | **In a conversation, the controls are the newer (by timestamp) of the event store's newest `ACPSessionControlsEvent` and one REST search for it by kind.** Replaced, never merged. | The WebSocket delivers changes; the history preload holds only the newest 50 events, and dr-acp's last controls event is sent at the first prompt, so in any long conversation it is older than those 50. Ordering by timestamp handles the race between the REST answer and a live event. | S2's `getAcpSessionControls` (it returns the lists without the event, so a REST answer could overwrite a newer live event; §8). A dedicated slice filled by the WebSocket handler: more edits in upstream's busiest context file. |
| I | **On the home screen, the preview body is built by the same function as the start body**, extracted from `createConversation`'s local path; the values the user picked live in a session-only store keyed by the launch agent; the start sends only values the last successful preview accepted. | S2's falsifier is "the commands a preview lists differ from those the started session lists"; the same builder and the same values make them differ only if the agent itself answers differently. A value the agent refused in the preview never reaches a start. | A preview body written by hand for the picker: a second builder, which drifts (secrets, hooks, workspace, profile). |
| J | **Agent controls on local backends only.** | The capability can be read only for the local agent-server; the Cloud start request (`AppConversationStartRequest`) has no `acp_config_options` and the Cloud App API has no preview or set route; Canvas Apps are already local-only (`use-canvas-extensions.ts:14–15`). Lifting it later is additive. | Reading controls events on Cloud too: half a feature (a menu with no picker) on a path no one in v1 runs. |
| K | **The picker is a row above the message input** (the spec's mock-up: `┌ Namespace: router ▾ ──`), one pill per option. | The actions row below the input already measures widths to decide what overflows (`chat-input-actions.tsx:228–348`); new pills there would enter that arithmetic and upstream's next merge conflicts (§9). A row of its own needs none. | Pills in the actions row; options inside the ⋯ overflow menu (hidden where the namespace matters most). |
| L | **Slash menu order: built-ins, then the agent's commands, then skills; a later item whose command repeats an earlier one is dropped.** | Built-ins are intercepted before the message is sent (`/btw`, `/model`, `/goal`, `/plan`, `/code`), so an agent command with the same name could never reach the agent: listing it would mislead. Between agent and skill, the agent's own command is the one an ACP agent acts on. | Showing duplicates (the menu keys items by command, `slash-command-menu.tsx:171`, so React would warn and selection would be ambiguous). |
| M | **The agent's refusals are shown in its own words**, read from the agent-server's `detail` by one small helper. *(v2, §3.2 B2: from a 4xx only; a 5xx's `detail` is always "Internal Server Error", and its reason is under `exception`.)* | S2 passes the agent's sentence through as `detail` (D1's `namespace is fixed once a conversation has started (it is 'router').`); the client's `HttpError` message wraps it in `HTTP request failed (422 …): {"detail": …}`, which no user should read. | A generic "the agent refused" toast. |
| N | **(PR 3; approved 2026-10-03) An App's backend is reached only in a host-owned, sandboxed frame on the agent-server's App ingress origin; the host keeps one ref-counted session per App alive.** | It is the bridge's own design (§6.1): a separate origin, a cookie session minted with the session key, non-GET requests only from that origin, a five-minute session. The host holds the key and can refresh; a page cannot. One session per App, because the cookie is per App and revoking one page's session would cut every other frame of that App. | Handing the page a session creator and letting each App refresh and revoke: every App re-implements the same timer, and a revoke on one tab's dispose kills its siblings. Calling `/app-backends/…` through `host.agentServer.request`: the bridge answers 421 or 503 on the agent-server's own origin. |

---

## 3 · Where this design departs from the approved spec, and what the build changed

### 3.1 Departures from, and additions to, the approved spec

Each item is a refinement inside C2's scope unless marked otherwise; if the Conductor reads any as a change of what
was approved, it goes back to Michael. *(v2: items 3 to 12 hold as built; items 1, 2 and 13 have notes; items 14 and
15 are new.)*

1. **A third pull request, App backend frames (§6), is outside C2's approved scope** and is proposed for the
   Conductor's ruling. Why: the spec's D3 reaches D2's API "bridged by the agent-server under
   `/app-backends/dr-library`", and the bridge works only through a separate ingress origin with a cookie session
   that only a holder of the session key can mint (§6.1); a page has no key. Without PR 3 (or another ruling), D3
   cannot save a decomposition. The bridge also needs the desktop app to configure an ingress origin, which no
   launcher does today (§11 item 1, for D5 and C3). *(v2: approved by Michael on 2026-10-03, spec, "Scope additions
   approved, 2026-10-03" (1); the same ruling's (2) gives every launcher a default ingress origin, C3's §2.9 B2,
   merged into this branch with `wiring/dr-1`.)*
2. **The estimate grows from ≈1.1k to ≈2.1k LOC with tests (≈5.5 h at Gate C instead of ≈3.5 h).** PR 1 ≈1.0k (the
   slot ≈600, tests ≈400 including one end-to-end spec), PR 2 ≈0.85k (≈500 and ≈350, with the mock agent's
   flags and one end-to-end spec), PR 3 ≈0.27k. Why: the spec costed neither the end-to-end specs (its §4 layer 5
   makes them C2's Gate B evidence), the persisted tab state's sanitizer and narrow-window page, the extraction
   that makes the preview body equal the start body (decision I), nor PR 3. *(v2: built at 6,955 lines added, about
   23 h at Gate C, §3.2 B20; for Michael's ruling, the Gate B section.)*
3. **The panel's title is the button's tooltip ("Show <title>", "Hide <title>") and the panel's accessible name,
   not a visible heading.** The drawer has no heading either; D3's mock-up has none.
4. **The App tab row scrolls horizontally when its tabs do not fit, instead of measuring and hiding the overflow**
   (`conversation-tabs.tsx:180–251` measures icon tabs); the ⋯ menu lists every tab either way. App tabs are text,
   not icons, so the drawer's arithmetic (which assumes collapsed icon tabs with one expanded label) does not apply.
5. **Clicking the selected App tab closes the panel**, as clicking the drawer's selected tab closes the drawer
   (`use-select-conversation-tab.ts:47–51`). The spec did not say; parity decided it.
6. **An App panel stays available on an archived conversation**, while Show panel is disabled there
   (`right-panel-toggle.tsx:41–43`). The drawer shows the conversation's runtime, which an archive no longer has;
   an App panel shows the App, which does not depend on it. The page receives the conversation's id either way.
7. **The overview's hover peek stays a drawer-only behaviour** (`conversation-overview-toggle.tsx:59–60`): hovering
   Show overview while an App panel is open opens no peek. Clicking it still opens the overview and closes the App
   panel.
8. **Agent controls only on local backends** (decision J).
9. **A command's input hint is shown in its menu row** (`/summarize-then-rank   comparing many courses
   ‹what to compare›`, the spec's mock-up), not as a placeholder inside the message box after the command is
   inserted. S2's §7 item 5 calls it a placeholder; a placeholder inside a `contentEditable` that already has text
   is a custom caret overlay, which buys little over the menu row.
10. **Boolean config options are not rendered.** S2 models them, but the bridge does not advertise boolean support,
    so no agent sends one (S2 §1, §7 item 6). Adding a toggle pill is additive when S2 advertises it.
11. **A conversation created without a first message** (the sidebar's new-thread menu,
    `local-new-conversation-menu.tsx`) shows no picker and no agent commands until its first message: its ACP
    session has not started, so no controls exist (S2 §7 item 4). For dr-acp that means the namespace is chosen on
    the home screen, which is the path the spec's v1-done criterion names. A preview for an existing, unstarted
    conversation would close the gap; it is an optional S2 addition (§8 item 3), not needed for v1.
12. **The Apps-page notice for an agent-server without panels is generic**: "{name} has header panels this
    agent-server does not support. Update the agent-server to show them." The spec's cell names the panel ("to show
    Show decompositions"), but that server dropped the key, so Canvas does not know the panel's title.
13. **C2 adds upstream product-spec entries** (`specs/canvas-extensions.md` gains the panel contract and invariants
    `CX-001`–`CX-005`; a new `specs/acp-session-controls.md` holds `ASC-001`–`ASC-004`; §4.9, §5.8, §6.4), and tags code and tests
    with `// @spec`, as upstream's `AGENTS.md` asks of behaviour changes. These are upstream's specs, not this
    design document. *(v2: they also hold `CX-006` and `ASC-005`, the `data-testid`s end-to-end tests rely on, §3.2
    B15.)*
14. *(v2)* **The live tier is the mock-LLM end to end, not a real task with a real model** (§10, §3.2 B19). The
    spec's §4 layer 5 gives C2's live evidence as its Playwright end-to-end tests, and v1's §10 runs them with the
    mock LLM and the scripted mock ACP agent. That follows the spec's words; it departs from the workspace's
    definition of a live tier (a real task against real services, its outcome asserted), so it goes to Michael at
    Gate B (ruling 2). Canvas's real-model end to end, with dr-acp, is D5's E12.
15. *(v2)* **Mutation testing on the diff did not run** (§3.2 B18). The spec's layer 3 names `npm run
    test:mutation:diff` for C2; no run is recorded.

### 3.2 Changed by the build (v2)

Each was checked against the code at `64b5a8b` and folded into the sections named. B1 to B5 follow S2's contract
as built; B6 to B9 are PR 1's, B10 to B12 PR 2's, B13 and B14 PR 3's; B15 and B16 the branch and the PR split; B17
to B19 the tests and the live tier; B20 the size. Where the build recorded no reason (in
a commit message, a code comment or PR #3's description), the reason given is marked as this design's reading.

**Against S2's contract**

- **B1. The events search uses the module-qualified kind** (`4caaecc`; §1.3, §5.3, §7.2). v1 wrote
  `kind: "ACPSessionControlsEvent"` for the search, in §5.3 and in §7.2's URL. Upstream's search matches
  `f"{module}.{name}"` (S2's §3.2 B2), so `useLatestAcpSessionControls` searches with the client's
  `ACP_SESSION_CONTROLS_EVENT_KIND`, `openhands.sdk.event.acp_session_controls.ACPSessionControlsEvent`; the event's
  own `kind` field stays `ACPSessionControlsEvent`, which `isACPSessionControlsEvent` reads in the event store. Also
  built: the event store's newest event counts only while the store holds this conversation's events
  (`loadedConversationId`), and the search is not retried. *Why* (the commit): "the newer of the event store's and
  one search by the module-qualified kind, so a report older than the preloaded history still counts"; v1 had
  upstream's search wrong, as S2's v1 did. *Pinned by:* `use-latest-acp-session-controls.test.tsx ›
  useLatestAcpSessionControls › searches the conversation's newest controls event by its module-qualified kind`, `›
  ignores live events loaded for another conversation`; live test 7, after its reload.
- **B2. A 5xx carries its reason under `exception`, not `detail`** (`70ce577`; §2 decision M, §5.1, §5.3, §6.2 step
  4, A.7, A.11). v1's §6.2 step 4 read `not-ready` from "a 503 whose detail says the backend is not ready", and §5.1's
  `getSdkHttpErrorDetail` returned a body's `detail` whatever the status. On the agent-server every answer of 500 or
  above is `{"detail": "Internal Server Error", "exception": "<status>: <reason>"}` (upstream's handler; S2's §3.2
  B26). Built: `getSdkHttpErrorDetail` returns `null` for any status of 500 or above; a new
  `getSdkHttpServerErrorReason(error)` returns a 5xx's `exception` string, else `null`; the session keeper looks for
  "not ready" and "ingress" in it. *Why* (the commit): "The App-backend session keeper looked for "not ready" and
  "ingress" in a 503's `detail`, so a stopped backend or an unconfigured ingress was reported as a refused session;
  it now reads the reason under `exception` … getSdkHttpErrorDetail returns null for a 5xx, so the placeholder is
  never shown as the agent-server's sentence". *Pinned by:* `agent-server-compatibility-bundled-pin.test.ts ›
  getSdkHttpErrorDetail › is null for %s` [a 5xx answer, whose detail is the agent-server's placeholder];
  `use-agent-controls.test.tsx › useConversationAgentControls › never shows a 5xx answer's placeholder detail as the
  agent's sentence`; `mount-app-backend-frame.test.ts › mountAppBackendFrame › reports %s once, with a notice in the
  container, for %s` [not-ready; no-ingress for an ingress the agent-server lacks], whose fake error now answers as
  the agent-server does (the commit: "the not-ready and no-ingress cases failed against the old keeper").
- **B3. A failed live set that is not a refusal toasts the client's raw error text** (`70ce577`; §5.3; the Gate B
  section's ruling 3). The code is v1's, `displayErrorToast(getSdkHttpErrorDetail(error) ?? error.message)`; B2
  changes what it shows. A 422 still shows the agent's sentence. A 5xx (the set route's 504 after 30 s; its 500 for an
  agent's internal error, -32603, whose message S2 puts under `exception` unmasked, S2's §3.2 B20) and any other
  failure toast `error.message`, which for the client's `HttpError` is `HTTP request failed (<status> <text>): <the
  body as JSON>`. Before `70ce577` a 5xx toasted "Internal Server Error". *Why* (the commit): "a failed config option
  set that is not a 422 now toasts the error itself". The model picker beside it reports its failures through
  upstream's global mutation toast (`use-switch-acp-model.ts`: "The rejection surfaces via the global mutation error
  toast"), whose `retrieveAxiosErrorMessage` shows the same text for a 5xx and upstream's own sentences for a client
  timeout or a lost connection. Michael rules (ruling 3); recommended: that helper, one line. *Pinned by:*
  `use-agent-controls.test.tsx › useConversationAgentControls › never shows a 5xx answer's placeholder detail as the
  agent's sentence`, which asserts the raw text.
- **B4. The first controls event after a start can be empty; the newest event is the state** (`86c00b5`; §5.3, §5.5,
  §7.2). v1 said "No event at all means no commands and no picker" and nothing of an empty first event. S2's §3.2 B4
  found that every session start persists one event, and that an agent that sends its menu after answering
  `session/new` (dr-acp does, and so does the mock agent, Appendix C) is published first with no commands, then with
  them; nothing in the event says which. The Conductor ruled, S2's Gate B carried it and Michael approved: nothing
  changes in S2; C2 follows the newest event and shows an empty slash menu until the commands arrive. v1's code
  already did (replace, never merge); `86c00b5` pins it. *Why* (the commit): "The conversation's controls follow the
  newest event, so the slash menu holds no agent command until the menu arrives, and then lists it." *Pinned by:*
  `use-agent-controls.test.tsx › useConversationAgentControls › shows no agent commands after an empty first report
  until the agent's menu arrives`.
- **B5. A 501, and any failure but a refusal, hides the controls** (`4caaecc`; §5.4). v1: "400, 429, 502 and 504
  show no agent commands and no picker". Built: any failed preview other than a 422 shows no commands, no picker and no
  start values; the tests name 400, 429, 501, 502 and 504. 501 is the agent-server's answer to every preview in the
  Docker conversation runtime (S2's §3.2 B3). *Why* (the commit): "Any other preview failure (400, 429, 501, 502,
  504) shows no controls; the user can still start." *Pinned by:* `use-acp-session-preview.test.tsx ›
  useHomeAgentControls › shows no commands and no picker, and starts with no values, when the preview answers %i`
  [400, 429, 501, 502, 504].

**PR 1 · App header panels**

- **B6. The demo-panel fixture is not served in MSW mock mode, and carries an icon and a tab-selecting button**
  (`1828cec`; §4.7, §4.8). v1: `canvas-extensions-handlers.ts` serves it beside `demo-page` in mock mode. Built: the
  mock handlers are untouched, so mock mode shows no panel. The fixture gains `icon.svg`, writes `conversation=<id>
  path=<path> tab=<tab>` into an element with `data-testid="demo-panel-context"`, and puts in each tab a button
  (`demo-panel-select-details`) that calls `surface.selectTab("details")`, so the end-to-end spec checks the icon and
  `selectTab` too. *Why:* for the icon and the button, the commit: "it writes its mount context into the page and
  counts mounts and disposes, and the tests read the lifecycle from it"; for mock mode none recorded, and this
  design's reading is that no test runs panels in mock mode, while the end-to-end spec installs the fixture by path
  on the real agent-server. *Pinned by:* live test 1.
- **B7. The panel body shows only a page's own failure; an App still activating, or failed, leaves the column
  closed** (`1828cec`; §4.4). v1: the body shows `LoadingSpinner` while the App activates and the unavailable state
  when its activation failed. Built: on a wide window an App panel shows only once its tabs are registered (§4.2: a
  key with no registered panel reads as closed), so the body never sees an activating or failed App. It shows the
  unavailable state (a new component, `ConversationAppPanelUnavailable`, with the route page's markup) when the tab's
  `mount` throws or rejects, and keeps the emptied container mounted, hidden, beside it. The narrow-window page shows
  the spinner and the unavailable state as v1 said. *Why* (the code): "The container stays mounted under an error,
  so selecting another tab has somewhere to mount into." That the spinner had nowhere to show is this design's
  reading. *Pinned by:* `conversation-app-panel.test.tsx › ConversationAppPanel › shows the unavailable state when a
  tab's mount rejects, and recovers on another tab`; `conversation-main.test.tsx › ConversationMain - App header
  panels › leaves the column closed for a panel that is not registered`; `conversation-app-panel-mobile-page.test.tsx
  › ConversationAppPanelMobilePage › shows the unavailable state once the App is active without that panel`.
- **B8. Smaller interface changes in PR 1** (`20b90cb`, `1828cec`; §4.1, §4.3, §4.4, A.2, A.6). Each is additive. A
  reason is quoted where the build recorded one; otherwise the reason is this design's reading.
  - The runtime's `notices` hold an i18n key, not a sentence; the Apps card translates it with the App's display
    name, and shows the activation error instead when there is one.
  - A registered tab's `contribution.path` is stored without its leading `/` (`""` for `/`), the form its mount
    receives.
  - `ConversationAppPanelProps` gains `leading?: React.ReactNode`, rendered before the tab row: the narrow-window
    page's back button sits in the panel's own 40 px row, not in a bar above it.
  - `ConversationTabNav` gains `testId?: string`, so an App tab is `conversation-app-panel-tab-<tab id>` rather than
    the drawer's `conversation-tab-<value>`.
  - The desktop column gets `data-testid="conversation-right-column"`, and a mounted tab's container `data-tab-id`.
  - `convertImageToBase64` takes a `Blob` (it took a `File`), so the icon query reuses it.
  - `CanvasExtensionsService` names its 60 s request timeout `CANVAS_EXTENSION_AGENT_SERVER_REQUEST_TIMEOUT_MS`,
    documented on `host.agentServer.request` and in upstream's spec; the value is upstream's. *Why* (the commit):
    it "names the 60 s timeout of requests to an App's agent-server, host.agentServer.request included"; (the code)
    "an App backend start can take 30 s".
  - `ConversationAppPanelToggles` checks only for a conversation id. On a Cloud backend the runtime has no Apps
    (`use-canvas-extensions.ts`), so there is no panel and no button, as v1 said.

  *Pinned by:* the tests §4.9 lists.
- **B9. On the narrow-window page, clicking the selected tab clears the open-panel key and leaves the page as it is**
  (`1828cec`; §4.5). The page renders `ConversationAppPanel`, whose click on the selected tab calls
  `closeAppPanel()`: the store's `activeAppPanel` becomes `null`, which closes a panel left open for the wide column,
  and the page stays. v1's "it does not touch `isRightPanelShown`" holds. *Why:* none recorded; this design's
  reading: the shared component's rule (§3.1 item 5), which a page cannot honour by closing itself. Read, not tested.

**PR 2 · Agent commands and the option picker**

- **B10. The preview sends a workspace mode only with a workspace** (`4caaecc`; §5.4, A.2, A.10). v1 keyed the
  preview by `(launchKey, workingDir, workspaceMode, values)` and always passed the mode. Built:
  `useAcpSessionPreview` passes `workspaceMode` only when `workingDir` is set, and keys on `workspaceMode ?? null`,
  so `ACP_SESSION_CONTROLS_QUERY_KEYS.preview` takes `WorkspaceMode | null`. *Why* (the code): "The start sends a
  workspace mode only with a workspace (HomeChatLauncher)", and decision I needs the preview's body to be the
  start's. *Pinned by:* `use-acp-session-preview.test.tsx › useHomeAgentControls › previews the launch agent with the
  start's workspace, and again for each pick and workspace`.
- **B11. The picker row, as built** (`4caaecc`; §5.6, A.10).
  - It keeps only `select` options (v1: it drops `boolean` ones), the same today, since an option is one or the
    other (`ACPConfigOptionType`).
  - It renders when there are options **or** a refusal sentence (v1: only with options); the sentence is the row's
    last line, `data-testid="agent-option-rejection"`, where §5.4 put it.
  - Choosing the value that is already current sends nothing.
  - A pill carries `data-value` (the value shown) and, when fixed, `data-fixed="true"`; the row is
    `data-testid="agent-options"`, and an open menu `agent-option-<id>-menu`.

  *Why:* the attributes are ASC-005's (B15); for the rest none recorded, and this design's reading is that a refusal
  must show even when no option is left to show, and that a pick of the current value should not cost a round trip
  to the agent. *Pinned by:* `chat-input-agent-options.test.tsx › ChatInputAgentOptions` (8 tests, the Gate B
  section's table).
- **B12. Where PR 2's names live** (`20b90cb`, `4caaecc`; §5.1, A.7, A.10). `HomeLaunchContext` is declared in
  `use-acp-session-preview.ts` and re-exported from `use-agent-controls.ts` (v1: declared in `use-agent-controls.ts`).
  Of §5.1's helpers, `localAgentServerHasCapability` landed with PR 1 (`20b90cb`) and `getSdkHttpErrorDetail` with
  PR 2 (`4caaecc`); v1 put both in PR 1. *Why:* none recorded; this design's reading: the preview hook takes the
  context, and `use-agent-controls.ts` imports the preview hook, not the reverse; the `detail` helper has no user in
  PR 1.

**PR 3 · App backend frames**

- **B13. Which failure is which, and what a failed refresh does** (`baddd10`, `70ce577`; §6.2, §6.3, A.11). v1:
  `session-refused` for 401, 403, 409 and 421, and a failed refresh reports `session-refused` to the App's live
  frames. Built:
  - `unsupported-backend` for any backend that is not local; `no-ingress` when the cached `/server_info` lacks
    `canvas_app_backend_bridge_v1` or `app_backend_ingress_url`, or when minting answers a 503 whose reason (under
    `exception`, B2) names the ingress; `not-ready` for a 503 whose reason says "not ready"; `session-refused` for
    every other failure, whatever its status, a network error included.
  - A failed refresh reports, by the same rule, the reason its error maps to, to every live frame of the App.
  - A frame stays in its container until it is disposed, also after a failed refresh: the notice is added before
    it, not in its place.
  - A session whose minting failed is forgotten, so the App's next frame tries again.

  *Why* (`baddd10`): the frame is "kept there, across session refreshes, until the returned disposer runs", and "a
  failed refresh reaches every live frame of the App". The catch-all `session-refused` and the forgotten session:
  none recorded; this design's reading: a frame cannot act on the difference, and one failed mint should not block
  the App's next frame. *Pinned by:* `mount-app-backend-frame.test.ts › mountAppBackendFrame › reports %s once, with a
  notice in the container, for %s` [5 cases], `› keeps its frame in the container through session refreshes, and
  when one fails adds the notice beside it`; `app-backend-session-keeper.test.ts › acquireAppBackendSession › tells
  every live lease of the App when a refresh fails`. The forgotten session is not pinned.
- **B14. Smaller interface changes in PR 3** (`baddd10`; A.2, A.11, Appendix B). `unsupported-backend` shows the
  no-ingress sentence (`CANVAS_EXTENSIONS$APP_BACKEND_NO_INGRESS`); v1's Appendix B gave it no key, and the build
  adds none. `CanvasExtensionsService.createAppBackendSession` returns `AppBackendSession`, the client's own answer
  type, rather than v1's `AgentServerAppBackendSessionResponse`. The keeper exports `appBackendError` and
  `toAppBackendError`, which `mountAppBackendFrame` shares. *Why:* none recorded; this design's reading: Apps do not
  run on Cloud at all, so one sentence serves; the client's type cannot drift from the client.

**The branch and the PR split**

- **B15. End-to-end test ids are a contract: `CX-006` and `ASC-005`** (`a5436be`, `82ff26a`; §3.1 item 13, §4.9,
  §5.8). v1 planned `CX-001`–`CX-005` and `ASC-001`–`ASC-004`. Upstream's specs also hold `CX-006` (header panels)
  and `ASC-005` (agent controls), each a table of the `data-testid`s that end-to-end tests select by: "a contract
  for end-to-end tests; renaming one is a breaking change". The slash menu gains one for it, `slash-command-item`,
  with the command in `data-command`. *Why* (the commits): "CX-006, the panel test ids end-to-end tests may rely on";
  "ASC-005, the test ids end-to-end tests may rely on". *Pinned by:* the two end-to-end specs, which select by them.
- **B16. The client pin arrives after PR 2's commits** (`c08ded0`; §9). v1's §9: PR 2 needs a client built from an
  SDK fork tag carrying S2's PR 1, and "PR 2's first commit is the client bump". Built: `4caaecc` imports
  `ACP_SESSION_CONTROLS_EVENT_KIND` and the controls types from `@openhands/typescript-client`, but at `4caaecc` the
  pin is still upstream's `1.50.1`, whose client exports none of them (the SDK fork's `v1.50.1` has no
  `ACP_SESSION_CONTROLS_EVENT_KIND`; its `cef3b24`, tag `dr-1`, exports it from the root). The pin arrives with the
  merge `c08ded0`, after PR 2's and PR 3's commits, so `4caaecc`, `82ff26a`, `baddd10` and `db3b4b9` should not
  type-check on their own; `64b5a8b`, the head CI ran, does. *Why:* none recorded. What it means: the PR split puts
  the client pin before PR 2's commits, as §9 says; nothing in the code changes. Read from those commits'
  `package.json` and the client's exports, not by building them.

**Tests and the live tier**

- **B17. The tests, as built** (§4.9, §5.8, §6.4). Every file v1 named exists but one, moved:
  - Added: two new files, `__tests__/hooks/chat/use-agent-controls.test.tsx` (a conversation's controls: the newest
    report, the empty first report, a live set, a refusal, a 5xx, the gate) and
    `src/components/features/canvas-extensions/canvas-extension-card.test.tsx` (the card's panels and notice);
    additions to two existing ones, `__tests__/api/agent-server-compatibility-bundled-pin.test.ts` (the capability
    and `detail` helpers) and `src/api/canvas-extensions-service.test.ts` (the icon and the timeout); and a helper,
    `__tests__/helpers/canvas-extension-panels.tsx`, which installs fake panel Apps into the real runtime.
  - Moved: the event-service tests are in `src/api/event-service/event-service.api.test.ts` (v1:
    `__tests__/api/event-service.test.ts`); the narrow-window page's are in a sibling file,
    `conversation-app-panel-mobile-page.test.tsx`, one of v1's two options.
  - Decision C's "a test asserts its node and session survive": the test replaces the drawer's content with a
    stand-in and asserts it is hidden and never unmounted; the real terminal's session is not exercised (§11 item 5).
  - The end-to-end specs assert what v1 listed and also: the start's body carries `acp_config_options`; the button
    shows the manifest's icon; a page selects another tab; going back to the first conversation remounts the panel for
    it; the narrow page's back button.

  Counts: 109 vitest test definitions (11 of them `it.each` tables) in 26 files, and 7 Playwright tests in 2. *Why:*
  none recorded; this design's reading: each added file covers a module v1 gave no test file, and the move follows
  upstream's existing file.
- **B18. Mutation testing on the diff did not run** (§3.1 item 15, §4.9, §5.8; the spec's §4 layer 3). v1: `npm run
  test:mutation:diff` (Stryker) runs on each PR, and the as-built lists the survivors. No workflow in the fork runs
  it, and neither PR #3's description nor the task's notes record a run. Nothing in the code changes; layer 3's
  evidence lacks it, for the Conductor to have it run on `9881d24..64b5a8b` or to waive it.
- **B19. The live tier, as run** (§10; §3.1 item 14; the Gate B section's ruling 2). v1: the two specs green in the
  fork's mock-LLM run at the branch's head, dispatched on the task branch. Built: the fork's wiring adds a `specs`
  input to `mock-llm-e2e.yml` (`9881d24`, fork-only, merged as `64b5a8b`), so one dispatch runs C2's two specs alone;
  run 37153648974 is that run, 7 of 7. A dispatch without the input runs the whole suite, which fails six of
  upstream's tests on this branch and on the fork's base alike (the Gate B section). *Why* (the merge `64b5a8b`):
  "Brings in the fork's specs input for a manual mock-LLM E2E run, so C2's two end-to-end specs can run on their
  own."

**Size**

- **B20. Size** (§3.1 item 2). `git diff --numstat 9881d24..64b5a8b`: 6,955 lines added and 167 removed, in 89
  files; 6,297 of the added lines are not blank.

  | Part | Spec | v1 | Built, added (removed) |
  |---|---|---|---|
  | Code (`src/`, not tests or fixtures) | ≈700 (slot ≈350, slash menu ≈100, picker ≈150, preview ≈100) | ≈1.1k, and PR 3's share | 2,635 (141) |
  | Tests: vitest | ≈400 in all | ≈750, and PR 3's share | 3,284 (11) |
  | Tests: the two Playwright specs | | | 474 |
  | Tests: the mock ACP agent's controls mode; the e2e mapping; the fixture App | | | 128 (12); 29; 67 |
  | Translations: ten keys in 15 languages | — | — | 170 |
  | Upstream's `specs/`; its e2e guide | — | — | 166 (1); 2 (2) |
  | **Total** | **≈1.1k, ≈3.5 h at Gate C** | **≈2.1k, ≈5.5 h** | **6,955 (167); about 23 h at Gate C** |

  By PR, per commit: PR 1 3,122 added (v1 ≈1.0k), PR 2 2,799 (v1 ≈0.85k), PR 3 996 (v1 ≈0.27k), `70ce577` 50; 12
  more than the diff, because `70ce577` rewrote lines PR 2 and PR 3 added. `ba4d883` and the wiring are not counted.
  The build recorded no reason for the growth. This design's reading: the tests (3,982) are ten times the spec's
  ≈400 and five times v1's ≈750, because the component and hook tests render the real runtime, stores and query
  client and fake the services, which costs setup in every file (the shared panel-App helper is 136 lines, the
  preview tests 357), and because the two end-to-end specs and the mock agent's controls mode are 631 lines with
  their mapping. The code is 2.4 times v1's ≈1.1k (which left PR 3's share unstated), because of JSDoc on nearly
  every export, in upstream's style, and because the parts v1 costed lightly are large: the runtime's
  declared-contribution resolution and panel derivation (213 lines added to `canvas-extensions-runtime.tsx`),
  `use-agent-controls.ts` with its two hooks (212), the picker (221) and the frame keeper (217). Translations and
  upstream's specs were in neither estimate. At ≈300 lines an hour Gate C reads it in about 23 h (22.6 h without
  the translations). The Scout and the Refactorer, after Gate B, are where it shrinks.

---

## 4 · PR 1: App header panels

### 4.1 Manifest types and registration

**Types** (`src/types/canvas-extension.ts`, Appendix A.1). `CanvasExtensionContributions` gains
`conversation_panels?: CanvasExtensionConversationPanelContribution[] | null`, each with `id`, `title`, `icon`
(a package-relative path or `null`) and `tabs: CanvasExtensionPanelTabContribution[]` (`id`, `title`, `path`).
These mirror S2's `CanvasExtensionConversationPanel` and `CanvasExtensionPanelTab` field for field; they sit beside
the manifest types Canvas already declares locally for pages (upstream keeps the manifest types local; the client
has no hand-written manifest mirror). `src/lib/index.ts` exports the new types next to the existing ones.

**Registration** (`canvas-extensions-runtime.tsx`). `getDeclaredPage` (`:57–82`) becomes
`resolveDeclaredContribution(extension, id)`, which answers one of:

- `{kind: "page", contribution}`: as today, path normalized and validated.
- `{kind: "panel-tab", panel, tab}`: the id is a tab of a declared panel. The panel id, the tab id and the tab path
  are re-validated the way pages are (kebab-case ids; a path of `/` or an absolute kebab-case path, S2 §5.1), as
  defence in depth against a manifest from a server that validated less.
- `{kind: "panels-unsupported"}`: the id is declared nowhere **and** the local agent-server lacks
  `canvas_conversation_panels_v1`.
- otherwise it throws as today: `Extension <name> registered undeclared page "<id>".` A panel's own id throws
  `Extension <name> registered panel "<id>"; register its tabs instead.`

`registerPage` keeps its signature and its "more than once" check. For a page, behaviour is unchanged. For a tab,
the registration is stored in the extension's map with its panel and tab. For `panels-unsupported`, nothing is
stored, the extension gets a **notice** (not an error) whose text is `SETTINGS$APPS_PANELS_UNSUPPORTED`, and
`registerPage` returns a no-op disposer, so the App's other registrations, and its activation, go on.

**The runtime value** gains `panels` and `notices` (Appendix A.2):

- `panels: RegisteredCanvasExtensionPanel[]`: for each enabled, activated App, in installed order, each declared
  panel (manifest order) that has at least one registered tab, with its registered tabs in manifest order. A panel
  whose tabs are only partly registered shows only those tabs. Derived from the registrations in a `useMemo`, so
  activation re-runs, disables and backend switches remove panels with their pages (`:244–254`).
- `notices: ReadonlyMap<string, string>`, keyed by App name like `errors`. *(v2, §3.2 B8: the value is an i18n key,
  which the Apps card translates with the App's display name.)*

The activation signature (`:119–141`) adds `conversation_panels` beside `pages`, so a manifest whose panels
changed re-activates the App.

**The mount context for route pages** gains `conversationId: null` and `surface: {kind: "page"}`
(`canvas-extension-page.tsx:47–51`). The page route's mount effect (`:34–75`) moves unchanged into a hook,
`useCanvasExtensionMount` (`src/components/features/canvas-extensions/use-canvas-extension-mount.ts`), which the
route page and the panel tab body both call; the route page's behaviour does not change (its tests stay as they are
and pass).

### 4.2 State: one column, at most one panel

`useConversationStore` (`conversation-store.ts`) gains one field and two actions (Appendix A.3):

```ts
interface ConversationState {
  // …existing fields…
  activeAppPanel: ConversationAppPanelKey | null; // `${extensionName}/${panelId}`; session-only, like the drawer
}

interface ConversationActions {
  // …existing actions…
  openAppPanel: (key: ConversationAppPanelKey) => void;
  closeAppPanel: () => void;
}
```

and two existing setters gain one clause each:

| Action | Sets | So that |
|---|---|---|
| `openAppPanel(key)` | `activeAppPanel = key`, `isRightPanelShown = false`, `hasRightPanelToggled = false`, `isOverviewPanelShown = false`, `isOverviewPanelPeeked = false` | the drawer and the overview close in the same `set`; `hasRightPanelToggled` false keeps `useChatInputLogic`'s mount effect (`use-chat-input-logic.ts:62–75`), which re-applies `setIsRightPanelShown(hasRightPanelToggled)`, from reopening the drawer over the panel |
| `closeAppPanel()` | `activeAppPanel = null` | — |
| `setIsRightPanelShown(true)` (existing) | also `activeAppPanel = null` | every drawer opener closes the panel without changing (decision A) |
| `setIsRightPanelShown(false)` (existing) | unchanged | the mobile drawer page's unmount and `useChatInputLogic` do not touch an open App panel |
| `setIsOverviewPanelShown(true)` (existing) | also `activeAppPanel = null` | Show overview closes the panel; the toggle's handler (`conversation-overview-toggle.tsx:90–108`) needs no change |

**Invariant (`CX-001`): after every store action, an App panel (`activeAppPanel !== null`) is never open together
with the drawer (`isRightPanelShown`) or the overview (`isOverviewPanelShown`).** The store's actions are the only
writers of the three fields. Between the drawer and the overview, upstream's existing rule stands unchanged (the
overview toggle's effect closes the overview when the drawer opens, `conversation-overview-toggle.tsx:53–57`).

**A key whose panel is not registered** (the App was disabled, re-activates, or the backend switched) is treated as
closed wherever it is read: the column and the button derive "open" from the key *and* a registered panel with that
key (`useRegisteredAppPanel`, Appendix A.2). No effect clears it; the next opener of anything overwrites it, and a
re-activation that registers the panel again shows it again without a flicker.

### 4.3 The header button

`ConversationAppPanelToggles` (new, `src/components/features/conversation/conversation-app-panel-toggle.tsx`)
renders after `<RightPanelToggle />` in the top-right group (`conversation-name-with-status.tsx:152`, one added
line). It renders nothing on a Cloud backend, without a conversation id, or when no panel is registered; otherwise
one `ConversationAppPanelToggle` per registered panel, in `panels` order. *(v2, §3.2 B8: it checks only the
conversation id; a Cloud backend has no Apps, so no panel.)*

Each button mirrors `RightPanelToggle` (`right-panel-toggle.tsx`): `ChatActionTooltip` with
`t(CONVERSATION$SHOW_APP_PANEL, {title})`, or `t(CONVERSATION$HIDE_APP_PANEL, {title})` while that panel is open on
a wide window; the same hit target (`mobileTopBarIconButtonClassName`, `size-7`); `aria-pressed` true while open
(false on a narrow window, as the drawer's); `data-testid="conversation-app-panel-toggle-<extension>-<panel>"`.

- **Icon:** the panel's `icon`, fetched as a `Blob` with the session key through
  `CanvasExtensionsService.fetchPanelIcon` (S2's `GET …/installed/{name}/panels/{panel_id}/icon`, the way bundles
  are fetched, never a bare `<img src>`), turned into a `data:` URL in the query function and shown in an `<img>`
  (an SVG in an `<img>` runs no script). The query is keyed by backend, App, resolved revision and panel; a missing
  icon, a 404 or any failure draws the default `lucide-react` `PanelRight` glyph.
- **Click on a wide window:** the panel is open → `closeAppPanel()`; otherwise `openAppPanel(key)`.
- **Click on a narrow window** (`useBreakpoint()`): navigate to
  `buildConversationAppPanelPath(conversationId, extensionName, panelId)` through `useNavigation()` (upstream asks
  components not to import `react-router` directly).

### 4.4 The panel in the column

`ConversationMain` (`conversation-main.tsx`) derives `appPanel = useRegisteredAppPanel(activeAppPanel)` and
`isRightColumnOpen = isRightPanelShown || appPanel !== null`, and uses `isRightColumnOpen` where it now uses
`isRightPanelShown` for the chat's width, the resize handle and the column (`:77, 98, 104, 113, 116`). Inside the
column (*v2:* as built, with the `hidden` attribute and the column's `data-testid="conversation-right-column"`):

```tsx
<div className="flex flex-col flex-1 min-h-0 bg-surface border-l border-border overflow-hidden">
  <div className="flex flex-1 min-h-0 flex-col" hidden={appPanel !== null}>
    <div data-testid="tabs-pane-header" className="flex shrink-0 flex-col border-b border-border">
      <ConversationTabs isPanelResizing={isDragging} />
    </div>
    <div className="flex-1 min-h-0 flex flex-col">
      <ConversationTabContent />
    </div>
  </div>
  {appPanel && conversationId ? (
    <ConversationAppPanel conversationId={conversationId} panel={appPanel} />
  ) : null}
</div>
```

`ConversationAppPanel` (new, `src/components/features/conversation/conversation-app-panel/`) is a region with
`aria-label={panel.contribution.title}` and two parts:

**The tab row** (`border-b`, `min-h-10 p-1`, like the drawer's): the visible tabs as `ConversationTabNav` items, then
a ⋯ `EllipsisButton` with `ConversationAppPanelTabsMenu`. `ConversationTabNav`'s `icon` becomes optional; without
an icon it always shows its label (one changed prop and one condition in `conversation-tab-nav.tsx`; *v2, §3.2 B8:*
and a `testId` prop, so an App tab gets its own id). The row
scrolls horizontally when the tabs do not fit (§3.1 item 4). Clicking a tab that is not selected selects it;
clicking the selected tab closes the panel (§3.1 item 5). `data-testid="conversation-app-panel-tab-<tab id>"`.

**The ⋯ menu** lists every registered tab with "open" and "pin" exactly like the drawer's menu
(`conversation-tabs-context-menu.tsx:169–247`: `ContextMenu`, the pill icons, `CONVERSATION$PIN_TAB` /
`CONVERSATION$UNPIN_TAB`, portaled to `document.body` against drawer overflow). Unpinning the selected tab selects
the next pinned tab, as the drawer does (`:142–152`). `data-testid="conversation-app-panel-menu-open-<tab id>"` and
`…-menu-pin-<tab id>`.

**Tab state** comes from `useConversationAppPanelTabs(conversationId, panel)` (Appendix A.5), the single owner of
the new blob key:

- `ConversationState` (`conversation-local-storage.ts:37–60`) gains
  `appPanelTabs?: Record<ConversationAppPanelKey, ConversationAppPanelTabState>`, each
  `{selectedTab: string | null; unpinnedTabs: string[]}`. `sanitizeStoredState` drops an `appPanelTabs` that is not
  a plain object, any entry that is not an object, a non-string `selectedTab` (to `null`) and non-string items of
  `unpinnedTabs`. Ids no longer registered are kept in storage (the App may come back) and ignored when read.
  `useConversationLocalStorageState` gains the optional setter `setAppPanelTabState(key, state)`.
- **Visible tabs:** pinned tabs, plus the selected tab when it is unpinned (the drawer's rule,
  `conversation-tabs.tsx:157–163`).
- **Selected tab:** the stored one if it is registered; otherwise the first pinned registered tab; otherwise the
  first registered tab. The fallback is read-time only; nothing is written until the user picks (`CX-003`).
- On a task placeholder or empty id, the hook falls back to in-memory state, as the blob hook already does
  (`:402–410`).

**The body** is `ConversationAppPanelTabContent` (Appendix A.6), which mounts the selected tab's page (§7.3) in a
`div` with `className="h-full min-h-0 overflow-auto"` and `data-testid="conversation-app-panel-content"`. ~~While the
App is still activating it shows `LoadingSpinner`; when the tab's mount throws or rejects, or the App's activation
failed, it shows the route page's unavailable state (`SETUP$UNAVAILABLE_TITLE` with the error, as
`canvas-extension-page.tsx:85–99`).~~ *(v2, §3.2 B7, replacing the struck sentence:)* An App that is activating or
failed has no registered panel, so the column stays closed (§4.2). When the tab's `mount` throws or rejects, the body
shows the route page's unavailable state (`SETUP$UNAVAILABLE_TITLE` with the error), from a new component,
`ConversationAppPanelUnavailable`, and keeps the emptied container mounted, hidden, so another tab can mount into it.
The container also carries `data-tab-id`.

### 4.5 Narrow windows

- `src/routes.ts` gains
  `route("conversations/:conversationId/panel/:extensionName/:panelId", "routes/conversation-app-panel.tsx")`;
  the new module re-exports `routes/conversation.tsx` exactly as `routes/conversation-panel.tsx` does, so React
  Router sees distinct route ids.
- `AppContent` (`routes/conversation.tsx:37, 219–225`) adds
  `useMatch("/conversations/:conversationId/panel/:extensionName/:panelId")` and renders
  `ConversationAppPanelMobilePage` for it, beside the drawer's `ConversationMobilePanelPage`.
- `ConversationAppPanelMobilePage` mirrors the drawer's page (`conversation-mobile-panel-page.tsx`): a 40 px top
  bar with the back button (`COMMON$BACK`, navigates to `/conversations/:id`) and the panel's tab row
  (`variant="compact"`), then the tab body filling the page. It does not touch `isRightPanelShown`. When the panel
  is not registered (yet, or any more) it shows the spinner while the runtime activates and the unavailable state
  after. *(v2: the back button is passed to `ConversationAppPanel` as `leading`, so it sits in the tab row's own
  40 px bar, §3.2 B8; clicking the selected tab there clears `activeAppPanel` and leaves the page, §3.2 B9. Test ids:
  `conversation-app-panel-page` and `conversation-app-panel-page-back`.)*
- Resizing across the breakpoint behaves as the drawer does: the desktop column disappears below 1024 px (the
  store still says open) and comes back above it; the page route is only entered by a click.

### 4.6 The Apps page

`CanvasExtensionCard` (`canvas-extension-card.tsx`) adds, beside its pages pill and list (`:71–111`), a
`SETTINGS$APPS_PANELS` pill with the panel count and one pill per panel title; and, under the description, the
runtime's notice or activation error for the App (`useCanvasExtensionsRuntime().notices` / `.errors`), so the
"panels unsupported" notice of §4.1 is visible where the user manages the App.

### 4.7 Files

New: `conversation-app-panel-toggle.tsx`; `conversation-app-panel/{conversation-app-panel.tsx,
conversation-app-panel-tabs-menu.tsx, conversation-app-panel-tab-content.tsx}`;
`conversation-main/conversation-app-panel-mobile-page.tsx`; `routes/conversation-app-panel.tsx`;
`hooks/use-conversation-app-panel-tabs.ts`; `hooks/query/use-canvas-extension-panel-icon.ts`;
`canvas-extensions/use-canvas-extension-mount.ts`; `utils/conversation-app-panel-path.ts`;
`fixtures/canvas-extensions/demo-panel/{canvas-extension.json, extension.js, README.md}`.
Changed: `types/canvas-extension.ts`, `lib/index.ts`, `canvas-extensions-runtime.tsx`, `routes/canvas-extension-page.tsx`,
`canvas-extension-card.tsx`, `api/canvas-extensions-service.ts`, `api/agent-server-compatibility.ts` (the capability
helper, §5.1, shared with PR 2), `hooks/query/query-keys.ts`, `stores/conversation-store.ts`,
`utils/conversation-local-storage.ts`, `conversation-name-with-status.tsx` (one line), `conversation-main.tsx`,
`conversation-tab-nav.tsx`, `routes.ts`, `routes/conversation.tsx`, `i18n/translation.json`,
`specs/canvas-extensions.md`, `tests/e2e/mock-llm/test-mapping.json`, `.agents/skills/e2e-testing/references/guide.md`.
*(v2, as built: also new, `conversation-app-panel/conversation-app-panel-unavailable.tsx` (B7) and
`demo-panel/icon.svg` (B6); also changed, `utils/convert-image-to-base-64.ts` (it takes a `Blob`, B8); not changed,
`mocks/canvas-extensions-handlers.ts` (B6). Tests: §4.9.)*

### 4.8 The demo-panel fixture

`src/fixtures/canvas-extensions/demo-panel` is a dependency-free App like upstream's `demo-page`, used by the unit
tests, the end-to-end spec and MSW mock mode (`canvas-extensions-handlers.ts` serves it beside `demo-page`)
*(v2, §3.2 B6: not in mock mode; the manifest as built also names `"icon": "icon.svg"`)*:

```json
{"schema_version": 1, "name": "demo-panel", "display_name": "Demo panel", "version": "0.1.0",
 "description": "A dependency-free fixture for Canvas conversation panels.", "entrypoint": "extension.js",
 "contributes": {"conversation_panels": [{"id": "demo", "title": "Demo panel",
   "tabs": [{"id": "overview", "title": "Overview", "path": "/"},
            {"id": "details", "title": "Details", "path": "/details"}]}]}}
```

`extension.js` registers both tabs with one mount that writes
`conversation=<conversationId> path=<path> tab=<surface.tabId>` into the container, increments a global mount
counter on mount and a dispose counter on dispose (`window.__demoPanelMounts`), so tests read the lifecycle from the
DOM. `demo-page` is left untouched, so upstream's existing Apps end-to-end spec is unaffected. *(v2, §3.2 B6: the text
is in an element with `data-testid="demo-panel-context"`, beside a button, `demo-panel-select-details`, that calls
`surface.selectTab("details")`.)*

### 4.9 Tests for PR 1

Upstream's layout and rules: vitest beside upstream's tests, the underlying service mocked rather than the hook,
the Zustand store seeded directly (upstream's note in `frontend-api-contracts`), Playwright under
`tests/e2e/mock-llm/`. Each test is named for the property it pins; `@spec` tags as listed.

`specs/canvas-extensions.md` gains, under "Package contract", the `conversation_panels` key and the mount
context's `conversationId` and `surface`; marks Slice 4's "extension tabs/panels" delivered; and adds the invariants
the code and tests are tagged with:

- **CX-001:** An App panel never shares the right side with the drawer or the overview.
- **CX-002:** A panel tab is mounted for the conversation it is shown in; changing the conversation remounts it.
- **CX-003:** A panel's selected tab and pins are kept per conversation; whether a panel is open is session-only.
- **CX-004:** A registration the manifest does not declare is refused; on an agent-server without conversation
  panels the refusal does not fail the App.
- *(v2, §3.2 B15)* **CX-006:** The panels' `data-testid`s are a contract for end-to-end tests: the button, the panel,
  a tab, the ⋯ menu's button and rows, the mounted container, the narrow page and its back button.

*(v2, §3.2 B17: the table below is v1's plan. As built, every file exists, the narrow page's tests are in the
sibling `conversation-app-panel-mobile-page.test.tsx`, and these are added: `canvas-extension-card.test.tsx` (the
card's panels pill and notice), `__tests__/api/agent-server-compatibility-bundled-pin.test.ts` (the capability
helper), `src/api/canvas-extensions-service.test.ts` (the icon fetch and the 60 s timeout) and the helper
`__tests__/helpers/canvas-extension-panels.tsx`. The tests, by name and property, are in the Gate B section's PR 1
table.)*

| File | Each test pins |
|---|---|
| `__tests__/stores/conversation-store.test.ts` (additions) | `CX-001`: a table of action sequences (open panel → open drawer, open drawer → open panel, overview ↔ panel, panel A → panel B, `setIsRightPanelShown(false)` with a panel open) never leaves an App panel open beside the drawer or the overview, after any step; `openAppPanel` clears `hasRightPanelToggled` |
| `src/components/features/canvas-extensions/canvas-extensions-runtime.test.tsx` (additions) | a declared tab registers and its panel appears with tabs in manifest order; a panel with no registered tab is absent; a panel id or an undeclared id throws on a server with `canvas_conversation_panels_v1`; on a server without it the tab registration is refused, the App's pages still register and its notice is set (`CX-004`); disabling the App removes its panels; a manifest whose panels change re-activates the App |
| `__tests__/conversation-local-storage.test.ts` (additions) | `appPanelTabs` round-trips; each malformed shape is sanitized as §4.4 says; entries for ids no longer registered survive a write |
| `__tests__/hooks/use-conversation-app-panel-tabs.test.ts` (new) | selection falls back to the first pinned tab when the stored one is gone, without writing; unpinning the selected tab selects the next pinned one; state is per conversation and per panel (`CX-003`) |
| `__tests__/components/features/conversation/conversation-app-panel-toggle.test.tsx` (new) | no button on a Cloud backend or without a registered panel; buttons follow Show panel in panel order; tooltip and `aria-pressed` follow the open state; a narrow window navigates to the panel page; a missing icon draws the default glyph |
| `__tests__/components/features/conversation/conversation-app-panel.test.tsx` (new) | the selected tab mounts with the conversation's id, its path and `surface`; switching tabs disposes the old mount first; a new `conversationId` disposes and remounts (`CX-002`); clicking the selected tab closes the panel; the ⋯ menu opens and pins tabs; a mount that rejects shows the unavailable state; `surface.selectTab` switches tabs |
| `__tests__/components/features/conversation/conversation-main.test.tsx` (additions) | with a panel open the column is open, the drawer's content is still in the DOM but hidden, and the App's content is shown; a key with no registered panel leaves the column closed |
| `__tests__/components/features/conversation/conversation-mobile-panel-page.test.tsx` (additions, or a sibling file for the App page) | the App panel page renders the panel's tabs and body for the route's App and panel; back returns to the conversation |
| `__tests__/components/features/conversation/conversation-tabs.test.tsx` | unchanged and green (the optional icon keeps every existing render) |
| `tests/e2e/mock-llm/canvas-extensions/mock-llm-canvas-extension-panels.spec.ts` (new) | against the real stack with our agent-server: install `demo-panel` by absolute path, enable it, create a conversation; the App's button is the last of the top-right group; it opens the panel showing `conversation=<id>`; Show panel closes it and opening it closes the drawer and the overview; ⋯ unpins Details, which survives a reload; switching conversation with the panel open shows the other id; at 800 px wide the button opens the panel page; disabling the App removes the button and closes the panel |

`npm run test:mutation:diff` (Stryker on the diff, the spec's layer 3) runs on the PR; survivors are listed in the
as-built. *(v2, §3.2 B18: not run.)*

---

## 5 · PR 2: agent commands and the option picker

### 5.1 The gate

`src/api/agent-server-compatibility.ts` gains `localAgentServerHasCapability(capability)` (true only for a local
active backend whose cached `/server_info` lists the string) and `getSdkHttpErrorDetail(error)` (the `detail` string
of an SDK `HttpError`'s parsed body, else `null`). *(v2, §3.2 B2: `getSdkHttpErrorDetail` is `null` for any status of
500 or above, whose `detail` is always "Internal Server Error"; a third helper, `getSdkHttpServerErrorReason(error)`,
returns a 5xx's `exception`, where the agent-server puts the reason.)* Agent controls exist when the backend is
local, the agent-server has `acp_session_controls_v1`, and the context is ACP: on the home screen `useAcpModelContext().isHomeAcp`
(`use-acp-model-context.ts:43–48`), in a conversation `conversation.agent_kind === "acp"`. Otherwise every surface
receives `NO_AGENT_CONTROLS` and renders exactly as today.

### 5.2 The event and the service

- **Types.** The event type comes from the client, as upstream's review guide requires ("Canvas consumes the
  published client type"): `src/types/agent-server/core/events/acp-session-controls-event.ts` re-exports
  `ACPSessionControlsEvent` from `@openhands/typescript-client` (the pattern of
  `conversation-state-event.ts:3–5`), joins Canvas's `OpenHandsEvent` union (`openhands-event.ts`), and
  `type-guards.ts` gains `isACPSessionControlsEvent`. `shouldRenderEvent` already returns `false` for it (no branch
  matches), so it never renders; transcript export skips it the same way (a test pins both).
- **`EventService.searchEvents`** (`event-service.api.ts:75–153`) gains `kind` in `EventSearchOptions`, passed to
  `RemoteEventsList.search` (which already accepts it) and, on Cloud, as a query parameter.
- **`AgentServerConversationService`** (`agent-server-conversation-service.api.ts`):
  - The local half of `createConversation` (`:518–558`: settings and profiles, the title profile, the workspace,
    `buildStartConversationRequestWithEncryptedSettings`) moves unchanged into
    `buildLocalStartConversationRequest(options)`, which returns the body, the new id and the resolved workspace
    mode. `createConversation` calls it, adds `acp_config_options` when the new `acpConfigOptions` option is
    non-empty (an empty map adds nothing, so the default body stays byte-identical, which upstream's payload
    snapshots assert), then `user_id` as today.
  - `previewAcpSession(options)` calls the same builder (no `query`), adds `acp_config_options`, and posts the body
    to `ConversationClient.previewAcpSession` with `ACP_PREVIEW_TIMEOUT_MS` (120 000: the agent-server's 90 s start-up
    bound plus its 2 s commands wait, with margin). Local only; Cloud throws.
  - `setAcpConfigOption(conversationId, configId, value)` mirrors `switchAcpModel` (`:1153–1172`) on the local path
    through `ConversationClient.setAcpConfigOption`; Cloud throws.
- **The launch agent.** For an ACP agent, `useCreateConversation`'s resolution
  (`use-create-conversation.ts:113–259`) reduces to "the active agent profile's id, else `agent_settings`": both
  fallbacks to `agent_settings` there are scoped to OpenHands profiles. The preview uses exactly that reduction
  (`resolveAcpLaunchProfile`, Appendix A.9), and a unit test asserts that the preview body equals the start body
  (less `initial_message` and `user_id`) for the same inputs, for a profile launch and an `agent_settings` launch.
- **The error code.** `acp-error-codes.ts` maps `ACPConfigOptionRejected` (S2's code when a start-time value is
  refused) to `ERROR$ACP_CONFIG_OPTION_REJECTED_TITLE`; the banner's detail is the agent's sentence.

### 5.3 In a conversation

`useConversationAgentControls(conversationId)` (Appendix A.10), called by `InteractiveChatBox`:

- **Current controls** = the newer of `useLatestAcpSessionControls(conversationId)`'s two sources (decision H):
  the event store's newest `ACPSessionControlsEvent` (a selector scanning `events` from the end) and a query
  (`ACP_SESSION_CONTROLS_QUERY_KEYS.latest(backendId, conversationId)`, `staleTime: Infinity`) of
  `EventService.searchEvents(id, null, null, {kind: ACP_SESSION_CONTROLS_EVENT_KIND, sortOrder: "TIMESTAMP_DESC", limit: 1})`
  whose first matching item is kept. Newer is by ISO timestamp, the event store's own ordering
  (`use-event-store.ts:28–40`). No event at all means no commands and no picker (S2 §7 item 4). *(v2, §3.2 B1: the
  search's `kind` is the module-qualified one the agent-server's search matches,
  `openhands.sdk.event.acp_session_controls.ACPSessionControlsEvent`, the client's `ACP_SESSION_CONTROLS_EVENT_KIND`;
  v1 wrote `"ACPSessionControlsEvent"`, the event's own `kind`. The event store's newest event counts only while the
  store holds this conversation, and the search is not retried. §3.2 B4: the first event after a start may list no
  commands, with the agent's menu in a later one; the newest is the state.)*
- **Options shown** = `config_options` without `id === "model"` (S2 §7 item 6; the model picker owns it) and without
  `type === "boolean"` (§3.1 item 10).
- **Setting** uses `useSetAcpConfigOption` (`meta: {disableToast: true}`): while pending, the pill shows the chosen
  value with a spinner and is disabled; on success nothing else is done (the agent-server publishes the next event,
  which replaces the controls); on failure, `displayErrorToast(getSdkHttpErrorDetail(error) ?? message)`, so a 422
  shows the agent's own sentence. *(v2, §3.2 B3: with B2, any other failure toasts the client's raw error text, for a
  5xx `HTTP request failed (504 Gateway Timeout): {"detail": …, "exception": …}`; what it should say is Michael's
  ruling 3.)* `applied: false` cannot arise from this UI (no picker exists before the session's
  first controls event).

### 5.4 On the home screen

`useHomeAgentControls({workingDir, workspaceMode})` (Appendix A.10), called by `HomeChatLauncher` with its pending
workspace (`undefined` when none or when the backend isolates the workspace, as the start does at `:122`):

- **The launch agent's key** is `${backendId}:${orgId}:${profile id or "agent-settings"}`. The values the user picked
  live in `useHomeAgentOptionsStore` (new, session-only), stored with the key they were picked under; values under
  another key are ignored (derived, no effect), so a backend switch or another active agent starts from the agent's
  defaults.
- **The preview** is `useAcpSessionPreview(...)`: a query keyed by
  `ACP_SESSION_CONTROLS_QUERY_KEYS.preview(launchKey, workingDir, workspaceMode, values)` (*v2, §3.2 B10:* the mode
  only with a workspace, else `null`, as the start sends it), whose function calls
  `previewAcpSession` and returns `{controls, values}` (the values it was asked with). `staleTime: 0`,
  `refetchOnMount: true`, `refetchOnWindowFocus: false` (each preview starts the agent once, S2 §4.6), `retry: false`,
  `placeholderData: keepPreviousData`, `meta: {disableToast: true}`. Every input is a discrete user action (a click, a
  workspace choice), so the key itself is the debounce S2 asks for; no timer is needed. A return to the home screen
  refetches, so a decomposition saved in D3 shows in the next home menu.
- **Shown:** commands and options from the newest successful preview; a pill whose value the user just changed
  shows that value with a spinner until its preview settles.
- **Errors:** a 422 keeps the last successful preview's controls, shows the agent's sentence
  (`getSdkHttpErrorDetail`) under the picker row (`data-testid="agent-option-rejection"`), and the refused value is
  not sent. 400, 429, 502 and 504 show no agent commands and no picker; the user can still start (S2 §7 item 2).
  *(v2, §3.2 B5: so does 501, and any failure but a 422.)*
- **Start values** (`startValues`) = the values of the last successful preview, restricted to option ids it reported
  and, for a select, to values it listed (`ASC-002`). `HomeChatLauncher.handleSubmit` passes them as
  `acpConfigOptions` to `useCreateConversation`, whose new variable reaches `createConversation` (§5.2). Values stay
  in the store after a start, so several conversations in one namespace need one pick; they reset with the app.
- **When the agent refuses a start value anyway** (the agent changed between preview and start), S2 ends the start
  in `ERROR` with `ConversationErrorEvent.code = "ACPConfigOptionRejected"`; the existing error banner shows
  `ERROR$ACP_CONFIG_OPTION_REJECTED_TITLE` and the agent's sentence.

### 5.5 The slash menu

`useSlashCommand(chatInputRef, {agentCommands})` (`use-slash-command.ts`) gains the option; `CustomChatInput` passes
`agentControls.commands`.

- Each command becomes a `SlashCommandItem` through `toAgentSlashCommandItem`: `command: "/" + name`, a `skill`
  shim the way `BUILT_IN_COMMANDS` builds one (`{name, type: "agentskills", source: null, description, triggers}`),
  and the new optional `inputHint`.
- `slashItems` (`:57–82`) becomes built-ins, then agent commands, then skills, dropping any item whose `command`
  repeats an earlier one (decision L). Agent commands do not wait for skills to load.
- `SlashCommandMenuItem` (`slash-command-menu.tsx:86–127`) renders `‹inputHint›` at the end of the command line when
  present (`data-testid="slash-command-hint"`; the guillemets are a display glyph under the guide's single-line
  `eslint-disable` exception, or a CSS pseudo-element). *(v2: the guillemets are literal text in the JSX; upstream's
  lint passes with no disable comment and no warning on that line. Each row also carries
  `data-testid="slash-command-item"` and `data-command`, ASC-005, §3.2 B15.)*
- Selecting an item still inserts `"/<name> "` (`:213–266`); the message is sent as usual, and S2 passes its text
  through unchanged.
- The list is replaced whenever `agentCommands` changes, never merged, so an agent that clears its commands (dr-acp
  at its first prompt) disappears from the menu with the next event (`ASC-001`).

### 5.6 The picker row

`ChatInputAgentOptions` (new, `src/components/features/chat/components/chat-input-agent-options.tsx`) renders in
`ChatInputContainer` (`chat-input-container.tsx:82`) after `UploadedFiles` and before the input row, only when
`controls.options` is non-empty: a `flex flex-wrap gap-2` row with `aria-label={t(CHAT_INTERFACE$AGENT_OPTIONS)}`,
one pill per option, in the agent's order. *(v2, §3.2 B11: it renders when there are options or a refusal sentence,
which is its last line; it keeps only `select` options; choosing the current value sends nothing; the row is
`data-testid="agent-options"`, a pill carries `data-value` and, when fixed, `data-fixed="true"`, and an open menu is
`agent-option-<id>-menu`.)*

- **A select with two or more values** is a pill `"<name>: <value name>"` with `ComboboxCaretInline`
  (`chatInputPillButtonClassName`, as the model pill). It opens a `ContextMenu` (the model popover's shape,
  `chat-input-model.tsx:180–193`) listing `options` by `name`, grouped under a small header per distinct `group`, the
  current value checked, each value's `description` as its `title`. Choosing a value calls `controls.setOption`.
  `data-testid="agent-option-<id>"` and `agent-option-<id>-value-<value>`.
- **A select with one value is fixed** (how dr-acp says the namespace cannot change any more): the same pill without
  a caret, not focusable as a button, with the option's `description` (else `CHAT_INTERFACE$AGENT_OPTION_FIXED`)
  as its tooltip.
- The picker is disabled while the composer is disabled (conversation being created, no LLM configured).

### 5.7 Files

New: `types/agent-server/core/events/acp-session-controls-event.ts`; `stores/home-agent-options-store.ts`;
`hooks/query/use-acp-session-preview.ts`; `hooks/query/use-latest-acp-session-controls.ts`;
`hooks/mutation/use-set-acp-config-option.ts`; `hooks/chat/use-agent-controls.ts`;
`components/features/chat/components/chat-input-agent-options.tsx`; `specs/acp-session-controls.md`;
`tests/e2e/mock-llm/conversations/mock-llm-acp-session-controls.spec.ts`.
Changed: `types/agent-server/core/{openhands-event.ts, events/index.ts}`, `types/agent-server/type-guards.ts`,
`api/event-service/{event-service.api.ts, event-service.types.ts}`,
`api/conversation-service/agent-server-conversation-service.api.ts`, `hooks/mutation/use-create-conversation.ts`
(one variable passed through), `hooks/chat/use-slash-command.ts`, `components/features/chat/components/{slash-command-menu.tsx,
chat-input-container.tsx}`, `components/features/chat/{custom-chat-input.tsx, interactive-chat-box.tsx}`,
`components/features/home/home-chat-launcher.tsx`, `utils/acp-error-codes.ts`, `hooks/query/query-keys.ts`,
`i18n/translation.json`, `tests/e2e/mock-llm/scripts/mock-acp-server.py`, `tests/e2e/mock-llm/test-mapping.json`,
`.agents/skills/e2e-testing/references/guide.md`. And `package.json`/`package-lock.json` only through the wiring
commit (§9). *(v2: as built; the wiring arrived by the merge `c08ded0`, after PR 2's commits, §3.2 B16. Tests: §5.8.)*

### 5.8 Tests for PR 2

`specs/acp-session-controls.md` (new, upstream's format, `specs/backend-management.md`):

- **ASC-001:** The slash menu lists exactly the commands of the agent's newest report; a new report replaces the
  last.
- **ASC-002:** The option values a conversation starts with are values the home screen's preview accepted.
- **ASC-003:** The option picker never offers the model option; the model picker owns it.
- **ASC-004:** Agent commands and options appear only where the local agent-server advertises
  `acp_session_controls_v1`; elsewhere the composer is unchanged.
- *(v2, §3.2 B15)* **ASC-005:** The agent controls' `data-testid`s are a contract for end-to-end tests: the slash
  menu, an item (with `data-command`), a hint, the picker row, a pill (with `data-value` and `data-fixed`), a value,
  the refusal.

*(v2, §3.2 B17: the table below is v1's plan. As built, the event-service tests are in
`src/api/event-service/event-service.api.test.ts`; added is `__tests__/hooks/chat/use-agent-controls.test.tsx` (a
conversation's controls: the newest report, the empty first report, a live set, a refusal, a 5xx, the gate), and
`__tests__/api/agent-server-compatibility-bundled-pin.test.ts` gains the `detail` helper's tests. The tests, by name
and property, are in the Gate B section's PR 2 table.)*

| File | Each test pins |
|---|---|
| `__tests__/api/agent-server-conversation-service.test.ts` (additions) | `acp_config_options` reaches the start body when non-empty and is absent otherwise (body otherwise byte-identical); the preview body equals the start body less `initial_message` and `user_id`, for a profile launch and an `agent_settings` launch (`ASC-002`); `setAcpConfigOption` posts through the client; both throw on Cloud |
| `__tests__/api/event-service.test.ts` (additions) | `kind` reaches the local search and the Cloud query string |
| `__tests__/hooks/query/use-latest-acp-session-controls.test.tsx` (new) | a REST event older than a live event loses, a newer one wins; no event gives `null`; the query is not issued for a non-ACP conversation or without the capability |
| `__tests__/hooks/query/use-acp-session-preview.test.tsx` (new) | the query key changes with the values, workspace and launch agent; values picked under another launch key are not sent; a 422 keeps the last controls and surfaces the agent's sentence; `startValues` keeps only ids and values the last successful preview reported |
| `__tests__/hooks/chat/use-slash-command.test.ts` (additions) | agent commands appear between built-ins and skills; a command repeating a built-in or an earlier item is dropped; a new `agentCommands` list replaces the old one (`ASC-001`); selecting one inserts `"/<name> "` |
| `__tests__/components/features/chat/slash-command-menu.test.tsx` (additions) | the hint renders only for commands with input |
| `__tests__/components/features/chat/components/chat-input-agent-options.test.tsx` (new) | no row without options; the `model` option and booleans never render (`ASC-003`); a one-value select is fixed with its description as tooltip; choosing a value calls `setOption`; groups render as headers |
| `__tests__/components/features/home/home-chat-launcher.test.tsx` (additions) | the start carries the accepted values; with the capability absent, no preview is requested and the start body is unchanged |
| `__tests__/components/features/chat/error-message-banner…` (additions where the banner is tested) | `ACPConfigOptionRejected` shows its header and the agent's sentence |
| `tests/e2e/mock-llm/conversations/mock-llm-acp-session-controls.spec.ts` (new) | with the mock ACP agent in controls mode (Appendix C) as the active agent: the home row shows `Profile: fast` and `/` lists `/summarize`; choosing `thorough` lists `/summarize` and `/compare ‹what to compare›`; sending `/compare a b` opens the conversation whose reply contains `profile=thorough` (the value reached the agent before its first prompt); there the pill is fixed at `thorough` and `/` lists no agent command; after a reload the same (the REST path) |

`npm run test:mutation:diff` runs on this PR too. *(v2, §3.2 B18: not run.)*

---

## 6 · PR 3: App backend frames

*(v2: proposed in v1; approved by Michael on 2026-10-03 as a scope addition to C2, the spec's "Scope additions
approved, 2026-10-03" (1).)*

### 6.1 Why a page cannot reach its backend today

Read in the SDK fork at `91430aa`:

- The bridge's HTTP and WebSocket routes (`canvas_extensions_bridge_router.py:80–105`) first require the request's own
  origin to be the configured ingress origin, `app_backend_public_url` (`bridge.py:296–301`, 421 otherwise; 503
  "Canvas App backend ingress is not configured" when unset, `:231–244`).
- A request is authorized only by the `oh_app_backend_session` cookie, minted by `POST
  /app-backends/{name}/session` on the ingress origin with `X-Session-API-Key` and the Canvas page's `Origin`, which
  must differ from the ingress origin (`:304–315`, `:416–434`). The cookie is `Secure; SameSite=None; Partitioned`,
  pathed to `/app-backends/{name}`, and lives five minutes (`APP_BACKEND_SESSION_TTL_SECONDS`, `:32–33`); a bridged
  WebSocket is cut when its session expires (`:193–214`).
- Any method other than GET, HEAD and OPTIONS must come *from* the ingress origin (`:454–455`, `:317–319`): a page running in
  Canvas cannot POST or PUT to its backend even with a cookie.
- `/server_info` reports the origin as `app_backend_ingress_url` and adds `canvas_app_backend_bridge_v1`
  (`server_details_router.py:127–152`); the TypeScript client already has `CanvasExtensionsClient.createAppBackendSession`
  and `revokeAppBackendSession`, whose docstring speaks of "the live frame" (`canvas-extensions-client.ts:103–131`).
- No launcher in the Canvas fork sets `app_backend_public_url` (no `OH_APP_BACKEND_PUBLIC_URL` anywhere in
  `scripts/`, `electron/` or `docker/`). *(v2: now every npm and desktop launcher does, `http://127.0.0.1:<agent-server
  port>` unless the environment names one: C3's `49db305`, approved on 2026-10-03 and merged into this branch with
  `wiring/dr-1`.)*

So the bridge's model is: Canvas, holding the session key, mints a session; the App's backend serves its own UI on
the ingress origin; that UI runs in a sandboxed frame and talks to its backend same-origin. An App page in Canvas
has neither the key nor the origin. PR 3 is the host half of that model, generic to any App with a backend.

### 6.2 The host API

`CanvasExtensionHost` gains `appBackend: {mountFrame(container, options)}` (Appendix A.11). `mountFrame`:

1. Resolves the target from the App's owning backend (local only) and the cached `/server_info` of that host. No
   `canvas_app_backend_bridge_v1` or no `app_backend_ingress_url` → reason `no-ingress`.
2. Acquires a session lease for `(backend id, App name)` from the session keeper (§6.3).
3. Appends an `<iframe>` filling the container (`width: 100%; height: 100%; border: 0`), with
   `src = lease.url + path` (path stripped of its leading `/`; may carry a query string), `sandbox` = the server's
   `iframe_sandbox` (`allow-forms allow-modals allow-popups allow-same-origin allow-scripts`), `title` = the
   option's title, and `referrerpolicy="no-referrer"`.
4. On failure, writes a short localized notice into the container (Appendix B) and calls `options.onError` once with
   `{reason, message}`: ~~`not-ready` for a 503 whose detail says the backend is not ready, `session-refused` for
   401, 403, 409 and 421, `unsupported-backend` on Cloud.~~ *(v2, §3.2 B2 and B13, replacing the struck words:)*
   `unsupported-backend` for a backend that is not local, shown with the no-ingress sentence; `not-ready` for a 503
   whose reason, under the body's `exception` (its `detail` is always "Internal Server Error"), says the backend is
   not ready; `no-ingress` also for a 503 whose reason names the ingress; `session-refused` for every other failure.
   The notice is a `<p role="status">` put before anything else in the container.
5. Returns a synchronous disposer: aborts a pending acquisition, removes the frame or notice, releases the lease.

### 6.3 The session keeper

`src/extensions/app-backend-session-keeper.ts` keeps one session per `(backend id, App name)`:

- The first lease creates the session (`CanvasExtensionsService.createAppBackendSession`, through
  `CanvasExtensionsClient` with `appBackendIngressUrl`, `credentials: "include"`) and schedules a refresh at
  `expires_at − 60 s` (never sooner than 10 s from now). A refresh mints a new session, whose cookie replaces the
  old one for every frame of that App; frames keep running. A failed refresh reports `session-refused` to the
  App's live frames (each shows its notice). *(v2, §3.2 B13: it reports the reason its error maps to by §6.2 step
  4's rule, and each frame stays in its container, its notice before it, until disposed. A session whose minting
  failed is forgotten, so the App's next frame tries again.)*
- Later leases share the live session. Releasing the last lease clears the timer and revokes the session
  (best-effort). A lease is never revoked while another frame of the same App is mounted: the cookie is per App,
  so revoking one frame's session would cut its siblings (decision N).
- A backend switch or App disable disposes every page, which releases every lease.

### 6.4 Tests for PR 3

`specs/canvas-extensions.md` adds **CX-005:** An App's backend session is revoked only when that App's last frame
closes.

| File | Each test pins |
|---|---|
| `src/extensions/app-backend-session-keeper.test.ts` (new; fake timers, the client faked at its HTTP boundary) | two leases share one session; the refresh fires before expiry; the last release revokes and the first does not; a failed refresh reaches every live lease |
| `src/extensions/mount-app-backend-frame.test.ts` (new) | the frame's `src`, `sandbox` and `title`; each failure reason writes its notice and calls `onError` once; dispose during a pending acquisition leaves nothing behind |
| `canvas-extensions-runtime.test.tsx` (addition) | every host gets `appBackend.mountFrame` bound to its own App and backend |

The browser end-to-end path needs an App with a backend artifact and an ingress-configured stack; that is D3's and
D5's to run (§10).

*(v2, §3.2 B17: as built, both new files fake the client's `CanvasExtensionsClient` class, not its HTTP; the keeper's
tests also pin the refresh floor, that two Apps keep two sessions, and an acquisition abandoned before the session
exists; the frame's, five failure cases (§6.2 step 4), the frame kept through refreshes, and one session for two
frames. The tests, by name, are in the Gate B section's PR 3 table.)*

---

## 7 · The contract D3 builds against

Everything here is generic: any App gets it. D3's App is `dr-library`, its panel `decompositions`, its tabs
`browse`, `create`, `namespaces`, `tools` (the spec's manifest, which S2 validates).

### 7.1 Declaring and registering

- Manifest: `contributes.conversation_panels: [{id, title, icon?, tabs: [{id, title, path}]}]`, validated by the
  agent-server (S2 §5.1): ids kebab-case and unique across the App's pages, panels and tabs; a panel has at least
  one tab; a tab's `path` is `/` or an absolute kebab-case path, unique in its panel; `icon` a package-relative `.svg`
  or `.png`.
- In `activate(host)`: `host.registerPage(<tab id>, mount)` for each tab. Registering the panel's id, an undeclared
  id or the same id twice throws (and fails activation, as for pages); on an agent-server without
  `canvas_conversation_panels_v1` the registration is refused without throwing (§4.1).
- The button appears when the App is enabled and activated and at least one of the panel's tabs is registered, on
  a local backend whose agent-server serves panels. Its tooltip is "Show <title>", its icon the manifest's.

### 7.2 What a tab's page receives

```ts
host.registerPage("create", ({ container, path, navigate, conversationId, surface }) => {
  // container: an empty <div> owned by Canvas
  // path: the tab's path without its leading "/" ("" for "/"), here "create"
  // navigate(path): app navigation, as host.navigate (leaves the conversation for another route)
  // conversationId: the conversation the panel is shown for; never null in a panel
  // surface: { kind: "conversation-panel", panelId: "decompositions", tabId: "create", selectTab(tabId) }
  return () => { /* dispose */ };
});
```

- `surface.selectTab(tabId)` selects another tab of the same panel, as a click would (for example, Decompositions
  after a save in Create decomposition); an id the panel does not have is ignored with a console warning.
- The same mount on a routed page receives `conversationId: null` and `surface: {kind: "page"}`.
- `host.agentServer.request(...)` still reaches the agent-server's own API with the session key. With the
  conversation's id, a page can read that conversation; for example its newest `ACPSessionControlsEvent`
  (`GET /api/conversations/<id>/events/search?kind=ACPSessionControlsEvent&sort_order=TIMESTAMP_DESC&limit=1`)
  says which namespace the conversation runs in, which Create decomposition could offer as the default. *(v2, §3.2
  B1: the search matches the module-qualified kind, so the query is
  `kind=openhands.sdk.event.acp_session_controls.ACPSessionControlsEvent`, the client's
  `ACP_SESSION_CONTROLS_EVENT_KIND`; the event's own `kind` field is `ACPSessionControlsEvent`. In an event a `null`
  field is absent, S2's §3.2 B2.)*

### 7.3 Size and lifecycle

- **Size.** The container fills the panel body: on a wide window, the drawer's column (20–70 % of the conversation
  area, 50 % by default, resized live by the user's drag) less the 40 px tab row; on a narrow window, the page less
  its 40 px top bar. It is `overflow-auto`; a page that fills it handles its own scrolling. Watch it with a
  `ResizeObserver` if layout depends on width. It sits inside Canvas's `[data-agent-server-ui]` scope, so Canvas's
  `--oh-*` variables (colors, fonts) are available; styles an App injects are not isolated (Apps are trusted,
  same-realm code, `specs/canvas-extensions.md` decision 2).
- **Mounted** when its tab becomes visible: the panel opens with that tab selected, or the tab is selected in an
  open panel, or the narrow-window page is opened. The container is attached and empty when `mount` runs; `mount`
  may be async.
- **Disposed** (the returned function, best-effort) when: another tab is selected; the panel closes (its button,
  clicking its selected tab, Show panel, Show overview, another App's panel); the conversation changes (then it is
  mounted again with the new `conversationId`, `CX-002`); the window crosses the 1024 px breakpoint; the App is
  disabled, updated or re-activated; the backend switches; the user leaves the conversation route. The container is
  emptied after dispose.
- **Nothing persists across mounts** except what the page stores itself; Canvas keeps only which tab is selected
  and which are pinned, per conversation. Errors from `mount` show Canvas's unavailable state in the panel. *(v2,
  §3.2 B7: the emptied container stays in the panel, hidden, so selecting another tab mounts into it; the container
  carries `data-tab-id`.)*

### 7.4 Reaching its own backend (with PR 3)

- D3's interactive UI is served by its backend (D2's Library API serving its own static UI) and shown with
  `host.appBackend.mountFrame(container, { path: "/ui/create?conversation=" + encodeURIComponent(conversationId),
  title: "Create decomposition" })`, returning the frame's disposer from `mount`.
- Inside the frame, the UI talks to its backend same-origin, with any method, using **relative** URLs (it is served
  under `/app-backends/dr-library/`); the cookie is sent automatically and refreshed by Canvas. A WebSocket opened by
  the frame is cut when its session expires, at most five minutes after it opened: reconnect, or use HTTP.
- The frame has no session key and cannot call the agent-server's own API; anything it needs from there, the page
  passes in the frame's URL.
- The backend must be running: D5's setup prepares and starts it (`/api/canvas-extensions/installed/{name}/backend/…`),
  or the page does so through `host.agentServer.request`. `mountFrame` reports `not-ready` otherwise.
- The agent-server must be configured with an App ingress origin (`OH_APP_BACKEND_PUBLIC_URL`), which no launcher
  sets today (§11 item 1). Without it `mountFrame` reports `no-ingress`. *(v2: every npm and desktop launcher now sets
  it to `http://127.0.0.1:<agent-server port>` unless the environment names one, C3's `49db305`; the desktop window
  is `http://localhost:8000`, so the frame's origin differs from Canvas's, as the bridge requires.)*
- *(v2, §3.2 B13)* `onError` is called once, and the frame, once shown, stays until the page disposes it: a refresh
  that fails adds the notice before the frame and reports its reason (`not-ready`, `no-ingress` or
  `session-refused`). Any failure the host cannot name is `session-refused`.
- **Without PR 3** there is no supported way for a D3 page to write to D2's API (§6.1); D3 should not be designed
  around the Library API until the Conductor has ruled. *(v2: PR 3 is approved and built.)*

---

## 8 · What C2 needs from S2

C2 builds on S2's §7 as written, with these points:

1. **Must change (small): export the controls types from the client's package root.** C2 imports
   `ACPAvailableCommand`, `ACPCommandInput`, `ACPConfigOption`, `ACPConfigOptionValue`, `ACPConfigOptionValues`,
   `ACPConfigOptionSetResponse`, `ACPSessionControls`, `ACPSessionControlsEvent` and `isACPSessionControlsEvent`
   from `@openhands/typescript-client`. S2's Appendix B puts them in `src/models/acp-session-controls.ts` and
   `src/events/types.ts`; its `src/index.ts` must re-export them (as it does `ACPModelOption` and
   `ConversationErrorEvent`), or Canvas would have to import from internal paths the package's `exports` map does not
   expose. *(v2: done in S2. The `dr-1` client exports them from its root, with `ACP_SESSION_CONTROLS_EVENT_KIND`, and
   C2 imports them from there, but for `isACPSessionControlsEvent`, which Canvas declares in its own
   `type-guards.ts`, as A.8 says.)*
2. **No change, a usage note:** C2 does not call `getAcpSessionControls`; it searches the newest event itself through
   Canvas's `EventService`, because it must compare that event's timestamp with live events (decision H). The client
   method can stay for other consumers. *(v2: the search uses the client's `ACP_SESSION_CONTROLS_EVENT_KIND`, §3.2
   B1.)*
3. **Optional, not for v1:** a preview for an existing conversation whose session has not started
   (`POST /api/conversations/{id}/acp/preview`), which would give conversations created without a first message a
   picker (§3.1 item 11).
4. **Relied on, already in S2:** the preview ignores start-request fields that do not reach `session/new`
   (`conversation_id`, `worktree`, `initial_message`); the set route's 422 `detail` is the agent's sentence; the icon
   route needs the session key; `conversation_panels` is omitted when empty.

---

## 9 · Where C2 touches other work

| Place | Who else | Rule |
|---|---|---|
| `types/agent-server/core/{openhands-event.ts, events/index.ts}`, `type-guards.ts` | C1 adds S1's two event kinds | adjacent union members, exports and guards; whoever lands second merges by hand |
| `tests/e2e/mock-llm/scripts/mock-acp-server.py` | C1 adds sub-agent behaviour (the spec's one generic fixture, mirrored in Canvas) | one script; each feature behind its own flag (Appendix C); defaults unchanged so upstream's ACP specs are unaffected |
| `tests/e2e/mock-llm/test-mapping.json`, `.agents/skills/e2e-testing/references/guide.md` | C1 | adjacent entries |
| `i18n/translation.json` | C1, C3 | adjacent keys |
| `package.json` / `package-lock.json` (`@openhands/typescript-client`) | the wiring commit (Q2 (a)) | PR 2 needs a client built from an SDK fork tag that carries S2 PR 1; PR 1 and PR 3 need no new client API (PR 1 uses `AgentServerClient.get`, PR 3 the existing `CanvasExtensionsClient`). For each PR's upstream-shaped draft branch on our fork's `main`, PR 2's first commit is the client bump (upstream's rule: release the client, then bump the pin). *(v2, §3.2 B16: on `feat/agent-surfaces` the pin, to the `dr-1` release tarball, arrived with the merge `c08ded0`, after PR 2's commits, which need it; the split must put it first.)* |
| `conversation-main.tsx`, `conversation-store.ts` | upstream (the spec's merge-conflict note) | small, local hunks |
| `chat-input-container.tsx`, `home-chat-launcher.tsx`, `custom-chat-input.tsx` | upstream `a8c8fb3` (voice dictation) touches `chat-input-container.tsx` and `chat-input-actions.tsx` | C2 adds one render line and one prop in the container and leaves the actions row alone (decision K), so the next upstream merge conflicts in at most one hunk |
| `scripts/`, `electron/`, `config/defaults.json` | C3 | C2 touches none of them *(v2: as built; they reach the branch only through the wiring merges)* |

**Order.** PR 1 can be built and unit-tested now; its end-to-end spec needs an agent-server with S2 PR 2 (through
the wiring commit's tag). PR 2 needs S2 PR 1 and its client. PR 3 needs nothing new from S2, but is useful only once
a launcher configures the ingress (§11 item 1). *(v2: all three are built on `feat/agent-surfaces`, on top of
`wiring/dr-1`, which carries the `dr-1` agent-server and client and C3's launcher with its default ingress.)*

---

## 10 · E11 and the testing layers

**E11 · Agent surfaces (S2, C2, D1)**, the parts C2 proves:

| E11 claim | Proven in C2 by | And elsewhere |
|---|---|---|
| On the home screen the preview lists the namespace's decompositions | the controls end-to-end spec (the mock agent's commands per value); `use-acp-session-preview.test.tsx` | S2's preview tests; D5's layer-4 flow with dr-acp |
| Changing the namespace changes them | the end-to-end spec (`fast` → `thorough` changes the menu) | D5 |
| The started run uses the chosen namespace | the end-to-end spec (the reply echoes `profile=thorough`); the start-body test | S2's request-log test; D1's run log |
| Commands are gone after the first message | the end-to-end spec; `use-slash-command` replacement test | D1 §5.2; S2 |
| The decompositions panel mounts with the right conversation | the panels end-to-end spec (conversation switch); `conversation-app-panel.test.tsx` (`CX-002`) | D3's own tests, against §7 |
| It never shares the right side with the drawer | the store's action-sequence test (`CX-001`); the panels end-to-end spec | — |

*(v2: as built, every row holds; the tests by name are in the Gate B section, where the seven end-to-end tests are
numbered. The first three rows are live test 6, the fourth live test 7, the fifth live tests 1, 3 and 4, the last
live test 1. E11's last claim, an App backend on macOS and Linux, is S2's PR 3 and D3's.)*

**The layers.** Layer 3 (inside the fork): §4.9, §5.8 and §6.4, in upstream's folders and style, plus upstream's
full vitest and Playwright suites green on `feat/agent-surfaces` and on `deep-reasoning` after merge, and `npm run
lint`, `npm test`, `npm run build` and `npm run build:lib` (upstream's verification commands) green. The mock-LLM
workflow does not run on pull requests (`.github/workflows/mock-llm-e2e.yml:3–6`); the Implementer runs it by
`workflow_dispatch` on the task branch, where the wiring commit makes it start our agent-server. Layer 4 (the real
desktop app with dr-acp, in deep-reasoning's CI) is D5's E12: it picks a namespace, opens Show decompositions and
uses the slash menu through C2. *(v2: CI's `npm run lint`, `npm test`, `npm run build` and `npm run build:lib` are
green at `64b5a8b`; upstream's full Playwright suite is not: six of its mock-LLM tests fail on this branch and on the
fork's base alike, none of them C2's (the Gate B section). Mutation testing did not run, §3.2 B18.)*

**The live tier (Gate B's evidence).** The spec's §4 layer 5 makes C2's evidence its end-to-end tests, "Playwright
written as tests that assert behaviour": the two specs above, green in the fork's mock-LLM run at the branch's head.
No real model is involved: the agent is the scripted mock ACP agent, and dr-acp's own behaviour behind these
surfaces is asserted by S2's live tier and D5's flow.

*(v2, §3.2 B19.)* As run: `mock-llm-e2e.yml` dispatched on `feat/agent-surfaces` at `64b5a8b` with the fork's `specs`
input naming the two specs, run 37153648974, 7 of 7. What is real in it: the agent-server, installed by C3's
launcher from the SDK fork at `cef3b24` (tag `dr-1`), the automation backend, the built frontend behind the ingress,
and Chromium; what is scripted: the model (openhands-sdk's `TestLLM` behind the mock LLM server) and the ACP agent
(Appendix C). This departs from the workspace's definition of a live tier, a real task against real services, and
is Michael's ruling 2 at Gate B (§3.1 item 14). The real-model end to end with dr-acp: S2's live tier through the
agent-server (deep-reasoning run 37147707860), D5's E12 through Canvas.

---

## 11 · Open items for the Conductor

1. **Not C2's to settle: the App ingress for the desktop app (D5, C3).** The App-backend bridge needs the agent-server
   started with `OH_APP_BACKEND_PUBLIC_URL` naming an origin distinct from Canvas's, which the browser can reach and
   which reaches the agent-server with its own `Host` intact (for example `http://localhost:<agent-server port>`
   while Canvas is served from `http://127.0.0.1:<port>`; the agent-server's CORS allows both loopback names with
   credentials, `middleware.py:34–60`). Whether a `Secure; Partitioned` cookie on `http://localhost` inside a frame
   under `127.0.0.1` behaves in Electron's Chromium is unverified here; D5's end-to-end flow settles it. Without this,
   D3's panel can show nothing from D2. *(v2: C3's `49db305`, approved on 2026-10-03, makes every launcher set it to
   `http://127.0.0.1:<agent-server port>` unless set, with the desktop window on `http://localhost:8000`: the
   reverse of the example above, with the same two loopback names. Whether the `Secure; Partitioned` cookie survives
   in Electron's Chromium inside a frame on the other name is still D5's to settle.)*
2. **Rule on PR 3** (§3.1 item 1, §6). Recommended: approve; it is the host half of the bridge upstream already ships.
   *(v2: approved by Michael on 2026-10-03, and built.)*
3. **Rule on the estimate** (§3.1 item 2). *(v2: replaced by the size ruling in the Gate B section, §3.2 B20.)*
4. **S2's item 1 in §8** (root exports) goes to S2's Implementer through you. *(v2: done; the `dr-1` client exports
   them.)*
5. **Unverified until the Implementer runs it:** that the drawer's terminal survives being hidden behind an App
   panel with `display: none` (decision C; a test asserts its node and session survive); that the guillemet glyph in
   the menu row passes upstream's lint (else a CSS pseudo-element, §5.5). *(v2: the guillemets pass lint as literal
   text. The terminal is still unverified: the test hides a stand-in for the drawer's content and asserts it is never
   unmounted (the drawer is hidden with the `hidden` attribute), so nothing exercises the real terminal's session
   behind an App panel, §3.2 B17.)*
6. *(v2)* **Rule for Michael at Gate B:** size (§3.2 B20), the live tier (§3.1 item 14) and what a failed live
   option set says (§3.2 B3).
7. *(v2)* **Mutation testing on the diff** (§3.2 B18): have it run on `9881d24..64b5a8b`, so the as-built can list
   the survivors, or waive it.
8. *(v2)* **The PR split** puts the client pin before PR 2's commits (§3.2 B16).

---

## Appendix A · Signature reference (TypeScript)

Valid TypeScript in declaration form, as a `.d.ts` would state it: `declare` marks a signature whose body the
sections above specify; `// …existing…` marks members that do not change; one field per line; paths relative to the
fork's root. Imports are shown where a name comes from outside the file; the fork's own names (`Backend`,
`WorkspaceMode`, `AgentKind`, `InstalledCanvasExtensionInfo`, …) are imported from where they live today.

*(v2: checked against the code at `64b5a8b`. A line the build changed or added carries a `// v2:` comment naming its
item in §3.2; everything else is as built.)*

### A.1 `src/types/canvas-extension.ts` (additions and changes; PR 1, PR 3)

```ts
export interface CanvasExtensionPanelTabContribution {
  /** Contribution id; the id the App registers this tab's page under. */
  id: string;
  /** Label in the panel's tab row. */
  title: string;
  /** "/" or an absolute kebab-case path; where the tab's page starts. */
  path: string;
}

export interface CanvasExtensionConversationPanelContribution {
  /** Contribution id of the panel. */
  id: string;
  /** Tooltip "Show <title>" and the panel's accessible name. */
  title: string;
  /** Package-relative .svg or .png for the header button. */
  icon?: string | null;
  /** The panel's tabs, in tab-row order; never empty. */
  tabs: CanvasExtensionPanelTabContribution[];
}

export interface CanvasExtensionContributions {
  pages?: CanvasExtensionPageContribution[] | null;
  conversation_panels?: CanvasExtensionConversationPanelContribution[] | null;
}

export interface CanvasExtensionPageSurface {
  kind: "page";
}

export interface CanvasExtensionConversationPanelSurface {
  kind: "conversation-panel";
  /** The panel's contribution id. */
  panelId: string;
  /** The tab's contribution id. */
  tabId: string;
  /** Select another tab of this panel, as a click on it would. */
  selectTab: (tabId: string) => void;
}

export type CanvasExtensionMountSurface =
  | CanvasExtensionPageSurface
  | CanvasExtensionConversationPanelSurface;

export interface CanvasExtensionPageMountContext {
  container: HTMLElement;
  /** Remainder of the route below the page's path, or the tab's path without its leading "/". */
  path: string;
  navigate: (path: string) => void;
  /** The conversation a panel is shown for; null on a routed page. */
  conversationId: string | null;
  /** Where the page is mounted. */
  surface: CanvasExtensionMountSurface;
}

// PR 3
export type CanvasExtensionAppBackendErrorReason =
  | "no-ingress"
  | "not-ready"
  | "session-refused"
  | "unsupported-backend";

export interface CanvasExtensionAppBackendError {
  reason: CanvasExtensionAppBackendErrorReason;
  /** Localized sentence, the one the host shows in the container. */
  message: string;
}

export interface CanvasExtensionAppBackendFrameOptions {
  /** Path on the App's backend below its ingress root; "/" by default; may carry a query string. */
  path?: string;
  /** Accessible name of the frame. */
  title: string;
  /** Called once if the frame cannot be shown. */
  onError?: (error: CanvasExtensionAppBackendError) => void;
}

export interface CanvasExtensionAppBackendHost {
  /**
   * Show the App's own backend in a sandboxed frame filling the container.
   * The frame is the `<iframe>` appended to the container, kept there (also
   * across session refreshes) until the returned disposer runs.
   */
  // v2: B13, the docstring's second sentence
  mountFrame: (
    container: HTMLElement,
    options: CanvasExtensionAppBackendFrameOptions,
  ) => CanvasExtensionDispose;
}

export interface CanvasExtensionHost {
  readonly apiVersion: typeof CANVAS_EXTENSION_HOST_API_VERSION;
  readonly extension: Readonly<{
    name: string;
    version: string;
    resolvedRef: string | null;
  }>;
  readonly backend: Readonly<{
    id: string;
    kind: "local" | "cloud";
    orgId: string | null;
  }>;
  registerPage: (
    contributionId: string,
    mount: CanvasExtensionPageMount,
  ) => CanvasExtensionDispose;
  navigate: (path: string) => void;
  /** Requests to the owning agent-server's API; each may take up to 60 s. */
  // v2: B8, the timeout documented
  agentServer: {
    request: <T = unknown>(
      request: CanvasExtensionAgentServerRequest,
    ) => Promise<T>;
  };
  /** PR 3. */
  readonly appBackend: CanvasExtensionAppBackendHost;
}
```

### A.2 `src/components/features/canvas-extensions/canvas-extensions-runtime.tsx` (additions; PR 1)

```ts
import type { ConversationAppPanelKey } from "#/stores/conversation-store";

export interface RegisteredCanvasExtensionPanelTab {
  extension: InstalledCanvasExtensionInfo;
  panel: CanvasExtensionConversationPanelContribution;
  /** The tab, its path without the leading "/" ("" for "/"). */
  // v2: B8
  contribution: CanvasExtensionPanelTabContribution;
  mount: CanvasExtensionPageMount;
}

export interface RegisteredCanvasExtensionPanel {
  key: ConversationAppPanelKey;
  extension: InstalledCanvasExtensionInfo;
  contribution: CanvasExtensionConversationPanelContribution;
  /** Registered tabs in manifest order; never empty. */
  tabs: RegisteredCanvasExtensionPanelTab[];
}

interface CanvasExtensionsRuntimeValue {
  pages: RegisteredCanvasExtensionPage[];
  panels: RegisteredCanvasExtensionPanel[];
  activating: boolean;
  errors: ReadonlyMap<string, string>;
  /** Per App: a condition that is not an activation failure, as an i18n key. */
  // v2: B8, the value is a key, translated by the Apps card
  notices: ReadonlyMap<string, string>;
}

type DeclaredContribution =
  | {
      kind: "page";
      contribution: CanvasExtensionPageContribution;
    }
  | {
      kind: "panel-tab";
      panel: CanvasExtensionConversationPanelContribution;
      tab: CanvasExtensionPanelTabContribution;
    }
  | {
      kind: "panels-unsupported";
    };

/** Throws for a panel id, a malformed declaration or an undeclared id on a server that serves panels. */
declare function resolveDeclaredContribution(
  extension: InstalledCanvasExtensionInfo,
  contributionId: string,
): DeclaredContribution;

/** The registered panel with this key, or null; reads the runtime. */
export declare function useRegisteredAppPanel(
  key: ConversationAppPanelKey | null,
): RegisteredCanvasExtensionPanel | null;
```

`src/components/features/canvas-extensions/use-canvas-extension-mount.ts` (new; PR 1):

```ts
export interface CanvasExtensionMountState {
  /** The mount's own error, if it threw or rejected. */
  error: string | null;
}

/**
 * Mount `mount` into the container while `mountKey` is unchanged; dispose and remount when it changes.
 * `context` is read through a ref, so only `mount` and `mountKey` decide remounting.
 */
export declare function useCanvasExtensionMount(
  containerRef: React.RefObject<HTMLDivElement | null>,
  mount: CanvasExtensionPageMount | null,
  context: Omit<CanvasExtensionPageMountContext, "container"> | null,
  mountKey: string,
): CanvasExtensionMountState;
```

`src/api/canvas-extensions-service.ts` (additions; PR 1, PR 3):

```ts
import type { CanvasExtensionsClient } from "@openhands/typescript-client/clients";

/** How long a request to an App's owning agent-server may take, `host.agentServer.request` included. */
// v2: B8, upstream's 60 s, named
export const CANVAS_EXTENSION_AGENT_SERVER_REQUEST_TIMEOUT_MS = 60_000;

// v2: B14, the client's own answer type
export type AppBackendSession = Awaited<
  ReturnType<CanvasExtensionsClient["createAppBackendSession"]>
>;

declare class CanvasExtensionsService {
  // …existing methods…

  /** GET …/installed/{name}/panels/{panelId}/icon with the session key (S2 PR 2). */
  static fetchPanelIcon(
    name: string,
    panelId: string,
    backend?: Backend,
  ): Promise<Blob>;

  /** PR 3: POST {ingress}/app-backends/{name}/session, credentials included. */
  static createAppBackendSession(
    name: string,
    backend: Backend,
    ingressUrl: string,
    signal?: AbortSignal,
  ): Promise<AppBackendSession>; // v2: B14

  /** PR 3: DELETE {ingress}/app-backends/{name}/session; errors are swallowed and logged. */
  static revokeAppBackendSession(
    name: string,
    backend: Backend,
    ingressUrl: string,
  ): Promise<void>;
}
```

`src/hooks/query/use-canvas-extension-panel-icon.ts` (new; PR 1):

```ts
/** A data: URL for the panel's icon, or null (no icon, loading, or any failure). */
export declare function useCanvasExtensionPanelIcon(
  panel: RegisteredCanvasExtensionPanel,
): string | null;
```

`src/hooks/query/query-keys.ts` (additions):

```ts
export const CANVAS_EXTENSIONS_QUERY_KEYS = {
  // …existing keys…
  panelIcon: (
    backendId: string,
    orgId: string | null,
    extensionName: string,
    resolvedRef: string | null,
    panelId: string,
  ) =>
    [
      "canvas-extensions",
      "panel-icon",
      backendId,
      orgId,
      extensionName,
      resolvedRef,
      panelId,
    ] as const,
} as const;

// PR 2
export const ACP_SESSION_CONTROLS_QUERY_KEYS = {
  all: ["acp-session-controls"] as const,
  latest: (backendId: string, conversationId: string) =>
    ["acp-session-controls", "latest", backendId, conversationId] as const,
  preview: (
    launchKey: string,
    workingDir: string | null,
    workspaceMode: WorkspaceMode | null, // v2: B10, null without a workspace
    values: ACPConfigOptionValues,
  ) =>
    [
      "acp-session-controls",
      "preview",
      launchKey,
      workingDir,
      workspaceMode,
      values,
    ] as const,
} as const;
```

### A.3 `src/stores/conversation-store.ts` (additions and changes; PR 1)

```ts
/** `${extensionName}/${panelId}`; both are kebab-case, so "/" cannot occur inside either. */
export type ConversationAppPanelKey = `${string}/${string}`;

export declare function toConversationAppPanelKey(
  extensionName: string,
  panelId: string,
): ConversationAppPanelKey;

interface ConversationState {
  // …existing fields…
  /** The open App header panel; session-only, like the drawer. */
  activeAppPanel: ConversationAppPanelKey | null;
}

interface ConversationActions {
  // …existing actions…
  /** Open an App panel; closes the drawer and the overview in the same update. */
  openAppPanel: (key: ConversationAppPanelKey) => void;
  closeAppPanel: () => void;
}

// Changed bodies (the only two):
//   setIsRightPanelShown: (isRightPanelShown) =>
//     set(
//       isRightPanelShown
//         ? { isRightPanelShown, activeAppPanel: null }
//         : { isRightPanelShown },
//       false,
//       "setIsRightPanelShown",
//     ),
//   setIsOverviewPanelShown: (isOverviewPanelShown) =>
//     set(
//       isOverviewPanelShown
//         ? { isOverviewPanelShown, isOverviewPanelPeeked: false, activeAppPanel: null }
//         : { isOverviewPanelShown, isOverviewPanelPeeked: false },
//       false,
//       "setIsOverviewPanelShown",
//     ),
```

### A.4 `src/utils/conversation-local-storage.ts` (additions; PR 1)

```ts
export interface ConversationAppPanelTabState {
  /** The tab last selected in this panel, or null for the default. */
  selectedTab: string | null;
  /** Tab ids the user unpinned from the row. */
  unpinnedTabs: string[];
}

export interface ConversationState {
  // …existing fields…
  /** Per App panel: its selected tab and unpinned tabs in this conversation. */
  appPanelTabs?: Record<ConversationAppPanelKey, ConversationAppPanelTabState>;
}

// useConversationLocalStorageState's return gains:
//   setAppPanelTabState?: (
//     key: ConversationAppPanelKey,
//     state: ConversationAppPanelTabState,
//   ) => void;
```

`src/utils/conversation-app-panel-path.ts` (new; PR 1):

```ts
export const CONVERSATION_APP_PANEL_ROUTE =
  "/conversations/:conversationId/panel/:extensionName/:panelId";

export declare function buildConversationAppPanelPath(
  conversationId: string,
  extensionName: string,
  panelId: string,
): string;
```

### A.5 `src/hooks/use-conversation-app-panel-tabs.ts` (new; PR 1)

```ts
export interface ConversationAppPanelTabView {
  id: string;
  title: string;
  pinned: boolean;
}

export interface ConversationAppPanelTabsState {
  /** Every registered tab, in manifest order. */
  tabs: ConversationAppPanelTabView[];
  /** Pinned tabs, plus the selected tab when it is unpinned. */
  visibleTabs: ConversationAppPanelTabView[];
  /** Resolved at read time; always a registered tab. */
  selectedTabId: string;
  selectTab: (tabId: string) => void;
  /** Unpinning the selected tab selects the next pinned tab. */
  togglePin: (tabId: string) => void;
}

export declare function useConversationAppPanelTabs(
  conversationId: string,
  panel: RegisteredCanvasExtensionPanel,
): ConversationAppPanelTabsState;
```

### A.6 Components (new; PR 1)

```ts
// src/components/features/conversation/conversation-app-panel-toggle.tsx
export declare function ConversationAppPanelToggles(): React.ReactElement | null;

export interface ConversationAppPanelToggleProps {
  panel: RegisteredCanvasExtensionPanel;
}

export declare function ConversationAppPanelToggle(
  props: ConversationAppPanelToggleProps,
): React.ReactElement;

// src/components/features/conversation/conversation-app-panel/conversation-app-panel.tsx
export interface ConversationAppPanelProps {
  conversationId: string;
  panel: RegisteredCanvasExtensionPanel;
  /** "compact" in the narrow-window page's top bar. */
  variant?: "default" | "compact";
  /** Rendered before the tab row, e.g. the narrow-window page's back button. */
  leading?: React.ReactNode; // v2: B8
}

export declare function ConversationAppPanel(
  props: ConversationAppPanelProps,
): React.ReactElement;

// src/components/features/conversation/conversation-app-panel/conversation-app-panel-tabs-menu.tsx
export interface ConversationAppPanelTabsMenuProps {
  isOpen: boolean;
  onClose: () => void;
  anchorRef: React.RefObject<HTMLElement | null>;
  tabs: ConversationAppPanelTabsState;
}

export declare function ConversationAppPanelTabsMenu(
  props: ConversationAppPanelTabsMenuProps,
): React.ReactElement | null;

// src/components/features/conversation/conversation-app-panel/conversation-app-panel-tab-content.tsx
export interface ConversationAppPanelTabContentProps {
  conversationId: string;
  panel: RegisteredCanvasExtensionPanel;
  tab: RegisteredCanvasExtensionPanelTab;
  selectTab: (tabId: string) => void;
}

export declare function ConversationAppPanelTabContent(
  props: ConversationAppPanelTabContentProps,
): React.ReactElement;

// src/components/features/conversation/conversation-app-panel/conversation-app-panel-unavailable.tsx (v2: B7)
/** The route page's unavailable state; a null error shows SETTINGS$APPS_PAGE_UNAVAILABLE. */
export declare function ConversationAppPanelUnavailable(props: {
  error: string | null;
}): React.ReactElement;

// src/components/features/conversation/conversation-main/conversation-app-panel-mobile-page.tsx
export interface ConversationAppPanelMobilePageProps {
  extensionName: string;
  panelId: string;
  onNavigateBack: () => void;
}

export declare function ConversationAppPanelMobilePage(
  props: ConversationAppPanelMobilePageProps,
): React.ReactElement;

// src/components/features/conversation/conversation-tabs/conversation-tab-nav.tsx (changed prop)
type ConversationTabNavProps = {
  tabValue: string;
  /** Without an icon, the label is always shown. */
  icon?: ComponentType<{ className: string }>;
  onClick(): void;
  isActive?: boolean;
  label?: string;
  className?: string;
  measureOnly?: boolean;
  suppressLayoutAnimation?: boolean;
  /** Overrides the default `conversation-tab-${tabValue}` test id. */
  testId?: string; // v2: B8
};
```

### A.7 `src/api/agent-server-compatibility.ts` (additions; PR 1 and PR 2, used by PR 3; v2: B2, B12)

```ts
export type AgentServerCapability =
  | "acp_session_controls_v1"
  | "canvas_conversation_panels_v1"
  | "canvas_app_backend_bridge_v1";

/** True only for a local active backend whose cached /server_info lists the capability. */
export declare function localAgentServerHasCapability(
  capability: AgentServerCapability,
): boolean;

/**
 * The agent-server's `detail` sentence from an SDK HttpError (for example an
 * ACP agent's own reason for refusing a config option value), or null. A 5xx
 * answer has none: its `detail` is always "Internal Server Error".
 */
// v2: B2, null for any status of 500 or above
export declare function getSdkHttpErrorDetail(error: unknown): string | null;

/**
 * Why the agent-server answered a 5xx, which its error handler moves under
 * `exception` (for example "503: Canvas App backend is not ready"), or null.
 */
// v2: B2, new
export declare function getSdkHttpServerErrorReason(
  error: unknown,
): string | null;
```

### A.8 Events and the event service (PR 2)

```ts
// src/types/agent-server/core/events/acp-session-controls-event.ts
import type { ACPSessionControlsEvent } from "@openhands/typescript-client";

export type { ACPSessionControlsEvent };

// src/types/agent-server/type-guards.ts (addition)
export const isACPSessionControlsEvent = (
  event: OpenHandsEvent,
): event is ACPSessionControlsEvent =>
  "kind" in event && event.kind === "ACPSessionControlsEvent";

// src/api/event-service/event-service.types.ts (addition)
export interface EventSearchOptions {
  // …existing fields…
  /** Filter: only events of this kind, as the server's search matches it. */
  // v2: B1, the module-qualified kind: the controls search passes the client's
  // ACP_SESSION_CONTROLS_EVENT_KIND, not the event's own "ACPSessionControlsEvent"
  kind?: string;
}
```

### A.9 `src/api/conversation-service/agent-server-conversation-service.api.ts` (PR 2)

```ts
import type {
  ACPConfigOptionSetResponse,
  ACPConfigOptionValues,
  ACPSessionControls,
} from "@openhands/typescript-client";

const ACP_PREVIEW_TIMEOUT_MS = 2 * 60 * 1000;

export interface CreateConversationOptions {
  // …existing fields…
  /** ACP config option values applied after session/new, before the first prompt (S2). */
  acpConfigOptions?: ACPConfigOptionValues;
}

export interface LocalStartConversationRequest {
  /** The body POST /api/conversations takes, without user_id and acp_config_options. */
  payload: Record<string, unknown>;
  conversationId: string;
  resolvedWorkspaceMode: WorkspaceMode;
}

/** The local half of createConversation, unchanged, shared with the preview. */
declare function buildLocalStartConversationRequest(
  options: CreateConversationOptions,
): Promise<LocalStartConversationRequest>;

export interface PreviewAcpSessionOptions {
  workingDirOverride?: string;
  workspaceMode?: WorkspaceMode;
  agentProfileId?: string;
  agentProfileKind?: AgentKind;
  acpConfigOptions: ACPConfigOptionValues;
}

declare class AgentServerConversationService {
  // …existing methods…

  /** POST /api/acp/preview with the body a start would send. Local only. */
  static previewAcpSession(
    options: PreviewAcpSessionOptions,
  ): Promise<ACPSessionControls>;

  /** POST /api/conversations/{id}/acp/config-options. Local only. */
  static setAcpConfigOption(
    conversationId: string,
    configId: string,
    value: string | boolean,
  ): Promise<ACPConfigOptionSetResponse>;
}

// src/hooks/mutation/use-create-conversation.ts (addition)
export interface CreateConversationVariables {
  // …existing fields…
  /** Values the home screen's picker accepted; sent as acp_config_options. */
  acpConfigOptions?: ACPConfigOptionValues;
}

// src/hooks/query/use-acp-session-preview.ts
export interface AcpLaunchProfile {
  /** `${backendId}:${orgId}:${profile id or "agent-settings"}`. */
  launchKey: string;
  agentProfileId?: string;
  agentProfileKind?: AgentKind;
}

/** The ACP launch agent a start would use: the active profile's id, else agent_settings. */
export declare function resolveAcpLaunchProfile(
  profiles: AgentProfileListResponse,
  backendId: string,
  orgId: string | null,
): AcpLaunchProfile;
```

### A.10 Agent controls (PR 2)

```ts
// src/hooks/chat/use-agent-controls.ts
import type {
  ACPAvailableCommand,
  ACPConfigOption,
  ACPConfigOptionValues,
} from "@openhands/typescript-client";

export interface AgentControls {
  /** The agent's slash commands now; replaced on every report. */
  commands: ACPAvailableCommand[];
  /** Options the picker shows: never "model", never booleans. */
  options: ACPConfigOption[];
  /** Value shown per option id while a change is in flight. */
  pendingValues: ACPConfigOptionValues;
  /** The agent's own sentence for the last refused value, if any. */
  rejection: string | null;
  /** True until the first controls arrive. */
  isLoading: boolean;
  setOption: (configId: string, value: string | boolean) => void;
}

export interface HomeAgentControls extends AgentControls {
  /** Values to send as acp_config_options: those the last successful preview accepted. */
  startValues: ACPConfigOptionValues;
}

// v2: B12, declared in use-acp-session-preview.ts (below) and re-exported here
export type { HomeLaunchContext } from "#/hooks/query/use-acp-session-preview";

export declare const NO_AGENT_CONTROLS: HomeAgentControls;

export declare function useHomeAgentControls(
  launch: HomeLaunchContext,
): HomeAgentControls;

export declare function useConversationAgentControls(
  conversationId: string | null,
): AgentControls;

// src/hooks/query/use-acp-session-preview.ts
export interface HomeLaunchContext {
  /** The pending workspace's path; undefined for none or an isolated backend. */
  workingDir: string | undefined;
  /** Sent, and keyed, only with a workspace (v2: B10). */
  workspaceMode: WorkspaceMode;
}

export interface AcpSessionPreview {
  controls: ACPSessionControls;
  /** The values this preview was asked with, which the agent accepted. */
  values: ACPConfigOptionValues;
}

export declare function useAcpSessionPreview(
  launch: AcpLaunchProfile | null,
  context: HomeLaunchContext,
  values: ACPConfigOptionValues,
): UseQueryResult<AcpSessionPreview, Error>;

// src/hooks/query/use-latest-acp-session-controls.ts
export declare function useLatestAcpSessionControls(
  conversationId: string | null,
  enabled: boolean,
): ACPSessionControlsEvent | null;

// src/hooks/mutation/use-set-acp-config-option.ts
export interface SetAcpConfigOptionVariables {
  conversationId: string;
  configId: string;
  value: string | boolean;
}

export declare function useSetAcpConfigOption(): UseMutationResult<
  ACPConfigOptionSetResponse,
  Error,
  SetAcpConfigOptionVariables
>;

// src/stores/home-agent-options-store.ts
export interface HomeAgentOptionsState {
  /** The launch agent the values were picked for; values under another key are ignored. */
  launchKey: string | null;
  values: ACPConfigOptionValues;
  /** Picking under a new launch key replaces the map. */
  setValue: (
    launchKey: string,
    configId: string,
    value: string | boolean,
  ) => void;
}

export declare const useHomeAgentOptionsStore: UseBoundStore<StoreApi<HomeAgentOptionsState>>;

// src/hooks/chat/use-slash-command.ts (changes)
export interface SlashCommandItem {
  skill: SlashCommandSkill;
  /** The slash command string, e.g. "/random-number". */
  command: string;
  /** Placeholder for the text after an agent command that takes input. */
  inputHint?: string;
}

export interface UseSlashCommandOptions {
  /** The agent's own commands, newest report; replaced, never merged. */
  agentCommands?: ACPAvailableCommand[];
}

export declare function toAgentSlashCommandItem(
  command: ACPAvailableCommand,
): SlashCommandItem;

export declare const useSlashCommand: (
  chatInputRef: React.RefObject<HTMLDivElement | null>,
  options?: UseSlashCommandOptions,
) => {
  isMenuOpen: boolean;
  filteredItems: SlashCommandItem[];
  selectedIndex: number;
  updateSlashMenu: () => void;
  selectItem: (item: SlashCommandItem) => void;
  handleSlashKeyDown: (e: React.KeyboardEvent) => boolean;
  closeMenu: () => void;
};

// src/components/features/chat/components/chat-input-agent-options.tsx
export interface ChatInputAgentOptionsProps {
  controls: AgentControls;
  disabled?: boolean;
}

export declare function ChatInputAgentOptions(
  props: ChatInputAgentOptionsProps,
): React.ReactElement | null;

// src/components/features/chat/custom-chat-input.tsx and components/chat-input-container.tsx (one prop each)
//   agentControls?: AgentControls;

// src/utils/acp-error-codes.ts (addition)
export const ACP_CONFIG_OPTION_REJECTED_CODE = "ACPConfigOptionRejected";
```

### A.11 App backend frames (PR 3)

```ts
// src/extensions/app-backend-session-keeper.ts
export const APP_BACKEND_SESSION_REFRESH_MARGIN_MS = 60_000;
export const APP_BACKEND_SESSION_MIN_REFRESH_MS = 10_000;

export interface AppBackendTarget {
  backend: Backend;
  extensionName: string;
  /** app_backend_ingress_url from the backend's /server_info. */
  ingressUrl: string;
}

export interface AppBackendSessionLease {
  /** ingress_url of the live session: {ingress}/app-backends/{name}/ */
  readonly url: string;
  /** The server's iframe_sandbox tokens. */
  readonly iframeSandbox: string;
  /** Release once; the last release of an App revokes its session. */
  release: () => void;
  /** Called if a refresh fails while the lease is held. */
  onLost: (listener: (error: CanvasExtensionAppBackendError) => void) => void;
}

export declare function acquireAppBackendSession(
  target: AppBackendTarget,
  signal: AbortSignal,
): Promise<AppBackendSessionLease>;

/** The localized error for a reason; unsupported-backend uses the no-ingress sentence. */
// v2: B14, exported for the frame
export declare function appBackendError(
  reason: CanvasExtensionAppBackendErrorReason,
  extensionName: string,
): CanvasExtensionAppBackendError;

/**
 * What a failed session request means for the App's frames: a 503 whose
 * `exception` says "not ready" → not-ready, one naming the ingress →
 * no-ingress, anything else → session-refused.
 */
// v2: B2, B13
export declare function toAppBackendError(
  error: unknown,
  extensionName: string,
): CanvasExtensionAppBackendError;

// src/extensions/mount-app-backend-frame.ts
export declare function mountAppBackendFrame(
  owner: {
    backend: Backend;
    extensionName: string;
  },
  container: HTMLElement,
  options: CanvasExtensionAppBackendFrameOptions,
): CanvasExtensionDispose;
```

---

## Appendix B · New translation keys

Every key gets all of upstream's languages (`npm run make-i18n`, then `check-translation-completeness`); English
values below. Reused keys: `COMMON$MORE_OPTIONS`, `CONVERSATION$PIN_TAB`, `CONVERSATION$UNPIN_TAB`, `COMMON$BACK`,
`SETUP$UNAVAILABLE_TITLE`, `SETTINGS$APPS_PAGE_UNAVAILABLE`, `CHAT_INTERFACE$COMMANDS`.

| Key | English | PR |
|---|---|---|
| `CONVERSATION$SHOW_APP_PANEL` | `Show {{title}}` | 1 |
| `CONVERSATION$HIDE_APP_PANEL` | `Hide {{title}}` | 1 |
| `SETTINGS$APPS_PANELS` | `Panels` | 1 |
| `SETTINGS$APPS_PANELS_UNSUPPORTED` | `{{name}} has header panels this agent-server does not support. Update the agent-server to show them.` | 1 |
| `CHAT_INTERFACE$AGENT_OPTIONS` | `Agent options` | 2 |
| `CHAT_INTERFACE$AGENT_OPTION_FIXED` | `Fixed for this conversation` | 2 |
| `ERROR$ACP_CONFIG_OPTION_REJECTED_TITLE` | `The agent refused an option` | 2 |
| `CANVAS_EXTENSIONS$APP_BACKEND_NO_INGRESS` | `This agent-server has no App ingress, so {{name}} cannot show its backend.` | 3 |
| `CANVAS_EXTENSIONS$APP_BACKEND_NOT_READY` | `{{name}}'s backend is not running.` | 3 |
| `CANVAS_EXTENSIONS$APP_BACKEND_SESSION_REFUSED` | `The agent-server refused {{name}}'s backend session.` | 3 |

---

## Appendix C · The mock ACP agent's controls mode (Canvas end-to-end)

`tests/e2e/mock-llm/scripts/mock-acp-server.py` gains `--session-controls`, off by default (so upstream's ACP specs
see today's agent). Its behaviour mirrors S2's scripted test agent (S2 Appendix C), names included, so the same
scenario reads the same in both repositories; C1 extends the same script behind its own flag.

- `initialize`: advertises `sessionCapabilities.close`.
- `session/new`: answers with one `select` option `profile` (`name` "Profile", values `fast` and `thorough`, current
  `fast`), then sends `available_commands_update` for the current value: `fast` → `summarize` ("Summarize the
  input", no input); `thorough` → `summarize` and `compare` ("Compare two things", input hint `what to compare`).
- `session/set_config_option`: an unknown id → invalid params `unknown option '{id}'`; an unknown value → `unknown
  profile '{value}'`; after the first prompt any value but the current one → `profile is fixed once the session has
  started (it is '{current}')`; otherwise it sends the new value's commands, then answers with the full options.
- `session/prompt`: on the first prompt, sends `available_commands_update` with no commands and a
  `config_option_update` whose `profile` lists only the current value; then the usual reply, which in this mode reads
  `MOCK_ACP_E2E_REPLY_OK profile=<current>`; then `end_turn`.
- `session/close`: answers `{}`.

*(v2, as built in `82ff26a`: as above, with three details. The commands after `session/new` are sent 50 ms after its
answer, from a background task, so the agent-server's first controls event of a start without values lists no
commands (S2's §3.2 B4; §3.2 B4 here); a start with a value gets the value's commands from the set, before the first
prompt. Every reply after the first prompt also reads `profile=<current>`. With `--session-controls` the agent runs
ACP's unstable protocol, where `session/close` is.)*
