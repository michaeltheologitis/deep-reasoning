# What deep-reasoning needs from deep_reasoner

A living record of everything this app uses from Dean's `deep_reasoner_beta`, how we expect it
to behave, and what we are asking him for. It is written so that Dean, or an agent working in
his repo, can read it without our context.

- **Owner:** Michael (deep-reasoning). **Counterpart:** Dean (deep_reasoner_beta).
- **Pinned against:** `DeanLight/deep_reasoner_beta` at `d7334ae` (main, 2026-09-28). Every
  path and line number below is at that commit.
- **Rule:** we do not change deep_reasoner_beta. If something cannot be done from outside, it
  becomes an ask in §3. A branch or PR on Dean's repo happens only if he agrees.
- **Status of the asks:** none has been raised as a GitHub issue yet (Michael's call,
  2026-10-02). When one is raised, put its link next to it.

## 1. What we use, surface by surface

### 1.1 Building and running an agent

We build a run the way the `dr` CLI does, in-process:

| Call | Where | What we rely on |
|---|---|---|
| `V2Config` (a `MainConfig`) | `deep_reasoner/v2/cli.py:80`, `deep_reasoner/config.py:355` | Built from our stored YAML, or with `load_cli_config`. The fields we write are in §1.2 |
| `build_reasoner(cfg, *, run_dir, extra_vars=(), main_decomposition=None)` | `deep_reasoner/v2/cli.py:308` | Returns `(reasoner, alias)`, and is the same path for the chat and Claude backbones. We keep `alias` entered for the whole run |
| `bound_contextvars(task_id=..., log_dir=...)` | structlog | We bind these around a run, as `run_task` does |
| `reasoner.send(user(task))`, then `await anext(reasoner)` | `deep_reasoner/v2/agent.py` | Runs to `FinalAnswer`. A `send` after a finished run resumes the same conversation, in memory |
| `reasoner.final_answer`, `reasoner.exhausted` | `deep_reasoner/v2/agent.py` | `exhausted` is the only way to tell an exhausted run from an answer |
| `close_run(reasoner)` | `deep_reasoner/v2/cli.py:439` | Persists tools, closes the REPL (including remote sandboxes), and releases shared sandboxes |

### 1.2 Configuration we store and generate

Users' namespaces and decompositions are stored in our SQLite database as **canonical YAML in
deep_reasoner's own shapes**, so a stored config is also a valid `dr` config. These are the
shapes we depend on:

- **`NamespaceConfig`** (`deep_reasoner/namespaces.py:63`, `extra="forbid"`): `name`, `repl`,
  `reasoner`, `decompositions`, `tools`, `vars`, `spawn`, `system_suffix`. Dotted names inherit
  from their parents. `repl`, `reasoner` and `spawn` are nearest-wins; `tools`, `vars`,
  decompositions and suffixes accumulate (`resolve`, `deep_reasoner/namespaces.py:272`).
- **`Decomposition`** (`deep_reasoner/prompt_config.py:25`, `extra="forbid"`): `name`, and
  `messages`, a non-empty list of `{role: system|user|assistant, content}`.
- **`MainConfig` / `V2Config` top level**:
  - model selection: `model`, `models`, `llm_kwargs`, `client`;
  - prompting and limits: `system_prompt`, `max_iter`, `max_depth`, `reasoner`;
  - namespaces and decompositions: `decompositions`, `namespaces`, `entry_namespace`;
  - tools and execution: `tools`, `repl`.

### 1.3 Custom tools

A user-written tool is a Python file plus a factory name. We rely on the existing `factory_from`
hook (`load_tool_factory`, `deep_reasoner/tools/base.py:329`; consumed in `make_tools`,
`deep_reasoner/v2/cli.py:125`):

- `tools: {<name>: {factory_from: <file.py>, factory: <fn>, ...params}}`, with the file
  relative to the config file;
- `fn(client, params) -> Func(value, description=...)`, where `params` is the block minus
  `factory` and `factory_from`;
- a namespace grants it with `tools: [<name>]`.

### 1.4 Events: how the app sees a run

The UI's live sub-agent tree and step view are built entirely from deep_reasoner's structlog
events. We install our own processor with `configure_structlog_fixture(extra_processors=[...])`
(`deep_reasoner/core.py:131`), the same way `ProgressView` and `LogProcessor` are installed.
Extra processors run before the level filter, so debug events reach us.

| Event | Emitted at | Fields we read |
|---|---|---|
| `agent.start` | `deep_reasoner/v2/agent.py:877` | `task`, `max_iter`, `backbone`, `namespace`, `run`, and the bound node fields (below) |
| `agent.turn` | `deep_reasoner/v2/agent.py:882` | `iter`, `max_iter` |
| `agent.end` | `deep_reasoner/v2/agent.py:897`, `:903`, `:911` | `status` (`done` / `failed` / `exhausted`), `iter`, `detail` (on failure) |
| `llm.call` | `deep_reasoner/v2/llm_coro.py:110` | `model`, `messages`, `response` (the think + `<repl>` text), `usage`, `duration_s` |
| `agent.loop` | `deep_reasoner/v2/llm_coro.py:240` | `messages` (the full history after each reply) |
| `repl.execute` | `deep_reasoner/v2/repl_coro.py:328` | `source`, `observation` |
| `claude.call` | `deep_reasoner/v2/claude_code.py:843` | `session_id`, `cost_usd`, `usage`, `num_turns`, `reason`, `response`, `ok`, `transcript`, `workdir` |

**Bound node fields** on every event: `task_id` and `log_dir` (bound by us), and `node_id`,
`node_name`, `depth`, `ancestry`, `kind`, `agent_depth` (from the node tree,
`deep_reasoner/v2/context.py:79`). The agent's own LLM and REPL fold into the agent's node, so
an `llm.call` or `repl.execute` belongs to the agent whose `node_id` it carries. **`ancestry` is
how we draw the tree.** We never infer parentage from timing.

**What we infer, and how:** which REPL cell spawned a child agent. A parent is blocked inside
one cell while its children run, so a child's `agent.start` belongs to the parent's latest
`agent.turn`. The cell's code is known before it runs, from that turn's `llm.call` `response`.
Ask A6 would replace this inference with an explicit id.

**Known gaps we work around:**
- `llm.call` and its usage accounting sit inside a disk-cached function, so a cache hit logs
  nothing. The cache is off by default.
- `repl.execute` is logged only after the cell finishes.
- Cost covers only Claude spend.

### 1.5 How we expose deep_reasoner to OpenHands (ACP)

Our ACP agent lives in this repo, not in deep_reasoner. It runs one deep_reasoner run per ACP
session and translates the events in §1.4:

| deep_reasoner | ACP |
|---|---|
| think text | `agent_thought_chunk` |
| a REPL cell | `tool_call` (kind `execute`), then `tool_call_update` |
| a sub-agent | its own ACP child session, announced with `subagent_update` (ACP's unstable Subagent Sessions draft) |
| `FinalAnswer` / exhaustion | the final message, then `stopReason` |
| decompositions | slash commands |
| namespaces | a session config option |

OpenHands' ACP bridge and its Canvas UI do not render child sessions today; changing them is
our work, in OpenHands, not Dean's.

## 2. What we expect to stay stable

We depend on everything in §1, especially:
- the event names and fields in §1.4;
- `build_reasoner`, `close_run` and the config shapes in §1.2;
- the `factory_from` contract in §1.3.

None of these is a documented public interface today; the events are debug-level internals.
See ask A2.

## 3. Asks

| # | Ask | Why we need it | Blocking? | Status |
|---|---|---|---|---|
| A1 | **Access and distribution.** How will self-hosters install deep_reasoner? The repo is private. Is a public release or PyPI planned, and under what license? | Anyone installing our app needs deep_reasoner | Blocks other people self-hosting; not our own development | Open (asked in the 2026-10-02 meeting) |
| A2 | **Stability of §1**, or a heads-up before changing it. Ideally the §1.4 events become a documented interface, perhaps with a test in deep_reasoner | The tree view and the stored configs break silently otherwise | No; we pin a commit | Open |
| A3 | **Cancellation** of a running agent, including mid-cell, and ideally per sub-agent | Our Stop button kills the worker process instead, which loses the REPL state | No (workaround) | Open |
| A4 | **Resume a conversation after a restart**, rebuilding an agent from stored history | Today resume is in-memory only, so a restarted app shows old conversations read-only | No (workaround) | Open |
| A5 | **Streaming** of model output (tokens) | Progress is shown per step, not as typing | No | Open |
| A6 | **A `repl.start` event with a cell id**, and that id on child agents' `agent.start` | Replaces the inference in §1.4 | No (inferred today) | Open |
| A7 | **Chat-backbone cost**, for example recording OpenRouter's `usage.cost` | Only Claude spend is counted | No (we compute it from `usage`) | Open |

### Bugs we found while reading (FYI, for Dean)

| # | Where | What |
|---|---|---|
| B1 | `deep_reasoner/v2/messages.py:185` | A tool that is an object, such as the `llm` tool, is described to the model as `fn(...)`, not by its binding name. It is visible in the committed `docs/running-agents.ipynb` output |
| B2 | `deep_reasoner/tools/rag.py:296` | Every new `RagStore` deletes all collections in chromadb's shared in-memory backend. A second store, such as `kg` search, likely wipes `rag`'s corpus. Not confirmed at runtime |
| B3 | `docs/configs/catalog/kg_agent.yaml:128` | `kg.enable_link_propagation("canonical")` passes `mode` positionally, but it is keyword-only (`deep_reasoner/tools/kg_main.py:877`), so it raises `TypeError` |
| B4 | `docs/configs/catalog/crossover.yaml:61` | `worker` sets no `spawn:`, so it is unrestricted and can spawn into `admin` |
| B5 | `docs/index.py:137`, `docs/observability.py:24`, `docs/reference.py:215`, `docs/running-agents.py:62`, `docs/knowledge-graph.py:220` | These pages say logs are "one YAML per turn"; it is one per node |
| B6 | `deep_reasoner/v2/agent.py:306`, `deep_reasoner/v2/claude_reasoner.py:460`, `configs/example/claude.yaml:39` | These name a `--decomposition` flag; the flag is `--main-decomposition` |
| B7 | `deep_reasoner/v2/repl_coro.py:313` | There is no execution timeout for in-process snippets, so a `while True` under `local` or `restricted` hangs the run |
| B8 | `deep_reasoner/v2/cli.py:157` | `factory_from` builders do not receive `config_path`, though `deep_reasoner/tools/base.py:279` says every builder does |

## 4. Questions for Dean, and his answers

Raised in the 2026-10-02 meeting. Answers are recorded here as they come.

| Question | Answer |
|---|---|
| Did "use ACP" mean deep_reasoner as an ACP agent inside OpenHands? Is the plug fine living in our repo? | pending |
| A real tree via ACP's draft sub-agent sessions plus an OpenHands change, aimed upstream. Any objection, or OpenHands contacts? | pending |
| Will §1 stay stable, or would he rather give us a proper event stream? (A2) | pending |
| Distribution and license (A1) | pending |
| Is any of A3–A6 already on his roadmap? | pending |
| Where should asks go: GitHub issues on his repo, or his Notion? | pending |
| Is the decomposition or namespace format about to change? | pending |
| Is `factory_from` the right contract for user tools? | pending |
| Default backbone and provider for the app (chat model or Claude Code)? | pending |
