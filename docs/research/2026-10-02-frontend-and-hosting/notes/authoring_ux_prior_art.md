# Authoring, organizing, testing and reusing agent behaviour: product and UX prior art (as of 2026-10-01)

Source-access note for the report writer: the egress proxy in this research session blocked direct fetches of most primary doc sites (platform.openai.com, openai.com, developers.openai.com, docs.langchain.com, changelog.langchain.com, langfuse.com, docs.dify.ai, docs.langflow.org, docs.openwebui.com, docs.openhands.dev, learn.microsoft.com, arxiv.org). Only the Anthropic Agent Skills overview (platform.claude.com) was read in full. Everything else comes from web-search result snippets attributed to the URLs cited, so the wording is a search-engine paraphrase of each page, not a verbatim quote. Claims that rest only on secondary sources (blogs, aggregators) are marked "(secondary)".

## Q1. How do products let users define agent behaviour without code, and what works for non-experts (forms vs. visual graphs vs. "describe and we generate")?

### Takeaway
By 2025–2026 nearly every vendor converged on the same three-step loop: describe in natural language → get a generated draft in a structured form → test in a live preview pane before saving. Visual graph canvases are moving away from "agent behaviour" and toward deterministic automation. OpenAI is retiring its graph-based Agent Builder (shutdown 30 Nov 2026), and Microsoft's newer Copilot Studio Build tab says plainly that it replaces explicit topic flows with natural-language description.

### Cited Findings
**OpenAI (GPTs, Agent Builder/AgentKit, Workspace Agents)**
- The GPT builder has two tabs. "Create" builds a GPT by chatting with a builder. "Configure" has explicit fields for instructions, conversation starters, knowledge-file uploads and Actions. Users can edit the instructions the builder generated. — [Zapier](https://zapier.com/blog/custom-chatgpt/) (secondary); [OpenAI Academy](https://academy.openai.com/public/clubs/work-users-ynjqu/resources/custom-gpts)
- Agent Builder (part of AgentKit, launched at DevDay, Oct 2025) is a drag-and-drop canvas of nodes and edges. It offers templates or a blank canvas, preview runs that show data trace by trace, inline eval configuration (an "Evaluate" tab that runs trace graders without leaving the canvas) and versioning, where each publish creates a snapshot that can be pinned in ChatKit or exported as SDK code. — [OpenAI, Introducing AgentKit](https://openai.com/index/introducing-agentkit/) (could not be fetched); details via [Superprompt](https://superprompt.com/blog/openai-agentkit-agent-builder-guide) and [cosupport.ai](https://cosupport.ai/articles/openai-agent-builder-agentkit-architecture) (secondary)
- OpenAI announced Agent Builder's deprecation on 3 June 2026, with shutdown on 30 Nov 2026. Recommended paths: the Agents SDK for workflows that should stay as code, and Workspace Agents in ChatGPT for natural-language team workflows. TypeScript/Python code export "does not convert the workflow graph or guarantee identical behavior". — [The Rundown](https://www.therundown.ai/tools/agent-builder), [AgenticWire](https://www.agenticwire.news/article/openai-agent-builder-migration-sdk-workspace) (secondary). One headline says the Evals platform and reusable Prompts are also deprecated for November 2026 — [TheRouter.ai](https://therouter.ai/news/openai-evals-agent-builder-prompts-deprecation-november-2026/) (secondary). The primary [OpenAI deprecations page](https://developers.openai.com/api/docs/deprecations) could not be fetched.
- ChatGPT Workspace Agents were announced on 22 Apr 2026 as a research preview for Business, Enterprise, Edu and Teachers plans. Teams define agents in the ChatGPT UI or start from templates, share them in the workspace, and use them in ChatGPT or Slack. They are Codex-powered and keep running in the cloud. OpenAI says GPTs will be convertible to Workspace Agents later. — [TechWyse](https://www.techwyse.com/news/ai-search/openai-chatgpt-workspace-agents-launch-2026), [UC Today](https://www.uctoday.com/productivity-automation/openai-workspace-agents-chatgpt-enterprise-workflows/) (secondary)

**Anthropic (Projects, Agent Skills, Claude Code subagents)**
- A Project holds instructions applied to every chat in it, plus a knowledge base. Context is not shared across chats unless it is added to project knowledge. — [Claude Help Center: What are projects?](https://support.claude.com/en/articles/9517075-what-are-projects)
- Agent Skills are directories with a `SKILL.md`. YAML frontmatter `name` (≤64 chars, lowercase letters, numbers and hyphens) and `description` (≤1024 chars) are required. The `description` "must say both what the Skill does and when to use it". Loading is progressive: metadata (~100 tokens per skill) always; the SKILL.md body (<5k tokens) when triggered; bundled files and scripts only when needed. — [Anthropic Agent Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) (fetched)
- Skills are authored differently on each surface. In claude.ai you upload a zip in Settings > Features. Via the API you use `/v1/skills`. In Claude Code you place files in `~/.claude/skills/` or `.claude/skills/`. — [Anthropic Agent Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- A built-in "skill-creator" skill writes skills through conversation. Claude asks about your workflow, you upload example materials, and it generates the folder and SKILL.md. Anthropic says to expect "about 15-30 minutes to build and test your first working skill". — [Claude tutorial: create a skill through conversation](https://claude.com/resources/tutorials/how-to-create-a-skill-with-claude-through-conversation); [Anthropic guide PDF](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf)
- Claude Code's `/agents` command opens a manager. Creating a subagent asks for scope (project or user), then offers "Generate with Claude": describe the subagent and Claude drafts its name, description and system prompt. The user then picks the allowed tools, the model and a color, and the result is saved as a Markdown file with YAML frontmatter. — [Anthropic blog: subagents in Claude Code](https://claude.com/blog/subagents-in-claude-code); [Claude Academy](https://academy.claude.com/courses/introduction-to-subagents/creating-a-subagent)

**Google Gemini Gems**
- A Gem has a name, instructions and up to 10 optional knowledge files. The builder is a split view: the form is on the left and a live Preview pane on the right. Previewing does not save the Gem. A "magic wand" button rewrites and expands draft instructions. — [Google blog: 5 tips for Gems](https://blog.google/products-and-platforms/products/gemini/google-gems-tips/); [Gemini Help: Tips for creating Gems](https://support.google.com/gemini/answer/15235603?hl=en); [Zapier](https://zapier.com/blog/gemini-gems/) (secondary)
- Gems are shared like Drive files, with Viewer or Editor roles, and the sharer chooses whether attached files are shared too. — [Zapier](https://zapier.com/blog/gemini-gems/) (secondary)

**Microsoft Copilot Studio**
- A "Describe" tab supports conversational authoring: as you answer the builder's questions, the agent's name, description, instructions and starter prompts update. — [MS release plan: create agents using natural language](https://learn.microsoft.com/en-us/power-platform/release-plan/2024wave1/microsoft-copilot-studio/create-agents-using-everyday-natural-language)
- The newer Build tab (in the "GitHub Copilot Harness" experience) puts authoring in one place: "instead of designing explicit topic flows and branching logic, you describe your agent in natural language and connect the resources it needs". — [MS Learn: Build an agent](https://learn.microsoft.com/en-us/microsoft-copilot-studio/agents-experience/build-overview) (search snippet)

**Open-source and low-code builders (Dify, Langflow, Flowise, n8n, CrewAI)**
- n8n: the AI Agent node connects a chat model and tools. An "AI Agent Tool" node lets one agent call others as tools on the same canvas, which supports supervisor and sub-agent hierarchies. — [n8n docs: AI Agent](https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.agent); [VKTR](https://www.vktr.com/ai-news/n8n-launches-ai-agent-tool-to-simplify-multi-agent-orchestration/) (secondary)
- n8n launched an AI Workflow Builder (beta) on 13 Oct 2025 that turns prompts into draft workflows you then refine in the editor. At launch it was Cloud-only, not self-hosted, and metered at 1 credit per prompt (Trial 20 / Starter 50 / Pro 150 per month). — [DEV Community](https://dev.to/alifar/n8n-ai-workflow-builder-brings-natural-language-automation-to-cloud-workflows-2ah4) (secondary)
- Langflow 1.9 (13 Apr 2026) added "Langflow Assistant", a graph-aware co-pilot that generates components from natural language. Release notes say 1.10 extended it to building whole flows. — [Langflow 1.9 blog](https://www.langflow.org/blog/langflow-1-9/); [Langflow Assistant docs](https://docs.langflow.org/langflow-assistant)
- CrewAI Crew Studio is conversational. You describe the problem, the "Crew Assistant" asks clarifying questions, then generates agents, tasks, tools and inputs for review. You can then export code, deploy to CrewAI AMP, or keep refining. — [CrewAI docs: Enable Crew Studio](https://docs.crewai.com/en/enterprise/guides/enable-crew-studio)
- Flowise and Dify remain canvas-first: Agentflow V2 in Flowise, workflow orchestration in Dify. Both ship template galleries (see Q5). — [DeepWiki: Flowise marketplace](https://deepwiki.com/FlowiseAI/Flowise/11.1-marketplace-and-template-flows); [Dify blog](https://dify.ai/blog/dify-creator-center-template-marketplace-share-your-workflows)

**Evidence on non-experts**
- In "Why Johnny Can't Prompt" (CHI 2023), non-AI-experts explored prompt designs "opportunistically, not systematically". Expectations carried over from instructing humans, and a tendency to overgeneralize from a single success or failure, got in the way. — [ACM DL](https://dl.acm.org/doi/pdf/10.1145/3544548.3581388)
- In "Why Johnny Can't Use Agents" (arXiv 2509.14528, 2025; ACM DOI 10.1145/3786335.3813140), 31 participants used commercial agents. SUS scores were relatively high (69.8–90.6), but five barriers appeared: capabilities misaligned with mental models, trust presumed without credibility, inflexible collaboration styles, "overwhelming amount of communication overhead", and weak meta-cognition. — [arXiv HTML](https://arxiv.org/html/2509.14528v1); [project page](https://cmu-spuds.github.io/why-johnny-can-t-use-agents/)

### Inferences
- The dominant authoring pattern is hybrid: natural-language "describe" to bootstrap, then a form for precise edits, with preview alongside. GPT Create/Configure, Gems with magic wand and Preview, Copilot Studio Describe/Build, Claude Code `/agents` "Generate with Claude", skill-creator, Crew Studio, n8n and Langflow assistants all follow it. A deep_reasoner panel should offer "Describe → draft namespace/decomposition → edit fields → try it" rather than a blank YAML editor or a node canvas.
- Graph canvases fit deterministic pipelines (n8n, Dify, Flowise). deep_reasoner's behaviour is decided by the model and expressed as Python code, so a canvas would misrepresent it. OpenAI retiring Agent Builder and Microsoft's "instead of topic flows" wording both support skipping a canvas for authoring. Graphs remain useful for viewing runs (Q3).
- Skills' insistence that `description` say "when to use it" maps directly onto decompositions: each one should carry a short "use when…" field, both for the user's mental model and as retrieval metadata.
- The "Johnny" studies suggest non-experts will save one lucky run as a decomposition and generalize from it. The UI should nudge them to test on a few varied tasks before saving (Q2, Q6).

### Gaps
- None of the primary OpenAI or Microsoft doc pages could be fetched, so the Agent Builder deprecation date (3 Jun 2026 announcement, 30 Nov 2026 shutdown) is confirmed only by several consistent secondary outlets.
- Whether n8n's AI Workflow Builder is now available to self-hosted users (it was Cloud-only at launch in Oct 2025) could not be confirmed for Oct 2026.
- No usability studies were found that compare forms, graphs and natural language for non-experts head to head. The preference for hybrid flows is inferred from vendor convergence, not controlled studies.
- Gemini Gems details come mostly from secondary guides plus Google's help page and blog. No Google changelog dates were found.

## Q2. Few-shot and example management: turning runs into reusable examples, versioning, A/B testing and evals (LangSmith, Langfuse, PromptLayer, Humanloop, promptfoo, Anthropic Console)

### Takeaway
The mature pattern is "trace → one click → dataset item / example → versioned → run as an experiment → compare side by side". LangSmith and Langfuse both offer "Add to dataset" and "Open in Playground" from any trace, with immutable versions and movable labels. The weak point in every product is round-trip fidelity for multi-message and tool-call traces.

### Cited Findings
**LangSmith**
- Runs can be added to a dataset by multi-selecting in the Runs table ("Add to Dataset"), from a run's detail page ("Add to → Dataset"), or by multi-selecting threads (whole conversations). Attachments are copied onto the new example. — [LangSmith docs: manage datasets in the UI](https://docs.langchain.com/langsmith/manage-datasets-in-application) (search snippet)
- Datasets can be indexed for dynamic few-shot selection: `client.similar_examples()` returns examples similar to the current input. This requires a KV-store dataset with a defined input schema. — [LangSmith: dynamic few-shot example selection](https://docs.smith.langchain.com/evaluation/how_to_guides/index_datasets_for_dynamic_few_shot_example_selection); [changelog](https://changelog.langchain.com/announcements/few-shot-examples-in-langsmith-datasets) (search snippet)
- Each saved prompt edit is a commit with a hash. Tags are human-readable and movable, so code can point at a tag and pick up a new version without redeploying. The Playground can switch model, tools and output schema and add any message role. Prompt Canvas commits on "Use this version". — [LangSmith: prompt engineering concepts](https://docs.langchain.com/langsmith/prompt-engineering-concepts); [Mirascope](https://mirascope.com/blog/langsmith-prompt-management) (secondary)
- "Open in Playground" on a trace run loads its inputs, messages, tools and model config. Users report two problems: edits from a trace-opened Playground cannot be saved back to an existing Prompt Hub prompt, and edits to multi-message prompts sometimes do not take effect. — [LangChain Forum bug](https://forum.langchain.com/t/bug-cannot-save-edited-prompt-back-to-prompt-hub-after-opening-trace-run-in-playground/3492); [langsmith-sdk #2671](https://github.com/langchain-ai/langsmith-sdk/issues/2671)

**Langfuse**
- From the Observations table you can multi-select, then choose Actions → Add to dataset, creating a new dataset or adding to an existing one, with field mapping. A single observation has "+ Add to dataset". — [Langfuse: Datasets](https://langfuse.com/docs/evaluation/experiments/datasets) (search snippet)
- Dataset item versioning shipped 15 Dec 2025: every add, update, delete or archive creates a timestamped dataset version with item-level diffs. Experiments on a specific dataset version shipped 11 Feb 2026, from UI, API or SDK. — [Langfuse changelog 2025-12-15](https://langfuse.com/changelog/2025-12-15-dataset-versioning); [changelog 2026-02-11](https://langfuse.com/changelog/2026-02-11-versioned-dataset-experiments)
- Langfuse explains why this matters: scores from different dates are only comparable if you know which dataset state each run saw. — [Langfuse: golden dataset evaluation](https://langfuse.com/resources/engineering/golden-dataset-evaluation) (search snippet)
- "Open in Playground" from a generation exists, and tool calling and structured output were added to the Playground in March 2025. Open issues show messages with function calls or ToolMessages sometimes fail to populate. — [Langfuse Playground](https://langfuse.com/docs/prompt-management/features/playground); [changelog 2025-03-28](https://langfuse.com/changelog/2025-03-28-tool-calling-structured-output-playground); [langfuse #3912](https://github.com/langfuse/langfuse/issues/3912); [langfuse-js #930](https://github.com/langfuse/langfuse-js/issues/930)

**PromptLayer**
- A prompt registry separates prompts from code. Release labels such as "prod", "staging" or "beta_users" point at versions. "Dynamic release labels" split traffic by percentage or user segment for A/B tests, for example 20% to a new version, ramped up later. — [PromptLayer: Release Labels](https://docs.promptlayer.com/features/prompt-registry/release-labels); [PromptLayer: A/B Testing](https://docs.promptlayer.com/why-promptlayer/ab-releases)

**Humanloop (cautionary)**
- Humanloop offered prompt versioning, evals and human feedback for customers including Duolingo, Gusto and Vanta. After an Anthropic acqui-hire it shut down on 8 Sept 2025. Customers were notified around July 2025 and told to export prompts, logs and evaluations through the existing APIs. — [Humanloop changelog Aug 2025](https://humanloop.com/docs/changelog/2025/08); [Hacker News](https://news.ycombinator.com/item?id=44592216)

**promptfoo**
- promptfoo is config-first: one `promptfooconfig.yaml` with prompts, providers and test cases with assertions. `promptfoo view` opens a local, color-coded matrix (rows are test cases, columns are prompt and model combinations) showing output, pass/fail, score, latency, tokens and cost, with a filter for failures. — [promptfoo intro](https://www.promptfoo.dev/docs/intro/); [qaskills](https://qaskills.sh/blog/promptfoo-llm-testing-guide) (secondary)

**Anthropic Console**
- The Workbench "Evaluate" tab supports test cases added by hand, imported from CSV, or generated by Claude. All cases run with one click, prompt versions can be compared side by side, and experts can grade responses on a 1–5 scale. — [Anthropic: Evaluate prompts](https://www.anthropic.com/news/evaluate-prompts); [SD Times](https://sdtimes.com/ai/anthropic-adds-prompt-evaluation-feature-to-console/)

### Inferences
- A deep_reasoner run trace already has the decomposition shape (task → think+repl → observation → … → FinalAnswer), so "Save this run as a decomposition" should be the main way decompositions get created. It is the equivalent of LangSmith/Langfuse "Add to dataset", and it avoids the fidelity bugs those tools hit when mapping arbitrary traces onto chat messages.
- Copy a split from the trackers: immutable versions (Langfuse timestamps, LangSmith commit hashes) plus movable labels (LangSmith tags, PromptLayer release labels). A namespace should reference a decomposition by label (e.g., `@current`) so edits don't silently change a pinned experiment, and old runs record exactly which version they used.
- Dynamic few-shot selection by similarity (LangSmith `similar_examples`) is prior art for choosing which decompositions to inject from a larger library. That suggests storing a "use when" description and embedding per decomposition.
- A lightweight "test set" per namespace (3–10 tasks, auto-suggested by the model as in Anthropic's Evaluate tab), shown as a promptfoo-style matrix of tasks × decomposition versions, is a familiar, proven way to answer "did this example help?".
- Humanloop's shutdown (and Langflow and OpenAI's, Q5) argues for keeping decompositions in a plain, exportable format the team owns.

### Gaps
- Could not confirm whether LangSmith or Langfuse can edit a multi-turn example containing code and execution output as a structured transcript (rather than raw JSON input/output fields). Their dataset editors appear to be JSON-field editors, but primary docs could not be fetched.
- Found no product that A/B tests few-shot examples themselves (as opposed to prompts) inside an agent loop. PromptLayer's A/B is at the prompt-version level.
- No public data on how much non-experts use "add trace to dataset".

## Q3. Run and trace visualization for nested multi-agent executions (LangGraph Studio, LangSmith/Langfuse, AgentOps, OpenHands, Claude Code)

### Takeaway
The standard view is an indented tree or waterfall: each node shows input and output, latency, tokens and cost, and parents show the totals of their children. It is often paired with an inferred agent graph and a step-by-step replay, and debuggers add fork-and-edit "time travel". Live views of running sub-agents are newer and buggier, with known problems attributing nested sub-agent activity to the right parent.

### Cited Findings
- **LangSmith:** a trace is a root run plus nested child runs drawn as a waterfall. Indentation shows nesting and bar length shows duration. The trace tree shows total usage, per-parent totals, and token and cost breakdowns per child run. — [LangSmith: cost tracking](https://docs.langchain.com/langsmith/cost-tracking) (search snippet); [theneuralbase](https://theneuralbase.com/langsmith/learn/beginner/the-trace-waterfall-understanding-the-timeline/) (secondary)
- **Langfuse:** a graph view for LangGraph traces shipped 14 Feb 2025. Agent Graphs are now GA and are inferred automatically from observation timing and nesting whenever an observation type other than span, event or generation appears. Typed observations include agent, tool, chain, retriever and more. Late-2025 updates added inline tool-call details and arguments and a unified Trace Log View. — [Langfuse changelog 2025-02-14](https://langfuse.com/changelog/2025-02-14-trace-graph-view); [Agent Graphs docs](https://langfuse.com/docs/observability/features/agent-graphs); [Observation Types](https://langfuse.com/docs/observability/features/observation-types); [Nov 2025 update](https://langfuse.com/blog/2025-11-30-langfuse-november-update)
- **LangGraph Studio:** time-travel through checkpoints, editing state before or after a node, interrupts that pause for human review or edits, and forking a new branch from a past checkpoint with modified state. — [LangGraph docs: time travel](https://docs.langchain.com/oss/python/langgraph/use-time-travel); [mem0 guide](https://mem0.ai/blog/visual-ai-agent-debugging-langgraph-studio) (secondary)
- **AgentOps:** organized around sessions. A session waterfall lays LLM calls, actions, tool calls and errors on a timeline, and "session replay" walks through a run step by step. Cost is tracked per session, per action and per agent. — [AgentOps docs: Sessions](https://docs.agentops.ai/v1/concepts/sessions); [AgentOps GitHub](https://github.com/agentops-ai/agentops); [theneuralbase](https://theneuralbase.com/agentops/learn/intermediate/cost-dashboard-views/) (secondary)
- **OpenHands GUI:** a chat panel plus workspace tabs (Changes, VS Code, Terminal, App, Browser). An earlier PR widened chat to 50% and moved the terminal into the tabs. An accessibility issue on agent-canvas v1.16.0 notes the drawer's Files, Commits, Planner, Terminal, Browser and Usage controls lack proper tab semantics. — [OpenHands docs: Key Features](https://docs.openhands.dev/openhands/usage/key-features) (search snippet); [PR #5584](https://github.com/OpenHands/OpenHands/pull/5584); [issue #17268](https://github.com/OpenHands/OpenHands/issues/17268)
- **Claude Code:** an open issue reports that in the VS Code "agent map", nested subagents show "Tool calls (0)" and attach to the main agent instead of their real parent, while "Open transcript" shows the right calls. A separate feature request asks for tool logs of nested sub-agents spawned in an orchestrator session. — [anthropics/claude-code #98118](https://github.com/anthropics/claude-code/issues/98118); [#67882](https://github.com/anthropics/claude-code/issues/67882)
- **Third-party Claude Code tooling:** subagent lifecycle events (started, progress, finished) carry a description, type, background flag, status, one-line summary, tool_uses, total_tokens, duration_ms and last_tool. Each subagent renders as its own tree, nested recursively, and a rail shows "Subagents: N running". — [claude-dev.tools](https://claude-dev.tools/docs/subagents) (secondary, third-party)

### Inferences
- A recursive REPL agent maps well onto the LangSmith/Langfuse tree: each node is an agent invocation tagged with its namespace, and its children are the think/repl/observation steps and the sub-agent spawns. Collapsed nodes should show status, a one-line summary, tokens, cost and duration, and parents should show subtree totals.
- "Expand to see code + output" fits deep_reasoner better than an inferred graph: the repl code block and its observation are the meaningful units, and OpenHands-style tabs are overkill. A small "Subagents: N running" indicator with a live tree, as in third-party Claude Code tools, covers live progress.
- The Claude Code bug (nested sub-agents attached to the wrong parent) is a direct warning: carry an explicit parent id on every spawn event. Do not reconstruct the tree from timing.
- LangGraph-style "fork from this step with edited state" makes a strong bridge to authoring. "Edit this step and re-run from here" is both a debugger and a way to repair a run before saving it as a decomposition.
- The "communication overhead" barrier from Q1 supports collapsed-by-default summaries with drill-down.

### Gaps
- Could not verify Devin's or Claude.ai's own UIs for multi-agent progress (for example how Claude Research shows parallel subagents) from primary sources.
- Langfuse and LangSmith docs on the latest tree and graph UIs (2026) could not be fetched. Details of their 2026 UIs are unconfirmed.
- No sources compared tree, graph and timeline views for comprehension by non-experts.

## Q4. Hierarchical/inherited configuration UIs and permission/allow-list editing that ordinary users understand

### Takeaway
The clearest inheritance UI is Google Admin's: each setting is labeled "Inherited" or "Overridden", with explicit Override and Inherit (reset) buttons. The clearest allow-list UI is Claude Code's `/permissions`: every rule is listed with the file it came from, deny beats ask beats allow at every level, and higher-level (managed) denies can't be overridden. Copilot Studio shows the parent and child trade-off for sub-agents: child agents inherit the parent's tools and authentication, connected agents are independent.

### Cited Findings
- **Google Admin console:** text under each setting shows whether it is "Overridden" or "Inherited". Admins click **Override** to diverge from the parent organizational unit (OU), **Save** to update an override, or **Inherit** to restore the parent value. Settings cascade from parent to child and grandchild OUs by default. — [Google Workspace Admin Help: Change service settings for different users](https://support.google.com/a/answer/2655363?hl=en); [namastu.com](https://namastu.com/google-workspace-admin-console-ou/) (secondary)
- **Claude Code `/permissions`:** an interactive panel lists every active allow, ask and deny rule and which settings file it came from, and lets the user add or remove rules. Deny rules are checked first across all levels, then ask, then allow. A project deny beats a user allow, and a managed deny cannot be overridden. `allowManagedPermissionRulesOnly` locks rules to managed settings. — [Vincent Qiao blog](https://blog.vincentqiao.com/en/posts/claude-code-permissions/); [eesel.ai](https://www.eesel.ai/blog/claude-code-permissions) (secondary; official Claude Code docs not fetched)
- **Claude Code `/agents`:** creating a subagent includes picking its allowed tools, and the result is a `tools:` list in its config. — [Anthropic blog](https://claude.com/blog/subagents-in-claude-code)
- **Copilot Studio:** child agents are "a lightweight agent that exists within the context of your main agent". They share the parent's environment, tools and authentication and always receive its context, but have their own instructions and input/output variables. Connected agents are separate agents with their own instructions, tools, knowledge and orchestration. — [candede.com](https://www.candede.com/articles/copilot-studio-child-to-connected-agents/); [Holger Imbery](https://holgerimbery.blog/copilot-studio-orchestration-part1) (secondary)
- **Open WebUI:** model presets bind a base model with a system prompt, knowledge, tools, skills and parameter overrides. Admins set "global defaults" as a baseline, and access is restricted per user or group. Workspace resources are private by default and shared via an "Access" button. — [Open WebUI docs: Models](https://docs.openwebui.com/features/workspace/models/); [Skills](https://docs.openwebui.com/features/workspace/skills/) (search snippets)
- **n8n:** delegation is drawn on the canvas as an edge from a supervisor AI Agent to AI Agent Tool nodes, so who can delegate to whom is visible structurally. — [n8n blog: multi-agent systems](https://blog.n8n.io/multi-agent-systems/)
- **Skills security guidance:** treat a skill like installed software, audit bundled scripts, and watch for unexpected network calls, because "a malicious Skill can direct Claude to invoke tools or execute code in ways that don't match the Skill's stated purpose." — [Anthropic Agent Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)

### Inferences
- For deep_reasoner namespaces (root → research → research.web), each field of a child namespace should show its effective value with a provenance badge ("Inherited from research" / "Overridden here") and Google-style **Override** and **Reset to inherited** actions. The YAML stays canonical, and the badge is computed from the resolved chain.
- List-valued fields (tools, decompositions, preloaded variables) need explicit merge semantics in the UI: inherited items shown greyed with the source namespace, items added here shown normally, and a clear way to remove an inherited item. Whether that is allowed should be a team decision. Claude Code's deny-wins rule is a safe default for tools: a parent can forbid, a child can only narrow.
- The spawn allow-list is a small directed graph. Two familiar presentations: a per-namespace "Can delegate to: [checkboxes]" list (like the `/agents` tool picker), and a read-only diagram of the namespace tree with delegation edges (like n8n's supervisor-to-tool edges). A matrix only helps once there are more than about 8 namespaces.
- Copilot Studio's child vs. connected split mirrors a deep_reasoner choice: does a spawned sub-agent run in a sub-namespace (inherit) or a sibling namespace (independent)? Labeling that explicitly in the spawn editor helps users understand what the child gets.
- Showing the source of every effective rule (as `/permissions` does) is the single most useful feature for debugging "why can't my agent use X?"

### Gaps
- Official Claude Code permissions docs (code.claude.com) and Copilot Studio Learn pages were not fetched. The precedence details come from consistent secondary sources.
- Found no product that offers a GUI editor for agent-to-agent delegation allow-lists as a first-class permission (separate from wiring sub-agents as tools). This seems to be an unoccupied niche.
- No published user research on how non-experts understand configuration inheritance in AI tools specifically.

## Q5. Storage and portability for per-user agent configs: SQLite-per-user vs. shared Postgres, YAML/JSON export-import, git-backed configs, sharing/forking/templates/marketplaces, lessons learned

### Takeaway
Self-hostable multi-user products (Open WebUI, Dify, Langfuse) keep shared Postgres for multi-user deployments. SQLite is the single-user or dev default and becomes a bottleneck under concurrent writes. Portability is through export/import of plain JSON or YAML that leaves secrets out. Git-style workflows are being added (Langflow 1.9 Flow DevOps Toolkit, Copilot Studio `pac copilot` YAML). Open marketplaces (GPT Store) produced a long tail, spam and moderation problems, and several hosted builders were shut down (Humanloop, DataStax Langflow, OpenAI Agent Builder), which makes owning an exportable format important.

### Cited Findings
**Database choice**
- Open WebUI defaults to SQLite but says "for any multi-user or high-concurrency setup, PostgreSQL is mandatory": SQLite hits locking errors under concurrent writes. Multiple replicas also need Redis for sessions and websockets and an external vector DB. — [Open WebUI: Scaling](https://docs.openwebui.com/getting-started/advanced-topics/scaling/); [Performance](https://docs.openwebui.com/troubleshooting/performance/) (search snippets)
- Langfuse v3 self-hosting needs web and worker containers plus Postgres (transactional data), ClickHouse (traces), Redis or Valkey (queue and cache) and S3 or MinIO. Minimums are roughly Postgres 2 CPU/4 GiB, ClickHouse 2 CPU/8 GiB and Redis 1 CPU/1.5 GiB. — [Langfuse v3 architecture discussion](https://github.com/orgs/langfuse/discussions/1902); [Langfuse: ClickHouse](https://langfuse.com/self-hosting/deployment/infrastructure/clickhouse); [Langfuse: Scaling](https://langfuse.com/self-hosting/configuration/scaling)
- Per-tenant SQLite isolates by file, so a missing `WHERE tenant_id = ?` cannot leak data, and deleting a user is one unlink. It suits isolated tenants with low write concurrency and no cross-tenant queries, and breaks down with cross-tenant queries, multiple writers, or very large databases. Postgres Row-Level Security mitigates leak risk in shared schemas. — [DEV: per-user SQLite vs row-level](https://dev.to/helperx/multi-tenant-data-isolation-in-sqlite-per-user-database-files-vs-row-level-5glm) (secondary); [Turso: multi-tenancy at scale](https://turso.tech/blog/multi-tenancy-at-scale); [PlanetScale: tenancy in Postgres](https://planetscale.com/blog/approaches-to-tenancy-in-postgres)

**Export/import formats**
- Dify exports and imports apps as "DSL" YAML. Exports include app config, workflow nodes, model parameters, prompts and knowledge-base links. They exclude third-party API keys, knowledge-base contents and logs. Import warns when the DSL version is older than the platform. — [Dify docs: Manage Apps](https://docs.dify.ai/en/cloud/use-dify/workspace/app-management) (search snippet)
- Pitfall: CVE-2025-32790 (Dify ≤0.6.8, fixed 0.6.13) let normal users export app DSL when only admins should have been able to. — [GitHub advisory GHSA-jp6m-v4gw-5vgp](https://github.com/langgenius/dify/security/advisories/GHSA-jp6m-v4gw-5vgp); [NVD](https://nvd.nist.gov/vuln/detail/CVE-2025-32790)
- Langflow exports flows as `FLOW_NAME.json` via Share → Export and imports via "Upload a flow". — [Langflow docs: import and export flows](https://docs.langflow.org/concepts-flows-import) (search snippet)
- Open WebUI model presets are plain JSON. You can export all or by id via `/api/v1/models/export`, and choose additive `/import` or reconciling `/sync`. Import also accepts community links. — [Open WebUI: Import & Export](https://docs.openwebui.com/features/chat-conversations/data-controls/import-export/); [Models](https://docs.openwebui.com/features/workspace/models/) (search snippets)
- Flowise exports chatflows and agentflows as JSON. A PR added controlled export/import with conflict management across AgentFlow V2, tools, variables and more, and issues report import failures across versions (e.g., v3.0.0). — [Flowise PR #5352](https://github.com/FlowiseAI/Flowise/pull/5352); [issue #4461](https://github.com/FlowiseAI/Flowise/issues/4461); [issue #4139](https://github.com/FlowiseAI/Flowise/issues/4139)

**Git-backed configs**
- Langflow 1.9 (Apr 2026) added the Flow DevOps Toolkit SDK (`lfx init`). It is a scaffold with flows/, tests, CI workflows and `.lfx/environments.yaml`, plus Git-style push and pull between local files and servers, "instead of manually exporting, sharing, and importing flow JSON files". — [Langflow: Flow DevOps Toolkit](https://docs.langflow.org/flow-devops-sdk); [Langflow 1.9 blog](https://www.langflow.org/blog/langflow-1-9/)
- Copilot Studio agents live in Power Platform "solutions" moved between Dev, Test and Prod environments. A VS Code extension (`pac copilot init` / `pack`) gives a local workspace of YAML (`agent.mcs.yml`, `settings.mcs.yml`) for Git and PRs. — [MS Learn: solutions](https://learn.microsoft.com/en-us/microsoft-copilot-studio/authoring-solutions-overview); [microsoft/copilot-alm-starter](https://github.com/microsoft/copilot-alm-starter); [The Workbench blog, Aug 2026](https://www.theworkbench.blog/2026/08/copilot-studio-real-alm-for-agents-and.html) (secondary)

**Sharing scopes**
- Claude Skills sharing differs by surface: claude.ai custom skills are "individual to each user", API skills are workspace-wide, and Claude Code skills are personal or per project (sharable via plugins). Custom skills "do not sync across surfaces". — [Anthropic Agent Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- Claude Projects on Team and Enterprise plans can be shared with "Can view" (use and chat) or "Can edit" (change instructions and knowledge). Free, Pro and Max have no project sharing. — [Claude Help: create and manage projects](https://support.claude.com/en/articles/9519177-how-can-i-create-and-manage-projects); [certsafari](https://www.certsafari.com/anthropic/claude-certified-associate-foundations/learn/sharing-claude-projects-plan-limits-permissions-and-admin-controls) (secondary)
- Gems are shared with Viewer or Editor roles, as Drive files are. Open WebUI resources are private by default and shareable with users or groups, and public prompts appear in everyone's suggestions. — [Zapier](https://zapier.com/blog/gemini-gems/) (secondary); [Open WebUI: Prompts](https://docs.openwebui.com/features/workspace/prompts/)

**Marketplaces and templates**
- Dify's Creator Center and Template Marketplace take uploads of exported DSL `.yml` files up to 10 MB. Users can then discover, try and adopt templates. — [Dify blog](https://dify.ai/blog/dify-creator-center-template-marketplace-share-your-workflows); [Dify: publish to marketplace](https://docs.dify.ai/en/cloud/use-dify/publish/publish-to-marketplace)
- Flowise marketplace templates are JSON files in the repo (`packages/server/marketplaces/…`) that load into the canvas. — [DeepWiki: Flowise marketplace](https://deepwiki.com/FlowiseAI/Flowise/11.1-marketplace-and-template-flows)
- GPT Store lessons:
  - One analysis reports about 3M GPTs with only 72 featured, and very heavy concentration: the top 7 GPTs had about 50% of conversations, and the GPT ranked #500 had about 1,000 conversations. — [Jaclyn Konzelmann product analysis](https://blog.jaclynkonzelmann.com/p/a-product-analysis-on-the-custom) (secondary, date not confirmed, likely 2024)
  - More than 100 GPTs were found violating policies in Sept 2024. — [WinBuzzer](https://winbuzzer.com/2024/09/05/openai-struggles-with-gpt-store-policy-enforcement-xcxwbn/) (secondary)
  - A CHI 2025 study found users reporting spam and no way to report malicious GPTs. — [ACM: Privacy perceptions of custom GPTs](https://dl.acm.org/doi/10.1145/3706598.3713540)

**Vendor shutdowns**
- Humanloop shut down 8 Sept 2025 ([HN](https://news.ycombinator.com/item?id=44592216)).
- DataStax-hosted Langflow was deprecated 9 Mar 2026 with shutdown 9 Apr 2026, and users were told to migrate to Langflow OSS ([DataStax Langflow FAQ](https://docs.datastax.com/en/langflow/faqs.html), search snippet).
- OpenAI Agent Builder shuts down 30 Nov 2026, and its code export does not convert the graph (Q1).

### Inferences
- For a University of Washington multi-user deployment, the prior art favors one shared database (SQLite is fine for a small pilot on one server; Postgres once concurrency or replicas matter) with a `user_id` on every config row. Per-user SQLite files give strong isolation and trivial "delete my data", but make sharing and forking across users (copying a colleague's decomposition) and admin queries awkward. A middle path matching the team's "YAML behind the scenes" idea: DB rows store the canonical YAML text plus indexed metadata (owner, name, version, label, parent namespace, visibility).
- Copy Dify's export hygiene: export a namespace or decomposition bundle as YAML with a format `version:` field, strip secrets and credentials (tool grants reference credentials by name, never by value), warn on version mismatch, and run export through the same permission check as reading (the Dify CVE is the cautionary tale).
- Treat Open WebUI's `/import` (additive) vs `/sync` (reconciling) as a useful API distinction for bulk-loading a lab's shared namespace library.
- For sharing, the Drive/Gems model (private by default; share with a person or group as viewer or editor; "Duplicate to edit") is familiar to university users. Forking beats editing shared items in place. A curated "lab templates" shelf beats an open marketplace, given GPT Store's spam and long-tail experience.
- Git-backed sync (Langflow `lfx`, Copilot `pac copilot`) is now expected by power users. An optional "export to / import from a git repo of YAML" keeps the hand-written YAML workflow alive alongside the GUI.
- Three hosted-builder shutdowns in about 14 months support the team's choice to be self-hostable with an open, file-based canonical format.

### Gaps
- Could not confirm how Dify stores per-tenant data internally (shared Postgres with tenant ids is widely reported but not verified from primary docs in this session).
- No first-hand post-mortems from teams that moved from per-user SQLite to shared Postgres (or back) for agent-config products specifically.
- Status of Langflow's original component "Store" (API endpoints still exist) as of 2026 is unclear. Whether it was discontinued could not be confirmed.
- Primary statistics on GPT Store usage in 2025–2026 were not found. The cited numbers are older and secondary.

## Q6. Distilled recommendations: editing multi-turn transcript examples with code, a namespace tree with inheritance, tool grants and spawn allow-lists, and testing an example before saving

### Takeaway
Copy four proven patterns: (1) record a run → trim and edit → save as decomposition, with "describe it and we draft it" as a second entry point; (2) a Google-Admin-style namespace tree with Inherited/Overridden badges and Reset; (3) Claude-Code-style tool and spawn checklists that show each rule's source, with deny-wins semantics; (4) a Gems/Console-style split preview with a small multi-task test set before saving. Avoid a node canvas for authoring, an open marketplace, and lossy trace-to-example conversion.

### Cited Findings
These are the specific precedents each recommendation rests on, already cited above:
- **Record → edit → save:** LangSmith "Add to dataset" from runs and threads, and Langfuse "+ Add to dataset" from an observation ([LangSmith](https://docs.langchain.com/langsmith/manage-datasets-in-application), [Langfuse](https://langfuse.com/docs/evaluation/experiments/datasets)). "Open in Playground" from a trace ([Langfuse Playground](https://langfuse.com/docs/prompt-management/features/playground)). Fidelity bugs in both ([langsmith-sdk #2671](https://github.com/langchain-ai/langsmith-sdk/issues/2671), [langfuse #3912](https://github.com/langfuse/langfuse/issues/3912)).
- **Edit a step and re-run from there:** LangGraph Studio fork and edit-state ([LangGraph time travel](https://docs.langchain.com/oss/python/langgraph/use-time-travel)).
- **Describe → draft:** GPT Create tab ([Zapier](https://zapier.com/blog/custom-chatgpt/)); Copilot Studio Describe ([MS](https://learn.microsoft.com/en-us/power-platform/release-plan/2024wave1/microsoft-copilot-studio/create-agents-using-everyday-natural-language)); Claude Code "Generate with Claude" ([Anthropic](https://claude.com/blog/subagents-in-claude-code)); skill-creator ([Claude tutorial](https://claude.com/resources/tutorials/how-to-create-a-skill-with-claude-through-conversation)); Crew Studio ([CrewAI](https://docs.crewai.com/en/enterprise/guides/enable-crew-studio)).
- **Preview before save:** Gems Preview pane, which does not autosave ([Google help](https://support.google.com/gemini/answer/15235603?hl=en)); Agent Builder preview runs and Evaluate tab ([Superprompt](https://superprompt.com/blog/openai-agentkit-agent-builder-guide), secondary); Anthropic Console generated test cases and side-by-side comparison ([Anthropic](https://www.anthropic.com/news/evaluate-prompts)); promptfoo matrix ([promptfoo](https://www.promptfoo.dev/docs/intro/)).
- **Inheritance UI:** Google Admin Inherited/Overridden with Override/Inherit ([Google](https://support.google.com/a/answer/2655363?hl=en)). Permission source display and deny-first precedence ([Vincent Qiao](https://blog.vincentqiao.com/en/posts/claude-code-permissions/), secondary).
- **Versions and labels:** LangSmith commits and movable tags ([LangSmith](https://docs.langchain.com/langsmith/prompt-engineering-concepts)); Langfuse timestamped dataset versions ([Langfuse](https://langfuse.com/changelog/2025-12-15-dataset-versioning)); PromptLayer release labels ([PromptLayer](https://docs.promptlayer.com/features/prompt-registry/release-labels)).
- **"Use when" metadata as trigger:** the Skills `description` must say what the skill does and when to use it ([Anthropic](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)).
- **Non-experts overgeneralize and explore opportunistically:** [Why Johnny Can't Prompt](https://dl.acm.org/doi/pdf/10.1145/3544548.3581388). Agent communication overhead: [Why Johnny Can't Use Agents](https://arxiv.org/html/2509.14528v1).

### Inferences
These are recommended patterns, inferred from the findings above.

**A. Decomposition (worked-example transcript) editor**
1. **Primary entry: "Save run as decomposition."**
   - From any finished run in the trace panel, the user picks the turns to keep and trims dead ends.
   - Long observations are collapsed with an "elide" toggle, so few-shot examples don't carry huge outputs.
   - Sub-agent spawns can be kept as a single repl call plus its observation (the sub-agent's internals stay hidden).
   - It is saved as a new version.
   - Because deep_reasoner traces already have the decomposition structure, this avoids the Langfuse/LangSmith fidelity bugs. Keep the mapping lossless and test it.
2. **Editor shape: chat-style cards, not raw YAML.**
   - One card per turn: User task; Assistant (collapsible `<think>` text plus a `<repl>` code block with syntax highlighting); Observation (monospace output, marked "captured" or "edited by hand"); a final FinalAnswer card.
   - Cards can be inserted, reordered and deleted.
   - A "View YAML" toggle shows the canonical source for power users.
   - Flag when a hand-edited observation no longer matches what the code would produce. Offer "Re-execute this step", following LangGraph's fork-from-step pattern, so examples stay honest.
3. **Secondary entry: "Describe it."**
   - The user writes "how should the agent split tasks like X?" and a model drafts a full transcript, which they then edit. This parallels GPT Create, Copilot Describe, Claude Code "Generate with Claude" and skill-creator.
   - Label generated observations as synthetic until a test run replaces them with real ones.
4. **Metadata fields:**
   - name, a "use when…" description (Skills-style; doubles as retrieval text for dynamic selection);
   - mode: few-shot example vs. "run literally as a fixed program";
   - which namespaces it is attached to.
5. **Versioning:** each save is an immutable version. A movable `current` label is what namespaces reference, and runs record the exact version used.

**B. Namespace tree with inheritance**
1. Use a left-hand tree (`root` › `research` › `research.web`), matching the dotted names. Selecting a node opens a form of its fields: backend, model, tools, preloaded variables, extra system text, decompositions, may-spawn.
2. Each field shows its effective value and a badge: "Inherited from research" (greyed, with a link to the parent) or "Overridden here". **Override** and **Reset to inherited** buttons follow the Google Admin pattern.
3. For list fields, show inherited items greyed with their source, items added locally, and an explicit "remove inherited item" if the semantics allow it. Write the merge rule (append vs. replace) in the UI copy.
4. Add an "Effective config" view with per-line provenance, the equivalent of Claude Code `/permissions` showing each rule's source file. It answers "why does my agent have or lack X?".
5. Creating a namespace means "New child of …" (inherit everything by default) or "Duplicate" (fork). Avoid empty forms.

**C. Tool grants and spawn allow-lists**
1. Tool grants: a checklist of available tools, as in Claude Code `/agents`. Inherited grants are checked and locked with a source badge. Deny-wins: a parent's deny cannot be re-enabled by a child, as with managed settings in Claude Code.
2. Spawn allow-list: on each namespace, a "Can delegate to" checklist of other namespaces. Alongside it, a small read-only diagram of the namespace tree with delegation arrows (n8n-style edges) so users see the whole picture. Distinguish "spawn into a child namespace (inherits)" from "spawn into a sibling or other namespace (independent)", echoing Copilot Studio's child vs. connected agents.
3. Warn on risky combinations: a namespace with code execution and network tools that any namespace may delegate to. Treat imported or shared namespaces like Skills: review before enabling.

**D. Test before saving**
1. Use a split view. The editor is on the left. A preview chat on the right runs the draft namespace or decomposition in a sandbox, nothing persists until Save, and the run tree streams live with collapsed summaries and an "N sub-agents running" indicator.
2. Give each namespace a small test set (3–10 tasks), seeded by "suggest test tasks" in the style of Anthropic's Console. "Run all" shows a promptfoo-style matrix of tasks × versions (or with vs. without this decomposition), with pass/fail or a 1–5 rating, tokens, cost and time. This counters the overgeneralize-from-one-run behaviour the CHI 2023 study documents.
3. Show a diff view between versions (decomposition text and effective namespace config) next to the comparison results.

**E. Storage, sharing and portability**
1. Keep the YAML text canonical inside the DB, plus metadata columns.
2. Use a single shared SQLite DB for the pilot and Postgres for multi-worker deployments. This follows Open WebUI's experience; per-user SQLite files are viable only if cross-user sharing stays rare.
3. Sharing works like Drive: private by default; share with people or groups as viewer or editor; recipients "Duplicate to my library" to fork, keeping a "forked from" link. Offer a curated lab or course template shelf rather than an open store.
4. Export and import YAML bundles carrying a format version, with secrets stripped and permission-checked export. Optional git sync covers power users.

**Pitfalls to avoid**
- A graph canvas for model-decided behaviour (OpenAI is retiring one).
- Lossy trace-to-example conversion and Playground edits that can't be saved back (known LangSmith/Langfuse bugs).
- Reconstructing nested agent trees from timing instead of explicit parent ids (Claude Code bug #98118).
- Configs that don't sync across surfaces (Claude Skills).
- Exports that leak secrets or skip permission checks (Dify CVE-2025-32790).
- An open marketplace that fills with spam (GPT Store).
- Depending on a hosted builder that may be shut down.

### Gaps
- No product found offers a purpose-built editor for multi-turn worked-example transcripts that contain code and execution output. The editor design above is synthesized from adjacent patterns (dataset editors, playgrounds, notebook-like cells), not copied from one product.
- No usability evidence was found on whether non-experts understand list-field inheritance (append vs. replace) or delegation allow-lists. Both should be user-tested with UW users.
- Real-world effectiveness data on "save run as example" (how often saved examples improve later runs) was not found for any product.
