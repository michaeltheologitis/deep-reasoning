# D3 · Decompositions panel — design

**TASK-8** · System Designer · task branch `v1-decompositions-panel` in
[deep-reasoning](https://github.com/michaeltheologitis/deep-reasoning) (this file is written on `design/d3`) ·
against the approved spec [TASK-1](https://app.notion.com/p/3ed62fb22237814ab425c81b3844f012) (D3 in full; D2, D4, D5
and C2 where they meet the panel; §4's E8 note, E11 and the testing layers; the dated notes at its end).
**Pinned against:** C2's design at deep-reasoning `72aa49f` (§6 and §7 are D3's host contract; PR 3, App backend frames,
approved by Michael on 2026-10-03) · D2 as built on `v1-library-store` at `5158693` (its design `555472b`, §6, is the
data contract) · D5's design `8086afb` (§4.6, §4.9, §8.3) · S2's design `9e32261` (§5, the manifest) · D1's design
`f281109` (§2, §4.6) and its harness on `v1-dr-acp` at `21c2c7a` · SDK fork `deep-reasoning` at `91430aa` (the App
backend manager and bridge; every agent-server `file:line` below) · Canvas fork `deep-reasoning` at `02b7ac7` ·
deep_reasoner_beta `d7334ae`.

**Revisions** (newest first; each line says which sentences to stop trusting):
- 2026-10-03 · v1 · first full-depth version. Folded in before it: Michael's yes to C2's PR 3; D5's four proposals to D3
  (§8.3 of D5, settled here in §8.4); C3's approved launcher default for the App ingress
  (`http://127.0.0.1:<agent-server port>`, Canvas's window on `http://localhost:8000`); D2's API as built (403 for a
  foreign `Host`, 415 for a non-JSON `PUT` or `POST`, 400 for an unknown body field, and a `PUT` that omits `use_when`
  or `hint` erases it).

**Where this file lives, and why nothing trips over it.** `docs/design/d3-decompositions-panel.md`. The `design/d3`
branch holds only documents. On `v1-decompositions-panel`, which carries D1's `pyproject.toml`, pytest collects
`tests/` only, the wheel is built from `src/deep_reasoning`, the sdist excludes `docs/`, and ruff excludes `docs`
(D1 §8.5). D3's TypeScript tools (`tsc`, `vitest`, `prettier`) run inside `canvas-app/` only (§4.1), so they never see
`docs/`. The PR split leaves this file behind.

**Reading guide.** Gate B: §1 (what D3 is and its decisions), §2 (the panel tab by tab, as the user meets it) and §3
(departures from the spec): about 25 minutes. D4's designer: §8.3, D4's contract, then §2.5 and §4.4. D5's designer:
§8.4 (D5's proposals, settled, and what D5 must do) and §4.6. C2's and D2's: §8.1 and §8.2. The Implementer reads
everything; Appendix A is the signature reference, §4.7 every user-visible sentence, §7 the tests.

**What was verified for this design (2026-10-03, in a scratch directory outside every repository):**

1. **The frame, end to end, with D2's real backend.** Headless Chromium 153 (Playwright 1.63; the Playwright CDN is
   blocked from this sandbox, so a Chromium build from npm), a Canvas stand-in page on `http://localhost:A`, a replica of
   the agent-server's App ingress and bridge on `http://127.0.0.1:B` (the cookie's attributes, the `Host` and `Origin`
   checks, the header filter and the redirect refusal copied from `canvas_extensions/bridge.py` and
   `docker_runtime/proxy.py`), and D2's own `dr-library serve` (`5158693`) on `127.0.0.1:C`, started with only `PATH` and
   `LANG` as the backend manager would. The page minted the session with a credentialed `fetch` and appended a frame
   with the bridge's sandbox and `referrerpolicy="no-referrer"`. In the frame, with relative URLs: `GET ../namespaces`
   200; `POST ../validate` (JSON) 200 with `slug`; `PUT ../decompositions/probe-x` (JSON, with `use_when`, `hint`,
   `namespaces`, `base_version: 0`) 201 version 1; the same again 409 `conflict` carrying the head; the same `PUT` with
   `Content-Type: text/plain` 415. So the `Secure; HttpOnly; SameSite=None; Partitioned` cookie set by the page's
   cross-site `fetch` is sent by the frame; the frame's writes carry the ingress `Origin`; **D2's `Host` check holds
   through the bridge** (it saw `127.0.0.1:C`) and **its JSON check holds** (`Content-Type` arrives unchanged). Directly,
   with `Host: evil.example:C`, D2 answered 403. `postMessage` from the frame reached the page with
   `event.source === iframe.contentWindow`, and `location.ancestorOrigins[0]` in the frame was Canvas's origin.
2. **What `Host` the backend sees, from the code.** The bridge forwards to `http://127.0.0.1:<port>` (`bridge.py:366–369`,
   the endpoint `backend.py:638–643` returns), drops the browser's `Host` (`proxy.py:48`, "recomputed by httpx") and
   builds one `httpx.AsyncClient` per request (`proxy.py:136–143`), so the backend sees `Host: 127.0.0.1:<port>`, the
   value D2 accepts (`api.py:90` as built). `Content-Type` is not in the hop-by-hop set (`proxy.py:32–51`). The health
   probe uses the same address (`backend.py:420`).
3. **YAML 1.1 in the browser reads as PyYAML reads.** `yaml` 2.9.1 with `version: "1.1"`, `uniqueKeys: false` against
   PyYAML (D2's environment) on `yes`, `on`, `0777`, `2024-01-02`, `1:30`, a duplicated key and a literal block: equal
   values; what it writes back (`"yes"` quoted, a date as `2024-01-02`, a multi-line string as `|`) PyYAML reads to the
   same values.

Not verified here: Electron 43's Chromium (D5's E12 step 5 runs the real app), and the agent-server's own bridge code
in a browser (the probe replicated it; E12 uses the real one).

---

## 1 · What D3 is

The Library (D2) holds the user's decompositions, namespaces, tools and run settings. D3 is the part of the app where
the user sees and changes them: a Canvas App, `dr-library`, whose header panel (C2) puts **Show Decompositions** at the
top right of a conversation, after Show overview and Show panel, and opens a panel the way Show panel opens the drawer,
with four tabs: **Decompositions** (by namespace), **Create decomposition**, **Namespaces** and **Tools**.

The App has two halves, because of how the agent-server lets an App reach its backend (C2 §6.1, verified above): only
from a separate browser origin, inside a frame, with a five-minute cookie session that only Canvas can mint.

- **The page bundle** (`dist/index.js`, about 300 lines) runs in Canvas's own page. It registers the four tabs, and for
  each mount it makes sure the backend runs, reads what only Canvas can read (the conversation's namespace, the spend
  cap, the theme), and asks Canvas to show the frame (`host.appBackend.mountFrame`, C2 PR 3).
- **The frame UI** (`ui/`, a small Preact app) is served by the backend itself, `dr-library serve`, from files built
  into the deep-reasoning wheel, and talks to D2's HTTP API same-origin, through the bridge.

```text
Canvas window, http://localhost:8000 · C2's header panel "decompositions", tab "create", conversation c1
  dr-library dist/index.js · mount({container, conversationId: "c1", surface})
    1  "Opening the Library…" in the container
    2  GET  /api/canvas-extensions/installed/dr-library/backend                          host.agentServer.request
         stopped or unhealthy, prepared revision = revision → POST …/backend/start {revision}   (≈2 s of imports)
    3  GET  /api/conversations/c1/events/search?kind=ACPSessionControlsEvent&…&limit=1      → namespace, started
       GET  /api/agent-profiles/deep_reasoner                                              → the spend cap
       getComputedStyle(container)                                                         → Canvas's theme
    4  host.appBackend.mountFrame(container, {path: "/ui/?tab=create&namespace=router&started=1&cap=5&parent=…&theme=…"})
         C2: session cookie for http://127.0.0.1:18000 → <iframe src="http://127.0.0.1:18000/app-backends/dr-library/ui/?…">
  the frame, http://127.0.0.1:18000 (another origin and another site than Canvas's)
    GET  ui/ · ui/assets/app.js · ui/assets/app.css     ── bridge ──▶ dr-library serve: D3's files, from the wheel
    GET  ../health · ../namespaces · ../effective · …   ── bridge ──▶ dr-library serve: D2's API
    PUT  ../decompositions/<slug>  {yaml, use_when, hint, namespaces, base_version}   (JSON; Host 127.0.0.1:<port>)
    postMessage(parent, {type: "dr-library/select-tab" | "dr-library/reload"})        → surface.selectTab | remount
```

What happens after a save, which is the point of the panel (spec D3, and E8's one surviving check):

```text
Create decomposition → PUT /decompositions/rank-by-prerequisites {…, namespaces: ["course_advisor"], base_version: 0}
   D2: revision 7 · "rank by prerequisites" v1 · course_advisor v4 (its list gains the name)
the open conversation: unchanged; its run was materialized at its first message (D1 §2 step 4)
the next conversation in course_advisor:
   home screen → S2's preview → dr-acp session/new → LibraryCatalog.snapshot() → the slash menu offers
     /rank-by-prerequisites  ordering courses by what they need first  ‹the task›           (C2 refetches on return)
   first message → LibraryCatalog.materialize → run.start.source.versions.decompositions["rank by prerequisites"] = 1
   every agent running in course_advisor sees it among its worked examples
```

### 1.1 Decisions this design takes

The spec's seven decisions in §2 stand, and so do C2's and D2's. These are the next layer down.

| # | Decision | Why | Rejected |
|---|---|---|---|
| A | **The UI is a frame served by the App's own backend; the App's registered tab pages only prepare and mount that frame** (`host.appBackend.mountFrame`, C2 PR 3, approved). | The bridge admits a request only on the ingress origin, with that App's cookie, and a write only with the ingress `Origin` (`bridge.py:296–301, 448–472`); a page in Canvas's realm has neither the session key nor that origin. The frame is the bridge's own model, and C2 keeps its session alive. | The UI in Canvas's realm calling the backend: every write is refused (403 or 421). Calling `dr-library serve` directly on its loopback port with CORS: bypasses the authenticated bridge, and the port changes on every start. |
| B | **One frame UI for all four tabs, chosen by `?tab=`; every tab mount loads a fresh frame.** Unsaved edits are drafts in the frame's `localStorage`. | C2 mounts an App tab only while it is visible and disposes it on every switch (C2 decision C, §7.3), so state in the frame dies with it; a draft keyed by what is being edited survives a tab switch, a conversation switch and a restart. One bundle keeps the build and the cache simple. | A frame per tab with its own bundle (four builds of shared code). Keeping one frame alive across tabs (C2 owns the mount lifecycle; a detached iframe reloads anyway). |
| C | **Preact and TypeScript, built by Vite; plain `<textarea>`s for code and YAML; `yaml` (eemeli) in YAML 1.1 mode.** Runtime dependencies: `preact`, `yaml`. | The built files are committed (decision D), so every byte is carried in the repository's history: Preact gives React's component model, which C1's and C2's maintainers read daily, in about 4 KB. D3's editing is YAML values and short code cells, which a monospace textarea serves. YAML 1.1 is what PyYAML, and so `dr`, reads: `on`, `yes`, `0777`, `1:30` mean the same in the panel as in a config file (verified). | React (≈45 KB more in every committed build). CodeMirror 6 for D3 (the spec's §2 candidate; ≈100 KB+): D4 may add it behind `CodeField` for Python (§8.3). A YAML 1.2 parser (`on` would become a string the user's `dr` config would read as `true`). No framework (about twice the code for the forms). |
| D | **The built App ships in the deep-reasoning wheel as package data under `deep_reasoning/canvas_app/`, committed; CI fails if a fresh build differs** (D5's proposal, accepted). `dr-library serve` serves the frame UI from the same package, at `/ui/`. | A user's machine builds the wheel from git with hatchling and has no npm (D5 §4.4.3). Serving the UI from the installed package means D5's backend command stays `dr-library serve --port {port} --home <home>` (no new argument), and a UI-only change needs no new App approval. | A build hook running npm at install (network, minutes, node_modules on every user's machine). Shipping the UI inside the App's backend artifact (D5 builds that artifact per machine from the runtime, D5 decision G; it would only copy the same files). |
| E | **The page computes everything only Canvas can know and passes it in the frame's URL**: the tab, the conversation's namespace and whether it has started, the spend cap, Canvas's theme tokens, an entry to focus, and Canvas's own origin. | The frame cannot call the agent-server (C2 §7.4) and cannot read Canvas's styles (another origin). A URL is inspectable and testable; the query string reaches the backend, which ignores it for `/ui/`. | `postMessage` after load (an ordering protocol for data that does not change during a mount). |
| F | **The page makes sure the backend is up before every mount, and may start an already approved revision; it never approves one** (D5's proposal, accepted, §8.4). | Backends do not survive an agent-server restart, and one can die (D5 §1.1 G). `ready_endpoint` reports a dead process as ready until someone asks for its status (`backend.py:309–332, 638–643`), so the page asks first; `start` with the prepared revision is no new consent, while `prepare` is the approval D5's setup gives. | Leaving a dead backend to the next app launch. Calling `prepare` from the panel (approving code the user did not install). |
| G | **The frame speaks to the page with two messages, `select-tab` and `reload`, and the page accepts a message only from its own frame's window.** | Moving to another tab after a save (C2's `surface.selectTab`), and asking for a remount when the backend stops answering, are the only things the frame needs from Canvas. Checking `event.source` against the frame's `contentWindow` admits nothing else. | A richer RPC (nothing else needs it). |
| H | **Every write carries `base_version`, and a decomposition write always carries `use_when` and `hint`.** Namespace and profile edits change the record's own YAML document (parsed, edited, written back); decomposition saves send JSON text. | D2's optimistic concurrency needs the version the edit started from (D2 decision L); D2 as built erases `use_when` and `hint` when a `PUT` omits them (§2.3's rule), so the panel never omits them. Editing the parsed document keeps every key the panel does not show; JSON is YAML (D2 §2.2), and a decomposition is strings only. | Sending only changed fields (D2's API replaces). Writing namespace YAML by string templating. |
| I | **A namespace edit saves on its own action** (Override, Reset, a grant, an attach): one revision each, no form-level Save. | Each action is one sentence in the Library's history and one conflict to resolve; a half-edited namespace never exists. | A namespace form with one Save (a stale-version conflict would cover unrelated fields). |
| J | **The card editor maps one message to one card, and a message that does not render back to exactly its own text is a raw card.** | Losslessness by construction: opening and saving an imported decomposition never changes a byte the user did not touch, so it never makes a spurious version. | A turn-shaped model that merges messages (a lossy parse; spurious versions on every save of an imported example). |
| K | **Live data by polling `GET /health` for `rev` every 3 s while the frame is visible**, refetching the tab's data when it moves. | D2 pushes nothing (D2 §6.1); a save in another conversation's panel, an import or `dr-app` must show up. | A WebSocket (the bridge cuts it at the session's expiry, C2 §7.4). |
| L | **Behaviour tests are pytest with Playwright (Python) against a real `dr-library serve`; logic is unit-tested in vitest.** | D1's ACP harness, D2's Library and D5's `dr_app.texts` are Python, so the E8 test (UI save, then `dr-acp`'s next conversation) is one Python test; Playwright is already in the dev group (D5 §4.1). Pure logic (cards, YAML, the frame protocol, the page's backend and context checks) is faster and sharper in vitest, with the outside world (the host API, `fetch`) faked at its boundary. | Playwright for TypeScript (a second runner and a second harness for `dr-acp`). |
| M | **At the top level (no parent window) the frame shows its own tab row.** | Tests and developers open `http://127.0.0.1:<port>/ui/` directly, against the same backend, with every tab reachable. In a panel the tab row is Canvas's. | A separate developer page. |

### 1.2 What D3 owns, and its seams

- **Owns:** `canvas-app/` (the TypeScript project: the page bundle, the frame UI, their unit tests and build); the App
  package `src/deep_reasoning/canvas_app/` (the manifest, the icon, and the built files, committed);
  `src/deep_reasoning/library/ui.py` (serving `/ui/`); `tests/canvas_app/` (behaviour tests, E8) and
  `tests/library/test_ui.py`; the `canvas-app` CI job.
- **Seam to C2** (C2 §6, §7): `registerPage(<tab id>, mount)`, the mount context's `conversationId` and `surface`,
  `host.appBackend.mountFrame`, `host.agentServer.request`. No change to C2; one statement asked of it (§8.1).
- **Seam to D2** (D2 §6 as built): the HTTP API, unchanged. D3 adds `ui_routes()` to D2's route list (one line in
  `api.py`) and two sentences to `texts.py` (§8.2).
- **Seam to D4** (§8.3): the Tools tab, `LibraryClient`, the shared components, the frame parameters.
- **Seam to D5** (§8.4): the App package D5 stages, the safety notice's text, the backend restart.
- **Seam to S2** (S2 §5.1): the manifest's `contributes.conversation_panels`, as S2 validates it.
- **Seam to D1**: none at run time; the E8 test drives `dr-acp` through D1's test harness (§7.4).

---

## 2 · The panel, tab by tab

The panel is the drawer's column (20–70 % of the conversation area, resizable), so every view is designed for about
320 px and up: one column, stacked, scrolling inside the frame.

### 2.1 Opening it

**The button.** Canvas draws it from the manifest (C2 §4.3): the panel's icon, tooltip "Show Decompositions" (C2's
`Show {{title}}`, with the title the spec's and S2's manifests use).

**The page, while the frame is not there yet.** Each mount writes "Opening the Library…" into the container, then:

| Backend status (`GET …/installed/dr-library/backend`) | The page |
|---|---|
| `ready` | mounts the frame |
| `starting` | polls the status every 500 ms, up to 45 s, saying "Starting the Library's backend…" |
| `stopped` or `unhealthy`, and `prepared_revision` = `revision` | `POST …/backend/start {revision}` (it returns once healthy or failed), saying "Starting the Library's backend…"; `ready` → mounts the frame; otherwise `BACKEND_FAILED` with the agent-server's `detail` and **Try again** |
| `stopped` or `unhealthy`, not prepared for this revision | `NOT_APPROVED`, no call made |
| `unsupported`, `missing` | `BACKEND_UNSUPPORTED` with the `detail` (an agent-server without S2 PR 3 on a Mac says "Canvas App backend does not support this platform") |

The two context reads (the conversation's namespace, the spend cap) run beside the status check; either failing is
silently treated as unknown. If `mountFrame` then reports `not-ready` (the backend died between the check and the
session), the page disposes and runs the whole mount once more; every other `onError` reason is C2's notice, already in
the container (`no-ingress`, `session-refused`, `unsupported-backend`). A Canvas without PR 3 (no `host.appBackend`) gets
`NO_FRAMES` instead of an exception.

**The safety notice** (spec D5; D5 §2.3). The first time the frame opens, before anything else, it shows, with one
button:

```text
deep_reasoner runs as you. It can read and change any file you can, and code it writes can find your model
keys on this computer if it tries. Spend through the key proxy stops at $5 per conversation.   [I understand]
```

The sentence is D5's `SAFETY`, verbatim; `$5` is the `--spend-cap-usd` argument of the `deep_reasoner` agent profile
(5 when it is absent, which is `dr-acp`'s own default). With `--no-key-proxy` in the profile's arguments, the last
sentence becomes `SAFETY_NO_CAP` (§4.7). "I understand" is remembered in the frame's `localStorage`; the Tools tab shows
the same sentence permanently, as a banner.

**When the backend stops answering later** (a bridge `502` or `503`, or the session's `401` after C2's renewal failed),
the frame replaces the view's footer with "The Library stopped answering (502). [Restart]" or "The panel's session with
the Library ended. [Reload]"; either button posts `reload`, and the page runs the mount again, which restarts the
backend if it died.

### 2.2 Decompositions

```text
┌ Decompositions │ Create decomposition │ Namespaces │ Tools │ ⋯ ───────────────────────────── (Canvas's row) ┐
│ ⚠ 1 problem in the Library ▸                                                                             │
│ Every namespace's menu                                                                                   │
│   triage nightly          v1   /triage-nightly         starts the nightly triage                         │
│ router                                                                                                   │
│   catalog lookup          v2   /catalog-lookup         one course at a time                              │
│   summarize then rank     v1   /summarize-then-rank    comparing many courses                            │
│ course_advisor                                                                                           │
│   catalog lookup          v2   /catalog-lookup         inherited from root                               │
│ Not attached                                                                                             │
│   old draft               v3   /old-draft                                                                │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

- **Groups,** in this order: *Every namespace's menu* (the top-level decompositions, which D1 offers first in every
  namespace, D1 §4.6; absent when there are none); then each namespace in `GET /namespaces` order (root first), listing
  `GET /effective`'s `decompositions` for it in prompt order; then *Not attached* (live decompositions in no namespace and
  not top level, so nothing in the Library is unreachable).
- **A row:** name, `v<version>`, the slash command `/<slug>`, and the use-when line; an inherited one (its `source` is
  not this namespace) shows "inherited from <source>" instead of nothing, as in the spec's mock-up. Each group folds.
- **If `GET /effective` fails** (a head that no longer validates makes D2's resolution fail), the tab falls back to
  `GET /decompositions` grouped by each record's `namespaces` (attachments only, no inheritance) under
  `EFFECTIVE_FAILED`, and the problems banner says why.
- **Opening one** (a click, or `focus=<slug>` in the URL) shows the decomposition editor of §2.3 for that record:
  the name read-only (a new name is a new decomposition, D2 §4.5), use-when, hint, **Attached to** (a checklist of every
  namespace; checked = the record's `namespaces`; namespaces that inherit it are listed as "also used in … (inherited)"),
  the cards, **View YAML**, **Save** and **Delete**.
  - **Save** sends `PUT /decompositions/<slug>` with `base_version` = the version opened, `namespaces` = the checked
    set (D2's exact-set rule), `use_when` and `hint` as shown. Success: `SAVED_EDIT`.
  - **A stale save** (409, the record moved on) shows D2's `CONFLICT_STALE` sentence with **Reload** (drop my changes and
    open the head) and **Save over it** (`base_version` = the head's version).
  - **Delete** asks inline (`DELETE_CONFIRM`), then `DELETE /decompositions/<slug>?base_version=<v>`; D2 detaches it
    everywhere.

### 2.3 Create decomposition

The spec's mock-up, as built:

```text
Name       rank by prerequisites                 → /rank-by-prerequisites
Use when   ordering courses by what they need first
Hint       the task                              (what the slash command asks for; optional)
Namespace  ( ) root  ( ) router  (•) course_advisor  ( ) health_advisor           (the Library's namespaces)
1  task    Which of CS201, CS310 and CS330 can I take first?
2  think   Each course's prerequisites decide it; look them up, then sort.
   code    order = sorted(cs, key=lambda c: len(catalog[c]['prereqs'])); print(order)
   output  ['CS201', 'CS310', 'CS330']                                  written by you, not run
3  think
   code    FinalAnswer(order)
   [+ turn]                                              [View YAML]   [Save to course_advisor]
✓ Saved 'rank by prerequisites' v1 in course_advisor. New conversations in course_advisor use it; this
  conversation does not, because its run was built at its first message.               [Show in Decompositions]
```

- **The namespace** is picked from the Library's namespaces (`GET /namespaces`), one of them, required. Preselected: the
  open conversation's namespace when the page found one and the Library has it, else the namespace new conversations
  start in (`/health`'s `default_namespace`).
- **The slash command** beside the name is `/` + the `slug` `POST /validate` returns (D2 computes it; the panel never
  slugs by itself).
- **Cards** (§5.1): a new decomposition starts with a task card and one step whose code is `FinalAnswer(...)`. A step
  has think (optional) and code; **+ turn** gives the last step an output card if it has none (the observation the agent
  will see) and adds a new step. Each step and output has a ✕ that removes it; a step's ✕ removes its output too.
  Output cards say "written by you, not run". A message that is not in this form (a system message, an assistant
  message with prose outside `<think>` and `<repl>`, a user message that is neither the task nor an observation) is a
  raw card: its role and its text, editable, labelled `RAW_NOTE`.
- **View YAML** shows the canonical YAML of what would be saved (`POST /validate`'s `yaml`), read-only, with **Edit
  YAML**: the textarea then holds the YAML, and **Edit as cards** parses it back (YAML 1.1) into the name and the cards,
  or stays in YAML with `YAML_SYNTAX` or `YAML_NOT_DECOMPOSITION`. A save from YAML mode sends that text as written.
- **Live validation**: 400 ms after the last keystroke, `POST /validate {kind: "decomposition", yaml}`; D2's errors are
  shown on the card their `loc` names (`messages.3.content` → card 4; `name` → the name field; others above the cards),
  in D2's (deep_reasoner's) words.
- **Save** (§5.2): a name is required (`NAME_REQUIRED`); validate; D2's warnings (today one: `NO_FINAL_ANSWER`) ask
  **Save anyway** / **Cancel**; then `PUT /decompositions/<slug>` with `namespaces: [picked]`, `use_when`, `hint`,
  `base_version: 0`.
  - **201:** the success line (below), the draft cleared, the form reset to a new decomposition; **Show in
    Decompositions** posts `select-tab` with `focus=<slug>`.
  - **409 `conflict` with a head** (the name exists): `EXISTS` — "'catalog lookup' already exists (v2, in router)." —
    with **Save mine as v3** (re-sends with `base_version` = the head's version and `namespaces` = the head's namespaces
    plus the picked one, D2 §6.4) and **Rename** (focuses the name).
  - **422:** D2's message and field errors, on their cards.
- **The success line** says what changed and what did not. When the page reported the conversation as started (its
  `namespace` option has a single value, which is how `dr-acp` fixes it after the first message, D1 §2 step 4), it is
  the spec's sentence, `SAVED_STARTED`. Otherwise (a conversation not started yet, or another agent) it is `SAVED`, which
  is true either way: "New conversations in course_advisor use it and offer it as /rank-by-prerequisites; a conversation
  that has already started keeps the run it began with."
- **The draft** (every field, the cards or the YAML, and the mode) is saved on each change under
  `dr-library.draft.create`, restored on the next mount, and cleared by a successful save or **Discard draft**.

### 2.4 Namespaces

```text
Run settings                                 router                                        ★ New conversations start here
root                                         ───────────────────────────────────────────────────────────────────────────
├ router            ★                        REPL            {type: local}                   From the run settings  [Override]
│ └ router.archive                           Backbone        —                                Not set               [Override]
├ course_advisor                             May spawn into  course_advisor, health_advisor   Overridden here        [Edit] [Reset]
└ health_advisor                             Tools           llm                              Inherited from root
[+ Add namespace]                                            ☐ word_count                                            (grant here)
                                             Variables       (none)                                                  [+ Add variable]
                                             System suffix   —                                                       [Override]
                                             Decompositions  route a course question          Attached here          [Detach]
                                                             route a wellbeing question       Attached here          [Detach]
                                                             catalog lookup                   Inherited from root
                                                             [Attach…]
                                             [Delete namespace]
```

(On a narrow panel the tree sits above the fields.)

- **The tree** comes from the dotted names (`a.b` under `a`; a top-level name under `root`). ★ marks the namespace new
  conversations start in. **Add namespace** takes a name, prefilled with the selected namespace's name and a dot, and
  sends `PUT /namespaces/<name> {yaml: "{\"name\": …}", base_version: 0}`; D2 refuses a bad name or a missing parent in
  its own words. **Delete namespace** asks inline, then `DELETE …?base_version=`; D2's refusals (root, the default, a
  parent) are shown as they come.
- **Each field** shows its effective value (`GET /namespaces/<name>/effective`) and its source, as the spec asks:

  | Field | Rule (deep_reasoner, D2 §4.9) | Source shown | Actions |
  |---|---|---|---|
  | REPL (`repl`), Backbone (`reasoner`) | nearest level wins | "Overridden here" / "Inherited from X" / "From the run settings" (`repl` only) / "Not set" | Override (opens a YAML editor with the effective value) · Edit, Reset (when set here) |
  | May spawn into (`spawn`) | nearest wins; unset everywhere = unrestricted | the same; unset shows "Any namespace" | Override (a checklist of namespaces; none checked = may not spawn) · Edit, Reset |
  | Tools (`tools`) | ordered union down the chain | each tool with "Inherited from X" or "Granted here"; a tool the Library does not define is flagged | a checkbox per Library tool (and `llm` while the run settings set a `model`) for granting here; inherited ones are shown checked and fixed |
  | Variables (`vars`) | shallow merge, child wins per key | each key with its source | per key: Override (an inherited key) · Edit, Reset (a key set here) · Add variable |
  | System suffix (`system_suffix`) | each level's text, joined root to leaf | each part with its level | this level's part: Override · Edit, Reset (a text area) |
  | Decompositions | accumulate; child wins by name | "Attached here" / "Inherited from X" | Detach (attached here) · Attach… (a list of the Library's other decompositions; appended at the end) |

  Override, Edit and Reset change one key of this namespace's own YAML document and save it at once (decision I):
  `PUT /namespaces/<name> {yaml: <document>, base_version: <version>}`. Attach and Detach send the same YAML unchanged
  with `decompositions` = the new list. A stale version (409) reloads the namespace and says so; nothing is retried.
- **YAML values** (REPL, Backbone, a variable) are edited as YAML text and parsed as YAML 1.1, so what the user types
  means what it would mean in a `dr` config; text values (System suffix) are plain text areas.
- **Start new conversations here** on any namespace but the current default: `PUT /profile` with the profile's document
  and `entry_namespace` set to it.
- **Run settings,** the first node, shows the profile's own keys (D2 decision D) except `entry_namespace`: each with Edit
  and Reset, and **Add setting** offering the spec's seven (`model`, `models`, `reasoner`, `system_prompt`, `max_iter`,
  `max_depth`, `repl`) or any name. `model` and `system_prompt` edit as text, everything else as YAML. D2 refuses
  `namespaces`, `decompositions` and `tools` there in its own words (`PROFILE_PART`).

### 2.5 Tools (D3's part; D4 extends it)

```text
⚠ deep_reasoner runs as you. … Spend through the key proxy stops at $5 per conversation.
word_count     v1   factory make · tools/word_count.py            granted in  course_advisor
rag            v2   factory make_rag                              granted in  root
```

The banner is permanent (D5 §2.3). The list is `GET /tools`: name, version, the block's `factory` (and `factory_from`
when the tool has a source), and `granted_in`. Writing, checking and granting tools, and MCP servers, are D4's (§8.3).
With no tools: "No tools in the Library."

### 2.6 What every tab shares

- **The problems banner** (`GET /problems`, on load and when `rev` moves): "⚠ 2 problems in the Library ▸", expanding to
  D2's sentences (`STALE_HEAD`, `UNKNOWN_TOOL`, `UNKNOWN_SPAWN`). A stale head blocks every conversation's materialize, so
  the user must see it where they edit.
- **Polling** (decision K): while `document.visibilityState` is `visible`, `GET /health` every 3 s; when `rev` changes, the
  tab refetches its data. An editor's draft is never overwritten by a refetch; its `base_version` makes a conflicting
  save a 409.
- **Errors** are always the backend's own sentence (D2's `message`, deep_reasoner's field messages), never a generic
  one. A request that fails without a D2 body is the backend being unreachable (§2.1).
- **Theme.** The frame takes Canvas's colours, radius, font and colour scheme from the `theme` parameter (§4.3), with
  Canvas's dark defaults when it is absent (the standalone page).
- **Accessibility.** Every input has a visible label; the save result is announced (`aria-live="polite"`); errors are
  linked to their fields (`aria-describedby`); every action is a button with text; the cards are an ordered list.

---

## 3 · Where this design departs from, or adds to, the approved spec

Each is a refinement inside D3's scope unless it says otherwise; if the Conductor reads any as a change of what was
approved, it goes back to Michael.

1. **The UI runs in a frame served by the backend; the App's pages only mount it** (decision A). The spec draws D3 as an
   App whose tabs are App pages over D2's bridged API; C2 found that a page cannot write through the bridge, and PR 3
   (approved 2026-10-03) is how D3 does.
2. **Preact, textareas and a YAML 1.1 parser instead of the spec's candidate "React with CodeMirror 6"** (decision C):
   the built files are committed (item 3). CodeMirror can come with D4's Python editor, behind `CodeField`.
3. **The built App is committed and ships in the wheel** (decision D; D5's proposal). The spec left packaging to the
   System Designer.
4. **About 40 lines of Python** (`library/ui.py`, one line in D2's `api.py`, two sentences in D2's `texts.py`). The
   spec's D3 cost says "No Python"; serving the UI from the backend needs a route.
5. **Additions beyond the spec's bullets**, each small and each something the panel is unusable without: adding and
   deleting a namespace (a new Library has only `root`, so "pick its namespace from the existing ones" would offer
   nothing else); deleting a decomposition; the run settings (D2 §3 item 1 says "the seven are what D3 edits"); the
   problems banner (a stale head stops every conversation); drafts that survive a tab switch (C2 unmounts hidden tabs);
   restarting a dead backend (D5's proposal); Canvas's theme in the frame.
6. **Not in the panel:** version history (D2 has the endpoints; nothing in the spec asks to show it); making a
   decomposition top level (D3 never sends `top_level`, so D2 keeps it as imported); reordering attachments (Attach
   appends, as D2 does); renaming (not an operation, D2 §4.5); export (the frame's sandbox has no `allow-downloads`,
   `bridge.py:53–55`; `dr-app export` is the path, D5 §4.8.1); saving a run as a decomposition (after v1, spec).
7. **The success line has two forms** (§2.3): the spec's sentence when the open conversation has started, and a neutral
   one otherwise, because a conversation whose first message is not yet sent will use the new decomposition.
8. **The tooltip reads "Show Decompositions"**, C2's `Show {{title}}` with the manifest title S2 and C2 use; the spec's
   "Show decompositions" differs in one capital (Michael: "The name not that important currently").
9. **D2's validation messages are deep_reasoner's in full** (`List should have at least 1 item after validation, not
   0`; the spec's mock-up shortened it, D2 §9 item 9).
10. **A second safety sentence**, `SAFETY_NO_CAP`, for a profile that runs `dr-acp --no-key-proxy`; D5's `SAFETY` states a
    cap that would then be false.
11. **Size:** about 2.4k lines of code and 1.1k of tests, about 10 h at Gate C, against the spec's ≈1.5k and ≈5 h (§10).

---

## 4 · Modules

### 4.1 Files in deep-reasoning

```text
canvas-app/                            the TypeScript project (D3's source; not in any wheel)
    package.json                       scripts: build, test, typecheck, format:check, dev; engines.node ">=22 <23"
    package-lock.json                  committed; CI runs npm ci
    .nvmrc                             22
    tsconfig.json                      strict; jsx react-jsx with jsxImportSource preact
    vite.config.ts                     the frame UI → ../src/deep_reasoning/canvas_app/ui/  (and vitest's config)
    vite.page.config.ts                the page bundle → ../src/deep_reasoning/canvas_app/dist/index.js
    index.html                         the frame's HTML entry
    src/
        shared/protocol.ts             TabId, FrameParams, FrameMessage: the page ↔ frame contract (§4.3)
        page/                          runs in Canvas's page
            index.ts                   activate(host): registers the four tabs
            host.ts                    the subset of C2's host API D3 uses (types only; Appendix A.1)
            mount.ts                   mountTab: the sequence of §2.1
            backend.ts                 ensureBackend
            context.ts                 readConversationNamespace, readSpendCap, spendCapFromArgs, readTheme
            texts.ts                   the page's sentences
        ui/                            runs in the frame
            main.tsx                   reads the URL, applies the theme, renders App
            app.tsx                    App: the notice, the tab (or the standalone row), problems, polling, backend loss
            api.ts                     D2's HTTP API: one function per endpoint, LibraryError, BackendUnavailable
            types.ts                   D2's records, as TypeScript
            cards.ts                   messages ↔ cards (§5.1)
            save.ts                    the bodies of §5.2
            yaml.ts                    parseYaml, stringifyYaml (YAML 1.1)
            drafts.ts                  localStorage drafts, tolerant of a storage that throws
            tree.ts                    namespaceTree
            texts.ts                   the frame's sentences (§4.7)
            theme.ts                   applyTheme, DEFAULT_THEME
            components/                DecompositionEditor, CardList, CodeField, ValueEditor, NamespacePicker,
                                       NamespaceChecklist, FieldErrors, SafetyNotice, ProblemsBanner, ConfirmRow, Banner
            tabs/                      browse.tsx, create.tsx, namespaces.tsx, tools.tsx
            styles.css
    tests/                             vitest: <module>.test.ts per module (§7.2)
src/deep_reasoning/canvas_app/         the App package: package data, D5 stages it (§4.6)
    __init__.py                        docstring and APP_NAME
    canvas-extension.json              hand-written (§4.6)
    panel.svg                          hand-written icon
    dist/index.js                      built from src/page, committed
    ui/index.html, ui/assets/app.js, ui/assets/app.css      built from src/ui, committed
src/deep_reasoning/library/ui.py       /ui/ routes (§4.5)
tests/library/test_ui.py               the routes (no browser)
tests/canvas_app/                      pytest + Playwright (marker browser) and E8 (§7.3, §7.4)
.gitattributes                         the built files: linguist-generated, -diff
.github/workflows/ci.yml               (D1's) gains the canvas-app job (§7.6)
```

Repository wiring: the root `pyproject.toml` declares the marker `browser` and adds `and not browser` to `addopts`
(beside D5's `not live and not desktop and not crossrepo`); the dev group has `playwright` (D5 adds it; D3 adds the same
line if D3 lands first). `.gitignore` gains `canvas-app/node_modules/`. Hatchling includes every tracked file under
`src/deep_reasoning`, so the App package ships in the wheel with no configuration (as D2's `starter.yaml` does); nothing
under `canvas-app/` does.

### 4.2 The page bundle (`src/page/`)

A self-contained ES module exporting `activate`, as Canvas loads every App (`canvas-extension-module-loader.ts`: the
bundle's text is imported from a `blob:` URL, so it can import nothing). It imports only `shared/protocol.ts`, which
Vite inlines.

**`activate(host)`** registers `browse`, `create`, `namespaces` and `tools` with `host.registerPage(id, mount)` and
returns a disposer that disposes all four registrations. On an agent-server without panels, C2 refuses the
registrations without throwing (C2 §4.1), and the App does nothing.

**`mountTab(host, tab, context)`** returns its disposer synchronously and does its work under an `AbortController`
(C2 allows an async mount; a synchronous disposer means a mount disposed early leaves nothing behind):

1. Write `LOADING` into `context.container`.
2. In parallel: `ensureBackend(request, signal)`; `readConversationNamespace(request, context.conversationId)`;
   `readSpendCap(request)`. `readTheme(context.container)` is synchronous.
3. Backend not ok → write its sentence and a **Try again** button (which reruns from 1); stop.
4. `host.appBackend` missing → `NO_FRAMES`; stop.
5. `params = {tab, parent: window.location.origin, namespace, started, cap, focus: takeFocus(tab), theme}`;
   `dispose = host.appBackend.mountFrame(container, {path: "/ui/" + frameSearch(params), title: TAB_TITLES[tab],
   onError})`. `onError({reason: "not-ready"})` → dispose and rerun from 1, once per mount; other reasons → nothing (C2
   wrote its notice).
6. Listen to `window`'s `message` events; accept one only when `event.source` is the `contentWindow` of the `iframe`
   C2 appended to the container (C2 §6.2 step 3) and `isFrameMessage(event.data)`:
   - `select-tab` → `putFocus(tab, focus)`; `context.surface.selectTab(tab)` (C2 then disposes this mount and mounts the
     other tab, which takes the focus);
   - `reload` → dispose the frame and rerun from 1.
7. The disposer aborts, removes the listener and disposes the frame.

`takeFocus` and `putFocus` are a module-level map keyed by tab, read once: a focus is meant for the very next mount of
that tab.

**`ensureBackend(request, signal)`** implements §2.1's table over `GET /api/canvas-extensions/installed/dr-library/backend`
and `POST …/backend/start {revision}` (`canvas_extensions_router.py:327–370`). It never calls `prepare`.

**`readConversationNamespace(request, conversationId)`**: `GET /api/conversations/<id>/events/search?kind=ACPSessionControlsEvent&sort_order=TIMESTAMP_DESC&limit=1`
(C2 §7.2, S2 §7 item 4); the newest event's `config_options` entry with `id === "namespace"` gives `namespace` =
`current_value` and `started` = it lists exactly one option. No event, no such option, or any failure → `null`.

**`readSpendCap(request)`**: `GET /api/agent-profiles/deep_reasoner` (`agent_profiles_router.py:285–305`, answering
`{name, profile}`); `spendCapFromArgs(profile.acp_args)`: `"off"` when the arguments contain `--no-key-proxy`; else the
value after `--spend-cap-usd` (or of `--spend-cap-usd=<v>`) when it is a decimal number; else `"5"` (D5's
`DEFAULT_SPEND_CAP_USD`, `dr-acp`'s default). A 404 or any failure → `"5"`.

**`readTheme(element)`**: `getComputedStyle(element)` for each of `THEME_TOKENS` (Appendix A.2: the `--oh-*` surface,
text, border, accent, status and radius tokens Canvas defines in `src/tailwind.css`), plus `color-scheme` and
`font-family`; a value is kept only if it is at most 200 characters of `[#\w\s(),.%'"-]` (no `;`, braces or `url(`).

### 4.3 The frame protocol (`src/shared/protocol.ts`)

The only code the page and the frame share. **The frame's URL** is `/ui/?` + these parameters (all strings in the URL;
`readFrameParams` is tolerant: an unknown or missing value takes its default, so a bad URL still shows a page):

| Parameter | Meaning | Default |
|---|---|---|
| `tab` | `browse`, `create`, `namespaces` or `tools` | `browse` |
| `parent` | Canvas's origin; the only `targetOrigin` the frame posts to | none: standalone (no messages, own tab row) |
| `namespace` | the open conversation's namespace | none |
| `started` | `1` when that namespace is fixed (the first message was sent) | not started |
| `cap` | the spend cap in USD as the profile states it, or `off` | `5` |
| `focus` | a decomposition's slug (browse) or a namespace's name (namespaces) to open | none |
| `theme` | JSON object of token → value (§4.2) | Canvas's dark defaults |

**Messages** from the frame: `{type: "dr-library/select-tab", tab, focus}` and `{type: "dr-library/reload"}`, posted to
`window.parent` with `targetOrigin = parent`. Nothing is posted the other way.

### 4.4 The frame UI (`src/ui/`)

**`api.ts`** has one function per D2 endpoint the panel and D4 use (Appendix A.3), each `fetch(<relative path>)` with
`Content-Type: application/json` on every body, returning D2's records. Relative paths (`../namespaces` from
`…/ui/`) resolve under `/app-backends/dr-library/` in a panel and under `/` on the standalone page (verified). Bodies
carry only the fields D2's models declare (D2 refuses others with 400). A response is classified:

- 2xx → its JSON;
- a JSON body with `error` (D2's shape, `{"error", "message", "errors"?, "head"?}`) → `LibraryError` with `status`,
  `code`, `message`, `errors`, `head`;
- anything else (the bridge's `{"detail": …}`, a non-JSON 502, a network failure) → `BackendUnavailable` with the status
  (`0` for a network failure).

**`app.tsx`** renders, in order: the safety notice until acknowledged; the tab named by `tab` (or the standalone tab
row and the selected tab); the problems banner; the backend-loss footer when any request has thrown
`BackendUnavailable`. It owns the `/health` poll and gives every tab `rev` (a refetch key), `health` and the frame
parameters. `navigateTab(tab, focus)` posts `select-tab` in a panel and switches its own state when standalone.

**Tabs** are §2.2–§2.5. **Components** (Appendix A.3) are shared, D4 included: `CodeField` (a monospace auto-growing
textarea; `language` is a hint only, for a later CodeMirror), `ValueEditor` (YAML or text, parse errors inline),
`NamespacePicker` (one of), `NamespaceChecklist` (some of, with fixed inherited entries), `FieldErrors`, `ConfirmRow`,
`Banner`, `SafetyNotice`, `ProblemsBanner`, `DecompositionEditor` (the editor of §2.2 and §2.3, with `CardList`).

**Styles**: one stylesheet using the theme's custom properties (`var(--oh-surface)`, …); no CSS framework.

### 4.5 `library/ui.py`: serving the UI

```python
UI_ROOT: Final = Path(__file__).resolve().parents[1] / "canvas_app" / "ui"
UI_HEADERS: Final[Mapping[str, str]] = {
    "Cache-Control": "no-cache",
    "X-Content-Type-Options": "nosniff",
    "Content-Security-Policy": (
        "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
        "base-uri 'none'; form-action 'none'; "
        "frame-ancestors http://localhost:* http://127.0.0.1:*"
    ),
}


def ui_routes(
    root: Path = UI_ROOT,
) -> list[Route]:
    """GET /ui/ → root/index.html; GET /ui/assets/{name} → root/assets/<name> for a name that was a file
    there at start-up, else 404 (LibraryNotFound, D2's JSON); every answer carries UI_HEADERS. Without
    root/index.html, /ui/ answers 503 UI_NOT_BUILT. Nothing outside root/assets is ever opened."""
```

`create_app` (D2's `api.py`) appends `*ui_routes()` to its routes, so D2's guard (`_Guard`, same user, `Host`) covers
`/ui/` too; GET needs no JSON. Starlette's `FileResponse` adds `ETag`, `Last-Modified` and the media type
(`text/javascript` for `.js`). File names are fixed (§4.6), so `no-cache` makes an upgraded runtime's files show at the
next mount. The policy: the frame runs only its own script and talks only to its own origin; `'unsafe-inline'` styles
because Preact sets style attributes; `frame-ancestors` admits Canvas on any loopback port and nothing else.

**No redirects.** The bridge refuses an upstream redirect with 502 (`bridge.py:471`, `proxy.py:154–161`), and
Starlette redirects a path that matches only with the other trailing slash. So the page always mounts `/ui/` (with the
slash) and the UI never requests a path that is not a route.

### 4.6 Build, the committed files, and the App package

**The manifest**, `src/deep_reasoning/canvas_app/canvas-extension.json` (hand-written; S2 §5.1 validates it; D5 adds the
`backend` block when it stages it, D5 §4.6):

```json
{
  "schema_version": 1,
  "name": "dr-library",
  "display_name": "Library",
  "version": "1.0.0",
  "description": "deep_reasoner's decompositions, namespaces and tools, from Show Decompositions at the top right of a conversation.",
  "entrypoint": "dist/index.js",
  "contributes": {
    "conversation_panels": [
      {
        "id": "decompositions",
        "title": "Decompositions",
        "icon": "panel.svg",
        "tabs": [
          {"id": "browse", "title": "Decompositions", "path": "/"},
          {"id": "create", "title": "Create decomposition", "path": "/create"},
          {"id": "namespaces", "title": "Namespaces", "path": "/namespaces"},
          {"id": "tools", "title": "Tools", "path": "/tools"}
        ]
      }
    ]
  }
}
```

`version` is deep-reasoning's package version (a test pins it, §7.5); D5 prints it.

**The build** (`npm run build` in `canvas-app/`) runs two Vite builds:

- `vite build` (`vite.config.ts`): `base: "./"`, `build.outDir: "../src/deep_reasoning/canvas_app/ui"`,
  `emptyOutDir: true`, `rollupOptions.output`: `entryFileNames: "assets/app.js"`, `assetFileNames: "assets/[name][extname]"`,
  `inlineDynamicImports: true`. Fixed names keep every build's file set the same.
- `vite build --config vite.page.config.ts`: `build.lib` with `entry: "src/page/index.ts"`, `formats: ["es"]`,
  `fileName: () => "index.js"`, `outDir: "../src/deep_reasoning/canvas_app/dist"`.

Both minify. Expected sizes: the page bundle under 10 KB; the frame UI about 170 KB minified (Preact ≈10, `yaml` ≈110,
D3's code ≈50), about 50 KB gzipped.

**Committed, and checked.** The CI job builds with Node 22 from `package-lock.json` and runs `git diff --exit-code --
src/deep_reasoning/canvas_app`; a difference fails the job and uploads the fresh build as an artifact to commit.
`.gitattributes` marks `src/deep_reasoning/canvas_app/dist/**` and `src/deep_reasoning/canvas_app/ui/**`
`linguist-generated=true -diff`, so diffs and the PR stack show them as changed files, not minified text; Gate C reads
`canvas-app/src`.

**`npm run dev`** serves the frame UI with Vite's dev server at `http://localhost:5173/ui/`, proxying D2's paths
(`/health`, `/problems`, `/validate`, `/profile`, `/namespaces`, `/effective`, `/decompositions`, `/tools`) to
`DR_LIBRARY_URL` with `changeOrigin` (so D2 sees its own `Host`).

### 4.7 Texts (verbatim; tests assert these)

The page (`src/page/texts.ts`):

| Name | Text |
|---|---|
| `LOADING` | `Opening the Library…` |
| `STARTING` | `Starting the Library's backend…` |
| `BACKEND_FAILED` | `The Library's backend did not start: {detail}` |
| `NOT_APPROVED` | `The Library's backend is not approved for this version of the App. Restart the app: its setup approves the App it installed.` |
| `BACKEND_UNSUPPORTED` | `This agent-server cannot run the Library's backend: {detail}` |
| `NO_FRAMES` | `This version of Canvas cannot show an App's own pages. Update the app.` |
| `TRY_AGAIN` | `Try again` |

The frame (`src/ui/texts.ts`):

| Name | Text |
|---|---|
| `SAFETY` | `deep_reasoner runs as you. It can read and change any file you can, and code it writes can find your model keys on this computer if it tries. Spend through the key proxy stops at ${cap} per conversation.` (D5's `SAFETY`, verbatim; a test pins equality, §7.3) |
| `SAFETY_NO_CAP` | `deep_reasoner runs as you. It can read and change any file you can, and code it writes can find your model keys on this computer if it tries. The key proxy is off for this agent (--no-key-proxy), so nothing caps what a conversation spends.` |
| `UNDERSTAND` | `I understand` |
| `SAVED_STARTED` | `✓ Saved '{name}' v{version} in {namespace}. New conversations in {namespace} use it; this conversation does not, because its run was built at its first message.` (the spec's) |
| `SAVED` | `✓ Saved '{name}' v{version} in {namespace}. New conversations in {namespace} use it and offer it as /{slug}; a conversation that has already started keeps the run it began with.` |
| `SAVED_EDIT` | `✓ Saved '{name}' v{version}. New conversations use it; conversations already started keep the version they began with.` |
| `SHOW_IN_DECOMPOSITIONS` | `Show in Decompositions` |
| `EXISTS` | `'{name}' already exists (v{version}, in {where}).` (`where`: the namespaces joined with `, `, or `no namespace`) |
| `SAVE_AS_NEXT` | `Save mine as v{next}` |
| `RENAME` | `Rename` |
| `RELOAD_ENTRY` | `Reload` |
| `SAVE_OVER` | `Save over it` |
| `SAVE_ANYWAY` | `Save anyway` |
| `CANCEL` | `Cancel` |
| `NAME_REQUIRED` | `Give the decomposition a name.` |
| `OUTPUT_NOTE` | `written by you, not run` (the spec's) |
| `RAW_NOTE` | `Shown as written: this message is not a task, a think-and-code step or an output.` |
| `YAML_SYNTAX` | `This is not valid YAML: {message}` |
| `YAML_NOT_DECOMPOSITION` | `To edit it as cards, the YAML must be a mapping with a name and a list of messages, each with a role and a content.` |
| `DELETE_CONFIRM` | `Delete '{name}'? It is removed from every namespace; its versions stay in the Library's history.` |
| `DELETE_NAMESPACE_CONFIRM` | `Delete namespace '{name}'? Its decompositions stay in the Library.` |
| `INHERITED` | `Inherited from {source}` (in Decompositions rows: `inherited from {source}`) |
| `OVERRIDDEN` | `Overridden here` |
| `SET_HERE` | `Set here` (root's own values) |
| `GRANTED_HERE` | `Granted here` |
| `ATTACHED_HERE` | `Attached here` |
| `FROM_PROFILE` | `From the run settings` |
| `NOT_SET` | `Not set: deep_reasoner's default` |
| `ANY_NAMESPACE` | `Any namespace` |
| `UNDEFINED_TOOL` | `not a tool in the Library` |
| `DEFAULT_BADGE` | `New conversations start here` |
| `MAKE_DEFAULT` | `Start new conversations here` |
| `EFFECTIVE_FAILED` | `Inherited decompositions cannot be shown: {message} Showing each decomposition where it is attached.` |
| `PROBLEMS` | `{n} problem in the Library` / `{n} problems in the Library` |
| `BACKEND_LOST` | `The Library stopped answering ({status}).` with `Restart` |
| `SESSION_ENDED` | `The panel's session with the Library ended.` with `Reload` |
| `NO_TOOLS` | `No tools in the Library.` |
| `DISCARD_DRAFT` | `Discard draft` |

Labels: `Name`, `Use when`, `Hint`, `Namespace`, `task`, `think`, `code`, `output`, `+ turn`, `View YAML`, `Edit YAML`,
`Edit as cards`, `Save to {namespace}`, `Save`, `Delete`, `Attached to`, `Override`, `Edit`, `Reset`, `Add variable`,
`Add namespace`, `Delete namespace`, `Run settings`, `Add setting`, `Attach…`, `Detach`.

D2's `texts.py` gains (D3's Python): `UI_NOT_BUILT` = `The panel's files are not in this installation: reinstall
deep-reasoning, or run npm run build in canvas-app/.` and `ui_file_missing(name)` = `There is no file '{name}' in the
panel's build.`

---

## 5 · Algorithms

### 5.1 Messages ↔ cards

A decomposition is `name` and `messages: [{role, content}]` (`prompt_config.py:18–29`). deep_reasoner's chat backbone
acts in `<repl>…</repl>` (`v2/messages.py:278–307`, the default delimiters, which no config field changes) and observes
in `<observation>\n…\n</observation>` (`v2/messages.py:131–137`); `<think>` is the convention every example's prompt
uses. The editor's model is one card per message:

```text
task    a user message that is not an observation of the step before it     text = content, verbatim
step    an assistant message of the form                                     think, thinkLayout, code, end
          (<think>T</think>\n | <think>\nT\n</think>\n)? <repl>\nC\n</repl> (\n)?
output  a user message, directly after a step, of the form                   text, end
          <observation>\nO\n</observation> (\n)?
raw     anything else                                                        role, content, verbatim
```

**Parse** (`messagesToCards`): for each message, try the form its role and position allow; **keep the card only if
rendering it gives back exactly `content`**; otherwise the message is a raw card. **Render** (`cardsToMessages`):

```text
step:   (think == "" ? "" : inline ? "<think>" + think + "</think>\n" : "<think>\n" + think + "\n</think>\n")
        + "<repl>\n" + code + "\n</repl>" + end
output: "<observation>\n" + text + "\n</observation>" + end
task:   text                      raw: content
```

So `cardsToMessages(messagesToCards(m))` equals `m` for every `m`, by construction, and the tests check it on a table
and on every decomposition in deep_reasoner_beta's configs (§7.2). `end` keeps the trailing newline a YAML literal
block gives (`|` clips to one) and the missing one a flow string has. `thinkLayout` keeps one-line and block thinks as
written; typing a newline into an inline think switches it to block, and an empty think renders none (so a message with
an empty `<think></think>` is a raw card, never silently rewritten).

**Editing.** `addTurn` gives the last step an empty output card when it has none, then appends a step with empty
think and code; `removeTurn(i)` removes step `i` and the output after it; `turnNumbers` numbers task and step cards
1, 2, 3…, an output sharing its step's number (the spec's mock-up). `cardIndexForLoc("messages.3.content")` is 3
(`null` for other locations), so D2's errors land on their card.

### 5.2 Saving a decomposition

```text
create     validate(json(name, cards))          not ok  → errors on their cards; stop
           warnings → "Save anyway" / "Cancel"
           PUT /decompositions/<validate.slug> createBody(draft, picked)
               = {yaml, use_when, hint, namespaces: [picked], base_version: 0}
           201 → SAVED_STARTED | SAVED; clear the draft
           409 conflict, head ≠ null → EXISTS; "Save mine as v{head.version + 1}":
               PUT … saveAsNextBody(draft, head, picked)
                 = {yaml, use_when, hint, namespaces: head.namespaces + [picked] (once, head's order first),
                    base_version: head.version}
               409 again (it moved meanwhile) → EXISTS with the new head
           422 → D2's message and errors
edit       PUT /decompositions/<record.slug> updateBody(draft, checked)
               = {yaml, use_when, hint, namespaces: checked, base_version: draft.baseVersion}
           409 stale → CONFLICT_STALE (D2's sentence) · "Reload" | "Save over it" (base_version = head.version)
```

`use_when` and `hint` are always present: the trimmed field, or `null` when empty (D2 stores no value for either). In
card mode `yaml` is `JSON.stringify({name, messages: cardsToMessages(cards)})`; in YAML mode it is the text as written.
`top_level` is never sent, so D2 leaves it as it was.

### 5.3 Override and Reset

```text
document = parseYaml(namespace.yaml)            (YAML 1.1; the namespace's own keys only, never inherited ones)
Override f      document[f] = effective value of f (the editor's starting point)  → the user edits → save
Edit f          document[f] = the edited value                                     → save
Reset f         delete document[f]                                                 → save
vars key k      document.vars[k] = v | delete document.vars[k]; an empty vars is deleted
tools           document.tools = this namespace's own grants, in order; empty → deleted
system_suffix   document.system_suffix = text; "" → deleted
save            PUT /namespaces/<name> {yaml: stringifyYaml(document), base_version: namespace.version}
attach/detach   PUT /namespaces/<name> {yaml: namespace.yaml, decompositions: list, base_version: namespace.version}
profile         the same over profile.yaml, PUT /profile; "Start new conversations here" sets entry_namespace
```

`stringifyYaml` writes YAML 1.1 (quotes `yes`, `on`; dates as dates; multi-line strings as literal blocks), so PyYAML
reads back the values the user saw (verified). D2 then validates with deep_reasoner's `NamespaceConfig` and writes its
canonical form; the next poll shows it.

### 5.4 Ensuring the backend

§2.1's table. Timing: `start` returns when the health probe answers or fails (`backend.py:448–533`, 30 s by default);
D2 measured about 1.4 s of imports, so a restarted backend shows in about two seconds. `starting` (another caller is
starting it, for example D5's setup at launch) is polled at 500 ms up to 45 s. An aborted mount stops polling at once.

---

## 6 · The traffic, as the backend sees it

| Concern | What happens | Holds because |
|---|---|---|
| D2's `Host` check | The bridge drops the browser's `Host` and httpx sends `127.0.0.1:<port>` | `proxy.py:48, 136–143`; `bridge.py:366–369`; `backend.py:638–643`; verified (§ header item 1) |
| D2's JSON check (415) | The frame sends `Content-Type: application/json` on every body; the bridge forwards it unchanged | `proxy.py:32–51` (not hop-by-hop); verified (a `text/plain` `PUT` was 415) |
| D2's unknown-field check (400) | `api.ts` sends only the fields of D2's body models | D2 `api.py:117–154` as built (`extra="forbid"`); vitest pins each body's keys |
| D2's same-user check (Linux) | The connection comes from the agent-server, which runs as the user | D2 decision K |
| The bridge's `Origin` check on writes | Same-origin `fetch` from the frame sends the ingress origin | `bridge.py:454–455`; verified |
| The session cookie | Partitioned under Canvas's site, minted by C2's keeper, sent by the frame on every request under `/app-backends/dr-library` (the page, the assets, the API) | `bridge.py:392–413`; verified in headless Chromium; E12 step 5 in Electron |
| Redirects | None: the UI requests only routes | `bridge.py:471`; §4.5 |
| `/app-backends/dr-library/session` | The agent-server's own route; D2 has no `/session` path, so nothing of the App is shadowed | `canvas_extensions_bridge_router.py:32–77` |
| Response headers | `Content-Type`, `Cache-Control`, `ETag`, the CSP pass through; `Set-Cookie` and `Content-Length` are dropped, which the UI never relies on | `proxy.py:172–177` |

---

## 7 · Testing

Plain pytest and vitest; each test named for the property it pins; the outside world faked at its boundary (Canvas's
host API and `fetch` in vitest; nothing faked in the browser tests but the browser's parent page). No screenshots: every
browser test asserts text, values and what the Library holds afterwards.

### 7.1 Layers

| Layer (spec §4) | Where |
|---|---|
| 1 · deterministic, every push | vitest (§7.2); `tests/library/test_ui.py`; the browser tests (§7.3) and E8 (§7.4) in the `canvas-app` job |
| 2 · contracts and replays | the manifest validates against S2's model where the SDK fork is installed (D5's cross-repo job); the frame's requests against D2's real API in every browser test |
| 4 · the real desktop app | D5's E12 (final flow): Show Decompositions opens the panel, its frame shows the Library's namespaces through the real bridge, Create decomposition saves into the picked namespace, the next conversation offers it and records it |
| 5 · Gate B's evidence | the browser tests and E8, green in CI at the branch's head (spec §4: "D3 … through their end-to-end tests, Playwright written as tests that assert behaviour"); no real model is called |

### 7.2 vitest (`canvas-app/tests/`)

| File | Pins |
|---|---|
| `cards.test.ts` | each form of §5.1 parses and renders (a table: inline and block think, no think, trailing newline or not, empty think → raw, prose outside the tags → raw, an observation not after a step → task, a system message → raw); `test round trip is identity` over a generated set (random roles, contents with and without the tags); over every decomposition in `$DR_BETA_CHECKOUT/docs/configs` and `configs` (read in place with `yaml` 1.1; skipped without the variable; a guard fails when `CI` is set and it is unset); `addTurn` adds the missing output before the new step; `removeTurn` takes the output with its step; `turnNumbers`; `cardIndexForLoc` |
| `yaml.test.ts` | the agreement table of the header's item 3 (each value as PyYAML reads it); `stringifyYaml` output reparses to the same value; multi-line strings are literal blocks; a syntax error throws with its message |
| `protocol.test.ts` | `readFrameParams(frameSearch(p))` equals `p`; an unknown tab, a bad `theme` JSON or an unsafe token value falls back; `isFrameMessage` accepts the two shapes only |
| `context.test.ts` | `spendCapFromArgs` table (`["--home", h, "--spend-cap-usd", "7"]` → `7`; `--spend-cap-usd=2.5` → `2.5`; absent → `5`; `--no-key-proxy` → `off`; `abc` → `5`); `readConversationNamespace` with a fake `request`: one value → started, several → not started, no event, another agent's options, a failing request → `null`; `readTheme` keeps the listed tokens and drops unsafe values |
| `backend.test.ts` | `ensureBackend` over each row of §2.1's table with a fake `request` (calls and their order recorded): `ready` makes one call; `stopped` and prepared → `start` with the revision; not prepared → `NOT_APPROVED` and no `start`, never `prepare`; `starting` polls until ready; `start` answering `unhealthy` → `BACKEND_FAILED` with its detail; an abort stops polling |
| `mount.test.ts` (jsdom) | a fake host (C2's API at its boundary: `registerPage`, `agentServer.request`, `appBackend.mountFrame` appending an `iframe`): `activate` registers exactly the four tab ids; a mount builds the frame path from the conversation's namespace, the cap and the theme; a second mount for another conversation carries that conversation's namespace (E11's "mounts with the right conversation", D3's part); a `select-tab` message from the frame's window calls `surface.selectTab` and the next mount of that tab gets the focus; the same message from another window is ignored; `reload` remounts; `onError("not-ready")` remounts once; disposing during the backend check leaves the container empty and no frame |
| `api.test.ts` | with `fetch` stubbed: every body is JSON with exactly D2's field names; a D2 error body → `LibraryError` with code, errors and head; the bridge's `{"detail"}` 503, a non-JSON 502 and a network failure → `BackendUnavailable` |
| `save.test.ts` | `createBody`, `saveAsNextBody` (the head's namespaces first, the picked one once), `updateBody`; `use_when` and `hint` are always present (`null` when blank) |
| `drafts.test.ts` | a draft round-trips; a `localStorage` that throws on read or write loses the draft and nothing else |
| `tree.test.ts` | `namespaceTree` from dotted names (root's children, nested levels, order kept) |

### 7.3 Browser tests (`tests/canvas_app/`, pytest + Playwright, marker `browser`)

Fixtures (`conftest.py`, Appendix A.4): `library_home` (a Library built in `tmp_path` by importing
`tests/canvas_app/fixtures/library.yaml`, a small config of our own: namespaces `root`, `router`, `router.archive`,
`course_advisor`; three decompositions, one inherited from root; one tool with a source; never deep_reasoner_beta's
files, which have no license); `library_server` (a real `dr-library serve --port <free> --home <home>` subprocess with
only `PATH`, `LANG` and `TMPDIR`, as the backend manager starts it, waited on `/health`); `browser` (session-scoped
Chromium; skipped with a reason when Playwright's browser is missing, and failing when `CI` is set); `open_ui(**params)`
(a page at `http://127.0.0.1:<port>/ui/?…`, standalone, which is the same document the panel frames). After each
action a test reads the Library through D2's Python API on the same home, so it asserts what was stored, not only what
was shown.

| File | Tests (each named for its property) |
|---|---|
| `test_browse.py` | `test_decompositions_are_grouped_by_namespace_with_version_slash_command_and_use_when`; `test_an_inherited_decomposition_says_where_it_comes_from`; `test_top_level_and_unattached_decompositions_have_groups_of_their_own`; `test_saving_an_opened_decomposition_makes_its_next_version`; `test_attached_to_is_the_exact_set_after_a_save`; `test_a_stale_save_offers_reload_or_save_over`; `test_deleting_a_decomposition_detaches_it_everywhere`; `test_a_change_made_elsewhere_appears_without_a_reload` (a `put_decomposition` through the Python API; the row appears within the poll); `test_the_tab_falls_back_to_attachments_when_inheritance_cannot_be_resolved`; `test_focus_opens_that_decomposition` |
| `test_create.py` | `test_saving_stores_version_1_in_the_picked_namespace` (the record's messages equal what the cards showed; `namespaces == [picked]`; `use_when`, `hint`); `test_the_picker_lists_the_librarys_namespaces_and_preselects_the_conversations`; `test_without_a_conversation_namespace_the_default_namespace_is_preselected`; `test_the_saved_line_says_the_started_conversation_does_not_change` (`started=1` → `SAVED_STARTED`; otherwise `SAVED`); `test_validation_errors_show_on_the_card_they_name`; `test_an_example_without_final_answer_asks_before_saving` (Cancel stores nothing; Save anyway stores it); `test_an_existing_name_offers_to_save_the_next_version_keeping_its_namespaces`; `test_view_yaml_shows_the_canonical_yaml_and_edited_yaml_returns_to_cards`; `test_use_when_in_the_yaml_is_refused_in_deep_reasoners_words`; `test_a_draft_survives_reloading_the_frame`; `test_use_when_and_hint_survive_a_save_that_did_not_touch_them`; `test_an_imported_decomposition_saved_unchanged_makes_no_new_version` (cards are lossless end to end) |
| `test_namespaces.py` | `test_the_tree_follows_dotted_names_and_marks_the_default`; `test_each_field_shows_its_effective_value_and_source`; `test_override_sets_a_field_here_and_reset_removes_it`; `test_a_variable_is_overridden_and_reset_key_by_key`; `test_a_tool_granted_here_adds_to_the_inherited_ones`; `test_attach_and_detach_change_only_this_namespaces_list`; `test_start_new_conversations_here_moves_the_default` (`/health`'s `default_namespace`); `test_adding_and_deleting_a_namespace` (and D2's refusal for root, the default and a parent, in its words); `test_run_settings_edit_the_profile`; `test_yaml_values_mean_what_dr_reads` (a variable typed as `on` is stored `true`); `test_keys_the_panel_does_not_show_survive_an_override` |
| `test_tools_tab.py` | `test_the_tools_tab_always_shows_the_safety_notice_with_the_cap`; `test_the_tools_tab_lists_tools_with_their_grants` |
| `test_notice.py` | `test_the_safety_notice_shows_until_understood`; `test_the_notice_is_d5s_sentence_with_the_cap` (equal to `dr_app.texts.SAFETY` formatted with `7`; skipped until D5's package is in the environment); `test_without_the_key_proxy_the_notice_says_nothing_caps_spending` |
| `test_backend_loss.py` | `test_a_backend_that_stops_answering_offers_restart` (kill the server; the next poll shows `BACKEND_LOST`; in a panel, Restart posts `reload`, checked through a parent page that records messages) |
| `test_page_bundle.py` | the built `dist/index.js`, imported from a `blob:` URL by a small parent page served on `http://localhost:<p>` that implements C2's host API over the real `library_server` (its `mountFrame` appends the frame at `http://127.0.0.1:<port>/ui/…`): `test_the_built_bundle_activates_and_registers_four_tabs`; `test_the_frame_opens_with_the_conversations_namespace`; `test_show_in_decompositions_selects_the_tab_and_opens_the_new_entry`; `test_the_frame_takes_canvas_theme` (the frame's computed `--oh-surface` equals the parent's) |

### 7.4 E8: a saved decomposition is used by the next conversation (`test_e8_next_conversation.py`)

The spec's surviving check of E8, end to end below Canvas, deterministic:

```text
home  = library_home with the profile's client at D1's FakeOpenAI (keyless; D5's proxy leaves keyless clients alone)
serve = library_server(home)
dr-acp --home home (no --config: LibraryCatalog, D2 §4.7) over stdio, D1's harness (ShimConnection, FakeOpenAI
         answering "<think>ok</think>\n<repl>\nFinalAnswer(\"done\")\n</repl>")
A: session/new; namespace router; prompt "Q1"                                   (A's run is built now)
UI: Create decomposition in a browser: name "rank by prerequisites", use when, a task "Which of CS201, CS310 and CS330
    can I take first?", one step FinalAnswer; namespace router; Save               → shows "v1 in router"
A: prompt "Q2"   → FakeOpenAI's request for this turn holds no message with that task       (the open run unchanged)
B: session/new; namespace router → available_commands_update lists /rank-by-prerequisites with the use-when line
B: prompt "Q3"   → run.start.namespace == "router",
                   run.start.source.versions.decompositions["rank by prerequisites"] == 1,
                   FakeOpenAI's first request holds the task among the worked examples
```

`test_a_decomposition_saved_in_create_is_used_by_the_next_conversation_in_its_namespace`. It uses D1's
`tests/acp/harness.dr_acp`, whose `config` argument becomes optional (`None` → no `--config`), a one-line change to a
test helper that D3's Implementer makes if D2's has not.

### 7.5 `tests/library/test_ui.py` (no browser)

`test_ui_serves_the_index_and_the_built_assets` (Starlette's `TestClient` with `Host: 127.0.0.1:<port>`, D2's guard
included); `test_a_file_not_in_the_build_is_404`; `test_no_path_outside_the_assets_is_served` (`..`, encoded, nested);
`test_every_answer_carries_the_csp_and_no_cache`; `test_an_unbuilt_ui_is_503_with_its_sentence`;
`test_the_ui_answers_only_its_own_host` (403 through D2's guard); `test_the_manifest_is_valid_and_its_version_is_the_packages`
(the JSON's keys, kebab-case ids, four tabs, `entrypoint` and `icon` present in the package; S2's own model validates it
in D5's cross-repo job); `test_the_committed_build_is_complete` (`dist/index.js`, `ui/index.html`, `ui/assets/app.js`
exist and `index.html` references only `./assets/` files).

### 7.6 CI: the `canvas-app` job (`.github/workflows/ci.yml`)

On every push touching `canvas-app/**`, `src/deep_reasoning/canvas_app/**`, `src/deep_reasoning/library/**`,
`tests/canvas_app/**` or the workflow:

1. `actions/setup-node` (Node 22, npm cache on `canvas-app/package-lock.json`); `npm ci`.
2. `npm run typecheck`, `npm run format:check`, `npm test` (with `DR_BETA_CHECKOUT` as D2's job sets it).
3. `npm run build`; `git diff --exit-code -- src/deep_reasoning/canvas_app` (on failure, upload the build).
4. `uv sync`; `uv run playwright install --with-deps chromium`; `uv run pytest -m browser tests/canvas_app` with
   `CI=true`.

About 4 minutes. `tests/library/test_ui.py` runs in D1's existing Python job.

---

## 8 · Contracts with other work

These are findings for the Conductor; none is settled sideways.

### 8.1 C2

- **No change to C2's signatures.** D3 uses `registerPage`, the mount context's `conversationId` and `surface`
  (`selectTab`), `host.agentServer.request` and `host.appBackend.mountFrame(container, {path, title, onError})` exactly
  as C2 §7 and Appendix A.1 state them.
- **One statement asked for C2's §7.4:** "the frame is the only `iframe` `mountFrame` appends to the container, and it
  stays there until the disposer runs" (C2 §6.2 step 3 says it appends one). D3's page finds it there to accept
  messages only from its window. If C2 prefers not to promise that, the alternative is an additive
  `options.onFrame?(frame: HTMLIFrameElement)`; either way D3's `mount.test.ts` pins what it relies on.
- **Noted, no change asked:** switching tabs disposes one frame and mounts the next, so C2's keeper revokes the App's
  session and mints a new one on every switch (C2 §6.3: the last release revokes). It costs two requests; the drafts
  make it invisible.

### 8.2 D2

- **D2's API holds as built** (`5158693`): the `Host`, JSON and unknown-field checks are compatible with the frame
  (§6, verified), and D3 always sends `use_when`, `hint` and `base_version`.
- **D3 adds, in D2's files:** `*ui_routes()` at the end of `create_app`'s route list (`api.py`), and `UI_NOT_BUILT` and
  `ui_file_missing` in `texts.py`. No existing route, body or sentence changes. D2's design §1.2 should then say that
  `dr-library serve` also serves the panel's files at `/ui/` (one line, D2's to add when it next revises).
- **Relied on, already in D2:** `POST /validate` returns `slug` even when not ok and the canonical `yaml` when ok;
  `GET /effective` in namespace order; a 409 `conflict` carries `head`; `DecompositionRecord.data` is the parsed YAML;
  `/health` carries `rev` and `default_namespace`.

### 8.3 D4's contract (D4 is designed after D3)

D4 adds writing, checking and granting tools, and MCP servers, to the Tools tab. What D4 gets, and what it must keep:

- **The tab.** `canvas-app/src/ui/tabs/tools.tsx` is D4's to extend; its id `tools`, path `/tools` and the manifest stay.
  **The safety banner stays at the top of the tab** (D5 §2.3; `test_the_tools_tab_always_shows_the_safety_notice_with_the_cap`
  must stay green).
- **The client.** `api.ts` already has `getTools`, `getTool`, `putTool`, `deleteTool` and `toolVersions` over D2's
  routes (Appendix A.3), with D2's body (`yaml`, `source`, `granted_in`, `base_version`). D4 adds `checkTool` for its own
  route (`POST /tools/{name}/check`, D2 §6.5), JSON in and out (D2's guard refuses anything else), and its tests in
  `api.test.ts`.
- **Components.** `CodeField` (D4 may put CodeMirror's Python mode behind the same props; if it does, it removes
  `inlineDynamicImports` and loads the editor as a separate chunk, which `ui_routes` serves like any built asset),
  `NamespaceChecklist` (grants per namespace), `FieldErrors` (D2's `loc`/`msg`), `ConfirmRow`, `Banner`, and the tab
  props (`rev`, `health`, `params`, `navigateTab`).
- **Data the frame cannot read** (Canvas's MCP server list, from the agent-server's settings) comes as a new frame
  parameter: D4 adds the field to `FrameParams` (`shared/protocol.ts`) and its read to `page/context.ts` through
  `host.agentServer.request`, with the same tolerance (a failure is "unknown").
- **Writes** follow §5's rules: `base_version` always; resend every field a `PUT` replaces (`source`, and `granted_in`
  when the grants are on screen).
- **Tests** go beside D3's: vitest units in `canvas-app/tests/`, browser tests in `tests/canvas_app/test_tools_tab.py`
  with the same fixtures (D4 adds a tool with a factory error to `fixtures/library.yaml` if it needs one).
- **The committed build** and its CI check cover D4's changes; the frame UI should stay under about 250 KB minified
  without an editor chunk.

### 8.4 D5: its proposals, settled, and what D5 must do

D5 §8.3 proposed four things; each is settled here:

| D5's proposal | Settled |
|---|---|
| The built App ships in the wheel under `deep_reasoning/canvas_app/`, built by D3's CI and committed, checked against a fresh build | **Accepted** (decision D). The package also holds the frame UI (`ui/`), which `dr-library serve` serves; D5 does not stage it. |
| D5's setup builds the App's backend artifact on the user's machine and stages, approves and starts it every launch | **Accepted.** D3 needs no new argument in the backend's argv; the backend D5 starts serves `/ui/` from the same runtime. |
| The panel shows the safety notice, with the cap read from the profile's `--spend-cap-usd` | **Accepted**, §2.1: the first time it opens and permanently in the Tools tab; the cap from `GET /api/agent-profiles/deep_reasoner`, `5` when absent; plus `SAFETY_NO_CAP` for `--no-key-proxy` (§3 item 10). |
| The panel may restart a backend that died | **Accepted**, §2.1 and decision F: before every mount and on the frame's Restart; `start` of the prepared revision only, never `prepare`. |

**What D5 must do for D3:**

1. **Stage only the App's own files**: `canvas-extension.json` (adding the `backend` block, D5 §4.6 step 3),
   `dist/index.js` and `panel.svg`, from `importlib.resources.files("deep_reasoning.canvas_app")`. Not `ui/` and not
   `__init__.py`: the frame UI is served from the runtime, so a UI-only change must not change the staged digest
   (which would force a reinstall that stops the backend, D5 §4.6 step 5).
2. **Keep the backend's argv as D5 §4.6 writes it** (`serve --port {port} --home <DR_HOME>`); D3 adds nothing to it.
3. **Configure the App ingress** (C3's approved launcher default, `http://127.0.0.1:<agent-server port>`); without it
   every mount ends in C2's `no-ingress` notice.
4. **Approve and start the backend at every launch** (D5 §4.6), so a first open does not wait on deep_reasoner's
   imports; the page only restarts an approved revision.
5. **Keep `--spend-cap-usd` (and, if used, `--no-key-proxy`) as separate entries of the profile's `acp_args`** (D5
   §4.5.1 writes `"--spend-cap-usd", "5"`); `spendCapFromArgs` also reads `--spend-cap-usd=<v>`.
6. **E12's final flow** uses D3's selectors (Appendix A.5) inside the frame: open Show Decompositions, see the
   Library's namespaces in the Namespaces tab, save in Create decomposition (`dr-create-*`, `dr-save`, `dr-result`),
   then the next conversation's menu and run log; and checks that the panel still loads after its first session's five
   minutes (C2's renewal).
7. **D5's `SAFETY` and D3's stay equal**: D3's `test_the_notice_is_d5s_sentence_with_the_cap` imports `dr_app.texts`;
   a change to one is a change to both.

### 8.5 S2

None. D3's manifest is the one S2 §5.1 validates, with `description` and the icon path as D3 places it.

---

## 9 · What D3 relies on

| # | Behaviour relied on | Their code |
|---|---|---|
| C2-1 | `registerPage(<tab id>, mount)`; the mount context's `container`, `path`, `conversationId` (never null in a panel), `surface.selectTab`; a tab mounted only while visible and disposed on every switch, close, conversation change | C2 `72aa49f` §4.1, §7.1–§7.3, Appendix A.1 |
| C2-2 | `host.appBackend.mountFrame(container, {path, title, onError})`: a frame at `lease.url + path` (leading `/` stripped; query kept) with the bridge's sandbox, appended to the container; `onError` reasons; the keeper renews the cookie | C2 §6.2, §6.3, §7.4, Appendix A.11 |
| C2-3 | `host.agentServer.request` reaches the agent-server with the session key, root-relative paths only | Canvas `canvas-extensions-service.ts:173–189` |
| C2-4 | The bundle is imported as one ES module from a `blob:` URL and must export `activate` | Canvas `canvas-extension-module-loader.ts` |
| B1 | The bridge strips `/app-backends/<name>`, forwards to `http://127.0.0.1:<port>/<path>` with the browser's headers minus hop-by-hop (`Host` included), refuses upstream redirects, and requires the ingress `Origin` on writes | `bridge.py:366–369, 448–472`; `proxy.py:32–51, 77–177` |
| B2 | Backend status reports a dead process as `unhealthy` and a failed probe as `unhealthy`; `start` needs the prepared revision and returns after the health check; `ready_endpoint` is `127.0.0.1` | `backend.py:309–332, 448–533, 638–643`; `canvas_extensions_router.py:327–370` |
| B3 | The frame's sandbox is `allow-forms allow-modals allow-popups allow-same-origin allow-scripts` (no downloads) | `bridge.py:53–55` |
| B4 | The agent-server's CORS admits loopback origins with credentials (the session bootstrap from Canvas) | `middleware.py:34–60` |
| P1 | `GET /api/agent-profiles/{name}` → `{name, profile}`, the profile's `acp_args` a list of strings | `agent_profiles_router.py:83–86, 285–305` |
| S2-1 | `ACPSessionControlsEvent` with `config_options[]` (`id`, `current_value`, `options[]`), searchable by kind | S2 `9e32261` §4.1, §7 item 4 |
| S2-2 | The manifest's `conversation_panels` as in §4.6 validates | S2 §5.1 |
| D1-1 | `dr-acp` offers the namespace as option `namespace`, narrows it to one value at the first prompt, and offers the namespace's decompositions as commands until then | D1 `f281109` §2 steps 2–4 |
| D1-2 | The test harness (`tests/acp/harness.dr_acp`, `ShimConnection`, `FakeOpenAI`) and `run.start.source.versions` | `v1-dr-acp` `21c2c7a` |
| D2-1 | The HTTP API of D2 §6 as built: routes, bodies (`extra="forbid"`), errors (`error`, `message`, `errors`, `head`), the guard (same user, `Host`, JSON) | `v1-library-store` `5158693`, `api.py` |
| D5-1 | The backend is approved and started at launch; `SAFETY`'s text; `--spend-cap-usd` in the profile's arguments | D5 `8086afb` §4.5.1, §4.6, §6 |
| R1 | Decompositions are `name` + `messages[{role, content}]`, strings only, extra keys refused; `<repl>` and `<observation>` as the chat backbone writes them | deep_reasoner `prompt_config.py:18–29`, `v2/messages.py:131–137, 278–307` |

---

## 10 · Size

| Part | Code | Tests |
|---|---|---|
| The page bundle (`activate`, `mountTab`, `ensureBackend`, context, host types, texts) | 300 | 260 (vitest: backend, context, mount) |
| The frame protocol | 70 | 50 |
| UI core (api 140, types 130, cards 130, save 40, yaml 30, drafts 30, tree 30, texts 110, theme 40, app and polling 140) | 820 | 330 (vitest: cards with the corpus, yaml, api, save, drafts, tree) |
| Components (decomposition editor and cards 250, value editor 80, pickers and checklists 70, notices and banners 80, errors and confirm 40) | 520 | — |
| Tabs (browse 170, create 170, namespaces 380, tools 50) | 770 | — |
| Python (`library/ui.py`, one line in `api.py`, two texts) | 50 | 60 (`test_ui.py`) |
| Browser tests (fixtures 90, the page-bundle parent page 60, test files 500) and E8 (70) | — | 720 |
| Build and CI configuration (two Vite configs, `tsconfig`, `package.json`, the job) | 110 | — |
| **Total** | **≈2.6k** | **≈1.4k** |

About 4k lines with tests, about 11 h at Gate C at the workspace's rate (the committed built files are generated and
not read). The spec estimated ≈1.5k lines of TypeScript and ≈5 h. The difference: the page bundle and the frame
protocol, which exist because a page cannot reach its backend (C2 §6.1); the additions of §3 item 5; unit tests (the
spec's figure had none); the browser tests that are Gate B's evidence (spec §4 layer 5); and E8 end to end.

---

## 11 · Open items, and what I was unsure about

1. **Electron's Chromium** has not run the frame: the probe used headless Chromium 153 and a replica of the bridge. D5's
   E12 step 5 (a probe App) and its final flow (D3's panel) are the proof; if Electron refuses the partitioned cookie,
   D5 §11 item 11 names the fallbacks, and D3 changes nothing (the frame's URLs are relative).
2. **The committed build must be reproducible** on a developer's machine and in CI (Node 22, the lockfile, Vite's
   deterministic output). If a developer's build differs, the CI job's artifact is what gets committed; a recurring
   difference would mean pinning Vite's and esbuild's platform binaries, which I have not measured.
3. **YAML 1.1 in the browser and PyYAML** agree on every case I tried (header item 3); PyYAML's resolver has corners
   (`=`, `<<` merge keys in odd places) I did not test. The backend is authoritative: the panel shows D2's canonical YAML
   after every save.
4. **C2's frame placement** (§8.1): D3 relies on the iframe being in the container. Small, but a contract C2 should
   state.
5. **The profile editor** (Run settings) is in because D2 §3 item 1 says D3 edits the seven settings; the spec's D3
   bullets name only the default namespace. If the Conductor reads it as scope growth, it is one node of the tree and
   about 60 lines to drop.
6. **`host.agentServer.request`'s timeout** is not stated by C2; `start` can take up to the backend's 30 s health
   timeout. If the client's default is shorter, `ensureBackend` falls back to polling the status, which §2.1's table
   already does for `starting`.
7. **The spec's tooltip** "Show decompositions" versus C2's "Show Decompositions" (§3 item 8) is Michael's to care about
   or not.
8. **D1's harness** requires `--config` today (`tests/acp/harness.py:180–203`); the E8 test needs it optional (§7.4).
9. **Size** (§10) is about twice the spec's estimate.

---

## Appendix A · Signature reference

TypeScript in declaration form (`declare` marks a body §2–§5 specify; one field per line); Python as it will be
written, ruff-formatted, bodies `...`. Paths are relative to `canvas-app/src/` unless they start with `src/` or `tests/`.

### A.1 `page/host.ts` (C2's host API, the subset D3 uses; types only)

```ts
export type CanvasExtensionDispose = () => void;

export interface CanvasExtensionPageSurface {
  kind: "page";
}

export interface CanvasExtensionConversationPanelSurface {
  kind: "conversation-panel";
  panelId: string;
  tabId: string;
  selectTab: (tabId: string) => void;
}

export interface CanvasExtensionPageMountContext {
  container: HTMLElement;
  path: string;
  navigate: (path: string) => void;
  conversationId: string | null;
  surface: CanvasExtensionPageSurface | CanvasExtensionConversationPanelSurface;
}

export type CanvasExtensionPageMount = (
  context: CanvasExtensionPageMountContext,
) => void | CanvasExtensionDispose | Promise<void | CanvasExtensionDispose>;

export interface CanvasExtensionAgentServerRequest {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  path: string;
  body?: unknown;
  headers?: Record<string, string>;
}

export type AgentServerRequest = <T = unknown>(
  request: CanvasExtensionAgentServerRequest,
) => Promise<T>;

export type CanvasExtensionAppBackendErrorReason =
  | "no-ingress"
  | "not-ready"
  | "session-refused"
  | "unsupported-backend";

export interface CanvasExtensionAppBackendError {
  reason: CanvasExtensionAppBackendErrorReason;
  message: string;
}

export interface CanvasExtensionAppBackendFrameOptions {
  path?: string;
  title: string;
  onError?: (error: CanvasExtensionAppBackendError) => void;
}

export interface CanvasExtensionHost {
  readonly apiVersion: "1";
  registerPage: (
    contributionId: string,
    mount: CanvasExtensionPageMount,
  ) => CanvasExtensionDispose;
  agentServer: {
    request: AgentServerRequest;
  };
  /** C2 PR 3; absent on a Canvas without it. */
  readonly appBackend?: {
    mountFrame: (
      container: HTMLElement,
      options: CanvasExtensionAppBackendFrameOptions,
    ) => CanvasExtensionDispose;
  };
}
```

### A.2 `shared/protocol.ts` and `page/`

```ts
// shared/protocol.ts
export const APP_NAME = "dr-library";
export const TAB_IDS = ["browse", "create", "namespaces", "tools"] as const;
export type TabId = (typeof TAB_IDS)[number];
export declare const TAB_TITLES: Readonly<Record<TabId, string>>; // "Decompositions", "Create decomposition", …
export declare const THEME_TOKENS: readonly string[]; // "--oh-surface", "--oh-surface-raised", "--oh-surface-deep",
// "--oh-foreground", "--oh-muted", "--oh-text-secondary", "--oh-text-dim", "--oh-border", "--oh-border-subtle",
// "--oh-border-input", "--oh-color-primary", "--oh-accent", "--oh-accent-foreground", "--oh-danger",
// "--oh-success", "--oh-warning", "--oh-interactive-hover", "--oh-interactive-active", "--oh-focus",
// "--oh-radius", "--oh-field-radius", "color-scheme", "font-family"
export const MAX_THEME_VALUE_LENGTH = 200;
export const DEFAULT_SPEND_CAP = "5";

export interface FrameParams {
  tab: TabId;
  /** Canvas's origin; null on the standalone page. */
  parent: string | null;
  /** The open conversation's namespace, when its agent reported one. */
  namespace: string | null;
  /** The namespace is fixed: the conversation's first message was sent. */
  started: boolean;
  /** USD as the profile states it, or "off". */
  cap: string;
  /** A decomposition's slug (browse) or a namespace's name (namespaces). */
  focus: string | null;
  /** Token → value; only values that pass isSafeThemeValue. */
  theme: Readonly<Record<string, string>>;
}

export type FrameMessage =
  | {
      type: "dr-library/select-tab";
      tab: TabId;
      focus: string | null;
    }
  | {
      type: "dr-library/reload";
    };

export declare function frameSearch(params: FrameParams): string; // "?tab=…&…", empty values omitted
export declare function readFrameParams(search: string, standalone: boolean): FrameParams;
export declare function isFrameMessage(value: unknown): value is FrameMessage;
export declare function isSafeThemeValue(value: string): boolean;

// page/index.ts
export declare function activate(host: CanvasExtensionHost): CanvasExtensionDispose;

// page/mount.ts
export declare function mountTab(
  host: CanvasExtensionHost,
  tab: TabId,
  context: CanvasExtensionPageMountContext,
): CanvasExtensionDispose;
export declare function putFocus(tab: TabId, focus: string | null): void;
export declare function takeFocus(tab: TabId): string | null;

// page/backend.ts
export const BACKEND_PATH = "/api/canvas-extensions/installed/dr-library/backend";
export const BACKEND_POLL_MS = 500;
export const BACKEND_START_TIMEOUT_MS = 45_000;

export interface BackendStatus {
  name: string;
  state: "missing" | "stopped" | "starting" | "ready" | "unhealthy" | "unsupported";
  revision: string | null;
  prepared_revision: string | null;
  detail: string | null;
}

export type BackendCheck =
  | {
      ok: true;
    }
  | {
      ok: false;
      message: string;
    };

export declare function ensureBackend(
  request: AgentServerRequest,
  signal: AbortSignal,
  onProgress: (sentence: string) => void,
): Promise<BackendCheck>;

// page/context.ts
export interface ConversationNamespace {
  namespace: string;
  started: boolean;
}

export declare function readConversationNamespace(
  request: AgentServerRequest,
  conversationId: string | null,
): Promise<ConversationNamespace | null>;
export declare function readSpendCap(request: AgentServerRequest): Promise<string>;
export declare function spendCapFromArgs(args: readonly string[] | null | undefined): string;
export declare function readTheme(element: Element): Record<string, string>;
```

### A.3 `ui/`

```ts
// ui/types.ts: D2's records (D2 §4.4, as built)
export type Kind = "profile" | "namespace" | "decomposition" | "tool";

export interface Saved {
  version: number;
  rev: number;
  saved_at: string;
}

export interface ProfileRecord extends Saved {
  yaml: string;
  decompositions: string[];
  default_namespace: string;
  data: Record<string, unknown>;
}

export interface NamespaceRecord extends Saved {
  name: string;
  yaml: string;
  decompositions: string[];
  data: Record<string, unknown>;
}

export interface ChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

export interface DecompositionRecord extends Saved {
  name: string;
  slug: string;
  yaml: string;
  use_when: string | null;
  hint: string | null;
  namespaces: string[];
  top_level: boolean;
  data: {
    name: string;
    messages: ChatMessage[];
  };
}

export interface ToolRecord extends Saved {
  name: string;
  yaml: string;
  source: string | null;
  granted_in: string[];
  data: Record<string, unknown>;
}

export interface HistoryEntry extends Saved {
  kind: Kind;
  name: string;
  action: string;
  deleted: boolean;
  yaml: string | null;
  decompositions: string[] | null;
  slug: string | null;
  use_when: string | null;
  hint: string | null;
  source: string | null;
  deep_reasoner: string;
}

export interface Health {
  ok: boolean;
  rev: number;
  path: string;
  deep_reasoner: string;
  default_namespace: string;
}

export interface FieldError {
  loc: string;
  msg: string;
}

export interface Problem {
  kind: Kind;
  name: string;
  message: string;
}

export interface ValidationResult {
  ok: boolean;
  message: string | null;
  errors: FieldError[];
  warnings: string[];
  name: string | null;
  slug: string | null;
  yaml: string | null;
}

export interface Sourced {
  value: unknown;
  source: string | null;
}

export interface SuffixPart {
  source: string;
  text: string;
}

export interface EffectiveTool {
  name: string;
  source: string;
  defined: boolean;
}

export interface EffectiveDecomposition {
  name: string;
  slug: string;
  version: number;
  use_when: string | null;
  source: string;
}

export interface Effective {
  namespace: string;
  chain: string[];
  repl: Sourced;
  reasoner: Sourced;
  spawn: Sourced;
  system_suffix: SuffixPart[];
  tools: EffectiveTool[];
  vars: Record<string, Sourced>;
  decompositions: EffectiveDecomposition[];
}

// ui/api.ts: bodies carry exactly D2's fields (D2 refuses others with 400)
export interface ValidateBody {
  kind: Kind;
  yaml: string;
  name?: string;
  source?: string;
}

export interface ProfileBody {
  yaml: string;
  decompositions?: string[];
  base_version: number;
}

export interface NamespaceBody {
  yaml: string;
  decompositions?: string[];
  base_version: number;
}

export interface DecompositionBody {
  yaml: string;
  use_when: string | null; // always sent: an absent one is erased
  hint: string | null; // always sent
  namespaces?: string[];
  base_version: number;
}

export interface ToolBody {
  yaml: string;
  source?: string | null;
  granted_in?: string[];
  base_version: number;
}

export interface Written<T> {
  record: T;
  created: boolean; // 201
}

export declare class LibraryError extends Error {
  readonly status: number;
  readonly code: string; // D2's: invalid, conflict, refused, not_found, bad_request, forbidden, unsupported_media_type
  readonly errors: readonly FieldError[];
  readonly head: unknown; // conflict: the current record, or null
}

export declare class BackendUnavailable extends Error {
  readonly status: number; // 0: no answer; 401: session; 502, 503: the bridge
}

export declare function getHealth(): Promise<Health>;
export declare function getProblems(): Promise<Problem[]>;
export declare function validate(body: ValidateBody): Promise<ValidationResult>;
export declare function getProfile(): Promise<ProfileRecord>;
export declare function putProfile(body: ProfileBody): Promise<ProfileRecord>;
export declare function getNamespaces(): Promise<NamespaceRecord[]>;
export declare function getNamespace(name: string): Promise<NamespaceRecord>;
export declare function putNamespace(name: string, body: NamespaceBody): Promise<Written<NamespaceRecord>>;
export declare function deleteNamespace(name: string, baseVersion: number): Promise<HistoryEntry>;
export declare function getEffective(): Promise<Effective[]>;
export declare function getNamespaceEffective(name: string): Promise<Effective>;
export declare function getDecompositions(): Promise<DecompositionRecord[]>;
export declare function getDecomposition(slug: string): Promise<DecompositionRecord>;
export declare function putDecomposition(
  slug: string,
  body: DecompositionBody,
): Promise<Written<DecompositionRecord>>;
export declare function deleteDecomposition(slug: string, baseVersion: number): Promise<HistoryEntry>;
export declare function getTools(): Promise<ToolRecord[]>;
export declare function getTool(name: string): Promise<ToolRecord>;
export declare function putTool(name: string, body: ToolBody): Promise<Written<ToolRecord>>;
export declare function deleteTool(name: string, baseVersion: number): Promise<HistoryEntry>;
export declare function toolVersions(name: string): Promise<HistoryEntry[]>;

// ui/cards.ts
export interface TaskCard {
  kind: "task";
  text: string;
}

export interface StepCard {
  kind: "step";
  think: string; // "" renders no <think>
  thinkLayout: "inline" | "block";
  code: string;
  end: "\n" | "";
}

export interface OutputCard {
  kind: "output";
  text: string;
  end: "\n" | "";
}

export interface RawCard {
  kind: "raw";
  role: ChatMessage["role"];
  content: string;
}

export type Card = TaskCard | StepCard | OutputCard | RawCard;

export declare function messagesToCards(messages: readonly ChatMessage[]): Card[];
export declare function cardsToMessages(cards: readonly Card[]): ChatMessage[];
export declare function parseStep(content: string): StepCard | null;
export declare function renderStep(card: StepCard): string;
export declare function parseOutput(content: string): OutputCard | null;
export declare function renderOutput(card: OutputCard): string;
export declare function newDecompositionCards(): Card[];
export declare function addTurn(cards: readonly Card[]): Card[];
export declare function removeTurn(cards: readonly Card[], index: number): Card[];
export declare function turnNumbers(cards: readonly Card[]): number[];
export declare function cardIndexForLoc(loc: string): number | null;

// ui/save.ts
export interface DecompositionDraft {
  mode: "cards" | "yaml";
  name: string;
  useWhen: string;
  hint: string;
  cards: Card[];
  yaml: string;
  baseVersion: number; // 0 for a new one
}

export declare function draftYaml(draft: DecompositionDraft): string;
export declare function createBody(draft: DecompositionDraft, picked: string): DecompositionBody;
export declare function saveAsNextBody(
  draft: DecompositionDraft,
  head: DecompositionRecord,
  picked: string,
): DecompositionBody;
export declare function updateBody(
  draft: DecompositionDraft,
  namespaces: readonly string[],
): DecompositionBody;

// ui/yaml.ts
export declare class YamlSyntaxError extends Error {}
export declare function parseYaml(text: string): unknown; // version "1.1", uniqueKeys false
export declare function stringifyYaml(value: unknown): string; // version "1.1", lineWidth 0, blockQuote "literal"

// ui/drafts.ts
export const DRAFT_PREFIX = "dr-library.draft.";
export const SAFETY_ACK_KEY = "dr-library.safety-acknowledged";
export declare function loadDraft<T>(key: string): T | null;
export declare function saveDraft(key: string, value: unknown): void;
export declare function clearDraft(key: string): void;

// ui/tree.ts
export interface NamespaceNode {
  name: string;
  children: NamespaceNode[];
}

export declare function namespaceTree(names: readonly string[]): NamespaceNode; // rooted at "root"

// ui/theme.ts
export declare const DEFAULT_THEME: Readonly<Record<string, string>>; // Canvas's dark values
export const POLL_MS = 3_000;
export declare function applyTheme(theme: Readonly<Record<string, string>>, root: HTMLElement): void;

// ui/components (props; Preact function components)
export interface TabProps {
  params: FrameParams;
  health: Health;
  rev: number;
  navigateTab: (tab: TabId, focus: string | null) => void;
  onBackendLost: (error: BackendUnavailable) => void;
}

export interface CodeFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  language: "yaml" | "python" | "text";
  errors?: readonly FieldError[];
  testId?: string;
}

export interface ValueEditorProps {
  label: string;
  value: unknown;
  mode: "yaml" | "text";
  onSave: (value: unknown) => void;
  onCancel: () => void;
}

export interface NamespacePickerProps {
  namespaces: readonly string[];
  value: string | null;
  onChange: (name: string) => void;
}

export interface NamespaceChecklistProps {
  namespaces: readonly string[];
  checked: readonly string[];
  /** Shown checked and fixed, with where each comes from. */
  inherited?: Readonly<Record<string, string>>;
  onChange: (checked: string[]) => void;
}

export interface SafetyNoticeProps {
  cap: string;
  variant: "first-open" | "banner";
  onUnderstood?: () => void;
}

export interface DecompositionEditorProps {
  record: DecompositionRecord | null; // null: Create decomposition
  namespaces: readonly NamespaceRecord[];
  params: FrameParams;
  health: Health;
  draftKey: string;
  onSaved: (record: DecompositionRecord, created: boolean) => void;
  navigateTab: TabProps["navigateTab"];
}
```

### A.4 Python

```python
# src/deep_reasoning/canvas_app/__init__.py
"""The Library App (D3): its manifest, icon and built files. Built from canvas-app/; committed."""

APP_NAME: Final = "dr-library"


# src/deep_reasoning/library/ui.py: §4.5 (UI_ROOT, UI_HEADERS, ui_routes)


# src/deep_reasoning/library/api.py (D2's; one change)
def create_app(
    library: Library,
    *,
    same_user: Callable[[tuple[str, int], tuple[str, int]], bool] | None = None,
) -> Starlette:
    """As D2 §4.8, with *ui_routes() after D2's routes."""


# tests/canvas_app/conftest.py
@dataclass(frozen=True)
class LibraryServer:
    url: str  # http://127.0.0.1:<port>
    home: Path
    process: subprocess.Popen[bytes]

    def library(self) -> Library:
        """Library.open on the same file, for asserting what was stored."""


@pytest.fixture
def library_home(tmp_path: Path) -> Path:
    """A Library at tmp_path/home holding fixtures/library.yaml (imported, starter=False)."""


@pytest.fixture
def library_server(library_home: Path) -> Iterator[LibraryServer]:
    """dr-library serve on a free port, environment PATH, LANG and TMPDIR only; waits for /health."""


@pytest.fixture(scope="session")
def browser() -> Iterator[Browser]:
    """Chromium; skips with a reason when Playwright's browser is missing, fails when CI is set."""


@pytest.fixture
def open_ui(
    browser: Browser,
    library_server: LibraryServer,
) -> Callable[..., Page]:
    """open_ui(tab="create", namespace="router", started=True, cap="5") → a page at /ui/?…, notice acknowledged
    unless notice=True is passed."""
```

### A.5 Test ids inside the frame (for D3's tests and D5's E12)

`dr-tab-<tab>` (standalone row) · `dr-notice`, `dr-notice-ack` · `dr-problems` · `dr-backend-lost`, `dr-restart` ·
Decompositions: `dr-group-<namespace>` (`dr-group-top-level`, `dr-group-unattached`), `dr-row-<namespace>-<slug>` ·
the editor: `dr-name`, `dr-use-when`, `dr-hint`, `dr-slash`, `dr-namespace-<namespace>`, `dr-attached-<namespace>`,
`dr-card-<index>-<field>` (`task`, `think`, `code`, `output`, `raw`), `dr-add-turn`, `dr-remove-<index>`,
`dr-view-yaml`, `dr-yaml`, `dr-edit-cards`, `dr-save`, `dr-save-anyway`, `dr-save-as-next`, `dr-save-over`,
`dr-reload-entry`, `dr-delete`, `dr-result`, `dr-errors`, `dr-show-in-decompositions`, `dr-discard-draft` ·
Namespaces: `dr-node-<namespace>` (`dr-node-run-settings`), `dr-field-<field>`, `dr-source-<field>`,
`dr-override-<field>`, `dr-edit-<field>`, `dr-reset-<field>`, `dr-var-<key>`, `dr-grant-<tool>`, `dr-attach`,
`dr-detach-<slug>`, `dr-make-default`, `dr-add-namespace`, `dr-delete-namespace` · Tools: `dr-tool-<name>`. The page,
in Canvas's DOM: `dr-library-loading`, `dr-library-error`, `dr-library-retry`.
