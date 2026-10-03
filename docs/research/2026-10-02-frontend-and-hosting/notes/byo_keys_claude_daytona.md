# Hosting Claude Code / Agent SDK and Daytona for many users with their own keys (BYO keys), and safe handling of those keys

Research date: 2026-10-01. Every page was read on that date unless marked otherwise. This is not legal advice; it reports what the published terms say.

Method note: the research proxy blocked direct fetches of daytona.io, openrouter.ai, e2b.dev, modal.com and theregister.com. Those topics were covered as follows:
- **Daytona:** the docs source in the public GitHub repo, frozen at the last open-source tag v0.190.0 (2026-06-23), plus search-result excerpts of the live docs.
- **Modal:** the client source code on GitHub.
- **E2B:** the open-source runtime repo on GitHub, plus search excerpts.
- **OpenRouter:** search-result excerpts of its docs pages only.

Claims that rest only on search excerpts or on secondary sources are marked as such.

## 1. Anthropic policy: may a hosted third-party service run Claude Code or the Agent SDK for its users with their own API keys, or with their Claude Pro/Max logins?

### Takeaway
**API keys: permitted.** A hosted service may run the Claude Agent SDK or Claude Code for its users with each user's own Anthropic API key, or with each user's own Bedrock, Vertex or Foundry credential. This falls under Anthropic's Commercial Terms.

Anthropic's Claude Code legal page sets conditions for products that preinstall or run Claude Code in hosted sandboxes:
- The `claude` binary must not be modified.
- The service must not remove the binary's built-in sign-in methods.
- The service must not pay for, resell or intermediate end users' Claude usage. Each end user authenticates with their own credentials and is billed directly.

**Subscription logins: not permitted for a third-party developer's product.** Using a user's Claude Free, Pro or Max subscription login (OAuth) in such a product is prohibited unless Anthropic has approved it:
- The developer may not offer claude.ai login in its product.
- It may not route requests through plan credentials on behalf of users.
- It may not "collect, store, or intermediate" claude.ai credentials or session tokens.

Anthropic began enforcing this against third-party tools during 2026.

**Academic use:** I found no academic or non-commercial exemption. Anthropic offers research API-credit programs instead.

### Cited Findings

**Which terms apply**
- The Claude Code legal page splits the terms by customer type:
  - "Commercial Terms of Service - for Team, Enterprise, and Claude API users"
  - "Consumer Terms of Service - for Free, Pro, and Max users"

  — [Claude Code: Legal and compliance](https://code.claude.com/docs/en/legal-and-compliance)
- "Use of the Claude Agent SDK is governed by Anthropic's Commercial Terms of Service, including when you use it to power products and services that you make available to your own customers and end users, except to the extent a specific component or dependency is covered by a different license as indicated in that component's LICENSE file." — [Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview)
  - PyPI metadata for `claude-agent-sdk` 0.2.163 (uploaded 2026-09-30) gives the license as "MIT". This presumably covers the wrapper code, not the bundled CLI. — [PyPI claude-agent-sdk JSON](https://pypi.org/pypi/claude-agent-sdk/json)

**"Can customers offer Claude Code in their products?"** (verbatim from the legal page)
- "Unless we've mutually agreed otherwise, preinstalling or running Claude Code in your products or services (e.g. in hosted sandboxes or other agent infrastructure) requires agreeing to our Commercial Terms of Service and complying with the conditions below:" — [Legal and compliance](https://code.claude.com/docs/en/legal-and-compliance)
- Condition 1: "The Claude Code binary must not be modified. Claude Code must be installed and run as published by Anthropic, and customers may not remove, disable, or restrict any authentication method built into it (including methods that permit signing in with a Claude account or the user's own API key)." — [Legal and compliance](https://code.claude.com/docs/en/legal-and-compliance)
- Condition 2: "Customers may not pay for, resell, or intermediate Claude usage on their end users' behalf. Each end user must authenticate with their own Anthropic API key, Claude subscription plan credentials, or 3P inference provider credential (Amazon Bedrock, Google Cloud's Agent Platform, Microsoft Foundry). That usage is billed directly to the end user under their own agreement with Anthropic or, for third-party inference providers, with the applicable provider." — [Legal and compliance](https://code.claude.com/docs/en/legal-and-compliance)
- On the Claude Code name and logo, a product may say in plain text "that your product has Claude Code preinstalled or that it runs Claude Code." It may not use the Claude Code or Anthropic names or logos "as part of your own product, feature, or company name … or in a way that suggests Anthropic built, endorses, or is partnered with your product." — [Legal and compliance](https://code.claude.com/docs/en/legal-and-compliance)

**Authentication and credential use** (verbatim from the legal page)
- "OAuth authentication is intended exclusively for purchasers of Claude Free, Pro, Max, Team, and Enterprise subscription plans and is designed to support ordinary use of Claude Code and other native Anthropic applications." — [Legal and compliance](https://code.claude.com/docs/en/legal-and-compliance)
- "Developers building products or services that interact with Claude's capabilities, including those using the Agent SDK, should use API key authentication through Claude Console or a supported cloud provider. Anthropic does not permit third-party developers to offer Claude.ai login into their own applications, or to route requests through Free, Pro, or Max plan credentials on behalf of their users. Moreover, developers may not collect, store, or intermediate Claude.ai credentials or session tokens — sign-in to a Claude account must complete through Anthropic's own flow." — [Legal and compliance](https://code.claude.com/docs/en/legal-and-compliance)
- The page then sets out two carve-outs:
  - "This does not restrict how customers provision and manage their own API keys or third-party inference provider credentials — for example, configuring an API key in a development environment, secrets manager, or machine image for use by the customer's own authorized users — provided the resulting usage is billed to the key owner … and is not resold or intermediated."
  - "Nor does it prevent an end user from signing in to the unmodified Claude Code binary with their own Claude subscription, including where a platform hosts Claude Code."

  — [Legal and compliance](https://code.claude.com/docs/en/legal-and-compliance)
- "Advertised usage limits for Pro and Max plans assume ordinary, individual usage of Claude Code and the Agent SDK." It also states: "Anthropic reserves the right to take measures to enforce these restrictions and may do so without prior notice." — [Legal and compliance](https://code.claude.com/docs/en/legal-and-compliance)
- The Agent SDK pages say the same: "Unless previously approved, Anthropic does not allow third party developers to offer claude.ai login or rate limits for their products, including agents built on the Claude Agent SDK. Use the API key authentication methods described in the Quickstart instead." — [Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview); [Agent SDK quickstart](https://code.claude.com/docs/en/agent-sdk/quickstart)

**Branding for products built on the Agent SDK**
- Allowed: "Claude Agent", "Claude" (inside a menu already labeled "Agents"), and "{YourAgentName} Powered by Claude".
- Not permitted: "Claude Code" or "Claude Code Agent", or "Claude Code-branded ASCII art or visual elements".
- "Your product should maintain its own branding and not appear to be Claude Code or any Anthropic product."

— [Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview)

**Commercial Terms** (effective June 17, 2025)
- They permit customers to "power products and services Customer makes available to its own customers and end users ('Users')."
- "Customer is responsible for all activity under its account."
- Customer may not "resell the Services except as expressly approved by Anthropic."
- "Anthropic may not train models on Customer Content from Services."
- I found no academic or research exemption clause.

— [Anthropic Commercial Terms](https://www.anthropic.com/legal/commercial-terms) (summary by the fetch tool, with quoted fragments)

**Consumer Terms** (effective October 8, 2025)
- Users may not "access the Services through automated or non-human means, whether through a bot, script, or otherwise" "Except when you are accessing our Services via an Anthropic API Key or where we otherwise explicitly permit it."
- "You may not share your Account login information, Anthropic API key, or Account credentials with anyone else. You also may not make your Account available to anyone else."

— [Anthropic Consumer Terms](https://www.anthropic.com/legal/consumer-terms)

**Usage Policy** (effective September 15, 2025)
- It applies to "anyone who can submit inputs to Anthropic's products," including end users of products built on Claude.
- Consumer-facing chatbots must "disclose to users that they are interacting with AI."
- "Agentic use cases must still comply with the Usage Policy."
- It prohibits creating malware and "Discover[ing] or exploit[ing] vulnerabilities in systems … without authorization."
- I found no explicit crypto-mining clause.

— [Anthropic Usage Policy](https://www.anthropic.com/legal/aup)

**Enforcement timeline** (from news coverage in search results; I could not fetch the articles)
- On 2026-01-09 Anthropic blocked subscription OAuth tokens from working outside its own apps, then reversed course.
- On 2026-02-20 it updated its legal terms to explicitly prohibit subscription OAuth tokens in third-party tools.
- From 2026-04-04 it blocked Pro/Max subscription access for third-party agentic harnesses such as OpenClaw and OpenCode.

— [The Register, 2026-02-20 (search excerpt)](https://www.theregister.com/2026/02/20/anthropic_clarifies_ban_third_party_claude_access/); [WinBuzzer 2026-02-19 (search excerpt)](https://winbuzzer.com/2026/02/19/anthropic-bans-claude-subscription-oauth-in-third-party-apps-xcxwbn/); [AlternativeTo (search excerpt)](https://alternativeto.net/news/2026/2/anthropic-officially-bans-using-subscription-authentication-for-third-party-claude-use)

- The `claude-mem` project (which uses the Agent SDK with CLI subscription auth by default) opened an issue saying it is affected by the April 4, 2026 ban. Its listed workarounds are to set `ANTHROPIC_API_KEY` or switch providers. — [claude-mem issue #1826](https://github.com/thedotmack/claude-mem/issues/1826)

**Academic programs**
- Anthropic runs an "AI for Science" program that gives researchers API credits. — [Anthropic support: AI for Science Program](https://support.claude.com/en/articles/11199177-anthropic-s-ai-for-science-program) (seen in search results only)
- Secondary sources say a 2026 round offered up to $30,000 in credits per project for 50 projects. Applications were due 2026-07-15 and funded projects run 2026-09-01 to 2026-12-01. — [GrantedAI (secondary)](https://grantedai.com/blog/anthropic-claude-science-2026-30k-api-credits-50-projects-july-15-deadline-ai-for-science-researchers-strategy)

### Inferences
**BYO API keys are the compliant path for a UW beta.** Each user pastes their own Anthropic Console key (or Bedrock/Vertex/Foundry credential), and usage bills to them. The "may not pay for, resell, or intermediate" clause means UW should not pay for users' Claude Code usage from a UW key without a separate agreement with Anthropic. That clause is written about "preinstalling or running Claude Code" in products.

**The SDK and the Claude Code clause appear to overlap for a UW-key model.** The Agent SDK's Commercial Terms language ("power products … for your own customers and end users") suggests an Agent-SDK product may use the developer's own key. But the Agent SDK spawns the unmodified `claude` binary, and deep_reasoner shells out to `claude -p` directly. So the stricter Claude Code clause plausibly applies. The published text does not clearly draw the line, so UW should ask Anthropic sales or legal before paying for usage centrally.

**Subscription logins should not be offered in the hosted beta.**
- deep_reasoner must not collect, store or proxy users' claude.ai OAuth tokens. That includes `claude setup-token` output pasted into a web form.
- The only allowed pattern is narrow: a user signs in, through Anthropic's own flow, to the unmodified binary running in a sandbox the platform hosts. That pattern does not fit deep_reasoner's backbone, which drives `claude -p` programmatically on the user's behalf.

**The localhost option has a grey area.**
- A user running deep_reasoner on their own machine with their own `claude` login is closer to "ordinary, individual usage of Claude Code and the Agent SDK".
- But Anthropic's April 2026 enforcement targeted third-party harnesses even when users ran them locally, and claude-mem considered itself affected.
- The safest documentation for localhost is "use an API key". Subscription login would be at the user's own risk and could be blocked without notice.

**UI and branding.**
- The UI may say "runs Claude Code" in plain text, or "deep_reasoner, Powered by Claude".
- It must not call a feature "Claude Code", and must not mimic Claude Code's visuals.
- It must not hide or remove the binary's sign-in methods. For example, it must not patch the binary.

### Gaps
- No page states an academic or non-commercial variant of the Commercial Terms. Whether a free university service counts as "making the Services available to Users" with any special obligations could not be confirmed.
- The legal-and-compliance page shows no "last updated" date. It was read on 2026-10-01.
- I could not fetch the original Anthropic statements behind the January, February and April 2026 enforcement. Those dates come from news excerpts.
- The fetched Commercial Terms page showed "Effective June 17, 2025". I could not confirm whether a newer version exists.
- It is unconfirmed whether Anthropic considers a UW-paid shared key acceptable for an Agent-SDK-based (rather than Claude-Code-branded) research service. Only direct contact with Anthropic can settle this.

## 2. Claude Agent SDK vs. shelling out to `claude -p`: capabilities, authentication, hosting and sandboxing guidance, and whether the SDK is the recommended way to embed Claude Code in a server

### Takeaway
Anthropic positions the Agent SDK (Python and TypeScript) as the way to "embed Claude Code's agent in your own Python or TypeScript application, in a process you operate". It recommends `claude -p --output-format json` only for other languages. The SDK is itself a wrapper that spawns the bundled `claude` binary over stdio, so its abilities overlap heavily with the CLI flags.

The SDK adds in-process features: permission callbacks (`can_use_tool`), Python hook functions, in-process MCP tools (`create_sdk_mcp_server`), `ClaudeSDKClient` multi-turn sessions with `interrupt()`, `SessionStore` for durable transcripts, and typed messages.

Anthropic's hosting docs give explicit multi-tenant guidance:
- per-tenant `cwd`;
- `setting_sources=[]`;
- per-tenant `CLAUDE_CONFIG_DIR`;
- `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`;
- per-tenant egress rules;
- container, gVisor or VM isolation;
- a credential-injecting proxy so the agent never sees keys.

Anthropic also offers "Managed Agents" (beta), which hosts the loop for you.

### Cited Findings

**Positioning**
- The overview's comparison table gives the Agent SDK this row: "Embed Claude Code's agent in your own Python or TypeScript application, in a process you operate | Agent SDK | A library that runs the Claude Code binary". It adds: "To drive the same agent loop from a language other than Python or TypeScript, run the CLI as a subprocess with the `-p` flag and `--output-format json`." — [Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview)
- SDK capabilities are listed as built-in tools, hooks, subagents, MCP, permissions, sessions ("resume or fork later"), skills, commands, memory and plugins. — [Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview)
- Managed Agents is a "Pre-built, configurable agent harness that runs in managed infrastructure". It is in beta (header `managed-agents-2026-04-01`) and needs a Claude API key. Environments are "an Anthropic-managed cloud sandbox, or a self-hosted sandbox on your own infrastructure". It is "not currently eligible for Zero Data Retention". — [Managed Agents overview](https://platform.claude.com/docs/en/managed-agents/overview)

**Python SDK features**
- `query()` creates a new session each time. `ClaudeSDKClient` reuses one session across exchanges and supports `interrupt()`. — [Python SDK reference](https://code.claude.com/docs/en/agent-sdk/python)
- Option fields include:
  - limits and models: `max_budget_usd`, `max_turns`, `model`, `fallback_model`;
  - permissions: `allowed_tools`, `disallowed_tools`, `permission_mode` (`default`, `acceptEdits`, `plan`, `dontAsk`, `bypassPermissions`, `auto`), `can_use_tool` (a callback "invoked only when permission flow falls through to a prompt");
  - extension points: `hooks`, `mcp_servers` (including in-process SDK servers created with `@tool` and `create_sdk_mcp_server`), `strict_mcp_config`;
  - sessions: `resume`, `fork_session`, `continue_conversation`, `session_store`;
  - prompt and environment: `system_prompt` (preset with `append`, custom, or file), `setting_sources`, `env`, `cwd`, `cli_path`, `user` (the POSIX OS user the subprocess runs as);
  - output and agents: `include_partial_messages`, `agents` (subagent definitions), `sandbox`, `task_budget`, `effort`.

  — [Python SDK reference](https://code.claude.com/docs/en/agent-sdk/python)
- `max_budget_usd`: "Stop when client-side cost estimate reaches this USD value. Counts only the call's own spend; totals restored from resumed sessions don't count." — [Python SDK reference](https://code.claude.com/docs/en/agent-sdk/python)
- Python hook events: PreToolUse, PostToolUse, PostToolUseFailure, UserPromptSubmit, Stop, SubagentStop, PreCompact, Notification, SubagentStart, PermissionRequest. The TypeScript SDK supports more. — [Python SDK reference](https://code.claude.com/docs/en/agent-sdk/python)

**CLI equivalents of SDK features**
- `--max-budget-usd` is "print mode only". "Spend from subagents counts toward the cap", and once the cap is reached, spawning another subagent fails with "Budget limit reached". — [CLI reference](https://code.claude.com/docs/en/cli-reference)
- `--permission-prompt-tool` routes permission prompts to an MCP tool. `--permission-prompts none` denies prompts in unattended runs (v2.1.259+). — [CLI reference](https://code.claude.com/docs/en/cli-reference)
- `--forward-subagent-text` emits subagent text with `parent_tool_use_id` in stream-json, which is useful for showing sub-agents. — [CLI reference](https://code.claude.com/docs/en/cli-reference)
- `--restricted` mode is for when "an evaluation harness drives `claude` on a shared machine". It removes the command and code-running tools unless named, confines file tools, and refuses `bypassPermissions`. — [CLI reference](https://code.claude.com/docs/en/cli-reference)
- `--exclude-dynamic-system-prompt-sections` is meant "for scripted, multi-user workloads" and improves prompt-cache reuse. — [CLI reference](https://code.claude.com/docs/en/cli-reference)
- `--no-session-persistence`, `--session-id`, `--resume`, `--fork-session`, `--setting-sources`, `--strict-mcp-config`, `--bare` and `--tools` also exist. — [CLI reference](https://code.claude.com/docs/en/cli-reference)

**Authentication**
- `ANTHROPIC_API_KEY` (the SDK "doesn't load `.env` files automatically").
- Amazon Bedrock: `CLAUDE_CODE_USE_BEDROCK=1`.
- Claude Platform on AWS: `CLAUDE_CODE_USE_ANTHROPIC_AWS=1` with `ANTHROPIC_AWS_WORKSPACE_ID`.
- Google Cloud Agent Platform (Vertex): `CLAUDE_CODE_USE_VERTEX=1`.
- Microsoft Foundry: `CLAUDE_CODE_USE_FOUNDRY=1`.

— [Agent SDK quickstart](https://code.claude.com/docs/en/agent-sdk/quickstart)

**Hosting guidance**
- "The Agent SDK spawns and supervises a `claude` CLI subprocess that owns a shell, a working directory, and session files on disk … One agent session maps to one subprocess." — [Hosting the Agent SDK](https://code.claude.com/docs/en/agent-sdk/hosting)
- Session state lives on local disk: transcripts in `~/.claude/projects/` (or under `CLAUDE_CONFIG_DIR`), CLAUDE.md files, and the working directory. None of it survives a container restart without a `SessionStore`. — [Hosting](https://code.claude.com/docs/en/agent-sdk/hosting)
- Session patterns: ephemeral, long-running, hybrid (which requires a `SessionStore`), and multi-agent container. — [Hosting](https://code.claude.com/docs/en/agent-sdk/hosting)
- Sizing: "1 GiB RAM, 5 GiB disk, and 1 CPU per agent is a reasonable starting point". Use agents per host = (host RAM − overhead) / per-session RAM ceiling. — [Hosting](https://code.claude.com/docs/en/agent-sdk/hosting)
- Cost: "Anthropic token cost typically dominates container infrastructure cost by an order of magnitude or more … roughly $0.05 per hour" per minimally provisioned container. — [Hosting](https://code.claude.com/docs/en/agent-sdk/hosting)
- Multi-tenant isolation inside a shared container: "Pass … `setting_sources=[]` … Set `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` … Point `CLAUDE_CONFIG_DIR` at a per-tenant directory … Use a per-tenant working directory … Apply per-tenant egress rules at your proxy." Auto memory "loads into the system prompt regardless of `settingSources`". — [Hosting](https://code.claude.com/docs/en/agent-sdk/hosting)
- Auth and secrets: "the subprocess reads `ANTHROPIC_API_KEY` from its environment. Supply it from your secret manager, or set `ANTHROPIC_BASE_URL` to route model calls through a proxy that injects the key outside the container." Also: "put authentication at a gateway in front of the agent container", and "keep tool credentials out of the agent environment". — [Hosting](https://code.claude.com/docs/en/agent-sdk/hosting)
- Known limits: "No top-level session timeout" (use `max_turns`), "Memory growth over long sessions", "Large parallel-subagent fanouts can hit rate limits", and "No per-subagent wall-clock deadline". — [Hosting](https://code.claude.com/docs/en/agent-sdk/hosting)
- Anthropic's hosting cookbook has deployable Docker, Modal and Kubernetes examples. — [claude-cookbooks hosting](https://github.com/anthropics/claude-cookbooks/tree/main/claude_agent_sdk/hosting) (linked from the Hosting page; not opened)

**Secure deployment guidance**
- The isolation options compared are sandbox-runtime (bubblewrap/Seatbelt), Docker, gVisor and Firecracker/QEMU VMs. — [Securely deploying AI agents](https://code.claude.com/docs/en/agent-sdk/secure-deployment)
- A hardened example uses `--cap-drop ALL`, `--network none` with a mounted Unix-socket proxy, `--read-only`, `--pids-limit 100`, `--memory 2g` and `--user 1000:1000`. — [Secure deployment](https://code.claude.com/docs/en/agent-sdk/secure-deployment)
- On gVisor: "For multi-tenant environments or when processing untrusted content, the additional isolation is often worth the overhead". — [Secure deployment](https://code.claude.com/docs/en/agent-sdk/secure-deployment)
- On credentials: "The recommended approach is to run a proxy outside the agent's security boundary that injects credentials into outgoing requests … The agent never sees the actual credentials." Suggested proxies are Envoy (`credential_injector`), mitmproxy, Squid and LiteLLM. — [Secure deployment](https://code.claude.com/docs/en/agent-sdk/secure-deployment)
- The Bash permission system "is a permission gate, not a sandbox". — [Secure deployment](https://code.claude.com/docs/en/agent-sdk/secure-deployment)
- sandbox-runtime does "No TLS inspection … Code running inside the sandbox can potentially use domain fronting … to reach hosts outside the allowlist." — [Secure deployment](https://code.claude.com/docs/en/agent-sdk/secure-deployment)
- Anthropic's sandboxing write-up (2025-10-20): "Without network isolation, a compromised agent could exfiltrate sensitive files like SSH keys". Claude Code on the web keeps "sensitive credentials (such as git credentials or signing keys) … never inside the sandbox with Claude." — [Anthropic Engineering: Claude Code sandboxing](https://www.anthropic.com/engineering/claude-code-sandboxing)

### Inferences
**Should deep_reasoner switch to the SDK?** deep_reasoner's current backbone (`claude -p --output-format stream-json`, `--max-budget-usd`, `--allowedTools "Bash(dr repl exec:*)"`, `--append-system-prompt`) is a supported pattern. Switching to the Python SDK would bring:
- in-process `can_use_tool` and hooks, so per-tenant policy can be enforced in Python rather than through CLI allow rules;
- an in-process MCP tool, which could replace the `dr repl exec` Bash indirection and the unix socket;
- `ClaudeSDKClient.interrupt()`;
- `SessionStore` for resumable sessions across hosts;
- the `user=` option to run each tenant's subprocess as a distinct OS user.

The binary and billing are the same either way.

**Per-tenant measures for the shared server:**
- A per-user `CLAUDE_CONFIG_DIR` and `cwd`, with skills written into the per-user directory.
- `setting_sources=[]` (CLI: `--setting-sources` set to nothing, or `--bare`).
- `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`.
- Pass the user's key per subprocess. Better, point `ANTHROPIC_BASE_URL` at a local proxy that injects the decrypted per-user key, so the key never sits in a long-lived environment that model-driven child processes inherit.

**`--max-budget-usd` is not a hard cap.** It is a client-side estimate and does not count spend restored from resumed sessions. Pair it with server-side per-user accounting, and tell users to set spend limits on their own Anthropic Console keys (a Console feature; see Gaps).

**The local REPL backends cannot isolate users.** The "local in-process exec" backend runs model-written code inside the server process, which would expose every user's decrypted keys and data on a multi-user host. RestrictedPython's own description says it "is not a sandbox system or a secured environment" ([PyPI RestrictedPython 8.5](https://pypi.org/pypi/RestrictedPython/json)). In a hosted multi-user beta, only a remote or VM-isolated backend (Daytona or similar), or a gVisor/Firecracker container per user, matches Anthropic's multi-tenant guidance.

### Gaps
- I did not fetch the TypeScript SDK reference, so TypeScript-only hook events are not listed.
- I did not fetch the Agent SDK permissions, cost-tracking or session-storage pages in full.
- Anthropic Console per-key or per-workspace spend limits (which a BYO user could set) were not confirmed in this session.
- Managed Agents pricing and rate limits were not fetched.

## 3. Claude Code ACP adapters: status, what they expose, and how they show sub-agents

### Takeaway
Zed's original adapter, `@zed-industries/claude-code-acp`, is deprecated. It was renamed to `@agentclientprotocol/claude-agent-acp` (repo `agentclientprotocol/claude-agent-acp`, Apache-2.0). That package is actively released: latest 0.85.0, preview 0.85.1-preview.4, registry last modified 2026-10-01.

It wraps the Claude Agent SDK (TypeScript) and authenticates with `ANTHROPIC_API_KEY`.

Sub-agents (Task/Agent tool) are shown in one of two ways:
- as "nested subagent transcripts", but only after both sides negotiate a `subagents` capability;
- otherwise flattened onto the root session as ordinary tool calls.

### Cited Findings
- npm deprecation notice on `@zed-industries/claude-code-acp` (latest 0.16.2): "This package has been renamed to @agentclientprotocol/claude-agent-acp. Please migrate to continue receiving updates." — [npm registry: @zed-industries/claude-code-acp](https://www.npmjs.com/package/@zed-industries/claude-code-acp)
- `@agentclientprotocol/claude-agent-acp` dist-tags (checked 2026-10-01): latest `0.85.0`, preview `0.85.1-preview.4`; modified 2026-10-01T14:50Z. — [npm registry: @agentclientprotocol/claude-agent-acp](https://registry.npmjs.org/@agentclientprotocol/claude-agent-acp)
- An intermediate package, `@zed-industries/claude-agent-acp`, last shipped 0.23.1, about six months before the search date (search excerpt). — [npm: @zed-industries/claude-agent-acp](https://www.npmjs.com/package/@zed-industries/claude-agent-acp)
- The README lists these features:
  - context @-mentions and images;
  - tool calls with permission requests;
  - compact file changes through the negotiated "AIR diff patch extension";
  - following, edit review and TODO lists;
  - nested subagent transcripts;
  - interactive and background terminals;
  - custom slash commands and client MCP servers;
  - session-scoped extensions (goals, structured errors, permission presentation).

  Install with `npm install @agentclientprotocol/claude-agent-acp@preview`; it requires `ANTHROPIC_API_KEY`. — [claude-agent-acp README](https://raw.githubusercontent.com/agentclientprotocol/claude-agent-acp/main/README.md)
- How the README describes sub-agents:
  - Subagent sessions become accessible only after both parties negotiate capabilities.
  - Until released SDKs preserve `clientCapabilities.subagents`, clients can advertise `nativeSubagentSessions` in `_meta.jetbrains.air.capabilities`.
  - Without either signal, child interactions stay on the root session using the legacy tool-call representation.
  - Clients using `_meta["subagent-transcript"]` or `forwardSubagentText` keep flattened child transcripts.

  — [claude-agent-acp README](https://raw.githubusercontent.com/agentclientprotocol/claude-agent-acp/main/README.md)
- The repo has about 2.6k stars and 416 forks, the Apache License 2.0, and a "preview" channel for unreleased main-branch changes. — [GitHub agentclientprotocol/claude-agent-acp](https://github.com/agentclientprotocol/claude-agent-acp)
- Zed lists the adapter as the "Claude Agent" ACP agent. — [Zed ACP: Claude Agent](https://zed.dev/acp/agent/claude-agent) (search result); [Zed blog: Claude Code via ACP](https://zed.dev/blog/claude-code-via-acp) (search result)

### Inferences
- The adapter is a ready-made bridge if deep_reasoner wants to expose its Claude Code worker to ACP clients (Zed, JetBrains), or to drive Claude Code via ACP instead of stream-json.
- It inherits the Agent SDK's terms: API-key auth, and no third-party claude.ai login.
- Its sub-agent model (nested child sessions negotiated by capability) resembles deep_reasoner's recursive sub-agents. It could be a reference design for how deep_reasoner presents nested agents to a UI.

### Gaps
- The exact ACP schema for `clientCapabilities.subagents`, and whether it is part of the released ACP spec or still the JetBrains "AIR" extension, was not confirmed.
- I did not verify whether the adapter supports any authentication other than `ANTHROPIC_API_KEY` (for example Bedrock env vars passed through to the SDK).

## 4. Daytona (2026): key model, per-user BYO keys, isolation, egress, lifecycle, snapshots, quotas, pricing, self-hosting and license, plus alternatives (E2B, Modal, Runloop)

### Takeaway
**Ownership and source.** Daytona went closed-source in June 2026. The public repo is frozen at v0.190.0 (AGPL-3.0, tag dated 2026-06-23) and is unmaintained. The managed service and SDKs continue (Python SDK `daytona` 0.220.0 was released 2026-09-29). A community fork, "Nightona", continues the AGPL code.

**API keys** are organization-scoped. Every user has a personal organization. Keys carry fine-grained scopes (for example `write:sandboxes`, `delete:sandboxes`, `write:snapshots`), optional expiry, and immediate revocation. That makes BYO per-user Daytona keys technically workable: each user's sandboxes, quota and billing stay in their own personal org.

**Isolation** uses Sysbox containers with user namespaces, which share the host kernel. Daytona's marketing also says "dedicated kernel", which conflicts with this.

**Egress** depends on billing tier:
- Tiers 1 and 2 have restricted egress that cannot be overridden. It is restricted to a broad "essential services" list that includes GitHub, PyPI, npm, S3, Vercel, Heroku, Supabase, Anthropic and OpenRouter.
- Tiers 3 and 4 have full access, with `networkAllowList` (IPv4 CIDRs, max 10) or `networkBlockAll`.

**Lifecycle:** auto-stop defaults to 15 minutes, and sandboxes can be made ephemeral.

**New in 2026:** a "Secrets" feature keeps credentials out of sandboxes by substituting placeholders at an outbound proxy. Separately, Daytona disclosed an April 2026 flaw where the API credential could be read from inside sandboxes; it was patched the same day.

**Alternatives:**
- E2B: Firecracker microVMs, with an Apache-2.0 self-hostable runtime and domain-level allow/deny egress.
- Modal Sandboxes: domain and CIDR allowlists and an experimental secret-injecting outbound policy.
- Runloop: VM-based devboxes.

### Cited Findings

**Open-source status and license**
- The repo notice reads: "As of June 2026, Daytona's core development has moved to a private codebase. This repository will receive no further updates, fixes, or releases. It remains public and free to use, fork, and build on under the LICENSE, as is and without support or warranty." — [GitHub daytonaio/daytona README](https://github.com/daytonaio/daytona)
- The last open tag is `v0.190.0` (commit dated 2026-06-23), licensed GNU AGPL v3. — [daytona v0.190.0 LICENSE](https://github.com/daytonaio/daytona/blob/v0.190.0/LICENSE)
- Secondary sources say Daytona cited "the risk of AI-assisted vulnerability discovery in open repositories". — [bex.co blog (secondary, search excerpt)](https://bex.co/blog/2026/09/12/daytona-closed-source-agent-sandbox-oss-risk)
- Community fork: "Nightona … Open-source continuation of Daytona … Community fork of the last AGPL-3.0 release (v0.190.0)". — [GitHub nightona-co/nightona (search result)](https://github.com/nightona-co/nightona)
- Self-hosting: v0.190.0 ships `docker/docker-compose.yaml`, with services api, proxy, runner, ssh-gateway, dex (OIDC), Postgres, Redis, registry, MinIO, Jaeger and others. Its README warns: "This setup is still in development and is **not safe to use in production**". A `scripts/setup-domain-oss-deployment.sh` (AGPL-3.0, "Automated deployment of Daytona OSS behind a custom domain with Caddy + TLS") also exists. — [daytona v0.190.0 docker/README.md](https://github.com/daytonaio/daytona/blob/v0.190.0/docker/README.md)
- The managed service continues: PyPI `daytona` 0.220.0 was uploaded 2026-09-29. — [PyPI daytona JSON](https://pypi.org/pypi/daytona/json)
- Bring Your Own Compute: Daytona's hosted control plane can use customer "runner machines" in "custom regions", and "custom regions have no limits applied for concurrent resource usage". — [Daytona docs @v0.190.0: bring-your-own-compute.mdx](https://github.com/daytonaio/daytona/blob/v0.190.0/apps/docs/src/content/docs/en/bring-your-own-compute.mdx)

**API keys and organizations** (docs at v0.190.0; the live URLs are www.daytona.io/docs/en/…, which could not be fetched)
- "Daytona API keys authenticate requests to the Daytona API … to access and manage resources in your organization." "API keys support optional expiration and can be revoked at any time. After creation, you can only retrieve a masked key value when listing keys." On deletion: "The key is revoked immediately and cannot be recovered." — [api-keys.mdx @v0.190.0](https://github.com/daytonaio/daytona/blob/v0.190.0/apps/docs/src/content/docs/en/api-keys.mdx)
- Scopes:
  - sandboxes: `write:sandboxes`, `delete:sandboxes`;
  - snapshots: `write:snapshots`, `delete:snapshots`;
  - registries: `write:registries`, `delete:registries`;
  - volumes: `read:volumes`, `write:volumes`, `delete:volumes`;
  - audit: `read:audit_logs`;
  - regions: `write:regions`, `delete:regions`;
  - runners: `read:runners`, `write:runners`, `delete:runners`.

  Organization admins can delete a key for a specific user. — [api-keys.mdx @v0.190.0](https://github.com/daytonaio/daytona/blob/v0.190.0/apps/docs/src/content/docs/en/api-keys.mdx)
- "Every Daytona user starts with a personal organization". Personal orgs are "Single user only" and have "Quota Scope: Per user". Collaborative orgs have Owners and Members, with "Roles with granular resource-based assignments". "Each organization has its own sandboxes, API keys, and resource quotas." — [organizations.mdx @v0.190.0](https://github.com/daytonaio/daytona/blob/v0.190.0/apps/docs/src/content/docs/en/organizations.mdx)

**Limits, tiers and rate limits**

Tier resources and requirements:

| Tier | vCPU / RAM / Storage | Requirement |
| --- | --- | --- |
| Tier 1 | 10 / 10GiB / 30GiB | Email verified |
| Tier 2 | 100 / 200GiB / 300GiB | Credit card linked, $25 top-up |
| Tier 3 | 250 / 500GiB / 2000GiB | $500 top-up |
| Tier 4 | 500 / 1000GiB / 5000GiB | $2000 top-up every 30 days |

Rate limits per minute:

| Tier | General requests | Sandbox creation |
| --- | --- | --- |
| Tier 1 | 10,000 | 300 |
| Tier 4 | 50,000 | 600 |

- The same page gives Tier 1 memory as 20 GiB in a second table, an internal inconsistency.
- Stopped sandboxes still use storage quota. Archived sandboxes have "no quota impact". Rate-limit errors return HTTP 429 with `X-RateLimit-*` headers.

— [limits.mdx @v0.190.0](https://github.com/daytonaio/daytona/blob/v0.190.0/apps/docs/src/content/docs/en/limits.mdx)

- Per-sandbox defaults: "1 vCPU, 1GB RAM, and 3GiB disk", with a per-org per-sandbox maximum of "4 vCPUs, 8GB RAM, and 10GB disk" (GPU sandboxes are larger). — [sandboxes.mdx @v0.190.0](https://github.com/daytonaio/daytona/blob/v0.190.0/apps/docs/src/content/docs/en/sandboxes.mdx)

**Lifecycle**
- "If the parameter is not set, the default interval of 15 minutes will be used". `0` disables auto-stop.
- "Merely having a script or background task running is not sufficient to keep the sandbox alive." What resets the timer: lifecycle updates, preview requests, SSH, and Toolbox API requests.
- "Ephemeral sandboxes are automatically deleted once they are stopped" (`ephemeral=True` or `autoDeleteInterval: 0`).

— [sandboxes.mdx @v0.190.0](https://github.com/daytonaio/daytona/blob/v0.190.0/apps/docs/src/content/docs/en/sandboxes.mdx)

**Network egress**
- "Tier 1 & Tier 2: Network access is restricted and cannot be overridden at the sandbox level." "Tier 3 & Tier 4: Full internet access is available by default, with the ability to configure custom network settings." — [network-limits.mdx @v0.190.0](https://github.com/daytonaio/daytona/blob/v0.190.0/apps/docs/src/content/docs/en/network-limits.mdx)
- `networkAllowList` is "IPv4 only: hostnames, domains, and IPv6 are not supported", with "Max 10 entries". "If both `networkBlockAll` and `networkAllowList` are specified, `networkBlockAll` takes precedence". Tiers 3 and 4 can update rules on a running sandbox. — [network-limits.mdx @v0.190.0](https://github.com/daytonaio/daytona/blob/v0.190.0/apps/docs/src/content/docs/en/network-limits.mdx)
- The "Essential services" available on all tiers include:
  - code and packages: `github.com`, `*.githubusercontent.com`, PyPI, npm, `docker.io`;
  - storage and hosting: S3 regional endpoints, `storage.googleapis.com`, `r2.cloudflarestorage.com`, `*.vercel.app`, `*.herokuapp.com`, `*.supabase.co`, `*.convex.site`;
  - AI APIs: `*.anthropic.com`, `openai.com`, `openrouter.ai`.

  — [network-limits.mdx @v0.190.0](https://github.com/daytonaio/daytona/blob/v0.190.0/apps/docs/src/content/docs/en/network-limits.mdx)
- The same page cautions: "Enabling unrestricted network access may pose security risks when executing untrusted code." — [network-limits.mdx @v0.190.0](https://github.com/daytonaio/daytona/blob/v0.190.0/apps/docs/src/content/docs/en/network-limits.mdx)

**Isolation**
- The security exhibit says isolation uses "container and/or microVM technology … dedicated namespaces per sandbox, network segmentation preventing lateral movement between sandboxes, resource quotas".
- It continues: "Daytona uses Sysbox as its container runtime to provide VM-level isolation without hardware virtualization overhead … root user inside a sandbox maps to a fully unprivileged user on the host."
- Ephemeral sandboxes revoke "any session-scoped credentials or tokens" on termination.

— [security-exhibit.mdx @v0.190.0](https://github.com/daytonaio/daytona/blob/v0.190.0/apps/docs/src/content/docs/en/security-exhibit.mdx)

- This conflicts with "Each sandbox runs in isolation, giving it a dedicated kernel" in [sandboxes.mdx @v0.190.0](https://github.com/daytonaio/daytona/blob/v0.190.0/apps/docs/src/content/docs/en/sandboxes.mdx). Sysbox containers share the host kernel.

**Credentials inside sandboxes**
- Daytona's security advisory (search excerpt):
  - On 2026-04-09 a researcher reported that "the API credential is passed into a sandbox process and held in memory".
  - Because "the default snapshot ships with passwordless sudo, anyone with shell access on the sandbox could read that credential out of memory and impersonate the account".
  - That gave access "to the rest of the org's sandboxes".
  - It was patched the same day: "The Authorization header is now stripped at the proxy layer before the request ever reaches the sandbox".

  — [Daytona Security Advisory: API Credential Exposure in Sandboxes (search excerpt)](https://www.daytona.io/dotfiles/updates/security-advisory-api-credential-exposure-in-sandboxes)
- Daytona Secrets (post-v0.190.0; search excerpt): "Secrets are organization-scoped, encrypted credentials that Daytona injects into a sandbox's outbound HTTPS traffic without ever placing the plaintext inside the sandbox … the sandbox holds an opaque placeholder token. An outbound proxy replaces the placeholder with the real value … only when the request goes to a host you have allowed." — [Daytona docs: Secrets (search excerpt)](https://www.daytona.io/docs/en/secrets/)
- A GitHub issue opened 2026-08-12 says substitution covers "HTTPS request headers only (`Authorization`, `X-Api-Key`, …)". The SDK accepts a `secrets` map from environment variable names to pre-created org Secret names. — [omnigent issue #4675](https://github.com/omnigent-ai/omnigent/issues/4675)

**Pricing** (no primary page fetched)
- Secondary sources say:
  - $0.0504 per vCPU-hour, $0.0162 per GiB-RAM-hour and $0.000108 per GiB-storage-hour, billed per second;
  - "$200 in free compute credit on signup".

  — [Northflank AI sandbox pricing (secondary)](https://northflank.com/blog/ai-sandbox-pricing); [bex.co pricing comparison 2026-09-09 (secondary)](https://bex.co/blog/2026/09/09/e2b-daytona-modal-sandbox-pricing-self-hosted)
- Billing docs describe a prepaid wallet with auto top-up and a 48-hour charge settlement window. — [billing.mdx @v0.190.0](https://github.com/daytonaio/daytona/blob/v0.190.0/apps/docs/src/content/docs/en/billing.mdx)

**Terms of service**
- The search excerpt of Daytona's acceptable use policy lists malware, vulnerability probing, privacy violations and unlawful activity. No explicit crypto-mining clause was found. — [Daytona Terms of Service (search excerpt only)](https://www.daytona.io/terms-of-service)

**Alternatives**
- E2B runtime: "Firecracker microVMs that resume from a snapshot, run untrusted agent code". Apache-2.0. Self-hosting is via Terraform on GCP, Kubernetes, or a single-machine "E2B Embed" (which is "an evaluation package, not a production deployment pattern"). — [GitHub e2b-dev/infra](https://github.com/e2b-dev/infra)
- E2B network (search excerpt):
  - Internet is on by default; `allow_internet_access=False` turns it off.
  - `network.allowOut` and `denyOut` accept domains, IPs and CIDRs.
  - "The network.egressProxy option tunnels every outbound TCP connection through a SOCKS5 proxy, applied on the host … so code inside the sandbox cannot see or route around it."

  — [E2B docs: Internet access (search excerpt)](https://e2b.dev/docs/network/internet-access)
- E2B pricing (search excerpts; the sources conflict):
  - Hobby is free with $100 one-time credit and 1-hour max sessions.
  - Pro is $150/month with 24-hour sessions.
  - Hobby concurrency is given as both 5 and 20 sandboxes.

  — [E2B docs: Billing (search excerpt)](https://e2b.dev/docs/billing); [Beam blog (secondary)](https://www.beam.cloud/blog/e2b-pricing-explained)
- Modal Sandboxes (from source code, fetched 2026-10-01):
  - `Sandbox.create(timeout=300, idle_timeout=None, block_network=False, outbound_cidr_allowlist=None, outbound_domain_allowlist=None, inbound_cidr_allowlist=None, …)`.
  - `timeout` is the "Maximum lifetime of the sandbox in seconds".
  - An experimental `OutboundPolicy` injects secret-backed headers. Its docstring says: "Secret values never enter the Sandbox: they are resolved and injected into matching requests outside the container."

  — [modal-client py/modal/sandbox.py](https://github.com/modal-labs/modal-client/blob/main/py/modal/sandbox.py); [modal-client py/modal/_outbound_policy.py](https://github.com/modal-labs/modal-client/blob/main/py/modal/_outbound_policy.py)
- Runloop (search excerpt):
  - Plans: Basic is free with usage-based compute; Pro is $250/month; Enterprise is custom.
  - $0.108 per CPU-hour and $0.0252 per GB-hour; "$50 in credits".
  - VM-based devboxes with network policies.

  — [Runloop pricing (search excerpt)](https://runloop.ai/pricing)

### Inferences
**BYO Daytona keys: what to ask users for.**
- Tell users to create a dedicated key in their personal org.
- Give it only the scopes deep_reasoner needs: `write:sandboxes`, `delete:sandboxes`, and `write:snapshots` (plus `delete:snapshots`) only if the framework builds its python:3.12 snapshot in the user's org.
- Set an expiry date on the key.
- Usage then bills to the user's wallet. Their tier sets their quota, and their egress policy is tier-forced.

**Free-tier users are both constrained and exposed.** Tier 1 (email only) users cannot set custom allowlists, and cannot override the restricted egress. Yet the essential-services list still lets sandbox code reach attacker-controllable hosts: GitHub gists, `*.vercel.app`, `*.herokuapp.com`, S3 buckets and `*.supabase.co`. Tier-forced "restricted" egress therefore does not prevent prompt-injected exfiltration of anything placed inside the sandbox. `networkBlockAll` is the strongest setting; whether it also blocks essential services was not confirmed.

**Keep every key out of the Daytona sandbox:**
- the user's Daytona key;
- Anthropic and OpenRouter keys;
- the relay's auth token, if it grants more than that one sandbox.

The model-written code that runs there is untrusted. The April 2026 advisory shows that even the platform's own credential handling was readable with sudo. If sandbox code must call an LLM, use Daytona Secrets, or route through a host-side proxy.

**Self-hosting Daytona is now riskier.**
- The control plane is closed.
- The last AGPL release is unmaintained.
- Its docker-compose setup is labelled not production-safe.
- AGPL §13 obliges offering source to network users if UW modifies it.

E2B's Apache-2.0 Firecracker runtime, or a gVisor/Firecracker container per user run by UW, are more sustainable self-hosted options. Note that Anthropic's own hosting cookbook targets Docker, Modal and Kubernetes.

**Rate limits are per organization.** With BYO keys, each user's own org carries their own sandbox-creation limit (300/minute at Tier 1), so the service's aggregate is not capped by one org. With a single UW org, all users share one tier's quota, egress policy and bill.

### Gaps
- I could not fetch the live Daytona docs (pricing, ToS, Secrets, live limits). Post-June-2026 changes to tiers, limits or key scopes are unverified. The figures above are from the v0.190.0 docs dated 2026-06-23.
- Daytona's pricing figures come only from secondary sources.
- Whether Daytona's ToS permits a third-party service to hold and use a customer's API key, or bans crypto-mining, was not confirmed. Only a search excerpt of the acceptable use policy was seen.
- Whether `networkBlockAll` also blocks the essential-services list was not stated in the docs read.
- Daytona Secrets limits, pricing and launch date were not confirmed.
- E2B's current Hobby concurrency limit is reported inconsistently (5 vs 20).
- Modal's isolation technology and pricing were not fetched; its docs site was blocked.

## 5. OpenRouter: BYO user keys, the OAuth PKCE flow, and key provisioning and limits

### Takeaway
OpenRouter supports an OAuth PKCE flow that mints a user-controlled OpenRouter API key for your app:
1. The app redirects the user to `https://openrouter.ai/auth` with `callback_url`, `code_challenge` and `code_challenge_method=S256`.
2. The app exchanges the returned code at `POST https://openrouter.ai/api/v1/auth/keys`.

There is no refresh-token model; the returned key is the persistent credential. OpenRouter also has management (provisioning) keys that can create per-user keys with credit limits that reset daily, weekly or monthly. With such keys, all spend draws from the provisioning account's balance, so UW would pay.

All OpenRouter facts here come from search-result excerpts of openrouter.ai pages; the site itself was blocked.

### Cited Findings
- "OpenRouter's Proof Key for Code Exchange (PKCE) allows users to connect to OpenRouter in one click." Send the user to `/auth` with `callback_url`, `code_challenge` and `code_challenge_method=S256`, then call `https://openrouter.ai/api/v1/auth/keys` with the `code`, `code_verifier` and `code_challenge_method` "to exchange the code for a user-controlled API key". For S256, `code_challenge` is the base64 of the SHA-256 of `code_verifier`. — [OpenRouter docs: OAuth PKCE (search excerpt)](https://openrouter.ai/docs/guides/overview/auth/oauth); [OpenRouter API: Exchange authorization code for API key (search excerpt)](https://openrouter.ai/docs/api/api-reference/oauth/exchange-authorization-code-for-api-key)
- Third-party implementations describe the result as a pooled or user API key used as the Bearer credential, with no access/refresh-token pair. — [NousResearch hermes-agent PR #104236 (search result)](https://github.com/NousResearch/hermes-agent/pull/104236)
- Management keys are "used only for key management operations (create, list, delete keys) and cannot be used for model completion requests". Keys can be created with "an optional spending limit in USD" and a `limit_reset` of daily, weekly or monthly (midnight UTC). "All keys draw from the same account credit balance." — [OpenRouter docs: Management API keys (search excerpt)](https://openrouter.ai/docs/guides/overview/auth/management-api-keys); [OpenRouter Help: one API key per user with its own spending limit (search excerpt)](https://openrouter.zendesk.com/hc/en-us/articles/51680687417499-Can-I-create-one-API-key-per-user-with-its-own-spending-limit-Management-API-keys)
- OpenRouter documents credit and rate limits with HTTP 402 and 429 errors. — [OpenRouter docs: Limits (search result)](https://openrouter.ai/docs/api_reference/limits)
- OpenRouter's own "BYOK" (users attach upstream provider keys to OpenRouter) is free up to $25,000 per month of list-price inference on pay-as-you-go as of 2026-07-14, then a 5% fee. — [OpenRouter docs: BYOK (search excerpt)](https://openrouter.ai/docs/use-cases/byok); [Glamdring Research, Sept 2026 (secondary)](https://www.glamdringresearch.com/post/openrouter-pricing)

### Inferences
**For the UW beta, PKCE is the best BYO path for OpenRouter.**
- The user never copies a raw key; the key is created in the user's own OpenRouter account and billed to them.
- The user can revoke it from their OpenRouter dashboard.
- The beta should store the returned key encrypted (see section 6). It should suggest users set a credit limit on that key, if the PKCE flow or dashboard allows it (not confirmed).

**Provisioning keys suit a UW-funded quota model, not BYO.** UW would create per-user keys with monthly caps from a UW-funded account. That is a clean way to give free-tier users a hard dollar ceiling, if UW chooses to fund chat backbones.

**Localhost callbacks.** The localhost/self-hosted option can use the same PKCE flow with a localhost `callback_url`, if OpenRouter allows it. Third-party CLI agents appear to do this, but it was not confirmed from OpenRouter docs.

### Gaps
- I could not open the OpenRouter docs directly, so exact parameter names, whether keys minted via PKCE can carry a limit at creation, localhost callback rules, and app attribution headers are unverified.
- OpenRouter's terms on apps holding user keys were not reviewed.

## 6. Best practices for storing user-supplied API keys in a web app, and the main abuse and cost risks of a free university beta

### Takeaway
Treat user keys as high-value secrets:
- Encrypt them at rest with envelope encryption: a per-record data key wrapped by a KMS-held key-encryption key, using AES-256-GCM. Never store wrapping keys next to the data.
- Decrypt them only in the component that calls the provider, ideally a credential-injecting egress proxy outside every sandbox.
- Never log them. Mask them in the UI after entry.
- Audit every use.
- Let users delete or replace keys, and encourage provider-side scoping, expiry and spend limits.

The main beta risks:
- Prompt injection or malicious model-written code reading keys from sandbox environments, memory or files, then exfiltrating them via allowed egress.
- Compute abuse ("freejacking" or crypto-mining) in sandboxes.
- Runaway token spend. With BYO keys, this is borne by users but caused by the service's agent loop.

### Cited Findings

**OWASP on secrets**
- Access control: "the Least Privilege principle should be applied" to who and what can read secrets. — [OWASP Secrets Management Cheat Sheet §2.3](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html) (source: [GitHub OWASP/CheatSheetSeries](https://github.com/OWASP/CheatSheetSeries/blob/master/cheatsheets/Secrets_Management_Cheat_Sheet.md), file last committed 2026-10-01)
- Auditing: audit "Who requested a secret and for what system and role … When the secret was used and by whom/what … When the secret was updated", and keep audit logs tamper-resistant. — [OWASP Secrets Management §2.6](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- Lifecycle: secrets go through creation, rotation, revocation and expiration. "You should create secrets to expire after a defined time where possible." Revoke secrets "when no longer required or potentially compromised". — [OWASP Secrets Management §2.7](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- Encryption: "preferably select an algorithm that provides encryption and confidentiality at the same time, such as AES-256 using GCM … or … ChaCha20 and Poly1305". "You should not store keys next to the secrets they encrypt, except if those keys are encrypted themselves (see envelope encryption)". — [OWASP Secrets Management §7.1, §7.3](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- Envelope encryption with a provider KMS: "use your key or the customer main key from the provider to encrypt the data key of the secrets management solution. The data key, in turn, encrypts the secret." — [OWASP Secrets Management §4.2.2](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- On key-encryption keys: "encrypt the keys using Key Encryption Keys (KEKs) prior to the export of the key material". — [OWASP Key Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Key_Management_Cheat_Sheet.html)
- Environment variables: they "are generally accessible to all processes and may be included in logs or system dumps. Using environment variables is therefore not recommended unless the other methods are not possible." — [OWASP Secrets Management §5.1](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- Secrets should "Be revocable (including the logging of attempt to use a revoked secret)" and "Never be logged (must implement either an encryption or masking approach in place to avoid logging plaintext secrets)". — [OWASP Secrets Management §8](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)

**Anthropic on keeping keys from agents**
- The proxy pattern: "the agent never sees the actual credentials … Credentials are stored in one secure location rather than distributed to each agent". Use `ANTHROPIC_BASE_URL` for model calls, and custom tools or a TLS-terminating proxy for other services. — [Anthropic: Securely deploying AI agents](https://code.claude.com/docs/en/agent-sdk/secure-deployment)
- Anthropic's list of credential files to keep out of agent mounts includes `.env`, `~/.aws/credentials`, `~/.git-credentials`, `.npmrc`, `.pypirc` and `*.pem`. — [Anthropic: Securely deploying AI agents](https://code.claude.com/docs/en/agent-sdk/secure-deployment)
- Observability exports exclude prompt text and tool inputs by default. — [Hosting the Agent SDK](https://code.claude.com/docs/en/agent-sdk/hosting)

**Provider-side controls a BYO user can use**
- Daytona keys: scopes, expiry, immediate revocation, and a masked value after creation. — [Daytona api-keys.mdx @v0.190.0](https://github.com/daytonaio/daytona/blob/v0.190.0/apps/docs/src/content/docs/en/api-keys.mdx)
- OpenRouter keys: per-key USD limits with daily, weekly or monthly reset (search excerpt). — [OpenRouter Management API keys](https://openrouter.ai/docs/guides/overview/auth/management-api-keys)

**Real incidents of credentials and exfiltration from sandboxes**
- Daytona's April 2026 advisory: an in-sandbox API credential was readable via passwordless sudo, and a stolen key gave access "to the rest of the org's sandboxes". — [Daytona Security Advisory (search excerpt)](https://www.daytona.io/dotfiles/updates/security-advisory-api-credential-exposure-in-sandboxes)
- Anthropic: "Without network isolation, a compromised agent could exfiltrate sensitive files like SSH keys". — [Anthropic Engineering: Claude Code sandboxing](https://www.anthropic.com/engineering/claude-code-sandboxing)
- Anthropic's secure deployment page cites Simon Willison's "lethal trifecta" (private data, untrusted content and external communication) as further reading. — [Anthropic: Securely deploying AI agents](https://code.claude.com/docs/en/agent-sdk/secure-deployment)

**Crypto-mining and free-tier abuse**
- "PurpleUrchin": attackers used over a million free GitHub Actions runs for automated crypto mining, continuously creating free accounts. — [The New Stack (search result)](https://thenewstack.io/purpleurchin-github-actions-hijacked-for-crypto-mining/); [Sysdig TRT (search result)](https://www.sysdig.com/blog/massive-cryptomining-operation-github-actions); [The Record (search result)](https://therecord.media/crypto-mining-gangs-are-running-amok-on-free-cloud-computing-platforms)
- A sandbox vendor's blog (secondary) gives the signature as sustained high CPU, long-lived sandboxes, no interactive session and near-zero inbound traffic. Its mitigations: "metering accurately, capping hard, requiring verification before sustained compute, and making egress default-deny". — [PandaStack blog (secondary)](https://www.pandastack.ai/blog/preventing-cryptomining-abuse-in-code-sandboxes/)

**Session limits**
- Anthropic: agent sessions have "No top-level session timeout" (bound them with `max_turns`). Spend caps via `--max-budget-usd` are client-side estimates. — [Hosting the Agent SDK](https://code.claude.com/docs/en/agent-sdk/hosting); [Python SDK reference](https://code.claude.com/docs/en/agent-sdk/python)

### Inferences
**Recommended design for deep_reasoner's hosted beta:**

1. Encrypt keys at rest. Store each user's keys (Anthropic, Daytona, OpenRouter) in Postgres as AES-256-GCM ciphertext under a per-user or per-record data key. Wrap that data key with a KMS key: UW cloud KMS, or HashiCorp Vault Transit in an on-prem deployment. Never place the KMS key-encryption key on the database host.
2. Restrict decryption. Decrypt only inside a small "credential broker" or egress proxy process. Do not decrypt in the web tier's request logs, the Claude Code subprocess environment, or any REPL backend.
3. Inject keys at the proxy. Point Claude Code at a per-user `ANTHROPIC_BASE_URL` on a loopback proxy that adds `x-api-key`. Route OpenRouter chat calls through the same broker. Make Daytona API calls from the broker or orchestrator, never from inside sandboxes.
4. Keep keys out of sandboxes. Never pass keys into Daytona sandboxes, the websocket relay, or snapshots. Where sandbox code legitimately needs an LLM, use Daytona Secrets (placeholder plus proxy) or a host-side call.
5. Keep keys out of logs and the UI.
   - Redact `sk-ant-…`, `sk-or-…` and Daytona key patterns in logs, tracebacks, OTEL exports and stream-json transcripts shown in the UI.
   - Show only the last four characters after entry.
   - Never echo keys back to the browser.
6. Give users control.
   - "Delete key" and "Replace key" actions that purge ciphertext immediately.
   - A per-key audit log ("used at …, for session …").
   - An encouragement to create dedicated, scoped, expiring keys, with spend limits where the provider supports them.
7. Bound each run.
   - Server-side caps per user and session: max turns, max wall clock, max sub-agent fan-out, max concurrent sandboxes, max sandbox lifetime.
   - Daytona `ephemeral=True` with a short `auto_stop_interval`.
   - `networkBlockAll` where tasks do not need internet.
   - Kill sandboxes with sustained high CPU and no interaction.

**Abuse is cheaper to UW with BYO, but not free.** With BYO Daytona and LLM keys, compute and token costs land on the abuser's own accounts, which removes most of UW's cost risk from mining. The remaining UW exposure is:
- the shared web, orchestrator and Claude Code subprocess host (CPU/RAM per session; Anthropic suggests about 1 GiB per agent);
- reputational and terms risk if UW infrastructure is used to proxy abusive traffic;
- account-level enforcement by providers against UW's IPs.

Requiring UW NetID login (SSO) before key entry is a cheap verification gate.

**Leaked keys are now the user's financial loss.** A key leaked through the beta lets an attacker spend the user's money. That makes "keys never enter model-reachable environments" the single most important control. The local in-process REPL backend must be disabled in the hosted multi-user deployment.

### Gaps
- No primary source was found on cost-abuse rates specific to university-hosted LLM or agent services.
- I did not review UW-specific policies on storing third-party credentials, data classification or acceptable use; the institution's own security office would need to confirm.
- The OWASP guidance is generic. No authoritative standard for "BYO LLM key" web apps specifically was found.
