# Alternatives to ACP for UI-to-agent events, and hostable chat front-ends (as of 1 Oct 2026)

Scope: (1) protocols for streaming agent events to a web chat UI; (2) reusable UI kits and hostable multi-user chat apps. Each is judged on how well it handles long, nested, concurrent multi-agent runs (deep_reasoner's agent tree), multi-user hosting with SSO (UW NetID/Shibboleth), and bring-your-own (BYO) API keys.

Research method note: several primary doc sites were blocked by this sandbox's egress proxy: docs.ag-ui.com, a2a-protocol.org, agentclientprotocol.com, ai-sdk.dev, docs.openwebui.com, openwebui.com, librechat.ai, assistant-ui.com, copilotkit.ai, sitepoint.com, linuxfoundation.org and pydantic.dev. Where possible I read the same primary content from the projects' GitHub repos (raw.githubusercontent.com / github.com). Claims taken only from search-engine snippets of those sites are marked "(search snippet)". The reader can trust those less than claims from a fetched page.

Naming hazard: "ACP" means two different things. The **Agent Client Protocol** is Zed's editor-to-agent protocol, the one the team is considering. The **Agent Communication Protocol** was IBM/BeeAI's agent-to-agent protocol, and it merged into A2A in Aug 2025. Many 2025-2026 comparison blog posts mix the two up.

---

## Q1. AG-UI (Agent-User Interaction Protocol, CopilotKit): events, transports, sub-agents, HITL, SDKs, adoption, license, maturity; ACP-to-AG-UI bridges and comparisons

### Takeaway
AG-UI reached a stable **1.0 spec in Sept 2026**. 1.0 adds first-class **sub-agent events** (`SUBAGENT_STARTED/FINISHED/ERROR` plus a `subagentRunId` attribution field on most events), interrupt-based human-in-the-loop, state snapshots/deltas, activity events and reasoning events. It is MIT-licensed and has schema-generated TypeScript, Python and .NET SDKs. Most major agent frameworks and the three big clouds support it. Of the protocols reviewed, it is the closest match to a recursive, concurrent agent tree streamed to a web UI. A small, immature ACP-to-AG-UI bridge exists. I found no rigorous published ACP-vs-AG-UI comparison.

### Cited Findings
**Event model (current spec, read from the repo's `docs/concepts/events.mdx`)** — [AG-UI events doc (GitHub raw)](https://raw.githubusercontent.com/ag-ui-protocol/ag-ui/main/docs/concepts/events.mdx)
- Lifecycle events:
  - `RunStarted` has `threadId`, `runId`, an optional `parentRunId` ("lineage pointer") and an optional `input`.
  - `RunFinished` has `outcome`, a discriminated union of `type: "success"` and `type: "interrupt"`.
  - `RunError` has `message` and `code`.
  - `StepStarted` and `StepFinished` carry `stepName`.
- Text message events: `TextMessageStart`, `TextMessageContent` (delta), `TextMessageEnd`, and `TextMessageChunk`, a convenience form for a whole message.
- Tool call events:
  - `ToolCallStart` has `toolCallId`, `toolCallName` and an optional `parentMessageId`.
  - `ToolCallArgs`, `ToolCallEnd` and `ToolCallChunk`.
  - `ToolCallResult` has `messageId`, `toolCallId`, `content` and `role`.
- State events:
  - `StateSnapshot`.
  - `StateDelta`, which carries a JSON Patch per RFC 6902.
  - `MessagesSnapshot`.
- Activity events: `ActivitySnapshot` and `ActivityDelta`. The spec describes them as "structured, in-progress activity updates that occur between chat messages", following a snapshot/delta pattern so that "UIs [can] render a complete activity view immediately and then incrementally update it as new information arrives."
- Reasoning events: `ReasoningStart`, `ReasoningMessageStart/Content/End/Chunk`, `ReasoningEnd` and `ReasoningEncryptedValue`. The older `THINKING_*` events are deprecated in favour of these.
- Special events: `Raw` (`event`, `source`) and `Custom` (`name`, `value`).
- Sub-agent events:
  - `SubagentStarted` has `subagentRunId`, `name`, an optional `description`, `parentSubagentRunId`, `parentToolCallId` and `parentMessageId`.
  - `SubagentFinished` has `subagentRunId`, `result` and `outcome`.
  - `SubagentError`.
  - Per the doc, these "let an agent report that it has delegated work to a child agent, so a frontend can tell which subagent produced which output". The `subagentRunId` identifies "one invocation, not a reusable subagent definition". Most other events accept an optional `subagentRunId` for attribution.
- Human-in-the-loop: `RunFinished` can end with `{ type: "interrupt", interrupts: [...] }`, meaning "the run paused for human input". The docs also contain a draft section on interrupts and meta events.

**1.0 release (Sept 2026)**
- The "AG-UI 1.0" PR #2774 was **merged 17 Sept 2026**. What it changed:
  - The spec is now written in RFC 2119 language.
  - A single JSON Schema (`spec/draft/schema.json`) is the source of truth, and the TS, Python and .NET SDKs plus the protobuf wire format are generated from it, with a drift gate.
  - Runs now say how they ended: success, interrupt or cancelled.
  - Tool results can be multimodal.
  - Token accounting is unified: cached and reasoning tokens are counted inside totals, not added on top.
  - The protocol version is sent in-band on `RunAgentInput` and `RUN_STARTED`.
  - Breaking: content parts were renamed (e.g. `TextInputContent` → `TextPart`), optional fields are now omitted instead of sent as null, and `BackwardCompatibility_0_0_47` was removed.
  - [PR #2774](https://github.com/ag-ui-protocol/ag-ui/pull/2774)
- Migration guide: the sub-agent events are **new in 1.0**. `THINKING_*` events are retired. 0.x agents work with 1.0 clients through a translation layer kept for 12 months. 1.0 agents work with 0.x clients because new event types are ignored. "JSON over SSE and the protobuf binding are unchanged in framing." — [Migrating to 1.0 (GitHub raw)](https://raw.githubusercontent.com/ag-ui-protocol/ag-ui/main/docs/migrating-to-1-0.mdx)
- Packages `@ag-ui/client`, `core`, `encoder` and `proto` were at **1.0.1 on 29 Sept 2026**. That release fixed `connectAgent()` reconnecting to threads that have pending interrupts, so that page reloads can restore interrupted sessions. — [AG-UI release 2026-09-29](https://github.com/ag-ui-protocol/ag-ui/releases/tag/release/2026-09-29)
- The public 1.0 announcement is dated **30 Sept 2026**. It describes "every event defined by a JSON Schema, TypeScript, Python, and .NET SDKs generated from that schema, plus … subagent support, metadata, multimodal tool results, and human-in-the-loop interrupts", "adopted by Google, Microsoft, Amazon and Oracle", and states "the 1.0 spec won't change". — [SitePoint (search snippet)](https://www.sitepoint.com/ag-ui-1-0-stable-spec-agent-user-interaction/); [CopilotKit blog "Introducing AG-UI 1.0" (search snippet; page blocked)](https://www.copilotkit.ai/blog/ag-ui-1.0). The adoption claim is vendor marketing.

**Transports, SDKs, license, adoption** — [ag-ui GitHub repo](https://github.com/ag-ui-protocol/ag-ui); [README (raw)](https://raw.githubusercontent.com/ag-ui-protocol/ag-ui/main/README.md)
- License: **MIT**. About **16.2k stars** (as of 1 Oct 2026).
- Transports: works over "any event transport (SSE, WebSockets, webhooks, etc.)". There are reference SSE and protobuf encodings.
- SDKs: TypeScript (`@ag-ui/core`, `@ag-ui/client`) and Python, plus Kotlin, Go, Dart, Java, Rust, Ruby, C++ and .NET.
- Frameworks marked supported: LangChain/LangGraph, CrewAI, Microsoft Agent Framework, Google ADK, AWS Strands, Mastra, Pydantic AI, Agno, LlamaIndex, AG2, Claude Agent SDK, Claude Managed Agents, Langroid.
- Marked in progress: OpenAI Agents SDK, Cloudflare Agents, AWS Bedrock Agents.
- Positioning: "MCP gives agents tools", A2A is agent-to-agent, and AG-UI brings agents into user-facing apps. A2A is listed as a supported partnership. **ACP is not mentioned.**
- Features listed: bidirectional state sync, generative UI, frontend tool integration, human-in-the-loop.
- **AWS Bedrock AgentCore Runtime added AG-UI support on 13 Mar 2026**. AgentCore handles auth, session isolation and scaling for AG-UI servers. — [AWS What's New (search snippet)](https://aws.amazon.com/about-aws/whats-new/2026/03/amazon-bedrock-agentcore-runtime-ag-ui-protocol); [AgentCore AG-UI contract](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-agui-protocol-contract.html)
- Python backend helpers: Pydantic AI "natively supports two UI event stream protocols": AG-UI (`AGUIAdapter`) and the Vercel AI Data Stream Protocol (`VercelAIAdapter`).
  - Both are subclasses of an abstract `UIAdapter`. A `UIEventStream` class encodes events "independently of request handling", for the case where the agent runs outside the frontend request.
  - Custom events are forwarded to the frontend.
  - The adapters "also serve as a reference for integrating with other UI event stream protocols".
  - [Pydantic AI UI overview (GitHub raw)](https://raw.githubusercontent.com/pydantic/pydantic-ai/main/docs/ui/overview.md)

**Bridges and comparisons**
- **acp-to-agui** (namanrajpal) describes itself as "a protocol bridge that sits between any coding agent (supporting ACP) and any web frontend". It translates ACP into AG-UI events over SSE, for use with CopilotKit, an AG-UI `HttpAgent` or a custom UI. It is TypeScript, has **22 stars** and was last updated 21 May 2026. — [GitHub topic acp-protocol](https://github.com/topics/acp-protocol); [acp-to-agui](https://github.com/namanrajpal/acp-to-agui)
- The comparison posts I found are generic "MCP vs A2A vs AG-UI" explainers (DZone, DEV, GetStream, HackerNoon "formal analysis of A2A, ACP and AG-UI"). Several of them use "ACP" for IBM's Agent Communication Protocol, not Zed's Agent Client Protocol. — [DZone](https://dzone.com/articles/mcp-vs-a2a-vs-agui); [GetStream](https://getstream.io/blog/ai-agent-protocols/); [HackerNoon](https://hackernoon.com/a-formal-analysis-of-agentic-ai-protocols-a2a-acp-and-agui)

### Inferences
- deep_reasoner maps onto AG-UI 1.0 with few custom events:
  - Each spawned sub-agent becomes `SUBAGENT_STARTED`. Its `parentToolCallId` is the code-execution "tool call" that spawned it, and `parentSubagentRunId` is its parent agent. This gives the tree structure.
  - Each REPL step becomes `TOOL_CALL_START/ARGS/END`, with the code as the args, followed by `TOOL_CALL_RESULT` carrying the printed observation.
  - The "think" text becomes `REASONING_*` or `TEXT_MESSAGE_CHUNK`.
  - FinalAnswer becomes `SUBAGENT_FINISHED.result`, or `RUN_FINISHED` at the root.
  - Per-agent cost can go in `CUSTOM` events, or in the agent tree kept in `STATE_SNAPSHOT/STATE_DELTA`. Token usage is now in-band in 1.0, but dollar cost is not standardised; I did not find a cost field.
  - Concurrent sub-agents interleave on one stream and are separated by `subagentRunId`.
- No token streaming is needed. deep_reasoner's internal run-to-completion events can be emitted as whole-message `*_CHUNK` events as they happen. That gives a live tree even without token deltas.
- The 1.0.1 reconnect-with-pending-interrupt fix and `MessagesSnapshot` together suit runs that last minutes and browser tabs that reload. Server-side run persistence and replay is still the backend's job.
- AG-UI is CopilotKit-led. I found no neutral foundation governance (see Gaps). That is a governance risk, partly offset by AWS, Microsoft and Google adoption and the MIT license.

### Gaps
- Could not fetch docs.ag-ui.com directly. The event list above comes from the GitHub source of the same docs.
- Could not confirm whether AG-UI has moved, or plans to move, to a foundation (LF/AAIF).
- Found no formal published comparison of **Zed's ACP** against AG-UI.
- The exact 1.0.0 package release date is unclear: the PR merged 17 Sept, 1.0.1 shipped 29 Sept, and the announcement is dated 30 Sept.

---

## Q2. A2A (Agent2Agent, Linux Foundation): purpose, task/artifact model, streaming; is it relevant to UI-to-agent? Note on IBM's ACP merging in

### Takeaway
A2A is an **agent-to-agent** interoperability protocol between "independent, potentially opaque" agents. Its v1.0 spec has Task/Message/Part/Artifact/AgentCard objects, streaming, push notifications, and JSON-RPC, gRPC and REST bindings. It can carry human-in-the-loop states, but it is not designed for rendering a UI. It fits deep_reasoner as an optional way to expose or consume agents, not as the chat-UI wire protocol. IBM's Agent Communication Protocol merged into A2A in Aug 2025.

### Cited Findings
- From the spec (read from the GitHub repo `docs/specification.md`; a2a-protocol.org was blocked):
  - It is version **1.0.0**, after 0.3.0, 0.2.6 and 0.1.0.
  - Core objects: **Task** (stateful, lifecycle, artifacts), **Message** (user or agent role, made of Parts), **Part** (text, file or structured data), **Artifact** (task output made of Parts), **AgentCard** (identity, skills, auth) and **contextId** (groups related tasks and messages).
  - Eight task states: SUBMITTED, WORKING, COMPLETED, FAILED, CANCELED, REJECTED, INPUT_REQUIRED, AUTH_REQUIRED.
  - Streaming: `POST /message:stream` returns a Task or Message and then streams `TaskStatusUpdateEvent` and `TaskArtifactUpdateEvent`. `POST /tasks/{id}:subscribe` re-subscribes to an existing task.
  - Push-notification configs deliver updates by webhook.
  - Bindings: JSON-RPC 2.0, gRPC and HTTP+JSON/REST. `spec/a2a.proto` is normative.
  - Purpose: "designed to facilitate communication and interoperability between independent, potentially opaque AI agent systems" without exposing internal state.
  - [A2A specification (GitHub raw)](https://raw.githubusercontent.com/a2aproject/A2A/main/docs/specification.md)
- Timeline:
  - Google donated A2A to the Linux Foundation on 23 June 2025.
  - **v1.0 was released around 9 Apr 2026** under LF governance, with SDKs in Python, TS, Java, Go and C#.
  - By its first anniversary (Apr 2026) it had 150+ supporting organisations and a TSC drawn from eight companies.
  - [Agora Intelligence (secondary, search snippet)](https://agora-intelligence.com/en/blog/leon-a2a-protocol-production-2026); [LF press release (search snippet; page blocked)](https://www.linuxfoundation.org/press/a2a-protocol-surpasses-150-organizations-lands-in-major-cloud-platforms-and-sees-enterprise-production-use-in-first-year); [Google Open Source blog, Apr 2026](https://opensource.googleblog.com/2026/04/a-year-of-open-collaboration-celebrating-the-anniversary-of-a2a.html)
- IBM's **Agent Communication Protocol** (BeeAI, launched Mar 2025) "joined forces" with A2A under LF AI & Data. The ACP team wound down development and contributed to A2A. The ACP repo was archived 27 Aug 2025, and BeeAI now uses A2A adapters. — [LF AI & Data blog, 29 Aug 2025](https://lfaidata.foundation/communityblog/2025/08/29/acp-joins-forces-with-a2a-under-the-linux-foundations-lf-ai-data/); [IBM Think](https://www.ibm.com/think/topics/agent-communication-protocol)
- UI-side support exists:
  - assistant-ui lists A2A as a runtime alongside AG-UI. — [assistant-ui repo](https://github.com/assistant-ui/assistant-ui)
  - AG-UI lists A2A as a supported partnership protocol. — [ag-ui repo](https://github.com/ag-ui-protocol/ag-ui)
  - AWS AgentCore supports MCP, A2A and AG-UI side by side and describes A2A as agent-to-agent and AG-UI as agent-to-user. — [AWS What's New (search snippet)](https://aws.amazon.com/about-aws/whats-new/2026/03/amazon-bedrock-agentcore-runtime-ag-ui-protocol)

### Inferences
- A2A's opaque Task/Artifact model hides the internal agent tree by design, so it cannot carry deep_reasoner's live tree, code cells and per-agent cost without heavy use of extensions or metadata. Use AG-UI or a similar protocol for the web UI.
- A2A could be a later "interop" surface in either direction:
  - other teams' A2A agents could appear as tools or sub-agents inside a namespace;
  - a deep_reasoner namespace could be published as an A2A agent with an AgentCard.

### Gaps
- Could not fetch a2a-protocol.org or the LF press release directly. The exact v1.0 release date rests on secondary sources.
- Did not check whether A2A 1.0 has an official extension for exposing internal sub-task trees or progress to UIs.

---

## Q3. Vercel AI SDK, assistant-ui, CopilotKit: rendering nested agent trees, code + output blocks, cost, long runs

### Takeaway
- **assistant-ui** (MIT) is the strongest ready-made fit for nested transcripts. Its `ToolCallMessagePart.messages` renders a sub-agent's conversation under the tool call that spawned it, recursively up to 16 levels. Its AG-UI runtime builds this from AG-UI 1.0 `SUBAGENT_*` events, and it also supports AI SDK, LangGraph, A2A and fully custom stores.
- **CopilotKit** (MIT) is AG-UI-native and good for shared state, generative UI and human-in-the-loop. Its built-in sub-agent grouping UI was **still an open PR on 30 Sept 2026**.
- **Vercel AI SDK** (now v7) has a well-specified SSE UI message stream with typed, id-reconciled custom `data-*` parts, which suit a live tree side panel. It has no native sub-agent primitive, so nested chat rendering would be custom.

### Cited Findings
**Vercel AI SDK**
- AI SDK 6 was released 22 Dec 2025. It added an `Agent` abstraction and tool-execution approval for human-in-the-loop. — [Vercel blog "AI SDK 6" (search snippet)](https://vercel.com/blog/ai-sdk-6)
- **AI SDK 7 exists.** `ai@7.0.127` was released 1 Oct 2026, with fixes for UI message stream cancellation and tool approval inputs. `ai@6.0.300` was still being patched the same day. — [vercel/ai releases](https://github.com/vercel/ai/releases)
- **UI message stream protocol**: SSE, and a custom backend must send the header `x-vercel-ai-ui-message-stream: v1`. Part types:
  - `start`
  - `text-start/delta/end`
  - `reasoning-start/delta/end`, `reasoning-file`
  - `tool-input-start/delta/available`, `tool-output-available`
  - `source-url`, `file`
  - `data-*` (custom)
  - `start-step/finish-step`
  - `finish`, `error`, `abort`
  - The stream ends with `data: [DONE]`.
  - The protocol is documented explicitly so that compatible endpoints can be "implemented in a different language such as Python".
  - [stream-protocol.mdx (GitHub raw)](https://raw.githubusercontent.com/vercel/ai/main/content/docs/04-ai-sdk-ui/50-stream-protocol.mdx)
- Custom data parts:
  - They are typed by a custom `UIMessage` type.
  - "When you write to a data part with the same ID, the client automatically reconciles and updates that part."
  - **Transient** parts "are sent to the client but not added to the message history" and are read through `onData`.
  - Message metadata is separate from data parts.
  - [streaming-data.mdx (GitHub raw)](https://raw.githubusercontent.com/vercel/ai/main/content/docs/04-ai-sdk-ui/20-streaming-data.mdx)
- A Python backend can emit this stream through Pydantic AI's `VercelAIAdapter`. — [Pydantic AI UI overview](https://raw.githubusercontent.com/pydantic/pydantic-ai/main/docs/ui/overview.md)

**assistant-ui**
- License **MIT**, about **12.4k stars**.
- Composable React primitives: Thread, Message, Composer, ThreadList, ActionBar. It handles streaming, auto-scroll, retries, attachments, markdown and code highlighting.
- Tool calls and JSON can be rendered as React components. Inline human approvals are supported.
- Runtimes: AI SDK, LangGraph/LangChain, AG-UI, A2A, Google ADK, OpenCode, and custom data-stream backends.
- The optional, paid "Assistant Cloud" adds thread persistence and analytics. React Native and terminal (Ink) variants exist.
- [assistant-ui GitHub](https://github.com/assistant-ui/assistant-ui)
- Multi-agent rendering (search snippets of assistant-ui docs; the site was blocked):
  - "Every task subagent transcript is attached to its spawning tool call as `ToolCallMessagePart.messages` … It streams while the subagent runs and nests recursively up to sixteen levels deep when subagents spawn subagents".
  - `MessagePartPrimitive.Messages` renders that field "as a nested thread".
  - "The AG-UI runtime assembles it from the protocol's subagent lifecycle events" (`SUBAGENT_STARTED/FINISHED/ERROR`). The LangChain and OpenCode runtimes fill it their own way.
  - `ExternalStoreRuntime` lets the app own the state through an adapter.
  - [Multi-Agent Chat UI](https://www.assistant-ui.com/docs/tools/multi-agent); [ExternalStoreRuntime](https://www.assistant-ui.com/docs/runtimes/custom/external-store); [@assistant-ui/react-ag-ui (npm)](https://www.npmjs.com/package/@assistant-ui/react-ag-ui)

**CopilotKit**
- License **MIT**, about **37.7k stars**.
- Chat UI, generative UI, shared agent-UI state, human-in-the-loop, AG-UI compliance, and backend tool rendering.
- Frontends: React, Angular, Vue, React Native, Slack and Teams. It has a Python SDK.
- Optional cloud ("CopilotKit Intelligence") provides persistent threads, memories and analytics, with self-hosting options.
- [CopilotKit GitHub](https://github.com/CopilotKit/CopilotKit)
- PR #7444, "group AG-UI subagent work in CopilotChat for React, Vue and Angular":
  - It was **open, not merged**: created 25 Sept 2026, base branch changed 30 Sept 2026.
  - Each sub-agent's work becomes a collapsible group under its `parentToolCallId`, nested by `parentSubagentRunId`, with status badges (Running/Done/Waiting/Failed).
  - Groups can be customised through slots, and `useSubagents()` exposes them read-only.
  - [PR #7444](https://github.com/CopilotKit/CopilotKit/pull/7444)

### Inferences
- **Nested agent tree in chat:**
  - assistant-ui does this today, through its AG-UI runtime or by populating `ToolCallMessagePart.messages` from a custom store.
  - CopilotKit will do it once PR #7444 ships.
  - With the AI SDK it has to be hand-built, either as one `data-agentNode` part per agent reconciled by id or as custom tool-part renderers.
- **Code + output blocks:** all three render tool calls as custom React components, so a "code cell + stdout" renderer is straightforward. This is true whether the cell is modelled as a tool call (AG-UI/AI SDK) or as a data part.
- **Cost:**
  - None of the three has a dedicated cost field; I found only AG-UI 1.0's unified token accounting.
  - Cost would be a custom event, data part or metadata field rendered in the side panel.
  - The AI SDK's `messageMetadata` and AG-UI's `CUSTOM`/`STATE_*` are natural carriers.
- **Long runs:** all are SSE-based, so a minutes-long run needs keep-alives and a server-side run store that the client can reattach to. AG-UI 1.0.1 explicitly fixed reconnecting to interrupted threads.
- **Side panels** (decompositions, namespaces) are ordinary app UI in all three. These are kits, not apps, so there is no constraint.

### Gaps
- Could not fetch assistant-ui.com, ai-sdk.dev or copilotkit.ai directly. The multi-agent details for assistant-ui come from search snippets of its docs.
- Did not confirm whether AI SDK 7 added any sub-agent or nested-message primitive (the v7 changelog was not reviewed in depth).
- Did not confirm the current CopilotKit version number or release date. Search hits mention "v1.50" but give no date.

---

## Q4. Hostable multi-user chat apps (Open WebUI, LibreChat, Chainlit, LobeChat, AnythingLLM): plugging in deep_reasoner, what is lost, licenses, SSO, maturity

### Takeaway
- All of these can host deep_reasoner as an **OpenAI-compatible "model"** or a plugin. Doing so flattens the agent tree into a single assistant message, with at best status lines, collapsible steps or iframe embeds. It also gives up custom side panels unless the app is forked.
- **LibreChat** (MIT; OIDC/SAML/LDAP; per-user `user_provided` keys; v0.8.8 on 30 Sept 2026) is the best off-the-shelf fit for UW SSO plus BYO keys.
- **Open WebUI** is the most popular and has no-timeout Python "pipes", but it has had a **non-OSI branding license since v0.6.6**.
- **Chainlit** is Python-native with nested steps, which suits a tree, but it has been **community-maintained since May 2025** and recently patched critical CVEs.

### Cited Findings
**Open WebUI**
- License history:
  - MIT, then BSD-3 on 10 Jan 2025.
  - From **v0.6.6 (19 Apr 2025)**, a branding-protection clause was added on top of BSD-3. The docs call the result "not an OSI-approved 'open source' license".
  - Code up to v0.6.5 stays BSD-3.
  - [Open WebUI license docs (search snippet)](https://docs.openwebui.com/license/); [HN discussion](https://news.ycombinator.com/item?id=43901575)
- The LICENSE file itself (fetched):
  - "Licensees are strictly prohibited from altering, removing, obscuring, or replacing any 'Open WebUI' branding".
  - The exceptions are deployments whose "total number of end users … does not exceed fifty (50) within any rolling thirty (30) day period", prior written permission, or "a duly executed enterprise license".
  - Contributions require a CLA.
  - [LICENSE (GitHub raw)](https://raw.githubusercontent.com/open-webui/open-webui/main/LICENSE)
- Versions: v0.11.0 (27 Jul 2026) reorganised the UI; **v0.11.4 shipped 25 Sept 2026**. — [Open WebUI blog v0.11.0 (search snippet; site blocked)](https://openwebui.com/blog/v0-11-0-the-interface-reorganized)
- Plugin surface:
  - A **Pipe Function** "appears as a selectable model in the UI". — [deepwiki summary of OWUI docs (secondary)](https://deepwiki.com/open-webui/docs/4.5-pipelines)
  - Pipes and tools can emit `status`, `message`/`chat:message:delta`, `replace`, `files`, `embeds` (rendered "inside a sandboxed iframe with `allow-scripts`"), `source`/`citation` ("references and code execution results"), `notification` and `chat:title`, and can call `input`/`confirmation`/`execute` dialogs.
  - "There is **no timeout** on pipe, tool, or action execution. Your code can run for minutes or hours."
  - Caveat: message content must be returned or yielded, or the frontend's final save overwrites it.
  - [OWUI events doc (GitHub raw)](https://raw.githubusercontent.com/open-webui/docs/main/docs/features/extensibility/plugin/development/events.mdx)
- Auth: OAuth/OIDC, **trusted-header auth** behind an authenticating reverse proxy (`WEBUI_AUTH_TRUSTED_EMAIL_HEADER`), and **SCIM 2.0** provisioning. — [OWUI SSO docs (search snippet)](https://docs.openwebui.com/features/authentication-access/auth/sso/)
- BYO keys: "Direct Connections" let users add their own OpenAI-compatible base URL and key.
  - The browser calls the provider directly, with keys in localStorage, bypassing the OWUI backend.
  - Marked experimental.
  - [OWUI Direct Connections (search snippet)](https://docs.openwebui.com/features/chat-conversations/direct-connections/)

**LibreChat**
- License **MIT**, about **45.2k stars**, latest **v0.8.8**. — [LibreChat GitHub](https://github.com/danny-avila/LibreChat)
- Features listed:
  - agents with "Subagents" for delegated work, and an agent marketplace;
  - a sandboxed code interpreter (Python, Node, Go and others);
  - MCP;
  - Artifacts (React, HTML, Mermaid);
  - custom endpoints;
  - **OAuth2, OIDC, SAML, LDAP** auth;
  - OpenTelemetry/Langfuse tracing;
  - **resumable streams**.
  - v0.8.8 added an Agent Management API.
  - [LibreChat GitHub](https://github.com/danny-avila/LibreChat)
- v0.8.8 was released **30 Sept 2026** (Agents SDK 4.0.0). It includes "Honor User-Provided MCP API Key Instead of Forcing OAuth". — [LibreChat changelog v0.8.8 (search snippet)](https://www.librechat.ai/changelog/v0.8.8)
- BYO keys: setting `apiKey: "user_provided"` on a custom endpoint asks each user for their own key in the UI. The key is stored encrypted per user. — [LibreChat custom endpoints docs (search snippet)](https://www.librechat.ai/docs/configuration/librechat_yaml/ai_endpoints)
- SAML and OpenID are mutually exclusive ("only one authentication method can be active at a time"). — [LibreChat SAML docs (search snippet)](https://www.librechat.ai/docs/configuration/authentication/SAML)
- "Remote Agents" expose LibreChat agents through an OpenAI-compatible `/api/v1/chat/completions`. This was beta in early 2026. JWT/OIDC bearer auth was added via PR #12450, and the discussion closed 7 May 2026. — [LibreChat discussion #11640](https://github.com/danny-avila/LibreChat/discussions/11640)

**Chainlit**
- License **Apache-2.0**, about **12.5k stars**.
- "Chainlit is now community-maintained. As of May 1st 2025, the original Chainlit team has stepped back from active development."
- Features: steps and nested steps, chain-of-thought display, password/OAuth/**header** auth, a data persistence layer, custom React elements, and copilot embedding.
- [Chainlit GitHub](https://github.com/Chainlit/chainlit)
- PyPI also notes that Chainlit SAS provides no warranties on future updates. — [PyPI chainlit (search snippet)](https://pypi.org/project/chainlit/)
- v2.9.0 (6 Nov 2025) improved nested steps for multi-agent use (step.input → child step → step.output). — [Chainlit CHANGELOG (search snippet)](https://github.com/Chainlit/chainlit/blob/main/CHANGELOG.md)
- Latest release on the releases page is **v2.12.0, a security release** fixing command injection (CVE-2026-45018) and SSRF (CVE-2026-45019), with breaking MCP config changes. The fetch tool rendered the date as "August 25, 2024", but the 2026 CVE IDs show this is almost certainly 25 Aug 2026. — [Chainlit releases](https://github.com/Chainlit/chainlit/releases)

**LobeChat / LobeHub**
- Licensed under the "LobeHub Community License", which is based on Apache 2.0. Commercial use of the unmodified app is allowed. A commercial license is needed for derivative works that are distributed or commercialised, including rebranding. — [lobehub LICENSE](https://github.com/lobehub/lobehub/blob/main/LICENSE); [aiagentplatforms.dev (secondary)](https://aiagentplatforms.dev/platforms/lobechat/)
- Multi-user through Better Auth (OAuth, email, magic links, MFA). — [aiagentplatforms.dev (secondary)](https://aiagentplatforms.dev/platforms/lobechat/)

**AnythingLLM**
- License MIT. Multi-user mode requires Docker. Includes built-in agents, RAG and custom OpenAI-compatible endpoints. Roughly 65k stars per a third-party tracker. — [Mintplex-Labs/anything-llm](https://github.com/Mintplex-Labs/anything-llm); [ideaproof.io (secondary)](https://ideaproof.io/open-source/project/anythingllm)

### Inferences
**What exposing deep_reasoner as an OpenAI-compatible model (`/v1/chat/completions`) gives up in any of these apps:**
- the live agent tree;
- per-sub-agent transcripts, which could only be shown as collapsed text or status lines;
- cost per node;
- the decomposition and namespace side panels;
- structured human-in-the-loop.
- What survives: final answers, chat history, auth, and (where supported) BYO keys.

**Open WebUI**
- A pipe could do better than plain chat: `status` events per agent step, `citation`/`source` for code results, and an `embeds` iframe pointing at a deep_reasoner-hosted tree view. The no-timeout guarantee helps long runs.
- Side panels for decompositions and namespaces would still need a fork or a separate page.
- **For UW**, a deployment with more than 50 users must keep the Open WebUI branding unless an enterprise license is bought. Keeping the branding is acceptable if the team doesn't mind it, but a fork must also keep it. The non-OSI license may matter for university policy.

**LibreChat**
- MIT plus SAML gives the cleanest fork base for a branded UW deployment. Shibboleth is a SAML 2.0 IdP, though this pairing was not tested here. `user_provided` keys give BYO.
- deep_reasoner would plug in as a custom endpoint. That keeps it flat, unless LibreChat's own agent/subagent UI can be driven externally, which was not verified.

**Chainlit**
- Gives the closest native Python mapping: nested `cl.Step` maps to the agent tree, and its header auth works with a Shibboleth reverse proxy.
- Its community-maintenance status and recent critical CVEs argue against making it the public, multi-user UW front door.

**Overall:** none of these apps gives a Claude.ai-like custom side panel plus a live tree without forking. They are best used as a quick, "good-enough" localhost or demo path, or as a secondary surface.

### Gaps
- Could not read docs.openwebui.com or librechat.ai directly. Several details (Open WebUI SSO and SCIM, Direct Connections, LibreChat SAML exclusivity, `user_provided`) come from search snippets.
- Did not verify whether Open WebUI pipe **UserValves** can hold per-user API keys server-side, which would be the BYO-key path for a pipe.
- Did not verify whether UW's IdP offers OIDC in addition to SAML/Shibboleth. That decides whether OIDC-only apps need a SAML-to-OIDC bridge such as Keycloak.
- Did not verify whether LibreChat's subagent UI can render an *external* agent's sub-agent tree.
- LobeHub and AnythingLLM details rely partly on secondary sources. Their SSO and SAML support was not checked in depth.

---

## Q5. Overall: viable protocol + UI-kit combinations for a web-first, multi-user product with custom side panels, and where Zed's ACP fits

### Takeaway
For a Claude.ai-like, multi-user web product, the most viable stack as of Oct 2026 is:
- **protocol:** **AG-UI 1.0** over SSE;
- **frontend:** a custom React/Next.js app built on **assistant-ui**, or **CopilotKit** once sub-agent grouping ships;
- **backend:** a Python FastAPI service, with the team's own auth (SAML/OIDC) and per-user encrypted key storage.

The AI SDK UI stream is a good second choice if the team wants the Vercel ecosystem, at the cost of custom nesting. **Zed's ACP is designed for editor/IDE ↔ local agent-subprocess integration.** Its remote HTTP/WebSocket transport is still an active RFD that does not target browsers. It suits an *additional* "use deep_reasoner from Zed/JetBrains" adapter, not the web UI's main wire protocol.

### Cited Findings
- ACP remote transport RFD ("Streamable HTTP & WebSocket Transport"):
  - Status **Active**, moved to Active on 2026-07-02.
  - It proposes Streamable HTTP (POST plus long-lived SSE GET streams, one per session, HTTP/2 required) and WebSocket upgrade.
  - Both profiles share the same JSON-RPC messages and lifecycle as the existing stdio local subprocess transport.
  - "ACP authentication is orthogonal and layered on top via HTTP headers, query parameters, or WebSocket subprotocols".
  - Multiple sessions per connection are supported.
  - It does **not** list browser clients as a design goal; it targets SDK implementers, desktop clients and cloud deployments.
  - [ACP RFD (GitHub raw)](https://raw.githubusercontent.com/agentclientprotocol/agent-client-protocol/main/docs/rfds/streamable-http-websocket-transport.mdx)
- A search snippet of the same RFD page says clients supporting remote ACP "MUST support both Streamable HTTP and WebSocket". It also mentions an experimental TypeScript SDK v2 with HTTP/WebSocket transports. — [agentclientprotocol.com RFD (search snippet)](https://agentclientprotocol.com/rfds/streamable-http-websocket-transport)
- acp-ui is an existing web client for ACP:
  - MIT, about 491 stars.
  - Its web version connects to remote agents only over WebSocket. Local stdio agents need a bridge such as `@rebornix/stdio-to-ws`.
  - Configuration lives in per-browser localStorage. Multi-user is not addressed.
  - [acp-ui GitHub](https://github.com/formulahendry/acp-ui)
- assistant-ui consumes AG-UI sub-agent events into nested threads. — [assistant-ui multi-agent docs (search snippet)](https://www.assistant-ui.com/docs/tools/multi-agent)
- CopilotKit's sub-agent grouping UI was in review on 30 Sept 2026. — [PR #7444](https://github.com/CopilotKit/CopilotKit/pull/7444)
- Pydantic AI ships Python adapters for both AG-UI and the AI SDK stream, usable as references or directly. — [Pydantic AI UI overview](https://raw.githubusercontent.com/pydantic/pydantic-ai/main/docs/ui/overview.md)
- AWS AgentCore hosts AG-UI servers with auth and session isolation. This is evidence of production-hosting patterns for AG-UI, though not required here. — [AWS AgentCore AG-UI contract](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-agui-protocol-contract.html)

### Inferences
Ranked options for deep_reasoner:

1. **AG-UI 1.0 + assistant-ui (custom Next.js/React app)**
   - Best match for a nested, concurrent tree: `SUBAGENT_*` events with `parentToolCallId`/`parentSubagentRunId`, rendered recursively via `ToolCallMessagePart.messages`.
   - Code cells become tool-call renderers.
   - The tree and cost side panel come from `STATE_SNAPSHOT/DELTA` or `CUSTOM` events.
   - Decompositions and namespaces panels are plain app pages backed by the team's REST API.
   - Everything is MIT.
   - Multi-user auth (SAML/Shibboleth or OIDC) and BYO-key storage must be built by the team; neither kit provides them.
2. **AG-UI 1.0 + CopilotKit**: similar, stronger on shared state, generative UI and human-in-the-loop. Sub-agent grouping is not yet released.
3. **AI SDK UI message stream + `useChat`, or assistant-ui's AI SDK runtime**
   - Strong ecosystem, and `data-*` parts with id reconciliation are a good fit for a live tree panel.
   - Nesting sub-agent transcripts in the chat is custom work.
   - Lock-in to Vercel's stream format, which changes across major versions (v5 → v6 → v7 in about 15 months).
4. **Fork LibreChat** (MIT, SAML/OIDC, `user_provided` keys, resumable streams) and add an AG-UI-aware deep_reasoner endpoint plus side panels.
   - Gives auth and BYO keys "for free" but means maintaining a fork of a large app.
   - Open WebUI is less attractive for a branded UW fork because of the branding clause above 50 users.
5. **Chainlit**: fastest Python-only prototype with nested steps. Not recommended as the hosted multi-user product, given the community-maintenance status and CVEs.

Where ACP fits:
- ACP's core transport is editor ↔ agent subprocess over stdio. Remote transport is still an RFD, and auth is out of scope.
- So ACP solves "drive deep_reasoner from Zed, JetBrains or Neovim", not "serve a multi-user browser UI".
- A thin ACP adapter over the same internal event bus as the AG-UI endpoint would give editor integrations cheaply. The community acp-to-agui bridge (22 stars) shows the two can be mapped, but it is too immature to depend on.
- If the team builds on OpenHands, whatever OpenHands uses internally for its web UI can sit behind an AG-UI façade. I did not research OpenHands' own protocol in this note.

Design implication: keep deep_reasoner's internal event model protocol-neutral, and write thin encoders for AG-UI (primary web), ACP (editors), optionally the AI SDK stream, and A2A (agent interop). Pydantic AI's `UIAdapter`/`UIEventStream` split is a reference design for this.

### Gaps
- No direct access to agentclientprotocol.com. ACP's core session-update schema (e.g. whether it now has sub-agent or nested-session notifications) was not verified in this note.
- No benchmark or experience reports were found on AG-UI or ACP over very long (multi-minute) SSE runs behind university proxies or load balancers.
- No source compares assistant-ui and CopilotKit specifically for deep recursive trees with many concurrent branches, e.g. render performance with hundreds of sub-agents.
