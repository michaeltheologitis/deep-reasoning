# C1 · Sub-agent sessions nested in the chat — design

**TASK-4** · System Designer · code lands in the Canvas fork
[michaeltheologitis/OpenHands](https://github.com/michaeltheologitis/OpenHands), branch
`feat/acp-subagent-sessions`, cut from `deep-reasoning` after the wiring commit (§9.3), as one pull request ·
against the approved spec [TASK-1](https://app.notion.com/p/3ed62fb22237814ab425c81b3844f012) (C1 in full, S1, D1's
emission and Stop, Q3, §4 E6 and the layers, the 2026-10-02 amendment and the note decided after approval), S1's
design (deep-reasoning `design/s1` `f956fda`, `docs/design/s1-acp-subagent-sessions.md`, §5 above all) and D1's wire
contract (deep-reasoning `f281109`, `docs/design/d1-dr-acp.md` §5).
**Pinned against:** Canvas fork `deep-reasoning` at `02b7ac7` (= upstream `1ff45c2` plus the ASE commit, which
touches only `AGENTS.md` and `CLAUDE.md`, so every `file:line` below is also upstream `1ff45c2`'s) ·
`@openhands/typescript-client` as S1 §4.9 extends it (`ConversationClient.cancelAcpSession`,
`CancelAcpSessionResponse`, `ACP_SETTINGS_KEYS` with `acp_subagents`) · SDK fork `91430aa` (= upstream `53a4bc5`) for
the agent-server facts · React 19.3, zustand 5.0.14, Playwright and Vitest as `package.json` pins them.

**Revisions** (newest first; each line says which sentences to stop trusting):
- 2026-10-02 · v2 · after D5's design (deep-reasoning `design/d5` `8086afb`, its §8.4) and the Conductor's note that
  S1 adds `acp_subagents` to `ACPAgentProfile`. Stop trusting: the replay variable `ACP_SUBAGENT_TRANSCRIPTS` (now
  D5's `OH_ACP_REPLAY_TRANSCRIPTS`, a path list) and the replay as a test inside the main spec (now its own file,
  `mock-llm-acp-replay.spec.ts`, §6.3–§6.4); `SubagentLink` without `toolCallIds` (A.9). Added: stable test ids as a
  contract (§4.12, `SUB-011`); §9.1 item 1 is agreed and §10 item 1 is now a sequencing note.
- 2026-10-02 · v1 · first full-depth version. Every TypeScript block in Appendix A was typechecked under `strict`
  (TypeScript 6.0.2, with stubs for React, react-query, the client and Playwright) and formatted with Prettier at
  upstream's `.prettierrc.json`.

**Where this file lives, and why nothing trips over it.** `docs/design/` on deep-reasoning's `design/c1` branch, not
in the fork: the fork's branches carry only code upstream would accept. deep-reasoning has no docs site, no package
and no test runner at this commit; once D1's `pyproject.toml` lands, pytest is pointed at `tests/` only and the sdist
excludes `docs/` (D1 §8.5), so this file is never collected, built or shipped. The upstream-shaped behaviour spec
that does go into the fork is `specs/acp-subagent-sessions.md` (§4.11), in upstream's own format.

**Reading guide.** Gate B: §1–§3 (the reasoning, about 15 minutes). S1's designer and the Conductor: §9 (what C1
needs S1 to change). C2's designer: §8 (every file both touch, with the rule for either landing order). D5's
designer: §6.4 (the replay of D1's golden recordings through the forked Canvas), §4.12 (the test ids E12 can rely
on) and §9.4. The Implementer reads
everything; Appendix A is the signature reference.

---

## 1 · What C1 changes

### 1.1 The problem, at `1ff45c2` with S1's events arriving

Canvas shows one flat transcript, and with S1 in the agent-server it would show a wrong one. Each point verified in
the fork:

1. **The new kinds are invisible.** `shouldRenderEvent` returns false for any kind it does not know
   (`should-render-event.ts:147–148`), so `ACPSubagentEvent`, `ACPSessionMessageEvent` and `ACPSessionTextEvent`
   never render. Nothing says which agent is a child of which, what state it is in or what it cost.
2. **Child tool calls flood the root's flow.** Every `ACPToolCallEvent` renders (`should-render-event.ts:139–141`),
   and Canvas merges a call's `started` and terminal events by `tool_call_id` alone
   (`handle-event-for-ui.ts:291–303`). ACP ids are unique only within a session, so two sessions' calls with one id
   would overwrite each other. The typing indicator keys by `tool_call_id` too (`typing-indicator.tsx:70–122`).
3. **Nothing can nest inside a tool call.** The ACP card is `GenericEventMessageWrapper` →
   `GenericEventMessage` (`event-message.tsx:236–240`), a title row and markdown details, with no slot for children.
4. **A fan-out is split across history pages.** Opening a conversation loads only its newest 50 events
   (`use-conversation-history.ts:10, 73–81`); older pages load when the user scrolls to the top, by
   `timestamp__lt` (`use-load-older-events.ts:141–152`). A 50-child fan-out is about 1,100 events, so on reopening,
   most children's snapshots and the spawning cell's start are not loaded.
5. **An ACP card remounts when its call completes.** `Messages` keys every single item by event id
   (`messages.tsx:85, 104`); the started event is replaced in place by the terminal one, which has another id, so the
   card's local state (`generic-event-message.tsx:38`) resets. Anything nested in it would collapse at the end of
   the run.
6. **The shared-conversation view renders `Messages` from its own query** (`routes/shared-conversation.tsx:51–67,
   150–155`), not from the event store, so anything that reads only the store shows nothing there.
7. **No call stops one child.** The client has no method before S1 (§4.9 of S1 adds `cancelAcpSession`).

### 1.2 The change

Fold every ACP sub-agent event into an index kept in the event store beside `uiEvents`; place each child from the
index (in the tool call that spawned it, else at its parent's message to it, else at its announcement); hide child
work from the root's flow; render each spawning cell's children under its card, collapsed to one summary line,
recursively; show each child's state, its latest cost and, when the agent granted it, Stop; and load the older
history a visible fan-out needs.

```text
agent-server (S1) ── REST page / WebSocket durable frames, same events, same order
   ▼
useEventStore.addEvent(s)  (stores/use-event-store.ts; one writer, one set per event or page)
   ├─ events, eventIds                                  unchanged
   ├─ uiEvents  ← handleEventForUI                      ACP merge key becomes (session, tool_call_id)
   └─ subagents ← foldSubagentEvents                    NEW: the sub-agent index (§4.3), placement (§4.4)
   ▼
ChatInterface                                           history backfill while subagents.needsOlderHistory (§4.8)
   └─ Messages(renderableEvents = uiEvents ∩ shouldRenderEvent)   child calls hidden from the root's flow
        ├─ root ACP call → AcpToolCallCell = today's card + SubagentBlock(cellKey)      (§4.6)
        │      SubagentBlock: "3 sub-agents · 2 done · 1 running", collapsed by default
        │        └─ SubagentRow(child): status · title · answer · N tool calls · cost · [Stop]
        │             └─ SubagentTranscript: task, thoughts, AcpToolCallCell(child call) …  ← recursion
        ├─ root-level children without a spawning call → interleaved by time (§4.6)
        └─ UnplacedSubagents: children whose parent session is not in the conversation (§4.6)
   Stop → useCancelAcpSession → EventService.cancelAcpSession → ConversationClient.cancelAcpSession
          → POST /api/conversations/{id}/acp/sessions/{session}/cancel (S1); confirmed by the child's next snapshot
```

Agents without sub-agent sessions (Claude Code, Codex and Gemini today, and every OpenHands agent) produce none of
these events and no `acp_session_id`: the index stays empty and the chat renders exactly as now, except that an ACP
card keeps its expanded state when its call completes (decision H).

### 1.3 Decisions this design takes

The spec's decisions stand (§2: generic and additive, ACP's names, `_meta.deep_reasoner` never read; C1's bullets) and
so do S1's (§5 is C1's contract). These are the next layer down.

| # | Decision | Why | Rejected |
|---|---|---|---|
| A | **The sub-agent index is derived state in the event store**, folded by a pure function in the same `set` as `events` and `uiEvents`, reset with them. | The store already owns derived state this way (`uiEvents` via `handleEventForUI`); one writer, one dedupe, one reset, and the guide's rule "one named owner and one obvious writer". Folding is incremental, so a sub-agent event costs O(children), not O(events). | (1) Rebuilding the tree from `events` on each render: every object new at 60 events/s, so every row re-renders. (2) A second store subscribed to the event store: two writers and an order between them. (3) Fetching sub-agent events separately with the search route's `kind` filter: it matches module-qualified class names only (`event_service.py:548–550`, `test_event_service.py:255–262`), which ties Canvas to the SDK's module paths, and the transcripts would still need the pages. |
| B | **Records by key, transcripts by reference.** A child's transcript is an array of keys into `toolCalls` and `messages`; each card, row and summary selects its own record. | A call completing or a cost changing replaces one record, so only the card or row that shows it re-renders; the transcript array keeps its identity. That is what keeps 50 × 5 responsive without virtualization (§5). | Transcripts holding events: every update to a call would replace the whole transcript and re-render every sibling card. |
| C | **Order by timestamp, ties by arrival; never by `seq`.** | REST events carry no `seq` (only WebSocket durable frames do, `conversation-websocket-context.tsx:165–168`), and the store already sorts by timestamp. Within one child, S1 creates every event on one thread in wire order, so timestamp order is log order per child (§9.1 asks S1 to state it). | `seq`: absent on the REST path, which is how every reopened conversation loads. |
| D | **Placement waits for history instead of guessing.** A child whose parent session, or whose named spawning call, is not loaded is *pending*: not rendered, and the chat loads older pages until it resolves. Fallbacks (S1 §5 rule 2) and "could not be placed" apply only once no older history remains. | On reopening a conversation the spawning cell is usually older than the newest 50 events; guessing would render dozens of children in the root's flow and then move them into the cell when the page lands. Loading stops at the spawning cell's start, so the cost is bounded by the visible fan-out, not the conversation. | (1) Placing at the fallback at once: the flash-and-jump above. (2) Loading the whole conversation on open: thousands of events for a long one, against upstream's lazy loading. |
| E | **Children placed without a spawning call join the root's flow by time, through `Messages`, not through `shouldRenderEvent`.** | `shouldRenderEvent` judges one event alone; whether a snapshot anchors a child needs the index. Interleaving anchors into `Messages`' rendered items keeps `uiEvents` and its consumers unaware of them. | Letting snapshots through `shouldRenderEvent` and rendering nothing for all but one: hundreds of empty items in the flow, and anchors that move when the store re-sorts a replaced event. |
| F | **Child tool calls stay in `uiEvents`; `shouldRenderEvent` hides them.** | Every consumer that asks "is this in the chat" (`/model` message anchoring, `record-model-switch-message.ts`, `model-command-event-anchor.ts`, the shared view) then agrees with the root's flow. The transcript export, which wants them, says so explicitly (§4.5). | Dropping child calls from `uiEvents`: the export, which builds its own `uiEvents`, would lose them. |
| G | **ACP tool calls are keyed by `(session, tool_call_id)` wherever Canvas merges or tracks them**: `handleEventForUI`, the typing indicator, the index and render keys. | S1 §5 rule 3; ACP ids are unique only within a session. dr-acp's ids never collide (D1 decision F), but a generic agent's may. | Keeping `tool_call_id` alone because dr-acp is safe: not generic. |
| H | **An ACP card's render key is its call key, not its event id.** | The card, and the sub-agents under it, keep their expanded state when the call completes (§1.1 item 5). | A UI-state store for expansion keyed by call: more state, one more owner, for what a stable key gives. |
| I | **Stop is never optimistic.** Enabled only for a running or waiting child whose latest snapshot is live and `cancellable`; disabled, with the spec's sentence, when the agent withheld `cancel`; absent for idle and unconfirmed children and in read-only views. After a 200 the row says "Stopping…" until the child's own `idle`/`cancelled` snapshot arrives. | S1 §5 rules 6–7 and §3 item 14; the RFD's freshness rule. dr-acp's stop lands at the agent's next turn, so a client-side "stopped" would be contradicted moments later. | Marking the branch stopped on click; hiding the control entirely when withheld (the spec's failure cell explains it on hover where Stop would be). |
| J | **Costs are shown per child and never added**, not even across siblings. | ACP forbids it and S1 §5 rule 5 extends it to siblings; dr-acp's costs are inclusive of descendants (D1 §6.2), so a sum would double-count at every level. | The mock-up's `$0.0021` on the summary line (§3 item 1). |
| K | **Components read the index through a context that defaults to the event store**; the shared view provides one built from its own events, marked read-only. | Keeps `Messages`' contract (it renders whatever events it is given) and the shared view correct. | Reading the global store everywhere: the shared view would hide child work entirely. |
| L | **No capability flag and no `minimumAgentServer` bump.** | Everything keys off events and fields that only an agent-server with S1 writes; on any other server the index stays empty and Stop never appears, so Canvas need not require S1 (`AGENTS.md`: raise the floor only when Canvas starts *requiring* something). | A `ServerInfo` capability: S1 adds none (S1 §9 row 11), and there is nothing to hide when the events are absent. |
| M | **No virtualization.** Blocks and rows are collapsed by default, a row renders its transcript only when expanded, and rows are memoized on their own record. | Upstream's chat has none; nested variable-height rows are the hard case for windowing libraries; §5 shows the work per event stays small. E6 measures it. | Adding a windowing dependency up front. If E6 fails, the first remedy is `content-visibility: auto` on rows (§5). |

---

## 2 · A fan-out in the chat, end to end

The spec's C1 mock-up, with the events S1 stores for D1's run (S1 §2) and what C1 does with each. Short ids as in the
spec (`n2` is `20261002-142233-4f1a2b-n2`, `c1.1` is `…-n1-c1`); the store always holds the full ones.

1. **The spawning cell.** `ACPToolCallEvent c1.1` (no `acp_session_id`: root), started. `uiEvents` gets it as
   today; the index records `toolCalls[(root, c1.1)]` with `startLoaded: true`. The main flow renders
   `AcpToolCallCell`: today's card, "Running cs = [...]; summaries = run_all({...})", and an empty `SubagentBlock`
   (renders nothing).
2. **The announcement.** `ACPSubagentEvent n2` (parent root, `parent_tool_call_id` `c1.1`, running, cancellable).
   The index adds `children[n2]`; placement puts `n2` in `byCell[(root, c1.1)]` and computes that cell's summary.
   The block appears: "1 sub-agent · 1 running", collapsed, with a spinner.
3. **The task.** `ACPSessionMessageEvent` on the root's transcript, root → `n2`. The index records it and
   `firstMessageTo[(root, n2)]`. Nothing renders in the root's flow (decision E); it is `n2`'s task when its row is
   expanded.
4. **The child works.** `ACPSessionTextEvent n2` (a thought), then `ACPToolCallEvent c2.1` with
   `acp_session_id n2`, started, then terminal. `shouldRenderEvent` hides the call from the root's flow
   (decision F); the index appends a text item and a tool-call item to `transcripts[n2]` and counts one tool call. If
   `n2`'s row is expanded, its transcript shows the thought (collapsed, as the root's reasoning is) and a card
   "Running c = catalog['CS101']; …", which completes in place.
5. **The answer and the cost.** `ACPSessionMessageEvent` on `n2`'s transcript, `n2` → root: `stats[n2].answerKey`.
   `ACPSubagentEvent n2` with `cost 0.0004 USD`: only `children[n2]` changes, so only `n2`'s row re-renders:
   `$0.0004`.
6. **Idle.** `ACPSubagentEvent n2` idle, `end_turn`: the summary recounts ("1 sub-agent · 1 done"), the row shows
   ✓ done, the answer `'3cr, 0 prereqs — light'` and `1 tool call`.
7. **Siblings, interleaved.** `n3` and `n4` the same; the block reads "3 sub-agents · 2 done · 1 running". Expanded:

   ```text
   ▾ Running cs = [...]; summaries = run_all({...}); print(summaries)
       ⟳ 3 sub-agents · 2 done · 1 running
         ✓ Summarize the workload of CS101.   '3cr, 0 prereqs — light'   1 tool call    $0.0004
         ⟳ Summarize the workload of CS201.   running                    1 tool call    $0.0009   [■ Stop]
              Task  Summarize the workload of CS201.
              ▸ Thinking
              ✓ Running c = catalog['CS201']; print(c['credits'], len(c['prereqs']))
         ✓ Summarize the workload of CS310.   '4cr, deep chain — heavy'  2 tool calls   $0.0008
   ```

8. **Stop on `n3`**, which has a child `n5`. Click → `POST …/acp/sessions/<n3>/cancel` → 200
   `{"requested": true}`; `n3`'s button turns "Stopping…". dr-acp's acknowledgement arrives as a thought on `n3`.
   As each agent of the branch actually ends, its snapshot arrives `idle`/`cancelled`: `n5` (under `n3`'s cell), then
   `n3`; each row turns ■ stopped and loses Stop. In the interim (Dean's API not shipped), `n4` turns
   `idle`/`cancelled` too, and the parent's cell output names it (D1 §6.3) — C1 shows what is stored and reads no
   `_meta.deep_reasoner`.
9. **The root finishes.** `c1.1` terminal replaces the started event in `uiEvents`; the card keeps its key
   (decision H), so the block under it stays expanded as the user left it. The root's answer renders as today and
   holds no child text (S1).
10. **Reopen the conversation later.** The newest 50 events hold `c1.1`'s terminal event and the last snapshots of
    some children, not `c1.1`'s start. Placement puts the loaded children in the cell, but the cell's start is not
    loaded, so `needsOlderHistory` is true; `ChatInterface` loads older pages until the start is in (§4.8).
    Meanwhile the block says "Loading earlier sub-agent activity…". Then all 50 are there.
11. **After an agent-server restart**, S1 writes `ACPSubagentEvent(source="environment", state=None,
    cancellable=False)` for each child that was active or cancellable. C1 shows the last state the agent confirmed
    (from the previous snapshot) without a spinner and without Stop; a child that was running reads "running · last
    known" (S1 §5 rule 7).

---

## 3 · Where this design departs from, or adds to, the approved spec

Each is a refinement inside C1's scope. If the Conductor reads any as a change of what was approved, it goes back to
Michael.

1. **No cost on the spawning cell's summary line.** The spec's mock-up prints `$0.0021` there, the sum of the three
   children; the spec's own bullet says costs are "never summed, by ACP's rule", and S1 §5 rule 5 forbids adding
   siblings. Each row shows its own cost; the conversation's cost stays where Canvas shows it today (the root's
   report, which for dr-acp covers the whole run).
2. **"N tool calls", not "N turns".** The mock-up's "1 turn · 2 turns" counts something C1 cannot know generically;
   the number of tool calls in the child's own transcript it can.
3. **The task is shown inside the child, not in the parent's flow.** A parent's `session_message` to a child is the
   first line of that child's expanded transcript ("Task …"); the parent's flow does not repeat it. Fifty task
   messages in the root's flow would be the flat list the spec rejects. A root message to a session that is not a
   child is not rendered (none in v1).
4. **Placement under partial history** (decision D): pending children, a bounded backfill in `ChatInterface`, and
   fallbacks only once history is complete. The spec assumes the whole log is loaded; Canvas loads 50 events.
5. **More existing files than the spec lists.** Besides `should-render-event.ts`, the ACP card, the chat list and
   the event types: the event store (decision A), `handle-event-for-ui.ts` and the typing indicator (decision G),
   `chat-interface.tsx` (§4.8), the shared-conversation route (decision K), the transcript export (§4.5) and
   `event-service.api.ts` (Stop). Each is a consumer upstream's checklist asks to enumerate.
6. **Size: ≈1.4k lines of production TypeScript, ≈1.0k of Vitest, ≈0.6k of Playwright specs, helpers and
   transcripts** (≈3.0k, plus ≈0.5k lines of translation JSON), not the spec's ≈1.2k with tests. The growth is the
   placement-under-partial-history and backfill (≈0.2k with tests), the shared view (≈0.1k), the consumers (≈0.1k)
   and above all E6's tests, which the spec's ≈450 lines of tests did not cover (the replay of recordings through the
   real agent-server, the 50 × 5 load case, D5's golden replay). About 8 h at Gate C, not 4.
7. **The transcript export stays flat.** It includes child tool calls in time order, as stock Canvas would export
   S1's events; a nested export is a later feature (§10 item 3).
8. **A failed dr-acp sub-agent shows as done**, with its answer `Failed: …` (D1 §3 item 5). ACP has no failure stop
   reason and C1 reads no `_meta.deep_reasoner`.
9. **Visual indentation stops at depth 6.** Deeper rows keep nesting in the DOM and show their depth; the chat
   column does not shrink to nothing.
10. **The spec's falsifier "a 50-child fan-out makes the chat unusable"** becomes E6's measurable null: over 1 s from
    a scheduled scroll to the next painted frame, with every child expanded, while the fan-out streams (§6.3).

---

## 4 · Modules and seams

### 4.1 Files

| Path (Canvas fork) | | ≈ lines | What |
|---|---|---|---|
| `src/types/agent-server/core/events/acp-subagent-event.ts` | new | 110 | The three kinds, as Canvas types (A.1). |
| `src/types/agent-server/core/events/acp-tool-call-event.ts` | changed | +10 | `acp_session_id`, `meta`. |
| `src/types/agent-server/core/events/index.ts`, `core/openhands-event.ts` | changed | +5 | Export; join the `OpenHandsEvent` union. |
| `src/types/agent-server/type-guards.ts` | changed | +25 | Four guards (A.2). |
| `src/utils/subagents/subagent-index.ts` | new | 230 | Keys, records, `foldSubagentEvents`, `buildSubagentIndex` (§4.3, A.3). |
| `src/utils/subagents/subagent-placement.ts` | new | 150 | `placeSubagents`, `anchorsForParent`, `unplacedGroups` (§4.4, A.4). |
| `src/utils/subagents/subagent-status.ts` | new | 70 | Status categories, Stop rules, cost format, summaries (§4.7, A.5). |
| `src/stores/use-event-store.ts` | changed | +25 | `subagents`, folded in `appendEvent` and `addEvents`, reset in both clears (A.8). |
| `src/utils/handle-event-for-ui.ts` | changed | +5 | ACP merge key `(session, tool_call_id)`. |
| `src/components/conversation-events/chat/event-content-helpers/should-render-event.ts` | changed | +5 | Hide child-session calls. |
| `src/components/conversation-events/chat/event-message.tsx` | changed | +3 | ACP branch renders `AcpToolCallCell`. |
| `src/components/conversation-events/chat/messages.tsx` | changed | +35 | `renderKeyOf`; root anchors interleaved; `UnplacedSubagents` at the end. |
| `src/components/conversation-events/chat/subagents/subagent-source.ts` | new | 45 | Source and history contexts, `useSubagents`, `useStaticSubagentSource` (A.6). |
| `src/components/conversation-events/chat/subagents/main-flow-anchors.ts` | new | 35 | `interleaveSubagentAnchors`. |
| `src/components/conversation-events/chat/subagents/acp-tool-call-cell.tsx` | new | 35 | Today's card plus `SubagentBlock`. |
| `src/components/conversation-events/chat/subagents/subagent-block.tsx` | new | 90 | Summary line, toggle, rows. |
| `src/components/conversation-events/chat/subagents/subagent-row.tsx` | new | 120 | One child's header and, expanded, its transcript. |
| `src/components/conversation-events/chat/subagents/subagent-transcript.tsx` | new | 110 | Task, entries, anchored grandchildren. |
| `src/components/conversation-events/chat/subagents/stop-subagent-button.tsx` | new | 70 | Stop, Stopping…, withheld. |
| `src/components/conversation-events/chat/subagents/unplaced-subagents.tsx` | new | 45 | "could not be placed", apart. |
| `src/components/features/chat/chat-interface.tsx` | changed | +35 | History context, backfill, scroll-follow (§4.8). |
| `src/routes/shared-conversation.tsx` | changed | +10 | Its own read-only source and history flag. |
| `src/components/features/chat/typing-indicator.tsx` | changed | +8 | Resolve ACP calls by call key. |
| `src/utils/transcript-export/index.ts` | changed | +3 | Keep exporting child calls (§4.5). |
| `src/api/event-service/event-service.api.ts` | changed | +20 | `cancelAcpSession` (A.7). |
| `src/hooks/mutation/use-cancel-acp-session.ts` | new | 35 | The mutation (A.7). |
| `src/i18n/translation.json` | changed | ≈+530 | 31 keys × 15 languages (§4.10). |
| `specs/acp-subagent-sessions.md` | new | 50 | Upstream's spec IDs `SUB-001`…`SUB-010` (§4.11). |
| `__tests__/…`, `src/**/*.test.ts` | new/changed | 1,000 | §6.1–§6.2. |
| `tests/e2e/mock-llm/conversations/mock-llm-acp-subagents.spec.ts` | new | 200 | §6.3. |
| `tests/e2e/mock-llm/conversations/mock-llm-acp-replay.spec.ts` | new | 50 | §6.3–§6.4: any transcripts named by `OH_ACP_REPLAY_TRANSCRIPTS`. |
| `tests/e2e/mock-llm/utils/acp-subagents.ts` | new | 220 | Shared helpers (A.9), reused by D5 and C2. |
| `tests/e2e/mock-llm/fixtures/acp-subagents/*.jsonl` | new | 150 | Three hand-written transcripts (§6.3). |
| `.github/workflows/mock-llm-e2e.yml` | changed | +15 | Fetch the scripted agent from the pinned SDK (§6.3). |

Nothing in `tests/e2e/mock-llm/test-mapping.json` changes: the spec sits under `conversations/`, which
`src/components/conversation-events/**` already maps to.

### 4.2 Event types

Canvas keeps its own agent-server event types in `src/types/agent-server/core/events/` and does not import the
client's; C1 follows that convention. The three new interfaces mirror S1 A.4/A.6 field for field, with two
Canvas-side precisions: `ACPSubagentEvent.source` is `"agent" | "environment"` (S1 writes `"environment"` for
reconnect snapshots), and every field S1 may omit is optional, because the agent-server stores events with
`exclude_none=True` (`event_store.py:225`, S1 §4.5), so the REST page and the WebSocket may carry an absent key or a
`null`. A root tool call therefore arrives without `acp_session_id`; `toSessionRef(undefined)` and
`toSessionRef(null)` are both the root.

`meta` is typed and never read (spec §2 decision 4: no fork reads `_meta.deep_reasoner`).

Guards (A.2): `isACPSubagentEvent`, `isACPSessionMessageEvent`, `isACPSessionTextEvent`, and
`isSubagentToolCallEvent` (an `ACPToolCallEvent` whose `acp_session_id` is a string).

### 4.3 The sub-agent index — `utils/subagents/subagent-index.ts`

**Keys.** `ROOT_SESSION = ""` stands for the root in every key and in `SessionRef`. `toolCallKey(session, id)`,
`messageKey(transcript, id)` and `routeKey(transcript, recipient)` join their parts with `"\u0000"`, which no ACP
id contains, so keys never collide across sessions.

**Records** (A.3). Every map is keyed so that S1 §5's "latest wins" is one lookup:

| Map | Key | Holds | "Latest" rule |
|---|---|---|---|
| `children` | child session id | `latest` snapshot, `lastConfirmed` (latest with `source !== "environment"`), `firstAt` | timestamp ≥ the held one replaces it (§1.3 C) |
| `toolCalls` | `toolCallKey` (root and children) | `latest` event, `firstAt`, `startLoaded` (a `pending`/`in_progress` event is loaded) | as above |
| `messages` | `messageKey` | `latest` version, `firstAt` | as above (messages are upserts) |
| `firstMessageTo` | `routeKey(transcript, recipient)` | the `messageKey` with the smallest `firstAt` | earliest wins |
| `transcripts` | child session id | `TranscriptItem[]`: `tool_call` and `message` items by key, `text` items with their event; sorted by `at` | insertion by binary search (upper bound), so equal timestamps keep arrival order |
| `stats` | child session id | `toolCalls` count; `answerKey`: newest message the child sent whose recipient is not one of its own children | newest by timestamp |

**The fold.** `foldSubagentEvents(index, events)` is pure. For each event, skipping any with
`isFromPlanningAgent` (the planning socket's events belong to another conversation):

- `ACPSubagentEvent e` → upsert `children[e.acp_session_id]`: `latest` = the later of the held one and `e`;
  `lastConfirmed` likewise unless `e.source === "environment"`; `firstAt` = the earlier. The placement is marked
  dirty only if the parent session, the spawning call, the state, the stop reason, the grant, the source or `firstAt`
  changed; a cost-only snapshot (D1 sends up to two a second per running child) changes one record and nothing else.
- `ACPToolCallEvent e` → upsert `toolCalls[toolCallKey(e.acp_session_id, e.tool_call_id)]`; `startLoaded` turns true
  on a `pending` or `in_progress` event and never back. A new key marks the placement dirty (a pending child may now
  resolve). A new key in a child session also appends a `tool_call` item to that child's transcript and counts it;
  an older page's started event moves the item to its earlier `at`.
- `ACPSessionMessageEvent e` → upsert `messages[messageKey(e.acp_session_id, e.message_id)]`; on a new key, record
  `firstMessageTo[routeKey(e.acp_session_id, e.recipient_session_id)]` if earlier than the held one; in a child's
  transcript append a `message` item and, if the child is the sender, update `stats.answerKey`; mark the placement
  dirty (a message can become an anchor).
- `ACPSessionTextEvent e` → append a `text` item to `transcripts[e.acp_session_id]`.
- Anything else → nothing.

Any item that opens the transcript of a session with no loaded snapshot also marks the placement dirty (§4.4's third
condition).

Each changed map is copied once per call (copy-on-write), not once per event; an unchanged record, transcript or
stats entry keeps its identity. When the placement is dirty, `placeSubagents(records, index.placement)` runs once
at the end of the call. `version` increments when anything changed. A call that changed nothing returns `index`
itself, so `useEventStore` selectors see no change for the conversation's other events.

The fold assumes each event arrives once; the store dedupes by id before folding (`use-event-store.ts:116–118,
171–174`). `buildSubagentIndex(events)` dedupes by id itself, for read-only views that pass raw pages.

### 4.4 Placement — `utils/subagents/subagent-placement.ts`

S1 §5 rules 1–2, with the history Canvas has actually loaded. For each child `X` (in `firstAt` order), with
`P = toSessionRef(X.latest.parent_session_id)` and `T = X.latest.parent_tool_call_id`:

1. **Parent session not loaded** (`P` is neither the root nor a known child), or `X`'s ancestry loops (S1 makes
   loops impossible; C1 refuses to recurse on bad data anyway) → `pending { reason: "parent-session", missingId: P,
   fallback: null }`.
2. **Its fallback anchor**: the message `firstMessageTo[routeKey(P, X)]` if loaded (`via: "message"`, at the
   message's `firstAt`), else the announcement (`via: "announcement"`, at `X.firstAt`).
3. **`T` set and `toolCalls[toolCallKey(P, T)]` loaded** → `byCell[that key]` (S1 rule 2, first clause).
4. **`T` set, the call not loaded** → `pending { reason: "parent-call", missingId: T, fallback }`. ACP's
   `parentToolCallId` names a call already sent on the parent's session (D1 §5.4 rule 2), so the call exists in an
   older page unless the log was cut.
5. **`T` not set** → `byAnchor[P]` gets the fallback anchor. If the history is incomplete, the first *loaded*
   snapshot or message stands in for the true one; it sits at the top of the loaded window either way, and moves up
   if the user loads older pages. This never waits, because a generic agent may send neither a spawning call nor a
   task message, and waiting would load the whole conversation.

Then: each `byCell` list sorted by `firstAt` (announcement order), each `byAnchor` list by `at`; `cellSummaries` from
`summarizeSubagents` (§4.7); and `needsOlderHistory` is true when any of three holds:

- a child is pending;
- a `byCell` key's call has `startLoaded === false`. This is what completes a fan-out on reopen: every event of a
  cell's subtree is later than the cell's start, because S1 stores the cell's `tool_call` before it even receives
  the announcement that names it (S1 §6), so once the start is loaded the whole subtree is;
- a transcript belongs to a session with no loaded snapshot (a child still busy in a long cell, whose announcement
  and cost reports are all older than the window). Its announcement precedes all its traffic (D1 §5.4 rule 1), so it
  is in an older page; until it loads, that session's calls are hidden and nowhere placed.

**Structural sharing.** `placeSubagents` reuses `previous`'s array for a key whose membership is unchanged, a summary
whose counts are unchanged, and a map whose entries are all reused. Selectors (`useSubagents`) return stored
references, so a component re-renders only when its own slice changed.

**At render time** (`anchorsForParent`, `unplacedGroups`): while history is incomplete, pending children render
nothing (the chat is loading older pages). Once complete, `parent-call` children render at their fallback anchor in
their parent's flow, and `parent-session` children render in `UnplacedSubagents`, grouped by the missing parent
(the spec's failure cell).

### 4.5 The store and every consumer of ACP events

- **`use-event-store.ts`**: `EventState.subagents: SubagentIndex`, initially `EMPTY_SUBAGENT_INDEX`. `appendEvent`
  (`:113–132`) folds `[event]` after the dedupe; `addEvents` (`:162–195`) folds the batch's new events once, after
  the loop; `clearEvents` and `clearEventsForConversation` (`:196–209`) reset it. `sortEventState` does not touch it:
  the index orders by timestamp itself. Streaming slots never reach it (they are not events).
- **`handle-event-for-ui.ts:291–303`**: the ACP merge compares `toolCallKey(uiEvent.acp_session_id,
  uiEvent.tool_call_id)` with the incoming event's.
- **`should-render-event.ts:139–141`**: `return !isSubagentToolCallEvent(event)`. The three new kinds already fall
  to the final `return false`.
- **`typing-indicator.tsx:70–122`** (`deriveLiveActivity`): ACP calls are resolved and looked up by call key in a
  set of their own, so a finished child call can never mask a running root call with the same id. A running child
  call may still be the live activity shown ("Running c = catalog['CS201']…"): it is what is happening.
- **Transcript export** (`transcript-export/index.ts:283–288`): the filter becomes
  `shouldRenderEvent(event) || isSubagentToolCallEvent(event) || …`, so child calls are exported in time order, as
  today with S1's events (§3 item 7).
- **`record-model-switch-message.ts`, `model-command-event-anchor.ts`**: unchanged; they use `shouldRenderEvent`, so
  a `/model` message anchors to a root event, never to a hidden child call.
- **`messages.tsx`**: §4.6. **`conversation-websocket-context.tsx`**: unchanged; durable frames reach the store
  through `addEvent` as today.

### 4.6 Rendering

**`EventMessage`'s ACP branch** (`event-message.tsx:236–240`) renders `AcpToolCallCell event={event} depth={0}`.

**`AcpToolCallCell`** wraps today's `GenericEventMessageWrapper` in
`<div data-testid="acp-tool-call" data-acp-tool-call-id={event.tool_call_id} data-acp-session-id={session}
data-acp-tool-call-status={event.status}>` (the session attribute absent for the root; §4.12) and renders `SubagentBlock cellKey={toolCallKey(...)} depth={depth + 1}` below the card, indented with a left rule. The
card itself is unchanged, so the title ("Running …", `get-acp-tool-call-content.ts:37–42` strips the agent's `Run`),
the details and the success mark are today's. The data attributes are what the E6 helpers read (§6.3).

**`SubagentBlock`** selects `placement.byCell.get(cellKey)` and `placement.cellSummaries.get(cellKey)`; renders
nothing when there are none. Otherwise a toggle button (`aria-expanded`, `aria-controls`, like `EventGroup`) whose
label is the summary: `3 sub-agents · 2 done · 1 running`, the count parts in a fixed order (done, running, waiting,
stopped, limit, refused, unconfirmed, other; zero parts omitted), with the spinner `EventGroup` uses while any child
runs. Collapsed by default (spec). When the cell's start is not loaded and history is incomplete, a muted line
"Loading earlier sub-agent activity…". Expanded: a list of `SubagentRow`, keyed by session id.

**`SubagentRow`** (memoized; selects `children.get(id)`, `stats.get(id)` and the answer,
`messages.get(stats.answerKey)`): a `li` with
`data-testid="subagent-row"` and `data-acp-session-id`. Its header is a toggle button (status icon and label, title,
the answer's first line in quotes, `N tool calls`) and, outside the button, the cost and `StopSubagentButton`.
Collapsed by default. Expanded, it mounts `SubagentTranscript`; collapsed rows mount nothing below their header.
Depth beyond 6 keeps nesting in the DOM without further indentation and shows its depth beside the title.

**`SubagentTranscript`** (selects `transcripts.get(id)`, `placement.byAnchor.get(id)` and, once history is complete,
`placement.pending`): first the **task**, the latest version of `messages[firstMessageTo[routeKey(parent, id)]]`
(else the snapshot's `description`, else nothing), then the transcript items merged with the anchored grandchildren
by `at`:

| Item | Renders |
|---|---|
| `tool_call` | `AcpToolCallCell` for `toolCalls.get(key).latest`, at `depth` — the recursion |
| `text`, `thought` true | `CollapsibleThinking`, as the root's reasoning |
| `text`, `thought` false | `MarkdownRenderer` |
| `message` whose recipient is a known child of this session | nothing (it is that child's task) |
| `message` sent by this session | "To {name}" and the text; `name` is the recipient's title, or "the main agent" for an id that is not a known child |
| `message` sent by another session | "From {name}" and the text |
| anchor | `SubagentRow` for the anchored child |

**The root's flow.** `Messages` selects `placement.byAnchor.get(ROOT_SESSION)` and `placement.pending`, reads
`SubagentHistoryContext`, computes `anchorsForParent(...)` in a `useMemo`, and renders
`interleaveSubagentAnchors(renderedItems, anchors)`: an anchor goes before the first item that starts after it (an
item's start is its first event's timestamp), so a child placed at the root's message to it appears where that
message was sent. After the items, `UnplacedSubagents`. `Messages`' memo comparator is unchanged: the new hook
re-renders it when anchors change, and they change rarely.

**Render keys.** `renderKeyOf(event)` is `acp-` plus `toolCallKey(...)` for an ACP call and the event id otherwise;
`Messages` uses it for both keys of a single item (`messages.tsx:85, 104`). Child cards are keyed by call key inside
their transcript.

**`UnplacedSubagents`** (once history is complete): one warning block per missing parent, "1 sub-agent could not be
placed: its parent session n7 is not in this conversation.", then its rows. It is never merged into the root's flow.

**Read-only views and Stop.** Components never render Stop when the source is `readOnly` (decision K).

### 4.7 Status, cost and Stop

**Status** (`getSubagentStatus`), from the latest snapshot, or from `lastConfirmed` when the latest is a reconnect
snapshot (`source === "environment"`) or its state is null:

| Reported | Category | Shown |
|---|---|---|
| `running` | running | spinner, "running" |
| `requires_action` | waiting | "waiting for action" |
| `idle` + `end_turn` (or no reason) | done | ✓ "done" |
| `idle` + `cancelled` | stopped | ■ "stopped" |
| `idle` + `max_tokens` or `max_turn_requests` | limited | "stopped at a limit" |
| `idle` + `refusal` | refused | "refused" |
| `unknown`, or any other string | other | the reported string, as it is (S1 §5 rule 4) |
| latest unconfirmed and nothing confirmed loaded | unconfirmed | "not confirmed since reconnecting", no spinner |
| latest unconfirmed, last confirmed active (running, waiting) | unconfirmed (`stale`) | the last state with "last known", no spinner |
| latest unconfirmed, last confirmed idle | that idle category (`stale`) | as above, without a marker: an ended agent's record is history either way |

**Cost** (`formatSubagentCost`): `null` or absent → nothing (unknown, not zero, D1 §6.2); `USD` → `$0.0004`
(`toFixed(4)`, the format Canvas uses for costs, `budget-usage-text.tsx:21`, `cost-section.tsx:24`); another
currency → `0.0004 EUR`. Never added (decision J).

**Stop** (`StopSubagentButton`, `canStopSubagent`, `isStopWithheld`):

| Latest snapshot | Control |
|---|---|
| `source` agent, state `running` or `requires_action`, `cancellable` | **Stop**, enabled, `aria-label` "Stop {title}" |
| the same, not `cancellable` | Stop, `aria-disabled`, tooltip: "This agent cannot stop a single sub-agent. Stop ends the whole turn." (the spec's sentence) |
| any other (idle, unconfirmed, a reconnect snapshot) | none |
| any, in a read-only view | none |

Click → `useCancelAcpSession().mutate({ conversationId, conversationUrl, sessionApiKey, sessionId })`, with the
conversation from `useActiveConversation()`, as `ConversationConfirmationButtons` does. On success the button reads
"Stopping…" and stays disabled for as long as the row stays mounted and the child's state is still running or
waiting; the child's own `idle`/`cancelled` snapshot then removes it. On a refusal the button returns and an error
toast shows `getApiErrorMessage(error, fallback)`, which is S1's `detail` (409: "ACP session … does not accept cancel;
cancel the conversation's turn instead."; 504 and 404 likewise). The mutation never touches the index (decision I).

`EventService.cancelAcpSession` calls `new ConversationClient(getAgentServerClientOptions({ conversationUrl,
sessionApiKey })).cancelAcpSession(conversationId, sessionId)`: the conversation's runtime host with its session key,
the path `respondToConfirmation` takes (`event-service.api.ts:40–55`). It is the same for local and Cloud runtimes,
and it is a typed client call, as `no-direct-agent-server-calls.test.ts` requires.

### 4.8 History completeness and scroll-follow — `chat-interface.tsx`

Three additions, all in the region the chat's history and scroll code already occupies:

1. **History flag.** The scroll container is wrapped in `SubagentHistoryContext.Provider value={!hasMoreOlderEvents}`
   (`hasMore` from `useLoadOlderEvents`, `:193–197`).
2. **Backfill.** `maybeLoadOlder` (`:224–256`) takes `{ force }`; forced, it skips the "near the top or no overflow"
   test and keeps everything else (one load at a time, scroll position preserved, errors to the banner). A new effect
   calls it forced while `subagents.needsOlderHistory && hasMoreOlderEvents && !backfillFailed`, re-run on
   `allConversationEvents.length`: each page that lands grows the event list and chains the next, a failed page sets
   `backfillFailed` (reset with the conversation id) and stops the chain, so a broken server is not hammered at the
   event rate. The existing auto-load effect (`:455–463`) is untouched.
3. **Scroll-follow.** The bottom-following effect (`:418–443`) also depends on `subagents.version`. Expanded
   sub-agent content grows without `renderableEvents.length` changing, so without this a user pinned to the bottom
   would watch a live fan-out grow out of view; and a backfilled page that holds only child events would leave its
   saved scroll geometry unrestored.

### 4.9 Read-only views — `routes/shared-conversation.tsx`

`useStaticSubagentSource(conversationEvents)` builds an index with `buildSubagentIndex` (memoized on the events
array) and marks it `readOnly`; the route wraps its `Messages` in `SubagentSourceContext.Provider` and
`SubagentHistoryContext.Provider value={!hasNextPage}`. Shared views load pages oldest first, so parents always
precede their children and nothing is ever pending for long. Any other component that renders `Messages` from its own
events does the same; library consumers who render from the event store need nothing.

### 4.10 Strings

All new copy goes through `t()` with keys in `src/i18n/translation.json`, 15 languages each, inserted as one block
right after `EVENT_GROUP$COLLAPSE` (§8 row 5); `npm run make-i18n` and `check-translation-completeness` as the guide
says. The `" · "` separator is a non-localizable glyph with a one-line `eslint-disable-next-line
i18next/no-literal-string`, as the guide allows.

| Key | English |
|---|---|
| `SUBAGENTS$COUNT_one` / `_other` | `{{count}} sub-agent` / `{{count}} sub-agents` |
| `SUBAGENTS$SUMMARY_PART` | `{{count}} {{status}}` |
| `SUBAGENTS$STATUS_RUNNING`, `_WAITING`, `_DONE`, `_STOPPED`, `_LIMITED`, `_REFUSED`, `_UNCONFIRMED` | `running`, `waiting for action`, `done`, `stopped`, `stopped at a limit`, `refused`, `not confirmed since reconnecting` |
| `SUBAGENTS$LAST_KNOWN` | `last known` |
| `SUBAGENTS$EXPAND`, `SUBAGENTS$COLLAPSE` | `Show sub-agents`, `Hide sub-agents` |
| `SUBAGENTS$EXPAND_ONE`, `SUBAGENTS$COLLAPSE_ONE` | `Show {{title}}`, `Hide {{title}}` |
| `SUBAGENTS$UNTITLED` | `Sub-agent {{id}}` |
| `SUBAGENTS$DEPTH` | `depth {{depth}}` |
| `SUBAGENTS$TOOL_CALLS_one` / `_other` | `{{count}} tool call` / `{{count}} tool calls` |
| `SUBAGENTS$TASK` | `Task` |
| `SUBAGENTS$MESSAGE_TO`, `SUBAGENTS$MESSAGE_FROM` | `To {{name}}`, `From {{name}}` |
| `SUBAGENTS$MAIN_AGENT` | `the main agent` |
| `SUBAGENTS$STOP`, `SUBAGENTS$STOP_LABEL` | `Stop`, `Stop {{title}}` |
| `SUBAGENTS$STOPPING` | `Stopping…` |
| `SUBAGENTS$STOP_WITHHELD` | `This agent cannot stop a single sub-agent. Stop ends the whole turn.` |
| `SUBAGENTS$STOP_FAILED` | `Could not stop the sub-agent.` (only when the server gave no `detail`) |
| `SUBAGENTS$UNPLACED_one` / `_other` | `{{count}} sub-agent could not be placed: its parent session {{parent}} is not in this conversation.` / `{{count}} sub-agents could not be placed: their parent session {{parent}} is not in this conversation.` |
| `SUBAGENTS$LOADING_EARLIER` | `Loading earlier sub-agent activity…` |

### 4.11 The upstream spec file — `specs/acp-subagent-sessions.md`

In the format of `specs/backend-management.md`; code and tests carry `// @spec SUB-00N — …` above the block that
implements or pins each:

- **SUB-001** Each ACP sub-agent session renders inside the tool call that spawned it, recursively.
- **SUB-002** Without a loaded spawning call, a sub-agent renders at its parent's message to it, else at its
  announcement, once the conversation's history is complete.
- **SUB-003** A sub-agent whose parent session is not in the conversation is shown apart, never in the root's flow.
- **SUB-004** The root's flow shows only the root session's work.
- **SUB-005** Each sub-agent shows its latest state; an unconfirmed state never shows a spinner.
- **SUB-006** Each sub-agent shows its latest reported cost; costs are never added.
- **SUB-007** Stop is offered only for a running sub-agent that granted cancel on the live connection; success is
  shown only when the agent reports it.
- **SUB-008** Opening a conversation loads the older history its visible sub-agents need, and no more.
- **SUB-009** Agents without sub-agent sessions render as before.
- **SUB-010** 50 sub-agents × 5 tool calls arriving at 60 events per second leave the chat responsive to scrolling
  within 1 s, with every sub-agent expanded.
- **SUB-011** The test ids and data attributes of §4.12 are stable: renaming one is a breaking change for the
  end-to-end tests that use them.

### 4.12 Stable test ids

D5's E12 drives the real desktop app and must not depend on text (D5 §8.4); C1's own Playwright helpers read the
same hooks. These are a contract (`SUB-011`): each is a `data-testid` (or a data attribute on one) written inline, as
upstream writes its test ids, and listed in `specs/acp-subagent-sessions.md` so a rename shows up in review.

| Element | `data-testid` | Data attributes and states |
|---|---|---|
| An ACP tool call (a cell), root or child | `acp-tool-call` | `data-acp-tool-call-id`; `data-acp-session-id` (absent for the root); `data-acp-tool-call-status`: `pending`, `in_progress`, `completed`, `failed` |
| The sub-agents of one cell | `subagent-block` | `data-subagent-count` |
| Its summary toggle | `subagent-block-toggle` | `aria-expanded` |
| One child | `subagent-row` | `data-acp-session-id`; `data-subagent-status`: §4.7's category (`running`, `waiting`, `done`, `stopped`, `limited`, `refused`, `unconfirmed`, `other`); `data-subagent-stale` when the state is the last known one |
| Its toggle | `subagent-row-toggle` | `aria-expanded` |
| Its title, status label, answer, tool-call count, cost | `subagent-title`, `subagent-status`, `subagent-answer`, `subagent-tool-calls`, `subagent-cost` | — |
| Its Stop | `subagent-stop` | `data-subagent-stop`: `ready`, `stopping` or `withheld` (`aria-disabled` in the last two) |
| Its expanded transcript, and the task at its top | `subagent-transcript`, `subagent-task` | — |
| Children whose parent session is missing | `subagent-unplaced` | `data-missing-parent-session-id` |
| "Loading earlier sub-agent activity…" | `subagent-loading-earlier` | — |

The message box already has one (`chat-input`, `chat-input-field.tsx:71`); C1 adds none outside the tree. C2
defines its own for the option picker, the slash menu's items and the header panel's button (D5 §8.4).

---

## 5 · Performance: the 50 × 5 load case

E6: 50 children × 5 cells at 60 events/s; null: over 1 s to respond to a scroll. About 1,100 events: per child an
announcement, a task, ~5 text runs, 10 call events, an answer, an idle snapshot and cost snapshots (D1 throttles to
two a second per running child, so with many children running, cost snapshots alone can exceed 60/s).

**Work per event, today, which C1 does not change:** the store copies `events` and `eventIds` and runs
`handleEventForUI` (O(events)); `ChatInterface` re-renders on every store change (it subscribes to the arrays);
`Messages` re-renders when the last event changes and recomputes `actionById` and `groupEvents` (O(events)); its
memoized `EventMessage`s skip. At 1,100 events this is microseconds of array work per event.

**Work per event that C1 adds:** the fold copies the changed maps once (O(children) ≤ 50 entries for `children`,
O(calls) ≈ 300 for `toolCalls`) and recomputes placement only when it is dirty (O(children)). React re-renders only
the components whose selected slice changed (decision B): a cost snapshot re-renders one row; a child's new call
appends one item to that child's transcript (re-rendering that transcript, if expanded, whose other cards are
memoized); a state change re-renders one row and one summary.

**What the DOM holds:** collapsed by default, a 50-child block is one line; expanded, 50 row headers; a row's
transcript exists only while that row is expanded. Fully expanded, 50 × 5 is about 300 cards, which upstream's
markdown performance test (`tests/e2e/conversation-markdown-render-performance.spec.ts`) shows Canvas handles at much
larger sizes.

**If E6 fails anyway:** first `content-visibility: auto` with `contain-intrinsic-size` on rows (CSS, no dependency);
then throttling the fold's store commits to one per animation frame, as the WebSocket already does for streaming
deltas (`createStreamingDeltaBatcher`). Both are local changes that keep every signature here.

---

## 6 · Testing

Upstream's layout and rules (`AGENTS.md`, the e2e-testing skill): Vitest beside its peers under `__tests__/` (or
co-located where the module's tests already are), Arrange–Act–Assert, the underlying service mocked rather than the
hook, existing files extended where natural, each test named for the property it pins, `// @spec SUB-00N` above it.
Upstream's full suite (764 Vitest files, `npm run lint`, `npm run build`, `npm run build:lib`) stays green; no
existing test needs editing, because decision L keeps every path without S1's events byte-identical except render
keys. Fixtures are plain event objects in the shape S1 stores (field names from S1 A.4), built by one helper,
`__tests__/helpers/subagent-events.ts`, so every test reads like the walkthrough in §2.

### 6.1 Pure modules (Vitest, no DOM)

`__tests__/utils/subagents/subagent-index.test.ts`:

| Test | Pins |
|---|---|
| `rebuilds parent links from each child's latest snapshot` | S1 §5 rule 1; three levels |
| `places a child in the tool call that spawned it` | rule 2, first clause; the key pairs session and id |
| `keeps tool calls of different sessions with the same id apart` | decision G |
| `places a child without a spawning call at its parent's message, else at its announcement` | rule 2's fallbacks |
| `keeps the newest snapshot when an older page arrives later` | §1.3 C; `firstAt` moves earlier, `latest` does not regress |
| `orders a child's transcript by first event, ties by arrival` | rule 3 |
| `upserts a message and keeps its place` | rule 3, messages |
| `waits for a parent session that is not loaded` | pending `parent-session` |
| `waits for a named spawning call that is not loaded, with its fallback` | pending `parent-call` |
| `needs older history until every spawning call's start is loaded` | §4.4, second condition |
| `needs older history for a transcript whose session was never announced in the loaded pages` | §4.4, third condition |
| `keeps every unchanged record, transcript, cell list and summary` | decision B; identity, by `toBe` |
| `does not recompute placement for a cost-only snapshot` | `placement` identity unchanged, `children` changed |
| `returns the same index for events that are not about ACP sessions` | identity |
| `ignores events from the planning agent` | §4.3 |
| `refuses to recurse into a parent loop` | defensive, §4.4 item 1 |
| `builds the same index from a page in any order` | `buildSubagentIndex` over shuffled pages equals in-order |

`__tests__/utils/subagents/subagent-status.test.ts`, table-driven: every row of §4.7's status table; `canStop` and
`isStopWithheld` over state × grant × source; `formatSubagentCost` for null, USD and another currency; summaries in
the fixed order.

### 6.2 Components, store and consumers (Vitest + Testing Library)

`__tests__/components/conversation-events/chat/subagents/subagent-block.test.tsx` seeds the real event store with
fixture events (`useEventStore.getState().addEvents(...)`, the default source; real data, no mocks), renders
`AcpToolCallCell`, folds further events to play a run forward, and spies `EventService.cancelAcpSession`, as
`__tests__/MSW.md` recommends for services. The read-only case renders through `useStaticSubagentSource`.

| Test | Pins |
|---|---|
| `shows a collapsed summary counting children by state` | spec bullet 2; "3 sub-agents · 2 done · 1 running" |
| `expands to each child's cells and their own sub-agents` | SUB-001 to depth 3 |
| `shows each child's latest cost and never a sum` | SUB-006 |
| `offers Stop only for a running child that granted cancel` | SUB-007 |
| `explains why Stop is unavailable when the agent withheld cancel` | the spec's failure cell, its sentence on hover |
| `shows the last known state without a spinner or Stop after a reconnect` | SUB-005, S1 §5 rule 7 |
| `asks to cancel and waits for the child's own cancelled state` | Stopping… until a folded idle/cancelled snapshot |
| `shows the server's reason when a cancel is refused` | 409 `detail` in the toast |
| `never offers Stop in a read-only view` | decision K |
| `shows a child's task first and its answer last` | §4.6 transcript table |
| `says earlier activity is loading while the cell's start is missing` | §4.6 |

Extended files:

| File | Tests |
|---|---|
| `__tests__/components/conversation-events/chat/messages-subagents.test.tsx` (new) | `main flow shows only the root's work` (SUB-004) · `anchors a child without a spawning call at the root's message to it` · `shows children of a missing parent apart once history is complete` (SUB-003) · `renders agents without sub-agent sessions as before` (SUB-009: no `subagent-block` in the DOM, the ACP card unchanged) · `keeps sub-agents expanded when the spawning call completes` (decision H) |
| `__tests__/stores/use-event-store.test.ts` | `folds sub-agent events with each event and each page` · `clears the sub-agent index with the conversation` · `an older page does not override a newer snapshot` |
| `__tests__/utils/handle-event-for-ui.test.ts` | `keeps ACP tool calls of different sessions apart` |
| `__tests__/components/conversation-events/chat/event-content-helpers/should-render-event.test.ts` | `hides tool calls made inside a sub-agent session` · `renders root ACP tool calls as before` |
| `__tests__/components/features/chat/typing-indicator.test.ts` | `a finished child call does not mask a running root call with the same id` |
| `src/utils/transcript-export/index.test.ts` | `exports tool calls made inside sub-agent sessions` |
| `src/api/event-service/event-service.api.test.ts` | `cancelAcpSession posts to the conversation's runtime with its session key` (MSW on the route, the network boundary) · `… rejects with the server's detail on 409` |
| `__tests__/components/chat/chat-interface.test.tsx` | `loads older pages until the spawning call's start is loaded` (MSW events search answers pages; asserts the `timestamp__lt` requests and that they stop) · `stops loading older pages after a failure` |
| `__tests__/routes/shared-conversation-viewer-behavior.test.tsx` | `nests sub-agents in a shared conversation` |

### 6.3 End to end, through the real agent-server (Playwright, mock-LLM suite)

`tests/e2e/mock-llm/conversations/mock-llm-acp-subagents.spec.ts`, in the mock-LLM suite because it is the one that
starts the real stack (`bin/agent-canvas.mjs`: the production build, the agent-server our wiring commit installs,
the ingress) — E6 in the fork, and C1's Gate B live tier (spec §4 layer 5: "D3, C1, C2, C3: through their end-to-end
tests"). The ACP agent is S1's scripted agent (`tests/fixtures/acp/scripted_agent.py`) in `--transcript` mode, so
every state is deterministic, configured through `configureScriptedAcpAgent` (A.9) as an ACP agent profile with
`acp_subagents: true` (which needs §9.1 item 1) and the flags `--transcript <file> --wait-timeout 120`, so a test has
two minutes to press Stop at a wait point. The three tests on `nested-stop` share one conversation, in order
(`test.describe.configure({ mode: "serial" })`, as the existing ACP spec does).

**Getting the scripted agent.** A new step in `.github/workflows/mock-llm-e2e.yml`, before the tests: read
`config/defaults.json`; take `sources.agentServerGitRepo` and `sources.agentServerGitRef` when the wiring commit set
them (C3 §2.1's keys), else `https://github.com/OpenHands/software-agent-sdk` at `v${versions.agentServer}`; fetch
that ref with `--depth 1` into `.tmp/sdk`, sparse to `tests/fixtures/acp`; export
`SCRIPTED_ACP_AGENT=$PWD/.tmp/sdk/tests/fixtures/acp/scripted_agent.py`. It runs with the existing
`.mock-llm-venv` Python, which has `agent-client-protocol` through `openhands-sdk`. The spec skips with a reason
when `SCRIPTED_ACP_AGENT` is unset locally and fails in CI. Under the Docker config it skips unless
`SCRIPTED_ACP_AGENT_CONTAINER` names a mounted copy (§10 item 5).

**Transcripts** (`tests/e2e/mock-llm/fixtures/acp-subagents/`, S1 §4.10's JSONL with client lines as wait points):

| File | Plays |
|---|---|
| `nested-stop.jsonl` | Root cell `cell-1`; children `child-x` (cancel) and `child-y` (no cancel) both running; `child-x`'s cell `cell-x1` spawns `child-z` (cancel); costs on each; then a **wait for `session/cancel` of `child-x`**; then `child-z` and `child-x` idle/cancelled, `cell-x1` failed, `child-y` idle/end_turn with an answer; root completes with an answer. |
| `fallback-placement.jsonl` | `child-m` announced on the root without `parentToolCallId`, with a root task message after a root cell; `child-a` with neither (placed at its announcement); `child-g` naming a call never sent; `child-o` announced on an unknown session `ghost` (could not be placed). The last relies on S1's router registering a child announced on an unannounced session with that session as its parent (S1 §4.3, "the first update for an unknown id announces it"); if S1's implementation drops it instead, this case is covered by Vitest only and the as-built document says so. |
| generated at test time by `writeFanoutTranscript` | one root cell, 50 children × 5 cells each, interleaved as concurrent children are, costs and idles, about 1,100 updates. |

**Tests** (serial, each a `test.step` sequence, every assertion on behaviour):

| Test | Asserts |
|---|---|
| `nests each sub-agent under the call that spawned it` | `nested-stop`: after `expandAllSubagents`, `readRenderedSubagentTree(page)` equals `readStoredSubagentTree(request, id)`; the summary reads "2 sub-agents · 2 running" while waiting; `child-x` shows `$0.0004`; no `child-*` card is in the root's flow; the root's answer contains no child text |
| `stops one sub-agent and its branch` | Stop on `child-y` is disabled and its tooltip is the spec's sentence; Stop on `child-x` is enabled; clicking posts `…/acp/sessions/child-x/cancel` (`page.waitForRequest`); `child-x` and `child-z` turn "stopped", `cell-x1` turns failed, Stop disappears; `child-y` turns done |
| `shows the same tree after reloading` | reload: the tree from REST equals the stored tree; no enabled Stop anywhere |
| `places sub-agents without a spawning call and shows orphans apart` | `fallback-placement`: `child-m` sits after the root cell, where the task was sent; `child-a` at its announcement; `child-g` at its announcement once history is complete; `child-o` in the "could not be placed" block naming `ghost`, never in the root's flow |
| `stays responsive while 50 sub-agents with 5 tool calls each stream in` | the generated fan-out, paced at 60 events/s (§9.1 item 2); every child expanded as it appears; `probeScrollResponsiveness` until the root completes: `maxScrollLatencyMs < 1000` (E6's null) and the rendered tree equals the stored one |

**The replay spec**, `tests/e2e/mock-llm/conversations/mock-llm-acp-replay.spec.ts` (D5 §8.4's ask): one test per
path in `OH_ACP_REPLAY_TRANSCRIPTS` (paths separated by the platform's path delimiter; the spec is skipped when the
variable is unset or empty), named after the file. Each configures the scripted agent with `--transcript <path>`
and `acp_subagents: true`, sends one message, waits for the turn to end, expands everything, and asserts that
`readRenderedSubagentTree(page)` equals `readStoredSubagentTree(request, id)`: the same children, the same parent
sessions, the same spawning calls, the same tool calls per child. In the fork's CI it plays C1's three transcripts
and the generated fan-out's file as a smoke check; D5 points it at D1's recordings (§6.4).

`readRenderedSubagentTree` reads nesting only: a row's parent is its nearest enclosing `subagent-row` (or the root),
its call the nearest enclosing `acp-tool-call` inside that parent, its own calls the `acp-tool-call`s whose nearest
enclosing row is it. A row's own attributes are never compared with themselves. `readStoredSubagentTree` keeps the
newest `ACPSubagentEvent` per child and the `ACPToolCallEvent`s per session from the events search route, and nulls
a `parentToolCallId` that names no stored call, which is exactly S1 §5 rule 2's placement.

`probeScrollResponsiveness` schedules a scroll of the chat container every 250 ms and measures, for each, the time
from when it was due to the next animation frame after it ran, so main-thread blocking counts; it also records long
tasks with a `PerformanceObserver`, as the markdown performance test does. No screenshot is evidence; Playwright's
own failure screenshots and videos stay as debugging artifacts.

### 6.4 The replay D5 runs (E6, second half)

D5's `canvas-replay` job (D5 §7.5) checks out the Canvas fork at its pinned commit and the SDK fork at its pinned
commit, and from the Canvas checkout runs
`npx playwright test --config=playwright.mock-llm.config.ts tests/e2e/mock-llm/conversations/mock-llm-acp-replay.spec.ts`
with:

- `OH_ACP_REPLAY_TRANSCRIPTS`: D1's native golden recordings (`tests/acp/golden/*.native.jsonl` in deep-reasoning,
  joined with `:`), outgoing-only, which S1's player replays with inferred wait points;
- `SCRIPTED_ACP_AGENT`: `<sdk checkout>/tests/fixtures/acp/scripted_agent.py`;
- what the mock-LLM config already needs: `npm ci`, a built `build/` (`npm run build:app`), Playwright's Chromium, and
  `MOCK_LLM_PYTHON` pointing at a virtualenv with `openhands-sdk` (the config starts the mock LLM server even though
  this spec never calls it), as `.github/workflows/mock-llm-e2e.yml` sets them up.

Nothing in the spec reads `_meta.deep_reasoner`; it compares parent links and tool calls per child only.

### 6.5 Mutation testing and upstream's guards

`npm run test:mutation:diff` (Stryker on the diff) runs on the branch; a surviving mutant in `subagent-index.ts`,
`subagent-placement.ts` or `subagent-status.ts` is a missing test and gets one. Survivors in components are reviewed
and either killed or named in the as-built document.

### 6.6 What each layer of the spec maps to

| Spec §4 layer | C1's part |
|---|---|
| 1 · deterministic, every push | §6.1–§6.2 (Vitest, in `npm test`) |
| 2 · contract and golden replays | §6.4, run by D5 |
| 3 · inside the fork | §6.1–§6.3 in upstream's folders; upstream's suite; the draft PR against the fork's `main` (§7); Stryker on the diff |
| 4 · the desktop app, end to end | D5's flow "see the nested tree" uses C1's helpers |
| 5 · Gate B's live tier | §6.3, run on demand (`workflow_dispatch` of `mock-llm-e2e.yml` on the branch) at the branch's head |

---

## 7 · Upstream guards and the pull request

**The branch** `feat/acp-subagent-sessions`, cut from the fork's `deep-reasoning` once it carries the wiring commit
with an SDK tarball that includes S1's TypeScript client (§9.3), in six commits, each green on its own and
cherry-pickable onto `main`:

1. `feat(events): ACP sub-agent session events and call keys` — the types and guards, `toolCallKey`, the
   `handleEventForUI`, typing-indicator and export changes, their tests.
2. `feat(chat): sub-agent index in the event store` — `subagent-index.ts`, `subagent-placement.ts`,
   `subagent-status.ts`, the store field, their tests.
3. `feat(chat): nest ACP sub-agent sessions under the tool call that spawned them` — the components, `Messages`,
   `EventMessage`, `shouldRenderEvent`, the shared view, the strings, `specs/acp-subagent-sessions.md`, their tests.
4. `feat(chat): stop one ACP sub-agent session` — the service method, the mutation, the button, their tests.
5. `feat(chat): load the history a sub-agent fan-out needs` — `chat-interface.tsx`, its tests.
6. `test(e2e): ACP sub-agent sessions through the agent-server` — the spec, helpers, transcripts, the workflow step.

**Upstream's guards** (spec §4 layer 3): the branch, cherry-picked onto the fork's `main`, gets a draft PR there that
is never merged, and runs upstream's CI as upstream would: `npm run lint` (typecheck, ESLint including the i18n and
query-key rules, Prettier), `npm test`, `npm run build`, `npm run build:lib`, `npm pack --dry-run`; the PR
description check; and, by dispatch, the mock-LLM end-to-end workflow. Upstream's PR would additionally need a
released `@openhands/typescript-client` with S1's additions (its guide: release the client first, then bump), so
upstream review waits for S1's server and client; in our fork the wiring tarball provides both. The PR description
uses upstream's template and leaves its `HUMAN:` section to Michael. No issue or pull request is opened on any
upstream repository.

**Upstream merges** (spec Q1 (a)): conflicts concentrate in `messages.tsx`, `event-message.tsx`'s ACP branch,
`chat-interface.tsx`'s history region and `use-event-store.ts`; everything else is new files.

---

## 8 · Where C1 and C2 touch the same files

C2 (App header panels, agent commands, option picker) is being designed at the same time; this lists every file C1
changes that C2 plausibly changes too, from C2's spec and S2's contract for it (S2 §7: `ACPSessionControlsEvent`,
the slash menu, the option picker, header panels). Each rule lets either PR land first.

| # | File | C1 | C2 (expected) | Rule for either order |
|---|---|---|---|---|
| 1 | `src/types/agent-server/core/events/index.ts` | export `./acp-subagent-event` | export its controls event | One line each, alphabetical; the second to land keeps both. |
| 2 | `src/types/agent-server/core/openhands-event.ts` | three union members after `ACPToolCallEvent` | `ACPSessionControlsEvent` | Union of both; C1's members directly after `ACPToolCallEvent`, C2's after C1's or anywhere else. |
| 3 | `src/types/agent-server/type-guards.ts` | four guards directly after `isACPToolCallEvent` | `isACPSessionControlsEvent` | C1's block stays contiguous after `isACPToolCallEvent`; C2 adds its guard after that block or at the end. |
| 4 | `should-render-event.ts` | the ACP branch (`:139–141`) | none needed (an unknown kind already returns false); if it adds an explicit branch, before the final `return false` | Different hunks. |
| 5 | `src/i18n/translation.json` | one `SUBAGENTS$` block right after `EVENT_GROUP$COLLAPSE` | its own keys | C2 does not insert after `EVENT_GROUP$COLLAPSE`; otherwise JSON hunks at different anchors merge cleanly. Re-run `make-i18n` after merging. |
| 6 | `src/api/event-service/event-service.api.ts` and its test | `cancelAcpSession` after `respondToConfirmation` | possibly a wrapper for the controls (events search by kind) | Separate methods and `describe` blocks; C1's directly after `respondToConfirmation`, C2's elsewhere. |
| 7 | `src/components/features/chat/chat-interface.tsx` | the history region: `useLoadOlderEvents` use, `maybeLoadOlder`, the two scroll effects, the provider around the scroll container (`:189–598`) | the composer region (`InteractiveChatBox` props for the picker, `hasConversationStarted`), `:600–684` | Each stays in its region; if C2 needs a value from the history region, it adds a new line rather than editing C1's effects. |
| 8 | `src/stores/use-event-store.ts` | the `subagents` field and its three call sites | if C2 derives the current controls from the event store, the same pattern | Each feature's derived field is one field and one call in `appendEvent`, `addEvents` and the clears; the second to land puts its call after the first's. |
| 9 | `tests/e2e/mock-llm/utils/acp-subagents.ts` (`SCRIPTED_ACP_AGENT`, `configureScriptedAcpAgent`) | creates it | needs the same to run the scripted agent with S2's flags | **Shared**: whoever lands first creates both exports with A.9's signatures; the other imports them and adds nothing to their shape. |
| 10 | `.github/workflows/mock-llm-e2e.yml` | the step that fetches the scripted agent and exports `SCRIPTED_ACP_AGENT` | needs the same | **Shared**: one step, whoever lands first; the other reuses the variable. |
| 11 | `package.json`, `package-lock.json` | none | none | The wiring commit points `@openhands/typescript-client` at one tarball holding S1's and S2's client additions; re-pointed once, not per feature. |
| 12 | `config/defaults.json` | none (decision L) | none expected (S2 decision H: capability detection) | If C2 raises `minimumAgentServer`, C1 is unaffected. |
| 13 | `specs/` | new `acp-subagent-sessions.md` | `canvas-extensions.md` (it already plans "conversation panels"), maybe a new file | Different files. |
| 14 | `tests/e2e/mock-llm/test-mapping.json` | none | maybe a mapping | No overlap. |
| 15 | Test ids for E12 (D5 §8.4) | §4.12, all inside the nested tree | the option picker, the slash menu's items, the header panel's button | No shared element; each lists its own in its spec file. |

Files C1 changes that C2 should not need: `messages.tsx`, `event-message.tsx`, `handle-event-for-ui.ts`,
`typing-indicator.tsx`, the transcript export, the shared-conversation route. If C2 does, the rule is the same:
separate hunks, and the second to land rebases.

---

## 9 · What C1 relies on, and what S1 must change

### 9.1 S1 (the contract is S1 §5; these are the changes C1 needs, for the Conductor)

1. **The opt-in must be storable on an ACP agent profile** — agreed: the Conductor has added it to S1's build
   (D5 §8.2 asks the same, with the seed carrying it back). Canvas launches new conversations from the active
   agent profile, not from `agent_settings` (`use-create-conversation.ts:106–121`; the two are mutually exclusive
   launch sources). `ACPAgentProfile` (`profiles/agent_profile.py:223–291`) forbids extra keys (`:86`) and has no
   `acp_subagents`, and `_build_acp_settings` (`profiles/resolver.py:267–308`) forwards a fixed list. So with
   S1 as designed, an ACP profile can never turn the opt-in on: C1's end-to-end tests cannot configure it, and D5's
   setup cannot either. S1 should add `acp_subagents: bool = False` to `ACPAgentProfile`, forward it in the resolver,
   and add a persisted fixture for it like its v7 settings fixture. `ACP_SETTINGS_KEYS` (S1 §4.9) still matters, for
   the legacy `agent_settings` launch path (`agent-server-adapter.ts:1018`), and Canvas's profile editor already
   preserves fields it does not model (`merge-agent-profile-save-input.ts`), so Canvas needs no change for either.
2. **Pacing for the scripted agent's transcripts**: `--transcript-interval-ms MS`, a sleep before each agent line it
   sends, so E6's fan-out arrives at 60 events/s (16 ms). Small and generic. Without it, C1's load test replays as a
   burst, which is a harsher load but a much shorter measuring window; the test then states "at least 60 events/s".
3. **State two ordering facts in S1 §5 as contract**, which S1 §6 already guarantees by construction but C1 relies on
   because Canvas orders by timestamp (decision C): (a) within one child session, event timestamps do not decrease in
   log order, and a reconnect snapshot is later than every earlier event of its child; (b) a spawning call's started
   event is earlier than every event of its subtree. If either stopped holding (say, timestamps assigned when the
   emitter's worker stores an event rather than when the portal creates it), C1's "latest" and its backfill criterion
   would break silently.
4. **Optional:** S1's seed writes a reconnect snapshot for every child that was cancellable *or* active; dr-acp keeps
   `cancel` on idle children (S1 §10), so after every restart every finished child gets one. C1 handles it (an idle
   last-confirmed state is shown as history without a marker), but writing reconnect snapshots only for children
   whose last state was active would keep the log smaller and the meaning sharper. Not needed by C1.

### 9.2 D1

Nothing must change. C1 relies on D1 §5 as S1 stores it: children announced before their traffic, with
`_meta.openhands.parentToolCallId` naming a call already sent (§5.4 rules 1–2), `cancel` on every child, a Stop
acknowledgement as a thought on the child's session, `Failed: …` as a failed child's answer (§3 item 5), and `Run …`
cell titles (§3 item 3). C1 never parses the flat fallback's `#1 › #3` titles: with the opt-in off, dr-acp's flat
stream renders as stock Canvas renders it.

### 9.3 The wiring commit (spec Q2 (a)) and C3

C1's branch needs, before its first commit builds: `package.json` pointing `@openhands/typescript-client` at a
tarball built from an SDK fork ref that contains S1's commit 5 (`ConversationClient.cancelAcpSession`,
`CancelAcpSessionResponse`, `ACP_SETTINGS_KEYS` with `acp_subagents`), and `config/defaults.json`'s `sources`
(C3 §2.1) naming that SDK fork ref, so the mock-LLM stack runs S1's agent-server and the workflow step can fetch the
scripted agent from the same ref. C3 lands first and the wiring commit follows (spec C3); C1 is cut after both.

### 9.4 D5

D5's setup writes `acp_subagents: true` on the dr-acp **agent profile** it makes the default (which needs §9.1 item
1), not only in `agent_settings`. D5's `canvas-replay` job runs §6.4's replay spec with `OH_ACP_REPLAY_TRANSCRIPTS`
(D5 §8.4's name, adopted). D5's E12 ("they appear nested under their cell, each with its state and cost, and one is
stopped with its branch") selects through §4.12's test ids and can reuse `expandAllSubagents` and
`readRenderedSubagentTree` from A.9 over CDP.

### 9.5 Observation for the Conductor, about S2 and C2 (not C1's to change)

S2 §7 tells C2 to read the current controls with `events/search?kind=ACPSessionControlsEvent`. The agent-server
compares `kind` with the module-qualified class name (`event_service.py:548–550`; its own test expects
`kind="ActionEvent"` to match nothing and passes `"openhands.sdk.event.llm_convertible.message.MessageEvent"` to
match, `test_event_service.py:255–262`), so that query returns nothing unless S2 changes the filter or C2 sends
`openhands.sdk.event.<module>.ACPSessionControlsEvent`. This is also why C1 does not fetch sub-agent events by kind
(decision A).

---

## 10 · Open items

1. **§9.1 item 1** (the opt-in on agent profiles) is agreed; C1's end-to-end tests need S1's build with it before
   they can run, so C1's commit 6 lands after it.
2. **E6's threshold in CI.** One second of scroll latency with all 50 children expanded is generous for a desktop,
   unmeasured on a 2-vCPU runner. If it fails there, §5's remedies apply before any threshold changes; a changed
   threshold goes back to Michael, since E6 is his.
3. **A nested transcript export** (§3 item 7): child calls are exported flat, in time order. A nested export would
   reuse `buildSubagentIndex`; not in v1.
4. **A race the backfill inherits:** a live event that lands while an older page is in flight restores the saved
   scroll geometry early (`chat-interface.tsx:418–431` already has this with root events). The backfill makes it more
   likely during a live fan-out; the visible effect is one small jump. Fixing it would mean restoring by anchor
   element instead of by height delta, a change to upstream's scroll code outside C1.
5. **Docker mock-LLM config:** the spec skips there unless the scripted agent is mounted
   (`SCRIPTED_ACP_AGENT_CONTAINER`). Upstream may want the mount added to `playwright.mock-llm-docker.config.ts`;
   v1 ships the desktop app, so C1 does not add it.
6. **Cloud:** Stop goes to the conversation's runtime host, which works for Cloud runtimes; Cloud's App-API event
   history may lack older pages on unpatched backends (`event-service.api.ts`'s fallback returns an empty page), in
   which case history is "complete" early and pending children fall back or show as unplaced. Cloud is out of v1's
   scope; nothing here makes it worse than stock.
7. **`datetime.now()` timestamps** (the SDK's event default) follow the wall clock, so a clock step backwards during
   a run could reorder a child's events in Canvas. Pre-existing for every event Canvas sorts; named, not handled.

---

## Appendix A · Signature reference

Every block is valid TypeScript, typechecked under `strict` with stubs for React, react-query, the client and
Playwright, and Prettier-formatted at upstream's settings. `declare` marks a signature whose body is the
Implementer's; excerpts of existing files show only what C1 adds.

### A.1 `src/types/agent-server/core/events/acp-subagent-event.ts` and the `ACPToolCallEvent` fields

```typescript
import { BaseEvent } from "../base/event";

/**
 * ACPSubagentEvent — an ACP sub-agent session's association with its parent,
 * as the agent-server last stored it (ACP schema 1.24.1, unstable). Each event
 * is the whole association with ACP's patch rules already applied, so the
 * newest event per `acp_session_id` is the child's current state.
 */
export interface ACPSubagentEvent extends BaseEvent {
  kind: "ACPSubagentEvent";

  /**
   * `"environment"` marks the agent-server's own record that the ACP
   * connection the last state came from has ended: state unconfirmed, cancel
   * withdrawn.
   */
  source: "agent" | "environment";

  /** The child's ACP session id. */
  acp_session_id: string;

  /** The parent's ACP session id; absent or null for the root session. */
  parent_session_id?: string | null;

  /**
   * The parent's tool call that spawned the child, from
   * `_meta.openhands.parentToolCallId`. Unique only within the parent session.
   */
  parent_tool_call_id?: string | null;

  title?: string | null;

  description?: string | null;

  /**
   * `running`, `idle`, `requires_action`, `unknown`, an agent-specific value
   * (shown as it is), or null: no confirmed current activity.
   */
  state?: string | null;

  /** ACP's stop reason when `state` is `idle`. */
  stop_reason?: string | null;

  /** The agent granted `cancel` for this child on the live connection. */
  cancellable?: boolean;

  /** The child's latest reported cumulative cost; never add it to another. */
  cost?: number | null;

  cost_currency?: string | null;

  /** The association's ACP `_meta`. Opaque: Canvas never reads it. */
  meta?: Record<string, unknown> | null;
}

/**
 * ACPSessionMessageEvent — a message between ACP sessions, as one session's
 * transcript shows it. Upserts: the newest per `(acp_session_id, message_id)`
 * is current.
 */
export interface ACPSessionMessageEvent extends BaseEvent {
  kind: "ACPSessionMessageEvent";

  source: "agent";

  /** The transcript the message belongs to; absent or null for the root. */
  acp_session_id?: string | null;

  message_id: string;

  /** Verbatim ACP session id: the root's real id, never null for the root. */
  sender_session_id?: string | null;

  /** Verbatim ACP session id: the root's real id, never null for the root. */
  recipient_session_id?: string | null;

  text?: string;

  /** The message's ACP `_meta`. Opaque: Canvas never reads it. */
  meta?: Record<string, unknown> | null;
}

/**
 * ACPSessionTextEvent — one run of a child session's own streamed text or
 * reasoning. Append-only, in log order.
 */
export interface ACPSessionTextEvent extends BaseEvent {
  kind: "ACPSessionTextEvent";

  source: "agent";

  /** Always a child session. */
  acp_session_id: string;

  /** True for reasoning (`agent_thought_chunk`), false for the child's text. */
  thought?: boolean;

  text: string;
}
```

```typescript
// src/types/agent-server/core/events/acp-tool-call-event.ts — the two new
// fields, appended after `is_error`; every existing field is unchanged.
export interface ACPToolCallEvent extends BaseEvent {
  /** The ACP sub-agent session the call ran in; absent or null for the root. */
  acp_session_id?: string | null;
  /**
   * The call's latest ACP `_meta`, recorded only for agents with
   * `acp_subagents`. Opaque: Canvas never reads it.
   */
  meta?: Record<string, unknown> | null;
}
```

### A.2 `src/types/agent-server/type-guards.ts` (additions after `isACPToolCallEvent`)

```typescript
/** An ACP tool call made inside a sub-agent session, not the root's. */
export const isSubagentToolCallEvent = (
  event: OpenHandsEvent,
): event is ACPToolCallEvent & { acp_session_id: string } =>
  isACPToolCallEvent(event) && typeof event.acp_session_id === "string";

export const isACPSubagentEvent = (
  event: OpenHandsEvent,
): event is ACPSubagentEvent =>
  "kind" in event && event.kind === "ACPSubagentEvent";

export const isACPSessionMessageEvent = (
  event: OpenHandsEvent,
): event is ACPSessionMessageEvent =>
  "kind" in event && event.kind === "ACPSessionMessageEvent";

export const isACPSessionTextEvent = (
  event: OpenHandsEvent,
): event is ACPSessionTextEvent =>
  "kind" in event && event.kind === "ACPSessionTextEvent";
```

### A.3 `src/utils/subagents/subagent-index.ts`

```typescript
import type { OpenHandsEvent } from "#/types/agent-server/core";
import type { ACPToolCallEvent } from "#/types/agent-server/core/events/acp-tool-call-event";
import type {
  ACPSessionMessageEvent,
  ACPSessionTextEvent,
  ACPSubagentEvent,
} from "#/types/agent-server/core/events/acp-subagent-event";

/** The root session in every key below. S1 stores the root as null. */
export declare const ROOT_SESSION: "";

/** A child's ACP session id, or `ROOT_SESSION`. */
export type SessionRef = string;

export declare function toSessionRef(
  sessionId: string | null | undefined,
): SessionRef;

/** ACP tool-call ids are unique only within a session, so keys pair them. */
export declare function toolCallKey(
  sessionId: string | null | undefined,
  toolCallId: string,
): string;

/** ACP message ids are unique only within a transcript. */
export declare function messageKey(
  transcriptSessionId: string | null | undefined,
  messageId: string,
): string;

/** The first message a transcript addressed to a recipient: its task. */
export declare function routeKey(
  transcriptSessionId: string | null | undefined,
  recipientSessionId: string,
): string;

export interface SubagentRecord {
  /** The newest snapshot in log order, whatever its source. */
  latest: ACPSubagentEvent;
  /** The newest snapshot the agent sent itself; null if only resets loaded. */
  lastConfirmed: ACPSubagentEvent | null;
  /** The earliest loaded snapshot's timestamp: the announcement, once loaded. */
  firstAt: string;
}

export interface ToolCallRecord {
  /** The newest event of the call: started, then terminal. */
  latest: ACPToolCallEvent;
  /** The earliest loaded event's timestamp: where the call sits. */
  firstAt: string;
  /** A pending or in_progress event of the call is loaded. */
  startLoaded: boolean;
}

export interface MessageRecord {
  /** The newest version of the message (ACP messages are upserts). */
  latest: ACPSessionMessageEvent;
  /** The earliest loaded version's timestamp: where the message sits. */
  firstAt: string;
}

export type TranscriptItem =
  | {
      kind: "tool_call";
      /** `toolCallKey(...)`; the record lives in `toolCalls`. */
      key: string;
      at: string;
    }
  | {
      kind: "message";
      /** `messageKey(...)`; the record lives in `messages`. */
      key: string;
      at: string;
    }
  | {
      kind: "text";
      /** Text runs are immutable, so the item holds the event itself. */
      event: ACPSessionTextEvent;
      at: string;
    };

export interface ChildStats {
  /** Tool calls in the child's own transcript (loaded ones). */
  toolCalls: number;
  /** `messageKey` of the newest message the child sent, not to a child. */
  answerKey: string | null;
}

export interface SubagentAnchor {
  sessionId: string;
  /** Timestamp the child is placed at in its parent's flow. */
  at: string;
  /** S1 §5 rule 2: the parent's message to the child, else the announcement. */
  via: "message" | "announcement";
}

export interface PendingSubagent {
  sessionId: string;
  /** Which part of the parent link is not in the loaded events. */
  reason: "parent-session" | "parent-call";
  /** The parent session id, or the spawning tool call id, that is missing. */
  missingId: string;
  parentSessionRef: SessionRef;
  /** Where the child goes once history is complete; null: could not be placed. */
  fallback: SubagentAnchor | null;
}

export interface SubagentSummary {
  total: number;
  running: number;
  waiting: number;
  done: number;
  stopped: number;
  limited: number;
  refused: number;
  unconfirmed: number;
  other: number;
}

export interface SubagentPlacement {
  /** Children placed in each tool call (`toolCallKey`), announcement order. */
  byCell: ReadonlyMap<string, readonly string[]>;
  /** Children placed in a parent's flow without a loaded spawning call. */
  byAnchor: ReadonlyMap<SessionRef, readonly SubagentAnchor[]>;
  /** Children whose parent session or spawning call is not loaded yet. */
  pending: readonly PendingSubagent[];
  /** The summary line of each spawning tool call, keyed like `byCell`. */
  cellSummaries: ReadonlyMap<string, SubagentSummary>;
}

export interface SubagentRecords {
  /** Every known child session, by its ACP session id. */
  children: ReadonlyMap<string, SubagentRecord>;
  /** Every ACP tool call, root and child alike, by `toolCallKey`. */
  toolCalls: ReadonlyMap<string, ToolCallRecord>;
  /** Every directed message, by `messageKey`. */
  messages: ReadonlyMap<string, MessageRecord>;
  /** `routeKey(transcript, recipient)` → `messageKey` of the first one. */
  firstMessageTo: ReadonlyMap<string, string>;
  /** Each child's own transcript, ordered by `at`, then by arrival. */
  transcripts: ReadonlyMap<string, readonly TranscriptItem[]>;
  stats: ReadonlyMap<string, ChildStats>;
}

export interface SubagentIndex extends SubagentRecords {
  placement: SubagentPlacement;
  /** A placement or a spawning call's start waits for an older page. */
  needsOlderHistory: boolean;
  /** Changes whenever anything above changes: a scroll-follow key. */
  version: number;
}

export declare const EMPTY_SUBAGENT_INDEX: SubagentIndex;

/**
 * Fold events into the index. Pure; returns `index` itself when no event
 * concerns ACP sessions, and otherwise a new index that reuses every record,
 * transcript, cell list and summary the events did not change. Events already
 * folded must not be passed again (the event store dedupes by id first).
 */
export declare function foldSubagentEvents(
  index: SubagentIndex,
  events: readonly OpenHandsEvent[],
): SubagentIndex;

/** `foldSubagentEvents(EMPTY_SUBAGENT_INDEX, events)`, deduped by event id. */
export declare function buildSubagentIndex(
  events: readonly OpenHandsEvent[],
): SubagentIndex;
```

### A.4 `src/utils/subagents/subagent-placement.ts`

```typescript
import type {
  PendingSubagent,
  SessionRef,
  SubagentAnchor,
  SubagentPlacement,
  SubagentRecords,
} from "./subagent-index";

export interface PlacementResult {
  placement: SubagentPlacement;
  needsOlderHistory: boolean;
}

/**
 * S1 §5 rules 1–2 over the loaded records, with partial history: a child
 * whose parent session or named spawning call is not loaded is pending, not
 * misplaced. Reuses `previous`'s arrays, maps and summaries wherever the
 * result is equal, so selectors keep their references.
 */
export declare function placeSubagents(
  records: SubagentRecords,
  previous: SubagentPlacement,
): PlacementResult;

/**
 * The anchors a parent's flow renders: the placed ones, plus, once history is
 * complete, the fallbacks of children whose spawning call never turned up.
 * Sorted by `at`; returns `placed` itself when nothing is added.
 */
export declare function anchorsForParent(
  placed: readonly SubagentAnchor[],
  pending: readonly PendingSubagent[],
  parent: SessionRef,
  historyComplete: boolean,
): readonly SubagentAnchor[];

export interface UnplacedGroup {
  /** The parent session id the conversation does not contain. */
  missingParentId: string;
  sessionIds: readonly string[];
}

/** Children whose parent session is not in the conversation, by parent. */
export declare function unplacedGroups(
  pending: readonly PendingSubagent[],
): readonly UnplacedGroup[];
```

### A.5 `src/utils/subagents/subagent-status.ts`

```typescript
import type { SubagentRecord, SubagentSummary } from "./subagent-index";

export type SubagentStatusCategory =
  | "running"
  | "waiting"
  | "done"
  | "stopped"
  | "limited"
  | "refused"
  | "unconfirmed"
  | "other";

export interface SubagentStatus {
  category: SubagentStatusCategory;
  /** `state` or `state / stop_reason` as reported, for `other` and tooltips. */
  reported: string | null;
  /**
   * The status is the last one the agent confirmed before the agent-server's
   * ACP connection was replaced. Never a spinner, never Stop.
   */
  stale: boolean;
}

export declare function getSubagentStatus(
  record: SubagentRecord,
): SubagentStatus;

/** Running or waiting, confirmed on the live connection, with `cancel`. */
export declare function canStopSubagent(record: SubagentRecord): boolean;

/** Running or waiting, confirmed, without `cancel`: Stop shown disabled. */
export declare function isStopWithheld(record: SubagentRecord): boolean;

/** `$0.0004` for USD (Canvas's own format), `0.0004 EUR` otherwise. */
export declare function formatSubagentCost(
  cost: number | null | undefined,
  currency: string | null | undefined,
): string | null;

export declare function summarizeSubagents(
  records: readonly SubagentRecord[],
): SubagentSummary;
```

### A.6 `src/components/conversation-events/chat/subagents/` — source, components, anchors

```typescript
// subagent-source.ts
import type React from "react";
import type { OpenHandsEvent } from "#/types/agent-server/core";
import type { SubagentIndex } from "#/utils/subagents/subagent-index";

export interface SubagentSourceState {
  subagents: SubagentIndex;
}

/**
 * Where sub-agent components read the index from. `useEventStore` satisfies
 * it as it is (it has `getState` and `subscribe`); a read-only view passes one
 * built from its own events.
 */
export interface SubagentSource {
  getState: () => SubagentSourceState;
  subscribe: (listener: () => void) => () => void;
  /** A read-only view (a shared conversation): never offer Stop. */
  readonly readOnly?: boolean;
}

/** Defaults to the live event store, so the chat needs no provider. */
export declare const SubagentSourceContext: React.Context<SubagentSource>;

/**
 * True when no older history remains to load, so a child whose parent link is
 * still missing is final ("could not be placed", or its fallback anchor).
 * Defaults to true.
 */
export declare const SubagentHistoryContext: React.Context<boolean>;

/**
 * Select from the nearest source's index. `selector` must return a stored
 * reference or a primitive (useSyncExternalStore compares by `Object.is`).
 */
export declare function useSubagents<T>(
  selector: (index: SubagentIndex) => T,
): T;

/** A read-only source over a fixed list of events, rebuilt when it changes. */
export declare function useStaticSubagentSource(
  events: readonly OpenHandsEvent[],
): SubagentSource;
```

```typescript
// One block per file in the fork; gathered here for the typecheck.
import type React from "react";
import type { ACPToolCallEvent } from "#/types/agent-server/core/events/acp-tool-call-event";
import type { OpenHandsEvent } from "#/types/agent-server/core";
import type { SubagentAnchor } from "#/utils/subagents/subagent-index";
import type { RenderedItem } from "../group-events";

// acp-tool-call-cell.tsx
export interface AcpToolCallCellProps {
  /** A root or child ACP tool call; its sub-agents are found by its key. */
  event: ACPToolCallEvent;
  /** Nesting depth of the session the call belongs to; the root is 0. */
  depth: number;
}

/** Today's ACP card, plus the sub-agents the call spawned. */
export declare function AcpToolCallCell(
  props: AcpToolCallCellProps,
): React.JSX.Element;

// subagent-block.tsx
export interface SubagentBlockProps {
  /** `toolCallKey` of the spawning call. */
  cellKey: string;
  /** Depth of the children in this block; children of root calls are 1. */
  depth: number;
}

/** The summary line, collapsed by default, and the children when expanded. */
export declare function SubagentBlock(
  props: SubagentBlockProps,
): React.JSX.Element | null;

// subagent-row.tsx
export interface SubagentRowProps {
  sessionId: string;
  depth: number;
}

/** One child: status, title, answer, tool calls, cost, Stop; its transcript. */
export declare const SubagentRow: React.MemoExoticComponent<
  (props: SubagentRowProps) => React.JSX.Element | null
>;

// subagent-transcript.tsx
export interface SubagentTranscriptProps {
  sessionId: string;
  depth: number;
}

/** A child's task, then its entries and anchored children, in log order. */
export declare function SubagentTranscript(
  props: SubagentTranscriptProps,
): React.JSX.Element;

// stop-subagent-button.tsx
export interface StopSubagentButtonProps {
  sessionId: string;
  title: string;
}

/** Enabled iff `canStopSubagent`; disabled with the reason iff withheld. */
export declare function StopSubagentButton(
  props: StopSubagentButtonProps,
): React.JSX.Element | null;

// unplaced-subagents.tsx
/** Children whose parent session is not in the conversation, shown apart. */
export declare function UnplacedSubagents(): React.JSX.Element | null;

// main-flow-anchors.ts
export type MainFlowItem =
  | RenderedItem
  | {
      kind: "subagent";
      anchor: SubagentAnchor;
    };

/**
 * Put each anchored root-level child before the first rendered item that
 * starts after its anchor; items keep their order. Returns `items` itself
 * when `anchors` is empty.
 */
export declare function interleaveSubagentAnchors(
  items: readonly RenderedItem[],
  anchors: readonly SubagentAnchor[],
): readonly MainFlowItem[];

// messages.tsx (excerpt)
/** Stable across an ACP call's started → terminal replacement. */
export declare function renderKeyOf(event: OpenHandsEvent): string;
```

### A.7 Stop: the service method and the mutation

```typescript
// src/api/event-service/event-service.api.ts
import type { CancelAcpSessionResponse } from "@openhands/typescript-client";

// Excerpt: the new static method beside respondToConfirmation.
export declare class EventService {
  /**
   * Ask the agent-server to send ACP `session/cancel` for one sub-agent
   * session (S1's route). Goes to the conversation's runtime host with its
   * session key, as respondToConfirmation does, so local and Cloud runtimes
   * take the same path. Rejects with the client's HttpError: 409 when the
   * child holds no live `cancel` grant, 404 when it is unknown.
   */
  static cancelAcpSession(
    conversationId: string,
    sessionId: string,
    conversationUrl?: string | null,
    sessionApiKey?: string | null,
  ): Promise<CancelAcpSessionResponse>;
}
```

```typescript
// src/hooks/mutation/use-cancel-acp-session.ts
import type { UseMutationResult } from "@tanstack/react-query";
import type { CancelAcpSessionResponse } from "@openhands/typescript-client";

export interface CancelAcpSessionVariables {
  conversationId: string;
  conversationUrl: string | null;
  sessionApiKey: string | null;
  sessionId: string;
}

/**
 * Cancel one ACP sub-agent session. Success means only that the request was
 * sent: the row shows "Stopping…" until the child's own idle/cancelled
 * snapshot arrives. A refusal shows the server's `detail` in an error toast.
 */
export declare function useCancelAcpSession(): UseMutationResult<
  CancelAcpSessionResponse,
  Error,
  CancelAcpSessionVariables
>;
```

### A.8 `src/stores/use-event-store.ts` (excerpt)

```typescript
import type { OpenHandsEvent } from "#/types/agent-server/core";
import type { SubagentIndex } from "#/utils/subagents/subagent-index";

type OHEvent = OpenHandsEvent;

// Excerpt: EventState with C1's field; every other member is unchanged.
export interface EventState {
  events: OHEvent[];
  eventIds: Set<string | number>;
  uiEvents: OHEvent[];
  loadedConversationId: string | null;
  /**
   * ACP sub-agent sessions folded from `events`, by `foldSubagentEvents`, in
   * the same `set` as `events` and `uiEvents`. Reset with them.
   */
  subagents: SubagentIndex;
  addEvent: (event: OHEvent) => void;
  addEvents: (events: OHEvent[]) => void;
  clearEvents: () => void;
  clearEventsForConversation: (conversationId: string | null) => void;
}
```

The typecheck also verified that the live store satisfies `SubagentSource` as it is (a bound zustand store's
`getState` and `subscribe` are assignable to the interface), so the context's default needs no adapter.

### A.9 `tests/e2e/mock-llm/utils/acp-subagents.ts` (shared with C2 and D5)

```typescript
import type { APIRequestContext, Page } from "@playwright/test";

/**
 * Absolute path of the SDK's scripted ACP agent
 * (`tests/fixtures/acp/scripted_agent.py` in a checkout of the pinned SDK),
 * from `SCRIPTED_ACP_AGENT`; null when unset.
 */
export declare const SCRIPTED_ACP_AGENT: string | null;

export interface ScriptedAcpAgentOptions {
  /** Flags after the script, e.g. `["--subagents", "--cancel-wait", "30"]`. */
  flags: readonly string[];
  /** Write `acp_subagents: true` on the profile (S1's opt-in). */
  subagents: boolean;
}

/**
 * Save and activate an ACP agent profile that runs the scripted agent.
 * Shared with C2's end-to-end tests; whichever lands first creates it.
 */
export declare function configureScriptedAcpAgent(
  request: APIRequestContext,
  options: ScriptedAcpAgentOptions,
): Promise<void>;

/**
 * Transcripts the replay spec plays, from `OH_ACP_REPLAY_TRANSCRIPTS`: file
 * paths separated by the platform's path delimiter (`:` on Linux and macOS).
 * Empty when unset.
 */
export declare const REPLAY_TRANSCRIPTS: readonly string[];

/** One child as a tree shows it: its parent link and its own tool calls. */
export interface SubagentLink {
  sessionId: string;
  /** null for the root session. */
  parentSessionId: string | null;
  /** null when the child is not placed inside a tool call. */
  parentToolCallId: string | null;
  /** The child's own tool calls (not its children's), sorted by id. */
  toolCallIds: readonly string[];
}

/** Expand every collapsed sub-agent block and row, until none is left. */
export declare function expandAllSubagents(page: Page): Promise<void>;

/**
 * The tree as the DOM nests it: each row's parent is its nearest enclosing
 * row (or the root), its tool call the nearest enclosing ACP cell inside that
 * parent, and its own calls the ACP cells whose nearest enclosing row is it.
 * Reads nesting only, never a row's own claims.
 */
export declare function readRenderedSubagentTree(
  page: Page,
): Promise<readonly SubagentLink[]>;

/**
 * The tree as stored: the newest ACPSubagentEvent per child and the
 * ACPToolCallEvents per session, from the events search route; a
 * `parentToolCallId` that names no stored call becomes null.
 */
export declare function readStoredSubagentTree(
  request: APIRequestContext,
  conversationId: string,
): Promise<readonly SubagentLink[]>;

export interface FanoutTranscriptOptions {
  children: number;
  cellsPerChild: number;
}

/**
 * Write an agent-outgoing JSONL transcript (S1 §4.10's format) of one root
 * cell fanning out to `children` sub-agents with `cellsPerChild` cells each,
 * interleaved as concurrent children are; returns the file's path.
 */
export declare function writeFanoutTranscript(
  directory: string,
  options: FanoutTranscriptOptions,
): Promise<string>;

export interface ScrollProbeResult {
  /** Worst delay between a scheduled scroll and the next painted frame. */
  maxScrollLatencyMs: number;
  /** Long tasks observed while the probe ran, in milliseconds. */
  longTasks: readonly number[];
}

/** Scroll the chat every 250 ms until `stop` resolves; report the worst. */
export declare function probeScrollResponsiveness(
  page: Page,
  stop: Promise<void>,
): Promise<ScrollProbeResult>;
```
