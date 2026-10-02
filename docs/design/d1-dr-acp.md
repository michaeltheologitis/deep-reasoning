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
- 2026-10-02 · v2 · after the Docwright wrote the live doc against v1 and returned nine problems.
  Stop trusting: §7's `Printer` and `tree()` (now specified in §8.2: `Printer` never prints by
  itself, `show()` prints from the calling cell, `wait_until()` waits for an update,
  `subagents` is keyed by full session id and `commands` by root session, `tree()` returns a
  `Tree` drawn per conversation and run); §6.3's interim and classification table (an agent
  cancelled under a stopped target is `stopped`, not `failed`; `branch` and `siblings` are
  redefined; a re-driven child is no longer stopped by an old request); §4.2's shutdown (1.4 s
  on stdin EOF *or* SIGTERM, not 2 s on EOF), `RunHandle.close`, and the pump's `run.end` reason
  after a failed or build-failed prompt (`failed`/`build_failed`, not `crashed`); the fresh-run
  notice, which now comes from `run.start.after` in the run log and is an `agent_message_chunk`
  ending in a blank line; §5.2's root closing messages, which gain
  `_meta.deep_reasoner.{run,prompt,outcome}`, and idle updates, which gain `collateral`; §5.5's
  errors (the sentence is the JSON-RPC `message`); §5.6's `StoppedByUser` row (Python prints the
  qualified class name); §5.1's launch environment; §8.5 (a `docs` group to execute the live doc,
  ruff). Added without changing earlier sentences: an unknown `session/cancel` id is logged
  (§4.2); §4.6 decides that every decomposition is offered (D2 may mark programs, §10 item 6);
  §8.1's test rows for the above. Every signature block is now valid, ruff-formatted Python with
  one field per line (Michael's request). New departures from the spec: §3 items 12–15.
- 2026-10-02 · v1 · first full-depth version.

**Where this file lives, and why nothing trips over it.** `docs/design/` on the task branch. This
repo has no docs site (no `mkdocs.yml`), pytest is pointed at `tests/` only
(`[tool.pytest.ini_options] testpaths = ["tests"]`, §8.5), the package uses a `src/` layout so
`docs/` is not in the wheel, and the sdist excludes `docs/` (§8.5). The PR split leaves it behind.

**Reading guide.** Gate B: §1–§3 (about 12 minutes). S1, C1 and S2 design against §5, which is
their contract. D2 against §4.6 and §4.4. D5 against §4.7 and §5.1. The Docwright and the
Implementer read everything; the live doc's own contract is §5 plus §8.2 (`Printer`, `tree()`),
and §7 is the signature index.

---

## 1 · What `dr-acp` is

A stdio ACP agent. Each ACP root session owns at most one live deep_reasoner **run**, executed in a
**worker** subprocess. The worker turns deep_reasoner's structlog events into our own
**RunEvents**; the front process writes them to the **run log** and only then encodes them as ACP.
Everything the client ever sees about a run is a function of the run log. OpenHands starts one
`dr-acp` per conversation (`_start_acp_server`, `acp_agent.py:2912`); `dr-acp` itself serves any
number of sessions on one connection.

```text
ACP client (agent-server bridge, S1)               $DR_HOME/
   │ stdio (JSON-RPC, ndjson)                         sessions/<session>.json      session index (§4.4)
   ▼                                                  runs/<run>/events.jsonl      RunEvents: the system of record
dr-acp front  (asyncio, one process per connection)   runs/<run>/worker.log        worker stdout+stderr
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
   (S2) costs a start-up and a catalog read. The commands arrive *after* the response, and ACP
   Python 0.12.1 resolves `new_session` before it handles them, so a client that needs the menu
   waits for that update (§5.4 rule 5; the live doc uses `Printer.wait_until`, §8.2).
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
   prompt answers `cancelled`. The next prompt starts a fresh run and says so, in an
   `agent_message_chunk` ahead of its answer.
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
12. **The mock-up's `Printer` changes in four places (v2).** It never prints by itself: its
    callbacks run in ACP Python's notification tasks, which carry the context of the cell that
    built the connection, so under ipykernel 7.3 their prints land in no cell (verified by the
    Docwright with nbclient 0.11); `printer.show()` prints from the calling cell instead. The
    commands arrive after `session/new`'s response (§5.4 rule 5), so the mock-up's first cell
    waits for them (`await printer.wait_until(...)`). `printer.commands` is keyed by root
    session (`printer.commands[s.session_id]`), and `printer.subagents` by full session id, with
    a short id such as `"n2"` still accepted when exactly one sub-agent has it: short ids repeat
    in every run. §8.2.
13. **`session/cancel` takes the full child session id (v2).** The mock-up's
    `conn.cancel(session_id="n3")` used the printer's short form; `dr-acp` ignores an id it does
    not know (a notification has no error reply) and logs it at WARNING. Short ids repeat in every
    run and every conversation, so they cannot address a session (decision F). A client reads the
    id from the announcement (`printer.subagents["n3"].session_id`).
14. **The parent's cell output names `deep_reasoning.acp.worker.stop.StoppedByUser` (v2),** not the
    mock-up's bare `StoppedByUser`: deep_reasoner formats a cell's exception with
    `traceback.format_exc()` (`repls/backends.py:523–524`, `v2/repl_coro.py:84–85`), which
    qualifies a class defined outside `builtins`. The text after the colon is the mock-up's.
15. **Root closing messages carry `_meta.deep_reasoner.{run,prompt,outcome}`, and idle updates
    `collateral` (v2),** extending item 7's superset, so a tree can be rebuilt from the updates
    alone: which run a root message ends and how, and whether a stopped agent was the target, in
    its branch, or beside it in a `run_all`.

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
    texts.py                       every user-visible sentence (§5.6), in one place
    worker/__main__.py             python -m deep_reasoning.acp.worker
    worker/runner.py               control loop, build, drive, close
    worker/recorder.py             Recorder (the structlog processor)
    worker/stop.py                 StopAdapter, DeanStop, InterimStop, StoppedByUser
    worker/protocol.py             control messages (front → worker)
    testing/__init__.py            for tests and the live doc, never imported by dr-acp itself
    testing/client.py              ShimConnection, Caps, Printer, Subagent (§8.2)
    testing/tree.py                tree(), Tree and its nodes (§8.2)
    testing/fake_model.py          FakeOpenAI: an OpenAI-compatible endpoint on 127.0.0.1
tests/acp/…                        §8
```

`dr-acp` never imports OpenHands. The front imports deep_reasoner only inside `ConfigCatalog`
(and, after D2, the Library); it never builds or drives an agent.

### 4.2 The front

**`cli.py`.** Parses options, applies the stdout guard (decision D), configures stdlib logging to
stderr (the bridge logs our stderr at INFO, so the default level is WARNING), builds the catalog,
the route and the agent, and runs `wire.serve`.

**Shutdown** starts on stdin EOF or on SIGTERM, whichever comes first, and runs once. Clients send
both and do not wait long: OpenHands' bridge closes the connection and sends SIGTERM at once,
killing after 5 s (`_shutdown_runtime`, `acp_agent.py:4563–4590`); ACP Python's
`spawn_stdio_transport` closes stdin, sends SIGTERM after 2.0 s and SIGKILL 2.0 s later
(`transports.py:96–117`). So every live run is closed concurrently with
`RunHandle.close(grace_s=0.3)`, which writes `run.end closed` within 1.4 s (0.3 s for the worker
to exit by itself, then §6.4's 0.8 s and 0.3 s), and `dr-acp` exits 0. Updates it can no longer
send (the client has closed the pipe) are dropped; the run log still has them. A run whose
`dr-acp` was killed before that replays as `lost` (§5.7).

```python
@dataclass(frozen=True)
class Options:
    config: Path | None  # --config PATH: a plain dr main.yaml; required until D2
    home: Path  # --home DIR, else $DR_HOME, else ~/.deep-reasoning
    flat: bool  # --flat: never send sub-agent sessions, whatever the client advertises
    heartbeat_s: float  # --heartbeat SECONDS, default 60
    log_level: str  # --log-level, default WARNING


def main(argv: Sequence[str] | None = None) -> int: ...


def guard_stdout() -> int:
    """os.dup(1) -> acp_fd; os.dup2(2, 1); sys.stdout = sys.stderr; return acp_fd.

    Called before any other import of ours. acp_fd, the original fd 1, is the ACP writer's.
    """
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
        """A session/update notification, raw JSON: {"sessionId": ..., "update": update}."""

    def observe(self, fn: Callable[[dict[str, Any]], None]) -> None:
        """fn sees every outgoing JSON-RPC message (tests, golden recording)."""

    @property
    def seconds_since_last_send(self) -> float: ...


async def serve(
    make_agent: Callable[[Outbox, ClientMode], DrAcpAgent],
    *,
    acp_out_fd: int,
    stdin_fd: int = 0,
) -> None:
    """Serve one ACP connection until the client closes stdin.

    Builds asyncio streams on (stdin_fd, acp_out_fd) with a 64 MiB reader limit, then
    Connection(handler, writer, reader), where handler is the initialize tap in front of
    build_agent_router(agent, use_unstable_protocol=True).
    """


class ClientMode:
    """Decided once per connection, by the tap, before the router sees initialize."""

    mode: Mode  # "native" iff clientCapabilities.subagents is an object and not --flat
```

`use_unstable_protocol=True` is needed for `session/close` (S2's preview closes its probe
session). Unimplemented unstable methods (`fork`, `resume`, `list`) answer method-not-found.

**`agent.py`.** The ACP surface. Handlers get the router's keyword arguments and return raw dicts.

```python
class DrAcpAgent:
    def __init__(
        self,
        outbox: Outbox,
        client: ClientMode,
        *,
        catalog: Catalog,
        home: Home,
        route: ModelRoute,
        prices: PriceTable,
        heartbeat_s: float,
    ) -> None: ...

    async def initialize(
        self,
        protocol_version: int,
        client_capabilities: Any = None,
        client_info: Any = None,
        **meta: Any,
    ) -> dict[str, Any]: ...  # §5.1

    async def new_session(
        self,
        cwd: str,
        mcp_servers: list[Any],
        additional_directories: list[str] | None = None,
        **meta: Any,
    ) -> dict[str, Any]: ...

    async def load_session(
        self,
        cwd: str,
        session_id: str,
        mcp_servers: list[Any],
        additional_directories: list[str] | None = None,
        **meta: Any,
    ) -> dict[str, Any]: ...

    async def set_config_option(
        self, config_id: str, session_id: str, value: str, **meta: Any
    ) -> dict[str, Any]: ...

    async def prompt(
        self, prompt: list[Any], session_id: str, **meta: Any
    ) -> dict[str, Any]: ...

    async def cancel(self, session_id: str, **meta: Any) -> None: ...  # root or child

    async def close_session(self, session_id: str, **meta: Any) -> dict[str, Any]: ...
```

`cancel` routes by id: a root session id → `Session.stop_root()`; an id in any live run's child
map → `Session.stop_child()`; anything else is ignored, since it is a notification and has no error
reply, and logged at WARNING (`session/cancel for unknown session '<id>' ignored`), so a client
that sent a short id such as `n3` finds out from `dr-acp`'s stderr. A cancel racing an ended agent
does not rewrite its outcome.

**`session.py`.** One per root session; holds the options, the commands and the runs; serializes
`prompt`, `set_config_option`, `load` and `close` with an `asyncio.Lock` (`cancel` never takes it).

```python
@dataclass
class Session:
    id: str  # "s-" + 16 hex
    cwd: Path
    snapshot: CatalogSnapshot
    namespace: str
    started: bool  # set by the first accepted prompt; fixes the namespace
    commands: dict[str, CommandEntry]  # by name, current namespace; empty once started
    advertised: set[str]  # every command name ever offered: detects late commands
    runs: list[str]  # run ids, oldest first
    cost: CostLedger  # the root's cumulative cost over all finished runs
    last_end: RunEndReason | None  # picks the next run's fresh-run notice
    mcp_servers: list[dict[str, Any]]  # kept for D4; unused in D1
    run: RunHandle | None  # the live run, if any
    ctx: AgentContext  # from DrAcpAgent: catalog, home, route, outbox, prices, mode

    async def prompt(self, text: str) -> PromptResult: ...

    def set_namespace(self, value: str) -> list[dict[str, Any]]:
        """The options after the change. Raises RequestError (§5.5)."""

    async def stop_root(self) -> None: ...

    def stop_child(self, child_session_id: str) -> None: ...

    async def close(self, grace_s: float = 2.0) -> None: ...


PromptOutcome = Literal[
    "answered",
    "exhausted",
    "failed",
    "build_failed",
    "stopped",
    "crashed",
    "closed",
    "rejected",
]


@dataclass(frozen=True)
class PromptResult:
    stop_reason: Literal["end_turn", "max_turn_requests", "cancelled"]
    run: str | None
    outcome: PromptOutcome
```

`Session.prompt`, exactly:
1. Refuse if a prompt is in flight (`PROMPT_BUSY`, invalid request, §5.5).
2. Text = the prompt's `text` blocks joined with `"\n"`; a `resource_link` block contributes its
   `uri` on its own line; other blocks are ignored (we advertise none).
3. Command parse: if the text starts with `/` and its first whitespace-separated token minus the
   slash is a name in `self.commands`, it is a command; otherwise, if the session has started and
   that token is in `self.advertised`, it is a *late* command; otherwise it is plain text (a path
   such as `/home/…` stays a task).
   - Late command → reply `texts.late_decomposition(name)`, outcome `rejected`, no run.
   - Command with an empty rest → reply `texts.command_needs_task(name, hint)`, outcome
     `rejected`, session stays unstarted.

   A *reply* is one root `agent_message_chunk` carrying
   `_meta.deep_reasoner = {"run": null, "prompt": null, "outcome": <outcome>}` (§5.2's closing
   message, sent by the session because no run log holds it).
4. If not started: started = True; send `available_commands_update []` then the narrowed
   `config_option_update`; write the session index.
5. If `self.run` is None: `run_id = ids.new_run_id()`; `source = await
   asyncio.to_thread(catalog.materialize, namespace, run_dir=home.run_dir(run_id))` (an exception →
   reply `texts.build_failed(detail)`, outcome `build_failed`, no run, `last_end` unchanged);
   `self.run = await RunHandle.start(run_id=run_id, source=source, after=self.last_end, …)`. The
   run's `run.start` records `after`, and the encoder sends the fresh-run notice from it (§5.2), so
   the notice is the run's first update both live and in a replay.
6. `await self.run.prompt(index, text, task, decomposition)` → `PromptEnd`. After a `failed` or
   `build_failed` outcome, `RunHandle.prompt` returns only once the worker has exited and the pump
   has logged `run.end` (the worker exits right after that `prompt.end`, §4.3), so the session's
   next prompt starts a fresh run instead of writing to a dead worker.
7. Every return path, `rejected` included, sends the root `usage_update` before returning: the
   bridge waits up to 2 s for one after every prompt (`acp_agent.py:3643–3654`).

`detail`, wherever an exception becomes one (a materialize failure here, a build or drive failure
in the worker, §4.3), is `f"{type(exc).__name__}: {exc}"`, the form deep_reasoner gives
`agent.end.detail` (`agent.py:904`), capped at 2,000 characters: for a missing key,
``ValueError: Missing API key. Set `OPENAI_API_KEY` (preferred) or `OPENAI_API_KEY`.``
(`build_client`, `config.py:256–266`, called by `build_reasoner`, `v2/cli.py:342`).

When the pump feeds a `run.end`, the session takes `cost = encoder.root_cost`, `last_end = reason`,
`run = None`, and saves the index. `stop_root` with no prompt in flight does nothing: the REPL
survives between prompts.

**`supervisor.py`.** A live run: the worker process, its two pipes, the pump.

```python
class RunHandle:
    run_id: str
    encoder: Encoder

    @classmethod
    async def start(
        cls,
        *,
        run_id: str,
        session: Session,
        source: RunSource,
        after: RunEndReason | None,
        home: Home,
        route: ModelRoute,
        outbox: Outbox,
        mode: Mode,
        heartbeat_s: float,
    ) -> RunHandle:
        """Create the run's log and worker, and start its pump and heartbeat.

        RunLog.create; append run.start (with after); grant = route.grant(session=...,
        run=run_id, upstream=source.client); spawn the worker: sys.executable -m
        deep_reasoning.acp.worker --control-fd C --events-fd E, pass_fds=(C, E),
        start_new_session=True, stdin=DEVNULL, stdout and stderr to runs/<run>/worker.log,
        cwd=session.cwd, env=worker_env(os.environ, grant); send
        Start(client_overrides=grant.client_overrides, ...).
        """

    async def prompt(
        self, index: int, text: str, task: str, decomposition: str | None
    ) -> PromptEnd:
        """Log prompt.start, send Prompt, return the prompt.end the pump receives.

        After a failed or build_failed outcome, return only once run.end is logged.
        """

    def stop_node(self, node: int) -> None:
        """Log stop.request and send Stop; return at once."""

    async def kill(self, reason: Literal["stopped", "closed"]) -> None:
        """End the worker's process group (§6.4). Idempotent."""

    async def close(self, grace_s: float = 2.0) -> None:
        """Send Close; kill("closed") if the worker has not exited after grace_s."""

    def child(self, session_id: str) -> ChildRef | None:
        """The live child with this session id, for cancel routing."""
```

`Session.close(grace_s)` closes its live run with the same grace: 2 s for `session/close`, 0.3 s at
shutdown.

The **pump** is one task per run: read a line from the event pipe → parse a RunEvent (an
unparseable line is logged to stderr and dropped) → `RunLog.append` → `Encoder.feed` → `await
Outbox.update` for each result, in order → resolve the prompt future on `prompt.end`. It also
calls `Encoder.flush_usage()` at most every 0.5 s. On EOF it waits for the process; if no `run.end`
was logged it appends one and feeds it, with `exit_code` and the first reason that applies:
`stopped` or `closed` when the front asked for the exit; `failed` or `build_failed` when the
worker's last `prompt.end` had that outcome (the worker exits 1 or 2 right after it, §4.3);
otherwise `crashed`. So a build failure leaves `last_end = build_failed` (no fresh-run notice: the
reply already said nothing ran), and a failed drive leaves `failed` (`FRESH_AFTER_ERROR`).

The **heartbeat** task, while a prompt is in flight, sends the root's `usage_update` when
`Outbox.seconds_since_last_send ≥ heartbeat_s`, which keeps the bridge's 1,800 s prompt-idle
watchdog quiet through a long cell (`acp_agent.py:1433–1439, 1758`).

### 4.3 The worker

#### Front → worker: the control pipe

**`worker/protocol.py`**: one JSON object per line.

```python
class Start(BaseModel):
    op: Literal["start"]
    run: str
    session: str
    run_dir: str
    config_path: str
    namespace: str
    client_overrides: dict[str, Any]  # merged over cfg.client


class Prompt(BaseModel):
    op: Literal["prompt"]
    prompt: int  # 1-based within the run
    task: str  # the text without its slash command
    decomposition: str | None  # the command's decomposition, first prompt only


class Stop(BaseModel):
    op: Literal["stop"]
    node: int


class Close(BaseModel):
    op: Literal["close"]


Control = Annotated[Start | Prompt | Stop | Close, Field(discriminator="op")]
```

#### Worker → front: the event pipe

RunEvents (§4.4) without `seq` and `t`, which the front assigns, one JSON object per line.

#### Inside the worker

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
   Any exception here → `prompt.end {outcome: build_failed, detail}` (§4.2's `detail` form), then
   teardown and exit 2.
4. Enter `bound_contextvars(task_id=run, log_dir=run_dir)` and `alias` once, for the whole run.
   Each `Prompt`: `answer = await reasoner.acall(task)`; emit
   `prompt.end {outcome: exhausted if reasoner.exhausted else answered, answer: as_text(answer)}`.
   An exception from `acall` → `prompt.end {outcome: failed, detail}`, then teardown and exit 1:
   after a raising drive the agent's `_done` stays false, so a later `send` would never reach the
   model (`agent.py:867–872, 749`).
5. Teardown (`Close`, failure, `RunKilled`): `close_run(reasoner)` under a 0.7 s watchdog thread that
   `os._exit(3)`s past it; then `os._exit` with 0 (`Close`, `RunKilled`), 1 (a failed drive) or 2
   (a build failure), never waiting for non-daemon sub-agent threads. The front reads the outcome
   from the last `prompt.end`, not from the code (§4.2's pump).

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

The events are grouped by the process that originates them. Every one is a `_Ev`:

```python
class _Ev(BaseModel):
    v: Literal[1] = 1
    seq: int = 0  # set by RunLog.append
    t: float = 0.0  # set by RunLog.append


RunEndReason = Literal["closed", "stopped", "crashed", "failed", "build_failed", "lost"]
```

#### Written by the front

```python
class RunStart(_Ev):
    kind: Literal["run.start"]
    run: str
    session: str
    index: int  # 1-based position of this run in the session
    after: RunEndReason | None  # the previous run's end: picks the notice
    cwd: str
    namespace: str
    mode: Mode
    decomposition: str | None
    source: dict[str, Any]  # RunSource as JSON: config_path, client, versions


class PromptStart(_Ev):
    kind: Literal["prompt.start"]
    prompt: int  # 1-based within the run
    text: str  # what the user typed
    task: str  # the text without its slash command
    decomposition: str | None


class StopRequest(_Ev):
    kind: Literal["stop.request"]
    node: int


class RunEnd(_Ev):
    kind: Literal["run.end"]
    reason: RunEndReason
    exit_code: int | None
    detail: str | None
```

#### Sent by the worker

```python
class WorkerReady(_Ev):
    kind: Literal["worker.ready"]
    pid: int
    deep_reasoner: str  # the installed version
    stop_mode: Literal["dean", "interim"]


class AgentStart(_Ev):
    kind: Literal["agent.start"]
    node: int
    parent: int | None
    ancestry: list[int]  # agent nodes only, root first, ending in node
    depth: int  # len(ancestry): the root is 1
    task: str
    namespace: str
    backbone: str  # "chat", "claude_code", or the agent's class name
    max_iter: int | None
    drive: int  # 1 on the first drive of this node
    parent_cell: int | None  # the parent's open cell; None for the root
    dr_run: str | None  # deep_reasoner's own run slug


class Thought(_Ev):
    kind: Literal["thought"]
    node: int
    text: str


class CellStart(_Ev):
    kind: Literal["cell.start"]
    node: int
    cell: int  # 1-based per node
    code: str  # "" while unknown (origin "inferred")
    origin: Literal["think", "puppeteered", "inferred"]


class CellEnd(_Ev):
    kind: Literal["cell.end"]
    node: int
    cell: int
    code: str
    output: str  # the observation without its <observation> wrapper
    interrupted: bool = False  # the agent ended before the cell reported


class Usage(_Ev):
    kind: Literal["usage"]
    node: int  # the owning agent
    call: Literal["think", "tool", "claude"]
    model: str | None
    tokens_in: int
    tokens_out: int
    cost_usd: float | None
    cost_source: Literal["provider", "table", "claude"] | None
    context_window: int | None


class StopAccepted(_Ev):
    kind: Literal["stop.accepted"]
    node: int
    mode: Literal["dean", "interim"]
    accepted: bool
    reason: str | None
    backbone: str | None


class AgentEnd(_Ev):
    kind: Literal["agent.end"]
    node: int
    status: Literal["done", "exhausted", "failed", "stopped"]
    dr_status: str  # deep_reasoner's own: done, exhausted, failed or stopped
    iter: int | None
    answer: str | None
    detail: str | None
    stopped_by: int | None  # the target whose stop ended this node (§6.3)
    collateral: bool = False  # interim: cancelled beside its stopped sibling (§6.3)


class PromptEnd(_Ev):
    kind: Literal["prompt.end"]
    prompt: int
    outcome: Literal["answered", "exhausted", "failed", "build_failed"]
    answer: str | None
    detail: str | None
```

#### The log itself

```python
RunEvent = Annotated[
    RunStart
    | PromptStart
    | StopRequest
    | RunEnd
    | WorkerReady
    | AgentStart
    | Thought
    | CellStart
    | CellEnd
    | Usage
    | StopAccepted
    | AgentEnd
    | PromptEnd,
    Field(discriminator="kind"),
]


class RunLog:
    @classmethod
    def create(cls, home: Home, run_id: str) -> RunLog: ...

    def append(self, ev: RunEvent) -> RunEvent:
        """Assign seq and t, write one line, flush."""

    @staticmethod
    def read(home: Home, run_id: str) -> Iterator[RunEvent]:
        """Every event of the run, in order. Raises on v != 1."""
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
# (sessionId, the "update" object of a session/update notification)
Update = tuple[str, dict[str, Any]]


@dataclass(frozen=True)
class CostLedger:
    usd: float = 0.0
    complete: bool = True  # False once any contributing call had no cost estimate
    tokens_in: int = 0
    tokens_out: int = 0


@dataclass(frozen=True)
class ChildRef:
    node: int
    running: bool


class Encoder:
    def __init__(
        self,
        *,
        root: str,
        run: str,
        mode: Mode,
        replay: bool = False,
        carry: CostLedger = CostLedger(),
    ) -> None: ...

    def feed(self, ev: RunEvent) -> list[Update]:
        """The updates one RunEvent produces: §5.2 (native), §5.3 (flat)."""

    def flush_usage(self) -> list[Update]:
        """A usage_update for each session whose totals changed since the last flush."""

    def root_usage(self) -> Update:
        """The root's usage_update, always."""

    def child(self, session_id: str) -> ChildRef | None: ...

    @property
    def root_cost(self) -> CostLedger:
        """carry plus this run's root total."""
```

### 4.6 The catalog: the seam to D2

```python
class Catalog(Protocol):
    def snapshot(self) -> CatalogSnapshot:
        """Blocking: the front runs it in a thread."""

    def materialize(self, namespace: str, *, run_dir: Path) -> RunSource:
        """Blocking: the front runs it in a thread."""


@dataclass(frozen=True)
class CommandEntry:
    name: str  # the slash command without "/": the decomposition name, slugged
    decomposition: str  # the name main_decomposition_turns looks up
    description: str  # the use-when line
    hint: str  # shown until the task is typed


@dataclass(frozen=True)
class CatalogSnapshot:
    namespaces: tuple[str, ...]  # "root" first, then by name
    default_namespace: str
    commands: Mapping[str, tuple[CommandEntry, ...]]  # namespace -> its menu


@dataclass(frozen=True)
class RunSource:
    config_path: Path  # a plain dr main.yaml the worker loads
    namespace: str  # becomes cfg.entry_namespace
    client: Mapping[str, Any]  # the config's client block as loaded: D5's upstream
    versions: Mapping[str, Any]  # recorded in run.start
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

**Every decomposition is offered, including few-shot examples written for one input (v2,
decided).** Most of deep_reasoner_beta's decompositions are worked examples, not programs:
deep_reasoner itself says one "not parametrised over `task` … usually means it was written for one
input" (`decomposition_turns`, `decompositions.py:188–189`). But some unparametrised ones are
programs (the live doc's `compare departments` runs the same survey whatever the question, then the
model answers it), `dr --main-decomposition` accepts any name, and the spec makes the menu "the
conversation namespace's decompositions". So `ConfigCatalog` filters nothing; one that cannot be
puppeteered fails at the first prompt with deep_reasoner's own message (`build_failed`). Marking
which decompositions are programs is a Library field, so it is D2's to add (§10).

**D2 implements `Catalog`**, with `materialize` writing the plain `dr` config directory into
`run_dir / "config"` and returning its `main.yaml`, the profile's client block and the versions it
used. Nothing in D1 changes when D2 lands except the default in `cli.py`.

### 4.7 Model route and costs: the seam to D5

```python
@dataclass(frozen=True)
class RouteGrant:
    client_overrides: Mapping[str, Any]  # merged over cfg.client (D5: base_url)
    env_add: Mapping[str, str]  # added to the worker's env (D5: its token)
    env_remove: frozenset[str]  # removed from it (D5: the provider keys)


class ModelRoute(Protocol):
    def grant(
        self, *, session: str, run: str, upstream: Mapping[str, Any]
    ) -> RouteGrant: ...

    def release(self, run: str) -> None: ...


# Glob patterns.
ALWAYS_REMOVED: tuple[str, ...] = (
    "OH_SECRET_KEY",
    "OH_SESSION_API_KEYS_*",
    "SESSION_API_KEY",
)


class DirectRoute:
    """D1's only route: no overrides; the provider keys stay in the environment."""

    def grant(
        self, *, session: str, run: str, upstream: Mapping[str, Any]
    ) -> RouteGrant: ...

    def release(self, run: str) -> None: ...


def worker_env(base: Mapping[str, str], grant: RouteGrant) -> dict[str, str]:
    """base minus ALWAYS_REMOVED and grant.env_remove, plus grant.env_add and
    PYTHONUNBUFFERED=1."""
```

The agent-server's own secrets (`OH_SECRET_KEY`, `OH_SESSION_API_KEYS_0`, which every ACP agent
inherits) never reach the worker, from D1 on. D5 adds `ProxyRoute` and the spend cap; until then
the worker reads the provider key from its environment, as `dr` does.

**So the key must be in `dr-acp`'s environment, and putting it there is the client's job** (§5.1).
OpenHands' bridge passes the agent-server's whole environment plus the conversation's secrets
(`acp_agent.py:2926–2952`). ACP Python's `spawn_stdio_transport` passes only `HOME`, `LOGNAME`,
`PATH`, `SHELL`, `TERM` and `USER` unless it is given `env=` (`DEFAULT_INHERITED_ENV_VARS`,
`transports.py:13–30`). Without the key the first prompt answers `build_failed` with
deep_reasoner's own message, which names the variable (§4.2's `detail`).

**`costs.py`.** Chat-backbone cost is an estimate until A7.

```python
@dataclass(frozen=True)
class Price:
    input_per_mtok: float
    output_per_mtok: float
    context_window: int | None


@dataclass(frozen=True)
class CostEstimate:
    usd: float | None
    source: Literal["provider", "table", "claude"] | None
    tokens_in: int
    tokens_out: int
    context_window: int | None


class PriceTable:
    @classmethod
    def load(cls, home: Home) -> PriceTable:
        """The package's prices.yaml, with $DR_HOME/prices.yaml over it."""

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
responses; checked 2026-10-02 with `jsonschema` 4.26, and v2's additions the same day: the closing
message, the fresh-run notice, `collateral` and a crashed idle update).

### 5.1 Launch, capabilities and ids

**Launch.** `dr-acp --config PATH [--home DIR] [--flat]`, ACP on stdio, logs on stderr. Until D5's
key proxy, the worker reads the model key from `dr-acp`'s environment under the config's
`client.api_key_env` (or `OPENAI_API_KEY`), so **a client must start `dr-acp` with that variable
set**: OpenHands' bridge passes its whole environment; ACP Python's `spawn_stdio_transport` passes
six variables unless given `env=` (§4.7). A missing key is not a launch error; the first prompt
answers `build_failed` and says which variable to set. Shutdown: close stdin or send SIGTERM;
`dr-acp` has closed its runs and exited within 1.4 s (§4.2).

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
short forms are what the spec's mock-ups print. **They are for display only:** every run has an
`n2` and a `c1.1`, so on the wire, and in `session/cancel`, ids are always the full ones
(`ids.short` maps full to short, never back).

### 5.2 Emission table, native mode

`S(n)` is node n's session (the root session for the root). `cellId(n, k)` and the message ids are
§5.1's. `DR` below is `{"run", "node", "parent", "depth", "namespace", "backbone", "drive"}` from
the node's `agent.start`. Every row is sent in this order, before anything the next RunEvent
produces.

A **closing message** `CM(text, outcome)` is the root message that ends a turn or a run:
`root` → `agent_message_chunk` `{"content": {"type": "text", "text": text}, "_meta":
{"deep_reasoner": {"run": run, "prompt": p, "outcome": outcome}}}`, where `p` is the prompt it
answers (the run's latest `prompt.start`) and `outcome` is one of `PromptResult.outcome`'s values or
`lost`. It is the only root `agent_message_chunk` with `_meta.deep_reasoner`, so a client that reads
`_meta` can tell an answer from the fresh-run notice, and which run and prompt it closes.

| RunEvent | Sent (session → update) |
|---|---|
| (not a RunEvent) a prompt the session rejects, or a `materialize` failure (§4.2) | `CM(text, "rejected" or "build_failed")` with `run` and `prompt` null |
| first prompt accepted | `root` → `available_commands_update` `{"availableCommands": []}`; `root` → `config_option_update` with `namespace` narrowed to the chosen value |
| `run.start` whose `after` has a notice (§5.6: `stopped`, `failed`, `crashed`, `lost`, `closed`) | `root` → `agent_message_chunk` `{"content": {"type": "text", "text": notice + "\n\n"}}`, no `_meta`. It is the run's first update; the blank line keeps it a paragraph of its own when a client joins a turn's chunks into one message, as OpenHands' bridge does (`"".join(accumulated_text)`, `acp_agent.py:3762`). |
| `agent.start` (root) | nothing |
| `agent.start` (child, drive 1) | `S(parent)` → `subagent_update` `{"sessionId": S(node), "title": T, ["description": task,] "capabilities": {"cancel": {}}, "state": {"state": "running"}, "_meta": {"openhands": {"parentToolCallId": cellId(parent, parent_cell)}, "deep_reasoner": DR}}`; then `S(parent)` → `session_message` `{"messageId": "<S(node)>-t1", "senderSessionId": S(parent), "recipientSessionId": S(node), "content": [{"type": "text", "text": task}]}` |
| `agent.start` (child, drive d > 1: the same child given new work) | `S(parent)` → `subagent_update` `{"sessionId", "title": T, "state": {"state": "running"}, "_meta": {…the current parent cell…, DR with drive d}}`; then the task `session_message` with id `-t<d>` |
| `thought` | `S(node)` → `agent_thought_chunk` `{"content": {"type": "text", "text": …}}` |
| `cell.start` | `S(node)` → `tool_call` `{"toolCallId": cellId, "title": "Run <first line>[ …]" or "Run …" when the code is unknown, "kind": "execute", "status": "in_progress", "rawInput": {"command": code}, "_meta": {"deep_reasoner": {"run", "node", "parent", "depth", "cell", "origin"}}}` |
| `cell.end` | `S(node)` → `tool_call_update` `{"toolCallId", "status": "completed", "content": [{"type": "content", "content": {"type": "text", "text": out}}], "rawOutput": out}`, adding `"title"` and `"rawInput"` when the start had no code; `interrupted` → `"status": "failed"` and the text `texts.cell_interrupted("the agent stopped")` |
| `usage` | nothing at once; the session and all its agent ancestors become dirty (§6.2) |
| (pump, ≤ every 0.5 s) | each dirty session → `usage_update` (§6.2) |
| `stop.accepted` | `S(node)` → `agent_thought_chunk` with `texts.stop_requested(mode, backbone)` (§5.6); nothing when `accepted` is false |
| `agent.end` (child) | if `answer`: `S(node)` → `session_message` `{"messageId": "<S(node)>-r<d>", "senderSessionId": S(node), "recipientSessionId": S(parent), "content": [text answer]}`; if `failed`: the same with `texts.child_failed(detail)`; then `S(node)` → its final `usage_update`; then `S(parent)` → `subagent_update` `{"sessionId": S(node), "state": {"state": "idle", "stopReason": R}, "_meta": {"openhands": {…}, "deep_reasoner": DR + {"status", ["detail",] ["stopped_by",] ["collateral": true]}}}` with R from the table below. An open cell of the node is first closed as `interrupted`. |
| `agent.end` (root) | nothing (`prompt.end` speaks for the root) |
| `prompt.start` | nothing live; in a replay, `root` → `user_message_chunk` with `text` |
| `prompt.end` | `CM(answer, outcome)` for answered and exhausted, `CM(texts.root_failed(detail), "failed")`, or `CM(texts.build_failed(detail), "build_failed")`; then `root` → `usage_update`. The prompt's response follows. |
| `run.end` `stopped`, `crashed` or `closed` while a prompt is in flight (its `prompt.end` not yet received) | for each running agent, deepest first and by node within a depth: its open cell → `tool_call_update` failed with `texts.cell_interrupted(reason)`, then, for a child, `S(parent)` → `subagent_update` idle (`stopped`, `closed`: `stopReason: "cancelled"`, `status: "stopped"`; `crashed`: no `stopReason`, `status: "crashed"`); then the root's open cell, failed likewise; then `CM(texts.ROOT_STOPPED, reason)` for stopped and closed, or `CM(texts.crashed(code, path), "crashed")`; then `root` → `usage_update` |
| `run.end` `lost` (replay only) | `CM(texts.REPLAY_LOST, "lost")`; nothing for children (the RFD forbids manufacturing an outcome from a gap) |
| `worker.ready`, `stop.request`; `run.end` `failed` or `build_failed` (its `prompt.end` has spoken); any `run.end` between prompts | nothing |

`T` (title) = the task's first line, at most 120 characters, with ` …` when cut; `description` is
the whole task (at most 2,000 characters) and is sent only when the title was cut.

| `agent.end.status` | `stopReason` | `_meta.deep_reasoner.status` |
|---|---|---|
| done | `end_turn` | `done` |
| exhausted | `max_turn_requests` | `exhausted` |
| failed | `end_turn` (ACP has no failure reason) | `failed`, with `detail` |
| stopped | `cancelled` | `stopped`, with `stopped_by` (the target whose stop ended it, §6.3), `detail`, and `collateral: true` when it was cancelled beside the target in a `run_all` rather than in the target's branch |

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
| `agent.end` (child) | `tool_call_update` on its card: `completed` for done/exhausted with the answer as content; `failed` for failed (`texts.child_failed(detail)`) and stopped (`detail`); `_meta.deep_reasoner` = `{"run", "node", "status", ["detail",] ["stopped_by",] ["collateral": true]}`, the same outcome keys as a native idle update |
| `run.end` in flight | as in §5.2, with each child's card in place of its idle update: for each running agent, deepest first and by node within a depth, its open cell → `failed`, then its card → `failed` with `texts.cell_interrupted(reason)`; then the root's open cell; then the closing message and usage |

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
   `set_config_option` response as current. A client must wait for it: ACP Python 0.12.1 resolves
   the `new_session` call as soon as the response arrives, before it handles the notification
   that follows (P6), so reading the commands right after `await conn.new_session(...)` finds none.
6. `session/load` sends the whole replay before its response, and nothing about children after it.
7. No child traffic follows the root's prompt response: a run's children have all ended (or been
   reported ended) before it. S1 persists late child traffic anyway; `dr-acp` sends none in v1.

### 5.5 Requests

| Request | Behaviour |
|---|---|
| `session/new` | §2 step 2. Response `{"sessionId", "configOptions": [namespace option]}`. A catalog that cannot be read → JSON-RPC internal error with `CATALOG_ERROR`. |
| `session/load` | Unknown id → invalid params (`UNKNOWN_SESSION`); the bridge then starts a new session. A session already open in this process is closed first (graceful); then replay (§5.7), response `{"configOptions": […]}`, then, if not started, the commands. The new `cwd` is used for the next run. |
| `session/set_config_option` | `configId` must be `namespace` (else invalid params, `UNKNOWN_OPTION`); value must be a catalog namespace (`UNKNOWN_NAMESPACE`); after the first prompt any value but the current one fails with `NAMESPACE_FIXED`, which S2 passes through as its 422. Response `{"configOptions": [namespace option]}`. |
| `session/prompt` | `Session.prompt` (§4.2). A second prompt in flight → invalid request (`PROMPT_BUSY`). |
| `session/cancel` | §2 steps 8–9. `sessionId` is a root session id or a full child session id (`<run>-n<node>`); an id that matches nothing is ignored and logged at WARNING (§4.2). |
| `session/close` | Graceful close of the live run (`Session.close(grace_s=2.0)`; a prompt in flight ends `cancelled`), session forgotten in memory; the index stays on disk. Response `{}`. |

**Errors.** A refused request is a JSON-RPC error whose `message` is the §5.6 sentence, verbatim,
and whose `data` is `{"deep_reasoner": {"error": "<the sentence's name>"}}`, for instance
`{"code": -32602, "message": "namespace is fixed once a conversation has started (it is
'router').", "data": {"deep_reasoner": {"error": "NAMESPACE_FIXED"}}}`. S2 passes `message` through
as its 422's `detail`. ACP Python raises it on the client as `acp.RequestError`, whose `str()` is
the `message` and whose `.data` is the `data` (`connection.py:249`). Codes: `UNKNOWN_SESSION`,
`UNKNOWN_OPTION`, `UNKNOWN_NAMESPACE` and `NAMESPACE_FIXED` are invalid params (-32602);
`PROMPT_BUSY` is invalid request (-32600); `CATALOG_ERROR` is internal error (-32603).
`RequestError`'s class constructors put a generic phrase in `message`, so `dr-acp` builds its
errors as `RequestError(code, sentence, data)`.

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

The Docwright's artifacts quote these; changing one is a design change. A sentence without fields
is a constant (`texts.ROOT_STOPPED`); one with `{fields}` is a function of them in lower case that
returns an f-string (`texts.late_decomposition(name)`, `texts.build_failed(detail)`), since the
Code Guide forbids `.format()`. The upper-case name is what an error's `data` carries (§5.5).
`detail` is §4.2's `f"{type(exc).__name__}: {exc}"`.

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
| (all four `FRESH_AFTER_*`) | sent as the new run's first update, an `agent_message_chunk` of the sentence plus `"\n\n"` (§5.2's `run.start` row), chosen by `run.start.after` |
| `BUILD_FAILED` | `Could not start the run: {detail}` (no fresh-run notice follows: nothing ran). For a missing key: ``Could not start the run: ValueError: Missing API key. Set `OPENAI_API_KEY` (preferred) or `OPENAI_API_KEY`.`` (deep_reasoner names the variable twice when the config's `api_key_env` is `OPENAI_API_KEY`) |
| `ROOT_FAILED` | `The run failed: {detail}. Its REPL state is gone; your next message starts a fresh run.` |
| `CRASHED` | `The run crashed (exit code {code}) and its REPL state is gone. Your next message starts a fresh run. The worker's log is {path}.` |
| `REPLAY_LOST` | `(This run ended when dr-acp stopped; its REPL state is gone.)` |
| `CHILD_FAILED` | `Failed: {detail}` |
| `CELL_INTERRUPTED` | `Not finished: {reason}` (`the run was stopped`, `the run crashed`, `the agent stopped`) |
| `stop_requested`, interim or Dean, chat | `Stop requested: this agent and its sub-agents stop at their next turn, before their next model call. A cell that is already running finishes first.` |
| `stop_requested`, interim, Claude backbone | `Stop requested: this agent runs a Claude Code session, which is one turn, so it stops when that session ends.` |
| `stop_requested`, Dean, Claude backbone | `Stop requested: its Claude Code session is being ended.` |
| `StoppedByUser` (interim, the exception's message) | `stopped #{t}[ and its branch (#a, #b)].[ Its running sibling #s in this run_all was stopped with it (A3).]` plural: `Its running siblings #s, #u in this run_all were stopped with it (A3).` (the mock-up's; `branch` and `siblings` as §6.3 defines them). The parent's cell output shows it as the last line of a traceback, `deep_reasoning.acp.worker.stop.StoppedByUser: stopped #2 and its branch (#4, #5).` (§3 item 14); the stopped agent's `detail` is `StoppedByUser: …` (deep_reasoner's unqualified form) |

### 5.7 `session/load` replay

1. Read the index (unknown → error). For each run id in order: if its log has no `run.end`, append
   `run.end {reason: lost}` (the dr-acp process that owned it is gone; its worker exits on control
   EOF); then feed every event to a fresh `Encoder(replay=True)` and send what it returns.
2. Replay differs from live in two ways only: an announcement carries no `capabilities` (historical
   capabilities must not authorize a Stop: the RFD's freshness rule), and no intermediate
   `usage_update` is sent (only each agent's final one and the root's at each `prompt.end`).
   Fresh-run notices and closing messages replay exactly as they were sent, since both come from
   the log (`run.start.after`, `prompt.end`, `run.end`). Rejected prompts do not replay (§3 item 11).
3. The response, then the commands if the session never started. No live child snapshot follows:
   after a restart there is no live child to describe.
4. The session's next prompt starts a fresh run with `FRESH_AFTER_RESTART` (or the notice for the
   last recorded end).

### 5.8 `_meta` keys, all of them

| Key | On | Meaning | Read by |
|---|---|---|---|
| `_meta.openhands.parentToolCallId` | `subagent_update` (native), flat agent cards | the `toolCallId` of the parent's cell that spawned (or re-drove) the child; always a call already sent on the parent's session | S1 (persists), C1 (placement) |
| `_meta.deep_reasoner.{run,node,parent,depth,namespace,backbone,drive}` | `subagent_update`, flat cards | the node's identity in deep_reasoner's tree | E1, our tests, golden replays; no fork |
| `_meta.deep_reasoner.{status,detail,stopped_by,collateral}` | idle `subagent_update`, closed flat cards | outcome (`done`, `exhausted`, `failed`, `stopped`, `crashed`); for `stopped`, the target whose stop ended it and, with `collateral: true`, that it was cancelled beside the target rather than in its branch | as above, `testing.tree` |
| `_meta.deep_reasoner.{run,prompt,outcome}` | the root's closing `agent_message_chunk` (§5.2's `CM`) | which run and prompt the message closes, and how (`PromptResult.outcome` or `lost`); `run` and `prompt` null for a rejected prompt | `testing.tree`, tests |
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
def stop(node_id: int) -> None: ...
```

1. Thread-safe: callable from any thread. 2. Takes effect at the agent's next turn, before its next
model call. 3. Its descendants stop too. 4. The agent ends with its own `agent.end` status
`stopped`, beside `done`, `failed` and `exhausted`. 5. Its parent's cell sees a returned value or an
`Exception`, never a `CancelledError`. 6. `run_all` returns the other children's results, with the
stopped one marked. 7. A Claude-backbone agent's `claude` process is ended.

**`worker/stop.py`:**

```python
# "module:attr" of Dean's stop(node_id), set when he ships it. DR_ACP_STOP_API overrides
# it (the tests point it at the fake). None means the interim.
DEAN_STOP_API: str | None = None


class StoppedByUser(Exception):
    """Interim only. An Exception, so the parent's cell catches it.

    Cells catch Exception (repls/backends.py:523, v2/repl_coro.py:84). The message is
    §5.6's StoppedByUser sentence.
    """

    def __init__(
        self, target: int, branch: tuple[int, ...], siblings: tuple[int, ...]
    ) -> None: ...


@dataclass(frozen=True)
class StopReceipt:
    node: int
    mode: Literal["dean", "interim"]
    accepted: bool  # False: unknown node, or it already ended
    reason: str | None


class StopAdapter(Protocol):
    mode: Literal["dean", "interim"]

    def stop(self, node_id: int) -> StopReceipt:
        """Thread-safe; returns at once."""


class DeanStop:
    """The one place dr-acp calls deep_reasoner's stop."""

    mode: Literal["dean"] = "dean"

    def __init__(self, fn: Callable[[int], None], recorder: Recorder) -> None: ...

    def stop(self, node_id: int) -> StopReceipt:
        """recorder.note_stop(node_id, "dean"), then fn(node_id)."""


class InterimStop:
    mode: Literal["interim"] = "interim"

    def __init__(self, recorder: Recorder) -> None: ...

    def stop(self, node_id: int) -> StopReceipt:
        """recorder.arm(node_id)."""


def resolve_stop_adapter(recorder: Recorder, spec: str | None) -> StopAdapter: ...
```

Both adapters make the recorder emit `stop.accepted` and record the target, so classification
works the same in both modes. **When Dean ships, the change is one line**: `DEAN_STOP_API`.

**Targets.** The recorder keeps every accepted target with the drive it had when the stop was
accepted. A target is **armed** while that drive is still its current one: ending does not disarm
it (its siblings may be cancelled after it ends, and their classification needs it), but a new
drive does, so a child the root re-drives after a stop runs normally (the stop was for the earlier
work). A target's **branch** is every agent other than the target with the target in its ancestry
that was running when the stop was accepted or started after it, ending or not; a branch member
is never re-driven before the target ends, so the set is well defined.

**The interim** (verified by the spec's third probe): at `agent.turn` of node n, if an armed target
t is n or is in n's ancestry (the nearest one, if several), raise `StoppedByUser(t, branch,
siblings)`, where `branch` is t's branch as defined above, ascending, including members that have
already ended (so the text is the same wherever it surfaces), and `siblings` is, when n is t
itself, the agents other than t running now that were opened in t's parent cell (they are in its
`run_all`, which deep_reasoner's `gather` will cancel, `agent.py:158–174`), and is empty when n is a
branch member (whose siblings are branch members too). A branch unwinds bottom-up: a stopped
parent blocked in a cell reaches its next turn when its stopped children have ended.

So stopping a department n2 while its course agents n4 and n5 run (the live doc's case): n4
reaches its turn first and raises `stopped #2 and its branch (#4, #5).`, which n2's cell catches;
`gather` cancels n5 before its turn; n2 then reaches its own turn and raises
`stopped #2 and its branch (#4, #5). Its running sibling #3 in this run_all was stopped with it
(A3).`, which the root's cell catches, and `gather` cancels n3.

**Classification at `agent.end`**, rows checked in order:

| deep_reasoner says | and | `status` | `stopped_by` | `collateral` |
|---|---|---|---|---|
| `stopped` (Dean) | — | `stopped` | the nearest target that is the node or in its ancestry | false |
| `failed`, detail starts `StoppedByUser` | — | `stopped` | the exception's target | false |
| `failed`, detail starts `CancelledError` | an armed target is the node or in its ancestry | `stopped` | the nearest such target | false |
| `failed`, detail starts `CancelledError` | an armed target was opened in the node's parent cell | `stopped` | that target | true |
| `failed`, otherwise | — | `failed` | — | — |
| `done`, `exhausted` | — | as is (a cancel racing ended work does not rewrite it) | — | — |

In the example, n4 is row 2 (`stopped`, by #2), n5 row 3 (`stopped`, by #2; v1 classified it
`failed` and sent `Failed: CancelledError: ` to n2), n2 row 2 (`stopped`, by itself), n3 row 4
(`stopped` with #2, collateral).

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

`closed` (`session/close`, `dr-acp` shutting down) is `RunHandle.close(grace_s)`: a `Close` op,
and if the worker has not exited after `grace_s` (2 s for `session/close`, 0.3 s at shutdown, §4.2),
steps 1–5 with reason `closed`. `crashed` (the worker exited without being asked) goes through
steps 3–5. A worker that exits after a failed or build-failed prompt is not forced: the pump logs
`run.end` `failed` or `build_failed` (§4.2).

---

## 7 · Signature index

Load-bearing signatures are given in full where their module is described: `Options`, `main`,
`guard_stdout` and `Outbox`, `serve`, `ClientMode` (§4.2); `DrAcpAgent`, `Session`, `PromptResult`,
`RunHandle` (§4.2); the control messages (§4.3); every RunEvent, `RunLog` (§4.4); `Encoder`,
`ChildRef`, `CostLedger` (§4.5); `Catalog`, `CatalogSnapshot`, `CommandEntry`, `RunSource`,
`ConfigCatalog` (§4.6); `ModelRoute`, `RouteGrant`, `DirectRoute`, `worker_env`, `PriceTable`,
`Price`, `CostEstimate` (§4.7); `StopAdapter`, `DeanStop`, `InterimStop`, `StoppedByUser`,
`StopReceipt`, `resolve_stop_adapter`, `DEAN_STOP_API` (§6.3); `Caps`, `ShimConnection`,
`Printer`, `Subagent`, `SubagentMap`, `tree`, `Tree` and its nodes (§8.2). The rest, by process:

#### Front process

```python
# ids.py
def new_session_id() -> str:
    """'s-' + secrets.token_hex(8)."""


def new_run_id(now: datetime | None = None) -> str: ...


def child_session_id(run: str, node: int) -> str: ...


def cell_id(run: str, node: int, k: int) -> str: ...


def card_id(run: str, node: int, drive: int) -> str: ...


def task_message_id(run: str, node: int, drive: int) -> str: ...


def answer_message_id(run: str, node: int, drive: int) -> str: ...


def short(id_: str) -> str:
    """§5.1's display form: "n2" for <run>-n2, "c2.1" for <run>-n2-c1, "a2.1" for
    <run>-n2-a1, "root" for a root session ("s-..."); any other id unchanged."""


# runlog.py
@dataclass(frozen=True)
class Home:
    root: Path

    @classmethod
    def resolve(cls, flag: Path | None) -> Home:
        """flag, else $DR_HOME, else ~/.deep-reasoning."""

    def run_dir(self, run: str) -> Path: ...

    def session_file(self, session: str) -> Path: ...


class SessionIndex(BaseModel):
    """The JSON of §4.4."""

    v: Literal[1] = 1
    session: str
    cwd: str
    namespace: str
    started: bool
    source: dict[str, Any]
    runs: list[str]
    cost: CostLedger
    last_end: RunEndReason | None
    created: datetime

    @classmethod
    def load(cls, home: Home, session: str) -> SessionIndex | None: ...

    def save(self, home: Home) -> None:
        """Atomic: a temp file, then rename."""
```

#### Worker process

```python
# worker/recorder.py
class EventSink:
    def __init__(self, fd: int) -> None: ...

    def emit(self, ev: Mapping[str, Any]) -> None:
        """One JSON line, under the recorder's lock."""


class Recorder:
    def __init__(self, sink: EventSink) -> None: ...

    def __call__(
        self, logger: Any, method_name: str, event_dict: dict[str, Any]
    ) -> dict[str, Any]: ...

    def set_puppeteer(self, turns: Sequence[str]) -> None: ...

    def note_stop(self, node: int, mode: Literal["dean", "interim"]) -> StopReceipt:
        """Record an accepted target (§6.3) and emit stop.accepted."""

    def arm(self, node: int) -> StopReceipt:
        """Interim: note_stop(node, "interim"); the target now raises at agent.turn."""

    def emit(self, kind: str, **fields: Any) -> None:
        """The runner's own events: worker.ready, prompt.end."""


# worker/runner.py
def main(argv: Sequence[str] | None = None) -> int:
    """python -m deep_reasoning.acp.worker --control-fd N --events-fd M."""


class RunKilled(BaseException): ...


def as_text(value: Any) -> str: ...
```

#### Tests only

```python
# testing/fake_model.py
class FakeOpenAI:
    """POST /v1/chat/completions on 127.0.0.1, as an async context manager.

    .base_url is the endpoint; .calls records each call's start time and messages.
    """

    def __init__(
        self,
        responder: Callable[[list[dict[str, Any]]], str],
        *,
        latency_s: float = 0.0,
        usage: Callable[[list[dict[str, Any]], str], dict[str, Any]] | None = None,
    ) -> None: ...
```

---

## 8 · Testing

### 8.1 Layers, mapped onto E1–E4 and E11

| Experiment | Where | How |
|---|---|---|
| **E1** tree fidelity | `tests/acp/test_tree_fidelity.py` | The spec's eight scripted runs (`tests/acp/scenarios.py`: linear; `run_all` of 2 and of 20; depth 3; a spawn into another namespace; `fork()`; exhausted; a failing cell; the Claude backbone with deep_reasoner's `write_fake_claude_cli`), each a small `dr` config with `client.base_url` at `FakeOpenAI`. `dr-acp` is spawned over stdio; a `ShimConnection` client records every update, in native and in flat mode; `testing.tree()` rebuilds parent links and cells per node; deep_reasoner's own tree comes from its node YAMLs (their `ancestry`) and its `repl.execute` count per node, in the same run directory. Null: any difference. |
| **E2** stdio integrity | `test_stdio_integrity.py` | A tool printing 10 MB to `sys.stdout`; `os.write(1, …)` in a cell; `os._exit(1)` in a cell; a print at the front's import time (monkeypatched module). Every outgoing line must parse as JSON-RPC; after the crash the next prompt answers (fresh run). |
| **E3** stop | `test_stop.py` | Root Stop during `while True: pass` and during a 20-way fan-out: `cancelled` within 2 s (the spec allows 5; the bridge needs 2). One child of a 20-way fan-out with children of its own, through the interim and through the fake Dean API. `FakeOpenAI` timestamps each call and attributes it by the task in its messages. Null: any call started after the stop by an agent of the stopped branch; any agent of the stopped branch reported `failed` rather than `stopped` (v2: one cancelled by `gather` before its own turn included); with the fake API, a sibling's result missing from the parent's `run_all`; in the interim, a sibling cancelled without the parent's cell output naming it. |
| **E4** contracts | `test_tripwire.py`, `test_schema.py` | Tripwire: every deep_reasoner event and field §6.1 reads, checked on scripted runs (names, the `<observation>` wrapper, the `FinalAnswer:` line, `kind` of think and tool calls, `agent.start` per drive), at `d7334ae` on every push and against Dean's `main` weekly. Schema: an `Outbox` observer validates every outgoing message (updates and responses) against the vendored `tests/acp/schema/acp-1.24.1.unstable.json` (sha256 checked) in every test that runs `dr-acp`. Red is reported, never absorbed. |
| **E11** (D1's part) | `test_surfaces.py` | Commands per namespace, changed by `set_config_option`; cleared and narrowed at the first prompt; the late-command and fixed-namespace errors verbatim; the run log's `run.start.namespace` equals the chosen one. |
| replay, shutdown | `test_load.py` | Kill `dr-acp` mid-run, start a new one, `session/load`: the replayed tree (`testing.tree`) equals the live one, notices and closing messages included, the response comes last, no child snapshot follows, the next prompt is fresh. Closing stdin mid-run, and separately SIGTERM, leave `run.end closed` in the run log within 1.4 s, so a replay never says `lost` after a clean shutdown. A failed and a build-failed prompt each leave `run.end` with that reason and pick the right notice (or none). |
| units | `test_encoder.py`, `test_recorder.py`, `test_costs.py`, `test_catalog.py`, `test_client.py`, `test_tree.py` | The encoder from hand-written RunEvents, both modes; the recorder fed synthetic event dicts in each order of §6.1, including inferred and puppeteered cells, and each row of §6.3's classification table (a re-driven target included); `Printer` lines, `subagents` lookups and `wait_until`, and `tree()` drawings, from hand-written update streams covering every row of §8.2's tables, two conversations on one connection and two runs in one conversation; prices; slugs and collisions; `ConfigCatalog` over small configs of our own, and over deep_reasoner_beta's `docs/configs` read in place when `DR_BETA_CHECKOUT` points at a checkout (skipped otherwise; never copied here). |

### 8.2 Fakes and helpers

- **`testing.fake_model.FakeOpenAI`**: `POST /v1/chat/completions` on 127.0.0.1 from a responder,
  with optional latency and usage, recording each call's start time and messages. Tests and the
  live doc use real HTTP, so the worker runs unmodified and D5's proxy can later sit in front of it.
- **`tests/acp/fakes/dean_stop.py`**: §6.3.
- **`testing.client`** and **`testing.tree`**, below: the client side the tests and the live doc
  share. The live doc imports the same modules, so everything below is the live doc's contract as
  much as §5 is S1's.

#### `testing.client`: `Caps`, `ShimConnection`, `Printer`

`Caps` and `ShimConnection` are the spec's shim (copied, not imported from the SDK fork: `dr-acp`
never imports OpenHands).

```python
UNSTABLE_UPDATES = frozenset(
    {"subagent_update", "session_message", "session_message_chunk"}
)


class Caps(acp.schema.ClientCapabilities):
    subagents: dict[str, Any] | None = None


class ShimConnection(acp.client.connection.ClientSideConnection):
    """A ClientSideConnection that hands UNSTABLE_UPDATES to client.unstable_update ahead
    of the library's router, and sends initialize typed with Caps so that subagents
    reaches the wire (0.12.1 drops both, P5, P7)."""

    def __init__(
        self,
        client: Printer,
        writer: asyncio.StreamWriter,
        reader: asyncio.StreamReader,
    ) -> None: ...

    async def initialize(
        self,
        protocol_version: int,
        client_capabilities: Caps | None = None,
        client_info: acp.schema.Implementation | None = None,
        **kwargs: Any,
    ) -> acp.schema.InitializeResponse: ...
```

**`Printer` records; it never prints by itself.** ACP Python runs each incoming notification in a
task of its own (P1), and those tasks carry the context of whatever created the connection's
receive loop: under ipykernel 7.3 a print from them lands in no cell, or in the cell that built
the connection (verified by the Docwright with nbclient 0.11). So `show()` prints, from the
calling cell, the lines recorded since its previous call. Each callback records before its first
`await`, so `updates` and `lines` are in arrival order.

```python
@dataclass
class Subagent:
    session_id: str  # "<run>-n<node>": what session/cancel takes
    short: str  # "n<node>"
    parent_session_id: str  # the session it was announced on
    title: str  # the latest non-empty title
    state: Literal["running", "idle"]
    stop_reason: str | None  # the latest idle update's stopReason
    field_meta: dict[str, Any]  # the latest subagent_update's _meta, as sent


class SubagentMap(Mapping[str, Subagent]):
    """Keyed by full session id. A short id ("n2") is also accepted when exactly one
    recorded sub-agent has it; when several do (one per run), KeyError names them."""


class Printer:
    """An acp Client that records every update on one connection."""

    updates: list[tuple[str, dict[str, Any]]]  # (sessionId, the update as JSON)
    lines: list[str]  # one per update, in the format below
    subagents: SubagentMap
    commands: dict[str, list[acp.schema.AvailableCommand]]  # root session id -> latest

    async def session_update(self, session_id: str, update: Any, **kwargs: Any) -> None:
        """Stable updates, as the library's models."""

    async def unstable_update(self, session_id: str, update: dict[str, Any]) -> None:
        """subagent_update, session_message, session_message_chunk, raw (ShimConnection)."""

    def show(self) -> None:
        """Print the lines recorded since the previous show(); all of them the first time."""

    async def wait_until(
        self, predicate: Callable[[Printer], T | None], *, timeout: float = 120.0
    ) -> T:
        """Return predicate(self)'s first result that is neither None nor False, checked
        now and after every recorded update. TimeoutError after timeout seconds."""
```

- **`updates`** holds wire-shaped dicts: a stable update is the library's model dumped with
  `model_dump(mode="json", by_alias=True, exclude_none=True)`, so it has `sessionUpdate`, `_meta`
  and the other wire names (verified on 0.12.1: `cost` and `_meta` survive); an unstable one is the
  raw dict `ShimConnection` received.
- **`subagents`** gains an entry at a child's first `subagent_update` and updates it at each later
  one; `field_meta` is replaced, not merged, so after an idle update it holds that update's `_meta`
  (with `status`). `printer.subagents["n2"].session_id` is the id to cancel with.
- **`commands`** holds, per root session, the `availableCommands` of its latest
  `available_commands_update`; a session that has sent none is absent.
- **`wait_until`** is how a cell waits for something that arrives as an update rather than with a
  response: the menu after `session/new` (§5.4 rule 5),
  `await printer.wait_until(lambda p: p.commands.get(s.session_id))`; a sub-agent at depth 3, `await
  printer.wait_until(lambda p: next((a for a in p.subagents.values() if
  a.field_meta["deep_reasoner"]["depth"] == 3), None))`. Results that are `None` or `False` mean
  "not yet", so an empty command list counts as arrived.
- **Scope.** A `Printer` records one connection: every root session on it and every run of each.
  `subagents`, `commands` and `tree()` stay exact across both, because they are keyed by full id or
  split by session and run. Only `lines` cannot tell two root sessions apart (both are `root`), so
  read lines with one conversation per connection, which is also how OpenHands runs `dr-acp`
  (§1). Within one conversation a fresh run's lines reuse `n2` and `c1.1`, after its fresh-run
  notice.

**A line** is `f"{who:<9}{kind:<17}  {body}"`: `who` is `ids.short(sessionId)`, `kind` is
`sessionUpdate` without a trailing `_chunk`, so the body starts at column 28 unless the kind is
longer than 17 characters. A *field* in the bodies below is shown on one line (a tool call's output
as its last non-empty line, any other text with each run of whitespace turned into one space) and
cut to 60 characters, the 60th being `…`. Only agent and user messages are shown whole.

| `sessionUpdate` | body | example line |
|---|---|---|
| `agent_message_chunk`, `user_message_chunk` | the whole text; each of its lines wrapped at 72 characters, continuation lines indented to column 28; trailing blank lines dropped | `root     agent_message      Starting a fresh run: the previous one was stopped, so its variables and`, then `                            sub-agents are gone.` |
| `agent_thought_chunk` | the text, as a field | `n2       agent_thought      First I identify the CS courses, then I'll ask a separate s…` |
| `tool_call` | `{short(toolCallId)} {kind:<7}  {title}` | `root     tool_call          c1.1 execute  Run depts = sorted({c['dept'] for c in catalog.values()}) …`, a flat card: `root     tool_call          a2.1 other    #1 › #2 · Summarize the workload of the CS department for a…` |
| `tool_call_update` | `{short(toolCallId)} {status}  {output}`, output being the first text content as a field, omitted when there is none | `n2       tool_call_update   c2.1 completed  ['CS101', 'CS102']`, a failed cell or card: `root     tool_call_update   a4.1 failed  Not finished: the run was stopped` |
| `subagent_update`, running | `{short(sessionId)}  '{title}'  running` | `root     subagent_update    n2  'Summarize the workload of the CS department for a first-yea…'  running` |
| `subagent_update`, idle | `{short(sessionId)}  idle[ {stopReason}][  ({outcome})]`, the outcome phrase (below) unless it is `done` or `exhausted` | `n2       subagent_update    n4  idle cancelled  (stopped by #2)`; `root     subagent_update    n2  idle end_turn  (failed: ValueError: boom)`; `root     subagent_update    n3  idle  (crashed)` |
| `session_message` | `→ {short(recipientSessionId)}  '{text}'` | `root     session_message    → n2  'Summarize the workload of CS101 for a first-year student.'`; a child's answer: `n4       session_message    → n2  'CS101: 4 credits, about 10 hours a week, no prerequisites.'`; a failure: `n4       session_message    → n2  'Failed: ValueError: boom'` |
| `usage_update` | `{amount:.4f} {currency}`, or `cost unknown` when `cost` is absent | `n2       usage_update       0.0037 USD`; `root     usage_update       cost unknown` |
| `available_commands_update` | the command names as a Python list | `root     available_commands_update  ['compare-departments']` |
| `config_option_update` | `{id} = {currentValue}` per option, joined by `, `, with ` (fixed)` after an option that offers only its current value | `root     config_option_update  namespace = advising (fixed)` |
| any other | empty | |

**Outcome phrases**, shared by idle lines and the tree, from `_meta.deep_reasoner` of a child's
idle update or closed flat card:

| `status` | and | phrase |
|---|---|---|
| `done`, `exhausted` | — | `done`, `exhausted` |
| `failed` | — | `failed: {detail}`, detail cut to 40 characters |
| `stopped` | `stopped_by` absent or the node itself | `stopped` |
| `stopped` | `collateral` true | `stopped with #{stopped_by}` |
| `stopped` | otherwise | `stopped by #{stopped_by}` |
| `crashed` | — | `crashed` |
| (no idle update or closed card yet) | — | `running` |

#### `testing.tree`: the tree rebuilt from the updates alone

```python
@dataclass
class CellNode:
    tool_call_id: str
    short: str  # "c2.1"
    title: str
    status: str  # the latest: "in_progress", "completed" or "failed"
    output: str  # the latest content text; "" before any
    agents: list[AgentNode]  # the drives this cell started, in announcement order


@dataclass
class MessageNode:
    outcome: str  # the closing message's _meta.deep_reasoner.outcome
    prompt: int | None
    text: str


@dataclass
class AgentNode:
    session_id: str  # the child's session; the root session for the root
    short: str  # "n2"; "root" for the root
    node: int | None  # _meta.deep_reasoner.node
    drive: int
    title: str  # the announcement's title; "" for the root
    outcome: str | None  # the outcome phrase; None for the root
    cost_usd: float | None  # the session's cost when this drive ended; None if unknown
    items: list[CellNode | MessageNode]  # in arrival order; messages on the root only


@dataclass
class RunNode:
    root_session_id: str
    run: str
    mode: Mode  # "flat" when this run's sub-agents came as cards
    root: AgentNode
    cost_usd: float | None  # the root's at the run's end: all runs so far


@dataclass
class Tree:
    runs: list[RunNode]  # in order of each run's first update

    def __str__(self) -> str: ...


def tree(updates: Iterable[tuple[str, Mapping[str, Any]]]) -> Tree: ...
```

**Rebuild.** `tree()` takes any mix of root sessions and runs (`printer.updates` as it is) and
needs no mode argument (v2: v1's `mode` is gone; each run's mode is read from its updates).
- A **root session** is a session id no `subagent_update` announced. Its updates are split by run:
  a cell or a closing message carries `_meta.deep_reasoner.run`; a fresh-run notice and a
  `usage_update` belong to the run whose updates surround them, by arrival order. Rejected-prompt
  messages (`run` null) and user messages belong to no run and are not drawn.
- **Native**: a child is drawn under the cell named by its announcement's
  `_meta.openhands.parentToolCallId`, once per drive (each `running` announcement); its cells are
  the `tool_call`s on its own session between that announcement and the next. Its outcome comes
  from the idle update that ends the drive; its cost from the last `usage_update` on its session
  before that idle update. This uses only ACP's own structure, which is what E1 tests.
- **Flat**: a child is a card (`tool_call` of kind `other`, id `<run>-n<node>-a<drive>`), drawn
  under its `parentToolCallId`; its cells are the root's `tool_call`s whose
  `_meta.deep_reasoner.node` is its node, between that card and the node's next card. Its outcome
  comes from the card's closing `tool_call_update`. Flat sends no child costs, so a flat child
  has none.
- The root's items are its own cells and its closing messages, in arrival order; a run with several
  prompts shows each prompt's closing message after that prompt's cells.

**Drawing** (`str(tree)`): one block per run, blocks separated by a blank line. Branches are drawn
with `├─ `, `└─ `, `│  ` and three spaces. Fields as for lines, but titles and message texts cut
to 60 characters and outputs to 40.

| node | line |
|---|---|
| run | `root {root_session_id} · run {run} · {cost}` |
| agent | `{short}[ (drive {d}, when d > 1)]  {title}  {outcome}[ · {cost}]` |
| cell | `{short}  {title}  {status}[ → {output}]` |
| closing message | `{outcome}  {text}` |

`{cost}` is `{usd:.4f} USD`. The run line shows `cost unknown` when `cost_usd` is None; an agent
whose `cost_usd` is None (flat, no `usage_update`, or one without `cost`) shows no cost. For the
live doc's first run:

```text
root s-7c1f9e0a2b4d6e8f · run 20261002-162835-3fa9c1 · 0.0089 USD
├─ c1.1  Run depts = sorted({c['dept'] for c in catalog.values()}) …  completed → {'CS': 'CS runs 10 to 12 hours a week: …
│  ├─ n2  Summarize the workload of the CS department for a first-yea…  done · 0.0037 USD
│  │  ├─ c2.1  Run print([cid for cid, c in catalog.items() if c['dept'] =…  completed → ['CS101', 'CS102']
│  │  ├─ c2.2  Run summaries = run_all({ …  completed → {'CS101': 'CS101: 4 credits, about 10 h…
│  │  │  ├─ n4  Summarize the workload of CS101 for a first-year student.  done · 0.0007 USD
│  │  │  │  ├─ c4.1  Run print(catalog['CS101'])  completed → {'title': 'Programming I', 'dept': 'CS'…
│  │  │  │  └─ c4.2  Run FinalAnswer('CS101: 4 credits, about 10 hours a week, n…  completed → FinalAnswer: 'CS101: 4 credits, about 1…
│  │  │  └─ n5  …
│  │  └─ c2.3  …
│  └─ n3  …
└─ answered  STAT is lighter: its courses take 6 to 8 hours a week, CS's 10 to 12.
```

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
records the stream with `testing.Printer` and prints it with `show()` and `tree()`, and stops one
branch; cents per run.

### 8.5 Repository wiring D1 adds

- `pyproject.toml`: `deep-reasoning`, `requires-python = ">=3.12,<3.13"` (deep_reasoner's range);
  dependencies `deep-reasoner @ git+https://github.com/DeanLight/deep_reasoner_beta@d7334ae6ea884617a377d9f1ce872530d898484c`,
  `agent-client-protocol>=0.12.1,<0.13` (locked at 0.12.1, the SDK fork's lock), `pydantic>=2.7`,
  `pyyaml`, and **`ipython`** (deep_reasoner imports `IPython.display` at module level in 12
  modules but declares it only through its dev group; verified: blocking `IPython` makes
  `import deep_reasoner.v2.cli` fail); script `dr-acp = "deep_reasoning.acp.cli:main"`; dev group
  `pytest`, `jsonschema`, `referencing`, `ruff` (the Code Guide's linter, `[tool.ruff]` at its
  defaults; CI runs `ruff check src tests` and `ruff format --check src tests`, leaving `docs/`
  alone, since ruff lints notebooks by default); `[tool.pytest.ini_options] testpaths =
  ["tests"]`; sdist excludes `docs/`. A test asserts the installed `agent-client-protocol` is the
  pinned 0.12.1.
- **A `docs` dependency group (v2): `ipykernel` and `nbclient`** (which brings `nbformat` and
  `jupyter_client`), so the live doc can be executed. It is an artifact notebook: run once with a
  real key at Live Doc Green and committed with its outputs, never re-run on push. The command, from
  the repo root:
  `OPENAI_API_KEY=… uv run --group docs jupyter execute --inplace docs/dr-acp.ipynb`.
  `jupyter execute` starts the kernel in the notebook's directory (nbclient's
  `resources={"metadata": {"path": …}}`, `cli.py:183, 211`), so the notebook's
  `configs/advising/main.yaml` resolves, and `uv run` puts the project's `dr-acp` and the
  ipykernel kernel of its environment on `PATH`. Top-level `await` works through ipykernel's
  autoawait. In CI, a `workflow_dispatch` workflow `live-doc.yml` runs the same command with an
  `OPENAI_API_KEY` repository secret (the spec's layer 5; Michael's to add, with the read token
  below) and uploads the executed notebook for the Docwright to commit.
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
| R14 | Interim: an exception raised by a processor at `agent.turn` ends that drive as `failed` with `detail` `f"{type(exc).__name__}: {exc}"`; cells catch `Exception` and show `traceback.format_exc()`, so the parent sees it; `run_all` is `gather` on a private loop, cancelling the siblings | `agent.py:158–174, 899–905`, `repls/backends.py:523–524`, `repl_coro.py:84–85`, `coro_base.py:73–92` | `worker/stop.py`, recorder |
| R17 | A missing model key raises `ValueError` from `build_client` inside `build_reasoner`, before any model call | `config.py:256–266`, `v2/cli.py:342` | runner (`build_failed`), §5.1 |
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
| P8 | Client side: a notification is handled in a task of its own created by the receive loop, so it carries the receive loop's context, and a call can return before the notifications sent after its response are handled; a JSON-RPC error is raised as `RequestError(code, message, data)` | `connection.py:140–163, 240–251` | `testing/client.py` (`show`, `wait_until`), §5.5 |
| P9 | `spawn_stdio_transport` passes only `DEFAULT_INHERITED_ENV_VARS` unless given `env=`; on exit it closes stdin, sends SIGTERM after `shutdown_timeout` (2.0 s) and SIGKILL 2.0 s later | `transports.py:13–45, 96–117` | §4.2 shutdown, §5.1, the live doc |

**The bridge (SDK fork, upstream behaviour S1 starts from):** it waits ≤ 2 s per turn for a root
`usage_update` (`acp_agent.py:3643–3654`); it restarts the agent when a cancelled prompt does not
answer within 2 s (`:169, 3472–3540`); any parsed update resets its 1,800 s prompt-idle watchdog
(`:1433–1439, 1758`); it drops stdout lines that are not JSON-RPC (`:1047–1076`); it calls
`session/load` with the prior id and falls back to `session/new` on a JSON-RPC error
(`:3200–3240`); it books cost as deltas of each session's cumulative amount (`:2065–2072`); it
starts one agent process per conversation with its own environment plus the conversation's secrets
(`:2912, 2926–2952`); it joins a turn's `agent_message_chunk` texts with no separator (`:3762`);
at shutdown it closes the connection, sends SIGTERM at once and kills after 5 s (`:4563–4590`).

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
6. **Which decompositions are programs (v2, for D2).** `dr-acp` offers every decomposition as a
   command (§4.6), including few-shot examples written for one input, which make poor openings.
   The Library can mark a decomposition as a program (or not) and D2's `Catalog.snapshot` then
   offers only programs; nothing in D1 changes. Raised by the Docwright; the Conductor decides
   whether it goes into D2's design or back to the spec.
7. **An `OPENAI_API_KEY` secret for `live-doc.yml`** (§8.5): Michael's to add.
