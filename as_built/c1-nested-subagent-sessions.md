# C1 · Sub-agent sessions nested in the chat, as built (r2)

**TASK-4** · Cartographer · r2, for Gate C · the code at `2c0e743`, head of `feat/acp-subagent-sessions` in the Canvas
fork [michaeltheologitis/OpenHands](https://github.com/michaeltheologitis/OpenHands) (draft PR #4 into `wiring/dr-1`
at `9881d24`; C1 is `9881d24..2c0e743`: 38 commits, no merges) · checked against design v3 (`8772b90`,
`docs/design/c1-nested-subagent-sessions.md` on `design/c1`), Michael's six Gate B rulings and his instruction "fold
the cost toggle into C1 now" · replaces r1 (`d16d3df`, the code at `9d75806` against design v2) · Node 22.22 and npm
10.9 here, Node 24.15 and npm 11.12 in CI · 2026-10-04.

**Where this file lives.** deep-reasoning's branch `as-built/c1-r2`, cut from `design/c1` at `9bb15be`. That branch
holds `AGENTS.md`, `CLAUDE.md`, `docs/` and `as_built/` only: nothing builds or collects `as_built/`, so there is
nothing to wire. [run: `git ls-tree -r HEAD`]

**Evidence marks.** Every claim carries one.
- **[run]**: executed here, in detached scratch worktrees of the Canvas fork at `2c0e743` and `4db661f` (and, for one
  check each, `9881d24`, `94b4bae`, `ba1c1d2`, a local merge of C1 with C2 and a local commit of C1's diff on
  deep-reasoning; none pushed): `npm ci` and `npm run make-i18n` first; C1's 13 Vitest files; typecheck, ESLint,
  Prettier and the translation check; the Refactorer's DOM probe and expect-counter at both commits; 27 mutation
  probes, one temporary edit each, reverted, the tree clean after each (§7); `git merge-tree` trial merges.
- **[CI]**: read from GitHub with `gh run view --log` (REST): CI
  [37184716626](https://github.com/michaeltheologitis/OpenHands/actions/runs/37184716626) and the live tier
  [37184736932](https://github.com/michaeltheologitis/OpenHands/actions/runs/37184736932) at `2c0e743`; for
  comparison CI 37177982694 and live 37177985083 at `4db661f`.
- **[read]**: read in the code, **not executed**. Weaker than [run]; §8 lists the read claims that matter.

No paid model, no `claude` CLI and no Playwright test ran here; nothing was dispatched. The live tier is CI's.

**Reading order.** §1 (what moved since Gate B), §2 (divergences), §3 (the design's stale lines), then §5 for D5 and
C2, §6–§7 for the measurements and probes, §8 for what is unverified. §4 is the route into the code.

---

## 1 · What moved since Gate B

Three steps follow r1's `9d75806`, all on the same branch, none a merge [run: `git log`]:

| Step | Commits | What |
|---|---|---|
| Rulings 5 and 6 | `94b4bae`, `ba1c1d2` (ruling 5); `b4f6354` (ruling 6) | D-2 fixed test-first; C5, C7, C9 pinned |
| The cost setting | `dfde47e`, `4db661f` | sub-agent costs hidden unless an App setting shows them (D-14) |
| The literate refactor | `6fafd62` … `2c0e743`, 17 commits | types from the client, a keys module, `replaceEqualDeep`, `upsert`, a scan, the anchor rule moved into the interleave, five exports made private, test helpers, reordering (D-15 to D-21) |

**The six rulings, as built.**

| Ruling | At `2c0e743` |
|---|---|
| 1 · size accepted | The refactor took C1's code and tests from 5,369 lines added to 5,147 (−222, −4.1%). Production is 2,034, below Gate B's 2,069; unit and end-to-end tests are 3,113, above Gate B's 2,965 (§6.3). [run] |
| 2 · keep ✓/■ | `Check` and `Square` with `subagent-done-icon` and `subagent-stopped-icon` (`subagent-row.tsx:87–100`), still outside SUB-011 (`specs/acp-subagent-sessions.md:39–48`). [run: `marks a %s / %s child …`] |
| 3 · E6 at 1,203 events, null 1 s | `SCROLL_LATENCY_LIMIT_MS = 1_000` (`mock-llm-acp-subagents.spec.ts:46`, asserted at `:348`); `writeFanoutTranscript` unchanged since `5b89471` but for its doc comment [run: `git diff 4db661f 2c0e743`]; the live run stored 1,203 ACP events, worst scroll 43 ms (§6.2) [CI] |
| 4 · one-transcript smoke replay | `.github/workflows/mock-llm-e2e.yml` unchanged since `9d75806`; `:104` still names `fallback-placement.jsonl` alone [run: `git diff`; CI: the job's environment] |
| 5 · fix D-2 test-first | `94b4bae` adds `sets apart only the child whose own parent is missing, not the children it spawns` (`subagent-index.test.ts:545`) and `nests a child spawned inside an unplaced child under it, in one block` (`messages-subagents.test.tsx:146`); both fail at `94b4bae` and pass at `ba1c1d2` [run]. The fix is one line: an unknown session fails the ancestry walk only when it is the child's own parent (`subagent-placement.ts:157`, `if (!record) return current !== parent;`), which is design §4.4 rule 1. Probe D2 restores the old walk; both tests fail [run] |
| 6 · pin C5, C7, C9 | `b4f6354`: `shows a child's task to its own child only as that child's task` (`subagent-block.test.tsx:251`), `keeps a root call where it started when a child's task lands before it ends` (`messages-subagents.test.tsx:108`), `follows sub-agent content into view as it grows without new root items` (`chat-interface.test.tsx:1077`). Each was written against code that already behaved so; probes C5, C7 and C9 each now fail exactly that test [run] |

**What the refactor did not change.** The Refactorer's DOM probe renders 16 states of the tree (every status, costs
hidden and shown, a three-level transcript, depth past 6, the root's flow with anchors, fallbacks and unplaced
blocks, Stop ready, stopping, withheld and confirmed, the read-only view, the switch off and on). Its normalized
markup is byte-identical at `4db661f` and `2c0e743`, and identical to the Refactorer's own baseline and final files.
No test name was lost except the three of D-21, and no surviving test makes fewer `expect()` calls. [run: §6.4]

---

## 2 · Divergences from design v3 and the rulings

r1's D-1 to D-13 were against v2; v3 absorbed them as its §3.2 B1–B17. At `2c0e743` B16 (r1's D-2) is fixed and
B17's three behaviours are pinned (§1); the others stand as v3 records them. Below are the divergences from v3 that
r1 could not see, numbered on from r1. The changelog holds no entry for TASK-4, so no `drift:` line to compare.
[read: Notion query of the Changelog]

### 2.1 Behaviour a user sees

**D-14 · Sub-agent costs are hidden unless an App setting shows them.** Design §1.2, §2 items 5 and 7, decision J,
§4.6 (`SubagentRow`), §4.7 ("Cost"), SUB-006 and §4.12: every row shows its child's latest cost. Built (`dfde47e`):
`useShowSubagentCosts()` (`subagent-cost-preference.ts:22–28`) is `useSyncExternalStore` over the localStorage key
`openhands-show-subagent-costs` read as `=== "true"`, subscribed to `storage` (other tabs) and to an event its one
writer, `writeShowSubagentCosts` (`:31–37`), dispatches in the same tab; `SubagentRow` formats a cost only when it is
on (`subagent-row.tsx:43, 53–55`). The switch, `SubagentCostsSwitch`
(`features/settings/app-settings/subagent-costs-switch.tsx`), is upstream's `SettingsSwitch` with test id
`show-subagent-costs-switch`, below the Getting Started switch on `/settings/app` (`routes/app-settings.tsx:230`).
Its label is a 33rd key, `SETTINGS$SHOW_SUBAGENT_COSTS`, placed after `SETTINGS$SHOW_GETTING_STARTED_CHECKLIST`
(`translation.json:42366`), not in the `SUBAGENTS$` block §4.10 and §8 row 5 describe. SUB-006 is reworded and
SUB-011 lists the switch (`specs/acp-subagent-sessions.md:24–25, 48`). Frontend only: no agent-server setting. The
shared-conversation view reads the viewer's own setting like the live chat; nothing in §4.9 or the code treats it
apart [read]. Live 2 now waits until the agent-server stored `child-x`'s cost, asserts the row shows none, turns the
switch on on the settings page, reloads and asserts `$0.0004` (`mock-llm-acp-subagents.spec.ts:137–161`) [read; CI:
passed]. *Reason:* Michael's instruction, folded from TASK-15; the commit's own: Canvas shows a conversation's cost
only on demand. *Pinned by:* `subagent-costs-switch.test.tsx` (`is off by default and shows sub-agent costs while
on`, `keeps sub-agent costs shown across a reload`) and `subagent-block.test.tsx › … › shows each child's latest
cost and never a sum when costs are shown`; probes K1, K2, K3, K5 are caught. Another tab's change (the `storage`
listener) is not pinned: probe K4 survives (§7). [run]

### 2.2 Structure and signatures (the refactor)

**D-15 · The three event types come from the TypeScript client.** Design §4.2: "Canvas keeps its own agent-server
event types … and does not import the client's; C1 follows that convention", and A.1 declares three interfaces.
Built (`1635097`): `acp-subagent-event.ts:16–22`, each `Client<Name> & BaseEvent`, 22 lines instead of 99. The fields
are the client's, with A.1's names and optionality (`dist/events/types.d.ts:142–172` of the `dr-1` tarball) [read];
`source` is Canvas's `SourceType` (`"agent" | "user" | "environment" | "hook"`) on all three, where A.1 has
`"agent" | "environment"` and `"agent"`; the per-field JSDoc is gone. Typecheck is clean [run]. *Reason (commit):* the
pinned client already exports all three, and Canvas already takes `AgentErrorEvent` and `ConversationErrorEvent` from
it. *Consequence:* C1 now needs five client exports, not A.7's two (§5.1); on the stock npm client C1 does not
typecheck (§5.3).

**D-16 · Keys and timestamp order have their own module.** A.3 and §4.3 put `ROOT_SESSION`, `SessionRef`,
`toSessionRef`, `compareTimestamps`, `toolCallKey`, `messageKey` and `routeKey` in `subagent-index.ts`. Built
(`4f5fb18`): `src/utils/subagents/subagent-keys.ts` (48 lines, no imports); the index imports `placeSubagents`, and
placement imports only types from the index. *Reason (commit):* placement imported the keys from the fold while the
fold imported placement. [read]

**D-17 · Structural sharing through react-query's `replaceEqualDeep`.** §4.4's rule holds (equal lists, summaries
and the pending list keep their identity); the mechanism is `replaceEqualDeep` from `@tanstack/react-query`
(`subagent-placement.ts:1, 78–81, 87, 215`) in place of the six `same*`/`reuseList` helpers; `reuseMap` stays for
Maps. The pure placement module now imports react-query, as `src/utils/cache-utils.ts` already does. *Reason
(commit):* the same sharing react-query applies to every query result, a public export. Probes R1–R3 are caught.
[run; read]

**D-18 · A transcript item's place is found by scanning back from the end.** §4.3's table: "insertion by binary
search (upper bound)". Built (`ea988b2`, `subagent-index.ts:375–377`): the same position in a sorted transcript, after
every item at or before `at`; one step for an item newer than the rest. Probes R7 and R8 are caught. [run]

**D-19 · `interleaveSubagentAnchors(items, anchors, toolCalls)`.** A.6 (v3): an optional `startOf?: ItemStart`
defaulting to the first event's timestamp, with `Messages` passing the call's `firstAt`. Built (`ed44161`):
`toolCalls` is a required third argument and the function dates an ACP call by its record's `firstAt` itself
(`main-flow-anchors.ts:30–38, 45–49`); `ItemStart` and the default are gone. The rule is v3's B5. Probe C7 is caught.
[run]

**D-20 · Smaller changes**, none changing what a user sees [read unless marked]:

| Design v3 | Built at `2c0e743` |
|---|---|
| A.3: `TranscriptItem` has three variants | two: `{kind: "tool_call" \| "message"; key; at}` and the text item (`subagent-index.ts:61–73`, `dfd5ab8`) |
| A.3: `SubagentSummary` interface in the index; A.5 exports `EMPTY_SUBAGENT_SUMMARY` | `Record<SubagentStatusCategory \| "total", number>` in `subagent-status.ts:15`; the empty constant is gone (`f507374`) |
| §4.3: three "latest" rules, one per record kind | one `upsert` (`subagent-index.ts:307–313`) for snapshots, calls and messages (`dfd5ab8`); probes R4–R6 caught [run] |
| B5: placement fields compared as one joined string (`subagent-index.ts:241` at `9d75806`) | `JSON.stringify` of the same nine fields (`:326–341`, `4f5fb18`); probe R14 (`String(...)`) survives: no test tells the two apart, and for the values S1 writes they agree [run] |
| §4.3: "A call that changed nothing returns `index` itself" | still so; the check compares each record map with the index's (`:179–182`) instead of asking each draft map whether it was written; a write always copies, so the two agree (`dfd5ab8`) |
| A.7: the refusal text reads the client error's body | through upstream's `getApiErrorBody` (`use-cancel-acp-session.ts:27`, `7df5ab0`); same toast; probe R15 caught [run] |
| A.6: `renderKeyOf`, `SUBAGENT_COUNT_I18N_KEY` exported; A.9: `SCRIPTED_ACP_PROFILE`, `deleteScriptedAcpAgent`, `startConversation` exported | all five private (`messages.tsx:42`, `subagent-labels.ts:10`, `acp-subagents.ts:43, 92, 112`; `77b602b`, `1b88117`) |
| A.9's helper list | adds `scriptedAcpRuns()` (`acp-subagents.ts:127–157`: `start` configures the scripted agent with `acp_subagents: true`, routes the session key, starts and records a conversation; `cleanUp` deletes them and restores the mock LLM's profile), `showSubagentCosts` (`:234`, D-14), `COLLAPSED_TOGGLES` (`:229`); `StoredEvent` gains `cost` |
| §4.11 (v3): `@spec` tags in implementation code for SUB-004 and SUB-008 only | also SUB-006 (`subagent-cost-preference.ts:20`) [run: grep] |

Two reorder commits claim to move lines unchanged: `2c0e743`'s placement file holds the same lines before and after
as a multiset; `c4ddd0c`'s index differs only in its new module comment and `draftOf` turned into a function
declaration, as its message says [run: sorted-line diff].

### 2.3 The tests and the pull request

**D-21 · Two tests dropped, one moved, seven added since Gate B.** Dropped (`58ee89f`): `useEventStore › sub-agent
index › an older page does not override a newer snapshot` and `sub-agents under the call that spawned them › hides
each child's cost unless costs are shown`; the commit's reason is that other tests pin each. Probes R4 and R5 (the
newest-wins and earliest-`firstAt` rules broken) still fail five and four index tests, and K1 and K2 fail the switch
tests [run]. Moved (`edb963e`): `groups children whose parent session is missing by that parent`, from
`anchorsForParent ›` to `unplacedGroups ›`, with the same one `expect()`. Added: the two of ruling 5, the three of
ruling 6, the switch's two; `shows each child's latest cost and never a sum` is renamed `… when costs are shown`.
C1's cases: 237 passing and 1 todo in 13 files, against 125 and 1 todo in the 8 of them that exist at `9881d24`, so
**C1 adds 112 cases** (106 at Gate B) [run]; CI's 8,228 passing is Gate B's 8,222 plus six [CI].

**D-22 · Thirty-eight commits in PR #4.** v3 §3.2 B14 recorded sixteen; the PR now carries 38, no merges, still into
`wiring/dr-1`, draft, mergeable (`clean`) [run: `git log`; read: REST `pulls/4`]. That each commit is green alone is
not shown; CI ran on pushed heads (green at `b4f6354`, `4db661f` and `2c0e743` since Gate B) [CI].

---

## 3 · Design v3's stale lines (line numbers of `8772b90`)

Each line below describes `9d75806` or an earlier plan and is no longer true at `2c0e743`. Lines v3 itself marks as
v2's plan (§6.1, §6.2 tables) are not listed.

| Lines | Says | At `2c0e743` |
|---|---|---|
| 17–25 | "Matches the build at `9d75806`": sixteen commits, +5,647 −44 in 51 files | 38 commits; +5,778 −44 in 56 files [run: `git diff --numstat`] |
| 44–120 | six things to rule on, with recommendations | ruled; as built in §1 |
| 46–57, 481–483, 712–747 (B15), 791–830 (§4.1) | sizes and per-file lines at `9d75806` | §6.3; new files `subagent-keys.ts` (48), `subagent-cost-preference.ts` (37), `subagent-costs-switch.tsx` (22) and its test (76), `app-settings.tsx` +3; `acp-subagent-event.ts` 22 |
| 127–188 | the evidence: CI and live at `9d75806`, Stryker | §6.1, §6.2; Stryker not rerun |
| 210 | `› groups children whose parent session is missing …` under `anchorsForParent` | under `unplacedGroups ›` (D-21) |
| 211 | `use-event-store.test.ts › … › an older page does not override a newer snapshot` | dropped (D-21) |
| 231, 159 | SUB-006 pinned by `shows each child's latest cost and never a sum`; Live 2 shows `$0.0004` | renamed `… when costs are shown`; the switch tests; Live 2 turns the setting on first (D-14) |
| 251–259 | "Not pinned by any test": B16, C5, C7, C9 | all four pinned (§1); the property table lacks those five tests and the switch's two |
| 340, 355, 383 (J), 410–412, 421–422, 429–431, 989–992, 1059–1062, 1165, 1614 | each row shows its latest cost | hidden unless the setting is on (D-14) |
| 557–562, 2231–2245 | `startOf?: ItemStart`, optional third argument | `toolCalls`, required; no `ItemStart` (D-19) |
| 563–567, 2247–2250, 2259–2260, 2092–2093 | `renderKeyOf`, `SUBAGENT_COUNT_I18N_KEY`, `EMPTY_SUBAGENT_SUMMARY`, `ItemStart` exported; `compareTimestamps` from `subagent-index.ts` | private or gone; `compareTimestamps` in `subagent-keys.ts` (D-16, D-20) |
| 568–569, 896–898 | `placementFieldsOf`, `subagent-index.ts:241`, a joined string | `:326–341`, JSON (D-20) |
| 677–678 | helper exports `SCRIPTED_ACP_PROFILE`, `deleteScriptedAcpAgent`, `startConversation` | private; `scriptedAcpRuns`, `showSubagentCosts`, `COLLAPSED_TOGGLES` exported (D-20) |
| 698–708 (B14), 1468–1472 | sixteen commits, "ten more, through `9d75806`" | 38 (D-22) |
| 751–765 (B16), 945–947 | the build diverges from §4.4 rule 1 | fixed, rule 1 as written (§1) |
| 766–783 (B17) | C5, C7, C9 unpinned | pinned (§1) |
| 837–843 | Canvas declares its own event types, not the client's; `source` is `"agent" \| "environment"` | the client's types (D-15) |
| 850–854, 901, 1821–1851 | the keys live in `subagent-index.ts` | `subagent-keys.ts` (D-16) |
| 864 | transcript insertion by binary search | a scan from the end (D-18) |
| 1017–1024 | `interleaveSubagentAnchors(renderedItems, anchors)` with the optional rule | D-19 |
| 1125–1130, 1132–1152 | 32 keys, all in one block after `EVENT_GROUP$COLLAPSE` | 33; `SETTINGS$SHOW_SUBAGENT_COSTS` elsewhere (D-14) |
| 1172–1178, 1186–1204 | SUB-011 and §4.12 without the switch; spec file 47 lines; tags SUB-004 and SUB-008 only | the switch is in SUB-011; 48 lines; SUB-006 tagged too |
| 1234–1238, 1637–1639 | E6 at `9d75806`: 138.6 ms; "five runs … 70.2 to 323.5 ms" | 43 ms at `2c0e743`, 74.8 ms at `4db661f` (§6.2) |
| 1252–1256 | "C1 adds four Vitest files"; CI ran 769 | five (`subagent-costs-switch.test.tsx`); CI ran 770 |
| 1339–1341, 1371, 1377–1382, 1446–1448 | runs at `9d75806`; Live 2's assertion list | runs at `2c0e743`; Live 2 adds the setting (D-14) |
| 1518–1529, 1557–1560 | C2 at `64b5a8b`/`f4c7ae5`; nine shared files; C2's `getSdkHttpServerErrorReason` | C2 at `a1ec3d1`, eight shared files; both read `exception` through `getApiErrorBody` (§5.3) |
| 1548–1551 | C1 needs `cancelAcpSession` and `CancelAcpSessionResponse` from the client | and the three event types (D-15) |
| 1667–1783 (A.1) | three interfaces, `source` as above | three intersections (D-15) |
| 1878–1896, 1924–1934, 2046, 2256 | `TranscriptItem`'s three variants; `SubagentSummary` in the index | D-20 |
| 2392–2417 (A.9) | the private helpers as exports; `StoredEvent` without `cost` | D-20 |

---

## 4 · The map at `2c0e743`

The architecture is r1's (§4 there) and v3's; the route into the code, with the refactor's moves:

```text
agent-server (dr-1) ── REST page / WebSocket frame
   ▼
useEventStore.addEvent(s) ── subagents = foldSubagentEvents(subagents, new events)   stores/use-event-store.ts
   utils/subagents/subagent-keys.ts       ROOT_SESSION, toolCallKey, messageKey, routeKey, compareTimestamps
   utils/subagents/subagent-index.ts      records (157–192 fold; 220–304 four steps; 307–313 upsert;
                                          326–341 placement fields; 363–379 placeItem; 382–399 answer)
   utils/subagents/subagent-placement.ts  placeSubagents (34–100), anchorsForParent, unplacedGroups,
                                          hasPlaceableAncestry (148–163), replaceEqualDeep sharing
   utils/subagents/subagent-status.ts     categories, SubagentSummary, Stop rules, cost format
   ▼
ChatInterface ── backfill while needsOlderHistory; scroll-follow on subagents.version (chat-interface.tsx:426–457, 483–497)
   └─ Messages ── interleaveSubagentAnchors(items, anchors, toolCalls); UnplacedSubagents   messages.tsx:100–212
        AcpToolCallCell → SubagentBlock → SubagentRow → SubagentTranscript → AcpToolCallCell …
        SubagentRow reads useShowSubagentCosts() (subagent-cost-preference.ts) ◄── /settings/app switch
   Stop → useCancelAcpSession (refusal via getApiErrorBody) → EventService.cancelAcpSession → client
```

[read; each path run by C1's 13 Vitest files, §6.4, and in the live tier, §6.1]

**Where the complexity sits.** Still in the fold and placement: 440 + 48 + 218 + 139 = 845 lines with status,
against 881 at Gate B. The fold's four steps share `upsert`; the dirty rules (a new call key or a newly loaded start;
a message that is new or moved earlier; a text run that opens a transcript; a snapshot whose nine placement fields
changed) decide when placement recomputes. The components are thin readers of the index; `SubagentTranscript` (204)
is the largest. [read]

---

## 5 · Who C1 relies on, and who relies on C1

### 5.1 What C1 relies on

As r1 §4.6 and v3 §9, with three changes [read unless marked]:
- **The `dr-1` client** (1.50.1 from the release tarball) now supplies five things: `ACPSubagentEvent`,
  `ACPSessionMessageEvent`, `ACPSessionTextEvent` (D-15), `CancelAcpSessionResponse` and
  `ConversationClient.cancelAcpSession`. [run: typecheck clean against it; fails without it, §5.3]
- **Upstream Canvas**, beyond r1's list: `getApiErrorBody` (`src/utils/api-error-message.ts:11`), `SettingsSwitch`,
  the App settings route, and `replaceEqualDeep` from `@tanstack/react-query`.
- **S1** is still pinned at `dr-1` (`cef3b24`). S1 has since merged into the SDK fork's `deep-reasoning` after its own
  refactor (Changelog, 2026-10-04 04:48); whether that build stores the same shapes C1 reads I did not check (§8).

### 5.2 D5 (design v2, deep-reasoning `design/d5` at `9ee36f6`, §7.5 and §8.4)

| D5 names | At `2c0e743` |
|---|---|
| SUB-011's test ids and data attributes | all 16 ids and 8 attributes are written in `src/` exactly as `specs/acp-subagent-sessions.md:39–48` lists them [run: grep]; the DOM probe renders them [run] |
| `show-subagent-costs-switch`, off by default, on `/settings/app` | `subagent-costs-switch.tsx`, `app-settings.tsx:230`; off by default [run: switch test, probe K1]; the live test reaches it at `/settings/app` [CI] |
| `OH_ACP_REPLAY_TRANSCRIPTS`, the replay spec's path | read at `acp-subagents.ts:104–110`, split on `path.delimiter`; `tests/e2e/mock-llm/conversations/mock-llm-acp-replay.spec.ts` unchanged in path; one test per path [read; CI: Live 1] |
| `expandAllSubagents`, `readRenderedSubagentTree` as in-page DOM reads | exported, `:242`, `:265`; both `page.evaluate` over SUB-011 selectors (`COLLAPSED_TOGGLES`, `:229`) [read] |
| `readStoredSubagentTree` | exported, `:306` [read] |
| `showSubagentCosts` (§7.5, "as C1's … does") | exported, `:234` [read; CI] |
| `SCRIPTED_ACP_AGENT` (the variable), `MOCK_LLM_PYTHON`, `npm run build:app` | `:38`; `playwright.mock-llm.config.ts:62`; `package.json:105` [read] |

The brief also named `REPLAY_TRANSCRIPTS` and `configureScriptedAcpAgent`; D5's design does not name them, but both
exist, exported, with A.9's signatures (`:104`, `:55`) [read; typecheck]. Nothing D5 names was renamed or made
private; the three helpers made private (D-20) are not in D5.

**A gap in what `canvas-replay` will prove** [read]. The replay spec asserts only `readRenderedSubagentTree(page)`
equals `readStoredSubagentTree(request, id)` (`mock-llm-acp-replay.spec.ts:73–75`); neither side is required to be
non-empty. If the agent-server stored no sub-agent events for a recording (the opt-in lost after the profile check at
`acp-subagents.ts:80`, or a recording without children), both trees are `[]` and the test passes. In C1's own
dispatch the main spec would catch a lost opt-in ("2 sub-agents · 2 running" never appears); D5's job runs the replay
spec alone.

### 5.3 C2 and the fork's `deep-reasoning`

**C2.** PR #3's head is `feat/agent-surfaces` at `a1ec3d1`, not `feat/agent-commands-panels-options` [run: `git
ls-remote`; read: REST `pulls/3`]. The two branches share eight files (r1 counted nine; C2 no longer touches
`type-guards.ts`): `events/index.ts`, `openhands-event.ts`, `translation.json`, `event-service.api.ts` and its test,
`should-render-event.test.ts`, `transcript-export/index.test.ts` and the e2e guide. `git merge-tree 2c0e743 a1ec3d1`
conflicts in one hunk, both branches' new first export line in `src/types/agent-server/core/events/index.ts` (the
Refactorer's finding, confirmed); everything else merges. Resolved by keeping both lines alphabetically, the merge
typechecks, its translations are complete, C1's 13 files pass (241 and 1 todo, C2 adding cases to the shared files)
and C2's 25 changed test files pass (518) [run: a local merge commit in a scratch worktree, never pushed]. Both
branches now read a 5xx's reason through upstream's `getApiErrorBody` (C1 `use-cancel-acp-session.ts:27`, C2
`app-backend-session-keeper.ts:76`); C2's `getSdkHttpServerErrorReason` no longer exists, and C2 also takes its
`ACPSessionControlsEvent` type from the client [read].

**The fork's `deep-reasoning` (`7c12afb`, C3 merged).** `git merge-tree 2c0e743 7c12afb` conflicts in nine files:
`config/defaults.json`, five launcher scripts and three of their tests. None is C1's: it is exactly the set
`9881d24` (`wiring/dr-1`) conflicts in against `7c12afb`, C1's base carrying the pre-split C3 and the dr-1 wiring; and
`deep-reasoning` touches none of C1's 56 files since `02b7ac7` [run]. C1's own diff (`9881d24..2c0e743`) applied onto
`7c12afb` merges cleanly (one auto-merge, the workflow), but does not typecheck: 10 errors, six naming a missing
client export or method (the three event types, `CancelAcpSessionResponse` twice, `cancelAcpSession`) and four in
code that reads those types (`subagent-index.ts:233–234`, upstream's `conversation-websocket-context.tsx:906`), which
I read as following from them; `deep-reasoning` alone has none [run]. Its stock `@openhands/typescript-client` 1.50.1 and null
`sources` lack S1. So C1 lands on `deep-reasoning` only with the redone wiring (D5 §8.6), which must bring a client
with S1's types and an agent-server and scripted agent with S1; without `sources` the workflow step falls back to
upstream's SDK at `v1.50.1` (`mock-llm-e2e.yml:91–94`) [read].

---

## 6 · Runs and measurements

### 6.1 The runs at `2c0e743`

| Run | Conditions | Result |
|---|---|---|
| CI [37184716626](https://github.com/michaeltheologitis/OpenHands/actions/runs/37184716626) | `pull_request`; ubuntu (Node 24.15.0, npm 11.12.1) 8 min 27 s; windows `npm ci` and build only, 1 min 43 s; `live-e2e` skipped as upstream's matrix does | green. Lint: typecheck, ESLint 0 errors and 376 warnings, none in any of C1's 56 files; Prettier clean. Vitest **770 files passed, 1 skipped; 8,228 passed, 1 skipped, 7 todo** in 379 s; build, build:lib, `npm pack --dry-run` green [CI] |
| live [37184736932](https://github.com/michaeltheologitis/OpenHands/actions/runs/37184736932) | `workflow_dispatch` of `mock-llm-e2e.yml`, `specs` = C1's two spec files; the stack from `config/defaults.json` (`cef3b24`); scripted agent at `.tmp/sdk/…/scripted_agent.py`; `OH_ACP_REPLAY_TRANSCRIPTS` = `fallback-placement.jsonl`; mock LLM, no paid model | **6 passed** (1.6 min; job 3 min 3 s), 1 worker: the replay of `fallback-placement.jsonl`; nests; stops one and its branch; same tree after reloading; fallback placement and orphans; E6 [CI] |
| for comparison, `4db661f` | CI 37177982694; live 37177985083, same inputs | green; 6 passed (1.7 min) [CI] |

Reproduce: `gh workflow run mock-llm-e2e.yml --ref feat/acp-subagent-sessions -f specs="tests/e2e/mock-llm/conversations/mock-llm-acp-subagents.spec.ts tests/e2e/mock-llm/conversations/mock-llm-acp-replay.spec.ts"`.
I did not dispatch it: nothing in the read raised a doubt the run had not answered.

### 6.2 E6 (spec §4, design §5): 50 children × 5 calls at 60 events/s

Conditions as r1 §6.2 and design §6.3: the generated fan-out, unchanged since `5b89471`; every block and row expanded
as it appears; a scroll every 250 ms, latency from when it was due to the next frame; null 1,000 ms; no stock-Canvas
arm.

| Run | Commit | ACP events, span, rate | Worst scroll | Long tasks | Scrolls |
|---|---|---|---|---|---|
| 37177985083 | `4db661f` (rulings, cost setting) | 1,203 in 19.7 s, 61.1/s | **74.8 ms** | none | 77 |
| 37184736932 | `2c0e743` (after the refactor) | 1,203 in 19.6 s, 61.4/s | **43 ms** | none | 79 |

Both pass the null by a factor of 13 or more [CI: the E6 log lines]. Gate B's three runs on this load (`5b89471`,
`09da5a1`, `9d75806`, one production code) measured 101.3 to 149.8 ms (r1 §6.2); these are single samples on
shared runners, and the refactor's hot-path changes (D-17, D-18) are not isolated by them.

### 6.3 Size, on the Refactorer's counting

Lines added in `git diff --unified=0 --no-renames 9881d24...<rev>`; production is `src/` without tests and
translations, unit is `__tests__/` and `src/**/*.test.*`, end to end is `tests/e2e/`. Reproduced with the
Refactorer's `count.py`; my per-file output equals its `lines-before.txt` (`4db661f`) and `lines-head.txt`
(`2c0e743`) line for line [run].

| | `9d75806` (Gate B) | `4db661f` | `2c0e743` | refactor |
|---|---|---|---|---|
| production | 2,069 | 2,139 | **2,034** | −105 |
| unit tests | 1,953 | 2,186 | **2,078** | −108 |
| end to end | 1,012 | 1,044 | **1,035** | −9 |
| code and tests | 5,034 (4,551 non-blank) | 5,369 (4,848) | **5,147 (4,659)** | −222 (−189) |
| translations, `specs/`, workflow, guide | 613 | 631 | 631 | 0 |
| `--numstat` total | +5,647 −44, 51 files | +6,000 −44, 55 | +5,778 −44, 56 | the 17 commits: +603 −825 in 24 files |

Where it moved [run]: `subagent-index.ts` 502 → 440 plus `subagent-keys.ts` 48; `subagent-placement.ts` 241 → 245
(ruling 5) → 218; `acp-subagent-event.ts` 99 → 22; `main-flow-anchors.ts` 55 → 69 and `messages.tsx` +75 → +69
(D-19); the cost setting 62 (preference 37, switch 22, route 3) and 4 in the row. Tests: `subagent-index.test.ts`
666 → 682 → 630, `subagent-block.test.tsx` 411 → 461 → 420, the store test 60 → 40, `chat-interface.test.tsx`
+132 → +184, `messages-subagents.test.tsx` 168 → 207, the switch test 76. End to end: helpers 511 → 520 → 550,
main spec 361 → 384 → 359, replay spec 92 → 78. At ≈300 lines an hour, Gate C reads the 5,147 lines in about 17 h,
as at Gate B.

### 6.4 The DOM probe and the expect-counter, rerun

The Refactorer's `dom-probe.test.tsx`, `freeze.sh` (pointed at my worktrees), `vitest.freeze.config.ts`,
`count-assertions.ts` and `compare.py`, with C1's 13 test files [run]:

| | `4db661f` (my baseline) | `2c0e743` |
|---|---|---|
| tests (13 files + the probe's 9) | 248 passed, 1 todo | 246 passed, 1 todo |
| `expect()` calls | 528 | 524 |
| DOM (16 states, normalized) | 147,235 bytes | byte-identical |

`compare.py base head`: removed the three names of D-21, added the moved one; no test with fewer `expect()` calls;
none failing. My baseline equals the Refactorer's `baseline-dom.json`, and my head equals its `placeorder-dom.json`.
The probe renders the same fixture events at both commits: `7f78727` changed the test helper's `message()` default
transcript, and every probe message either names its transcript or is the root's, which the change leaves as it was
[read]. The probe does not cover `ChatInterface` (backfill, scroll) or the e2e helpers.

### 6.5 Local checks at `2c0e743`

`npm run typecheck` clean; ESLint on C1's 34 changed `src/` TypeScript files, 0 problems; Prettier on its 50 `.ts`/`.tsx`
files, clean; translation completeness, every key in every language; C1's 13 Vitest files, 237 passed and 1 todo
[run]. The full suite, the builds and Playwright did not run here; CI's are the record.

---

## 7 · What no test pins: mutation probes

Each probe is one exact edit in my worktree of `2c0e743`, then C1's 13 Vitest files (238 cases), then `git checkout`
of the file; `git status` was empty after every one, and is now [run]. The first six repeat r1's survivors and D-2;
the rest target what the refactor and the cost setting touched.

| Probe | Edit | Result | What it shows |
|---|---|---|---|
| C5 | drop the "own child" check in `TranscriptMessage` (`subagent-transcript.tsx:118`) | caught (1): `shows a child's task to its own child only as that child's task` | ruling 6 holds |
| C7 | a root call starts at its terminal event (`main-flow-anchors.ts:37`) | caught (1): `keeps a root call where it started …` | ruling 6 holds |
| C9 | scroll-follow without `subagentsVersion` (`chat-interface.tsx:457`) | caught (1): `follows sub-agent content into view …` | ruling 6 holds |
| D2 | the ancestry walk fails on any unknown ancestor (`subagent-placement.ts:157`) | caught (2): the two of ruling 5 | ruling 5 holds |
| I3 | `latest.state` out of the placement fields | survived | as r1: equivalent for what S1 writes |
| S1 | Stop when `cancellable` is absent (`=== true` → `!== false`) | survived | as r1: unreachable, S1 always stores the field |
| R1 | no `replaceEqualDeep` for `byCell`/`byAnchor` lists | caught (2): `keeps every unchanged record, transcript, cell list and summary`, `keeps the placement when recomputing it changes nothing` | D-17's sharing is pinned |
| R2 | no `replaceEqualDeep` for `pending` | caught (1): `keeps the placement when recomputing it changes nothing` | pinned |
| R3 | no `replaceEqualDeep` for summaries | caught (2), the same two | pinned |
| R4 | `upsert`: the last arrival wins whatever its time | caught (5), e.g. `keeps the newest snapshot when an older page arrives later` | the dropped store test's rule is still pinned |
| R5 | `upsert`: `firstAt` never moves earlier | caught (4), e.g. `orders a child's transcript by first event, ties by arrival` | pinned |
| R6 | a tie goes to the held event (`>= 0` → `> 0`) | caught (1): `takes the later arrival of two snapshots with one timestamp` | pinned |
| R7 | the scan puts an item before equal timestamps | caught (1): `orders a child's transcript by first event, ties by arrival` | D-18 pinned |
| R8 | no scan: every item appended | caught (1), the same | pinned |
| R9 | the interleave keys a call without its session | survived | equivalent: only root calls reach the root's flow |
| R10 | an anchor at a tie goes before the item (`< 0` → `<= 0`) | survived | not pinned; differs only when an anchor's time equals a root item's start exactly |
| R11 | placement never recomputed for a known child's change | caught (1): `recomputes the summary when a child's state changes` | pinned |
| R12 | `parent_tool_call_id` out of the placement fields | survived | **not pinned**: a later snapshot that only names (or changes) a child's spawning call would leave it at its fallback until another fold marks placement dirty. Unreachable for dr-acp, which names the call at announcement (D1 §5.4); reachable for a generic agent [read] |
| R13 | `lastConfirmed.state` out of the placement fields | survived | not pinned; reachable only when a page brings a confirmed snapshot between two loaded ones without moving `firstAt`, which contiguous pages do not [read] |
| R14 | the fields as `String([...])`, not JSON | survived | equivalent for every value S1 writes (D-20) |
| R15 | a 5xx shows `detail`, not `exception` | caught (1): the 504 refusal case | pinned |
| R16 | `toolCallKey` ignores the session | caught (3), e.g. `keeps tool calls of different sessions with the same id apart` | pinned |
| K1 | costs on by default (`=== "true"` → `!== "false"`) | caught (2): both switch tests | D-14's default is pinned |
| K2 | the row ignores the setting | caught (1): `is off by default and shows sub-agent costs while on` | pinned |
| K3 | the writer does not tell this tab | caught (1), the same | pinned |
| K4 | no `storage` listener: another tab's change ignored | survived | **not pinned**: the commit's "follows other tabs" has no test |
| K5 | the switch writes the opposite value | caught (2) | pinned |
| E1 | `scriptedAcpRuns().start` with `subagents: false` | **not run** (no Playwright here, and a dispatch runs only pushed code) | by reading: the main spec fails at "2 sub-agents · 2 running"; the replay spec passes, both trees empty (§5.2) |
| E3 | `cleanUp` without `ensureMockLLMAgentProfile` | **not run** | by reading: no assertion follows in C1's dispatch; a full mock-LLM run would start later suites on the scripted profile |

In all, 27 run: 19 caught, 8 survived. Of the survivors I3, S1, R9 and R14 are equivalent or unreachable for what S1
writes; R10, R12, R13 and K4 change behaviour in cases no test states, R12 and K4 in cases a user can reach.

---

## 8 · What I could not verify

1. **Playwright, the builds and the full Vitest suite here**: CI's records only. The scripted-agent mutants E1 and E3
   are read, not run.
2. **Each of the 38 commits alone** (D-22): CI ran on pushed heads; I ran ruling 5's two at `94b4bae` and `ba1c1d2`
   only.
3. **The merged S1** (SDK fork `deep-reasoning`, after its refactor): C1 was run only against `dr-1` (`cef3b24`).
   Whether the merged S1 stores the shapes and order C1 reads, and whether its client exports the five names of
   §5.1, is not checked; the redone wiring will decide it.
4. **D5's `canvas-replay` on D1's ten recordings**: still only `1135e87`'s report; no run at `2c0e743`.
5. **The Refactorer's report**: its directory holds scripts, logs and baselines, not a report text; the modules that
   moved (D-15 to D-21) and the property-table rows that changed (§3) are mine, from the commits.
6. **The cost setting in the shared view and across tabs**: read only (D-14, K4).
7. **Stryker**: not rerun since Gate B; the components were never mutated by it. My probes are 27 hand edits, not a
   score.
8. **E6 off GitHub's runners**, and scroll position (jsdom has no layout): as r1.
