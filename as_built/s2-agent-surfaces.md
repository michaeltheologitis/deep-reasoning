# S2 · Agent commands, options and App panels in the agent-server, as built

**TASK-6** · Cartographer · revision 5, 2026-10-04 · the code at `d938c90`, head of `feat/agent-surfaces` in the SDK fork
[michaeltheologitis/software-agent-sdk](https://github.com/michaeltheologitis/software-agent-sdk), based on the fork's
`deep-reasoning`, `1f2b52d`; S2 is `git diff 1f2b52d..d938c90`: 38 commits and two merges of `deep-reasoning`; the
literate refactor is `5e3317f..7f03b56`, then two test-only commits, `76533fc` and `d938c90`. `d938c90`'s source is
`7f03b56`'s: only three test files differ [run: `git diff --stat 7f03b56 d938c90`] · D-1 to D-18 checked against the
design v2.3 (`09e1462`); D-19 against v2.4 (`1ef4f70`; v2.5, `008dd4b`, is now on this branch and takes D-19 in), read
only for its test names, counts and untested list · agent-client-protocol 0.12.1 and websockets 15.0.1 (the fork's
lock, unchanged since `1f2b52d`) · uv 0.12.23 and Python 3.13.14 in this sandbox.

**The PR stack.** Draft PRs #3 to #9 in the fork, each based on the one below, #3 on `deep-reasoning`; the top's head
`5e58984` has `d938c90`'s tree (`ce575e3`). PR #1, which carried S2 whole, is closed. [run: `git rev-parse
<commit>^{tree}`; CI: the fork's PR list]

**Revisions** (newest first).
- r5, code `d938c90`: the two test commits that close most of §5's gaps. Checked here: r4's thirteen probes rerun at
  `d938c90`, plus one (P2b); S2's cases counted again (116); CI green at `d938c90` (§6.1). Changed: the header and
  the PR stack, §1's size table, D-17, D-18, the new D-19, §3's set route, §4.9, §5, §6 and §7. Everything else is
  r4's, at `7f03b56`, whose source `d938c90` shares.
- r4, code `7f03b56`: the literate refactor, behaviour unchanged by its claim. Checked here: the OpenAPI export is
  byte-identical, 5e3317f's own tests pass on 7f03b56's source, and CI and the live tier are green at `7f03b56` (§6).
  Divergences are now counted from v2.3, which took in r3's D-1 to D-11 (§2.3); D-6 no longer holds (D-16). New:
  D-12 to D-18, and §5, what the refactor removed from the tests. Surface, line numbers, counts, proof and size are
  rewritten for `7f03b56`.
- r3, code `5e3317f`: the REST breakage check compared against `v1.50.1` in CI (run 37146974332, attempt 2).
- r2, code `5e3317f`; r1, code `6f97bf3`.

**Evidence marks.** Every claim carries one. **A claim marked [read] was read in the code and not executed.**
- **[run]**: executed in this sandbox, in my own worktree of the fork at `7f03b56` (r4) and at `d938c90` (r5), each
  detached and removed afterwards, never committing there. Among the runs: S2's tests and their neighbours; 5e3317f's
  tests against 7f03b56's source; the OpenAPI export at both commits; the mutation probes (§5), each one temporary edit
  to the code, reverted with `git checkout` before the next, the worktree checked clean after; each unit's net change
  applied alone onto the fork's `main` in a scratch clone.
- **[CI]**: read from GitHub through the GitHub MCP tools, full job logs downloaded through signed URLs: the fork's
  runs on PR #1 at `7f03b56` and at `d938c90`, and deep-reasoning's live run 37163413911.
- **[read]**: read in the code, not executed. §7 lists the ones that matter.

Nothing here ran a paid model, a live test or the `claude` CLI.

**Reading order.** §2 (divergences) and §5 (what the tests pin, and no longer pin) first; §1, §3 and §4 are the map
of the code for Gate C; §6 the proof, counts and size; §7 what I could not verify.

**Where this file lives.** On deep-reasoning's `as-built/s2-r2`, cut from `design/s2`, which holds only documents: no
`pyproject.toml`, no docs site, no test runner, so nothing collects `as_built/` and there is nothing to wire. [run:
`git ls-tree`]

---

## 1 · What exists

S2 is three upstream-shaped units in one branch. Nothing in them names deep_reasoner or dr-acp or reads `_meta`.
[run: grep of S2's added lines at `7f03b56`]

1. **ACP session controls.** The ACP bridge records each ACP session's slash commands and config options; the agent
   publishes the root session's as one persisted, latest-wins `ACPSessionControlsEvent`; a start request can carry
   option values (`acp_config_options`), applied after `session/new` and before the first prompt; a route sets an
   option on a live session or keeps it for the start; `POST /api/acp/preview` runs the real start-up in a throwaway
   state and answers what the agent would offer. The TypeScript client gains the matching calls and types.
2. **Conversation header panels.** A Canvas App manifest may declare `contributes.conversation_panels`; the
   agent-server validates them, returns them in the manifest it already serves, and serves each panel's icon.
3. **App backends on macOS.** `darwin-amd64` and `darwin-arm64` backend platforms; loopback traffic to an App backend
   bypasses HTTP proxies; a `macos-app-backend-tests` CI job.

```text
Canvas (C2)                     agent-server (acp_router.py, conversation_service.py)        SDK (acp_agent.py …)                dr-acp
POST /api/acp/preview ───────▶ _resolve_launch (shared with POST /api/conversations)
  start payload + values        RunSlot → to_thread(preview_acp_session) ──────────────▶ throwaway ConversationState
                                                                                         ACPAgent.init_state: new → model ──▶ session/new …
                                                                                         → acp_config_options → mode ──────▶ set_config_option
◀── ACPSessionControls ◀─────── safe_rmtree(preview-<hex>), release slot ◀───────────── wait ≤ 2 s for commands, session/close, close()
POST /api/conversations ─────▶ fold values into ACPAgent.acp_config_options ──────────▶ LocalConversation._ensure_agent_ready
                                                                                         wires agent._on_session_event
updates ──────────────────────────────────────────────────────────────── bridge.session_update ◀── available_commands_update,
                                                                         _record_session_controls     config_option_update
WebSocket / events search ◀── persisted ◀── LocalConversation._emit_event_from_any_thread ◀── ACPAgent._publish_session_controls
POST …/{id}/acp/config-options ─▶ EventService → LocalConversation.set_acp_config_option ─▶ ACPAgent.set_acp_config_option ─▶ set_config_option
```

[read; each path run by the tests of §6.2]

| Unit | S2's net change at `d938c90` (code / tests, lines added) | At `7f03b56` | At `5e3317f` |
|---|---|---|---|
| 1 · session controls | +3,447 −115 (1,299 / 2,148) | +3,433 −115 (1,299 / 2,134) | +3,839 −114 (1,371 / 2,468) |
| 2 · header panels | +533 −19 (218 / 315) | +523 −19 (218 / 305) | +593 −12 (234 / 359) |
| 3 · macOS | +363 −29 (104 / 259) | +363 −29 (104 / 259) | +405 −29 (109 / 296) |
| **All** | **+4,343 −163 in 47 files** (1,621 / 2,722) | +4,319 −163 in 47 files (1,621 / 2,698) | +4,837 −155 in 48 files (1,714 / 3,123) |

The units are split from the net diff hunk by hunk: each hunk of the four shared files (`manifest.py`,
`server_details_router.py`, `tests.yml`, the canvas tests' `conftest.py`) belongs to one unit, and at `5e3317f` the
manifest test file's 24-line backend-platform block is unit 3's. The split reproduces v2.3's 3,839, 593 and 405.
[run: a split script over `git diff -U3 1f2b52d..<commit>`, not committed] Each of the 20 refactor commits stays inside
one unit's files (unit 1: 11, unit 2: 6, unit 3: 3), but they sit on top of all 16 original commits, interleaved, so
the PR split regroups them. [run: `git diff --name-only` per commit] The `d938c90` column adds the three changed test
files to `7f03b56`'s split: the router's and the session-controls file's +4 and +10 are unit 1's, the manifest test
file's +10 (the malformed-panel table) unit 2's. [run: `git diff --numstat 1f2b52d..<commit>` of those files]

---

## 2 · Divergences from the design (v2.3; D-19 from v2.4)

The changelog has no entry for TASK-6, so no `drift:` line to carry [run: Notion query of the Changelog]. Every item
below was found from the code. v2.3 describes `5e3317f`; the refactor came after it.

### 2.1 What the refactor changed in the code's shape

None of these changes what a client or an agent sees; 5e3317f's tests pass on 7f03b56's source, and the OpenAPI
export is byte-identical (§6.1). [run]

**D-12 · The option-id refusal is one annotated type, and the start's fold no longer repeats it.** Design §4.4, A.3
and A.5: `ACPAgent` and `StartConversationRequest` each carry a `@field_validator` `_reject_model_config_option`, and
`_resolve_launch` repeats `_check_config_option_id` on the merged values because `model_copy` skips validators. Built:

```python
ACPConfigOptionValues = Annotated[
    dict[str, str | bool], AfterValidator(_check_config_option_ids)
]
```

(`acp_agent.py:609–617`) is the type of both fields (`acp_agent.py:1951`, `request.py:318`), and the fold
(`conversation_service.py:1945–1958`) checks nothing. Both halves of the merged dict were validated where they were
built, the request at parse time and the agent at construction [read], so on the routes' paths no `model` key reaches
the fold [run: probe P7, §5]. A value placed by `model_copy` is not checked: `ACPAgent(...).model_copy(update=
{"acp_config_options": {"model": "x"}})` succeeds [run: REPL]. `request.py` no longer imports the private
`_check_config_option_id`. Reason (`5236485`): "both dicts it merges were validated when their models were built, and
none of the copies before it changes acp_config_options."

**D-13 · Contribution ids are one annotated type, upstream's page validator included.** Design A.8: `_validate_id`
field validators on `CanvasExtensionPanelTab` and `CanvasExtensionConversationPanel`, calling
`_validate_contribution_id`. Built: `ContributionId = Annotated[str, AfterValidator(_validate_contribution_id)]`
(`manifest.py:54`) types the `id` of pages, tabs and panels (`:60, :80, :103`). Upstream's own
`CanvasExtensionPage._validate_id`, whose body `5e3317f` had already replaced, is now removed whole, so unit 2's
removed lines go from 12 to 19 (§1). The message ("Invalid contribution id. Expected kebab-case, got …") is
unchanged. [read; run: the manifest tests] Reason (`0e8421c`): "replaces the three identical id field validators".

**D-14 · The bridge stores both lists through one helper.** Not in A.3. `record_available_commands` and
`record_config_options` (`acp_agent.py:1529–1542`) parse, then call `_store_session_controls(session_id, field,
entries)` (`:1544–1553`), which dumps the session's snapshot, replaces the one list with the masked dumps of the new
entries and validates a new `ACPSessionControls`; the other list is rebuilt from its own dump rather than shared.
Snapshots are still replaced, never mutated. [read; run: the masking and per-session tests] Reason (`6907f85`): they
"repeated the same parse, mask, rebuild and replace steps for one field each".

**D-15 · `_is_loopback_host` is gone.** Design A.9 and B15: a helper beside `_LOOPBACK_HOSTS`. Built: both call sites
test `urlsplit(...).hostname` against `_LOOPBACK_HOSTS` themselves (`docker_runtime/proxy.py:146, 222`); a missing
host is `None`, not in the set, as before. [read; run: the bridge test] Reason (`46664eb`): it "wrapped a single set
membership".

Also, without a D-number: Appendix A says every block has "one field and one parameter per line"; the code now puts a
short signature or `Field(...)` on one line (`f8304e3`, `547dfe7`, `671979a`, `7f03b56`). Docstrings the design quotes
are shorter (`aa7bcdd`, `f29a3cc`): `ACPPreviewError` no longer lists the five codes (`acp_preview.py:30–35`),
`ACPConfigOptionRejectedError` drops "clients show it as it is" (`acp_agent.py:587–591`), and
`ACPAgent.set_acp_config_option` now says "Only the session changes; `acp_config_options` keeps its values"
(`:4780`). [read]

### 2.2 The PR split and the proof

**D-16 · PR 3 now applies to `main` without PR 2.** Design §1 (the v2 paragraph), B16 and §10 item 10: PR 3 conflicts
in `test_canvas_extensions_manifest.py` cherry-picked alone, so the split cuts it after PR 2. Built: `c4a246a` drops
unit 3's two manifest tests, and unit 3's net change no longer touches that file. Each unit's net change at `7f03b56`
applies alone onto the fork's `main` (`53a4bc5`) with no conflict, and the three stacked equal S2's tree except the
eight `runs-on` lines of the fork-only `ea51b3f`. [run: `git apply --index --3way` of each unit's hunks in a scratch
clone] The original commits do not: `759ffb2` cherry-picked alone onto `main` still conflicts in that file, since the
refactor commits sit on top of the original ones, not inside them. [run: the same clone]

**D-17 · Tests the design names that no longer exist.** The Gate B table "Which tests carry which property", §3.2 (B1,
B2, B12, B19), §4.10, §5.3 and §6.3 name 23 test functions that are gone, four that were merged into two renamed
ones, and three cases cut from the platform table's ten rows; S2's deterministic cases go from 146 to 116 and its
TypeScript tests from 8 to 7. (At `7f03b56` the malformed-panel test had also lost `[panel-title, no-tabs, tab-title]`,
and the count was 111; `d938c90` puts the three back.) §5 lists each with what still pins its property; §6.2 has the
counts by file. Among them, the property rows that lose a named test:

| v2.3's row | Its tests now |
|---|---|
| Falsifier 2 (the preview lists what the start lists) | `test_acp_preview.py::test_the_preview_equals_the_started_session_before_its_first_prompt[3]` and the router's `test_the_preview_answers_for_each_way_of_naming_the_agent[3]`; `test_resolve_launch_gives_the_start_and_the_preview_the_same_agent[3]` is gone (§5) |
| B2, the events search by the module-qualified kind | `test_the_events_search_returns_the_newest_controls_event` is gone; the router's `test_a_started_session_reports_the_chosen_value_and_cleared_commands` reads through the same query (§5) |
| B12, EPERM on macOS only | the two tests are one, `test_a_refusal_to_signal_the_group_means_it_exited_on_macos_only[probe, signal]` |
| Decision E, the model stays with `switch_acp_model` | `ACPAgent`'s set call is asserted again, inside `test_the_model_option_and_an_empty_id_are_refused_in_the_field_and_by_a_live_set` (`76533fc`); `LocalConversation`'s set-call test and `test_the_preview_refuses_the_model_option` are gone (§5) |

**D-18 · Size.** v2.3's Gate B "one thing to rule on" and B19 give 4,837 lines added at `5e3317f` (1,714 code and CI,
3,123 tests). Built: 4,319 at `7f03b56` (1,621 and 2,698), and 4,343 at `d938c90` (1,621 and 2,722; the two test
commits add +33 −9); non-blank added, 4,023 → 3,618 → 3,642. The task row's `Lines After` is 4,319, `7f03b56`'s.
[run: `git diff --numstat`; read: the task row]

**D-19 · v2.4 describes `7f03b56`'s tests, not `d938c90`'s.** v2.4's refactor section ("What no test asserts any
more", "Not pinned by any test", the property tables), §4.5's v2.4 note and §4.10/§5.3's file tables, read at
`d938c90`:
- They name `test_a_set_that_is_not_for_this_route_is_a_bad_request[not-acp, model-option]` and
  `test_the_model_option_and_an_empty_id_are_refused_in_the_field[model, '']`. Built:
  `test_a_set_that_is_not_for_this_route_is_refused[not-acp, model-option, empty-id]` and
  `test_the_model_option_and_an_empty_id_are_refused_in_the_field_and_by_a_live_set`, whose two cases pytest ids by
  value: `[model-The 'model' option is set with switch_acp_model]` and `[-config_id must be a non-empty string]`.
- They count 111 cases (PR 1 68, PR 2 29), the router 27 and the manifest additions 16. Built: 116 (69, 33), 28 and 20.
- They list as unasserted `ACPAgent.set_acp_config_option`'s refusals, the route's `min_length=1`, and, as gone, the
  `panel-title`, `no-tabs` and `tab-title` cases and the tab's default path. Each is asserted at `d938c90` (§5).
  `LocalConversation`'s refusal of `""` is still unasserted, as v2.4 says.
- *(Conductor, on cherry-picking r5 onto `design/s2`: v2.5 (`008dd4b`) takes each point in; its case ids now
  name the two cases by value.)*

[read: v2.4 at `1ef4f70`; run: collection and probes at `d938c90`] Reason: `76533fc` and `d938c90` came after v2.4.

### 2.3 r3's divergences, as v2.3 holds them

v2.x took in every divergence r3 named, and each still holds at `7f03b56` as v2.3 states it [read; run: the tests in
§6.2 except where §5 says a test is gone]:

| r3 | v2.3 | At `7f03b56` |
|---|---|---|
| D-1 · the events search matches only the module-qualified kind | B2, §7 item 4 | holds; its named test is gone (D-17) |
| D-2 · an empty first controls event after every start and resume | B4, §10 item 14 (ruled: no change) | holds; still pinned by no test |
| D-3 · the preview answers 501 in the Docker runtime | B3 | holds |
| D-4 · ACP's schema drops unusable entries before S2's code | B1 | holds |
| D-5 · one draft PR into `deep-reasoning`; upstream's main-only guards run on it | B18, B25 | holds (§6.1) |
| D-6 · unit 3 conflicts cherry-picked onto `main` alone | B16, §10 item 10 | **no longer holds** (D-16) |
| D-7 · built in the order 1, 2, 3 | B16 | holds |
| D-8 · one REST-check allowlist alternative | B14 | holds (`check_agent_server_rest_api_breakage.py:644–647`) |
| D-9 · four status rows untested at `6f97bf3` | B24 | holds: all four still have their tests |
| D-10 · the dr-acp live tier at S2's own head | §10 item 12 | holds (run 37163413911 at `7f03b56`) |
| D-11 · every 5xx `detail` is "Internal Server Error" | B26 | holds |

---

## 3 · The public surface, from the code at `7f03b56` (= `d938c90`'s)

**REST.** Every 5xx answer's body is `{"detail": "Internal Server Error", "exception": …}` (D-11); "reason" below means
`detail` for a 4xx and `exception` for a 5xx. [run: the router tests, except where marked]

| Route | Body | Answer | Statuses |
|---|---|---|---|
| `POST /api/acp/preview` (`acp_router.py:60–113`) | the start payload (`StartConversationRequest`), its `acp_config_options` applied | `ACPSessionControls` | 400 not an ACP agent · 404 unknown profile · 422 invalid request, values for a non-ACP agent, a dangling MCP reference, or a value the agent refused (reason: its sentence) · 422 for a `model` or empty key [run: REPL, the request model refuses both; read: FastAPI's 422; no test, §5] · 429 run limit · 501 Docker runtime · 502 any other start failure (e.g. `502: [-32000] Authentication required`) · 504 start-up timeout |
| `POST /api/conversations/{id}/acp/config-options` (`acp_router.py:116–157`) | `{"config_id": str (min 1), "value": str \| bool}` | `{"applied": bool, "controls": ACPSessionControls}`: live → `true` and the agent's controls; before the start → `false` and empty controls | 400 not ACP, `model`, inactive service · 404 unknown conversation · 422 refused (reason verbatim) · 422 an empty `config_id` [run: `test_a_set_that_is_not_for_this_route_is_refused[empty-id]`, P8] · 504 no answer in 30 s · 500 the agent's -32603 (reason: its message, unmasked) |
| `POST /api/conversations` | gains `acp_config_options: {id: str \| bool}` | unchanged | 422 with a non-ACP agent or a `model` key |
| `GET /api/conversations/{id}/events/search?kind=openhands.sdk.event.acp_session_controls.ACPSessionControlsEvent&sort_order=TIMESTAMP_DESC&limit=1` | — | the newest controls event, `null` fields left out | — |
| `GET /api/canvas-extensions/installed/{name}/panels/{panel_id}/icon` (`canvas_extensions_router.py:459–490`) | — | the icon file, `image/svg+xml` or `image/png`, with `Cache-Control: no-cache`, `X-Content-Type-Options: nosniff`, `Content-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; sandbox` | 404 unknown App, unknown panel, no icon, or an icon no longer contained (re-checked per request) |
| `GET /server_info` | — | `capabilities` gains `acp_session_controls_v1` (`server_details_router.py:70`) and `canvas_conversation_panels_v1` (`:141`) | — |

Both ACP routers are registered at `api.py:457–458`; the start route's `except` gains `InvalidACPConfigOptions`
(`conversation_router.py:285`). [read]

**The event and its DTOs.** `openhands/sdk/agent/acp_models.py:80–238`: `ACPCommandInput(hint)`,
`ACPAvailableCommand(name, description, input)` with `from_protocol` (`None` without a name), `ACPConfigOptionValue(value,
name, description, group)`, `ACPConfigOption(id, name, type: "select" | "boolean", current_value: str | bool,
description, category, options)` with `from_protocol`, and `ACPSessionControls(available_commands, config_options)`
with `parse_commands` and `parse_config_options`. `openhands/sdk/event/acp_session_controls.py`:
`ACPSessionControlsEvent(available_commands, config_options)`, `source` `"agent"`, `from_controls`, `.controls`, a
one-line `visualize`; exported from `openhands.sdk.event` (`__init__.py:33`); the default visualizer names it "ACP
Session Controls" (`visualizer/default.py:211–214`). [read; run: tests]

**SDK** (`openhands/sdk/agent/acp_agent.py` unless named).
- `ACPConfigOptionValues` (`:615–617`, D-12), the type of `ACPAgent.acp_config_options` (`:1951–1959`) and of
  `StartConversationRequest.acp_config_options` (`request.py:318–325`); it refuses `""` and `"model"`.
- `ACPConfigOptionRejectedError(config_id, value, message)` (`:587–596`), a `ValueError` whose `str()` is the agent's
  message, masked; `_classify_acp_init_error` returns `"ACPConfigOptionRejected"` for it first (`:1305–1306`).
- `ACPAgent`: `session_controls` (`:2421–2427`), `set_acp_config_option(config_id, value) -> ACPSessionControls`
  (`:4775–4813`), `wait_for_available_commands(timeout)` (`:4815–4819`), `close_acp_session(timeout=2.0)`
  (`:4821–4832`). `ACP_CONFIG_OPTION_TIMEOUT` (environment, default 30 s, `:184–188`) bounds one set.
- `LocalConversation.set_acp_config_option(config_id, value) -> ACPSessionControls | None`
  (`local_conversation.py:1795–1830`).
- `openhands.sdk.conversation.acp_preview`: `preview_acp_session(agent, workspace, persistence_dir, *, secrets=None,
  cipher=None, commands_wait_seconds=2.0)`, `ACPPreviewError(code, detail)`, `PREVIEW_COMMANDS_WAIT_SECONDS = 2.0`.
  [read; run: tests]

**Manifest** (`canvas_extensions/manifest.py`). `contributes.conversation_panels: [{id, title, icon?, tabs: [{id,
title, path="/"}]}]` (`:77–154`): ids kebab-case (`ContributionId`) and unique across pages, panels and tabs of one App
(`:156–166`); titles non-empty; at least one tab; a tab path `/` or an absolute kebab-case path, unique within its
panel; an icon a package-relative `.svg` or `.png`, refused if absolute or with `..`, and at install and on every serve
refused unless it resolves (symlinks followed) to a regular `.svg`/`.png` inside the package (`resolve_package_file`
`:340–358`, `resolve_panel_icon` `:361–378`). An empty list is left out of every dump. `BackendPlatform` adds
`darwin-amd64`, `darwin-arm64` (`:185`). [read; run: tests, and §5's probes P9 to P13]

**TypeScript client** (`clients/typescript`, version 1.50.1). Unchanged by the refactor [run: `git diff --stat
5e3317f 7f03b56`]: `src/models/acp-session-controls.ts` (the DTOs, `ACPConfigOptionValues`, the set request and
response, `ACP_SESSION_CONTROLS_EVENT_KIND`); `ACPSessionControlsEvent` in the `ConversationEvent` union with
`isACPSessionControlsEvent` and the unexported helper `acpSessionControlsOf` (`src/events/types.ts:257–279`);
`ConversationClient.previewAcpSession`, `setAcpConfigOption`, `getAcpSessionControls`
(`conversation-client.ts:398–433`); `RemoteConversation.setAcpConfigOption`, `getAcpSessionControls`
(`remote-conversation.ts:343–366`); `CreateConversationPayload.acp_config_options?`. [read; CI: 354 tests]

---

## 4 · Structure and seams

### 4.1 Recording and publishing (where the complexity sits)

**The bridge records per session id.** `_OpenHandsACPBridge.session_update` calls `_record_session_controls` right after
the idle-clock reset (`acp_agent.py:1598`); it consumes `AvailableCommandsUpdate` and `ConfigOptionUpdate` for any
session id and returns before any other routing (`:1564–1572`). The `configOptions` of `session/new` (`:3475–3477`),
`session/load` (`:3434–3436`) and every `session/set_config_option` (S2's at `:644`; the model path's through the
`on_config_options` argument passed at `:3490, :3520, :4723–4727`) are recorded too. A record parses, then
`_store_session_controls` masks the new list with the conversation's masker and replaces the session's snapshot
(D-14); `record_available_commands` also sets the session's `threading.Event`, which `wait_for_available_commands`
waits on; then `_notify_session_controls_changed` calls the publisher and logs, never raises, a failure
(`:1574–1581`). [read; run: the masking, per-session and protocol-drop tests]

**The agent publishes the root's.** `_launch_acp_session` creates the bridge and calls `_bind_session_controls`
(`:3109–3113`), which points the bridge at a weak reference to the agent (`:4834–4848`). `_publish_session_controls`
(`:4850–4866`) returns unless `_on_session_event` and `_session_id` are set and no start is in progress; under
`_session_controls_lock` it reads the root's snapshot, returns if it equals the last one submitted, and otherwise
submits a new event. `_start_acp_server` sets `_starting_session` around `_launch_acp_session` and publishes once after
it (`:3095–3107`), so every start persists one event, possibly before the agent's menu (D-2). [read; run:
`test_nothing_is_published_while_a_session_is_starting`, `test_concurrent_publishes_keep_snapshot_order_and_end_on_the_newest`]

**The emitter.** `LocalConversation._ensure_agent_ready` sets `agent._on_session_event =
self._emit_event_from_any_thread` for an `ACPAgent` before `init_state` (`local_conversation.py:1577–1578`).
`_emit_event_from_any_thread` (`:1863–1872`) submits upstream's `_on_event_with_state_lock` to a one-worker executor
created in `__init__` (`:320–324`); after `close()` shuts it down (`:2897–2898`) a submit is dropped with a debug log.
Events persist and reach every callback in submission order, and submission order is snapshot order. [read; run: the
three emitter tests of `test_local_conversation_acp_config_option.py`]

**The agent swap.** `switch_acp_model` (`:1781`) and `set_acp_config_option` (`:1821–1829`) go through
`_replace_acp_agent(update, live=)` (`:1832–1861`): a shallow `model_copy`; when live, the copy takes over atexit
cleanup, file-credential masking and the bridge's publish callback, and the old agent's runtime is released. [read;
run: `test_the_agent_swap_hands_publishing_to_the_copy`]

### 4.2 Option values

At the start, in `_init`'s fresh-session branch only: `new_session` → record its options → the model call → 
`_apply_config_options` (`acp_agent.py:3498–3506`) → the existing `set_session_mode`. After a successful
`session/load` only the response's options are recorded; a failed load falls through to the fresh branch, which
applies everything. `_apply_config_options` (`:620–644`) sets each value in dict order and records every response;
-32603 is re-raised unchanged, any other `ACPRequestError` becomes `ACPConfigOptionRejectedError` with the masked
message. At the start that error leaves `init_state` through its existing handler: a `ConversationErrorEvent` with
code `ACPConfigOptionRejected`, status `ERROR`, no prompt sent. [read; run:
`test_start_values_reach_the_agent_after_session_new_and_before_the_prompt`,
`test_a_refused_start_value_ends_the_start_and_no_prompt_is_sent`, the load and fallback tests]

A set: `LocalConversation.set_acp_config_option` (`local_conversation.py:1795–1830`) refuses a non-ACP agent and
calls `_check_config_option_id`, then under the state lock calls the agent if the session is live (a refusal
propagates before anything is written) and in every case swaps in an agent whose `acp_config_options` holds the
value, so `base_state.json` persists it. `ACPAgent.set_acp_config_option` checks the id again, needs a live session,
and runs one `_apply_config_options` on the portal within `_ACP_CONFIG_OPTION_TIMEOUT`, read at call time (`:4796`).
`EventService.set_acp_config_option` (`event_service.py:2028–2041`) runs it in the default executor and raises
`ValueError("inactive_service")` without a conversation. [read; run: the set tests]

### 4.3 The preview

`ConversationService.preview_acp_session` (`conversation_service.py:1961–1994`): `_resolve_launch(request)`; a non-ACP
agent → `ValueError("preview needs an ACP agent")`; a run slot (`RunSlot.acquire`); in a thread, the SDK's
`preview_acp_session` with `persistence_dir = conversations_dir / f"preview-{uuid4().hex}"`; `safe_rmtree` in a
`finally`. The SDK function (`acp_preview.py:43–94`) creates the directory, uses an empty `persistence_dir/workspace`
when the working directory does not exist, seeds the secret registry from the agent context and then the request,
runs `agent.init_state` under the state's lock (any failure → `ACPPreviewError(_classify_acp_init_error(e),
_acp_error_detail(e, registry))`), waits at most 2 s for the root's first commands, sends `session/close` if the agent
advertised it, and closes the agent in a `finally`. No plugins and no per-conversation file-credential bindings are
loaded. [read; run: `test_acp_preview.py`, the router's preview tests, which also check that no `preview-*` directory
is left]

### 4.4 The agent-server's shared launch

`_resolve_launch` (`conversation_service.py:1847–1959`) is the block `_create_conversation` used to hold (settings,
profile resolution and its secret allow-list, `load_memory`, ACP skill sourcing, the system-message suffix), plus the
fold (`:1945–1958`): values with a non-ACP agent → `InvalidACPConfigOptions`; otherwise `agent.model_copy(update=
{"acp_config_options": {**agent's, **request's}})`, with no id check (D-12). `_create_conversation` calls it first
(`:1667`) and leaves `acp_config_options` out of the stored record (`:1769–1773`), so the values live only inside the
agent in `base_state.json`. [read; run: `test_the_start_folds_option_values_into_the_agent_only`]

### 4.5 Panels

Validation sits in the manifest models (§3). The install check calls `resolve_panel_icon` for every panel beside the
entrypoint's (`installed.py:62–63`); `get_canvas_extension_panel_icon_path` re-resolves the icon per request against
the live install and answers `None` on any failure (`installed.py:254–269`); the route maps `None` to 404 and takes
the media type from the resolved file's suffix (`canvas_extensions_router.py:459–490`; the path type and headers at
`:61–75`). The icon is served whether the App is enabled or not, with the session key like every route. [read; run:
the router and containment tests]

### 4.6 macOS

`current_platform()` (`backend.py:161–172`) maps `platform.system()` and `platform.machine().lower()` through two tables
(`:42–51`) to the four names, else `None`. The health probe opens through `_LOOPBACK_OPENER` (`ProxyHandler({})`,
`:52–56`, used at `:431`); `proxy_http` builds its `httpx.AsyncClient` with `trust_env=False` and `bridge_websocket`
passes `proxy=None` when the target host is in `_LOOPBACK_HOSTS` (`docker_runtime/proxy.py:77–79, 146, 222`); other
targets keep `trust_env=True` and `proxy=True`. `_signal_group` and `_group_alive` (`backend.py:574–588`) treat ESRCH as
gone everywhere and EPERM as gone on Darwin only (`_group_exited`, `:110–120`). [read; run: the platform table,
dead-proxy, bridge and EPERM tests on Linux; CI: the macOS job, §6.1]

### 4.7 What it relies on

- **agent-client-protocol 0.12.1**: its schema drops unusable list entries instead of failing the update [run: the
  protocol-drop test]; `ClientSideConnection.close_session` exists [run: tests]; a notification sent before a response
  is recorded before the awaiting call resumes [read: `acp/connection.py:152–164`; not stressed].
- **The agent's order**: a preview shows a chosen value's commands only if the agent sends them before its
  `set_config_option` response, as dr-acp and the scripted agent do. [read]
- **websockets 15.0.1** (`proxy` parameter) [run, r1]; pydantic's `exclude_if` and `AfterValidator` [run: tests];
  upstream's `RunSlot`, its 429 handler and `_on_event_with_state_lock` [run: test; read].

### 4.8 Who consumes S2

- **S1** (`feat/acp-subagent-sessions`, pushed head `a3279be`: 10 commits and two merges on `5e3317f`; draft PR #2
  based on `feat/agent-surfaces`). It is not rebased onto `7f03b56`; merged with it, git reports no textual conflict [run: `git
  merge-tree --write-tree 7f03b56 a3279be`]. None of S1's own added lines uses a name the refactor removed or reshaped
  (`_is_loopback_host`, `_reject_model_config_option`, `bridged_agent`, `Started`, the per-file `conversation`
  fixtures) [run: grep of `git diff 5e3317f a3279be`]. Whether S1's tests pass on the merge is S1's to show; I ran none.
  S1 sets `client.on_session_event = self._on_session_event`, so its child-session events use S2's emitter, and keeps
  S2's recording line first in `session_update` [read, r3].
- **C2** (Canvas fork, `db3b4b9`, read only at r3) uses the TypeScript client's calls and constant, both capability
  strings, `manifest.contributes.conversation_panels`, the icon route with the session key, and the
  `ACPConfigOptionRejected` code. Nothing C2 uses changed in the refactor (the client source and the OpenAPI are
  unchanged). [read; run: the two diffs]
- **D1's dr-acp** receives `session/set_config_option(namespace, …)` after `session/new` and before the first prompt,
  and its menu and option updates are recorded; S2 relies on dr-acp sending a new namespace's menu before the set's
  response, and on its clearing the menu at the first prompt (the live tier asserts both outcomes, §6.4). [read; CI]

### 4.9 Wiring

`.github/workflows/tests.yml`: S2's live file joins upstream's `acp-live-tests` job (its change filter and pytest line,
`:161, :194`), and `macos-app-backend-tests` (`:330–369`) runs `tests/agent_server/canvas_extensions` on `macos-latest`
when the canvas, proxy, lock or workflow files change. The endpoint audit lists the two new routes as client-ahead. The
dr-acp live job is deep-reasoning's `fork-live.yml` on `ci/fork-live` (`a8154e2`), a `workflow_dispatch` taking
`sdk_ref` and `suites`. None of this changed in the refactor. [read; run: `git diff --stat 5e3317f 7f03b56 -- .github`]
S2 reaches review as the draft stack #3 to #9 (above the revisions); PR #1 is closed. I read the stack's bases, heads
and top tree, not its descriptions or its per-level CI. [run; CI: the PR list]

---

## 5 · What the refactor removed from test coverage, and what came back

The refactor removes 40 of S2's 146 deterministic test cases at `5e3317f` and adds 5 (the merged EPERM test's two and
the folded icon-404 table's three): 111 remain at `7f03b56`. `76533fc` adds one case and `d938c90` four: 116. In
TypeScript, 8 tests become 7. [run: `pytest --collect-only` at the three commits, compared; read: the TypeScript
files] The refactor's commit messages give a reason for each removal (`0d21d58`, `44dd4f4`, `c4a246a`, `920b0e3`,
`9e92cb2`, `79e77d0`, `1118139`): another test pins the property, or the property is pydantic's or upstream's.

The two test commits [read; run: collection]:
- `76533fc`: the field test becomes `test_the_model_option_and_an_empty_id_are_refused_in_the_field_and_by_a_live_set`,
  which also calls `ACPAgent.set_acp_config_option` on a started scripted session and matches each refusal by its
  sentence; the router's refusal table becomes `test_a_set_that_is_not_for_this_route_is_refused[not-acp,
  model-option, empty-id]`, expecting 400, 400 and 422.
- `d938c90`: `test_a_malformed_panel_makes_the_manifest_invalid` gains `panel-title`, `no-tabs`, `tab-title` and
  `duplicate-default-tab-path` (a tab at `/` beside a tab with no path, which collide only because the default is `/`).

To check "another test pins it" where reading could not settle it, I made the mutation the removed test would have
caught and ran the tests against it, at `7f03b56` (r4) and at `d938c90` (r5); the source lines are the same at both
[run: one temporary edit each, reverted; P1–P8 and P2b against unit 1's deterministic test files (68 cases at
`7f03b56`, 69 at `d938c90`), P9–P13 against all of `tests/agent_server/canvas_extensions` and the canvas router,
upstream's tests included (207, 211); unmutated, every case passes]:

| Probe: the code made to… | Tests that fail at `7f03b56` | at `d938c90` |
|---|---|---|
| P1 · skip the id check in `ACPAgent.set_acp_config_option` (`acp_agent.py:4788`) | **none** | both cases of `…_refused_in_the_field_and_by_a_live_set` |
| P2 · skip it in `LocalConversation.set_acp_config_option` (`local_conversation.py:1814`) | `test_acp_router.py::…_is_a_bad_request[model-option]` | the same case, `…_is_refused[model-option]` |
| P2b · skip it there for `""` only (r5) | not run | **none** |
| P3 · skip both | the router case | the router case and both field-test cases |
| P4 · accept an empty id in `_check_config_option_id` (`acp_agent.py:601`) | the field test's `""` case | the field test's `""` case (its field half fails first) |
| P5 · refuse -32603 like any other error in `_apply_config_options` (`:641`) | `test_an_internal_error_from_the_agent_is_a_500_carrying_its_message_unmasked` | the same |
| P6 · publish an unchanged snapshot again (`:4863`) | `test_each_session_keeps_its_own_controls_and_only_the_root_is_published`, `test_concurrent_publishes_keep_snapshot_order_and_end_on_the_newest` | the same two |
| P7 · type `StartConversationRequest.acp_config_options` as a plain dict (`request.py:318`) | `test_the_start_refuses_option_values_it_cannot_apply[model-option]` | the same |
| P8 · drop `min_length=1` from the set request's `config_id` (`acp_router.py:39`) | **none** | `…_is_refused[empty-id]` (400, not 422) |
| P9 · default a tab's path to `/home` instead of `/` (`manifest.py:85`) | **none** | `[duplicate-default-tab-path]` |
| P10 · allow an empty panel title (`:105`) | **none** | `[panel-title]` |
| P11 · allow a panel with no tabs (`:112`) | **none** | `[no-tabs]` |
| P12 · allow an empty tab title (`:83`) | **none** | `[tab-title]` |
| P13 · drop the darwin keys from `BackendPlatform` (`:185`) | 11 backend tests, upstream's lifecycle tests among them | the same 11 |

P1 is caught by the sentence, not by the exception's type: without the check the scripted agent refuses `"model"` and
`""` itself (`ACPConfigOptionRejectedError: unknown option 'model'`, also a `ValueError`), and the test fails on "Regex
pattern did not match". The conversation's check (P2) is still what the route's `model` case reaches, request
validation (P7) is the start's only `model` guard now that the fold has none (D-12), and the concurrency test pins
"no repeat" (P6), as `0d21d58` says. [run]

Removed, and the property still pinned elsewhere [read unless a probe above says run]:

- The command and option parsing of `test_acp_models.py` (a command without input, nameless commands dropped in order,
  a boolean option): `test_entries_the_protocol_cannot_parse_are_dropped_not_raised` parses all three through the
  bridge.
- A refusal's sentence and attributes (`test_a_refusal_raises_with_the_agents_own_sentence`): the router's 422
  verbatim, and `test_a_live_set_is_persisted_and_survives_a_reload` now asserts `config_id` and `value`.
- A non-ACP conversation refused: the router's `test_a_set_that_is_not_for_this_route_is_refused[not-acp]`.
- The preview's refused value (SDK level): the router's `[refused-value]` case asserts 422 and the sentence.
- The events search by the module-qualified kind: the router's cleared-commands test reads the newest event through
  that query and would time out on a kind that matched nothing; that the search returns the newest of several events
  is asserted only as "the newest is the narrowed one".
- A manifest with panels dumped: the router's list-and-get test compares the panel in full. A page at `/`: upstream's
  `test_invalid_page_path_rejected["/"]`.
- Darwin keys accepted (`test_macos_backend_artifacts_are_accepted`): every backend lifecycle test's artifact declares
  them [run: P13].
- A contained icon resolves and an unknown panel answers `None`: the router's icon tests, end to end.
- Three platform-table rows (`Linux/arm64`, `FreeBSD`, `Darwin/ppc`): each mapping entry and each unknown branch keeps
  a row. The two EPERM tests: one test asserts both sides.
- The TypeScript client's empty page: `acpSessionControlsOf([])` in the helper's own test.

**Pinned again at `d938c90`** (r4's items 1, 9 and 10, and the bound in item 2) [run: the probes named]:

- `ACPAgent.set_acp_config_option` refusing `""` and `"model"` (r4 item 1): both cases of
  `test_the_model_option_and_an_empty_id_are_refused_in_the_field_and_by_a_live_set`, which pytest ids by value,
  `[model-The 'model' option is set with switch_acp_model]` and `[-config_id must be a non-empty string]` (P1).
- The set route's `min_length=1` (r4 item 2): `test_a_set_that_is_not_for_this_route_is_refused[empty-id]` (P8).
- A tab's `path` defaulting to `/` (r4 item 9): `[duplicate-default-tab-path]` (P9).
- A non-empty panel title, at least one tab and a non-empty tab title (r4 item 10): `[panel-title]`, `[no-tabs]`,
  `[tab-title]` (P10–P12).

**Pinned by no test at `d938c90`** (each held at `5e3317f` by the test named; r4's numbers kept):

2. `LocalConversation.set_acp_config_option` refusing `""` (`test_the_model_option_and_an_empty_id_are_refused['']`).
   At the route `min_length=1` answers first, with 422, and no test calls the conversation with `""`: skipping its
   check for `""` alone fails nothing [run: P2b]. The shared `_check_config_option_id`'s `""` branch is pinned by the
   field test alone [run: P4]. The conversation's `model` refusal is pinned through the router [run: P2].
3. The set's `TimeoutError` naming the option, raised within the bound
   (`test_a_silent_agent_times_out_within_the_config_option_timeout`): the router's 504 test asserts the status only.
   [read]
4. A preview spawn failure classified `ACPSpawnError` (`test_an_agent_that_cannot_be_spawned_raises_a_spawn_error`):
   the router's `[spawn-error]` case asserts 502, which every code but the two mapped ones gets; the classification
   is upstream's. [read]
5. The preview refusing a `model` key (`test_the_preview_refuses_the_model_option`): the preview takes the same
   request model, whose refusal the start's test pins (P7). [run: REPL, r4, the model refuses it; read: the route]
6. The start and the preview resolving the same agent for each way of naming it
   (`test_resolve_launch_gives_the_start_and_the_preview_the_same_agent[agent, agent_settings, agent_profile_id]`):
   the router checks each naming's preview answer, and a start with values only for `agent` and `agent_settings`;
   nothing compares a start with a preview. Both go through `_resolve_launch`. [read] This was one of falsifier 2's
   three agent-server tests (D-17).
7. A prompt's controls events persisted in order through a conversation, first the chosen menu, then only cleared
   ones (`test_changes_during_a_prompt_are_published_in_order`): the router asserts the final newest event; the order
   is pinned underneath by the emitter and concurrency tests. [read]
8. The resume transcript skipping the event (`test_resume_transcript_skips_session_controls`): upstream's
   `render_resume_transcript` renders only `MessageEvent`, `ACPToolCallEvent` and `ActionEvent`
   (`event/resume_transcript.py:258`). [read]
11. An unknown backend platform refused (`test_an_unknown_backend_platform_is_still_refused`): the `Literal` alone;
    no upstream test names another platform either. [read: grep of the tests, r4]

The refactor's commit messages say so for 4, 8 and 11 (upstream's or pydantic's) and for 6 (a private method). For 2,
3 and 5, `0d21d58` says the property "is asserted by a test that remains"; the remaining tests assert a neighbouring
property (the route's status, the start route's refusal), not that one. `76533fc` and `d938c90` name the gaps they
close as ones that left the suite green when mutated. [read]

---

## 6 · Proof, counts and size

### 6.1 The runs at `d938c90` and `7f03b56`

| Run | Conditions | Result |
|---|---|---|
| fork `Run tests` [37167747319](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37167747319), at `d938c90` | `pull_request` (PR #1, before it closed); ubuntu-24.04, Python 3.13 | **attempt 1**, all 11 jobs green: `agent-server-tests` 2,417 passed (`7f03b56`'s 2,412 and the 5 new cases); sdk 6,683 passed, 7 skipped, 12 xfailed (the field test's two cases renamed, none added); `macos-app-backend-tests` (macos-latest) 168 passed (164 and the 4 manifest cases) [CI: job logs] |
| fork, the other workflows at `d938c90` | REST API breakage 37167747311, persisted settings 37167747354, TypeScript client CI 37167747326, its integration tests 37167747316, version bump guard 37167747328, pre-commit 37167747337, docstrings 37167747406, deprecation deadlines 37167747313, endpoint audit 37167747322 | all succeeded; the PR description check skipped. Statuses only; logs not opened [CI] |
| this sandbox at `d938c90`, S2's files and neighbours | r4's set and command (below) | **463 passed**, 8 deselected (the live file), 138.6 s: `7f03b56`'s 458 and the 5 new cases [run] |
| this sandbox at `d938c90`, the probe sets unmutated | unit 1's six deterministic files; `tests/agent_server/canvas_extensions` and the canvas router | **69** and **211 passed** [run] |
| fork `Run tests` [37161720972](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37161720972), at `7f03b56` | `pull_request` into `deep-reasoning`; ubuntu-24.04, Python 3.13 | **attempt 1**: `agent-server-tests` failed 1, passed 2,411: upstream's `tests/agent_server/telemetry/test_telemetry_sink.py::test_emit_never_awaits_even_when_the_exporter_hangs`, "emit() blocked for 0.557s" against a 0.05 s bound; S2 touches no telemetry file [run: `git log`]. **attempt 2** re-ran that job only: 2,412 passed. The rest, attempt 1: sdk 6,683 passed, 7 skipped, 12 xfailed · cross 496 passed, 1 skipped · `macos-app-backend-tests` (macos-latest) 164 passed · `acp-live-tests` 25 passed, 2 skipped (the six provider previews passed; the two dr-acp tests skip without an agent command) · tools, workspace, stress, windows, test-directory allowlist and coverage green [CI] |
| fork, upstream's main-only guards on PR #1 at `7f03b56` | REST API breakage 37161721016, persisted settings 37161720978, TypeScript client CI 37161720995, its integration tests 37161721026, version bump guard 37161720984 | all green. REST: fetched `v1.50.1`, oasdiff 1.19.1, the same eight changes as at `5e3317f` (`ACPSessionControlsEvent` in two `oneOf` lists, the two darwin keys in three manifest responses), all accepted, exit 0. Persisted settings: 17 fixtures and 8 PyPI-1.50.1 payloads validated. TypeScript: lint 0 errors and 7 warnings, 23 files and **354 tests**. Version bump guard: "No package version changes detected", so the SDK API breakage check did not run [CI] |
| fork, other checks on PR #1 at `7f03b56` | pre-commit 37161720999, docstrings 37161721012, deprecation deadlines 37161721001, endpoint audit 37161720973 | green; "Validate PR description" skipped (draft); 28 check runs in all [CI] |
| deep-reasoning `fork-live` [37163413911](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37163413911) | SDK checkout `7f03b56`, deep-reasoning `ci/fork-live` `a8154e2`; Python 3.12.3; `OPENAI_API_KEY`; S2's step only (S1's skipped); `dr-acp --config docs/configs/advising/main.yaml`, `{"namespace": "root"}`, `OPENHANDS_ACP_LIVE_EXPECT_COMMANDS_CLEARED=1` | S2's live file: **8 passed** in 96.6 s, 3 warnings (§6.4) [CI] |
| this sandbox at `7f03b56`, S2's files and neighbours | serial, `--basetemp` outside `/tmp`: `tests/agent_server/canvas_extensions`, the ACP and canvas routers, `test_openapi_contract.py`, all of `test_conversation_service.py`, the cross breakage tests, S2's SDK files | **458 passed**, 8 deselected (the live file), 222.8 s [run] |
| this sandbox, 5e3317f's tests on 7f03b56's source | the same set, with `tests/` checked out from `5e3317f` | **493 passed**, 8 deselected: r3's count for this set [run] |
| this sandbox, the OpenAPI export | `export_agent_server_openapi.py` at `5e3317f` and twice at `7f03b56` | **byte-identical** (1,033,556 bytes, sha256 `3ea3ab51…`); `check_agent_server_openapi_quality.py` passes, 62 allowlisted weak locations [run] |
| this sandbox, each unit alone on `main` | §1's split of the net diff, `git apply --3way` onto `53a4bc5` | all three apply; stacked, they equal S2 but for `ea51b3f`'s eight `runs-on` lines (D-16) [run] |

CI's counts move with the refactor exactly: the agent-server job loses 19 cases (2,431 → 2,412), sdk 16 (6,699 →
6,683), macOS 14 (178 → 164), TypeScript 1 (355 → 354), the removals of §5; and with the two test commits, agent-server
+5 and macOS +4. [CI; run: the collected ids] The live tier did not run at `d938c90`; its newest run is the one above,
at `7f03b56`, whose source and live file `d938c90` shares. [CI: the `fork-live` run list; run: `git diff --stat`]

Reproduce: `OPENHANDS_SUPPRESS_BANNER=1 uvx uv@latest run --frozen python -m pytest -o addopts="" -m "not stress and
not acp_live" --basetemp=<outside /tmp> <the files above>`; the live tier by dispatching `fork-live.yml` with
`sdk_ref` and `suites: s2`.

### 6.2 S2's tests, measured

Cases after parametrization, deterministic (the live file's 8 apart) [run: collection at `1f2b52d`, `5e3317f`,
`7f03b56` and `d938c90`; no upstream case is lost at any]:

| File | `5e3317f` | `7f03b56` | `d938c90` |
|---|---|---|---|
| **Unit 1** | **89** | **68** | **69** |
| `tests/sdk/agent/test_acp_models.py` | 7 | 4 | 4 |
| `tests/sdk/event/test_acp_session_controls_event.py` | 4 | 3 | 3 |
| `tests/sdk/agent/test_acp_session_controls.py` | 25 | 18 | 18 |
| `tests/sdk/conversation/local/test_local_conversation_acp_config_option.py` | 10 | 7 | 7 |
| `tests/sdk/conversation/test_acp_preview.py` | 11 | 9 | 9 |
| `tests/agent_server/test_acp_router.py` | 29 | 27 | 28 |
| `tests/agent_server/test_conversation_service.py` (S2's additions) | 3 | 0 | 0 |
| **Unit 2** | **36** | **29** | **33** |
| `…/canvas_extensions/test_canvas_extensions_manifest.py` (unit 2's) | 22 | 16 | 20 |
| `…/canvas_extensions/test_canvas_extensions_entrypoint_containment.py` | 5 | 4 | 4 |
| `tests/agent_server/test_canvas_extensions_router.py` | 8 | 8 | 8 |
| `tests/agent_server/test_openapi_contract.py` | 1 | 1 | 1 |
| **Unit 3** | **21** | **14** | **14** |
| `…/canvas_extensions/test_canvas_extension_backend.py` | 17 | 12 | 12 |
| `…/canvas_extensions/test_canvas_extension_bridge.py` | 1 | 1 | 1 |
| `…/test_canvas_extensions_manifest.py` (unit 3's) | 2 | 0 | 0 |
| `tests/cross/test_check_agent_server_rest_api_breakage.py` | 1 | 1 | 1 |
| **All** | **146** | **111** | **116** |

Plus the 8 live cases (unchanged) and TypeScript 7: `api-clients.test.ts` 4, `event-types.test.ts` 2, `index.test.ts`
1 [read]. `tests/conftest.py` now holds the shared helpers `scripted_conversation` (a fixture that also resumes a
persisted conversation by id), `controls_events` and `wait_until`, beside `scripted_acp_command` and
`acp_request_log`; the scripted agent (`tests/fixtures/acp/scripted_agent.py`, 310 lines) is unchanged. [read]

### 6.3 Size, before and after

| Part | `5e3317f` (added / removed) | `7f03b56` | `d938c90` |
|---|---|---|---|
| SDK | 818 / 27 | 757 / 28 | 757 / 28 |
| agent-server | 647 / 112 | 615 / 119 | 615 / 119 |
| TypeScript client | 200 / 1 | 200 / 1 | 200 / 1 |
| CI (`tests.yml`, the REST check) | 49 / 3 | 49 / 3 | 49 / 3 |
| **Code and CI** | **1,714** | **1,621** | **1,621** |
| Python tests | 2,658 / 11 | 2,242 / 11 | 2,266 / 11 |
| The scripted ACP agent | 310 | 310 | 310 |
| TypeScript tests | 155 / 1 | 146 / 1 | 146 / 1 |
| **Tests** | **3,123** | **2,698** | **2,722** |
| **All** | **4,837 / 155** | **4,319 / 163** | **4,343 / 163** |

The Refactorer's figures (source 1,714 → 1,621, tests 3,123 → 2,698) hold. [run: `git diff --numstat 1f2b52d..<commit>`]
The refactor itself is `git diff 5e3317f..7f03b56`: +262 −788 in 28 files, in 20 commits, each touching source or
tests, never both: four change the source's structure (`5236485`, `0e8421c`, `6907f85`, `46664eb`; source +45 −88),
two reformat it (`f8304e3`, `547dfe7`; +29 −82), two reword docstrings (`aa7bcdd`, `f29a3cc`; +11 −16), and twelve
change tests only (+182 −607, of which `0d21d58` alone removes 216). The per-commit sums exceed the net diff by five
lines each way, lines touched twice. [run: `git diff --numstat` per commit]

### 6.4 The live tier and E11

`test_acp_session_controls_live.py` at `7f03b56`, run 37163413911 [CI]:

| Test | Result |
|---|---|
| `test_a_built_in_provider_can_be_previewed[claude-code, codex, gemini-cli, kimi-code, pi, opencode]` | 6 passed, 12–19 s each by log timestamps. Commands / options: claude-code 40 / `mode, model, effort, fast`; codex 17 / `mode, collaboration_mode, model, reasoning_effort, fast-mode`; gemini-cli 20 / none; kimi-code 15 / `model, thinking, mode`; pi 8 / `model, thought_level`; opencode 3 / `model, mode`, the same as r3's runs. The fork's own `acp-live-tests` job shows the same six. |
| `test_the_preview_lists_what_the_started_session_lists` (dr-acp, `namespace=root`) | passed, about 4 s |
| `test_the_first_prompt_runs_with_the_chosen_values` (dr-acp; the reported namespace is `root`, the last controls event after the prompt lists no commands) | passed, about 5 s |

The three warnings are `PytestUnraisableExceptionWarning`s ("Event loop is closed", a subprocess transport collected
after its loop closed) in the codex, opencode and pi previews; no assertion depends on them. No run prints its model
spend.

E11's S2 claims stand as r3 measured them: the preview lists the namespace's commands and equals the started session
(scripted agent, three value sets [run]; dr-acp with one value [CI]); a refused value fails the start in the agent's
words [run]; the commands are cleared by the first prompt (scripted [run], dr-acp [CI]); App backends start on macOS
and Linux [CI, run]. "Changing the namespace changes the menu" is still shown with the scripted agent only; the live
tier sets one value.

---

## 7 · What I could not verify

1. **The SDK API breakage check** ran nowhere at `7f03b56`: CI skips it without a version change, and I did not run it.
   At `d938c90` I read only the version bump guard's status (green), not its log. The REST comparison is CI's (oasdiff
   is not set up here).
2. **macOS** is CI's: the job passed 164 at `7f03b56` and 168 at `d938c90`; Intel (`darwin-amd64`) is never run.
3. **Each unit's tests on its own tree.** I applied each unit alone onto `main` (D-16) but did not run any unit's
   tests there.
4. **S1 on `7f03b56`**: a textual merge only; no S1 test ran.
5. **C2** is read from its code at `db3b4b9` (r3); nothing of C2 ran.
6. **The live tier's namespace coverage**: one value, so it cannot show a menu that changes with the namespace, nor
   which commands `root` offers; and its cost is not printed.
7. **Ordering inside ACP Python** (§4.7) is read, not stressed.
8. **The design v2.4** (`1ef4f70`) is read only for D-19 (its test names, counts and untested list); D-1 to D-18
   are from v2.3 and were not checked again against v2.4.
9. **The live tier at `d938c90`** did not run: the newest `fork-live` run is 37163413911, at `7f03b56`. The source
   and the live file are unchanged between the two [run: `git diff --stat`].
10. **The PR stack** (#3 to #9): its bases, heads and top tree only; not its descriptions, nor each level's CI.

If this document resists shortening, the part that resists is §5: the refactor's removals are many and small, and
each needs its own "still pinned by" to be checked rather than trusted.
