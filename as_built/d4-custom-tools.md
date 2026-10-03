# D4 · Custom tools and MCP servers, as built

**TASK-9** · Cartographer · revision 2 · the code at `f69bc73` (head of `v1-custom-tools`; this
file is on `as-built/d4-r2`) · checked against design v3 (`edf1212`,
`docs/design/d4-custom-tools.md`) · deep_reasoner_beta `d7334ae` · `mcp` 1.30.0 (locked) ·
agent-client-protocol 0.12.1 · SDK fork `91430aa` (read only) · 2026-10-03.

This revision replaces r1 (`756f5f9`), which read the code at `965f318` against design v1.
Design v2 and v3 took in r1's findings as their §6.2 B1–B23. This revision checks v3 against the
build and names what still differs. D4's code is `src/deep_reasoning/tools/`,
`src/deep_reasoning/mcp/`, the Tools tab in D3's `canvas-app/` and its built files, and
`tests/tools/`, `tests/mcp/`. It also edits D1's, D2's and D3's files (§6). D1's, D2's and D3's
code is described only where D4 meets it.

**Evidence marks.** Every claim carries one.
- **[run]**: executed on this machine on the code at `f69bc73`. That covers:
  - the default suite (`DR_BETA_CHECKOUT=/home/user/deep_reasoner_beta uv run pytest`);
  - the browser tier (`CI=true uv run pytest -m browser tests/canvas_app`, preinstalled Chromium);
  - in `canvas-app/`: `npm ci`, vitest, `tsc --noEmit`, prettier, and a build into a scratch folder compared with the committed files;
  - `git` commands;
  - two probe scripts, not committed, that call `check_tool`, the shim, and the App backend through Starlette's `TestClient`.
- **[CI]**: read from GitHub's logs, and from the artifacts the live job kept, of the runs in §7.1. I ran no live
  test and made no paid model call.
- **[read]**: read in the code and **not executed**. This is weaker evidence than [run]. §8 lists the read claims that matter most.

**Reading order.** §1 first: the divergences from v3. §2–§4 are the map. §5 is what D4 stands on,
§6 the wiring and the size, §7 the experiments and the evidence as measured, §8 what I could not
verify.

---

## 1 · Divergences from design v3

No changelog entry carries a `drift:` line for TASK-9; the Changelog's newest entry is from
2026-10-02 [read: the Notion Changelog]. Every item below was found in the code or the runs.

v3 says it matches the build at `aa67f0a` and that the commits after it change only `docs/`.
Five D4 commits since then change code, tests or CI: `1847ef0`, `9255778`, `7eb7812`,
`933ac08`, `f69bc73`. §1.1 is what they changed. §1.2 is where v3 already differed from the code.
§1.3 is behaviour v3 does not state. Each row gives the reason the commit or the code records, or
"none recorded".

### 1.1 Changed after v3

| # | v3 says | Built | Where | Reason |
|---|---|---|---|---|
| 1 | §8.4 maps JSON Schema types to Python names and has no entry for a boolean schema. §14 item 15: the shim cannot describe a property whose schema is `true` or `false`, "not changed by the build". | `_type` describes a `true` property schema as `Any` and `false` as `Never`. A tool with such properties is told as `odd.odd(anything: Any = …, nothing: Never = …) -> str`. [run: probe, plain `dr`; CI: both tests below] | `src/deep_reasoning/mcp/shim.py:398-400`; tests `tests/mcp/test_session.py:275-283`, `tests/mcp/test_shim.py:257-263` | `7eb7812`: JSON Schema allows a boolean as a schema; under plain `dr` the factory raised and the run did not start |
| 2 | §6.2 B19 and §10.3: the case "it cannot be told" of `test_a_server_open_session_cannot_bind_fails_alone_and_the_others_bind` is a property whose schema is `true`. | That case now uses a property schema that is a string (`ODD_PROPERTIES={"anything": "string"}`), which is no JSON Schema. The detail is `AttributeError: 'str' object has no attribute 'get'`. `odd_server.py` takes its properties from `ODD_PROPERTIES`. [CI; run: the default suite] | `tests/mcp/test_session.py:225, 243-248`; `tests/mcp/servers/odd_server.py:13-15` | `7eb7812` |
| 3 | §6.2 B23: `tests/mcp/fixtures/shim_v1.py` is byte-identical to today's `shim.py`. | The two differ in `_type` only (3 lines). `test_a_stored_v1_shim_works_with_todays_session` now loads an older stored text through `load_tool_factory` and reads today's `SESSION`. Every grant stored before `7eb7812` has `shim_current: false`, so the Tools tab shows it with `MCP_SHIM_OLD` and **Update**. The marker line still says version 1. [run: `diff`; read: `grants.py:96` compares the text] | `tests/mcp/fixtures/shim_v1.py:398`; `src/deep_reasoning/mcp/shim.py:1, 398-400`; `src/deep_reasoning/mcp/grants.py:96` | `7eb7812`: the contract between a stored shim and the package (`SESSION`) is unchanged, so the marker stays at 1 |
| 4 | §10.5 and the Gate B table: the live tests ask "How many credits is course ZQ-417?" and "What must a student finish before ZQ-417?". §14 item 8: a model may answer without calling the tool. | The tasks name the tool and the server: "Use course_credits to find how many credits course ZQ-417 is." and "Use the catalog server to find what a student must finish before ZQ-417." Every assertion is unchanged. So the live tier does not test whether the model decides on its own to call the tool or the server. [read; CI: §7.4] | `tests/tools/test_live.py:43, 66`; `tests/mcp/test_live.py:32, 68` | `933ac08`, `f69bc73`: asked bare, gpt-6-luna answered "4 credits." without a cell in both attempts of run 37153297958 (§7.4) |
| 5 | §10.5: the live tier runs "in D1's on-demand `live.yml`". The Gate B section: the failed MCP test's run log "was not kept". | `live.yml` runs `pytest -m live -v -rA --basetemp="$RUNNER_TEMP/live"`. On a failure, a step greps every kept file for the model key. Only if none holds it, every test's dr home is uploaded as `live-dr-homes`, kept 7 days. A home holds its runs' `events.jsonl`, `llm_calls.jsonl` (every prompt and reply), `worker.log`, `mcp-<alias>.log`, `library.sqlite` and, for the MCP test, `transcript.jsonl`. The MCP test writes that transcript on every run. Its first assertion's message is the run's `mcp.status`, `agent.end` and `prompt.end`. [read; CI: run 37153297958 uploaded two artifacts, 254,222 and 234,114 bytes] | `.github/workflows/live.yml:27-44`; `tests/mcp/test_live.py:72-78` | `9255778`: run 37145903109 failed twice and kept nothing to say why |
| 6 | §10.2 lists the fake MCP servers; §10.3 lists `test_session.py`'s tests. | One fake server more, `loud_server.py`: it prints 1 MB to stderr at start and 256 KB on each call, its `LOUD_TOKEN` on every line. `test_a_server_that_prints_more_than_a_pipe_holds_answers_and_its_log_is_redacted` pins that the server answers three calls and that its log is exactly what it printed with the token as `[redacted]`. [CI; run] | `tests/mcp/servers/loud_server.py`; `tests/mcp/test_session.py:308-326` | `1847ef0`: if the log's copier stopped, a server printing more than a pipe holds would block |
| 7 | §13 and §6.2 B16: 3,397 lines of code and 3,686 of tests over D3's `d4e9cd3`. | **3,399 and 3,778** (§6.2). [run] | `shim.py` +2; tests +92 | the five commits |
| 8 | The Gate B section: CI at `aa67f0a` is green and the live tier is red (5 of 6, the MCP test `exhausted`) until a re-run passes. | CI at `f69bc73` is green, and the live tier passed twice at `f69bc73`, 6 of 6 each (§7.1). | — | evidence, not build |

### 1.2 Not as v3 says, already at `aa67f0a`

| # | v3 says | Built | Where | Reason |
|---|---|---|---|---|
| 9 | §4.3: a call's "anything else → `CALL_FAILED` with the innermost exception" ("Type: message"). | An `McpError` whose code is neither 408 nor −32000 becomes `CALL_FAILED` with `str(exc)`, which is the server's message without its type. Any other exception carries "Type: message". [read] | `src/deep_reasoning/mcp/shim.py:265-271` and `:279-280` | none recorded |
| 10 | §2.1: on Save, "a `409` and a `422 invalid` are D3's (§5.2 there)". | The tool editor shows a refused save's message, as one paragraph in `dr-errors`. It does not use D3's `FieldErrors`, so D2's field errors appear only as the lines of D2's message. A `409 conflict` on a saved tool gets D3's **Reload** and **Save over**, through `dr-reload-entry` and `dr-save-over`. [read] | `canvas-app/src/ui/components/ToolEditor.tsx:122-128, 323-349`; D3's editor: `canvas-app/src/ui/components/editor.tsx:437-441` | none recorded |

### 1.3 Behaviour v3 does not state

| # | Found | Where | Evidence |
|---|---|---|---|
| 11 | **Under plain `dr`, a server whose tool has a property schema that is neither a mapping nor a boolean stops the run.** The server answers, then `describe` raises inside the shim's factory. `make_tools` passes the exception on, so the run does not start. Under `dr-acp` the same server fails alone (`MCP_FAILED`) and the run goes on (B19). v3 §4.8 says only what happens to a server that cannot be reached: it becomes a stand-in and the run goes on. | `shim.py:401` via `bound` (`:442-447`) in `mcp_server` (`:507-508`); deep_reasoner `v2/cli.py:157` | [run: probe, `ODD_PROPERTIES={"anything": "string"}` → the factory raised `AttributeError: 'str' object has no attribute 'get'`; read: `make_tools`] |
| 12 | **A server's `auth`, forwarded by the bridge as headers, is not in the grant's snapshot.** For a remote server, the SDK fork's bridge adds a header-compatible `auth` to the headers it forwards. So under `dr-acp` the server gets them, and `wire.redact` redacts their values. The frame's `mcpServersFromSettings` lists only the keys of `headers`. So the grant's block names no variable for `auth`, and under plain `dr` an export does not send it. | SDK fork `openhands-sdk/openhands/sdk/agent/acp_agent.py:717-736` (at `91430aa` and at the fork's head `1f2b52d`); `canvas-app/src/page/context.ts:147`; `src/deep_reasoning/mcp/grants.py:79` | [read] |
| 13 | **D4 is built on D1 and D2 as they were at D2's Gate B build, not on their current heads.** D4 contains D2 at `90044f0` and D1 at `21f4a8b`. D1 was refactored and merged into `main` (`32c7f61`). D2's head `cd0b60c` has merged that `main` and adds a fix in `library/library.py`. D3's head `dcbe6b3` adds documents only after `d4e9cd3`. In `src/deep_reasoning/acp/`, D2's head differs from `d4e9cd3` in 18 files (+125 −330), six of which D4 also edits. Every D1 name D4 calls is still present on `main`, and `git merge-tree` of `f69bc73` with D2's head reports no conflict. The merged tree was not built or tested. | §5.1 | [run: `git merge-base`, `git diff --stat`, `git merge-tree`, `git grep`] |

### 1.4 Where v3 holds

Every behaviour in v3's §1–§11 and Appendix A that the code could contradict was compared with the
code at `f69bc73`. Beyond §1.1–§1.3, it matches:
- B1–B22 as v3 states them [read];
- §9's and §11.1's sentences, verbatim in the code [run: a script that splits each sentence at its placeholders and finds every fragment in `tools/texts.py`, `acp/texts.py`, `shim.py` or `ui/texts.ts`];
- every test id of Appendix B [run: `grep` of `canvas-app/src`];
- every test function v3 names, and the renamed capability test [run: `pytest --collect-only`];
- §11.1's place for `mcp.status` in the run log, after `prompt.start` and `worker.ready` and before the root's `agent.start` [CI: two real runs' `events.jsonl`, §7.3];
- the `mcp` 1.30.0 line numbers of §12 M1–M3, and deep_reasoner's of R1–R8 [read].

---

## 2 · What exists

D4 adds two things to the Library and to `dr-acp`.
- A **tool of your own** is a D2 tool row: a block and a Python source. **Check** builds it in a throwaway process, and the App backend runs Check again before it saves a changed tool.
- An **MCP grant** is also a D2 tool row. Its block snapshots a server's non-secret settings from Canvas's MCP settings, and its source is D4's **shim**.

In a conversation, `dr-acp`'s worker connects the granted servers before deep_reasoner builds its
tools, and the shim's factory hands each one over. Under plain `dr` (an export), the same shim
connects by itself. [read; each path run end to end by the tests in §7]

```text
Tools tab (frame) ─ POST ../tools/{n}/check ─▶ routes.check ─ check_tool ─┬ static stage: invalid · syntax · builtin · bad_factory   (no process)
                                                                         └ check_child: own process group, no secrets, model at 127.0.0.1:9
                  ─ PUT ../tools/{n} ───────▶ D2 put_tool ─ require_check ─ check_tool ─▶ 422 check_failed | 409/400 MCP_VIA_GRANT | Library.put_tool
                  ─ PUT ../mcp/{n} ─────────▶ routes.put_grant ─ mcp_block + shim_source() ─▶ Library.put_tool  (a tool row)
                  ─ GET ../mcp ─────────────▶ grant_record + read_seen($DR_HOME/mcp/<sha256[:16]>.json)
page (Canvas's realm), Tools tab only: GET /api/settings + the deep_reasoner profile ─▶ frame URL ?mcp=[…]  (names, never values)

dr-acp front:  session/new keeps mcpServers ─ first prompt: materialize ─ specs_for_run ─▶ Start.mcp_servers (control pipe)
worker:        load_dr_config ─ open_session: start every granted, reachable server at once; stderr → pipe → redacting copier → runs/<run>/mcp-<alias>.log
               ─ emit mcp.status ─ shim.SESSION = {alias: Func} ─ build_reasoner ─ make_tools ─ shim.mcp_server() returns SESSION[alias]
front pump:    mcp.status ─▶ events.jsonl ─▶ Encoder: one root notice per server not bound; remember_seen ─▶ $DR_HOME/mcp/
plain dr:      make_tools ─ shim.mcp_server() with SESSION None ─ Connection from the block, values from os.environ
```

| Part | Lines | Where |
|---|---|---|
| Check and the routes | 700 | `src/deep_reasoning/tools/`: `check.py` 392, `check_child.py` 128, `texts.py` 100, `routes.py` 80 |
| MCP | 1,046 | `src/deep_reasoning/mcp/`: `shim.py` 541, `session.py` 244, `wire.py` 163, `grants.py` 98 |
| edits to D1's files | +101 −7 | `acp/agent.py`, `encoder.py`, `runlog.py`, `session.py`, `supervisor.py`, `texts.py`, `worker/protocol.py`, `worker/runner.py` |
| edits to D2's `api.py` | +70 −46 | most of it D2's route helper moved to module level as `json_route` |
| the frame (D3's project) | +1,475 −30 | 15 files in `canvas-app/src/`, `vite.config.ts`, `package.json` |
| built files | `app.js` 169,027 B; `editor.js` 348,475 B (new); page bundle `dist/index.js` 8,520 B | `src/deep_reasoning/canvas_app/` |

[run: `wc`, `git diff --numstat d4e9cd3 f69bc73`]

The length sits in four places:
- `shim.py`: the connection, the REPL objects, the description and the guard (§4.6);
- `check.py`: the supervisor of the throwaway process (§4.1);
- `session.py`: `open_session` and its redacting log copier (§4.5);
- the frame's `ToolEditor.tsx`, 361 lines (§4.8).

[read]

---

## 3 · The public surface, from the code

### 3.1 HTTP (the App backend)

D4's routes come after D3's `/ui/` routes, behind D2's guard. The guard checks the same user, the
`Host` header and a JSON body. [read: `library/api.py:396-398`; CI:
`test_mcp_routes_answer_only_their_own_host`]

```text
POST /tools/{name}/check  {"yaml", "source"?, "example"?}            200 CheckReport, always (400 for a body it cannot read)
PUT  /tools/{name}        D2's body + "accept_check_failure"?        D2's answers, and, before anything is written:
                                                                     400 MCP_VIA_GRANT   (the body's block is an MCP grant's)
                                                                     409 refused, MCP_VIA_GRANT   (the head is a grant; any base_version)
                                                                     422 {"error": "check_failed", "message", "check": CheckReport}
GET  /mcp                                                            200 [McpGrant], in GET /tools order
PUT  /mcp/{name}          {"server", "transport", "command"?, "args"?, "url"?, "env"?, "headers"?, "granted_in", "base_version"}
                                                                     201 | 200 McpGrant
                                                                     400 MCP_BAD_REQUEST + pydantic's reason; MCP_NEEDS_COMMAND; MCP_NEEDS_URL
                                                                     409 refused: MCP_NAME_TAKEN (a tool of your own) | MCP_SERVER_TAKEN
                                                                     409 conflict (D2's); 422 invalid (the name rules)
DELETE /tools/{name}?base_version=   D2's route; removes a grant as it removes any tool
```

[read: `tools/routes.py:50-74`, `tools/check.py:378-392`, `library/api.py:289-297`; CI:
`tests/tools/test_routes.py`, 27 cases]

`PUT /mcp/{name}` checks, in this order: the body, D2's name rule and `RESERVED_NAMES`, a tool of
your own under that name, a server another grant already names, then the snapshot's command or
URL. [read: `tools/routes.py:52-72`]

What I ran against `create_app` [run: probe]:
- `PUT /tools/run_all` answers **422 `check_failed`**, `check.outcome: "invalid"`, with the message
  "'run_all' did not pass Check, so it was not saved." The reserved names are Check's rule, not
  D2's, so a reserved name never reaches D2's `422 invalid`.
- `PUT /mcp/x` without `base_version` answers 400 with `MCP_BAD_REQUEST`, then "Field required".
- `POST /tools/word_count/check` with a block that is a list, or with a `factory_from` other than
  `tools/word_count.py`, answers 200 with outcome `invalid` and D2's own message. D2's message
  lists the field errors; the report carries no separate list of them.

### 3.2 Python

- `deep_reasoning.tools.check`:
  - `check_tool(name, yaml_text, source, *, example=None, limits=DEFAULT_LIMITS) -> CheckReport`;
  - `require_check(library, name, yaml_text, source, *, accept_failure)`;
  - `ToolCheckFailed(name, report)`, `check_env(base)` and `tool_name_errors(name)`;
  - `CheckLimits(ready_s=30, build_s=10, example_s=10)` and `RESERVED_NAMES`.

  `CheckReport` has A.1's eleven fields, and `Outcome` has A.1's ten values. [read]
- `python -m deep_reasoning.tools.check_child --report-fd N --name NAME [--example EXPR] MAIN`. [read]
- `deep_reasoning.mcp.shim` is a module, and also every grant's `factory_from` file. It holds:
  - the factory `mcp_server(client, params)`;
  - `McpToolError`, `SESSION`, `ServerSpec`, `Connection`, `Server`, `McpTool`, `Unavailable`, `describe`, `bound`, `unavailable`, `spec_from_block`;
  - the guard, run as `python -I shim.py --guard -- COMMAND ARGS…`.

  Its first line is `# deep-reasoning MCP shim, version 1. …`. Its module level imports the standard library only. [read; CI:
  `test_the_shim_imports_only_the_standard_library_at_module_level`]
- `deep_reasoning.mcp.session.open_session(cfg, specs, *, run_dir) -> list[McpServerStatus]`, and
  `reachable(registry, start, names)`. [read]
- `deep_reasoning.mcp.wire` is what `dr-acp`'s front imports (pydantic and yaml only):
  - `McpServerSpec`, `McpServerStatus` and `McpSeen`;
  - `forwarded_specs`, `servers_named` and `specs_for_run`;
  - `redact`, `remember_seen` and `read_seen`.

  [read]
- `deep_reasoning.mcp.grants` is the backend's side: `McpGrantBody`, `McpGrant`, `shim_source`,
  `is_mcp_tool`, `header_env_name`, `mcp_block` and `grant_record`. [read]

### 3.3 `dr-acp`

- `initialize` advertises `mcpCapabilities: {"http": true, "sse": true}`. [CI:
  `test_dr_acp_advertises_http_and_sse`; D1's 18 golden recordings differ from D3's base in that
  line only, run: `git diff --numstat`]
- The run log has one new event, `mcp.status {servers: [McpServerStatus]}`. The worker emits it
  once per run, before `build_reasoner`, and only when the run's config has an MCP block. [read:
  `acp/worker/runner.py:151-154`]
- The encoder turns it into one root `agent_message_chunk` per server whose state is
  `no_answer`, `failed` or `not_enabled`, in both modes and on replay. Its text is the notice, then
  `"\n\n"`, with no `_meta`. The three sentences are §9.2's, verbatim. [read:
  `acp/encoder.py:356-366`, `acp/texts.py:143-173`; CI:
  `tests/acp/test_encoder.py::test_each_mcp_server_not_bound_is_a_notice_on_the_root[native, flat, replay]`,
  `test_the_notice_replays_on_load`]

### 3.4 The Tools tab

The tab shows, in this order:
- D3's safety banner;
- the risk line `TOOLS_RISK`;
- **Your tools**: the list with **+ New tool**, or an editor in its place, with a back link;
- **MCP servers (from Canvas's settings)**: one row per server, under `MCP_SETTINGS_UNKNOWN` when Canvas's settings were not read;
- `MCP_EXPORT_NOTE`.

[read: `canvas-app/src/ui/tabs/tools.tsx:72-174`; CI: the 17 browser tests of §7.2–§7.3]

The frame takes one new parameter, `mcp`, a JSON list of `McpServerInfo`. An entry of another shape
is dropped, and an unreadable value is `null`. [read: `canvas-app/src/shared/protocol.ts:154-183`;
CI: `protocol.test.ts`]

---

## 4 · Structure and seams

### 4.1 Check: `tools/check.py` and `tools/check_child.py`

**The static stage** runs in the backend and starts no process. Its steps, in order:
1. D2's `shapes.validate_tool` (`invalid`, D2's message);
2. `RESERVED_NAMES` (`invalid`);
3. an `mcp_server` block (`invalid`, `MCP_VIA_GRANT`);
4. a block without a source: `builtin` if its factory is `llm` or a key of deep_reasoner's `TOOL_BUILDERS`, else `bad_factory` in `make_tools`' words;
5. `compile(source, "tools/<name>.py")` (`syntax`).

[read: `check.py:327-346`; CI: each case with a fixture that fails the test if `Popen` is called]

**The child.** `_build_in_a_child` writes a one-tool config into `mkdtemp(prefix="dr-check-")`,
which is mode 0700:
- `config/main.yaml`, holding a client at `http://127.0.0.1:9/v1` with no retries, and the canonical block;
- `config/tools/<name>.py`, the source byte for byte.

It starts `sys.executable -m deep_reasoning.tools.check_child` with:
- the config folder as its working directory;
- `check_env`: the six variables `PATH`, `LANG`, `LC_ALL`, `LC_CTYPE`, `TMPDIR` and `TZ`; `HOME`, `USER` and `LOGNAME` from the password database; the two `PYTHON*` flags; nothing else;
- stdin `/dev/null`, and stdout and stderr to `printed.txt`;
- a pipe fd for its report;
- a new session.

A `Popen` that raises `OSError` is outcome `unavailable`, with phase `starting`. [read:
`check.py:274-307`; CI: `test_check_gets_no_secret`, `test_check_never_reaches_a_model`,
`test_a_check_whose_process_cannot_be_started_is_unavailable`]

The child mirrors `make_tools`' `factory_from` branch. It reports JSON lines on the pipe:
1. `ready`, after importing deep_reasoner;
2. `loaded`;
3. `built`, with `told`, which is deep_reasoner's `func(name, value, description).describe()`; or `failed`;
4. `example`;
5. `done`.

It classifies a `load_tool_factory` `ValueError` by its `__cause__`:
- an `ImportError` → `import_failed`;
- any other cause → `raised`;
- no cause → `bad_factory`.

An exception from the factory is `raised`, with the traceback's frames in `tools/<name>.py`. A
non-`Func` result is `not_func`, in `make_tools`' sentence. [read: `check_child.py:41-81`; CI:
`test_not_func_and_unknown_factory_sentences_equal_make_tools`, which fails if deep_reasoner's
inline text changes]

**The supervisor** is where the subtlety is. A daemon thread reads the pipe into a queue
(`_Reports`), so each phase can be awaited with a deadline:
- `ready` within 30 s, else `unavailable`;
- `built` or `failed` within 10 s more, else `timeout`;
- `example` within 10 s more, else the example's own `TimeoutError` while the build stays ✓.

A pipe that closes early is `CHILD_ENDED`, in one of three phases:
- `starting`: the outcome is `unavailable`;
- `building the tool`: the outcome is `raised`;
- `trying it`: the build stays ✓ and the example carries the sentence.

On every path, `_end` sends `SIGKILL` to the child's process group **before** it reaps the child.
The report carries the last 2,000 characters of `printed.txt`. The folder is removed in a `finally`.
[read: `check.py:141-248`; CI: `test_nothing_a_stopped_tool_started_is_left_running`,
`test_the_temporary_folder_is_removed[word_count, hang]`, `test_printing_cannot_corrupt_the_report`,
`test_an_example_that_ends_the_process_says_how_and_the_build_stays_ok`]

### 4.2 The gate: D2's `PUT /tools/{name}`

`api.put_tool` calls `require_check` before anything else (`api.py:289-297`). `require_check`
decides, in this order:
1. YAML that D2 refuses passes through, so D2's `422 invalid` answers as before;
2. a block whose factory is `mcp_server` → `400 MCP_VIA_GRANT`;
3. a head that is an MCP grant → `409 refused MCP_VIA_GRANT`, at any `base_version`;
4. a canonical block and source equal to the head's (a grant-only change) → no Check;
5. otherwise `check_tool` runs with no example. A report that `can_save`, or `can_save_anyway` with `accept_check_failure: true`, goes on to `Library.put_tool`. Anything else is `ToolCheckFailed` → `422 check_failed`, carrying the report.

`Library.put_tool` and `dr-library import` are not gated. [read: `check.py:362-392`; CI:
`test_a_grant_only_change_runs_no_check`, `test_save_anyway_stores_a_raising_tool_only_when_asked`,
`test_a_structural_failure_cannot_be_saved_anyway`,
`test_a_tool_of_your_own_cannot_replace_a_grant[new, the head's]`]

### 4.3 A grant is a D2 tool row: `mcp/grants.py`, `tools/routes.py`

`PUT /mcp/{name}` writes `Library.put_tool(name, canonical_yaml(mcp_block(name, body)),
source=shim_source(), granted_in=…, base_version=…)` after the checks of §3.1.

The block holds `factory: mcp_server`, `name`, `server` and `transport`, then either:
- for stdio: `command`, `args` and `env` (names);
- for HTTP or SSE: `url` and `headers`, each header mapped to the variable `dr` reads it from, `header_env_name(server, header)`.

D2 adds `factory_from: tools/<name>.py`. A row is a grant when its factory is `mcp_server` and its
source starts with `# deep-reasoning MCP shim` (`is_mcp_tool`). That also holds after an export and
re-import. A resend of the stored snapshot makes no new tool version, because D2 writes no version
for an unchanged row (`library/library.py:192-199`); only `granted_in` changes. [read; CI:
`test_put_mcp_writes_the_block_and_the_shim_and_grants`,
`test_put_mcp_resent_unchanged_makes_no_tool_version`,
`test_an_exported_and_reimported_grant_is_still_a_grant`]

`shim_current` is exact text equality with the installed `shim.py` (`grants.py:96`). [read]

### 4.4 Front to worker: the seam that carries secrets

D1's `Session` keeps the `mcpServers` of `session/new`, and of `session/load`, as dumped dicts. At
a run's start the front runs `Session._materialize` in one `asyncio.to_thread`
(`acp/session.py:193, 221-224`):
1. It materializes the run as D1 and D2 do.
2. It calls `specs_for_run(self.mcp_servers, source.config_path)`. That function reads `main.yaml` as plain YAML for the `server` of each `mcp_server` block.
3. It converts the forwarded entries. Stdio has no `type` in ACP 0.12.1's dump; HTTP and SSE carry `"http"` and `"sse"`; other types are dropped.
4. It keeps only the servers some block names.

The specs travel in `Start.mcp_servers` over the control pipe, never in the worker's environment.
A forwarded server that no block names never reaches the worker, and neither do its secrets.
[read: `mcp/wire.py:69-114`; CI: `test_a_run_gets_only_the_specs_its_blocks_name`,
`test_a_forwarded_server_no_grant_names_is_never_started`]

### 4.5 The worker: `mcp/session.py`

`Worker.build` calls `open_session(cfg, start.mcp_servers, run_dir=run_dir)` after `load_dr_config`,
the namespace and client overrides and the decomposition's puppeteer, and before `build_reasoner`
(`runner.py:150-157`). `open_session` works in five steps.

1. It takes every block whose factory is `mcp_server`. Without any, it sets `shim.SESSION = {}` and returns `[]`, so no `mcp.status` is emitted.
2. With deep_reasoner's own registry, it computes two things:
   - for each alias, the namespaces whose `registry.resolve(ns).tools` names it;
   - the namespaces this conversation can reach: the closure of `cfg.entry_namespace` under `check_spawn`, over root, `namespaces_dir` and the inline namespaces.

   An error here fails the build, as D1's `build_failed`.
3. It decides each alias, and starts a server only in the last case:
   - granted nowhere, or only out of reach → `skipped`, with a stand-in (`NOT_REACHED`);
   - no forwarded spec for its `server` → `not_enabled`, with a stand-in (`NOT_ENABLED`);
   - otherwise `_Started` reads the block's timeouts, opens `runs/<run>/mcp-<alias>.log` and starts a thread that copies a pipe into it. Then it starts a `Connection` whose stderr is that pipe.

   An exception in any of this is that server's `failed`, its "Type: message" redacted.
4. It waits for each started server in turn, until the shared start plus that server's own `connect_timeout_s`. Each becomes `bound`, `failed` or `no_answer`:
   - `bound`: count, the time from the shared start, and `told`, deep_reasoner's `describe()` of the binding;
   - `failed`: the pipe is closed and the copier given `DRAIN_S` = 2 s. Then the failure, plus the last 300 characters of the log, with every `env` and header value of 4+ characters replaced by `[redacted]`;
   - `no_answer`: `abandon()`.

   An exception while deciding abandons the connection and is that server's `failed`.
5. It sets `shim.SESSION` to a `Func` for every block, either `Server(…, granted=frozenset(...))` or a stand-in. It returns one status per block.

[read: `session.py:188-244`; CI: `test_session.py`, 17 cases]

**The log copier** (`_copy_redacted`, `session.py:104-118`) reads `PIPE_READ` = 64 KiB at a time,
decodes incrementally and applies `wire.redact` with the spec's `env` and header values. It writes
all but the last (longest secret − 1) characters, which wait for the next read. So a secret split
across two writes is still caught. A server's arguments are not redacted. [read; CI:
`test_a_server_that_exits_at_start_is_failed_with_its_stderr_redacted[whole, split]` (the log reads
`invalid token [redacted]`), `test_a_server_that_prints_more_than_a_pipe_holds_answers_and_its_log_is_redacted`
(1 MB at start and 3 × 256 KB, every line redacted, the three calls answered)]

`make_tools` then loads each grant's stored copy of the shim as `tools/<alias>.py`. Its
`mcp_server` imports `deep_reasoning.mcp.shim`, finds `SESSION` set and returns `SESSION[alias]`
without connecting (`shim.py:477-493`). [read; CI:
`test_a_stored_v1_shim_works_with_todays_session`]

### 4.6 The shim at run time: `mcp/shim.py`

**`Connection`** is one server, on a daemon thread that runs its own event loop. Its transports
are:
- stdio, through the guard: `sys.executable -I <this file> --guard -- command args…`, with `env=spec.env`. `mcp` adds its six variables and starts the guard in a new session.
- streamable HTTP, through an `httpx.AsyncClient` that carries the headers, with a 30 s timeout and a 300 s read timeout;
- SSE, through `sse_client(url, headers=…)`.

`_serve` initializes, lists every page of tools, sets `ready`, and waits until it is cancelled. Any
exception becomes `failure`, the innermost exception as "Type: message". [read: `shim.py:138-234`;
CI: `test_an_http_server_is_reached_with_its_headers[http, sse]`,
`test_calls_from_many_threads_and_under_nest_asyncio`]

**A call** is `run_coroutine_threadsafe(session.call_tool(..., read_timeout_seconds=call_timeout_s))`,
given up after `call_timeout_s` + 5 s. It maps outcomes as follows:
- `McpError` 408, or no result in time → `CALL_TIMEOUT`;
- `McpError` −32000, or anyio's closed, broken or end-of-stream errors → the connection is dead. That call and every later one raise `SERVER_STOPPED`; later ones raise it at once.
- any other `McpError` → `CALL_FAILED` with its message (§1 #9);
- anything else → `CALL_FAILED` with "Type: message".

The result follows §8.3:
- `isError` raises;
- `structuredContent` is unwrapped when both the tool's `outputSchema` and the content hold only `result`;
- all-text content becomes one string;
- any other content is a list of dumped blocks.

[read: `shim.py:245-296`; CI: `test_results_are_unwrapped_dicts_text_or_blocks`,
`test_a_call_that_never_answers_raises_after_its_timeout`,
`test_a_server_that_dies_fails_the_call_and_every_later_one_at_once`]

**What the REPL binds**:
- `Server` is callable as `name(tool, /, **arguments)`. It is unannotated, so deep_reasoner renders exactly that.
- `Server` gets one `McpTool` attribute per tool whose name, with non-word characters as `_`, is a free identifier and not a keyword.
- `McpTool` maps positional arguments onto the required parameters, then the optional ones.
- `Server`, `McpTool` and `Unavailable` return themselves from `__copy__` and `__deepcopy__`.
- `__cross_namespace__(src, dst)` raises `PermissionError(HANDOFF_REFUSED)` when a grant set is known and `dst` is outside it. The first bind (`src is None`) always passes.
- `Unavailable` answers a call, or any attribute not starting with `_`, with `McpToolError` and its sentence. An attribute starting with `_` is an `AttributeError`.

[read: `shim.py:299-395`; CI: `test_a_server_survives_fork`,
`test_a_stand_in_is_plain_to_deep_reasoners_seams`,
`test_handing_a_server_to_an_ungranted_namespace_is_refused`]

**The description** is §8.4's, with one addition: a boolean property schema is `Any` or `Never`
(§1 #1). [read: `shim.py:398-439`; CI: `test_the_description_is_what_8_4_says`]

**Plain `dr`** is the case where `SESSION` is `None`:
- `spec_from_block` reads each `env` name and each header's variable from `os.environ`.
- The shim connects, waits up to `connect_timeout_s` (default 10 s) and binds `Server(granted=None)`, which refuses no hand-off.
- If it cannot bind the server, it logs a structlog warning, `mcp.unavailable`, and returns a stand-in. The stand-in names any variable missing from the environment, on `NO_ANSWER` as on `COULD_NOT_START`.
- Without the `mcp` package, the stand-in says `pip install mcp`.
- A stdio server's stderr goes to `dr`'s own stderr, unredacted.
- A server that answers but cannot be described raises (§1 #11).

[read: `shim.py:487-519`; run: probe; CI: `test_an_exported_grant_runs_under_dr`,
`test_without_the_mcp_package_the_factory_returns_a_stand_in`,
`test_a_server_it_cannot_reach_becomes_a_stand_in_saying_why[crashes, hangs]`]

**The guard** remembers `os.getppid()` and starts the command with `subprocess.Popen` in its own
process group (the session `mcp` gave it). A daemon thread polls the parent every 0.5 s. Once the
parent changes, it sends `SIGKILL` to the group (`os.killpg(0, …)`). The guard exits with the
command's code, or 128 + N for a signal N. [read: `shim.py:522-541`; CI:
`test_the_guard_ends_its_server_when_its_parent_is_killed` (gone within 1.5 s),
`test_no_stdio_server_outlives_a_root_stop` and `…_a_closed_session` (within 2 s)]

### 4.7 What comes back: the run log, the notices and the seen cache

The worker emits `mcp.status` through D1's recorder. The pump logs it, and the encoder emits the
notices. For a live event, never a replay, the pump calls `remember_seen(home.root, run_id,
servers, now)`, which writes one file per `bound` server:
- the path is `$DR_HOME/mcp/<first 16 hex of sha256(server)>.json`;
- the content is `{v, server, tool, transport, at, run, count, told}`;
- it is written through `mkstemp` and `os.replace`, mode 0600 in a 0700 folder.

An `OSError` there is logged, not raised. `GET /mcp` reads the file from `library.path.parent`, which
is the same folder when the Library sits at `$DR_HOME/library.sqlite`. [read:
`acp/supervisor.py:209-226`, `mcp/wire.py:126-163`, `tools/routes.py:36`; CI:
`test_the_seen_cache_is_written_for_bound_servers`,
`test_the_seen_cache_round_trips_and_is_private`; the seen file is in both kept live homes,
`<home>/mcp/652f55016243bf1b.json`]

### 4.8 The frame

**The page** runs in Canvas's realm, and for the Tools tab only:
- `readMcpServers` sends `GET /api/settings`, without `X-Expose-Secrets`, and `GET /api/agent-profiles/deep_reasoner`, in parallel. Either failing gives `null`.
- `mcpServersFromSettings` reads `agent_settings.mcp_config` as a map from name to server:
  - the transport is stdio with a `command`, SSE with a `url` and `transport: "sse"`, otherwise HTTP with a `url`; a server with neither is skipped;
  - `env` and `headers` become their keys only;
  - `why_not` is `disabled` (`enabled === false`) or `not_in_profile` (refs not `null` and the name absent).
- The list rides in the frame URL as `mcp`.

[read: `page/context.ts:105-180`, `page/mount.ts:107-127`; CI: `context.test.ts`, `mount.test.ts`]

**`mcpRows`** joins Canvas's list with `GET /mcp` by server name. It returns Canvas's servers in
Canvas's order, then the grants gone from Canvas's list, sorted by server name. `changed` compares the
JSON of `snapshotOf(info)` and of the grant's snapshot, so the order of args, env names and header
names counts. With `mcp` null there are only the grants' rows, each in state `given`, and no new
grant can be made. [read: `ui/tools.ts:102-146`; CI: `tools.test.ts`]

**The editor**:
- A saved tool's namespace tick `PUT`s the **head's** `yaml`, source and version with the new `granted_in`, so no Check runs and no unsaved code is sent.
- **Save** sends the draft. A 422 with a report shows the report, and **Save anyway** shows under any report whose `can_save_anyway` is true.
- The source field is `PythonField`. It mounts CodeMirror from the `editor` chunk with the draft's text and owns the text from then on. A reset (**Discard draft**, **Reload**, a save) remounts it under a new key. If the chunk cannot load, it is D3's textarea.
- The draft is kept in `localStorage` under `dr-library.draft.tool.<name>`, or `….new` for a new tool.
- A built-in tool, which has no source, shows no source field.

[read: `ToolEditor.tsx:88-361`, `python.tsx`, `editor/python.ts`; CI:
`test_a_grant_tick_on_a_saved_tool_saves_without_unsaved_code`,
`test_the_editor_keeps_python_indentation`]

**An MCP row**:
- A first tick `PUT`s Canvas's snapshot with `base_version: 0`. A `409 conflict` there reads `MCP_NAME_TAKEN`; a `409 refused` shows the backend's sentence, which is the same one for a tool of your own.
- Later ticks resend the stored snapshot at the grant's version.
- **Update** resends Canvas's snapshot, or the stored one when Canvas's settings are unread.
- **Remove** is D2's `DELETE /tools/{name}`.

[read: `McpServerRow.tsx:72-120`; CI: the browser tests of §7.3]

---

## 5 · What D4 relies on

### 5.1 Where D4 sits

```text
f69bc73  D4 (v1-custom-tools)
  └ aa67f0a merges D3's d4e9cd3 (v1-decompositions-panel; D3's head dcbe6b3 adds documents only)
      └ D2 at 90044f0 (v1-library-store; D2's head cd0b60c is 54 commits on, 7 on its first parent)
          └ D1 at 21f4a8b (v1-dr-acp before its refactor)

D1 after its refactor: main 32c7f61 (PRs #1–#8), whose src/ equals v1-dr-acp's head f7a91f3
```

[run: `git merge-base`, `git rev-list`, `git diff --stat origin/v1-dr-acp origin/main -- src` (empty)]

D2's head adds two things D4 does not have:
- a fix in `library/library.py`: "the effective view refuses a stale head as materialize does, 422";
- merges of refactored D1 and of `main`.

D2's head differs from `d4e9cd3` in 29 source files (+145 −437). In `src/deep_reasoning/acp/`
the difference is 18 files (+125 −330), mostly D1's refactor: helpers moved, `detail_of` moved to
`runlog.py`, `Session.menu()` new. Six of the 18 are files D4 also edits: `agent.py`, `encoder.py`,
`runlog.py`, `session.py`, `supervisor.py`, `worker/runner.py`. [run: `git diff --stat`; read: the
diff]

Every D1 name D4 calls (§5.4) is present on `main` [run: `git grep`]. `git merge-tree --write-tree
f69bc73 origin/v1-library-store` reports no conflict [run]. The merged tree was not built or
tested.

Line numbers in §5.2–§5.6 are those at `f69bc73`. For D1's and D2's files they include D4's own
edits. For deep_reasoner and `mcp` they are those of the locked versions installed in the
worktree's `.venv`.

### 5.2 deep_reasoner (`d7334ae`, the locked revision)

| Relied on | Where |
|---|---|
| `make_tools` builds every block of `cfg.tools` once per run. A `factory_from` block is built by `load_tool_factory`, then `build(client, params)` without `factory` and `factory_from`, then the inline `Func` check. An unknown factory has an inline sentence too. Check mirrors this, and copies the two sentences into `tools/texts.py`. | `deep_reasoner/v2/cli.py:125-180` (branch `:152-165`, sentences `:158-164`, `:171-176`) |
| `load_tool_factory` resolves against `config_path`, wraps an import failure `from` its cause, raises "defines no" and "not a function" without one, and caches modules by path | `tools/base.py:329-407` (`_FACTORY_MODULES` `:318`; wrap `:379-385`; `:396-406`) |
| `TOOL_BUILDERS`, for `builtin` | `tools/base.py:285` |
| `load_cli_config(…, schema=V2Config)`; `build_client` needs no key for a loopback `base_url` | `config.py:454`; `config.py:249-265` |
| `Func`, and `func(name, value, description).describe()`, which is what the agent is told | `primitives.py:55`; `v2/messages.py:184, 217-224` |
| A namespace's tools are bound through `cross_namespace`, which calls a tool's `__cross_namespace__`; a name the registry lacks raises | `namespaces.py:379-386`, `:645-654` |
| `check_spawn`, `NamespaceSpawnError`, `NamespaceRegistry.resolve`, `load_namespaces_from_dir`, `ROOT`, `build_namespace_registry` | `namespaces.py:672-685`, `:657`, `:197`/`:272`, `:754`, `:56`; `v2/cli.py:289` |
| Namespace bindings override the framework's `subagent` and `run_all`, which is why §3.2's six names are reserved | `v2/agent.py:647, 673-675` |
| A fork deep-copies the REPL per binding, degrading to a copy or the reference | `repls/backends.py:104-125` |

[read]

### 5.3 `mcp` 1.30.0

| Relied on | Where |
|---|---|
| `stdio_client` starts the server in a new session, merges six inherited variables into its environment, closes stdin, waits 2 s, then ends the process group | `client/stdio/__init__.py:28-66, 106, 197-210, 256, 262-278`; `os/posix/utilities.py:15-45` |
| `ClientSession.call_tool(…, read_timeout_seconds=…)`; `list_tools(params=PaginatedRequestParams(cursor=…))` | `client/session.py:386-408, 524-532` |
| `streamable_http_client(url, http_client=…)`; `sse_client(url, headers=…)` | `client/streamable_http.py:619`; `client/sse.py:35` |
| A dead connection fails a request with `McpError` −32000; a read timeout is `McpError` 408 | `types.py:182`; `shared/session.py:296, 451` |

[read]

### 5.4 D1 (`21f4a8b`, inside D2's `90044f0`)

| Relied on | Where |
|---|---|
| `Start` over the control pipe; D4 adds `mcp_servers` | `acp/worker/protocol.py:10-20` |
| `Worker.build`: `load_dr_config`, the overrides, then `build_reasoner`. D4's `open_session` runs between them, and `build_failed` covers what it raises. | `acp/worker/runner.py:126-162, 164-171` |
| The recorder's `emit(kind, **fields)` | `acp/worker/recorder.py:189` |
| `RunHandle.start`, which sends `Start`; the pump, which logs each event before D4's seen cache is written | `acp/supervisor.py:87-155, 199-226` |
| `Session.mcp_servers`, kept from `session/new` and `session/load`; `_start_run`'s one `to_thread` | `acp/session.py:107, 188-224`; `acp/agent.py:131, 162` |
| The encoder's root message form (`_text`), the `RunEvent` union, `Home.root` | `acp/encoder.py:99`; `acp/runlog.py:20, 166, 175` |
| The test harness: `DrAcp`, `FakeOpenAI`, `ShimConnection`, the schema check of every message | `tests/acp/harness.py:138` (`open_session`), `:149` (`ask`), `:154` (`run_log`) |

[read]

### 5.5 D2 (`90044f0`)

| Relied on | Where |
|---|---|
| Tool rows; `put_tool`; `granted_in` as the exact set; `base_version` rules (0 with a head is `409 conflict`) | `library/library.py:460-475, 245, 557-575` |
| An unchanged write makes no version | `library/library.py:192-199` |
| `state()`, `tools()` | `library/library.py:288, 316` |
| `shapes.validate_tool`, `canonical_yaml`, `tool_file`, `TOOL_DIR`, `deep_reasoner_build` | `library/shapes.py:190, 48, 185, 31, 60` |
| `materialize` writes `tools/<name>.py` beside `main.yaml`, with `factory_from` set | `library/configdir.py:99, 160-162` |
| The error family (`LibraryError`, `LibraryValidationError`, `LibraryRefused`, `LibraryBadRequest`) and `ToolRecord` | `library/records.py:158-221, 59` |
| `_parse` (private; D4 adds its `sentence` argument), `json_route` (moved to module level by D4), `create_app`, the guard, the error handler | `library/api.py:154, 208, 225, 100, 400` |

[read]

### 5.6 D3 (`d4e9cd3`)

| Relied on | Where |
|---|---|
| `NamespaceChecklist`, with inherited grants fixed | `canvas-app/src/ui/components/pickers.tsx:43` |
| `CodeField` (the fallback and the YAML field), `Banner`, `ConfirmRow` (D4 adds `confirmTestId`) | `ui/components/fields.tsx:24, 69, 85` |
| `drafts.ts`, `load.ts` (`attempt`, `useLoaded`, `resolved`, `OnBackendLost`), `SafetyNotice`, `stringifyYaml` | `ui/drafts.ts:25-39`; `ui/load.ts:9-74`; `ui/components/notices.tsx:13`; `ui/yaml.ts:20` |
| The frame protocol and the page's mount step 2 | `shared/protocol.ts`; `page/mount.ts:104-127` |
| `ui_routes`, which serves `assets/editor.js` like any built asset | `src/deep_reasoning/library/ui.py:26` |

[read]

### 5.7 The SDK fork (read, not a dependency)

The bridge forwards each enabled server of the profile's filtered `mcp_config` as ACP
`mcpServers`, at `session/new` and `session/load`. Stdio is always forwarded; HTTP and SSE only
when advertised. Secrets travel in plain text, and a header-compatible `auth` travels as extra
headers. [read: `openhands-sdk/openhands/sdk/agent/acp_agent.py:717-821` at `91430aa`]

---

## 6 · Wiring and size

### 6.1 Wiring

- **`pyproject.toml`**:
  - `mcp>=1.28,<2` joins the runtime dependencies;
  - ruff's `extend-exclude` adds `tests/mcp/fixtures`;
  - `as_built/` is in the sdist's `exclude` beside `docs/`.

  Pytest's `testpaths`, the wheel's `packages` and CI's ruff (`src`, `tests`) leave `as_built/`
  out; prettier runs inside `canvas-app/` only. [read]
- **D1's files**:
  - `AGENT_CAPABILITIES` flips both MCP flags;
  - `McpStatus` joins the `RunEvent` union, and the encoder has a `case` for it;
  - `texts.py` gains the three notices and `mcp_notice`;
  - `Start.mcp_servers` is new;
  - `RunHandle.start(…, mcp_servers=())` passes the specs, and the pump calls `_remember`;
  - `Session._materialize` computes the specs;
  - `Worker.build` calls `open_session`.

  D1's tests change too: `DrAcp.open_session(cwd, mcp_servers=())`, the capability test renamed
  `test_initialize_advertises_load_close_and_http_and_sse_mcp`, the 18 golden recordings' first
  line, and the notice test in `test_encoder.py`. A shared helper, `tests/processes.py` (`alive`,
  `running_after`), is new. [read: `git diff d4e9cd3 f69bc73`]
- **D2's `api.py`**:
  - `_ToolBody.accept_check_failure: bool = False`;
  - `_parse` takes the sentence to lead with;
  - the route closure becomes the module-level `json_route`, with no change in behaviour;
  - `put_tool` calls `require_check` first;
  - `create_app` appends `*tool_routes(lib)`, and imports D4's modules inside the function.

  `tests/library/test_ui.py` asserts that `editor.js` is built and that `app.js` references it. [read]
- **D3's project**:
  - `tabs/tools.tsx` is extended, and `api.ts`, `types.ts`, `texts.ts`, `shared/protocol.ts`, `page/context.ts`, `page/mount.ts` and `fields.tsx` are edited;
  - `components/`, `editor/` and `tools.ts` hold new files;
  - `vite.config.ts` emits the `editor` chunk;
  - `package.json` adds five pinned CodeMirror packages.

  [read]
- **CI.** `ci.yml` is unchanged. D3's `canvas-app` job runs `tsc`, prettier, vitest, the build, a check that the committed build is what a fresh build gives, and `pytest -m browser tests/canvas_app`. `live.yml` runs `pytest -m live` and keeps a failed run's homes (§1 #5). [CI; read]

### 6.2 Size

These are the lines D4 adds over D3's finished head `d4e9cd3` (`git diff --numstat d4e9cd3
f69bc73`, added column), by design §13's parts. [run]

| Part | Code | Tests |
|---|---|---|
| Check: `check.py` 392, `check_child.py` 128, `texts.py` 100 | 620 | 553 (`test_check.py` 474, fixtures 79) |
| Routes and the gate: `routes.py` 80, D2's `api.py` +70 (−46) | 150 | 341 (`test_routes.py`) |
| MCP: `shim.py` 541, `session.py` 244, `wire.py` 163, `grants.py` 98 | 1,046 | 1,291 (`test_shim` 412, `test_session` 341, `test_grants` 172, `test_wire` 149, fake servers 217) |
| D1's files | 101 (−7) | 570 (`tests/mcp/test_acp.py` 495, D1's test files 45, `tests/processes.py` 30) |
| Export and live tier | — | 235 (`test_export.py` 67, `tests/mcp/test_live.py` 89, `tests/tools/test_live.py` 79) |
| The frame: 15 files in `canvas-app/src/`, `vite.config.ts`, `package.json` | 1,475 (−30) | 788 (vitest 433, browser 352, `test_ui.py` 3) |
| `pyproject.toml`, the two packages' `__init__.py` | 7 | |
| **Total** | **3,399** | **3,778** |

Not counted:
- `tests/mcp/fixtures/shim_v1.py`, 539 lines;
- the two lock files, `uv.lock` +137 and `package-lock.json` +136;
- the 18 changed lines of D1's golden recordings;
- `live.yml` +18;
- the built assets.

With tests, D4 is 7,177 lines; at the workspace's ~300 lines an hour, that is about 24 h at
Gate C. Since v3 the code grew by 2 lines and the tests by 92 (§1 #7).

---

## 7 · Experiments and evidence, as measured

D4's design names these:
- E9, your own tools and MCP servers (§10.2);
- the live tier, spec §4 layer 5 (§10.5);
- E10 with MCP servers bound, E12's MCP step and the cross-repository forwarding test (§10.6, §11.4), none of them built in D4.

### 7.1 The runs

| Run | Conditions | Commit | Result |
|---|---|---|---|
| CI [37157785695](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37157785695), job `test` | ubuntu-latest, Python 3.12.3, pytest 9.1.1; `ruff check src tests` and `ruff format --check src tests` first | `f69bc73` | **683 passed, 79 deselected, 466.70 s**. D4's directories: `tests/mcp/` 80, `tests/tools/` 69 (the two live tests deselected). Ruff: "131 files already formatted" [CI] |
| the same run, job `canvas-app` | Node 22.23.3; `npm ci`, typecheck, prettier, vitest, build, committed-build check, then Playwright 1.56.0 Chromium against a real `dr-library serve` | `f69bc73` | vitest **190 passed, 1 skipped** (11 files); build `app.js` 169.03 kB, `editor.js` 348.48 kB (gzip 117.55 kB), page 8.52 kB; committed build matches; browser **72 passed, 1 skipped, 169.40 s**. `test_tools_tab.py` has 20 cases, 17 of them D4's; the skip is D3's `test_the_notice_is_d5s_sentence_with_the_cap`, "D5's dr_app is not installed" [CI] |
| live [37157799600](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37157799600) | `workflow_dispatch`, `OPENAI_API_KEY` secret, `pytest -m live -v -rA --basetemp=…`; the starter profile's model, gpt-6-luna (the model the kept homes at `7eb7812` record) | `f69bc73` | **6 passed, 628 deselected, 120.49 s**. D4's: the MCP test ≈21.6 s, the tool test ≈36.7 s (between successive PASSED lines) [CI] |
| live [37157801762](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37157801762) | the same, dispatched 2 s later | `f69bc73` | **6 passed, 628 deselected, 79.40 s**. MCP ≈15.9 s, tool ≈14.9 s [CI] |
| local, default suite | this machine, 4 cores, load average 10–24 from other agents' suites; `DR_BETA_CHECKOUT=/home/user/deep_reasoner_beta uv run pytest` | `f69bc73` | **683 passed, 79 deselected, 1053.64 s**, no failure, so nothing was rerun. By directory: `tests/acp` 233, `tests/library` 301, `tests/mcp` 80, `tests/tools` 69. D4's 149 took 243.0 s; the slowest were `test_check_and_make_tools_agree[hang]` 14.79 s and `test_a_hanging_factory_is_stopped_at_the_build_limit` 12.51 s [run] |
| local, browser | `CI=true uv run pytest -m browser tests/canvas_app`, Playwright 1.56.0 with the preinstalled Chromium | `f69bc73` | **72 passed, 1 skipped, 290.69 s**, the same skip as CI. `test_tools_tab.py`: 20 passed in 85.7 s, the slowest `test_a_hanging_factory_shows_the_limit` at 15.8 s [run] |
| local, frame | `npm ci`; `npx vitest run` with `DR_BETA_CHECKOUT`; `npx tsc --noEmit`; `npx prettier --check .`; `vite build` of both configs into a scratch folder, then `diff -r` with the committed files | `f69bc73` | vitest **190 passed, 1 skipped**; `tsc` and prettier exit 0; the build is byte-identical to the committed `ui/` and `dist/` [run] |

The live record before `f69bc73`, for D4's two tests. [CI: each run's log; the artifacts of
37153297958]

| Run | Commit | Task | The tool test | The MCP test | All |
|---|---|---|---|---|---|
| [37106223637](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37106223637) | `965f318` | bare | passed | passed | 6 of 6, 81.33 s |
| [37145903109](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37145903109) attempt 1 | `aa67f0a` | bare | passed | **failed**: `exhausted`, ≈49.5 s | 5 of 6, 250.55 s |
| the same, attempt 2 | `aa67f0a` | bare | passed | **failed**: `failed`, ≈9.1 s | 5 of 6, 75.91 s |
| [37149393726](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37149393726) | `7eb7812` | bare | passed, ≈17.4 s | passed, ≈9.5 s | 5 of 6: D1's `test_live_the_stream_rebuilds_deep_reasoners_tree_and_the_root_pays_for_all` failed (`{1: (None, 3), 2: (1, 0), 3: (1, 0)} == {1: (None, 3)}`) |
| [37153297958](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37153297958) attempt 1 | `7eb7812` | bare | **failed**: `exhausted`, ≈55.7 s | passed, ≈9.8 s | 5 of 6, 118.74 s |
| the same, attempt 2 | `7eb7812` | bare | **failed**: `exhausted`, ≈63.8 s | passed, ≈9.1 s | 5 of 6, 130.26 s |
| 37157799600, 37157801762 | `f69bc73` | names the tool or server | passed, passed | passed, passed | 6 of 6, 6 of 6 |

Asked bare, each D4 test passed 4 of 6 times. With the task naming the tool or the server, each
passed 2 of 2. Run 37145903109 kept no artifact, so its two MCP failures have no record beyond the
assertion. [CI]

To reproduce:
- E9 and the rest of the deterministic suite: `DR_BETA_CHECKOUT=<deep_reasoner_beta at d7334ae> uv run pytest tests/tools tests/mcp`.
- The panel: `CI=true uv run pytest -m browser tests/canvas_app/test_tools_tab.py`, and `npx vitest run` in `canvas-app/`.
- The live tier, which is paid: `OPENAI_API_KEY=… uv run pytest -m live tests/tools/test_live.py tests/mcp/test_live.py`, or dispatch `live.yml`.

### 7.2 E9 · your own tools

**Conditions.** `check_tool` ran from a probe script on the committed fixtures, under the default
limits (30/10/10 s), one at a time, at 22:51 UTC with the machine at load average about 10.6. Each
row's null is "a failure that shows only at run time". [run]

| Case | Outcome | Save | Wall time | What the report says |
|---|---|---|---|---|
| `word_count.py`, tried `word_count("one two three")` | `built` | yes | 2.24 s | told `` - `word_count(text: str) -> int` `` / `word_count(text) -> int: number of words in text.`; example `'3'` |
| `not_func.py` | `not_func` | no | 1.98 s | `make_tools`' sentence: "tool 'word_count': make in tools/word_count.py returned function, not a Func. …" |
| `word_count.py` with `factory: mkae` | `bad_factory` | no | 2.12 s | "tool 'word_count': 'tools/word_count.py' defines no 'mkae'. It defines: make, make_broken. Known built-in factories: claude_code, kg, llm, rag, safe_url." |
| `import_error.py` | `import_failed` | no | 2.02 s | "tool 'word_count': importing 'tools/word_count.py' raised ModuleNotFoundError: No module named 'yaml_x'" |
| `env_at_build.py` | `raised` | anyway | 2.28 s | "tool 'word_count': make raised KeyError: 'D4_TOKEN'", with the frame `tools/word_count.py", line 7, in make` |
| `exits.py` (`os._exit(3)`) | `raised` | anyway | 2.09 s | "tool 'word_count': the Check process ended (exit code 3) while building the tool." |
| `prints.py` (1 MB printed) | `built` | yes | 1.93 s | told `` - `len(obj, /)` `` / `length`; `printed` holds the last 2,000 characters |
| `calls_model.py` | `built` | yes | 2.32 s | The factory calls the model, catches the error and builds; told `` - `<lambda>()` `` / `APIConnectionError: Connection error.` |
| `def make(` | `syntax` | no | 0.00 s | "tool 'word_count': tools/word_count.py line 1: '(' was never closed" (no process) |
| `factory: rag`, no source | `builtin` | yes | 0.00 s | `BUILTIN` (no process) |
| `word_count.py` named `run_all` | `invalid` | no | 0.00 s | `RESERVED_NAME` (no process) |
| `hang.py` | `timeout` | anyway | **11.75 s** | `BUILD_TIMEOUT`, "longer than 10 s" |

A tool that builds is checked in about two seconds, most of it the throwaway process importing
deep_reasoner. The static stage answers at once. A hanging factory is answered at the build limit,
plus the time to start.

**Check and `make_tools` agree** [CI and run: `test_check_and_make_tools_agree`, 8 cases: works,
`not_func`, misspelled, `import_error`, `hang`, `env_at_build`, `prints`, `exits`]. For each
fixture, Check's `ok` equals whether deep_reasoner's own `make_tools` builds the same one-tool
config in a subprocess with `check_env` (10 s limit). Where deep_reasoner words the failure
(`not_func`, misspelled, `import_error`), the sentences are equal. Both sides run without secrets,
so `env_at_build` agrees by failing on both. The test says nothing about what a conversation, which
has the secrets, would build. `spawns.py` is not among the eight; `test_nothing_a_stopped_tool_started_is_left_running`
covers it (the `sleep 3600` it started is gone within 1 s).

**Through the API and a conversation** [CI]:
- `test_routes.py::test_a_tool_that_cannot_build_is_not_saved[not_func, misspelled, import_error]`: 422 `check_failed`, nothing stored;
- `test_a_checked_tool_is_saved_with_its_grants`;
- `tests/mcp/test_acp.py::test_a_tool_saved_through_the_api_is_built_and_called_in_the_next_conversation`: a real `dr-acp` with `FakeOpenAI`; the cell's output is `4`, and the first model request carries `` - `word_count(text: str) -> int` ``;
- the browser tests `test_a_tool_that_cannot_build_shows_why_and_cannot_be_saved[3]`, `test_a_hanging_factory_shows_the_limit` and `test_a_raising_factory_offers_save_anyway`.

The hanging-factory test asserts `10 s ≤ took < ready + 10 s + 1 s`.

### 7.3 E9 · MCP servers

The fake servers are real FastMCP (or `mcp` low-level) servers of the project's own, run as scripts:
- `echo_server.py`: stdio, `--http PORT` and `--sse PORT`, with eleven tools;
- `hang_server.py`: never reads its stdin;
- `crash_server.py`: prints its token and exits 1;
- `odd_server.py`: one tool whose properties come from `ODD_PROPERTIES`;
- `loud_server.py`: prints 1 MB, then 256 KB per call;
- `catalog_server.py`: used by the live tier.

Every row below is [CI] at `f69bc73` and [run] locally (§7.1).

| Null | Test | Measured condition |
|---|---|---|
| a crashing server blocks the session or takes the worker down | `test_session.py::test_a_server_that_exits_at_start_is_failed_with_its_stderr_redacted[whole, split]`; `::test_a_server_open_session_cannot_bind_fails_alone_and_the_others_bind[3]`; `test_acp.py::test_a_server_that_crashes_at_start_is_reported_and_the_run_answers`, `::test_a_server_that_crashes_mid_run_fails_the_call_and_the_run_goes_on` | The detail is exactly `McpError: Connection closed; it printed: "invalid token [redacted]"`, and the log reads the same. A server whose log cannot open, whose block has no number, or whose tool cannot be described fails alone, and `echo` still answers. The notice comes first, then the answer. After a mid-run crash, the failing call and the next one both raise `SERVER_STOPPED`, and the next prompt is answered. |
| a hanging server blocks the session | `test_session.py::test_servers_connect_at_once_and_a_silent_one_is_given_up_at_the_deadline`; `test_acp.py::test_session_new_does_not_wait_and_the_first_answer_waits_at_most_the_deadline`; `test_shim.py::test_a_call_that_never_answers_raises_after_its_timeout`; `test_session.py::test_a_server_given_up_is_ended_within_three_seconds` | Three silent servers at 1.5 s are all `no_answer` with `seconds` 1.5, decided in 1.5–3 s. `session/new` starts no server. With a 2 s grant, `mcp.status` comes 2–5 s after `worker.ready`, and the first root text is `mcp_no_answer("silent", 2)`. An abandoned server is gone within 3 s. |
| a server that prints a lot blocks on its pipe | `test_session.py::test_a_server_that_prints_more_than_a_pipe_holds_answers_and_its_log_is_redacted` | 1 MB at start and 3 × 256 KB: the server is `bound`, three calls answer, and the log equals every printed line with the token as `[redacted]` within 10 s |
| a server not granted to the conversation's namespace is in its REPL | `test_acp.py::test_a_server_granted_elsewhere_is_not_in_this_agents_repl_or_prompt`, `::test_a_sub_agent_spawned_into_a_granted_namespace_gets_it`, `::test_a_grant_reaches_a_child_namespace`, `::test_handing_a_server_to_an_ungranted_namespace_is_refused`; `test_session.py::test_a_server_granted_nowhere_is_not_started`, `::test_a_server_granted_only_where_spawning_is_not_allowed_is_not_started` | Granted to `course_advisor` with the conversation in `router`: a cell's `'echo' in dir()` prints `False`, and the first model request lacks `echo(tool`. A sub-agent spawned into the granted namespace, and a child namespace, both reach it. A hand-off outside the grant raises `PermissionError` with `HANDOFF_REFUSED`. |
| a server outlives its run | `test_acp.py::test_no_stdio_server_outlives_a_root_stop`, `::test_no_stdio_server_outlives_a_closed_session`; `test_shim.py::test_the_guard_ends_its_server_when_its_parent_is_killed` | A cell in `while True: pass`, then a root Stop: no fake server runs 2 s later. A `SIGKILL`ed parent: the server is gone within 1.5 s. |
| a server's secret leaks | `test_acp.py::test_server_secrets_never_reach_the_run_log_or_the_transcript`; `test_wire.py::test_a_run_gets_only_the_specs_its_blocks_name` | The token is absent from `events.jsonl`, the ACP lines, `worker.log` and `mcp-<alias>.log` |

**In real runs** [CI: the homes run 37153297958 kept, both attempts, at `7eb7812`]:
- The MCP test's run log goes `run.start`, `prompt.start`, `worker.ready`, `mcp.status`, `agent.start`.
- `mcp.status` is `catalog` `bound`, with 1 tool, in 0.99 s and 0.949 s.
- The first cell is `catalog.prerequisites(course="ZQ-417")`, and the prompt ends `answered`.
- No file in either home, which includes `llm_calls.jsonl`, `worker.log`, `mcp-catalog.log`, `transcript.jsonl` and `library.sqlite`, holds a string of the token's form (`catalog-` and 24 hex) [run: `grep -r`].

**Contracts** (design §10.1, layer 2). Every test that drives `dr-acp` uses D1's harness. The harness
checks each message against ACP's schema and asserts, on exit, that there was no violation and that
stdout held only JSON-RPC lines. So the notices are schema-checked in `test_acp.py`'s 16 cases and in
both live tests. [read; CI]

**Under plain `dr`** [CI: `test_export.py::test_an_exported_grant_runs_under_dr`]:
- `dr-library export` writes the export;
- then `dr <dir>/main.yaml` runs with `FakeOpenAI` scripted to call `echo.echo("hi")` and with `ECHO_TOKEN` in the environment;
- it exits 0, and the cell's output is `hi`.

### 7.4 Live tier (gpt-6-luna)

Both tests write through `create_app` and `TestClient`, so the gate and a real Check run. They then
drive a real `dr-acp --home` over stdio with D1's harness and the starter profile.

| Test | Asserted | At `f69bc73` |
|---|---|---|
| `tests/tools/test_live.py::test_live_a_tool_written_in_the_library_is_used_by_the_agent` | `PUT /tools/course_credits`, granted to `root` → 201; a Check on the same body → `built`. The task "Use course_credits to find how many credits course ZQ-417 is." → outcome `answered`, and the last root text contains `7`; a cell's code calls `course_credits(` and its output contains `7`. | passed in both runs [CI] |
| `tests/mcp/test_live.py::test_live_an_mcp_server_granted_to_the_namespace_is_used_by_the_agent` | `PUT /mcp/catalog` (stdio, `CATALOG_TOKEN` by name, granted to `root`) → 201; `session/new` forwards `McpServerStdio` with a random token. The task "Use the catalog server to find what a student must finish before ZQ-417." → `answered`, and the last root text contains `ZQ-101`; `mcp.status` is `[("catalog", "bound")]`; a cell calls `catalog.prerequisites(`; the token is in neither `events.jsonl` nor the ACP lines. | passed in both runs [CI] |

**The two failed attempts of the tool test** at `7eb7812` asked the bare question. Each home holds
30 model calls of gpt-6-luna. The system prompt described `` - `course_credits(code: str) -> int` ``
and its description. No reply held a `<repl>` block. deep_reasoner answered each reply with "Your
response did not contain a `<repl>...</repl>` block. Please include one." The agent ended
`exhausted` at iteration 30. The replies, as logged:
- attempt 1: 22 empty and 8 "4 credits.";
- attempt 2: 12 empty, 17 "4 credits." and 1 "Course ZQ-417 is worth 4 credits.".

[run: counted from `llm_calls.jsonl` in the kept homes] Commit `933ac08` counts attempt 1 as 21
empty and 9 "4 credits.". Over the 29 replies echoed in the last request I count 21 empty and 8.

Neither run records the token cost in its log. I ran no live test.

### 7.5 Named in the design, not run by D4

- **E10 with MCP servers bound** (§11.4) is D5's run.
- **E12's MCP step** (§11.4) is a proposal for D5.
- **The cross-repository forwarding test** (§10.6, `tests/crossrepo/test_mcp_forwarding.py`) does not exist on this branch. The bridge-to-`dr-acp` forwarding is exercised only with a hand-built `McpServerStdio` (the live test and `test_acp.py`) and with dicts (`test_wire.py`).

---

## 8 · What I could not verify

1. **Forwarding through a real agent-server.** The tests build by hand the ACP shapes `dr-acp` receives. The bridge's `_mcp_config_to_acp_servers` was read at `91430aa`, not run. `forwarded_specs` accepts both a missing and a `"stdio"` `type`. [read]
2. **The frame against real Canvas settings.** `mcpServersFromSettings` was tested against hand-written settings JSON. The shape, `MCPConfig` as a map from name to server and `profile.mcp_server_refs`, was read in the SDK fork. So was the `auth` header of §1 #12. [read]
3. **The live tier** ran in CI only. Its token cost is not in the logs. The cause of run 37145903109's two MCP failures, `exhausted` and then `failed`, is not recorded anywhere. D1's tree-test failure in 37149393726 is, per the brief, fixed in D1; I did not check that fix.
4. **macOS.** Nothing ran on macOS: not the guard's `getppid` polling, not `check_env`'s password database, and not Check's process-group kill.
5. **Remote servers** were exercised only against the local fake servers, over streamable HTTP and SSE on loopback. OAuth-protected servers and slow networks were not.
6. **Load.** One Check at a time, and at most three servers per run, are tested. Two Checks at once, or many servers, were not run. The worst case of a 50 s Check through the agent-server's bridge, which has no read timeout, was read in the design, not run.
7. **The ungated paths.** `Library.put_tool` and `dr-library import` store a tool that cannot build, which then stops every conversation, because `make_tools` builds every block. This is design §3.5 and §14 item 4. [read]
8. **D4 on the current stack.** The trial merge with D2's head (which holds `main`) is textual only. No suite ran on the merged tree. [run: `git merge-tree`]
9. **The read claims that matter most:**
   - §4.4's statement that secrets never enter the worker's environment. The tests check the run log, the transcript, `worker.log` and the server's log, not `/proc/<worker>/environ`.
   - §4.7's assumption that `library.path.parent` is `$DR_HOME`.
   - §1 #9 and #10, which no test provokes.
