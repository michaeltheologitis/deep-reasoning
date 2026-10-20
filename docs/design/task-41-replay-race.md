# TASK-41 · The replay spec reads once — design

**TASK-41** · System Designer · design branch `design/task-41` in
[deep-reasoning](https://github.com/michaeltheologitis/deep-reasoning), cut from `main` at `9e8109e`; this file is
the only change on it · code lands in the Canvas fork
[michaeltheologitis/OpenHands](https://github.com/michaeltheologitis/OpenHands) on `fix/replay-spec-settles`, cut
from tag `dr-3`, and ships in tag `dr-4` with the UX round · **no spec**: Michael, 2026-10-19, "Do them without the
spec go with what you recommend". Every decision below is that recommendation.

**Pinned against:** Canvas fork `dr-3` `4355a36` (every Canvas `file:line`) · SDK fork `dr-2` `34c540c`, the
agent-server the Canvas stack runs (`config/defaults.json` `sources`) · deep-reasoning `main` `9e8109e` ·
`@playwright/test` 1.63.0 (`package.json:133`).

**Revisions** (newest first):
- 2026-10-19 · v1 · first version.

**Where this file lives, and why nothing trips over it.** `docs/design/task-41-replay-race.md`. At `9e8109e`
pytest collects `tests/` only (`testpaths`), ruff excludes `docs` (`extend-exclude`), the sdist excludes `docs/`, and
the wheel packages only `src/deep_reasoning`. No Canvas pull request carries it.

**Reading guide.** Gate B: §0 and §1 (what failed and why), §2 (decisions), about 6 minutes. The Implementer:
everything; §3 is the change, §4 the two guard tests, §5 the proof.

---

## 0 · Findings for the Conductor (read first)

1. **Four failures, not two, in three shapes.** The task row names two; the runs since show two more, both
   `exhausted.native.jsonl`, with an empty rendered tree (§1.3). From the first `canvas-replay` run (2026-10-04) to
   today: **4 failed of 33 attempts** (about 1 in 8, not 1 in 5), about **1.3 % of test executions** (4 of ≈309).

   | Run (attempt) | Date | Recording | What failed | Cause |
   |---|---|---|---|---|
   | 37234595801 (1) | 10-04 | `fork` | `events search: 502` inside `waitForTurnsToEnd` | §1.1 |
   | 37240441432 (1) | 10-04 | `fanout20` | n16, n17 rendered with `toolCallIds: []` | §1.2 |
   | 37259740259 (1) | 10-05 | `exhausted` | rendered `[]`, stored n2 with 3 calls | §1.3 |
   | 38523531844 (1) | 10-14 nightly | `exhausted` | the same | §1.3 |

2. **"The turn ended" does not mean "the store is final".** The pinned agent-server can still be storing a turn's
   sub-agent events after the turn's `FinishAction` (§1.2). This fix waits it out. Whether the agent-server should
   drain them before the `FinishAction` is an SDK-fork question, not TASK-41's. Any client that reads the store at a
   turn's end sees a partial tree for about a second.
3. **The same race sits in the sibling spec**, `mock-llm-acp-subagents.spec.ts`, so §3.3 edits it. That file is
   also edited by `fix/subagent-costs-on-by-default` (already in `ux-round-integration`), which gives one trivial
   conflict in its import list (§7). §3.3 is separable: drop it to keep TASK-41 inside the replay spec and its
   helpers.
4. **The 502 is the ingress's own** (§1.1). It answers an unlogged 502 when its socket to the agent-server fails
   with an error it classes as benign. The browser's requests go through the same ingress. That is a product
   question, not this task's.

## 1 · The causes, as the runs show them

### 1.1 One 502 ends a 120 s wait (37234595801, `fork.native.jsonl`)

The stack: `readStoredEvents` (`utils/acp-subagents.ts:186`) ← the `expect.poll` callback ← `waitForTurnsToEnd`
(`:203`) ← the spec (`mock-llm-acp-replay.spec.ts:74`), 8 s into the test.

- **The 502 is the ingress's.** `BACKEND_URL` is the stack's ingress (`playwright.mock-llm.config.ts`), which writes
  502 only when its own request to the agent-server errors (`scripts/proxy-utils.mjs:57, 107, 163, 199`). The
  agent-server's events route never answers 502. The ingress logs every error to stderr except ECONNRESET,
  EPIPE, ECONNABORTED and ERR_STREAM_PREMATURE_CLOSE (`proxy-utils.mjs:7–12`). Playwright pipes the stack's stderr
  into the job log, and no such line appears there. So the error was one of those four; the logs do not say which
  one or why.
- **Why one 502 failed the test.** Playwright 1.63's `expect.poll` awaits its callback outside its `try`
  (`lib/matchers/expect.js:13391`). A throw from the callback therefore ends the poll at once, and only a matcher
  failure is retried. `readStoredEvents` turns every non-ok status into a throw with a hard `expect`. Reproduced in
  scratch: a callback answering 502 then 200 stops after one call with `events search: 502`.

### 1.2 Rows without their calls (37240441432 attempt 1, `fanout20.native.jsonl`)

The evidence:
- **The diff:** only n16 and n17 differ; each has one call stored and none rendered.
- **The failure screenshot, taken after both reads:** the root's final answer is on screen, but children C17
  (n19) and C19 (n21) still show "running · 0 tool calls".
- **The video's last frame, about a second later:** every child is done, with one call each.

The mechanism:
- **Root and sub-agent events are stored on different paths.** In the pinned agent-server, the root session's
  events are stored inline, on the ACP thread. A sub-agent's events (`ACPSubagentEvent`, a child's
  `ACPToolCallEvent`) go instead to `LocalConversation._emit_event_from_any_thread`. That is a one-worker
  `ThreadPoolExecutor` which takes the state lock for each event and stores them in order
  (`local_conversation.py:322, 1578, 1881–1890, 1957–1960`; `acp_agent.py:1626–1641, 1880–1904`). Under `arun()`,
  the lock is not held across the ACP prompt (`acp_agent.py:4557–4572`).
- **So the store lags.** A replayed recording arrives as a burst, and the worker falls behind it. The root's
  `FinishAction`, which `waitForTurnsToEnd` counts, can be stored while child events are still queued.
- **The test read the two trees at two points of that drain.** The chat only ever gains calls. n19 and n21 were
  therefore empty in the rendered read, and because they compared equal, the stored read lacked their calls too:
  the store itself was incomplete after the `FinishAction`. Between the two reads, the store gained n16's and n17's
  calls; the chat had not yet.
- **The expansion was not the cause.** n16 and n17 were rendered and expanded; their calls had not arrived.

### 1.3 The page had not loaded (37259740259 attempt 1, 38523531844; `exhausted.native.jsonl`)

**The evidence.** Both runs show the same thing:
- **The diff:** the rendered tree is `[]`; the stored tree holds n2 with three calls.
- **Both screenshots:** skeleton placeholders, and the composer reads "Connecting".
- **The video:** about 6 s on the home page while the conversation is created, then the conversation page opens
  about 1 s before the failure.

**The mechanism.**
- **The turn beat the page.** This short recording's turn ended within about a second of the conversation page
  opening, before the page had loaded any events.
- **`waitForTurnsToEnd` reads REST only**, so it returned without waiting for the page.
- **`expandAllSubagents` passed vacuously.** Its poll found no collapsed toggle, because nothing had rendered, and
  passed at once (`:242–256`). The rendered tree was empty.

### 1.4 What the three share

The spec waits for a signal, the stored `FinishAction`, that says nothing about the page. Nor does it say that the
store holds every sub-agent event. The spec then reads each side once. Both sides converge within about a second
(the videos). So the fix is to:
- poll the comparison;
- read both sides on every poll;
- treat the stored tree as final only once it holds still between two polls;
- retry the one status the ingress answers for a dropped upstream connection.

## 2 · Decisions

- **D1 · The polling form.** `await expect(async () => { … }).toPass({ timeout, intervals: [1_000] })` around
  expand, read rendered, read stored and compare.
  - **Why not `expect.poll`:** it matches one moving value against a fixed expected value, and it does not retry
    a throw (§1.1). Here both sides move.
  - **The message on timeout:** `toPass` reports the last iteration's `toEqual` diff verbatim, then
    `Call Log: - Timeout 30000ms exceeded while waiting on the predicate`.
  - **The bound:** it fails no later than its timeout, because it skips any interval that would cross the
    deadline (Playwright 1.63, `expect.js:12974–12998`; reproduced in scratch).
- **D2 · Settled means two things:** the rendered tree equals the stored tree, *and* the stored tree equals the
  previous poll's.
  - **Why the second condition:** without it, a poll can pass on a half-stored tree (§1.2). With polls 1 s apart,
    a pass on a partial tree needs the worker to store no tree change for a full second mid-drain. That residual
    risk is named in §5; it weakens one execution, and it can never fail a correct one.
  - **Rejected: a "drained" marker.** The agent-server emits none: nothing is submitted to the worker after a
    turn's last child event (`acp_agent.py:4085, 5101–5117`).
  - **Rejected: counting all stored events.** That would also wait on events the tree does not contain.
- **D3 · Every poll expands again** (`expandAllSubagents`). A row that renders collapsed after the first poll is
  opened then, whether it arrived late (§1.3) or is a child announced late in the drain.
- **D4 · Deadline and interval.** The deadline is 30 s per comparison, the same as `expandAllSubagents`'s own poll;
  the interval is 1 s. Within the replay test's 180 s, that leaves up to 120 s for the turn plus 30 s for the
  comparison. A passing comparison costs at least one interval, about 1 s per test.
- **D5 · What counts as transient: HTTP 502 on the events search, and nothing else.**
  - **The budget:** up to 2 retries, 500 ms apart, so about 1 s per page.
  - **What still fails at once, with today's message `events search: <status>`:** the third consecutive 502, any
    other non-ok status, and a request that throws (thrown errors are not retried).
  - **Why only 502:** it is the only status the ingress emits for a failed upstream request. A 503 from the
    agent-server means it is not initialised, and nothing in this stack answers 504. Retrying either would hide a
    real failure.
  - **Visibility:** every retry writes one `console.warn` line, so a tolerated 502 is counted (§5), never silent.
- **D6 · Where each part lives.**
  - **The retry lives in `readStoredEvents`.** That way `waitForTurnsToEnd`'s poll, both tree reads, and the
    sibling's polls all get it.
  - **The settle loop is one helper** that every rendered-vs-stored comparison in the family calls: one in the
    replay spec, three in the sibling.
- **D7 · Kept unchanged:**
  - **The names D5 relies on** (C1 design §9.4): `OH_ACP_REPLAY_TRANSCRIPTS`, the replay spec's path, SUB-011's ids,
    `expandAllSubagents`, `readRenderedSubagentTree` and `readStoredSubagentTree`, with their signatures and
    behaviour.
  - **The test titles,** "nests X as the agent-server stored it", which `cross-repo.yml`'s verdict matches.
  - **Every failure message.**

## 3 · The change

### 3.1 `tests/e2e/mock-llm/utils/acp-subagents.ts`

```ts
/** The status the stack's ingress answers when its request to the agent-server fails (scripts/proxy-utils.mjs). */
const TRANSIENT_STATUSES: ReadonlySet<number> = new Set([502]);

export interface RetryTransientOptions {
  /** Further attempts after the first; default 2. */
  retries?: number;
  /** Wait before each further attempt; default 500. */
  delayMs?: number;
}

/**
 * Call `send` again, `delayMs` apart, while it answers a transient status, at
 * most `retries` more times; returns the last response, ok or not. Each retry
 * writes one `console.warn` line: `transient <status>; retry <n> of <retries>`.
 */
export async function retryTransient<R extends { status(): number }>(
  send: () => Promise<R>,
  options?: RetryTransientOptions,
): Promise<R>;

// Unchanged signature. Each page's GET goes through retryTransient; the line
// `expect(response.ok(), `events search: ${response.status()}`).toBe(true)` stays as it is.
export async function readStoredEvents(
  request: APIRequestContext,
  conversationId: string,
): Promise<StoredEvent[]>;

export interface TreeMatchOptions {
  /** How long the two trees may take to settle and agree; default 30_000. */
  timeout?: number;
}

/**
 * Expand every sub-agent and compare the rendered tree with the stored one,
 * once a second, until they are equal and the stored tree equals the previous
 * poll's; fails at `timeout` with the last comparison's diff. Returns the
 * stored tree it settled on.
 */
export async function expectRenderedTreeToMatchStored(
  page: Page,
  request: APIRequestContext,
  conversationId: string,
  options?: TreeMatchOptions,
): Promise<readonly SubagentLink[]>;
```

One poll, in this order. The first poll is exactly the spec's single read today, which §5 relies on.

1. `await expandAllSubagents(page)`.
2. `rendered = await readRenderedSubagentTree(page)`.
3. `stored = await readStoredSubagentTree(request, conversationId)`. Keep the previous poll's value, then store
   this one as the new previous.
4. `expect(rendered).toEqual(stored)`: the message a real mismatch fails with.
5. `expect(stored, "the agent-server was still storing the sub-agent tree").toEqual(previous)`: on the first poll
   there is no previous value, so this fails by construction.

Once it passes, it adds one annotation through `test.info()`:
`{ type: "subagent-tree", description: "settled after <n> polls; first read <matched|differed>" }`.

### 3.2 `tests/e2e/mock-llm/conversations/mock-llm-acp-replay.spec.ts`

- `:76–87` becomes `const stored = await expectRenderedTreeToMatchStored(page, request, conversationId);`,
  followed by the existing `SUBAGENT_UPDATE` check, run on `stored`. Its message is unchanged.
- Imports: drop `expandAllSubagents`, `readRenderedSubagentTree` and `readStoredSubagentTree`. Add the helper,
  `retryTransient`, `writeFanoutTranscript`, and `mkdtemp`, `tmpdir` and `join`.
- The two guard tests of §4 go in the same `describe`, **declared before the per-transcript loop**.

### 3.3 `tests/e2e/mock-llm/conversations/mock-llm-acp-subagents.spec.ts` (separable)

- `:129–133` and `:231–235` become `await expectRenderedTreeToMatchStored(page, request, conversationId);`.
- `:354–357` becomes `const stored = await expectRenderedTreeToMatchStored(page, request, id);` followed by
  `expect(stored).toHaveLength(50);`.
- Imports: add the helper; drop `readRenderedSubagentTree`, which is then unused.

### 3.4 `.agents/skills/e2e-testing/references/guide.md`

The fork's `AGENTS.md` says to "update the owning skill whenever an invariant changes". Append one sentence to the
"Scripted ACP agent" bullet:

> The two trees are compared by polling, through `expectRenderedTreeToMatchStored`, until they agree and the stored
> tree holds still. The agent-server may still be storing a turn's sub-agent events after its `FinishAction`, and
> the page may still be loading. Never compare them with a single read.

### 3.5 Not changed

- deep-reasoning's `cross-repo.yml`, which picks the fix up when `desktop/pins.toml` moves to `dr-4`.
- `waitForTurnsToEnd`.
- The recordings and fixtures.
- The agent-server, and every line of product code.

## 4 · The guards: a real failure still fails

Both go in the replay spec. Its `describe` is serial, so a failing guard skips the ten recordings. That matters
because `cross-repo.yml`'s verdict (`:152–164`) counts only the "nests … as" tests: without this ordering, a failing
guard would not fail D5's job.

**G1 · `fails a rendered tree the agent-server did not store, with the tree diff, within its deadline`** proves that
polling cannot hide a mismatch.
- **Arrange.** Write a fan-out with `writeFanoutTranscript(await mkdtemp(...), { children: 1, cellsPerChild: 1 })`.
  Then `runs.start`, `waitForTurnsToEnd`, and run `expectRenderedTreeToMatchStored` until it passes.
- **Act.** In the page, set the `data-acp-tool-call-id` of the `fanout-1-c1` cell to `not-stored`. This is a call
  the chat nests but the store does not have, which is what a mis-render looks like. React leaves the attribute
  alone, since no prop changes. Then call the helper with `{ timeout: 5_000 }`, catch its error, and time it.
- **Assert.** The message contains `expect(received).toEqual(expected)` and `"not-stored"`: the same diff a single
  read gives. It took less than 10 s.

**G2 · `retries only a 502, at most twice`** proves that the retry cannot hide a failure. It needs no stack or
page; it uses fake `send`s whose `status()` follows a list, with `delayMs: 0`.
- **[502, 502, 200]:** it returns the 200, after 3 calls.
- **[502, 502, 502, 200]:** it returns the third 502, after 3 calls. `readStoredEvents` then fails with
  `events search: 502`, its unchanged line.
- **[404]:** it returns the 404, after 1 call.

## 5 · Proof: the flake is gone

**The counterfactual is built in.**
- **Cause §1.2 and §1.3:** the helper's first poll does exactly what the spec did once (§3.1). So "first read
  differed" in its annotation marks an execution the old spec would have failed.
- **Cause §1.1:** each `transient 502` warning marks a 502 the old spec would have failed at.

No "before" arm is needed.

- **P1 · The guards.** G1 and G2 pass in the fork's `mock-llm-e2e.yml`, dispatched on the branch, which also runs
  the sibling spec's three switched comparisons; and in P2.
- **P2 · Repeated runs where it flaked.** The setting is GitHub's `ubuntu-24.04` runner, `canvas-replay`'s exact
  setup, and D1's ten recordings.
  - **The branch.** A throwaway deep-reasoning branch, `proof/task-41`, never merged and deleted afterwards.
    `desktop/pins.toml` points `canvas_fork.commit` at the fix's head. In `cross-repo.yml`, every job but
    `canvas-replay` gets `if: false`, and `canvas-replay` becomes a 6-way matrix that runs the spec with
    `--repeat-each=5`.
  - **Its verdict** reads `results.json`, fails on any execution that did not pass, and prints four counts:
    executions, failures, "first read differed", and `transient 502` warnings.
  - **The run.** Dispatch it with `gh workflow run cross-repo.yml --ref proof/task-41`. That makes 6 × 5 × 10 =
    **300 executions** of the ten recordings, plus 30 of each guard. Each shard runs about 50 executions × 9 s,
    inside the 20 min `MOCK_LLM_GLOBAL_TIMEOUT_MS`.
  - **Accept** only if both hold:
    - all 300 passed, and none was flaky (the config's `retries` stays 0);
    - **at least one** execution's first read differed, or one 502 was retried.

    At the old rate, about 4 such executions are expected in 300, and P(none) ≈ 2 %. If none appears, the run did
    not exercise the race: report it and run 300 more. Never accept on zero evidence.
- **P3 · After the merge (not a gate).** The nightly `canvas-replay` runs once the pin moves to `dr-4`. At 4 in 33,
  a fortnight of green nights is weak evidence on its own; P2 is the proof.

## 6 · Other single reads in the family

| Site | Shape | Race | Action |
|---|---|---|---|
| sibling `:129–133`, `nested-stop` while waiting on Stop | rendered vs stored | **open**: `:121–127` waits for the three child ids only, so `cell-z1` and `cell-y1` (fixture lines 15–18) can still be draining, and the page can lag | fix (§3.3) |
| sibling `:231–235`, after reload | rendered vs stored | closed, but only by an unstated property: the summary "1 done · 1 stopped" needs child-y's last event, and the worker stores in order | switch (§3.3), so there is one form |
| sibling `:354–357`, E6 | rendered vs stored | closed the same way, by "50 sub-agents · 50 done" | switch (§3.3) |
| sibling `:134`, `rootCellIds` | page vs a constant | none: `cell-1` is the root's first event, stored inline | leave |
| sibling `:240–247`, child answer inside rows | page vs a constant | none: it follows `NESTED_STOP_DONE` and the summary wait | leave |
| sibling `:274–294`, fallback flow | page vs a constant | none: the `ghost` group needs child-o (fixture line 9), the last row it lists, and the worker stores rows in order; the root's `cell-2` is covered by the `FALLBACK_PLACEMENT_DONE` wait | leave |
| `waitForTurnsToEnd` `:203`, sibling polls `:121`, `:138` | `expect.poll` over `readStoredEvents` | the 502 of §1.1 | covered by §3.1's retry, no edit |
| `configureScriptedAcpAgent` `:64–88` | one-shot setup requests | could 502 through the same ingress; not a read of moving state | leave |

## 7 · Size and seams

- **Size.** Canvas: about +95 / −20 lines over four files (§3.1–§3.4). No product code, no new dependency. About
  half a day for the Implementer, plus P2's wall time (about 15 min per dispatch).
- **Seam with `fix/subagent-costs-on-by-default`** (in `ux-round-integration`). It edits the sibling at `:28–39`
  (imports), `:97` and `:136–160`, and the helpers at `:233–240`. This change's hunks are elsewhere, except the
  sibling's import list: both add a name after `expandAllSubagents`. That is one conflict hunk; resolve it by
  keeping both. Dropping §3.3 avoids it.
- **The task row.** `Design` = `docs/design/task-41-replay-race.md` (on deep-reasoning's `design/task-41`);
  `Branch` = `fix/replay-spec-settles` (Canvas fork).
