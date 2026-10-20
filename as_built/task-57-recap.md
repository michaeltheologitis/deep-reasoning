# TASK-57 · As built: a fresh run is given the conversation

**TASK-57** · Cartographer · 2026-10-19 · branch `as-built/task-57`, cut from `task-57-recap` at `c44dcc4`
(7 commits on `main` `9e8109e`, +893/−27). The build is checked against one document: the design,
`docs/design/task-57-recap.md` on `design/task-57` at `e8c3ee2`. There is no spec.

**Evidence.** Every claim carries a mark. **[run]**: I ran it at `c44dcc4`, on this machine, with FakeOpenAI;
no model was paid. **[CI]**: a named CI run at `c44dcc4` shows it. **[read]**: I read it in the code and did not
run it. The probe scripts behind some [run] marks are not committed.

**Reading guide.** §0 is the five-minute read. §3 lists every divergence from the design; §4 has the measured
results. §2 is the map of the code.

---

## 0 · What Michael gets, and what changed against what he approved

**What he approved** (2026-10-19, in chat, no spec): the Conductor's recommendation, to fix it so the model
keeps the conversation after a stop, a crash or a restart. The design carried the scope.

**What he gets.** A run can end before its conversation does: a root Stop, a failed drive, a failed build in
the worker, a worker crash, a `session/close`, or a dr-acp restart. After any of these, the next message's
fresh run is given every earlier message of the conversation, each with its answer, as one user message read
from the run logs. On the chat backbone the model's first call is `[system, recap, the new message]` [run].
A turn without an answer is carried with the reason: stopped, cut off, failed (with its detail), could not
start (with its detail), or ended without a final answer [run]. The newest whole turns that fit in 32,000
characters are kept, and each text is cut at 4,000 [run].

The user reads one more sentence on the fresh-run notice [run]:

> Starting a fresh run: the previous one was stopped, so its variables and sub-agents are gone. This run is
> given your earlier messages and their answers.

When older turns are left out, the sentence is "This run is given your messages from message 1485 on, and
their answers: older ones are left out to fit the model's context." When a text was cut, the notice adds "Any
message or answer longer than 4,000 characters is cut short." A replay shows the same notice, and a log from
before TASK-57 replays its old one [run].

**Against the design, the behaviour is as designed.** Every signature in design §4 and every sentence in §5 is
in the code as written there [read; the §5 sentences also run in tests]. The divergences are in the tests, the
workflow and the size (§3):

1. `live.yml` gains an optional `tests` input, so a run by hand can name the live tests it runs.
2. There is one test more, for R9 (a run log that cannot be read).
3. The endings test never ends an open prompt with a `run.end` of `failed` or `build_failed`. The front never
   writes that order.
4. The live test also asserts that the first two prompts answered and stopped, and the fresh run's
   `RecapNote(2, 0, False)`.
5. Some assertions take a different form.
6. Not reported by the Implementer: the build is larger than design §9 estimated. Code is +227/−6 against
   ≈165, and tests are +657/−20 against ≈430.

**Proof.** CI, cross-repo and live passed at `c44dcc4` [CI]. The live test ran on gpt-6-luna: after a root
Stop, the fresh run was asked to quote the first message, and its answer contained "prerequisites" [CI].

**Points for Michael**, each a fact, detailed in §2:

- An *exhausted* turn's answer is shown in the window as its closing message. The model is given "(none: the
  run ended without a final answer)" for it instead, as design §5.2 specifies [run; the window: read].
- When one of a conversation's run logs cannot be read, every later message answers "Could not start the run:
  FileNotFoundError: …", until the user starts a new conversation (R9) [run]. dr-acp logs this as
  `dr_acp.materialize_failed`, the event a config that cannot be materialized also logs [read].
- R8's namespace label never fires today: a conversation's namespace is fixed after its first message [read].
- Only the root is given the recap. A sub-agent of the fresh run starts from its own task [run].
- No test sends a recap through a Claude Code root, the path of EXP-74 [read].
- TASK-57 does not depend on TASK-69 either way (§5) [read; run with the re-send].

**Merging.** A trial merge with `origin/ux-round` (`6d31d2c`) has one conflict, the `route` import line in
`session.py`; both lines are kept [run]. A trial merge with `task-48-browser` (`44bf931`) is clean [run].

---

## 1 · The public surface

Copied from the code at `c44dcc4`.

`deep_reasoning.acp.recap`, new (176 lines):

```python
TEXT_CAP = 4_000
RECAP_MAX_CHARS = 32_000
RECAP_HEAD, RECAP_TAIL, EXHAUSTED, STOPPED, CUT_OFF, CUT_MARK      # design §5.2's texts
def left_out(n: int) -> str
def failed(detail: str) -> str
def could_not_start(detail: str) -> str
TurnEnd = Literal["answered", "exhausted", "failed", "build_failed", "stopped", "crashed", "closed", "lost"]
class Turn:  index: int; namespace: str; message: str; ended: TurnEnd; answer: str | None; detail: str | None
class Recap: text: str | None; note: RecapNote | None              # both frozen dataclasses
NO_RECAP = Recap(None, None)
def turns_of(events: Iterable[RunEvent], first: int = 1) -> list[Turn]
def read_turns(home: Home, runs: Sequence[str]) -> list[Turn]
def recap_of(turns: Sequence[Turn], namespace: str) -> Recap
```

One field or keyword each, added last, defaulting to none:

- `runlog.RecapNote(turns: int, left_out: int, shortened: bool)`, and `RunStart.recap: RecapNote | None = None`.
  The run log stays `v: 1`.
- `worker.protocol.Start.recap: str | None = None`.
- `supervisor.RunHandle.start(..., recap: Recap = NO_RECAP)`.
- `texts.fresh_run_notice(after: str | None, recap: RecapNote | None = None) -> str | None`, with `RECAP_ALL`,
  `RECAP_CUT_SHORT` and `recap_from(first: int)`.
- `.github/workflows/live.yml`: a `workflow_dispatch` input `tests`, empty by default. It reaches pytest as
  `$TESTS`, split into words.

Nothing a user types changed: there is no new command, option or ACP method.

---

## 2 · The path of one fresh run

```
Session._start_run ── to_thread ──▶ Session._recap
    read_turns(home, self.runs): turns_of(RunLog.read(...)) for each run ─▶ recap_of(turns, self.namespace) ─▶ Recap(text, note)
RunHandle.start(…, recap=)
    ├─ RunStart(after=…, recap=note) ── run log ──▶ Encoder._run_start: fresh_run_notice(after, note)      live and on replay
    └─ Start(…, recap=text) ── control pipe ──▶ Worker.build: reasoner.send(user(text)); then Worker.prompt: acall(task)
```

- **The front builds the recap; the worker only sends it.** `Session._recap` runs in a thread, inside the same
  `try` as `_materialize`, and before `self.runs.append`. So the run being started is never one of its own
  turns [read]. The worker's only new call, the last line of `Worker.build`, uses Dean's public
  `deep_reasoner.v2.messages.user` and `send` [read].
- **What crosses each seam.** Into the front: every run log of the session, read whole. Into the run log: a
  `RecapNote` of three fields. Into the worker: the text, a little over 32,000 characters at most (32,248 in the
  probe) [run]. The run log does not hold the text. The text is in the run directory's `llm_calls.jsonl` and in
  the root's node YAML [run].
- **The complexity sits in two functions**: `turns_of` (§2.1) and `recap_of` (§2.2). Each other change carries
  one field.

### 2.1 How a turn ends: `recap.turns_of`

A turn is a `prompt.start` together with the event that ended it:

| In the run log | `Turn.ended` | The model reads, after `Answer i:` |
|---|---|---|
| `prompt.end`, answered | answered | the answer |
| `prompt.end`, exhausted | exhausted | (none: the run ended without a final answer) |
| `prompt.end`, failed | failed | (none: the run failed: {detail}) |
| `prompt.end`, build_failed | build_failed | (none: the run could not start: {detail}) |
| `run.end` stopped, under an open prompt | stopped | (none: the user stopped the run before it answered) |
| `run.end` crashed, closed or lost, under an open prompt | that reason | (none: the run was cut off before it answered) |
| the log ends with the prompt open | lost | (none: the run was cut off before it answered) |

The nine cases of `test_a_turn_ends_with_its_answer_or_says_why_it_has_none` pin every row [run].

- `Session.replay` appends `run.end` `lost`, on `session/load`, to any run that never ended. So after a dr-acp
  restart, the cut-off turn arrives through the sixth row, and the seventh is a fallback [read].
- The supervisor writes a `run.end` of `failed` or `build_failed` only after a `prompt.end` of the same outcome
  (`RunHandle._end_reason`). So neither ever ends an open prompt [read]. If one did, the turn would read
  "(none: the run failed: )", with an empty detail [run].
- An exhausted turn keeps its answer on `Turn.answer`, and the recap does not render it [run]. For the same
  prompt, the window's closing message is that answer (`encoder.CLOSING_TEXT`) [read].
- The message is `PromptStart.task`: the user's text without a slash command [run]. A slash command can only
  open a conversation, because `_start_conversation` clears the menu. So a run with a decomposition never has
  earlier turns, and a recap is never sent with one [read].
- Turns are numbered from 1 across the runs, oldest first. A run with no prompt adds no turn [run].

### 2.2 The message and its bound: `recap.recap_of`

The message is `RECAP_HEAD`, a blank line, the turns' blocks (`Message i: …` ⏎ `Answer i: …`) separated by blank
lines, a blank line, and `RECAP_TAIL`. It matches design §5.2's example to the character [run].

- **The bound.** Starting from the newest turn, it keeps whole turns while their blocks, joined by blank lines,
  fit in 32,000 characters. The newest turn is always kept. Each message and each answer is cut at 4,000
  characters, right-stripped and marked " … (cut short)". Kept turns keep their numbers, and the head adds
  "Messages 1 to n are left out, to fit." [run]
- **Measured** [run]: one turn of two 50,000-character texts gives an 8,275-character message. 500 such turns
  keep 3, in 24,423 characters. 2,000 short turns keep the newest 516, in 32,248 characters. The bound counts the
  blocks only: the head, the left-out sentence and the tail add about 250 characters.
- **R8.** A turn whose run's namespace differs from the session's is labeled `Message i (namespace ns):`. Today
  the two cannot differ. `Session.set_namespace` refuses a change once the conversation has started
  (`NAMESPACE_FIXED`). Both catalogs' `materialize` return the namespace they were given, and `RunStart.namespace`
  records it [read]. Only its unit test reaches the label [run].

### 2.3 What reaches the model

- On the chat backbone, the fresh run's first model call is `[system, user(recap), user(new message)]`. The
  root's `agent.start` task is the new message, not the recap [run:
  `test_after_a_root_stop_the_next_message_is_given_the_earlier_messages_and_answers`].
- The recap stays in the root's history for the rest of the run. Every root call of the run carries it, and a
  second prompt in the same run answers from it [run: a probe, and the local cross-repo run in §5].
- A sub-agent is not given the recap. In the probe, the fresh run's root called `subagent('Read CS101.')`. Both of
  the root's calls held the recap; the child's call held only `[system, user(task)]` [run].
- On a Claude Code root, the recap reaches the CLI through `ClaudeDeepReasoner.think`. Design F2 says that
  renders it as `user('…')` until EXP-74 is fixed. No test covers this path [read].

### 2.4 What the user reads: `texts.fresh_run_notice`

The lead sentence is unchanged, chosen from `_FRESH_AFTER` by how the previous run ended. Given a `RecapNote`,
one sentence follows it: `RECAP_ALL` when nothing was left out, otherwise `recap_from(left_out + 1)`. Then
`RECAP_CUT_SHORT` follows when `shortened` is true [run].

A conversation's first run has no notice and no recap. A run after `build_failed` has no notice (R10), and the
recap is still given [notice: run; recap: read]. `Encoder._run_start` renders the notice from `RunStart.recap`,
so the live notice and the replayed one agree. A `run.start` without the field, from before TASK-57, replays its
lead sentence alone [run].

### 2.5 When a run log cannot be read (R9)

`read_turns` raises whatever `RunLog.read` raises. `_start_run` catches it as it catches a materialize failure:
it logs `dr_acp.materialize_failed` with the traceback, answers "Could not start the run: {type}: {message}"
with outcome `build_failed`, and starts no run [run:
`test_a_run_log_that_cannot_be_read_answers_build_failed_without_a_run`]. Every later message reads the same
logs, so the conversation keeps answering this way until the user opens a new one [read]. A `session/load` of
such a conversation already fails in `replay` [read].

**Reading cost** [run, on synthetic logs]: 100 runs of 100 cells with 2 KB outputs (22.9 MB) are read in 159 ms,
and 400 such runs (91.6 MB) in 459 ms. `recap_of` takes under 1 ms. This happens once per fresh run, before its
worker starts.

---

## 3 · Divergences from the design (`e8c3ee2`)

No divergence of behaviour was found. Every row below is in the tests, the workflow or the size. The reasons are
the Implementer's, as relayed by the Conductor, except where a commit message is cited.

| # | Design | Build | Reason | Checked |
|---|---|---|---|---|
| 1 | §6.4: the Implementer runs the live tier | `live.yml` gains the input `tests` (9 lines added, 1 changed). Empty runs every live test. The live run named one node id | "TASK-57's live test can then run alone, on gpt-6-luna only" (`6f10ccd`) | one id [CI]; empty [read] |
| 2 | §6.1 lists no test for R9 | `test_session.py`: `test_a_run_log_that_cannot_be_read_answers_build_failed_without_a_run`. It deletes a run's `events.jsonl`, then sends a message | R9 had no test | [run] |
| 3 | §6.1: "a run.end of each reason while a prompt is open" | `failed` and `build_failed` follow their `prompt.end`, never an open prompt | they cannot end an open prompt | [read] `_end_reason`; the other order [run] |
| 4 | §6.4 asserts `answered`, and "prerequisites" in the answer | It also asserts the three outcomes `answered, stopped, answered`, and `RunStart.recap == RecapNote(2, 0, False)` | two more preconditions | [read] |
| 5 | §6.1–6.2: the assertions' form | The close test compares the notice with `f"{FRESH_AFTER_CLOSE} {RECAP_ALL}"`, not a `model_dump()`. The numbering test uses three runs, not two: one has no prompt, one runs in namespace `math`. The load test checks the texts of the `Answer` lines, not `Turn.ended` | choices of form | [read] |
| 6 | §9: ≈165 lines of code, ≈430 of tests, ≈2 h at Gate C | Code +227/−6 (`recap.py`: 176 against ≈110). Tests +657/−20 (`test_recap.py`: 252 against ≈150). About 3 h at 300 lines an hour | not reported | [run] `git diff --numstat` |

The docstrings of `RunHandle.start` and `Worker.build` each gain a sentence about the recap.

---

## 4 · Measured results

**In CI, at `c44dcc4`.** The Conductor opened the runs; I read each one's commit, conclusion and log.

| Run | Result |
|---|---|
| `ci` 39211178628 (push) | success |
| `cross-repo` 39211233568 | `bridge-replay`: 13 passed, 12 deselected, in 66.5 s, `tests/crossrepo/test_recap.py` among them. `canvas-replay`: 10 passed. `desktop-e2e` (E12): 17 passed |
| `live` 39212429791 | `tests` named `tests/acp/test_live.py::test_live_after_a_root_stop_the_model_still_knows_the_first_message`. gpt-6-luna on `docs/configs/advising`: 1 passed, in 16.91 s |

The live log holds neither the model's reply nor its cost: the run's dr home is uploaded only on a failure.
There is no baseline arm, because the live test was not run on `main`. Design F1's baseline (on `main`, the fresh
run's first model call holds none of the first question) was shown with FakeOpenAI through the bridge, not with a
real model. To reproduce the live run: `gh workflow run live.yml --ref task-57-recap -f
tests=tests/acp/test_live.py::test_live_after_a_root_stop_the_model_still_knows_the_first_message`.

**On this machine, at `c44dcc4`** (FakeOpenAI only):

- `pytest tests/acp/test_{recap,texts,runlog,encoder,supervisor,session,agent}.py`: 142 passed, 8 failed. Every
  TASK-57 test passed. The 8 are golden and tree comparisons that pass in CI and fail on this machine: its
  Python 3.12.15 puts a stdlib traceback line at 59 where the goldens (3.12.3) have 58 (`failing`,
  `unanswered`), and the `claude` scenarios hit `AF_UNIX path too long` under a long temporary path.
- `DR_SDK_CHECKOUT=<tree of the SDK pin 34c540c> pytest -m crossrepo tests/crossrepo/test_recap.py`: passed in
  48 s; the tree's two bridge files are byte-identical to the pin's. §5 reads its run logs.
- The probes behind §2's numbers: the bound, the endings, the sub-agent check and the reading cost.

---

## 5 · Seams with other work

- **TASK-69 (the re-send after a Stop).** TASK-57 reads only dr-acp's own run logs, when a run starts, and no
  code looks for a re-sent message [read]. In the local cross-repo run the re-send happened: run 2 began with
  "Wait for me." again, then "What did I ask first?". Its recap, fixed before either, held 2 turns, and the last
  answer quoted the first message [run]. The test asserts only that, and answers a re-sent "Wait for me." at
  once, so it holds either way [read; the path without the re-send was not run]. While the re-send lasts, a
  later recap lists the stopped message twice, once stopped and once answered [read, from these logs].
- **The UX round.** The trial merge with `origin/ux-round` at `6d31d2c` (the design read `0955bc2`) has one
  conflict, the `route` import line in `session.py`. It resolves by keeping both
  `from deep_reasoning.acp.recap import Recap, read_turns, recap_of` and the UX round's
  `from deep_reasoning.acp.route import ModelRoute, missing_model_keys` [run]. `texts.py` and the three shared
  test files merge without a conflict [run]. The UX round's `tests/test_names.py` scans `acp/texts.py`, and the
  new sentences name neither `deep_reasoner` nor `deep-reasoning` [read; the merged suite was not run].
- **TASK-48** (`task-48-browser`, `44bf931`): no shared file, and the trial merge is clean [run].
- **TASK-56** would enter at `turns_of`, which takes a turn's namespace from its run's `RunStart` (design §7.2)
  [read].

---

## 6 · Not verified

- The Claude Code root's path (EXP-74): no test, and not run.
- `live.yml` with an empty `tests` input: read only.
- The bridge without the re-send, as after TASK-69: read only.
- The test suite on a tree merged with the UX round: not run.
- How a model uses a recap with turns left out or texts cut: only the texts are tested; no model was asked.
- The live reply's text and its cost: they are not in the CI log.
