# What deep-reasoning needs from deep_reasoner

A living record of everything this app uses from Dean's `deep_reasoner_beta` and how we expect
it to behave. It is written so that Dean, or an agent working in his repo, can read it without
our context. What we ask of him is tracked elsewhere: see §3.

- **Owner:** Michael (deep-reasoning). **Counterpart:** Dean (deep_reasoner_beta).
- **Pinned against:** `DeanLight/deep_reasoner_beta` at `d7334ae` (main, 2026-09-28). Every
  path and line number below is at that commit.
- **Rule:** we do not change deep_reasoner_beta. If something cannot be done from outside, it
  becomes an ask (§3). A branch or PR on Dean's repo happens only if he agrees.

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
EXP-6 asks for an explicit id to replace this inference.

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
| a sub-agent | its own ACP child session, announced with `subagent_update` (ACP's unstable Subagent Sessions draft). The REPL cell that spawned it travels as `_meta.openhands.parentToolCallId`; deep_reasoner's own node data travels as `_meta.deep_reasoner`, which no fork reads. A client that does not advertise `subagents` gets a labelled flat stream instead |
| `FinalAnswer` / exhaustion | the final message, then `stopReason` |
| decompositions | slash commands |
| namespaces | a session config option |

OpenHands' ACP bridge and its Canvas UI do not render child sessions today. Changing them is our
work, not Dean's. It lives in our two OpenHands forks (`michaeltheologitis/software-agent-sdk`
and `michaeltheologitis/OpenHands`), as generic, upstream-shaped features. ACP itself is not
forked: sub-agent sessions are in its upstream (unstable) schema.

## 2. What we expect to stay stable

We depend on everything in §1, especially:
- the event names and fields in §1.4;
- `build_reasoner`, `close_run` and the config shapes in §1.2;
- the `factory_from` contract in §1.3.

None of these is a documented public interface today; the events are debug-level internals.
EXP-2 asks for that.

## 3. What we ask of Dean

Our asks, our questions for him and the bugs we found reading his code are rows in the
**Expectations** table in Michael's Notion,
<https://app.notion.com/p/1fb9c801a17046e6888c1ed2b00e2797> (ask Michael for access). Each row
has its status (`Open`, `Asked`, `Done`, `Dropped`), why we need it, and Dean's answer once it
comes. From a session in this repo, `ase-skills expectations list --task 1` prints them.

They moved there from this file on 2026-10-02. Older references map like this:
- asks A1–A7 are EXP-1 to EXP-7;
- the meeting questions are EXP-8 to EXP-13, except three folded into rows above: stability
  into EXP-2, distribution into EXP-1, and the roadmap question into EXP-3 to EXP-6;
- bugs B1–B8 are EXP-14 to EXP-21.
