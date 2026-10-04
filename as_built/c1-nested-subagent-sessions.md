# C1 · Sub-agent sessions nested in the chat, as built

**TASK-4** · Cartographer · the code at `9d75806`, head of `feat/acp-subagent-sessions` in the Canvas fork
[michaeltheologitis/OpenHands](https://github.com/michaeltheologitis/OpenHands) (draft PR #4 into `wiring/dr-1` at
`9881d24`; C1 is `git diff 9881d24 9d75806`: sixteen commits of its own and no merges) · checked against the design at
`88f5c43` (`docs/design/c1-nested-subagent-sessions.md` v2, the head of `design/c1` when this branch was cut; a v3 is
being written elsewhere and I did not read it) · agent-server and TypeScript client from the SDK fork's tag `dr-1`
(`cef3b24`) · Node 22.22 and npm 10.9 in this sandbox, Node 24.15 and npm 11.12 in CI · 2026-10-04.

**Where this file lives.** On deep-reasoning's branch `as-built/c1`, cut from `design/c1` at `88f5c43`. C1's code is
in the Canvas fork, whose branches carry only upstream-shaped code, so no document of ours goes there. This branch
holds `AGENTS.md`, `CLAUDE.md` and `docs/` only: no `pyproject.toml`, no docs site, no test runner, so nothing builds
or collects `as_built/` and there is nothing to wire. [run: `git ls-tree -r HEAD`]

**Evidence marks.** Every claim carries one.
- **[run]**: executed in this sandbox, never in the shared checkout: a detached worktree of `9d75806` (and one of
  `9881d24`, C1's base, for comparison) using the C1 checkout's installed `node_modules`. C1's 12 Vitest files at head
  and the 8 of them that exist at base; `npm run typecheck`; ESLint and Prettier on C1's files; the translation check;
  one behavioural probe test and 23 hand mutation probes, each one temporary edit, reverted (§6.4); an in-memory
  `git merge-tree` against C2's branch.
- **[CI]**: read from GitHub's records through the GitHub MCP tools, with full job logs downloaded: CI run
  [37171885463](https://github.com/michaeltheologitis/OpenHands/actions/runs/37171885463) and live run
  [37171891707](https://github.com/michaeltheologitis/OpenHands/actions/runs/37171891707) at `9d75806`, the live runs
  37164950255, 37166999500 and 37171444972, and the tail of 37162417280.
- **[read]**: read in the code, **not executed**. Weaker than [run]; §7 lists the read claims that matter.

Nothing here ran a paid model, the `claude` CLI or a live test. The live tier is reported from CI.

**Reading order.** §2 first (the divergences), then §1 and §3–§4 as the map, §4.6–§4.7 for what C1 relies on and who
relies on C1, §6 for the runs and the mutation probes, §7 for what I could not verify.

---

## 1 · What exists

An ACP agent that runs sub-agent sessions (S1's events, stored by the dr-1 agent-server) now shows each child inside
the tool call that spawned it, recursively, instead of one flat list. Each spawning call's card gets a collapsed
summary line ("3 sub-agents · 2 done · 1 running") that expands to one row per child: status, title, the first line
of its answer, its own tool-call count, its latest cost, and Stop when the agent granted `cancel`. An expanded row
shows the child's task, its thoughts, text, messages and calls, and its own children the same way. Calls made inside
a child leave the root's flow. On reopening, the chat loads older pages until every visible child can be placed.
Agents without sub-agent sessions render as before. No production line names deep_reasoner or dr-acp or reads `meta`;
`_meta` appears only in type comments and, as the wire's `_meta.openhands.parentToolCallId`, in the transcripts; two
test comments name dr-acp ("A finished dr-acp child keeps its grant"). [run: grep of the added lines; read; each
path run by the tests of §6.5, and the whole in the live tier, §6.3]

```text
agent-server (dr-1) ── REST page / WebSocket frame, the same events
   ▼
useEventStore.addEvent(s)            one set per event or page; dedupe by id first
   ├─ events, eventIds, uiEvents     uiEvents' ACP merge key is now (session, tool_call_id)
   └─ subagents = foldSubagentEvents(subagents, newEvents)        utils/subagents/subagent-index.ts
        records by key: children · toolCalls · messages · firstMessageTo · transcripts · stats
        placement (only when dirty) = placeSubagents(records, previous)   utils/subagents/subagent-placement.ts
          byCell · byAnchor · pending · cellSummaries · needsOlderHistory
   ▼
ChatInterface ── needsOlderHistory → forced older-page loads until it clears or a page fails
   └─ <SubagentHistoryContext value={!hasMoreOlderEvents}> Messages(uiEvents ∩ shouldRenderEvent)
        ├─ root ACP call → AcpToolCallCell = today's card + SubagentBlock(cellKey)
        │     SubagentBlock → SubagentRow(child) → SubagentTranscript → AcpToolCallCell(child call) …  recursion
        ├─ children placed without a spawning call → SubagentRow, interleaved by time
        └─ UnplacedSubagents (history complete, parent session missing)
   Stop → useCancelAcpSession → EventService.cancelAcpSession → ConversationClient.cancelAcpSession
        → POST /api/conversations/{id}/acp/sessions/{session}/cancel; success shown only by the child's next snapshot
shared-conversation route: the same components over useStaticSubagentSource(its events), read-only (no Stop)
```

[read; the store, fold, placement, render and Stop paths run by the tests of §6.5]

| Part | Commits | Lines |
|---|---|---|
| events, guards, call keys; `handleEventForUI`, typing indicator, transcript export | `3f0fea8` | in the totals below |
| the index, placement and status in the event store | `b76b7ad` | |
| nesting: cell, block, row, transcript, unplaced, root anchors, render keys, shared view, strings, `specs/` | `08fb2cc` | |
| Stop: service method, mutation, button | `67e3cdb` | |
| history backfill and scroll-follow in `ChatInterface` | `81d810e` | |
| end-to-end specs, helpers, transcripts, workflow step | `85e9899` | |
| after the six | `e49d19a` tooltip placement · `9c23e8d` memoized transcript entries · `15f66c5` probe and pointer · `1135e87` replay's LLM profile · `dee08db` status icons · `ed8a7fc` aborted-turn test · `98a43ab` SUB-011 tag · `5b89471` E6 load · `09da5a1` mutation-found tests · `9d75806` a test's typing | |

In all, **+5,647 −44 in 51 files** [run: `git diff --numstat 9881d24 9d75806`]:

| Kind | Lines | Files |
|---|---|---|
| production TypeScript (`src/`, no tests, no translations) | +2,069 −28 | 28 |
| unit tests (`__tests__/`, `src/**/*.test.ts`, two helpers) | +1,953 −16 | 14 |
| end-to-end: specs +453, helpers +511, transcripts +48 | +1,012 | 5 |
| translations (`src/i18n/translation.json`, 32 keys × 15 languages) | +544 | 1 |
| upstream product spec (`specs/acp-subagent-sessions.md`) | +47 | 1 |
| workflow step +21, e2e skill guide +1 | +22 | 2 |

Production by part: the three pure modules 881 (`subagent-index.ts` 502, `subagent-placement.ts` 241,
`subagent-status.ts` 138); the nine component files 780 (`subagent-transcript.tsx` 202, `subagent-row.tsx` 130,
`stop-subagent-button.tsx` 103, `subagent-block.tsx` 85, `subagent-labels.ts` 80, `subagent-source.ts` 56,
`main-flow-anchors.ts` 55, `unplaced-subagents.tsx` 40, `acp-tool-call-cell.tsx` 29); types and guards 142; changed
consumers, the service method and the mutation 266. [run: `git diff --numstat`]

---

## 2 · Divergences from the design (`88f5c43`)

The changelog holds no entry for TASK-4, so no `drift:` line; every item below was found from the code. All sixteen of
C1's commits were made after the design (`88f5c43`, 2026-10-02 19:12; C1's commits 2026-10-03 21:45 to 2026-10-04
02:42). "Design §x" cites `88f5c43`. The brief named nine known divergences; the last paragraph of §2.3 says where each
landed. [run: Notion query of the Changelog; `git log`]

### 2.1 Behaviour a user or a consumer sees

**D-1 · A refused Stop shows a 5xx's reason from `exception`, without its status prefix.** Design §4.7 and A.7: the
toast shows `getApiErrorMessage(error, fallback)`, "which is S1's `detail`", for the 409, 504 and 404 alike. The
agent-server answers every 5xx `HTTPException` with `{"detail": "Internal Server Error", "exception": "<status>:
<reason>"}` (`_http_exception_handler`, `api.py:671–714` at `cef3b24`) [read], so `getApiErrorMessage`
(`src/utils/api-error-message.ts:24–38`) would show "Internal Server Error" for S1's 504. Built, `refusalReason`
(`src/hooks/mutation/use-cancel-acp-session.ts:16–34`) reads `detail` for a 4xx and `exception` for a 5xx, strips a
leading `NNN: `, and shows "Could not stop the sub-agent." (§4.10's key for a refusal without `detail`) for an error
with neither, a network failure included. The toast for S1's 504 therefore reads "ACP server
did not accept the cancel for n2 within 2s." Reason: commit `67e3cdb`. C2's branch reads the same field through its
own helper, `getSdkHttpServerErrorReason` (`src/api/agent-server-compatibility.ts:235` on `feat/agent-surfaces`, C2's
as-built D-2); the two branches carry separate implementations of the rule. [run: `shows the server's reason when a
cancel is refused` ×3, including the 504 case, and probe C3, which the 504 case catches; read: the handler]

**D-2 · A child whose parent is placed apart is itself placed apart, under a block that says its loaded parent is
missing.** Design §4.4 rule 1: a child is pending on `parent-session` when its parent `P` "is neither the root nor a
known child", or its ancestry loops. Built, `hasPlaceableAncestry` (`src/utils/subagents/subagent-placement.ts:40–54,
147–156`) walks the whole chain to the root and fails if any ancestor is unknown, recording the child's own parent as
`missingId`. So with `child-o` announced on a session `ghost` that is not in the conversation and `child-p` spawned in
`child-o`'s loaded call `co1`: the design places `child-p` in `byCell[(child-o, co1)]`, inside `child-o`'s row; the
build makes it pending, and once history is complete `UnplacedSubagents` shows two blocks, `ghost: [child-o]` and
`child-o: [child-p]`, the second reading "1 sub-agent could not be placed: its parent session child-o is not in this
conversation." while `child-o` is shown in the block above. Like any pending child, this keeps `needsOlderHistory`
true, so the chat loads older pages until none remain. No test covers a subtree under an unplaced child; the only
ancestry test is the loop. No reason recorded. [run: an uncommitted probe test printing the index and the rendered
blocks; read: the walk]

**D-3 · The smoke replay plays one transcript.** Design §6.3: in the fork's CI the replay spec "plays C1's three
transcripts and the generated fan-out's file as a smoke check". Built, the workflow sets `OH_ACP_REPLAY_TRANSCRIPTS`
to `fallback-placement.jsonl` alone (`.github/workflows/mock-llm-e2e.yml:104`), so the replay spec runs one test.
`nested-stop.jsonl` is played only by the main spec, which presses Stop; the fan-out is written to a temporary
directory inside its test. Reason: none recorded beyond commit `85e9899` ("replays the fallback-placement transcript as
a smoke check"). My reading, not run: `nested-stop.jsonl` holds a wait point for `session/cancel` that the replay spec
never sends, and S1's player exits non-zero on a wait point never reached (S1's as-built §7.2). [CI: the live log's
environment and its test list; read: the transcripts]

**D-4 · Status icons, with test ids outside the contract.** Design §2 and §4.7 draw ✓ for done and ■ for stopped. The
build had a spinner and words only until `dee08db`, which adds lucide's `Check` and `Square` beside the label
(`src/components/conversation-events/chat/subagents/subagent-row.tsx:77–96`) with `data-testid` `subagent-done-icon`
and `subagent-stopped-icon`; the running spinner reuses upstream's `spinner-icon`. Waiting, limited, refused,
unconfirmed and other show the label alone. The icons are the design's; the three test ids are in neither §4.12 nor
`SUB-011` (`specs/acp-subagent-sessions.md:39–47`), so the stable-id contract does not cover them. The call cards,
root and child, keep upstream's own result mark (`getACPToolCallResult` in `generic-event-message-wrapper.tsx:82–90`,
unchanged); the row's mark is the child's state, not a call's. [run: `marks a %s / %s child with %s beside its status`
×5]

**D-5 · Both end-to-end specs always skip under the Docker config.** Design §6.3 and §10 item 5: the spec skips there
"unless `SCRIPTED_ACP_AGENT_CONTAINER` names a mounted copy". Built, both skip whenever `MOCK_LLM_DOCKER_MODE` is
`"true"` (`tests/e2e/mock-llm/conversations/mock-llm-acp-subagents.spec.ts:87–90`, `mock-llm-acp-replay.spec.ts:43–46`);
no variable names a mounted copy. The e2e skill guide says so (`.agents/skills/e2e-testing/references/guide.md:52`).
No reason recorded. [read]

**D-6 · In the root's flow, a call's place is its first event's time, which the design's rule does not give.** Design
§4.6 and A.6: an anchor goes before the first rendered item "that starts after it (an item's start is its first
event's timestamp)", `interleaveSubagentAnchors(items, anchors)`. A completed call's item holds only its terminal event
(the started one is replaced in `uiEvents`), so by that rule the call would start at its completion. Built, the
function takes a third parameter, `startOf` (`main-flow-anchors.ts:21–35`), and `Messages` passes the call's `firstAt`
from the index (`messages.tsx:105–134`, comment: "A call's item starts when the call did, not when its terminal event
replaced it"). The two rules order a row differently only when its anchor falls between a root call's start and its
completion: the design's puts the row before that call, the build's after it. No test pins it: probe C7, which restores
the design's rule, survives the messages tests (§6.4), and the live tier's fallback order (`cell-1, child-m, …`, with
`child-m`'s task sent after `cell-1` completes) is the same under both rules. No reason recorded beyond the comment.
[read; run: probe C7]

### 2.2 Signatures and small behaviours

None of these changes what §2.1 describes. [read unless marked]

| Design | Built |
|---|---|
| A.5 `SubagentStatus {category, reported, stale}` | adds `lastKnown: SubagentStatusCategory \| null`, the last confirmed active category of an unconfirmed child (`subagent-status.ts:23–27, 87–94`); "running · last known" is built from it (`subagent-labels.ts:51–63`). Behaviour as §4.7's table [run: status and block tests] |
| §4.1's file list | adds `subagent-labels.ts` (80: `statusLabel`, `summaryLabel`, `MAX_INDENTED_DEPTH = 6`, the plural key names) and the test helper `__tests__/helpers/english-translations.ts` (21: a `t` that renders the real English strings, plural by `count`) |
| A.3, A.4, A.5 exports | also `compareTimestamps` (string comparison of ISO timestamps, `subagent-index.ts:27–30`), `NO_SUBAGENT_ANCHORS`, `EMPTY_SUBAGENT_SUMMARY`; `nestedIndentClass` from `subagent-block.tsx:20` |
| A.6 `renderKeyOf(event): string` | `string \| undefined` (an event without an id), `messages.tsx:41–45` |
| §4.10: 31 keys | 32: adds `SUBAGENTS$STATUS_OTHER` ("other"), so the summary counts unknown states as "N other"; one block after `EVENT_GROUP$COLLAPSE` as designed; no `eslint-disable` needed for the separator, which is a module constant [run: key count; translation check] |
| §4.7 cost: `USD` → `$0.0004`, else `0.0004 EUR` | and no currency → `0.0004` (`subagent-status.ts:115`) [run: status test] |
| §4.8 item 1: the scroll container is wrapped in `SubagentHistoryContext` | only `<Messages>` is wrapped (`chat-interface.tsx:613–618`), which is the only reader |
| §4.6 transcript: "To/From {name}", the name the child's title or "the main agent" | a known child without a title is named by its session id (`subagent-transcript.tsx:118–120`) |
| §4.3: a text item marks placement dirty when it opens the transcript of an unannounced session | any item that opens a transcript marks it dirty (`subagent-index.ts:263–271, 348–353, 384–391`); placement then recomputes and finds nothing new |
| §4.6 `SubagentBlock`: a toggle with `aria-expanded`, `aria-controls` | also `title` "Show sub-agents" / "Hide sub-agents" |
| §4.7 withheld Stop: tooltip "on hover where Stop would be" | `StyledTooltip placement="left"` (`stop-subagent-button.tsx:72–75`, `e49d19a`: the default placement covered the Stop of the row above in the live run) |
| §5: rows memoized on their own record | also each transcript entry (task, call, message, text) memoized on its own record (`9c23e8d`, `subagent-transcript.tsx:54–145`) |
| A.9 helpers | adds `SCRIPTED_ACP_PROFILE` (`scripted-acp-subagents`), `deleteScriptedAcpAgent`, `startConversation`, `readStoredEvents`, `waitForTurnsToEnd`; `ScrollProbeResult.scrolls`; a scroll still unpainted when the run ends counts as its latency (`15f66c5`). `readRenderedSubagentTree` gives a row in an unplaced block the block's missing parent id as its parent (`acp-subagents.ts:218–246`), which is what `readStoredSubagentTree` reads for it |
| §6.2: the service test with MSW on the route; the backfill test with MSW answering the events search | the service test mocks the client class (`vi.mock("@openhands/typescript-client/clients")`, the file's existing pattern); the backfill test spies `EventService.searchEvents` and asserts its `timestampLt` arguments (`chat-interface.test.tsx`) [run] |
| §4.1: "Three hand-written transcripts" (§6.3 lists two and the generated one) | two: `nested-stop.jsonl` (31 lines, with client lines as wait points) and `fallback-placement.jsonl` (17, outgoing only) |

### 2.3 The pull request, the proof and size

**D-7 · Sixteen commits in one PR into the wiring branch, not six cherry-pickable commits with a draft on `main`.**
Design §7: six commits, "each green on its own and cherry-pickable onto `main`", and a never-merged draft PR on the
fork's `main` to run upstream's guards. Built: PR #4 (`feat/acp-subagent-sessions` → `wiring/dr-1`). Its first six
commits carry the design's six titles word for word, in order; ten follow. I did not check any commit alone or
cherry-pick onto `main` (§7). The upstream checks that ran are CI's lint, test, build, build:lib and package check;
no PR-description check appears among PR #4's nine check runs, and its `HUMAN:` section is empty. [CI; run: `git
log`]

**D-8 · The full mock-LLM suite never ran on the branch.** Design §7: upstream's guards include "by dispatch, the
mock-LLM end-to-end workflow". All five `mock-llm-e2e.yml` runs on `feat/acp-subagent-sessions` were dispatches with
the fork-only `specs` input set to C1's two spec files, each running the same six tests. The design's live tier (§6.6 row 5)
is exactly that run, and it is green at the head (§6.3). [CI: the five runs]

**D-9 · Mutation testing covered the three pure modules, by Stryker's command runner; components were not mutated.**
Design §6.5: `npm run test:mutation:diff` on the branch; a survivor in the three modules "gets a test", and survivors
in components "are reviewed and either killed or named in the as-built document". The Implementer reports Stryker on
`subagent-index`, `subagent-placement` and `subagent-status` only, with the command runner because Stryker's Vitest
runner stopped applying mutants after a worker restart: 134 of 599 alive (77.6%) before `09da5a1`, 89.3% after, 64
survivors. The arithmetic holds (465/599, 535/599); I did not rerun it, and no committed file lists the 64. No run
mutated a component. My 23 hand probes (§6.4) cover the three modules and seven component and consumer files: 18
caught, 5 survived. [read: commit `09da5a1`, the brief; run: the probes]

**D-10 · `@spec` tags sit in implementation code for SUB-004 and SUB-008 only.** Design §4.11 ("code and tests carry
`// @spec SUB-00N` above the block that implements or pins each") and upstream's `AGENTS.md` ("Tag implementation code
and tests"). Built: implementation tags at `should-render-event.ts:142` (SUB-004) and `chat-interface.tsx:487`
(SUB-008); every ID from SUB-001 to SUB-011 is tagged in at least one test, SUB-010 and SUB-011 once each (the E6 test,
the e2e helpers). [run: grep]

**D-11 · E6's load was lighter than the design's until `5b89471`.** Design §5: about 1,100 events, per child "an
announcement, a task, ~5 text runs, 10 call events, an answer, an idle snapshot and cost snapshots". The generated
fan-out first sent no child text and one cost report per child (753 ACP events in the live run at `ed8a7fc`); since
`5b89471` each cell starts with a thought and ends with a cumulative cost report, 24 stored events per child and 1,203
in all (`acp-subagents.ts:320–428`). That is the design's load case, slightly above its estimate, not a heavier one.
Both loads are measured in §6.2. [CI; read]

**D-12 · Size: 1.6 times the estimate.** Design §3 item 6: ≈1.4k production, ≈1.0k Vitest, ≈0.6k Playwright with
helpers and transcripts, ≈0.5k translations (≈3.5k). Built (§1): 2.07k, 1.95k (14 files, 106 new cases), 1.01k, 0.54k
(5.65k with the spec file and workflow). Production is 1.5 times, unit tests 2.0, end-to-end 1.7, translations 1.0.
The largest overruns against §4.1's per-file figures: `subagent-index.ts` 502 against 230, `subagent-placement.ts`
241 against 150, `subagent-transcript.tsx` 202 against 110, `subagent-status.ts` 138 against 70, `messages.tsx` +75
against +35, the mutation hook 67 against 35, and `subagent-labels.ts` 80 unplanned; `subagent-index.test.ts` alone is
666. [run]

**D-13 · Every test the design names exists; some are renamed or merged, and more were added.** Renamed:
`places a child in the tool call that spawned it, in announcement order`; `builds the same index from a page in any
order, each event once`; `shows the last known state without a spinner after a reconnect` (it still asserts no Stop);
`rejects with the server's refusal as the client raised it` (the 409 case); `nests sub-agents in a shared
conversation, read-only`. `renders root ACP tool calls as before` is an assertion inside `hides tool calls made inside
a sub-agent session`. `shows the server's reason when a cancel is refused` is three cases (409, 504, no body). Added
beyond the design: the five icon cases, `leaves sub-agent snapshots, messages and text to the sub-agent tree`, the
aborted-turn case (`ed8a7fc`), and `09da5a1`'s +250 lines of index and status tests on keys, order across folds,
identity and unconfirmed snapshots. The shared-view test's file-wide `Messages` mock was rewritten to expose the
context values (`data-read-only`, `data-history-complete`, `data-subagents-in-cells`), so that view's nesting is
tested through the context, not rendered rows. [run: test names diffed between head and base]

**Where the nine known items landed.** The Stop refusal text: D-1. No Stop for an idle child still marked
`cancellable: true`: **not a divergence**; design §4.7's table gives idle children no control and decision I says
Stop is enabled only for a running or waiting child (`subagent-status.ts:63–67, 97–105`;
`stop-subagent-button.tsx:98–102`) [run: `offers Stop only for a running child that granted cancel`, its `n4`];
it matters because S1's reconnect leaves idle dr-acp children `cancellable: true` (S1's as-built D-1).
`SubagentStatus.lastKnown`: §2.2. `subagent-labels.ts` and `english-translations.ts`: §2.2. The ✓/■ icons and their
test ids: D-4. The smoke replay: D-3. E6's load: D-11. Sixteen commits: D-7. PR #4's base: D-7.

**Not divergences.** Decisions A–M as written (the index as derived state in the store, folded in the same `set` and
reset with it; records by key and transcripts by reference; timestamp order with arrival ties, never `seq`; placement
that waits for history; anchors interleaved in `Messages`; child calls kept in `uiEvents` and hidden by
`shouldRenderEvent`; call keys in `handleEventForUI`, the typing indicator, the index and render keys; render keys by
call; Stop never optimistic; costs never added; a context defaulting to the store with a read-only source for the
shared view; no capability flag and no `minimumAgentServer` change, still `1.47.0`; no virtualization and no
`content-visibility`). Design §3 items 1–5 and 7–10. §4.2's types and the four guards, field for field. §4.3's keys
(joined with `\u0000`), maps, "latest" rules, copy-on-write and identity. §4.5's consumers. §4.8's backfill with
`{ force }`, a failure flag reset per conversation, and scroll-follow on `subagents.version`. §4.9's shared view.
§4.11's eleven IDs in upstream's format. Every test id and data attribute of §4.12. §8's placement rules for the files
C2 shares (§4.7). [run for the behaviours the tests of §6.5 name; read for the rest]

---

## 3 · The public surface, from the code

**Event types and guards** (`src/types/agent-server/core/events/acp-subagent-event.ts`, joined to `OpenHandsEvent`
after `ACPToolCallEvent`): `ACPSubagentEvent`, `ACPSessionMessageEvent`, `ACPSessionTextEvent`; `ACPToolCallEvent`
gains optional `acp_session_id` and `meta`. Every field S1 may leave unset is optional. Guards
`isSubagentToolCallEvent` (an ACP call whose `acp_session_id` is a string), `isACPSubagentEvent`,
`isACPSessionMessageEvent`, `isACPSessionTextEvent`, directly after `isACPToolCallEvent`. `meta` is typed and never
read. [read; run: typecheck]

**The index** (`src/utils/subagents/subagent-index.ts`): `ROOT_SESSION = ""`, `toSessionRef`, `toolCallKey`,
`messageKey`, `routeKey`, `compareTimestamps`; the record, placement and index types of design A.3; `EMPTY_SUBAGENT_INDEX`,
`foldSubagentEvents(index, events)`, `buildSubagentIndex(events)`. **Placement** (`subagent-placement.ts`):
`placeSubagents(records, previous) → {placement, needsOlderHistory}`, `anchorsForParent`, `unplacedGroups`,
`NO_SUBAGENT_ANCHORS`. **Status** (`subagent-status.ts`): `getSubagentStatus → {category, reported, stale,
lastKnown}`, `canStopSubagent`, `isStopWithheld`, `formatSubagentCost`, `summarizeSubagents`. [read; run: their tests]

**Components and state** (`src/components/conversation-events/chat/subagents/`): `AcpToolCallCell {event, depth}`,
`SubagentBlock {cellKey, depth}`, `SubagentRow {sessionId, depth}` (memo), `SubagentTranscript`, `StopSubagentButton
{sessionId, title}`, `UnplacedSubagents`, `interleaveSubagentAnchors(items, anchors, startOf?)`; `SubagentSourceContext`
(default: the `useEventStore` hook itself, which satisfies `{getState, subscribe}`), `SubagentHistoryContext` (default
`true`), `useSubagents(selector)` over `useSyncExternalStore`, `useStaticSubagentSource(events)`. `renderKeyOf` in
`messages.tsx`. `EventState.subagents` in the event store. `EventService.cancelAcpSession(conversationId, sessionId,
conversationUrl?, sessionApiKey?)`; `useCancelAcpSession()` (toast disabled globally, its own error toast). [read;
run: the component tests]

**Requests Canvas makes for C1.** One new: `POST {runtime}/api/conversations/{id}/acp/sessions/{session}/cancel`
through the client, which URL-encodes the session id, on the conversation's runtime URL with its session key
[read: the dr-1 tarball's `conversation-client.js:221–225`; run: service test; CI: the live Stop test waits for this
request]. The backfill uses the existing older-page loader (`useLoadOlderEvents`, `timestamp__lt`) [run: backfill
test].

**What the user sees.** Under a spawning call's card, a summary toggle "N sub-agents · a done · b running · …" (the
parts in the order done, running, waiting, stopped, limited, refused, unconfirmed, other; zero parts omitted; a spinner
while any child runs), collapsed; while the call's start is not loaded and older history remains, "Loading earlier
sub-agent activity…". Expanded, one row per child in announcement order: chevron, ✓ / ■ / spinner, status ("running",
"waiting for action", "done", "stopped", "stopped at a limit", "refused", "not confirmed since reconnecting",
"running · last known", or the reported string), title (or "Sub-agent <id>"), "depth N" past depth 6, the answer's
first line in quotes, "N tool calls", then outside the toggle the cost and Stop. Stop reads "Stop", then "Stopping…"
(disabled) after a 200 until the child's own idle snapshot removes it; withheld, it is shown disabled with "This agent
cannot stop a single sub-agent. Stop ends the whole turn." on hover. An expanded row shows "Task" and the parent's first
message (else the child's description), then its calls, thoughts (collapsed, as the root's), text, "To/From <name>"
messages and anchored children, by time. Children whose parent session is missing sit in their own bordered block at
the end of the chat, one per missing parent. Every string is in all 15 languages. [run: component tests; CI: the live
tier]

**Stable test ids** (`SUB-011`, `specs/acp-subagent-sessions.md:39–47`): `acp-tool-call` (`data-acp-tool-call-id`,
`data-acp-session-id` absent for the root, `data-acp-tool-call-status`), `subagent-block` (`data-subagent-count`),
`subagent-block-toggle`, `subagent-row` (`data-acp-session-id`, `data-subagent-status`, `data-subagent-stale`),
`subagent-row-toggle`, `subagent-title`, `subagent-status`, `subagent-answer`, `subagent-tool-calls`, `subagent-cost`,
`subagent-stop` (`data-subagent-stop`: `ready`, `stopping`, `withheld`), `subagent-transcript`, `subagent-task`,
`subagent-unplaced` (`data-missing-parent-session-id`), `subagent-loading-earlier`. Outside the contract:
`subagent-done-icon`, `subagent-stopped-icon`, `spinner-icon` (D-4). [read; run: the tests that select them]

**End-to-end hooks** (`tests/e2e/mock-llm/utils/acp-subagents.ts`): `SCRIPTED_ACP_AGENT` (from the variable of that
name), `configureScriptedAcpAgent(request, {flags, subagents})` (saves profile `scripted-acp-subagents` with
`agent_kind: "acp"`, `acp_server: "custom"`, the shell-quoted command and `acp_subagents`, checks the opt-in survived,
activates it), `REPLAY_TRANSCRIPTS` (from `OH_ACP_REPLAY_TRANSCRIPTS`, split on `path.delimiter`),
`expandAllSubagents`, `readRenderedSubagentTree`, `readStoredSubagentTree`, `writeFanoutTranscript`,
`probeScrollResponsiveness`, and the five helpers of §2.2. The workflow step fetches
`tests/fixtures/acp` sparse and shallow from `config/defaults.json`'s `sources` (else the released SDK tag) into
`.tmp/sdk` and exports both variables. [read; CI: the step's environment]

---

## 4 · Structure and seams

### 4.1 The fold (`subagent-index.ts`; where most of the complexity sits)

`foldSubagentEvents` builds one draft per call: six copy-on-write maps (`writableMap` copies a map on its first write
in the fold), the transcripts already copied in this fold, and the sessions whose answer may have changed. Each event
not marked `isFromPlanningAgent` goes to one of four steps, each returning whether placement must be recomputed:

- **Snapshot.** `latest` is the event if its timestamp is at least the held one's (an equal timestamp arrived later and
  wins); `lastConfirmed` likewise but only for `source !== "environment"`; `firstAt` the earlier. An unchanged record
  returns early. Placement is dirty when any of nine fields differs: `firstAt`, the parent session and call, state,
  stop reason, grant, source, and the last confirmed state and stop reason; a cost-only snapshot changes one record
  and nothing else.
- **Tool call.** Upserted under `toolCallKey(acp_session_id, tool_call_id)`, root and child alike; `startLoaded` turns
  true on a `pending` or `in_progress` event and stays. A new key or a newly loaded start is dirty. A child's call also
  places a `tool_call` item in that child's transcript (moved earlier if an older page brings an earlier event) and,
  when new, adds one to its count.
- **Message.** Upserted under `messageKey(transcript, message_id)`; a new message, or one moved earlier, may become the
  first message of its route (the child's task) and is placed in its transcript's items; always dirty then.
- **Text.** Placed in its child's transcript; dirty only when it opens the transcript.

Items are inserted after every item at or before their `at` (binary search), so equal timestamps keep arrival order.
After the loop, each child's answer is recomputed for the sessions touched: the newest `message` item in its
transcript that it sent and whose recipient is not one of its own children. If no map was written, the same index is
returned; otherwise placement is recomputed only when dirty, and `version` increments. [read; run: 37 index cases,
probes I1–I6]

`ChatInterface` reads `version` for scroll-follow and `needsOlderHistory` for the backfill; every component reads its
own slice through `useSubagents`, so a cost snapshot re-renders one row and a child's new call re-renders that child's
transcript list and the one entry it adds. [read]

### 4.2 Placement and history (`subagent-placement.ts`, `chat-interface.tsx`)

`placeSubagents` walks the children in `firstAt` order: a child whose ancestry does not reach the root through known
children is pending `parent-session` (D-2); otherwise its fallback anchor is the parent's first message to it, else its
announcement; a named spawning call that is loaded puts it in `byCell`, an unloaded one makes it pending `parent-call`
with that fallback, and no named call puts the fallback in `byAnchor[parent]`. Lists, summaries and maps equal to the
previous placement keep their identity, and an unchanged placement is returned as the previous object.
`needsOlderHistory` is true while any child is pending, any `byCell` call's start is unloaded, or any transcript belongs
to a session with no snapshot. At render time, pending children render nothing until history is complete; then
`parent-call` children join their parent's flow at their fallback (`anchorsForParent`) and `parent-session` children
go to `UnplacedSubagents`, grouped by missing parent. [read; run: placement cases, probes P1–P4]

**The backfill.** An effect in `ChatInterface` calls the existing `maybeLoadOlder(target, {force: true})` while
`needsOlderHistory` holds and no backfill page has failed, re-run on `needsOlderHistory`, the failure flag,
`hasMoreOlderEvents` and `allConversationEvents.length`: each landed page chains the next; a failed page sets the flag
(reset when the conversation changes) and its message goes to the chat's existing `setErrorMessage`. `force` skips only the "near the top or
no overflow" check; one load at a time and scroll restoration are upstream's. The bottom-following effect also depends
on `subagents.version`. Bound: the chain stops when the cell's start and the pending parents are in, or when no older
page remains; an orphan (D-2, or any child of a session not in the conversation) keeps it going to the conversation's
start. [read; run: the two backfill tests; CI: the reload test of §6.3]

### 4.3 Rendering

`EventMessage`'s ACP branch renders `AcpToolCallCell` at depth 0: the unchanged `GenericEventMessageWrapper` (its
`isLastMessage` prop, now always `false`, is unused by the wrapper) inside a `div` carrying the cell's test id and data
attributes, then a `SubagentBlock` for the call's key. The block selects its `byCell` list, its summary and its call's
`startLoaded`; it renders nothing without children. A row selects its record, stats and answer; collapsed, it mounts
nothing below its header. The transcript merges items and anchored children by `at` (items first on a tie); each entry
selects its own record. Recursion is through `AcpToolCallCell` for a child's calls. Indentation (a left rule) stops at
depth 6. In the root's flow, `Messages` selects the root's anchors, the pending list and the `toolCalls` map,
interleaves rows into its rendered items (D-6), keys ACP singles by call key, and ends with `UnplacedSubagents`;
`Messages`' memo comparator is unchanged and already re-renders it on every appended event. [read; run: messages and
block tests, probes C4–C7]

### 4.4 Stop

`StopSubagentButton` renders nothing in a read-only source or for an unknown child; `StopControl` when
`canStopSubagent` (latest snapshot from the agent, state running or requires_action, `cancellable === true`);
`WithheldStop` when the same holds without the grant; nothing otherwise. A click calls the mutation with the active
conversation's id, runtime URL and session key; on success the control shows "Stopping…" and stays disabled while it is
mounted, which ends when the child's own snapshot makes `canStopSubagent` false. The mutation never touches the index.
A refusal toasts D-1's reason and the control returns to "Stop". [read; run: the five Stop tests; CI: the live Stop
test]

### 4.5 Where the complexity sits

In the fold and placement (881 lines with status, 37 + 33 test cases): the "latest" and `firstAt` rules under pages that
arrive out of order, the dirty rules that keep cost snapshots cheap, the answer rule, and identity reuse. The components
are thin readers of the index, except `SubagentTranscript` (the merge and the message naming) and the backfill's
interplay with upstream's scroll restoration (design §10 item 4's race, unchanged). [read]

### 4.6 What C1 relies on

- **S1, through `dr-1` (`cef3b24`).** The three event kinds and `ACPToolCallEvent.acp_session_id` as S1 stores them,
  with `exclude_none` storage, so unset fields arrive absent (`conversation/event_store.py:225` at `cef3b24`) [read]; `cancellable`
  is a `bool` defaulting to `False` (`event/acp_subagent.py:62–65`), so it is always present [read]. Placement relies on
  S1 §5 rules 1–2 and on its rule 10's ordering (per child, timestamps never decrease in log order and a reconnect
  snapshot is later than its child's earlier events; a spawning cell's started event is earlier than its subtree),
  which the backfill's stopping criterion and "latest" both assume; S1's as-built runs the three ordering tests [read:
  S1's as-built §4.4]. From the client tarball (version string 1.50.1): `ConversationClient.cancelAcpSession` and
  `CancelAcpSessionResponse` [run: typecheck; read: tarball]. The cancel route's statuses and the 409 `detail`
  shown verbatim; the 504's reason through upstream's 5xx `exception` format (D-1) [read]. `acp_subagents` on
  `ACPAgentProfile`, which `configureScriptedAcpAgent` writes and reads back [CI: the live tier]. The scripted agent
  by path with `--transcript`, `--transcript-interval-ms` (16 for E6) and `--wait-timeout` (120 for `nested-stop`)
  (`scripted_agent.py:704–708` at `cef3b24`) [read; CI]. S1's router registering a child announced on an unknown
  session under that session, which the orphan case needs: the live tier shows `child-o` under `ghost` [CI].
- **C3 and the wiring, through `wiring/dr-1`.** `config/defaults.json`'s `sources` naming the SDK fork at `cef3b24`,
  which C3's launcher installs as the mock stack's agent-server and which the workflow step reads for the scripted
  agent; the client tarball pin. C1 changes neither file. [read]
- **Upstream Canvas.** `useLoadOlderEvents` (`hasMore`, `loadOlder`, `timestamp__lt` pages), `maybeLoadOlder` and the
  scroll restoration, `GenericEventMessageWrapper`, `CollapsibleThinking`, `StyledTooltip`, `displayErrorToast`,
  `isSdkHttpError`, `getAgentServerClientOptions`, the mock-LLM harness (`playwright.mock-llm.config.ts`, its helpers)
  and the fork-only `specs` dispatch input (`9881d24`). [read]

### 4.7 Who relies on C1, and on what

- **D5, deep-reasoning's desktop app** (its design is not in my ground; what follows is what C1 offers it, from C1's
  design §6.4 and §9.4 and the code). The replay hook: `mock-llm-acp-replay.spec.ts`, one test per path in
  `OH_ACP_REPLAY_TRANSCRIPTS` (`path.delimiter`-separated; skipped when empty or under Docker), each configuring the
  scripted agent with `--transcript <path>` and `acp_subagents: true`, starting one conversation, waiting for one
  `FinishAction`, expanding everything and comparing the rendered tree with the stored one; it needs `SCRIPTED_ACP_AGENT`,
  `MOCK_LLM_PYTHON`, a built `build/` and Chromium, and sets the mock LLM profile once through the API (`1135e87`). The
  comparison covers parent session, spawning call and each child's own tool-call ids; not state, cost or text. Commit
  `1135e87` reports all ten of D1's dr-acp goldens rendering as stored against the dr-1 agent-server; that run is the
  Implementer's and is not in CI (§7). The stable test ids of `SUB-011` and the helpers `expandAllSubagents` and
  `readRenderedSubagentTree`, which take a Playwright `Page`; the icon test ids are not part of the contract (D-4).
  [read]
- **C2** shares nine files with C1 over `wiring/dr-1`: `events/index.ts`, `openhands-event.ts`, `type-guards.ts`,
  `translation.json`, `event-service.api.ts` and its test, `should-render-event.test.ts`, `transcript-export/index.test.ts`
  and the e2e guide. C1 follows design §8's rules where it lands (export, union members and guards directly after the
  ACP tool-call ones; its key block after `EVENT_GROUP$COLLAPSE`; `cancelAcpSession` after `respondToConfirmation`). An
  in-memory merge of `9d75806` with C2's head conflicts in one hunk, both branches' new export line at the top of
  `events/index.ts`, against both C2's Gate B commit `64b5a8b` and its current `61b9bdc`; the other eight files merge
  cleanly. C2 does not use C1's shared helper or workflow step (its live tier runs its own mock ACP agent). D-1's
  5xx rule exists on both branches separately. [run: `git merge-tree`; read]
- **S1's as-built §5** described C1 as designed, not built; its C1 paragraph checked stored shapes against C1's design.
  [read]

---

## 5 · Wiring

PR #4 is a draft, `feat/acp-subagent-sessions` → `wiring/dr-1`, 16 commits, +5,647 −44 in 51 files, labelled
`type: feat`, mergeable (`clean`). Its nine check runs at `9d75806`: CI's `test-and-build (ubuntu)` (lint, test, build,
build:lib, package contents), `test-and-build (windows)` (install and app build; lint, test, library and package
skipped), `prepare-test-matrix`, `live-e2e` skipped, two pairs of `pr-title` jobs, and the `mock-llm-e2e` dispatch, all
green. The PR body reports the runs at `9d75806`. [CI] `wiring/dr-1` is the fork's C3 plus the dr-1 wiring
(`69d2a6a` agent-server source and client pin, `32bc76e`, `9881d24` the `specs` input), all fork-only and not C1's.
Upstream's product spec gains `specs/acp-subagent-sessions.md` (SUB-001 to SUB-011, each checked); the e2e skill guide
gains one paragraph on the scripted agent; `test-mapping.json` is unchanged, since the specs sit under
`conversations/`. [read]

---

## 6 · Tests and runs, as measured

### 6.1 The runs

| Run | Commit | Conditions | Result |
|---|---|---|---|
| CI [37171885463](https://github.com/michaeltheologitis/OpenHands/actions/runs/37171885463) | `9d75806` | `pull_request`; ubuntu-24.04 full checks; windows app build only; Node 24.15.0, npm 11.12.1 | green. Lint 0 errors, 376 warnings, none in a file C1 touches; Prettier clean; test **769 files passed, 1 skipped; 8,222 passed, 1 skipped, 7 todo** in 413 s; build, build:lib and package contents green [CI] |
| live tier [37171891707](https://github.com/michaeltheologitis/OpenHands/actions/runs/37171891707) | `9d75806` | `workflow_dispatch` of `mock-llm-e2e.yml` with `specs` = C1's two spec files; ubuntu-24.04; Playwright 1.63.0 Chromium; uv 0.12.23; the mock LLM in a Python 3.12.3 venv with `openhands-sdk` 1.50.1; agent-server from `sources` (`cef3b24`) [read]; scripted agent fetched from the same source; no paid model | **6 passed** (1.7 min), 1 worker; E6 line in §6.2 [CI] |
| earlier live runs | `15f66c5`, `ed8a7fc`, `5b89471`, `09da5a1` | the same, runs 37162417280, 37164950255, 37166999500, 37171444972 | 6 passed each [CI] |
| here: C1's 12 Vitest files | `9d75806` | Node 22.22, 4 CPUs, load average 13–17, beside other agents | **231 passed, 1 todo** in 39 s; the 8 files that exist at the base: 125 passed, 1 todo; **C1 adds 106 cases, all passing, and removes none** [run] |
| here: typecheck, lint, format, translations | `9d75806` | `npm run typecheck`; `npx eslint` on C1's 30 `.ts`/`.tsx` files under `src/` (upstream lints `src` only); `npx prettier --check` on all 45 of C1's `.ts`/`.tsx` files; `check-translation-completeness.cjs` | `tsc` clean; ESLint 0 problems; Prettier clean; every key in every language [run] |

I did not run the full Vitest suite, the builds or any Playwright test here; CI's runs are the record. Reproduce the unit
part with `npm ci && npm run make-i18n && npx vitest run <the 12 files>`, and the live tier with
`gh workflow run mock-llm-e2e.yml --ref feat/acp-subagent-sessions -f specs="tests/e2e/mock-llm/conversations/mock-llm-acp-subagents.spec.ts tests/e2e/mock-llm/conversations/mock-llm-acp-replay.spec.ts"`.
[read]

### 6.2 E6 (spec §4, design §5): 50 children × 5 calls at 60 events/s

Conditions: the generated transcript (`writeFanoutTranscript`, 50 children, 5 cells each) played by the scripted agent
with `--transcript-interval-ms 16`; an in-page interval clicks every collapsed block and row toggle every 100 ms, so
every child is expanded as it appears; `probeScrollResponsiveness` scrolls the chat container every 250 ms and records,
per scroll, the time from when it was due to the next animation frame, plus long tasks; it stops when the turn's
`FinishAction` is stored. The rate is the count of stored events whose kind starts with `ACP` (C1's four kinds and S2's
`ACPSessionControlsEvent`) over their first-to-last timestamp span. The test asserts worst latency < 1,000 ms (E6's
null), more than 10 scrolls, the summary "50 sub-agents · 50 done", and the rendered tree equal to the stored one with
50 children. There is no stock-Canvas arm: the null is the baseline. [read: the spec and helper]

| Run | Commit | Load | ACP events, span, rate | Worst scroll latency | Long tasks | Scrolls |
|---|---|---|---|---|---|---|
| 37164950255 | `ed8a7fc` | before `5b89471`: no child text, one cost per child | 753 in 12.5 s, 60.5/s | **323.5 ms** | one, 72 ms | 47 |
| 37166999500 | `5b89471` | a thought and a cost per cell | 1,203 in 19.8 s, 60.7/s | **149.8 ms** | none | 75 |
| 37171444972 | `09da5a1` | the same | 1,203 in 19.8 s, 60.6/s | **101.3 ms** | none | 75 |
| 37171891707 | `9d75806` | the same | 1,203 in 19.7 s, 61.1/s | **138.6 ms** | none | 76 |

All four pass the null by a factor of 3 or more [CI: the E6 log lines]. The lighter load's run measured the highest
latency; the runs are single samples on shared GitHub runners, and `9c23e8d` (memoized transcript entries) precedes all
four. The tail of 37162417280 (`15f66c5`) does not include its E6 line. [CI]

### 6.3 The live tier, test by test (run 37171891707) [CI]

1. `mock-llm-acp-replay.spec.ts`: `nests fallback-placement.jsonl as the agent-server stored it`.
2. `nests each sub-agent under the call that spawned it`: `nested-stop.jsonl` with `--wait-timeout 120`; the summary
   reads "2 sub-agents · 2 running" while the transcript waits; the stored tree is `child-x`, `child-y`, `child-z`;
   after expanding, the rendered tree equals the stored one (three levels); the root's own cards are `cell-1` alone;
   `child-x` shows `$0.0004`.
3. `stops one sub-agent and its branch`: opened with the pointer; `child-y`'s Stop is `withheld`, `aria-disabled`, and
   its tooltip is the spec's sentence; `child-x`'s is `ready`; clicking sends `POST …/acp/sessions/child-x/cancel`;
   `child-x` and `child-z` turn `stopped`, `cell-x1` turns `failed`, `child-y` turns `done`, and no Stop remains.
4. `shows the same tree after reloading`: after the turn ends, a reload shows "2 sub-agents · 1 done · 1 stopped", the
   tree equals the stored one, no Stop, the root's `NESTED_STOP_DONE` is visible, and `child-y`'s answer appears only
   inside rows.
5. `places sub-agents without a spawning call and shows orphans apart`: the flow reads `cell-1, child-m, child-a,
   child-g, cell-2`, then the unplaced block for `ghost` with `child-o`.
6. `stays responsive while 50 sub-agents with 5 tool calls each stream in`: §6.2.

### 6.4 Mutation probes [run]

Each probe is one edit in my worktree of `9d75806`, the named test files run, then `git checkout` of the file; the copy
was clean after every probe. Stryker's 64 survivors (D-9) are not listed anywhere committed, so I cannot say which of
these overlap them.

| Probe | Edit | Result |
|---|---|---|
| I1 | equal timestamps: the held snapshot wins (`>= 0` → `> 0`) | caught: `takes the later arrival of two snapshots with one timestamp` |
| I2 | a started event no longer sets `startLoaded` | caught by 4, e.g. `needs older history until every spawning call's start is loaded` |
| I3 | `latest.state` dropped from the placement-dirty fields | **survived** (55 passed), and equivalent for what S1 writes: a confirmed snapshot's new state also changes `lastConfirmed.state`, which stays in the list, and an `environment` snapshot changes `source` or carries `state: null` (S1 writes reconnect snapshots with no state). It would differ only for two consecutive `environment` snapshots with different non-null states [read: the fold; S1's as-built D-1] |
| I4 | a child's answer may be its task to its own child | caught: `counts a child's own calls and takes its answer from its newest message outside its children` |
| I5 | transcript ties placed before equal timestamps | caught: `orders a child's transcript by first event, ties by arrival` |
| I6 | planning-agent events folded | caught: `ignores events from the planning agent` |
| P1 | anchors left in announcement order (no sort by `at`) | caught by 2 placement cases |
| P2 | an unannounced session's transcript no longer needs older history | caught: `needs older history for a transcript whose session was never announced in the loaded pages` |
| P3 | fallbacks shown while history is incomplete | caught: `anchorsForParent > adds the fallbacks …` |
| P4 | the announcement outranks the parent's message as fallback | caught by 4 placement cases |
| S1 | Stop offered when `cancellable` is absent (`=== true` → `!== false`) | **survived** (51 passed): the fixture helper `child()` always writes the field (default `false`), and S1 always stores it (§4.6), so no test and no dr-1 event reaches the difference |
| S2 | a stale active child shows its last state instead of unconfirmed | caught by 4 status and block cases |
| S3 | `max_turn_requests` no longer reads as limited | caught: `reads idle / max_turn_requests as limited` |
| S4 | a cost without a currency hidden | caught: `formats 0.0004 null as 0.0004` |
| C1 | Stop shown in a read-only view | caught: `never offers Stop in a read-only view` |
| C2 | no "Stopping…" after a 200 | caught: `asks to cancel and waits for the child's own cancelled state` |
| C3 | a 5xx reason keeps its `504: ` prefix | caught: the 504 refusal case |
| C4 | "Loading earlier…" shown once history is complete | caught: `says earlier activity is loading while the cell's start is missing` |
| C5 | a child's task to its own child also shown as a "To …" message in the parent's transcript | **survived** (23 passed in the block and messages tests): no test expands a child that has a child of its own and checks its messages; the live tier compares tree shape only |
| C6 | ACP render key back to the event id (decision H) | caught: `keeps sub-agents expanded when the spawning call completes` |
| C7 | a root call's item starts at its current (terminal) event, the design's rule (D-6) | **survived** (5 passed): the messages tests never anchor a child between a call's start and its completion |
| C8 | a failed backfill page no longer stops the chain | caught: `stops loading older pages after a failure` |
| C9 | scroll-follow no longer depends on `subagents.version` | **survived** (28 passed, 1 todo): no test checks that a chat pinned to the bottom follows sub-agent content that grows without new root items; jsdom has no layout |

In all, 18 caught and 5 survived. Of the survivors, I3 is equivalent for anything S1 writes and S1's mutant is
unreachable through dr-1; C5, C7 and C9 change what a user sees, in cases no test states.

### 6.5 The deterministic tests C1 adds (106 cases in 12 files, all passing) [run]

- **The three pure modules, 70.** `subagent-index.test.ts` 37: parent links from the latest snapshot; placement in the
  spawning call in announcement order (also when an older page brings an earlier child); keys per session for calls,
  messages and routes; fallbacks to the parent's message, else the announcement, moving when an earlier task arrives;
  latest and last-confirmed rules across pages and equal timestamps; a child known only from reconnects never
  confirmed; message upserts; transcript order with arrival ties and every entry kept across folds; the aborted-turn
  case; counts and the answer rule; pending on a missing parent session and on a missing named call, then placed when
  the call's page arrives; the three `needsOlderHistory` conditions, with `pending` and `in_progress` both counting as
  a start; identity of unchanged records, transcripts, stats, lists, summaries, placement and index; no placement for a
  cost-only snapshot, a recomputed summary on a state change; non-ACP events and planning-agent events; the parent
  loop; `buildSubagentIndex` over a shuffled, duplicated page; `anchorsForParent`; `unplacedGroups`.
  `subagent-status.test.ts` 33, table-driven: every row of §4.7's status table, `canStopSubagent` and
  `isStopWithheld` over state × grant × source, costs for null, USD, EUR and no currency, summaries.
- **Components, 23.** `subagent-block.test.tsx` 18 against the real event store: the collapsed summary; three levels
  of nesting; costs never summed; the last known state; the five icon cases; task first and answer last; the loading
  line; Stop offered, withheld with its tooltip, sent and "Stopping…" until the child's cancelled snapshot, three
  refusals, none read-only. `messages-subagents.test.tsx` 5: the root's flow only; a child anchored at the root's
  message; orphans apart once history is complete; no sub-agent markup for agents without sessions; a block staying
  expanded when its call completes.
- **Consumers, 13.** Event store 3 (fold per event and per page, an older page not overriding, the reset); backfill 2;
  `should-render-event` 2; service 2; `handleEventForUI`, typing indicator, transcript export and the shared view 1
  each.

Plus the six live-tier tests of §6.3.

---

## 7 · What I could not verify

1. **Each commit alone, and cherry-picks onto `main`** (D-7): not checked.
2. **Stryker's numbers** (D-9): the Implementer's; I did not rerun Stryker, and its 64 survivors are not listed in any
   committed file. My probes are 23 hand edits, not a mutation score.
3. **The ten-golden replay** (`1135e87`): the Implementer's local run of D1's recordings through the replay spec; no CI
   run plays them, and I ran no Playwright test. Whether D5's jobs have run against `9d75806` I did not check.
4. **Playwright, builds and the full Vitest suite here**: not run; CI's records only. The live log does not print which
   SDK ref the scripted agent was fetched from; `cef3b24` is read from `config/defaults.json`.
5. **D-3's reason** (why `nested-stop.jsonl` is not replayed) is my inference from the transcript and S1's as-built,
   not run.
6. **The Docker config, Cloud runtimes and Electron**: C1 skips the first (D-5); Stop on a Cloud runtime and the
   backfill against Cloud's event history are read only (design §10 item 6); nothing ran in the desktop app.
7. **Scroll behaviour**: the backfill's scroll restoration and design §10 item 4's race are read; jsdom has no layout,
   and E6 measures latency, not position. Nothing pins scroll-follow on sub-agent growth (probe C9 survived).
8. **The restart path** (`source: "environment"` snapshots from a real agent-server restart): unit-tested with fixture
   events; no live run restarts the agent-server.
9. **E6 off GitHub's runners**: four single samples on `ubuntu-24.04`; not measured on a desktop.

If this document resists shortening, the part that resists is §2: the build follows the design's architecture
closely, and what differs is spread thin across the refusal text, one placement rule, the proof's shape and the size,
each of which a Gate B reader may want to rule on.
