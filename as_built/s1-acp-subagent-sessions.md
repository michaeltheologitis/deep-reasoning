# S1 · ACP sub-agent sessions in the agent-server, as built

**TASK-3** · Cartographer · **r4**, 2026-10-04 · the code at `6a05b13`, head of
`feat/acp-subagent-sessions-07-transcript-player`, the top of S1's stack of seven draft PRs #10–#16 in the SDK fork
[michaeltheologitis/software-agent-sdk](https://github.com/michaeltheologitis/software-agent-sdk); #10's base is
`deep-reasoning` at `9277e71`, where S2 is merged; S1's own diff is `9277e71..6a05b13` · checked against the design
at `e05986f` (`docs/design/s1-acp-subagent-sessions.md` v2.2, on this branch) · agent-client-protocol 0.12.1 (the
fork's lock), pydantic 2.12.5 · uv 0.12.23 (`uvx uv@latest`), Python 3.13.14 in this sandbox.

**This revision** (r4) describes S1's PR stack as it stands, for Gate C. The stack replaced draft PR #2
(`feat/acp-subagent-sessions` at `2675399`), closed unmerged at 03:47 UTC with a comment naming #10–#16 [CI]. Its
first top commit, `d766bd7`, has `2675399`'s tree exactly; `6a05b13`'s tree differs from `2675399`'s by exactly three
test files and no source file [run: `git diff --stat 2675399 6a05b13`]:

| File | Change | What |
|---|---|---|
| `tests/sdk/agent/test_acp_subagents.py` | +28 −3 | the `[--transcript]` case of the opt-off test (`306731d`, P4); `test_transcript_exits_non_zero_when_a_wait_point_outlasts_the_wait_timeout` (`6a05b13`, P6′) |
| `tests/sdk/agent/test_acp_unstable.py` | +16 −1 | `test_session_message_with_a_non_text_block_reaches_the_callback_whole` (`049ceb5`, P7) |
| `tests/sdk/conversation/local/test_local_conversation_acp_config_option.py` | +6 −4 | S2's agent-swap test race fix (`2f7642c` on level 01, a cherry-pick of `90e99f6`, fork PR #17, merged into `deep-reasoning` as `9277e71`) |

So every source claim and source line number of r3 holds at `6a05b13`, and r3's runs that exercise the source only
(the wire probe, the state probe, D1's recordings, the OpenAPI export, the ratchet) were not repeated: the source, the
scripted agent and `tests/conftest.py` are byte-identical [run: `git diff`]. r4 changes §1's counts, V-7 to V-10, §6
(the proof, now the stack's CI), §7.1–7.3, §8's probes, §9 and §10. r3 (`1b0b7c3`) read `2675399`; r2 read
`a3279be`; r1 read `0cfb6a2`. Every count, test line number and run is `6a05b13`'s unless it says otherwise.

**Where this file lives.** deep-reasoning's branch `as-built/s1-r4`, cut from `design/s1` at `1b0b7c3`; the
Conductor merges it into `design/s1`. The branch has no `pyproject.toml`, docs site or test runner, so nothing
collects `as_built/` and there is nothing to wire. [run: `git ls-tree -r HEAD`]

**Evidence marks.** Every claim carries one.
- **[run]**: executed here, without writing a tracked file in either checkout. r4: S1's test files at `6a05b13` in a
  detached worktree (removed after); six mutation probes, one temporary edit each, reverted, the tree clean after
  each (§8); two uncommitted probe scripts in my scratchpad (an opt-off conversation's store and log under P4's
  unstable half; the transcript player run directly under P6). r3's runs at `2675399` and `a3279be` are marked "(r3)"
  where they are cited. No model calls; network only for GitHub.
- **[CI]**: GitHub's records through the MCP tools: the checks of PRs #10–#16 at their heads, with the full logs of
  each `sdk-tests`, `cross-tests`, `agent-server-tests` and `acp-live-tests` job that ran tests and of `test (22.12)`
  at #15 and #16 (downloaded through signed URLs); PR #2's and #17's records; and the live run
  [37171079147](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37171079147), at `2675399`.
- **[read]**: read in the code, **not executed**. §10 lists the read claims that matter.

**Reading order.** §2, then §8, then §6 for the proof; §1, §3 and §4 as the map; §7 for the measurements; §10 for
what I could not verify.

---

## 1 · What exists

With `acp_subagents` on, the bridge connects through the shim's connection class, which advertises
`clientCapabilities.subagents` and takes ACP's three unstable updates ahead of agent-client-protocol's router; the
bridge routes every update by session and stores each announced child (its association with its parent, its tool
calls, the messages between sessions, its own text, its cost) through the conversation's out-of-turn emitter, which
S2 built. A REST route cancels one child that holds a live `cancel` grant. With the opt-in off the connection class,
the `initialize` call, the routing and the stored events are the stock ones. [read; each part run in §7]

```text
ACP agent ── stdout ──▶ _filter_jsonrpc_lines (unchanged)
   ▼
SubagentClientSideConnection (acp_unstable.py; opt-in on)        stock ClientSideConnection (opt-in off)
   │ session/update whose sessionUpdate ∈ {subagent_update, session_message, session_message_chunk}
   │    → one TypeAdapter → bridge.unstable_session_update(sessionId, update)   (acp_agent.py:1602), synchronously
   │ every other message → the library's router → bridge.session_update          (:1725), as before
   ▼
session_update: S2's controls recorder (:1738) → ask_agent fork session (:1745) → _child_session (:1753)
   ├ root, or a session never announced → the stock path: answer text, thoughts, tool calls, usage → turn's on_event
   └ announced child → ACPSubagentSessions (acp_subagents.py): text runs, usage → cost
                       its tool calls take the shared tool-call path, keyed (session, toolCallId)
child events ─▶ bridge.on_session_event = ACPAgent._on_session_event = LocalConversation._emit_event_from_any_thread
                (S2's: one worker thread, first in first out, takes the state lock, calls _on_event)
   ▼
ConversationState.events ── /events/search, WebSocket ── TypeScript client ── Canvas (C1)

cancel: POST /api/conversations/{id}/acp/sessions/{session_id}/cancel (acp_router.py:175–224, S2's module)
        → EventService.cancel_acp_session (event_service.py:2043, default executor)
        → LocalConversation.cancel_acp_session (local_conversation.py:1832, no lock)
        → ACPAgent.cancel_acp_session (:5036) → run_async(_acancel_acp_session (:5065), timeout=2.0) on the ACP loop
        → check_cancel(session_id) → session/cancel {sessionId}; the outcome arrives as the child's own update
```

| Part | before: `5e3317f..a3279be` | r3: `d938c90..2675399` | now: `9277e71..6a05b13` | Where |
|---|---|---|---|---|
| the shim | 247 | 222 | the same | `openhands-sdk/openhands/sdk/agent/acp_unstable.py` |
| the router | 338 | 299 | the same | `openhands-sdk/openhands/sdk/agent/acp_subagents.py` |
| bridge and agent | +317 −40 | +294 −43 | the same | `openhands-sdk/openhands/sdk/agent/acp_agent.py` (5,253 lines) |
| events | +177 | +175 | the same | `event/acp_subagent.py` (158), `event/acp_tool_call.py`, `event/__init__.py` |
| other SDK consumers | +79 −8 | +76 −8 | the same | local and remote conversation, visualizer, resume transcript, settings, three profile files |
| agent-server | +77 −1 | +77 −1 | the same | `acp_router.py`, `event_service.py` |
| TypeScript client | +112 −2, +27 config | the same | the same | `clients/typescript/src/…`, `endpoint-audit.config.json`, `config/public-type-budget.json` |
| CI config | +20 | +20 | the same | weak-schema allowlist (+18), `.github/workflows/tests.yml` (+2) |
| **source** | **+1,394 −51** | **+1,302 −54** | **+1,302 −54** | |
| Python tests | +2,149 | +1,806 −4 | +1,846 −4 | `tests/…`, with `tests/conftest.py` (+11 −4) |
| scripted agent | +459 −4 | +442 −4 | the same | `tests/fixtures/acp/scripted_agent.py` (748 lines) |
| persisted baselines | +27 | +27 | the same | `v7/agent_settings_acp_subagents.json`, `v2/agent_profile_acp_subagents.json` |
| TypeScript tests | +126 | +113 | the same | `clients/typescript/src/__tests__/…` |
| **tests** | **+2,761 −5** | **+2,388 −9** | **+2,428 −9** | |

Total +3,730 −63 in 43 files (r3 +3,690 −63; before +4,155 −56). Tests are `tests/**` and `__tests__/**`. `9277e71`
is `d938c90`'s tree plus the swap fix that `6a05b13` also carries, so that file is not in S1's diff. [run: `git diff
--numstat`; `git diff d938c90 5e58984` is empty]

**The stack**, bottom up, one feature commit per level; each later change on a level is merged into every level
above it ("Merge …: the agent-swap test race fix (PR #17)", "…: the non-text session_message pin") [run: `git log
--first-parent`]:

| PR | Level | Feature commit | Later commits on the level | Head |
|---|---|---|---|---|
| #10 | `01-unstable-shim` | `ee1f5c9` | `2f7642c` (the swap fix), `049ceb5` (P7) | `049ceb5` |
| #11 | `02-subagent-events` | `5c44da4` | two merges | `3ba31ae` |
| #12 | `03-bridge-routing` | `939ad06` | two merges | `eab2eb8` |
| #13 | `04-settings-opt-in` | `9acdb91` | two merges | `1c72537` |
| #14 | `05-cancel-route` | `dac153c` | two merges | `6481bcf` |
| #15 | `06-typescript-client` | `0cf32da` | two merges | `ba8f89c` |
| #16 | `07-transcript-player` | `d766bd7` | two merges, `306731d` (P4), `6a05b13` (P6′) | `6a05b13` |

Tests: **78** deterministic Python cases, 2 live (`acp_live`), 5 TypeScript (r3: 75, 2 and 5; v2.2: 88, 2 and 6).
[run: collected; TS read and CI]

---

## 2 · Divergences from the design (v2.2)

The changelog holds no `drift:` line for TASK-3 [run: Notion query of the Changelog's six newest entries, 2026-10-04,
after S2's and D2's merges]. V-2 to V-10 come from the refactor, each with the commit that says why; r4 revises V-7
to V-10 for the restored tests.

**V-1 · E-4's warning, one per session per path (r2's; holds, renamed).** v2.2's Gate B section and §5.1's E-4 note
say one warning per unannounced session. Built: one per session **per path**: one helper,
`_warn_unannounced(session_id, routing)` (`acp_agent.py:1678–1687`), remembers `(session, routing)` pairs in
`_warned_unannounced: set[tuple[str, str]]` (`:1455`), so a session that sends both stable and unstable updates draws
two WARNINGs, each naming it by `_fingerprint_session_id`. v2.2's §3.2 E-4 note, §4.4 note and A.3 name
`_unannounced_sessions`, `_unannounced_unstable_sessions` and `_warn_once_for_unannounced_unstable_traffic`; none
exists. The text is unchanged. *Why:* `73e47f8`. [run: both unannounced-session tests; read]

**V-2 · The sub-agent connection always advertises `subagents`.** v2.2 §4.2 and A.1: `initialize` sends a standalone
`_SubagentInitializeRequest(ACPModel)` only when given a `SubagentClientCapabilities`, else `super().initialize`;
§4.4: the bridge passes `SUBAGENT_CLIENT_CAPABILITIES` when on. Built: `SubagentClientSideConnection.initialize`
(`acp_unstable.py:158–177`) always sends through `request_model` with `client_capabilities or
SUBAGENT_CLIENT_CAPABILITIES`, as `_SubagentInitializeRequest(InitializeRequest)` (`:129–134`), whose
`client_capabilities` is `SerializeAsAny[ClientCapabilities] | None`; the bridge has one call for both connection
classes, `conn.initialize(protocol_version=1)` (`acp_agent.py:3478`). The wire is unchanged: the `--subagents` run's
`initialize` is `{"protocolVersion": 1, "clientCapabilities": {"auth": {}, "subagents": {}}}` at `a3279be` and at
`2675399`, and `{"protocolVersion": 1}` at both with the opt-in off [run (r3): wire probe]. The branch for explicit
capabilities has no caller in the SDK and no test [read]. *Why:* `bf57a3a`.

**V-3 · `SubagentState` keeps no extra keys.** v2.2 §4.2 ("anything else kept"), A.1 (`extra="allow"`), §7.1
(`test_custom_state_is_kept_whole`: "keeps its state and its extra key"). Built: `SubagentState`
(`acp_unstable.py:68–73`) has the library's base config, which ignores unknown keys; a custom state's name is kept
(the merge test's `state-custom` case). Fed two `subagent_update`s whose states carry `x`, `progress`, `_meta` and
`extra`, the bridge stores identical `ACPSubagentEvent`s at `a3279be` and `2675399`, and none holds those keys [run (r3):
state probe]. *Why:* `6b089e5` (nothing read them).

**V-4 · The router holds each child as its latest `ACPSubagentEvent`.** v2.2 §4.3's state table and A.2:
`_children: dict[str, _Association]`, a dataclass with `cancel_granted`. Built: `_children: dict[str,
ACPSubagentEvent]` (`acp_subagents.py:76`), whose `cancellable` is the live grant; a merge or a cost change is a
`model_copy` (`:237`, `:189`); each stored snapshot is a new event built from the held one without `id`, `timestamp`
and `parent_id` (`_PER_EVENT_FIELDS`, `:35`; `_snapshot`, `:239–243`); `seed` holds each stored snapshot with
`state`, `stop_reason` and `cancellable` cleared (`:80–93`). Stored output is unchanged (§7.4). One property is new
and pinned: no snapshot carries a stored event's `parent_id` (probe P1, §8). *Why:* `a682f6a`.

**V-5 · The `session/load` replay is marked by a bridge context manager.** v2.2 §3.2 B7, §4.4's v2 table and A.3:
`ACPAgent._load_session(conn, client, session_id, working_dir, mcp_servers) -> LoadSessionResponse`. Built:
`_OpenHandsACPBridge.replaying(root_session_id)` (`acp_agent.py:1648–1662`), which with the opt-in on sets the root's
id and `replaying` and clears the flag in a `finally`, and with it off does nothing; the call site is upstream's
`conn.load_session(...)` under `with client.replaying(prior_session_id):` (`:3602–3607`). Unit tests enter it the
same way. *Why:* `fec0b95`. [read; run: P10]

**V-6 · Small signature and file differences.** None changes behaviour. [read]

| v2.2 | Built at `6a05b13` (as at `2675399`) |
|---|---|
| A.3: `unstable_session_update(session_id, update: SubagentUpdate \| SessionMessage \| SessionMessageChunk)` | `update: UnstableSessionUpdate`, the shim's alias for the same union (`acp_unstable.py:112`) |
| A.2: `before_update` "called before any update for it that is not a text chunk, a message chunk or a usage update" | "Flush `session_id`'s open segment, ahead of an update that ends it" (`acp_subagents.py:194–196`); the bridge flushes before every update but a usage update or a child's text chunk (`acp_agent.py:1754–1759`), so the root's own text ends the root's open chunked message, as §4.3's rule already says |
| A.7: S1's additions to the scripted agent | also eleven wire builders the two sub-agent test files import: `text`, `subagent`, `announce`, `idle`, `tool_call`, `tool_done`, `thought`, `said`, `usage`, `message`, `message_chunk` (`scripted_agent.py:305–386`; `d03ec2c`) |
| §4.1, §7.3, §9 row 15: S1's tests in new files and `test_acp_router.py`; `tests/sdk/test_settings.py` | S1 also edits `tests/conftest.py`: `subagent_snapshots`, and `wait_until` returns the value it waited for (`2fb47b2`); it no longer touches `tests/sdk/test_settings.py` |

**V-7 · The tests v2.2 names.** v2.2's Gate B table, §5.1's "Pinned by" lines and §7 name fifteen Python tests and
one TypeScript test that no longer exist under those names, and two under a class that are now module functions;
they count 88 deterministic Python cases (52 in `test_acp_subagents.py`) and 6 TypeScript. Built: 78 (48) and 5.
Three of the fifteen properties have a test again under a new name:
`test_session_message_with_a_non_text_block_reaches_the_callback_whole` (v2.2:
`test_message_content_keeps_non_text_blocks_typed`); the `[--transcript]` case of
`test_subagents_off_stores_only_root_work_through_the_stock_connection` (v2.2:
`test_scripted_run_with_subagents_off_stores_only_root_work[--transcript]`); and
`test_transcript_exits_non_zero_when_a_wait_point_outlasts_the_wait_timeout` (v2.2:
`test_transcript_wait_point_that_is_never_reached_exits_non_zero`). §8 lists each name and where its property went.
*Why:* `a910ac9`, `6dcde3e`, `ca39def`, `5b17efd`, `bf57a3a`, `6b089e5`; restored in `049ceb5`, `306731d`,
`6a05b13`. [run: collected]

**V-8 · What §5.1 calls pinned, against the tests.** r3 found three properties without a test; each has one again
[run: probes P4, P6′, P7, §8]: the transcript player's conformance rule for other sessions' updates (caught through
a child's tool call stored as root work), guarantee 9's wait timeout (the fixture row), and the parse of a
`session_message` with a non-text block. Still without a test:
- the rule's other half, that without `subagents` the player skips the three unstable updates. With the opt-in off,
  the stock connection drops each one after an ERROR log with a traceback, so the stored events are identical with
  and without that half (P4u) [run];
- guarantee 6: the route's 200 is reached only by the cross test (P9) [run in r3; the files are unchanged].

**V-9 · E5's tree reader places a child by its spawning cell only.** v2.2's Gate B table and §7.2: "Rebuilding the
tree from stored events with §5's rules". Built: `tree_from` (`test_acp_subagents.py:584–634`) keeps rule 2's first
placement; any other placement reads `("unplaced",)` and fails the comparison. Every expected tree places by cell,
so rule 2's fallbacks (first message, then position) are exercised by no test. *Why:* `a910ac9`. [read]

**V-10 · Size.** v2.2's Gate B section, B16 and §11 item 8: 4,155 added and 56 removed, about 14 h at Gate C. Built:
3,730 added and 63 removed (§1, §9), about 12.4 h at ≈300 lines an hour. As GitHub shows the stack, #10's diff also
carries the swap fix's +6 −4, because GitHub diffs from the merge base `5e58984` and level 01 carries the cherry-pick
`2f7642c`, not `90e99f6`. [run; CI: #10's file list]

**r1's divergences from v1 (D-1 to D-13, v2.2's B-entries) at `6a05b13`** (source identical to `2675399`, where r3
checked them). Unchanged in behaviour: D-1 (B3: after a reconnect an idle child whose last snapshot said
`cancellable: true` keeps it, while the route answers 409, ruled acceptable; `seed`, `acp_subagents.py:89–93`) [run:
`test_new_connection_withdraws_cancel_and_unconfirms_state`]; D-2 (the opt-in on the agent profile) [run]; D-3
(B4: no trace spans for a child's tool calls, `acp_agent.py:1803`, `:1863`, `:4199`; unpinned) [read]; D-4 to D-8,
D-11, D-12 [read]. Superseded: D-9 and D-10 by V-7, D-13 by V-10.
r2's small differences: one warn helper (V-1); the root id set in `replaying()` before `session/load` (V-5) and after
`session/new` (`:3659`); a notification without `sessionId` dropped by the shim (`acp_unstable.py:204–206`), still
untested [CI: uncovered]; `cancel_acp_session` with the opt-in off: 404 once a session is live, 409 before
(`acp_agent.py:5050–5053`) [read].

---

## 3 · The public surface, from the code

**The opt-in.** `ACPAgent.acp_subagents: bool = False` (`acp_agent.py:2217`); `ACPAgentSettings.acp_subagents`
(`settings/model.py:1751`), forwarded by `create_agent()` (`:1964`); `ACPAgentProfile.acp_subagents`
(`profiles/agent_profile.py:292`), forwarded by the resolver (`profiles/resolver.py:305`) and carried back by the seed
(`profiles/seed.py:58`). No `SETTINGS_METADATA_KEY`; `AGENT_SETTINGS_SCHEMA_VERSION` stays 7 and the profile schema 2,
with a baseline each. The field rides on the serialized agent. [read; run: resolver tests, persisted-settings check]

**Python calls.** `ACPAgent.cancel_acp_session(session_id) -> None` and `LocalConversation.cancel_acp_session(session_id)
-> None` (no state lock; `ValueError` for a non-ACP agent). Errors: `ACPSessionNotFoundError(LookupError)` and
`ACPSessionNotCancellableError(RuntimeError)` from `openhands.sdk.agent.acp_subagents` (not re-exported), and
`TimeoutError` after `_ACP_SUBAGENT_CANCEL_TIMEOUT` = 2.0 s (`acp_agent.py:202`). The Python `RemoteConversation` has
no cancel method. [read; run: tests]

**Events** (`openhands.sdk.event`, registered by import; fields as design A.4) [read; run: round trip]:

| Kind | Written | Latest-wins key | Fields |
|---|---|---|---|
| `ACPSubagentEvent` | per `subagent_update`; per change of the child's cost; per reconnect for an active child (`source="environment"`) | `acp_session_id` | `parent_session_id` (`None` = root), `parent_tool_call_id`, `title`, `description`, `state` (`None` = unconfirmed), `stop_reason`, `cancellable`, `cost`, `cost_currency`, `meta` |
| `ACPSessionMessageEvent` | per `session_message`; per flushed chunked message | `(acp_session_id, message_id)` | `acp_session_id` (`None` = root), `message_id`, `sender_session_id`, `recipient_session_id` (verbatim), `text`, `meta` |
| `ACPSessionTextEvent` | per flushed run of one child's `agent_message_chunk` or `agent_thought_chunk` | append-only | `acp_session_id`, `thought`, `text` |
| `ACPToolCallEvent` (changed) | as before | `(acp_session_id, tool_call_id)` | adds `acp_session_id` and `meta`, both `None` unless the opt-in is on, dropped by `exclude_none` |

**REST.** `POST /api/conversations/{conversation_id}/acp/sessions/{session_id}/cancel` on S2's
`conversation_acp_router` (`acp_router.py:175–224`), returning `CancelACPSessionResponse{session_id, requested=true}`
(`:165`): 200 once `session/cancel` is written; 404 for an unknown conversation; 404 `ACP session {id} is not a
sub-agent session of this conversation.`; 409 `ACP session {id} does not accept cancel; cancel the conversation's turn
instead.` (the root, no live connection, no live grant); 400 with the error's text (not ACP, or `inactive_service`);
504 `ACP server did not accept the cancel for {id} within 2s.` The exported OpenAPI is byte-identical at `a3279be`,
`3fb8f8d` and `2675399` (sha256 `a7a1b5b3…7202c`). [run: route tests; run (r3): export]

**TypeScript** (`clients/typescript`, unchanged by the refactor): `ACPToolCallEvent` intersected with
`{acp_session_id?, meta?}` (`src/events/types.ts:38`); hand-written `ACPSubagentEvent` (`:189`),
`ACPSessionMessageEvent`, `ACPSessionTextEvent` with guards (`isACPSubagentEvent`, `:316`, and two more);
`ConversationClient.cancelAcpSession` (`src/client/conversation-client.ts:430`) and `RemoteConversation.cancelAcpSession`
(`src/conversation/remote-conversation.ts:363`), both URL-encoding the id; `ACP_SETTINGS_KEYS` gains `acp_subagents`
(`src/models/acp.ts:159`); `ACPAgentProfile.acp_subagents?` (`src/models/agent-profile.ts:80`). [read; CI]

**The scripted agent** (`tests/fixtures/acp/scripted_agent.py`, run by path, imports only `agent-client-protocol`):
S1's flags `--subagents`, `--cancel-wait SECONDS` (0), `--transcript PATH`, `--transcript-interval-ms MS` (0),
`--wait-timeout SECONDS` (30, `DEFAULT_WAIT_TIMEOUT_S`, `:105`), added by `add_subagent_arguments` (`:695`), and the
eleven builders of V-6. [read; run: the tests that use all but `--transcript-interval-ms`]

---

## 4 · Structure and seams

### 4.1 The shim, `acp_unstable.py` (222 lines)

Models for the four unstable types on 0.12.1's `acp.schema.BaseModel` (aliases, optionality, `model_fields_set`
telling an omitted field from `null`); a `TypeAdapter` over the three updates discriminated by `sessionUpdate`;
`SubagentClientCapabilities(ClientCapabilities)` with `subagents`; and `SubagentClientSideConnection` (`:139`), the
`@final` library class subclassed under one pyright suppression (`:140`), whose constructor wraps the private
`self._conn._handler` with `route_unstable_updates` (`:154`) and whose `initialize` advertises `subagents` (V-2). The
wrapper (`:180–210`) hands each unstable update to the callback synchronously, inside the library's per-message task,
so unstable and stable updates reach the bridge in wire order; an invalid update, or one without a string
`sessionId`, is dropped with a WARNING, so a `session_message` whose content fails to parse is lost whole, text
included. Two tripwire tests fail once the library parses `subagent_update` or grows `ClientCapabilities.subagents`.
[run: `test_acp_unstable.py`, 7 cases; P7]

### 4.2 The router, `acp_subagents.py` (299 lines)

`ACPSubagentSessions` is bookkeeping for one connection: each method returns the events to store; nothing emits,
locks, awaits or does I/O. State: `root_session_id`, `replaying`, `_children` (each known child's latest
`ACPSubagentEvent`, V-4), `_pending` (at most one open segment per session: a text run or a chunked message),
`_messages` (resolved directed messages by `(session, messageId)`). [read]

- **Children.** A child is known once announced on this connection or seeded from stored events; the first
  `subagent_update` for an id announces it under the session it arrived on (`None` for the root), so a child's child
  is a grandchild. A known child is never re-parented, and an update naming the root or its own session is ignored,
  each with a WARNING (`:102–127`). [run]
- **Merge** (`_merge`, `:214–237`). Omitted keeps, `null` clears, a value replaces; `cancellable` is true iff
  `capabilities.cancel` is an object; `parent_tool_call_id` is lifted from `_meta.openhands.parentToolCallId` and is
  sticky. `title`, `description`, `meta` and all stored text pass through the bridge's secret masking. [run: the
  ten-case merge test, P8]
- **Segments.** Consecutive text chunks of one kind in one child form one run; chunks of one `messageId` form one
  message; anything else for that session flushes first, usage never does; a `subagent_update` flushes the parent's
  segment, then the child's, then stores the snapshot. [run]
- **Cost** (`on_child_usage`, `:181–192`). A child's `usage_update` sets `cost`/`cost_currency` (`None` when omitted)
  and stores a snapshot only on change; the root's usage sync, context window and metrics never see it. [run]
- **Replay.** While `replaying`, nothing is returned and only unknown children are registered (parent only). [run]
- **Grants** (`check_cancel`, `:204–212`): not cancellable for the root, not found for an unknown id, not cancellable
  without a grant received live on this connection. [run]
- **Seed** (`:80–93`): each stored child is held unconfirmed and without a grant; a `source="environment"` snapshot is
  returned for each child whose last stored `state` is neither `None` nor `"idle"` (D-1). [run]

### 4.3 The bridge, `acp_agent.py`: where the complexity sits

+294 −43 lines through a 5,253-line file, the one upstream changes most. [run: `wc`, `git diff --numstat`]

- **Diversion** (`:1753–1761`). After S2's recorder and the fork branch, `_child_session` (`:1664`) returns a known
  child's id, else `None` (warning once for an id that is neither root nor child, V-1). With the opt-in on, every
  update but a usage update or a child's text chunk first flushes its session's segment; for a child,
  `_route_child_update` (`:1689–1712`) drops everything while replaying, sends text and usage to the router, drops
  plans and other updates with a DEBUG line, and lets tool calls through. [run]
- **The unstable path** (`unstable_session_update`, `:1602–1624`): idle clock, fork check, the warning for an
  unannounced session, the router, `emit_subagent_events` (`:1626`), which drops events while replaying, drops them
  with a DEBUG line without an emitter, and logs and swallows an emitter's exception per event. [run; the swallow at
  `:1640–1641` is uncovered in CI]
- **The shared tool-call path.** Entries carry `acp_session_id` and (opt-in on) `meta`, are masked, and are matched
  by `(tool_call_id, acp_session_id)` (`:1825–1828`); trace spans open and close only for root calls (`:1803`,
  `:1863`); `_emit_tool_call_event` (`:1870`) sends a child's call to `on_session_event` and a root call to the turn's
  `on_event`. [run]
- **Three close-outs.** `reset()` (`:1459`) keeps open child entries, so a child's cell can outlive the turn; the
  successful turn's force-complete skips child entries (`:3869–3873`); an aborted turn's `_cancel_inflight_tool_calls`
  (`:3795–3850`) emits one synthetic `failed` per open entry, a child's through `on_session_event`, and marks it
  `failed_by_abort` (`:3821`, `:3842`) so later aborts skip it and the agent's own report wins (E-1). [run]
- **Turn end.** `_do_acp_prompt` submits every open segment after the usage wait (`:4085`), on both `run()` and
  `arun()`; `trace.finish_turn` gets root calls only (`:4199–4206`). [read; `flush_all`'s loop body,
  `acp_subagents.py:201`, is uncovered in CI]
- **Connection start** (`_launch_acp_session`, `:3286–3304`): the bridge with `subagents=self.acp_subagents`, the
  conversation's emitter, the seed's reset snapshots, all before the subprocess starts; then the shim connection
  (`:3451`), `initialize` (`:3478`), `session/load` under `replaying()` (`:3602`), or the root id after `session/new`
  (`:3659`). [read; seed and the reconnect run in tests]

### 4.4 Threads, order and what the store holds

The portal (ACP loop) thread only submits child events; S2's single worker stores them under the state lock; root
events keep the turn's synchronous path. Under a synchronous `run()` a turn's child events are stored after its
`FinishAction`; under `arun()` they interleave while the turn runs [run in r2 at `a3279be`: 0 of 9 child snapshots
before `FinishAction` under `run()`, 8 of 9 under `arun()`; the refactor does not touch the emitter or the threads,
read]. Within one child the order is wire order.

The `--subagents` turn stores these 25 ACP events, identical in kind, order and content at `a3279be` and `2675399`
apart from ids, timestamps, `parent_id` and the root's random session id in two message participants [run (r3): wire
probe]:

```text
 0–1   ACPSessionControlsEvent ×2 (S2's)      2–3  ACPToolCallEvent root cell-1 in_progress, completed
 4–5   ACPSessionControlsEvent ×2             6    ACPSubagentEvent child-a running, in cell-1, cancellable
 7     ACPSessionMessageEvent root→child-a    8    ACPSessionTextEvent child-a thought 'Reading part A.' (2 chunks)
 9     ACPToolCallEvent child-a cell-a1       10–12 child-a-1: running in cell-a1; its two-chunk answer; idle
13     cell-a1 completed                      14   ACPSubagentEvent child-a running, cost 0.0004 USD
15     ACPSessionMessageEvent child-a→root    16   ACPSubagentEvent child-a idle end_turn
17–20  child-c: running, not cancellable; cell-c1 in_progress, completed; idle
21–24  child-b: running; cell-b1 in_progress, completed; idle
```

Each event's timestamp is taken when the portal creates it, so per child the timestamps never decrease in log order,
a reconnect snapshot is later than every earlier event of its child, and a spawning cell's `started` event precedes
its whole subtree. [run: the three ordering tests; over REST, the cross test]

### 4.5 The four edges v2.1 ruled

E-1 (one synthetic `failed` per child call), E-2 (nothing a replay sends is tracked), E-3 (a cancel for an idle child
keeping its grant is sent) and E-4 (unstable updates on an unannounced session stay under its id, with a warning) are
built as at `a3279be` and pinned by the tests v2.1 named, all passing [run]. E-4's helper is V-1's.

---

## 5 · What each consumer relies on

**C1 (Canvas fork; designed at `design/c1` `88f5c43`, not built)** reads stored events through design §5 and §5.1.
As built: the scripted tree rebuilds from stored events when children are placed by spawning cell (V-9), and §5 rule
2's fallbacks are not exercised [run; read]; the three ordering facts of §4.4 [run]; storage with `exclude_none`
[read]; the 409 and 404 `detail` texts, asserted verbatim [run]; `cancelAcpSession`, the three types and guards,
`ACP_SETTINGS_KEYS` [CI]; the profile field and its baseline [run]; the scripted agent by path with `--subagents
--cancel-wait N` and `--transcript` [run]. `--transcript-interval-ms` (C1 §9.1 item 2) exists [read] and no test pins
its pacing, now or at `a3279be` (P5, §8).

**D1's `dr-acp`.** `initialize` carries `subagents` as an object, unchanged on the wire (V-2) [run]; D1's ten native
golden recordings (`c8d7fbb`) replay through the bridge into stores identical at `a3279be` and `2675399` (§7.4)
[run (r3)]; `session/cancel` carries the full child id [run: request log; CI: the live stop test]; the live tier
passes on dr-acp at `2675399` [CI]. A dr-acp run killed by a restart replays its children's open cells; E-2's unit test pins that they are not
tracked [run], and no test drives a real replay (§10).

**D5 (desktop app; designed at `design/d5` `8086afb`).** `acp_subagents` on its agent profile, through the resolver
and seed, with a persisted baseline [run]; the scripted agent's `--transcript` mode for its `bridge-replay` job [run];
S1's live file with its two variables, which D5's `fork-live.yml` runs [CI].

**S2.** Owns the emitter, the scripted agent's serving and `acp_router.py`; its recorder stays first in
`session_update` (`:1738`). [read]

---

## 6 · Wiring

**The proof is the stack's CI.** Every PR of #10–#16 is green at its head: 28 or 29 checks each, every one
`success` but `Validate PR description`, skipped (draft; #10, #12 and #16 list it twice) [CI]. Each run checks out
GitHub's merge of the head into its base; for #11–#16 the base is the head's ancestor, and for #10 the merge of
`049ceb5` into `9277e71` has `049ceb5`'s tree [run: `git merge-tree`], so each run tested its head's own tree [CI:
`HEAD is now at …` in each log].

`Run tests` runs a job's tests only when its paths changed between the PR's base and head (`tj-actions/changed-files`
in `.github/workflows/tests.yml`: `sdk-tests` on `openhands-sdk/**`, `tests/sdk/**`; `agent-server-tests` on
`openhands-agent-server/**`, `tests/agent_server/**`; `cross-tests` on `tests/**`; every job on `tests.yml` itself)
[read]; a job without changes passes in seconds without running pytest [CI: #16's `agent-server-tests` log]. So each
level's CI tests what that level changes:

| PR · head | Diff against its base | `Run tests` run | Python jobs that ran tests [CI] |
|---|---|---|---|
| #10 · `049ceb5` | +462 −4, 4 files (with the swap fix, §2 V-10) | [37174876576](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37174876576) | `sdk-tests` 6,690 passed; `cross-tests` 496 passed, 1 skipped |
| #11 · `3ba31ae` | +356 −8, 10 | 37175595431 | `sdk-tests` 6,701; `cross-tests` 496 |
| #12 · `eab2eb8` | +1,657 −48, 8, with `tests.yml` | 37175597225 | every job runs (I read these four): `sdk-tests` 6,739; `agent-server-tests` 2,418; `cross-tests` 496; `acp-live-tests` 25 passed, 3 skipped |
| #13 · `1c72537` | +97, 7 | 37175598478 | `sdk-tests` 6,742 (one unrelated xpass, `test_bubus_timeout_does_not_free_blocked_handler_thread`); `cross-tests` 496 |
| #14 · `6481bcf` | +500 −9, 10 | 37175599887 | `sdk-tests` 6,747; `agent-server-tests` 2,425; `cross-tests` 497; `acp-live-tests` 25 passed, 4 skipped |
| #15 · `ba8f89c` | +252 −2, 11, TypeScript only | 37175601521 | none; TypeScript `test (22.12)` 23 files, 359 passed |
| #16 · `6a05b13` | +423 −7, 2 | [37175602976](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37175602976) | `sdk-tests` 6,752 passed, 7 skipped, 12 xfailed, 166.4 s; `cross-tests` 497 passed, 1 skipped, 138.3 s; TypeScript 359 passed |

The per-PR diffs sum to more than S1's total because later levels rewrite lines earlier ones add. [run: `git diff
--shortstat`] At the top: each of S1's 69 SDK cases has its own `PASSED` line in #16's `sdk-tests`, the three
restored tests and S2's swap test among them, and the cross test passes in #16's `cross-tests`; S1's 8 agent-server
cases pass in #14's `agent-server-tests` [CI]. The agent-server suite never ran at #15's or #16's head; from `6481bcf`
to `6a05b13` the Python changes are the scripted agent and `test_acp_subagents.py` (level 07), and the one
agent-server file that starts the scripted agent, `test_acp_router.py`, passes here at `6a05b13` with S1's other
agent-server cases (§7.1) [run]. Also green at every head: `pre-commit`, `Persisted settings` (at #16: 19 fixtures
validated), `REST API (OpenAPI)` (at #16: only additive `oneOf` expansions and S2's enum values, passed), the
TypeScript client CI, integration tests, `endpoint-audit`, `check-docstrings`, `check` [CI]. Still outside CI: the
SDK API breakage step (runs only on a version change) and the OpenAPI quality ratchet (no pull-request trigger in the
fork); the ratchet passed at `2675399` (§7.6) [run (r3)].

**PR #2** (`2675399`) was green at its head, 28 checks (r3's §6) [CI], and is closed unmerged; **PR #17** (the swap
fix, `90e99f6`) merged into `deep-reasoning` at 03:41 UTC [CI].

**The live workflow** is deep-reasoning's `fork-live.yml` on `ci/fork-live` (`a8154e2`): it checks out the SDK at
`sdk_ref`, installs deep-reasoning and `dr-acp`, and runs `pytest -m acp_live tests/sdk/agent/test_acp_subagents_live.py`
with `OPENHANDS_ACP_LIVE_AGENT_COMMAND="<dr-acp> --config docs/configs/advising/main.yaml --home <temp>"` and
`OPENHANDS_ACP_LIVE_SUBAGENTS_PROMPT="/compare-departments Which department is lighter for a first-year student, CS
or STAT?"`. [CI]

---

## 7 · Experiments and tests, as measured

### 7.1 The runs

| Run | Commit | Conditions | Result |
|---|---|---|---|
| CI #16 `Run tests` 37175602976 | `6a05b13` | `pull_request`, ubuntu, Python 3.13 | `sdk-tests` **6,752 passed**, 7 skipped, 12 xfailed, 166.4 s; `cross-tests` **497 passed**, 1 skipped, 138.3 s; S1's 69 SDK cases and the cross test each `PASSED` [CI] |
| CI #14 `Run tests` 37175599887 | `6481bcf` | as above | `agent-server-tests` **2,425 passed**, 337.8 s, S1's 8 cases each `PASSED`; `acp-live-tests` 25 passed, 4 skipped, S1's two among the skipped ("not both set") [CI] |
| coverage in those jobs | `6a05b13`; `6481bcf` | as above | the same as r3's at `2675399`: `acp_subagents.py` 96% (uncovered 140 a message's `_meta`; 147, 168, 184 replay or unknown-child returns; 157, 286 non-text blocks; 201 `flush_all`'s body); `acp_unstable.py` 95% (205–206 no `sessionId`; 218, 220); `event/acp_subagent.py` 93%; `acp_router.py` 99% in #14's `agent-server-tests`, missing only 224, the 200 return [CI] |
| CI TypeScript client, #15 and #16 | `ba8f89c`, `6a05b13` | Node 22.12 | **23 files, 359 passed** each [CI] |
| live [37171079147](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37171079147), job 111343992767 | SDK `2675399`, deep-reasoning `a8154e2` | started 02:26:53 UTC; ubuntu, Python 3.12.3; dr-acp on gpt-6-luna; suites `s1` (the S2 step skipped) | **2 passed** in 48.26 s (§7.5) [CI]; no live run since [CI: the workflow's run list] |
| here: S1's SDK files | `6a05b13` | 4 CPUs, load 4–9, serial | `test_acp_unstable.py`, `test_acp_subagents.py`, `test_acp_subagent_events.py`: **64 passed**, 19.0 s [run] |
| here: the shared files | `6a05b13` | serial | `test_acp_router.py` (S2's tests with S1's 6), `tests/cross/test_check_persisted_settings_compat.py`, and S1's 7 cases in the event-service, dedup, resume-transcript and resolver files: **55 passed**, 30.6 s [run] |
| here: the cross test, alone | `6a05b13` | serial | **1 passed**, 12.9 s [run] |
| here: S2's swap test, alone, five times | `6a05b13` | serial | **5 of 5 passed**, 1.2–1.5 s each [run]; PR #17 records that the race never reproduced locally (48 of 48) [CI] |
| here: `a3279be`'s own tests | `a3279be` (archive) | serial | `test_acp_subagents.py`, `test_acp_unstable.py`: **62 passed**, 36.8 s; the baseline for §8's comparisons [run (r3)] |

No run failed but the probes' (§8), so nothing was rerun. Reproduce: `OPENHANDS_SUPPRESS_BANNER=1 uvx uv@latest run
--frozen pytest tests/sdk/agent/test_acp_unstable.py tests/sdk/agent/test_acp_subagents.py
tests/sdk/event/test_acp_subagent_events.py`.

### 7.2 S1's tests, by file

| File | Cases | What they pin |
|---|---|---|
| `tests/sdk/agent/test_acp_unstable.py` | 7 | the two tripwires; the whole `initialize` the agent receives; nine interleaved updates in wire order; a `session_message` with a text and an image block reaches the callback with both blocks, typed; a stable update on a child id still parsed by the library; a malformed update dropped with one WARNING. Over a real agent-side `Connection` on a socket pair |
| `tests/sdk/agent/test_acp_subagents.py` | 48 | 33 bridge units (the ten-case merge table, segments, messages, cost, keyed tool calls, the three close-outs, the emitter, replay, reconnect, unannounced sessions, E-1, E-2, E-4); 14 cases through a real `LocalConversation` on the scripted agent and one on the scripted agent alone (§7.3) |
| `tests/sdk/event/test_acp_subagent_events.py` | 9 | JSON round trip of four kinds; a legacy `ACPToolCallEvent` loads with both new fields `None`; visualization (4) |
| `tests/agent_server/test_acp_router.py` | 6 | through an in-process agent-server and the scripted agent: unknown conversation 404, unknown session 404 and `detail`, `child-c` 409 and `detail`, non-ACP 400, a cancel never written 504; every stored event of a run validates against the public `Event` schema |
| `tests/agent_server/test_event_service.py` | 2 | the event loop keeps running while a cancel blocks; an inactive service refuses |
| `tests/cross/test_remote_conversation_live_server.py` | 1 | a real server and WebSocket: cancel `child-b` through the route (the 200 and its body), every sub-agent event reaches the WebSocket client, order and timestamps on the REST log |
| dedup, resume transcript, resolver | 1, 1, 3 | the remote cache merges child and root calls apart; the resume transcript skips child calls; the opt-in through the resolver to the agent (2) and back through the seed |
| `tests/sdk/agent/test_acp_subagents_live.py` | 2 live | §7.5 |
| TypeScript | 5 | `cancelAcpSession` posts, encodes the id, posts for its conversation; the opt-in survives the settings filter; each guard matches only its kind |

[run: collected and passed; TS: CI]

### 7.3 E5 through a conversation (the agent-server half)

A real `LocalConversation` with `ACPAgent(acp_command=[python, scripted_agent.py, …], acp_subagents=True)`, no
network; the baseline is the scripted or recorded wire stream itself. All passed here and in CI. [run; CI]

| Test | Asserts |
|---|---|
| `test_scripted_run_stores_the_scripted_tree` | the stored tree, children placed by cell, equals the scripted one: `child-a` (0.0004 USD, `cell-a1`, task and answer, one thought run), `child-a-1` in `cell-a1`, `child-c` not cancellable, `child-b` |
| `test_scripted_run_books_only_the_roots_cost` | the conversation's cost is 0.0011, not 0.0015 |
| `test_subagents_off_stores_only_root_work_through_the_stock_connection[--subagents, --transcript]` | off, with `--subagents` or with an outgoing-only recording of a turn with two children: the connection is exactly `ClientSideConnection`; `initialize` equals the library's serialization; only `cell-1`, no `acp_session_id`, no new kinds |
| `test_cancel_acp_session_reaches_the_child_without_waiting_for_the_state_lock` | `--cancel-wait 30`, `run()` in a thread: the call that succeeded began while the run held the lock; the run finishes; `session/cancel {sessionId: child-b}` logged; `child-b` idle `cancelled`, `cell-b1` failed |
| `test_cancel_acp_session_for_an_idle_child_that_keeps_its_grant_is_sent` | E-3: the cancel is written; `child-b`'s stored snapshot is unchanged |
| `…_refuses_a_child_without_a_grant` · `…_refuses_unknown_and_root_sessions` · `…_without_a_live_connection_is_refused` | 409-class and no `session/cancel`; 404- and 409-class; 409-class before the first run |
| `test_scripted_transcript_replays_a_recording[full, outgoing-only]` | a recorded turn with two children replays into its tree |
| `test_transcript_exits_non_zero_when_a_wait_point_outlasts_the_wait_timeout` | no conversation: the scripted agent with `--transcript` and `--wait-timeout 0.2`, stdin held open, no client; it exits non-zero within 10 s |
| three ordering tests | §4.4's three facts; the reconnect one drives a second connection whose `session/load` the player refuses, so the bridge falls back to `session/new` |

### 7.4 D1's golden recordings through the bridge

An uncommitted probe replays each of D1's **ten** `tests/acp/golden/*.native.jsonl` at deep-reasoning `c8d7fbb`
(r2 listed nine; `unanswered` was not among them) through `--transcript` into a `LocalConversation` with the opt-in
on, one message per recorded prompt, and compares what is stored at `a3279be` and at `2675399`. [run (r3); the
source and the scripted agent are identical at `6a05b13`]

| Recording | Children | Stored ACP events | Equal at both commits |
|---|---|---|---|
| `claude`, `linear` (2 prompts) | 0 | 2, 12 | yes |
| `depth3`, `fanout2`, `fork`, `unanswered` | 2 each | 22, 23, 26, 16 | yes |
| `exhausted`, `failing`, `namespace` | 1 each | 19, 15, 13 | yes |
| `fanout20` | 20 | 146 | yes |

10 of 10 equal, ids, timestamps and `parent_id` aside. r2's comparison of each stored tree with the tree read from
the recording was not repeated; with the stores equal, its result at `a3279be` (9 of 9) carries to the nine it
covered.

### 7.5 The live tier (dr-acp on gpt-6-luna)

Run 37171079147 [CI], SDK at `2675399`, `-m acp_live tests/sdk/agent/test_acp_subagents_live.py -v -rA`: **2
passed** in 48.26 s. No live run has used a stack commit; `6a05b13` differs from `2675399` only in the three test
files of the header, none of them the live file or `tests/conftest.py`, which it imports [run: `git diff`; CI: the
workflow's run list]. The assertions are r2's; the refactor moved the file's helpers to `tests/conftest.py`, so both
tests now poll every 0.02 s instead of 0.1 s [read].

| Test | Asserts | Result |
|---|---|---|
| `test_live_agent_tree_is_well_formed` | `run()` on the CS-vs-STAT prompt; within 30 s no child `running`; at least one grandchild; every child's parent is the root or a stored child; every set `parent_tool_call_id` names a stored call of its parent; no child text run of ≥ 40 characters in the answer; the conversation's cost equals the root's last reported cost | passed; prompt returned in 20.2 s |
| `test_live_agent_stops_one_subagent_and_its_branch` | `arun()` under 120 s; on the first grandchild whose parent is `running` and `cancellable`, `cancel_acp_session(parent)` from a thread; that child and its descendants stored idle `cancelled` within 30 s; no non-terminal call of the branch after the branch root's `cancelled` snapshot | passed; prompt returned in 22.4 s |

The run's spend is not printed. [CI]

### 7.6 Upstream guards

| Guard | Result |
|---|---|
| OpenAPI export | byte-identical at `a3279be`, `3fb8f8d` and `2675399`, sha256 `a7a1b5b3b15284008de10c5777f2d0755e82881ffec7e43920c3c62067e7202c`, the Refactorer's `a7a1b5b3…202c` [run (r3)]; not rerun at `6a05b13`, whose source is `2675399`'s |
| OpenAPI weak-schema ratchet | passes at `2675399`, "65 allowlisted weak locations"; the allowlist is unchanged since `a3279be` [run (r3)] |
| REST breakage, persisted settings, TypeScript lint, suite and type budget, pre-commit | green in CI at every head of #10–#16 (§6) [CI]; not run here |
| SDK API breakage (Griffe against PyPI 1.50.1) | not rerun; r2 found one upstream error (`ACPAgentSettings.llm`) and nothing of S1's at `a3279be`, and the refactor changes no public signature (§3) [read] |

---

## 8 · What the refactor removed from test coverage

Fifteen Python tests and one TypeScript test that v2.2 names are gone, merged or renamed, and two moved out of a
class; the stack restored three of the properties under new names (V-7). Each row says where its property is pinned
at `6a05b13`. Probes are one temporary edit each, run against the files named, reverted, the tree clean after each;
where a cut test might have pinned the property, r3 ran the same edit against `a3279be`'s own tests and code. [run]

| v2.2's test (at `a3279be`) | At `6a05b13` | The property, and what pins it now |
|---|---|---|
| `test_scripted_run_keeps_child_text_out_of_the_answer` | cut (`a910ac9`) | child text never in the root's answer: the bridge unit `test_child_text_never_reaches_the_root_answer` |
| `test_scripted_run_with_subagents_off_stores_only_root_work[--subagents, --transcript]` and `test_subagents_off_uses_the_stock_connection_and_initialize` | merged into `test_subagents_off_stores_only_root_work_through_the_stock_connection` (`a910ac9`), `--subagents` only; its `[--transcript]` case restored (`306731d`) | the stock connection and `initialize`, root work only: pinned. **The transcript player's conformance rule**: no other session's update without `subagents`: **pinned** (P4, P4s); no unstable update without `subagents`: **unpinned**, and no stored event shows it (P4u) |
| `test_cancel_acp_session_reaches_the_child_and_its_cancelled_state_is_stored`, `test_cancel_acp_session_does_not_wait_for_the_state_lock` | merged into `test_cancel_acp_session_reaches_the_child_without_waiting_for_the_state_lock` (`a910ac9`) | both tests' assertions are in it [read] |
| route `test_a_cancel_reaches_the_child_and_its_cancelled_state_is_stored` | cut (`a910ac9`) | the route's 200 and body: the cross test only (P9) |
| `test_child_cost_is_on_its_association_and_never_booked_to_the_conversation` | renamed `test_child_cost_is_stored_on_its_association_when_it_changes`, booking assertion dropped (`ca39def`) | stored once per change: the unit; never booked: `test_scripted_run_books_only_the_roots_cost` |
| `test_transcript_interval_paces_the_replay` | cut (`6dcde3e`) | pacing: **unpinned now and at `a3279be`** (P5) |
| `test_transcript_wait_point_that_is_never_reached_exits_non_zero` | cut (`6dcde3e`); restored as `test_transcript_exits_non_zero_when_a_wait_point_outlasts_the_wait_timeout` (`6a05b13`) | the wait timeout: **pinned** (P6′); a missed wait point that returns instead of raising still fails the script, through `_respond`, so it is not pinned, nor was it at `a3279be` (P6) |
| `test_initialize_without_subagent_capabilities_is_the_library_call` | cut with its branch (`bf57a3a`) | the opt-off `initialize`: the merged opt-off conversation test |
| `test_custom_state_is_kept_whole` | cut with `extra="allow"` (`6b089e5`) | a custom state's name: the merge table's `state-custom` case; extra keys are no longer kept (V-3) |
| `test_patch_fields_tell_omitted_from_null` | cut (`a910ac9`) | the merge table (P8) |
| `test_message_content_keeps_non_text_blocks_typed` | cut (`a910ac9`); restored as `test_session_message_with_a_non_text_block_reaches_the_callback_whole` (`049ceb5`), over the wire | a `session_message` with a non-text block parses and reaches the bridge whole: **pinned** (P7) |
| `test_root_tool_call_event_is_stored_as_before` | cut (`a910ac9`) | the model's `meta` default: `test_legacy_acp_tool_call_event_loads_without_session_fields` (P3b); the bridge leaving a root call's `meta` unset: unpinned, and was at `a3279be` (P3) |
| `test_acp_create_agent_forwards_subagents` | cut (`a910ac9`) | the resolver test, which builds the agent (P2) |
| `TestEventServiceCancelACPSession::…` (2) | module functions (`5b17efd`) | off-the-loop now pins that the loop keeps running while the cancel blocks, not a thread id |
| TS `sub-agent event shapes accept stored events` | cut (`a910ac9`) | the stored shapes: the guards' test |

| Probe | The temporary edit | At `6a05b13` (r4) | At `2675399` (r3) | At `a3279be` (r3) |
|---|---|---|---|---|
| P1 | `_PER_EVENT_FIELDS` without `parent_id` (a snapshot keeps a stored event's place in the conversation tree) | not rerun | **caught**: `test_new_connection_withdraws_cancel_and_unconfirms_state`, `test_partial_patch_after_reconnect_keeps_the_stored_title` | — (no such field) |
| P2 | `create_agent()` stops forwarding `acp_subagents` | not rerun | **caught**: `test_acp_profile_carries_the_subagents_opt_in_to_the_agent[True]` | — |
| P3 | the bridge stores a root call with `meta={}` | not rerun | not caught (624 cases: S1's SDK files, `test_acp_agent.py`, dedup, resume transcript) | not caught by the cut test either, which built the event itself [read] |
| P3b | `ACPToolCallEvent.meta` defaults to `{}` | not rerun | **caught**: the legacy-load test | — |
| P4 | the transcript player plays everything without `subagents` (`_plays` returns `True`) | **caught**: `…_through_the_stock_connection[--transcript]`, stored calls `{cell-1, w1}`: the worker's tool call stored as root work; the other 63 of S1's SDK cases pass | not caught (S1's 46 and the cross test) | **caught**: `…_off_stores_only_root_work[--transcript]` |
| P4s | the stable half: other sessions' updates played, unstable ones still skipped | **caught**: the same case, the same `w1` | — | — |
| P4u | the unstable half: the root session's unstable updates played, other sessions still skipped | **not caught**: S1's 64 SDK cases pass; an opt-off conversation on the same recording stores the same 7 events as without the edit, random ids aside; its log gains 5 ERROR records with tracebacks, `Unhandled error while handling notification method=session/update`, from `acp/connection.py:232` on the root logger, one per unstable update the recording sends on the root session [run: scratch probe] | — | — |
| P5 | the player ignores `--transcript-interval-ms` | not rerun; no test passes the flag [run: `grep`] | not caught | **not caught**: the unpaced run took 1.47 s against the test's floor of 15 × 50 ms |
| P6 | a missed wait point returns instead of raising | **not caught** (S1's 64 SDK cases): run directly with stdin held open, the script still exits 1, through `KeyError: 0` in `_respond` [run: scratch probe] | not caught | not caught: the script still exits non-zero, through a `KeyError` in `_respond` |
| P6′ | the wait timeout is ignored (`asyncio.timeout(None)`) | **caught**: `test_transcript_exits_non_zero_when_a_wait_point_outlasts_the_wait_timeout`, `TimeoutExpired` after 10 s; the agent is killed in its `finally` | not caught | **caught**: `test_transcript_wait_point_that_is_never_reached_exits_non_zero` |
| P7 | `SessionMessage.content` accepts text blocks only | **caught**: `test_session_message_with_a_non_text_block_reaches_the_callback_whole`, `TimeoutError` waiting for the update, which the shim drops with "Dropping an invalid ACP session_message (2 validation errors)"; the other 63 pass | not caught (S1's 61) | **caught**: `test_message_content_keeps_non_text_blocks_typed` |
| P8 | a `null` title treated as omitted | not rerun | **caught**: the merge table's `title-null` | — |
| P9 | the route answers 200 with `requested: false` | not rerun | **caught by the cross test only**; the route and service files pass (48) | — |
| P10 | `replaying()` never clears the flag | not rerun | **caught** by the reconnect conversation test only; the two replay units pass | — |

Not rerun at `6a05b13`: P1–P3b, P5 and P8–P10; the code each edits and the tests that met it are unchanged [run:
`git diff 2675399 6a05b13`]. P4 to P7 ran against S1's three SDK files (64 cases): no other test file uses the
transcript player [run: `grep`], and the scripted `--subagents` run that the router and cross tests use sends
text-only messages [read]. Without the edits, the player run directly exits 1 through its `TimeoutError` [run]; a
client that closes the player's stdin before a wait point ends it with exit 0 before the timeout [run], which the
restored test avoids by holding stdin open [read].

Plainly: the three properties that lost their only test in the refactor have one again, the conformance rule for
other sessions' updates (P4), the wait timeout (P6′) and the parse of a message with a non-text block, without which
such a message is dropped whole, text included (P7). The rule's unstable half has no test, and no stored event can
show it: the stock connection logs and drops each unstable update (P4u). Pacing was never pinned (P5), nor a missed
wait point that returns (P6). The route's success path is reached only through the cross test (P9). The create-agent
forwarding, the omitted-versus-null merge, the model default and the replay flag stay pinned by other tests (P2, P8,
P3b, P10), and the refactor added one pin (P1).

---

## 9 · Size, and what resisted compression

S1 is +1,302 −54 of source (Python product code +1,143 −52, was +1,235 −49 at `a3279be`; TypeScript +112 −2) and
+2,428 −9 of tests and fixtures (deterministic Python tests +1,658, r3 +1,618, `a3279be` +1,942; the live file 188,
was 207; the scripted agent +442 −4, was +459 −4). [run: `git diff --numstat 9277e71 6a05b13`] About 12.4 h at Gate
C at ≈300 lines an hour, against 14 h before; the stack splits it into seven PRs, the largest #12 (+1,657 −48). The
parts of this document that will not shrink are §2 and §8: the refactor is mostly test cuts and renames, and each one
changes a line v2.2 states or a property a consumer reads.

---

## 10 · What I could not verify

1. **The live tier at the stack.** The last live run is at `2675399`; none used a stack commit (§7.5). Its cost is
   not printed [CI].
2. **A real `session/load` replay of sub-agent traffic.** The replay flag is pinned by units that enter `replaying()`
   and, for clearing it, by the reconnect test, whose `session/load` the transcript player refuses; no agent replays
   sub-agent traffic in any test or probe.
3. **`arun()` interleaving at the stack**: measured in r2 at `a3279be` only; the code it depends on is unchanged
   [read].
4. **The top's whole suite in one run, and each commit on its own.** CI ran at each PR's head, but only the jobs whose
   paths that level changes (§6): the agent-server suite last ran at #14's `6481bcf`, and no run covered `6a05b13`'s
   tree with every job. Commits below a head (`2f7642c` alone, `306731d` alone) did not run; whether S1's commits
   cherry-pick onto `main` is unknown.
5. **Not run here**: the full SDK, agent-server and cross suites; the TypeScript suite and lint, pre-commit and
   pyright, and the REST breakage script, which CI ran green (§6); and the SDK API breakage check, which nothing ran
   at a stack commit.
6. **Paths read but not seen run**: a notification without `sessionId` (uncovered in CI); a message's `_meta` and
   non-text blocks in the router (`acp_subagents.py` 157, 286, uncovered in CI; the restored P7 test stops at the
   shim's callback); an emitter's exception swallowed per event; the turn-end flush of a still-open segment
   (`flush_all`'s body, uncovered in CI; r2's probe ran it at `a3279be`); the explicit-capabilities branch of
   `initialize`; the Python `RemoteEventsList` reordering; masking of `meta`.
7. **The opt-in from a profile through a real agent-server launch**: the resolver, seed and baseline are checked; no
   run started a conversation from such a profile.
8. **Canvas** (C1) is not built; §5 checks the stored shapes against C1's design, not Canvas code.
9. **The brief's and the Implementer's claims**: the stack's top differs from `2675399` by exactly the three test
   files (holds); 75 + 3 deterministic cases (holds: 78 collected); the swap fix is the same change as PR #17
   (holds: `2f7642c` is a cherry-pick of `90e99f6`, the file identical at both heads). P4's unstable half, "no
   conversation can see it": holds for the stored events and for every S1 test; the client's log does show it, five
   ERROR records with tracebacks (P4u). r3's Refactorer claims hold as r3 recorded.
