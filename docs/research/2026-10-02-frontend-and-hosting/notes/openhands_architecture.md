# OpenHands architecture and extensibility for a foreign (non-CodeAct) agent — state as of 2026-10-01

Method note: most findings come from reading source at the HEAD of `main` on 2026-10-01: OpenHands/OpenHands @ `a8c05584` (2026-10-01), OpenHands/software-agent-sdk @ `53a4bc50` (2026-10-01), OpenHands/OpenHands-CLI @ `954f2ba6` (2026-08-11), OpenHands/docs (HEAD 2026-10-01), agentclientprotocol/agent-client-protocol (HEAD 2026-10-01). Release dates come from git tag dates. The egress proxy blocked `www.openhands.dev`, `agentclientprotocol.com` and the GitHub REST API (`gh api`). So docs are cited by their GitHub source files; the matching docs.openhands.dev page is the same path without `.mdx`. Line numbers are approximate and refer to those commits.

## 1. Current OpenHands architecture (2026): repos, V0 vs V1, event model, and how the GUI talks to the backend

### Takeaway
OpenHands changed shape twice. It began as the V0 Python monorepo, which was removed in April 2026. Next came the "V1" app server plus agent-server, which ran from Dec 2025 to Jul 2026. Since 2026-07-27 it is "Agent Canvas". The flagship repo `OpenHands/OpenHands` now holds only a React/TypeScript frontend and a launcher. All agent execution, the event model and the canonical REST/WebSocket API live in the Python `software-agent-sdk` ("V1": `openhands-sdk`, `openhands-tools`, `openhands-workspace`, `openhands-agent-server`). The frontend talks to the agent-server through `@openhands/typescript-client`.

### Cited Findings
**Repo map today**
- `OpenHands/OpenHands` README title is now "Agent Canvas — The self-hosted developer control center for coding agents and automations. Run OpenHands, Claude Code, Codex, Gemini, or any ACP-compatible agent across local, remote, and cloud backends." It carries a "status-beta" badge and is published as npm `@openhands/agent-canvas` (v1.24.0) and as Docker `ghcr.io/openhands/agent-canvas:1.24.0` — [OpenHands README](https://github.com/OpenHands/OpenHands/blob/main/README.md), [package.json](https://github.com/OpenHands/OpenHands/blob/main/package.json)
- The README's "Repository boundaries" table:
  - `OpenHands/OpenHands` = "Agent Canvas frontend, user-facing control center, backend selection, and local-stack orchestration".
  - `OpenHands/software-agent-sdk` = "Python SDK, Agent Server, agents, tools, conversations, workspaces, events, and the canonical server API".
  - `OpenHands/typescript-client` = "Browser-compatible TypeScript client for the Agent Server API".
  - `OpenHands/automation` = scheduling, webhooks and dispatching.
  - Source: [OpenHands README §Architecture](https://github.com/OpenHands/OpenHands/blob/main/README.md)
- The docs also list `OpenHands/sandbox-server` ("Standalone API and sandbox control plane", community-driven), `OpenHands/docs` and `OpenHands/benchmarks`. They state "Each public repository includes its own license" — [docs overview/introduction.mdx](https://github.com/OpenHands/docs/blob/main/overview/introduction.mdx), [agent-canvas/architecture.mdx](https://github.com/OpenHands/docs/blob/main/openhands/usage/agent-canvas/architecture.mdx)
- Canvas "is not responsible for: Executing agent actions directly; Providing the sandbox or workspace isolation layer…". It is "adapted from the OpenHands frontend to talk directly to the OpenHands Agent Server" — [docs/architecture.md](https://github.com/OpenHands/OpenHands/blob/main/docs/architecture.md)
- Canvas can connect to several agent-servers (local, Docker, VM, Kubernetes, Modal, OpenHands Cloud/Enterprise) and switch between them from the UI. "Agent Server stores conversation history, agent and LLM profiles, secrets, MCP configuration"; Canvas only stores connection information — [agent-canvas/architecture.mdx](https://github.com/OpenHands/docs/blob/main/openhands/usage/agent-canvas/architecture.mdx)
- Frontend stack: React 19.3, react-router 7.18, TanStack Query, Zustand stores, HeroUI, Monaco, xterm, `@openhands/typescript-client` 1.50.1 and `@openhands/extensions` 0.24.0 — [package.json](https://github.com/OpenHands/OpenHands/blob/main/package.json), [docs/architecture.md](https://github.com/OpenHands/OpenHands/blob/main/docs/architecture.md)
- SDK packages `openhands-sdk`, `openhands-tools`, `openhands-workspace` and `openhands-agent-server` are all at version 1.50.1. The SDK has a tech report at arXiv 2511.03690 — [software-agent-sdk pyproject files](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-sdk/pyproject.toml), [SDK README](https://github.com/OpenHands/software-agent-sdk/blob/main/README.md)

**Transition timeline**
- Agent Canvas Initiative issue, opened 2026-05-11 by rbren: "Starting June 1, Agent Canvas moves into the flagship OpenHands/OpenHands repository… The existing code in OpenHands/OpenHands will be moved into a separate repo". It also says the enterprise directory is being eliminated, that "Bring your own agent" will come via ACP, and that the CLI moves to "sandbox" status — [OpenHands#14374](https://github.com/OpenHands/OpenHands/issues/14374)
- Transition FAQ dated 2026-06-03: the Local GUI (Docker or `openhands serve`) "will continue to work" in maintenance mode. The CLI TUI enters maintenance mode, while "Headless and ACP modes" get "full support indefinitely" — [OpenHands/docs#657](https://github.com/OpenHands/docs/issues/657). **Contradicted later**: on 2026-08-11 the CLI README was changed to say "This project is no longer actively maintained" and recommends Agent Canvas — [OpenHands-CLI README, PR #808](https://github.com/OpenHands/OpenHands-CLI/blob/main/README.md)
- Git history shows the switch itself:
  - 2026-07-27: commit `cb9138ca` "chore: clear repository for Agent Canvas migration (#15397)".
  - Same day: merge of PR #15413 "chore: replay Agent Canvas history".
  - The standalone `OpenHands/agent-canvas` repo was archived on 2026-07-27 (per search-result snippet).
  - Sources: [OpenHands PR #15397](https://github.com/OpenHands/OpenHands/pull/15397), [PR #15413](https://github.com/OpenHands/OpenHands/pull/15413), [OpenHands/agent-canvas](https://github.com/OpenHands/agent-canvas)
- The old backend now lives in the archived `OpenHands/legacy` snapshot. The docs describe it as preserving "the previous backend and runtime architecture for historical reference"; the "Legacy Local GUI" is "deprecated" — [docs overview/introduction.mdx](https://github.com/OpenHands/docs/blob/main/overview/introduction.mdx), [OpenHands/legacy](https://github.com/OpenHands/legacy)

**V0 vs V1 (V0 is DEPRECATED and REMOVED)**
- At tag `0.62.0` (2025-11-11) the repo's `openhands/` package still held the V0 stack: `agenthub` (CodeActAgent and others), `controller`, `runtime`, `events`, `memory`, `microagent`, `security`, `resolver`, `llm`, `mcp`, `server`, `storage`, plus a new `app_server`. At tag `1.11.0` (2026-07-09) only `app_server`, `server`, `db` and `analytics` remained, alongside `enterprise/` and `frontend/` — git tree listing of [OpenHands tags 0.62.0 / 1.11.0](https://github.com/OpenHands/OpenHands/tree/1.11.0)
- V0 removal PRs (dates are merge-commit dates):
  - Deprecation notice: "Mark V0 legacy files" #12165 (2025-12-30); "legacy v0 deprecation notice with version and removal date" #12455 (2026-01-15); "Deprecate V0 endpoints now handled by agent server" #12710 (2026-02-02).
  - Removal: "Remove deprecated V0 FastAPI endpoints" #13952 (2026-04-19); "stop publishing v0 runtime image" #14005 (2026-04-21); "Removed V0 sessions" #14061 (2026-04-22); "Removed the V0 resolver" #14062 (2026-04-23); V0 microagent and memory packages removed #14053/#14057 (2026-04-24).
  - Sources: [#13952](https://github.com/OpenHands/OpenHands/pull/13952), [#14005](https://github.com/OpenHands/OpenHands/pull/14005), [#14053](https://github.com/OpenHands/OpenHands/pull/14053), [#12455](https://github.com/OpenHands/OpenHands/pull/12455)
- The legacy V1-era frontend (tag 1.11.0) still depended on `socket.io-client` 4.8.3, which V0 conversations used. Canvas instead uses the agent-server's native WebSocket — [legacy frontend/package.json @1.11.0](https://github.com/OpenHands/OpenHands/blob/1.11.0/frontend/package.json), [conversation-websocket-context.tsx](https://github.com/OpenHands/OpenHands/blob/main/src/contexts/conversation-websocket-context.tsx)

**V1 SDK event / action / observation model**
- Events are pydantic models with a `kind` discriminator (`DiscriminatedUnionMixin`). `LLMConvertibleEvent` subclasses — `MessageEvent`, `ActionEvent` (tool call plus thought/reasoning/security risk) and `ObservationEvent` (tool result) — are converted into LLM messages. Parallel tool calls are grouped by `llm_response_id`. There are also "internal" events (condensation, state updates, pause, errors) — [docs sdk/arch/events.mdx](https://github.com/OpenHands/docs/blob/main/sdk/arch/events.mdx), [sdk/event/](https://github.com/OpenHands/software-agent-sdk/tree/main/openhands-sdk/openhands/sdk/event)
- The event set in `openhands.sdk.event` includes:
  - `acp_tool_call` (ACPToolCallEvent), `condenser`, `conversation_error`, `conversation_state`, `hook_execution`, `streaming_delta`, `token`, `user_action`, `resume_transcript`.
  - `llm_convertible/{action,message,observation,system}`.
  - Source: [sdk/event/](https://github.com/OpenHands/software-agent-sdk/tree/main/openhands-sdk/openhands/sdk/event)

**GUI ↔ backend API**
- Agent-server REST (FastAPI with OpenAPI at `/docs`):
  - `POST /conversations`, `GET /conversations/search`, `GET|POST /conversations/{id}/events`, plus WebSocket `/conversations/{id}/events/socket` (README).
  - Many more routers: settings, secrets, profiles, skills, plugins, MCP, hooks, bash, files, git, sub-agents, canvas-extensions, app-backends bridge, an OpenAI-compatible `/v1/models` + completions gateway, and server_info/health.
  - Sources: [agent-server README](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-agent-server/openhands/agent_server/README.md), [agent_server/ (routers)](https://github.com/OpenHands/software-agent-sdk/tree/main/openhands-agent-server/openhands/agent_server)
- Canvas now uses a newer session socket, `/sockets/session/{conversation_id}`. Its wire protocol is an envelope of `Durable` / `Delta` / `ItemStarted` / `ItemAborted` frames with `after_seq` reconnect replay, and the module is marked "PROVISIONAL". Canvas requires agent-server ≥ 1.47.0 for this socket — [session_protocol.py](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-agent-server/openhands/agent_server/session_protocol.py), [docs/ACP_AGENTS.md](https://github.com/OpenHands/OpenHands/blob/main/docs/ACP_AGENTS.md)
- The agent-server README tells client authors to "treat discriminator values such as `kind` as open-ended: skip or ignore unknown variants" — [agent-server README §Event schema compatibility](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-agent-server/openhands/agent_server/README.md)
- Conversations have `parent_conversation_id` and `sub_conversation_ids` fields ("Name mirrors the Cloud API field"). The frontend uses them for planner sub-conversations — [agent_server/models.py ~L264](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-agent-server/openhands/agent_server/models.py), [use-handle-plan-click.ts](https://github.com/OpenHands/OpenHands/blob/main/src/hooks/use-handle-plan-click.ts)

### Inferences
- "OpenHands V1" today effectively means the software-agent-sdk plus agent-server. The "OpenHands GUI" means Agent Canvas, a separate client of that API. Anything targeting the 2025-era V0 `agenthub`/`runtime`/`Agent` registry is obsolete.
- The agent-server, not the frontend, is the integration surface to target. The frontend already supports switching between several backends.

### Gaps
- I could not read the archived `OpenHands/legacy` repo contents directly; I relied on tags in the main repo's history. The exact archive date of `legacy` was not confirmed.
- The `www.openhands.dev` blog and docs site could not be fetched (proxy). Docs were read from the `OpenHands/docs` GitHub source.

## 2. Defining agents and tools in the V1 SDK; custom agent loops; extension points; official "plugin" mechanisms

### Takeaway
A fully custom loop is possible at the SDK level: subclass `AgentBase` and implement `step()`. `ACPAgent` itself is a non-LLM-loop agent that runs a whole external turn inside one `step()`. The agent-server will deserialize any *imported* `AgentBase` subclass by its `kind`, and `--import-modules`/`OH_EXTRA_PYTHON_PATH` let you preload one. However, the official, documented extension points are tools, MCP, skills, hooks, Claude-Code-compatible plugins, sub-agent definitions and Canvas "Apps". Agent Canvas can only *launch* two agent kinds, `openhands` (LLM tool-calling `Agent`) and `acp` (`ACPAgent`). There is no plugin mechanism for registering a new agent class into the GUI.

### Cited Findings
- `AgentBase(DiscriminatedUnionMixin, ABC)` is a frozen pydantic model ("Agents are stateless and should be fully defined by their configuration") with required `llm: LLM` and `tools: list[Tool]` fields. Its one abstract method is `step(conversation, on_event, on_token=None)`. The documented contract is to "make a LLM call, execute the tool, update state…; if finished set state.execution_status to FINISHED". `astep()` defaults to running `step()` in a thread. Other hooks: `init_state()`, `verify()` (on resume, "Agent class/type must match"), `ask_agent()`, `close()` — [sdk/agent/base.py L101–700, L1049–1065](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-sdk/openhands/sdk/agent/base.py)
- Only two concrete agents exist in the SDK: `Agent(CriticMixin, ResponseDispatchMixin, AgentBase)` (the LLM tool-calling/CodeAct-successor loop, ~1,600 LOC) and `ACPAgent(AgentBase)` (~4,700 LOC). `ACPAgent` is lazily imported because "eagerly importing ACPAgent registers it in the DiscriminatedUnionMixin, which makes `kind` required" — [sdk/agent/__init__.py](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-sdk/openhands/sdk/agent/__init__.py), [agent.py L414](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-sdk/openhands/sdk/agent/agent.py), [acp_agent.py L1714](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-sdk/openhands/sdk/agent/acp_agent.py)
- Polymorphic resolution: `resolve_kind()` looks the class up among "all currently loaded non abstract subclasses". A subclass therefore has to be imported before it can be deserialized — [sdk/utils/models.py ~L352](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-sdk/openhands/sdk/utils/models.py)
- The agent-server start-conversation request field is typed `agent: AgentBase` (a polymorphic union) — [agent_server/models.py ~L350](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-agent-server/openhands/agent_server/models.py)
- The agent-server CLI has `--extra-python-path` / env `OH_EXTRA_PYTHON_PATH` ("so importlib.import_module can find external custom-tool modules — even when running from a PyInstaller binary"). It also has `--import-modules` ("Import user-specified modules so their top-level side effects run… to register custom tools before any conversation is created") — [agent_server/__main__.py L74–135, L240](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-agent-server/openhands/agent_server/__main__.py)
- Settings and the UI launch path only know `agent_kind: Literal["openhands", "acp"]`; `"llm"` is deprecated and canonicalized to `"openhands"` — [sdk/settings/api_models.py L103](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-sdk/openhands/sdk/settings/api_models.py), [sdk/settings/model.py L1237, L636–651](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-sdk/openhands/sdk/settings/model.py). Canvas branches on `agent_kind === "openhands"` when creating conversations — [use-create-conversation.ts](https://github.com/OpenHands/OpenHands/blob/main/src/hooks/mutation/use-create-conversation.ts)
- The official "Creating Custom Agent" guide is really about *configuring* agents (custom tool sets and prompts, e.g. a read-only planning agent built from `get_planning_agent()`), not about subclassing `AgentBase` — [docs sdk/guides/agent-custom.mdx](https://github.com/OpenHands/docs/blob/main/sdk/guides/agent-custom.mdx)
- Other documented extension points (SDK guides):
  - `custom-tools` and `agent-server/custom-tools`; `mcp`; `skill`; `hooks`; `plugins`.
  - `task-tool-set` and `agent-file-based`, both sub-agents.
  - `critic`, `security`, `convo-custom-visualizer`, `llm-routing`, `agent-settings`.
  - Source: [docs sdk/guides/](https://github.com/OpenHands/docs/tree/main/sdk/guides)
- **Plugins (official):** "Plugins bundle skills, hooks, MCP servers, agents, and commands into reusable packages"; "The plugin format is compatible with the Claude Code plugin structure" (`.plugin/plugin.json`, `skills/*/SKILL.md`, `hooks/hooks.json`, …). The agent-server has `/plugins` install/marketplace routes backed by `openhands.sdk.plugin` — [docs sdk/guides/plugins.mdx](https://github.com/OpenHands/docs/blob/main/sdk/guides/plugins.mdx), [plugins_service.py](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-agent-server/openhands/agent_server/plugins_service.py). Plugin "agents" are *agent definitions*, i.e. prompt/tool configs for sub-agents (`openhands.sdk.subagent`: `AgentDefinition`, `register_agent`, `register_plugin_agents`), not new loop classes — [sdk/subagent/__init__.py](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-sdk/openhands/sdk/subagent/__init__.py)
- **Canvas Apps / "Canvas Extensions" (beta), the official UI plugin mechanism:**
  - Manifest: `canvas-extension.json` with `contributes.pages`. The entrypoint is an ES module exporting `activate(host)`.
  - Host API v1: `registerPage(id, mount)`, `navigate()`, `agentServer.request({method, path, body})` (authenticated HTTP to the active agent-server), plus backend/extension metadata.
  - An app may declare a trusted backend subprocess (`linux-amd64`/`linux-arm64` `.tar.gz` artifact with sha256, `argv` using `{port}`/`{data_dir}`/`{artifact_dir}`, a health probe). It is bridged by the agent-server at `/app-backends/{extension_name}` (HTTP and WebSocket).
  - Sources: [canvas_extensions/manifest.py](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-agent-server/openhands/agent_server/canvas_extensions/manifest.py), [canvas_extensions/backend.py](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-agent-server/openhands/agent_server/canvas_extensions/backend.py), [src/types/canvas-extension.ts](https://github.com/OpenHands/OpenHands/blob/main/src/types/canvas-extension.ts), [demo extension](https://github.com/OpenHands/OpenHands/blob/main/src/fixtures/canvas-extensions/demo-page/extension.js)
- Docs on Apps (beta): "Apps let you add custom pages to Agent Canvas without changing the Agent Canvas source code… The current beta does not support conversation tabs, arbitrary interface slots, themes, visualizer replacement, or direct Agent Server WebSocket connections." Apps "are not available when an OpenHands Cloud backend is active"; "The name and app API may change" — [docs agent-canvas/canvas-extensions.mdx](https://github.com/OpenHands/docs/blob/main/openhands/usage/agent-canvas/canvas-extensions.mdx)

### Inferences
- A `DeepReasonerAgent(AgentBase)` running the whole think→REPL→FinalAnswer loop inside `step()` is technically feasible, following the `ACPAgent` pattern. It would emit `MessageEvent`s and `ACPToolCallEvent`s (or custom Action/Observation events) via `on_event`, plus tokens via `on_token`. It can be loaded into a stock agent-server with `OH_EXTRA_PYTHON_PATH` + `--import-modules`, and conversations could be created through the REST API with `agent.kind="DeepReasonerAgent"`. But Canvas's "new conversation" flow cannot select it without patching the frontend and the settings `agent_kind` literal. The agent would also be tightly coupled to a fast-moving SDK (see Q5), in-process with the server's Python and dependencies, and must satisfy a frozen-pydantic, `llm`-required schema.
- The "plugin" concept in OpenHands means Claude-Code-style capability bundles (skills/hooks/MCP/sub-agent configs). It does not mean swapping the agent runtime. Bring-your-own-agent is officially done through ACP.
- deep_reasoner's per-user decompositions/namespaces management UI maps naturally onto a Canvas App: a full page in the left rail, with an optional trusted backend that stores namespaces. It cannot be an in-conversation side panel under the current beta.

### Gaps
- I did not find an official doc or example that subclasses `AgentBase` with a non-LLM loop other than `ACPAgent` itself. The pattern is supported by the code, not by the docs.
- Not verified: whether a REST-created conversation with an unknown-to-Canvas agent kind lists and renders cleanly in Canvas. Canvas branches on `agent_kind` in several places.

## 3. ACP support: OpenHands as ACP server, OpenHands as ACP client (ACPAgent), and what survives the bridge into the web GUI

### Takeaway
OpenHands is an ACP **client/host** in its main product line. The SDK's `openhands.sdk.agent.ACPAgent` spawns any stdio ACP agent and the agent-server exposes it to Agent Canvas. Canvas has built-in presets for Claude Code, Codex and Gemini CLI, plus a **"Custom"** option that accepts any ACP launch command. OpenHands as an ACP **server/agent** (`openhands acp` for Zed/JetBrains/Toad) lives only in the OpenHands-CLI, which has been unmaintained since Aug 2026. The bridge keeps:
- streamed assistant text,
- thoughts (folded into the final message's reasoning),
- tool calls (start plus one terminal update, with kind/title/rawInput/rawOutput/content including diffs),
- cost/usage,
- cancel.

It drops plans, mode/command/session-info updates and any subagent structure. It auto-approves permissions, declines elicitations and offers no client fs/terminal capabilities.

### Cited Findings
**OpenHands as ACP client**
- `ACPAgent`: "Instead of calling an LLM directly, the agent spawns an ACP server subprocess and communicates with it over JSON-RPC… The server manages its own LLM, tools, and execution." Usage: `ACPAgent(acp_command=["npx","-y","@agentclientprotocol/claude-agent-acp"])`. Unsupported fields are `tools`, `mcp_config`, `condenser` and `critic` (they raise `NotImplementedError`). "Permission requests from the server are automatically granted"; "Token usage and costs from the server are captured into the agent's `LLM.metrics`". It works with `RemoteConversation` via `/api/acp/conversations` routes — [docs sdk/guides/agent-acp.mdx](https://github.com/OpenHands/docs/blob/main/sdk/guides/agent-acp.mdx) (= https://docs.openhands.dev/sdk/guides/agent-acp), [example 40_acp_agent_example.py](https://github.com/OpenHands/software-agent-sdk/blob/main/examples/01_standalone_sdk/40_acp_agent_example.py)
- `ACPAgent` appends the rendered `AgentContext` (skills catalog, repo context, datetime, `system_message_suffix`) to the **user message text** sent to the ACP server; `secrets` are injected into the subprocess env and masked in output — [docs sdk/guides/agent-acp.mdx](https://github.com/OpenHands/docs/blob/main/sdk/guides/agent-acp.mdx)
- Pinned library: `agent-client-protocol>=0.12.1,<0.13.0`, with the comment "0.11.0 reordered prompt() args, broke the client (#4830)". The provider registry is `openhands.sdk.settings.acp_providers`, and there is an install catalog `acp_install_catalog` — [openhands-sdk/pyproject.toml](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-sdk/pyproject.toml), [sdk/settings/](https://github.com/OpenHands/software-agent-sdk/tree/main/openhands-sdk/openhands/sdk/settings)
- `ACPAgent` config fields include:
  - `acp_command`, `acp_server`, `acp_args`, `acp_session_mode`, `acp_model`.
  - `acp_prompt_timeout`, `acp_startup_timeout`.
  - `acp_resume_session_id` (uses ACP `session/load`), `acp_file_secrets`, `acp_isolate_data_dir`.
  - Source: [acp_agent.py ~L1714–1870](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-sdk/openhands/sdk/agent/acp_agent.py)
- The handshake is `conn.initialize(protocol_version=1)` with no client capabilities advertised. The client-side `write_text_file`/`read_text_file`/`create_terminal`/… methods all `raise NotImplementedError("ACP server handles file operations")`. `create_elicitation` returns decline; `ext_method` returns `{}` — [acp_agent.py ~L1602–1700, ~L3090](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-sdk/openhands/sdk/agent/acp_agent.py)
- `session_update` handling in `acp_agent.py ~L1427–1600`:
  - `AgentMessageChunk` text is masked, accumulated and relayed live via `on_token`.
  - `AgentThoughtChunk` is accumulated, then attached as `reasoning_content` of the final assistant message (~L3763–3785).
  - `UsageUpdate` stores context size and cost. Cost deltas go to `llm.metrics.add_cost` (~L2062–2100); for Gemini, which sends no UsageUpdate, cost is derived from tokens.
  - `ToolCallStart` emits one "started" `ACPToolCallEvent`. `ToolCallProgress` is merged silently and emits exactly one terminal event ("Persist exactly one terminal event per tool call").
  - **Everything else is dropped**: `else: logger.debug("ACP session update: %s", …)`. This covers plans, available-commands, mode, session-info and user-message-chunk updates.
  - Source: [acp_agent.py](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-sdk/openhands/sdk/agent/acp_agent.py)
- `ACPToolCallEvent(Event)` fields: `tool_call_id, title, status, tool_kind, raw_input, raw_output, content: list, is_error`. It has no parent/child field and is "*not* an `LLMConvertibleEvent`". `raw_output` is truncated to `MAX_ACP_CONTENT_CHARS` — [sdk/event/acp_tool_call.py](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-sdk/openhands/sdk/event/acp_tool_call.py)
- Pause/cancel maps to ACP `session/cancel` (`_arequest_session_cancel`) — [acp_agent.py ~L3446](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-sdk/openhands/sdk/agent/acp_agent.py)

**In Agent Canvas (web GUI)**
- "Agent Canvas can drive your conversations with the built-in OpenHands agent or with an external ACP agent — Claude Code, Codex, or Gemini CLI… the Agent Server spawns the agent's own CLI as a subprocess and relays each turn". Default commands: `npx -y @agentclientprotocol/claude-agent-acp`, `npx -y @agentclientprotocol/codex-acp`, `npx -y @google/gemini-cli --acp`. "**Custom ACP servers**: Any stdio ACP server works: choose Custom in Settings → Agent and enter its launch command… Pass credentials by adding the env vars the server reads as global secrets." Saving writes `agent_kind`, `acp_server`, `acp_command`, `acp_model` via `PATCH /api/settings` — [docs/ACP_AGENTS.md](https://github.com/OpenHands/OpenHands/blob/main/docs/ACP_AGENTS.md) (also https://docs.openhands.dev/openhands/usage/agent-canvas/acp-agents)
- Containerized ACP: image `ghcr.io/openhands/agent-server:1.47.0-python` "pre-installs the ACP CLI wrappers". Credentials go in as `LookupSecret`s. Per-conversation HOME isolation (`acp_isolate_data_dir`, SDK#3492) is not yet exposed by the TS client (agent-canvas#1019) — [docs/ACP_AGENTS.md](https://github.com/OpenHands/OpenHands/blob/main/docs/ACP_AGENTS.md)
- Search results also show an SDK PR adding OpenCode as a built-in ACP provider, "feat(acp): add OpenCode as a built-in ACP provider" — [software-agent-sdk PR #4827](https://github.com/OpenHands/software-agent-sdk/pull/4827) (merge status not verified)
- Blog post "Controlling any Coding Agent with the OpenHands Agent Canvas and SDK" — [openhands.dev blog](https://www.openhands.dev/blog/use-any-coding-agent-in-openhands-with-acp) (blocked by proxy; only the search snippet was seen; date unknown)

**OpenHands as ACP server**
- OpenHands-CLI offers `openhands acp [--llm-approve] [--resume <id>]` for IDE integration ("Toad, Zed, VSCode, JetBrains"). The CLI is v1.16.0, pins `agent-client-protocol>=0.8.1,<0.9.0`, and its implementation is in `openhands_cli/acp_impl/` — [OpenHands-CLI README](https://github.com/OpenHands/OpenHands-CLI/blob/main/README.md), [pyproject.toml](https://github.com/OpenHands/OpenHands-CLI/blob/main/pyproject.toml), [docs cli/command-reference.mdx](https://github.com/OpenHands/docs/blob/main/openhands/usage/cli/command-reference.mdx). The CLI is "no longer actively maintained" (2026-08-11) — [OpenHands-CLI README](https://github.com/OpenHands/OpenHands-CLI/blob/main/README.md)
- The ACP site's agent list includes "OpenHands" linking to `docs.openhands.dev/openhands/usage/run-openhands/acp`, a page that no longer exists in the docs repo (`run-openhands/` now holds only `gui-mode` and `local-setup`). The ACP **clients** list (120 entries) does not mention OpenHands or Agent Canvas — [ACP get-started/agents.mdx L38](https://github.com/agentclientprotocol/agent-client-protocol/blob/main/docs/get-started/agents.mdx), [clients.mdx](https://github.com/agentclientprotocol/agent-client-protocol/blob/main/docs/get-started/clients.mdx)

**ACP spec features relevant to deep_reasoner (as of 2026-10-01)**
- The "Subagent Sessions" RFD (Vadim Briliantov, Ben Brandt) proposes exposing subagents as child ACP sessions linked through `subagent_update`, gated on a `clientCapabilities.subagents` capability. It is listed under the **Draft** group. Status quo per the RFD: "there is no portable way to tell the Client that an update came from a subagent… Agents therefore have to flatten subagent activity into the parent session, hide it, or encode it in custom tool calls" — [ACP rfds/subagents.mdx](https://github.com/agentclientprotocol/agent-client-protocol/blob/main/docs/rfds/subagents.mdx), [docs.json RFD groups](https://github.com/agentclientprotocol/agent-client-protocol/blob/main/docs/docs.json)
- A "Streamable HTTP / WebSocket transport" RFD is in the **Active** group, so it is not finalized. The ACP schema released v1.10.2 on 2026-10-01 — [ACP rfds/streamable-http-websocket-transport.mdx](https://github.com/agentclientprotocol/agent-client-protocol/blob/main/docs/rfds/streamable-http-websocket-transport.mdx), [ACP repo](https://github.com/agentclientprotocol/agent-client-protocol)

### Inferences
- **Lowest-coupling path**: wrap deep_reasoner as a stdio ACP agent using the same Python `agent-client-protocol` package the OpenHands CLI used for its agent side. Register it in Canvas as a **Custom** ACP agent. No OpenHands fork is needed, and the UI gets chat, live token streaming, tool-call cards, cost and cancel. Suggested mapping:
  - **think** → `agent_thought_chunk`. It appears only at the end, as reasoning, not streamed.
  - **each REPL exec** → `tool_call` with `kind:"execute"`, `rawInput:{"command": <code>}`, `content:[text output]`, `status: completed|failed`.
  - **FinalAnswer** → `agent_message_chunk`s.
  - **cost** → `usage_update.cost`.
  - **subagent(task)** → a tool_call (e.g. `kind:"other"`, title "subagent: …"). Child steps are either flattened into the parent stream or summarized.
- Because ACPAgent advertises no fs/terminal capabilities and auto-approves permissions, deep_reasoner keeps its own sandboxing (local exec / RestrictedPython / Daytona). OpenHands' Docker isolation then applies only to the agent-server container the ACP subprocess runs in.
- Nested sub-agent trees will not survive. ACP has no ratified subagent model (RFD is Draft), OpenHands' bridge has no parent linkage on `ACPToolCallEvent`, and OpenHands drops unknown session updates. Plans, if deep_reasoner emitted any, are also dropped.
- deep_reasoner's Claude Code backbone is orthogonal. Canvas can already run Claude Code directly via `claude-agent-acp`, but in a deep_reasoner deployment Claude Code sits *inside* the deep_reasoner ACP agent.

### Gaps
- I did not verify end-to-end that a custom (non-preset) ACP command renders identically to the presets, e.g. whether `tool_kind` values other than execute/edit/read/fetch get a generic card. Code suggests a generic "ACP_TOOL" title.
- The blog post's date and contents could not be fetched.
- The status of SDK PR #4827 (OpenCode provider) was not checked.

## 4. Frontend coupling to OpenHands event types; can foreign events (sub-agent trees, REPL code+output, cost) display without forking?

### Takeaway
The Canvas renderer uses a **closed TypeScript union** of OpenHands SDK event types with per-`kind` renderers and a `shouldRenderEvent` allow-list, so arbitrary foreign event types will not render. Two things can display without a fork:
- **REPL code + output, as ACP "execute" tool-call cards**. ACP tool calls already have first-class rendering.
- **Cost**, which flows into the standard metrics.

**Nested sub-agent trees** have no rendering path. The closest existing concept is parent/child *conversations*, which would need frontend work to drive from a foreign agent. Extra UI (a namespace/decomposition manager) can be added as a beta Canvas App page, but not as a conversation side panel.

### Cited Findings
- `OpenHandsEvent` is a union of `ActionEvent | MessageEvent | ObservationEvent | UserRejectObservation | AgentErrorEvent | SystemPromptEvent | ACPToolCallEvent ("ACP sub-agent tool call events") | HookExecutionEvent | Condensation* | ConversationStateUpdateEvent | ConversationErrorEvent | PauseEvent | ServerErrorEvent | StreamingDeltaEvent` — [openhands-event.ts](https://github.com/OpenHands/OpenHands/blob/main/src/types/agent-server/core/openhands-event.ts)
- `shouldRenderEvent` filters by type guards and hard-coded action kinds (e.g. hides `PlanningFileEditorAction`, `SwitchLLMAction`, goal-loop reprompts matched by literal prompt text). It renders `ACPToolCallEvent` "at every lifecycle stage". The started card is replaced in place by `tool_call_id` when the terminal event arrives — [should-render-event.ts](https://github.com/OpenHands/OpenHands/blob/main/src/components/conversation-events/chat/event-content-helpers/should-render-event.ts)
- ACP tool-call card rendering:
  - Title keys depend on `tool_kind` (`execute` → RUN, `edit`, `read`, `fetch`, default → generic "ACP_TOOL"). For `execute`, `raw_input.command` is shown as the command line.
  - The body prefers `content` blocks: `diff` blocks render as a diff, `content` text/resource blocks as fenced text. `terminal` blocks and non-text media are skipped. `raw_output` is a fallback.
  - Content is truncated to `MAX_CONTENT_LENGTH`.
  - Source: [get-acp-tool-call-content.ts](https://github.com/OpenHands/OpenHands/blob/main/src/components/conversation-events/chat/event-content-helpers/get-acp-tool-call-content.ts)
- For unknown `ActionEvent` action kinds, the content renderer falls through to `getNoContentActionContent()` (empty string). Unknown observation kinds get a title derived from the type name and `getDefaultEventContent()` for content — [get-action-content.ts](https://github.com/OpenHands/OpenHands/blob/main/src/components/conversation-events/chat/event-content-helpers/get-action-content.ts), [get-event-content.tsx ~L281](https://github.com/OpenHands/OpenHands/blob/main/src/components/conversation-events/chat/event-content-helpers/get-event-content.tsx), [get-observation-content.ts ~L467](https://github.com/OpenHands/OpenHands/blob/main/src/components/conversation-events/chat/event-content-helpers/get-observation-content.ts)
- `reasoning_content` is rendered by `event-message.tsx`. Cost (`accumulated_cost`) is consumed in the conversation WebSocket context — [event-message.tsx](https://github.com/OpenHands/OpenHands/blob/main/src/components/conversation-events/chat/event-message.tsx), [conversation-websocket-context.tsx](https://github.com/OpenHands/OpenHands/blob/main/src/contexts/conversation-websocket-context.tsx)
- Parent/child conversations exist: `parent_conversation_id` / `sub_conversation_ids`, a `use-sub-conversations` hook, and a `launch_child_conversation` client tool whose result is posted back as a user message. They are used for planner→executor flows — [use-handle-plan-click.ts](https://github.com/OpenHands/OpenHands/blob/main/src/hooks/use-handle-plan-click.ts), [should-render-event.ts](https://github.com/OpenHands/OpenHands/blob/main/src/components/conversation-events/chat/event-content-helpers/should-render-event.ts)
- Canvas ships as a standalone app and as library entrypoints ("browser, conversation, files, settings, sidebar, terminal, and i18n modules") via `npm run build:lib`. This gives an embedding option rather than a full fork — [docs/architecture.md](https://github.com/OpenHands/OpenHands/blob/main/docs/architecture.md)
- Apps beta excludes "conversation tabs, arbitrary interface slots… visualizer replacement, or direct Agent Server WebSocket connections" — [canvas-extensions.mdx](https://github.com/OpenHands/docs/blob/main/openhands/usage/agent-canvas/canvas-extensions.mdx)

### Inferences — integration options matrix (effort and coupling)
| # | Option | What deep_reasoner builds | OpenHands changes | What displays | Coupling / risk |
|---|---|---|---|---|---|
| A | **deep_reasoner as Custom ACP agent** behind stock Canvas + agent-server | ACP stdio server (Python `agent-client-protocol`): initialize/new/prompt/cancel, session/update mapping | None (configure "Custom" command + secrets) | Chat, streamed answer text, thoughts (end-of-turn), REPL cells as Run cards, cost, cancel | Low code coupling. Coupled only to the ACP spec plus OpenHands' partial bridge. Loses subagent tree and plans. Permissions auto-approved. ACP lib minor versions have broken OpenHands before (#4830). Effort: days–2 weeks. |
| B | A **+ Canvas App** for namespaces/decompositions | Option A plus an ES-module page (and an optional trusted backend tarball) using `host.agentServer.request` or its own backend | None (beta API) | Separate left-rail page; not an in-chat side panel | Beta API "may change"; local backends only (not Cloud). Effort: +1–2 weeks. |
| C | **Custom `AgentBase` subclass** loaded into agent-server (`OH_EXTRA_PYTHON_PATH` + `--import-modules`) | Python agent whose `step()` runs the deep_reasoner loop, emitting `MessageEvent` / `ACPToolCallEvent` / custom events | Small Canvas patch to select it (settings `agent_kind` is `openhands`/`acp` only), or create conversations via REST | Same cards as A if it emits `ACPToolCallEvent`; custom kinds render poorly | High coupling to a weekly-releasing SDK (pydantic schemas, `step()` contract, resume `verify()`), in-process with server deps. Gains direct access to OpenHands secrets/metrics/sub-conversations. |
| D | A/C **+ fork Canvas** (or use its library entrypoints) for tree view / side panel | Custom renderers for subagent trees; side panel | Fork or embed | Everything | Highest maintenance: Canvas shipped ~19 minor releases in Jul 24–Sep 25 2026. |
| E | Use only **agent-server + typescript-client** under a bespoke UI | Own UI | None | Whatever you build | You still build the UI. Mostly reuses OpenHands' sandbox/secrets/conversation persistence. |
- Sub-agent trees: the only near-term route without a fork is flattening, e.g. titled tool-call cards per subagent with the result as output. A further option is mapping each subagent to a child *conversation* (`parent_conversation_id`), which Canvas partly understands; that would need option C or extra agent-server calls, and is unverified. A proper fix would follow the ACP subagents RFD, which is still Draft, and then OpenHands would need to adopt it.

### Gaps
- I did not run Canvas against a custom ACP agent, so the visual result of options A/B is inferred from code.
- It is unknown whether the Canvas library entrypoints are stable or documented enough to embed a custom conversation view.

## 5. Project health: release cadence, V0→V1 churn, licenses, community size; multi-user hosting implications

### Takeaway
The project is very active but high-churn:
- the SDK went 1.0.0 → 1.50.1 in under 11 months;
- Canvas went v1.6.1 → v1.24.0 in about 2 months;
- the flagship repo was wholesale replaced in July 2026;
- the CLI was deprecated two months after being promised indefinite ACP support.

All core OSS repos are MIT. The old `enterprise/` code was PolyForm Free Trial, and it is gone from the main repo. **Multi-user auth/RBAC/organizations and isolated sandboxes at scale are commercial (OpenHands Cloud / Enterprise).** OSS Canvas plus agent-server is designed for a single user per backend, protected by one shared session API key.

### Cited Findings
**Release cadence (git tag dates)**
- Agent Canvas tags:
  - v1.6.1 (2026-07-24), v1.7.0 (07-29), v1.8.0 (07-30), v1.9.0 (08-03), v1.10.0 (08-05).
  - v1.11.0/v1.12.0 (08-07), v1.13.0 (08-12), v1.14.0 (08-17), v1.15.0 (08-21), v1.16.0 (08-27).
  - v1.17.0 (09-09), v1.18.0 (09-11), v1.19.0 (09-16), v1.20.0 (09-17), v1.21.0 (09-21), v1.22.0 (09-22), v1.23.0 (09-23), v1.24.0 (09-25).
  - Source: [OpenHands tags](https://github.com/OpenHands/OpenHands/tags)
- Pre-Canvas app tags:
  - 0.50.0 (2025-07-23) … 0.62.0 (2025-11-11).
  - **1.0.0 (2025-12-15)**, then 1.1.0 (2025-12-30), 1.2.0 (2026-01-15), 1.3.0 (02-02), 1.4.0 (02-17), 1.5.0 (03-10), 1.6.0 (03-30), 1.7.0 (04-30), 1.8.0 (06-10), 1.9.0–1.11.0 (07-06…07-09).
  - Separate `cloud-1.40.0`…`cloud-1.47.1` tags (2026-06-26…07-21).
  - Source: [OpenHands tags](https://github.com/OpenHands/OpenHands/tags)
- software-agent-sdk tags:
  - 1.0.0a1 (2025-10-15), **1.0.0 (2025-11-07)**.
  - v1.10.0 (2026-01-26), v1.20.0 (2026-05-04), v1.30.0 (2026-07-01), v1.40.0 (2026-07-31).
  - v1.45.0 (09-06) … v1.49.0 (09-16) through v1.49.6 (09-25), v1.50.0 (09-29), v1.50.1 (09-30).
  - Source: [software-agent-sdk tags](https://github.com/OpenHands/software-agent-sdk/tags)
- Commit counts at HEAD: OpenHands/OpenHands 8,374 (including replayed Canvas history); software-agent-sdk 2,473 — git history of both repos (cloned 2026-10-01).

**Churn examples**
- `acp_env` deprecated and removed in 1.29.0 — [agent-acp.mdx](https://github.com/OpenHands/docs/blob/main/sdk/guides/agent-acp.mdx)
- `agent_kind 'llm'` renamed to `'openhands'` — [settings/model.py](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-sdk/openhands/sdk/settings/model.py)
- ACP lib 0.11 broke the client (#4830) — [openhands-sdk/pyproject.toml](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-sdk/pyproject.toml)
- The session socket protocol is "PROVISIONAL" — [session_protocol.py](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-agent-server/openhands/agent_server/session_protocol.py)
- Canvas needs agent-server ≥ 1.47.0, and the `canvas_ui_tool` → `client_tools` migration needed a compatibility mount — [docs/ACP_AGENTS.md](https://github.com/OpenHands/OpenHands/blob/main/docs/ACP_AGENTS.md)
- The Apps API is beta and "may change" — [canvas-extensions.mdx](https://github.com/OpenHands/docs/blob/main/openhands/usage/agent-canvas/canvas-extensions.mdx)

**Licenses**
- OpenHands/OpenHands: MIT ("Copyright © 2025 OpenHands contributors"). software-agent-sdk: MIT (2026). OpenHands-CLI: MIT — LICENSE files in [OpenHands](https://github.com/OpenHands/OpenHands/blob/main/LICENSE), [software-agent-sdk](https://github.com/OpenHands/software-agent-sdk/blob/main/LICENSE), [OpenHands-CLI](https://github.com/OpenHands/OpenHands-CLI/blob/main/LICENSE)
- In the pre-Canvas repo (tag 1.11.0), `enterprise/` was under "PolyForm Free Trial License 1.0.0" and the rest MIT — [LICENSE @1.11.0](https://github.com/OpenHands/OpenHands/blob/1.11.0/LICENSE), [enterprise/LICENSE @1.11.0](https://github.com/OpenHands/OpenHands/blob/1.11.0/enterprise/LICENSE)
- Feature matrix licensing: Agent Canvas (local/VM backend) is Open Source; OpenHands Cloud is Commercial SaaS; OpenHands Enterprise (self-hosted) is Commercial — [docs enterprise/enterprise-vs-oss.mdx](https://github.com/OpenHands/docs/blob/main/enterprise/enterprise-vs-oss.mdx)

**Community size**
- OpenHands/OpenHands: ~89.7k stars, ~11.8k forks (GitHub page, fetched 2026-10-01) — [github.com/OpenHands/OpenHands](https://github.com/OpenHands/OpenHands)
- software-agent-sdk: ~1.2k stars, 595 forks (GitHub page, fetched 2026-10-01; extracted by a summarizer, so treat as approximate) — [github.com/OpenHands/software-agent-sdk](https://github.com/OpenHands/software-agent-sdk)

**Multi-user and hosting (relevant to UW BYO-key hosting)**
- Feature matrix: "Authentication & authorization", "Role-based access control" and "Multi-user organizations" are absent (—) for Agent Canvas (local and VM backends) and present (✓) only for Cloud/Enterprise. "Isolated sandboxes" for the VM backend is "On Roadmap". SAML, LLM gateway & budgeting (LiteLLM) and the plugin marketplace are Enterprise-only — [enterprise-vs-oss.mdx](https://github.com/OpenHands/docs/blob/main/enterprise/enterprise-vs-oss.mdx)
- Self-hosting security: "every `/api/*` call must carry a matching `X-Session-API-Key` header". `--public` mode shows an API-key entry screen. A 2 vCPU/4 GB VM "is plenty for a single user" — [docs/SELF_HOSTING.md](https://github.com/OpenHands/OpenHands/blob/main/docs/SELF_HOSTING.md)
- Newer Canvas supports per-conversation Docker containers (`OH_CONVERSATION_RUNTIME=docker agent-canvas`). "This setting isolates conversation execution; it does not move the entire Canvas or automation service into a sandbox" — [OpenHands README Option 3](https://github.com/OpenHands/OpenHands/blob/main/README.md)
- The agent-server README: "Authentication: Use `session_api_key` in production… The server binds to `0.0.0.0` by default… has full access to the configured workspace directory" — [agent-server README](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-agent-server/openhands/agent_server/README.md)

### Inferences
- For a multi-user UW deployment on OSS, the realistic shape is **one agent-server (with its own secret store holding that user's BYO keys) per user**. It would sit behind a university SSO reverse proxy that injects or validates the session key, with Canvas served once and each user's backend registered. OpenHands OSS does not provide that tenancy layer; it is what Cloud/Enterprise sell. The community `OpenHands/sandbox-server` might help but was not evaluated. Localhost self-hosting is well supported (`npx @openhands/agent-canvas`).
- Given ~weekly SDK and Canvas releases plus repeated architectural pivots (V0 → V1 app-server → Canvas within ~8 months), deep_reasoner should integrate at the most stable seam. That is the ACP protocol (option A), not SDK internals (option C) or a frontend fork (option D). Pin agent-server/Canvas versions in deployment.

### Gaps
- Contributor counts and download stats could not be retrieved (GitHub API blocked).
- Not confirmed: the license of `OpenHands/legacy`, `OpenHands/automation`, `OpenHands/typescript-client` and `OpenHands/sandbox-server`.
- Not evaluated: `OpenHands/sandbox-server`'s fitness for multi-tenant hosting.
- No information was found on OpenHands Enterprise pricing or academic licensing.
