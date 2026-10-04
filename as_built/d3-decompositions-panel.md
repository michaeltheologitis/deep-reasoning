# D3 · Decompositions panel, as built

**TASK-8** · Cartographer · the code at `a7a50db` (head of `v1-decompositions-panel`, after the literate refactor;
this file is on `as-built/d3-r2`) · checked against the design's **v8** (`088edf6`,
`docs/design/d3-decompositions-panel.md`) · D2 at `0f16c67`, merged as `e6f3beb` (its library code is `main`'s at
`16d4b3a`, PRs #11–#18) · deep_reasoner_beta `d7334ae` · 2026-10-04. Gate C's map of the code.

**Revisions** (newest first):
- **Fourth, the code at `a7a50db`.** Since the third: Michael's four UI changes B27–B30 (`141784a`/`436c513`,
  `2fda86d`/`93f4e24`, `9578c2e`/`7af632a`, `b5353af`/`97febe3`), the merge of D2's refactored head (`e6f3beb`), and
  20 refactor commits (`8d70477` … `a7a50db`). **The divergences are now against v8, not v1**: v2 to v8 took in the
  divergences the first three revisions named (as B1–B25) but three, which §2.4 carries;
  everything else in §2 comes from the merge and the refactor, which came after v8. Every line reference, count and
  size is re-measured; §7 is new (what the refactor did to test coverage, with mutation probes).
- Third, the code at `d4e9cd3` (commit `dcbe6b3`). Second, at `2af80ef`. First, at `5effe26`.

D3's code is `canvas-app/` (TypeScript: the page bundle and the frame UI), the App package
`src/deep_reasoning/canvas_app/` (manifest, icon, committed built files), `src/deep_reasoning/library/ui.py`, 13
lines in D2's `api.py` and `texts.py`, `tests/canvas_app/`, `tests/library/test_ui.py`, the `canvas-app` CI job
and the wiring of §5. D1's and D2's code is described only where D3 meets it.

**None of D3 has run inside Canvas.** Every test of the page bundle runs against a **faked host**: vitest's
`fakeHost` (`canvas-app/tests/fakes.ts`) and, in Chromium, a parent page in `test_page_bundle.py` whose `mountFrame`
appends an `<iframe>` pointing straight at `dr-library serve`. No test goes through the agent-server's App ingress,
its bridge, its session cookie, a real agent-server or Electron. C2's branch on the Canvas fork has moved from the
design's `db3b4b9` to `f4c7ae5`; I did not check whether it is green.

**Evidence marks.** Every claim carries one.
- **[run]**: executed in this sandbox at `a7a50db`, on 4 CPUs shared with other agents' suites:
  - `CI=true uv run pytest -m browser tests/canvas_app` (Playwright 1.56.0, preinstalled Chromium build 1194):
    **56 passed, 1 skipped**, 205.66 s, at the first attempt; nothing needed a rerun;
  - in `canvas-app/`: `npm ci`; `npx tsc --noEmit` and `npx prettier --check .`, clean; `npx vitest run`, **164
    passed, 1 skipped** with `DR_BETA_CHECKOUT=/home/user/deep_reasoner_beta` (`d7334ae`) and 163 passed, 2 skipped
    without; `npm run build`, after which `git status --porcelain` prints nothing (the four built files are
    byte-identical to the committed ones);
  - `DR_BETA_CHECKOUT=… uv run pytest tests/library/test_ui.py`: **16 passed**;
  - uncommitted probes: D2's answers over `http.client` and the frame in Chromium (a stale head; a 500 on the
    effective routes, injected with Playwright's `route`; B29's and B30's turns measured; a date through D2); the
    Refactorer's 47-state DOM probe, rerun at `e6f3beb` and at `a7a50db` in scratch worktrees; a trial merge of
    `a7a50db` into D4's `e866563`; five mutation probes (§7), each one temporary edit, reverted, the tree clean after.
  - Not rerun: the default suite (CI's 541 is cited) and `uv build` (the wiring is unchanged since the third
    revision but for one dependency line D1 brought through the merge, §5).
- **[CI]**: read from GitHub's logs: run 37175786974 at `a7a50db`, run 37172494852 at `e6f3beb`, both jobs green;
  live run 37172637866 (§6.5). D3 has no live tier of its own (design §7.1). I ran no paid model and no live run.
- **[read]**: read in the code and **not executed**: weaker evidence than [run]. §9 lists the read claims that
  matter most.

**Reading order.** §2 (divergences from v8) and §7 (coverage) first; §1, §3–§5 are the map; §6 the measured runs;
§8 what D3 relies on and what relies on it; §9 what I could not verify.

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
  main.tsx: Canvas's theme over DEFAULT_THEME on <html> → App: safety notice → tab → GET /health every 3 s
  api.ts: fetch("../<D2 path>"), JSON bodies   ─▶ dr-library serve: D2's API, unchanged
```

| Part | Lines at `a7a50db` | Where |
|---|---|---|
| the page bundle and the shared protocol | 463 + 168 | `canvas-app/src/page/`, `canvas-app/src/shared/protocol.ts` |
| the frame UI | 3,304 TypeScript, 373 CSS | `canvas-app/src/ui/` |
| Python | 59 + 5, plus 5 lines in D2's `api.py` and 8 in `texts.py` | `library/ui.py`, `canvas_app/__init__.py` |
| configuration | 153 (package, tsconfig, two Vite configs, `index.html`, Prettier, `.nvmrc`, `.gitattributes`, manifest, icon) | `canvas-app/`, `canvas_app/` |
| built files, committed | 7.52 kB page bundle; 150.63 kB script, 4.08 kB CSS, 0.37 kB HTML | `canvas_app/dist/`, `canvas_app/ui/` |
| tests | 1,823 vitest (163 of them the fakes); 1,591 browser (the fixture Library 99 and `conftest.py` 196 among them); 130 `test_ui.py` | `canvas-app/tests/`, `tests/canvas_app/`, `tests/library/` |

[run: `wc -l` and the build's own report] The length sits in two files: `ui/components/editor.tsx` (812: the
decomposition editor for Create and for an opened entry, §4.3) and `ui/tabs/namespaces.tsx` (885: the tree, seven
kinds of field and the run settings, §4.4). §6.6 gives the totals before and after the refactor.

---

## 2 · Divergences from the design (v8, `088edf6`)

No changelog entry names D3 [read: the six newest entries, to 03:46 UTC today]; the D2 merge's `Drift` records the
422 that #1 follows from. Every item below was found from the code. v8 was committed at 01:41 UTC; the merge
(`e6f3beb`, 02:35) and the refactor (`8d70477` to `a7a50db`, 03:01 to 03:59) came after it. Paths are under
`canvas-app/src/` unless they say otherwise.

### 2.1 Behaviour

| # | v8 says | Built | Where | Reason |
|---|---|---|---|---|
| 1 | B1, §2.2, §2.4, §2.6, §4.4, §8.2, §9 D2-2, §11 item 10, A.3's `Resolved`: D2 answers a stale head with a bare 500 on `/effective` and `/namespaces/<n>/effective`; `resolved()` reads a 500 from those routes as the stale head, takes the sentence from `GET /problems`, and never shows the backend-loss footer for it. "Any other 500 still does." | D2 answers a stale head with **422** `invalid`, its message the stale head's sentence (several stale heads joined by a newline) [run: `http.client` on both routes; `library.py:118-127, 664-670` read]. `resolved()` gives the tab the message of **any** `LibraryError` (any status) and rethrows everything else, so the tabs show D2's sentence as before and no footer [run: browse with a stale head; the two stale-head tests]. A **500** from those routes is now `BackendUnavailable`: the footer says "The Library stopped answering (500)." Behind it, Decompositions draws nothing (its one load fails as a whole) and Namespaces draws the tree, the title, the badge and Delete namespace with no fields and no message; the next `/health` answer clears the footer and the tab stays so until the Library's revision moves [run: probe with the routes answering 500]. D4's Tools tab calls `resolved(getEffective)` too (§8.2). | `ui/load.ts:66-82`; `ui/tabs/browse.tsx:46-60`; `ui/tabs/namespaces.tsx:277-281, 355-362` | commit `c503806` ("a 500 from those routes is now the backend failing, which reaches the footer like any other"); D2's `cd0b60c`. **Not pinned** (§7, M3) |
| 2 | §5.3: `document = parseYaml(namespace.yaml)` (YAML 1.1 in the browser); the profile likewise. | Override, Reset, Start new conversations here and the run settings start from D2's `record.data`, PyYAML's parse of the record's canonical YAML, sent as JSON. Attach and Detach still send `namespace.yaml` unchanged. D2 writes every record from `model_dump(mode="json")`, so a date is already a quoted string in the stored YAML and both parses agree on it [run: a namespace put with `since: 2024-01-02` is stored as `since: '2024-01-02'`, `data` holds the string]; that the two parses agree on every canonical record is [read: `shapes.py:103-127, 141-152, 208-217`, `records.py:23-42`]. | `ui/tabs/namespaces.tsx:285, 316-319, 806` | commit `8d70477` |

### 2.2 Structure and signatures (A.2, A.3, §4.1, §8.3)

None of these changes what a user sees: the Refactorer's 47-state DOM probe gives the same markup at `e6f3beb`
and at `a7a50db` in all 47 states [run, both ends rerun by me], which cover every tab, the editor's outcomes, the
YAML mode, the turns, the namespace editors and both stale-head views. It does not cover a 500 (#1).

| v8 | Built |
|---|---|
| `ui/theme.ts` with `DEFAULT_THEME`, `POLL_MS` and `applyTheme` (§4.1, A.3) | gone. `DEFAULT_THEME` is in `shared/protocol.ts:15-40`, and `THEME_TOKENS` is its keys (`:41`), still the 23 of A.2; `main.tsx:13-16` sets `{...DEFAULT_THEME, ...params.theme}` on `<html>`, as `applyTheme` did; `POLL_MS` is private to `ui/app.tsx:31` (commits `cc6122f`, `9aa78c9`, `897cb44`) [read; `git show` of the old file]. The page bundle now carries the default values: 7.17 → 7.52 kB [run] |
| A.3 and §8.3 (D4's contract): `api.ts` has `getNamespace`, `getDecomposition`, `getTool`, `toolVersions` | deleted, with their four `api.test.ts` rows (commit `0fed4d1`). `api.ts` keeps one function per endpoint the panel calls, plus `putTool` and `deleteTool` [read]. D4 calls none of the four (§8.2) |
| A.2: `export const APP_NAME = "dr-library"` in `protocol.ts` | deleted; the Python `APP_NAME` in `canvas_app/__init__.py` stays [read] |
| A.3: `class YamlSyntaxError` in `yaml.ts` | `yaml.ts:6` re-exports yaml's own `YAMLParseError`; `parseYaml` lets it through. The old wrapper caught only that class too, so the same errors become `YAML_SYNTAX` with the same message (commit `341f0fb`) [read] |
| A.3's `tree.ts`: `namespaceTree`, `ancestors` | also exports `ROOT` (`tree.ts:8`); Namespaces takes a deleted namespace's parent as `ancestors(name).at(-1) ?? ROOT` (commit `f7b323b`) [read] |

Refactored without a change of signature [read]: the editor builds a new and an opened decomposition from one
`fresh(record)` (`editor.tsx:105-121`), validates through one `validateDraft` (`:198-202`), and draws a card's text
areas with one `field()` helper (`:747-761`); `OutcomeView` no longer takes the draft and the pick; Namespaces opens
each field with a `FieldRow` (`namespaces.tsx:416-427`).

**B27–B30 as built equal v8** [run unless marked]:
- **B27**: the events search is
  `?kind=openhands.sdk.event.acp_session_controls.ACPSessionControlsEvent&sort_order=TIMESTAMP_DESC&limit=1`
  (`page/context.ts:20-21, 30-32`) [read]; vitest's `eventsSearch` and `test_page_bundle.py`'s fake match only that
  kind [read], and the cases v8 lists pass.
- **B28**: the result card's label and accessible name are `observation` (`LABELS.output`, `ui/texts.ts`), `RAW_NOTE`
  ends "or an observation."; `kind: "output"`, `OutputCard` and `dr-card-<i>-output` keep their names [read].
- **B29**: `cardGroups`, `turnNumbers`, `addTurn` and `removeTurn` (`ui/cards.ts:148-193`) as §5.1 says. After **+
  turn** twice the turns read [think, code], [observation, think, code], [observation, think, code]; their ✕ are named
  `Remove turn 1..3` with ids `dr-remove-1`, `dr-remove-2`, `dr-remove-4` (each turn's first card) [run: probe].
- **B30**: no "written by you, not run" anywhere; `.card-group` has 14 px above and below its `--oh-border` divider,
  `.cards .field` 4 px below each field, and the textareas are blocks (`ui/styles.css:270-297`). Measured: 4.0 px
  inside a turn (5 gaps), 33.0 px between groups (3 gaps) [run: probe], v8's figures.

### 2.3 Tests and sizes

| v8 | Built |
|---|---|
| §7.2: 169 vitest cases at `7af632a` (168 + 1 with the configs) | **165** at `a7a50db`: 164 + 1 with the configs, 163 + 2 without [run; CI]. `api` has 24: the rows of the four deleted functions went, and the `a b` → `a%20b` encoding check moved to `deleteDecomposition`'s row [read] |
| §7.3: 59 browser cases at `97febe3`; the lists name `test_use_when_and_hint_survive_a_save_that_did_not_touch_them`, `test_the_built_bundle_activates_and_registers_four_tabs` and `test_saving_an_opened_decomposition_makes_its_next_version` (and so do the Gate B property rows for the frame protocol and for writes) | **57** cases in 52 functions (56 + 1) [run; CI]. The first is folded into the third, renamed `test_saving_an_opened_decomposition_makes_its_next_version_keeping_use_when_and_hint`; the second is deleted (commit `875e113`). §7 says what each leaves pinned |
| §10, B16, the Gate B size: code 4,623 and tests 3,308 at `d4e9cd3`; B15: 7.12 kB and 152.05 kB | §6.6: code **4,525**, tests **3,544** by the design's rule; 7.52 kB and 150.63 kB [run; CI] |

### 2.4 Carried from the earlier revisions: built before v8, not recorded in it

| Earlier # | v8 says | Built | Where | Reason |
|---|---|---|---|---|
| 5 | §2.3: View YAML shows `POST /validate`'s canonical `yaml` | when the draft does not validate (no canonical YAML), it shows the browser's own YAML 1.1 rendering of `{name, messages}` [read] | `ui/components/editor.tsx:313-324` | none recorded |
| 13 | §5.1: `cardIndexForLoc("messages.3.content")` is 3, `null` "for other locations" | any `messages.<n>` or `messages.<n>.<…>` maps to `n` (`messages.0.role` → 0, `messages.12` → 12) [run: vitest at the first revision; the regex is unchanged, read] | `ui/cards.ts:39, 196-199` | none recorded |
| 14 | §4.6: "Both minify" | the frame UI is minified; the page bundle's names are shortened but its whitespace kept, as Vite's library build does for `es`: 227 lines, 7.52 kB [run] | `canvas-app/vite.page.config.ts` | none recorded |

---

## 3 · The public surface, from the code

### 3.1 The App package, `deep_reasoning.canvas_app`

`__init__.py` (`APP_NAME = "dr-library"`), `canvas-extension.json`, `panel.svg`, `dist/index.js`, `ui/index.html`,
`ui/assets/app.js` and `ui/assets/app.css` [read; unchanged since the third revision, whose `uv build` showed the
wheel carries exactly these and nothing of `canvas-app/`]. The manifest: `name` `dr-library`, `display_name`
`Library`, `version` `0.1.0`, `entrypoint` `dist/index.js`; one `conversation_panels` entry, `decompositions`
(icon `panel.svg`), with tabs `browse` `/`, `create` `/create`, `namespaces` `/namespaces`, `tools` `/tools`; no
`backend` block (D5 adds it) [read; its keys run by `test_ui.py`]. `dist/index.js` is one ES module that imports
nothing and exports `activate` [run: imported from a `blob:` URL in `test_page_bundle.py`].

### 3.2 What the page bundle asks of Canvas

`activate(host)` (`page/index.ts:7-12`) registers the four tabs and returns one disposer [run: vitest; §7 M2 for
the browser tier]. Each mount makes these requests through `host.agentServer.request` [run: vitest over fakes; read
against the real agent-server]:

```text
GET  /api/canvas-extensions/installed/dr-library/backend            → {state, revision, prepared_revision, detail}
POST /api/canvas-extensions/installed/dr-library/backend/start {revision}   only when stopped or unhealthy, and prepared = revision
GET  /api/conversations/<id>/events/search?kind=openhands.sdk.event.acp_session_controls.ACPSessionControlsEvent&sort_order=TIMESTAMP_DESC&limit=1
GET  /api/agent-profiles/deep_reasoner                               → profile.acp_args → the cap
```

Then `host.appBackend.mountFrame(container, {path: "/ui/?…", title: <the tab's title>, onError})`
(`page/mount.ts:123-127`). It never calls `prepare` [run: vitest].

### 3.3 The page ↔ frame contract, `shared/protocol.ts`

- **URL parameters** `tab`, `parent`, `namespace`, `started`, `cap`, `focus`, `theme`, written in that order, empty
  values omitted, `cap` always written (`frameSearch`, `:102-112`). `readFrameParams` (`:140-156`) gives a bad value
  its default; `parent` must be exactly an `http(s)` origin; `cap` must be `off` or a decimal.
- **Messages from the frame**: `{type: "dr-library/select-tab", tab, focus}` and `{type: "dr-library/reload"}` with
  no other key (`isFrameMessage`, `:158-168`), posted to `window.parent` with `targetOrigin = parent`.
- **At the top level** `parent` is null: the frame posts nothing and shows its own tab row.

[run: vitest `protocol.test.ts`, 22 cases; Chromium]

### 3.4 `/ui/` on `dr-library serve`

Unchanged since the third revision (`library/ui.py`, and D3's route line in `api.py:364`) [read; `test_ui.py` 16
passed, run]:

```text
GET /ui/            200  index.html, whatever the query
GET /ui/assets/<n>  200  for a file present when create_app ran; else 404 {"error": "not_found", "message": …}
no index.html       503  {"error": "not_built", "message": UI_NOT_BUILT}
every answer above: Cache-Control: no-cache · X-Content-Type-Options: nosniff · the CSP of design §4.5
GET /ui             307 (Starlette's slash redirect) · Host other than 127.0.0.1:<port> or localhost:<port> → 403
```

The page always mounts `/ui/` with the slash (`page/mount.ts:124`), so the 307 is not reached from the panel [read].

### 3.5 What each tab reads and writes

| Tab | Reads on open (besides `/health` every 3 s and `/problems` at each new `rev`) |
|---|---|
| Decompositions | `/namespaces`, `/decompositions`, `/profile`, `/effective` |
| Create decomposition | `/namespaces`; `POST /validate` 400 ms after each change |
| Namespaces | `/namespaces`, `/profile`, `/tools`, `/decompositions`, `/namespaces/<selected>/effective` |
| Tools | `/tools` |

[read: `loadBrowse`, `CreateTab`, `loadLibrary`, `ToolsTab`; recorded in Chromium at the first revision, and since
then only Decompositions' `/problems` read after a 500 has gone, #1]

Writes [run: vitest `api.test.ts` pins each body's keys; the browser tests read the Library back]:
`PUT /decompositions/<slug>` `{yaml, use_when, hint, namespaces, base_version}` and `DELETE …?base_version=`;
`PUT /namespaces/<name>` `{yaml, base_version}`, or `{yaml, decompositions, base_version}` to attach and detach, and
`DELETE …?base_version=`; `PUT /profile` `{yaml, base_version}`. Every body is JSON with
`Content-Type: application/json` (`api.ts:105-131`).

---

## 4 · Structure and seams

### 4.1 The page bundle (`src/page/`)

`mountTab` (`mount.ts:59-137`) returns its disposer at once and works under an `AbortController`; `run`
(`:98-129`) writes `LOADING`, runs `ensureBackend`, `readConversationNamespace` and `readSpendCap` together (the
last two never throw: `null` and `"5"`), then shows the backend's sentence with **Try again**, or `NO_FRAMES`
without `appBackend`, or mounts the frame and listens for messages, accepting one only when `event.source` is the
`contentWindow` of the container's `<iframe>` (`:70-84`). `select-tab` stores the focus for the target tab and calls
`surface.selectTab` (panel surfaces only); `reload` reruns; `onError("not-ready")` reruns once per mount (`:86-90`).
[run: vitest `mount.test.ts`, 10 cases over the fake host; Chromium for `select-tab` and the focus]

`ensureBackend` (`backend.ts:45-102`) is design §2.1's table: `starting` is polled every 500 ms within 45 s, then
`STILL_STARTING`; a `start` that gets no answer (an error without a numeric `status`) reads the status with a fresh
45 s (`:90-96`); a `start` the agent-server answered ends in `BACKEND_FAILED` in its words [run: vitest, 15 cases].
`readConversationNamespace` (`context.ts:25-52`) reads the newest event's `config_options` entry `namespace`:
`current_value`, and started when `options` has exactly one value [run: vitest, over a fake of the search].
`readTheme` keeps each of the 23 tokens whose computed value passes `isSafeThemeValue` [run: vitest; in Chromium the
frame's `--oh-surface` equals the parent page's].

### 4.2 The frame: `main.tsx`, `app.tsx`, `api.ts`, `load.ts`

`main.tsx` reads the URL, sets the theme on `<html>` and renders `App`. `App` (`app.tsx:67-131`) shows only the
safety notice until `localStorage` holds `dr-library.safety-acknowledged` = `"1"`; then the tab row (standalone only),
the problems banner, the tab and, when set, the backend-loss footer. `useHealth` (`:38-65`) polls `/health` every
3 s while the document is visible and on `visibilitychange`; `health` keeps its identity until `rev` moves, so a tab
refetches only on a new revision, and a `/health` answer clears the footer. [run:
`test_a_change_made_elsewhere_appears_without_a_reload`, `test_a_backend_that_stops_answering_offers_restart`; read
for the visibility rule]

The seam inside the frame is how `api.call` classifies an answer: 2xx with a JSON body → the data; a JSON body with
`error` and `message` → `LibraryError` (D2 refused; the tab shows D2's words); anything else, no answer (status 0)
and a non-JSON body of any status included → `BackendUnavailable` (the footer: `BACKEND_LOST(status)`, or
`SESSION_ENDED` for 401, with a button that posts `reload` in a panel or reloads the page standalone).
`load.attempt` (`load.ts:15-29`) routes the two; `useLoaded` (`:38-64`) loads per `deps` and drops a late answer;
`resolved` (`:72-82`) turns a `LibraryError` into the tab's `failure` and rethrows the rest (#1). There is no
exception left for any status. [run: vitest `api.test.ts`, Chromium for status 0 and 500; read for 401]

### 4.3 Where the complexity sits: the cards and the editor

**The cards** (`ui/cards.ts`, 199 lines): one card per message, and a parsed card is kept only if it renders back
to exactly its message, otherwise a raw card, so `cardsToMessages(messagesToCards(m))` is `m` by construction
(`:41-135`). The editor shows them in groups (`cardGroups`, `:158-168`): an observation and the step after it are
one turn; turn 1 is the first step alone; the task and raw cards are in no turn (B29). [run: vitest, 44 cases, a
table, 2,000 generated message lists, every deck of up to six cards, and every decomposition in deep_reasoner_beta's
`docs/configs` and `configs`] How those 43 decompositions open, measured at the second revision over the same 39
files (19 raw cards in 10 decompositions, each an assistant message with a blank line between `</think>` and
`<repl>`), is design B17; the corpus walk now uses `readdirSync(…, {recursive: true})` and reads the same 39 files
[run: `find`; §7 M5].

**The editor** (`ui/components/editor.tsx`) serves Create (`record` null, draft key `create`) and an opened
decomposition (`decomposition.<slug>`). [read unless marked]
- **State** is `{draft, attached, picked?}` (`:84-88`), written to `localStorage` on every change, a pick included
  (`keep`, `:216-221`). A stored draft wins over the record at mount, so a draft started at an older version saves
  with that `base_version` and meets D2's 409. A save, **Discard draft** and **Reload** all restart from
  `fresh(…)`, which has no `picked`, so Create returns to the preselection [run for Discard draft:
  `test_a_draft_keeps_the_namespace_picked_over_the_preselected_one`].
- **Saving** (`save`, `:271-297`): the card-mode name check, then `POST /validate`; errors placed by `loc` (name,
  card, else the block between the picker or Attached to and the cards, `:337-352, 418-426`); warnings ask Save
  anyway or Cancel; then `send` (`:234-269`) with `createBody`, `updateBody` or, from **Save mine as v<n+1>**,
  `saveAsNextBody` (`ui/save.ts`). [run: the browser tests]
- **Conflicts**: a 409 with a head is `EXISTS` (Save mine, Rename) in Create and D2's `CONFLICT_STALE` (Reload, Save
  over it) in an opened one.
- **Attached to** marks a namespace with a checked ancestor as checked, fixed and "also used in … (inherited)",
  recomputed from the boxes on each click (`inheritedNotes`, `:147-160`) [run:
  `test_attached_to_is_the_exact_set_after_a_save`].

### 4.4 Namespaces (`ui/tabs/namespaces.tsx`)

[run: `test_namespaces.py`, 16 cases; read for the rest]
- **Writes.** Each action changes one key of the record's `data` (#2) and `PUT`s its YAML at once with the version
  read (`save`, `:288-297`); Attach and Detach send `namespace.yaml` with a new `decompositions` list (`:303-313`);
  Start new conversations here and the run settings `PUT /profile` from `profile.data`.
- **Refusals**, a 409 included, show D2's sentence in one message line above the fields, and the tab reloads
  (`write`, `:134-140`). Nothing is retried.
- **Sources** come from `/namespaces/<n>/effective` through `resolved` (#1): "From the run settings", "Overridden
  here" ("Set here" on root), "Inherited from <it>", "Not set: deep_reasoner's default" (`sourceOf`, `:89-94`).
- **Selection after a write** (B26): Add and Delete select the new namespace or the parent only if the selection
  counter has not moved since the write began (`selectOnAnswer`, `:126-131`); Add namespace is empty under root and
  Run settings, `<selected>.` elsewhere (`:150-153`, B25).
- **Layout**: under 560 px the tree sits above the fields (`ui/styles.css:316`) [read].

### 4.5 The Python

`ui_routes(root=UI_ROOT)` lists `root/assets` once, when `create_app` runs, and serves only those names;
`create_app` appends `*ui_routes()` after D2's routes (`api.py:364`), inside D2's `_Guard`. D3's lines in D2's files:
the import (`api.py:32`), the route line, a docstring sentence, and `UI_NOT_BUILT` and `ui_file_missing` in
`texts.py` [run: `git diff 0e0a394 a7a50db`, which shows these and nothing else in D2's code].

---

## 5 · Wiring

Unchanged since the third revision [read; `git diff d4e9cd3 a7a50db` touches only D1's and D2's workflow files and
one runtime dependency in `pyproject.toml`, D1's `genai-prices`, through the merge]:
- **`pyproject.toml`**: marker `browser`; `addopts = "-m 'not live and not browser'"`; `playwright==1.56.0` in the
  dev group; the sdist excludes `docs/` and `as_built/`.
- **`.gitattributes`** marks `canvas_app/dist/**` and `canvas_app/ui/**` `linguist-generated=true -diff`;
  **`.gitignore`** adds `canvas-app/node_modules/`.
- **`ci.yml`**, job `canvas-app`, on every push and pull request (`ci.yml:4-6, 33`): Node from `.nvmrc`;
  deep_reasoner_beta at `d7334ae`; `npm ci`, typecheck, format check, `npm test`, `npm run build`; the check
  `git status --porcelain -- src/deep_reasoning/canvas_app` (`:65-68`); `uv sync --locked`, `playwright install`,
  `pytest -m browser tests/canvas_app -v -rA`. `tests/library/test_ui.py` runs in the `test` job.

---

## 6 · Experiments and tests, as measured

### 6.1 The runs

| Run | Commit | Result |
|---|---|---|
| CI [37175786974](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37175786974), job `canvas-app` (Node 22.23.3, Chromium Headless Shell 141.0.7390.37, build 1194) | `a7a50db` | typecheck and format clean; vitest **164 passed, 1 skipped**; the fresh build (7.52 kB, 3.11 kB gzip; 150.63 kB, 48.76 kB gzip) equal to the committed files; browser **56 passed, 1 skipped**, 138.67 s; job 3 min 20 s [CI] |
| same run, job `test` (Python 3.12, corpus at `d7334ae`, ruff first) | `a7a50db` | **541 passed**, 62 deselected (57 browser, 5 live), 392.49 s; `test_ui.py` 16 passed; D3's falsifier at the store, `tests/library/test_acp.py` (2) and `test_catalog.py` (6), passed [CI] |
| CI [37172494852](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37172494852), both jobs | `e6f3beb` (the merge) | vitest **168 passed, 1 skipped**; build 7.17 kB and 152.42 kB, equal to the committed files; browser **58 passed, 1 skipped**, 127.16 s; `test` **541 passed**, 64 deselected [CI] |
| this sandbox, browser tests | `a7a50db` | **56 passed, 1 skipped**, 205.66 s, first attempt [run] |
| this sandbox, `canvas-app/` (Node 22.22.0) | `a7a50db` | vitest **164 + 1** with the corpus, **163 + 2** without; `tsc` and Prettier clean; the build byte-identical to the committed four files; `test_ui.py` 16 passed [run] |

Earlier: CI 37090168700 at `5effe26`, 37139529187 at `2af80ef`, 37144441476 at `d4e9cd3`, all green (third
revision). In every run the browser skip is `test_the_notice_is_d5s_sentence_with_the_cap` (D5's `dr_app` is not
installed); with the corpus, vitest's skip is the guard that fails in CI when the corpus is missing.

To reproduce: `CI=true uv run pytest -m browser tests/canvas_app`; in `canvas-app/`:
`npm ci && DR_BETA_CHECKOUT=<deep_reasoner_beta at d7334ae> npx vitest run && npm run build`, then
`git status --porcelain -- ../src/deep_reasoning/canvas_app` prints nothing.

### 6.2 E8's surviving check: the next conversation uses a decomposition saved in the panel

`test_a_decomposition_saved_in_create_is_used_by_the_next_conversation_in_its_namespace`, unchanged since the third
revision [read]. Conditions: the fixture Library with its profile's client at D1's `FakeOpenAI`; a real
`dr-library serve` with only `PATH`, `LANG` and `TMPDIR`; `dr-acp --home <home>` without `--config`, driven by D1's
harness; Chromium on the frame, standalone. Conversation A opens (in `router`) and asks Q1; the browser saves "rank by
prerequisites" in `router`; A asks Q2 and no request for that turn holds the task; conversation B's menu offers
`rank-by-prerequisites` with its use-when line; B's `run.start` records `router` and version 1, and its first model
request holds the task. The baseline is A, opened before the save, beside B, opened after it. **Passed** in CI at
`a7a50db` (about 6.7 s between PASSED lines) and here (9.99 s for the call) [CI; run].

### 6.3 E11, D3's part: each mount carries its own conversation

Against the fake host only: vitest `mounts each conversation with its own namespace`, and Chromium
`test_the_frame_opens_with_the_conversations_namespace` (the built bundle mounts Create for `c2`, then `c1`: the
frame preselects `course_advisor`, then `router`, with `namespace=router`, `started=1`, `cap=7` in the URL) [run; CI].
Both fakes answer only the module-qualified kind (B27). No real `ACPSessionControlsEvent` is in any test.

### 6.4 The tests

**Browser**: 57 cases in eight files, each against its own real `dr-library serve` over the fixture Library; 27 of
the 52 functions also read the Library back through D2's Python API [run: collected and counted].

| File | Cases | What they pin |
|---|---|---|
| `test_browse.py` | 10 | groups, `v<n>`, `/slug`, use-when, "inherited from"; top-level and unattached groups; an opened save makes the next version **and keeps use-when and hint**; Attached to is the exact set; a stale save offers Reload or Save over it; delete detaches everywhere; a change made elsewhere appears within a poll; the fallback with a stale head; `focus` |
| `test_create.py` | 20 | v1 in the picked namespace; the turns (B28, B29) and their spacing (B30); the picker and its preselection; both success lines; no name in card mode; errors on their card and above the cards; Save anyway and Cancel; Save mine as v2; Rename in YAML mode; View and Edit YAML; `use_when` in the YAML refused; the draft across a reload and its pick; an imported decomposition saved unchanged makes no version |
| `test_namespaces.py` | 16 | as in the third revision: tree, values and sources, Override and Reset, variables, grants, attach and detach, Start new conversations here, add and delete with D2's refusals, no prefill (2), a late write keeps the selection (2), run settings, `on` stored `true`, unshown keys survive, a stale head |
| `test_tools_tab.py` | 3 | the safety banner with cap 5 and 12; tools with their grants |
| `test_notice.py` | 3 | the notice until understood; `SAFETY_NO_CAP`; D5's equality, skipped |
| `test_backend_loss.py` | 1 | a stopped server gives "The Library stopped answering (0)." and Restart posts `reload` to a parent page |
| `test_page_bundle.py` | 3 | §6.3; Show in Decompositions calls `selectTab("browse")` and the next mount opens the new entry; Canvas's theme reaches the frame |
| `test_e8_next_conversation.py` | 1 | §6.2 |

**vitest**: 165 cases in ten files: `api` 24, `backend` 15, `cards` 44 (the corpus guard among them), `context` 19,
`drafts` 4, `mount` 10, `protocol` 22, `save` 6, `tree` 6, `yaml` 15 [run; CI].

### 6.5 The live path below D3

D3 has no live tier (design §7.1), and the refactor touched no code below the frame. D3's falsifier at the store
(D2 design §7.3: a saved decomposition reaches the next conversation at its saved version) runs deterministically in
CI's `test` job (§6.1). Its live counterpart is D2's
`tests/library/test_live.py::test_an_edited_decomposition_reaches_a_real_run_at_its_saved_version` (gpt-6-luna). The last `live.yml` run is
[37172637866](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37172637866), on 2026-10-04 02:57,
**at `0f8828a`** (`v1-library-store-08-app-backend`, PR #18's branch): 5 passed, that test among them, 49.07 s [CI].
`0f8828a`'s `src/` and `tests/` equal `0f16c67`'s, and between `0f16c67`'s parent code (`0e0a394`) and `a7a50db`,
D2's and D1's code differ only by D3's lines of §4.5 [run: `git diff`]. No live run has been made at `a7a50db`.

### 6.6 Size, before and after the refactor

| Measure | `d4e9cd3` | `e6f3beb` (after B27–B30) | `a7a50db` |
|---|---|---|---|
| Design's rule (code: `canvas-app/src`, configuration, manifest, icon, `ui.py`, `__init__.py`; tests: `canvas-app/tests`, `tests/canvas_app`, `test_ui.py`), all lines (non-blank) | code 4,623 (4,285), tests 3,308 (2,968) | 4,670 (4,329), 3,596 (3,234) | **4,525 (4,189), 3,544 (3,190)** |
| The Refactorer's rule, lines added over D2's head (lockfiles, built files, `docs/`, `as_built/` left out; code also counts the CI job 55, `pyproject.toml` 6, `.gitignore` 1, and D3's 13 lines in D2's files) | — | code 4,745, tests 3,596 | **4,600, 3,544** |

[run: `git show … | wc -l` per file, and `git diff --numstat 0f16c67`; the second rule reproduces the task row's
`Lines Before` 8,341 and `Lines After` 8,144] The refactor took 145 lines of code (editor 886 → 812, Namespaces 902
→ 885, `theme.ts` 39 → 0, `api.ts` 186 → 179, `load.ts` 89 → 82, `yaml.ts` 26 → 20; `protocol.ts` 165 → 168,
`main.tsx` 15 → 17) and 52 of tests (`api.test.ts` 14, `fakes.ts` 11, `test_create.py` 11, `test_page_bundle.py` 9,
`cards.test.ts` 5, `conftest.py` 4, `mount.test.ts` 1, against `test_browse.py` +3) [run]. At the workspace's 300
lines an hour, 8,069 lines are about 27 h at Gate C.

---

## 7 · Test coverage the refactor changed, with mutation probes

Each probe is one temporary edit at `a7a50db`, the bundles rebuilt where a browser test reads them, the named
tests run, then the edit reverted with `git checkout` and `git status --porcelain` empty [run, every row].

| # | What the refactor did | Probe (temporary edit) | Tests run | Result |
|---|---|---|---|---|
| M1 | Folded `test_use_when_and_hint_survive_a_save_that_did_not_touch_them` (Create file, through `focus=`) into Browse's opened-save test, as an assertion on `summarize then rank` | `editor.tsx`'s `fresh()`: `hint: ""` instead of the record's hint | the renamed Browse test | **caught**: `('comparing many courses', None) != (…, 'the courses')`. The property is still pinned |
| M2 | Deleted `test_the_built_bundle_activates_and_registers_four_tabs` | `page/index.ts` registers every tab but `tools`; both bundles rebuilt | `test_page_bundle.py`; vitest `mount.test.ts` | browser tier: **3 passed** (its tests mount only Create and Decompositions). vitest: **caught** by `registers exactly the four tabs, and its disposer removes them`. The built bundle's four registrations are pinned only through the source, plus CI's committed-build check |
| M3 | Dropped `resolved()`'s 500 rule: a 500 from the effective routes now reaches the footer (#1) | `resolved()` also turns a `BackendUnavailable` into the tab's `failure` | all vitest; `test_browse.py`, `test_namespaces.py`, `test_backend_loss.py` | **not caught**: 164 + 1 vitest and 27 browser cases pass. Nothing pins what a 500 from `/effective` or `/namespaces/<n>/effective` does, before or after the refactor; the stale-head tests now exercise D2's 422 only |
| M4 | Same commit: the stale head now arrives as D2's 422 | `resolved()` rethrows `LibraryError` too | the two stale-head tests | **caught**, both: no `dr-effective-failed` banner |
| M5 | Corpus walk replaced by `readdirSync(…, {recursive: true})` | `recursive: false` | `cards.test.ts` with the corpus | **caught**: "expected 0 to be greater than 30" |

Not probed, because nothing was cut: the four deleted `api.test.ts` rows went with the functions they tested;
`fakes.ts`'s `deferred` became `Promise.withResolvers` (`mount.test.ts`, same assertions); conftest's `text()` had
no caller [read].

---

## 8 · What D3 relies on, and what relies on it

### 8.1 D3 relies on

- **D2's HTTP API as on `main`.** `main`'s `src/deep_reasoning/library` (at `16d4b3a`, PRs #11–#18) equals
  `0f16c67`'s, which D3 merged [run: empty `git diff`]. The behaviours D3 reads: the routes and bodies of §3.5,
  `extra="forbid"` bodies, D2's error shape (`error`, `message`, `errors`, `head`); a 409 `conflict` carrying the head;
  `POST /validate`'s `slug` and canonical `yaml`; `/health`'s `rev` and `default_namespace`; `record.data` on every
  record (`records.py:23-69`, a computed field, PyYAML's parse of `yaml`); **a stale head answered 422 with its
  sentence** on both effective routes (`library.py:118-127`, `664-670`), on which #1 now rests; `/problems`; the
  guard (same user, `Host`, JSON) [read; run for the 422 and the guard's 403 via `test_ui.py`]. `main` also carries
  D1's interim stop-test fix (PR #10, `tests/acp/test_stop.py`) and a contract-doc edit that D3's branch does not
  [run: `git log a7a50db..origin/main`].
- **C2's host API.** `page/host.ts` is a structural subset of `src/types/canvas-extension.ts` on the Canvas fork's
  `feat/agent-surfaces`, now at `f4c7ae5`: `registerPage`, the mount context (`container`, `conversationId`,
  `surface.selectTab` on a `conversation-panel`), `agentServer.request` ("each may take up to 60 s"), and
  `appBackend.mountFrame(container, {path, title, onError})` with its four `onError` reasons, whose doc still says
  the appended `<iframe>` is the frame and stays until the disposer runs. C2 declares `appBackend` required; D3
  treats it as optional. The design pins `db3b4b9` [read].
- The agent-server's events search, backend status and `start`, and agent profiles, as design §9 lists them; S2's
  manifest model; D1's harness for E8 [read; unchanged].

### 8.2 What relies on D3: D4 (`v1-custom-tools`)

[read: `v1-custom-tools` at `01abb88`, D4's merge of `a7a50db`, now on `origin`] D4's Tools tab and components
import from D3:
`CodeField`, `ConfirmRow`, `Banner` (`components/fields.tsx`), `NamespaceChecklist`, `SafetyNotice`; `loadDraft`,
`saveDraft`, `clearDraft` (`drafts.ts`); `OnBackendLost`, `attempt`, `useLoaded` and **`resolved`**, which its Tools
tab calls as `resolved(getEffective)`; `api.ts` (`getEffective`, `getNamespaces`, `getTools`, `deleteTool`, and its
own additions); `stringifyYaml` (`yaml.ts`); `TabProps`; and it extends `FrameParams`, `page/context.ts` and
`page/mount.ts`. What the refactor changed under it: #1 holds for its Tools tab (a 500 from `/effective` reaches the
footer); `getNamespace`, `getDecomposition`, `getTool`, `toolVersions`, `YamlSyntaxError`, `applyTheme`, `POLL_MS`
and `APP_NAME` are gone, and at D4's pre-merge head `e866563` only D3's own files named them [run: `git grep -w`]. A
trial merge of `a7a50db` into `e866563` conflicts in six files: `ui/api.ts`, `ui/tabs/tools.tsx`,
`tests/api.test.ts`, the two built bundles and `library/api.py` [run]. I did not build D4.

### 8.3 D5

Stages `canvas-extension.json`, `dist/index.js` and `panel.svg`, not `ui/` or `__init__.py`; the backend's argv is
unchanged; D3's `SAFETY` has never been compared with D5's (the one browser skip) [read].

---

## 9 · What I could not verify

1. **Everything through Canvas and C2.** The page bundle has run only in a fake host; C2's head moved to `f4c7ae5`
   and I did not check its CI. Not tested here: the App ingress and the bridge (relative URLs under
   `/app-backends/dr-library/`, the `Host` the backend sees, `Origin` on writes, `Content-Type` passing through, no
   redirects); the session cookie and its renewal; `onError` from a real `mountFrame`; Electron's Chromium.
2. **The agent-server's answers as the page reads them**: status, `start`, the events search and the profile are
   faked; B27's kind is pinned against a fake modelled on the real filter (design B27), not the filter.
3. **What the bridge does with a backend 500** (#1): whether a 500 from D2 reaches the frame as a non-JSON 500, so
   that the footer, not a tab message, is what a user sees; only the injected 500 of §2.1 #1 ran.
4. **That `record.data` and a YAML 1.1 parse of `record.yaml` agree for every canonical record** (#2): one date ran;
   the rest is read from D2's writer.
5. **401 and `SESSION_ENDED`**, and **Restart end to end** (the frame posting `reload` and the page remounting have
   not run together, and no test restarts a real backend through `start`).
6. **D5's `SAFETY` equality**; **layout and accessibility** beyond B30's measured gaps and `--oh-surface`.
7. **The wheel's contents at `a7a50db`** (no `uv build` this revision), and **D4's build** after its merge.
8. Design §6's and §9's agent-server and Canvas line references, except the C2 points of §8.1.

If this document will not get shorter, the part that resists is §2.1 #1: one refactor commit moved a failure from a
tab sentence to the footer, and saying what a user then sees takes the tab-by-tab detail.
