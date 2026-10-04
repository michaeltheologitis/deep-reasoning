# C2 · App header panels, agent commands and an option picker, as built

**TASK-7** · Cartographer · **r2, 2026-10-04: Gate C's map of the code at `f4c7ae5`**, head of `feat/agent-surfaces` in
the Canvas fork [michaeltheologitis/OpenHands](https://github.com/michaeltheologitis/OpenHands) (draft PR #3 into
`wiring/dr-1` at `9881d24`; C2 is `git diff 9881d24...f4c7ae5`) · checked against the design **v2 at `6e489ea`**
(`docs/design/c2-header-panels-and-menus.md`, which describes `64b5a8b`) · agent-server and TypeScript client from the
SDK fork's tag `dr-1` (`cef3b24`) · Node 22.22 and npm 10.9 in this sandbox, Node 24.15 and npm 11.12 in CI.

**Revisions** (newest first):
- **r2 · 2026-10-04 · `f4c7ae5`.** Since r1's `64b5a8b`: three Gate B fixes (`3912c52`, `6fb7f05`, `61b9bdc`) and 13
  refactor commits (`0e396b9` … `f4c7ae5`). The yardstick changed with them. r1 checked the build against v1. r2 checks
  it against v2, which took in r1's D-1, D-2 and D-4 to D-11. D-12 to D-19 are new; D-3 and four small rows are still
  open from r1 (§2.3). Stop trusting these parts of r1: D-1's consequence for D3 (D3 fixed its search in `436c513`);
  D-2's helper names; §3's error helpers and exported names; §4.2's paragraph on refusals; §4.5's counts; §4.7's C1
  file count; and every number in §6.
- r1 · 2026-10-03 · `64b5a8b`, against v1 at `72aa49f`.

**Where this file lives.** It is on deep-reasoning's branch `as-built/c2-r2`, cut from `design/c2` at `f925698`, and
the Conductor merges it into `design/c2`. The branch holds only documents: no `pyproject.toml`, no docs site and no
test runner. So nothing collects `as_built/`, and there is nothing to wire. [run: `git ls-tree` of this branch]

**Evidence marks.** Every claim carries one.
- **[run]** means executed in this sandbox. Every run used a detached worktree of `f4c7ae5` with its own `npm ci`.
  Comparison worktrees at `61b9bdc`, `64b5a8b` and `9881d24` share that `node_modules`, because `package.json` and
  `package-lock.json` are byte-identical at all four commits. What ran:
  - C2's test files at all four commits;
  - typecheck, `npm run build` and `npm run build:lib` at `f4c7ae5`;
  - `git merge-tree` against C1;
  - ten mutation probes (§6.3), each one edit, reverted, with `git status` empty after it.
- **[CI]** means read from GitHub's records through the GitHub MCP tools, with the full job logs downloaded: CI run
  37174140874 and live run 37174141226, both at `f4c7ae5`.
- **[read]** means read in the code and **not executed**. It is weaker evidence; §8 lists the read claims that matter.

Nothing here ran a paid model, the `claude` CLI or a live test. I made no commit in the Canvas clone.

**Reading order.** §2 first (the divergences), then §6.3 (what the refactor took out of the tests, with probes). Use
§1, §3 and §4 as the map, and §4.6–§4.7 for who C2 relies on and who relies on C2.

---

## 1 · What exists

C2 adds three generic surfaces to Agent Canvas. Each sits behind an agent-server capability, read from the local
backend's cached `/server_info`. No added source line names deep_reasoner, dr-acp or `dr-library`, or reads `_meta`.
[run: grep of the added `src/` lines at `f4c7ae5`]

1. **App header panels** (`canvas_conversation_panels_v1`). An App's `contributes.conversation_panels` gives each
   panel a button after Show panel. The button opens the drawer's column with the App's tab row and a ⋯ menu. The body
   is the selected tab's App page, mounted with the conversation's id. At most one of drawer, App panel and overview is
   open. A narrow window gets a page per panel.
2. **Agent commands and an option picker** (`acp_session_controls_v1`). An ACP agent's slash commands join the slash
   menu. Its select options, except `model`, show as pills above the message input.
   - On the home screen both come from `POST /api/acp/preview`. A refused pick is withdrawn, and the accepted values go
     with the start.
   - In a conversation both come from the newest `ACPSessionControlsEvent`. A pick is set live, and its failure is a
     toast.
3. **App backend frames** (`canvas_app_backend_bridge_v1`). `host.appBackend.mountFrame(container, {path, title,
   onError})` shows the App's own backend in a sandboxed `<iframe>` on the agent-server's App ingress origin. The host
   keeps one refreshed session per App.

```text
App header panel
  manifest.contributes.conversation_panels → activate(host) → host.registerPage(<tab id>, mount)
     → resolveDeclaredContribution → panel-tab | page | panels-unsupported
  header [Git] [Overview] [Show panel] [◇ per panel] → store.openAppPanel("<app>/<panel>")   (narrow: the panel's page)
  column: drawer kept mounted under `hidden`; ConversationAppPanel: tab row + ⋯ (tab state in conversation-state-<id>)
          tab body: useCanvasExtensionMount(mount, {path, navigate, conversationId, surface}), key [conv, panel, tab]

Agent controls
  home:  useHomeAgentControls ─ launch key, picks (session store) ─ useAcpSessionPreview (staleTime: fresh since mount)
           → POST /api/acp/preview (the start's own body + acp_config_options)
           422 → picks withdrawn to the last answered values; other failure → no controls
         send → createConversation(..., acpConfigOptions = the last answered preview's accepted values)
  convo: useConversationAgentControls ─ useLatestAcpSessionControls: newer of (event store's newest, one GET
           …/events/search?kind=<module-qualified>&sort_order=TIMESTAMP_DESC&limit=1)
         pick → useSetAcpConfigOption → POST …/acp/config-options; failure → toast from the mutation's own onError
  both:  CustomChatInput(agentControls) → useSlashCommand({agentCommands}) and ChatInputAgentOptions

App backend frame
  mountFrame → resolveTarget (bridge capability + app_backend_ingress_url) → acquireAppBackendSession
    (one session per backend + App: mint, refresh 60 s before expiry, revoke at the last release)
    → <iframe src="{ingress}/app-backends/{name}/{path}" sandbox=<server's tokens> referrerpolicy=no-referrer>
```

[read; each path is run by the tests of §6.2, and the first two by the live tier, §6.4]

| Commits | What | Code | Unit tests | Other |
|---|---|---|---|---|
| `20b90cb` `1828cec` `a5436be` | unit 1, header panels, with spec text and E2E | +1,224 −87 | +1,391 −8 | E2E +275, fixture +67, i18n +68, spec +81 −1 |
| `4caaecc` `82ff26a` | unit 2, agent controls, with spec text, mock agent and E2E | +957 −53 | +1,349 −3 | E2E +199, harness +142 −12, i18n +51, spec +47 |
| `baddd10` `db3b4b9` | unit 3, backend frames, with spec text | +429 −1 | +478 | i18n +51, spec +38 |
| `70ce577` `86c00b5` | Gate B's fixes before r1 | +35 −10 | +68 −2 | — |
| `3912c52` `6fb7f05` `61b9bdc` | the three Gate B fixes (§2.1 D-12, D-13, D-14) | +48 −12 | +146 −23 | spec +3 −1 |
| `0e396b9` … `f4c7ae5` (13) | the refactor | +62 −107 | +177 −304 | — |

These are per-commit figures [run: `git show --numstat`]. The first four rows are as committed, measured in r1. The net
size at `f4c7ae5`, by kind, is in §7. Not C2's: `ba4d883` (fork-only, byte-identical to C3's file in the wiring) and the
merges `c08ded0` and `64b5a8b`, which bring in `wiring/dr-1` with no hunk of their own (r1, [run]).

---

## 2 · Divergences from the design (v2, `6e489ea`)

The changelog still holds no entry for TASK-7, so there is no `drift:` line. Every item was found from the code
[run: Notion query of the Changelog]. All of `3912c52` … `f4c7ae5` were committed after v2 (2026-10-03 23:20 →
2026-10-04 03:20). "v2 §x" cites `6e489ea`.

### 2.1 Behaviour a user, an App or a collaborator sees

**D-12 · A failed live set toasts upstream's words, from the mutation itself (ruling 3(b)).**
- v2 says: §5.3, §3.2 B3 and the Gate B section's ruling 3 describe option (a) as built, `displayErrorToast(
  getSdkHttpErrorDetail(error) ?? message)` in `mutate`'s `onError`, with (b) recommended.
- Built: the toast is `useSetAcpConfigOption`'s own `onError` (`src/hooks/mutation/use-set-acp-config-option.ts:37–42`).
  - A 422 shows upstream's `getApiErrorMessage(error, error.message)`: the body's `message`, else a string `detail`,
    else the error's text.
  - Any other failure shows upstream's `retrieveAxiosErrorMessage(error)`:
    - for the client's `HttpError` (a 4xx other than 422, or any 5xx), its own `HTTP request failed (<status>
      <text>): <body as JSON>`;
    - for a client timeout, "Disconnected (request timed out). …";
    - for a lost connection, "Disconnected (check URL or network). …".
  - `useConversationAgentControls` calls `mutate` with no callbacks (`src/hooks/chat/use-agent-controls.ts:138–139`),
    so the toast still fires after the composer unmounts.
- Reasons: `3912c52` (ruling 3(b)); `4ff261c` ("completes ruling 3(b) as approved": a 400 or 404 with a string
  `detail` had toasted that `detail`); `3461e1c` ("React Query drops mutate-scoped callbacks once the calling component
  unmounts").
- Evidence: [run: `use-agent-controls.test.tsx › useConversationAgentControls › reports a failed pick that is not a
  refusal as upstream does, for %s` (a 504, a 400, a 404, a client timeout, a lost connection), `› shows the agent's
  own sentence when it refuses a pick` and `› still reports a failed pick when the composer unmounts before the agent
  answers`; probes P6b and P7, §6.3]. Unit tests only: no live test sets an option in a conversation [read].

**D-13 · On the home screen a refused pick is withdrawn.**
- v2 says, in §5.4: "a 422 keeps the last successful preview's controls, shows the agent's sentence … and the refused
  value is not sent". §5.6 has a pick call `controls.setOption`; ASC-002 (§5.8) is one sentence. r1 §4.2 recorded the
  old build: the refused value stayed in the store, and picking it again asked nothing.
- Built (`use-agent-controls.ts:187–227`; `src/stores/home-agent-options-store.ts:15, 36`):
  - On a 422, an effect (`:201–207`) replaces the stored picks. They become the values of the preview the agent last
    answered for this launch key, or none if it has answered nothing. The key then returns to that answer, which is
    cached, so nothing new is asked (D-14).
  - The agent's sentence is kept in a ref. It shows while controls are shown (`:218–221`) and clears on the next pick
    (`:223–226`) or on another launch key. With no earlier answer, it appears once the agent's default preview
    answers.
  - Picking the refused value again moves the key to the failed query, which has no data, so the agent is asked again.
  - Choosing the value in effect still sends nothing (`chat-input-agent-options.tsx:169`).
  - A failure that is not a 422 withdraws nothing. The pick stays in the store and the controls hide; the next preview
    (after a workspace change, or a return to the home screen) carries the pick [read].
- `specs/acp-session-controls.md:21–25`, ASC-002, gains: "A refused pick is withdrawn: the picker shows the agent's
  value again, and picking the refused value again asks the agent again."
- Reasons: `6fb7f05` lists four faults of the old behaviour; `61b9bdc` makes its test wait for the withdrawal, which
  runs in an effect after the render that shows the sentence.
- Evidence: [run: `use-acp-session-preview.test.tsx › useHomeAgentControls › returns the picks to the last accepted
  values when the agent refuses one, without asking again, and says why`, `› returns refused picks to the agent's
  defaults when the home screen has no answer yet`, `› asks the agent again when the value it refused is picked again`;
  `chat-input-agent-options.test.tsx › ChatInputAgentOptions › sets nothing when the value in effect is chosen`; probe
  P8]. Unit tests only: no live test reaches a refusal [read].

**D-14 · A preview's answer stays current until the home screen unmounts.**
- v2 says: §5.4, and the options under A.10, give `staleTime: 0`.
- Built (`src/hooks/query/use-acp-session-preview.ts:74, 95–96`):
  - `staleTime` is `Infinity` for data fetched since this hook mounted, and `0` for older data.
  - Going back to inputs the agent answered during the visit asks nothing. That covers D-13's withdrawal; it also
    covers re-picking `fast` after `thorough` [read].
  - A remount, such as a return to the home screen, asks again, as v2 says.
- Reason: `6fb7f05`, "so that the withdrawal does not start the agent again for values it has just answered".
- Evidence: [run: `› asks the agent again when the home screen returns`; probes P9a and P9b].

**D-15 · Upstream's error helpers replace C2's three.**
- v2 says: §5.1, A.7, §3.2 B2 and decision M give `getSdkHttpErrorDetail` (null for a 5xx) and
  `getSdkHttpServerErrorReason` in `agent-server-compatibility.ts`.
- Built:
  - Neither helper exists. C2's addition to that file is `AgentServerCapability` and `localAgentServerHasCapability`
    only (`src/api/agent-server-compatibility.ts:159–175`).
  - Both refusal sites read a 422 with upstream's `getApiErrorMessage` (`src/utils/api-error-message.ts:24–38`).
  - The session keeper reads a 503's `exception` through upstream's `getApiErrorBody`
    (`src/extensions/app-backend-session-keeper.ts:74–88`).
- What this changes: "a 5xx's placeholder is never the agent's sentence" now rests on each site's 422 check, not on a
  helper. On the live set that check is pinned (P6b). On the home screen nothing pins it, and has not since `6fb7f05`
  (P6, §6.3).
- Reason: `4ff261c`.
- Evidence: [run: the frame tests' `not-ready` and `no-ingress` rows; read: upstream's helpers]. C1's as-built §2.1
  D-1 cites `getSdkHttpServerErrorReason` at `:235` of this branch, a line that no longer exists (§4.7).

**D-16 · The controls event guard is the client's, and C2 no longer touches `type-guards.ts`.**
- v2 says: §5.2, A.8, §8 item 1's v2 note ("which Canvas declares in its own `type-guards.ts`") and §9's first row.
- Built: `useLatestAcpSessionControls` imports the `dr-1` client's `isACPSessionControlsEvent`
  (`src/hooks/query/use-latest-acp-session-controls.ts:4, 17`).
  - It checks `event.kind === 'ACPSessionControlsEvent'`, as C2's guard did [read: the installed tarball's
    `dist/events/types.js:60–62`].
  - The call site keeps `"kind" in event`, because Canvas's event union holds a message event without `kind`.
  - C2's diff leaves `src/types/agent-server/type-guards.ts` untouched. C1 and C2 now share 8 files, not 9 (§4.7).
- Reason: `0e396b9`.
- Evidence: [run: the latest-controls tests; `git merge-tree`].

### 2.2 Signatures, tests and size

**D-17 · Names no longer exported, or gone** (`258944e`, `01411cd`, `501f0c6`; their messages give the reasons: "read
only in their own modules", "neither reader used it"). [read; run: typecheck and both builds pass]

| v2 | Built |
|---|---|
| A.10 `export const ACP_CONFIG_OPTION_REJECTED_CODE` | gone; the header map's entry is the literal `ACPConfigOptionRejected` (`src/utils/acp-error-codes.ts:12`), C2's only line in that file |
| A.10 `export declare function toAgentSlashCommandItem` (and §5.5) | module-private (`src/hooks/chat/use-slash-command.ts:29`) |
| A.9 `export interface LocalStartConversationRequest {payload, conversationId, resolvedWorkspaceMode}`; §5.2: the builder "returns the body, the new id and the resolved workspace mode" | module-private, `{payload, resolvedWorkspaceMode}` (`agent-server-conversation-service.api.ts:429–433`); the id travels in the body as `conversation_id` |
| A.2 `export const CANVAS_EXTENSION_AGENT_SERVER_REQUEST_TIMEOUT_MS`; B8: "documented … in upstream's spec" | module-private (`src/api/canvas-extensions-service.ts:23`); `specs/canvas-extensions.md:124` still names it as the source of `host.agentServer.request`'s 60 s |
| A.10 `useLatestAcpSessionControls(conversationId, enabled)`, no rule for disabled | `enabled` gates the event-store selector and the query (`:35`, `:57`) but not the return: while disabled it can return a search cached earlier under the same key. Its one caller returns `NO_AGENT_CONTROLS` first (`use-agent-controls.ts:130`) [read] |
| A.10 `HomeAgentOptionsState {launchKey, values, setValue}` | adds `setValues(launchKey, values)` (`home-agent-options-store.ts:15, 36`), for D-13 |

**D-18 · v2's test tables name seven tests that no longer exist, and miss three unpinned properties.**
- v2 says: its Gate B tables, and §3.2 B17 with 109 vitest definitions (11 of them `it.each`) in 26 files.
- Built: 108 definitions (11 `it.each`) in 25 files that carry C2 lines, plus two shared helpers
  (`__tests__/helpers/canvas-extension-panels.tsx`, and the new `__tests__/helpers/query-wrapper.tsx`). That is 138
  cases, all passing (§6.2) [run].
- Gone from v2's tables:
  - `getSdkHttpErrorDetail › …` (5 cases);
  - `never shows a 5xx answer's placeholder detail as the agent's sentence`, now the 504 row of D-12's table;
  - `keeps the last accepted controls and start values when the agent refuses a pick, and says why`, now D-13's first
    test;
  - `issues no search and reads nothing while disabled`;
  - `maps a refused start-time option value to its own header`;
  - `gives an App's agent-server requests a minute, more than an App backend start takes`;
  - `keeps one session for two frames of the App and revokes it when the last one closes`.
- New: D-12's and D-13's tests.
- v2's "Not pinned by any test" paragraph lacks three properties that §6.3's probes leave unpinned:
  - two frames of one App share one session through `mountAppBackendFrame` (CX-005 is now pinned only at the keeper);
  - a home-screen preview failure that is not a 422 is never shown as the agent's sentence;
  - a disabled latest-controls hook does not scan the event store.

**D-19 · Size after the fixes and the refactor.**
- v2 says: §3.2 B20 and ruling 1 give 6,955 lines added and 167 removed, in 89 files.
- Built: 6,944 added and 167 removed, in 88 files (§7) [run].

### 2.3 Still open from r1: what v2 does not record

- **r1's D-3 · The preview's body is not the start's less `initial_message` and `user_id`.**
  - v2 §5.2, decision I and the parity test's name still say it is.
  - Built: the builder mints a fresh `conversation_id` per call (`agent-server-conversation-service.api.ts:455–510`,
    `uuidv4()` at `:479`). Without a workspace it also derives a different `working_dir` from that id.
  - Evidence: [read at `f4c7ae5`: unchanged but for its return value; run in r1 at `64b5a8b`].
- **Four of r1's small rows:**
  - §4.1 says the route page's mount effect "moves unchanged" into `useCanvasExtensionMount`. Built, it remounts on
    `mount` or path changes, not on a change of `page` or `navigate`.
  - Decision L applies to the whole menu, so two skills with the same slash trigger, both listed before C2, now list
    once (`use-slash-command.ts:47–55, 110, 126`).
  - §5.6 calls a fixed pill "a select with one value". Built, the test is `options.length < 2`, so a select with none
    is fixed too (`chat-input-agent-options.tsx:111`).
  - A.2's `createAppBackendSession(…, signal?)` is never passed a signal. The keeper races the mint against the abort
    instead (`app-backend-session-keeper.ts:189–201`).
  - Evidence: [read].

**Recorded in v2 since r1:**

| r1 divergence | Where v2 records it |
|---|---|
| D-1 | B1; D3 itself now searches with the qualified kind, §4.7 |
| D-2 | B2; its mechanism changed again, D-15 |
| D-4 | B4 |
| D-5 | B13 |
| D-6 | B6 |
| D-7 | the Gate B section, B16 |
| D-8 | the Gate B section, B19 |
| D-9 | B18 |
| D-10 | B20 |
| D-11 | B17 |
| r1 §2.2's other rows | B7, B8, B10, B11, B12, B14 and B15 |

**Not divergences.** These hold as v2 describes them, unchanged since r1 [run for behaviours §6.2's tests name; read
for the rest]:
- decisions A–N;
- §4's panel slot, store actions, tab rules and narrow page;
- §5.5's menu;
- §6's frame and keeper;
- Appendix B's ten keys, each in 15 languages.

---

## 3 · The public surface, from the code

**App manifest and host API** (`src/types/canvas-extension.ts`, re-exported from `src/lib/index.ts`; host API still
version `"1"`), unchanged since r1:
- `contributes.conversation_panels: [{id, title, icon?, tabs: [{id, title, path}]}]`.
- Every mount context gains `conversationId: string | null` and a `surface`:
  - `{kind: "page"}` on a routed page;
  - `{kind: "conversation-panel", panelId, tabId, selectTab(tabId)}` in a panel, whose `path` is the tab's path
    without its leading `/` (`""` for `/`).
- `host.appBackend.mountFrame(container, {path?, title, onError?}) → dispose`:
  - `onError({reason: "no-ingress" | "not-ready" | "session-refused" | "unsupported-backend", message})` is called at
    most once;
  - the frame is the `<iframe>` appended to the container, and it stays there, across refreshes, until disposed.
- `host.agentServer.request` takes up to 60 s (`canvas-extension.ts:162`).
- `registerPage` throws, failing activation, for a panel's own id, an undeclared id or an id registered twice. On an
  agent-server without `canvas_conversation_panels_v1`, an undeclared id returns a no-op disposer and sets the App's
  notice instead.

[run: runtime and frame tests]

**Routes and state**, unchanged since r1:
- `/conversations/:conversationId/panel/:extensionName/:panelId` is the narrow-window page.
- `useConversationStore` gains `activeAppPanel`, `openAppPanel(key)` and `closeAppPanel()`. `setIsRightPanelShown(true)`
  and `setIsOverviewPanelShown(true)` also clear `activeAppPanel` (`conversation-store.ts:169–189, 423–437`).
- `useHomeAgentOptionsStore` gains `setValues` (D-13).
- The `conversation-state-<id>` blob gains `appPanelTabs`, which is sanitized on every read.

[run]

**Services:**
- `CanvasExtensionsService`:
  - `fetchPanelIcon(name, panelId, backend?) → Blob`;
  - `createAppBackendSession(name, backend, ingressUrl, signal?)`;
  - `revokeAppBackendSession(name, backend, ingressUrl)`, which logs errors and never throws.
- `AgentServerConversationService`, both refusing a Cloud backend:
  - `previewAcpSession({workingDirOverride?, workspaceMode?, agentProfileId?, agentProfileKind?, acpConfigOptions}) →
    ACPSessionControls`, with a 120 s timeout;
  - `setAcpConfigOption(conversationId, configId, value)`.
- `createConversation` and `useCreateConversation` accept `acpConfigOptions`, sent only when non-empty.
- `EventSearchOptions.kind`.
- `agent-server-compatibility.ts` adds only `AgentServerCapability` and `localAgentServerHasCapability` (D-15).

[run]

**Hooks and components:**
- `useConversationAgentControls(conversationId)`, `useHomeAgentControls({workingDir, workspaceMode})` and
  `NO_AGENT_CONTROLS`;
- `useLatestAcpSessionControls`, `useAcpSessionPreview`, `resolveAcpLaunchProfile`, `useSetAcpConfigOption` (which
  owns its toast) and `useHomeAgentOptionsStore`;
- `useSlashCommand(ref, {agentCommands})`;
- `ChatInputAgentOptions`;
- the panel components under `components/features/conversation/`;
- `useCanvasExtensionMount`.

The refactor un-exported `toAgentSlashCommandItem`, `LocalStartConversationRequest` and the timeout constant (D-17).
[read; run: typecheck]

**What the user sees**, as r1 described it, with two changes:
- in a conversation, a failed pick toasts D-12's words;
- on the home screen, a refusal returns the pill to the agent's last accepted value, with the sentence under the pills
  until the next pick (D-13).

[run: component and hook tests; CI: the live tier for header, panel, pills and menu]

**Requests Canvas makes for C2**, unchanged since r1:

| Request | When | Evidence |
|---|---|---|
| `GET /api/canvas-extensions/installed/{name}/panels/{panel_id}/icon` (session key) | a panel declares an icon | [CI] |
| `POST /api/acp/preview` | home screen, ACP launch agent, capability present; for each set of inputs not answered since the home screen mounted (D-14); never on focus; no retry | [CI; run] |
| `POST /api/conversations` + `acp_config_options` | a home start with accepted values | [CI] |
| `GET /api/conversations/{id}/events/search?kind=<qualified>&sort_order=TIMESTAMP_DESC&limit=1` | once per backend and conversation (`staleTime: Infinity`), ACP conversation, capability present | [run: unit; CI: the reload pass, §6.4] |
| `POST /api/conversations/{id}/acp/config-options` | a pick in a conversation | [run: unit only] |
| `POST` / `DELETE {ingress}/app-backends/{name}/session` | first frame of an App; refresh 60 s before expiry (not sooner than 10 s); last frame closed | [run: unit, the client faked at its boundary] |

---

## 4 · Structure and seams

### 4.1 The panel slot (unit 1)

The panel slot is unchanged since r1 except for the comments in `301f960` [run: `git diff 64b5a8b f4c7ae5` touches only
comments in these files].
- **Registration:** `resolveDeclaredContribution` (`canvas-extensions-runtime.tsx:157–183`). Tabs are published after
  `activate` returns. `panels` is derived in a `useMemo` from the enabled Apps and their registered tabs, so a panel
  with no registered tab does not exist.
- **One column:** `isRightColumnOpen = isRightPanelShown || appPanel !== null` (`conversation-main.tsx:32–34`). The
  drawer stays mounted under `hidden`. The store's four actions are the only writers of the three open-flags.
- **Tab state:** `use-conversation-app-panel-tabs.ts`, written through `setAppPanelTabState`
  (`conversation-local-storage.ts:487–494`). It re-reads the blob, so a write keeps other panels' entries.
- **Mount lifecycle:** `useCanvasExtensionMount`, keyed `[conversationId, panel key, tab id]`. A change of key disposes
  first, then empties the container and mounts. A mount that throws shows the unavailable state and keeps the
  container.

[run: store, main, runtime, tab-hook and panel tests; CI: live tests 1–5]

### 4.2 Agent controls (unit 2; most of the complexity sits here)

**The gate** (`use-agent-controls.ts:75–79`) requires an ACP context, a local backend, and the capability in the cached
`/server_info`. The capability is read from a module-level cache at render time, and nothing subscribes to it. [read]

**In a conversation** (`:116–141`, `use-latest-acp-session-controls.ts`), there are two sources:
- a selector that scans the event store from the end, only while enabled and while the store holds this conversation
  (`:34–38`);
- one REST search by the module-qualified kind (`:39–61`), cached for the session and not retried.

The newer by ISO timestamp wins, and the live one wins a tie; nothing is merged (`:63–64`). The options shown are the
selects except `model`. A pick calls `useSetAcpConfigOption`, which carries `meta: {disableToast: true}` and its own
`onError` (D-12); the pill shows the value with a spinner while the set is pending. On success nothing happens: the
next event replaces the controls. [run]

**On the home screen** (`:156–229`, `use-acp-session-preview.ts`, `home-agent-options-store.ts`):
- The launch agent is the active agent profile, else `agent_settings`. Its key is `<backend>:<org>:<profile or
  "agent-settings">`.
- Picks live in a session store under that key; picks under another key are ignored.
- The preview query is keyed by launch key, workspace, workspace mode (only with a workspace) and picks. It keeps the
  previous data while a new key loads, follows D-14's `staleTime`, never refetches on focus and never retries.
- Two refs hold the last preview the agent answered for this launch key (`:172–185`) and the last refusal's sentence
  (`:193–199`). Both are written during render.
- What is shown:
  - the last answered preview, unless the newest preview failed with anything but a 422, which shows nothing (`:210`);
  - after a 422, the effect at `:205–207` withdraws the pick (D-13).
- `startValues` are the shown preview's accepted values, restricted to ids it reported and, for a select, to values it
  listed (`acceptedValues`, `:81–95`, ASC-002). `HomeChatLauncher` sends them only when non-empty
  (`home-chat-launcher.tsx:151–152`).

[run]

**The slash menu** (`use-slash-command.ts:102–127`) lists the built-ins, then the agent's commands, then skills, and
drops any repeated command after its first appearance. **The pill row** renders in `ChatInputContainer` only when there
are options or a refusal (`chat-input-container.tsx:89`; `chat-input-agent-options.tsx:188`). [run]

### 4.3 The start body and the preview

`buildLocalStartConversationRequest` (`agent-server-conversation-service.api.ts:455–510`) builds the start body less
`user_id` and `acp_config_options`, and returns `{payload, resolvedWorkspaceMode}`. Its callers are:
- `createConversation` (`:608–618`), which adds `acp_config_options` when non-empty, then `user_id`;
- `previewAcpSession` (`:661–676`), which adds `acp_config_options` and posts to the client's `previewAcpSession`.

The start's body without values is byte-identical to the body before C2; a test compares the JSON. [run; §2.3 r1's D-3
for what differs from the preview]

### 4.4 App backend frames (unit 3)

`mountAppBackendFrame` (`src/extensions/mount-app-backend-frame.ts`) is unchanged since r1.
- A non-local backend is `unsupported-backend`. A missing bridge capability or `app_backend_ingress_url` is
  `no-ingress`.
- It acquires a lease, then appends the frame. A failure prepends a `<p role="status">` and calls `onError` once.
- A lost session adds the notice beside the frame, which stays.
- The disposer aborts, removes frame and notice, and releases.

The keeper (`app-backend-session-keeper.ts`) holds one entry per `[backend id, App name]`:
- The first acquisition mints, and a failed mint is forgotten so the next frame retries.
- It refreshes at `expires_at − 60 s`, at least 10 s away (`:105–130`).
- The last release deletes the entry and revokes once the mint has settled (`:156–172`).
- `release` is idempotent per lease (`:208–213`).
- `toAppBackendError` (`:70–88`) maps a 503 whose `exception` says "not ready" to `not-ready`, one naming the ingress to
  `no-ingress`, and anything else to `session-refused`.

[run: 7 keeper and 9 frame tests, fake timers, the client faked at its boundary]

### 4.5 Where the complexity sits

- **The home path of §4.2:** 74 lines (`use-agent-controls.ts:156–229`) with 16 tests of their own. It has two refs
  written during render and one effect. The withdrawal depends on D-14's `staleTime` rule not to ask again: probe P9b
  makes both fail together.
- **The keeper's lease counting** (§4.4).

The panel slot is many small pieces, each simple.

### 4.6 What C2 relies on

- **S2, through `dr-1`.** The annotated tag `dr-1` (`8de2887`) still names `cef3b24` [run: `git ls-remote`]. From the
  `dr-1` client tarball (version string 1.50.1), C2 uses:
  - `ConversationClient.previewAcpSession` and `setAcpConfigOption`;
  - `ACP_SESSION_CONTROLS_EVENT_KIND` and, since D-16, `isACPSessionControlsEvent`;
  - the controls types;
  - `CanvasExtensionsClient` with `appBackendIngressUrl`;
  - `HttpError`, in the tests.

  From the agent-server, C2 relies on: the three capability strings and `app_backend_ingress_url` in `/server_info`;
  `contributes.conversation_panels`; the icon route; the preview ignoring `conversation_id` and `initial_message`;
  `acp_config_options` on the start; the set route's 422 sentence in `detail`; the qualified-kind search; the
  `ACPConfigOptionRejected` error code; the 5xx `{detail, exception}` shape; and the bridge's session route with its
  503 sentences.

  S2 merged into the SDK fork's `deep-reasoning` on 2026-10-04 (changelog). `cef3b24` is not in that branch's history.
  In the files C2's contract touches, the branch differs from `cef3b24` mostly by S1's absence (its events and cancel
  route) and by formatting [read: `git diff --stat`, and the diffs of `acp_router.py` and `event_service.py` skimmed].
  Nothing here ran C2 against it. [CI for what the live tier exercises; read for the bridge]
- **C3, through the wiring.** `wiring/dr-1` (`9881d24`) carries C3 at `22272d9`. C3's branch is now at `61d9217`, 12
  commits further, and those commits are not in the wiring. C2 uses two things from C3, and both are present at both
  commits [read]:
  - `config/defaults.json`'s `sources.agentServerGitRepo` and `agentServerGitRef` (`cef3b24`), from which the launcher
    installs the agent-server for the stack the live tier runs;
  - the default `OH_APP_BACKEND_PUBLIC_URL` (`49db305`, `scripts/dev-safe.mjs:885–886`), without which every frame
    reports `no-ingress`.

  The task row holds the PR split until C3 merges and `wiring/dr-1` follows it [read: TASK-7].

### 4.7 Who relies on C2, and on what

- **D3, the Decompositions panel** (deep-reasoning `v1-decompositions-panel` at `897cb44`). D3 relies on:
  - the manifest key and the button;
  - `registerPage` for its four tab ids;
  - `conversationId`, and `surface.selectTab`, which D3 calls on a frame message (`canvas-app/src/page/mount.ts:80–82`);
  - `host.agentServer.request` within its 60 s, for the backend's status and start; the 60 s is still pinned (P1);
  - `host.appBackend.mountFrame(container, {path: "/ui/…", title, onError})`, retrying once on `not-ready`
    (`:86–90`);
  - the frame being the container's `<iframe>` child (`:71`), which C2 keeps across refreshes. D3 empties the container
    before each mount; C2 appends the frame and prepends any notice.

  Since `436c513` (2026-10-03 22:57), D3's `readConversationNamespace` searches with the module-qualified kind
  (`canvas-app/src/page/context.ts:20–32`), so r1's D-1 consequence for D3 no longer holds. Nothing in C2's tests runs
  D3, and D3 has not run inside Canvas. [read: D3's `canvas-app/src/page/*.ts`]
- **C1** (`feat/acp-subagent-sessions` at `9d75806`) shares 8 files with C2 over `wiring/dr-1`: `events/index.ts`,
  `openhands-event.ts`, `translation.json`, `event-service.api.ts` and its test, `should-render-event.test.ts`,
  `transcript-export/index.test.ts` and the e2e guide. `type-guards.ts` is no longer one of them (D-16).
  - An in-memory merge of `9d75806` with `f4c7ae5` conflicts in one hunk: both branches' new export line at the top of
    `events/index.ts` (`./acp-subagent-event` and `./acp-session-controls-event`). The other seven files merge cleanly.
    [run: `git merge-tree`]
  - **The shared 5xx-reason rule** that C1's as-built §2.1 D-1 names is now C2's in one place only: `toAppBackendError`
    (`:74–88`), reading `exception` through upstream's `getApiErrorBody`. It matches the reason by regular expression
    to classify a 503 and shows it to no user. C1's `refusalReason` strips the `NNN: ` prefix and shows the reason in
    a toast. The two remain separate implementations. [read]
- **D1's dr-acp, through S2.** Its commands and its `namespace` select reach C2's menu and pills. C2 relies on the
  namespace being a `select` not named `model`, on a single value meaning "fixed", and on a new report replacing the
  last. [read]
- **D5's E12** drives the real desktop app through C2's surfaces. It has not run. [read]

---

## 5 · The pull request

PR #3 is a draft, `feat/agent-surfaces` → `wiring/dr-1`, labelled `type: feat`, with mergeable state clean. It has 28
commits: C2's 25, `ba4d883` and the two wiring merges. The diff is +6,944 −167 in 88 files.

Every check at `f4c7ae5` is green:
- `test-and-build (ubuntu)`;
- `test-and-build (windows)`, which builds the app only;
- `prepare-test-matrix`;
- both `pr-title` jobs;
- one `mock-llm-e2e`, the specs-only dispatch;
- `live-e2e`, skipped.

No full mock-LLM run exists at this head. The description's "How to Test" still reports the runs at `86c00b5`, and its
summary predates D-12 and D-13. [CI]

---

## 6 · Tests and runs, as measured

### 6.1 The runs

| Run | Commit | Conditions | Result |
|---|---|---|---|
| CI [37174140874](https://github.com/michaeltheologitis/OpenHands/actions/runs/37174140874) | `f4c7ae5` | `pull_request`; ubuntu-24.04 full checks; windows build only; Node 24.15.0, npm 11.12.1 | green. Lint 0 errors, 379 warnings. Test: **776 files passed, 1 skipped; 8,254 tests passed, 1 skipped, 7 todo** in 366 s. Build, build:lib and the package check green. C2's 26 files ran, each with my count [CI] |
| live tier [37174141226](https://github.com/michaeltheologitis/OpenHands/actions/runs/37174141226) | `f4c7ae5` | `workflow_dispatch` of `mock-llm-e2e.yml` with `specs` = C2's two spec files; the mock LLM; the mock ACP agent; uv 0.12.23 | **7 passed** (1.6 min; the job 2 min 54 s), 1 worker [CI] |
| full mock-LLM suite | — | none at `f4c7ae5`. r1's record at `64b5a8b` (37153914745): 6 upstream failures, the same 6 as at `ba4d883` without C2 | not re-run [CI, r1] |
| this sandbox, r1's 26 test files | `f4c7ae5`, `61b9bdc`, `64b5a8b`, `9881d24` | Node 22.22, 4 CPUs, load average 5–10 | **515**, 521, 515 passed; the 15 that exist at the base, 377. No failure at any commit [run] |
| this sandbox, typecheck and builds | `f4c7ae5` | `npm run typecheck`, `npm run build`, `npm run build:lib` | all succeed (83 s, 26 s, 58 s). ESLint and Prettier were not run here; CI's lint is green [run; CI] |

**Lint warnings in C2's lines** are 3 of the 379, as in r1: `shadcn/no-arbitrary-values` in
`chat-input-agent-options.tsx` (`:52`, and `:163` twice). The other seven warnings in files C2 touches fall on lines
from before C2. [CI: lint log; run: `git blame`]

### 6.2 The deterministic tests C2 adds

There are **138 cases in r1's 26 files, all passing** (515 at head, less the base's 377). They come from **108
definitions**, 11 of them `it.each`. `acp-error-codes.test.ts` no longer carries a C2 line, so 25 files hold C2's
tests. [run]
- **Unit 1: 58.** Store (9: `CX-001`'s 7 sequences, start state, `hasRightPanelToggled`); local storage (8); runtime
  (6); tab hook (5); toggle (8); panel (8); column (2); narrow page (3); Apps card (3); capability helper (5); icon
  fetch (1).
- **Unit 2: 63.** Service (6); event search `kind` (2); latest controls (6); conversation controls (13); home controls
  (16); slash menu (5 hook, 1 menu); pills (9); home launcher (2); banner, rendering and transcript export of the event
  (1 each).
- **Unit 3: 17.** Keeper (7); frame (9); the host's frame mounter (1).

Since r1, by name [run: test names diffed between `64b5a8b`, `61b9bdc` and `f4c7ae5`]:
- The Gate B fixes replaced 2 tests and added 6, a net of +6:
  - D-12's 504 row replaced `never shows a 5xx answer's placeholder detail…`, and the timeout and lost-connection rows
    joined it;
  - D-13's first test replaced `keeps the last accepted controls…`, and three home tests and the pills' `sets nothing
    when the value in effect is chosen` joined it.
- The refactor removed 9 (§6.3) and added 3: D-12's 400 and 404 rows and its unmount test.

Two `it.each` tables print duplicate titles. Three sanitizer rows each read `sanitizes a stored { 'demo/panel':
[Object] }`, and two `CX-001` sequences share `keeps one right-hand panel after open drawer then open panel A`. A report
shows 135 distinct names for the 138 cases. [run]

Every vitest file fakes services at their boundary (the client, `EventService`, `AgentServerConversationService`). The
refactor's `8708eae` makes the tests throw the client's own `HttpError` class, so D-12's toast assertions read the
client's real message format. [read]

### 6.3 What the refactor removed from test coverage, with probes

**Method.** Each probe makes one temporary replacement in the `f4c7ae5` copy and runs the named test files, or all 26.
Then `git checkout` restores the file and `git status --porcelain` is empty. Probes P1–P6 test the nine cut tests;
P6b–P9b test the fixes' own tests. [run]

| Cut test (`9c49036`, `4ff261c`) | Where its property stands | Probe | Result |
|---|---|---|---|
| `getSdkHttpErrorDetail › reads the agent-server's detail sentence…` | the helper is gone; a 422's sentence is pinned at both refusal sites (D-12, D-13 tests) | — | — |
| `› is null for a validation error list` | no test. `getApiErrorMessage` falls back to the error's text for a non-string `detail`, as the helper's fallback did [read] | — | — |
| `› is null for a body without detail`, `› … not an SDK HTTP error` | the set's table pins non-HTTP failures (timeout, lost connection) | — | — |
| `› is null for a 5xx answer…` | the live set: pinned by its 504 row | **P6b**: any HTTP status counts as a refusal in `useSetAcpConfigOption` | **killed** by the 504, 400 and 404 rows |
| (same) | the home screen: **not pinned** | **P6**: the same edit in `useHomeAgentControls` (`:190`) | **survived** all 26 files. The same edit is **killed** at `64b5a8b` by the five `… when the preview answers %i` rows, and **survives** at `61b9bdc`. `6fb7f05`'s `rejection` shows only beside shown controls, and those rows have no earlier answer. With the edit, a 504 after an answered preview would show "Internal Server Error" as the agent's sentence and withdraw the pick |
| `useLatestAcpSessionControls › issues no search and reads nothing while disabled`: the search half | pinned by `useConversationAgentControls › has no controls, and searches nothing, for %s` | **P3**: the query ignores `enabled` | **killed** in all 3 rows |
| (same): the scan half | **not pinned**; not observable through the one caller | **P2**: the selector ignores `enabled` | **survived** all 26. The cost is a scan of the whole event store on every store update in every non-ACP conversation (`501f0c6`'s message) [read] |
| `acp-error-codes › maps a refused start-time option value to its own header` | pinned by the banner test | **P4**: rename the map's key | **killed** by `heads a refused start-time option with its title…` |
| `CanvasExtensionsService › gives an App's agent-server requests a minute…` | pinned by upstream's `fetches the bundle as authenticated text…`, which asserts `timeout: 60000` on the client builder `requestAgentServer` shares (`canvas-extensions-service.ts:75–87, 256`) | **P1**: the constant 60 000 → 5 000 | **killed** by that upstream test |
| `mountAppBackendFrame › keeps one session for two frames of the App…` | **not pinned** through the frame; the keeper's tests pin sharing for direct leases | **P5**: `resolveTarget` gives each frame its own backend id | **survived** all 26. The same edit is **killed** at `61b9bdc` by the cut test |

| Fix's own test | Probe | Result |
|---|---|---|
| D-12, `3461e1c`'s unmount test | **P7**: the toast moves back to `mutate`'s callbacks | **killed** by `still reports a failed pick when the composer unmounts…` only |
| D-13, the withdrawal | **P8**: the effect never withdraws | **killed** by D-13's three home tests |
| D-14, `staleTime` | **P9a** `Infinity` / **P9b** `0` | **killed** by `asks the agent again when the home screen returns` / by D-13's first and third tests |

The refactor also rewrote tests without cutting them [read]:
- three shared helpers (`createQueryWrapper`, `demoPageShows`, `renderToggles`);
- the toggle-order test reads every rendered button instead of buttons inside a wrapper;
- the repeat-dropping slash test now names which copy survives (`f4c7ae5`).

### 6.4 The live tier

The two spec files and the mock agent are unchanged since r1 [run: `git diff 64b5a8b f4c7ae5 -- tests/e2e` is empty].
In run 37174141226 the seven tests ran in order [CI]:
1. the button follows Show panel and opens one right-hand panel;
2. an unpinned tab survives a reload while the panel starts closed;
3. switching conversation remounts the panel;
4. the narrow window's page;
5. disabling the App;
6. the home preview, a pick, and `profile=thorough` reaching the agent;
7. the started conversation's fixed pill and no agent commands, after a reload too.

None of the seven reaches a refusal, the refusal line, a toast or a live set. The mock agent can refuse
(`mock-acp-server.py:123–127`), but no spec picks a value it refuses. D-12, D-13 and D-14 are therefore proved by unit
tests only, as the Refactorer's report corrects [read]. As r1 noted, test 7's reload does not isolate the REST search,
because the preloaded history holds the controls events [read].

---

## 7 · Size, before and after

`git diff --numstat 9881d24...<ref>`, by kind [run; the totals match the figures the Refactorer reported from its own
script]:

| Kind | r1, `64b5a8b` | after the Gate B fixes, `61b9bdc` | after the refactor, `f4c7ae5` |
|---|---|---|---|
| Code (`src/`, not tests, fixtures or translations) | +2,635 −141 (50 files) | +2,671 −141 (50) | **+2,626 −141 (49)** |
| Unit tests (incl. helpers) | +3,284 −11 (27) | +3,407 −11 (27) | **+3,280 −11 (27)** |
| Playwright specs | +474 (2) | +474 | +474 |
| Mock agent and test mapping | +157 −12 (2) | +157 −12 | +157 −12 |
| Translations, fixture, upstream `specs/`, skill guide | +405 −3 (8) | +407 −3 | +407 −3 |
| **All** | **+6,955 −167 (89); 6,297 non-blank** | **+7,116 −167 (89); 6,443** | **+6,944 −167 (88); 6,287** |

- The refactor took out 172 lines (2.4 %): code 45 (1.7 %) and unit tests 127 (3.7 %).
- Most of the code went from `agent-server-compatibility.ts` (−37), `use-agent-controls.ts` (−11) and
  `type-guards.ts` (−6, now untouched). `use-set-acp-config-option.ts` grew by 14.
- Most of the test lines went from the helper tests and duplicates of §6.3, and from four copies of one wrapper, which
  became `query-wrapper.tsx` (+21).
- At ≈300 lines an hour, Gate C reads the whole diff in about 23 h, and the code with its unit tests (5,906 lines) in
  about 20 h.
- The largest pieces are now:
  - code: `use-agent-controls.ts` 229, `chat-input-agent-options.tsx` 221, `app-backend-session-keeper.ts` 219,
    `canvas-extensions-runtime.tsx` +213 −19, the conversation service +131 −42;
  - tests: `use-acp-session-preview.test.tsx` 410, `use-agent-controls.test.tsx` 305, `mount-app-backend-frame.test.ts`
    246.

---

## 8 · What I could not verify

1. **App backend frames against a real agent-server.** Every frame and keeper test fakes the client at its boundary.
   No test, and nothing I ran, mints a session on a real ingress or loads a frame in Chromium or Electron.
2. **D-12, D-13 and D-14 end to end.** A live set, its toast, a home refusal and its withdrawal run in unit tests only;
   no live test reaches them (§6.4).
3. **The REST search end to end**, and the history preload's limit: read only.
4. **The drawer's terminal behind an App panel**: the test keeps a mocked stand-in mounted.
5. **Unit isolation and the PR split**: nothing was cherry-picked or run alone.
6. **Mutation testing over the diff** (v2 B18): Stryker has still not run. §6.3's probes are ten hand edits aimed at the
   cut tests and the fixes.
7. **The full mock-LLM suite at `f4c7ae5`**: nobody has run it; §6.1 cites r1's record at `64b5a8b`.
8. **The full vitest suite locally**: not run, per the brief; CI's run is green.
9. **D3 inside Canvas**, and **C2 against the SDK fork's merged `deep-reasoning`**: both read only.
10. **The capability gate's timing**, and `useLatestAcpSessionControls` returning a cached search while disabled
    (D-17): both read only.

What resists shortening is §2 and §6.3. The code follows v2 closely in shape. What moved is concentrated in the
refusal paths (D-12 to D-15) and in what the tests now pin (D-18, §6.3). Of the three unpinned properties, one lost its
pin in Gate B fix 2 (`6fb7f05`) and two with the refactor's cut tests (`9c49036`).
