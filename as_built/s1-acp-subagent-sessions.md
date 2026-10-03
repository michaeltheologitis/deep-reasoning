# S1 · ACP sub-agent sessions in the agent-server, as built

**TASK-3** · Cartographer · the code at `a3279be`, head of `feat/acp-subagent-sessions` in the SDK fork
[michaeltheologitis/software-agent-sdk](https://github.com/michaeltheologitis/software-agent-sdk) (draft PR #2 into
`feat/agent-surfaces`, S2's head `5e3317f`; S1 is `5e3317f..a3279be`) · checked against the design at `e05986f`
(`docs/design/s1-acp-subagent-sessions.md` v2.2, on this branch, which matches `a3279be`); §2.2–§2.6's divergences
were found against v1, `f956fda` · agent-client-protocol 0.12.1 (the fork's lock) · uv 0.12.23
(`uvx uv@latest`), Python 3.13.14 and Node 22.22 in this sandbox · 2026-10-03.

**This revision** (r2) re-reads the code at `a3279be`; r1 (`17ab4d5`) read `0cfb6a2`. Between them: the four edges
r1 found are fixed or pinned, the persisted agent-profile fixture is added, and S1 merged S2's new head and the fork's
`deep-reasoning` (which now runs upstream's main-only guards on PR #2). The design's v2.2 (`e05986f`) has since
absorbed those changes; §2.1 is what v2.2 still states differently from the code. Every count, line number and run
below is `a3279be`'s unless it says otherwise.

**Where this file lives.** On deep-reasoning's branch `as-built/s1`, reset to `design/s1` at `6402969`: S1's code
is in the SDK fork, whose branches carry only upstream-shaped code, so no document of ours goes there. This branch
has no `pyproject.toml`, no docs site and no test runner, so nothing builds an sdist or collects `as_built/`, and
there is nothing to wire. [run: `git ls-tree -r HEAD`]

**Evidence marks.** Every claim carries one.
- **[run]**: executed in this sandbox, without writing tracked files in the checkout: S1's Python test files (§7.1),
  upstream's guard scripts, and uncommitted probe scripts in my scratchpad that drive a real `LocalConversation`
  against the scripted ACP agent, or feed the bridge directly; and, for the fixes, the new tests run against a
  `git archive` of `0cfb6a2`. No model; network only for PyPI baselines.
- **[CI]**: read from GitHub's records through the MCP tools: PR #2's 28 checks at `a3279be` (the REST breakage
  job in both its attempts) and the live run
  [37147706623](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37147706623). Log tails only (§9).
- **[read]**: read in the code, **not executed**. Weaker than [run]; §9 lists the read claims that matter.

Nothing in this document ran a paid model or the `claude` CLI; the live tier is reported from CI.

**Reading order.** §2 first (§2.1 is where the design's v2.2 and the code still differ), then §1, §3 and §4 as the
map, §5 for what C1, D1 and D5 rely on, §7 for the measurements, §9 for what I could not verify.

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
_OpenHandsACPBridge.session_update (acp_agent.py:1736)
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

| Part | Lines (`5e3317f..a3279be`) | Where |
|---|---|---|
| the shim | 247, new | `openhands-sdk/openhands/sdk/agent/acp_unstable.py` |
| the router | 338, new | `openhands-sdk/openhands/sdk/agent/acp_subagents.py` |
| bridge and agent | +317 −40 | `openhands-sdk/openhands/sdk/agent/acp_agent.py` |
| events | +177 | `event/acp_subagent.py` (160, new), `event/acp_tool_call.py`, `event/__init__.py` |
| other SDK consumers | +79 −8 | local and remote conversation, visualizer, resume transcript, settings, three profile files |
| agent-server | +77 −1 | `acp_router.py`, `event_service.py` |
| TypeScript client | +112 −2 source, +27 config | `clients/typescript/src/…`, `endpoint-audit.config.json`, `config/public-type-budget.json` |
| tests | Python +2,149, scripted agent +459 −4, persisted baselines +27, TypeScript +126 | `tests/…`, `clients/typescript/src/__tests__/…` |
| CI config | +20 | weak-schema allowlist (+18), `.github/workflows/tests.yml` (+2) |

Total +4,155 −56 in 43 files. [run: `git diff --numstat 5e3317f a3279be`] S1's commits, oldest first: the five
feature commits, with design §8's titles word for word, `13f4571` (the shim), `d10c021` (events), `6938ba5` (bridge,
settings, profiles, scripted agent, SDK and live tests), `57c0925` (the cancel route), `0cfb6a2` (TypeScript); two
merges, `0f161f8` (the fork's `deep-reasoning` at `1f2b52d`) and `2114d23` (S2's `feat/agent-surfaces` at `5e3317f`;
the scripted agent's flags conflicted and S2's come first); and five after r1: `d74940b` (E-2), `f6d8e1e` (E-1),
`e65335d` (E-3's test), `562c31d` (E-4's warning), `a3279be` (the profile fixture). [run: `git log`]

Tests added: 90 Python cases (88 deterministic, 2 marked `acp_live`) and 6 TypeScript. [run: collected]

---

## 2 · Divergences from the design

The changelog holds no `drift:` line for TASK-3 [run: Notion query of the Changelog, r1], so every item was found
from the code. The design has four revisions on this branch: v1 `f956fda` (before the build), v2 `73768e3` ("in
line with the build at `0cfb6a2`"), v2.1 `9fd2c92` (r1's thirteen divergences mapped onto its §3.2 as B1–B17, and
r1's four edges ruled as E-1 to E-4) and v2.2 `e05986f` ("Matches the build at `a3279be`": the fixes, the fixture,
the guards in CI, the counts). §2.1 compares `a3279be` with v2.2; §2.2–§2.6 keep r1's comparison with v1, each item
with the B-entry that carries it in v2.2 and its state at `a3279be`.

### 2.1 Against v2.2: what it still states differently

v2.2 absorbs everything r2's first draft listed against v2.1: E-2's fix (B5, §5.1 guarantee 7), E-1's fix (its
§5.1 note), E-3's test, E-4's warning, the persisted profile fixture (B2, §11 item 11), the guards now in CI (B14,
§11 items 8, 9, 13), the counts (88 deterministic Python cases, 52 in `test_acp_subagents.py`) and the size (+4,155
−56 in 43 files); its *(v2.2)* notes cite `a3279be`'s line numbers, which match the code. [read: the design at
`e05986f`; run: the code] One point remains:

- **V-1 · E-4's warning, in two of v2.2's sentences.** The Gate B section ("E-4 in `562c31d` (one warning per
  unannounced session)") and §5.1's E-4 note ("the bridge warns once per such session") say one warning per
  session. Built, and as v2.2's own §3.2 E-4 note says: one warning per session **per path**, since
  `_warn_once_for_unannounced_unstable_traffic` (`acp_agent.py:1639–1656`) keeps its own set,
  `_unannounced_unstable_sessions` (`:1455`), apart from the stable path's `_unannounced_sessions` (`:1454`); a
  session that sends both kinds of update draws two WARNINGs. Neither v2.1's ruling ("one WARNING names the
  session") nor v2.2 says how the session is named: the warning carries its fingerprint
  (`_fingerprint_session_id`), not its id, and the test asserts the fingerprint. [run:
  `test_unstable_updates_on_an_unannounced_session_stay_under_that_session`; read: the two paths]

### 2.2 v1 against the build: behaviour a client or a consumer sees

**D-1 · A reconnect writes "state unconfirmed, cancel withdrawn" snapshots only for children last seen active.**
`ACPSubagentSessions.seed` returns an `environment` snapshot for each stored child whose latest snapshot has a
`state` other than `None` and `"idle"` (`acp_subagents.py:104–108`); `cancellable` plays no part. v1 (§1.3 H, §2,
§3 item 7, §4.3): "cancellable **or** active". So a child whose last snapshot was `idle` and `cancellable: true`
(every finished dr-acp child, since D1 keeps `capabilities.cancel` on idle children) keeps `cancellable: true` in the
store after a reconnect, while the route answers 409 for it. Reason: C1 design v2 §9.1 item 4. *v2.2: B3, ruled
acceptable against C1's Stop rule. At `a3279be`: unchanged.* [run:
`test_new_connection_withdraws_cancel_and_unconfirms_state`]

**D-2 · The opt-in also lives on `ACPAgentProfile`** (`profiles/agent_profile.py:292`), forwarded by the resolver
(`profiles/resolver.py:305`) and carried back by the seed (`profiles/seed.py:58`); the TypeScript `ACPAgentProfile`
gains `acp_subagents?: boolean`. v1 §4.6: `ACPAgent` and `ACPAgentSettings` only. Reason: Canvas starts conversations
from the active agent profile, and `ACPAgentProfile` forbids unknown keys (C1 §9.1 item 1, D5 §8.2). *v2.2: B2. At
`a3279be`: the persisted-profile fixture both asked for is built: `tests/sdk/persisted_settings_baselines/v2/
agent_profile_acp_subagents.json` (`a3279be`), a minimal ACP profile at profile schema 2 with the opt-in on.* [run:
the two resolver tests; the guard validates 19 fixtures, this one among them; CI: the same]

**D-3 · Child tool calls get no observability spans.** The bridge opens and closes `ACPTurnTrace` tool spans only for
root calls (`acp_agent.py:1814`, `:1874`), and `finish_turn` receives only root calls (`:4225–4233`). v1 §4.4 does not
mention the trace. No reason recorded. *v2.2: B4, unpinned. At `a3279be`: unchanged.* [read]

### 2.3 v1 against the build: where the code landed

**D-4 · S1 is stacked on S2 and owns none of the shared pieces.** v1 §8 cut the branch from `91430aa`. Built: S1 is
on S2's `feat/agent-surfaces`; S2 owns the out-of-turn emitter (`_emit_event_from_any_thread`, wired in
`_ensure_agent_ready`, `local_conversation.py:1578`), the scripted agent's `Connection`-based `serve`, and
`acp_router.py` with `conversation_acp_router`. S1's start hunk sits in `_launch_acp_session` (`acp_agent.py:3326`),
S2's split of `_start_acp_server`. *v2.2: B1. At `a3279be`: S1 merged S2's new head `5e3317f` (`2114d23`).* [run:
`git log`, `git merge-base`]

**D-5 · The draft PR targets `feat/agent-surfaces`, not the fork's `main`.** v1 §8: a draft PR to `main`. At
`0cfb6a2` upstream's main-only guards therefore did not run in CI. *v2.2: B14. At `a3279be`: the fork-only `1f2b52d`
runs them on pull requests into the fork's branches, and on PR #2 the REST breakage check, persisted settings and the
TypeScript client's CI and integration tests ran green. The REST breakage check compared against PyPI 1.50.1 only in
its second attempt, after the `v1.50.1` tag was pushed to the fork (§6). Still outside CI: the SDK API breakage step
(skipped without a version change) and the OpenAPI quality ratchet (no pull-request trigger); I ran both here
(§7.6).* [CI; run]

### 2.4 v1 against the build: the scripted agent

**D-6 · `--transcript-interval-ms MS`** (`scripted_agent.py:33`, `:718`), from C1 §9.1 item 2. *v2.2: B8.* [run:
`test_transcript_interval_paces_the_replay`]

**D-7 · The `--subagents` run's order differs in detail** (`play_subagent_run`, `scripted_agent.py:371`): `child-a`
sends two thoughts (stored as one run); its grandchild runs while `cell-a1` is open (v1: `cell-a1` completes, then the
grandchild runs); the root's 0.0011 USD `usage_update` follows S2's reply text. The tree, ids, titles, grants and
costs are v1 §4.10's. *v2.2: B9.* [read; the stored result run in §7.2]

**D-8 · An outgoing-only transcript whose responses are not `initialize`, `session/new` or `session/prompt` is
refused** by `_inferred_method` (`scripted_agent.py:484–497`) before the script serves. All nine of D1's native
golden recordings hold only those three shapes. *v2.2: B10.* [run: §7.3]

### 2.5 v1 against the build: tests, the live tier and size

**D-9 · Tests moved, renamed, or tested through a real server.** The schema test is
`tests/agent_server/test_acp_router.py::test_stored_sub_agent_events_validate_against_the_event_schema` (events read
over the REST page of an in-process agent-server app with a real `ConversationService` and the scripted agent as a
subprocess); the transcript test is `test_scripted_transcript_replays_a_recording[full, outgoing-only]`; the route
tests use that in-process app, S2's fixture, not a mocked event service, under other names (§7.5); the root's 409 is
tested at the SDK level only. *v2.2: B12.* [run]

**D-10 · Tests beyond v1 §7:** `test_custom_state_is_kept_whole`, `test_message_content_keeps_non_text_blocks_typed`,
`test_scripted_run_books_only_the_roots_cost`, `test_transcript_interval_paces_the_replay`,
`test_transcript_wait_point_that_is_never_reached_exits_non_zero`, the three ordering tests C1 §9.1 item 3 asked for
(v2 states them as §5 rule 10), two visualizer tests, `test_cancel_acp_session_on_an_inactive_service_is_refused`,
`test_acp_seeded_profile_keeps_the_subagents_opt_in`, the TypeScript `each guard recognises only its own kind`, and,
since r1, the four edge tests v2.1 named (§4.5). *v2.2: B11, B12, E-1 to E-4.* [run]

**D-11 · The live tier asserts less than v1 §7.4 in one place and differently in another.**
`test_live_agent_tree_is_well_formed` does not assert "every child that reported a cost has it on its association";
its "no child text in the answer" checks child text runs of 40 characters or more (`QUOTED_TEXT_MIN_CHARS`,
`test_acp_subagents_live.py:46`); it requires a grandchild. The fork's `acp-live-tests` job lists the file and skips
it without its variables. *v2.2: B13.* [read; CI]

**D-12 · Upstream guard data v1 did not list:** the TypeScript public weak-type budget's `acp-protocol-meta` category
(three `meta` sites); the OpenAPI allowlist has three entries, no `-Input`/`-Output` twins. *v2.2: B15.* [run: the
ratchet passes, §7.6]

**D-13 · Size: about 2.3 times v1's estimate** (≈1.8k with tests): +4,155 −56. Product code is near its estimates
except the bridge (`acp_agent.py` +317 −40 against +100); the excess is in the tests (Python +2,149 against 750, of
which `test_acp_subagents.py` is 1,241) and the scripted agent (+459 against +180). *v2.2: B16, for Michael to rule
on.* [run: `git diff --numstat`]

### 2.6 Small differences from v1

None changes what §2.2 describes. *v2.2: B6, B7.* [read unless marked]

| v1 | Built at `a3279be` |
|---|---|
| router field `_warned: set[str]` (§4.3) | two bridge sets: `_unannounced_sessions` (`acp_agent.py:1454`) for stable traffic and `_unannounced_unstable_sessions` (`:1455`) for unstable traffic, one WARNING per session per path [run: tests] |
| `root_session_id` set "after the session is resolved" (§4.4) | set to the prior id in `_load_session` before `session/load` (`:5101–5123`), and to the new id in the `session/new` branch (`:3684`); same outcome on every path |
| the shim drops an invalid update with a WARNING (§4.2) | also drops a notification without a `sessionId` (`acp_unstable.py:227–229`), untested |
| `cancel_acp_session` with the opt-in off: not specified | `ACPSessionNotFoundError` (404) once a session is live; `ACPSessionNotCancellableError` (409) before (`acp_agent.py:5079–5082`) |

Not divergences: the shim (v1 §4.2, A.1) with its one pyright suppression (`acp_unstable.py:156`) and one
private-attribute touch (`self._conn._handler`, `:170`); v1 §4.3's merge, segment, message, cost and replay rules; the
bridge hunks of v1 §4.4 other than D-3 and the E-1 and E-2 fixes (§4.5); the event models of A.4 field for field; the route's statuses and
`detail` texts of v1 §4.7; the consumers of v1 §4.8; the TypeScript surface of v1 §4.9 and A.6; the v7 fixture of v1
§4.6 byte for byte. [read; the behaviours run in §7]

---

## 3 · The public surface, from the code

**The opt-in.** `ACPAgent.acp_subagents: bool = False` (`acp_agent.py:2239`), `ACPAgentSettings.acp_subagents`
(`settings/model.py:1754`, forwarded by `create_agent()` at `:1967`), `ACPAgentProfile.acp_subagents` (D-2). No
`SETTINGS_METADATA_KEY`, so it is not in the settings form; `AGENT_SETTINGS_SCHEMA_VERSION` stays 7, the agent-profile
schema stays 2, and two baselines pin a stored `true`: `v7/agent_settings_acp_subagents.json` and
`v2/agent_profile_acp_subagents.json`. The field rides on the serialized agent, so `ConversationInfo.agent` carries
it. [read; run: settings guard, oasdiff §7.6]

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

**TypeScript** (`clients/typescript`, unchanged since `0cfb6a2`): `ACPToolCallEvent` is the generated type
intersected with `{acp_session_id?, meta?}`; hand-written `ACPSubagentEvent`, `ACPSessionMessageEvent`,
`ACPSessionTextEvent` in the `ConversationEvent` union with guards `isACPSubagentEvent`, `isACPSessionMessageEvent`,
`isACPSessionTextEvent`; `CancelAcpSessionResponse`; `ConversationClient.cancelAcpSession(conversationId,
sessionId)` and `RemoteConversation.cancelAcpSession(sessionId)`, both URL-encoding the session id;
`ACP_SETTINGS_KEYS` gains `acp_subagents`; the route is an `allowClientOnly` entry in the endpoint audit. [read; run
in r1; CI: the client's suite at `a3279be`, §7.1]

**The scripted agent** (`tests/fixtures/acp/scripted_agent.py`, run by path): S1's flags `--subagents`,
`--cancel-wait SECONDS` (default 0), `--transcript PATH`, `--transcript-interval-ms MS` (default 0),
`--wait-timeout SECONDS` (default 30), after S2's flags. It imports only `agent-client-protocol`. [read; run: tests]

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
- **Merge.** Omitted keeps, `null` clears, a value replaces; `capabilities` grants iff `cancel` is an object;
  `parent_tool_call_id` is lifted from `_meta.openhands.parentToolCallId` and is sticky. `title`, `description`,
  `meta` and all stored text pass through the bridge's secret masking. [run: the ten-case parametrized test; masking
  of a title and of child text by a probe, §4.3]
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

+317 −40 lines spread through `acp_agent.py` (5,307 lines at `a3279be`), the file upstream changes most. [run: `wc`,
`git diff --numstat`]

- **Diversion** (`:1764–1772`). After S2's controls recorder and the `ask_agent` fork branch, `_child_session`
  returns the id of a known child, else `None` (warning once for an id that is neither root nor child). With the
  opt-in on, every update except a usage update or a child's text chunk first flushes its session's segment. For a
  child, `_route_child_update` (`:1700`) drops everything while `replaying` (E-2's fix, §4.5), sends text and usage to the router,
  drops its plans and other updates with a DEBUG line, and lets its tool calls through. [run: tests]
- **The unstable path** (`unstable_session_update`, `:1620`): idle clock, fork check, the warn-once for an
  unannounced session (E-4, §4.5), the router, the emitter. [run: tests]
- **The shared tool-call path.** Entries carry `acp_session_id` and (opt-in on) `meta`, are masked, and are matched
  by `(tool_call_id, acp_session_id)`; `_emit_tool_call_event` (`:1881`) sends a child's call to the emitter and a
  root call to the turn's `on_event`, which is unset between turns, as before. [run: tests]
- **Three close-outs.** `reset()` (`:1460`) keeps child entries that are not terminal, so a child's cell can outlive
  the turn; the successful turn's force-complete skips child entries (`:3895`); an aborted turn's
  `_cancel_inflight_tool_calls` (`:3820–3876`) emits a synthetic `failed` for every open entry not yet failed, child
  entries through the emitter so they follow the call's own `started` event, and marks each child entry it failed
  (E-1's fix, §4.5). [run: tests]
- **Turn end.** `_do_acp_prompt`, on the ACP loop, submits every open segment after the usage wait (`:4111`), on
  both the `run()` and the `arun()` path. [run: a probe transcript whose child's last update before the prompt
  response is a thought: it is stored as one `ACPSessionTextEvent` after the turn, and a secret registered on the
  conversation reads `<secret-hidden>` in that text and in the child's stored title. CI's coverage does not reach this
  path, §7.1]
- **Connection start.** `_launch_acp_session` builds the bridge with `subagents=self.acp_subagents`, hands it the
  conversation's emitter, seeds the router from `state.events` and submits the reset snapshots (`:3326`), all before
  the subprocess starts; then the shim connection (`:3473`), the `initialize` with the capability, and
  `_load_session` (`:5101`), which sets `replaying` around `session/load`. [read; seed run in tests]

### 4.4 Threads, order and what the store holds

The portal (ACP loop) thread only submits child events; S2's single worker stores them under the state lock. Root
events keep the turn's synchronous path. Measured with the scripted agent (`--subagents --cancel-wait 2`, sampling
the store every 0.1 s): under a synchronous `run()`, which holds the lock for the whole step, none of the 9 child
snapshots is stored before the turn's `FinishAction`; under `arun()`, 8 of 9 are stored while the turn is still
running. [run: probe, at `0cfb6a2` and again at `a3279be`] So in the log, children follow the root's events of the
same turn under `run()`, and interleave under `arun()` only when the turn lasts long enough; within one child the
order is always wire order.

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

### 4.5 The edges r1 found, and where they stand

r1's probes at `0cfb6a2` found four behaviours no test pinned; v2.1 ruled on each (its §3.2 E-1 to E-4). At
`a3279be` each is built or pinned with the test v2.1 named, word for word. Each new test was also run against a
`git archive` of `0cfb6a2` with `a3279be`'s test file. [run]

| Edge (r1, at `0cfb6a2`) | v2.1's ruling | At `a3279be` | Test | On `0cfb6a2`'s code |
|---|---|---|---|---|
| **E-1** a child call open across aborted turns is failed once per turn (`in_progress, failed, failed, completed`) | defect; fix with E-2 | fixed, `f6d8e1e`: `in_progress, failed, completed` | `test_child_call_open_across_aborted_turns_is_failed_once_and_the_agents_report_wins` | fails |
| **E-2** a child call replayed by `session/load` and left open is stored as `failed` at the next aborted turn | bug; fix before Gate B | fixed, `d74940b`: no entry, nothing stored | `test_replayed_child_calls_are_never_tracked_nor_failed_later` | fails |
| **E-3** a second cancel to an idle child that keeps its grant is accepted | acceptable, stated | unchanged, pinned, `e65335d`; three probe trials accept it | `test_cancel_acp_session_for_an_idle_child_that_keeps_its_grant_is_sent` | passes |
| **E-4** unstable updates on an unannounced session stay under its id, without a WARNING (read) | acceptable; WARNING wanted, not required | WARNING added, `562c31d` (V-1); routing unchanged | `test_unstable_updates_on_an_unannounced_session_stay_under_that_session` | fails |

How each is built [read; each behaviour run by its test and, for E-1 and E-2, by r1's probes, which now give
`in_progress, failed, completed` and an empty accumulator with nothing stored]:

- **E-2** (`d74940b`, the first of v2.1's two options): `_route_child_update` (`acp_agent.py:1700–1708`) returns while
  `replaying` before the tool-call branch, so a child's replayed `tool_call` or `tool_call_update` is neither tracked
  nor stored, and a later live update for that call finds no entry and stores nothing, as for a root call. On
  `0cfb6a2`'s code the test fails because the accumulator holds the replayed entry.
- **E-1** (`f6d8e1e`): `_cancel_inflight_tool_calls` (`:3820–3876`) marks a child entry `failed_by_abort` once its
  synthetic failure is emitted (`:3868`) and skips marked entries afterwards (`:3845`), across aborted turns and
  across retries within one; the entry stays open, so the agent's later report lands last. On `0cfb6a2`'s code the
  test fails with `failed, failed, completed`.
- **E-3** (`e65335d`): no code change; a cancel for an idle child that keeps its grant writes `session/cancel` and
  stores nothing new.
- **E-4** (`562c31d`): `unstable_session_update` (`:1620`) calls `_warn_once_for_unannounced_unstable_traffic`
  (`:1639–1656`), one WARNING per session per path, naming the session by fingerprint (V-1); routing is unchanged.
  `test_child_is_never_reparented_nor_its_own_parent` now counts only the router's three refusals. On `0cfb6a2`'s code
  the test fails: no WARNING.

One edge r1 read and nobody changed: the Python `RemoteEventsList` cache merges an ACP call's two events in place, so
its order can differ from the server's log when child traffic interleaves; the cross test checks order on the REST
log. [read: PR #2's notes, the cross test's comment]

---

## 5 · What each consumer relies on

**C1 (Canvas fork; designed at `design/c1` `88f5c43`, not built).** C1 reads stored events only, through design §5
and §5.1 (tree by latest snapshot, placement by `parent_tool_call_id` then first message then position, per-session
transcripts keyed `(acp_session_id, …)`, state, cost never added, Stop only for `cancellable` and `running` or
`requires_action`, `source == "environment"` as unconfirmed history). As built, the stored shapes and rules hold
[run: `tree_from` in the E5 tests implements these rules over stored events, §7.2]. C1 also relies on: the three
ordering facts of §4.4 (its decision C orders by timestamp) [run]; storage with `exclude_none`, so unset fields arrive
as absent keys [run: the dump test; read: `event_store.py:225`]; the 409 `detail` text, shown verbatim [run];
`cancelAcpSession`, the three types and guards, and `ACP_SETTINGS_KEYS` with `acp_subagents` in the TypeScript client
[run in r1; CI]; the profile field and its baseline for its launches [run]; and the scripted agent by path from a fork
checkout, with `--subagents --cancel-wait N`, `--transcript` and `--transcript-interval-ms` [run]. All four of C1's
asks (§9.1) are built: item 1 with its fixture (D-2), item 2 (D-6), item 3 as tests and as v2's §5 rule 10
(D-10), item 4 (D-1).

**D1's `dr-acp`.** S1 relies on D1's contract as design §10 lists it: each child announced on its parent's session
before its traffic, with `_meta.openhands.parentToolCallId` naming a cell already sent (ids `<run>-n<node>`, cells
`<run>-n<node>-c<k>`, path-safe); `capabilities.cancel` on every child; reasoning and the Stop acknowledgement as
`agent_thought_chunk`s on the child's session (stored as `ACPSessionTextEvent`); goldens replayable as they are; no
child traffic after the prompt response. All nine native goldens replay through the bridge into the recorded tree
[run: §7.3], and the live tier passes on dr-acp [CI: §7.4]. D1 in turn relies on S1 putting `subagents` on the wire
as an object (D1 turns native mode on iff `clientCapabilities.subagents` is an object, read from D1's as-built §3)
[run: `test_initialize_puts_subagents_capability_on_the_wire`] and on `session/cancel` carrying the full child id
[run: the scripted agent's request log; CI: the live stop test]. A dr-acp run killed by a restart replays its
children's open cells (v2.1's E-2); after `d74940b` the bridge neither tracks nor stores them [run: the E-2 unit test; read:
no real replay drives it, §9 item 3]. The compatibility fact underneath: agent-client-protocol 0.12.1 rejects the
unstable types and marks `ClientSideConnection` `@final`, so the shim subclasses it with one suppression [run: the
tripwires; read: `acp/client/connection.py:109`].

**D5 (desktop app; designed at `design/d5` `8086afb`).** D5 turns sub-agent sessions on for `deep_reasoner`; they
are off by default [run: `test_acp_create_agent_forwards_subagents`]. It relies on: `acp_subagents` on the agent
profile it owns, through the resolver and back through the seed, now with a persisted-profile baseline (D-2),
and a 422 fallback on servers without it [run: resolver tests, the guard; the fallback is D5's]; the scripted agent's
`--transcript` mode for E5's `bridge-replay` job against D1's goldens [run: §7.3, with my own comparator, not D5's
`testing.tree()`]; and S1's live file with its two variables, which D5 §7.4's `fork-live.yml` runs [CI: §7.4].

**S2.** Shares the emitter, the scripted agent and `acp_router.py`, all S2's (D-4). S2's controls recorder stays
first in `session_update`, so commands and options never reach S1's diversion. [read]

---

## 6 · Wiring

**PR #2** (draft, `feat/acp-subagent-sessions` → `feat/agent-surfaces`): 28 checks at `a3279be`, 27 green and
`Validate PR description` skipped [CI]:

| Workflow (run) | Jobs | What it checks for S1 |
|---|---|---|
| Run tests (37146975823) | `sdk-tests`, `agent-server-tests`, `cross-tests`, `acp-live-tests`, `tools-tests`, `workspace-tests`, `windows-tests`, `macos-app-backend-tests`, `agent-server-stress-tests`, `Test directory allowlist`, `coverage-report` | S1's tests; counts in §7.1 |
| Pre-commit checks (37146975749) | `pre-commit` | ruff, pycodestyle, pyright, the forbidden-dynamic-attribute, import-rule and tool-registration checks |
| Persisted settings (37146975832) | `Persisted settings` | 19 fixtures (both of S1's) and 8 PyPI 1.50.1 baselines validated, on PR #2's merge commit `464c710` |
| REST API breakage (37146975811) | `REST API (OpenAPI)`, two attempts | Attempt 1 (job 111272841546): green without comparing, since the fork did not carry the baseline tag ("Failed to extract source for v1.50.1 … not a valid object name"), after which the script exits 0 by design. Attempt 2 (job 111276572426), after `v1.50.1` was pushed to the fork: the tag fetched, oasdiff 1.19.1 ran against PyPI 1.50.1's schema, and the check passed. Its findings, each listed as allowed ("additive response oneOf expansions"): `ACPSessionControlsEvent` (S2's), `ACPSessionMessageEvent`, `ACPSessionTextEvent` and `ACPSubagentEvent` added to the `Event` `oneOf` at two response-200 locations (the events list and the single event); and `darwin-amd64` and `darwin-arm64` (the fork's macOS App backends, not S1's) added to the Canvas extension manifest's backend-artifacts enum, six lines at three response locations. Both attempts wrote the REST contract summary into PR #2's description |
| TypeScript client CI (37146975745) | `build`, `test (22.12)`, `test (24.x)`, `public-type-budget`, `agent-server-api`, `security`, `validate-acp-providers` | the client's 23 files, 361 tests, lint 0 errors, prettier, the type budget |
| TypeScript client integration tests (37146975836) | `smoke-test`, `integration-test` | green |
| Version bump guard (37146975831) | `Check package versions` | green; its SDK API breakage step ("Check Python API compatibility") was skipped, as it runs only when a package version changes |
| Endpoint audit, docstrings, deprecation deadlines | `endpoint-audit`, `check-docstrings`, `check` | green |

Still not run in CI on PR #2: the SDK API breakage check (above) and the OpenAPI quality ratchet, which runs in
`server.yml` (`make test-server-schema`; pull requests to `main` only, a trigger `1f2b52d` did not change) and in the
release workflow. I ran both here (§7.6). [CI; read: workflow triggers]

**The live workflow** is deep-reasoning's `.github/workflows/fork-live.yml` on branch `ci/fork-live` (`a8154e2`,
one commit on D1's `c8d7fbb`): `workflow_dispatch` with `sdk_ref`, `suites`, `sdk_repo`, `live_config`; it checks out
both repositories, installs deep-reasoning with `uv sync --locked` (deep_reasoner at `d7334ae` through a read token)
and the fork with `uv sync --frozen --group dev`, then runs `pytest -m acp_live
tests/sdk/agent/test_acp_subagents_live.py` with `OPENHANDS_ACP_LIVE_AGENT_COMMAND="<dr-acp> --config
docs/configs/advising/main.yaml --home <temp>"` and `OPENHANDS_ACP_LIVE_SUBAGENTS_PROMPT="/compare-departments Which
department is lighter for a first-year student, CS or STAT?"`, then S2's file. [read; CI]

---

## 7 · Experiments and tests, as measured

### 7.1 The runs

| Run | Commit | Conditions | Result |
|---|---|---|---|
| CI `Run tests` [37146975823](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37146975823) | `a3279be` (merge `464c710` into `5e3317f`) | `pull_request`, ubuntu, uv 0.12.23, Python 3.13.16 | `sdk-tests` **6,777 passed**, 7 skipped, 12 xfailed, 164.7 s; `agent-server-tests` **2,440 passed**, 341.1 s; `cross-tests` **497 passed**, 1 skipped, 147.2 s; `acp-live-tests` 25 passed, 4 skipped, S1's two among the skipped [CI] |
| coverage in those jobs | `a3279be` | as above | `acp_subagents.py` 96% (uncovered 157 a message's `_meta`; 166, 191, 211 three replay early-returns; 176 a non-text chunk; 227 the turn-end `flush_all` body; 325 a message's non-text blocks), `acp_unstable.py` 96% (228–229, 243, 245), `event/acp_subagent.py` 93%; `acp_router.py` 100% in `agent-server-tests` [CI] |
| CI TypeScript client [37146975745](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37146975745) | `a3279be` | Node 22.12 and 24.x | **23 files, 361 passed**; lint 0 errors, 7 warnings [CI] |
| live [37147706623](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37147706623), job 111274963526 | SDK `a3279be`, deep-reasoning `a8154e2` | ubuntu, Python 3.12.3, uv 0.12.23, dr-acp on gpt-6-luna | **2 passed** in 41.29 s (§7.4); the S2 step passed too [CI] |
| here: S1's SDK files | `a3279be` | 4 CPUs, serial | `test_acp_unstable.py`, `test_acp_subagents.py`, `test_acp_subagent_events.py`: **72 passed**, 27.9 s; three repeats of the first two **62 passed** each [run] |
| here: the other files S1 touches | `a3279be` | serial | `test_acp_router.py` (with S2's tests in it), the event-service class, the cross test, resume transcript, dedup, settings, resolver, `test_check_persisted_settings_compat.py`: **325 passed**, 2 deselected (the live file), 49.6 s [run] |
| here: the four edge tests on the old code | `0cfb6a2`'s tree, `a3279be`'s test file | `git archive`, `PYTHONPATH` | E-1, E-2 and E-4's tests **fail**, E-3's passes (§4.5) [run] |
| earlier (r1) | `0cfb6a2` | CI 37105068562; live 37141960911; here | sdk 6,773, agent-server 2,435, cross 497 passed; live 2 passed in 33.55 s; here 68 and 307 passed; TypeScript 361 passed [CI; run] |

I did not run the full Python suite here; CI's is the record. Reproduce: `OPENHANDS_SUPPRESS_BANNER=1 uvx uv@latest
run --frozen pytest tests/sdk/agent/test_acp_subagents.py tests/sdk/agent/test_acp_unstable.py
tests/sdk/event/test_acp_subagent_events.py tests/agent_server/test_acp_router.py`.

### 7.2 E5 in the fork (the agent-server half)

A real `LocalConversation` with `ACPAgent(acp_command=[python, scripted_agent.py, …], acp_subagents=True)`, no
network. The baseline for each arm is the scripted or recorded wire stream itself. All passed here at `a3279be`
[run], and their CI jobs finished with no failure [CI; §9 item 2].

| Test | What it asserts | Result |
|---|---|---|
| `test_scripted_run_stores_the_scripted_tree` | the tree rebuilt from stored events by design §5's rules equals the scripted one: `child-a` (cost 0.0004 USD, `cell-a1`, its task and answer, one thought run), grandchild `child-a-1` placed in `cell-a1` with its two-chunk answer, `child-c` not cancellable, `child-b`; every child placed by cell | passed |
| `test_scripted_run_keeps_child_text_out_of_the_answer` | the `FinishAction` message is the root's reply alone | passed |
| `test_scripted_run_books_only_the_roots_cost` | the conversation's cost is 0.0011, not 0.0015 | passed |
| `test_scripted_run_with_subagents_off_stores_only_root_work[--subagents, --transcript]` | off: only `cell-1`, no new kinds, no `acp_session_id`, `initialize` without `subagents` | passed ×2 |
| `test_subagents_off_uses_the_stock_connection_and_initialize` | off: the connection is exactly `ClientSideConnection`; `initialize`'s params equal the library's own serialization | passed |
| `test_cancel_acp_session_reaches_the_child_and_its_cancelled_state_is_stored` | `--cancel-wait 30`, `run()` in a thread: the request log holds `session/cancel {sessionId: child-b}`; `cell-b1` stored `failed`, `child-b` idle `cancelled` | passed |
| `test_cancel_acp_session_does_not_wait_for_the_state_lock` | the successful call began while the run held the state lock; the run finishes | passed |
| `test_cancel_acp_session_for_an_idle_child_that_keeps_its_grant_is_sent` | after `child-b` is idle and still cancellable, the cancel is written and no new snapshot is stored (E-3) | passed |
| `test_cancel_acp_session_refuses_a_child_without_a_grant` · `…_unknown_and_root_sessions` · `…_without_a_live_connection_is_refused` | `child-c` 409-class and no `session/cancel` sent; unknown 404-class, root 409-class; before the first run 409-class | passed |
| `test_scripted_transcript_replays_a_recording[full, outgoing-only]` | a recorded turn with two children replays into its tree, from a full recording and from the agent's lines only | passed ×2 |
| `test_transcript_interval_paces_the_replay` · `test_transcript_wait_point_that_is_never_reached_exits_non_zero` | pacing ≥ 50 ms per update; a missed wait point exits non-zero | passed |
| three ordering tests (D-10) | §4.4's three facts | passed |
| `test_stored_sub_agent_events_validate_against_the_event_schema` (agent-server) | every stored event of a sub-agent run, read over REST, validates against the public `Event` schema | passed |
| `test_acp_subagent_sessions_over_live_server` (cross) | a real server and WebSocket: cancel `child-b` through the route, every sub-agent event reaches the WebSocket client, order and timestamps on the REST log | passed |

Measured beside them [run: probe, three trials each time, scripted agent, `run()` holding the state lock]: the cancel
call returned in 0.5, 0.9 and 1.6 ms at `a3279be` (14.7, 3.3 and 2.4 ms at `0cfb6a2`); the run ended 1.02 to 1.11 s
later with `child-b` idle `cancelled`.

### 7.3 D1's golden recordings through the bridge (a preview of E5's second half)

An uncommitted probe replays each of D1's nine `tests/acp/golden/*.native.jsonl` (deep-reasoning `c8d7fbb`;
agent-outgoing lines only) through `--transcript` into a `LocalConversation` with `acp_subagents=True`, one message
per recorded prompt, and compares the stored tree with the tree read straight from the recording (each child's parent
session and `parentToolCallId`, the tool call ids per session, each child's final state and stop reason). Run at
`0cfb6a2` and again at `a3279be`, with the same result. [run]

| Recording | Children | Tree, calls, final states equal | Child text runs (recorded chunks) | Time at `a3279be` |
|---|---|---|---|---|
| `claude`, `linear` (2 prompts) | 0 | yes | 0 | 1.1 s, 3.2 s |
| `depth3`, `fanout2`, `fork` | 2 each | yes | 0, 1 (1), 0 | 1.4–1.5 s |
| `exhausted`, `failing`, `namespace` | 1 each | yes | 0 | 1.4–1.9 s |
| `fanout20` | 20 | yes | 0 | 3.0 s |

9 of 9 equal. The comparator is mine, not D1's `testing.tree()`, which D5 §7.5 names for this job; costs are not
compared (D1's goldens keep only each session's last `usage_update`).

### 7.4 The live tier (dr-acp on gpt-6-luna)

Run 37147706623 [CI], SDK checked out at `a3279be`, `-m acp_live tests/sdk/agent/test_acp_subagents_live.py -v -rA`,
2 passed in 41.29 s (r1's run 37141960911 at `0cfb6a2`: 2 passed in 33.55 s):

| Test | Asserts | Result |
|---|---|---|
| `test_live_agent_tree_is_well_formed` | `run()` on the CS-vs-STAT prompt; within 30 s no child is `running`; at least one grandchild; every child's parent is the root or a stored child; every set `parent_tool_call_id` names a stored call of its parent; no child text run of ≥ 40 characters appears in the answer; the conversation's cost equals the root's last reported cost | passed; prompt returned in 19.1 s |
| `test_live_agent_stops_one_subagent_and_its_branch` | `arun()` under a 120 s limit, watched by a conversation callback; on the first announcement of a grandchild whose parent is `running` and `cancellable`, `cancel_acp_session(parent)` from a new thread; then that child and all its descendants are stored idle `cancelled` within 30 s, and no non-terminal tool call of the branch is stored after the branch root's `cancelled` snapshot | passed; prompt returned in 17.0 s |

The run's spend is not printed. [CI]

### 7.5 The other tests S1 adds

- **Shim** (`test_acp_unstable.py`, 10): two tripwires; the capability on the wire and the library call without it;
  nine interleaved stable and unstable updates in wire order; a stable update on a child id still parsed by the
  library; a malformed update dropped with one WARNING; omitted versus `null`; a custom state kept; non-text blocks
  kept typed. Over a real agent-side `Connection` on a socket pair. [run]
- **Router and bridge units** (`test_acp_subagents.py`, 24 names, 33 cases with the ten-case merge test): v1 §7.2's
  unit list by name, plus E-1's, E-2's and E-4's tests; v1's 22nd name, the stock-connection test, runs a
  conversation and is in §7.2's table. [run]
- **Events** (`test_acp_subagent_events.py`, 10): JSON round trip of the four kinds; a legacy `ACPToolCallEvent` loads;
  a root call dumps with no new keys; visualization. [run]
- **Consumers**: resume transcript skips child calls; `RemoteEventsList` merges child and root calls separately;
  `create_agent` forwards the opt-in; the profile resolver and seed (3); both persisted baselines, through
  `test_collect_fixture_cases_and_validate_current_repo_fixtures`. [run]
- **Route** (`test_acp_router.py`, 7): 200 then idle `cancelled` stored; unknown conversation 404; unknown session 404
  with its `detail`; `child-c` 409 with its `detail`; non-ACP 400; a cancel that never writes, 504 at a 0.2 s
  timeout; the schema test. **Service** (2): runs off the event loop; inactive refused. [run]
- **TypeScript** (6): `cancelAcpSession` posts, encodes the id, and posts for its conversation; the opt-in survives
  the settings filter; stored-event shapes type-check; each guard matches only its kind. [run in r1; CI]

### 7.6 Upstream guards, run here at `a3279be`

| Guard | Result |
|---|---|
| persisted settings (`check_persisted_settings_compat.py`) | 19 fixtures validated (both of S1's), 8 PyPI 1.50.1 baseline payloads validated [run; CI the same] |
| OpenAPI weak-schema ratchet on the exported schema | **passes**: "65 allowlisted weak locations" (62 at S2's `5e3317f`, which also passes; S1's three `meta` entries are the difference). At `0cfb6a2` it failed on one S2 pointer, the panel-icon response, which S2's `13e5904` now declares as an image [run] |
| REST breakage: oasdiff 1.19.1, S2's `5e3317f` export → S1's | S1's share only: 2 ERR-level changes, both `response-property-one-of-added` / `response-body-one-of-added` for S1's three kinds in the `Event` union, the two rule ids `check_agent_server_rest_api_breakage.py` treats as additive; 15 info (the new endpoint, optional properties) [run]. The script itself, against PyPI 1.50.1, passed in CI's second attempt (§6) [CI] |
| TypeScript lint, suite, public type budget | in CI at `a3279be` (§6) [CI]; run here at `0cfb6a2` in r1, and the client is unchanged since [run in r1] |
| pre-commit (ruff, pycodestyle, pyright, the repository's checks) | green in CI [CI]; not run here |
| SDK API breakage (`check_sdk_api_breakage.py`, Griffe against PyPI 1.50.1) | exits 1 on one change: `ACPAgentSettings.llm`'s field (`settings/model.py:1776`) gained `exclude=True` and a deprecation, which the script calls breaking without a minor version bump. S1 does not touch that field (its diff to `settings/model.py` adds only `acp_subagents`); the change is the fork base's, since the script compares the whole branch with the release. `openhands-workspace` and `openhands-tools`: no breaking change. Not run in CI (§6) [run] |

---

## 8 · Size, and what resisted compression

S1 is +1,235 −49 lines of Python product code, +112 −2 of TypeScript, and +2,761 of tests and fixtures (D-13). The
part of this document that will not get shorter is §2: v1 was written before S2 landed and before C1's and D5's
asks, so its differences from the build are many and mostly small, and each changes a sentence C1, D5 or S2 may have
read; v2.2 now carries them all, and §2.1 is what remains.

---

## 9 · What I could not verify

1. **The live tier and its cost**: not run here; results are GitHub's log [CI]. No amount is printed, so the cost per
   live run is unknown.
2. **Each S1 test's line in CI.** The GitHub tools return at most the last 5,000 lines of a job log, and full log
   downloads are blocked here. `sdk-tests`, `agent-server-tests` and `cross-tests` were read from their tails only:
   I saw their totals and coverage tables, not each S1 test's result line, so "passed in CI" for an individual test
   rests on the job's total having no failure.
3. **A real `session/load` replay.** The `replaying` flag, and E-2's fix under it, are exercised by unit tests that
   set it directly; no test or probe drives a `session/load` whose agent replays sub-agent traffic (the scripted
   agent's transcript mode refuses `session/load`, and the reconnect test falls back to `session/new`). The restart
   path of design §2 is read, except the seed, which is run.
4. **Upstream guards still outside CI**: the SDK API breakage check and the OpenAPI ratchet ran here, not in CI; that
   the `ACPAgentSettings.llm` error is the fork base's I read from S1's diff, without running the script on the fork's
   `deep-reasoning`. Also unchecked: whether each of S1's commits is green on its own and cherry-picks onto `main`
   (§6, §7.6).
5. **pyright on the shim**: green in CI's pre-commit [CI]; not run here.
6. **Paths read but not seen run**: a notification without `sessionId` dropped by the shim; a `session_message`'s
   `_meta` and non-text blocks; the 504 against a real stalled agent (tested by patching `cancel` to sleep); the
   Python `RemoteEventsList` reordering (§4.5); masking of `meta`.
7. **The opt-in from a profile through a real agent-server launch**: the resolver, the seed and the baseline are
   checked; no run started a conversation from a profile with `acp_subagents` and saw child events stored.
8. **Canvas** (C1) is not built, so nothing renders S1's events yet; §5's C1 paragraph checks the stored shapes
   against C1's design, not against Canvas code.
