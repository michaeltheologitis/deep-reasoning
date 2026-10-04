# D4 · Custom tools and MCP servers, as built

**TASK-9** · Cartographer · revision 4 · 2026-10-04 · the code at `68ebe81` (head of `v1-custom-tools`; this file
is on `as-built/d4-r4`) and the stack #27–#33 cut from it · checked against design v5 with B30
(`docs/design/d4-custom-tools.md`, last changed in `60f1d00`, unchanged at `68ebe81`) · deep_reasoner_beta `d7334ae`,
`mcp` 1.30.0 and agent-client-protocol 0.12.1, as `uv.lock` pins them · SDK fork `91430aa`, read only, as r3 read it.

**Merged:** #27–#33 merged bottom-up into `main`, now `53c821b`, whose tree equals #33's head `c95e059` (both
`99986b2`). [run: `git rev-parse <commit>^{tree}`]

This revision revises r3 (`461c3b5`: the code at `3129da9`). It keeps r3's section and finding numbers, which the PR
bodies cite, and numbers new findings after r3's. Since r3, `v1-custom-tools` has gained four commits, each a fix for
an r3 finding, landed test-first:
- `f553260` fixes §1.3 #10;
- `6e07549` and its fixup `68ebe81` fix #11;
- `6739e0f` pins r3's probe survivors M1, M3 and M4 (§7.4).

The PR Splitter cut #27–#33 on `main`, and the same fixes were landed per level (§5.1). D4's code is
`src/deep_reasoning/tools/`, `src/deep_reasoning/mcp/`, the Tools tab in D3's `canvas-app/` with its built files, and
`tests/tools/` and `tests/mcp/`. It also edits D1's, D2's and D3's files (§6.1).

**Evidence marks.** Every claim carries one.
- **[run]**: executed on this machine at `68ebe81`. That covers the suites and builds of §7.1, the probes of §1.3, §7.4
  and §7.5 (not committed), the evidence step's script (§1.3 #11), and `git`.
- **[run at 3129da9]**: r3's run, not repeated. Between `3129da9` and `68ebe81` nothing under `src/` changed but the
  built `app.js`, and of the frame's sources only `ui/tools.ts` did [run: `git diff --stat`]. These claims stand for
  the code they name.
- **[CI]**: read from GitHub's logs of the runs in §7.1. I ran no live test, dispatched no workflow and made no paid
  model call.
- **[read]**: read in the code and **not executed**. This is weaker evidence than [run]. §8 lists the read claims
  that matter most.

**Reading order:**
- §1: the divergences from the design, and r3's findings resolved.
- §2–§4: the map, with routes into the code.
- §5: what D4 stands on, the stack and the merge, and what stands on D4.
- §6: wiring and size, per level too.
- §7: tests and evidence, per level too, and the probes (§7.4).
- §8: what I could not verify.

---

## 1 · Divergences from design v5 and B30

The Changelog's D4 merge entry (2026-10-04 07:53) has a drift line: design v5 is stale where r3 listed, and where the
fixes changed it, "MCP_CHANGED per transport, B25's evidence step, B30 for stdio, the test lists". It names v6 and
this r4 as the record after the merge. [read: the Notion Changelog] Those are #13, #14, #1 and §7.2 below. Everything
else was found in the code or the runs.

The design says it matches the build at `f69bc73` (its line 16). Since then `v1-custom-tools` has gained:
- B30's two commits, `87f24e5` and `e32bc3d`;
- five merges of D3: `fd0fc84`, `a87e898`, `3f85560` and `e866563` bring D3's UI changes, and `3129da9` brings
  D3's `73c6425`;
- `01abb88`, the merge of D3's refactored head together with D2's;
- the 12 refactor commits;
- r4's four fix commits.

Of D4's Python, only `tools/` changed, and nothing under `src/` since `3129da9` but the built `app.js`.
`src/deep_reasoning/mcp/` is byte-identical to `f69bc73`. [run: `git diff`]

### 1.1 Built otherwise than the design says

| # | Design says | Built | Where | Reason recorded |
|---|---|---|---|---|
| 1 | B30: the frame adds the header names that "a remote server's `auth`" sends to that server's `headers`. | `mcpServersFromSettings` adds them for every transport. For HTTP and SSE, B30 holds as written. For stdio the names reach `McpServerInfo.headers`, but no block stores them and, since `f553260`, no row compares them (#10, #13). [run at 3129da9: §7.5; run: §1.3 #10's probe] | `canvas-app/src/page/context.ts:126-140, 168-173` | `e32bc3d`'s title says "a remote server's auth"; it records nothing about stdio |
| 2 | §7.1, §7.2, §11.2, B12, B16, A.2, A.5: `tool_routes(library)`, built with a module-level `json_route` that D4 moved out of `create_app`. | `tool_routes(library, route)` takes D2's own `route` closure. `json_route` exists nowhere. D4's edit to `api.py` is +17 −5, where it was +70 −46. `tools/routes.py` still imports D2's private `_parse`, so `create_app` still imports D4's modules inside itself (B12's cycle, now through `_parse`). [read; run: `git grep json_route` is empty] | `tools/routes.py:37-86`; `library/api.py:208-210, 316-327, 376` | `01abb88`: D2's refactor deleted the `_dump` that `json_route` called; resolved with the Scout's cut |
| 3 | §3.3: `tmp = mkdtemp("dr-check-")`, removed after the child is reaped. | `tempfile.TemporaryDirectory(prefix="dr-check-", ignore_cleanup_errors=True)`. That is still `mkdtemp` underneath, so the folder is still mode 0700, and it is removed on every path, after `_end`. One difference: CPython 3.12's cleanup resets permissions and retries where the old `rmtree(ignore_errors=True)` gave up. [read: `check.py:182-218`, the 3.12.3 stdlib; CI: `test_the_temporary_folder_is_removed[word_count, hang]`] | `tools/check.py:182-184` | `eb19663`: the Scout's adopted cut |
| 4 | §3.3: the child reports `ready`, `loaded`, `built` or `failed`, `example`, `done`. | It reports `ready`, then `built` or `failed`, then `example` (only with `--example`). The supervisor never awaited `loaded` or `done`, and a report is built from the same lines. No child writes a line the phase filter in `_Reports.get` skips; since `6739e0f` a test feeds it one directly (§7.4, M1). [read; run: M1] | `tools/check_child.py:29-54` | `e5583e6`: "written for no reader" |
| 5 | §7.4, A.6: `ui/tools.ts` exports `RESERVED_NAMES`, `McpSnapshot = Omit<McpGrantBody, …>`, `snapshotOf(info)`, `grantSnapshot(grant)` and `inheritedGrants`. | `McpSnapshot` is an interface in `ui/types.ts`, and `McpGrant` and `McpGrantBody` extend it. `snapshotOf(server, target)` takes a target from Canvas's settings or from a grant, and `grantSnapshot` is gone. `inheritedNotes(tool, effective)` returns the note text (`INHERITED_ROW`), so both components pass it as it is. `RESERVED_NAMES` is module-private. The Tools tab's markup is unchanged in 28 states (§7.4). [read; run: DOM probe] | `ui/types.ts:175-191`; `ui/tools.ts:9-16, 75-78, 130-141` | `be131ce`, `58dd18f` |
| 6 | §7.1, §10.3, B15: no conftest under `tests/tools/` or `tests/mcp/`; `test_put_mcp_refuses_a_stdio_grant_without_a_command`. | `tests/tools/conftest.py` holds `source(fixture)` and the `no_process` fixture (it was `no_check` in `test_routes.py`). `tests/mcp/conftest.py` holds `put_grant(lib, alias, granted_in, *, block=None, **fields)`. The test is renamed `test_put_mcp_refuses_a_grant_without_its_command_or_url`. `test_acp.py`'s conversations go through a `converse` fixture. Every other test name the design gives exists. [run: name comparison; read] | `tests/tools/conftest.py`, `tests/mcp/conftest.py`, `tests/mcp/test_acp.py:87-113` | `488c580`, `58e9be4`, `5363cc8`, `c62d30f` |
| 7 | B16, §13 and the Gate B section: 3,399 lines of code and 3,778 of tests. | **3,314 and 3,807**, measured the design's way; 3,352 and 4,366 measured the task row's way (§6.2). [run] | — | the refactor, B30, the route cut, and r4's fixes and pins |
| 8 | The Gate B section: the evidence is at `f69bc73`, and the live tier has six tests. B11: 18 golden recordings change one line. | CI is green at `68ebe81` and at every level of the stack; the live tier passed at `3129da9`, and r4's commits change nothing it runs (§7.1). The live job runs seven tests: the merges brought in D1's `test_live_claude_code_on_sonnet_…` (`2a15388`). There are 20 golden recordings, each with the `http`/`sse` line: the merge added `unanswered.flat` and `unanswered.native`. [CI; run: `git diff --numstat`] | `tests/acp/golden/` | evidence, not build |
| 9 | §7.4 and B22: `app.js` is 169 KB (169,027 B). | `app.js` is 167,267 B, `editor.js` 348,475 B (unchanged) and the page bundle `dist/index.js` 9,358 B. Over D3's head (`app.js` 150,631 B, page 7,517 B), D4 adds 16,636 B and 1,841 B. [run: `git cat-file -s`, a fresh build] | `src/deep_reasoning/canvas_app/` | the merges and the refactor (−423 B on `app.js`); `f553260` (+75 B) |
| 13 | §8.6 and §5's row table: a granted row is `changed` when Canvas's transport, command, args, URL, env names or header names differ from the grant's snapshot. | `mcpRows` compares only what the grant's block keeps, per transport (`kept`): transport, command, args and env for stdio; transport, URL and headers for HTTP and SSE. A stdio entry's header names, and a remote entry's args or env, make no row changed. [run: §1.3 #10's probe, and M5 in §7.4; CI: `tools.test.ts`] | `ui/tools.ts:80-87, 105` | `f553260`: r3's #10 |
| 14 | B25: on a failure, a step checks that no file under the live folder holds the model key (`grep -rqF -- "$OPENAI_API_KEY"`); "the step checks the model key only". | The step "No dr home holds a secret" (`id: secretless`) checks `OPENAI_API_KEY`, `CLAUDE_CODE_OAUTH_TOKEN` and `DEEP_REASONER_TOKEN`. The last is in the step's `env` only, not the tests'. It skips an empty value. For each other value, only grep's exit 1 goes on; exit 0 (found) or any other exit refuses. The upload waits on `steps.secretless.outcome == 'success'`. [read; run: §1.3 #11] | `.github/workflows/live.yml:38-74` | `6e07549`, `68ebe81`: r3's #11 |

### 1.2 Stale lines in the design

These are the ones r3's brief named, each confirmed [read]:
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
- "18" golden recordings (lines 72, 1168);
- `changed` (line 470, lines 1553-1554; #13);
- B25's step (lines 1266, 1274-1275, 1771; #14).

### 1.3 Behaviour the design does not state

| # | Found | Where | Evidence |
|---|---|---|---|
| 10 | **Resolved at `f553260`.** r3 found that a stdio server whose Canvas entry has `headers`, or an `auth` that sends a header, read as changed forever. The frame still names those headers in `McpServerInfo.headers`, and `mcp_block` still stores none for stdio, so `GET /mcp` answers `headers: []`. `mcpRows` no longer compares them (#13), so the row is not changed. In the mirror case, a remote entry with `args` or `env` is not changed either. A remote entry's extra header still makes its row changed. | `page/context.ts:168-173`; `mcp/grants.py:76`; `ui/tools.ts:80-87, 105` | [run: `mcpRows` on the page's reading of Canvas entries, against a grant as `GET /mcp` answers it: stdio with a bearer `auth`, with `headers` or with neither → `false`, with another variable → `true`; HTTP with `args` and `env` → `false`, with a bearer `auth` → `true`. CI: `tools.test.ts`'s two new cases; `test_a_changed_server_offers_update[a header a stdio block does not keep]`] |
| 11 | **Resolved at `6e07549` and `68ebe81`.** r3 found that the live job's evidence step checked the OpenAI key only, while the job also holds `CLAUDE_CODE_OAUTH_TOKEN`. It now checks all three secrets the job holds, skips an empty value, and fails closed (#14). When all three are empty, it runs no grep and the upload proceeds. | `.github/workflows/live.yml:38-74` | [run: the step's script, extracted from `live.yml`, under `bash -e` with a scratch `RUNNER_TEMP` and made-up values: clean → exit 0, with `DEEP_REASONER_TOKEN` set, empty or unset; each value planted → exit 1, naming it; no live folder, or a mode-000 file read with `CAP_DAC_OVERRIDE` and `CAP_DAC_READ_SEARCH` dropped → exit 1 (grep exit 2); all three empty → exit 0] |
| 12 | **Resolved by the stack, and merged.** r3 found that D4 did not merge cleanly with `main`. The stack is cut on D3's split top `c60d6d9`, whose tree is `main` `1f9fe52`'s. A trial merge of its top into `1f9fe52` was clean, and `main` `53c821b` now has the top's tree. The top's tree equals `68ebe81`'s except for the docs and three files, each equal to `main`'s (§5.1). `v1-custom-tools` itself merges into `53c821b` without a conflict. | §5.1 | [run: `git merge-tree --write-tree`, `git diff --stat`, `git rev-parse ^{tree}`] |

### 1.4 Where the design holds

I compared every behaviour in the design that the code could contradict with the code at `68ebe81`. Beyond
§1.1–§1.3:
- B1–B29 hold as v5 states them, except B12 (#2), B15's test name (#6), B16 (#7), B22's size (#9) and B25's step
  (#14). `mcp/` is unchanged and the D1 and D2 seams are unchanged in substance [read; run: `git diff`];
- B30 holds for remote servers [run at 3129da9: §7.5; `context.ts` is unchanged since];
- every test function the design names exists, except #6's rename, the old capability-test name that the design
  quotes as history, and §10.6's proposed cross-repository test [run: name comparison];
- Appendix A.1's public surface is `check.py`'s, name for name [read].

r2's #11 (a non-boolean property schema stops a plain-`dr` run) is in the design (B26's "Left", §14 item 15), and the
code is unchanged [run: `git diff`]. r2's #13 (D4 on stale D1 and D2) is resolved (§5.1).

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

[read: `ui/tabs/tools.tsx:72-173`; CI and run: the 20 browser cases of D4's in `test_tools_tab.py`]

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
`test_printing_cannot_corrupt_the_report`, `test_an_example_that_ends_the_process_says_how_and_the_build_stays_ok`,
`test_a_report_line_of_a_phase_not_awaited_is_skipped`, which writes `ready`, `loaded`, `built` and `done` to a pipe
and hands it to `_Reports` directly, with no child]

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
- for stdio: `command`, `args` and `env` (names only), and **no** `headers` (`grants.py:76`);
- for HTTP or SSE: `url`, and `headers` mapped to the variable that `dr` reads each one from,
  `header_env_name(server, header)`, which gives `POSTGRES_AUTHORIZATION` (`:79-80`).

These two sets are what the frame's `mcpRows` compares (§4.8). D2 adds `factory_from: tools/<name>.py`. A row is a
grant when its factory is `mcp_server` and its source starts with `# deep-reasoning MCP shim` (`is_mcp_tool`). That
still holds after an export and re-import. A resend of the stored snapshot makes no tool version, because D2 writes
none for an unchanged row (`library/library.py:438-449`). `shim_current` is exact equality with the installed
`shim.py`'s text (`grants.py:96`). [read; CI: `test_put_mcp_writes_the_block_and_the_shim_and_grants`,
`test_put_mcp_resent_unchanged_makes_no_tool_version`, `test_an_exported_and_reimported_grant_is_still_a_grant`]

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
  the stand-in says `pip install mcp`. [read: `:457-519`; run at 3129da9: §7.5; CI: `test_an_exported_grant_runs_under_dr`]
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

[read; run at 3129da9: §7.5; CI: `context.test.ts`'s "adds the header names a remote server's auth sends" (7 cases)]

**`mcpRows`** (`ui/tools.ts:91-126`) joins Canvas's list with `GET /mcp` by server name. It returns Canvas's servers in
order, then the grants gone from Canvas's list, by name. `changed` compares `kept(info)` with `kept(grant)`
(`:80-87, 105`): for stdio the transport, command, args and env, and for HTTP and SSE the transport, URL and headers,
which are the two sets a block keeps (§4.3; §1 #13). With `mcp` null there are the grants' rows only, in state
`given`. [read; run: §1.3 #10; CI: `tools.test.ts`, 24 cases]

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

[read; CI: the browser tests of §7.2, `test_a_later_tick_keeps_the_granted_settings` and
`test_an_inherited_server_grant_is_fixed` among them; §7.4 shows each of these lines is now pinned]

---

## 5 · What D4 relies on, and what relies on D4

### 5.1 Where D4 sits

```text
68ebe81  D4 (v1-custom-tools)
  └ D3's head 73c6425 (v1-decompositions-panel), merged whole
      └ D2's code head 0e0a394 (v1-library-store; its head f54a2aa is two document commits on)
          └ D1's head f7a91f3 (v1-dr-acp)

main 53c821b  #27 … #33, merged bottom-up, one merge commit each; its tree is c95e059's
  └ 1f9fe52   D1's, D2's and D3's PRs (#19–#26 are D3's); its tree is D3's split top c60d6d9's
#27–#33       v1-custom-tools-01-check … -07-mcp-tab, cut on c60d6d9; each PR's base the level below, #27's main
```

[run: `git merge-base`, `git log --format=%p`, `git rev-parse ^{tree}`; read: the PRs over REST]

The top `c95e059` equals `68ebe81` except for three files and the docs. Each of the three equals `main`'s:
- `docs/deep-reasoner-contract.md`;
- `pyproject.toml`'s sdist exclude, `["docs/"]`, where `68ebe81` also excludes `as_built/`;
- `tests/acp/test_stop.py`, D1's later version with `SIBLING_HOLD_S`.

The design docs and `as_built/` are not in the stack. D3's split top differs from D3's head by the same three files
and the docs.
[run: `git diff --stat`]

| PR | Level and head | What it adds | A fix landed here |
|---|---|---|---|
| #27 | `01-check` `151fbe3` | Check, its routes and the gate | `151fbe3`, the M1 pin |
| #28 | `02-mcp-wire` `adb8967` | `mcp/wire.py`: specs, redaction, the seen cache | — |
| #29 | `03-shim` `cf14ba3` | `mcp/shim.py`, the `mcp` dependency and its lock, the fake servers | — |
| #30 | `04-grants` `51820ca` | `mcp/grants.py`, `PUT /mcp`, `GET /mcp`, export | — |
| #31 | `05-acp-servers` `1caa229` | `mcp/session.py`, D1's edits, the golden lines, the MCP live test and `live.yml` | `1caa229`, the evidence step |
| #32 | `06-tools-tab` `cfcf2c4` | the Tools tab's tool editor, the CodeMirror packages, the built `app.js` and `editor.js` | — |
| #33 | `07-mcp-tab` `c95e059` | the page's MCP reading, `McpServerRow`, `mcpRows`, the rebuilt `app.js` and page bundle | `28355d4`, the stdio fix; `c95e059`, the M3 and M4 pins |

[read: the PR titles; run: `git diff --name-status` per level] Each fix equals its commit on `v1-custom-tools`:
`1caa229` is `6e07549` and `68ebe81` squashed, `28355d4` is `f553260`, and `151fbe3` and `c95e059` are `6739e0f`'s
two halves. The levels between take each fix by a merge from below. [run: `cmp` of the diffs] `v1-custom-tools` now
merges into `main` `53c821b` without a conflict. Outside `docs/` and `as_built/`, the two differ only in
`pyproject.toml` and `test_stop.py`. [run: `git merge-tree`]

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
this (§4.8), with two differences: it names an `auth` header even when its secret is unset, and it also applies to
stdio, where since `f553260` the names change no row (§1 #1, #13). [run at 3129da9: §7.5; run: §1.3 #10] Both files
are the same at `91430aa` and `1f2b52d`. [run at 3129da9: `git diff --stat` in the fork]

### 5.7 What relies on D4

- **D5**, by its design (`8086afb`) and D4's §11.4: E10 re-run with an MCP server bound, the `deep_reasoner` profile's
  `mcp_server_refs: null` (which D4 reads), and E12's proposed MCP step through Appendix B's test ids. D5's code is on
  `v1-desktop` (`2a7b0ec`). That branch does not contain D4: its `src/deep_reasoning/` has no `tools/` or `mcp/`, and
  its merge-base with `68ebe81` is `32c7f61`. Its `dr_app/profile.py:46` writes `"mcp_server_refs": None`, with
  which D4's page marks every enabled server forwarded (`shared/protocol.ts:57`). At `68ebe81`, `test_notice.py` still skips:
  "D5's dr_app is not installed". [read; run: `git ls-tree`, `git merge-base`]
- Nothing else in this repository imports `deep_reasoning.tools` or `deep_reasoning.mcp`. The importers are D4's own
  files (`test_tools_tab.py` among them), six D1 files and D2's `api.py`, all seams of §6.1. [run: `git grep`]

---

## 6 · Wiring and size

### 6.1 Wiring

- **`pyproject.toml`**: `mcp>=1.28,<2` joins the runtime dependencies; ruff's `extend-exclude` adds
  `tests/mcp/fixtures`; the sdist excludes `as_built/` beside `docs/` on `v1-custom-tools`, and not on `main` (§5.1).
  Pytest collects `tests/` only, and CI's ruff runs on `src` and `tests`. [read]
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
  `git diff --numstat 73c6425 68ebe81`]
- **D2's `api.py`**, +17 −5: `accept_check_failure`, `_parse`'s `sentence`, `require_check` in `put_tool`,
  `*tool_routes(lib, route)`, and the two imports inside `create_app`. `tests/library/test_ui.py` requires the editor
  chunk (+3). [run: `git diff`]
- **D3's project**, +1,462 −30 in 17 files:
  - `tabs/tools.tsx` is extended;
  - `api.ts`, `types.ts`, `texts.ts`, `styles.css`, `shared/protocol.ts`, `page/context.ts`, `page/mount.ts` and
    `fields.tsx` are edited;
  - new files: `ToolEditor.tsx`, `CheckResult.tsx`, `McpServerRow.tsx`, `python.tsx`, `editor/python.ts` and
    `tools.ts`;
  - `vite.config.ts` emits the `editor` chunk;
  - `package.json` adds five pinned CodeMirror packages.

  [run: `git diff --numstat`]
- **CI.** D4 leaves `ci.yml` as D3 has it [run: `git diff`]. `live.yml` runs `pytest -m live` and keeps a failed
  run's homes, after a step that checks them for every secret the job holds (B25; §1 #14). [read; run: §1.3 #11]

### 6.2 Size

Lines added over D3's head. Built files, docs and locks are not counted. [run: `git diff --numstat`, scripts not
committed]

| Measure | Code | Tests | Total |
|---|---|---|---|
| r2: `f69bc73` over `d4e9cd3`, the design's way | 3,399 | 3,778 | 7,177 |
| Before the refactor: `01abb88` over `a7a50db`, the design's way | 3,375 | 3,840 | 7,215 |
| r3: `3129da9` over `73c6425`, the design's way | 3,309 | 3,728 | 7,037 |
| **Now: `68ebe81` over `73c6425`, the design's way** | **3,314** | **3,807** | **7,121** |
| Before the refactor, the task row's way (Lines Before) | 3,393 | 4,399 | 7,792 |
| r3, the task row's way (Lines After) | 3,327 | 4,287 | 7,614 |
| **Now, the task row's way** | **3,352** | **4,366** | **7,718** |

The two ways differ only in three things the design leaves out:
- `tests/mcp/fixtures/shim_v1.py`, 539 lines;
- `.github/workflows/live.yml`, +38 (it was +18);
- the golden recordings, +20.

The stack's top over `main` `1f9fe52` measures 3,352 and 4,366 the task row's way, the same as `68ebe81` over D3's
head. [run]

Now, by part, the design's way:

| Part | Code | Tests |
|---|---|---|
| Check: `check.py` 369, `check_child.py` 126, `texts.py` 100 | 595 | 573 (`test_check.py` 470, fixtures 79, conftest 24) |
| Routes and the gate: `routes.py` 86; D2's `api.py` +17 | 103 | 333 (`test_routes.py`) |
| MCP: `shim.py` 541, `session.py` 244, `wire.py` 163, `grants.py` 98 | 1,046 | 1,296 (`test_shim` 412, `test_session` 328, `test_grants` 167, `test_wire` 149, fake servers 217, conftest 23) |
| D1's files | 101 | 485 (`tests/mcp/test_acp.py` 410, D1's test files 45, `tests/processes.py` 30) |
| Export and live tier | — | 228 (`test_export.py` 60, the two live tests 89 and 79) |
| The frame | 1,462 | 892 (vitest 534, browser 355, `test_ui.py` 3) |
| `pyproject.toml`, the two `__init__.py` | 7 | |
| **Total** | **3,314** | **3,807** |

Against r3, the code is +5 (`kept`) and the tests +79: `test_check.py` +10 (M1's pin), `test_tools_tab.py` +30
(M3's and M4's pins, the stdio parameter) and `tools.test.ts` +39 (the per-transport table). At the workspace's ~300 lines an hour, 7,121 lines is about 23.7 h
at Gate C; 7,718 is about 25.7 h.

**Per level**, the design's way, each level over the one below:

| PR | Level | Code | Tests | GitHub's count, all files |
|---|---|---|---|---|
| #27 | `01-check` | 616 | 811 | +1,427 −1 |
| #28 | `02-mcp-wire` | 165 | 149 | +314 −0 |
| #29 | `03-shim` | 544 | 577 (1,116 with `shim_v1.py`) | +1,797 −1 |
| #30 | `04-grants` | 189 | 454 | +643 −11 |
| #31 | `05-acp-servers` | 345 (383 with `live.yml`) | 924 (944 with the golden recordings) | +1,327 −34 |
| #32 | `06-tools-tab` | 925 | 330 | +1,509 −123 |
| #33 | `07-mcp-tab` | 542 | 565 | +1,361 −203 |

[run: `git diff --numstat` per level; read: the PRs' `additions` and `deletions` over REST] The levels sum to 7,136
the design's way, 15 more than the whole: a line added at one level and changed at a later one counts at both. The
largest level, #29, is 1,121 lines the design's way.

---

## 7 · Tests and evidence

### 7.1 The runs

| Run | Conditions | Commit | Result |
|---|---|---|---|
| CI [37186335030](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37186335030) | push to `v1-custom-tools`; both jobs | `68ebe81` | test **694 passed, 84 deselected, 524.75 s**; vitest **214 passed, 1 skipped**; browser **76 passed, 1 skipped, 204.78 s** [CI] |
| CI [37184460145](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37184460145), job `test` | push to `fix/d4-r3`; ubuntu, Python 3.12.3, pytest 9.1.1; `ruff check`, `ruff format --check` first | `68ebe81` | **694 passed, 84 deselected, 365.63 s**: `tests/acp` 241, `tests/library` 303, `tests/mcp` 80, `tests/tools` 70. Ruff: "All checks passed!" and "133 files already formatted" [CI] |
| the same run, job `canvas-app` | Node 22.23.3: `npm ci`, typecheck, prettier, vitest, build, the committed-build check, then Playwright Chromium against a real `dr-library serve` | `68ebe81` | vitest **214 passed, 1 skipped** (12 files); build `app.js` 167.27 kB, `editor.js` 348.48 kB; committed build matches; browser **76 passed, 1 skipped, 147.42 s** (`test_tools_tab.py` 23; the skip is D3's `test_notice.py`, "D5's dr_app is not installed") [CI] |
| **live [37180265916](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37180265916)** | `workflow_dispatch` on `v1-custom-tools`, created 05:34:07 UTC; job 05:34:11–05:36:03; `OPENAI_API_KEY` and `CLAUDE_CODE_OAUTH_TOKEN` secrets; Claude Code 2.1.285; `pytest -m live -v -rA --basetemp=…` | `3129da9` | **success: 7 passed, 639 deselected, 92.95 s**. The evidence and upload steps were skipped, as they are on success. [CI] |
| local, D4's suites | `DR_BETA_CHECKOUT=/home/user/deep_reasoner_beta uv run pytest tests/tools tests/mcp tests/library/test_api.py`; 4 cores, load average 4–9 | `68ebe81` | **190 passed, 2 deselected, 224.70 s**: `test_check` 43, `test_routes` 27, `test_acp` 16, `test_export` 1, `test_grants` 17, `test_session` 17, `test_shim` 23, `test_wire` 6, `test_api` 40. The slowest are `test_check_and_make_tools_agree[hang]` 14.72 s and `test_a_hanging_factory_is_stopped_at_the_build_limit` 12.82 s. No failure, so nothing was rerun. `ruff check` and `ruff format --check` on `src` and `tests` pass. [run] |
| local, browser | `CI=true uv run pytest -m browser tests/canvas_app`, preinstalled Chromium | `68ebe81` | **76 passed, 1 skipped, 283.54 s**, the same skip as CI; `test_tools_tab.py` 23 passed [run] |
| local, frame | in `canvas-app/`: `npm ci`, `npx tsc --noEmit`, `npx prettier --check .`, `DR_BETA_CHECKOUT=… npx vitest run`, `npm run build` | `68ebe81` | `tsc` and prettier exit 0; vitest **214 passed, 1 skipped**. The skip is the CI-only guard "has deep_reasoner_beta's configs in CI"; with `DR_BETA_CHECKOUT` set, the round trip over deep_reasoner_beta's configs ran and passed. The build leaves `git status` clean, so it equals the committed `ui/` and `dist/` (`app.js` 167.27 kB, `editor.js` 348.48 kB, page 9.36 kB) [run] |

**The stack, per level.** Every run below is `success` in both jobs. From #28 up, each PR has two `pull_request`
runs on the same merge commit (for #28, `f3766d1` both times). [CI]

| PR | Head | push run | pull_request runs | test: passed, deselected | vitest | browser |
|---|---|---|---|---|---|---|
| base | `main` `1f9fe52` | 37181971014 | — | 541, 62 | 166 + 1 skipped | 56 + 1 skipped |
| #27 | `151fbe3` | 37186335473 | 37186338259 | 591, 63 | 166 + 1 | 56 + 1 |
| #28 | `adb8967` | 37186335322 | 37186338354, 37186338770 | 597, 63 | 166 + 1 | 56 + 1 |
| #29 | `cf14ba3` | 37186335061 | 37186338275, 37186338547 | 620, 63 | 166 + 1 | 56 + 1 |
| #30 | `51820ca` | 37186336491 | 37186337719, 37186337630 | 658, 63 | 166 + 1 | 56 + 1 |
| #31 | `1caa229` | 37186335342 | 37186338684, 37186338979 | 694, 64 | 166 + 1 | 56 + 1 |
| #32 | `cfcf2c4` | 37186334875 | 37186338549, 37186338988 | 694, 75 | 174 + 1 | 67 + 1 |
| #33 | `c95e059` | 37186335307 | 37186338108, 37186338790 | 694, 84 | 214 + 1 | 76 + 1 |

The Python suite is whole by #31; #32 and #33 add frame tests. The deselected count rises by D4's two live tests
(#27, #31) and its 20 browser cases (#32 11, #33 9). `main` `53c821b`'s push run 37187128304 was still running when I
read it. [CI]

**The live run, D4's two tests.** The MCP test passed at 05:35:53.90, ≈32.5 s after the previous PASSED line, and the
tool test at 05:36:01.58, ≈7.7 s after that. [CI] The tool test writes through `create_app`'s `PUT /tools/course_credits`,
so the gate and a real Check run, and then asserts that a Check of the same body says `built`. Both tests open the
starter Library, whose model is gpt-6-luna (`library/starter.yaml:3`). [read: `tests/tools/test_live.py:43-79`,
`tests/mcp/test_live.py`] The other five are D1's three, D2's one and D1's
`tests/acp/test_claude_code.py::test_live_claude_code_on_sonnet_answers_through_acp_and_each_snippet_is_a_cell`, and
all passed. The log names no model and no token cost. [CI]

**Why it stands at `68ebe81`.** Between `3129da9` and `68ebe81`, `src/` differs only in the built `app.js`, which
none of the five live test files loads; the changed tests (`test_check.py`, `test_tools_tab.py`, `tools.test.ts`)
are none of them live; the lock is unchanged; and in `live.yml` only the evidence step and the upload's condition
changed, which run after a failure only and were skipped in 37180265916. [run: `git diff --stat`, `git grep`] No live
run has been made since. [CI: `gh run list`]

### 7.2 Which tests carry D4

Python: 150 deterministic cases and 2 live ones, spread as in §7.1. Beyond those, D1's `test_encoder.py` carries the
notice test (3 cases) and D2's `test_ui.py` requires the editor chunk. Together these are the 153 cases the stack adds
to `main`'s 541. [run; CI]

The browser tier has 20 of D4's cases in `test_tools_tab.py`; D3's three are the safety notice ×2 and the tool list.
[run: `--collect-only`, 23 items]

vitest: `tools.test.ts` has 24 cases, all D4's. D3's files hold 24 more of D4's:
- `context.test.ts`: `mcpServersFromSettings` 11, B30's 7 among them, and `readMcpServers` 3;
- `api.test.ts`: 5;
- `protocol.test.ts`: 4;
- `mount.test.ts`: 1.

[run: vitest's JSON report; those four files are unchanged since `3129da9`]

The design's property table (Gate B section) still maps each property to tests that exist, apart from §1 #6's
rename. It does not name the three pins, `test_a_changed_server_offers_update`'s stdio parameter, or `tools.test.ts`'s
two new cases. [run: name comparison]

### 7.3 E9 at this commit

`check_tool` ran on the committed fixtures, one at a time, with the default limits, at load average about 4. [run at
3129da9: probe script] `check.py`, `check_child.py` and the fixtures are byte-identical at `68ebe81` [run: `git diff`].

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
passed at `68ebe81`, locally and in CI. [run; CI]

### 7.4 What the refactor removed from test coverage

**No test was cut.** The test functions in `tests/tools/`, `tests/mcp/` and `test_tools_tab.py` number 128 at
`f69bc73` and at `3129da9`, and the one difference is the rename of §1 #6. At `68ebe81` they number 131: the three
pins of `6739e0f`. [run: `git grep` of `def test_`] The refactor's test commits move helpers into conftests and a
fixture. Reading their diffs, every assertion stands. `test_acp.py`'s unused `START_S` went, and the three crash tests
share a function-scoped `crashed` fixture, so each still has its own conversation. [read]

**The probes.** For each probe I made one temporary edit, ran the tests named, then reverted the source and the built
files. `git status` was clean after each. M1 ran `tests/tools`. M3, M4 and M5 rebuilt the frame and ran
`test_tools_tab.py`'s 23 cases; M5 also ran `tools.test.ts`. [run]

| Probe | Edit | At `68ebe81` | r3, at `3129da9` |
|---|---|---|---|
| **M1**, the phase filter | `_Reports.get` returns the next line whatever its phase (`check.py:241`, `if True:`) | **caught**: 1 failed, 69 passed. The failure is `test_a_report_line_of_a_phase_not_awaited_is_skipped`. | survived: 70 passed. The same edit at `01abb88`, before the child stopped writing `loaded` and `done`, failed 26. |
| **M3**, `0100905`'s line | a later tick on an MCP row sends Canvas's snapshot instead of the grant's stored one (`McpServerRow.tsx:89`, `...snapshot`) | **caught**: 1 failed, 22 passed. `test_a_later_tick_keeps_the_granted_settings` got version 2 and Canvas's variable, where it expects 1 and `OLD_TOKEN`. | survived: 20 passed |
| **M4**, `58dd18f`'s line | an MCP row passes no inherited notes (`McpServerRow.tsx:116`, `{}`) | **caught**: 1 failed, 22 passed. `test_an_inherited_server_grant_is_fixed`: "Locator expected to be checked". | survived: 20 passed |
| **M5**, new: `f553260`'s comparison | `kept` compares all six fields whatever the transport, which is r3's comparison (`ui/tools.ts:84-86`) | **caught**. vitest: 2 failed, 22 passed, namely the stdio-header case and the remote args-and-env case. Browser: 1 failed, 22 passed, namely `test_a_changed_server_offers_update[a header a stdio block does not keep]`, whose row is still changed after **Update**. | — |
| C1, a control | the same edit as M4 in the tool editor (`ToolEditor.tsx:204`) | not repeated | caught: `test_an_inherited_grant_is_fixed` |

The M1 pin feeds `_Reports` a hand-written pipe and never runs a child (§4.1). [read]

**The markup.** I re-ran the Refactorer's DOM probe
(`/tmp/claude-0/-home-user/f8e56d4d-b822-5c27-9bd1-fe1ab3886dee/scratchpad/d4r/dom_probe.py`) at `68ebe81`. It
renders 28 states of the Tools tab against a real `dr-library serve`, with ids and timings normalized. Its output is
byte-identical to r3's at `3129da9`, which equalled the output at `01abb88` and the Refactorer's baseline and final
files. So `f553260` changes none of those 28 states. [run: `cmp`]

### 7.5 B30 and the stdio case, run

- **The frame.** `mcpServersFromSettings` ran through `vite-node` on one remote server per strategy, each with its own
  header `X-Trace`. The results [run at 3129da9; `context.ts` is unchanged since]:
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
  `POSTGRES_X_TRACE` missing. [run at 3129da9; the Python is unchanged since]
- **The stdio case.** See §1.3 #10: the row is no longer changed. [run]

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
3. **The live tier** ran in CI only, at `3129da9`. I did not dispatch it at `68ebe81`, and no one has; §7.1 says why
   it stands. Its log records no model name and no token cost; gpt-6-luna is the starter profile's model, read in the
   code.
4. **The evidence step** (§1 #14) ran here, extracted from `live.yml`, not on GitHub's runner: no live run has failed
   since `6e07549`, so the step has not run there. I ran it as root with two capabilities dropped, not as the runner's
   user.
5. **The stack** ran only in CI. I ran no level locally, and the live tier ran at no level. `main` `53c821b`'s CI run
   was in progress when I read it.
6. **macOS**: nothing ran there, not the guard, not `check_env`'s password database, not the group kill.
7. **Remote servers** ran only against the local fake servers over loopback. OAuth servers and slow networks did not.
8. **The read claims that matter most:**
   - §4.4, that secrets never enter the worker's environment: the tests check the logs and the transcript, not
     `/proc/<worker>/environ`;
   - §4.7, that `library.path.parent` is `$DR_HOME`;
   - B28's branch (a JSON-RPC error with a code other than 408 or −32000), which no fake server sends.
