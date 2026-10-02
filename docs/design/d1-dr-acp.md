# D1 · `dr-acp` — design

**TASK-2** · System Designer · branch `v1-dr-acp` · against the approved spec
[TASK-1](https://app.notion.com/p/3ed62fb22237814ab425c81b3844f012) (D1, §2, D2's materialization,
D4's MCP note, §4, the 2026-10-02 amendment).
**Pinned against:** deep_reasoner_beta `d7334ae6ea884617a377d9f1ce872530d898484c` ·
`agent-client-protocol` 0.12.1 (the SDK fork's lock) · ACP schema 1.24.1 `schema.unstable.json`
(sha256 `6449a87a…09109e`) · SDK fork at `53a4bc5` (`acp_agent.py` line numbers; its
`deep-reasoning` branch adds only the ASE commit) · Canvas fork at `1ff45c2` (likewise).

**Revisions** (newest first; the Gate B reader approved the previous one, so each line says which
sentences to stop trusting):
- 2026-10-02 · v1 · first full-depth version.

**Where this file lives, and why nothing trips over it.** `docs/design/` on the task branch. This
repo has no docs site (no `mkdocs.yml`), pytest is pointed at `tests/` only
(`[tool.pytest.ini_options] testpaths = ["tests"]`, §8.5), the package uses a `src/` layout so
`docs/` is not in the wheel, and the sdist excludes `docs/` (§8.5). The PR split leaves it behind.

**Reading guide.** Gate B: §1–§3 (about 12 minutes). S1, C1 and S2 design against §5, which is
their contract. D2 against §4.6 and §4.4. D5 against §4.7. The Docwright and the Implementer read
everything; §7 is the signature index.

---

## 1 · What `dr-acp` is

A stdio ACP agent. Each ACP root session owns at most one live deep_reasoner **run**, executed in a
**worker** subprocess. The worker turns deep_reasoner's structlog events into our own
**RunEvents**; the front process writes them to the **run log** and only then encodes them as ACP.
Everything the client ever sees is a function of the run log.

```text
ACP client (agent-server bridge, S1)               $DR_HOME/
   │ stdio (JSON-RPC, ndjson)                         sessions/<session>.json      session index (§4.4)
   ▼                                                  runs/<run>/events.jsonl      RunEvents: the system of record
dr-acp front  (asyncio, one process per bridge)       runs/<run>/worker.log        worker stdout+stderr
   wire ── agent ── session ── run handle             runs/<run>/*.yaml            deep_reasoner's own node logs
                                 │   ▲
                 control pipe ───┘   └─── event pipe (RunEvents, JSON lines)
                                 ▼   │
                         worker  (python -m deep_reasoning.acp.worker; own process group)
                           runner: build_reasoner → acall(task) per prompt → close_run
                           recorder: structlog processor, deep_reasoner events → RunEvents
                           stop adapter: Dean's stop(node_id) | the interim
                           cwd = the conversation's workspace; stdin = /dev/null; stdout,stderr → worker.log
```

### 1.1 Decisions this design takes (the spec's seven in §2 stand; these are the next layer down)

| # | Decision | Why | Rejected |
|---|---|---|---|
| A | **The front is the run log's only writer.** The worker sends RunEvents over a dedicated pipe; the front appends each one to `events.jsonl` (fsync-free, flushed per line) *before* encoding it. | One writer, one order: the encoding of any prefix of the log is the prefix of the stream. Replay and live share one encoder. The worker's fd 1 can then be anything. | The worker writing `events.jsonl` and the front tailing it (polling latency, two writers once the front logs stops and kills). The spec's diagram drew the arrow through the file; the file still holds exactly what ACP saw, in that order. |
| B | **The worker normalizes; the front never reads deep_reasoner's event names.** The recorder (worker) owns every inference about deep_reasoner (which cell spawned whom, which reply is a think, what the answer was). The encoder (front) is a pure function of RunEvents. | A2 breaks land in one module. The run log is stable even when Dean's events move, so a later "save a run as a decomposition" reads our schema, not his. | Logging raw deep_reasoner events and interpreting them in the front. |
| C | **Every outgoing ACP message is raw JSON through one `Outbox`.** We build `acp.connection.Connection` around `build_agent_router` ourselves and never use `AgentSideConnection` (it is `@final` and its typed `session_update` cannot carry the unstable types). | One send path for stable and unstable updates; E4 validates that path; the `initialize` tap sits in our own handler, not in a private attribute. | Monkeypatching `conn._conn._handler` on an `AgentSideConnection`. |
| D | **Stdout is guarded at start-up.** `dr-acp` dups fd 1 for the ACP writer, then points fd 1 and `sys.stdout` at stderr. | A stray print anywhere in the front (an import, a library) cannot corrupt framing (E2). | Trusting that nothing prints. |
| E | **The worker runs in its own process group and is ended by group.** `start_new_session=True`; root Stop is SIGTERM, 0.8 s grace, SIGKILL. | Ends `claude` CLIs and other children (Dean's point 7 for the whole run); fits the bridge's 2 s cancel drain (§6.4). | SIGKILL at once (loses `close_run` even when the run could unwind). |
| F | **Ids are derived, not stored.** Child session = `<run>-n<node>`, cell = `<run>-n<node>-c<k>`. | Replay reproduces every id from the log alone; ids are unique across runs, sessions and connections; URL-safe for S1's cancel route. | Random ids with a mapping table. |
| G | **A cell is opened by the first evidence of it**: the agent's think reply, a puppeteered turn, or a child starting under a parent with no open cell (the code then arrives when the cell ends). | The one rule that covers the chat backbone, main decompositions and the Claude backbone, and guarantees a child's `parentToolCallId` always names a tool call already sent. | Opening cells only from `repl.execute`, which is logged after the cell ends (A6). |

### 1.2 What D1 owns, and what it leaves seams for

- **Owns:** the `dr-acp` command; the worker; the recorder; the run log and session index; the ACP
  encoding in both modes; slash commands from decompositions; the namespace option; cost per
  session; root Stop; per-sub-agent Stop through the stop adapter (Dean's API and the interim);
  `session/load` replay; this repo's first `pyproject.toml`, test suite and CI.
- **Seam for D2** (§4.6): `Catalog`, which the Library implements. Before D2, `ConfigCatalog`
  reads a plain `dr` config: `dr-acp --config path/main.yaml`.
- **Seam for D4** (§4.8): `Session.mcp_servers` is kept from `session/new`; D1 never passes it on
  and advertises `mcpCapabilities` http/sse false.
- **Seam for D5** (§4.7): `ModelRoute`, which the key proxy implements; `DR_HOME`; the worker's
  environment scrub.

---

## 2 · A conversation, end to end

The order below is the order on the wire. Names in `code` are RunEvents (§4.4) or ACP updates (§5).

1. **`initialize`.** The wire's tap reads `params.clientCapabilities.subagents` raw (0.12.1's
   `ClientCapabilities` drops it). Non-null object → **native** mode for this connection; anything
   else, or `dr-acp --flat` → **flat** mode. `dr-acp` advertises `loadSession`, `sessionCapabilities.close`,
   no MCP transports, text-only prompts.
2. **`session/new {cwd, mcpServers}`.** The front takes a catalog snapshot (namespaces, the
   default namespace, each namespace's commands; in a thread, since `ConfigCatalog` imports
   deep_reasoner). It answers with a session id and the `namespace` select option, then sends
   `available_commands_update` for the default namespace. No worker starts: a preview session
   (S2) costs a start-up and a catalog read.
3. **`session/set_config_option namespace=…`** before the first prompt: the commands update for the
   new namespace goes out, then the response with the full options.
4. **First prompt.** If its first token is an advertised command, the decomposition opens the run
   and the rest of the text is the task. The session becomes *started*: `available_commands_update []`
   and a `config_option_update` narrowing `namespace` to the chosen one go out first. The front
   materializes the run (`Catalog.materialize`), creates `runs/<run>/`, logs `run.start`, spawns the
   worker, sends it `start` and `prompt`.
5. **The run.** The worker builds the reasoner with `build_reasoner(…, main_decomposition=…)`,
   enters its alias for the whole run, and calls `reasoner.acall(task)`. The recorder emits
   `agent.start`, `thought`, `cell.start`, `usage`, `cell.end`, `agent.end` …; the front logs and
   encodes each: the root's think as `agent_thought_chunk`, each cell as a `tool_call` completed by a
   `tool_call_update`, each sub-agent as a child session announced on its parent with
   `_meta.openhands.parentToolCallId` naming the spawning cell (native), or as labelled cards and
   cells on the root (flat).
6. **Answer.** `prompt.end` → the root's `agent_message_chunk`, the root's `usage_update`, then the
   `session/prompt` response (`end_turn`, or `max_turn_requests` when exhausted). The worker stays
   up with the REPL.
7. **Later prompts** resume the same reasoner (`acall` again), as `dr --interactive` does. A slash
   command now gets the "only works as the first message" reply and no run traffic.
8. **Stop on a sub-agent** (`session/cancel` with a child's session id): the front logs
   `stop.request` and tells the worker; the stop adapter calls Dean's `stop(node_id)` or arms the
   interim. The child's session gets a thought saying when the stop lands; each agent of the branch
   turns `idle`/`cancelled` as it actually ends (the RFD: evidence, not acknowledgement).
9. **Stop on the root:** the worker's process group is terminated within 2 s; every running child
   turns `idle`/`cancelled`, unfinished cells fail, the root says the REPL state is gone, and the
   prompt answers `cancelled`. The next prompt starts a fresh run and says so.
10. **Restart.** The bridge calls `session/load`; `dr-acp` replays every run of the session from the
    run log (user prompts included) before answering, marks a run that never ended as `lost`, and
    the next prompt starts fresh.

---

## 3 · Where this design departs from, or adds to, the approved spec

Each is a refinement inside D1's scope, not a re-scope. If the Conductor reads any as a change of
what was approved, it goes back to Michael.

1. **The run log is written by the front, not the worker** (decision A). The spec's §2 diagram
   draws "processor → events.jsonl → dr-acp". The file and its role are unchanged.
2. **Commands are cleared at the start of the first prompt, not at its end** as the D1 mock-up
   prints them. A menu must not offer a decomposition while the run that can no longer take one is
   already starting (C2's falsifier).
3. **Cell titles start `Run `, not `RUN `.** Canvas's ACP card renders execute calls through a
   "Running …" template and strips a leading `Run ` (case-sensitive,
   `get-acp-tool-call-content.ts`); `RUN` would print "Running RUN cs = …" in stock Canvas and in
   C1, which reuses the card. Flat titles become `#1 › #3 › Run …`.
4. **The flat stream also carries one card per sub-agent** (a `tool_call` of kind `other` on the
   root, titled `#1 › #3 · <task>`, completed with the answer). The spec names only the labelled
   cells. Without the cards, a sub-agent with no cell is invisible in flat mode (E1 could not
   rebuild its parent link) and a stock client never sees a child's answer or failure. About 30
   lines.
5. **A failed sub-agent sends `Failed: <detail>` back to its parent as a `session_message`.** The
   spec sends a message back only for an answer. A generic client (C1 reads no
   `_meta.deep_reasoner`) otherwise shows a failed child as an ordinary `idle`/`end_turn` with no
   output.
6. **The root's cost is the whole conversation, not only the current run.** ACP's `cost` is
   cumulative per session and the bridge books deltas per session (`_record_usage`); after a root
   Stop the next run's root cost continues from the previous total. Children are per run.
7. **`_meta.deep_reasoner` on an announcement adds `backbone` and `drive`** to the mock-up's `run`,
   `node`, `parent`, `depth`, `namespace`; idle updates add `status`, `detail`, `stopped_by`. A
   superset; nothing in the mock-up changes meaning.
8. **The worker does not call `load_dotenv`.** `dr` does, but python-dotenv searches upward from
   the file of the module that calls it (`find_dotenv`), not from the workspace; under `dr-acp` it
   would load whatever `.env` sits above wherever the app was installed. In the desktop app keys
   must come only from the environment (D5).
9. **A Stop request is acknowledged on the child's own session** with a thought saying when it
   lands (next turn; for a Claude-backbone agent, when its Claude session ends). The spec asks that
   the interim's differences be "said where the user sees them"; this is where.
10. **Root Stop answers within 2 s, and E3 tests 2 s, not 5.** The bridge restarts the agent when a
    cancelled prompt has not answered within 2 s (`_ACP_CANCEL_DRAIN_TIMEOUT`); a slower Stop would
    work but cost a restart and a replay.
11. **A prompt `dr-acp` rejects without running anything** (a late slash command, a command with no
    task) is answered but not recorded: no run log holds it, so it does not replay after a restart.

---

## 4 · Modules and seams

### 4.1 Package layout (this repo's first code)

```text
pyproject.toml                     deep-reasoning 0.1.0, src layout, script dr-acp (§8.5)
src/deep_reasoning/__init__.py
src/deep_reasoning/acp/
    __init__.py                    __version__
    cli.py                         dr-acp: options, stdout guard, logging, serve()
    wire.py                        Connection + router tap, Outbox, ClientMode
    agent.py                       DrAcpAgent: the ACP methods
    session.py                     Session: options, commands, prompt state machine, runs
    supervisor.py                  RunHandle: spawn, pipes, pump, stop, kill, close
    runlog.py                      RunEvent models, RunLog, SessionIndex, Home
    encoder.py                     Encoder: RunEvents → ACP updates (native, flat, replay)
    ids.py                         id derivation and the short forms the printer uses
    catalog.py                     Catalog protocol, CatalogSnapshot, ConfigCatalog
    route.py                       ModelRoute protocol, DirectRoute, environment scrub
    costs.py                       PriceTable, CostEstimate
    prices.yaml                    shipped price and context-window table
    texts.py                       every user-visible sentence (§5.6), one place
    worker/__main__.py             python -m deep_reasoning.acp.worker
    worker/runner.py               control loop, build, drive, close
    worker/recorder.py             Recorder (the structlog processor)
    worker/stop.py                 StopAdapter, DeanStop, InterimStop, StoppedByUser
    worker/protocol.py             control messages (front → worker)
    testing/__init__.py            for tests and the live doc, never imported by dr-acp itself
    testing/client.py              ShimConnection, Caps, Printer, tree() (§8.2)
    testing/fake_model.py          FakeOpenAI: an OpenAI-compatible endpoint on 127.0.0.1
tests/acp/…                        §8
```

`dr-acp` never imports OpenHands. The front imports deep_reasoner only inside `ConfigCatalog`
(and, after D2, the Library); it never builds or drives an agent.

### 4.2 The front

**`cli.py`.** Parses options, applies the stdout guard (decision D), configures stdlib logging to
stderr (the bridge logs our stderr at INFO, so the default level is WARNING), builds the catalog,
the route and the agent, and runs `wire.serve`. On stdin EOF it closes every session (graceful
close, 2 s, then kill) and exits 0.

```python
@dataclass(frozen=True)
class Options:
    config: Path | None          # --config PATH: a plain dr main.yaml (ConfigCatalog). Required until D2.
    home: Path                   # --home DIR, else $DR_HOME, else ~/.deep-reasoning
    flat: bool                   # --flat: never send sub-agent sessions, whatever the client advertises
    heartbeat_s: float           # --heartbeat SECONDS (default 60)
    log_level: str               # --log-level (default WARNING)

def main(argv: Sequence[str] | None = None) -> int: ...
def guard_stdout() -> int:        # returns the dup of the original fd 1, for the ACP writer
    """os.dup(1) → acp_fd; os.dup2(2, 1); sys.stdout = sys.stderr. Called before any other import of ours."""
```

Before D2 lands, `dr-acp` without `--config` exits 2 with
`dr-acp needs --config PATH (a dr main.yaml) until the Library exists.` D2 makes the Library the default.

**`wire.py`.** The connection, the `initialize` tap and the single send path.

```python
Mode = Literal["native", "flat"]

class Outbox:
    """Every byte dr-acp sends to the client goes through here, in call order."""
    def __init__(self, conn: acp.connection.Connection) -> None: ...
    async def update(self, session_id: str, update: Mapping[str, Any]) -> None:
        """session/update notification, raw JSON: {"sessionId": session_id, "update": update}."""
    def observe(self, fn: Callable[[dict[str, Any]], None]) -> None:
        """Tests and golden recording: fn sees every outgoing JSON-RPC message (Connection observers)."""
    @property
    def seconds_since_last_send(self) -> float: ...

async def serve(make_agent: Callable[[Outbox, ClientMode], "DrAcpAgent"], *,
                acp_out_fd: int, stdin_fd: int = 0) -> None:
    """Build asyncio streams on (stdin_fd, acp_out_fd) with a 64 MiB reader limit, then
    Connection(handler, writer, reader), where handler = tap ∘ build_agent_router(agent,
    use_unstable_protocol=True). Returns when the client closes stdin."""

class ClientMode:
    """Decided once per connection, by the tap, before the router sees initialize."""
    mode: Mode                   # "native" iff clientCapabilities.subagents is a JSON object and not --flat
```

`use_unstable_protocol=True` is needed for `session/close` (S2's preview closes its probe
session). Unimplemented unstable methods (`fork`, `resume`, `list`) answer method-not-found.

**`agent.py`.** The ACP surface. Handlers get the router's keyword arguments and return raw dicts.

```python
class DrAcpAgent:
    def __init__(self, outbox: Outbox, client: ClientMode, *, catalog: Catalog, home: Home,
                 route: ModelRoute, prices: PriceTable, heartbeat_s: float) -> None: ...
    async def initialize(self, protocol_version: int, client_capabilities: Any = None,
                         client_info: Any = None, **meta: Any) -> dict: ...                 # §5.1
    async def new_session(self, cwd: str, mcp_servers: list[Any],
                          additional_directories: list[str] | None = None, **meta: Any) -> dict: ...
    async def load_session(self, cwd: str, session_id: str, mcp_servers: list[Any],
                           additional_directories: list[str] | None = None, **meta: Any) -> dict: ...
    async def set_config_option(self, config_id: str, session_id: str, value: str, **meta: Any) -> dict: ...
    async def prompt(self, prompt: list[Any], session_id: str, **meta: Any) -> dict: ...
    async def cancel(self, session_id: str, **meta: Any) -> None: ...                        # root or child
    async def close_session(self, session_id: str, **meta: Any) -> dict: ...
```

`cancel` routes by id: a root session id → `Session.stop_root()`; an id in any live run's child
map → `Session.stop_child()`; anything else is ignored (it is a notification; a cancel racing an
ended agent does not rewrite its outcome).

**`session.py`.** One per root session; holds the options, the commands and the runs; serializes
`prompt`, `set_config_option`, `load` and `close` with an `asyncio.Lock` (`cancel` never takes it).

```python
@dataclass
class Session:
    id: str                              # "s-" + 16 hex
    cwd: Path
    snapshot: CatalogSnapshot
    namespace: str
    started: bool                        # set by the first accepted prompt; the namespace is fixed from then on
    commands: dict[str, CommandEntry]    # by command name, for the current namespace; empty once started
    advertised: set[str]                 # every command name this session has offered: detects late commands
    runs: list[str]                      # run ids, oldest first
    cost: CostLedger                     # the root's cumulative cost over all finished runs
    last_end: RunEndReason | None        # how the previous run ended: chooses the fresh-run notice
    mcp_servers: list[dict[str, Any]]    # kept for D4; unused in D1
    run: RunHandle | None                # the live run, if any
    ctx: "AgentContext"                  # shared from DrAcpAgent: catalog, home, route, outbox, prices, mode, heartbeat_s

    async def prompt(self, text: str) -> PromptResult: ...
    def set_namespace(self, value: str) -> list[dict]: ...      # raises RequestError (§5.6)
    async def stop_root(self) -> None: ...
    def stop_child(self, child_session_id: str) -> None: ...
    async def close(self) -> None: ...

@dataclass(frozen=True)
class PromptResult:
    stop_reason: Literal["end_turn", "max_turn_requests", "cancelled"]
    run: str | None
    outcome: Literal["answered", "exhausted", "failed", "build_failed", "stopped", "crashed",
                     "closed", "rejected"]
```

`Session.prompt`, exactly:
1. Refuse if a prompt is in flight (`RequestError.invalid_request`, §5.6).
2. Text = the prompt's `text` blocks joined with `"\n"`; a `resource_link` block contributes its
   `uri` on its own line; other blocks are ignored (we advertise none).
3. Command parse: if the text starts with `/` and its first whitespace-separated token minus the
   slash is a name in `self.commands`, it is a command; otherwise, if the session has started and
   that token is in `self.advertised`, it is a *late* command; otherwise it is plain text (a path
   such as `/home/…` stays a task).
   - Late command → reply `texts.LATE_DECOMPOSITION`, outcome `rejected`, no run.
   - Command with an empty rest → reply `texts.COMMAND_NEEDS_TASK`, outcome `rejected`, session
     stays unstarted.
4. If not started: started = True; send `available_commands_update []` then the narrowed
   `config_option_update`; write the session index.
5. If `self.run` is None: send the fresh-run notice for `self.last_end`, if it has one (§5.6);
   `run_id = ids.new_run_id()`; `source = await asyncio.to_thread(catalog.materialize, namespace,
   run_dir=home.run_dir(run_id))` (an exception → reply `texts.BUILD_FAILED`, outcome
   `build_failed`, no run); `self.run = await RunHandle.start(run_id=run_id, source=source, …)`.
6. `await self.run.prompt(index, text, task, decomposition)` → `PromptEnd`.
7. Every return path, `rejected` included, sends the root `usage_update` before returning: the
   bridge waits up to 2 s for one after every prompt (`acp_agent.py:3643–3654`).

When the pump feeds a `run.end`, the session takes `cost = encoder.root_cost`, `last_end = reason`,
`run = None`, and saves the index. `stop_root` with no prompt in flight does nothing: the REPL
survives between prompts.

**`supervisor.py`.** A live run: the worker process, its two pipes, the pump.

```python
class RunHandle:
    run_id: str
    encoder: Encoder
    @classmethod
    async def start(cls, *, run_id: str, session: Session, source: RunSource, home: Home,
                    route: ModelRoute, outbox: Outbox, mode: Mode, heartbeat_s: float) -> "RunHandle":
        """RunLog.create; append run.start; grant = route.grant(session=…, run=run_id,
        upstream=source.client); spawn the worker (sys.executable -m deep_reasoning.acp.worker
        --control-fd C --events-fd E, pass_fds=(C, E), start_new_session=True, stdin=DEVNULL,
        stdout=stderr=runs/<run>/worker.log, cwd=session.cwd, env=worker_env(os.environ, grant));
        send Start(client_overrides=grant.client_overrides, …); start the pump and the heartbeat."""
    async def prompt(self, index: int, text: str, task: str, decomposition: str | None) -> PromptEnd: ...
    def stop_node(self, node: int) -> None:            # logs stop.request, sends Stop; returns at once
    async def kill(self, reason: Literal["stopped", "closed"]) -> None:   # §6.4; idempotent
    async def close(self) -> None:                     # Close op, 2 s, then kill("closed")
    def child(self, session_id: str) -> ChildRef | None:   # for cancel routing
```

The **pump** is one task per run: read a line from the event pipe → parse a RunEvent (an
unparseable line is logged to stderr and dropped) → `RunLog.append` → `Encoder.feed` → `await
Outbox.update` for each result, in order → resolve the prompt future on `prompt.end`. It also
calls `Encoder.flush_usage()` at most every 0.5 s. On EOF it waits for the process; if no `run.end`
was logged it appends `run.end {reason: crashed, exit_code}` (or `stopped`/`closed` when the front
asked for the exit) and feeds it. The **heartbeat** task, while a prompt is in flight, sends the
root's `usage_update` when `Outbox.seconds_since_last_send ≥ heartbeat_s`, which keeps the bridge's
1,800 s prompt-idle watchdog quiet through a long cell (`acp_agent.py:1433–1439, 1758`).

### 4.3 The worker

**`worker/protocol.py`** — front → worker, one JSON object per line on the control pipe:

```python
class Start(BaseModel):    op: Literal["start"]; run: str; session: str; run_dir: str
                           config_path: str; namespace: str; client_overrides: dict[str, Any]
class Prompt(BaseModel):   op: Literal["prompt"]; prompt: int; task: str; decomposition: str | None
class Stop(BaseModel):     op: Literal["stop"]; node: int
class Close(BaseModel):    op: Literal["close"]
Control = Annotated[Start | Prompt | Stop | Close, Field(discriminator="op")]
```

Worker → front: RunEvents (§4.4) without `seq`/`t`, which the front assigns.

**`worker/runner.py`**, in order:
1. A reader thread on the control pipe. `Stop` is handled *on that thread* by
   `StopAdapter.stop(node)` (Dean's point 1: callable from any thread). `Prompt`/`Close` go to the
   main loop through `loop.call_soon_threadsafe`. EOF (the front died) → `os.killpg(0, SIGKILL)`.
2. On `Start` (the process already runs in the session's `cwd`): `set_cache_dir(None)`;
   `quiet_http_client_logs()`;
   `configure_structlog_fixture(console=False, extra_processors=[recorder, LogProcessor(run_dir.parent)],
   default_level=logging.WARNING)`; a SIGTERM handler that raises `RunKilled(BaseException)` in the
   main thread; emit `worker.ready {pid, deep_reasoner, stop_mode}`.
3. On the first `Prompt`: `cfg = load_cli_config(config_path, schema=V2Config)`; resolve a relative
   `namespaces_dir` against the config's directory (as `dr` does, `cli.py:696–697`);
   `cfg.entry_namespace = namespace`; `cfg.client = cfg.client.model_copy(update=client_overrides)`;
   if a decomposition: `cfg.task = task` and the recorder is given the puppeteered turns,
   `main_decomposition_turns(decomposition, task, cfg.decompositions,
   build_namespace_registry(cfg).resolve(namespace).decompositions,
   template_vars=cfg.prompt_template_variables)` (the registry closed after);
   `reasoner, alias = build_reasoner(cfg, run_dir=run_dir, main_decomposition=decomposition)`.
   Any exception here → `prompt.end {outcome: build_failed, detail}` and exit 2.
4. Enter `bound_contextvars(task_id=run, log_dir=run_dir)` and `alias` once, for the whole run.
   Each `Prompt`: `answer = await reasoner.acall(task)`; emit
   `prompt.end {outcome: exhausted if reasoner.exhausted else answered, answer: as_text(answer)}`.
   An exception from `acall` → `prompt.end {outcome: failed, detail}`, then teardown and exit 1:
   after a raising drive the agent's `_done` stays false, so a later `send` would never reach the
   model (`agent.py:867–872, 749`).
5. Teardown (`Close`, failure, `RunKilled`): `close_run(reasoner)` under a 0.7 s watchdog thread that
   `os._exit(3)`s past it; then `os._exit(0)` (never wait for non-daemon sub-agent threads).

`as_text(value) = value if isinstance(value, str) else repr(value)`; the same rule unquotes a
child's answer (§6.1).

**`worker/recorder.py`** — §6.1. **`worker/stop.py`** — §6.3.

### 4.4 The run log

**Home.** `$DR_HOME` (default `~/.deep-reasoning`; D5 sets it): `sessions/<session>.json`,
`runs/<run>/events.jsonl`, `runs/<run>/worker.log`, and deep_reasoner's own files in the same run
directory (its `LogProcessor` writes `{runs}/{task_id}/`, and `task_id` is the run id; a Claude
backbone serves its runtime from the same directory, as under `dr`).

**Run id**: `YYYYmmdd-HHMMSS-<6 hex>`, made by the front (deep_reasoner's slug format; deep_reasoner's
own `run` slug is recorded in `agent.start` as `dr_run`).

**`events.jsonl`**: one RunEvent per line, `{"v": 1, "seq": n, "t": unix_seconds, "kind": …, …}`.
`seq` is the front's append counter, gap-free per run. Text fields are capped at 8 MiB by the
recorder (head and tail kept, `… N bytes elided …` between).

```python
class _Ev(BaseModel):
    v: Literal[1] = 1
    seq: int = 0            # set by RunLog.append
    t: float = 0.0          # set by RunLog.append

# front-originated
class RunStart(_Ev):     kind: Literal["run.start"];  run: str; session: str; index: int  # 1-based in the session
                         cwd: str; namespace: str; mode: Mode; decomposition: str | None
                         source: dict[str, Any]       # RunSource as JSON: config_path, client, versions
class PromptStart(_Ev):  kind: Literal["prompt.start"]; prompt: int; text: str; task: str; decomposition: str | None
class StopRequest(_Ev):  kind: Literal["stop.request"]; node: int
class RunEnd(_Ev):       kind: Literal["run.end"]; reason: RunEndReason; exit_code: int | None; detail: str | None
RunEndReason = Literal["closed", "stopped", "crashed", "failed", "build_failed", "lost"]

# worker-originated
class WorkerReady(_Ev):  kind: Literal["worker.ready"]; pid: int; deep_reasoner: str; stop_mode: Literal["dean", "interim"]
class AgentStart(_Ev):   kind: Literal["agent.start"]; node: int; parent: int | None
                         ancestry: list[int]          # agent nodes only, root first, ending in node
                         depth: int                   # len(ancestry): the root is 1
                         task: str; namespace: str; backbone: str   # "chat" | "claude_code" | class name
                         max_iter: int | None; drive: int           # 1 on the first drive of this node
                         parent_cell: int | None      # the parent's open cell; None for the root
                         dr_run: str | None
class Thought(_Ev):      kind: Literal["thought"]; node: int; text: str
class CellStart(_Ev):    kind: Literal["cell.start"]; node: int; cell: int  # 1-based per node
                         code: str                    # "" while unknown (origin "inferred")
                         origin: Literal["think", "puppeteered", "inferred"]
class CellEnd(_Ev):      kind: Literal["cell.end"]; node: int; cell: int; code: str
                         output: str                  # the observation without its <observation> wrapper
                         interrupted: bool = False    # the agent ended before the cell reported
class Usage(_Ev):        kind: Literal["usage"]; node: int  # the owning agent
                         call: Literal["think", "tool", "claude"]; model: str | None
                         tokens_in: int; tokens_out: int; cost_usd: float | None
                         cost_source: Literal["provider", "table", "claude"] | None
                         context_window: int | None
class StopAccepted(_Ev): kind: Literal["stop.accepted"]; node: int; mode: Literal["dean", "interim"]
                         accepted: bool; reason: str | None; backbone: str | None
class AgentEnd(_Ev):     kind: Literal["agent.end"]; node: int
                         status: Literal["done", "exhausted", "failed", "stopped"]
                         dr_status: str               # deep_reasoner's own: done|exhausted|failed|stopped
                         iter: int | None; answer: str | None; detail: str | None
                         stopped_by: int | None       # the node the user stopped, when status is stopped
                         collateral: bool = False     # interim: cancelled because a sibling was stopped
class PromptEnd(_Ev):    kind: Literal["prompt.end"]; prompt: int
                         outcome: Literal["answered", "exhausted", "failed", "build_failed"]
                         answer: str | None; detail: str | None

RunEvent = Annotated[RunStart | PromptStart | StopRequest | RunEnd | WorkerReady | AgentStart |
                     Thought | CellStart | CellEnd | Usage | StopAccepted | AgentEnd | PromptEnd,
                     Field(discriminator="kind")]

class RunLog:
    @classmethod
    def create(cls, home: Home, run_id: str) -> "RunLog": ...
    def append(self, ev: RunEvent) -> RunEvent: ...           # assigns seq and t, writes one line, flushes
    @staticmethod
    def read(home: Home, run_id: str) -> Iterator[RunEvent]: ...  # raises on v != 1
```

**Session index** `sessions/<session>.json`, written atomically (temp + rename), first at the first
prompt (so S2's preview sessions leave nothing), then at every run start and end:

```json
{"v": 1, "session": "s-7c1f9e0a2b4d6e8f", "cwd": "/workspace", "namespace": "router",
 "started": true, "source": {"kind": "config", "config_path": "/abs/main.yaml"},
 "runs": ["20261002-142233-4f1a2b"], "cost": {"usd": 0.0041, "complete": true,
 "tokens_in": 9120, "tokens_out": 1388}, "last_end": "stopped", "created": "2026-10-02T14:22:31Z"}
```

What D2 needs from the log: `run.start.source.versions` holds whatever `Catalog.materialize`
returned (D2: the library versions the run used), and `run.start.namespace` is the namespace the
run used (E8, E11).

### 4.5 The encoder

Pure: no I/O, no clock. One per run, plus one per run in a replay.

```python
Update = tuple[str, dict[str, Any]]          # (sessionId, the "update" object of session/update)

class Encoder:
    def __init__(self, *, root: str, run: str, mode: Mode, replay: bool = False,
                 carry: CostLedger = CostLedger()) -> None: ...
    def feed(self, ev: RunEvent) -> list[Update]: ...       # §5.2 (native), §5.3 (flat)
    def flush_usage(self) -> list[Update]: ...              # usage_update for sessions whose totals changed
    def root_usage(self) -> Update: ...                     # the root's usage_update, always
    def child(self, session_id: str) -> "ChildRef | None": ...
    @property
    def root_cost(self) -> CostLedger: ...                  # carry + this run's root total

@dataclass(frozen=True)
class ChildRef: node: int; running: bool

@dataclass(frozen=True)
class CostLedger:
    usd: float = 0.0
    complete: bool = True        # False once any contributing call had no cost estimate
    tokens_in: int = 0
    tokens_out: int = 0
```

### 4.6 The catalog: the seam to D2

```python
class Catalog(Protocol):
    def snapshot(self) -> "CatalogSnapshot": ...                       # blocking; run in a thread
    def materialize(self, namespace: str, *, run_dir: Path) -> "RunSource": ...   # blocking

@dataclass(frozen=True)
class CatalogSnapshot:
    namespaces: tuple[str, ...]                     # "root" first, then by name
    default_namespace: str
    commands: Mapping[str, tuple["CommandEntry", ...]]   # namespace → its commands, menu order

@dataclass(frozen=True)
class CommandEntry:
    name: str            # the slash command, without "/": slug of the decomposition name
    decomposition: str   # the name deep_reasoner looks up (main_decomposition_turns)
    description: str     # the use-when line
    hint: str            # shown until the task is typed

@dataclass(frozen=True)
class RunSource:
    config_path: Path                 # a plain dr main.yaml the worker loads
    namespace: str                    # becomes cfg.entry_namespace
    client: Mapping[str, Any]         # the config's client block as loaded (base_url, api_key_env): D5's upstream
    versions: Mapping[str, Any]       # recorded in run.start; ConfigCatalog: {"config_sha256": …}
```

**`ConfigCatalog(path)`** (before D2): `load_cli_config(path, schema=V2Config)` with the relative
`namespaces_dir` resolved as `dr` does; `registry = build_namespace_registry(cfg)`; namespaces =
`root` ∪ `cfg.namespaces` keys ∪ the names in `load_namespaces_from_dir(cfg.namespaces_dir)`;
default = `cfg.entry_namespace`; for each namespace, commands = the decompositions
`main_decomposition_turns` can find for that entry namespace, in its lookup order:
`cfg.decompositions` first, then `registry.resolve(ns).decompositions`, first occurrence of a name
wins (`find_decomposition`, `decompositions.py:117`). This answers the spec's deferred "how
top-level decompositions combine with a namespace's": they are offered in every namespace, ahead of
the namespace's own, and shadow a namespace decomposition of the same name. `registry.close()`
afterwards. `materialize` returns the given path unchanged, with its sha256.

Command fields before D2: `name = slug(decomposition)` (lower case, runs of non-alphanumerics → `-`,
trimmed; a collision gets `-2`, `-3` in menu order); `description = f"Open with the
'{decomposition}' decomposition"` (a plain `dr` config has no use-when line); `hint = "the task"`.
D2's Library supplies the use-when line (its metadata column) and may supply a hint.

**D2 implements `Catalog`**, with `materialize` writing the plain `dr` config directory into
`run_dir / "config"` and returning its `main.yaml`, the profile's client block and the versions it
used. Nothing in D1 changes when D2 lands except the default in `cli.py`.

### 4.7 Model route and costs: the seam to D5

```python
class ModelRoute(Protocol):
    def grant(self, *, session: str, run: str, upstream: Mapping[str, Any]) -> "RouteGrant": ...
    def release(self, run: str) -> None: ...

@dataclass(frozen=True)
class RouteGrant:
    client_overrides: Mapping[str, Any]     # merged over cfg.client in the worker (D5: base_url, api_key_env)
    env_add: Mapping[str, str]              # added to the worker's environment (D5: the per-session token)
    env_remove: frozenset[str]              # removed from it (D5: the provider keys)

ALWAYS_REMOVED: tuple[str, ...] = ("OH_SECRET_KEY", "OH_SESSION_API_KEYS_*", "SESSION_API_KEY")  # globs

class DirectRoute:                          # D1's only route: no overrides; the keys stay in the environment
    def grant(self, *, session: str, run: str, upstream: Mapping[str, Any]) -> RouteGrant: ...
    def release(self, run: str) -> None: ...

def worker_env(base: Mapping[str, str], grant: RouteGrant) -> dict[str, str]:
    """base minus ALWAYS_REMOVED minus grant.env_remove, plus grant.env_add, plus PYTHONUNBUFFERED=1."""
```

The agent-server's own secrets (`OH_SECRET_KEY`, `OH_SESSION_API_KEYS_0`, which every ACP agent
inherits) never reach the worker, from D1 on. D5 adds `ProxyRoute` and the spend cap; until then
the worker reads the provider key from its environment, as `dr` does.

**`costs.py`.** Chat-backbone cost is an estimate until A7.

```python
@dataclass(frozen=True)
class Price:
    input_per_mtok: float; output_per_mtok: float; context_window: int | None

@dataclass(frozen=True)
class CostEstimate:
    usd: float | None
    source: Literal["provider", "table", "claude"] | None
    tokens_in: int; tokens_out: int
    context_window: int | None

class PriceTable:
    @classmethod
    def load(cls, home: Home) -> "PriceTable": ...      # package prices.yaml, then $DR_HOME/prices.yaml over it
    def estimate(self, model: str | None, usage: Mapping[str, Any]) -> CostEstimate: ...
```

`estimate`: `usage["cost"]` when the provider reports it (OpenRouter) → source `provider`; else the
table entry whose key equals the model id, or is the longest matching `*`-glob → source `table`;
else `usd=None`. Tokens: `prompt_tokens`/`input_tokens` and `completion_tokens`/`output_tokens`,
as `RunStats.add_usage` reads them (`run_stats.py:52–61`). Claude spend is exact: `claude.call`'s
`cost_usd`, source `claude`. `prices.yaml` ships entries with `source` and `as_of` for each; the
Implementer fills `gpt-6-luna` from OpenAI's price page (§10).

### 4.8 `mcpServers`: the seam to D4

`new_session`/`load_session` store the forwarded `mcpServers` on the `Session`; D1 passes nothing
to the worker and advertises `mcpCapabilities: {http: false, sse: false}`, so OpenHands forwards
only stdio servers (`_mcp_config_to_acp_servers`, `acp_agent.py:739–821`). D4 adds the ≈30 lines
that hand the granted ones to the worker (a `Start.mcp_servers` field) and flip the two flags.

---

## 5 · The ACP contract

This section is what S1, C1 and S2 build against. Every example below validates against schema
1.24.1's `schema.unstable.json` (`SessionNotification` for updates, the named response types for
responses; checked 2026-10-02 with `jsonschema` 4.26).

### 5.1 Capabilities and ids

`initialize` → 

```json
{"protocolVersion": 1,
 "agentCapabilities": {"loadSession": true,
   "promptCapabilities": {"image": false, "audio": false, "embeddedContext": false},
   "mcpCapabilities": {"http": false, "sse": false},
   "sessionCapabilities": {"close": {}}},
 "agentInfo": {"name": "dr-acp", "title": "deep_reasoner", "version": "<package version>"},
 "authMethods": []}
```

| Thing | Id | Example (run `20261002-142233-4f1a2b`) | Printer short form |
|---|---|---|---|
| root session | `s-` + 16 hex, made at `session/new` | `s-7c1f9e0a2b4d6e8f` | `root` |
| child session | `<run>-n<node>` | `20261002-142233-4f1a2b-n2` | `n2` |
| cell (`toolCallId`) | `<run>-n<node>-c<k>`, k from 1 per node | `20261002-142233-4f1a2b-n1-c1` | `c1.1` |
| flat agent card | `<run>-n<node>-a<drive>` | `…-n2-a1` | `a2.1` |
| task message (parent's transcript) | `<run>-n<node>-t<drive>` | `…-n2-t1` | — |
| answer message (child's transcript) | `<run>-n<node>-r<drive>` | `…-n2-r1` | — |

`node` is deep_reasoner's `node_id`. Node ids are shared with the LLM and Claude nodes deep_reasoner
allocates, so sibling agents need not be consecutive (`#1 › #2`, then `#1 › #4`). The printer's
short forms are what the spec's mock-ups print.

### 5.2 Emission table, native mode

`S(n)` is node n's session (the root session for the root). `cellId(n, k)` and the message ids are
§5.1's. `DR` below is `{"run", "node", "parent", "depth", "namespace", "backbone", "drive"}` from
the node's `agent.start`. Every row is sent in this order, before anything the next RunEvent
produces.

| RunEvent | Sent (session → update) |
|---|---|
| first prompt accepted | `root` → `available_commands_update` `{"availableCommands": []}`; `root` → `config_option_update` with `namespace` narrowed to the chosen value |
| `agent.start` (root) | nothing |
| `agent.start` (child, drive 1) | `S(parent)` → `subagent_update` `{"sessionId": S(node), "title": T, ["description": task,] "capabilities": {"cancel": {}}, "state": {"state": "running"}, "_meta": {"openhands": {"parentToolCallId": cellId(parent, parent_cell)}, "deep_reasoner": DR}}`; then `S(parent)` → `session_message` `{"messageId": "<S(node)>-t1", "senderSessionId": S(parent), "recipientSessionId": S(node), "content": [{"type": "text", "text": task}]}` |
| `agent.start` (child, drive d > 1: the same child given new work) | `S(parent)` → `subagent_update` `{"sessionId", "title": T, "state": {"state": "running"}, "_meta": {…the current parent cell…, DR with drive d}}`; then the task `session_message` with id `-t<d>` |
| `thought` | `S(node)` → `agent_thought_chunk` `{"content": {"type": "text", "text": …}}` |
| `cell.start` | `S(node)` → `tool_call` `{"toolCallId": cellId, "title": "Run <first line>[ …]" or "Run …" when the code is unknown, "kind": "execute", "status": "in_progress", "rawInput": {"command": code}, "_meta": {"deep_reasoner": {"run", "node", "parent", "depth", "cell", "origin"}}}` |
| `cell.end` | `S(node)` → `tool_call_update` `{"toolCallId", "status": "completed", "content": [{"type": "content", "content": {"type": "text", "text": out}}], "rawOutput": out}`, adding `"title"` and `"rawInput"` when the start had no code; `interrupted` → `"status": "failed"` and the text `texts.CELL_INTERRUPTED` |
| `usage` | nothing at once; the session and all its agent ancestors become dirty (§6.2) |
| (pump, ≤ every 0.5 s) | each dirty session → `usage_update` (§6.2) |
| `stop.accepted` | `S(node)` → `agent_thought_chunk` with `texts.stop_requested(mode, backbone)` (§5.6); nothing when `accepted` is false |
| `agent.end` (child) | if `answer`: `S(node)` → `session_message` `{"messageId": "<S(node)>-r<d>", "senderSessionId": S(node), "recipientSessionId": S(parent), "content": [text answer]}`; if `failed`: the same with `texts.CHILD_FAILED`; then `S(node)` → its final `usage_update`; then `S(parent)` → `subagent_update` `{"sessionId": S(node), "state": {"state": "idle", "stopReason": R}, "_meta": {"openhands": {…}, "deep_reasoner": DR + {"status", ["detail",] ["stopped_by",]}}}` with R from the table below. An open cell of the node is first closed as `interrupted`. |
| `agent.end` (root) | nothing (`prompt.end` speaks for the root) |
| `prompt.start` | nothing live; in a replay, `root` → `user_message_chunk` with `text` |
| `prompt.end` | `root` → `agent_message_chunk` with `answer` (answered, exhausted), `texts.ROOT_FAILED` (failed) or `texts.BUILD_FAILED` (build_failed); then `root` → `usage_update`. The prompt's response follows. |
| `run.end` while a prompt is in flight (`stopped`, `crashed`, `closed`) | every open cell → `tool_call_update` failed with `texts.CELL_INTERRUPTED`; every running child, deepest first → `subagent_update` idle: `stopped`/`closed` with `stopReason: "cancelled"` and `status: "stopped"`, `crashed` with no `stopReason` and `status: "crashed"`; `root` → `agent_message_chunk` with `texts.ROOT_STOPPED` or `texts.CRASHED`; `root` → `usage_update` |
| `run.end` `lost` (replay only) | `root` → `agent_message_chunk` `texts.REPLAY_LOST`; nothing for children (the RFD forbids manufacturing an outcome from a gap) |
| `run.start`, `worker.ready`, `stop.request`, other `run.end` | nothing |

`T` (title) = the task's first line, at most 120 characters, with ` …` when cut; `description` is
the whole task (at most 2,000 characters) and is sent only when the title was cut.

| `agent.end.status` | `stopReason` | `_meta.deep_reasoner.status` |
|---|---|---|
| done | `end_turn` | `done` |
| exhausted | `max_turn_requests` | `exhausted` |
| failed | `end_turn` (ACP has no failure reason) | `failed`, with `detail` |
| stopped | `cancelled` | `stopped`, with `stopped_by` (the node the user stopped) and `detail` |

`usage_update`: `{"used": U, "size": W, ["cost": {"amount": usd, "currency": "USD"},] "_meta":
{"deep_reasoner": {"cost_source", "tokens_in", "tokens_out", "unknown_calls"}}}`. `U` = the tokens
of the node's latest think call (prompt + completion), its context; `W` = the model's context
window from the price table, `0` when unknown. `cost` is the node's inclusive cumulative total and
is **omitted** while any contributing call has no estimate (`unknown_calls > 0`): ACP forbids
fabricating a total from incomplete counts, and a missing cost is unknown, not zero.

The prompt response: `{"stopReason": …, "_meta": {"deep_reasoner": {"run": run_id | null,
"outcome": PromptResult.outcome}}}`. Stop reasons: answered → `end_turn`; exhausted →
`max_turn_requests`; failed, build_failed, crashed, rejected → `end_turn`; stopped, closed →
`cancelled`.

**The spawning cell in the mock-up**, as it goes out:

```json
{"sessionId": "s-7c1f9e0a2b4d6e8f", "update": {"sessionUpdate": "subagent_update",
  "sessionId": "20261002-142233-4f1a2b-n2", "title": "Summarize the workload of CS101.",
  "capabilities": {"cancel": {}}, "state": {"state": "running"},
  "_meta": {"openhands": {"parentToolCallId": "20261002-142233-4f1a2b-n1-c1"},
            "deep_reasoner": {"run": "20261002-142233-4f1a2b", "node": 2, "parent": 1, "depth": 2,
                              "namespace": "router", "backbone": "chat", "drive": 1}}}}
```

### 5.3 Emission table, flat mode

For a client without `subagents` (stock OpenHands, Zed) or under `--flat`. Nothing is sent on a
child session id; `subagent_update`, `session_message` and `session_message_chunk` are never sent.

| RunEvent | Sent (always on `root`) |
|---|---|
| root's `thought`, `cell.start`, `cell.end`, `prompt.*`, `run.end`, first prompt | as in §5.2 |
| `agent.start` (child) | `tool_call` `{"toolCallId": "<S(node)>-a<d>", "title": "<path> · <T>", "kind": "other", "status": "in_progress", "rawInput": {"task": task}, "_meta": {"openhands": {"parentToolCallId": …}, "deep_reasoner": DR}}` |
| child `cell.start` / `cell.end` | as in §5.2 but on `root`, title `"<path> › Run <first line>"` |
| child `thought`, `usage`, `stop.accepted` | nothing |
| `agent.end` (child) | `tool_call_update` on its card: `completed` for done/exhausted with the answer as content; `failed` for failed (`texts.CHILD_FAILED`) and stopped (`detail`); `_meta.deep_reasoner` with `status` |
| `run.end` in flight | open cells and open cards → `failed`, then the root message, as in §5.2 |

`<path>` is `#` + each agent node of the ancestry, root first, joined by ` › ` (`#1 › #2`). The
root's cells carry no path. The root's `usage_update` covers the whole tree, as in native mode.
A flat client cannot stop one sub-agent (it never sees a child id); root Stop works.

### 5.4 Ordering guarantees

1. Per session, updates are sent in run-log order; a session's updates never overtake its
   announcement (the recorder emits `agent.start` before anything of that node, and the pump
   sends each RunEvent's updates before the next RunEvent's).
2. A child's `parentToolCallId` names a `tool_call` already sent on the parent's session (decision G).
3. Every `session/prompt` response is preceded by a root `usage_update` in the same turn.
4. All of a prompt's updates are sent before its response.
5. After `session/new`'s response the next update for that session is its
   `available_commands_update`; `session/set_config_option` sends the new namespace's
   `available_commands_update` *before* its response. S2's preview can therefore wait for the first
   `available_commands_update` after `session/new`, and treat the one before a
   `set_config_option` response as current.
6. `session/load` sends the whole replay before its response, and nothing about children after it.
7. No child traffic follows the root's prompt response: a run's children have all ended (or been
   reported ended) before it. S1 persists late child traffic anyway; `dr-acp` sends none in v1.

### 5.5 Requests

| Request | Behaviour |
|---|---|
| `session/new` | §2 step 2. Response `{"sessionId", "configOptions": [namespace option]}`. A catalog that cannot be read → JSON-RPC internal error with `texts.CATALOG_ERROR`. |
| `session/load` | Unknown id → invalid params (`texts.UNKNOWN_SESSION`); the bridge then starts a new session. A session already open in this process is closed first (graceful); then replay (§5.7), response `{"configOptions": […]}`, then, if not started, the commands. The new `cwd` is used for the next run. |
| `session/set_config_option` | `configId` must be `namespace` (else invalid params, `texts.UNKNOWN_OPTION`); value must be a catalog namespace (`texts.UNKNOWN_NAMESPACE`); after the first prompt any value but the current one fails with `texts.NAMESPACE_FIXED`, which S2 passes through as its 422. Response `{"configOptions": [namespace option]}`. |
| `session/prompt` | `Session.prompt` (§4.2). A second prompt in flight → invalid request (`texts.PROMPT_BUSY`). |
| `session/cancel` | §2 steps 8–9; ignored when nothing matches. |
| `session/close` | Graceful close of the live run (a prompt in flight ends `cancelled`), session forgotten in memory; the index stays on disk. Response `{}`. |

**The namespace option:**

```json
{"id": "namespace", "name": "Namespace", "type": "select", "currentValue": "router",
 "description": "The namespace this conversation runs in. Fixed after the first message.",
 "options": [{"value": "root", "name": "root"}, {"value": "router", "name": "router"}]}
```

After the first prompt `options` holds only the current value and `description` is
`"Fixed for this conversation."`.

**Commands:** `{"name": "summarize-then-rank", "description": "comparing many courses", "input":
{"hint": "what to compare"}, "_meta": {"deep_reasoner": {"decomposition": "summarize then rank",
"namespace": "router"}}}`.

### 5.6 User-visible sentences (`texts.py`, verbatim)

The Docwright's artifacts quote these; changing one is a design change.

| Name | Text |
|---|---|
| `ROOT_STOPPED` | `Stopped. The run was ended and its REPL state is gone: deep_reasoner cannot cancel a running cell yet (ask A3). Your next message starts a fresh run.` (the mock-up's) |
| `LATE_DECOMPOSITION` | `/{name} starts a conversation with a decomposition, so it only works as the first message. Start a new conversation, or ask in plain words.` (the mock-up's) |
| `COMMAND_NEEDS_TASK` | `/{name} needs a task after it: /{name} <{hint}>` |
| `NAMESPACE_FIXED` | `namespace is fixed once a conversation has started (it is '{namespace}').` (S2's mock-up) |
| `UNKNOWN_NAMESPACE` | `unknown namespace '{value}'; this library has: {names}.` |
| `UNKNOWN_OPTION` | `dr-acp has one option, 'namespace'; got '{config_id}'.` |
| `UNKNOWN_SESSION` | `unknown session '{session_id}'.` |
| `PROMPT_BUSY` | `a prompt is already running in this session.` |
| `CATALOG_ERROR` | `dr-acp could not read its configuration: {detail}` |
| `FRESH_AFTER_STOP` | `Starting a fresh run: the previous one was stopped, so its variables and sub-agents are gone.` |
| `FRESH_AFTER_ERROR` | `Starting a fresh run: the previous one ended with an error, so its variables and sub-agents are gone.` (after `failed`, `crashed`) |
| `FRESH_AFTER_RESTART` | `Starting a fresh run: the previous one ended when dr-acp restarted, so its variables and sub-agents are gone.` (after `lost`) |
| `FRESH_AFTER_CLOSE` | `Starting a fresh run: the previous one was closed, so its variables and sub-agents are gone.` (after `closed`; after `build_failed` no notice) |
| `BUILD_FAILED` | `Could not start the run: {detail}` (no fresh-run notice follows: nothing ran) |
| `ROOT_FAILED` | `The run failed: {detail}. Its REPL state is gone; your next message starts a fresh run.` |
| `CRASHED` | `The run crashed (exit code {code}) and its REPL state is gone. Your next message starts a fresh run. The worker's log is {path}.` |
| `REPLAY_LOST` | `(This run ended when dr-acp stopped; its REPL state is gone.)` |
| `CHILD_FAILED` | `Failed: {detail}` |
| `CELL_INTERRUPTED` | `Not finished: {reason}` (`the run was stopped`, `the run crashed`, `the agent stopped`) |
| `stop_requested`, interim or Dean, chat | `Stop requested: this agent and its sub-agents stop at their next turn, before their next model call. A cell that is already running finishes first.` |
| `stop_requested`, interim, Claude backbone | `Stop requested: this agent runs a Claude Code session, which is one turn, so it stops when that session ends.` |
| `stop_requested`, Dean, Claude backbone | `Stop requested: its Claude Code session is being ended.` |
| `StoppedByUser` (interim, in the parent's cell output) | `stopped #{t}[ and its branch (#a, #b)].[ Its running sibling #s in this run_all was stopped with it (A3).]` plural: `Its running siblings #s, #u in this run_all were stopped with it (A3).` (the mock-up's) |

### 5.7 `session/load` replay

1. Read the index (unknown → error). For each run id in order: if its log has no `run.end`, append
   `run.end {reason: lost}` (the dr-acp process that owned it is gone; its worker exits on control
   EOF); then feed every event to a fresh `Encoder(replay=True)` and send what it returns.
2. Replay differs from live in two ways only: an announcement carries no `capabilities` (historical
   capabilities must not authorize a Stop: the RFD's freshness rule), and no intermediate
   `usage_update` is sent (only each agent's final one and the root's at each `prompt.end`).
3. The response, then the commands if the session never started. No live child snapshot follows:
   after a restart there is no live child to describe.
4. The session's next prompt starts a fresh run with `FRESH_AFTER_RESTART` (or the notice for the
   last recorded end).

### 5.8 `_meta` keys, all of them

| Key | On | Meaning | Read by |
|---|---|---|---|
| `_meta.openhands.parentToolCallId` | `subagent_update` (native), flat agent cards | the `toolCallId` of the parent's cell that spawned (or re-drove) the child; always a call already sent on the parent's session | S1 (persists), C1 (placement) |
| `_meta.deep_reasoner.{run,node,parent,depth,namespace,backbone,drive}` | `subagent_update`, flat cards | the node's identity in deep_reasoner's tree | E1, our tests, golden replays; no fork |
| `_meta.deep_reasoner.{status,detail,stopped_by}` | idle `subagent_update`, closed flat cards | outcome (`done`, `exhausted`, `failed`, `stopped`, `crashed`) | as above |
| `_meta.deep_reasoner.{run,node,parent,depth,cell,origin}` | cell `tool_call` | the cell's owner and how it was opened | E1 (flat tree), tests |
| `_meta.deep_reasoner.{cost_source,tokens_in,tokens_out,unknown_calls}` | `usage_update` | how the cost was obtained | tests, the live doc |
| `_meta.deep_reasoner.{decomposition,namespace}` | each `availableCommands` entry | the decomposition the command opens | tests |
| `_meta.deep_reasoner.{run,outcome}` | the prompt response | which run answered, and how the turn ended | E11, tests |

---

## 6 · Algorithms

### 6.1 The recorder: deep_reasoner events → RunEvents

A structlog processor installed ahead of deep_reasoner's `LogProcessor` and before the level filter
(`configure_structlog_fixture` puts extra processors there, `core.py:148–150`). It runs on every
thread that logs (the root on the main thread, sub-agents on `_run_sync` worker threads), holds one
lock for its state and its writes, returns the event dict unchanged, and raises only
`StoppedByUser` (§6.3). State per agent node: parent, agent ancestry, drive, open cell (k or None),
cell counter, iteration, the latest think tokens, the latest `FinalAnswer` line, status.

*Owner* of an event = its `node_id` if that is a known agent, else the deepest known agent in its
`ancestry` (the `llm` tool and a Claude session take nodes of their own under the agent, kind `llm`
and `claude`; verified below).

| deep_reasoner event (d7334ae) | Recorder |
|---|---|
| `agent.start` (`agent.py:877`; `task`, `max_iter`, `backbone`, `namespace`, `run`, node fields) | agent ancestry = the known agents in `ancestry`, plus this node; parent = the one before it. If the parent has no open cell, first emit `cell.start {origin: inferred, code: ""}` for it. New node → drive 1, else drive + 1 (a resumed root, a re-driven child); the kept answer is reset. Emit `agent.start` with `parent_cell` = the parent's open cell, `backbone` = `chat` for `DeepReasoner`, `claude_code` for `ClaudeDeepReasoner`, else the class name, and `dr_run` = deep_reasoner's `run`. |
| `agent.turn` (`:882`, inside the drive's `try`) | Stop check (§6.3). Then: if this is the root's first drive and puppeteered turns remain, emit `cell.start {origin: puppeteered, code: turn's <repl> source}`. |
| `agent.loop` with `kind == "agent"` (`llm_coro.py:240`) and no open cell for the node | The think reply = `messages[-1].content`. `thought` = the reply without its `<repl>` block and `<think>` tags, stripped (none if empty). If `code(reply)` parses (`messages.py:288`), emit `cell.start {origin: think}`. A reply without a block opens no cell: deep_reasoner asks for a correction and spends a turn. `agent.loop` is used rather than `llm.call` because it fires on a disk-cache hit too; the worker also turns the cache off. |
| `llm.call` (`llm_coro.py:110`) | `usage` for the owner: `call` = `think` when `kind == "agent"`, else `tool`; cost from `PriceTable.estimate(model, usage)`. A think call also sets the owner's context tokens. |
| `claude.call` (`claude_code.py:842`) | `usage` for the owner with `cost_usd` (source `claude`), and `thought` = its `response`. |
| `repl.execute` (`repl_coro.py:328`) for a known agent | Close the open cell (or open and close one at once, `origin: inferred`) with `code` = `source` and `output` = the observation without its `<observation>` wrapper (`messages.py:137`). If the output's last line starts `FinalAnswer: `, keep the rest as the node's answer repr (`repl_coro.py:324`). |
| `agent.end` (`:897`, `:903`, `:911`; `status`, `iter`, `detail`) | Close an open cell as `interrupted`. Classify (§6.3) and emit `agent.end` with `answer`: for done, the kept repr, unquoted when it is a Python string literal (`ast.literal_eval`); for exhausted, `Agent failed to produce a final answer within {max_iter} iterations.` (`agent.py:197–206`). |
| anything else | ignored |

**Verified at d7334ae, 2026-10-02** (a scripted run with `FakeCompletionClient`: the root fans out
two children with `run_all`, the first calls the `llm` tool, then a second prompt resumes the
root; and the same opened by a one-step main decomposition):

```text
agent.start  node 1 anc [1]        kind agent  MainThread   task 'Rank the courses.'
agent.turn   node 1
llm.call     node 1 anc [1]        kind agent               resp '<think>fan out</think>|<repl>|r = run_all(...'
agent.loop   node 1 anc [1]        kind agent               last = the same reply           ← cell.start (think)
agent.start  node 2 anc [1, 2]     kind agent  ThreadPool   task 'Summarize C1'
llm.call     node 3 anc [1, 2, 3]  kind llm    ThreadPool   resp 'hi'                        ← the llm tool: owner 2
repl.execute node 2                                         obs '<observation>|FinalAnswer: 'ok C1 hi'|</observation>'
agent.end    node 2 done
agent.start  node 4 anc [1, 4] …                                                             ← node ids skip 3
repl.execute node 1                                         ← the root's cell, reported only after its children
agent.start  node 1 anc [1]                                 task 'second question'          ← resume: drive 2
main decomposition: decomposition.puppeteered (no node) · agent.start 1 · agent.turn 1 · agent.start 2 …
                    (no llm.call or agent.loop for the puppeteered turn)
```

### 6.2 Cost roll-up

The encoder keeps, per agent node, a ledger (usd, complete, tokens) for the node's own calls and
an inclusive total = own + descendants'. A `usage` event adds to its owner's own ledger and to the
inclusive total of the owner and every agent ancestor, marking each dirty. The root session's
total is `carry` (all earlier runs of the conversation) plus the root node's inclusive total; it
never decreases, so the bridge's per-session deltas (`acp_agent.py:2065–2072`) stay right across a
fresh run. `complete` turns false for good once any contributing call had `cost_usd: None`.

### 6.3 Stop

**The API we code against (Dean's, from the spec; the name and module are his):**

```python
stop(node_id: int) -> None
```
1. Thread-safe: callable from any thread. 2. Takes effect at the agent's next turn, before its next
model call. 3. Its descendants stop too. 4. The agent ends with its own `agent.end` status
`stopped`, beside `done`, `failed` and `exhausted`. 5. Its parent's cell sees a returned value or an
`Exception`, never a `CancelledError`. 6. `run_all` returns the other children's results, with the
stopped one marked. 7. A Claude-backbone agent's `claude` process is ended.

**`worker/stop.py`:**

```python
DEAN_STOP_API: str | None = None
"""'module:attr' of Dean's stop(node_id), set when he ships it. DR_ACP_STOP_API overrides it
(the tests point it at the fake). None → the interim."""

class StoppedByUser(Exception):
    """Interim only. An Exception, so the parent's cell catches it (cells catch Exception,
    repls/backends.py:523, repl_coro.py:84)."""
    def __init__(self, target: int, branch: tuple[int, ...], siblings: tuple[int, ...]) -> None: ...

@dataclass(frozen=True)
class StopReceipt:
    node: int
    mode: Literal["dean", "interim"]
    accepted: bool               # False: unknown node, or it already ended
    reason: str | None

class StopAdapter(Protocol):
    mode: Literal["dean", "interim"]
    def stop(self, node_id: int) -> StopReceipt: ...        # thread-safe, returns at once

class DeanStop:                  # the one place dr-acp calls deep_reasoner's stop
    def __init__(self, fn: Callable[[int], None], recorder: "Recorder") -> None: ...
    def stop(self, node_id: int) -> StopReceipt:            # recorder.note_stop(node_id); fn(node_id)
        ...

class InterimStop:
    def __init__(self, recorder: "Recorder") -> None: ...
    def stop(self, node_id: int) -> StopReceipt:            # recorder.arm(node_id)
        ...

def resolve_stop_adapter(recorder: "Recorder", spec: str | None) -> StopAdapter: ...
```

Both adapters make the recorder emit `stop.accepted` and remember the target, so classification
works the same in both modes. **When Dean ships, the change is one line**: `DEAN_STOP_API`.

**The interim** (verified by the spec's third probe): at `agent.turn` of node n, if an armed target
t is n or is in n's ancestry, raise `StoppedByUser(t, branch, siblings)`, where `branch` = the
target's descendants running now and `siblings` = the running agents opened in the same parent
cell as t (they are in its `run_all`, which deep_reasoner's `gather` will cancel, `agent.py:158–174`).
A branch unwinds bottom-up: a stopped parent blocked in a cell reaches its next turn when its
stopped children have ended.

**Classification at `agent.end`:**

| deep_reasoner says | and | RunEvent status |
|---|---|---|
| `stopped` (Dean) | — | `stopped`, `stopped_by` = the target whose branch holds the node |
| `failed`, detail starts `StoppedByUser` | — | `stopped`, `stopped_by` |
| `failed`, detail starts `CancelledError` | a sibling in the same parent cell is an armed target | `stopped`, `stopped_by` = that sibling, `collateral: true` |
| `failed`, otherwise | — | `failed` |
| `done`, `exhausted` | — | as is (a cancel racing ended work does not rewrite it) |

**Where the interim differs from Dean's API, and where the user sees it:** (1) the stopped child's
running siblings in its `run_all` are cancelled; the parent's cell output names them (the
`StoppedByUser` text, §5.6), and each of them turns `idle`/`cancelled` with `collateral` in its
`_meta`. A collateral sibling that is itself waiting on its own children is cancelled only when
they finish, and they are not stopped: their results are discarded. (2) A Claude-backbone agent's
one turn is a whole Claude session, so the stop lands when it ends; the child's session says so at
once (`stop_requested`). (3) A running cell is never interrupted, in either mode (A3).

**The fake of Dean's API** (tests only, `tests/acp/fakes/dean_stop.py`, exposed as `stop`, reached
through `DR_ACP_STOP_API`): inside the worker it wraps `DeepReasonerAgentBase._note_drive` so that
`agent.turn` of a node in a stopped branch raises a private `BaseException`, the `agent.end` that
follows is logged with status `stopped`, and `__anext__` returns a `Stopped(node)` marker instead of
raising. That satisfies points 1–6 on d7334ae; point 7 is not faked.

### 6.4 Root Stop and other forced ends

`RunHandle.kill("stopped")`, budgeted inside the bridge's 2 s cancel drain (`_ACP_CANCEL_DRAIN_TIMEOUT`,
`acp_agent.py:169`; past it the bridge restarts `dr-acp` and replays):

1. Mark the run stopping (no `run.end` yet); `SIGTERM` the worker's process group.
   The worker's handler raises `RunKilled` in its main thread; `close_run` runs under its 0.7 s
   watchdog and the worker exits.
2. After 0.8 s, `SIGKILL` the group if it is still alive.
3. Drain the event pipe to EOF (≤ 0.3 s; events the worker wrote before dying are logged and sent).
4. Append `run.end {reason: stopped}`; feed it (§5.2: cells, children, the root's message, usage).
5. Resolve the prompt with `cancelled`. `ModelRoute.release(run)`.

Verified at d7334ae (2026-10-02): with the root's own cell in `while True: pass`, the SIGTERM
handler's exception unwound the drive and `close_run` ran 0.01 s after the signal; with a
sub-agent's cell looping, the main thread unwound into `ThreadPoolExecutor.__exit__`, which waits
for the looping thread, so only `SIGKILL` ends the run and `close_run` does not run. So: a run stuck
in the root's cell releases its sandboxes and persists its tools; one stuck in a sub-agent does not
(a remote Daytona sandbox can then outlive the run, until A3).

`crashed` (the worker exited without being asked) and `closed` (`session/close`, `dr-acp` exiting)
go through steps 3–5 with their reason.

---

## 7 · Signature index

Load-bearing signatures are given in full where their module is described: `Options`, `main`,
`guard_stdout` and `Outbox`, `serve`, `ClientMode` (§4.2); `DrAcpAgent`, `Session`, `PromptResult`,
`RunHandle` (§4.2); the control messages (§4.3); every RunEvent, `RunLog` (§4.4); `Encoder`,
`ChildRef`, `CostLedger` (§4.5); `Catalog`, `CatalogSnapshot`, `CommandEntry`, `RunSource`,
`ConfigCatalog` (§4.6); `ModelRoute`, `RouteGrant`, `DirectRoute`, `worker_env`, `PriceTable`,
`Price`, `CostEstimate` (§4.7); `StopAdapter`, `DeanStop`, `InterimStop`, `StoppedByUser`,
`StopReceipt`, `resolve_stop_adapter`, `DEAN_STOP_API` (§6.3). The rest:

```python
# ids.py
def new_session_id() -> str: ...                      # "s-" + secrets.token_hex(8)
def new_run_id(now: datetime | None = None) -> str: ...
def child_session_id(run: str, node: int) -> str: ...
def cell_id(run: str, node: int, k: int) -> str: ...
def card_id(run: str, node: int, drive: int) -> str: ...
def task_message_id(run: str, node: int, drive: int) -> str: ...
def answer_message_id(run: str, node: int, drive: int) -> str: ...
def short(id_: str, root: str) -> str: ...           # the printer's forms, §5.1

# runlog.py
@dataclass(frozen=True)
class Home:
    root: Path
    @classmethod
    def resolve(cls, flag: Path | None) -> "Home": ...  # flag, else $DR_HOME, else ~/.deep-reasoning
    def run_dir(self, run: str) -> Path: ...
    def session_file(self, session: str) -> Path: ...
class SessionIndex(BaseModel): ...                     # the JSON of §4.4
    @classmethod
    def load(cls, home: Home, session: str) -> "SessionIndex | None": ...
    def save(self, home: Home) -> None: ...            # atomic

# worker/recorder.py
class EventSink:
    def __init__(self, fd: int) -> None: ...
    def emit(self, ev: Mapping[str, Any]) -> None: ...  # one JSON line, under the recorder's lock
class Recorder:
    def __init__(self, sink: EventSink) -> None: ...
    def __call__(self, logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]: ...
    def set_puppeteer(self, turns: Sequence[str]) -> None: ...
    def note_stop(self, node: int, mode: Literal["dean", "interim"]) -> StopReceipt: ...
    def arm(self, node: int) -> StopReceipt: ...       # interim
    def emit(self, kind: str, **fields: Any) -> None: ...   # the runner's own events (worker.ready, prompt.end)

# worker/runner.py
def main(argv: Sequence[str] | None = None) -> int: ...  # --control-fd N --events-fd M
class RunKilled(BaseException): ...
def as_text(value: Any) -> str: ...

# testing/client.py (§8.2)
class Caps(acp.schema.ClientCapabilities): subagents: dict | None = None
class ShimConnection(acp.client.connection.ClientSideConnection): ...
class Printer:                                         # an acp Client that records and prints
    lines: list[str]; updates: list[tuple[str, dict]]
    subagents: dict[str, SimpleNamespace]              # by short id; .field_meta, .state
    commands: list[SimpleNamespace]
    async def session_update(self, session_id: str, update: Any, **kw: Any) -> None: ...
    async def unstable_update(self, session_id: str, update: dict) -> None: ...
def tree(updates: Sequence[tuple[str, dict]], *, mode: Mode) -> "Tree": ...   # E1's rebuild

# testing/fake_model.py
class FakeOpenAI:                                      # async context manager; .base_url; .calls
    def __init__(self, responder: Callable[[list[dict]], str], *, latency_s: float = 0.0,
                 usage: Callable[[list[dict], str], dict] | None = None) -> None: ...
```

---

## 8 · Testing

### 8.1 Layers, mapped onto E1–E4 and E11

| Experiment | Where | How |
|---|---|---|
| **E1** tree fidelity | `tests/acp/test_tree_fidelity.py` | The spec's eight scripted runs (`tests/acp/scenarios.py`: linear; `run_all` of 2 and of 20; depth 3; a spawn into another namespace; `fork()`; exhausted; a failing cell; the Claude backbone with deep_reasoner's `write_fake_claude_cli`), each a small `dr` config with `client.base_url` at `FakeOpenAI`. `dr-acp` is spawned over stdio; a `ShimConnection` client records every update, in native and in flat mode; `testing.tree()` rebuilds parent links and cells per node; deep_reasoner's own tree comes from its node YAMLs (their `ancestry`) and its `repl.execute` count per node, in the same run directory. Null: any difference. |
| **E2** stdio integrity | `test_stdio_integrity.py` | A tool printing 10 MB to `sys.stdout`; `os.write(1, …)` in a cell; `os._exit(1)` in a cell; a print at the front's import time (monkeypatched module). Every outgoing line must parse as JSON-RPC; after the crash the next prompt answers (fresh run). |
| **E3** stop | `test_stop.py` | Root Stop during `while True: pass` and during a 20-way fan-out: `cancelled` within 2 s (the spec allows 5; the bridge needs 2). One child of a 20-way fan-out with children of its own, through the interim and through the fake Dean API. `FakeOpenAI` timestamps each call and attributes it by the task in its messages. Null: any call started after the stop by an agent of the stopped branch; with the fake API, a sibling's result missing from the parent's `run_all`; in the interim, a sibling cancelled without the parent's cell output naming it. |
| **E4** contracts | `test_tripwire.py`, `test_schema.py` | Tripwire: every deep_reasoner event and field §6.1 reads, checked on scripted runs (names, the `<observation>` wrapper, the `FinalAnswer:` line, `kind` of think and tool calls, `agent.start` per drive), at `d7334ae` on every push and against Dean's `main` weekly. Schema: an `Outbox` observer validates every outgoing message (updates and responses) against the vendored `tests/acp/schema/acp-1.24.1.unstable.json` (sha256 checked) in every test that runs `dr-acp`. Red is reported, never absorbed. |
| **E11** (D1's part) | `test_surfaces.py` | Commands per namespace, changed by `set_config_option`; cleared and narrowed at the first prompt; the late-command and fixed-namespace errors verbatim; the run log's `run.start.namespace` equals the chosen one. |
| replay | `test_load.py` | Kill `dr-acp` mid-run, start a new one, `session/load`: the replayed tree equals the live one, the response comes last, no child snapshot follows, the next prompt is fresh. |
| units | `test_encoder.py`, `test_recorder.py`, `test_costs.py`, `test_catalog.py` | The encoder from hand-written RunEvents, both modes; the recorder fed synthetic event dicts in each order of §6.1, including inferred and puppeteered cells; prices; slugs and collisions; `ConfigCatalog` over small configs of our own, and over deep_reasoner_beta's `docs/configs` read in place when `DR_BETA_CHECKOUT` points at a checkout (skipped otherwise; never copied here). |

### 8.2 Fakes and helpers

- **`testing.fake_model.FakeOpenAI`**: `POST /v1/chat/completions` on 127.0.0.1 from a responder,
  with optional latency and usage, recording each call's start time and messages. Tests and the
  live doc use real HTTP, so the worker runs unmodified and D5's proxy can later sit in front of it.
- **`testing.client`**: the spec's `ShimConnection` and `Caps` (copied, not imported from the SDK
  fork; `dr-acp` never imports OpenHands) and `Printer`, whose short forms print the mock-ups as
  approved. The live doc imports the same module.
- **`tests/acp/fakes/dean_stop.py`**: §6.3.

### 8.3 Golden recordings

`uv run python -m tests.acp.golden record` reruns E1's eight scenarios in both modes and writes
`tests/acp/golden/<scenario>.<native|flat>.jsonl`: the outgoing JSON-RPC messages, normalized (the
run id → `RUN`, the root id → `ROOT`, intermediate `usage_update`s dropped, keeping each session's
last before a state change). The check compares per-session sequences and the tree, not the global
interleaving, which concurrent children make nondeterministic. They carry `_meta.deep_reasoner`, so
they live here and D5's cross-repo CI replays them into S1 and C1. Whoever changes the encoding
re-records, and the diff is reviewed.

### 8.4 Real-model runs

None in layers 1–2. The Gate B live doc (Docwright) runs `dr-acp` against gpt-6-luna through a
config of our own (`client: {base_url: https://api.openai.com/v1, api_key_env: OPENAI_API_KEY}`),
prints the stream through `testing.Printer`, and stops one branch; cents per run.

### 8.5 Repository wiring D1 adds

- `pyproject.toml`: `deep-reasoning`, `requires-python = ">=3.12,<3.13"` (deep_reasoner's range);
  dependencies `deep-reasoner @ git+https://github.com/DeanLight/deep_reasoner_beta@d7334ae6ea884617a377d9f1ce872530d898484c`,
  `agent-client-protocol>=0.12.1,<0.13` (locked at 0.12.1, the SDK fork's lock), `pydantic>=2.7`,
  `pyyaml`, and **`ipython`** (deep_reasoner imports `IPython.display` at module level in 12
  modules but declares it only through its dev group; verified: blocking `IPython` makes
  `import deep_reasoner.v2.cli` fail); script `dr-acp = "deep_reasoning.acp.cli:main"`; dev group
  `pytest`, `jsonschema`, `referencing`; `[tool.pytest.ini_options] testpaths = ["tests"]`; sdist
  excludes `docs/`. A test asserts the installed `agent-client-protocol` is the pinned 0.12.1.
- `.github/workflows/ci.yml` (layers 1–2 on push) and `acp-tripwire.yml` (weekly, deep_reasoner at
  `main`). Both fetch the private dependency with a read token stored as a repository secret
  (Michael's to add; the same token Q8's cross-repo CI needs).

---

## 9 · What D1 relies on (the Expectation rows to write at merge)

The workspace writes a row only once merged code relies on it; this list is what the Conductor
turns into rows, with the merged `file:line`.

**deep_reasoner (d7334ae)**

| # | Behaviour relied on | Their code | Ours |
|---|---|---|---|
| R1 | **`stop(node_id)` with the seven-point contract of §6.3** (not yet in his repo) | — | `worker/stop.py` `DeanStop.stop` |
| R2 | `load_cli_config(path, schema=V2Config)` composes and validates, stamping `config_path` | `config.py:454–481`, `cli.py:80` | `catalog.py`, `worker/runner.py` |
| R3 | `V2Config` fields `entry_namespace`, `namespaces_dir`, `client` (`base_url`, `api_key_env`), `decompositions`, `task`, `prompt_template_variables` | `config.py:355–440` | same |
| R4 | `build_namespace_registry(cfg)`, `NamespaceRegistry.resolve(name).decompositions` (accumulated root→leaf, child wins by name), `load_namespaces_from_dir`, `registry.close()` | `cli.py:289`, `namespaces.py:248–320, 754, 772` | `catalog.py`, runner |
| R5 | `main_decomposition_turns(spec, task, *pools, template_vars=)`, searching pools in order, first name wins | `decompositions.py:117–169` | catalog (commands), runner (puppeteered cells) |
| R6 | `build_reasoner(cfg, run_dir=, main_decomposition=)` → `(reasoner, alias)`, alias kept entered for the run; works with a later resumed prompt (`dr` forbids the combination only in its CLI, `cli.py:719`) | `cli.py:308–373` | runner (verified: a decomposition then a second prompt) |
| R7 | `reasoner.acall(task)` drives one prompt and resumes the conversation on the next call; `reasoner.exhausted` | `agent.py:388–437, 456, 749–778` | runner |
| R8 | `close_run(reasoner)` | `cli.py:439–450` | runner |
| R9 | `configure_structlog_fixture(extra_processors=)` puts them before the level filter, so debug events reach us; `LogProcessor` writes `{base}/{task_id}/`; `set_cache_dir(None)` turns the cache off | `core.py:131–160, 264`, `logging_utils.py:79–90, 227` | runner |
| R10 | The events and fields of §6.1's table, including `agent.turn` inside the drive's `try` and a per-drive `agent.start` | `agent.py:857–912`, `llm_coro.py:110, 240`, `repl_coro.py:315–328`, `claude_code.py:842`, `context.py:79–114` | `worker/recorder.py` |
| R11 | The agent's own LLM logs with `kind: agent` on the agent's node; the `llm` tool and a Claude session take their own nodes under it | `agent.py:936–938`, `context.py:240–243` (verified) | recorder (owner rule) |
| R12 | An observation is `<observation>\n…\n</observation>` and ends with `FinalAnswer: <repr>` when the cell answered | `messages.py:130–137`, `repl_coro.py:315–325` | recorder (answers) |
| R13 | `code(text, start, end)` extracts the last `<repl>` block, raising `NoCodeBlock` | `messages.py:288–307` | recorder (think cells) |
| R14 | Interim: an exception raised by a processor at `agent.turn` ends that drive as `failed`; cells catch `Exception`, so the parent sees it; `run_all` is `gather` on a private loop, cancelling the siblings | `agent.py:158–174, 899–905`, `repls/backends.py:523`, `repl_coro.py:84`, `coro_base.py:73–92` | `worker/stop.py`, recorder |
| R15 | A cell runs synchronously in its coroutine; a sub-agent runs on a `_run_sync` worker thread, so a signal can unwind the root's cell but not a sub-agent's (verified) | `repl_coro.py:311–315`, `coro_base.py:73–92` | `worker/runner.py`, §6.4 |
| R16 | Importing deep_reasoner writes nothing to stdout (verified) | — | `catalog.py` in the front |

**ACP Python 0.12.1**

| # | Behaviour relied on | Their code | Ours |
|---|---|---|---|
| P1 | `acp.connection.Connection(handler, writer, reader)` with a raw `(method, params, is_notification)` handler; each incoming message handled in its own task, so `session/cancel` runs during a `session/prompt` (verified) | `connection.py:41–79, 152–166` | `wire.py` |
| P2 | `acp.agent.router.build_agent_router(agent, use_unstable_protocol=True)` maps methods to snake_case handlers with validated keyword arguments, `_meta` merged in; `session/close` routed only when unstable is on (verified) | `agent/router.py:56–119`, `router.py:93–107, 111–150, 165–184` | `wire.py`, `agent.py` |
| P3 | A handler's plain dict is sent as the result unchanged | `connection.py:198–210` | `agent.py` |
| P4 | `Connection.send_notification(method, params)` sends raw JSON, in call order (one FIFO sender) | `connection.py:132–136`, `task/sender.py:28–58` | `Outbox` |
| P5 | `InitializeRequest`/`ClientCapabilities` drop `subagents`, so it is read from the raw params (verified) | `schema.py` | the tap |
| P6 | A notification sent from a task created inside a request handler goes out after that handler's response (the response is queued before the handler's task yields; verified) | `connection.py:187–189`, `task/sender.py:28–32` | §5.4 rule 5 |
| P7 | Test only: `ClientSideConnection` routes through `_conn._handler`, which the shim wraps; `request_model` and an `InitializeRequest` subclass put `subagents` on the wire | `client/connection.py`, `utils.py` | `testing/client.py` |

**The bridge (SDK fork, upstream behaviour S1 starts from):** it waits ≤ 2 s per turn for a root
`usage_update` (`acp_agent.py:3643–3654`); it restarts the agent when a cancelled prompt does not
answer within 2 s (`:169, 3472–3540`); any parsed update resets its 1,800 s prompt-idle watchdog
(`:1433–1439, 1758`); it drops stdout lines that are not JSON-RPC (`:1047–1076`); it calls
`session/load` with the prior id and falls back to `session/new` on a JSON-RPC error
(`:3200–3240`); it books cost as deltas of each session's cumulative amount (`:2065–2072`).

---

## 10 · Open items

1. **gpt-6-luna's price and context window** for `prices.yaml`: not known to this design; the
   Implementer takes them from OpenAI's page with a date. Until then its cost is reported as unknown.
2. **The live doc's config** must be our own: deep_reasoner_beta's `docs/configs/catalog` cannot be
   copied into this repo (no license), and the git dependency installs the package without its
   `docs/`. Tests that want Dean's configs read a checkout named by `DR_BETA_CHECKOUT` and skip
   with a reason otherwise.
3. **A read token for deep_reasoner_beta in this repo's CI** (§8.5): Michael's to add.
4. **Bug for Dean, found here:** deep_reasoner imports IPython but does not declare it (§8.5). D1
   works around it; the row belongs in the changelog's findings, not in Expectations.
5. **Disk:** run directories are never pruned in v1.
