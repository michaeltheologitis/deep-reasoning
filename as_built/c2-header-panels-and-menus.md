# C2 · App header panels, agent commands and an option picker, as built

**TASK-7** · Cartographer · **r3, 2026-10-04: Gate C's map of the stack #20–#26, top `6810335`**, in the Canvas fork
[michaeltheologitis/OpenHands](https://github.com/michaeltheologitis/OpenHands). The stack's base is the fork's
`deep-reasoning` at `1913c58`, which holds C1; its top's tree (`10dfa89`) equals `feat/agent-surfaces` at `7a8f714`;
C2 is `git diff 1913c58...6810335` · checked against the design **v2 at `6e489ea`** (`docs/design/c2-header-panels-and-menus.md`;
the v3 being drafted on `design/c2-next` is not this document's yardstick) · agent-server and TypeScript client from the
SDK fork's tag `dr-2` (`34c540c`) · Node 22.22 and npm 10.9 in this sandbox, Node 24.15 and npm 11.12 in CI.

**Revisions** (newest first):
- **r3 · 2026-10-04 · `6810335`.** C2's code did not change; its base, its tests and its shape did. Since r2's
  `f4c7ae5`: two test-only pins (`667ec86`, `a1ec3d1`); the merge of the fork's `deep-reasoning` at `fc87687`
  (`30068b8`); the split into seven draft PRs (top `ca1dd71`); three test fixes (`52b0bfe`, `eef08ab`, `73d2e1a`); and
  the merge of `deep-reasoning` at `1913c58`, which holds C1, into every level (top `6810335`). Of C2's 88 files, 13
  have a new blob since `f4c7ae5`: five test files, and the 8 C1 also changes, where C2's own lines are unchanged.
  None of the 13 is cited here by line, so every line number in this document holds [run]. Stop trusting these parts
  of r2: D-15's and D-18's "not pinned" claims; D-19 and §7's figures; §4.6 (`dr-1`); §4.7's C1 and D3 locations; §5
  (PR #3); §6.1–§6.3's runs and counts; §8 items 5, 7 and 9. New: §2.4 (D-20, D-21), §5.1–§5.3, §6.5, and D5 in §4.7.
  This revision was first pushed at `ca1dd71` (`bab4615`) and redone at `6810335`.
- r2 · 2026-10-04 · `f4c7ae5`, against v2: three Gate B fixes and 13 refactor commits; D-12 to D-19.
- r1 · 2026-10-03 · `64b5a8b`, against v1 at `72aa49f`.

**Where this file lives.** It is on deep-reasoning's branch `as-built/c2-r3`, cut from `as-built/c2-r2` at `fbf4230`,
and the Conductor merges it into `design/c2`. The branch holds only documents: no `pyproject.toml`, no docs site and no
test runner. So nothing collects `as_built/`, and there is nothing to wire. [run: `git ls-tree` of this branch]

**Evidence marks.** Every claim carries one.
- **[run]** means executed in this sandbox, in a detached worktree of `6810335` with a fresh `npm ci` (then
  `npm run make-i18n`), and one of `1913c58` whose `node_modules` hard-links that install (`package-lock.json` is the
  same blob at both). What ran:
  - C2's 26 test files at the top and the 15 of them that exist at the base, and nine mutation probes (§6.3), each one
    edit, reverted, `git status` empty after;
  - typecheck and the level's own tests for #23's level diff on the base, and #26's on #22 and on #20 (§5.2);
  - ESLint over `__tests__/` and Prettier over `specs/` at both commits (§6.5);
  - `git merge-tree` and patch comparisons for the merges (§5.1).
  Before the redo, at `ca1dd71`: the client type-check and digests (§4.6), which the unchanged pins carry over [run:
  `git diff fc87687 1913c58 -- package.json package-lock.json config/defaults.json` is empty]. r2's runs, at
  `f4c7ae5` and its comparison commits, are marked as r2's where they still stand.
- **[CI]** means read from GitHub's records through the GitHub MCP tools: CI run 37223122365 and mock-LLM run
  37223123058, both at `6810335`, with their full job logs downloaded; each level's check runs; and, before the redo,
  runs 37215713339 and 37215721829 at `30068b8`.
- **[read]** means read in the code and **not executed**. It is weaker evidence; §8 lists the read claims that matter.

Nothing here ran a paid model, the `claude` CLI or a live test. I made no commit in the Canvas clone.

**Reading order.** §2 first (the divergences, with §2.4 new in r3), then §5 (the merges and the stack) and §6.3 (the
probes). Use §1, §3 and §4 as the map, and §4.6–§4.7 for who C2 relies on and who relies on C2.

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
| `667ec86` `a1ec3d1` | two pins after r2 (§6.3 P5, P6) | — | +35 −5 | — |
| `52b0bfe` `eef08ab` `73d2e1a` | two lint fixes (§6.5) and the P2 pin (§6.3), on #20, #21 and #24 | — | +12 −4 | — |

These are per-commit figures [run: `git show --numstat`]. The first four rows are as committed, measured in r1. The net
size at the top, by kind, is in §7. Not C2's: `ba4d883` (fork-only, byte-identical to C3's file in the wiring), the
merges `c08ded0` and `64b5a8b`, which bring in `wiring/dr-1` with no hunk of their own (r1, [run]), and the merges of
`deep-reasoning` (`30068b8`; the `1913c58` merges into each level), which add no line to C2's diff except #23's
resolution of one conflict (§5.1). Gate C reads these commits as the seven levels of §5.2.

---

## 2 · Divergences from the design (v2, `6e489ea`)

The changelog still holds no entry for TASK-7, so there is no `drift:` line. Every item was found from the code
[run: Notion query of the Changelog, r3]. All of `3912c52` … `73d2e1a`, the merges and the split were committed after
v2 (2026-10-03 23:20 → 2026-10-04 18:07). "v2 §x" cites `6e489ea`.

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
  helper. On the live set that check is pinned (P6b). On the home screen it was unpinned from `6fb7f05` to `f4c7ae5`;
  `a1ec3d1` pins it (P6, §6.3).
- Reason: `4ff261c`.
- Evidence: [run: the frame tests' `not-ready` and `no-ingress` rows; read: upstream's helpers]. C1's as-built §2.1
  D-1 cites `getSdkHttpServerErrorReason` at `:235` of this branch, a line that no longer exists (§4.7).

**D-16 · The controls event guard is the client's, and C2 no longer touches `type-guards.ts`.**
- v2 says: §5.2, A.8, §8 item 1's v2 note ("which Canvas declares in its own `type-guards.ts`") and §9's first row.
- Built: `useLatestAcpSessionControls` imports the client's `isACPSessionControlsEvent`
  (`src/hooks/query/use-latest-acp-session-controls.ts:4, 17`).
  - It checks `event.kind === 'ACPSessionControlsEvent'`, as C2's guard did [read: `dist/events/types.js:60–62` in
    the `dr-1` tarball (r2) and in the `dr-2` tarball (r3)].
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

**D-18 · v2's test tables name seven tests that no longer exist, and v2's unpinned list is out of date.**
- v2 says: its Gate B tables, and §3.2 B17 with 109 vitest definitions (11 of them `it.each`) in 26 files.
- Built: 110 definitions (12 `it.each`) in 25 files that carry C2 lines, plus two shared helpers
  (`__tests__/helpers/canvas-extension-panels.tsx`, and the new `__tests__/helpers/query-wrapper.tsx`). That is 141
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
- New: D-12's and D-13's tests, `a1ec3d1`'s two rows and `73d2e1a`'s one.
- v2's "Not pinned by any test" paragraph lacks three properties that r2's probes found unpinned. Since r2 all three
  are pinned, and §6.3's probes find none left [run, §6.3]:
  - two frames of one App share one session through `mountAppBackendFrame` (P5, by `667ec86`);
  - a home-screen preview failure that is not a 422 is never shown as the agent's sentence (P6, by `a1ec3d1`);
  - a disabled latest-controls hook reads no live event (P2, by `73d2e1a`).

**D-19 · Size after the fixes, the refactor and the pins.**
- v2 says: §3.2 B20 and ruling 1 give 6,955 lines added and 167 removed, in 89 files.
- Built: 6,982 added and 167 removed, in 88 files (§7) [run].

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

**Recorded in v2 since r1:** D-1 as B1 (D3 itself now searches with the qualified kind, §4.7); D-2 as B2 (its mechanism
changed again, D-15); D-4 as B4; D-5 as B13; D-6 as B6; D-7 and D-8 in the Gate B section, B16 and B19; D-9 as B18;
D-10 as B20; D-11 as B17; r1 §2.2's other rows as B7, B8, B10, B11, B12, B14 and B15.

**Not divergences.** These hold as v2 describes them, unchanged since r1 [run for behaviours §6.2's tests name; read
for the rest]:
- decisions A–N;
- §4's panel slot, store actions, tab rules and narrow page;
- §5.5's menu;
- §6's frame and keeper;
- Appendix B's ten keys, each in 15 languages.

### 2.4 Since r2: the base, the client and the split

**D-20 · C2 runs on the fork's `deep-reasoning` with the `dr-2` agent-server and client, not on `wiring/dr-1`.**
- v2 says: its header (`:11–23`), §8 (`:1280`), §9's files table and Order paragraph (`:1304–1312`) and §10
  (`:1350`) build C2 on `wiring/dr-1`, with the agent-server from the SDK fork's `cef3b24` (tag `dr-1`) and that tag's
  client tarball; its Gate B section reads PR #3.
- Built: the stack's base is `deep-reasoning` at `1913c58`, which holds C3's launcher stack (#5–#11), the redone
  wiring (#12) and C1 (#13–#19). `config/defaults.json` names the SDK fork at `34c540c` (tag `dr-2`), and `package.json` pins the `dr-2`
  release's client tarball. `cef3b24` is not an ancestor of `34c540c` (§4.6) [run: `git show`, `git merge-base`].
- Reason: `30068b8`'s message, "Bring C2 onto deep-reasoning at fc87687, which carries C3's launcher stack and the dr-2
  wiring in place of wiring/dr-1"; then C1 merged into `deep-reasoning`, and every level merged it (§5.1).
- Evidence: §5.1 (the merges), §4.6 (the client), §6.1 (CI and the live tier against `dr-2`) [run; CI].

**D-21 · Seven PRs, not three.**
- v2 says: §4, §5 and §6 are PR 1 (header panels), PR 2 (agent commands and the picker) and PR 3 (backend frames).
- Built: PR 1 is #20–#22 (registration, the column, the button); PR 2 is #23–#25 (the contract, the conversation, the
  home screen); PR 3 is #26 (§5.2) [run: per-level file lists].
- Reason: the PR Splitter's, in each PR's body [read].

---

## 3 · The public surface, from the code

No code changed since r2, so this section stands as r2 wrote it [run: blobs compared, see the revision note].

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

- **The home path of §4.2:** 74 lines (`use-agent-controls.ts:156–229`) with 18 tests of their own. It has two refs
  written during render and one effect. The withdrawal depends on D-14's `staleTime` rule not to ask again: probe P9b
  makes both fail together.
- **The keeper's lease counting** (§4.4).

The panel slot is many small pieces, each simple.

### 4.6 What C2 relies on

- **S2, through `dr-2`.** The annotated tag `dr-2` (`9e142cc`) names `34c540c`, the head of the SDK fork's
  `deep-reasoning`, where S1 and S2 are merged [run: `git ls-remote`, `git branch -r --contains`]. The `dr-2` release
  says its client is "built … at 34c540c". The tarball the lockfile pins is that release's asset: its sha256 equals
  GitHub's digest (`7bcd8134…`) and its sha512 the lockfile's `integrity` [run]. Its version string is 1.50.1, like
  npm's, whose integrity differs. C2's added lines import eleven names from it and use five client members (four
  methods and the `appBackendIngressUrl` option). Each exists at `34c540c`'s `clients/typescript/src` [run: `git grep`]
  and in the tarball [run: a file importing all of them type-checks against it]. Against npm's 1.50.1 the same file
  fails on ten of the sixteen:

  | C2 uses | npm's 1.50.1 |
  |---|---|
  | `ACP_SESSION_CONTROLS_EVENT_KIND`, `isACPSessionControlsEvent`, the types `ACPSessionControlsEvent`, `ACPSessionControls`, `ACPAvailableCommand`, `ACPConfigOption`, `ACPConfigOptionValues`, `ACPConfigOptionSetResponse`; `ConversationClient.previewAcpSession` and `setAcpConfigOption` | absent |
  | `HttpError` (tests only), `AgentKind`, `CanvasExtensionsClient` with `appBackendIngressUrl`, `createAppBackendSession` and `revokeAppBackendSession` | present: upstream's |

  So, by its imports, C2's unit 2 needs the fork's client and unit 3 does not [run: `tsc --noEmit` against both
  packages].

  From the agent-server, C2 relies on: the three capability strings and `app_backend_ingress_url` in `/server_info`;
  `contributes.conversation_panels`; the icon route; the preview ignoring `conversation_id` and `initial_message`;
  `acp_config_options` on the start; the set route's 422 sentence in `detail`; the qualified-kind search; the
  `ACPConfigOptionRejected` error code; the 5xx `{detail, exception}` shape; and the bridge's session route with its
  503 sentences. Each string is present at `34c540c` [read: `git grep`]; the SDK's tag `v1.50.1` has no `/preview`
  route [read]. CI and the live tier now run C2 against `dr-2` (§6.1) [CI; read for the bridge].
- **C3, through `deep-reasoning`.** C3's stack (#5–#11) merged into `deep-reasoning` before `fc87687` [read: the PR
  list]. C2 uses two things from it, both present, at the same lines, at `fc87687` and `1913c58` [read]:
  - `config/defaults.json`'s `sources.agentServerGitRepo` and `agentServerGitRef` (`34c540c`), from which the launcher
    installs the agent-server for the stack the live tier runs;
  - the default `OH_APP_BACKEND_PUBLIC_URL` (`scripts/dev-safe.mjs:883–884`), without which every frame reports
    `no-ingress`.

### 4.7 Who relies on C2, and on what

- **D3, the Decompositions panel**, now on deep-reasoning's `main` (`b2a74e0`; the changelog's "D3 merged"). Its
  manifest names the App `dr-library` and the panel `decompositions` (`src/deep_reasoning/canvas_app/canvas-extension.json`).
  D3 relies on:
  - the manifest key and the button;
  - `registerPage` for its four tab ids;
  - `conversationId`, and `surface.selectTab`, which D3 calls on a frame message (`canvas-app/src/page/mount.ts:87`);
  - `host.agentServer.request` within its 60 s, for the backend's status and start (`:106`); the 60 s is pinned (P1);
  - `host.appBackend.mountFrame(container, {path: "/ui/…", title, onError})` (`:130`), retrying once on `not-ready`
    (`:91–95`);
  - the frame being the container's `<iframe>` child (`:76`), which C2 keeps across refreshes. D3 empties the container
    before each mount (`:129`); C2 appends the frame and prepends any notice.

  D3's `readConversationNamespace` searches with the module-qualified kind (`canvas-app/src/page/context.ts:28, 38–40`).
  Nothing in C2's tests runs D3, and D3 has not run inside Canvas. [read: D3's `canvas-app/src/page/*.ts` on `main`]
- **C1** is now part of C2's base: its stack #13–#19 merged into `deep-reasoning` (`1913c58` is "Merge pull request
  #19"), and its top `51ed1ad` is an ancestor of `1913c58` [run: `git merge-base`]. It shares 8 files with C2:
  `events/index.ts`, `openhands-event.ts`, `translation.json`, `event-service.api.ts` and its test,
  `should-render-event.test.ts`, `transcript-export/index.test.ts` and the e2e guide.
  - In those 8 files C2's added and removed lines are the same on the new base; only their context and blobs moved
    [run: the patches' `+`/`-` lines compared against r3's `fc87687...ca1dd71`].
  - The one conflict r3 predicted, line 2 of `src/types/agent-server/core/events/index.ts`, arose at #23 and was
    resolved there (`c979c89`) by keeping both exports: C2's `./acp-session-controls-event` on line 2, C1's
    `./acp-subagent-event` on line 3 [run: `git show`; the original `5e875d2` on `1913c58` conflicts on that line,
    `git merge-tree`]. #23's body still says "whichever stack merges second resolves that one line" [read].
  - **The shared 5xx-reason rule** that C1's as-built §2.1 D-1 names is C2's in one place only: `toAppBackendError`
    (`:74–88`), reading `exception` through upstream's `getApiErrorBody`. It matches the reason by regular expression
    to classify a 503 and shows it to no user. C1's `refusalReason` (`use-cancel-acp-session.ts:25` at `1913c58`)
    shows the reason in a toast. The two remain separate implementations. [read]
- **D1's dr-acp, through S2.** Its commands and its `namespace` select reach C2's menu and pills. C2 relies on the
  namespace being a `select` not named `model`, on a single value meaning "fixed", and on a new report replacing the
  last. [read]
- **D5** (design v2, deep-reasoning `design/d5` at `9ee36f6`). §8.4 names, and §7.5's E12 drives, these of C2's.
  Each exists at the top, in the spec table and in the code [read: specs, and the `data-testid` sites]:

  | D5 names | Spec | Code |
  |---|---|---|
  | `conversation-app-panel-toggle-<extension>-<panel>` (E12: `…-dr-library-decompositions`) | CX-006 | `conversation-app-panel-toggle.tsx:72` |
  | `conversation-app-panel-tab-<tab>`, `conversation-app-panel-content` | CX-006 | `conversation-app-panel.tsx:65`; `conversation-app-panel-tab-content.tsx:55` |
  | `agent-options`; `agent-option-<id>`; `agent-option-<id>-value-<value>` (E12: `agent-option-namespace-value-<ns>`) | ASC-005 | `chat-input-agent-options.tsx:196`, `:114`, `:62` |
  | `slash-command-item` with `data-command`; `slash-command-hint` | ASC-005 | `slash-command-menu.tsx:109–110`, `:125` |
  | `host.appBackend.mountFrame`, reading `app_backend_ingress_url` | §3; frames section | `mount-app-backend-frame.ts:24–41` |
  | the renewal: the panel still loads after the first session's five minutes | frames section (`canvas-extensions.md:150`) | the keeper's refresh, §4.4 |

  Two of D5's sentences predate the split: §8.4 cites C2 as "PR #3" and says C2 "is built on `wiring/dr-1`" and will
  merge the redone wiring; C2 now sits on `deep-reasoning` as #20–#26 (§5). The value element D5 picks exists only
  while the option has more than one value, which is the home screen's case for `namespace` (§2.3's fixed-pill row).
  E12 has not run. [read]

---

## 5 · The pull requests

### 5.1 The merges

C2 reached its base in two merges of the fork's `deep-reasoning`.
- **`fc87687`, at `30068b8`.** r3's first pass checked it: C2's diff against `fc87687` was byte-identical to its diff
  `9881d24...a1ec3d1`, and each of the 11 conflicted files (C3's launcher scripts and three of their tests,
  `config/defaults.json`, `package.json`, `package-lock.json`) took `fc87687`'s blob and is outside C2's diff [run].
- **`1913c58`, which adds C1.** It was merged into #20 (`2368937`) and carried up, level by level, to #26 (`6810335`).
  `feat/agent-surfaces` then merged the top as `7a8f714`, whose tree (`10dfa89`) equals the top's [run].
  - C2's diff `1913c58...6810335` touches the same 88 files as r3's `fc87687...ca1dd71`. For 77 of them the patch is
    byte-identical. Three differ by the test fixes (§1). The other 8 are the files C1 shares (§4.7): C2's added and
    removed lines are the same, and only context and blob ids moved [run].
  - Outside those 88 files, `6810335` equals `1913c58` file for file [run].
  - Of the 13 merges inside the stack, 12 equal git's automatic result. The 13th, #23's `c979c89`, differs from it only
    in `events/index.ts`, the one conflict (§4.7). `7a8f714` conflicts in four files, the three fixed tests and that
    one, because `feat/agent-surfaces` still held `30068b8`; it takes the top's tree whole [run: each merge replayed
    with `git merge-tree`]. The diff is +6,982 −167 [run].
  - CI 37223122365 and the mock-LLM run 37223123058 at `6810335` are green (§6.1) [CI].

### 5.2 The stack

Seven draft PRs labelled `type: feat`, each based on the one below; #20's base is `deep-reasoning` at `1913c58`. Each
level now holds its original commit, its own fix if it has one (#20, #21, #24), and the merges that carry `1913c58`
and the levels below up: one merge at #20, two at every other level, three or four commits in all [run:
`git rev-list`]. Every level's `test-and-build`
passed on ubuntu (lint, the full suite, build, build:lib) and windows (build); `live-e2e` was skipped; the `pr-title`
jobs passed [CI].

| PR | Head | Title | Lines changed: code / unit tests / other | CI run | r2/r3 sections it carries |
|---|---|---|---|---|---|
| #20 | `2368937` | let an App declare conversation panels and register each tab as a page | 1,092: 458 / 455 / spec 78, fixture 67, i18n 34 | 37221677161 | §1 item 1; §3 manifest and host API; §4.1 registration; §2.3 mount-effect row |
| #21 | `0e8c202` | show an open App panel in the drawer's column, one right-hand panel at a time | 1,156: 554 / 602 | 37221768639 | §3 routes and state; §4.1 column, tab state, mount lifecycle |
| #22 | `47dfbbc` | give each App panel a header button, and a page of its own on a narrow window | 937: 292 / 319 / e2e 290, i18n 34, guide 2 | 37221860027 | §3 icon request; §6.4 live tests 1–5 |
| #23 | `c979c89` | preview, set and find an ACP agent's session controls, and start with chosen option values | 499: 192 / 241 / spec 49, i18n 17 | 37221999557 | §3 services; §4.3; §4.6; D-17's two rows; §2.3 r1's D-3 |
| #24 | `b796e18` | offer an ACP conversation's agent commands in the slash menu and its options as pickers set live | 1,256: 514 / 708 / i18n 34 | 37222106730 | D-12, D-16; D-17's two rows; §4.2 gate, conversation, menu, pills; P2, P3, P6b, P7 |
| #25 | `0cdb1b8` | preview the ACP agent's commands and options before the first message, and start with the values it accepted | 1,205: 320 / 530 / e2e and mock agent 353, guide 2 | 37222207434 | D-13, D-14; D-17 `setValues`; §4.2 home; §4.5; P6, P8, P9a, P9b; §6.4 live tests 6–7 |
| #26 | `6810335` | show an App's own backend in a host-kept, sandboxed frame | 1,006: 439 / 474 / spec 42, i18n 51 | 37223122365 | §1 item 3; D-15; D-17 timeout; §2.3 unused `signal`; §4.4; P1, P5; §8 item 1 |

The lines are my `git diff --numstat` per level, base head to level head [run]. They sum to 7,151, two more than the
stack's diff (the interim line below). Only #24 changed size since `ca1dd71`, by `73d2e1a`'s 8 lines; the two lint
fixes each replace one line of a file their level adds. The PR bodies predate the fixes and the merge: #23's cites
`5e875d2` and the C1 line as unresolved, and #24's still says 1,248 lines and that P2 holds [read]. The last column is
#26's reading map, checked against each level's files [run]. It omits three placements: D-15 spans #20 (C2's only
addition to `agent-server-compatibility.ts`), #24 and #25 (the two refusal sites), and only its keeper half is #26's;
P4's banner is #23's; and §2.3's slash-menu and fixed-pill rows are #24's.

**The Splitter's three choices**, each checked:
1. **Spec text lands at its first level, ahead of its code.** #20 adds CX-001 to CX-004 and CX-006; their `@spec`
   tags arrive at #20 (CX-004) and #21–#22 (the rest). #23 adds all of `specs/acp-session-controls.md`, ASC-001 to
   ASC-005; its code is tagged at #23 (ASC-002's start body), #24 and #25. #26 adds the frames section and CX-005, with
   their code. No other level touches `specs/` [run: per-level spec diffs and `@spec` tags, at `ca1dd71`; the fixes
   touch no spec and no tag].
2. **#23 and #26 need nothing from the levels just below them.** Taken as a level diff, this still holds:
   - #23's diff (`47dfbbc..c979c89`) applies cleanly to `1913c58` alone; there typecheck passes and its five test
     files pass (198 tests, five more than at `fc87687` because C1's tests share those files). Its original commit
     `5e875d2` no longer applies cleanly to that base: it conflicts on C1's line 2 of `events/index.ts`, which #23's
     merge resolves.
   - #26's diff applies cleanly to #22: typecheck and its three test files (27 tests) pass. On #20 alone it conflicts
     in one file, `canvas-extensions-service.ts`, whose hunk has #22's `fetchPanelIcon` as context. With that context
     removed, typecheck and the same 27 tests pass. So #26 needs #20 in substance, and #22 only as text.

   [run: `git merge-tree` cherry-picks, then `npm run typecheck` and vitest, at the new heads]
3. **One interim line, at #24.** Each file's lines across the levels sum to its lines in the stack's diff except
   `src/hooks/chat/use-agent-controls.ts`, by +1 −1. #24 writes `import { localAgentServerHasCapability } from
   "#/api/agent-server-compatibility";` and #25 replaces it with the multi-name import. No other line is written and
   then rewritten [run, at the new heads]. #24's body names the line, then says "no line is rewritten between the
   levels" [read].

### 5.3 PR #3 and the task row

PR #3 is still open as a draft, `feat/agent-surfaces` → `wiring/dr-1`, now at `7a8f714`. Against that base it shows
+13,662 −1,000 in 148 files: C2 plus everything `deep-reasoning` gained since `wiring/dr-1`, C1 included. Its
description still reports the runs at `86c00b5` [CI; run: `git diff --shortstat`]. TASK-7's row has `Lines After`
6,982, the stack's added lines, and its `Design` field names `design/c2` with v3 on `design/c2-next` [read:
`ase-skills tasks get TASK-7`].

---

## 6 · Tests and runs, as measured

### 6.1 The runs

| Run | Commit | Conditions | Result |
|---|---|---|---|
| CI [37223122365](https://github.com/michaeltheologitis/OpenHands/actions/runs/37223122365) | `6810335` | `pull_request` (#26); ubuntu-24.04 full checks; windows build only; Node 24.15.0, npm 11.12.1 | green. Lint 0 errors, 379 warnings. Test: **781 files passed, 1 skipped; 8,376 tests passed, 1 skipped, 7 todo** in 651 s. Build, build:lib and the package check green [CI] |
| mock-LLM [37223123058](https://github.com/michaeltheologitis/OpenHands/actions/runs/37223123058) | `6810335` | `workflow_dispatch` of `mock-llm-e2e.yml` with `SPECS` = C2's two spec files and C1's two (`mock-llm-acp-subagents`, `mock-llm-acp-replay`); the mock LLM; the mock ACP agent; the agent-server the launcher installs from `defaults.json`'s source, `34c540c` | **13 passed** (2.9 min; the job 4 min 33 s), 1 worker: C2's 7 and C1's 6. The log does not print the agent-server's commit [CI; read for the source] |
| each level's CI | the seven heads | as the first row, on `pull_request` | all green (§5.2) [CI] |
| before the redo | `30068b8` | CI 37215713339; mock-LLM 37215721829 with C2's two specs only | green; 776 files, 8,258 tests; 7 passed, C2's first run against `dr-2` [CI] |
| full mock-LLM suite | — | none since r1. r1's record at `64b5a8b` (37153914745): 6 upstream failures, the same 6 as at `ba4d883` without C2 | not re-run [CI, r1] |
| this sandbox, r1's 26 test files | `6810335`; the 15 that exist at the base, at `1913c58` (r2: `f4c7ae5`, `61b9bdc`, `64b5a8b`, `9881d24`) | Node 22.22, a fresh `npm ci` | **523** passed at the top; **382** at the base, five more than r2's 377 because C1's tests share three of those files (r2: 515, 521, 515) [run] |
| this sandbox, typecheck | #23's level diff on `1913c58`; #26's on #22 and on #20 | `npm run typecheck` | all pass (§5.2). r2 ran typecheck and both builds at `f4c7ae5`; the top's are CI's [run; CI] |

**Lint warnings in C2's lines** are 3 of the 379, as in r1: `shadcn/no-arbitrary-values` in
`chat-input-agent-options.tsx` (`:52`, and `:163` twice). The other seven warnings in files C2 touches fall on lines
from before C2. [CI: the lint log at `6810335`; r2: `git blame`] CI lints only `src/` (§6.5).

### 6.2 The deterministic tests C2 adds

There are **141 cases in r1's 26 files, all passing** (523 at the top, less the base's 382). They come from **110
definitions**, 12 of them `it.each`. `acp-error-codes.test.ts` no longer carries a C2 line, so 25 files hold C2's
tests. [run]
- **Unit 1: 58.** Store (9: `CX-001`'s 7 sequences, start state, `hasRightPanelToggled`); local storage (8); runtime
  (6); tab hook (5); toggle (8); panel (8); column (2); narrow page (3); Apps card (3); capability helper (5); icon
  fetch (1).
- **Unit 2: 66.** Service (6); event search `kind` (2); latest controls (7); conversation controls (13); home controls
  (18); slash menu (5 hook, 1 menu); pills (9); home launcher (2); banner, rendering and transcript export of the event
  (1 each).
- **Unit 3: 17.** Keeper (7); frame (9); the host's frame mounter (1).

Since r1, by name [r2's run: test names diffed between `64b5a8b`, `61b9bdc` and `f4c7ae5`; r3's: the two commits]:
the Gate B fixes replaced 2 tests and added 6 (D-12's and D-13's, §2.1); the refactor removed 9 (§6.3) and added 3
(D-12's 400 and 404 rows and its unmount test). Since r2, `a1ec3d1` adds `keeps a pick whose preview answers %i after
an earlier answer, and shows no sentence for it` (400, 504); `667ec86` rewrites the frame's dispose test to mount two
frames of one App, as `removes its frame when disposed, and releases the App's one session when its last frame
closes`; and `73d2e1a` adds `useLatestAcpSessionControls › ignores live events while disabled`.

Two `it.each` tables print duplicate titles. Three sanitizer rows each read `sanitizes a stored { 'demo/panel':
[Object] }`, and two `CX-001` sequences share `keeps one right-hand panel after open drawer then open panel A`. A report
shows 138 distinct names for the 141 cases. [run]

Every vitest file fakes services at their boundary (the client, `EventService`, `AgentServerConversationService`). The
refactor's `8708eae` makes the tests throw the client's own `HttpError` class, so D-12's toast assertions read the
client's real message format. [read]

### 6.3 What the refactor removed from test coverage, with probes

**Method.** Each probe makes one temporary replacement and runs the named test files, or all 26. Then `git checkout`
restores the file and `git status --porcelain` is empty. Probes P1–P6 test the nine cut tests; P6b–P9b test the fixes'
own tests. r2 ran all ten at `f4c7ae5`. r3 re-ran all but P7 against all 26 files, at `ca1dd71` and again at
`6810335`. P7 moves the toast across two files, so it is not one edit; its files have not changed since r2. At
`6810335` every probe is killed: P2, P5 and P6 only by the tests `73d2e1a`, `667ec86` and `a1ec3d1` added, the other
six by the same tests as in r2. At `ca1dd71`, before `73d2e1a`, P2 still survived. [run]

| Cut test (`9c49036`, `4ff261c`) | Where its property stands | Probe | Result |
|---|---|---|---|
| `getSdkHttpErrorDetail › reads the agent-server's detail sentence…` | the helper is gone; a 422's sentence is pinned at both refusal sites (D-12, D-13 tests) | — | — |
| `› is null for a validation error list` | no test. `getApiErrorMessage` falls back to the error's text for a non-string `detail`, as the helper's fallback did [read] | — | — |
| `› is null for a body without detail`, `› … not an SDK HTTP error` | the set's table pins non-HTTP failures (timeout, lost connection) | — | — |
| `› is null for a 5xx answer…` | the live set: pinned by its 504 row | **P6b**: any HTTP status counts as a refusal in `useSetAcpConfigOption` | **killed** by the 504, 400 and 404 rows |
| (same) | the home screen: pinned since r2 by `a1ec3d1` | **P6**: the same edit in `useHomeAgentControls` (`:190`) | **killed** at `ca1dd71` and `6810335` by `keeps a pick whose preview answers %i after an earlier answer…`, both rows (400, 504), and by nothing else. At `f4c7ae5` it **survived** all 26 files: `6fb7f05`'s `rejection` shows only beside shown controls, and the older `… when the preview answers %i` rows have no earlier answer. Unpinned, a 504 after an answered preview would show "Internal Server Error" as the agent's sentence and withdraw the pick |
| `useLatestAcpSessionControls › issues no search and reads nothing while disabled`: the search half | pinned by `useConversationAgentControls › has no controls, and searches nothing, for %s` | **P3**: the query ignores `enabled` | **killed** in all 3 rows |
| (same): the scan half | pinned since r3 by `73d2e1a`, through what the hook returns | **P2**: the selector ignores `enabled` | **killed** at `6810335` by `useLatestAcpSessionControls › ignores live events while disabled` only (522 of 523 passed). It survived all 26 at `f4c7ae5` and at `ca1dd71`. Unpinned, every store update in every non-ACP conversation would scan the whole event store (`501f0c6`'s message) [read] |
| `acp-error-codes › maps a refused start-time option value to its own header` | pinned by the banner test | **P4**: rename the map's key | **killed** by `heads a refused start-time option with its title…` |
| `CanvasExtensionsService › gives an App's agent-server requests a minute…` | pinned by upstream's `fetches the bundle as authenticated text…`, which asserts `timeout: 60000` on the client builder `requestAgentServer` shares (`canvas-extensions-service.ts:75–87, 256`) | **P1**: the constant 60 000 → 5 000 | **killed** by that upstream test |
| `mountAppBackendFrame › keeps one session for two frames of the App…` | pinned through the frame since r2 by `667ec86` | **P5**: `resolveTarget` gives each frame its own backend id | **killed** at `ca1dd71` and `6810335` by `removes its frame when disposed, and releases the App's one session when its last frame closes` only. At `f4c7ae5` it **survived** all 26; at `61b9bdc` the cut test killed it |

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

The two spec files and the mock agent are unchanged since r1 [run: r2's `git diff 64b5a8b f4c7ae5 -- tests/e2e` is
empty, and r3's blob comparison]. C2's seven tests ran in this order in r2's run at `f4c7ae5` against `dr-1`, in run
37215721829 at `30068b8` against `dr-2`, and in run 37223123058 at `6810335`, where they are tests 1–5, 7 and 8 of 13,
interleaved with C1's [CI]:
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

### 6.5 Lint outside CI's reach

CI's lint is `npm run typecheck && eslint src && prettier --check src/**/*.{ts,tsx}`, and lint-staged covers
`src/**` only [CI: the lint log; read: `package.json`]. So `__tests__/` and `specs/` are never linted. The PR Splitter
found two gaps there, each holding content from C2 in a gap that predates it [run at `6810335` and `1913c58`]:
- **ESLint over `__tests__/`** reports 837 errors in 724 files, nearly all upstream's, and **none on C2's lines**. At
  `ca1dd71` two fell on C2's lines, both from C2's `1828cec`, and the fixes removed them:
  - `__tests__/helpers/canvas-extension-panels.tsx:71`, `import-x/extensions` (the `.js` in the import of the
    `demo-panel` fixture): `52b0bfe` drops the extension, on #20.
  - `__tests__/components/features/conversation/conversation-app-panel.test.tsx:171`, `no-param-reassign` (a mount
    that set `container.textContent`): `eef08ab` appends the text instead, on #21.

  Seven errors in C2-touched files (`conversation-main.test.tsx` 1, `home-chat-launcher.test.tsx` 6) fall on
  upstream's lines, as before.
- **Prettier over `specs/*.md`**, unfixed: at `1913c58`, 4 of the 6 files already fail (`acp-subagent-sessions.md`,
  C1's, `backend-management.md`, `canvas-extensions.md`, `workspace-upload-path.md`). At the top 5 of 7 fail, the
  fifth being C2's new `acp-session-controls.md`. In `canvas-extensions.md`, Prettier's changes grow from 1 hunk to 13. The 12 new ones fall
  in C2's invariants block (lines 359–392): Prettier wants a blank line after each `### CX-…` heading and a deeper
  indent on each `- [x]` item's continuation line. `acp-session-controls.md` fails the same way.

---

## 7 · Size, before and after

`git diff --numstat <base>...<ref>`, by kind, with base `9881d24` before the merges and `1913c58` after them [run;
r2's totals match the figures the Refactorer reported from its own script]:

| Kind | r1, `64b5a8b` | after the refactor, `f4c7ae5` | the top, `6810335` |
|---|---|---|---|
| Code (`src/`, not tests, fixtures or translations) | +2,635 −141 (50 files) | +2,626 −141 (49) | **+2,626 −141 (49)** |
| Unit tests (incl. helpers) | +3,284 −11 (27) | +3,280 −11 (27) | **+3,318 −11 (27)** |
| Playwright specs | +474 (2) | +474 | +474 |
| Mock agent and test mapping | +157 −12 (2) | +157 −12 | +157 −12 |
| Translations, fixture, upstream `specs/`, skill guide | +405 −3 (8) | +407 −3 | +407 −3 |
| **All** | **+6,955 −167 (89); 6,297 non-blank** | **+6,944 −167 (88); 6,287** | **+6,982 −167 (88); 6,318** |

- Since r2, only unit tests moved: +38 lines, 30 from the two pins and 8 from `73d2e1a`; the two lint fixes each
  replace one line.
- After the Gate B fixes (`61b9bdc`, +7,116 −167), the refactor took out 172 lines (2.4 %): code 45 (1.7 %) and unit
  tests 127 (3.7 %).
- Most of the code went from `agent-server-compatibility.ts` (−37), `use-agent-controls.ts` (−11) and
  `type-guards.ts` (−6, now untouched). `use-set-acp-config-option.ts` grew by 14.
- Most of the test lines went from the helper tests and duplicates of §6.3, and from four copies of one wrapper, which
  became `query-wrapper.tsx` (+21).
- At ≈300 lines an hour, Gate C reads the whole diff (7,149 lines changed) in about 24 h, and the code with its unit
  tests (5,944 lines added) in about 20 h. Split into the seven levels, the reading is 7,151 lines (§5.2).
- The largest pieces are now:
  - code: `use-agent-controls.ts` 229, `chat-input-agent-options.tsx` 221, `app-backend-session-keeper.ts` 219,
    `canvas-extensions-runtime.tsx` +213 −19, the conversation service +131 −42;
  - tests: `use-acp-session-preview.test.tsx` 431, `use-agent-controls.test.tsx` 305, `mount-app-backend-frame.test.ts`
    255.

---

## 8 · What I could not verify

1. **App backend frames against a real agent-server.** Every frame and keeper test fakes the client at its boundary.
   No test, and nothing I ran, mints a session on a real ingress or loads a frame in Chromium or Electron.
2. **D-12, D-13 and D-14 end to end.** A live set, its toast, a home refusal and its withdrawal run in unit tests only;
   no live test reaches them (§6.4).
3. **The REST search end to end**, and the history preload's limit: read only.
4. **The drawer's terminal behind an App panel**: the test keeps a mocked stand-in mounted.
5. **Unit isolation and the PR split**: I ran #23's level diff alone on the base, and #26's on #22 and on #20 (§5.2).
   Levels #20–#22, #24 and #25 rest on CI's run of each head; only #26's head ran end-to-end specs (§6.1).
6. **Mutation testing over the diff** (v2 B18): Stryker has still not run. §6.3's probes are ten hand edits aimed at the
   cut tests and the fixes; they find nothing unpinned, which says nothing about what they did not aim at.
7. **The full mock-LLM suite at `6810335`**: nobody has run it; run 37223123058 covers C2's and C1's four specs only,
   and §6.1 cites r1's full record at `64b5a8b`.
8. **The full vitest suite locally**: not run by me, per the brief. CI's run is green, and the agent that made the
   fixes reports 781 files and 8,376 tests passing locally after a fresh `npm ci`, the same totals [read: its report].
9. **D3 inside Canvas**: read only. C2 against the SDK fork's `deep-reasoning` now runs in CI and the live tier (§6.1).
10. **The capability gate's timing**, and `useLatestAcpSessionControls` returning a cached search while disabled
    (D-17): both read only.
11. **Which agent-server the live tier ran.** Its log does not print the commit; `34c540c` is read from
    `defaults.json` and the launcher, and supported by C2's two home-preview tests needing a `/preview` route that the
    SDK's `v1.50.1` lacks.
12. **The `dr-2` tarball's build.** Its digest matches the release asset, whose body says it was built at `34c540c`;
    I did not rebuild it from that commit.
13. **The base's install.** The top's runs used a fresh `npm ci`. The base worktree's `node_modules` hard-links it,
    on the same lockfile blob, and r3's first pass at `ca1dd71` used the Splitter's install (Evidence marks).

What resists shortening is §2, §5.2 and §6.3. The code follows v2 closely in shape. What moved is concentrated in the
refusal paths (D-12 to D-15), in what the tests pin (D-18, §6.3), and, since r2, in the base and the split (D-20,
D-21). Of the three properties r2 found unpinned, all are now pinned: P5 by `667ec86`, P6 by `a1ec3d1` and P2 by
`73d2e1a`.
