# C1 · Sub-agent sessions nested in the chat — design

**TASK-4** · System Designer · code lands in the Canvas fork
[michaeltheologitis/OpenHands](https://github.com/michaeltheologitis/OpenHands), branch
`feat/acp-subagent-sessions`, as one pull request (v1: cut from `deep-reasoning` after the wiring commit, §9.3; built
on the fork's `wiring/dr-1`, §3.2 B14) · against the approved spec
[TASK-1](https://app.notion.com/p/3ed62fb22237814ab425c81b3844f012) (C1 in full, S1, D1's
emission and Stop, Q3, §4 E6 and the layers, the 2026-10-02 amendment and the note decided after approval), S1's
design (deep-reasoning `design/s1` `f956fda`, `docs/design/s1-acp-subagent-sessions.md`, §5 above all) and D1's wire
contract (deep-reasoning `f281109`, `docs/design/d1-dr-acp.md` §5).
**Pinned against:** Canvas fork `deep-reasoning` at `02b7ac7` (= upstream `1ff45c2` plus the ASE commit, which
touches only `AGENTS.md` and `CLAUDE.md`, so every `file:line` below is also upstream `1ff45c2`'s) ·
`@openhands/typescript-client` as S1 §4.9 extends it (`ConversationClient.cancelAcpSession`,
`CancelAcpSessionResponse`, `ACP_SETTINGS_KEYS` with `acp_subagents`) · SDK fork `91430aa` (= upstream `53a4bc5`) for
the agent-server facts · React 19.3, zustand 5.0.14, Playwright and Vitest as `package.json` pins them.

**Matches the build at `9d75806`** (v3): `feat/acp-subagent-sessions` in the draft pull request
[michaeltheologitis/OpenHands#4](https://github.com/michaeltheologitis/OpenHands/pull/4) against the fork's branch
`wiring/dr-1` (head `9881d24`: C3's launcher, `config/defaults.json` naming the SDK fork's commit `cef3b24` (tag
`dr-1`, which carries S1 at its v2.2 build) as the agent-server's source, `@openhands/typescript-client` 1.50.1 pinned
to the `dr-1` release tarball, and the `specs` input on `mock-llm-e2e.yml`). C1's own commits are sixteen, with no
merge: the six §7 planned, `3f0fea8`, `b76b7ad`, `08fb2cc`, `67e3cdb`, `81d810e` and `85e9899`, then `e49d19a`,
`9c23e8d`, `15f66c5`, `1135e87`, `dee08db`, `ed8a7fc`, `98a43ab`, `5b89471`, `09da5a1` and `9d75806` (§3.2 B14). So
`git diff 9881d24..9d75806`, PR #4's diff, is C1 alone: 5,647 lines added and 44 removed, in 51 files. Line numbers
cited from the built code are at `9d75806`; v1's and v2's stay upstream `1ff45c2`'s.

## Gate B: what to read

**About an hour, in this order.** The codebase stays closed. The Gate B set is this doc, C1's as-built document
(`as_built/c1-nested-subagent-sessions.md` on deep-reasoning's branch `as-built/c1`, the Cartographer's) and the two
runs below. Everything after §3 is kept whole as the reference D5, C2 and the PR split build against (Michael: don't
force compression); Gate B does not need it, except §5 and §6.3.

| # | Read | What it gives you | Minutes |
|---|---|---|---|
| 1 | This section and the v3 revision line below it | where the proof is, six rulings, and which sentences of v2 changed | 18 |
| 2 | §1 | what C1 changes, and why (unchanged; decisions I and M carry v3 notes) | 6 |
| 3 | §3.1 | where the design departs from the spec (v2's §3; item 6's estimate is replaced by the size below) | 3 |
| 4 | §3.2 | what the build changed, each with its reason and the test that pins it | 15 |
| 5 | §5 and §6.3 | E6 and the live tier, as run | 4 |
| 6 | Open the two runs below | that they are green at `9d75806` | 2 |
| 7 | `as_built/c1-nested-subagent-sessions.md` | what exists and its divergences, as the Cartographer read them | 10 |

**Six things to rule on.** Nothing changes in code until Michael rules.

1. **Size.** The spec estimated C1 at ≈1.2k lines with tests and ≈4 h at Gate C; v2 at ≈3.0k, plus ≈0.5k of
   translations, and ≈8 h (§3.1 item 6). The build is **5,647 lines added and 44 removed** in 51 files at `9d75806`
   (5,150 of the added lines are not blank), 1.6 times v2's ≈3.5k: 2,069 of production TypeScript (v2 ≈1.4k), 1,953 of
   Vitest tests and their helpers (≈1.0k), 1,012 of Playwright specs, helpers and transcripts (≈0.6k), 544 of
   translations (≈530; 32 keys in upstream's 15 languages) and 69 of upstream's `specs/` file, the workflow step and
   the e2e guide. The excess is concentrated: `subagent-index.ts` is 502 lines against 230, `subagent-placement.ts`
   241 against 150, `subagent-transcript.tsx` 202 against 110, the end-to-end helpers 511 against 220, and the tests
   mutation testing asked for are 238. At v2's own rate (3.0k lines in 8 h, 375 an hour) Gate C reads the 5,103 lines
   that are not translations in about 13.6 h, against v2's 8; at the workspace's ≈300 an hour, the rate C2's and C3's
   Gate B sections use, in about 17 h (18.8 h with the translations), against the spec's 4. §3.2 B15 has the table.
   The build recorded no reason for the growth; the reading there is this design's. **Recommended: accept it into the
   next phase**, where the Scout and the Refactorer are where it shrinks; B15 names where the lines are.
2. **The ✓ and ■ marks on finished sub-agents** (§3.2 B6). v2's walkthrough and status table drew a finished child as
   ✓ done and a stopped one as ■ stopped; the first build showed the words alone, and `dee08db` adds the marks
   (lucide's `Check` and `Square`, 41 lines with their test). v2 also said the ACP card keeps "today's success mark":
   at this base upstream's tool-call cards show none (their `SuccessIndicator` draws only a clock, for a timeout,
   `success-indicator.tsx:8–18`). Upstream's chat does mark "done" in its two status lists, though: a finished task
   in the task tracker gets a check-circle (`task-tracking/task-item.tsx:28–29`), and a completed goal a green one
   (`goal-status-content.tsx:151–154`). The choices: (a) keep them, as built; (b) drop them, so a finished row says
   "done" or "stopped" in words only, as upstream's cards say nothing on success. **Recommended: (a).** A sub-agent
   row is a status line like a task's, its state is what the user scans for in a list of up to fifty, and the
   running ones already spin; the marks are one commit, which upstream review could drop whole. Drawing the done mark
   with the task tracker's own `u-check-circle.svg` would match upstream's look more closely; that is a one-line
   change, and not needed for Gate B. Either way their test ids stay out of SUB-011's stable list.
3. **E6's load** (§3.2 B10). E6 is Michael's falsifier (the spec's "a 50-child fan-out makes the chat unusable";
   §3.1 item 10's null: over 1 s from a scheduled scroll to the next painted frame). The first build's generated
   fan-out sent no child text and one cost report per child: 753 stored events. `5b89471` gives each of a child's five
   cells a thought and a cumulative cost report, which is §5's load case (per child an announcement, a task, ~5 text
   runs, 10 call events, an answer, an idle snapshot and cost snapshots: about 1,100 events), so 1,203 events and a
   thinking block per cell in every expanded child. That reading of §5 is the Implementer's. At `9d75806` it
   measured 138.6 ms against the 1,000 ms null. **Recommended: confirm the 1,203-event load as E6's and keep the null
   at 1 s.** It is the load §5 named and the shape a dr-acp fan-out streams, it is the harsher of the two, and the
   worst of five runs so far is 323.5 ms.
4. **The smoke replay plays one transcript** (§3.2 B11). §6.3 had CI's run of the replay spec play C1's transcripts
   and the fan-out; the workflow names only `fallback-placement.jsonl`. `nested-stop.jsonl` has a client
   `session/cancel` line, a wait point only a press of Stop answers: replayed, the scripted agent waits, exits
   non-zero at its default 30 s `--wait-timeout`, and the turn never ends. The fan-out is written into a temporary
   directory inside E6's own test, so no file exists when the workflow sets the variable. The choices: (a) as built;
   (b) make both replayable: a third hand-written transcript, `nested.jsonl`, that is `nested-stop.jsonl` with its
   children ending on their own (about 25 lines of JSONL and one more path in the workflow's
   `OH_ACP_REPLAY_TRANSCRIPTS`), and a workflow step that writes the fan-out before Playwright starts (a `node` call
   of `writeFanoutTranscript`, about 10 lines; the replay plays it unpaced, as a burst); (c) the first half of (b)
   only. **Recommended: (a).** The smoke replay proves that the replay spec itself runs in CI, the path D5 drives with
   D1's recordings (§6.4), and one transcript proves it; the trees of the other two are already compared with what
   the agent-server stored, by live tests 2, 4 and 6.
5. **A child spawned inside a child that could not be placed is shown apart a second time** (§3.2 B16; the as-built
   document's §2.1 D-2, a new finding). Take `child-o`, announced on a session `ghost` the conversation does not hold,
   and `child-p`, spawned in `child-o`'s own loaded call. The design (§4.4 rule 1) places `child-p` inside that call,
   under `child-o`'s row in the could-not-be-placed block. The build walks `child-p`'s whole ancestry and, finding
   `ghost` missing two levels up, sets `child-p` apart too: a second block says "1 sub-agent could not be placed: its
   parent session child-o is not in this conversation." while `child-o` is shown just above it. The Cartographer's
   probe confirmed it, and no test covers a subtree under an unplaced child. The choices: (a) a test-first fix before
   merge: the probe's case as a fold test and a `Messages` test, then `hasPlaceableAncestry` fails only on an unknown
   direct parent or a loop, not on an unknown ancestor further up (a few lines in `subagent-placement.ts`); (b) leave
   it, and name it in the PR as a known gap, since it needs an agent that announces a child on a session it never
   announced, which D1's contract rules out for dr-acp (D1 §5.4 rule 1: every child is announced before its
   traffic). **Recommended: (a).** The block states something false about a parent shown
   on the same screen, and the fix is small and local.
6. **Three behaviours a user sees that no test pins** (§3.2 B17; the as-built document's §6.4, probes C5, C7 and
   C9). Each probe changed the code and every test still passed; the code at `9d75806` behaves as designed in all
   three. For each, pin it (one test) or leave it:
   - **C5: a child's task to its own child must not also show as a "To …" message in the child's transcript.**
     **Recommended: pin it**, with one `subagent-block.test.tsx` case that expands a child with a child of its own;
     a regression would print every task twice in a fan-out's expanded rows.
   - **C7: in the root's flow, a call sits where it started, not where it finished** (§3.2 B5; the as-built's §2.1
     D-6). v2's own rule was the wrong one, so nothing but this build's code states the right one. **Recommended: pin
     it**, with one `messages-subagents.test.tsx` case anchoring a child whose task lands between a root call's start
     and its end.
   - **C9: a chat pinned to the bottom follows sub-agent content that grows without new root items** (§4.8 item 3).
     **Recommended: pin it**, with one `chat-interface.test.tsx` case modelled on upstream's own test that follows the
     goal banner into view (it stubs the scroll geometry jsdom lacks); otherwise a user watching a live fan-out
     would see it grow out of view.

   The other two survivors are not worth a test: probe I3 is equivalent for every snapshot S1 writes, and probe S1 (a
   Stop offered when `cancellable` is absent) is unreachable, since S1 always stores the field.

**The live tier is the mock-LLM end to end, not a real task with a real model.** §6.3 and §6.6 define it so, after
the spec's §4 layer 5 ("D3, C1, C2, C3: through their end-to-end tests"); it departs from the workspace's definition
of a live tier (a real task against real services, its outcome asserted) exactly as C2's does, and C2's Gate B ruling
2 asks that question for both. dr-acp through Canvas with a real model is D5's E12.

**The evidence.** Both runs are at `9d75806`, the branch's head.

- **CI**, upstream's `ci.yml` on PR #4, [run 37171885463](https://github.com/michaeltheologitis/OpenHands/actions/runs/37171885463), green:
  - **test-and-build (ubuntu)**, 9 min 13 s: `npm ci`; `npm run lint` (typecheck, eslint and prettier: 0 errors and
    376 warnings, every one upstream's `shadcn/no-arbitrary-values` rule and none on C1's lines); `npm test` (Vitest:
    769 files passed and 1 skipped; **8,222 tests passed**, 1 skipped, 7 todo; C1's 106 new cases among them, from 74
    test definitions, 8 of them `it.each` tables, in 12 test files); `npm run build`; `npm run build:lib`; `npm pack
    --dry-run`.
  - **test-and-build (windows)**, 1 min 33 s: `npm ci` and `npm run build` only. Upstream's matrix skips lint, tests
    and the library build there, so no C1 test runs on Windows.
  - **prepare-test-matrix**, green. **live-e2e**, upstream's real-model job, skipped: it runs only on
    `workflow_dispatch` or a push to `main` (`ci.yml:83–86`).
  - Also green on PR #4: the PR-title workflow (runs 37171885197 and 37172407006). Upstream's PR-description check
    is disabled in the fork, so it did not run. CI one commit earlier, at `09da5a1`, was red on lint (a test's object
    literal failed TypeScript's excess-property check); `9d75806` is that fix.
- **Live tier**, as §6.3 and §6.6 define it: the fork's `mock-llm-e2e.yml` dispatched on `feat/acp-subagent-sessions`
  with its `specs` input naming C1's two specs and nothing else,
  [run 37171891707](https://github.com/michaeltheologitis/OpenHands/actions/runs/37171891707): **6 of 6 passed**
  (1.7 min; the job 3 min 19 s). The stack is the one `bin/agent-canvas.mjs` starts, so the agent-server is installed
  from `config/defaults.json` `sources`, the SDK fork at `cef3b24` (tag `dr-1`), with the `dr-1` client; the
  workflow's new step fetched the scripted ACP agent from the same commit, sparse and shallow. The model is the mock
  LLM server; the ACP agent is S1's scripted agent in `--transcript` mode, as an agent profile with
  `acp_subagents: true`; no key, no paid model. The six, each named for what it asserts (Live 1 to 6 below):
  - `tests/e2e/mock-llm/conversations/mock-llm-acp-replay.spec.ts › ACP sub-agent sessions, replayed ›`
    1. `nests fallback-placement.jsonl as the agent-server stored it`: the replay path D5 drives (§6.4), on the one
       transcript CI names; with everything expanded, the tree the DOM nests equals the tree the agent-server stored
       (SUB-001).
  - `tests/e2e/mock-llm/conversations/mock-llm-acp-subagents.spec.ts › ACP sub-agent sessions ›` (serial; 2 to 4
    share one conversation on `nested-stop.jsonl`)
    2. `nests each sub-agent under the call that spawned it`: three levels (`child-x` and `child-y` in the root's
       `cell-1`, `child-z` in `child-x`'s `cell-x1`); the summary reads "2 sub-agents · 2 running" while the run
       waits; the rendered tree equals the stored one; the root's flow holds `cell-1` alone; `child-x` shows its own
       `$0.0004` (SUB-001, SUB-004, SUB-006).
    3. `stops one sub-agent and its branch`: `child-y`'s Stop is withheld, `aria-disabled`, and its tooltip is the
       spec's sentence; `child-x`'s Stop posts `…/acp/sessions/child-x/cancel`; then `child-x` and `child-z` turn
       stopped, `cell-x1` failed and `child-y` done, each from the agent's own report, and no Stop is left (SUB-007).
    4. `shows the same tree after reloading`: from the REST history, "2 sub-agents · 1 done · 1 stopped"; the rendered
       tree equals the stored one; no Stop anywhere; the root's answer is there, and a child's answer appears only
       inside its row (SUB-004, SUB-005).
    5. `places sub-agents without a spawning call and shows orphans apart`: on `fallback-placement.jsonl` the root's
       flow reads `cell-1`, `child-m` (where the root sent its task, after `cell-1`), `child-a` (at its
       announcement), `child-g` (it names a call never sent: at its announcement, once history is complete),
       `cell-2`, then the could-not-be-placed block naming `ghost`, holding `child-o` (SUB-002, SUB-003).
    6. `stays responsive while 50 sub-agents with 5 tool calls each stream in`: E6. **1,203 ACP events in 19.7 s
       (61.1/s)**, every block and row expanded as it appeared, a scroll every 250 ms: **worst scroll latency
       138.6 ms** against the 1,000 ms null, 76 scrolls, no long task; then "50 sub-agents · 50 done", and the
       rendered tree equals the stored one (SUB-010). The same test measured 149.8 and 101.3 ms on the same load and
       the same production code at `5b89471` and `09da5a1`, and 70.2 and 323.5 ms (one 72 ms long task) on the
       earlier 753-event load at `15f66c5` and `ed8a7fc`, whose production code differs only by the status marks:
       runner noise is at least 2x, and the worst run so far is a third of the null.

  The whole mock-LLM suite was not run at `9d75806`. C2's Gate B found six of upstream's tests failing on the fork's
  base itself (C2's run 37149694708), none of them C1's.
- **Mutation testing**, which §6.5 asks for (§3.2 B13): Stryker on `subagent-index.ts`, `subagent-placement.ts` and
  `subagent-status.ts`, each against its own Vitest suite: 599 mutants, of which 134 survived before `09da5a1` (77.6%
  killed). `09da5a1` adds the tests that kill the ones that change what Canvas shows (238 lines), leaving 64 (89.3%),
  most of them equivalent; two real but contrived survivors were left untested. The tooling finding: Stryker's Vitest
  runner, which upstream's `stryker.config.mjs` names, is unreliable in this repo, so the run used Stryker's command
  runner. The components were not mutated. The 134 of 599 is in `09da5a1`'s message; the 64, the two survivors and
  the runner are the Implementer's report, with no committed configuration or log. The Cartographer's own 23 hand
  mutation probes over the three modules and seven component and consumer files (the as-built's §6.4): 18 caught, 5
  survived; ruling 6 takes the three a user would see.

**Which tests carry which property.** Each test's name states the property it pins. Paths are from the fork's root;
`›` separates `describe` blocks; `[…]` is an `it.each`; "Live" names the six above by number. `index.test` is
`__tests__/utils/subagents/subagent-index.test.ts`, `status.test` its sibling `subagent-status.test.ts`, `block.test`
`__tests__/components/conversation-events/chat/subagents/subagent-block.test.tsx` (its outer block is `sub-agents
under the call that spawned them`, written `…` below) and `messages.test`
`__tests__/components/conversation-events/chat/messages-subagents.test.tsx` (outer block `Messages with ACP sub-agent
sessions`, likewise `…`).

*Part 1 · events and call keys* (`3f0fea8`)

| Property | Tests |
|---|---|
| **ACP calls of two sessions with one id never merge** (decision G; S1 §5 rule 3) | `__tests__/utils/handle-event-for-ui.test.ts › handleEventForUI › ACPToolCallEvent dedup › keeps ACP tool calls of different sessions apart`; `index.test › foldSubagentEvents › keeps tool calls of different sessions with the same id apart`, `› keeps messages and routes of different transcripts apart`; `__tests__/components/features/chat/typing-indicator.test.ts › deriveLiveActivity › a finished child call does not mask a running root call with the same id` |
| **The transcript export keeps a child's calls, in time order** (§4.5) | `src/utils/transcript-export/index.test.ts › conversation transcript export › exports tool calls made inside sub-agent sessions` |

*Part 2 · the sub-agent index, placement and status* (`b76b7ad`, `ed8a7fc`, `09da5a1`)

| Property | Tests |
|---|---|
| **The tree is each child's latest snapshot; a child sits in the call that spawned it, in announcement order** (SUB-001; S1 §5 rules 1–2) | **Live:** 1, 2, 6. `index.test › foldSubagentEvents › rebuilds parent links from each child's latest snapshot`, `› places a child in the tool call that spawned it, in announcement order`, `› orders a cell's children by announcement when an older page brings an earlier one`, `› refuses to recurse into a parent loop` |
| **Without a loaded spawning call, at the parent's message to it, else at its announcement; a missing parent is apart** (SUB-002, SUB-003) | **Live:** 5. `index.test › foldSubagentEvents › places a child without a spawning call at its parent's message, else at its announcement`, `› moves a child to its parent's message to it, and to an earlier one an older page brings`; `› anchorsForParent › adds the fallbacks of children whose spawning call never turned up, once history is complete`, `› groups children whose parent session is missing by that parent` |
| **The newest wins by timestamp, a tie by arrival, whatever page brings it** (decision C) | `index.test › foldSubagentEvents › keeps the newest snapshot when an older page arrives later`, `› takes the later arrival of two snapshots with one timestamp`, `› keeps the newest version of a message when an older page arrives later`, `› upserts a message and keeps its place`, `› orders a child's transcript by first event, ties by arrival`, `› keeps every entry of a child's transcript across folds, whatever its kind`, `› takes the agent's own report of a child call over the failure stored when the root's turn was aborted`; `› buildSubagentIndex › builds the same index from a page in any order, each event once`; `__tests__/stores/use-event-store.test.ts › useEventStore › sub-agent index › an older page does not override a newer snapshot` |
| **A reconnect never confirms; the last confirmed snapshot survives it** (S1 §5 rule 7) | `index.test › foldSubagentEvents › keeps the newest confirmed snapshot across a reconnect, whichever page brings it`, `› holds a child known only from reconnect snapshots as never confirmed` |
| **A child's own call count and its answer** (§4.3 `stats`) | `index.test › foldSubagentEvents › counts a child's own calls and takes its answer from its newest message outside its children`, `› takes a child's answer from the newest message it sent` |
| **Partial history: wait, do not guess; ask for older pages only while needed** (decision D; SUB-008) | `index.test › foldSubagentEvents › waits for a parent session that is not loaded`, `› waits for a named spawning call that is not loaded, with its fallback`, `› places a waiting child once the older page with its spawning call arrives`, `› needs older history until every spawning call's start is loaded`, `› takes a %s event as the spawning call's start` [pending, in_progress], `› needs older history for a transcript whose session was never announced in the loaded pages` |
| **What did not change keeps its identity, which is what keeps 50 × 5 cheap** (decision B) | `index.test › foldSubagentEvents › keeps every unchanged record, transcript, cell list and summary`, `› keeps a child's transcript and stats when one of its calls completes`, `› returns the same index for an older snapshot that changes nothing`, `› keeps the placement when recomputing it changes nothing`, `› does not recompute placement for a cost-only snapshot`, `› recomputes the summary when a child's state changes`, `› returns the same index for events that are not about ACP sessions` (SUB-009), `› ignores events from the planning agent` |
| **One writer: folded in the store's own `set`, reset with it** (decision A) | `use-event-store.test.ts › useEventStore › sub-agent index › folds sub-agent events with each event and each page`, `› clears the sub-agent index with the conversation` |
| **Each child's latest state; an unconfirmed state never spins** (SUB-005; §4.7) | `status.test › getSubagentStatus › reads %s / %s as %s` [11 reported states], `› reads %s as unconfirmed` [the agent's own snapshot without a state, a reconnect snapshot that still carries one], `› reads a reconnect with nothing confirmed loaded as unconfirmed`, `› keeps a last confirmed %s state as the last known one after a reconnect` [running, requires_action], `› keeps a last confirmed idle state as history after a reconnect`; `› summarizeSubagents › counts children by status category` |
| **Each child's latest cost, never added** (SUB-006) | `status.test › formatSubagentCost › formats %s %s as %s` [6: null, absent, USD, zero, another currency, no currency] |
| **Stop only for a running or waiting child that granted cancel on the live connection** (SUB-007; §3.2 B2) | `status.test › Stop › %s, cancellable %s, from the %s: Stop %s, withheld %s` [9, among them an idle child that still carries the grant] |

*Part 3 · nesting in the chat* (`08fb2cc`, `dee08db`, `9c23e8d`)

| Property | Tests |
|---|---|
| **Each sub-agent renders inside the call that spawned it, recursively** (SUB-001) | **Live:** 1, 2, 4, 6. `block.test › … › expands to each child's cells and their own sub-agents` (three levels) |
| **The shared view nests from its own events, read-only** (decision K) | `__tests__/routes/shared-conversation-viewer-behavior.test.tsx › shared conversation viewer › nests sub-agents in a shared conversation, read-only` (its `Messages` stand-in reports the index it is given: the child in its cell, read-only, history complete); `block.test › … › Stop › never offers Stop in a read-only view` |
| **A collapsed summary counts children by state, never by cost** (spec bullet 2; decision J) | **Live:** 2, 4, 6. `block.test › … › shows a collapsed summary counting children by state` |
| **The root's flow shows only the root's work** (SUB-004) | **Live:** 2, 4. `messages.test › … › main flow shows only the root's work`; `__tests__/components/conversation-events/chat/event-content-helpers/should-render-event.test.ts › shouldRenderEvent - ACPToolCallEvent › hides tool calls made inside a sub-agent session`, `› leaves sub-agent snapshots, messages and text to the sub-agent tree` |
| **Placement in the root's flow, and orphans apart** (SUB-002, SUB-003) | **Live:** 5. `messages.test › … › anchors a child without a spawning call at the root's message to it`, `› shows children of a missing parent apart once history is complete` |
| **The state as shown: the last known one without a spinner; the marks** (SUB-005; §3.2 B3, B6) | **Live:** 3, 4. `block.test › … › shows the last known state without a spinner after a reconnect`, `› marks a %s / %s child with %s beside its status` [running, done, stopped, waiting, limited] |
| **The latest cost per child** (SUB-006) | **Live:** 2. `block.test › … › shows each child's latest cost and never a sum` |
| **A child's task first, its answer last** (§4.6) | `block.test › … › shows a child's task first and its answer last` |
| **The card and its sub-agents keep their expansion when the call completes** (decision H) | `messages.test › … › keeps sub-agents expanded when the spawning call completes` |
| **Agents without sub-agent sessions render as before** (SUB-009) | `messages.test › … › renders agents without sub-agent sessions as before`; `should-render-event.test.ts › shouldRenderEvent - ACPToolCallEvent › hides tool calls made inside a sub-agent session` (its root-call assertion) and upstream's cases in that block, unchanged and green |

*Part 4 · Stop* (`67e3cdb`, `e49d19a`)

| Property | Tests |
|---|---|
| **Stop is offered only when granted, explained when withheld, never optimistic, never in a read-only view** (SUB-007; decisions I, K) | **Live:** 3, 4. `block.test › … › Stop › offers Stop only for a running child that granted cancel`, `› explains why Stop is unavailable when the agent withheld cancel`, `› asks to cancel and waits for the child's own cancelled state`, `› never offers Stop in a read-only view` |
| **The request goes to the conversation's runtime with its session key; a refusal shows the agent-server's reason** (§3.2 B1) | **Live:** 3 (the request). `src/api/event-service/event-service.api.test.ts › EventService › cancelAcpSession › cancelAcpSession posts to the conversation's runtime with its session key`, `› rejects with the server's refusal as the client raised it`; `block.test › … › Stop › shows the server's reason when a cancel is refused: %s` [a 409 with its detail, a 504 whose reason is under `exception`, a failure without a body] |

*Part 5 · the history a fan-out needs* (`81d810e`)

| Property | Tests |
|---|---|
| **Opening a conversation loads older pages until the spawning call's start is in, and stops after a failure** (SUB-008) | `__tests__/components/chat/chat-interface.test.tsx › ChatInterface - Sub-agent history backfill › loads older pages until the spawning call's start is loaded`, `› stops loading older pages after a failure`; `block.test › … › says earlier activity is loading while the cell's start is missing`; Part 2's partial-history row |

*Part 6 · end to end* (`85e9899` and the test commits after it): Live 1 to 6, above. SUB-010 is Live 6 alone.

**Not pinned by any test:** a child spawned inside an unplaced child, which the build gets wrong (§3.2 B16, ruling 5);
a child's task to its own child never also showing as a "To …" message (B17's C5); an ACP card's place in the root's
flow being its call's start rather than its terminal event's (B5, B17's C7); the bottom-following scroll on the
index's version (B17's C9) and the scroll restore after an older page that holds only child events (§4.8 item 3); the
indentation stopping at depth 6 and the "depth N" label (§3.1 item 9); "From {name}" lines in a transcript; the
per-entry memoization (§3.2 B8), which E6 measures but nothing counts; the backfill through the real stack, since
every live conversation fits in its first page (SUB-008 is pinned in Vitest only); the two Stryker survivors the
Implementer left; and anything Stryker would find in the components, which it did not mutate (§3.2 B13). §6.1 and §6.2
are v2's plan; this section and §3.2 B9 are the tests as built.

**Revisions** (newest first; the Gate B reader approved the previous version, so each line says which sentences to
stop trusting):
- 2026-10-04 · v3 · brought in line with the build at `9d75806`, after Proof Green, and with C1's as-built document
  (deep-reasoning `as-built/c1` at `d16d3df`), whose findings B16 and B17 and rulings 5 and 6 carry. Stop trusting:
  the header's "cut from `deep-reasoning` after the wiring commit", and §7's six commits and its draft PR against the
  fork's `main` (B14); v2's §3 item 6 estimate (now §3.1 item 6, replaced by B15); §4.1's line counts and file list
  (B4, B15); §4.4 rule 1 as a description of the code, which diverges from it (the rule stands, B16); §4.6's "the
  success mark [is] today's" (B6), "an item's start is its first event's timestamp" (B5) and the transcript's naming
  of an untitled child (B5); §4.7's refusal toast through `getApiErrorMessage` (B1) and its "another currency" as the
  only non-USD case (B5); §4.8 item 1's provider around the scroll container (B5); §4.10's 31 keys and the separator's
  `eslint-disable` (B5); §4.11's tags in implementation code (B5); §5's "E6 measures it", now measured (B10); §6.1's
  and §6.2's test tables, now v2's plan with the built ones in the section above (B9); §6.3's assertion list, its CI
  replay of every transcript and the fan-out, and the Docker variable (B11, B12); §6.5 (B13); §6.6's layers 3 and 5
  (B13, B14); §8 rows 9 and 10 (C2 shares neither); §9.1 (all four built in S1); §10 items 1, 2 and 5; Appendix A.3 to
  A.7 and A.9 where a signature or its comment changed (each such line carries `// v3:`). Renumbered: v2's §3 is §3.1,
  and every "§3 item N" of C1's own now reads "§3.1 item N"; decision I's reference to S1's "§3 item 14" now reads
  S1's own renumbering, "§3.1 item 14", and §9.2's two references to D1's §3 now say "D1". Added without changing
  earlier sentences: the "Matches the build" paragraph and this Gate B section; §3.2; notes marked *(v3)* in §1.3
  (decisions I and M), §2 items 6, 7, 8 and 11, §3.1 items 6, 9 and 10, §4.1, §4.3 to §4.8, §4.10 to §4.12, §5, §6,
  §6.1 to §6.6, §7, §8, §9.1, §9.3, §9.4 and §10; §9's opening list of what C1's code relies on and shares; Appendix
  A's block for `subagent-labels.ts`. Every TypeScript block in Appendix A still typechecks under `strict` (TypeScript
  6.0.3, against the built code's own types where a block imports them) and passes Prettier at upstream's settings,
  one field per line. Every change is listed, with its reason, in §3.2.
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

**Reading guide.** Gate B: the section above. §3.1 lists every departure from the approved spec, §3.2 every change
the build made. S1's designer and the Conductor: §9 (what C1 relies on). C2's designer and the PR splitter: §8 (every
file both touch, with a trial merge of the two heads) and §3.2 B14. D5's designer: §6.4 (the replay of D1's golden
recordings through the forked Canvas), §4.12 (the test ids E12 can rely on) and §9.4. The Implementer, the
Cartographer and the Refactorer read everything; Appendix A is the signature reference.

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
| I | **Stop is never optimistic.** Enabled only for a running or waiting child whose latest snapshot is live and `cancellable`; disabled, with the spec's sentence, when the agent withheld `cancel`; absent for idle and unconfirmed children and in read-only views. After a 200 the row says "Stopping…" until the child's own `idle`/`cancelled` snapshot arrives. | S1 §5 rules 6–7 and S1 §3.1 item 14; the RFD's freshness rule. dr-acp's stop lands at the agent's next turn, so a client-side "stopped" would be contradicted moments later. *(v3: built so. A refusal shows the agent-server's own reason, §3.2 B1; an idle child whose snapshot still carries the grant gets no control, B2.)* | Marking the branch stopped on click; hiding the control entirely when withheld (the spec's failure cell explains it on hover where Stop would be). |
| J | **Costs are shown per child and never added**, not even across siblings. | ACP forbids it and S1 §5 rule 5 extends it to siblings; dr-acp's costs are inclusive of descendants (D1 §6.2), so a sum would double-count at every level. | The mock-up's `$0.0021` on the summary line (§3.1 item 1). |
| K | **Components read the index through a context that defaults to the event store**; the shared view provides one built from its own events, marked read-only. | Keeps `Messages`' contract (it renders whatever events it is given) and the shared view correct. | Reading the global store everywhere: the shared view would hide child work entirely. |
| L | **No capability flag and no `minimumAgentServer` bump.** | Everything keys off events and fields that only an agent-server with S1 writes; on any other server the index stays empty and Stop never appears, so Canvas need not require S1 (`AGENTS.md`: raise the floor only when Canvas starts *requiring* something). | A `ServerInfo` capability: S1 adds none (S1 §9 row 11), and there is nothing to hide when the events are absent. |
| M | **No virtualization.** Blocks and rows are collapsed by default, a row renders its transcript only when expanded, and rows are memoized on their own record. | Upstream's chat has none; nested variable-height rows are the hard case for windowing libraries; §5 shows the work per event stays small. E6 measures it. | Adding a windowing dependency up front. If E6 fails, the first remedy is `content-visibility: auto` on rows (§5). *(v3: E6 passed without either remedy, its worst scroll 138.6 ms against 1,000, §3.2 B10.)* |

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
   ✓ done, the answer `'3cr, 0 prereqs — light'` and `1 tool call`. *(v3: the ✓ is built in `dee08db`, after a first
   build that showed the word alone; Michael rules on it, §3.2 B6.)*
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

   *(v3: as built, a row's header reads mark, status word, title, answer, tool calls, then the cost and Stop outside
   the toggle: `✓ done  Summarize the workload of CS101.  "3cr, 0 prereqs — light"  1 tool call  $0.0004`. The child's
   card has no ✓: upstream's card shows no success mark, §3.2 B6.)*

8. **Stop on `n3`**, which has a child `n5`. Click → `POST …/acp/sessions/<n3>/cancel` → 200 `{"requested": true}`;
   `n3`'s button turns "Stopping…". dr-acp's acknowledgement arrives as a thought on `n3`. As each agent of the branch
   actually ends, its snapshot arrives `idle`/`cancelled`: `n5` (under `n3`'s cell), then `n3`; each row turns ■
   stopped and loses Stop *(v3: ■ built in `dee08db`, §3.2 B6)*. In the interim (Dean's API not shipped), `n4` turns
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
    cancellable=False)` for each child that was active or cancellable *(v3: for each child that was active, S1's v2
    B3; an idle child keeps its last snapshot, which may still say `cancellable: true`, §3.2 B2)*. C1 shows the last
    state the agent confirmed (from the previous snapshot) without a spinner and without Stop; a child that was
    running reads "running · last known" (S1 §5 rule 7). *(v3: carried by `SubagentStatus.lastKnown`, §3.2 B3.)*

---

## 3 · Where this design departs from the approved spec, and what the build changed

### 3.1 Departures from, and additions to, the approved spec

Each is a refinement inside C1's scope. If the Conductor reads any as a change of what was approved, it goes back to
Michael. *(v3: items 1 to 5, 7 and 8 hold as built; items 6, 9 and 10 have notes.)*

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
   real agent-server, the 50 × 5 load case, D5's golden replay). About 8 h at Gate C, not 4. *(v3: built at 5,647
   lines added, about 13.6 h at Gate C at this item's own rate and 17 h at ≈300 lines an hour; for Michael's ruling,
   the Gate B section and §3.2 B15.)*
7. **The transcript export stays flat.** It includes child tool calls in time order, as stock Canvas would export
   S1's events; a nested export is a later feature (§10 item 3).
8. **A failed dr-acp sub-agent shows as done**, with its answer `Failed: …` (D1 §3 item 5). ACP has no failure stop
   reason and C1 reads no `_meta.deep_reasoner`.
9. **Visual indentation stops at depth 6.** Deeper rows keep nesting in the DOM and show their depth; the chat
   column does not shrink to nothing. *(v3: built, `MAX_INDENTED_DEPTH` in `subagent-labels.ts`; not pinned by a
   test.)*
10. **The spec's falsifier "a 50-child fan-out makes the chat unusable"** becomes E6's measurable null: over 1 s from
    a scheduled scroll to the next painted frame, with every child expanded, while the fan-out streams (§6.3).
    *(v3: measured at 138.6 ms at `9d75806`, on the load §3.2 B10 describes.)*

### 3.2 Changed by the build (v3)

Each was checked against the code at `9d75806` and folded into the sections named. B1 to B3 follow S1's contract and
upstream's agent-server as built; B4 to B8 are files and interfaces; B9 to B14 the tests, the live tier and the
branch; B15 the size; B16 and B17 come from C1's as-built document (`as_built/c1-nested-subagent-sessions.md` at
deep-reasoning `d16d3df`). Where the build recorded no reason (in a commit message, a code comment or PR #4's
description), the reason given is marked as this design's reading. C1's Implementer reported B1 to B3, B6, B7, B10,
B11 and B14, and parts of B4, B8 and B9; the rest were found by reading the commits against v2.

**Against S1's contract and upstream's agent-server**

- **B1. A refused Stop shows the agent-server's own reason, read by status** (`67e3cdb`; §4.7, A.7). v2: the error
  toast shows `getApiErrorMessage(error, fallback)`. That helper returns a body's `message` or `detail`, else the
  error's own message, so for the agent-server's 5xx, whose handler always sets `detail` to "Internal Server Error"
  and puts `"<status>: <reason>"` under `exception` (`openhands-agent-server/openhands/agent_server/api.py:701–704` at
  the SDK fork's `cef3b24`), it would toast the placeholder. Built: `refusalReason` in `use-cancel-acp-session.ts:24`
  reads a 4xx's `detail` verbatim (the 409's sentence, S1 §5 rule 6) and a 5xx's `exception` without its status
  prefix (`/^\d{3}: /`, so a 504 reads "ACP server did not accept the cancel for n2 within 2s."); any other failure,
  an SDK error without such a body or a network failure, shows `SUBAGENTS$STOP_FAILED`, "Could not stop the
  sub-agent." The mutation sets `meta: { disableToast: true }` (`:65`), so upstream's global mutation toast does not
  show a second one. *Why* (the commit): "toasts the agent-server's reason on a refusal: a 4xx's `detail` (the 409's
  sentence verbatim), or for a 5xx the reason its error handler moves under `exception`"; the code comment names the
  handler. S1's contract decides the 409; the 5xx format is upstream's (C2's §3.2 B2 found the same). C2's Gate B
  ruling 3 asks how C2's option picker words the same 5xx; whichever Michael picks there, C1's Stop shows the bare
  reason, and aligning the two is one line in either feature. *Pinned by:* `block.test › … › Stop › shows the
  server's reason when a cancel is refused: %s` [a 409 with its detail, a 504 whose reason the agent-server moves
  under exception, a failure without a body]; `src/api/event-service/event-service.api.test.ts › EventService ›
  cancelAcpSession › rejects with the server's refusal as the client raised it`.
- **B2. No Stop for an idle child whose last snapshot still says `cancellable: true`** (`b76b7ad`, `67e3cdb`; §4.7).
  Not a change: §4.7's Stop table and decision I already gave an idle child no control. S1's v2 made the case
  concrete after C1's v2: a reconnect snapshot is written only for a child that was active, so an idle child's last
  snapshot may still carry the grant (S1 §5 rule 7's note); and dr-acp keeps `cancel` on idle children, so on the
  live connection the route sends `session/cancel` and answers 200 for a no-op (S1 §5.1, E-3), and after a reconnect
  it answers 409. Stop would do nothing either way, so `canStopSubagent` and `isStopWithheld`
  (`subagent-status.ts:98–106`) read the state before the grant. *Why* (the commit): "It is absent for an idle child
  even when its last snapshot still says `cancellable` (dr-acp keeps the grant; the route then answers 409)". By
  S1's E-3 the live route answers 200 there; the conclusion is the same. *Pinned by:* `status.test › Stop › %s,
  cancellable %s, from the %s: Stop %s, withheld %s` [`idle`, `true`, `agent`: neither]; `block.test › … › Stop ›
  offers Stop only for a running child that granted cancel` (`n4`, idle with the grant: no control).
- **B3. `SubagentStatus.lastKnown`** (`b76b7ad`; §4.7, A.5). v2's status table shows an unconfirmed child whose last
  confirmed state was active as "the last state with 'last known'", but A.5 had no field to carry that state while
  the category is `unconfirmed`. Built: `lastKnown: SubagentStatusCategory | null` (`subagent-status.ts:27`), the
  last confirmed active state's category (`running` or `waiting`) for an unconfirmed child, else null; `statusLabel`
  renders it as "running · last known". *Why* (the code comment): "For an unconfirmed child whose last confirmed
  state was active, that state's category ("running · last known"); null otherwise." *Pinned by:* `status.test ›
  getSubagentStatus › keeps a last confirmed %s state as the last known one after a reconnect` [running,
  requires_action]; `block.test › … › shows the last known state without a spinner after a reconnect`.

**Files and interfaces**

- **B4. Four files §4.1 did not list** (§4.1). `src/components/conversation-events/chat/subagents/subagent-labels.ts`
  (80 lines: `statusLabel`, `summaryLabel`, `MAX_INDENTED_DEPTH` and the three plural keys, shared by the block, the
  row and the unplaced groups); `__tests__/helpers/english-translations.ts` (21: a `t` that renders the real English
  strings, plurals and interpolation included, which the block tests use to assert the text a user reads);
  `__tests__/helpers/subagent-events.ts` (157: the fixture builder §6 named, missing from §4.1's table); one line in
  upstream's e2e guide (`.agents/skills/e2e-testing/references/guide.md`) on how the scripted-agent specs run. *Why:*
  for the English helper, the code comment: "so a test can assert the text a user reads. The suite's default mock
  returns bare keys"; for the labels the code says only "Plural keys: `_one` and `_other` exist in translation.json,
  not the base", and that the block and the row both format statuses, so the formatting has one home, is this
  design's reading; for the guide line, this design's reading: the guide lists every mock-LLM suite and how it runs.
- **B5. Smaller interface changes** (`b76b7ad`, `08fb2cc`; §4.3, §4.6, §4.7, §4.8, §4.10, A.3 to A.6). Each is
  additive or local. A reason is quoted where the build recorded one; otherwise it is this design's reading.
  - *An ACP card sits in the root's flow where its call started.* `interleaveSubagentAnchors` takes a third, optional
    argument, `startOf`, and `Messages` passes one that reads an ACP call's `firstAt` from the index
    (`messages.tsx:121–126`). `uiEvents` replaces a call's started event with its terminal one in place, so v2's "an
    item's start is its first event's timestamp" would date a root card by its end, and a child anchored during the
    call would land above it. *Why* (the code comment): "A call's item starts when the call did, not when its
    terminal event replaced it." Not pinned by a test.
  - `renderKeyOf` returns `string | undefined`: Canvas's event types make `id` optional, and React takes either.
  - New exports the modules share: `compareTimestamps` from `subagent-index.ts` ("ISO timestamps in one format order
    as strings; never by locale"), `NO_SUBAGENT_ANCHORS` from `subagent-placement.ts` (one shared empty list),
    `EMPTY_SUBAGENT_SUMMARY` from `subagent-status.ts`, `nestedIndentClass` from `subagent-block.tsx` (the
    transcript indents with it) and the type `ItemStart` from `main-flow-anchors.ts`.
  - The placement is also recomputed when a child's last *confirmed* state or stop reason changes
    (`placementFieldsOf`, `subagent-index.ts:241`): a stale child's category in its cell's summary is read from it.
  - `formatSubagentCost` with a cost and no currency shows the bare amount (`0.0004`).
  - A 32nd key, `SUBAGENTS$STATUS_OTHER` ("other"), names the summary's count of agent-specific states ("1 other");
    32 keys in 15 languages are the 544 lines. The `" · "` separator is a named constant in `subagent-labels.ts`, and
    no `eslint-disable` was needed.
  - `SubagentHistoryContext.Provider` wraps `Messages`, not the whole scroll container (`chat-interface.tsx`, the
    `Messages` render); `Messages` and what it renders are the only readers.
  - Found by the as-built document (§2.2, §2.3 D-10): a known child without a title is named by its session id in
    "To/From …"; any item that opens a transcript marks the placement dirty, not only a text run of an unannounced
    session, and placement then recomputes and finds nothing new; the block's toggle also carries a `title` ("Show
    sub-agents" / "Hide sub-agents"); and the `// @spec` tags in implementation code are SUB-004's and SUB-008's
    only, though every id is tagged in a test, where §4.11 asked for both.
- **B6. The ✓ and ■ marks, and their test ids** (`dee08db`; §2, §4.6, §4.7, §4.12; the Gate B section's ruling 2).
  v2's §2 and §4.7 drew a finished child as ✓ done and a stopped one as ■ stopped, while §4.6 said the card keeps
  "today's success mark". The first build (`08fb2cc`) showed the words alone. `dee08db` adds lucide's `Check` beside
  "done" and `Square` beside "stopped", inside the row's toggle (`subagent-row.tsx:83–96`), with the test ids
  `subagent-done-icon` and `subagent-stopped-icon`; every other state keeps its word alone, and only `running` spins
  (the block and the row reuse upstream's `spinner-icon` id). At this base upstream's tool-call cards show no success
  mark: the wrapper computes a result (`getACPToolCallResult`) but `SuccessIndicator` draws a clock for a timeout and
  nothing else (`success-indicator.tsx:8–18`), so v2's sentence in §4.6 was wrong. Upstream's status lists do mark
  "done": the task tracker's finished task (`task-tracking/task-item.tsx:28–29`) and a completed goal
  (`goal-status-content.tsx:151–154`) each get a check-circle. *Why* (the commit): "A sub-agent row showed a
  spinner while its child ran and only a word once it ended. A child that finished now shows a check beside "done",
  and one that was stopped a square beside "stopped"; every other state keeps its label alone, and an unconfirmed
  state still never spins." That the two test ids stay out of §4.12 and SUB-011 is this design's reading: nothing
  but C1's own Vitest reads them. *Pinned by:* `block.test › … › marks a %s / %s child with %s beside its status`
  [running: the spinner; idle/end_turn: the check; idle/cancelled: the square; requires_action and idle/max_tokens:
  none].
- **B7. The withheld-Stop tooltip opens beside its button** (`e49d19a`; §4.7). `StyledTooltip placement="left"`
  (`stop-subagent-button.tsx:74`). *Why* (the commit): "The reason a sub-agent cannot be stopped opened above its
  button, over the Stop of the row above, until the pointer left. It now opens beside the button. Found by the
  end-to-end run, where it blocked that Stop." *Pinned by:* Live 3, which hovers `child-y`'s withheld Stop, reads the
  tooltip, moves away and clicks the Stop of `child-x`, the row above.
- **B8. Each transcript entry re-renders alone, and the ACP merge compares the id first** (`9c23e8d`; §4.5, §4.6,
  §5, decision B). v2 memoized rows and named cards as memoized. Built: a transcript's task, calls, messages and text
  runs are each a memoized component that selects its own record (`SubagentTask`, `TranscriptToolCall`,
  `TranscriptMessage`, `TranscriptText`, `subagent-transcript.tsx:58–145`), so a child's new event re-renders its
  list and the entry it changed; `handleEventForUI` compares `tool_call_id` before the session
  (`handle-event-for-ui.ts:298`) instead of building a key per event. *Why* (the commit): "so a child's new event
  re-renders its transcript list and the entry it changed, not every card and Markdown block of the child. The ACP
  merge in handleEventForUI compares a call's id before its session instead of building a key per event." *Pinned
  by:* no test counts renders; E6 (Live 6) measures the result, and `handle-event-for-ui.test.ts › … › keeps ACP
  tool calls of different sessions apart` pins the merge.

**Tests, the live tier and the branch**

- **B9. The tests, as built** (§6.1, §6.2). Every file v2 named exists. The differences:
  - Renamed, the property sharpened: `places a child in the tool call that spawned it, in announcement order`;
    `builds the same index from a page in any order, each event once`; `shows the last known state without a
    spinner after a reconnect` (it still asserts no Stop); `shows the server's reason when a cancel is refused: %s`
    (three cases, B1); `rejects with the server's refusal as the client raised it` (v2: `… rejects with the
    server's detail on 409`); `nests sub-agents in a shared conversation, read-only`.
  - Folded: v2's `renders root ACP tool calls as before` is an assertion inside `hides tool calls made inside a
    sub-agent session` (a call with `acp_session_id: null` renders), beside upstream's five existing
    `shouldRenderEvent - ACPToolCallEvent` cases, whose calls carry no session, and `messages.test › … › renders
    agents without sub-agent sessions as before`; the new `leaves sub-agent snapshots, messages and text to the
    sub-agent tree` pins the three kinds' absence from the root's flow. *Why:* none recorded; this design's reading:
    one assertion and upstream's cases already cover the root's path.
  - Added beyond v2's tables: the thirteen tests and two tables mutation testing asked for (`09da5a1`, B13); `takes
    the agent's own report of a child call over the failure stored when the root's turn was aborted` (`ed8a7fc`: S1
    stores one synthetic `failed` for every open call when the root's turn is aborted, S1 §5.1's E-1); `marks a %s /
    %s child with %s beside its status` (`dee08db`, B6); and from the first build `counts a child's own calls and
    takes its answer from its newest message outside its children`, `recomputes the summary when a child's state
    changes` and the two `anchorsForParent` tests.
  - Faked at another boundary than v2 said: the two `cancelAcpSession` tests fake the typed client's
    `ConversationClient` (as the file's `respondToConfirmation` tests already do), not the route through MSW; the
    two backfill tests spy `EventService.searchEvents` under the real `useLoadOlderEvents` and assert each older
    page's `timestampLt`, not MSW's requests. The shared-view test reads the index its `Messages` stand-in receives,
    not rendered rows. *Why:* none recorded; this design's reading: each follows its file's existing fakes, and each
    still fakes a service, not the hook under test.
  - Counts: 74 Vitest test definitions (8 of them `it.each` tables), 106 cases once the tables expand, in 12 test
    files, 4 of them new, plus two helpers (as-built §6.5 counts the same 106); in Playwright, 5 tests in the main
    spec and one per named transcript in the replay spec. The Gate B section maps each to its
    property.
- **B10. E6's load is §5's** (`5b89471`; §5, §6.3; the Gate B section's ruling 3). v2's §5 names the load case: per
  child an announcement, a task, ~5 text runs, 10 call events, an answer, an idle snapshot and cost snapshots, about
  1,100 events. The first build's `writeFanoutTranscript` sent no child text and one cost report per child: 753
  stored events. `5b89471` starts each of a child's five cells with a thought and ends it with a cumulative
  `usage_update` cost: 1,203 events, a thinking block per cell in every expanded child, a cost snapshot per cell.
  *Why* (the commit): "the load case the design names: about 1,200 updates at 60 per second, a thinking block per
  cell in every expanded child, and a cost snapshot per cell." The reading of §5 is the Implementer's; E6 is
  Michael's falsifier, so he confirms it. Measured: 1,203 events in 19.7 s, worst scroll 138.6 ms at `9d75806`;
  149.8 and 101.3 ms at `5b89471` and `09da5a1`; on the old load, 70.2 and 323.5 ms at `15f66c5` and `ed8a7fc`.
  *Pinned by:* Live 6.
- **B11. CI's smoke replay plays one transcript** (`85e9899`; §6.3; the Gate B section's ruling 4). v2: "In the
  fork's CI it plays C1's three transcripts and the generated fan-out's file as a smoke check." Built: the workflow
  step that fetches the scripted agent also writes
  `OH_ACP_REPLAY_TRANSCRIPTS=…/fixtures/acp-subagents/fallback-placement.jsonl` into `GITHUB_ENV`
  (`mock-llm-e2e.yml:104`). There are two hand-written transcripts, not three; the fan-out is the third, generated.
  *Why:* none recorded (the commit and the e2e guide state it, not why). This design's reading: `nested-stop.jsonl`'s
  client `session/cancel` line is a wait point only a press of Stop answers, so replayed, the scripted agent exits
  non-zero at its default 30 s `--wait-timeout` (`tests/fixtures/acp/scripted_agent.py:100` at `cef3b24`) and the
  turn never ends; the fan-out exists only inside E6's test, in a temporary directory. Because the step writes the
  variable into the job's environment, a dispatch cannot name other transcripts without editing the workflow; D5's
  `canvas-replay` job runs Playwright with its own environment (§6.4) and is unaffected. *Pinned by:* Live 1.
- **B12. The end-to-end helpers and specs, as built** (`85e9899`, `15f66c5`, `1135e87`, `98a43ab`; §6.3, A.9).
  - `readRenderedSubagentTree` reads a row inside the could-not-be-placed block as a child of the missing parent its
    group names (`data-missing-parent-session-id`, `acp-subagents.ts:231–246`), so an orphan compares equal to its
    stored parent; v2's reading (the nearest row, else the root) would have read `null` against the stored `ghost`.
  - The scroll probe counts a scroll still waiting for its frame when the run ends, and reports `scrolls`; E6
    asserts more than ten. *Why* (`15f66c5`): "so a main thread starved for the whole run reads as the worst latency,
    not as a run without scrolls".
  - E6 waits for "50 sub-agents · 50 done" before comparing the trees; the check that the root's answer holds no
    child text moved from test 1 to test 3, after the turn has ended.
  - The Stop test opens the block with a pointer click. *Why* (`15f66c5`): "hover tooltips open only once the page
    has seen pointer input".
  - The replay spec sets the mock LLM profile once, through the API, before any transcript plays. *Why* (`1135e87`):
    "editing the profile the second time timed out on a loaded machine before any replay ran".
  - Helper exports beyond A.9, which the two specs share: `SCRIPTED_ACP_PROFILE`, `deleteScriptedAcpAgent`,
    `startConversation`, `readStoredEvents` and `waitForTurnsToEnd`.
  - Both specs skip under the Docker config unconditionally; v2's `SCRIPTED_ACP_AGENT_CONTAINER` does not exist
    (§10 item 5).
  - `child-o`, announced on the unknown session `ghost`, is shown apart end to end: S1 stores such an announcement
    under that session's id (S1 §5.1, E-4), so v2's fallback, "covered by Vitest only", was not needed.
  - `98a43ab` tags the helpers' test-id selectors with `@spec SUB-011`.

  *Why*, where not quoted: this design's reading; the tree comparison needs the orphan's parent, and the specs need
  the shared helpers.
- **B13. Mutation testing ran on the three pure modules, not on the diff** (`09da5a1`; §6.5, §6.6; the Gate B
  section's evidence). v2: `npm run test:mutation:diff` (Stryker on the diff); a survivor in the three pure modules
  gets a test, and survivors in components are reviewed and killed or named in the as-built document. Built: Stryker
  on `subagent-index.ts`, `subagent-placement.ts` and `subagent-status.ts`, each against its own suite, with
  Stryker's command runner because its Vitest runner (upstream's `stryker.config.mjs`) is unreliable in this repo;
  599 mutants, 134 alive before `09da5a1`, 64 after (77.6% to 89.3% killed), most of them equivalent, two real but
  contrived ones left untested. The components were not mutated, so no component survivor was reviewed. *Why*
  (the commit): "The behaviours behind the ones that change what Canvas shows now have tests". The scope, the runner,
  the 64 and the two survivors are not in any commit, code comment or PR #4's description: they are the
  Implementer's report, and this design could not check them against a committed configuration or log. *Pinned by:*
  the thirteen tests and two tables of `09da5a1` (B9).
- **B14. Sixteen commits, on `wiring/dr-1`** (§7, §6.6). v2: six commits, each green on its own and cherry-pickable
  onto `main`, with a draft PR against the fork's `main`. Built: the six planned (`3f0fea8`, `b76b7ad`, `08fb2cc`,
  `67e3cdb`, `81d810e`, `85e9899`), then ten that follow from the live tier, review and mutation testing: a fix
  (`e49d19a`, B7), a performance change (`9c23e8d`, B8), the marks (`dee08db`, B6), test changes (`15f66c5`,
  `1135e87`, `ed8a7fc`, `98a43ab`, `5b89471`, `09da5a1`) and the typecheck fix to one of them (`9d75806`). PR #4 is
  against `wiring/dr-1`, as C2's PR #3 is. *Why* (PR #4's description): "Base is `wiring/dr-1`: the fork's C3 plus the
  dr-1 wiring (agent-server and TypeScript client from the SDK fork's tag dr-1, which carries S1)." CI ran on pushed
  heads only: green at `85e9899`, `1135e87`, `ed8a7fc`, `98a43ab`, `5b89471` and `9d75806`; red at `09da5a1` (lint);
  cancelled at `81d810e` and `15f66c5`. That each planned commit is green on its own is not shown; the PR split,
  after Gate B, re-cuts the stack and owns it. That the ten were not folded into the six is this design's reading:
  each answers a run that came after them, and Gate C's split re-cuts them anyway.

**Size**

- **B15. Size** (§3.1 item 6; the Gate B section's ruling 1). `git diff --numstat 9881d24..9d75806`: 5,647 lines
  added and 44 removed, in 51 files; 5,150 of the added lines are not blank. The sixteen commits add 5,689 between
  them, because later commits rewrote lines earlier ones added.

  | Part | Spec | v2 | Built, added (removed) |
  |---|---|---|---|
  | Production TypeScript (`src/`, not tests or translations) | ≈1.2k with tests, in all | ≈1.4k | 2,069 (28) |
  | Vitest tests and their helpers | | ≈1.0k | 1,953 (16) |
  | Playwright specs, helpers and transcripts | | ≈0.6k | 1,012 |
  | Translations | — | ≈530 (31 keys × 15 languages) | 544 (32 × 15) |
  | Upstream's `specs/` file; the workflow step; the e2e guide | — | 50; 15; — | 47; 21; 1 |
  | **Total** | **≈1.2k, ≈4 h at Gate C** | **≈3.5k, ≈8 h** | **5,647 (44): 13.6 h at v2's 375 lines an hour, 17 h at ≈300 (18.8 h with the translations)** |

  Where the lines are, against §4.1's estimates:
  - `subagent-index.ts`, 502 against 230: about 180 lines are A.3's own keys, interfaces and empty index with their
    JSDoc, which v2's figure did not count; the copy-on-write draft (`writableMap`, `Draft`) about 60; the fold
    itself, `ownTranscript` and `placeItem` through `buildSubagentIndex`, about 245.
  - `subagent-placement.ts`, 241 against 150: the structural-sharing helpers (`reuseList`, `reuseMap`, `reuseLists`,
    `sameAnchor`, `samePending`, `sameSummary`) are about 60.
  - `subagent-transcript.tsx`, 202 against 110: four memoized entry components (B8).
  - `subagent-labels.ts`, 80, unplanned (B4); `stop-subagent-button.tsx`, 103 against 70, and
    `use-cancel-acp-session.ts`, 67 against 35 (the withheld variant and B1's reading); `messages.tsx`, +75 against
    +35 (B5's `startOf` and the anchors); `subagent-status.ts`, 138 against 70.
  - Vitest: `subagent-index.test.ts` 666, of which 238 are `09da5a1`'s; `subagent-block.test.tsx` 411; the fixture
    builder 157; `chat-interface.test.tsx` +132; `subagent-status.test.ts` 166; `messages-subagents.test.tsx` 168.
  - Playwright: the helpers, 511 against 220 (the fan-out writer about 130, the scroll probe about 80, the two tree
    readers and the expander about 115, the profile, conversation and stored-event helpers about 120); the main spec
    361 against 200; the replay spec 92 against 50; the transcripts 48 against 150.

  The build recorded no reason for the growth. This design's reading: v2 costed the fold but not the surface A.3
  declares, costed structural sharing and per-entry memoization as free, and costed E6's tests before the fan-out
  writer and the probe had a shape; the tests are twice v2's because mutation testing added 238 lines and each
  component test seeds the real store with whole runs, as §6.2 asked. The Implementer counted +5,650, Vitest 1,956
  and 13–14 h; the numbers here are the diff's at `9d75806`, and the 13–14 h is v2's own rate. The Scout and the
  Refactorer, after Gate B, are where it shrinks: the duplicated JSDoc on A.3's surface, the structural-sharing
  helpers and the four entry components are where to look first.

**Found by the as-built document** (`d16d3df`)

- **B16. A child spawned inside an unplaced child is shown apart too, under a block that calls its shown parent
  missing** (as-built §2.1 D-2; §4.4; the Gate B section's ruling 5). v2's §4.4 rule 1: a child is pending on
  `parent-session` when its parent "is neither the root nor a known child", or its ancestry loops. Built,
  `hasPlaceableAncestry` (`subagent-placement.ts:40–54`, called at `:147–156`) walks the child's whole chain up to
  the root and fails at any unknown ancestor, recording the child's own parent as `missingId`. With `child-o`
  announced on `ghost`, a session the conversation never announced, and `child-p` spawned in `child-o`'s loaded call
  `co1`, v2 places `child-p` in `byCell[(child-o, co1)]`, under `child-o`'s row; the build makes `child-p` pending,
  and once history is complete `UnplacedSubagents` shows two blocks, `ghost: [child-o]` and `child-o: [child-p]`,
  the second reading "1 sub-agent could not be placed: its parent session child-o is not in this conversation."
  while `child-o` is on screen above it. *Why:* none recorded; this design's reading: the loop guard was written as
  a reachability walk, which also rejects an unknown ancestor. The design stands; the code diverges. *Pinned by:*
  nothing (the only ancestry test is the loop, `index.test › foldSubagentEvents › refuses to recurse into a parent
  loop`); the Cartographer's probe test, uncommitted, shows it. The fix the ruling recommends: that probe as a fold
  test and a `Messages` test, then a walk that fails only on an unknown direct parent or on returning to a session
  already seen.
- **B17. Three behaviours a user sees, which the code gets right and no test pins** (as-built §6.4, probes C5, C7,
  C9; the Gate B section's ruling 6).
  - *C5.* `TranscriptMessage` renders nothing for a message the child sent to one of its own children
    (`subagent-transcript.tsx:94–133`): that is the grandchild's task, shown inside the grandchild. A mutant that drops
    the check passes all 23 block and messages tests, since none expands a child that has a child of its own and reads
    its messages; the live tier compares tree shape only.
  - *C7.* The root's flow dates an ACP call by its call's `firstAt` (B5). A mutant restoring v2's rule passes the
    messages tests, which never anchor a child between a call's start and its completion; the live tier's fallback
    order is the same under both rules (as-built §2.1 D-6).
  - *C9.* The bottom-following effect depends on `subagents.version` (§4.8 item 3). A mutant that drops it passes
    every test: none checks that a chat pinned to the bottom follows sub-agent content that grows without new root
    items. Upstream's `chat-interface.test.tsx › ChatInterface - Auto-scroll on submit (issue #817) › follows the live
    goal banner into view when an active goal advances` pins the same kind of growth for the goal banner, with the
    scroll geometry stubbed; a C1 case can copy it.

  The probes' other two survivors need nothing: I3 (the latest state dropped from the placement-dirty fields) is
  equivalent for every snapshot S1 writes, and S1 (Stop offered when `cancellable` is absent) is unreachable through
  dr-1, which always stores the field (as-built §6.4).

---

## 4 · Modules and seams

### 4.1 Files

| Path (Canvas fork) | | ≈ lines | Built (v3) | What |
|---|---|---|---|---|
| `src/types/agent-server/core/events/acp-subagent-event.ts` | new | 110 | 99 | The three kinds, as Canvas types (A.1). |
| `src/types/agent-server/core/events/acp-tool-call-event.ts` | changed | +10 | +9 | `acp_session_id`, `meta`. |
| `src/types/agent-server/core/events/index.ts`, `core/openhands-event.ts` | changed | +5 | +8 | Export; join the `OpenHandsEvent` union. |
| `src/types/agent-server/type-guards.ts` | changed | +25 | +26 | Four guards (A.2). |
| `src/utils/subagents/subagent-index.ts` | new | 230 | 502 | Keys, records, `foldSubagentEvents`, `buildSubagentIndex` (§4.3, A.3). |
| `src/utils/subagents/subagent-placement.ts` | new | 150 | 241 | `placeSubagents`, `anchorsForParent`, `unplacedGroups` (§4.4, A.4). |
| `src/utils/subagents/subagent-status.ts` | new | 70 | 138 | Status categories, Stop rules, cost format, summaries (§4.7, A.5). |
| `src/stores/use-event-store.ts` | changed | +25 | +18 −3 | `subagents`, folded in `appendEvent` and `addEvents`, reset in both clears (A.8). |
| `src/utils/handle-event-for-ui.ts` | changed | +5 | +5 −1 | ACP merge key `(session, tool_call_id)`. |
| `src/components/conversation-events/chat/event-content-helpers/should-render-event.ts` | changed | +5 | +5 −1 | Hide child-session calls. |
| `src/components/conversation-events/chat/event-message.tsx` | changed | +3 | +6 −6 | ACP branch renders `AcpToolCallCell`. |
| `src/components/conversation-events/chat/messages.tsx` | changed | +35 | +75 −4 | `renderKeyOf`; root anchors interleaved; `UnplacedSubagents` at the end. |
| `src/components/conversation-events/chat/subagents/subagent-source.ts` | new | 45 | 56 | Source and history contexts, `useSubagents`, `useStaticSubagentSource` (A.6). |
| `src/components/conversation-events/chat/subagents/main-flow-anchors.ts` | new | 35 | 55 | `interleaveSubagentAnchors`. |
| `src/components/conversation-events/chat/subagents/acp-tool-call-cell.tsx` | new | 35 | 29 | Today's card plus `SubagentBlock`. |
| `src/components/conversation-events/chat/subagents/subagent-block.tsx` | new | 90 | 85 | Summary line, toggle, rows. |
| `src/components/conversation-events/chat/subagents/subagent-row.tsx` | new | 120 | 130 | One child's header and, expanded, its transcript. |
| `src/components/conversation-events/chat/subagents/subagent-transcript.tsx` | new | 110 | 202 | Task, entries, anchored grandchildren. |
| `src/components/conversation-events/chat/subagents/subagent-labels.ts` | *(v3)* new | — | 80 | Status and summary labels, the depth limit, the plural keys (§3.2 B4). |
| `src/components/conversation-events/chat/subagents/stop-subagent-button.tsx` | new | 70 | 103 | Stop, Stopping…, withheld. |
| `src/components/conversation-events/chat/subagents/unplaced-subagents.tsx` | new | 45 | 40 | "could not be placed", apart. |
| `src/components/features/chat/chat-interface.tsx` | changed | +35 | +42 −6 | History context, backfill, scroll-follow (§4.8). |
| `src/routes/shared-conversation.tsx` | changed | +10 | +16 −4 | Its own read-only source and history flag. |
| `src/components/features/chat/typing-indicator.tsx` | changed | +8 | +6 −2 | Resolve ACP calls by call key. |
| `src/utils/transcript-export/index.ts` | changed | +3 | +3 −1 | Keep exporting child calls (§4.5). |
| `src/api/event-service/event-service.api.ts` | changed | +20 | +23 | `cancelAcpSession` (A.7). |
| `src/hooks/mutation/use-cancel-acp-session.ts` | new | 35 | 67 | The mutation and its refusal text (A.7, §3.2 B1). |
| `src/i18n/translation.json` | changed | ≈+530 | +544 | 31 keys × 15 languages (§4.10); built, 32 (§3.2 B5). |
| `specs/acp-subagent-sessions.md` | new | 50 | 47 | Upstream's spec IDs `SUB-001`…`SUB-011` (§4.11). |
| `__tests__/…`, `src/**/*.test.ts` | new/changed | 1,000 | 1,953 −16 | §6.1–§6.2; as built, the Gate B section and §3.2 B9. Includes the helpers `__tests__/helpers/subagent-events.ts` (157) and *(v3)* `english-translations.ts` (21). |
| `tests/e2e/mock-llm/conversations/mock-llm-acp-subagents.spec.ts` | new | 200 | 361 | §6.3. |
| `tests/e2e/mock-llm/conversations/mock-llm-acp-replay.spec.ts` | new | 50 | 92 | §6.3–§6.4: any transcripts named by `OH_ACP_REPLAY_TRANSCRIPTS`. |
| `tests/e2e/mock-llm/utils/acp-subagents.ts` | new | 220 | 511 | Shared helpers (A.9), reused by D5 (*(v3)* C2 runs its own mock agent and does not use them, §8). |
| `tests/e2e/mock-llm/fixtures/acp-subagents/*.jsonl` | new | 150 | 48 | Three hand-written transcripts (§6.3); built, two: `nested-stop.jsonl` and `fallback-placement.jsonl` (the fan-out is generated). |
| `.github/workflows/mock-llm-e2e.yml` | changed | +15 | +21 | Fetch the scripted agent from the pinned SDK (§6.3); name the smoke replay's transcript (§3.2 B11). |
| `.agents/skills/e2e-testing/references/guide.md` | *(v3)* changed | — | +1 | How the scripted-agent specs run (§3.2 B4). |

*(v3)* The built column is `git diff --numstat 9881d24..9d75806`; the total is 5,647 added and 44 removed (§3.2 B15).

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

*(v3)* Built as written, with three refinements (§3.2 B5): the placement is also recomputed when a child's last
confirmed state or stop reason changes, because a stale child's category in its cell's summary is read from it
(`placementFieldsOf`, `subagent-index.ts:241`); `stats.answerKey` is recomputed for each session whose transcript
gained a message, and for the parent of each child whose placement fields changed (a new child turns its parent's
message into a task), as the newest message the session sent in its transcript's order; and timestamps compare
through the exported `compareTimestamps`, as strings, never by locale.

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

*(v3)* Built as written. A parent with no anchored children reads one shared empty list, `NO_SUBAGENT_ANCHORS`
(§3.2 B5). Through the real agent-server, a child announced on a session the conversation never announced is stored
under that session's id and shown apart (Live 5; S1 §5.1, E-4). Rule 1 diverges: the build also sets apart a child
whose *direct* parent is loaded but whose ancestry reaches an unknown session further up, so a child spawned inside
an unplaced child gets a second could-not-be-placed block that names its shown parent as missing. This section's rule
stands; the code is to follow it, test first, if Michael so rules (§3.2 B16, the Gate B section's ruling 5).

### 4.5 The store and every consumer of ACP events

- **`use-event-store.ts`**: `EventState.subagents: SubagentIndex`, initially `EMPTY_SUBAGENT_INDEX`. `appendEvent`
  (`:113–132`) folds `[event]` after the dedupe; `addEvents` (`:162–195`) folds the batch's new events once, after
  the loop; `clearEvents` and `clearEventsForConversation` (`:196–209`) reset it. `sortEventState` does not touch it:
  the index orders by timestamp itself. Streaming slots never reach it (they are not events).
- **`handle-event-for-ui.ts:291–303`**: the ACP merge compares `toolCallKey(uiEvent.acp_session_id,
  uiEvent.tool_call_id)` with the incoming event's. *(v3: it compares `tool_call_id` first and then the session, so
  no key is built per event, §3.2 B8.)*
- **`should-render-event.ts:139–141`**: `return !isSubagentToolCallEvent(event)`. The three new kinds already fall
  to the final `return false`.
- **`typing-indicator.tsx:70–122`** (`deriveLiveActivity`): ACP calls are resolved and looked up by call key in a
  set of their own, so a finished child call can never mask a running root call with the same id. A running child
  call may still be the live activity shown ("Running c = catalog['CS201']…"): it is what is happening.
- **Transcript export** (`transcript-export/index.ts:283–288`): the filter becomes
  `shouldRenderEvent(event) || isSubagentToolCallEvent(event) || …`, so child calls are exported in time order, as
  today with S1's events (§3.1 item 7).
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
the details and the success mark are today's. The data attributes are what the E6 helpers read (§6.3). *(v3: at
this base the card has no success mark: upstream's `SuccessIndicator` draws only a clock, for a timeout, §3.2 B6.)*

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
*(v3: the header reads, in order, the mark (the spinner while running, ✓ when done, ■ when stopped, nothing
otherwise; §3.2 B6), the status word, the title, the depth past 6, the answer and the tool-call count.)*

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

*(v3)* Each entry (the task, a call, a message, a text run) is its own memoized component selecting its own record,
so a child's new event re-renders the list and the entry it changed (§3.2 B8). Items sort before anchors at an equal
`at`. In "To/From {name}", a known child without a title is named by its session id (§3.2 B5).

**The root's flow.** `Messages` selects `placement.byAnchor.get(ROOT_SESSION)` and `placement.pending`, reads
`SubagentHistoryContext`, computes `anchorsForParent(...)` in a `useMemo`, and renders
`interleaveSubagentAnchors(renderedItems, anchors)`: an anchor goes before the first item that starts after it (an
item's start is its first event's timestamp), so a child placed at the root's message to it appears where that
message was sent. After the items, `UnplacedSubagents`. `Messages`' memo comparator is unchanged: the new hook
re-renders it when anchors change, and they change rarely. *(v3: an ACP card's item starts at its call's `firstAt`
from the index, not at its first event's timestamp, which after the started → terminal replacement is the call's end;
`interleaveSubagentAnchors` takes that rule as its optional third argument, §3.2 B5.)*

**Render keys.** `renderKeyOf(event)` is `acp-` plus `toolCallKey(...)` for an ACP call and the event id otherwise;
`Messages` uses it for both keys of a single item (`messages.tsx:85, 104`). Child cards are keyed by call key inside
their transcript. *(v3: `renderKeyOf` returns `string | undefined`, since an event's `id` is optional in Canvas's
types, §3.2 B5.)*

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

*(v3)* Built as the table says. The ✓ and ■ are lucide's `Check` and `Square`, added in `dee08db` after a first build
that showed the words alone (§3.2 B6, for Michael's ruling). "The last state with 'last known'" is carried by a field
A.5 lacked, `SubagentStatus.lastKnown` (§3.2 B3), and reads "running · last known". An agent's own snapshot without a
state, and a reconnect snapshot that still carries one, both read as unconfirmed.

**Cost** (`formatSubagentCost`): `null` or absent → nothing (unknown, not zero, D1 §6.2); `USD` → `$0.0004`
(`toFixed(4)`, the format Canvas uses for costs, `budget-usage-text.tsx:21`, `cost-section.tsx:24`); another
currency → `0.0004 EUR`. Never added (decision J). *(v3: a cost with no currency shows the bare amount, `0.0004`,
§3.2 B5.)*

**Stop** (`StopSubagentButton`, `canStopSubagent`, `isStopWithheld`):

| Latest snapshot | Control |
|---|---|
| `source` agent, state `running` or `requires_action`, `cancellable` | **Stop**, enabled, `aria-label` "Stop {title}" |
| the same, not `cancellable` | Stop, `aria-disabled`, tooltip: "This agent cannot stop a single sub-agent. Stop ends the whole turn." (the spec's sentence) |
| any other (idle, unconfirmed, a reconnect snapshot) | none |
| any, in a read-only view | none |

*(v3)* Built as the table says. An idle child gets no control even when its last snapshot still says `cancellable:
true`, which S1's v2 made possible (§3.2 B2). The withheld variant's tooltip opens to the left of its button, so it
never covers the Stop of the row above (§3.2 B7).

Click → `useCancelAcpSession().mutate({ conversationId, conversationUrl, sessionApiKey, sessionId })`, with the
conversation from `useActiveConversation()`, as `ConversationConfirmationButtons` does. On success the button reads
"Stopping…" and stays disabled for as long as the row stays mounted and the child's state is still running or
waiting; the child's own `idle`/`cancelled` snapshot then removes it. On a refusal the button returns and an error
toast shows the agent-server's reason *(v3, §3.2 B1; v2 named `getApiErrorMessage(error, fallback)`, which shows a
5xx's placeholder `detail`)*: a 4xx's `detail` verbatim (409: "ACP session … does not accept cancel; cancel the
conversation's turn instead."; 404 likewise), a 5xx's `exception` without its status prefix (504: "ACP server did not
accept the cancel for … within 2s."), and otherwise `SUBAGENTS$STOP_FAILED`. The mutation sets `meta: { disableToast:
true }`, so upstream's global mutation toast stays silent, and never touches the index (decision I).

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

*(v3)* Built as written, except that the provider of item 1 wraps `Messages` rather than the whole scroll container
(`Messages` and what it renders are the only readers, §3.2 B5). The backfill effect's dependencies are
`needsOlderHistory`, the failure flag, `hasMoreOlderEvents` and `allConversationEvents.length`. Item 2 is pinned in
Vitest (`chat-interface.test.tsx › ChatInterface - Sub-agent history backfill`, two tests); item 3 is not pinned, and
no live conversation is long enough to need the backfill.

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
i18next/no-literal-string`, as the guide allows. *(v3: built as one block right after `EVENT_GROUP$COLLAPSE`, 32 keys
with `SUBAGENTS$STATUS_OTHER` below; the separator is a named constant in `subagent-labels.ts`, which needs no
`eslint-disable`, §3.2 B5.)*

| Key | English |
|---|---|
| `SUBAGENTS$COUNT_one` / `_other` | `{{count}} sub-agent` / `{{count}} sub-agents` |
| `SUBAGENTS$SUMMARY_PART` | `{{count}} {{status}}` |
| `SUBAGENTS$STATUS_RUNNING`, `_WAITING`, `_DONE`, `_STOPPED`, `_LIMITED`, `_REFUSED`, `_UNCONFIRMED` | `running`, `waiting for action`, `done`, `stopped`, `stopped at a limit`, `refused`, `not confirmed since reconnecting` |
| `SUBAGENTS$STATUS_OTHER` *(v3)* | `other` (the summary's count of agent-specific states) |
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
| `SUBAGENTS$STOP_FAILED` | `Could not stop the sub-agent.` (only when the server gave no `detail`; *v3:* no 4xx `detail` and no 5xx `exception`, §3.2 B1) |
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

*(v3)* Built as listed, 47 lines, every requirement checked; SUB-011 lists §4.12's ids and attributes and not the
marks' `subagent-done-icon` and `subagent-stopped-icon` (§3.2 B6). Every id from SUB-001 to SUB-011 is tagged in at
least one test (the end-to-end helpers' selectors got SUB-011's in `98a43ab`), but implementation code carries tags
for SUB-004 (`should-render-event.ts`) and SUB-008 (`chat-interface.tsx`) only (as-built §2.3 D-10; §3.2 B5).

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

*(v3)* Every id and attribute above is built as listed. Three ids exist outside the contract: the marks'
`subagent-done-icon` and `subagent-stopped-icon` (§3.2 B6; kept or dropped by Michael's ruling, they stay out of
SUB-011 either way), and upstream's own `spinner-icon`, which the block and the row reuse for their spinner.

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

*(v3)* Measured on GitHub's hosted `ubuntu-24.04` runner, with every block and row expanded as it appeared: 1,203 ACP
events in 19.7 s (61.1/s), worst scroll latency 138.6 ms against the 1,000 ms null, no long task (Live 6 at
`9d75806`). Five runs so far range from 70.2 to 323.5 ms (§3.2 B10). Neither remedy above was needed. The generated
load is this section's case since `5b89471`: each child's five cells open with a thought and close with a cumulative
cost report, so a cost snapshot per cell rather than D1's two a second.

---

## 6 · Testing

Upstream's layout and rules (`AGENTS.md`, the e2e-testing skill): Vitest beside its peers under `__tests__/` (or
co-located where the module's tests already are), Arrange–Act–Assert, the underlying service mocked rather than the
hook, existing files extended where natural, each test named for the property it pins, `// @spec SUB-00N` above it.
Upstream's full suite (764 Vitest files, `npm run lint`, `npm run build`, `npm run build:lib`) stays green; no
existing test needs editing, because decision L keeps every path without S1's events byte-identical except render
keys. Fixtures are plain event objects in the shape S1 stores (field names from S1 A.4), built by one helper,
`__tests__/helpers/subagent-events.ts`, so every test reads like the walkthrough in §2.

*(v3)* Built so. C1 adds four Vitest files; at `9d75806` CI ran 769 and skipped one (the Gate B section). Two
existing files changed beyond additions, with no existing assertion changed: the shared-conversation test's `Messages`
stand-in now also reports the sub-agent source and history flag it receives, and `chat-interface.test.tsx`'s Vitest
import line. The tests as built, by property, are in the Gate B section; §6.1 and §6.2 below are v2's plan, and §3.2
B9 lists the differences.

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

*(v3: the two tables above are v2's plan. As built, two tests are renamed, the first build added four (the stats test,
`recomputes the summary when a child's state changes` and two for `anchorsForParent`), `ed8a7fc` one, and mutation
testing thirteen and a table in the index file and a table in the status file; §3.2 B9 and the Gate B section.)*

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

*(v3: the two tables above are v2's plan. As built, several names are sharper, `renders root ACP tool calls as
before` is an assertion inside the hide test, the marks have a test of their own, the refusal test has three
cases, and the event-service and backfill tests fake the typed client and `EventService` rather than MSW; §3.2 B9
lists each, and the Gate B section maps every test to its property.)*

### 6.3 End to end, through the real agent-server (Playwright, mock-LLM suite)

`tests/e2e/mock-llm/conversations/mock-llm-acp-subagents.spec.ts`, in the mock-LLM suite because it is the one that
starts the real stack (`bin/agent-canvas.mjs`: the production build, the agent-server our wiring commit installs,
the ingress) — E6 in the fork, and C1's Gate B live tier (spec §4 layer 5: "D3, C1, C2, C3: through their end-to-end
tests"). The ACP agent is S1's scripted agent (`tests/fixtures/acp/scripted_agent.py`) in `--transcript` mode, so
every state is deterministic, configured through `configureScriptedAcpAgent` (A.9) as an ACP agent profile with
`acp_subagents: true` (which needs §9.1 item 1) and the flags `--transcript <file> --wait-timeout 120`, so a test has
two minutes to press Stop at a wait point. The three tests on `nested-stop` share one conversation, in order
(`test.describe.configure({ mode: "serial" })`, as the existing ACP spec does). *(v3: built so; `--wait-timeout 120`
is passed for `nested-stop.jsonl` only, `--transcript-interval-ms 16` for the fan-out, and neither for
`fallback-placement.jsonl`. Run at `9d75806`: run 37171891707, 6 of 6, the Gate B section.)*

**Getting the scripted agent.** A new step in `.github/workflows/mock-llm-e2e.yml`, before the tests: read
`config/defaults.json`; take `sources.agentServerGitRepo` and `sources.agentServerGitRef` when the wiring commit set
them (C3 §2.1's keys), else `https://github.com/OpenHands/software-agent-sdk` at `v${versions.agentServer}`; fetch
that ref with `--depth 1` into `.tmp/sdk`, sparse to `tests/fixtures/acp`; export
`SCRIPTED_ACP_AGENT=$PWD/.tmp/sdk/tests/fixtures/acp/scripted_agent.py`. It runs with the existing
`.mock-llm-venv` Python, which has `agent-client-protocol` through `openhands-sdk`. The spec skips with a reason
when `SCRIPTED_ACP_AGENT` is unset locally and fails in CI. Under the Docker config it skips unless
`SCRIPTED_ACP_AGENT_CONTAINER` names a mounted copy (§10 item 5). *(v3: built so, except that both specs skip under
the Docker config unconditionally, with no container variable (§3.2 B12), and that the same step writes
`OH_ACP_REPLAY_TRANSCRIPTS` for the smoke replay (B11). At `9d75806` the step fetched `cef3b24` from
`michaeltheologitis/software-agent-sdk`.)*

**Transcripts** (`tests/e2e/mock-llm/fixtures/acp-subagents/`, S1 §4.10's JSONL with client lines as wait points):

| File | Plays |
|---|---|
| `nested-stop.jsonl` | Root cell `cell-1`; children `child-x` (cancel) and `child-y` (no cancel) both running; `child-x`'s cell `cell-x1` spawns `child-z` (cancel); costs on each; then a **wait for `session/cancel` of `child-x`**; then `child-z` and `child-x` idle/cancelled, `cell-x1` failed, `child-y` idle/end_turn with an answer; root completes with an answer. |
| `fallback-placement.jsonl` | `child-m` announced on the root without `parentToolCallId`, with a root task message after a root cell; `child-a` with neither (placed at its announcement); `child-g` naming a call never sent; `child-o` announced on an unknown session `ghost` (could not be placed). The last relies on S1's router registering a child announced on an unannounced session with that session as its parent (S1 §4.3, "the first update for an unknown id announces it"); if S1's implementation drops it instead, this case is covered by Vitest only and the as-built document says so. |
| generated at test time by `writeFanoutTranscript` | one root cell, 50 children × 5 cells each, interleaved as concurrent children are, costs and idles, about 1,100 updates. |

*(v3)* `fallback-placement.jsonl`'s last case holds end to end: S1 stores `child-o` under `ghost`, and C1 shows it
apart (Live 5; §3.2 B12). Since `5b89471` each generated cell opens with a thought and closes with a cumulative cost
report, 1,203 stored events (§3.2 B10).

**Tests** (serial, each a `test.step` sequence, every assertion on behaviour):

| Test | Asserts |
|---|---|
| `nests each sub-agent under the call that spawned it` | `nested-stop`: after `expandAllSubagents`, `readRenderedSubagentTree(page)` equals `readStoredSubagentTree(request, id)`; the summary reads "2 sub-agents · 2 running" while waiting; `child-x` shows `$0.0004`; no `child-*` card is in the root's flow; the root's answer contains no child text |
| `stops one sub-agent and its branch` | Stop on `child-y` is disabled and its tooltip is the spec's sentence; Stop on `child-x` is enabled; clicking posts `…/acp/sessions/child-x/cancel` (`page.waitForRequest`); `child-x` and `child-z` turn "stopped", `cell-x1` turns failed, Stop disappears; `child-y` turns done |
| `shows the same tree after reloading` | reload: the tree from REST equals the stored tree; no enabled Stop anywhere |
| `places sub-agents without a spawning call and shows orphans apart` | `fallback-placement`: `child-m` sits after the root cell, where the task was sent; `child-a` at its announcement; `child-g` at its announcement once history is complete; `child-o` in the "could not be placed" block naming `ghost`, never in the root's flow |
| `stays responsive while 50 sub-agents with 5 tool calls each stream in` | the generated fan-out, paced at 60 events/s (§9.1 item 2); every child expanded as it appears; `probeScrollResponsiveness` until the root completes: `maxScrollLatencyMs < 1000` (E6's null) and the rendered tree equals the stored one |

*(v3)* As built (§3.2 B12; the Gate B section has each test's assertions as run): the tests are plain sequences,
not `test.step`s; the check that the root's answer holds no child text is in the reload test, after the turn has
ended, with the answer's presence; the reload test also reads "2 sub-agents · 1 done · 1 stopped"; the Stop test
opens the block with a pointer click, which hover tooltips wait for, and checks that the tooltip goes when the pointer
leaves; the fallback test reads the root's whole flow in document order; E6 also asserts more than ten scrolls and
"50 sub-agents · 50 done" before comparing the trees.

**The replay spec**, `tests/e2e/mock-llm/conversations/mock-llm-acp-replay.spec.ts` (D5 §8.4's ask): one test per
path in `OH_ACP_REPLAY_TRANSCRIPTS` (paths separated by the platform's path delimiter; the spec is skipped when the
variable is unset or empty), named after the file. Each configures the scripted agent with `--transcript <path>`
and `acp_subagents: true`, sends one message, waits for the turn to end, expands everything, and asserts that
`readRenderedSubagentTree(page)` equals `readStoredSubagentTree(request, id)`: the same children, the same parent
sessions, the same spawning calls, the same tool calls per child. In the fork's CI it plays C1's three transcripts
and the generated fan-out's file as a smoke check; D5 points it at D1's recordings (§6.4). *(v3: CI plays
`fallback-placement.jsonl` alone, §3.2 B11, for Michael's ruling; the spec sets the mock LLM profile once, through
the API, before any transcript, B12.)*

`readRenderedSubagentTree` reads nesting only: a row's parent is its nearest enclosing `subagent-row` (or the root),
its call the nearest enclosing `acp-tool-call` inside that parent, its own calls the `acp-tool-call`s whose nearest
enclosing row is it. A row's own attributes are never compared with themselves. `readStoredSubagentTree` keeps the
newest `ACPSubagentEvent` per child and the `ACPToolCallEvent`s per session from the events search route, and nulls
a `parentToolCallId` that names no stored call, which is exactly S1 §5 rule 2's placement. *(v3: a row inside the
could-not-be-placed block reads as a child of the missing parent its block names, so an orphan compares equal to
its stored parent, §3.2 B12.)*

`probeScrollResponsiveness` schedules a scroll of the chat container every 250 ms and measures, for each, the time
from when it was due to the next animation frame after it ran, so main-thread blocking counts; it also records long
tasks with a `PerformanceObserver`, as the markdown performance test does. No screenshot is evidence; Playwright's
own failure screenshots and videos stay as debugging artifacts. *(v3: a scroll still waiting for its frame when the
run ends counts, as the time it has waited, and the result also reports how many scrolls ran, §3.2 B12.)*

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

*(v3)* `1135e87`'s message reports that "All ten of D1's dr-acp golden recordings replayed through the dr-1
agent-server render as stored". No CI run of that exists to open; it is D5's `canvas-replay` job's to run (§9.4).
The fork's workflow writes `OH_ACP_REPLAY_TRANSCRIPTS` itself, so this job's own environment is what names D1's
recordings, as above (§3.2 B11).

### 6.5 Mutation testing and upstream's guards

`npm run test:mutation:diff` (Stryker on the diff) runs on the branch; a surviving mutant in `subagent-index.ts`,
`subagent-placement.ts` or `subagent-status.ts` is a missing test and gets one. Survivors in components are reviewed
and either killed or named in the as-built document.

*(v3)* Stryker ran on the three pure modules, each against its own suite, with Stryker's command runner, since its
Vitest runner is unreliable in this repo: 599 mutants, 134 alive before `09da5a1` and 64 after (77.6% to 89.3%
killed), most of the rest equivalent, two real but contrived ones left untested. The components were not mutated
(§3.2 B13). Upstream's other guards ran as §7 says (the Gate B section).

### 6.6 What each layer of the spec maps to

| Spec §4 layer | C1's part |
|---|---|
| 1 · deterministic, every push | §6.1–§6.2 (Vitest, in `npm test`) |
| 2 · contract and golden replays | §6.4, run by D5 |
| 3 · inside the fork | §6.1–§6.3 in upstream's folders; upstream's suite; the draft PR against the fork's `main` (§7); Stryker on the diff. *(v3: PR #4 against `wiring/dr-1`, CI run 37171885463 green; Stryker on the three pure modules, §3.2 B13, B14.)* |
| 4 · the desktop app, end to end | D5's flow "see the nested tree" uses C1's helpers |
| 5 · Gate B's live tier | §6.3, run on demand (`workflow_dispatch` of `mock-llm-e2e.yml` on the branch) at the branch's head. *(v3: with the `specs` input naming C1's two specs; run 37171891707 at `9d75806`, 6 of 6.)* |

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

*(v3)* Built: the six as planned, with these titles and contents, as `3f0fea8`, `b76b7ad`, `08fb2cc`, `67e3cdb`,
`81d810e` and `85e9899` (the first also creates `subagent-index.ts` with `toolCallKey`, and the third holds the
strings and `subagent-labels.ts`), on `wiring/dr-1` rather than `deep-reasoning`; then ten more, through `9d75806`
(§3.2 B14). CI ran on pushed heads only, so that each planned commit is green on its own is not shown; the PR split
owns it.

**Upstream's guards** (spec §4 layer 3): the branch, cherry-picked onto the fork's `main`, gets a draft PR there that
is never merged, and runs upstream's CI as upstream would: `npm run lint` (typecheck, ESLint including the i18n and
query-key rules, Prettier), `npm test`, `npm run build`, `npm run build:lib`, `npm pack --dry-run`; the PR
description check; and, by dispatch, the mock-LLM end-to-end workflow. Upstream's PR would additionally need a
released `@openhands/typescript-client` with S1's additions (its guide: release the client first, then bump), so
upstream review waits for S1's server and client; in our fork the wiring tarball provides both. The PR description
uses upstream's template and leaves its `HUMAN:` section to Michael. No issue or pull request is opened on any
upstream repository. *(v3: the draft is PR #4, against `wiring/dr-1`, not cherry-picked onto `main`; its CI and the
mock-LLM dispatch are the Gate B section's runs. The PR description check did not run: the workflow is disabled in
the fork. The description uses upstream's template and leaves `HUMAN:` empty. §3.2 B14.)*

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

*(v3)* As built, both PRs stand on `wiring/dr-1` (C1's PR #4 at `9d75806`; C2's PR #3 at its Gate B head `64b5a8b`,
since moved by C2's Refactorer, to `f4c7ae5` when this was written). They share nine files: those of rows
1, 2, 3, 5 and 6 (`events/index.ts`, `openhands-event.ts`, `type-guards.ts`, `translation.json`, `event-service.api.ts`
and its test), row 4's test file, the transcript export's test and upstream's e2e guide. A trial merge of
`9d75806` with each of those C2 heads (`git merge-tree`, nothing written; the as-built's §4.7 found the same)
conflicts in one file only, `events/index.ts`: both add an export on its first line, row 1's case, resolved by keeping
both, alphabetical. Everything else merges cleanly. C2 touches neither `chat-interface.tsx` nor `use-event-store.ts`
(rows 7 and 8). Rows 9 and 10 did not happen: C2's end-to-end runs its own mock agent (`mock-acp-server.py
--session-controls`), so C1 alone created the scripted-agent helpers and the workflow step, and C2 touches neither. No
test id is shared (row 15). Both features read a 5xx's reason from `exception`, each with its own code (as-built §2.1
D-1): C1's `refusalReason` (§3.2 B1), C2's `getSdkHttpServerErrorReason` at `64b5a8b`; the PR split or the Refactorers
may make it one helper, whichever lands second.

---

## 9 · What C1 relies on, and what S1 must change

*(v3)* **What C1's code relies on at `9d75806`**, each pinned where it says, for the Conductor's Expectations once C1
merges:

1. **S1, at the SDK fork's tag `dr-1` (`cef3b24`), which `wiring/dr-1`'s `sources` installs.** The persisted
   contract (S1 §5 rules 1 to 9: the tree, placement, a child's transcript, state, cost, Stop, freshness, the root);
   rule 10's ordering, which decision C's "latest" and the backfill's criterion read (a child's timestamps never
   decrease in log order, a reconnect snapshot is later than its child's earlier events, a spawning call's started
   event precedes its whole subtree); the cancel route and its statuses (S1 §5.1 guarantee 6); `acp_subagents` on
   `ACPAgentProfile`, which `configureScriptedAcpAgent` saves and reads back (guarantee 8); and the scripted agent's
   `--transcript`, `--transcript-interval-ms` and `--wait-timeout` flags (guarantee 9;
   `tests/fixtures/acp/scripted_agent.py:706–708` at `cef3b24`), which the workflow fetches by path from the same
   commit. S1 is being cut into a stack of pull requests now; its transcript player stays upstream-shaped on a level
   of its own, so the flags C1's specs pass survive the split. Moving the pin is the Conductor's.
2. **The `dr-1` TypeScript client** (`@openhands/typescript-client` 1.50.1 from the `dr-1` release tarball):
   `ConversationClient.cancelAcpSession(conversationId, sessionId)` and the type `CancelAcpSessionResponse`
   (`dist/client/conversation-client.d.ts:125`, `dist/events/types.d.ts:174`), which `EventService.cancelAcpSession`
   calls.
3. **Upstream's 5xx format in the agent-server**: `{"detail": "Internal Server Error", "exception": "<status>:
   <reason>"}` (`openhands-agent-server/openhands/agent_server/api.py:701–704` at `cef3b24`). §3.2 B1's refusal text
   reads the `exception` key and strips the `"<status>: "` prefix; a change to either would fall back to "Could not
   stop the sub-agent."

What C1 shares with C2, which lands on the same `wiring/dr-1` (§8): one line conflicts, each branch's new export at
the top of `src/types/agent-server/core/events/index.ts`, kept both, alphabetical (§8 row 1; as-built §4.7); and the
5xx rule above exists twice, C1's `refusalReason` and C2's own helper (as-built §2.1 D-1), so a change to the
agent-server's format reaches both.

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

*(v3: all four are built in S1 at its v2.2 build, which `dr-1` carries: item 1 as guarantee 8, with the persisted
profile fixture of `a3279be`; item 2 as `--transcript-interval-ms`, which E6 passes as 16 ms; item 3 as S1 §5 rule 10;
item 4 as S1's B3, a reconnect snapshot only for a child that was active.)*

### 9.2 D1

Nothing must change. C1 relies on D1 §5 as S1 stores it: children announced before their traffic, with
`_meta.openhands.parentToolCallId` naming a call already sent (§5.4 rules 1–2), `cancel` on every child, a Stop
acknowledgement as a thought on the child's session, `Failed: …` as a failed child's answer (D1 §3 item 5), and `Run …`
cell titles (D1 §3 item 3). C1 never parses the flat fallback's `#1 › #3` titles: with the opt-in off, dr-acp's flat
stream renders as stock Canvas renders it.

### 9.3 The wiring commit (spec Q2 (a)) and C3

C1's branch needs, before its first commit builds: `package.json` pointing `@openhands/typescript-client` at a
tarball built from an SDK fork ref that contains S1's commit 5 (`ConversationClient.cancelAcpSession`,
`CancelAcpSessionResponse`, `ACP_SETTINGS_KEYS` with `acp_subagents`), and `config/defaults.json`'s `sources`
(C3 §2.1) naming that SDK fork ref, so the mock-LLM stack runs S1's agent-server and the workflow step can fetch the
scripted agent from the same ref. C3 lands first and the wiring commit follows (spec C3); C1 is cut after both.
*(v3: done as the fork's `wiring/dr-1` at `9881d24`, which C1 is cut from; the client is the `dr-1` release tarball
and `sources` names `cef3b24`.)*

### 9.4 D5

D5's setup writes `acp_subagents: true` on the dr-acp **agent profile** it makes the default (which needs §9.1 item
1), not only in `agent_settings`. D5's `canvas-replay` job runs §6.4's replay spec with `OH_ACP_REPLAY_TRANSCRIPTS`
(D5 §8.4's name, adopted). D5's E12 ("they appear nested under their cell, each with its state and cost, and one is
stopped with its branch") selects through §4.12's test ids and can reuse `expandAllSubagents` and
`readRenderedSubagentTree` from A.9 over CDP. *(v3: the replay spec as built reads the variable from the job's
environment; the fork's own workflow sets it to one transcript, §3.2 B11, which does not reach D5's job. `1135e87`
reports D1's ten recordings rendering as stored through `dr-1`; D5's job is where that becomes evidence, §6.4.)*

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
   they can run, so C1's commit 6 lands after it. *(v3: closed; S1 built it, and commit 6, `85e9899`, runs on it.)*
2. **E6's threshold in CI.** One second of scroll latency with all 50 children expanded is generous for a desktop,
   unmeasured on a 2-vCPU runner. If it fails there, §5's remedies apply before any threshold changes; a changed
   threshold goes back to Michael, since E6 is his. *(v3: measured on GitHub's hosted runner: 70.2 to 323.5 ms over
   five runs, 138.6 ms at `9d75806`; the threshold stands. The load E6 measures is for Michael to confirm, the Gate B
   section's ruling 3.)*
3. **A nested transcript export** (§3.1 item 7): child calls are exported flat, in time order. A nested export would
   reuse `buildSubagentIndex`; not in v1.
4. **A race the backfill inherits:** a live event that lands while an older page is in flight restores the saved
   scroll geometry early (`chat-interface.tsx:418–431` already has this with root events). The backfill makes it more
   likely during a live fan-out; the visible effect is one small jump. Fixing it would mean restoring by anchor
   element instead of by height delta, a change to upstream's scroll code outside C1.
5. **Docker mock-LLM config:** the spec skips there unless the scripted agent is mounted
   (`SCRIPTED_ACP_AGENT_CONTAINER`). Upstream may want the mount added to `playwright.mock-llm-docker.config.ts`;
   v1 ships the desktop app, so C1 does not add it. *(v3: as built both specs skip under the Docker config whatever
   is mounted; there is no `SCRIPTED_ACP_AGENT_CONTAINER`, §3.2 B12. Adding the mount would add the variable too.)*
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
Implementer's; excerpts of existing files show only what C1 adds. *(v3: the blocks now match the build at `9d75806`;
every line v3 added or changed carries `// v3:` and the §3.2 item behind it, and the blocks were typechecked again
under `strict`, against the built code's own types where a block imports them.)*

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

// v3: exported; placement, the anchors and the transcript order by it (B5).
/** ISO timestamps in one format order as strings; never by locale. */
export declare function compareTimestamps(a: string, b: string): number;

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

// v3: added (B5).
/** What a parent with no anchored children renders; one shared reference. */
export declare const NO_SUBAGENT_ANCHORS: readonly SubagentAnchor[];

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
  // v3: added; A.5 had no field for the last known state (B3).
  /**
   * For an unconfirmed child whose last confirmed state was active, that
   * state's category ("running · last known"); null otherwise.
   */
  lastKnown: SubagentStatusCategory | null;
}

export declare function getSubagentStatus(
  record: SubagentRecord,
): SubagentStatus;

/** Running or waiting, confirmed on the live connection, with `cancel`. */
export declare function canStopSubagent(record: SubagentRecord): boolean;

/** Running or waiting, confirmed, without `cancel`: Stop shown disabled. */
export declare function isStopWithheld(record: SubagentRecord): boolean;

// v3: without a currency, the bare amount, `0.0004` (B5).
/** `$0.0004` for USD (Canvas's own format), `0.0004 EUR` otherwise. */
export declare function formatSubagentCost(
  cost: number | null | undefined,
  currency: string | null | undefined,
): string | null;

// v3: added (B5).
export declare const EMPTY_SUBAGENT_SUMMARY: SubagentSummary;

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

// v3: exported; the transcript indents with it too (B5).
/** Nested sub-agent content is indented under a rule, down to a limit. */
export declare function nestedIndentClass(depth: number): string;

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

// v3: added; `Messages` dates an ACP call by its call's `firstAt` (B5).
/** When an item starts: its first event's timestamp, unless told otherwise. */
export type ItemStart = (event: OpenHandsEvent) => string | undefined;

/**
 * Put each anchored root-level child before the first rendered item that
 * starts after its anchor; items keep their order. Returns `items` itself
 * when `anchors` is empty.
 */
export declare function interleaveSubagentAnchors(
  items: readonly RenderedItem[],
  anchors: readonly SubagentAnchor[],
  // v3: added, optional; defaults to the first event's timestamp (B5).
  startOf?: ItemStart,
): readonly MainFlowItem[];

// messages.tsx (excerpt)
// v3: `string | undefined`; an event's `id` is optional in Canvas's types (B5).
/** Stable across an ACP call's started → terminal replacement. */
export declare function renderKeyOf(event: OpenHandsEvent): string | undefined;
```

```typescript
// subagent-labels.ts (v3: a file v2 did not list, B4)
import type { TFunction } from "i18next";
import type { SubagentSummary } from "#/utils/subagents/subagent-index";
import type { SubagentStatus } from "#/utils/subagents/subagent-status";

/** Plural keys: `_one` and `_other` exist in translation.json, not the base. */
export declare const SUBAGENT_COUNT_I18N_KEY: "SUBAGENTS$COUNT";
export declare const SUBAGENT_TOOL_CALLS_I18N_KEY: "SUBAGENTS$TOOL_CALLS";
export declare const SUBAGENTS_UNPLACED_I18N_KEY: "SUBAGENTS$UNPLACED";

/** Visual indentation stops here; deeper rows show their depth instead. */
export declare const MAX_INDENTED_DEPTH: 6;

/** "running", "running · last known", or an agent's own state as reported. */
export declare function statusLabel(
  t: TFunction<"openhands">,
  status: SubagentStatus,
): string;

/** "3 sub-agents · 2 done · 1 running". Costs are never on it (never added). */
export declare function summaryLabel(
  t: TFunction<"openhands">,
  summary: SubagentSummary,
): string;
```

### A.7 Stop: the service method and the mutation

```typescript
// src/api/event-service/event-service.api.ts
import type { CancelAcpSessionResponse } from "@openhands/typescript-client";

// Excerpt: the new static method beside respondToConfirmation.
export declare class EventService {
  // v3: the comment names the 504.
  /**
   * Ask the agent-server to send ACP `session/cancel` for one sub-agent
   * session (S1's route). Goes to the conversation's runtime host with its
   * session key, as respondToConfirmation does, so local and Cloud runtimes
   * take the same path. Rejects with the client's HttpError: 409 when the
   * child holds no live `cancel` grant, 404 when it is unknown, 504 when the
   * agent did not take it in time.
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

// v3: the refusal text is read by status (B1).
/**
 * Cancel one ACP sub-agent session. Success means only that the request was
 * sent: the row shows "Stopping…" until the child's own idle/cancelled
 * snapshot arrives. A refusal shows the server's reason in an error toast: a
 * 4xx's `detail`; a 5xx's `exception` without its "<status>: " prefix, since
 * the agent-server's 5xx handler sets `detail` to "Internal Server Error".
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

*(v3: shared with D5; C2 runs its own mock agent and does not import it, §8.)*

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

// v3: the four helpers below are added; both specs use them (B12).
/** The agent profile the scripted agent runs as. */
export declare const SCRIPTED_ACP_PROFILE: "scripted-acp-subagents";

/** Remove the scripted agent's profile; the caller re-activates its own. */
export declare function deleteScriptedAcpAgent(
  request: APIRequestContext,
): Promise<void>;

/** Start a conversation from the home page with the active agent profile. */
export declare function startConversation(
  page: Page,
  message: string,
): Promise<string>;

/** The fields the helpers read from a stored event (not exported). */
interface StoredEvent {
  kind?: string;
  timestamp: string;
  acp_session_id?: string | null;
  parent_session_id?: string | null;
  parent_tool_call_id?: string | null;
  tool_call_id?: string;
  state?: string | null;
  action?: { kind?: string };
}

/** Every stored event of the conversation, in log order, from the REST route. */
export declare function readStoredEvents(
  request: APIRequestContext,
  conversationId: string,
): Promise<StoredEvent[]>;

/** Wait until the conversation's turns have ended (one FinishAction each). */
export declare function waitForTurnsToEnd(
  request: APIRequestContext,
  conversationId: string,
  options?: {
    /** How many turns must have ended; default 1. */
    turns?: number;
    /** Milliseconds to wait; default 120 000. */
    timeout?: number;
  },
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

// v3: a row in the could-not-be-placed block reads its block's missing parent (B12).
/**
 * The tree as the DOM nests it: each row's parent is its nearest enclosing
 * row (or the root; or, apart, the missing parent its group names), its tool
 * call the nearest enclosing ACP cell inside that parent, and its own calls
 * the ACP cells whose nearest enclosing row is it. Reads nesting only, never
 * a row's own claims.
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

// v3: each cell is a thought, a call and a cumulative cost report (B10).
/**
 * Write an agent-outgoing JSONL transcript (S1 §4.10's format) of one root
 * cell fanning out to `children` sub-agents with `cellsPerChild` cells each,
 * each cell a thought, a call and a cost report, interleaved as concurrent
 * children are; returns the file's path.
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
  // v3: added; E6 asserts more than ten (B12).
  /** How many scrolls the probe made. */
  scrolls: number;
}

/** Scroll the chat every 250 ms until `stop` resolves; report the worst. */
export declare function probeScrollResponsiveness(
  page: Page,
  stop: Promise<void>,
): Promise<ScrollProbeResult>;
```
