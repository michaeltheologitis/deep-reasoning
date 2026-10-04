# C1 · Sub-agent sessions nested in the chat, as built (r3)

**TASK-4** · Cartographer · r3, for Gate C · the code at `51ed1ad`, the top of C1's stack of seven draft PRs (#13–#19)
in the Canvas fork [michaeltheologitis/OpenHands](https://github.com/michaeltheologitis/OpenHands), on the fork's
`deep-reasoning` at `fc87687` (C3 and the dr-2 wiring); its tree is exactly `feat/acp-subagent-sessions` at `090a9d0`
(C1 with `deep-reasoning` merged in) · C1 is `fc87687..51ed1ad`: seven commits, one per level, no merges; +5,865 −44
in 56 files · checked against design v3 (`8772b90`, `docs/design/c1-nested-subagent-sessions.md` on `design/c1`),
Michael's six Gate B rulings and his instruction "fold the cost toggle into C1 now" · revises r2 (`46bde22`, the code at
`2c0e743`): r2's section, finding and probe numbers are kept, since the PR bodies cite them; new findings follow D-22,
the new probe follows R16 · Node 22.22 and npm 10.9 here, Node 24.15 and npm 11.12 in CI · 2026-10-04.

**Where this file lives.** deep-reasoning's branch `as-built/c1-r3`, cut from `as-built/c1-r2` at `46bde22`. That
branch holds `AGENTS.md`, `CLAUDE.md`, `docs/` and `as_built/` only: nothing builds or collects `as_built/`, so there
is nothing to wire. [run: `git ls-tree -r HEAD`]

**Evidence marks.** Every claim carries one.
- **[run]**: executed here, at `51ed1ad` unless marked, in detached scratch worktrees of the Canvas fork (and, for one
  check each, `fc87687` and `bd4cabb`; none pushed): `npm ci` and `npm run make-i18n` first; C1's 13 Vitest files;
  typecheck, ESLint, Prettier and the translation check; nine of r2's mutation probes and one new one, one temporary
  edit each, reverted, the tree clean after each (§7); the Refactorer's `count.py`; `git diff`, `git merge-tree`.
- **[r2: run]**: run by r2 at `2c0e743` and not rerun. No production line has changed since (§1), so these carry over
  by reading; they are not checks made at the top.
- **[CI]**: read from GitHub through REST (`gh api …/actions/jobs/<id>/logs`): the runs D-23, §6.1 and §7 (E1) link.
- **[read]**: read in the code, **not executed**. Weaker than [run]; §8 lists the read claims that matter.

No paid model, no `claude` CLI and no Playwright test ran here. I dispatched nothing and pushed nothing to the Canvas
fork: the replay probe is run 37210189754, dispatched by the agent that narrowed the check, reused because the replay
spec, its helpers and the workflow are byte-identical at the top (§7, E1).

**Reading order.** §1 (what moved, r3's steps included), §2 (divergences; D-23, the stack, and D-24, the replay check,
are new), §3 (the design's stale lines), then §5 for D5, C2 and what C1 relies on, §7 for the probes, §8 for what is
unverified. §4 is the route into the code.

---

## 1 · What moved since Gate B

Seven steps follow r1's `9d75806` [run: `git log`]:

| Step | Commits | What |
|---|---|---|
| Rulings 5 and 6 | `94b4bae`, `ba1c1d2` (ruling 5); `b4f6354` (ruling 6) | D-2 fixed test-first; C5, C7, C9 pinned |
| The cost setting | `dfde47e`, `4db661f` | sub-agent costs hidden unless an App setting shows them (D-14) |
| The literate refactor | `6fafd62` … `2c0e743`, 17 commits | types from the client, a keys module, `replaceEqualDeep`, `upsert`, a scan, the anchor rule moved into the interleave, five exports made private, test helpers, reordering (D-15 to D-21) |
| r2's probes pinned | `a77c3bc` (K4), `bd4cabb` (R12), `db09fc2` (R10) | five test cases, no production line; each fails with its probe's edit (§7) |
| The replay check | `ece9e10`, then `85a84c6` | a transcript that announces a sub-agent must leave one stored (D-24) |
| The redone wiring | `090a9d0` merges the fork's `deep-reasoning` at `fc87687` | C3's stack; `config/defaults.json` names the SDK fork's `dr-2` (`34c540c`); the `dr-2` client tarball |
| The split | `aa745a0` … `51ed1ad` on `fc87687`, draft PRs #13–#19 | seven levels whose top has `090a9d0`'s tree (D-23) |

**What the last four steps changed in C1's 56 files.** Only tests: `git diff 2c0e743 51ed1ad` over them touches four
unit-test files, all additions (+75), and the replay spec (+16 −4) [run]. The merge changed none of them: `git diff
fc87687 51ed1ad` is byte-identical to `git diff 9881d24 85a84c6` (6,729 lines, one patch-id), and each of the 56 files
has the same blob at `9881d24` and at `fc87687` [run]. So C1 is the same diff on its new base, as the PR Splitter says.

**The six rulings, as built.**

| Ruling | At `51ed1ad` |
|---|---|
| 1 · size accepted | Production is 2,034 lines added, as after the refactor and below Gate B's 2,069; unit and end-to-end tests are 3,200, 87 more than r2's 3,113 for the pins and the replay check (§6.3). [run] |
| 2 · keep ✓/■ | `Check` and `Square` with `subagent-done-icon` and `subagent-stopped-icon` (`subagent-row.tsx:87–100`), still outside SUB-011 (`specs/acp-subagent-sessions.md:39–48`). [run: `marks a %s / %s child …`] |
| 3 · E6 at 1,203 events, null 1 s | `SCROLL_LATENCY_LIMIT_MS = 1_000` (`mock-llm-acp-subagents.spec.ts:46`, asserted at `:348`); the main spec is unchanged since `2c0e743` [run: `git diff`]; the live run at the top stored 1,203 ACP events, worst scroll 53.5 ms (§6.2) [CI] |
| 4 · one-transcript smoke replay | `.github/workflows/mock-llm-e2e.yml` unchanged since `9d75806`; `:104` still names `fallback-placement.jsonl` alone [run: `git diff`; CI: the job's environment] |
| 5 · fix D-2 test-first | `94b4bae` adds `sets apart only the child whose own parent is missing, not the children it spawns` (`subagent-index.test.ts:565`) and `nests a child spawned inside an unplaced child under it, in one block` (`messages-subagents.test.tsx:163`); both fail at `94b4bae` and pass at `ba1c1d2` [r2: run]. The fix is one line: an unknown session fails the ancestry walk only when it is the child's own parent (`subagent-placement.ts:157`, `if (!record) return current !== parent;`), which is design §4.4 rule 1. Probe D2 restores the old walk; both tests fail |
| 6 · pin C5, C7, C9 | `b4f6354`: `shows a child's task to its own child only as that child's task` (`subagent-block.test.tsx:251`), `keeps a root call where it started when a child's task lands before it ends` (`messages-subagents.test.tsx:108`), `follows sub-agent content into view as it grows without new root items` (`chat-interface.test.tsx:1077`). Each was written against code that already behaved so; probes C5, C7 and C9 each fail exactly that test |

**What the refactor did not change.** The Refactorer's DOM probe, 16 states of the tree, renders byte-identical
markup at `4db661f` and `2c0e743`; no test name was lost except D-21's three, and no test makes fewer `expect()`
calls [r2: run, §6.4].

---

## 2 · Divergences from design v3 and the rulings

r1's D-1 to D-13 were against v2; v3 absorbed them as its §3.2 B1–B17. B16 (r1's D-2) is fixed and B17's three
behaviours are pinned (§1); the others stand as v3 records them. Below are the divergences from v3 that r1 could not
see, numbered on from r1. The changelog still holds no entry for TASK-4, so no `drift:` line to compare. [read: Notion
query of the Changelog, 2026-10-04]

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
apart [read]. Live 2 waits until the agent-server stored `child-x`'s cost, asserts the row shows none, turns the
switch on on the settings page, reloads and asserts `$0.0004` (`mock-llm-acp-subagents.spec.ts:137–161`) [read; CI:
passed at the top]. *Reason:* Michael's instruction, folded from TASK-15; the commit's own: Canvas shows a
conversation's cost only on demand. *Pinned by:* `subagent-costs-switch.test.tsx` (`is off by default and shows
sub-agent costs while on`, `keeps sub-agent costs shown across a reload`, and, since `a77c3bc`, `follows the setting
when another tab changes it`, which writes the key and dispatches the `StorageEvent` another tab's write raises) and
`subagent-block.test.tsx › … › shows each child's latest cost and never a sum when costs are shown`. Probes K1, K2,
K3, K5 are caught [r2: run]; K4, which drops the `storage` listener, is now caught too [run, §7].

### 2.2 Structure and signatures (the refactor)

**D-15 · The three event types come from the TypeScript client.** Design §4.2: "Canvas keeps its own agent-server
event types … and does not import the client's; C1 follows that convention", and A.1 declares three interfaces.
Built (`1635097`): `acp-subagent-event.ts:16–22`, each `Client<Name> & BaseEvent`, 22 lines instead of 99. The fields
are the client's, with A.1's names and optionality (`dist/events/types.d.ts:142–172`, the same lines in the `dr-1` and
`dr-2` tarballs) [read]; `source` is Canvas's `SourceType` (`"agent" | "user" | "environment" | "hook"`) on all three,
where A.1 has `"agent" | "environment"` and `"agent"`; the per-field JSDoc is gone. Typecheck is clean against the
`dr-2` client [run]. *Reason (commit):* the pinned client already exports all three, and Canvas already takes
`AgentErrorEvent` and `ConversationErrorEvent` from it. *Consequence:* C1 needs five client exports, not A.7's two
(§5.1); on the stock npm client C1 does not typecheck (§5.3).

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
[r2: run; read]

**D-18 · A transcript item's place is found by scanning back from the end.** §4.3's table: "insertion by binary
search (upper bound)". Built (`ea988b2`, `subagent-index.ts:375–377`): the same position in a sorted transcript, after
every item at or before `at`; one step for an item newer than the rest. Probes R7 and R8 are caught. [r2: run]

**D-19 · `interleaveSubagentAnchors(items, anchors, toolCalls)`.** A.6 (v3): an optional `startOf?: ItemStart`
defaulting to the first event's timestamp, with `Messages` passing the call's `firstAt`. Built (`ed44161`):
`toolCalls` is a required third argument and the function dates an ACP call by its record's `firstAt` itself
(`main-flow-anchors.ts:30–38, 45–49`); `ItemStart` and the default are gone. The rule is v3's B5. Probe C7 is caught.
[r2: run]

**D-20 · Smaller changes**, none changing what a user sees [read unless marked]:

| Design v3 | Built at `51ed1ad` (production as at `2c0e743`) |
|---|---|
| A.3: `TranscriptItem` has three variants | two: `{kind: "tool_call" \| "message"; key; at}` and the text item (`subagent-index.ts:61–73`, `dfd5ab8`) |
| A.3: `SubagentSummary` interface in the index; A.5 exports `EMPTY_SUBAGENT_SUMMARY` | `Record<SubagentStatusCategory \| "total", number>` in `subagent-status.ts:15`; the empty constant is gone (`f507374`) |
| §4.3: three "latest" rules, one per record kind | one `upsert` (`subagent-index.ts:307–313`) for snapshots, calls and messages (`dfd5ab8`); probes R4–R6 caught [r2: run] |
| B5: placement fields compared as one joined string (`subagent-index.ts:241` at `9d75806`) | `JSON.stringify` of the same nine fields (`:326–341`, `4f5fb18`); probe R14 (`String(...)`) survives at the top: no test tells the two apart, and for the values S1 writes they agree [run] |
| §4.3: "A call that changed nothing returns `index` itself" | still so; the check compares each record map with the index's (`:179–182`) instead of asking each draft map whether it was written; a write always copies, so the two agree (`dfd5ab8`) |
| A.7: the refusal text reads the client error's body | through upstream's `getApiErrorBody` (`use-cancel-acp-session.ts:27`, `7df5ab0`); same toast; probe R15 caught [r2: run] |
| A.6: `renderKeyOf`, `SUBAGENT_COUNT_I18N_KEY` exported; A.9: `SCRIPTED_ACP_PROFILE`, `deleteScriptedAcpAgent`, `startConversation` exported | all five private (`messages.tsx:42`, `subagent-labels.ts:10`, `acp-subagents.ts:43, 92, 112`; `77b602b`, `1b88117`) |
| A.9's helper list | adds `scriptedAcpRuns()` (`acp-subagents.ts:127–157`: `start` configures the scripted agent with `acp_subagents: true`, routes the session key, starts and records a conversation; `cleanUp` deletes them and restores the mock LLM's profile), `showSubagentCosts` (`:234`, D-14), `COLLAPSED_TOGGLES` (`:229`); `StoredEvent` gains `cost` |
| §4.11 (v3): `@spec` tags in implementation code for SUB-004 and SUB-008 only | also SUB-006 (`subagent-cost-preference.ts:20`) [run: grep] |

Two reorder commits claim to move lines unchanged: `2c0e743`'s placement file holds the same lines before and after
as a multiset; `c4ddd0c`'s index differs only in its new module comment and `draftOf` turned into a function
declaration, as its message says [r2: run: sorted-line diff].

### 2.3 The tests and the pull requests

**D-21 · Two tests dropped, one moved, twelve added since Gate B.** Dropped (`58ee89f`): `useEventStore › sub-agent
index › an older page does not override a newer snapshot` and `sub-agents under the call that spawned them › hides
each child's cost unless costs are shown`; the commit's reason is that other tests pin each. Probes R4 and R5 (the
newest-wins and earliest-`firstAt` rules broken) still fail five and four index tests, and K1 and K2 fail the switch
tests [r2: run]. Moved (`edb963e`): `groups children whose parent session is missing by that parent`, from
`anchorsForParent ›` to `unplacedGroups ›`, with the same one `expect()`. Added: the two of ruling 5, the three of
ruling 6, the switch's two, and r2's three pins as five cases (`follows the setting when another tab changes it`;
`re-places a child whose later snapshot names a spawning call` and `… names another spawning call`
(`subagent-index.test.ts:79`, one `it.each`); `puts a child anchored at the instant a root call starts after that call`
(`messages-subagents.test.tsx:125`) and `puts a grandchild anchored at the instant a child's call starts after that
call` (`subagent-block.test.tsx:277`)). `shows each child's latest cost and never a sum` is renamed `… when costs are
shown`. C1's cases: 242 passing and 1 todo in 13 files, against 125 and 1 todo in the 8 of them that exist at
`fc87687`, so **C1 adds 117 cases** (112 at r2, 106 at Gate B) [run]. CI's 8,235 passing at the top is 8,118 at
`fc87687`'s tree (CI [37211097770](https://github.com/michaeltheologitis/OpenHands/actions/runs/37211097770) on
`9035f9e`, the same tree) plus 117, and 765 files plus C1's five new ones [CI; run: tree ids].

**D-22 · The development branch.** v3 §3.2 B14 recorded sixteen commits; `feat/acp-subagent-sessions` now carries 43
of C1's, no merges among them, then `090a9d0`, the merge of `deep-reasoning` [run: `git log`]. Draft PR #4 still
points at it, into `wiring/dr-1`, open and `clean`; against that base it now lists 71 commits and +6,680 −833 in 68
files, `deep-reasoning`'s own changes included [read: REST `pulls/4`]. That each of the 43 is green alone is not shown;
Gate C reads the stack instead (D-23).

**D-23 · C1 reaches Gate C as seven stacked draft PRs, in an order v3 did not plan.** Design v3 §7: one branch, cut
from `deep-reasoning` once it carries the wiring, "in six commits, each green on its own": events, index, nesting,
Stop, history, end to end. Built: seven levels, one commit each, each a draft PR into the level below, the first into
`deep-reasoning` at `fc87687`, which carries the wiring as §7 asked [run: `git log --graph`; read: REST `pulls/13`–`19`,
all draft, open, `clean`]. The cost setting, which v3 did not have, is its own level; history comes before Stop.
*Reason* (#16's notes): "the stack puts the tree's completeness before the one action on it, as as-built r2 §4's map
reads. Neither this level nor Stop (level 5) uses the other's code; they share only a test file." Each level is green
on its own in CI, which v3 §7 could not show [CI].

| # | PR · head | Title (`feat(chat):` unless shown) | Reviewable lines | CI on the PR (Vitest passed) | r2 sections read beside it (#19's map) |
|---|---|---|---|---|---|
| 1 | #13 · `aa745a0` | `feat(events):` type the ACP sub-agent session events, and keep tool calls of different sessions apart | 314 | [37216786166](https://github.com/michaeltheologitis/OpenHands/actions/runs/37216786166): 8,120 | D-15, D-16; §5.1 |
| 2 | #14 · `6d0ac13` | the event store folds ACP sub-agent sessions into an index that places each child | 1,602 | [37216807043](https://github.com/michaeltheologitis/OpenHands/actions/runs/37216807043): 8,180 | §4; D-17, D-18, D-20 (rows 1–4); §1 ruling 5; §7 R1–R14, I3 |
| 3 | #15 · `16bf782` | nest each ACP sub-agent session under the tool call that spawned it, recursively | 1,379 (+442 translations) | [37216811329](https://github.com/michaeltheologitis/OpenHands/actions/runs/37216811329): 8,203 | D-19; D-20 (private exports); §1 rulings 2, 6; §5.2 |
| 4 | #16 · `c2d5262` | load the older history a visible sub-agent fan-out needs, and follow it as it grows | 260 (+17) | [37216812537](https://github.com/michaeltheologitis/OpenHands/actions/runs/37216812537): 8,207 | §4 (`ChatInterface`); §1 ruling 6; §7 C9 |
| 5 | #17 · `ed70933` | stop one ACP sub-agent session, only when the agent granted cancel | 453 (+85) | [37216814113](https://github.com/michaeltheologitis/OpenHands/actions/runs/37216814113): 8,225 | D-20 (`getApiErrorBody`); §5.1; §7 R15, S1 |
| 6 | #18 · `512bb34` | show sub-agent costs only when an App setting asks for them | 231 (+17) | [37216816205](https://github.com/michaeltheologitis/OpenHands/actions/runs/37216816205): 8,235 | D-14; §7 K1–K5 |
| 7 | #19 · `51ed1ad` | `test(e2e):` drive ACP sub-agent sessions through the real agent-server with a scripted agent | 1,072 | [37216817918](https://github.com/michaeltheologitis/OpenHands/actions/runs/37216817918): 8,235; mock-LLM 6 of 6 | §1 rulings 3, 4; §5.2; §6.1, §6.2; D-20 (A.9); §8 item 1 |

Reviewable lines: added over the level below, code, tests, `specs/`, workflow and guide; translations in brackets, not
counted. My `count.py` split gives each figure the Gate C ledger states [run]. Every run is green on lint (ESLint 0
errors, 376 warnings), Vitest (upstream's 1 skipped, 7 todo), both builds and Windows [CI]. The pins sit in the levels
their tests' files arrive in: `bd4cabb` level 2, `db09fc2` level 3, `a77c3bc` level 6, `ece9e10` and `85a84c6` level 7
[run: `git grep` at each head and its parent].

**The tree check.** `51ed1ad^{tree}` = `090a9d0^{tree}` = `591ce4f` [run]. Each level's parent is the level below, and
`aa745a0`'s is `fc87687` [run]. The levels sum to 5,311 reviewable lines against 5,304 at the top: seven lines are
added by one level and rewritten by a later one [run: each level's removed lines]. All are comments, imports or the
spec's id list: `subagent-row.tsx`'s comment names what its level shows (Stop added at level 5, "cost (when shown)" at
6) and its `getSubagentStatus` import becomes a two-name import at 6, the two the Splitter names; the spec's row-ids
line gains `subagent-stop` at 5 and `subagent-cost` at 6; one import line each in `subagent-block.tsx` (4) and its
test (5) [run: `git show`]. Two more interim states rewrite no line [run]: `subagent-status.ts` arrives at level 2
with 112 lines and no Stop rules or cost format (`canStopSubagent` and `isStopWithheld` join at level 5,
`formatSubagentCost` at 6, 139 lines at the top); and level 1's `keeps ACP tool calls of different sessions apart`
carries `@spec SUB-004` (`handle-event-for-ui.test.ts:306`) while `specs/acp-subagent-sessions.md` arrives with level
3 (`16bf782`). Level 5 also adds a "no Stop" assertion to level 3's reconnect test.

**D-24 · The replay spec requires a stored sub-agent when the transcript announces one.** Design v3 §6.3 (lines
1384–1392): each replay test asserts `readRenderedSubagentTree(page)` equals `readStoredSubagentTree(request, id)`,
nothing more. Built: `ece9e10` added `expect(stored.length).toBeGreaterThan(0)`; `85a84c6` narrowed it to
transcripts whose text matches `/"sessionUpdate":\s*"subagent_update"/` (`mock-llm-acp-replay.spec.ts:33, 81–86`);
the equality follows (`:87`). *Reason (commits):* two empty trees passed the spec, and D5's job runs it alone
(`ece9e10`); two of D1's ten recordings announce no sub-agent and would fail (`85a84c6`). It closes r2 §5.2's gap for
eight of D1's ten recordings (§5.2). *Pinned by:* the probe in §7, E1. [run: `git show`; CI]

---

## 3 · Design v3's stale lines (line numbers of `8772b90`)

Each line below describes `9d75806` or an earlier plan and is no longer true at `51ed1ad`. Lines v3 itself marks as
v2's plan (§6.1, §6.2 tables) are not listed.

| Lines | Says | At `51ed1ad` |
|---|---|---|
| 17–25, 6 | "Matches the build at `9d75806`": sixteen commits on `wiring/dr-1`, +5,647 −44 in 51 files | seven levels on `deep-reasoning` (`fc87687`); +5,865 −44 in 56 files [run: `git diff --numstat`] |
| 44–120 | six things to rule on, with recommendations | ruled; as built in §1 |
| 46–57, 481–483, 712–747 (B15), 791–830 (§4.1) | sizes and per-file lines at `9d75806` | §6.3; new files `subagent-keys.ts` (48), `subagent-cost-preference.ts` (37), `subagent-costs-switch.tsx` (22) and its test (94), `app-settings.tsx` +3; `acp-subagent-event.ts` 22; replay spec 90 |
| 127–188 | the evidence: CI and live at `9d75806`, Stryker | §6.1, §6.2; Stryker not rerun |
| 210 | `› groups children whose parent session is missing …` under `anchorsForParent` | under `unplacedGroups ›` (D-21) |
| 211 | `use-event-store.test.ts › … › an older page does not override a newer snapshot` | dropped (D-21) |
| 231, 159 | SUB-006 pinned by `shows each child's latest cost and never a sum`; Live 2 shows `$0.0004` | renamed `… when costs are shown`; the switch's three tests; Live 2 turns the setting on first (D-14) |
| 251–259 | "Not pinned by any test": B16, C5, C7, C9 | all four pinned (§1); the property table lacks those five tests, the switch's three and the pins' five cases (D-21) |
| 340, 355, 383 (J), 410–412, 421–422, 429–431, 989–992, 1059–1062, 1165, 1614 | each row shows its latest cost | hidden unless the setting is on (D-14) |
| 557–562, 2231–2245 | `startOf?: ItemStart`, optional third argument | `toolCalls`, required; no `ItemStart` (D-19) |
| 563–567, 2247–2250, 2259–2260, 2092–2093 | `renderKeyOf`, `SUBAGENT_COUNT_I18N_KEY`, `EMPTY_SUBAGENT_SUMMARY`, `ItemStart` exported; `compareTimestamps` from `subagent-index.ts` | private or gone; `compareTimestamps` in `subagent-keys.ts` (D-16, D-20) |
| 568–569, 896–898 | `placementFieldsOf`, `subagent-index.ts:241`, a joined string | `:326–341`, JSON (D-20) |
| 677–678 | helper exports `SCRIPTED_ACP_PROFILE`, `deleteScriptedAcpAgent`, `startConversation` | private; `scriptedAcpRuns`, `showSubagentCosts`, `COLLAPSED_TOGGLES` exported (D-20) |
| 698–708 (B14), 1452–1472 (§7) | sixteen commits on `wiring/dr-1`; six planned, Stop before history; "each green on its own … not shown" | 43 commits and a merge on the branch (D-22); seven levels, history before Stop, each green in CI (D-23) |
| 751–765 (B16), 945–947 | the build diverges from §4.4 rule 1 | fixed, rule 1 as written (§1) |
| 766–783 (B17) | C5, C7, C9 unpinned | pinned (§1) |
| 837–843 | Canvas declares its own event types, not the client's; `source` is `"agent" \| "environment"` | the client's types (D-15) |
| 850–854, 901, 1821–1851 | the keys live in `subagent-index.ts` | `subagent-keys.ts` (D-16) |
| 864 | transcript insertion by binary search | a scan from the end (D-18) |
| 1017–1024 | `interleaveSubagentAnchors(renderedItems, anchors)` with the optional rule | D-19 |
| 1125–1130, 1132–1152 | 32 keys, all in one block after `EVENT_GROUP$COLLAPSE` | 33; `SETTINGS$SHOW_SUBAGENT_COSTS` elsewhere (D-14) |
| 1172–1178, 1186–1204 | SUB-011 and §4.12 without the switch; spec file 47 lines; tags SUB-004 and SUB-008 only | the switch is in SUB-011; 48 lines; SUB-006 tagged too |
| 1234–1238, 1637–1639 | E6 at `9d75806`: 138.6 ms; "five runs … 70.2 to 323.5 ms" | 53.5 ms at `51ed1ad` (§6.2) |
| 1252–1256 | "C1 adds four Vitest files"; CI ran 769 | five (`subagent-costs-switch.test.tsx`); CI ran 770 |
| 1339–1341, 1371, 1377–1382, 1446–1448 | runs at `9d75806`; Live 2's assertion list | runs at `51ed1ad`; Live 2 adds the setting (D-14) |
| 1384–1392 | the replay spec asserts rendered equals stored | and a stored sub-agent when the transcript announces one (D-24) |
| 1518–1529, 1557–1560 | C1 and C2 on `wiring/dr-1`; C2 at `64b5a8b`/`f4c7ae5`; nine shared files; C2's `getSdkHttpServerErrorReason` | both on `deep-reasoning`; C2 at `30068b8`, eight shared files; both read `exception` through `getApiErrorBody` (§5.3) |
| 1538–1553, 1588, 1607 | S1 at the SDK fork's `dr-1` (`cef3b24`); the `dr-1` client; `wiring/dr-1` | `dr-2` (`34c540c`) and its client, through `fc87687` (§5.1) |
| 1548–1551 | C1 needs `cancelAcpSession` and `CancelAcpSessionResponse` from the client | and the three event types (D-15) |
| 1667–1783 (A.1) | three interfaces, `source` as above | three intersections (D-15) |
| 1878–1896, 1924–1934, 2046, 2256 | `TranscriptItem`'s three variants; `SubagentSummary` in the index | D-20 |
| 2392–2417 (A.9) | the private helpers as exports; `StoredEvent` without `cost` | D-20 |

---

## 4 · The map at `51ed1ad`

The architecture is r1's (§4 there) and v3's; no production line has changed since `2c0e743` (§1). The route into
the code, with the refactor's moves:

```text
agent-server (S1 at dr-2) ── REST page / WebSocket frame
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

[read; each path run by C1's 13 Vitest files at the top, §6.5, and in the live tier, §6.1]

**Where the complexity sits.** Still in the fold and placement: 440 + 48 + 218 + 139 = 845 lines with status,
against 881 at Gate B. The fold's four steps share `upsert`; the dirty rules (a new call key or a newly loaded start;
a message that is new or moved earlier; a text run that opens a transcript; a snapshot whose nine placement fields
changed) decide when placement recomputes. The components are thin readers of the index; `SubagentTranscript` (204)
is the largest. Anchors at a tie go after the item, in the root's flow (`main-flow-anchors.ts:58`, `< 0`) and in a
transcript (`subagent-transcript.tsx:40–48`, items spread before anchors into a stable sort), as v3 §4.6 states
(lines 1014, 1019). [read; run: probes R10, R17]

---

## 5 · Who C1 relies on, and who relies on C1

### 5.1 What C1 relies on

As r1 §4.6 and v3 §9, with these changes [read unless marked]:
- **The `dr-2` client** (1.50.1, `releases/download/dr-2/openhands-typescript-client-1.50.1.tgz`, `package.json:27`)
  supplies five things: `ACPSubagentEvent`, `ACPSessionMessageEvent`, `ACPSessionTextEvent` (D-15),
  `CancelAcpSessionResponse` and `ConversationClient.cancelAcpSession`. [run: all five in its `dist/index.d.ts:26` and
  `client/conversation-client.d.ts`; typecheck clean against it; r2 showed it fails without them, §5.3]
- **Upstream Canvas**, beyond r1's list: `getApiErrorBody` (`src/utils/api-error-message.ts:11`), `SettingsSwitch`,
  the App settings route, and `replaceEqualDeep` from `@tanstack/react-query`.
- **S1 at `dr-2`**: `config/defaults.json` names `34c540c`, the head of the SDK fork's `deep-reasoning` and the commit
  tag `dr-2` peels to [run: `git ls-remote`, `merge-base`]. The mock-LLM tier passed 6 of 6 against it at `090a9d0` and
  at `51ed1ad` [CI]. Sub-agents stay behind S1's opt-in there: `ACPAgent.acp_subagents` defaults to `False`
  (`acp_agent.py:2217–2226`), and only with it does the client advertise the capability (`:3288`) and use the
  sub-agent connection (`:3450`).
- **ACP's wire name `subagent_update`**, from the unstable schema 1.24.1, which the SDK vendors
  (`openhands-sdk/openhands/sdk/agent/acp_unstable.py:76–77`, `Literal["subagent_update"]`, beside
  `agent-client-protocol` 0.12.1 in `uv.lock`). The replay spec decides whether a transcript announces a sub-agent by
  that name alone (`mock-llm-acp-replay.spec.ts:33`). If a later schema renames it, a recording made with the new name
  matches nothing, the stored-sub-agent check is skipped, and two empty trees compare equal: the spec passes and
  proves nothing. **Whoever bumps the SDK pin or ACP's must rerun the replay probe** (§7, E1: an announcing
  transcript replayed with the opt-in off) and see it fail.

### 5.2 D5 (design v2, deep-reasoning `design/d5` at `9ee36f6`, §7.5 and §8.4)

| D5 names | At `51ed1ad` |
|---|---|
| SUB-011's test ids and data attributes | all 16 ids and 8 attributes are written in `src/` exactly as `specs/acp-subagent-sessions.md:39–48` lists them [r2: run: grep; `src/` and the spec file unchanged since]; the DOM probe renders them [r2: run] |
| `show-subagent-costs-switch`, off by default, on `/settings/app` | `subagent-costs-switch.tsx`, `app-settings.tsx:230`; off by default [r2: run: probe K1]; the live test reaches it at `/settings/app` [CI] |
| `OH_ACP_REPLAY_TRANSCRIPTS`, the replay spec's path | read at `acp-subagents.ts:104–110`, split on `path.delimiter`; `tests/e2e/mock-llm/conversations/mock-llm-acp-replay.spec.ts` unchanged in path; one test per path [read; CI: Live 1] |
| `expandAllSubagents`, `readRenderedSubagentTree` as in-page DOM reads | exported, `:242`, `:265`; both `page.evaluate` over SUB-011 selectors (`COLLAPSED_TOGGLES`, `:229`) [read] |
| `readStoredSubagentTree` | exported, `:306` [read] |
| `showSubagentCosts` (§7.5, "as C1's … does") | exported, `:234` [read; CI] |
| `SCRIPTED_ACP_AGENT` (the variable), `MOCK_LLM_PYTHON`, `npm run build:app` | `:38`; `playwright.mock-llm.config.ts:62`; `package.json:105` [read] |

The helpers file is byte-identical to `2c0e743`'s, so every line number above is r2's [run: `git diff`].
`REPLAY_TRANSCRIPTS` and `configureScriptedAcpAgent` exist, exported, with A.9's signatures (`:104`, `:55`) [read;
typecheck]. Nothing D5 names was renamed or made private.

**The gap r2 named is closed for announcing transcripts** (D-24). r2: neither tree was required to be non-empty, so a
lost opt-in or a recording without children passed. Now a transcript with a `subagent_update` fails unless the
agent-server stored a sub-agent; probe E1 shows it (§7).

**Two of D1's ten recordings announce no sub-agent.** `linear.native.jsonl` and `claude.native.jsonl` hold no
`subagent_update`; the other eight hold 2 to 40 each [run: grep of deep-reasoning `main`, `b2a74e0`; the same blobs at
`53c821b`]. For those two, `canvas-replay` proves only that two empty trees are equal: that the replay ran and Canvas
rendered no sub-agent where none was stored. Run 37210189754 replayed byte-identical copies of both: passed, both
trees empty [CI].

**A condition D5's job must keep** (named by the D5 Implementer): the replayed agent runs with `acp_subagents` on.
C1's spec sets it: `scriptedAcpRuns().start` calls `configureScriptedAcpAgent(request, { flags, subagents: true })`
(`acp-subagents.ts:136`), which asserts the profile kept the opt-in (`:80`). A job that runs C1's spec unchanged meets
it; one that builds its own profile must set it. With it off, an announcing transcript now fails (E1); a non-announcing
one passes either way. [read; CI]

**D5's own lines that moved** [read]: §8.4 names C1 as "PR #4" and says C1 and C2 "are built on `wiring/dr-1` and
merge the redone wiring (§8.6) before they merge"; C1 is now #13–#19 on `deep-reasoning` with that wiring merged
(D-23). §7.5's `canvas-replay` row ends "Each transcript's rendered tree equals its stored tree"; the spec now also
fails an announcing transcript with nothing stored (D-24).

**`nested-stop.jsonl` is not a replay transcript, by design** [read]. Replayed through the replay spec, its turn never
ends: the wiring agent's finding, which fails the same way at C1's old head (as relayed to me). It is the Stop spec's
fixture: a two-way transcript whose client `session/cancel` for `child-x` (line 22 of 31) is a wait point only a press
of Stop answers. Its one use is `mock-llm-acp-subagents.spec.ts:104–113` (`nests each sub-agent …`, `--wait-timeout
120`), whose conversation the serial Stop (`:163`) and reload (`:221`) tests reuse; the workflow replays
`fallback-placement.jsonl` alone (`mock-llm-e2e.yml:104`). Replayed, nobody presses Stop: the scripted agent waits its
default 30 s (`scripted_agent.py:105` at `34c540c`) and exits non-zero, no `FinishAction` is stored, and
`waitForTurnsToEnd` times out at 120 s, as design v3 B11 (lines 658–663) reads it. Neither the replay spec nor the e2e
guide says that a transcript with a client wait point cannot be replayed.

### 5.3 C2 and the fork's `deep-reasoning`

**C2.** `feat/agent-surfaces` is at `30068b8` (C2 with `deep-reasoning` merged in), and C2's stack top
`feat/agent-surfaces-07-app-backend-frames` (`ca1dd71`) has its tree (`14be24f`) [run: `git ls-remote`, tree ids]. The
two share eight files, as at r2: `src/types/agent-server/core/events/index.ts`, `openhands-event.ts`,
`translation.json`, `event-service.api.ts` and its test, `should-render-event.test.ts`,
`transcript-export/index.test.ts` and the e2e guide. `git merge-tree 51ed1ad 30068b8` (and `ca1dd71 51ed1ad`)
conflicts in one hunk of one file, `src/types/agent-server/core/events/index.ts`: C1's `export * from
"./acp-subagent-event";` against C2's `export * from "./acp-session-controls-event";`, both the file's new first
export; the other seven auto-merge [run]. Whichever stack merges second keeps both lines (#13's notes). r2 resolved
the merge against `a1ec3d1`, typechecked it and ran both branches' tests [r2: run]; against `30068b8` only the trial
merge ran. Both branches read a 5xx's reason through upstream's `getApiErrorBody` (C1 `use-cancel-acp-session.ts:27`)
[read].

**The fork's `deep-reasoning`.** r2 found that C1's diff onto `7c12afb` did not typecheck without a client with S1's
types. That is resolved: `fc87687` carries the `dr-2` client and `sources`, C1 merged it (`090a9d0`) and its stack
starts on it, and the top typechecks [run]. On the stock npm client C1 still does not typecheck [r2: run].

---

## 6 · Runs and measurements

### 6.1 The runs at `51ed1ad`

| Run | Conditions | Result |
|---|---|---|
| CI [37216817918](https://github.com/michaeltheologitis/OpenHands/actions/runs/37216817918) | `pull_request` on #19; ubuntu (Node 24.15.0) 11 min; windows `npm ci` and build only, 1 min 50 s; `live-e2e` skipped as upstream's matrix does | green. Lint: typecheck, ESLint 0 errors and 376 warnings; Prettier clean. Vitest **770 files passed, 1 skipped; 8,235 passed, 1 skipped, 7 todo** in 494 s; build, build:lib, `npm pack --dry-run` green [CI] |
| mock-LLM [37216822781](https://github.com/michaeltheologitis/OpenHands/actions/runs/37216822781) | `workflow_dispatch` of `mock-llm-e2e.yml` on the level-7 branch, `specs` = C1's two spec files; the stack `config/defaults.json` names (SDK fork `34c540c`, `dr-2`); `OH_ACP_REPLAY_TRANSCRIPTS` = `fallback-placement.jsonl`; mock LLM, no paid model | **6 passed** (1.8 min; job 3 min 47 s): the replay of `fallback-placement.jsonl`; nests; stops one and its branch; same tree after reloading; fallback placement and orphans; E6 [CI] |
| for comparison, `090a9d0` (same tree) | CI [37215757890](https://github.com/michaeltheologitis/OpenHands/actions/runs/37215757890); mock-LLM [37215758052](https://github.com/michaeltheologitis/OpenHands/actions/runs/37215758052), same inputs | green, 8,235 passed; 6 passed (1.8 min) [CI] |
| for comparison, `85a84c6` (before the merge, `dr-1`) | mock-LLM [37210407059](https://github.com/michaeltheologitis/OpenHands/actions/runs/37210407059), same inputs | 6 passed (1.7 min) [CI] |

Reproduce: `gh workflow run mock-llm-e2e.yml --ref feat/acp-subagent-sessions-07-agent-server-e2e -f
specs="tests/e2e/mock-llm/conversations/mock-llm-acp-subagents.spec.ts
tests/e2e/mock-llm/conversations/mock-llm-acp-replay.spec.ts"`. r2's runs at `2c0e743` (CI 37184716626, live
37184736932) and `4db661f` stand for that code.

### 6.2 E6 (spec §4, design §5): 50 children × 5 calls at 60 events/s

Conditions as r1 §6.2 and design §6.3: the generated fan-out, unchanged since `5b89471`; every block and row expanded
as it appears; a scroll every 250 ms, latency from when it was due to the next frame; null 1,000 ms; no stock-Canvas
arm.

| Run | Commit | Agent-server | ACP events, span, rate | Worst scroll | Long tasks | Scrolls |
|---|---|---|---|---|---|---|
| 37177985083 | `4db661f` (rulings, cost setting) | `dr-1` | 1,203 in 19.7 s, 61.1/s | **74.8 ms** | none | 77 |
| 37184736932 | `2c0e743` (after the refactor) | `dr-1` | 1,203 in 19.6 s, 61.4/s | **43 ms** | none | 79 |
| 37210407059 | `85a84c6` (pins, replay check) | `dr-1` | 1,203 in 19.8 s, 60.8/s | **97.2 ms** | none | 78 |
| 37215758052 | `090a9d0` (merged) | `dr-2` | 1,203 in 19.7 s, 61.0/s | **74.5 ms** | none | 82 |
| 37216822781 | `51ed1ad` (stack top, same tree) | `dr-2` | 1,203 in 19.6 s, 61.3/s | **53.5 ms** | none | 79 |

All pass the null by a factor of 10 or more [CI: the E6 log lines]. No production line differs between the last four
rows' commits (§1); each row is one sample on a shared runner, and two agent-servers appear. Gate B's three runs on
this load measured 101.3 to 149.8 ms (r1 §6.2).

### 6.3 Size, on the Refactorer's counting

Lines added in `git diff --unified=0 --no-renames <base>...<rev>`; production is `src/` without tests and
translations, unit is `__tests__/` and `src/**/*.test.*`, end to end is `tests/e2e/`. Run with the Refactorer's
`count.py` (scratchpad `c1r/count.py`), base `9881d24` for the first three columns and `fc87687` for the top. I ran
the `2c0e743` column, which reproduces r2's, and the top's [run]; the first two are r2's [r2: run].

| | `9d75806` (Gate B) | `4db661f` | `2c0e743` (r2) | `51ed1ad` on `fc87687` | since r2 |
|---|---|---|---|---|---|
| production | 2,069 | 2,139 | 2,034 | **2,034** | 0 |
| unit tests | 1,953 | 2,186 | 2,078 | **2,153** | +75 |
| end to end | 1,012 | 1,044 | 1,035 | **1,047** | +12 |
| code and tests | 5,034 (4,551 non-blank) | 5,369 (4,848) | 5,147 (4,659) | **5,234 (4,732)** | +87 (+73) |
| translations, `specs/`, workflow, guide | 613 | 631 | 631 | 631 (561 of them translations) | 0 |
| `--numstat` total | +5,647 −44, 51 files | +6,000 −44, 55 | +5,778 −44, 56 | +5,865 −44, 56 | +87 |

`count.py` with base `9881d24` at `85a84c6` gives the top's column line for line, since the two diffs are one (§1)
[run]. Where it moved since r2 [run]: `subagent-index.test.ts` 630 → 650, `subagent-block.test.tsx` 420 → 440,
`messages-subagents.test.tsx` 207 → 224, the switch test 76 → 94, the replay spec 92 → 78 (refactor) → 90 (D-24). The
rest is r2's: `subagent-index.ts` 502 → 440 plus `subagent-keys.ts` 48; `subagent-placement.ts` 241 → 218;
`acp-subagent-event.ts` 99 → 22; the cost setting 62; helpers 550; main spec 359. At ≈300 lines an hour, Gate C reads
the 5,234 lines in about 17 h; the stack's levels add seven interim lines (D-23).

### 6.4 The DOM probe and the expect-counter (r2's, not rerun)

r2 ran the Refactorer's DOM probe and expect-counter with C1's 13 test files at `4db661f` and `2c0e743`: 248 and 246
tests passed (1 todo each), 528 and 524 `expect()` calls, and the 16 normalized DOM states (147,235 bytes)
byte-identical; `compare.py` found only D-21's removals and move, and no test with fewer `expect()` calls [r2: run]. It
does not cover `ChatInterface` or the e2e helpers. Not rerun at the top: the components are unchanged since `2c0e743`,
and the tests only gained cases [read].

### 6.5 Local checks at `51ed1ad`

`npm run typecheck` clean against the `dr-2` client; ESLint on C1's 34 changed `src/` TypeScript files, 0 problems;
Prettier on its 50 `.ts`/`.tsx` files, clean; translation completeness, every key in every language; C1's 13 Vitest
files, 242 passed and 1 todo; at `fc87687` the 8 that exist there, 125 passed and 1 todo [run]. The full suite, the
builds and Playwright did not run here; CI's are the record.

---

## 7 · What no test pins: mutation probes

Each probe is one exact edit in a scratch worktree, then C1's 13 Vitest files, then `git checkout` of the file;
`git status` was empty after every one, and is now [run]. r2 ran 27 at `2c0e743`. r3 reran at `51ed1ad` the eight that
survived there and added R17, the transcript's half of the tie rule; R10 and R17 also ran at `bd4cabb`, the commit
before `db09fc2`. Rows marked [run] ran here; the others are r2's results [r2: run], carried because no production line
changed and no test was removed since (§1), so each test that failed then still exists [read].

| Probe | Edit | Result | What it shows |
|---|---|---|---|
| C5 | drop the "own child" check in `TranscriptMessage` (`subagent-transcript.tsx:118`) | caught (1): `shows a child's task to its own child only as that child's task` | ruling 6 holds |
| C7 | a root call starts at its terminal event (`main-flow-anchors.ts:37`) | caught (1): `keeps a root call where it started …` | ruling 6 holds |
| C9 | scroll-follow without `subagentsVersion` (`chat-interface.tsx:457`) | caught (1): `follows sub-agent content into view …` | ruling 6 holds |
| D2 | the ancestry walk fails on any unknown ancestor (`subagent-placement.ts:157`) | caught (2): the two of ruling 5 | ruling 5 holds |
| I3 | `latest.state` out of the placement fields | survived [run] | as r1: equivalent for what S1 writes |
| S1 | Stop when `cancellable` is absent (`=== true` → `!== false`) | survived [run] | as r1: unreachable, S1 always stores the field |
| R1 | no `replaceEqualDeep` for `byCell`/`byAnchor` lists | caught (2): `keeps every unchanged record, transcript, cell list and summary`, `keeps the placement when recomputing it changes nothing` | D-17's sharing is pinned |
| R2 | no `replaceEqualDeep` for `pending` | caught (1): `keeps the placement when recomputing it changes nothing` | pinned |
| R3 | no `replaceEqualDeep` for summaries | caught (2), the same two | pinned |
| R4 | `upsert`: the last arrival wins whatever its time | caught (5), e.g. `keeps the newest snapshot when an older page arrives later` | the dropped store test's rule is still pinned |
| R5 | `upsert`: `firstAt` never moves earlier | caught (4), e.g. `orders a child's transcript by first event, ties by arrival` | pinned |
| R6 | a tie goes to the held event (`>= 0` → `> 0`) | caught (1): `takes the later arrival of two snapshots with one timestamp` | pinned |
| R7 | the scan puts an item before equal timestamps | caught (1): `orders a child's transcript by first event, ties by arrival` | D-18 pinned |
| R8 | no scan: every item appended | caught (1), the same | pinned |
| R9 | the interleave keys a call without its session (`toolCallKey(null, …)`, `main-flow-anchors.ts:36`) | survived [run] | equivalent: only root calls reach the root's flow |
| R10 | an anchor at a tie goes before the item (`main-flow-anchors.ts:58`, `< 0` → `<= 0`) | **caught** (1): `puts a child anchored at the instant a root call starts after that call` [run]; survived at `bd4cabb` [run] | `db09fc2` pins v3 §4.6's rule in the root's flow |
| R11 | placement never recomputed for a known child's change | caught (1): `recomputes the summary when a child's state changes` | pinned |
| R12 | `parent_tool_call_id` out of the placement fields | **caught** (2): `re-places a child whose later snapshot names a spawning call`, `… names another spawning call` [run] | `bd4cabb` pins it: a later snapshot that only names, or changes, a child's spawning call re-places it, which a generic ACP agent can send |
| R13 | `lastConfirmed.state` out of the placement fields | survived [run] | not pinned; reachable only when a page brings a confirmed snapshot between two loaded ones without moving `firstAt`, which contiguous pages do not [read] |
| R14 | the fields as `String([...])`, not JSON | survived [run] | equivalent for every value S1 writes (D-20) |
| R15 | a 5xx shows `detail`, not `exception` | caught (1): the 504 refusal case | pinned |
| R16 | `toolCallKey` ignores the session | caught (3), e.g. `keeps tool calls of different sessions with the same id apart` | pinned |
| **R17** | a transcript's anchor at a tie goes before the item (`subagent-transcript.tsx:46–47`, anchors spread before items) | **caught** (1): `puts a grandchild anchored at the instant a child's call starts after that call` [run]; survived at `bd4cabb` [run] | `db09fc2` pins the same rule inside a transcript |
| K1 | costs on by default (`=== "true"` → `!== "false"`) | caught (2): both first switch tests | D-14's default is pinned |
| K2 | the row ignores the setting | caught (1): `is off by default and shows sub-agent costs while on` | pinned |
| K3 | the writer does not tell this tab | caught (1), the same | pinned |
| K4 | no `storage` listener (`subagent-cost-preference.ts:12` removed) | **caught** (1): `follows the setting when another tab changes it` [run] | `a77c3bc` pins the commit's "follows other tabs" |
| K5 | the switch writes the opposite value | caught (2) | pinned |
| E1 | the scripted agent run with `acp_subagents` off | replay spec: **caught** [CI]; main spec: **not run** | run [37210189754](https://github.com/michaeltheologitis/OpenHands/actions/runs/37210189754) at `fcb14a7` (`85a84c6` plus the probe) replayed `fallback-placement.jsonl` (passed), copies of D1's `linear` and `claude` (passed, empty trees), and a byte-identical copy of `fallback-placement.jsonl` with the opt-in off: its one failure, `the agent-server stored no sub-agent for this transcript` (`Received: 0`). Spec, helpers and workflow are byte-identical at the top [run: `git diff`]; the agent-server was `dr-1` (§8 item 9). Main spec, by reading: fails at "2 sub-agents · 2 running" |
| E3 | `cleanUp` without `ensureMockLLMAgentProfile` | **not run** | by reading: no assertion follows in C1's dispatch; a full mock-LLM run would start later suites on the scripted profile |

In all, 28 run: 23 caught, 5 survived; E1's replay half caught in CI. Nine ran at the top: K4, R10, R12 and R17
caught, I3, S1, R9, R13 and R14 survived; the new tests catch none of those five. Of the survivors, I3, S1, R9 and
R14 are equivalent or unreachable for what S1 writes; R13 changes behaviour only in a case contiguous pages do not
produce [read].

---

## 8 · What I could not verify

1. **Playwright, the builds and the full Vitest suite here**: CI's records only. E3 and E1's main-spec half are read,
   not run.
2. **Each of the development branch's 43 commits alone** (D-22). Each of the stack's seven levels is green in CI
   (D-23); locally only the top ran.
3. **The merged S1** is now the pin (`dr-2`, `34c540c`), and the mock-LLM tier passed against it [CI]. Beyond what that
   tier and the typecheck exercise, I did not check that it stores every shape and order C1 reads.
4. **D5's `canvas-replay` on D1's ten recordings**: still only `1135e87`'s report, against `dr-1`. Two of them
   (`linear`, `claude`) ran in the probe at `fcb14a7`, both trees empty; the eight that announce sub-agents have not run
   through the spec as narrowed, at any commit.
5. **The Refactorer's report**: its directory holds scripts, logs and baselines, not a report text; the modules that
   moved (D-15 to D-21) and the property-table rows that changed (§3) are mine, from the commits.
6. **The cost setting in the shared view**: read only (D-14). Across tabs it is now pinned (K4).
7. **Stryker**: not rerun since Gate B; the components were never mutated by it. My probes are 28 hand edits, not a
   score.
8. **E6 off GitHub's runners**, and scroll position (jsdom has no layout): as r1.
9. **E1 at the top's agent-server.** Run 37210189754 used `dr-1` (`cef3b24`), since its branch predates the merge.
   That `dr-2` with the opt-in off stores no sub-agent is read in its code (§5.1), not run.
10. **`nested-stop.jsonl` through the replay spec** (§5.2): the wiring agent's finding, read here, not run.
11. **C1 merged with C2's current head**: only `git merge-tree` against `30068b8`; the resolved merge was typechecked
    and tested by r2 against `a1ec3d1`.
12. **R10 and R17 at `bd4cabb`** ran with the top's `node_modules`, so on the `dr-2` client, while `bd4cabb`'s lock
    names `dr-1`'s.
