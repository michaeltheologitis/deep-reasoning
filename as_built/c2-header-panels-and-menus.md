# C2 · App header panels, agent commands and an option picker, as built

**TASK-7** · Cartographer · the code at `64b5a8b`, head of `feat/agent-surfaces` in the Canvas fork
[michaeltheologitis/OpenHands](https://github.com/michaeltheologitis/OpenHands) (draft PR #3 into `wiring/dr-1` at
`9881d24`; C2 is `git diff 9881d24 64b5a8b`: nine commits of its own, the fork's `ba4d883` at its base, and two merges
of `wiring/dr-1`) · checked against the design at `72aa49f` (`docs/design/c2-header-panels-and-menus.md` v1, still the
head of `origin/design/c2` when I wrote this) · agent-server and TypeScript client from the SDK fork's tag `dr-1`
(`cef3b24`) · Node 22.22 and npm 10.9 in this sandbox, Node 24.15 and npm 11.12 in CI · 2026-10-03.

**Where this file lives.** On deep-reasoning's branch `as-built/c2`, cut from `design/c2`. C2's code is in the
Canvas fork, which carries only upstream-shaped code plus marked fork-only commits, so no document of ours goes
there. This branch holds only documents (no `pyproject.toml`, no docs site, no test runner), so nothing builds or
collects `as_built/` and there is nothing to wire. [run: `git ls-tree` of this branch]

**Evidence marks.** Every claim carries one.
- **[run]**: executed in this sandbox, never in the fork's checkout: a `git archive` of `64b5a8b` (and of `9881d24`,
  C2's base, for comparison) with its own `npm ci`. C2's 26 test files at head and base, the full suite, `npm run
  lint`, `npm run build`, `npm run build:lib`, the translation check, and uncommitted probes (copies of C2's test
  files with one probe test added; a Python probe of the agent-server's search filter in an export of `cef3b24`).
- **[CI]**: read from GitHub's records through the GitHub MCP tools, with the full job logs downloaded: CI run
  37153648487 and live run 37153648974 at `64b5a8b`, and the full mock-LLM runs 37153914745 (`64b5a8b`), 37149694708
  (`ba4d883`) and 37152465164 (`86c00b5`).
- **[read]**: read in the code, **not executed**. Weaker than [run]; §7 lists the read claims that matter.

Nothing here ran a paid model, the `claude` CLI or a live test. The live tier is reported from CI.

**Reading order.** §2 first (the divergences), then §1 and §3–§4 as the map, §4.6–§4.7 for who C2 relies on and who
relies on C2 (D3 above all), §6 for the tests and runs, §7 for what I could not verify.

---

## 1 · What exists

C2 adds three generic surfaces to Agent Canvas, each behind an agent-server capability read from the local
backend's cached `/server_info`. No added source line names deep_reasoner, dr-acp or `dr-library` or reads `_meta`
(one comment says "namespace" generically; the pill tests use a `namespace` option as their example). [run: grep of
the added lines]

1. **App header panels** (`canvas_conversation_panels_v1`). An App's `contributes.conversation_panels` gives each
   panel a button after Show panel. It opens the drawer's column with the App's tab row, a ⋯ menu that opens and pins
   tabs, and the selected tab's page, an App page registered under the tab's id and mounted with the conversation's
   id. The store keeps at most one of drawer, App panel and overview open. A narrow window gets a page per panel.
2. **Agent commands and an option picker** (`acp_session_controls_v1`). An ACP agent's slash commands join the slash
   menu; a row above the message input shows its select options, except `model`, as pills. On the home screen both
   come from `POST /api/acp/preview`, and the accepted values go with the start as `acp_config_options`; in a
   conversation they come from the newest `ACPSessionControlsEvent`, and a pick is set live.
3. **App backend frames** (`canvas_app_backend_bridge_v1`). `host.appBackend.mountFrame(container, {path, title,
   onError})` shows the App's own backend in a sandboxed `<iframe>` on the agent-server's App ingress origin, with one
   host-kept, refreshed session per App. The design proposed this unit for the Conductor's ruling (design §3 item 1,
   §11 item 2); it is built as proposed.

```text
App header panel
  /server_info ─ canvas_conversation_panels_v1 ─┐
  GET /api/canvas-extensions/installed ─ manifest.contributes.conversation_panels
  runtime: activate(host) → host.registerPage(<tab id>, mount) → resolveDeclaredContribution → panel-tab | page | panels-unsupported
           panels = toRegisteredPanels(enabled Apps, registered tabs)       (manifest order, tabs registered only)
  header:  [Git] [Overview] [Show panel] [◇ per panel] ── click → store.openAppPanel("<app>/<panel>")  (narrow: navigate to the panel page)
  column:  ConversationMain: isRightColumnOpen = drawer || registered panel; drawer kept mounted, `hidden`
           ConversationAppPanel: tab row + ⋯ (useConversationAppPanelTabs ⇄ localStorage conversation-state-<id>.appPanelTabs)
           ConversationAppPanelTabContent: useCanvasExtensionMount(mount, {path, navigate, conversationId, surface}, key=[conv, panel, tab])

Agent controls
  home:    useHomeAgentControls ─ launch key, picked values (session store) ─ useAcpSessionPreview
             → previewAcpSession: buildLocalStartConversationRequest (the start's builder) + acp_config_options → POST /api/acp/preview
           send → createConversation(..., acpConfigOptions = values the last answered preview accepted) → POST /api/conversations
  convo:   useConversationAgentControls ─ useLatestAcpSessionControls:
             newer by timestamp of (event store's newest controls event, one GET …/events/search?kind=<module-qualified>&sort_order=TIMESTAMP_DESC&limit=1)
           pick → POST /api/conversations/{id}/acp/config-options; the next event replaces the controls
  both:    CustomChatInput(agentControls) → useSlashCommand({agentCommands}) and ChatInputAgentOptions (the pill row)

App backend frame
  host.appBackend.mountFrame → resolveTarget (/server_info: bridge capability + app_backend_ingress_url)
    → acquireAppBackendSession (one session per backend + App: mint, refresh 60 s before expiry, revoke at the last release)
    → <iframe src="{ingress}/app-backends/{name}/{path}" sandbox=<server's tokens> referrerpolicy=no-referrer>
```

[read; each path run by the tests of §6.4, and the first two in the live tier, §6.3]

| Unit | Commits | Code | Unit tests | End-to-end | Specs (`specs/*.md`) | Other |
|---|---|---|---|---|---|---|
| 1 · header panels | `20b90cb` registration, store, tab state · `1828cec` button, column, panel, narrow page, fixture · `a5436be` spec text, E2E | +1,224 −87 | +1,391 −8 | +275 spec, +15 mapping | +81 −1 | i18n +68; fixture +67; skill guide +1 −1 |
| 2 · agent controls | `4caaecc` controls, preview, slash menu, pills · `82ff26a` spec text, mock agent flag, E2E | +957 −53 | +1,349 −3 | +199 spec, +142 −12 mock agent and mapping | +47 | i18n +51; skill guide +1 −1 |
| 3 · backend frames | `baddd10` session keeper, frame, host API · `db3b4b9` spec text | +429 −1 | +478 | — | +38 | i18n +51 |
| fixes | `70ce577` 5xx reasons from `exception` · `86c00b5` empty first report | +35 −10 | +68 −2 | — | — | — |

In all (the net diff), **+6,955 −167 in 89 files**: code +2,635 −141 (50 files), unit tests +3,284 −11 (27 files,
one a shared helper), end-to-end specs +474, mock agent and test mapping +157 −12, fixture +67, translations +170,
upstream product specs +166 −1, skill guide +2 −2. The per-commit code figures sum to 10 lines more than the net,
because `70ce577` rewrites lines `4caaecc` and `baddd10` added. [run: `git diff --numstat`, `git show --numstat`]

Not counted as C2's: `ba4d883` (the fork's launcher-workflow registration, on `deep-reasoning` before C2 began; its
file is byte-identical to C3's `22272d9` in the wiring, so it adds nothing to the net diff [run: `git diff 9881d24
64b5a8b -- .github/workflows/launcher-live.yml` is empty]), and the merges `c08ded0` and `64b5a8b`, which bring in
`wiring/dr-1`: C3's launcher, `config/defaults.json` `sources` naming the SDK fork at `cef3b24`, the client tarball
pin, and the fork-only `specs` input of the mock-LLM workflow (`9881d24`). Neither merge carries a conflict
resolution of its own. [run: `git show --cc` prints no combined hunks]

---

## 2 · Divergences from the design (`72aa49f`)

The changelog holds no entry for TASK-7, so no `drift:` line; every item below was found from the code. All nine
of C2's commits were made after the design (`72aa49f`, 2026-10-02 19:00; C2's commits 2026-10-03 05:31–20:41).
"Design §x" cites `72aa49f`. The brief named four known divergences, which D-1, D-2 and D-4 verify; the others, and
D-1's consequence for D3, are new. [run: Notion query of the Changelog; `git log`]

### 2.1 Behaviour a user, an App or D3 sees

**D-1 · The events search uses the module-qualified kind; the short kind the design gives, and D3 copied, finds
nothing.** Design §5.3 and §7.2 search with `kind: "ACPSessionControlsEvent"`. Built,
`useLatestAcpSessionControls` passes the client's `ACP_SESSION_CONTROLS_EVENT_KIND`
(`src/hooks/query/use-latest-acp-session-controls.ts:50`), whose value in the dr-1 client is
`openhands.sdk.event.acp_session_controls.ACPSessionControlsEvent` [run: read from the installed tarball]. At dr-1
the agent-server compares `kind` with `f"{module}.{class}"` (`event_service.py:548–551` at `cef3b24`): a probe of
that filter returns `False` for the short kind and `True` for the qualified one, while the serialized event still
says `"kind": "ACPSessionControlsEvent"` [run: probe in an export of `cef3b24`]. C2's type guard
`isACPSessionControlsEvent` (`src/types/agent-server/type-guards.ts:315–318`) checks the serialized short kind,
the kind a fetched event carries. Reason: S2's as-built D-1 and commit `4caaecc` ("one search by the
module-qualified kind"). **Consequence outside C2:** design §7.2, the contract D3 built against, still prints the
short kind as the way a panel page reads its conversation's namespace, and D3's `readConversationNamespace`
(deep-reasoning `v1-decompositions-panel`, `canvas-app/src/page/context.ts`) searches with exactly that string. At
dr-1 its search therefore returns no items, and D3's frame is always given `namespace = null`, `started = false`
(§4.7). D3's as-built does not name this; its tests use a fake host. [run: the filter probe; read: D3's code]

**D-2 · A 5xx answer's reason is read from `exception`; `getSdkHttpErrorDetail` is null for every 5xx**
(`70ce577`). Design §5.1 and A.7: `getSdkHttpErrorDetail` returns "the `detail` string of an SDK `HttpError`'s parsed
body, else `null`", and §6.2 item 4 reads "a 503 whose detail says the backend is not ready". The agent-server's
handler answers every 5xx `HTTPException` with `{"detail": "Internal Server Error", "exception": "<status>:
<reason>"}` (`api.py`, `_http_exception_handler`, at `cef3b24`; S2's as-built D-11) [read]. Built:
`getSdkHttpErrorDetail` returns `null` when the status is 500 or more (`src/api/agent-server-compatibility.ts:225–229`),
and the new `getSdkHttpServerErrorReason` returns `exception` only for a 5xx (`:235–239`); the session keeper reads
the latter (`src/extensions/app-backend-session-keeper.ts:76–84`). Consequences: a failed live set that is not a
422 toasts the client's own message (`HTTP request failed (504)` in the test) rather than the agent-server's reason;
before `70ce577`, a stopped App backend or a missing ingress was reported to the frame as `session-refused`. Reason:
the commit message. [run: `getSdkHttpErrorDetail is null for a 5xx answer…`, `never shows a 5xx answer's
placeholder detail as the agent's sentence`, and the frame's `not-ready` and `no-ingress` cases, which the commit
message says failed against the old keeper]

**D-3 · The preview's body equals the start's less `initial_message`, `user_id` and `conversation_id`, and, with no
workspace chosen, `working_dir` too.** Design §5.2 and decision I: the preview body equals the start body "less
`initial_message` and `user_id`". Built, `previewAcpSession` calls the start's own builder,
`buildLocalStartConversationRequest` (`src/api/conversation-service/agent-server-conversation-service.api.ts:456–510,
662–676`), which mints a fresh conversation id per call (`:480`) and, when no workspace is chosen, derives the
working directory from that id through `resolveNewConversationWorkspace`. So each preview and the start name
different ids, and without a workspace different working directories (each `<workspace root>/<its own id>`); the
parity test deletes `conversation_id` from both bodies and uses `workingDirOverride: "/repo"`. With a workspace the
bodies match as designed. The agent-server's preview runs in an empty scratch workspace when the directory does not
exist (S2's as-built §4.3). No reason recorded. [run: a probe copying the service tests, no workspace chosen: two
previews and the start differ pairwise in `workspace` (three working directories, `/state/workspaces/<id hex>` under
the tests' stub) and `conversation_id`, and the start also in `initial_message`; read: the builder]

**D-4 · The first controls report of a start or resume is shown as it is, even when it lists no commands**
(`86c00b5`, the Conductor's ruling). Design §5.3 says no event means no commands and no picker, and treats the
newest event as the agent's current state; it does not anticipate S2's as-built D-2, under which every ACP session
start (and resume) persists one event right after `session/new`, which can list no commands before the agent's menu
follows in a later event. Built, the conversation's controls are whatever the newest event says
(`src/hooks/chat/use-agent-controls.ts:131–138`): for that interval the picker shows the first report's options and
the slash menu lists no agent command; the next event replaces both. Reason: commit `86c00b5` ("the menu follows
whichever report is newest") pins the sequence. [run: `shows no agent commands after an empty first report until
the agent's menu arrives`]

**D-5 · App-backend failures are classified by the reason's words, not by status.** Design §6.2 item 4: `not-ready`
for a 503 whose detail says not ready, `session-refused` for 401, 403, 409 and 421; §6.3: a failed refresh reports
`session-refused`. Built, `toAppBackendError` (`src/extensions/app-backend-session-keeper.ts:72–86`): a 503 whose
`exception` matches `/not ready/i` is `not-ready`; a 503 matching `/ingress/i` (the bridge's "ingress is not
configured" or "misconfigured" at mint time, `bridge.py:231–244` at `cef3b24`) is `no-ingress`, which the design
reaches only from `/server_info`; anything else (any status, a network error, the bridge's other 503s such as "Canvas
App sessions require HTTPS or a loopback secure context") is `session-refused`. A failed refresh goes through the same
mapping, so it can report `not-ready` or `no-ingress`. `unsupported-backend` shows the `no-ingress` sentence
(`:58`). No reason recorded. [run: the frame tests for each reason; read: the bridge's sentences]

**D-6 · MSW mock mode does not serve the `demo-panel` fixture.** Design §4.8: the fixture is used "by the unit
tests, the end-to-end spec and MSW mock mode (`canvas-extensions-handlers.ts` serves it beside `demo-page`)". Built,
`src/mocks/canvas-extensions-handlers.ts` is unchanged and serves `demo-page` only (`:7–12`); the fixture is used by
the unit tests and the panels end-to-end spec. The fixture also gains an `icon.svg` the design's manifest lacked,
which the end-to-end spec asserts is fetched. No reason recorded. [read; run: grep for `demo-panel`]

### 2.2 Signatures and small behaviours

None of these changes what §2.1 describes. [read unless marked]

| Design | Built |
|---|---|
| `ConversationAppPanelTabContent` shows `LoadingSpinner` while the App activates (§4.4) | no spinner in the column: a panel exists only once a tab is registered, i.e. after activation. The narrow-window page has the spinner and the unavailable state (`conversation-app-panel-mobile-page.tsx:81–89`) |
| `ConversationAppPanelProps {conversationId, panel, variant?}` (A.6) | adds `leading?: ReactNode`; the narrow page puts its back button in the tab row through it |
| `ConversationTabNav` gains an optional `icon` (A.6) | also gains `testId?: string` (the App tabs' `conversation-app-panel-tab-<id>`) |
| the runtime's `notices` hold the notice text (§4.1) | they hold the i18n key; the Apps card translates it with `{name: display name}` (`canvas-extension-card.tsx:28–35`) [run: card test] |
| `ConversationAppPanelToggles` renders nothing on a Cloud backend (§4.3) | no backend check of its own; the App list query is local-only (`use-canvas-extensions.ts:15`), so no panel exists on Cloud [run: `renders no button on a Cloud backend`] |
| — | `CANVAS_EXTENSION_AGENT_SERVER_REQUEST_TIMEOUT_MS = 60_000` exported and documented in `specs/canvas-extensions.md` (the existing 60 s of `host.agentServer.request`, named) |
| preview key `[…, launchKey, workingDir, workspaceMode, values]` (A.2) | `workspaceMode` is `null` when no workspace is chosen, as the start sends none (`use-acp-session-preview.ts:71`) |
| the route page's mount effect "moves unchanged" into `useCanvasExtensionMount` (§4.1) | it remounts when `mount` or the route path changes; upstream's effect also re-ran when the `page` object or `navigate` changed (`routes/canvas-extension-page.tsx`) |
| decision L: a later item repeating an earlier command is dropped | applied to the whole list, so two skills with the same slash trigger, both listed before C2, now list once (`use-slash-command.ts:47–55, 110, 126`) |
| a fixed pill is "a select with one value" (§5.6) | `options.length < 2`, so also a select with none (`chat-input-agent-options.tsx:111`) |
| choosing a value calls `controls.setOption` (§5.6) | only when it differs from the option's `current_value` (`:169`); see §4.2 for what that means after a refusal |
| invariants `CX-001`–`CX-005`, `ASC-001`–`ASC-004` (§3 item 13) | adds `CX-006` and `ASC-005`, each a table of `data-testid`s declared a contract for end-to-end tests (`specs/canvas-extensions.md:380`, `specs/acp-session-controls.md:35`); new ids `conversation-right-column`, `slash-command-item` (with `data-command`), `agent-options`, `agent-option-rejection` |
| mock agent: `initialize` advertises `sessionCapabilities.close` (Appendix C) | only with `--session-controls`, which also switches on ACP's unstable protocol (for `session/close`); the first menu is sent 50 ms after `session/new` answers (`mock-acp-server.py`) |
| `CanvasExtensionsService.createAppBackendSession(…, signal?)` (A.2) | built with the signal parameter; the keeper never passes it and abandons a pending mint by racing it with the abort instead (`app-backend-session-keeper.ts:172–199`) |

### 2.3 The pull request, the proof and size

**D-7 · One draft PR into the wiring branch, not three upstream-shaped PRs.** Design §1.2 and §9: three PRs, each an
upstream-shaped draft branch on the fork's `main`, with PR 2's first commit the client bump. Built: PR #3
(`feat/agent-surfaces` → `wiring/dr-1`) carries all three units as code-then-spec commit pairs, then the two fixes;
the client pin arrives with the wiring merge (`c08ded0`), not as a commit of PR 2. Units 1 and 2 share
`agent-server-compatibility.ts` and its test, `query-keys.ts`, the e2e guide and `test-mapping.json`; units 1 and 3
share the manifest types, `lib/index.ts`, the runtime and its test, `canvas-extensions-service.ts` and
`specs/canvas-extensions.md`; all three share `translation.json`. I did not cherry-pick them apart (§7). [CI: the PR;
run: `git log`, `git show --name-only` per commit]

**D-8 · The full mock-LLM suite is red; the live tier is C2's two specs alone.** Design §10, layer 3: upstream's
"full vitest and Playwright suites green on `feat/agent-surfaces`"; the live tier is "the two specs above, green in
the fork's mock-LLM run at the branch's head". The vitest suite is green in CI; here two upstream files failed under
load and pass alone (§6.1) [CI, run]. The full Playwright suite at
`64b5a8b` fails **six** upstream tests (run 37153914745), the same six with the same first errors as at `ba4d883`, the
fork's `deep-reasoning` before C2 (run 37149694708), §6.5. The live tier ran as a separate dispatch of the same
workflow with the fork-only `specs` input (`9881d24`) set to C2's two spec files: 7 of 7 passed (run 37153648974);
C2's seven also pass inside the full run. The brief, the task row and the PR body say five upstream failures: that
count is the run at `86c00b5` (37152465164), in which `mock-llm-files-and-git.spec.ts` step 2 passed; in both runs
the brief cites it fails. [CI: all four logs]

**D-9 · No mutation testing ran.** Design §4.9 and §5.8: `npm run test:mutation:diff` (Stryker on the diff) "runs on
the PR", and survivors "are listed in the as-built". No workflow in the fork runs Stryker (`.github/workflows/`), the
PR body reports none, and I did not run it (§7). [read; run: grep of the workflows]

**D-10 · Size: about three times the estimate.** Design §3 item 2: ≈2.1k lines with tests (PR 1 ≈1.0k: slot ≈600,
tests ≈400; PR 2 ≈0.85k: ≈500 and ≈350; PR 3 ≈0.27k). Built: +6,955 −167 (§1); without translations, the fixture and
the spec texts, code +2,635 and tests +3,915 (unit 3,284, end-to-end 474, harness 157). Code is about twice the
estimate, tests about five times. The largest code pieces: `canvas-extensions-runtime.tsx` +213 −19 (registration,
panels, the host's frame mounter), `chat-input-agent-options.tsx` 221, `app-backend-session-keeper.ts` 217,
`use-agent-controls.ts` 212, the conversation service +132 −42; the largest tests:
`use-acp-session-preview.test.tsx` 357, `mount-app-backend-frame.test.ts` 264, `use-agent-controls.test.tsx` 253,
the toggle and panel tests 221 and 219. [run: `git diff --numstat`]

**D-11 · Every test the design names exists; a few more were added.** Each row of §4.9, §5.8 and §6.4 has a test
under a name stating its property, or an `it.each` case (§6.4). Beyond them: the capability helper (5 cases), the
icon fetch and the named timeout, the Apps card (3), the `appPanelTabs` write that keeps another panel's entry, a
selected unpinned tab staying visible, the narrow page's unavailable state, the in-flight pill, a fixed option
without a description, D-2's and D-4's tests, and the
frame's notice beside a frame whose refresh failed. Design §11 item 5's first check, that the drawer's terminal
survives being hidden, is pinned at the component level only: the test asserts the drawer's content component is not
unmounted and is not visible, with that component mocked (§7). [run: the tests; read: the mapping]

**Not divergences.** Decisions A–N as written (one column, the store as the only writer, `hasRightPanelToggled`
cleared on open; tabs registered through `registerPage`; the drawer kept mounted; per-conversation tab state,
session-only open state; the narrow-window route; capability gates with a non-fatal refusal; controls computed by
each composer's owner; newer-by-timestamp of the live and searched event; one start builder; local backends only; the
picker row; menu order; refusals in the agent's words; the host-kept frame); design §3 items 3–12 (tooltip as the
title, scrolling tab row, the selected tab closing the panel, the panel on an archived conversation, no overview peek
while a panel is open, the hint in the menu row, booleans not rendered, no picker before the first message, the
generic Apps notice); §4.2's action table and `CX-001`; §4.4's tab rules; §5.4's key, store and start values; §5.6's
pills; §6.3's session keeping; and Appendix B's ten keys, each in all 15 languages. [run for every behaviour the tests
of §6.4 name and the translation check; read for the rest]

---

## 3 · The public surface, from the code

**App manifest and host API** (`src/types/canvas-extension.ts`, re-exported from `src/lib/index.ts`; host API still
version `"1"`). `contributes.conversation_panels: [{id, title, icon?, tabs: [{id, title, path}]}]`. Every mount
context gains `conversationId: string | null` and `surface`: `{kind: "page"}` on a routed page, `{kind:
"conversation-panel", panelId, tabId, selectTab(tabId)}` in a panel, where `path` is the tab's path without its
leading `/` (`""` for `/`). `host.appBackend.mountFrame(container, {path?, title, onError?}) → dispose`, with
`onError({reason: "no-ingress" | "not-ready" | "session-refused" | "unsupported-backend", message})` at most once;
the frame is the `<iframe>` appended to the container and stays there, across refreshes, until disposed.
`registerPage` of a panel's own id, an undeclared id or an id twice throws (failing activation); on an agent-server
without `canvas_conversation_panels_v1` an undeclared id returns a no-op disposer and sets the App's notice instead.
[run: runtime and frame tests]

**Routes and state.** `/conversations/:conversationId/panel/:extensionName/:panelId` (a narrow-window page,
`routes/conversation-app-panel.tsx` re-exporting the conversation route). `useConversationStore` gains
`activeAppPanel: "<app>/<panel>" | null` (session-only), `openAppPanel(key)` (also closes drawer and overview and
clears `hasRightPanelToggled`) and `closeAppPanel()`; `setIsRightPanelShown(true)` and `setIsOverviewPanelShown(true)`
also clear `activeAppPanel` (`conversation-store.ts:169–189, 423–437`). The `conversation-state-<id>` localStorage blob
gains `appPanelTabs: {"<app>/<panel>": {selectedTab, unpinnedTabs}}`, sanitized on every read. [run]

**Services.** `CanvasExtensionsService.fetchPanelIcon(name, panelId, backend?) → Blob`, `createAppBackendSession(name,
backend, ingressUrl, signal?)`, `revokeAppBackendSession(name, backend, ingressUrl)` (errors logged, never thrown).
`AgentServerConversationService.previewAcpSession({workingDirOverride?, workspaceMode?, agentProfileId?,
agentProfileKind?, acpConfigOptions}) → ACPSessionControls` (120 s timeout) and `setAcpConfigOption(conversationId,
configId, value) → ACPConfigOptionSetResponse`, both refusing a Cloud backend; `createConversation` and
`useCreateConversation` accept `acpConfigOptions`, sent only when non-empty. `EventSearchOptions.kind`, passed to
the local search and to the Cloud query string. `agent-server-compatibility.ts`: `AgentServerCapability`,
`localAgentServerHasCapability`, `getSdkHttpErrorDetail`, `getSdkHttpServerErrorReason`. [run]

**Hooks and components.** `useConversationAgentControls(conversationId)`, `useHomeAgentControls({workingDir,
workspaceMode})` and `NO_AGENT_CONTROLS` (`hooks/chat/use-agent-controls.ts`); `useLatestAcpSessionControls`,
`useAcpSessionPreview`, `resolveAcpLaunchProfile`, `useSetAcpConfigOption`, `useHomeAgentOptionsStore`;
`useSlashCommand(ref, {agentCommands})` and `toAgentSlashCommandItem`; `ChatInputAgentOptions`; the panel components
of design A.6 under `components/features/conversation/`, plus `ConversationAppPanelUnavailable`; the
`useCanvasExtensionMount` hook shared by routed pages and panel tabs. [read]

**What the user sees.** A header button per panel, tooltip and accessible name "Show <title>" or "Hide <title>",
the manifest's icon (fetched with the session key, shown as a `data:` URL) or a panel glyph; the open panel as a
region named after the panel, with text tabs and a ⋯ menu of "open" and pin rows. On the Apps page, a "Panels: N"
pill, one pill per panel title, and under the description the App's activation error or "<name> has header panels
this agent-server does not support. Update the agent-server to show them." Above the message input, one pill per
select option, `<option name>: <value name>`, a spinner while a pick is in flight, a fixed pill (no caret, tooltip
the option's description or "Fixed for this conversation") for a single value. In the slash menu, agent commands
after the built-ins with their hint as `‹what to compare›`. On the home screen a refusal shows under the pills; in a
conversation it is a toast; a start-time refusal heads the error banner "The agent refused an option" with the
agent's sentence. A frame that cannot be shown leaves a one-line notice in its container. [run: component tests; CI:
the live tier for the header, panel, pills and menu]

**Requests Canvas makes for C2.**

| Request | When | Evidence |
|---|---|---|
| `GET /api/canvas-extensions/installed/{name}/panels/{panel_id}/icon` (session key, blob) | a panel declares an icon; cached per backend, org, App, resolved ref and panel | [CI: the icon's `data:image/svg+xml`] |
| `POST /api/acp/preview` (the start body + `acp_config_options`) | home screen, ACP launch agent, capability present; again for each new pick or workspace; never on focus; no retry | [CI] |
| `POST /api/conversations` + `acp_config_options` | a home start with accepted values | [CI: the request body] |
| `GET /api/conversations/{id}/events/search?kind=<qualified>&sort_order=TIMESTAMP_DESC&limit=1` | once per backend and conversation (`staleTime: Infinity`), ACP conversation, capability present | [run: unit; CI: the reload pass, §6.3] |
| `POST /api/conversations/{id}/acp/config-options` | a pick in a conversation | [run: unit only] |
| `POST` / `DELETE {ingress}/app-backends/{name}/session` (session key, credentials) | first frame of an App; refresh 60 s before expiry (not sooner than 10 s); last frame closed | [run: unit, client faked at its boundary] |

**The mock ACP agent** (`tests/e2e/mock-llm/scripts/mock-acp-server.py`) gains `--session-controls`, off by default:
one select option `profile` (`fast`, `thorough`), commands per value (`fast`: `summarize`; `thorough`: `summarize`,
`compare` with hint `what to compare`), refusals as invalid params, and at the first prompt an empty menu and a
one-value `profile`; replies then read `MOCK_ACP_E2E_REPLY_OK profile=<value>`. [CI: the live tier; read]

---

## 4 · Structure and seams

### 4.1 The panel slot (unit 1)

**Registration** (`canvas-extensions-runtime.tsx`). `registerPage` first rejects a repeated id, then asks
`resolveDeclaredContribution` (`:157–183`): a declared page (as before), a declared tab of a declared panel
(re-validated: kebab-case App, panel and tab ids, a path of `/` or an absolute kebab-case path), a panel's own id
(throws), or an id declared nowhere, which throws unless the **active local** agent-server's cached `/server_info`
lacks `canvas_conversation_panels_v1`, in which case it is `panels-unsupported`: a no-op disposer and the App's notice.
Tabs are kept per App during activation and published into state after `activate` returns; `panels` is derived in
a `useMemo` from the enabled Apps (list order) and the registered tabs (manifest order), so a panel with no registered
tab does not exist and a disable, a re-activation or a backend switch removes panels with their pages. The
activation signature now includes `conversation_panels`. [run: runtime tests]

**One column** (`conversation-main.tsx:32–34, 135`). `isRightColumnOpen = isRightPanelShown || appPanel !== null`,
where `appPanel` is the registered panel for `activeAppPanel`, so a key whose App is gone reads as closed and nothing
clears it. The drawer's tabs and content stay mounted under the `hidden` attribute (Tailwind 4.3.3's preflight makes
`[hidden]` `display: none !important`, over the element's `flex` class [read]). The column's width, resize handle and
the chat's width are the drawer's. The store's four actions are the only writers of the three open-flags. [run:
store table test, main tests; CI: the first panels test]

**Tab state** (`hooks/use-conversation-app-panel-tabs.ts`). The selected tab is resolved at read time (stored if
registered, else the first pinned, else the first) and written only on a pick; unpinning the selected tab selects the
next pinned one; `selectTab` of an unknown id is ignored with a console warning. Writes go through
`setAppPanelTabState`, which re-reads the stored blob so a write for one panel keeps another panel's entry
(`conversation-local-storage.ts:487–494`). [run]

**Mount lifecycle** (`conversation-app-panel-tab-content.tsx`, `use-canvas-extension-mount.ts`). The selected tab is
mounted into an emptied container with the key `[conversationId, panel key, tab id]`; a change of key or of the
`mount` function disposes first, then empties the container and mounts again; the context is read through a ref. A
mount that throws or rejects shows the unavailable state, keeping the container for the next tab. Leaving the
column (another opener, the conversation route, the breakpoint) unmounts the component, which disposes. [run: panel
tests; CI: the demo App's lifecycle in the live tier]

### 4.2 Agent controls (unit 2; where most of the complexity sits)

**The gate** (`use-agent-controls.ts:76–80`): ACP context, a local backend, and the capability in the cached
`/server_info`. The capability is read from a module-level cache when the hook renders; nothing subscribes to it.
[read]

**In a conversation** (`:117–148`, `use-latest-acp-session-controls.ts`). Two sources: a selector scanning the event
store from the end for the newest controls event of this conversation (only when the store is loaded for it), and one
REST search (D-1), cached for the session. The newer by ISO timestamp wins, the live one on a tie; nothing is merged.
Options shown are the selects except `model`; a pick calls the set route through `useSetAcpConfigOption` (no global
toast), shows the value with a spinner while pending, and on failure toasts `getSdkHttpErrorDetail(error) ??
error.message` (D-2). Success does nothing: the next event replaces the controls. [run]

**On the home screen** (`:157–212`, `use-acp-session-preview.ts`, `stores/home-agent-options-store.ts`). The launch
agent is the active agent profile, else `agent_settings` (`resolveAcpLaunchProfile`); its key is
`<backend>:<org>:<profile or "agent-settings">`. Picked values live in a session store under the key they were picked
with; values under another key are ignored. The preview query is keyed by launch key, workspace, workspace mode and
values; it keeps the previous data while a new key loads, never refetches on focus and never retries. A ref keeps
the last preview the agent answered for this launch key. Then:
- a 422 shows the agent's sentence under the pills and keeps showing the last answered preview's commands and
  options; any other failure shows no commands and no pills;
- `startValues` are the last answered preview's values, restricted to option ids it reported and, for a select, to
  values it listed (`ASC-002`); `HomeChatLauncher` sends them only when non-empty (`home-chat-launcher.tsx:151–152`).

After a refusal the refused value stays in the store (a test pins it), while the pill shows the last accepted value.
The store keeps it until a third value is picked, the launch agent changes or the app restarts: choosing the value
the pill shows does nothing (`chat-input-agent-options.tsx:169`), and choosing the refused value again keeps the same
query key, so no new preview is sent and the refusal stays (a return to the home screen does refetch it). A two-value
option has no third value. A start still sends
only the last accepted values (here none, so the agent's default). Every later preview carries the refused value
with any other pick [read]. [run: two probes copying the preview and pill tests, `thorough` refused after `fast`:
shown `fast`, store `{profile: "thorough"}`, `startValues` `{}`, no preview on re-picking, no `setOption` for the
shown value]

**The slash menu** (`use-slash-command.ts:102–127`): built-ins, then the agent's commands (not waiting for skills),
then skills, with any repeated command dropped after its first appearance. Each agent command becomes a
`SlashCommandItem` with a skill shim and its hint; selecting it inserts `/<name> `. **The pill row** renders in
`ChatInputContainer` after the uploaded files, only when there are options or a refusal (`chat-input-container.tsx:89`).
[run]

### 4.3 The start body and the preview

`buildLocalStartConversationRequest` is `createConversation`'s former local half, moved unchanged (settings and
profiles, the title profile, a new id, the workspace, the encrypted-settings body); `createConversation` adds
`acp_config_options` (only when non-empty) and `user_id`, and `previewAcpSession` adds `acp_config_options` and posts to
the client's `previewAcpSession`. The start's body without values is byte-identical to the body before C2 (a test
compares the JSON). [run; D-3 for what differs]

### 4.4 App backend frames (unit 3)

`mountAppBackendFrame` (`src/extensions/mount-app-backend-frame.ts`) resolves the target from the App's owning
backend: a non-local backend is `unsupported-backend`; no bridge capability or no `app_backend_ingress_url` in that
backend's cached `/server_info` is `no-ingress`. It then acquires a lease and appends the frame (`src =
lease.url + path` without its leading `/`, `sandbox` = the server's tokens, `referrerpolicy="no-referrer"`, `title`,
full size, no border). A failure prepends a `<p role="status">` with the localized sentence and calls `onError` once;
a lost session (a failed refresh) adds the notice beside the frame, which stays. The disposer aborts a pending
acquisition and removes frame and notice, then releases the lease. [run: 10 frame tests]

The keeper (`app-backend-session-keeper.ts`) holds one entry per `[backend id, App name]`: a holder count (leases plus
waiting acquisitions), the mint promise, the refresh timer and the lost-listeners. The first acquisition mints; the
entry is forgotten if the mint fails, so the next frame retries. A minted session schedules a refresh at `expires_at −
60 s`, at least 10 s away; a refresh replaces the cookie for every frame of the App. The last release deletes the
entry, clears the timer and revokes once the mint has settled (`:154–170`). After a failed refresh the entry stays,
with no timer: a frame of the same App mounted while another still holds it gets the old session again and no
further refresh [read]. [run: 7 keeper tests, fake timers, the client faked at its boundary]

### 4.5 Where the complexity sits

In the home path of §4.2 (the launch key, the last-answered ref, refusal handling and start values: 56 lines, with
13 tests of their own) and in the keeper's lease counting (§4.4). The panel slot is many small pieces across
the store, the column, the runtime and the tab hook, each simple.

### 4.6 What C2 relies on

- **S2, through `dr-1`.** `cef3b24` is S2 at `6f97bf3` plus S1's five commits (`13f4571`…`0cfb6a2`) and the fork-only
  `cef3b24` (publishing the TypeScript client); S2's later `13e5904` and `5e3317f` are not in it, and differ from
  `6f97bf3` in the agent-server only by the icon route's OpenAPI declaration [run: `git merge-base`, `git diff --stat`
  in the SDK fork]. From the dr-1 client tarball (version string 1.50.1): `ConversationClient.previewAcpSession` and
  `setAcpConfigOption`, `ACP_SESSION_CONTROLS_EVENT_KIND`, the controls types, and
  `CanvasExtensionsClient.createAppBackendSession` / `revokeAppBackendSession` with `appBackendIngressUrl` [run: `tsc`
  through `npm run lint`]. From the agent-server directly: the three capability strings and `app_backend_ingress_url`
  in `/server_info`; `contributes.conversation_panels` in the installed manifest; the icon route needing the session
  key; the preview ignoring `conversation_id`, `worktree` and `initial_message`; `acp_config_options` on the start;
  the set route's 422 carrying the agent's sentence in `detail`; the qualified-kind search (D-1); the
  `ACPConfigOptionRejected` error code; the 5xx body shape (D-2); the bridge's session route and its 503 sentences
  (D-5). S2's transient empty first report reaches C2 as D-4. [CI for what the live tier exercises, §6.3; read for
  the bridge, never run against a server here]
- **C3, through the wiring.** The mock-LLM stack and the desktop app start the agent-server through C3's launcher,
  which installs it from `config/defaults.json` `sources` (`git+…software-agent-sdk@cef3b24`) [read]; the live tier's
  `beforeAll` asserts both capabilities in that server's `/server_info` [CI]. C3's default
  `OH_APP_BACKEND_PUBLIC_URL` (`49db305`) is what gives the npm and desktop launchers an App ingress, without which
  every frame reports `no-ingress` [read].

### 4.7 Who relies on C2, and on what

- **D3, the Decompositions panel** (deep-reasoning `v1-decompositions-panel`, code at `d4e9cd3`; App `dr-library`,
  panel `decompositions`, tabs `browse`, `create`, `namespaces`, `tools`, icon `panel.svg`). It relies on: the
  manifest key and the button ("Show Decompositions"); `registerPage` for its four tab ids; the mount context's
  `conversationId` and `surface.kind === "conversation-panel"` with `selectTab`, through which a frame message switches
  tabs (C2 remounts the new tab, and D3 hands the next mount a focus through a module-level map); `host.agentServer.
  request` within its 60 s for the backend's status and start, the `deep_reasoner` profile and the events search;
  `host.appBackend.mountFrame(container, {path: "/ui/?…", title, onError})`, retrying once on `not-ready`, which C2
  reports only since `70ce577` (D-2); and the frame being the `<iframe>` child of the container (D3 finds it with
  `container.querySelector("iframe")` to match `message` events to its `contentWindow`), which C2 keeps across
  refreshes. D3 types `appBackend` as optional and shows a sentence without it. **D3's namespace read uses the short
  kind and finds nothing at dr-1 (D-1).** D3's as-built records that none of D3 has run inside Canvas; nothing in C2's
  tests runs D3. [read: D3's `canvas-app/src/page/*.ts`; run: the filter probe]
- **D1's dr-acp, through S2.** Its decomposition commands and its `namespace` select reach C2's menu and pills; C2
  relies on the namespace being a `select` not named `model`, on a one-value select meaning "fixed", and on a new
  report replacing the last (dr-acp clears its menu at the first prompt). With dr-acp, D-4's empty first report is
  the expected sequence (S2's as-built D-2). [read]
- **D5's layer 4 (E12)** drives the real desktop app through C2's surfaces with dr-acp; it has not run. [read: design
  §10]
- **S2's as-built §4.8** described C2 at `db3b4b9`; since then C2's own commits are `70ce577` and `86c00b5`, besides
  the wiring merges. [run: `git log db3b4b9..64b5a8b`]

---

## 5 · Wiring

PR #3 is a draft, `feat/agent-surfaces` → `wiring/dr-1`, 12 commits, +6,955 −167 in 89 files, labelled `type: feat`,
mergeable. Its checks at `64b5a8b`: CI's `test-and-build (ubuntu)` (lint, test, build, build:lib, package check) and
`test-and-build (windows)` (app build only; lint and test skipped), `prepare-test-matrix`, `live-e2e` skipped,
`pr-title` (both jobs) green; two `mock-llm-e2e` checks from the two dispatches, the specs-only run green and the full
run red (§6.5). No desktop workflow ran on the PR. [CI] The PR body's "How to Test" reports the runs at `86c00b5`
(CI 37152459103, mock-LLM 37152465164), not at the head. [CI: PR body]

Fork-only and not C2's, but on its path: `ba4d883` at its base; through the wiring, `69d2a6a` (the `dr-1` agent-server
source and client pin), `32bc76e` (the SDK version check reading a tarball pin) and `9881d24` (the `specs` input).
Upstream's product specs gain the panel contract, App backend frames and `CX-001`–`CX-006`
(`specs/canvas-extensions.md`, which also marks Slice 4's "extension tabs/panels" delivered) and a new
`specs/acp-session-controls.md` (`ASC-001`–`ASC-005`); code and tests carry `// @spec` tags. The e2e skill guide and
`test-mapping.json` name the two new specs. [read]

---

## 6 · Tests and runs, as measured

### 6.1 The runs

| Run | Commit | Conditions | Result |
|---|---|---|---|
| CI [37153648487](https://github.com/michaeltheologitis/OpenHands/actions/runs/37153648487) | `64b5a8b` | `pull_request`; ubuntu-24.04 full checks; windows build only; Node 24.15.0, npm 11.12.1 | green. Lint 0 errors, 379 warnings; test **776 files passed, 1 skipped; 8,254 tests passed, 1 skipped, 7 todo** in 650 s; build, build:lib and the package check green. All 26 of C2's test files ran, with the counts of my run [CI] |
| live tier [37153648974](https://github.com/michaeltheologitis/OpenHands/actions/runs/37153648974) | `64b5a8b` | `workflow_dispatch` of `mock-llm-e2e.yml` with `specs` = C2's two spec files; uv 0.12.23; the mock LLM; the mock ACP agent; agent-server from `cef3b24` [read] | **7 passed** (1.8 min), 1 worker [CI] |
| full mock-LLM 37153914745 | `64b5a8b` | the same, `specs` empty: 79 tests | **6 failed**, all upstream specs (§6.5); C2's 7 pass within; teardown hung and was killed (exit 124) after the done marker [CI] |
| full mock-LLM 37149694708 | `ba4d883` (fork `deep-reasoning`, without C2, C3 and the wiring; agent-server from PyPI at `versions.agentServer` [read]) | 72 tests | the **same 6 failed**, same first errors [CI] |
| full mock-LLM 37152465164 | `86c00b5` | 79 tests | 5 failed: the same less `files-and-git` step 2 [CI] |
| this sandbox, C2's 26 test files | `64b5a8b` and `9881d24` | Node 22.22, 4 CPUs, load average 20–30 | head **515 passed**; the same files at the base 377; **C2 adds 138 test cases, all passing** [run] |
| this sandbox, full suite (`npm test`) | `64b5a8b` | the same, beside two other agents' suites; 46 min | **774 files passed, 2 failed, 1 skipped; 8,252 tests passed, 2 failed, 1 skipped, 7 todo** (the same 8,262 as CI). The two failures, `conversation-panel.test.tsx` ("pins the active backend…") and `automations-subpages-absent.test.tsx`, are upstream files C2 does not touch, each a `findBy` that did not find its element; rerun alone, both files pass (70 of 70), and both pass in CI [run] |
| this sandbox, lint, builds, translations | `64b5a8b` | `npm run lint`, `npm run build`, `npm run build:lib`, `check-translation-completeness.cjs` | lint 0 errors, 379 warnings, Prettier clean, `tsc` clean; both builds succeed; every key in every language [run] |

**Lint warnings in C2's lines:** 3 of the 379, all `shadcn/no-arbitrary-values`, in `chat-input-agent-options.tsx`
(`:52` `text-[11px]`, `:163` `z-[60]` and `max-h-[60vh]`); the other warnings in files C2 touched are on upstream's
lines. The `‹hint›` glyph passes lint without an exception (design §11 item 5's second check). [CI: lint log, `git
blame`]

### 6.2 E11, C2's part (design §10)

| E11 claim | In C2, measured | Result |
|---|---|---|
| The home screen's preview lists the namespace's commands | live test 6: with the mock agent as the active ACP profile, the home pill reads `Profile: fast` and `/` lists `/summarize`, not `/compare` [CI]; `useHomeAgentControls` tests [run] | passed with the mock agent; dr-acp's namespaces are not in C2's tests |
| Changing the namespace changes them | live test 6: choosing `thorough` gives `Profile: thorough` and lists `/summarize`, `/compare ‹what to compare›` [CI] | passed |
| The started run uses the chosen namespace | live test 6: the `POST /api/conversations` body has `acp_config_options: {profile: "thorough"}` and the agent's reply reads `MOCK_ACP_E2E_REPLY_OK profile=thorough` [CI]; the start-body tests [run] | passed |
| Commands are gone after the first message | live test 7: in the conversation the pill is fixed at `thorough` and `/` lists neither agent command, before and after a reload [CI]; the replacement test [run] | passed |
| The Decompositions panel mounts with the right conversation | live test 3 with the `demo-panel` App: switching conversation with the panel open remounts it with the other id, and going back shows the first [CI]; `CX-002` tests [run] | passed for the demo App; D3's panel never ran in Canvas |
| It never shares the right side with the drawer | the store's action-sequence table (`CX-001`) [run]; live test 1: opening the drawer closes the panel, opening the panel hides the drawer and closes the overview, and the reverse [CI] | passed |

### 6.3 The live tier

`mock-llm-canvas-extension-panels.spec.ts` (5 tests) needs `canvas_conversation_panels_v1` and installs `demo-panel`
by absolute path through the API (skipped in the Docker config); `mock-llm-acp-session-controls.spec.ts` (2 tests)
needs `acp_session_controls_v1` and saves and activates an ACP profile running the mock agent with
`--session-controls`. In run 37153648974, in order [CI]:

1. The App's button is the last of the header's top-right group, after Show panel, with the icon as an SVG `data:`
   URL; it opens a region named "Demo panel" with `aria-pressed`, mounted as `conversation=<id> path= tab=overview`;
   Show panel closes it; opening it again hides the drawer; the overview closes it and the panel closes the
   overview; the page's `surface.selectTab("details")` remounts with `path=details tab=details`.
2. Unpinning Details from ⋯ survives a reload while the panel itself comes back closed.
3. Switching conversation with the panel open remounts it with the new id; back shows the first.
4. At 800 px the button opens `/conversations/<id>/panel/demo-panel/demo` with the tab mounted; back returns.
5. Disabling the App on the Apps page removes its button and closes its panel.
6. The home screen previews, picks, sends and gets `profile=thorough` (§6.2).
7. The conversation shows the pill fixed and no agent command, before and after a reload.

The reload pass of test 7 does not isolate the REST search: the page also preloads the conversation's newest events,
which here include the controls events. That path is unit-tested only (`useLatestAcpSessionControls`). [read]

### 6.4 The deterministic tests C2 adds (138 cases, 26 files, all passing) [run]

- **Unit 1, 59.** Store: the `CX-001` action table (7 sequences), no panel at start, `hasRightPanelToggled` cleared.
  Local storage: round trip, six malformed shapes, a write keeping another panel's entry. Runtime: tab registration
  in manifest order with paths without `/`, a panel id and an undeclared id fail activation, the refusal without the
  capability keeps the App, disable removes, a manifest change re-activates. Tab hook (5), toggle (8: Cloud, no tab,
  order, open and close with tooltip and `aria-pressed`, narrow window, icon, no icon, icon failure), panel (8: region
  and order, mount context, dispose before remount, conversation change, selected tab closes, ⋯ menu, rejecting mount
  and recovery, `selectTab`), column (2), narrow page (3), Apps card (3), capability helper (5), icon fetch and
  timeout (2).
- **Unit 2, 61, three of them from the fixes.** Service (6: values in the start and an otherwise identical body,
  preview equals start for a profile and an `agent_settings` launch, 120 s timeout, live set, Cloud refused), event search `kind` local and Cloud (2),
  `useLatestAcpSessionControls` (7), `useConversationAgentControls` (8, two of them `86c00b5`'s), `useHomeAgentControls`
  (13, five of them the 400, 429, 501, 502 and 504 cases), slash menu (6), pills (8), home launcher (2), the banner,
  the error code, rendering and transcript export of the event (1 each), `getSdkHttpErrorDetail` (5, one `70ce577`'s).
- **Unit 3, 18.** Keeper (7: one session per App shared by leases, Apps apart, refresh a minute early and stops after
  the last release, the 10 s floor, revoke only at the last release, a failed refresh reaching every lease, an
  abandoned acquisition leaving nothing), frame (10: `src`, `sandbox`, `title`; each of four reasons once with its
  notice, two `no-ingress` cases; a refresh keeping the frame and a failed one adding the notice; two frames sharing
  one session; dispose during a mint; dispose), and the host's frame mounter bound to its App and backend.

Plus the 7 live-tier tests of §6.3. [run: test names diffed between head and base, and the runs]

### 6.5 The full mock-LLM suite: the six failures

In runs 37153914745 (`64b5a8b`) and 37149694708 (`ba4d883`), each with this first error [CI]:

1. `automations/mock-llm-automation.spec.ts:523` step 2: "Expected `<RUNTIME_SERVICES>` block in a system message",
   in both attempts of the spec's own retry.
2. `conversations/mock-llm-conversation.spec.ts:268` step 3: "No successful bash execution after 30000ms".
3. `conversations/mock-llm-image-upload.spec.ts:76`: `toBeVisible()` after 30 s.
4. `files/mock-llm-files-and-git.spec.ts:140` step 2: a 60 s predicate timeout. Passed at `86c00b5`.
5. `onboarding/mock-llm-onboarding-happy-path.spec.ts:70`: a 30 s predicate timeout.
6. `settings/mock-llm-profile-management.spec.ts:285`: `toBeVisible()` after 30 s.

None is in a file C2 touches. The base run had neither C3's launcher nor the dr-1 agent-server, so the six fail with
upstream's agent-server too. Why they fail I did not investigate. [CI; read: the file list]

---

## 7 · What I could not verify

1. **App backend frames against a real agent-server.** Every frame and keeper test fakes the client at its HTTP
   boundary; no test, and nothing I ran, mints a session on a real ingress, loads a frame, refreshes a cookie or
   exercises `SameSite=None; Partitioned` cookies in Chromium or Electron. The bridge's sentences that D-5 depends on
   are read from `cef3b24`.
2. **A live set in a conversation** (`POST …/acp/config-options`): unit-tested only; the live tier's agent fixes its
   option at the first prompt, so it never sets one live.
3. **The REST search path end to end** (§6.3) and the history preload's limit: read.
4. **The drawer's terminal surviving behind an App panel** (design §11 item 5): the test keeps a mocked content
   component mounted; no real terminal session was observed.
5. **Unit isolation** (D-7): I did not cherry-pick the units onto the fork's `main` or run any unit alone.
6. **Mutation testing** (D-9): not run here; Stryker over C2's ~45 changed source files with `related` vitest runs
   would take hours on this machine, and the design gives no time budget for it.
7. **The full mock-LLM suite locally**: not run; the six failures are CI's record, and why they fail is not
   investigated.
8. **D3's consequence of D-1** is read from D3's code and the filter probe; no D3 panel ran against a real
   agent-server.
9. **Electron and Windows**: C2 adds no Electron code; CI builds the app on Windows without running tests.
10. **The capability gate's timing** (§4.2): read only; no test renders before `/server_info` is cached and checks
    that the controls appear afterwards.

If this document resists shortening, the part that resists is §2: the code follows the design closely, and what
differs is spread across the contract D3 reads (D-1, D-2, D-5), the preview's parity (D-3, D-4) and the proof (D-7 to
D-11).
