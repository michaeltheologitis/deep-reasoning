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

**Revisions** (newest first; the Gate B reader approved the previous version, so each line says which sentences to
stop trusting):
- 2026-10-02 · v1 · first full-depth version.

**Where this file lives, and why nothing trips over it.** `docs/design/c2-header-panels-and-menus.md` on
deep-reasoning's branch `design/c2`. That branch holds only documents: no docs site, no `pyproject.toml`, no test
runner, no package, so nothing collects, builds or ships this file. No design document goes into the fork: its pull
requests carry code, tests, translations and upstream's own product specs (`specs/*.md`, which upstream keeps
beside the code and tags with `// @spec` ids; §4.9, §5.8), in upstream's layout. The PR split leaves this file
behind.

**Reading guide.** Gate B: §1 to §3 (what C2 changes, the decisions, and every departure from the approved spec),
then §10 (how E11 and the test layers are proven). D3's designer: §7 is the contract D3 builds against; read §6 with
it, because it is how a panel page reaches its own backend. The Conductor: §3, §8 (what S2 must change) and §11
(open items, two of which are not C2's to settle). The Implementer reads everything; Appendix A is the signature
reference, Appendix B the new translation keys, Appendix C the end-to-end agent's flags.

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
| **3 · App backend frames** (proposed, §6; the Conductor rules) | `host.appBackend.mountFrame(container, {path, title})`: the App's own backend, served through the agent-server's App ingress, in a sandboxed frame whose session the host keeps alive. | the agent-server's existing App-backend bridge (`canvas_app_backend_bridge_v1`); the TypeScript client's existing `CanvasExtensionsClient` | D3's pages, to reach D2's Library API |

PR 3 exists because the spec's D3 says the Library API is reached "bridged by the agent-server under
`/app-backends/dr-library`", and that bridge is reachable only through a separate browser origin with a cookie
session a page cannot bootstrap without the session key (§6.1). Without it, D3 has no way to write to its backend.

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
  newest ACPSessionControlsEvent (WebSocket, else one REST search by kind) → picker row + slash menu
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
| M | **The agent's refusals are shown in its own words**, read from the agent-server's `detail` by one small helper. | S2 passes the agent's sentence through as `detail` (D1's `namespace is fixed once a conversation has started (it is 'router').`); the client's `HttpError` message wraps it in `HTTP request failed (422 …): {"detail": …}`, which no user should read. | A generic "the agent refused" toast. |
| N | **(PR 3, proposed) An App's backend is reached only in a host-owned, sandboxed frame on the agent-server's App ingress origin; the host keeps one ref-counted session per App alive.** | It is the bridge's own design (§6.1): a separate origin, a cookie session minted with the session key, non-GET requests only from that origin, a five-minute session. The host holds the key and can refresh; a page cannot. One session per App, because the cookie is per App and revoking one page's session would cut every other frame of that App. | Handing the page a session creator and letting each App refresh and revoke: every App re-implements the same timer, and a revoke on one tab's dispose kills its siblings. Calling `/app-backends/…` through `host.agentServer.request`: the bridge answers 421 or 503 on the agent-server's own origin. |

---

## 3 · Where this design departs from, or adds to, the approved spec

Each item is a refinement inside C2's scope unless marked otherwise; if the Conductor reads any as a change of what
was approved, it goes back to Michael.

1. **A third pull request, App backend frames (§6), is outside C2's approved scope** and is proposed for the
   Conductor's ruling. Why: the spec's D3 reaches D2's API "bridged by the agent-server under
   `/app-backends/dr-library`", and the bridge works only through a separate ingress origin with a cookie session
   that only a holder of the session key can mint (§6.1); a page has no key. Without PR 3 (or another ruling), D3
   cannot save a decomposition. The bridge also needs the desktop app to configure an ingress origin, which no
   launcher does today (§11 item 1, for D5 and C3).
2. **The estimate grows from ≈1.1k to ≈2.1k LOC with tests (≈5.5 h at Gate C instead of ≈3.5 h).** PR 1 ≈1.0k (the
   slot ≈600, tests ≈400 including one end-to-end spec), PR 2 ≈0.85k (≈500 and ≈350, with the mock agent's
   flags and one end-to-end spec), PR 3 ≈0.27k. Why: the spec costed neither the end-to-end specs (its §4 layer 5
   makes them C2's Gate B evidence), the persisted tab state's sanitizer and narrow-window page, the extraction
   that makes the preview body equal the start body (decision I), nor PR 3.
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
    design document.

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
- `notices: ReadonlyMap<string, string>`, keyed by App name like `errors`.

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
one `ConversationAppPanelToggle` per registered panel, in `panels` order.

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
column:

```tsx
<div className="flex flex-col flex-1 min-h-0 bg-surface border-l border-border overflow-hidden">
  <div className={cn("flex flex-1 min-h-0 flex-col", appPanel && "hidden")}>
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
an icon it always shows its label (one changed prop and one condition in `conversation-tab-nav.tsx`). The row
scrolls horizontally when the tabs do not fit (§3 item 4). Clicking a tab that is not selected selects it;
clicking the selected tab closes the panel (§3 item 5). `data-testid="conversation-app-panel-tab-<tab id>"`.

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
`div` with `className="h-full min-h-0 overflow-auto"` and `data-testid="conversation-app-panel-content"`. While the
App is still activating it shows `LoadingSpinner`; when the tab's mount throws or rejects, or the App's activation
failed, it shows the route page's unavailable state (`SETUP$UNAVAILABLE_TITLE` with the error, as
`canvas-extension-page.tsx:85–99`).

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
  after.
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

### 4.8 The demo-panel fixture

`src/fixtures/canvas-extensions/demo-panel` is a dependency-free App like upstream's `demo-page`, used by the unit
tests, the end-to-end spec and MSW mock mode (`canvas-extensions-handlers.ts` serves it beside `demo-page`):

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
DOM. `demo-page` is left untouched, so upstream's existing Apps end-to-end spec is unaffected.

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
as-built.

---

## 5 · PR 2: agent commands and the option picker

### 5.1 The gate

`src/api/agent-server-compatibility.ts` gains `localAgentServerHasCapability(capability)` (true only for a local
active backend whose cached `/server_info` lists the string) and `getSdkHttpErrorDetail(error)` (the `detail` string
of an SDK `HttpError`'s parsed body, else `null`). Agent controls exist when the backend is local, the agent-server
has `acp_session_controls_v1`, and the context is ACP: on the home screen `useAcpModelContext().isHomeAcp`
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
  `EventService.searchEvents(id, null, null, {kind: "ACPSessionControlsEvent", sortOrder: "TIMESTAMP_DESC", limit: 1})`
  whose first matching item is kept. Newer is by ISO timestamp, the event store's own ordering
  (`use-event-store.ts:28–40`). No event at all means no commands and no picker (S2 §7 item 4).
- **Options shown** = `config_options` without `id === "model"` (S2 §7 item 6; the model picker owns it) and without
  `type === "boolean"` (§3 item 10).
- **Setting** uses `useSetAcpConfigOption` (`meta: {disableToast: true}`): while pending, the pill shows the chosen
  value with a spinner and is disabled; on success nothing else is done (the agent-server publishes the next event,
  which replaces the controls); on failure, `displayErrorToast(getSdkHttpErrorDetail(error) ?? message)`, so a 422
  shows the agent's own sentence. `applied: false` cannot arise from this UI (no picker exists before the session's
  first controls event).

### 5.4 On the home screen

`useHomeAgentControls({workingDir, workspaceMode})` (Appendix A.10), called by `HomeChatLauncher` with its pending
workspace (`undefined` when none or when the backend isolates the workspace, as the start does at `:122`):

- **The launch agent's key** is `${backendId}:${orgId}:${profile id or "agent-settings"}`. The values the user picked
  live in `useHomeAgentOptionsStore` (new, session-only), stored with the key they were picked under; values under
  another key are ignored (derived, no effect), so a backend switch or another active agent starts from the agent's
  defaults.
- **The preview** is `useAcpSessionPreview(...)`: a query keyed by
  `ACP_SESSION_CONTROLS_QUERY_KEYS.preview(launchKey, workingDir, workspaceMode, values)`, whose function calls
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
  `eslint-disable` exception, or a CSS pseudo-element).
- Selecting an item still inserts `"/<name> "` (`:213–266`); the message is sent as usual, and S2 passes its text
  through unchanged.
- The list is replaced whenever `agentCommands` changes, never merged, so an agent that clears its commands (dr-acp
  at its first prompt) disappears from the menu with the next event (`ASC-001`).

### 5.6 The picker row

`ChatInputAgentOptions` (new, `src/components/features/chat/components/chat-input-agent-options.tsx`) renders in
`ChatInputContainer` (`chat-input-container.tsx:82`) after `UploadedFiles` and before the input row, only when
`controls.options` is non-empty: a `flex flex-wrap gap-2` row with `aria-label={t(CHAT_INTERFACE$AGENT_OPTIONS)}`,
one pill per option, in the agent's order.

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
commit (§9).

### 5.8 Tests for PR 2

`specs/acp-session-controls.md` (new, upstream's format, `specs/backend-management.md`):

- **ASC-001:** The slash menu lists exactly the commands of the agent's newest report; a new report replaces the
  last.
- **ASC-002:** The option values a conversation starts with are values the home screen's preview accepted.
- **ASC-003:** The option picker never offers the model option; the model picker owns it.
- **ASC-004:** Agent commands and options appear only where the local agent-server advertises
  `acp_session_controls_v1`; elsewhere the composer is unchanged.

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

`npm run test:mutation:diff` runs on this PR too.

---

## 6 · PR 3 (proposed): App backend frames

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
  `scripts/`, `electron/` or `docker/`).

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
   `{reason, message}`: `not-ready` for a 503 whose detail says the backend is not ready, `session-refused` for 401,
   403, 409 and 421, `unsupported-backend` on Cloud.
5. Returns a synchronous disposer: aborts a pending acquisition, removes the frame or notice, releases the lease.

### 6.3 The session keeper

`src/extensions/app-backend-session-keeper.ts` keeps one session per `(backend id, App name)`:

- The first lease creates the session (`CanvasExtensionsService.createAppBackendSession`, through
  `CanvasExtensionsClient` with `appBackendIngressUrl`, `credentials: "include"`) and schedules a refresh at
  `expires_at − 60 s` (never sooner than 10 s from now). A refresh mints a new session, whose cookie replaces the
  old one for every frame of that App; frames keep running. A failed refresh reports `session-refused` to the
  App's live frames (each shows its notice).
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
  says which namespace the conversation runs in, which Create decomposition could offer as the default.

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
  and which are pinned, per conversation. Errors from `mount` show Canvas's unavailable state in the panel.

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
  sets today (§11 item 1). Without it `mountFrame` reports `no-ingress`.
- **Without PR 3** there is no supported way for a D3 page to write to D2's API (§6.1); D3 should not be designed
  around the Library API until the Conductor has ruled.

---

## 8 · What C2 needs from S2

C2 builds on S2's §7 as written, with these points:

1. **Must change (small): export the controls types from the client's package root.** C2 imports
   `ACPAvailableCommand`, `ACPCommandInput`, `ACPConfigOption`, `ACPConfigOptionValue`, `ACPConfigOptionValues`,
   `ACPConfigOptionSetResponse`, `ACPSessionControls`, `ACPSessionControlsEvent` and `isACPSessionControlsEvent`
   from `@openhands/typescript-client`. S2's Appendix B puts them in `src/models/acp-session-controls.ts` and
   `src/events/types.ts`; its `src/index.ts` must re-export them (as it does `ACPModelOption` and
   `ConversationErrorEvent`), or Canvas would have to import from internal paths the package's `exports` map does not
   expose.
2. **No change, a usage note:** C2 does not call `getAcpSessionControls`; it searches the newest event itself through
   Canvas's `EventService`, because it must compare that event's timestamp with live events (decision H). The client
   method can stay for other consumers.
3. **Optional, not for v1:** a preview for an existing conversation whose session has not started
   (`POST /api/conversations/{id}/acp/preview`), which would give conversations created without a first message a
   picker (§3 item 11).
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
| `package.json` / `package-lock.json` (`@openhands/typescript-client`) | the wiring commit (Q2 (a)) | PR 2 needs a client built from an SDK fork tag that carries S2 PR 1; PR 1 and PR 3 need no new client API (PR 1 uses `AgentServerClient.get`, PR 3 the existing `CanvasExtensionsClient`). For each PR's upstream-shaped draft branch on our fork's `main`, PR 2's first commit is the client bump (upstream's rule: release the client, then bump the pin) |
| `conversation-main.tsx`, `conversation-store.ts` | upstream (the spec's merge-conflict note) | small, local hunks |
| `chat-input-container.tsx`, `home-chat-launcher.tsx`, `custom-chat-input.tsx` | upstream `a8c8fb3` (voice dictation) touches `chat-input-container.tsx` and `chat-input-actions.tsx` | C2 adds one render line and one prop in the container and leaves the actions row alone (decision K), so the next upstream merge conflicts in at most one hunk |
| `scripts/`, `electron/`, `config/defaults.json` | C3 | C2 touches none of them |

**Order.** PR 1 can be built and unit-tested now; its end-to-end spec needs an agent-server with S2 PR 2 (through
the wiring commit's tag). PR 2 needs S2 PR 1 and its client. PR 3 needs nothing new from S2, but is useful only once
a launcher configures the ingress (§11 item 1).

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

**The layers.** Layer 3 (inside the fork): §4.9, §5.8 and §6.4, in upstream's folders and style, plus upstream's
full vitest and Playwright suites green on `feat/agent-surfaces` and on `deep-reasoning` after merge, and `npm run
lint`, `npm test`, `npm run build` and `npm run build:lib` (upstream's verification commands) green. The mock-LLM
workflow does not run on pull requests (`.github/workflows/mock-llm-e2e.yml:3–6`); the Implementer runs it by
`workflow_dispatch` on the task branch, where the wiring commit makes it start our agent-server. Layer 4 (the real
desktop app with dr-acp, in deep-reasoning's CI) is D5's E12: it picks a namespace, opens Show decompositions and
uses the slash menu through C2.

**The live tier (Gate B's evidence).** The spec's §4 layer 5 makes C2's evidence its end-to-end tests, "Playwright
written as tests that assert behaviour": the two specs above, green in the fork's mock-LLM run at the branch's head.
No real model is involved: the agent is the scripted mock ACP agent, and dr-acp's own behaviour behind these
surfaces is asserted by S2's live tier and D5's flow.

---

## 11 · Open items for the Conductor

1. **Not C2's to settle: the App ingress for the desktop app (D5, C3).** The App-backend bridge needs the agent-server
   started with `OH_APP_BACKEND_PUBLIC_URL` naming an origin distinct from Canvas's, which the browser can reach and
   which reaches the agent-server with its own `Host` intact (for example `http://localhost:<agent-server port>`
   while Canvas is served from `http://127.0.0.1:<port>`; the agent-server's CORS allows both loopback names with
   credentials, `middleware.py:34–60`). Whether a `Secure; Partitioned` cookie on `http://localhost` inside a frame
   under `127.0.0.1` behaves in Electron's Chromium is unverified here; D5's end-to-end flow settles it. Without this,
   D3's panel can show nothing from D2.
2. **Rule on PR 3** (§3 item 1, §6). Recommended: approve; it is the host half of the bridge upstream already ships.
3. **Rule on the estimate** (§3 item 2).
4. **S2's item 1 in §8** (root exports) goes to S2's Implementer through you.
5. **Unverified until the Implementer runs it:** that the drawer's terminal survives being hidden behind an App
   panel with `display: none` (decision C; a test asserts its node and session survive); that the guillemet glyph in
   the menu row passes upstream's lint (else a CSS pseudo-element, §5.5).

---

## Appendix A · Signature reference (TypeScript)

Valid TypeScript in declaration form, as a `.d.ts` would state it: `declare` marks a signature whose body the
sections above specify; `// …existing…` marks members that do not change; one field per line; paths relative to the
fork's root. Imports are shown where a name comes from outside the file; the fork's own names (`Backend`,
`WorkspaceMode`, `AgentKind`, `InstalledCanvasExtensionInfo`, …) are imported from where they live today.

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
  /** Show the App's own backend in a sandboxed frame filling the container. */
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
  /** Per App: a condition that is not an activation failure (e.g. panels unsupported). */
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
  ): Promise<AgentServerAppBackendSessionResponse>;

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
    workspaceMode: WorkspaceMode,
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
};
```

### A.7 `src/api/agent-server-compatibility.ts` (additions; PR 1, used by PR 2 and PR 3)

```ts
export type AgentServerCapability =
  | "acp_session_controls_v1"
  | "canvas_conversation_panels_v1"
  | "canvas_app_backend_bridge_v1";

/** True only for a local active backend whose cached /server_info lists the capability. */
export declare function localAgentServerHasCapability(
  capability: AgentServerCapability,
): boolean;

/** The agent-server's `detail` sentence from an SDK HttpError, or null. */
export declare function getSdkHttpErrorDetail(error: unknown): string | null;
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
  /** Filter: only events of this kind. */
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

export interface HomeLaunchContext {
  /** The pending workspace's path; undefined for none or an isolated backend. */
  workingDir: string | undefined;
  workspaceMode: WorkspaceMode;
}

export declare const NO_AGENT_CONTROLS: HomeAgentControls;

export declare function useHomeAgentControls(
  launch: HomeLaunchContext,
): HomeAgentControls;

export declare function useConversationAgentControls(
  conversationId: string | null,
): AgentControls;

// src/hooks/query/use-acp-session-preview.ts
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
