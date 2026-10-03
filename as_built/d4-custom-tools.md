# D4 · Custom tools and MCP servers, as built

**TASK-9** · Cartographer · the code at `965f318` (head of `v1-custom-tools`: D4's 14 commits on D3's
`5effe26`, itself on D2 and D1; this file is on `as-built/d4`) · checked against the design at
`0be057d` (`docs/design/d4-custom-tools.md` v1, identical to `e14fda7` on `design/d4`) ·
deep_reasoner_beta `d7334ae` · `mcp` 1.30.0 (locked) · agent-client-protocol 0.12.1 · SDK fork
`91430aa` (read only) · 2026-10-03.

D4's code is `src/deep_reasoning/tools/`, `src/deep_reasoning/mcp/`, the Tools tab in D3's
`canvas-app/` and its rebuilt files, and `tests/tools/`, `tests/mcp/`, plus edits in D1's, D2's and
D3's files (§5). D1's, D2's and D3's code is described only where D4 meets it.

**Evidence marks.** Every claim carries one.
- **[run]**: executed in this sandbox on the code at `965f318`. That covers the deterministic suite
  (`CI=true DR_BETA_CHECKOUT=<clone of deep_reasoner_beta at d7334ae> uv run pytest`: §6.1), the
  browser tier (`CI=true uv run pytest -m browser tests/canvas_app` with the preinstalled Chromium),
  `npx vitest run`, `npx tsc --noEmit`, `npm run build` compared with the committed files, and
  uncommitted probe scripts that call `check_tool`, the App backend through Starlette's
  `TestClient`, and the shim. The original deep_reasoner_beta checkout was not touched.
- **[CI]**: read from GitHub's logs of CI run 37106223937 and live run 37106223637, both at `965f318`.
  I did not run a paid model or a real `claude` CLI.
- **[read]**: read in the code and **not executed**. This is weaker evidence than [run]; §7 lists the
  read claims that matter most.

**Reading order.** Start with §2 (the divergences). Then §1 and §3–§5 are the map, §6 gives E9 and
the live tier as measured, and §7 says what I could not verify.

---

## 1 · What exists

D4 adds two things to the Library and to `dr-acp`. A **tool of your own** is a D2 tool row (a block
and a Python source). **Check** builds it in a throwaway process, and the App backend runs Check
again before it saves a changed tool. An **MCP grant** is also a D2 tool row: its block snapshots a
server's non-secret settings from Canvas's MCP settings, and its source is D4's **shim**. In a
conversation, `dr-acp`'s worker connects the granted servers before deep_reasoner builds its tools,
and the shim's factory hands each one over. Under plain `dr` (an export), the same shim connects by
itself. [read; each path run end to end by the tests in §6]

```text
Tools tab (frame) ─ POST ../tools/{n}/check ─▶ routes.check ─ check_tool ─┬ static stage: invalid · syntax · builtin · bad_factory   (no process)
                                                                         └ check_child: own process group, no secrets, model at 127.0.0.1:9
                  ─ PUT ../tools/{n} ───────▶ D2 put_tool ─ require_check ─ check_tool ─▶ 422 check_failed | Library.put_tool
                  ─ PUT ../mcp/{n} ─────────▶ routes.put_grant ─ mcp_block + shim_source() ─▶ Library.put_tool  (a tool row)
                  ─ GET ../mcp ─────────────▶ grant_record + read_seen($DR_HOME/mcp/<sha256[:16]>.json)
page (Canvas's realm), Tools tab only: GET /api/settings + the deep_reasoner profile ─▶ frame URL ?mcp=[…]  (names, never values)

dr-acp front:  session/new keeps mcpServers ─ first prompt: materialize ─ specs_for_run ─▶ Start.mcp_servers (control pipe)
worker:        load_dr_config ─ open_session: connect every granted, reachable server at once ─ emit mcp.status
               ─ shim.SESSION = {alias: Func} ─ build_reasoner ─ make_tools ─ shim.mcp_server() returns SESSION[alias]
front pump:    mcp.status ─▶ events.jsonl ─▶ Encoder: one root notice per server not bound; remember_seen ─▶ $DR_HOME/mcp/
plain dr:      make_tools ─ shim.mcp_server() with SESSION None ─ Connection from the block, values from os.environ
```

| Part | Lines | Where |
|---|---|---|
| Check and the routes | 684 | `src/deep_reasoning/tools/` (`check.py` 386, `check_child.py` 128, `texts.py` 91, `routes.py` 77) |
| MCP | 983 | `src/deep_reasoning/mcp/` (`shim.py` 539, `session.py` 181, `wire.py` 163, `grants.py` 98) |
| edits to D1's files | +101 −7 | `acp/agent.py`, `encoder.py`, `runlog.py`, `session.py`, `supervisor.py`, `texts.py`, `worker/protocol.py`, `worker/runner.py` |
| edits to D2's `api.py` | +65 −42 | most of it the route helper renamed (§5) |
| the frame (D3's project) | +1,475 −30 | `canvas-app/src/`, `vite.config.ts`, `package.json` |
| built files | `app.js` 168,759 B, `editor.js` 348,475 B (new), page bundle 8,364 B | `src/deep_reasoning/canvas_app/` |
| tests | +3,617 −7 Python (539 of them a frozen copy of the shim), +433 vitest | `tests/tools/`, `tests/mcp/`, `tests/canvas_app/test_tools_tab.py`, `canvas-app/tests/` |

[run: `wc -l`, `git diff --numstat 5effe26..965f318`]

The length sits in `shim.py` (the connection, the REPL objects, the description and the guard,
§4.6), `check.py` (the supervisor, §4.1) and the frame's `ToolEditor.tsx` (361 lines, §4.8). [read]

---

## 2 · Divergences from the design (`0be057d`)

No changelog entry carries a `drift:` line for TASK-9, so every divergence below was found from the
code. Each row gives what the design says, what is built, where, and the reason the code or its
commit message gives ("none recorded" when neither does).

### 2.1 Behaviour a user, D3, D5 or a reviewer sees

| # | Design | Built | Where | Reason |
|---|---|---|---|---|
| 1 | The editor chunk `assets/editor.js` is at most 300 KB minified; `app.js` stays under 250 KB (§7.4). | `editor.js` is **348,475 bytes** (117,254 gzipped). `app.js` is 168,759 bytes. A fresh build is byte-identical to the committed files. [run: `vite build` into a scratch folder, `diff -r`; CI: "editor.js 348.48 kB │ gzip: 117.55 kB"] | `src/deep_reasoning/canvas_app/ui/assets/editor.js`; the chunk rule `canvas-app/vite.config.ts:17-18` | The overrun has none recorded. Commit `93110f3` states the size. `editor/python.ts:62` leaves out `python()`'s autocompletion "and its size (§7.4's budget)". |
| 2 | One shared deadline for every server: now plus the largest `connect_timeout_s` (§4.4, §8.2). | Each server waits until one shared start plus **its own** `connect_timeout_s`. The two rules agree when every grant has the same timeout, which is always the case through the panel: the panel never writes a timeout, so every grant gets the default 10 s. [read; CI: `test_servers_connect_at_once_and_a_silent_one_is_given_up_at_the_deadline`, three 1.5 s servers decided in under 3 s] | `mcp/session.py:154, 175` | Commit `0bd1611`: "at once against one start" |
| 3 | `open_session`: "a failure inside it is caught per server and never fails the build" (§11.1). | A server's own failure is caught inside its connection (`shim.py:221-226`). `open_session` has no handler of its own. A raise while resolving namespaces (`session.py:63-72`), opening `runs/<run>/mcp-<alias>.log` (`session.py:106`) or rendering a binding ends the build as D1's `build_failed` (`runner.py:152, 166-170`). [read] | `mcp/session.py`, `acp/worker/runner.py:152-154` | none recorded |
| 4 | The stand-in: "calling it, or any attribute of it, raises `McpToolError`" (§4.3). | An attribute whose name starts with `_` raises `AttributeError`. Every other attribute, and a call, raises `McpToolError`. [run: `stand.value.search` → `McpToolError`; `stand.value._private`, `__cross_namespace__` → `AttributeError`] | `mcp/shim.py:384-389` | Code comment: Python's and deep_reasoner's own lookups (`__cross_namespace__`, `__wrapped__`, inspect's) "must find nothing, as on any plain object". Pinned by `test_a_stand_in_is_plain_to_deep_reasoners_seams`. |
| 5 | A server that dies mid-run: "the call in flight fails (`McpError: Connection closed`)", and every later call raises `SERVER_STOPPED` (§4.5). | The call in flight also raises `SERVER_STOPPED`, with `McpError: Connection closed` as its detail. If the connection's own task notices the end first (`shim.py:223-225`), it marks the connection dead too. [CI: `test_a_server_that_crashes_mid_run_fails_the_call_and_the_run_goes_on` asserts the same `McpToolError` sentence for both calls] | `mcp/shim.py:265-270` | none recorded |
| 6 | Under plain `dr`, `; not set in the environment: {names}` is added to `COULD_NOT_START` (§9.2). | It is added to `NO_ANSWER` too. [run: a silent server with an unset variable: "…did not answer within 2 s when the conversation started; not set in the environment: D4_PROBE_UNSET."] | `mcp/shim.py:512-513` | none recorded |
| 7 | A first tick whose REPL name another tool has gets 409 (§2.2). `MCP_VIA_GRANT` reads "'{name}' is an MCP server's grant: change it in the MCP servers list" (§3.2 item 3, §9.1). | The 409 is D2's `CONFLICT_EXISTS`, so it comes only with `base_version: 0`. **`PUT /mcp/{name}` sent with the head's version replaces a user's own tool with a grant.** [run: own tool `word_count` v1, then `PUT /mcp/word_count` with `base_version: 1` → 200; the row became an MCP grant at v2.] **`PUT /tools/{name}` replaces a grant with an own tool.** `require_check` refuses only a body whose block is `mcp_server`, not a write over a grant's row. [run: `PUT /tools/github` over the grant → 200, factory `make`.] The panel's first tick sends `base_version: 0`, so through the panel the 409 holds. [CI: `test_canvas_mcp_servers_are_listed_and_granted_per_namespace`] | `tools/routes.py:50-71`, `tools/check.py:374-386` | none recorded |
| 8 | A tool's row shows `make · tools/word_count.py`, or `built-in rag` for a block without a source (§2.1). | D3's text is kept: `factory make · tools/word_count.py` and `factory rag`. | `canvas-app/src/ui/tabs/tools.tsx:48-54` | D3's function and D3's test (`test_the_tools_tab_lists_tools_with_their_grants`) are unchanged |
| 9 | **Save anyway** is offered on the report of a refused save (`CheckResultProps.saving`, A.6). The editor's header carries `· saved <date>` (§2.1). | `CheckResult` has no `saving` prop. **Save anyway** shows under any report whose `can_save_anyway` is true, so it also appears after a plain Check. The header is `Tools › <name> v<n>`, with no date. | `canvas-app/src/ui/components/CheckResult.tsx:13-17, 57-69`; `ToolEditor.tsx:213-216, 272` | none recorded |

### 2.2 Signatures and structure

| # | Design | Built | Where | Reason |
|---|---|---|---|---|
| 10 | D3's `CodeField` with `language: "python"` loads the editor chunk (§7.4, §11.3). | A new `PythonField` loads the chunk with `import()`. If the load fails it falls back to D3's `CodeField` textarea. D3's `CodeField` is unchanged. | `canvas-app/src/ui/components/python.tsx:18-66` | none recorded |
| 11 | `PythonEditor { setValue, destroy }` (A.6). | `{ destroy }` only. A reset (Discard draft, Reload, after a save) remounts the field under a new key. | `editor/python.ts:22-24, 73`; `ToolEditor.tsx:99, 115-120, 237` | Commit `200e820`: feeding the editor its own text back "replaced the document mid-keystroke; a reset remounts it" |
| 12 | `@codemirror/lang-python` through its language support (§7.4's list). | `new LanguageSupport(pythonLanguage)` instead of `python()`, plus `lineNumbers`, `historyKeymap` and a four-space `indentUnit`. | `canvas-app/src/ui/editor/python.ts:55-66` | Code comment: `python()` would bring autocompletion and its size |
| 13 | `ToolCheckFailed(report)` (A.1). | `ToolCheckFailed(name, report)`; the message is `CHECK_FAILED` with the name. | `tools/check.py:351` | none recorded (`CHECK_FAILED` takes the name) |
| 14 | `Connection(spec, *, errlog, call_timeout_s)` (A.3). | It also takes `name=None`: the REPL name its sentences use. `spec.name` stays the server's name in Canvas's settings. | `mcp/shim.py:144-153` | none recorded |
| 15 | Only D2's route helper moves to module level, as `json_route` (§11.2). | `tools/routes.py` also imports D2's private `_parse`. | `tools/routes.py:10` | none recorded |
| 16 | The constants of A.1–A.3. | Added constants: `CALL_GRACE_S` 5 s past a call's own timeout; an HTTP client with a 30 s timeout and a 300 s read timeout; `REQUEST_TIMEOUT` 408 and `CONNECTION_CLOSED` −32000 (the `McpError` codes); `MISSING_ENV`; and in `session.py`, `LOG_TAIL` 300, `PRINTED`, `GRANTED_NOWHERE` and `OUT_OF_REACH`. | `mcp/shim.py:33-40, 56, 197-205`; `mcp/session.py:27-30` | code comments |
| 17 | `CHILD_ENDED`'s phases: `starting` and `building the tool` (§9.1). | It adds a third phase, `trying it`, for a child that ends while it evaluates the tried expression. | `tools/check.py:238` | none recorded |
| 18 | The guard exits "with the command's exit code" (§4.6). | A server ended by signal N exits with 128 + N. | `mcp/shim.py:535` | none recorded |
| 19 | The props and helpers of A.6. | `ToolEditorProps` has no `takenNames` and gains `onBackendLost`. `McpServerRowProps` gains `onBackendLost`. `tools.ts` adds `RESERVED_NAMES`, `grantSnapshot` and `McpSnapshot`. `toolDraftKey` returns `tool.<name>`; D3's `drafts.ts` adds the `dr-library.draft.` prefix, so the stored key is the design's. | `ToolEditor.tsx:44-51`, `McpServerRow.tsx:33-40`, `tools.ts:9-16, 89-100, 162-165` | none recorded |

### 2.3 Dependencies, tests and size

| # | Design | Built | Where | Reason |
|---|---|---|---|---|
| 20 | Verified against `mcp` 1.28.1, the SDK fork's lock (header, M1, M2). | `uv.lock` resolves **`mcp` 1.30.0**, and every MCP test ran on it. [read] In 1.30.0, `stdio_client` still starts the server with `start_new_session=True` and merges the same six inherited variables (`HOME`, `LOGNAME`, `PATH`, `SHELL`, `TERM`, `USER`). | `uv.lock:1331-1333`; `.venv/…/mcp/client/stdio/__init__.py:28-45, 256` | Commit `cd3e153`: "the lock resolves 1.30.0" |
| 21 | §10.2's fixtures include `syntax.py`; the agreement test runs "every fixture". | The syntax case is an inline string (`SYNTAX_ERROR`). Two fixtures are added: `exits.py` (`os._exit(3)` in the factory) and `calls_model.py`. The agreement test has 8 cases: works, `not_func`, misspelled, `import_error`, `hang`, `env_at_build`, `prints` and `exits`. It does not cover `spawns`. | `tests/tools/test_check.py:38, 204-235`; `tests/tools/fixtures/` | none recorded |
| 22 | `library_home`'s fixture gains a tool whose factory raises (§10.4). | `tests/canvas_app/conftest.py` is unchanged. The test types `env_at_build.py` into the editor itself. | `tests/canvas_app/test_tools_tab.py:230-246` | none recorded |
| 23 | "A frozen copy of v1 in `fixtures/`" (§10.3). | `tests/mcp/fixtures/shim_v1.py` is **byte-identical** to today's `shim.py` [run: `diff`]. For now, `test_a_stored_v1_shim_works_with_todays_session` exercises the same text. It pins that a stored file, loaded through `load_tool_factory`, reads the package's `SESSION`. | `tests/mcp/fixtures/shim_v1.py` | none recorded |
| 24 | §10's test list. | Every test that §10.2–§10.4 names exists. Thirteen more pin behaviour the design states but does not list: `test_a_name_d2_refuses_is_invalid_in_d2s_words`, `test_an_mcp_grant_is_not_checked_as_a_tool_of_your_own`, `test_a_tool_that_ends_the_process_is_raised_saying_how_it_ended`, `test_a_check_that_cannot_start_deep_reasoner_in_time_is_unavailable`, `test_put_mcp_refuses_a_name_the_repl_cannot_bind[3]`, `test_mcp_block_needs_a_command_or_a_url[4]`, `test_the_shim_source_starts_with_its_marker_and_version`, `test_grant_record_reads_the_block`, `test_without_mcp_blocks_the_session_is_empty`, `test_a_stand_in_is_plain_to_deep_reasoners_seams`, `test_a_server_it_cannot_reach_becomes_a_stand_in_saying_why[2]`, `test_a_server_that_dies_fails_the_call_and_every_later_one_at_once` and `test_a_hand_off_outside_the_grant_is_refused`. [run: `pytest --collect-only`] | `tests/tools/`, `tests/mcp/` | — |
| 25 | About 1.98k lines of code and 2.19k of tests; D1's edits about 90 lines (§13, §11.1). | About **3.3k lines of code**: 1,667 in `tools/` and `mcp/`, 101 in D1's files, 65 in D2's and 1,475 in the frame. About **4.05k lines of tests**: 3,617 Python (539 of them the frozen shim) and 433 vitest. [run] | §1 | §4.1, §4.6 and the frame hold most of the length |

---

## 3 · The public surface, from the code

### 3.1 HTTP (the App backend)

D4's routes are appended after D3's `/ui/` routes, behind D2's guard, which checks the same user,
`Host` and JSON. [read: `library/api.py:396`; CI: `test_mcp_routes_answer_only_their_own_host`]

```text
POST /tools/{name}/check  {"yaml", "source"?, "example"?}          200 CheckReport, always
PUT  /tools/{name}        D2's body + "accept_check_failure"?      D2's answers, and 422 {"error": "check_failed", "message", "check": CheckReport}
                                                                   or 400 MCP_VIA_GRANT before any save
GET  /mcp                                                          200 [McpGrant], in GET /tools order
PUT  /mcp/{name}          {"server", "transport", "command"?, "args"?, "url"?, "env"?, "headers"?, "granted_in", "base_version"}
                                                                   201 | 200 McpGrant; 400 no command or URL, or a bad body;
                                                                   409 conflict (D2's) | refused (MCP_SERVER_TAKEN); 422 invalid
```

[read: `tools/routes.py`, `library/api.py:288-296`; CI: `tests/tools/test_routes.py`, 21 cases]

What I ran against `create_app` [run]:
- `PUT /tools/run_all` answers **422 `check_failed`** with `check.outcome: "invalid"`, not D2's
  `422 invalid`. The reserved names are Check's rule, not D2's.
- A `PUT /mcp/…` body without `base_version` answers 400 with D2's `BAD_REQUEST` sentence, "The body
  must be a JSON object with a 'yaml' string. Field required". That sentence names `yaml`, which the
  MCP body does not have.
- Resending a grant unchanged answers 200 and keeps version 1.

### 3.2 Python

- `deep_reasoning.tools.check`:
  - `check_tool(name, yaml_text, source, *, example=None, limits=DEFAULT_LIMITS) -> CheckReport`;
  - `require_check(library, name, yaml_text, source, *, accept_failure)`;
  - `ToolCheckFailed`, `check_env(base)` and `tool_name_errors(name)`;
  - `CheckLimits(ready_s=30, build_s=10, example_s=10)` and `RESERVED_NAMES`.

  `CheckReport` has A.1's eleven fields, and `Outcome` has A.1's ten values. [read]
- `python -m deep_reasoning.tools.check_child --report-fd N --name NAME [--example EXPR] MAIN`. [read]
- `deep_reasoning.mcp.shim`, which is a module and also every grant's `factory_from` file:
  - the factory `mcp_server(client, params)`;
  - `McpToolError`, `SESSION`, `Connection`, `Server`, `McpTool` and `Unavailable`;
  - `python -I shim.py --guard -- COMMAND ARGS…`.

  Its first line is `# deep-reasoning MCP shim, version 1. …`. [read; CI:
  `test_the_shim_imports_only_the_standard_library_at_module_level`]
- `deep_reasoning.mcp.session.open_session(cfg, specs, *, run_dir) -> list[McpServerStatus]`. [read]
- `deep_reasoning.mcp.wire`, which `dr-acp`'s front imports (pydantic and yaml only):
  - `McpServerSpec`, `McpServerStatus` and `McpSeen`;
  - `forwarded_specs`, `servers_named` and `specs_for_run`;
  - `redact`, `remember_seen` and `read_seen`.
- `deep_reasoning.mcp.grants`, the backend's side: `McpGrantBody`, `McpGrant`, `shim_source`,
  `is_mcp_tool`, `header_env_name`, `mcp_block` and `grant_record`. [read]

### 3.3 `dr-acp`

- `initialize` advertises `mcpCapabilities: {"http": true, "sse": true}`. [CI:
  `test_dr_acp_advertises_http_and_sse`; D1's 18 golden recordings changed on that line only]
- The run log has one new event, `mcp.status {servers: [McpServerStatus]}`. It is logged before
  `build_reasoner` and only when the run's config has an MCP block.
- The encoder turns it into one root `agent_message_chunk` per server whose state is `no_answer`,
  `failed` or `not_enabled`, in both modes and on replay. The three sentences are §9.2's, verbatim.

[read: `acp/runlog.py:138-143`, `acp/encoder.py:356-366`, `acp/texts.py:143-173`; CI:
`test_the_notice_replays_on_load`]

### 3.4 The Tools tab

The tab shows, in this order:
- D3's safety banner;
- the risk line `TOOLS_RISK`;
- **Your tools**: the list with **+ New tool**, or an editor in its place, with a back link;
- **MCP servers (from Canvas's settings)**: one row per server;
- `MCP_EXPORT_NOTE`.

Every test id in Appendix B exists. [run: a `grep` of `canvas-app/src` for each id] Every sentence in §9.1–§9.3 is in the
code verbatim [run: a script that splits each sentence of the design's §9 tables at its
placeholders and finds every fragment in `tools/texts.py`, `acp/texts.py`, `mcp/shim.py` or
`ui/texts.ts`]. The frame takes one new parameter, `mcp`: a JSON list of `McpServerInfo`. Entries of
another shape are dropped, and an unreadable value is `null`. [read: `shared/protocol.ts:154-183`;
CI: `protocol.test.ts`]

---

## 4 · Structure and seams

### 4.1 Check: `tools/check.py` and `tools/check_child.py`

**The static stage** runs in the backend and starts no process. Its steps, in order: D2's
`shapes.validate_tool` (`invalid`, D2's message); `RESERVED_NAMES` (`invalid`); an `mcp_server` block
(`invalid`, `MCP_VIA_GRANT`); a block without a source (`builtin` if its factory is `llm` or a key of
deep_reasoner's `TOOL_BUILDERS`, else `bad_factory` in `make_tools`' words); then `compile(source,
"tools/<name>.py")` (`syntax`). [read: `check.py:325-344`; CI: each with a `no_process` fixture that
fails the test if `Popen` is called]

**The child.** `_build_in_a_child` writes a one-tool config into `mkdtemp(prefix="dr-check-")` (0700):
- `config/main.yaml`, holding a client at `http://127.0.0.1:9/v1` with no retries and the canonical
  block;
- `config/tools/<name>.py`, the source byte for byte.

It starts `sys.executable -m deep_reasoning.tools.check_child` with:
- the config folder as its working directory;
- `check_env` (the six variables `PATH`, `LANG`, `LC_ALL`, `LC_CTYPE`, `TMPDIR` and `TZ`; `HOME`,
  `USER` and `LOGNAME` from the password database; the two `PYTHON*` flags; nothing else);
- stdin `/dev/null`, stdout and stderr to `printed.txt`;
- a pipe fd for its report;
- a new session.

[read: `check.py:264-305`; CI: `test_check_gets_no_secret`, `test_check_never_reaches_a_model`
(a factory that calls `client.chat.completions.create` gets `APIConnectionError`, and a fake model
on another port records no request)]

The child mirrors `make_tools`' `factory_from` branch. It reports JSON lines on the pipe: `ready`
(after importing deep_reasoner), `loaded`, then `built` (with `told`, deep_reasoner's
`func(name, value, description).describe()`) or `failed`, then `example` and `done`. It classifies a
`load_tool_factory` `ValueError` by its `__cause__`:
- an `ImportError` → `import_failed`;
- any other cause → `raised`;
- no cause → `bad_factory`.

An exception from the factory is `raised`, with the traceback's frames in `tools/<name>.py`. A
non-`Func` result is `not_func` in `make_tools`' sentence. [read: `check_child.py:41-81`; CI:
`test_not_func_and_unknown_factory_sentences_equal_make_tools`, a tripwire on deep_reasoner's inline
text]

**The supervisor** is where the subtlety is. A daemon thread reads the pipe into a queue
(`_Reports`), so each phase can be awaited with a deadline:
- `ready` within 30 s, else `unavailable`;
- `built` or `failed` within 10 s more, else `timeout`;
- `example` within 10 s more, else the example's own `TimeoutError` while the build stays ✓.

A pipe that closes early is `CHILD_ENDED` (`unavailable` before `ready`, `raised` after). On every
path, `_end` sends `SIGKILL` to the child's process group **before** reaping the child. The report
carries the last 2,000 characters of `printed.txt`, and the folder is removed in a `finally`.
[read: `check.py:139-246`; CI: `test_nothing_a_stopped_tool_started_is_left_running` (a `sleep 3600`
the tool started is gone within 1 s), `test_the_temporary_folder_is_removed`,
`test_printing_cannot_corrupt_the_report` (1 MB printed)]

### 4.2 The gate: D2's `PUT /tools/{name}`

`api.put_tool` calls `require_check` before anything else (`api.py:290-296`):
- YAML that D2 refuses passes through, so D2's `422 invalid` answers as before;
- an `mcp_server` block is `400 MCP_VIA_GRANT`;
- a canonical block and source equal to the head's (a grant-only change) runs no Check;
- otherwise `check_tool` runs with no example. A report that `can_save`, or `can_save_anyway` with
  `accept_check_failure: true`, proceeds to `Library.put_tool`. Anything else is
  `ToolCheckFailed` → 422 `check_failed` carrying the report.

`Library.put_tool` and `dr-library import` are not gated. [read: `check.py:360-386`; CI:
`test_a_grant_only_change_runs_no_check` (a broken tool stored directly, then a grant-only `PUT` → 200),
`test_save_anyway_stores_a_raising_tool_only_when_asked`, `test_a_structural_failure_cannot_be_saved_anyway`]

### 4.3 A grant is a D2 tool row: `mcp/grants.py`, `tools/routes.py`

`PUT /mcp/{name}` builds the row as follows:
1. It validates the name with D2's rule (`validate_tool(name, "{}", None)`) and `RESERVED_NAMES`.
2. It refuses (`409 refused`) a server that another grant names.
3. It writes `Library.put_tool(name, canonical_yaml(mcp_block(name, body)), source=shim_source(),
   granted_in=…, base_version=…)`.

The block is `factory: mcp_server`, `name`, `server`, `transport`, and either `command`, `args` and
`env` (names) for stdio, or `url` and `headers` for HTTP and SSE. Each header maps to the variable
`dr` reads it from, `header_env_name(server, header)`. D2 adds `factory_from: tools/<name>.py`. A
row is a grant when its factory is `mcp_server` and its source starts with
`# deep-reasoning MCP shim` (`is_mcp_tool`), which also holds after an export and re-import.
[read; CI: `test_put_mcp_writes_the_block_and_the_shim_and_grants`,
`test_an_exported_and_reimported_grant_is_still_a_grant`]

`shim_current` is exact text equality with the installed `shim.py` (`grants.py:96`), so any edit to
`shim.py` marks every stored grant `MCP_SHIM_OLD` in the panel until its **Update** is clicked.
[read]

### 4.4 Front to worker: the seam that carries secrets

D1's `Session` keeps the `mcpServers` of `session/new` (and of `session/load`) as dumped dicts. At a
run's start the front runs `_materialize` in one `asyncio.to_thread`. It materializes the run as D1
and D2 do, then calls `specs_for_run(self.mcp_servers, source.config_path)`. That function reads
`main.yaml` as plain YAML for the `server` of each `mcp_server` block, converts the forwarded
entries (stdio has no `type` in ACP 0.12.1's dump; HTTP and SSE carry `"http"` and `"sse"`; other
types are dropped) and keeps only the named ones. They travel in `Start.mcp_servers` over the
control pipe, never in the worker's environment. A forwarded server that no block names, and its
secrets, never reach the worker. [read: `acp/session.py:193, 221-224`, `mcp/wire.py:71-116`; run:
`McpServerStdio(...).model_dump(by_alias=True)` has no `type` key; CI:
`test_a_run_gets_only_the_specs_its_blocks_name`, `test_a_forwarded_server_no_grant_names_is_never_started`
(the fake server's start marker is absent)]

### 4.5 The worker: `mcp/session.py`

`Worker.build` calls `open_session(cfg, start.mcp_servers, run_dir=run_dir)` after `load_dr_config`,
the namespace and client overrides and the decomposition's puppeteer, and before `build_reasoner`
(`runner.py:150-157`). `open_session` works in five steps:

1. It takes every block whose factory is `mcp_server`. Without any, it sets `shim.SESSION = {}` and
   no `mcp.status` is emitted.
2. With deep_reasoner's own registry it computes, for each alias, the namespaces whose
   `registry.resolve(ns).tools` names it. It also computes the namespaces this conversation can
   reach: the closure of `cfg.entry_namespace` under `check_spawn` over root, `namespaces_dir` and
   inline namespaces.
3. It decides each alias:
   - granted nowhere, or only out of reach → `skipped`, with a stand-in (`NOT_REACHED`);
   - no forwarded spec for its `server` → `not_enabled`, with a stand-in (`NOT_ENABLED`);
   - otherwise it starts a `Connection` whose `errlog` is `runs/<run>/mcp-<alias>.log`.
4. It waits for every started connection against one start (§2 #2). The outcome is `bound` (count,
   time, and `told`, deep_reasoner's describe of the binding), `failed` or `no_answer`:
   - `failed`: the failure plus the last 300 characters of the server's log, with every `env` and
     header value of 4+ characters replaced by `[redacted]`;
   - `no_answer`: `abandon()`.
5. It sets `shim.SESSION` to a `Func` for every block (`Server` with `granted=frozenset(...)`, or a
   stand-in) and returns one status per block.

[read; CI: `test_session.py`, 10 cases]

`make_tools` then loads each grant's stored copy of the shim as `tools/<alias>.py`. Its
`mcp_server` imports `deep_reasoning.mcp.shim`, finds `SESSION` set and returns `SESSION[alias]`
without connecting (`shim.py:475-491`). The server's own log in the run folder holds what the server
printed **unredacted**; only the status and the notice are redacted. [run: `crash_server.py` with
`CRASH_TOKEN=tok-SECRET-123` → detail `McpError: Connection closed; it printed: "invalid token
[redacted]"`, while `mcp-crash.log` reads `invalid token tok-SECRET-123`; CI:
`test_server_secrets_never_reach_the_run_log_or_the_transcript` checks `events.jsonl`, the
transcript and `worker.log`, not `mcp-<alias>.log`]

### 4.6 The shim at run time: `mcp/shim.py`

- **`Connection`**: one server, on a daemon thread that runs its own event loop. Its transports:
  - stdio runs through the guard: `sys.executable -I <this file> --guard -- command args…`, with
    `env=spec.env`. `mcp` adds its six variables and starts the guard in a new session.
  - streamable HTTP uses an `httpx.AsyncClient` that carries the headers;
  - SSE uses `sse_client(url, headers=…)`.

  `_serve` initializes, lists every page of tools, sets `ready` and waits until it is cancelled. Any
  exception becomes `failure`, the innermost exception as "Type: message". [read; CI:
  `test_an_http_server_is_reached_with_its_headers[http, sse]`, `test_calls_from_many_threads_and_under_nest_asyncio`]
- **A call** is `run_coroutine_threadsafe(session.call_tool(..., read_timeout_seconds=call_timeout_s))`,
  given up after `call_timeout_s` + 5 s. It maps outcomes as follows:
  - `McpError` 408 → `CALL_TIMEOUT`;
  - `McpError` −32000, or anyio's closed, broken or end-of-stream errors → the connection is dead,
    and every call from then on raises `SERVER_STOPPED`;
  - anything else → `CALL_FAILED`.

  The result follows §8.3: `isError` raises; `structuredContent` is unwrapped when both the tool's
  `outputSchema` and the content hold only `result`; all-text content becomes one string; other
  content is a list of dumped blocks. [read: `shim.py:245-296`; CI:
  `test_results_are_unwrapped_dicts_text_or_blocks`, `test_a_call_that_never_answers_raises_after_its_timeout`]
- **What the REPL binds**:
  - `Server` is callable as `name(tool, /, **arguments)`, unannotated so deep_reasoner renders
    exactly that. It gets one `McpTool` attribute per tool whose name, with non-word characters as
    `_`, is a free identifier.
  - `McpTool` maps positional arguments onto required-then-optional parameters.
  - Both return themselves from `__copy__` and `__deepcopy__`.
  - `__cross_namespace__(src, dst)` raises `PermissionError(HANDOFF_REFUSED)` when a grant set is
    known and `dst` is outside it. The first bind (`src is None`) always passes.

  [read; CI: `test_a_server_survives_fork`, `test_handing_a_server_to_an_ungranted_namespace_is_refused`]
- **The description** is §8.4's, exactly. [CI: `test_the_description_is_what_8_4_says`]
- **A stand-in** (`Unavailable`) is told to the agent as `` `wiki(*args, **kwargs)` `` followed by
  its reason. [run]
- **Plain `dr`** (`SESSION` is `None`): `spec_from_block` reads each `env` name and each header's
  variable from `os.environ`. The shim connects, waits up to `connect_timeout_s` (default 10 s) and
  binds `Server(granted=None)`, which refuses no hand-off. Otherwise it logs a structlog warning,
  `mcp.unavailable`, and returns a stand-in; without the `mcp` package the stand-in says
  `pip install mcp`. A crashing server's stderr goes to `dr`'s own stderr, unredacted. [run: crash
  server 0.14 s, silent server 2.59 s with a 2 s timeout; CI: `test_an_exported_grant_runs_under_dr`,
  `test_without_the_mcp_package_the_factory_returns_a_stand_in`]
- **The guard** remembers `os.getppid()` and starts the command in its own process group. A daemon
  thread polls the parent every 0.5 s and sends `SIGKILL` to the group (`os.killpg(0, …)`) once the
  parent changes. [read: `shim.py:520-539`; CI: `test_the_guard_ends_its_server_when_its_parent_is_killed`
  (gone within 1.5 s), `test_no_stdio_server_outlives_a_root_stop` and `…_a_closed_session` (within 2 s)]

### 4.7 What comes back: the run log, notices and the seen cache

The worker emits `mcp.status` through D1's recorder. The pump logs it, the encoder emits the
notices, and for a live event (never a replay) the front calls `remember_seen(home.root, run_id,
servers, now)`. For each `bound` server, that writes `$DR_HOME/mcp/<first 16 hex of
sha256(server)>.json` = `{v, server, tool, transport, at, run, count, told}` through `mkstemp` and
`os.replace` (0600 in a 0700 folder). An `OSError` is logged, not raised. `GET /mcp` reads it from
`library.path.parent`, which is the same folder when the Library sits at `$DR_HOME/library.sqlite`.
[read: `acp/supervisor.py:209-226`, `mcp/wire.py:128-165`; CI:
`test_the_seen_cache_is_written_for_bound_servers`, `test_the_seen_cache_round_trips_and_is_private`]

### 4.8 The frame

- **The page** (Canvas's realm), for the Tools tab only:
  - `readMcpServers` runs `GET /api/settings` (no `X-Expose-Secrets`) and `GET
    /api/agent-profiles/deep_reasoner` in parallel. Either failing → `null`.
  - `mcpServersFromSettings` reads `agent_settings.mcp_config` as a name → server map.
  - Each server's transport is stdio with a `command`, SSE with a `url` and `transport: "sse"`,
    otherwise HTTP with a `url`. A server with neither is skipped.
  - `env` and `headers` become their keys only.
  - `why_not` is `disabled` (`enabled === false`) or `not_in_profile` (refs not `null` and the name
    absent).

  The list rides in the frame URL as `mcp`. [read: `page/context.ts:105-180`, `page/mount.ts:107-127`;
  CI: `context.test.ts`, `mount.test.ts` "reads Canvas's MCP servers for the Tools tab only"]
- **`mcpRows`** joins Canvas's list with `GET /mcp` by server name. It returns Canvas's servers in
  Canvas's order, then grants gone from it, sorted. `changed` compares the JSON of
  `snapshotOf(info)` and the grant's snapshot, so the order of args, env names and header names
  counts. With `mcp` null there are only grant rows, and no new grant can be made. [read: `tools.ts:102-146`]
- **The editor**:
  - A saved tool's namespace tick `PUT`s the **head's** `yaml`, source and version with the new
    `granted_in`, so no Check runs and unsaved code is not sent.
  - Save sends the draft; a 422 with a report shows the report.
  - The draft is kept in `localStorage` under `dr-library.draft.tool.<name>` or `….new`.
  - A built-in tool (no source) shows no source field.

  [read: `ToolEditor.tsx:146-189`; CI: `test_a_grant_tick_on_a_saved_tool_saves_without_unsaved_code`]
- **An MCP row**:
  - A first tick `PUT`s Canvas's snapshot with `base_version: 0`; a 409 `conflict` there reads
    `MCP_NAME_TAKEN`.
  - Later ticks resend the stored snapshot at the grant's version.
  - **Update** resends Canvas's snapshot, or the stored one when Canvas's settings are unread.
  - **Remove** is D2's `DELETE /tools/{name}`.

  [read: `McpServerRow.tsx:72-120`; CI: browser tests in §6.1]

### 4.9 What it relies on

- **deep_reasoner** (`d7334ae`):
  - from `config`: `load_cli_config` and `build_client`;
  - from `v2.cli`: `V2Config`, `build_namespace_registry` and `make_tools` (in a test);
  - from `tools.base`: `load_tool_factory` and `TOOL_BUILDERS`;
  - from `primitives`: `Func`; from `v2.messages`: `func`;
  - from `namespaces`: `ROOT`, `NamespaceRegistry`, `check_spawn`, `NamespaceSpawnError` and
    `load_namespaces_from_dir`.

  `make_tools`' two inline sentences are copied into `tools/texts.py`, and a test fails if
  deep_reasoner's change. [read: imports]
- **`mcp`** (1.30.0): `stdio_client`, `StdioServerParameters`, `ClientSession`,
  `streamable_http_client(url, http_client=…)`, `sse_client`, `PaginatedRequestParams`, and
  `McpError`'s codes 408 and −32000. [read]
- **The SDK fork** (read at `91430aa`; the local checkout's head `ea51b3f` is one commit later):
  - `MCPConfig` is a `RootModel[dict[str, MCPServer]]`;
  - `_mcp_config_to_acp_servers` forwards each enabled server: stdio always, HTTP or SSE by
    `effective_transport` when advertised;
  - a header-compatible `auth` is forwarded as extra headers.

  [read: `openhands-sdk/openhands/sdk/settings/api_models.py:63`,
  `…/agent/acp_agent.py:717-821`, `…/mcp/config.py:497-577`]
- **D1**: `Start`, `Worker.build`, the recorder, the pump, `Session.mcp_servers` and the harness.
  **D2**: tool rows, `granted_in` as the exact set, `validate_tool`, unchanged-is-not-a-save, and
  `create_app`'s guard. **D3**: `NamespaceChecklist`, `drafts.ts`, `CodeField`, `ConfirmRow`, `load.ts`
  and the frame protocol. [read]

---

## 5 · Wiring

- **`pyproject.toml`**:
  - `mcp>=1.28,<2` joins the runtime dependencies;
  - ruff's `extend-exclude` adds `tests/mcp/fixtures`, so the frozen shim stays as the Library
    stores it.

  This document's commit adds `as_built/` to the sdist's `exclude` beside `docs/`. Pytest's
  `testpaths` and the wheel's `packages` already leave it out, CI's ruff checks only `src` and
  `tests`, and prettier runs inside `canvas-app/` only. [run: `uv build`, §6.1]
- **D1's files**:
  - `AGENT_CAPABILITIES` flips both MCP flags;
  - `McpStatus` joins the `RunEvent` union, and the encoder has a `case` for it;
  - `texts.py` gains the three notices and `mcp_notice`;
  - `Start.mcp_servers` is new;
  - `RunHandle.start(…, mcp_servers=())` passes the specs, and the pump calls `_remember`;
  - `Session._materialize` computes the specs;
  - `Worker.build` calls `open_session`.

  In D1's tests: `DrAcp.open_session(cwd, mcp_servers=())`, the capability test is renamed
  `test_initialize_advertises_load_close_and_http_and_sse_mcp`, and the 18 golden recordings change
  on their first line (the `initialize` response) only. A new shared helper is
  `tests/processes.py` (`alive`, `running_after`). [read: `git diff 5effe26..965f318`]
- **D2's `api.py`**:
  - `_ToolBody.accept_check_failure: bool = False`;
  - the route closure becomes the module-level `json_route`, with no change in behaviour (its 28
    call sites renamed);
  - `put_tool` calls `require_check` first;
  - `create_app` appends `*tool_routes(lib)` and imports D4's modules inside the function.

  D2's `test_ui.py` adds two asserts that `editor.js` is built and referenced. [read]
- **D3's project**:
  - `tabs/tools.tsx` is extended; `api.ts`, `types.ts`, `texts.ts`, `shared/protocol.ts`,
    `page/context.ts` and `page/mount.ts` are edited;
  - `fields.tsx`'s `ConfirmRow` takes an optional `confirmTestId`;
  - there are new files in `components/`, `editor/` and `tools.ts`;
  - `vite.config.ts` now emits chunks;
  - five pinned CodeMirror packages are added to `package.json`.

  [read]
- **CI.** D4 changes no workflow. D3's `canvas-app` job runs `tsc`, prettier, vitest, the build, a
  check that the committed build is what a fresh one gives, and `pytest -m browser tests/canvas_app`.
  D1's `live.yml` runs `pytest -m live`, which collects D4's two live tests. [CI]

---

## 6 · Experiments, as measured

### 6.1 The runs

| Run | Conditions | Commit | Result |
|---|---|---|---|
| CI [37106223937](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37106223937), job `test` | ubuntu-latest, Python 3.12.3; ruff check and format first | `965f318` | **667 passed, 71 deselected, 355.08 s**. D4's files: `tests/mcp/` 72, `tests/tools/` 61 (the two live tests are deselected) [CI] |
| the same run, job `canvas-app` | Node 22; `npm ci`, `tsc`, prettier, vitest, build, committed-build check, Playwright 1.56.0 Chromium | `965f318` | vitest **187 passed, 1 skipped** (11 files); build `app.js` 168.76 kB, `editor.js` 348.48 kB, page 8.36 kB; committed build matches; browser **64 passed, 1 skipped, 180.61 s** (the skip is D3's `test_the_notice_is_d5s_sentence_with_the_cap`: "D5's dr_app is not installed") [CI] |
| live [37106223637](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37106223637) | `workflow_dispatch`, `OPENAI_API_KEY` secret, `pytest -m live -v -rA` | `965f318` | **6 passed, 604 deselected, 81.33 s**, including both of D4's live tests (§6.4) [CI] |
| local, deterministic | this sandbox, `CI=true`, the clone of deep_reasoner_beta at `d7334ae`, other agents' suites running on the same machine (load average 6–9) | `965f318` | **667 passed, 71 deselected, 759.95 s**, with no failure and so no rerun. D4's slowest: `test_check_and_make_tools_agree[hang]` 14.55 s, `test_a_hanging_factory_is_stopped_at_the_build_limit` 12.88 s [run] |
| local, browser | `CI=true uv run pytest -m browser tests/canvas_app`, Playwright 1.56.0, `PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers` | `965f318` | **64 passed, 1 skipped, 233.16 s** (the same skip as CI) [run] |
| local, frame | `npm ci`; `npx vitest run` with `DR_BETA_CHECKOUT` set; `npx tsc --noEmit`; `npm run build`, then `git status` | `965f318` | vitest 187 passed, 1 skipped (186 and 2 without `DR_BETA_CHECKOUT`: D3's corpus round trip skips); `tsc` exit 0; `npm run build` leaves every tracked file unchanged, and a build into a scratch folder is byte-identical under `diff -r` [run] |

To reproduce:
- E9 and the rest of the deterministic suite: `DR_BETA_CHECKOUT=<deep_reasoner_beta at d7334ae> uv run
  pytest tests/tools tests/mcp`.
- The panel: `CI=true uv run pytest -m browser tests/canvas_app/test_tools_tab.py`, and `npx vitest run`
  in `canvas-app/`.
- The live tier: `OPENAI_API_KEY=… uv run pytest -m live tests/tools/test_live.py tests/mcp/test_live.py`.

### 6.2 E9 · your own tools

**Conditions.** `check_tool` ran on the committed fixtures under the default limits (30/10/10 s),
from a probe script, with the machine under load (load average about 7). Each row's null is "a
failure that shows only at run time". [run]

| Case | Outcome | Save | Wall time | What the report says |
|---|---|---|---|---|
| `word_count.py`, tried `word_count("one two three")` | `built` | yes | 1.88 s | told `` - `word_count(text: str) -> int` `` / `word_count(text) -> int: number of words in text.`; example `'3'` |
| `not_func.py` | `not_func` | no | 2.51 s | `make_tools`' sentence: "tool 'word_count': make in tools/word_count.py returned function, not a Func. …" |
| `word_count.py` with `factory: mkae` | `bad_factory` | no | 1.54 s | "'tools/word_count.py' defines no 'mkae'. It defines: make, make_broken. Known built-in factories: claude_code, kg, llm, rag, safe_url." |
| `import_error.py` | `import_failed` | no | 1.65 s | "importing 'tools/word_count.py' raised ModuleNotFoundError: No module named 'yaml_x'" |
| `env_at_build.py` | `raised` | anyway | 2.01 s | "make raised KeyError: 'D4_TOKEN'", with the frame `File "tools/word_count.py", line 7, in make` |
| `exits.py` (`os._exit(3)`) | `raised` | anyway | 1.46 s | "the Check process ended (exit code 3) while building the tool." |
| `def make(` | `syntax` | no | 0.00 s | "tools/word_count.py line 1: '(' was never closed" (no process) |
| `factory: rag`, no source | `builtin` | yes | 0.00 s | `BUILTIN` (no process) |
| `hang.py` | `timeout` | anyway | **11.66 s** | `BUILD_TIMEOUT` with "10 s" |

**Check and `make_tools` agree** [CI and run: `test_check_and_make_tools_agree`, 8 cases]. For each
fixture, Check's `ok` equals whether deep_reasoner's own `make_tools` builds the same one-tool config
in a subprocess with `check_env` (10 s limit). Where deep_reasoner words the failure (`not_func`,
misspelled, `import_error`), the sentences are equal. Both sides run without secrets, so
`env_at_build` agrees by failing on both. The test says nothing about what a conversation, which has
the secrets, would build.

**Through the panel and a conversation** [CI]:
- `test_routes.py::test_a_tool_that_cannot_build_is_not_saved[not_func, misspelled, import_error]`
  (422 `check_failed`, nothing stored);
- `test_a_checked_tool_is_saved_with_its_grants`;
- `tests/mcp/test_acp.py::test_a_tool_saved_through_the_api_is_built_and_called_in_the_next_conversation`
  (a real `dr-acp` with `FakeOpenAI`: the cell's output is `4`, and the first model request carries
  `` - `word_count(text: str) -> int` ``);
- the browser tests `test_a_tool_that_cannot_build_shows_why_and_cannot_be_saved[3]`,
  `test_a_hanging_factory_shows_the_limit` and `test_a_raising_factory_offers_save_anyway`.

The hanging-factory unit test asserts `10 s ≤ took < ready + 10 s + 1 s` and that a process the tool
started is gone 1 s later.

### 6.3 E9 · MCP servers

The fake servers are real FastMCP servers of the project's own, run as scripts:
- `echo_server.py`: stdio, `--http PORT` and `--sse PORT`, with eleven tools;
- `hang_server.py`: never reads its stdin;
- `crash_server.py`: prints its token and exits 1;
- `catalog_server.py`: used by the live tier.

Every row is [CI] at `965f318`. The local results are in §6.1.

| Null | Test | Measured condition |
|---|---|---|
| a crashing server blocks the session or takes the worker down | `test_session.py::test_a_server_that_exits_at_start_is_failed_with_its_stderr_redacted`; `test_acp.py::test_a_server_that_crashes_at_start_is_reported_and_the_run_answers`, `::test_a_server_that_crashes_mid_run_fails_the_call_and_the_run_goes_on` | detail exactly `McpError: Connection closed; it printed: "invalid token [redacted]"`; the notice comes first, then the answer; after a mid-run crash the failing call and the next one both raise `McpToolError` with the `SERVER_STOPPED` sentence, and the next prompt is answered |
| a hanging server blocks the session | `test_session.py::test_servers_connect_at_once_and_a_silent_one_is_given_up_at_the_deadline`; `test_acp.py::test_session_new_does_not_wait_and_the_first_answer_waits_at_most_the_deadline`; `test_shim.py::test_a_call_that_never_answers_raises_after_its_timeout`; `test_session.py::test_a_server_given_up_is_ended_within_three_seconds` | three silent servers at 1.5 s are all `no_answer` in 1.5–3 s; `session/new` starts no server; with a 2 s grant, `mcp.status` comes 2–5 s after `worker.ready`, and the first root text is `mcp_no_answer("silent", 2)`; an abandoned server is gone within 3 s |
| a server not granted to the conversation's namespace is in its REPL | `test_acp.py::test_a_server_granted_elsewhere_is_not_in_this_agents_repl_or_prompt`, `::test_a_sub_agent_spawned_into_a_granted_namespace_gets_it`, `::test_a_grant_reaches_a_child_namespace`, `::test_handing_a_server_to_an_ungranted_namespace_is_refused`; `test_session.py::test_a_server_granted_nowhere_is_not_started`, `::test_a_server_granted_only_where_spawning_is_not_allowed_is_not_started` | granted to `course_advisor` with the conversation in `router`: a cell's `'echo' in dir()` prints `False`, and the first model request lacks `echo(tool`; a sub-agent spawned into the granted namespace and a child namespace both reach it; a hand-off outside the grant raises `PermissionError: HANDOFF_REFUSED` |
| a server outlives its run | `test_acp.py::test_no_stdio_server_outlives_a_root_stop`, `::test_no_stdio_server_outlives_a_closed_session`; `test_shim.py::test_the_guard_ends_its_server_when_its_parent_is_killed` | a cell in `while True: pass`, then a root Stop: no fake server runs 2 s later; a `SIGKILL`ed parent: the server is gone within 1.5 s |
| a server's secret leaks | `test_acp.py::test_server_secrets_never_reach_the_run_log_or_the_transcript`; `test_wire.py::test_a_run_gets_only_the_specs_its_blocks_name` | the token is absent from `events.jsonl`, the ACP lines and `worker.log`; it is present in `runs/<run>/mcp-<alias>.log` (§4.5) |

**Contracts** (design §10.1, layer 2). Every test that drives `dr-acp` uses D1's `dr_acp` harness.
The harness validates each message against ACP's schema and asserts, when it exits, that there was
no violation and that stdout held only JSON-RPC lines (`tests/acp/harness.py:240-241`). So the
notices are schema-checked in `test_acp.py`'s 16 cases and in both live tests. [read; CI]

**Under plain `dr`** [CI: `test_export.py::test_an_exported_grant_runs_under_dr`]. `dr-library export`
writes the export; then `dr <dir>/main.yaml` runs with `FakeOpenAI` scripted to call `echo.echo("hi")`
and `ECHO_TOKEN` in the environment. It exits 0, and the cell's output is `hi`.

### 6.4 Live tier (gpt-6-luna)

Both tests write through `create_app` and `TestClient`, so the gate and a real Check run. They drive
a real `dr-acp --home` over stdio with D1's harness and the starter profile. The facts asked for
exist only in the tool or the server.

| Test | Asserted | Result |
|---|---|---|
| `tests/tools/test_live.py::test_live_a_tool_written_in_the_library_is_used_by_the_agent` | `PUT /tools/course_credits` (granted to `root`) → 201; a Check on the same body → `built`; "How many credits is course ZQ-417?" → outcome `answered`, and the last root text contains `7`; a cell's code calls `course_credits(` and its output contains `7` | **passed**, about 22.7 s between its PASSED line and the previous one [CI] |
| `tests/mcp/test_live.py::test_live_an_mcp_server_granted_to_the_namespace_is_used_by_the_agent` | `PUT /mcp/catalog` (stdio, `CATALOG_TOKEN` by name, granted to `root`) → 201; `session/new` forwards `McpServerStdio` with a random token; "What must a student finish before ZQ-417?" → `answered`, and the last root text contains `ZQ-101`; `mcp.status` is `[("catalog", "bound")]`; a cell calls `catalog.prerequisites(`; the token is in neither `events.jsonl` nor the ACP lines | **passed**, about 10.0 s [CI] |

Both passed in live run 37106223637 at `965f318`. Each ran once, and the log does not record the
run's token cost. I could not run them here: `OPENAI_API_KEY` is not set in this sandbox.

### 6.5 Named in the design, not run by D4

- **E10 with MCP servers bound** (§11.4) is D5's run.
- **E12's MCP step** (§11.4) is a proposal for D5.
- **The cross-repository forwarding test** (§10.6, `tests/crossrepo/test_mcp_forwarding.py`) does not
  exist on this branch. The bridge-to-`dr-acp` forwarding is exercised only with a hand-built
  `McpServerStdio` (the live test, `test_acp.py`) and dicts (`test_wire.py`).

---

## 7 · What I could not verify

1. **Forwarding through a real agent-server.** The ACP shapes `dr-acp` receives were built by hand in
   the tests; the bridge's `_mcp_config_to_acp_servers` was read at `91430aa`, not run (§6.5).
   `forwarded_specs` accepts both a missing and a `"stdio"` `type`.
2. **The frame against real Canvas settings.** `mcpServersFromSettings` was tested against
   hand-written settings JSON; the shape (`MCPConfig` as a name → server map) was read in the SDK
   fork. A server whose credentials are in `auth` rather than `headers` gets an `Authorization`
   header from the bridge (`acp_agent.py:717-736`). That header is not in the frame's `headers` list,
   so it is not in the grant's snapshot, and an export under `dr` would not send it. [read]
3. **The live tier** ran once, in CI. Its token cost is not in the log, and I could not re-run it
   here.
4. **macOS.** Nothing ran on macOS: not the guard's `getppid` polling, not `check_env`'s password
   database, and not Check's process-group kill.
5. **Remote servers** were exercised only against the local fake servers over streamable HTTP and SSE
   on loopback. OAuth-protected servers and slow networks were not.
6. **Load.** One Check at a time, and at most three servers per run, are tested. Two Checks at once,
   or many servers, were not run. The worst case of a 50 s Check through the agent-server's bridge
   (no read timeout, B3) was read in the design, not run.
7. **The ungated paths.** `Library.put_tool` and `dr-library import` store a tool that cannot build,
   which then stops every conversation (`make_tools` builds every block). This is design §3.5 and
   §14 item 4. I read it and did not run it.
8. **`open_session` raising** (§2 #3) was read, not provoked.
9. **The read claims that matter most:**
   - §4.4's statement that secrets never enter the worker's environment (the tests check the run
     log, the transcript and `worker.log`, not `/proc/<worker>/environ`);
   - §4.7's assumption that `library.path.parent` is `$DR_HOME`.
