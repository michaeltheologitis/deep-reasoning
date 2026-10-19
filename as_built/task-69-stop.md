# TASK-69 · As built: after a Stop, the next message is sent alone

**TASK-69** · Cartographer · 2026-10-19 · branch `as-built/task-69`, cut from `main` `9e8109e`. The build is one
commit in the SDK fork: `fix/acp-stop-supersedes-stopped-prompt` at `d878bbb`, on `dr-2` `34c540c`, +196/−6 in
three files. deep-reasoning has no code change yet. It is checked against the design only:
`docs/design/task-69-stop.md` on `design/task-69` at `579be52`, its only revision. There is no spec.

**Evidence.** **[run]**: I ran it here, at `d878bbb` or, for a baseline, on `dr-2`'s code, with FakeOpenAI and
no model call. **[read]**: read in the code or in the Implementer's logs, not run by me. There is no CI run: the
fork's CI runs only on pull requests, and none is open. The scripts behind [run] are not committed.

---

## 0 · What Michael gets, and what changed against what he approved

**He approved** (2026-10-19, in chat, no spec): "Yeah let's go with ur recommendation on task 69". The
recommendation: Stop means "not that one"; the stopped message stays visible, the model is told it was stopped
(TASK-57's recap), and it is never run again.

**What he gets**, once the app's SDK pin moves to `dr-3`:

- After a Stop, the next message is answered on its own. Through the real bridge and dr-acp, run 2 is sent only
  `What did I ask first?`, and the reply under it is the fresh-run notice and `no idea` [run]. On `dr-2` it was
  sent `Spin.` first, and `spun` landed under the new question [read: the Implementer's probe].
- It holds over the socket and through `EventService.send_message`, which REST also calls; for a message queued
  and then run; and across a relaunch between the Stop and the message [run].
- Quitting the app mid-prompt counts as a Stop (design D5) [run: a throwaway test of `EventService.close()`].
- TASK-57's `read_turns` lists the stopped message once, ending `stopped` [run].

**Against what he approved**, one point, the design's D2 (⚠): **▷ Resume after a Stop still runs the stopped
message again** [run]. "Never run again" is built as "the system never runs it again"; the user still can, with
▷. Dropping it on ▷ too needs a fork setting and a Canvas change (design D2). Otherwise the behaviour is as
designed; the divergences (§2) are in the tests and the size.

**Not yet in the app.** The fork pull request is not open, `dr-3` is Michael's tag, and `desktop/pins.toml` still
names `dr-2`. `tests/crossrepo/test_stop.py` (design §5.2) is not written; it lands with the pin move.

## 1 · Where the change sits

One seam, in `LocalConversation` (`openhands-sdk/.../conversation/impl/local_conversation.py`). The run that is
cancelled hands the next run one `agent_state` key, `acp_retryable_prompt_user_message_id`, persisted with the
state [run].

```
Stop       _arun, except CancelledError (:2642): in-flight prompt A neither superseded nor completed
             → agent_state[acp_retryable_prompt_user_message_id] = A.id          (dr-2 kept nothing)
Next run   _arun's opening lock block (:2252), ACP agents only → _supersede_retryable_acp_prompt() (:726)
             a prompt message follows A   → cursor := A.id    → the run sends the message after A
             A is the last one (▷)        → cursor unchanged  → the run sends A again
             A not on the active branch   → cursor unchanged  → as on dr-2
           the key is removed in every case; with no key the method writes nothing
```

- All four rows behave as the design's §4 table says, with the method called directly [run]. The key is gone
  after run 2 in both probes [run].
- Nothing else changed: the diff is four hunks in this file (constant, method, call, handler). The selection, the
  post-step commit, the error path, `EventService` and the bridge are untouched [read].
- No public surface changes: the constant is not exported and the method is private [read]. There is no schema
  version, golden fixture or TypeScript change.

The tests are design §5.1's four, under its names; each asserts the prompts the agent was sent. Three are in
`test_conversation_send_message.py` (a newer message, ▷, a reload from disk). One is in `test_event_service.py`
(Canvas's path: run, interrupt, `send_message(run=True)`). Upstream's "retryable" test is unchanged and passes
[run].

## 2 · Divergences from the design

1. **The method checks for the key, then pops it from a copy** (reported). This meets the design's text [run]. It
   differs from the designer's probe patch (`pop` with a `None` default) only for a key stored as `None`, which
   the one writer never stores [read].
2. **Two test names carry `# noqa: E501`** (reported). They are the design's names, too long for the `def` line.
   Six other test definitions in the fork are marked the same way [read]; ruff and pycodestyle pass [run].
3. **An in-file fixture, `acp_prompts_first_blocks`, and two helpers serve the three SDK tests** (reported). The
   neighbours inline everything, and the fork's `AGENTS.md` asks for shared mock setup in `conftest.py`. The
   event-service test inlines the same blocking `astep`, so the commit holds that stub twice [read].
4. **One commit holds the tests and the fix** (reported). The design names no split. Red is shown by running the
   new tests on `dr-2`'s code [run].
5. **Size** (not reported). Design §8 estimated ≈ 35 code and ≈ 130 test lines; the build has +34/−6 and +162,
   about 1.2 times the estimate, the excess in tests.

## 3 · Measured results

No live tier: design §5.3 adds no live test, since no model behaviour changes.

| Check | `dr-2` `34c540c` | `d878bbb` | Mark |
|---|---|---|---|
| The 4 design tests (`-k stopped`) | 3 fail with `['stop me', 'stop me', …]`; the ▷ test passes | 4 pass | run; the Implementer's `red.txt`, `green.txt` agree |
| Both touched test files | 143 pass (the 4 excluded) | 147 pass | run |
| `tests/sdk` + `tests/agent_server`, 4 workers | 9163 passed, 13 failed | 9163 passed, 17 failed | read: the Implementer's logs |
| Those failures, run alone | 5 fail: OpenRouter model lists | the same 5 | run |
| Bridge probe: Stop, then a message on the socket | run 2 sent `Spin.`, then the question | run 2 sent only the question | dr-2 read; fix run |
| Bridge probe: Stop, then ▷ (`POST /run`) | run 2 sent `Spin.` | run 2 sent `Spin.` | dr-2 read; fix run |
| TASK-57 `read_turns` on the socket probe's logs | 4 turns, `Spin.` twice | 3 turns, `Spin.` once, stopped | run |
| D5: `close()` mid-prompt, reload, new message | the cut-off prompt sent twice | sent once | run |
| Trial merge with TASK-46's `1f1a381` | | clean, tree `4c4ef73` | run |
| ruff, pycodestyle, pyright, the fork's 3 hook scripts | | pass | run |

The other wide-run failures, 12 with the fix and 8 on `dr-2`, pass alone. They depend on order:
`test_openapi_discriminator.py` fails all 5 of its tests right after `test_execute_tool.py`, on both sides [run].

**To reproduce:** in the SDK worktree, `UV_FROZEN=1 .venv/bin/python -m pytest
tests/sdk/conversation/local/test_conversation_send_message.py tests/agent_server/test_event_service.py -k stopped`.
For the baseline, add `PYTHONPATH` naming an export of `dr-2`'s four package directories. Plain `uv run` and
pre-commit re-resolve `uv.lock` on uv 0.8.17. The probe is the System Designer's `probe_stop.py` and
`seam_turns.py`, in the session scratchpad's `task-69-design/`, not committed; `test_stop.py` replaces them.

## 4 · Not verified, and out of scope

- **Canvas's window.** No browser rendered the events. The probe makes Canvas's own calls (socket send,
  `POST /interrupt`, `POST /run`), as design F1 did.
- **A Stop before the prompt reached dr-acp** (design §9.4) was not probed.
- **Out of scope, unchanged.** The cursor still re-runs an errored or stuck prompt before the next message: the
  error path writes no key, and the post-step commit still skips `ERROR` and `STUCK` [read]. dr-acp's
  `ROOT_STOPPED` sentence ("Stopped. … Your next message starts a fresh run.") is not among the agent-server's
  events in the probe [run]; the bridge drops a cancelled turn's text (design F7) [read].

## 5 · Seams

- **TASK-46 and `dr-3`.** TASK-46's `fix/title-llm-without-credentials` (two commits on `dr-2`, ending `1f1a381`)
  shares no file with this fix, and the trial merge is clean. As of the last fetch, these two are the only fork
  branches ahead of `dr-2` [run]. This pull request must merge before Michael tags `dr-3` (design §7.1).
- **TASK-57.** No file overlap. `read_turns` ran at `task-57-recap` `c0e56c8`; the design read `c44dcc4`, and
  `recap.py` changed between them.
- **deep-reasoning.** `test_stop.py` lands after TASK-57 and the pin move, in its own pull request (design §7.2).
  This branch holds only this document and the sdist exclusion of `as_built/`.
