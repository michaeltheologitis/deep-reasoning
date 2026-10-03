# D3 · Decompositions panel, as built

**TASK-8** · Cartographer · the code at `d4e9cd3` (head of `v1-decompositions-panel`: D3's code through `5effe26`;
four fixes, `450bed1`, `aaa97ef`, `4123ec7` and `2af80ef`, each answering a divergence this document named; then
`c5964ff`, `02b93dc`, `54625ab` and `d4e9cd3`, listed in the third revision below; this file is on `as-built/d3`) ·
checked against the design's v1, `ab6f2ec` (`docs/design/d3-decompositions-panel.md`) · D2 as built at `90044f0`,
D3's base · deep_reasoner_beta `d7334ae` · 2026-10-03.

**Revisions** (newest first):
- Third, the code at `d4e9cd3`: `c5964ff` gives a `start` that got no answer a fresh 45 s (#9's limit is gone);
  `02b93dc` and `54625ab` add tests pinning #6's and #10's rulings; `d4e9cd3` keeps the user's selection when an
  Add or Delete namespace is answered after another node was selected (§4.4), with a test, and fixes a missing
  wait in `test_adding_and_deleting_a_namespace`. Counts, sizes and line numbers are re-measured. The branch also
  carries design v3 (`2b03ef8`); the divergences stay against v1.
- Second, the code at `2af80ef`: §2.1's #3, #4 and #9 are closed and #6 is closed in part; #6's rest and #10 carry
  the Conductor's ruling; counts, sizes and line numbers are re-measured. The branch now also carries the design's v2
  (`dcde588`, "brought in line with the build at `5effe26`"), which a System Designer is still revising. The
  divergences below are against v1; I did not re-check them against v2.
- First, the code at `5effe26`.

D3's code is `canvas-app/` (TypeScript: the page bundle and the frame UI), the App package
`src/deep_reasoning/canvas_app/` (the manifest, the icon and the committed built files),
`src/deep_reasoning/library/ui.py`, an import and a route line in D2's `api.py` and two sentences in D2's `texts.py`,
`tests/canvas_app/`, `tests/library/test_ui.py`, the `canvas-app` CI job, and the wiring in §5. D1's and D2's
code is described only where D3 meets it.

**C2 is not green, and none of D3 has run inside Canvas.** C2's host API (the panel host, `registerPage` with a
`conversation-panel` surface, `host.appBackend.mountFrame`) is designed (`72aa49f`) and built on the Canvas fork
(`openhands-c2` at `db3b4b9`), but not green. Every test of D3's page bundle runs against a **faked host**: vitest's
`fakeHost` (`canvas-app/tests/fakes.ts`), and in Chromium a parent page in `test_page_bundle.py` whose
`mountFrame` appends an `<iframe>` pointing straight at `dr-library serve`. No test in this repository goes
through the agent-server's App ingress, its bridge, its session cookie, a real agent-server API or Electron. The
design's header item 1 probed the bridge once, outside the repository, against a replica; that remains the only
evidence for that path, and it is the design's, not the build's.

**Evidence marks.** Every claim carries one.
- **[run]**: executed in this sandbox, with other agents' suites running on the same 4 CPUs. At `d4e9cd3`:
  - `CI=true uv run pytest -m browser tests/canvas_app` (Playwright 1.56.0, preinstalled Chromium build 1194):
    55 passed, 1 skipped, 236.28 s;
  - in `canvas-app/`: `npx vitest run`, 150 passed and 2 skipped without the corpus, and 151 passed and 1 skipped
    with `DR_BETA_CHECKOUT` on deep_reasoner_beta `d7334ae`; `npx tsc --noEmit` and `prettier --check .` (clean);
    a fresh build of both bundles into a scratch directory, byte-identical to the committed files;
    `tests/library/test_ui.py` (16 passed);
  - an uncommitted vitest probe of `ensureBackend` with a slow `start` (#9), and five more runs of the namespace
    add-and-delete tests (§4.4).

  At `2af80ef`: the same commands (browser 50 passed, 1 skipped; vitest 149 + 2 and 150 + 1).

  At `5effe26`, not repeated, because the commits since change only `canvas-app/`, the built files,
  `tests/canvas_app/`, `docs/`, `as_built/` and the sdist's `exclude` (`test_ui.py`, which reads the built files,
  was rerun): the default suite, `CI=true DR_BETA_CHECKOUT=<clone of d7334ae> uv run pytest` (531 passed,
  52 deselected); `uv build`; and the uncommitted probes that drive a real `dr-library serve` with Playwright or
  `http.client`, or run the card model over deep_reasoner_beta's configs.
- **[CI]**: read from GitHub's logs: run 37090168700 at `5effe26`, run 37139529187 at `2af80ef` and run 37144441476 at `d4e9cd3`, jobs `test` and `canvas-app`, all green. D3 has
  no live tier (design §7.1: no model is called). I ran no paid model and no real `claude` CLI.
- **[read]**: read in the code and **not executed**. Weaker evidence than [run]; §7 lists the read claims that
  matter most.

**Reading order.** §2 (the divergences) first. Then §1 and §3–§5 are the map, §6 gives the experiments and the
test results as measured, and §7 says what I could not verify.

---

## 1 · What exists

D3 is a Canvas App, `dr-library`, in two halves that never share a JavaScript realm. The page bundle runs in
Canvas's page and only prepares and mounts a frame; the frame UI is served by the App's own backend,
`dr-library serve`, and talks to D2's HTTP API same-origin. [read; everything below the host run end to end by the
browser tests, §6]

```text
Canvas's page · C2's panel host (FAKED in every test here)
  dist/index.js  activate(host) → registerPage(browse | create | namespaces | tools)
  mountTab: "Opening the Library…" → ensureBackend ∥ readConversationNamespace ∥ readSpendCap ; readTheme
         → host.appBackend.mountFrame(container, {path: "/ui/?tab=…&parent=…&namespace=…&started=1&cap=…&focus=…&theme=…"})
         ◀─ postMessage {dr-library/select-tab | dr-library/reload}, accepted only from that iframe's window
the frame · another origin (in the tests http://127.0.0.1:<port>/ui/, without a bridge)
  ui/index.html, ui/assets/app.js, app.css   ◀─ dr-library serve: GET /ui/, /ui/assets/{name}      (library/ui.py)
  App: safety notice → tab → GET /health every 3 s → the tab refetches when rev moves
  api.ts: fetch("../<D2 path>"), JSON bodies   ─▶ dr-library serve: D2's API, unchanged
```

| Part | Lines | Where |
|---|---|---|
| the page bundle and the shared protocol | 625 | `canvas-app/src/page/`, `canvas-app/src/shared/protocol.ts` |
| the frame UI | 3,413 TypeScript, 368 CSS | `canvas-app/src/ui/` |
| Python | 59 + 5, plus an import, a route line and a docstring in `api.py`, and 2 sentences in `texts.py` | `library/ui.py`, `canvas_app/__init__.py` |
| built files, committed | 7.12 kB page bundle; 152.05 kB script, 4.05 kB CSS, 0.37 kB HTML | `canvas_app/dist/`, `canvas_app/ui/` |
| tests | 1,672 vitest (125 of them the fakes); 1,537 pytest, plus a 99-line fixture | `canvas-app/tests/`, `tests/canvas_app/`, `tests/library/test_ui.py` |

The TypeScript is 4,038 lines (3,777 non-blank). Design §10 estimated about 2.6k lines of code and 1.4k of tests.
The length sits in two files: `ui/components/editor.tsx` (869 lines: the decomposition editor for Create and for
an opened entry, §4.3; design §10 gave the editor and cards 250) and `ui/tabs/namespaces.tsx` (902: the tree,
seven kinds of field and the run settings; design §10 gave 380). [read]

---

## 2 · Divergences from the design (`ab6f2ec`)

No changelog `drift:` line exists for TASK-8, so every item below was found from the code. Design v1 (`ab6f2ec`,
01:30:57 UTC) precedes all twelve first build commits (`3ce186a` to `5effe26`, 01:40 to 02:19 UTC); the four fixes
(16:47 to 17:06 UTC) and the four commits after them (17:19 to 18:24 UTC) came after this document's first version. Each row gives what the design says, what is built,
where, and the reason the code or its commit gives ("none recorded" when neither does). A row a fix answered keeps
its number and says **Closed** or **Ruled**, with the commit. Paths are under `canvas-app/src/` unless they say
otherwise.

### 2.1 Behaviour a user or a collaborator sees

| # | Design | Built | Where | Reason |
|---|---|---|---|---|
| 1 | §2.2: when `GET /effective` fails, the tab falls back under `EFFECTIVE_FAILED` with D2's message. §2.6, §4.4: an answer that is not D2's JSON is the backend being unreachable. | D2 answers a head that no longer validates with a bare `text/plain` 500 `Internal Server Error` on `/effective` and on `/namespaces/<n>/effective`, not with its JSON [run: a real `dr-library serve` with a stale head]. `load.resolved` treats a non-JSON 500 from those reads as "inheritance cannot be resolved", fetches `/problems` and puts its sentences into `EFFECTIVE_FAILED`; no backend-loss footer appears [run: `test_the_tab_falls_back_to_attachments_when_inheritance_cannot_be_resolved`]. Any 500 from those two routes is reported this way, whatever its cause; a 500 from another route still shows the footer. | `ui/load.ts:71-89`; `ui/tabs/browse.tsx:46-60` | comment at `load.ts:71-73`; commit `5effe26` |
| 2 | Namespaces when inheritance cannot be resolved: not specified. | The namespace shows the same `/problems` sentence and **no fields at all**: only Start new conversations here and Delete namespace remain [run: with a stale head, 0 `dr-field-*` elements]. One stale namespace head makes every namespace's effective read fail [run: `router`, `router.archive` and `course_advisor` all answered 500 with `router.archive` stale], so until it is fixed no namespace field can be overridden from the panel. | `ui/tabs/namespaces.tsx:282-286, 363-402` | commit `5effe26`: "both tabs now show D2's own sentence for that head, from /problems, instead of the backend-loss footer" |
| 3 | §2.3: the draft holds "every field, the cards or the YAML, and the mode". | **Closed by `aaa97ef`.** At `5effe26` the draft left out the picked namespace, so each mount preselected again [run]. Now the draft (`localStorage` key `dr-library.draft.create`) stores the pick, which wins over the preselection while the Library still has that namespace [run: `test_a_draft_keeps_the_namespace_picked_over_the_preselected_one`]. Picking alone starts a draft, and a draft cleared by a save or Discard draft takes the preselection again [read]. | `ui/components/editor.tsx:85-89, 196-202, 433` | commit `aaa97ef` |
| 4 | §2.3: D2's errors that name no card and not the name are shown "above the cards". | **Closed by `4123ec7`.** At `5effe26` their banner sat below the cards. Now it sits between the namespace picker (or Attached to) and the cards, or the YAML; D2's message for a refused save is in the same banner [run: `test_an_error_that_names_no_card_shows_above_the_cards`]. | `editor.tsx:436-444` | commit `4123ec7` |
| 5 | §2.3: View YAML shows `POST /validate`'s canonical `yaml`. | When the draft does not validate (no canonical YAML), it shows the browser's own YAML 1.1 rendering of `{name, messages}`. | `editor.tsx:328-342` | none recorded |
| 6 | §2.3: Rename "focuses the name". | **Closed in part by `2af80ef`.** At `5effe26` Rename in YAML mode focused nothing. Now it focuses the YAML field and stays in YAML mode [run: `test_rename_in_yaml_mode_focuses_the_yaml_which_holds_the_name`]. **Ruled** (the Conductor; the designer records it): YAML mode has no name field, since the name is the YAML's own, and `NAME_REQUIRED` is checked only in card mode, D2's validation answering in YAML mode [run: no `dr-name` element in YAML mode; `02b93dc` pins the card-mode check with `test_saving_without_a_name_in_card_mode_asks_for_one_and_writes_nothing`]. | `editor.tsx:284-285, 374-399, 548-553` | commit `2af80ef`; the ruling |
| 7 | §2.2: in the opened editor, "namespaces that inherit it are listed as 'also used in … (inherited)'". | Each namespace below an attached one is a **checked, disabled** box labelled with its own name followed by "also used in <that same name> (inherited)" [run: `catalog lookup`, attached to root, shows `router` / `also used in router (inherited)`, and likewise for `router.archive` and `course_advisor`]. Unchecking the ancestor frees them. | `editor.tsx:160-175`; `ui/components/pickers.tsx:54-66`; `ui/texts.ts:90` | commit `b42b3b5`: "so moving a decomposition from a parent to a child is one save" |
| 8 | §2.1: `starting` is polled "up to 45 s". §4.7 lists every page sentence. | After 45 s the page shows `BACKEND_FAILED` with a new detail, `STILL_STARTING` = "it was still starting after 45 seconds." [run: vitest `gives up on a backend still starting after the timeout`] | `page/backend.ts:65-72`; `page/texts.ts:14` | none recorded |
| 9 | §11 item 6: if `start`'s request times out, `ensureBackend` "falls back to polling the status". | **Closed by `450bed1`.** At `5effe26` any failed request ended the check. Now a `start` that gets no answer (an error without a numeric `status`) reads the status and goes on by §2.1's table: `starting` is polled, `ready` mounts, anything else is `BACKEND_FAILED` with its detail. A `start` the agent-server answered with an error still ends with `BACKEND_FAILED` in its words [run: vitest `polls the status when start gets no answer, …`, 2 cases]. The test for an answer matches the client C2 uses (`@openhands/typescript-client` in `openhands-c2`): an HTTP error is an `HttpError` with a numeric `status`, and a timeout or a failed connection is a plain `Error` [read]. **Since `c5964ff`**, the fallback restarts the 45 s budget. At `2af80ef` the budget counted from the first status read, so a `start` that timed out after 60 s (C2's documented request limit [read: `openhands-c2` `src/types/canvas-extension.ts`]) with the backend still `starting` ended at once with `STILL_STARTING` [run: probe]. At `d4e9cd3`, with `start` failing after 60 s, a backend ready by the third status read mounts; one still `starting` 45 s later ends with `STILL_STARTING` after 92 status reads, about 105 s after the check began [run: probe; vitest `gives a backend still starting after start timed out a fresh 45 s`]. | `page/backend.ts:50, 85-97, 105-107` | commits `450bed1`, `c5964ff` |
| 10 | §2.4: Add namespace is prefilled "with the selected namespace's name and a dot". | Empty when root or Run settings is selected; `<selected>.` otherwise. Unchanged at `2af80ef`. **Ruled** the design's reading (the Conductor): root's children are top-level names, and Run settings is not a namespace. `54625ab` pins it with `test_add_namespace_is_not_prefilled_under_root_or_run_settings[root, run-settings]` [run]. | `ui/tabs/namespaces.tsx:155-158` | the ruling |
| 11 | §2.1, §4.4: the backend-loss footer appears when a request throws `BackendUnavailable`. | It also **disappears** when the next `/health` poll answers. | `ui/app.tsx:44-53` | none recorded |
| 12 | §2.2: opening a decomposition "shows the decomposition editor". | The editor replaces the list, with a "← Decompositions" button back to it. | `ui/tabs/browse.tsx:119-147`; `ui/texts.ts:102` | none recorded |
| 13 | §5.1: `turnNumbers` numbers task and step cards; `cardIndexForLoc("messages.3.content")` is 3, and `null` for other locations. | Raw cards are numbered too. `cardIndexForLoc` maps any `messages.<n>` or `messages.<n>.<…>` (`messages.0.role` → 0, `messages.12` → 12) [run: vitest]. | `ui/cards.ts:39, 166-177` | none recorded |

Not divergences. Design §2.3 calls "a user message that is neither the task nor an observation" a raw card,
while its §5.1 table makes every user message that is not an observation right after a step a task card. The
build follows §5.1 [run: vitest `an observation not after a step: a task`]. An unchanged save of an existing
decomposition makes no revision (D2 writes nothing) and still shows "✓ Saved '<name>' v<n>. …" [run].

### 2.2 Build, CI and packaging

| # | Design | Built | Where | Reason |
|---|---|---|---|---|
| 14 | §4.6: "Both [builds] minify." | The frame UI is minified (151.96 kB, 49.00 kB gzip). The page bundle's names are shortened but its whitespace is kept, as Vite's library build does for `es` (226 lines, 7.09 kB, 2.89 kB gzip). Both are within the design's sizes (under 10 KB; about 170 KB) [run]. | `canvas-app/vite.page.config.ts` | none recorded |
| 15 | §7.6: the job runs "on every push touching" five path globs. | The workflow has no path filter: `canvas-app` runs on every push and every pull request, beside `test`. | `.github/workflows/ci.yml:4-6, 33` | none recorded |
| 16 | §4.6, §7.6: the check is `git diff --exit-code -- src/deep_reasoning/canvas_app`. | It is `git status --porcelain -- src/deep_reasoning/canvas_app`, failing on any output. | `ci.yml:63-70` | commit `375a3d1`: "so a file the build adds or drops fails the check too" |
| 17 | §4.6's sample manifest has `"version": "1.0.0"`, under the rule "deep-reasoning's package version (a test pins it)". | `"version": "0.1.0"`, the package's version, pinned by `test_the_manifest_is_valid_and_its_version_is_the_packages`. The rule holds; only the sample differs. | `src/deep_reasoning/canvas_app/canvas-extension.json:5` | the rule |
| 18 | §4.1, §4.6: the build options listed there. | Also `modulePreload: false` and `input: {app: "index.html"}`; `npm run dev` proxies to `http://127.0.0.1:8765` when `DR_LIBRARY_URL` is unset. Playwright is pinned `==1.56.0`. | `canvas-app/vite.config.ts:15-40`; `pyproject.toml:30` | commit `3ce186a`: 1.56.0's Chromium build (1194) is the one preinstalled in the sandbox |

### 2.3 Tests

| # | Design | Built | Where | Reason |
|---|---|---|---|---|
| 19 | Appendix A.4: `browser` is session-scoped. | It is module-scoped. | `tests/canvas_app/conftest.py:109-125` | comment: while Playwright's sync API is started, `asyncio.run` (D1's harness) fails in that thread; E8 uses Playwright's async API instead |
| 20 | §7.3: the fixture is `tests/canvas_app/fixtures/library.yaml`. | It is a folder: `fixtures/library/main.yaml` (a `dr` config), `library.yaml` (D2's manifest, for the use-when lines and hints) and `tools/word_count.py`, imported with `Library.import_config`. The contents are as designed: namespaces `root`, `router`, `router.archive`, `course_advisor`; three decompositions (one top level, one in root and so inherited, one in router); one tool with a source. | `tests/canvas_app/fixtures/library/` | none recorded |
| 21 | §7.4: conversation A is opened with "namespace router". | A opens in the profile's entry namespace, which the fixture sets to `router`; nothing sets the option. The browser opens the frame standalone, without the page bundle. | `tests/canvas_app/test_e8_next_conversation.py:60-67` | none recorded |
| 22 | §7.3: `test_the_notice_is_d5s_sentence_with_the_cap` is "skipped until D5's package is in the environment". | It is skipped in every run, here and in CI: `dr_app` is not installed. No run compares D3's `SAFETY` with D5's (D3 §8.4 item 7). | `tests/canvas_app/test_notice.py:31` | as designed |
| 23 | §7.3's list of tests. | Seven more: `test_a_namespace_whose_inheritance_cannot_be_resolved_says_why` (#2); with the fixes, `test_an_error_that_names_no_card_shows_above_the_cards` (#4), `test_rename_in_yaml_mode_focuses_the_yaml_which_holds_the_name` (#6) and `test_a_draft_keeps_the_namespace_picked_over_the_preselected_one` (#3); pinning the rulings, `test_saving_without_a_name_in_card_mode_asks_for_one_and_writes_nothing` (#6) and `test_add_namespace_is_not_prefilled_under_root_or_run_settings` (#10, 2 cases); and `test_a_write_answered_after_another_node_is_selected_keeps_that_selection` (§4.4, 2 cases: `add`, `delete`). | `tests/canvas_app/test_namespaces.py:242-246, 260-277, 332`; `tests/canvas_app/test_create.py:102, 145, 193, 286` | commits `5effe26`, `4123ec7`, `2af80ef`, `aaa97ef`, `02b93dc`, `54625ab`, `d4e9cd3` |

### 2.4 Signatures and structure

None of these changes behaviour beyond §2.1. [read]

| Design | Built |
|---|---|
| `ui/components/` holds eleven components | `editor.tsx` (DecompositionEditor, CardList), `fields.tsx` (CodeField, FieldErrors, Banner, ConfirmRow, ValueEditor), `pickers.tsx` (NamespacePicker, NamespaceChecklist), `notices.tsx` (SafetyNotice, ProblemsBanner) |
| `TabProps` among the components' props | in `ui/tabs/props.ts` |
| no such module | `ui/load.ts`: `attempt` (D2's refusal to the tab, `BackendUnavailable` to the footer), `useLoaded`, `resolved` (#1) |
| `DecompositionEditorProps` | adds `onDeleted?` and `onBackendLost` |
| `CodeFieldProps`, `ValueEditorProps`, `NamespaceChecklistProps` | add `readOnly` and `describedBy`; `testId`; `label` and `testIdPrefix` |
| the exports of Appendix A.2 and A.3 | also `isTabId`, `safeTheme` (`protocol.ts`), `call` (`api.ts`), `safetyAcknowledged`, `acknowledgeSafety` (`drafts.ts`), `ancestors` (`tree.ts`), `errorDetail` (`backend.ts`) |
| `readFrameParams`: an unknown value takes its default | also: a `cap` that is neither `off` nor a decimal becomes `5` (`shared/protocol.ts:69, 149`) |
| §4.5: `/ui/` without a build answers 503 `UI_NOT_BUILT` | with the body `{"error": "not_built", "message": UI_NOT_BUILT}`, a code that is not one of D2's (`library/ui.py:43`) |
| §2.2: Browse's fallback groups `/decompositions` by each record's `namespaces` | it uses each namespace record's own `decompositions` list (`browse.tsx:92`); D2's cascades keep the two equal [read] |

Equal to the design [run: compared by script]: `page/host.ts` is Appendix A.1 verbatim and `ui/types.ts` is
A.3's types verbatim; every sentence of §4.7, the page's and the frame's, matches verbatim, and so do D2's two new
texts; every test id of A.5 exists; every test named in §7.3 to §7.5 exists.

---

## 3 · The public surface, from the code

### 3.1 The App package, `deep_reasoning.canvas_app`

The wheel carries `__init__.py` (`APP_NAME = "dr-library"`), `canvas-extension.json`, `panel.svg`,
`dist/index.js`, `ui/index.html`, `ui/assets/app.js` and `ui/assets/app.css`, and nothing from `canvas-app/`
[run: `uv build`]. The manifest [read; its keys run by `test_the_manifest_is_valid_…`]:

- `name` `dr-library`, `display_name` `Library`, `version` `0.1.0`, `entrypoint` `dist/index.js`;
- one `conversation_panels` entry, `decompositions` ("Decompositions", icon `panel.svg`), with tabs `browse` `/`,
  `create` `/create`, `namespaces` `/namespaces` and `tools` `/tools`;
- no `backend` block (D5 adds it when it stages the App).

`dist/index.js` is one ES module that imports nothing and exports `activate` [run: imported from a `blob:` URL in
`test_page_bundle.py`].

### 3.2 What the page bundle asks of Canvas

`activate(host)` registers `browse`, `create`, `namespaces` and `tools`, and returns one disposer for all four
[run: vitest and Chromium]. Each mount makes these requests through `host.agentServer.request` [run: vitest with
a fake `request`; read against a real agent-server]:

```text
GET  /api/canvas-extensions/installed/dr-library/backend            → {state, revision, prepared_revision, detail}
POST /api/canvas-extensions/installed/dr-library/backend/start {revision}   only when stopped or unhealthy, and prepared = revision
GET  /api/conversations/<id>/events/search?kind=ACPSessionControlsEvent&sort_order=TIMESTAMP_DESC&limit=1
GET  /api/agent-profiles/deep_reasoner                               → profile.acp_args → the cap
```

It then calls `host.appBackend.mountFrame(container, {path: "/ui/?…", title: <the tab's title>, onError})`. It
never calls `prepare` [run: vitest `backend.test.ts`].

### 3.3 The page ↔ frame contract, `shared/protocol.ts`

- **URL parameters**: `tab`, `parent`, `namespace`, `started`, `cap`, `focus`, `theme`, as design §4.3. They are
  written in that order, with empty values omitted; `cap` is always written.
- **Messages from the frame**: `{type: "dr-library/select-tab", tab, focus}` and `{type: "dr-library/reload"}`
  (with no other key), posted to `window.parent` with `targetOrigin = parent`. Nothing is posted the other way.
- **At the top level** (no parent window), `parent` is ignored, the frame posts nothing and shows its own tab
  row.

[run: vitest `protocol.test.ts`; Chromium]

### 3.4 `/ui/` on `dr-library serve`

[run: a real `dr-library serve` over `http.client`]

```text
GET /ui/            200  index.html, whatever the query
GET /ui/assets/<n>  200  for a file present when create_app ran;
                    else 404 {"error": "not_found", "message": "There is no file '<n>' in the panel's build."}
no index.html       503  {"error": "not_built", "message": UI_NOT_BUILT}
every answer above: Cache-Control: no-cache · X-Content-Type-Options: nosniff · Content-Security-Policy:
                    default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; base-uri 'none';
                    form-action 'none'; frame-ancestors http://localhost:* http://127.0.0.1:*
GET /ui             307 → http://127.0.0.1:<port>/ui/   (Starlette's slash redirect; no UI headers)
GET /ui/index.html  404 text/plain                      (no such route; no UI headers)
Host other than 127.0.0.1:<port> or localhost:<port> → 403 (D2's guard)
```

The page always mounts `/ui/` with the slash (`page/mount.ts:124`), so the 307, which design §4.5 says the
bridge refuses, is not reached from the panel [read].

### 3.5 What each tab reads and writes

| Tab | Reads on open (besides `/health` every 3 s and `/problems` at each new `rev`) |
|---|---|
| Decompositions | `/namespaces`, `/decompositions`, `/profile`, `/effective` |
| Create decomposition | `/namespaces`; `POST /validate` 400 ms after each change |
| Namespaces | `/namespaces`, `/profile`, `/tools`, `/decompositions`, `/namespaces/<selected>/effective` |
| Tools | `/tools` |

[run: requests recorded in Chromium as each tab opened]

The writes [run: vitest `api.test.ts` pins each body's keys, and the browser tests read the Library back]:
- `PUT /decompositions/<slug>` with `{yaml, use_when, hint, namespaces, base_version}`, and
  `DELETE /decompositions/<slug>?base_version=`;
- `PUT /namespaces/<name>` with `{yaml, base_version}`, or `{yaml, decompositions, base_version}` to attach and
  detach, and `DELETE /namespaces/<name>?base_version=`;
- `PUT /profile` with `{yaml, base_version}`.

Every body is JSON, sent with `Content-Type: application/json`.

---

## 4 · Structure and seams

### 4.1 The page bundle (`src/page/`)

`mountTab` returns its disposer at once and does its work under an `AbortController`. Each run does this:
1. It writes `LOADING` into the container.
2. It runs `ensureBackend`, `readConversationNamespace` and `readSpendCap` together. The last two never throw: a
   failure is `null` and `"5"`.
3. A backend that is not ok gives its sentence and **Try again**, which reruns. A host without `appBackend` gives
   `NO_FRAMES`.
4. Otherwise it calls `mountFrame` with the parameters, and listens for `message` events, accepting only those
   whose `source` is the `contentWindow` of the `<iframe>` in the container.
5. `select-tab` stores the focus for the target tab (read once, by that tab's next mount) and calls
   `surface.selectTab`. `reload` reruns from 1. `onError("not-ready")` reruns once per mount.
6. The disposer aborts, removes the listener, disposes the frame and empties the container.

[run: vitest `mount.test.ts`, 10 tests over the fake host; Chromium for `select-tab` and the focus]

`ensureBackend` is design §2.1's table, plus #8 and the fallback of #9 [run: vitest, 15 tests]. `readConversationNamespace`
reads `items[0].config_options`, the entry with `id` `namespace`: `current_value` is the namespace, and the
conversation counts as started when that entry's `options` has exactly one value [run: vitest]. That shape matches
the SDK fork's `EventPage.items` and `ACPSessionControlsEvent.config_options` (`sdk-s2` at `6f97bf3`) [read]; no
test reads a real agent-server. `readTheme` keeps the 23 listed tokens whose computed value passes
`isSafeThemeValue` [run: vitest; in Chromium the frame's `--oh-surface` and body background equal the parent
page's].

### 4.2 The frame: `app.tsx`, `api.ts`, `load.ts`

`App` shows only the safety notice until `localStorage` holds `dr-library.safety-acknowledged` = `"1"`. Then it
shows the tab row (standalone only), the problems banner, the tab and, when set, the backend-loss footer. It polls
`/health` every 3 s while `document.visibilityState` is `visible`, and on `visibilitychange`. `health` keeps its
identity until `rev` moves, so a tab refetches only on a new revision. [run:
`test_a_change_made_elsewhere_appears_without_a_reload`; read for the visibility rule]

The seam inside the frame is how `api.call` classifies an answer:
- 2xx with a JSON body → the data;
- a JSON body with `error` and `message` → `LibraryError`: D2 refused, and the tab shows D2's words;
- anything else, a network failure (status 0) and a non-JSON body of any status included → `BackendUnavailable`:
  the footer says `BACKEND_LOST(status)`, or `SESSION_ENDED` for 401, with a button that posts `reload` (in a
  panel) or reloads the page (standalone).

`load.attempt` routes the two; `load.resolved` is the one exception (#1). [run: vitest `api.test.ts`; Chromium for
status 0; read for 401]

### 4.3 Where the complexity sits: the cards and the editor

**The cards** (`ui/cards.ts`, 177 lines) are design §5.1: one card per message, and a parsed card is kept only if
it renders back to exactly its message; otherwise the message is a raw card. So
`cardsToMessages(messagesToCards(m))` is `m` by construction. [run: vitest, on a table, on 2,000 generated message
lists, and on every decomposition in deep_reasoner_beta's configs]

How deep_reasoner_beta's own decompositions open in the editor, measured at `d7334ae` over `docs/configs` and
`configs` with an uncommitted probe that walks them as the test does [run]:

| Decompositions | Messages | Task cards | Step cards | Output cards | Raw cards | Decompositions with a raw card |
|---|---|---|---|---|---|---|
| 43 (37 distinct names) | 147 | 53 | 55 | 20 | **19** | 10 |

All 19 raw cards are assistant messages with a blank line between `</think>` and `<repl>`, a form §5.1's grammar
does not include. They show as their role and text with `RAW_NOTE`, editable, and save back unchanged [run: such
a decomposition, opened and saved unchanged, made no revision].

**The editor** (`ui/components/editor.tsx`) serves Create (`record` null, draft key `create`) and an opened
decomposition (draft key `decomposition.<slug>`). [read unless marked]
- **State** is `{draft, attached, picked?}`, written to `localStorage` on every change, a pick in the
  namespace picker included. A stored draft wins over the
  record when the editor mounts, so a draft started at an older version saves with that `base_version` and meets
  D2's 409.
- **Saving** follows design §5.2 [run: the browser tests]: the card-mode name check, then `POST /validate`; errors
  placed by `loc`; warnings ask Save anyway or Cancel; then a `PUT` with one of three bodies:
  - `createBody`: `namespaces: [picked]`, `base_version: 0`;
  - `updateBody`: the checked set and the version opened;
  - `saveAsNextBody`: the head's namespaces, then the picked one, and the head's version.
- **Conflicts**: a 409 with a head is `EXISTS` (Save mine as v<n+1>, Rename) in Create, and D2's
  `CONFLICT_STALE` sentence (Reload, Save over it) in an opened one.
- **Success** clears the draft. Create resets to a new decomposition; an opened one reopens at the saved version.

### 4.4 Namespaces (`ui/tabs/namespaces.tsx`)

[run: `test_namespaces.py`, 16 cases; read for the rest]
- **Writes.** Each action changes one key of the namespace's own YAML document (parsed as YAML 1.1; never the
  effective view) and `PUT`s it at once with the version read. Attach and Detach send the record's YAML unchanged
  with a new `decompositions` list. Start new conversations here and Run settings `PUT /profile` the same way.
- **Refusals**, a 409 included, show D2's sentence above the fields, and the tab reloads. Nothing is retried.
- **Sources** come from `/namespaces/<n>/effective`: `profile` is "From the run settings"; this namespace is
  "Overridden here" ("Set here" on root); another is "Inherited from <it>"; none is "Not set: deep_reasoner's
  default".
- **Tools** offers every Library tool, plus `llm` while the profile has a `model`. Inherited grants are checked
  and fixed; a granted tool the Library does not define is flagged.
- **Selection after a write.** When D2 answers Add namespace, the new namespace is selected; when it answers Delete
  namespace, the parent (root for a top-level name). Since `d4e9cd3`, either select is dropped if the user selected
  another node while the write was in flight: a counter of selections is read when the write starts (for Delete,
  when the panel last rendered before the click) and compared when it is answered [run:
  `test_a_write_answered_after_another_node_is_selected_keeps_that_selection[add, delete]`, which hold the request
  in the browser, select `course_advisor`, then release it]. Until the answer is handled, a selected namespace that the
  `/health` poll has already dropped shows as the default namespace, as any unknown selection does [read]
  (`namespaces.tsx:116-121, 123-136, 147-154, 231`). The commit's reason: under load, the answer's select moved the panel after the user, or the test, had moved
  on. I did not reproduce the failure at `54625ab`; at `d4e9cd3`, `test_adding_and_deleting_a_namespace` and both cases of the new test passed 5 runs of 5 here, at a load average of 12 to 15 on 4 CPUs [run]. The implementer reports 2 of 10 before and 20 of 20 after under 14 busy loops; I did not repeat that.
- **Layout**: under 560 px the tree sits above the fields [read: `ui/styles.css:311-314`].

### 4.5 The Python: `library/ui.py` and D2's `create_app`

`ui_routes(root=UI_ROOT)` lists `root/assets` once, when `create_app` runs, and serves only those names.
`create_app` appends `*ui_routes()` after D2's routes, inside D2's `_Guard`, so `/ui/` gets D2's same-user and
`Host` checks; the JSON check does not apply to `GET`. `UI_ROOT` is `deep_reasoning/canvas_app/ui` beside the
installed package. [run: `test_ui.py`, 16 cases, and §3.4] D2's `api.py` is otherwise unchanged from the `5158693`
the design pins [run: `git diff`].

### 4.6 Seams left for D4 and D5

- **D4**: `ui/tabs/tools.tsx` (42 lines: the safety banner, then `GET /tools` rows with
  `factory <name>[ · <factory_from>]` and `granted in …`); `api.ts` already has `getTools`, `getTool`,
  `putTool`, `deleteTool` and `toolVersions`; the components of §2.4; `FrameParams` and `page/context.ts` for any
  new frame parameter. [read]
- **D5**: stage `canvas-extension.json`, `dist/index.js` and `panel.svg`, not `ui/` or `__init__.py`; the
  backend's argv is unchanged. D3's `SAFETY` has never been compared with D5's (#22). [read]

### 4.7 C2 as built on the Canvas fork (read only, not green)

[read: `openhands-c2` at `db3b4b9`]
- `src/types/canvas-extension.ts` declares the host types that `page/host.ts` copies. There, `appBackend` is
  required; D3 treats it as optional, for a Canvas without it.
- Its `mountFrame` documents: "The frame is the `<iframe>` appended to the container, kept there (also across
  session refreshes) until the returned disposer runs." That is the statement design §8.1 asked C2 for.
- `src/extensions/mount-app-backend-frame.ts:84` sets the frame's `src` to the lease URL plus `path` without its
  leading slashes, so D3's `/ui/?…` becomes `<ingress>/ui/?…`.
- `agentServer.request` "may take up to 60 s".

None of this has run with D3.

---

## 5 · Wiring

- **`pyproject.toml`**: the marker `browser`; `addopts = "-m 'not live and not browser'"`; `playwright==1.56.0`
  in the dev group; no new runtime dependency. The wheel ships the App package as package data with no
  configuration. The sdist carries `canvas-app/` (49 files, no `node_modules`). [run: `uv build`]
- **`.gitattributes`** marks `canvas_app/dist/**` and `canvas_app/ui/**` `linguist-generated=true -diff`;
  **`.gitignore`** adds `canvas-app/node_modules/`. [read]
- **`ci.yml`**, job `canvas-app` (#15, #16) [read; CI], in order:
  1. Node from `.nvmrc` (22), and deep_reasoner_beta's configs fetched at `d7334ae` for the cards corpus;
  2. `npm ci`, `npm run typecheck`, `npm run format:check`, `npm test`;
  3. `npm run build`, then the committed-build check, uploading the fresh build if the job fails;
  4. `uv sync --locked`, `playwright install --with-deps chromium`, `pytest -m browser tests/canvas_app -v -rA`.

  `tests/library/test_ui.py` runs in the `test` job.
- **`as_built/`.** This document's commit adds `as_built/` to the sdist's `exclude`, beside `docs/`. Pytest's
  `testpaths = ["tests"]` and the wheel's `packages` already leave it out, CI's ruff checks only `src` and
  `tests`, and the repo has no docs site. [run: before the change the sdist carried
  `as_built/d3-decompositions-panel.md`; after it neither the sdist nor the wheel does, `uv lock --check` passes,
  and pytest still collects 531 of 583 with the corpus set]

---

## 6 · Experiments and tests, as measured

### 6.1 The runs

| Run | Conditions | Commit | Result |
|---|---|---|---|
| CI [37090168700](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37090168700), job `test` | ubuntu-latest, Python 3.12, corpus at `d7334ae`, ruff check and format first | `5effe26` | **531 passed**, 52 deselected (48 browser, 4 live), 364.17 s; `test_ui.py` 16 passed [CI] |
| same run, job `canvas-app` | Node 22.23.3; Playwright's Chromium Headless Shell 141.0.7390.37 (build 1194) | `5effe26` | typecheck and format clean; vitest **148 passed, 1 skipped**; the fresh build equal to the committed files; browser tests **47 passed, 1 skipped**, 109.09 s; the job took 2 min 54 s [CI] |
| this sandbox, browser tests | `CI=true`, Playwright 1.56.0, `PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers` (build 1194), 4 CPUs shared with other agents' suites | `5effe26` | **47 passed, 1 skipped**, 214.15 s, at the first attempt [run] |
| this sandbox, `canvas-app/` | Node 22.22.0, `npm ci`, `DR_BETA_CHECKOUT` on `d7334ae` | `5effe26` | vitest **148 passed, 1 skipped**; `tsc` and prettier clean; `npm run build` byte-identical to the committed four files [run] |
| this sandbox, default suite | `CI=true DR_BETA_CHECKOUT=<clone of d7334ae> uv run pytest` | `5effe26` | **531 passed**, 52 deselected, 553.67 s (D1's, D2's and `test_ui.py`) [run] |
| CI [37139529187](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37139529187), job `canvas-app` | as above | `2af80ef` | typecheck and format clean; vitest **150 passed, 1 skipped**; the fresh build (7.09 kB and 151.96 kB) equal to the committed files; browser tests **50 passed, 1 skipped**, 130.25 s; the job took 3 min 5 s [CI] |
| same run, job `test` | as above | `2af80ef` | **531 passed**, 55 deselected (51 browser, 4 live), 357.56 s; `test_ui.py` 16 passed [CI] |
| this sandbox, browser tests | as above | `2af80ef` | **50 passed, 1 skipped**, 198.77 s, at the first attempt; nothing needed a rerun [run] |
| this sandbox, `canvas-app/` | Node 22.22.0, the same `node_modules` | `2af80ef` | vitest **149 passed, 2 skipped** without the corpus, **150 passed, 1 skipped** with it; `tsc` and prettier clean; a fresh build of both bundles byte-identical to the committed four files; `test_ui.py` 16 passed [run] |
| CI [37144441476](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37144441476), job `canvas-app` | as above | `d4e9cd3` | typecheck and format clean; vitest **151 passed, 1 skipped**; the fresh build (7.12 kB and 152.05 kB) equal to the committed files; browser tests **55 passed, 1 skipped**, 141.61 s; the job took 3 min 22 s [CI] |
| same run, job `test` | as above | `d4e9cd3` | **531 passed**, 60 deselected (56 browser, 4 live), 360.48 s; `test_ui.py` 16 passed [CI] |
| this sandbox, browser tests | as above | `d4e9cd3` | **55 passed, 1 skipped**, 236.28 s, at the first attempt; nothing needed a rerun; then `test_adding_and_deleting_a_namespace` and both cases of the selection test 5 times more, 15 of 15 passed, load average 12 to 15 on 4 CPUs [run] |
| this sandbox, `canvas-app/` | as above | `d4e9cd3` | vitest **150 passed, 2 skipped** without the corpus, **151 passed, 1 skipped** with it; `tsc` and prettier clean; a fresh build (7.12 kB, 2.89 kB gzip; 152.05 kB, 49.04 kB gzip) byte-identical to the committed four files; `test_ui.py` 16 passed [run] |

In every run the one skip in the browser tests is `test_the_notice_is_d5s_sentence_with_the_cap` (#22). With the
corpus, vitest's one skip is the guard that fails in CI when the corpus is missing (skipped because the corpus is
present, so the corpus round trip ran); without it and outside CI, both the round trip and the guard are skipped.

To reproduce:
- `CI=true uv run pytest -m browser tests/canvas_app` (needs Playwright's Chromium);
- in `canvas-app/`: `npm ci && DR_BETA_CHECKOUT=<deep_reasoner_beta at d7334ae> npx vitest run && npm run build`,
  then `git status --porcelain -- ../src/deep_reasoning/canvas_app` prints nothing.

### 6.2 E8's surviving check: the next conversation uses a decomposition saved in the panel

`test_a_decomposition_saved_in_create_is_used_by_the_next_conversation_in_its_namespace`, deterministic, below
Canvas.

**Conditions:**
- the fixture Library, its profile's client pointed at D1's `FakeOpenAI`, which answers every call with
  `<think>ok</think>` and `FinalAnswer("done")`;
- a real `dr-library serve`, started with only `PATH`, `LANG` and `TMPDIR`;
- `dr-acp --home <home>` with no `--config` (D2's `LibraryCatalog`), driven over stdio by D1's harness;
- Chromium on the frame, standalone, with `started=1`.

**Sequence and assertions:**
1. Conversation A opens (in `router`, the entry namespace, #21) and asks Q1, so A's run is built.
2. In the browser, Create decomposition: name "rank by prerequisites", a use-when line, the task "Which of CS201,
   CS310 and CS330 can I take first?", one step `FinalAnswer("CS201")`, namespace `router`, Save. The result line
   starts "✓ Saved 'rank by prerequisites' v1 in router."
3. A asks Q2. None of the model requests for that turn holds the task: the open conversation is unchanged.
4. Conversation B opens. Its menu offers `rank-by-prerequisites` described by the use-when line.
5. B asks Q3. `run.start.namespace` is `router`, `run.start.source.versions.decompositions["rank by
   prerequisites"]` is 1, and the model's first request for B holds the task.

The baseline is conversation A, opened before the save, beside B, opened after it.

**Result: passed** in CI at `5effe26` and at `2af80ef` (about 5.4 s and 6.9 s between the previous test's PASSED
line and its own) and at `d4e9cd3` (6.7 s), and here at `5effe26`, `2af80ef` and `d4e9cd3` (9.06 s, 10.22 s and 10.41 s for the
call) [CI; run].

### 6.3 E11, D3's part: each mount carries its own conversation

Against the fake host only:
- vitest `mount.test.ts`, `mounts each conversation with its own namespace`: conversation `c1` started in `router`
  and `c2` not started in `course_advisor` give frame paths with their own `namespace` and `started` [run];
- Chromium `test_the_frame_opens_with_the_conversations_namespace`: the built bundle, loaded from a `blob:` URL,
  mounts Create for `c2`, then `c1`; the frame preselects `course_advisor`, then `router`, and the second frame's
  URL carries `namespace=router`, `started=1` and `cap=7` (the fake profile's `--spend-cap-usd 7`) [run; CI].

The real `ACPSessionControlsEvent` from a real `dr-acp` behind a real agent-server is not in any test.

### 6.4 The browser tests

56 cases in eight files at `d4e9cd3`, each against its own real `dr-library serve` and a Library built from the
fixture. 27 of the 51 test functions also read the Library back through D2's Python API on the same file, so they assert what was
stored, not only what was shown; E8 asserts through `dr-acp` instead. [read; all pass, run and CI]

| File | Cases | What they pin |
|---|---|---|
| `test_browse.py` | 10 | the groups, `v<n>`, `/slug`, use-when and "inherited from"; top-level and unattached groups; save makes the next version; Attached to is the exact set; stale save offers Reload or Save over it; delete detaches everywhere; a write through the Python API appears within one poll; the fallback with a stale head (#1); `focus` |
| `test_create.py` | 18 | v1 in the picked namespace with the cards' messages, use-when and hint; the picker and its preselection (conversation, then the default); both success lines; no name in card mode asks for one and writes nothing (#6); errors on the card D2 names; an error that names no card above the cards (#4); Save anyway and Cancel; Save mine as v2 keeping the head's namespaces; Rename in YAML mode focusing the YAML (#6); View and Edit YAML; `use_when` inside the YAML refused in deep_reasoner's words; the draft across a reload, and the picked namespace kept over the preselected one (#3); use-when and hint kept by a save that did not touch them; an imported decomposition saved unchanged makes no version |
| `test_namespaces.py` | 16 | the tree and the default; each field's value and source; Override and Reset; variables key by key; a grant here beside inherited ones; attach and detach; Start new conversations here; add and delete, with D2's refusals for root, the default and a parent; no prefill under root or Run settings (#10, 2 cases); an Add or Delete answered after another node was selected keeps that selection (§4.4, 2 cases); run settings; `on` stored as `true`; keys the panel does not show survive; a stale head (#2) |
| `test_tools_tab.py` | 3 | the safety banner with cap 5 and 12; tools with their grants |
| `test_notice.py` | 3 | the notice until understood, remembered across a reload; `SAFETY_NO_CAP` for `cap=off`; D5's equality, skipped (#22) |
| `test_backend_loss.py` | 1 | a stopped server gives "The Library stopped answering (0)." and Restart posts `{"type": "dr-library/reload"}` to a parent page |
| `test_page_bundle.py` | 4 | the built bundle from a `blob:` URL registers the four tabs; §6.3; Show in Decompositions calls `selectTab("browse")` and the next mount opens the new entry; Canvas's theme reaches the frame |
| `test_e8_next_conversation.py` | 1 | §6.2 |

The slowest step here at `d4e9cd3` was E8's call (10.41 s); at `2af80ef`, E8's call (10.22 s); at `5effe26` it was the backend-loss test's setup, the
first in that run (24.76 s, which includes starting Chromium) [run].

### 6.5 vitest

151 tests in ten files at `d4e9cd3`: cards (27 + the CI guard), yaml (15: the YAML 1.1 agreement table, round
trips, literal blocks), protocol (22), context (18), backend (15: three of them the fallback of `450bed1` and
`c5964ff`), mount (10, jsdom), api (28), save (6), drafts (4), tree (6) [run; CI]. The cards test ran over the corpus in both places: `DR_BETA_CHECKOUT` was set, and the guard that
fails when it is missing in CI was skipped [run; CI].

---

## 7 · What I could not verify

1. **Everything through Canvas and C2.** The page bundle has run only in a fake host (§6.3); C2 is built but not
   green. Not tested by any test here: the App ingress and the bridge (that the frame's relative URLs resolve under
   `/app-backends/dr-library/`, the `Host` the backend sees, `Origin` on writes, `Content-Type` passing through,
   no redirects); the session cookie and its renewal; `onError` reasons from a real `mountFrame`; Electron's
   Chromium. The design's header item 1 is the only evidence for the bridge path, and it was a replica outside the
   repository.
2. **The agent-server's answers as the page reads them.** The backend status and `start`, the events search and
   the agent profile are faked in vitest and in `test_page_bundle.py`. The shapes match the SDK fork's models by
   reading (§4.1); `starting`, `unhealthy`, `NOT_APPROVED`, the 45 s timeout and the fallback after a `start` with
   no answer, with its fresh 45 s, ran only against a fake.
3. **D5's `SAFETY` equality** (#22): no run compares the two sentences.
4. **401 and the session ending**: `SESSION_ENDED` and its Reload are read only; the backend-loss test covers
   status 0 (a stopped server). Through the bridge, a dead backend would answer 502 or 503 [read].
5. **Restart, end to end**: the frame posting `reload` is run in Chromium, and the page remounting and checking the
   backend again on `reload` is run in vitest with a fake host; the two have not run together, and no test restarts
   a real backend through `start`.
6. **Whether D2's bare 500 crosses the bridge as a non-JSON 500**, which #1 relies on.
7. **Layout and accessibility**: the narrow-panel layout, the colour scheme beyond `--oh-surface`, labels,
   `aria-live` and `aria-describedby` are read, not checked.
8. **Design §6's and §9's agent-server and Canvas line references** were not re-checked, except the four C2
   points in §4.7.

If this document will not get shorter, the part that resists is §2.1: the editor and the Namespaces tab carry many
small decisions the design did not spell out, and each is something a user meets.
