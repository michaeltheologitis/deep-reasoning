# S1 · ACP sub-agent sessions in the agent-server — design

**TASK-3** · System Designer · code lands in the SDK fork
[michaeltheologitis/software-agent-sdk](https://github.com/michaeltheologitis/software-agent-sdk), branch
`feat/acp-subagent-sessions`, cut from `deep-reasoning` at `91430aa`, as one pull request · against the approved
spec [TASK-1](https://app.notion.com/p/3ed62fb22237814ab425c81b3844f012) (S1, §2, C1, §4 E5 and the layers, the
2026-10-02 amendment) and D1's wire contract (`deep-reasoning` `f281109`, `docs/design/d1-dr-acp.md` §5).
**Pinned against:** SDK fork `91430aa` (= upstream `53a4bc5` plus the ASE commit, which touches only `AGENTS.md`
and `CLAUDE.md`, so every `file:line` below is also upstream `53a4bc5`'s) · `agent-client-protocol` 0.12.1 (the
fork's lock) · ACP schema 1.24.1 `schema.unstable.json` (sha256 `6449a87a…be09109e`, the file D1 validates
against) · pyright 1.1.411 in `standard` mode (the fork's pre-commit).

**Revisions** (newest first; each line says which sentences to stop trusting):
- 2026-10-02 · v1 · first full-depth version, aligned before its first commit with S2's design (deep-reasoning
  `design/s2` `9e32261`, `docs/design/s2-agent-surfaces.md`) on three shared pieces, at the Conductor's request:
  one ordered emitter for events that arrive outside a turn (`ACPAgent._on_session_event`,
  `LocalConversation._emit_event_from_any_thread`, S2 §4.3), one scripted test agent at
  `tests/fixtures/acp/scripted_agent.py` (S2 Appendix C), and one route module, `acp_router.py` (S2 §4.7).
  Whichever PR lands first creates each; the other uses it.

**Build notes.** In this container `uv` is 0.8.17, which cannot parse the fork's `exclude-newer = "7 days"`
(`pyproject.toml:7`); run every check in the fork with `uvx uv@latest` (0.12.22 works), for example
`uvx uv@latest run pytest tests/sdk/agent/test_acp_subagents.py`. The probes this design cites ran in a scratch
virtualenv with `agent-client-protocol` 0.12.1 and pyright 1.1.411, not in the fork's environment.

**Where this file lives, and why nothing trips over it.** `docs/design/` on deep-reasoning's `design/s1` branch,
not in the fork: the fork's branches carry only code upstream would accept, and upstream keeps PR-only design
notes in `.pr/`, which its own workflow deletes. deep-reasoning has no docs site, no package and no test runner
at this commit; once D1's `pyproject.toml` lands, pytest is pointed at `tests/` only and the sdist excludes
`docs/` (D1 §8.5), so this file is never collected, built or shipped.

**Reading guide.** Gate B: §1–§3 (the reasoning, about 15 minutes). C1's designer: §5 (what is stored and how to
read it) and §4.5. S2's designer: §9 (every place S1 and S2 touch the same code). D5's designer: §4.6 (the
opt-in), §4.10 (the scripted agent that replays D1's recordings) and §7.4 (the live tier). The Implementer reads
everything; Appendix A is the signature reference, every block valid, ruff-formatted Python or TypeScript, plus
the scripted agent's command line.

---

## 1 · What S1 changes

### 1.1 The problem, at `53a4bc5`

An ACP agent that exposes sub-agent sessions (ACP schema 1.24.1, unstable since 2026-09-30) cannot be driven
through OpenHands' bridge today, for four reasons, each verified:

1. **The bridge never asks.** It calls `initialize` with no client capabilities (`acp_agent.py:3090`), so a
   conforming agent may not send sub-agent updates at all (the RFD: an agent MUST NOT unless the client
   advertised `subagents`). Even if it asked, ACP Python 0.12.1's `ClientCapabilities` has no `subagents`
   field, and its `initialize` serializes by the declared type, so the field is dropped on the way out.
2. **The library drops the updates.** 0.12.1's router validates every `session/update` against
   `SessionNotification`, whose union has no `subagent_update`, `session_message` or `session_message_chunk`:
   each one fails with a `ValidationError` inside the library (`acp/router.py`, `model.model_validate`) and is
   logged as an exception; the bridge never sees it.
3. **Everything else is merged into the root.** `session_update` (`acp_agent.py:1427–1548`) routes nothing by
   session except the `ask_agent` fork (`:1445–1451`). A child's `agent_message_chunk` joins the root's answer,
   its tool calls are stored as if the root ran them, and a child's `usage_update` overwrites the bridge's
   context-window fallback (`:1471–1478`).
4. **Nothing can stop one child.** There is no route, SDK call or client method that sends `session/cancel`
   for a session other than the root.

### 1.2 The change

Behind one opt-in per agent (`acp_subagents`, default off), the bridge advertises `subagents`, receives the three
unstable updates through a small shim ahead of the library's router, routes every update by session, and
persists each child: its association with its parent (with the spawning tool call), its tool calls, its
messages, its own text and its latest cost. A new REST call cancels one child that offers `cancel`. With the
opt-in off, nothing changes: the stock connection class, the stock `initialize` call, the stock routing, and
byte-identical stored events.

```text
ACP agent process (dr-acp, or any agent speaking schema 1.24.1's sub-agent sessions)
   │ stdout, JSON-RPC lines
   ▼
_filter_jsonrpc_lines (unchanged, :1047)
   ▼
SubagentClientSideConnection  ── acp_unstable.py (THE SHIM; deleted when the library catches up)
   │  session/update with sessionUpdate ∈ {subagent_update, session_message, session_message_chunk}
   │     → parsed by the shim's models → bridge.unstable_session_update(sessionId, update)
   │  everything else → the library's own router → bridge.session_update(...) as today
   ▼
_OpenHandsACPBridge (acp_agent.py)
   │  commands, options → S2's recorder (its first line in session_update; not S1's)
   │  fork session      → fork accumulator (unchanged)
   │  root or unknown   → today's path (answer text, thoughts, root tool calls, root usage)
   │  announced child   → ACPSubagentSessions (acp_subagents.py): merge, segment, cost
   │                       child tool calls: today's tool-call path, keyed by (session, toolCallId)
   ▼
root events:  the turn's on_event, as today
child events: ACPAgent._on_session_event = LocalConversation._emit_event_from_any_thread
              (shared with S2: one worker, first in first out, takes the state lock; the ACP
              thread only submits), during a turn and between turns alike
   ▼
ConversationState.events ── REST /events/search, WebSocket ── TS client ── Canvas (C1)

cancel: POST /api/conversations/{id}/acp/sessions/{session_id}/cancel   (acp_router.py, shared with S2)
        → EventService → LocalConversation.cancel_acp_session → ACPAgent.cancel_acp_session
        → (on the ACP loop) check the live cancel grant → session/cancel {sessionId: child}
        → the agent's own idle/cancelled update arrives and is persisted like any other
```

### 1.3 Decisions this design takes

The spec's decisions stand (§2: generic and additive, ACP's names, `_meta.deep_reasoner` never read; S1's
bullets). These are the next layer down.

| # | Decision | Why | Rejected |
|---|---|---|---|
| A | **One opt-in gates everything**: `ACPAgent.acp_subagents` / `ACPAgentSettings.acp_subagents`, default `False`. Off: the stock `ClientSideConnection`, the stock `initialize(protocol_version=1)` call, today's routing, and no new fields written. | Claude Code, Codex and Gemini run exactly as today while ACP's draft is unstable; every upstream test that patches `acp_agent.ClientSideConnection` or spies `ClientSideConnection.initialize` (the conformance probe, `test_acp_conformance.py`) keeps working untouched. | Routing by session for every agent: a behaviour change for providers that never asked for it. |
| B | **The shim is a `ClientSideConnection` subclass** that wraps its connection's handler and sends `initialize` with a standalone request model carrying `subagents`. It needs one targeted pyright suppression, because 0.12.1 marks the class `@final` (verified). | The fewest lines that keep every message in arrival order, keep the library's router for everything stable, and put the capability on the wire. | (1) Connection observers (`Connection(..., observers=)`, public): the router still raises and logs an exception per unstable update, and every incoming message is deep-copied. (2) Rewriting unstable updates into an extension method in the stdout filter: in order and public, but it hides a protocol message behind a fake one. (3) Re-implementing `ClientSideConnection` from `Connection` and `build_client_router`: duplicates ~250 library lines. (4) Subclassing `InitializeRequest` with a narrower field type: fails pyright's variable-override check (verified). |
| C | **A session is a child iff it was announced** (a `subagent_update` on this connection, or a child recorded in this conversation's history). Traffic for any other non-root session follows today's root path, with one WARNING per session id. | The RFD makes announcement-before-traffic the agent's obligation; routing by announcement keeps every existing bridge test (which sends updates under arbitrary session ids) valid. | Treating every non-root id as a child: an unannounced id has no parent to place it under. |
| D | **One persisted snapshot per association change**: `ACPSubagentEvent` carries the whole merged association (the RFD's patch rules already applied). | Consumers keep the latest per session; nobody re-implements "omitted keeps, `null` clears, an object replaces" in TypeScript. | Persisting raw patches. |
| E | **The root is `None` in persisted routing fields** (`acp_session_id`, `parent_session_id`); message participants are stored verbatim. | Mirrors the spec's "`acp_session_id` absent = root"; survives the bridge falling back to a fresh ACP session after a failed `session/load`, when the root's id changes but its children stay under the root. | Storing the root's ACP id everywhere: a fallback session would orphan every earlier child. |
| F | **A child's own streamed text is persisted per segment**, as a third event kind, `ACPSessionTextEvent` (a divergence, §3 item 1). | D1 sends each child's reasoning and its Stop acknowledgement as `agent_thought_chunk` on the child's session; the RFD models a child as a full transcript. Without it, both are dropped. | Dropping child text (spec reading); merging it into the root (today's bug). |
| G | **Every child event goes through the conversation's one ordered emitter, during a turn and between turns**: `ACPAgent._on_session_event`, which `LocalConversation._ensure_agent_ready` wires to `_emit_event_from_any_thread` (one worker, first in first out, which takes the state lock and calls `_on_event`). The same primitive S2 uses for commands and options (S2 decision B). The root's events keep today's path, and the root's trailing traffic between turns stays dropped, as today. | The spec's "persisted, not dropped", without the ACP thread ever taking the state lock (a deadlock under the synchronous `run()`, §6). One path per stream means a child's events can never overtake each other, which "latest wins" needs. One primitive in both PRs, not two. | (1) The turn's `on_event` during a turn and a second sink between turns: two paths reorder at the boundary. (2) A deferred queue persisted at the next turn (this design's first draft): late traffic waits for a turn that may never come. (3) Child tool calls on the turn's `on_event` and child text through the emitter: a child's thought could be stored after the cell it preceded. |
| H | **Cancel authorization is in memory, per connection, and only from fresh updates.** A grant counts only when it arrived after the `session/load` response; when a connection starts, the bridge persists, for each child whose last snapshot was cancellable or active, a snapshot with `source="environment"`, `cancellable=False` and `state=None`. | The RFD's freshness rule: historical capabilities never authorize a mutation, and current state starts unconfirmed after a reconnect; the stored events say so, so C1 hides Stop. | Trusting the last persisted `cancellable` (a Stop that answers 409 or, worse, cancels a reused id). |
| I | **Cancel never takes the conversation's state lock.** It runs on the ACP loop, checks the grant there, sends `session/cancel`, and returns; the outcome arrives as the child's own update. | The sync run loop holds the state lock for a whole turn; a lock-taking cancel would wait for the turn it is trying to shorten. | Routing cancel through `with state:` as `switch_acp_model` does. |
| J | **Costs are never added.** A child's cost lives on its association; `_record_usage` keeps booking only the root's, as today (`:2046`). | ACP forbids clients to add parent and child costs; D1's root cost already covers its descendants. | Summing children into the conversation's metrics. |
| K | **One scripted test agent, `tests/fixtures/acp/scripted_agent.py`, shared with S2** (S2 Appendix C): S2's behaviours by default, S1's behind its own flags, `--subagents` (a built-in sub-agent run) and `--transcript PATH` (replays any JSONL transcript, including D1's golden recordings). It needs only `agent-client-protocol`, so it runs by path from a checkout of the SDK fork. | One fixture for the spec's "built in S1, reused in C1, S2 and C2"; `tests/fixtures` is shared by the SDK and agent-server suites. D5's cross-repo CI already checks out the fork at its pinned tag (spec Q8), and so can Canvas's mock-LLM end-to-end run (C1, C2). | Shipping it in the SDK wheel as `openhands.sdk.testing.scripted_acp_agent` (this design's first draft): `python -m` from any install, but a test fixture in the product package, and a second fixture beside S2's. |

---

## 2 · A sub-agent's life through the bridge

The spec's S1 mock-up, in wire order, with what the bridge stores. Ids are D1's (§5.1 of its design), shown in
its short form (`n2` is `20261002-142233-4f1a2b-n2`, `c1.1` is `…-n1-c1`); the wire and the store always carry the
full ids.

1. **Start.** `LocalConversation._ensure_agent_ready` sets `agent._on_session_event` to the conversation's
   emitter, then calls `init_state` → `_start_acp_server`. The bridge is built with `subagents=True` and handed
   that emitter; its `ACPSubagentSessions` is seeded from this conversation's stored events (nothing on a first
   start). The connection is a `SubagentClientSideConnection`; `initialize` goes out with
   `"clientCapabilities": {"auth": {}, "subagents": {}}` (the library's own defaults plus ours, verified on the
   wire). `session/new` answers `s-7c1f…`, which the router records as the root.
2. **Prompt.** `_reset_client_for_turn` wires the turn's `on_event`, as today; S1 does not touch it.
3. **The spawning cell.** `root tool_call c1.1` → today's path → `ACPToolCallEvent` (no `acp_session_id`),
   stored at once through the turn's `on_event`.
4. **The announcement.** `root subagent_update n2 {title, capabilities.cancel, state running,
   _meta.openhands.parentToolCallId = c1.1, _meta.deep_reasoner = …}` reaches the bridge through the shim →
   `ACPSubagentEvent(acp_session_id=n2, parent_session_id=None, parent_tool_call_id=c1.1, state="running",
   cancellable=True, meta={…})`, submitted to the emitter, like every event from steps 4 to 10. `n2` is now a
   child. (In the agent-server, which drives `arun()`, the emitter's worker stores each event as it comes,
   because the state lock is free while a prompt is awaited; under a synchronous `run()` they are stored right
   after the step.)
5. **The task.** `root session_message → n2` → `ACPSessionMessageEvent(acp_session_id=None, message_id=…-n2-t1,
   sender=s-7c1f…, recipient=n2, text=task)`.
6. **The child thinks.** `n2 agent_thought_chunk` → appended to `n2`'s pending text segment; nothing stored yet,
   and nothing reaches the root's thoughts.
7. **The child's cell.** `n2 tool_call c2.1` → flushes the segment as `ACPSessionTextEvent(acp_session_id=n2,
   thought=True, text=…)`, then today's tool-call path with the entry keyed `(n2, c2.1)` →
   `ACPToolCallEvent(acp_session_id=n2, meta={deep_reasoner: …})`; its `tool_call_update` → the terminal
   `ACPToolCallEvent`.
8. **The answer.** `n2 session_message → root` → `ACPSessionMessageEvent(acp_session_id=n2, …)`.
9. **The cost.** `n2 usage_update cost 0.0004 USD` → the association's cost changes →
   `ACPSubagentEvent(n2, state="running", cost=0.0004, cost_currency="USD")`. The root's usage sync, its
   context window and the conversation's metrics are untouched.
10. **Idle.** `root subagent_update n2 {state idle, stopReason end_turn, _meta …}` →
    `ACPSubagentEvent(n2, state="idle", stop_reason="end_turn", cost=0.0004, cancellable=True)`.
11. **The root finishes.** `root tool_call_update c1.1 completed`, the root's `agent_message_chunk`s, the root's
    `usage_update`, the response. At the end of `_do_acp_prompt` the bridge submits every child's pending text;
    `_finalize_successful_turn` books the root's cost only, force-completes only root tool calls left open, and
    stores the `FinishAction` with the root's text alone.

What `GET /events/search` then holds for the sub-agent part (the mock-up's `jq` line, against the real route):

```bash
curl -s "$AS/api/conversations/$C/events/search?limit=100" | jq -r '.items[] | select(.kind | startswith("ACP"))
  | [.kind, .acp_session_id // "root", .state // .title // .text // ""] | @tsv'
```

```text
ACPToolCallEvent         root   Run cs = [...]; summaries = run_all({...})
ACPSubagentEvent         n2     running        (parent root, in c1.1, cancellable)
ACPSessionMessageEvent   root   Summarize the workload of CS101.
ACPSessionTextEvent      n2     CS101's record: credits and prerequisites, then a one-line verdict.
ACPToolCallEvent         n2     Run c = catalog['CS101']; print(c['credits'], len(c['prereqs']))
ACPToolCallEvent         n2     Run c = catalog['CS101']; ...                      (completed: 3 0)
ACPSessionMessageEvent   n2     3cr, 0 prereqs — light
ACPSubagentEvent         n2     running        (0.0004 USD)
ACPSubagentEvent         n2     idle           (end_turn, 0.0004 USD)
ACPToolCallEvent         root   Run cs = [...]; summaries = run_all({...})        (completed)
```

**Stop on one child.** `POST …/acp/sessions/n3/cancel` → 200 `{"session_id": "…-n3", "requested": true}`. The
bridge sent `session/cancel {"sessionId": "…-n3"}`; dr-acp acknowledges with a thought on `n3` (stored as an
`ACPSessionTextEvent` at the next boundary) and, as each agent of the branch actually ends, sends its idle
`subagent_update` with `stopReason: cancelled`, each stored as an `ACPSubagentEvent`. A child that did not
advertise `cancel`: 409, `ACP session fx2 does not accept cancel; cancel the conversation's turn instead.`

**Restart.** The agent-server restarts mid-run. On the next message, `_start_acp_server` seeds the router from
the stored events (n2…n4 are known children) and, for each child whose last snapshot was cancellable or active,
submits `ACPSubagentEvent(source="environment", state=None, cancellable=False)`; then it calls `session/load`.
dr-acp replays its run log before the response, which the bridge neither stores again (it is already stored)
nor lets authorize anything. C1 shows those children with unconfirmed state and no Stop.

---

## 3 · Where this design departs from, or adds to, the approved spec

Each is a refinement inside S1's scope. If the Conductor reads any as a change of what was approved, it goes back
to Michael.

1. **A third persisted kind, `ACPSessionTextEvent`, for a child's own `agent_message_chunk` and
   `agent_thought_chunk`.** The spec names two kinds (the association and the directed message). D1 sends each
   child's reasoning and, by its §3 item 9, its Stop acknowledgement ("said where the user sees them") as thoughts
   on the child's session; with two kinds the bridge has nowhere to put them and they are lost. Text is stored
   per segment (consecutive chunks of one kind in one session), not per chunk. About 60 lines with tests.
2. **`ACPSubagentEvent.parent_tool_call_id` is a typed field**, lifted from `_meta.openhands.parentToolCallId`
   (the generic key of spec §2 decision 3), and sticky: an update whose `_meta` lacks the key, or clears
   `_meta`, does not move the child out of its cell. `meta` itself is stored verbatim (masked), so
   `_meta.deep_reasoner` passes through unread.
3. **The shim needs one pyright suppression and a standalone `initialize` request model.** 0.12.1 marks
   `ClientSideConnection` `@final`; subclassing it fails pyright `standard` ("Base class … is marked final",
   verified), so the class line carries `# pyright: ignore[reportGeneralTypeIssues]` with a one-line reason.
   Subclassing `InitializeRequest` with the capability subclass also fails (`reportIncompatibleVariableOverride`,
   verified), so the request model is a small standalone model. Both verified to put `subagents` on the wire.
4. **`ACPToolCallEvent.acp_session_id` and `meta` are written only with the opt-in on.** The spec says the event
   gains them; populating `meta` for every agent would change Claude Code's stored events (its adapter puts tool
   output in `_meta`), against decision A.
5. **The cancel route has five outcomes, not two**: 200; 404 (no conversation, or no sub-agent session with that
   id); 400 (not an ACP conversation, matching `switch_acp_model`); 409 (no live connection, the root session, or
   no current `cancel` grant); 504 (the notification was not written within 2 s). The spec's 409 text is kept
   verbatim.
6. **Child traffic after the parent's turn is stored as it arrives**, through S2's emitter (decision G). It is
   lost only if it is still queued when `close()` cancels the emitter's pending jobs, or arrives after that
   (dropped with a DEBUG line, S2's emitter semantics). dr-acp sends none (D1 §5.4 rule 7). Under a synchronous `run()`, a turn's child events are stored
   just after the step's own events; C1 places children by id, not by position, so nothing reads that order.
7. **A reconnect writes "controls off, state unconfirmed" snapshots** (`source="environment"`), so the stored
   events, not only the bridge's memory, carry the RFD's freshness rule. Between an agent-server crash and the
   next connection the old snapshot still shows; the route answers 409 there.
8. **The generic fixture is S2's scripted test agent** (`tests/fixtures/acp/scripted_agent.py`) with S1's flags,
   one of which replays JSONL transcripts in D1's recording format (§4.10). Canvas (C1, C2) and D5 run it by path
   from a checkout of the SDK fork at the pinned tag.
9. **The cancel route lives in S2's new `acp_router.py`**, on its `conversation_acp_router` (prefix
   `/conversations/{conversation_id}/acp`), not in `conversation_router.py`.
10. **The TypeScript client's new event types are hand-written** until upstream's pinned release artifact
    carries them (its generated schema is pinned to a release, `package.json` `config.agentServerImage`), and the
    new route is listed as client-ahead in `endpoint-audit.config.json`. `ACP_SETTINGS_KEYS` gains
    `acp_subagents`, or Canvas would strip the opt-in when it filters an ACP settings payload.
11. **Upstream's guards, checked:** the OpenAPI breakage check explicitly allows additive `oneOf` expansion and
    optional response properties (`check_agent_server_rest_api_breakage.py`, rules at `:29–33, :571`), so no
    migration is needed; the persisted-settings change is additive (no schema bump), with a new v7 fixture; and
    the OpenAPI weak-schema ratchet (`check_agent_server_openapi_quality.py`, run on the exported schema by the
    release workflow, `release-binaries.yml:215`, against an exact allowlist) flags every new `dict[str, Any]`,
    so each `meta` field gets an allowlist entry, as `raw_input`/`raw_output` have today. ACP's `_meta` is an
    arbitrary object by protocol, so it cannot be typed away as S2's fields are.
12. **Directed messages store text only** (the spec's field); non-text content blocks are counted in a DEBUG line
    and not stored.
13. **The mock-up's `GET /events` is `GET /events/search`** in the real API (`event_router.py:68`).
14. **No optimistic cancel marking.** The RFD says a client SHOULD mark a cancelled child's unfinished tool calls
    as cancelled; D1's Stop lands at the agent's next turn and lets a running cell finish, so a client-side
    "failed" would be contradicted moments later. The bridge stores only what the agent reports.
15. **Four more SDK consumers change, which the spec did not list:** the Python `RemoteConversation` event cache
    keys ACP tool calls by `(session, id)`; `render_resume_transcript` skips child tool calls; the default
    visualizer gets entries for the three kinds; `LocalConversation` gains `cancel_acp_session` (and, if S1 lands
    before S2, the shared emitter). Upstream's checklist ("trace cross-layer changes through every affected
    public entry point") asks for exactly these.
16. **Size:** about 1.8k lines with tests, not the spec's 1.5k: the third kind (+60), the fixture's sub-agent and
    transcript modes (+180), the extra consumers (+60), the TS hand-written types (+60). If S1 lands before S2,
    it also carries the shared emitter and the fixture's skeleton (about +120 more), which S2 then does not.

---

## 4 · Modules and seams

### 4.1 Files

| Path (SDK fork) | | ≈ lines | What |
|---|---|---|---|
| `openhands-sdk/openhands/sdk/agent/acp_unstable.py` | new | 150 | **The shim**: models for the three updates and the capability, `SubagentClientSideConnection`, `SUBAGENT_CLIENT_CAPABILITIES`. Deleted at the pin bump. |
| `openhands-sdk/openhands/sdk/agent/acp_subagents.py` | new | 280 | `ACPSubagentSessions` (routing, merge, segments, cost, cancel grants, seed); `ACPSessionNotFoundError`, `ACPSessionNotCancellableError`. Stays after the shim goes. |
| `openhands-sdk/openhands/sdk/agent/acp_agent.py` | changed | +100 | The bridge's routing and emission; the opt-in field; the connection swap; seed, replay flag and root id in `_init`; `cancel_acp_session`. §4.4 lists every hunk. |
| `openhands-sdk/openhands/sdk/event/acp_subagent.py` | new | 120 | `ACPSubagentEvent`, `ACPSessionMessageEvent`, `ACPSessionTextEvent`. |
| `openhands-sdk/openhands/sdk/event/acp_tool_call.py` | changed | +12 | `acp_session_id`, `meta`. |
| `openhands-sdk/openhands/sdk/event/__init__.py` | changed | +6 | Export (and so register) the three kinds. |
| `openhands-sdk/openhands/sdk/event/resume_transcript.py` | changed | +4 | Skip child tool calls. |
| `openhands-sdk/openhands/sdk/conversation/impl/remote_conversation.py` | changed | +10 | Cache key `(acp_session_id, tool_call_id)` for child calls. |
| `openhands-sdk/openhands/sdk/conversation/impl/local_conversation.py` | changed | +25 | `cancel_acp_session`; plus, if S1 lands first, S2's emitter (`_emit_event_from_any_thread`, its executor, its wiring in `_ensure_agent_ready`, its shutdown in `close()`; S2 §4.3, about +40). |
| `openhands-sdk/openhands/sdk/conversation/visualizer/default.py` | changed | +12 | Three `EventVisualizationConfig` entries. |
| `openhands-sdk/openhands/sdk/settings/model.py` | changed | +20 | `ACPAgentSettings.acp_subagents`, forwarded by `create_agent()`. |
| `tests/fixtures/acp/scripted_agent.py` | shared with S2 | +180 | S1's flags on S2's scripted test agent (§4.10); the whole script (about +300) if S1 lands first. |
| `openhands-agent-server/openhands/agent_server/acp_router.py` | shared with S2 | +55 | The cancel route on `conversation_acp_router` and `CancelACPSessionResponse`; the module, its router and its `include_router` line in `api.py` if S1 lands first. |
| `openhands-agent-server/openhands/agent_server/event_service.py` | changed | +15 | `cancel_acp_session`. |
| `.github/agent-server-openapi-weak-schema-allowlist.json` | changed | +24 | One entry per new `meta` location. |
| `clients/typescript/src/…` | changed | +130 | Types, `cancelAcpSession` ×2, `ACP_SETTINGS_KEYS` (§4.9). |
| `tests/…`, `clients/typescript/src/__tests__/…` | new/changed | 750 | §7. |
| `tests/sdk/persisted_settings_baselines/v7/agent_settings_acp_subagents.json` | new | 12 | The opt-in's fixture. |

### 4.2 The shim — `acp_unstable.py`

Everything that exists only because agent-client-protocol 0.12.1 does not know schema 1.24.1's sub-agent types.
Its module docstring names the tripwire test that tells you when to delete it.

**Models.** Transcribed from upstream's own generator output (python-sdk `9d07d78` regenerated from
`schema-v1.24.1` with `scripts/gen_all.py`, the run the spec cites), keeping its field names, aliases and
optionality, adapted in three ways: they subclass 0.12.1's generated `acp.schema.BaseModel` (so `populate_by_name`
and the `_meta` salvage validator are the library's own); content blocks use 0.12.1's five block classes as one
discriminated union; and the five-way state union collapses into one tolerant `SubagentState` (`state: str`,
`extra="allow"`), which keeps an agent-specific or future state whole, as the RFD requires of clients. Each update
model carries its `sessionUpdate` literal as the discriminator, and pydantic's `model_fields_set` tells an omitted
field from an explicit `null`, which the RFD's patch rules need (verified on 0.12.1 with pydantic 2).

| Model | Fields (wire names) |
|---|---|
| `SubagentCapabilities` | `_meta` |
| `SessionCancelCapabilities` | `_meta` |
| `SubagentSessionCapabilities` | `cancel`, `_meta` |
| `SubagentState` | `state`, `stopReason`, `_meta`, anything else kept |
| `SubagentUpdate` | `sessionUpdate = "subagent_update"`, `sessionId`, `title`, `description`, `capabilities`, `state`, `_meta` |
| `SessionMessage` | `sessionUpdate = "session_message"`, `messageId`, `senderSessionId`, `recipientSessionId`, `content` (list), `_meta` |
| `SessionMessageChunk` | `sessionUpdate = "session_message_chunk"`, `messageId`, `senderSessionId`, `recipientSessionId`, `content` (one block), `_meta` |
| `SubagentClientCapabilities(ClientCapabilities)` | the library's fields plus `subagents` |

`SUBAGENT_CLIENT_CAPABILITIES = SubagentClientCapabilities(subagents=SubagentCapabilities())` is what the bridge
advertises; serialized with the library's own `serialize_params` it is `{"auth": {}, "subagents": {}}` (verified).

**`SubagentClientSideConnection`**, used at `acp_agent.py:3070` when the opt-in is on:

- `__init__(to_client, input_stream, output_stream, *, on_unstable_update)` calls the library's constructor,
  then replaces `self._conn._handler` with `route_unstable_updates(self._conn._handler, on_unstable_update)`.
  This is the one place the shim touches a private attribute of the library; the shim's own tests exercise it
  through a real connection, so a rename in the library fails a test instead of silently dropping updates.
- `route_unstable_updates(inner, on_unstable_update)` returns a handler that, for a notification
  `session/update` whose `params.update.sessionUpdate` is one of the three, validates the update with one
  `TypeAdapter` and calls `on_unstable_update(params["sessionId"], update)` **synchronously** (the callback must
  not await, §6); an invalid one is logged at WARNING with its error count and dropped, as the library would have
  done. Every other message goes to `inner` unchanged.
- `initialize(protocol_version, client_capabilities=None, client_info=None, **kwargs)`: when
  `client_capabilities` is a `SubagentClientCapabilities`, sends `initialize` through `acp.utils.request_model`
  with the standalone `_SubagentInitializeRequest`, whose `clientCapabilities` is declared as the subclass, so
  serialization keeps `subagents`; otherwise it is `super().initialize(...)`, the library's call.

Probed for this design on 0.12.1 (2026-10-02, `scratchpad/s1probe/shim2.py`): the capability arrives at the
agent; nine interleaved stable and unstable updates arrive at the client in wire order; `fields_set` separates
`"title": null` from an omitted title; a `{"state": "_custom", "x": 1}` state is kept; the module passes pyright
`standard` with the single suppression.

### 4.3 The router — `acp_subagents.py`

`ACPSubagentSessions` is the client side of ACP's sub-agent RFD for one connection. It is bookkeeping only: it
returns the events to persist and never emits, locks, awaits or does I/O; the bridge calls it from the
connection's event loop (the one exception, `seed`, runs before the connection exists, §6). A class because it
holds state across calls.

**State.**

| Field | Meaning |
|---|---|
| `root_session_id` | the root's ACP id on this connection; set by `_init` before `session/load` (the prior id) and after the session is resolved |
| `replaying` | `True` from just before `session/load` until it returns |
| `_children: dict[str, _Association]` | every known child: seeded from history or announced on this connection |
| `_pending: dict[str, _Pending]` | per session (root included), at most one open segment: a text run or a chunked message |
| `_messages: dict[tuple[str, str], _Message]` | resolved directed messages, keyed `(transcript session, messageId)` |
| `_warned: set[str]` | unannounced session ids already warned about |

`_Association` holds `parent_session_id` (`None` = root), `parent_tool_call_id`, `title`, `description`,
`state`, `stop_reason`, `cancel_granted` (a grant received live on this connection), `cost`, `cost_currency`,
`meta`.

**Routing.**

- `is_child(session_id)`: `session_id in _children`.
- `key(session_id)`: `None` when `session_id == root_session_id`, else `session_id`. Used for every stored
  routing field.
- Children of children are children: a `subagent_update` on a child's session announces a grandchild whose
  `parent_session_id` is that child.

**Merge rules** for `on_subagent_update(session_id, update)`, the RFD's, applied field by field:

| Wire field | Omitted | `null` | A value |
|---|---|---|---|
| `title`, `description` | unchanged | cleared | replaced |
| `state` | unchanged | cleared (`state = stop_reason = None`: unconfirmed) | replaced whole (`state`, `stop_reason`) |
| `capabilities` | unchanged | grant withdrawn | replaced whole: granted iff `cancel` is an object |
| `_meta` | unchanged | cleared (but `parent_tool_call_id` kept) | replaced whole; `parent_tool_call_id` updated iff it carries `openhands.parentToolCallId` as a string |

Ownership is never changed: an update for a known child arriving on a different session keeps the original
parent (WARNING); an update whose child id is the root, or equals the session it arrives on, is ignored
(WARNING). The first update for an unknown id announces it. Masking (the bridge's `_mask_value`) is applied to
`title`, `description` and `meta` before they are stored. Each update returns, in order: the parent's open
segment flushed, the child's open segment flushed (its last words precede its state change), then one
`ACPSubagentEvent` snapshot.

**Segments.** A session's open segment is either a text run (`thought` true or false) or one chunked message
(`messageId`). `on_child_text` appends to a text run of the same kind, else flushes and opens one;
`on_session_message_chunk` appends to the same message, else flushes and opens one. `before_update(session_id)`
flushes, and the bridge calls it before every other update for a known session (tool calls, upserts, and anything
else). Usage updates never flush: D1 sends them every 0.5 s while a child is dirty, and they are not transcript
entries. `flush_all()` flushes every session. A flushed text run becomes one `ACPSessionTextEvent`; a flushed
chunked message becomes one `ACPSessionMessageEvent` with its accumulated text.

**Directed messages.** `on_session_message` flushes the session's segment, then resolves the upsert into
`_messages[(session, messageId)]`: content omitted keeps, `null` or `[]` clears, a list replaces; `_meta` the
same; `senderSessionId` and `recipientSessionId` omitted or `null` keep the known value (the RFD's identity rule,
different from the content rule). Returns one `ACPSessionMessageEvent` snapshot. Text is the concatenation of the
text blocks (masked); other blocks are counted in a DEBUG line.

**Cost.** `on_child_usage(session_id, update)` sets the child's `cost`/`cost_currency` from `update.cost`
(`None` when the update omits it: unknown, not zero, D1 §5.2) and returns a snapshot only when either changed.
`size` and `used` are not stored (context windows are per session and not summed).

**Replay.** While `replaying`, every entry point returns no events and changes nothing except one thing:
an unknown child announced in the replay is registered (parent only), so its replayed traffic is routed away from
the root accumulators. Grants and states in a replay are never merged.

**Cancel grants.** `check_cancel(session_id)` raises `ACPSessionNotCancellableError` for the root,
`ACPSessionNotFoundError` for an unknown id, `ACPSessionNotCancellableError` when the child holds no live grant,
and returns otherwise. A grant is live only if it arrived on this connection outside a replay.

**Seed.** `seed(events)` runs once per connection, over this conversation's stored events, before the connection
exists. For each `ACPSubagentEvent` it keeps the latest snapshot per child, registers the child with its stored
parent, title, description, meta, `parent_tool_call_id` and cost, and leaves `state`, `stop_reason` and the grant
empty. It returns, for each child whose latest stored snapshot had `cancellable` true or a `state` other than
`None` and `"idle"`, a copy of that snapshot with `source="environment"`, `state=None`, `stop_reason=None`,
`cancellable=False`. Partial patches after a reconnect therefore merge onto the stored association instead of
blanking its title.

### 4.4 The bridge — `acp_agent.py`, hunk by hunk

Line numbers are `53a4bc5`'s.

| Where | Change |
|---|---|
| imports `:42–74` | add `from openhands.sdk.agent.acp_unstable import (SUBAGENT_CLIENT_CAPABILITIES, SessionMessage, SessionMessageChunk, SubagentClientSideConnection, SubagentUpdate)`, `from openhands.sdk.agent.acp_subagents import ACPSubagentSessions`, `Event` in the event import. |
| `_OpenHandsACPBridge.__init__` `:1289` | keyword-only `subagents: bool = False`; creates `self.subagents = ACPSubagentSessions(mask=self._mask_value) if subagents else None` and `self.on_session_event: Callable[[Event], None] \| None = None` (the conversation's emitter, set by `_start_acp_server`). Existing callers (`_OpenHandsACPBridge()` in the tests) get today's bridge. |
| `reset()` `:1334` | `accumulated_tool_calls` keeps child entries that are not terminal (`[tc for tc in … if tc.get("acp_session_id") is not None and tc.get("status") not in _TERMINAL_TOOL_CALL_STATUSES]`), so a child's cell that outlives a turn can still complete. The router and `on_session_event` are not reset. |
| `_mask_tool_call_entry` `:1406` | also masks `meta`. |
| `session_update` `:1427`, after the fork branch `:1445–1451` (and after S2's one line, first after the idle-clock reset, which takes `AvailableCommandsUpdate` and `ConfigOptionUpdate` for every session and returns) | `child = self._child_session(session_id)`. When the opt-in is on: `self.emit_subagent_events(self.subagents.before_update(session_id))` for any update that is neither a child's text chunk nor a usage update, then, for a child: `AgentMessageChunk`/`AgentThoughtChunk` (text blocks) → `on_child_text`; `UsageUpdate` → `on_child_usage`; `ToolCallStart`/`ToolCallProgress` → fall through to the tool-call branches with `child`; anything else (plans, session info, mode) → DEBUG and return. `_child_session` returns the id for a known child, else `None`, and warns once for an id that is neither root, fork nor known. |
| `ToolCallStart` branch `:1479` | the entry gains `"acp_session_id": child` and `"meta": update.field_meta if self.subagents is not None else None`. |
| `ToolCallProgress` branch `:1504` | matches on `tc["tool_call_id"] == update.tool_call_id and tc.get("acp_session_id") == child`; when the opt-in is on, a non-`None` `update.field_meta` replaces `updated["meta"]`. |
| `_emit_tool_call_event` `:1550` | passes `acp_session_id` and `meta` to `ACPToolCallEvent`; a child entry (`acp_session_id` not `None`) goes through `emit_subagent_events`, a root entry through today's `on_event` path (dropped between turns, as today). |
| new methods on the bridge | `unstable_session_update` (the shim's callback: resets the idle clock, ignores the fork session, dispatches to the router, emits, signals activity); `emit_subagent_events` (submits each event to `on_session_event`; drops them while `replaying`, and with a DEBUG line when no emitter is wired, as for an `ACPAgent` driven without a `LocalConversation`); `flush_subagent_text`. Appendix A. |
| `ACPAgent` fields, after `acp_isolate_data_dir` `:1862` | `acp_subagents: bool = False` with its description. |
| `ACPAgent` private attrs, after `:1992` | none of S1's own. S1 uses S2's `_on_session_event: Callable[[Event], None] \| None` (S2 Appendix A.3), which `LocalConversation._ensure_agent_ready` sets before `init_state`; if S1 lands first, it adds that attribute and its wiring exactly as S2 specifies. |
| `_start_acp_server` `:2914–2915` | `client = _OpenHandsACPBridge(subagents=self.acp_subagents)`; `client.on_session_event = self._on_session_event`; then, before spawning, `if client.subagents is not None: client.emit_subagent_events(client.subagents.seed(state.events))` (the reset snapshots go to the emitter, whose worker stores them once the caller releases the state lock). The emitter is the conversation's function, not the agent's, so S2's agent swap (`_replace_acp_agent`) needs no rebinding for S1. |
| `_init`, connection `:3070` | `SubagentClientSideConnection(client, process.stdin, filtered_reader, on_unstable_update=client.unstable_session_update)` when `self.acp_subagents`, else today's `ClientSideConnection(client, process.stdin, filtered_reader)`, byte for byte. |
| `_init`, initialize `:3090` | `await conn.initialize(protocol_version=1, client_capabilities=SUBAGENT_CLIENT_CAPABILITIES)` when on, else today's call. |
| `_init`, load `:3204–3240` | when on: `subagents.root_session_id = prior_session_id; subagents.replaying = True` before `load_session`, `replaying = False` in a `finally`. |
| `_init`, after the session is resolved (`:3252`, `session_id` known) | `subagents.root_session_id = session_id`. |
| `_cancel_inflight_tool_calls` `:3402–3420` | the synthetic failures carry `acp_session_id` and `meta` from the entry; child entries are included (the RFD's optimistic close of a cancelled turn) and go through `emit_subagent_events`, not the captured `on_event`, so a child call's synthetic failure can never be stored before its own earlier `started` event. |
| `_flush_inflight_tool_calls_as_completed` `:3438–3444` | skips entries with an `acp_session_id`: a child's open cell is its agent's to close. |
| `_do_acp_prompt` `:3626–3654`, after the usage wait | `self._client.flush_subagent_text()`: every child's open segment is submitted, on the ACP loop (§6). |
| new `ACPAgent.cancel_acp_session` and `_acancel_acp_session` | Appendix A. |

Unchanged on purpose: `_reset_client_for_turn`, `_clear_turn_callbacks` and `init_state` (child events never
use the turn's callbacks); `_record_usage` (root only); `prepare_usage_sync`/`get_turn_usage_update` (the root's
turn sync never sees a child); `_finalize_successful_turn`'s text (root only, because child text never reaches
`accumulated_text`); the stdout filter; `ask_agent` (fork routing still runs first; unstable updates on the fork
session are ignored).

### 4.5 Persisted events — `event/acp_subagent.py`, `event/acp_tool_call.py`

All three are plain `Event` subclasses (frozen, `extra="forbid"`, `kind` = class name, registered by import in
`openhands/sdk/event/__init__.py`), not LLM-convertible, with a short `visualize` and `__str__` like
`ACPToolCallEvent`'s. Fields, in full in Appendix A:

| Kind | Written | Key for "latest wins" | Fields |
|---|---|---|---|
| `ACPSubagentEvent` | per `subagent_update`; per change of the child's cost; per reconnect (`source="environment"`) | `acp_session_id` | `acp_session_id`, `parent_session_id` (`None` = root), `parent_tool_call_id`, `title`, `description`, `state` (`None` = unconfirmed), `stop_reason`, `cancellable`, `cost`, `cost_currency`, `meta` |
| `ACPSessionMessageEvent` | per `session_message`; per flushed chunked message | `(acp_session_id, message_id)` | `acp_session_id` (the transcript; `None` = root), `message_id`, `sender_session_id`, `recipient_session_id` (verbatim ACP ids), `text`, `meta` |
| `ACPSessionTextEvent` | per flushed text run of a child | none (append-only, in order) | `acp_session_id` (always a child), `thought`, `text` |
| `ACPToolCallEvent` (changed) | as today | `(acp_session_id, tool_call_id)` | today's fields plus `acp_session_id` (`None` = root) and `meta` (the call's `_meta`, latest), both written only with the opt-in on |

Compatibility: old conversations load unchanged (every new field is optional, every new kind is new); events are
stored with `exclude_none=True` (`event_store.py:225`), so a root tool call is byte-identical to today's; new
kinds are written only for agents with the opt-in, so no existing deployment's clients see them. An older Python
`RemoteConversation` that meets a new kind raises on the unknown `kind` (`resolve_kind`), as with every kind
upstream adds.

### 4.6 The opt-in — `ACPAgent` and `ACPAgentSettings`

`acp_subagents: bool = False` on both, forwarded by `ACPAgentSettings.create_agent()` (`settings/model.py:1926`)
next to `acp_isolate_data_dir`. Like that knob it is programmatic and downstream-facing (no
`SETTINGS_METADATA_KEY`, so it is not in the settings form): the deploying application turns it on for an agent
it knows implements sub-agent sessions. **D5's seam:** the desktop app's setup writes the `dr-acp` agent settings
with `"acp_subagents": true` beside `"acp_server": "custom"` and its `acp_command`. Adding a defaulted field is
additive: `AGENT_SETTINGS_SCHEMA_VERSION` stays 7, and a new fixture,
`tests/sdk/persisted_settings_baselines/v7/agent_settings_acp_subagents.json`, pins that a stored `true` survives
`validate_agent_settings`:

```json
{
  "__expected__": {
    "agent_kind": "acp",
    "acp_server": "custom",
    "acp_subagents": true
  },
  "schema_version": 7,
  "agent_kind": "acp",
  "acp_server": "custom",
  "acp_command": ["my-acp-agent"],
  "acp_subagents": true
}
```

The field also rides on the serialized agent (`base_state.json`, `ConversationInfo.agent`), so a client can tell
whether a conversation's agent stores sub-agent sessions.

### 4.7 The agent-server

**Route**, on S2's `conversation_acp_router` in the new `openhands/agent_server/acp_router.py` (prefix
`/conversations/{conversation_id}/acp`, tag `ACP`, registered in `api.py` after `conversation_router`; S2 §4.7):
`POST /api/conversations/{conversation_id}/acp/sessions/{session_id}/cancel` → `CancelACPSessionResponse`. If S1
lands first, it creates the module with that router, prefix, tag and registration, and S2 adds its routes there.

| Outcome | Status | `detail` |
|---|---|---|
| sent | 200 | body `{"session_id": "<id>", "requested": true}`; confirmed later by an idle `ACPSubagentEvent` with `stop_reason: "cancelled"` |
| conversation unknown | 404 | — |
| `ACPSessionNotFoundError` | 404 | `ACP session {session_id} is not a sub-agent session of this conversation.` |
| `ValueError` (not an ACP agent, or the service is inactive) | 400 | the error's text, as `switch_acp_model` |
| `ACPSessionNotCancellableError` | 409 | `ACP session {session_id} does not accept cancel; cancel the conversation's turn instead.` (the spec's text, also for the root and for a conversation with no live ACP connection) |
| `TimeoutError` | 504 | `ACP server did not accept the cancel for {session_id} within 2s.` |

`session_id` is a path parameter taken verbatim (clients URL-encode it; D1's ids are path-safe already).
**`EventService.cancel_acp_session`** (`event_service.py`, after `switch_acp_model` `:2005`) runs the blocking SDK
call in the default executor, so the server's loop never waits on the ACP portal, and raises
`ValueError("inactive_service")` when the service has no conversation, as its neighbours do.
**`LocalConversation.cancel_acp_session`** (`local_conversation.py`, after `switch_acp_model` `:1721`) checks the
agent is an `ACPAgent` (else `ValueError`, the same sentence shape as `switch_acp_model`) and delegates, without
`with self._state:` (decision I). The Python `RemoteConversation` gets no method, matching `switch_acp_model`.
**`CancelACPSessionResponse`** lives in `acp_router.py` beside S2's `ACPConfigOptionSetResponse`.

**The OpenAPI ratchet.** `check_agent_server_openapi_quality.py` reports every unconstrained object; each `meta`
(`ACPToolCallEvent`, `ACPSubagentEvent`, `ACPSessionMessageEvent`, and any `-Input`/`-Output` twins the export
produces) gets an entry in `.github/agent-server-openapi-weak-schema-allowlist.json`, kind
`unrestricted-additional-properties`, reason `ACP _meta is opaque by protocol: implementations MUST NOT assume
values at these keys.`, owner `OpenHands OSS`. The Implementer runs the script and adds exactly what it reports.

### 4.8 Other SDK consumers

- **`RemoteConversation`'s event cache** (`remote_conversation.py:420–465`) merges an ACP tool call's `started`
  and terminal events by `tool_call_id`. ACP ids are unique only within a session, so the key becomes
  `event.tool_call_id` for a root call (unchanged: the existing tests read `["tc-1"]`) and
  `(event.acp_session_id, event.tool_call_id)` for a child's; the dict's type widens to
  `dict[str | tuple[str, str], str]`.
- **`render_resume_transcript`** (`resume_transcript.py:258`) renders a lost session's history into the next
  session's first prompt. Child tool calls are the children's work, already summarized by the root's own cells
  and answers; they are skipped (`event.acp_session_id is not None`), and the three new kinds are not rendered.
- **The default visualizer** (`visualizer/default.py:210`) gets `ACPSubagentEvent` ("ACP Sub-agent"),
  `ACPSessionMessageEvent` ("ACP Session Message") and `ACPSessionTextEvent` ("ACP Sub-agent Text") entries in
  the action and message colours already used for ACP tool calls.

### 4.9 The TypeScript client — `clients/typescript`

- `src/events/types.ts:33`: `ACPToolCallEvent` becomes the generated type intersected with
  `{ acp_session_id?: string | null; meta?: Record<string, unknown> | null }`; three hand-written interfaces,
  `ACPSubagentEvent`, `ACPSessionMessageEvent`, `ACPSessionTextEvent`, extend `BaseEvent` with their `kind`
  literal and §4.5's fields (Appendix A.6), join the `ConversationEvent` union (`:171`), and get type guards
  (`isACPSubagentEvent`, `isACPSessionMessageEvent`, `isACPSessionTextEvent`) beside `isMessageEvent`, as S2 does
  for its event. When upstream's pinned release artifact carries the kinds, they become aliases of the generated
  types, as `ACPToolCallEvent` is.
- `src/client/conversation-client.ts` (after `switchAcpModel` `:383`):
  `cancelAcpSession(conversationId, sessionId): Promise<CancelAcpSessionResponse>`, posting to
  `` `/api/conversations/${conversationId}/acp/sessions/${encodeURIComponent(sessionId)}/cancel` ``.
- `src/conversation/remote-conversation.ts` (after `switchAcpModel` `:332`): `cancelAcpSession(sessionId)`.
- `src/models/acp.ts:150`: `ACP_SETTINGS_KEYS` gains `'acp_subagents'`.
- `src/index.ts`: export the three types and `CancelAcpSessionResponse`.
- `endpoint-audit.config.json`: an `allowClientOnly` entry for `POST /api/conversations/{}/acp/sessions/{}/cancel`,
  reason "Client-ahead of the pinned Agent Server release, which does not yet carry ACP sub-agent sessions", owner
  "OpenHands TypeScript client maintainers" (the audit is report-only; this keeps it quiet).
- In our fork, the SDK fork's release step (spec Q2 (a)) regenerates `src/generated/agent-server-schema.ts` from
  our agent-server's OpenAPI with `AGENT_SERVER_OPENAPI_PATH`; the hand-written types compile against either
  schema. S1 does not commit a regenerated schema (upstream's `check:agent-server-api` would flag it as drift
  from the pinned release).

### 4.10 The generic fixture — S2's scripted test agent, with S1's flags

One scripted ACP agent serves both tasks' tests (decision K): `tests/fixtures/acp/scripted_agent.py`, run as
`[sys.executable, "<repo>/tests/fixtures/acp/scripted_agent.py", *flags]`. S2 specifies its default behaviour (a
`profile` option, commands per value, the first prompt clearing them, `session/load`, `session/close`, and the
request log named by `SCRIPTED_ACP_LOG`; S2 Appendix C). S1 adds two modes behind flags, and one requirement on
how the script serves its agent. Whichever task lands first creates the script; the other extends it. It
imports only `agent-client-protocol`, so the cross-repo jobs run it by path from a checkout of the SDK fork at the
pinned tag (D5, for the replay of D1's recordings; C1 and C2, for Canvas's mock-LLM end-to-end run).

**Serving.** The agent is served through `acp.connection.Connection(handler, writer, reader)` over
`acp.stdio.stdio_streams()`, where `handler` is `acp.agent.router.build_agent_router(agent)` wrapped by a small
tap. The tap keeps `initialize`'s raw `clientCapabilities` (0.12.1's model drops `subagents`, D1 §5.1 reads it
the same way) and writes S2's request log; the agent sends its unstable updates as raw JSON with
`Connection.send_notification`. All public pieces of 0.12.1. S2's behaviours are unchanged by this: they are the
same agent methods behind the same router. (S2's Appendix C names `acp.run_agent`, which builds an
`AgentSideConnection`; that class can neither send the unstable types nor show the raw capability, so if S2 lands
first, S1 replaces that one serving call.)

**`--subagents`** plays one generic sub-agent run on each `session/prompt`, before S2's reply text, with plain
ids and no agent-specific `_meta`:

1. `root` → `tool_call cell-1` (execute, "Run spawn", in progress).
2. `child-a`: announced on `root` (title "Summarize part A", `capabilities.cancel`, running,
   `_meta.openhands.parentToolCallId = cell-1`); the task as a `session_message` root → child-a; a thought on
   `child-a`; `tool_call cell-a1` and its completion; a grandchild `child-a-1` announced on `child-a`
   (`parentToolCallId = cell-a1`), whose answer arrives as two `session_message_chunk`s and which turns idle
   `end_turn`; a `usage_update` on `child-a` (0.0004 USD); its answer as a `session_message` child-a → root;
   idle `end_turn`.
3. `child-c`: announced without capabilities (the spec's "generic fixture has one" child that cannot be
   cancelled); one cell; idle `end_turn`.
4. `child-b`: announced with `capabilities.cancel`; `tool_call cell-b1` in progress; then it waits up to
   `--cancel-wait` seconds (default 0: no wait) for `session/cancel` naming `child-b`. Cancelled: `cell-b1`
   failed, then idle `cancelled`. Not cancelled in time: `cell-b1` completed, then idle `end_turn`. Either way the
   run continues, so tests without a cancel still finish.
5. `root` → `tool_call_update cell-1` completed, a `usage_update` covering the run (0.0011 USD), then S2's reply
   and `end_turn`.

If the client's `initialize` did not advertise `subagents`, steps 2–4 are skipped (an agent MUST NOT send them,
the RFD) and only the root's lines are played.

**`--transcript PATH`** replaces every built-in behaviour with a JSONL transcript, one JSON-RPC message per line
as it appeared on the wire, played once:

| Line | Who sent it on the recorded wire | The player |
|---|---|---|
| a request or notification whose `method` is one of `acp.meta.AGENT_METHODS`' values (`initialize`, `session/new`, `session/prompt`, `session/cancel`, …) | the client | **waits** for the client's next message with that method (and, for `session/cancel`, the same `sessionId`); remembers a request's live `id` |
| a response (`id` with `result` or `error`) | the agent | sends it with the live `id` of the request it answers (matched by the recorded `id`) |
| a `session/update` notification | the agent | sends it |

An **outgoing-only transcript** (D1's golden recordings, §8.3 of its design, hold only what `dr-acp` sent) has no
client lines. The player then infers one wait point before each response, by the response's shape: a result with
`protocolVersion` waits for `initialize`; one with `sessionId` and no `stopReason` waits for `session/new`; one
with `stopReason` waits for `session/prompt`, and so do the notifications before it that follow the previous
response. (D1's post-`session/new` commands therefore replay when the first prompt arrives; harmless for E5, which
compares trees.) The same conformance rule applies: without `subagents`, the three unstable updates and every
`session/update` whose `sessionId` is not the root's (that of the `session/new` result) are skipped. A client
message the transcript is not waiting for is logged; a request gets `-32601`. A wait point times out after
`--wait-timeout` seconds (default 30) and the script exits non-zero, so a test fails loudly. After the last line
the script stays connected, answering nothing more, and exits when the client closes its stdin.

---

## 5 · The persisted contract (what C1 reads)

This is C1's contract with S1, the spec's "S1's event shapes fixed". C1 reads stored events (REST page or the
WebSocket stream; the same events in the same order) and keeps no other channel.

1. **The tree.** The children of a session `P` are the sessions whose latest `ACPSubagentEvent` has
   `parent_session_id == P` (`None` is the conversation's root). "Latest" is log order; the WebSocket delivers in
   the same order.
2. **Placement in the parent.** `parent_tool_call_id`, when set, names a tool call in the parent's own session:
   the `ACPToolCallEvent` with `acp_session_id == parent_session_id` and that `tool_call_id`. When it is not set,
   or names no stored call, the first `ACPSessionMessageEvent` in the parent's transcript whose
   `recipient_session_id` is the child; else where the child's first `ACPSubagentEvent` sits. A child whose
   `parent_session_id` is neither `None` nor a known child is "could not be placed" (C1's failure cell).
3. **A child's own transcript**, in log order: its `ACPToolCallEvent`s (merge `started` and terminal by
   `(acp_session_id, tool_call_id)`, last wins, exactly as for the root today), its `ACPSessionTextEvent`s
   (`thought` true: render like the root's reasoning), and its `ACPSessionMessageEvent`s (last wins per
   `(acp_session_id, message_id)`; "To …" when `sender_session_id` is the child, "From …" otherwise).
4. **State.** The latest snapshot's `state`: `running`, `idle` (with `stop_reason`), `requires_action`,
   `unknown`, any other string (agent-specific, show as is), or `null` (no confirmed current activity: never a
   spinner).
5. **Cost.** The latest snapshot's `cost` with `cost_currency`; `null` is unknown, not zero. Never add a child's
   cost to its parent's, its siblings' or the conversation's (ACP's rule).
6. **Stop.** Show Stop only when the latest snapshot has `cancellable` true and `state` is `running` or
   `requires_action`; click → `cancelAcpSession(conversationId, sessionId)`. A 409 means "not now" (show its
   `detail`); success is shown only when the child's next snapshot arrives (`idle`, `stop_reason: "cancelled"`).
   For deep_reasoner, every agent of the stopped branch turns idle/cancelled the same way.
7. **Freshness.** A snapshot with `source == "environment"` is the bridge's record that the connection its last
   state came from ended: show the child's last known state as history, unconfirmed, without Stop.
8. **The root.** Unchanged: user `MessageEvent`s, root `ACPToolCallEvent`s (no `acp_session_id`), the turn's
   `FinishAction`, which never contains child text.
9. **Stock Canvas with S1** renders the new kinds as nothing (`should-render-event.ts` drops unknown kinds) and
   child tool calls in the flat main flow (it ignores `acp_session_id`); it may merge a child call into a root
   call only if both share a `tool_call_id`, which D1's ids never do.

---

## 6 · Threads, ordering and locks

**Who runs where.** The ACP connection lives on the `AsyncExecutor`'s portal loop (one thread). Every
notification is handled in its own task, created in arrival order by the library's receive loop; tasks start in
FIFO order. The bridge's `session_update` and the shim's callback never await, so each update is fully handled in
its task's first step, in arrival order, unstable and stable alike (verified with nine interleaved updates). A
prompt's response wakes `conn.prompt` only after the tasks of every notification received before it have run.

**The router is touched only on the portal thread**, with one exception made safe by timing: `seed` runs in
`_start_acp_server` before the connection exists, when no other thread can reach this bridge. Turn-end flushing
therefore happens at the end of `_do_acp_prompt`, which runs on the portal, not in `_finalize_successful_turn`.
Segments left open by an aborted turn are submitted by the session's next update, or at the end of the next turn.

**Two streams, two paths, each in order.** The root's events keep today's path: the turn's `on_event`, called
on the portal thread while a prompt is in flight (unchanged, so today's ordering guarantees for the root stand).
Every child event (associations, directed messages, text runs, child tool calls and their synthetic failures, the
reconnect snapshots) is submitted to the conversation's emitter, S2's `_emit_event_from_any_thread`: one worker,
first in first out, which takes the state lock and calls `_on_event`, so the event is persisted and reaches every
subscriber exactly like any other. The portal thread only submits; it never waits for the lock.

- *Within a child*, order is exact: every one of its events takes the one FIFO path, in the order the portal
  produced them, which is wire order. So "latest wins" per key (§5) always sees the newest last.
- *Between a parent's cell and the children it spawns*, references always point back: the cell's `tool_call` is
  stored synchronously on the turn's path before the announcement that names it is even received.
- *Between the root's and the children's events*, positions in the log may interleave differently from the
  wire: in the agent-server (`arun()`), the worker stores each child event as it comes, because the state lock is
  free while a prompt is awaited; under a synchronous `run()`, which holds the lock for the whole step, a turn's
  child events are stored right after the step. Nothing in §5 reads that relative position (placement is by id),
  except the last-resort placement "where the child's first `ACPSubagentEvent` sits".

**No deadlock.** The ACP thread never takes the state lock. The worker waits for it, and every holder releases it
without waiting on the worker: the synchronous `run()` releases it between steps, `arun()` while it awaits a
prompt (S2 §4.3), `init_state` when it returns. `close()` shuts the worker down with `cancel_futures=True`, so a
child event still queued at that moment, or submitted after it, is dropped with a DEBUG line (S2's semantics).

**Cancel** runs `_acancel_acp_session` on the portal through `run_async(..., timeout=2.0)` from an executor
thread: the grant check and the send happen on the thread that owns the router and the connection; no state lock
is taken.

**Replay boundary.** `replaying` is set and cleared on the portal around `await conn.load_session(...)`; by the
FIFO argument, every replayed notification has been handled before `load_session` returns, so nothing replayed
leaks out of the flag, and every notification after the response is live.

---

## 7 · Testing

In upstream's layout and style (pytest beside `tests/sdk/agent/test_acp_agent.py`, classes where the
neighbouring file uses them, the default run touching no network); each test named for the property it pins. The
boundary that is faked is the ACP agent process: the shared scripted agent of §4.10, launched as a real
subprocess, or, for the shim, a real 0.12.1 agent connection over the library's in-memory transport. Upstream's
full suite (615 files) must stay green; decision A is what keeps it green without edits. Like S2 (its §4.10), S1
puts its tests in new files and leaves the 10,258-line `test_acp_agent.py` alone. Child events reach the store
through the emitter's worker, so a test that reads `state.events` after `run()` waits until the expected events
are there (a polling helper with a 5 s limit), never on a sleep.

### 7.1 The shim and its tripwire — `tests/sdk/agent/test_acp_unstable.py`

| Test | Pins |
|---|---|
| `test_acp_library_rejects_subagent_update` | **The tripwire.** `acp.schema.SessionNotification.model_validate` of a minimal `subagent_update` raises `ValidationError`. Its failure message: "agent-client-protocol now parses ACP's sub-agent updates: delete openhands/sdk/agent/acp_unstable.py, use the library's types and capability, re-run the ACP conformance probes against Claude Code, Codex and Gemini, and bump agent-client-protocol in openhands-sdk/pyproject.toml." |
| `test_acp_library_has_no_subagents_capability` | The second tripwire: `"subagents" not in ClientCapabilities.model_fields`. |
| `test_initialize_puts_subagents_capability_on_the_wire` | An agent-side tap sees `{"auth": {}, "subagents": {}}`. |
| `test_initialize_without_subagent_capabilities_is_the_library_call` | `super().initialize` path: no `subagents` on the wire. |
| `test_unstable_updates_reach_the_callback_in_wire_order` | Nine interleaved stable/unstable updates arrive in order. |
| `test_stable_updates_still_reach_the_library_router` | `agent_message_chunk` on a child id arrives as `AgentMessageChunk`. |
| `test_malformed_unstable_update_is_dropped_with_a_warning` | A `subagent_update` without `sessionId`: no callback, one WARNING. |
| `test_patch_fields_tell_omitted_from_null` | `fields_set` contains `title` for `"title": null`, not for an omitted title. |

### 7.2 The router and the bridge — `tests/sdk/agent/test_acp_subagents.py`

Units feed `ACPSubagentSessions` and `_OpenHandsACPBridge(subagents=True)` directly (as `TestClientForkTextRouting`
feeds the bridge today), with the shim's models and the library's update models, and with `on_session_event` set
to a list's `append`:

`test_announcement_stores_parent_cell_and_cancel_grant` ·
`test_omitted_field_keeps_value_and_null_clears_it` ·
`test_parent_tool_call_id_survives_meta_without_it` ·
`test_child_is_never_reparented_nor_its_own_parent` ·
`test_child_text_never_reaches_the_root_answer` ·
`test_child_text_is_stored_per_segment_in_transcript_order` ·
`test_usage_never_splits_a_text_segment` ·
`test_chunked_message_is_stored_whole_at_the_next_boundary` ·
`test_message_upsert_replaces_content_and_keeps_participants` ·
`test_child_cost_is_on_its_association_and_never_booked_to_the_conversation` ·
`test_child_usage_leaves_root_usage_sync_and_context_window_alone` ·
`test_child_tool_calls_are_keyed_by_session_and_tool_call_id` ·
`test_turn_end_force_completes_only_root_tool_calls` ·
`test_aborted_turn_fails_child_tool_calls_with_their_session` ·
`test_child_events_go_to_the_session_emitter_and_root_events_to_the_turn` ·
`test_child_traffic_between_turns_reaches_the_emitter_in_order` ·
`test_child_events_without_an_emitter_are_dropped_with_a_debug_line` ·
`test_replay_is_neither_stored_nor_grants_cancel` ·
`test_new_connection_withdraws_cancel_and_unconfirms_state` ·
`test_partial_patch_after_reconnect_keeps_the_stored_title` ·
`test_unannounced_session_follows_the_root_path_with_one_warning` ·
`test_subagents_off_uses_the_stock_connection_and_initialize` (patches `acp_agent.ClientSideConnection` as the
existing tests do and asserts `initialize(protocol_version=1)` exactly).

**E5 in the fork**, through a real `LocalConversation` and an `ACPAgent(acp_command=[sys.executable,
<repo>/tests/fixtures/acp/scripted_agent.py, "--subagents", …], acp_subagents=True)`, or `--transcript` with a
hand-written transcript, no network:

| Test | Pins (E5's nulls) |
|---|---|
| `test_scripted_run_stores_the_scripted_tree` | Rebuilding the tree from stored events with §5's rules gives exactly the transcript's parent links, placements, per-session tool calls, messages and costs. |
| `test_scripted_run_keeps_child_text_out_of_the_answer` | The `FinishAction` text is the root's alone. |
| `test_stored_events_validate_against_the_agent_server_event_schema` | Every stored event validates against the `Event` schema in `build_public_openapi()`, so any OpenAPI-typed client parses them. |
| `test_scripted_run_with_subagents_off_stores_only_root_work` | Off: no new kinds, no `acp_session_id`; the conforming agent sent no child traffic. |
| `test_cancel_acp_session_reaches_the_child_and_its_cancelled_state_is_stored` | With `--cancel-wait 30` and `run()` in a thread, the test thread retries `cancel_acp_session("child-b")` until it stops raising `ACPSessionNotFoundError` (the announcement has been handled; under a synchronous `run()` the events themselves are stored only after the step, §6); S2's request log shows `session/cancel` for `child-b`; afterwards `child-b`'s cell is stored failed and its idle/cancelled snapshot follows. |
| `test_scripted_transcript_replays_an_outgoing_only_recording` | A transcript of agent lines only (the shape of D1's golden files) replays into the same stored tree as its hand-written source. |
| `test_cancel_acp_session_refuses_a_child_without_a_grant` | `child-c`: `ACPSessionNotCancellableError`; the request log shows no `session/cancel`. |
| `test_cancel_acp_session_refuses_unknown_and_root_sessions` | 404- and 409-class errors respectively. |
| `test_cancel_acp_session_without_a_live_connection_is_refused` | Before `init_state`: `ACPSessionNotCancellableError`. |
| `test_cancel_acp_session_does_not_wait_for_the_state_lock` | During a sync `run()` (state lock held for the turn) the cancel returns within 2 s. |

### 7.3 Everything else

| File | Tests |
|---|---|
| `tests/sdk/event/test_acp_subagent_events.py` | `test_subagent_events_round_trip_through_json` · `test_legacy_acp_tool_call_event_loads_without_session_fields` · `test_root_tool_call_event_is_stored_as_before` (`exclude_none` dump has no new keys) |
| `tests/sdk/event/test_resume_transcript.py` | `test_resume_transcript_skips_child_tool_calls` |
| `tests/sdk/agent/test_acp_dedup_and_truncation.py` | `test_remote_events_merge_child_and_root_calls_separately` |
| `tests/sdk/test_settings.py` | `test_acp_create_agent_forwards_subagents` |
| `tests/sdk/persisted_settings_baselines/v7/agent_settings_acp_subagents.json` | picked up by the existing compat check |
| `tests/sdk/conversation/local/test_local_conversation_event_emitter.py` (only if S1 lands before S2, which then owns these tests) | S2's emitter tests (S2 §4.10): an event emitted from the ACP thread during a synchronous `run()` does not deadlock and lands after the step; events keep submission order; events emitted after `close()` are dropped |
| `tests/agent_server/test_acp_router.py` (S2's file) | `test_cancel_acp_session_success` · `…_conversation_not_found` · `…_unknown_session_returns_404` · `…_not_cancellable_returns_409` · `…_non_acp_returns_400` · `…_timeout_returns_504` (upstream's style: a mocked event service) |
| `tests/agent_server/test_event_service.py` | `test_cancel_acp_session_runs_off_the_event_loop` |
| `tests/cross/test_remote_conversation_live_server.py` | `test_acp_subagent_sessions_over_live_server`: a real server, the scripted agent with `--subagents --cancel-wait 30`, events read over REST and WebSocket, the cancel route end to end (the agent-server AGENTS.md asks for one such test per endpoint addition) |
| `clients/typescript/src/__tests__/api-clients.test.ts` | `ConversationClient.cancelAcpSession posts to the session cancel endpoint` · `… encodes the session id` · `RemoteConversation.cancelAcpSession posts for its conversation` |
| `clients/typescript/src/__tests__/acp-providers.test.ts` | `forwards the sub-agent opt-in` |
| `clients/typescript/src/__tests__/event-types.test.ts` | `sub-agent event shapes accept stored events` |

### 7.4 The live tier (Gate B)

Spec §4 layer 5: "S1, S2: through the SDK's own tests, with `dr-acp` behind the bridge". The fork cannot name
`dr-acp`, so the test is generic and the agent is configured from outside:

- **In the fork:** `tests/sdk/agent/test_acp_subagents_live.py`, `pytestmark = pytest.mark.acp_live` (upstream's
  marker for live ACP probes, deselected by default), skipped unless `OPENHANDS_ACP_LIVE_AGENT_COMMAND` is set
  (a shell-split command line; the same variable S2's live tier reads, S2 §9) together with
  `OPENHANDS_ACP_LIVE_SUBAGENTS_PROMPT` (a prompt that makes that agent spawn sub-agents, at least one with a
  child of its own). The agent runs with `acp_subagents=True`.
  - `test_live_agent_tree_is_well_formed`: one prompt; every stored child has a known parent; every
    `parent_tool_call_id` names a stored tool call of its parent; no child text in the answer; every child that
    reported a cost has it on its association; the conversation's cost equals the root's last reported cost.
  - `test_live_agent_stops_one_subagent_and_its_branch`: the run through `arun()` (so child events are stored as
    they come, §6), watched through a conversation callback; on the first `running`, cancellable child that has a
    child of its own, `LocalConversation.cancel_acp_session` from a worker thread; within 120 s
    that child and every session announced under it are stored `idle`/`cancelled`, no tool call starts in the
    branch after its root's idle snapshot, and the turn ends.
- **In deep-reasoning:** the same on-demand workflow S2's live tier needs (`workflow_dispatch`, input: the SDK
  fork's ref; not in the public fork, because installing `dr-acp` installs deep_reasoner_beta, which needs a read
  token): it checks out both, installs the fork's packages and `dr-acp`, and runs S1's file with
  `OPENHANDS_ACP_LIVE_AGENT_COMMAND="dr-acp --config <D1's live config>"`, the CS vs STAT prompt and
  `OPENAI_API_KEY` from the repository's secrets (gpt-6-luna, cents per run), and S2's file with S2's variables. Comparing the stored tree with deep_reasoner's own node tree needs deep_reasoner's run
  directory, so that stronger check is D5's cross-repo replay (E5's second half), not this tier. See §11 item 2
  for who writes the workflow.

---

## 8 · Upstream guards and the pull request

**The branch** `feat/acp-subagent-sessions`, cut from the fork's `deep-reasoning` at `91430aa`, in five commits,
each green on its own, each cherry-pickable onto `main`:

1. `feat(acp): carry ACP's unstable sub-agent types past agent-client-protocol 0.12.1` — `acp_unstable.py`,
   `test_acp_unstable.py` (with the tripwire).
2. `feat(events): ACP sub-agent session events` — `event/acp_subagent.py`, `ACPToolCallEvent` fields, exports,
   visualizer, resume transcript, `RemoteConversation` cache key, the OpenAPI allowlist, event tests.
3. `feat(acp): route and persist sub-agent sessions in the ACP bridge (opt-in acp_subagents)` —
   `acp_subagents.py`, `acp_agent.py`, the settings field and fixture, S1's modes of the scripted agent,
   router/bridge/E5 tests, the live tests. If S1 lands before S2, this commit is preceded by one that adds the
   shared pieces exactly as S2 specifies them (`_emit_event_from_any_thread` with its wiring and tests, the
   scripted agent's skeleton), so S2's PR finds them in place.
4. `feat(agent-server): cancel one ACP sub-agent session` — `LocalConversation`, `EventService`, the route on
   `conversation_acp_router` (and `acp_router.py` with its registration, if S1 lands first), the response model,
   router/service/live-server tests.
5. `feat(ts-client): sub-agent event types and cancelAcpSession` — §4.9.

**Upstream's guards** run only on pull requests to `main`, so the branch, cherry-picked onto the fork's `main`,
gets a draft PR there that is never merged (spec §4 layer 3). Expected results, each checked against the script:
REST breakage (oasdiff) passes (additive route, additive `oneOf`, optional properties); persisted settings pass
with the new fixture; OpenAPI quality passes with the allowlist entries; SDK API breakage passes (additions
only); the TypeScript client CI passes against the pinned release (hand-written types); the endpoint audit
reports one client-ahead route, allowlisted; pre-commit (ruff, pycodestyle, pyright, the dynamic-attribute
ratchet, import rules) passes. The PR description uses upstream's template and leaves its `HUMAN:` field as the
placeholder for Michael. No issue or pull request is opened on any upstream repository.

**Upstream merges** (spec Q1 (a)): our conflicts sit in `acp_agent.py`'s `session_update`, `_start_acp_server`
and tool-call close-out hunks of §4.4 (≈100 lines in upstream's busiest file); everything else is new files or
appended lines.

**When the library catches up** (the tripwire fails): delete `acp_unstable.py`; import `SubagentUpdate`,
`SessionMessage`, `SessionMessageChunk` and the capability from `acp.schema`; replace the connection subclass
with the library's own routing (the bridge's `unstable_session_update` becomes three `isinstance` branches in
`session_update`); bump the pin; re-run `pytest -m acp_live tests/sdk/agent/test_acp_conformance.py` for Claude
Code, Codex and Gemini, because the bump changes the library they all go through. `acp_subagents.py`, the events,
the route and the client stay.

---

## 9 · Where S1 and S2 touch the same code

Checked against S2's design (`design/s2` `9e32261`, its §8). Three pieces are shared by design, one owner per
landing order: the out-of-turn emitter (rows 6–7), the scripted test agent (row 13) and `acp_router.py`
(row 9). Everything else is textual neighbourhood, with the rule that lets either PR land first.

| # | Place (`53a4bc5`) | S1 | S2 | Rule |
|---|---|---|---|---|
| 1 | `acp_agent.py` imports `:42–74` | the shim's names, `ACPSubagentSessions` | `AvailableCommandsUpdate`, `ConfigOptionUpdate`, its models | One import list; the second to land merges by hand, keeping it sorted. |
| 2 | `_OpenHandsACPBridge.__init__` / `reset()` `:1289–1345` | `subagents`, `on_session_event`; `reset()` keeps open child tool calls | `_session_controls`, `_commands_reported`, `on_session_controls_changed` | Appended attributes, no shared name; neither is cleared by `reset()`. |
| 3 | `_OpenHandsACPBridge.session_update` `:1427–1548` | the child diversion after the fork branch (`:1451`); the `ToolCallStart`/`ToolCallProgress` branches gain the session key | one line, first after the idle-clock reset: `if self._record_session_controls(session_id, update): return` | S2's line stays first: commands and options of any session go to S2's per-session recorder (only the root's are published) and never reach S1's diversion. S1's diversion therefore never sees those two types. |
| 4 | `_start_acp_server` and `_init` `:2912–3330` | the bridge's `subagents` flag and emitter, the seed, the connection class (`:3070`), the `initialize` call (`:3090`), root id and `replaying` around `load_session` (`:3204–3240`) and after `:3252` | `_starting_session` set at the top and cleared in a `finally`; reads `init_response.agent_capabilities.session_capabilities.close`; records the `session/new`/`session/load` responses' options; applies start-time option values after the model call; one post-start publish | S2 reads the `initialize` *response*, so S1 changes the call freely; S2's blocks sit after the model call, away from S1's lines. S1's seed runs before the subprocess starts, independent of `_starting_session`. |
| 5 | `ACPAgent` fields and private attributes `:1714–1992` | `acp_subagents` | `acp_config_options`, `_on_session_event`, `_session_controls_lock`, `_published_session_controls`, `_supports_session_close`, `_starting_session` | Appended. `_on_session_event` is S2's name, used by S1 (row 6). |
| 6 | **Events outside a turn** | every child event, during turns and between them (decision G) | every controls event (S2 decision B) | **One primitive:** `ACPAgent._on_session_event`, set by `LocalConversation._ensure_agent_ready` to `_emit_event_from_any_thread` before `init_state` (S2 §4.3, Appendix A.3–A.4). Whoever lands first builds it with those names and semantics; the other uses it. Both streams share one FIFO worker. S1 passes the emitter to the bridge as `on_session_event` at each `_start_acp_server`; S2 publishes through the agent. |
| 7 | `LocalConversation` `:1533–1600`, `:1721–1803` | `cancel_acp_session` (no state lock) | the emitter and its wiring, `set_acp_config_option`, `_replace_acp_agent` extracted from `switch_acp_model` | Adjacent methods. S1 needs nothing rebound on S2's agent swap (its emitter belongs to the conversation, not the agent). |
| 8 | `openhands/sdk/event/__init__.py` | three kinds | `ACPSessionControlsEvent` | Adjacent import and `__all__` lines. |
| 9 | **Routes** | `POST …/acp/sessions/{session_id}/cancel` | `acp_router.py`: `acp_router` (`/acp`, the preview) and `conversation_acp_router` (`/conversations/{conversation_id}/acp`, the set route), registered in `api.py` after `conversation_router` | **One module:** S1's route goes on `conversation_acp_router`; whoever lands first creates the module, the router and the `include_router` line. Path segments do not overlap (`/sessions/…` vs `/config-options`). |
| 10 | `EventService` after `switch_acp_model` `:2005–2025` | `cancel_acp_session` | `set_acp_config_option` | Adjacent methods. |
| 11 | `ServerInfo.capabilities` (`server_details_router.py:63–70`) | none: its events exist only on a server that has S1, and the cancel route answers 404 where it does not | `acp_session_controls_v1` | No overlap. |
| 12 | TypeScript client | `cancelAcpSession` ×2, three hand-written event interfaces in `src/events/types.ts`, the `ACPToolCallEvent` intersection, `ACP_SETTINGS_KEYS` | its client methods, `src/models/acp-session-controls.ts`, `ACPSessionControlsEvent` and its guard in `src/events/types.ts` | Same files (`conversation-client.ts`, `remote-conversation.ts`, `events/types.ts`, `index.ts`, `endpoint-audit.config.json`, `api-clients.test.ts`); union of both, one `allowClientOnly` entry each. |
| 13 | **The scripted test agent** `tests/fixtures/acp/scripted_agent.py` | `--subagents`, `--cancel-wait`, `--transcript`, `--wait-timeout`; serving through `Connection` and `build_agent_router` with a raw tap (§4.10) | its default behaviours, `--no-close`, `--no-commands`, `--slow-set`, `SCRIPTED_ACP_LOG` (S2 Appendix C) | **One script:** whoever lands first creates it; the other adds its flags. If S2's `acp.run_agent` serving is in place, S1 swaps that one call (§4.10). |
| 14 | Upstream guards | `meta` fields (ACP `_meta`, opaque by protocol) need weak-schema allowlist entries; a v7 persisted-settings fixture | fully typed; no settings field | Independent: only S1 edits the allowlist and the settings baselines. |
| 15 | Tests | new files; does not edit `test_acp_agent.py` | new files; does not edit it | No overlap; `tests/agent_server/test_acp_router.py` is S2's file, to which S1 adds its route tests. |
| 16 | The generated TS schema in the fork's release step | regenerated | regenerated | Never merged by hand; regenerate after both. |

---

## 10 · What S1 relies on from its neighbours

**D1's contract (`f281109` §5): nothing must change.** S1 relies on these, all already in D1's design:

1. Every child is announced on its parent's session before any traffic bearing its id (§5.4 rule 1).
2. Announcements carry `_meta.openhands.parentToolCallId` naming a tool call already sent on the parent's session
   (§5.4 rule 2); later updates that carry `_meta` repeat it (§5.2's idle row does). S1 tolerates its absence
   (sticky field).
3. Every child is announced with `capabilities.cancel` (§5.2) and a `session/cancel` with the full child id stops
   its branch (§3 item 13); replayed announcements carry no capabilities (§5.7), which S1 would ignore anyway.
4. Ids are path-safe (`<run>-n<node>`, decision F of D1).
5. The Stop acknowledgement and each child's reasoning are `agent_thought_chunk`s on the child's session (§3 item
   9, §5.2): S1 stores them as `ACPSessionTextEvent` **only if §3 item 1 here is approved**; if it is not, D1's
   acknowledgement needs another carrier and that is D1's change to make.
6. The golden recordings (§8.3) are agent-outgoing JSON-RPC messages, one per line, with prompt responses
   carrying `stopReason` and the root id normalized consistently: the scripted agent's `--transcript` mode
   (§4.10) replays them as they are.
7. No child traffic follows the root's prompt response (§5.4 rule 7); S1 stores late traffic anyway.

One observation for D1, not a change: D1 keeps `capabilities.cancel` on a child after it turns idle; C1 hides
Stop on idle children by §5 rule 6, so nothing breaks, but a Stop sent to an idle node by another client reaches
`dr-acp`, which D1 already treats as a no-op for a re-driven child.

**C1** reads only §5, and runs the scripted agent (`--subagents --cancel-wait N`) by path from a checkout of the
SDK fork for its Canvas end-to-end run. **D5** sets `acp_subagents: true` for `dr-acp` (§4.6), replays D1's
recordings through the scripted agent's `--transcript` mode into the pinned agent-server and compares the stored
tree with `testing.tree` (E5's second half), and hosts or absorbs §7.4's live workflow, shared with S2's.
**S2** shares three pieces (§9). **C3, D2** do not touch S1.

---

## 11 · Open items

1. **The third event kind** (§3 item 1) needs the Conductor's yes, or Michael's if it reads as a change of the
   approved event model.
2. **Who writes the live workflow in deep-reasoning** (§7.4), which S2 needs too (S2 §10 item 3). S1's and S2's
   Gate B need it before D5 exists; the recommendation is one small `workflow_dispatch` workflow on a
   deep-reasoning branch from `self-hosted-v1`, written by whichever Implementer reaches its live tier first and
   absorbed by D5's cross-repo CI. It also needs `dr-acp` runnable (D1's Implementer) and D1's live config path.
3. **The `@final` suppression** (§3 item 3) is the one line upstream may push back on; the fallback is decision B's
   alternative (1), observers, at the cost of a logged exception per sub-agent update.
4. **Whether the TypeScript commit rides the same upstream PR** (client-ahead, allowlisted) or follows the server's
   release as its own PR. The spec says one PR; upstream's own flow would split it.
5. **The shared pieces' landing order** (§9 rows 6, 9, 13): whichever of S1 and S2 is built first creates the
   emitter, `acp_router.py` and the scripted agent to the other's specification. The Conductor sequences the two
   Implementers so they do not both create them on parallel branches; if they do, the second rebases onto the
   first's commit and drops its own copy.
6. **Child events still queued at `close()` are dropped** (S2's emitter cancels pending jobs, §6). Draining instead
   would need `close()` never to be called while the state lock is held; not needed by any v1 agent, since
   dr-acp's children all end before the root's turn does.
7. **Cost snapshots per change** could be frequent for a generic agent that reports usage often; D1 throttles at
   the source (≤ 2 per second per dirty child). If E6's 50-child run shows the store as the bottleneck, add a
   per-child minimum interval in the router; the contract does not change.

---

## Appendix A · Signature reference

Every block is valid, ruff-formatted Python (line length 88, upstream's setting) or TypeScript. Bodies are `...`
where §4 describes them. Excerpts of existing classes show only what S1 adds.

### A.1 `openhands-sdk/openhands/sdk/agent/acp_unstable.py` (the shim)

```python
"""ACP's unstable sub-agent types, carried until agent-client-protocol parses them.

ACP schema 1.24.1 added ``clientCapabilities.subagents`` and the ``subagent_update``,
``session_message`` and ``session_message_chunk`` session updates behind its unstable
flag; agent-client-protocol 0.12.1 drops all four. The models are upstream's generator
output for schema 1.24.1 (python-sdk 9d07d78), adapted to 0.12.1's base model. Delete
this module when ``test_acp_library_rejects_subagent_update`` fails.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Annotated, Any, Final, Literal

from acp.client.connection import ClientSideConnection
from acp.connection import MethodHandler
from acp.interfaces import Client
from acp.meta import AGENT_METHODS
from acp.schema import (
    AudioContentBlock,
    BaseModel as ACPModel,
    ClientCapabilities,
    EmbeddedResourceContentBlock,
    ImageContentBlock,
    Implementation,
    InitializeResponse,
    ResourceContentBlock,
    StopReason,
    TextContentBlock,
)
from acp.utils import request_model
from pydantic import ConfigDict, Field, TypeAdapter


UNSTABLE_SESSION_UPDATES: Final[frozenset[str]] = frozenset(
    {"subagent_update", "session_message", "session_message_chunk"}
)

ContentBlock = Annotated[
    TextContentBlock
    | ImageContentBlock
    | AudioContentBlock
    | ResourceContentBlock
    | EmbeddedResourceContentBlock,
    Field(discriminator="type"),
]


class SubagentCapabilities(ACPModel):
    field_meta: Annotated[dict[str, Any] | None, Field(alias="_meta")] = None


class SessionCancelCapabilities(ACPModel):
    field_meta: Annotated[dict[str, Any] | None, Field(alias="_meta")] = None


class SubagentSessionCapabilities(ACPModel):
    cancel: SessionCancelCapabilities | None = None
    field_meta: Annotated[dict[str, Any] | None, Field(alias="_meta")] = None


class SubagentState(ACPModel):
    """running, idle, requires_action, unknown, or a custom state kept whole."""

    model_config = ConfigDict(extra="allow")

    state: str
    stop_reason: Annotated[StopReason | None, Field(alias="stopReason")] = None
    field_meta: Annotated[dict[str, Any] | None, Field(alias="_meta")] = None


class SubagentUpdate(ACPModel):
    session_update: Annotated[
        Literal["subagent_update"],
        Field(alias="sessionUpdate"),
    ]
    session_id: Annotated[str, Field(alias="sessionId")]
    title: str | None = None
    description: str | None = None
    capabilities: SubagentSessionCapabilities | None = None
    state: SubagentState | None = None
    field_meta: Annotated[dict[str, Any] | None, Field(alias="_meta")] = None


class SessionMessage(ACPModel):
    session_update: Annotated[
        Literal["session_message"],
        Field(alias="sessionUpdate"),
    ]
    message_id: Annotated[str, Field(alias="messageId")]
    sender_session_id: Annotated[
        str | None,
        Field(alias="senderSessionId"),
    ] = None
    recipient_session_id: Annotated[
        str | None,
        Field(alias="recipientSessionId"),
    ] = None
    content: list[ContentBlock] | None = None
    field_meta: Annotated[dict[str, Any] | None, Field(alias="_meta")] = None


class SessionMessageChunk(ACPModel):
    session_update: Annotated[
        Literal["session_message_chunk"],
        Field(alias="sessionUpdate"),
    ]
    message_id: Annotated[str, Field(alias="messageId")]
    sender_session_id: Annotated[
        str | None,
        Field(alias="senderSessionId"),
    ] = None
    recipient_session_id: Annotated[
        str | None,
        Field(alias="recipientSessionId"),
    ] = None
    content: ContentBlock
    field_meta: Annotated[dict[str, Any] | None, Field(alias="_meta")] = None


UnstableSessionUpdate = SubagentUpdate | SessionMessage | SessionMessageChunk
UnstableUpdateHandler = Callable[[str, UnstableSessionUpdate], None]

_UNSTABLE_UPDATE_ADAPTER: Final = TypeAdapter(
    Annotated[UnstableSessionUpdate, Field(discriminator="session_update")]
)


class SubagentClientCapabilities(ClientCapabilities):
    subagents: SubagentCapabilities | None = None


SUBAGENT_CLIENT_CAPABILITIES: Final = SubagentClientCapabilities(
    subagents=SubagentCapabilities()
)


class _SubagentInitializeRequest(ACPModel):
    protocol_version: Annotated[int, Field(alias="protocolVersion")]
    client_capabilities: Annotated[
        SubagentClientCapabilities,
        Field(alias="clientCapabilities"),
    ]
    client_info: Annotated[Implementation | None, Field(alias="clientInfo")] = None
    field_meta: Annotated[dict[str, Any] | None, Field(alias="_meta")] = None


# ClientSideConnection is @final in agent-client-protocol 0.12.1; this subclass
# lives only until the library parses ACP's sub-agent updates itself.
class SubagentClientSideConnection(
    ClientSideConnection,  # pyright: ignore[reportGeneralTypeIssues]
):
    """A ClientSideConnection that hands ACP's unstable sub-agent updates to a
    callback ahead of the library's router, and can advertise ``subagents``."""

    def __init__(
        self,
        to_client: Client,
        input_stream: asyncio.StreamWriter,
        output_stream: asyncio.StreamReader,
        *,
        on_unstable_update: UnstableUpdateHandler,
    ) -> None: ...

    async def initialize(
        self,
        protocol_version: int,
        client_capabilities: ClientCapabilities | None = None,
        client_info: Implementation | None = None,
        **kwargs: Any,
    ) -> InitializeResponse:
        """Send ``initialize`` typed with ``SubagentClientCapabilities`` when given
        one, so ``subagents`` reaches the wire; otherwise the library's call."""
        ...


def route_unstable_updates(
    inner: MethodHandler,
    on_unstable_update: UnstableUpdateHandler,
) -> MethodHandler:
    """Wrap a connection handler: the three unstable updates reach
    ``on_unstable_update`` synchronously, in arrival order; an invalid one is
    logged and dropped; every other message goes to ``inner``."""
    ...
```

### A.2 `openhands-sdk/openhands/sdk/agent/acp_subagents.py`

```python
"""Sub-agent sessions of an ACP agent, as the bridge sees them on one connection.

The client side of ACP's sub-agent sessions (schema 1.24.1, unstable): which sessions
are children, their merged association, their streamed text and directed messages,
their cost, and whether a client may cancel them now. Bookkeeping only: each method
returns the events to persist; nothing here emits, locks, awaits or does I/O.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any

from acp.schema import UsageUpdate

from openhands.sdk.agent.acp_unstable import (
    SessionMessage,
    SessionMessageChunk,
    SubagentUpdate,
)
from openhands.sdk.event import (
    ACPSessionMessageEvent,
    ACPSessionTextEvent,
    ACPSubagentEvent,
    Event,
)


class ACPSessionNotFoundError(LookupError):
    """No sub-agent session with this id is known on the ACP connection."""


class ACPSessionNotCancellableError(RuntimeError):
    """The session cannot be cancelled now: no live connection, the root session,
    or no current ``cancel`` grant from the agent."""


@dataclass
class _Association:
    parent_session_id: str | None
    parent_tool_call_id: str | None = None
    title: str | None = None
    description: str | None = None
    state: str | None = None
    stop_reason: str | None = None
    cancel_granted: bool = False
    cost: float | None = None
    cost_currency: str | None = None
    meta: dict[str, Any] | None = None


@dataclass
class _Pending:
    thought: bool | None
    message_id: str | None
    parts: list[str] = field(default_factory=list)


@dataclass
class _Message:
    sender_session_id: str | None = None
    recipient_session_id: str | None = None
    text: str = ""
    meta: dict[str, Any] | None = None


class ACPSubagentSessions:
    """Routing, merge, segments, cost and cancel grants for one ACP connection."""

    root_session_id: str | None
    replaying: bool

    def __init__(self, *, mask: Callable[[Any], Any]) -> None: ...

    def seed(self, events: Iterable[Event]) -> list[ACPSubagentEvent]:
        """Register the children stored in ``events``; return the snapshots that
        withdraw their cancel grants and unconfirm their states."""
        ...

    def is_child(self, session_id: str) -> bool: ...

    def key(self, session_id: str) -> str | None:
        """The stored form of a session id: ``None`` for the root."""
        ...

    def on_subagent_update(
        self,
        session_id: str,
        update: SubagentUpdate,
    ) -> list[Event]: ...

    def on_session_message(
        self,
        session_id: str,
        update: SessionMessage,
    ) -> list[Event]: ...

    def on_session_message_chunk(
        self,
        session_id: str,
        update: SessionMessageChunk,
    ) -> list[Event]: ...

    def on_child_text(
        self,
        session_id: str,
        text: str,
        *,
        thought: bool,
    ) -> list[Event]: ...

    def on_child_usage(
        self,
        session_id: str,
        update: UsageUpdate,
    ) -> list[Event]: ...

    def before_update(self, session_id: str) -> list[Event]:
        """Flush ``session_id``'s open segment; called before any update for it
        that is not a text chunk, a message chunk or a usage update."""
        ...

    def flush_all(self) -> list[Event]: ...

    def check_cancel(self, session_id: str) -> None:
        """Raise unless the agent granted ``cancel`` for this child, live."""
        ...
```

### A.3 `openhands-sdk/openhands/sdk/agent/acp_agent.py` (excerpts)

```python
class _OpenHandsACPBridge:
    """Excerpt: the new members only."""

    subagents: ACPSubagentSessions | None
    # The conversation's emitter (ACPAgent._on_session_event), set per connection.
    on_session_event: Callable[[Event], None] | None

    def __init__(self, *, subagents: bool = False) -> None: ...

    def unstable_session_update(
        self,
        session_id: str,
        update: SubagentUpdate | SessionMessage | SessionMessageChunk,
    ) -> None:
        """The shim's callback: route one unstable update; never awaits."""
        ...

    def emit_subagent_events(self, events: Sequence[Event]) -> None:
        """Submit each event to ``on_session_event``, in order; drop them while
        replaying, and with a debug line when no emitter is wired."""
        ...

    def flush_subagent_text(self) -> None:
        """Submit every open child segment; runs on the ACP loop after a prompt."""
        ...

    def _child_session(self, session_id: str) -> str | None: ...


class ACPAgent(AgentBase):
    """Excerpt: the new members only. ``_on_session_event`` is S2's (its A.3)."""

    acp_subagents: bool = Field(
        default=False,
        description=(
            "Advertise ACP's unstable sub-agent sessions "
            "(clientCapabilities.subagents, schema 1.24.1) to the ACP server, and "
            "route and persist the child sessions it exposes: their association "
            "with the parent, tool calls, messages, text and cost. Off by default "
            "while the protocol draft is unstable."
        ),
    )

    def cancel_acp_session(self, session_id: str) -> None:
        """Ask the ACP server to cancel one sub-agent session's current work.

        Sends ``session/cancel`` for ``session_id`` when the server announced that
        child on the live connection with a ``cancel`` capability. Returns once the
        notification is written; the outcome arrives as the child's next state
        update. Never takes the conversation's state lock, so it works mid-turn.

        Raises:
            ACPSessionNotFoundError: no sub-agent session with this id is known.
            ACPSessionNotCancellableError: no live ACP connection, the root
                session, or no current ``cancel`` grant.
            TimeoutError: the notification was not written within 2 seconds.
        """
        ...

    async def _acancel_acp_session(self, session_id: str) -> None: ...
```

### A.4 Events: `event/acp_subagent.py` and the `ACPToolCallEvent` fields

```python
class ACPSubagentEvent(Event):
    """An ACP sub-agent session's association with its parent, as last reported.

    ACP's ``subagent_update`` (schema 1.24.1, unstable) with its patch semantics
    already applied: each event is the whole current association, so consumers
    keep the latest per ``acp_session_id``. Written per ``subagent_update``, per
    change of the child's reported cost, and, with ``source="environment"``, when
    a new ACP connection starts (state unconfirmed, cancel withdrawn).
    """

    source: SourceType = "agent"
    acp_session_id: str = Field(description="The child's ACP session id.")
    parent_session_id: str | None = Field(
        default=None,
        description="The parent's ACP session id; None for the root session.",
    )
    parent_tool_call_id: str | None = Field(
        default=None,
        description=(
            "The parent's tool call that spawned the child, from "
            "_meta.openhands.parentToolCallId."
        ),
    )
    title: str | None = None
    description: str | None = None
    state: str | None = Field(
        default=None,
        description=(
            "'running', 'idle', 'requires_action', 'unknown', an agent-specific "
            "value, or None when the current state is unconfirmed."
        ),
    )
    stop_reason: str | None = None
    cancellable: bool = Field(
        default=False,
        description="Whether a client may cancel this child's work now.",
    )
    cost: float | None = Field(
        default=None,
        description="The child's latest cumulative cost; never add it to others.",
    )
    cost_currency: str | None = None
    meta: dict[str, Any] | None = Field(
        default=None,
        description="The association's ACP _meta, verbatim.",
    )


class ACPSessionMessageEvent(Event):
    """A message between ACP sessions, as one session's transcript shows it.

    ACP's ``session_message`` and accumulated ``session_message_chunk`` (schema
    1.24.1, unstable). Upserts: consumers keep the latest per
    ``(acp_session_id, message_id)``.
    """

    source: SourceType = "agent"
    acp_session_id: str | None = Field(
        default=None,
        description="The transcript this entry belongs to; None for the root.",
    )
    message_id: str
    sender_session_id: str | None = None
    recipient_session_id: str | None = None
    text: str = ""
    meta: dict[str, Any] | None = None


class ACPSessionTextEvent(Event):
    """A run of a sub-agent session's own streamed text or reasoning.

    Consecutive ``agent_message_chunk`` (``thought`` false) or
    ``agent_thought_chunk`` (``thought`` true) updates of one child session,
    stored once the run ends.
    """

    source: SourceType = "agent"
    acp_session_id: str
    thought: bool = False
    text: str


class ACPToolCallEvent(Event):
    """Excerpt: the two new fields."""

    acp_session_id: str | None = Field(
        default=None,
        description="The ACP sub-agent session the call ran in; None for the root.",
    )
    meta: dict[str, Any] | None = Field(
        default=None,
        description="The call's latest ACP _meta; recorded with acp_subagents.",
    )
```

### A.5 Settings, conversation and agent-server

```python
class ACPAgentSettings(AgentSettingsBase):
    """Excerpt: the new field, forwarded by ``create_agent()``."""

    acp_subagents: bool = Field(
        default=False,
        description=(
            "Advertise ACP's unstable sub-agent sessions to the ACP server and "
            "persist the child sessions it exposes. Forwarded to "
            ":attr:`~openhands.sdk.agent.ACPAgent.acp_subagents`; off by default."
        ),
    )


class LocalConversation(BaseConversation):
    """Excerpt: S1's method. S2's emitter, ``_emit_event_from_any_thread``, its
    executor and its wiring are S2's Appendix A.4, built by whichever lands
    first."""

    def cancel_acp_session(self, session_id: str) -> None:
        """Cancel one ACP sub-agent session's current work.

        Unlike ``switch_acp_model`` this takes no state lock: it must work while
        a synchronous ``run()`` holds the lock for the whole turn.

        Raises:
            ValueError: the conversation's agent is not an ``ACPAgent``.
            ACPSessionNotFoundError: as ``ACPAgent.cancel_acp_session``.
            ACPSessionNotCancellableError: as ``ACPAgent.cancel_acp_session``.
            TimeoutError: as ``ACPAgent.cancel_acp_session``.
        """
        ...


class EventService:
    """Excerpt: the new method."""

    async def cancel_acp_session(self, session_id: str) -> None:
        """Run ``LocalConversation.cancel_acp_session`` off the server's loop."""
        ...


# openhands/agent_server/acp_router.py (S2's module; S1's additions)
class CancelACPSessionResponse(BaseModel):
    """A cancel sent to an ACP sub-agent session; its outcome arrives later."""

    session_id: str = Field(description="The ACP session the cancel was sent for.")
    requested: bool = Field(
        default=True,
        description="Always true; the child's next state update confirms it.",
    )


@conversation_acp_router.post(
    "/sessions/{session_id}/cancel",
    responses={
        400: {"description": "The conversation's agent is not an ACP agent"},
        404: {"description": "Conversation or ACP sub-agent session not found"},
        409: {"description": "The ACP session does not accept cancel right now"},
        504: {"description": "The ACP server did not take the cancel in time"},
    },
)
async def cancel_conversation_acp_session(
    conversation_id: UUID,
    session_id: str,
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> CancelACPSessionResponse:
    """Cancel the current work of one ACP sub-agent session.

    Sends ``session/cancel`` for a child session the ACP agent announced with a
    ``cancel`` capability. The child's next ``ACPSubagentEvent`` (idle, stop
    reason ``cancelled``) confirms it.
    """
    ...
```

### A.6 TypeScript client

```typescript
// src/events/types.ts
export type ACPToolCallEvent = AgentServerAcpToolCallEvent & {
  /** The ACP sub-agent session the call ran in; absent for the root session. */
  acp_session_id?: string | null;
  /** The call's latest ACP `_meta`; recorded only for agents with `acp_subagents`. */
  meta?: Record<string, unknown> | null;
};

/** The latest association of an ACP sub-agent session with its parent. */
export interface ACPSubagentEvent extends BaseEvent {
  kind: 'ACPSubagentEvent';
  acp_session_id: string;
  parent_session_id?: string | null;
  parent_tool_call_id?: string | null;
  title?: string | null;
  description?: string | null;
  state?: string | null;
  stop_reason?: string | null;
  cancellable?: boolean;
  cost?: number | null;
  cost_currency?: string | null;
  meta?: Record<string, unknown> | null;
}

/** A message between ACP sessions, as one session's transcript shows it. */
export interface ACPSessionMessageEvent extends BaseEvent {
  kind: 'ACPSessionMessageEvent';
  acp_session_id?: string | null;
  message_id: string;
  sender_session_id?: string | null;
  recipient_session_id?: string | null;
  text?: string;
  meta?: Record<string, unknown> | null;
}

/** A run of a sub-agent session's own streamed text or reasoning. */
export interface ACPSessionTextEvent extends BaseEvent {
  kind: 'ACPSessionTextEvent';
  acp_session_id: string;
  thought?: boolean;
  text: string;
}

export interface CancelAcpSessionResponse {
  session_id: string;
  requested: boolean;
}

// ConversationEvent gains `| ACPSubagentEvent | ACPSessionMessageEvent | ACPSessionTextEvent`.
export function isACPSubagentEvent(event: BaseEvent): event is ACPSubagentEvent {
  return event.kind === 'ACPSubagentEvent';
}

export function isACPSessionMessageEvent(event: BaseEvent): event is ACPSessionMessageEvent {
  return event.kind === 'ACPSessionMessageEvent';
}

export function isACPSessionTextEvent(event: BaseEvent): event is ACPSessionTextEvent {
  return event.kind === 'ACPSessionTextEvent';
}

// src/client/conversation-client.ts (excerpt)
export class ConversationClient {
  /**
   * Cancel one ACP sub-agent session's current work. 409 when the child did not
   * advertise `cancel` (or no ACP connection is live); the child's next
   * `ACPSubagentEvent` (idle, `cancelled`) confirms it.
   */
  async cancelAcpSession(
    conversationId: string,
    sessionId: string
  ): Promise<CancelAcpSessionResponse> {
    const session = encodeURIComponent(sessionId);
    const response = await this.client.post<CancelAcpSessionResponse>(
      `/api/conversations/${conversationId}/acp/sessions/${session}/cancel`
    );
    return response.data;
  }
}

// src/conversation/remote-conversation.ts (excerpt)
export class RemoteConversation {
  async cancelAcpSession(sessionId: string): Promise<CancelAcpSessionResponse> {
    const session = encodeURIComponent(sessionId);
    const response = await this.client.post<CancelAcpSessionResponse>(
      `/api/conversations/${this.id}/acp/sessions/${session}/cancel`
    );
    return response.data;
  }
}

// src/models/acp.ts: ACP_SETTINGS_KEYS gains 'acp_subagents'.
```

### A.7 `tests/fixtures/acp/scripted_agent.py` (S1's additions to S2's script)

The command line S1 adds (S2's flags and `SCRIPTED_ACP_LOG` unchanged, S2 Appendix C):

| Flag | Default | Effect |
|---|---|---|
| `--subagents` | off | play §4.10's sub-agent run on each `session/prompt`, before S2's reply |
| `--cancel-wait SECONDS` | `0` | how long `child-b` waits for `session/cancel` (0: it does not wait) |
| `--transcript PATH` | — | play a JSONL transcript instead of every built-in behaviour |
| `--wait-timeout SECONDS` | `30` | a transcript wait point's limit; past it the script exits non-zero |

```python
DEFAULT_WAIT_TIMEOUT_S: Final[float] = 30.0


def add_subagent_arguments(parser: argparse.ArgumentParser) -> None:
    """Add --subagents, --cancel-wait, --transcript and --wait-timeout."""
    ...


async def serve(
    handler: MethodHandler,
    *,
    on_initialize: Callable[[dict[str, Any]], None],
) -> Connection:
    """Serve ``handler`` over stdio through ``acp.connection.Connection``.

    ``handler`` is ``build_agent_router(agent)`` for the built-in behaviours, or
    a ``TranscriptPlayer``'s ``handle``; a tap in front of it passes
    ``initialize``'s raw params to ``on_initialize`` and writes the request log.
    """
    ...


async def play_subagent_run(
    conn: Connection,
    root_session_id: str,
    *,
    advertised: bool,
    cancel_wait_s: float,
    cancelled: asyncio.Event,
) -> None:
    """Send §4.10's generic sub-agent run as raw session/update notifications;
    only the root's lines when the client did not advertise ``subagents``."""
    ...


class TranscriptPlayer:
    """Plays one JSONL transcript over one connection (§4.10's rules)."""

    def __init__(
        self,
        transcript: Sequence[dict[str, Any]],
        *,
        wait_timeout_s: float = DEFAULT_WAIT_TIMEOUT_S,
    ) -> None: ...

    async def handle(
        self,
        method: str,
        params: Any,
        is_notification: bool,
    ) -> Any:
        """The connection's handler: match a client message to a wait point."""
        ...

    async def play(self, conn: Connection) -> None:
        """Walk the transcript once; raise TimeoutError at a missed wait point."""
        ...
```
