# D3 · Decompositions panel — design

**TASK-8** · System Designer · task branch `v1-decompositions-panel` in
[deep-reasoning](https://github.com/michaeltheologitis/deep-reasoning) (v1 was written on `design/d3`; the task branch
has carried this file since `923e802`) · against the approved spec
[TASK-1](https://app.notion.com/p/3ed62fb22237814ab425c81b3844f012) (D3 in full; D2, D4, D5 and C2 where they meet the
panel; §4's E8 note, E11 and the testing layers; the dated notes at its end).
**Pinned against:** C2's design at deep-reasoning `72aa49f` (§6 and §7 are D3's host contract; PR 3, App backend frames,
approved by Michael on 2026-10-03) and C2's code on the Canvas fork's `feat/agent-surfaces` at `db3b4b9` (read for
§8.1; v2) · D2 as built on `v1-library-store` at `5158693` (its design `555472b`, §6, is the data contract; v2: D2 at
`90044f0`, under D3's code) · D5's design `8086afb` (§4.6, §4.9, §8.3) · S2's design `9e32261` (§5, the manifest) ·
D1's design `f281109` (§2, §4.6) and its harness on `v1-dr-acp` at `21c2c7a` · SDK fork `deep-reasoning` at `91430aa`
(the App backend manager and bridge; every agent-server `file:line` below) · Canvas fork `deep-reasoning` at `02b7ac7`
· deep_reasoner_beta `d7334ae`.

**Matches the build at `d4e9cd3`** (v4): D3's code (`3ce186a` … `5effe26`, then fixes after the as-built checks:
`450bed1`, `aaa97ef`, `4123ec7`, `2af80ef`, and `c5964ff`, `02b93dc`, `54625ab`, `d4e9cd3`) on D2 as built
(`90044f0`). Commits after it on this branch change only `docs/` and `as_built/`.

## Gate B: what to read

**About 70 minutes, in this order.** The codebase stays closed. The Gate B set is this doc, D3's as-built document
(`as_built/d3-decompositions-panel.md`, the Cartographer's) and the CI run below. Everything after §3 is kept whole as
the reference D4 and D5 build against (Michael: don't force compression); Gate B does not need it.

| # | Read | What it gives you | Minutes |
|---|---|---|---|
| 1 | This section and the v4, v3 and v2 revision lines below it | where the proof is, and which sentences of v1 changed | 8 |
| 2 | §1 | what D3 is (a page bundle in Canvas that mounts a frame the Library's backend serves), and decisions A–M | 10 |
| 3 | §2 | the panel tab by tab, as the user meets it; v2's to v4's changes are marked | 15 |
| 4 | §3.1 | where the design departs from the spec (v1's list; not yet ruled on) | 5 |
| 5 | §3.2 | what the build changed, each with its reason and the test that pins it | 15 |
| 6 | Open the run below | that both jobs are green at `d4e9cd3` | 2 |
| 7 | `as_built/d3-decompositions-panel.md` | what exists, and its divergences, read from the code | 15 |

**Two things to rule on.**

1. **§3.1, D3's departures from the spec.** No ruling covers them yet: the spec's dated notes accept D2's departures
   (2026-10-02) and C2's third pull request, App backend frames, on which D3's frame rests (2026-10-03), but not D3's
   list. The visible ones: the UI is a frame the Library's backend serves (item 1); Preact and plain text areas instead
   of React and CodeMirror (item 2); the built App committed and shipped in the wheel (item 3); Python where the spec
   said "No Python" (item 4: about 75 lines as built); adding and deleting namespaces, deleting decompositions, the run
   settings and the problems banner (item 5); two success lines (item 7); a second safety sentence (item 10).
2. **Size.** The spec estimated D3 at ≈1.5k lines of TypeScript and ≈5 h at Gate C; v1 at ≈2.6k of code and ≈1.4k of
   tests (§10). The build is **4,623 lines of code and 3,308 of tests** at `d4e9cd3` (4,285 and 2,968 non-blank; the
   committed built files, generated, are not counted), about 26 h at Gate C at the workspace's rate. Two files carry
   most of the growth: `tabs/namespaces.tsx`, 902 lines (v1: 380), and `components/editor.tsx`, 869 (v1: 250 with the
   cards); `styles.css`, 368, was in no line of v1's estimate. The build recorded no reason for the growth; the
   estimate was this design's. The breakdown is §3.2 B16 and §10. The Scout and the Refactorer, after Gate B, are
   where it shrinks.

**The evidence.** One CI run, at `d4e9cd3`, the branch's last commit that touches code.

- **CI**, [run 37144441476](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37144441476), on push,
  both jobs green:
  - **`canvas-app`** (D3's job, §7.6), 3 min 22 s: `tsc`, Prettier, vitest **151 passed, 1 skipped** (the skip is the
    guard that fails only when deep_reasoner_beta's configs are missing; they were checked out at `d7334ae`, so the
    cards round trip ran over all of them; without them, 150 passed and 2 skipped), `npm run build`, the
    **committed-build check** (a fresh build leaves `src/deep_reasoning/canvas_app` unchanged), then the browser tier
    against a real `dr-library serve`: **55 passed, 1 skipped** in 2 min 21 s, E8 among them. The skip is
    `test_the_notice_is_d5s_sentence_with_the_cap`, which waits for D5's `dr_app` (§3.2 B19).
  - **`test`** (D1's job): ruff and the deterministic suite, **531 passed** (60 live and browser tests deselected) in
    6 min 18 s; `tests/library/test_ui.py`'s 16 cases among them.
  - Earlier evidence, superseded by this run: v3's
    [run 37139529187](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37139529187) at `2af80ef`
    (150 + 1 vitest, 50 + 1 browser, 531 passed) and v2's
    [run 37090168700](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37090168700) at `5effe26`
    (148 + 1, 47 + 1, 531).
- **No live tier** (§7.1): no D3 test calls a model, and the one real service the panel talks to, D2's backend, runs
  for real in every browser test. The real desktop app is D5's E12 (layer 4). Gate B's evidence for D3 is the browser
  tier and E8, green in CI (spec §4 layer 5).

**Which tests carry which property.** Each test's name states the property it pins. Python tests are under
`tests/canvas_app/` unless named otherwise; vitest cases are `canvas-app/tests/<file> › <describe> › <case>`; `[…]` is
a parametrization.

| Property | Tests |
|---|---|
| **E8** (spec §4: "a decomposition saved in Create decomposition is used by the next conversation in that namespace, as our run log records"). Saved in Create decomposition in Chromium, against a real `dr-library serve`, while conversation A is open in `dr-acp` (D1's harness, stdio, D1's `FakeOpenAI`): A's next turn sends the model nothing of it; conversation B's menu offers `/rank-by-prerequisites` with its use-when line; B's `run.start` records namespace `router` and the decomposition at version 1; B's first model request holds its task | `test_e8_next_conversation.py::test_a_decomposition_saved_in_create_is_used_by_the_next_conversation_in_its_namespace` |
| **E11, the panel's part** ("the decompositions panel mounts with the right conversation"): each mount carries its own conversation's namespace and whether it started, through the built bundle as Canvas loads it, and in a unit test | `test_page_bundle.py::test_the_frame_opens_with_the_conversations_namespace` (c2 → `course_advisor` picked; then c1 → `router`, `started=1`, `cap=7` in the frame's URL); `mount.test.ts › mountTab › mounts each conversation with its own namespace` |
| **The frame protocol** (§4.3): the URL round-trips and falls back safely; the page accepts only the two messages, only from its own frame's window; `select-tab` moves Canvas's tab and the next mount takes the focus; `reload` and `not-ready` remount; Canvas's theme reaches the frame | `protocol.test.ts` (22 cases: `the frame's URL`, `isFrameMessage`); `mount.test.ts › mountTab ›` `selects the tab a frame asks for, and that tab's next mount takes the focus`, `ignores a message from any window but its frame's`, `remounts on reload, checking the backend again`, `remounts once when the frame's backend was not ready`, `leaves nothing behind when disposed during the backend check`; `test_page_bundle.py::test_the_built_bundle_activates_and_registers_four_tabs`, `::test_show_in_decompositions_selects_the_tab_and_opens_the_new_entry`, `::test_the_frame_takes_canvas_theme`; `test_backend_loss.py::test_a_backend_that_stops_answering_offers_restart` (the frame posts `reload` to a parent page on another site) |
| **The backend before every mount** (§2.1, decision F): ready, start of the approved revision only, never `prepare`, the 45 s limit, a start that gets no answer read from the status, an abort | `backend.test.ts › ensureBackend ›` (15 cases, among them `gives up on a backend still starting after the timeout`; v3, `polls the status when start gets no answer, [until it is ready, and says why it did not start]`; v4, `gives a backend still starting after start timed out a fresh 45 s`); `mount.test.ts › mountTab › says the backend is not approved, and Try again checks again`, `says when Canvas cannot show an App's frames` |
| **Writes and conflicts** (§5.2, §5.3, decision H): every body is exactly D2's fields, `use_when` and `hint` always sent; a new decomposition is version 1 in the picked namespace; an edit is the next version; Attached to is the exact set; a stale save offers Reload or Save over it; an existing name offers Save mine as v*n* keeping its namespaces; an unchanged imported decomposition makes no version; a namespace edit changes one key of the namespace's own YAML and keeps the rest | `save.test.ts`; `api.test.ts › the requests`; `test_create.py::test_saving_stores_version_1_in_the_picked_namespace`, `::test_an_existing_name_offers_to_save_the_next_version_keeping_its_namespaces`, `::test_use_when_and_hint_survive_a_save_that_did_not_touch_them`, `::test_an_imported_decomposition_saved_unchanged_makes_no_new_version`, `::test_an_example_without_final_answer_asks_before_saving`; `test_browse.py::test_saving_an_opened_decomposition_makes_its_next_version`, `::test_attached_to_is_the_exact_set_after_a_save`, `::test_a_stale_save_offers_reload_or_save_over`, `::test_deleting_a_decomposition_detaches_it_everywhere`; `test_namespaces.py::test_override_sets_a_field_here_and_reset_removes_it`, `::test_keys_the_panel_does_not_show_survive_an_override`, `::test_yaml_values_mean_what_dr_reads`, `::test_attach_and_detach_change_only_this_namespaces_list` |
| **Create decomposition's draft and errors** (§2.3): the draft survives a reload of the frame, the namespace picked included; a card-mode save without a name asks for one and writes nothing; D2's errors land on the card they name, and an error that names no card sits above the cards; Rename in YAML mode focuses the YAML, which holds the name | `test_create.py::test_saving_without_a_name_in_card_mode_asks_for_one_and_writes_nothing` (v4), `::test_a_draft_survives_reloading_the_frame`, `::test_a_draft_keeps_the_namespace_picked_over_the_preselected_one` (v3), `::test_validation_errors_show_on_the_card_they_name`, `::test_an_error_that_names_no_card_shows_above_the_cards` (v3), `::test_rename_in_yaml_mode_focuses_the_yaml_which_holds_the_name` (v3) |
| **Namespaces: adding, deleting, and the selection** (§2.4): Add namespace is prefilled `<selected>.`, and empty under `root` and Run settings; D2's refusals come in its words; a write answered after the user selected another node leaves that selection | `test_namespaces.py::test_adding_and_deleting_a_namespace`, `::test_add_namespace_is_not_prefilled_under_root_or_run_settings[root, run-settings]` (v4), `::test_a_write_answered_after_another_node_is_selected_keeps_that_selection[add, delete]` (v4) |
| **Lossless cards** (§5.1, decision J): one card per message; the round trip is the identity on a table, on 2,000 generated conversations and on every decomposition in deep_reasoner_beta's configs | `cards.test.ts › messages ↔ cards ›` (the table; `round trip is identity over generated messages`; `round trip is identity over every decomposition in deep_reasoner_beta's configs`) |
| **A Library D2 cannot resolve** (§3.2 B1): both tabs say why in D2's words, Decompositions falls back to attachments, and neither reports the backend lost | `test_browse.py::test_the_tab_falls_back_to_attachments_when_inheritance_cannot_be_resolved`; `test_namespaces.py::test_a_namespace_whose_inheritance_cannot_be_resolved_says_why` |
| **The safety notice** (D5 §2.3): on first open until understood, permanent in Tools, with the cap; the sentence without the key proxy | `test_notice.py::test_the_safety_notice_shows_until_understood`, `::test_without_the_key_proxy_the_notice_says_nothing_caps_spending`, `::test_the_notice_is_d5s_sentence_with_the_cap` (skipped until D5); `test_tools_tab.py::test_the_tools_tab_always_shows_the_safety_notice_with_the_cap[5, 12]` |
| **The committed build** (decision D): CI fails when a fresh build differs from what is committed; the committed build is complete and served | the `canvas-app` job's step "The committed build is what a fresh build gives" (§7.6); `tests/library/test_ui.py::test_the_committed_build_is_complete`, `::test_ui_serves_the_index_and_the_built_assets`, `::test_the_manifest_is_valid_and_its_version_is_the_packages` |
| **Serving `/ui/`** (§4.5): only built files, behind D2's guard, with the CSP and `no-cache` | `tests/library/test_ui.py::test_a_file_not_in_the_build_is_404`, `::test_no_path_outside_the_assets_is_served[…]`, `::test_every_answer_carries_the_csp_and_no_cache[…]`, `::test_an_unbuilt_ui_is_503_with_its_sentence`, `::test_the_ui_answers_only_its_own_host` |

§7.2–§7.5 list every test file.

**Revisions** (newest first; each line says which sentences to stop trusting):
- 2026-10-03 · v4 · brought in line with the build at `d4e9cd3`: four commits after v3 (`c5964ff`, `02b93dc`,
  `54625ab`, `d4e9cd3`). Stop trusting: B20's, §2.1's, §4.2's and §5.4's "within the same 45 s" and "a backend still
  `starting` ends in `STILL_STARTING` at once" (the 45 s now restart when a start gets no answer, `c5964ff`; §11 item
  6 gains a note); B24's and B25's "Not pinned" (both are pinned now); §7.2's and §7.3's counts; the Gate B evidence (now
  CI at `d4e9cd3`) and size; §10's table; B15's sizes. Added without changing earlier sentences: §3.2 B26 (a
  namespace write answered after another node was selected keeps that selection, `d4e9cd3`) and §2.4's sentence on
  the selection after Add namespace and Delete namespace; §11 items 15 and 16 (two known behaviours left as they are);
  the property table's Namespaces row and its new cases. Nothing else of v3 changes.
- 2026-10-03 · v3 · brought in line with the build at `2af80ef`: four fixes an Implementer made after the as-built
  check (`450bed1`, `aaa97ef`, `4123ec7`, `2af80ef`), and two rulings of the Conductor's recorded as this design's
  reading. Stop trusting: §2.1's `stopped or unhealthy` row, §4.2's and §5.4's "a request that fails is
  `BACKEND_FAILED`", and B6's `errorDetail` bullet (a start that gets no answer now reads the status, B20); §2.3's
  draft (it keeps the namespace picked, B21), where D2's errors that name no card sit (B22), and what Rename focuses in
  YAML mode (B23); §7.2's and §7.3's counts; the Gate B evidence (now CI at `2af80ef`) and size (B16's v3 note); §10's
  totals; §11 item 6 (built). Added without changing earlier sentences: §3.2 B20–B25, of which B24 (YAML mode has no
  name field, and `NAME_REQUIRED` is a card-mode check) and B25 (Add namespace is not prefilled under `root` or Run
  settings) are the rulings, and §2.4's sentence for B25; the property table's row for Create decomposition's draft and
  errors, and the backend row's new case; v3 notes on B15's sizes, §7.6's time and §10's table. Nothing else of v2 changes.
- 2026-10-03 · v2 · brought in line with the build at `5effe26`, after Proof Green (CI run 37090168700). Stop
  trusting: §2.1's `starting` row (the 45 s limit has a sentence, B4); §2.2's fallback and what triggers it (B1),
  "Attached to"'s inherited entries (B2) and Save on an opened decomposition (B3); §2.6's "a request that fails without
  a D2 body is the backend being unreachable" (B1); §4.1's file tree (B7, B10); §4.2 step 6's `select-tab` (only in a
  panel, B6); §4.3's `parent` and `cap` (B6); §4.4's components (B7); §4.5's 503 body (B6); §4.6's manifest `version`
  (B5), its sizes (B15) and the CI check (B13); §4.7's page texts (B4) and labels (B8); §5.2's edit path (B3); §5.4's
  limit (B4); §7.3's fixtures (B10, B11) and test list (B1); §7.4's harness note (B12); §7.6 (B13); §8.3's file names
  (B7, B10); §8.4 item 6's `dr-create-*` (B9); §10 and §3.1 item 11's size (B16); Appendix A.3's component props
  (B7, B8); A.4's `browser` scope and `open_ui`'s type (B11); §11 items 4, 8 and 9. Added without changing earlier
  sentences: this Gate B section; §3.2; §2.4's sentence for a namespace D2 cannot resolve (B1); §4.4's `load.ts` (B7);
  §7.2's counts; Appendix A's new names (B8) and A.5's additional test ids (B9); §8.1's answer from C2's code; §8.2's
  open item for D2 (a 422 for a stale head); §9's D2-2; §11 items 10–14. §3.1 (v1's §3) keeps every item as written,
  with marked v2 notes on items 4 and 11. The contracts of §8.3 (D4) and §8.4 (D5) are unchanged. Every change is
  listed, with its reason, in §3.2.
- 2026-10-03 · v1 · first full-depth version. Folded in before it: Michael's yes to C2's PR 3; D5's four proposals to D3
  (§8.3 of D5, settled here in §8.4); C3's approved launcher default for the App ingress
  (`http://127.0.0.1:<agent-server port>`, Canvas's window on `http://localhost:8000`); D2's API as built (403 for a
  foreign `Host`, 415 for a non-JSON `PUT` or `POST`, 400 for an unknown body field, and a `PUT` that omits `use_when`
  or `hint` erases it).

**Where this file lives, and why nothing trips over it.** `docs/design/d3-decompositions-panel.md`, on
`v1-decompositions-panel` (v1 lived on `design/d3`, which holds only documents). On this branch, which carries D1's
`pyproject.toml`, pytest collects `tests/` only, the wheel is built from `src/deep_reasoning`, the sdist excludes
`docs/`, and ruff excludes `docs` (D1 §8.5). D3's TypeScript tools (`tsc`, `vitest`, `prettier`) run inside
`canvas-app/` only (§4.1), so they never see `docs/`. The PR split leaves this file behind.

**Reading guide.** Gate B: the section above. D4's designer: §8.3, D4's contract, then §2.5, §4.4 and §3.2 B7–B9 (the
names, files and test ids as built). D5's designer: §8.4 (D5's proposals, settled, and what D5 must do), §4.6 and §3.2
B19. C2's and D2's: §8.1 and §8.2. The Implementer and the Cartographer read everything; Appendix A is the signature
reference, §4.7 every user-visible sentence, §7 the tests.

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
in a browser (the probe replicated it; E12 uses the real one). (v2: the browser tests run on Playwright 1.56.0's
Chromium build 1194, not on the probe's Chromium 153, §3.2 B14.)

---

## 1 · What D3 is

The Library (D2) holds the user's decompositions, namespaces, tools and run settings. D3 is the part of the app where
the user sees and changes them: a Canvas App, `dr-library`, whose header panel (C2) puts **Show Decompositions** at the
top right of a conversation, after Show overview and Show panel, and opens a panel the way Show panel opens the drawer,
with four tabs: **Decompositions** (by namespace), **Create decomposition**, **Namespaces** and **Tools**.

The App has two halves, because of how the agent-server lets an App reach its backend (C2 §6.1, verified above): only
from a separate browser origin, inside a frame, with a five-minute cookie session that only Canvas can mint.

- **The page bundle** (`dist/index.js`, about 300 lines; v2: 448 of source and the 165 of the shared protocol, 6.96 kB
  built) runs in Canvas's own page. It registers the four tabs, and for
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
| `starting` | polls the status every 500 ms, up to 45 s, saying "Starting the Library's backend…"; still `starting` after 45 s → `BACKEND_FAILED` with the detail `STILL_STARTING` ("The Library's backend did not start: it was still starting after 45 seconds.") and **Try again** (v2, B4) |
| `stopped` or `unhealthy`, and `prepared_revision` = `revision` | `POST …/backend/start {revision}` (it returns once healthy or failed), saying "Starting the Library's backend…"; `ready` → mounts the frame; otherwise `BACKEND_FAILED` with the agent-server's `detail` and **Try again**. (v3, B20: a start that gets no answer, the client's timeout or a network failure, reads the status and goes on by this table: `ready` mounts, `starting` is polled within a fresh 45 s from then (v4), anything else is `BACKEND_FAILED` with the status's `detail`. A start the agent-server answered with an error is `BACKEND_FAILED` in its words.) |
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
backend if it died. (v2, B6: the footer goes away by itself when `/health` answers again. On the standalone page,
with no parent to post to, the button reloads the page. A 500 from D2's two effective routes is not this case: it is a
Library D2 cannot resolve, §2.2, B1.)

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
- **If D2 cannot resolve inheritance** (a head that no longer validates makes D2's resolution fail), the tab falls back
  to attachments only, no inheritance: each namespace's group lists the namespace's own list from `GET /namespaces`
  (v2, B6; v1 said `GET /decompositions` grouped by each record's `namespaces`, which D2 derives from the same lists).
  The banner is `EFFECTIVE_FAILED` with D2's own sentence for that head, and the problems banner lists it too. **As
  built, D2 answers that failure with a bare 500** (Starlette's `text/plain`), not a JSON refusal, so the frame treats a
  500 from `/effective` as this case and takes the sentence from `GET /problems`; it never shows the backend-loss
  footer for it (v2, B1).
- **Opening one** (a click, or `focus=<slug>` in the URL) shows the decomposition editor of §2.3 for that record:
  the name read-only (a new name is a new decomposition, D2 §4.5), use-when, hint, **Attached to**, the cards, **View
  YAML**, **Save** and **Delete**, and **← Decompositions** back to the list.
  - **Attached to** is a checklist of every namespace; checked = the record's `namespaces`. A namespace that has a
    checked ancestor (root, then each dotted prefix) is shown checked and fixed, "also used in <namespace>
    (inherited)", and this follows the boxes as the user clicks, before any save, not the saved `/effective` (v2, B2).
    So moving a decomposition from a parent to a child is one save: uncheck the parent, check the child, Save.
  - **Save** validates first, as Create decomposition does: D2's errors on their cards (those that name no card between
    Attached to and the cards, v3, B22), and D2's warnings ask **Save anyway** / **Cancel** (v2, B3). Then `PUT /decompositions/<slug>` with `base_version` = the version opened,
    `namespaces` = the checked set (D2's exact-set rule), `use_when` and `hint` as shown. Success: `SAVED_EDIT`. A save
    that changes only Attached to makes no new version of the decomposition (D2 versions the namespaces' lists, D2
    decision B), so `SAVED_EDIT` names the version it had.
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
  start in (`/health`'s `default_namespace`). (v3, B21: a namespace the user picked is part of the draft and wins over
  the preselection while the Library still has it.)
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
  in D2's (deep_reasoner's) words. (v3, B22: "above the cards" is one error block between the namespace picker, or
  Attached to, and the cards; in YAML mode, above the YAML field. A refused save's message shows there too.)
- **Save** (§5.2): a name is required (`NAME_REQUIRED`; in YAML mode the name is the YAML's own, and D2's validation
  speaks for it; YAML mode has no name field, v3, B24); validate; D2's warnings (today one: `NO_FINAL_ANSWER`) ask
  **Save anyway** / **Cancel**; then `PUT /decompositions/<slug>` with `namespaces: [picked]`, `use_when`, `hint`,
  `base_version: 0`.
  - **201:** the success line (below), the draft cleared, the form reset to a new decomposition; **Show in
    Decompositions** posts `select-tab` with `focus=<slug>`.
  - **409 `conflict` with a head** (the name exists): `EXISTS` — "'catalog lookup' already exists (v2, in router)." —
    with **Save mine as v3** (re-sends with `base_version` = the head's version and `namespaces` = the head's namespaces
    plus the picked one, D2 §6.4) and **Rename** (focuses the name; v3, B23: in YAML mode, which has no name field,
    it focuses the YAML, which holds the name, and stays in YAML mode).
  - **422:** D2's message and field errors, on their cards (v3, B22: the message in the error block above the cards).
- **The success line** says what changed and what did not. When the page reported the conversation as started (its
  `namespace` option has a single value, which is how `dr-acp` fixes it after the first message, D1 §2 step 4), it is
  the spec's sentence, `SAVED_STARTED`. Otherwise (a conversation not started yet, or another agent) it is `SAVED`, which
  is true either way: "New conversations in course_advisor use it and offer it as /rank-by-prerequisites; a conversation
  that has already started keeps the run it began with."
- **The draft** (every field, the cards or the YAML, and the mode) is saved on each change under
  `dr-library.draft.create`, restored on the next mount, and cleared by a successful save or **Discard draft**. (v3,
  B21: the draft also keeps the namespace picked. Picking is a change to the draft, so it clears the result line and
  shows **Discard draft**; after a save or **Discard draft** the picker returns to the preselection.)

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
  conversations start in. **Add namespace** takes a name, prefilled with the selected namespace's name and a dot (v3,
  B25: empty when `root` or Run settings is selected, since `root`'s children are top-level names and Run settings is
  not a namespace), and sends `PUT /namespaces/<name> {yaml: "{\"name\": …}", base_version: 0}`; D2 refuses a bad name or a missing parent in
  its own words. **Delete namespace** asks inline, then `DELETE …?base_version=`; D2's refusals (root, the default, a
  parent) are shown as they come. When D2 answers, the panel selects the new namespace (Add) or the deleted one's parent
  (Delete), unless the user selected another node since the write began, in which case that selection stays (v4, B26).
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
- **If D2 cannot resolve this namespace's inheritance** (v2, B1): no field is shown; in their place, D2's own sentence
  for the head that no longer validates (from `GET /problems`, as in §2.2), and never the backend-loss footer. **Start
  new conversations here** and **Delete namespace** stay.
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
- **Polling** (decision K): while `document.visibilityState` is `visible`, `GET /health` every 3 s, and once when the
  frame becomes visible again (v2, B6); when `rev` changes, the tab refetches its data. A tab is first drawn after the
  first `/health` answer. An editor's draft is never overwritten by a refetch; its `base_version` makes a conflicting
  save a 409.
- **Errors** are always the backend's own sentence (D2's `message`, deep_reasoner's field messages), never a generic
  one. A request that fails without a D2 body is the backend being unreachable (§2.1), with one exception (v2, B1): a
  500 from `/effective` or `/namespaces/<name>/effective` is D2 failing to resolve a stale head, and its sentence comes
  from `GET /problems`.
- **Theme.** The frame takes Canvas's colours, radius, font and colour scheme from the `theme` parameter (§4.3), with
  Canvas's dark defaults when it is absent (the standalone page).
- **Accessibility.** Every input has a visible label; the save result is announced (`aria-live="polite"`); errors are
  linked to their fields (`aria-describedby`); every action is a button with text; the cards are an ordered list.

---

## 3 · Departures from the spec, and what the build changed

§3.1 is where this design departs from the approved spec (v1, unchanged in v2 but for two marked notes). §3.2 is what
the build changed in this design (v2). None is a re-scope.

### 3.1 Where this design departs from, or adds to, the approved spec

Each is a refinement inside D3's scope unless it says otherwise; if the Conductor reads any as a change of what was
approved, it goes back to Michael. **Not yet ruled on** (v2): the spec's dated notes accept C2's PR 3 (2026-10-03), on
which item 1 rests, but no list of D3's; Michael rules on it at Gate B.

1. **The UI runs in a frame served by the backend; the App's pages only mount it** (decision A). The spec draws D3 as an
   App whose tabs are App pages over D2's bridged API; C2 found that a page cannot write through the bridge, and PR 3
   (approved 2026-10-03) is how D3 does.
2. **Preact, textareas and a YAML 1.1 parser instead of the spec's candidate "React with CodeMirror 6"** (decision C):
   the built files are committed (item 3). CodeMirror can come with D4's Python editor, behind `CodeField`.
3. **The built App is committed and ships in the wheel** (decision D; D5's proposal). The spec left packaging to the
   System Designer.
4. **About 40 lines of Python** (`library/ui.py`, one line in D2's `api.py`, two sentences in D2's `texts.py`). The
   spec's D3 cost says "No Python"; serving the UI from the backend needs a route. *(v2: about 75 as built:
   `library/ui.py` 59, `canvas_app/__init__.py` 5, and 10 lines in D2's `api.py` and `texts.py`; nothing else.)*
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
    *(v2: v1's own §10 already said ≈2.6k and ≈1.4k; built at 4.6k and 3.1k, about 26 h, §3.2 B16; v3: 4.6k and 3.2k at `2af80ef`; v4: 4.6k and 3.3k at `d4e9cd3`.)*

### 3.2 Changed by the build (v2, v3)

Each was checked against the code at `5effe26` and folded into the section named. B1–B6 change behaviour v1 specified
or decide what it left open; B7–B9 are names, files and props, none of which changes §8.3's or §8.4's contract;
B10–B15 are the tests, the wiring and the build; B16 is the size; B17–B19 are findings, each an open item in §11.
B20–B25 are v3, checked against the code at `2af80ef`: four fixes made after the as-built check (B20–B23) and two
rulings of the Conductor's (B24, B25). Where the build recorded no reason, the reason given is marked as this design's
reading.

**Behaviour**

- **B1. A Library D2 cannot resolve: D2's bare 500, read as the stale head, in D2's words** (§2.2, §2.4, §2.6, §4.4).
  When a head no longer validates under the installed deep_reasoner, D2's resolution raises, and both `GET /effective`
  and `GET /namespaces/<name>/effective` answer a bare **500** (Starlette's `text/plain` "Internal Server Error"); v1
  assumed a D2 error body. `load.ts`'s `resolved()`, which wraps those two calls and no other, treats a 500 as that
  failure and takes the reason from `GET /problems` (D2's sentences, joined; with none listed, the `BACKEND_LOST`
  sentence). Decompositions shows it in `EFFECTIVE_FAILED` and falls back to attachments (§2.2); Namespaces, new in v2,
  shows it where the fields would be (§2.4). Neither shows the backend-loss footer; any other 500 still does. *Why
  (commit `5effe26`):* "both tabs now show D2's own sentence for that head, from /problems, instead of the backend-loss
  footer." Checked for this revision against a scratch Library at `5effe26` with a stale `router.archive` head: both
  routes answer 500 `text/plain`, `/problems` answers 200 with the sentence. **Open for D2** (§8.2, §11 item 10): answer
  422 with that sentence, and the panel can drop the 500 rule. *Pinned by:*
  `test_browse.py::test_the_tab_falls_back_to_attachments_when_inheritance_cannot_be_resolved`,
  `test_namespaces.py::test_a_namespace_whose_inheritance_cannot_be_resolved_says_why` (each asserts D2's sentence and
  no footer).
- **B2. "Attached to" works out inheritance from the checked boxes, live** (§2.2, Appendix A.3). v1 listed the
  namespaces that inherit an opened decomposition as "also used in … (inherited)" without saying from what. Built:
  every namespace with a checked ancestor (`tree.ts`'s `ancestors`: `root`, then each dotted prefix, as deep_reasoner
  walks the chain) is shown checked and fixed with that note, recomputed on every click; the saved `/effective` is not
  read. `DecompositionEditorProps` gains `onDeleted?` (Decompositions goes back to its list) and `onBackendLost`
  (every tab's channel to the footer, B7). The Implementer reported that the editor "loses `inherited`"; v1's A.3 never
  gave `DecompositionEditorProps` one, and `NamespaceChecklistProps.inherited` stays and carries the notes. *Why
  (commit `b42b3b5`):* "Attached to treats a namespace as inheriting while an ancestor is checked, so moving a
  decomposition from a parent to a child is one save." *Pinned by:*
  `test_browse.py::test_attached_to_is_the_exact_set_after_a_save` (`root` checked, so `router` is fixed with "also
  used in router (inherited)"; uncheck `root`, check `course_advisor`, save: `namespaces == ["course_advisor"]` and
  `root`'s list is empty).
- **B3. Saving an opened decomposition validates first and asks on warnings** (§2.2, §5.2). v1's edit path went
  straight to the `PUT`. Built: one `save()` serves both editors: the name (card mode), `POST /validate`, D2's errors
  on their cards or D2's warnings with **Save anyway** / **Cancel**, then the `PUT` (`updateBody` for an opened one,
  `createBody` in Create decomposition). *Why (this design's reading; the build recorded none):* D2's one warning,
  `NO_FINAL_ANSWER`, is as true of an edited example as of a new one, and one save path keeps the two editors from
  drifting apart. **Not pinned** on the edit path; on the create path,
  `test_create.py::test_an_example_without_final_answer_asks_before_saving`.
- **B4. A sentence for a backend still starting after 45 s** (§2.1, §4.7, Appendix A.2). v1 polled a `starting`
  backend for up to 45 s and gave the limit no sentence. Built: `BACKEND_FAILED` with the page's new `STILL_STARTING`
  as its detail ("The Library's backend did not start: it was still starting after 45 seconds."), with **Try again**.
  *Why (this design's reading):* when the page itself gives up, the agent-server has no `detail` to show. *Pinned by:*
  `backend.test.ts › ensureBackend › gives up on a backend still starting after the timeout`.
- **B5. The manifest's `version` is `"0.1.0"`** (§4.6). v1's JSON block said `"1.0.0"`; its next sentence said
  `version` is deep-reasoning's package version, pinned by a test. The build follows the sentence (`pyproject.toml`:
  `0.1.0`). *Why:* v1's own rule; the JSON was the slip. A version bump of deep-reasoning moves the manifest with it.
  *Pinned by:* `tests/library/test_ui.py::test_the_manifest_is_valid_and_its_version_is_the_packages`
  (`metadata.version("deep-reasoning")`).
- **B6. Smaller behaviour, each inside v1's intent** (§2.1, §2.2, §2.6, §4.2, §4.3, §4.5). *Why (this design's
  reading; the build recorded none):* each fills a detail v1 left open.
  - The backend-loss footer clears itself when `/health` answers again. On the standalone page its button reloads the
    page, as there is no parent to post `reload` to.
  - `/health` is also polled when the frame becomes visible again; a tab is first drawn after the first answer (it
    needs `health`).
  - The page acts on `select-tab` only when mounted in a panel (`surface.kind === "conversation-panel"`, the only
    surface with `selectTab`); `reload` acts on any surface.
  - `readFrameParams` also refuses a `cap` that is not `off` or a decimal (it becomes `5`) and a `parent` that is not
    exactly an `http(s)` origin (it becomes none: the frame posts nothing and shows its own tab row).
  - Decompositions' fallback lists each namespace's own list from `GET /namespaces` (B1; v1 said each record's
    `namespaces`, which D2 derives from those lists).
  - `/ui/`'s 503 carries the code `not_built` beside `UI_NOT_BUILT`, in D2's error shape.
  - `ensureBackend` takes the agent-server's own words from a failed request for `BACKEND_FAILED` (`errorDetail`: an
    `HttpError`'s `detail`, else the error's message). (v3, B20: except a `start` that gets no answer, which now reads
    the status instead.)

**Names, files and props (§8.3's and §8.4's contracts unchanged)**

- **B7. Files** (§4.1, §4.4). The components are four files, by role: `components/fields.tsx` (`CodeField`,
  `ValueEditor`, `FieldErrors`, `ConfirmRow`, `Banner`), `components/pickers.tsx` (`NamespacePicker`,
  `NamespaceChecklist`), `components/notices.tsx` (`SafetyNotice`, `ProblemsBanner`) and `components/editor.tsx`
  (`DecompositionEditor`, `CardList`). `TabProps` lives in `tabs/props.ts`. A new module, `ui/load.ts`, is how a tab
  reads and writes D2: `attempt` (D2's refusal back to the tab, `BackendUnavailable` to the footer), `useLoaded` (a load
  per `rev`; a late answer to an older load is dropped) and `resolved` (B1). The vitest fakes of C2's host and the
  agent-server are `canvas-app/tests/fakes.ts`. Prettier runs at its defaults (`.prettierrc.json` is `{}`;
  `.prettierignore` skips `node_modules` and the lockfile). *Why (this design's reading):* v1 named eleven components in
  one folder and gave `TabProps` no home; one file per role keeps each short enough to read.
- **B8. Additive props and names** (Appendix A.2, A.3, §4.7). Props: `CodeFieldProps.readOnly?` (View YAML) and
  `.describedBy?` (an error shown elsewhere, for `aria-describedby`); `ValueEditorProps.testId?`;
  `NamespaceChecklistProps.label?` (the legend) and `.testIdPrefix?` (`dr-attached`, `dr-spawn`);
  `DecompositionEditorProps.onDeleted?` and `.onBackendLost` (B2); `FieldErrors`' `id?`, `testId?` and `located?`;
  `CardListProps`. Names: `isTabId` and `safeTheme` (`shared/protocol.ts`), `errorDetail` (`page/backend.ts`),
  `STILL_STARTING` (`page/texts.ts`), `ancestors` (`ui/tree.ts`), `safetyAcknowledged` and `acknowledgeSafety`
  (`ui/drafts.ts`); in `ui/texts.ts`, `INHERITED_ROW` (v1's lower-case form of `INHERITED` for Decompositions' rows),
  `RESTART` and `RELOAD` (v1's buttons of `BACKEND_LOST` and `SESSION_ENDED`), and `LABELS`: v1's labels plus
  `hintNote`, `alsoUsedIn`, `remove` (✕), `back`, `everyNamespace` and `notAttached`. A few labels are literals in
  their tab, not in `texts.ts`: Tools' "granted in"; Namespaces' "REPL", "Backbone", "May spawn into", "Tools",
  "Variables" and "System suffix"; the editor's "YAML" and "role". *Why (this design's reading):* each is additive and
  serves accessibility, a test id, or a sentence v1 named only in a table.
- **B9. Test ids beyond Appendix A.5**, listed there as v2 additions. Every id of v1's A.5 is present and means what
  A.5 says. v1's §8.4 item 6 names `dr-create-*` for E12, which neither v1's A.5 nor the build defines; E12 saves with
  the ids E8 uses (`dr-name`, `dr-use-when`, `dr-card-0-task`, `dr-card-1-code`, `dr-namespace-<namespace>`,
  `dr-save`, `dr-result`), and §8.4 item 6 now says so.

**Tests, wiring and the build**

- **B10. The fixture Library is a directory** (§7.3, Appendix A.4): `tests/canvas_app/fixtures/library/` holds
  `main.yaml` (the config: a profile with `entry_namespace: router`; namespaces `root`, `router`, `router.archive` and
  `course_advisor`; `triage nightly` top level, `catalog lookup` in `root`, `summarize then rank` in `router`; the tool
  `word_count`, granted in `course_advisor`), `library.yaml` (the use-when lines and hints, in the manifest an export
  writes and `dr-library import` reads beside `main.yaml`) and `tools/word_count.py` (the source `factory_from` names).
  v1 named one file, `fixtures/library.yaml`. *Why (this design's reading):* a tool with a source and the use-when lines
  both need files beside the config, and D2's import reads them from the config's folder.
- **B11. The `browser` fixture is module-scoped, and E8 drives its own Chromium through Playwright's async API**
  (§7.3, §7.4, Appendix A.4). v1: session-scoped, shared with E8. *Why (the code's comment):* "while Playwright's sync
  API is started, its event loop counts as running in this thread, so asyncio.run (D1's harness) fails until it
  stops." Module scope stops it at the end of each file, and E8's file, which runs D1's async harness, never starts it;
  E8 launches Chromium with `async_playwright` inside its own event loop and starts the backend with conftest's
  `serve` and `stop` instead of the `library_server` fixture. New conftest helpers: `serve`, `stop`, `ui_url`,
  `write_new`, `parent_site` (files served from another site, `http://localhost:<port>`, as Canvas's page is; used by
  `test_page_bundle.py` and `test_backend_loss.py`), `stale_head` (writes a head that no longer validates straight to
  D2's store, which the Library itself refuses to do; B1) and `SAFETY_ACK`.
- **B12. E8 needed no change to D1's harness** (§7.4, §11 item 8). `dr_acp(None, home)`, without `--config`, has
  existed since D2's `90044f0` (D2's design v2, B13). E8 as built points the profile's client at D1's `FakeOpenAI` with
  `put_profile`; opens conversations A and B in the Library's default namespace, `router` (the fixture's
  `entry_namespace`), rather than choosing it; and writes `FinalAnswer("CS201")` as the step's code. Every assertion
  of v1's §7.4 is made.
- **B13. CI** (§7.6). The `canvas-app` job runs on every push and pull request, with no path filter. *Why (the
  Implementer's report):* a `paths` filter applies to a whole workflow, and the job lives in D1's `ci.yml`. The
  committed-build check is `git status --porcelain -- src/deep_reasoning/canvas_app`, not `git diff --exit-code`.
  *Why (commit `375a3d1`):* "so a file the build adds or drops fails the check too." Also: Node comes from
  `canvas-app/.nvmrc`; the job checks deep_reasoner_beta out at `d7334ae` itself, as D1's job does, for the cards round
  trip; `uv sync --locked`; 2 min 54 s at `5effe26`, not about 4 minutes.
- **B14. Versions** (§1.1 C, §4.1, §4.6). Runtime: `preact` 10.29.8, `yaml` 2.9.1. Development: `vite` 7.3.6,
  `vitest` 3.2.7, `typescript` 5.9.3, `jsdom` 26.1.0 (per file, for `context`, `drafts` and `mount`), `prettier`
  3.6.2, `@types/node` 22.20.5; no `@preact/preset-vite` (Vite's esbuild takes `jsx` and `jsxImportSource` from
  `tsconfig.json`). Python: `playwright==1.56.0` in the dev group, added by D3 (v1: D5 adds `playwright`, D3 the same
  line if it lands first). *Why (commit `3ce186a`):* "Playwright is pinned at 1.56.0, whose Chromium build (1194) is
  the one preinstalled in the development sandbox; CI installs the same build with playwright install." D5's own
  Playwright line, when it lands, meets this pin in the same `pyproject.toml`.
- **B15. Build details and sizes** (§4.6). `vite.config.ts`: `base` is `./` for the build and `/ui/` for the dev
  server; `input: {app: "index.html"}`; `modulePreload: false` (this design's reading: one chunk, nothing to
  preload); the dev proxy's target is `DR_LIBRARY_URL`, else `http://127.0.0.1:8765`; vitest's default environment is
  `node`. Sizes at `5effe26`, from CI's build: the page bundle 6.96 kB (2.85 kB gzipped); the frame UI 151.78 kB of
  JavaScript (48.94 kB gzipped), 4.05 kB of CSS and 0.37 kB of HTML. v1 expected under 10 kB and about 170 kB. (v3:
  CI's build at `2af80ef`: the page bundle 7.09 kB (2.89 kB gzipped), the frame's JavaScript 151.96 kB (49.00 kB
  gzipped); the CSS and HTML unchanged. v4, at `d4e9cd3`: 7.12 kB (2.89) and 152.05 kB (49.04).)

**Size**

- **B16. About 4.6k lines of code and 3.1k of tests, against v1's 2.6k and 1.4k** (§3.1 item 11, §10). At `5effe26`,
  all lines (non-blank in brackets): code 4,588 (4,252), tests 3,135 (2,819), not counting the committed built files,
  the lockfile, the CI job (54 lines) or D3's 10 lines in D2's files. Code: `tabs/namespaces.tsx` 891,
  `components/editor.tsx` 857, `styles.css` 368, `api.ts` 186, `tabs/browse.tsx` 184, `cards.ts` 177,
  `components/fields.tsx` 176, `shared/protocol.ts` 165, `app.tsx` 151, `page/mount.ts` 137, `types.ts` 129,
  `page/backend.ts` 117, `texts.ts` 105, `page/context.ts` 96, `load.ts` 89, `page/host.ts` 72,
  `components/pickers.tsx` 72, `save.ts` 66, `library/ui.py` 59, `components/notices.tsx` 56, `drafts.ts` 49,
  `vite.config.ts` 45, `tabs/tools.tsx` 42, `theme.ts` 39, `tree.ts` 36, `tabs/create.tsx` 30, `package.json` 30,
  `yaml.ts` 26, and 138 in fourteen small files (entry points, the page's texts, `TabProps`, configuration, the
  manifest, the icon). Tests: vitest 1,628 (`cards` 338, `mount` 265, `api` 244, `backend` 178, `fakes.ts` 125,
  `context` 119, `protocol` 110, `save` 81, `drafts` 60, `yaml` 57, `tree` 51); browser 1,377 (`test_namespaces.py`
  272, `test_create.py` 260, `conftest.py` 200, `test_browse.py` 186, `test_page_bundle.py` 161, the fixture Library
  99, E8 88, `test_backend_loss.py` 42, `test_notice.py` 40, `test_tools_tab.py` 29); `tests/library/test_ui.py` 130.
  The Implementer's figures, about 4.5k and 3.0k, count the same files more loosely. The build recorded no reason for
  the growth; the estimate was this design's: v1 sized the Namespaces tab at 380 and the editor with its cards at 250,
  and left the stylesheet out. At the workspace's 300 lines an hour, about 26 h at Gate C. Michael rules on it at
  Gate B. *(v3: at `2af80ef`, code 4,610 (4,273) and tests 3,206 (2,883): B20–B23 added 22 lines of code
  (`components/editor.tsx` 869, `page/backend.ts` 127) and 71 of tests (`backend.test.ts` 203, `test_create.py` 306);
  still about 26 h. v4: at `d4e9cd3`, code 4,623 (4,285) and tests 3,308 (2,968): B20's fresh budget and B26 added 13
  lines of code (`page/backend.ts` 129, `tabs/namespaces.tsx` 902) and 102 of tests (`backend.test.ts` 222,
  `test_create.py` 320, `test_namespaces.py` 341); still about 26 h.)*

**Findings (no change to the design; each is an open item in §11)**

- **B17. 19 messages in 10 of Dean's decompositions open as raw cards.** Of the 43 decompositions in
  deep_reasoner_beta's `docs/configs` and `configs` at `d7334ae`, 10 have assistant messages (19 in all) with a blank
  line between `</think>` and `<repl>`, which §5.1's step form does not allow, so each is a raw card: shown and
  editable as text, and saved byte for byte (the round trip still holds). They are `docs/configs/catalog/agent.yaml`'s
  `catalog lookup`; `configs/example/agent.yaml`'s `direct computation`, `llm batch to process held data`, `break
  into sequential subtasks`, `batch independent subtasks`, `facts seen directly` and `exploring short and long text`;
  `configs/example/namespaces/math.geometry.yaml`'s `area of a circle`; `configs/example/namespaces/math.yaml`'s
  `numeric computation`; and `configs/example/rag_agent.yaml`'s `retrieve then answer with rag`. A `gap` field on
  `StepCard` (the newlines between `</think>` and `<repl>`, kept as `end` keeps the trailing one) would show them as
  steps and stay lossless. Counted for this revision with the build's `messagesToCards` over the files the corpus test
  reads. §11 item 11.
- **B18. `npm audit`: one moderate advisory, in development dependencies only.** GHSA-82fw-gwwq-j7x9 (path traversal
  through `@vitest/mocker`'s redirect mock) affects `vitest` and `@vitest/mocker` below 4.1.11; D3 has 3.2.7. `npm
  audit --omit=dev` finds nothing, and nothing of vitest is in the built files. Vitest 4.1.11 fixes it, but npm 10
  cannot resolve its pinned optional peers: on a copy of the lockfile, `npm install --package-lock-only
  vitest@4.1.11` with npm 10.9.4 fails with "Cannot read properties of null (reading 'edgesOut')" (tried for this
  revision). §11 item 12.
- **B19. D5's `SAFETY` is assumed to be a `str.format` template.**
  `test_notice.py::test_the_notice_is_d5s_sentence_with_the_cap` compares the notice with
  `dr_app.texts.SAFETY.format(cap=7)`, so it assumes D5's constant has a `{cap}` field; it is skipped until D5's
  `dr_app` is installed (CI's one browser skip). If D5 writes it otherwise (a function, or a jinja2 template, since the
  Code Guide forbids `.format()` in our own code), the test follows D5 (§8.4 item 7, §11 item 13).

**v3: fixed after the as-built check**

- **B20. A `start` that gets no answer reads the status** (§2.1, §4.2, §5.4, §11 item 6; commit `450bed1`). v2 ended
  every failed request in `BACKEND_FAILED`, so a `start` that outlasted C2's client (its requests "may take up to 60 s",
  `src/types/canvas-extension.ts:162` at `db3b4b9`) or lost the network gave up while the backend was still coming up;
  v1's §11 item 6 had said the page would fall back to polling. Built: when `POST …/start` rejects with an error that
  carries no numeric `status` (a plain `Error`: the client's timeout, or the network), `ensureBackend` reads the status
  and goes on by §2.1's table: `ready` mounts; `starting` is polled every 500 ms within a **fresh 45 s**, counted from
  when the start went unanswered; `stopped` or `unhealthy` is `BACKEND_FAILED` with the status's `detail`. A `start`
  the agent-server answered (C2's `HttpError`, which carries the status it answered with) still ends in
  `BACKEND_FAILED` in its own words. (v3, at `450bed1`, counted the 45 s from the start of the check, so after C2's
  full 60 s timeout a backend still `starting` ended in `STILL_STARTING` at the first read, the very case the fallback
  is for; v4, `c5964ff`, restarts the budget.) *Why (commits `450bed1`, `c5964ff`):* "a start that outlasts the
  client's timeout gave up while the backend was still coming up"; "the budget now restarts when start gets no
  answer." *Pinned by:* `backend.test.ts › ensureBackend › polls the status when start gets no answer, [until it is
  ready, and says why it did not start]` (`start` rejects with `Error("Request timeout after 60000ms")`; the calls are
  status, start, status) and, v4, `gives a backend still starting after start timed out a fresh 45 s` (a start that
  takes the client's 60 s and times out, then 40 `starting` reads, 20 s, then `ready`: the frame mounts).
- **B21. The Create draft keeps the namespace picked** (§2.3; commit `aaa97ef`). v2's draft held every field but the
  picked namespace, so a reload preselected again. Built: the stored draft has an optional `picked`, which wins over the
  preselection while the Library still has that namespace (else the preselection applies). Picking goes through the
  draft like any edit: it clears the result line and shows **Discard draft**. A save or **Discard draft** clears the
  draft, so the picker returns to the preselection, as for a new decomposition. *Why (commit `aaa97ef`):* "§2.3's draft
  holds every field; the picked namespace was the one it left out." *Pinned by:*
  `test_create.py::test_a_draft_keeps_the_namespace_picked_over_the_preselected_one` (`course_advisor` picked over the
  preselected `router`, then a reload: still picked, the button reads "Save to course_advisor"; **Discard draft**:
  `router` again).
- **B22. D2's errors that name no card sit above the cards** (§2.3, §2.2; commit `4123ec7`). §2.3 put them above the
  cards; v2 built their block, which also holds a refused save's message, below the cards, above the buttons. Built:
  between the namespace picker (or, for an opened decomposition, Attached to) and the cards, and above the YAML field in
  YAML mode. *Why (commit `4123ec7`):* §2.3's own placement. *Pinned by:*
  `test_create.py::test_an_error_that_names_no_card_shows_above_the_cards` (the picked namespace deleted behind the
  panel's back; D2's "There is no namespace 'router.archive' in the library." sits above card 0).
- **B23. Rename in YAML mode focuses the YAML** (§2.3; commit `2af80ef`). YAML mode has no name field (B24), so v2's
  Rename focused nothing there. Built: card mode focuses the name; YAML mode focuses the YAML field, which holds the
  name, and stays in YAML mode. *Why (commit `2af80ef`):* "in YAML mode there is no name field, since the name is the
  YAML's own, so Rename focused nothing." *Pinned by:*
  `test_create.py::test_rename_in_yaml_mode_focuses_the_yaml_which_holds_the_name`.
- **B24. YAML mode has no name field, and `NAME_REQUIRED` is a card-mode check** (§2.3). v1 said "a name is required"
  without saying in which mode. *Why (the Conductor's ruling, recorded as this design's reading):* in YAML mode the
  name is the YAML's own, and D2's validation speaks for it, in deep_reasoner's words. *Pinned by* (v4, `02b93dc`):
  `test_create.py::test_saving_without_a_name_in_card_mode_asks_for_one_and_writes_nothing` ("Give the decomposition a
  name." under the name; the Library's revision unchanged).
- **B25. Add namespace is not prefilled when `root` or Run settings is selected** (§2.4). v1 prefilled "the selected
  namespace's name and a dot" without exception. Built: empty for those two, `<selected>.` otherwise. *Why (the
  Conductor's ruling, recorded as this design's reading):* `root`'s children are top-level names (§2.4's tree rule,
  and deep_reasoner's: the parent of `a` is `root`), and Run settings is not a namespace. *Pinned by:*
  `test_namespaces.py::test_adding_and_deleting_a_namespace` for the prefill under `router` (`router.`) and, v4
  (`54625ab`), `test_namespaces.py::test_add_namespace_is_not_prefilled_under_root_or_run_settings[root, run-settings]`.

**v4: after the second as-built check**

- **B26. A namespace write answered after another node was selected keeps that selection** (§2.4; commit `d4e9cd3`).
  v3 selected the new namespace when D2 answered Add namespace, and the deleted one's parent when it answered Delete
  namespace, whatever the user had selected meanwhile; so an answer that arrived late moved the panel away from the
  node the user had just chosen (and, after a delete, took an open confirmation row with it). Built: the tab counts the
  user's selections; Add and Delete note the count when their write begins (for Delete, at the panel's last drawing of
  the namespace being deleted), and their select on the answer is dropped if the count has moved. *Why (commit
  `d4e9cd3`):* `test_adding_and_deleting_a_namespace` failed under load on two races: the test selected
  `course_advisor` while `course_advisor.deep`'s `PUT` was in flight (the test now waits for the new namespace's
  title, its missing wait), and after `router.next`'s delete the `/health` poll could drop its node before the answer
  was handled, so the panel jumped back to `router` after the user had chosen `root`. *Pinned by:*
  `test_namespaces.py::test_a_write_answered_after_another_node_is_selected_keeps_that_selection[add, delete]` (the
  frame's `PUT` or `DELETE` held in the browser, `course_advisor` selected, then the write let through: the write
  lands and `course_advisor` stays selected). Two behaviours are left as they are (§11 items 15 and 16).

---

## 4 · Modules

### 4.1 Files in deep-reasoning

```text
canvas-app/                            the TypeScript project (D3's source; not in any wheel)
    package.json                       scripts: build, test, typecheck, format:check, dev; engines.node ">=22 <23"
    package-lock.json                  committed; CI runs npm ci
    .nvmrc                             22
    .prettierrc.json, .prettierignore  Prettier at its defaults; node_modules and the lockfile skipped (v2)
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
            load.ts                    attempt, useLoaded, resolved: how a tab reads and writes D2 (v2, B7)
            types.ts                   D2's records, as TypeScript
            cards.ts                   messages ↔ cards (§5.1)
            save.ts                    the bodies of §5.2
            yaml.ts                    parseYaml, stringifyYaml (YAML 1.1)
            drafts.ts                  localStorage drafts, tolerant of a storage that throws
            tree.ts                    namespaceTree
            texts.ts                   the frame's sentences (§4.7)
            theme.ts                   applyTheme, DEFAULT_THEME
            components/                four files by role (v2, B7):
                fields.tsx             CodeField, ValueEditor, FieldErrors, ConfirmRow, Banner
                pickers.tsx            NamespacePicker, NamespaceChecklist
                notices.tsx            SafetyNotice, ProblemsBanner
                editor.tsx             DecompositionEditor, CardList
            tabs/                      props.ts (TabProps, v2), browse.tsx, create.tsx, namespaces.tsx, tools.tsx
            styles.css
    tests/                             vitest: <module>.test.ts per module (§7.2); fakes.ts, C2's host and the
                                       agent-server faked at their boundary (v2)
src/deep_reasoning/canvas_app/         the App package: package data, D5 stages it (§4.6)
    __init__.py                        docstring and APP_NAME
    canvas-extension.json              hand-written (§4.6)
    panel.svg                          hand-written icon
    dist/index.js                      built from src/page, committed
    ui/index.html, ui/assets/app.js, ui/assets/app.css      built from src/ui, committed
src/deep_reasoning/library/ui.py       /ui/ routes (§4.5)
tests/library/test_ui.py               the routes (no browser)
tests/canvas_app/                      pytest + Playwright (marker browser) and E8 (§7.3, §7.4); fixtures/library/ (v2, B10)
.gitattributes                         the built files: linguist-generated, -diff
.github/workflows/ci.yml               (D1's) gains the canvas-app job (§7.6)
```

Repository wiring: the root `pyproject.toml` declares the marker `browser` and adds `and not browser` to `addopts`
(beside D5's `not live and not desktop and not crossrepo`); the dev group has `playwright` (D5 adds it; D3 adds the same
line if D3 lands first; v2: D3 added `playwright==1.56.0`, B14). `.gitignore` gains `canvas-app/node_modules/`. Hatchling includes every tracked file under
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
   C2 appended to the container (C2 §6.2 step 3) and `isFrameMessage(event.data)`. (v2: the page looks the frame up as
   `container.querySelector("iframe")` when a message arrives; C2's code states that this element is the frame, §8.1.)
   - `select-tab` → `putFocus(tab, focus)`; `context.surface.selectTab(tab)` (C2 then disposes this mount and mounts the
     other tab, which takes the focus); only on a conversation-panel surface, the one with `selectTab` (v2, B6);
   - `reload` → dispose the frame and rerun from 1.
7. The disposer aborts, removes the listener and disposes the frame.

`takeFocus` and `putFocus` are a module-level map keyed by tab, read once: a focus is meant for the very next mount of
that tab.

**`ensureBackend(request, signal, onProgress)`** implements §2.1's table over `GET /api/canvas-extensions/installed/dr-library/backend`
and `POST …/backend/start {revision}` (`canvas_extensions_router.py:327–370`). It never calls `prepare`. A request that
fails is `BACKEND_FAILED` with the agent-server's own words (`errorDetail`, v2, B6); an abort rejects at once. (v3,
B20: except a `start` that gets no answer, an error without a numeric `status`, such as the client's timeout or a
network failure: then it reads the status and goes on by §2.1's table, within a fresh 45 s from then; v4, `c5964ff`.)

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
| `parent` | Canvas's origin; the only `targetOrigin` the frame posts to (v2: exactly an `http(s)` origin, else none; always none on the standalone page) | none: standalone (no messages, own tab row) |
| `namespace` | the open conversation's namespace | none |
| `started` | `1` when that namespace is fixed (the first message was sent) | not started |
| `cap` | the spend cap in USD as the profile states it, or `off` (v2: anything else is the default) | `5` |
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

(v2, B1: D2's bare 500 for a stale head is `BackendUnavailable(500)` here; `load.ts`'s `resolved()`, around the two
effective calls only, turns it into the stale-head failure with D2's sentence from `GET /problems`.)

**`load.ts`** (v2, B7) is how every tab talks to D2: `attempt(run, onBackendLost)` gives a tab D2's refusal
(`LibraryError`) and hands `BackendUnavailable` to the footer; `useLoaded(load, deps, onBackendLost)` loads on mount,
on each change of `deps` (`rev` among them) and on `reload()`, and drops a late answer to an older load; `resolved(load)`
is B1's rule.

**`app.tsx`** renders, in order: the safety notice until acknowledged; the tab named by `tab` (or the standalone tab
row and the selected tab); the problems banner; the backend-loss footer when any request has thrown
`BackendUnavailable`. It owns the `/health` poll and gives every tab `rev` (a refetch key), `health` and the frame
parameters. `navigateTab(tab, focus)` posts `select-tab` in a panel and switches its own state when standalone. (v2,
B6: a tab is drawn after the first `/health` answer; a later answer clears the footer.)

**Tabs** are §2.2–§2.5, each a `TabProps` component (`tabs/props.ts`). **Components** (Appendix A.3) are shared, D4
included, in four files by role (v2, B7): `fields.tsx` has `CodeField` (a monospace auto-growing textarea; `language`
is a hint only, for a later CodeMirror), `ValueEditor` (YAML or text, parse errors inline), `FieldErrors`,
`ConfirmRow` and `Banner`; `pickers.tsx` has `NamespacePicker` (one of) and `NamespaceChecklist` (some of, with fixed
inherited entries); `notices.tsx` has `SafetyNotice` and `ProblemsBanner`; `editor.tsx` has `DecompositionEditor` (the
editor of §2.2 and §2.3) with `CardList`.

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

(v2, B6: the 503's body is `{"error": "not_built", "message": UI_NOT_BUILT}`, D2's error shape.)

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
  "version": "0.1.0",
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

`version` is deep-reasoning's package version (a test pins it, §7.5); D5 prints it. (v2, B5: `"0.1.0"`, the package's
version; v1's block said `"1.0.0"`, against its own rule.)

**The build** (`npm run build` in `canvas-app/`) runs two Vite builds:

- `vite build` (`vite.config.ts`): `base: "./"`, `build.outDir: "../src/deep_reasoning/canvas_app/ui"`,
  `emptyOutDir: true`, `rollupOptions.output`: `entryFileNames: "assets/app.js"`, `assetFileNames: "assets/[name][extname]"`,
  `inlineDynamicImports: true`. Fixed names keep every build's file set the same. (v2, B15: also
  `rollupOptions.input: {app: "index.html"}` and `modulePreload: false`; `base` is `/ui/` for the dev server.)
- `vite build --config vite.page.config.ts`: `build.lib` with `entry: "src/page/index.ts"`, `formats: ["es"]`,
  `fileName: () => "index.js"`, `outDir: "../src/deep_reasoning/canvas_app/dist"`.

Both minify. Expected sizes: the page bundle under 10 KB; the frame UI about 170 KB minified (Preact ≈10, `yaml` ≈110,
D3's code ≈50), about 50 KB gzipped. (v2, B15, measured in CI at `5effe26`: the page bundle 6.96 kB, 2.85 kB gzipped;
the frame UI 151.78 kB of JavaScript, 48.94 kB gzipped, plus 4.05 kB of CSS.)

**Committed, and checked.** The CI job builds with Node 22 from `package-lock.json` and runs `git diff --exit-code --
src/deep_reasoning/canvas_app`; a difference fails the job and uploads the fresh build as an artifact to commit. (v2,
B13: the check is `git status --porcelain -- src/deep_reasoning/canvas_app`, so a file the build adds or drops fails it
too.)
`.gitattributes` marks `src/deep_reasoning/canvas_app/dist/**` and `src/deep_reasoning/canvas_app/ui/**`
`linguist-generated=true -diff`, so diffs and the PR stack show them as changed files, not minified text; Gate C reads
`canvas-app/src`.

**`npm run dev`** serves the frame UI with Vite's dev server at `http://localhost:5173/ui/`, proxying D2's paths
(`/health`, `/problems`, `/validate`, `/profile`, `/namespaces`, `/effective`, `/decompositions`, `/tools`) to
`DR_LIBRARY_URL` with `changeOrigin` (so D2 sees its own `Host`); v2: `http://127.0.0.1:8765` when it is unset.

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
| `STILL_STARTING` | `it was still starting after 45 seconds.` (v2, B4: `BACKEND_FAILED`'s detail when the page gives up on a `starting` backend) |

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
| `INHERITED` | `Inherited from {source}` (in Decompositions rows: `inherited from {source}`, v2's `INHERITED_ROW`) |
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
| `BACKEND_LOST` | `The Library stopped answering ({status}).` with `Restart` (v2's `RESTART`) |
| `SESSION_ENDED` | `The panel's session with the Library ended.` with `Reload` (v2's `RELOAD`) |
| `NO_TOOLS` | `No tools in the Library.` |
| `DISCARD_DRAFT` | `Discard draft` |

Labels: `Name`, `Use when`, `Hint`, `Namespace`, `task`, `think`, `code`, `output`, `+ turn`, `View YAML`, `Edit YAML`,
`Edit as cards`, `Save to {namespace}`, `Save`, `Delete`, `Attached to`, `Override`, `Edit`, `Reset`, `Add variable`,
`Add namespace`, `Delete namespace`, `Run settings`, `Add setting`, `Attach…`, `Detach`. (v2, B8: they are `LABELS` in
`ui/texts.ts`, which also has `what the slash command asks for; optional` (the hint's note), `also used in {namespace}
(inherited)`, `✕`, `← Decompositions`, `Every namespace's menu` and `Not attached`. A few are literals in their tab:
`granted in` (Tools); `REPL`, `Backbone`, `May spawn into`, `Tools`, `Variables`, `System suffix` (Namespaces); `YAML`
and `role` (the editor).)

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
edit       validate and warnings as for create                          (v2, B3)
           PUT /decompositions/<record.slug> updateBody(draft, checked)
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
starting it, for example D5's setup at launch) is polled at 500 ms up to 45 s, then given up with `STILL_STARTING`
(v2, B4). An aborted mount stops polling at once. (v3, B20: a `start` that gets no answer, C2's client timing out after
60 s or the network failing, reads the status and goes on as above, with a fresh 45 s from then (v4, `c5964ff`; v3
counted them from the start of the check, which a 60 s timeout had already used up).)

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

There is no live tier: nothing in the panel calls a model, and the one real service it talks to, D2's backend, runs for
real in every browser test. (v2: so Proof Green for D3 is the CI run alone, run 37090168700 at `5effe26`; v3: run
37139529187 at `2af80ef`; v4: run 37144441476 at `d4e9cd3`.)

### 7.2 vitest (`canvas-app/tests/`)

| File | Pins |
|---|---|
| `cards.test.ts` | each form of §5.1 parses and renders (a table: inline and block think, no think, trailing newline or not, empty think → raw, prose outside the tags → raw, an observation not after a step → task, a system message → raw); `test round trip is identity` over a generated set (random roles, contents with and without the tags); over every decomposition in `$DR_BETA_CHECKOUT/docs/configs` and `configs` (read in place with `yaml` 1.1; skipped without the variable; a guard fails when `CI` is set and it is unset); `addTurn` adds the missing output before the new step; `removeTurn` takes the output with its step; `turnNumbers`; `cardIndexForLoc` |
| `yaml.test.ts` | the agreement table of the header's item 3 (each value as PyYAML reads it); `stringifyYaml` output reparses to the same value; multi-line strings are literal blocks; a syntax error throws with its message |
| `protocol.test.ts` | `readFrameParams(frameSearch(p))` equals `p`; an unknown tab, a bad `theme` JSON or an unsafe token value falls back; `isFrameMessage` accepts the two shapes only |
| `context.test.ts` | `spendCapFromArgs` table (`["--home", h, "--spend-cap-usd", "7"]` → `7`; `--spend-cap-usd=2.5` → `2.5`; absent → `5`; `--no-key-proxy` → `off`; `abc` → `5`); `readConversationNamespace` with a fake `request`: one value → started, several → not started, no event, another agent's options, a failing request → `null`; `readTheme` keeps the listed tokens and drops unsafe values |
| `backend.test.ts` | `ensureBackend` over each row of §2.1's table with a fake `request` (calls and their order recorded): `ready` makes one call; `stopped` and prepared → `start` with the revision; not prepared → `NOT_APPROVED` and no `start`, never `prepare`; `starting` polls until ready; `start` answering `unhealthy` → `BACKEND_FAILED` with its detail; an abort stops polling; v3: a `start` that gets no answer reads the status, then mounts when it is ready or says why it did not start (B20) |
| `mount.test.ts` (jsdom) | a fake host (C2's API at its boundary: `registerPage`, `agentServer.request`, `appBackend.mountFrame` appending an `iframe`): `activate` registers exactly the four tab ids; a mount builds the frame path from the conversation's namespace, the cap and the theme; a second mount for another conversation carries that conversation's namespace (E11's "mounts with the right conversation", D3's part); a `select-tab` message from the frame's window calls `surface.selectTab` and the next mount of that tab gets the focus; the same message from another window is ignored; `reload` remounts; `onError("not-ready")` remounts once; disposing during the backend check leaves the container empty and no frame |
| `api.test.ts` | with `fetch` stubbed: every body is JSON with exactly D2's field names; a D2 error body → `LibraryError` with code, errors and head; the bridge's `{"detail"}` 503, a non-JSON 502 and a network failure → `BackendUnavailable` |
| `save.test.ts` | `createBody`, `saveAsNextBody` (the head's namespaces first, the picked one once), `updateBody`; `use_when` and `hint` are always present (`null` when blank) |
| `drafts.test.ts` | a draft round-trips; a `localStorage` that throws on read or write loses the draft and nothing else |
| `tree.test.ts` | `namespaceTree` from dotted names (root's children, nested levels, order kept); v2: `ancestors` |
| `fakes.ts` (v2) | not a test: C2's host (`registerPage`, `agentServer.request`, `appBackend.mountFrame` appending an `iframe` to the container, as C2 §6.2 step 3 does) and the agent-server's answers, faked at their boundary for `mount.test.ts` and `backend.test.ts` |

v2, as built: 149 cases in ten files, 148 passed and one skipped (the corpus guard, which runs only without the
corpus): `api` 28, `cards` 28 (the skip among them), `protocol` 22, `context` 18, `yaml` 15, `backend` 12, `mount`
10, `tree` 6, `save` 6, `drafts` 4. `context`, `drafts` and `mount` run in jsdom (`// @vitest-environment jsdom`), the
rest in Node. `mount.test.ts` adds two cases to v1's list: `says the backend is not approved, and Try again checks
again` and `says when Canvas cannot show an App's frames`; `backend.test.ts` also pins the 45 s limit (`gives up on a
backend still starting after the timeout`, B4).

v3, at `2af80ef`: 151 cases. With deep_reasoner_beta's configs (CI), 150 passed and one skipped (the guard); without
them, 149 passed and two skipped (the guard and the corpus round trip). `backend` has 14: B20 adds `polls the status
when start gets no answer, [until it is ready, and says why it did not start]`.

v4, at `d4e9cd3`: 152 cases. With the configs, 151 passed and one skipped; without them, 150 passed and two skipped.
`backend` has 15: `gives a backend still starting after start timed out a fresh 45 s` (B20); the helper `agentServer`
takes an optional `startTakesMs`.

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

v2, as built: the fixture Library is the directory `tests/canvas_app/fixtures/library/` (`main.yaml`, `library.yaml`
with the use-when lines and hints, `tools/word_count.py`; B10); `browser` is **module-scoped** (B11); and conftest
adds `serve` and `stop` (the server without the fixture, for E8), `parent_site` (files served from
`http://localhost:<port>`, another site than the frame's, as Canvas's page is), `stale_head` (B1), `ui_url`,
`write_new` and `SAFETY_ACK`. 48 cases in eight files, 47 passed and one skipped (D5's sentence, B19); the new test
and the parametrizations are marked v2 below. v3, at `2af80ef`: 51 cases, 50 passed and the same one skipped;
`test_create.py` gains three (B21–B23), marked v3. v4, at `d4e9cd3`: 56 cases, 55 passed and the same one skipped;
`test_create.py` gains one (B24) and `test_namespaces.py` four (B25, B26), marked v4.

| File | Tests (each named for its property) |
|---|---|
| `test_browse.py` | `test_decompositions_are_grouped_by_namespace_with_version_slash_command_and_use_when`; `test_an_inherited_decomposition_says_where_it_comes_from`; `test_top_level_and_unattached_decompositions_have_groups_of_their_own`; `test_saving_an_opened_decomposition_makes_its_next_version`; `test_attached_to_is_the_exact_set_after_a_save`; `test_a_stale_save_offers_reload_or_save_over`; `test_deleting_a_decomposition_detaches_it_everywhere`; `test_a_change_made_elsewhere_appears_without_a_reload` (a `put_decomposition` through the Python API; the row appears within the poll); `test_the_tab_falls_back_to_attachments_when_inheritance_cannot_be_resolved`; `test_focus_opens_that_decomposition` |
| `test_create.py` | `test_saving_stores_version_1_in_the_picked_namespace` (the record's messages equal what the cards showed; `namespaces == [picked]`; `use_when`, `hint`); `test_the_picker_lists_the_librarys_namespaces_and_preselects_the_conversations`; `test_without_a_conversation_namespace_the_default_namespace_is_preselected` (v2: `[None, not_in_the_library]`); `test_the_saved_line_says_the_started_conversation_does_not_change` (`started=1` → `SAVED_STARTED`; otherwise `SAVED`; v2: one case each); `test_validation_errors_show_on_the_card_they_name`; `test_an_example_without_final_answer_asks_before_saving` (Cancel stores nothing; Save anyway stores it); `test_an_existing_name_offers_to_save_the_next_version_keeping_its_namespaces`; `test_view_yaml_shows_the_canonical_yaml_and_edited_yaml_returns_to_cards`; `test_use_when_in_the_yaml_is_refused_in_deep_reasoners_words`; `test_a_draft_survives_reloading_the_frame`; `test_use_when_and_hint_survive_a_save_that_did_not_touch_them`; `test_an_imported_decomposition_saved_unchanged_makes_no_new_version` (cards are lossless end to end); v3: `test_a_draft_keeps_the_namespace_picked_over_the_preselected_one` (B21), `test_an_error_that_names_no_card_shows_above_the_cards` (B22), `test_rename_in_yaml_mode_focuses_the_yaml_which_holds_the_name` (B23); v4: `test_saving_without_a_name_in_card_mode_asks_for_one_and_writes_nothing` (B24) |
| `test_namespaces.py` | `test_the_tree_follows_dotted_names_and_marks_the_default`; `test_each_field_shows_its_effective_value_and_source`; `test_override_sets_a_field_here_and_reset_removes_it`; `test_a_variable_is_overridden_and_reset_key_by_key`; `test_a_tool_granted_here_adds_to_the_inherited_ones`; `test_attach_and_detach_change_only_this_namespaces_list`; `test_start_new_conversations_here_moves_the_default` (`/health`'s `default_namespace`); `test_adding_and_deleting_a_namespace` (and D2's refusal for root, the default and a parent, in its words); `test_run_settings_edit_the_profile`; `test_yaml_values_mean_what_dr_reads` (a variable typed as `on` is stored `true`); `test_keys_the_panel_does_not_show_survive_an_override`; v2: `test_a_namespace_whose_inheritance_cannot_be_resolved_says_why` (B1); v4: `test_add_namespace_is_not_prefilled_under_root_or_run_settings[root, run-settings]` (B25), `test_a_write_answered_after_another_node_is_selected_keeps_that_selection[add, delete]` (B26; `test_adding_and_deleting_a_namespace` now also waits for the added namespace's title) |
| `test_tools_tab.py` | `test_the_tools_tab_always_shows_the_safety_notice_with_the_cap` (v2: `[5, 12]`, the cap from the URL); `test_the_tools_tab_lists_tools_with_their_grants` |
| `test_notice.py` | `test_the_safety_notice_shows_until_understood`; `test_the_notice_is_d5s_sentence_with_the_cap` (equal to `dr_app.texts.SAFETY` formatted with `7`; skipped until D5's package is in the environment); `test_without_the_key_proxy_the_notice_says_nothing_caps_spending` |
| `test_backend_loss.py` | `test_a_backend_that_stops_answering_offers_restart` (kill the server; the next poll shows `BACKEND_LOST`; in a panel, Restart posts `reload`, checked through a parent page that records messages; v2: the parent is on `parent_site`, and the status is `0`, no answer) |
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

v2, as built (B11, B12): D2 made the harness change (`90044f0`), so D3 changed nothing of D1's. The profile's client is
pointed at `FakeOpenAI` with `put_profile`; A and B open in the Library's default namespace, `router` (the fixture's
`entry_namespace`), rather than choosing it; the server is started with conftest's `serve` and `stop`, and the browser
with Playwright's async API inside the test's own event loop, since the sync API's loop would make D1's `asyncio.run`
fail. The step's code is `FinalAnswer("CS201")`. Every assertion above is made, the menu's as
`description == use_when` on B's `rank-by-prerequisites` command.

### 7.5 `tests/library/test_ui.py` (no browser)

`test_ui_serves_the_index_and_the_built_assets` (Starlette's `TestClient` with `Host: 127.0.0.1:<port>`, D2's guard
included); `test_a_file_not_in_the_build_is_404`; `test_no_path_outside_the_assets_is_served` (`..`, encoded, nested);
`test_every_answer_carries_the_csp_and_no_cache`; `test_an_unbuilt_ui_is_503_with_its_sentence`;
`test_the_ui_answers_only_its_own_host` (403 through D2's guard); `test_the_manifest_is_valid_and_its_version_is_the_packages`
(the JSON's keys, kebab-case ids, four tabs, `entrypoint` and `icon` present in the package; S2's own model validates it
in D5's cross-repo job); `test_the_committed_build_is_complete` (`dist/index.js`, `ui/index.html`, `ui/assets/app.js`
exist and `index.html` references only `./assets/` files). v2: 16 cases with the parametrizations, all in D1's `test`
job.

### 7.6 CI: the `canvas-app` job (`.github/workflows/ci.yml`)

On every push touching `canvas-app/**`, `src/deep_reasoning/canvas_app/**`, `src/deep_reasoning/library/**`,
`tests/canvas_app/**` or the workflow:

1. `actions/setup-node` (Node 22, npm cache on `canvas-app/package-lock.json`); `npm ci`.
2. `npm run typecheck`, `npm run format:check`, `npm test` (with `DR_BETA_CHECKOUT` as D2's job sets it).
3. `npm run build`; `git diff --exit-code -- src/deep_reasoning/canvas_app` (on failure, upload the build).
4. `uv sync`; `uv run playwright install --with-deps chromium`; `uv run pytest -m browser tests/canvas_app` with
   `CI=true`.

About 4 minutes. `tests/library/test_ui.py` runs in D1's existing Python job.

v2, as built (B13): the job runs on **every** push and pull request, with no path filter (a `paths` filter applies to a
whole workflow, and the job is in D1's `ci.yml`). Its steps: checkout; `actions/setup-node` with
`node-version-file: canvas-app/.nvmrc` and the npm cache; deep_reasoner_beta checked out at `d7334ae` into
`$DR_BETA_CHECKOUT`, as D1's job does; `npm ci`, `typecheck`, `format:check`, `test`, `build`; the check
`git status --porcelain -- src/deep_reasoning/canvas_app` (any change, added or dropped files included, fails with
"src/deep_reasoning/canvas_app differs from a fresh build"), and on failure the upload of `dist/` and `ui/` as the
artifact `canvas-app-build`; `astral-sh/setup-uv` (Python 3.12); `uv sync --locked`;
`uv run playwright install --with-deps chromium`; `uv run pytest -m browser tests/canvas_app -v -rA`, with `CI=true`.
2 min 54 s at `5effe26`; 3 min 5 s at `2af80ef` (v3); 3 min 22 s at `d4e9cd3` (v4).

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
  - **v2: C2's code states it; C2's design does not.** C2's design at `72aa49f` (its only revision) still says only that
    `mountFrame` appends one `<iframe>` (§6.2 step 3) and that the disposer removes it (step 5); nothing in its §7.4.
    C2's code on the Canvas fork's `feat/agent-surfaces` at `db3b4b9` states it three times: the public type's doc,
    `CanvasExtensionAppBackendHost.mountFrame` in `src/types/canvas-extension.ts:133–138` ("The frame is the
    `<iframe>` appended to the container, kept there (also across session refreshes) until the returned disposer
    runs."); `mountAppBackendFrame`'s doc in `src/extensions/mount-app-backend-frame.ts:46–52`; and the fork's
    `specs/canvas-extensions.md:142–144` ("That element is the frame: it stays in the container, also across session
    refreshes, until the returned disposer removes it."). Its tests pin it:
    `mount-app-backend-frame.test.ts` "appends a sandboxed frame of the App's backend to the container, at the page's
    path" and "keeps its frame in the container through session refreshes, and when one fails adds the notice beside
    it". A failed refresh adds a `<p>` notice beside the frame, never a second `iframe`, so D3's
    `container.querySelector("iframe")` finds the frame. No `onFrame` is needed. C2's code is not yet green: it waits
    on the wiring commit that pins S2's client (§11 item 14). D3's `mount.test.ts` fakes `mountFrame` the same way
    (`canvas-app/tests/fakes.ts`, appending the `iframe` to the container), and `test_page_bundle.py`'s parent page
    does too.
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
  `/health` carries `rev` and `default_namespace`. (v2: and `GET /problems` names a head that no longer validates, in
  D2's sentence, while the effective routes fail; B1.)
- **v2, open for D2: a stale head should be a 422, not a bare 500** (§3.2 B1, §11 item 10). When a head no longer
  validates, `GET /effective` and `GET /namespaces/<name>/effective` answer Starlette's plain-text 500: D2's
  resolution raises something its error handler does not map. D2 should answer **422** in its error shape with that
  head's sentence (the one `GET /problems` gives). Until it does, the panel reads a 500 from those two routes, and only
  those, as this case and fetches the sentence from `/problems`; once D2 answers 422, `load.ts`'s `resolved()` already
  shows D2's message (a `LibraryError`), and its 500 branch can go.

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
  props (`rev`, `health`, `params`, `navigateTab`). (v2, B7: `CodeField`, `FieldErrors`, `ConfirmRow` and `Banner` are
  in `components/fields.tsx`, `NamespaceChecklist` in `components/pickers.tsx`, `TabProps` in `tabs/props.ts` and
  with `onBackendLost`; `load.ts`'s `attempt` and `useLoaded` are how a tab reads and writes D2 so that an unanswered
  request reaches the footer. `NamespaceChecklist` takes `label` and `testIdPrefix`, so D4's per-namespace grant list gets its
  own legend and its own ids.)
- **Data the frame cannot read** (Canvas's MCP server list, from the agent-server's settings) comes as a new frame
  parameter: D4 adds the field to `FrameParams` (`shared/protocol.ts`) and its read to `page/context.ts` through
  `host.agentServer.request`, with the same tolerance (a failure is "unknown").
- **Writes** follow §5's rules: `base_version` always; resend every field a `PUT` replaces (`source`, and `granted_in`
  when the grants are on screen).
- **Tests** go beside D3's: vitest units in `canvas-app/tests/`, browser tests in `tests/canvas_app/test_tools_tab.py`
  with the same fixtures (D4 adds a tool with a factory error to `fixtures/library.yaml` if it needs one; v2, B10: the
  fixture is `fixtures/library/main.yaml`, with a tool's source under `fixtures/library/tools/`).
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
   minutes (C2's renewal). (v2, B9: no id is called `dr-create-*`, in v1's A.5 or in the build; Create decomposition's
   are the editor's, as E8 uses them: `dr-name`, `dr-use-when`, `dr-card-0-task`, `dr-card-1-code`,
   `dr-namespace-<namespace>`, `dr-save`, `dr-result`; the Namespaces tab's tree is `dr-node-<namespace>`.)
7. **D5's `SAFETY` and D3's stay equal**: D3's `test_the_notice_is_d5s_sentence_with_the_cap` imports `dr_app.texts`;
   a change to one is a change to both. (v2, B19: the test calls `SAFETY.format(cap=7)`, assuming a template with a
   `{cap}` field; if D5 writes it otherwise, the test follows D5. Skipped until `dr_app` is installed.)

### 8.5 S2

None. D3's manifest is the one S2 §5.1 validates, with `description` and the icon path as D3 places it.

---

## 9 · What D3 relies on

| # | Behaviour relied on | Their code |
|---|---|---|
| C2-1 | `registerPage(<tab id>, mount)`; the mount context's `container`, `path`, `conversationId` (never null in a panel), `surface.selectTab`; a tab mounted only while visible and disposed on every switch, close, conversation change | C2 `72aa49f` §4.1, §7.1–§7.3, Appendix A.1 |
| C2-2 | `host.appBackend.mountFrame(container, {path, title, onError})`: a frame at `lease.url + path` (leading `/` stripped; query kept) with the bridge's sandbox, appended to the container; `onError` reasons; the keeper renews the cookie; (v2) the appended `<iframe>` is the frame and stays in the container until the disposer runs | C2 §6.2, §6.3, §7.4, Appendix A.11; v2: Canvas fork `feat/agent-surfaces` `db3b4b9`, `src/types/canvas-extension.ts:133–138`, `src/extensions/mount-app-backend-frame.ts` (not yet green, §11 item 14) |
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
| D1-2 | The test harness (`tests/acp/harness.dr_acp`, `ShimConnection`, `FakeOpenAI`) and `run.start.source.versions` | `v1-dr-acp` `21c2c7a`; v2: `dr_acp(None, home)` from D2's `90044f0` |
| D2-1 | The HTTP API of D2 §6 as built: routes, bodies (`extra="forbid"`), errors (`error`, `message`, `errors`, `head`), the guard (same user, `Host`, JSON) | `v1-library-store` `5158693`, `api.py` |
| D2-2 | (v2) A head that no longer validates: the effective routes answer a bare 500, and `GET /problems` gives the head's sentence | D2's `api.py` as on this branch at `5effe26`, lines 344–352 (the routes; the app's one handler maps only `LibraryError`, line 380); measured, §3.2 B1 |
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

**As built at `d4e9cd3`** (v4; v3 counted at `2af80ef`, 13 lines of code and 102 of tests fewer; v2 at `5effe26`, 35 and 173 fewer; §3.2 B16; all lines, the committed built files, the lockfile and the CI job's 54 lines
not counted):

| Part | Code, v1 → built | Tests, v1 → built |
|---|---|---|
| The page bundle (`index` 12, `texts` 14, `host` 72, `context` 96, `backend` 129, `mount` 137) | 300 → 460 | 260 → 731 (`mount` 265, `backend` 222, `context` 119, `fakes.ts` 125) |
| The frame protocol | 70 → 165 | 50 → 110 |
| UI core (`api` 186, `cards` 177, `app` 151, `types` 129, `texts` 105, `load` 89, `save` 66, `drafts` 49, `theme` 39, `tree` 36, `yaml` 26, `main` 15) | 820 → 1,068 | 330 → 831 (`cards` 338, `api` 244, `save` 81, `drafts` 60, `yaml` 57, `tree` 51) |
| The stylesheet | — → 368 | — |
| Components (`editor` 869, `fields` 176, `pickers` 72, `notices` 56) | 520 → 1,173 | — |
| Tabs (`namespaces` 902, `browse` 184, `tools` 42, `create` 30, `props` 14) | 770 → 1,172 | — |
| Python (`library/ui.py` 59, `canvas_app/__init__.py` 5; plus 10 lines in D2's `api.py` and `texts.py`) | 50 → 64 | 60 → 130 (`test_ui.py`) |
| Browser tests (fixture Library 99, `conftest.py` 200, test files 1,119) and E8 (88) | — | 720 → 1,506 |
| Build configuration (`package.json`, `tsconfig.json`, two Vite configs, `index.html`, Prettier, `.nvmrc`, `.gitattributes`, the manifest, the icon) | 110 → 153 | — |
| **Total** | **≈2.6k → 4,623** | **≈1.4k → 3,308** |

About 7.9k lines with tests, about 26 h at Gate C. The growth is in the two largest files (the Namespaces tab, three
times v1's figure: seven field kinds, each with its own editor and actions, and the run settings; the editor, three
and a half times: card and YAML modes, live validation, five outcomes with their actions, drafts and Attached to), the
stylesheet v1 left out, and tests that grew with them. The build recorded no reason; the estimate was this design's.

---

## 11 · Open items, and what I was unsure about

1. **Electron's Chromium** has not run the frame: the probe used headless Chromium 153 and a replica of the bridge. D5's
   E12 step 5 (a probe App) and its final flow (D3's panel) are the proof; if Electron refuses the partitioned cookie,
   D5 §11 item 11 names the fallbacks, and D3 changes nothing (the frame's URLs are relative).
2. **The committed build must be reproducible** on a developer's machine and in CI (Node 22, the lockfile, Vite's
   deterministic output). If a developer's build differs, the CI job's artifact is what gets committed; a recurring
   difference would mean pinning Vite's and esbuild's platform binaries, which I have not measured. (v2: the build
   committed from the development sandbox equals CI's fresh build at `5effe26`; one data point, not a measurement
   across machines.)
3. **YAML 1.1 in the browser and PyYAML** agree on every case I tried (header item 3); PyYAML's resolver has corners
   (`=`, `<<` merge keys in odd places) I did not test. The backend is authoritative: the panel shows D2's canonical YAML
   after every save.
4. **C2's frame placement** (§8.1): D3 relies on the iframe being in the container. Small, but a contract C2 should
   state. *(v2: C2's code states it and tests it, at `db3b4b9` on the Canvas fork; C2's design at `72aa49f` does not.
   Settled once C2's code is green, item 14; C2's design could say it in one line when it next revises.)*
5. **The profile editor** (Run settings) is in because D2 §3 item 1 says D3 edits the seven settings; the spec's D3
   bullets name only the default namespace. If the Conductor reads it as scope growth, it is one node of the tree and
   about 60 lines to drop.
6. **`host.agentServer.request`'s timeout** is not stated by C2; `start` can take up to the backend's 30 s health
   timeout. If the client's default is shorter, `ensureBackend` falls back to polling the status, which §2.1's table
   already does for `starting`. *(v3: C2's code states it, 60 s per request, `src/types/canvas-extension.ts:162` at
   `db3b4b9`. The fallback was not in v2's build and is built since `450bed1`, for a timeout or a network failure,
   §3.2 B20; since `c5964ff` (v4) it gets a fresh 45 s, so a start that timed out at 60 s can still finish. Closed.)*
7. **The spec's tooltip** "Show decompositions" versus C2's "Show Decompositions" (§3 item 8) is Michael's to care about
   or not.
8. **D1's harness** requires `--config` today (`tests/acp/harness.py:180–203`); the E8 test needs it optional (§7.4).
   *(v2: resolved by D2's `90044f0`, §3.2 B12.)*
9. **Size** (§10) is about twice the spec's estimate. *(v2: built at about 7.7k lines with tests (v3: 7.8k; v4: 7.9k), about
   five times the spec's ≈1.5k and about twice v1's ≈4k; Michael rules on it at Gate B, §3.2 B16.)*
10. **(v2) D2 answers a stale head with a bare 500** on `/effective` and `/namespaces/<name>/effective` (§3.2 B1, §8.2).
    D2's to fix: a 422 in its error shape with the head's sentence. The panel works either way.
11. **(v2) 19 messages in 10 of Dean's decompositions open as raw cards** (§3.2 B17): a blank line between `</think>`
    and `<repl>`. A `gap` field on `StepCard` would show them as steps, still lossless: a small change to `StepCard`,
    `parseStep` and `renderStep`, and a few table cases. Not built: raw cards are correct, only less convenient.
12. **(v2) `npm audit`'s moderate advisory in `@vitest/mocker`** (§3.2 B18): development only, nothing shipped. Moving
    to Vitest 4.1.11 waits on an npm that resolves its optional peers (or on installing them explicitly); until then
    it stays at 3.2.7.
13. **(v2) D5's `SAFETY` shape** (§3.2 B19, §8.4 item 7): D3's test assumes `SAFETY.format(cap=…)`. D5 decides the
    shape; the test follows it when D5's package lands and the test stops skipping.
14. **(v2) C2's code is not yet green.** It is built on the Canvas fork (`feat/agent-surfaces`, `db3b4b9`) and waits on
    a wiring commit that pins S2's client. D3's browser tests stand in for C2's host with a page of their own
    (`test_page_bundle.py`); the real host is first exercised by D5's E12.
15. **(v4) A late namespace write's refusal shows under whatever is selected when it arrives** (§3.2 B26). The
    Namespaces tab keeps one message line; a write that D2 refuses after the user moved to another node puts D2's
    sentence there, under that node, until the next selection clears it. Known and left as is: the sentence still names
    the namespace it is about.
16. **(v4) Just after Add namespace, the panel shows the default namespace for one Library reload** (§3.2 B26). The new
    name is selected when D2 answers, but the tab's copy of the Library does not have it until its reload returns, and
    a selection the Library lacks falls back to the default namespace; the new namespace shows once the reload lands.
    Known and left as is.

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
export declare function isTabId(value: unknown): value is TabId; // v2
export declare function safeTheme(
  theme: Readonly<Record<string, unknown>>,
): Record<string, string>; // v2: the listed tokens whose values are safe

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
export declare function errorDetail(error: unknown): string; // v2: an HttpError's detail, else the message

// page/texts.ts (§4.7; v2 adds)
export const STILL_STARTING = "it was still starting after 45 seconds.";

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
// v2: the one function the others are built on
export declare function call<T>(
  method: "GET" | "POST" | "PUT" | "DELETE",
  path: string,
  body?: unknown,
): Promise<{
  status: number;
  data: T;
}>;

// ui/load.ts (v2, B7): how a tab reads and writes D2
export type OnBackendLost = (error: BackendUnavailable) => void;

export type Attempt<T> =
  | {
      ok: true;
      value: T;
    }
  | {
      ok: false;
      error: LibraryError;
    }
  | {
      ok: false;
      error: null; // the backend did not answer; the footer says so
    };

export interface Loaded<T> {
  data: T | null;
  error: LibraryError | null;
  reload: () => void;
}

export type Resolved<T> =
  | {
      value: T;
      failure: null;
    }
  | {
      value: null;
      failure: string; // D2's sentence for the stale head, from GET /problems (B1)
    };

export declare function attempt<T>(
  run: () => Promise<T>,
  onBackendLost: OnBackendLost,
): Promise<Attempt<T>>;
export declare function useLoaded<T>(
  load: () => Promise<T>,
  deps: readonly unknown[],
  onBackendLost: OnBackendLost,
): Loaded<T>; // load on mount, on each change of deps and on reload(); a late answer to an older load is dropped
export declare function resolved<T>(load: () => Promise<T>): Promise<Resolved<T>>;

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
export declare function safetyAcknowledged(): boolean; // v2
export declare function acknowledgeSafety(): void; // v2

// ui/tree.ts
export interface NamespaceNode {
  name: string;
  children: NamespaceNode[];
}

export declare function namespaceTree(names: readonly string[]): NamespaceNode; // rooted at "root"
export declare function ancestors(name: string): string[]; // v2: "root", then each dotted prefix; [] for root

// ui/theme.ts
export declare const DEFAULT_THEME: Readonly<Record<string, string>>; // Canvas's dark values
export const POLL_MS = 3_000;
export declare function applyTheme(theme: Readonly<Record<string, string>>, root: HTMLElement): void;

// ui/tabs/props.ts (v2: its own file, B7)
export interface TabProps {
  params: FrameParams;
  health: Health;
  rev: number;
  navigateTab: (tab: TabId, focus: string | null) => void;
  onBackendLost: OnBackendLost;
}

// ui/components/fields.tsx (props; Preact function components; v2: four files by role, B7)
export interface CodeFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  language: "yaml" | "python" | "text";
  errors?: readonly FieldError[];
  testId?: string;
  readOnly?: boolean; // v2
  /** v2: the id of errors shown elsewhere that describe this field (aria-describedby). */
  describedBy?: string;
}

export interface ValueEditorProps {
  label: string;
  value: unknown; // undefined starts empty
  mode: "yaml" | "text";
  onSave: (value: unknown) => void;
  onCancel: () => void;
  testId?: string; // v2
}

export interface FieldErrorsProps {
  errors?: readonly FieldError[];
  id?: string; // v2
  testId?: string; // v2
  /** v2: each error's location before its message. */
  located?: boolean;
}

export interface BannerProps {
  kind: "error" | "warning" | "info" | "success";
  testId?: string;
  children: ComponentChildren;
}

export interface ConfirmRowProps {
  sentence: string;
  confirm: string;
  onConfirm: () => void;
  onCancel: () => void;
}

// ui/components/pickers.tsx
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
  label?: string; // v2: the legend
  /** v2: each box is <prefix>-<namespace>, the list <prefix>-list; default "dr-namespaces". */
  testIdPrefix?: string;
}

// ui/components/notices.tsx
export interface SafetyNoticeProps {
  cap: string;
  variant: "first-open" | "banner";
  onUnderstood?: () => void;
}

export interface ProblemsBannerProps {
  rev: number;
  onBackendLost: OnBackendLost;
}

// ui/components/editor.tsx
export interface DecompositionEditorProps {
  record: DecompositionRecord | null; // null: Create decomposition
  namespaces: readonly NamespaceRecord[];
  params: FrameParams;
  health: Health;
  draftKey: string;
  onSaved: (record: DecompositionRecord, created: boolean) => void;
  onDeleted?: () => void; // v2
  navigateTab: TabProps["navigateTab"];
  onBackendLost: OnBackendLost; // v2
}

export interface CardListProps {
  cards: readonly Card[];
  /** D2's errors for each card, by index. */
  errors: readonly (readonly FieldError[])[];
  onChange: (cards: Card[]) => void;
}
```

(v2: in the code, `FieldErrors`, `Banner`, `ConfirmRow` and `ProblemsBanner` declare these props inline, without the
interface names used here.)

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


FIXTURE = Path(__file__).parent / "fixtures" / "library" / "main.yaml"  # v2: a directory, B10
BACKEND_ENV = ("PATH", "LANG", "TMPDIR")
SAFETY_ACK = "localStorage.setItem('dr-library.safety-acknowledged', '1')"  # v2


@pytest.fixture
def library_home(tmp_path: Path) -> Path:
    """A Library at tmp_path/home holding fixtures/library (imported, starter=False)."""


def serve(home: Path) -> LibraryServer:
    """v2: dr-library serve on a free port, environment PATH, LANG and TMPDIR only, cwd home;
    waits for /health. E8 uses it directly."""


def stop(server: LibraryServer) -> None:
    """v2: terminate, then kill after 10 s."""


@pytest.fixture
def library_server(library_home: Path) -> Iterator[LibraryServer]:
    """serve(library_home), stopped afterwards."""


# v2 (B11): module scope. While Playwright's sync API is started, its event loop counts as
# running in this thread, so asyncio.run (D1's harness) fails until it stops.
@pytest.fixture(scope="module")
def browser() -> Iterator[Browser]:
    """Chromium; skips with a reason when Playwright's browser is missing, fails when CI is set."""


def ui_url(
    base: str,
    **params: str | bool,
) -> str:
    """v2: base/ui/?<params>, True as "1", False left out."""


@pytest.fixture
def open_ui(
    browser: Browser,
    library_server: LibraryServer,
) -> Iterator[Callable[..., Page]]:
    """open_ui(tab="create", namespace="router", started=True, cap="5") → a page at /ui/?…, notice acknowledged
    unless notice=True is passed; each page in its own browser context, closed afterwards."""


def write_new(
    page: Page,
    name: str,
    task: str,
    code: str = "FinalAnswer(1)",
) -> None:
    """v2: in Create decomposition, the name, the task card and the step's code."""


@pytest.fixture
def parent_site(tmp_path: Path) -> Iterator[Callable[[dict[str, str]], str]]:
    """v2: parent_site({"name": content, ...}) serves the files from http://localhost:<port>/, another
    site than the frame's, as Canvas's page is; returns that origin."""


def stale_head(server: LibraryServer) -> None:
    """v2 (B1): a router.archive head that no longer validates, written to D2's store directly, since
    the Library refuses to write one."""
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

**v2 additions** (§3.2 B9; every id above is present and unchanged):

- **Both browsing tabs:** `dr-effective-failed` (the banner when D2 cannot resolve inheritance, B1).
- **Decompositions:** `dr-back` (from the editor to the list).
- **The editor:** `dr-name-errors`; `dr-card-<index>` (the card itself), `dr-card-<index>-role` (a raw card's role),
  `dr-card-<index>-errors`; `dr-edit-yaml`, `dr-yaml-error`; `dr-warnings`, `dr-cancel-save`; `dr-conflict` (the
  `EXISTS` or stale-save banner), `dr-rename`; `dr-attached-list`; `dr-confirm`, `dr-confirm-yes`, `dr-confirm-no`
  (any confirmation row, here Delete's).
- **Namespaces:** `dr-tree-<namespace>` (a node's list item), `dr-namespace-title`, `dr-default-badge`, `dr-message`
  (D2's refusal of the last write), `dr-new-namespace`, `dr-create-namespace`; the value editor's text
  `dr-value-<field>` (`dr-value-repl`, `dr-value-reasoner`, `dr-value-var-<key>`, `dr-value-system_suffix`,
  `dr-value-<setting>`, `dr-value-new-variable`, `dr-value-new-setting`) and its `dr-value-save`, `dr-value-cancel`,
  `dr-value-error`; a variable's actions `dr-override-var-<key>`, `dr-edit-var-<key>`, `dr-reset-var-<key>`;
  `dr-add-variable`, `dr-new-variable`; `dr-spawn-<namespace>`, `dr-spawn-list`; `dr-tool-source-<tool>`;
  `dr-suffix-<source>`; `dr-decomposition-<slug>`, `dr-attach-choice`, `dr-attach-confirm`; in Run settings,
  `dr-field-<key>` for each profile key, `dr-add-setting`, `dr-new-setting`.
- **Tools:** `dr-no-tools`.
- A `NamespaceChecklist` without a `testIdPrefix` uses `dr-namespaces-<namespace>` and `dr-namespaces-list` (no D3 view
  does).
