# D4 · Custom tools and MCP servers, as built

**TASK-9** · Cartographer · revision 3 · 2026-10-04 · the code at `3129da9` (head of `v1-custom-tools`; this file
is on `as-built/d4-r3`) · checked against design v5 with B30 (`docs/design/d4-custom-tools.md`, last changed in
`60f1d00`) · deep_reasoner_beta `d7334ae`, `mcp` 1.30.0 and agent-client-protocol 0.12.1, as `uv.lock` pins them ·
SDK fork `91430aa`, read only (the two files cited are unchanged at the fork's head `1f2b52d`).

This revision replaces r2 (`2353fe6`: the code at `f69bc73`, against design v3). It is Gate C's map of the code
after three things: Michael's ruling (b) (design B30), the merges of D3's and D2's refactored heads, and D4's
literate refactor (12 commits, `be131ce` … `dcd84af`). D4's code is `src/deep_reasoning/tools/`,
`src/deep_reasoning/mcp/`, the Tools tab in D3's `canvas-app/` with its built files, and `tests/tools/` and
`tests/mcp/`. It also edits D1's, D2's and D3's files (§6.1).

**Evidence marks.** Every claim carries one.
- **[run]**: executed on this machine at `3129da9`. That covers the suites and builds of §7.1, the probe scripts
  and mutation probes of §7.4 and §7.5 (not committed), and `git`.
- **[CI]**: read from GitHub's logs of the runs in §7.1. I ran no live test and made no paid model call.
- **[read]**: read in the code and **not executed**. This is weaker evidence than [run]. §8 lists the read claims
  that matter most.

**Reading order:**
- §1: the divergences from the design.
- §2–§4: the map, with routes into the code.
- §5: what D4 stands on, and what stands on D4.
- §6: wiring and size.
- §7: tests and evidence, including what the refactor left unpinned (§7.4).
- §8: what I could not verify.

---

## 1 · Divergences from design v5 and B30

No Changelog entry is linked to TASK-9, so none carries a drift line for it. The newest entries are the merges of
D1, D2, S1, S2 and C3 on 2026-10-03 and 2026-10-04 [read: the Notion Changelog]. Everything below was found in
the code or the runs.

The design says it matches the build at `f69bc73` (its line 16). Since then `v1-custom-tools` has gained:
- B30's two commits, `87f24e5` and `e32bc3d`;
- five merges of D3: `fd0fc84`, `a87e898`, `3f85560` and `e866563` bring D3's UI changes, and `3129da9` brings
  D3's `73c6425`;
- `01abb88`, the merge of D3's refactored head together with D2's;
- the 12 refactor commits.

Of D4's Python, only `tools/` changed. `src/deep_reasoning/mcp/` is byte-identical to `f69bc73` [run: `git diff`].

### 1.1 Built otherwise than the design says

| # | Design says | Built | Where | Reason recorded |
|---|---|---|---|---|
| 1 | B30: the frame adds the header names that "a remote server's `auth`" sends to that server's `headers`. | `mcpServersFromSettings` adds them for every transport. For HTTP and SSE, B30 holds as written. For stdio, see #10. [run: probe, §7.5] | `canvas-app/src/page/context.ts:126-140, 168-173` | `e32bc3d`'s title says "a remote server's auth"; it records nothing about stdio |
| 2 | §7.1, §7.2, §11.2, B12, B16, A.2, A.5: `tool_routes(library)`, built with a module-level `json_route` that D4 moved out of `create_app`. | `tool_routes(library, route)` takes D2's own `route` closure. `json_route` exists nowhere. D4's edit to `api.py` is now +17 −5, where it was +70 −46. `tools/routes.py` still imports D2's private `_parse`, so `create_app` still imports D4's modules inside itself (B12's cycle, now through `_parse`). [read; run: `git grep json_route` is empty] | `tools/routes.py:37-86`; `library/api.py:208-210, 316-327, 376` | `01abb88`: D2's refactor deleted the `_dump` that `json_route` called; resolved with the Scout's cut |
| 3 | §3.3: `tmp = mkdtemp("dr-check-")`, removed after the child is reaped. | `tempfile.TemporaryDirectory(prefix="dr-check-", ignore_cleanup_errors=True)`. That is still `mkdtemp` underneath, so the folder is still mode 0700, and it is removed on every path, after `_end`. One difference: CPython 3.12's cleanup resets permissions and retries where the old `rmtree(ignore_errors=True)` gave up. [read: `check.py:182-218`, the 3.12.3 stdlib; CI: `test_the_temporary_folder_is_removed[word_count, hang]`] | `tools/check.py:182-184` | `eb19663`: the Scout's adopted cut |
| 4 | §3.3: the child reports `ready`, `loaded`, `built` or `failed`, `example`, `done`. | It reports `ready`, then `built` or `failed`, then `example` (only with `--example`). The supervisor never awaited `loaded` or `done`, and a report is built from the same lines. One consequence: the phase filter in `_Reports.get` now skips no line (§7.4, M1). [read; run: M1] | `tools/check_child.py:29-54` | `e5583e6`: "written for no reader" |
| 5 | §7.4, A.6: `ui/tools.ts` exports `RESERVED_NAMES`, `McpSnapshot = Omit<McpGrantBody, …>`, `snapshotOf(info)`, `grantSnapshot(grant)` and `inheritedGrants`. | `McpSnapshot` is an interface in `ui/types.ts`, and `McpGrant` and `McpGrantBody` extend it. `snapshotOf(server, target)` takes a target from Canvas's settings or from a grant, and `grantSnapshot` is gone. `inheritedNotes(tool, effective)` returns the note text (`INHERITED_ROW`), so both components pass it as it is. `RESERVED_NAMES` is module-private. The Tools tab's markup is unchanged in 28 states (§7.4). [read; run: DOM probe] | `ui/types.ts:175-191`; `ui/tools.ts:9-16, 75-78, 125-136` | `be131ce`, `58dd18f` |
| 6 | §7.1, §10.3, B15: no conftest under `tests/tools/` or `tests/mcp/`; `test_put_mcp_refuses_a_stdio_grant_without_a_command`. | `tests/tools/conftest.py` holds `source(fixture)` and the `no_process` fixture (it was `no_check` in `test_routes.py`). `tests/mcp/conftest.py` holds `put_grant(lib, alias, granted_in, *, block=None, **fields)`. The test is renamed `test_put_mcp_refuses_a_grant_without_its_command_or_url`. `test_acp.py`'s conversations go through a `converse` fixture. Every other test name the design gives exists. [run: name comparison; read] | `tests/tools/conftest.py`, `tests/mcp/conftest.py`, `tests/mcp/test_acp.py:87-113` | `488c580`, `58e9be4`, `5363cc8`, `c62d30f` |
| 7 | B16, §13 and the Gate B section: 3,399 lines of code and 3,778 of tests. | **3,309 and 3,728**, measured the design's way; 3,327 and 4,287 measured the task row's way (§6.2). [run] | — | the refactor, B30, and the route cut |
| 8 | The Gate B section: the evidence is at `f69bc73`, and the live tier has six tests. B11: 18 golden recordings change one line. | CI and the live tier are green at `3129da9` (§7.1). The live job runs seven tests: the merges brought in D1's `test_live_claude_code_on_sonnet_…` (`2a15388`). There are 20 golden recordings, each with the `http`/`sse` line: the merge added `unanswered.flat` and `unanswered.native`. [CI; run: `git diff --numstat`] | `tests/acp/golden/` | evidence, not build |
| 9 | §7.4 and B22: `app.js` is 169 KB (169,027 B). | `app.js` is 167,192 B, `editor.js` 348,475 B (unchanged) and the page bundle `dist/index.js` 9,358 B. Over D3's head (`app.js` 150,631 B, page 7,517 B), D4 adds 16,561 B and 1,841 B. [run: `git cat-file -s`, a fresh build] | `src/deep_reasoning/canvas_app/` | the merges and the refactor (−423 B on `app.js`) |

### 1.2 Stale lines in the design

These are the ones the brief named, each confirmed [read]:
- line 16, "Matches the build at `f69bc73`";
- the Revisions list, which has no B30 entry;
- the Gate B section's third ruling, "Nothing changes in code until Michael rules" (line 94);
- §7.5's v5 note (lines 1472-1474), that an entry's `auth` is not read;
- §14 item 6's v5 note (line 1989).

Beyond those, I found these:
- §3.3's `mkdtemp`, `loaded` and `done` (lines 549, 582, 589);
- `json_route` (lines 1103-1108, 1159, 1370, 1397, 1864-1866, 2327-2328, 2605-2610);
- `ui/types.ts` (line 1435) and `ui/tools.ts`'s exports (lines 1068, 1438-1439, 1737, 2749, 2751, 2780-2782);
- the test name of #6 (lines 1147, 1701);
- "18" golden recordings (lines 72, 1168).

### 1.3 Behaviour the design does not state

| # | Found | Where | Evidence |
|---|---|---|---|
| 10 | **A stdio server whose Canvas entry has `headers`, or (since B30) an `auth` that sends a header, reads as changed forever.** Its `McpServerInfo.headers` is non-empty. `mcp_block` stores only `command`, `args` and `env` for stdio, so `GET /mcp` answers `headers: []`. `mcpRows` therefore marks the row `changed` and it shows **Update**. Update `PUT`s the same block, D2 writes no version for an unchanged row, and the row stays changed. The SDK fork's `MCPServer` accepts `headers` and `auth` on a stdio entry. The bridge forwards neither to a stdio server, so a conversation is unaffected. | `page/context.ts:168-173`; `mcp/grants.py:76`; `ui/tools.ts:96-100`; SDK fork `mcp/config.py:497-563` | [run: `PUT /mcp` of a stdio body with `headers: ["Authorization"]` → the block has no headers, `GET /mcp` → `[]`, the resend → 200 at version 1; `mcpRows` on the frame's reading of `{command, auth: bearer}` and of `{command, headers}` → `changed: true`, and of `{command}` → `false`; read: the SDK model] |
| 11 | **The live job's evidence step checks for one secret of two.** On a failure, the step that guards the upload of every dr home (D4's B25) greps for `$OPENAI_API_KEY` only. The job now also holds `CLAUDE_CODE_OAUTH_TOKEN`, which D1's merged `live.yml` added. | `.github/workflows/live.yml`, the steps "No dr home holds the model key" and `upload-artifact` | [read] |
| 12 | **D4 does not merge cleanly with `main`.** `main` (`16d4b3a`) holds D1 and D2's eight PRs, and its `src/` equals D2's `0e0a394`, which D4 contains. A trial merge reports add/add conflicts in `library/api.py` and `library/texts.py`. D3's head `73c6425` conflicts with `main` in the same two files. | §5.1 | [run: `git merge-tree --write-tree`] |

### 1.4 Where the design holds

I compared every behaviour in the design that the code could contradict with the code at `3129da9`. Beyond
§1.1–§1.3:
- B1–B29 hold as v5 states them, except B12 (#2), B15's test name (#6), B16 (#7) and B22's size (#9). `mcp/` is
  unchanged and the D1 and D2 seams are unchanged in substance [read; run: `git diff`];
- B30 holds for remote servers [run: §7.5];
- every test function the design names exists, except #6's rename, the old capability-test name that the design
  quotes as history, and §10.6's proposed cross-repository test [run: name comparison];
- Appendix A.1's public surface is `check.py`'s, name for name [read].

r2's #11 (a non-boolean property schema stops a plain-`dr` run) is now in the design (B26's "Left", §14 item 15),
and the code is unchanged [run: `git diff`]. r2's #13 (D4 on stale D1 and D2) is resolved (§5.1).

---

## 2 · What exists

D4 adds two things to the Library and to `dr-acp`:
- A **tool of your own** is a D2 tool row: a block and a Python source. **Check** builds it in a throwaway process,
  and the App backend runs Check again before it saves changed code.
- An **MCP grant** is also a D2 tool row. Its block snapshots a server's non-secret settings from Canvas's MCP
  settings, and its source is D4's **shim**.

In a conversation, `dr-acp`'s worker connects the granted servers before deep_reasoner builds its tools, and the
shim's factory hands each server over. Under plain `dr` (an export), the same shim connects by itself. [read; run
end to end by the tests of §7]

```text
Tools tab (frame) ─ POST ../tools/{n}/check ─▶ routes.check ─ check_tool ─┬ static stage (no process)
                                                                         └ check_child: own group, no secrets, model at 127.0.0.1:9
                  ─ PUT ../tools/{n} ───────▶ D2 put_tool ─ require_check ─▶ 422 check_failed | 400/409 MCP_VIA_GRANT | Library.put_tool
                  ─ PUT ../mcp/{n} ─────────▶ routes.put_grant ─ mcp_block + shim_source() ─▶ Library.put_tool (a tool row)
                  ─ GET ../mcp ─────────────▶ grant_record + read_seen($DR_HOME/mcp/<sha256[:16]>.json)
page (Canvas's realm), Tools tab only: GET /api/settings + the deep_reasoner profile ─▶ frame URL ?mcp=[…] (names only;
                  an entry's auth adds the names of the headers it sends)

dr-acp front:  session/new keeps mcpServers ─ first prompt: materialize ─ specs_for_run ─▶ Start.mcp_servers (control pipe)
worker:        load_dr_config ─ open_session: start every granted, reachable server at once; stderr → redacting copier → mcp-<alias>.log
               ─ emit mcp.status ─ shim.SESSION = {alias: Func} ─ build_reasoner ─ make_tools ─ mcp_server() returns SESSION[alias]
front pump:    mcp.status ─▶ events.jsonl ─▶ Encoder: one root notice per server not bound; remember_seen ─▶ $DR_HOME/mcp/
plain dr:      make_tools ─ mcp_server() with SESSION None ─ Connection from the block, each value from os.environ
```

The length sits in four places:
- `mcp/shim.py`, 541 lines: the connection, the REPL objects, the description and the guard (§4.6);
- `tools/check.py`, 369 lines: the supervisor of the throwaway process (§4.1);
- `mcp/session.py`, 244 lines: `open_session` and its redacting log copier (§4.5);
- the frame's `ToolEditor.tsx`, 356 lines (§4.8).

[run: `wc -l`]

---

## 3 · The public surface, from the code

### 3.1 HTTP (the App backend)

D4's three routes come after D3's `/ui/` routes. They are built with D2's `route`, behind D2's guard (same user,
`Host`, JSON body). [read: `library/api.py:375-376`; CI: `test_mcp_routes_answer_only_their_own_host`]

```text
POST /tools/{name}/check  {"yaml", "source"?, "example"?}            200 CheckReport, always (400 for a body it cannot read)
PUT  /tools/{name}        D2's body + "accept_check_failure"?        D2's answers, and, before anything is written:
                                                                     400 MCP_VIA_GRANT   (the body's block is a grant's)
                                                                     409 refused MCP_VIA_GRANT   (the head is a grant; any base_version)
                                                                     422 {"error": "check_failed", "message", "check": CheckReport}
GET  /mcp                                                            200 [McpGrant], in GET /tools order
PUT  /mcp/{name}          {"server", "transport", "command"?, "args"?, "url"?, "env"?, "headers"?, "granted_in", "base_version"}
                                                                     201 | 200 McpGrant
                                                                     400 MCP_BAD_REQUEST + pydantic's reason; MCP_NEEDS_COMMAND; MCP_NEEDS_URL
                                                                     409 refused MCP_NAME_TAKEN | MCP_SERVER_TAKEN; 409 conflict (D2's)
                                                                     422 invalid (D2's name rule, RESERVED_NAMES)
DELETE /tools/{name}?base_version=   D2's route; removes a grant as it removes any tool
```

[read: `tools/routes.py:44-86`, `tools/check.py:344-369`, `library/api.py:263-276`; CI: `tests/tools/test_routes.py`,
27 cases]

`PUT /mcp/{name}` checks, in this order: the body, D2's name rule and `RESERVED_NAMES`, a tool of your own under that
name, a server another grant already names, then the snapshot's command or URL (`mcp_block`). [read:
`tools/routes.py:56-80`]

### 3.2 Python

- **`deep_reasoning.tools.check`** (`check.py`, read in the order a Check runs):
  - the report: `Outcome` (ten values), `ExampleResult` and `CheckReport` (eleven fields), `:40-119`;
  - `check_tool(name, yaml_text, source, *, example=None, limits=DEFAULT_LIMITS) -> CheckReport`, `:122-151`;
  - `tool_name_errors` and `check_env`, `:154-171`;
  - the child and its supervisor: `_build_in_a_child`, `_Reports`, `_follow`, `_end`, `_tail`, `:174-328`;
  - `ToolCheckFailed(name, report)` and `require_check(library, name, yaml_text, source, *, accept_failure)`,
    `:331-369`;
  - the constants `CheckLimits(ready_s=30, build_s=10, example_s=10)`, `RESERVED_NAMES` (six names),
    `CHECK_MODEL_URL` and `SHOWN_LIMIT` (2,000).

  [read]
- **`python -m deep_reasoning.tools.check_child --report-fd N --name NAME [--example EXPR] MAIN`**. The file opens with
  `main` (`:29-54`), then `_build`, `_load`, `_frames`, `_try`. [read]
- **`deep_reasoning.tools.routes`**: `CheckBody` and `tool_routes(library, route) -> list[Route]`, where `route` is
  `Callable[[str, str, Handler], Route]`. [read: `:26-41`]
- **`deep_reasoning.mcp.shim`** is a module, and also every grant's `factory_from` file. It holds:
  - the factory `mcp_server(client, params)`, `:487`;
  - `McpToolError`, `SESSION`, `ServerSpec`, `Connection` (`:138`), `Server` (`:328`), `McpTool` (`:299`),
    `Unavailable` (`:373`), `describe`, `bound`, `unavailable` and `spec_from_block` (`:457`);
  - the guard (`:522`), run as `python -I shim.py --guard -- COMMAND ARGS…`.

  Its first line is `# deep-reasoning MCP shim, version 1. …`, and its module level imports only the standard
  library. [read; CI: `test_the_shim_imports_only_the_standard_library_at_module_level`]
- **`deep_reasoning.mcp.session`**: `open_session(cfg, specs, *, run_dir) -> list[McpServerStatus]` (`:188`) and
  `reachable(registry, start, names)` (`:44`). [read]
- **`deep_reasoning.mcp.wire`** is what `dr-acp`'s front imports (pydantic and yaml only). [read]
  - `McpServerSpec`, `McpServerStatus` and `McpSeen`;
  - `forwarded_specs` (`:69`), `servers_named` and `specs_for_run` (`:107`);
  - `redact` (`:117`), `remember_seen` (`:132`) and `read_seen` (`:157`).
- **`deep_reasoning.mcp.grants`** is the backend's side: `McpGrantBody`, `McpGrant`, `shim_source`, `is_mcp_tool`,
  `header_env_name` (`:58`), `mcp_block` (`:64`) and `grant_record` (`:83`). [read]

### 3.3 `dr-acp`

- `initialize` advertises `mcpCapabilities: {"http": true, "sse": true}` (`acp/agent.py:31`). [CI:
  `test_dr_acp_advertises_http_and_sse`; run: `grep` finds it in all 20 golden recordings]
- The run log has one event of D4's, `mcp.status {servers: [McpServerStatus]}` (`acp/runlog.py:145, 173`). The worker
  emits it once per run, before `build_reasoner`, and only when the run's config has an MCP block. [read:
  `acp/worker/runner.py:146-148`]
- The encoder turns it into one root `agent_message_chunk` per server whose state is `no_answer`, `failed` or
  `not_enabled`. It does so in both modes and on replay. The text is the notice and `"\n\n"`, with no `_meta`.
  [read: `acp/encoder.py:249, 353-363`, `acp/texts.py:143-173`; CI:
  `test_encoder.py::test_each_mcp_server_not_bound_is_a_notice_on_the_root[native, flat, replay]`,
  `test_acp.py::test_the_notice_replays_on_load`]

### 3.4 The Tools tab

The tab shows, top to bottom:
- D3's safety banner;
- `TOOLS_RISK`;
- **Your tools**: the list with **+ New tool**, or an editor with a back link in its place;
- **MCP servers (from Canvas's settings)**, under `MCP_SETTINGS_UNKNOWN` when Canvas's settings were not read;
- `MCP_EXPORT_NOTE`.

[read: `ui/tabs/tools.tsx:72-173`; CI and run: the 17 browser tests of D4's in `test_tools_tab.py`]

The frame takes one parameter of D4's, `mcp`: a JSON list of `McpServerInfo`. An entry of another shape is dropped,
and an unreadable value is `null`. [read: `shared/protocol.ts:45-61, 129, 162-186`; CI: `protocol.test.ts`]

---

## 4 · Structure and seams

### 4.1 Check: `tools/check.py` and `tools/check_child.py`

**The static stage** runs in the backend and starts no process. It runs these steps in order, and the first
failure ends it:
1. D2's `shapes.validate_tool` → `invalid`, with D2's message;
2. `RESERVED_NAMES` → `invalid`;
3. an `mcp_server` block → `invalid`, `MCP_VIA_GRANT`;
4. no source: `builtin` when the factory is `llm` or a key of deep_reasoner's `TOOL_BUILDERS`, otherwise
   `bad_factory` in `make_tools`' words;
5. `compile` → `syntax`.

[read: `check.py:132-150`; CI: each case runs under `no_process`, which fails the test if `Popen` is called]

**The child.** `_build_in_a_child` writes a one-tool config into a `TemporaryDirectory`:
- `config/main.yaml`, with a client at `http://127.0.0.1:9/v1` and no retries, plus the canonical block;
- `config/tools/<name>.py`, the source byte for byte.

It then starts `sys.executable -m deep_reasoning.tools.check_child` with:
- the config folder as working directory;
- the environment `check_env`: the six variables `PATH`, `LANG`, `LC_ALL`, `LC_CTYPE`, `TMPDIR` and `TZ`; `HOME`,
  `USER` and `LOGNAME` from the password database; and two `PYTHON*` flags;
- stdin `/dev/null`, and stdout and stderr to `printed.txt`;
- a pipe fd for the report;
- a new session.

A `Popen` that raises `OSError` is `unavailable`, phase `starting`. [read: `check.py:174-218`; CI:
`test_check_gets_no_secret`, `test_check_never_reaches_a_model`,
`test_a_check_whose_process_cannot_be_started_is_unavailable`]

The child mirrors `make_tools`' `factory_from` branch, and writes JSON lines to the report fd: `ready`; then `built`
(with `told`, deep_reasoner's `func(name, value, description).describe()`, and `seconds`) or `failed` (with an
outcome); then `example` when one was given. A `load_tool_factory` `ValueError` is classified by its `__cause__`:
- an `ImportError` → `import_failed`;
- any other cause → `raised`;
- no cause → `bad_factory`.

An exception from the factory is `raised`, with the traceback's frames in `tools/<name>.py`. A result that is not a
`Func` is `not_func`, in `make_tools`' sentence. [read: `check_child.py:29-96`; CI:
`test_not_func_and_unknown_factory_sentences_equal_make_tools`]

**The supervisor** is where the subtlety is. `_Reports` reads the pipe on a daemon thread into a queue, and
`get(phases, seconds)` returns the next line of those phases, `None` at the end of the pipe, or raises
`queue.Empty`. `_follow` awaits each phase in turn:

| Awaited | Within | Missed | The pipe closes instead |
|---|---|---|---|
| `ready` | 30 s | `unavailable`, `READY_TIMEOUT` | `unavailable`, `CHILD_ENDED` "starting" |
| `built` or `failed` | 10 s more | `timeout`, `BUILD_TIMEOUT` | `raised`, `CHILD_ENDED` "building the tool" |
| `example` | 10 s more | the example's `EXAMPLE_TIMEOUT`; the build stays ✓ | the example's `CHILD_ENDED` "trying it"; the build stays ✓ |

On every path, `_end` sends `SIGKILL` to the child's group **before** reaping it. The report carries the last 2,000
characters of `printed.txt`, and the folder goes when the `with` block exits. [read: `check.py:221-328`; CI:
`test_nothing_a_stopped_tool_started_is_left_running`, `test_the_temporary_folder_is_removed[word_count, hang]`,
`test_printing_cannot_corrupt_the_report`, `test_an_example_that_ends_the_process_says_how_and_the_build_stays_ok`]

### 4.2 The gate: D2's `PUT /tools/{name}`

D2's `put_tool` calls `require_check` before anything else (`api.py:263-267`). `require_check` decides, in this
order:
1. YAML D2 refuses passes through, so D2's `422 invalid` answers;
2. an `mcp_server` block → `400 MCP_VIA_GRANT`;
3. a head that is a grant → `409 refused MCP_VIA_GRANT`;
4. a canonical block and source equal to the head's (a change of grants only) → no Check;
5. otherwise `check_tool` runs without an example. A report that `can_save`, or `can_save_anyway` with
   `accept_check_failure`, goes on; anything else is `ToolCheckFailed` → `422 check_failed`.

`Library.put_tool` and `dr-library import` are not gated. [read: `check.py:344-369`; CI:
`test_a_grant_only_change_runs_no_check`, `test_save_anyway_stores_a_raising_tool_only_when_asked`,
`test_a_structural_failure_cannot_be_saved_anyway`, `test_a_tool_of_your_own_cannot_replace_a_grant[new, the head's]`]

### 4.3 A grant is a D2 tool row: `mcp/grants.py`, `tools/routes.py`

`PUT /mcp/{name}` writes `Library.put_tool(name, canonical_yaml(mcp_block(name, body)), source=shim_source(), …)`.
The block holds `factory: mcp_server`, `name`, `server` and `transport`, and then one of two sets:
- for stdio: `command`, `args` and `env` (names only), and **no** `headers` (`grants.py:76`; §1 #10);
- for HTTP or SSE: `url`, and `headers` mapped to the variable that `dr` reads each one from,
  `header_env_name(server, header)`, which gives `POSTGRES_AUTHORIZATION` (`:79-80`).

D2 adds `factory_from: tools/<name>.py`. A row is a grant when its factory is `mcp_server` and its source starts with
`# deep-reasoning MCP shim` (`is_mcp_tool`). That still holds after an export and re-import. A resend of the stored
snapshot makes no tool version, because D2 writes none for an unchanged row (`library/library.py:438-449`).
`shim_current` is exact equality with the installed `shim.py`'s text (`grants.py:96`). [read; CI:
`test_put_mcp_writes_the_block_and_the_shim_and_grants`, `test_put_mcp_resent_unchanged_makes_no_tool_version`,
`test_an_exported_and_reimported_grant_is_still_a_grant`]

### 4.4 Front to worker: the seam that carries secrets

D1's `Session` keeps the `mcpServers` of `session/new` and `session/load` as dumped dicts (`acp/session.py:104`). At
a run's start, `Session._materialize`, in one `asyncio.to_thread` (`:194, 222-225`), does three things:
1. it materializes the run;
2. it calls `specs_for_run`, which reads `main.yaml` as plain YAML for each MCP block's `server`;
3. it keeps only the forwarded servers that some block names. A stdio entry has no `type` in ACP 0.12.1's dump;
   `http` and `sse` are typed; other types are dropped.

The specs travel in `Start.mcp_servers` over the control pipe (`acp/worker/protocol.py:18-19`), never in the worker's
environment. [read: `mcp/wire.py:69-114`; CI: `test_a_run_gets_only_the_specs_its_blocks_name`,
`test_a_forwarded_server_no_grant_names_is_never_started`]

### 4.5 The worker: `mcp/session.py`

`Worker.build` calls `open_session` after `load_dr_config` and before `build_reasoner` (`acp/worker/runner.py:124,
146, 149`). `open_session` does five things:
1. It takes every `mcp_server` block. With none, it sets `shim.SESSION = {}` and returns `[]`, so no `mcp.status`
   is emitted.
2. With deep_reasoner's own registry, it computes which namespaces grant each alias, and the namespaces this
   conversation can reach (the closure of the entry namespace under `check_spawn`). An error here fails the build,
   as D1's `build_failed`.
3. It decides each alias:
   - granted nowhere, or only out of reach → `skipped`;
   - no forwarded spec → `not_enabled`;
   - otherwise `_Started` opens `runs/<run>/mcp-<alias>.log`, starts the redacting copier, and starts a
     `Connection` whose stderr is that pipe.

   An exception in any of this is that server's `failed`, redacted.
4. It waits for each started server until the shared start plus that server's `connect_timeout_s`. The outcome is
   `bound` (count, seconds, and `told`), `failed` (the pipe closed, `DRAIN_S` = 2 s, then the failure and the
   log's last 300 characters, redacted), or `no_answer` (`abandon()`).
5. It sets `shim.SESSION` to a `Func` per block, either a `Server(…, granted=…)` or a stand-in, and returns one
   status per block.

[read: `session.py:188-244`; CI: `test_session.py`, 17 cases]

**The log copier** (`_copy_redacted`, `session.py:104-118`) reads 64 KiB at a time and applies `wire.redact` with the
spec's `env` and header values. It holds back the last (longest secret − 1) characters for the next read, so a secret
split across two writes is still caught. A server's arguments are not redacted. [read; CI:
`test_a_server_that_exits_at_start_is_failed_with_its_stderr_redacted[whole, split]`,
`test_a_server_that_prints_more_than_a_pipe_holds_answers_and_its_log_is_redacted`]

`make_tools` then loads each grant's stored copy of the shim. Its `mcp_server` finds `SESSION` set and returns
`SESSION[alias]` without connecting (`shim.py:477-493`). [read; CI: `test_a_stored_v1_shim_works_with_todays_session`]

### 4.6 The shim at run time: `mcp/shim.py`

- **`Connection`** is one server, on a daemon thread with its own event loop. Its transports:
  - stdio through the guard: `sys.executable -I <this file> --guard -- command args…`;
  - streamable HTTP through an `httpx.AsyncClient` that carries the headers;
  - SSE through `sse_client(url, headers=…)`.

  `_serve` initializes, lists every page of tools, sets `ready`, and waits. [read: `:138-234`; CI:
  `test_an_http_server_is_reached_with_its_headers[http, sse]`, `test_calls_from_many_threads_and_under_nest_asyncio`]
- **A call** runs `call_tool(…, read_timeout_seconds=call_timeout_s)` and is given up after that plus 5 s. Its
  failures map as follows:
  - `McpError` 408, or no answer in time → `CALL_TIMEOUT`;
  - `McpError` −32000, or anyio's closed-stream errors → `SERVER_STOPPED`, for this call and, at once, for every
    later one;
  - any other `McpError` → `CALL_FAILED` with the server's message (B28);
  - anything else → `CALL_FAILED` with "Type: message".

  A result is unwrapped per §8.3: `isError` raises; FastMCP's `{"result": …}` wrapper is unwrapped; all-text
  content becomes one string; any other content becomes a list of blocks. [read: `:245-296`; CI:
  `test_results_are_unwrapped_dicts_text_or_blocks`, `test_a_server_that_dies_fails_the_call_and_every_later_one_at_once`]
- **What the REPL binds**:
  - `Server`, callable as `name(tool, /, **arguments)`, with one `McpTool` attribute per tool whose name makes an
    identifier;
  - `__cross_namespace__`, which refuses a hand-off outside a known grant set with `HANDOFF_REFUSED`;
  - `Unavailable`, which raises its sentence on any call or public attribute.

  [read: `:299-395`; CI: `test_handing_a_server_to_an_ungranted_namespace_is_refused`]
- **The description** is §8.4's: a boolean property schema is `Any` or `Never`, and a non-mapping, non-boolean one
  raises. [read: `:398-439`]
- **Plain `dr`** (when `SESSION` is `None`): `spec_from_block` reads each `env` name and each header's variable from
  `os.environ`, and leaves out a variable that is unset, naming it in the stand-in's reason if the server cannot be
  bound. The shim connects, waits `connect_timeout_s`, and binds `Server(granted=None)`. Without the `mcp` package
  the stand-in says `pip install mcp`. [read: `:457-519`; run: §7.5; CI: `test_an_exported_grant_runs_under_dr`]
- **The guard** starts the command in its own process group and polls its parent every 0.5 s. When the parent
  changes, it sends `SIGKILL` to the group. [read: `:522-541`; CI:
  `test_the_guard_ends_its_server_when_its_parent_is_killed`]

### 4.7 What comes back: notices and the seen cache

The pump logs `mcp.status`, and for a live event calls `_remember` → `remember_seen(home.root, run_id, servers, now)`
(`acp/supervisor.py:208-226`). That writes `$DR_HOME/mcp/<16 hex of sha256(server)>.json` for each `bound` server,
through `mkstemp` and `os.replace`, mode 0600 in a 0700 folder. An `OSError` there is logged, not raised. `GET /mcp`
reads the cache from `library.path.parent` (`tools/routes.py:42`). [read; CI:
`test_the_seen_cache_is_written_for_bound_servers`, `test_the_seen_cache_round_trips_and_is_private`]

### 4.8 The frame

**The page** runs in Canvas's realm, and only for the Tools tab (`page/mount.ts:113`). `readMcpServers` sends
`GET /api/settings`, without `X-Expose-Secrets`, and `GET /api/agent-profiles/deep_reasoner`; either failing gives
`null` (`page/context.ts:183-206`). `mcpServersFromSettings` (`:144-179`) then builds one `McpServerInfo` per
server:
- **transport**: stdio when there is a `command`; SSE when there is a `url` and `transport: "sse"`; HTTP when
  there is only a `url`; otherwise the server is skipped;
- **`env`**: the keys only;
- **`headers`**: the keys of `headers`, then `authHeaderNames(auth)`, each name once. Since B30, `auth` gives:

  | `auth.strategy` | Header names added |
  |---|---|
  | `bearer`, `basic` | `Authorization` |
  | `api_key` | its `header_name`, or `Authorization` when the name is empty or absent |
  | `header` | the keys of its `headers` |
  | `none`, `oauth2`, anything else | none |

- **`why_not`**: `disabled` or `not_in_profile`.

[read; run: §7.5; CI: `context.test.ts`'s "adds the header names a remote server's auth sends" (7 cases)]

**`mcpRows`** (`ui/tools.ts:82-121`) joins Canvas's list with `GET /mcp` by server name. It returns Canvas's servers in
order, then the grants gone from Canvas's list, by name. `changed` compares the JSON of `snapshotOf(server, info)`
and `snapshotOf(server, grant)`, so a header name the grant lacks makes a row changed (§1 #10). With `mcp` null there
are the grants' rows only, in state `given`. [read; CI: `tools.test.ts`, 22 cases]

**The editor** (`ToolEditor.tsx`):
- A saved tool's namespace tick `PUT`s the head's YAML, source and version with the new `granted_in`
  (`:175-188`), so no Check runs and no unsaved code is sent.
- **Save** sends the draft (`:164-171`). A 422 with a report shows the report, with **Save anyway** when
  `can_save_anyway`. A `409 conflict` on a saved tool gets D3's **Reload** and **Save over** (`:121-127, 324-338`).
- The source is `PythonField`, CodeMirror from the `editor` chunk, remounted under `key={generation}` after a reset.
  If the chunk cannot load, it falls back to D3's textarea.
- The draft is kept under `dr-library.draft.tool.<name>`, or `….new` for a new tool.

[read; CI: `test_a_grant_tick_on_a_saved_tool_saves_without_unsaved_code`, `test_the_editor_keeps_python_indentation`]

**An MCP row** (`McpServerRow.tsx`):
- A first tick sends Canvas's snapshot at `base_version: 0`; later ticks resend the grant's stored snapshot at the
  grant's version (`:86-94`).
- **Update** sends Canvas's snapshot, or the stored one when Canvas's settings are unread (`:107-113`).
- **Remove** is D2's `DELETE /tools/{name}`.
- Inherited namespaces show `inheritedNotes` (`:115-117`).

[read; CI: the browser tests of §7.2; §7.4 says which of these lines no test pins]

---

## 5 · What D4 relies on, and what relies on D4

### 5.1 Where D4 sits

```text
3129da9  D4 (v1-custom-tools)
  └ D3's head 73c6425 (v1-decompositions-panel), merged whole
      └ D2's code head 0e0a394 (v1-library-store; its head f54a2aa is two document commits on)
          └ D1's head f7a91f3 (v1-dr-acp)
main 16d4b3a: D1 and D2's eight PRs; its src/ equals 0e0a394's. D4 has not merged it (merge-base 32c7f61).
```

[run: `git merge-base`, `git rev-list`, `git diff --stat 0e0a394 origin/main -- src` (empty)] The trial merge with
`main` conflicts in two of D2's files, as D3's head does (§1 #12). D4 adds to them: `api.py` +17 −5 (§1 #2), and
none to `texts.py`; the `texts.py` conflict is D3's. [run]

### 5.2 deep_reasoner (`d7334ae`), `mcp` (1.30.0)

The lock pins both at the same versions as in r2 (it gained only D1's `genai-prices`), so r2's references stand:
- `make_tools`' `factory_from` branch and its two inline sentences, which Check mirrors and copies
  (`v2/cli.py:125-180`);
- `load_tool_factory`'s wrap of an import failure (`tools/base.py:329-407`);
- `TOOL_BUILDERS` and `func(…).describe()`;
- `check_spawn`, the namespace registry and `cross_namespace`, which calls `__cross_namespace__`;
- a loopback client needs no key;
- from `mcp`: `stdio_client` puts the server in a new session; `call_tool(…, read_timeout_seconds=…)`;
  `streamable_http_client` and `sse_client`; `McpError` −32000 and 408.

[read]

### 5.3 D1

| Relied on | Where |
|---|---|
| `Start` over the control pipe; D4 adds `mcp_servers` | `acp/worker/protocol.py:18-19` |
| `Worker.build`: `load_dr_config`, then D4's `open_session`, then `build_reasoner`; `build_failed` covers what `open_session` raises | `acp/worker/runner.py:120-163` |
| The recorder's `emit(kind, **fields)` | `acp/worker/recorder.py:182` |
| `RunHandle.start(…, mcp_servers=())`; the pump logs each event, then D4's `_remember` | `acp/supervisor.py:87-155, 199-226` |
| `Session.mcp_servers`; the one `to_thread` of `_materialize` | `acp/session.py:104, 194, 222-225` |
| The encoder's root message form; the `RunEvent` union | `acp/encoder.py:249, 353-363`; `acp/runlog.py:145, 173` |
| The test harness: `DrAcp.open_session(cwd, mcp_servers=())`, `FakeOpenAI`, and the ACP client shim `ShimConnection`, with the schema check of every message | `tests/acp/harness.py:138, 213`; `acp/testing/client.py:32` |

D1 has no MCP shim of its own: D4's shim is `mcp/shim.py`. [read]

### 5.4 D2: the API and its `route` closure

| Relied on | Where |
|---|---|
| `create_app`'s `route(path, method, handler)` closure, handed to `tool_routes` | `library/api.py:316-327, 376` |
| `_parse(model, body, sentence=BAD_REQUEST)` (private; D4 added `sentence`) | `library/api.py:155-162` |
| `_ToolBody.accept_check_failure` (D4's field) and `put_tool` calling `require_check` first | `library/api.py:139-143, 263-276` |
| The guard and the `LibraryError` handler | `library/api.py:378-385` |
| `put_tool`; `base_version` 0 against a head → `409 conflict`; an unchanged write makes no version | `library/library.py:245-260, 339-358, 438-449` |
| `state()`, `tools()` | `library/library.py:73, 101` |
| `shapes.validate_tool`, `canonical_yaml`, `tool_file`, `TOOL_DIR`, `deep_reasoner_build` | `library/shapes.py:185, 48, 180, 31, 60` |
| `materialize` writes `tools/<name>.py`, with `factory_from` set | `library/configdir.py:99, 160-162` |
| The error family and `ToolRecord`, `FieldError` | `library/records.py:162-233, 60, 141` |

[read]

### 5.5 D3: the frame's components

| Relied on | Where |
|---|---|
| `NamespaceChecklist`, its `inherited` notes fixed and checked | `ui/components/pickers.tsx:35, 43-72` |
| `CodeField` (the YAML field and `PythonField`'s fallback), `Banner`, `ConfirmRow` (D4 adds `confirmTestId`) | `ui/components/fields.tsx:24, 69, 85-99` |
| `drafts.ts`, `load.ts` (`attempt`, `useLoaded`, `resolved`, `OnBackendLost`), `SafetyNotice`, `stringifyYaml` | `ui/drafts.ts:25-41`; `ui/load.ts:8-72`; `ui/components/notices.tsx:13`; `ui/yaml.ts:14` |
| `resolved(getEffective)` handing a 500 to the backend-loss footer rather than the tab (pinned by D3's `73c6425`) | `ui/tabs/tools.tsx:43`; `canvas-app/tests/load.test.ts` |
| The frame protocol and the page's mount step 2 | `shared/protocol.ts`; `page/mount.ts:107-127` |
| `ui_routes`, which serves `assets/editor.js` like any built asset | `library/ui.py:26` |

[read]

### 5.6 The SDK fork: the bridge, and the header names

The bridge forwards each enabled server of the profile's filtered `mcp_config` as ACP `mcpServers`, with its secrets
in plain text (`acp_agent.py:739-821`). For a remote server, `_remote_mcp_headers` (`:717-736`) sends the server's own
`headers`, then `auth.to_http_headers()`:

| Strategy | What `to_http_headers` sends |
|---|---|
| bearer | `Authorization: Bearer …` |
| basic | `Authorization: Basic …` |
| api_key | `{header_name: value}`, or `Authorization: Bearer value` when there is no `header_name` |
| header | its `headers` |
| none | `{}` |
| OAuth | `None`, so the bridge logs a warning and sends nothing for it |

An unset secret sends `{}`. [read: `mcp/config.py:131, 153-159, 179-182, 203, 231, 480`] B30's frame mirrors exactly
this (§4.8), except that it names an `auth` header even when its secret is unset, and that it also applies to stdio
(§1 #10). [run: §7.5] Both files are the same at `91430aa` and `1f2b52d` [run: `git diff --stat`].

### 5.7 What relies on D4

- **D5**, by its design (`8086afb`) and D4's §11.4: E10 re-run with an MCP server bound, the `deep_reasoner` profile's
  `mcp_server_refs: null` (which D4 reads), and E12's proposed MCP step through Appendix B's test ids. None of this
  is built in D4. No branch of this repository holds D5's code: `test_notice.py` skips because "D5's dr_app is not
  installed". [read; run: `git branch -r`, `git grep`]
- Nothing else in this repository imports `deep_reasoning.tools` or `deep_reasoning.mcp`. The importers are D4's own
  files (`test_tools_tab.py` among them), six D1 files and D2's `api.py`, all seams of §6.1. [run: `git grep`]

---

## 6 · Wiring and size

### 6.1 Wiring

- **`pyproject.toml`**: `mcp>=1.28,<2` joins the runtime dependencies; ruff's `extend-exclude` adds
  `tests/mcp/fixtures`; the sdist excludes `as_built/` beside `docs/`. Pytest collects `tests/` only, and CI's ruff
  runs on `src` and `tests`. [read]
- **D1's files**, +101 −7, as at `f69bc73`:
  - `AGENT_CAPABILITIES` turns on both MCP transports;
  - `McpStatus` joins the run-event union, and the encoder handles it;
  - the three notices are added to D1's texts;
  - `Start.mcp_servers` is added;
  - `RunHandle.start` passes the specs, and the pump calls `_remember`;
  - `Session._materialize` computes the specs;
  - `Worker.build` calls `open_session`.

  D1's tests change too: the harness's `open_session(cwd, mcp_servers)` (+7 −4), the renamed capability test
  (+2 −2), the notice test in `test_encoder.py` (+36), and one line in each of the 20 golden recordings. [run:
  `git diff --numstat 73c6425 3129da9`]
- **D2's `api.py`**, +17 −5: `accept_check_failure`, `_parse`'s `sentence`, `require_check` in `put_tool`,
  `*tool_routes(lib, route)`, and the two imports inside `create_app`. `tests/library/test_ui.py` requires the editor
  chunk (+3). [run: `git diff`]
- **D3's project**, +1,457 −30 in 17 files:
  - `tabs/tools.tsx` is extended;
  - `api.ts`, `types.ts`, `texts.ts`, `styles.css`, `shared/protocol.ts`, `page/context.ts`, `page/mount.ts` and
    `fields.tsx` are edited;
  - new files: `ToolEditor.tsx`, `CheckResult.tsx`, `McpServerRow.tsx`, `python.tsx`, `editor/python.ts` and
    `tools.ts`;
  - `vite.config.ts` emits the `editor` chunk;
  - `package.json` adds five pinned CodeMirror packages.

  [run: `git diff --numstat`]
- **CI.** D4 leaves `ci.yml` as D3 has it [run: `git diff`]. `live.yml` runs `pytest -m live` and keeps a failed
  run's homes (B25; §1 #11). [read]

### 6.2 Size

Lines added over D3's head. Built files, docs and locks are not counted. [run: `git diff --numstat`, scripts not
committed]

| Measure | Code | Tests | Total |
|---|---|---|---|
| r2: `f69bc73` over `d4e9cd3`, the design's way | 3,399 | 3,778 | 7,177 |
| Before the refactor: `01abb88` over `a7a50db`, the design's way | 3,375 | 3,840 | 7,215 |
| **Now: `3129da9` over `73c6425`, the design's way** | **3,309** | **3,728** | **7,037** |
| Before the refactor, the task row's way (Lines Before) | 3,393 | 4,399 | 7,792 |
| **Now, the task row's way (Lines After)** | **3,327** | **4,287** | **7,614** |

The two ways differ only in three things the design leaves out: `tests/mcp/fixtures/shim_v1.py` (539 lines),
`.github/workflows/live.yml` (+18) and the golden recordings (+20). The Refactorer's figures, 3,393 → 3,327 and
4,399 → 4,287, are the task row's way, and they reproduce. [run]

Now, by part, the design's way:

| Part | Code | Tests |
|---|---|---|
| Check: `check.py` 369, `check_child.py` 126, `texts.py` 100 | 595 | 563 (`test_check.py` 460, fixtures 79, conftest 24) |
| Routes and the gate: `routes.py` 86; D2's `api.py` +17 | 103 | 333 (`test_routes.py`) |
| MCP: `shim.py` 541, `session.py` 244, `wire.py` 163, `grants.py` 98 | 1,046 | 1,296 (`test_shim` 412, `test_session` 328, `test_grants` 167, `test_wire` 149, fake servers 217, conftest 23) |
| D1's files | 101 | 485 (`tests/mcp/test_acp.py` 410, D1's test files 45, `tests/processes.py` 30) |
| Export and live tier | — | 228 (`test_export.py` 60, the two live tests 89 and 79) |
| The frame | 1,457 | 823 (vitest 495, browser 325, `test_ui.py` 3) |
| `pyproject.toml`, the two `__init__.py` | 7 | |
| **Total** | **3,309** | **3,728** |

Against r2, Check is −25, the routes and gate −47 (the route cut), and the frame −18 (B30 +23, refactor −41). In the
tests, `test_acp.py` is −85 (the `converse` fixture) and the frame +35 (B30's 62 vitest lines, browser −27). At the
workspace's ~300 lines an hour, 7,037 lines is about 23.5 h at Gate C; 7,614 is about 25 h.

---

## 7 · Tests and evidence

### 7.1 The runs

| Run | Conditions | Commit | Result |
|---|---|---|---|
| CI [37179695984](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37179695984), job `test` | push; ubuntu, Python 3.12.3, pytest 9.1.1; `ruff check`, `ruff format --check` first | `3129da9` | **693 passed, 81 deselected, 558.88 s**: `tests/acp` 241, `tests/library` 303, `tests/mcp` 80, `tests/tools` 69. Ruff: "All checks passed!" and "133 files already formatted" [CI] |
| the same run, job `canvas-app` | Node 22.23.3: `npm ci`, typecheck, prettier, vitest, build, the committed-build check, then Playwright Chromium against a real `dr-library serve` | `3129da9` | vitest **212 passed, 1 skipped** (12 files); build `app.js` 167.19 kB, `editor.js` 348.48 kB (gzip 117.55), page 9.36 kB; committed build matches; browser **73 passed, 1 skipped, 197.54 s** (`test_tools_tab.py` 20; the skip is D3's `test_notice.py`, "D5's dr_app is not installed") [CI] |
| CI [37177530471](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37177530471) | push, both jobs | `01abb88` (the merge) | **693 passed, 81 deselected, 387.14 s**, with the same D4 counts; vitest 210 passed, 1 skipped (11 files); `app.js` 167.62 kB; browser 73 passed, 1 skipped, 199.16 s [CI] |
| **live [37180265916](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37180265916)** | `workflow_dispatch` on `v1-custom-tools`, created 05:34:07 UTC; job 05:34:11–05:36:03; `OPENAI_API_KEY` and `CLAUDE_CODE_OAUTH_TOKEN` secrets; Claude Code 2.1.285; `pytest -m live -v -rA --basetemp=…` | `3129da9` | **success: 7 passed, 639 deselected, 92.95 s**. The evidence and upload steps were skipped, as they are on success. [CI] |
| local, D4's suites | `DR_BETA_CHECKOUT=/home/user/deep_reasoner_beta uv run pytest tests/tools tests/mcp tests/library/test_api.py`; 4 cores, load average 3–4 | `3129da9` | **189 passed, 2 deselected, 213.79 s**: `test_check` 42, `test_routes` 27, `test_acp` 16, `test_export` 1, `test_grants` 17, `test_session` 17, `test_shim` 23, `test_wire` 6, `test_api` 40. The slowest are `test_check_and_make_tools_agree[hang]` 14.34 s and `test_a_hanging_factory_is_stopped_at_the_build_limit` 12.65 s. No failure, so nothing was rerun. [run] |
| local, browser | `CI=true uv run pytest -m browser tests/canvas_app`, preinstalled Chromium | `3129da9` | **73 passed, 1 skipped, 237.63 s**, the same skip as CI; `test_tools_tab.py` 20 passed [run] |
| local, frame | in `canvas-app/`: `npm ci`, `npx tsc --noEmit`, `npx prettier --check .`, `DR_BETA_CHECKOUT=… npx vitest run`, `npm run build` | `3129da9` | `tsc` and prettier exit 0; vitest **212 passed, 1 skipped**; the build leaves `git status` clean, so it equals the committed `ui/` and `dist/` [run] |

**The live run, D4's two tests.** The MCP test passed at 05:35:53.90, ≈32.5 s after the previous PASSED line, and the
tool test at 05:36:01.58, ≈7.7 s after that. [CI] The tool test writes through `create_app`'s `PUT /tools/course_credits`,
so the gate and a real Check run, and then asserts that a Check of the same body says `built`. Both tests open the
starter Library, whose model is gpt-6-luna (`library/starter.yaml:3`). [read: `tests/tools/test_live.py:43-79`,
`tests/mcp/test_live.py`] Both tests are unchanged since `f69bc73` [run: `git diff`]. The other five are D1's three,
D2's one and D1's
`tests/acp/test_claude_code.py::test_live_claude_code_on_sonnet_answers_through_acp_and_each_snippet_is_a_cell`, and
all passed. The log names no model and no token cost. [CI]

### 7.2 Which tests carry D4

Python: 149 deterministic cases and 2 live ones, spread as in §7.1. Beyond those, D1's `test_encoder.py` carries the
notice test (3 cases) and D2's `test_ui.py` requires the editor chunk. [run]

The browser tier has 17 of D4's cases in `test_tools_tab.py`; D3's three are the safety notice ×2 and the tool list.
[run: `--collect-only`]

vitest: `tools.test.ts` has 22 cases, all D4's. D3's files hold 24 more of D4's:
- `context.test.ts`: `mcpServersFromSettings` 11, B30's 7 among them, and `readMcpServers` 3;
- `api.test.ts`: 5;
- `protocol.test.ts`: 4;
- `mount.test.ts`: 1.

[run: vitest's JSON report]

The design's property table (Gate B section) still maps each property to tests that exist, apart from §1 #6's
rename. [run: name comparison]

### 7.3 E9 at this commit

`check_tool` ran on the committed fixtures, one at a time, with the default limits, at load average about 4. [run:
probe script]

| Case | Outcome | Save | Wall time |
|---|---|---|---|
| `word_count.py`, tried `word_count("one two three")` | `built`, example `'3'` | yes | 1.33 s |
| `not_func.py` | `not_func`, in `make_tools`' sentence | no | 1.43 s |
| `word_count.py` with `factory: mkae` | `bad_factory`: "defines no 'mkae'. It defines: make, make_broken. …" | no | 1.47 s |
| `import_error.py` | `import_failed`: "… raised ModuleNotFoundError: No module named 'yaml_x'" | no | 1.36 s |
| `env_at_build.py` | `raised`: "make raised KeyError: 'D4_TOKEN'" | anyway | 1.40 s |
| `exits.py` | `raised`: "the Check process ended (exit code 3) while building the tool." | anyway | 1.35 s |
| `prints.py`, `calls_model.py` | `built` | yes | 1.62 s, 1.44 s |
| `def make(` | `syntax`: "line 1: '(' was never closed" | no | 0.00 s |
| `factory: rag`, no source | `builtin` | yes | 0.00 s |
| `word_count.py` named `run_all` | `invalid`, `RESERVED_NAME` | no | 0.00 s |
| `hang.py` | `timeout`, "longer than 10 s" | anyway | 11.37 s |

Every outcome and every "save" is the same as r2 measured at `f69bc73`. `test_check_and_make_tools_agree` (8 cases)
passed locally and in CI. [run; CI]

### 7.4 What the refactor removed from test coverage

**No test was cut.** The test functions in `tests/tools/`, `tests/mcp/` and `test_tools_tab.py` number 128 at
`f69bc73` and at `3129da9`, and the one difference is the rename of §1 #6. The per-file case counts in CI at `3129da9`
and at `01abb88` equal those r2 read at `f69bc73`. [run: `git grep` of `def test_`; CI] The
refactor's test commits move helpers into conftests and a fixture. Reading their diffs, every assertion stands.
`test_acp.py`'s unused `START_S` went, and the three crash tests share a function-scoped `crashed` fixture, so each
still has its own conversation. [read]

**What the code changes left unpinned.** I ran one temporary edit per probe, ran the tests named, and reverted.
`git status` was clean after each. [run]

| Probe | Edit | Tests run | Result | What it shows |
|---|---|---|---|---|
| **M1**, the dropped report lines | `_Reports.get` returns the next line whatever its phase (`check.py:241`, `if True:`) | `tests/tools` and `test_acp.py`'s tool-through-the-API test, at `3129da9` | **survived**: 70 passed | Since `e5583e6` the child writes only the lines it is asked for, in order, so the phase filter skips nothing and no test needs it. |
| M1 before the cut | the same edit at `01abb88`, where the child still wrote `loaded` and `done` | `tests/tools`, in a scratch worktree (removed) | **caught**: 26 failed, 43 passed (`KeyError: 'told'`: `loaded` was taken for the build's answer) | Before the cut, every Check past `ready` exercised the filter. |
| **M3**, a refactored line (`0100905`) | a later tick on an MCP row sends Canvas's snapshot instead of the grant's stored one (`McpServerRow.tsx:89`) | `test_tools_tab.py`, after a rebuild | **survived**: 20 passed | No test ticks a granted row whose Canvas snapshot differs from the stored one. Only **Update** should change a snapshot, and nothing pins that a tick does not. The same holds before `0100905` [read: the same tests]. |
| **M4**, a refactored line (`58dd18f`) | an MCP row passes no inherited notes (`McpServerRow.tsx:116`) | `test_tools_tab.py`, after a rebuild | **survived**: 20 passed | No browser test grants an MCP server to a parent namespace and looks at the child's checkbox. |
| C1, a control | the same edit in the tool editor (`ToolEditor.tsx:204`) | `test_tools_tab.py`, after a rebuild | **caught**: `test_an_inherited_grant_is_fixed` | The probe method detects a change the browser tier pins. |

**The markup.** I re-ran the Refactorer's DOM probe
(`/tmp/claude-0/-home-user/f8e56d4d-b822-5c27-9bd1-fe1ab3886dee/scratchpad/d4r/dom_probe.py`) myself. It renders 28
states of the Tools tab against a real `dr-library serve`, with ids and timings normalized. It ran at `01abb88`, in a
scratch worktree with its own venv, and at `3129da9`. The two outputs are byte-identical, and both equal the
Refactorer's own baseline and final files. [run: `cmp`]

### 7.5 B30 and the stdio case, run

- **The frame.** `mcpServersFromSettings` ran through `vite-node` on one remote server per strategy, each with its own
  header `X-Trace`. The results [run]:
  - bearer, basic, `api_key` without a `header_name`, and `api_key` with `header_name: ""` → `["X-Trace",
    "Authorization"]`;
  - `api_key` with `header_name: "X-Api-Key"` → `["X-Trace", "X-Api-Key"]`;
  - `header` with `X-Tenant` and `Authorization` → `["X-Trace", "X-Tenant", "Authorization"]`;
  - `none` and `oauth2` → `["X-Trace"]`;
  - a bearer whose `value` is unset → `["X-Trace", "Authorization"]`;
  - a stdio entry with a bearer `auth` → `["Authorization"]`.
- **The backend and `dr`.** Through `create_app`, `PUT /mcp/postgres` with headers `["X-Trace", "Authorization"]`
  stores `{"X-Trace": "POSTGRES_X_TRACE", "Authorization": "POSTGRES_AUTHORIZATION"}`. `spec_from_block` with only
  `POSTGRES_AUTHORIZATION="Bearer s3cret"` in the environment sends `{"Authorization": "Bearer s3cret"}` and names
  `POSTGRES_X_TRACE` missing. [run]
- **The stdio case.** See §1 #10. [run]

### 7.6 Named in the design, not run by D4

E10 with MCP servers bound and E12's MCP step are D5's (§11.4). The cross-repository forwarding test (§10.6) does not
exist. Forwarding is exercised only with a hand-built `McpServerStdio` (the MCP live test and `test_acp.py`) and with
dicts (`test_wire.py`). [read]

---

## 8 · What I could not verify

1. **Forwarding through a real agent-server.** The bridge's `_mcp_config_to_acp_servers` and `_remote_mcp_headers`
   were read, not run. So was the claim that `GET /api/settings` answers `auth` with the shape §7.5 fed the frame.
   B30's design entry says it ran that route; I did not. [read]
2. **`TemporaryDirectory`'s permission reset** (§1 #3) was read in the 3.12.3 stdlib and not run: as root, a read-only
   folder does not block removal.
3. **The live tier** ran in CI only. Its log records no model name and no token cost; gpt-6-luna is the starter
   profile's model, read in the code. The brief placed the dispatch at about 05:25 UTC; the only `live.yml` run on
   `v1-custom-tools` after `f69bc73` is 37180265916, created 05:34:07 UTC.
4. **§1 #11**, the evidence step and the Claude Code token, was read in `live.yml`. I did not check whether a Claude
   Code test's home can hold the token.
5. **macOS**: nothing ran there, not the guard, not `check_env`'s password database, not the group kill.
6. **Remote servers** ran only against the local fake servers over loopback. OAuth servers and slow networks did not.
7. **The read claims that matter most:**
   - §4.4, that secrets never enter the worker's environment: the tests check the logs and the transcript, not
     `/proc/<worker>/environ`;
   - §4.7, that `library.path.parent` is `$DR_HOME`;
   - B28's branch (a JSON-RPC error with a code other than 408 or −32000), which no fake server sends.
