# D1 · `dr-acp`, as built

**TASK-2** · Cartographer · the code at `21f4a8b` (head of `v1-dr-acp`; this file is on `as-built/d1`)
· checked against the design at `f281109` (`docs/design/d1-dr-acp.md` v2, unchanged at `21f4a8b`)
· deep_reasoner_beta `d7334ae` · agent-client-protocol 0.12.1 · 2026-10-03.

**Evidence marks.** Every claim carries one.
- **[run]**: executed in this sandbox at `21f4a8b`: the full suite
  (`DR_BETA_CHECKOUT=<checkout> uv run pytest`: 230 passed, 3 deselected, 334 s), a REPL call, or an
  uncommitted script that drives a real `dr-acp` over stdio against `FakeOpenAI`.
- **[CI]**: read from GitHub's logs of the CI and live runs at `21f4a8b`. I did not run a paid model
  or a real `claude` CLI.
- **[read]**: read in the code, **not executed**. Weaker evidence than [run]; §7 lists the
  load-bearing ones.

**Reading order.** §1 (what exists), then §2 (divergences: read this first), then §3–§5 as a map,
§6 (the experiments as measured), §7 (what I could not verify).

---

## 1 · What exists

`dr-acp` is a stdio ACP agent. One front process (asyncio) serves one ACP connection and any number
of root sessions on it; each root session has at most one live deep_reasoner **run**, executed in a
**worker** subprocess in its own process group. The worker turns deep_reasoner's structlog events
into **RunEvents** and writes them to a pipe; the front appends each to the run log, then encodes it
as ACP updates. [read; run end to end by every test that spawns `dr-acp`]

```text
ACP client ── stdio, JSON-RPC lines ──▶ front: wire.serve ─ agent.DrAcpAgent ─ session.Session ─ supervisor.RunHandle
                                                                                   │ control pipe ▲ event pipe
                                         worker: runner.Worker ─ recorder.Recorder ─ stop.InterimStop | DeanStop
pump (one task per run): event line ─▶ RunLog.append (runs/<run>/events.jsonl) ─▶ Encoder.feed ─▶ Outbox.update
```

| Part | Lines | Where |
|---|---|---|
| front and worker | 3,209 | `src/deep_reasoning/acp/`, `…/acp/worker/` |
| client-side helpers, shipped in the package | 667 | `src/deep_reasoning/acp/testing/` |
| tests | 4,737 + 584 lines of golden recordings | `tests/acp/` |

233 tests: 230 deterministic (no network beyond 127.0.0.1), 3 marked `live`. [run]

The front imports neither deep_reasoner nor OpenHands at start-up: after importing `cli`, `agent`,
`supervisor` and `wire`, no `deep_reasoner*` or `*openhands*` module is loaded. [run] deep_reasoner
is imported by the front only inside `ConfigCatalog`'s methods (in a thread), and by the worker. [read]

---

## 2 · Divergences from the design (`f281109`)

The changelog holds no `drift:` line for TASK-2; every item below was found from the code. The
design doc has not moved since `f281109`, and all eleven build commits come after it. "Design §x"
cites `f281109`.

### 2.1 Behaviour a client or a user sees

**D-1 · The task is the first text block, not all of them.** `agent.user_text`
(`agent.py:38–49`) takes the prompt's first `text` block plus each `resource_link`'s uri on a line
of its own; every later text block is left out of the task and logged in `prompt.start.dropped`
(`runlog.py:44`). Design §4.2 step 2 joins all text blocks with `"\n"`. Reason (commit `db47b5e`):
OpenHands' bridge sends the user's message as one block, then the turn's extensions and, on the
first prompt, its system suffix (with the `<CUSTOM_SECRETS>` list), each as a block of its own;
joining them made all of that deep_reasoner's task. [run: `user_text([first, second, third])` →
`("first", ["second", "third"])`; `test_what_openhands_appends_to_a_prompt_never_reaches_the_task_and_is_logged`
also checks none of it reaches the model]

**D-2 · `usage_update._meta.deep_reasoner.cost_source` can be `"mixed"`.** When a session's total
includes calls priced from more than one source, the encoder reports `"mixed"`
(`encoder.py:72–76`). Design §5.2 and §5.8 allow `provider`, `table`, `claude` (or null). No test
covers it. [run: REPL, two calls priced `table` and `provider` → `"mixed"`]

**D-3 · The worker's environment also loses `OPENHANDS_AUTOMATION_API_KEY`.** `ALWAYS_REMOVED`
(`route.py:145–152`) has four patterns; design §4.7 has three. Reason (commit `21f4a8b`): Canvas's
launcher puts the agent-server's session API key there, the bridge passes its environment to
`dr-acp`, and the key opens the agent-server's whole API. [run: `test_the_agent_servers_secrets_never_reach_the_worker`, and REPL]

**D-4 · After SIGTERM the worker sends nothing more.** The worker's SIGTERM handler mutes the
recorder before raising `RunKilled` (`runner.py:159–161`, `recorder.py:189–198`). So after a root
Stop, or a `closed` end that had to be forced, the run log holds no `agent.end` or `cell.end` for the
agents the signal unwound; the front's `run.end` alone ends them on the wire (§4.4). Design §6.4
step 3 drains "events the worker wrote before dying"; that still holds, but nothing is written once
the signal lands. The docstring's reason: "the front is ending the run and describes its end
itself". [run: a root Stop during the root's own busy cell, which SIGTERM unwinds (exit 0), leaves
`run.start, prompt.start, worker.ready, agent.start, usage, cell.start, run.end stopped`, although
deep_reasoner logs `agent.end failed` on any `BaseException` that leaves a drive
(`v2/agent.py:899–905`); a forced shutdown leaves the same shape ending `run.end closed`. Under
four spinning children the client still receives four idle updates with `status: stopped`, all from
`run.end`]

**D-5 · `session/close` and shutdown do not take the session lock.** The lock serializes `prompt`
(`session.py:143`), `set_config_option` (`agent.py:183`) and the replay in `load_session`
(`agent.py:168`); `close_session`, `close_all` and the close inside `load_session` call
`Session.close` without it. Design §4.2 lists `close` among the serialized calls. Consequence: a
`session/close` during a prompt ends that prompt. [run: close during a hanging root cell returned
after 2.02 s; the prompt answered `cancelled` with outcome `closed`; `run.end closed`, exit 0]

### 2.2 How the worker reads deep_reasoner and stops it

**D-6 · A forked agent's own LLM and REPL are attributed to the fork.** `Recorder._working_for`
(`recorder.py:212–221`) treats an `agent.loop`/`llm.call` of kind `llm`, or a `repl.execute` of kind
`repl`, on a node directly under a known agent as that agent's own think call or cell, when the
agent has no open cell (for `llm`). Design §6.1 opens think cells only from `kind == "agent"`, types
a call as `think` only for `kind == "agent"`, and closes cells from `repl.execute` "for a known
agent". Reason (commit `cbb0148`): deep_reasoner's `fork()` branches the parent's LLM and REPL
(`v2/agent.py:478–520` at `d7334ae`), and they log on nodes of their own under the fork. [run:
`test_a_forks_own_llm_and_repl_nodes_work_for_the_fork`, and E1's `fork` scenario in both modes]

**D-7 · `DeanStop.stop` calls Dean's function first, under the recorder's lock, and only for a
running agent.** `stop.py:60–67`: holding the recorder's lock, `fn(node)` if the node's current
drive has not ended, then `note_stop` (which emits `stop.accepted`). Design §6.3: `note_stop`, then
`fn`. Docstring's reason: `stop.accepted` marks the moment the stop is in force, and no `agent.end`
is classified between the two. To support it the recorder gains `holding()` and `running()`
(`recorder.py:175–183`). [read; the path runs in `test_dean_stop_ends_the_branch_and_the_parent_keeps_every_siblings_result`, run]

### 2.3 Signatures and fields

None of these changes behaviour beyond §2.1–2.2. [read]

| Design | Built |
|---|---|
| `Options.home: Path` | `Path \| None`; `Home.resolve` applies `$DR_HOME`, then `~/.deep-reasoning` (`cli.py:23–25`) |
| `serve(make_agent, *, acp_out_fd, stdin_fd=0)` | adds `flat=False`, `shutdown_grace_s=0.3` (`wire.py:203–210`) |
| `Session.prompt(text)` | `prompt(text, dropped=())` (`session.py:136`) |
| `RunHandle.start(…)` | adds `decomposition` (`supervisor.py:82–95`); `run.start.source` also carries `namespace` (`supervisor.py:125–130`) |
| `RunHandle.prompt(index, text, task, decomposition) -> PromptEnd` | adds `dropped`; returns `PromptEnd \| RunEnd` (the `run.end` of a run stopped, closed or crashed under the prompt) |
| `PromptStart` | adds `dropped: list[str] = []` |
| `Recorder(sink)` | `Recorder(sink, prices)`; adds `holding`, `running`, `mute` |
| `CostLedger` in `encoder.py` | in `costs.py` |
| `Encoder` | adds `prompt_in_flight`; the menu, option, closing-message and idle-usage builders are module functions in `encoder.py` |

### 2.4 Repository, CI and the proof

**D-8 · No live doc: a live test tier instead.** Design §8.4 and §8.5 have the Docwright run
`docs/dr-acp.ipynb` against gpt-6-luna, a `docs` dependency group (`ipykernel`, `nbclient`), and a
`live-doc.yml` workflow. Built: three `@pytest.mark.live` tests (`tests/acp/test_live.py`), excluded
by default (`pyproject.toml:43–44`), run by `live.yml` on demand. There is no `docs` group and no
`live-doc.yml`; `docs/dr-acp.ipynb` (from `4b527a2`, before the build) has 52 cells, no outputs, and
nothing runs it. Reason: the workspace's changelog entry of 2026-10-02 17:38, "The proof is the
code's tests: no live-doc stage, no Docwright". [read; the notebook's state run]

**D-9 · gpt-6-luna's price is from secondary listings.** `prices.yaml`: 0.10 USD in and 0.50 USD out
per million tokens, 1,050,000-token window, "as listed by OpenRouter and eesel.ai, read through a web
search on 2026-10-02 (openai.com was unreachable from the build sandbox)". Design §10 item 1: from
OpenAI's page. [read]

**D-10 · `structlog` is a direct dependency, and the front configures it.** `pyproject.toml:12`;
`cli.configure_logging` sets up structlog and stdlib logging, both to stderr (`cli.py:59–75`).
Design §8.5's dependency list has no structlog, and §4.2 configures stdlib logging only. [read]

**D-11 · Tests are laid out per module, not per experiment.** Design §8.1 names
`test_tree_fidelity.py`, `test_stdio_integrity.py`, `test_tripwire.py`, `test_schema.py`,
`test_surfaces.py`, `test_load.py`; none exists. The experiments live in the module tests, mapped in
§6. [read]

**D-12 · E1's reference tree is read differently.** Design §8.1: deep_reasoner's tree from its node
YAMLs' `ancestry` and its `repl.execute` count per node. Built (`scenarios.py:250–277`): agents are
the nodes whose model calls `llm_calls.jsonl` logs as kind `agent`, a fork's kind-`llm` node that
writes code, or the node a `claude_calls.jsonl` row runs for; cells are the turns with a `<repl>`
block in the node YAML's conversation (demonstrations before a system prompt skipped). The reference
still reads only deep_reasoner's own files. [read]

**D-13 · E3's null is relaxed to "at most one call per branch agent after the stop".**
`test_stop.py:97–103` allows each branch agent at most one model call that starts after
`stop.accepted` was logged ("A turn that began before the stop may still make its call"); the live
test allows at most one `usage` event per branch node (`test_live.py:123–126`). Design §8.1's null:
"any call started after the stop by an agent of the stopped branch". [read]

**D-14 · The schema check sits in the test client, not on the `Outbox`.** `harness.DrAcp.observe`
(`harness.py:160–170`) validates every message the client receives from `dr-acp` (updates, responses,
errors) against the vendored schema. Design §8.1 E4: an `Outbox` observer. Same messages, other end
of the pipe. [read]

**D-15 · Golden normalization.** `golden.py:34, 61–89`: run ids become `00000000-000000-000000`, root
ids `s-0000000000000000`, install paths `SITE`/`STDLIB`/`TMP`, amounts are rounded to 10 decimals, and
only each session's **last** `usage_update` is kept. Design §8.3: `RUN`, `ROOT`, and each session's
last `usage_update` before a state change. [read]

**D-16 · The weekly tripwire against Dean's `main` has never run.** `acp-tripwire.yml` exists only on
`v1-dr-acp`; GitHub registers only `ci`, `live` and `token-check` for the repo, and `main` (the
default branch, from which GitHub fires `schedule`) holds only `live.yml`. Design §8.1 E4 runs it
weekly. [run: `gh api …/actions/workflows`, `git ls-tree main .github`]

Not a divergence: design §8.1 says "eight scripted runs" for E1 and lists nine; nine are built.

---

## 3 · The public surface, from the code

**Command line.** [run: `test_cli.py`]

```text
dr-acp --config PATH [--home DIR] [--flat] [--heartbeat SECONDS] [--log-level LEVEL]
```

Without `--config`: exit 2, stdout empty, stderr `dr-acp needs --config PATH (a dr main.yaml) until
the Library exists.` Defaults: heartbeat 60 s, level `WARNING`. `--flat` wins over a client that
advertises `subagents` [run]. The worker is `python -m deep_reasoning.acp.worker --control-fd N
--events-fd M`, started only by the front.

**ACP.** `initialize` answers exactly design §5.1's object (`loadSession`, no image/audio/embedded
context, `mcpCapabilities` http and sse false, `sessionCapabilities.close`, agent `dr-acp` 0.1.0,
no auth methods). [run] Native mode iff `clientCapabilities.subagents` is an object and `--flat` is
off. [run] Implemented: `session/new`, `session/load`, `session/set_config_option` (one option,
`namespace`), `session/prompt`, `session/cancel`, `session/close`; `session/fork` answers -32601
[run]; `resume` and `list` are left to the router [read]. Every prompt response carries
`_meta.deep_reasoner.{run, outcome}`. Refusals carry the §5.6 sentence as `message` and
`{"deep_reasoner": {"error": NAME}}` as `data`: `UNKNOWN_SESSION`, `UNKNOWN_OPTION`,
`UNKNOWN_NAMESPACE`, `NAMESPACE_FIXED` (-32602), `PROMPT_BUSY` (-32600) [run], `CATALOG_ERROR`
(-32603) [read]. Every sentence of §5.6 matches the design verbatim: the seven constants, the
twelve with fields and the three stop acknowledgements [run: compared against the design's table;
`test_texts.py` pins the ones with fields].

**Ids** (`ids.py`), all derived from the run id `YYYYmmdd-HHMMSS-<6 hex>`: root session `s-<16 hex>`,
child session `<run>-n<node>`, cell `<run>-n<node>-c<k>`, flat card `<run>-n<node>-a<drive>`, task and
answer messages `-t<drive>` / `-r<drive>`. `ids.short` maps them to `root`, `n2`, `c2.1`, `a2.1` for
display, one way. [run: `test_ids.py`]

**Files** under `--home`, else `$DR_HOME`, else `~/.deep-reasoning`: `sessions/<session>.json`
(written atomically, first at the first prompt); `runs/<run>/events.jsonl` (the run log),
`worker.log` (the worker's stdout and stderr), and deep_reasoner's own `llm_calls.jsonl`,
`claude_calls.jsonl` and node YAMLs; `prices.yaml` laid over the shipped table. [run]

**The run log.** One JSON object per line, `v: 1`, `seq` gap-free from 1, `t` in Unix seconds, and
one of 13 kinds: front-written `run.start`, `prompt.start`, `stop.request`, `run.end`; worker-sent
`worker.ready`, `agent.start`, `thought`, `cell.start`, `cell.end`, `usage`, `stop.accepted`,
`agent.end`, `prompt.end`. `run.end.reason` is one of `closed`, `stopped`, `crashed`, `failed`,
`build_failed`, `lost`. Text fields are capped at 8 MiB, head and tail kept. [run: `test_runlog.py`,
`test_text_over_8_mib_keeps_its_head_and_tail`]

**`deep_reasoning.acp.testing`** (shipped, never imported by `dr-acp`): `Caps` and `ShimConnection`
(put `subagents` on the wire and hand the unstable updates to the client), `Printer` (records every
update as wire JSON and as a display line; `show()`, `wait_until()`, `subagents`, `commands`),
`tree()` (rebuilds each run's tree from updates alone, native or flat), `FakeOpenAI` (a chat
completions endpoint on 127.0.0.1). [run: `test_client.py`, `test_tree.py`, `test_fake_model.py`]

---

## 4 · Structure and seams

### 4.1 The front

- **`cli.main`** dups fd 1 for ACP, points fd 1 and `sys.stdout` at stderr, and only then imports the
  rest. [run: an import hook that prints to stdout and to fd 1 while the front imports
  `deep_reasoning.acp.agent` lands on stderr and every stdout line is JSON-RPC]
- **`wire.serve`** builds `acp.connection.Connection` around a handler that reads
  `initialize`'s raw `clientCapabilities.subagents` before handing every message to
  `build_agent_router(agent, use_unstable_protocol=True)`. `Outbox` is the only send path: raw dicts
  through `send_notification`, dropped silently once the client has closed the pipe (the run log still
  has them). Shutdown starts on stdin EOF or SIGTERM, closes every live run concurrently with a 0.3 s
  grace, and exits 0. [run: `test_wire.py`]
- **`agent.DrAcpAgent`** routes the ACP methods. `session/new` reads a catalog snapshot in a thread,
  answers, and sends the menu from a task created in the handler, so it follows the response (ACP
  Python's P6). `cancel` routes a root id to `Session.stop_root`, a live child's id to
  `stop_child`, and logs anything else at WARNING. [run: `test_cancel_with_an_unknown_id_is_ignored_and_logged`]
- **`session.Session`**, one per root session: the namespace, the menu, the `started` flag, the run
  ids, the cost carried over finished runs, and `last_end`, which picks the next run's notice. Its
  prompt parse is design §4.2 step 3 to the letter: a leading `/name` in the current menu is a
  command; one in any menu offered before, once started, is a late command (rejected, nothing runs, no
  run log holds it); anything else, a path such as `/home/…` included, is the task. [run:
  `test_session.py`] `load_session` rebuilds the cost and `last_end` from the run logs during replay;
  the index's own `cost` is written but not read back. [read] A replay is encoded in the **loading**
  connection's mode, not the mode `run.start` recorded. [run: a native run replayed to a flat client
  arrives as 2 cards and 7 cells on the root, no `subagent_update`]
- **`supervisor.RunHandle`**, one per live run, owns the worker process, both pipes, the pump task and
  the heartbeat task (§4.2).

### 4.2 The seam that matters: the event pipe, the pump and the run log

The front is the run log's only writer. The pump reads one line from the worker's event pipe, parses
it as a RunEvent (an unparseable line is logged and dropped), appends it with `seq` and `t`, feeds it
to the run's `Encoder`, and sends every resulting update, all under one lock, so one RunEvent's
updates never interleave with the ticker's. A second task, every `min(0.5 s, heartbeat)`, flushes
dirty usage and, while a prompt is in flight and nothing has been sent for `heartbeat` seconds, sends
the root's `usage_update`. [read; heartbeat run: `test_a_long_cell_keeps_the_root_sending_usage_on_the_heartbeat`]
Because the encoder is a pure function of the log, a replay runs the same encoder over the same events
with `replay=True` (no `capabilities` on announcements, no intermediate usage). [run: the replayed tree
equals the live one in `test_load_replays_every_run_and_marks_a_killed_one_lost`]

The control pipe carries `Start` (run, session, run dir, config path, namespace, client overrides),
`Prompt` (index, task, decomposition), `Stop` (node) and `Close`, one JSON line each
(`worker/protocol.py`). [read]

### 4.3 The worker

`runner.Worker` reads the control pipe on a daemon thread: `Stop` is handled on that thread by the stop
adapter; the rest goes to the main loop. Control EOF (the front died) kills the worker's process group.
[read] On `Start` it turns deep_reasoner's cache off, installs the recorder ahead of deep_reasoner's
`LogProcessor` through `configure_structlog_fixture`, sets the SIGTERM handler and emits
`worker.ready`. On the first `Prompt` it loads the config, sets the namespace and client overrides, and,
for a decomposition, sets `cfg.task` and hands the recorder the puppeteered turns; then
`build_reasoner(…, main_decomposition=…)`. The log context and model alias stay entered for the run;
each prompt is one `reasoner.acall(task)`. A build exception ends the prompt `build_failed` and the
worker with exit 2; a drive exception, `failed` and exit 1; `Close` or SIGTERM, exit 0; each through
`close_run` under a 0.7 s watchdog that exits 3. [read; exit codes 0, 1 and 2 run: read back from
the run logs of `test_a_failed_drive_…`, `test_a_missing_key_…` and the closing scripts; exit 3 not
seen] The worker does not call `load_dotenv`. [read]

### 4.4 Where the complexity sits: the recorder and the encoder

**The recorder** (`worker/recorder.py`, 464 lines) holds every inference about deep_reasoner, under
one re-entrant lock, on whichever thread logs. A cell is opened by its first evidence: the root's
puppeteered turn at `agent.turn`, a think reply with a `<repl>` block at `agent.loop`, or a child
starting under a parent with no open cell (`inferred`, code filled in when the cell ends). An event's
owner is its node if that is a known agent, else the deepest known agent in its ancestry, so the `llm`
tool's and a Claude session's nodes bill their agent. A second `agent.start` for a node is its next
drive. `agent.end` closes an open cell as interrupted and classifies the end by design §6.3's table
(stop targets stay armed until the target's next drive; `collateral` marks a sibling `gather`
cancelled). The interim stop raises `StoppedByUser` at the next `agent.turn` of the target or a
member of its branch. [run: `test_recorder.py`, 21 tests, and the tripwire on the real deep_reasoner]

**The encoder** (`encoder.py`, 626 lines) turns RunEvents into updates, design §5.2 (native) and §5.3
(flat), with one method per kind. It keeps per-agent state: open cells, drive, and an inclusive cost
tally rolled up to every ancestor; the root's total adds the cost carried from earlier runs of the
conversation. A cost is omitted while any contributing call had no price. [run: `test_encoder.py`, 45 tests]

### 4.5 How a run ends

| End | Who writes `run.end` | Client sees | Prompt answers | Next run's notice |
|---|---|---|---|---|
| answer / exhausted (`prompt.end`) | nobody: the run stays up | closing message with the answer, root usage | `end_turn` / `max_turn_requests` | — |
| drive raised | pump at EOF; reason from the last `prompt.end`; exit 1 | `The run failed: …` | `end_turn`, `failed` | `FRESH_AFTER_ERROR` |
| build raised in the worker | pump; exit 2 | `Could not start the run: …` (with a run id) | `end_turn`, `build_failed` | none |
| `materialize` raised in the front | no run exists | the same sentence, `run: null` | `end_turn`, `build_failed` | unchanged (`last_end` is not touched) |
| root Stop, prompt in flight | `kill("stopped")`: SIGTERM to the group, SIGKILL after 0.8 s, drain ≤ 0.3 s | running children idle `cancelled`/`stopped`, open cells `Not finished: the run was stopped`, `ROOT_STOPPED` | `cancelled`, `stopped` | `FRESH_AFTER_STOP` |
| `session/close` (2 s grace), shutdown (0.3 s), `session/load` of an open session (2 s) | `Close`, then `kill("closed")` past the grace | in flight: as root Stop with outcome `closed`; between prompts: nothing | `cancelled`, `closed` | `FRESH_AFTER_CLOSE` |
| worker exited unasked | pump; detail = `worker.log` path | children idle with no `stopReason`, `status: crashed`; `The run crashed (exit code N) …` | `end_turn`, `crashed` | `FRESH_AFTER_ERROR` |
| no `run.end` found at replay | `Session.replay` appends `lost` | `(This run ended when dr-acp stopped; …)` only | — | `FRESH_AFTER_RESTART` |

[run for every row: `test_session.py`, `test_supervisor.py`, `test_agent.py`, `test_wire.py`, and the
scripts of §6.3; except the `materialize` row's last cell, read] Measured exit codes of a stopped run: 0 when SIGTERM unwound the root's own busy cell,
-9 when a sub-agent's cell held the main thread in `ThreadPoolExecutor.__exit__` until SIGKILL;
closed runs exit 0. [run]

### 4.6 Seams left for D2, D4, D5

- **D2: `Catalog`** (`catalog.py`): `snapshot()` and `materialize(namespace, run_dir=)`, both blocking,
  run in a thread. `ConfigCatalog` offers every decomposition in every namespace, the config's first,
  first name wins, slugs numbered on collision (`triage`, `triage-2`); description `Open with the
  '<name>' decomposition`, hint `the task`; `materialize` returns the path unchanged with
  `{"config_sha256": …}`. [run: `test_catalog.py`, including 18 of deep_reasoner_beta's own configs
  read in place]
- **D4: `Session.mcp_servers`** is stored from `session/new`/`load` and never passed on. [read]
- **D5: `ModelRoute`** (`route.py`): `DirectRoute` grants nothing; `worker_env` strips
  `ALWAYS_REMOVED` and the grant's removals, adds the grant's variables and `PYTHONUNBUFFERED=1`.
  `release(run)` is called when `run.end` is logged. [run: `test_route.py`]

### 4.7 What it relies on in deep_reasoner (`d7334ae`)

Front: `load_cli_config`, `V2Config`, `build_namespace_registry`, `load_namespaces_from_dir`, `ROOT`.
Worker: `configure_structlog_fixture`, `quiet_http_client_logs`, `set_cache_dir`, `build_reasoner`,
`close_run`, `LogProcessor`, `main_decomposition_turns`, `messages.code`, and the event names and
fields of design §6.1, plus the fork's kind-`llm`/`repl` nodes (D-6). Tests only:
`DeepReasonerAgentBase._note_drive`, `__anext__`, `_node`, `_done`, `final_answer` (the fake of Dean's
stop), `mocks.FakeCompletionClient`, `mocks.write_fake_claude_cli`. `tests/conftest.py` imports four
deep_reasoner modules with `pytest` hidden from `sys.modules`, because deep_reasoner runs its notebook
tests on import wherever pytest is imported. [read]

---

## 5 · Wiring

`pyproject.toml`: `deep-reasoning` 0.1.0, Python `>=3.12,<3.13`, `deep-reasoner` pinned by git to
`d7334ae`, `agent-client-protocol>=0.12.1,<0.13` (locked 0.12.1; a test pins it), `pydantic`,
`pyyaml`, `structlog`, `ipython`; script `dr-acp`; dev group `pytest`, `jsonschema`, `referencing`,
`ruff`; `testpaths = ["tests"]`, `addopts = "-m 'not live'"`; wheel `src/deep_reasoning` only; sdist
excludes `docs/` and `as_built/` (the latter added with this document). [read; the exclusion run:
before it the sdist carried `as_built/d1-dr-acp.md`, after it neither the sdist nor the wheel does,
and pytest still collects 230 of 233 with the lock unchanged]

Workflows: `ci.yml` (every push: `uv sync --locked`, deep_reasoner_beta's configs fetched at `d7334ae`
into `DR_BETA_CHECKOUT`, `ruff check` and `ruff format --check` on `src tests`, `pytest`); `live.yml`
(on demand: fails without the `OPENAI_API_KEY` secret, then `pytest -m live -v -rA`);
`acp-tripwire.yml` (Mondays 06:17 UTC: deep_reasoner at `main`, `test_recorder.py` and `test_agent.py`;
never registered, D-16). [read]

---

## 6 · Experiments, as measured

### 6.1 The runs

| Run | Commit | Conditions | Result |
|---|---|---|---|
| CI `ci` [37052495476](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37052495476) | `21f4a8b` | ubuntu-latest, Python 3.12, deep_reasoner at `d7334ae`, beta configs present | ruff clean; **230 passed**, 3 deselected, 173 s [CI] |
| CI `live` [37053166300](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37053166300) | `21f4a8b` | ubuntu-latest, Python 3.12.3, `OPENAI_API_KEY` secret, gpt-6-luna, no beta configs | **3 passed**, 213 deselected, 38.8 s [CI] |
| this sandbox | `21f4a8b` | Linux, 4 CPUs, `DR_BETA_CHECKOUT=/home/user/deep_reasoner_beta` (`d7334ae`) | **230 passed**, 3 deselected, 334 s [run] |
| earlier: `ci` 37049699113, `live` 37050366757 | `db47b5e` | — | ci failed 2 golden tests (`failing` scenario: `FakeOpenAI` counted tokens from characters, and tracebacks carry install paths), fixed in `381f81d`; live passed [CI] |

Reproduce: `DR_BETA_CHECKOUT=<deep_reasoner_beta at d7334ae> uv run pytest` (the deterministic tier),
`OPENAI_API_KEY=… uv run pytest -m live` (the live tier, a few cents).

65 of the 230 deterministic tests spawn a real `dr-acp` over stdio through `tests/acp/harness.py`; in
each, every message `dr-acp` sends is validated against the vendored ACP schema 1.24.1 (sha256
checked) and every stdout line must parse as JSON-RPC 2.0 (E2, E4). [read: counted from the code; run:
they pass]

### 6.2 E1 · tree fidelity

`test_agent.py::test_tree_rebuilt_from_the_stream_is_deep_reasoners_own`, 9 scenarios × {native, flat}
= 18 tests: `linear` (a main decomposition, then a resumed prompt), `fanout2`, `fanout20`, `depth3`,
`namespace`, `fork`, `exhausted`, `failing` (a failing cell and a child whose model answers 500),
`claude` (deep_reasoner's fake `claude` CLI). Each runs `dr-acp` against `FakeOpenAI` and asserts:
each prompt's outcome; the tree `testing.tree()` rebuilds from the client's updates equals the
reference read from deep_reasoner's own run directory (per agent node: its parent and its cell count,
D-12); native: every child's announcement names a cell already sent on its parent, nothing reaches a
child session before its announcement, every prompt response follows a root `usage_update`; flat: only
the root session is used and no unstable update kind appears. **18/18 passed** [CI, run].
Baseline beside each arm: deep_reasoner's own files for the same run.

`test_each_stream_matches_its_golden_recording`, the same 18: per-stream sequences and the rebuilt tree
equal `tests/acp/golden/<scenario>.<mode>.jsonl` (D-15). **18/18 passed** [CI, run]. Re-record with
`uv run python -m tests.acp.golden record`.

### 6.3 E3 · stop

Root Stop (`test_supervisor.py`): during the root's `while True: pass` cell, and under 20 spinning
children; asserts the prompt answers `cancelled` within 2.0 s, the open cell fails with `Not finished:
the run was stopped`, `ROOT_STOPPED` closes the turn, every child is idle `cancelled` with `status:
stopped`, and the next prompt opens with `FRESH_AFTER_STOP`. **Passed** [CI, run]. Measured with an
uncommitted script, three trials each [run]:

| Condition | Threshold (design) | Measured |
|---|---|---|
| root Stop, busy root cell | 2 s (bridge drain; spec allowed 5) | 0.02, 0.03, 0.02 s |
| root Stop, 20 spinning children | 2 s | 0.87, 0.86, 0.87 s (SIGKILL after the 0.8 s grace) |
| shutdown on stdin EOF, root cell sleeping | 1.4 s to `run.end closed` | 0.32 s ×3, exit 0 |
| shutdown on SIGTERM, same | 1.4 s | 0.32 s ×3, exit 0 |
| `session/close`, root cell sleeping | 2 s grace, then kill | 2.02 s (one trial) |

Stop on one sub-agent (`test_stop.py`): 20 department agents, department `D0` with two course agents;
`D0` is cancelled by its full session id once a depth-3 agent is announced; `FakeOpenAI` adds 0.2 s
latency and timestamps every call. Asserted for both adapters: the root still answers; `stop.request`
and an accepted `stop.accepted` are logged; no branch agent makes more than one call after
`stop.accepted` (D-13); `D0` and both course agents end idle `cancelled` with `status: stopped`, the
courses `stopped_by` `D0`. Interim: the root's cell output ends with the qualified
`deep_reasoning.acp.worker.stop.StoppedByUser: stopped #… and its branch (…). Its running siblings …`
naming exactly the agents marked `collateral`; `D0` shows the interim stop thought. Fake Dean API:
every other department's result `D<i> surveyed` is in the root's cell output beside `Stopped(node=…)`,
and the siblings end `done`. **2/2 passed** [CI, run]. The classification rows of design §6.3 are unit
tested in `test_recorder.py` (interim branch, Dean nearest target, re-driven target, unknown or ended
target) [run].

### 6.4 E2 · stdio integrity

`test_cli.py`: a cell writes 10 MB with `sys.stdout.write`, writes to fd 1 with `os.write`, prints, then
prints 10 MB: the run answers, the first cell's output is `quiet` (the raw writes go to the worker's
own stdout, which is `worker.log` [read]), the 10 MB print arrives cut to under 10 MB with `bytes
elided`; an import hook that prints to stdout and to fd 1 while the front imports: the print lands
on stderr and every stdout line stays JSON-RPC. `test_supervisor.py`: `os._exit(1)` in a cell gives
`crashed` with exit code 1 and the `worker.log` path, and the next prompt answers after
`FRESH_AFTER_ERROR`. Plus the JSON-RPC line check in all 65 spawning tests. **All passed** [CI, run].

### 6.5 E4 · contracts

Tripwire: `test_recorder.py::test_tripwire_deep_reasoner_still_logs_everything_the_recorder_reads`
drives the real deep_reasoner in process with `FakeCompletionClient` (a main decomposition fans out two
children, one calls the `llm` tool, a second prompt resumes the root) and asserts the recorder's
`agent.start` drives and parent cells, the root's cells (`puppeteered`, `think`, `think`), every cell
closed, the children's answers, think versus tool calls, and the thought. **Passed at `d7334ae` on
every push** [CI, run]. **Against Dean's `main`: never run** (D-16). Schema: the harness check of §6.1,
on every message of 65 tests; **no violation** [CI, run].

### 6.6 E11 · surfaces (D1's part)

Six tests in `test_session.py`: the menu follows `set_config_option` (`triage`, `summarize-then-rank`
→ `triage`, `compare-departments`), with each entry's `_meta.deep_reasoner.{decomposition, namespace}`;
the first prompt sends `available_commands_update []` then the narrowed option (`Fixed for this
conversation.`) before anything else; `run.start.namespace` and `.decomposition` are the chosen ones; a
late command and a command with no task are answered with their sentences and run nothing; unknown
namespace, unknown option and `NAMESPACE_FIXED` refusals carry their sentences, codes and names. **6/6
passed** [CI, run]. The file's other six (a path as a task, `PROMPT_BUSY`, a missing key, a failed
drive, a failed `materialize`, the bridge's appended blocks) pass too and back §4.5 and D-1.

### 6.7 Replay and shutdown

`test_agent.py`: `dr-acp` SIGKILLed mid-prompt, a new one `session/load`s: both runs replay, the first
equal to the live tree, the second equal plus its `lost` closing message; the user's four prompts replay
as `user_message_chunk`; no `subagent_update` follows the response; the next prompt opens with
`FRESH_AFTER_RESTART`. `session/close` leaves `run.end closed` and the next run opens with
`FRESH_AFTER_CLOSE`. `test_wire.py`: stdin close and SIGTERM each leave `run.end closed` under 1.4 s,
exit 0. **All passed** [CI, run].

### 6.8 The live tier (gpt-6-luna, `docs/configs/advising`)

Run 37053166300 at `21f4a8b`, three tests, durations from the log's timestamps [CI]:

| Test | Asserts | Result |
|---|---|---|
| `test_live_the_stream_rebuilds_deep_reasoners_tree_and_the_root_pays_for_all` | `/compare-departments Which department is lighter for a first-year student, CS or STAT?` answers; the rebuilt tree equals deep_reasoner's with ≥ 3 agents; the answer names `STAT`; every call priced; root cost = sum of the log's call costs; every child cost strictly between 0 and the root's | passed, ~25 s |
| `test_live_stopping_a_department_stops_it_and_its_course_agents` | stop a department once a course agent is announced (interim): the root answers; `stop.accepted` for that node; the department and its course agents idle `cancelled`, `status: stopped`; at most one `usage` per branch node after the stop; the stop thought on the department | passed, ~10.7 s |
| `test_live_without_the_key_the_run_fails_before_any_call_and_says_which` | without `OPENAI_API_KEY`: `build_failed`, the sentence naming `OPENAI_API_KEY`, no `usage` in the log | passed, ~2.3 s |

The run's spend is not recorded: the tests assert relations between costs and print no amount. [CI, read]

---

## 7 · What I could not verify

- **The live tier and its cost**: not run here; results are GitHub's log [CI]. No amount was printed,
  so the cost per live run is unknown.
- **Dean's real `stop(node_id)`** does not exist at `d7334ae`; the Dean path runs only against the
  test fake, which fakes points 1–6 of design §6.3, not 7 (ending a `claude` process). [read]
- **The Claude backbone** runs only against deep_reasoner's fake `claude` CLI; its stop sentences are
  tested as text and selection, not end to end. [run for what is tested]
- **The weekly tripwire against Dean's `main`**: never run (D-16).
- **OpenHands' bridge**: no test runs against it. The prompt layout D-1 handles is reproduced from the
  bridge's source as constants (`harness.py:82–101`); the 2 s cancel drain, the 1,800 s idle watchdog
  and the ≤ 2 s wait for a root `usage_update` are the design's citations, not observed. [read]
- **gpt-6-luna's price** is from secondary listings (D-9); costs in the live tier are only as right as
  that table.
- **Paths I read but did not see run**: control-pipe EOF killing the worker's group; the 0.7 s
  `close_run` watchdog's exit 3; a decomposition that `main_decomposition_turns` cannot puppeteer
  answering `build_failed`; `CATALOG_ERROR` on `session/new`; `cost_source: "mixed"` reaching a client
  (the encoder's output was run, a client never saw it). [read]
- **Concurrency** of the recorder across sub-agent threads is exercised by the 20-way fan-outs; I did
  not test it beyond the suite.

If this document will not get shorter, the part that resists is §2: the build's divergences are many
and small, and each changes a sentence a collaborator (S1, C1, S2, D2, D5) may have read in the design.
