# S1 · ACP sub-agent sessions in the agent-server, as built

**TASK-3** · Cartographer · the code at `0cfb6a2`, head of `feat/acp-subagent-sessions` in the SDK fork
[michaeltheologitis/software-agent-sdk](https://github.com/michaeltheologitis/software-agent-sdk) (draft PR #2 into
`feat/agent-surfaces`; S1 is `6f97bf3..0cfb6a2`, five commits stacked on S2's head `6f97bf3`) · checked against the
design at `f956fda` (`docs/design/s1-acp-subagent-sessions.md` v1, unchanged on this branch) · agent-client-protocol
0.12.1 (the fork's lock) · uv 0.12.23 (`uvx uv@latest`), Python 3.13.14 and Node 22.22 in this sandbox · 2026-10-03.

**Where this file lives.** On deep-reasoning's branch `as-built/s1`, cut from `design/s1` at `f956fda`: S1's code is
in the SDK fork, whose branches carry only upstream-shaped code, so no document of ours goes there. This branch has
no `pyproject.toml`, no docs site and no test runner, so nothing builds an sdist or collects `as_built/`, and there is
nothing to wire. [run: `git ls-tree -r HEAD`]

**Evidence marks.** Every claim carries one.
- **[run]**: executed in this sandbox at `0cfb6a2`, without writing tracked files in the checkout: S1's Python test
  files (§7.1), the TypeScript client's suite in a `git archive` copy, upstream's guard scripts, and uncommitted
  probe scripts in my scratchpad that drive a real `LocalConversation` against the scripted ACP agent, or feed the
  bridge directly. No network beyond PyPI for the settings guard; no model.
- **[CI]**: read from GitHub's records through the MCP tools: PR #2's checks at `0cfb6a2` and the live run
  [37141960911](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37141960911). Log tails only (§9).
- **[read]**: read in the code, **not executed**. Weaker than [run]; §9 lists the read claims that matter.

Nothing in this document ran a paid model or the `claude` CLI; the live tier is reported from CI.

**Reading order.** §2 first (the divergences), then §1, §3 and §4 as the map, §5 for what C1, D1 and D5 rely on, §7
for the measurements, §9 for what I could not verify.

---

## 1 · What exists

With `acp_subagents` on, the bridge advertises `clientCapabilities.subagents`, takes ACP's three unstable updates
ahead of agent-client-protocol's router, routes every update by session, and stores each announced child (its
association with its parent, its tool calls, the messages between sessions, its own text, its cost) through the
conversation's out-of-turn emitter, which S2 built. A REST route cancels one child that holds a live `cancel` grant.
With the opt-in off (the default) the connection class, the `initialize` call, the routing and the stored events
are the stock ones. [read; each part run in §7]

```text
ACP agent ── stdout ──▶ _filter_jsonrpc_lines (unchanged)
   ▼
SubagentClientSideConnection (acp_unstable.py; opt-in on)          stock ClientSideConnection (opt-in off)
   │ session/update whose sessionUpdate ∈ {subagent_update, session_message, session_message_chunk}
   │    → one TypeAdapter → bridge.unstable_session_update(sessionId, update), synchronously
   │ every other message → the library's router → bridge.session_update, as before
   ▼
_OpenHandsACPBridge.session_update (acp_agent.py:1712)
   S2's controls recorder → ask_agent fork session → _child_session(session_id)
   ├ root, or a session never announced → the stock path: answer text, thoughts, tool calls, usage → turn's on_event
   └ announced child → ACPSubagentSessions (acp_subagents.py): text runs, usage → cost
                       its tool calls take the shared tool-call path, keyed (session, toolCallId)
child events ─▶ bridge.on_session_event = ACPAgent._on_session_event = LocalConversation._emit_event_from_any_thread
                (S2's: one worker thread, first in first out, takes the state lock, calls _on_event)
   ▼
ConversationState.events ── /events/search, WebSocket ── TypeScript client ── Canvas (C1)

cancel: POST /api/conversations/{id}/acp/sessions/{session_id}/cancel (acp_router.py, S2's module)
        → EventService.cancel_acp_session (default executor) → LocalConversation.cancel_acp_session (no lock)
        → ACPAgent.cancel_acp_session → run_async(_acancel_acp_session, timeout=2.0) on the ACP loop
        → check_cancel(session_id) → session/cancel {sessionId}; the outcome arrives as the child's own update
```

| Part | Lines (`6f97bf3..0cfb6a2`) | Where |
|---|---|---|
| the shim | 247, new | `openhands-sdk/openhands/sdk/agent/acp_unstable.py` |
| the router | 338, new | `openhands-sdk/openhands/sdk/agent/acp_subagents.py` |
| bridge and agent | +287 −40 | `openhands-sdk/openhands/sdk/agent/acp_agent.py` |
| events | +177 | `event/acp_subagent.py` (160, new), `event/acp_tool_call.py`, `event/__init__.py` |
| other SDK consumers | +79 −8 | local and remote conversation, visualizer, resume transcript, settings, three profile files |
| agent-server | +77 −1 | `acp_router.py`, `event_service.py` |
| TypeScript client | +112 −2 source, +27 config | `clients/typescript/src/…`, `endpoint-audit.config.json`, `config/public-type-budget.json` |
| tests | Python +2,069, scripted agent +459 −4, settings fixture +12, TypeScript +126 | `tests/…`, `clients/typescript/src/__tests__/…` |
| CI config | +20 | weak-schema allowlist (+18), `.github/workflows/tests.yml` (+2) |

Total +4,030 −56 in 42 files. Five commits, oldest first, with design §8's titles word for word: `13f4571` (the
shim, +510), `d10c021` (events, +367 −8), `6938ba5` (bridge, settings, profiles, scripted agent, SDK tests, live
tests, +2,565 −44), `57c0925` (the cancel route, +323 −2), `0cfb6a2` (TypeScript, +265 −2). [run: `git log`,
`git diff --numstat`]

Tests added: 86 Python (84 deterministic, 2 marked `acp_live`) and 6 TypeScript. [run: collected]

---

## 2 · Divergences from the design (`f956fda`)

The changelog holds no `drift:` line for TASK-3 [run: Notion query of the Changelog], so every item below was found
from the code. The design file has one commit on this branch, `f956fda` (2026-10-02 18:39); all five build commits
are later (2026-10-03 06:00). "Design §x" cites `f956fda`. Several items trace to asks in C1's design v2
(`design/c1` `88f5c43`, §9.1) and D5's (`design/d5` `8086afb`, §8.2), which came after `f956fda`; S1's design was not
revised to carry them.

### 2.1 Behaviour a client or a consumer sees

**D-1 · A reconnect writes "state unconfirmed, cancel withdrawn" snapshots only for children last seen active.**
`ACPSubagentSessions.seed` returns an `environment` snapshot for each stored child whose latest snapshot has a
`state` other than `None` and `"idle"` (`acp_subagents.py:104–108`); `cancellable` plays no part. Design §1.3 H,
§2 (Restart), §3 item 7 and §4.3 (Seed): "cancellable **or** active". Consequence: a child whose last snapshot was
`idle` and `cancellable: true` (every finished dr-acp child, since D1 keeps `capabilities.cancel` on idle children,
design §10) keeps `cancellable: true` in the store after a reconnect, while the route answers 409 for it (the new
connection holds no grant). Design §5 rule 6, which C1 follows, hides Stop on idle children either way. Reason: C1 design v2 §9.1 item 4
(optional: "would keep the log smaller and the meaning sharper"). [run: `test_new_connection_withdraws_cancel_and_unconfirms_state`
asserts that an idle, cancellable child gets no reset snapshot and that `check_cancel` refuses it]

**D-2 · The opt-in also lives on `ACPAgentProfile`.** `acp_subagents: bool = False` on `ACPAgentProfile`
(`profiles/agent_profile.py:292`), forwarded by the resolver (`profiles/resolver.py:305`) and carried back by the seed
(`profiles/seed.py:58`); the TypeScript `ACPAgentProfile` gains `acp_subagents?: boolean`. Design §4.6 puts the field
on `ACPAgent` and `ACPAgentSettings` only. Reason: Canvas starts conversations from the active agent profile, and
`ACPAgentProfile` forbids unknown keys (C1 §9.1 item 1, D5 §8.2). Both asks also name a persisted-profile fixture;
none is added (the only new baseline is the settings one). [run: `test_acp_profile_carries_the_subagents_opt_in_to_the_agent`
(both values), `test_acp_seeded_profile_keeps_the_subagents_opt_in`; read: no new profile baseline under
`tests/sdk/persisted_settings_baselines/`]

**D-3 · Child tool calls get no observability spans.** The bridge opens and closes `ACPTurnTrace` tool spans only for
root calls (`acp_agent.py:1790`, `:1850`), and `finish_turn` receives only root calls (`:4196–4202`). Design §4.4 does
not mention the trace. No reason recorded in the commits. [read]

### 2.2 Where the code landed

**D-4 · S1 is stacked on S2 and owns none of the shared pieces.** Design §8 cuts the branch from the fork's
`deep-reasoning` at `91430aa`; §9 and §11 item 5 leave the landing order open. Built: S2 landed first, so S1 is
`6f97bf3..0cfb6a2` on top of `feat/agent-surfaces` (which merged the fork's `deep-reasoning`, now `ea51b3f`, after
`91430aa`), and S2 owns the out-of-turn emitter (`LocalConversation._emit_event_from_any_thread`, `_ensure_agent_ready`'s wiring at
`local_conversation.py:1578`), the scripted agent with its `Connection`-based `serve` (design §4.10's serving
requirement was already met), and `acp_router.py` with `conversation_acp_router`. S1 adds no emitter commit. The seed
call sits in `_launch_acp_session` (`acp_agent.py:3302`), S2's split of `_start_acp_server`. [run: `git log`, `git
merge-base`]

**D-5 · The draft PR targets `feat/agent-surfaces`, so upstream's main-only guards did not run in CI.** Design §8:
the branch "cherry-picked onto the fork's `main`, gets a draft PR there". PR #2's base is `feat/agent-surfaces`; the
persisted-settings, REST-breakage and TypeScript-client CI workflows trigger only on pull requests to `main`, and the
OpenAPI quality ratchet only in the release workflow. PR #2 ran 16 checks (§6). I ran the guards here instead (§7.6).
Whether each commit is green on its own, and cherry-picks onto `main`, is not checked (§9). [CI: check runs; read:
workflow triggers]

### 2.3 The scripted agent

**D-6 · `--transcript-interval-ms MS`**, a sleep before each `session/update` a transcript sends
(`scripted_agent.py:29`, `:707`), not in design §4.10 or A.7. Reason: C1 §9.1 item 2 (E6 paced at 60 events/s).
[run: `test_transcript_interval_paces_the_replay`]

**D-7 · The `--subagents` run's order differs in detail** (`play_subagent_run`, `scripted_agent.py:362`): `child-a`
sends two thoughts (stored as one run); its grandchild is announced, answers and turns idle while `cell-a1` is still
in progress, and `cell-a1` completes after it (design: `cell-a1` completes, then the grandchild runs); the root's
0.0011 USD `usage_update` follows S2's reply text instead of preceding it. The tree, ids, titles, grants and costs
are design §4.10's. [read; the stored result run in §7.2]

**D-8 · An outgoing-only transcript whose responses are not `initialize`, `session/new` or `session/prompt` is
refused.** `_inferred_method` raises `ValueError` naming the line (`scripted_agent.py:475–488`), so the script exits
before serving. Design §4.10 names the three shapes and is silent on any other. All nine of D1's native golden
recordings hold only those three [run: §7.3].

### 2.4 Tests, the live tier and size

**D-9 · Tests moved, renamed, or tested through a real server.**
- `test_stored_events_validate_against_the_agent_server_event_schema` (design §7.2, SDK file) is
  `tests/agent_server/test_acp_router.py::test_stored_sub_agent_events_validate_against_the_event_schema`: the
  events are read over the REST page of an in-process agent-server app (httpx `ASGITransport`, real
  `ConversationService`, the scripted agent as a subprocess) and validated against `build_public_openapi()`'s
  `Event` schema with `jsonschema`. [run]
- `test_scripted_transcript_replays_an_outgoing_only_recording` is `test_scripted_transcript_replays_a_recording`,
  parametrized `full` and `outgoing-only`. [run]
- The route tests (design §7.3: six names, "a mocked event service") are seven tests against that same in-process
  app, S2's fixture, under other names (§7.5). The root's 409 is tested at the SDK
  level only. [run]

**D-10 · Tests beyond design §7** (all pass, §7): `test_custom_state_is_kept_whole`,
`test_message_content_keeps_non_text_blocks_typed`, `test_scripted_run_books_only_the_roots_cost`,
`test_transcript_interval_paces_the_replay`, `test_transcript_wait_point_that_is_never_reached_exits_non_zero`,
three ordering tests that C1 §9.1 item 3 asked S1 to state as contract (`test_a_childs_stored_timestamps_never_decrease_in_log_order`,
`test_a_reconnect_snapshot_is_later_than_the_childs_earlier_events`, `test_a_spawning_cells_started_event_precedes_its_whole_subtree`;
design §5 does not state them), two visualizer tests, `test_cancel_acp_session_on_an_inactive_service_is_refused`,
`test_acp_seeded_profile_keeps_the_subagents_opt_in`, and the TypeScript `each guard recognises only its own kind`.
[run]

**D-11 · The live tier asserts less than design §7.4 in one place and differently in another.**
`test_live_agent_tree_is_well_formed` does not assert "every child that reported a cost has it on its association";
its "no child text in the answer" checks only child text runs of 40 characters or more (`QUOTED_TEXT_MIN_CHARS`,
`test_acp_subagents_live.py:46`); it additionally requires at least one grandchild. The fork's own CI job
`acp-live-tests` now lists S1's live file (`.github/workflows/tests.yml`, +2), where it skips without the two
variables. [read; CI: both skipped in the fork's job, both passed in 37141960911]

**D-12 · Upstream guards the design did not list.** The TypeScript public weak-type budget gains three `meta` sites
(`config/public-type-budget.json`, category `acp-protocol-meta`); design §3 item 11 names the OpenAPI allowlist only.
The OpenAPI allowlist has three entries and no `-Input`/`-Output` twins (+18 lines against +24). [run: budget
"unchanged: 106 sites"; ratchet §7.6]

**D-13 · Size: about 2.2 times the estimate.** Design §3 item 16: about 1.8k lines with tests. Built: +4,030 −56.
Product code is near its estimates except the bridge (`acp_agent.py` +287 −40 against +100); the excess is in the
tests: Python tests +2,069 against 750 (of which `test_acp_subagents.py` is 1,161), the scripted agent +459 against
+180. [run: `git diff --numstat`]

### 2.5 Small differences

None changes what §2.1 describes. [read unless marked]

| Design | Built |
|---|---|
| router field `_warned: set[str]` (§4.3) | the bridge's `_unannounced_sessions` (`acp_agent.py:1452`); one WARNING per id [run: test] |
| `root_session_id` set "after the session is resolved" (§4.4) | set to the prior id in `_load_session` before `session/load` (`:5071–5093`), and to the new id in the `session/new` branch (`:3660`); same outcome on every path |
| the shim drops an invalid update with a WARNING (§4.2) | also drops a notification without a `sessionId` (`acp_unstable.py:227–229`), untested |
| `cancel_acp_session` with the opt-in off: not specified | `ACPSessionNotFoundError` (404 at the route) once a session is live (`acp_agent.py:5049–5052`) |

Not divergences: the shim (§4.2, A.1) is built as specified, with the one pyright suppression
(`acp_unstable.py:156`) and the one private-attribute touch (`self._conn._handler`, `:170`); the merge table of §4.3;
segments, directed messages, cost and replay rules; the bridge hunks of §4.4 other than D-3; the event models of
A.4 field for field; the route's statuses and `detail` texts of §4.7; the consumers of §4.8; the TypeScript surface of
§4.9 and A.6; the v7 fixture of §4.6 byte for byte; the commit titles of §8. [read; the behaviours run in §7]

---

## 3 · The public surface, from the code

**The opt-in.** `ACPAgent.acp_subagents: bool = False` (`acp_agent.py:2215`), `ACPAgentSettings.acp_subagents`
(`settings/model.py:1754`, forwarded by `create_agent()` at `:1967`), `ACPAgentProfile.acp_subagents` (D-2). No
`SETTINGS_METADATA_KEY`, so it is not in the settings form; `AGENT_SETTINGS_SCHEMA_VERSION` stays 7, and
`tests/sdk/persisted_settings_baselines/v7/agent_settings_acp_subagents.json` pins a stored `true`. The field rides
on the serialized agent, so `ConversationInfo.agent` carries it. [read; run: settings guard, oasdiff §7.6]

**Python calls.** `ACPAgent.cancel_acp_session(session_id) -> None` and
`LocalConversation.cancel_acp_session(session_id) -> None` (`local_conversation.py:1834`, no state lock;
`ValueError("cancel_acp_session is only supported for ACP conversations.")` for a non-ACP agent). Errors:
`ACPSessionNotFoundError(LookupError)` and `ACPSessionNotCancellableError(RuntimeError)`, importable from
`openhands.sdk.agent.acp_subagents` (not re-exported from `openhands.sdk.agent`), and `TimeoutError` after 2 s
(`_ACP_SUBAGENT_CANCEL_TIMEOUT`, `acp_agent.py:204`). The Python `RemoteConversation` has no cancel method. [read;
run: tests]

**Events** (`openhands.sdk.event`, registered by import; fields exactly design A.4) [read; run: round trip]:

| Kind | Written | Latest-wins key | Fields |
|---|---|---|---|
| `ACPSubagentEvent` | per `subagent_update`; per change of the child's cost; per reconnect for an active child (`source="environment"`, D-1) | `acp_session_id` | `parent_session_id` (`None` = root), `parent_tool_call_id`, `title`, `description`, `state` (`None` = unconfirmed), `stop_reason`, `cancellable`, `cost`, `cost_currency`, `meta` |
| `ACPSessionMessageEvent` | per `session_message`; per flushed chunked message | `(acp_session_id, message_id)` | `acp_session_id` (the transcript; `None` = root), `message_id`, `sender_session_id`, `recipient_session_id` (verbatim ids), `text`, `meta` |
| `ACPSessionTextEvent` | per flushed run of one child's `agent_message_chunk` or `agent_thought_chunk` | none, append-only | `acp_session_id`, `thought`, `text` |
| `ACPToolCallEvent` (changed) | as before | `(acp_session_id, tool_call_id)` | adds `acp_session_id` and `meta`, both written only with the opt-in on and dropped by `exclude_none` when unset |

**REST.** `POST /api/conversations/{conversation_id}/acp/sessions/{session_id}/cancel` on S2's
`conversation_acp_router` (`acp_router.py:168–227`), response `CancelACPSessionResponse{session_id, requested=true}`
[run: route tests; the exported OpenAPI lists the path with 200, 400, 404, 409, 422, 504]:

| Outcome | Status | `detail` |
|---|---|---|
| `session/cancel` written | 200 | — |
| no such conversation | 404 | — |
| `ACPSessionNotFoundError` | 404 | `ACP session {id} is not a sub-agent session of this conversation.` |
| `ACPSessionNotCancellableError` (the root, no live connection, no live grant) | 409 | `ACP session {id} does not accept cancel; cancel the conversation's turn instead.` |
| `ValueError` (not ACP; `inactive_service`) | 400 | the error's text |
| `TimeoutError` | 504 | `ACP server did not accept the cancel for {id} within 2s.` |

The exported OpenAPI gains `ACPSubagentEvent`, `ACPSessionMessageEvent`, `ACPSessionTextEvent` in the `Event`
union, `CancelACPSessionResponse`, `ACPToolCallEvent.acp_session_id`/`meta`, and `acp_subagents` on `ACPAgent`
wherever an agent appears. [run: export and oasdiff, §7.6]

**TypeScript** (`clients/typescript`): `ACPToolCallEvent` is the generated type intersected with
`{acp_session_id?, meta?}`; hand-written `ACPSubagentEvent`, `ACPSessionMessageEvent`, `ACPSessionTextEvent` in the
`ConversationEvent` union with guards `isACPSubagentEvent`, `isACPSessionMessageEvent`, `isACPSessionTextEvent`;
`CancelAcpSessionResponse`; `ConversationClient.cancelAcpSession(conversationId, sessionId)` and
`RemoteConversation.cancelAcpSession(sessionId)`, both URL-encoding the session id; `ACP_SETTINGS_KEYS` gains
`acp_subagents`; the route is an `allowClientOnly` entry in the endpoint audit. [read; run: the suite, §7.5]

**The scripted agent** (`tests/fixtures/acp/scripted_agent.py`, run by path): S1's flags `--subagents`,
`--cancel-wait SECONDS` (default 0), `--transcript PATH`, `--transcript-interval-ms MS` (default 0),
`--wait-timeout SECONDS` (default 30). It imports only `agent-client-protocol`. [read; run: tests]

---

## 4 · Structure and seams

### 4.1 The shim, `acp_unstable.py`

Models for the four unstable types on 0.12.1's `acp.schema.BaseModel` (aliases, optionality, `model_fields_set`
telling an omitted field from `null`; one tolerant `SubagentState` with `extra="allow"`), a `TypeAdapter` over the
three updates discriminated by `sessionUpdate`, `SubagentClientCapabilities(ClientCapabilities)` with `subagents`,
and `SubagentClientSideConnection`, which wraps its connection's handler with `route_unstable_updates` and sends
`initialize` through `request_model` with a standalone `_SubagentInitializeRequest` when given the subclass
capability. The callback runs inside the library's per-message handler task and never awaits, so unstable and
stable updates reach the bridge in wire order. With `SUBAGENT_CLIENT_CAPABILITIES` the wire carries
`"clientCapabilities": {"auth": {}, "subagents": {}}`. Two tripwire tests fail once the library parses
`subagent_update` or grows `ClientCapabilities.subagents`; the first fails with the design's instruction text word
for word. They pass at 0.12.1, which still rejects the unstable types. [run: `test_acp_unstable.py`, 10 tests]

### 4.2 The router, `acp_subagents.py`

`ACPSubagentSessions` is bookkeeping for one connection: each method returns the events to store; nothing emits,
locks, awaits or does I/O. State: `root_session_id`, `replaying`, `_children` (one `_Association` per known child),
`_pending` (at most one open segment per session: a text run or a chunked message), `_messages` (resolved directed
messages by `(session, messageId)`). [read]

- **Children.** A child is known once announced on this connection or seeded from stored events. The first
  `subagent_update` for an id announces it under the session it arrived on (`None` for the root), so a child's
  child is a grandchild. A known child is never re-parented and an update naming the root, or the session it arrives
  on, is ignored, each with a WARNING. [run: tests]
- **Merge.** Design §4.3's table: omitted keeps, `null` clears, a value replaces; `capabilities` grants iff `cancel`
  is an object; `parent_tool_call_id` is lifted from `_meta.openhands.parentToolCallId` and is sticky. `title`,
  `description`, `meta` and all stored text pass through the bridge's secret masking. [run: the ten-case
  parametrized test; masking of a title and of child text by a probe, §4.3]
- **Segments.** Consecutive text chunks of one kind in one child form one run; chunks of one `messageId` form one
  message; anything else for that session flushes first, usage never does; a `subagent_update` flushes the parent's
  segment, then the child's, then stores the snapshot. [run: tests]
- **Cost.** A child's `usage_update` sets `cost`/`cost_currency` (`None` when omitted) and stores a snapshot only on
  change; `size` and `used` are not kept, and the root's usage sync, context window and metrics never see a child's
  update. [run: tests]
- **Replay.** While `replaying`, nothing is returned and only unknown children are registered (parent only). [run:
  unit test]
- **Grants.** `check_cancel` raises `NotCancellable` for the root, `NotFound` for an unknown id, `NotCancellable`
  without a grant received live on this connection. [run: tests]

### 4.3 The bridge, `acp_agent.py`: where the complexity sits

+287 −40 lines spread through `acp_agent.py` (5,277 lines at `0cfb6a2`), the file upstream changes most. [run:
`wc`, `git diff --numstat`]

- **Diversion** (`:1740–1748`). After S2's controls recorder and the `ask_agent` fork branch, `_child_session`
  returns the id of a known child, else `None` (warning once for an id that is neither root nor child). With the
  opt-in on, every update except a usage update or a child's text chunk first flushes its session's segment; a child's
  text and usage go to the router, its plans and other updates are dropped with a DEBUG line, and its tool calls fall
  through.
- **The shared tool-call path.** Entries carry `acp_session_id` and (opt-in on) `meta`, are masked, and are matched
  by `(tool_call_id, acp_session_id)`; `_emit_tool_call_event` sends a child's call to the emitter and a root call to
  the turn's `on_event`, which is unset between turns, as before. [run: tests]
- **Three close-outs.** `reset()` keeps child entries that are not terminal, so a child's cell can outlive the turn;
  the successful turn's force-complete skips child entries ("a sub-agent's open call is its agent's to close",
  `:3865`); an aborted turn's `_cancel_inflight_tool_calls` emits a synthetic `failed` for every open entry, child
  entries through the emitter so they follow the call's own `started` event (`:3812–3848`). [run: tests]
- **Turn end.** `_do_acp_prompt`, on the ACP loop, submits every open segment after the usage wait (`:4081`), on
  both the `run()` and the `arun()` path. [run: a probe transcript whose child's last update before the prompt
  response is a thought: it is stored as one `ACPSessionTextEvent` after the turn, and a secret registered on the
  conversation reads `<secret-hidden>` in that text and in the child's stored title. CI's coverage does not reach this
  path, §7.1]
- **Connection start.** `_launch_acp_session` builds the bridge with `subagents=self.acp_subagents`, hands it the
  conversation's emitter, seeds the router from `state.events` and submits the reset snapshots, all before the
  subprocess starts; then the shim connection, the `initialize` with the capability, and `_load_session`, which sets
  `replaying` around `session/load`. [read; seed run in tests]

### 4.4 Threads, order and what the store holds

The portal (ACP loop) thread only submits child events; S2's single worker stores them under the state lock. Root
events keep the turn's synchronous path. Measured with the scripted agent (`--subagents --cancel-wait 2`, sampling
the store every 0.1 s): under a synchronous `run()`, which holds the lock for the whole step, none of the 9 child
snapshots is stored before the turn's `FinishAction`; under `arun()`, 8 of 9 are stored while the turn is still
running. [run: probe] So in the log, children follow the root's events of the same turn under `run()`, and
interleave under `arun()` only when the turn lasts long enough; within one child the order is always wire order.

The log of one `--subagents` turn under `run()`, as stored (`ACPSessionControlsEvent`s are S2's) [run: probe]:

```text
 0–2   MessageEvent (user), SystemPromptEvent, ACPSessionControlsEvent
 3–4   ACPToolCallEvent        root        cell-1 in_progress, then completed
 5–7   ActionEvent FinishAction, ObservationEvent, ACPSessionControlsEvent
 8     ACPSubagentEvent        child-a     running, parent root, in cell-1, cancellable
 9     ACPSessionMessageEvent  root        root → child-a   'Summarize part A.'
10     ACPSessionTextEvent     child-a     thought          'Reading part A.'   (two chunks, one run)
11     ACPToolCallEvent        child-a     cell-a1 in_progress
12–14  child-a-1: running (in cell-a1); message child-a-1 → child-a 'Part A checks out.' (two chunks); idle end_turn
15     ACPToolCallEvent        child-a     cell-a1 completed
16     ACPSubagentEvent        child-a     running, cost 0.0004 USD
17     ACPSessionMessageEvent  child-a     child-a → root   'Part A: fine.'
18     ACPSubagentEvent        child-a     idle end_turn, cost 0.0004 USD
19–22  child-c: running (not cancellable); cell-c1 in_progress, completed; idle end_turn
23–26  child-b: running; cell-b1 in_progress, completed; idle end_turn
```

Each event's timestamp is taken when the portal thread creates it, so per child the timestamps never decrease in log
order, a reconnect snapshot is later than every earlier event of its child, and a spawning cell's `started` event is
earlier than its whole subtree. [run: the three ordering tests; REST order also in the cross test]

### 4.5 Edges observed

Behaviour as built that no test pins. [run: probes, unless marked]

- **A child call open across aborted turns is failed once per turn.** Each aborted turn's close-out emits another
  synthetic `failed` for a child entry that stays open (the entry is not marked terminal), and a later report from
  the agent still lands: stored sequence `in_progress, failed, failed, completed` over two aborted turns. Design §4.4
  includes child entries in an aborted turn's close-out and does not say what happens to one that stays open across
  turns.
- **A replayed open child call can reach the store.** A child `tool_call` replayed during `session/load` and left
  open is not stored, but stays in the bridge's accumulator; the next aborted turn stores a synthetic `failed` for
  it.
- **The grant outlives idle.** An agent that keeps `capabilities.cancel` on an idle child (the scripted agent and,
  per design §10, dr-acp) keeps it cancellable on the live connection: a second cancel after `child-b` turned idle
  answered without error, three trials out of three.
- **Unstable updates on an unannounced, non-root session are not sent to the root path.** A `session_message` there
  is stored under that session's id, and a child announced there gets it as its parent ("could not be placed" for
  C1). [read]
- **The Python `RemoteEventsList` cache** merges an ACP call's two events in place, so its order can differ from the
  server's log when child traffic interleaves; the cross test checks order on the REST log. [read: PR #2's notes, the
  cross test's comment]

---

## 5 · What each consumer relies on

**C1 (Canvas fork; designed at `design/c1` `88f5c43`, not built).** C1 reads stored events only, through design §5
(tree by latest snapshot, placement by `parent_tool_call_id` then first message then position, per-session
transcripts keyed `(acp_session_id, …)`, state, cost never added, Stop only for `cancellable` and `running` or
`requires_action`, `source == "environment"` as unconfirmed history). As built, the stored shapes and rules hold
[run: `tree_from` in the E5 tests implements exactly these rules over stored events, §7.2]. C1 also relies on: the
three ordering facts of §4.4 (its decision C orders by timestamp) [run]; storage with `exclude_none`, so unset
fields arrive as absent keys [run: the dump test; read: `event_store.py:225`]; the 409 `detail` text, shown
verbatim [run]; `cancelAcpSession`, the three types and guards, and `ACP_SETTINGS_KEYS` with `acp_subagents` in the
TypeScript client [run]; the profile field (D-2) for its launches
[run]; and the scripted agent by path from a fork checkout, with `--subagents --cancel-wait N`, `--transcript` and
`--transcript-interval-ms` [run]. Of C1's four asks (§9.1): items 1, 2 and 4 are built (D-2, D-6, D-1), item 3 is
built as tests but not written into S1's design §5 (D-10); item 1's persisted-profile fixture is not built.

**D1's `dr-acp`.** S1 relies on design §10's seven points of D1's contract: each child announced on its parent's
session before its traffic, with `_meta.openhands.parentToolCallId` naming a cell already sent (ids `<run>-n<node>`,
cells `<run>-n<node>-c<k>`, path-safe); `capabilities.cancel` on every child; reasoning and the Stop acknowledgement as
`agent_thought_chunk`s on the child's session (stored as `ACPSessionTextEvent`); goldens replayable as they are; no
child traffic after the prompt response. All nine native goldens replay through the bridge into the recorded tree
[run: §7.3], and the live tier passes on dr-acp [CI: §7.4]. D1 in turn relies on S1 putting `subagents` on the wire
as an object (D1 turns native mode on iff `clientCapabilities.subagents` is an object, read from D1's as-built §3)
[run: `test_initialize_puts_subagents_capability_on_the_wire`] and on `session/cancel` carrying the full child id [run: the
scripted agent's request log; CI: the live stop test]. The compatibility fact underneath: agent-client-protocol
0.12.1 rejects the unstable types and marks `ClientSideConnection` `@final`, so the shim subclasses it with one
suppression [run: the tripwires; read: `acp/client/connection.py:109`].

**D5 (desktop app; designed at `design/d5` `8086afb`).** D5 turns sub-agent sessions on for `deep_reasoner`; they
are off by default [run: `test_acp_create_agent_forwards_subagents`]. It relies on: `acp_subagents` on the agent
profile it owns, through the resolver and back through the seed (D-2), with a 422 fallback on servers without it
[run: resolver tests; the fallback is D5's]; the scripted agent's `--transcript` mode for E5's `bridge-replay` job
against D1's goldens [run: §7.3, with my own comparator, not D5's `testing.tree()`]; and S1's live file with its two
variables, which D5 §7.4's `fork-live.yml` runs [CI: §7.4]. D5's persisted-profile fixture ask (§8.2) is not built.

**S2.** Shares the emitter, the scripted agent and `acp_router.py`, all S2's (D-4). S2's controls recorder stays
first in `session_update`, so commands and options never reach S1's diversion. [read]

---

## 6 · Wiring

**PR #2** (draft, `feat/acp-subagent-sessions` → `feat/agent-surfaces`, 5 commits, +4,030 −56 in 42 files): 16
checks at `0cfb6a2`, 15 green and `Validate PR description` skipped: `Run tests` (run 37105068562: `sdk-tests`,
`agent-server-tests`, `cross-tests`, `tools-tests`, `workspace-tests`, `windows-tests`, `macos-app-backend-tests`,
`agent-server-stress-tests`, `acp-live-tests`, `Test directory allowlist`, `coverage-report`), `pre-commit` (ruff,
pycodestyle, pyright, the forbidden-dynamic-attribute, import-rule and tool-registration checks), `endpoint-audit`,
`check-docstrings`, `Deprecation deadlines`. The persisted-settings, REST-breakage and TypeScript-client workflows do
not run on it (D-5). [CI]

**The live workflow** is deep-reasoning's `.github/workflows/fork-live.yml` on branch `ci/fork-live` (`a8154e2`,
one commit on D1's `c8d7fbb`): `workflow_dispatch` with `sdk_ref`, `suites`, `sdk_repo`, `live_config`; it checks out
both repositories, installs deep-reasoning with `uv sync --locked` (deep_reasoner at `d7334ae` through a read
token) and the fork with `uv sync --frozen --group dev`, then runs `pytest -m acp_live
tests/sdk/agent/test_acp_subagents_live.py` with `OPENHANDS_ACP_LIVE_AGENT_COMMAND="<dr-acp> --config
docs/configs/advising/main.yaml --home <temp>"` and `OPENHANDS_ACP_LIVE_SUBAGENTS_PROMPT="/compare-departments Which
department is lighter for a first-year student, CS or STAT?"`, then S2's file. [read; CI]

---

## 7 · Experiments and tests, as measured

### 7.1 The runs

| Run | Commit | Conditions | Result |
|---|---|---|---|
| CI `Run tests` [37105068562](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37105068562) | `0cfb6a2` | `pull_request`, ubuntu, uv 0.12.22 | `sdk-tests` **6,773 passed**, 7 skipped, 12 xfailed, 159.5 s; `agent-server-tests` **2,435 passed**, 415.7 s; `cross-tests` **497 passed**, 1 skipped (`test_security_risk_field_with_live_server`), 157.3 s; `acp-live-tests` 25 passed, 4 skipped, S1's two among the skipped [CI] |
| coverage in `sdk-tests` | `0cfb6a2` | as above | `acp_subagents.py` 96% (uncovered 157, 166, 176, 191, 211, 227, 325: message `_meta`, three replay early-returns, non-text blocks, the turn-end `flush_all` body), `acp_unstable.py` 96% (228–229, 243, 245), `event/acp_subagent.py` 93%; `acp_router.py` 99% in `agent-server-tests` [CI] |
| live [37141960911](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37141960911), job 111258092968 | SDK `0cfb6a2`, deep-reasoning `a8154e2` | ubuntu, Python 3.12.3, uv 0.12.23, dr-acp on gpt-6-luna | **2 passed** in 33.55 s (§7.4) [CI] |
| here: S1's SDK files | `0cfb6a2` | 4 CPUs, serial | `test_acp_unstable.py`, `test_acp_subagents.py`, `test_acp_subagent_events.py`: **68 passed**, 26.4 s; three repeats of the first two **58 passed** each; with `-n 4` plus `test_acp_router.py` **90 passed** [run] |
| here: the other files S1 touches | `0cfb6a2` | serial | `test_acp_router.py`, the event-service class, the cross test, resume transcript, dedup, settings, resolver: **307 passed**, 2 deselected (the live file), 51.7 s; the live file under `-m acp_live` without its variables: 2 skipped [run] |
| here: TypeScript client | `0cfb6a2` | `git archive` copy, Node 22.22 | S1's three files **140 passed**; full suite **23 files, 361 passed**; lint 0 errors, 7 warnings; public type budget unchanged at 106 sites [run] |

I did not run the full Python suite here; CI's is the record (the brief's known local wsproto errors were not met).
Reproduce: `OPENHANDS_SUPPRESS_BANNER=1 uvx uv@latest run --frozen pytest tests/sdk/agent/test_acp_subagents.py
tests/sdk/agent/test_acp_unstable.py tests/sdk/event/test_acp_subagent_events.py tests/agent_server/test_acp_router.py`.

### 7.2 E5 in the fork (the agent-server half)

A real `LocalConversation` with `ACPAgent(acp_command=[python, scripted_agent.py, …], acp_subagents=True)`, no
network. The baseline for each arm is the scripted or recorded wire stream itself. All passed here [run], and their
CI jobs (`sdk-tests`, `agent-server-tests`, `cross-tests`) finished with no failure [CI; §9 item 2].

| Test | What it asserts | Result |
|---|---|---|
| `test_scripted_run_stores_the_scripted_tree` | the tree rebuilt from stored events by design §5's rules equals the scripted one: `child-a` (cost 0.0004 USD, `cell-a1`, its task and answer, one thought run), grandchild `child-a-1` placed in `cell-a1` with its two-chunk answer, `child-c` not cancellable, `child-b`; every child placed by cell | passed |
| `test_scripted_run_keeps_child_text_out_of_the_answer` | the `FinishAction` message is the root's reply alone | passed |
| `test_scripted_run_books_only_the_roots_cost` | the conversation's cost is 0.0011, not 0.0015 | passed |
| `test_scripted_run_with_subagents_off_stores_only_root_work[--subagents, --transcript]` | off: only `cell-1`, no new kinds, no `acp_session_id`, `initialize` without `subagents` | passed ×2 |
| `test_subagents_off_uses_the_stock_connection_and_initialize` | off: the connection is exactly `ClientSideConnection`; `initialize`'s params equal the library's own serialization | passed |
| `test_cancel_acp_session_reaches_the_child_and_its_cancelled_state_is_stored` | `--cancel-wait 30`, `run()` in a thread: the request log holds `session/cancel {sessionId: child-b}`; `cell-b1` stored `failed`, `child-b` idle `cancelled` | passed |
| `test_cancel_acp_session_does_not_wait_for_the_state_lock` | the successful call began while the run held the state lock; the run finishes | passed |
| `test_cancel_acp_session_refuses_a_child_without_a_grant` · `…_unknown_and_root_sessions` · `…_without_a_live_connection_is_refused` | `child-c` 409-class and no `session/cancel` sent; unknown 404-class, root 409-class; before the first run 409-class | passed |
| `test_scripted_transcript_replays_a_recording[full, outgoing-only]` | a recorded turn with two children replays into its tree, from a full recording and from the agent's lines only | passed ×2 |
| `test_transcript_interval_paces_the_replay` · `test_transcript_wait_point_that_is_never_reached_exits_non_zero` | pacing ≥ 50 ms per update; a missed wait point exits non-zero | passed |
| three ordering tests (D-10) | §4.4's three facts | passed |
| `test_stored_sub_agent_events_validate_against_the_event_schema` (agent-server) | every stored event of a sub-agent run, read over REST, validates against the public `Event` schema | passed |
| `test_acp_subagent_sessions_over_live_server` (cross) | a real server and WebSocket: cancel `child-b` through the route, every sub-agent event reaches the WebSocket client, order and timestamps on the REST log | passed |

Measured beside them [run: probe, three trials, scripted agent, `run()` holding the state lock]: the cancel call
returned in 14.7, 3.3 and 2.4 ms; the run ended 1.07, 1.09 and 1.04 s later with `child-b` idle `cancelled`.

### 7.3 D1's golden recordings through the bridge (a preview of E5's second half)

An uncommitted probe replays each of D1's nine `tests/acp/golden/*.native.jsonl` (deep-reasoning `c8d7fbb`, D1's
golden set; agent-outgoing lines only) through `--transcript` into a `LocalConversation` with `acp_subagents=True`,
one message per recorded prompt, and compares the stored tree with the tree read straight from the recording
(each child's parent session and `parentToolCallId`, the tool call ids per session, each child's final state and stop
reason). [run]

| Recording | Children | Tree, calls, final states equal | Child text runs (recorded chunks) | Time |
|---|---|---|---|---|
| `claude`, `linear` (2 prompts) | 0 | yes | 0 | 1.3 s, 3.9 s |
| `depth3`, `fanout2`, `fork` | 2 each | yes | 0, 1 (1), 0 | 1.7–2.0 s |
| `exhausted`, `failing`, `namespace` | 1 each | yes | 0 | 1.6–2.0 s |
| `fanout20` | 20 | yes | 0 | 3.5 s |

9 of 9 equal. The comparator is mine, not D1's `testing.tree()`, which D5 §7.5 names for this job; costs are not
compared (D1's goldens keep only each session's last `usage_update`).

### 7.4 The live tier (dr-acp on gpt-6-luna)

Run 37141960911 [CI], `-m acp_live tests/sdk/agent/test_acp_subagents_live.py -v -rA`, 2 passed in 33.55 s:

| Test | Asserts | Result |
|---|---|---|
| `test_live_agent_tree_is_well_formed` | `run()` on the CS-vs-STAT prompt; within 30 s no child is `running`; at least one grandchild; every child's parent is the root or a stored child; every set `parent_tool_call_id` names a stored call of its parent; no child text run of ≥ 40 characters appears in the answer; the conversation's cost equals the root's last reported cost | passed; prompt returned in 18.1 s |
| `test_live_agent_stops_one_subagent_and_its_branch` | `arun()` under a 120 s limit, watched by a conversation callback; on the first announcement of a grandchild whose parent is `running` and `cancellable`, `cancel_acp_session(parent)` from a new thread; then that child and all its descendants are stored idle `cancelled` within 30 s, and no non-terminal tool call of the branch is stored after the branch root's `cancelled` snapshot | passed; prompt returned in 10.8 s |

The run's spend is not printed. [CI]

### 7.5 The other tests S1 adds

- **Shim** (`test_acp_unstable.py`, 10): two tripwires; the capability on the wire and the library call without it;
  nine interleaved stable and unstable updates in wire order; a stable update on a child id still parsed by the
  library; a malformed update dropped with one WARNING; omitted versus `null`; a custom state kept; non-text blocks
  kept typed. Over a real agent-side `Connection` on a socket pair. [run]
- **Router and bridge units** (`test_acp_subagents.py`, 21 names, 30 cases with the ten-case merge test): design
  §7.2's unit list, each by its name; its 22nd name, the stock-connection test, runs a conversation and is in §7.2's
  table. [run]
- **Events** (`test_acp_subagent_events.py`, 10): JSON round trip of the four kinds; a legacy `ACPToolCallEvent` loads;
  a root call dumps with no new keys; visualization. [run]
- **Consumers**: resume transcript skips child calls; `RemoteEventsList` merges child and root calls separately;
  `create_agent` forwards the opt-in; the profile resolver and seed (3). [run]
- **Route** (`test_acp_router.py`, 7): 200 then idle `cancelled` stored; unknown conversation 404; unknown session 404
  with its `detail`; `child-c` 409 with its `detail`; non-ACP 400; a cancel that never writes, 504 at a 0.2 s
  timeout; the schema test. **Service** (2): runs off the event loop; inactive refused. [run]
- **TypeScript** (6): `cancelAcpSession` posts, encodes the id, and posts for its conversation; the opt-in survives
  the settings filter; stored-event shapes type-check; each guard matches only its kind. [run]

### 7.6 Upstream guards, run here

| Guard | Result |
|---|---|
| persisted settings (`check_persisted_settings_compat.py`) | 18 fixtures validated (the new v7 one among them), 8 PyPI baseline payloads from 1.50.1 validated [run] |
| OpenAPI weak-schema ratchet on the exported schema | fails at S1's head and at S2's head `6f97bf3` alike, on one pointer outside S1 (`/api/canvas-extensions/installed/{extension_name}/panels/{panel_id}/icon` response, `empty-object-schema`); no S1 location is reported, so the three `meta` entries suffice [run] |
| REST breakage: oasdiff 1.19.1, S2's export → S1's | 2 ERR-level changes, both `response-property-one-of-added` / `response-body-one-of-added` for the three kinds in the `Event` union, the two rule ids `check_agent_server_rest_api_breakage.py` treats as additive (`:571–578`); 15 info (the new endpoint, optional properties). I did not run the script itself. [run] |
| TypeScript lint, suite, public type budget | §7.1 [run]; endpoint audit green in CI [CI] |
| pre-commit (ruff, pycodestyle, pyright, the repository's checks) | green in CI [CI]; not run here |
| SDK API breakage (Griffe against PyPI) | not run: it compares the whole branch, S2 and the fork base included, with the last release |

---

## 8 · Size, and what resisted compression

S1 is +1,205 −49 lines of Python product code, +112 −2 of TypeScript, and +2,666 of tests and fixtures (D-13). The
part of this document that will not get shorter is §2: the design was written before S2 landed and before C1's and
D5's asks, so the build's differences are many and mostly small, and each changes a sentence C1, D5 or S2 may have
read in the design.

---

## 9 · What I could not verify

1. **The live tier and its cost**: not run here; results are GitHub's log [CI]. No amount is printed, so the cost per
   live run is unknown.
2. **Each S1 test's line in CI.** The GitHub tools return at most the last 5,000 lines of a job log, and full log
   downloads are blocked here. `sdk-tests` (20,205 lines), `agent-server-tests` (9,898) and `cross-tests` (10,311)
   were read from their tails only: I saw their totals and coverage tables, not each S1 test's result line, so "passed
   in CI" for an individual test rests on the job's total having no failure.
3. **A real `session/load` replay.** The `replaying` flag is exercised by unit tests that set it directly; no test or
   probe drives a session/load whose agent replays sub-agent traffic (the scripted agent's transcript mode refuses
   `session/load`, and the reconnect test falls back to `session/new`). The restart path of design §2 is read, except
   the seed, which is run.
4. **Upstream guards on `main`**: whether each of the five commits is green on its own and cherry-picks cleanly onto
   the fork's `main`, the REST-breakage script itself, and the SDK API breakage check (D-5, §7.6).
5. **pyright on the shim**: green in CI's pre-commit [CI]; not run here.
6. **Paths read but not seen run**: a notification without `sessionId` dropped by the shim; a `session_message`'s
   `_meta` and non-text blocks; the 504 against a real stalled agent (tested by patching `cancel` to sleep); the
   Python `RemoteEventsList` reordering (§4.5); unstable updates on an unannounced session (§4.5); masking of `meta`.
7. **The opt-in from a profile through a real agent-server launch**: the resolver and seed are unit-tested; no run
   started a conversation from a profile with `acp_subagents` and saw child events stored.
8. **Canvas** (C1) is not built, so nothing renders S1's events yet; §5's C1 paragraph checks the stored shapes
   against C1's design, not against Canvas code.
