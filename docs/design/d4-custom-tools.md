# D4 · Custom tools — design

**TASK-9** · System Designer · task branch `v1-custom-tools` in
[deep-reasoning](https://github.com/michaeltheologitis/deep-reasoning) (v1 was written on `design/d4`, `e14fda7`; v2
and v3 on the task branch; v4 on `design/d4-v4`, cut from it at `f69bc73` and merged back; v6 on `design/d4-v6`, cut
from it at `68ebe81`) · against the approved
spec [TASK-1](https://app.notion.com/p/3ed62fb22237814ab425c81b3844f012) (D4 in full; §1's "done when"; §2's
decisions 1 and 7; §4's E9, E10 and the live tier; the dated notes at its end, read live on 2026-10-03, through "Scope
additions approved, 2026-10-03").
**Pinned against:** D3's design at `ab6f2ec` on `design/d3` (§8.3 is D4's UI contract; §2.5, §4, Appendix A) · D2 as
built on `v1-library-store` at `90044f0` (`src/deep_reasoning/library/`; its design `555472b`, §6.5 and §9 items 7
and 10) · D1's design at `c8d7fbb` (§4.3, §4.4, §4.7, §4.8) and its code as merged into `90044f0` · D5's design at
`8086afb` (§2, §4.7, §7.1) · SDK fork `deep-reasoning` at `91430aa` (`acp_agent.py`, `settings_router.py`, the App
bridge; `mcp` 1.28.1 in its lock) · deep_reasoner_beta `d7334ae` · `agent-client-protocol` 0.12.1 · `mcp` 1.28.1 for
v1's probes; 1.30.0 as this branch's lock resolves it (v2, §6.2 B10).

**Matches the build at `68ebe81`** (v6): D4's code as v4 and v5 had it at `f69bc73`; B30, decided at Gate B (`87f24e5`,
`e32bc3d`); D3's finished head merged, after its literate refactor (`fd0fc84`, `a87e898`, `3f85560`, `e866563`,
`01abb88`, `3129da9`), which brought D2's refactored code head `0e0a394` and D1's `f7a91f3`; D4's literate refactor (12
commits, `be131ce` … `dcd84af`); and four commits after the as-built r3 (`f553260`, `6e07549`, `6739e0f`, `68ebe81`).
§6.2 B30–B37 give each change its reason and its test, and the sections they name say it in place. Of D4's Python, only
`tools/` changed: `src/deep_reasoning/mcp/` is as it was at `f69bc73`. v6 changes only this file. `main` holds the same
code since the merge, at `53c821b` (the next paragraph). (v4 and v5 matched `f69bc73`: D4's code, `cd3e153` … `f69bc73`,
on D3's finished head `d4e9cd3`, merged at `aa67f0a`; D4 was first stacked on D3's `5effe26`. v3 matched `aa67f0a`, v2
`965f318`; `756f5f9` added the as-built document, `as_built/d4-custom-tools.md`, and excluded `as_built/` from the
sdist.)

**Merged, after Gate C** (v6, 2026-10-04). Michael accepted D4 at Gate C, and its seven PRs, #27 to #33, merged
bottom-up into `main` (`cbcad70` … `53c821b`). Each was against the one below it, and #27 against `main`, on D3's top
PR's head `c60d6d9`, which `main` holds (D3's #19–#26, merged as `1f9fe52`). `main`'s tree at `53c821b` equals #33's
head `c95e059`, which is this branch's tree at `68ebe81` but for the design and as-built documents, which no PR carried,
the sdist's exclude of `as_built/`, and two files `main` has newer (`docs/deep-reasoner-contract.md`,
`tests/acp/test_stop.py`). So this design states the code `main` holds at `53c821b`. What was read beside each PR is the
table in #33's description, "Gate C: reading beside the PRs", which cites v6 and the as-built document's revision 4
(`497d56b`, on `as-built/d4-r4`). What changed since Gate B, each change with its commit, is §6.2's last two groups,
B30–B37; the tests that carry each property are the table "Which tests carry which property" in the Gate B section,
current at `68ebe81` (its v6 marks), and §10 maps every test file. The evidence at `68ebe81`: CI [run
37186335030](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37186335030), on push, both jobs green:
**694 passed** (84 deselected), vitest **214 passed, 1 skipped**, the browser tests **76 passed, 1 skipped**; `app.js`
167.27 kB, `editor.js` 348.48 kB (run 37184460145, at the same commit, the same); after the merge, `main`'s push run at
`53c821b`, [37187128304](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37187128304), is green with
the same counts, as was every level of the stack (as-built r4 §7.1). The live tier last ran at `3129da9` ([run
37180265916](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37180265916), **7 of 7**, D4's two among
them, B37). No live run is at `68ebe81`: the four commits since change the frame's `mcpRows`, tests, and the live job's
steps that run only after a failure (B35, B36), none of them code a live test runs.

## Gate B: what to read

*(v6: this section is kept as Gate B read it, with v5 and the as-built r2 at `f69bc73`, but for marked v6 notes. Its
third ruling was decided (b), built as B30. Its property table, "Which tests carry which property", is current at
`68ebe81`, its v6 marks naming the tests added since.)*

**About 75 minutes, in this order.** The codebase stays closed. The Gate B set is this doc, D4's as-built document and
the three runs below. The as-built document is `as_built/d4-custom-tools.md`, revision 2, on this branch since
`2353fe6`: the Cartographer's reading of the code at `f69bc73` against design v3, which also reports E9's and the live
tier's measured results. Its §1 numbers the divergences: #1–#8 are this design's B24–B27 (v4), and #9–#13 are answered
in v5 (B28, B29, the third ruling below, §4.8 with §14 item 15, and §14 item 17). Everything after §6 is kept whole as
the reference that D1's, D3's and D5's next revisions and the Gate C reviewers work against (Michael: don't force
compression); Gate B does not need it.

| # | Read | What it gives you | Minutes |
|---|---|---|---|
| 1 | This section and the v5, v4, v3 and v2 revision lines below it | where the proof is, the live tier's record, what to rule on, and which sentences of v1–v4 changed | 12 |
| 2 | §1 | what D4 is, and the decisions under it (F and L changed in v2) | 10 |
| 3 | §2 | the Tools tab, and what the conversation and the agent are told | 8 |
| 4 | §5 | what a tool or an MCP server can reach, said plainly | 4 |
| 5 | §6.1 | where the design departs from the spec: written at design, not yet ruled on | 6 |
| 6 | §6.2 | what the build changed (B1–B29), each with its reason and the test that pins it; B24–B29 are new since v3 | 17 |
| 7 | §11.1, its last part | the RunEvent D4 adds to `dr-acp`, and its three sentences | 3 |
| 8 | Open the three runs below | that CI is green and the live tier passed twice, 6 of 6, at `f69bc73` | 3 |
| 9 | `as_built/d4-custom-tools.md`, r2: §1, then §7 | its divergences from v3 (#1–#13), and E9 and the live tier as measured | 14 |

**Three things to rule on.** Michael has not ruled on the first two for D4; v2 and v3 asked both, and both are
refreshed here to `f69bc73`. The third is new in v5, from the as-built r2.

1. **D4's departures from the spec** (§6.1, fourteen items, unchanged since v1) **and the build's changes** (§6.2,
   B1–B29). The spec's dated notes accept D2's departures and S1's and S2's ("Rulings at design, 2026-10-02" (2),
   (3)); none names D4's, so they reach Michael here. The ones a user meets: saving runs Check and refuses a tool that
   cannot build (§6.1 item 1); Check runs without secrets or a model (item 2); six names are reserved (item 3); a
   granted server that a conversation was not given, or that does not answer, leaves a stand-in and a notice (item 7,
   §2.2); a grant reaches child namespaces and sub-agents spawned into a granted one (item 5), and a hand-off outside
   it is refused (item 6); under plain `dr` an export needs each server's secrets in the environment (item 8); the
   tool editor's CodeMirror chunk is 348 KB against a 300 KB budget (§6.2 B3). Since v2: a server that `open_session`
   cannot start or bind fails alone and the run goes on (B19), while a namespace error still fails the build, in one
   case where `build_reasoner` alone would not (§14 item 16); a write of the other kind over a tool's row is refused,
   `409` (B20). Since v3: a tool property whose schema is `true` or `false` is described as `Any` or `Never` instead
   of failing its server (B26); that changes the shim's text, so a grant made before it reads `MCP_SHIM_OLD` until its
   **Update** (none exists outside the tests: nothing has shipped). And one about the proof, not the product: the two
   live tests now name the tool and the server in the task (B27), so they pin that each is bound and works when the
   agent calls it, not that gpt-6-luna reaches for it unprompted, which twice it did not. Since v4, two places where
   v3 described the build wrongly and the build is right (as-built r2 #9, #10): a server's JSON-RPC error reaches the
   cell in the server's words, without the type `McpError` (B28); a `422 invalid` on Save shows D2's message, one line
   per field error, without marking the fields (B29). Already ruled, on 2026-10-03 (relayed by the Conductor): a
   server's command-line arguments are not secrets, so a server's log redacts its env and header values only (B18, §14
   item 3).
2. **Size.** The spec costed D4 at **≈1.0k lines with tests** and ≈3 h at Gate C; v1 estimated ≈2.0k of code and
   ≈2.2k of tests (§13). The build is **3,399 lines of code and 3,778 of tests** at `f69bc73`, 7,177 in all, about
   seven times the spec's figure and about 24 h at Gate C at the workspace's rate. These are lines added over D3's
   finished head `d4e9cd3`; not counted are the built files, the two lock files, D1's golden recordings (18 one-line
   changes), `tests/mcp/fixtures/shim_v1.py` (539 lines, the v1 shim frozen as a Library stores it) and the live
   job's 18 lines in `.github/workflows/live.yml` (B25). Since v3 (`aa67f0a`: 3,397 and 3,686): 2 lines of code, the
   shim's `_type` (B26), and 92 of tests, the two fake servers and three tests of B24 and B26 and the live tests'
   changes (B25, B27). The breakdown is §6.2 B16. The build recorded no reason for the growth; the estimate was this
   design's. The Scout and the Refactorer, after Gate B, are where it shrinks; §13 names two parts that cut cleanly.
   *(v6, B37: at `68ebe81`, **3,314 and 3,807**, 7,121 in all, measured the same way over D3's refactored head
   `73c6425`; the golden recordings are 20, each with its one changed line.)*
3. **An export does not carry a remote server's `auth`** (as-built r2 #12; v5). Canvas's MCP settings can hold a
   remote server's credential in `auth` (bearer, basic, API key or named headers) instead of `headers`. The bridge
   forwards header-compatible `auth` as headers (SDK fork `acp_agent.py:717–736`), so in a conversation the server
   gets it and `dr-acp` redacts it. But the frame snapshots only the keys of `headers` (`page/context.ts:147`), so a
   grant's block names no variable for `auth` (`mcp/grants.py:79`), and under plain `dr` an export connects without
   the credential: the server refuses it, and the agent meets a stand-in or a failed call. That breaks what §4.8 and
   §6.1 item 8 promise, an export that runs under `dr` with each secret read from the environment. The code does what
   §7.5 says; §7.5 is what is wrong, so the fix is the code's. The choices: (a) as built, with `MCP_EXPORT_NOTE`
   saying that a credential set in `auth` is not exported; one sentence. (b) `mcpServersFromSettings` adds to
   `headers` the names `auth` would send, all of them non-secret settings: `Authorization` for bearer, basic, and an
   API key without a header name; the API key's header name; a header strategy's keys; none for `none` or OAuth (read
   from the SDK fork's `mcp/config.py` at `91430aa`, not run, as §7.5's shapes were, §14 item 12). The grant then
   names a variable for each (`POSTGRES_AUTHORIZATION`), which under `dr` holds the whole header value (`Bearer …`),
   and **Update** offers itself on grants made before. About 10 lines and a `context.test.ts` case, written
   test-first, landing before the Scout; OAuth stays unexported (§14 item 6). **Recommended: (b)**: it keeps the
   export promise for the commonest remote credentials, through the snapshot path that already exists. Nothing changes
   in code until Michael rules. *(v6: Michael decided (b), and it is built: §6.2 B30, `87f24e5` and `e32bc3d`. The
   frame names the headers for a stdio server's `auth` too, which no stdio block keeps and no comparison reads, B35.)*

**The evidence.** All three runs are at `f69bc73`, the branch's head and its last commit that touches code or tests.
(v3's, at `aa67f0a`, were CI [run 37145903416](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37145903416),
green, and live [run 37145903109](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37145903109), red;
v2's, at `965f318`, CI [run 37106223937](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37106223937)
and live [run 37106223637](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37106223637), 6 of 6.)

- **CI**, [run 37157785695](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37157785695), on push:
  two jobs, both green. `test` (8 min): `ruff check`, `ruff format --check` and the deterministic suite, **683
  passed** (the 6 live and 73 browser tests deselected, nothing skipped) in 7 min 47 s; 149 of the 683 are D4's
  (`tests/tools/` 69: `test_check.py` 42, `test_routes.py` 27; `tests/mcp/` 80: `test_shim.py` 23, `test_session.py`
  17, `test_grants.py` 17, `test_acp.py` 16, `test_wire.py` 6, `test_export.py` 1), and D1's
  `tests/acp/test_encoder.py` carries D4's notice test (three cases). `canvas-app` (4 min): typecheck, format check,
  vitest **190 passed, 1 skipped** (D3's), the build (`app.js` 169 KB, `editor.js` 348 KB, §6.2 B3) and "the
  committed build is what a fresh build gives", then the browser tests in Chromium against a real `dr-library serve`,
  **72 passed, 1 skipped** (D5's `dr_app` is not installed) in 2 min 49 s; 17 of the 72 are D4's. No test in CI
  calls a model: the model is `FakeOpenAI` on 127.0.0.1, and every MCP server is a real one of ours written with
  `mcp` (FastMCP, or its low-level `Server` for `odd_server.py`), over stdio, streamable HTTP or SSE.
- **Live tier, twice**, on gpt-6-luna, on demand (`.github/workflows/live.yml`, `pytest -m live`):
  [run 37157799600](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37157799600), **6 of 6** in
  120 s, and [run 37157801762](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37157801762), **6 of
  6** in 79 s. The six, as they run on this branch: D4's two,
  `tests/tools/test_live.py::test_live_a_tool_written_in_the_library_is_used_by_the_agent` and
  `tests/mcp/test_live.py::test_live_an_mcp_server_granted_to_the_namespace_is_used_by_the_agent`; D1's three,
  `tests/acp/test_live.py::test_live_the_stream_rebuilds_deep_reasoners_tree_and_the_root_pays_for_all`,
  `::test_live_stopping_a_department_stops_it_and_its_course_agents` and
  `::test_live_without_the_key_the_run_fails_before_any_call_and_says_which`; and D2's one,
  `tests/library/test_live.py::test_an_edited_decomposition_reaches_a_real_run_at_its_saved_version`. Since `9255778`
  the job keeps a failed run's evidence (§6.2 B25); neither run failed, so neither kept any.

**The live tier's record on this branch, said plainly.** Since v2, D4's two live tests failed in four of eight
attempts: the tool test twice at `7eb7812` and the MCP test twice at `aa67f0a`. Both passed in every attempt at the
head.

| Run (attempt) | At | Tool test | MCP test | D1's three and D2's one |
|---|---|---|---|---|
| [37106223637](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37106223637) | `965f318` (v2) | passed | passed | passed |
| [37145903109](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37145903109) (1) | `aa67f0a` (v3) | passed | **failed**: `exhausted` | passed |
| 37145903109 (2) | `aa67f0a` | passed | **failed**: `failed` | passed |
| [37149393726](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37149393726) | `7eb7812` | passed | passed | D1's tree test failed (OpenAI refused a department's first call, as D1's `ac2ac87` reads it) |
| [37153297958](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37153297958) (1) | `7eb7812` | **failed**: `exhausted` | passed | passed |
| 37153297958 (2) | `7eb7812` | **failed**: `exhausted` | passed | passed |
| [37157799600](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37157799600) | `f69bc73` | passed | passed | passed |
| [37157801762](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37157801762) | `f69bc73` | passed | passed | passed |

- **The tool test failed twice at `7eb7812`**, in both attempts of run 37153297958. Asked "How many credits is course
  ZQ-417?", gpt-6-luna answered from nothing instead of using the REPL: 30 turns in each attempt and no cell written;
  in the first, 9 replies were "4 credits." and 21 were empty; in the second, 18 said 4 credits. The tool says 7.
  Each prompt ended `exhausted` at deep_reasoner's turn limit. The tool was built, bound and described
  (`course_credits(code: str) -> int`), and the question was the one that had passed at `965f318`, twice at
  `aa67f0a`, and in run 37149393726 at `7eb7812` (`933ac08`'s account, read from the evidence B25 kept).
- **The MCP test failed twice at `aa67f0a`**, in both attempts of run 37145903109: the first prompt ended
  `exhausted`, the second `failed`. Neither kept evidence (the job kept none before `9255778`), so why is not known.
  `exhausted` fits the tool test's cause; `failed` does not, because a `failed` prompt is an error in the run, not a
  model that would not call the server, and nothing since explains it. The test has passed in all five attempts
  since: three at `7eb7812`, still asked bare ("What must a student finish before ZQ-417?"), calling
  `catalog.prerequisites` from its first turn (`f69bc73`), and two at `f69bc73`. (v3 read the first attempt only; the
  second, the re-run §14 item 8 asks for, failed too. `f69bc73`'s message says the test failed "once" at `aa67f0a`;
  the run's two attempts say twice.)
- **What changed.** `933ac08` and `f69bc73` name the tool and the server in the task, and keep every assertion
  (§6.2 B27, §10.5): "Use course_credits to find how many credits course ZQ-417 is." and "Use the catalog server to
  find what a student must finish before ZQ-417." So the live tier pins that a tool written in the Library, and a
  server granted to the namespace, is bound into a real run and works when the agent calls it. It no longer pins that
  the model chooses to call it (§14 item 8).

**Which tests carry which property.** Each test's name states the property it pins. Python files are under
`tests/tools/`, `tests/mcp/` and `tests/canvas_app/`; `[…]` is a parametrization.

| Property | Tests |
|---|---|
| **E9, your own tool.** A tool that cannot build is found by Check, in deep_reasoner's own words, and cannot be saved; a failure Check cannot attribute (the factory raised, ran past its limit, or Check did not start) is saved only when asked; a grant-only change runs no Check. Check and `make_tools` agree on every fixture. | `test_check.py::test_check_and_make_tools_agree[works, not_func, misspelled, import_error, hang, env_at_build, prints, exits]` (Check's `ok` is whether deep_reasoner's own `make_tools` builds the same materialized config in a subprocess, and where deep_reasoner words the failure, the same words); `::test_a_factory_that_returns_no_func_fails_check_in_deep_reasoners_words`; `::test_a_misspelled_factory_fails_check_naming_what_the_file_defines`; `::test_an_import_of_a_missing_module_fails_check_and_cannot_be_saved_anyway`; `::test_a_hanging_factory_is_stopped_at_the_build_limit`; `::test_nothing_a_stopped_tool_started_is_left_running`; `test_routes.py::test_a_tool_that_cannot_build_is_not_saved[not_func, misspelled, import_error]` (422 `check_failed` even with `accept_check_failure`; no revision made); `::test_a_structural_failure_cannot_be_saved_anyway`; `::test_save_anyway_stores_a_raising_tool_only_when_asked`; `::test_a_grant_only_change_runs_no_check` |
| **Check builds a tool as a conversation would**, minus what only a conversation has (secrets, a model, its folder) | `test_check.py::test_a_working_tool_builds_and_says_what_the_agent_is_told` (deep_reasoner's own `describe()`); `::test_the_tried_expression_is_evaluated_with_the_tool_bound`; `::test_check_never_reaches_a_model` (a factory calling the model gets a connection error; a fake model on another port records nothing); `::test_check_gets_no_secret`; `::test_printing_cannot_corrupt_the_report`; `::test_a_tool_that_ends_the_process_is_raised_saying_how_it_ended`; `::test_an_example_that_ends_the_process_says_how_and_the_build_stays_ok`; `::test_a_check_whose_process_cannot_be_started_is_unavailable`; `::test_the_temporary_folder_is_removed[word_count, hang]`; `::test_not_func_and_unknown_factory_sentences_equal_make_tools` (a tripwire on deep_reasoner's inline text); (v6) `::test_a_report_line_of_a_phase_not_awaited_is_skipped` (the supervisor, awaiting a phase, skips a line of any other, §6.2 B32); and through `dr-acp`, a tool saved through the API is built and called: `tests/mcp/test_acp.py::test_a_tool_saved_through_the_api_is_built_and_called_in_the_next_conversation` |
| **E9, MCP servers, end to end through `dr-acp`.** A server that crashes or never answers blocks neither the session nor the run and takes nothing down with it, nor does one that `open_session` cannot start or bind (v3), nor one that prints more than a pipe holds (v4); one not granted to an agent's namespace is not in that agent's REPL or prompt; a grant reaches child namespaces and sub-agents spawned into a granted namespace; a hand-off outside the grant is refused; no stdio server outlives its run | `test_acp.py::test_a_granted_server_is_bound_and_a_cell_calls_it`; `::test_a_server_that_crashes_at_start_is_reported_and_the_run_answers`; `::test_a_server_that_crashes_mid_run_fails_the_call_and_the_run_goes_on` (the next cell and the next prompt are answered); `::test_session_new_does_not_wait_and_the_first_answer_waits_at_most_the_deadline`; `::test_a_server_granted_elsewhere_is_not_in_this_agents_repl_or_prompt` (a cell's `dir()` and the fake model's first request lack it); `::test_a_sub_agent_spawned_into_a_granted_namespace_gets_it`; `::test_a_grant_reaches_a_child_namespace`; `::test_handing_a_server_to_an_ungranted_namespace_is_refused`; `::test_no_stdio_server_outlives_a_root_stop`; `::test_no_stdio_server_outlives_a_closed_session`; `test_session.py::test_servers_connect_at_once_and_a_silent_one_is_given_up_at_the_deadline`, `::test_a_server_granted_nowhere_is_not_started`, `::test_a_server_granted_only_where_spawning_is_not_allowed_is_not_started`, `::test_a_server_given_up_is_ended_within_three_seconds`, `::test_a_server_open_session_cannot_bind_fails_alone_and_the_others_bind[its log cannot be opened, its block has no number, it cannot be told]`, (v4) `::test_a_server_that_prints_more_than_a_pipe_holds_answers_and_its_log_is_redacted` (1 MB at start and 256 KB a call: bound, and three calls answer), and the one error that still fails the build, `::test_a_namespace_registry_deep_reasoner_refuses_fails_the_build_as_it_would_anyway`; `test_shim.py::test_a_call_that_never_answers_raises_after_its_timeout`, `::test_the_guard_ends_its_server_when_its_parent_is_killed` |
| **MCP grants are D2 tool rows** (decision D): the block snapshots the server, the source is the shim, `granted_in` grants it, a resend unchanged makes no version; neither kind of write replaces the other kind's row (v3); export and re-import keep a grant a grant; an export runs under `dr` | `test_routes.py::test_put_mcp_writes_the_block_and_the_shim_and_grants`; `::test_put_mcp_resent_unchanged_makes_no_tool_version`; `::test_a_server_cannot_be_granted_under_two_names`; `::test_put_mcp_refuses_a_name_the_repl_cannot_bind[run_all, not a name, class]`; `::test_an_mcp_block_through_put_tools_is_refused`; `::test_a_grant_cannot_replace_a_tool_of_your_own[new, the head's]`; `::test_a_tool_of_your_own_cannot_replace_a_grant[new, the head's]`; `::test_a_put_mcp_body_it_cannot_read_is_told_the_mcp_bodys_fields[no base_version, a yaml it does not have]`; `::test_get_mcp_lists_grants_with_their_last_seen_tools`; `::test_get_mcp_says_when_a_grant_has_an_old_shim`; `test_grants.py::test_is_mcp_tool_needs_the_factory_and_the_marker[…]`, `::test_an_exported_and_reimported_grant_is_still_a_grant`; `test_export.py::test_an_exported_grant_runs_under_dr` (`dr-library export`, then `dr` with `ECHO_TOKEN` in the environment: exit 0, the server's answer); `test_shim.py::test_a_stored_v1_shim_works_with_todays_session` (v4: a stored text older than today's, §6.2 B26) |
| **The shim's token** (a server's secret): it reaches the server from what the client forwarded, or under `dr` from the environment, and nothing else: not the Library or an export, the run log, the transcript, the worker's log, the server's own log (v3) or a failure's detail; a forwarded server that no grant names is never started | `test_wire.py::test_a_run_gets_only_the_specs_its_blocks_name`, `::test_redact_replaces_every_secret_value`; `test_session.py::test_a_server_that_exits_at_start_is_failed_with_its_stderr_redacted[whole, split]` (the server's log reads `invalid token [redacted]`, the token printed in one write or two), (v4) `::test_a_server_that_prints_more_than_a_pipe_holds_answers_and_its_log_is_redacted` (its log is every line it printed, the token `[redacted]` in each); `test_acp.py::test_server_secrets_never_reach_the_run_log_or_the_transcript` (a crashing server prints its token: it is in none of `events.jsonl`, the ACP stream, `worker.log` or the server's own log), `::test_a_server_that_crashes_at_start_is_reported_and_the_run_answers` (its notice reads `invalid token [redacted]`), `::test_a_forwarded_server_no_grant_names_is_never_started`; `test_shim.py::test_the_shim_connects_from_its_block_with_env_from_the_environment`; `test_routes.py::test_put_mcp_writes_the_block_and_the_shim_and_grants` (the block holds variable names only); the live tier's MCP test (the token is nowhere in the run log or the updates) |
| **What the conversation is told** (§2.2, §11.1): one root notice per server not bound, in native and flat mode and on replay; what the agent is told of a bound server, a tool whose properties take any value or none included (v4); the seen cache | `tests/acp/test_encoder.py::test_each_mcp_server_not_bound_is_a_notice_on_the_root[native, flat, replay]`; `test_acp.py::test_the_notice_replays_on_load`, `::test_the_seen_cache_is_written_for_bound_servers`, `::test_dr_acp_advertises_http_and_sse`; `test_session.py::test_statuses_carry_what_the_agent_is_told`, (v4) `::test_a_tool_whose_properties_take_any_value_or_none_is_bound_and_told_so`; `test_shim.py::test_the_description_is_what_8_4_says`, (v4) `::test_properties_that_take_any_value_or_none_are_described_as_any_and_never` (both told `odd.odd(anything: Any = …, nothing: Never = …) -> str`, §6.2 B26) |
| **The Tools tab** (§2), in Chromium against a real `dr-library serve` | `test_tools_tab.py::test_the_risk_line_is_under_the_safety_banner`; `::test_a_new_tool_is_written_checked_and_saved_with_its_grants` (the stored source byte for byte); `::test_check_shows_what_the_agent_is_told_and_the_tried_value`; `::test_a_tool_that_cannot_build_shows_why_and_cannot_be_saved[not_func, misspelled, import_error]`; `::test_a_hanging_factory_shows_the_limit`; `::test_a_raising_factory_offers_save_anyway`; `::test_a_grant_tick_on_a_saved_tool_saves_without_unsaved_code`; `::test_an_inherited_grant_is_fixed`; (v6) `::test_an_inherited_server_grant_is_fixed` (§6.2 B33); `::test_the_editor_keeps_python_indentation`; `::test_canvas_mcp_servers_are_listed_and_granted_per_namespace`; (v6) `::test_a_later_tick_keeps_the_granted_settings` (a tick resends the stored snapshot, not Canvas's changed one, B33); `::test_a_disabled_server_says_so_and_can_still_be_granted`; `::test_a_grant_gone_from_canvas_offers_remove`; `::test_a_changed_server_offers_update` (v6: `[its settings, a header a stdio block does not keep]`, B35); `::test_the_last_seen_tools_are_shown`; `::test_without_canvas_settings_only_grants_are_shown`; D3's two Tools-tab tests stay green. vitest: `context.test.ts` (`mcpServersFromSettings`: no value of `env` or `headers` in the output; `readMcpServers`; v6: the header names an `auth` sends, B30), `tools.test.ts` (v6: `changed` compares what the block keeps, per transport, B35), `api.test.ts` (a `422 check_failed` carries the report), `protocol.test.ts`, `mount.test.ts` (Canvas's MCP servers are read for the Tools tab only) |
| **Live tier**, on gpt-6-luna (spec §4 layer 5: "a tool written in the Library, and an MCP server, each used by an agent"): a tool or a server is bound into a real run and works when the agent calls it; since v4 the task names which (§6.2 B27), so the model's choosing it is not pinned. Both passed twice at `f69bc73`, and (v6) once at `3129da9`, run 37180265916, 7 of 7 (B37); the record above has their failures | `tests/tools/test_live.py::test_live_a_tool_written_in_the_library_is_used_by_the_agent`: `PUT /tools/course_credits` through the API (the gate and the real Check run; Check says `built`), granted to `root`; "Use course_credits to find how many credits course ZQ-417 is." (v4; v1–v3 asked "How many credits is course ZQ-417?") → the outcome is `answered`, the answer contains `7`, and a cell called `course_credits(` and printed `7`. `tests/mcp/test_live.py::test_live_an_mcp_server_granted_to_the_namespace_is_used_by_the_agent`: `PUT /mcp/catalog` granted to `root`; `session/new` forwards our catalog server with a random `CATALOG_TOKEN`, without which it refuses to answer; "Use the catalog server to find what a student must finish before ZQ-417." (v4; v1–v3 asked "What must a student finish before ZQ-417?") → the outcome is `answered`, the answer contains `ZQ-101`, `mcp.status` says `bound`, a cell called `catalog.prerequisites(`, and the token is nowhere in the run log or the updates |

§10 maps every test file; §6.2 B15 lists the names v2 added, B18–B27 v3's and v4's, and B32–B35 v6's.

**Revisions** (newest first; each line says which sentences to stop trusting):
- 2026-10-04 · v6 · brought in line with the build at `68ebe81`, which Michael accepted at Gate C and which merged into
  `main` as #27–#33 (`cbcad70` … `53c821b`, its tree #33's head `c95e059`). Since v5: B30, decided at Gate B and added
  to v5 without a revision line (`aa1774c`, `60f1d00`); D3's refactored head merged; D4's literate refactor; and four
  commits after the as-built r3 (`461c3b5`), which answered its #10, #11 and §7.4. B-numbers are §6.2's. Stop trusting:
  the "Matches the build" line; the Gate B section's third ruling, "nothing changes in code until Michael rules" (ruled
  (b), B30); B30's "a grant made before offers **Update**", which holds for HTTP and SSE only (B35); §2.2's and §8.6's
  account of a changed server (B35); B25's and §10.5's check of the model key alone (B36); §3.3's `mkdtemp`, `loaded`,
  `done` and where `seconds` starts (B32); every `json_route` (§7.1, §7.2, §11.2, B12, B16, A.2, A.5; B31);
  `ui/tools.ts`'s exports and `McpSnapshot`'s place (§7.4, §10.4, B8, A.6; B33); the test name in B15 and §10.3 (B34);
  "18" golden recordings and `app.js`'s 169 KB (B11, B16, §7.4, §11.3; B37); A.1's `require_check`, which raises
  `LibraryRefused` too (B20, v3); §7.5's v5 note and §14 item 6's (B30, B35); §14 item 17's trial merge (now merged).
  Added without changing earlier sentences: the "Merged" paragraph; §6.2 B31–B37 and B30's commits; §4.2's note on what
  a block keeps per transport; v6 notes in §2.2, §3.3, §7.1, §10.3, §10.4, §10.5, §13 and §14 item 17; the property
  table's v6 tests; the Gate B section's v6 preface. §6.1 and B1–B29 stand as v5 left them, but for the marked v6 notes
  in B8, B11, B12, B15, B16 and B25. No section is renumbered.
- 2026-10-03 · v5 · answers the as-built r2 (`2353fe6`, its #9–#13); no code changed. Stop trusting: §2.1's and
  §3.2's account of a `422 invalid` (B29); §4.3's `CALL_FAILED` "with the innermost exception" for an `McpError`
  (B28); "not run" in §4.8 and §14 item 15 (r2 ran it); §14 item 17's numbers (now r2's). Added: §6.2 B28–B29; the
  third ruling, on `auth` in an export (r2 #12), with notes in §7.5 and §14 item 6; the reading list, now r2.
- 2026-10-03 · v4 · brought in line with the build at `f69bc73`: five commits after v3 (`1847ef0`, `9255778`,
  `7eb7812`, `933ac08`, `f69bc73`); B-numbers are §6.2's. Stop trusting: the Gate B section's reading table, evidence,
  rulings and size (now `f69bc73`'s: CI green, the live tier twice 6 of 6), and v3's account of the live tier (the MCP
  test failed twice at `aa67f0a`, not once, and the tool test twice at `7eb7812`: the record is now in the Gate B
  section); the "Matches the build" line; the property table's live-tier row (B27); §8.4's types, which now read a
  boolean schema (B26); §10.5's two questions (B27); §14 item 8 (now only partly true) and item 15 (fixed for boolean
  schemas, B26); B16's and §13's totals (3,399 and 3,778) and B16's file sizes; B19's example of a binding that cannot
  be described, and B23's "byte-identical" (both changed by B26). Added without changing earlier sentences: §6.2
  B24–B27; v4 notes in §4.4 (B24), §4.8 (the one plain-`dr` case that still stops a run), §10.2 (the fake servers),
  §10.3 (v4's tests) and §10.5 (the kept evidence, B25); the property table's v4 tests; §14 item 17 (D4's head and
  `main`); Appendix A's preface. §6.1 and B1–B23 stand as v3 left them, but for B16, B19's example and B23's second
  bullet.
- 2026-10-03 · v3 · brought in line with the build at `aa67f0a`: five D4 commits after the as-built document
  (`059b738`, `c2cfdc0`, `55f139f`, `4a86581`, `6fdee0d`) and D3's finished head merged; B-numbers are §6.2's. Stop
  trusting: the Gate B section's evidence, rulings and size (now `aa67f0a`'s; its live run is red, one MCP test
  `exhausted`, pending §14 item 8's re-run); §4.4's pseudo-code where a stdio
  server's stderr went straight to its log (B18); v2's note in §11.1 that an error about one server inside
  `open_session` fails the build (B19); §2.2's and §4.2's `409` for a taken name, which held only
  at `base_version: 0` (B20); §7.2's 400 for `PUT /mcp`, which named D2's `yaml` (B21); B7's "not pinned" (now
  pinned); B16's and §13's totals (3,397 and 3,686). Added without changing earlier sentences: §6.2 B18–B23; §4.5's
  row for a server `open_session` cannot start or bind; §3.5's line for a `PUT /tools` over a grant; §9.1's
  `MCP_NAME_TAKEN` and `MCP_BAD_REQUEST`; §11.2's `_parse` note; Michael's ruling that a server's arguments are not
  secrets (§5, §14 item 3); §14 items 15 and 16; A.3's `PIPE_READ` and `DRAIN_S`; A.5's `_parse`; §10's v3 tests.
  §6.1 and B1–B17 stand as v2 wrote them, but for B7, B12 and B16.
- 2026-10-03 · v2 · brought in line with the build at `965f318`, after Proof Green; B-numbers are §6.2's. Stop
  trusting: §1.1 decision F's one deadline (B5) and decision L's route through D3's `CodeField` (B1); §2.1's tool-row
  text and its `def make(:` cell (B8, B14); §3.3's two `CHILD_ENDED` phases (B7); §4.3's annotated `Server.__call__`,
  the stand-in's every-attribute rule, and the call in flight on a dead server (B4, B6); §4.4's and §8.2's one
  deadline, and what `seconds` holds (B5); §4.5's rows for a call's timeout and for a server that dies (B6); §4.6's
  exit code after a signal (B9); §7.4's `CodeField` line and its 300 KB budget (B1, B3); §9.1's names as constants
  (B9); §10.2's fixture list, §10.3's re-recorded goldens and §10.4's `library_home` sentence (B11, B13, B14); §12's
  M1 and M2 line numbers (B10); §13's totals (B16); A.1's `ToolCheckFailed`, A.3's `Connection`, `Server.__call__`
  and `Unavailable`, A.6's `PythonEditor`, `ToolEditorProps`, `CheckResultProps` and `McpServerRowProps` (B2, B4, B8,
  B9). Added without changing earlier sentences: the Gate B section and the "Matches the build" line; §6.2; §11.1's
  account of `mcp.status` and its sentences, as D1's next revision should carry them; §12's M3; §14 items 10–14; the
  marked v2 notes in §2, §3.2, §7, §8.3, §8.6, §9, §10, §11.2–§11.4 and Appendices A and B. Appendix A's Python
  blocks are now exactly ruff-formatted (v1 had seven lines past 88 characters; no content changed there). §6.1 (v1's
  §6) keeps every item as written, with marked v2 notes on items 4, 11, 13 and 14. Every change is listed, with its
  reason, in §6.2.
- 2026-10-03 · v1 · first full-depth version.

**Where this file lives, and why nothing trips over it.** `docs/design/d4-custom-tools.md` on the task branch
`v1-custom-tools` (v1 also on `design/d4`, which holds only documents; v6 on `design/d4-v6`, which changes only this
file). Pytest collects `tests/` only, the wheel is built from `src/deep_reasoning`, the sdist excludes `docs/`, and ruff
excludes `docs` (D1 §8.5; v2: and `tests/mcp/fixtures`, §6.2 B12). D3's TypeScript tools run inside `canvas-app/` only
(D3 §4.1), so they never see `docs/`. The PR split leaves this file behind.

**Reading guide.** After the merge (v6): the "Merged" paragraph at the top, #33's table beside each PR, and §6.2
B30–B37 for what changed since Gate B. Gate B: the section above. D1's next revision: §11.1, whose last part is the
event and sentences D4 added to `dr-acp`. D2's, D3's and D5's designers: §11, then the sections it points to. The
Refactorer and the Gate C reviewers: §6.2 B12 and §14 item 14 first. Everyone else who works on the code reads
everything; Appendix A is the signature reference, §9 every user-visible sentence, §10 the tests.

**What was verified for this design (2026-10-03, in a scratch environment outside every repository: Python 3.12,
deep_reasoner at `d7334ae` from D2's scratch install, `mcp` 1.28.1 from PyPI, the version the SDK fork locks):**

1. **Check can mirror `make_tools` exactly.** A one-tool config written as D2 materializes one (`main.yaml` with a
   `client` and `tools: {word_count: {factory, factory_from: tools/word_count.py}}`), loaded with
   `load_cli_config(…, schema=V2Config)`, then built step by step (`load_tool_factory`, the factory call, the `Func`
   check) and also by `make_tools` itself, on six fixtures: a working tool, a factory returning a plain function, a
   misspelled factory, an import of a missing module, a factory raising `KeyError`, a module reading an unset
   environment variable at import. Every outcome agreed. `load_tool_factory`'s messages are deep_reasoner's own and
   identical in both; an import failure is a `ValueError` whose `__cause__` is the original exception, a misspelled
   factory one with no cause; the non-`Func` sentence exists only inline in `make_tools` (`v2/cli.py:158–164`); an
   exception raised by the factory itself reaches `make_tools`' caller unwrapped and without the tool's name
   (`KeyError: 'GITHUB_TOKEN'`). The working tool's line, from deep_reasoner's own
   `func(name, value, description).describe()`, is ``- `word_count(text: str) -> int` `` followed by its
   description. A client whose `base_url` is `http://127.0.0.1:9/v1` builds without any key (`config.py:249–265`).
2. **`mcp` 1.28.1 starts a stdio server in a session of its own** (`client/stdio/__init__.py:256`,
   `start_new_session=True`), so D1's process-group kill of the worker does not reach it. A server that never answers
   and never reads its stdin outlived the client process that started it. Run through a 20-line guard that polls its
   parent's pid and kills its own process group when the parent is gone, both a working server and a silent one were
   gone within 1.5 s of the client process being `SIGKILL`ed (§4.6).
3. **One MCP connection on a loop thread of its own serves synchronous calls from any thread**, including a thread
   inside its own running loop, and before and after `nest_asyncio.apply()` (deep_reasoner applies it when an `llm`
   call is made inside a running loop, `llm.py:188–196`; it swaps asyncio's task and future classes for the whole
   process). Measured: a FastMCP stdio server answered `initialize` and `tools/list` in 1.2 s; a server exiting at
   start failed with `McpError: Connection closed`; three servers started at once were all decided by one shared
   deadline; a server that crashed mid-run failed the call in flight with `McpError: Connection closed` and the next
   call with an empty `ClosedResourceError`, while the connection's own task never noticed (§4.4); bad arguments
   came back as `isError` with the server's validation text; FastMCP wraps a primitive return as
   `{"result": value}` and advertises an `outputSchema` whose only property is `result`.
4. **A crashing server's stderr carried its own secret** (the fixture printed its token), so a failure's detail must
   be redacted before it reaches the run log (§4.5).

Not verified here: the agent-server forwarding Canvas's MCP settings to `dr-acp` end to end (`_mcp_config_to_acp_servers`
was read, not run; §10.6 proposes the cross-repo test), HTTP and SSE servers (read from the `mcp` source), macOS, and
CodeMirror's build size (§7.4 sets a budget). *(v2: the build runs HTTP and SSE against our own FastMCP server,
`test_shim.py::test_an_http_server_is_reached_with_its_headers[http, sse]`, and the chunk's size is measured, §6.2 B3;
the forwarding is still read, not run, and macOS is untested, §6.2 B17.)*

---

## 1 · What D4 is

deep_reasoner already supports tools of one's own: a tool block names a Python file and a factory in it
(`factory_from`, `tools/base.py:294–407`), and `make_tools` builds every block when a run starts
(`v2/cli.py:125–180`). D4 makes that usable from the app, and adds existing MCP servers beside it, as Michael chose
(Q6 (d)):

- **Your own tools.** The decompositions panel's **Tools** tab gets a tool editor: a name, the tool block (YAML), the
  Python source, an optional expression to try, a **Check** button, and the namespaces it is granted to. Check builds
  the tool exactly as a conversation would, in a throwaway process, and shows what the agent will be told, the tried
  value, or deep_reasoner's own error. Saving runs Check again on the server and refuses a tool that cannot build.
  The tool is a D2 tool row (the block plus the source); a conversation's run writes it to `tools/<name>.py` beside
  the materialized config, and an export carries it.
- **Existing MCP servers.** The same tab lists the servers configured in Canvas's MCP settings, each with namespace
  checkboxes. A grant is a D2 tool row too: its block names the server and snapshots its non-secret settings, and its
  source is D4's **shim**, a self-contained `factory_from` file whose factory binds the server's tools as one REPL
  object. In a conversation, `dr-acp` takes the servers OpenHands forwards at session start, its worker connects the
  granted ones when the run is built, and the shim hands each agent the connected server; under plain `dr`, on an
  export, the same shim connects by itself from the snapshot.

```text
Canvas window · Show Decompositions › Tools  (D3's frame; D4's tab)
   your tool:  editor ── POST ../tools/{name}/check ──▶ dr-library serve ── python -m …check_child (throwaway; 30/10/10 s)
               Save   ── PUT  ../tools/{name}       ──▶ Check again (code changed) ──▶ D2: tool row {block, source}, granted_in
   MCP server: Canvas's MCP settings (the page reads GET /api/settings; frame parameter `mcp`)
               a tick ── PUT  ../mcp/{name}         ──▶ D2: tool row {block: server snapshot, source: the shim}, granted_in

a conversation, first message (D1 §2 step 4)
   dr-acp front: LibraryCatalog.materialize → runs/<run>/config/{main.yaml, namespaces/, tools/<name>.py}
                 the forwarded mcpServers (session/new) that main.yaml's MCP blocks name → Start.mcp_servers
   worker:       load_dr_config → open_session: connect the granted, reachable servers at once (each within its own
                 connect timeout, 10 s by default; stdio through the guard) → mcp.status (run log; a notice for each
                 server not bound) → build_reasoner → make_tools
                 builds every block: your tool's factory; the shim's mcp_server() takes the connected server
   each agent:   binds the tools its namespace resolves (deep_reasoner): `word_count`, `github` (github.search_issues(…))
```

What a user does, end to end (spec §1's "done when"): they write a tool, check it, grant it to a namespace, and the
agent uses it; they connect an MCP server in Canvas's settings, grant it to a namespace, and the agent uses its tools.

### 1.1 Decisions this design takes

The spec's seven decisions in §2 stand, and so do D1's, D2's and D3's. These are the next layer down.

| # | Decision | Why | Rejected |
|---|---|---|---|
| A | **Check runs where saving happens: in the App backend (`dr-library serve`), as a throwaway child process of the same runtime Python, against a one-tool config materialized the way a run's is, built by a step-by-step mirror of `make_tools`' `factory_from` branch.** | Same deep_reasoner, same file layout, same resolution of `factory_from` against `config_path`, same messages (verified, header item 1). A child process survives nothing the tool does to itself, can be killed by group at a limit, and keeps the tool's prints out of the report. The mirror, not `make_tools` itself, so each failure is classified by the step that failed rather than by matching message text; a test pins that both agree on every fixture (§10.2). | Calling `make_tools` and parsing its exceptions (the factory's own exception and deep_reasoner's `ValueError`s are told apart only by text). Building in the backend's own process (a hanging factory hangs the API; an import is cached forever in `_FACTORY_MODULES`). Building in a conversation's worker (the panel cannot reach one). |
| B | **Check gives the tool no secrets and no model**: the backend's six environment variables plus `HOME`, `USER` and `LOGNAME`, a client pointed at a closed loopback port, the materialized config folder as working directory. **It is not a sandbox**: the tool runs as the user, with the disk and the network. | Check must never spend money or leak a key, and the backend has no keys to give (the agent-server starts it with six variables, D2 §4.8). A sandbox that a real run does not have would make Check pass what a run fails. | Running Check with the user's Canvas secrets (the backend cannot read them). A network or filesystem sandbox (`unshare` needs privileges on some Linux machines and does not exist on macOS; and it would diverge from a run). |
| C | **Saving through the panel runs Check whenever the code changes; a structural failure is refused, and a failure Check cannot attribute (an exception the tool raised, its time limit, Check itself not starting) can be saved anyway, explicitly.** | `make_tools` builds every tool block of a run's config (`v2/cli.py:149`), so one tool that does not build stops every conversation in every namespace from starting. That is E9's null in its worst form. A tool that reads a secret or a file when it is built fails in Check's environment and works in a conversation; refusing it outright would make a valid tool unsaveable. | Check as advice only (the spec's mock-up; a broken tool then surfaces at run time, for every conversation). Refusing every failure (traps tools that need the conversation's folder or a secret at build time). |
| D | **An MCP grant is a D2 tool row** (D2's option (a)): block `factory: mcp_server`, `factory_from: tools/<name>.py`, the server's name and non-secret settings; source the shim; granted through `granted_in`. | Grants become deep_reasoner's own namespace `tools` lists, so inheritance, the effective view, D3's Namespaces tab, versions, history, export and import all work with no change to D2's schema or to D1's Catalog; and an export runs under `dr` by construction, because the shim is the factory file. | A table of D4's own through `store.MIGRATIONS` (D2's option (b)): a new versioned kind (the `versions.kind` CHECK constraint is rebuilt with the table), its own materializer path so `dr` sees the grants at all, and its own inheritance rules beside deep_reasoner's. |
| E | **Canvas's MCP settings decide how a server is reached; the Library decides who gets it.** In `dr-acp`, a server is connected only from what OpenHands forwarded at session start, with its secrets; a granted server that was not forwarded (disabled in Canvas, or left out of the profile's `mcp_server_refs`) is not started, and the conversation says so. The row's snapshot is used only by plain `dr`. | OpenHands withholds a disabled server from an ACP agent on purpose ("withholding the entry is the only way to keep a disabled server out of its reach", `acp_agent.py:750–752`); falling back to the Library's snapshot would start it anyway. Secrets never enter the Library or an export. | Storing the server's whole definition, secrets included, in the Library (secrets in SQLite and in every export). Storing only the grant (an export could not reach the server under `dr`, which the spec requires). |
| F | **The worker connects the servers, all at once, before `build_reasoner`, each within its own connect timeout (10 s by default) from one shared start (v2: v1 had one deadline for all, §6.2 B5); the shim's factory, called by `make_tools`, takes what the worker connected.** | Each block's factory runs in turn inside `make_tools`, so connecting there would cost 10 s per silent server; connecting first costs the longest connect timeout at most, in all. The worker learns each server's outcome before the run starts, so the notice is in the run log ahead of the first answer. | Connecting in the shim's factory (sequential). Connecting in `dr-acp`'s front and proxying calls to the worker (a second transport between the two processes, and a shim that would differ under `dr`). |
| G | **A run connects every server granted to a namespace its agents can reach** (deep_reasoner's `check_spawn` from the conversation's namespace, transitively), and each agent binds a server's tools only when its own namespace resolves the grant; a server handed to a sub-agent in a namespace not granted it is refused. | deep_reasoner builds one tool registry per run and binds per agent (`namespaces.py:345–392`); a sub-agent spawned into a granted namespace must get the server even when the conversation began elsewhere, and only `__cross_namespace__` (`namespaces.py:645–654`, the seam `safe_url` uses) can stop an explicit hand-off. | Binding only the conversation's own namespace's grants (a sub-agent spawned into a granted namespace would lose a tool deep_reasoner gives it). Starting every granted server regardless of reach (a restricted `spawn` list would still start, and warn about, servers no agent can use). |
| H | **A server that is not bound leaves a stand-in under its REPL name**, which tells the agent why and raises that sentence if called. | deep_reasoner refuses an agent whose namespace names a tool the registry lacks (`namespaces.py:379–382`), so an unbound server cannot simply be missing; and a decomposition that calls it gets a sentence instead of a `NameError`. | Editing the run's config to drop the server (the run's namespaces are files deep_reasoner reads inside `build_reasoner`). |
| I | **Each stdio server runs under a guard**: the shim file run as a script (`--guard`), which starts the server in its own process group and ends that group when the process that started it is gone. | Verified need (header item 2): `mcp` puts the server in a session of its own, and a server that ignores its closed stdin outlives a worker that was killed. The guard imports only the standard library (about 30 ms) and works on Linux and macOS. | Relying on stdin EOF (fails exactly for the servers that hang). Recording pids for the front to kill later (a crashed server's pid can be reused). A stdio transport of our own (duplicates `mcp`'s). |
| J | **The shim is one self-contained module, `deep_reasoning/mcp/shim.py`, whose text is the row's source.** It imports only the standard library at module level; `mcp` and deep_reasoner's `Func` when used. In a `dr-acp` worker its factory returns what the worker installed (`SESSION`); anywhere else it connects by itself. | One code path for the app and for `dr`. A stored shim keeps working when deep-reasoning moves on, because in `dr-acp` it only reads `SESSION`, a dict of `Func`s, the one contract between versions. Without `mcp` installed a run still starts, with a stand-in that says to install it. | A thin shim importing deep-reasoning (an export would need deep-reasoning, not just `mcp`). |
| K | **What the panel shows of a server's tools is what the last conversation that connected it saw**, from a small cache `dr-acp` writes (`$DR_HOME/mcp/`). | The panel cannot connect a server: the backend has no access to its secrets. The spec's mock-up ("12 tools", "the agent is told: …") needs the list. | Connecting from the panel through the agent-server's `POST /api/mcp/test` (it returns tool names only, and needs the secrets sent back in). |
| L | **The tool source is edited in CodeMirror 6 (Python), in a field of D4's own (`PythonField`), loaded as a separate chunk only by the tool editor; every other field keeps D3's textareas, the decomposition cards' Python code included** (v2: v1's §7.4 routed it through D3's `CodeField`, §6.2 B1). | The spec costed a CodeMirror editor for Q6's answer; indentation and highlighting matter for Python in a way they do not for D3's YAML values. A separate chunk keeps D3's other tabs at their size (D3 §8.3 anticipated it). v2: the chunk is 348 KB, over §7.4's budget (§6.2 B3). | A textarea for Python (no indentation help). CodeMirror for every field (D3 decision C). |

### 1.2 What D4 owns, and its seams

- **Owns:** `src/deep_reasoning/tools/` (Check and the tool routes), `src/deep_reasoning/mcp/` (the shim, the wire
  models, the worker's session, the Library-side grant records), the Tools tab's frame code in `canvas-app/`
  (extending D3's `tabs/tools.tsx`), `tests/tools/`, `tests/mcp/`, D4's additions to `tests/canvas_app/test_tools_tab.py`.
- **Seam to D1** (§11.1): `Start.mcp_servers`; one RunEvent, `mcp.status`, its encoding and sentences; the
  capabilities flip; the seen cache written by the pump; about 90 lines in D1's files (v2: 101 lines added).
- **Seam to D2** (§11.2): tool rows, `granted_in`, `materialize`'s `tools/<name>.py`; the Check gate in `PUT /tools/{name}`;
  D4's routes appended to `create_app`; no schema change.
- **Seam to D3** (§11.3): exactly §8.3 of D3: `tabs/tools.tsx`, `api.ts`'s `checkTool` and two MCP calls, the shared
  components, one frame parameter, the editor chunk; v2: one optional prop on D3's `ConfirmRow` (§6.2 B8).
- **Seam to D5** (§11.4): E10 re-run with MCP servers bound; one exception in §2.1's table; the profile's
  `mcp_server_refs: null`; a proposed E12 step. None of it is built in D4 (§6.2 B17).

---

## 2 · The Tools tab, as the user meets it

D3's banner stays at the top of the tab, permanently (D3 §2.5, D5 §2.3). D4 adds its own sentence under it, then the
two lists.

```text
┌ Decompositions │ Create decomposition │ Namespaces │ Tools │ ⋯ ──────────────────────────────── (Canvas's row) ┐
│ ⚠ deep_reasoner runs as you. It can read and change any file you can, … stops at $5 per conversation.         │
│ ⚠ Tools and MCP servers run as you, with your files and network: your tools inside the agent's process, a    │
│   stdio MCP server as a program started for each conversation that can use it. Check runs your code too.     │
│   Add only code and servers you trust.                                                                       │
│ Your tools                                                                               [+ New tool]        │
│   word_count   v1   factory make · tools/word_count.py          granted in course_advisor                    │
│   rag          v2   factory rag                                 granted in root                              │
│ MCP servers (from Canvas's settings)                                                                         │
│   github    stdio  npx -y @modelcontextprotocol/server-github   as github     ☑ router  ☐ course_advisor  …  │
│             12 tools, as the conversation of 3 Oct, 14:02 saw them ▸                                         │
│   postgres  http   https://db.lab.example/mcp                   as postgres   ☐ router  ☑ course_advisor  …  │
│             Its tools are listed here after the first conversation that starts it.                          │
│   slack     stdio  Disabled in Canvas's MCP settings: not started until you enable it there.                 │
│   old-wiki         Granted, but no longer in Canvas's MCP settings.                                [Remove]  │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Your tools

**The list** is `GET /tools` minus the MCP grants (`GET /mcp` names them): name, version, `factory <factory> · <file>`
for a tool with a source and `factory <factory>` for one without (v2: D3's row text, kept; v1 said `<factory> · <file>`
and `built-in <factory>`, §6.2 B8), and the namespaces that grant it directly. With none:
D3's `NO_TOOLS`. A row opens the editor; **+ New tool** opens it empty.

**The editor** (the spec's mock-up, as built):

```text
Tools › word_count                                                                         v1 · saved 3 Oct
Name     word_count                        how the agent calls it: a Python name, fixed once saved
Block    factory: make                     YAML: the factory's name and its parameters (factory_from is the Library's)
Source   1  from deep_reasoner import Func
         2
         3
         4  def make(client, params):
         5      def word_count(text: str) -> int:
         6          """Count the words in text."""
         7          return len(text.split())
         8
         9      return Func(word_count, description="word_count(text) -> int: number of words in text.")
Try      word_count("one two three")       optional: an expression Check evaluates with the tool bound
[Check]  ✓ builds (0.02 s). The agent is told:
           - `word_count(text: str) -> int`
             word_count(text) -> int: number of words in text.
         word_count("one two three") → 3
Granted in   ☑ course_advisor   ☐ router   ☐ health_advisor   ☑ root.archive (inherited from root)
How tools work ▸
[Save]   [Delete]
```

*(v3: the header is `Tools › word_count v1`, with no save date; §6.2 B23.)*

- **New tool** starts with the name empty, `factory: make` and the template above (`NEW_TOOL_SOURCE`, §9.3). The
  name is required, must be a Python identifier, not a keyword and not one of deep_reasoner's own REPL names
  (`RESERVED_NAMES`, §3.2), and cannot change after the first save (D2 §4.5: a new name is a new tool). v2: the
  backend enforces the rules (Check's `invalid`, D2's `409` for a name taken); the editor sends the name as typed and
  shows the sentence that comes back (§6.2 B8).
- **A built-in tool** (a block without `factory_from`: `rag`, `kg`, `llm` aliases, `safe_url`, `claude_code`) shows
  the block only; Check says whether the factory is one of deep_reasoner's (§3.3).
- **Check** sends `POST /tools/{name}/check {yaml, source, example}` with what is on screen (saved or not) and shows
  the report (§3.4): a ✓ with the time and what the agent is told, the tried value or its error, and, on a failure,
  deep_reasoner's sentence, the frames from the tool's own file, and the last 2,000 characters the tool printed.
  While it runs, `CHECKING` shows under the button (`dr-check-status`, v2).
- **Save** sends `PUT /tools/{name} {yaml, source, granted_in, base_version}`. The backend runs Check when the block
  or the source differs from the head (§3.5): "Checking and saving…". On `422 check_failed` the report is shown;
  when it allows it, **Save anyway** resends with `accept_check_failure: true` under `SAVE_ANYWAY_NOTE`. A `409`
  and a `422 invalid` are D3's (§5.2 there). Success: `SAVED_TOOL`. *(v5, §6.2 B29: a `422 invalid` shows D2's
  message in `dr-errors`, one line per field error with its field; no field is marked, as D3 marks its cards. A `409
  conflict` on a saved tool offers D3's **Reload** and **Save over**.)*
- **Granted in** is D3's `NamespaceChecklist`: checked = the record's `granted_in`; a namespace that inherits the grant
  from an ancestor (from `GET /effective`'s `tools[].source`) is checked and fixed with "inherited from X". For a saved
  tool, a tick saves at once (D3 decision I): `PUT /tools/{name}` with the **head's** block and source, the new
  `granted_in` and the head's version, so a grant never carries unsaved, unchecked code and needs no Check. For a new
  tool, the ticks go with the first Save.
- **Delete** asks inline (`DELETE_TOOL_CONFIRM`), then `DELETE /tools/{name}?base_version=`; D2 removes it from every
  namespace's `tools`.
- **How tools work** folds open `TOOL_HELP` (§9.3): the factory contract, one file only (D2 §9 item 7), models through
  `client`, secrets read when called rather than built, `config_path` not passed (the spec's known gap B8), and the
  `kg` layer note (D2 §9 item 10).
- **The source field** is CodeMirror, in D4's `PythonField` (§7.4). It takes the draft's text when it mounts and
  owns it from then on; whatever replaces the draft (a save, **Discard draft**, **Reload**) mounts a new one (v2,
  §6.2 B2). If the editor chunk cannot load, it is D3's textarea.
- **The draft** (every field) is kept under `dr-library.draft.tool.<name>` (`.new` for a new one) with D3's
  `drafts.ts`, cleared by a save or **Discard draft**; a refetch never overwrites it (D3 §2.6).

**Failure cells**, deep_reasoner's own sentences where it has one (verified, header item 1):

```text
factory make_broken → ✗ tool 'word_count': make_broken in tools/word_count.py returned function, not a Func. A tool
                        factory returns Func(value, description=…) — the registry reads its `.value` (what the REPL
                        binds) and `.description` (what the agent is told).
                      Fix this before saving: a tool that does not build stops every conversation from starting.
factory mkae        → ✗ tool 'word_count': 'tools/word_count.py' defines no 'mkae'.
                        It defines: make, make_broken.
                        Known built-in factories: claude_code, kg, llm, rag, safe_url.
import yaml_x       → ✗ tool 'word_count': importing 'tools/word_count.py' raised ModuleNotFoundError: No module
                        named 'yaml_x'
a hanging factory   → ✗ tool 'word_count': building it took longer than 10 s, so Check stopped it. A tool is built
                        at the start of every conversation; a factory must return quickly.          [Save anyway]
os.environ['TOKEN'] → ✗ tool 'word_count': make raised KeyError: 'TOKEN'
                        File "tools/word_count.py", line 5, in make
                      Check could not build this tool here, where it has no secrets, no model and only its own
                      folder. If it builds in a conversation, save it anyway; if it does not, no conversation will
                      start until you fix it.                                                        [Save anyway]
def make(           → ✗ tool 'word_count': tools/word_count.py line 1: '(' was never closed    (no process started)
```

### 2.2 MCP servers

The list joins Canvas's MCP settings (frame parameter `mcp`, §7.5) with the Library's grants (`GET /mcp`), one row
per server name:

| The server | The row |
|---|---|
| in Canvas's settings, given to the agent, not granted | its transport and target (command and arguments, or URL), "as `<name>`" (an editable REPL name, prefilled with `defaultToolName`, §8.5), and a namespace checklist all unticked |
| granted | the same with its grants ticked (D3's `NamespaceChecklist`, inherited grants fixed); below it, the last seen tools (`MCP_SEEN`, folding open to exactly what the agent was told) or `MCP_NOT_SEEN` |
| granted, and Canvas's settings differ from the snapshot in what the grant's block keeps (v6, §6.2 B35): the transport; for stdio the command, arguments or environment names; for HTTP or SSE the URL or header names | `MCP_CHANGED` with **Update** |
| granted with a shim older than this deep-reasoning's | `MCP_SHIM_OLD` with **Update** |
| disabled in Canvas's settings | `MCP_DISABLED`; its checklist still works (a grant waits for the server to be enabled) |
| left out by the `deep_reasoner` profile's `mcp_server_refs` | `MCP_NOT_IN_PROFILE`; the same |
| granted, not in Canvas's settings any more | `MCP_GONE` with **Remove** |
| Canvas's settings could not be read (`mcp` is null) | the grants only, under `MCP_SETTINGS_UNKNOWN`, each drawn from its stored snapshot (state `given`, v2, §6.2 B8); no new grant can be made |

- **A first tick** sends `PUT /mcp/{name}` with the server's name, transport, command, arguments, URL, environment
  variable names and header names (never a value; the page never reads one, §7.5), `granted_in: [that namespace]`,
  `base_version: 0`. The backend writes the block and the shim (§4.2). `409`: the REPL name is taken by another tool
  ("a tool named 'github' exists: choose another name") or the server is already granted under another name. *(v3:
  both are `409 refused`, the first with `mcp_name_taken`, at any `base_version`, so no write through `PUT /mcp`
  replaces a tool of your own, nor one through `PUT /tools` a grant; §6.2 B20.)*
- **Later ticks** resend the **stored** snapshot with the new `granted_in` and the grant's version (no new tool
  version, D2 §4.5's "unchanged is not a save"). **Update** resends Canvas's current settings (or regenerates an old
  shim): a new version. Unticking every namespace keeps the row with no grants; **Remove** deletes it
  (`DELETE /tools/{name}?base_version=`). *(v6: a first tick sends every name the frame has, but a stdio block keeps
  no header names and a remote block no arguments or environment names (§4.2), so a stdio server's headers, its
  `auth`'s included (B30), are never stored, and never make its row changed (B35). That a later tick keeps the
  stored snapshot when Canvas's has changed is pinned since `6739e0f`, B33.)*
- `MCP_EXPORT_NOTE` sits under the list: an export keeps each server's command, arguments and URL, never an
  environment or header value.

**In the conversation.** A granted server that a conversation's run could not bind is said once, ahead of the first
answer, as a root `agent_message_chunk` (the same form as D1's fresh-run notice), and is in the run log, so it replays:

```text
⚠ MCP server 'postgres' did not answer within 10 s; its tools are not bound in this conversation.
⚠ MCP server 'slack' is granted to router in the Library, but this conversation was not given it: enable it in
  Canvas's MCP settings. Its tools are not bound.
⚠ MCP server 'wiki' could not be started (McpError: Connection closed; it printed: "invalid token [redacted]");
  its tools are not bound in this conversation.
```

**What the agent is told** (deep_reasoner renders the binding, `v2/messages.py:216–224`, from the signature of the
unannotated `Server.__call__`, §6.2 B4; the rest is the shim's description, §8.4):

```text
- `github(tool, /, **arguments)`
  MCP server 'github' (stdio): call a tool as github.<tool>(…) or github("<tool name>", **arguments); a failed call
  raises McpToolError.
  github.search_issues(query: str, repo: str, page: int = …) -> dict
    Search issues in a repository.
  github.get_file_contents(owner: str, repo: str, path: str) -> str
    Get the contents of a file or directory.
```

---

## 3 · Check

### 3.1 What it answers

"Will this tool build when a conversation starts, and what will the agent be told?" Check answers it by doing what
a run does, in a process of its own, minus what only a conversation has: the user's secrets, a model, the
conversation's folder. It answers in about two seconds for a tool that builds (most of it deep_reasoner's import,
1.4–3 s measured) and within its limits for one that does not.

### 3.2 Before any process: the static stage

In the backend, in this order, each failure ending Check:

1. **Shape**: D2's `shapes.validate_tool(name, yaml, source)` (the block is a mapping, `factory_from` absent or
   `tools/<name>.py`, a name that is an identifier). Failure → outcome `invalid`, D2's message and field errors.
   *(v5, §6.2 B29: the report carries D2's message, whose lines are the field errors; `CheckReport` has no list of
   them.)*
2. **Name**: not in `RESERVED_NAMES` = `subagent`, `run_all`, `FinalAnswer`, `Var`, `Func`, `task`. A namespace's
   tools are bound over the agent's framework tools by name (`v2/agent.py:647, 675`), so a tool called `run_all`
   would replace deep_reasoner's own. `llm` is not reserved: deep_reasoner lets a user's own factory be called `llm`
   (`v2/cli.py:154–155`). Failure → `invalid`, `RESERVED_NAME`.
3. **An MCP grant's block** (`factory: mcp_server`): refused here, outcome `invalid` with `MCP_VIA_GRANT`; grants
   are written by `PUT /mcp/{name}` (§4.2).
4. **A block without a source**: its factory (default: the tool's name) is `llm` or a key of deep_reasoner's
   `TOOL_BUILDERS` → `builtin` (✓; not built, because a built-in needs the model and the data a conversation has);
   otherwise `bad_factory` with `make_tools`' own sentence (`v2/cli.py:171–176`), copied into `texts.py` and pinned by
   a test. No process starts.
5. **Syntax**: `compile(source, f"tools/{name}.py", "exec")`. A `SyntaxError` → `syntax`, with its line. No process
   starts.

### 3.3 The throwaway process

```text
tmp = TemporaryDirectory(prefix="dr-check-", ignore_cleanup_errors=True)    (v6, B32: 0700, under the backend's TMPDIR)
tmp/config/main.yaml       {client: {base_url: "http://127.0.0.1:9/v1", max_retries: 0},
                            tools: {<name>: <the canonical block, factory_from: tools/<name>.py>}}
tmp/config/tools/<name>.py the source, byte for byte
tmp/printed.txt            the child's stdout and stderr, both
Popen([sys.executable, "-m", "deep_reasoning.tools.check_child", "--report-fd", W, "--name", <name>,
       ("--example", <expression>)?, "tmp/config/main.yaml"],
      cwd=tmp/config, env=check_env(os.environ), stdin=DEVNULL, stdout=stderr=printed.txt,
      pass_fds=(W,), start_new_session=True)
```

- **Python** is `sys.executable` of `dr-library serve`, which under D5 is the runtime's (`runtime/current`, D5
  decision C), the same interpreter and deep_reasoner as every `dr-acp` worker.
- **Environment** (`check_env`): `PATH`, `LANG`, `LC_ALL`, `LC_CTYPE`, `TMPDIR`, `TZ` as the backend has them (the six
  the agent-server gives an App backend); `HOME`, `USER`, `LOGNAME` from the password database (code that reads
  `os.environ["HOME"]` works); `PYTHONUNBUFFERED=1`, `PYTHONDONTWRITEBYTECODE=1`. No key, no Canvas secret, no
  `DR_HOME`.
- **The model**: the config's client points at port 9 on loopback with no retries, so `build_client` needs no key
  (`config.py:256–262`) and any model call fails at once with a connection error. Check never reaches a model.
- **Working directory**: the materialized config folder, so deep_reasoner's messages name `tools/<name>.py` as the
  spec's mock-up does, and anything the tool writes is removed with the folder.
- **Its own process group**, so a limit or the end of Check kills whatever the tool started.

**The child** (`check_child.py`) reports JSON lines on the report fd, never on stdout, which the tool may print to:

```text
import deep_reasoner's config loader, V2Config, load_tool_factory, Func, func       → {"phase": "ready"}
cfg = load_cli_config(main, schema=V2Config); block = cfg.tools[name]; started = monotonic()
params = block minus factory and factory_from          (as make_tools passes them: no config_path, the spec's B8)
factory = load_tool_factory(name, block["factory"], block["factory_from"], cfg.config_path)
   ValueError with an ImportError cause      → {"phase": "failed", "outcome": "import_failed", "message": str(exc)}
   ValueError with any other cause           → "raised"       (the module raised while importing)
   ValueError without a cause                → "bad_factory"  (defines no …, or not a function)
built = factory(build_client(cfg.client), params)
   any exception                             → "raised", FACTORY_RAISED, the traceback's frames in tools/<name>.py
   not isinstance(built, Func)               → "not_func", make_tools' sentence (NOT_FUNC, copied and pinned)
→ {"phase": "built", "told": func(name, built.value, built.description).describe(), "seconds": …}
only with --example: eval(compile(expression, "<try>", "eval"), {name: built.value})
→ {"phase": "example", "ok", "value": repr(result)[:2000] | null, "error": "Type: message" | null, "seconds"}
exit 0
```

*(v6, §6.2 B32: v1–v5 had the child also report `loaded` after the import and `done` before it exits; the
supervisor awaited neither, and `e5583e6` removed both. A `failed` line ends the child at once; `seconds` counts from
before the file is loaded, as §3.4 says.)*

**The supervisor** (`check.py`) reads the report fd with deadlines and kills the group at the first one missed;
awaiting a phase, it skips a line of any other (v6: pinned, B32):

| Phase awaited | Limit (`CheckLimits`) | Missed → outcome |
|---|---|---|
| `ready` after start | `ready_s` = 30 s (deep_reasoner's import on a cold disk) | `unavailable`, `READY_TIMEOUT` |
| `built` or `failed` after `ready` | `build_s` = 10 s (importing the tool's file and calling its factory) | `timeout`, `BUILD_TIMEOUT` |
| `example` after `built` | `example_s` = 10 s | the example's error: `EXAMPLE_TIMEOUT`; the build stays ✓ |

The child exiting without a final line is `unavailable` (before `ready`) or `raised` (after it), with how it ended
(`CHILD_ENDED`: its exit code or signal). v2 (§6.2 B7): a child that ends while evaluating the tried expression
leaves the build ✓ and gives the example `CHILD_ENDED` with phase `trying it`; a child that cannot be started at all
(`Popen` raises `OSError`) is `unavailable`, `CHILD_ENDED` naming the error, phase `starting`. After the last
line, or a missed limit, the supervisor sends `SIGKILL` to the group **before** reaping the child (an unreaped child
keeps its pid, so the group id cannot have been reused), then waits, then removes `tmp` (v6: as the `with` ends, on
every path). So Check answers within the limit it reports, plus well under a second, and leaves no process behind
(§10.2).

### 3.4 What it reports

`CheckReport` (Appendix A.1): `ok`; `outcome`; `message` (deep_reasoner's sentence where it has one, else §9.1's);
`told` (deep_reasoner's own rendering, verbatim); `traceback` (for `raised`: the frames in the tool's own file and
the exception line, at most 2,000 characters); `example`; `printed` (the last 2,000 characters of what the tool
printed); `seconds` (load and build); `deep_reasoner` (the build that checked it, D2's `deep_reasoner_build()`);
`can_save`; `can_save_anyway`.

| Outcome | `ok` | Save | Why |
|---|---|---|---|
| `built`, `builtin` | yes | yes | |
| `invalid`, `syntax`, `import_failed`, `bad_factory`, `not_func` | no | no | the same runtime would fail the same way in every conversation |
| `raised`, `timeout`, `unavailable` | no | anyway, explicitly | the tool may need what only a conversation has (a secret, its folder, a slow network), or Check itself did not start |

`POST /tools/{name}/check` always answers 200 with the report (as D2's `/validate` does); the bridge sets no read
timeout on App-backend requests (`bridge.py:467–472`, `proxy.py:96–97`), so a 50 s worst case passes through.

### 3.5 The gate on saving

D2's `PUT /tools/{name}` endpoint calls `require_check(lib, name, yaml, source, accept_failure=…)` before
`lib.put_tool`:

```text
the YAML does not validate                     → nothing here: lib.put_tool raises D2's 422 invalid as before
an MCP grant's block                           → 400 MCP_VIA_GRANT
the head is an MCP grant                       → 409 refused MCP_VIA_GRANT, at any base_version  (v3, §6.2 B20)
canonical block and source equal the head's    → nothing to check (a grant-only change; D2 then writes namespaces only)
otherwise: report = check_tool(name, yaml, source)          (no example)
   report.can_save                                           → save
   report.can_save_anyway and accept_check_failure is true   → save
   else                                                      → 422 {"error": "check_failed", "message": CHECK_FAILED,
                                                                    "check": report}
```

Only the HTTP API is gated: `Library.put_tool` (Python) and `dr-library import` are not, so an imported tool can be
broken; the editor's Check finds it, and §14 item 4 proposes a check after upgrades.

---

## 4 · MCP servers

### 4.1 From Canvas's settings to `dr-acp`

OpenHands holds MCP servers in its settings (`agent_settings.mcp_config`, a map from name to `MCPServer`,
`mcp/config.py:497–533`), filtered for a conversation by the agent profile's `mcp_server_refs` (`null`: all;
`profiles/resolver.py:160–168`). At ACP session start the bridge turns every enabled one into an ACP `mcpServers`
entry (`_mcp_config_to_acp_servers`, `acp_agent.py:739–821`, called at `:3114` for `session/new` and again for
`session/load`): stdio always, with its environment as `[{name, value}]` in plain text; HTTP and SSE only when the
agent advertises `mcpCapabilities.http` / `.sse`, with headers in plain text. **D4 flips both flags to true** in
`dr-acp`'s `initialize` (D1 §4.8 left them false).

`dr-acp` already keeps the forwarded list on the session (`Session.mcp_servers`, D1 §4.8; refreshed on `session/load`).
At a run's start (the first message, or the first after a fresh-run reset) the front:

1. materializes the run (D1, unchanged);
2. reads the run's `main.yaml` (plain YAML, no deep_reasoner import) for MCP blocks and the server names they carry
   (`servers_named`);
3. converts the forwarded entries it names into `McpServerSpec`s (`forwarded_specs`: stdio has no `type` key in ACP
   0.12.1, HTTP `"http"`, SSE `"sse"`; anything else is ignored) and puts them in `Start.mcp_servers`, over the
   control pipe, never in the worker's environment. Steps 2 and 3 are one function, `specs_for_run(forwarded,
   config_path)`.

Servers that no Library grant names are never sent to the worker: their secrets stay in the front.

### 4.2 A grant in the Library

`PUT /mcp/{name}` (`name`: the REPL name, an identifier; D4's route, §7.2) writes one D2 tool row:

```yaml
# block (canonical YAML; D2 adds factory_from)          # http or sse instead of stdio:
factory: mcp_server                                     # transport: http
factory_from: tools/github.py                           # url: https://db.lab.example/mcp
name: github                                            # headers:
server: github                                          #   Authorization: POSTGRES_AUTHORIZATION
transport: stdio
command: npx
args:
- -y
- '@modelcontextprotocol/server-github'
env:
- GITHUB_PERSONAL_ACCESS_TOKEN
```

- `name` repeats the row's key because `make_tools` does not pass a factory its alias (`v2/cli.py:152`), and the shim
  must know the name it is bound under. `server` is the key in Canvas's settings. `env` lists names only; `headers`
  maps each header to the environment variable `dr` will read it from (`header_env_name`, §8.5). Optional
  `connect_timeout_s` (default 10) and `call_timeout_s` (default 120) are honoured if present; the panel never writes
  them, tests do. *(v6: as built from the first build on, and not said here before: a stdio block keeps
  `command`, `args` and `env` and no `headers`; an HTTP or SSE block keeps `url` and `headers` and no `args` or `env`
  (`mcp_block`, `grants.py:73–80`). The body may carry all of them; what the block does not keep is dropped. The
  bridge forwards neither headers nor `auth` to a stdio server, so nothing is lost; §8.6 compares only what a block
  keeps, §6.2 B35.)*
- `source` is `shim_source()`: the text of `deep_reasoning/mcp/shim.py` in the installed package. Its first line is the
  marker `# deep-reasoning MCP shim, version 1. …`; a row is an MCP grant when its block's factory is `mcp_server`
  and its source starts with the marker (`is_mcp_tool`), which also holds for an export re-imported.
- Refused: a server already granted under another name (`409 refused`, `MCP_SERVER_TAKEN`); stdio without a command,
  HTTP or SSE without a URL (`400`); the name rules of §3.2 (`422 invalid`). v3 (§6.2 B20, B21): a name held by a
  tool of your own (`409 refused`, `MCP_NAME_TAKEN`, at any `base_version`); a body that is not an `McpGrantBody`
  (`400`, `MCP_BAD_REQUEST` and pydantic's reason). The checks run in that order: the body, the name rules, a tool
  of your own, a server granted elsewhere, then the snapshot's command or URL.
- `GET /mcp` lists every grant as an `McpGrant` (Appendix A.2): the snapshot, `granted_in`, `version`,
  `shim_current` (the source equals today's shim) and `seen` (§4.7).

### 4.3 The shim

`deep_reasoning/mcp/shim.py` is the factory file of every grant, self-contained (decision J). Its module level imports
only the standard library; `mcp` and `deep_reasoner.primitives.Func` are imported where used.

**The factory**, `mcp_server(client, params) -> Func`:

```text
SESSION = the package module's SESSION, if `from deep_reasoning.mcp import shim` succeeds, else None
SESSION is not None (a dr-acp worker installed it)
    → SESSION.get(params["name"]) or a stand-in (NOT_IN_SESSION)            no connection is made here
SESSION is None (plain dr, an export, or deep-reasoning not installed)
    spec, missing = spec_from_block(params, os.environ)     env and header values from the environment
    import mcp fails                                         → a stand-in (NO_MCP_PACKAGE)
    connection = Connection(spec, name=params["name"], errlog=sys.stderr, call_timeout_s=…); start;
    wait_ready(connect_timeout_s)
    ready                                                    → Func(Server(name, connection, granted=None), describe(…))
    otherwise                                                → a stand-in (NO_ANSWER / COULD_NOT_START, naming missing
                                                               variables); a structlog warning mcp.unavailable
```

**`Connection`**: one server, on a daemon thread running its own event loop (verified, header item 3):

```text
_serve():  async with transport(spec) as streams:              stdio: stdio_client(StdioServerParameters(
                                                                  command=sys.executable,
                                                                  args=["-I", this file, "--guard", "--", command, *args],
                                                                  env=spec.env), errlog=…)
                                                               http:  streamable_http_client(url, http_client=
                                                                  httpx.AsyncClient(headers=spec.headers, …))
                                                               sse:   sse_client(url, headers=spec.headers)
               async with ClientSession(read, write) as session:
                   await session.initialize()
                   tools = every page of session.list_tools()
                   ready (threading.Event)
                   await stop (asyncio.Event)
           any exception → failure = the innermost exception, "Type: message"; ready
call(tool, arguments): run_coroutine_threadsafe(session.call_tool(tool, arguments,
                           read_timeout_seconds=call_timeout_s), loop).result(call_timeout_s + 5)
    McpError -32000 (connection closed), anyio's ClosedResourceError, BrokenResourceError, EndOfStream
                                                    → marked dead; SERVER_STOPPED, now and for every later call (v2)
    McpError 408 (mcp's own read timeout), or no result by call_timeout_s + 5 → CALL_TIMEOUT
    McpError of any other code                      → CALL_FAILED with its message, no type (v5, B28)
    anything else                                   → CALL_FAILED with the innermost exception
abandon(): loop.call_soon_threadsafe(task.cancel)   (mcp then closes stdin and ends the guard's group)
```

A stdio server's environment is what Canvas's settings give it plus the six variables `mcp` adds itself (`HOME`,
`LOGNAME`, `PATH`, `SHELL`, `TERM`, `USER`, `client/stdio/__init__.py:28–66`); it never inherits the worker's. Its
working directory is the worker's: the conversation's folder (ACP carries no `cwd` for a stdio server).

**What the REPL binds** (`Server`): a callable object named after the grant (`__name__ = name`), so deep_reasoner
renders it as `` `github(tool, /, **arguments)` ``. Its `__call__` carries no annotations, since deep_reasoner renders
annotations too (v2, §6.2 B4). Each MCP tool whose name, with every character that cannot be in a
Python name replaced by `_`, is an identifier, not a keyword and not already taken is also an attribute (an `McpTool`),
so `github.search_issues(…)` works; every tool is callable by its exact name, `github("get-file", path="x")`.
`McpTool(*args, **kwargs)` maps positional arguments onto the parameters in the order `describe` prints them; a
surplus positional argument is a `TypeError`. The return value (§8.3) is the unwrapped result, a dict, text, or the
content blocks; a failed call raises `McpToolError`. `Server`, `McpTool` and the stand-in return themselves from
`__copy__` and `__deepcopy__`, because deep_reasoner's `fork` deep-copies the REPL (`repls/backends.py:105–140`) and a connection is
shared, not copied. They implement `__cross_namespace__(src, dst)`: with a grant set (in `dr-acp`), a hand-off into a
namespace outside it raises `PermissionError` (`HANDOFF_REFUSED`, the same kind of refusal `safe_url` makes,
`tools/safe_url.py:86–96`); the first bind (`src is None`) always passes, because deep_reasoner binds a tool only in a
namespace that resolves it.

**The stand-in** (`Unavailable`): calling it, or any attribute of it whose name does not start with `_`, raises
`McpToolError` with its reason; its description is `UNAVAILABLE` (the same reason), so the agent is told before it
tries. An attribute starting with `_` is an `AttributeError`, as on any plain object, because Python's and
deep_reasoner's own lookups probe such names (`inspect.signature` reads `_partialmethod`, deep_reasoner
`__cross_namespace__`); its `__call__(*args, **kwargs)` is unannotated like `Server`'s (v2, §6.2 B4).

### 4.4 Session start, in the worker

`Worker.build` (D1 §4.3 step 3), after `load_dr_config` and the namespace and client overrides, before
`build_reasoner`, calls `open_session(cfg, start.mcp_servers, run_dir=run_dir)` (`deep_reasoning/mcp/session.py`):

```text
blocks    = {alias: block for alias, block in cfg.tools.items() if block.get("factory") == "mcp_server"}
none      → shim.SESSION = {}; return []
registry  = build_namespace_registry(cfg)
names     = root, every namespace of namespaces_dir (load_namespaces_from_dir) and of cfg.namespaces
granted   = {alias: {ns in names: alias in registry.resolve(ns).tools}}          deep_reasoner's own resolution
reach     = the closure of {cfg.entry_namespace} under check_spawn(registry, src, dst) succeeding
registry.close()
for each alias (all started at once):
    no namespace grants it                → skipped   "granted to no namespace"           (no notice)
    granted ∩ reach is empty              → skipped   "granted only where this conversation cannot spawn"
    no forwarded spec for block["server"] → not_enabled                                  (a notice)
    else Connection(spec, name=alias, errlog=a pipe, call_timeout_s=…).start()
         a thread copies the pipe into runs/<run>/mcp-<alias>.log through redact(env and header values),
         holding back each read's last (longest secret − 1) characters for the next          (v3, §6.2 B18)
    an exception here (the log cannot open, the block cannot be read) → failed, "Type: message" redacted
                                                                                           (v3, §6.2 B19)
begun = the moment before the first start
wait each started one in turn, until begun + its own connect_timeout_s (default 10 s)           (v2, §6.2 B5)
    ready, no failure → bound        told = deep_reasoner's func(alias, server, description).describe(); count;
                                     seconds = from begun until its wait returned
    ready, failure    → failed       detail = failure + the log's last 300 characters, every secret value of that
                                     server's spec (env and header values of 4+ characters) replaced by [redacted]
                                     (v3: the pipe is closed, and the copy given DRAIN_S = 2 s, before the tail is read)
    not ready         → no_answer    seconds = its connect_timeout_s; connection.abandon()
    deciding raises (its binding cannot be described)  → abandon(); failed, "Type: message" redacted   (v3, B19)
shim.SESSION = {alias: Func(Server(…, granted=frozenset(granted[alias]))) | a stand-in, for every block}
return a McpServerStatus per block
```

*(v4, §6.2 B24: the copying thread is also what keeps a talkative server answering. A server whose stderr fills a
pipe nobody reads (64 KB) blocks on its next write and stops answering; a test pins that a server printing 1 MB at
start and 256 KB on each call is bound, answers, and leaves a log with its token redacted on every line.)*

The worker emits `mcp.status {servers: [...]}` (a new RunEvent, §7.3) through its recorder, up the event pipe like
every worker event, when there is any MCP block, then builds (D1's view of it: §11.1).
`make_tools` then calls each MCP block's factory, which returns `SESSION[alias]` without connecting (§4.3).

**Timing.** `session/new` never waits on a server (D1 builds nothing there). The first answer waits at most the
longest connect timeout (10 s by default) on a silent server, and about one server start (1.2 s for a Python FastMCP server, header item 3) when
all answer, overlapped with nothing else the worker does: deep_reasoner's import has already happened (`load_dr_config`).
The front's heartbeat (D1 §4.2) keeps the bridge's idle watchdog quiet meanwhile.

### 4.5 When a server fails

| When | What happens | What the user sees |
|---|---|---|
| it is not forwarded | not started; stand-in bound | `MCP_NOT_ENABLED` once, before the first answer |
| it exits or errors before answering | `failed`, with its stderr's tail, redacted; stand-in bound | `MCP_FAILED` |
| `open_session` cannot start or bind it: its log cannot be opened, its block cannot be read (a `connect_timeout_s` that is not a number), its tools cannot be described (v3, §6.2 B19) | that server alone is `failed`, its detail the error's `"Type: message"`, redacted; a connection already started is abandoned; stand-in bound; the other servers bind and the run goes on | `MCP_FAILED` |
| it does not answer within its connect timeout | `no_answer`; abandoned (stdin closed, its guard's group ended by `mcp`); stand-in bound | `MCP_NO_ANSWER`, the spec's sentence |
| a call returns `isError` | `McpToolError("{name}.{tool} failed: {text}")` in the cell | the cell's output |
| a call does not answer within `call_timeout_s` (120 s), or `mcp` gives up reading first (`McpError` 408) | `McpToolError(CALL_TIMEOUT)`; the request is abandoned; the server stays | the cell's output |
| it dies during the run | the call in flight meets `McpError: Connection closed` (verified); the connection is marked dead with that reason, and that call and every later one raise `SERVER_STOPPED` (`MCP server 'echo' stopped (McpError: Connection closed); …`), later ones at once (v2: v1 let the call in flight raise the bare `McpError`, §6.2 B6); nothing restarts it before the next run | the cell's output |

None of these reaches the worker's main thread except as an exception in the calling cell, and a server is another
process, so a server cannot take the worker down (E9). Because a dead connection's own task does not notice (header
item 3), `Connection.call` marks it dead on `McpError` code -32000 ("Connection closed") and on
`anyio.ClosedResourceError`, `BrokenResourceError` and `EndOfStream`.

### 4.6 How a server ends

- **The run ends normally** (Close, a failed prompt): the worker exits (D1 §4.3 step 5); each stdio server's stdin
  closes with it, a well-behaved server exits, and its guard follows.
- **The worker is killed** (root Stop, D1's 0.8 s grace then `SIGKILL` to its group; the front dying, after which the
  worker kills its own group): the servers are not in that group (`mcp` puts each in a session of its own), so each
  guard sees its parent's pid change within 0.5 s and sends `SIGKILL` to its own group (verified, header item 2).
- **A server given up at start**: `abandon()` cancels its task; `mcp` closes its stdin, waits 2 s and ends its process
  tree (`client/stdio/__init__.py:180–210`), while the run goes on.

**The guard** (`python -I shim.py --guard -- <command> <args…>`): remember `os.getppid()`; start the command with
`subprocess.Popen` (same stdin, stdout, stderr, process group and environment); a daemon thread polls `os.getppid()`
every 0.5 s and `os.killpg(0, SIGKILL)` when it changed; exit with the command's exit code (128 plus the signal's
number when a signal ended it, v2). It compares with the
original parent, not with 1, so a subreaper (systemd's user manager, the desktop app) changes nothing. One extra
Python process per stdio server, about 30 ms to start, standard library only. `-I` (isolated mode) keeps the shim's
own folder off `sys.path`, so a sibling module there (`wire.py`, `session.py`) can never shadow a standard-library
one the guard imports, and keeps `PYTHON*` variables of the server's environment from changing the guard.

### 4.7 What the panel learns of a server's tools

When the pump logs an `mcp.status`, the front writes, for each `bound` server, `$DR_HOME/mcp/<first 16 hex of
sha256(server name)>.json` = `{"v": 1, "server", "tool", "transport", "at", "run", "count", "told"}`, atomically
(a temporary file, then `os.replace`; mode 0600 in a 0700 directory). `GET /mcp` reads it for each grant (`seen`),
from the Library's own home (`library.path.parent`). It holds tool names and descriptions, never a secret. Replays
(`session/load`) do not write it.

### 4.8 Under plain `dr`, on an export

`dr <export>/main.yaml …` with the `mcp` package installed: each MCP block's factory connects from its snapshot (§4.3),
reading each `env` name and each header's variable from `dr`'s environment, one block after another inside
`make_tools` (each up to its connect timeout); a server it cannot reach becomes a stand-in and a structlog warning, and
the run goes on. No grant set is known there, so a hand-off is not refused (deep_reasoner's ordinary rule). Without
`mcp` installed the run still starts and the stand-in says `pip install mcp`.

*(v4, v5: one case where the run does not go on. A server the shim reaches, one of whose tools has a property schema
that is neither a mapping nor a boolean (a string, a number: no JSON Schema, so no valid server sends it), cannot be
described. `mcp_server` calls `bound()`, and so `describe()`, outside any handler, so the shim raises
`AttributeError`; `make_tools` passes it on (deep_reasoner `v2/cli.py:157`), and the run does not start. Until
`7eb7812` a boolean schema did the same (§6.2 B26). Under `dr-acp` the same server fails alone (B19). Read in the code
at `f69bc73`, and run by the as-built r2's probe (its #11). §14 item 15 is the same case.)*

---

## 5 · What a tool or a server can reach

Said plainly, as the spec asks; the Tools tab says the short form (`TOOLS_RISK`), under D5's `SAFETY`.

- **A tool you write** is Python that runs as you, inside the agent's worker process: when every conversation starts
  (its factory) and whenever an agent calls it. It can read and change any file you can (the conversation's folder is
  only the working directory, D5 §2.2), reach any host your machine can, read the worker's environment (the key
  proxy's tokens under your keys' names, which work only through the proxy and up to the spend cap, D5 §4.7; and your
  other Canvas secrets, which D5 leaves there on purpose), call the model through the `client` it is given (through
  the proxy, so counted against the cap), and touch everything else in the worker's memory: the REPL's variables,
  other tools, and the environment and header values of every MCP server granted in that conversation.
- **Check runs your code too**, as you, in the App backend's child process: without your secrets or a model, with the
  disk and the network.
- **A stdio MCP server** is a program `dr-acp`'s worker starts as you, for each conversation one of whose reachable
  namespaces is granted it, with exactly the environment Canvas's settings give it plus `HOME`, `LOGNAME`, `PATH`,
  `SHELL`, `TERM`, `USER`, in the conversation's folder. It can do anything a program of yours can: the whole disk,
  the network. It does not get the key proxy's tokens or your keys unless its settings name them; then E10's
  property (D5 §2.1, "not in any process the worker starts") does not hold for it, by your configuration (§11.4).
- **An HTTP or SSE server** runs elsewhere; it gets the headers Canvas's settings give it and the arguments the agent
  sends it. What it does with them is its operator's business.
- **A grant is not a sandbox.** It decides which namespaces' agents are given a tool or a server, and `dr-acp` refuses
  to hand a server to a sub-agent outside its grants. It does not stop code: any cell in any namespace can start any
  program you can, read Canvas's settings file and its key (D5 §2.2), or call a server's results it was passed.
- **The Library and its exports** hold your tools' sources and each granted server's command, arguments and URL (with
  anything you typed into them), never an environment or header value. The frame's URL carries the same non-secret
  fields (§7.5). *(v3: a server's arguments are not secrets, by Michael's ruling of 2026-10-03, §14 item 3; a stdio
  server's own log, `runs/<run>/mcp-<alias>.log`, is written with its env and header values redacted, §6.2 B18.)*

---

## 6 · Departures from the spec, and what the build changed

§6.1 is where this design departs from the approved spec (v1, unchanged in v2 but for marked notes). §6.2 is what the
build changed in this design (v2; v3–v6 added to it). None is a re-scope.

### 6.1 Where this design departs from, or adds to, the approved spec

Each is a refinement inside D4's scope unless it says otherwise; if the Conductor reads any as a change of what was
approved, it goes back to Michael. **Not yet ruled on:** the spec's dated notes accept D2's, S1's and S2's departures,
not these; Michael rules on them at Gate B, with §6.2.

1. **Saving through the panel runs Check, and refuses a tool that cannot build** (§3.5); failures Check cannot
   attribute can be saved anyway, explicitly. The spec has Check as a button that shows the result. Reason: every
   tool block is built in every conversation, so one broken tool stops all of them (decision C).
2. **Check runs without your secrets, without a model and in its own folder** (§3.3), with limits of 30, 10 and 10 s,
   and never reaches a model. The spec says "a throwaway process" and "a time limit".
3. **Six names are refused for new tools and grants** (`RESERVED_NAMES`, §3.2): deep_reasoner would let a tool hide
   its own `run_all` or `subagent`. A config imported with such a name still imports.
4. **"At session start" is when the conversation's run is built**, at its first message: D1 starts the worker there
   (D1 §2 step 4), so the servers are connected there, all at once, within one 10 s deadline, and the notice appears
   ahead of the first answer. The spec's sentence is kept. *(v2: each within its own connect timeout, 10 s by
   default, from one shared start; §6.2 B5.)*
5. **Grants follow deep_reasoner's namespace rules** (decision G): a grant to `a` reaches `a.b`; a sub-agent spawned
   into a granted namespace gets the server even when the conversation began elsewhere; a run starts every server
   granted to a namespace its agents can reach. The spec says "binds only the servers granted to the conversation's
   namespace"; read per agent, no agent outside a granted namespace ever gets a server's tools, which is E9's null.
6. **Handing a server to a sub-agent in a namespace not granted it is refused** in `dr-acp` (an addition that makes
   E9's null hold for explicit hand-offs too); under plain `dr` deep_reasoner's ordinary hand-off applies.
7. **A server that is not bound leaves a stand-in under its name** (decision H) that tells the agent why; none of its
   tools is bound. The spec's sentence "its tools are not bound in this conversation" stays true.
8. **A grant snapshots the server's non-secret settings for export**, and under `dr` its environment and header
   values come from environment variables (§4.2, §4.8). The spec says an export "still runs under `dr` with the `mcp`
   package installed"; it also needs the server's secrets in the environment.
9. **Each stdio server runs under a guard process** (decision I), because `mcp` detaches it from the worker's process
   group and a silent server otherwise outlives a killed worker (verified).
10. **The panel shows a server's tools as the last conversation saw them** (decision K); it cannot connect a server
    itself.
11. **D4's change to `dr-acp` is about 90 lines in D1's files, not 30** (§11.1): a RunEvent, its encoding and three
    sentences, the specs' filter, and the seen cache. *(v2: 101 lines added, `cf131e5`; §11.1 states the event and
    its sentences as D1's next revision should carry them.)*
12. **`mcp>=1.28,<2` becomes a runtime dependency of deep-reasoning** (the spec named it as a candidate); 1.28 is the
    first with `streamable_http_client(url, http_client=…)` and the SDK fork's lock.
13. **CodeMirror for the source field only** (decision L); D3 departed from the spec's React and CodeMirror; D4 brings
    CodeMirror back where the spec's Q6 costed it. *(v2: in D4's own `PythonField`, not D3's `CodeField`; the chunk
    is 348 KB against §7.4's 300 KB budget; §6.2 B1, B3.)*
14. **Size: about 2.0k lines of code and 2.2k of tests**, about 14 h at Gate C, against the spec's ≈1.0k with tests and
    ≈3 h (§13). *(v2: built at about 3.3k and 3.5k, about 23 h; §6.2 B16.)*

The spec's known gap B8 (`factory_from` builders do not receive `config_path`) is mirrored by Check, so Check and a
run agree, and is stated in `TOOL_HELP`; not worked around, as the spec says.

### 6.2 Changed by the build (v2–v6)

Each was checked against the code and folded into the section named: B1–B17 at `965f318` (v2), B18–B23 at `aa67f0a`
(v3), with B7, B12 and B16 updated there, B24–B27 at `f69bc73` (v4), with B16, B19 and B23 updated there, and B28–B29
at `f69bc73` too (v5, from the as-built r2). B1–B7 change behaviour or a contract v1 specified; B8–B9 are what v1 left
open, and the signatures; B10–B12 are dependencies and wiring; B13–B15 are how the tests prove it; B16 is the size;
B17 is what was not built; B18–B23 are what landed after the as-built document; B24–B27 what landed after v3; B28–B29
are where v1–v4 described the build wrongly and the build is right. B30 is the ruling made at Gate B, and B31–B37
(v6) what changed after it, each checked against the code at `68ebe81`, with v6 notes in B8, B11, B12, B15, B16, B25
and B30. Where the build recorded no reason, the reason
given is marked as this design's reading. The B-numbers are this section's; the spec's known gap B8 (`config_path`,
above) is another list.

**Behaviour**

- **B1. CodeMirror lives in a new `PythonField`, used only by the tool editor; D3's `CodeField` is unchanged** (§1.1
  L, §7.4, §11.3, A.6). v1's §7.4 and §11.3 had D3's `CodeField` load the editor chunk for `language: "python"`.
  `ui/components/python.tsx`'s `PythonField` mounts `createPythonEditor` from the chunk, and falls back to D3's
  `CodeField` (a textarea) when the chunk cannot load. *Why:* D3's decomposition cards give their code field
  `language: "python"` (`ui/components/editor.tsx`), so v1's route would have put CodeMirror into every card,
  against decision L's own "every other field keeps D3's textareas", and D3's browser tests fill those fields as
  textareas (`test_create.py`'s `dr-card-1-code`). *Pinned by:* `test_tools_tab.py::test_the_editor_keeps_python_indentation`;
  D3's `test_create.py`, unchanged and green.
- **B2. The editor owns its text once mounted; a reset remounts it; `PythonEditor` has no `setValue`** (§2.1, §7.4,
  A.6). `ToolEditor` keys its `PythonField` on a counter that it bumps whenever it replaces the draft (a save,
  **Discard draft**, **Reload**). *Why:* feeding the parent's copy of the text back into the editor replaced the
  document mid-keystroke and hung fast typing, which a browser test caught (the Implementer's report; `200e820`
  records it). *Pinned by:*
  `::test_the_editor_keeps_python_indentation` (types key by key), `::test_a_new_tool_is_written_checked_and_saved_with_its_grants`
  (the stored source byte for byte).
- **B3. `assets/editor.js` is 348 KB minified (348,475 bytes; 118 KB gzip), over §7.4's 300 KB budget** (§7.4). It
  loads only when the tool editor opens; `assets/app.js` is 169 KB, under D3's 250 KB. The editor uses the bare
  `pythonLanguage` instead of `python()`, which drops autocompletion (13 KB); the keymap (default, history, Tab
  indents), history, bracket matching, auto-indent and line numbers stay. *Why it does not fit:* measured for this
  revision (esbuild, minified, the versions the branch locks): the CodeMirror packages the editor uses come to 281 KB
  without Python's grammar and 349 KB with it (`@lezer/python`), which the built chunk matches; `python()` adds 13 KB.
  So no CodeMirror Python editor fits 300 KB; it is the grammar, not CodeMirror's core, that crosses the line (§14
  item 13). The budget was this design's guess (header, "Not verified"). Michael's choice: accept 348 KB loaded on
  demand, or §13's cut (D3's textarea with Tab handling instead, so `editor/python.ts`, `python.tsx` (141 lines) and
  the five CodeMirror packages go). *Pinned by:*
  `tests/library/test_ui.py::test_the_committed_build_is_complete` (the chunk exists and `app.js` loads it); no test
  pins its size.
- **B4. The REPL's server object and its stand-in show plain signatures** (§2.2, §4.3, A.3).
  `Server.__call__(self, tool, /, **arguments)` and `Unavailable.__call__(self, *args, **kwargs)` carry no annotations, so deep_reasoner
  tells the agent `` `github(tool, /, **arguments)` `` as §2.2 shows, not A.3's annotated
  `github(tool: str, /, **arguments: Any) -> Any`. `Unavailable.__getattr__` answers every name starting with `_` with
  `AttributeError`, as a plain object does, and raises `McpToolError` with its reason only for other names;
  `Unavailable` returns itself from `__copy__` and `__deepcopy__`. *Why:* `inspect.signature`, under deep_reasoner's
  `describe()`, probes `obj._partialmethod` (CPython 3.12's `inspect._signature_from_callable`; checked for this
  revision), so v1's stand-in raised `McpToolError` there and deep_reasoner could not describe it;
  `__cross_namespace__` and `__wrapped__` are probed the same way. *Pinned by:*
  `test_shim.py::test_the_description_is_what_8_4_says` (`echo(tool, /, **arguments)`),
  `::test_a_stand_in_is_plain_to_deep_reasoners_seams` (no `__cross_namespace__`, deep-copied to itself, told
  `echo(*args, **kwargs)`).
- **B5. Each server waits for its own `connect_timeout_s`, from one shared start** (§1.1 F, §4.4, §8.2, A.2). v1: one
  deadline for all, at the largest connect timeout. Built: every connection is started first; then each is waited for
  in turn until the shared start plus its own connect timeout. `McpServerStatus.seconds` holds, for `bound`, the time
  from the shared start until its wait returned, and for `no_answer`, the time it was given (its connect timeout),
  which `MCP_NO_ANSWER` prints. *Why (this design's reading):* §4.2 promises a grant's `connect_timeout_s` is
  honoured, and one deadline at the largest would hold a 2 s server for 10 s; with every grant at the default (10 s),
  as the panel writes them, nothing changes. *Pinned by:*
  `test_session.py::test_servers_connect_at_once_and_a_silent_one_is_given_up_at_the_deadline`,
  `test_acp.py::test_session_new_does_not_wait_and_the_first_answer_waits_at_most_the_deadline` (a 2 s grant:
  `no_answer` with `seconds` 2, decided 2 to 5 s after `worker.ready`). Open: §14 item 11.
- **B6. A server that dies fails the call in flight with `SERVER_STOPPED` too** (§4.3, §4.5). v1: the call in flight
  raises `McpError: Connection closed`, later calls `SERVER_STOPPED`. Built: `Connection.call` reads the `McpError`'s
  code. `-32000` (`CONNECTION_CLOSED`) marks the connection dead and raises `SERVER_STOPPED`, whose detail is
  `McpError: Connection closed`, for that call and every later one; `408` (`mcp`'s own read timeout) raises
  `CALL_TIMEOUT`; any other is `CALL_FAILED`. *Why (this design's reading):* one sentence for a dead server, whichever
  call met it. *Pinned by:* `test_shim.py::test_a_server_that_dies_fails_the_call_and_every_later_one_at_once`,
  `test_acp.py::test_a_server_that_crashes_mid_run_fails_the_call_and_the_run_goes_on`,
  `test_shim.py::test_a_call_that_never_answers_raises_after_its_timeout`.
- **B7. Check's process has two more ways to end** (§3.3, §9.1). `CHILD_ENDED` gains a third phase, `trying it`: a
  child that ends while evaluating the tried expression leaves the build ✓, and the example carries the sentence. A
  child that cannot be started (`Popen` raises `OSError`) is `unavailable`, `CHILD_ENDED` naming the error with phase
  `starting`. *Why (this design's reading):* v1 named two phases only, and a child that cannot start is Check not
  starting. *Pinned by:* `test_check.py::test_a_tool_that_ends_the_process_is_raised_saying_how_it_ended` (phase
  `building the tool`); v3 (`6fdee0d`, no code change) pins the two new cases:
  `::test_an_example_that_ends_the_process_says_how_and_the_build_stays_ok` (the expression calls `os._exit(5)`) and
  `::test_a_check_whose_process_cannot_be_started_is_unavailable` (`sys.executable` names a missing file).

**Where v1 was silent, and the signatures**

- **B8. The frame's components, as built** (§2.1, §2.2, §8.6, A.6, Appendix B).
  - `ToolEditorProps` has no `takenNames`, and has `onBackendLost` (D3's `OnBackendLost`, which D3's `attempt` needs
    for every request); `McpServerRowProps` gains `onBackendLost` too. The editor does not check a name itself: the
    backend's Check and `PUT` refuse a bad or reserved name (`invalid`), D2 a taken one (`409`), and the editor shows
    the sentence that comes back. *Why (this design's reading):* one place for the rule, the backend's.
  - `CheckResultProps` drops `saving`: the report renders the same whether it came from Check or from a refused save,
    and offers **Save anyway** whenever `can_save_anyway`. *Why (this design's reading):* the flag changed nothing
    shown.
  - D3's `ConfirmRow` gains an optional `confirmTestId` (default D3's `dr-confirm-yes`), so the delete confirmation
    carries Appendix B's `dr-tool-delete-confirm`. A new test id, `dr-check-status`, marks `CHECKING` and
    `SAVING_CHECKING` while they show; the browser tests wait on it.
  - Tool rows keep D3's text, `factory make · tools/word_count.py` (`factory rag` without a source), not v1's
    `make · tools/word_count.py` and `built-in rag`. *Why (this design's reading):* D3's
    `test_the_tools_tab_lists_tools_with_their_grants` asserts that text, and §10.4 keeps D3's tests green.
  - With Canvas's settings unread (`mcp` null), `mcpRows` gives each grant a row in state `given` with `info` null,
    drawn from its stored snapshot. *Why (this design's reading):* without Canvas's list, "gone" cannot be told from
    "not read", and `MCP_SETTINGS_UNKNOWN` says which it is. *Pinned by:* `tools.test.ts` ("without Canvas's settings,
    lists only the grants, none of them gone"), `test_tools_tab.py::test_without_canvas_settings_only_grants_are_shown`.
  - Smaller: `toolDraftKey` returns `tool.<name>` (`tool.new`), to which D3's `drafts.ts` adds `dr-library.draft.`, so
    the stored key is v1's. New exported names: `RESERVED_NAMES`, `McpSnapshot` and `grantSnapshot` (`ui/tools.ts`),
    `MCP_TRANSPORTS` (`shared/protocol.ts`), `LibraryError.check` (`ui/api.ts`: the report a `422 check_failed`
    carries), `mcpTestId` (`McpServerRow.tsx`). `vite.config.ts` assigns the chunk by module path (CodeMirror, Lezer,
    their three helper packages, and `src/ui/editor/`), not by an object of package names. *(v6, B33: `RESERVED_NAMES`
    is module-private in `ui/tools.ts`; `McpSnapshot` is an interface in `ui/types.ts`; `grantSnapshot` is gone.)*
- **B9. Python signatures and names added** (§3.2, §4.6, §9.1, A.1–A.3).
  - `ToolCheckFailed(name, report)`: the name is for `CHECK_FAILED`'s sentence, which names the tool.
  - `Connection(…, name=…)`: the REPL name that `CALL_FAILED`, `CALL_TIMEOUT` and `SERVER_STOPPED` use (default: the
    server's name); `open_session` and the shim's factory pass the alias.
  - §9.1's sentences with fields are lower-case functions of them in `tools/texts.py` (`texts.reserved_name(name)`,
    `texts.check_failed(name)`, …), D1 §5.6's convention, since the Code Guide forbids `.format()`; `BUILT`,
    `MCP_NEEDS_COMMAND` and `MCP_NEEDS_URL` are constants. The shim's (§9.2) stay `str.format` templates, as v1
    specified them (§14 item 14).
  - New constants: `check.CHILD`; `wire.SECRET_MIN` (4), `SEEN_VERSION`, `REMOTE`; `shim.CALL_GRACE_S` (5 s past
    `call_timeout_s`), `HTTP_TIMEOUT_S` and `HTTP_READ_TIMEOUT_S` (`mcp`'s own defaults, for the HTTP client the shim
    builds), `REQUEST_TIMEOUT` (408), `CONNECTION_CLOSED` (-32000), `JSON_TYPES`, `MISSING_ENV`;
    `session.GRANTED_NOWHERE`, `OUT_OF_REACH`, `LOG_TAIL` (300), `PRINTED`.
  - `check_tool` reports an MCP grant's block as outcome `invalid` with `MCP_VIA_GRANT` (§3.2 item 3 named no
    outcome). The guard exits with the command's code, or 128 plus the signal's number when a signal ended it (§4.6).

  *Why (this design's reading)*, beyond the two named: each serves a sentence or a value v1 described in words.

**Dependencies and wiring**

- **B10. `mcp` resolves to 1.30.0 under `>=1.28,<2`** (header, §6.1 item 12, §12). v1 verified 1.28.1, the SDK
  fork's lock. *Why:* the branch's lock takes the newest release in the range (recorded in `cd3e153`). M1 and M2 were
  rechecked in 1.30.0's source by the build and again for this revision (§12's line numbers are 1.30.0's), and the
  whole suite runs on it.
- **B11. D1's golden recordings: only the `initialize` line changed, by hand** (§10.3). v1: re-recorded with D1's
  command. Each of the 18 recordings differs from D3's base in that one line (`mcpCapabilities` `false` → `true`);
  D1's `test_initialize_advertises_load_close_and_no_mcp_transports` is now
  `test_initialize_advertises_load_close_and_http_and_sse_mcp`. *Why (recorded in `cf131e5`, "that line only"):*
  nothing else in any stream changes. *(v6, B37: there are 20 recordings, each with that one line changed: D3's
  merge brought D1's `unanswered.flat` and `unanswered.native`.)*
- **B12. Wiring** (§7.1, §7.2, §11.2).
  - `pyproject.toml`'s ruff `extend-exclude` adds `tests/mcp/fixtures`: it holds `shim_v1.py`, the v1 shim frozen as a
    Library stores it, which formatting would change (the comment in `pyproject.toml`).
  - `create_app` imports `require_check` and `tool_routes` inside the function: `tools/routes.py` imports
    `json_route` from `library/api.py`, so importing it at `api.py`'s module level is circular (the comment in the
    code). *(v6, B31: `json_route` is gone; `tools/routes.py` imports only `_parse` from `api.py`, which keeps the
    cycle, so the two imports stay inside `create_app`.)*
  - `tools/routes.py` imports D2's private `_parse` (a body model's 400 with D2's `BAD_REQUEST`), so D4's bodies fail
    exactly as D2's. *Why (this design's reading):* no second copy of D2's error mapping. A private name crossing
    packages is for the Refactorer at Gate C: make it public beside `json_route`. (v3: `_parse` also takes the
    sentence to lead with, B21.) *(v6: the refactor left `_parse` private and imported, B31.)*
  - `tests/processes.py` (30 lines) holds `running_after`, which `tests/tools/` and `tests/mcp/` share.

**How the tests prove it**

- **B13. D3's shared browser fixture Library gets no raising tool** (§10.4). v1 said `library_home` gains one. *Why:*
  E8 (`test_e8_next_conversation.py`) runs real conversations from that Library, and `make_tools` builds every tool
  block, granted or not (§11.2), so a raising tool there would stop every E8 conversation. D4's browser tests make
  such a tool inside the test (`test_a_raising_factory_offers_save_anyway` writes `env_at_build.py` through the
  editor).
- **B14. Fixtures, as built** (§2.1's failure cells, §8.3, §10.2).
  - The syntax error is `def make(` (inline in `test_check.py`), which Python 3.12 reports as `'(' was never closed`;
    v1's `def make(:` gives only `invalid syntax` there. §2.1's cell is corrected. There is no `syntax.py`, and
    `misspelled` is `word_count.py` with `factory: mkae`.
  - Two fixtures more: `exits.py` (ends its process with code 3 while building) and `calls_model.py` (calls the model
    from its factory). The agreement test runs eight: works, not_func, misspelled, import_error, hang, env_at_build,
    prints, exits.
  - A FastMCP tool returning a bare `dict` advertises no `outputSchema` and sends the dict as JSON text with no
    structured content (measured again on 1.30.0 for this revision), so by §8.3 the shim returns that text as a `str`:
    it never parses text as JSON. The fake server's `add` returns a `TypedDict` (`Sum`) to exercise the dict case.
    *Pinned by:* `test_shim.py::test_results_are_unwrapped_dicts_text_or_blocks`.
  - `echo_server.py` has eleven tools: `echo`, `add`, `plain` (text without structured content), `picture` (an image
    block), `fail`, `token`, `env_names`, `sleep`, `crash`, `2nd-opinion` (no attribute name) and `whoami`;
    `--sse PORT` beside `--http PORT`; with `ECHO_MARKER_DIR` set it writes a file named after its pid when it starts.
    `catalog_server.py` is the live tier's.
- **B15. Test names, as built** (§10.2–§10.4). Every name v1 listed exists. Added:
  `test_check.py::test_a_name_d2_refuses_is_invalid_in_d2s_words`, `::test_an_mcp_grant_is_not_checked_as_a_tool_of_your_own`,
  `::test_a_tool_that_ends_the_process_is_raised_saying_how_it_ended`,
  `::test_a_check_that_cannot_start_deep_reasoner_in_time_is_unavailable`;
  `test_routes.py::test_a_checked_tool_is_saved_with_its_grants`,
  `::test_put_mcp_refuses_a_name_the_repl_cannot_bind[run_all, not a name, class]`;
  `test_grants.py::test_mcp_block_needs_a_command_or_a_url`, `::test_the_shim_source_starts_with_its_marker_and_version`,
  `::test_grant_record_reads_the_block`; `test_shim.py::test_a_stand_in_is_plain_to_deep_reasoners_seams`,
  `::test_a_server_it_cannot_reach_becomes_a_stand_in_saying_why[crashes, hangs]`,
  `::test_a_server_that_dies_fails_the_call_and_every_later_one_at_once`, `::test_a_hand_off_outside_the_grant_is_refused`;
  `test_session.py::test_without_mcp_blocks_the_session_is_empty`; in D1's files,
  `tests/acp/test_encoder.py::test_each_mcp_server_not_bound_is_a_notice_on_the_root[native, flat, replay]`; vitest's
  `mount.test.ts` ("reads Canvas's MCP servers for the Tools tab only"); and `tests/library/test_ui.py::test_the_committed_build_is_complete`
  now requires the editor chunk. `test_put_mcp_refuses_a_stdio_grant_without_a_command` runs stdio, http and sse, and
  `test_an_http_server_is_reached_with_its_headers` http and sse. *(v6, B34: the first is now
  `test_put_mcp_refuses_a_grant_without_its_command_or_url`.)*

**Size**

- **B16. About 3.4k lines of code and 3.8k of tests, against v1's ≈2.0k and ≈2.2k** (§6.1 item 14, §13) and the
  spec's ≈1.0k with tests. Lines added at `f69bc73` over D3's finished head `d4e9cd3` (v3's column: at `aa67f0a`, over
  the same base; v2's: at `965f318` over `5effe26`), by §13's parts; the file sizes are v4's:

  | Part | Code, v1 → v2 → v3 → v4 | Tests, v1 → v2 → v3 → v4 |
  |---|---|---|
  | Check: `check.py` 392, `check_child.py` 128, `texts.py` 100 | 300 → 605 → 620 → 620 | 330 → 526 → 553 → 553 (`test_check.py` 474, fixtures 79) |
  | Routes and the gate: `routes.py` 80, D2's `api.py` 70 (and 46 removed: most of that change is `route` moved to module level as `json_route`) | 125 → 142 → 150 → 150 | 200 → 301 → 341 → 341 |
  | MCP: `shim.py` 541, `wire.py` 163, `grants.py` 98, `session.py` 244 | 540 → 981 → 1,044 → 1,046 | 650 → 1,102 → 1,207 → 1,291 (`test_shim` 412, `test_session` 341, `test_grants` 172, `test_wire` 149, fake servers 217: `echo` 109, `odd` 31, `loud` 30, `catalog` 22, `crash` 14, `hang` 11) |
  | D1's changes | 90 → 101 → 101 → 101 | 330 → 567 → 570 → 570 (`tests/mcp/test_acp.py` 495, D1's test files 45, `tests/processes.py` 30) |
  | Export and live tier | — | 200 → 227 → 227 → 235 (`test_export.py` 67, the MCP live test 89, the tool live test 79) |
  | The frame: `ToolEditor` 361, `McpServerRow` 203, `tools.ts` 165, `tabs/tools.tsx` 151, `context.ts` 86, `editor/python.ts` 74, `CheckResult` 73, `texts.ts` 69, `python.tsx` 67, `types.ts` 59, `styles.css` 55, `protocol.ts` 51, `api.ts` 34, `mount.ts` 10, `vite.config.ts` 9, `package.json` 5, `fields.tsx` 3 | 920 → 1,475 → 1,475 → 1,475 | 480 → 788 → 788 → 788 (vitest 433, browser 352, `test_ui.py` 3) |
  | `pyproject.toml`, the two packages' `__init__.py` | — → 7 → 7 → 7 | |
  | **Total** | **≈1.98k → 3,311 → 3,397 → 3,399** | **≈2.19k → 3,511 → 3,686 → 3,778** |

  About 7.2k lines (v3: 7.1k), about 24 h at Gate C at the workspace's rate. Not counted: the built assets, the two
  lock files, D1's golden recordings (18 one-line changes, B11), `tests/mcp/fixtures/shim_v1.py` (539 lines, the v1
  shim as stored) and, v4, the live job's 18 lines in `.github/workflows/live.yml` (B25). v4's growth is B24–B27: the
  shim's `_type` (2 lines), two fake servers (38: `loud_server.py`, and `odd_server.py`'s
  properties), three tests and B19's changed case (46), and the live tests (8). The shim, Check and the editor
  component grew most. The build recorded no reason; the estimate was this design's. Michael rules on it at Gate B.

  *(v6, B37: at `68ebe81`, over D3's refactored head `73c6425`, measured the same way: **3,314 lines of code and
  3,807 of tests**, 7,121 in all, about 24 h at Gate C. By part, code then tests: Check 595 (`check.py` 369,
  `check_child.py` 126, `texts.py` 100) and 573 (`test_check.py` 470, fixtures 79, conftest 24); routes and the gate
  103 (`routes.py` 86, D2's `api.py` +17 −5, B31) and 333; MCP 1,046 and 1,296 (`test_session` 328, `test_grants`
  167, conftest 23); D1's files 101 and 485 (`test_acp.py` 410); export and live tier 228 (`test_export.py` 60); the
  frame 1,462 (`ToolEditor` 356, `McpServerRow` 194, `tools.ts` 146, `context.ts` 109, `types.ts` 63) and 892
  (vitest 534, browser 355, `test_ui.py` 3); `pyproject.toml` and the `__init__.py` files 7. The golden recordings
  are 20 (B11). Against `f69bc73`'s 3,399 and 3,778: the route cut, the refactor and B30 in the code; the conftests,
  the `converse` fixture, B30's and B35's vitest cases and the three tests of B32 and B33 in the tests.)*

**Not built**

- **B17. Left to D5 or to proposals, as v1 marked them:** §11.4 (E10 with MCP servers bound, the E12 step, D5's
  `deep_reasoner` profile with `mcp_server_refs: null`, which D4 reads and does not create), §10.6's
  cross-repository forwarding test, and D2's proposed `only_granted` (§11.2). Nothing in D4's code depends on them;
  until §10.6 or E12 runs, the forwarding shape stays read, not run (§14 items 1 and 12).

**After the as-built (v3)**

Each landed after v2, answering the as-built document at `756f5f9` or v2's own list, and was checked against the code
at `aa67f0a`.

- **B18. A server's own log is written through a redacting pipe** (§4.4, §5; `059b738`). v2's build gave a stdio
  server `runs/<run>/mcp-<alias>.log` as its stderr, so what it printed reached that log unredacted; only the status's
  detail and the notice were redacted. Built: the server's stderr is a pipe, and a thread copies it into the log: it
  reads `PIPE_READ` (64 KiB) at a time, decodes incrementally, applies `wire.redact` with the spec's env and header
  values, and writes all but the last (longest secret − 1) characters, which wait for the next read, so a secret
  split across two writes is still caught. Once the server is bound or has failed, `open_session` closes its end of
  the pipe; for a failure it waits up to `DRAIN_S` (2 s) for the copy before reading the log's tail. **Arguments are
  not redacted:** Michael ruled on 2026-10-03 (relayed by the Conductor) that a server's command-line arguments are
  not secrets, as designed (keys go in `env`; §5, §14 item 3). *Why (recorded in `059b738`):* the same text that
  §4.4 redacts in a failure's detail reached the log whole. *Pinned by:*
  `test_session.py::test_a_server_that_exits_at_start_is_failed_with_its_stderr_redacted[whole, split]` (the log
  reads `invalid token [redacted]`, the token printed in one write or two), and
  `test_acp.py::test_server_secrets_never_reach_the_run_log_or_the_transcript`, which now checks the server's log.
- **B19. One server that `open_session` cannot start or bind fails alone; the run goes on** (§4.4, §4.5, §11.1;
  `c2cfdc0`). Found by the as-built (its §2 #3; v2's §11.1 note named only the namespace case): `open_session` had no
  handler of its own, so an error about one server ended the whole build as D1's `build_failed`: its log not opening,
  its block not read (a `connect_timeout_s` that is not a number), its binding not described (a tool property whose
  schema is `true`, which the shim's `describe` cannot render, §14 item 15; v4: it can since B26, so the test's case
  now uses a schema that is a string). Built: starting each server and deciding it each run under a handler; the error
  becomes that server's status, `failed`, with its `"Type: message"` redacted as a failure's detail is, and a stand-in
  that says why; a connection already started is abandoned. The other servers bind. An error in deep_reasoner's own
  namespace resolution still fails the build. *Why (recorded in `c2cfdc0`):* §11.1 promised a failure caught per
  server; and in a run built from the Library, D2's invariants (root exists, every namespace's parent exists, checked
  on every save) leave only namespace errors that `build_reasoner` raises next anyway. *Caveat:* a hand-written config
  run through `dr-acp --config`, with a broken namespace outside the entry namespace's chain, fails here when it has
  an MCP block, where `build_reasoner` alone would not (§14 item 16). *Pinned by:*
  `test_session.py::test_a_server_open_session_cannot_bind_fails_alone_and_the_others_bind[…]` (cases: its log cannot
  be opened, its block has no number, it cannot be told; a new fake server, `tests/mcp/servers/odd_server.py`) and
  `::test_a_namespace_registry_deep_reasoner_refuses_fails_the_build_as_it_would_anyway` (`open_session` and
  `build_reasoner` raise the same error, and nothing is written to the run's folder).
- **B20. A write of the other kind over a tool's head is refused, `409 refused`** (§2.2, §3.5, §4.2, §7.2, §9.1;
  `55f139f`). Found by the as-built (its §2 #7): D2's `409` for a taken name came only with `base_version: 0`, so
  `PUT /mcp/{name}` sent with the head's version replaced a tool of your own with a grant, and `PUT /tools/{name}`
  replaced a grant with a tool of your own (`require_check` refused only a body whose block is `mcp_server`). Built:
  both are refused at any `base_version`, before anything is checked or written: `PUT /mcp` over a tool of your own
  with `MCP_NAME_TAKEN` (new in `tools/texts.py`, the frame's sentence), `PUT /tools` over a grant with
  `MCP_VIA_GRANT`. So a grant changes only through `PUT /mcp`, as §2.2 has the panel do. The panel shows a `refused`
  message as sent, so its first tick on a taken name reads as before. *Why (recorded in `55f139f`):* `409 refused` is
  the answer §4.2 gives a grant's name clash (`MCP_SERVER_TAKEN`). *Pinned by:*
  `test_routes.py::test_a_grant_cannot_replace_a_tool_of_your_own[new, the head's]`,
  `::test_a_tool_of_your_own_cannot_replace_a_grant[new, the head's]`.
- **B21. `PUT /mcp`'s 400 names the MCP body's fields** (§4.2, §7.2, §9.1, §11.2; `4a86581`). v2's build answered a
  body it could not read with D2's `BAD_REQUEST`, which names `yaml`, a field the MCP body does not have. Built:
  `MCP_BAD_REQUEST` (new), then pydantic's reason, through D2's `_parse`, which gains an optional
  `sentence: str = texts.BAD_REQUEST`; D2's own callers are unchanged. *Why (recorded in `4a86581`):* the sentence
  names the body the route takes. *Pinned by:*
  `test_routes.py::test_a_put_mcp_body_it_cannot_read_is_told_the_mcp_bodys_fields[…]` (cases: no base_version, a
  yaml it does not have).
- **B22. D3's finished head is merged** (`aa67f0a`, D3's `d4e9cd3`): D3's design v3 and as-built document, and D3's
  fixes in three of its own frame files (`page/backend.ts`, `ui/components/editor.tsx`, `ui/tabs/namespaces.tsx`) with
  their tests. D4 changed none of the three, so no source file conflicted; the built files were rebuilt with `npm ci`
  and `npm run build` (`app.js` is 169,027 bytes; `editor.js`, `app.css` and `index.html` came out unchanged). B16's
  counts are now taken over `d4e9cd3`.
- **B23. Three details the as-built found that v2 missed** (`756f5f9`, its §2 #9, #21, #23; no code change):
  - The tool editor's header is `Tools › <name> v<n>`, without §2.1's `· saved <date>`. The build recorded no reason.
  - `tests/mcp/fixtures/shim_v1.py` is byte-identical to today's `shim.py`, so until the shim changes,
    `test_a_stored_v1_shim_works_with_todays_session` exercises today's text; what it pins now is that a stored file,
    loaded through `load_tool_factory`, reads the package's `SESSION`. *(v4: no longer identical. `7eb7812` changed
    today's `_type` (B26) and left the fixture as it was stored, so the test now runs an older stored text against
    today's `SESSION`, which is what it was written for.)*
  - The agreement test's eight cases leave out `spawns.py`, which
    `test_check.py::test_nothing_a_stopped_tool_started_is_left_running` covers instead.

**After v3 (v4)**

Each landed after v3, and was checked against the code at `f69bc73`. Only B26 changes product code; B24 is a test,
B25 the live job's machinery, B27 the live tier's two questions.

- **B24. A server that prints more than a pipe holds still answers, and its log is still redacted** (§4.4; `1847ef0`;
  a test, no code change). Since B18 a stdio server's stderr is a pipe that a thread copies into
  `runs/<run>/mcp-<alias>.log`. *Why (recorded in `1847ef0`):* if that copy stopped, a server printing more than the
  pipe holds (64 KB) would block on its own stderr and stop answering, and no test pinned it. A new fake server,
  `tests/mcp/servers/loud_server.py`, prints 1 MB at start and 256 KB on each call of its one tool, `say`, with its
  `LOUD_TOKEN` on every line. *Pinned by:*
  `test_session.py::test_a_server_that_prints_more_than_a_pipe_holds_answers_and_its_log_is_redacted`: the server is
  bound, three calls answer, and once it has ended its log is exactly every line it printed, with the token as
  `[redacted]`. The commit records that with the copier never started the server is `no_answer` at its 10 s connect
  timeout, so the test fails without the copy.
- **B25. The live job keeps a failed run's evidence** (§10.5; `9255778`; the job and one test, no product code).
  `.github/workflows/live.yml` runs pytest with `--basetemp="$RUNNER_TEMP/live"`. On a failure, a step checks that no
  file under it holds the model key (`grep -rqF -- "$OPENAI_API_KEY"`), and only if that passed is every test's dr home
  uploaded as the artifact `live-dr-homes`, kept 7 days: its runs' `events.jsonl`, `llm_calls.jsonl`, deep_reasoner's
  trace, `worker.log` and each `mcp-<alias>.log` (redacted, B18). `tests/mcp/test_live.py` writes the ACP transcript
  to `<home>/transcript.jsonl`, and its first assertion's message is the run's `mcp.status`, `agent.end` and
  `prompt.end` events, one per line: how the server was bound, and how each agent and the prompt ended. *Why
  (recorded in `9255778`):* run 37145903109 failed the MCP live test twice at `aa67f0a` and kept nothing to say why;
  the job log held only the assertion. *Used:* the three failed attempts at `7eb7812` kept their homes, and B27's
  account of the tool test's failure is read from them. Not pinned by a test (it is the job's own machinery); the
  commit records a local check that a scripted run's home holds neither the key nor the server's token. The step
  checks the model key only; the catalog server's token is a random value made for the run. *(v6, B36: the step is
  now "No dr home holds a secret", and checks every secret the job holds, `OPENAI_API_KEY`,
  `CLAUDE_CODE_OAUTH_TOKEN` and `DEEP_REASONER_TOKEN`, skipping an empty one; it fails closed, so only grep's exit 1
  lets the homes be uploaded.)*
- **B26. The shim describes a property schema of `true` as `Any` and of `false` as `Never`** (§8.4, §4.8, §14 item
  15; `7eb7812`). JSON Schema allows a boolean as a schema: `true` takes any value, `false` none. v1–v3's `_type` read
  every property schema as a mapping, so a tool with such a property could not be described: under `dr-acp` its
  server failed alone (B19); under plain `dr` the shim's factory raised `AttributeError`, `make_tools` raised, and the
  whole run did not start. Built: `_type(schema: Mapping[str, Any] | bool)` answers `Any` for `true` and `Never` for
  `false`, the nearest names §8.4's types have. *Why (recorded in `7eb7812`):* the as-built found it (the commit
  cites its #26), and §14 item 15 had left it open. *The stored shim,* as §14 item 14 foresaw: the edit changes the
  text every new grant stores, so a grant written before it reads `MCP_SHIM_OLD` until its **Update**; it keeps
  working under `dr-acp`, where its factory only reads `SESSION`, and under plain `dr` its export keeps the old
  `_type` until then. Nothing has shipped, so no grant outside the tests has the old text. The marker stays at
  version 1: the contract between a stored shim and the package (`SESSION`) is unchanged, `is_mcp_tool` reads only
  the marker's prefix, and `shim_current` compares the text. `tests/mcp/fixtures/shim_v1.py` stays as it was stored
  (B23). *Pinned by:* `test_session.py::test_a_tool_whose_properties_take_any_value_or_none_is_bound_and_told_so`
  (under `dr-acp`'s worker) and `test_shim.py::test_properties_that_take_any_value_or_none_are_described_as_any_and_never`
  (plain `dr`), each told `odd.odd(anything: Any = …, nothing: Never = …) -> str`. `odd_server.py` takes its
  properties from `ODD_PROPERTIES` (by default `{"anything": true, "nothing": false}`), and B19's case "it cannot be
  told" now gives it a property schema that is not a schema at all (a string): `AttributeError: 'str' object has no
  attribute 'get'`. *Left:* under plain `dr`, such a server, which no valid server sends, still stops the run (§4.8,
  §14 item 15).
- **B27. The two live tests name their tool or server in the task** (§10.5, §14 item 8; `933ac08`, `f69bc73`). The
  tool test asks "Use course_credits to find how many credits course ZQ-417 is." (v1–v3: "How many credits is course
  ZQ-417?"); the MCP test asks "Use the catalog server to find what a student must finish before ZQ-417." (v1–v3:
  "What must a student finish before ZQ-417?"), naming the server, not its method. Each is a `TASK` constant with a
  one-line comment saying why. Every assertion stays: the outcome `answered`; the answer holds `7`, and a cell called
  `course_credits(` and printed `7`; or the answer holds `ZQ-101`, `mcp.status` says `bound`, a cell called
  `catalog.prerequisites(`, and the token is in neither the run log nor the updates. *Why (recorded in `933ac08` and
  `f69bc73`):* asked bare, gpt-6-luna answered "4 credits." without writing a cell, 30 turns in each of the two
  attempts of run 37153297958, although the tool was built, bound and described; the MCP test's bare question had
  the same weakness, though it answered in all three runs at `7eb7812`. What the tests pin is that a tool or server
  is bound and works when called, not that the model chooses to call it. *Departs from* v1's §10.5 only in what it
  adds: the facts are still the tool's and the server's alone; the task now also says where they are. *Pinned by:*
  the two live runs at `f69bc73`, 6 of 6 each (Gate B section).

**Where v1–v4 described the build wrongly (v5)**

Found by the as-built r2 (`2353fe6`, its §1.2), and so already at `aa67f0a`. Each was read in the code at `f69bc73`.
In both the design is what was wrong, and the build stands; neither commit recorded a reason, so each reason is this
design's reading.

- **B28. A server's JSON-RPC error reaches the cell in the server's words, without its type** (§4.3, §4.5; r2 #9;
  `shim.py:265–271`). v1's §4.3 had every call failure that is not a timeout or a dead server raise `CALL_FAILED`
  "with the innermost exception", which is "Type: message". Built: an `McpError` whose code is neither 408 nor −32000
  raises `CALL_FAILED` with `str(exc)`, the server's message alone (`github.search failed: <its message>`); any other
  exception keeps "Type: message". *Why the build is right (this design's reading):* such an error is the server's
  own sentence about the call, as an `isError` result is, and §8.3 already passes that one on bare; in that branch
  the type is always `McpError`, so it would add a word and no information, while for an exception raised on our
  side (a `TypeError`, a validation error) the type is the information. *Not pinned:* FastMCP reports a tool's own
  failure as `isError` (`test_a_failed_call_raises_mcp_tool_error_with_the_servers_text`), so this branch is reached
  only by a protocol-level error, which no fake server sends.
- **B29. A `422 invalid` on Save shows D2's message, without marking the fields** (§2.1, §3.2; r2 #10;
  `ToolEditor.tsx:122–128, 323–349`). v1's §2.1 said "a `409` and a `422 invalid` are D3's (§5.2 there)", and D3's
  §5.2 places D2's field errors on the cards they name (`editor.tsx:437–441`). Built: the tool editor shows the error's
  message in `dr-errors` and does not use D3's `FieldErrors`; a `409 conflict` on a saved tool gets D3's **Reload**
  and **Save over**. Check's `invalid` is the same: `CheckReport` carries D2's message and no list (`check.py:330`).
  *Why the build is right (this design's reading):* D2's message is one line per field error, each with its field
  (`  name: …`, `  factory_from: …`, `library/texts.py:28–33`), and the banner keeps its lines (`white-space:
  pre-wrap`), so nothing D2 says is lost; D3's own banner shows the same message on a failed save, and what D3 adds,
  placing each error on its card, has no counterpart in a form of three fields. *Not pinned:* no browser test sends
  a block D2 refuses; D3's `api.test.ts` case "a D2 validation error carries its field errors" pins only that the
  frame keeps them.

**Decided at Gate B**

- **B30 (2026-10-03). An export names the header variables a remote server's `auth` sends** (§4.8, §6.1 item 8,
  §7.5; the Gate B section's third ruling, which Michael decided as (b); as-built r2 #12; `87f24e5` the tests,
  `e32bc3d` the code). `mcpServersFromSettings`
  adds to a server's `headers`, after its own and each name once, the headers the bridge sends for its `auth`:
  `Authorization` for `bearer`, `basic` and an `api_key` without a `header_name`; the `header_name` when it has one;
  a `header` strategy's keys; none for `none` or `oauth2`. A grant then names a variable for each
  (`POSTGRES_AUTHORIZATION`), which under `dr` holds the whole header value (`Bearer …`), and a grant made before
  offers **Update**. *(v6: an HTTP or SSE grant only. The frame names an `auth`'s headers whatever the transport, so
  for a stdio entry too, which the SDK fork's `MCPServer` accepts (as-built r3 #1, #10); but a stdio block keeps no
  headers (§4.2), and since B35 `mcpRows` does not compare a stdio server's, so for stdio the names are neither
  stored nor compared. The bridge forwards neither headers nor `auth` to a stdio server, so a conversation is the same
  either way.)* The Python side and `MCP_EXPORT_NOTE` are unchanged: an `auth` header is now a header. The names
  were run, not read: on the SDK fork at `91430aa`, `_remote_mcp_headers` sends exactly these, and `GET
  /api/settings` without `X-Expose-Secrets` returns `strategy`, `username`, `header_name` and the header keys, every
  secret as `**********` and an unset one absent (§14 item 12, for `auth`). Re-run on 2026-10-04 at `fd0fc84`: the
  frame's `mcpServersFromSettings`, given that route's own answer, names exactly the headers `_remote_mcp_headers`
  sends, for each strategy with its secret set (an `api_key` whose `header_name` is `""` included). An `auth` whose
  secret is unset still names its header, which the bridge does not send; under `dr` that variable, unset too, is
  left out (§4.3). Stop trusting §7.5's v5 note that an entry's `auth` is not read, and §14 item 6's that
  header-compatible `auth` is not exported. OAuth stays unexported (§14 item 6). *Pinned by:*
  `context.test.ts`'s "adds the header names a remote server's auth sends" [bearer, basic, an API key without a
  header name, an API key with a header name, named headers, none, OAuth]; the rest of the path was pinned already,
  by `test_grants.py::test_mcp_block_for_stdio_http_and_sse[http]` and
  `test_shim.py::test_an_http_server_is_reached_with_its_headers[http, sse]`. (v6: that a stdio row is not changed by
  a header name is B35's.)

**After Gate B (v6)**

Each landed after Gate B, and was checked against the code at `68ebe81`. B31–B34 are the merge of D3's and D2's
refactored heads and D4's literate refactor, which changed no behaviour a test pins; B35 and B36 answer the as-built
r3's #10 and #11; B32 and B33 also carry `6739e0f`, the tests for r3's M1, M3 and M4; B37 is what moved with the
merges.

- **B31. D4's routes take D2's own `route`; `json_route` is gone** (§7.1, §7.2, §11.2, B12, B16, A.2, A.5;
  `01abb88`). D2's refactor deleted the `_dump` that `json_route` called, and the merge took the Scout's cut:
  `tool_routes(library, route)` takes `create_app`'s `route` closure, typed `Callable[[str, str, Handler], Route]`
  with `Handler = Callable[[Request, bytes], Any]`, and `create_app` appends `*tool_routes(lib, route)`. D2's
  `route` is D2's code, unchanged, so D4's edit to `api.py` is +17 −5 (it was +70 −46): `accept_check_failure`,
  `_parse`'s `sentence`, `require_check` in `put_tool`, the routes, and the two imports inside `create_app`, which
  stay because `tools/routes.py` still imports D2's private `_parse` (B12). *Why (recorded in `01abb88`):*
  `json_route` called D2's `_dump`, which D2's refactor deleted; the merge took the Scout's cut
  (`scout/d4-adopt` `ed13d0f`), so D2's `api.py` keeps its own closure. *Pinned by:* `test_routes.py`, its 27
  cases unchanged, and `::test_mcp_routes_answer_only_their_own_host` (D2's guard covers D4's routes).
- **B32. Check's folder is a `TemporaryDirectory`, and its child reports only what is awaited** (§3.3; `eb19663`,
  `e5583e6`; `c8ab00e` and `dcd84af` reorder and document `check.py` and `check_child.py` without a change of
  behaviour). The folder is `tempfile.TemporaryDirectory(prefix="dr-check-", ignore_cleanup_errors=True)`: `mkdtemp`
  underneath, so still 0700, and removed when its `with` ends, after `_end`; CPython 3.12's cleanup resets
  permissions and retries where `rmtree(ignore_errors=True)` gave up. The child writes `ready`, then `built` or
  `failed`, then `example` only when given one; v1–v5's `loaded` and `done` are gone. *Why (recorded):* `eb19663`,
  the Scout's adopted cut; `e5583e6`, the two lines were "written for no reader". *Pinned by:*
  `test_check.py::test_the_temporary_folder_is_removed[word_count, hang]`; and, since `6739e0f`,
  `::test_a_report_line_of_a_phase_not_awaited_is_skipped`: after `e5583e6` the child writes only the lines it is
  asked for, in order, so no Check exercised `_Reports.get`'s phase filter (as-built r3 §7.4, M1); the test feeds it
  `ready`, `loaded`, `built`, `done` and asserts that awaiting `built` returns `built` and awaiting `example` the end.
- **B33. The frame's grant snapshot is one `McpSnapshot`, and both grant lists take one function's notes** (§2.2,
  §7.4, §10.4, B8, A.6; `be131ce`, `58dd18f`, `0100905`). `McpSnapshot` is an interface in `ui/types.ts`, which
  `McpGrant` and `api.ts`'s `McpGrantBody` extend; `snapshotOf(server, target)` takes a target from Canvas's settings
  or from a grant, so `grantSnapshot` is gone; `RESERVED_NAMES` is module-private in `ui/tools.ts`;
  `inheritedNotes(tool, effective)` (v1–v5: `inheritedGrants`) gives each inheriting namespace its note
  (`INHERITED_ROW`, "inherited from X"), which the tool editor and an MCP row both pass to D3's
  `NamespaceChecklist`; an MCP row's tick sends one body, the grant's stored snapshot or, on a first tick, Canvas's.
  The Tools tab's markup is unchanged in 28 states (the Refactorer's DOM probe, which the as-built r3 re-ran), and
  each body's keys keep their order. *Why (recorded in the three commits):* a grant's snapshot had two builders, and
  `mcpRows` built each of its three kinds of row apart; the two components each turned `inheritedGrants`' map into
  notes the same way; a tick's two branches built the same body. *Pinned by:*
  `test_tools_tab.py::test_an_inherited_grant_is_fixed`; and, since `6739e0f`, the two lines no test pinned (as-built
  r3 §7.4): `::test_a_later_tick_keeps_the_granted_settings` (M3: a tick on a granted server whose Canvas settings
  changed keeps the stored environment and version, and the row still offers **Update**) and
  `::test_an_inherited_server_grant_is_fixed` (M4: a server granted to `router` shows `router.archive` ticked, fixed
  and "inherited from router").
- **B34. Test helpers moved into conftests and fixtures; one test renamed** (§7.1, §10.3, B15; `488c580`, `58e9be4`,
  `5363cc8`, `c62d30f`). `tests/tools/conftest.py` holds `source(fixture)` and the `no_process` guard, which
  `test_check.py` and `test_routes.py` (as `no_check`) each defined; `tests/mcp/conftest.py` holds `put_grant(lib,
  alias, granted_in, *, block=None, **fields)`, the grant as `PUT /mcp` writes it; `test_acp.py`'s conversations go
  through a `converse` fixture, and its three crash tests share a function-scoped `crashed` fixture; `test_session.py`
  builds a root-only config and abandons servers through one helper each.
  `test_put_mcp_refuses_a_stdio_grant_without_a_command` is now
  `test_put_mcp_refuses_a_grant_without_its_command_or_url`, named for its URL cases. No test was cut: 128 test
  functions at `f69bc73` and at `3129da9` (as-built r3 §7.4), 131 at `68ebe81` with B32's and B33's three.
- **B35. An MCP row compares only what its grant's block keeps** (§2.2, §4.2, §8.6, B30; `f553260`; as-built r3
  #10). A stdio server whose Canvas entry has `headers`, or since B30 an `auth` that sends one, read as changed
  forever: the block keeps no headers for stdio, so `GET /mcp` answered `headers: []`, `mcpRows` found Canvas's names
  missing, and **Update** rewrote the same block, which D2 stores as no new version. A remote server's arguments and
  environment did the same. Built: `mcpRows` compares, per transport, what the block keeps: the transport, a stdio
  server's command, arguments and environment names, a remote one's URL and header names. Nothing new is stored.
  *Why (recorded in `f553260`):* the bridge forwards neither headers nor `auth` to a stdio server, and the block
  keeps none. *Pinned by:* `tools.test.ts`'s "a granted … is changed" table (a remote server with another header:
  changed; a stdio server with a header, and a remote server with arguments and a variable: not changed), and
  `test_tools_tab.py::test_a_changed_server_offers_update[its settings, a header a stdio block does not keep]`, whose
  second case runs **Update** on a stdio entry with a header and sees the row unchanged after it.
- **B36. The live job's evidence step checks every secret the job holds, and fails closed** (§10.5, B25; `6e07549`,
  `68ebe81`; as-built r3 #11; the job only). The step, now "No dr home holds a secret" (id `secretless`), greps the dr
  homes for each of `OPENAI_API_KEY`, `CLAUDE_CODE_OAUTH_TOKEN` (D1's live tier, merged) and `DEEP_REASONER_TOKEN`
  (the read of deep_reasoner_beta, given to this step alone), skipping an empty value, which `grep -F` would find in
  every line. Only grep's exit 1, every file read and nothing found, lets the upload run: 0 (a match) refuses naming
  the secret, and any other exit (a file or the folder unreadable) refuses too, where before an unreadable file
  counted as clean and a missing folder passed. *Why (recorded in `6e07549` and `68ebe81`):* the step grepped for the
  model key alone while the job holds two more secrets, and with `-q` an unreadable file read as clean. *Pinned by:*
  no test (the job's own machinery); both commits record running the step's script under GitHub's bash flags against a
  scratch `RUNNER_TEMP`, each secret planted, a clean folder, an empty value and a mode-000 file. GitHub has not run
  it yet: no live run has run since it landed.
- **B37. What moved with the merges** (the Gate B section, B11, B16, B22, §7.4, §11.3, §13). D1's golden recordings
  are 20, each with B11's one line: D3's merge brought D1's `unanswered.flat` and `unanswered.native`, whose line
  `01abb88` flipped as D4 had flipped the other eighteen. The live job runs seven tests: D1's
  `test_live_claude_code_on_sonnet_answers_through_acp_and_each_snippet_is_a_cell` came with the merges (`2a15388`);
  all seven passed at `3129da9`, run 37180265916, D4's two among them, both tests unchanged since `f69bc73`. `app.js`
  is 167,267 B at `68ebe81` (169,027 at `aa67f0a`), `editor.js` 348,475 B as before. The size is B16's v6 note: 3,314
  lines of code and 3,807 of tests over D3's head `73c6425`.

---

## 7 · Modules

### 7.1 Files

```text
src/deep_reasoning/tools/                 D4: your own tools
    __init__.py                           docstring only
    check.py                              check_tool, check_env, require_check, ToolCheckFailed, CheckReport (§3)
    check_child.py                        python -m deep_reasoning.tools.check_child (§3.3)
    routes.py                             tool_routes(library, route): POST /tools/{name}/check, GET /mcp,
                                          PUT /mcp/{name} (v6: route is create_app's own, B31)
    texts.py                              D4's backend sentences (§9.1)
src/deep_reasoning/mcp/                   D4: MCP servers
    __init__.py                           docstring only; imports nothing (the shim imports this package)
    shim.py                               the factory_from shim and the guard; standard library at module level (§4.3)
    wire.py                               McpServerSpec, McpServerStatus, specs_for_run, redact,
                                          the seen cache (pydantic and yaml only: the front imports it)
    grants.py                             McpGrantBody, McpGrant, McpSeen, mcp_block, shim_source, is_mcp_tool,
                                          grant_record, header_env_name (the backend's side)
    session.py                            open_session (the worker's side; imports deep_reasoner)
src/deep_reasoning/acp/…                  D1's files: §11.1's changes
src/deep_reasoning/library/api.py         D2's: §11.2's changes
canvas-app/src/…                          D3's project: §7.5
tests/tools/                              test_check.py, test_routes.py, test_live.py, fixtures/ (§10);
                                          v6: conftest.py (source, no_process; B34)
tests/mcp/                                test_wire.py, test_grants.py, test_shim.py, test_session.py, test_acp.py,
                                          test_export.py, test_live.py, servers/ (fake MCP servers, run as scripts),
                                          fixtures/shim_v1.py (v2: the v1 shim, frozen as a Library stores it);
                                          v6: conftest.py (put_grant; B34)
tests/processes.py                        v2: running_after, shared by tests/tools/ and tests/mcp/
tests/canvas_app/test_tools_tab.py        D3's file, D4's tests added (§10.4)
pyproject.toml                            dependencies += "mcp>=1.28,<2"; v2: ruff's extend-exclude += tests/mcp/fixtures
```

`tests/mcp/` is the package `tests.mcp` (`tests/__init__.py` exists, D1), so it never shadows the `mcp` library; the
servers under `tests/mcp/servers/` run as scripts.

### 7.2 `tools/routes.py`: the routes D4 adds to the App backend

`create_app` (D2) appends `*tool_routes(lib)` to its routes, after D3's `*ui_routes()`; D2's guard (same user, `Host`,
JSON) covers them. *(v6, §6.2 B31: `*tool_routes(lib, route)`, built with `create_app`'s own `route` closure.)*

| Method and path | Body | Answer |
|---|---|---|
| `POST /tools/{name}/check` | `{"yaml", "source"?, "example"?}` | `CheckReport`, always 200 |
| `GET /mcp` | | `[McpGrant]`, in `GET /tools` order |
| `PUT /mcp/{name}` | `McpGrantBody`: `{"server", "transport", "command"?, "args"?, "url"?, "env"?, "headers"?, "granted_in", "base_version"}` | `McpGrant`, 201 or 200; 400 (a stdio grant without a command, a remote one without a URL; v3: a body it cannot read, `MCP_BAD_REQUEST`); 409 `conflict` (D2's, carrying the head) or `refused` (`MCP_SERVER_TAKEN`; v3: `MCP_NAME_TAKEN`, the name is a tool of your own); 422 `invalid` |

`PUT /mcp/{name}`: validate the body (v3: D2's `_parse` with `MCP_BAD_REQUEST`); apply the name rules; refuse a name
a tool of your own holds (v3); refuse a server another grant already names; `lib.put_tool(name,
canonical_yaml(mcp_block(name, body)), source=shim_source(), granted_in=body.granted_in,
base_version=body.base_version)`; answer `grant_record(record, read_seen(home, body.server))`. Removing a grant is
D2's `DELETE /tools/{name}`.

### 7.3 The worker, the run log and the encoder (in D1's files)

- `worker/protocol.py`: `Start.mcp_servers: list[McpServerSpec] = []`.
- `worker/runner.py`: `build` calls `open_session` and, when it returns any status, emits `mcp.status` through the
  recorder (§4.4).
- `runlog.py`: `McpStatus` (`kind: "mcp.status"`, `servers: list[McpServerStatus]`) joins the `RunEvent` union.
- `encoder.py`: `McpStatus` → one root `agent_message_chunk` per server whose state is `no_answer`, `failed` or
  `not_enabled`, text `mcp_notice(status) + "\n\n"`, in both modes and on replay; nothing for `bound` or `skipped`.
- `supervisor.py`: `RunHandle.start(…, mcp_servers=…)` passes them in `Start`; the pump, after logging an `McpStatus`
  (the pump sees live events only; a replay does not run it), calls `remember_seen(home, run_id, servers, now)`, and
  logs an `OSError` there rather than failing the run.
- `session.py`: `_start_run` computes the specs (§4.1) in the same `asyncio.to_thread` as the materialize
  (`Session._materialize(run_dir)` returns both).
- `agent.py`: `mcpCapabilities: {"http": True, "sse": True}`.
- `texts.py`: `mcp_no_answer`, `mcp_failed`, `mcp_not_enabled` (§9.2).

### 7.4 The frame (`canvas-app/src/`, D3's project)

```text
shared/protocol.ts       McpTransport, MCP_TRANSPORTS, McpServerInfo; FrameParams.mcp: McpServerInfo[] | null;
                         frameSearch and readFrameParams carry it (JSON; an entry of another shape is dropped)
page/context.ts          readMcpServers(request), mcpServersFromSettings(…)
page/mount.ts            step 2 reads readMcpServers only when tab === "tools"
ui/types.ts              CheckOutcome, ExampleResult, CheckReport, McpSeen, McpGrant; v6: McpSnapshot, which McpGrant
                         and McpGrantBody extend (B33)
ui/api.ts                checkTool, getMcp, putMcp; ToolBody.accept_check_failure; CheckBody, McpGrantBody;
                         LibraryError.check (v2)
ui/tools.ts              pure logic (v6, B33): splitTools, defaultToolName, mcpRows, snapshotOf(server, target),
                         inheritedNotes, toolDraftKey; RESERVED_NAMES is module-private. v1–v5 also exported
                         RESERVED_NAMES and grantSnapshot, and had inheritedGrants for inheritedNotes
ui/editor/python.ts      CodeMirror 6, Python, loaded by import(): createPythonEditor(parent, value, onChange)
ui/components/python.tsx v2: PythonField, the source's field: mounts the editor chunk; on a load failure, D3's CodeField
                         (a textarea). D3's CodeField is unchanged (§6.2 B1)
ui/components/fields.tsx (D3's) ConfirmRow gains an optional confirmTestId (v2, §6.2 B8)
ui/components/ToolEditor.tsx, CheckResult.tsx, McpServerRow.tsx
ui/tabs/tools.tsx        D3's file, extended: banner, risk line, your tools, MCP servers
ui/texts.ts              D4's sentences (§9.3)
vite.config.ts           inlineDynamicImports: false; chunkFileNames "assets/[name].js"; manualChunks: "editor" for
                         CodeMirror, Lezer, their helpers (style-mod, w3c-keyname, crelt) and src/ui/editor/
```

CodeMirror packages, as runtime dependencies: `@codemirror/state`, `@codemirror/view`, `@codemirror/commands`
(`defaultKeymap`, `history`, `indentWithTab`), `@codemirror/language` (`syntaxHighlighting`, `defaultHighlightStyle`,
`indentOnInput`, `bracketMatching`), `@codemirror/lang-python`. Budget: `assets/editor.js` at most 300 KB minified;
`assets/app.js` stays under D3's 250 KB. *(v2, §6.2 B3: built, `editor.js` is 348 KB (118 KB gzip) and `app.js`
169 KB. The editor takes `lang-python`'s bare `pythonLanguage` in a `LanguageSupport`, not `python()`, which would
add autocompletion and 13 KB; it adds `lineNumbers`, `historyKeymap` and a four-space `indentUnit`. No CodeMirror
Python editor fits 300 KB: Python's grammar alone takes it from 281 KB to 349 KB.)* *(v6, §6.2 B37: at `68ebe81`,
`app.js` is 167,267 B, after D3's merges and the refactor; `editor.js` is 348,475 B as before; the page bundle,
`dist/index.js`, is 9,358 B.)* The chunk's name is fixed, so `ui_routes` serves it like any built asset and D3's
`test_the_committed_build_is_complete` adds it to its list.

### 7.5 Canvas's MCP settings in the frame

`readMcpServers(request)` runs in the page (Canvas's realm), beside D3's reads, and only for the Tools tab:

- `GET /api/settings` without `X-Expose-Secrets`, so every secret comes back as `"**********"`
  (`settings_router.py:113–177`, `mcp/config.py:64–74`), and `GET /api/agent-profiles/deep_reasoner`, in parallel.
- `mcpServersFromSettings(agent_settings.mcp_config, profile.mcp_server_refs)`: for each entry, `transport` =
  `stdio` when it has a `command`, `sse` when it has a `url` and `transport` is `"sse"`, otherwise `http` when it has
  a `url` (the bridge's own rule, `acp_agent.py:774–797`), otherwise the entry is skipped; `env` and `headers` are
  the **keys** of those maps (a value is never copied); `forwarded` = `enabled !== false` and (`refs === null` or the
  name is in `refs`); `why_not` = `"disabled"` or `"not_in_profile"`. *(v6, §6.2 B30: `headers` is the keys of
  `headers`, then the names of the headers the entry's `auth` sends, each name once, for every transport.)*
- Either request failing → `null` (D3's tolerance).
- v5: an entry's `auth` is not read, so the header names a remote server's `auth` sends (the bridge forwards them,
  `acp_agent.py:717–736`) are in no grant, and an export does not send them. The Gate B section's third ruling asks
  whether to add them to `headers` here (recommended) or say so in `MCP_EXPORT_NOTE` (as-built r2 #12). *(v6: no
  longer so. Michael ruled (b), and `mcpServersFromSettings` reads `auth` (B30): an HTTP or SSE grant names a
  variable for each of its headers, and an export sends them. The names are added for a stdio entry too, but a stdio
  block keeps no headers (§4.2) and §8.6 does not compare them (B35); the bridge forwards neither headers nor `auth`
  to a stdio server.)*
- As built (v2): the profile's refs are read from the answer's `profile.mcp_server_refs`, and a refs value that is not
  a list counts as `null`. Both shapes were read from the SDK fork at `91430aa`, not run against it (§14 item 12).

The list rides in the frame's URL as the `mcp` parameter (D3 §8.3). It carries commands, arguments and URLs, which a
user may have put a token into; they are already stored unencrypted in Canvas's settings, and the URL stays on the
machine (§14 item 3).

---

## 8 · Algorithms

### 8.1 Classifying a Check

§3.3's child. The one subtle line is the import: `load_tool_factory` wraps every failure of `exec_module` in a
`ValueError` raised `from` the original (`tools/base.py:380–385`) and raises its "defines no" and "not a function"
`ValueError`s without a cause (`:388–406`). So `__cause__` is the classifier: an `ImportError` (and so
`ModuleNotFoundError`) is `import_failed`, which the same runtime would fail in every conversation; any other cause
is `raised` (the module did something at import that may depend on the conversation, such as reading a variable);
no cause is `bad_factory`.

### 8.2 Connecting at once, giving up at once

§4.4. Every `Connection.start()` is called before any wait; then, in turn, each
`ready.wait(max(0, begun + its connect_timeout_s - monotonic()))`, which costs the longest connect timeout, not their
sum (v2: each server's own timeout from one shared start, not one deadline at the largest, §6.2 B5). A server given
up is `abandon()`ed and forgotten: its cleanup runs on its own thread while the run proceeds.

### 8.3 A call's result

```text
result.isError                                       → raise McpToolError("{name}.{tool} failed: " + its text)
result.structuredContent is not None
    outputSchema's properties are exactly {"result"} and structuredContent's keys are {"result"}
                                                     → structuredContent["result"]   (the Python SDK's wrapper, verified)
    otherwise                                        → structuredContent (a dict)
every content block is text                          → their texts joined by "\n" (a str; never parsed as JSON)
otherwise                                            → [block.model_dump(mode="json") for each block] (images, resources)
```

v2 (§6.2 B14): a FastMCP tool whose return annotation is a bare `dict` advertises no `outputSchema` and sends the dict
as JSON text without structured content (measured on 1.30.0), so it arrives here as a `str`; a typed return (a
`TypedDict`, a model) comes back as structured content, a dict. The rule stands: the shim never parses text.

### 8.4 The description

```text
line 1:  MCP server '{server}' ({transport}): call a tool as {name}.<tool>(…) or {name}("<tool name>", **arguments);
         a failed call raises McpToolError.
per tool, in the server's order:
  "  {name}.{ident}({params}) -> {returns}"          ident: the attribute name, or the exact name in quotes
                                                       when it has none: {name}("get-file", …)
  "    {the description's first line, at most 300 characters}"
params:  required properties first, then the others with " = …", each "{prop}: {type}"; type from JSON Schema:
         string str · integer int · number float · boolean bool · array list · object dict · null None ·
         a list of types joined by " | " · absent Any
         v4: the schema true Any · the schema false Never
returns: the type of "result" for the Python SDK's wrapper; dict for another outputSchema; str without one
```

*(v4, §6.2 B26: JSON Schema allows a boolean as a schema, `true` taking any value and `false` none, so a property's
schema need not be a mapping. v1–v3 read every one as a mapping and could not describe such a tool (§14 item 15);
`Any` and `Never` are the nearest names the table has. A tool `odd` with `{"anything": true, "nothing": false}` is
told `odd.odd(anything: Any = …, nothing: Never = …) -> str`.)*

Lines after the first start with two spaces, because deep_reasoner indents only the first line of a description
(`v2/messages.py:221–224`).

### 8.5 Names

- `defaultToolName(server, taken)` (TypeScript): lower-case; every run of characters other than `[a-z0-9]` → `_`;
  trimmed of `_`; a leading digit gets `mcp_` in front; empty → `mcp_server`; a Python keyword, a name in
  `RESERVED_NAMES` or one in `taken` (every tool's name) gets `_2`, `_3`, … until free.
- `header_env_name(server, header)` (Python): `f"{server}_{header}"` upper-cased, every run of characters other than
  `[A-Z0-9]` → `_`, trimmed of `_`: `postgres` + `Authorization` → `POSTGRES_AUTHORIZATION`.

### 8.6 What the frame shows for a server (`mcpRows`)

For each name in Canvas's list or in the grants: `granted` = a grant names it; `state` = `gone` (granted, not in
Canvas's list), `disabled`, `not_in_profile`, or `given`; `changed` = granted and Canvas's settings differ from the
grant's snapshot in what its block keeps (§4.2): the transport, and for stdio the command, args and env names, for
HTTP and SSE the url and header names (v6, §6.2 B35; v1–v5 compared all six for every transport, so a stdio entry
with a header, or an `auth`, read as changed forever); `old_shim` = `!grant.shim_current`.
Rows in Canvas's order, then gone grants by name. With Canvas's list unread (`null`, v2): one row per grant, in
`GET /mcp`'s order, state `given`, `info` null, `changed` false; the row shows the grant's stored snapshot (§6.2 B8).

---

## 9 · Texts (verbatim; tests assert these)

### 9.1 The backend (`deep_reasoning/tools/texts.py`)

As built (v2, §6.2 B9): a sentence with fields is a lower-case function of them that returns an f-string
(`texts.reserved_name(name)`, `texts.child_ended(name, how, phase)`, `texts.mcp_server_taken(server, other)`, …), as
D1 §5.6 does, since the Code Guide forbids `.format()`; the upper-case names below are the sentences' names. `BUILT`,
`MCP_NEEDS_COMMAND` and `MCP_NEEDS_URL` are constants.

| Name | Text |
|---|---|
| `RESERVED_NAME` | `'{name}' is one of deep_reasoner's own names in the REPL (subagent, run_all, FinalAnswer, Var, Func, task); a tool by that name would hide it. Choose another name.` |
| `SYNTAX` | `tool '{name}': tools/{name}.py line {line}: {message}` |
| `UNKNOWN_FACTORY` | `make_tools`' own sentence, copied: `Unknown tool factory {factory!r} for {alias!r}. Known: {known}. A factory of your own is reached with factory_from: <a .py file, relative to this config>.` |
| `NOT_FUNC` | `make_tools`' own sentence, copied: `tool {alias!r}: {factory} in {factory_from} returned {type}, not a Func. A tool factory returns Func(value, description=…) — the registry reads its `.value` (what the REPL binds) and `.description` (what the agent is told).` |
| `FACTORY_RAISED` | `tool '{name}': {factory} raised {type}: {message}` |
| `BUILD_TIMEOUT` | `tool '{name}': building it took longer than {seconds:g} s, so Check stopped it. A tool is built at the start of every conversation; a factory must return quickly.` |
| `READY_TIMEOUT` | `Check could not start deep_reasoner within {seconds:g} s, so it did not build the tool. Try again.` |
| `CHILD_ENDED` | `tool '{name}': the Check process ended ({how}) while {phase}.` (`how`: `exit code 3`, `signal 11`, or the error when the process could not start; `phase`: `starting`, `building the tool`, and v2's `trying it`, §6.2 B7) |
| `EXAMPLE_TIMEOUT` | `TimeoutError: the expression did not finish within {seconds:g} s` |
| `BUILTIN` | `'{factory}' is one of deep_reasoner's own factories. It is built when a conversation starts, with your model and files, so Check does not build it here.` |
| `BUILT` | `builds` (the frame composes the ✓ line) |
| `CHECK_FAILED` | `'{name}' did not pass Check, so it was not saved.` |
| `MCP_VIA_GRANT` | `'{name}' is an MCP server's grant: change it in the MCP servers list.` (400 for an MCP block through `PUT /tools`; v3: also 409 for any `PUT /tools` over a grant's row) |
| `MCP_SERVER_TAKEN` | `MCP server '{server}' is already granted as '{other}'.` |
| `MCP_NEEDS_COMMAND` | `A stdio MCP server needs a command.` |
| `MCP_NEEDS_URL` | `An HTTP or SSE MCP server needs a URL.` |
| `MCP_NAME_TAKEN` | (v3) `A tool named '{name}' exists: choose another name.` (409, `PUT /mcp` over a tool of your own; the frame's `MCP_NAME_TAKEN`, §9.3, is the same sentence) |
| `MCP_BAD_REQUEST` | (v3) `The body must be a JSON object with 'server', 'transport', 'granted_in' and 'base_version', and may have 'command', 'args', 'url', 'env' and 'headers'.` (400, followed by pydantic's reason, as D2's `BAD_REQUEST` is) |

`load_tool_factory`'s own sentences reach the report unchanged ("defines no", "is a …, not a function", "importing …
raised …").

### 9.2 The conversation (D1's `texts.py`)

| Name | Text |
|---|---|
| `mcp_no_answer` | `⚠ MCP server '{server}' did not answer within {seconds:g} s; its tools are not bound in this conversation.` (the spec's) |
| `mcp_failed` | `⚠ MCP server '{server}' could not be started ({detail}); its tools are not bound in this conversation.` |
| `mcp_not_enabled` | `⚠ MCP server '{server}' is granted to {namespaces} in the Library, but this conversation was not given it: enable it in Canvas's MCP settings. Its tools are not bound.` (`namespaces` joined with `, `) |

The shim's own (`shim.py`, in the agent's REPL and prompt; `str.format` templates, constants of the shim, which
imports only the standard library: §14 item 14):

| Name | Text |
|---|---|
| `UNAVAILABLE` | `{name} is not available in this conversation: {reason}.` |
| `NO_ANSWER` | reason: `its MCP server did not answer within {seconds:g} s when the conversation started` |
| `COULD_NOT_START` | reason: `its MCP server could not be started ({detail})` (plain `dr` adds `; not set in the environment: {names}` when any is missing: `MISSING_ENV`, v2, which is also added to `NO_ANSWER`) |
| `NOT_ENABLED` | reason: `its MCP server is not enabled in this app's MCP settings` |
| `NOT_REACHED` | reason: `no namespace this conversation can reach is granted it` |
| `NOT_IN_SESSION` | reason: `it was not connected when this conversation started` |
| `NO_MCP_PACKAGE` | reason: `the mcp package is not installed (pip install mcp)` |
| `CALL_FAILED` | `{name}.{tool} failed: {text}` |
| `CALL_TIMEOUT` | `{name}.{tool} did not answer within {seconds:g} s` |
| `SERVER_STOPPED` | `MCP server '{server}' stopped ({detail}); {name} is unavailable for the rest of this run.` |
| `HANDOFF_REFUSED` | `MCP server '{server}' is granted to {granted}, not to '{dst}', so {name} cannot be handed to a sub-agent there. Grant it to '{dst}' in the Library's Tools tab.` |
| `DESCRIPTION_HEAD` | `MCP server '{server}' ({transport}): call a tool as {name}.<tool>(…) or {name}("<tool name>", **arguments); a failed call raises McpToolError.` |

### 9.3 The Tools tab (`ui/texts.ts`)

| Name | Text |
|---|---|
| `TOOLS_RISK` | `Tools and MCP servers run as you, with your files and network: your tools inside the agent's process, a stdio MCP server as a program started for each conversation that can use it. Check runs your code too. Add only code and servers you trust.` |
| `YOUR_TOOLS` · `NEW_TOOL` · `MCP_SERVERS` | `Your tools` · `+ New tool` · `MCP servers (from Canvas's settings)` |
| `CHECKING` · `SAVING_CHECKING` | `Checking… (building your tool in a separate process)` · `Checking and saving…` |
| `CHECK_BUILT` | `✓ builds ({seconds} s). The agent is told:` |
| `CANNOT_SAVE` | `Fix this before saving: a tool that does not build stops every conversation from starting.` |
| `SAVE_ANYWAY_NOTE` | `Check could not build this tool here, where it has no secrets, no model and only its own folder. If it builds in a conversation, save it anyway; if it does not, no conversation will start until you fix it.` |
| `SAVE_ANYWAY` | `Save anyway` |
| `SAVED_TOOL` | `✓ Saved '{name}' v{version}. New conversations build it; conversations already started keep the version they began with.` |
| `DELETE_TOOL_CONFIRM` | `Delete '{name}'? It is removed from every namespace; its versions stay in the Library's history.` |
| `TRY_LABEL` · `PRINTED` | `Try (an expression Check evaluates with the tool bound)` · `It printed:` |
| `NAME_FIXED` | `how the agent calls it: a Python name, fixed once saved` |
| `MCP_AS` | `as {name}` |
| `MCP_SEEN` | `{count} tools, as the conversation of {date} saw them` |
| `MCP_NOT_SEEN` | `Its tools are listed here after the first conversation that starts it.` |
| `MCP_DISABLED` | `Disabled in Canvas's MCP settings: not started until you enable it there.` |
| `MCP_NOT_IN_PROFILE` | `Not given to the deep_reasoner agent: its profile lists other MCP servers.` |
| `MCP_GONE` · `REMOVE` | `Granted, but no longer in Canvas's MCP settings.` · `Remove` |
| `MCP_CHANGED` · `MCP_SHIM_OLD` · `UPDATE` | `Canvas's settings for this server changed since it was granted; an export still has the old ones.` · `Granted by an older deep-reasoning.` · `Update` |
| `MCP_SETTINGS_UNKNOWN` | `Canvas's MCP settings could not be read; showing the servers already granted.` |
| `MCP_NAME_TAKEN` | `A tool named '{name}' exists: choose another name.` |
| `MCP_EXPORT_NOTE` | `An export keeps each server's command, arguments and URL, never its environment or header values: under dr each is read from an environment variable (env names as they are; a header from SERVER_HEADER).` |
| `NEW_TOOL_SOURCE` | the template in §2.1's mock-up, byte for byte |
| `TOOL_HELP` | `A tool is a factory, make(client, params), that returns Func(value, description=…): the REPL binds value under the tool's name and the agent is told description. params are the block's other keys. Only this file is stored, so it cannot import a file beside it. Call models through client, the conversation's own, never with a key of your own. Read secrets and files when the tool is called, not when it is built: it is built at the start of every conversation and by Check, which has neither. The factory is not told where the config is (deep_reasoner passes no config_path to factory_from tools). A kg tool's saved layers record document paths against the config folder of the conversation that saved them.` |

Test ids (for D4's tests and D5's E12) are in Appendix B.

---

## 10 · Testing

Plain pytest and vitest; each test named for the property it pins; the outside world faked at its boundary (a fake
model, fake MCP servers that are real MCP servers written with `mcp`'s FastMCP, Canvas's host API in vitest); never a
mock of our own code.

### 10.1 Layers

| Layer (spec §4) | Where |
|---|---|
| 1 · deterministic, every push | `tests/tools/`, `tests/mcp/` (no network; fake servers on stdio and loopback); vitest; the browser tests in D3's `canvas-app` job |
| 2 · contracts | Check against `make_tools` on every fixture (§10.2); a stored v1 shim against today's `SESSION` (§10.3); every message `dr-acp` sends still validated by D1's harness, notices included |
| 4 · the real desktop app | D5's E12, with the MCP step §11.4 proposes; the cross-repo forwarding test (§10.6) |
| 5 · Gate B's evidence | the above green in CI at the branch's head, and §10.5's live tier |

### 10.2 E9 in full

**Fixtures** (`tests/tools/fixtures/`, our own code, never deep_reasoner_beta's): `word_count.py` (works),
`not_func.py` (returns a plain function), `misspelled` (`word_count.py` with `factory: mkae`), `import_error.py`
(`import yaml_x`), `hang.py` (`time.sleep(3600)` in the factory), `spawns.py` (starts `sleep 3600` with `subprocess`,
then hangs), `env_at_build.py` (reads `os.environ["D4_TOKEN"]` in the factory), `prints.py` (prints 1 MB while
building), and, v2, `exits.py` (ends its process with code 3 while building) and `calls_model.py` (calls the model
from its factory); the syntax error is inline in `test_check.py`, `def make(`, not a `syntax.py` (§6.2 B14). **Fake
MCP servers** (`tests/mcp/servers/`): `echo_server.py` (FastMCP over stdio: `echo`, `add` → a dict (a `TypedDict`,
v2), `plain` (text only), `picture` (an image), `fail`, `token` → its `ECHO_TOKEN`, `env_names` → its environment's
names, `sleep(s)`, `crash` → `os._exit`, `2nd-opinion` (no attribute name); `--http PORT` serves streamable HTTP and
`--sse PORT` SSE, with `whoami` → the request's `Authorization`; `ECHO_MARKER_DIR` makes it write a file named after
its pid when it starts), `hang_server.py` (never reads its stdin), `crash_server.py` (prints its token to stderr and
exits 1), and the live tier's `catalog_server.py` (§10.5). *(v3 added `odd_server.py`, written with `mcp`'s
low-level `Server`: one tool, `odd`, whose properties are, v4, `ODD_PROPERTIES` (JSON; by default
`{"anything": true, "nothing": false}`, §6.2 B26). v4 adds `loud_server.py`: one tool, `say`, and 1 MB of stderr at
start and 256 KB a call, its `LOUD_TOKEN` on every line (§6.2 B24).)*

| E9 case | Its null | Tests |
|---|---|---|
| your tool: a working tool | — (it builds, is saved, and a conversation's agent calls it) | `test_check.py::test_a_working_tool_builds_and_says_what_the_agent_is_told`, `::test_the_tried_expression_is_evaluated_with_the_tool_bound`; `test_routes.py::test_a_checked_tool_is_saved_with_its_grants`; `tests/mcp/test_acp.py::test_a_tool_saved_through_the_api_is_built_and_called_in_the_next_conversation` |
| a non-`Func` factory | shows only at run time | `test_check.py::test_a_factory_that_returns_no_func_fails_check_in_deep_reasoners_words`; `test_routes.py::test_a_tool_that_cannot_build_is_not_saved[not_func]` |
| a misspelled factory | shows only at run time | `test_check.py::test_a_misspelled_factory_fails_check_naming_what_the_file_defines`; `test_routes.py::…[misspelled]` |
| an import error | shows only at run time | `test_check.py::test_an_import_of_a_missing_module_fails_check_and_cannot_be_saved_anyway`; `test_routes.py::…[import_error]` |
| a hanging factory | a Check past its time limit | `test_check.py::test_a_hanging_factory_is_stopped_at_the_build_limit` (default limits: the report arrives within ready time + 10 s + 1 s, outcome `timeout`), `::test_nothing_a_stopped_tool_started_is_left_running` (`spawns.py`: no `sleep 3600` afterwards) |
| (all five) | a failure that shows only at run time | `test_check.py::test_check_and_make_tools_agree[works, not_func, misspelled, import_error, hang, env_at_build, prints, exits]`: for each, Check's `ok` equals whether `make_tools` builds the same materialized config in a subprocess, and where deep_reasoner words the failure, the same words |
| an MCP server that crashes | blocks the session or takes the worker down | `test_session.py::test_a_server_that_exits_at_start_is_failed_with_its_stderr_redacted`; v3: `::test_a_server_open_session_cannot_bind_fails_alone_and_the_others_bind[…]` (one server `open_session` cannot start or bind fails alone); `test_acp.py::test_a_server_that_crashes_at_start_is_reported_and_the_run_answers`, `::test_a_server_that_crashes_mid_run_fails_the_call_and_the_run_goes_on` (the next cell and the next prompt are answered) |
| an MCP server that hangs | blocks the session | `test_session.py::test_servers_connect_at_once_and_a_silent_one_is_given_up_at_the_deadline` (three servers: decided by the deadline, not three times it); `test_acp.py::test_session_new_does_not_wait_and_the_first_answer_waits_at_most_the_deadline` (a 2 s `connect_timeout_s` in the grant); `test_shim.py::test_a_call_that_never_answers_raises_after_its_timeout` |
| an MCP server not granted to the conversation's namespace | its tools in the REPL | `test_acp.py::test_a_server_granted_elsewhere_is_not_in_this_agents_repl_or_prompt` (granted to `course_advisor`, the conversation in `router`: a cell's `dir()` and the fake model's first request lack it), `::test_a_sub_agent_spawned_into_a_granted_namespace_gets_it`, `::test_a_grant_reaches_a_child_namespace`, `::test_handing_a_server_to_an_ungranted_namespace_is_refused`; `test_session.py::test_a_server_granted_nowhere_is_not_started`, `::test_a_server_granted_only_where_spawning_is_not_allowed_is_not_started` |

### 10.3 Test files

| File | Pins (besides §10.2) |
|---|---|
| `tests/tools/test_check.py` | `test_a_syntax_error_fails_before_any_process_starts`; `test_a_reserved_name_is_invalid[subagent, run_all, FinalAnswer, Var, Func, task]`; `test_llm_is_not_reserved`; `test_a_built_in_factory_is_named_not_built`; `test_an_unknown_built_in_factory_is_refused_in_deep_reasoners_words`; `test_a_factory_raising_can_be_saved_anyway` (`env_at_build.py`: outcome `raised`, its frame in `tools/word_count.py`); `test_check_never_reaches_a_model` (a factory calling `client.chat.completions.create` gets a connection error; a fake model on another port records no request); `test_check_gets_no_secret` (`check_env` of an environment holding `OPENAI_API_KEY` and `OH_SECRET_KEY` has neither); `test_printing_cannot_corrupt_the_report` (`prints.py`); `test_an_example_that_raises_is_reported_and_the_build_stays_ok`; `test_a_slow_example_is_stopped_at_its_limit`; `test_the_temporary_folder_is_removed`; `test_not_func_and_unknown_factory_sentences_equal_make_tools` (tripwire on deep_reasoner's inline text); v2 adds `test_a_name_d2_refuses_is_invalid_in_d2s_words`, `test_an_mcp_grant_is_not_checked_as_a_tool_of_your_own`, `test_a_tool_that_ends_the_process_is_raised_saying_how_it_ended` (`exits.py`), `test_a_check_that_cannot_start_deep_reasoner_in_time_is_unavailable`; `test_check_never_reaches_a_model` uses `calls_model.py`; `test_the_temporary_folder_is_removed` runs `word_count` and `hang`; v3 adds `test_an_example_that_ends_the_process_says_how_and_the_build_stays_ok`, `test_a_check_whose_process_cannot_be_started_is_unavailable` (§6.2 B7); v6 adds `test_a_report_line_of_a_phase_not_awaited_is_skipped` (§6.2 B32), and `tests/tools/conftest.py`'s `no_process` fails a static-stage test that starts a process (B34) |
| `tests/tools/test_routes.py` | Starlette's `TestClient` with `Host: 127.0.0.1:<port>`: `test_check_route_answers_200_with_a_report`; `test_a_grant_only_change_runs_no_check` (a broken tool stored through `Library.put_tool`, then a `PUT` that changes only `granted_in` answers 200); `test_save_anyway_stores_a_raising_tool_only_when_asked`; `test_a_structural_failure_cannot_be_saved_anyway`; `test_an_mcp_block_through_put_tools_is_refused`; `test_put_mcp_writes_the_block_and_the_shim_and_grants`; `test_put_mcp_resent_unchanged_makes_no_tool_version`; `test_a_server_cannot_be_granted_under_two_names`; `test_put_mcp_refuses_a_stdio_grant_without_a_command`; `test_get_mcp_lists_grants_with_their_last_seen_tools`; `test_get_mcp_says_when_a_grant_has_an_old_shim`; `test_mcp_routes_answer_only_their_own_host` (D2's guard); v2 adds `test_a_checked_tool_is_saved_with_its_grants`, `test_put_mcp_refuses_a_name_the_repl_cannot_bind[run_all, not a name, class]`; `test_put_mcp_refuses_a_stdio_grant_without_a_command` runs stdio, http and sse (v6: renamed `test_put_mcp_refuses_a_grant_without_its_command_or_url`, B34); v3 adds `test_a_grant_cannot_replace_a_tool_of_your_own[new, the head's]`, `test_a_tool_of_your_own_cannot_replace_a_grant[new, the head's]` (B20), `test_a_put_mcp_body_it_cannot_read_is_told_the_mcp_bodys_fields[no base_version, a yaml it does not have]` (B21) |
| `tests/mcp/test_wire.py` | `test_forwarded_specs_read_acps_stdio_http_and_sse_shapes`; `test_other_mcp_server_types_are_ignored`; `test_servers_named_reads_mcp_blocks_only`; `test_a_run_gets_only_the_specs_its_blocks_name` (`specs_for_run`: a forwarded server no block names, and its secrets, are not in the result); `test_redact_replaces_every_secret_value`; `test_the_seen_cache_round_trips_and_is_private` (0600, 0700) |
| `tests/mcp/test_grants.py` | `test_mcp_block_for_stdio_http_and_sse`; `test_header_env_name`; `test_is_mcp_tool_needs_the_factory_and_the_marker`; `test_an_exported_and_reimported_grant_is_still_a_grant`; v2 adds `test_mcp_block_needs_a_command_or_a_url`, `test_the_shim_source_starts_with_its_marker_and_version`, `test_grant_record_reads_the_block` |
| `tests/mcp/test_shim.py` | plain mode (no `SESSION`): `test_the_shim_connects_from_its_block_with_env_from_the_environment` (`token` returns the variable's value); `test_results_are_unwrapped_dicts_text_or_blocks` (§8.3's table); `test_a_failed_call_raises_mcp_tool_error_with_the_servers_text`; `test_positional_arguments_follow_the_described_order`; `test_tools_without_an_identifier_are_called_by_their_exact_name`; `test_the_description_is_what_8_4_says` (exact text); `test_a_server_survives_fork` (`copy.deepcopy` returns the same object; no warning); `test_calls_from_many_threads_and_under_nest_asyncio`; `test_without_the_mcp_package_the_factory_returns_a_stand_in` (`mcp` hidden with `monkeypatch.setitem(sys.modules, "mcp", None)`); `test_the_shim_imports_only_the_standard_library_at_module_level` (its AST); `test_a_stored_v1_shim_works_with_todays_session` (a frozen copy of v1 in `fixtures/`); the guard: `test_the_guard_ends_its_server_when_its_parent_is_killed` (a parent process started for the test, `SIGKILL`ed; the server's pid is gone within 1.5 s); `test_the_guard_passes_the_exit_code`; HTTP: `test_an_http_server_is_reached_with_its_headers` (`whoami`); v2 adds `test_a_stand_in_is_plain_to_deep_reasoners_seams`, `test_a_server_it_cannot_reach_becomes_a_stand_in_saying_why[crashes, hangs]`, `test_a_server_that_dies_fails_the_call_and_every_later_one_at_once`, `test_a_hand_off_outside_the_grant_is_refused`; the HTTP test runs http and sse; v4 adds `test_properties_that_take_any_value_or_none_are_described_as_any_and_never` (B26), and `test_a_stored_v1_shim_works_with_todays_session` now runs a stored text older than today's (B23) |
| `tests/mcp/test_session.py` | `test_only_granted_and_reachable_servers_are_started`; `test_grant_sets_follow_deep_reasoners_resolution` (root, `a`, `a.b`); `test_a_granted_server_not_forwarded_is_not_enabled`; `test_statuses_carry_what_the_agent_is_told`; `test_a_server_given_up_is_ended_within_three_seconds`; v2 adds `test_without_mcp_blocks_the_session_is_empty`; v3 adds `test_a_server_open_session_cannot_bind_fails_alone_and_the_others_bind[its log cannot be opened, its block has no number, it cannot be told]` and `test_a_namespace_registry_deep_reasoner_refuses_fails_the_build_as_it_would_anyway` (B19); `test_a_server_that_exits_at_start_is_failed_with_its_stderr_redacted` runs `whole` and `split` and reads the server's log (B18); v4 adds `test_a_tool_whose_properties_take_any_value_or_none_is_bound_and_told_so` (B26) and `test_a_server_that_prints_more_than_a_pipe_holds_answers_and_its_log_is_redacted` (B24), and the case `it cannot be told` gives `odd_server.py` a property schema that is a string (B26) |
| `tests/mcp/test_acp.py` | D1's harness (`dr_acp(None, home)`, `FakeOpenAI`, `ShimConnection`), the Library at `home`, `open_session(cwd, mcp_servers=[…])`: `test_dr_acp_advertises_http_and_sse`; `test_a_granted_server_is_bound_and_a_cell_calls_it`; `test_a_forwarded_server_no_grant_names_is_never_started` (the fake server writes a marker file when it starts; there is none); `test_server_secrets_never_reach_the_run_log_or_the_transcript` (`crash_server.py` prints its token; the notice says `[redacted]`); `test_the_notice_replays_on_load`; `test_the_seen_cache_is_written_for_bound_servers`; `test_no_stdio_server_outlives_a_root_stop` (a cell in `while True: pass`; root Stop; within 2 s no fake server is running); `test_no_stdio_server_outlives_a_closed_session`; the E9 rows of §10.2; v3: `test_server_secrets_never_reach_the_run_log_or_the_transcript` also reads the server's own log (B18); v6: each conversation goes through a `converse` fixture, and grants are written with `tests/mcp/conftest.py`'s `put_grant` (B34) |
| `tests/mcp/test_export.py` | `test_an_exported_grant_runs_under_dr` (`dr-library export`, then `dr <dir>/main.yaml` with `FakeOpenAI` scripted to call `echo.echo("hi")` and `ECHO_TOKEN` in the environment: exit 0, the cell's output `hi`) |

**D1's files** gain: `tests/acp/harness.py`: `DrAcp.open_session(cwd, mcp_servers=())`; `test_agent.py`'s
capability assertion; golden recordings re-recorded once if they hold the `initialize` response (D1's one command).
*(v2, §6.2 B11: each recording's `initialize` line was changed by hand, nothing else; the capability test is now
`test_initialize_advertises_load_close_and_http_and_sse_mcp`; `tests/acp/test_encoder.py` gains
`test_each_mcp_server_not_bound_is_a_notice_on_the_root[native, flat, replay]`.)*

### 10.4 The Tools tab (D3's harness: `tests/canvas_app/`, Playwright, marker `browser`; and vitest)

D3's `test_the_tools_tab_always_shows_the_safety_notice_with_the_cap` and `test_the_tools_tab_lists_tools_with_their_grants`
stay green. D4 adds to `test_tools_tab.py`: `test_the_risk_line_is_under_the_safety_banner`;
`test_a_new_tool_is_written_checked_and_saved_with_its_grants` (asserts the stored row, the source byte for byte, and
`granted_in`); `test_check_shows_what_the_agent_is_told_and_the_tried_value`;
`test_a_tool_that_cannot_build_shows_why_and_cannot_be_saved[not_func, misspelled, import_error]`;
`test_a_hanging_factory_shows_the_limit`; `test_a_raising_factory_offers_save_anyway`;
`test_a_grant_tick_on_a_saved_tool_saves_without_unsaved_code`; `test_an_inherited_grant_is_fixed`;
`test_the_editor_keeps_python_indentation` (Tab, Enter after `:`); `test_canvas_mcp_servers_are_listed_and_granted_per_namespace`
(the frame opened with `mcp=`); `test_a_disabled_server_says_so_and_can_still_be_granted`;
`test_a_grant_gone_from_canvas_offers_remove`; `test_a_changed_server_offers_update`;
`test_the_last_seen_tools_are_shown` (a seen file written first); `test_without_canvas_settings_only_grants_are_shown`.
*(v6: and `test_an_inherited_server_grant_is_fixed`, `test_a_later_tick_keeps_the_granted_settings` (§6.2 B33);
`test_a_changed_server_offers_update` runs `[its settings, a header a stdio block does not keep]` (B35). D4's
browser cases are 20.)*
`library_home`'s fixture gains a tool whose factory raises (D3 §8.3 allows it). *(v2, §6.2 B13: it does not; E8 runs
real conversations from that Library and `make_tools` builds every block, so D4's tests make the raising tool inside
`test_a_raising_factory_offers_save_anyway`.)* vitest also gains, v2, `mount.test.ts`'s "reads Canvas's MCP servers
for the Tools tab only", and `tests/library/test_ui.py::test_the_committed_build_is_complete` requires the editor
chunk.

vitest: `protocol.test.ts` (the `mcp` parameter round-trips; bad JSON → `null`); `context.test.ts`
(`mcpServersFromSettings`: stdio, http, sse and skipped entries; `disabled` and `not_in_profile`; no value of `env` or
`headers` in the output, `"**********"` never; a failing request → `null`); `tools.test.ts` (`defaultToolName`'s
table; `mcpRows`' states; `snapshotOf` and `changed`; `inheritedGrants` from an `Effective` list); `api.test.ts`
(`checkTool`, `getMcp`, `putMcp`: bodies with exactly the backend's field names; a `422 check_failed` → `LibraryError`
carrying the report). *(v6: `context.test.ts` also has B30's "adds the header names a remote server's auth sends",
seven cases; `tools.test.ts`'s `changed` table compares per transport (B35), and `inheritedNotes` replaces
`inheritedGrants` (B33).)*

### 10.5 Live tier (Gate B; `@pytest.mark.live`, skipped without `OPENAI_API_KEY`; gpt-6-luna)

Spec §4 layer 5: "D4: a tool written in the Library, and an MCP server, each used by an agent". Each test sets up a
Library at a temporary home with the starter profile (gpt-6-luna on OpenAI, D2 decision M), writes through the HTTP
API (`create_app`, `TestClient`), so the gate and the real Check run, then drives a real `dr-acp --home` over stdio
with D1's harness. The facts asked for exist nowhere but in the tool, so the answer can only come from it. *(v4,
§6.2 B27: and the task names the tool, or the server, in which they are. Asked bare, gpt-6-luna twice answered from
nothing; so the tier pins that a tool or server is bound into a real run and works when the agent calls it, not that
the model chooses to call it.)*

1. `tests/tools/test_live.py::test_live_a_tool_written_in_the_library_is_used_by_the_agent`: `PUT /tools/course_credits`
   (a factory whose `course_credits(code: str) -> int` knows `ZQ-417` is 7 credits), granted to `root`; the response
   is 201 and a Check report on the same body says `built`; prompt "Use course_credits to find how many credits
   course ZQ-417 is." (v4; v1–v3: "How many credits is course ZQ-417?") → the outcome is `answered` and the answer
   contains `7`; the run log holds a cell whose code calls `course_credits(` and whose output contains `7`.
2. `tests/mcp/test_live.py::test_live_an_mcp_server_granted_to_the_namespace_is_used_by_the_agent`: a FastMCP stdio
   server of ours (`catalog_server.py`: `prerequisites(course: str) -> list[str]`, `ZQ-417` → `["ZQ-101"]`, refusing
   to answer without its `CATALOG_TOKEN`); `PUT /mcp/catalog` granted to `root`; `session/new` forwards it as the
   bridge would (`McpServerStdio` with `env: [{CATALOG_TOKEN, …}]`); prompt "Use the catalog server to find what a
   student must finish before ZQ-417." (v4, naming the server, not its method; v1–v3: "What must a student finish
   before ZQ-417?") → the outcome is `answered` and the answer contains `ZQ-101`; the run log's `mcp.status` says
   `bound`, a cell calls `catalog.prerequisites(`, and the token appears nowhere in the run log or the updates.
   v4 (§6.2 B25): the test writes the ACP transcript to `<home>/transcript.jsonl`, and a prompt that does not end
   `answered` fails with the run's `mcp.status`, `agent.end` and `prompt.end` events as its message.

Cents per run, in D1's on-demand `live.yml` with the same secret. *(v2: both passed at `965f318`, run 37106223637,
with D1's three and D2's one, 6 of 6 in 81 s. v3: at `aa67f0a`, run 37145903109, the MCP test failed once, its
prompt `exhausted`; the tool test passed; §14 item 8's re-run is pending, Gate B section. v4: that run's re-run
failed too, its prompt `failed`; the tool test failed twice at `7eb7812`; both passed twice at `f69bc73`, runs
37157799600 and 37157801762, 6 of 6 each. The Gate B section has the whole record. Since `9255778` a failed run
keeps every test's dr home as the artifact `live-dr-homes`, after a check that none holds the model key, §6.2 B25.)*
*(v6: the check now covers every secret the job holds (`OPENAI_API_KEY`, `CLAUDE_CODE_OAUTH_TOKEN`,
`DEEP_REASONER_TOKEN`), skips an empty one, and fails closed: only grep's exit 1 uploads, §6.2 B36. Both tests
passed at `3129da9`, run 37180265916, 7 of 7 with D1's Claude Code test, B37.)*

### 10.6 Across the repositories (proposed; D5's `crossrepo` harness; not built in D4, §6.2 B17)

`tests/crossrepo/test_mcp_forwarding.py`: the agent-server from the SDK fork's pinned commit; `PATCH
/api/settings/mcp/echo` with `echo_server.py` as a stdio server and one secret in its `env`; the `deep_reasoner`
profile; the Library granting `echo` to `root`; a conversation with `FakeOpenAI` scripted to call `echo.token()` →
the cell's output is the secret (it travelled through Canvas's settings, the bridge and `dr-acp`), and `mcp.status`
says `bound`. This is the one place the forwarding shape is run rather than read (header, "Not verified").

---

## 11 · Contracts with other work

These are findings for the Conductor; none is settled sideways.

### 11.1 D1

D4 makes these changes in D1's files (§7.3), about 90 lines with the sentences (v2: 101 added, `cf131e5`):

- `Start.mcp_servers` (D1 §4.8 named it) and `AGENT_CAPABILITIES.mcpCapabilities = {"http": True, "sse": True}` (D1 §4.8
  anticipated the flip).
- **A new RunEvent, `mcp.status`**, in `runlog.py`, emitted by the worker before `build_reasoner`, encoded as root
  notices. D1 §4.4's event table and §5.6's sentences should list it and them when D1 next revises; E4's schema check
  covers the notices as it covers the fresh-run notice.
- `Worker.build` calls `open_session` between `load_dr_config` and `build_reasoner`; a failure inside it is caught per
  server and never fails the build. *(v2: a server's failure is caught; an error in deep_reasoner's own namespace
  resolution, which `open_session` calls first, fails the build, as it would fail `build_reasoner` next.)* *(v3,
  §6.2 B19: so it is now for every error about one server, inside `open_session` too: its log not opening, its
  block not read, its binding not described. That server is `failed` and the run goes on. An error in
  deep_reasoner's own namespace resolution still fails the build, as D1's `build_failed`; in a run built from the
  Library, D2's invariants leave only errors that `build_reasoner` raises next anyway. One case differs (§14 item
  16): a hand-written config with a broken namespace outside the entry's chain fails here, when the run has an MCP
  block, where `build_reasoner` alone would not.)*
- The pump writes the seen cache (§4.7) for live, not replayed, `mcp.status` events.
- The test harness's `open_session` takes `mcp_servers`.
- **No change to D1's process handling**: stdio servers end through their guards (§4.6), so `RunHandle.kill` and the
  worker's `killpg(0)` stay as they are.

**What D4 adds to D1's surface, as built (`cf131e5`; v2).** D1's design (v3, `c8d7fbb`) names no such event: its
§4.4 lists the RunEvents and its §5.6 the sentences, and neither has these. This is the change D4 makes to D1's
surface, written so that D1's next revision can take it in as it stands.

- **The event** (D1 §4.4, "Sent by the worker"), in `acp/runlog.py`, joining the `RunEvent` union:

  ```python
  class McpStatus(_Ev):
      """D4: how each MCP server a run's config names was bound, before build_reasoner."""

      kind: Literal["mcp.status"] = "mcp.status"
      servers: list[McpServerStatus]  # deep_reasoning.mcp.wire (Appendix A.2)
  ```

  The worker emits it through its recorder at most once per run: in the first prompt's build, after `load_dr_config`
  and before `build_reasoner`, and only when the run's config has an MCP block. In the run log it follows that
  prompt's `prompt.start` and precedes the root's `agent.start`. The front logs it as it logs every RunEvent; after
  logging it, the pump writes the seen cache (§4.7). A replay re-encodes it and writes nothing.
- **Its encoding** (a row for D1 §5.2; §5.3's "as in §5.2" covers flat mode): `mcp.status` → for each server whose
  `state` is `no_answer`, `failed` or `not_enabled`, in the event's order, `root` → `agent_message_chunk`
  `{"content": {"type": "text", "text": notice + "\n\n"}}` with no `_meta`, the fresh-run notice's form, so a client
  that reads `_meta` tells it from an answer; nothing for `bound` or `skipped`. The same in native and flat mode and
  on `session/load`. E4's schema check covers it as it covers every message `dr-acp` sends.
- **Its three sentences** (D1 §5.6), in `acp/texts.py` as functions of their fields
  (`texts.mcp_no_answer(server, seconds)`, `texts.mcp_failed(server, detail)`,
  `texts.mcp_not_enabled(server, namespaces)`), one of them picked by `texts.mcp_notice(status)`:

  | Name | Text |
  |---|---|
  | `MCP_NO_ANSWER` | `⚠ MCP server '{server}' did not answer within {seconds:g} s; its tools are not bound in this conversation.` (`seconds`: the status's, the server's connect timeout) |
  | `MCP_FAILED` | `⚠ MCP server '{server}' could not be started ({detail}); its tools are not bound in this conversation.` (`detail`: the failure and the tail of what the server printed, its secrets redacted, §4.4; v3: or the `"Type: message"` of an error `open_session` met about that server, redacted, §6.2 B19) |
  | `MCP_NOT_ENABLED` | `⚠ MCP server '{server}' is granted to {namespaces} in the Library, but this conversation was not given it: enable it in Canvas's MCP settings. Its tools are not bound.` (`namespaces`: the status's `granted`, joined with `, `; §14 item 10) |

- **Around it** (D1 §4.8, §5.1, §7): `Start.mcp_servers: list[McpServerSpec] = []`, filled by `Session._materialize`
  through `specs_for_run`; `RunHandle.start(…, mcp_servers=…)`; `initialize` advertises
  `mcpCapabilities: {"http": true, "sse": true}`, which changes each golden recording's `initialize` line and renames D1's capability
  test (§6.2 B11); the harness's `DrAcp.open_session(cwd, mcp_servers=())`. D1 §4.8's "≈30 lines" came to 101 in D1's
  source files.
- *Pinned by:*
  `tests/acp/test_encoder.py::test_each_mcp_server_not_bound_is_a_notice_on_the_root[native, flat, replay]`;
  `tests/mcp/test_acp.py::test_a_server_that_crashes_at_start_is_reported_and_the_run_answers` (the notice, then the
  answer), `::test_the_notice_replays_on_load`,
  `::test_session_new_does_not_wait_and_the_first_answer_waits_at_most_the_deadline`,
  `::test_the_seen_cache_is_written_for_bound_servers`, `::test_dr_acp_advertises_http_and_sse`.

### 11.2 D2

- **The gate**: `_ToolBody` gains `accept_check_failure: bool = False`; `put_tool` calls `require_check` first (§3.5).
  Old clients are unaffected (the field is optional); `Library.put_tool` and import are not gated. *(v3: D2's
  `PUT /tools/{name}` over a grant's row now answers `409 refused` with `MCP_VIA_GRANT`, at any `base_version`,
  before anything is checked or written; §6.2 B20.)*
- **`_parse` takes the sentence to lead with** (v3, `4a86581`): `_parse(model, body, sentence=texts.BAD_REQUEST)`,
  so `PUT /mcp` leads its 400 with `MCP_BAD_REQUEST` through D2's one error mapping (§6.2 B21). D2's own callers are
  unchanged. The import of a private name stays for the Refactorer (§6.2 B12).
- **Routes**: `create_app` appends `*tool_routes(lib)`. For that, D2's `route()` helper, today a closure inside
  `create_app`, becomes a module-level `json_route(path, method, handler)` with no change in behaviour, so D4's
  routes are built the same way (the alternative is an eight-line copy in `tools/routes.py`). *(v2: built so,
  `70dd540`; `tools/routes.py` also imports D2's private `_parse`, and `create_app` imports D4's modules inside
  itself, to break an import cycle: §6.2 B12.)* *(v6, §6.2 B31: no longer so. D2's refactor deleted what
  `json_route` called, and the merge (`01abb88`) took the third way: D2's `route` stays a closure inside
  `create_app`, which passes it, `*tool_routes(lib, route)`. D4's edit to `api.py` is +17 −5.)*
- **No schema change, no migration**: MCP grants are tool rows (decision D), D2's recommendation.
- **Proposed, not required**: `Library.materialize(…, only_granted: bool = False)`, with `LibraryCatalog` passing
  `True`, so a run's `main.yaml` holds only tools some namespace grants. Today an ungranted tool is still built in
  every conversation (`make_tools` builds every block), so a tool imported broken and granted nowhere still stops every
  conversation; an export keeps every tool. D4 does not depend on it: an ungranted MCP grant is never connected
  (§4.4), and the gate keeps the panel from storing a broken tool. *(v2: not built, §6.2 B17. It is also why D3's
  shared browser Library holds no raising tool, §6.2 B13.)*
- D2 §6.5 said Check "can materialize the Library into a temporary directory"; D4 materializes only the tool being
  checked (one tool's failures, no others').

### 11.3 D3

All within D3 §8.3: `tabs/tools.tsx` extended, the banner kept at the top; `api.ts` gains `checkTool` (D2 §6.5's
route) and `getMcp`, `putMcp`; `ToolBody` gains `accept_check_failure`; `FrameParams.mcp` with its read in
`page/context.ts`, through `host.agentServer.request`, `null` on failure; a `PythonField` of D4's own loads
CodeMirror as the `editor` chunk, with `inlineDynamicImports` removed as D3 foresaw (v2: v1 said D3's `CodeField`
would, for `language: "python"`, which D3's decomposition cards use; §6.2 B1); tests beside D3's, with the same
fixtures. Two additions D3 should know: `page/mount.ts` step 2 reads `readMcpServers` for the Tools tab only (one
line), and D3's `ConfirmRow` gains an optional `confirmTestId` (v2, §6.2 B8). The frame UI stays under 250 KB without
the editor chunk (§7.4; v2: `app.js` is 169 KB; v6: 167,267 B, §6.2 B37).

**Branch base.** D4's code extends D3's files, so `v1-custom-tools` should be cut from `v1-decompositions-panel` once
D3 is far enough, as D2's was cut from D1's (D2 §9 item 4). *(v2: so it was; D4's code is stacked on D3's `5effe26`.)*

### 11.4 D5

None of this section is built in D4 (§6.2 B17). What it would use exists: `echo_server.py`, with its `env_names`
tool.

- **E10 with MCP servers bound** (D5 §1.2's final part): D4 provides `echo_server.py` and the grant to run E10 with a
  stdio server bound and a call made. Expected to hold unchanged: the provider key and the agent-server's secrets are
  not in the worker's environment, a cell's `os.environ` or `/proc/self/environ`, the transcript or the run log; the
  server's own environment (its `env_names` tool) holds only its configured variables and `mcp`'s six. The MCP
  server's secrets travel in the control pipe, never in an environment, and are redacted from failure details.
- **D5 §2.1's first row** ("not in … any process the worker starts") needs one exception stated: an MCP server whose
  Canvas settings give it a provider key gets it, by the user's configuration. D5 §2.2's bullet on tools and MCP
  servers can point at §5 here.
- **The profile**: D4 relies on D5 creating the `deep_reasoner` profile with `mcp_server_refs: null` (D5 §4.5.1) and
  reads `mcp_server_refs` to say when a server is left out.
- **E12**: proposed, a final-part step: add an MCP server through Canvas's settings API, tick it for the conversation's
  namespace in the Tools tab (Appendix B's ids), and see the next conversation's cell call it (§10.6's server).
- **After an upgrade** (§14 item 4): optionally, `dr-app setup` could run a check of every stored tool and print the
  failures in the startup log.

### 11.5 C2, S2, S1, C1, C3

None.

---

## 12 · What D4 relies on

| # | Behaviour relied on | Their code |
|---|---|---|
| R1 | `make_tools` builds every block of `cfg.tools` once per run; a `factory_from` block: `load_tool_factory(alias, factory, factory_from, cfg.config_path)`, then `build(client, params)` with the block minus `factory` and `factory_from`, then the `Func` check with the inline sentence | deep_reasoner `v2/cli.py:125–180, 348` |
| R2 | `load_tool_factory` resolves against `config_path`, wraps an import failure `from` its cause, raises "defines no" and "not a function" without one, and caches modules by path | `tools/base.py:316–407` |
| R3 | A namespace's tools are resolved as an ordered union down the dotted chain; an agent binds them through `cross_namespace`, which calls a tool's `__cross_namespace__`; a missing registry entry raises | `namespaces.py:272–320, 345–392, 645–654` |
| R4 | `check_spawn(registry, src, dst)` is deep_reasoner's own spawn rule | `namespaces.py:672–685` |
| R5 | Namespace bindings override the framework's names | `v2/agent.py:647, 671–676` |
| R6 | `func(name, value, description).describe()` is what the agent is told | `v2/messages.py:184–189, 216–224` |
| R7 | `fork` deep-copies the REPL, degrading per binding | `repls/backends.py:105–140` |
| R8 | A client on loopback needs no key | `config.py:249–265` |
| M1 | `stdio_client` starts the server in a new session, merges six variables into its environment, closes stdin then ends the process tree on exit | `mcp` 1.28.1 `client/stdio/__init__.py:28–66, 180–260`; the same lines in 1.30.0 (v2) |
| M2 | `ClientSession.call_tool(…, read_timeout_seconds=…)`, `list_tools(cursor=…)` (v2: the shim passes `params=PaginatedRequestParams(cursor=…)`), `streamable_http_client(url, http_client=…)`, `sse_client(url, headers=…)` | 1.28.1: `client/session.py:386, 525`; `client/streamable_http.py:601`; `client/sse.py:30`. 1.30.0 (v2): `client/session.py:386, 524–532`; `client/streamable_http.py:619`; `client/sse.py:35` |
| M3 | (v2) A dead connection fails a request with `McpError` code -32000 ("Connection closed"); a read timeout is `McpError` code 408; a FastMCP tool returning a bare `dict` sends JSON text and no structured content | 1.30.0: `types.py:182`; `shared/session.py:296, 451`; measured (§6.2 B14) |
| B1 | OpenHands forwards every enabled server of the profile's filtered `mcp_config` as ACP `mcpServers` at `session/new` and `session/load`, stdio always, HTTP and SSE when advertised, secrets in plain text | SDK fork `acp_agent.py:739–821, 3105–3120`; `profiles/resolver.py:160–168` |
| B2 | `GET /api/settings` without `X-Expose-Secrets` redacts every secret value | `settings_router.py:113–177`; `mcp/config.py:64–74` |
| B3 | App-backend requests have no read timeout through the bridge | `bridge.py:467–472`; `docker_runtime/proxy.py:96–97` |
| D1-1 | `Start`, `Worker.build`, the pump, `Session.mcp_servers`, the harness | D1 at `90044f0` |
| D2-1 | Tool rows, `granted_in` as the exact set, `shapes.validate_tool`, unchanged-is-not-a-save, `materialize`'s `tools/<name>.py`, `create_app`'s guard and error handler | D2 at `90044f0` |
| D3-1 | §8.3's contract | D3 `ab6f2ec` |

---

## 13 · Size

| Part | Code | Tests |
|---|---|---|
| Check: `check.py` 150, `check_child.py` 90, `texts.py` 60 | 300 | 330 (`test_check.py`, fixtures) |
| Routes and the gate: `routes.py` 110, D2's changes 15 | 125 | 200 (`test_routes.py`) |
| MCP: `shim.py` 270 (guard included), `wire.py` 90, `grants.py` 80, `session.py` 100 | 540 | 650 (`test_wire`, `test_grants`, `test_shim`, `test_session`, fake servers 90) |
| D1's changes (event, encoding, sentences, pump, front, capabilities) | 90 | 330 (`tests/mcp/test_acp.py`, harness) |
| Export and live tier | — | 200 |
| The frame: protocol and context 70, types and api 80, `tools.ts` 90, `tabs/tools.tsx` 180, `ToolEditor` 200, `CheckResult` 70, `McpServerRow` 120, editor chunk 60, texts 50 | 920 | 480 (vitest 200; browser 280) |
| **Total** | **≈1.98k** | **≈2.19k** |

About 4.2k lines with tests, about 14 h at Gate C at the workspace's rate, against the spec's ≈1.0k and ≈3 h. The
differences: unit and browser tests (the spec's figure was nearly all code); the gate and its two save paths; the
guard and the concurrent session start, which the probes showed are needed; the MCP side of the Tools tab, which the
spec costed at 40 lines; the event and notices in `dr-acp`. **If the Conductor wants a smaller D4**, two parts cut
cleanly, each with what is lost: the seen cache (≈60 lines and its tests; the Tools tab then shows no server tools)
and CodeMirror (≈60 lines and a dependency; a textarea with Tab handling instead).

*(v2: built at 3,311 lines of code and 3,511 of tests, about 6.8k and 23 h; v3: 3,397 and 3,686, about 7.1k and 24 h;
v4: 3,399 and 3,778, about 7.2k and 24 h; v6: 3,314 and 3,807 at `68ebe81`, about 7.1k and 24 h. §6.2 B16 gives
this table with the built figures, and its v6 note the parts at `68ebe81`. As built, CodeMirror is
`ui/editor/python.ts` (74 lines) and `ui/components/python.tsx` (67), five packages and the 348 KB chunk, §6.2 B3.)*

---

## 14 · Open items, and what I was unsure about

1. **The forwarding path was read, not run** (header): `_mcp_config_to_acp_servers`, the ACP 0.12.1 model shapes and
   the settings JSON. §10.6's test runs it; until then `forwarded_specs` accepts both a missing and a `"stdio"` `type`.
   *(v2: still read, not run; §10.6 was not built, §6.2 B17.)*
2. **E9's "not granted to the conversation's namespace"** is designed per agent (decision G, §6.1 item 5). If Michael
   meant "only the conversation's own namespace, and never a sub-agent's", that is a narrower rule deep_reasoner does
   not have, and it would need the stand-in in every agent of a non-granted namespace even when spawned into a granted
   one.
3. **The frame's URL carries MCP commands, arguments and URLs.** They are not secrets by Canvas's model, but a user can
   put a token in an argument; the agent-server's or the backend's access log may then hold it. The alternative is to
   send the list by `postMessage` after the frame loads, which D3 rejected for static data (D3 decision E); D4 follows
   D3's §8.3. *(v3: Michael ruled on 2026-10-03, as relayed by the Conductor, that a server's command-line arguments
   are not secrets, as designed: keys go in `env`. So arguments stay unredacted in the URL, the Library, exports and a
   server's own log, §6.2 B18. The ruling is not yet among the spec's dated notes.)*
4. **A tool broken by an upgrade or an import** is not found until it is checked or a conversation fails to start
   (§3.5). D2's `only_granted` (§11.2) narrows the blast radius; a check of every tool after an upgrade (§11.4) would
   find it at launch.
5. **Check's false failures** (a tool that needs a secret, the conversation's folder or the network at build time)
   are handled by "Save anyway", not reproduced. A per-tool "build in this folder" option was considered and left out.
6. **OAuth-protected remote servers**: OpenHands forwards only header-compatible credentials (`acp_agent.py:717–736`);
   a server needing OAuth fails at connect and is reported. Not designed around. *(v5: header-compatible `auth` is
   forwarded in a conversation but not exported; the Gate B section's third ruling.)* *(v6: no longer so. Since B30
   an HTTP or SSE grant names a variable for each header its `auth` sends, so an export sends them under `dr`. A
   stdio entry's `auth` is named by the frame and kept by no block, and the bridge does not forward it either (B35).
   OAuth stays unexported, and unforwarded.)*
7. **Remote REPLs** (`repl: daytona`): how deep_reasoner carries a `Func`'s value into a remote REPL decides whether
   an MCP server can be used there; untested.
8. **The live tier depends on the model choosing the tool**; the facts are unguessable and the tool is described,
   but a model may still answer without calling it. A failure there is re-run once before it is read as a regression.
   *(v3: at `aa67f0a` the MCP test's prompt ended `exhausted` once, live run 37145903109; its re-run is pending, and
   the Gate B section says so.)* *(v4: now only partly true. The re-run failed too, its prompt `failed`, which is not
   the model declining a tool; and at `7eb7812` the tool test's prompt ended `exhausted` twice, gpt-6-luna answering
   "4 credits." without a cell. Since `933ac08` and `f69bc73` the task names the tool or the server (§6.2 B27), so
   the model is told which to use; it must still call it correctly, and a run can still fail for the model's own
   reasons. What the tier no longer shows is the model reaching unprompted for a tool it is merely told about. The
   rule stands, and since §6.2 B25 a failure's evidence is kept, so the next one can be read rather than re-run
   blind.)*
9. **The Code Guide** says never to ship un-run fenced Python in a `.md`; this design, like D1's to D3's, carries
   signatures as fenced code, as the brief asks. A tension in the pages, not a choice made here.
10. **The "not enabled" notice names every namespace whose resolved tools include the server** (v2, carried from the
    build). `McpServerStatus.granted` is deep_reasoner's resolution (§4.4), so a grant to `root` makes
    `MCP_NOT_ENABLED` list every namespace in the Library. The namespaces that grant it directly (the Library's
    `granted_in`, which each materialized namespace file's own `tools` carries) would read better. Not changed by the
    build; a small change in `open_session`, for Michael or D1's next revision to choose.
11. **"Time to connect" can be overstated** (v2, carried from the build). A bound server's `seconds` is taken when its
    own wait returns, and the waits run in turn (§6.2 B5), so a server that answered while an earlier one was still
    awaited is recorded with the later time. It is in the run log only; the Tools tab shows no time.
12. **Canvas's settings shape was read, not run** (v2, carried from the build): `agent_settings.mcp_config` from
    `GET /api/settings` and `profile.mcp_server_refs` from `GET /api/agent-profiles/deep_reasoner`, both read from the
    SDK fork at `91430aa` (§7.5). vitest's `context.test.ts` fixes the shape as read; §10.6's test or D5's E12, neither
    built, would run it.
13. **The editor's size, as reported and as measured** (v2). The build's report said CodeMirror's core alone is above
    300 KB. This revision's measurement (§6.2 B3) has the packages the editor uses at 281 KB without Python's grammar
    and 349 KB with it. The conclusion stands (no CodeMirror Python editor fits 300 KB); the reason is the grammar,
    not the core.
14. **The shim formats its sentences with `str.format`** (v2, found reading the build): §9.2's templates, as v1
    specified them for a file that imports only the standard library, against the Code Guide's "never `.format()`";
    small functions returning f-strings, as `tools/texts.py` and D1's `texts.py` have, would follow it. Any edit to
    `shim.py` changes the text every new grant stores, so each existing grant then shows `MCP_SHIM_OLD` until its
    **Update** (`shim_current` compares the stored source with today's byte for byte); a stored v1 shim keeps working
    (`test_a_stored_v1_shim_works_with_todays_session`). For the Refactorer at Gate C, with §6.2 B12's `_parse`.
15. **The shim cannot describe a tool property whose schema is `true` or `false`** (v3, found by `c2cfdc0`'s fake
    `odd_server.py`). JSON Schema allows a boolean schema; §8.4's `_type` reads every property schema as a mapping and
    raises `AttributeError`. Since §6.2 B19 that server fails alone (`MCP_FAILED`) rather than the run, but a valid
    server cannot be bound. Reading a boolean schema as `Any` would fix it; not changed by the build. *(v4: fixed by
    `7eb7812`, §6.2 B26: `true` is `Any`, `false` `Never`.)* *(v5: what is left is §4.8's case: a property schema that
    is neither a mapping nor a boolean (a string, a number: no JSON Schema, so no valid server sends it). Under
    `dr-acp` that server fails alone; under plain `dr` the shim raises `AttributeError`, `make_tools` passes it on,
    and the run does not start. Read in the code, and run by the as-built r2's probe (its #11). Catching it in
    `mcp_server`, as `open_session` does, would give a stand-in instead; not proposed, since a valid server never
    sends it.)*
16. **A namespace error fails the build in one case `build_reasoner` alone would not** (v3, §6.2 B19).
    `open_session` resolves every namespace of the config to find each grant (§4.4, `registry.resolve(ns)` for each),
    while `build_reasoner` resolves what the run needs. So a hand-written config run through `dr-acp --config`, with a
    broken namespace outside the entry namespace's chain, fails at build when it has an MCP block. This is the
    Conductor's caveat on `c2cfdc0`; I read it in the code and did not reproduce it. A run built from the Library
    cannot reach it (D2's invariants). Left as is; for Michael to accept, or for D1's next revision.
17. **D4's head will move under it** (v4; v5 with the as-built r2's numbers, its #13 and §5.1): D4 carries D2 at
    `90044f0` and D1 at `21f4a8b`, before D1's refactor merged into `main` (`32c7f61`). D2's head `cd0b60c` has
    merged `main`; in `src/deep_reasoning/acp/` it differs from `d4e9cd3` in 18 files (+125 −330), six of which D4
    edits (`agent.py`, `encoder.py`, `runlog.py`, `session.py`, `supervisor.py`, `worker/runner.py`), and a trial
    merge of `f69bc73` with it (`git merge-tree`) is clean; the merged tree was not built or tested. So once D3 is
    brought onto D2's head, D4 follows: a new head, no D4 behaviour changed, and the Gate B runs are `f69bc73`'s, not
    that head's. *(v6: so it happened. D4 at `68ebe81` carries D3's head `73c6425`, D2's code head `0e0a394` and D1's
    `f7a91f3` (`01abb88`, `3129da9`); CI ran at `68ebe81` and the live tier at `3129da9` (the "Merged" paragraph). D1's,
    D2's and D3's code reached `main` through their PR stacks (D3's #19–#26, `1f9fe52`), whose commits are not the task
    branches' that D4 merged, so against `1f9fe52` a trial merge of `68ebe81` conflicted in 23 files, 22 of them add/add
    (D3's frame files and tests, the built files, `uv.lock` and D2's `library/api.py`), as the as-built r3 found at
    `3129da9` (its #12). The stack did not: #27 sat on D3's top PR head `c60d6d9`, whose tree is `1f9fe52`'s, and
    #27–#33 merged into `main` as `cbcad70` … `53c821b`, whose tree is #33's head `c95e059`. Against `53c821b`,
    `68ebe81` now merges without a conflict, and outside `docs/` and `as_built/` the two differ only in
    `pyproject.toml`'s sdist exclude and `tests/acp/test_stop.py` (as-built r4 §1.3 #12, §5.1).)*

---

## Appendix A · Signature reference

Python as it will be written, ruff-formatted, bodies `...`; TypeScript in declaration form (`declare` marks a body
the sections above specify), one field per line. Paths are relative to `src/deep_reasoning/` or `canvas-app/src/`.
v2: every block matches the code at `965f318`; a `# v2` comment marks what the build changed or added (§6.2).
v4: and at `f69bc73`; no signature here changed after v3 (`7eb7812` changed only the shim's private `_type`, §6.2
B26). v6: and at `68ebe81`, where `# v6` marks what changed after Gate B: `tool_routes` takes D2's `route` and
`json_route` is gone (A.2, A.5; B31); `ui/tools.ts`'s exports and `McpSnapshot` (A.6; B33); and A.1's
`require_check`, whose docstring now names `LibraryRefused` (B20 added it at v3; this appendix missed it).

### A.1 `tools/check.py`, `tools/check_child.py`

Each block lists its imports only where they name where a type comes from; the rest are the standard library's
and pydantic's.

```python
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final, Literal

from pydantic import BaseModel

from deep_reasoning.library.library import Library
from deep_reasoning.library.records import FieldError, LibraryError

Outcome = Literal[
    "built",
    "builtin",
    "invalid",
    "syntax",
    "import_failed",
    "bad_factory",
    "not_func",
    "raised",
    "timeout",
    "unavailable",
]
OK_OUTCOMES: Final = frozenset({"built", "builtin"})
SAVE_ANYWAY_OUTCOMES: Final = frozenset({"raised", "timeout", "unavailable"})
RESERVED_NAMES: Final = frozenset(
    {"FinalAnswer", "Func", "Var", "run_all", "subagent", "task"}
)
CHECK_MODEL_URL: Final = "http://127.0.0.1:9/v1"
PASSED_ENV: Final = ("PATH", "LANG", "LC_ALL", "LC_CTYPE", "TMPDIR", "TZ")
# Characters of printed output, tracebacks and example values a report carries.
SHOWN_LIMIT: Final = 2_000
# v2: the module the throwaway process runs.
CHILD: Final = "deep_reasoning.tools.check_child"


@dataclass(frozen=True)
class CheckLimits:
    ready_s: float = 30.0  # the throwaway process imports deep_reasoner
    build_s: float = 10.0  # the tool's file is imported and its factory called
    example_s: float = 10.0  # the tried expression


DEFAULT_LIMITS: Final = CheckLimits()


class ExampleResult(BaseModel):
    expression: str
    ok: bool
    value: str | None  # repr of the result, at most SHOWN_LIMIT characters
    error: str | None  # "TypeName: message"
    seconds: float


class CheckReport(BaseModel):
    ok: bool
    outcome: Outcome
    message: str
    told: str | None  # deep_reasoner's func(name, value, description).describe()
    # raised: the frames in tools/<name>.py and the exception line
    traceback: str | None
    example: ExampleResult | None
    printed: str  # the last SHOWN_LIMIT characters the tool printed
    seconds: float | None  # loading the file and calling the factory
    deep_reasoner: str  # the build that checked it
    can_save: bool
    can_save_anyway: bool


def tool_name_errors(name: str) -> list[FieldError]:
    """RESERVED_NAME for a name in RESERVED_NAMES; D2's TOOL_NAME rule is shapes.validate_tool's."""


def check_env(base: Mapping[str, str]) -> dict[str, str]:
    """PASSED_ENV from base; HOME, USER and LOGNAME from the password database;
    PYTHONUNBUFFERED=1 and PYTHONDONTWRITEBYTECODE=1. Nothing else."""


def check_tool(
    name: str,
    yaml_text: str,
    source: str | None,
    *,
    example: str | None = None,
    limits: CheckLimits = DEFAULT_LIMITS,
) -> CheckReport:
    """§3.2's static stage, then §3.3's throwaway process under limits; never raises for
    anything the tool does."""


class ToolCheckFailed(LibraryError):
    code = "check_failed"
    status = 422

    # v2: name, for CHECK_FAILED's sentence (§6.2 B9).
    def __init__(self, name: str, report: CheckReport) -> None: ...

    def payload(self) -> dict[str, Any]:
        """{"error", "message", "check": report.model_dump(mode="json")}."""


# v6: the docstring is the code's; LibraryRefused is B20's (v3), which v3–v5 left out here.
def require_check(
    library: Library,
    name: str,
    yaml_text: str,
    source: str | None,
    *,
    accept_failure: bool,
) -> None:
    """§3.5: returns when the PUT may proceed; raises ToolCheckFailed, LibraryBadRequest
    or LibraryRefused. YAML D2 refuses goes on to D2's own 422, and a change of grants
    alone (the head's block and source) runs no Check."""
```

```python
# tools/check_child.py
def main(argv: Sequence[str] | None = None) -> int:
    """python -m deep_reasoning.tools.check_child --report-fd N --name NAME [--example EXPR] MAIN
    Writes §3.3's JSON lines to fd N; prints nothing of its own to stdout."""
```

### A.2 `tools/routes.py`, `mcp/grants.py`, `mcp/wire.py`

```python
# mcp/wire.py: pydantic and yaml only (dr-acp's front imports it)
Transport = Literal["stdio", "http", "sse"]
McpState = Literal["bound", "no_answer", "failed", "not_enabled", "skipped"]
MCP_FACTORY: Final = "mcp_server"
SEEN_DIR: Final = "mcp"
REDACTED: Final = "[redacted]"
# v2: shorter values are not redacted: they would match everywhere.
SECRET_MIN: Final = 4
SEEN_VERSION: Final = 1  # v2: the seen cache's "v"
REMOTE: Final = ("http", "sse")  # v2


class McpServerSpec(BaseModel):
    """A server as OpenHands forwarded it, secrets included: control pipe only."""

    name: str
    transport: Transport
    command: str | None = None
    args: list[str] = []
    env: dict[str, str] = {}
    url: str | None = None
    headers: dict[str, str] = {}


class McpServerStatus(BaseModel):
    tool: str  # the name it is bound under
    server: str  # its name in Canvas's MCP settings
    transport: Transport | None
    state: McpState
    detail: str | None = None  # failed and skipped: why; secrets redacted
    granted: list[str] = []  # the namespaces whose resolved tools name it
    # bound: time to connect; v2: no_answer: the time waited.
    seconds: float | None = None
    count: int = 0  # bound: its tools
    told: str | None = None  # bound: deep_reasoner's describe() of its binding


class McpSeen(BaseModel):
    at: datetime
    run: str
    count: int
    told: str


def forwarded_specs(servers: Sequence[Mapping[str, Any]]) -> list[McpServerSpec]:
    """ACP mcpServers as D1 keeps them (dumped by alias): stdio (no type, or "stdio"),
    "http", "sse"; any other type is left out."""


def servers_named(config_path: Path) -> set[str]:
    """The `server` of every tool block in main.yaml whose factory is MCP_FACTORY."""


def specs_for_run(
    forwarded: Sequence[Mapping[str, Any]],
    config_path: Path,
) -> list[McpServerSpec]:
    """forwarded_specs(forwarded), keeping only the servers servers_named(config_path) names:
    what the front puts in Start.mcp_servers."""


def redact(text: str, secrets: Iterable[str]) -> str:
    """Every secret of at least 4 characters replaced by REDACTED."""


def remember_seen(
    home: Path,
    run: str,
    servers: Sequence[McpServerStatus],
    at: datetime,
) -> None:
    """§4.7: one file per bound server, atomically, 0600 in a 0700 directory."""


def read_seen(home: Path, server: str) -> McpSeen | None: ...
```

```python
# mcp/grants.py: the backend's side
SHIM_MARKER: Final = "# deep-reasoning MCP shim"


class McpGrantBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    server: str = Field(min_length=1, max_length=128)
    transport: Transport
    command: str | None = None
    args: list[str] = []
    url: str | None = None
    env: list[str] = []  # names only
    headers: list[str] = []  # names only
    granted_in: list[str]
    base_version: int


class McpGrant(BaseModel):
    name: str  # the tool row's name: how the agent calls it
    version: int
    server: str
    transport: Transport
    command: str | None
    args: list[str]
    url: str | None
    env: list[str]
    headers: list[str]
    granted_in: list[str]
    shim_current: bool
    seen: McpSeen | None


def shim_source() -> str:
    """The installed shim.py's text (importlib.resources)."""


def is_mcp_tool(record: ToolRecord) -> bool:
    """Factory MCP_FACTORY and a source starting with SHIM_MARKER."""


def header_env_name(server: str, header: str) -> str: ...


def mcp_block(name: str, body: McpGrantBody) -> dict[str, Any]:
    """§4.2's block, without factory_from (D2 adds it). Raises LibraryBadRequest for a
    stdio grant without a command or a remote one without a URL."""


def grant_record(record: ToolRecord, seen: McpSeen | None) -> McpGrant: ...
```

```python
# tools/routes.py
class CheckBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    yaml: str
    source: str | None = None
    example: str | None = None


# v6: D2's route closure is passed in (§6.2 B31); v1–v5 had tool_routes(library), built
# with a module-level json_route.
Handler = Callable[[Request, bytes], Any]


def tool_routes(
    library: Library, route: Callable[[str, str, Handler], Route]
) -> list[Route]:
    """POST /tools/{name}/check, GET /mcp, PUT /mcp/{name} (§7.2), built with D2's route."""
```

### A.3 `mcp/shim.py` (standard library at module level) and `mcp/session.py`

```python
# deep-reasoning MCP shim, version 1. Generated by the Library; grant and update it in the Tools tab.
"""One MCP server as a deep_reasoner tool (factory_from this file, factory mcp_server)."""

SHIM_VERSION: Final = 1
FACTORY: Final = "mcp_server"
CONNECT_TIMEOUT_S: Final = 10.0
CALL_TIMEOUT_S: Final = 120.0
CALL_GRACE_S: Final = 5.0  # v2: past mcp's own read timeout, the call is given up here
GUARD_POLL_S: Final = 0.5
DESCRIPTION_LIMIT: Final = 300
RESULT_KEY: Final = "result"
HTTP_TIMEOUT_S: Final = 30.0  # v2: mcp's own defaults for its HTTP client
HTTP_READ_TIMEOUT_S: Final = 300.0  # v2
REQUEST_TIMEOUT: Final = 408  # v2: the code mcp's McpError carries for a read timeout
CONNECTION_CLOSED: Final = -32000  # v2: mcp.types.CONNECTION_CLOSED
JSON_TYPES: Final = {  # v2: §8.4's JSON Schema types as Python's
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
    "array": "list",
    "object": "dict",
    "null": "None",
}
# §9.2's sentences are str.format templates here (UNAVAILABLE, NO_ANSWER, COULD_NOT_START,
# MISSING_ENV (v2), NOT_ENABLED, NOT_REACHED, NOT_IN_SESSION, NO_MCP_PACKAGE, CALL_FAILED,
# CALL_TIMEOUT, SERVER_STOPPED, HANDOFF_REFUSED, DESCRIPTION_HEAD).

# Set by dr-acp's worker (deep_reasoning.mcp.session) before tools are built: bound name -> Func.
SESSION: "dict[str, Any] | None" = None


class McpToolError(Exception):
    """A call that failed, timed out, or reached a server that is gone or was never bound."""


@dataclass(frozen=True)
class ServerSpec:
    name: str
    transport: Literal["stdio", "http", "sse"]
    command: str | None
    args: tuple[str, ...]
    env: Mapping[str, str]
    url: str | None
    headers: Mapping[str, str]


class Connection:
    """One server on a daemon thread running its own event loop (§4.3)."""

    failure: str | None
    tools: tuple[Any, ...]  # mcp.types.Tool

    def __init__(
        self,
        spec: ServerSpec,
        *,
        errlog: TextIO,
        call_timeout_s: float = CALL_TIMEOUT_S,
        # v2: the REPL name its sentences use; default spec.name.
        name: str | None = None,
    ) -> None: ...

    def start(self) -> None: ...

    def wait_ready(self, timeout_s: float) -> bool: ...

    def abandon(self) -> None: ...

    def call(self, tool: str, arguments: Mapping[str, Any]) -> Any:
        """§8.3's result, or McpToolError; marks the connection dead when the server is gone
        (v2: SERVER_STOPPED for the call in flight too; McpError 408 is CALL_TIMEOUT, §4.3)."""


class McpTool:
    def __init__(self, server: "Server", tool: Any) -> None: ...

    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...

    def __cross_namespace__(self, src: str | None, dst: str) -> "McpTool": ...

    def __copy__(self) -> "McpTool": ...

    def __deepcopy__(self, memo: dict[int, Any]) -> "McpTool": ...


class Server:
    """What the REPL binds: callable by a tool's exact name, with one McpTool attribute per
    tool whose name makes a Python identifier."""

    __name__: str

    def __init__(
        self,
        name: str,
        connection: Connection,
        *,
        granted: frozenset[str] | None,
    ) -> None: ...

    # v2: unannotated, so deep_reasoner tells the agent `name(tool, /, **arguments)` (§6.2 B4).
    def __call__(self, tool, /, **arguments): ...

    def __cross_namespace__(self, src: str | None, dst: str) -> "Server":
        """With granted set: PermissionError (HANDOFF_REFUSED) for a hand-off outside it."""

    def __copy__(self) -> "Server": ...

    def __deepcopy__(self, memo: dict[int, Any]) -> "Server": ...


class Unavailable:
    """The stand-in for a server that is not bound: every call says why."""

    __name__: str

    def __init__(self, name: str, reason: str) -> None: ...

    # v2: unannotated, as Server.__call__: the agent is told `name(*args, **kwargs)`.
    def __call__(self, *args, **kwargs): ...

    def __getattr__(self, attr: str) -> NoReturn:
        """v2: AttributeError for a name starting with "_" (inspect.signature probes
        _partialmethod, deep_reasoner __cross_namespace__); McpToolError for any other."""

    def __copy__(self) -> "Unavailable": ...  # v2

    def __deepcopy__(self, memo: dict[int, Any]) -> "Unavailable": ...  # v2


def describe(name: str, spec: ServerSpec, tools: Sequence[Any]) -> str:
    """§8.4's description."""


def bound(name: str, connection: Connection, *, granted: frozenset[str] | None) -> Any:
    """Func(Server(...), describe(...))."""


def unavailable(name: str, reason: str) -> Any:
    """Func(Unavailable(name, reason), UNAVAILABLE)."""


def spec_from_block(
    params: Mapping[str, Any],
    environ: Mapping[str, str],
) -> tuple[ServerSpec, list[str]]:
    """Plain dr: the block's snapshot with values from environ; the names it could not find."""


def mcp_server(client: Any, params: dict[str, Any]) -> Any:
    """The factory (§4.3)."""


def guard(argv: Sequence[str]) -> NoReturn:
    """python -I shim.py --guard -- COMMAND ARGS… (§4.6)."""
```

```python
# mcp/session.py: the worker's side
GRANTED_NOWHERE: Final = "granted to no namespace"  # v2: a skipped status's detail
OUT_OF_REACH: Final = "granted only where this conversation cannot spawn"  # v2
LOG_TAIL: Final = 300  # v2: characters of a failed server's own output in its status
PRINTED: Final = '{failure}; it printed: "{tail}"'  # v2
PIPE_READ: Final = 65_536  # v3: bytes of a server's stderr read at a time
DRAIN_S: Final = 2.0  # v3: a failed server's last output reaches its log within this


def open_session(
    cfg: V2Config,
    specs: Sequence[McpServerSpec],
    *,
    run_dir: Path,
) -> list[McpServerStatus]:
    """§4.4: connect the granted, reachable servers at once, each within its own
    connect_timeout_s from one shared start (v2; the code's docstring still says
    "under one deadline"), install shim.SESSION for every MCP block, and return one
    status per block."""


def reachable(
    registry: NamespaceRegistry,
    start: str,
    names: Sequence[str],
) -> set[str]:
    """The closure of {start} under deep_reasoner's check_spawn."""
```

### A.4 D1's files

```python
# acp/worker/protocol.py
class Start(BaseModel):
    op: Literal["start"] = "start"
    run: str
    session: str
    run_dir: str
    config_path: str
    namespace: str
    client_overrides: dict[str, Any]  # merged over cfg.client
    # D4: the forwarded servers the run's MCP blocks name
    mcp_servers: list[McpServerSpec] = []


# acp/runlog.py
class McpStatus(_Ev):
    kind: Literal["mcp.status"] = "mcp.status"
    servers: list[McpServerStatus]


# acp/texts.py
def mcp_no_answer(server: str, seconds: float) -> str: ...


def mcp_failed(server: str, detail: str) -> str: ...


def mcp_not_enabled(server: str, namespaces: Sequence[str]) -> str: ...


def mcp_notice(status: McpServerStatus) -> str | None:
    """The notice for no_answer, failed and not_enabled; None otherwise."""


# acp/supervisor.py
class RunHandle:
    @classmethod
    async def start(
        cls,
        *,
        run_id: str,
        session: "Session",
        source: RunSource,
        after: RunEndReason | None,
        decomposition: str | None,
        home: Home,
        route: ModelRoute,
        outbox: Outbox,
        mode: Mode,
        heartbeat_s: float,
        mcp_servers: Sequence[McpServerSpec] = (),
    ) -> "RunHandle": ...


# tests/acp/harness.py
class DrAcp:
    async def open_session(
        self,
        cwd: Path,
        mcp_servers: Sequence[Any] = (),
    ) -> str: ...
```

### A.5 D2's `api.py`

```python
class _ToolBody(_Body):
    source: str | None = None
    granted_in: list[str] | None = None
    # D4: save a tool whose Check failed in a way it allows
    accept_check_failure: bool = False


# v3: sentence leads the 400; tools/routes.py passes MCP_BAD_REQUEST (§6.2 B21)
def _parse[T: BaseModel](
    model: type[T],
    body: bytes,
    sentence: str = texts.BAD_REQUEST,
) -> T:
    """The body as model; a body it cannot read is 400, sentence and pydantic's reason."""


# v6: no json_route (§6.2 B31). create_app keeps D2's route(path, method, handler)
# closure and appends *tool_routes(lib, route); it imports require_check and
# tool_routes inside itself, since tools/routes.py imports _parse from this module.
```

### A.6 The frame (TypeScript)

```ts
// shared/protocol.ts
export type McpTransport = "stdio" | "http" | "sse";
export declare const MCP_TRANSPORTS: readonly McpTransport[]; // v2: readFrameParams checks entries against it

export interface McpServerInfo {
  name: string; // the key in Canvas's MCP settings
  transport: McpTransport;
  command: string | null;
  args: string[];
  url: string | null;
  env: string[]; // names only
  headers: string[]; // names only; v6: its auth's included, for every transport (§6.2 B30)
  forwarded: boolean; // enabled, and in the deep_reasoner profile's mcp_server_refs (or refs null)
  why_not: "disabled" | "not_in_profile" | null;
}

export interface FrameParams {
  tab: TabId;
  parent: string | null;
  namespace: string | null;
  started: boolean;
  cap: string;
  focus: string | null;
  theme: Readonly<Record<string, string>>;
  /** D4: Canvas's MCP servers, for the Tools tab; null when unread or unreadable. */
  mcp: readonly McpServerInfo[] | null;
}

// page/context.ts
export declare function readMcpServers(request: AgentServerRequest): Promise<McpServerInfo[] | null>;
export declare function mcpServersFromSettings(
  mcpConfig: Readonly<Record<string, unknown>>,
  refs: readonly string[] | null,
): McpServerInfo[];

// ui/types.ts
export type CheckOutcome =
  | "built"
  | "builtin"
  | "invalid"
  | "syntax"
  | "import_failed"
  | "bad_factory"
  | "not_func"
  | "raised"
  | "timeout"
  | "unavailable";

export interface ExampleResult {
  expression: string;
  ok: boolean;
  value: string | null;
  error: string | null;
  seconds: number;
}

export interface CheckReport {
  ok: boolean;
  outcome: CheckOutcome;
  message: string;
  told: string | null;
  traceback: string | null;
  example: ExampleResult | null;
  printed: string;
  seconds: number | null;
  deep_reasoner: string;
  can_save: boolean;
  can_save_anyway: boolean;
}

export interface McpSeen {
  at: string;
  run: string;
  count: number;
  told: string;
}

// v6: what a grant stores of a server, never a value; McpGrant and McpGrantBody extend it (§6.2 B33)
export interface McpSnapshot {
  server: string;
  transport: McpTransport;
  command: string | null;
  args: string[];
  url: string | null;
  env: string[];
  headers: string[];
}

export interface McpGrant extends McpSnapshot {
  name: string;
  version: number;
  granted_in: string[];
  shim_current: boolean;
  seen: McpSeen | null;
}

// ui/api.ts
export interface ToolBody {
  yaml: string;
  source?: string | null;
  granted_in?: string[];
  base_version: number;
  accept_check_failure?: boolean; // D4
}

export interface CheckBody {
  yaml: string;
  source: string | null;
  example: string | null;
}

export interface McpGrantBody extends McpSnapshot {
  // v6: the snapshot's fields come from McpSnapshot
  granted_in: string[];
  base_version: number;
}

export declare function checkTool(name: string, body: CheckBody): Promise<CheckReport>;
export declare function getMcp(): Promise<McpGrant[]>;
export declare function putMcp(name: string, body: McpGrantBody): Promise<Written<McpGrant>>;

// D3's error class; v2 adds one field
export declare class LibraryError extends Error {
  readonly status: number;
  readonly code: string; // D2's codes, and D4's check_failed
  readonly errors: readonly FieldError[];
  readonly head: unknown; // conflict: the current record, or null
  readonly check: CheckReport | null; // v2: check_failed's report
}

// ui/tools.ts. v6 (§6.2 B33): RESERVED_NAMES, §3.2's six for defaultToolName, is module-private
// (v2–v5: exported); McpSnapshot is ui/types.ts's interface (v2–v5: Omit<McpGrantBody, …> here).
export type McpRowState = "given" | "disabled" | "not_in_profile" | "gone";

export interface McpRow {
  server: string;
  info: McpServerInfo | null; // null: gone from Canvas's settings, or (v2) its settings unread
  grant: McpGrant | null;
  state: McpRowState;
  changed: boolean;
  oldShim: boolean;
}

export interface ToolDraft {
  name: string;
  yaml: string;
  source: string;
  example: string;
  grantedIn: string[];
  baseVersion: number; // 0 for a new tool
}

export declare function splitTools(
  tools: readonly ToolRecord[],
  grants: readonly McpGrant[],
): ToolRecord[]; // the user's own tools, in GET /tools order
export declare function defaultToolName(server: string, taken: ReadonlySet<string>): string;
export declare function mcpRows(
  servers: readonly McpServerInfo[] | null,
  grants: readonly McpGrant[],
): McpRow[];
// v6: one function for Canvas's settings and for a grant; v2–v5's grantSnapshot(grant) is gone
export declare function snapshotOf(
  server: string,
  target: Omit<McpSnapshot, "server">,
): McpSnapshot;
// v6: v1–v5's inheritedGrants returned namespace -> ancestor; this returns each one's note
export declare function inheritedNotes(
  tool: string,
  effective: readonly Effective[],
): Record<string, string>; // namespace -> "inherited from <ancestor>" (INHERITED_ROW)
// v2: "tool.<name>" | "tool.new"; D3's drafts.ts prefixes "dr-library.draft."
export declare function toolDraftKey(name: string | null): string;

// ui/editor/python.ts (the "editor" chunk)
export interface PythonEditor {
  destroy(): void; // v2: no setValue; the editor owns its text once mounted (§6.2 B2)
}

export declare function createPythonEditor(
  parent: HTMLElement,
  value: string,
  onChange: (value: string) => void,
): PythonEditor;

// ui/components (props; Preact function components). OnBackendLost is D3's, from ui/load.ts.

// ui/components/python.tsx (v2, §6.2 B1, B2)
export interface PythonFieldProps {
  label: string;
  value: string; // the text the editor starts with; a caller that replaces it mounts a new field (a new key)
  onChange: (value: string) => void;
  testId: string;
}

export declare function PythonField(props: PythonFieldProps): JSX.Element;

export interface ToolEditorProps {
  record: ToolRecord | null; // null: + New tool
  namespaces: readonly NamespaceRecord[];
  effective: readonly Effective[];
  onSaved: (record: ToolRecord, created: boolean) => void;
  onDeleted: (name: string) => void;
  onBackendLost: OnBackendLost; // v2; v1's takenNames is gone (§6.2 B8)
}

export interface CheckResultProps {
  report: CheckReport;
  onSaveAnyway?: () => void; // offered when report.can_save_anyway; v2: no saving flag (§6.2 B8)
}

export interface McpServerRowProps {
  row: McpRow;
  namespaces: readonly NamespaceRecord[];
  effective: readonly Effective[];
  takenNames: ReadonlySet<string>;
  onChanged: () => void;
  onBackendLost: OnBackendLost; // v2
}

export declare const mcpTestId: (server: string) => string; // v2: Appendix B's <server>

// ui/components/fields.tsx: D3's ConfirmRow, whose props are an inline type there; v2 adds one
export interface ConfirmRowProps {
  sentence: string;
  confirm: string;
  onConfirm: () => void;
  onCancel: () => void;
  confirmTestId?: string; // v2: the confirming button's test id; dr-confirm-yes when absent
}
```

---

## Appendix B · Test ids inside the frame (for D4's tests and D5's E12)

Tools tab: `dr-tools-risk` · `dr-tool-<name>` (D3's row id) · `dr-tool-new` · the editor: `dr-tool-name`,
`dr-tool-yaml`, `dr-tool-source` (the CodeMirror host or the textarea), `dr-tool-example`, `dr-check`,
`dr-check-result`, `dr-check-told`, `dr-check-example`, `dr-check-printed`, `dr-tool-grant-<namespace>`,
`dr-tool-save`, `dr-tool-save-anyway`, `dr-tool-delete`, `dr-tool-delete-confirm`, `dr-tool-result`,
`dr-tool-help`, `dr-discard-draft` (D3's) · MCP: `dr-mcp-<server>` (the server's name with every character outside
`[A-Za-z0-9_-]` as `_`), `dr-mcp-name-<server>`, `dr-mcp-grant-<server>-<namespace>`, `dr-mcp-seen-<server>`,
`dr-mcp-update-<server>`, `dr-mcp-remove-<server>`, `dr-mcp-state-<server>`, `dr-mcp-unknown`.

v2, as built: `dr-check-status` (the editor's `CHECKING` or `SAVING_CHECKING` line while it shows) is new;
`dr-tool-delete-confirm` reaches D3's `ConfirmRow` through its new `confirmTestId`; the editor's view also reuses D3's
`dr-back`, `dr-errors`, `dr-conflict`, `dr-reload-entry`, `dr-save-over` and `dr-tool-grant-list` (D3's
`NamespaceChecklist` list for the prefix `dr-tool-grant`).
