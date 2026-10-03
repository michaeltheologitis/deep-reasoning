# D1 · `dr-acp`, as built

**TASK-2** · Cartographer · the code at `2a15388` (head of `v1-dr-acp`, pushed; this file is on
`as-built/d1`) · checked against the design at `c8d7fbb` (`docs/design/d1-dr-acp.md` v3, unchanged
at `2a15388`; the revision being written on `refactor/d1` is not read here) · deep_reasoner_beta
`d7334ae` · agent-client-protocol 0.12.1 · genai-prices 0.1.9 · 2026-10-03.

This version replaces the one at `b67aa29`, which read `21f4a8b` against v2 (`f281109`). Since
then: design v3, which took in that version's D-1 to D-15, and the fourteen commits
`c8d7fbb..2a15388` (the literate refactor `77c65f6..65428c4`, two rulings of Michael's in
`96926d0` and `e00a78f`, and his request in `2a15388`).

**Revised 2026-10-03, after Gate C was called**, for `72d9588` (E1's reference; a tenth scenario)
and `0053bbf` (the live tier's failure messages), on `v1-dr-acp` and in #7 and #8. Both touch only
`tests/acp/`; `src/` is as at `2a15388` [run]. Revised: D-12 (now in §2.1), §1's counts, §4.7's
Expectations paragraph, §6.1, §6.2, §6.4, §6.5, §6.8, §7. The design on the branch is v4
(`554fccb`), whose text on these points is v3's; `design/d1-e1` is not read. In the revised
passages, [run] means run at `0053bbf`.

**Evidence marks.** Every claim carries one.
- **[run]**: executed in this sandbox at `2a15388`: the full suite
  (`DR_BETA_CHECKOUT=/home/user/deep_reasoner_beta uv run pytest`: 233 passed, 4 deselected,
  397 s, at a load average of about 13 on 4 CPUs, from other agents' suites), `ruff`, `uv build`,
  a REPL call, or an uncommitted script that drives a real `dr-acp` over stdio against
  `FakeOpenAI` through `tests/acp/harness.py`.
- **[CI]**: read from GitHub's logs of the CI and live runs, at `2a15388` unless another commit is
  named. I ran no paid model and no real `claude` CLI.
- **[read]**: read in the code or in a commit message, **not executed**. Weaker evidence than
  [run]; §7 lists the load-bearing ones. A measurement another agent made and I did not repeat is
  marked [read] and names the commit that reports it.

**Reading order.** §2 first (divergences: §2.1 is what departs from the design as it stands), then
§1 and §3–§5 as a map, §6 (the experiments as measured), §7 (what I could not verify).

---

## 1 · What exists

`dr-acp` is a stdio ACP agent. One front process (asyncio) serves one ACP connection and any number
of root sessions on it; each root session has at most one live deep_reasoner **run**, executed in a
**worker** subprocess in its own process group. The worker turns deep_reasoner's structlog events
into **RunEvents** and writes them to a pipe; the front appends each to the run log, then encodes it
as ACP updates. [read; run end to end by every test that spawns `dr-acp`]

```text
ACP client ── stdio, JSON-RPC lines ──▶ front: wire.serve ─ agent.DrAcpAgent ─ session.Session ─ supervisor.RunHandle
                                                                                   │ control pipe ▲ event pipe
                                         worker: runner.Worker ─ recorder.Recorder ─ stop.InterimStop | DeanStop
pump (one task per run): event line ─▶ RunLog.append (runs/<run>/events.jsonl) ─▶ Encoder.feed ─▶ Outbox.update
```

| Part | Non-blank lines of `.py` | Where |
|---|---|---|
| front and worker | 2,719 | `src/deep_reasoning/acp/`, `…/acp/worker/` |
| client-side helpers, shipped in the package | 424 | `src/deep_reasoning/acp/testing/` |
| tests | 4,082, plus 622 lines of golden recordings (at `0053bbf`) | `tests/` |

Counted the Refactorer's way (non-blank lines of `.py` files under `src/` and `tests/`):

| Commit | Source | Tests |
|---|---|---|
| `c8d7fbb` (same code as `21f4a8b`) | 3,301 | 4,135 |
| `65428c4`, the literate refactor's last | 3,261 | 3,886 |
| `96926d0`, genai-prices | 3,276 | 3,942 |
| `e00a78f`, display helpers deleted | 3,143 | 3,855 |
| `2a15388`, Claude Code test | 3,143 | 4,010 |
| `0053bbf`, E1's `unanswered` | 3,143 | 4,082 |

The shipped `src/deep_reasoning/acp/prices.yaml` (11 lines) is gone. [run]

241 tests at `0053bbf`: 237 deterministic (no network beyond 127.0.0.1), 4 marked `live`. [run]

The front imports neither deep_reasoner nor OpenHands at start-up: after importing `cli`, `agent`,
`supervisor` and `wire`, no `deep_reasoner*` or `*openhands*` module is loaded. It does import
genai-prices, through `costs.py`, which `runlog.py` imports. [run] deep_reasoner is imported by the
front only inside `ConfigCatalog`'s methods (in a thread), and by the worker. [read]

---

## 2 · Divergences from the design

The design at `2a15388` is v3 (`c8d7fbb`). v3 took in D-1 to D-15 of this document's previous
version, as its §3.2 B1–B18 and §3.3 C1–C2; §2.2 keeps them, each with where v3 records it and
whether it still holds. §2.1 is what departs from v3: D-16, which v3 did not take in, what the
fourteen commits after it changed, and D-12 as `72d9588` revised it. The changelog holds no
`drift:` line for TASK-2 [read: the
Changelog database, queried 2026-10-03]; every item below was found from the code. "Design §x" and
"v3 §x" cite `c8d7fbb`.

### 2.1 Where `2a15388` departs from v3

**Behaviour a client or a user sees**

**D-9 · Costs come from genai-prices' bundled data; the shipped `prices.yaml` is gone.** (This
supersedes the previous D-9, gpt-6-luna's price from secondary listings, which v3 recorded as
B16.) `PriceTable.estimate` (`costs.py:84–114`) takes the provider's `usage["cost"]` when there is
one (source `provider`); else the `$DR_HOME/prices.yaml` entry whose key is the model id, or the
longest glob that matches it; else genai-prices; else `usd None`. genai-prices is read through a
`DataSnapshot` of its bundled data built at import with `from_auto_update=False`
(`costs.py:18–20`), called as `calc(usage, model, None, None, None)`: no provider, and no request
timestamp, so the price is the one in force when the worker prices the call. A home entry and
genai-prices both give source `table`, and the context window comes from whichever priced the call,
also when the provider reported the cost. `PriceTable.load` reads only `$DR_HOME/prices.yaml`
(`costs.py:67–73`). Claude calls do not go through it: their cost is `claude.call`'s `cost_usd`,
source `claude` (`recorder.py:327–343`). genai-prices 0.1.9 prices gpt-6-luna at $0.10 in and
$0.50 out per million tokens up to 272K input tokens, and the whole call at $0.20 and $0.75 above,
with a 1,050,000-token window. Matching is by model id alone: `openai/gpt-6-luna` and `sonnet` are
unknown to it. `genai-prices>=0.1.9,<0.2` is a runtime dependency (`pyproject.toml:10`), locked at
0.1.9; it adds about 0.2 s to the front's import of `agent` (1.1 to 1.4 s here, under load).
Design v3: §4.1 ships `prices.yaml`; §4.7's `PriceTable.load` lays `$DR_HOME/prices.yaml` over the
package's table, which holds gpt-6-luna at $0.10 and $0.50 flat (B16, §10 item 1); §8.5's
dependencies and §9's rows have no genai-prices. Reason (commit `96926d0`): Michael's ruling of
2026-10-03, "no, stick to what genai-prices gives us", after the Scout found that the shipped table
underpriced prompts above 272K input tokens (300K in and 10K out: $0.0675, not $0.0350). The
override stays because D5's design relies on it, and the test harness prices `fake-model` through
it (`harness.py:37–45, 174–176`). [run: `test_costs.py`'s 12 tests, including one that prices a
call in a fresh interpreter with DNS and connect refused and checks no thread was started, and one
that swaps genai-prices' process-wide snapshot for an empty one and still prices from the bundled
data; REPL: gpt-6-luna at 100K/10K → $0.015, at 300K/10K → $0.0675, window 1,050,000;
`claude-sonnet-4-5` at 1,000/100 → $0.0045; `openai/gpt-6-luna`, `sonnet` → `usd None`; `-X
importtime`]

**D-19 · In the interim, the parent's cell output can name a sibling that was not stopped.**
`StoppedByUser`'s message names every sibling running in the target's `run_all` as "stopped with
it", relying on `gather` to cancel them (design §6.3, §9 R14). A sibling whose `openai` call is
cancelled mid-response can swallow the cancellation and run on to `done`: the message names it, and
its idle update says `done`. CI run
[37086285097](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37086285097), at
`1652b5a` (the code of `21f4a8b`), failed in this test: the agents marked `collateral` were 18 of
D0's 19 siblings (#4 missing), and the root's cell output did not end with the sentence built from
them (1 failed, 229 passed) [CI; the log elides the output's start]. The Refactorer's run logs show
the cause, a sibling named in the message that ran on to `done`; its measurements (commit
`ffa97f3`): the interim test failed in 2 of 12, then 4 of 15 runs with eight busy processes
on four CPUs; apart from `dr-acp`, of 20 tasks calling `FakeOpenAI` and cancelled at a random
moment, 4 of 600 ran to completion unloaded and 43 of 600 under load (httpx 0.28.1, httpcore 1.0.9,
anyio 4.15.1) [read: not repeated here]. The code did not change; the test did: `FakeOpenAI` now
holds D0's 19 siblings at their first model call until the root's next turn, which comes only after
`run_all` has ended, so each sibling is awaiting its model when D0's stop ends `run_all`
(`test_stop.py:54–70`). The assertion is unchanged; the Dean-stop test keeps the plain plan. Design
v3's E3 null (§8.1) fails a sibling cancelled without the message naming it; it says nothing of a
sibling named but not cancelled. [read; run: the held test passes in this sandbox's suite at a load
average of about 13]

**The client-side helpers and the proof**

**D-12 · E1's reference takes an agent that never got a reply from our run log** (revised
2026-10-03, at `0053bbf`). `scenarios.deep_reasoner_tree` (`scenarios.py:278–319`) reads
deep_reasoner's files as before (agents from `llm_calls.jsonl`, kind `agent` or a fork's
code-writing kind-`llm` node, and from `claude_calls.jsonl`; cells from the `<repl>` turns of the
node YAML's conversation), then adds each agent our run log starts that has no `usage` event there,
under its run-log ancestry, with its `cell.end` count (none, for a child that never got a reply). An
agent with a `usage` event that deep_reasoner's files lack is still a difference. deep_reasoner
writes nothing for an agent until one of its model calls returns (§4.7), while the stream announces
and closes every agent (design §5.2). **For such agents the reference is our own run log, not a
record independent of the stream's source.** A Claude Code agent's files give no cells, so D-18's
tests compare only its parent links and count cells against the run log and the transcript. A
failed comparison prints both trees and each disputed agent's run-log events, long texts cut to 300
characters at each end (`scenarios.tree_evidence`; `test_agent.py:83`, `test_live.py:57`). E1 gains
a tenth scenario, `unanswered` (§6.2). Design v4 (`554fccb`, as v3): §3.2 B14 and §8.1's E1 row read
agents from the two files only; B14, §8.1 and §8.3 say nine scenarios. Reason (commit `72d9588`):
live run 37149393726 (§6.8). [run: on `unanswered`'s two run directories the previous function
returns `{1: (None, 2)}` and this one `{1: (None, 2), 2: (1, 0), 3: (1, 0)}`, the stream's tree; on
run 37149393726's, `{1: (None, 3)}` and the stream's `{1: (None, 3), 2: (1, 0), 3: (1, 0)}`; the
suite]

**D-17 · The client-side helpers keep no display.** `Printer` is `updates`, `subagents` (a plain
`dict` by full session id), `commands` and `wait_until()` (`testing/client.py:115–169`). There is
no `lines`, no `show()`, no line format, no `SubagentMap` and no `Subagent.short`, so
`printer.subagents["n2"]` raises `KeyError`. `Tree` is its `runs`, with no `__str__` and no
drawing (`testing/tree.py:54–56`). `outcome_phrase` keeps its 40-character cut of a failure's
detail, and the tree's nodes keep their short ids; `ids.short` is now read only by
`testing.tree`. Design v3: §8.2's `Printer` (`lines`, `show()`, `SubagentMap`), its line-format
table and the drawing table; §7 lists `SubagentMap`; §4.1 says `ids.py` holds "the short forms the
printer uses"; §8.1's unit row tests "`Printer` lines … and `tree()` drawings". Reason (commit
`e00a78f`): Michael's ruling of 2026-10-03, which deleted them as having no reader once the
live-doc notebook was gone. [run: REPL (`KeyError: 'n2'`, no `show`, no `lines`, `Tree` without
`__str__`); `test_client.py` (13 tests) and `test_tree.py` (4) pass]

**D-18 · The live tier has a fourth test: Claude Code on Sonnet, on Michael's subscription.**
`tests/acp/test_claude_code.py` asks `What is 17 times 23?` of a config whose reasoner is
`claude_code` with model `sonnet`, `max_budget_usd: 0.5`, `timeout_s: 180` and no tools, plus a
loopback chat client that nothing calls (deep_reasoner builds one for every run)
(`test_claude_code.py:22–39`). The live test (`:164–178`) runs the installed `claude` through a
wrapper that exports `CLAUDE_CODE_OAUTH_TOKEN` from `DR_ACP_LIVE_CLAUDE_TOKEN` (`:69–83`), since
deep_reasoner strips every `CLAUDE_CODE*` variable from a Claude child's environment
(`claude_code.child_env`, `v2/claude_code.py:285`); it skips without the token and fails if
`ANTHROPIC_API_KEY` is set. A deterministic twin (`:150–161`) runs the same config against a fake
CLI that runs two snippets through `dr repl exec` and checks it was called with `--model sonnet`.
Both assert: the answer contains `391`; the root's `agent.start` has backbone `claude_code`, and
every `usage` is a `claude` call on `sonnet`; the rebuilt tree's agents and parent links equal
deep_reasoner's; the root's cell count equals its `cell.end` events, the last cell calls
`FinalAnswer`, and the cells appear in order among the `dr repl exec` snippets of the session's
transcript. `live.yml` now also requires the `CLAUDE_CODE_OAUTH_TOKEN` secret, sets up Node 22 and
installs `@anthropic-ai/claude-code@2.1.285`. Design v3 §8.4 and §8.5: three live tests on
gpt-6-luna, `live.yml` failing only without `OPENAI_API_KEY`, two secrets. Reason (commit
`2a15388`): Michael's request of 2026-10-03. [read; CI: §6.8; run: the twin passes]

**D-16 · The weekly tripwire against Dean's `main` has never run.** `acp-tripwire.yml` exists only
on `v1-dr-acp`; GitHub registers `ci`, `live`, `token-check` and `fork-live` (the last another
task's) for the repo, and `main` (the default branch, from which GitHub fires `schedule`) holds
`live.yml` and `fork-live.yml`. Design v3 §8.1 E4 and §8.5 still run it weekly. [run: GitHub's
workflow list through the GitHub MCP tools, `git ls-tree main .github`]

**Signatures**

**D-20 · Signatures v3 gives that the cleanup changed.** None changes behaviour; each reason is
its commit's. [read; run: the suite]

| Design v3 | Built at `2a15388` | Commit |
|---|---|---|
| `StopReceipt`; `StopAdapter.stop`, `DeanStop.stop` and `InterimStop.stop` return it (§6.3) | no `StopReceipt`; each `stop` returns `None`; the `stop.accepted` event carries node, mode, accepted and reason (`stop.py:34–69`) | `5a0a5a8`: the worker's control thread discarded the receipt |
| `Recorder.note_stop(…) -> StopReceipt`; `Recorder.arm(node)` (§7) | `note_stop(…) -> None`; no `arm`: `InterimStop.stop` calls `note_stop(node, "interim")` (`recorder.py:150–170`, `stop.py:68–69`) | `5a0a5a8` |
| `RunHandle.child(session_id)` (§4.2) | gone; `Session.stop_child` asks `run.encoder.child` | `d4d7930` |
| `Session.stop_child(…) -> None` (§4.2) | `-> bool`: whether the live run has a child of that id, running or not (`session.py:234–240`); `DrAcpAgent.cancel` logs the id as unknown when no session claims it (`agent.py:193–198`) | `d4d7930` |
| — | `Session.menu() -> Update`: the session's `available_commands_update`, empty once started (`session.py:117–119`); sent after `session/new`, `session/load` and `set_config_option` (`agent.py:90, 180`) and at the first prompt (`session.py:184`) | `70e1988` |
| `Outbox.observe(fn)` (§4.2) | gone (`wire.py:40–63`) | `b2fb48a`: nothing called it (v3 B10 put the schema check on the client) |
| `PriceTable.load`: "The package's prices.yaml, with $DR_HOME/prices.yaml over it." (§4.7) | `$DR_HOME/prices.yaml` only, laid over genai-prices in `estimate` (D-9) | `96926d0` |
| `Printer.lines`, `Printer.show()`, `SubagentMap`, `Subagent.short`, `Tree.__str__` (§8.2) | gone (D-17) | `e00a78f` |

Moves the design does not name: one `detail_of` and `DETAIL_CAP = 2000`, in `runlog.py:17–23`,
replace the identical copies in `session.py` and `worker/runner.py` (`77c65f6`); the encoder's
private `_dr` and `_closed_card` are inlined into `_meta` and `_agent_end` (`a597668`); docstrings
that named their callers or restated their bodies are rewritten, prose only (`89f1ad3`); the
encoder, recorder and stop tests are rewritten with the same cases and names (`42733ad`,
`83344a1`, `65428c4`). [read]

### 2.2 Divergences from v2 that v3 took in

Each is the previous version's, found against v2 (`f281109`); "v3:" names where v3 records it.
Citations are to `2a15388`. Each holds at `2a15388` unless the entry says otherwise.

**D-1 · The task is the first text block, not all of them.** v3: B1. `agent.user_text`
(`agent.py:36–47`) takes the prompt's first `text` block plus each `resource_link`'s uri on a line
of its own; every later text block is left out of the task and logged in `prompt.start.dropped`
(`runlog.py:51`). v2 §4.2 step 2 joined all text blocks with `"\n"`. Reason (commit `db47b5e`):
OpenHands' bridge sends the user's message as one block, then the turn's extensions and, on the
first prompt, its system suffix (with the `<CUSTOM_SECRETS>` list), each as a block of its own.
[run: `user_text([first, second, link, third])` → `("first\nfile:///a", ["second", "third"])`;
`test_what_openhands_appends_to_a_prompt_never_reaches_the_task_and_is_logged` also checks none of
it reaches the model]

**D-2 · `usage_update._meta.deep_reasoner.cost_source` can be `"mixed"`.** v3: B8. When a
session's total includes calls priced from more than one source, the encoder reports `"mixed"`
(`encoder.py:72–76`). Since D-9, a home entry and genai-prices are one source (`table`). No test
covers it. [run: REPL, two calls priced `table` and `provider` → `"mixed"`; grep finds no test]

**D-3 · The worker's environment also loses `OPENHANDS_AUTOMATION_API_KEY`.** v3: B2.
`ALWAYS_REMOVED` (`route.py:29–34`) has four patterns; v2 §4.7 had three. Reason (commit
`21f4a8b`): Canvas's launcher puts the agent-server's session API key there, the bridge passes its
environment to `dr-acp`, and the key opens the agent-server's whole API. [run:
`test_the_agent_servers_secrets_never_reach_the_worker`]

**D-4 · After SIGTERM the worker sends nothing more.** v3: B4. The worker's SIGTERM handler mutes
the recorder before raising `RunKilled` (`runner.py:115–117`, `recorder.py:189–192`). So after a
root Stop, or a `closed` end that had to be forced, the run log holds no `agent.end` or `cell.end`
for the agents the signal unwound; the front's `run.end` alone ends them on the wire (§4.5).
deep_reasoner logs `agent.end failed` on any `BaseException` that leaves a drive
(`v2/agent.py:899–905`), so without the mute those would reach the client. [run: a root Stop during
the root's own busy cell left `run.start, prompt.start, worker.ready, agent.start, usage,
cell.start, run.end stopped`, exit 0, three times; under 20 spinning children the log held no
`agent.end` or `cell.end`, exit −9, and every child reached the client idle `cancelled` with
`status: stopped`, all from `run.end`, three times]

**D-5 · `session/close` and shutdown do not take the session lock.** v3: B18. The lock serializes
`prompt` (`session.py:144`), `set_config_option` (`agent.py:176`) and the replay in `load_session`
(`agent.py:161`); `close_session` (`agent.py:200–203`), `close_all` (`:205–207`) and the close
inside `load_session` (`:145`) call `Session.close` without it. Consequence: a `session/close`
during a prompt ends that prompt. [run: `session/close` during a hanging root cell returned after
2.05 and 2.13 s; the prompt answered `cancelled` with outcome `closed`; `run.end closed`, exit 0]

**D-6 · A forked agent's own LLM and REPL are attributed to the fork.** v3: B5.
`Recorder._working_for` (`recorder.py:206–215`) treats an `agent.loop`/`llm.call` of kind `llm`,
or a `repl.execute` of kind `repl`, on a node directly under a known agent as that agent's own
think call or cell, when the agent has no open cell (for `llm`). Reason (commit `cbb0148`):
deep_reasoner's `fork()` branches the parent's LLM and REPL (`v2/agent.py:478–523` at `d7334ae`),
and they log on nodes of their own under the fork. [run:
`test_a_forks_own_llm_and_repl_nodes_work_for_the_fork`, and E1's `fork` scenario in both modes]

**D-7 · `DeanStop.stop` calls Dean's function first, under the recorder's lock, and only for a
running agent.** v3: B3. `stop.py:52–59`: holding the recorder's lock, `fn(node)` if the node's
current drive has not ended, then `note_stop` (which emits `stop.accepted`); it returns nothing
(D-20). Docstring's reason: `stop.accepted` marks the moment the stop is in force, and no
`agent.end` is classified between the two. The recorder's `holding()` and `running()`
(`recorder.py:172–180`) support it. [read; the path runs in
`test_dean_stop_ends_the_branch_and_the_parent_keeps_every_siblings_result`, run]

**D-8 · No live doc: a live test tier instead.** v3: B17, and §8.4. v2 §8.4 and §8.5 had the
Docwright run `docs/dr-acp.ipynb`, a `docs` dependency group and a `live-doc.yml` workflow. Built:
four `@pytest.mark.live` tests (three in `tests/acp/test_live.py`, one in `test_claude_code.py`,
D-18), deselected by default (`pyproject.toml:44–45`), run by `live.yml` on demand. There is no
`docs` group, no `live-doc.yml`, and no notebook: v3's commit `1fef880` deleted it. [read; run:
`ls docs`]

**D-9** is superseded; see §2.1.

**D-10 · `structlog` is a direct dependency, and the front configures it.** v3: C1, B17.
`pyproject.toml:13`; `cli.configure_logging` sets up structlog and stdlib logging, both to stderr
(`cli.py:56–72`). [read]

**D-11 · Tests are laid out per module, not per experiment.** v3: C2. v2 §8.1 named
`test_tree_fidelity.py`, `test_stdio_integrity.py`, `test_tripwire.py`, `test_schema.py`,
`test_surfaces.py`, `test_load.py`; none exists. The experiments live in the module tests, mapped
in §6. `test_claude_code.py` is named for deep_reasoner's backbone, not for a module of ours.
[read]

**D-12** (E1's reference, v3's B14) is revised: since `72d9588` it also reads our run log; see
§2.1.

**D-13 · E3's null is relaxed to "at most one call per branch agent after the stop".** v3: B12.
`test_stop.py:108–111` allows each branch agent at most one model call that starts after
`stop.accepted` was logged ("A turn that began before the stop may still make its call"); the live
test bounds the total: no more `usage` events from the branch after the stop than the branch has
agents (`test_live.py:123–126`). [read]

**D-14 · The schema check sits in the test client, not on the `Outbox`.** v3: B10.
`harness.DrAcp.observe` (`harness.py:126–136`) validates every message the client receives from
`dr-acp` (updates, responses, errors) against the vendored schema. `Outbox.observe` itself is now
gone (D-20). [read]

**D-15 · Golden normalization.** v3: B13. `golden.py:34, 61–89`: run ids become
`00000000-000000-000000`, root ids `s-0000000000000000`, install paths `SITE`/`STDLIB`/`TMP`,
amounts are rounded to 10 decimals, and only each session's **last** `usage_update` is kept. [read]

The signatures v2 gave and the build changed, all taken into v3 by B15, at `2a15388`. None of
these changes behaviour beyond the items above. [read]

| v2 | Built |
|---|---|
| `Options.home: Path` | `Path \| None` (`cli.py:22–24`); `Home.resolve` applies `$DR_HOME`, then `~/.deep-reasoning` (`runlog.py:175–182`) |
| `serve(make_agent, *, acp_out_fd, stdin_fd=0)` | adds `flat=False`, `shutdown_grace_s=0.3` (`wire.py:81–88`) |
| `Session.prompt(text)` | `prompt(text, dropped=())` (`session.py:137`) |
| `RunHandle.start(…)` | adds `decomposition` (`supervisor.py:82–95`); `run.start.source` also carries `namespace` (`supervisor.py:125–130`) |
| `RunHandle.prompt(index, text, task, decomposition) -> PromptEnd` | adds `dropped`; returns `PromptEnd \| RunEnd`, the `run.end` of a run stopped, closed or crashed under the prompt (`supervisor.py:251`) |
| `PromptStart` | adds `dropped: list[str] = []` (`runlog.py:51`) |
| `Recorder(sink)` | `Recorder(sink, prices)`; adds `holding`, `running`, `mute` (`recorder.py:117, 172–192`) |
| `CostLedger` in `encoder.py` | in `costs.py` (`costs.py:23–28`) |
| `Encoder` | adds `prompt_in_flight`; the menu, option, closing-message and idle-usage builders are module functions in `encoder.py` |

---

## 3 · The public surface, from the code

**Command line.** [run: `test_cli.py`]

```text
dr-acp --config PATH [--home DIR] [--flat] [--heartbeat SECONDS] [--log-level LEVEL]
```

Without `--config`: exit 2, stdout empty, stderr `dr-acp needs --config PATH (a dr main.yaml) until
the Library exists.` Defaults: heartbeat 60 s, level `WARNING`. `--flat` wins over a client that
advertises `subagents` [run]. The worker is `python -m deep_reasoning.acp.worker --control-fd N
--events-fd M`, started only by the front.

**ACP.** `initialize` answers exactly design §5.1's object (`loadSession`, no image/audio/embedded
context, `mcpCapabilities` http and sse false, `sessionCapabilities.close`, agent `dr-acp` 0.1.0,
no auth methods). [run] Native mode iff `clientCapabilities.subagents` is an object and `--flat` is
off. [run] Implemented: `session/new`, `session/load`, `session/set_config_option` (one option,
`namespace`), `session/prompt`, `session/cancel`, `session/close`; `session/fork` answers -32601
[run]; `resume` and `list` are left to the router [read]. Every prompt response carries
`_meta.deep_reasoner.{run, outcome}`. Refusals carry the §5.6 sentence as `message` and
`{"deep_reasoner": {"error": NAME}}` as `data`: `UNKNOWN_SESSION`, `UNKNOWN_OPTION`,
`UNKNOWN_NAMESPACE`, `NAMESPACE_FIXED` (-32602), `PROMPT_BUSY` (-32600) [run], `CATALOG_ERROR`
(-32603) [read]. Every sentence of design §5.6 matches `texts.py` verbatim: the seven constants,
the twelve with fields, the three stop acknowledgements and the `StoppedByUser` forms [run: an
uncommitted script that parses §5.6's table and calls `texts`; `test_texts.py` pins the ones with
fields].

**Ids** (`ids.py`), all derived from the run id `YYYYmmdd-HHMMSS-<6 hex>` (UTC): root session
`s-<16 hex>`, child session `<run>-n<node>`, cell `<run>-n<node>-c<k>`, flat card
`<run>-n<node>-a<drive>`, task and answer messages `-t<drive>` / `-r<drive>`. `ids.short` maps them
to `root`, `n2`, `c2.1`, `a2.1`, one way; only `testing.tree` uses it. [run: `test_ids.py`; read]

**Files** under `--home`, else `$DR_HOME`, else `~/.deep-reasoning`: `sessions/<session>.json`
(written atomically, first at the first prompt); `runs/<run>/events.jsonl` (the run log),
`worker.log` (the worker's stdout and stderr), and deep_reasoner's own `llm_calls.jsonl`,
`claude_calls.jsonl` and node YAMLs; and, if present, `prices.yaml`: per model id or glob,
`input_per_mtok`, `output_per_mtok` (USD per million tokens) and `context_window`, laid over
genai-prices (D-9). [run]

**The run log.** One JSON object per line, `v: 1`, `seq` gap-free from 1, `t` in Unix seconds, and
one of 13 kinds: front-written `run.start`, `prompt.start`, `stop.request`, `run.end`; worker-sent
`worker.ready`, `agent.start`, `thought`, `cell.start`, `cell.end`, `usage`, `stop.accepted`,
`agent.end`, `prompt.end`. `run.end.reason` is one of `closed`, `stopped`, `crashed`, `failed`,
`build_failed`, `lost`. Text fields are capped at 8 MiB, head and tail kept. [run: `test_runlog.py`,
`test_text_over_8_mib_keeps_its_head_and_tail`]

**`deep_reasoning.acp.testing`** (shipped in the wheel, never imported by `dr-acp`): `Caps` and
`ShimConnection` (put `subagents` on the wire and hand the unstable updates to the client);
`Printer` (records every update as wire JSON in `updates`, the latest of each sub-agent in
`subagents` by full session id, each root session's latest menu in `commands`, and `wait_until()`;
D-17); `tree()` (rebuilds each run's tree from updates alone, native or flat, as data); `FakeOpenAI`
(a chat completions endpoint on 127.0.0.1). [run: `test_client.py`, `test_tree.py`,
`test_fake_model.py`; `uv build`: the wheel holds `testing/`]

---

## 4 · Structure and seams

### 4.1 The front

- **`cli.main`** dups fd 1 for ACP, points fd 1 and `sys.stdout` at stderr, and only then imports the
  rest. [run: `test_a_print_while_the_front_imports_cannot_corrupt_the_stream`, an import hook that
  prints to stdout and to fd 1 while the front imports]
- **`wire.serve`** builds `acp.connection.Connection` around a handler that reads
  `initialize`'s raw `clientCapabilities.subagents` before handing every message to
  `build_agent_router(agent, use_unstable_protocol=True)`. `Outbox` is the only send path: raw dicts
  through `send_notification`, dropped silently once the client has closed the pipe (the run log still
  has them). Shutdown starts on stdin EOF or SIGTERM, closes every live run concurrently with a 0.3 s
  grace, and exits 0. [run: `test_wire.py`, and §6.3's script]
- **`agent.DrAcpAgent`** routes the ACP methods. `session/new` reads a catalog snapshot in a thread,
  answers, and sends `session.menu()` from a task created in the handler, so it follows the response
  (ACP Python's P6). `cancel` routes a root id to `Session.stop_root`; any other id is offered to each
  session's `stop_child`, which stops the child's branch if it is running and says whether its live
  run has that child; an id no session claims is logged at WARNING. [run:
  `test_cancel_with_an_unknown_id_is_ignored_and_logged`, and the stop tests]
- **`session.Session`**, one per root session: the namespace, the menu (and `menu()`, its update),
  the `started` flag, the run ids, the cost carried over finished runs, and `last_end`, which picks
  the next run's notice. Its prompt parse is design §4.2 step 3 to the letter: a leading `/name` in
  the current menu is a command; one in any menu offered before, once started, is a late command
  (rejected, nothing runs, no run log holds it); anything else, a path such as `/home/…` included,
  is the task. [run: `test_session.py`] `load_session` rebuilds the cost and `last_end` from the run
  logs during replay; the index's own `cost` is written but not read back. [read] A replay is
  encoded in the **loading** connection's mode, not the mode `run.start` recorded. [run: the native
  `fanout2` run replayed to a flat client arrives on the root session only, as 2 cards and 5 cells,
  with no `subagent_update`]
- **`supervisor.RunHandle`**, one per live run, owns the worker process, both pipes, the pump task and
  the heartbeat task (§4.2).

### 4.2 The seam that matters: the event pipe, the pump and the run log

The front is the run log's only writer. The pump reads one line from the worker's event pipe, parses
it as a RunEvent (an unparseable line is logged and dropped), appends it with `seq` and `t`, feeds it
to the run's `Encoder`, and sends every resulting update, all under one lock, so one RunEvent's
updates never interleave with the ticker's. A second task, every `min(0.5 s, heartbeat)`, flushes
dirty usage and, while a prompt is in flight and nothing has been sent for `heartbeat` seconds, sends
the root's `usage_update`. [read; heartbeat run: `test_a_long_cell_keeps_the_root_sending_usage_on_the_heartbeat`]
Because the encoder is a pure function of the log, a replay runs the same encoder over the same events
with `replay=True` (no `capabilities` on announcements, no intermediate usage). [run: the replayed tree
equals the live one in `test_load_replays_every_run_and_marks_a_killed_one_lost`]

The control pipe carries `Start` (run, session, run dir, config path, namespace, client overrides),
`Prompt` (index, task, decomposition), `Stop` (node) and `Close`, one JSON line each
(`worker/protocol.py`). [read]

### 4.3 The worker

`runner.Worker` reads the control pipe on a daemon thread: `Stop` is handled on that thread by the stop
adapter, which returns nothing (the recorder's `stop.accepted` is the answer); the rest goes to the
main loop. Control EOF (the front died) kills the worker's process group. [read] On `Start` it turns
deep_reasoner's cache off, builds the recorder with `PriceTable.load(Home(run_dir.parents[1]))`
(`$DR_HOME/prices.yaml` over genai-prices), installs it ahead of deep_reasoner's `LogProcessor`
through `configure_structlog_fixture`, sets the SIGTERM handler and emits `worker.ready`. On the
first `Prompt` it loads the config, sets the namespace and client overrides, and, for a
decomposition, sets `cfg.task` and hands the recorder the puppeteered turns; then
`build_reasoner(…, main_decomposition=…)`. The log context and model alias stay entered for the run;
each prompt is one `reasoner.acall(task)`. A build exception ends the prompt `build_failed` and the
worker with exit 2; a drive exception, `failed` and exit 1; `Close` or SIGTERM, exit 0; each through
`close_run` under a 0.7 s watchdog that exits 3. [read; exit codes 0, 1 and 2 run: read from the run
logs of `test_a_failed_drive_…`, `test_a_missing_key_…` and §6.3's script; exit 3 not seen] The
worker does not call `load_dotenv`. [run: grep]

The front also loads a `PriceTable` and holds it as `AgentContext.prices`; nothing in the front
reads it. [run: grep for `.prices` at `c8d7fbb` and `2a15388` finds no reader]

### 4.4 Where the complexity sits: the recorder and the encoder

**The recorder** (`worker/recorder.py`, 406 non-blank lines) holds every inference about
deep_reasoner, under one re-entrant lock, on whichever thread logs. A cell is opened by its first
evidence: the root's puppeteered turn at `agent.turn`, a think reply with a `<repl>` block at
`agent.loop`, or a child starting under a parent with no open cell (`inferred`, code filled in when
the cell ends). An event's owner is its node if that is a known agent, else the deepest known agent
in its ancestry, so the `llm` tool's and a Claude session's nodes bill their agent. A second
`agent.start` for a node is its next drive. `agent.end` closes an open cell as interrupted and
classifies the end by design §6.3's table (stop targets stay armed until the target's next drive;
`collateral` marks a sibling `gather` cancelled, D-19). `note_stop` records a target and emits
`stop.accepted` for both adapters; the interim raises `StoppedByUser` at the next `agent.turn` of the
target or a member of its branch. [run: `test_recorder.py`, 21 tests, and the tripwire on the real
deep_reasoner]

**The encoder** (`encoder.py`, 554 non-blank lines) turns RunEvents into updates, design §5.2
(native) and §5.3 (flat), with one method per kind. It keeps per-agent state: open cells, drive, and
an inclusive cost tally rolled up to every ancestor; the root's total adds the cost carried from
earlier runs of the conversation. A cost is omitted while any contributing call had no price. [run:
`test_encoder.py`, 45 tests]

### 4.5 How a run ends

| End | Who writes `run.end` | Client sees | Prompt answers | Next run's notice |
|---|---|---|---|---|
| answer / exhausted (`prompt.end`) | nobody: the run stays up | closing message with the answer, root usage | `end_turn` / `max_turn_requests` | — |
| drive raised | pump at EOF; reason from the last `prompt.end`; exit 1 | `The run failed: …` | `end_turn`, `failed` | `FRESH_AFTER_ERROR` |
| build raised in the worker | pump; exit 2 | `Could not start the run: …` (with a run id) | `end_turn`, `build_failed` | none |
| `materialize` raised in the front | no run exists | the same sentence, `run: null` | `end_turn`, `build_failed` | unchanged (`last_end` is not touched) |
| root Stop, prompt in flight | `kill("stopped")`: SIGTERM to the group, SIGKILL after 0.8 s, drain ≤ 0.3 s | running children idle `cancelled`/`stopped`, open cells `Not finished: the run was stopped`, `ROOT_STOPPED` | `cancelled`, `stopped` | `FRESH_AFTER_STOP` |
| `session/close` (2 s grace), shutdown (0.3 s), `session/load` of an open session (2 s) | `Close`, then `kill("closed")` past the grace | in flight: as root Stop with outcome `closed`; between prompts: nothing | `cancelled`, `closed` | `FRESH_AFTER_CLOSE` |
| worker exited unasked | pump; detail = `worker.log` path | children idle with no `stopReason`, `status: crashed`; `The run crashed (exit code N) …` | `end_turn`, `crashed` | `FRESH_AFTER_ERROR` |
| no `run.end` found at replay | `Session.replay` appends `lost` | `(This run ended when dr-acp stopped; …)` only | — | `FRESH_AFTER_RESTART` |

[run for every row: `test_session.py`, `test_supervisor.py`, `test_agent.py`, `test_wire.py`, and the
script of §6.3; except the `materialize` row's last cell, read] Measured exit codes of a stopped
run: 0 when SIGTERM unwound the root's own busy cell, −9 when a sub-agent's cell held the main
thread in `ThreadPoolExecutor.__exit__` until SIGKILL; closed runs exit 0. [run]

### 4.6 Seams left for D2, D4, D5

- **D2: `Catalog`** (`catalog.py`): `snapshot()` and `materialize(namespace, run_dir=)`, both blocking,
  run in a thread. `ConfigCatalog` offers every decomposition in every namespace, the config's first,
  first name wins, slugs numbered on collision (`triage`, `triage-2`); description `Open with the
  '<name>' decomposition`, hint `the task`; `materialize` returns the path unchanged with
  `{"config_sha256": …}`. [run: `test_catalog.py`, including 18 of deep_reasoner_beta's own configs
  read in place]
- **D4: `Session.mcp_servers`** is stored from `session/new`/`load` and never passed on. [read]
- **D5: `ModelRoute`** (`route.py`): `DirectRoute` grants nothing; `worker_env` strips
  `ALWAYS_REMOVED` and the grant's removals, adds the grant's variables and `PYTHONUNBUFFERED=1`.
  `release(run)` is called when `run.end` is logged. [run: `test_route.py`] D5's design relies on the
  `$DR_HOME/prices.yaml` override, by commit `96926d0`'s account. [read]

### 4.7 What it relies on outside this repo

deep_reasoner (`d7334ae`). Front: `load_cli_config`, `V2Config`, `build_namespace_registry`,
`load_namespaces_from_dir`, `ROOT`. Worker: `configure_structlog_fixture`, `quiet_http_client_logs`,
`set_cache_dir`, `build_reasoner`, `close_run`, `LogProcessor`, `main_decomposition_turns`,
`messages.code`, and the event names and fields of design §6.1, plus the fork's kind-`llm`/`repl`
nodes (D-6). Tests only: `DeepReasonerAgentBase._note_drive`, `__anext__`, `_node`, `_done`,
`final_answer` (the fake of Dean's stop), `mocks.FakeCompletionClient`,
`mocks.write_fake_claude_cli`, and, for D-18, `claude_code.child_env`'s stripping of `CLAUDE_CODE*`
and `dr repl exec` as the Claude session's way to act. `tests/conftest.py` imports four
deep_reasoner modules with `pytest` hidden from `sys.modules`, because deep_reasoner runs its
notebook tests on import wherever pytest is imported. [read]

**For the Expectations row at merge: deep_reasoner's run directory has no record of an agent that
never got a reply.** At `d7334ae`, `LogProcessor` writes `llm_calls.jsonl` on `llm.call`,
`claude_calls.jsonl` on `claude.call`, and a node YAML on an `agent*` event carrying `messages`,
which in `v2/` is `agent.loop` alone (`logging_utils.py:307–330, 361–368`); all three are logged
only once their call has returned (`v2/llm_coro.py:103–111, 232–240`, `v2/claude_code.py:842–846`),
and `agent.start`/`agent.end` carry no messages (`v2/agent.py:789–801`). An agent whose drive ends
before any reply leaves nothing there, so E1 reads it from our run log (D-12;
`tests/acp/scenarios.py::deep_reasoner_tree`). [read; run: run 37149393726's run directory holds
files for node 1 only, while its run log starts nodes 1, 2 and 3]

genai-prices (0.1.9, D-9): `genai_prices.Usage`, `genai_prices.data.providers`, and
`DataSnapshot(…).calc(usage, model, None, None, None)`, which raises `LookupError` for a model it
does not know and returns `total_price` and `model.context_window`; `calc` prices at
`datetime.now(UTC)` when given no timestamp. [read: `costs.py`, and genai-prices' `DataSnapshot.calc`]

---

## 5 · Wiring

`pyproject.toml`: `deep-reasoning` 0.1.0, Python `>=3.12,<3.13`, `deep-reasoner` pinned by git to
`d7334ae`, `agent-client-protocol>=0.12.1,<0.13` (locked 0.12.1; a test pins it),
`genai-prices>=0.1.9,<0.2` (locked 0.1.9), `pydantic`, `pyyaml`, `structlog`, `ipython`; script
`dr-acp`; dev group `pytest`, `jsonschema`, `referencing`, `ruff`; `testpaths = ["tests"]`, a `live`
marker, `addopts = "-m 'not live'"`; ruff `extend-exclude = ["docs"]`; wheel `src/deep_reasoning`
only; sdist excludes `docs/` and `as_built/`. [read; run: `uv build` makes an sdist with no
`docs/`, `as_built/` or `prices.yaml`, and a wheel with no `prices.yaml`; `ruff check` and
`ruff format --check` on `src tests` pass]

Workflows: `ci.yml` (every push: `uv sync --locked`, deep_reasoner_beta's configs fetched at
`d7334ae` into `DR_BETA_CHECKOUT`, `ruff check` and `ruff format --check` on `src tests`, `pytest`);
`live.yml` (on demand: fails without the `OPENAI_API_KEY` or `CLAUDE_CODE_OAUTH_TOKEN` secret, sets
up Node 22, installs `@anthropic-ai/claude-code@2.1.285`, then `pytest -m live -v -rA`; its comment
says never `ANTHROPIC_API_KEY`); `acp-tripwire.yml` (Mondays 06:17 UTC: deep_reasoner at `main`,
`test_recorder.py` and `test_agent.py`; never registered, D-16). Secrets used: `DEEP_REASONER_TOKEN`,
`OPENAI_API_KEY`, `CLAUDE_CODE_OAUTH_TOKEN`. [read; CI: the live run's environment carries both
model secrets, masked]

---

## 6 · Experiments, as measured

### 6.1 The runs

| Run | Commit | Conditions | Result |
|---|---|---|---|
| CI `ci` [37157372658](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37157372658) | `0053bbf` | as at `2a15388` below | ruff check and format clean; **237 passed**, 4 deselected, 187.4 s [CI] |
| CI `live` [37157389645](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37157389645) | `ac2ac87`, #8's head: `src/`, `tests/`, `uv.lock`, `live.yml` as at `0053bbf` | as at `2a15388` below | **4 passed**, 220 deselected, 50.8 s; no agent went unanswered, so the run-log half of D-12 was not exercised [CI] |
| this sandbox | `0053bbf` | as at `2a15388` below; load average 15 to 20 | `test_agent.py`: **48 passed**, 243.6 s; the suite: **237 passed**, 4 deselected, 470.2 s. An earlier `test_agent.py` run with `--basetemp` under a long scratch path failed the two `claude` E1 tests with `OSError: AF_UNIX path too long`, from the socket deep_reasoner's `repl_cli_interface.serve` opens under the run directory [run] |
| CI `live` [37149393726](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37149393726) | `7eb7812`, D4's branch: D1's `21f4a8b` plus D4's own changes to `src/deep_reasoning/acp/`; `scenarios.py`'s reference and `test_live.py` as at `2a15388` | D1's three gpt-6-luna tests and D4's three live tests | **failed**: D1's tree test, `{1: (None, 3), 2: (1, 0), 3: (1, 0)} == {1: (None, 3)}`; 5 passed (§6.8) [CI] |
| CI `ci` [37144598450](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37144598450) | `2a15388` | ubuntu-latest, Python 3.12.3, deep_reasoner at `d7334ae`, beta configs present | ruff check and format clean; **233 passed**, 4 deselected, 218.8 s [CI] |
| CI `live` [37144608009](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37144608009) | `2a15388` | ubuntu-latest, Python 3.12.3, `OPENAI_API_KEY` and `CLAUDE_CODE_OAUTH_TOKEN` secrets, Node 22.23.3, Claude Code 2.1.285, genai-prices 0.1.9, no beta configs | **4 passed**, 216 deselected, 47.9 s [CI] |
| this sandbox | `2a15388` | Linux, 4 CPUs, load average about 13 (other agents' suites), `DR_BETA_CHECKOUT=/home/user/deep_reasoner_beta` (`d7334ae`) | **233 passed**, 4 deselected, 396.6 s; no failure to rerun [run] |
| earlier, code of `21f4a8b` | `21f4a8b`, `1fef880`, `1652b5a`, `c8d7fbb` | as above, 3 live tests | `ci` 37052495476 (`21f4a8b`) 230 passed; `live` 37053166300 (`21f4a8b`) 3 passed; `ci` 37086236436 (`1fef880`) passed; `ci` 37086285097 (`1652b5a`) **failed**: the interim stop test (D-19), 229 passed; `ci` 37086294973 and `live` 37086300425 (`c8d7fbb`) passed [CI] |
| earlier: `ci` 37049699113, `live` 37050366757 | `db47b5e` | — | ci failed 2 golden tests (`failing` scenario: `FakeOpenAI` counted tokens from characters, and tracebacks carry install paths), fixed in `381f81d`; live passed [CI] |

At `2a15388`, GitHub listed ten runs on `v1-dr-acp`, those from `2a15388` down; none is at the
thirteen commits between `c8d7fbb` and `2a15388`. Since: `ci` 37148543910 at `554fccb` (design
only) and 37157372658 at `0053bbf`, both passed. [CI]

Reproduce: `DR_BETA_CHECKOUT=<deep_reasoner_beta at d7334ae> uv run pytest` (the deterministic tier);
`OPENAI_API_KEY=… CLAUDE_CODE_OAUTH_TOKEN=… uv run pytest -m live` (the live tier; the Claude test
needs the `claude` CLI on `PATH` and skips without its token).

70 of the 237 deterministic tests spawn a real `dr-acp` over stdio through `tests/acp/harness.py`,
and so do the 4 live tests; in each, every message `dr-acp` sends is validated against the vendored
ACP schema 1.24.1 (sha256 checked) and every stdout line must parse as JSON-RPC 2.0 (E2, E4). [read:
counted from the code (65 at `c8d7fbb`, D-18's twin, `unanswered`'s four); run: they pass]

### 6.2 E1 · tree fidelity

`test_agent.py::test_tree_rebuilt_from_the_stream_is_deep_reasoners_own`, 10 scenarios × {native, flat}
= 20 tests: `linear` (a main decomposition, then a resumed prompt), `fanout2`, `fanout20`, `depth3`,
`namespace`, `fork`, `exhausted`, `failing` (a failing cell and a child whose model answers 500),
`unanswered` (the root's `run_all` of two children: the first's first call answers 500, and
`FakeOpenAI` holds the second's until the root's next turn, so `run_all` cancels it before any
reply; `scripted(…, held=)`, `scenarios.py:44–67, 249–266`), `claude` (deep_reasoner's fake `claude`
CLI). Each runs `dr-acp` against `FakeOpenAI` and asserts: each prompt's outcome; the tree
`testing.tree()` rebuilds from the client's updates equals the reference (per agent node: its parent
and its cell count, D-12); native: every child's announcement names a cell already sent on its
parent, nothing reaches a child session before its announcement, every prompt response follows a
root `usage_update`; flat: only the root session is used and no unstable update kind appears.
**20/20 passed** at `0053bbf` [CI, run]. Baseline beside each arm: deep_reasoner's own files for
the same run, and our run log for an agent with no model call (only `unanswered`'s two children,
which end `failed` on the 500 and on `CancelledError: ` [run]; D-12).

`test_each_stream_matches_its_golden_recording`, the same 20: per-stream sequences and the rebuilt tree
equal `tests/acp/golden/<scenario>.<mode>.jsonl` (D-15); the nine earlier scenarios' recordings did
not change since `21f4a8b`, and `unanswered`'s are new in `72d9588`. **20/20 passed** [CI, run].
Re-record with `uv run python -m tests.acp.golden record`.

D-18's deterministic twin adds a Claude Code root that acts through `dr repl exec` (a fake CLI, two
snippets): its tree, cells and `claude` usage, as §6.8 lists. **Passed** [CI, run].

### 6.3 E3 · stop

Root Stop (`test_supervisor.py`): during the root's `while True: pass` cell, and under 20 spinning
children; asserts the prompt answers `cancelled` within 2.0 s, the open cell fails with `Not finished:
the run was stopped`, `ROOT_STOPPED` closes the turn, every child is idle `cancelled` with `status:
stopped`, and the next prompt opens with `FRESH_AFTER_STOP`. **Passed** [CI, run]. Measured with an
uncommitted script at `2a15388`, at a load average of about 12.6 on 4 CPUs [run]:

| Condition | Threshold (design) | Measured |
|---|---|---|
| root Stop, busy root cell | 2 s (bridge drain; spec allowed 5) | 0.024, 0.031, 0.132 s; exit 0 |
| root Stop, 20 spinning children | 2 s | 1.00, 0.92, 0.87 s; exit −9 (SIGKILL after the 0.8 s grace) |
| shutdown on stdin EOF, root cell sleeping | 1.4 s to `run.end closed` | 0.32, 0.33, 0.33 s; `dr-acp` exited 0 at 0.86 to 1.14 s |
| shutdown on SIGTERM, same | 1.4 s | 0.32, 0.31, 0.34 s; exited 0 at 0.95 to 1.20 s |
| `session/close`, root cell hanging | 2 s grace, then kill | 2.05, 2.13 s; `run.end closed`, exit 0 |

The previous version measured the same conditions at `21f4a8b`, with no load recorded: 0.02–0.03 s,
0.86–0.87 s, 0.32 s, 0.32 s and 2.02 s. [read: `b67aa29`]

Stop on one sub-agent (`test_stop.py`): 20 department agents, department `D0` with two course agents;
`D0` is cancelled by its full session id once a depth-3 agent is announced; `FakeOpenAI` adds 0.2 s
latency and timestamps every call. Asserted for both adapters: the root still answers; `stop.request`
and an accepted `stop.accepted` are logged; no branch agent makes more than one call after
`stop.accepted` (D-13); `D0` and both course agents end idle `cancelled` with `status: stopped`, the
courses `stopped_by` `D0`. Interim: the 19 siblings are held at their first model call until the root
moves on (D-19); the root's cell output ends with the qualified
`deep_reasoning.acp.worker.stop.StoppedByUser: stopped #… and its branch (…). Its running siblings …`
naming exactly the agents marked `collateral`; `D0` shows the interim stop thought. Fake Dean API:
every other department's result `D<i> surveyed` is in the root's cell output beside `Stopped(node=…)`,
and the siblings end `done`. **2/2 passed** [CI, run]; the interim test failed once in CI at
`1652b5a`, before its siblings were held (D-19) [CI]. The classification rows of design §6.3 are unit
tested in `test_recorder.py` (interim branch, Dean nearest target, re-driven target, unknown or ended
target, the last also pinning each refusal's node and reason) [run].

### 6.4 E2 · stdio integrity

`test_cli.py`: a cell writes 10 MB with `sys.stdout.write`, writes to fd 1 with `os.write`, prints, then
prints 10 MB: the run answers, the first cell's output is `quiet` (the raw writes go to the worker's
own stdout, which is `worker.log` [read]), the 10 MB print arrives cut to under 10 MB with `bytes
elided`; an import hook that prints to stdout and to fd 1 while the front imports: the print lands
on stderr and every stdout line stays JSON-RPC. `test_supervisor.py`: `os._exit(1)` in a cell gives
`crashed` with exit code 1 and the `worker.log` path, and the next prompt answers after
`FRESH_AFTER_ERROR`. Plus the JSON-RPC line check in all 70 spawning tests. **All passed** [CI, run].

### 6.5 E4 · contracts

Tripwire: `test_recorder.py::test_tripwire_deep_reasoner_still_logs_everything_the_recorder_reads`
drives the real deep_reasoner in process with `FakeCompletionClient` (a main decomposition fans out two
children, one calls the `llm` tool, a second prompt resumes the root) and asserts the recorder's
`agent.start` drives and parent cells, the root's cells (`puppeteered`, `think`, `think`), every cell
closed, the children's answers, think versus tool calls, and the thought. **Passed at `d7334ae` on
every push** [CI, run]. **Against Dean's `main`: never run** (D-16). Schema: the harness check of §6.1,
on every message of 70 deterministic and 4 live tests; **no violation** [CI, run].

### 6.6 E11 · surfaces (D1's part)

Six tests in `test_session.py`: the menu follows `set_config_option` (`triage`, `summarize-then-rank`
→ `triage`, `compare-departments`), with each entry's `_meta.deep_reasoner.{decomposition, namespace}`;
the first prompt sends `available_commands_update []` then the narrowed option (`Fixed for this
conversation.`) before anything else; `run.start.namespace` and `.decomposition` are the chosen ones; a
late command and a command with no task are answered with their sentences and run nothing; unknown
namespace, unknown option and `NAMESPACE_FIXED` refusals carry their sentences, codes and names. **6/6
passed** [CI, run]. The file's other six (a path as a task, `PROMPT_BUSY`, a missing key, a failed
drive, a failed `materialize`, the bridge's appended blocks) pass too and back §4.5 and D-1.

### 6.7 Replay and shutdown

`test_agent.py`: `dr-acp` SIGKILLed mid-prompt, a new one `session/load`s: both runs replay, the first
equal to the live tree, the second equal plus its `lost` closing message; the user's four prompts replay
as `user_message_chunk`; no `subagent_update` follows the response; the next prompt opens with
`FRESH_AFTER_RESTART`. `session/close` leaves `run.end closed` and the next run opens with
`FRESH_AFTER_CLOSE`. `test_wire.py`: stdin close and SIGTERM each leave `run.end closed` under 1.4 s,
exit 0. **All passed** [CI, run]; §6.3 has the timings.

### 6.8 The live tier

Run 37144608009 at `2a15388`, four tests, durations from the log's timestamps [CI]:

| Test | Conditions | Asserts | Result |
|---|---|---|---|
| `test_claude_code.py::test_live_claude_code_on_sonnet_answers_through_acp_and_each_snippet_is_a_cell` | Claude Code CLI 2.1.285 on model alias `sonnet`, Michael's subscription token, `max_budget_usd` 0.5 | `What is 17 times 23?` answered with `391` through ACP; root backbone `claude_code`; every `usage` a `claude` call on `sonnet`; the tree's agents and parents are deep_reasoner's; one root cell per `cell.end`, the last calling `FinalAnswer`, in order among the transcript's `dr repl exec` snippets (D-18) | passed, ~8.9 s |
| `test_live.py::test_live_the_stream_rebuilds_deep_reasoners_tree_and_the_root_pays_for_all` | gpt-6-luna, `docs/configs/advising`, priced by genai-prices (the harness's `prices.yaml` holds only `fake-model`) | `/compare-departments Which department is lighter for a first-year student, CS or STAT?` answers; the rebuilt tree equals the reference (D-12) with ≥ 3 agents; the answer names `STAT`; every call priced; root cost = sum of the log's call costs; every child idle `done` or `exhausted`; every child cost strictly between 0 and the root's | passed, ~21.6 s |
| `test_live.py::test_live_stopping_a_department_stops_it_and_its_course_agents` | as above | stop a department once a course agent is announced (interim): the root answers; `stop.accepted` for that node; the department and its course agents idle `cancelled`, `status: stopped`; no more `usage` events from the branch after the stop than it has agents; the stop thought on the department | passed, ~12.8 s |
| `test_live.py::test_live_without_the_key_the_run_fails_before_any_call_and_says_which` | no `OPENAI_API_KEY` | `build_failed`, the sentence naming `OPENAI_API_KEY`, no `usage` in the log | passed, ~3.3 s |

Baseline: deep_reasoner's own run directory for the tree and the cells (our run log for an agent
with no model call, D-12); the run log's own `usage` events for the cost sum. The run's spend is not
recorded: the tests assert relations between costs and print no amount. [CI, read]

Since `0053bbf` a failed tree comparison prints `tree_evidence` (D-12) and a failed status check
prints each child's `_meta.deep_reasoner`, `detail` included (`test_live.py:57, 69–72`). The
status check itself dates from `9ece2e5`; design §8.4's list for this test does not name it. Run
37157389645 passed all four at `ac2ac87` (§6.1). [CI, read]

**Observed risk: OpenAI refuses a call with `invalid_prompt`.** In run 37149393726 (D4's branch,
§6.1) the root's puppeteered cell gave each department to a sub-agent with `run_all`; OpenAI
answered department 2's first call `400`, code `invalid_prompt` ("flagged as potentially violating
our usage policy"), which ended `run_all` and cancelled department 3 before any reply; the root
answered `STAT` on its own. The test failed on the tree comparison alone, `{1: (None, 3), 2: (1, 0),
3: (1, 0)}` against `{1: (None, 3)}` [CI]. On that run's log and run directory (the job's
`live-dr-homes` artifact), at `0053bbf`: the reference equals the stream's tree; replayed through
the encoder, the log gives both children idle `status: failed`, with the 400's full text and
`CancelledError: `; every assertion before the status check holds. So the test as it stands fails
at the status check, and its message names the refusal [run: an uncommitted script; the live
encoder and the test itself were not run]. GitHub lists 14 attempts of `live.yml` (12 runs); in
the 11 I confirmed ran D1's three gpt-6-luna tests (six on D1's branches, five on D4's), the
refusal surfaced once, on a sub-agent's first call; D4's other four attempts failed in D4's own
tests. Its trigger is unknown: the refusal's text gives none beyond the policy. [CI]

---

## 7 · What I could not verify

- **The live tier and its cost**: not run here; results are GitHub's log [CI]. No amount is printed,
  so the cost per live run is unknown. The Claude Code test asserts no cost; what the CLI's
  `cost_usd` means on a subscription was not looked at, and which Sonnet model the alias `sonnet`
  resolved to is not in the log.
- **genai-prices' gpt-6-luna price** is genai-prices 0.1.9's bundled data, not checked against
  OpenAI's page either; it is fixed until the dependency moves. [run for what genai-prices returns;
  read for its source]
- **D-19's race** was measured by the Refactorer (`ffa97f3`), not by me; the CI failure at
  `1652b5a` is the one record I read. With the siblings held, the interim test no longer has a
  sibling mid-response when the stop lands, so nothing in the suite exercises the race. Whether it
  occurs against a real model's API was not tested.
- **Dean's real `stop(node_id)`** does not exist at `d7334ae`; the Dean path runs only against the
  test fake, which fakes points 1–6 of design §6.3, not 7 (ending a `claude` process). [read]
- **The Claude backbone**: the live test covers a Claude Code root answering and its cells (D-18),
  and E1's `claude` scenario and D-18's twin run a Claude root on fake CLIs. No test runs a Claude
  agent as a sub-agent or stops one end to end: the recorder's Claude handling is tested on
  synthetic events, and the stop sentences as text and selection. [run and CI for what is tested;
  read for what is not]
- **The weekly tripwire against Dean's `main`**: never run (D-16).
- **An agent that never got a reply** (D-12): E1 checks it against our run log, written by the
  recorder whose events the stream encodes, not against deep_reasoner. `unanswered` fakes the
  refusal as a 500.
- **OpenAI's `invalid_prompt` refusal** (§6.8): trigger unknown, not reproduced. That the fixed live
  test fails at the status check comes from a replay of run 37149393726's log; no live run since
  `0053bbf` has had an agent go unanswered.
- **OpenHands' bridge**: no test runs against it. The prompt layout D-1 handles is reproduced from the
  bridge's source as constants (`harness.py:48–67`); the 2 s cancel drain, the 1,800 s idle watchdog
  and the ≤ 2 s wait for a root `usage_update` are the design's citations, not observed. [read]
- **Paths I read but did not see run**: control-pipe EOF killing the worker's group; the 0.7 s
  `close_run` watchdog's exit 3; a decomposition that `main_decomposition_turns` cannot puppeteer
  answering `build_failed`; `CATALOG_ERROR` on `session/new`; `cost_source: "mixed"` reaching a client
  (the encoder's output was run, a client never saw it). [read]
- **Concurrency** of the recorder across sub-agent threads is exercised by the 20-way fan-outs; I did
  not test it beyond the suite.
- **v3 itself**: I checked v3 against the code where the fourteen commits touched it and where it
  restates D-1 to D-16; its other new prose (the Gate B section, §1–§2's narrative) was not re-read
  line by line against the build.

If this document will not get shorter, the part that resists is §2.2: v3 took those divergences in,
and they are kept here, with their evidence re-run where the cleanup touched their code, because the
design's next revision is still being written.
