# TASK-69 · After a Stop, the next message is sent alone — design

**TASK-69** · System Designer · branch `design/task-69` in
[deep-reasoning](https://github.com/michaeltheologitis/deep-reasoning), cut from `main` at `9e8109e`. This file
is the only change on the branch. **There is no spec.** Michael approved the Conductor's recommendation in chat on
2026-10-19: "Yeah let's go with ur recommendation on task 69." The recommendation: Stop means "not that one". The
stopped message stays visible, the model is told it was stopped (TASK-57's recap), and it is never run again. §1
and §2 therefore carry what a spec would have: before and after, the scope, and the decisions that are expensive
to reverse.

**Pinned against:** deep-reasoning `main` `9e8109e` · SDK fork `34c540c` (`dr-2`, `desktop/pins.toml`; every SDK
`file:line` unless said otherwise) · Canvas fork `4355a36` (`dr-3`) · upstream SDK `main` `3f32945` (2026-10-19),
read for intent only. Seams are read at `origin/task-57-recap` `c44dcc4` and `origin/design/ux-round`.

**Revisions** (newest first):
- 2026-10-19 · v1 · first version.

**Where this file lives.** At `docs/design/task-69-stop.md`, beside the other task designs. `testpaths` is `tests`,
ruff `extend-exclude`s `docs`, the sdist excludes `docs/`, and the wheel packages `src/deep_reasoning` only. No
pull request carries this file. The fix itself is in the SDK fork (§4); deep-reasoning gets one test file (§5.2).

**Reading guide.** Gate B: §0, §1 and §2 (about 6 minutes). The Implementer: everything; §4 is the contract, §5
the tests. The Conductor: §7, the release chain.

---

## 0 · Findings (read first)

Each was run on 2026-10-19 with the scripts in the System Designer's scratchpad (`task-69-design/`:
`probe_stop.py`, `seam_turns.py`, and a throwaway patch, `probe_patch.diff`). The agent-server ran from a copy of
the pinned tree, with its real ACP bridge and dr-acp from `main`. No model was paid: FakeOpenAI stood in.

**F1 · It reproduces on Canvas's own path.** Canvas sends a message as JSON with `run: true` over
`/sockets/events/{id}` (`conversation-websocket-context.tsx:1236-1290`). That reaches
`event_service.send_message(message, True)` (`sockets.py:360`), the same call as REST `POST /events`
(`event_router.py:227`). Canvas's Stop in local mode is `POST /interrupt` (`conversation-mutation-utils.ts:55-60`).
The probe sent `Which course is lightest?`, then `Spin.`, whose cell sleeps. It pressed Stop in that cell, then sent
`What did I ask first?` over the socket. dr-acp received, in order:

```
run 1 (after none):    Which course is lightest? → answered   Spin. → run ended "stopped"
run 2 (after stopped): Spin. → answered                       What did I ask first? → answered
```

The agent-server's events, which Canvas renders, hold the new question, then the answer to `Spin.`, then the
answer to the question (§1). I read the events Canvas renders, not its window: the app is not installed here,
and E12 has no root Stop step.

**F2 · The cause is the SDK's ACP prompt cursor. Upstream wants it to keep a stopped prompt retryable, not to
replay it before a new message.**
- `LocalConversation._arun` keeps the cursor in `agent_state` (`acp_last_prompt_user_message_id`, `:122`). Each
  run sends the prompt message after it (`:2293-2337`).
- A step commits its prompt when it ends neither in error, stuck nor paused (`:2531-2543`). On a cancellation it
  commits only when a newer message superseded the prompt or the prompt completed during the cancel
  (`:2627-2642`). A Stop is neither, so the cursor stays before `Spin.`.
- Upstream asks for that: `test_acp_arun_does_not_commit_cursor_on_explicit_interrupt` says "Explicit interruption
  should leave the in-flight ACP prompt retryable." (`test_conversation_send_message.py:630`). It came with
  upstream #3376 (2026-05-28), and upstream `main` still has it.
- Upstream also asks that a new message supersede a running prompt without replaying it. In
  `test_send_message_with_run_true_interrupts_running_acp_turn` (`test_event_service.py:956`) the prompts are
  `["initial request", "intervening"]`. The cancellation test at `:673` says "Completed ACP prompts should not be
  replayed after cancellation."
- No upstream test covers a new message *after* a Stop. The replay there follows from "retryable"; nothing asks for
  it.

**F3 · Retryable is what Canvas's Resume button uses.** After a Stop, Canvas shows `Stopped` and a play button, ▷
(`agent-status.tsx:81-84`, `:153-157`), which is `POST /run` (`conversation-mutation-utils.ts:117-123`). The probe
pressed it in place of the new message, and run 2 was sent `Spin.` alone. That is the one path where running the
stopped message again is what the user asked for.

**F4 · Native OpenHands agents never answer the stopped message on its own.** The same steps on an `Agent` (not ACP)
give one model call after the Stop, `[system, user, assistant, user]`, whose last user message is `["Spin.", "What
did I ask first?"]`. The stopped text joins the new message's turn. The separate re-run is ACP-only.

**F5 · §4's shape passes upstream's tests and the real bridge.**
- A probe patch of 34 changed lines passed the 143 tests of `test_conversation_send_message.py` and
  `test_event_service.py` unchanged.
- Over the wider `tests/sdk/conversation`, `tests/sdk/agent` and `tests/agent_server` suites (eight workers), 4,280
  passed with the patch and 4,279 without. Both runs had the same 19 errors, from the sandbox: 11 where a test's
  own agent-server would not start, and 8 from a file outside `tests/` that the copy lacks.
- No failure is the patch's. Every test that failed with it passed when run alone with it, except the OpenRouter
  model list in `test_llm_router.py`, which fails without it too. The other failures differ between the runs; they
  are timing tests, two of them the bridge's cancel drain, which also failed unpatched.
- §5.1's four tests ran against it: on `dr-2` three fail on the replay and the retry test passes; with the patch
  all four pass.
- Through the real bridge, run 2 was sent `What did I ask first?` alone, and the fresh-run notice led its answer.
  ▷ still sent `Spin.` alone.

**F6 · TASK-57's recap double-counts today.** TASK-57's `read_turns` (`task-57-recap` `c44dcc4`), read over F1's
logs, gives four turns: the first question, answered; `Spin.`, stopped; `Spin.` again, answered; the question,
answered. Over the patched run's logs it gives three: `Spin.` once, stopped. TASK-57's as-built found the same on
its own cross-repo test at `c44dcc4`: run 2 began with `Wait for me.` again (`as_built/task-57-recap.md`,
`as-built/task-57` `adc5114`).

**F7 · Out of scope, for the Conductor.**
- **The same cursor also replays after an error.** A step that ends in error or stuck is not committed
  (`:2531-2543`, `:2668-2675`), so the next message first re-runs the failed one. dr-acp answers every drive with
  `end_turn` or `cancelled` (`session.py`, `STOP_REASONS`), so with dr-acp this follows only a bridge-level failure:
  dr-acp dying, or an ACP timeout. A hard kill of the agent-server mid-prompt is the same case: the conversation
  reloads as an error (`event_service.py:1325-1327`), with no handler run. I read this from the code; I did not
  probe it.
- **Canvas never shows `ROOT_STOPPED`.** dr-acp's "Stopped. … Your next message starts a fresh run." is not in the
  agent-server's events. The bridge drops a cancelled turn's text (`acp_agent.py:4736-4745`). The only traces of a
  Stop are the `Stopped` label, until the next message, and a started cell's card, "Not finished: the run was
  stopped". I did not check whether Canvas shows the text while it streams.

---

## 1 · What the user sees, and what is out of scope

**Before (`dr-2`).**

```
You   Which course is lightest?
DR    STAT101
You   Spin.
        Run import time …   Not finished: the run was stopped
                                                            Stopped  ▷
You   What did I ask first?
DR    Starting a fresh run: the previous one was stopped, so its variables and sub-agents are gone.

      spun                                  ← "Spin." run again, unasked, and answered here
DR    no idea                               ← the answer to the question
```

**After.**

```
You   What did I ask first?
DR    Starting a fresh run: the previous one was stopped, so its variables and sub-agents are gone.

      no idea
```

Once TASK-57 is merged, the notice goes on, "This run is given your earlier messages and their answers.", and the
answer is the first question. That is TASK-57's own §1, which assumed this fix (its F4).

Nothing else in the chat changes, and no sentence is added. The stopped message keeps what it shows today: the
user's bubble, the card of any cell it started ("Not finished: the run was stopped"), and the `Stopped` label with
▷ until the next message. **▷ after a Stop still runs the stopped message again** (D2).

**In scope.** Every way the run loop is cancelled out of an ACP prompt it has not committed:
- Canvas's Stop (`POST /interrupt`);
- the agent-server's `close()`, when the app quits mid-prompt. It pauses, then cancels the run task
  (`event_service.py:2052-2100`), and reaches the same handler.

After either, the next message is sent alone, however it arrives: over the socket, by REST, or queued with
`run: false` and then run. That holds across an agent-server restart between the Stop and the message, because the
state is persisted with the cursor.

**Out of scope.**
- F7's replay after an error or stuck, and `ROOT_STOPPED`'s loss.
- A mark on the stopped user bubble. Canvas renders no `InterruptEvent`; that is the UX round's area.
- Hiding ▷ for ACP conversations (D2's alternative).
- How native agents fold the stopped text into the next turn (F4): upstream's semantics, and our app has no
  native conversations.
- The synchronous `run()`, which has no ACP cursor.

---

## 2 · Decisions

Marked ⚠ where reversing one costs more than a code change.

- **D1 ⚠ · The fix is in the SDK fork's `LocalConversation`,** not in the bridge, the agent-server's
  `EventService`, dr-acp or Canvas.
  - `LocalConversation` owns the cursor, and every client goes through it: Canvas over the socket or REST,
    `RemoteConversation`, and an SDK user calling `interrupt()`, `send_message()` and `arun()`.
  - The bridge (`ACPAgent.astep`) is handed one `prompt_message` a step. It cannot tell a retry from a replay.
  - `EventService` would fix only the agent-server's clients, and it does not own the cursor.
  - dr-acp would have to guess. A replayed prompt has the same text as one the user retypes or retries with ▷.
    dr-acp would still have to answer it, so the chat would still show an answer to it. Every other ACP agent would
    need its own copy of the guess.
  - Canvas only posts the message.
- **D2 ⚠ · A newer message supersedes the stopped prompt; ▷ alone still retries it.** This is upstream's supersede
  rule, extended from a message that arrives while the prompt runs to one that arrives after it was stopped.
  - It keeps upstream's "retryable" (F2), which ▷ relies on (F3).
  - The alternative, dropping the prompt at the Stop itself, contradicts upstream's test. Under the fork rule it
    would then be off by default behind a setting, and ▷ would do nothing for ACP unless Canvas hid it: a setting
    and a Canvas change, for a narrower result.
  - "Never run again" then means the system never runs it again. The user still can, with ▷. If Michael means his
    call to cover ▷ too, it is that alternative, and that cost is why this is ⚠.
- **D3 · A plain bug fix: on by default, upstream-shaped, with no setting and no `[fork only]`.**
  - Upstream's tests ask for both halves of D2, and none asks for the replay (F2, F5).
  - Upstream's native agents never answer the stopped message on its own (F4).
  - Upstream's Canvas users see the same wrong answer.
  - It can be offered upstream as is.
- **D4 · The run loop decides, when a run starts, against the prompt messages it would send.**
  - Every cursor write is in `_arun` today, and this keeps it so.
  - Deciding there covers every way a message is appended: `send_message`, a `run: false` queue, a fork.
  - One new `agent_state` key, `acp_retryable_prompt_user_message_id`, is written where a cancellation leaves the
    prompt uncommitted. The start of the next ACP run removes it, whatever that run decides, so it never outlives
    one run.
- **D5 · A prompt cut off by `close()` is treated as a stopped one.** `LocalConversation` cannot tell the two
  apart, and the rule reads the same for both: a new message means "not that one", and ▷ retries. In TASK-57's
  recap such a turn ends `closed`.
- **D6 · The SDK side guarantees that the recap lists a stopped message once, as stopped; neither dr-acp nor
  Canvas changes.**
  - The agent-server no longer sends the stopped message again, so dr-acp's run logs hold it once. TASK-57's
    `read_turns` then gives it once, ending `stopped`, with no change of its own (F6).
  - The recap is not de-duplicated on dr-acp's side. Once the SDK is fixed, a stopped turn followed by an answered
    one with the same text can only be a ▷ retry, and the recap should list those as the two attempts they were.
  - §5.2 asserts both cases on the real bridge.
- **D7 · The fix ships in SDK `dr-3`, not a later release** (§7.1). Every SDK pin move costs a Canvas re-wire and
  tag, because Canvas's pinned commit names the SDK's (`desktop/build.py`, `check_pins`, `:245-256`), and `dr-3` is
  already moving for TASK-46.

---

## 3 · The shape

```
Stop    POST /interrupt → EventService.interrupt → LocalConversation.interrupt → the arun task is cancelled
        _arun, except CancelledError: the in-flight prompt A was neither superseded nor completed
            → agent_state[ACP_RETRYABLE_PROMPT_USER_MESSAGE_ID] = A.id          (new; today nothing is kept)

Next    send_message(B, run=True) → EventService.run → _arun
        _arun's opening lock block → _supersede_retryable_acp_prompt()
            a prompt message follows A          → cursor := A.id      → B is sent
            A is the last prompt message (▷)    → cursor unchanged    → A is sent again
            A is not on the active branch       → cursor unchanged    → as today
            the key is removed in every case
```

---

## 4 · Signatures

The SDK fork, `openhands-sdk/openhands/sdk/conversation/impl/local_conversation.py`:

```python
ACP_RETRYABLE_PROMPT_USER_MESSAGE_ID = "acp_retryable_prompt_user_message_id"   # after :124, with its siblings


class LocalConversation(BaseConversation):
    def _supersede_retryable_acp_prompt(self) -> None:   # after _latest_acp_prompt_message_id (:716-723)
        """A prompt a cancelled run left retryable is retried only while no newer
        prompt message follows it; once one does, the cursor moves past it, as for a
        prompt superseded while it ran. The state lock is held."""
```

**Its contract.** "Prompt messages" are `_is_acp_prompt_message` events (`:163`) on `self._state.active_branch()`,
in order, the same list the run loop selects from (`:2296-2300`).

| The key holds | The prompt messages | The cursor afterwards | The run's first prompt |
|---|---|---|---|
| nothing | any | unchanged | as today |
| A's id | A, then at least one more | A's id | the one after A |
| A's id | A last | unchanged (before A) | A, again (▷) |
| A's id | A not among them (a fork from an earlier event, an edited branch) | unchanged | as today |

In every row the key is gone afterwards. When the key is set, the method writes `self._state.agent_state` once, as
a new dict, as its neighbours do; when it is not, it writes nothing.

**Its two call sites.**
- **`_arun`'s opening `with self._state:` block** (`:2213-2238`). It runs after the `FINISHED`/`IDLE` promotion of
  the in-flight id (`:2214-2228`) and before `last_acp_prompt_user_message_id` is read (`:2236`):
  `if isinstance(self.agent, ACPAgent): self._supersede_retryable_acp_prompt()`.
- **The `except asyncio.CancelledError` handler** (`:2627-2642`). It keeps its rule, and adds the other branch.
  When the in-flight id is not `None`, it is written as `ACP_LAST_PROMPT_USER_MESSAGE_ID` if
  `superseded_by_new_message or completed_cancelled_prompt`, as today, and otherwise as
  `ACP_RETRYABLE_PROMPT_USER_MESSAGE_ID`.

Nothing else changes: not the selection (`:2293-2337`), not the post-step commit (`:2516-2543`), not the error path
(`:2668-2675`), not `EventService`, not the bridge.

**Compatibility.**
- `agent_state` is `dict[str, Any]`, persisted in `base_state.json`. The key is additive: no schema version, no
  golden fixture, no TypeScript client change.
- A `dr-2` agent-server reading a later state ignores the key and retries the prompt, as today.
- `fork()` deep-copies `agent_state` (`:917`) and keeps event ids, so the key stays valid in a fork. A fork from an
  earlier event falls in the table's last row.

---

## 5 · Tests

### 5.1 The SDK fork (pytest, as its neighbours: `ACPAgent.init_state` and `ACPAgent.astep` patched)

In `tests/sdk/conversation/local/test_conversation_send_message.py`, after
`test_acp_arun_commits_cursor_when_cancelled_prompt_completed` (`:673-716`). In each, `astep` records the prompt's
text and blocks on its first prompt until it is cancelled; `interrupt()` comes once it blocks:
- `test_acp_arun_passes_over_a_stopped_prompt_once_a_newer_message_follows`: send `stop me`, `arun`, interrupt;
  send `not that one`, `arun`. The prompts are `["stop me", "not that one"]`.
- `test_acp_arun_retries_a_stopped_prompt_while_no_newer_message_follows`: as above, but `arun` with nothing new
  (▷), then send `next` and `arun`. The prompts are `["stop me", "stop me", "next"]`. It pins D2, and that a
  retried prompt, once answered, is not sent a third time. It passes on `dr-2` too; it guards the half that must
  not change.
- `test_acp_a_stopped_prompt_is_passed_over_by_a_conversation_reloaded_from_disk`: with a `persistence_dir`. After
  the interrupt, a new `LocalConversation` on the same directory and `conversation_id` is sent `after the relaunch`
  and run. The prompts are `["stop me", "after the relaunch"]`. This is the app quit between the Stop and the next
  message.

In `tests/agent_server/test_event_service.py`, in `TestEventServiceSendMessage`, after
`test_send_message_with_run_true_interrupts_running_acp_turn` (`:956-1026`):
- `test_send_message_after_an_explicit_interrupt_does_not_resend_the_stopped_acp_prompt`. This is Canvas's path:
  `await event_service.run()`, the first step blocks, `await event_service.interrupt()`, then `await
  event_service.send_message(<not that one>, run=True)`. The prompts are `["stop me", "not that one"]`.

`test_acp_arun_does_not_commit_cursor_on_explicit_interrupt` (`:630`) is unchanged and stays green, and its
docstring stays true. Each file gets `uv run pre-commit run --files <file>`, per the fork's `AGENTS.md`.

### 5.2 deep-reasoning: across the repositories (`crossrepo` marker, `bridge-replay` job)

`tests/crossrepo/test_stop.py` (new). Its setup is that of `test_mcp_forwarding.py` and of TASK-57's
`test_recap.py`: `agent_server(sdk_checkout(), …)`, `desired_profile`, FakeOpenAI. It sends by REST, which is the
same server call as Canvas's socket (F1).
- `test_after_a_stop_through_the_bridge_the_next_message_is_sent_alone`.
  - The steps: ask `Which course is lightest?`. Post `Spin.` with `run: true`; once its cell sleeps in the run log,
    `POST /interrupt` and wait for `paused`. Then ask `What did I ask first?`.
  - `Spin.` sleeps on its first drive only and answers `replayed` on any later one, so a replay fails an assertion,
    not the timeout.
  - It asserts:
    - two runs;
    - run 1's prompts are `[first, Spin.]`, and its `run.end` is `stopped`;
    - run 2's prompts are exactly `[What did I ask first?]`;
    - `read_turns(Home(home), runs)` (TASK-57) gives `(message, ended)` pairs `(first, answered), (Spin., stopped),
      (question, answered)`. That is the TASK-57 seam (D6): the stopped message is counted once, as stopped.
- `test_resume_after_a_stop_through_the_bridge_sends_the_stopped_message_again`: post `Spin.`, Stop, then `POST
  /run` (▷). Run 2's prompts are exactly `[Spin.]`, and `read_turns` gives `(Spin., stopped), (Spin., answered)`:
  two attempts, as D6 says. It pins D2 at the pin.

The first fails on `dr-2`'s agent-server and passes on `dr-3`'s, so the file lands with the pin move or after it
(§7.2). The second passes on both and guards D2. Both import TASK-57's `read_turns`, so the file also lands after
TASK-57 (§7.2).

### 5.3 Not added

- **No E12 step.** Canvas does not change. §5.2 makes Canvas's two calls against the same server code (F1). E12 has
  no root Stop today, and the UX round is rewriting it.
- **No dr-acp test.** Nothing of dr-acp changes. TASK-57's tests hold either way (§7.2).
- **No live test.** No model behaviour changes.

---

## 6 · Upstream

- **What upstream intends** (F2): an explicitly interrupted ACP prompt stays retryable, and a newer message
  supersedes an ACP prompt without replaying it. §4 keeps both; it only closes the gap where the newer message
  arrives after the Stop.
- **Shaped as an upstream PR** (D3): one SDK file, upstream's own test files, nothing deep_reasoner-specific.
  Whether to open it upstream is Michael's call.
- **Expectations.** Nothing new: the code relies on our SDK fork and on TASK-57's `read_turns`, none of it Dean's.

---

## 7 · Seams

### 7.1 The SDK fork: `dr-3` and TASK-46

- **The branch:** `fix/acp-stop-supersedes-stopped-prompt`, cut from the fork's `deep-reasoning` at `34c540c`
  (`dr-2`). It is a pull request into `deep-reasoning` of its own, as TASK-46's `fix/title-llm-without-credentials`
  (`1f1a381`) is.
- **No file in common with TASK-46,** which changes `agent_profiles_router.py`, `conversation_service.py` and
  their two test files. No other fork branch is ahead of `dr-2` (checked 2026-10-19).
- **The release chain** (the UX round's design, §8 step 1) has Michael tag `dr-3` at TASK-46's merge. **This pull
  request must merge before that tag.** The rest of the chain then carries it unchanged: Canvas's
  `chore/wire-sdk-dr-3`, then both pins in one deep-reasoning commit.
- **If it is not ready, the Conductor chooses:** hold `dr-3` for it (the SDK pull request is ≈ 165 lines, §8), or
  ship it in a later `dr-N`. A later release costs another Canvas re-wire and tag, and another pin move. I
  recommend holding `dr-3`.
- No TypeScript client change, so `dr-release.yml`'s client tarball is unaffected.

### 7.2 deep-reasoning: `task-57-recap` and `ux-round`

- **No dr-acp file changes,** so nothing overlaps `task-57-recap`'s 19 files or `ux-round`'s.
- **`tests/crossrepo/test_stop.py` is new.** `task-57-recap` adds `test_recap.py` beside it. `ux-round` gives
  `agent_server()` an `outbound_proxy=` keyword, which a positional call leaves alone.
- **TASK-57's `test_recap.py` stays green on `dr-3`.** It asserts run 2's `RecapNote(turns=2, …)` and that the last
  answer is the first question; both hold with or without the replay (F6). Its `waiting_once` tolerance becomes
  unneeded; it is TASK-57's file, so it stays.
- **TASK-57's F4 and its §10.5** ("seen through REST only") are answered by F1 here.
- **TASK-57's as-built names the double listing** (F6) and asks which side guarantees one listing: the SDK side
  (D6), asserted by `test_stop.py`. TASK-57 itself depends on the re-send neither way.
- **Merge order:** TASK-57 and `ux-round` (which moves the pins to `dr-3` and `dr-4`), in either order; then
  TASK-69's pull request, which holds `test_stop.py` only and needs both.

### 7.3 Everyone else

TASK-48 (`task-48-browser`) and TASK-64, TASK-66 and TASK-41 (Canvas branches): TASK-69 changes no Canvas file and
no dr-acp file, so there is no seam.

---

## 8 · Size

Lines added and removed, tests included.

| Where | Code | Tests |
|---|---|---|
| SDK fork, `local_conversation.py` | ≈ 35 | n/a |
| SDK fork, `test_conversation_send_message.py`, `test_event_service.py` | n/a | ≈ 130 |
| deep-reasoning, `tests/crossrepo/test_stop.py` | n/a | ≈ 110 |
| **Total** | **≈ 35** | **≈ 240**: ≈ 0.28k lines, under an hour at Gate C |

---

## 9 · What I was unsure about

1. **D2: whether Michael's "never run again" covers ▷.** I read it as "the system never re-runs it"; ▷ is the user
   asking. If he meant ▷ too, D2's alternative costs a fork setting and a Canvas change.
2. **Canvas's window was not looked at.** F1 reads the events Canvas renders, sent through Canvas's own calls; no
   browser rendered them.
3. **D5: a prompt cut off by quitting is passed over by the next message.** After the relaunch the conversation is
   paused, so ▷ is there to retry it. Whether that is what a user expects after a quit, rather than after a Stop,
   is a judgment.
4. **A Stop that lands before the prompt reached the ACP agent.** For example, during the bridge's restart and
   `session/load`. The agent never saw that message, and the next message passes over it, so TASK-57's recap
   (built from dr-acp's logs) will not list it. The user stopped it, which is "not that one". I did not probe this.
5. **Upstream may want a different rule:** fold the stopped text into the next prompt, as native agents do (F4).
   Michael's call is to drop it. If upstream asks for folding, only §4's method changes.
6. **F7's error replay is from reading the code.** It may deserve its own task.
