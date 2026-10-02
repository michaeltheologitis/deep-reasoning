# S2 · Agent commands, options and App panels in the agent-server: design

**TASK-6** · System Designer · task branch `feat/agent-surfaces` in
[michaeltheologitis/software-agent-sdk](https://github.com/michaeltheologitis/software-agent-sdk),
cut from its `deep-reasoning` branch · against the approved spec
[TASK-1](https://app.notion.com/p/3ed62fb22237814ab425c81b3844f012) (S2 in full; §2's decisions,
interfaces and pins; C2 and D3, which consume S2; D1's slash-command and namespace bullets; §4's E11
and testing layers).
**Pinned against:** SDK fork `deep-reasoning` at `91430aa` (upstream `main` at `53a4bc5` plus the ASE
commit, which touches only `AGENTS.md` and `CLAUDE.md`, so every line number below is upstream's) ·
`agent-client-protocol` 0.12.1 (the fork's lock) · D1's design at deep-reasoning `f281109`
(`docs/design/d1-dr-acp.md` §5, the ACP contract S2 forwards) · Canvas fork `deep-reasoning` at
`02b7ac7` (`1ff45c2` plus its ASE commit).

**Revisions** (newest first; the Gate B reader approved the previous one, so each line says which
sentences to stop trusting):
- 2026-10-02 · v1 · first full-depth version.

**Where this file lives, and why nothing trips over it.** `docs/design/` on deep-reasoning's
`design/s2` branch. That branch holds only documents: no docs site, no `pyproject.toml`, no test
runner, no package, so nothing collects, builds or ships this file. No design document goes into the
fork: its three pull requests carry code and tests only, in upstream's layout. The PR split leaves
this file behind.

**Reading guide.** Gate B: §1 to §3 (what S2 changes, the decisions, and where it departs from the
approved spec), then §9 (how E11 is proven). C2's designer: §7 is the contract C2 builds against.
S1's designer and the Conductor: §8 names every place S1 and S2 touch the same code. The Implementer
reads everything; Appendix A (Python) and Appendix B (TypeScript) are the signature reference, and
Appendix C is the test agent's behaviour.

---

## 1 · What S2 changes

Three generic, upstream-shaped changes to the agent-server, the SDK under it and its TypeScript
client. Each is its own pull request, cherry-picked onto the fork's `main` as its own upstream PR.
Nothing in them names deep_reasoner or reads `_meta`.

| PR | What it delivers | Who consumes it |
|---|---|---|
| **1 · ACP session controls** | The ACP bridge keeps the slash commands and config options the agent reports for the conversation's root session, and records each change as one persisted event. A client can set an option, on a live session or before the session starts. A start request may carry option values, which the bridge applies after `session/new` and before the first prompt. A preview runs the real start-up path in a throwaway session to answer "what would this agent offer?" before any conversation exists. | C2's slash menu and option picker, on the home screen (the preview) and in a conversation (the event). D1's decomposition commands and namespace option travel through it. |
| **2 · Conversation header panels** | A Canvas App manifest may declare `contributes.conversation_panels` (an id, a title, an optional icon, and tabs shaped like pages). The agent-server validates them, serves them in the manifest it already returns, and serves the icon. | C2's header-panel slot, and through it D3's Show decompositions. |
| **3 · App backends on macOS** | `darwin-arm64` and `darwin-amd64` backend artifacts; platform detection on macOS; loopback traffic to an App backend never goes through an HTTP proxy; a macOS CI job for the App-backend tests. | D3's Library backend on a Mac; D5's macOS build. |

**Order and independence.** Build PR 3 first (smallest; D3 and D5 need it on a Mac), then PR 2 (C2's
slot and D3 need it), then PR 1 (the largest, and the one that meets S1). The three touch disjoint
files except two: `canvas_extensions/manifest.py`, where PR 2 adds its classes above
`CanvasExtensionContributes` and its new field and validator above that class's existing pages
validator, and PR 3 changes only `BackendPlatform` (line 88), so unchanged lines separate them; and `server_details_router.py`, where PR 1 extends the default capability list and PR 2
appends in `build_server_info`. So each PR's commits cherry-pick onto the fork's `main` without the
others, which the PR split checks.

PR 1, end to end, with D1's `dr-acp` behind the bridge:

```text
Canvas (C2)                         agent-server and SDK (S2)                              dr-acp (D1)
home screen
  POST /api/acp/preview  ─────────▶ resolve the agent exactly as a start would
   (the start payload               throwaway ConversationState, ACPAgent.init_state ─────▶ initialize, session/new
    + acp_config_options)             set_config_option for each chosen value ───────────▶ (commands for that value
                                      wait for the commands report (at most 2 s) ◀──────── before its response)
  ◀── ACPSessionControls              session/close, stop the process, delete the state
  POST /api/conversations ────────▶ fold acp_config_options into the ACPAgent
                                    first run: session/new → model → options → mode ─────▶
                                      record commands and options per ACP session ◀──────── available_commands_update
                                      ACPSessionControlsEvent: ordered, persisted, streamed ──▶ Canvas
                                    first prompt ──────────────────────────────────────────▶ commands [] and the
                                      ACPSessionControlsEvent (no commands) ◀───────────────  namespace narrowed
  POST /api/conversations/{id}/acp/config-options ─▶ session/set_config_option ──────────▶ refused once started
  ◀── 422 "namespace is fixed once a conversation has started (it is 'router')."
```

**What S2 does not change.** The prompt path: a slash command is a user message whose text starts
with `/<name>` (ACP's rule); the bridge already forwards the user's own content first, with per-turn
extensions and the first prompt's system-message suffix after it (`MessageEvent.to_llm_message`,
`event/llm_convertible/message.py:116–119`; `_build_acp_prompt`, `acp_agent.py:3572–3590`), and S2
leaves that alone. The `initialize` call: S2
advertises no new client capability (S1 owns that call, §8), so agents send only `select` options,
not `boolean` ones; S2 still models both. `_meta`: S2 forwards none of it, because nothing reads it.

---

## 2 · Decisions

The spec's seven expensive-to-reverse decisions in §2 stand. These are the next layer down.

| # | Decision | Why | Rejected |
|---|---|---|---|
| A | **One persisted event kind, latest wins: `ACPSessionControlsEvent` carries both lists in full, every time either changes.** | Commands and options are state, not a log: a client needs only the newest. One kind follows upstream's own precedent, `ACPToolCallEvent`, which folds ACP's `tool_call` and `tool_call_update` into one latest-wins event. The event log becomes the only store: serving the controls needs no new route (the events search by kind, newest first), and they survive an agent-server restart with nothing added. | Two kinds mirroring ACP's two updates (two lookups for one picture, two code paths). Keys in `state.agent_state` lifted onto `ConversationInfo`, as `available_models` is: the state-update event for `agent_state` carries the whole internal dict, and writing it from the bridge's thread needs the conversation lock. A `GET …/acp/controls` route: a second source of truth for the same data. |
| B | **Every controls event goes through one ordered, lock-taking emitter owned by `LocalConversation`.** | The bridge receives updates on the ACP portal thread. There, taking the conversation lock deadlocks the synchronous `run()` (the bridge's docstring, `acp_agent.py:1275–1279`), and a turn's `on_event` exists only while a prompt is in flight (`_clear_turn_callbacks`, `:3934`). D1 sends its commands right after `session/new`'s response, outside any turn, and any ACP agent may send updates between turns. So `ACPAgent` gets one sink, `_on_session_event`, which `LocalConversation` wires to a single-worker executor that takes the state lock and calls `_on_event`. Events persist in submission order; a lock in `ACPAgent` makes submission order equal snapshot order; so the last persisted event is always the newest state (§4.3). | The turn's `on_event` during a turn plus something else between turns: two paths, which can reorder at the boundary. The agent-server's `_emit_event_from_thread` (`event_service.py:1000`): a shared thread pool with no ordering, and agent-server only. **S1 needs the same primitive** for child traffic after the parent's turn has ended, which the spec says is "persisted, not dropped" (§8). |
| C | **Option values ride the start request, live on the agent, and apply only to a fresh `session/new`.** | `StartConversationRequest.acp_config_options` is launch-only, like `agent_profile_id`. It is folded into `ACPAgent.acp_config_options` after the agent is resolved, so it works whether the client sent `agent`, `agent_settings` or `agent_profile_id`. `_init` applies the values in order, after the model and before the session mode. A value the agent refuses fails the start, with the agent's own words, rather than running the first prompt in an option the user did not choose (S2's falsifier). The values are not reapplied after a successful `session/load` (the agent restored its own state, and D1 refuses any different value once started), but they are applied when a resume falls back to a fresh session. A live set also writes the value into the agent, as `switch_acp_model` does for the model, so a fresh fallback session comes back with the user's choices. | A field in `ACPAgentSettings`: it fires the persisted-settings guard (a v8 baseline), and no profile needs a stored default, since dr-acp takes its default namespace from the Library. Reapplying on every `session/load`: a resume would fail whenever the agent had moved a value itself. |
| D | **The preview is the real start-up path in a throwaway state, and its body is the start request.** | `POST /api/acp/preview` takes the JSON a client sends to `POST /api/conversations`, resolves the agent with the same code (extracted from `_create_conversation`, §4.6), builds a `ConversationState` under `conversations_dir/preview-<hex>`, and calls `ACPAgent.init_state`. That spawns the agent with the same environment, secrets, authentication, MCP servers and option values as a start; then the preview waits for the first commands report (at most 2 s), sends `session/close` if the agent advertises it, stops the process and deletes the directory. Same request and same code, so a preview can differ from the started session only if the agent itself answers differently. It holds a run slot while it runs, like any running agent. | A hand-written spawn-and-initialize probe: a second copy of environment building, secret injection, authentication, MCP translation and file credentials, which would drift. An agent looked up by name, as the spec's mock-up has it: the agent-server keeps no agents by name; agents are profiles and settings. A full throwaway `LocalConversation`: it runs hooks, opens observability spans and fetches plugins. |
| E | **The model stays with `switch_acp_model`.** | S2's set route refuses the option id `model` (400), and so does `acp_config_options`. The model path keeps `acp_model`, the sentinel LLM, the persisted model hint and cost attribution in step (`set_acp_model`, `acp_agent.py:4416`); a generic set would leave them stale. S2 does record the model path's `set_config_option` responses, so the controls it publishes stay current after a model switch. | Routing `model` through S2's route to `switch_acp_model`: two routes for one action. |
| F | **Panels share one contribution-id namespace with pages; the icon is a validated package file with its own route; an empty panel list is never serialized.** | Canvas mounts App pages by contribution id (`registerPage(contributionId, mount)`, Canvas `src/types/canvas-extension.ts:81`), so a tab id is the id an App registers that tab's page under, and must be unique across pages, panels and tabs. Canvas also keys the drawer's selected tab and pins by tab id (`conversation-tabs.tsx`), so ids are stable storage keys. The icon gets the entrypoint's containment check at install and on every serve. `exclude_if` keeps `"conversation_panels": []` out of `model_dump_json`, because a locally installed App's backend approval revision is the hash of that dump (`backend.py:121–129`); without it, every local App with a backend would need re-approval after an upgrade. | Icons as names from Canvas's icon set (couples the manifest to one client's icon library). Tabs keyed separately from pages (an App could not reuse one registered page in two places without ambiguity about where it mounts). |
| G | **macOS needs more than the two platform names.** | On macOS, Python's `urllib`, httpx and websockets all read the system proxy settings (`urllib.request.getproxies()` falls back to System Configuration there), and macOS's default proxy exceptions (`*.local`, `169.254/16`) do not include `127.0.0.1`. With a system HTTP proxy configured, common on managed networks, the backend's health probe and the bridge to it go to the proxy, and the backend never becomes ready. Linux reads only environment variables, and has the same bug when `HTTP_PROXY` is set without `NO_PROXY`. PR 3 sends loopback traffic direct. A `macos-latest` job runs the App-backend tests, mirroring upstream's `windows-tests` job (`tests.yml:252`). | Only the names, as the spec's evidence proposed: the falsifier ("the Library App's backend does not start on macOS as it does on Linux") would fail on any Mac with a system proxy. |
| H | **Features are detected through `ServerInfo.capabilities`.** | PR 1 adds `acp_session_controls_v1` and PR 2 adds `canvas_conversation_panels_v1`, upstream's existing mechanism (`server_details_router.py:63–70`). C2 can then tell "this App has no panels" from "this agent-server cannot show panels". PR 3 needs none: a backend's status already says `unsupported` and "does not support this platform". | A version comparison in Canvas (breaks on every fork tag). |
| I | **No guard is weakened.** | S2 adds no persisted-settings field (decision C). Every new public schema is fully typed, with no `dict[str, Any]`, so the weak-schema ratchet (`tests/agent_server/test_openapi_contract.py:248`) stays exact. The new event kind is an additive `oneOf` member, which the REST breakage check accepts (`check_agent_server_rest_api_breakage.py:570–583`). New routes and optional fields are additive. §4.9 and §6.4 name the one place a guard might still object. | — |

---

## 3 · Where this design departs from, or adds to, the approved spec

Each is a refinement inside S2's scope. If the Conductor reads any as a change of what was approved,
it goes back to Michael.

1. **The preview's request and response differ from the mock-up.** The body is the start payload a
   client already builds for `POST /api/conversations` (plus `acp_config_options`), not
   `{"agent": "dr-acp", "cwd": …, "config": …}`; the response is
   `{"available_commands": […], "config_options": […]}` with each option value an object
   (`value`, `name`, …), not `"commands"` and bare strings. Why: the agent-server has no agent
   registry by name; the same body guarantees the same agent resolution (E11's "the commands a
   preview lists differ from those the started session lists"); `availableCommands` is ACP's name
   (the spec's decision 4); a picker needs each value's label.
2. **Setting an option takes the id in the body, and answers with the full set.**
   `POST /api/conversations/{id}/acp/config-options` with `{"config_id", "value"}`, not
   `…/config-options/{config_id}` with `{"value"}`; the answer is `{"applied", "controls"}`, not
   `{"id", "current_value"}`. Why: ACP config ids are arbitrary strings, and a path segment cannot
   carry one with a `/`; ACP's own response is the full option set, because setting one option may
   change others; `applied` says whether the value reached a live session or waits for the start.
3. **No GET route for the commands and options.** They are served as the newest
   `ACPSessionControlsEvent`, through the existing events search (decision A). The TypeScript client
   wraps that in one call (§4.8).
4. **One event kind for commands and options together**, not a stream per ACP update (decision A).
5. **The preview does not load plugins attached to that one conversation, nor the per-conversation
   file-credential bindings the agent-server holds** (Codex's `auth.json`). An agent whose commands
   come from a plugin's MCP server shows them only after the start. Why: loading plugins means a git
   fetch and hooks on every preview. It does not affect dr-acp, whose commands come from the Library.
6. **A start-time value the agent refuses ends the start in an error**, with the agent's words, rather
   than continuing in the agent's default (decision C).
7. **macOS gets a loopback-proxy fix and a CI job**, beyond the two platform names the spec's
   evidence called sufficient (decision G).
8. **A dedicated route serves a panel's icon, and two capability strings announce the features**
   (decisions F and H). The spec named neither.
9. **A tab's `path` may be `/`**, which a page's may not: a tab has no route of its own; its path is
   where its page starts inside the panel (§5.1).
10. **The model option cannot be set through S2's route** (decision E).

---

## 4 · PR 1: ACP session controls

### 4.1 The data

Three stable DTOs, added to `openhands/sdk/agent/acp_models.py`, the module that exists so the
agent-server can import ACP shapes without importing `ACPAgent` (its docstring): `ACPAvailableCommand`
(with `ACPCommandInput`), `ACPConfigOption` (with `ACPConfigOptionValue`), and `ACPSessionControls`,
which holds a list of each. One event, `ACPSessionControlsEvent`, in a new
`openhands/sdk/event/acp_session_controls.py`, exported from `openhands.sdk.event`. Full signatures:
Appendix A.1 and A.2.

What one event looks like, for D1's session in the namespace `router` before its first prompt:

```json
{"kind": "ACPSessionControlsEvent", "id": "5f0c…", "timestamp": "2026-10-02T14:22:31.120417",
 "source": "agent", "parent_id": null,
 "available_commands": [
   {"name": "summarize-then-rank", "description": "comparing many courses",
    "input": {"hint": "what to compare"}}],
 "config_options": [
   {"id": "namespace", "name": "Namespace", "type": "select", "current_value": "router",
    "description": "The namespace this conversation runs in. Fixed after the first message.",
    "category": null,
    "options": [{"value": "root", "name": "root", "description": null, "group": null},
                {"value": "router", "name": "router", "description": null, "group": null}]}]}
```

**Normalization at the boundary** (`from_protocol`, tolerant like `ACPModelInfo.from_protocol`):

- A command needs a non-empty string `name`, or it is dropped. A missing `description` becomes `""`.
  `input` is read through 0.12.1's `RootModel` wrapper (`raw.input.root.hint`) or directly
  (`raw.input.hint`); a non-string hint means no input.
- An option is unwrapped from `.root` when present, as `_model_config_option` already does for older
  ACP Python releases (`acp_agent.py:592–614`). `type == "select"`: each `SessionConfigSelectOption`
  becomes an `ACPConfigOptionValue`; each `SessionConfigSelectGroup` contributes its options with
  `group` set to the group's `name`, so a client always gets one flat list. `type == "boolean"`:
  `options` is empty and `current_value` is the boolean. Any other type is dropped and logged at
  debug. `category` keeps ACP's string categories (`mode`, `model`, `model_config`,
  `thought_level`) and is `None` for anything else.
- A dropped entry never fails the update that carried it.

### 4.2 Recording, in the bridge

`_OpenHandsACPBridge` keeps one `ACPSessionControls` per ACP session id, replaced on every change and
never mutated:

- **The first line of `session_update` after the idle-clock reset** is
  `if self._record_session_controls(session_id, update): return`. It handles
  `AvailableCommandsUpdate` (→ `record_available_commands`) and `ConfigOptionUpdate`
  (→ `record_config_options`) and returns `False` for anything else. Today both update types fall
  through to the final `else` and are logged at debug (`acp_agent.py:1547–1548`).
- **Responses are recorded too**: the `configOptions` of the `session/new` and `session/load`
  responses, and of every `session/set_config_option` response, S2's own and the model path's.
- **Per session id, not only the root's.** Two reasons. The root session id is not yet on the agent
  when D1's commands arrive: ACP Python 0.12.1 resolves `new_session` as soon as the response arrives,
  and the notification that follows may be handled before `_init` returns (D1 §5.4 rule 5). And with
  S1, child sessions may report commands of their own. Only the root's are published (§4.3).
- **Masked like tool calls.** Each record passes the agent-supplied text through `_mask_value` before
  it is stored, so a command description that echoes an injected credential never reaches the
  persisted event stream (the same rule as `_mask_tool_call_entry`, `:1406`).
- **One writer.** Every record runs on the portal loop's thread: notifications are handled there, and
  so are `_init` and the coroutines that `set_acp_config_option` and the model path schedule. Readers
  on other threads read a snapshot reference, which is never mutated after it is stored.
- **A commands-reported flag per session** (a `threading.Event`), set by
  `record_available_commands`, is what the preview waits on (§4.6).
- After each record the bridge calls `on_session_controls_changed()`, which the agent binds (§4.3).

### 4.3 Publishing: the root session's controls, in order

`ACPAgent._publish_session_controls()` turns the root session's snapshot into an event:

```python
def _publish_session_controls(self) -> None:
    if self._on_session_event is None or self._session_id is None:
        return
    if self._starting_session:
        return
    with self._session_controls_lock:
        controls = self._client.session_controls(self._session_id)
        if controls == self._published_session_controls:
            return
        self._published_session_controls = controls
        self._on_session_event(ACPSessionControlsEvent.from_controls(controls))
```

It is called by the bridge after every record, and once by `_start_acp_server` itself, right after
`self._session_id` is assigned and `_starting_session` is cleared. Every start goes through
`_start_acp_server`: the first run, a resume after an agent-server restart, and the restart after a
drain timeout (`_restart_session_after_drain_timeout`, `:3524`), which keeps the old session id
while the new process starts. `_starting_session` is set at the top of `_start_acp_server` (and
cleared in a `finally`), so nothing is published from a half-started session, whose root id may
still be the previous process's.

**Invariant: the last `ACPSessionControlsEvent` persisted for a conversation equals the root
session's newest snapshot, one emitter round-trip later.** Why it holds:

1. *Nothing is lost.* A record made while `_starting_session` is set (or before the root id is known)
   happens before the post-start publish reads the snapshot, so that publish includes it. A record
   made after the flag is cleared publishes itself.
2. *Nothing is reordered.* Under the lock, each publish reads the newest snapshot, compares and
   submits; so submissions happen in snapshot order. The emitter is first-in first-out (one worker).
   So the persisted order is the snapshot order, and event timestamps, taken at construction under
   the same lock, agree with it.
3. *No repeats.* A publish that finds the snapshot equal to the last one submitted submits nothing:
   for example the post-start publish after a start in which every record already published itself.

**The emitter.** `LocalConversation._ensure_agent_ready` sets
`self.agent._on_session_event = self._emit_event_from_any_thread` before it calls `init_state`, for
an `ACPAgent` only. `_emit_event_from_any_thread(event)` submits one job to a
`ThreadPoolExecutor(max_workers=1, thread_name_prefix="conversation-events")`, created on first use;
the job runs `with self._state: self._on_event(event)`, so the event is persisted and reaches every
callback (in the agent-server, the WebSocket publisher and the webhooks) exactly like any other. No
deadlock: the portal thread only submits; the worker waits for the lock, which the synchronous
`run()` releases between steps and `arun()` releases while it awaits a prompt (the `astep` docstring,
`:4119–4127`). `close()` shuts the executor down with `cancel_futures=True`; a submit after that is
dropped with a debug log, and the next session start publishes again.

**Without a `LocalConversation`** (an `ACPAgent` driven by hand, the preview, upstream's conformance
probes) nothing is emitted, and `ACPAgent.session_controls` is always readable.

**The agent swap.** `switch_acp_model`, and now `set_acp_config_option`, replace the conversation's
agent with a shallow `model_copy` that shares the live runtime (`local_conversation.py:1721–1803`).
The swap is extracted into one helper, `_replace_acp_agent`, which both call. It already rebinds the
copy's atexit cleanup and file-credential masking (`:1782–1784`); it now also calls
`new_agent._bind_session_controls()`, so the shared
bridge publishes through the copy. The lock is shared by the shallow copy; the last published
snapshot is copied with it.

### 4.4 Option values at the start

- **The request.** `StartConversationRequest.acp_config_options: dict[str, str | bool]`, default `{}`.
  Launch-only: it is added to the explicit exclude set where `_create_conversation` builds the stored
  record (`exclude={"agent_profile_id", "agent_launch_additions", "acp_config_options"}`,
  `conversation_service.py:1845`), so it is never written to `meta.json`; it lives in
  `base_state.json`, inside the agent. A `"model"` key is refused by the request's validator (422 from
  FastAPI).
- **The fold.** In `ConversationService._resolve_launch` (§4.6), after the agent is resolved: a
  non-empty dict with an agent that is not an `ACPAgent` raises `InvalidACPConfigOptions`, which the
  start route gains an `except` for (422, beside its `InvalidParentConversation`,
  `conversation_router.py:284–287`) and the preview route maps the same way; otherwise the agent
  becomes
  `agent.model_copy(update={"acp_config_options": {**agent.acp_config_options, **values}})`.
  `model_copy` skips validators, so the `"model"` check is repeated explicitly
  (`_check_config_option_id`).
- **The agent.** `ACPAgent.acp_config_options: dict[str, str | bool]`, default `{}`, whose validator
  refuses `"model"`. Old `base_state.json` files load with the default.
- **Applying them.** In `_start_acp_server._init`, on the fresh-session path only, in this order:
  `new_session` → record the response's options → the existing model call (`_maybe_set_session_model`,
  now passed the bridge's recorder) → `_apply_config_options(conn, session_id,
  self.acp_config_options, …)` → the existing `set_session_mode`. On the `session/load` path: record the
  response's options, and apply nothing.
- **`_apply_config_options`** sets each value in the dict's order (JSON object order, which the
  request preserves), recording every response, because a set may change other options. An
  `ACPRequestError` with code -32603 propagates unchanged, as it does from `set_acp_model` (the
  retriable class, `_RETRIABLE_SERVER_ERROR_CODES`). Any other `ACPRequestError` becomes
  `ACPConfigOptionRejectedError(config_id, value, message)`, whose `str()` is the agent's own message,
  masked. That includes method-not-found: the user asked for an option the agent cannot take.
- **A refusal at the start.** `ACPConfigOptionRejectedError` leaves `_start_acp_server`; `init_state`'s
  existing handler (`:2312–2343`) emits `ConversationErrorEvent(code=…, detail=…)`, sets the
  conversation to ERROR, cleans up and re-raises. `_classify_acp_init_error` gains a first branch for
  it, returning `"ACPConfigOptionRejected"`, and `_acp_error_detail` already returns `str(exc)` for a
  non-ACP exception, so the detail is the agent's sentence, redacted and masked. The first message is
  persisted but never prompted.
- **Time.** All of this runs inside `_init`, under the existing `acp_startup_timeout` (90 s).

### 4.5 Setting an option

- **`ACPAgent.set_acp_config_option(config_id, value) -> ACPSessionControls`**, live sessions only,
  mirroring `set_acp_model`: `ValueError` for an empty id or `"model"`; `RuntimeError` before a session
  exists; runs `_apply_config_options` for the one value on the portal with
  `_ACP_CONFIG_OPTION_TIMEOUT` (30 s, overridable by the environment variable
  `ACP_CONFIG_OPTION_TIMEOUT`, like the module's other ACP timeouts); a timeout raises `TimeoutError`
  naming the option; a refusal raises `ACPConfigOptionRejectedError`; returns the root session's
  controls after the response is recorded (the record has already published them).
  Why 30 s and not `acp_prompt_timeout` (1,800 s), which `set_acp_model` uses: this call holds the
  conversation lock and answers a click in a picker.
- **`LocalConversation.set_acp_config_option(config_id, value) -> ACPSessionControls | None`**, mirroring
  `switch_acp_model`: `ValueError` if the agent is not an `ACPAgent`; `_check_config_option_id`; then,
  holding the state lock: if the session is live, the agent's call (a refusal propagates before
  anything is written); in every case `_replace_acp_agent({"acp_config_options": {…, config_id:
  value}}, live=live)`. Returns the controls when live, `None` when the value waits for the start.
- **`EventService.set_acp_config_option`** runs the conversation's call in the default executor, as
  `switch_acp_model` does (`event_service.py:2005–2025`), and raises `ValueError("inactive_service")`
  when the service has no conversation.
- **The route** answers `ACPConfigOptionSetResponse{applied, controls}` (§4.7).
- While a turn is running, a set still goes through (`arun` does not hold the lock across the prompt),
  and the agent decides: D1 refuses any change once its run has started; ACP allows others to accept.

### 4.6 The preview

**Shared resolution.** The steps of `_create_conversation` from reading `OH_RUNTIME_LAUNCHED_PROFILE`
through the deployment's system-message suffix (`conversation_service.py:1661–1744`: settings load,
profile resolution and its secret allow-list, `load_memory`, ACP skill sourcing, launch additions)
move unchanged into `ConversationService._resolve_launch(request) -> (request, launched_profile)`,
which also does S2's fold (§4.4). `_create_conversation` calls it first; the preview calls it too.
Worktree creation stays in `_create_conversation`: the preview uses the source workspace.

**`ConversationService.preview_acp_session(request) -> ACPSessionControls`:**

1. `_resolve_launch(request)`; its errors map to statuses exactly as the start route maps them
   (`conversation_router.py:273–287`). A resolved agent that is not an `ACPAgent` raises
   `ValueError("preview needs an ACP agent")` (400).
2. Acquire a run slot (`RunSlot.acquire(self._run_semaphore)`); at the deployment's limit this raises
   `ConversationRunLimitExceeded`, which the app already answers with 429 (`api.py:564`).
3. In a worker thread, call the SDK's `preview_acp_session(agent, workspace, persistence_dir,
   secrets=request.secrets, cipher=self.cipher)` with
   `persistence_dir = self.conversations_dir / f"preview-{uuid4().hex}"`. That directory is a direct
   child of the conversations directory so the agent's npm cache resolves to the one every
   conversation shares (`_acp_npm_cache_dir`, `acp_agent.py:2527`: the persistence directory's
   parent), which keeps Claude Code's and Codex's previews warm. It never holds a `meta.json`, so the
   catalog loader skips it even if a crash leaves it behind (`_load_catalog_sync`, `:745–748`), and
   its name is not a UUID, so it can never collide with a conversation.
4. `finally`: delete the directory (`shutil.rmtree(…, ignore_errors=True)`) and release the slot.

**The SDK's `preview_acp_session`** (`openhands/sdk/conversation/acp_preview.py`, Appendix A.6):

1. The working directory is the request's `workspace.working_dir` when it exists, and otherwise an
   empty `persistence_dir / "workspace"`: what the agent would see in a fresh folder, without creating
   anything in the user's tree.
2. `ConversationState.create(id=uuid4(), agent=agent, workspace=…, persistence_dir=…, cipher=…)`;
   seed its secret registry the way `LocalConversation.__init__` does for a new conversation: the
   agent context's secrets, then `secrets` over them (`local_conversation.py:517–545`).
3. `agent.init_state(state, on_event=<discard>)`: the real start-up, option values included.
4. `agent.wait_for_available_commands(commands_wait_seconds)`: returns at once if the root session has
   reported commands at least once, otherwise after `PREVIEW_COMMANDS_WAIT_SECONDS` (2.0 s). Because
   D1 sends the commands for a newly chosen value before its `set_config_option` response (D1 §5.4
   rule 5), when option values were applied the right commands are already recorded by the time
   `init_state` returns.
5. Read `agent.session_controls`, then `agent.close_acp_session()` (sends `session/close` if the
   agent advertised `sessionCapabilities.close` in its `initialize` response, bounded by 2 s, errors
   logged and ignored), then `agent.close()`.
6. Any failure inside 3 becomes `ACPPreviewError(code, detail)`, with `code` from
   `_classify_acp_init_error` and `detail` from `_acp_error_detail` (redacted and masked). `close()`
   runs in every case.

**Cost.** One agent start-up per call, plus at most 2 s for an agent that never reports commands.
For dr-acp: its front process starts, reads the Library for the snapshot, and starts no worker (D1
§2 step 2); it writes no session index, since it writes that only at a first prompt (D1 §4.4).
Canvas should debounce previews (§7).

### 4.7 The REST surface

| Method and path | Body | Answer | Errors |
|---|---|---|---|
| `POST /api/acp/preview` (new `acp_router`) | `StartConversationRequest` (the start payload; fields that do not reach `session/new`, such as `initial_message`, are ignored) | `ACPSessionControls` | 400 not an ACP agent · 404 unknown profile · 422 invalid request, a dangling MCP reference, or a value the agent refused (`detail` is the agent's sentence) · 429 run limit · 502 the agent failed to start (`detail` names why) · 504 start-up timed out |
| `POST /api/conversations/{conversation_id}/acp/config-options` (new `conversation_acp_router`) | `ACPConfigOptionSetRequest{config_id, value}` | `ACPConfigOptionSetResponse{applied, controls}`: `applied: true` and the agent's resulting controls on a live session; `applied: false` and empty controls when the value waits for the session's start | 400 not an ACP conversation, the `model` option, or an inactive service · 404 unknown conversation · 422 the agent refused (`detail` is its sentence verbatim, for example D1's `namespace is fixed once a conversation has started (it is 'router').`) · 504 no answer within 30 s · 500 the agent's internal error (-32603), as for `switch_acp_model` |
| `POST /api/conversations` (existing) | gains `acp_config_options` | unchanged | 422 `acp_config_options` with an agent that is not ACP, or a `model` key |
| `GET /api/conversations/{id}/events/search?kind=ACPSessionControlsEvent&sort_order=TIMESTAMP_DESC&limit=1` (existing) | — | the newest controls event, if any | — |
| `GET /server_info` (existing) | — | `capabilities` gains `acp_session_controls_v1` | — |

Both new routers live in a new module, `openhands/agent_server/acp_router.py`, registered in
`api.py` after `conversation_router`. Keeping them out of `conversation_router.py` keeps S2 off the
lines S1's cancel route may add there (§8).

The preview's status codes come from the `ACPPreviewError.code`: `ACPConfigOptionRejected` → 422,
`ACPStartupTimeout` → 504, everything else (`ACPAuthRequired`, `ACPSpawnError`, `ACPInitError`) → 502.
The route never answers 401 for an agent's authentication failure, because Canvas reads 401 as its
own session to the agent-server having expired.

### 4.8 The TypeScript client

Upstream's client takes its generated types from the pinned release's OpenAPI and checks in CI that
they are current (`scripts/check-agent-server-api.mjs`), so a PR cannot use types its server has not
released yet. It hand-writes them instead, as it does for client-ahead APIs (the meta-profiles client,
`endpoint-audit.config.json`'s `allowClientOnly`). Our fork's build regenerates the generated types
from our agent-server (`AGENT_SERVER_OPENAPI_PATH`, the spec's pins), where the same shapes then also
appear under their generated names.

- `src/models/acp-session-controls.ts` (new): the interfaces of Appendix B, field for field with the
  Python models.
- `src/events/types.ts`: `ACPSessionControlsEvent extends BaseEvent` with `kind:
  'ACPSessionControlsEvent'`, joined to the `ConversationEvent` union, and an
  `isACPSessionControlsEvent` guard, like the hand-written `ThinkEvent` there.
- `ConversationClient`: `previewAcpSession(payload)`, `setAcpConfigOption(conversationId, configId,
  value)`, and `getAcpSessionControls(conversationId)`, which calls `searchEvents` with
  `{kind: 'ACPSessionControlsEvent', sort_order: 'TIMESTAMP_DESC', limit: 1}` and returns that event's
  lists, or empty lists. `CreateConversationPayload` gains `acp_config_options?`.
- `RemoteConversation`: `setAcpConfigOption(configId, value)` and `getAcpSessionControls()`, next to
  its `switchAcpModel`.
- `endpoint-audit.config.json`: an `allowClientOnly` entry for the two new routes, reason
  "client-ahead until the pinned release carries them", tracking our fork's draft PR.
- Tests beside the existing ones in `src/__tests__/api-clients.test.ts`, as for `switchAcpModel`.

### 4.9 Upstream's guards, for PR 1

| Guard | What PR 1 does to it | Expected |
|---|---|---|
| REST breakage (oasdiff) | new routes; new optional request fields (`acp_config_options` on the start request and on `ACPAgent`); one new member of the event `oneOf` | additive routes and fields pass; the `oneOf` addition is downgraded to a notice by the script's own rule |
| Weak-schema ratchet | eight new schemas, all fully typed | the allowlist stays exact |
| Persisted settings | nothing in `ACPAgentSettings`, profiles or settings | untouched |
| SDK API breakage | additions only; `_apply_acp_model` and the other changed helpers are private | passes |
| Docstrings (MDX) | fenced code only in docstrings, no `>>>` | passes |
| TypeScript client CI | hand-written types; generated file untouched | passes |
| Endpoint audit | report-only; the two new routes are listed as client-ahead | report clean |

### 4.10 Tests for PR 1

In upstream's layout. New files rather than additions to `tests/sdk/agent/test_acp_agent.py`
(10,258 lines, which S1 will edit): the tests stay out of S1's way. The outside world is the ACP agent
process, so tests that cross it run a real one: the scripted test agent of Appendix C, launched as
`acp_command=[sys.executable, <fixture>]`.

| File | Each test pins |
|---|---|
| `tests/sdk/agent/test_acp_models.py` | a grouped select flattens with `group`; a boolean option keeps its boolean value; an unknown option type and a nameless command are dropped, not raised; a command's hint is read through 0.12.1's `RootModel` |
| `tests/sdk/event/test_acp_session_controls_event.py` | the event round-trips through JSON with `kind == "ACPSessionControlsEvent"`; it renders as one short line; `render_resume_transcript` skips it |
| `tests/sdk/agent/test_acp_session_controls.py` | commands reported after `session/new` are published once the session starts; a change during a prompt is published; each session id keeps its own controls and only the root's are published; agent-supplied text is masked; concurrent records publish in snapshot order and the last event is the newest (a stress test with a fake sink); start-time values reach the agent after `session/new` and before the first `session/prompt` (from the agent's request log), in order; a refused start-time value ends `init_state` with `ConversationErrorEvent.code == "ACPConfigOptionRejected"` and the agent's sentence as detail, and no prompt is sent; after a successful `session/load` nothing is reapplied, after a fallback to `session/new` everything is; `"model"` is refused in the field, the set call and the fold; a live set returns the agent's new controls; a refusal raises `ACPConfigOptionRejectedError` with the agent's sentence; a silent agent raises `TimeoutError` within `ACP_CONFIG_OPTION_TIMEOUT`; a model switch through `set_config_option` updates the published `model` option |
| `tests/sdk/conversation/local/test_local_conversation_acp_config_option.py` | a set on a not-yet-started conversation persists into `acp_config_options` and reaches the agent at the start; a live set persists too and survives a reload from `base_state.json`; the agent swap rebinds publishing to the copy; an event emitted from the portal thread during a synchronous `run()` does not deadlock and lands after the step; events emitted after `close()` are dropped |
| `tests/sdk/conversation/test_acp_preview.py` | the preview's controls equal those of a conversation started from the same agent and values, before its first prompt; different values give the values' own commands; `session/close` is sent when advertised and not otherwise; an agent that never reports commands is previewed within `PREVIEW_COMMANDS_WAIT_SECONDS` plus its start-up; a refused value raises `ACPPreviewError` with code `ACPConfigOptionRejected`; the agent process is gone afterwards in every case; a missing working directory is previewed from an empty scratch directory |
| `tests/agent_server/test_acp_router.py` | the preview route answers for `agent_settings` and for `agent_profile_id`, holds a run slot, maps each `ACPPreviewError` code to its status, and leaves no `preview-*` directory; the set route's statuses for every row of §4.7; the start route folds `acp_config_options` into the agent and refuses it for a non-ACP agent; `GET /server_info` lists `acp_session_controls_v1` |
| `tests/agent_server/test_conversation_service.py` (additions) | `_resolve_launch` gives the start and the preview the same agent for each of `agent`, `agent_settings` and `agent_profile_id` |
| `tests/sdk/agent/test_acp_session_controls_live.py` (`pytestmark = pytest.mark.acp_live`) | §9's live tier |

---

## 5 · PR 2: conversation header panels

### 5.1 The manifest

```json
{"schema_version": 1, "name": "dr-library", "display_name": "Library", "version": "1.0.0",
 "entrypoint": "dist/index.js",
 "contributes": {"conversation_panels": [
   {"id": "decompositions", "title": "Decompositions", "icon": "dist/panel.svg",
    "tabs": [{"id": "browse", "title": "Decompositions", "path": "/"},
             {"id": "create", "title": "Create decomposition", "path": "/create"},
             {"id": "namespaces", "title": "Namespaces", "path": "/namespaces"},
             {"id": "tools", "title": "Tools", "path": "/tools"}]}]}}
```

That is C2's mock-up with the two fields every manifest already requires (`display_name`, `version`)
added, and it validates. The rules (Appendix A.8):

- **Panel:** `id` kebab-case; `title` non-empty (the header button's tooltip reads "Show " plus it, and
  it heads the panel); `icon` optional, a package-relative `.svg` or `.png` path, refused if absolute
  or containing `..`, and, at install and on every serve, refused if it resolves (symlinks included)
  outside the package or to anything but a regular file; `tabs` at least one.
- **Tab:** `id` kebab-case; `title` non-empty; `path` defaults to `/` and is `/` or an absolute
  kebab-case path, unique within its panel.
- **One namespace of contribution ids** per extension: page ids, panel ids and tab ids are all
  distinct (decision F). Page ids and paths stay unique as before.
- **Serialization:** `conversation_panels` is omitted from every dump when empty (decision F), so a
  manifest without panels dumps exactly as it does today.
- Manifests are still strict: an invalid panel makes the whole manifest invalid, as an invalid page
  does. On an agent-server without PR 2, pydantic's default drops the unknown key and the App installs
  without panels (C2's failure cell).

What a tab's path means is C2's to define in the host API; S2 only fixes its form. The intent, which
C2's mock-up implies: when a tab is selected, Canvas mounts the page the App registered under the
tab's id, with the tab's path as the mount context's `path`.

### 5.2 Serving

- **The manifest:** unchanged route. `GET /api/canvas-extensions/installed` and
  `…/installed/{name}` already return the validated manifest (`InstalledCanvasExtensionResponse.manifest`,
  `canvas_extensions_router.py:113`), now with `contributes.conversation_panels`.
- **The icon:** `GET /api/canvas-extensions/installed/{extension_name}/panels/{panel_id}/icon`, a
  `FileResponse` mirroring the bundle route (`:416–439`): containment re-checked on every request;
  404 for an unknown extension, an unknown panel or a panel without an icon; media type
  `image/svg+xml` or `image/png` from the suffix; headers `Cache-Control: no-cache`,
  `X-Content-Type-Options: nosniff` and
  `Content-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; sandbox`, so an SVG opened
  directly cannot run script in the agent-server's origin. Like the bundle, it is served for an
  installed App whether or not it is enabled, and it needs the session key, so Canvas fetches it the
  way it fetches bundles (with the key, into a blob URL,
  `canvas-extension-module-loader.ts:26–36`), not with a bare `<img src>`.
- **The capability:** `canvas_conversation_panels_v1`, appended in `build_server_info`, a different
  hunk from PR 1's, so each PR cherry-picks onto `main` alone.

### 5.3 Tests for PR 2

| File | Each test pins |
|---|---|
| `tests/agent_server/canvas_extensions/test_canvas_extensions_manifest.py` (additions) | C2's manifest above validates; a tab path of `/` is accepted and a page path of `/` still is not; each malformed id, title, path and icon is refused; duplicate ids across pages, panels and tabs are refused; a panel without tabs is refused; a manifest without panels dumps without `conversation_panels`, byte for byte as before (so its approval revision is unchanged) |
| `tests/agent_server/canvas_extensions/test_canvas_extensions_entrypoint_containment.py` (additions) | an icon symlinked outside the package, a missing icon and a directory icon each make the installed manifest invalid |
| `tests/agent_server/test_canvas_extensions_router.py` (additions) | the list and get routes return the panels; the icon route serves the file with its media type and the three headers, and answers 404 for each missing case; `GET /server_info` lists `canvas_conversation_panels_v1` |

---

## 6 · PR 3: App backends on macOS

### 6.1 The changes

- **`BackendPlatform`** gains `"darwin-amd64"` and `"darwin-arm64"` (`manifest.py:88`, still one line).
- **`CanvasExtensionBackendManager.current_platform()`** maps `platform.system()` (`Linux`, `Darwin`)
  and `platform.machine()` (`x86_64`/`amd64` → `amd64`, `aarch64`/`arm64` → `arm64`) through two
  constant tables to the four names, and anything else to `None` (`backend.py:134–142`). An x86-64
  Python under Rosetta reports `x86_64` and gets the `darwin-amd64` artifact, which runs under
  Rosetta too.
- **Loopback is never proxied** (decision G):
  - the health probe opens its URL through `urllib.request.build_opener(urllib.request.ProxyHandler({}))`
    (a module constant) instead of `urllib.request.urlopen` (`backend.py:401–406`);
  - `proxy_http` (`docker_runtime/proxy.py`, used by the App-backend bridge and the Docker runtime)
    builds its `httpx.AsyncClient` with `trust_env=False` when the target host is loopback
    (`127.0.0.1`, `::1`, `localhost`);
  - `bridge_websocket` passes `proxy=None` to `websockets.connect` for a loopback target. The lock
    holds websockets 15.0.1; the Implementer confirms that release has the `proxy` parameter (the
    releases from 15 on default it to the system's proxies); if it does not, that release does not
    proxy and this item is dropped and recorded.
  Non-loopback targets keep today's behaviour, so the Docker runtime is unchanged unless it too
  targets loopback, where the same bug applies.
- **Process groups:** nothing changes unless the macOS job shows otherwise. A backend starts in a new
  session and is stopped by group (`start_new_session=True`, `os.killpg`, `backend.py:507, 543–556,
  566–586`), which is POSIX. If the existing stop tests fail on macOS with `PermissionError` from
  `os.killpg` (macOS may refuse to signal a group whose members are all zombies, which is unverified
  here), then `_signal_group` ignores and `_group_alive` treats `PermissionError` as "gone": the group
  is ours and runs as our user, so a refusal means nothing of ours is left to signal. Either way the
  as-built records what the job showed.
- **The macOS CI job**, `macos-app-backend-tests` in `.github/workflows/tests.yml`, a copy of the
  `windows-tests` job's shape (`:252–327`): `macos-latest`, gated by `tj-actions/changed-files` on
  `openhands-agent-server/openhands/agent_server/canvas_extensions/**`,
  `openhands-agent-server/openhands/agent_server/docker_runtime/proxy.py`,
  `tests/agent_server/canvas_extensions/**`, `pyproject.toml`, `uv.lock` and the workflow itself; it
  runs `uv run pytest tests/agent_server/canvas_extensions`. The workflow runs for pull requests to
  any branch (`tests.yml:3–8`), so it runs on the fork's draft PRs and on PRs into `deep-reasoning`;
  public repositories get macOS runners free.

### 6.2 What PR 3 cannot check, for D3 and D5

- **A native arm64 executable must be signed, at least ad hoc**, or macOS kills it at `exec`. Linkers
  sign ad hoc by default; a post-link edit (`strip`, `install_name_tool`) removes it. D3's artifact
  build owns this. A script with a shebang has no such issue.
- **Ship both darwin artifacts** (D3): the universal desktop app (D5) may run on either architecture.
- **The backend's environment is sanitized** (`_SAFE_INHERITED_ENV`); on macOS `TMPDIR` is per-user and
  is on the allowed list, so declare it if the backend needs a temporary directory.

### 6.3 Tests for PR 3

| File | Each test pins |
|---|---|
| `tests/agent_server/canvas_extensions/test_canvas_extension_backend.py` (additions and one fixture change) | `current_platform()` for each row of a `(system, machine)` table, `platform` faked at its boundary with `monkeypatch`; the test extension's fixture declares all four platforms, so the existing lifecycle tests (prepare, start, logs, stop, descendants) run unchanged on the macOS job; a backend becomes ready with `HTTP_PROXY`/`http_proxy` pointing at a dead port (the probe goes direct) |
| `tests/agent_server/canvas_extensions/test_canvas_extension_bridge.py` (additions) | an HTTP request and a WebSocket bridged to a loopback backend with `HTTP_PROXY` pointing at a dead port both reach the backend |
| `tests/agent_server/canvas_extensions/test_canvas_extensions_manifest.py` (additions) | `darwin-arm64` and `darwin-amd64` artifact keys are accepted; an unknown platform key is still refused |

### 6.4 Upstream's guards, for PR 3

`BackendPlatform` sits in a response schema (the manifest's `backend.artifacts` keys), which pydantic
emits as `propertyNames: {"enum": […]}`. The REST check treats a new response enum value as breaking
(`check_agent_server_rest_api_breakage.py:745–757`), but oasdiff 1.19.1 is not expected to read
`propertyNames` (it is a JSON Schema 2020-12 keyword outside what oasdiff diffs). If it does flag
`response-property-enum-value-added` there, the PR keeps the change and adds a narrowly scoped
allowlist pattern for `backend/artifacts` keys, beside the existing `HookConfig` one, since a platform
list is extensible by nature. This is the one guard in S2 I could not settle without running it.

---

## 7 · The contract C2 builds against

Everything below is generic: C2 never needs to know the agent is dr-acp, and must not read `_meta`.

**Feature detection.** `GET /server_info` → `capabilities` contains `acp_session_controls_v1`
(commands, options, preview) and `canvas_conversation_panels_v1` (panels). Absent means the
agent-server predates S2: hide the option picker and agent commands, and show an App's missing panel
as C2's failure cell says.

**Home screen (no conversation yet).**

1. Build the start payload exactly as for `POST /api/conversations` (the same
   `agent_settings` or `agent_profile_id`, workspace and secrets), add the chosen values as
   `acp_config_options: {<config_id>: <value>}`, and `POST /api/acp/preview`. The answer is
   `ACPSessionControls`. Each call starts the agent once; debounce, and call again when the user
   changes an option or the workspace. For dr-acp that is a Python start-up and a Library read (not yet
   measured); budget the agent's start-up plus 2 s.
2. On 422 show `detail` (the agent's sentence); on 429, 502 or 504 show no agent commands and no
   picker, and let the user start anyway.
3. Start with the same payload plus the same `acp_config_options`. They are applied before the first
   message reaches the agent. If the agent refuses one, the conversation ends in `ERROR` with a
   `ConversationErrorEvent` whose `code` is `"ACPConfigOptionRejected"` and whose `detail` is the
   agent's sentence; the first message is not sent.

**In a conversation.**

4. The current commands and options are the newest `ACPSessionControlsEvent`: from the WebSocket as
   they change, and on opening a conversation from
   `GET /api/conversations/{id}/events/search?kind=ACPSessionControlsEvent&sort_order=TIMESTAMP_DESC&limit=1`
   (the client's `getAcpSessionControls`). No event means the agent has reported nothing yet: an
   empty menu and no picker. Every event carries both lists in full; replace, never merge.
5. **The slash menu** lists `available_commands`: `/` + `name`, `description`, and `input.hint` as the
   placeholder for the text after the name when `input` is present. Choosing one inserts
   `/<name> ` in the message box; the user's message is sent as usual and S2 passes its text through
   unchanged. An empty `available_commands` means the agent offers none now: dr-acp clears its
   commands when the first message is accepted, which reaches Canvas as an event before the run's
   output.
6. **The option picker** shows `config_options` except the one whose `id` is `"model"` (the existing
   model picker owns it; S2 refuses to set it). A `select` shows `options` by `name` (grouped by
   `group` when present) with `current_value` selected; a `select` with a single value is fixed, which
   is how dr-acp says its namespace can no longer change; a `boolean` is a toggle (none arrive today,
   because the bridge does not advertise boolean support).
7. **Changing an option:** `POST /api/conversations/{id}/acp/config-options` with
   `{"config_id", "value"}` → `{applied, controls}`. On a live session, `controls` is the agent's new
   state (the event follows too). Before the session starts, `applied` is `false` and the value is
   kept for the start. A 422's `detail` is the agent's sentence; show it as it is.

**Header panels.**

8. `GET /api/canvas-extensions/installed` → each `manifest.contributes.conversation_panels` (absent
   when the App has none, or on an agent-server without the capability). Each panel: `id`, `title`,
   `icon` (or `null`), `tabs[]` of `{id, title, path}`.
9. The icon is `GET /api/canvas-extensions/installed/{name}/panels/{panel_id}/icon`, fetched with the
   session key like the bundle; 404 means draw a default.
10. Tab ids are contribution ids: the App registers each tab's page with `host.registerPage(<tab id>,
    mount)`. Ids are unique across the App's pages, panels and tabs, and are stable, so they can key
    the selected tab and pins. A tab's `path` is `/` or an absolute kebab-case path, unique within its
    panel; what Canvas does with it is C2's host API (the mount context's `path`, by C2's mock-up).
11. Not in S2, and C2's own: the button and its "Show …" tooltip, one right-hand panel at a time,
    `conversationId` in the mount context, the narrow-window page.

---

## 8 · Where S2 and S1 touch the same code

S1 is being designed at the same time; these are the places its spec (S1 in TASK-1) and this design
both touch, and the rule that lets either land first. The single shared design point is item 6; the
rest are textual neighbours.

| # | Place | S1 (from its spec) | S2 | Either order |
|---|---|---|---|---|
| 1 | `acp_agent.py` imports from `acp.schema` | its shim's types | `AvailableCommandsUpdate`, `ConfigOptionUpdate` | adjacent lines in one import list; the second to land merges by hand |
| 2 | `_OpenHandsACPBridge.__init__` | per-session routing state | `_session_controls`, `_commands_reported`, `on_session_controls_changed` | appended attributes; no shared name |
| 3 | `_OpenHandsACPBridge.session_update` | routes every update by session, and handles the shim's three unstable types | one line, first after the idle-clock reset: `if self._record_session_controls(session_id, update): return` | S2's line handles only `AvailableCommandsUpdate` and `ConfigOptionUpdate`, for any session id, and returns before any routing; S1's routing below it never sees those two types. Whoever lands second keeps the line first. |
| 4 | `_start_acp_server._init` | builds the shim's connection class instead of `ClientSideConnection` (`:3070`) and calls `initialize` with client capabilities (`:3090`) | reads `init_response.agent_capabilities.session_capabilities.close` after `initialize`; records the `session/new` and `session/load` responses' options; applies option values after the model call | S2 reads the response object, not the call, so S1 can change the call freely; S2's options block sits after the model block, away from S1's lines |
| 5 | `ACPAgent` private attributes | possibly its own | `_on_session_event`, `_session_controls_lock`, `_published_session_controls`, `_supports_session_close`, `_starting_session` | appended; no shared name |
| 6 | **Emitting events outside a turn** | must persist child traffic that arrives after the parent's turn ended ("persisted, not dropped") | `ACPAgent._on_session_event` and `LocalConversation._emit_event_from_any_thread`: an ordered, lock-taking, single-worker emitter (decision B) | **One primitive, not two.** Whoever lands first builds it with these names and semantics (§4.3, Appendix A.3 and A.4); the other uses it. S1's events are a sequence, not latest-wins state, which the FIFO order serves too. For the Conductor to confirm with S1's designer. |
| 7 | `LocalConversation` | none expected | `_emit_event_from_any_thread`, its wiring in `_ensure_agent_ready`, `set_acp_config_option`, and `_replace_acp_agent` extracted from `switch_acp_model` | only S2 edits these lines, unless item 6 lands with S1 |
| 8 | `openhands/sdk/event/__init__.py` | its two event kinds | `ACPSessionControlsEvent` | adjacent import and `__all__` lines |
| 9 | Routes | `POST /api/conversations/{id}/acp/sessions/{session_id}/cancel` | `acp_router.py` with `acp_router` and `conversation_acp_router` (prefix `/conversations/{conversation_id}/acp`), registered in `api.py` | S1's route fits `conversation_acp_router`; if S1 puts it in `conversation_router.py` instead, nothing conflicts but one `include_router` line in `api.py` |
| 10 | `EventService` | `cancel_acp_session` (expected) | `set_acp_config_option` | adjacent methods |
| 11 | `ServerInfo.capabilities` | possibly one string | `acp_session_controls_v1` in the default list | adjacent list entries |
| 12 | TypeScript client | the cancel call, its event types | §4.8 | the same files (`conversation-client.ts`, `remote-conversation.ts`, `src/events/types.ts`, `endpoint-audit.config.json`, `api-clients.test.ts`); new types in their own files (`src/models/acp-session-controls.ts` for S2) |
| 13 | Test agent | the generic scripted ACP agent (spec §4, layer 3: "Built in S1, reused in C1, S2 and C2") | needs the behaviours of Appendix C | one script, `tests/fixtures/acp/scripted_agent.py` (`tests/fixtures` is on upstream's test-directory allowlist and is shared by the SDK and agent-server suites); whoever lands first creates it, the other extends it behind flags. Its path is for the Conductor to settle with S1's designer. |
| 14 | Upstream guards | its `meta` (ACP `_meta`) fields are untyped dicts, which the weak-schema ratchet refuses unless allowlisted; its new event kinds | one new event kind, fully typed | independent; S2 adds no allowlist entry |
| 15 | `tests/sdk/agent/test_acp_agent.py` | will edit | does not edit (new files, §4.10) | no overlap |

Not shared: `_record_usage`, `ACPToolCallEvent`, the cancel path, `_apply_acp_model` (only S2 changes
its signature), the manifest and backend code (only S2).

---

## 9 · E11 and the testing layers

**E11 · Agent surfaces (S2, C2, D1).** What S2 proves, where, and what it leaves to C2, D1 and D5:

| E11 claim | Proven in S2 by | And elsewhere |
|---|---|---|
| On the home screen the preview lists the namespace's decompositions | `test_acp_preview.py` (the scripted agent's commands per value); the live tier with dr-acp | D1's `test_surfaces.py` (commands per namespace); C2's end-to-end |
| Changing the namespace changes them | previews with different `acp_config_options` give each value's commands; a pre-start set changes what the started session reports | C2's end-to-end |
| The started run uses the chosen namespace | the agent's request log shows `session/set_config_option` before the first `session/prompt`; after the first prompt the reported option equals the chosen value (live tier with dr-acp) | D1's run log, `run.start.namespace` (D1's `test_surfaces.py`, D5's cross-repo run) |
| Commands are gone after the first message | the event after the first prompt has no commands when the agent clears them (scripted agent; live tier with dr-acp) | D1 clears them (D1 §5.2); C2's menu |
| The panel mounts with the right conversation and never shares the right side with the drawer | — (manifest and icon only) | C2 |
| The Library App's backend starts on macOS and on Linux | the macOS job and the Linux suite start a real backend artifact (§6.3) | D3's artifacts; D5's macOS release build starts the Library itself |

**Layer 3 (inside the fork).** §4.10, §5.3 and §6.3, in upstream's folders and style, so they ship in
the upstream PRs. Upstream's full suites stay green on the task branch, and each PR's commits,
cherry-picked onto the fork's `main`, get a draft PR there that is never merged, so the guards that
run only for pull requests to `main` run as upstream would run them (the spec's §4, layer 3).

**The live tier.** `tests/sdk/agent/test_acp_session_controls_live.py`, marked `acp_live`, upstream's
existing marker for tests that launch real ACP agents (deselected by default, `pyproject.toml:102`;
upstream runs `-m acp_live` in a separate job):

- *Built-in providers* (Claude Code, Codex, Gemini, through `npx` with a bogus key, as
  `test_acp_conformance.py` does): a preview succeeds; every command has a name; where the registry
  says the provider selects its model through config options, the `model` option is present.
- *Any agent named by the environment*: when `OPENHANDS_ACP_LIVE_AGENT_COMMAND` (shell-split) and
  `OPENHANDS_ACP_LIVE_CONFIG_OPTIONS` (JSON object of start values) are set, it asserts S2's two
  falsifiers against that agent: the preview equals the started conversation's controls before its
  first prompt; after the first prompt, every chosen option is reported at its chosen value. With
  `OPENHANDS_ACP_LIVE_EXPECT_COMMANDS_CLEARED=1` it also asserts the first prompt leaves no commands.
  Skipped when unset. This is a generic hook, and it is how dr-acp runs behind the bridge.
- *Where it runs with dr-acp:* not in the public fork, because installing dr-acp installs
  deep_reasoner_beta, which needs a read token that must not sit on a public repository's workflows.
  It runs in deep-reasoning's CI: a `workflow_dispatch` job that checks out the fork at the task
  branch's head, installs its three packages and dr-acp, and runs the file with
  `OPENHANDS_ACP_LIVE_AGENT_COMMAND="dr-acp --config <test config>"`,
  `OPENHANDS_ACP_LIVE_CONFIG_OPTIONS='{"namespace": "<a non-default namespace>"}'` and
  `OPENHANDS_ACP_LIVE_EXPECT_COMMANDS_CLEARED=1`. dr-acp clears its commands and narrows the
  namespace when it accepts the first prompt, before it builds the run, so these assertions need no
  model key; with the live tier's `OPENAI_API_KEY` (gpt-6-luna) the run also completes. That job is
  D5's cross-repo CI to own, or a small workflow in deep-reasoning until it exists (§10).

---

## 10 · Open items and decisions for the Conductor

1. **The shared out-of-turn emitter (§8 item 6).** S1 needs it too. Confirm with S1's designer that
   S1 uses `ACPAgent._on_session_event` and `LocalConversation._emit_event_from_any_thread` as
   specified here, or bring the difference back.
2. **The test agent's path (§8 item 13)**: `tests/fixtures/acp/scripted_agent.py`, to settle with S1.
3. **Where the live job with dr-acp runs (§9):** deep-reasoning's CI, because of the private
   dependency. D5 owns cross-repo CI; until D5 lands, a small `workflow_dispatch` workflow in
   deep-reasoning.
4. **The macOS job is part of PR 3 itself** (upstream-shaped, like their Windows job), not a
   fork-only commit. If upstream would rather not run macOS, it is one job to drop from the PR.
5. **Possible guard objection (§6.4):** oasdiff on `BackendPlatform`'s new keys. Settled by running
   the check on PR 3's draft PR.
6. **Unverified on hardware:** `os.killpg` on a zombie-only group on macOS (§6.1), and websockets
   15.0.1's `proxy` parameter (§6.1). Both are settled by the macOS job and the lock, and recorded in
   the as-built.
7. **Noticed outside S2, for D1 (no action in S2):** an ACP agent's prompt carries, after the user's
   own text, any per-turn extensions (`extended_content`), and the first prompt also carries the
   conversation's system-message suffix (secret names, and skills where the deployment manages them),
   each as further text blocks (`message.py:116–119`, `acp_agent.py:3586–3590`). A slash command is
   still the first token of the first block, as D1 expects; but if `dr-acp` joins all text blocks into
   the task, those blocks become part of the task. D1's designer should know.
8. **No new persisted-settings baseline, no new allowlist entry** are expected for S2 (§4.9).

---

## Appendix A · Signature reference (Python)

Every block is valid Python, formatted as ruff would, one field per line. Bodies are `...` where the
behaviour is specified in the sections above; module paths are relative to the fork's root.

### A.1 `openhands-sdk/openhands/sdk/agent/acp_models.py` (additions)

```python
from collections.abc import Sequence
from typing import Any, Literal

from pydantic import BaseModel, Field


ACPConfigOptionType = Literal["select", "boolean"]


class ACPCommandInput(BaseModel):
    """The text a command takes after its name; ACP's ``UnstructuredCommandInput``."""

    hint: str = Field(
        description="Placeholder a client shows until the user types the input.",
    )


class ACPAvailableCommand(BaseModel):
    """One slash command an ACP session offers; ACP's ``AvailableCommand``.

    A client invokes it by sending a user message whose text starts with
    ``/<name>``; the bridge forwards that text unchanged.
    """

    name: str = Field(
        description="Command name, without the leading slash.",
    )
    description: str = Field(
        description="What the command does, in the agent's words.",
    )
    input: ACPCommandInput | None = Field(
        default=None,
        description="Present when the command takes text after its name.",
    )

    @classmethod
    def from_protocol(cls, raw: Any) -> "ACPAvailableCommand | None":
        """Build from an ACP ``AvailableCommand``; ``None`` without a usable name."""
        ...


class ACPConfigOptionValue(BaseModel):
    """One value of a select option; ACP's ``SessionConfigSelectOption``."""

    value: str = Field(
        description="The value to send back in session/set_config_option.",
    )
    name: str = Field(
        description="Human-readable label for the value.",
    )
    description: str | None = Field(
        default=None,
        description="Optional longer description supplied by the agent.",
    )
    group: str | None = Field(
        default=None,
        description="Label of the ACP option group the value came from, if any.",
    )


class ACPConfigOption(BaseModel):
    """One session config option; ACP's ``SessionConfigOptionSelect`` or ``…Boolean``.

    Select groups are flattened into ``options``, each value keeping its
    group's label in ``group``.
    """

    id: str = Field(
        description="The option's id, the configId of session/set_config_option.",
    )
    name: str = Field(
        description="Human-readable label for the option.",
    )
    type: ACPConfigOptionType = Field(
        description="'select' (one of options) or 'boolean'.",
    )
    current_value: str | bool = Field(
        description="The current value: a str for a select, a bool for a boolean.",
    )
    description: str | None = Field(
        default=None,
        description="Optional description for the client to display.",
    )
    category: str | None = Field(
        default=None,
        description="ACP's UX hint: mode, model, model_config or thought_level.",
    )
    options: list[ACPConfigOptionValue] = Field(
        default_factory=list,
        description="The selectable values of a select; empty for a boolean.",
    )

    @classmethod
    def from_protocol(cls, raw: Any) -> "ACPConfigOption | None":
        """Build from an ACP config option; ``None`` for a type this model lacks."""
        ...


class ACPSessionControls(BaseModel):
    """The slash commands and config options an ACP session offers now."""

    available_commands: list[ACPAvailableCommand] = Field(
        default_factory=list,
        description="The agent's slash commands, in the agent's order.",
    )
    config_options: list[ACPConfigOption] = Field(
        default_factory=list,
        description="The agent's session config options, in the agent's order.",
    )

    @classmethod
    def parse_commands(cls, raw: Sequence[Any]) -> list[ACPAvailableCommand]:
        """Normalize ACP commands, dropping unusable entries."""
        ...

    @classmethod
    def parse_config_options(cls, raw: Sequence[Any]) -> list[ACPConfigOption]:
        """Normalize ACP config options, dropping unknown types."""
        ...
```

### A.2 `openhands-sdk/openhands/sdk/event/acp_session_controls.py` (new)

```python
from pydantic import Field
from rich.text import Text

from openhands.sdk.agent.acp_models import (
    ACPAvailableCommand,
    ACPConfigOption,
    ACPSessionControls,
)
from openhands.sdk.event.base import Event
from openhands.sdk.event.types import SourceType


class ACPSessionControlsEvent(Event):
    """The slash commands and config options an ACP session offers now.

    Latest wins: every event carries both lists in full, and the newest event
    of a conversation is its current state. Emitted when the session starts
    and whenever the agent reports a change.
    """

    source: SourceType = "agent"
    available_commands: list[ACPAvailableCommand] = Field(
        default_factory=list,
        description="The agent's slash commands.",
    )
    config_options: list[ACPConfigOption] = Field(
        default_factory=list,
        description="The agent's session config options.",
    )

    @classmethod
    def from_controls(cls, controls: ACPSessionControls) -> "ACPSessionControlsEvent":
        """Build the event for one snapshot."""
        ...

    @property
    def controls(self) -> ACPSessionControls:
        """The snapshot this event carries."""
        ...

    @property
    def visualize(self) -> Text:
        """One line: the command names, then each option's id and current value."""
        ...

    def __str__(self) -> str: ...
```

### A.3 `openhands-sdk/openhands/sdk/agent/acp_agent.py` (additions and changes)

```python
_ACP_CONFIG_OPTION_TIMEOUT: float = float(
    os.environ.get("ACP_CONFIG_OPTION_TIMEOUT", "30.0")
)
_ACP_SESSION_CLOSE_TIMEOUT: float = 2.0


class ACPConfigOptionRejectedError(ValueError):
    """The ACP server refused a session/set_config_option.

    ``str()`` is the server's own message, masked; clients show it as it is.
    """

    def __init__(
        self,
        config_id: str,
        value: str | bool,
        message: str,
    ) -> None:
        super().__init__(message)
        self.config_id = config_id
        self.value = value


def _check_config_option_id(config_id: str) -> None:
    """Refuse an empty id, and the model option, which switch_acp_model owns."""
    ...


async def _apply_config_options(
    conn: ClientSideConnection,
    session_id: str,
    values: Mapping[str, str | bool],
    *,
    on_config_options: Callable[[str, Sequence[Any]], None],
    mask: Callable[[Any], Any],
) -> None:
    """Set each value in order, recording every response.

    Raises:
        ACPConfigOptionRejectedError: The server refused a value (any
            ACPRequestError except -32603).
        ACPRequestError: The server's internal error (-32603), unchanged.
    """
    ...


# Changed: the three model helpers gain a recorder for set_config_option responses.
async def _apply_acp_model(
    conn: ClientSideConnection,
    session_id: str,
    model: str,
    *,
    agent_name: str | None = None,
    via_config_option: bool,
    on_config_options: Callable[[str, Sequence[Any]], None] | None = None,
) -> None: ...


async def _maybe_set_session_model(
    conn: ClientSideConnection,
    agent_name: str,
    session_id: str,
    acp_model: str | None,
    *,
    via_config_option: bool,
    on_config_options: Callable[[str, Sequence[Any]], None] | None = None,
) -> bool: ...


async def _reapply_session_model_on_resume(
    conn: ClientSideConnection,
    agent_name: str,
    session_id: str,
    acp_model: str | None,
    *,
    via_config_option: bool,
    on_config_options: Callable[[str, Sequence[Any]], None] | None = None,
) -> bool: ...


# Changed: first branch added.
def _classify_acp_init_error(exc: BaseException) -> str:
    """... ``ACPConfigOptionRejected``: the server refused a start-time option value."""
    ...


class _OpenHandsACPBridge:
    def __init__(self) -> None:
        # ... existing attributes ...
        self._session_controls: dict[str, ACPSessionControls] = {}
        self._commands_reported: dict[str, threading.Event] = {}
        self.on_session_controls_changed: Callable[[], None] | None = None

    def record_available_commands(
        self,
        session_id: str,
        commands: Sequence[Any],
    ) -> None:
        """Mask, normalize and store a session's commands; then notify."""
        ...

    def record_config_options(
        self,
        session_id: str,
        options: Sequence[Any],
    ) -> None:
        """Mask, normalize and store a session's config options; then notify."""
        ...

    def session_controls(self, session_id: str) -> ACPSessionControls:
        """The session's latest snapshot; empty if it has reported nothing."""
        ...

    def wait_for_available_commands(
        self,
        session_id: str,
        timeout: float,
    ) -> bool:
        """Block until the session has reported commands once, or the timeout."""
        ...

    def _record_session_controls(self, session_id: str, update: Any) -> bool:
        """Record an AvailableCommandsUpdate or ConfigOptionUpdate; else False."""
        ...


class ACPAgent(AgentBase):
    # ... existing fields ...
    acp_config_options: dict[str, str | bool] = Field(
        default_factory=dict,
        description=(
            "Session config option values to set with session/set_config_option "
            "after session/new and before the first prompt, in order. Applied to "
            "a fresh session only, not after session/load. The model is set with "
            "acp_model, never here."
        ),
    )

    @field_validator("acp_config_options")
    @classmethod
    def _reject_model_config_option(
        cls,
        value: dict[str, str | bool],
    ) -> dict[str, str | bool]: ...

    # ... existing private attributes ...
    _on_session_event: Callable[[Event], None] | None = PrivateAttr(default=None)
    _session_controls_lock: threading.Lock = PrivateAttr(default_factory=threading.Lock)
    _published_session_controls: ACPSessionControls | None = PrivateAttr(default=None)
    _supports_session_close: bool = PrivateAttr(default=False)
    _starting_session: bool = PrivateAttr(default=False)

    @property
    def session_controls(self) -> ACPSessionControls:
        """The root session's commands and options; empty before a session."""
        ...

    def set_acp_config_option(
        self,
        config_id: str,
        value: str | bool,
    ) -> ACPSessionControls:
        """Set one option on the live session; return the resulting controls.

        Raises:
            ValueError: ``config_id`` is empty or ``"model"``.
            RuntimeError: There is no live session yet.
            ACPConfigOptionRejectedError: The server refused the value.
            TimeoutError: No answer within ``ACP_CONFIG_OPTION_TIMEOUT``.
        """
        ...

    def wait_for_available_commands(self, timeout: float) -> ACPSessionControls:
        """Wait until the root session has reported commands once, or the timeout."""
        ...

    def close_acp_session(self, timeout: float = _ACP_SESSION_CLOSE_TIMEOUT) -> None:
        """Send session/close if the server advertised it; log and ignore errors."""
        ...

    def _bind_session_controls(self) -> None:
        """Point the bridge's change callback at this agent's publisher."""
        ...

    def _publish_session_controls(self) -> None:
        """Emit the root session's snapshot through _on_session_event (§4.3)."""
        ...
```

### A.4 `openhands-sdk/openhands/sdk/conversation/impl/local_conversation.py` (additions)

```python
from concurrent.futures import ThreadPoolExecutor


class LocalConversation(BaseConversation):
    # Created on first use by _emit_event_from_any_thread; shut down in close().
    _event_emitter: ThreadPoolExecutor | None

    def set_acp_config_option(
        self,
        config_id: str,
        value: str | bool,
    ) -> ACPSessionControls | None:
        """Set an ACP session config option, live or for the session's start.

        Live: issues session/set_config_option and returns the resulting
        controls. Not yet started: returns None and the value is applied after
        session/new. Either way the value is persisted on the agent.

        Raises:
            ValueError: Not an ACP conversation, or ``config_id`` is empty or
                ``"model"``.
            ACPConfigOptionRejectedError: The server refused the value.
            TimeoutError: No answer within ``ACP_CONFIG_OPTION_TIMEOUT``.
        """
        ...

    def _replace_acp_agent(
        self,
        update: dict[str, Any],
        *,
        live: bool,
    ) -> None:
        """Swap in ``agent.model_copy(update=update)``, handing over the runtime.

        Extracted from switch_acp_model; rebinds atexit cleanup, file-credential
        masking and session-controls publishing on the copy, releases the old
        agent's runtime when live, and updates both self.agent and the state.
        """
        ...

    def _emit_event_from_any_thread(self, event: Event) -> None:
        """Persist and publish ``event`` from any thread, in submission order.

        One worker takes the state lock and calls _on_event; never blocks the
        caller. Dropped with a debug log after close().
        """
        ...
```

### A.5 `openhands-sdk/openhands/sdk/conversation/request.py` (addition)

```python
class StartConversationRequest(ConversationConfig):
    # ... existing fields ...
    acp_config_options: dict[str, str | bool] = Field(
        default_factory=dict,
        description=(
            "ACP session config option values to apply after session/new and "
            "before the first prompt, in order. Requires an ACP agent. Launch-only: "
            "folded into the agent, not stored with the conversation record."
        ),
    )

    @field_validator("acp_config_options")
    @classmethod
    def _reject_model_config_option(
        cls,
        value: dict[str, str | bool],
    ) -> dict[str, str | bool]: ...
```

### A.6 `openhands-sdk/openhands/sdk/conversation/acp_preview.py` (new)

```python
from collections.abc import Mapping
from pathlib import Path
from typing import Final

from openhands.sdk.agent.acp_agent import ACPAgent
from openhands.sdk.agent.acp_models import ACPSessionControls
from openhands.sdk.secret.secrets import SecretValue
from openhands.sdk.utils.cipher import Cipher
from openhands.sdk.workspace import LocalWorkspace


PREVIEW_COMMANDS_WAIT_SECONDS: Final[float] = 2.0


class ACPPreviewError(RuntimeError):
    """The agent could not be previewed.

    ``code`` is the ConversationErrorEvent code a start would have reported
    (``ACPConfigOptionRejected``, ``ACPStartupTimeout``, ``ACPAuthRequired``,
    ``ACPSpawnError`` or ``ACPInitError``); ``detail`` is redacted and masked.
    """

    def __init__(
        self,
        code: str,
        detail: str,
    ) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


def preview_acp_session(
    agent: ACPAgent,
    workspace: LocalWorkspace,
    persistence_dir: Path,
    *,
    secrets: Mapping[str, SecretValue] | None = None,
    cipher: Cipher | None = None,
    commands_wait_seconds: float = PREVIEW_COMMANDS_WAIT_SECONDS,
) -> ACPSessionControls:
    """Start ``agent``'s ACP session in a throwaway state, read what it offers, close it.

    Runs ACPAgent.init_state, so the agent starts exactly as a conversation's
    would, ``agent.acp_config_options`` included. Blocking; the caller deletes
    ``persistence_dir``.

    Raises:
        ACPPreviewError: The agent failed to start or refused an option value.
    """
    ...
```

### A.7 `openhands-agent-server` (PR 1)

```python
# openhands/agent_server/acp_router.py (new)
from typing import Final
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from openhands.agent_server.conversation_service import ConversationService
from openhands.agent_server.dependencies import get_conversation_service
from openhands.sdk.agent.acp_models import ACPSessionControls
from openhands.sdk.conversation.request import StartConversationRequest


acp_router = APIRouter(prefix="/acp", tags=["ACP"])
conversation_acp_router = APIRouter(
    prefix="/conversations/{conversation_id}/acp",
    tags=["ACP"],
)

_PREVIEW_ERROR_STATUS: Final[dict[str, int]] = {
    "ACPConfigOptionRejected": 422,
    "ACPStartupTimeout": 504,
}
_PREVIEW_ERROR_DEFAULT_STATUS: Final[int] = 502


class ACPConfigOptionSetRequest(BaseModel):
    """Set one ACP session config option."""

    config_id: str = Field(
        min_length=1,
        description="The option's id, as the agent reports it.",
    )
    value: str | bool = Field(
        description="A select option's value, or a boolean option's value.",
    )


class ACPConfigOptionSetResponse(BaseModel):
    """What setting an option did."""

    applied: bool = Field(
        description=(
            "True when a live session took the value; False when it is kept for "
            "the session's start."
        ),
    )
    controls: ACPSessionControls = Field(
        description="The session's controls after the set; empty when not applied.",
    )


@acp_router.post(
    "/preview",
    responses={
        400: {"description": "The resolved agent is not an ACP agent"},
        404: {"description": "Agent profile not found"},
        422: {"description": "Invalid request, or the agent refused an option value"},
        429: {"description": "Conversation run limit reached"},
        502: {"description": "The agent failed to start"},
        504: {"description": "The agent did not start in time"},
    },
)
async def preview_acp_session(
    request: StartConversationRequest,
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> ACPSessionControls:
    """What an ACP agent would offer for this start request, before it exists."""
    ...


@conversation_acp_router.post(
    "/config-options",
    responses={
        400: {"description": "Not an ACP conversation, or the model option"},
        404: {"description": "Conversation not found"},
        422: {"description": "The agent refused the value"},
        504: {"description": "The agent did not answer in time"},
    },
)
async def set_acp_config_option(
    conversation_id: UUID,
    request: ACPConfigOptionSetRequest,
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> ACPConfigOptionSetResponse:
    """Set an ACP session config option, live or for the session's start."""
    ...


# openhands/agent_server/conversation_service.py (additions)
class InvalidACPConfigOptions(ValueError):
    """acp_config_options sent with an agent that is not an ACP agent."""


class ConversationService:
    async def preview_acp_session(
        self,
        request: StartConversationRequest,
    ) -> ACPSessionControls:
        """Resolve the agent as a start would, then preview it (§4.6)."""
        ...

    async def _resolve_launch(
        self,
        request: StartConversationRequest,
    ) -> tuple[StartConversationRequest, LaunchedAgentProfile | None]:
        """The agent-resolution steps shared by a start and a preview.

        Extracted unchanged from _create_conversation, plus the
        acp_config_options fold.

        Raises:
            ProfileNotFound: Unknown agent_profile_id.
            DanglingMcpServerRef: The profile references a missing MCP server.
            InvalidACPConfigOptions: Option values for a non-ACP agent.
        """
        ...


# openhands/agent_server/event_service.py (addition)
class EventService:
    async def set_acp_config_option(
        self,
        config_id: str,
        value: str | bool,
    ) -> ACPSessionControls | None:
        """Run LocalConversation.set_acp_config_option off the event loop."""
        ...
```

### A.8 `openhands-agent-server` (PR 2)

```python
# openhands/agent_server/canvas_extensions/manifest.py (additions and changes)
from typing import Final

from pydantic import BaseModel, Field, field_validator, model_validator


# "/" or an absolute kebab-case path; a tab's place inside its panel.
_TAB_PATH_PATTERN: re.Pattern[str] = re.compile(
    r"^/(?:[a-z0-9]+(?:-[a-z0-9]+)*(?:/[a-z0-9]+(?:-[a-z0-9]+)*)*)?$"
)
PANEL_ICON_MEDIA_TYPES: Final[dict[str, str]] = {
    ".png": "image/png",
    ".svg": "image/svg+xml",
}


def _validate_contribution_id(value: str) -> str:
    """Kebab-case, as validate_extension_name; shared by pages, panels and tabs."""
    ...


class CanvasExtensionPanelTab(BaseModel):
    """One tab of a conversation panel; its page mounts when the tab is selected."""

    id: str = Field(
        description="Contribution id; the id the App registers this tab's page under",
    )
    title: str = Field(
        min_length=1,
        description="Tab label in the panel's tab row",
    )
    path: str = Field(
        default="/",
        description="Where the tab's page starts inside the panel; '/' is its root",
    )


class CanvasExtensionConversationPanel(BaseModel):
    """A panel opened from a button in the conversation header."""

    id: str = Field(
        description="Contribution id of the panel",
    )
    title: str = Field(
        min_length=1,
        description="Panel title; the header button's tooltip is 'Show' and this",
    )
    icon: str | None = Field(
        default=None,
        description="Package-relative .svg or .png for the header button",
    )
    tabs: list[CanvasExtensionPanelTab] = Field(
        min_length=1,
        description="The panel's tabs, in tab-row order",
    )


class CanvasExtensionContributes(BaseModel):
    """Contributions an extension makes to the Canvas UI."""

    pages: list[CanvasExtensionPage] = Field(
        default_factory=list,
        description="Pages contributed to Canvas navigation",
    )
    conversation_panels: list[CanvasExtensionConversationPanel] = Field(
        default_factory=list,
        exclude_if=lambda value: not value,
        description="Panels opened from buttons in the conversation header",
    )

    @model_validator(mode="after")
    def _validate_unique_contribution_ids(self) -> "CanvasExtensionContributes":
        """Page, panel and tab ids form one namespace per extension."""
        ...


def resolve_package_file(package_root: Path, relative: str, what: str) -> Path:
    """Resolve ``relative`` inside ``package_root`` to a contained regular file.

    The check resolve_entrypoint performs today, shared with panel icons.

    Raises:
        ValueError: It escapes the package or is not a regular file.
    """
    ...


def resolve_panel_icon(
    manifest: CanvasExtensionManifest,
    panel_id: str,
    package_root: Path,
) -> Path | None:
    """The contained icon file of a panel; None for no such panel or no icon.

    Raises:
        ValueError: The declared icon escapes the package or is not a file.
    """
    ...


# openhands/agent_server/canvas_extensions/installed.py (addition)
def get_canvas_extension_panel_icon_path(
    name: str,
    panel_id: str,
    installed_dir: Path | None = None,
) -> Path | None:
    """Re-validated icon path for a serve; None if anything is missing or invalid."""
    ...


# openhands/agent_server/canvas_extensions_router.py (addition)
CanvasExtensionContributionIdPath = Annotated[
    str,
    Path(
        min_length=1,
        max_length=255,
        pattern=CANVAS_EXTENSION_NAME_PATTERN,
        description="Contribution id (lowercase alphanumeric, hyphens)",
    ),
]
_PANEL_ICON_HEADERS: Final[dict[str, str]] = {
    "Cache-Control": "no-cache",
    "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; sandbox",
    "X-Content-Type-Options": "nosniff",
}


@canvas_extensions_router.get(
    "/installed/{extension_name}/panels/{panel_id}/icon",
    responses={404: {"description": "Canvas extension, panel or icon not found"}},
)
def get_canvas_extension_panel_icon_endpoint(
    extension_name: CanvasExtensionNamePath,
    panel_id: CanvasExtensionContributionIdPath,
) -> FileResponse:
    """Serve a conversation panel's icon, re-validating containment."""
    ...
```

### A.9 `openhands-agent-server` (PR 3)

```python
# openhands/agent_server/canvas_extensions/manifest.py (change)
BackendPlatform = Literal["linux-amd64", "linux-arm64", "darwin-amd64", "darwin-arm64"]


# openhands/agent_server/canvas_extensions/backend.py (additions and changes)
_PLATFORM_SYSTEMS: Final[dict[str, str]] = {
    "Darwin": "darwin",
    "Linux": "linux",
}
_PLATFORM_MACHINES: Final[dict[str, str]] = {
    "aarch64": "arm64",
    "amd64": "amd64",
    "arm64": "arm64",
    "x86_64": "amd64",
}
# Loopback health probes never go through an HTTP proxy (macOS system proxies).
_LOOPBACK_OPENER: Final[urllib.request.OpenerDirector] = urllib.request.build_opener(
    urllib.request.ProxyHandler({})
)


class CanvasExtensionBackendManager:
    @staticmethod
    def current_platform() -> BackendPlatform | None:
        """The running platform's artifact key, or None where backends do not run."""
        ...

    @staticmethod
    def _probe(url: str) -> bool:
        """GET ``url`` through _LOOPBACK_OPENER; True on a 2xx or 3xx answer."""
        ...


# openhands/agent_server/docker_runtime/proxy.py (addition)
def _is_loopback_host(host: str | None) -> bool:
    """127.0.0.1, ::1 or localhost: targets that must never be proxied."""
    ...
```

---

## Appendix B · Signature reference (TypeScript client)

```typescript
// clients/typescript/src/models/acp-session-controls.ts (new)
// Hand-written until the pinned agent-server release carries these schemas;
// field for field with openhands.sdk.agent.acp_models.

export type ACPConfigOptionType = 'select' | 'boolean';

export interface ACPCommandInput {
  hint: string;
}

export interface ACPAvailableCommand {
  name: string;
  description: string;
  input?: ACPCommandInput | null;
}

export interface ACPConfigOptionValue {
  value: string;
  name: string;
  description?: string | null;
  group?: string | null;
}

export interface ACPConfigOption {
  id: string;
  name: string;
  type: ACPConfigOptionType;
  current_value: string | boolean;
  description?: string | null;
  category?: string | null;
  options: ACPConfigOptionValue[];
}

export interface ACPSessionControls {
  available_commands: ACPAvailableCommand[];
  config_options: ACPConfigOption[];
}

export type ACPConfigOptionValues = Record<string, string | boolean>;

export interface ACPConfigOptionSetRequest {
  config_id: string;
  value: string | boolean;
}

export interface ACPConfigOptionSetResponse {
  applied: boolean;
  controls: ACPSessionControls;
}
```

```typescript
// clients/typescript/src/events/types.ts (additions)
export interface ACPSessionControlsEvent extends BaseEvent {
  kind: 'ACPSessionControlsEvent';
  available_commands: ACPAvailableCommand[];
  config_options: ACPConfigOption[];
}

export function isACPSessionControlsEvent(
  event: BaseEvent
): event is ACPSessionControlsEvent {
  return event.kind === 'ACPSessionControlsEvent';
}
```

```typescript
// clients/typescript/src/client/conversation-client.ts (additions)
export interface CreateConversationPayload {
  agent_profile_id?: string;
  agent?: unknown;
  agent_settings?: unknown;
  acp_config_options?: ACPConfigOptionValues;
  [key: string]: unknown;
}

export class ConversationClient {
  /** POST /api/acp/preview with the payload a start would send. */
  async previewAcpSession(payload: CreateConversationPayload): Promise<ACPSessionControls> {
    const response = await this.client.post<ACPSessionControls>('/api/acp/preview', payload);
    return response.data;
  }

  /** POST /api/conversations/{id}/acp/config-options. */
  async setAcpConfigOption(
    conversationId: string,
    configId: string,
    value: string | boolean
  ): Promise<ACPConfigOptionSetResponse> {
    const response = await this.client.post<ACPConfigOptionSetResponse>(
      `/api/conversations/${conversationId}/acp/config-options`,
      { config_id: configId, value }
    );
    return response.data;
  }

  /** The newest ACPSessionControlsEvent's lists, or empty lists. */
  async getAcpSessionControls(conversationId: string): Promise<ACPSessionControls> {
    const page = await this.searchEvents(conversationId, {
      kind: 'ACPSessionControlsEvent',
      sort_order: 'TIMESTAMP_DESC',
      limit: 1,
    });
    const event = page.items.find(isACPSessionControlsEvent);
    return {
      available_commands: event?.available_commands ?? [],
      config_options: event?.config_options ?? [],
    };
  }
}

// clients/typescript/src/conversation/remote-conversation.ts (additions)
export class RemoteConversation {
  async setAcpConfigOption(
    configId: string,
    value: string | boolean
  ): Promise<ACPConfigOptionSetResponse> {
    const response = await this.client.post<ACPConfigOptionSetResponse>(
      `/api/conversations/${this.id}/acp/config-options`,
      { config_id: configId, value }
    );
    return response.data;
  }

  async getAcpSessionControls(): Promise<ACPSessionControls> {
    const response = await this.client.get<ConversationEventPage>(
      `/api/conversations/${this.id}/events/search`,
      { params: { kind: 'ACPSessionControlsEvent', sort_order: 'TIMESTAMP_DESC', limit: 1 } }
    );
    const event = response.data.items.find(isACPSessionControlsEvent);
    return {
      available_commands: event?.available_commands ?? [],
      config_options: event?.config_options ?? [],
    };
  }
}
```

The bodies above are written out because they are the whole of each method; the exact option names
of `searchEvents` and the item type of its page follow the client's existing
`ConversationEventSearchOptions` and `ConversationEventPage`, which the Implementer checks.

---

## Appendix C · The scripted test agent

A Python script run as `[sys.executable, "tests/fixtures/acp/scripted_agent.py", *flags]`, built on
ACP Python's own agent side (`acp.run_agent`), with generic names only. S2 needs it to behave as
follows; S1's sub-agent behaviour lives in the same script behind its own flags (§8 item 13).

- **`initialize`:** advertises `sessionCapabilities.close` unless `--no-close`.
- **`session/new`:** answers with one `select` option `profile` (values `fast` and `thorough`, current
  `fast`), then sends `available_commands_update` for the current value: `fast` →
  `summarize` (description "Summarize the input", no input); `thorough` → `summarize` and `compare`
  (description "Compare two things", input hint "what to compare"). With `--no-commands` it never
  sends commands.
- **`session/set_config_option`:** an unknown id → invalid params "unknown option '{id}'"; an unknown
  value → invalid params "unknown profile '{value}'"; after the first prompt, any value but the
  current one → invalid params "profile is fixed once the session has started (it is '{current}')";
  otherwise it sends the new value's `available_commands_update`, then answers with the full options.
  With `--slow-set SECONDS` it waits before answering (for the timeout test).
- **`session/prompt`:** on the first prompt it sends `available_commands_update` with no commands and
  a `config_option_update` whose `profile` lists only the current value, then one
  `agent_message_chunk` echoing the prompt's first text block, a `usage_update`, and `end_turn`.
- **`session/load`:** loads a session it created in this process (or answers invalid params), answers
  with its options, and sends its commands if it has not been prompted.
- **`session/close`:** answers `{}`.
- **Request log:** when `SCRIPTED_ACP_LOG` names a file, it appends one JSON line per request
  (`{"method", "params"}`) in arrival order, so tests assert what reached the agent and when.
