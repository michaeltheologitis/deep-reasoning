# S1 · ACP sub-agent sessions in the agent-server, as built

**TASK-3** · Cartographer · **r3**, 2026-10-04 · the code at `2675399`, head of `feat/acp-subagent-sessions` in the
SDK fork [michaeltheologitis/software-agent-sdk](https://github.com/michaeltheologitis/software-agent-sdk) (draft
PR #2 into `feat/agent-surfaces`; S2's head `d938c90`, merged at `cd6cb23`; S1's own diff is `d938c90..2675399`) ·
checked against the design at `e05986f` (`docs/design/s1-acp-subagent-sessions.md` v2.2, on this branch, which
matches `a3279be`) · agent-client-protocol 0.12.1 (the fork's lock), pydantic 2.12.5 · uv 0.12.23 (`uvx uv@latest`),
Python 3.13.14 in this sandbox.

**This revision** (r3) is Gate C's map of the code after the literate refactor: fifteen S1 commits after `a3279be`,
with S2's refactor merged at `3fb8f8d` and S2's `d938c90` at `cd6cb23`. r2 (`cad94ff`) read `a3279be`; r1
(`17ab4d5`) read `0cfb6a2`. The design is not revised yet, so §2 lists what v2.2 now states differently from the
code (V-2 to V-10 are new; V-1 is r2's and still holds), and §8 says what the refactor took out of the tests. Every
count, line number and run is `2675399`'s unless it says otherwise.

**Where this file lives.** deep-reasoning's branch `as-built/s1-r3`, cut from `design/s1` at `cad94ff`; the
Conductor merges it into `design/s1`. The branch has no `pyproject.toml`, docs site or test runner, so nothing
collects `as_built/` and there is nothing to wire. [run: `git ls-tree -r HEAD`]

**Evidence marks.** Every claim carries one.
- **[run]**: executed here, without writing a tracked file in either checkout: S1's test files; uncommitted probe
  scripts in my scratchpad (a wire probe, a state probe, a replay of D1's golden recordings), run at `2675399` and,
  for comparison, against `a3279be`'s code from a `git archive` on `PYTHONPATH` in the same environment (the lock is
  unchanged between them); ten mutation probes, one temporary edit each, reverted, the worktree clean after each
  (§8). No model calls; network only for GitHub.
- **[CI]**: GitHub's records through the MCP tools: PR #2's 28 checks at `2675399`, with the full logs of
  `sdk-tests`, `agent-server-tests`, `cross-tests`, `acp-live-tests`, `test (22.12)`, the REST breakage and the
  persisted-settings jobs (downloaded through signed URLs), and the live run
  [37171079147](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37171079147).
- **[read]**: read in the code, **not executed**. §10 lists the read claims that matter.

**Reading order.** §2, then §8, then §1, §3 and §4 as the map; §7 for the measurements; §10 for what I could not
verify.

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

| Part | before: `5e3317f..a3279be` | now: `d938c90..2675399` | Where |
|---|---|---|---|
| the shim | 247 | 222 | `openhands-sdk/openhands/sdk/agent/acp_unstable.py` |
| the router | 338 | 299 | `openhands-sdk/openhands/sdk/agent/acp_subagents.py` |
| bridge and agent | +317 −40 | +294 −43 | `openhands-sdk/openhands/sdk/agent/acp_agent.py` (5,253 lines) |
| events | +177 | +175 | `event/acp_subagent.py` (158), `event/acp_tool_call.py`, `event/__init__.py` |
| other SDK consumers | +79 −8 | +76 −8 | local and remote conversation, visualizer, resume transcript, settings, three profile files |
| agent-server | +77 −1 | +77 −1 | `acp_router.py`, `event_service.py` |
| TypeScript client | +112 −2, +27 config | the same | `clients/typescript/src/…`, `endpoint-audit.config.json`, `config/public-type-budget.json` |
| CI config | +20 | +20 | weak-schema allowlist (+18), `.github/workflows/tests.yml` (+2) |
| **source** | **+1,394 −51** | **+1,302 −54** | |
| Python tests | +2,149 | +1,806 −4 | `tests/…`; now also `tests/conftest.py` (+11 −4), no longer `tests/sdk/test_settings.py` |
| scripted agent | +459 −4 | +442 −4 | `tests/fixtures/acp/scripted_agent.py` (748 lines) |
| persisted baselines | +27 | +27 | `v7/agent_settings_acp_subagents.json`, `v2/agent_profile_acp_subagents.json` |
| TypeScript tests | +126 | +113 | `clients/typescript/src/__tests__/…` |
| **tests** | **+2,761 −5** | **+2,388 −9** | |

Total +3,690 −63 in 43 files (was +4,155 −56 in 43). Tests are `tests/**` and `__tests__/**`. [run: `git diff
--numstat`; the Refactorer's 1,394 → 1,302 and 2,761 → 2,388 match exactly]

S1's commits, oldest first: the five feature commits (`13f4571`, `d10c021`, `6938ba5`, `57c0925`, `0cfb6a2`); the
merges `0f161f8` and `2114d23`; the five on v2.1's rulings (`d74940b`, `f6d8e1e`, `e65335d`, `562c31d`, `a3279be`);
the merge `3fb8f8d` (S2's refactor, at `7f03b56`); the refactor: `a682f6a`, `bf57a3a`, `6b089e5`, `d03ec2c`,
`a910ac9`, `73e47f8`, `fec0b95`, `1c66ce2`, `2fb47b2`, `6dcde3e`, `5b17efd`, `ec95abc`, `ca39def`, `49dda35`; the merge
`cd6cb23` (S2's `d938c90`); and `2675399`. [run: `git log --first-parent`]

Tests: **75** deterministic Python cases, 2 live (`acp_live`), 5 TypeScript (were 88, 2 and 6). [run: collected; TS
read and CI]

---

## 2 · Divergences from the design (v2.2)

The changelog holds no `drift:` line for TASK-3 [run: Notion query of the Changelog's newest entries, 2026-10-04].
V-2 to V-10 come from the refactor, each with the commit that says why.

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
`2675399`, and `{"protocolVersion": 1}` at both with the opt-in off [run: wire probe]. The branch for explicit
capabilities has no caller in the SDK and no test [read]. *Why:* `bf57a3a`.

**V-3 · `SubagentState` keeps no extra keys.** v2.2 §4.2 ("anything else kept"), A.1 (`extra="allow"`), §7.1
(`test_custom_state_is_kept_whole`: "keeps its state and its extra key"). Built: `SubagentState`
(`acp_unstable.py:68–73`) has the library's base config, which ignores unknown keys; a custom state's name is kept
(the merge test's `state-custom` case). Fed two `subagent_update`s whose states carry `x`, `progress`, `_meta` and
`extra`, the bridge stores identical `ACPSubagentEvent`s at `a3279be` and `2675399`, and none holds those keys [run:
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

| v2.2 | Built at `2675399` |
|---|---|
| A.3: `unstable_session_update(session_id, update: SubagentUpdate \| SessionMessage \| SessionMessageChunk)` | `update: UnstableSessionUpdate`, the shim's alias for the same union (`acp_unstable.py:112`) |
| A.2: `before_update` "called before any update for it that is not a text chunk, a message chunk or a usage update" | "Flush `session_id`'s open segment, ahead of an update that ends it" (`acp_subagents.py:194–196`); the bridge flushes before every update but a usage update or a child's text chunk (`acp_agent.py:1754–1759`), so the root's own text ends the root's open chunked message, as §4.3's rule already says |
| A.7: S1's additions to the scripted agent | also eleven wire builders the two sub-agent test files import: `text`, `subagent`, `announce`, `idle`, `tool_call`, `tool_done`, `thought`, `said`, `usage`, `message`, `message_chunk` (`scripted_agent.py:305–386`; `d03ec2c`) |
| §4.1, §7.3, §9 row 15: S1's tests in new files and `test_acp_router.py`; `tests/sdk/test_settings.py` | S1 also edits `tests/conftest.py`: `subagent_snapshots`, and `wait_until` returns the value it waited for (`2fb47b2`); it no longer touches `tests/sdk/test_settings.py` |

**V-7 · The tests v2.2 names.** v2.2's Gate B table, §5.1's "Pinned by" lines and §7 name fifteen Python tests and
one TypeScript test that no longer exist, and two under a class that are now module functions; they count 88
deterministic Python cases (52 in `test_acp_subagents.py`) and 6 TypeScript. Built: 75 (46) and 5, with three new
names from merges and a rename. §8 lists each name and where its property went. *Why:* `a910ac9`, `6dcde3e`,
`ca39def`, `5b17efd`, `bf57a3a`, `6b089e5`. [run: collected]

**V-8 · Three properties §5.1 calls pinned have no test.** Guarantee 9's "Pinned by: the fixture row": that row's
`test_transcript_wait_point_that_is_never_reached_exits_non_zero` is gone, and the transcript player's conformance
rule (no unstable update and no other session's update without `subagents`) lost its only test when the two opt-off
tests became one (P4, P6′). Shim content: a `session_message` with a non-text block no longer has a parse test (P7).
Guarantee 6: the route's 200 is reached only by the cross test (P9). [run: probes, §8]

**V-9 · E5's tree reader places a child by its spawning cell only.** v2.2's Gate B table and §7.2: "Rebuilding the
tree from stored events with §5's rules". Built: `tree_from` (`test_acp_subagents.py:583–633`) keeps rule 2's first
placement; any other placement reads `("unplaced",)` and fails the comparison. Every expected tree places by cell,
so rule 2's fallbacks (first message, then position) are exercised by no test. *Why:* `a910ac9`. [read]

**V-10 · Size.** v2.2's Gate B section, B16 and §11 item 8: 4,155 added and 56 removed, about 14 h at Gate C. Built:
3,690 added and 63 removed (§1, §9), about 12.3 h at ≈300 lines an hour. [run]

**r1's divergences from v1 (D-1 to D-13, v2.2's B-entries) at `2675399`.** Unchanged in behaviour: D-1 (B3: after a
reconnect an idle child whose last snapshot said `cancellable: true` keeps it, while the route answers 409, ruled
acceptable; `seed`, `acp_subagents.py:89–93`) [run: `test_new_connection_withdraws_cancel_and_unconfirms_state`]; D-2
(the opt-in on the agent profile) [run]; D-3 (B4: no trace spans for a child's tool calls, `acp_agent.py:1803`,
`:1863`, `:4199`; unpinned) [read]; D-4 to D-8, D-11, D-12 [read]. Superseded: D-9 and D-10 by V-7, D-13 by V-10.
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
`3fb8f8d` and `2675399` (sha256 `a7a1b5b3…7202c`). [run: route tests, export]

**TypeScript** (`clients/typescript`, unchanged by the refactor): `ACPToolCallEvent` intersected with
`{acp_session_id?, meta?}` (`src/events/types.ts:38`); hand-written `ACPSubagentEvent` (`:189`),
`ACPSessionMessageEvent`, `ACPSessionTextEvent` with guards (`isACPSubagentEvent`, `:316`, and two more);
`ConversationClient.cancelAcpSession` (`src/client/conversation-client.ts:430`) and `RemoteConversation.cancelAcpSession`
(`src/conversation/remote-conversation.ts:363`), both URL-encoding the id; `ACP_SETTINGS_KEYS` gains `acp_subagents`
(`src/models/acp.ts:159`); `ACPAgentProfile.acp_subagents?` (`src/models/agent-profile.ts:80`). [read; CI]

**The scripted agent** (`tests/fixtures/acp/scripted_agent.py`, run by path, imports only `agent-client-protocol`):
S1's flags `--subagents`, `--cancel-wait SECONDS` (0), `--transcript PATH`, `--transcript-interval-ms MS` (0),
`--wait-timeout SECONDS` (30, `DEFAULT_WAIT_TIMEOUT_S`, `:105`), added by `add_subagent_arguments` (`:695`), and the
eleven builders of V-6. [read; run: the tests that use the first three]

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
`sessionId`, is dropped with a WARNING. Two tripwire tests fail once the library parses `subagent_update` or grows
`ClientCapabilities.subagents`. [run: `test_acp_unstable.py`, 6 cases]

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
apart from ids, timestamps, `parent_id` and the root's random session id in two message participants [run: wire
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
golden recordings (`c8d7fbb`) replay through the bridge into stores identical at `a3279be` and `2675399` (§7.4) [run];
`session/cancel` carries the full child id [run: request log; CI: the live stop test]; the live tier passes on dr-acp
[CI]. A dr-acp run killed by a restart replays its children's open cells; E-2's unit test pins that they are not
tracked [run], and no test drives a real replay (§10).

**D5 (desktop app; designed at `design/d5` `8086afb`).** `acp_subagents` on its agent profile, through the resolver
and seed, with a persisted baseline [run]; the scripted agent's `--transcript` mode for its `bridge-replay` job [run];
S1's live file with its two variables, which D5's `fork-live.yml` runs [CI].

**S2.** Owns the emitter, the scripted agent's serving and `acp_router.py`; its recorder stays first in
`session_update` (`:1738`). [read]

---

## 6 · Wiring

**PR #2** at `2675399`: 28 checks, 27 green and `Validate PR description` skipped (draft) [CI]: `Run tests`
([37170487023](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37170487023): `sdk-tests`,
`agent-server-tests`, `cross-tests`, `acp-live-tests`, `tools-tests`, `workspace-tests`, `windows-tests`,
`macos-app-backend-tests`, `agent-server-stress-tests`, `Test directory allowlist`, `coverage-report`); `pre-commit`
(37170487044); `Persisted settings` (37170487009: 19 fixtures validated, both of S1's); `REST API (OpenAPI)`
(37170487020: compared against PyPI 1.50.1 with oasdiff 1.19.1; findings only the additive `oneOf` expansions,
S2's `ACPSessionControlsEvent` and S1's three kinds, at two response-200 locations; passed); TypeScript client CI
(37170486987: `build`, `test (22.12)`, `test (24.x)`, `public-type-budget`, `agent-server-api`, `security`,
`validate-acp-providers`); integration tests (37170487015: `smoke-test`, `integration-test`); `Check package
versions` (37170486981); `endpoint-audit`, `check-docstrings`, `check`. Still outside CI: the SDK API breakage step
(runs only on a version change) and the OpenAPI quality ratchet (no pull-request trigger in the fork); the ratchet
passes here (§7.6).

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
| CI `Run tests` 37170487023 | `2675399` | `pull_request`, ubuntu, Python 3.13.16 | `sdk-tests` **6,749 passed**, 7 skipped, 12 xfailed, 142.3 s; `agent-server-tests` **2,425 passed**, 415.3 s; `cross-tests` **497 passed**, 1 skipped, 157.9 s; `acp-live-tests` 25 passed, 4 skipped, S1's two among the skipped ("not both set"). Each of S1's 75 deterministic cases has its own `PASSED` line [CI] |
| coverage in those jobs | `2675399` | as above | `acp_subagents.py` 96% (uncovered 140 a message's `_meta`; 147, 168, 184 replay or unknown-child returns; 157, 286 non-text blocks; 201 `flush_all`'s body); `acp_unstable.py` 95% (205–206 no `sessionId`; 218, 220); `event/acp_subagent.py` 93%; `acp_router.py` 99% in `agent-server-tests`, missing only 224, the 200 return, which `cross-tests` covers [CI] |
| CI TypeScript client 37170486987 | `2675399` | Node 22.12 and 24.x | **23 files, 359 passed** [CI] |
| live [37171079147](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37171079147), job 111343992767 | SDK `2675399`, deep-reasoning `a8154e2` | started 02:26:53 UTC; ubuntu, Python 3.12.3; dr-acp on gpt-6-luna; suites `s1` (the S2 step skipped) | **2 passed** in 48.26 s (§7.5) [CI] |
| here: S1's SDK files | `2675399` | 4 CPUs, load ≈ 20, serial | `test_acp_unstable.py`, `test_acp_subagents.py`, `test_acp_subagent_events.py`: **61 passed**, 26.2 s [run] |
| here: the shared files | `2675399` | serial | `test_acp_router.py` (S2's tests with S1's 6), `test_check_persisted_settings_compat.py`, and S1's 7 cases in the event-service, dedup, resume-transcript and resolver files: **55 passed**, 66.5 s [run] |
| here: the cross test, alone | `2675399` | serial | **1 passed**, 21.8 s [run] |
| here: `a3279be`'s own tests | `a3279be` (archive) | serial | `test_acp_subagents.py`, `test_acp_unstable.py`: **62 passed**, 36.8 s; the baseline for §8's comparisons [run] |

No run failed, so nothing was rerun. CI's totals fell from `a3279be`'s (6,777, 2,440) with S1's and S2's test cuts
together; I did not separate them. Reproduce: `OPENHANDS_SUPPRESS_BANNER=1 uvx uv@latest run --frozen pytest
tests/sdk/agent/test_acp_unstable.py tests/sdk/agent/test_acp_subagents.py tests/sdk/event/test_acp_subagent_events.py`.

### 7.2 S1's tests, by file

| File | Cases | What they pin |
|---|---|---|
| `tests/sdk/agent/test_acp_unstable.py` | 6 | the two tripwires; the whole `initialize` the agent receives; nine interleaved updates in wire order; a stable update on a child id still parsed by the library; a malformed update dropped with one WARNING. Over a real agent-side `Connection` on a socket pair |
| `tests/sdk/agent/test_acp_subagents.py` | 46 | 33 bridge units (the ten-case merge table, segments, messages, cost, keyed tool calls, the three close-outs, the emitter, replay, reconnect, unannounced sessions, E-1, E-2, E-4); 13 through a real `LocalConversation` on the scripted agent (§7.3) |
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
| `test_subagents_off_stores_only_root_work_through_the_stock_connection` | off, with `--subagents`: the connection is exactly `ClientSideConnection`; `initialize` equals the library's serialization; only `cell-1`, no `acp_session_id`, no new kinds |
| `test_cancel_acp_session_reaches_the_child_without_waiting_for_the_state_lock` | `--cancel-wait 30`, `run()` in a thread: the call that succeeded began while the run held the lock; the run finishes; `session/cancel {sessionId: child-b}` logged; `child-b` idle `cancelled`, `cell-b1` failed |
| `test_cancel_acp_session_for_an_idle_child_that_keeps_its_grant_is_sent` | E-3: the cancel is written; `child-b`'s stored snapshot is unchanged |
| `…_refuses_a_child_without_a_grant` · `…_refuses_unknown_and_root_sessions` · `…_without_a_live_connection_is_refused` | 409-class and no `session/cancel`; 404- and 409-class; 409-class before the first run |
| `test_scripted_transcript_replays_a_recording[full, outgoing-only]` | a recorded turn with two children replays into its tree |
| three ordering tests | §4.4's three facts; the reconnect one drives a second connection whose `session/load` the player refuses, so the bridge falls back to `session/new` |

### 7.4 D1's golden recordings through the bridge

An uncommitted probe replays each of D1's **ten** `tests/acp/golden/*.native.jsonl` at deep-reasoning `c8d7fbb`
(r2 listed nine; `unanswered` was not among them) through `--transcript` into a `LocalConversation` with the opt-in
on, one message per recorded prompt, and compares what is stored at `a3279be` and at `2675399`. [run]

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
passed** in 48.26 s. The assertions are r2's; the refactor moved the file's helpers to `tests/conftest.py`, so both
tests now poll every 0.02 s instead of 0.1 s [read].

| Test | Asserts | Result |
|---|---|---|
| `test_live_agent_tree_is_well_formed` | `run()` on the CS-vs-STAT prompt; within 30 s no child `running`; at least one grandchild; every child's parent is the root or a stored child; every set `parent_tool_call_id` names a stored call of its parent; no child text run of ≥ 40 characters in the answer; the conversation's cost equals the root's last reported cost | passed; prompt returned in 20.2 s |
| `test_live_agent_stops_one_subagent_and_its_branch` | `arun()` under 120 s; on the first grandchild whose parent is `running` and `cancellable`, `cancel_acp_session(parent)` from a thread; that child and its descendants stored idle `cancelled` within 30 s; no non-terminal call of the branch after the branch root's `cancelled` snapshot | passed; prompt returned in 22.4 s |

The run's spend is not printed. [CI]

### 7.6 Upstream guards at `2675399`

| Guard | Result |
|---|---|
| OpenAPI export | byte-identical at `a3279be`, `3fb8f8d` and `2675399`, sha256 `a7a1b5b3b15284008de10c5777f2d0755e82881ffec7e43920c3c62067e7202c`, the Refactorer's `a7a1b5b3…202c` [run] |
| OpenAPI weak-schema ratchet | passes, "65 allowlisted weak locations"; the allowlist is unchanged since `a3279be` [run] |
| REST breakage, persisted settings, TypeScript lint, suite and type budget, pre-commit | green in CI (§6) [CI]; not run here |
| SDK API breakage (Griffe against PyPI 1.50.1) | not rerun; r2 found one upstream error (`ACPAgentSettings.llm`) and nothing of S1's at `a3279be`, and the refactor changes no public signature (§3) [read] |

---

## 8 · What the refactor removed from test coverage

Fifteen Python tests and one TypeScript test that v2.2 names are gone, merged or renamed (13 Python cases fewer),
and two moved out of a class. Each row says where its property is pinned now. Probes are one temporary edit each,
run against the files named, reverted, the worktree clean after each; where a cut test might have pinned the
property, the same edit was run against `a3279be`'s own tests and code. [run]

| v2.2's test (at `a3279be`) | At `2675399` | The property, and what pins it now |
|---|---|---|
| `test_scripted_run_keeps_child_text_out_of_the_answer` | cut (`a910ac9`) | child text never in the root's answer: the bridge unit `test_child_text_never_reaches_the_root_answer` |
| `test_scripted_run_with_subagents_off_stores_only_root_work[--subagents, --transcript]` and `test_subagents_off_uses_the_stock_connection_and_initialize` | merged into `test_subagents_off_stores_only_root_work_through_the_stock_connection`, `--subagents` only (`a910ac9`) | the stock connection and `initialize`, root work only: pinned. **The transcript player's conformance rule** (no unstable update, no other session's update, without `subagents`): **unpinned** (P4) |
| `test_cancel_acp_session_reaches_the_child_and_its_cancelled_state_is_stored`, `test_cancel_acp_session_does_not_wait_for_the_state_lock` | merged into `test_cancel_acp_session_reaches_the_child_without_waiting_for_the_state_lock` (`a910ac9`) | both tests' assertions are in it [read] |
| route `test_a_cancel_reaches_the_child_and_its_cancelled_state_is_stored` | cut (`a910ac9`) | the route's 200 and body: the cross test only (P9) |
| `test_child_cost_is_on_its_association_and_never_booked_to_the_conversation` | renamed `test_child_cost_is_stored_on_its_association_when_it_changes`, booking assertion dropped (`ca39def`) | stored once per change: the unit; never booked: `test_scripted_run_books_only_the_roots_cost` |
| `test_transcript_interval_paces_the_replay` | cut (`6dcde3e`) | pacing: **unpinned now and at `a3279be`** (P5) |
| `test_transcript_wait_point_that_is_never_reached_exits_non_zero` | cut (`6dcde3e`) | a missed wait point fails the script: **unpinned** (P6, P6′) |
| `test_initialize_without_subagent_capabilities_is_the_library_call` | cut with its branch (`bf57a3a`) | the opt-off `initialize`: the merged opt-off conversation test |
| `test_custom_state_is_kept_whole` | cut with `extra="allow"` (`6b089e5`) | a custom state's name: the merge table's `state-custom` case; extra keys are no longer kept (V-3) |
| `test_patch_fields_tell_omitted_from_null` | cut (`a910ac9`) | the merge table (P8) |
| `test_message_content_keeps_non_text_blocks_typed` | cut (`a910ac9`) | **a `session_message` with a non-text block parses: unpinned** (P7) |
| `test_root_tool_call_event_is_stored_as_before` | cut (`a910ac9`) | the model's `meta` default: `test_legacy_acp_tool_call_event_loads_without_session_fields` (P3b); the bridge leaving a root call's `meta` unset: unpinned, and was at `a3279be` (P3) |
| `test_acp_create_agent_forwards_subagents` | cut (`a910ac9`) | the resolver test, which builds the agent (P2) |
| `TestEventServiceCancelACPSession::…` (2) | module functions (`5b17efd`) | off-the-loop now pins that the loop keeps running while the cancel blocks, not a thread id |
| TS `sub-agent event shapes accept stored events` | cut (`a910ac9`) | the stored shapes: the guards' test |

| Probe | The temporary edit | At `2675399` | At `a3279be` |
|---|---|---|---|
| P1 | `_PER_EVENT_FIELDS` without `parent_id` (a snapshot keeps a stored event's place in the conversation tree) | **caught**: `test_new_connection_withdraws_cancel_and_unconfirms_state`, `test_partial_patch_after_reconnect_keeps_the_stored_title` | — (no such field) |
| P2 | `create_agent()` stops forwarding `acp_subagents` | **caught**: `test_acp_profile_carries_the_subagents_opt_in_to_the_agent[True]` | — |
| P3 | the bridge stores a root call with `meta={}` | not caught (624 cases: S1's SDK files, `test_acp_agent.py`, dedup, resume transcript) | not caught by the cut test either, which built the event itself [read] |
| P3b | `ACPToolCallEvent.meta` defaults to `{}` | **caught**: the legacy-load test | — |
| P4 | the transcript player plays everything without `subagents` | not caught (S1's 46 and the cross test) | **caught**: `…_off_stores_only_root_work[--transcript]` |
| P5 | the player ignores `--transcript-interval-ms` | not caught; no test passes the flag | **not caught**: the unpaced run took 1.47 s against the test's floor of 15 × 50 ms |
| P6 | a missed wait point returns instead of raising | not caught | not caught: the script still exits non-zero, through a `KeyError` in `_respond` |
| P6′ | the wait timeout is ignored | not caught | **caught**: `test_transcript_wait_point_that_is_never_reached_exits_non_zero` |
| P7 | `SessionMessage.content` accepts text blocks only | not caught (S1's 61) | **caught**: `test_message_content_keeps_non_text_blocks_typed` |
| P8 | a `null` title treated as omitted | **caught**: the merge table's `title-null` | — |
| P9 | the route answers 200 with `requested: false` | **caught by the cross test only**; the route and service files pass (48) | — |
| P10 | `replaying()` never clears the flag | **caught** by the reconnect conversation test only; the two replay units pass | — |

Plainly: three properties lost their only test, the transcript player's conformance rule (P4), its wait timeout
(P6′) and the parse of a message with a non-text block, without which such a message is dropped whole, text included
(P7). Pacing was never pinned (P5). The route's success path is reached only through the cross test (P9). The
create-agent forwarding, the omitted-versus-null merge, the model default and the replay flag stay pinned by other
tests (P2, P8, P3b, P10), and the refactor added one pin (P1).

---

## 9 · Size, and what resisted compression

S1 is +1,302 −54 of source (Python product code +1,143 −52, was +1,235 −49; TypeScript +112 −2) and +2,388 −9 of
tests and fixtures (deterministic Python tests +1,618, was +1,942; the live file 188, was 207; the scripted agent
+442 −4, was +459 −4). [run: `git diff --numstat`] About 12.3 h at Gate C at ≈300 lines an hour, against 14 h before.
The parts of this document that will not shrink are §2 and §8: the refactor is mostly test cuts and renames, and each
one changes a line v2.2 states or a property a consumer reads.

---

## 10 · What I could not verify

1. **The live tier's cost**: no amount is printed [CI].
2. **A real `session/load` replay of sub-agent traffic.** The replay flag is pinned by units that enter `replaying()`
   and, for clearing it, by the reconnect test, whose `session/load` the transcript player refuses; no agent replays
   sub-agent traffic in any test or probe.
3. **`arun()` interleaving at `2675399`**: measured in r2 at `a3279be` only; the code it depends on is unchanged
   [read].
4. **Each commit green on its own**, and whether S1's commits cherry-pick onto `main`: CI ran only at the head.
5. **Not run here**: the TypeScript suite and lint, pre-commit and pyright, and the REST breakage script, which CI ran
   green (§6); and the SDK API breakage check, which nothing ran at `2675399`.
6. **Paths read but not seen run**: a notification without `sessionId` (uncovered in CI); a message's `_meta` and
   non-text blocks; an emitter's exception swallowed per event; the turn-end flush of a still-open segment (`flush_all`'s
   body, uncovered in CI; r2's probe ran it at `a3279be`); the explicit-capabilities branch of `initialize`; the
   Python `RemoteEventsList` reordering; masking of `meta`.
7. **The opt-in from a profile through a real agent-server launch**: the resolver, seed and baseline are checked; no
   run started a conversation from such a profile.
8. **Canvas** (C1) is not built; §5 checks the stored shapes against C1's design, not Canvas code.
9. **The Refactorer's claims**: all checked and holding (lines, the OpenAPI hash, the wire, the stored events with
   extra state keys, the 23 sub-agent notifications of the `--subagents` turn, the moved names, 88 → 75 with 2 live,
   the route's 200 in the cross test only). The one qualification: "always advertises `subagents`" holds unless a
   caller passes other capabilities, which no caller in the SDK does (V-2).
