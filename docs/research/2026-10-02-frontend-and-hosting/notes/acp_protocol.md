# Agent Client Protocol (ACP): spec summary (October 2026) and fit as the web-UI ↔ deep_reasoner event protocol

> Method note: most spec facts below come from the source of agentclientprotocol.com, which lives in
> `github.com/agentclientprotocol/agent-client-protocol` (the `docs/` MDX pages and the `schema/` JSON). I cloned it at commit
> `9e03215` (2026-10-01) and read it directly. Citations give the matching public website URL (the path mirrors `docs/`), plus
> the repo file where that helps. Package versions came from live registry APIs (PyPI, npm, crates.io, Maven Central) on 2026-10-01.
> docs.openhands.dev, openhands.dev and research.ibm.com were blocked by the sandbox egress proxy. OpenHands facts therefore come from
> the `OpenHands/docs` GitHub repo, which is the source of docs.openhands.dev.

## 1. Spec basics: version, governance, and the JSON-RPC lifecycle

### Takeaway
The stable protocol is ACP v1 (`protocolVersion: 1`). It is JSON-RPC 2.0, stdio is the baseline transport, and it has grown since
August 2025 through additive RFDs. The current schema release is v1.24.1 (2026-09-30). ACP v2 has been a public Draft since
2026-07-20 (schema `v2.0.0-alpha.7`). Zed Industries and JetBrains govern the project jointly under an interim BDFL-style model.
The lifecycle is initialize → (authenticate) → session/new | load | resume → session/prompt (streamed `session/update`
notifications, ending in a `stopReason`) → session/cancel/close. Modes are being replaced by "config options", and slash
commands are advertised with `available_commands_update`.

### Cited Findings
**History and governance**
- Zed announced ACP on 2025-08-27, with Google's Gemini CLI as the first reference agent ("Bring Your Own Agent to Zed"). — [Zed blog](https://zed.dev/blog/bring-your-own-agent-to-zed)
- JetBrains said in October 2025 that it would co-develop ACP with Zed (Zed blog "ACP Brings JetBrains on Board"; The Register covered it 2025-10-07). — [Zed blog](https://zed.dev/blog/jetbrains-on-acp); [The Register](https://www.theregister.com/2025/10/07/jetbrains_acp_vs_code/)
- The governance page calls the model interim: "ACP is jointly governed by Zed and JetBrains … while working toward transitioning to an independent foundation." It has two lead maintainers with veto power (BDFL): Ben Brandt (Zed Industries) and Sergey Ignatov (JetBrains). Core maintainers meet every two weeks. Changes go through an RFD ("Request for Dialog") process with stages Draft → Active → Preview → Completed. Only "Completed" can be a one-way-door stability commitment. — [Governance](https://agentclientprotocol.com/community/governance); [RFD process](https://agentclientprotocol.com/rfds/about)
- Sergey Ignatov (JetBrains) became a Lead Maintainer on 2026-02-18. — [Updates](https://agentclientprotocol.com/updates)
- The v2 announcement says v1 shipped "15+ RFDs" through additive, future-compatible evolution. v2 is a Draft, and implementers should "gate your implementation behind the version negotiation AND feature flags", "Don't ship it by default in production", and keep supporting v1 alongside v2. — [ACP v2 Draft announcement, 2026-07-20](https://agentclientprotocol.com/announcements/acp-v2-draft)

**Stabilization timeline** (all from the [Updates page](https://agentclientprotocol.com/updates) and [RFD updates](https://agentclientprotocol.com/rfds/updates))

| Date | What was stabilized or released |
|---|---|
| 2025-10-24 | `clientInfo`/`agentInfo` implementation info |
| 2026-02-04 | Session config options |
| 2026-03-09 | `session/list`, `session_info_update`, ACP Agent Registry |
| 2026-04-22 | `session/resume` |
| 2026-04-23 | `session/close` |
| 2026-05-21/22 | `logout` |
| 2026-06-01 | `additionalDirectories` |
| 2026-06-03 | `_meta` propagation |
| 2026-06-05 | `session/delete`, `usage_update` (context size + cost), message IDs |
| 2026-06-24 | `model_config` category |
| 2026-06-25 | Rust and TS SDKs reach 1.0 |
| 2026-06-29 | `$/cancel_request` |
| 2026-07-06 | Boolean config options |
| 2026-07-22/24 | Elicitation |
| 2026-08-20 | Terminal Authentication RFD completed |
| 2026-09-17 | Tool call `name` |

**Methods in stable v1** — [schema/v1/meta.json](https://github.com/agentclientprotocol/agent-client-protocol/blob/main/schema/v1/meta.json)
- Agent-side methods (client → agent): `initialize`, `authenticate`, `session/new`, `session/load`, `session/set_mode`, `session/set_config_option`, `session/prompt`, `session/cancel` (notification), `session/list`, `session/delete`, `session/resume`, `session/close`, `logout`.
- Client-side methods (agent → client): `session/request_permission`, `session/update` (notification), `fs/read_text_file`, `fs/write_text_file`, `terminal/create|output|release|wait_for_exit|kill`, `elicitation/create`, `elicitation/complete`.
- Protocol-level: `$/cancel_request`.

**initialize and capability negotiation**
- `InitializeRequest {protocolVersion (required), clientCapabilities, clientInfo, _meta}` → `InitializeResponse {protocolVersion, agentCapabilities, authMethods[], agentInfo, _meta}`.
- `ClientCapabilities`: `fs{readTextFile, writeTextFile}`, `terminal`, `session`, `auth`, `elicitation`.
- `AgentCapabilities`: `loadSession`, `promptCapabilities{image, audio, embeddedContext}`, `mcpCapabilities{http, sse}`, `sessionCapabilities{list, delete, additionalDirectories, resume, close}`, `auth`.
- Source: [Initialization](https://agentclientprotocol.com/protocol/v1/initialization); [schema/v1/schema.json](https://github.com/agentclientprotocol/agent-client-protocol/blob/main/schema/v1/schema.json)

**Authentication**
- Agents list `authMethods` in the initialize response. In v1 there are two method types: the default "agent" type, where the client calls `authenticate(methodId)` and the agent runs its own login, and the "terminal" type, where the client launches the agent program interactively to log in, then reconnects and re-initializes.
- `logout` is advertised through `agentCapabilities.auth.logout`.
- In v2 these become `auth/login` and `auth/logout`.
- Source: [Authentication](https://agentclientprotocol.com/protocol/v1/authentication); [schema/v2/meta.json](https://github.com/agentclientprotocol/agent-client-protocol/blob/main/schema/v2/meta.json)

**Sessions**
- `session/new {cwd (required, absolute), additionalDirectories?, mcpServers[] (required), _meta}` → `{sessionId, modes?, configOptions?}`. — [Session Setup](https://agentclientprotocol.com/protocol/v1/session-setup)
- `session/load` is gated by `loadSession`. The agent "MUST replay the entire conversation to the Client in the form of `session/update` notifications" before it responds. The spec presents this as enabling "persistence across restarts and sharing sessions between different Client instances." — [Session Setup](https://agentclientprotocol.com/protocol/v1/session-setup)
- `session/resume` (stable 2026-04-22) reconnects without replaying history. — [Session Setup](https://agentclientprotocol.com/protocol/v1/session-setup)

**Prompt turn (v1)**
- `session/prompt {sessionId, prompt: ContentBlock[]}`. The response `{stopReason}` arrives when the turn ends. Values: `end_turn | max_tokens | max_turn_requests | refusal | cancelled`.
- `session/cancel` is a notification. After it, the client must answer any pending permission requests with `cancelled`.
- Source: [Prompt Turn](https://agentclientprotocol.com/protocol/v1/prompt-turn); [schema/v1/schema.json](https://github.com/agentclientprotocol/agent-client-protocol/blob/main/schema/v1/schema.json)
- In v2, `session/prompt` returns `{messageId}` when the user message is inserted, not when the turn ends. Foreground work is then reported via `state_update` (`running | idle | requires_action`). — [v2 migration](https://agentclientprotocol.com/protocol/v2/migration); [v2 prompt RFD](https://agentclientprotocol.com/rfds/v2/prompt)

**Modes and config options**
- Session modes: `SessionModeState {currentModeId, availableModes[{id, name, description}]}`, set with `session/set_mode` and reported by `current_mode_update`.
- Config options are now preferred: "If an Agent provides `configOptions`, Clients SHOULD use them instead of the `modes` field. Modes will be removed in a future version."
- `SessionConfigOption {id, name, description?, category?}` of type `select` or `boolean`. Categories are `mode`, `model`, `model_config`, `thought_level`, or `_custom`. Set with `session/set_config_option`; the agent pushes `config_option_update`.
- v2 removes modes entirely.
- Source: [Session Config Options](https://agentclientprotocol.com/protocol/v1/session-config-options); [Session Modes](https://agentclientprotocol.com/protocol/v1/session-modes); [v2 migration](https://agentclientprotocol.com/protocol/v2/migration)

**Slash commands**
- The agent sends `available_commands_update {availableCommands: [{name, description, input?: {hint}}]}`.
- The client invokes a command by sending its text in an ordinary `session/prompt`.
- Source: [Slash Commands](https://agentclientprotocol.com/protocol/v1/slash-commands)

### Inferences
- v1 is the version to build on today. v2's prompt lifecycle, where the prompt is acknowledged and work is reported separately (background updates, idle state, upserts), fits long-running recursive runs better. It is a Draft, so plan for a v1 implementation with a v2 migration path.
- A Zed and JetBrains duopoly with an aspiration to join a foundation means the project is healthy but vendor-steered. It is not yet under a neutral foundation, unlike MCP and A2A.

### Gaps
- I did not fetch the Zed and JetBrains blog pages themselves. The dates come from search-result snippets and The Register.
- There is no published date for v2 stabilization. The v2 announcement gives no timeline.

## 2. `session/update` variants, tool calls, plans, permissions, client fs/terminal, MCP passing

### Takeaway
Stable v1 has 11 `session/update` variants. The unstable v1 schema adds plan ops, notices, compaction, and subagent/session-message
variants. v2 (draft) reworks updates into ID-keyed upserts. Tool calls carry a closed `kind` enum, a `status`, and content of
type `content`, `diff` or `terminal`, plus `locations` and free-form `rawInput`/`rawOutput`. The client-side fs and terminal
methods are editor-centric, and v2 removes them. MCP servers are passed per session in `session/new`.

### Cited Findings
**Stable v1 `SessionUpdate` variants** (discriminator `sessionUpdate`) — [schema/v1/schema.json](https://github.com/agentclientprotocol/agent-client-protocol/blob/main/schema/v1/schema.json); [Prompt Turn](https://agentclientprotocol.com/protocol/v1/prompt-turn)
- Message chunks: `user_message_chunk`, `agent_message_chunk`, `agent_thought_chunk`. Each is a `ContentChunk {content: ContentBlock, messageId?}`.
- Tool calls: `tool_call`, `tool_call_update`.
- Other updates: `plan`, `available_commands_update`, `current_mode_update`, `config_option_update`, `session_info_update {title?, updatedAt?}`.
- `usage_update {used, size, cost?: {amount, currency}}`: context-window tokens used and total size, plus optional cumulative session cost. Stable since 2026-06-05.

**Unstable v1 additions** (in `schema.unstable.json`, marked "not part of the spec yet") — [schema/v1/schema.unstable.json](https://github.com/agentclientprotocol/agent-client-protocol/blob/main/schema/v1/schema.unstable.json)
- `plan_update`, `plan_removed`
- `notice`
- `compaction_update`, `compaction_summary_chunk`
- `subagent_update`, `session_message`, `session_message_chunk`
- `PromptResponse.usage`, the per-turn token breakdown from the Draft "End-Turn Token Usage" RFD: `totalTokens`, `inputTokens`, `outputTokens`, `thoughtTokens`, `cachedReadTokens`, `cachedWriteTokens`. — [End-Turn Token Usage RFD](https://agentclientprotocol.com/rfds/end-turn-token-usage)

**v2 (draft) variants** — [schema/v2/schema.json](https://github.com/agentclientprotocol/agent-client-protocol/blob/main/schema/v2/schema.json); [v2 migration](https://agentclientprotocol.com/protocol/v2/migration)
- `user_message(_chunk)`, `agent_message(_chunk)`, `agent_thought(_chunk)`
- `state_update`
- `tool_call_content_chunk`, `tool_call_update`. `tool_call` is removed: the first update creates the call.
- `terminal_update`, `terminal_output_chunk`: agent-owned, display-only terminals with base64 byte chunks.
- `plan_update`, `available_commands_update`, `config_option_update`, `session_info_update`, `usage_update`
- Any `_`-prefixed custom variant.

**Tool call fields** — [Tool Calls](https://agentclientprotocol.com/protocol/v1/tool-calls); [schema/v1/schema.json](https://github.com/agentclientprotocol/agent-client-protocol/blob/main/schema/v1/schema.json)
- `ToolCall {toolCallId (req), title (req), name?, kind?, status?, content?: ToolCallContent[], locations?: [{path, line?}], rawInput?, rawOutput?, _meta?}`. `name` is a programmatic tool name, stable since 2026-09-17.
- `kind` values: `read | edit | delete | move | search | execute | think | fetch | switch_mode | other`.
- `status` values: `pending | in_progress | completed | failed`.
- `ToolCallContent` types:
  - `content`: a normal ContentBlock (text, image, audio, resource_link, resource).
  - `diff`: a file path with old and new text.
  - `terminal`: embeds a terminal the client created with `terminal/create`, by `terminalId`.
- `tool_call_update` patches by `toolCallId`.

**Plan** — [Agent Plan](https://agentclientprotocol.com/protocol/v1/agent-plan); [schema/v1/schema.json](https://github.com/agentclientprotocol/agent-client-protocol/blob/main/schema/v1/schema.json)
- `Plan {entries: [{content, priority: high|medium|low, status: pending|in_progress|completed}]}`.
- Each `plan` update replaces the full list.
- v2 replaces this with `plan_update` keyed by `planId` with a `type` discriminator ("plan variants").

**Permissions** — [schema/v1/schema.json](https://github.com/agentclientprotocol/agent-client-protocol/blob/main/schema/v1/schema.json); [v2 migration](https://agentclientprotocol.com/protocol/v2/migration)
- v1 request: `session/request_permission {sessionId, toolCall: ToolCallUpdate, options: [{optionId, name, kind: allow_once|allow_always|reject_once|reject_always}]}`.
- v1 response: `{outcome: {outcome: "selected", optionId} | {outcome: "cancelled"}}`.
- v2 instead gives requests their own `title`, an optional `description` and an extensible `subject`, rather than a hard-wired tool call.

**Client-side filesystem and terminal** — [File System](https://agentclientprotocol.com/protocol/v1/file-system); [Terminals](https://agentclientprotocol.com/protocol/v1/terminals); [schema/v1/schema.json](https://github.com/agentclientprotocol/agent-client-protocol/blob/main/schema/v1/schema.json); [v2 migration](https://agentclientprotocol.com/protocol/v2/migration)
- Filesystem: `fs/read_text_file {sessionId, path, line?, limit?}` and `fs/write_text_file {sessionId, path, content}`, gated by `clientCapabilities.fs`.
- Terminal: `terminal/create {sessionId, command, args, env, cwd, outputByteLimit}` plus output, wait_for_exit, kill and release, gated by `clientCapabilities.terminal`. In this design the **client** executes the command.
- v2 removes all of these. The migration guide says this surface "was inconsistently implemented outside of a few IDEs". Clients should instead expose such tools by passing an MCP server.

**Elicitation** (stable July 2026) — [Elicitation](https://agentclientprotocol.com/protocol/v1/elicitation); [Updates](https://agentclientprotocol.com/updates)
- `elicitation/create` lets an agent request structured, non-sensitive form input.
- A URL mode directs the user to "secure out-of-band flows".

**MCP passing** — [Session Setup](https://agentclientprotocol.com/protocol/v1/session-setup); [Architecture](https://agentclientprotocol.com/get-started/architecture)
- `mcpServers` on `session/new`, `load` and `resume` is an array of one of:
  - stdio `{name, command, args, env}`, which all agents MUST support;
  - `{type: "http", name, url, headers}`, if `mcpCapabilities.http`;
  - `{type: "sse", …}`, if `mcpCapabilities.sse`. v2 removes SSE.
- The agent connects to these MCP servers itself.
- A Draft "MCP-over-ACP" RFD (unstable `mcp/message` methods) would let a client serve MCP tools through the ACP connection. — [MCP-over-ACP RFD](https://agentclientprotocol.com/rfds/mcp-over-acp)

### Inferences
- The v1 `terminal` content type is not suitable for a REPL whose code runs on the server. It references a terminal the *client* created and executes. For v1, REPL output should be `content` text blocks inside the tool call, for example a fenced code block followed by the stdout. v2's agent-owned display terminals fit better, but they are draft.
- A web UI client can advertise `fs: false` and `terminal: false` and ignore those methods entirely.

- I checked the v1 content shapes against the schema. `diff` content is `{path (req), oldText?, newText (req), _meta?}`. `terminal` content is `{terminalId (req), _meta?}`. — [schema/v1/schema.json](https://github.com/agentclientprotocol/agent-client-protocol/blob/main/schema/v1/schema.json)

### Gaps
- I did not check which clients actually render `locations` ("follow-along") or `rawInput`/`rawOutput`. These rendering choices are left to each client.

## 3. Transports: stdio baseline; status of remote HTTP/WebSocket; multi-client; remote auth

### Takeaway
As of October 2026, the only normative transport is stdio. The v1 spec page still says Streamable HTTP is "in discussion, draft
proposal in progress". A concrete "Streamable HTTP & WebSocket Transport" RFD has been Active since 2026-07-02, owned by a
Transports Working Group (JetBrains and Block/Goose). Official TS, Python, Kotlin and Go SDKs already ship *experimental*
implementations of it. Durability (replay of missed messages, resumable streams) is explicitly deferred to v2. There is no
standardized multi-client session sharing and no user-identity model. Auth for remote agents is "orthogonal": it rides on HTTP
headers, cookies, query parameters or WebSocket subprotocols.

### Cited Findings
**stdio, the only normative transport** — [Transports (v1)](https://agentclientprotocol.com/protocol/v1/transports)
- The v1 transports page lists "1. stdio … 2. _Streamable HTTP (draft proposal in progress)_".
- stdio framing: the client launches the agent as a subprocess, and messages are newline-delimited JSON-RPC.
- Custom transports are allowed if they preserve JSON-RPC and the ACP lifecycle.

**Remote agents are acknowledged but unfinished** — [Introduction](https://agentclientprotocol.com/get-started/introduction); [Architecture](https://agentclientprotocol.com/get-started/architecture)
- The intro page says ACP "is suitable for both local and remote scenarios… Remote agents … communicating over HTTP or WebSocket". It adds: "Full support for remote agents is a work in progress."
- The architecture page still says "the editor boots the agent sub-process on demand, and all communication happens over stdin/stdout".
- Design principle "Trusted": "ACP works when you're using a code editor to talk to a model you trust."

**Transports Working Group** — [Transports WG announcement](https://agentclientprotocol.com/announcements/transports-working-group)
- Announced 2026-04-22, led by Anna Zhdan (JetBrains, core maintainer) and Alex Hancock (Block/Goose).
- "Remote Agent support is a key focus of ACP."

**Streamable HTTP & WebSocket Transport RFD** — authors alexhancock and jh-block, champion anna239 — [RFD](https://agentclientprotocol.com/rfds/streamable-http-websocket-transport); [PR #721](https://github.com/agentclientprotocol/agent-client-protocol/pull/721)
- Status history: Draft on 2026-04-22, Active on 2026-07-02. Its revision history starts with an "Initial draft" entry dated "2025-03-10", which is probably a typo for 2026.
- Shape of the proposal:
  - A single `/acp` endpoint.
  - Streamable HTTP: POST client→server. Responses return `202 Accepted` immediately, except `initialize`, which returns `200` with JSON.
  - Server→client traffic goes on long-lived SSE GET streams: one connection-scoped stream (`Acp-Connection-Id`) and one session-scoped stream per session (`Acp-Connection-Id` + `Acp-Session-Id`).
  - `DELETE` terminates the connection.
  - HTTP/2 is required.
  - Alternatively, a WebSocket upgrade on the same endpoint.
- Requirements: "Clients that support remote ACP over HTTP MUST support both Streamable HTTP and WebSocket", so a server may offer WebSocket only. Clients MUST support cookies, so servers can use sticky sessions. Multiple sessions per connection are allowed. Batch requests return 501.
- Auth: "ACP authentication is orthogonal and layered on top via HTTP headers, query parameters, or WebSocket subprotocols. `Acp-Connection-Id` and `Acp-Session-Id` are transport-level identifiers, not auth tokens."
- What v1 guarantees over this transport: "Sessions survive disconnects"; you reconnect via `session/load`. "Reconnect and retry are up to the implementer"; liveness is up to the implementer. "In-flight messages are not replayed": server→client messages emitted while disconnected are lost.
- Deferred to v2: message IDs for replay, SSE `Last-Event-ID` resumability, defined reconnection semantics, standardized keepalive.
- Implementation plan: Goose is the reference implementation. The Rust SDK (`sacp`) gets client support first, then TS. Origin validation and the `Acp-Protocol-Version` header are deferred to "Phase 4 hardening".

**Experimental SDK implementations**
- TypeScript `@agentclientprotocol/sdk` added "Experimental Streamable HTTP & WebSocket Transport" in v0.27.0 (2026-06-18). The current 1.6.0 (2026-10-01) has `AcpServer` (SSE plus WebSocket upgrade), `createHttpStream` and `createWebSocketStream`. The WebSocket stream defaults to `globalThis.WebSocket` and notes that "Browser WebSocket constructors ignore custom headers" and that "Browser WebSocket uses the platform cookie jar". — [typescript-sdk CHANGELOG / src/ws-stream.ts](https://github.com/agentclientprotocol/typescript-sdk)
- Python `agent-client-protocol` added "Initial implementation of ACP web transport" (PR #118, 2026-07-31). It has an experimental `acp.http.AcpServer` (Starlette/ASGI, `pip install agent-client-protocol[http]`) and `acp.ws.create_websocket_stream`, both docstring-marked "(experimental)". — [python-sdk](https://github.com/agentclientprotocol/python-sdk)
- Kotlin SDK has optional `acp-ktor-client` / `acp-ktor-server` modules: "Ktor utilities for HTTP/WebSocket transports". — [kotlin-sdk README](https://github.com/agentclientprotocol/kotlin-sdk)
- Go (coder/acp-go-sdk) has a streamable HTTP PR; the Java SDK has an HTTP/WebSocket PR. — [coder/acp-go-sdk PR #41](https://github.com/coder/acp-go-sdk/pull/41); [java-sdk PR #7](https://github.com/agentclientprotocol/java-sdk/pull/7)

**Multi-client sessions and observing**
- v1 has no spec for several clients attaching to one live session. `session/load` replay is the only "sharing" mechanism. — [Session Setup](https://agentclientprotocol.com/protocol/v1/session-setup)
- The v2 prompt RFD says decoupling prompt responses from updates and adding message IDs addresses "multi-client replays". Its validation scenarios include "submissions from multiple clients". This is groundwork, not a fan-out spec. — [v2 Prompt RFD](https://agentclientprotocol.com/rfds/v2/prompt)
- The Agent Telemetry Export RFD was removed on 2026-07-02 because its env-var injection "doesn't translate to the new remote transports where agents aren't launched by the client". This shows remote is now the design driver. — [RFD updates](https://agentclientprotocol.com/rfds/updates)

**Remote auth**
- The Terminal Authentication RFD was completed on 2026-08-20. An `auth/status` (get-auth-state) RFD is a Draft. — [RFD updates](https://agentclientprotocol.com/rfds/updates)
- The ACP Registry lists only agents that "support authentication". — [Registry](https://agentclientprotocol.com/get-started/registry)
- There is no per-user identity, tenancy, or authorization concept in the protocol. I found none in the schema. Auth methods describe how the *agent* logs into its model provider, not how a *user* logs into a server.

**Community bridges** (from the official clients list) — [Clients](https://agentclientprotocol.com/get-started/clients)
- "ACP Remote" (acpkit): a remote WebSocket transport.
- "Aptove Bridge": stdio agents to WebSocket.
- `acp_rpc_bridge`: stdio agents to HTTP.
- "ACP to AG-UI": "bridges any ACP agent to web frontends via AG-UI events over SSE".
- marimo's `use-acp`: React hooks for ACP over WebSockets, used with `npx stdio-to-ws "<agent cmd>"`. — [marimo-team/use-acp README](https://github.com/marimo-team/use-acp)

### Inferences
- A browser can speak ACP today only through (a) the experimental HTTP/WebSocket transport, which is draft and expected to change, (b) a stdio↔WebSocket bridge, or (c) a server-side ACP client that translates to your own browser protocol. That last option is the OpenHands pattern; see §5.
- For UW multi-user hosting, everything ACP leaves out must come from your own server layer: authentication (login, OAuth), per-user session isolation, authorization, rate and cost limits, session persistence and replay after disconnect, and multi-tab fan-out. The WebSocket/cookie design of the RFD is compatible with that: cookie-based auth works with browser WebSockets.
- Because "in-flight messages are not replayed" in v1, a browser refresh mid-run would lose events unless the server buffers or persists the event log itself and re-emits it, for example via `session/load` replay.

### Gaps
- I could not confirm whether Goose's reference HTTP/WS implementation is released, or which agents run in production over the remote transport.
- I found no RFD or proposal dedicated to multi-user or multi-tenant hosting, or to multi-client live attach.

## 4. Extensibility, and sub-agents / nested sessions / agent trees

### Takeaway
ACP has strong, sanctioned extension points:
- `_meta` on almost every type;
- `_`-prefixed custom methods and notifications;
- custom capabilities advertised under `_meta`;
- in v2, `_`-prefixed enum variants everywhere.

Sub-agents are not in stable ACP. A detailed "Subagent Sessions" RFD (Draft) landed as **unstable schema on 2026-09-30** (schema
v1.24.0, PR #1992). Each child is its own session ID, announced with `subagent_update` on the parent stream. Nesting is
arbitrary, child events are delivered automatically, there is a per-child `cancel` capability, inter-session messages use
`session_message`, and costs are explicitly **not** aggregated. Today the Claude adapter by default flattens Task sub-agents
into the parent session, tagging child tool calls with `_meta.claudeCode.parentToolUseId`. It implements native child
sessions behind a capability flag, but using an earlier draft's message names.

### Cited Findings
**Extension mechanisms** — [Extensibility](https://agentclientprotocol.com/protocol/v1/extensibility)
- `_meta: {[key]: unknown}` exists on most requests, responses, notifications and nested types, including content blocks, tool calls, plan entries and capabilities.
- Root keys `traceparent`, `tracestate` and `baggage` are reserved for W3C trace context.
- "Implementations MUST NOT add any custom fields at the root of a type that's part of the specification."
- "The protocol reserves any method name starting with an underscore (`_`) for custom extensions", for example `_zed.dev/workspace/buffers`. Unknown custom requests get "Method not found" (-32601). Unknown custom notifications SHOULD be ignored.
- Custom capabilities SHOULD be advertised under `_meta` of the capability objects, e.g. `agentCapabilities._meta["zed.dev"]`.

**v2 forward-compatibility** — [ACP v2 Draft announcement](https://agentclientprotocol.com/announcements/acp-v2-draft); [v2 migration](https://agentclientprotocol.com/protocol/v2/migration)
- "Enum-like values across the schema accept unknown variants with a `_` prefix for implementation-specific extensions". This includes `SessionUpdate`, `StateUpdate` and `ToolCallContent` variants.

**Subagent Sessions RFD** — authors Vadim Briliantov and Ben Brandt — [Subagents RFD](https://agentclientprotocol.com/rfds/subagents); [PR #1992](https://github.com/agentclientprotocol/agent-client-protocol/pull/1992); [schema CHANGELOG v1.24.0](https://github.com/agentclientprotocol/agent-client-protocol/blob/main/schema/v1/CHANGELOG.md)
- Status: in the "Draft" group of the RFD index. Schema landed 2026-09-30 behind `unstable_subagents`. Revisions are dated 2026-09-15 and 2026-09-24.
- Problem it states: today agents must "flatten subagent activity into the parent session, hide it, or encode it in custom tool calls". Clients cannot "track nested subagents" or "cancel one subagent without cancelling the parent turn".
- Capability: in v1 the client advertises `clientCapabilities.subagents: {}`. In v2, support is baseline.
- Announcement: `session/update` on the parent with `{sessionUpdate: "subagent_update", sessionId: <child>, title?, description?, capabilities?: {cancel?: {}}, state?, _meta?}`. This must come before any traffic bearing the child ID.
- Nesting: "The outer `sessionId` establishes the immediate parent. This supports arbitrary nesting." A child's own children are announced on the child's stream. A child "cannot reparent … or create a cycle".
- Delivery: "Child events then flow automatically on the same connection." Children reuse every ordinary update type (messages, thoughts, plans, tool calls). Clients "MUST NOT call `session/load` or `session/resume` on a child".
- Restrictions: children are restricted sessions. The client may not prompt, steer, close or configure them unless a capability allows it, and `cancel` is the only defined capability. `session/cancel` on a child cascades to its descendants.
- Children may still use permission, fs and terminal requests.
- Inter-session messages: `session_message` and `session_message_chunk {messageId, senderSessionId?, recipientSessionId?, content}` represent parent→child task text and child→parent results as messages, "rather than tool-call content".
- Work state: v1 carries a state snapshot (`running`, or `idle` + `stopReason`, or `unknown`) on `subagent_update.state`. v2 uses the child's own `state_update`, mirrored on the parent.
- Cost: "Exposing child sessions does not make existing `usage_update.cost` values exclusive or additive." Clients "MUST NOT infer a combined tree total by adding parent and child values". "This RFD adds no cost-scope field". A future usage extension may define inclusive/exclusive breakdowns.
- Validation: the RFD requires validation against both the Claude Code and Codex adapters, and a client with a concurrent-session UI, before stabilization. Rejected alternatives include "Use only tool-call parent/child relationships. This cannot represent nested, independent session streams cleanly" and a `subagentId` on every update.

**Claude adapter today** (`@agentclientprotocol/claude-agent-acp` 0.85.0, 2026-10-01, renamed from `@zed-industries/claude-code-acp` / `claude-agent-acp`) — [README](https://github.com/zed-industries/claude-agent-acp); [docs/air-extensions.md](https://github.com/zed-industries/claude-agent-acp/blob/main/docs/air-extensions.md); [src/tool-calls/renderer.ts](https://github.com/zed-industries/claude-agent-acp/blob/main/src/tool-calls/renderer.ts); [npm](https://www.npmjs.com/package/@agentclientprotocol/claude-agent-acp)
- Default behavior: "Agent/Task lifecycle keeps its legacy ordinary ACP tool-call representation and child interactions stay on the root session."
- Tool calls made inside a subagent carry `_meta.claudeCode.parentToolUseId`, which "Mirrors the SDK's `parent_tool_use_id`".
- Agent/Task calls are flagged `_meta.jetbrains.air.subagent: true` for JetBrains' AIR client, because "ACP has no standard subagent ToolKind yet."
- Native child sessions are enabled when the client sends `clientCapabilities.subagents` or the `_meta.jetbrains.air.capabilities: ["nativeSubagentSessions"]` shim. The adapter then emits `subagent_spawned` and `subagent_state_update`. These names come from the pre-2026-09-15 draft, since merged into `subagent_update`. The adapter's own types file calls itself a "Temporary typed surface for … #1992".

**Agents vs. clients in the RFD's integration notes** — [Subagents RFD](https://agentclientprotocol.com/rfds/subagents)
- The Claude Agent SDK (0.3.280) exposes `parent_tool_use_id`, `listSubagents` and `getSubagentMessages`.
- Codex (0.156.1) has thread/turn IDs and `turn/interrupt`.

**Related Draft RFDs** — [RFD index](https://agentclientprotocol.com/rfds/about); [Proxy Chains RFD](https://agentclientprotocol.com/rfds/proxy-chains)
- `session/fork` (client-initiated; the subagent RFD says it is not a substitute).
- "Agent Extensions via ACP Proxies" (proxy chains, by Niko Matsakis): components between client and agent that can "coordinate between multiple agents".

### Inferences
- The subagent RFD's model maps almost one-to-one onto deep_reasoner's tree:
  - `subagent(task)` → `subagent_update` announcing a child session;
  - the task string → a `session_message` from parent to child;
  - the child's REPL loop → ordinary updates on the child session ID;
  - the child's `FinalAnswer` → a `session_message` back to the parent plus an idle state with `end_turn`;
  - recursive spawns → nesting via the outer `sessionId`;
  - concurrency → interleaved child streams on one connection.

  Its no-aggregation cost rule means deep_reasoner's per-agent and per-tree cost needs a custom `_meta` field until ACP defines accounting scope, for example `_meta.deep_reasoner.cost = {self, subtree}`.
- Today, safe interop means emitting the subagent as a tool call and tagging child events with a `_meta` parent ID, as the Claude adapter does. Gate native `subagent_update` behind the unstable capability. Expect the field names to keep changing: the Claude adapter is already one draft behind.

### Gaps
- I could not find any client, beyond JetBrains AIR via the adapter shim, that renders native subagent sessions today. Zed's support is unconfirmed.
- The RFD names no stabilization target date.

## 5. SDKs and implementations (agents, clients, web/browser clients, bridges, OpenHands)

### Takeaway
Official SDKs exist for TypeScript (1.6.0), Rust (crate 2.2.0), Python (0.12.1 stable, 1.0.0rc2 pre-release), Kotlin (0.30.1)
and Java. Most mature are TS and Rust, which reached 1.0 on 2026-06-25. About 40 agents are listed, including Claude
(adapter), Codex (adapter), Gemini CLI, Copilot CLI, Cursor, Goose, OpenCode, Junie, Kiro and OpenHands. Clients include Zed,
JetBrains, Neovim, Emacs, VS Code extensions, marimo, and many desktop and web UIs. OpenHands uses ACP on the **backend** side:
its browser UI (Agent Canvas) talks OpenHands' own REST/WebSocket API to Agent Server, which spawns ACP agents over stdio.

### Cited Findings
**SDKs**

| SDK | Package and version | Notes |
|---|---|---|
| Python | `pip install agent-client-protocol` (repo agentclientprotocol/python-sdk). PyPI latest stable 0.12.1 (2026-08-16). Pre-releases 1.0.0rc1 (2026-09-11) and 1.0.0rc2 (2026-09-21). First release 0.0.1 on 2025-09-06. | Python >=3.10,<3.15. Pydantic models, asyncio. Experimental HTTP/WS transports and an experimental v2 module. |
| TypeScript | `@agentclientprotocol/sdk` 1.6.0 (2026-10-01). 1.0.0 was 2026-06-24. | Renamed from `@zed-industries/agent-client-protocol` (deprecated 0.4.5). |
| Rust | crate `agent-client-protocol` 2.2.0 (updated 2026-09-18, ~4.8M downloads). | 1.0 announced 2026-06-25. |
| Kotlin | Maven `com.agentclientprotocol:acp`, latest 0.30.1 (lastUpdated 2026-08-25). | The docs page still shows `0.1.0-SNAPSHOT` and "JVM, other targets in progress". |
| Java | agentclientprotocol/java-sdk, with Spring AI examples. | Version not confirmed. |

Sources:
- Python: [Python library page](https://agentclientprotocol.com/libraries/python); [PyPI JSON](https://pypi.org/project/agent-client-protocol/)
- TypeScript and Rust: [npm](https://www.npmjs.com/package/@agentclientprotocol/sdk); [SDK 1.0 announcement](https://agentclientprotocol.com/announcements/sdk-1-0-releases)
- Rust crate: [crates.io](https://crates.io/crates/agent-client-protocol)
- Kotlin: [Kotlin page](https://agentclientprotocol.com/libraries/kotlin); [Maven Central metadata](https://repo1.maven.org/maven2/com/agentclientprotocol/acp/maven-metadata.xml)
- Java: [Java page](https://agentclientprotocol.com/libraries/java)
- Community SDKs exist in Go (several, e.g. coder/acp-go-sdk), C#, Swift, Dart, Elixir, Emacs Lisp (`acp.el`), React (`marimo-team/use-acp`) and others. — [Community libraries](https://agentclientprotocol.com/libraries/community)

**Agents** — [Agents list](https://agentclientprotocol.com/get-started/agents); [Registry](https://agentclientprotocol.com/get-started/registry)
- The official list includes Claude Agent (via the adapter), Codex CLI (via `agentclientprotocol/codex-acp`), Gemini CLI, GitHub Copilot (public preview since 2026-01-28), Cursor, Goose, OpenCode, OpenHands, Junie (JetBrains), Kiro CLI, Kimi CLI, Qwen Code, Mistral Vibe, Cline, Augment, Factory Droid, Docker cagent, fast-agent and Pi (via pi-acp).
- The ACP Registry (stable 2026-03-09) is served at `https://cdn.agentclientprotocol.com/registry/v1/latest/registry.json`.

**Clients** — [Clients list](https://agentclientprotocol.com/get-started/clients)
- Editors and IDEs: Zed, JetBrains IDEs, Neovim (CodeCompanion, avante.nvim, agentic.nvim), Emacs (agent-shell.el), VS Code extensions, Obsidian plugins, Qt Creator, Sublime, Visual Studio (Poolside).
- Notebooks: marimo, Jupyter (agent-client-kernel), DuckDB.
- Web or self-hosted UIs:
  - "ACP UI" (formulahendry; targets include Web);
  - "Casper — A web client for kiro-cli … browser-based chat UI";
  - "tlbx — self-hosted browser control station for persistent ACP agent and terminal sessions";
  - "Panda — a ready-made UI for your ACP agent: you implement the agent side, Panda ships the streaming chat, tool-call cards, inline permission prompts, diffs and session history";
  - "ACP Components — A universal frontend component library for building AI Agent interfaces based on the ACP";
  - "Ghosty Teams — multi-tenant team workspace";
  - "Octop — self-hosted multi-user AI assistant with bidirectional ACP support";
  - Codeg ("self-hosted");
  - "Remote Agent Server — self-hosted ACP agent execution gateway … asynchronous Task API".
- Frameworks: LangChain Deep Agents ACP, Pydantic AI and LangChain via ACP Kit, LlamaIndex workflows-acp, Mastra, Koog (JetBrains), fast-agent.

**OpenHands** (source: `OpenHands/docs` repo, which backs docs.openhands.dev)
- `ACPAgent` in the OpenHands Software Agent SDK "lets you use any Agent Client Protocol server as the backend for an OpenHands conversation … the agent spawns an ACP server subprocess and communicates with it over JSON-RPC". — [sdk/guides/agent-acp.mdx](https://github.com/OpenHands/docs/blob/main/sdk/guides/agent-acp.mdx)
- Its "Auto-approval: Permission requests from the server are automatically granted".
- "Token usage and costs from the server are captured into the agent's `LLM.metrics`".
- It works with remote agent-server deployments via `/api/acp/conversations` routes.
- Agent Canvas, the OpenHands browser UI, can drive "the built-in OpenHands agent or … an external ACP agent". — [agent-canvas/acp-agents.mdx](https://github.com/OpenHands/docs/blob/main/openhands/usage/agent-canvas/acp-agents.mdx)
- The documented flow is Canvas → Agent Server ("PATCH /api/settings", conversation turns) → "spawn + JSON-RPC over stdio" → ACP subprocess.
- "The provider list is sourced from the OpenHands SDK registry … Adding or changing a provider happens upstream in the SDK". The listed providers are Claude Code, Codex and Gemini CLI.
- Agent Server "exposes SDK conversations and workspaces to remote clients through REST and WebSocket APIs". — [OpenHands SDK overview (search snippet)](https://docs.openhands.dev/sdk/arch/overview)
- The OpenHands CLI is itself an ACP agent: "Your IDE launches `openhands acp` as a subprocess". The page says "IDE integration via ACP is experimental". — [cli/ide/overview.mdx](https://github.com/OpenHands/docs/blob/main/openhands/usage/cli/ide/overview.mdx)

### Inferences
- If deep_reasoner implements an **ACP agent** (Python SDK, stdio), it immediately works in Zed, JetBrains, Neovim, Emacs and marimo, and in ACP web UIs such as Panda or ACP UI. In principle it could also become an OpenHands Agent Canvas backend via `ACPAgent(acp_command=[...])`.
- Using deep_reasoner inside Canvas's provider picker appears to need an upstream SDK change. Canvas would also flatten deep_reasoner's agent tree into OpenHands events, and it auto-approves permissions.
- The OpenHands architecture is direct evidence of the "ACP on the server side, product-specific protocol to the browser" pattern.

### Gaps
- I could not verify how OpenHands maps ACP `tool_call` and subagent events into its own event stream and UI. The docs page did not say.
- I did not confirm whether Gemini CLI still requires `--experimental-acp` or uses `--acp`. OpenHands docs use `--acp`; marimo's README uses `--experimental-acp`.
- I did not verify Zed's or JetBrains' current client feature coverage, for example whether they render `usage_update` or subagents.

## 6. Disambiguation: IBM/BeeAI "Agent Communication Protocol"

### Takeaway
There is a second "ACP": IBM Research's *Agent Communication Protocol*, an agent-to-agent protocol for the BeeAI platform, launched
March 2025. It merged into Google-originated A2A under the Linux Foundation on 2025-08-25 and is winding down. It is unrelated to
Zed/JetBrains' *Agent Client Protocol*, which is client(editor/UI)-to-agent, JSON-RPC, and stdio-first.

### Cited Findings
- IBM Research launched the Agent Communication Protocol in March 2025 to power the BeeAI Platform. BeeAI, and with it ACP, was donated to the Linux Foundation the same month. — [i-am-bee discussion #5 / IBM (search snippet)](https://github.com/orgs/i-am-bee/discussions/5)
- On 2025-08-25 it announced: "ACP is officially merging with the A2A under the Linux Foundation umbrella… the ACP team will be winding down active development and will begin contributing its technology and expertise directly to A2A." — [i-am-bee discussion #5](https://github.com/orgs/i-am-bee/discussions/5)
- The repo README now reads "ACP is now part of A2A under the Linux Foundation!" and links an ACP→A2A migration guide. It describes itself as "an open protocol for communication between AI agents, applications, and humans". Packages are `acp-sdk` on PyPI and npm; the site was agentcommunicationprotocol.dev. — [i-am-bee/acp README](https://github.com/i-am-bee/acp)
- Zed's ACP is modeled on LSP: "standardizes communication between code editors/IDEs and coding agents". Its packages are `agent-client-protocol` (PyPI) and `@agentclientprotocol/sdk` (npm), and its site is agentclientprotocol.com. — [Introduction](https://agentclientprotocol.com/get-started/introduction)

### Inferences
- When searching, filter for "Agent **Client** Protocol" and agentclientprotocol.com. Watch for name collisions on PyPI and npm (`acp-sdk` is IBM's).

### Gaps
- I could not fetch IBM's own pages (egress blocked) to confirm transport details of IBM's ACP. It is commonly described as REST-based, but I did not verify that here.

## 7. Fit assessment for deep_reasoner: (a) web frontend ↔ remote multi-user server, (b) nested sub-agent trees

### Takeaway
ACP's v1 *event vocabulary* fits a REPL-based recursive agent well: thoughts, tool calls with execute kind, plans, slash
commands, config options, sessions list/resume, and usage/cost. As a **browser↔multi-user-server wire protocol** it is
immature: the remote transport is a draft, there is no user identity or tenancy, no replay of missed events in v1, and no
multi-client attach. The agent tree is only an unstable draft. Costs per subtree are explicitly out of scope.

A pragmatic architecture:
- Make deep_reasoner a conforming **ACP agent**, for ecosystem reach: Zed, JetBrains, marimo, OpenHands `ACPAgent`, ACP web UIs.
- Have its own web UI talk to it either through ACP-over-WebSocket, as an experimental bet, or through a thin server layer that adds auth, tenancy and persistence.
- Use `_meta` and `_deep_reasoner/...` extensions for tree, cost and decomposition management. Optionally adopt `subagent_update` behind the unstable flag.

### Cited Findings (mapping basis)
- REPL execution → `tool_call` with `kind: "execute"`, `rawInput` (code), `content` (text/markdown blocks), status `pending → in_progress → completed|failed`, `rawOutput`. The v1 `terminal` content type references a *client-created* terminal, so it is not suitable for server-side execution. — [Tool Calls](https://agentclientprotocol.com/protocol/v1/tool-calls); [schema/v1](https://github.com/agentclientprotocol/agent-client-protocol/blob/main/schema/v1/schema.json)
- v2 adds agent-owned, display-only terminals (`terminal_update`, `terminal_output_chunk`) and streamed tool content (`tool_call_content_chunk`), but is draft. — [v2 migration](https://agentclientprotocol.com/protocol/v2/migration)
- "think" text → `agent_thought_chunk`. The final answer → `agent_message_chunk`(s), then `PromptResponse{stopReason:"end_turn"}`. — [schema/v1](https://github.com/agentclientprotocol/agent-client-protocol/blob/main/schema/v1/schema.json)
- Decompositions → `available_commands_update` entries `{name, description, input:{hint}}`. These are invoked as prompt text such as `/decomp-name args`. ACP has no CRUD for commands. — [Slash Commands](https://agentclientprotocol.com/protocol/v1/slash-commands)
- Namespaces and model tiers → `configOptions` (`select`/`boolean`, categories `model`, `model_config`, `thought_level`, `mode`, `_custom`), via `session/set_config_option` and `config_option_update`. — [Session Config Options](https://agentclientprotocol.com/protocol/v1/session-config-options)
- Conversation history sidebar → `session/list`, `session/resume`/`load`, `session/delete`, `session/close`, and `session_info_update` (title). All are stable as of mid-2026. — [Updates](https://agentclientprotocol.com/updates)
- Plan or decomposition progress → `plan` entries `{content, priority, status}`. — [Agent Plan](https://agentclientprotocol.com/protocol/v1/agent-plan)
- Asking the user mid-run (`input()` in the REPL) → `elicitation/create` (stable July 2026). Dangerous operations → `session/request_permission`. — [Elicitation](https://agentclientprotocol.com/protocol/v1/elicitation)
- Cost: `usage_update.cost {amount, currency}` is a cumulative per-session total. The subagent RFD forbids clients summing parent and child values and adds no inclusive/exclusive scope. Per-turn token usage is still a Draft RFD. — [Subagents RFD](https://agentclientprotocol.com/rfds/subagents); [End-Turn Token Usage RFD](https://agentclientprotocol.com/rfds/end-turn-token-usage)
- Agent tree: stable v1 has no representation. Unstable `subagent_update` / `session_message` (schema v1.24.0, 2026-09-30) gives child session IDs, arbitrary nesting, automatic delivery, per-child cancel and work state. — [Subagents RFD](https://agentclientprotocol.com/rfds/subagents)
- Run-to-completion without streaming: v1 does not require token-level streaming. An agent may send coarse updates and then the response. With the draft HTTP transport, POSTs return 202 and the response arrives later on the SSE stream. v2 makes "prompt accepted" separate from "work idle", which suits long and background runs. — [Transport RFD](https://agentclientprotocol.com/rfds/streamable-http-websocket-transport); [v2 Draft announcement](https://agentclientprotocol.com/announcements/acp-v2-draft)
- Multi-user remote: no user identity in the protocol. Auth for remote transport is "orthogonal" (headers, cookies, WebSocket subprotocol). v1 transport promises no message replay after disconnect. Origin validation is deferred. — [Transport RFD](https://agentclientprotocol.com/rfds/streamable-http-websocket-transport)
- Editor assumptions: `session/new` requires an absolute `cwd` and an `mcpServers` array. The design principle is "Trusted … a code editor to talk to a model you trust". — [Session Setup](https://agentclientprotocol.com/protocol/v1/session-setup); [Architecture](https://agentclientprotocol.com/get-started/architecture)

### Inferences
**What maps cleanly**

| deep_reasoner concept | ACP construct |
|---|---|
| think | `agent_thought_chunk` |
| `<repl>` code + observation | `tool_call` (kind=execute, title = short summary or first code line, `rawInput={code}`) + `tool_call_update` (`content` = stdout as fenced text, `rawOutput={stdout, stderr, vars?}`, status) |
| FinalAnswer | `agent_message_chunk` + `end_turn`, with structured value in `_meta` or an embedded `resource` block |
| namespace / model tier | `select` config options |
| per-user decompositions | slash commands (listing and invocation only) |
| chat history | `session/list` / `resume` / `delete` |
| title | `session_info_update` |
| context and cost display | `usage_update` |
| user Q&A | `elicitation` |
| cancel | `session/cancel` (and per-child cancel in the subagent draft) |

**What is missing or weak**
1. **Agent trees** are stable only as flattening. The native model is unstable and changing: the Claude adapter is already one draft behind. For now, emit both a `subagent` tool call carrying `_meta["deep_reasoner"].{agentId, parentAgentId, depth}` on every update, and opt-in `subagent_update` when the client advertises `subagents`.
2. **Cost and tree accounting**: there is no per-agent/subtree cost and no per-turn token usage in stable. Use `_meta` (e.g. `{self, subtree, currency}`) or a `_deep_reasoner/usage` notification.
3. **Decomposition/namespace management** (create, edit or delete a decomposition; manage sandboxes, tools, vars) has no ACP surface. Use `_deep_reasoner/...` extension requests or a separate REST API for the side panel. ACP covers only the chat pane.
4. **"Run a decomposition literally as a fixed program"** has no special concept. It can be a slash command or config option whose run emits the same tool_call stream.
5. **Multi-user hosting**: auth, tenancy, quotas, persistence, reconnect replay and multi-tab observation are all outside ACP. The remote transport is draft, with experimental SDK support (TS 1.x, Python 0.12/1.0rc). A browser using the TS SDK's `createWebSocketStream` with cookie auth is technically feasible now, but would track a moving spec.
6. **Editor-isms** to stub out: `cwd`, `mcpServers`, client `fs`/`terminal` (advertise false), and permission prompts. The web UI can simply not implement these.

**Recommended stance for the team**
- Adopt ACP v1 as the **backend agent interface** and as the semantic event model for the chat pane.
- Pin to stable v1 plus documented `_meta` extensions.
- Treat browser transport as either (i) the experimental ACP WebSocket transport behind your own auth cookie, or (ii) your own WebSocket/SSE protocol that wraps ACP events one-to-one.
- Revisit when the transport RFD reaches Preview/Completed and the subagent RFD stabilizes, likely tied to v2.

### Gaps
- I found no evidence of any production multi-tenant deployment using ACP's HTTP/WS transport. Several self-hosted UIs exist in the clients list, but I did not inspect their architectures.
- I did not determine whether any existing ACP client renders `plan`, `usage_update` or nested subagents well enough to reuse as the deep_reasoner web UI. Candidates to evaluate are Panda, ACP UI, ACP Components and tlbx.
- I could not confirm timelines for v2 stabilization, transport-RFD completion or subagent-RFD completion. None are published.
