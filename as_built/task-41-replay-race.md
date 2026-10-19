# TASK-41 · The replay spec settles — as built

**TASK-41** · Cartographer · 2026-10-19 · on deep-reasoning `as-built/task-41`, cut from `main` `9e8109e`; never
merged.

- **Built:** the Canvas fork's `fix/replay-spec-settles` at `1d6ea20`. It is two commits (`7debacf`, `1d6ea20`)
  on `dr-3` (`4355a36`), +196/−37 over four files: test code and one guide sentence.
- **Checked against:** the design `docs/design/task-41-replay-race.md` on `design/task-41` (`2f9b589`), and
  nothing else. `@playwright/test` is 1.63.0.
- **Marks.**
  - **run**: run in this sandbox. That is a scratch harness that drives the real helpers at `1d6ea20` with a fake
    page and request under Playwright 1.63.0, `git merge-tree`, or a count over a run's downloaded `results.json`.
  - **CI**: a run's log or artifacts, opened.
  - **read**: read in the code or a record, and not run.

## 0 · What Michael gets, and what changed against what he approved

**Approved:** the design's recommendation (Michael, 2026-10-19: "go with what you recommend"), merged without his
review.

**He gets:**
- **Polling, not a single read.** C1's replay spec, and the sibling sub-agent spec in three places, compare the
  rendered and the stored sub-agent trees once a second, for up to 30 s. They stop when the two agree and the
  store has stopped changing. **run, CI**
- **A real mismatch still fails,** with the same diff. **run, CI**
- **A 502 is retried, and nothing else:** every events-search GET retries a 502 at most twice. **run**
- **Test code only.** **read**
- **The proof:** 300 of 300 passed in run 39211074434. Of the 600 proof executions, 8 hit the old race and
  passed. **CI, run**

**Against the design, nothing changes in behaviour.** What differs:
- G2 also tests a 503 and `readStoredEvents` itself.
- G1 strips colour codes from the message.
- The work is two commits, and the second can be dropped.
- The proof ran from `ux-round` through a dispatch input, and ran twice.

§2 has all nine divergences. One result was not predicted: the "store has stopped" condition never decided an
outcome in 600 executions (§3).

## 1 · What is built

### The helper

`expectRenderedTreeToMatchStored(page, request, conversationId, { timeout = 30_000 })` lives in
`tests/e2e/mock-llm/utils/acp-subagents.ts`. **read**
- **Callers:** the replay spec's per-recording test, and the sibling spec's nested-stop, reload and 50-sub-agent
  tests.
- **One poll,** inside `toPass({ timeout, intervals: [1_000] })`:
  1. expand every sub-agent;
  2. read the rendered tree, then the stored tree;
  3. `expect(rendered).toEqual(stored)`;
  4. `expect(stored, "the agent-server was still storing the sub-agent tree").toEqual(previous)`.

How it behaves (**run**):
- **A pass takes at least two polls,** because the first poll has no previous tree.
- **A store still being written** passes one poll after it stops.
- **A store that never stops** fails with the "still storing" message.
- **A mismatch** fails with the last poll's diff and `Call Log: - Timeout …`, before its deadline. A 5 s deadline
  failed at 4.0 s.

**On a pass,** it returns the stored tree and adds the annotation
`subagent-tree: settled after <n> polls; first read <matched|differed>`. "differed" is the default, so a first
poll that throws also counts as "differed". **read**

### The seam: `readStoredEvents`

Each page's GET goes through `retryTransient(send, { retries = 2, delayMs = 500 })`. **run**
- **It retries a 502 only.** It sends again while the status is in `TRANSIENT_STATUSES`, which holds only `502`.
- **It returns the last response,** whatever its status.
- **Every retry is logged** as `transient <status>; retry <n> of <retries>`.
- **A thrown error is not retried.**

Every stored read therefore gets the retry: `waitForTurnsToEnd`'s poll, both tree reads, and the sibling spec's
direct reads. The failure line `events search: <status>` is unchanged.

Playwright 1.63's `expect.poll` ends at the first throw from its callback. So before this change, a single 502 in
`waitForTurnsToEnd` failed the test. **run**

### The guards

The two guards come before the recordings in the replay spec's serial describe. **read, CI**
- **A failing guard fails the job.** It skips the recordings, which fails `cross-repo.yml`'s verdict.
- **They skip with the spec,** when `OH_ACP_REPLAY_TRANSCRIPTS` is unset or the run is in Docker mode.
- **G1:** after a pass, it renames one rendered call's `data-acp-tool-call-id` to `not-stored`. It expects the
  helper, at 5 s, to fail with that diff in under 10 s.
- **G2:** it runs four status sequences through `retryTransient`, then runs `readStoredEvents` through a fake
  client.

### Everything else

The e2e-testing guide gains the design's sentence, word for word. Nothing else changes: product code,
`waitForTurnsToEnd`, fixtures, workflows, test titles, and the single reads that design §6 marks "leave".
**read**

## 2 · Divergences from the design

The Implementer reported 1 to 7. Nobody reported 8 or 9.

| # | Design | As built | Why |
|---|---|---|---|
| 1 | G2 has three status rows. | It adds `[503, 200]`, which returns 503 after one call. | Without that row, mutation m5 (503 and 504 count as transient) passes G2. |
| 2 | G2 says `readStoredEvents` "then fails". | G2 runs it through `{ get } as unknown as APIRequestContext`, and expects `events search: 502` after three calls. | This is the only check that `readStoredEvents` uses the retry. It caught m6. |
| 3 | G1 expects `expect(received).toEqual(expected)` in the message. | It checks `stripVTControlCharacters(message)`. | Playwright colours the matcher hint, so the raw message lacks the plain string. **run** |
| 4 | One change. | Two commits: `7debacf` is §3.1, §3.2 and §4; `1d6ea20` is §3.3 and §3.4. | It keeps §3.3 droppable, as design §0.3 offers. Dropping `1d6ea20` drops the guide sentence too. |
| 5 | The verdict reads "`results.json`". | It reads Playwright's JSON report, `test-results-mock-llm/results.json`. `main`'s verdict reads the done-marker's `.mock-llm-markers/.results.json` instead. It also counts guard executions. | The done-marker file holds titles and statuses only, and the counts need annotations and stderr. Playwright 1.63 writes the JSON report after the webServer teardown, so a shard killed in teardown has no file. That fails red, never green. **read** |
| 6 | One 300-execution run; a second only if the first shows no evidence. | Two runs. | Run 1 failed acceptance on a failure outside TASK-41's code (§3). |
| 7 | G1's timeout is unstated, and "first read differed" means a mismatch. | G1 sets `test.setTimeout(180_000)`, as the recordings do. "differed" also counts a first poll that threw. | Each such throw also fails the old single read, so the counterfactual holds. **read** |
| 8 | `proof/task-41` points `desktop/pins.toml` at the fix. | It is cut from `ux-round` (`2ba0bc8`), not `main`. `pins.toml` is unchanged, and the Canvas commit comes in through `ux-round`'s `canvas_commit` dispatch input. | That input already existed. Run 2 checked out Canvas `1d6ea20` and SDK `34c540c`, the commits the design names. **CI** |
| 9 | About +95/−20. | +196/−37. | The guards and their fake take about 80 lines, and the design gave signatures without bodies or doc comments. |

## 3 · Proof and measured results

**Baseline** (design §0): 4 of 33 `canvas-replay` attempts failed from 2026-10-04 to 2026-10-19, about 1.3 % of
roughly 309 test executions.

| Run | What | Commit | Result | Mark |
|---|---|---|---|---|
| 39209106292 | The fork's `mock-llm-e2e.yml`, dispatched with `SPECS` set to the two specs, on recording `fallback-placement.jsonl`. | Canvas `1d6ea20` | 8 of 8: G1, G2, one recording, and the sibling spec's 5 tests. | CI |
| 39209541483 | `proof/task-41` (`939708a`): `canvas-replay` alone, 6 shards × `--repeat-each=5`. | Canvas `1d6ea20`, SDK `34c540c` | 298 of 300, and the guards 60 of 60. `namespace` timed out at 180 s in `startConversation`, on a disabled submit button, before any TASK-41 code ran. The serial describe then skipped `unanswered`. Filed as TASK-72 (a failed `GET /api/agent-profiles`). | CI; the cause is **read** |
| 39211074434 | The same, again. | The same | 300 of 300, and the guards 60 of 60. | CI |
| 39220656317, 39221995995 | deep-reasoning `cross-repo` on `ux-round` (`b283be2`). | Canvas `1a9e3c6`: this branch merged into `ux-round-integration` | `canvas-replay` 12 of 12 in each (2 guards and 10 recordings); every job green. | CI |

- **The counterfactual.** 8 of the 600 proof executions did something the old single read fails on, and passed.
  That is 1.3 %, the baseline rate. **run** (counted from each shard's `results.json`)
  - **4 first reads differed:** in run 1, `failing` and `fanout2`; in run 2, `namespace` and `unanswered`.
  - **4 retried one 502:** all in run 1: `fanout20`, `fanout2` twice, and `failing`.
  - **Run 2 alone meets the design's acceptance:** 300 of 300, and two first reads that differed.
- **All 598 passing executions settled in exactly two polls,** the minimum. **run**
  - In each of the four that differed, the stored tree was the same on both polls, and only the page caught up.
  - The case of design §1.2, a store still draining, did not occur, so the second condition never decided an
    outcome. Only the scratch harness exercises it.
- **Cost.** **run**
  - A recording execution averages 8.4 to 8.6 s, with a maximum of 11.3 s.
  - A shard's Playwright run takes 8.5 to 11.6 min, under the 20 min `MOCK_LLM_GLOBAL_TIMEOUT_MS`.
  - G1 takes about 14.5 s, and G2 at most 1.25 s.
  - G1 passed 63 times in CI, and React never reset its renamed attribute.
- **Mutations.** Six mutations, each caught, from the Implementer's local runs (attributed, not repeated).
  **read**
  - G1 caught two: m1, which drops the tree comparison, and m2, which ignores the deadline.
  - G2 caught four: m3, which retries any failure; m4, with no retry bound; m5, which counts 503 and 504 as
    transient; and m6, which leaves the search unretried.
- **Lint:** 0 errors, and no warning in the four files. From the Implementer's `npm run lint`, attributed. **read**
- **The residual the design names stays open.** A pass on a partial tree needs the store to stall for a full
  interval mid-drain. Nothing built closes it. **read**
- **Reproduce P2** with
  `gh workflow run cross-repo.yml --repo michaeltheologitis/deep-reasoning --ref proof/task-41 -f canvas_commit=1d6ea20630fedfa92fa9baf5cb8f972ecefbca33`.
  Each shard writes its counts to the run summary.

## 4 · Seams

- **`fix/subagent-costs-on-by-default`.** Merging it conflicts in one hunk, the sibling spec's import list:
  `expectRenderedTreeToMatchStored` against `hideSubagentCosts`. Keep both, as `ux-round-integration`'s `1a9e3c6`
  does. Everything else merges clean. **run** (`git merge-tree`)
- **Ships in** Canvas `dr-4` with the UX round. `cross-repo.yml` on `main` runs it once `desktop/pins.toml` moves
  there. **read**
- **`proof/task-41`** (`939708a`) is throwaway, for Michael to delete. **read**

## 5 · Not verified here

- **Run 1's failure.** Its cause is TASK-72's diagnosis.
- **The mutations and the lint.** Both are the Implementer's local runs, and were not repeated here.
- **The guards on a live stack.** Only CI ran them there. The harness drove the helpers with fakes, not a page.
