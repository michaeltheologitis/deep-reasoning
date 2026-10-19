# TASK-57 · A fresh run is given the conversation — design

**TASK-57** · System Designer · branch `design/task-57` in
[deep-reasoning](https://github.com/michaeltheologitis/deep-reasoning), cut from `main` at `9e8109e`. This file
is the only change on the branch. **There is no spec.** Michael approved the Conductor's recommendation without
one on 2026-10-19: "Do them without the spec go with what you recommend no need to write spec in notion". The
recommendation was to fix it so the model keeps the conversation after a stop, crash or restart. §1 therefore
carries what a spec would have: the mock-up, the scope and the decisions that are expensive to reverse.

**Pinned against:** deep-reasoning `main` `9e8109e` (every deep-reasoning `file:line`) · deep_reasoner
`d7334ae` (Dean's, from this repo's locked environment) · SDK fork `34c540c` (`dr-2`, `desktop/pins.toml`).
The UX round (TASK-65) is read at `origin/ux-round` `0955bc2` for the seams (§7).

**Revisions** (newest first):
- 2026-10-19 · v1 · first version.

**Where this file lives.** At `docs/design/task-57-recap.md`, as D5's and TASK-48's designs do. `testpaths` is
`tests`, ruff `extend-exclude`s `docs`, the sdist excludes `docs/`, and the wheel packages `src/deep_reasoning`
only. No pull request of the task's stack carries this file.

**Names.** The task row calls the new thing "the carry". In code it is **the recap**, because `carry` already
means the cost carried between runs (`Encoder(carry=…)`, `Session.replay`).

**Reading guide.** Gate B: §0 and §1 (about 8 minutes). The Implementer: everything. §4 holds the signatures,
§5 every sentence and §6 the tests. The UX round's implementer: §7.

---

## 0 · Findings (read first)

Each finding was run on 2026-10-19 with the scripts in the System Designer's scratchpad (`task-57-design/`).
No model was paid: FakeOpenAI and the fake claude CLI stood in.

**F1 · In the app, every root Stop is followed by a dr-acp restart and a `session/load`.** Canvas's Stop is
`POST /interrupt` in local mode. The bridge then sends `session/cancel`, and dr-acp answers `stopReason:
cancelled`. On a cancelled response the bridge sets `_restart_session_on_next_turn` (`acp_agent.py:4739-4741`
at `34c540c`), kills dr-acp, starts a new one and calls `load_session` with the same id (`:3955-3970`, `:3603`).
I ran this through the pinned agent-server and its bridge (`probe_bridge.py`): `Restarting ACP session` → `ACP
server initialized` → `Resumed ACP session` → the next prompt. The second run's `run.start` had `after: stopped`.
Its first model call held none of the first question; that is the bug, reproduced through the real client. **So
the recap must be read from disk. A record kept in memory would never survive into the run it is for.**

**F2 · On a Claude Code root, seeded chat messages reach the CLI as their reprs.**
`ClaudeDeepReasoner.think` joins `str(getattr(m, "content", m))` (`claude_reasoner.py:248`), but `Chat` holds
`.text`. Without a recap the prompt is already `user('What did I ask first?')`; this is EXP-74, still Needed. The
task row's proposal, `send(user(q), assistant(a), …)`, arrives as `user('q')\nassistant('a')\nuser('task')`.
Once Dean fixes EXP-74, the same messages arrive as bare lines, and nothing says which line is a question and
which an answer. **This is why the recap is one user message that labels its own turns (R3, divergence V1).**

**F3 · On the chat backbone, the seeding works through Dean's public API alone** (`probe_chat.py`,
`probe_jinja.py`). Messages `send` queues before the first drive land after the system prompt, the worked
examples and the bindings' block, in order (`agent.py:690`, `:1027`). The bindings' block folds into the system
prefix, so it is not displaced (`llm_coro.py:66`). The text is not Jinja-rendered (`messages.py:98`), so `{{ }}`
in a user's question reaches the model verbatim. A later `acall(task)` makes `task` the agent's task:
`agent.start` carries the latest `send`'s first text (`agent.py:388-411`, `:877`). **So the recap gets its own
`send`, before `acall`.** One `send` holding both would title the root with the recap. Resumes keep it in
history, so later prompts of the same run still have it (EXP-38).

**F4 · Out of scope, for the Conductor: after a Stop, the next message re-runs the stopped one first.** The
pinned agent-server advances its ACP prompt cursor only when a step ends neither paused nor in error
(`local_conversation.py:2530-2543`). When the conversation runs again, it sends the interrupted message to the
new dr-acp first, then the new one. In the probe, run 2's prompts were `Spin.`, then `What did I ask first?`. I
saw this through the agent-server's REST API, not through Canvas's UI. It is a separate task, with Michael's
call on whether Stop should drop the message. This design only makes sure that tests tolerate it (§6.3).

---

## 1 · What the user sees, and what is out of scope

**Before (main).** The model of a fresh run has never seen the conversation; only the window has.

```
You   Which course is lightest?
DR    STAT101, at 6 hours a week.
You   Plan my term around it.                                      [Stop]
DR    Stopped. The run was ended and its REPL state is gone: … Your next message starts a fresh run.
You   What did I ask first?
DR    Starting a fresh run: the previous one was stopped, so its variables and sub-agents are gone.
      This is the first message you have sent me.                  ← it was given nothing
```

**After.**

```
DR    Starting a fresh run: the previous one was stopped, so its variables and sub-agents are gone.
      This run is given your earlier messages and their answers.
      You first asked which course is lightest.
```

A long conversation, after dr-acp restarted:

```
DR    Starting a fresh run: the previous one ended when dr-acp restarted, so its variables and sub-agents
      are gone. This run is given your messages from message 9 on, and their answers: older ones are left out
      to fit the model's context. Any message or answer longer than 4,000 characters is cut short.
```

**In scope.** Every way a run ends before the conversation does: a root Stop, a failed drive, a failed build in
the worker, a crash, a close (`session/close`, then `session/load`) and a dr-acp restart (`session/load` of a
run that never ended). The recap and the notice are the same live and on replay.

**Out of scope.**
- The REPL's variables and sub-agents. They are still lost; that is deep_reasoner's (ROOT_STOPPED, A3).
- The model's own working (cells, their output, sub-agents' talk). Only messages and answers are carried.
- A new conversation (`session/new`). It is given nothing from other conversations.
- What was never in a run log. That covers refusals answered without a run (`_reply`: a late decomposition, a
  command without a task, the UX round's missing key) and the bridge's appended text blocks (`dropped`).
- Switching namespaces (TASK-56). §7.2 says what it reuses.
- F4's re-send, and EXP-74's repr, which is Dean's.
- A token-exact budget. The bound is in characters (R5).

---

## 2 · Decisions

Marked ⚠ where reversing one costs more than a code change.

- **R1 ⚠ · The run logs are the source.** A session's runs come from `SessionIndex.runs`, oldest first. Each
  `runs/<run>/events.jsonl` gives `prompt.start` (`task`), `prompt.end` (`outcome`, `answer`, `detail`) and
  `run.end` (`reason`). Both survive a dr-acp restart and a `session/load`, which F1 makes the common path.
  Replay already trusts them. The agent-server's events are the client's, carry the bridge's extensions, and
  dr-acp cannot read them. A store of dr-acp's own would duplicate the run log. The logs are read whole, in a
  thread, when a run starts (`RunLog.read`).
- **R2 · Every turn of the conversation is carried, not only those since the last fresh run.** The run before
  the last was itself given the turns before it, so carrying only the latest run would forget them. Within a
  live run nothing changes: deep_reasoner's resume keeps the history, the recap included.
- **R3 ⚠ · The recap is one `user` message, not `user`/`assistant` pairs** (divergence V1 from the task row's
  proposal). It says the earlier runs have ended and their variables are gone, numbers each turn, and ends by
  saying the user's next message follows. Reasons:
  - it reads the same on both backbones, before and after EXP-74 (F2);
  - the chat model's own assistant turns stay `<repl>` blocks. An assistant turn of bare prose is one it might
    imitate, and the loop then spends an iteration asking for a block;
  - the model is told the variables are gone, so it does not reach for a name an old answer mentions.

  It is not a `system` message: one would join the leading system run, and the bindings' block would be
  appended to it (F3).
- **R4 · A turn without an answer is carried, with why it has none.** The message is kept and its answer says
  why there is none: the user stopped it; it was cut off (a crash, a close or a restart); it failed, with its
  detail; it could not start, with its detail; or it ended without a final answer (exhausted). "Try that again"
  after a Stop needs the stopped message.
- **R5 · The bound: the newest whole turns that fit in 32,000 characters, each message and answer cut at 4,000.**
  That is about 8k tokens. The cap per text keeps one long answer from crowding out the rest, and lets the
  newest turn always fit (2 × 4,000 plus labels). Older turns are left out whole and keep their numbers: the
  model reads "Messages 1 to 8 are left out", then "Message 9". The notice says what was left out and whether
  anything was cut short (§5.1). The numbers are constants (`RECAP_MAX_CHARS`, `TEXT_CAP`), cheap to change.
- **R6 ⚠ · `run.start` records what the run was given** (`RunStart.recap: RecapNote | None`, additive, `v` stays
  1). The notice is rendered from it, so a replay says what the run was given then, and a log from before
  TASK-57 (no field) replays its old notice unchanged. The recap's text is not logged: deep_reasoner's node
  YAML in the run directory already holds it.
- **R7 · The front builds the recap; the worker only sends it.** The front owns the run log, so it builds the
  recap and puts the text in `Start.recap`. The worker sends `user(start.recap)` at the end of `build`, before
  the first `acall`. Its only API is Dean's public one: `deep_reasoner.v2.messages.user`, `send`, `acall`.
- **R8 · A turn from another namespace is labeled with it:** `Message 3 (namespace math): …`. A session's
  namespace is fixed today, so no label is ever written yet. It is the recap's rule for any turn a run log can
  hold, and TASK-56 inherits it (§7.2). It costs one conditional and one test.
- **R9 · A run log that cannot be read fails the run's start, as a config that cannot be materialized does.**
  The user reads `Could not start the run: <detail>`, rather than a recap that quietly lacks turns. `load`
  already fails the same way on such a log.
- **R10 · No notice after `build_failed`, as today.** Nothing was lost, so there is nothing to warn about. The
  recap is still given.

---

## 3 · The shape

```
Session._start_run ─ to_thread ─▶ read_turns(home, self.runs) ─▶ recap_of(turns, self.namespace) ─▶ Recap(text, note)
        │
        └▶ RunHandle.start(…, recap=) ─┬▶ RunStart(after=…, recap=note)  ── run log ──▶ Encoder._run_start
                                        │                                              fresh_run_notice(after, note)
                                        └▶ Start(…, recap=text) ── control pipe ──▶ Worker.build
                                                                                    reasoner.send(user(text))
                                                                     Worker.prompt: reasoner.acall(prompt.task)
```

`read_turns` reads the runs that have ended. `_start_run` runs before `self.runs.append` (`session.py:217`), so
the new run is not one of them. `self.prompting` and `self.lock` keep any other run from being live.

---

## 4 · Signatures

```python
# src/deep_reasoning/acp/recap.py (new)
"""What a fresh run is given of its conversation: every earlier message and its answer, read
from the run logs, as one user message (TASK-57)."""

TEXT_CAP = 4_000          # characters of one message or one answer; the rest is cut (R5)
RECAP_MAX_CHARS = 32_000  # characters of the kept turns' blocks, "\n\n"-joined (R5)

TurnEnd = Literal[
    "answered", "exhausted", "failed", "build_failed", "stopped", "crashed", "closed", "lost"
]

@dataclass(frozen=True)
class Turn:
    index: int          # 1-based across the conversation's runs, oldest first
    namespace: str      # its run's RunStart.namespace
    message: str        # PromptStart.task: the user's text without its slash command
    ended: TurnEnd      # PromptEnd.outcome; else the reason of the RunEnd under it; else "lost"
    answer: str | None  # PromptEnd.answer (answered, exhausted); else None
    detail: str | None  # PromptEnd.detail (failed, build_failed); else None

@dataclass(frozen=True)
class Recap:
    text: str | None          # the user message the run is seeded with; None when there are no turns
    note: RecapNote | None    # what RunStart records; None exactly when text is None

NO_RECAP = Recap(None, None)

def turns_of(events: Iterable[RunEvent], first: int = 1) -> list[Turn]:
    """One run's turns, numbered from first: each prompt.start, ended by its prompt.end, or by
    the run.end that came while it was open; one the log leaves open ended "lost"."""

def read_turns(home: Home, runs: Sequence[str]) -> list[Turn]:
    """Every run's turns, oldest first, numbered across the conversation. Raises what
    RunLog.read raises (R9)."""

def recap_of(turns: Sequence[Turn], namespace: str) -> Recap:
    """§5.2's message, with the newest turns whose blocks fit in RECAP_MAX_CHARS (always the
    newest); each message and answer cut at TEXT_CAP with CUT_MARK; a turn whose namespace is
    not namespace labeled with it (R8). No turns: NO_RECAP."""
```

```python
# src/deep_reasoning/acp/runlog.py
class RecapNote(BaseModel):
    """TASK-57: what a fresh run was given of its conversation, for its notice."""
    turns: int        # the turns in the recap
    left_out: int     # the oldest turns not in it, to fit RECAP_MAX_CHARS
    shortened: bool   # a message or answer in it was cut at TEXT_CAP

class RunStart(_Ev):                      # :33-43, one field added last
    recap: RecapNote | None = None        # None: no earlier turns, or logged before TASK-57

# src/deep_reasoning/acp/worker/protocol.py
class Start(BaseModel):                   # :10-22, one field added last
    recap: str | None = None              # TASK-57: sent to the reasoner before its first drive
```

```python
# src/deep_reasoning/acp/worker/runner.py, Worker.build (:132-165), its last lines
        if start.recap is not None:
            self._reasoner.send(user(start.recap))   # its own send, before acall (F3)
# (import: from deep_reasoner.v2.messages import user)

# src/deep_reasoning/acp/supervisor.py, RunHandle.start (:86-166): one keyword
    recap: Recap = NO_RECAP,   # RunStart(..., recap=recap.note); Start(..., recap=recap.text)

# src/deep_reasoning/acp/session.py
#   _start_run (:193-197): inside the try, after _materialize,
#       recap = await asyncio.to_thread(self._recap)
#   and RunHandle.start(..., recap=recap, ...) (:204-216).
    def _recap(self) -> Recap:
        """TASK-57: the conversation so far, for the run about to start."""
        return recap_of(read_turns(self.ctx.home, self.runs), self.namespace)

# src/deep_reasoning/acp/encoder.py, _run_start (:343-351)
        notice = texts.fresh_run_notice(ev.after, ev.recap)

# src/deep_reasoning/acp/texts.py
def fresh_run_notice(after: str | None, recap: RecapNote | None = None) -> str | None:
    """The notice a run starts with: how the previous run ended, then what of the conversation
    this one is given (§5.1). None for the first run and after build_failed; with no recap,
    the lead sentence alone (a run logged before TASK-57)."""
```

---

## 5 · Texts (verbatim; tests assert these)

### 5.1 `deep_reasoning.acp.texts`: what the user reads

`FRESH_AFTER_STOP`, `_ERROR`, `_RESTART` and `_CLOSE` are unchanged. Each is now the notice's **lead**, and the
whole notice for a run logged before TASK-57. After the lead, separated by a space:

| Name | Sentence |
|---|---|
| `RECAP_ALL` (`left_out == 0`) | This run is given your earlier messages and their answers. |
| `recap_from(first)` (`left_out > 0`, `first = left_out + 1`) | This run is given your messages from message {first} on, and their answers: older ones are left out to fit the model's context. |
| `RECAP_CUT_SHORT` (when `shortened`), from `TEXT_CAP` | Any message or answer longer than 4,000 characters is cut short. |

So `fresh_run_notice("stopped", RecapNote(turns=2, left_out=0, shortened=False))` is "Starting a fresh run: the
previous one was stopped, so its variables and sub-agents are gone. This run is given your earlier messages and
their answers." The new literals say neither `deep_reasoner` nor `deep-reasoning`, so the UX round's allow-list
test passes them.

### 5.2 `deep_reasoning.acp.recap`: what the model reads

| Name | Text |
|---|---|
| `RECAP_HEAD` | This conversation began before this run. Its earlier runs have ended, so their variables and sub-agents are gone; below are the user's earlier messages, each with the answer it got. |
| `left_out(n)`, after the head and a space | `n == 1`: Message 1 is left out, to fit. · else: Messages 1 to {n} are left out, to fit. |
| a turn's block | `Message {i}: {message}` ⏎ `Answer {i}: {answer}`. With R8's label: `Message {i} (namespace {ns}): …` |
| `RECAP_TAIL` | The user's next message follows. |
| `EXHAUSTED` | (none: the run ended without a final answer) |
| `STOPPED` | (none: the user stopped the run before it answered) |
| `CUT_OFF` (crashed, closed, lost) | (none: the run was cut off before it answered) |
| `failed(detail)` | (none: the run failed: {detail}) |
| `could_not_start(detail)` | (none: the run could not start: {detail}) |
| `CUT_MARK`, after a cut text's `rstrip()` | ` … (cut short)` |

The message is the head, then a blank line, the blocks joined by blank lines, another blank line, and the tail.
`test_the_recap_is_one_message_in_the_designs_words` asserts this one exactly:

```
This conversation began before this run. Its earlier runs have ended, so their variables and sub-agents are gone; below are the user's earlier messages, each with the answer it got.

Message 1: Which course is lightest?
Answer 1: STAT101

Message 2: Spin.
Answer 2: (none: the user stopped the run before it answered)

The user's next message follows.
```

---

## 6 · Tests

### 6.1 Unit

`tests/acp/test_recap.py` (new); it builds run logs with `RunLog.create`/`append`.
- `test_a_turn_ends_with_its_answer_or_says_why_it_has_none`, over the eight endings. A `prompt.end` of each
  outcome; a `run.end` of each reason while a prompt is open; a log left open, which is lost. Each asserts the
  `Answer 1:` line of §5.2.
- `test_turns_are_numbered_across_the_runs_of_the_conversation`: two runs, 1..n in order, each with its run's
  namespace. A run closed between prompts adds no turn.
- `test_the_recap_is_one_message_in_the_designs_words`: §5.2's example; note `(2, 0, False)`.
- `test_a_message_or_answer_over_the_cap_is_cut_and_the_note_says_so`.
- `test_the_oldest_turns_are_left_out_to_fit_and_the_rest_keep_their_numbers`. The newest turn, at the largest
  size it can have, is still kept.
- `test_a_turn_from_another_namespace_names_it` (R8).
- `test_no_earlier_turns_means_no_recap`.

Elsewhere:
- `tests/acp/test_texts.py`: `test_a_fresh_run_says_what_it_is_given`, inserted after the first test (`:44`).
  Parametrized cases: `stopped` with no recap is `FRESH_AFTER_STOP`; `stopped` `(2,0,F)`; `lost` `(14,6,T)`;
  `closed` `(1,0,T)`; `build_failed` `(1,0,F)` is None. Each is the verbatim sentence.
- `tests/acp/test_runlog.py`: `test_a_run_start_logged_before_task_57_reads_with_no_recap`, a line with no
  `recap` key.
- `tests/acp/test_encoder.py`: one more row in `test_a_run_starts_with_the_notice_its_predecessors_end_calls_for`
  (`:163-178`), a `stopped` run with a note; its `run_start` helper (`:38`) takes `recap=`.

### 6.2 End to end: dr-acp over stdio, FakeOpenAI

- **New**, in `tests/acp/test_supervisor.py`:
  `test_after_a_root_stop_the_next_message_is_given_the_earlier_messages_and_answers`.
  - The prompts: `Which course is lightest?` answers `STAT101`; `Spin.` is stopped; `What did I ask first?`.
  - A responder in `tests/acp/scenarios.py`, `answering_from_the_recap(plan)`, answers that question with
    `FinalAnswer(<Message 1's text>)`, read from the user message that starts with `RECAP_HEAD`.
  - It asserts:
    - the answer is `Which course is lightest?`;
    - run 2's first model call is `[system, user, user]`. The first `user` is `recap_of` of the two turns, and
      the second is the question;
    - run 2's root `agent.start` task is the question (F3's order);
    - the notice is `fresh_run_notice("stopped", RecapNote(turns=2, left_out=0, shortened=False))`.
- **Extended**, in `tests/acp/test_agent.py`: `test_load_replays_every_run_and_marks_a_killed_one_lost`
  (`:148-212`; its docstring ends "…starts fresh, given every earlier turn"). This is the restart and
  `session/load` path. `body()` also returns `model.calls`. It asserts:
  - the fresh run after the load is given 4 turns, ending answered, stopped, answered and lost;
  - its notice is `fresh_run_notice("lost", …)`, with its `RunStart.recap.model_dump()` equal to
    `{"turns": 4, "left_out": 0, "shortened": False}`;
  - the replayed updates hold run 2's notice, `fresh_run_notice("stopped", (2,0,F))`. The test tree drops
    notices (they carry no `run` in `_meta`), so the tree comparison does not pin this.
- **One line each**, the notice assertions that now carry a 1-turn note:
  - `test_supervisor.py:73` (stop) and `:131` (crash);
  - `test_session.py:323` (failed drive);
  - `test_agent.py:270` (close). It compares `model_dump()` and adds no import (§7.1).

### 6.3 Cross-repo: the real bridge (`crossrepo` marker, `bridge-replay` job)

`tests/crossrepo/test_recap.py`:
`test_after_a_stop_through_the_bridge_the_next_message_is_given_the_first`. This is the probe of F1, made a
test. It uses `agent_server(sdk_checkout(), root)` and the profile and conversation set up as in
`test_mcp_forwarding.py`.
- The steps: ask `Which course is lightest?`; post `Wait for me.`; once its cell starts in the run log, `POST
  /interrupt` (Canvas's Stop); then ask `What did I ask first?`.
- `Wait for me.` sleeps in a cell on its first drive and answers on any later one. That way F4's re-send
  finishes, whichever path the bridge takes.
- It asserts:
  - two runs;
  - run 2's `RunStart.after == "stopped"` and `recap.turns == 2`;
  - run 2's last `prompt.end` answers `Which course is lightest?`.
- Nothing is asserted about the bridge's internals, so the test holds if the bridge stops restarting.

### 6.4 Live (`live` marker, `live.yml`; the Implementer runs it, a few cents)

`tests/acp/test_live.py`: `test_live_after_a_root_stop_the_model_still_knows_the_first_message`. It runs on
gpt-6-luna with `docs/configs/advising`.
- The steps: ask `Which STAT course has no prerequisites?`; ask a fan-out over every course and stop the root
  at its first cell; then ask `Quote my first message in this conversation exactly.`
- It asserts `answered`, and `prerequisites` in the answer.
- It is the only measure of R3 on a real model: that the one-message recap is used, and that the reply is still
  a `<repl>` block.

### 6.5 E12 and the goldens

- **E12 gets no step.** The path that matters is the bridge's: cancel, restart, `session/load`. §6.3 runs it
  from the same pinned SDK without the UI. Canvas's Stop is only `POST /interrupt`, which TASK-57 does not
  change. The UX round is rewriting E12, too.
- **The goldens do not change.** No scenario has a second run, and none of the 20 recordings holds a fresh-run
  notice (checked: `grep -l "Starting a fresh run" tests/acp/golden/*` is empty). No golden is added: §6.2 pins
  the notice and the model's messages directly.

---

## 7 · Seams

### 7.1 With the UX round (`ux-round` at `0955bc2`) and TASK-48

| File | UX round | TASK-57 | Merge |
|---|---|---|---|
| `acp/session.py` | `import os, shutil`; the `route` import (`:25`); 4 lines after the `except` (`:197`) | the `recap` import, sorted between the `encoder` block and `route` (`:24`/`:25`); one line in the `try` (`:194`); `recap=` in `RunHandle.start` (`:204-216`); `_recap` after `_materialize` (`:225`) | the one overlap: the import touches the `route` line, so keep both lines; the rest is disjoint |
| `acp/texts.py` | `ROOT_STOPPED` (`:11-14`); `missing_model_key` after `build_failed` (`:95`); `cap_reached` | two imports before `:9`; `RECAP_*` after `_FRESH_AFTER` (`:53`); `fresh_run_notice` (`:87-89`) | disjoint (5 lines apart at `:89`/`:95`) |
| `acp/agent.py`, the 20 goldens, `test_e12.py` | changed | untouched | none |
| `tests/acp/test_agent.py` | imports (`:14`, `:23-30`), `:130`, appended at the end | `:148-212`, `:270`; no import | disjoint |
| `tests/acp/test_session.py`, `test_texts.py` | `:257-291`; `:71-81` and the end | `:323` and an import; inserted at `:44` | disjoint |
| `tests/crossrepo/agent_server.py` | adds `outbound_proxy=` (keyword) | untouched; `test_recap.py` calls it positionally | compatible |

**TASK-48** (`task-48-browser`) touches no dr-acp file and no test this design changes, so there is no seam.

### 7.2 What TASK-56 reuses (none of it built here)

- **If Dean's `agent.enter` (#114, EXP-81) lands,** a switch happens inside one run and needs no recap. A Stop
  after a switch is still a fresh run, though. TASK-56 then adds `PromptStart.namespace` and has `turns_of`
  prefer it to the run's, and R8 labels the old namespace's turns.
- **If Dean declines** (TASK-56's fallback), a switch becomes `_start_run` in the new namespace with this
  recap, and adds an `after` reason and a lead sentence for it.

---

## 8 · Dean's code: Expectations for the Conductor

- **New, In place:** "Chat messages sent to a v2 reasoner with `send()` before its first drive open its
  conversation in order, after the system prompt, the worked examples and the bindings' block, not
  Jinja-rendered; a later `acall(task)` makes `task` the agent's task, the one `agent.start` logs." The code
  that relies on it is `Worker.build`'s new lines and `recap.py`. Verified at `d7334ae` by `probe_chat.py` and
  `probe_jinja.py`.
- **EXP-74 (Needed):** add `Worker.build`'s recap line to what relies on it. Until it is fixed, a Claude root
  receives the recap as `user('…')`, escapes included; afterwards, as plain text. Either way `RECAP_TAIL` marks
  where the new message starts (F2).
- **EXP-38** already covers resume, which is what keeps the recap for the rest of the run.

Nothing is filed on Dean's repository.

---

## 9 · Size

Lines added and removed, tests included.

| Where | Code | Tests |
|---|---|---|
| `recap.py` (new) | ≈ 110 | ≈ 150 (`test_recap.py`) |
| `runlog`, `protocol`, `runner`, `supervisor`, `session`, `encoder` | ≈ 35 | ≈ 25 (runlog, encoder rows) |
| `texts.py` | ≈ 20 | ≈ 35 |
| end to end, the notice lines, `scenarios` helper | n/a | ≈ 85 |
| cross-repo and live | n/a | ≈ 135 |
| **Total** | **≈ 165** | **≈ 430**: ≈ 0.6k lines, about 2 h at Gate C |

---

## 10 · What I was unsure about

1. **R3 on a real model.** One message versus chat pairs was argued, not measured: no paid call was allowed.
   §6.4 measures one case. If the model handles the pairs better, `recap_of` is the only function to change.
2. **The bound's numbers** (32,000 and 4,000) are judgment. `prices.yaml`'s `context_window` could size the
   budget per model later.
3. **R8 is built ahead of need.** It costs one conditional and one test. The Conductor may cut it to TASK-56.
4. **R9 favours an error over a silent gap.** A deleted run directory then blocks the conversation until the
   user starts a new one.
5. **F4 seen through REST only.** I did not check Canvas's UI; E12 or a manual run would.
6. **The cost of reading the logs.** Every log is read whole at each fresh run. That is fine at today's sizes,
   but it was not measured on a very long conversation.
