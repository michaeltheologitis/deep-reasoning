# D4 · Custom tools — design

**TASK-9** · System Designer · task branch `v1-custom-tools` in
[deep-reasoning](https://github.com/michaeltheologitis/deep-reasoning) (this file is written on `design/d4`) ·
against the approved spec [TASK-1](https://app.notion.com/p/3ed62fb22237814ab425c81b3844f012) (D4 in full; §1's
"done when"; §2's decisions 1 and 7; §4's E9, E10 and the live tier; the dated notes at its end, read live on
2026-10-03, through "Scope additions approved, 2026-10-03").
**Pinned against:** D3's design at `ab6f2ec` on `design/d3` (§8.3 is D4's UI contract; §2.5, §4, Appendix A) · D2 as
built on `v1-library-store` at `90044f0` (`src/deep_reasoning/library/`; its design `555472b`, §6.5 and §9 items 7
and 10) · D1's design at `c8d7fbb` (§4.3, §4.4, §4.7, §4.8) and its code as merged into `90044f0` · D5's design at
`8086afb` (§2, §4.7, §7.1) · SDK fork `deep-reasoning` at `91430aa` (`acp_agent.py`, `settings_router.py`, the App
bridge; `mcp` 1.28.1 in its lock) · deep_reasoner_beta `d7334ae` · `agent-client-protocol` 0.12.1 · `mcp` 1.28.1.

**Revisions** (newest first; each line says which sentences to stop trusting):
- 2026-10-03 · v1 · first full-depth version.

**Where this file lives, and why nothing trips over it.** `docs/design/d4-custom-tools.md`. The `design/d4` branch
holds only documents. On the task branch, which carries D1's `pyproject.toml`, pytest collects `tests/` only, the
wheel is built from `src/deep_reasoning`, the sdist excludes `docs/`, and ruff excludes `docs` (D1 §8.5). D3's
TypeScript tools run inside `canvas-app/` only (D3 §4.1), so they never see `docs/`. The PR split leaves this file
behind.

**Reading guide.** Gate B: §1 (what D4 is and its decisions), §2 (the Tools tab as the user meets it), §3 (Check),
§4 (MCP servers), §5 (what a tool or a server can reach) and §6 (departures from the spec): about 35 minutes. D1's,
D2's, D3's and D5's designers: §11, then the sections it points to. The Implementer reads everything; Appendix A is
the signature reference, §9 every user-visible sentence, §10 the tests.

**What was verified for this design (2026-10-03, in a scratch environment outside every repository: Python 3.12,
deep_reasoner at `d7334ae` from D2's scratch install, `mcp` 1.28.1 from PyPI, the version the SDK fork locks):**

1. **Check can mirror `make_tools` exactly.** A one-tool config written as D2 materializes one (`main.yaml` with a
   `client` and `tools: {word_count: {factory, factory_from: tools/word_count.py}}`), loaded with
   `load_cli_config(…, schema=V2Config)`, then built step by step (`load_tool_factory`, the factory call, the `Func`
   check) and also by `make_tools` itself, on six fixtures: a working tool, a factory returning a plain function, a
   misspelled factory, an import of a missing module, a factory raising `KeyError`, a module reading an unset
   environment variable at import. Every outcome agreed. `load_tool_factory`'s messages are deep_reasoner's own and
   identical in both; an import failure is a `ValueError` whose `__cause__` is the original exception, a misspelled
   factory one with no cause; the non-`Func` sentence exists only inline in `make_tools` (`v2/cli.py:158–164`); an
   exception raised by the factory itself reaches `make_tools`' caller unwrapped and without the tool's name
   (`KeyError: 'GITHUB_TOKEN'`). The working tool's line, from deep_reasoner's own
   `func(name, value, description).describe()`, is ``- `word_count(text: str) -> int` `` followed by its
   description. A client whose `base_url` is `http://127.0.0.1:9/v1` builds without any key (`config.py:249–265`).
2. **`mcp` 1.28.1 starts a stdio server in a session of its own** (`client/stdio/__init__.py:256`,
   `start_new_session=True`), so D1's process-group kill of the worker does not reach it. A server that never answers
   and never reads its stdin outlived the client process that started it. Run through a 20-line guard that polls its
   parent's pid and kills its own process group when the parent is gone, both a working server and a silent one were
   gone within 1.5 s of the client process being `SIGKILL`ed (§4.6).
3. **One MCP connection on a loop thread of its own serves synchronous calls from any thread**, including a thread
   inside its own running loop, and before and after `nest_asyncio.apply()` (deep_reasoner applies it when an `llm`
   call is made inside a running loop, `llm.py:188–196`; it swaps asyncio's task and future classes for the whole
   process). Measured: a FastMCP stdio server answered `initialize` and `tools/list` in 1.2 s; a server exiting at
   start failed with `McpError: Connection closed`; three servers started at once were all decided by one shared
   deadline; a server that crashed mid-run failed the call in flight with `McpError: Connection closed` and the next
   call with an empty `ClosedResourceError`, while the connection's own task never noticed (§4.4); bad arguments
   came back as `isError` with the server's validation text; FastMCP wraps a primitive return as
   `{"result": value}` and advertises an `outputSchema` whose only property is `result`.
4. **A crashing server's stderr carried its own secret** (the fixture printed its token), so a failure's detail must
   be redacted before it reaches the run log (§4.5).

Not verified here: the agent-server forwarding Canvas's MCP settings to `dr-acp` end to end (`_mcp_config_to_acp_servers`
was read, not run; §10.6 proposes the cross-repo test), HTTP and SSE servers (read from the `mcp` source), macOS, and
CodeMirror's build size (§7.4 sets a budget).

---

## 1 · What D4 is

deep_reasoner already supports tools of one's own: a tool block names a Python file and a factory in it
(`factory_from`, `tools/base.py:294–407`), and `make_tools` builds every block when a run starts
(`v2/cli.py:125–180`). D4 makes that usable from the app, and adds existing MCP servers beside it, as Michael chose
(Q6 (d)):

- **Your own tools.** The decompositions panel's **Tools** tab gets a tool editor: a name, the tool block (YAML), the
  Python source, an optional expression to try, a **Check** button, and the namespaces it is granted to. Check builds
  the tool exactly as a conversation would, in a throwaway process, and shows what the agent will be told, the tried
  value, or deep_reasoner's own error. Saving runs Check again on the server and refuses a tool that cannot build.
  The tool is a D2 tool row (the block plus the source); a conversation's run writes it to `tools/<name>.py` beside
  the materialized config, and an export carries it.
- **Existing MCP servers.** The same tab lists the servers configured in Canvas's MCP settings, each with namespace
  checkboxes. A grant is a D2 tool row too: its block names the server and snapshots its non-secret settings, and its
  source is D4's **shim**, a self-contained `factory_from` file whose factory binds the server's tools as one REPL
  object. In a conversation, `dr-acp` takes the servers OpenHands forwards at session start, its worker connects the
  granted ones when the run is built, and the shim hands each agent the connected server; under plain `dr`, on an
  export, the same shim connects by itself from the snapshot.

```text
Canvas window · Show Decompositions › Tools  (D3's frame; D4's tab)
   your tool:  editor ── POST ../tools/{name}/check ──▶ dr-library serve ── python -m …check_child (throwaway; 30/10/10 s)
               Save   ── PUT  ../tools/{name}       ──▶ Check again (code changed) ──▶ D2: tool row {block, source}, granted_in
   MCP server: Canvas's MCP settings (the page reads GET /api/settings; frame parameter `mcp`)
               a tick ── PUT  ../mcp/{name}         ──▶ D2: tool row {block: server snapshot, source: the shim}, granted_in

a conversation, first message (D1 §2 step 4)
   dr-acp front: LibraryCatalog.materialize → runs/<run>/config/{main.yaml, namespaces/, tools/<name>.py}
                 the forwarded mcpServers (session/new) that main.yaml's MCP blocks name → Start.mcp_servers
   worker:       load_dr_config → open_session: connect the granted, reachable servers at once (≤ 10 s, each through
                 the guard) → mcp.status (run log; a notice for each server not bound) → build_reasoner → make_tools
                 builds every block: your tool's factory; the shim's mcp_server() takes the connected server
   each agent:   binds the tools its namespace resolves (deep_reasoner): `word_count`, `github` (github.search_issues(…))
```

What a user does, end to end (spec §1's "done when"): they write a tool, check it, grant it to a namespace, and the
agent uses it; they connect an MCP server in Canvas's settings, grant it to a namespace, and the agent uses its tools.

### 1.1 Decisions this design takes

The spec's seven decisions in §2 stand, and so do D1's, D2's and D3's. These are the next layer down.

| # | Decision | Why | Rejected |
|---|---|---|---|
| A | **Check runs where saving happens: in the App backend (`dr-library serve`), as a throwaway child process of the same runtime Python, against a one-tool config materialized the way a run's is, built by a step-by-step mirror of `make_tools`' `factory_from` branch.** | Same deep_reasoner, same file layout, same resolution of `factory_from` against `config_path`, same messages (verified, header item 1). A child process survives nothing the tool does to itself, can be killed by group at a limit, and keeps the tool's prints out of the report. The mirror, not `make_tools` itself, so each failure is classified by the step that failed rather than by matching message text; a test pins that both agree on every fixture (§10.2). | Calling `make_tools` and parsing its exceptions (the factory's own exception and deep_reasoner's `ValueError`s are told apart only by text). Building in the backend's own process (a hanging factory hangs the API; an import is cached forever in `_FACTORY_MODULES`). Building in a conversation's worker (the panel cannot reach one). |
| B | **Check gives the tool no secrets and no model**: the backend's six environment variables plus `HOME`, `USER` and `LOGNAME`, a client pointed at a closed loopback port, the materialized config folder as working directory. **It is not a sandbox**: the tool runs as the user, with the disk and the network. | Check must never spend money or leak a key, and the backend has no keys to give (the agent-server starts it with six variables, D2 §4.8). A sandbox that a real run does not have would make Check pass what a run fails. | Running Check with the user's Canvas secrets (the backend cannot read them). A network or filesystem sandbox (`unshare` needs privileges on some Linux machines and does not exist on macOS; and it would diverge from a run). |
| C | **Saving through the panel runs Check whenever the code changes; a structural failure is refused, and a failure Check cannot attribute (an exception the tool raised, its time limit, Check itself not starting) can be saved anyway, explicitly.** | `make_tools` builds every tool block of a run's config (`v2/cli.py:149`), so one tool that does not build stops every conversation in every namespace from starting. That is E9's null in its worst form. A tool that reads a secret or a file when it is built fails in Check's environment and works in a conversation; refusing it outright would make a valid tool unsaveable. | Check as advice only (the spec's mock-up; a broken tool then surfaces at run time, for every conversation). Refusing every failure (traps tools that need the conversation's folder or a secret at build time). |
| D | **An MCP grant is a D2 tool row** (D2's option (a)): block `factory: mcp_server`, `factory_from: tools/<name>.py`, the server's name and non-secret settings; source the shim; granted through `granted_in`. | Grants become deep_reasoner's own namespace `tools` lists, so inheritance, the effective view, D3's Namespaces tab, versions, history, export and import all work with no change to D2's schema or to D1's Catalog; and an export runs under `dr` by construction, because the shim is the factory file. | A table of D4's own through `store.MIGRATIONS` (D2's option (b)): a new versioned kind (the `versions.kind` CHECK constraint is rebuilt with the table), its own materializer path so `dr` sees the grants at all, and its own inheritance rules beside deep_reasoner's. |
| E | **Canvas's MCP settings decide how a server is reached; the Library decides who gets it.** In `dr-acp`, a server is connected only from what OpenHands forwarded at session start, with its secrets; a granted server that was not forwarded (disabled in Canvas, or left out of the profile's `mcp_server_refs`) is not started, and the conversation says so. The row's snapshot is used only by plain `dr`. | OpenHands withholds a disabled server from an ACP agent on purpose ("withholding the entry is the only way to keep a disabled server out of its reach", `acp_agent.py:750–752`); falling back to the Library's snapshot would start it anyway. Secrets never enter the Library or an export. | Storing the server's whole definition, secrets included, in the Library (secrets in SQLite and in every export). Storing only the grant (an export could not reach the server under `dr`, which the spec requires). |
| F | **The worker connects the servers, all at once, before `build_reasoner`, with one shared deadline (10 s); the shim's factory, called by `make_tools`, takes what the worker connected.** | Each block's factory runs in turn inside `make_tools`, so connecting there would cost 10 s per silent server; connecting first costs 10 s at most in all. The worker learns each server's outcome before the run starts, so the notice is in the run log ahead of the first answer. | Connecting in the shim's factory (sequential). Connecting in `dr-acp`'s front and proxying calls to the worker (a second transport between the two processes, and a shim that would differ under `dr`). |
| G | **A run connects every server granted to a namespace its agents can reach** (deep_reasoner's `check_spawn` from the conversation's namespace, transitively), and each agent binds a server's tools only when its own namespace resolves the grant; a server handed to a sub-agent in a namespace not granted it is refused. | deep_reasoner builds one tool registry per run and binds per agent (`namespaces.py:345–392`); a sub-agent spawned into a granted namespace must get the server even when the conversation began elsewhere, and only `__cross_namespace__` (`namespaces.py:645–654`, the seam `safe_url` uses) can stop an explicit hand-off. | Binding only the conversation's own namespace's grants (a sub-agent spawned into a granted namespace would lose a tool deep_reasoner gives it). Starting every granted server regardless of reach (a restricted `spawn` list would still start, and warn about, servers no agent can use). |
| H | **A server that is not bound leaves a stand-in under its REPL name**, which tells the agent why and raises that sentence if called. | deep_reasoner refuses an agent whose namespace names a tool the registry lacks (`namespaces.py:379–382`), so an unbound server cannot simply be missing; and a decomposition that calls it gets a sentence instead of a `NameError`. | Editing the run's config to drop the server (the run's namespaces are files deep_reasoner reads inside `build_reasoner`). |
| I | **Each stdio server runs under a guard**: the shim file run as a script (`--guard`), which starts the server in its own process group and ends that group when the process that started it is gone. | Verified need (header item 2): `mcp` puts the server in a session of its own, and a server that ignores its closed stdin outlives a worker that was killed. The guard imports only the standard library (about 30 ms) and works on Linux and macOS. | Relying on stdin EOF (fails exactly for the servers that hang). Recording pids for the front to kill later (a crashed server's pid can be reused). A stdio transport of our own (duplicates `mcp`'s). |
| J | **The shim is one self-contained module, `deep_reasoning/mcp/shim.py`, whose text is the row's source.** It imports only the standard library at module level; `mcp` and deep_reasoner's `Func` when used. In a `dr-acp` worker its factory returns what the worker installed (`SESSION`); anywhere else it connects by itself. | One code path for the app and for `dr`. A stored shim keeps working when deep-reasoning moves on, because in `dr-acp` it only reads `SESSION`, a dict of `Func`s, the one contract between versions. Without `mcp` installed a run still starts, with a stand-in that says to install it. | A thin shim importing deep-reasoning (an export would need deep-reasoning, not just `mcp`). |
| K | **What the panel shows of a server's tools is what the last conversation that connected it saw**, from a small cache `dr-acp` writes (`$DR_HOME/mcp/`). | The panel cannot connect a server: the backend has no access to its secrets. The spec's mock-up ("12 tools", "the agent is told: …") needs the list. | Connecting from the panel through the agent-server's `POST /api/mcp/test` (it returns tool names only, and needs the secrets sent back in). |
| L | **The tool source is edited in CodeMirror 6 (Python), loaded as a separate chunk only by the tool editor; every other field keeps D3's textareas.** | The spec costed a CodeMirror editor for Q6's answer; indentation and highlighting matter for Python in a way they do not for D3's YAML values. A separate chunk keeps D3's other tabs at their size (D3 §8.3 anticipated it). | A textarea for Python (no indentation help). CodeMirror for every field (D3 decision C). |

### 1.2 What D4 owns, and its seams

- **Owns:** `src/deep_reasoning/tools/` (Check and the tool routes), `src/deep_reasoning/mcp/` (the shim, the wire
  models, the worker's session, the Library-side grant records), the Tools tab's frame code in `canvas-app/`
  (extending D3's `tabs/tools.tsx`), `tests/tools/`, `tests/mcp/`, D4's additions to `tests/canvas_app/test_tools_tab.py`.
- **Seam to D1** (§11.1): `Start.mcp_servers`; one RunEvent, `mcp.status`, its encoding and sentences; the
  capabilities flip; the seen cache written by the pump; about 90 lines in D1's files.
- **Seam to D2** (§11.2): tool rows, `granted_in`, `materialize`'s `tools/<name>.py`; the Check gate in `PUT /tools/{name}`;
  D4's routes appended to `create_app`; no schema change.
- **Seam to D3** (§11.3): exactly §8.3 of D3: `tabs/tools.tsx`, `api.ts`'s `checkTool` and two MCP calls, the shared
  components, one frame parameter, the editor chunk.
- **Seam to D5** (§11.4): E10 re-run with MCP servers bound; one exception in §2.1's table; the profile's
  `mcp_server_refs: null`; a proposed E12 step.

---

## 2 · The Tools tab, as the user meets it

D3's banner stays at the top of the tab, permanently (D3 §2.5, D5 §2.3). D4 adds its own sentence under it, then the
two lists.

```text
┌ Decompositions │ Create decomposition │ Namespaces │ Tools │ ⋯ ──────────────────────────────── (Canvas's row) ┐
│ ⚠ deep_reasoner runs as you. It can read and change any file you can, … stops at $5 per conversation.         │
│ ⚠ Tools and MCP servers run as you, with your files and network: your tools inside the agent's process, a    │
│   stdio MCP server as a program started for each conversation that can use it. Check runs your code too.     │
│   Add only code and servers you trust.                                                                       │
│ Your tools                                                                               [+ New tool]        │
│   word_count   v1   make · tools/word_count.py                  granted in course_advisor                    │
│   rag          v2   built-in rag                                granted in root                              │
│ MCP servers (from Canvas's settings)                                                                         │
│   github    stdio  npx -y @modelcontextprotocol/server-github   as github     ☑ router  ☐ course_advisor  …  │
│             12 tools, as the conversation of 3 Oct, 14:02 saw them ▸                                         │
│   postgres  http   https://db.lab.example/mcp                   as postgres   ☐ router  ☑ course_advisor  …  │
│             Its tools are listed here after the first conversation that starts it.                          │
│   slack     stdio  Disabled in Canvas's MCP settings: not started until you enable it there.                 │
│   old-wiki         Granted, but no longer in Canvas's MCP settings.                                [Remove]  │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Your tools

**The list** is `GET /tools` minus the MCP grants (`GET /mcp` names them): name, version, the factory and the file
for a tool with a source (`built-in <factory>` for one without), and the namespaces that grant it directly. With none:
D3's `NO_TOOLS`. A row opens the editor; **+ New tool** opens it empty.

**The editor** (the spec's mock-up, as built):

```text
Tools › word_count                                                                         v1 · saved 3 Oct
Name     word_count                        how the agent calls it: a Python name, fixed once saved
Block    factory: make                     YAML: the factory's name and its parameters (factory_from is the Library's)
Source   1  from deep_reasoner import Func
         2
         3
         4  def make(client, params):
         5      def word_count(text: str) -> int:
         6          """Count the words in text."""
         7          return len(text.split())
         8
         9      return Func(word_count, description="word_count(text) -> int: number of words in text.")
Try      word_count("one two three")       optional: an expression Check evaluates with the tool bound
[Check]  ✓ builds (0.02 s). The agent is told:
           - `word_count(text: str) -> int`
             word_count(text) -> int: number of words in text.
         word_count("one two three") → 3
Granted in   ☑ course_advisor   ☐ router   ☐ health_advisor   ☑ root.archive (inherited from root)
How tools work ▸
[Save]   [Delete]
```

- **New tool** starts with the name empty, `factory: make` and the template above (`NEW_TOOL_SOURCE`, §9.3). The
  name is required, must be a Python identifier, not a keyword and not one of deep_reasoner's own REPL names
  (`RESERVED_NAMES`, §3.2), and cannot change after the first save (D2 §4.5: a new name is a new tool).
- **A built-in tool** (a block without `factory_from`: `rag`, `kg`, `llm` aliases, `safe_url`, `claude_code`) shows
  the block only; Check says whether the factory is one of deep_reasoner's (§3.3).
- **Check** sends `POST /tools/{name}/check {yaml, source, example}` with what is on screen (saved or not) and shows
  the report (§3.4): a ✓ with the time and what the agent is told, the tried value or its error, and, on a failure,
  deep_reasoner's sentence, the frames from the tool's own file, and the last 2,000 characters the tool printed.
- **Save** sends `PUT /tools/{name} {yaml, source, granted_in, base_version}`. The backend runs Check when the block
  or the source differs from the head (§3.5): "Checking and saving…". On `422 check_failed` the report is shown;
  when it allows it, **Save anyway** resends with `accept_check_failure: true` under `SAVE_ANYWAY_NOTE`. A `409`
  and a `422 invalid` are D3's (§5.2 there). Success: `SAVED_TOOL`.
- **Granted in** is D3's `NamespaceChecklist`: checked = the record's `granted_in`; a namespace that inherits the grant
  from an ancestor (from `GET /effective`'s `tools[].source`) is checked and fixed with "inherited from X". For a saved
  tool, a tick saves at once (D3 decision I): `PUT /tools/{name}` with the **head's** block and source, the new
  `granted_in` and the head's version, so a grant never carries unsaved, unchecked code and needs no Check. For a new
  tool, the ticks go with the first Save.
- **Delete** asks inline (`DELETE_TOOL_CONFIRM`), then `DELETE /tools/{name}?base_version=`; D2 removes it from every
  namespace's `tools`.
- **How tools work** folds open `TOOL_HELP` (§9.3): the factory contract, one file only (D2 §9 item 7), models through
  `client`, secrets read when called rather than built, `config_path` not passed (the spec's known gap B8), and the
  `kg` layer note (D2 §9 item 10).
- **The draft** (every field) is kept under `dr-library.draft.tool.<name>` (`.new` for a new one) with D3's
  `drafts.ts`, cleared by a save or **Discard draft**; a refetch never overwrites it (D3 §2.6).

**Failure cells**, deep_reasoner's own sentences where it has one (verified, header item 1):

```text
factory make_broken → ✗ tool 'word_count': make_broken in tools/word_count.py returned function, not a Func. A tool
                        factory returns Func(value, description=…) — the registry reads its `.value` (what the REPL
                        binds) and `.description` (what the agent is told).
                      Fix this before saving: a tool that does not build stops every conversation from starting.
factory mkae        → ✗ tool 'word_count': 'tools/word_count.py' defines no 'mkae'.
                        It defines: make, make_broken.
                        Known built-in factories: claude_code, kg, llm, rag, safe_url.
import yaml_x       → ✗ tool 'word_count': importing 'tools/word_count.py' raised ModuleNotFoundError: No module
                        named 'yaml_x'
a hanging factory   → ✗ tool 'word_count': building it took longer than 10 s, so Check stopped it. A tool is built
                        at the start of every conversation; a factory must return quickly.          [Save anyway]
os.environ['TOKEN'] → ✗ tool 'word_count': make raised KeyError: 'TOKEN'
                        File "tools/word_count.py", line 5, in make
                      Check could not build this tool here, where it has no secrets, no model and only its own
                      folder. If it builds in a conversation, save it anyway; if it does not, no conversation will
                      start until you fix it.                                                        [Save anyway]
def make(:          → ✗ tool 'word_count': tools/word_count.py line 1: '(' was never closed    (no process started)
```

### 2.2 MCP servers

The list joins Canvas's MCP settings (frame parameter `mcp`, §7.5) with the Library's grants (`GET /mcp`), one row
per server name:

| The server | The row |
|---|---|
| in Canvas's settings, given to the agent, not granted | its transport and target (command and arguments, or URL), "as `<name>`" (an editable REPL name, prefilled with `defaultToolName`, §8.5), and a namespace checklist all unticked |
| granted | the same with its grants ticked (D3's `NamespaceChecklist`, inherited grants fixed); below it, the last seen tools (`MCP_SEEN`, folding open to exactly what the agent was told) or `MCP_NOT_SEEN` |
| granted, and Canvas's command, arguments, URL, transport, environment or header names differ from the snapshot | `MCP_CHANGED` with **Update** |
| granted with a shim older than this deep-reasoning's | `MCP_SHIM_OLD` with **Update** |
| disabled in Canvas's settings | `MCP_DISABLED`; its checklist still works (a grant waits for the server to be enabled) |
| left out by the `deep_reasoner` profile's `mcp_server_refs` | `MCP_NOT_IN_PROFILE`; the same |
| granted, not in Canvas's settings any more | `MCP_GONE` with **Remove** |
| Canvas's settings could not be read (`mcp` is null) | the grants only, under `MCP_SETTINGS_UNKNOWN`; no new grant can be made |

- **A first tick** sends `PUT /mcp/{name}` with the server's name, transport, command, arguments, URL, environment
  variable names and header names (never a value; the page never reads one, §7.5), `granted_in: [that namespace]`,
  `base_version: 0`. The backend writes the block and the shim (§4.2). `409`: the REPL name is taken by another tool
  ("a tool named 'github' exists: choose another name") or the server is already granted under another name.
- **Later ticks** resend the **stored** snapshot with the new `granted_in` and the grant's version (no new tool
  version, D2 §4.5's "unchanged is not a save"). **Update** resends Canvas's current settings (or regenerates an old
  shim): a new version. Unticking every namespace keeps the row with no grants; **Remove** deletes it
  (`DELETE /tools/{name}?base_version=`).
- `MCP_EXPORT_NOTE` sits under the list: an export keeps each server's command, arguments and URL, never an
  environment or header value.

**In the conversation.** A granted server that a conversation's run could not bind is said once, ahead of the first
answer, as a root `agent_message_chunk` (the same form as D1's fresh-run notice), and is in the run log, so it replays:

```text
⚠ MCP server 'postgres' did not answer within 10 s; its tools are not bound in this conversation.
⚠ MCP server 'slack' is granted to router in the Library, but this conversation was not given it: enable it in
  Canvas's MCP settings. Its tools are not bound.
⚠ MCP server 'wiki' could not be started (McpError: Connection closed; it printed: "invalid token [redacted]");
  its tools are not bound in this conversation.
```

**What the agent is told** (deep_reasoner renders the binding, `v2/messages.py:216–224`; the rest is the shim's
description, §8.4):

```text
- `github(tool, /, **arguments)`
  MCP server 'github' (stdio): call a tool as github.<tool>(…) or github("<tool name>", **arguments); a failed call
  raises McpToolError.
  github.search_issues(query: str, repo: str, page: int = …) -> dict
    Search issues in a repository.
  github.get_file_contents(owner: str, repo: str, path: str) -> str
    Get the contents of a file or directory.
```

---

## 3 · Check

### 3.1 What it answers

"Will this tool build when a conversation starts, and what will the agent be told?" Check answers it by doing what
a run does, in a process of its own, minus what only a conversation has: the user's secrets, a model, the
conversation's folder. It answers in about two seconds for a tool that builds (most of it deep_reasoner's import,
1.4–3 s measured) and within its limits for one that does not.

### 3.2 Before any process: the static stage

In the backend, in this order, each failure ending Check:

1. **Shape**: D2's `shapes.validate_tool(name, yaml, source)` (the block is a mapping, `factory_from` absent or
   `tools/<name>.py`, a name that is an identifier). Failure → outcome `invalid`, D2's message and field errors.
2. **Name**: not in `RESERVED_NAMES` = `subagent`, `run_all`, `FinalAnswer`, `Var`, `Func`, `task`. A namespace's
   tools are bound over the agent's framework tools by name (`v2/agent.py:647, 675`), so a tool called `run_all`
   would replace deep_reasoner's own. `llm` is not reserved: deep_reasoner lets a user's own factory be called `llm`
   (`v2/cli.py:154–155`). Failure → `invalid`, `RESERVED_NAME`.
3. **An MCP grant's block** (`factory: mcp_server`): refused here (`MCP_VIA_GRANT`); grants are written by
   `PUT /mcp/{name}` (§4.2).
4. **A block without a source**: its factory (default: the tool's name) is `llm` or a key of deep_reasoner's
   `TOOL_BUILDERS` → `builtin` (✓; not built, because a built-in needs the model and the data a conversation has);
   otherwise `bad_factory` with `make_tools`' own sentence (`v2/cli.py:171–176`), copied into `texts.py` and pinned by
   a test. No process starts.
5. **Syntax**: `compile(source, f"tools/{name}.py", "exec")`. A `SyntaxError` → `syntax`, with its line. No process
   starts.

### 3.3 The throwaway process

```text
tmp = mkdtemp("dr-check-")                                     (0700, under the backend's TMPDIR)
tmp/config/main.yaml       {client: {base_url: "http://127.0.0.1:9/v1", max_retries: 0},
                            tools: {<name>: <the canonical block, factory_from: tools/<name>.py>}}
tmp/config/tools/<name>.py the source, byte for byte
tmp/printed.txt            the child's stdout and stderr, both
Popen([sys.executable, "-m", "deep_reasoning.tools.check_child", "--report-fd", W, "--name", <name>,
       ("--example", <expression>)?, "tmp/config/main.yaml"],
      cwd=tmp/config, env=check_env(os.environ), stdin=DEVNULL, stdout=stderr=printed.txt,
      pass_fds=(W,), start_new_session=True)
```

- **Python** is `sys.executable` of `dr-library serve`, which under D5 is the runtime's (`runtime/current`, D5
  decision C), the same interpreter and deep_reasoner as every `dr-acp` worker.
- **Environment** (`check_env`): `PATH`, `LANG`, `LC_ALL`, `LC_CTYPE`, `TMPDIR`, `TZ` as the backend has them (the six
  the agent-server gives an App backend); `HOME`, `USER`, `LOGNAME` from the password database (code that reads
  `os.environ["HOME"]` works); `PYTHONUNBUFFERED=1`, `PYTHONDONTWRITEBYTECODE=1`. No key, no Canvas secret, no
  `DR_HOME`.
- **The model**: the config's client points at port 9 on loopback with no retries, so `build_client` needs no key
  (`config.py:256–262`) and any model call fails at once with a connection error. Check never reaches a model.
- **Working directory**: the materialized config folder, so deep_reasoner's messages name `tools/<name>.py` as the
  spec's mock-up does, and anything the tool writes is removed with the folder.
- **Its own process group**, so a limit or the end of Check kills whatever the tool started.

**The child** (`check_child.py`) reports JSON lines on the report fd, never on stdout, which the tool may print to:

```text
import deep_reasoner's config loader, V2Config, load_tool_factory, Func, func       → {"phase": "ready"}
cfg = load_cli_config(main, schema=V2Config); block = cfg.tools[name]
params = block minus factory and factory_from          (as make_tools passes them: no config_path, the spec's B8)
factory = load_tool_factory(name, block["factory"], block["factory_from"], cfg.config_path)
   ValueError with an ImportError cause      → {"phase": "failed", "outcome": "import_failed", "message": str(exc)}
   ValueError with any other cause           → "raised"       (the module raised while importing)
   ValueError without a cause                → "bad_factory"  (defines no …, or not a function)
                                                                                    → {"phase": "loaded"}
started = monotonic(); built = factory(build_client(cfg.client), params)
   any exception                             → "raised", FACTORY_RAISED, the traceback's frames in tools/<name>.py
   not isinstance(built, Func)               → "not_func", make_tools' sentence (NOT_FUNC, copied and pinned)
→ {"phase": "built", "told": func(name, built.value, built.description).describe(), "seconds": …}
example: eval(compile(expression, "<try>", "eval"), {name: built.value})
→ {"phase": "example", "ok", "value": repr(result)[:2000] | null, "error": "Type: message" | null, "seconds"}
→ {"phase": "done"}; exit 0
```

**The supervisor** (`check.py`) reads the report fd with deadlines and kills the group at the first one missed:

| Phase awaited | Limit (`CheckLimits`) | Missed → outcome |
|---|---|---|
| `ready` after start | `ready_s` = 30 s (deep_reasoner's import on a cold disk) | `unavailable`, `READY_TIMEOUT` |
| `built` or `failed` after `ready` | `build_s` = 10 s (importing the tool's file and calling its factory) | `timeout`, `BUILD_TIMEOUT` |
| `example` after `built` | `example_s` = 10 s | the example's error: `EXAMPLE_TIMEOUT`; the build stays ✓ |

The child exiting without a final line is `unavailable` (before `ready`) or `raised` (after it), with how it ended
(`CHILD_ENDED`: its exit code or signal). After the last line, or a missed limit, the supervisor sends `SIGKILL` to
the group **before** reaping the child (an unreaped child keeps its pid, so the group id cannot have been reused),
then waits, then removes `tmp`. So Check answers within the limit it reports, plus well under a second, and leaves no
process behind (§10.2).

### 3.4 What it reports

`CheckReport` (Appendix A.1): `ok`; `outcome`; `message` (deep_reasoner's sentence where it has one, else §9.1's);
`told` (deep_reasoner's own rendering, verbatim); `traceback` (for `raised`: the frames in the tool's own file and
the exception line, at most 2,000 characters); `example`; `printed` (the last 2,000 characters of what the tool
printed); `seconds` (load and build); `deep_reasoner` (the build that checked it, D2's `deep_reasoner_build()`);
`can_save`; `can_save_anyway`.

| Outcome | `ok` | Save | Why |
|---|---|---|---|
| `built`, `builtin` | yes | yes | |
| `invalid`, `syntax`, `import_failed`, `bad_factory`, `not_func` | no | no | the same runtime would fail the same way in every conversation |
| `raised`, `timeout`, `unavailable` | no | anyway, explicitly | the tool may need what only a conversation has (a secret, its folder, a slow network), or Check itself did not start |

`POST /tools/{name}/check` always answers 200 with the report (as D2's `/validate` does); the bridge sets no read
timeout on App-backend requests (`bridge.py:467–472`, `proxy.py:96–97`), so a 50 s worst case passes through.

### 3.5 The gate on saving

D2's `PUT /tools/{name}` endpoint calls `require_check(lib, name, yaml, source, accept_failure=…)` before
`lib.put_tool`:

```text
the YAML does not validate                     → nothing here: lib.put_tool raises D2's 422 invalid as before
an MCP grant's block                           → 400 MCP_VIA_GRANT
canonical block and source equal the head's    → nothing to check (a grant-only change; D2 then writes namespaces only)
otherwise: report = check_tool(name, yaml, source)          (no example)
   report.can_save                                           → save
   report.can_save_anyway and accept_check_failure is true   → save
   else                                                      → 422 {"error": "check_failed", "message": CHECK_FAILED,
                                                                    "check": report}
```

Only the HTTP API is gated: `Library.put_tool` (Python) and `dr-library import` are not, so an imported tool can be
broken; the editor's Check finds it, and §14 item 4 proposes a check after upgrades.

---

## 4 · MCP servers

### 4.1 From Canvas's settings to `dr-acp`

OpenHands holds MCP servers in its settings (`agent_settings.mcp_config`, a map from name to `MCPServer`,
`mcp/config.py:497–533`), filtered for a conversation by the agent profile's `mcp_server_refs` (`null`: all;
`profiles/resolver.py:160–168`). At ACP session start the bridge turns every enabled one into an ACP `mcpServers`
entry (`_mcp_config_to_acp_servers`, `acp_agent.py:739–821`, called at `:3114` for `session/new` and again for
`session/load`): stdio always, with its environment as `[{name, value}]` in plain text; HTTP and SSE only when the
agent advertises `mcpCapabilities.http` / `.sse`, with headers in plain text. **D4 flips both flags to true** in
`dr-acp`'s `initialize` (D1 §4.8 left them false).

`dr-acp` already keeps the forwarded list on the session (`Session.mcp_servers`, D1 §4.8; refreshed on `session/load`).
At a run's start (the first message, or the first after a fresh-run reset) the front:

1. materializes the run (D1, unchanged);
2. reads the run's `main.yaml` (plain YAML, no deep_reasoner import) for MCP blocks and the server names they carry
   (`servers_named`);
3. converts the forwarded entries it names into `McpServerSpec`s (`forwarded_specs`: stdio has no `type` key in ACP
   0.12.1, HTTP `"http"`, SSE `"sse"`; anything else is ignored) and puts them in `Start.mcp_servers`, over the
   control pipe, never in the worker's environment. Steps 2 and 3 are one function, `specs_for_run(forwarded,
   config_path)`.

Servers that no Library grant names are never sent to the worker: their secrets stay in the front.

### 4.2 A grant in the Library

`PUT /mcp/{name}` (`name`: the REPL name, an identifier; D4's route, §7.2) writes one D2 tool row:

```yaml
# block (canonical YAML; D2 adds factory_from)          # http or sse instead of stdio:
factory: mcp_server                                     # transport: http
factory_from: tools/github.py                           # url: https://db.lab.example/mcp
name: github                                            # headers:
server: github                                          #   Authorization: POSTGRES_AUTHORIZATION
transport: stdio
command: npx
args:
- -y
- '@modelcontextprotocol/server-github'
env:
- GITHUB_PERSONAL_ACCESS_TOKEN
```

- `name` repeats the row's key because `make_tools` does not pass a factory its alias (`v2/cli.py:152`), and the shim
  must know the name it is bound under. `server` is the key in Canvas's settings. `env` lists names only; `headers`
  maps each header to the environment variable `dr` will read it from (`header_env_name`, §8.5). Optional
  `connect_timeout_s` (default 10) and `call_timeout_s` (default 120) are honoured if present; the panel never writes
  them, tests do.
- `source` is `shim_source()`: the text of `deep_reasoning/mcp/shim.py` in the installed package. Its first line is the
  marker `# deep-reasoning MCP shim, version 1. …`; a row is an MCP grant when its block's factory is `mcp_server`
  and its source starts with the marker (`is_mcp_tool`), which also holds for an export re-imported.
- Refused: a server already granted under another name (`409 refused`, `MCP_SERVER_TAKEN`); stdio without a command,
  HTTP or SSE without a URL (`400`); the name rules of §3.2 (`422 invalid`).
- `GET /mcp` lists every grant as an `McpGrant` (Appendix A.2): the snapshot, `granted_in`, `version`,
  `shim_current` (the source equals today's shim) and `seen` (§4.7).

### 4.3 The shim

`deep_reasoning/mcp/shim.py` is the factory file of every grant, self-contained (decision J). Its module level imports
only the standard library; `mcp` and `deep_reasoner.primitives.Func` are imported where used.

**The factory**, `mcp_server(client, params) -> Func`:

```text
SESSION = the package module's SESSION, if `from deep_reasoning.mcp import shim` succeeds, else None
SESSION is not None (a dr-acp worker installed it)
    → SESSION.get(params["name"]) or a stand-in (NOT_IN_SESSION)            no connection is made here
SESSION is None (plain dr, an export, or deep-reasoning not installed)
    spec, missing = spec_from_block(params, os.environ)     env and header values from the environment
    import mcp fails                                         → a stand-in (NO_MCP_PACKAGE)
    connection = Connection(spec, errlog=sys.stderr); start; wait_ready(connect_timeout_s)
    ready                                                    → Func(Server(name, connection, granted=None), describe(…))
    otherwise                                                → a stand-in (NO_ANSWER / COULD_NOT_START, naming missing
                                                               variables); a structlog warning mcp.unavailable
```

**`Connection`**: one server, on a daemon thread running its own event loop (verified, header item 3):

```text
_serve():  async with transport(spec) as streams:              stdio: stdio_client(StdioServerParameters(
                                                                  command=sys.executable,
                                                                  args=["-I", this file, "--guard", "--", command, *args],
                                                                  env=spec.env), errlog=…)
                                                               http:  streamable_http_client(url, http_client=
                                                                  httpx.AsyncClient(headers=spec.headers, …))
                                                               sse:   sse_client(url, headers=spec.headers)
               async with ClientSession(read, write) as session:
                   await session.initialize()
                   tools = every page of session.list_tools()
                   ready (threading.Event)
                   await stop (asyncio.Event)
           any exception → failure = the innermost exception, "Type: message"; ready
call(tool, arguments): run_coroutine_threadsafe(session.call_tool(tool, arguments,
                           read_timeout_seconds=call_timeout_s), loop).result(call_timeout_s + 5)
abandon(): loop.call_soon_threadsafe(task.cancel)   (mcp then closes stdin and ends the guard's group)
```

A stdio server's environment is what Canvas's settings give it plus the six variables `mcp` adds itself (`HOME`,
`LOGNAME`, `PATH`, `SHELL`, `TERM`, `USER`, `client/stdio/__init__.py:28–66`); it never inherits the worker's. Its
working directory is the worker's: the conversation's folder (ACP carries no `cwd` for a stdio server).

**What the REPL binds** (`Server`): a callable object named after the grant (`__name__ = name`), so deep_reasoner
renders it as `` `github(tool, /, **arguments)` ``. Each MCP tool whose name, with every character that cannot be in a
Python name replaced by `_`, is an identifier, not a keyword and not already taken is also an attribute (an `McpTool`),
so `github.search_issues(…)` works; every tool is callable by its exact name, `github("get-file", path="x")`.
`McpTool(*args, **kwargs)` maps positional arguments onto the parameters in the order `describe` prints them; a
surplus positional argument is a `TypeError`. The return value (§8.3) is the unwrapped result, a dict, text, or the
content blocks; a failed call raises `McpToolError`. `Server` and `McpTool` return themselves from `__copy__` and
`__deepcopy__`, because deep_reasoner's `fork` deep-copies the REPL (`repls/backends.py:105–140`) and a connection is
shared, not copied. They implement `__cross_namespace__(src, dst)`: with a grant set (in `dr-acp`), a hand-off into a
namespace outside it raises `PermissionError` (`HANDOFF_REFUSED`, the same kind of refusal `safe_url` makes,
`tools/safe_url.py:86–96`); the first bind (`src is None`) always passes, because deep_reasoner binds a tool only in a
namespace that resolves it.

**The stand-in** (`Unavailable`): calling it, or any attribute of it, raises `McpToolError` with its reason; its
description is `UNAVAILABLE` (the same reason), so the agent is told before it tries.

### 4.4 Session start, in the worker

`Worker.build` (D1 §4.3 step 3), after `load_dr_config` and the namespace and client overrides, before
`build_reasoner`, calls `open_session(cfg, start.mcp_servers, run_dir=run_dir)` (`deep_reasoning/mcp/session.py`):

```text
blocks    = {alias: block for alias, block in cfg.tools.items() if block.get("factory") == "mcp_server"}
none      → shim.SESSION = {}; return []
registry  = build_namespace_registry(cfg)
names     = root, every namespace of namespaces_dir (load_namespaces_from_dir) and of cfg.namespaces
granted   = {alias: {ns in names: alias in registry.resolve(ns).tools}}          deep_reasoner's own resolution
reach     = the closure of {cfg.entry_namespace} under check_spawn(registry, src, dst) succeeding
registry.close()
for each alias (all started at once):
    no namespace grants it                → skipped   "granted to no namespace"           (no notice)
    granted ∩ reach is empty              → skipped   "granted only where this conversation cannot spawn"
    no forwarded spec for block["server"] → not_enabled                                  (a notice)
    else Connection(spec, errlog=runs/<run>/mcp-<alias>.log, call_timeout_s=…).start()
wait every started one against one deadline: now + the largest connect_timeout_s (10 s)
    ready, no failure → bound        told = deep_reasoner's func(alias, server, description).describe(); count
    ready, failure    → failed       detail = failure + the log's last 300 characters, every secret value of that
                                     server's spec (env and header values of 4+ characters) replaced by [redacted]
    not ready         → no_answer    connection.abandon()
shim.SESSION = {alias: Func(Server(…, granted=frozenset(granted[alias]))) | a stand-in, for every block}
return a McpServerStatus per block
```

The worker emits `mcp.status {servers: [...]}` (a new RunEvent, §7.3) when there is any MCP block, then builds.
`make_tools` then calls each MCP block's factory, which returns `SESSION[alias]` without connecting (§4.3).

**Timing.** `session/new` never waits on a server (D1 builds nothing there). The first answer waits at most the
deadline (10 s) on a silent server, and about one server start (1.2 s for a Python FastMCP server, header item 3) when
all answer, overlapped with nothing else the worker does: deep_reasoner's import has already happened (`load_dr_config`).
The front's heartbeat (D1 §4.2) keeps the bridge's idle watchdog quiet meanwhile.

### 4.5 When a server fails

| When | What happens | What the user sees |
|---|---|---|
| it is not forwarded | not started; stand-in bound | `MCP_NOT_ENABLED` once, before the first answer |
| it exits or errors before answering | `failed`, with its stderr's tail, redacted; stand-in bound | `MCP_FAILED` |
| it does not answer by the deadline | `no_answer`; abandoned (stdin closed, its guard's group ended by `mcp`); stand-in bound | `MCP_NO_ANSWER`, the spec's sentence |
| a call returns `isError` | `McpToolError("{name}.{tool} failed: {text}")` in the cell | the cell's output |
| a call does not answer within `call_timeout_s` (120 s) | `McpToolError(CALL_TIMEOUT)`; the request is abandoned; the server stays | the cell's output |
| it dies during the run | the call in flight fails (`McpError: Connection closed`, verified); the connection is marked dead with that reason and every later call raises `SERVER_STOPPED` at once; nothing restarts it before the next run | the cell's output |

None of these reaches the worker's main thread except as an exception in the calling cell, and a server is another
process, so a server cannot take the worker down (E9). Because a dead connection's own task does not notice (header
item 3), `Connection.call` marks it dead on `McpError` "Connection closed" and on `anyio.ClosedResourceError`,
`BrokenResourceError` and `EndOfStream`.

### 4.6 How a server ends

- **The run ends normally** (Close, a failed prompt): the worker exits (D1 §4.3 step 5); each stdio server's stdin
  closes with it, a well-behaved server exits, and its guard follows.
- **The worker is killed** (root Stop, D1's 0.8 s grace then `SIGKILL` to its group; the front dying, after which the
  worker kills its own group): the servers are not in that group (`mcp` puts each in a session of its own), so each
  guard sees its parent's pid change within 0.5 s and sends `SIGKILL` to its own group (verified, header item 2).
- **A server given up at start**: `abandon()` cancels its task; `mcp` closes its stdin, waits 2 s and ends its process
  tree (`client/stdio/__init__.py:180–210`), while the run goes on.

**The guard** (`python -I shim.py --guard -- <command> <args…>`): remember `os.getppid()`; start the command with
`subprocess.Popen` (same stdin, stdout, stderr, process group and environment); a daemon thread polls `os.getppid()`
every 0.5 s and `os.killpg(0, SIGKILL)` when it changed; exit with the command's exit code. It compares with the
original parent, not with 1, so a subreaper (systemd's user manager, the desktop app) changes nothing. One extra
Python process per stdio server, about 30 ms to start, standard library only. `-I` (isolated mode) keeps the shim's
own folder off `sys.path`, so a sibling module there (`wire.py`, `session.py`) can never shadow a standard-library
one the guard imports, and keeps `PYTHON*` variables of the server's environment from changing the guard.

### 4.7 What the panel learns of a server's tools

When the pump logs an `mcp.status`, the front writes, for each `bound` server, `$DR_HOME/mcp/<first 16 hex of
sha256(server name)>.json` = `{"v": 1, "server", "tool", "transport", "at", "run", "count", "told"}`, atomically
(a temporary file, then `os.replace`; mode 0600 in a 0700 directory). `GET /mcp` reads it for each grant (`seen`),
from the Library's own home (`library.path.parent`). It holds tool names and descriptions, never a secret. Replays
(`session/load`) do not write it.

### 4.8 Under plain `dr`, on an export

`dr <export>/main.yaml …` with the `mcp` package installed: each MCP block's factory connects from its snapshot (§4.3),
reading each `env` name and each header's variable from `dr`'s environment, one block after another inside
`make_tools` (each up to its connect timeout); a server it cannot reach becomes a stand-in and a structlog warning, and
the run goes on. No grant set is known there, so a hand-off is not refused (deep_reasoner's ordinary rule). Without
`mcp` installed the run still starts and the stand-in says `pip install mcp`.

---

## 5 · What a tool or a server can reach

Said plainly, as the spec asks; the Tools tab says the short form (`TOOLS_RISK`), under D5's `SAFETY`.

- **A tool you write** is Python that runs as you, inside the agent's worker process: when every conversation starts
  (its factory) and whenever an agent calls it. It can read and change any file you can (the conversation's folder is
  only the working directory, D5 §2.2), reach any host your machine can, read the worker's environment (the key
  proxy's tokens under your keys' names, which work only through the proxy and up to the spend cap, D5 §4.7; and your
  other Canvas secrets, which D5 leaves there on purpose), call the model through the `client` it is given (through
  the proxy, so counted against the cap), and touch everything else in the worker's memory: the REPL's variables,
  other tools, and the environment and header values of every MCP server granted in that conversation.
- **Check runs your code too**, as you, in the App backend's child process: without your secrets or a model, with the
  disk and the network.
- **A stdio MCP server** is a program `dr-acp`'s worker starts as you, for each conversation one of whose reachable
  namespaces is granted it, with exactly the environment Canvas's settings give it plus `HOME`, `LOGNAME`, `PATH`,
  `SHELL`, `TERM`, `USER`, in the conversation's folder. It can do anything a program of yours can: the whole disk,
  the network. It does not get the key proxy's tokens or your keys unless its settings name them; then E10's
  property (D5 §2.1, "not in any process the worker starts") does not hold for it, by your configuration (§11.4).
- **An HTTP or SSE server** runs elsewhere; it gets the headers Canvas's settings give it and the arguments the agent
  sends it. What it does with them is its operator's business.
- **A grant is not a sandbox.** It decides which namespaces' agents are given a tool or a server, and `dr-acp` refuses
  to hand a server to a sub-agent outside its grants. It does not stop code: any cell in any namespace can start any
  program you can, read Canvas's settings file and its key (D5 §2.2), or call a server's results it was passed.
- **The Library and its exports** hold your tools' sources and each granted server's command, arguments and URL (with
  anything you typed into them), never an environment or header value. The frame's URL carries the same non-secret
  fields (§7.5).

---

## 6 · Where this design departs from, or adds to, the approved spec

Each is a refinement inside D4's scope unless it says otherwise; if the Conductor reads any as a change of what was
approved, it goes back to Michael.

1. **Saving through the panel runs Check, and refuses a tool that cannot build** (§3.5); failures Check cannot
   attribute can be saved anyway, explicitly. The spec has Check as a button that shows the result. Reason: every
   tool block is built in every conversation, so one broken tool stops all of them (decision C).
2. **Check runs without your secrets, without a model and in its own folder** (§3.3), with limits of 30, 10 and 10 s,
   and never reaches a model. The spec says "a throwaway process" and "a time limit".
3. **Six names are refused for new tools and grants** (`RESERVED_NAMES`, §3.2): deep_reasoner would let a tool hide
   its own `run_all` or `subagent`. A config imported with such a name still imports.
4. **"At session start" is when the conversation's run is built**, at its first message: D1 starts the worker there
   (D1 §2 step 4), so the servers are connected there, all at once, within one 10 s deadline, and the notice appears
   ahead of the first answer. The spec's sentence is kept.
5. **Grants follow deep_reasoner's namespace rules** (decision G): a grant to `a` reaches `a.b`; a sub-agent spawned
   into a granted namespace gets the server even when the conversation began elsewhere; a run starts every server
   granted to a namespace its agents can reach. The spec says "binds only the servers granted to the conversation's
   namespace"; read per agent, no agent outside a granted namespace ever gets a server's tools, which is E9's null.
6. **Handing a server to a sub-agent in a namespace not granted it is refused** in `dr-acp` (an addition that makes
   E9's null hold for explicit hand-offs too); under plain `dr` deep_reasoner's ordinary hand-off applies.
7. **A server that is not bound leaves a stand-in under its name** (decision H) that tells the agent why; none of its
   tools is bound. The spec's sentence "its tools are not bound in this conversation" stays true.
8. **A grant snapshots the server's non-secret settings for export**, and under `dr` its environment and header
   values come from environment variables (§4.2, §4.8). The spec says an export "still runs under `dr` with the `mcp`
   package installed"; it also needs the server's secrets in the environment.
9. **Each stdio server runs under a guard process** (decision I), because `mcp` detaches it from the worker's process
   group and a silent server otherwise outlives a killed worker (verified).
10. **The panel shows a server's tools as the last conversation saw them** (decision K); it cannot connect a server
    itself.
11. **D4's change to `dr-acp` is about 90 lines in D1's files, not 30** (§11.1): a RunEvent, its encoding and three
    sentences, the specs' filter, and the seen cache.
12. **`mcp>=1.28,<2` becomes a runtime dependency of deep-reasoning** (the spec named it as a candidate); 1.28 is the
    first with `streamable_http_client(url, http_client=…)` and the SDK fork's lock.
13. **CodeMirror for the source field only** (decision L); D3 departed from the spec's React and CodeMirror; D4 brings
    CodeMirror back where the spec's Q6 costed it.
14. **Size: about 2.0k lines of code and 2.2k of tests**, about 14 h at Gate C, against the spec's ≈1.0k with tests and
    ≈3 h (§13).

The spec's known gap B8 (`factory_from` builders do not receive `config_path`) is mirrored by Check, so Check and a
run agree, and is stated in `TOOL_HELP`; not worked around, as the spec says.

---

## 7 · Modules

### 7.1 Files

```text
src/deep_reasoning/tools/                 D4: your own tools
    __init__.py                           docstring only
    check.py                              check_tool, check_env, require_check, ToolCheckFailed, CheckReport (§3)
    check_child.py                        python -m deep_reasoning.tools.check_child (§3.3)
    routes.py                             tool_routes(library): POST /tools/{name}/check, GET /mcp, PUT /mcp/{name}
    texts.py                              D4's backend sentences (§9.1)
src/deep_reasoning/mcp/                   D4: MCP servers
    __init__.py                           docstring only; imports nothing (the shim imports this package)
    shim.py                               the factory_from shim and the guard; standard library at module level (§4.3)
    wire.py                               McpServerSpec, McpServerStatus, specs_for_run, redact,
                                          the seen cache (pydantic and yaml only: the front imports it)
    grants.py                             McpGrantBody, McpGrant, McpSeen, mcp_block, shim_source, is_mcp_tool,
                                          grant_record, header_env_name (the backend's side)
    session.py                            open_session (the worker's side; imports deep_reasoner)
src/deep_reasoning/acp/…                  D1's files: §11.1's changes
src/deep_reasoning/library/api.py         D2's: §11.2's changes
canvas-app/src/…                          D3's project: §7.5
tests/tools/                              test_check.py, test_routes.py, test_live.py, fixtures/ (§10)
tests/mcp/                                test_wire.py, test_grants.py, test_shim.py, test_session.py, test_acp.py,
                                          test_export.py, test_live.py, servers/ (fake MCP servers, run as scripts)
tests/canvas_app/test_tools_tab.py        D3's file, D4's tests added (§10.4)
pyproject.toml                            dependencies += "mcp>=1.28,<2"
```

`tests/mcp/` is the package `tests.mcp` (`tests/__init__.py` exists, D1), so it never shadows the `mcp` library; the
servers under `tests/mcp/servers/` run as scripts.

### 7.2 `tools/routes.py`: the routes D4 adds to the App backend

`create_app` (D2) appends `*tool_routes(lib)` to its routes, after D3's `*ui_routes()`; D2's guard (same user, `Host`,
JSON) covers them.

| Method and path | Body | Answer |
|---|---|---|
| `POST /tools/{name}/check` | `{"yaml", "source"?, "example"?}` | `CheckReport`, always 200 |
| `GET /mcp` | | `[McpGrant]`, in `GET /tools` order |
| `PUT /mcp/{name}` | `McpGrantBody`: `{"server", "transport", "command"?, "args"?, "url"?, "env"?, "headers"?, "granted_in", "base_version"}` | `McpGrant`, 201 or 200; 400 (a stdio grant without a command, a remote one without a URL); 409 `conflict` (D2's, carrying the head) or `refused` (`MCP_SERVER_TAKEN`); 422 `invalid` |

`PUT /mcp/{name}`: validate the body; refuse a server another grant already names; `lib.put_tool(name,
canonical_yaml(mcp_block(name, body)), source=shim_source(), granted_in=body.granted_in,
base_version=body.base_version)`; answer `grant_record(record, read_seen(home, body.server))`. Removing a grant is
D2's `DELETE /tools/{name}`.

### 7.3 The worker, the run log and the encoder (in D1's files)

- `worker/protocol.py`: `Start.mcp_servers: list[McpServerSpec] = []`.
- `worker/runner.py`: `build` calls `open_session` and emits `mcp.status` (§4.4).
- `runlog.py`: `McpStatus` (`kind: "mcp.status"`, `servers: list[McpServerStatus]`) joins the `RunEvent` union.
- `encoder.py`: `McpStatus` → one root `agent_message_chunk` per server whose state is `no_answer`, `failed` or
  `not_enabled`, text `mcp_notice(status) + "\n\n"`, in both modes and on replay; nothing for `bound` or `skipped`.
- `supervisor.py`: `RunHandle.start(…, mcp_servers=…)` passes them in `Start`; the pump, after logging an `McpStatus`
  that is not a replay, calls `remember_seen(home, run_id, servers)`.
- `session.py`: `_start_run` computes the specs (§4.1) in the same `asyncio.to_thread` as the materialize.
- `agent.py`: `mcpCapabilities: {"http": True, "sse": True}`.
- `texts.py`: `mcp_no_answer`, `mcp_failed`, `mcp_not_enabled` (§9.2).

### 7.4 The frame (`canvas-app/src/`, D3's project)

```text
shared/protocol.ts       FrameParams.mcp: McpServerInfo[] | null; frameSearch and readFrameParams carry it (JSON)
page/context.ts          readMcpServers(request), mcpServersFromSettings(…)
page/mount.ts            step 2 reads readMcpServers only when tab === "tools"
ui/types.ts              CheckOutcome, ExampleResult, CheckReport, McpTransport, McpSeen, McpGrant
ui/api.ts                checkTool, getMcp, putMcp; ToolBody.accept_check_failure; CheckBody, McpGrantBody
ui/tools.ts              pure logic: splitTools, defaultToolName, mcpRows, snapshotOf, inheritedGrants, toolDraftKey
ui/editor/python.ts      CodeMirror 6, Python, loaded by import(): createPythonEditor(parent, value, onChange)
ui/components/CodeField.tsx   (D3's) language "python" → the editor chunk; on a load failure, D3's textarea
ui/components/ToolEditor.tsx, CheckResult.tsx, McpServerRow.tsx
ui/tabs/tools.tsx        D3's file, extended: banner, risk line, your tools, MCP servers
ui/texts.ts              D4's sentences (§9.3)
vite.config.ts           inlineDynamicImports: false; chunkFileNames "assets/[name].js"; manualChunks {editor: CodeMirror}
```

CodeMirror packages, as runtime dependencies: `@codemirror/state`, `@codemirror/view`, `@codemirror/commands`
(`defaultKeymap`, `history`, `indentWithTab`), `@codemirror/language` (`syntaxHighlighting`, `defaultHighlightStyle`,
`indentOnInput`, `bracketMatching`), `@codemirror/lang-python`. Budget: `assets/editor.js` at most 300 KB minified;
`assets/app.js` stays under D3's 250 KB. The chunk's name is fixed, so `ui_routes` serves it like any built asset and
D3's `test_the_committed_build_is_complete` adds it to its list.

### 7.5 Canvas's MCP settings in the frame

`readMcpServers(request)` runs in the page (Canvas's realm), beside D3's reads, and only for the Tools tab:

- `GET /api/settings` without `X-Expose-Secrets`, so every secret comes back as `"**********"`
  (`settings_router.py:113–177`, `mcp/config.py:64–74`), and `GET /api/agent-profiles/deep_reasoner`, in parallel.
- `mcpServersFromSettings(agent_settings.mcp_config, profile.mcp_server_refs)`: for each entry, `transport` =
  `stdio` when it has a `command`, `sse` when it has a `url` and `transport` is `"sse"`, otherwise `http` when it has
  a `url` (the bridge's own rule, `acp_agent.py:774–797`), otherwise the entry is skipped; `env` and `headers` are
  the **keys** of those maps (a value is never copied); `forwarded` = `enabled !== false` and (`refs === null` or the
  name is in `refs`); `why_not` = `"disabled"` or `"not_in_profile"`.
- Either request failing → `null` (D3's tolerance).

The list rides in the frame's URL as the `mcp` parameter (D3 §8.3). It carries commands, arguments and URLs, which a
user may have put a token into; they are already stored unencrypted in Canvas's settings, and the URL stays on the
machine (§14 item 3).

---

## 8 · Algorithms

### 8.1 Classifying a Check

§3.3's child. The one subtle line is the import: `load_tool_factory` wraps every failure of `exec_module` in a
`ValueError` raised `from` the original (`tools/base.py:380–385`) and raises its "defines no" and "not a function"
`ValueError`s without a cause (`:388–406`). So `__cause__` is the classifier: an `ImportError` (and so
`ModuleNotFoundError`) is `import_failed`, which the same runtime would fail in every conversation; any other cause
is `raised` (the module did something at import that may depend on the conversation, such as reading a variable);
no cause is `bad_factory`.

### 8.2 Connecting at once, giving up at once

§4.4. Every `Connection.start()` is called before any wait; then `ready.wait(max(0, deadline - monotonic()))` in turn,
which costs the longest wait, not their sum. A server given up is `abandon()`ed and forgotten: its cleanup runs on its
own thread while the run proceeds.

### 8.3 A call's result

```text
result.isError                                       → raise McpToolError("{name}.{tool} failed: " + its text)
result.structuredContent is not None
    outputSchema's properties are exactly {"result"} and structuredContent's keys are {"result"}
                                                     → structuredContent["result"]   (the Python SDK's wrapper, verified)
    otherwise                                        → structuredContent (a dict)
every content block is text                          → their texts joined by "\n" (a str; never parsed as JSON)
otherwise                                            → [block.model_dump(mode="json") for each block] (images, resources)
```

### 8.4 The description

```text
line 1:  MCP server '{server}' ({transport}): call a tool as {name}.<tool>(…) or {name}("<tool name>", **arguments);
         a failed call raises McpToolError.
per tool, in the server's order:
  "  {name}.{ident}({params}) -> {returns}"          ident: the attribute name, or the exact name in quotes
                                                       when it has none: {name}("get-file", …)
  "    {the description's first line, at most 300 characters}"
params:  required properties first, then the others with " = …", each "{prop}: {type}"; type from JSON Schema:
         string str · integer int · number float · boolean bool · array list · object dict · null None ·
         a list of types joined by " | " · absent Any
returns: the type of "result" for the Python SDK's wrapper; dict for another outputSchema; str without one
```

Lines after the first start with two spaces, because deep_reasoner indents only the first line of a description
(`v2/messages.py:221–224`).

### 8.5 Names

- `defaultToolName(server, taken)` (TypeScript): lower-case; every run of characters other than `[a-z0-9]` → `_`;
  trimmed of `_`; a leading digit gets `mcp_` in front; empty → `mcp_server`; a Python keyword, a name in
  `RESERVED_NAMES` or one in `taken` (every tool's name) gets `_2`, `_3`, … until free.
- `header_env_name(server, header)` (Python): `f"{server}_{header}"` upper-cased, every run of characters other than
  `[A-Z0-9]` → `_`, trimmed of `_`: `postgres` + `Authorization` → `POSTGRES_AUTHORIZATION`.

### 8.6 What the frame shows for a server (`mcpRows`)

For each name in Canvas's list or in the grants: `granted` = a grant names it; `state` = `gone` (granted, not in
Canvas's list), `disabled`, `not_in_profile`, or `given`; `changed` = granted and `snapshotOf(info)` differs from the
grant's snapshot in transport, command, args, url, env names or header names; `old_shim` = `!grant.shim_current`.
Rows in Canvas's order, then gone grants by name.

---

## 9 · Texts (verbatim; tests assert these)

### 9.1 The backend (`deep_reasoning/tools/texts.py`)

| Name | Text |
|---|---|
| `RESERVED_NAME` | `'{name}' is one of deep_reasoner's own names in the REPL (subagent, run_all, FinalAnswer, Var, Func, task); a tool by that name would hide it. Choose another name.` |
| `SYNTAX` | `tool '{name}': tools/{name}.py line {line}: {message}` |
| `UNKNOWN_FACTORY` | `make_tools`' own sentence, copied: `Unknown tool factory {factory!r} for {alias!r}. Known: {known}. A factory of your own is reached with factory_from: <a .py file, relative to this config>.` |
| `NOT_FUNC` | `make_tools`' own sentence, copied: `tool {alias!r}: {factory} in {factory_from} returned {type}, not a Func. A tool factory returns Func(value, description=…) — the registry reads its `.value` (what the REPL binds) and `.description` (what the agent is told).` |
| `FACTORY_RAISED` | `tool '{name}': {factory} raised {type}: {message}` |
| `BUILD_TIMEOUT` | `tool '{name}': building it took longer than {seconds:g} s, so Check stopped it. A tool is built at the start of every conversation; a factory must return quickly.` |
| `READY_TIMEOUT` | `Check could not start deep_reasoner within {seconds:g} s, so it did not build the tool. Try again.` |
| `CHILD_ENDED` | `tool '{name}': the Check process ended ({how}) while {phase}.` (`how`: `exit code 3`, `signal 11`; `phase`: `starting`, `building the tool`) |
| `EXAMPLE_TIMEOUT` | `TimeoutError: the expression did not finish within {seconds:g} s` |
| `BUILTIN` | `'{factory}' is one of deep_reasoner's own factories. It is built when a conversation starts, with your model and files, so Check does not build it here.` |
| `BUILT` | `builds` (the frame composes the ✓ line) |
| `CHECK_FAILED` | `'{name}' did not pass Check, so it was not saved.` |
| `MCP_VIA_GRANT` | `'{name}' is an MCP server's grant: change it in the MCP servers list.` |
| `MCP_SERVER_TAKEN` | `MCP server '{server}' is already granted as '{other}'.` |
| `MCP_NEEDS_COMMAND` | `A stdio MCP server needs a command.` |
| `MCP_NEEDS_URL` | `An HTTP or SSE MCP server needs a URL.` |

`load_tool_factory`'s own sentences reach the report unchanged ("defines no", "is a …, not a function", "importing …
raised …").

### 9.2 The conversation (D1's `texts.py`)

| Name | Text |
|---|---|
| `mcp_no_answer` | `⚠ MCP server '{server}' did not answer within {seconds:g} s; its tools are not bound in this conversation.` (the spec's) |
| `mcp_failed` | `⚠ MCP server '{server}' could not be started ({detail}); its tools are not bound in this conversation.` |
| `mcp_not_enabled` | `⚠ MCP server '{server}' is granted to {namespaces} in the Library, but this conversation was not given it: enable it in Canvas's MCP settings. Its tools are not bound.` (`namespaces` joined with `, `) |

The shim's own (`shim.py`, in the agent's REPL and prompt):

| Name | Text |
|---|---|
| `UNAVAILABLE` | `{name} is not available in this conversation: {reason}.` |
| `NO_ANSWER` | reason: `its MCP server did not answer within {seconds:g} s when the conversation started` |
| `COULD_NOT_START` | reason: `its MCP server could not be started ({detail})` (plain `dr` adds `; not set in the environment: {names}` when any is missing) |
| `NOT_ENABLED` | reason: `its MCP server is not enabled in this app's MCP settings` |
| `NOT_REACHED` | reason: `no namespace this conversation can reach is granted it` |
| `NOT_IN_SESSION` | reason: `it was not connected when this conversation started` |
| `NO_MCP_PACKAGE` | reason: `the mcp package is not installed (pip install mcp)` |
| `CALL_FAILED` | `{name}.{tool} failed: {text}` |
| `CALL_TIMEOUT` | `{name}.{tool} did not answer within {seconds:g} s` |
| `SERVER_STOPPED` | `MCP server '{server}' stopped ({detail}); {name} is unavailable for the rest of this run.` |
| `HANDOFF_REFUSED` | `MCP server '{server}' is granted to {granted}, not to '{dst}', so {name} cannot be handed to a sub-agent there. Grant it to '{dst}' in the Library's Tools tab.` |
| `DESCRIPTION_HEAD` | `MCP server '{server}' ({transport}): call a tool as {name}.<tool>(…) or {name}("<tool name>", **arguments); a failed call raises McpToolError.` |

### 9.3 The Tools tab (`ui/texts.ts`)

| Name | Text |
|---|---|
| `TOOLS_RISK` | `Tools and MCP servers run as you, with your files and network: your tools inside the agent's process, a stdio MCP server as a program started for each conversation that can use it. Check runs your code too. Add only code and servers you trust.` |
| `YOUR_TOOLS` · `NEW_TOOL` · `MCP_SERVERS` | `Your tools` · `+ New tool` · `MCP servers (from Canvas's settings)` |
| `CHECKING` · `SAVING_CHECKING` | `Checking… (building your tool in a separate process)` · `Checking and saving…` |
| `CHECK_BUILT` | `✓ builds ({seconds} s). The agent is told:` |
| `CANNOT_SAVE` | `Fix this before saving: a tool that does not build stops every conversation from starting.` |
| `SAVE_ANYWAY_NOTE` | `Check could not build this tool here, where it has no secrets, no model and only its own folder. If it builds in a conversation, save it anyway; if it does not, no conversation will start until you fix it.` |
| `SAVE_ANYWAY` | `Save anyway` |
| `SAVED_TOOL` | `✓ Saved '{name}' v{version}. New conversations build it; conversations already started keep the version they began with.` |
| `DELETE_TOOL_CONFIRM` | `Delete '{name}'? It is removed from every namespace; its versions stay in the Library's history.` |
| `TRY_LABEL` · `PRINTED` | `Try (an expression Check evaluates with the tool bound)` · `It printed:` |
| `NAME_FIXED` | `how the agent calls it: a Python name, fixed once saved` |
| `MCP_AS` | `as {name}` |
| `MCP_SEEN` | `{count} tools, as the conversation of {date} saw them` |
| `MCP_NOT_SEEN` | `Its tools are listed here after the first conversation that starts it.` |
| `MCP_DISABLED` | `Disabled in Canvas's MCP settings: not started until you enable it there.` |
| `MCP_NOT_IN_PROFILE` | `Not given to the deep_reasoner agent: its profile lists other MCP servers.` |
| `MCP_GONE` · `REMOVE` | `Granted, but no longer in Canvas's MCP settings.` · `Remove` |
| `MCP_CHANGED` · `MCP_SHIM_OLD` · `UPDATE` | `Canvas's settings for this server changed since it was granted; an export still has the old ones.` · `Granted by an older deep-reasoning.` · `Update` |
| `MCP_SETTINGS_UNKNOWN` | `Canvas's MCP settings could not be read; showing the servers already granted.` |
| `MCP_NAME_TAKEN` | `A tool named '{name}' exists: choose another name.` |
| `MCP_EXPORT_NOTE` | `An export keeps each server's command, arguments and URL, never its environment or header values: under dr each is read from an environment variable (env names as they are; a header from SERVER_HEADER).` |
| `NEW_TOOL_SOURCE` | the template in §2.1's mock-up, byte for byte |
| `TOOL_HELP` | `A tool is a factory, make(client, params), that returns Func(value, description=…): the REPL binds value under the tool's name and the agent is told description. params are the block's other keys. Only this file is stored, so it cannot import a file beside it. Call models through client, the conversation's own, never with a key of your own. Read secrets and files when the tool is called, not when it is built: it is built at the start of every conversation and by Check, which has neither. The factory is not told where the config is (deep_reasoner passes no config_path to factory_from tools). A kg tool's saved layers record document paths against the config folder of the conversation that saved them.` |

Test ids (for D4's tests and D5's E12) are in Appendix B.

---

## 10 · Testing

Plain pytest and vitest; each test named for the property it pins; the outside world faked at its boundary (a fake
model, fake MCP servers that are real MCP servers written with `mcp`'s FastMCP, Canvas's host API in vitest); never a
mock of our own code.

### 10.1 Layers

| Layer (spec §4) | Where |
|---|---|
| 1 · deterministic, every push | `tests/tools/`, `tests/mcp/` (no network; fake servers on stdio and loopback); vitest; the browser tests in D3's `canvas-app` job |
| 2 · contracts | Check against `make_tools` on every fixture (§10.2); a stored v1 shim against today's `SESSION` (§10.3); every message `dr-acp` sends still validated by D1's harness, notices included |
| 4 · the real desktop app | D5's E12, with the MCP step §11.4 proposes; the cross-repo forwarding test (§10.6) |
| 5 · Gate B's evidence | the above green in CI at the branch's head, and §10.5's live tier |

### 10.2 E9 in full

**Fixtures** (`tests/tools/fixtures/`, our own code, never deep_reasoner_beta's): `word_count.py` (works),
`not_func.py` (returns a plain function), `misspelled` (`word_count.py` with `factory: mkae`), `import_error.py`
(`import yaml_x`), `hang.py` (`time.sleep(3600)` in the factory), `spawns.py` (starts `sleep 3600` with `subprocess`,
then hangs), `env_at_build.py` (reads `os.environ["D4_TOKEN"]` in the factory), `prints.py` (prints 1 MB while
building), `syntax.py`. **Fake MCP servers** (`tests/mcp/servers/`): `echo_server.py` (FastMCP over stdio: `echo`,
`add` → dict, `token` → its `ECHO_TOKEN`, `env_names` → its environment's names, `sleep(s)`, `crash` → `os._exit`;
`--http PORT` serves streamable HTTP with `whoami` → the request's `Authorization`), `hang_server.py` (never reads its
stdin), `crash_server.py` (prints its token to stderr and exits 1).

| E9 case | Its null | Tests |
|---|---|---|
| your tool: a working tool | — (it builds, is saved, and a conversation's agent calls it) | `test_check.py::test_a_working_tool_builds_and_says_what_the_agent_is_told`, `::test_the_tried_expression_is_evaluated_with_the_tool_bound`; `test_routes.py::test_a_checked_tool_is_saved_with_its_grants`; `tests/mcp/test_acp.py::test_a_tool_saved_through_the_api_is_built_and_called_in_the_next_conversation` |
| a non-`Func` factory | shows only at run time | `test_check.py::test_a_factory_that_returns_no_func_fails_check_in_deep_reasoners_words`; `test_routes.py::test_a_tool_that_cannot_build_is_not_saved[not_func]` |
| a misspelled factory | shows only at run time | `test_check.py::test_a_misspelled_factory_fails_check_naming_what_the_file_defines`; `test_routes.py::…[misspelled]` |
| an import error | shows only at run time | `test_check.py::test_an_import_of_a_missing_module_fails_check_and_cannot_be_saved_anyway`; `test_routes.py::…[import_error]` |
| a hanging factory | a Check past its time limit | `test_check.py::test_a_hanging_factory_is_stopped_at_the_build_limit` (default limits: the report arrives within ready time + 10 s + 1 s, outcome `timeout`), `::test_nothing_a_stopped_tool_started_is_left_running` (`spawns.py`: no `sleep 3600` afterwards) |
| (all five) | a failure that shows only at run time | `test_check.py::test_check_and_make_tools_agree[every fixture]`: for each, Check's `ok` equals whether `make_tools` builds the same materialized config in a subprocess, and where deep_reasoner words the failure, the same words |
| an MCP server that crashes | blocks the session or takes the worker down | `test_session.py::test_a_server_that_exits_at_start_is_failed_with_its_stderr_redacted`; `test_acp.py::test_a_server_that_crashes_at_start_is_reported_and_the_run_answers`, `::test_a_server_that_crashes_mid_run_fails_the_call_and_the_run_goes_on` (the next cell and the next prompt are answered) |
| an MCP server that hangs | blocks the session | `test_session.py::test_servers_connect_at_once_and_a_silent_one_is_given_up_at_the_deadline` (three servers: decided by the deadline, not three times it); `test_acp.py::test_session_new_does_not_wait_and_the_first_answer_waits_at_most_the_deadline` (a 2 s `connect_timeout_s` in the grant); `test_shim.py::test_a_call_that_never_answers_raises_after_its_timeout` |
| an MCP server not granted to the conversation's namespace | its tools in the REPL | `test_acp.py::test_a_server_granted_elsewhere_is_not_in_this_agents_repl_or_prompt` (granted to `course_advisor`, the conversation in `router`: a cell's `dir()` and the fake model's first request lack it), `::test_a_sub_agent_spawned_into_a_granted_namespace_gets_it`, `::test_a_grant_reaches_a_child_namespace`, `::test_handing_a_server_to_an_ungranted_namespace_is_refused`; `test_session.py::test_a_server_granted_nowhere_is_not_started`, `::test_a_server_granted_only_where_spawning_is_not_allowed_is_not_started` |

### 10.3 Test files

| File | Pins (besides §10.2) |
|---|---|
| `tests/tools/test_check.py` | `test_a_syntax_error_fails_before_any_process_starts`; `test_a_reserved_name_is_invalid[subagent, run_all, FinalAnswer, Var, Func, task]`; `test_llm_is_not_reserved`; `test_a_built_in_factory_is_named_not_built`; `test_an_unknown_built_in_factory_is_refused_in_deep_reasoners_words`; `test_a_factory_raising_can_be_saved_anyway` (`env_at_build.py`: outcome `raised`, its frame in `tools/word_count.py`); `test_check_never_reaches_a_model` (a factory calling `client.chat.completions.create` gets a connection error; a fake model on another port records no request); `test_check_gets_no_secret` (`check_env` of an environment holding `OPENAI_API_KEY` and `OH_SECRET_KEY` has neither); `test_printing_cannot_corrupt_the_report` (`prints.py`); `test_an_example_that_raises_is_reported_and_the_build_stays_ok`; `test_a_slow_example_is_stopped_at_its_limit`; `test_the_temporary_folder_is_removed`; `test_not_func_and_unknown_factory_sentences_equal_make_tools` (tripwire on deep_reasoner's inline text) |
| `tests/tools/test_routes.py` | Starlette's `TestClient` with `Host: 127.0.0.1:<port>`: `test_check_route_answers_200_with_a_report`; `test_a_grant_only_change_runs_no_check` (a broken tool stored through `Library.put_tool`, then a `PUT` that changes only `granted_in` answers 200); `test_save_anyway_stores_a_raising_tool_only_when_asked`; `test_a_structural_failure_cannot_be_saved_anyway`; `test_an_mcp_block_through_put_tools_is_refused`; `test_put_mcp_writes_the_block_and_the_shim_and_grants`; `test_put_mcp_resent_unchanged_makes_no_tool_version`; `test_a_server_cannot_be_granted_under_two_names`; `test_put_mcp_refuses_a_stdio_grant_without_a_command`; `test_get_mcp_lists_grants_with_their_last_seen_tools`; `test_get_mcp_says_when_a_grant_has_an_old_shim`; `test_mcp_routes_answer_only_their_own_host` (D2's guard) |
| `tests/mcp/test_wire.py` | `test_forwarded_specs_read_acps_stdio_http_and_sse_shapes`; `test_other_mcp_server_types_are_ignored`; `test_servers_named_reads_mcp_blocks_only`; `test_a_run_gets_only_the_specs_its_blocks_name` (`specs_for_run`: a forwarded server no block names, and its secrets, are not in the result); `test_redact_replaces_every_secret_value`; `test_the_seen_cache_round_trips_and_is_private` (0600, 0700) |
| `tests/mcp/test_grants.py` | `test_mcp_block_for_stdio_http_and_sse`; `test_header_env_name`; `test_is_mcp_tool_needs_the_factory_and_the_marker`; `test_an_exported_and_reimported_grant_is_still_a_grant` |
| `tests/mcp/test_shim.py` | plain mode (no `SESSION`): `test_the_shim_connects_from_its_block_with_env_from_the_environment` (`token` returns the variable's value); `test_results_are_unwrapped_dicts_text_or_blocks` (§8.3's table); `test_a_failed_call_raises_mcp_tool_error_with_the_servers_text`; `test_positional_arguments_follow_the_described_order`; `test_tools_without_an_identifier_are_called_by_their_exact_name`; `test_the_description_is_what_8_4_says` (exact text); `test_a_server_survives_fork` (`copy.deepcopy` returns the same object; no warning); `test_calls_from_many_threads_and_under_nest_asyncio`; `test_without_the_mcp_package_the_factory_returns_a_stand_in` (`mcp` hidden with `monkeypatch.setitem(sys.modules, "mcp", None)`); `test_the_shim_imports_only_the_standard_library_at_module_level` (its AST); `test_a_stored_v1_shim_works_with_todays_session` (a frozen copy of v1 in `fixtures/`); the guard: `test_the_guard_ends_its_server_when_its_parent_is_killed` (a parent process started for the test, `SIGKILL`ed; the server's pid is gone within 1.5 s); `test_the_guard_passes_the_exit_code`; HTTP: `test_an_http_server_is_reached_with_its_headers` (`whoami`) |
| `tests/mcp/test_session.py` | `test_only_granted_and_reachable_servers_are_started`; `test_grant_sets_follow_deep_reasoners_resolution` (root, `a`, `a.b`); `test_a_granted_server_not_forwarded_is_not_enabled`; `test_statuses_carry_what_the_agent_is_told`; `test_a_server_given_up_is_ended_within_three_seconds` |
| `tests/mcp/test_acp.py` | D1's harness (`dr_acp(None, home)`, `FakeOpenAI`, `ShimConnection`), the Library at `home`, `open_session(cwd, mcp_servers=[…])`: `test_dr_acp_advertises_http_and_sse`; `test_a_granted_server_is_bound_and_a_cell_calls_it`; `test_a_forwarded_server_no_grant_names_is_never_started` (the fake server writes a marker file when it starts; there is none); `test_server_secrets_never_reach_the_run_log_or_the_transcript` (`crash_server.py` prints its token; the notice says `[redacted]`); `test_the_notice_replays_on_load`; `test_the_seen_cache_is_written_for_bound_servers`; `test_no_stdio_server_outlives_a_root_stop` (a cell in `while True: pass`; root Stop; within 2 s no fake server is running); `test_no_stdio_server_outlives_a_closed_session`; the E9 rows of §10.2 |
| `tests/mcp/test_export.py` | `test_an_exported_grant_runs_under_dr` (`dr-library export`, then `dr <dir>/main.yaml` with `FakeOpenAI` scripted to call `echo.echo("hi")` and `ECHO_TOKEN` in the environment: exit 0, the cell's output `hi`) |

**D1's files** gain: `tests/acp/harness.py`: `DrAcp.open_session(cwd, mcp_servers=())`; `test_agent.py`'s
capability assertion; golden recordings re-recorded once if they hold the `initialize` response (D1's one command).

### 10.4 The Tools tab (D3's harness: `tests/canvas_app/`, Playwright, marker `browser`; and vitest)

D3's `test_the_tools_tab_always_shows_the_safety_notice_with_the_cap` and `test_the_tools_tab_lists_tools_with_their_grants`
stay green. D4 adds to `test_tools_tab.py`: `test_the_risk_line_is_under_the_safety_banner`;
`test_a_new_tool_is_written_checked_and_saved_with_its_grants` (asserts the stored row, the source byte for byte, and
`granted_in`); `test_check_shows_what_the_agent_is_told_and_the_tried_value`;
`test_a_tool_that_cannot_build_shows_why_and_cannot_be_saved[not_func, misspelled, import_error]`;
`test_a_hanging_factory_shows_the_limit`; `test_a_raising_factory_offers_save_anyway`;
`test_a_grant_tick_on_a_saved_tool_saves_without_unsaved_code`; `test_an_inherited_grant_is_fixed`;
`test_the_editor_keeps_python_indentation` (Tab, Enter after `:`); `test_canvas_mcp_servers_are_listed_and_granted_per_namespace`
(the frame opened with `mcp=`); `test_a_disabled_server_says_so_and_can_still_be_granted`;
`test_a_grant_gone_from_canvas_offers_remove`; `test_a_changed_server_offers_update`;
`test_the_last_seen_tools_are_shown` (a seen file written first); `test_without_canvas_settings_only_grants_are_shown`.
`library_home`'s fixture gains a tool whose factory raises (D3 §8.3 allows it).

vitest: `protocol.test.ts` (the `mcp` parameter round-trips; bad JSON → `null`); `context.test.ts`
(`mcpServersFromSettings`: stdio, http, sse and skipped entries; `disabled` and `not_in_profile`; no value of `env` or
`headers` in the output, `"**********"` never; a failing request → `null`); `tools.test.ts` (`defaultToolName`'s
table; `mcpRows`' states; `snapshotOf` and `changed`; `inheritedGrants` from an `Effective` list); `api.test.ts`
(`checkTool`, `getMcp`, `putMcp`: bodies with exactly the backend's field names; a `422 check_failed` → `LibraryError`
carrying the report).

### 10.5 Live tier (Gate B; `@pytest.mark.live`, skipped without `OPENAI_API_KEY`; gpt-6-luna)

Spec §4 layer 5: "D4: a tool written in the Library, and an MCP server, each used by an agent". Each test sets up a
Library at a temporary home with the starter profile (gpt-6-luna on OpenAI, D2 decision M), writes through the HTTP
API (`create_app`, `TestClient`), so the gate and the real Check run, then drives a real `dr-acp --home` over stdio
with D1's harness. The facts asked for exist nowhere but in the tool, so the answer can only come from it.

1. `tests/tools/test_live.py::test_live_a_tool_written_in_the_library_is_used_by_the_agent`: `PUT /tools/course_credits`
   (a factory whose `course_credits(code: str) -> int` knows `ZQ-417` is 7 credits), granted to `root`; the response
   is 201 and a Check report on the same body says `built`; prompt "How many credits is course ZQ-417?" → the answer
   contains `7`; the run log holds a cell whose code calls `course_credits(` and whose output contains `7`.
2. `tests/mcp/test_live.py::test_live_an_mcp_server_granted_to_the_namespace_is_used_by_the_agent`: a FastMCP stdio
   server of ours (`catalog_server.py`: `prerequisites(course: str) -> list[str]`, `ZQ-417` → `["ZQ-101"]`, refusing
   to answer without its `CATALOG_TOKEN`); `PUT /mcp/catalog` granted to `root`; `session/new` forwards it as the
   bridge would (`McpServerStdio` with `env: [{CATALOG_TOKEN, …}]`); prompt "What must a student finish before
   ZQ-417?" → the answer contains `ZQ-101`; the run log's `mcp.status` says `bound`, a cell calls
   `catalog.prerequisites(`, and the token appears nowhere in the run log or the updates.

Cents per run, in D1's on-demand `live.yml` with the same secret.

### 10.6 Across the repositories (proposed; D5's `crossrepo` harness)

`tests/crossrepo/test_mcp_forwarding.py`: the agent-server from the SDK fork's pinned commit; `PATCH
/api/settings/mcp/echo` with `echo_server.py` as a stdio server and one secret in its `env`; the `deep_reasoner`
profile; the Library granting `echo` to `root`; a conversation with `FakeOpenAI` scripted to call `echo.token()` →
the cell's output is the secret (it travelled through Canvas's settings, the bridge and `dr-acp`), and `mcp.status`
says `bound`. This is the one place the forwarding shape is run rather than read (header, "Not verified").

---

## 11 · Contracts with other work

These are findings for the Conductor; none is settled sideways.

### 11.1 D1

D4 makes these changes in D1's files (§7.3), about 90 lines with the sentences:

- `Start.mcp_servers` (D1 §4.8 named it) and `AGENT_CAPABILITIES.mcpCapabilities = {"http": True, "sse": True}` (D1 §4.8
  anticipated the flip).
- **A new RunEvent, `mcp.status`**, in `runlog.py`, emitted by the worker before `build_reasoner`, encoded as root
  notices. D1 §4.4's event table and §5.6's sentences should list it and them when D1 next revises; E4's schema check
  covers the notices as it covers the fresh-run notice.
- `Worker.build` calls `open_session` between `load_dr_config` and `build_reasoner`; a failure inside it is caught per
  server and never fails the build.
- The pump writes the seen cache (§4.7) for live, not replayed, `mcp.status` events.
- The test harness's `open_session` takes `mcp_servers`.
- **No change to D1's process handling**: stdio servers end through their guards (§4.6), so `RunHandle.kill` and the
  worker's `killpg(0)` stay as they are.

### 11.2 D2

- **The gate**: `_ToolBody` gains `accept_check_failure: bool = False`; `put_tool` calls `require_check` first (§3.5).
  Old clients are unaffected (the field is optional); `Library.put_tool` and import are not gated.
- **Routes**: `create_app` appends `*tool_routes(lib)`. For that, D2's `route()` helper, today a closure inside
  `create_app`, becomes a module-level `json_route(path, method, handler)` with no change in behaviour, so D4's
  routes are built the same way (the alternative is an eight-line copy in `tools/routes.py`).
- **No schema change, no migration**: MCP grants are tool rows (decision D), D2's recommendation.
- **Proposed, not required**: `Library.materialize(…, only_granted: bool = False)`, with `LibraryCatalog` passing
  `True`, so a run's `main.yaml` holds only tools some namespace grants. Today an ungranted tool is still built in
  every conversation (`make_tools` builds every block), so a tool imported broken and granted nowhere still stops every
  conversation; an export keeps every tool. D4 does not depend on it: an ungranted MCP grant is never connected
  (§4.4), and the gate keeps the panel from storing a broken tool.
- D2 §6.5 said Check "can materialize the Library into a temporary directory"; D4 materializes only the tool being
  checked (one tool's failures, no others').

### 11.3 D3

All within D3 §8.3: `tabs/tools.tsx` extended, the banner kept at the top; `api.ts` gains `checkTool` (D2 §6.5's
route) and `getMcp`, `putMcp`; `ToolBody` gains `accept_check_failure`; `FrameParams.mcp` with its read in
`page/context.ts`, through `host.agentServer.request`, `null` on failure; `CodeField`'s `language: "python"` loads
CodeMirror as the `editor` chunk, with `inlineDynamicImports` removed as D3 foresaw; tests beside D3's, with the same
fixtures. One addition D3 should know: `page/mount.ts` step 2 reads `readMcpServers` for the Tools tab only (one
line). The frame UI stays under 250 KB without the editor chunk (§7.4).

**Branch base.** D4's code extends D3's files, so `v1-custom-tools` should be cut from `v1-decompositions-panel` once
D3 is far enough, as D2's was cut from D1's (D2 §9 item 4).

### 11.4 D5

- **E10 with MCP servers bound** (D5 §1.2's final part): D4 provides `echo_server.py` and the grant to run E10 with a
  stdio server bound and a call made. Expected to hold unchanged: the provider key and the agent-server's secrets are
  not in the worker's environment, a cell's `os.environ` or `/proc/self/environ`, the transcript or the run log; the
  server's own environment (its `env_names` tool) holds only its configured variables and `mcp`'s six. The MCP
  server's secrets travel in the control pipe, never in an environment, and are redacted from failure details.
- **D5 §2.1's first row** ("not in … any process the worker starts") needs one exception stated: an MCP server whose
  Canvas settings give it a provider key gets it, by the user's configuration. D5 §2.2's bullet on tools and MCP
  servers can point at §5 here.
- **The profile**: D4 relies on D5 creating the `deep_reasoner` profile with `mcp_server_refs: null` (D5 §4.5.1) and
  reads `mcp_server_refs` to say when a server is left out.
- **E12**: proposed, a final-part step: add an MCP server through Canvas's settings API, tick it for the conversation's
  namespace in the Tools tab (Appendix B's ids), and see the next conversation's cell call it (§10.6's server).
- **After an upgrade** (§14 item 4): optionally, `dr-app setup` could run a check of every stored tool and print the
  failures in the startup log.

### 11.5 C2, S2, S1, C1, C3

None.

---

## 12 · What D4 relies on

| # | Behaviour relied on | Their code |
|---|---|---|
| R1 | `make_tools` builds every block of `cfg.tools` once per run; a `factory_from` block: `load_tool_factory(alias, factory, factory_from, cfg.config_path)`, then `build(client, params)` with the block minus `factory` and `factory_from`, then the `Func` check with the inline sentence | deep_reasoner `v2/cli.py:125–180, 348` |
| R2 | `load_tool_factory` resolves against `config_path`, wraps an import failure `from` its cause, raises "defines no" and "not a function" without one, and caches modules by path | `tools/base.py:316–407` |
| R3 | A namespace's tools are resolved as an ordered union down the dotted chain; an agent binds them through `cross_namespace`, which calls a tool's `__cross_namespace__`; a missing registry entry raises | `namespaces.py:272–320, 345–392, 645–654` |
| R4 | `check_spawn(registry, src, dst)` is deep_reasoner's own spawn rule | `namespaces.py:672–685` |
| R5 | Namespace bindings override the framework's names | `v2/agent.py:647, 671–676` |
| R6 | `func(name, value, description).describe()` is what the agent is told | `v2/messages.py:184–189, 216–224` |
| R7 | `fork` deep-copies the REPL, degrading per binding | `repls/backends.py:105–140` |
| R8 | A client on loopback needs no key | `config.py:249–265` |
| M1 | `stdio_client` starts the server in a new session, merges six variables into its environment, closes stdin then ends the process tree on exit | `mcp` 1.28.1 `client/stdio/__init__.py:28–66, 180–260` |
| M2 | `ClientSession.call_tool(…, read_timeout_seconds=…)`, `list_tools(cursor=…)`, `streamable_http_client(url, http_client=…)`, `sse_client(url, headers=…)` | `client/session.py:386, 525`; `client/streamable_http.py:601`; `client/sse.py:30` |
| B1 | OpenHands forwards every enabled server of the profile's filtered `mcp_config` as ACP `mcpServers` at `session/new` and `session/load`, stdio always, HTTP and SSE when advertised, secrets in plain text | SDK fork `acp_agent.py:739–821, 3105–3120`; `profiles/resolver.py:160–168` |
| B2 | `GET /api/settings` without `X-Expose-Secrets` redacts every secret value | `settings_router.py:113–177`; `mcp/config.py:64–74` |
| B3 | App-backend requests have no read timeout through the bridge | `bridge.py:467–472`; `docker_runtime/proxy.py:96–97` |
| D1-1 | `Start`, `Worker.build`, the pump, `Session.mcp_servers`, the harness | D1 at `90044f0` |
| D2-1 | Tool rows, `granted_in` as the exact set, `shapes.validate_tool`, unchanged-is-not-a-save, `materialize`'s `tools/<name>.py`, `create_app`'s guard and error handler | D2 at `90044f0` |
| D3-1 | §8.3's contract | D3 `ab6f2ec` |

---

## 13 · Size

| Part | Code | Tests |
|---|---|---|
| Check: `check.py` 150, `check_child.py` 90, `texts.py` 60 | 300 | 330 (`test_check.py`, fixtures) |
| Routes and the gate: `routes.py` 110, D2's changes 15 | 125 | 200 (`test_routes.py`) |
| MCP: `shim.py` 270 (guard included), `wire.py` 90, `grants.py` 80, `session.py` 100 | 540 | 650 (`test_wire`, `test_grants`, `test_shim`, `test_session`, fake servers 90) |
| D1's changes (event, encoding, sentences, pump, front, capabilities) | 90 | 330 (`tests/mcp/test_acp.py`, harness) |
| Export and live tier | — | 200 |
| The frame: protocol and context 70, types and api 80, `tools.ts` 90, `tabs/tools.tsx` 180, `ToolEditor` 200, `CheckResult` 70, `McpServerRow` 120, editor chunk 60, texts 50 | 920 | 480 (vitest 200; browser 280) |
| **Total** | **≈1.98k** | **≈2.19k** |

About 4.2k lines with tests, about 14 h at Gate C at the workspace's rate, against the spec's ≈1.0k and ≈3 h. The
differences: unit and browser tests (the spec's figure was nearly all code); the gate and its two save paths; the
guard and the concurrent session start, which the probes showed are needed; the MCP side of the Tools tab, which the
spec costed at 40 lines; the event and notices in `dr-acp`. **If the Conductor wants a smaller D4**, two parts cut
cleanly, each with what is lost: the seen cache (≈60 lines and its tests; the Tools tab then shows no server tools)
and CodeMirror (≈60 lines and a dependency; a textarea with Tab handling instead).

---

## 14 · Open items, and what I was unsure about

1. **The forwarding path was read, not run** (header): `_mcp_config_to_acp_servers`, the ACP 0.12.1 model shapes and
   the settings JSON. §10.6's test runs it; until then `forwarded_specs` accepts both a missing and a `"stdio"` `type`.
2. **E9's "not granted to the conversation's namespace"** is designed per agent (decision G, §6 item 5). If Michael
   meant "only the conversation's own namespace, and never a sub-agent's", that is a narrower rule deep_reasoner does
   not have, and it would need the stand-in in every agent of a non-granted namespace even when spawned into a granted
   one.
3. **The frame's URL carries MCP commands, arguments and URLs.** They are not secrets by Canvas's model, but a user can
   put a token in an argument; the agent-server's or the backend's access log may then hold it. The alternative is to
   send the list by `postMessage` after the frame loads, which D3 rejected for static data (D3 decision E); D4 follows
   D3's §8.3.
4. **A tool broken by an upgrade or an import** is not found until it is checked or a conversation fails to start
   (§3.5). D2's `only_granted` (§11.2) narrows the blast radius; a check of every tool after an upgrade (§11.4) would
   find it at launch.
5. **Check's false failures** (a tool that needs a secret, the conversation's folder or the network at build time)
   are handled by "Save anyway", not reproduced. A per-tool "build in this folder" option was considered and left out.
6. **OAuth-protected remote servers**: OpenHands forwards only header-compatible credentials (`acp_agent.py:717–736`);
   a server needing OAuth fails at connect and is reported. Not designed around.
7. **Remote REPLs** (`repl: daytona`): how deep_reasoner carries a `Func`'s value into a remote REPL decides whether
   an MCP server can be used there; untested.
8. **The live tier depends on the model choosing the tool**; the facts are unguessable and the tool is described,
   but a model may still answer without calling it. A failure there is re-run once before it is read as a regression.
9. **The Code Guide** says never to ship un-run fenced Python in a `.md`; this design, like D1's to D3's, carries
   signatures as fenced code, as the brief asks. A tension in the pages, not a choice made here.

---

## Appendix A · Signature reference

Python as it will be written, ruff-formatted, bodies `...`; TypeScript in declaration form (`declare` marks a body
the sections above specify), one field per line. Paths are relative to `src/deep_reasoning/` or `canvas-app/src/`.

### A.1 `tools/check.py`, `tools/check_child.py`

Each block lists its imports only where they name where a type comes from; the rest are the standard library's
and pydantic's.

```python
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final, Literal

from pydantic import BaseModel

from deep_reasoning.library.library import Library
from deep_reasoning.library.records import FieldError, LibraryError

Outcome = Literal[
    "built",
    "builtin",
    "invalid",
    "syntax",
    "import_failed",
    "bad_factory",
    "not_func",
    "raised",
    "timeout",
    "unavailable",
]
OK_OUTCOMES: Final = frozenset({"built", "builtin"})
SAVE_ANYWAY_OUTCOMES: Final = frozenset({"raised", "timeout", "unavailable"})
RESERVED_NAMES: Final = frozenset({"FinalAnswer", "Func", "Var", "run_all", "subagent", "task"})
CHECK_MODEL_URL: Final = "http://127.0.0.1:9/v1"
PASSED_ENV: Final = ("PATH", "LANG", "LC_ALL", "LC_CTYPE", "TMPDIR", "TZ")
SHOWN_LIMIT: Final = 2_000  # characters of printed output, tracebacks and example values


@dataclass(frozen=True)
class CheckLimits:
    ready_s: float = 30.0  # the throwaway process imports deep_reasoner
    build_s: float = 10.0  # the tool's file is imported and its factory called
    example_s: float = 10.0  # the tried expression


DEFAULT_LIMITS: Final = CheckLimits()


class ExampleResult(BaseModel):
    expression: str
    ok: bool
    value: str | None  # repr of the result, at most SHOWN_LIMIT characters
    error: str | None  # "TypeName: message"
    seconds: float


class CheckReport(BaseModel):
    ok: bool
    outcome: Outcome
    message: str
    told: str | None  # deep_reasoner's func(name, value, description).describe()
    traceback: str | None  # raised: the frames in tools/<name>.py and the exception line
    example: ExampleResult | None
    printed: str  # the last SHOWN_LIMIT characters the tool printed
    seconds: float | None  # loading the file and calling the factory
    deep_reasoner: str  # the build that checked it
    can_save: bool
    can_save_anyway: bool


def tool_name_errors(name: str) -> list[FieldError]:
    """RESERVED_NAME for a name in RESERVED_NAMES; D2's TOOL_NAME rule is shapes.validate_tool's."""


def check_env(base: Mapping[str, str]) -> dict[str, str]:
    """PASSED_ENV from base; HOME, USER and LOGNAME from the password database;
    PYTHONUNBUFFERED=1 and PYTHONDONTWRITEBYTECODE=1. Nothing else."""


def check_tool(
    name: str,
    yaml_text: str,
    source: str | None,
    *,
    example: str | None = None,
    limits: CheckLimits = DEFAULT_LIMITS,
) -> CheckReport:
    """§3.2's static stage, then §3.3's throwaway process under limits; never raises for
    anything the tool does."""


class ToolCheckFailed(LibraryError):
    code = "check_failed"
    status = 422

    def __init__(self, report: CheckReport) -> None: ...

    def payload(self) -> dict[str, Any]:
        """{"error", "message", "check": report.model_dump(mode="json")}."""


def require_check(
    library: Library,
    name: str,
    yaml_text: str,
    source: str | None,
    *,
    accept_failure: bool,
) -> None:
    """§3.5: returns when the PUT may proceed; raises ToolCheckFailed or LibraryBadRequest."""
```

```python
# tools/check_child.py
def main(argv: Sequence[str] | None = None) -> int:
    """python -m deep_reasoning.tools.check_child --report-fd N --name NAME [--example EXPR] MAIN
    Writes §3.3's JSON lines to fd N; prints nothing of its own to stdout."""
```

### A.2 `tools/routes.py`, `mcp/grants.py`, `mcp/wire.py`

```python
# mcp/wire.py: pydantic and yaml only (dr-acp's front imports it)
Transport = Literal["stdio", "http", "sse"]
McpState = Literal["bound", "no_answer", "failed", "not_enabled", "skipped"]
MCP_FACTORY: Final = "mcp_server"
SEEN_DIR: Final = "mcp"
REDACTED: Final = "[redacted]"


class McpServerSpec(BaseModel):
    """A server as OpenHands forwarded it, secrets included: control pipe only."""

    name: str
    transport: Transport
    command: str | None = None
    args: list[str] = []
    env: dict[str, str] = {}
    url: str | None = None
    headers: dict[str, str] = {}


class McpServerStatus(BaseModel):
    tool: str  # the name it is bound under
    server: str  # its name in Canvas's MCP settings
    transport: Transport | None
    state: McpState
    detail: str | None = None  # failed and skipped: why; secrets redacted
    granted: list[str] = []  # the namespaces whose resolved tools name it
    seconds: float | None = None  # bound: time to connect
    count: int = 0  # bound: its tools
    told: str | None = None  # bound: deep_reasoner's describe() of its binding


class McpSeen(BaseModel):
    at: datetime
    run: str
    count: int
    told: str


def forwarded_specs(servers: Sequence[Mapping[str, Any]]) -> list[McpServerSpec]:
    """ACP mcpServers as D1 keeps them (dumped by alias): stdio (no type, or "stdio"),
    "http", "sse"; any other type is left out."""


def servers_named(config_path: Path) -> set[str]:
    """The `server` of every tool block in main.yaml whose factory is MCP_FACTORY."""


def specs_for_run(
    forwarded: Sequence[Mapping[str, Any]],
    config_path: Path,
) -> list[McpServerSpec]:
    """forwarded_specs(forwarded), keeping only the servers servers_named(config_path) names:
    what the front puts in Start.mcp_servers."""


def redact(text: str, secrets: Iterable[str]) -> str:
    """Every secret of at least 4 characters replaced by REDACTED."""


def remember_seen(home: Path, run: str, servers: Sequence[McpServerStatus], at: datetime) -> None:
    """§4.7: one file per bound server, atomically, 0600 in a 0700 directory."""


def read_seen(home: Path, server: str) -> McpSeen | None: ...
```

```python
# mcp/grants.py: the backend's side
SHIM_MARKER: Final = "# deep-reasoning MCP shim"


class McpGrantBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    server: str = Field(min_length=1, max_length=128)
    transport: Transport
    command: str | None = None
    args: list[str] = []
    url: str | None = None
    env: list[str] = []  # names only
    headers: list[str] = []  # names only
    granted_in: list[str]
    base_version: int


class McpGrant(BaseModel):
    name: str  # the tool row's name: how the agent calls it
    version: int
    server: str
    transport: Transport
    command: str | None
    args: list[str]
    url: str | None
    env: list[str]
    headers: list[str]
    granted_in: list[str]
    shim_current: bool
    seen: McpSeen | None


def shim_source() -> str:
    """The installed shim.py's text (importlib.resources)."""


def is_mcp_tool(record: ToolRecord) -> bool:
    """Factory MCP_FACTORY and a source starting with SHIM_MARKER."""


def header_env_name(server: str, header: str) -> str: ...


def mcp_block(name: str, body: McpGrantBody) -> dict[str, Any]:
    """§4.2's block, without factory_from (D2 adds it). Raises LibraryBadRequest for a
    stdio grant without a command or a remote one without a URL."""


def grant_record(record: ToolRecord, seen: McpSeen | None) -> McpGrant: ...
```

```python
# tools/routes.py
class CheckBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    yaml: str
    source: str | None = None
    example: str | None = None


def tool_routes(library: Library) -> list[Route]:
    """POST /tools/{name}/check, GET /mcp, PUT /mcp/{name} (§7.2), built with D2's json_route."""
```

### A.3 `mcp/shim.py` (standard library at module level) and `mcp/session.py`

```python
# deep-reasoning MCP shim, version 1. Generated by the Library; grant and update it in the Tools tab.
"""One MCP server as a deep_reasoner tool (factory_from this file, factory mcp_server)."""

SHIM_VERSION: Final = 1
FACTORY: Final = "mcp_server"
CONNECT_TIMEOUT_S: Final = 10.0
CALL_TIMEOUT_S: Final = 120.0
GUARD_POLL_S: Final = 0.5
DESCRIPTION_LIMIT: Final = 300
RESULT_KEY: Final = "result"

# Set by dr-acp's worker (deep_reasoning.mcp.session) before tools are built: bound name -> Func.
SESSION: "dict[str, Any] | None" = None


class McpToolError(Exception):
    """A call that failed, timed out, or reached a server that is gone or was never bound."""


@dataclass(frozen=True)
class ServerSpec:
    name: str
    transport: Literal["stdio", "http", "sse"]
    command: str | None
    args: tuple[str, ...]
    env: Mapping[str, str]
    url: str | None
    headers: Mapping[str, str]


class Connection:
    """One server on a daemon thread running its own event loop (§4.3)."""

    failure: str | None
    tools: tuple[Any, ...]  # mcp.types.Tool

    def __init__(
        self,
        spec: ServerSpec,
        *,
        errlog: TextIO,
        call_timeout_s: float = CALL_TIMEOUT_S,
    ) -> None: ...

    def start(self) -> None: ...

    def wait_ready(self, timeout_s: float) -> bool: ...

    def abandon(self) -> None: ...

    def call(self, tool: str, arguments: Mapping[str, Any]) -> Any:
        """§8.3's result, or McpToolError; marks the connection dead when the server is gone."""


class McpTool:
    def __init__(self, server: "Server", tool: Any) -> None: ...

    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...

    def __cross_namespace__(self, src: str | None, dst: str) -> "McpTool": ...

    def __copy__(self) -> "McpTool": ...

    def __deepcopy__(self, memo: dict[int, Any]) -> "McpTool": ...


class Server:
    """What the REPL binds: callable by a tool's exact name, with one McpTool attribute per
    tool whose name makes a Python identifier."""

    __name__: str

    def __init__(
        self,
        name: str,
        connection: Connection,
        *,
        granted: frozenset[str] | None,
    ) -> None: ...

    def __call__(self, tool: str, /, **arguments: Any) -> Any: ...

    def __cross_namespace__(self, src: str | None, dst: str) -> "Server":
        """With granted set: PermissionError (HANDOFF_REFUSED) for a hand-off outside it."""

    def __copy__(self) -> "Server": ...

    def __deepcopy__(self, memo: dict[int, Any]) -> "Server": ...


class Unavailable:
    def __init__(self, name: str, reason: str) -> None: ...

    def __call__(self, *args: Any, **kwargs: Any) -> NoReturn: ...

    def __getattr__(self, attr: str) -> NoReturn: ...


def describe(name: str, spec: ServerSpec, tools: Sequence[Any]) -> str:
    """§8.4's description."""


def bound(name: str, connection: Connection, *, granted: frozenset[str] | None) -> Any:
    """Func(Server(...), describe(...))."""


def unavailable(name: str, reason: str) -> Any:
    """Func(Unavailable(name, reason), UNAVAILABLE)."""


def spec_from_block(
    params: Mapping[str, Any],
    environ: Mapping[str, str],
) -> tuple[ServerSpec, list[str]]:
    """Plain dr: the block's snapshot with values from environ; the names it could not find."""


def mcp_server(client: Any, params: dict[str, Any]) -> Any:
    """The factory (§4.3)."""


def guard(argv: Sequence[str]) -> NoReturn:
    """python -I shim.py --guard -- COMMAND ARGS… (§4.6)."""
```

```python
# mcp/session.py: the worker's side
def open_session(
    cfg: V2Config,
    specs: Sequence[McpServerSpec],
    *,
    run_dir: Path,
) -> list[McpServerStatus]:
    """§4.4: connect the granted, reachable servers at once under one deadline, install
    shim.SESSION for every MCP block, and return one status per block."""


def reachable(registry: NamespaceRegistry, start: str, names: Sequence[str]) -> set[str]:
    """The closure of {start} under deep_reasoner's check_spawn."""
```

### A.4 D1's files

```python
# acp/worker/protocol.py
class Start(BaseModel):
    op: Literal["start"] = "start"
    run: str
    session: str
    run_dir: str
    config_path: str
    namespace: str
    client_overrides: dict[str, Any]  # merged over cfg.client
    mcp_servers: list[McpServerSpec] = []  # D4: the forwarded servers the run's MCP blocks name


# acp/runlog.py
class McpStatus(_Ev):
    kind: Literal["mcp.status"] = "mcp.status"
    servers: list[McpServerStatus]


# acp/texts.py
def mcp_no_answer(server: str, seconds: float) -> str: ...


def mcp_failed(server: str, detail: str) -> str: ...


def mcp_not_enabled(server: str, namespaces: Sequence[str]) -> str: ...


def mcp_notice(status: McpServerStatus) -> str | None:
    """The notice for no_answer, failed and not_enabled; None otherwise."""


# acp/supervisor.py
class RunHandle:
    @classmethod
    async def start(
        cls,
        *,
        run_id: str,
        session: "Session",
        source: RunSource,
        after: RunEndReason | None,
        decomposition: str | None,
        home: Home,
        route: ModelRoute,
        outbox: Outbox,
        mode: Mode,
        heartbeat_s: float,
        mcp_servers: Sequence[McpServerSpec] = (),
    ) -> "RunHandle": ...


# tests/acp/harness.py
class DrAcp:
    async def open_session(
        self,
        cwd: Path,
        mcp_servers: Sequence[Any] = (),
    ) -> str: ...
```

### A.5 D2's `api.py`

```python
class _ToolBody(_Body):
    source: str | None = None
    granted_in: list[str] | None = None
    accept_check_failure: bool = False  # D4: save a tool whose Check failed in a way it allows


def json_route(
    path: str,
    method: str,
    handler: Callable[[Request, bytes], Any],
) -> Route:
    """D2's route() helper, moved to module level unchanged, so tool_routes uses it too."""
```

### A.6 The frame (TypeScript)

```ts
// shared/protocol.ts
export type McpTransport = "stdio" | "http" | "sse";

export interface McpServerInfo {
  name: string; // the key in Canvas's MCP settings
  transport: McpTransport;
  command: string | null;
  args: string[];
  url: string | null;
  env: string[]; // names only
  headers: string[]; // names only
  forwarded: boolean; // enabled, and in the deep_reasoner profile's mcp_server_refs (or refs null)
  why_not: "disabled" | "not_in_profile" | null;
}

export interface FrameParams {
  tab: TabId;
  parent: string | null;
  namespace: string | null;
  started: boolean;
  cap: string;
  focus: string | null;
  theme: Readonly<Record<string, string>>;
  /** D4: Canvas's MCP servers, for the Tools tab; null when unread or unreadable. */
  mcp: readonly McpServerInfo[] | null;
}

// page/context.ts
export declare function readMcpServers(request: AgentServerRequest): Promise<McpServerInfo[] | null>;
export declare function mcpServersFromSettings(
  mcpConfig: Readonly<Record<string, unknown>>,
  refs: readonly string[] | null,
): McpServerInfo[];

// ui/types.ts
export type CheckOutcome =
  | "built"
  | "builtin"
  | "invalid"
  | "syntax"
  | "import_failed"
  | "bad_factory"
  | "not_func"
  | "raised"
  | "timeout"
  | "unavailable";

export interface ExampleResult {
  expression: string;
  ok: boolean;
  value: string | null;
  error: string | null;
  seconds: number;
}

export interface CheckReport {
  ok: boolean;
  outcome: CheckOutcome;
  message: string;
  told: string | null;
  traceback: string | null;
  example: ExampleResult | null;
  printed: string;
  seconds: number | null;
  deep_reasoner: string;
  can_save: boolean;
  can_save_anyway: boolean;
}

export interface McpSeen {
  at: string;
  run: string;
  count: number;
  told: string;
}

export interface McpGrant {
  name: string;
  version: number;
  server: string;
  transport: McpTransport;
  command: string | null;
  args: string[];
  url: string | null;
  env: string[];
  headers: string[];
  granted_in: string[];
  shim_current: boolean;
  seen: McpSeen | null;
}

// ui/api.ts
export interface ToolBody {
  yaml: string;
  source?: string | null;
  granted_in?: string[];
  base_version: number;
  accept_check_failure?: boolean; // D4
}

export interface CheckBody {
  yaml: string;
  source: string | null;
  example: string | null;
}

export interface McpGrantBody {
  server: string;
  transport: McpTransport;
  command: string | null;
  args: string[];
  url: string | null;
  env: string[];
  headers: string[];
  granted_in: string[];
  base_version: number;
}

export declare function checkTool(name: string, body: CheckBody): Promise<CheckReport>;
export declare function getMcp(): Promise<McpGrant[]>;
export declare function putMcp(name: string, body: McpGrantBody): Promise<Written<McpGrant>>;

// ui/tools.ts
export type McpRowState = "given" | "disabled" | "not_in_profile" | "gone";

export interface McpRow {
  server: string;
  info: McpServerInfo | null; // null: gone from Canvas's settings
  grant: McpGrant | null;
  state: McpRowState;
  changed: boolean;
  oldShim: boolean;
}

export interface ToolDraft {
  name: string;
  yaml: string;
  source: string;
  example: string;
  grantedIn: string[];
  baseVersion: number; // 0 for a new tool
}

export declare function splitTools(
  tools: readonly ToolRecord[],
  grants: readonly McpGrant[],
): ToolRecord[]; // the user's own tools, in GET /tools order
export declare function defaultToolName(server: string, taken: ReadonlySet<string>): string;
export declare function mcpRows(
  servers: readonly McpServerInfo[] | null,
  grants: readonly McpGrant[],
): McpRow[];
export declare function snapshotOf(info: McpServerInfo): Omit<McpGrantBody, "granted_in" | "base_version">;
export declare function inheritedGrants(
  tool: string,
  effective: readonly Effective[],
): Record<string, string>; // namespace -> the ancestor that grants it
export declare function toolDraftKey(name: string | null): string; // "dr-library.draft.tool.<name>" | ".new"

// ui/editor/python.ts (the "editor" chunk)
export interface PythonEditor {
  setValue(value: string): void;
  destroy(): void;
}

export declare function createPythonEditor(
  parent: HTMLElement,
  value: string,
  onChange: (value: string) => void,
): PythonEditor;

// ui/components (props; Preact function components)
export interface ToolEditorProps {
  record: ToolRecord | null; // null: + New tool
  namespaces: readonly NamespaceRecord[];
  effective: readonly Effective[];
  takenNames: ReadonlySet<string>;
  onSaved: (record: ToolRecord, created: boolean) => void;
  onDeleted: (name: string) => void;
}

export interface CheckResultProps {
  report: CheckReport;
  saving: boolean; // the report came back from a refused save
  onSaveAnyway?: () => void;
}

export interface McpServerRowProps {
  row: McpRow;
  namespaces: readonly NamespaceRecord[];
  effective: readonly Effective[];
  takenNames: ReadonlySet<string>;
  onChanged: () => void;
}
```

---

## Appendix B · Test ids inside the frame (for D4's tests and D5's E12)

Tools tab: `dr-tools-risk` · `dr-tool-<name>` (D3's row id) · `dr-tool-new` · the editor: `dr-tool-name`,
`dr-tool-yaml`, `dr-tool-source` (the CodeMirror host or the textarea), `dr-tool-example`, `dr-check`,
`dr-check-result`, `dr-check-told`, `dr-check-example`, `dr-check-printed`, `dr-tool-grant-<namespace>`,
`dr-tool-save`, `dr-tool-save-anyway`, `dr-tool-delete`, `dr-tool-delete-confirm`, `dr-tool-result`,
`dr-tool-help`, `dr-discard-draft` (D3's) · MCP: `dr-mcp-<server>` (the server's name with every character outside
`[A-Za-z0-9_-]` as `_`), `dr-mcp-name-<server>`, `dr-mcp-grant-<server>-<namespace>`, `dr-mcp-seen-<server>`,
`dr-mcp-update-<server>`, `dr-mcp-remove-<server>`, `dr-mcp-state-<server>`, `dr-mcp-unknown`.
