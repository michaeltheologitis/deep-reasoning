# S1 · ACP sub-agent sessions in the agent-server — design

**TASK-3** · System Designer · code lands in the SDK fork
[michaeltheologitis/software-agent-sdk](https://github.com/michaeltheologitis/software-agent-sdk), branch
`feat/acp-subagent-sessions`, as one pull request (v1: cut from `deep-reasoning` at `91430aa`; built stacked on S2's
`feat/agent-surfaces`, §3.2 B1; *v2.3:* read at Gate C as a stack of seven draft pull requests, #10 to #16, inside
the fork, the Gate C section) · against the approved spec
[TASK-1](https://app.notion.com/p/3ed62fb22237814ab425c81b3844f012) (S1, §2, C1, §4 E5 and the layers, the
2026-10-02 amendment, the rulings at design) and D1's wire contract (`deep-reasoning` `f281109`,
`docs/design/d1-dr-acp.md` §5).
**Pinned against:** SDK fork `91430aa` (= upstream `53a4bc5` plus the ASE commit, which touches only `AGENTS.md`
and `CLAUDE.md`, so every v1 `file:line` below is also upstream `53a4bc5`'s) · `agent-client-protocol` 0.12.1 (the
fork's lock) · ACP schema 1.24.1 `schema.unstable.json` (sha256 `6449a87a…be09109e`, the file D1 validates
against) · pyright 1.1.411 in `standard` mode (the fork's pre-commit).

**Matches the code at `6a05b13`** (v2.3): the top of S1's Gate C stack, seven draft pull requests in the fork, #10 to
#16 (the Gate C section). Its tree is `2675399`'s, the head of `feat/acp-subagent-sessions` after the literate
refactor, plus tests only: the agent-swap test race fix (`2f7642c`, the same change as the fork's #17) and three
restored pins (`049ceb5`, `306731d`, `6a05b13`). S1's own diff is `9277e71..6a05b13`, against the fork's
`deep-reasoning`: 3,730 lines added and 63 removed, in 43 files. The draft pull request #2, which held the whole
branch against S2's `feat/agent-surfaces`, is closed as superseded by the stack. The `file:line` references in notes
marked *(v2.3)* are `6a05b13`'s, which for every source file are `2675399`'s (the top changes three test files only),
so as-built r3's line numbers hold. v2.3 is committed on `design/s1` and changes only this file.

**Changed by the refactor** (v2.3): S1's fifteen commits in `a3279be..2675399`, each with the as-built r3 divergence
that reads it (§2, V-1 to V-10) and the sections it touches here. None changes what is stored or sent: the exported
OpenAPI and the `--subagents` turn's stored events are the same before and after (as-built r3 §3, §4.4).

- `a682f6a` **Each child is held as its latest `ACPSubagentEvent`** (V-4). `_Association` is gone; the held event's
  `cancellable` is the live grant, and each stored snapshot is a new event (§4.3, A.2).
- `bf57a3a` **The sub-agent connection always advertises `subagents`** (V-2). `_SubagentInitializeRequest`
  subclasses `InitializeRequest` with `SerializeAsAny[ClientCapabilities]`, and the bridge makes one `initialize`
  call for both connection classes (decision B, §3.1 item 3, §4.2, §4.4, A.1).
- `6b089e5` **`SubagentState` keeps no extra keys** (V-3). A custom state's name is kept; the store never held the
  rest (§4.2, A.1).
- `73e47f8` **One warn-once helper** (V-1): `_warn_unannounced(session_id, routing)`, once per session per path
  (decision C, §4.3, §4.4, E-4, A.3).
- `fec0b95` **`replaying()` replaces `_load_session`** (V-5): a bridge context manager around upstream's own
  `conn.load_session(...)` call (§4.3, §4.4, §6, B7, A.3).
- `d03ec2c` **Shared wire builders** (V-6): eleven functions in the scripted agent build ACP updates for it and for
  both sub-agent test files (§4.10, A.7).
- `2fb47b2` **Shared test helpers** (V-6): `tests/conftest.py` gains `subagent_snapshots`, and `wait_until` returns
  what it waited for (§4.1, §7, §9).
- `a910ac9`, `6dcde3e`, `ca39def`, `5b17efd`, and the tests cut with `bf57a3a` and `6b089e5`: **88 deterministic
  cases become 75** (V-7 to V-9), by cuts, merges and renames. The next section's property table says which test
  carries each property now.
- `1c66ce2`, `2675399`: docstrings state their own contract (A.2, A.3, A.5). `49dda35`, `ec95abc`: layout only;
  Appendix A keeps one parameter per line.
- **Size** (V-10): source 1,394 → 1,302 lines added, tests 2,761 → 2,388.

**Since the refactor, on the stack** (tests only): `2f7642c` on #10, the race fix; `049ceb5` on #10, P7's pin;
`306731d` and `6a05b13` on #16, P4's and P6′'s pins; each merged upward with merge commits.

**Matches the build at `0cfb6a2`** (v2): S1's five commits on `feat/acp-subagent-sessions` (`13f4571`, `d10c021`,
`6938ba5`, `57c0925`, `0cfb6a2`), on top of S2's `feat/agent-surfaces` at `6f97bf3`, in the draft pull request
[michaeltheologitis/software-agent-sdk#2](https://github.com/michaeltheologitis/software-agent-sdk/pull/2) against
`feat/agent-surfaces`. `0cfb6a2` is the branch's head. The `file:line` references in §3.2 and in the notes marked
*(v2)* are `0cfb6a2`'s; v1's stay `53a4bc5`'s.

**Matches the build at `a3279be`** (v2.2): the five commits above, then the fixes made on v2.1's rulings, `d74940b`
(E-2), `f6d8e1e` (E-1), `e65335d` (E-3), `562c31d` (E-4) and `a3279be` (the persisted agent-profile fixture), with
two merges between: `0f161f8` (the fork's `deep-reasoning`, bringing the fork-only `1f2b52d`) and `2114d23` (S2's new
head `5e3317f`). `a3279be` is the branch's head and PR #2's; S1's own diff is `5e3317f..a3279be`. The `file:line`
references in notes marked *(v2.2)* are `a3279be`'s.

**Revisions** (newest first; the Gate B reader approved the previous version, so each line says which sentences to
stop trusting):
- 2026-10-04 · v2.3 · read beside S1's Gate C stack, #10 to #16, and brought in line with the literate refactor and
  the stack's top, `6a05b13`, on the Conductor's request, so that Gate C's reviewers read a design that names the
  code as it now is. Gate B approved v2.2; nothing the refactor did changes what is stored or sent. Stop trusting:
  the header's "as one pull request" and PR #2 as S1's open draft (now the stack; #2 is closed); decision B's
  standalone request model and §3.1 item 3's (V-2); §4.2's `extra="allow"`, "anything else kept" and its
  `initialize` branch (V-3, V-2); §4.3's `_children: dict[str, _Association]`, `_Association`, `_warned` and "set by
  `_init`" (V-4, V-1, V-5); §4.4's first-table rows for `_init`'s `initialize` and load, and its v2 and v2.2 rows
  and notes naming `_load_session`, `LoadSessionResponse` and E-4's set and helper (V-2, V-5, V-1); B7's and E-4's
  v2.2 notes' names for the same (V-5, V-1); the test names and counts in §5.1's "Pinned by" lines, B8, B10, B12 and
  §7 (V-7; the property table at `6a05b13` replaces them); §5.1 guarantee 9's "pinned by the fixture row" (pacing
  and a missed wait point are unpinned, V-8); §8's "each cherry-pickable onto `main`", its draft PR onto `main` and
  "whether the fixes fold", B14's reading of spec §4 layer 3, and §11 items 3 and 4's upstream PR (the stack is
  internal and based on the fork's `deep-reasoning`; nothing goes to `main` or upstream); A.1's `SubagentState`,
  `_SubagentInitializeRequest` and `initialize` docstring; A.2's `_Association`, `_merge` and `before_update`
  docstring; A.3's warn-once members, `unstable_session_update`'s parameter type and docstring, and
  `_load_session`; A.5's `LocalConversation.cancel_acp_session` docstring; A.7's list of S1's additions (the
  builders). Moved: these revision lines, the build notes, where this file lives and the reading guide, from the end
  of the Gate B section to above the Gate C section. Added: the header's v2.3 paragraphs ("Matches the code at
  `6a05b13`", "Changed by the refactor"); the Gate C section; the section after it (the evidence at the refactored
  head and on each level, the property table at `6a05b13`, the restored pins, what stays unpinned, the counts and
  the size); the Gate B section's banner; v2.3 notes in decisions B and C, §3.1 items 3, 8 and 16, B7, B8, B10, B12,
  B14, B16, B17, E-4, §4.1 to §4.4, §4.10, §5.1, §6, §7, §8, §9, §10 and §11, §11 item 16, and Appendix A's
  preface. The Gate B section is otherwise as approved; its test names are `a3279be`'s.
- 2026-10-03 · v2.2 · the fixes made on v2.1's rulings, at `a3279be`. Stop trusting: the Gate B section's
  evidence, its size and its "Before Gate B: one fix" (now built; the runs at `0cfb6a2` are superseded by CI and the
  live run at `a3279be`); B2's "Not built" (the profile fixture is built); B5's in-flight replayed entries and the
  E-1 to E-4 bullets' present tense about the code (each is now built, its note says where); B14's "did not run in
  CI" and B17's open guard runs; §5.1 guarantee 7's exception, the E-1 non-guarantee and the profile-fixture
  non-guarantee; §11 items 8, 9, 11, 13 and 14. Added without changing earlier sentences: the header's v2.2
  paragraph, §4.1's, §4.4's, §7.4's and §8's v2.2 notes, §7's new tests, and Appendix A.3's new members.
- 2026-10-03 · v2.1 · reconciled with the as-built document (`as_built/s1-acp-subagent-sessions.md`, `17ab4d5`)
  and its four uncovered edges ruled, at the Conductor's request. Stop trusting: §5.1 guarantee 7's "nothing
  `session/load` replays is stored", which fails in one case until E-2's fix lands; B17's list of what was not
  checked (the Cartographer ran most of it). Added without changing earlier sentences: §3.2's map to the as-built's
  D-1 to D-13, the details it had that §3.2 lacked (B10, B12, B14, B17), and "Edges the build left open, ruled"
  (E-1 to E-4, and D-1 against C1's Stop rule); the Gate B section's "Before Gate B" paragraph and its notes on the
  guards and D1's goldens; decision C's and §4.3's notes on unannounced sessions; §5.1's new non-guarantees; §6's
  measured interleaving; §11 items 13–15.
- 2026-10-03 · v2 · brought in line with the build at `0cfb6a2`, after Proof Green. Stop trusting: the header's
  branch point, and every "if S1 lands first" clause, here and in §4, §7, §8 and §9 (S2 landed first and S1 is
  stacked on it, B1); decision H's and §2's "cancellable or active" (active only, B3); §4.3's `_warned` and its
  replay sentence (B5, B7); §4.4's rows for `_start_acp_server`, `_init`'s load and root id, `session_update`, and
  its "unchanged" `_finalize_successful_turn` (B1, B4, B7); §4.6's single home for the opt-in (B2); §4.7's
  allowlist count and §4.9's file list (B2, B15); §4.10's serving paragraph, the order of the `--subagents` run and
  "answering nothing more" (B1, B9, B10); §5 rule 7 (B3); §7's file names, test names and the route tests' mocked
  service, and §7.4's assertions (B12, B13); §8's branch, commit contents and guard results (B1, B14); §3.1 item
  16's size (B16); §11 items 1, 2 and 5 (resolved). Added without changing earlier sentences: this Gate B section;
  §3.2; §5 rule 10 and §5.1 (what C1 and D5 may rely on); §6's note on timestamps; §11 items 8–12; Appendix A's new
  members. §3.1 (v1's §3) keeps every item as written, each with a v2 note on whether it still holds; the Conductor
  accepted them at design (spec, "Rulings at design, 2026-10-02" (3)). Every change is listed, with its reason, in
  §3.2.
- 2026-10-02 · v1 · first full-depth version, aligned before its first commit with S2's design (deep-reasoning
  `design/s2` `9e32261`, `docs/design/s2-agent-surfaces.md`) on three shared pieces, at the Conductor's request:
  one ordered emitter for events that arrive outside a turn (`ACPAgent._on_session_event`,
  `LocalConversation._emit_event_from_any_thread`, S2 §4.3), one scripted test agent at
  `tests/fixtures/acp/scripted_agent.py` (S2 Appendix C), and one route module, `acp_router.py` (S2 §4.7).
  Whichever PR lands first creates each; the other uses it.

**Build notes.** In this container `uv` is 0.8.17, which cannot parse the fork's `exclude-newer = "7 days"`
(`pyproject.toml:7`); run every check in the fork with `uvx uv@latest` (0.12.22 works), for example
`OPENHANDS_SUPPRESS_BANNER=1 uvx uv@latest run pytest tests/sdk/agent/test_acp_subagents.py`. The probes v1 cites
ran in a scratch virtualenv with `agent-client-protocol` 0.12.1 and pyright 1.1.411, not in the fork's environment.

**Where this file lives, and why nothing trips over it.** `docs/design/` on deep-reasoning's `design/s1` branch,
not in the fork: the fork's branches carry only code upstream would accept, and upstream keeps PR-only design
notes in `.pr/`, which its own workflow deletes. deep-reasoning has no docs site, no package and no test runner
on this branch; on D1's branch pytest is pointed at `tests/` only and the sdist excludes `docs/` (D1 §8.5), so this
file is never collected, built or shipped. The PR split leaves it behind. *(v2.3: the split made seven pull requests,
#10 to #16, and neither this file nor the as-built document, `as_built/s1-acp-subagent-sessions.md` on this same
branch, is in any of them.)*

**Reading guide.** Gate B: the Gate B section (*v2.3:* below the two Gate C sections). C1's designer: §5 and §5.1 (what
is stored, how to read it, and what C1 may rely on) and §4.5. S2's designer: §9 (every place S1 and S2 touch the same
code). D5's designer: §5.1, §4.6 (the opt-in), §4.10 (the scripted agent that replays D1's recordings) and §7.4 (the
live tier). The Implementer, the Cartographer and the Refactorer read everything; §3.2 is what the build changed, and
Appendix A is the signature reference, every block valid, ruff-formatted Python or TypeScript, plus the scripted agent's
command line. *(v2.3)* Gate C's reviewers start at the Gate C section, next: which PR holds what, its lines, and which
sections to read beside it. The section after it says what changed since Gate B and which test carries each property at
`6a05b13`; §1 to §11 and Appendix A name the code as it is there. The Gate B section, after those two, is history.

## Gate C: reading beside the PRs (v2.3)

The code is read as a stack of seven semantic PRs, tests included; this doc is the reference beside them. Where the
two differ, that is a finding to raise, not a reading to choose. The stack is open in
michaeltheologitis/software-agent-sdk as draft PRs, bottom-up, each based on the level below it (2026-10-04). They are
internal drafts inside the fork: the bottom one, #10, is based on the fork's `deep-reasoning` at `9277e71`, which is
S2's stack merged (`69c00ca`, whose tree is S2's `d938c90`) plus the fork's #17, the agent-swap test race fix. Nothing
in the stack goes to the fork's `main` or upstream, so §8's draft onto `main` and its cherry-picks, and spec §4 layer
3's draft PR, are steps not taken. Each level was cut by idea from S1's net diff `d938c90...2675399` as one commit; the
race fix and the three restored pins were added on #10 and #16 and merged upward, so the top, #16, has `6a05b13`'s
tree exactly. Every level's checks are green: 27 each, with upstream's "Validate PR description" skipped on a draft.
This doc and the as-built document (`as_built/s1-acp-subagent-sessions.md`, r3, the Cartographer's) are both on
deep-reasoning's `design/s1`, and neither is in any PR. Review comments and their status are in the Conductor's
[review ledger](https://app.notion.com/p/3ef62fb222378141a6f9e98a358c04bc).

**v1's five commits are seven levels** (§8). Commit 1 is #10 and commit 2 is #11. Commit 3 is cut three ways: the
bridge (#12), the opt-in on settings and profiles (#13), and the transcript player (#16). Commit 4 is #14, with the
live stop test and `--cancel-wait`, which v1 had put in commit 3. Commit 5 is #15. The transcript player sits at the
top so that it can be dropped alone: only our projects replay recordings, but four upstream-shaped tests depend on it,
one of them the only test that reconnects a real second connection. It needs #10 to #12 and nothing from #13 to #15.

| Level | PR | What it holds | Lines added (removed) | Read beside | Reading |
|---|---|---|---|---|---|
| 1 | [#10](https://github.com/michaeltheologitis/software-agent-sdk/pull/10) carry ACP's unstable sub-agent updates past agent-client-protocol 0.12.1 | `acp_unstable.py`: the four models, `SubagentClientSideConnection`, `route_unstable_updates`. Four wire builders in the scripted agent (`text`, `subagent`, `said`, `message`). `test_acp_unstable.py`, 7 cases, P7's pin among them | 456: 222 of code, 234 of tests (28 the builders). GitHub shows 462 (4): #10's diff also holds `2f7642c`, the race fix in S2's `test_local_conversation_acp_config_option.py`, the same change `9277e71` carries | Decision B, §3.1 item 3, §4.2, §7.1, §8 ("When the library catches up"), §11 item 3, A.1, A.7 (the four builders); *v2.3:* `bf57a3a` (V-2), `6b089e5` (V-3), the shim row of the property table. As-built r3: §4.1, §7.2 (`test_acp_unstable.py`), §2 V-2 and V-3, §8 (P7) | 1.5 h |
| 2 | [#11](https://github.com/michaeltheologitis/software-agent-sdk/pull/11) add sub-agent session events; keep child tool calls apart from the root's | `event/acp_subagent.py` (the three kinds), `ACPToolCallEvent`'s two fields, the exports, the visualizer's entries, the resume transcript's skip, `RemoteEventsList`'s key, the weak-schema allowlist; the event, dedup and resume-transcript tests | 356 (8): 232 of code and allowlist (18 the allowlist), 124 of tests | Decisions D, E and F, §3.1 items 1, 2, 4, 12 and 15, §4.5, §4.7 ("The OpenAPI ratchet"), §4.8, §5 rules 1 to 9, §5.1, A.4, B15. As-built r3: §3 "Events", §5, §7.2 (the event, dedup and resume-transcript rows), §8 (`test_root_tool_call_event_is_stored_as_before`, P3, P3b) | 1.2 h |
| 3 | [#12](https://github.com/michaeltheologitis/software-agent-sdk/pull/12) route and persist ACP sub-agent sessions in the bridge (opt-in `acp_subagents`) | `acp_subagents.py`; `acp_agent.py`'s hunks (the opt-in field, the connection swap, the diversion, child tool calls, the three close-outs, the seed, `replaying()`, the turn-end flush, the trace); `--subagents` and seven more builders in the scripted agent; `tests/conftest.py`'s helpers; `test_acp_subagents.py`'s 33 bridge units and 5 conversation cases, the schema test in `test_acp_router.py`, the live tree test; S1's line in `acp-live-tests` | 1,657 (48): 553 of code and CI (the router 299, the bridge +252 −43, the job 2), 1,104 of tests (141 the scripted agent, 119 the live tree test) | §1.1, §1.2, decisions A, C, G, H, J and K (`--subagents`), §2, §3.1 items 2, 6, 7 and 14, §4.3, §4.4, §4.6 (the agent's field), §4.10 (`--subagents`), §5 rule 10, §6, §7.2, §7.4 (the tree test), §11 items 6, 7 and 15, A.2, A.3 (all but the cancel members), A.7 (`--subagents`); B3, B4, B5, B7, B9, B11, B12, B13, E-1, E-2, E-4 and D-1; *v2.3:* `a682f6a` (V-4), `73e47f8` (V-1), `fec0b95` (V-5), `d03ec2c` and `2fb47b2` (V-6), V-9. As-built r3: §1, §2 V-1, V-4, V-5, V-6, V-9 and its paragraph on r1's D-1, D-3, D-7 and D-11, §4.2 to §4.5, §7.2 (`test_acp_subagents.py`), §7.3, §7.5 (the tree test), §8 (P1, P8, P10) | 5.5 h |
| 4 | [#13](https://github.com/michaeltheologitis/software-agent-sdk/pull/13) carry the `acp_subagents` opt-in through agent settings and profiles | `ACPAgentSettings.acp_subagents` and `create_agent()`'s forwarding; `ACPAgentProfile.acp_subagents`, the resolver's and the seed's lines; the v7 settings and v2 profile baselines; the resolver tests | 97: 19 of code, 78 of tests (27 the baselines) | Decision A (its v2 note), §4.6, §5.1 guarantee 8, A.5 (the settings and profile fields), B2. As-built r3: §3 "The opt-in", §2's paragraph on r1's D-2, §6 (`Persisted settings`), §7.2 (the resolver row), §7.6, §8 (P2) | 20 min |
| 5 | [#14](https://github.com/michaeltheologitis/software-agent-sdk/pull/14) cancel one ACP sub-agent session | The route and `CancelACPSessionResponse` in `acp_router.py`, `EventService.cancel_acp_session`, `LocalConversation.cancel_acp_session`, `ACPAgent.cancel_acp_session`, `_acancel_acp_session` and the 2 s bound; `--cancel-wait`; the five cancel cases in `test_acp_subagents.py`, the route's five, the service's two, the cross test, the live stop test | 500 (9): 138 of code, 362 of tests (24 the scripted agent, 70 the live stop test) | Decisions H and I, §2 ("Stop on one child"), §3.1 items 5, 9 and 14, §4.7, §4.10 (`child-b`, `--cancel-wait`), §5 rule 6, §5.1 guarantee 6, §6 ("Cancel"), §7.3 (the route, service and cross rows), §7.4 (the stop test), A.3 (`cancel_acp_session`, `_acancel_acp_session`, `_ACP_SUBAGENT_CANCEL_TIMEOUT`), A.5 (the conversation, service and route), B6, B13, E-3; *v2.3:* `5b17efd`, V-8 (the route's 200 is reached by the cross test alone). As-built r3: §3 "Python calls" and "REST", §4.5 (E-3), §7.2 (the route, service and cross rows), §7.3 (the cancel rows), §7.5 (the stop test), §2 V-8, §8 (P9, the merged cancel tests) | 1.7 h |
| 6 | [#15](https://github.com/michaeltheologitis/software-agent-sdk/pull/15) read ACP sub-agent events and cancel one sub-agent session (TypeScript client) | The three event types and their guards, `ACPToolCallEvent`'s two fields, `cancelAcpSession` twice, `CancelAcpSessionResponse`, `ACP_SETTINGS_KEYS`, `ACPAgentProfile.acp_subagents?`, the exports, the endpoint-audit entry and the type budget; the client's 5 tests | 252 (2): 139 of code and configuration (27 the audit and the budget), 113 of tests | §3.1 item 10, §4.9, §5 rule 6, §11 item 4, A.6, B2 (the profile field), B15. As-built r3: §3 "TypeScript", §2's paragraph on r1's D-12, §7.2 (the TypeScript row), §8 (the TypeScript row) | 50 min |
| 7 | [#16](https://github.com/michaeltheologitis/software-agent-sdk/pull/16) replay recorded ACP transcripts through the scripted agent | The transcript player (`_Wait` to `play_transcript`, `--transcript`, `--transcript-interval-ms`, `--wait-timeout`, `run()`'s branch); `test_scripted_transcript_replays_a_recording[full, outgoing-only]`, the reconnect ordering test, and two restored pins: the opt-off test's `[--transcript]` case (P4) and `test_transcript_exits_non_zero_when_a_wait_point_outlasts_the_wait_timeout` (P6′) | 423 (7): all tests, 253 of them the scripted agent | Decision K, §3.1 item 8, §4.10 (the transcript player), §5 rule 10, §5.1 guarantee 9, §10 item 6, §11 items 12 and 15, A.7 (`plan_transcript` to `play_transcript`), B8, B10, B11, the Gate B section's paragraph on D1's golden recordings; *v2.3:* `6dcde3e`, the unpinned list in the next section. As-built r3: §2's paragraph on r1's D-6 and D-8, §2 V-8, §3 "The scripted agent", §7.3 (the transcript and reconnect rows), §7.4, §8 (P4, P5, P6, P6′) | 1.4 h |

Lines are each PR's own diff against its base's head (`git diff --numstat`, two dots, which equals GitHub's view for
#11 to #16), split into tests (`tests/`, the scripted agent and the persisted baselines with them, and the
TypeScript `__tests__/`) and the rest. They sum to 3,741 added and 74 removed, about 12.5 h at ≈300 lines an hour,
against the spec's ≈5 h. The net diff `9277e71..6a05b13` is 3,730 and 63, because higher levels rewrite 11 lines that
lower levels add (an import, docstrings, a test's signature). Code, CI and client configuration are 1,302 lines at
every count; tests are 2,428, the refactor's 2,388 plus 40 of restored pins. The reading column is the lines added
at ≈300 an hour; the sections beside each level add to it.

**The sections to read beside each PR** were listed by the PR Splitter against v2.2 and as-built r2, and are in each
PR's body in that form. v2.3 renumbers nothing here (it adds this section and the next beside the numbered ones),
so those references hold. The entries marked *v2.3* add the refactor's commits, and the sections that describe a
level's code but were missing from its list are added without a mark (§1.1, §1.2, §3.1's items, §11's items, §2's
"Stop on one child", §6's "Cancel" and §5.1's guarantees). As-built r3 renumbered r2's, so this table gives r3's
numbers, which r4 keeps: r2's §2.1 to §2.5 are r3's §2 (V-1 to V-10, then one paragraph on r1's D-1 to D-13); r2's
§7.2 (E5 through a conversation), §7.3 (D1's golden recordings) and §7.4 (the live tier) are r3's §7.3, §7.4 and
§7.5; r2's §7.5 ("Shim", "Events", "Consumers", "Route", "Service", "TypeScript") is r3's §7.2, one row per test file;
and r3's §8, what the refactor took out of the tests, is new.

**Three places to read with care.**

- **#12 is large, and was kept whole**: 1,657 lines added, about 5.5 h, 44% of the stack. Its 551 lines of code are
  one mechanism: every update passes the bridge's diversion (§4.4), and every child event leaves through the
  conversation's one emitter (decision G, §6). A level for reconnect handling, or for child tool calls, alone would
  need intermediate code that nobody reviews, and would take the end-to-end tests away from the claim they prove (the
  PR's notes). Of its 1,104 lines of tests, about 460 feed the bridge wire updates directly; the rest drive a real
  `LocalConversation` against the scripted agent, one real agent-server run whose events validate against the
  published schema, and the live tree test; 141 are the scripted agent's `--subagents` run. Read §4.3 with
  `acp_subagents.py`, then §4.4 with `acp_agent.py`'s hunks, then `test_acp_subagents.py` from the top.
- **The cancel grant is checked in #12 and used in #14.** `check_cancel` and its two errors sit in #12, whose tests
  pin the grant (an announcement grants it, a replay never does, a new connection withdraws it); the call that uses
  them is #14's.
- **Files that arrive in parts.** The scripted agent grows over four levels: four builders in #10; seven more and
  `--subagents` in #12, where `child-b` always completes; `--cancel-wait` in #14; the transcript player in #16.
  `test_acp_subagents.py` grows over three (#12, #14, and #16, which also adds the opt-off test's `[--transcript]`
  case), the live file over two (the tree test in #12, the stop test in #14), and `test_acp_router.py`'s additions
  over two (the schema test in #12, the route's cases in #14). And #10 holds the race fix, 6 lines added and 4 removed in S2's
  test file, which have nothing to do with S1.

**For any PR:** its tests, file by file, are §7, with its v2.3 notes; which test carries which property is the next
section's table, at `6a05b13`; what changed since Gate B, each change with its commit, is the header's "Changed by the
refactor".

| Module | Section |
|---|---|
| `sdk/agent/acp_unstable.py` | §4.2, decision B, A.1 |
| `sdk/agent/acp_subagents.py` | §4.3, A.2 |
| `sdk/agent/acp_agent.py` | §4.4 and §6; decisions A, C and G to J; A.3 |
| `sdk/event/acp_subagent.py`, `acp_tool_call.py`, `__init__.py` | §4.5, §5, A.4 |
| `sdk/conversation/impl/remote_conversation.py`, `sdk/event/resume_transcript.py`, `sdk/conversation/visualizer/default.py` | §4.8 |
| `sdk/settings/model.py`, `sdk/profiles/` | §4.6, A.5 |
| `sdk/conversation/impl/local_conversation.py`, `agent_server/event_service.py`, `agent_server/acp_router.py` | §4.7, A.5 |
| `clients/typescript/` | §4.9, A.6 |
| `tests/fixtures/acp/scripted_agent.py` | §4.10, A.7 |
| the weak-schema allowlist, `tests.yml`, the client's audit and type budget | §4.7, B15, §7.3 |

## After Gate B: the refactor and the stack (v2.3)

What changed since Gate B, commit by commit, is the header's "Changed by the refactor"; each change is folded into
the sections it names, with a *(v2.3)* note. This section is the evidence, the tests and the size.

**The evidence.**

- **At `2675399`, the refactored head** (PR #2, now closed): CI's 28 checks, 27 green and "Validate PR description"
  skipped; [Run tests 37170487023](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37170487023):
  `sdk-tests` 6,749 passed, `agent-server-tests` 2,425, `cross-tests` 497, `acp-live-tests` 25 passed and 4 skipped,
  S1's two live tests among the skipped. The live tier, deep-reasoning's `fork-live.yml`,
  [run 37171079147](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37171079147) with `sdk_ref`
  `2675399`: 2 of 2 passed in 48.26 s, against dr-acp on gpt-6-luna. The exported OpenAPI is byte-identical at
  `a3279be` and `2675399`, and the OpenAPI ratchet passes with 65 allowlisted locations (as-built r3 §6, §7).
- **On the stack**, each level's checks, 27 green each; the `Run tests` runs are #10
  [37174876576](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37174876576), #11
  [37175595431](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37175595431), #12
  [37175597225](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37175597225), #13
  [37175598478](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37175598478), #14
  [37175599887](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37175599887), #15
  [37175601521](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37175601521) and #16
  [37175602976](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37175602976). Each level runs
  the suites its own diff touches (upstream's change detection), so a level that touches no agent-server file shows
  `agent-server-tests` green with its pytest step skipped. At #12, `agent-server-tests` passed 2,418 and `sdk-tests`
  6,739; at #14, 2,425 and 6,747; at the top, #16, `sdk-tests` passed 6,752, `2675399`'s 6,749 plus the three
  restored cases, and `cross-tests` 497. The top differs from `2675399` in three test files, not the live file, so
  the live run at `2675399` stands for it.

**Which tests carry which property, at `6a05b13`.** Each test's name states the property it pins. Python files are in
the SDK fork under `tests/sdk/agent/` unless a path is given; TypeScript ones under `clients/typescript/src/__tests__/`;
`[…]` is a parametrization; the level that adds each test is in brackets. *Gone* names a Gate B test that no longer
exists and where its property went (as-built r3 §8); *restored* marks the three pins added back on the stack.

| Property | Tests |
|---|---|
| **E5 · The stored events rebuild the agent's tree** | `test_acp_subagents.py::test_scripted_run_stores_the_scripted_tree` [#12] (the scripted run through a real `LocalConversation`; its tree reader places a child by its spawning cell only, so §5 rule 2's fallbacks are exercised by no test, V-9), `::test_scripted_transcript_replays_a_recording[full, outgoing-only]` [#16]; the routing units `::test_announcement_stores_parent_cell_and_cancel_grant`, `::test_parent_tool_call_id_survives_meta_without_it`, `::test_child_is_never_reparented_nor_its_own_parent`, `::test_child_tool_calls_are_keyed_by_session_and_tool_call_id`, `::test_omitted_field_keeps_value_and_null_clears_it[10 patches]`, `::test_unannounced_session_follows_the_root_path_with_one_warning`, `::test_unstable_updates_on_an_unannounced_session_stay_under_that_session` [#12]; **live:** `test_acp_subagents_live.py::test_live_agent_tree_is_well_formed` [#12] |
| **E5 · No child text reaches the root's answer** | `test_acp_subagents.py::test_child_text_never_reaches_the_root_answer` [#12]; **live:** the tree test. *Gone:* `test_scripted_run_keeps_child_text_out_of_the_answer` (`a910ac9`) |
| **E5 · The stored events break no client** | `tests/agent_server/test_acp_router.py::test_stored_sub_agent_events_validate_against_the_event_schema` [#12]; `tests/sdk/event/test_acp_subagent_events.py::test_subagent_events_round_trip_through_json[4 events]` [#11]; `event-types.test.ts › ACP sub-agent session events › each guard recognises only its own kind` [#15]. *Gone:* the TypeScript `sub-agent event shapes accept stored events` (`a910ac9`) |
| **Old conversations load unchanged, and with the opt-in off nothing changes** | `tests/sdk/event/test_acp_subagent_events.py::test_legacy_acp_tool_call_event_loads_without_session_fields` [#11] (and so the model's `meta` default, P3b); `test_acp_subagents.py::test_subagents_off_stores_only_root_work_through_the_stock_connection[--subagents]` [#12], `[--transcript]` [#16] (the stock connection class, `initialize` equal to the library's own serialization, only the root's cell, no `acp_session_id`, no new kinds); upstream's suites and its conformance probe. *Gone:* `test_subagents_off_uses_the_stock_connection_and_initialize` and `test_scripted_run_with_subagents_off_stores_only_root_work[…]` (merged into the test above, `a910ac9`); `test_initialize_without_subagent_capabilities_is_the_library_call` (cut with its branch, `bf57a3a`); `test_root_tool_call_event_is_stored_as_before` (`a910ac9`), so the bridge leaving a root call's `meta` unset is unpinned (P3; the cut test built the event itself, so it never pinned that) |
| **A child's own text and reasoning are stored per segment, in order; directed messages whole** | `test_acp_subagents.py::test_child_text_is_stored_per_segment_in_transcript_order`, `::test_usage_never_splits_a_text_segment`, `::test_chunked_message_is_stored_whole_at_the_next_boundary`, `::test_message_upsert_replaces_content_and_keeps_participants` [#12]; *restored:* `test_acp_unstable.py::test_session_message_with_a_non_text_block_reaches_the_callback_whole` [#10] (P7) |
| **A child's cost is on its association and never added** | `test_acp_subagents.py::test_child_cost_is_stored_on_its_association_when_it_changes` (renamed from `…_is_on_its_association_and_never_booked_to_the_conversation`, its booking assertion left to the next test, `ca39def`), `::test_scripted_run_books_only_the_roots_cost`, `::test_child_usage_leaves_root_usage_sync_and_context_window_alone` [#12]; **live:** the tree test |
| **Child traffic after the parent's turn is stored, and every child event takes one ordered path** | `test_acp_subagents.py::test_child_traffic_between_turns_reaches_the_emitter_in_order`, `::test_child_events_go_to_the_session_emitter_and_root_events_to_the_turn`, `::test_child_events_without_an_emitter_are_dropped_with_a_debug_line`, `::test_turn_end_force_completes_only_root_tool_calls`, `::test_aborted_turn_fails_child_tool_calls_with_their_session`, `::test_child_call_open_across_aborted_turns_is_failed_once_and_the_agents_report_wins` [#12] |
| **Cancel one child** | `test_acp_subagents.py::test_cancel_acp_session_reaches_the_child_without_waiting_for_the_state_lock` (merged from `…_reaches_the_child_and_its_cancelled_state_is_stored` and `…_does_not_wait_for_the_state_lock`, `a910ac9`), `::test_cancel_acp_session_refuses_a_child_without_a_grant`, `::test_cancel_acp_session_refuses_unknown_and_root_sessions`, `::test_cancel_acp_session_without_a_live_connection_is_refused`, `::test_cancel_acp_session_for_an_idle_child_that_keeps_its_grant_is_sent` [#14]; the route on a real agent-server, `tests/agent_server/test_acp_router.py::test_a_cancel_for_an_unknown_conversation_is_not_found`, `::test_a_cancel_for_an_unknown_session_is_not_found`, `::test_a_cancel_for_a_child_without_a_grant_is_a_conflict`, `::test_a_cancel_on_a_conversation_that_is_not_acp_is_a_bad_request`, `::test_a_cancel_the_agent_does_not_take_in_time_times_out` [#14]; `tests/agent_server/test_event_service.py::test_cancel_acp_session_runs_off_the_event_loop` (now module functions, and it pins that the loop keeps running while the cancel blocks, `5b17efd`), `::test_cancel_acp_session_on_an_inactive_service_is_refused` [#14]; `tests/cross/test_remote_conversation_live_server.py::test_acp_subagent_sessions_over_live_server` [#14], the route's only test of its 200 and body (P9); `api-clients.test.ts › ACP sub-agent sessions › …` (3) [#15]; **live:** `test_acp_subagents_live.py::test_live_agent_stops_one_subagent_and_its_branch` [#14]. *Gone:* the route's `test_a_cancel_reaches_the_child_and_its_cancelled_state_is_stored` (`a910ac9`) |
| **After `session/load`, associations are kept and controls stay off until fresh state arrives** | `test_acp_subagents.py::test_replay_is_neither_stored_nor_grants_cancel`, `::test_new_connection_withdraws_cancel_and_unconfirms_state`, `::test_partial_patch_after_reconnect_keeps_the_stored_title` (both also pin that no snapshot keeps a stored event's `parent_id`, P1, V-4), `::test_replayed_child_calls_are_never_tracked_nor_failed_later` [#12]; `::test_a_reconnect_snapshot_is_later_than_the_childs_earlier_events` [#16], a second real connection, and the one test that catches `replaying()` leaving its flag set (P10) |
| **The shim, and the tripwire that deletes it** | `test_acp_unstable.py::test_acp_library_rejects_subagent_update`, `::test_acp_library_has_no_subagents_capability` (the tripwires), `::test_initialize_puts_subagents_capability_on_the_wire` (the whole `initialize` the agent receives), `::test_unstable_updates_reach_the_callback_in_wire_order`, `::test_stable_updates_still_reach_the_library_router`, `::test_malformed_unstable_update_is_dropped_with_a_warning` [#10]; *restored:* `::test_session_message_with_a_non_text_block_reaches_the_callback_whole` [#10] (P7). *Gone:* `test_patch_fields_tell_omitted_from_null` (the merge table's `title-null` pins it, P8, `a910ac9`); `test_custom_state_is_kept_whole` (cut with `extra="allow"`, `6b089e5`; a custom state's name is the merge table's `state-custom`); `test_message_content_keeps_non_text_blocks_typed` (`a910ac9`, restored as P7's test); `test_initialize_without_subagent_capabilities_is_the_library_call` (above) |
| **One opt-in per agent, off by default**, on the agent's settings and its agent profile | `tests/sdk/profiles/test_resolver.py::test_acp_profile_carries_the_subagents_opt_in_to_the_agent[False, True]` (it builds the agent, so it also pins `create_agent()`'s forwarding, P2), `::test_acp_seeded_profile_keeps_the_subagents_opt_in` [#13]; the v7 settings and v2 profile baselines, loaded by the `Persisted settings` guard and by `tests/cross/test_check_persisted_settings_compat.py::test_collect_fixture_cases_and_validate_current_repo_fixtures` [#13]; `acp-providers.test.ts › … › forwards the sub-agent opt-in` [#15]. *Gone:* `tests/sdk/test_settings.py::test_acp_create_agent_forwards_subagents` (`a910ac9`) |
| **The other SDK consumers** (§4.8) | `tests/sdk/agent/test_acp_dedup_and_truncation.py::…::test_remote_events_merge_child_and_root_calls_separately`, `tests/sdk/event/test_resume_transcript.py::…::test_resume_transcript_skips_child_tool_calls`, `tests/sdk/event/test_acp_subagent_events.py::test_subagent_events_visualize_their_essentials[3 kinds]`, `::test_unconfirmed_state_is_shown_as_such` [#11] |
| **The ordering C1 relies on** (§5 rule 10) | `test_acp_subagents.py::test_a_childs_stored_timestamps_never_decrease_in_log_order`, `::test_a_spawning_cells_started_event_precedes_its_whole_subtree` [#12], `::test_a_reconnect_snapshot_is_later_than_the_childs_earlier_events` [#16]; over REST, the cross test [#14] |
| **The fixture C1 and D5 reuse** (§4.10) | `test_acp_subagents.py::test_scripted_transcript_replays_a_recording[full, outgoing-only]` [#16]; *restored:* `::test_subagents_off_stores_only_root_work_through_the_stock_connection[--transcript]` (P4: without `subagents` the player sends no other session's update) and `::test_transcript_exits_non_zero_when_a_wait_point_outlasts_the_wait_timeout` (P6′) [#16]; every E5 test runs `--subagents`. *Gone:* `test_transcript_interval_paces_the_replay` and `test_transcript_wait_point_that_is_never_reached_exits_non_zero` (`6dcde3e`) |

**The three restored pins.** As-built r3 §8 found three properties whose only test the refactor had cut; each is pinned
again, and each new test was mutation-checked by the Implementer (its report on the task row; not re-run here):

- **P7**, `049ceb5` on #10: `test_session_message_with_a_non_text_block_reaches_the_callback_whole` sends a
  `session_message` holding a text and an image block over the wire and needs both blocks, typed, at the callback.
  Without that parse the shim drops such a message whole, its text included.
- **P4**, `306731d` on #16: `test_subagents_off_stores_only_root_work_through_the_stock_connection[--transcript]` plays
  a recording to a client that did not advertise `subagents`; a player that played every update would store the
  child's tool call as root work.
- **P6′**, `6a05b13` on #16: `test_transcript_exits_non_zero_when_a_wait_point_outlasts_the_wait_timeout` starts the
  agent with `--wait-timeout 0.2`, never sends `initialize`, and needs a non-zero exit within 10 s.

**What stays unpinned.** Three properties of the transcript player have no test:

- **Pacing (P5).** `--transcript-interval-ms` sleeps before each update a transcript sends (B8, which C1 asked for),
  and no test passes the flag. The cut test did not pin it either: at `a3279be`, with the flag ignored, it still
  passed (as-built r3 §8).
- **A missed wait point raising (P6).** `TranscriptPlayer.play` raises `TimeoutError` at a wait point the client never
  reaches. If it returned instead, the script would still exit non-zero, through another error (as-built r3 §8), so
  P6′'s test passes either way: it pins the exit, not its cause.
- **The unstable half of the conformance rule.** Without `subagents` the player must also skip the three unstable
  updates. No conversation can see whether it does: with the opt-in off the bridge uses the stock connection, whose
  library router drops those updates whatever the player sends. P4's case pins the other half, that no update for
  another session is sent.

Also unpinned, at Gate B or since the refactor (as-built r3 §8, §10): the bridge leaving a root call's `meta` unset
(P3); §5 rule 2's fallback placements (V-9); a child call's absence from the turn's trace (B4); and paths read but not
run: a notification without `sessionId`, an emitter's exception swallowed per event, `flush_all`'s loop body, and
`initialize` given other capabilities (V-2). Two properties have one test each: the route's 200 and its body, the
cross test (P9); `replaying()` clearing its flag through a real connection, the reconnect test (P10).

**Counts.** At `6a05b13` S1 adds **78** deterministic Python cases, **5** TypeScript cases and **2** live tests:
`a3279be`'s 88, 6 and 2, less the refactor's cuts (88 → 75, 6 → 5), plus the three restored. The 78: 48 in
`test_acp_subagents.py` (33 bridge units, 15 through a conversation), 7 in `test_acp_unstable.py`, 9 in
`test_acp_subagent_events.py`, 6 in `test_acp_router.py`, 2 in `test_event_service.py`, 3 in `test_resolver.py`, and
one each in the cross, dedup and resume-transcript files. By level: #10 7, #11 11, #12 39 and the live tree test, #13
3, #14 13 and the live stop test, #15 the 5 TypeScript cases, #16 5.

**Size.** S1's diff against the base each version was built on (`git diff --numstat`):

| | `a3279be` (Gate B), against `5e3317f` | `2675399` (the refactor), against `d938c90` | `6a05b13` (the stack's top), against `9277e71` |
|---|---|---|---|
| Source: code, CI and client configuration | +1,394 −51 | +1,302 −54 | +1,302 −54 |
| Tests, with the scripted agent and the baselines | +2,761 −5 | +2,388 −9 | +2,428 −9 |
| **Total** | **+4,155 −56, 43 files; about 14 h** | **+3,690 −63, 43 files; about 12.3 h** | **+3,730 −63, 43 files; about 12.4 h** |

Of the 1,302 lines of source, 1,143 are Python product code (`acp_agent.py` +294 −43, the router 299, the shim 222),
112 TypeScript and 47 CI and client configuration; of the 2,428 of tests, 1,658 are deterministic Python tests, 188
the live file, 442 the scripted agent, 113 TypeScript and 27 the baselines. The stack's seven levels add 3,741 between
them, about 12.5 h at Gate C, against the spec's ≈1.5k lines and ≈5 h.

## Gate B: what to read (approved at v2.2, kept as history)

*(v2.3)* This section is Gate B's, approved at v2.2: its evidence, size and test names are `a3279be`'s, before the
literate refactor. Gate C reads the two sections above; the property table at `6a05b13` replaces this one's. The
revision lines, build notes, file location and reading guide that ended this section are above it now.

**About 55 minutes, in this order.** The codebase stays closed. The Gate B set is this doc, S1's as-built document
(`as_built/s1-acp-subagent-sessions.md`, the Cartographer's, on deep-reasoning's `as-built/s1` and on this branch) and the runs
below. The rest (§2, §4, §6 onward and Appendix A) is kept whole as the reference C1, D5 and the later PR split
build against (Michael: don't force compression); Gate B does not need it.

| # | Read | What it gives you | Minutes |
|---|---|---|---|
| 1 | This section and the v2, v2.1 and v2.2 revision lines below it | where the proof is, which sentences of v1 changed, the ruling on size, and the fixes made before Gate B | 9 |
| 2 | §1 | what S1 changes, and the decisions under it (A, G, H and K carry v2 notes) | 7 |
| 3 | §3.1 | where the design departs from the spec: accepted at design on 2026-10-02, and which items still hold | 4 |
| 4 | §3.2 | what the build changed, each with its reason and the test that pins it, and the four uncovered edges, ruled and now built | 16 |
| 5 | §5 and §5.1 | the stored events C1 reads, and what C1 and D5 may rely on | 7 |
| 6 | Open the runs below | that they are green at `a3279be` | 3 |
| 7 | `as_built/s1-acp-subagent-sessions.md` (on this branch since `17ab4d5`) | what exists and its divergences, as the Cartographer read them | 9 |

**One thing to rule on: size.** The spec estimated S1 at ≈1.5k lines with tests and ≈5 h at Gate C (shim ≈150,
routing and persistence ≈450, endpoint ≈80, TypeScript client ≈150, tests ≈650); v1 at ≈1.8k (§3.1 item 16), without
the shared pieces, since S2 landed first. The build at `a3279be`, against S2's head `5e3317f`, is **4,155 lines added
and 56 removed** (3,486 non-blank lines added), in 43 files: 1,235 of Python code, 112 of TypeScript code, 74 of guard
and fixture data, 459 of the scripted test agent, 2,068 of deterministic tests (1,942 Python, 126 TypeScript) and the
207-line live file. The fixes made on v2.1's rulings are 125 of them. That is about 2.3 times v1's estimate and 2.8
times the spec's; at ≈300 lines an hour, Gate C reads it in about 14 h against the spec's ≈5 h. Two thirds of it is
tests and the fixture (2,734 lines against v1's ≈930); the code is 1,347 lines against v1's ≈940. The build recorded
no reason for the growth; the reading of this design is §3.2 B16. The Scout and the Refactorer, after Gate B, are
where it shrinks.

**The fixes, built (v2.2).** v2.1 ruled one bug to fix before Gate B and three edges to state (§3.2, "Edges the
build left open, ruled"). All four are built and pinned: E-2 in `d74940b` (nothing a `session/load` replay sends is
tracked, failed or stored), E-1 in `f6d8e1e` (at most one synthetic `failed` per child call; the agent's later
report wins), E-3 pinned in `e65335d`, and E-4 in `562c31d` (one warning per unannounced session); `a3279be` adds the
persisted agent-profile fixture C1 and D5 asked for. The branch also merged the fork's `deep-reasoning` (`0f161f8`,
which brings the fork-only `1f2b52d`: upstream's main-only guards now run on pull requests into the fork's branches)
and S2's new head (`2114d23`, merging `5e3317f`, with one conflict, in the scripted agent's flag list). The evidence
below is at `a3279be`; the runs v2 cited at `0cfb6a2` (CI 37105068562, live 37141960911) are superseded.

**The evidence.** Both at `a3279be`, the branch's head.

- **CI**, PR #2's 28 checks at `a3279be`, all green (the one not green, "Validate PR description", was skipped):
  - **Run tests**, [run 37146975823](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37146975823):
    `sdk-tests` **6,777 passed**, 7 skipped, 12 xfailed (2 min 45 s); `agent-server-tests` **2,440 passed**
    (5 min 41 s); `cross-tests` **497 passed**, 1 skipped (2 min 27 s); `acp-live-tests` 25 passed, 4 skipped, among
    the passed upstream's ACP conformance probe against six real agents (Claude Code, Codex, Gemini CLI, Kimi Code,
    Pi, OpenCode) with the opt-in off, so decision A on real providers, and among the skipped S1's two live tests,
    for want of an agent command there; and `tools-tests`, `workspace-tests`, `windows-tests`,
    `macos-app-backend-tests`, `agent-server-stress-tests`, `Test directory allowlist` and `coverage-report`.
  - **Upstream's main-only guards, now in CI** (`1f2b52d`):
    [REST API breakage checks](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37146975811)
    (`REST API (OpenAPI)`);
    [Persisted settings compatibility checks](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37146975832)
    (`Persisted settings`, which loads S1's v7 settings fixture and v2 profile fixture);
    [TypeScript client CI](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37146975745)
    (`build`, `test (22.12)`, `test (24.x)`, `public-type-budget`, `agent-server-api`, `security`,
    `validate-acp-providers`);
    [TypeScript client integration tests](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37146975836)
    (`smoke-test`, `integration-test`); and the
    [Version bump guard](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37146975831)
    (`Check package versions`), whose SDK API breakage step runs only when a package version changes, so it was
    skipped. Run locally (the Conductor's report), that step shows one upstream error, `ACPAgentSettings.llm`
    against PyPI 1.50.1, the same on the fork's `deep-reasoning`, and nothing of S1's.
  - [Pre-commit checks](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37146975749)
    (`pre-commit`: ruff format and lint, pycodestyle, pyright with the one suppression, the dynamic-attribute and
    import-rule checks), the
    [TypeScript client endpoint audit](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37146975855),
    [Check Docstrings](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37146975744) and
    [Deprecation deadlines](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37146975841).
  - **Not in CI:** the OpenAPI quality ratchet, which upstream runs only in its release workflow and the fork gives
    no pull-request trigger (it would start image pushes to ghcr that the fork cannot write). Run locally at
    `a3279be` (`make test-server-schema`, the Conductor's report), it passes, with 65 allowlisted locations: S2's
    `13e5904` cleared the one pointer of S2's that failed at v2.1 (§11 item 13).
- **Live tier**, deep-reasoning's `fork-live.yml`,
  [run 37147706623](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37147706623), dispatched on
  `ci/fork-live` (`a8154e2`: D1's `dr-acp` at `c8d7fbb` plus D5 §7.4's workflow file) with `sdk_ref` `a3279be`, both
  suites. Its step "S1, sub-agent sessions through the bridge" ran `tests/sdk/agent/test_acp_subagents_live.py`:
  **2 of 2 passed** in 41.3 s, `test_live_agent_tree_is_well_formed` and
  `test_live_agent_stops_one_subagent_and_its_branch`, with `dr-acp` on gpt-6-luna (D1's
  `docs/configs/advising/main.yaml`) and the prompt "/compare-departments Which department is lighter for a
  first-year student, CS or STAT?". The run is on demand only (cents per run). Its S2 step passed too (8 of 8); that
  is S2's evidence.

**Which tests carry which property.** Each test's name states the property it pins. Python files are in the SDK
fork under `tests/sdk/agent/` unless a path is given; TypeScript ones under `clients/typescript/src/__tests__/`, where
`›` separates `describe` blocks; `[…]` is a parametrization. S1 adds 88 deterministic Python cases (52 of them in
`test_acp_subagents.py`), 6 TypeScript cases and the 2 live tests, at `a3279be`.

| Property | Tests |
|---|---|
| **E5 · The stored events rebuild the agent's tree**: each child under its parent session and the call that spawned it, each session's own calls, messages, text and cost | `test_acp_subagents.py::test_scripted_run_stores_the_scripted_tree` (the scripted agent's run, three children and a grandchild, through a real `LocalConversation`); `::test_scripted_transcript_replays_a_recording[full, outgoing-only]` (a JSONL recording, also in the agent-outgoing-only shape of D1's golden files); the routing units `::test_announcement_stores_parent_cell_and_cancel_grant`, `::test_parent_tool_call_id_survives_meta_without_it`, `::test_child_is_never_reparented_nor_its_own_parent`, `::test_child_tool_calls_are_keyed_by_session_and_tool_call_id`, `::test_omitted_field_keeps_value_and_null_clears_it[10 patches]`, `::test_unannounced_session_follows_the_root_path_with_one_warning`, `::test_unstable_updates_on_an_unannounced_session_stay_under_that_session` (E-4); **live:** `test_acp_subagents_live.py::test_live_agent_tree_is_well_formed` |
| **E5 · No child text reaches the root's answer** | `test_acp_subagents.py::test_scripted_run_keeps_child_text_out_of_the_answer`, `::test_child_text_never_reaches_the_root_answer`; **live:** `test_live_agent_tree_is_well_formed` (no stored child text of 40 characters or more appears in the answer) |
| **E5 · The stored events break no client** (the spec's "stock Canvas erroring on the stored events") | `tests/agent_server/test_acp_router.py::test_stored_sub_agent_events_validate_against_the_event_schema` (every event of a real run, read over REST, validates against the agent-server's published `Event` schema); `tests/sdk/event/test_acp_subagent_events.py::test_subagent_events_round_trip_through_json[4 events: the three kinds and a child's call]`; `event-types.test.ts › ACP sub-agent session events › sub-agent event shapes accept stored events`. Stock Canvas drops kinds it does not know (`should-render-event.ts`); how they render is C1's E6 |
| **Old conversations load unchanged, and with the opt-in off nothing changes** | `tests/sdk/event/test_acp_subagent_events.py::test_legacy_acp_tool_call_event_loads_without_session_fields`, `::test_root_tool_call_event_is_stored_as_before`; `test_acp_subagents.py::test_subagents_off_uses_the_stock_connection_and_initialize`, `::test_scripted_run_with_subagents_off_stores_only_root_work[--subagents, --transcript]`; upstream's suites, unchanged and green, and its conformance probe against six real agents (`acp-live-tests`) |
| **A child's own text and reasoning are stored** (§3.1 item 1, the third kind), per segment, in order; directed messages whole | `test_acp_subagents.py::test_child_text_is_stored_per_segment_in_transcript_order`, `::test_usage_never_splits_a_text_segment`, `::test_chunked_message_is_stored_whole_at_the_next_boundary`, `::test_message_upsert_replaces_content_and_keeps_participants` |
| **A child's cost is on its association and never added** | `test_acp_subagents.py::test_child_cost_is_on_its_association_and_never_booked_to_the_conversation`, `::test_child_usage_leaves_root_usage_sync_and_context_window_alone`, `::test_scripted_run_books_only_the_roots_cost`; **live:** `test_live_agent_tree_is_well_formed` (the conversation's cost equals the root's last reported cost) |
| **Child traffic after the parent's turn is stored, not dropped**, and every child event takes one ordered path | `test_acp_subagents.py::test_child_traffic_between_turns_reaches_the_emitter_in_order`, `::test_child_events_go_to_the_session_emitter_and_root_events_to_the_turn`, `::test_child_events_without_an_emitter_are_dropped_with_a_debug_line`, `::test_turn_end_force_completes_only_root_tool_calls`, `::test_aborted_turn_fails_child_tool_calls_with_their_session`, `::test_child_call_open_across_aborted_turns_is_failed_once_and_the_agents_report_wins` (E-1) |
| **Cancel one child**: `session/cancel` only for a child that holds a live grant, the spec's 409 otherwise, never waiting for the state lock | `test_acp_subagents.py::test_cancel_acp_session_reaches_the_child_and_its_cancelled_state_is_stored`, `::test_cancel_acp_session_does_not_wait_for_the_state_lock`, `::test_cancel_acp_session_refuses_a_child_without_a_grant`, `::test_cancel_acp_session_refuses_unknown_and_root_sessions`, `::test_cancel_acp_session_without_a_live_connection_is_refused`, `::test_cancel_acp_session_for_an_idle_child_that_keeps_its_grant_is_sent` (E-3); the route on a real agent-server, `tests/agent_server/test_acp_router.py::test_a_cancel_reaches_the_child_and_its_cancelled_state_is_stored`, `::test_a_cancel_for_an_unknown_conversation_is_not_found`, `::test_a_cancel_for_an_unknown_session_is_not_found`, `::test_a_cancel_for_a_child_without_a_grant_is_a_conflict`, `::test_a_cancel_on_a_conversation_that_is_not_acp_is_a_bad_request`, `::test_a_cancel_the_agent_does_not_take_in_time_times_out`; `tests/agent_server/test_event_service.py::TestEventServiceCancelACPSession::test_cancel_acp_session_runs_off_the_event_loop`, `::test_cancel_acp_session_on_an_inactive_service_is_refused`; end to end over REST and the WebSocket, `tests/cross/test_remote_conversation_live_server.py::test_acp_subagent_sessions_over_live_server`; `api-clients.test.ts › ACP sub-agent sessions › …` (3); **live:** `test_acp_subagents_live.py::test_live_agent_stops_one_subagent_and_its_branch` |
| **After `session/load`, associations are kept and controls stay off until fresh state arrives** | `test_acp_subagents.py::test_replay_is_neither_stored_nor_grants_cancel`, `::test_new_connection_withdraws_cancel_and_unconfirms_state`, `::test_partial_patch_after_reconnect_keeps_the_stored_title`, `::test_a_reconnect_snapshot_is_later_than_the_childs_earlier_events` (a second connection to the same conversation), `::test_replayed_child_calls_are_never_tracked_nor_failed_later` (E-2) |
| **The shim, and the tripwire that deletes it** | `test_acp_unstable.py::test_acp_library_rejects_subagent_update` and `::test_acp_library_has_no_subagents_capability` (the tripwires); `::test_initialize_puts_subagents_capability_on_the_wire`, `::test_initialize_without_subagent_capabilities_is_the_library_call`, `::test_unstable_updates_reach_the_callback_in_wire_order`, `::test_stable_updates_still_reach_the_library_router`, `::test_malformed_unstable_update_is_dropped_with_a_warning`, `::test_patch_fields_tell_omitted_from_null`, `::test_custom_state_is_kept_whole`, `::test_message_content_keeps_non_text_blocks_typed` |
| **One opt-in per agent, off by default**, on the agent's settings and its agent profile (§3.2 B2) | `tests/sdk/test_settings.py::test_acp_create_agent_forwards_subagents`; `tests/sdk/profiles/test_resolver.py::test_acp_profile_carries_the_subagents_opt_in_to_the_agent[False, True]`, `::test_acp_seeded_profile_keeps_the_subagents_opt_in`; the v7 settings fixture `agent_settings_acp_subagents.json` and the v2 profile fixture `agent_profile_acp_subagents.json` (v2.2), both loaded by the `Persisted settings` guard and validated by `tests/cross/test_check_persisted_settings_compat.py::test_collect_fixture_cases_and_validate_current_repo_fixtures`; `acp-providers.test.ts › … › forwards the sub-agent opt-in` |
| **The ordering C1 relies on** (§5 rule 10, §3.2 B11) | `test_acp_subagents.py::test_a_childs_stored_timestamps_never_decrease_in_log_order`, `::test_a_reconnect_snapshot_is_later_than_the_childs_earlier_events`, `::test_a_spawning_cells_started_event_precedes_its_whole_subtree`; over REST, `test_acp_subagent_sessions_over_live_server` |
| **The fixture C1 and D5 reuse** (§4.10) | `test_acp_subagents.py::test_scripted_transcript_replays_a_recording[full, outgoing-only]`, `::test_transcript_interval_paces_the_replay`, `::test_transcript_wait_point_that_is_never_reached_exits_non_zero` |

Not carried by S1's tests: E5's replay of D1's actual golden recordings into the pinned agent-server. That is D5's
`bridge-replay` job (D5 §7.5), not built yet; S1's part of it, the scripted agent's `--transcript` mode, is pinned on
hand-written transcripts of the same shape. *(v2.1)* The Cartographer's uncommitted probe replayed all nine of D1's
native golden recordings (`c8d7fbb`) through `--transcript` into the bridge: 9 of 9 stored trees, call ids and final
states equal the recordings' (as-built §7.3; its own comparator, not D1's `testing.tree()`; costs not compared). §7
maps every test file.

---

## 1 · What S1 changes

### 1.1 The problem, at `53a4bc5`

An ACP agent that exposes sub-agent sessions (ACP schema 1.24.1, unstable since 2026-09-30) cannot be driven
through OpenHands' bridge today, for four reasons, each verified:

1. **The bridge never asks.** It calls `initialize` with no client capabilities (`acp_agent.py:3090`), so a
   conforming agent may not send sub-agent updates at all (the RFD: an agent MUST NOT unless the client
   advertised `subagents`). Even if it asked, ACP Python 0.12.1's `ClientCapabilities` has no `subagents`
   field, and its `initialize` serializes by the declared type, so the field is dropped on the way out.
2. **The library drops the updates.** 0.12.1's router validates every `session/update` against
   `SessionNotification`, whose union has no `subagent_update`, `session_message` or `session_message_chunk`:
   each one fails with a `ValidationError` inside the library (`acp/router.py`, `model.model_validate`) and is
   logged as an exception; the bridge never sees it.
3. **Everything else is merged into the root.** `session_update` (`acp_agent.py:1427–1548`) routes nothing by
   session except the `ask_agent` fork (`:1445–1451`). A child's `agent_message_chunk` joins the root's answer,
   its tool calls are stored as if the root ran them, and a child's `usage_update` overwrites the bridge's
   context-window fallback (`:1471–1478`).
4. **Nothing can stop one child.** There is no route, SDK call or client method that sends `session/cancel`
   for a session other than the root.

### 1.2 The change

Behind one opt-in per agent (`acp_subagents`, default off; *(v2, B2)* settable on the agent, its settings and its
agent profile), the bridge advertises `subagents`, receives the three unstable updates through a small shim ahead of the library's router, routes every update by session, and
persists each child: its association with its parent (with the spawning tool call), its tool calls, its
messages, its own text and its latest cost. A new REST call cancels one child that offers `cancel`. With the
opt-in off, nothing changes: the stock connection class, the stock `initialize` call, the stock routing, and
byte-identical stored events.

```text
ACP agent process (dr-acp, or any agent speaking schema 1.24.1's sub-agent sessions)
   │ stdout, JSON-RPC lines
   ▼
_filter_jsonrpc_lines (unchanged, :1047)
   ▼
SubagentClientSideConnection  ── acp_unstable.py (THE SHIM; deleted when the library catches up)
   │  session/update with sessionUpdate ∈ {subagent_update, session_message, session_message_chunk}
   │     → parsed by the shim's models → bridge.unstable_session_update(sessionId, update)
   │  everything else → the library's own router → bridge.session_update(...) as today
   ▼
_OpenHandsACPBridge (acp_agent.py)
   │  commands, options → S2's recorder (its first line in session_update; not S1's)
   │  fork session      → fork accumulator (unchanged)
   │  root or unknown   → today's path (answer text, thoughts, root tool calls, root usage)
   │  announced child   → ACPSubagentSessions (acp_subagents.py): merge, segment, cost
   │                       child tool calls: today's tool-call path, keyed by (session, toolCallId)
   ▼
root events:  the turn's on_event, as today
child events: ACPAgent._on_session_event = LocalConversation._emit_event_from_any_thread
              (shared with S2, and S2's code (v2, B1): one worker, first in first out, takes the
              state lock; the ACP thread only submits), during a turn and between turns alike
   ▼
ConversationState.events ── REST /events/search, WebSocket ── TS client ── Canvas (C1)

cancel: POST /api/conversations/{id}/acp/sessions/{session_id}/cancel   (acp_router.py, S2's module)
        → EventService → LocalConversation.cancel_acp_session → ACPAgent.cancel_acp_session
        → (on the ACP loop) check the live cancel grant → session/cancel {sessionId: child}
        → the agent's own idle/cancelled update arrives and is persisted like any other
```

### 1.3 Decisions this design takes

The spec's decisions stand (§2: generic and additive, ACP's names, `_meta.deep_reasoner` never read; S1's
bullets). These are the next layer down.

| # | Decision | Why | Rejected |
|---|---|---|---|
| A | **One opt-in gates everything**: `ACPAgent.acp_subagents` / `ACPAgentSettings.acp_subagents`, default `False`. Off: the stock `ClientSideConnection`, the stock `initialize(protocol_version=1)` call, today's routing, and no new fields written. | Claude Code, Codex and Gemini run exactly as today while ACP's draft is unstable; every upstream test that patches `acp_agent.ClientSideConnection` or spies `ClientSideConnection.initialize` (the conformance probe, `test_acp_conformance.py`) keeps working untouched. *(v2, B2: the field is also on `ACPAgentProfile`, forwarded by the profile resolver and carried back by the seed, because Canvas starts conversations from the active agent profile.)* | Routing by session for every agent: a behaviour change for providers that never asked for it. |
| B | **The shim is a `ClientSideConnection` subclass** that wraps its connection's handler and sends `initialize` with a standalone request model carrying `subagents`. It needs one targeted pyright suppression, because 0.12.1 marks the class `@final` (verified). *(v2.3, V-2, `bf57a3a`: the request model is no longer standalone. `_SubagentInitializeRequest` subclasses `InitializeRequest` and declares `client_capabilities` as `SerializeAsAny[ClientCapabilities] \| None`, a wider type than the parent's, so pyright accepts it and serialization keeps the subclass's `subagents`; and the connection's `initialize` always advertises `subagents` unless given other capabilities, so the bridge makes one call for both connection classes. The wire is unchanged, as-built r3 §2.)* | The fewest lines that keep every message in arrival order, keep the library's router for everything stable, and put the capability on the wire. | (1) Connection observers (`Connection(..., observers=)`, public): the router still raises and logs an exception per unstable update, and every incoming message is deep-copied. (2) Rewriting unstable updates into an extension method in the stdout filter: in order and public, but it hides a protocol message behind a fake one. (3) Re-implementing `ClientSideConnection` from `Connection` and `build_client_router`: duplicates ~250 library lines. (4) Subclassing `InitializeRequest` with a narrower field type: fails pyright's variable-override check (verified). |
| C | **A session is a child iff it was announced** (a `subagent_update` on this connection, or a child recorded in this conversation's history). Traffic for any other non-root session follows today's root path, with one WARNING per session id. | The RFD makes announcement-before-traffic the agent's obligation; routing by announcement keeps every existing bridge test (which sends updates under arbitrary session ids) valid. | Treating every non-root id as a child: an unannounced id has no parent to place it under. *(v2.1, E-4: the root path is for stable updates, which reached the root before S1; the three unstable updates on such a session stay under its id, so a child announced there is "could not be placed".)* *(v2.3, V-1, `73e47f8`: both paths warn through one helper, `_warn_unannounced(session_id, routing)`, once per session per path, so a session that sends stable and unstable updates draws two WARNINGs.)* |
| D | **One persisted snapshot per association change**: `ACPSubagentEvent` carries the whole merged association (the RFD's patch rules already applied). | Consumers keep the latest per session; nobody re-implements "omitted keeps, `null` clears, an object replaces" in TypeScript. | Persisting raw patches. |
| E | **The root is `None` in persisted routing fields** (`acp_session_id`, `parent_session_id`); message participants are stored verbatim. | Mirrors the spec's "`acp_session_id` absent = root"; survives the bridge falling back to a fresh ACP session after a failed `session/load`, when the root's id changes but its children stay under the root. | Storing the root's ACP id everywhere: a fallback session would orphan every earlier child. |
| F | **A child's own streamed text is persisted per segment**, as a third event kind, `ACPSessionTextEvent` (a divergence, §3.1 item 1; accepted at design, v2). | D1 sends each child's reasoning and its Stop acknowledgement as `agent_thought_chunk` on the child's session; the RFD models a child as a full transcript. Without it, both are dropped. | Dropping child text (spec reading); merging it into the root (today's bug). |
| G | **Every child event goes through the conversation's one ordered emitter, during a turn and between turns**: `ACPAgent._on_session_event`, which `LocalConversation._ensure_agent_ready` wires to `_emit_event_from_any_thread` (one worker, first in first out, which takes the state lock and calls `_on_event`). The same primitive S2 uses for commands and options (S2 decision B). The root's events keep today's path, and the root's trailing traffic between turns stays dropped, as today. | The spec's "persisted, not dropped", without the ACP thread ever taking the state lock (a deadlock under the synchronous `run()`, §6). One path per stream means a child's events can never overtake each other, which "latest wins" needs. One primitive in both PRs, not two. *(v2, B1: S2 landed first and built it; S1 uses it unchanged.)* | (1) The turn's `on_event` during a turn and a second sink between turns: two paths reorder at the boundary. (2) A deferred queue persisted at the next turn (this design's first draft): late traffic waits for a turn that may never come. (3) Child tool calls on the turn's `on_event` and child text through the emitter: a child's thought could be stored after the cell it preceded. |
| H | **Cancel authorization is in memory, per connection, and only from fresh updates.** A grant counts only when it arrived after the `session/load` response; when a connection starts, the bridge persists, for each child whose last snapshot was cancellable or active, a snapshot with `source="environment"`, `cancellable=False` and `state=None`. *(v2, B3: for each child whose last snapshot was active, a `state` other than `None` and `"idle"`; every grant is still withdrawn.)* | The RFD's freshness rule: historical capabilities never authorize a mutation, and current state starts unconfirmed after a reconnect; the stored events say so, so C1 hides Stop. | Trusting the last persisted `cancellable` (a Stop that answers 409 or, worse, cancels a reused id). |
| I | **Cancel never takes the conversation's state lock.** It runs on the ACP loop, checks the grant there, sends `session/cancel`, and returns; the outcome arrives as the child's own update. | The sync run loop holds the state lock for a whole turn; a lock-taking cancel would wait for the turn it is trying to shorten. | Routing cancel through `with state:` as `switch_acp_model` does. |
| J | **Costs are never added.** A child's cost lives on its association; `_record_usage` keeps booking only the root's, as today (`:2046`). | ACP forbids clients to add parent and child costs; D1's root cost already covers its descendants. | Summing children into the conversation's metrics. |
| K | **One scripted test agent, `tests/fixtures/acp/scripted_agent.py`, shared with S2** (S2 Appendix C): S2's behaviours by default, S1's behind its own flags, `--subagents` (a built-in sub-agent run) and `--transcript PATH` (replays any JSONL transcript, including D1's golden recordings). It needs only `agent-client-protocol`, so it runs by path from a checkout of the SDK fork. *(v2, B1, B8: S2 created the script; S1 added `--subagents`, `--cancel-wait`, `--transcript`, `--transcript-interval-ms` and `--wait-timeout`.)* | One fixture for the spec's "built in S1, reused in C1, S2 and C2"; `tests/fixtures` is shared by the SDK and agent-server suites. D5's cross-repo CI already checks out the fork at its pinned tag (spec Q8), and so can Canvas's mock-LLM end-to-end run (C1, C2). | Shipping it in the SDK wheel as `openhands.sdk.testing.scripted_acp_agent` (this design's first draft): `python -m` from any install, but a test fixture in the product package, and a second fixture beside S2's. |

---

## 2 · A sub-agent's life through the bridge

The spec's S1 mock-up, in wire order, with what the bridge stores. Ids are D1's (§5.1 of its design), shown in
its short form (`n2` is `20261002-142233-4f1a2b-n2`, `c1.1` is `…-n1-c1`); the wire and the store always carry the
full ids.

1. **Start.** `LocalConversation._ensure_agent_ready` sets `agent._on_session_event` to the conversation's
   emitter, then calls `init_state` → `_start_acp_server` (*v2, B1:* → `_launch_acp_session`, which S2 split out
   of it). The bridge is built with `subagents=True` and handed
   that emitter; its `ACPSubagentSessions` is seeded from this conversation's stored events (nothing on a first
   start). The connection is a `SubagentClientSideConnection`; `initialize` goes out with
   `"clientCapabilities": {"auth": {}, "subagents": {}}` (the library's own defaults plus ours, verified on the
   wire). `session/new` answers `s-7c1f…`, which the router records as the root.
2. **Prompt.** `_reset_client_for_turn` wires the turn's `on_event`, as today; S1 does not touch it.
3. **The spawning cell.** `root tool_call c1.1` → today's path → `ACPToolCallEvent` (no `acp_session_id`),
   stored at once through the turn's `on_event`.
4. **The announcement.** `root subagent_update n2 {title, capabilities.cancel, state running,
   _meta.openhands.parentToolCallId = c1.1, _meta.deep_reasoner = …}` reaches the bridge through the shim →
   `ACPSubagentEvent(acp_session_id=n2, parent_session_id=None, parent_tool_call_id=c1.1, state="running",
   cancellable=True, meta={…})`, submitted to the emitter, like every event from steps 4 to 10. `n2` is now a
   child. (In the agent-server, which drives `arun()`, the emitter's worker stores each event as it comes,
   because the state lock is free while a prompt is awaited; under a synchronous `run()` they are stored right
   after the step.)
5. **The task.** `root session_message → n2` → `ACPSessionMessageEvent(acp_session_id=None, message_id=…-n2-t1,
   sender=s-7c1f…, recipient=n2, text=task)`.
6. **The child thinks.** `n2 agent_thought_chunk` → appended to `n2`'s pending text segment; nothing stored yet,
   and nothing reaches the root's thoughts.
7. **The child's cell.** `n2 tool_call c2.1` → flushes the segment as `ACPSessionTextEvent(acp_session_id=n2,
   thought=True, text=…)`, then today's tool-call path with the entry keyed `(n2, c2.1)` →
   `ACPToolCallEvent(acp_session_id=n2, meta={deep_reasoner: …})`; its `tool_call_update` → the terminal
   `ACPToolCallEvent`.
8. **The answer.** `n2 session_message → root` → `ACPSessionMessageEvent(acp_session_id=n2, …)`.
9. **The cost.** `n2 usage_update cost 0.0004 USD` → the association's cost changes →
   `ACPSubagentEvent(n2, state="running", cost=0.0004, cost_currency="USD")`. The root's usage sync, its
   context window and the conversation's metrics are untouched.
10. **Idle.** `root subagent_update n2 {state idle, stopReason end_turn, _meta …}` →
    `ACPSubagentEvent(n2, state="idle", stop_reason="end_turn", cost=0.0004, cancellable=True)`.
11. **The root finishes.** `root tool_call_update c1.1 completed`, the root's `agent_message_chunk`s, the root's
    `usage_update`, the response. At the end of `_do_acp_prompt` the bridge submits every child's pending text;
    `_finalize_successful_turn` books the root's cost only, force-completes only root tool calls left open, and
    stores the `FinishAction` with the root's text alone.

What `GET /events/search` then holds for the sub-agent part (the mock-up's `jq` line, against the real route):

```bash
curl -s "$AS/api/conversations/$C/events/search?limit=100" | jq -r '.items[] | select(.kind | startswith("ACP"))
  | [.kind, .acp_session_id // "root", .state // .title // .text // ""] | @tsv'
```

```text
ACPToolCallEvent         root   Run cs = [...]; summaries = run_all({...})
ACPSubagentEvent         n2     running        (parent root, in c1.1, cancellable)
ACPSessionMessageEvent   root   Summarize the workload of CS101.
ACPSessionTextEvent      n2     CS101's record: credits and prerequisites, then a one-line verdict.
ACPToolCallEvent         n2     Run c = catalog['CS101']; print(c['credits'], len(c['prereqs']))
ACPToolCallEvent         n2     Run c = catalog['CS101']; ...                      (completed: 3 0)
ACPSessionMessageEvent   n2     3cr, 0 prereqs — light
ACPSubagentEvent         n2     running        (0.0004 USD)
ACPSubagentEvent         n2     idle           (end_turn, 0.0004 USD)
ACPToolCallEvent         root   Run cs = [...]; summaries = run_all({...})        (completed)
```

**Stop on one child.** `POST …/acp/sessions/n3/cancel` → 200 `{"session_id": "…-n3", "requested": true}`. The
bridge sent `session/cancel {"sessionId": "…-n3"}`; dr-acp acknowledges with a thought on `n3` (stored as an
`ACPSessionTextEvent` at the next boundary) and, as each agent of the branch actually ends, sends its idle
`subagent_update` with `stopReason: cancelled`, each stored as an `ACPSubagentEvent`. A child that did not
advertise `cancel`: 409, `ACP session fx2 does not accept cancel; cancel the conversation's turn instead.`

**Restart.** The agent-server restarts mid-run. On the next message, `_start_acp_server` seeds the router from
the stored events (n2…n4 are known children) and, for each child whose last snapshot was cancellable or active
(*v2, B3:* active only, so an idle `n2` gets none),
submits `ACPSubagentEvent(source="environment", state=None, cancellable=False)`; then it calls `session/load`.
dr-acp replays its run log before the response, which the bridge neither stores again (it is already stored)
nor lets authorize anything. C1 shows those children with unconfirmed state and no Stop.

---

## 3 · Departures from the spec, and what the build changed

§3.1 is where this design departs from the approved spec (v1, kept as written, with a v2 note on each item). §3.2 is
what the build changed in this design (v2). None is a re-scope.

### 3.1 Where this design departs from, or adds to, the approved spec

Each is a refinement inside S1's scope. If the Conductor reads any as a change of what was approved, it goes back
to Michael. *(v2: the Conductor accepted them at design, the third stored kind included: spec, "Rulings at design,
2026-10-02" (3), "S1's and S2's design departures (§3 of each) are accepted by the Conductor as refinements of our
own interfaces", approved by Michael ('commit', 'yes'). Each item's v2 note says whether it still holds at
`0cfb6a2`.)*

1. **A third persisted kind, `ACPSessionTextEvent`, for a child's own `agent_message_chunk` and
   `agent_thought_chunk`.** The spec names two kinds (the association and the directed message). D1 sends each
   child's reasoning and, by its §3 item 9, its Stop acknowledgement ("said where the user sees them") as thoughts
   on the child's session; with two kinds the bridge has nowhere to put them and they are lost. Text is stored
   per segment (consecutive chunks of one kind in one session), not per chunk. About 60 lines with tests.
   *(v2: holds. Built as described, `event/acp_subagent.py:135–160`; D1's Stop acknowledgement and each child's
   reasoning are stored, and the live run's branch Stop went through it.)*
2. **`ACPSubagentEvent.parent_tool_call_id` is a typed field**, lifted from `_meta.openhands.parentToolCallId`
   (the generic key of spec §2 decision 3), and sticky: an update whose `_meta` lacks the key, or clears
   `_meta`, does not move the child out of its cell. `meta` itself is stored verbatim (masked), so
   `_meta.deep_reasoner` passes through unread. *(v2: holds; `acp_subagents.py:256–261`.)*
3. **The shim needs one pyright suppression and a standalone `initialize` request model.** 0.12.1 marks
   `ClientSideConnection` `@final`; subclassing it fails pyright `standard` ("Base class … is marked final",
   verified), so the class line carries `# pyright: ignore[reportGeneralTypeIssues]` with a one-line reason.
   Subclassing `InitializeRequest` with the capability subclass also fails (`reportIncompatibleVariableOverride`,
   verified), so the request model is a small standalone model. Both verified to put `subagents` on the wire.
   *(v2: holds; `acp_unstable.py:143–157`, and pre-commit's pyright passes with that one suppression.)* *(v2.3, V-2:
   the suppression holds, `acp_unstable.py:140`; the request model is now a subclass of `InitializeRequest` after
   all, widening `client_capabilities` to `SerializeAsAny[ClientCapabilities] | None` rather than narrowing it,
   which pyright accepts, `:129–134`.)*
4. **`ACPToolCallEvent.acp_session_id` and `meta` are written only with the opt-in on.** The spec says the event
   gains them; populating `meta` for every agent would change Claude Code's stored events (its adapter puts tool
   output in `_meta`), against decision A. *(v2: holds; with the opt-in off both are `None`, so the stored dump
   is today's.)*
5. **The cancel route has five outcomes, not two**: 200; 404 (no conversation, or no sub-agent session with that
   id); 400 (not an ACP conversation, matching `switch_acp_model`); 409 (no live connection, the root session, or
   no current `cancel` grant); 504 (the notification was not written within 2 s). The spec's 409 text is kept
   verbatim. *(v2: holds; `acp_router.py:168–227`, each outcome pinned against a real server.)*
6. **Child traffic after the parent's turn is stored as it arrives**, through S2's emitter (decision G). It is
   lost only if it is still queued when `close()` cancels the emitter's pending jobs, or arrives after that
   (dropped with a DEBUG line, S2's emitter semantics). dr-acp sends none (D1 §5.4 rule 7). Under a synchronous `run()`, a turn's child events are stored
   just after the step's own events; C1 places children by id, not by position, so nothing reads that order.
   *(v2: holds; the emitter is S2's, B1.)*
7. **A reconnect writes "controls off, state unconfirmed" snapshots** (`source="environment"`), so the stored
   events, not only the bridge's memory, carry the RFD's freshness rule. Between an agent-server crash and the
   next connection the old snapshot still shows; the route answers 409 there. *(v2: holds, narrowed: only for a
   child whose last stored state was active, B3.)*
8. **The generic fixture is S2's scripted test agent** (`tests/fixtures/acp/scripted_agent.py`) with S1's flags,
   one of which replays JSONL transcripts in D1's recording format (§4.10). Canvas (C1, C2) and D5 run it by path
   from a checkout of the SDK fork at the pinned tag. *(v2: holds; S2 created the script, B1, and S1 added one
   more flag, `--transcript-interval-ms`, B8.)* *(v2.3: and eleven wire builders its tests share, V-6; at Gate C the
   transcript player is its own level, #16, at the top of the stack.)*
9. **The cancel route lives in S2's new `acp_router.py`**, on its `conversation_acp_router` (prefix
   `/conversations/{conversation_id}/acp`), not in `conversation_router.py`. *(v2: holds; S2 created the
   module, B1.)*
10. **The TypeScript client's new event types are hand-written** until upstream's pinned release artifact
    carries them (its generated schema is pinned to a release, `package.json` `config.agentServerImage`), and the
    new route is listed as client-ahead in `endpoint-audit.config.json`. `ACP_SETTINGS_KEYS` gains
    `acp_subagents`, or Canvas would strip the opt-in when it filters an ACP settings payload. *(v2: holds;
    also `ACPAgentProfile.acp_subagents?`, B2, and three entries in the client's public type budget, B15.)*
11. **Upstream's guards, checked:** the OpenAPI breakage check explicitly allows additive `oneOf` expansion and
    optional response properties (`check_agent_server_rest_api_breakage.py`, rules at `:29–33, :571`), so no
    migration is needed; the persisted-settings change is additive (no schema bump), with a new v7 fixture; and
    the OpenAPI weak-schema ratchet (`check_agent_server_openapi_quality.py`, run on the exported schema by the
    release workflow, `release-binaries.yml:215`, against an exact allowlist) flags every new `dict[str, Any]`,
    so each `meta` field gets an allowlist entry, as `raw_input`/`raw_output` have today. ACP's `_meta` is an
    arbitrary object by protocol, so it cannot be typed away as S2's fields are. *(v2: the expected results are
    reported, not shown in CI: the guards that run only for pull requests to `main` ran locally, B14; the
    allowlist has three entries, B15.)*
12. **Directed messages store text only** (the spec's field); non-text content blocks are counted in a DEBUG line
    and not stored. *(v2: holds.)*
13. **The mock-up's `GET /events` is `GET /events/search`** in the real API (`event_router.py:68`). *(v2:
    holds.)*
14. **No optimistic cancel marking.** The RFD says a client SHOULD mark a cancelled child's unfinished tool calls
    as cancelled; D1's Stop lands at the agent's next turn and lets a running cell finish, so a client-side
    "failed" would be contradicted moments later. The bridge stores only what the agent reports. *(v2: holds for
    a child's cancel; a cancel or abort of the root's own turn still fails every open call, children's included,
    §4.4.)*
15. **Four more SDK consumers change, which the spec did not list:** the Python `RemoteConversation` event cache
    keys ACP tool calls by `(session, id)`; `render_resume_transcript` skips child tool calls; the default
    visualizer gets entries for the three kinds; `LocalConversation` gains `cancel_acp_session` (and, if S1 lands
    before S2, the shared emitter). Upstream's checklist ("trace cross-layer changes through every affected
    public entry point") asks for exactly these. *(v2: holds; `LocalConversation` gains only
    `cancel_acp_session`, since the emitter is S2's, B1; two more consumers changed: the agent profile, B2, and the
    turn's trace, B4.)*
16. **Size:** about 1.8k lines with tests, not the spec's 1.5k: the third kind (+60), the fixture's sub-agent and
    transcript modes (+180), the extra consumers (+60), the TS hand-written types (+60). If S1 lands before S2,
    it also carries the shared emitter and the fixture's skeleton (about +120 more), which S2 then does not.
    *(v2: superseded by B16: 4,030 lines added; S2 carried the shared pieces.)* *(v2.3: 3,730 at `6a05b13`, after the
    refactor; the section after the Gate C section.)*

### 3.2 Changed by the build (v2)

Each was found by reading S1's five commits (`6f97bf3..0cfb6a2`) against v1, checked against the code at `0cfb6a2`,
and folded into the sections named. B1 is where S1 sits; B2–B6 change or decide behaviour; B7 is the signatures;
B8–B10 the fixture; B11–B13 how the tests prove it; B14 and B15 the pull request and upstream's guards; B16 the
size; B17 what this design could not check. Where the build recorded no reason (in a commit message, a code comment
or PR #2's description), the reason given is marked as this design's reading.

*(v2.1)* The as-built document (`as_built/s1-acp-subagent-sessions.md`, `17ab4d5`, §2) found thirteen divergences;
each is here: D-1 is B3, D-2 B2, D-3 B4, D-4 B1, D-5 B14, D-6 B8, D-7 B9, D-8 B10, D-9 and D-10 B12, D-11 B13, D-12
B15, D-13 B16, and its §2.5 rows are B6, B7 and §4.2's note. Its §4.5 edges are ruled at the end of this section
(E-1 to E-4).

*(v2.2)* The rulings are built, at `a3279be`: each E-item and B2, B5, B14, B16 and B17 carry a note saying where.

*(v2.3)* The literate refactor changed the names some of these entries give (the header's "Changed by the
refactor"); B7, B8, B10, B12, B14, B16, B17 and E-4 carry a note. Behaviour is as these entries state it.

**Where S1 sits**

- **B1. S2 landed first, and S1 is stacked on it** (the header, §1.3 G and K, §2 step 1, §4.1, §4.4, §4.10, §8,
  §9, §11 item 5). The branch starts at S2's `feat/agent-surfaces` `6f97bf3` (which carries the fork's
  `deep-reasoning` up to `ea51b3f`), not at `deep-reasoning` `91430aa`, and PR #2's base is `feat/agent-surfaces`.
  The three shared pieces are S2's code, which S1 uses unchanged: the out-of-turn emitter (`ACPAgent._on_session_event`,
  set by `LocalConversation._ensure_agent_ready` to `_emit_event_from_any_thread`, `local_conversation.py:1578,
  1883`); the scripted agent, already served through `Connection` and `build_agent_router` behind a tap
  (`serve(handler, *, on_initialize)`), so S1 replaced no serving call; and `acp_router.py` with
  `conversation_acp_router`, registered in `api.py`. S2 also split `_start_acp_server` into a wrapper
  (`acp_agent.py:3270`) and `_launch_acp_session` (`:3284`), where S1's start hunk sits. Every v1 clause "if S1
  lands first" is void. *Why:* the Conductor's sequencing (§11 item 5); PR #2's description: "stacked on the
  session-controls branch (`feat/agent-surfaces`, its own draft PR in this fork), so this diff shows only S1's five
  commits". *(v2.2: the branch has since merged the fork's `deep-reasoning` (`0f161f8`) and S2's new head `5e3317f`
  (`2114d23`); the one conflict was the scripted agent's flag list, where S2 added `--set-error` and
  `--auth-required` beside S1's flags.)*

**Behaviour**

- **B2. The opt-in also lives on the agent profile** (§1.2, §1.3 A, §4.6, §4.9, §5.1). `ACPAgentProfile.acp_subagents:
  bool = False` (`profiles/agent_profile.py:292`), forwarded by the resolver's `_build_acp_settings`
  (`profiles/resolver.py:305`) and carried back from settings by `build_seed_profile` (`profiles/seed.py:58`); the
  TypeScript client's `ACPAgentProfile` gains `acp_subagents?: boolean` (`models/agent-profile.ts:80`). *Why:* C1
  §9.1 item 1 and D5 §8.2: Canvas starts every new conversation from the active agent profile, `ACPAgentProfile`
  forbids unknown keys and the resolver forwards a fixed list, so without it no profile could turn the opt-in on and
  the desktop app would always show the flat fallback; the Conductor added it to S1's build (C1 design v2, its
  revision line). *Not built:* the persisted agent-profile fixture both designs asked for. The build recorded no
  reason; this design's reading: the committed profile baselines are only `v1` and `v2`
  `agent_profile_default.json`, and two resolver tests pin the round trip instead, but upstream's
  profile-compatibility check does not see the field (§11 item 11). *Pinned by:*
  `tests/sdk/profiles/test_resolver.py::test_acp_profile_carries_the_subagents_opt_in_to_the_agent[False, True]`,
  `::test_acp_seeded_profile_keeps_the_subagents_opt_in`. *(v2.2: built in `a3279be`:
  `tests/sdk/persisted_settings_baselines/v2/agent_profile_acp_subagents.json`, a minimal ACP profile at profile
  schema 2 with the opt-in on, loaded by the `Persisted settings` guard and the cross test that validates every
  committed fixture, both green at `a3279be`.)*
- **B3. A reconnect unconfirms only the children that were active** (§1.3 H, §2 "Restart", §3.1 item 7, §4.3
  "Seed", §4.5, §5 rule 7). `seed` returns a `source="environment"` snapshot for each child whose latest stored
  snapshot has a `state` other than `None` and `"idle"` (`acp_subagents.py:104–108`); v1 also wrote one for an idle
  child whose last snapshot was cancellable. Every grant is still withdrawn: no seeded child holds one. So after a
  reconnect an idle child's last stored snapshot can still say `cancellable: true`; the route answers 409 for it,
  and §5 rule 6 never shows Stop on an idle child. *Why:* C1 §9.1 item 4: dr-acp keeps `cancel` on idle children
  (§10), so v1's rule gave every finished child one more snapshot on every restart, which C1 does not need.
  *Pinned by:* `test_acp_subagents.py::test_new_connection_withdraws_cancel_and_unconfirms_state` (of a running, an
  idle-and-cancellable, an unconfirmed and a custom-state child, only the running and the custom one get a snapshot,
  and none of the four can be cancelled).
- **B4. A child's tool calls stay out of the turn's trace** (§4.4). v1 did not consider `acp_tracing.py`'s
  `ACPTurnTrace` (upstream's, present at `53a4bc5`). The bridge opens and closes a TOOL span only for a root call
  (`acp_agent.py:1790–1796, 1850–1851`), and `_finalize_successful_turn` hands `trace.finish_turn` the root's calls
  only (`:4195–4203`). *Why* (this design's reading; no comment or message says): a trace's turn is the root agent's
  turn, and a child's call is the child's work, may outlive the turn (`reset()` keeps it open), and would bill its
  span to the turn. *Pinned by:* nothing.
- **B5. Replayed child tool calls enter the bridge's in-flight list, unstored** (§4.3 "Replay"). v1 said that while
  `replaying` every entry point "changes nothing" except registering an unknown child. As built, a child's replayed
  `tool_call` and `tool_call_update` take the shared tool-call path (`_route_child_update` returns `False` for
  them, `acp_agent.py:1681–1682`), so their entries are kept in `accumulated_tool_calls`; what is suppressed is
  storage (`emit_subagent_events` drops everything while replaying, `:1638`). A consequence, read from the code and
  not observed in any test: a replayed child call the replay leaves open stays open across `reset()`, and if the
  next root turn is aborted, `_cancel_inflight_tool_calls` stores a synthetic `failed` for it. *Why:* none recorded;
  this design's reading: a child's calls take today's tool-call path on purpose (§1.2's diagram), so they are tracked
like the root's, and only the emission knows about the replay. *Pinned by:*
  `test_replay_is_neither_stored_nor_grants_cancel` (nothing stored, no grant); the in-flight entry is unpinned.
  *(v2.2: fixed in `d74940b`, ruled E-2: `_route_child_update` now returns for a replayed update before the tool-call
  path, so a replayed child call is never tracked; pinned by `test_replayed_child_calls_are_never_tracked_nor_failed_later`.)*
- **B6. Cancel and emission details v1 left open** (§4.4, §4.7). None was recorded with a reason; each reason is this
  design's reading.
  - With the opt-in off and a live connection, `ACPAgent.cancel_acp_session` raises `ACPSessionNotFoundError`
    (404). With no live connection it raises `ACPSessionNotCancellableError` (409) for any id, since that check
    comes first (`acp_agent.py:5049–5052`), as v1's table says for a conversation not yet started.
  - The 2 s bound is a module constant, `_ACP_SUBAGENT_CANCEL_TIMEOUT` (`:204`), which the 504 test patches.
  - `emit_subagent_events` catches an exception from the emitter per event and logs it at DEBUG (`:1648–1650`), as
    `_emit_tool_call_event` does for `on_event`: one failing event neither drops the rest nor raises into the ACP
    loop.
  - A child's `agent_message_chunk` or `agent_thought_chunk` whose content is not a text block is dropped without a
    log line (`:1686`).

  *Pinned by:* `test_cancel_acp_session_without_a_live_connection_is_refused` and
  `tests/agent_server/test_acp_router.py::test_a_cancel_the_agent_does_not_take_in_time_times_out`; the rest is
  unpinned.

**Signatures** (§4.3, §4.4, Appendix A)

- **B7. The signatures the tests were written against.** With no change of behaviour beyond B3–B6: two private
  helpers carry v1's inline hunks, `_OpenHandsACPBridge._route_child_update(child, update) -> bool` (a child's text,
  usage and other updates; `False` for a tool call) and `ACPAgent._load_session(conn, client, session_id,
  working_dir, mcp_servers)` (the root id and `replaying` around `session/load`, `acp_agent.py:5071`); the warn-once
  set is the bridge's `_unannounced_sessions` (`:1452`), not the router's `_warned`; a fresh session's root id is set
  right after `session/new` returns, inside `_init` (`:3660`); the shim's handler asks a private
  `_unstable_update_kind(method, params, is_notification)` (`acp_unstable.py:236`); the router's private helpers are
  `_merge`, `_snapshot`, `_message`, `_message_event`, `_flush`, `_text_of` and the module's `_parent_tool_call_id`.
  `LocalConversation.cancel_acp_session` and `ACPAgent.cancel_acp_session` land in commit 3, not 4 (§8). *Why:* none
  recorded; this design's reading: the Code Guide's three levels of indentation, in `session_update` and `_init`.
  *(v2.3: `_load_session` is gone; the bridge's context manager `replaying(root_session_id)` sets the root's id and
  `replaying` around upstream's own `conn.load_session(...)` call (`acp_agent.py:1648–1662`, `:3602`; V-5,
  `fec0b95`). The warn-once set is `_warned_unannounced: set[tuple[str, str]]` (`:1455`), behind one helper,
  `_warn_unannounced(session_id, routing)` (`:1678`; V-1, `73e47f8`). The router's `_merge` takes the child's id, and
  `_snapshot` builds each stored event from the held one (V-4). At Gate C the cancel methods are in #14, the route's
  level, and the grant check they call is in #12.)*

**The fixture** (§4.10, A.7)

- **B8. `--transcript-interval-ms MS`.** A sleep of `MS` before each `session/update` a transcript sends (default
  0); `TranscriptPlayer` takes it as `interval_s`. *Why:* C1 §9.1 item 2, so E6's fan-out arrives at 60 events/s
  (16 ms) instead of in one burst. *Pinned by:* `test_transcript_interval_paces_the_replay`. *(v2.3: cut in
  `6dcde3e`; pacing is unpinned (P5), and the cut test did not catch an ignored flag either, as-built r3 §8.)*
- **B9. The `--subagents` run, as built.** Three differences from v1's list, none with a recorded reason:
  `child-a`'s thought arrives as two chunks (`Reading `, `part A.`) and is stored as one segment; the grandchild is
  announced, answers and turns idle while `cell-a1` is open, and `cell-a1` completes after it; and the root's run
  cost (0.0011 USD) rides on S2's usage update after the reply text, not before it. This design's reading: the first
  exercises segmenting, and the second puts a grandchild inside its spawning cell, as a real agent does. *Pinned
  by:* `test_scripted_run_stores_the_scripted_tree`, `test_scripted_run_books_only_the_roots_cost`.
- **B10. The transcript player's edges.** After the last line, a client request gets -32601 and a notification is
  logged (v1: "answering nothing more"); in an agent-outgoing-only transcript, a response whose shape names no
  request (no `protocolVersion`, `stopReason` or `sessionId`) stops the script before it serves, with "cannot tell
  which request this response answers; record the client's lines too"; the root of the conformance rule is the
  first `sessionId` result without a `stopReason`. *Why:* none recorded; this design's reading: an unanswered
  request would hold the bridge until its own timeout, and a transcript the player cannot read must fail loudly.
  *(v2.1)* All nine of D1's native golden recordings hold only the three shapes the player infers (as-built D-8).
  *Pinned by:* `test_transcript_wait_point_that_is_never_reached_exits_non_zero` pins the wait timeout; these edges
  are unpinned. *(v2.3: that test was cut in `6dcde3e` and the wait timeout pinned again on #16 (`6a05b13`) by
  `test_transcript_exits_non_zero_when_a_wait_point_outlasts_the_wait_timeout`, P6′; that the timeout raises (P6),
  and these edges, are unpinned.)*

**How the tests prove it** (§7)

- **B11. The ordering C1 relies on is pinned, and stated in §5 as contract** (§5 rule 10, §5.1, §6). (a) Within one
  child, stored timestamps never decrease in log order, and a reconnect snapshot is later than every earlier event of
  its child; (b) a spawning call's `started` event precedes every event of its subtree, in log position and in
  timestamp. v1's §6 already guaranteed both by construction (one FIFO path per child; the cell stored on the turn's
  path before the announcement is received); timestamps are taken when the portal creates an event
  (`Event.timestamp`'s default, `event/base.py:28–31`), not when the worker stores it. *Why:* C1 §9.1 item 3:
  Canvas orders by timestamp, so C1's "latest" and its backfill would break silently if either stopped holding.
  *Pinned by:* `test_a_childs_stored_timestamps_never_decrease_in_log_order`,
  `test_a_reconnect_snapshot_is_later_than_the_childs_earlier_events`,
  `test_a_spawning_cells_started_event_precedes_its_whole_subtree`, and over REST
  `test_acp_subagent_sessions_over_live_server`.
- **B12. The tests, as built.** Every v1 test exists under its name, except as follows.
  - §7.1: the far side is a real agent-side `Connection` over a socket pair (v1: the library's in-memory
    transport). Added: `test_custom_state_is_kept_whole`, `test_message_content_keeps_non_text_blocks_typed`.
  - §7.2: `test_stored_events_validate_against_the_agent_server_event_schema` is
    `tests/agent_server/test_acp_router.py::test_stored_sub_agent_events_validate_against_the_event_schema`, which
    reads a real run's events over the REST route; `test_scripted_transcript_replays_an_outgoing_only_recording` is
    `test_scripted_transcript_replays_a_recording[full, outgoing-only]`;
    `test_scripted_run_with_subagents_off_stores_only_root_work` runs in both modes; and
    `test_subagents_off_uses_the_stock_connection_and_initialize` runs a conversation and checks the connection's
    type and the `initialize` params on the wire, instead of patching `acp_agent.ClientSideConnection`. Added:
    `test_scripted_run_books_only_the_roots_cost`, B8's and B11's tests, and
    `test_transcript_wait_point_that_is_never_reached_exits_non_zero`.
  - §7.3: the route tests run against a real agent-server with the scripted agent as a process, in S2's harness in
    that file, not against a mocked event service, under names that state the outcome
    (`test_a_cancel_reaches_the_child_and_its_cancelled_state_is_stored`,
    `…_for_an_unknown_conversation_is_not_found`, `…_for_an_unknown_session_is_not_found`,
    `…_for_a_child_without_a_grant_is_a_conflict`, `…_on_a_conversation_that_is_not_acp_is_a_bad_request`,
    `…_the_agent_does_not_take_in_time_times_out`); *(v2.1)* the root's 409 is pinned at the SDK level only
    (`test_cancel_acp_session_refuses_unknown_and_root_sessions`), not through the route. Added:
    `test_cancel_acp_session_on_an_inactive_service_is_refused`;
    `test_subagent_events_visualize_their_essentials[3 kinds]` and `test_unconfirmed_state_is_shown_as_such`; the
    TypeScript `each guard recognises only its own kind`; B2's two resolver tests.
  - S1's live file is also in upstream's `acp-live-tests` job (`.github/workflows/tests.yml:162, 196`), where it
    skips without its variables.

  Counts: 84 deterministic Python cases, 6 TypeScript cases, 2 live. *Why:* none recorded; this design's reading:
  each change tests through the real boundary (a socket, a server, a conversation) where v1 planned a patch or a
  mock, as the Code Guide prefers. *(v2.3: 88 deterministic Python cases at `a3279be`; 75 after the refactor and 78
  at `6a05b13`, with 5 TypeScript and 2 live; the property table at `6a05b13` gives each test's name now.)*
- **B13. The live tier, as built** (§7.4, §11 item 2). The file, marker, variables and two test names are v1's.
  `test_live_agent_tree_is_well_formed` asserts that at least one child has a parent other than the root; that
  every child's parent is the root or a known child; that every `parent_tool_call_id` names a stored call of its
  parent's session; that no stored child text of 40 characters or more appears in the answer
  (`QUOTED_TEXT_MIN_CHARS`; the code's reason: shorter phrases can coincide); and that the conversation's cost
  equals the root's last reported cost. v1's "every child that reported a cost has it on its association" is not
  asserted live; `test_child_cost_is_on_its_association_and_never_booked_to_the_conversation` pins it.
  `test_live_agent_stops_one_subagent_and_its_branch` runs `arun()` under a 120 s limit; on the first stored
  `ACPSubagentEvent` whose parent is a running, cancellable child, it cancels that parent from a thread; then, within
  30 s, the parent and every session under it must be stored `idle`/`cancelled`, and no call of the branch may be
  stored non-terminal after the parent's cancelled snapshot. The workflow is deep-reasoning's `fork-live.yml`, D5
  §7.4's file (inputs `sdk_ref`, `suites`, `sdk_repo`, `live_config`), committed on `ci/fork-live` on top of D1's
  `c8d7fbb` until D5's branch carries it. *Pinned by:* the live run in the Gate B section.

**The pull request and upstream's guards** (§8)

- **B14. PR #2 is a draft against `feat/agent-surfaces`, not a cherry-pick onto `main`.** With B1's stacking no
  pull request of S1's targets the fork's `main`, so upstream's guards that run only for pull requests to `main` did
  not run in CI on S1's head: REST API breakage (oasdiff), persisted-settings compatibility, and the TypeScript
  client's CI and integration tests; the OpenAPI quality ratchet runs only in the release workflow. PR #2's
  description reports them run locally: "the persisted-settings guard (new v7 fixture), the dynamic-attribute
  ratchet, the REST breakage check (additive `oneOf` kinds only), the weak-schema allowlist (three `meta` entries)
  and the TypeScript client's lint, build, 361 tests, API tooling, endpoint audit and public type budget: pass". Of
  those, CI does cover the fixture (`cross-tests` validates every committed persisted-settings fixture) and the
  endpoint audit. *Why:* B1. Spec §4 layer 3 asks for a draft PR to the fork's `main` (§11 item 9). *(v2.1)* The
  Cartographer ran them at `0cfb6a2` (as-built §7.6; the Gate B section has the results): all pass but the OpenAPI
  quality ratchet, which fails at S2's head too, on a pointer of S2's, not S1's (§11 item 13). *(v2.2: resolved.
  The fork-only `1f2b52d`, merged in `0f161f8`, widens the pull-request triggers of the REST breakage, persisted
  settings, TypeScript client CI and integration tests, and version bump guard workflows to the fork's branches, so
  all ran on PR #2 at `a3279be`, green; the version bump guard's SDK API breakage step runs only on a version change.
  The OpenAPI ratchet has no pull-request trigger in the fork (it would start ghcr image pushes the fork cannot
  write); run locally at `a3279be`, it passes, S2's `13e5904` having cleared its pointer. The Gate B section has the
  runs.)* *(v2.3: no draft onto `main` was opened and none will be. The Gate C stack is seven internal drafts, #10 to
  #16, the bottom one based on the fork's `deep-reasoning`; nothing goes to `main` or upstream, so spec §4 layer 3's
  draft onto `main` is a step not taken. Upstream's guards ran on every level, through `1f2b52d`'s triggers.)*
- **B15. Upstream's guard data.** The weak-schema allowlist gains three entries, one per `meta`
  (`ACPSessionMessageEvent`, `ACPSubagentEvent`, `ACPToolCallEvent`, each at
  `…/properties/meta/anyOf/0/additionalProperties`); v1 allowed for `-Input`/`-Output` twins as well, and PR #2
  reports the ratchet passing with three. The TypeScript client's public type budget
  (`clients/typescript/config/public-type-budget.json`, upstream's, which v1 did not know) gains a category,
  `acp-protocol-meta`, holding the three `meta` fields. *Why* (the commit): "the three opaque meta fields join the
  public weak-type budget".

**Size** (§3.1 item 16, §4.1)

- **B16. Size.** `git diff --numstat 6f97bf3..0cfb6a2`: 4,030 lines added and 56 removed, in 42 files; §4.1 lists
  them per file. Against v1's §4.1: the code is 1,317 lines (1,205 Python, 112 TypeScript) against ≈940, chiefly
  `acp_agent.py` (+287 −40 against +100: B4, B6, B7 and the cancel methods' docstrings) and the shim (247 against
  150); the tests are 2,195 (1,988 deterministic, 207 live) against 750; the scripted agent gains 459 lines against
  180 (the transcript player's planning, B8, B10); guard and fixture data are 59 against 36. The build recorded no
  reason for the growth. This design's reading: most of it is tests that cross the real boundary (B12), a
  conversation, a server or a second connection, each with its own set-up, and C1's ordering tests (B11); the code
  itself grew by about two fifths. At ≈300 lines an hour Gate C reads the 4,030 lines in about 13.5 h, against the
  spec's ≈5 h. Michael rules on it at Gate B (the Gate B section). *(v2.2: at `a3279be`, `git diff --numstat
  5e3317f..a3279be`: 4,155 added and 56 removed in 43 files; the fixes added 125: 30 of code in `acp_agent.py`
  (+317 −40 in all), 80 of tests in `test_acp_subagents.py` (1,241 lines), and the 15-line profile fixture. About 14 h
  at Gate C.)* *(v2.3: after the refactor, 3,690 added and 63 removed against `d938c90`; at `6a05b13`, 3,730 and 63
  against `9277e71`, about 12.4 h; `acp_agent.py` +294 −43, `test_acp_subagents.py` 1,046 lines. The section after
  the Gate C section has the table, and the Gate C section each level's lines.)*

**Unverified**

- **B17. What this design could not check:** that each of the five commits is green on its own (v1's §8 said
  each would be; CI ran only at the head); the local runs of the guards CI did not run (B14); and that the
  allowlist and type-budget entries are exactly what those scripts report (B15). *(v2.1)* The Cartographer has since
  run the guards (B14), so of these only the per-commit check stands, with the REST breakage script itself and
  upstream's SDK API breakage check (as-built §9 item 4). Also unrun, per the as-built document (§9): a real
  `session/load` that replays sub-agent traffic (the `replaying` flag is pinned by units that set it; the scripted
  agent's transcript mode refuses `session/load`, so the reconnect test falls back to `session/new`); a conversation
  started from an agent profile with the opt-in through a real agent-server; and the paths read but not run: a
  notification without `sessionId`, a message's `_meta` and non-text blocks, masking of `meta`, and E-4.
  *(v2.2: the guards now run in CI at `a3279be`, B14, and E-4 is pinned; still unverified: each commit green on its
  own, and the two local runs the Conductor reports, the SDK API breakage step and the OpenAPI ratchet.)* *(v2.3: each
  level of the Gate C stack is green on its own, in CI, for the suites its diff touches; the SDK API breakage step
  still runs only on a version change, and nothing ran it at `2675399` or on the stack.)*

**Edges the build left open, ruled (v2.1)**

The as-built document's §4.5 lists behaviour no test pins, observed by its probes. Each is ruled here against this
design's rules (§4.3, §5, §5.1), the spec, and C1's reading rules (C1 decisions C and I, its §4.7). "Fix before Gate
B" means the Implementer changes the code and adds the test, and CI and the live tier run again at the new head;
"stated" means the behaviour stands and §5.1 now says so. No code was changed by this design.

- **E-1. A child call left open across aborted turns is failed once per turn** (probe: `in_progress, failed, failed,
  completed`). The close-out of an aborted turn (`_cancel_inflight_tool_calls`) stores a synthetic `failed` but
  leaves the entry open, and `reset()` keeps open child entries, so each later aborted turn fails it again; the
  agent's later report still lands. v1 §4.4 puts child entries in an aborted turn's close-out once, as the
  optimistic close of a cancelled turn; repeating it is a defect, but the store's last word per call is still the
  agent's, which is all §5 rule 3's "last wins" and C1's decision C read, and with dr-acp a child call does not
  outlive a stopped root turn (its root Stop ends the run and closes every open cell, D1 §5.2's `run.end` row).
  **Ruling: acceptable for Gate B, stated (§5.1); fix it with E-2, in the same lines.** *The design wants:* an
  aborted turn stores at most one synthetic `failed` per open child call, and the agent's later report for that call
  still lands and wins. *Test:* `test_child_call_open_across_aborted_turns_is_failed_once_and_the_agents_report_wins`
  (bridge units: a child's `tool_call`, two aborted turns with `reset()` between, then its `tool_call_update`
  `completed`; the emitted statuses are `in_progress, failed, completed`). *(v2.2: built in `f6d8e1e`: once its
  synthetic failure is stored the entry is marked `failed_by_abort` (`acp_agent.py:3845, 3868`) and later aborts,
  and retries within one, skip it; the entry stays open, so the agent's later report still lands and wins. Pinned by
  that test.)*
- **E-2. A child call replayed by `session/load` and left open reaches the store at the next aborted turn** (B5).
  Replayed child calls enter the bridge's in-flight list; the next turn's `reset()` clears root entries but keeps open
  child ones, so a later aborted turn stores a synthetic `failed` for a call that only the replay mentioned. This
  breaks the design's rule that replayed traffic never reaches the store (§2's Restart, §4.3's Replay, §5.1
  guarantee 7; the spec: recorded history is kept, controls wait for fresh state), and it manufactures an outcome
  from a gap, which D1 refuses for the same case (`run.end lost` replays "nothing for children", D1 §5.2). dr-acp
  reaches it: a run killed by a restart replays its children's open cells and leaves them open. **Ruling: a bug; fix
  before Gate B.** *The design wants:* nothing a `session/load` replay sends is tracked, failed or stored, so the
  bridge keeps no in-flight entry for a call it saw only in a replay (either it records none while `replaying`, or
  `_load_session` drops the ones the replay created). A live update after the reconnect for such a call then finds
  no entry and is not stored, as for a root call today; the call keeps its last live state under a child whose state
  is unconfirmed (§5 rule 7). *Test:* `test_replayed_child_calls_are_never_tracked_nor_failed_later` (bridge units:
  `replaying` set, a child's `tool_call` left open, `replaying` cleared, then an aborted turn: nothing is emitted for
  that call, and `accumulated_tool_calls` holds no entry for it). *(v2.2: built in `d74940b`, the first of the two
  ways: `_route_child_update` (`acp_agent.py:1700`) returns for a replayed update before the tool-call path, so
  nothing a replay sends is tracked; pinned by that test.)*
- **E-3. A second cancel to a child that has already gone idle is accepted** (three trials of three). The router
  authorizes by the grant alone (§4.3, "Cancel grants"), and an agent that keeps `capabilities.cancel` on an idle
  child (dr-acp, §10; the scripted agent) keeps the grant live, so the route writes `session/cancel` and answers
  200. The spec makes the agent's advertisement the condition ("409 unless it advertised `cancel`"), the RFD makes
  the grant the agent's to give or withdraw, and ACP makes a cancel with nothing in flight a no-op, which dr-acp
  honours (§10's observation). C1 never offers Stop on an idle child (C1 decision I, §4.7), so only a direct API call
  does this. **Ruling: acceptable, stated (§5.1).** *The design wants:* the route authorizes a cancel by the agent's
  live grant alone, not by the child's state, and leaves an idle child's no-op to the agent; `requested: true`
  promises that `session/cancel` was written, not that anything stopped. *Test:*
  `test_cancel_acp_session_for_an_idle_child_that_keeps_its_grant_is_sent` (the scripted run without
  `--cancel-wait`, after `child-b` is idle: the call returns, the request log holds `session/cancel` for `child-b`,
  and no new `child-b` snapshot is stored). *(v2.2: pinned in `e65335d` by that test; no code changed.)*
- **E-4. Unstable updates on a session never announced are stored under that session's id** (read). Decision C sends
  an unannounced non-root session's traffic down today's root path so that existing bridge tests, which use
  arbitrary session ids, keep their meaning; that reasoning covers the stable updates, which reached the root before
  S1, and not the three unstable ones, which had no path before S1. As built, a `session_message` on such a session
  is stored with that `acp_session_id` (in no rendered transcript), and a child announced there gets it as
  `parent_session_id`, so C1 shows it as "could not be placed" (§5 rule 2; the spec's C1 failure cell: "shown apart,
  never merged into the root's stream"). Sending them to the root would merge an unplaceable child into the root's
  flow, which the spec forbids. The one gap: no WARNING on this path (`_child_session`'s warn-once runs for stable
  updates only). **Ruling: acceptable, stated (decision C, §4.3, §5.1); the WARNING is not needed for Gate B.** *The
  design wants:* unstable updates on a session that is neither the root nor announced stay under that session's id,
  so a child announced there is "could not be placed", and the bridge warns once per such session, as for stable
  traffic. *Test:* `test_unstable_updates_on_an_unannounced_session_stay_under_that_session` (bridge units: a
  `subagent_update` and a `session_message` on `stranger`: the snapshot's `parent_session_id` and the message's
  `acp_session_id` are `stranger`, the root's accumulators stay empty, and one WARNING names the session). *(v2.2:
  built in `562c31d`: `unstable_session_update` warns once per such session from its own set,
  `_unannounced_unstable_sessions` (`acp_agent.py:1455, 1639`), since the two paths route differently, so a session
  that sends both stable and unstable updates can draw two warnings, one per path.
  `test_child_is_never_reparented_nor_its_own_parent` now counts only the router's three refusals, as its
  self-announcing session also draws this warning. Pinned by that test.)* *(v2.3, V-1, `73e47f8`: the two sets and
  `_warn_once_for_unannounced_unstable_traffic` are one set of `(session, routing)` pairs, `_warned_unannounced`, and
  one helper, `_warn_unannounced(session_id, routing)` (`acp_agent.py:1455`, `:1678–1687`); still one WARNING per
  session per path, each naming the session by its fingerprint.)*
- **D-1 (B3) against C1's Stop rule.** After a reconnect, a finished dr-acp child keeps its stored `cancellable:
  true` (it gets no reconnect snapshot), and the route answers 409 for it (no live grant). C1's rule already keeps
  Stop off it: decision I enables Stop "only for a running or waiting child whose latest snapshot is live and
  `cancellable`" and makes it "absent for idle and unconfirmed children", and C1 §4.7's table gives "any other (idle,
  unconfirmed, a reconnect snapshot): none". `canStopSubagent` asks for running or waiting first, so an idle child
  never shows Stop, enabled or disabled, whatever `cancellable` says. **Ruling: acceptable; no change to S1 or C1.**
  If the agent re-drives that child live, its fresh update sets the state and, if it grants `cancel`, the live grant
  together (§4.3's merge rules), and Stop follows both. *Test:* S1's is
  `test_new_connection_withdraws_cancel_and_unconfirms_state`; C1's, when built: `canStopSubagent` is false for an idle
  snapshot with `cancellable: true`.

---

## 4 · Modules and seams

### 4.1 Files

*(v2)* The last column is the build, `git diff --numstat 6f97bf3..0cfb6a2` (added, and removed where any); rows
marked *(v2)* are files v1 did not list.

| Path (SDK fork) | | ≈ lines | What | Built (v2) |
|---|---|---|---|---|
| `openhands-sdk/openhands/sdk/agent/acp_unstable.py` | new | 150 | **The shim**: models for the three updates and the capability, `SubagentClientSideConnection`, `SUBAGENT_CLIENT_CAPABILITIES`. Deleted at the pin bump. | 247 |
| `openhands-sdk/openhands/sdk/agent/acp_subagents.py` | new | 280 | `ACPSubagentSessions` (routing, merge, segments, cost, cancel grants, seed); `ACPSessionNotFoundError`, `ACPSessionNotCancellableError`. Stays after the shim goes. | 338 |
| `openhands-sdk/openhands/sdk/agent/acp_agent.py` | changed | +100 | The bridge's routing and emission; the opt-in field; the connection swap; seed, replay flag and root id in `_init`; `cancel_acp_session`. §4.4 lists every hunk. | +287 −40 |
| `openhands-sdk/openhands/sdk/event/acp_subagent.py` | new | 120 | `ACPSubagentEvent`, `ACPSessionMessageEvent`, `ACPSessionTextEvent`. | 160 |
| `openhands-sdk/openhands/sdk/event/acp_tool_call.py` | changed | +12 | `acp_session_id`, `meta`. | +9 |
| `openhands-sdk/openhands/sdk/event/__init__.py` | changed | +6 | Export (and so register) the three kinds. | +8 |
| `openhands-sdk/openhands/sdk/event/resume_transcript.py` | changed | +4 | Skip child tool calls. | +9 −1 |
| `openhands-sdk/openhands/sdk/conversation/impl/remote_conversation.py` | changed | +10 | Cache key `(acp_session_id, tool_call_id)` for child calls. | +15 −7 |
| `openhands-sdk/openhands/sdk/conversation/impl/local_conversation.py` | changed | +25 | `cancel_acp_session`; plus, if S1 lands first, S2's emitter (`_emit_event_from_any_thread`, its executor, its wiring in `_ensure_agent_ready`, its shutdown in `close()`; S2 §4.3, about +40). | +18: `cancel_acp_session` only; S2 built the emitter (B1) |
| `openhands-sdk/openhands/sdk/conversation/visualizer/default.py` | changed | +12 | Three `EventVisualizationConfig` entries. | +15 |
| `openhands-sdk/openhands/sdk/settings/model.py` | changed | +20 | `ACPAgentSettings.acp_subagents`, forwarded by `create_agent()`. | +12 |
| *(v2)* `openhands-sdk/openhands/sdk/profiles/agent_profile.py`, `resolver.py`, `seed.py` | changed | — | `ACPAgentProfile.acp_subagents`, forwarded by the resolver, carried back by the seed (B2). | +10 |
| `tests/fixtures/acp/scripted_agent.py` | shared with S2 | +180 | S1's flags on S2's scripted test agent (§4.10); the whole script (about +300) if S1 lands first. | +459 −4: S1's flags only (B1, B8–B10) |
| `openhands-agent-server/openhands/agent_server/acp_router.py` | shared with S2 | +55 | The cancel route on `conversation_acp_router` and `CancelACPSessionResponse`; the module, its router and its `include_router` line in `api.py` if S1 lands first. | +68 −1: the route only (B1) |
| `openhands-agent-server/openhands/agent_server/event_service.py` | changed | +15 | `cancel_acp_session`. | +9 |
| `.github/agent-server-openapi-weak-schema-allowlist.json` | changed | +24 | One entry per new `meta` location. | +18: three entries (B15) |
| *(v2)* `.github/workflows/tests.yml` | changed | — | S1's live file in upstream's `acp-live-tests` job (B12). | +2 |
| `clients/typescript/src/…` | changed | +130 | Types, `cancelAcpSession` ×2, `ACP_SETTINGS_KEYS` (§4.9). | +112 −2, with `models/agent-profile.ts` (B2) |
| *(v2)* `clients/typescript/config/public-type-budget.json`, `endpoint-audit.config.json` | changed | — | The three `meta` fields' budget entries (B15); the client-ahead route. | +27 |
| `tests/…`, `clients/typescript/src/__tests__/…` | new/changed | 750 | §7. | +1,988 −1 deterministic (1,862 Python, 126 TypeScript), and the 207-line live file |
| `tests/sdk/persisted_settings_baselines/v7/agent_settings_acp_subagents.json` | new | 12 | The opt-in's fixture. | 12 |
| **total** | | **≈1.8k** (§3.1 item 16) | | **4,030 added, 56 removed** (B16) |

*(v2.2)* At `a3279be`, against S2's head `5e3317f`: `acp_agent.py` +317 −40 (E-1, E-2, E-4),
`tests/sdk/agent/test_acp_subagents.py` 1,241, and a new
`tests/sdk/persisted_settings_baselines/v2/agent_profile_acp_subagents.json` of 15 lines (B2); the other rows are as
above. In all, 4,155 added and 56 removed, in 43 files.

*(v2.3)* At `6a05b13`, against `9277e71`: the shim 222, the router 299, `acp_agent.py` +294 −43, the events 158 (with
`acp_tool_call.py` +9 and `__init__.py` +8), the other SDK consumers +76 −8, the agent-server +77 −1, the TypeScript
client +112 −2 and +27 of its configuration, CI +20; the scripted agent +442 −4, the Python tests +1,846 −5 (the live
file 188, `test_acp_subagents.py` 1,046), the TypeScript tests +113, the baselines 27. Two rows change: S1 also edits
`tests/conftest.py` (+11 −4: `subagent_snapshots`, and `wait_until` returns what it waited for, V-6), and no longer
touches `tests/sdk/test_settings.py`, whose one test was cut (`a910ac9`). In all, 3,730 added and 63 removed, in 43
files; the Gate C section gives each level's share.

### 4.2 The shim — `acp_unstable.py`

Everything that exists only because agent-client-protocol 0.12.1 does not know schema 1.24.1's sub-agent types.
Its module docstring names the tripwire test that tells you when to delete it.

**Models.** Transcribed from upstream's own generator output (python-sdk `9d07d78` regenerated from
`schema-v1.24.1` with `scripts/gen_all.py`, the run the spec cites), keeping its field names, aliases and
optionality, adapted in three ways: they subclass 0.12.1's generated `acp.schema.BaseModel` (so `populate_by_name`
and the `_meta` salvage validator are the library's own); content blocks use 0.12.1's five block classes as one
discriminated union; and the five-way state union collapses into one tolerant `SubagentState` (`state: str`,
`extra="allow"`), which keeps an agent-specific or future state whole, as the RFD requires of clients. Each update
model carries its `sessionUpdate` literal as the discriminator, and pydantic's `model_fields_set` tells an omitted
field from an explicit `null`, which the RFD's patch rules need (verified on 0.12.1 with pydantic 2). *(v2.3, V-3,
`6b089e5`: `SubagentState` has the library's base config, which ignores unknown keys, so a custom state's name is
kept and its other keys are not. The store never held them: the router reads only `state` and `stopReason`, and the
stored events are identical before and after, as-built r3 §2. Nothing read them, the commit's reason.)*

| Model | Fields (wire names) |
|---|---|
| `SubagentCapabilities` | `_meta` |
| `SessionCancelCapabilities` | `_meta` |
| `SubagentSessionCapabilities` | `cancel`, `_meta` |
| `SubagentState` | `state`, `stopReason`, `_meta` (*v2.3:* other keys ignored, V-3) |
| `SubagentUpdate` | `sessionUpdate = "subagent_update"`, `sessionId`, `title`, `description`, `capabilities`, `state`, `_meta` |
| `SessionMessage` | `sessionUpdate = "session_message"`, `messageId`, `senderSessionId`, `recipientSessionId`, `content` (list), `_meta` |
| `SessionMessageChunk` | `sessionUpdate = "session_message_chunk"`, `messageId`, `senderSessionId`, `recipientSessionId`, `content` (one block), `_meta` |
| `SubagentClientCapabilities(ClientCapabilities)` | the library's fields plus `subagents` |

`SUBAGENT_CLIENT_CAPABILITIES = SubagentClientCapabilities(subagents=SubagentCapabilities())` is what the bridge
advertises; serialized with the library's own `serialize_params` it is `{"auth": {}, "subagents": {}}` (verified).

**`SubagentClientSideConnection`**, used at `acp_agent.py:3070` (*v2:* `:3448–3460`) when the opt-in is on:

- `__init__(to_client, input_stream, output_stream, *, on_unstable_update)` calls the library's constructor,
  then replaces `self._conn._handler` with `route_unstable_updates(self._conn._handler, on_unstable_update)`.
  This is the one place the shim touches a private attribute of the library; the shim's own tests exercise it
  through a real connection, so a rename in the library fails a test instead of silently dropping updates.
- `route_unstable_updates(inner, on_unstable_update)` returns a handler that, for a notification
  `session/update` whose `params.update.sessionUpdate` is one of the three, validates the update with one
  `TypeAdapter` and calls `on_unstable_update(params["sessionId"], update)` **synchronously** (the callback must
  not await, §6); an invalid one is logged at WARNING with its error count and dropped, as the library would have
  done. Every other message goes to `inner` unchanged. *(v2, B7: the test for "one of the three" is a private
  `_unstable_update_kind(method, params, is_notification)`; an update without a string `sessionId` is dropped
  with its own WARNING.)*
- `initialize(protocol_version, client_capabilities=None, client_info=None, **kwargs)`: when
  `client_capabilities` is a `SubagentClientCapabilities`, sends `initialize` through `acp.utils.request_model`
  with the standalone `_SubagentInitializeRequest`, whose `clientCapabilities` is declared as the subclass, so
  serialization keeps `subagents`; otherwise it is `super().initialize(...)`, the library's call. *(v2.3, V-2,
  `bf57a3a`: it always sends through `request_model`, with `client_capabilities or SUBAGENT_CLIENT_CAPABILITIES`, as
  `_SubagentInitializeRequest(InitializeRequest)`, whose `client_capabilities` is
  `SerializeAsAny[ClientCapabilities] | None` (`acp_unstable.py:129–134`, `:158–177`). So this connection advertises
  `subagents` by itself, the bridge calls `conn.initialize(protocol_version=1)` for both connection classes (§4.4),
  and the library's call is reached only through the stock connection, with the opt-in off. Given other
  capabilities it sends those, whole; no caller does, and no test drives that branch.)*

Probed for this design on 0.12.1 (2026-10-02, `scratchpad/s1probe/shim2.py`): the capability arrives at the
agent; nine interleaved stable and unstable updates arrive at the client in wire order; `fields_set` separates
`"title": null` from an omitted title; a `{"state": "_custom", "x": 1}` state is kept; the module passes pyright
`standard` with the single suppression.

### 4.3 The router — `acp_subagents.py`

`ACPSubagentSessions` is the client side of ACP's sub-agent RFD for one connection. It is bookkeeping only: it
returns the events to persist and never emits, locks, awaits or does I/O; the bridge calls it from the
connection's event loop (the one exception, `seed`, runs before the connection exists, §6). A class because it
holds state across calls.

**State.**

| Field | Meaning |
|---|---|
| `root_session_id` | the root's ACP id on this connection; set by `_init` before `session/load` (the prior id) and after the session is resolved *(v2.3, V-5: before `session/load` by the bridge's `replaying(prior_session_id)`; after `session/new` by `_init`)* |
| `replaying` | `True` from just before `session/load` until it returns *(v2.3: set and cleared by `replaying()`, in a `finally`)* |
| `_children: dict[str, _Association]` | every known child: seeded from history or announced on this connection *(v2.3, V-4: `dict[str, ACPSubagentEvent]`, each child's latest snapshot, below)* |
| `_pending: dict[str, _Pending]` | per session (root included), at most one open segment: a text run or a chunked message |
| `_messages: dict[tuple[str, str], _Message]` | resolved directed messages, keyed `(transcript session, messageId)` |
| `_warned: set[str]` | unannounced session ids already warned about *(v2, B7: built as the bridge's `_unannounced_sessions`, since the bridge is what warns; v2.3, V-1: the bridge's `_warned_unannounced: set[tuple[str, str]]`, one entry per session and path)* |

`_Association` holds `parent_session_id` (`None` = root), `parent_tool_call_id`, `title`, `description`,
`state`, `stop_reason`, `cancel_granted` (a grant received live on this connection), `cost`, `cost_currency`,
`meta`.

*(v2.3, V-4, `a682f6a`)* There is no `_Association`: the router holds each child as its latest `ACPSubagentEvent`
(`acp_subagents.py:76`), the stored kind itself, whose `cancellable` is the live grant. A merge or a cost change is
a `model_copy` of the held event (`:237`, `:189`). Each snapshot stored is a new event built from the held one
without its `id`, `timestamp` and `parent_id` (`_PER_EVENT_FIELDS`, `:35`; `_snapshot`, `:239–243`), so it gets its
own id and time and never keeps a stored event's place in the conversation's tree (as-built r3's P1, now pinned).
The fields, the merge rules and what is stored are as below.

**Routing.**

- `is_child(session_id)`: `session_id in _children`.
- `key(session_id)`: `None` when `session_id == root_session_id`, else `session_id`. Used for every stored
  routing field.
- Children of children are children: a `subagent_update` on a child's session announces a grandchild whose
  `parent_session_id` is that child.
- *(v2.1, E-4)* An unstable update on a session that is neither the root nor announced is kept under that session's
  id (`key` returns it), never moved to the root: a child announced there has it as `parent_session_id` and is "could
  not be placed" (§5 rule 2); a directed message there is stored with it as `acp_session_id`. Decision C's root path
  is for stable updates only.

**Merge rules** for `on_subagent_update(session_id, update)`, the RFD's, applied field by field:

| Wire field | Omitted | `null` | A value |
|---|---|---|---|
| `title`, `description` | unchanged | cleared | replaced |
| `state` | unchanged | cleared (`state = stop_reason = None`: unconfirmed) | replaced whole (`state`, `stop_reason`) |
| `capabilities` | unchanged | grant withdrawn | replaced whole: granted iff `cancel` is an object |
| `_meta` | unchanged | cleared (but `parent_tool_call_id` kept) | replaced whole; `parent_tool_call_id` updated iff it carries `openhands.parentToolCallId` as a string |

Ownership is never changed: an update for a known child arriving on a different session keeps the original
parent (WARNING); an update whose child id is the root, or equals the session it arrives on, is ignored
(WARNING). The first update for an unknown id announces it. Masking (the bridge's `_mask_value`) is applied to
`title`, `description` and `meta` before they are stored. Each update returns, in order: the parent's open
segment flushed, the child's open segment flushed (its last words precede its state change), then one
`ACPSubagentEvent` snapshot.

**Segments.** A session's open segment is either a text run (`thought` true or false) or one chunked message
(`messageId`). `on_child_text` appends to a text run of the same kind, else flushes and opens one;
`on_session_message_chunk` appends to the same message, else flushes and opens one. `before_update(session_id)`
flushes, and the bridge calls it before every other update for a known session (tool calls, upserts, and anything
else). Usage updates never flush: D1 sends them every 0.5 s while a child is dirty, and they are not transcript
entries. `flush_all()` flushes every session. A flushed text run becomes one `ACPSessionTextEvent`; a flushed
chunked message becomes one `ACPSessionMessageEvent` with its accumulated text.

**Directed messages.** `on_session_message` flushes the session's segment, then resolves the upsert into
`_messages[(session, messageId)]`: content omitted keeps, `null` or `[]` clears, a list replaces; `_meta` the
same; `senderSessionId` and `recipientSessionId` omitted or `null` keep the known value (the RFD's identity rule,
different from the content rule). Returns one `ACPSessionMessageEvent` snapshot. Text is the concatenation of the
text blocks (masked); other blocks are counted in a DEBUG line.

**Cost.** `on_child_usage(session_id, update)` sets the child's `cost`/`cost_currency` from `update.cost`
(`None` when the update omits it: unknown, not zero, D1 §5.2) and returns a snapshot only when either changed.
`size` and `used` are not stored (context windows are per session and not summed).

**Replay.** While `replaying`, every entry point returns no events and changes nothing except one thing:
an unknown child announced in the replay is registered (parent only), so its replayed traffic is routed away from
the root accumulators. Grants and states in a replay are never merged. *(v2, B5: true of the router; in the bridge,
a child's replayed tool calls still enter `accumulated_tool_calls`, and only their storage is suppressed.)*

**Cancel grants.** `check_cancel(session_id)` raises `ACPSessionNotCancellableError` for the root,
`ACPSessionNotFoundError` for an unknown id, `ACPSessionNotCancellableError` when the child holds no live grant,
and returns otherwise. A grant is live only if it arrived on this connection outside a replay.

**Seed.** `seed(events)` runs once per connection, over this conversation's stored events, before the connection
exists. For each `ACPSubagentEvent` it keeps the latest snapshot per child, registers the child with its stored
parent, title, description, meta, `parent_tool_call_id` and cost, and leaves `state`, `stop_reason` and the grant
empty. It returns, for each child whose latest stored snapshot had `cancellable` true or a `state` other than
`None` and `"idle"` (*v2, B3:* only the second: a `state` other than `None` and `"idle"`), a copy of that snapshot with `source="environment"`, `state=None`, `stop_reason=None`,
`cancellable=False`. Partial patches after a reconnect therefore merge onto the stored association instead of
blanking its title. *(v2.3, V-4: it holds each stored snapshot with `state`, `stop_reason` and `cancellable`
cleared, `acp_subagents.py:80–93`.)*

### 4.4 The bridge — `acp_agent.py`, hunk by hunk

Line numbers are `53a4bc5`'s. *(v2: the second table, after "Unchanged on purpose", gives each hunk's place at
`0cfb6a2` and what the build did differently.)*

| Where | Change |
|---|---|
| imports `:42–74` | add `from openhands.sdk.agent.acp_unstable import (SUBAGENT_CLIENT_CAPABILITIES, SessionMessage, SessionMessageChunk, SubagentClientSideConnection, SubagentUpdate)`, `from openhands.sdk.agent.acp_subagents import ACPSubagentSessions`, `Event` in the event import. |
| `_OpenHandsACPBridge.__init__` `:1289` | keyword-only `subagents: bool = False`; creates `self.subagents = ACPSubagentSessions(mask=self._mask_value) if subagents else None` and `self.on_session_event: Callable[[Event], None] \| None = None` (the conversation's emitter, set by `_start_acp_server`). Existing callers (`_OpenHandsACPBridge()` in the tests) get today's bridge. |
| `reset()` `:1334` | `accumulated_tool_calls` keeps child entries that are not terminal (`[tc for tc in … if tc.get("acp_session_id") is not None and tc.get("status") not in _TERMINAL_TOOL_CALL_STATUSES]`), so a child's cell that outlives a turn can still complete. The router and `on_session_event` are not reset. |
| `_mask_tool_call_entry` `:1406` | also masks `meta`. |
| `session_update` `:1427`, after the fork branch `:1445–1451` (and after S2's one line, first after the idle-clock reset, which takes `AvailableCommandsUpdate` and `ConfigOptionUpdate` for every session and returns) | `child = self._child_session(session_id)`. When the opt-in is on: `self.emit_subagent_events(self.subagents.before_update(session_id))` for any update that is neither a child's text chunk nor a usage update, then, for a child: `AgentMessageChunk`/`AgentThoughtChunk` (text blocks) → `on_child_text`; `UsageUpdate` → `on_child_usage`; `ToolCallStart`/`ToolCallProgress` → fall through to the tool-call branches with `child`; anything else (plans, session info, mode) → DEBUG and return. `_child_session` returns the id for a known child, else `None`, and warns once for an id that is neither root, fork nor known. |
| `ToolCallStart` branch `:1479` | the entry gains `"acp_session_id": child` and `"meta": update.field_meta if self.subagents is not None else None`. |
| `ToolCallProgress` branch `:1504` | matches on `tc["tool_call_id"] == update.tool_call_id and tc.get("acp_session_id") == child`; when the opt-in is on, a non-`None` `update.field_meta` replaces `updated["meta"]`. |
| `_emit_tool_call_event` `:1550` | passes `acp_session_id` and `meta` to `ACPToolCallEvent`; a child entry (`acp_session_id` not `None`) goes through `emit_subagent_events`, a root entry through today's `on_event` path (dropped between turns, as today). |
| new methods on the bridge | `unstable_session_update` (the shim's callback: resets the idle clock, ignores the fork session, dispatches to the router, emits, signals activity); `emit_subagent_events` (submits each event to `on_session_event`; drops them while `replaying`, and with a DEBUG line when no emitter is wired, as for an `ACPAgent` driven without a `LocalConversation`); `flush_subagent_text`. Appendix A. |
| `ACPAgent` fields, after `acp_isolate_data_dir` `:1862` | `acp_subagents: bool = False` with its description. |
| `ACPAgent` private attrs, after `:1992` | none of S1's own. S1 uses S2's `_on_session_event: Callable[[Event], None] \| None` (S2 Appendix A.3), which `LocalConversation._ensure_agent_ready` sets before `init_state`; if S1 lands first, it adds that attribute and its wiring exactly as S2 specifies. |
| `_start_acp_server` `:2914–2915` | `client = _OpenHandsACPBridge(subagents=self.acp_subagents)`; `client.on_session_event = self._on_session_event`; then, before spawning, `if client.subagents is not None: client.emit_subagent_events(client.subagents.seed(state.events))` (the reset snapshots go to the emitter, whose worker stores them once the caller releases the state lock). The emitter is the conversation's function, not the agent's, so S2's agent swap (`_replace_acp_agent`) needs no rebinding for S1. |
| `_init`, connection `:3070` | `SubagentClientSideConnection(client, process.stdin, filtered_reader, on_unstable_update=client.unstable_session_update)` when `self.acp_subagents`, else today's `ClientSideConnection(client, process.stdin, filtered_reader)`, byte for byte. |
| `_init`, initialize `:3090` | `await conn.initialize(protocol_version=1, client_capabilities=SUBAGENT_CLIENT_CAPABILITIES)` when on, else today's call. |
| `_init`, load `:3204–3240` | when on: `subagents.root_session_id = prior_session_id; subagents.replaying = True` before `load_session`, `replaying = False` in a `finally`. |
| `_init`, after the session is resolved (`:3252`, `session_id` known) | `subagents.root_session_id = session_id`. |
| `_cancel_inflight_tool_calls` `:3402–3420` | the synthetic failures carry `acp_session_id` and `meta` from the entry; child entries are included (the RFD's optimistic close of a cancelled turn) and go through `emit_subagent_events`, not the captured `on_event`, so a child call's synthetic failure can never be stored before its own earlier `started` event. |
| `_flush_inflight_tool_calls_as_completed` `:3438–3444` | skips entries with an `acp_session_id`: a child's open cell is its agent's to close. |
| `_do_acp_prompt` `:3626–3654`, after the usage wait | `self._client.flush_subagent_text()`: every child's open segment is submitted, on the ACP loop (§6). |
| new `ACPAgent.cancel_acp_session` and `_acancel_acp_session` | Appendix A. |

Unchanged on purpose: `_reset_client_for_turn`, `_clear_turn_callbacks` and `init_state` (child events never
use the turn's callbacks); `_record_usage` (root only); `prepare_usage_sync`/`get_turn_usage_update` (the root's
turn sync never sees a child); `_finalize_successful_turn`'s text (root only, because child text never reaches
`accumulated_text`); the stdout filter; `ask_agent` (fork routing still runs first; unstable updates on the fork
session are ignored). *(v2, B4: `_finalize_successful_turn` did change, in one place: the turn's trace gets the
root's calls only.)*

**As built (v2)**, at `0cfb6a2`; "as v1" means the matching row of the first table holds.

| Where (`0cfb6a2`) | As built |
|---|---|
| imports `:62`, `:105–117` | as v1, plus `LoadSessionResponse` from `acp.schema`, for `_load_session`. |
| `_OpenHandsACPBridge.__init__` `:1397`, `:1448–1455` | as v1, plus `self._unannounced_sessions: set[str]`, the warn-once set (B7). |
| `reset()` `:1457`, `_mask_tool_call_entry` `:1536` | as v1. |
| `session_update` `:1712`: S2's recorder first (`:1725`), then the fork branch, then S1's lines (`:1740–1748`) | as v1; a child's non-tool updates are handled by `_route_child_update` (`:1677`, B7), which drops a non-text chunk without a log line (B6). |
| `ToolCallStart` `:1776`, `ToolCallProgress` `:1805` | as v1, and the turn's trace opens and closes a TOOL span only for a root call (B4). |
| `_emit_tool_call_event` `:1857` | as v1. |
| new bridge methods `:1617–1710` | as v1; `emit_subagent_events` also logs and swallows an emitter's exception per event (B6). |
| `ACPAgent.acp_subagents` `:2215` | as v1. |
| `_start_acp_server` `:3270` → `_launch_acp_session` `:3284–3302` | S2 split it (B1); S1's lines are v1's, in `_launch_acp_session`. |
| `_init`: connection `:3448–3460`, `initialize` `:3476–3482` | as v1. |
| `_init`: `session/load` | moved into `ACPAgent._load_session` `:5071–5093` (B7), which sets the root id to the prior id and `replaying` around the call. |
| `_init`: after `session/new` `:3659–3660` | `client.subagents.root_session_id = session_id` (B7); a loaded session keeps the id `_load_session` set. |
| `_cancel_inflight_tool_calls` `:3796`, `_flush_inflight_tool_calls_as_completed` `:3848` | as v1. |
| `_do_acp_prompt` `:4081` | as v1; `run()` and `arun()` both go through it. |
| `_finalize_successful_turn` `:4195–4203` | `trace.finish_turn` gets the root's calls only (B4). |
| `cancel_acp_session` `:5035`, `_acancel_acp_session` `:5064`, `_ACP_SUBAGENT_CANCEL_TIMEOUT` `:204` | Appendix A; the opt-in-off and no-connection answers are B6's. |

*(v2.2)* At `a3279be`: `_route_child_update` (`:1700`) returns for a replayed update before the tool-call path (E-2);
`_cancel_inflight_tool_calls` (`:3820`) marks a child entry `failed_by_abort` once its synthetic failure is stored and
skips it after (E-1); `unstable_session_update` (`:1620`) calls `_warn_once_for_unannounced_unstable_traffic`
(`:1639`), with its own set `_unannounced_unstable_sessions` (`:1455`) (E-4).

*(v2.3)* At `6a05b13` (the same lines as `2675399`), three rows of the tables above read differently, and the
rest hold at new lines. **Imports** (`:104–115`): `ACPSessionNotCancellableError`, `ACPSessionNotFoundError` and
`ACPSubagentSessions`; `SessionMessage`, `SubagentClientSideConnection`, `SubagentUpdate` and `UnstableSessionUpdate`;
no `SUBAGENT_CLIENT_CAPABILITIES`, `SessionMessageChunk` or `LoadSessionResponse`. **`_init`'s `initialize`**
(`:3478`): one call, `conn.initialize(protocol_version=1)`, for both connection classes, since the shim's connection
advertises `subagents` itself (V-2). **`_init`'s load** (`:3602–3607`): upstream's own `conn.load_session(...)` call
under `with client.replaying(prior_session_id):`, the bridge's context manager (`:1648–1662`), which with the
opt-in on sets the root's id and `replaying` and clears the flag in a `finally`, and with it off does nothing (V-5);
`ACPAgent._load_session` is gone. The rest: the bridge's `__init__` `:1399`, its new attributes `:1450–1457` (one
warn-once set, `_warned_unannounced`, V-1); `reset()` `:1459`; `_mask_tool_call_entry` `:1538`, which now says it
masks `meta`; the new bridge methods `:1602–1712` (`unstable_session_update` `:1602`, `emit_subagent_events` `:1626`,
`flush_subagent_text` `:1643`, `replaying` `:1649`, `_child_session` `:1664`, `_warn_unannounced` `:1678`,
`_route_child_update` `:1689`); `session_update` `:1725`, S2's recorder first (`:1738`), S1's diversion
`:1753–1761`; the tool-call branches `:1798`, `:1825–1828`; `_emit_tool_call_event` `:1870`; `ACPAgent.acp_subagents`
`:2217`; `_launch_acp_session` `:3286–3304`, the seed at `:3304`; the connection `:3451`; the root id after
`session/new` `:3659`; `_cancel_inflight_tool_calls` `:3795`, `failed_by_abort` `:3821`, `:3842`;
`_flush_inflight_tool_calls_as_completed` `:3852`; the turn-end flush `:4085`; `trace.finish_turn` `:4199–4206`;
`cancel_acp_session` `:5036`, `_acancel_acp_session` `:5065`, `_ACP_SUBAGENT_CANCEL_TIMEOUT` `:202`.

### 4.5 Persisted events — `event/acp_subagent.py`, `event/acp_tool_call.py`

All three are plain `Event` subclasses (frozen, `extra="forbid"`, `kind` = class name, registered by import in
`openhands/sdk/event/__init__.py`), not LLM-convertible, with a short `visualize` and `__str__` like
`ACPToolCallEvent`'s. Fields, in full in Appendix A:

| Kind | Written | Key for "latest wins" | Fields |
|---|---|---|---|
| `ACPSubagentEvent` | per `subagent_update`; per change of the child's cost; per reconnect (`source="environment"`; *v2, B3:* only for a child whose last stored state was active) | `acp_session_id` | `acp_session_id`, `parent_session_id` (`None` = root), `parent_tool_call_id`, `title`, `description`, `state` (`None` = unconfirmed), `stop_reason`, `cancellable`, `cost`, `cost_currency`, `meta` |
| `ACPSessionMessageEvent` | per `session_message`; per flushed chunked message | `(acp_session_id, message_id)` | `acp_session_id` (the transcript; `None` = root), `message_id`, `sender_session_id`, `recipient_session_id` (verbatim ACP ids), `text`, `meta` |
| `ACPSessionTextEvent` | per flushed text run of a child | none (append-only, in order) | `acp_session_id` (always a child), `thought`, `text` |
| `ACPToolCallEvent` (changed) | as today | `(acp_session_id, tool_call_id)` | today's fields plus `acp_session_id` (`None` = root) and `meta` (the call's `_meta`, latest), both written only with the opt-in on |

Compatibility: old conversations load unchanged (every new field is optional, every new kind is new); events are
stored with `exclude_none=True` (`event_store.py:225`), so a root tool call is byte-identical to today's; new
kinds are written only for agents with the opt-in, so no existing deployment's clients see them. An older Python
`RemoteConversation` that meets a new kind raises on the unknown `kind` (`resolve_kind`), as with every kind
upstream adds.

### 4.6 The opt-in — `ACPAgent`, `ACPAgentSettings` and *(v2)* `ACPAgentProfile`

`acp_subagents: bool = False` on both, forwarded by `ACPAgentSettings.create_agent()` (`settings/model.py:1926`)
next to `acp_isolate_data_dir`. Like that knob it is programmatic and downstream-facing (no
`SETTINGS_METADATA_KEY`, so it is not in the settings form): the deploying application turns it on for an agent
it knows implements sub-agent sessions. **D5's seam:** the desktop app's setup writes the `dr-acp` agent settings
with `"acp_subagents": true` beside `"acp_server": "custom"` and its `acp_command`. *(v2, B2: Canvas starts a
conversation from the active agent profile, so D5's setup writes it on the `deep_reasoner` agent profile, D5 §4.5;
`ACPAgentProfile.acp_subagents: bool = False` carries it, `_build_acp_settings` forwards it to the settings and
`build_seed_profile` carries it back, so a settings-seeded profile keeps it. An agent-server without S1 refuses the
key with 422, which D5 handles.)* Adding a defaulted field is
additive: `AGENT_SETTINGS_SCHEMA_VERSION` stays 7, and a new fixture,
`tests/sdk/persisted_settings_baselines/v7/agent_settings_acp_subagents.json`, pins that a stored `true` survives
`validate_agent_settings` *(v2: committed as written; upstream's compatibility test in `cross-tests` validates it;
no agent-profile fixture was committed, B2; v2.2: `a3279be` adds
`tests/sdk/persisted_settings_baselines/v2/agent_profile_acp_subagents.json`, the profile's equivalent)*:

```json
{
  "__expected__": {
    "agent_kind": "acp",
    "acp_server": "custom",
    "acp_subagents": true
  },
  "schema_version": 7,
  "agent_kind": "acp",
  "acp_server": "custom",
  "acp_command": ["my-acp-agent"],
  "acp_subagents": true
}
```

The field also rides on the serialized agent (`base_state.json`, `ConversationInfo.agent`), so a client can tell
whether a conversation's agent stores sub-agent sessions.

### 4.7 The agent-server

**Route**, on S2's `conversation_acp_router` in the new `openhands/agent_server/acp_router.py` (prefix
`/conversations/{conversation_id}/acp`, tag `ACP`, registered in `api.py` after `conversation_router`; S2 §4.7):
`POST /api/conversations/{conversation_id}/acp/sessions/{session_id}/cancel` → `CancelACPSessionResponse`. If S1
lands first, it creates the module with that router, prefix, tag and registration, and S2 adds its routes there.

| Outcome | Status | `detail` |
|---|---|---|
| sent | 200 | body `{"session_id": "<id>", "requested": true}`; confirmed later by an idle `ACPSubagentEvent` with `stop_reason: "cancelled"` |
| conversation unknown | 404 | — |
| `ACPSessionNotFoundError` | 404 | `ACP session {session_id} is not a sub-agent session of this conversation.` |
| `ValueError` (not an ACP agent, or the service is inactive) | 400 | the error's text, as `switch_acp_model` |
| `ACPSessionNotCancellableError` | 409 | `ACP session {session_id} does not accept cancel; cancel the conversation's turn instead.` (the spec's text, also for the root and for a conversation with no live ACP connection) |
| `TimeoutError` | 504 | `ACP server did not accept the cancel for {session_id} within 2s.` |

`session_id` is a path parameter taken verbatim (clients URL-encode it; D1's ids are path-safe already).
**`EventService.cancel_acp_session`** (`event_service.py`, after `switch_acp_model` `:2005`) runs the blocking SDK
call in the default executor, so the server's loop never waits on the ACP portal, and raises
`ValueError("inactive_service")` when the service has no conversation, as its neighbours do.
**`LocalConversation.cancel_acp_session`** (`local_conversation.py`, after `switch_acp_model` `:1721`) checks the
agent is an `ACPAgent` (else `ValueError`, the same sentence shape as `switch_acp_model`) and delegates, without
`with self._state:` (decision I). The Python `RemoteConversation` gets no method, matching `switch_acp_model`.
**`CancelACPSessionResponse`** lives in `acp_router.py` beside S2's `ACPConfigOptionSetResponse`.

**The OpenAPI ratchet.** `check_agent_server_openapi_quality.py` reports every unconstrained object; each `meta`
(`ACPToolCallEvent`, `ACPSubagentEvent`, `ACPSessionMessageEvent`, and any `-Input`/`-Output` twins the export
produces) gets an entry in `.github/agent-server-openapi-weak-schema-allowlist.json`, kind
`unrestricted-additional-properties`, reason `ACP _meta is opaque by protocol: implementations MUST NOT assume
values at these keys.`, owner `OpenHands OSS`. The Implementer runs the script and adds exactly what it reports.
*(v2, B15: three entries, one per `meta`, each at `…/properties/meta/anyOf/0/additionalProperties`; PR #2 reports the
ratchet run locally and passing, B14.)*

### 4.8 Other SDK consumers

- **`RemoteConversation`'s event cache** (`remote_conversation.py:420–465`) merges an ACP tool call's `started`
  and terminal events by `tool_call_id`. ACP ids are unique only within a session, so the key becomes
  `event.tool_call_id` for a root call (unchanged: the existing tests read `["tc-1"]`) and
  `(event.acp_session_id, event.tool_call_id)` for a child's; the dict's type widens to
  `dict[str | tuple[str, str], str]`.
- **`render_resume_transcript`** (`resume_transcript.py:258`) renders a lost session's history into the next
  session's first prompt. Child tool calls are the children's work, already summarized by the root's own cells
  and answers; they are skipped (`event.acp_session_id is not None`), and the three new kinds are not rendered.
- **The default visualizer** (`visualizer/default.py:210`) gets `ACPSubagentEvent` ("ACP Sub-agent"),
  `ACPSessionMessageEvent` ("ACP Session Message") and `ACPSessionTextEvent` ("ACP Sub-agent Text") entries in
  the action and message colours already used for ACP tool calls.

### 4.9 The TypeScript client — `clients/typescript`

- `src/events/types.ts:33`: `ACPToolCallEvent` becomes the generated type intersected with
  `{ acp_session_id?: string | null; meta?: Record<string, unknown> | null }`; three hand-written interfaces,
  `ACPSubagentEvent`, `ACPSessionMessageEvent`, `ACPSessionTextEvent`, extend `BaseEvent` with their `kind`
  literal and §4.5's fields (Appendix A.6), join the `ConversationEvent` union (`:171`), and get type guards
  (`isACPSubagentEvent`, `isACPSessionMessageEvent`, `isACPSessionTextEvent`) beside `isMessageEvent`, as S2 does
  for its event. When upstream's pinned release artifact carries the kinds, they become aliases of the generated
  types, as `ACPToolCallEvent` is.
- `src/client/conversation-client.ts` (after `switchAcpModel` `:383`):
  `cancelAcpSession(conversationId, sessionId): Promise<CancelAcpSessionResponse>`, posting to
  `` `/api/conversations/${conversationId}/acp/sessions/${encodeURIComponent(sessionId)}/cancel` ``.
- `src/conversation/remote-conversation.ts` (after `switchAcpModel` `:332`): `cancelAcpSession(sessionId)`.
- `src/models/acp.ts:150`: `ACP_SETTINGS_KEYS` gains `'acp_subagents'`.
- *(v2, B2)* `src/models/agent-profile.ts:80`: `ACPAgentProfile` gains `acp_subagents?: boolean` ("absent from
  older servers").
- `src/index.ts`: export the three types and `CancelAcpSessionResponse`.
- *(v2, B15)* `config/public-type-budget.json`: a category `acp-protocol-meta` admits the three `meta` fields'
  `Record<string, unknown> | null` into the client's public type budget, reason "ACP _meta is opaque by protocol".
- `endpoint-audit.config.json`: an `allowClientOnly` entry for `POST /api/conversations/{}/acp/sessions/{}/cancel`,
  reason "Client-ahead of the pinned Agent Server release, which does not yet carry ACP sub-agent sessions", owner
  "OpenHands TypeScript client maintainers" (the audit is report-only; this keeps it quiet).
- In our fork, the SDK fork's release step (spec Q2 (a)) regenerates `src/generated/agent-server-schema.ts` from
  our agent-server's OpenAPI with `AGENT_SERVER_OPENAPI_PATH`; the hand-written types compile against either
  schema. S1 does not commit a regenerated schema (upstream's `check:agent-server-api` would flag it as drift
  from the pinned release).

### 4.10 The generic fixture — S2's scripted test agent, with S1's flags

One scripted ACP agent serves both tasks' tests (decision K): `tests/fixtures/acp/scripted_agent.py`, run as
`[sys.executable, "<repo>/tests/fixtures/acp/scripted_agent.py", *flags]`. S2 specifies its default behaviour (a
`profile` option, commands per value, the first prompt clearing them, `session/load`, `session/close`, and the
request log named by `SCRIPTED_ACP_LOG`; S2 Appendix C). S1 adds two modes behind flags, and one requirement on
how the script serves its agent. Whichever task lands first creates the script; the other extends it. *(v2, B1:
S2 created it, serving it as below, so S1 added only its modes.)* It imports only `agent-client-protocol`, so the cross-repo jobs run it by path from a checkout of the SDK fork at the
pinned tag (D5, for the replay of D1's recordings; C1 and C2, for Canvas's mock-LLM end-to-end run).

**Serving.** The agent is served through `acp.connection.Connection(handler, writer, reader)` over
`acp.stdio.stdio_streams()`, where `handler` is `acp.agent.router.build_agent_router(agent)` wrapped by a small
tap. The tap keeps `initialize`'s raw `clientCapabilities` (0.12.1's model drops `subagents`, D1 §5.1 reads it
the same way) and writes S2's request log; the agent sends its unstable updates as raw JSON with
`Connection.send_notification`. All public pieces of 0.12.1. S2's behaviours are unchanged by this: they are the
same agent methods behind the same router. (S2's Appendix C names `acp.run_agent`, which builds an
`AgentSideConnection`; that class can neither send the unstable types nor show the raw capability, so if S2 lands
first, S1 replaces that one serving call.) *(v2, B1: S2 built this serving itself, `serve(handler, *,
on_initialize)`; S1 replaced nothing.)*

**`--subagents`** plays one generic sub-agent run on each `session/prompt`, before S2's reply text, with plain
ids and no agent-specific `_meta`:

1. `root` → `tool_call cell-1` (execute, "Run spawn", in progress).
2. `child-a`: announced on `root` (title "Summarize part A", `capabilities.cancel`, running,
   `_meta.openhands.parentToolCallId = cell-1`); the task as a `session_message` root → child-a; a thought on
   `child-a`; `tool_call cell-a1` and its completion; a grandchild `child-a-1` announced on `child-a`
   (`parentToolCallId = cell-a1`), whose answer arrives as two `session_message_chunk`s and which turns idle
   `end_turn`; a `usage_update` on `child-a` (0.0004 USD); its answer as a `session_message` child-a → root;
   idle `end_turn`.
3. `child-c`: announced without capabilities (the spec's "generic fixture has one" child that cannot be
   cancelled); one cell; idle `end_turn`.
4. `child-b`: announced with `capabilities.cancel`; `tool_call cell-b1` in progress; then it waits up to
   `--cancel-wait` seconds (default 0: no wait) for `session/cancel` naming `child-b`. Cancelled: `cell-b1`
   failed, then idle `cancelled`. Not cancelled in time: `cell-b1` completed, then idle `end_turn`. Either way the
   run continues, so tests without a cancel still finish.
5. `root` → `tool_call_update cell-1` completed, a `usage_update` covering the run (0.0011 USD), then S2's reply
   and `end_turn`.

*(v2, B9: as built, `child-a`'s thought is two chunks stored as one segment; `child-a-1` is announced, answers
and turns idle while `cell-a1` is open, and `cell-a1` completes after it; and the run's 0.0011 USD rides on S2's
usage update, after the reply text.)*

If the client's `initialize` did not advertise `subagents`, steps 2–4 are skipped (an agent MUST NOT send them,
the RFD) and only the root's lines are played.

**`--transcript PATH`** replaces every built-in behaviour with a JSONL transcript, one JSON-RPC message per line
as it appeared on the wire, played once:

| Line | Who sent it on the recorded wire | The player |
|---|---|---|
| a request or notification whose `method` is one of `acp.meta.AGENT_METHODS`' values (`initialize`, `session/new`, `session/prompt`, `session/cancel`, …) | the client | **waits** for the client's next message with that method (and, for `session/cancel`, the same `sessionId`); remembers a request's live `id` |
| a response (`id` with `result` or `error`) | the agent | sends it with the live `id` of the request it answers (matched by the recorded `id`) |
| a `session/update` notification | the agent | sends it |

An **outgoing-only transcript** (D1's golden recordings, §8.3 of its design, hold only what `dr-acp` sent) has no
client lines. The player then infers one wait point before each response, by the response's shape: a result with
`protocolVersion` waits for `initialize`; one with `sessionId` and no `stopReason` waits for `session/new`; one
with `stopReason` waits for `session/prompt`, and so do the notifications before it that follow the previous
response. (D1's post-`session/new` commands therefore replay when the first prompt arrives; harmless for E5, which
compares trees.) The same conformance rule applies: without `subagents`, the three unstable updates and every
`session/update` whose `sessionId` is not the root's (that of the `session/new` result) are skipped. A client
message the transcript is not waiting for is logged; a request gets `-32601`. A wait point times out after
`--wait-timeout` seconds (default 30) and the script exits non-zero, so a test fails loudly. After the last line
the script stays connected, answering nothing more, and exits when the client closes its stdin. *(v2, B10: after the
last line a request gets `-32601` and a notification is logged; an outgoing-only response whose shape names no
request stops the script before it serves, asking for the client's lines.)*

*(v2, B8)* **`--transcript-interval-ms MS`** sleeps `MS` before each `session/update` the transcript sends
(default 0), so a replay can arrive at a set rate: C1's E6 load case plays its fan-out at 60 events/s (16 ms).
*(v2.3: no test passes it, P5; the section after the Gate C section.)*

*(v2.3, V-6, `d03ec2c`)* **Wire builders.** The script's ACP updates are built by eleven module functions, which
both sub-agent test files import instead of writing JSON by hand: `text`, `subagent`, `announce`, `idle`,
`tool_call`, `tool_done`, `thought`, `said`, `usage`, `message` and `message_chunk` (`scripted_agent.py:305–386`,
A.7). The `--subagents` run they build is the one above, unchanged on the wire (as-built r3 §4.4). At Gate C the
script arrives in parts: four builders in #10, the rest and `--subagents` in #12, `--cancel-wait` in #14, and the
transcript player with its three flags in #16.

---

## 5 · The persisted contract (what C1 reads)

This is C1's contract with S1, the spec's "S1's event shapes fixed". C1 reads stored events (REST page or the
WebSocket stream; the same events in the same order) and keeps no other channel.

1. **The tree.** The children of a session `P` are the sessions whose latest `ACPSubagentEvent` has
   `parent_session_id == P` (`None` is the conversation's root). "Latest" is log order; the WebSocket delivers in
   the same order.
2. **Placement in the parent.** `parent_tool_call_id`, when set, names a tool call in the parent's own session:
   the `ACPToolCallEvent` with `acp_session_id == parent_session_id` and that `tool_call_id`. When it is not set,
   or names no stored call, the first `ACPSessionMessageEvent` in the parent's transcript whose
   `recipient_session_id` is the child; else where the child's first `ACPSubagentEvent` sits. A child whose
   `parent_session_id` is neither `None` nor a known child is "could not be placed" (C1's failure cell).
3. **A child's own transcript**, in log order: its `ACPToolCallEvent`s (merge `started` and terminal by
   `(acp_session_id, tool_call_id)`, last wins, exactly as for the root today), its `ACPSessionTextEvent`s
   (`thought` true: render like the root's reasoning), and its `ACPSessionMessageEvent`s (last wins per
   `(acp_session_id, message_id)`; "To …" when `sender_session_id` is the child, "From …" otherwise).
4. **State.** The latest snapshot's `state`: `running`, `idle` (with `stop_reason`), `requires_action`,
   `unknown`, any other string (agent-specific, show as is), or `null` (no confirmed current activity: never a
   spinner).
5. **Cost.** The latest snapshot's `cost` with `cost_currency`; `null` is unknown, not zero. Never add a child's
   cost to its parent's, its siblings' or the conversation's (ACP's rule).
6. **Stop.** Show Stop only when the latest snapshot has `cancellable` true and `state` is `running` or
   `requires_action`; click → `cancelAcpSession(conversationId, sessionId)`. A 409 means "not now" (show its
   `detail`); success is shown only when the child's next snapshot arrives (`idle`, `stop_reason: "cancelled"`).
   For deep_reasoner, every agent of the stopped branch turns idle/cancelled the same way.
7. **Freshness.** A snapshot with `source == "environment"` is the bridge's record that the connection its last
   state came from ended: show the child's last known state as history, unconfirmed, without Stop. *(v2, B3: it is
   written only for a child whose last stored state was active, a `state` other than `null` and `idle`. An idle
   child gets none, and its last snapshot may still say `cancellable: true` although no grant survives the
   reconnect: the route answers 409, and rule 6 never shows Stop on `idle`.)*
8. **The root.** Unchanged: user `MessageEvent`s, root `ACPToolCallEvent`s (no `acp_session_id`), the turn's
   `FinishAction`, which never contains child text.
9. **Stock Canvas with S1** renders the new kinds as nothing (`should-render-event.ts` drops unknown kinds) and
   child tool calls in the flat main flow (it ignores `acp_session_id`); it may merge a child call into a root
   call only if both share a `tool_call_id`, which D1's ids never do.
10. *(v2, B11)* **Ordering.** (a) A child's own events (those whose `acp_session_id` is the child: its
    associations, text runs, messages and tool calls) are stored in the order the agent sent them, and their
    `timestamp`s never decrease in log order; a `source == "environment"` snapshot is later than every earlier event
    of its child. (b) When the agent sends a spawning call during a prompt and before the announcement that names it
    (D1 §5.4 rule 2), that call's `started` `ACPToolCallEvent` precedes every event of the child's subtree, in log
    position and in timestamp. Nothing else is promised about the relative position of root and child events (§6).

### 5.1 What C1 and D5 may rely on, and what they may not (v2)

Stated as what the SDK fork guarantees from the commit that carries S1 (`0cfb6a2`; *v2.2:* `a3279be`, with the
fixes, and every tag cut after it), for
an ACP agent run with `acp_subagents` on. C1 (deep-reasoning `design/c1` `88f5c43`, its §9.1) and D5 (`design/d5`
`8086afb`, its §8.2 and §9) may rely on everything here and on nothing else about S1. C1 has no code yet; D5 has its
`fork-live.yml` on `ci/fork-live`. Each guarantee names what pins it. *(v2.3: every guarantee holds at `6a05b13`,
the stack's top, and the refactor changed none. The "Pinned by" lines name `a3279be`'s tests; where a test was
cut, merged or renamed, a v2.3 note names what pins the guarantee now, from the property table after the Gate C
section.)*

Guarantees:

1. **Where the events are.** Every association snapshot, directed message, child text run and child tool call is a
   stored event of the conversation, read through `GET /api/conversations/{id}/events/search` and the
   conversation's WebSocket, with §4.5's fields (Appendix A.4), each valid against the agent-server's published
   `Event` schema; child events are stored during a turn and between turns alike.
   *Pinned by:* `tests/agent_server/test_acp_router.py::test_stored_sub_agent_events_validate_against_the_event_schema`,
   `tests/cross/test_remote_conversation_live_server.py::test_acp_subagent_sessions_over_live_server`,
   `test_child_traffic_between_turns_reaches_the_emitter_in_order`.
2. **The tree** is rules 1–3: the latest `ACPSubagentEvent` per `acp_session_id`; `parent_session_id` `null` for the
   root; `parent_tool_call_id` as the agent last sent it in `_meta.openhands.parentToolCallId`, never cleared by a
   later update without it; a child's calls keyed by `(acp_session_id, tool_call_id)`; a root call stored exactly
   as before S1. *Pinned by:* `test_scripted_run_stores_the_scripted_tree`,
   `test_scripted_transcript_replays_a_recording[…]`, `test_parent_tool_call_id_survives_meta_without_it`,
   `test_child_tool_calls_are_keyed_by_session_and_tool_call_id`, `test_root_tool_call_event_is_stored_as_before`.
   *(v2.3: the last was cut, `a910ac9`. A root call's stored shape is pinned by
   `test_legacy_acp_tool_call_event_loads_without_session_fields` (the model's defaults, P3b) and by the opt-off
   conversation test (no `acp_session_id`); that the bridge leaves a root call's `meta` unset with the opt-in on is
   unpinned, P3. And `test_scripted_run_stores_the_scripted_tree` places a child by its spawning cell only (V-9), so
   rule 2's fallbacks, the first message and then the position, are exercised by no test.)*
3. **Ordering** is rule 10. *Pinned by:* `test_a_childs_stored_timestamps_never_decrease_in_log_order`,
   `test_a_reconnect_snapshot_is_later_than_the_childs_earlier_events`,
   `test_a_spawning_cells_started_event_precedes_its_whole_subtree`.
4. **The root's answer.** The turn's `FinishAction` holds the root's text alone; a child's text and thoughts are
   only in `ACPSessionTextEvent`s, one per run of one kind. *Pinned by:*
   `test_scripted_run_keeps_child_text_out_of_the_answer`, `test_child_text_is_stored_per_segment_in_transcript_order`.
   *(v2.3: the first was cut, `a910ac9`; the bridge unit `test_child_text_never_reaches_the_root_answer` pins it.)*
5. **State and cost** are rules 4 and 5: `state` is the agent's string, `null` when unconfirmed; `cost` is the
   child's latest reported cumulative cost, `null` when unknown; the conversation's metrics book the root's cost
   only. *Pinned by:* `test_omitted_field_keeps_value_and_null_clears_it[…]`,
   `test_child_cost_is_on_its_association_and_never_booked_to_the_conversation`,
   `test_scripted_run_books_only_the_roots_cost`. *(v2.3: the second is
   `test_child_cost_is_stored_on_its_association_when_it_changes`, `ca39def`, which leaves the booking to the third.)*
6. **Cancel.** `POST /api/conversations/{conversation_id}/acp/sessions/{session_id}/cancel` (TypeScript:
   `ConversationClient.cancelAcpSession(conversationId, sessionId)` and `RemoteConversation.cancelAcpSession(sessionId)`,
   which URL-encode the id) answers 200 `{"session_id": …, "requested": true}` only after a `session/cancel` naming
   that child was written to the live connection, and it writes one only for a child whose latest update on that
   connection, outside a replay, granted `cancel`. Otherwise 404 (no such conversation; no such sub-agent session,
   which includes an agent with the opt-in off), 409 with the spec's sentence (the root, no live connection, no live
   grant), 400 (not an ACP agent) or 504 (not written within 2 s). It never takes the conversation's state lock, so it
   works mid-turn under `run()` and `arun()`. Its outcome is only the agent's next snapshot. *Pinned by:* the cancel
   rows of the Gate B table. *(v2.3: the cancel row of the property table at `6a05b13`. The route's 200 and its body
   are reached by one test, the cross test, since the route's own success test was cut, P9.)*
7. **Freshness.** On each new connection, each child whose last stored state was active gets one
   `source: "environment"` snapshot (`state: null`, `cancellable: false`), stored before any event of that child
   from the new connection; no grant survives a connection, and nothing `session/load` replays is stored again or grants
   anything. *Pinned by:* `test_new_connection_withdraws_cancel_and_unconfirms_state`,
   `test_replay_is_neither_stored_nor_grants_cancel`, `test_a_reconnect_snapshot_is_later_than_the_childs_earlier_events`.
   *(v2.1: at `0cfb6a2` one exception: a child call the replay leaves open is failed and stored by the next aborted
   turn, §3.2 E-2, ruled a bug to fix before Gate B; the guarantee is the design's, and E-2's test pins it once fixed.
   The flag itself is pinned by units only: no test drives a real replay of sub-agent traffic, B17.)* *(v2.2: the
   exception is fixed in `d74940b` and pinned by `test_replayed_child_calls_are_never_tracked_nor_failed_later`; the
   guarantee holds without exception at `a3279be`.)* *(v2.3: `replaying()` sets and clears the flag, V-5; the
   reconnect test is the one test that catches it left set, P10.)*
8. **The opt-in.** `acp_subagents` on `ACPAgent`, `ACPAgentSettings` and `ACPAgentProfile`, default `false`,
   forwarded by `create_agent()`, the profile resolver and the seed; a stored `true` survives validation at settings
   schema 7; `ACP_SETTINGS_KEYS` and the TypeScript `ACPAgentProfile` keep it. With it off, nothing S1 adds is sent or
   stored. *Pinned by:* the opt-in rows of the Gate B table. *(v2.2: and a stored profile with `acp_subagents: true`
   survives validation at profile schema 2, pinned by the persisted-settings guard's new fixture.)* *(v2.3: the opt-in
   row of the property table at `6a05b13`; `create_agent()`'s forwarding is pinned by the resolver test, which builds
   the agent, since `test_acp_create_agent_forwards_subagents` was cut, P2.)*
9. **The scripted agent.** `tests/fixtures/acp/scripted_agent.py` at the pinned commit runs by path with only
   `agent-client-protocol` and the standard library: `--subagents` plays §4.10's run with its ids (`child-a`,
   `child-a-1`, `child-b`, `child-c`; cells `cell-1`, `cell-a1`, `cell-b1`, `cell-c1`), `--cancel-wait` holds
   `child-b`, `--transcript PATH` replays full and agent-outgoing-only JSONL recordings with §4.10's wait points,
   `--transcript-interval-ms` paces them, and `--wait-timeout` exits non-zero at a missed wait point. When the client
   did not advertise `subagents`, it sends neither the unstable updates nor any update for another session.
   *Pinned by:* the fixture row of the Gate B table, and every E5 test, which runs it. *(v2.3: not all of it. At
   `6a05b13` the transcript replay is pinned by `test_scripted_transcript_replays_a_recording[full, outgoing-only]`,
   the non-zero exit past `--wait-timeout` by
   `test_transcript_exits_non_zero_when_a_wait_point_outlasts_the_wait_timeout` (P6′, restored), and "no update for
   another session" by the opt-off test's `[--transcript]` case (P4, restored).
   Three parts hold in the code, read, and no test pins them: the pacing of `--transcript-interval-ms` (P5); that a
   missed wait point raises, rather than the script failing some other way (P6); and that the unstable updates
   are not sent without `subagents`, which no conversation can see, since the stock connection drops them anyway.)*
10. **The live tier's interface**, for D5's `fork-live.yml`: `tests/sdk/agent/test_acp_subagents_live.py`, marker
    `acp_live`, runs only with both `OPENHANDS_ACP_LIVE_AGENT_COMMAND` (shell-split) and
    `OPENHANDS_ACP_LIVE_SUBAGENTS_PROMPT` set, and the prompt must make the agent spawn a sub-agent with a child of
    its own, cancellable and running long enough to be stopped (§7.4).

Not guaranteed:

- The relative log position of root events and child events (§6): under a synchronous `run()` a turn's child events
  are stored after the step, under `arun()` as they come. Place by id; only rule 2's last resort reads position.
- That an idle child's last snapshot says `cancellable: false` after a reconnect (B3); rule 6's state condition is
  what keeps Stop off it.
- Optimistic cancel marking (§3.1 item 14): a cancelled child's open calls are closed only by what the agent
  reports. A cancel or abort of the root's own turn, though, stores a synthetic `failed` for every open call, the
  children's included (§4.4). *(v2.1, E-1)* At `0cfb6a2` a child call that stays open is failed again by each later
  aborted turn; the agent's own later report still lands last, so "last wins" reads the agent's word. *(v2.2:
  fixed in `f6d8e1e`: at most one synthetic `failed` per child call, and the agent's later report still wins.)*
- *(v2.1, E-3)* That a cancel is refused once a child is idle: the route authorizes by the agent's live grant, not by
  state, so a child whose agent keeps `cancel` on it after idle (dr-acp does) is sent `session/cancel` and the route
  answers 200; the agent treats it as a no-op. `requested: true` means the cancel was written, not that anything
  stopped.
- *(v2.1, E-4)* A home for unstable updates on a session never announced: they are stored under that session's id,
  so a child announced there is "could not be placed" (rule 2) and a message there belongs to no rendered transcript.
  *(v2.2: the bridge warns once per such session, `562c31d`.)* *(v2.3: once per session per path, through one
  helper, V-1.)*
- Content other than text: the non-text blocks of directed messages and of a child's text are not stored.
- Child events still queued when the conversation closes, or emitted after it: S2's emitter drops them (§11 item 6).
- When a chunked message or a text run is stored: at its session's next boundary (§4.3) or at the end of the
  prompt; an aborted turn's open segments wait for the session's next update or the next turn's end (§6).
- Timestamps against the wall clock: they are the machine's `datetime.now()` (C1 §10 item 7).
- The order of the Python `RemoteConversation`'s cache: its in-place merge of a call's two events can reorder it
  when child traffic interleaves (PR #2's notes; §11 item 10). The stored log is the order.
- A persisted agent-profile fixture (B2): upstream's profile-compatibility check does not pin the profile field.
  *(v2.2: no longer so; `a3279be` adds it, and guarantee 8 now covers stored profiles.)*
- E5 on D1's actual golden recordings: S1's tests replay hand-written transcripts of the same shape; D5's
  `bridge-replay` job is that check.
- The shim past agent-client-protocol 0.12.x: the tripwires fail once the library parses the updates, and the shim
  then goes (§8).

---

## 6 · Threads, ordering and locks

**Who runs where.** The ACP connection lives on the `AsyncExecutor`'s portal loop (one thread). Every
notification is handled in its own task, created in arrival order by the library's receive loop; tasks start in
FIFO order. The bridge's `session_update` and the shim's callback never await, so each update is fully handled in
its task's first step, in arrival order, unstable and stable alike (verified with nine interleaved updates). A
prompt's response wakes `conn.prompt` only after the tasks of every notification received before it have run.

**The router is touched only on the portal thread**, with one exception made safe by timing: `seed` runs in
`_start_acp_server` before the connection exists, when no other thread can reach this bridge. Turn-end flushing
therefore happens at the end of `_do_acp_prompt`, which runs on the portal, not in `_finalize_successful_turn`.
Segments left open by an aborted turn are submitted by the session's next update, or at the end of the next turn.

**Two streams, two paths, each in order.** The root's events keep today's path: the turn's `on_event`, called
on the portal thread while a prompt is in flight (unchanged, so today's ordering guarantees for the root stand).
Every child event (associations, directed messages, text runs, child tool calls and their synthetic failures, the
reconnect snapshots) is submitted to the conversation's emitter, S2's `_emit_event_from_any_thread`: one worker,
first in first out, which takes the state lock and calls `_on_event`, so the event is persisted and reaches every
subscriber exactly like any other. The portal thread only submits; it never waits for the lock.

- *Within a child*, order is exact: every one of its events takes the one FIFO path, in the order the portal
  produced them, which is wire order. So "latest wins" per key (§5) always sees the newest last. *(v2, B11: an
  event's `timestamp` is taken when the portal creates it, `Event.timestamp`'s default, not when the worker stores
  it, so within a child the timestamps follow wire order too; §5 rule 10 states both as contract.)*
- *Between a parent's cell and the children it spawns*, references always point back: the cell's `tool_call` is
  stored synchronously on the turn's path before the announcement that names it is even received.
- *Between the root's and the children's events*, positions in the log may interleave differently from the
  wire: in the agent-server (`arun()`), the worker stores each child event as it comes, because the state lock is
  free while a prompt is awaited; under a synchronous `run()`, which holds the lock for the whole step, a turn's
  child events are stored right after the step. *(v2.1, measured by the as-built document, §4.4: with the scripted
  agent, none of 9 child snapshots was stored before the turn's `FinishAction` under `run()`, and 8 of 9 were stored
  while the turn still ran under `arun()`.)* Nothing in §5 reads that relative position (placement is by id),
  except the last-resort placement "where the child's first `ACPSubagentEvent` sits".

**No deadlock.** The ACP thread never takes the state lock. The worker waits for it, and every holder releases it
without waiting on the worker: the synchronous `run()` releases it between steps, `arun()` while it awaits a
prompt (S2 §4.3), `init_state` when it returns. `close()` shuts the worker down with `cancel_futures=True`, so a
child event still queued at that moment, or submitted after it, is dropped with a DEBUG line (S2's semantics).

**Cancel** runs `_acancel_acp_session` on the portal through `run_async(..., timeout=2.0)` from an executor
thread: the grant check and the send happen on the thread that owns the router and the connection; no state lock
is taken.

**Replay boundary.** `replaying` is set and cleared on the portal around `await conn.load_session(...)`; by the
FIFO argument, every replayed notification has been handled before `load_session` returns, so nothing replayed
leaks out of the flag, and every notification after the response is live. *(v2.3, V-5: the bridge's
`replaying(prior_session_id)` context manager sets the flag, and the root's id, and clears the flag in a `finally`,
around upstream's own `conn.load_session(...)` call, on the portal as before.)*

---

## 7 · Testing

In upstream's layout and style (pytest beside `tests/sdk/agent/test_acp_agent.py`, classes where the
neighbouring file uses them, the default run touching no network); each test named for the property it pins. The
boundary that is faked is the ACP agent process: the shared scripted agent of §4.10, launched as a real
subprocess, or, for the shim, a real 0.12.1 agent connection over the library's in-memory transport (*v2, B12:* a
real agent-side `Connection` over a socket pair). Upstream's
full suite (615 files) must stay green; decision A is what keeps it green without edits. Like S2 (its §4.10), S1
puts its tests in new files and leaves the 10,258-line `test_acp_agent.py` alone. Child events reach the store
through the emitter's worker, so a test that reads `state.events` after `run()` waits until the expected events
are there (a polling helper with a 5 s limit), never on a sleep. *(v2: the helper's default limit is 10 s, and
the cancel tests allow 15–30 s for the announcement and the idle snapshot.)*

*(v2.3)* The tables below name the tests v1 planned and v2 and v2.2 added; the refactor cut, merged or renamed
some (V-7, `a910ac9`, `6dcde3e`, `ca39def`, `5b17efd`, `bf57a3a`, `6b089e5`), and the stack restored three. Each row
that changed says how; the property table after the Gate C section is the reference at `6a05b13`, 78 deterministic
Python cases. The polling helper is now shared, `tests/conftest.py`'s `wait_until`, which returns what it waited
for, beside `subagent_snapshots`, each child's latest stored snapshot (V-6, `2fb47b2`).

### 7.1 The shim and its tripwire — `tests/sdk/agent/test_acp_unstable.py`

| Test | Pins |
|---|---|
| `test_acp_library_rejects_subagent_update` | **The tripwire.** `acp.schema.SessionNotification.model_validate` of a minimal `subagent_update` raises `ValidationError`. Its failure message: "agent-client-protocol now parses ACP's sub-agent updates: delete openhands/sdk/agent/acp_unstable.py, use the library's types and capability, re-run the ACP conformance probes against Claude Code, Codex and Gemini, and bump agent-client-protocol in openhands-sdk/pyproject.toml." |
| `test_acp_library_has_no_subagents_capability` | The second tripwire: `"subagents" not in ClientCapabilities.model_fields`. |
| `test_initialize_puts_subagents_capability_on_the_wire` | An agent-side tap sees `{"auth": {}, "subagents": {}}`. *(v2.3: the whole `initialize` params, from a call with no capabilities, V-2.)* |
| `test_initialize_without_subagent_capabilities_is_the_library_call` | `super().initialize` path: no `subagents` on the wire. *(v2.3: cut with its branch, `bf57a3a`; the opt-off conversation test pins the stock `initialize`.)* |
| `test_unstable_updates_reach_the_callback_in_wire_order` | Nine interleaved stable/unstable updates arrive in order. |
| `test_stable_updates_still_reach_the_library_router` | `agent_message_chunk` on a child id arrives as `AgentMessageChunk`. |
| `test_malformed_unstable_update_is_dropped_with_a_warning` | A `subagent_update` without `sessionId`: no callback, one WARNING. |
| `test_patch_fields_tell_omitted_from_null` | `fields_set` contains `title` for `"title": null`, not for an omitted title. *(v2.3: cut, `a910ac9`; the merge table's `title-null` case pins it, P8.)* |
| *(v2)* `test_custom_state_is_kept_whole` | `{"state": "_reviewing", "x": 1}` keeps its state and its extra key. *(v2.3: cut with `extra="allow"`, `6b089e5`; the extra key is no longer kept, V-3, and the merge table's `state-custom` case pins the state's name.)* |
| *(v2)* `test_message_content_keeps_non_text_blocks_typed` | A `session_message` with a text and an image block parses both, typed. *(v2.3: cut, `a910ac9`, and restored on #10, `049ceb5`, as the next row.)* |
| *(v2.3)* `test_session_message_with_a_non_text_block_reaches_the_callback_whole` | P7: a `session_message` with a text and an image block, sent over the wire, reaches the callback with both blocks typed; without the parse the shim drops the message whole, its text included. |

### 7.2 The router and the bridge — `tests/sdk/agent/test_acp_subagents.py`

Units feed `ACPSubagentSessions` and `_OpenHandsACPBridge(subagents=True)` directly (as `TestClientForkTextRouting`
feeds the bridge today), with the shim's models and the library's update models, and with `on_session_event` set
to a list's `append`:

`test_announcement_stores_parent_cell_and_cancel_grant` ·
`test_omitted_field_keeps_value_and_null_clears_it` ·
`test_parent_tool_call_id_survives_meta_without_it` ·
`test_child_is_never_reparented_nor_its_own_parent` ·
`test_child_text_never_reaches_the_root_answer` ·
`test_child_text_is_stored_per_segment_in_transcript_order` ·
`test_usage_never_splits_a_text_segment` ·
`test_chunked_message_is_stored_whole_at_the_next_boundary` ·
`test_message_upsert_replaces_content_and_keeps_participants` ·
`test_child_cost_is_on_its_association_and_never_booked_to_the_conversation` ·
`test_child_usage_leaves_root_usage_sync_and_context_window_alone` ·
`test_child_tool_calls_are_keyed_by_session_and_tool_call_id` ·
`test_turn_end_force_completes_only_root_tool_calls` ·
`test_aborted_turn_fails_child_tool_calls_with_their_session` ·
`test_child_events_go_to_the_session_emitter_and_root_events_to_the_turn` ·
`test_child_traffic_between_turns_reaches_the_emitter_in_order` ·
`test_child_events_without_an_emitter_are_dropped_with_a_debug_line` ·
`test_replay_is_neither_stored_nor_grants_cancel` ·
`test_new_connection_withdraws_cancel_and_unconfirms_state` ·
`test_partial_patch_after_reconnect_keeps_the_stored_title` ·
`test_unannounced_session_follows_the_root_path_with_one_warning` ·
`test_subagents_off_uses_the_stock_connection_and_initialize` (patches `acp_agent.ClientSideConnection` as the
existing tests do and asserts `initialize(protocol_version=1)` exactly; *v2, B12:* built in the conversation tests
below instead).

*(v2.2)* Added with the fixes: `test_replayed_child_calls_are_never_tracked_nor_failed_later` (E-2) ·
`test_child_call_open_across_aborted_turns_is_failed_once_and_the_agents_report_wins` (E-1) ·
`test_unstable_updates_on_an_unannounced_session_stay_under_that_session` (E-4);
`test_child_is_never_reparented_nor_its_own_parent` now counts only the router's three refusals.

*(v2.3)* At `6a05b13` these are 24 tests, 33 cases with the merge table's ten, all in #12: the list above with E-1's,
E-2's and E-4's, less the stock-connection test (merged below), and with the cost test renamed
`test_child_cost_is_stored_on_its_association_when_it_changes`, its booking assertion left to
`test_scripted_run_books_only_the_roots_cost` (`ca39def`). They feed the bridge wire updates built with the scripted
agent's builders (V-6).

**E5 in the fork**, through a real `LocalConversation` and an `ACPAgent(acp_command=[sys.executable,
<repo>/tests/fixtures/acp/scripted_agent.py, "--subagents", …], acp_subagents=True)`, or `--transcript` with a
hand-written transcript, no network:

| Test | Pins (E5's nulls) |
|---|---|
| `test_scripted_run_stores_the_scripted_tree` | Rebuilding the tree from stored events with §5's rules gives exactly the transcript's parent links, placements, per-session tool calls, messages and costs. *(v2.3, V-9: its tree reader places a child by its spawning cell only, and any other placement fails the comparison; every expected tree places by cell, so rule 2's fallbacks are exercised by no test.)* |
| `test_scripted_run_keeps_child_text_out_of_the_answer` | The `FinishAction` text is the root's alone. *(v2.3: cut, `a910ac9`; the bridge unit `test_child_text_never_reaches_the_root_answer` pins it.)* |
| *(v2)* `test_scripted_run_books_only_the_roots_cost` | The conversation's accumulated cost is the root's 0.0011, not the children's added. |
| `test_stored_events_validate_against_the_agent_server_event_schema` | Every stored event validates against the `Event` schema in `build_public_openapi()`, so any OpenAPI-typed client parses them. *(v2, B12: built as `tests/agent_server/test_acp_router.py::test_stored_sub_agent_events_validate_against_the_event_schema`, on a real server's REST page.)* |
| `test_scripted_run_with_subagents_off_stores_only_root_work` | Off: no new kinds, no `acp_session_id`; the conforming agent sent no child traffic. *(v2: `[--subagents, --transcript]`; also asserts `initialize` carried no `subagents`.)* |
| *(v2)* `test_subagents_off_uses_the_stock_connection_and_initialize` | Off: the conversation's connection is the library's `ClientSideConnection`, and `initialize`'s params on the wire equal the library's own `InitializeRequest(protocol_version=1, client_capabilities=ClientCapabilities())`. |
| *(v2.3)* `test_subagents_off_stores_only_root_work_through_the_stock_connection[--subagents, --transcript]` | The two rows above, merged (`a910ac9`): the stock connection class, `initialize` equal to the library's own serialization, only the root's `cell-1`, no `acp_session_id`, no new kinds. `[--subagents]` is #12's; `[--transcript]`, which the merge had dropped, is restored on #16 (`306731d`, P4): the player sends no other session's update to a client that did not advertise `subagents`. |
| `test_cancel_acp_session_reaches_the_child_and_its_cancelled_state_is_stored` *(v2.3: merged with `…_does_not_wait_for_the_state_lock` into `test_cancel_acp_session_reaches_the_child_without_waiting_for_the_state_lock`, `a910ac9`, which keeps both tests' assertions)* | With `--cancel-wait 30` and `run()` in a thread, the test thread retries `cancel_acp_session("child-b")` until it stops raising `ACPSessionNotFoundError` (the announcement has been handled; under a synchronous `run()` the events themselves are stored only after the step, §6); S2's request log shows `session/cancel` for `child-b`; afterwards `child-b`'s cell is stored failed and its idle/cancelled snapshot follows. |
| `test_scripted_transcript_replays_an_outgoing_only_recording` | A transcript of agent lines only (the shape of D1's golden files) replays into the same stored tree as its hand-written source. *(v2: `test_scripted_transcript_replays_a_recording[full, outgoing-only]`.)* |
| `test_cancel_acp_session_refuses_a_child_without_a_grant` | `child-c`: `ACPSessionNotCancellableError`; the request log shows no `session/cancel`. |
| `test_cancel_acp_session_refuses_unknown_and_root_sessions` | 404- and 409-class errors respectively. |
| `test_cancel_acp_session_without_a_live_connection_is_refused` | Before `init_state`: `ACPSessionNotCancellableError`. |
| `test_cancel_acp_session_does_not_wait_for_the_state_lock` | During a sync `run()` (state lock held for the turn) the cancel returns within 2 s. *(v2: the call that succeeded began while the run's thread held the state lock, and the run then finishes.)* |
| *(v2)* `test_transcript_interval_paces_the_replay` | `--transcript-interval-ms 50`: the run takes at least 50 ms per update (B8). *(v2.3: cut, `6dcde3e`; pacing is unpinned, P5.)* |
| *(v2)* `test_transcript_wait_point_that_is_never_reached_exits_non_zero` | `--wait-timeout 0.2` with no client: the script exits non-zero. *(v2.3: cut, `6dcde3e`; restored as the next row.)* |
| *(v2.3)* `test_transcript_exits_non_zero_when_a_wait_point_outlasts_the_wait_timeout` | P6′, on #16 (`6a05b13`): the agent started with `--transcript` and `--wait-timeout 0.2`, never sent `initialize`, exits non-zero within 10 s. That the exit comes from the wait point raising is unpinned, P6. |
| *(v2)* `test_a_childs_stored_timestamps_never_decrease_in_log_order` | §5 rule 10 (a), for all four children of the scripted run. |
| *(v2)* `test_a_reconnect_snapshot_is_later_than_the_childs_earlier_events` | A second connection to the same conversation: one `environment` snapshot, for the child left running, later than its earlier events and no later than its next. |
| *(v2)* `test_a_spawning_cells_started_event_precedes_its_whole_subtree` | §5 rule 10 (b), for all four children. |
| *(v2.2)* `test_cancel_acp_session_for_an_idle_child_that_keeps_its_grant_is_sent` | E-3: after `child-b` is idle, the cancel is sent and answered, and nothing new is stored for `child-b`. |

*(v2.3)* At `6a05b13` the conversation tests are 13, 15 cases: in #12 the tree, the cost, the opt-off test's
`[--subagents]` and two ordering tests; in #14 the five cancel tests; in #16 the transcript replay's two cases, the
opt-off test's `[--transcript]`, the wait-timeout test and the reconnect test, which drives a recording so that a
child stays open across two agent processes.

### 7.3 Everything else

| File | Tests |
|---|---|
| `tests/sdk/event/test_acp_subagent_events.py` | `test_subagent_events_round_trip_through_json` · `test_legacy_acp_tool_call_event_loads_without_session_fields` · `test_root_tool_call_event_is_stored_as_before` (`exclude_none` dump has no new keys) · *(v2)* `test_subagent_events_visualize_their_essentials[…]` · `test_unconfirmed_state_is_shown_as_such` *(v2.3: 9 cases, in #11; the root-call test was cut, `a910ac9`, P3)* |
| `tests/sdk/event/test_resume_transcript.py` | `test_resume_transcript_skips_child_tool_calls` |
| `tests/sdk/agent/test_acp_dedup_and_truncation.py` | `test_remote_events_merge_child_and_root_calls_separately` |
| `tests/sdk/test_settings.py` | `test_acp_create_agent_forwards_subagents` *(v2.3: cut, `a910ac9`, and S1 no longer touches this file; the resolver test builds the agent, P2)* |
| *(v2)* `tests/sdk/profiles/test_resolver.py` | `test_acp_profile_carries_the_subagents_opt_in_to_the_agent[False, True]` · `test_acp_seeded_profile_keeps_the_subagents_opt_in` (B2) |
| *(v2.2)* `tests/sdk/persisted_settings_baselines/v2/agent_profile_acp_subagents.json` | picked up by the `Persisted settings` guard and the same cross test (B2) |
| `tests/sdk/persisted_settings_baselines/v7/agent_settings_acp_subagents.json` | picked up by the existing compat check *(v2: `tests/cross/test_check_persisted_settings_compat.py::test_collect_fixture_cases_and_validate_current_repo_fixtures`, in CI's `cross-tests`)* |
| `tests/sdk/conversation/local/test_local_conversation_event_emitter.py` (only if S1 lands before S2, which then owns these tests) | S2's emitter tests (S2 §4.10): an event emitted from the ACP thread during a synchronous `run()` does not deadlock and lands after the step; events keep submission order; events emitted after `close()` are dropped *(v2: S2's, B1; S1 adds none)* |
| `tests/agent_server/test_acp_router.py` (S2's file) | `test_cancel_acp_session_success` · `…_conversation_not_found` · `…_unknown_session_returns_404` · `…_not_cancellable_returns_409` · `…_non_acp_returns_400` · `…_timeout_returns_504` (upstream's style: a mocked event service). *(v2, B12: against a real agent-server and the scripted agent: `test_a_cancel_reaches_the_child_and_its_cancelled_state_is_stored` · `test_a_cancel_for_an_unknown_conversation_is_not_found` · `test_a_cancel_for_an_unknown_session_is_not_found` · `test_a_cancel_for_a_child_without_a_grant_is_a_conflict` · `test_a_cancel_on_a_conversation_that_is_not_acp_is_a_bad_request` · `test_a_cancel_the_agent_does_not_take_in_time_times_out` · `test_stored_sub_agent_events_validate_against_the_event_schema`)* *(v2.3: 6 cases; the first was cut, `a910ac9`, so the route's 200 is the cross test's alone, P9; the schema test is in #12, the route's five in #14)* |
| `tests/agent_server/test_event_service.py` | `test_cancel_acp_session_runs_off_the_event_loop` · *(v2)* `test_cancel_acp_session_on_an_inactive_service_is_refused` *(v2.3: module functions now, out of `TestEventServiceCancelACPSession`; the first pins that the event loop keeps running while the cancel blocks, not a thread id, `5b17efd`)* |
| `tests/cross/test_remote_conversation_live_server.py` | `test_acp_subagent_sessions_over_live_server`: a real server, the scripted agent with `--subagents --cancel-wait 30`, events read over REST and WebSocket, the cancel route end to end (the agent-server AGENTS.md asks for one such test per endpoint addition) |
| `clients/typescript/src/__tests__/api-clients.test.ts` | `ConversationClient.cancelAcpSession posts to the session cancel endpoint` · `… encodes the session id` · `RemoteConversation.cancelAcpSession posts for its conversation` |
| `clients/typescript/src/__tests__/acp-providers.test.ts` | `forwards the sub-agent opt-in` |
| `clients/typescript/src/__tests__/event-types.test.ts` | `sub-agent event shapes accept stored events` · *(v2)* `each guard recognises only its own kind` *(v2.3: the first was cut, `a910ac9`; the client has 5 tests, all in #15)* |
| *(v2)* `.github/workflows/tests.yml` | S1's live file joins upstream's `acp-live-tests` job, which skips it without its variables |
| *(v2.3)* `tests/conftest.py` | no tests: `subagent_snapshots` and `wait_until`, shared by the sub-agent files and the live file (V-6) |

### 7.4 The live tier (Gate B)

Spec §4 layer 5: "S1, S2: through the SDK's own tests, with `dr-acp` behind the bridge". The fork cannot name
`dr-acp`, so the test is generic and the agent is configured from outside:

- **In the fork:** `tests/sdk/agent/test_acp_subagents_live.py`, `pytestmark = pytest.mark.acp_live` (upstream's
  marker for live ACP probes, deselected by default), skipped unless `OPENHANDS_ACP_LIVE_AGENT_COMMAND` is set
  (a shell-split command line; the same variable S2's live tier reads, S2 §9) together with
  `OPENHANDS_ACP_LIVE_SUBAGENTS_PROMPT` (a prompt that makes that agent spawn sub-agents, at least one with a
  child of its own). The agent runs with `acp_subagents=True`.
  - `test_live_agent_tree_is_well_formed`: one prompt; every stored child has a known parent; every
    `parent_tool_call_id` names a stored tool call of its parent; no child text in the answer; every child that
    reported a cost has it on its association; the conversation's cost equals the root's last reported cost.
  - `test_live_agent_stops_one_subagent_and_its_branch`: the run through `arun()` (so child events are stored as
    they come, §6), watched through a conversation callback; on the first `running`, cancellable child that has a
    child of its own, `LocalConversation.cancel_acp_session` from a worker thread; within 120 s
    that child and every session announced under it are stored `idle`/`cancelled`, no tool call starts in the
    branch after its root's idle snapshot, and the turn ends.
  - *(v2, B13) As built:* the tree test also requires one child whose parent is not the root, and checks "no child
    text in the answer" for stored child text of 40 characters or more (`QUOTED_TEXT_MIN_CHARS`); it does not
    assert children's costs live (a unit test does). The stop test runs `arun()` under a 120 s limit, cancels the
    first running, cancellable child seen to have a child of its own, then waits up to 30 s for that child and every
    session under it to be stored `idle`/`cancelled`, and finds no call of the branch stored non-terminal after the
    child's cancelled snapshot.
- **In deep-reasoning:** the same on-demand workflow S2's live tier needs (`workflow_dispatch`, input: the SDK
  fork's ref; not in the public fork, because installing `dr-acp` installs deep_reasoner_beta, which needs a read
  token): it checks out both, installs the fork's packages and `dr-acp`, and runs S1's file with
  `OPENHANDS_ACP_LIVE_AGENT_COMMAND="dr-acp --config <D1's live config>"`, the CS vs STAT prompt and
  `OPENAI_API_KEY` from the repository's secrets (gpt-6-luna, cents per run), and S2's file with S2's variables. Comparing the stored tree with deep_reasoner's own node tree needs deep_reasoner's run
  directory, so that stronger check is D5's cross-repo replay (E5's second half), not this tier. See §11 item 2
  for who writes the workflow. *(v2, B13: it is D5 §7.4's `fork-live.yml`, inputs `sdk_ref`, `suites`, `sdk_repo`,
  `live_config`, committed on deep-reasoning's `ci/fork-live` on top of D1's `c8d7fbb` until D5's branch carries it.
  The S1 step runs `dr-acp --config docs/configs/advising/main.yaml --home <temp>` with the prompt "/compare-departments
  Which department is lighter for a first-year student, CS or STAT?". Run 37141960911 passed 2 of 2 at `0cfb6a2`, the
  Gate B section.)* *(v2.2: run 37147706623 passed 2 of 2 at `a3279be`, in 41.3 s; it supersedes the first.)*
  *(v2.3: run 37171079147 passed 2 of 2 at `2675399`, in 48.26 s; the live file is unchanged since, and the stack's
  top differs from `2675399` in three other test files only. The refactor moved the file's helpers to
  `tests/conftest.py`, so both tests poll every 0.02 s instead of 0.1 s; their assertions are as above. At Gate C
  the tree test is in #12 and the stop test in #14.)*

---

## 8 · Upstream guards and the pull request

**The branch** `feat/acp-subagent-sessions`, cut from the fork's `deep-reasoning` at `91430aa`, in five commits,
each green on its own, each cherry-pickable onto `main`. *(v2, B1, B7, B17: built on S2's `feat/agent-surfaces`
`6f97bf3`, as `13f4571`, `d10c021`, `6938ba5`, `57c0925`, `0cfb6a2`, under exactly these five titles. Commit 3 also
carries `LocalConversation.cancel_acp_session`, `ACPAgent.cancel_acp_session`, the agent-profile field (B2) and the
`tests.yml` line; commit 4 is the route, `EventService` and their tests; commit 5 adds the type budget. No commit of
S2's pieces was needed. CI ran only at the head, so "each green on its own" is unverified.)* *(v2.2: five more
commits followed, the fixes made on v2.1's rulings: `d74940b` `fix(acp): never track a child tool call that only a
session/load replay sent`, `f6d8e1e` `fix(acp): fail a child tool call at most once across aborted turns`, `e65335d`
`test(acp): pin that a cancel for an idle child keeping its grant is sent`, `562c31d` `fix(acp): warn once for
unstable updates on a session never announced`, and `a3279be` `test(profiles): add a persisted ACP agent-profile
fixture with the sub-agent opt-in`; between them, two merges, `0f161f8` (the fork's `deep-reasoning`) and `2114d23`
(S2's `5e3317f`). Upstream's main-only guards now run on PR #2 through the fork-only `1f2b52d` and passed at
`a3279be`; the OpenAPI ratchet passes locally, B14. Whether the fixes fold into the commits they mend is the PR
split's call, at Gate C.)* *(v2.3: the branch then took the literate refactor, fourteen commits and `2675399` (the
header's "Changed by the refactor"), with S2's refactor merged at `3fb8f8d` and S2's `d938c90` at `cd6cb23`. For
Gate C its net diff was cut by idea into seven levels, one commit each, #10 to #16 (the Gate C section), so the
fixes sit in the levels whose code they mend: E-1, E-2 and E-4 in #12, E-3's test in #14, the profile fixture in
#13. Each level is green on its own in CI. Nothing is cherry-picked onto `main`: the stack is internal to the fork,
its bottom based on `deep-reasoning`, and nothing goes upstream. PR #2 is closed as superseded.)*

1. `feat(acp): carry ACP's unstable sub-agent types past agent-client-protocol 0.12.1` — `acp_unstable.py`,
   `test_acp_unstable.py` (with the tripwire).
2. `feat(events): ACP sub-agent session events` — `event/acp_subagent.py`, `ACPToolCallEvent` fields, exports,
   visualizer, resume transcript, `RemoteConversation` cache key, the OpenAPI allowlist, event tests.
3. `feat(acp): route and persist sub-agent sessions in the ACP bridge (opt-in acp_subagents)` —
   `acp_subagents.py`, `acp_agent.py`, the settings field and fixture, S1's modes of the scripted agent,
   router/bridge/E5 tests, the live tests. If S1 lands before S2, this commit is preceded by one that adds the
   shared pieces exactly as S2 specifies them (`_emit_event_from_any_thread` with its wiring and tests, the
   scripted agent's skeleton), so S2's PR finds them in place.
4. `feat(agent-server): cancel one ACP sub-agent session` — `LocalConversation`, `EventService`, the route on
   `conversation_acp_router` (and `acp_router.py` with its registration, if S1 lands first), the response model,
   router/service/live-server tests.
5. `feat(ts-client): sub-agent event types and cancelAcpSession` — §4.9.

**Upstream's guards** run only on pull requests to `main`, so the branch, cherry-picked onto the fork's `main`,
gets a draft PR there that is never merged (spec §4 layer 3). Expected results, each checked against the script:
REST breakage (oasdiff) passes (additive route, additive `oneOf`, optional properties); persisted settings pass
with the new fixture; OpenAPI quality passes with the allowlist entries; SDK API breakage passes (additions
only); the TypeScript client CI passes against the pinned release (hand-written types); the endpoint audit
reports one client-ahead route, allowlisted; pre-commit (ruff, pycodestyle, pyright, the dynamic-attribute
ratchet, import rules) passes. The PR description uses upstream's template and leaves its `HUMAN:` field as the
placeholder for Michael. No issue or pull request is opened on any upstream repository. *(v2, B14: the draft PR is
michaeltheologitis/software-agent-sdk#2, against `feat/agent-surfaces`, not a cherry-pick onto `main`, so the guards
that run only for pull requests to `main` did not run in CI; PR #2's description reports them run locally and
passing. Its `HUMAN:` field is the placeholder, as planned. Pre-commit and the endpoint audit ran in CI, green.)*
*(v2.3: no branch is cherry-picked onto `main` and no draft is opened there. The guards run on each level of the
Gate C stack instead, through the fork-only `1f2b52d`'s pull-request triggers, and are green on all seven; each
level's description uses upstream's template with its `HUMAN:` field left as the placeholder.)*

**Upstream merges** (spec Q1 (a)): our conflicts sit in `acp_agent.py`'s `session_update`, `_start_acp_server`
and tool-call close-out hunks of §4.4 (≈100 lines in upstream's busiest file); everything else is new files or
appended lines. *(v2: `acp_agent.py` is +287 −40, B16, and the start hunk is in S2's `_launch_acp_session`, B1.)*
*(v2.3: +294 −43 at `6a05b13`; the load hunk is now one `with client.replaying(...)` line around upstream's own call,
V-5.)*

**When the library catches up** (the tripwire fails): delete `acp_unstable.py`; import `SubagentUpdate`,
`SessionMessage`, `SessionMessageChunk` and the capability from `acp.schema`; replace the connection subclass
with the library's own routing (the bridge's `unstable_session_update` becomes three `isinstance` branches in
`session_update`); bump the pin; re-run `pytest -m acp_live tests/sdk/agent/test_acp_conformance.py` for Claude
Code, Codex and Gemini, because the bump changes the library they all go through. `acp_subagents.py`, the events,
the route and the client stay. *(v2.3, V-2: the bridge's one `initialize` call
then has to pass the library's capability itself when the opt-in is on, since today the shim's connection adds it,
`acp_agent.py:3478`.)*

---

## 9 · Where S1 and S2 touch the same code

Checked against S2's design (`design/s2` `9e32261`, its §8). Three pieces are shared by design, one owner per
landing order: the out-of-turn emitter (rows 6–7), the scripted test agent (row 13) and `acp_router.py`
(row 9). Everything else is textual neighbourhood, with the rule that lets either PR land first. *(v2, B1: S2
landed first, and S1 is stacked on it. Rows 6, 7 (the emitter), 9 and 13 are S2's code, used by S1 unchanged; row
4's `_start_acp_server` is S2's wrapper around `_launch_acp_session`, where S1's lines sit; row 3's order holds,
S2's recorder first at `acp_agent.py:1725`. The other rows hold as written.)* *(v2.3: at `6a05b13` S2's recorder is
at `acp_agent.py:1738`, still first; row 15 gains one shared file, `tests/conftest.py`, where S1 adds
`subagent_snapshots` beside S2's helpers and makes `wait_until` return what it waited for (V-6); and S2's stack is
merged into the fork's `deep-reasoning` (`69c00ca`), the base of S1's.)*

| # | Place (`53a4bc5`) | S1 | S2 | Rule |
|---|---|---|---|---|
| 1 | `acp_agent.py` imports `:42–74` | the shim's names, `ACPSubagentSessions` | `AvailableCommandsUpdate`, `ConfigOptionUpdate`, its models | One import list; the second to land merges by hand, keeping it sorted. |
| 2 | `_OpenHandsACPBridge.__init__` / `reset()` `:1289–1345` | `subagents`, `on_session_event`; `reset()` keeps open child tool calls | `_session_controls`, `_commands_reported`, `on_session_controls_changed` | Appended attributes, no shared name; neither is cleared by `reset()`. |
| 3 | `_OpenHandsACPBridge.session_update` `:1427–1548` | the child diversion after the fork branch (`:1451`); the `ToolCallStart`/`ToolCallProgress` branches gain the session key | one line, first after the idle-clock reset: `if self._record_session_controls(session_id, update): return` | S2's line stays first: commands and options of any session go to S2's per-session recorder (only the root's are published) and never reach S1's diversion. S1's diversion therefore never sees those two types. |
| 4 | `_start_acp_server` and `_init` `:2912–3330` | the bridge's `subagents` flag and emitter, the seed, the connection class (`:3070`), the `initialize` call (`:3090`), root id and `replaying` around `load_session` (`:3204–3240`) and after `:3252` | `_starting_session` set at the top and cleared in a `finally`; reads `init_response.agent_capabilities.session_capabilities.close`; records the `session/new`/`session/load` responses' options; applies start-time option values after the model call; one post-start publish | S2 reads the `initialize` *response*, so S1 changes the call freely; S2's blocks sit after the model call, away from S1's lines. S1's seed runs before the subprocess starts, independent of `_starting_session`. |
| 5 | `ACPAgent` fields and private attributes `:1714–1992` | `acp_subagents` | `acp_config_options`, `_on_session_event`, `_session_controls_lock`, `_published_session_controls`, `_supports_session_close`, `_starting_session` | Appended. `_on_session_event` is S2's name, used by S1 (row 6). |
| 6 | **Events outside a turn** | every child event, during turns and between them (decision G) | every controls event (S2 decision B) | **One primitive:** `ACPAgent._on_session_event`, set by `LocalConversation._ensure_agent_ready` to `_emit_event_from_any_thread` before `init_state` (S2 §4.3, Appendix A.3–A.4). Whoever lands first builds it with those names and semantics; the other uses it. Both streams share one FIFO worker. S1 passes the emitter to the bridge as `on_session_event` at each `_start_acp_server`; S2 publishes through the agent. |
| 7 | `LocalConversation` `:1533–1600`, `:1721–1803` | `cancel_acp_session` (no state lock) | the emitter and its wiring, `set_acp_config_option`, `_replace_acp_agent` extracted from `switch_acp_model` | Adjacent methods. S1 needs nothing rebound on S2's agent swap (its emitter belongs to the conversation, not the agent). |
| 8 | `openhands/sdk/event/__init__.py` | three kinds | `ACPSessionControlsEvent` | Adjacent import and `__all__` lines. |
| 9 | **Routes** | `POST …/acp/sessions/{session_id}/cancel` | `acp_router.py`: `acp_router` (`/acp`, the preview) and `conversation_acp_router` (`/conversations/{conversation_id}/acp`, the set route), registered in `api.py` after `conversation_router` | **One module:** S1's route goes on `conversation_acp_router`; whoever lands first creates the module, the router and the `include_router` line. Path segments do not overlap (`/sessions/…` vs `/config-options`). |
| 10 | `EventService` after `switch_acp_model` `:2005–2025` | `cancel_acp_session` | `set_acp_config_option` | Adjacent methods. |
| 11 | `ServerInfo.capabilities` (`server_details_router.py:63–70`) | none: its events exist only on a server that has S1, and the cancel route answers 404 where it does not | `acp_session_controls_v1` | No overlap. |
| 12 | TypeScript client | `cancelAcpSession` ×2, three hand-written event interfaces in `src/events/types.ts`, the `ACPToolCallEvent` intersection, `ACP_SETTINGS_KEYS` | its client methods, `src/models/acp-session-controls.ts`, `ACPSessionControlsEvent` and its guard in `src/events/types.ts` | Same files (`conversation-client.ts`, `remote-conversation.ts`, `events/types.ts`, `index.ts`, `endpoint-audit.config.json`, `api-clients.test.ts`); union of both, one `allowClientOnly` entry each. |
| 13 | **The scripted test agent** `tests/fixtures/acp/scripted_agent.py` | `--subagents`, `--cancel-wait`, `--transcript`, `--wait-timeout`; serving through `Connection` and `build_agent_router` with a raw tap (§4.10) | its default behaviours, `--no-close`, `--no-commands`, `--slow-set`, `SCRIPTED_ACP_LOG` (S2 Appendix C) | **One script:** whoever lands first creates it; the other adds its flags. If S2's `acp.run_agent` serving is in place, S1 swaps that one call (§4.10). |
| 14 | Upstream guards | `meta` fields (ACP `_meta`, opaque by protocol) need weak-schema allowlist entries; a v7 persisted-settings fixture | fully typed; no settings field | Independent: only S1 edits the allowlist and the settings baselines. |
| 15 | Tests | new files; does not edit `test_acp_agent.py` | new files; does not edit it | No overlap; `tests/agent_server/test_acp_router.py` is S2's file, to which S1 adds its route tests. |
| 16 | The generated TS schema in the fork's release step | regenerated | regenerated | Never merged by hand; regenerate after both. |

---

## 10 · What S1 relies on from its neighbours

**D1's contract (`f281109` §5): nothing must change.** S1 relies on these, all already in D1's design:

1. Every child is announced on its parent's session before any traffic bearing its id (§5.4 rule 1).
2. Announcements carry `_meta.openhands.parentToolCallId` naming a tool call already sent on the parent's session
   (§5.4 rule 2); later updates that carry `_meta` repeat it (§5.2's idle row does). S1 tolerates its absence
   (sticky field).
3. Every child is announced with `capabilities.cancel` (§5.2) and a `session/cancel` with the full child id stops
   its branch (§3 item 13); replayed announcements carry no capabilities (§5.7), which S1 would ignore anyway.
4. Ids are path-safe (`<run>-n<node>`, decision F of D1).
5. The Stop acknowledgement and each child's reasoning are `agent_thought_chunk`s on the child's session (§3 item
   9, §5.2): S1 stores them as `ACPSessionTextEvent` **only if §3.1 item 1 here is approved**; if it is not, D1's
   acknowledgement needs another carrier and that is D1's change to make. *(v2: approved at design, §3.1; built.)*
6. The golden recordings (§8.3) are agent-outgoing JSON-RPC messages, one per line, with prompt responses
   carrying `stopReason` and the root id normalized consistently: the scripted agent's `--transcript` mode
   (§4.10) replays them as they are.
7. No child traffic follows the root's prompt response (§5.4 rule 7); S1 stores late traffic anyway.

One observation for D1, not a change: D1 keeps `capabilities.cancel` on a child after it turns idle; C1 hides
Stop on idle children by §5 rule 6, so nothing breaks, but a Stop sent to an idle node by another client reaches
`dr-acp`, which D1 already treats as a no-op for a re-driven child. *(v2, B3: and a reconnect no longer writes a
snapshot for such an idle child, at C1's request; the bridge holds no grant for it after a reconnect, so the route
answers 409.)*

**C1** reads only §5, and runs the scripted agent (`--subagents --cancel-wait N`) by path from a checkout of the
SDK fork for its Canvas end-to-end run. **D5** sets `acp_subagents: true` for `dr-acp` (§4.6), replays D1's
recordings through the scripted agent's `--transcript` mode into the pinned agent-server and compares the stored
tree with `testing.tree` (E5's second half), and hosts or absorbs §7.4's live workflow, shared with S2's.
**S2** shares three pieces (§9). **C3, D2** do not touch S1. *(v2: what C1 and D5 may rely on is now stated as
guarantees in §5.1. What they asked of S1 and got: the opt-in on the agent profile (C1 §9.1 item 1, D5 §8.2: B2,
without the profile fixture), transcript pacing (C1 §9.1 item 2: B8), the ordering facts as contract (C1 §9.1
item 3: §5 rule 10, B11), and reconnect snapshots for active children only (C1 §9.1 item 4: B3). D5's
`fork-live.yml` exists on `ci/fork-live` and ran S1's live tier, B13.)* *(v2.3: of those, the transcript pacing C1
asked for exists and is unpinned (P5, the section after the Gate C section); the rest hold and are pinned at
`6a05b13`. The live tier ran again at `2675399`, run 37171079147, 2 of 2.)*

---

## 11 · Open items

1. **The third event kind** (§3.1 item 1) needs the Conductor's yes, or Michael's if it reads as a change of the
   approved event model. *(v2: resolved. Accepted at design, spec "Rulings at design, 2026-10-02" (3); built.)*
2. **Who writes the live workflow in deep-reasoning** (§7.4), which S2 needs too (S2 §10 item 3). S1's and S2's
   Gate B need it before D5 exists; the recommendation is one small `workflow_dispatch` workflow on a
   deep-reasoning branch from `self-hosted-v1`, written by whichever Implementer reaches its live tier first and
   absorbed by D5's cross-repo CI. It also needs `dr-acp` runnable (D1's Implementer) and D1's live config path.
   *(v2: resolved. D5 §7.4's `fork-live.yml`, on `ci/fork-live` over D1's `c8d7fbb`; run 37141960911, B13.)*
3. **The `@final` suppression** (§3.1 item 3) is the one line upstream may push back on; the fallback is decision B's
   alternative (1), observers, at the cost of a logged exception per sub-agent update. *(v2.3: no upstream PR is
   opened; the stack is internal to the fork, so this stands only if the work is ever offered upstream.)*
4. **Whether the TypeScript commit rides the same upstream PR** (client-ahead, allowlisted) or follows the server's
   release as its own PR. The spec says one PR; upstream's own flow would split it. *(v2: it rides PR #2 as its fifth
   commit; the question stands for upstream.)* *(v2.3: it is its own level, #15, inside the fork; nothing goes
   upstream.)*
5. **The shared pieces' landing order** (§9 rows 6, 9, 13): whichever of S1 and S2 is built first creates the
   emitter, `acp_router.py` and the scripted agent to the other's specification. The Conductor sequences the two
   Implementers so they do not both create them on parallel branches; if they do, the second rebases onto the
   first's commit and drops its own copy. *(v2: resolved. S2 built all three; S1 is stacked on it, B1.)*
6. **Child events still queued at `close()` are dropped** (S2's emitter cancels pending jobs, §6). Draining instead
   would need `close()` never to be called while the state lock is held; not needed by any v1 agent, since
   dr-acp's children all end before the root's turn does.
7. **Cost snapshots per change** could be frequent for a generic agent that reports usage often; D1 throttles at
   the source (≤ 2 per second per dirty child). If E6's 50-child run shows the store as the bottleneck, add a
   per-child minimum interval in the router; the contract does not change.
8. *(v2)* **Rule on the size** (B16): 4,030 lines added against v1's ≈1.8k and the spec's ≈1.5k; about 13.5 h at
   Gate C against ≈5 h. *(v2.2: 4,155 added at `a3279be`, about 14 h.)* *(v2.3: 3,730 at `6a05b13`, after the
   refactor and the restored pins, about 12.4 h; the stack's levels add 3,741, about 12.5 h.)*
9. *(v2)* **Run upstream's main-only guards in CI** (B14): REST API breakage, persisted-settings compatibility and
   the TypeScript client's CI ran only locally. A draft PR of S1's commits (on S2's) against the fork's `main`, as
   spec §4 layer 3 asks, would run them. The Conductor decides whether that comes before Gate B or before
   anything goes upstream. *(v2.1: the Cartographer ran them here; all pass but the ratchet's S2 pointer, item 13.)*
   *(v2.2: resolved. The fork-only `1f2b52d` runs them on pull requests into the fork's branches; all green on PR #2
   at `a3279be`, B14.)* *(v2.3: and on each level of the Gate C stack; nothing goes to `main` or upstream.)*
10. *(v2)* **The Python `RemoteConversation` cache can reorder** (PR #2's notes): `RemoteEventsList` merges an ACP
    call's `started` and terminal events in place, which can reorder its cache when child traffic interleaves; the
    stored log and the REST page are in order (`test_acp_subagent_sessions_over_live_server` checks the REST log).
    Named as a follow-up by the build; C1 reads events through Canvas's own client, not this cache. *(v2.3: still a
    follow-up, named again in #11's notes.)*
11. *(v2)* **A persisted agent-profile fixture for the opt-in** (B2), which C1 and D5 asked for: not committed, so
    upstream's profile-compatibility check does not pin `ACPAgentProfile.acp_subagents`. About 12 lines, beside
    `tests/sdk/persisted_settings_baselines/v2/agent_profile_default.json`, if wanted. *(v2.2: resolved; built in
    `a3279be` as `v2/agent_profile_acp_subagents.json`.)*
12. *(v2)* **E5's second half is D5's** (§5.1): no test in the fork replays D1's actual golden recordings; D5's
    `bridge-replay` job does, once built. *(v2.1: the Cartographer's uncommitted probe replayed all nine through the
    bridge, 9 of 9 equal, as-built §7.3; D5's job is still the committed check.)*
13. *(v2.1)* **The OpenAPI quality ratchet fails at S1's head, on S2's pointer** (as-built §7.6): one
    `empty-object-schema` at `/api/canvas-extensions/installed/{extension_name}/panels/{panel_id}/icon`'s response,
    failing at S2's `6f97bf3` too. S1's three `meta` locations are allowlisted and none is reported. It is S2's to fix
    (an allowlist entry or a typed response), and S1's head inherits the fix; PR #2's description reports the
    allowlist passing, which holds for S1's entries only. *(v2.2: resolved. S2's `13e5904` declares the icon route's
    response as a PNG or SVG image instead of allowlisting it; the ratchet passes locally at `a3279be`, with 65
    allowlisted locations.)*
14. *(v2.1)* **The four uncovered edges** (§3.2 E-1 to E-4): E-2 is a bug to fix before Gate B, E-1 rides with it,
    E-3 and E-4 are stated in §5.1. Each ruling names the test that pins it. *(v2.2: resolved; all four are built
    and pinned at `a3279be`, and CI and the live tier passed there.)*
15. *(v2.1)* **A `session/load` replay of sub-agent traffic is never driven end to end** (B17): a transcript mode that
    answers `session/load` with a replay would let E-2's fix be pinned through a real conversation too; the unit
    test of E-2 is enough for Gate B. *(v2.3: still so; the reconnect test's `session/load` is refused by the player,
    so the bridge falls back to `session/new`.)*
16. *(v2.3)* **What the refactor left unpinned** (the section after the Gate C section): three properties of the
    transcript player, its pacing (P5), a missed wait point raising (P6) and the unstable half of its conformance rule,
    which no conversation can see. P4, P6′ and P7, whose only tests the refactor cut, are pinned again on the stack.
    Whether the three are worth a test is the Conductor's call at Gate C: the first two are a test fixture's own
    behaviour, and the third needs a client that reads the wire, not a conversation.

---

## Appendix A · Signature reference

Every block is valid, ruff-formatted Python (line length 88, upstream's setting) or TypeScript. Bodies are `...`
where §4 describes them. Excerpts of existing classes show only what S1 adds. *(v2: every block is the build's at
`0cfb6a2`, one field or parameter per line wherever there are several; B7 lists what changed from v1. v2.2: A.3
adds the members the fixes added at `a3279be`.)* *(v2.3: every block is the code's at `6a05b13`, the stack's top, after
the literate refactor: A.1's `SubagentState`, `_SubagentInitializeRequest` and `initialize` (V-3, V-2); A.2 without
`_Association`, with `_PER_EVENT_FIELDS` and `_merge` taking the child's id (V-4); A.3's one warn-once set and
helper, `unstable_session_update`'s alias, and `replaying()` in place of `_load_session` (V-1, V-6, V-5); A.5's
`LocalConversation.cancel_acp_session` docstring; A.7's wire builders (V-6). Comments marked `(v2.3, …)` say which.
Blocks keep one field and one parameter per line, so their layout differs from the code where `49dda35` joined
short signatures onto one line; each Python block parses and passes `ruff format --check` at 88 columns.)*

### A.1 `openhands-sdk/openhands/sdk/agent/acp_unstable.py` (the shim)

```python
"""ACP's unstable sub-agent types, carried until agent-client-protocol parses them.

ACP schema 1.24.1 added ``clientCapabilities.subagents`` and the ``subagent_update``,
``session_message`` and ``session_message_chunk`` session updates behind its unstable
flag; agent-client-protocol 0.12.1 drops all four. The models are upstream's generator
output for schema 1.24.1 (python-sdk 9d07d78), adapted to 0.12.1's base model. Delete
this module when ``test_acp_library_rejects_subagent_update`` fails.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Annotated, Any, Final, Literal

from acp.client.connection import ClientSideConnection
from acp.connection import JsonValue, MethodHandler
from acp.interfaces import Client
from acp.meta import AGENT_METHODS, CLIENT_METHODS
from acp.schema import (
    AudioContentBlock,
    BaseModel as ACPModel,
    ClientCapabilities,
    EmbeddedResourceContentBlock,
    ImageContentBlock,
    Implementation,
    InitializeRequest,
    InitializeResponse,
    ResourceContentBlock,
    StopReason,
    TextContentBlock,
)
from acp.utils import request_model
from pydantic import Field, SerializeAsAny, TypeAdapter, ValidationError

from openhands.sdk.logger import get_logger


logger = get_logger(__name__)

UNSTABLE_SESSION_UPDATES: Final[frozenset[str]] = frozenset(
    {"subagent_update", "session_message", "session_message_chunk"}
)

ContentBlock = Annotated[
    TextContentBlock
    | ImageContentBlock
    | AudioContentBlock
    | ResourceContentBlock
    | EmbeddedResourceContentBlock,
    Field(discriminator="type"),
]


class SubagentCapabilities(ACPModel):
    field_meta: Annotated[dict[str, Any] | None, Field(alias="_meta")] = None


class SessionCancelCapabilities(ACPModel):
    field_meta: Annotated[dict[str, Any] | None, Field(alias="_meta")] = None


class SubagentSessionCapabilities(ACPModel):
    cancel: SessionCancelCapabilities | None = None
    field_meta: Annotated[dict[str, Any] | None, Field(alias="_meta")] = None


# (v2.3, V-3) The library's base config: unknown keys are ignored.
class SubagentState(ACPModel):
    """running, idle, requires_action, unknown, or a custom state."""

    state: str
    stop_reason: Annotated[StopReason | None, Field(alias="stopReason")] = None
    field_meta: Annotated[dict[str, Any] | None, Field(alias="_meta")] = None


class SubagentUpdate(ACPModel):
    session_update: Annotated[
        Literal["subagent_update"],
        Field(alias="sessionUpdate"),
    ]
    session_id: Annotated[str, Field(alias="sessionId")]
    title: str | None = None
    description: str | None = None
    capabilities: SubagentSessionCapabilities | None = None
    state: SubagentState | None = None
    field_meta: Annotated[dict[str, Any] | None, Field(alias="_meta")] = None


class SessionMessage(ACPModel):
    session_update: Annotated[
        Literal["session_message"],
        Field(alias="sessionUpdate"),
    ]
    message_id: Annotated[str, Field(alias="messageId")]
    sender_session_id: Annotated[
        str | None,
        Field(alias="senderSessionId"),
    ] = None
    recipient_session_id: Annotated[
        str | None,
        Field(alias="recipientSessionId"),
    ] = None
    content: list[ContentBlock] | None = None
    field_meta: Annotated[dict[str, Any] | None, Field(alias="_meta")] = None


class SessionMessageChunk(ACPModel):
    session_update: Annotated[
        Literal["session_message_chunk"],
        Field(alias="sessionUpdate"),
    ]
    message_id: Annotated[str, Field(alias="messageId")]
    sender_session_id: Annotated[
        str | None,
        Field(alias="senderSessionId"),
    ] = None
    recipient_session_id: Annotated[
        str | None,
        Field(alias="recipientSessionId"),
    ] = None
    content: ContentBlock
    field_meta: Annotated[dict[str, Any] | None, Field(alias="_meta")] = None


UnstableSessionUpdate = SubagentUpdate | SessionMessage | SessionMessageChunk
UnstableUpdateHandler = Callable[[str, UnstableSessionUpdate], None]

_UNSTABLE_UPDATE_ADAPTER: Final = TypeAdapter(
    Annotated[UnstableSessionUpdate, Field(discriminator="session_update")]
)


class SubagentClientCapabilities(ClientCapabilities):
    subagents: SubagentCapabilities | None = None


SUBAGENT_CLIENT_CAPABILITIES: Final = SubagentClientCapabilities(
    subagents=SubagentCapabilities()
)


# (v2.3, V-2) A subclass after all: the wider type serializes a subclass whole.
class _SubagentInitializeRequest(InitializeRequest):
    """Serializes a capabilities subclass whole, so ``subagents`` reaches the wire."""

    client_capabilities: Annotated[
        SerializeAsAny[ClientCapabilities] | None,
        Field(alias="clientCapabilities"),
    ] = None


# ClientSideConnection is @final in agent-client-protocol 0.12.1; this subclass
# lives only until the library parses ACP's sub-agent updates itself.
class SubagentClientSideConnection(
    ClientSideConnection,  # pyright: ignore[reportGeneralTypeIssues]
):
    """A ClientSideConnection that hands ACP's unstable sub-agent updates to a
    callback ahead of the library's router, and advertises ``subagents``."""

    def __init__(
        self,
        to_client: Client,
        input_stream: asyncio.StreamWriter,
        output_stream: asyncio.StreamReader,
        *,
        on_unstable_update: UnstableUpdateHandler,
    ) -> None: ...

    async def initialize(
        self,
        protocol_version: int,
        client_capabilities: ClientCapabilities | None = None,
        client_info: Implementation | None = None,
        **kwargs: Any,
    ) -> InitializeResponse:
        """Send ``initialize``, advertising ``subagents`` unless given other
        capabilities."""
        ...


def route_unstable_updates(
    inner: MethodHandler,
    on_unstable_update: UnstableUpdateHandler,
) -> MethodHandler:
    """Wrap a connection handler: the three unstable updates reach
    ``on_unstable_update`` synchronously, in arrival order; an invalid one is
    logged and dropped; every other message goes to ``inner``."""
    ...


def _unstable_update_kind(
    method: str,
    params: JsonValue | None,
    is_notification: bool,
) -> str | None:
    """The ``sessionUpdate`` of an unstable session/update notification, else None."""
    ...
```

### A.2 `openhands-sdk/openhands/sdk/agent/acp_subagents.py`

```python
"""Sub-agent sessions of an ACP agent, as the bridge sees them on one connection.

The client side of ACP's sub-agent sessions (schema 1.24.1, unstable): which sessions
are children, their merged association, their streamed text and directed messages,
their cost, and whether a client may cancel them now. Bookkeeping only: each method
returns the events to persist; nothing here emits, locks, awaits or does I/O.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any

from acp.schema import UsageUpdate

from openhands.sdk.agent.acp_unstable import (
    SessionMessage,
    SessionMessageChunk,
    SubagentUpdate,
)
from openhands.sdk.event import (
    ACPSessionMessageEvent,
    ACPSessionTextEvent,
    ACPSubagentEvent,
    Event,
)
from openhands.sdk.event.types import SourceType


# (v2.3, V-4) Each stored snapshot is a new event: its own id and time, no parent yet.
_PER_EVENT_FIELDS = {"id", "timestamp", "parent_id"}


class ACPSessionNotFoundError(LookupError):
    """No sub-agent session with this id is known on the ACP connection."""


class ACPSessionNotCancellableError(RuntimeError):
    """The session cannot be cancelled now: no live connection, the root session,
    or no current ``cancel`` grant from the agent."""


@dataclass
class _Pending:
    thought: bool | None
    message_id: str | None
    parts: list[str] = field(default_factory=list)


@dataclass
class _Message:
    sender_session_id: str | None = None
    recipient_session_id: str | None = None
    text: str = ""
    meta: dict[str, Any] | None = None


class ACPSubagentSessions:
    """Routing, merge, segments, cost and cancel grants for one ACP connection.

    A child's association is held as its latest ``ACPSubagentEvent``, whose
    ``cancellable`` is the live grant; each snapshot stored is a new event.
    """

    root_session_id: str | None
    replaying: bool

    def __init__(self, *, mask: Callable[[Any], Any]) -> None: ...

    def seed(self, events: Iterable[Event]) -> list[ACPSubagentEvent]:
        """Register the children stored in ``events``; return the snapshots that
        withdraw their cancel grants and unconfirm their states."""
        ...

    def is_child(self, session_id: str) -> bool: ...

    def key(self, session_id: str) -> str | None:
        """The stored form of a session id: ``None`` for the root."""
        ...

    def on_subagent_update(
        self,
        session_id: str,
        update: SubagentUpdate,
    ) -> list[Event]: ...

    def on_session_message(
        self,
        session_id: str,
        update: SessionMessage,
    ) -> list[Event]: ...

    def on_session_message_chunk(
        self,
        session_id: str,
        update: SessionMessageChunk,
    ) -> list[Event]: ...

    def on_child_text(
        self,
        session_id: str,
        text: str,
        *,
        thought: bool,
    ) -> list[Event]: ...

    def on_child_usage(
        self,
        session_id: str,
        update: UsageUpdate,
    ) -> list[Event]: ...

    def before_update(self, session_id: str) -> list[Event]:
        """Flush ``session_id``'s open segment, ahead of an update that ends it."""
        ...

    def flush_all(self) -> list[Event]: ...

    def check_cancel(self, session_id: str) -> None:
        """Raise unless the agent granted ``cancel`` for this child, live."""
        ...

    # (v2, B7) The private helpers the build added; (v2.3, V-4) _merge takes the
    # child's id and replaces its held event with a merged copy.
    def _merge(
        self,
        child: str,
        update: SubagentUpdate,
    ) -> None:
        """Apply ACP's patch rules: omitted keeps, null clears, a value replaces."""
        ...

    def _snapshot(
        self,
        child: str,
        *,
        source: SourceType = "agent",
    ) -> ACPSubagentEvent: ...

    def _message(
        self,
        session_id: str,
        update: SessionMessage | SessionMessageChunk,
    ) -> _Message:
        """The resolved message, with any participants the update names."""
        ...

    def _message_event(
        self,
        session_id: str,
        message_id: str,
    ) -> ACPSessionMessageEvent: ...

    def _flush(self, session_id: str) -> list[Event]: ...

    def _text_of(self, blocks: Sequence[Any]) -> str: ...


def _parent_tool_call_id(meta: dict[str, Any] | None) -> str | None:
    """``_meta.openhands.parentToolCallId`` when it is a string."""
    ...
```

### A.3 `openhands-sdk/openhands/sdk/agent/acp_agent.py` (excerpts)

```python
class _OpenHandsACPBridge:
    """Excerpt: the new members only."""

    # None without sub-agent sessions: every update takes the root's path.
    subagents: ACPSubagentSessions | None
    # Receives every sub-agent event, in order; unset, they are dropped.
    on_session_event: Callable[[Event], None] | None
    # (v2.3, V-1) (session, routing) pairs already warned about as never announced.
    _warned_unannounced: set[tuple[str, str]]

    def __init__(self, *, subagents: bool = False) -> None: ...

    def unstable_session_update(
        self,
        session_id: str,
        update: UnstableSessionUpdate,
    ) -> None:
        """Route one unstable sub-agent update; never awaits, so it keeps wire order."""
        ...

    def emit_subagent_events(self, events: Sequence[Event]) -> None:
        """Submit each event to ``on_session_event``, in order; drop them while
        replaying, and with a debug line when no emitter is wired."""
        ...

    def flush_subagent_text(self) -> None:
        """Submit every open child segment; runs on the ACP loop after a prompt."""
        ...

    # (v2.3, V-5) Replaces ACPAgent._load_session.
    @contextlib.contextmanager
    def replaying(self, root_session_id: str) -> Generator[None]:
        """Around ``session/load`` of ``root_session_id``: the history it replays
        is neither stored again nor lets an old ``cancel`` grant authorize
        anything."""
        ...

    def _child_session(self, session_id: str) -> str | None:
        """``session_id`` when it is an announced child, else None.

        A session that is neither the root nor a child is warned about once;
        its traffic follows the root's path, as without the opt-in.
        """
        ...

    # (v2.3, V-1) Replaces the two sets and the unstable path's own helper.
    def _warn_unannounced(
        self,
        session_id: str,
        routing: str,
    ) -> None:
        """Warn, once per session and routing, of a session never announced."""
        ...

    # (v2, B7)
    def _route_child_update(
        self,
        child: str,
        update: Any,
    ) -> bool:
        """Store a child's text, usage or other non-tool update; False for a
        tool call, which takes the shared tool-call path. A replayed update,
        a tool call included, is neither stored nor tracked."""
        ...


# (v2, B6) Bound for writing one sub-agent session/cancel notification.
_ACP_SUBAGENT_CANCEL_TIMEOUT: float = 2.0


class ACPAgent(AgentBase):
    """Excerpt: the new members only. ``_on_session_event`` is S2's (its A.3)."""

    acp_subagents: bool = Field(
        default=False,
        description=(
            "Advertise ACP's unstable sub-agent sessions "
            "(clientCapabilities.subagents, schema 1.24.1) to the ACP server, and "
            "route and persist the child sessions it exposes: their association "
            "with the parent, tool calls, messages, text and cost. Off by default "
            "while the protocol draft is unstable."
        ),
    )

    def cancel_acp_session(self, session_id: str) -> None:
        """Ask the ACP server to cancel one sub-agent session's current work.

        Sends ``session/cancel`` for ``session_id`` when the server announced that
        child on the live connection with a ``cancel`` capability. Returns once the
        notification is written; the outcome arrives as the child's next state
        update. Never takes the conversation's state lock, so it works mid-turn.

        Raises:
            ACPSessionNotFoundError: no sub-agent session with this id is known.
            ACPSessionNotCancellableError: no live ACP connection, the root
                session, or no current ``cancel`` grant.
            TimeoutError: the notification was not written within 2 seconds.
        """
        ...

    async def _acancel_acp_session(self, session_id: str) -> None:
        """Check the live grant and send ``session/cancel``; on the ACP loop."""
        ...
```

### A.4 Events: `event/acp_subagent.py` and the `ACPToolCallEvent` fields

```python
class ACPSubagentEvent(Event):
    """An ACP sub-agent session's association with its parent, as last reported.

    ACP's ``subagent_update`` (schema 1.24.1, unstable) with its patch semantics
    already applied: each event is the whole current association, so consumers
    keep the latest per ``acp_session_id``. Written per ``subagent_update``, per
    change of the child's reported cost, and, with ``source="environment"``, when
    a new ACP connection starts (state unconfirmed, cancel withdrawn).
    """

    source: SourceType = "agent"
    acp_session_id: str = Field(description="The child's ACP session id.")
    parent_session_id: str | None = Field(
        default=None,
        description="The parent's ACP session id; None for the root session.",
    )
    parent_tool_call_id: str | None = Field(
        default=None,
        description=(
            "The parent's tool call that spawned the child, from "
            "_meta.openhands.parentToolCallId."
        ),
    )
    title: str | None = None
    description: str | None = None
    state: str | None = Field(
        default=None,
        description=(
            "'running', 'idle', 'requires_action', 'unknown', an agent-specific "
            "value, or None when the current state is unconfirmed."
        ),
    )
    stop_reason: str | None = None
    cancellable: bool = Field(
        default=False,
        description="Whether a client may cancel this child's work now.",
    )
    cost: float | None = Field(
        default=None,
        description="The child's latest cumulative cost; never add it to others.",
    )
    cost_currency: str | None = None
    meta: dict[str, Any] | None = Field(
        default=None,
        description="The association's ACP _meta, verbatim.",
    )


class ACPSessionMessageEvent(Event):
    """A message between ACP sessions, as one session's transcript shows it.

    ACP's ``session_message`` and accumulated ``session_message_chunk`` (schema
    1.24.1, unstable). Upserts: consumers keep the latest per
    ``(acp_session_id, message_id)``.
    """

    source: SourceType = "agent"
    acp_session_id: str | None = Field(
        default=None,
        description="The transcript this entry belongs to; None for the root.",
    )
    message_id: str
    sender_session_id: str | None = None
    recipient_session_id: str | None = None
    text: str = ""
    meta: dict[str, Any] | None = None


class ACPSessionTextEvent(Event):
    """A run of a sub-agent session's own streamed text or reasoning.

    Consecutive ``agent_message_chunk`` (``thought`` false) or
    ``agent_thought_chunk`` (``thought`` true) updates of one child session,
    stored once the run ends.
    """

    source: SourceType = "agent"
    acp_session_id: str
    thought: bool = False
    text: str


class ACPToolCallEvent(Event):
    """Excerpt: the two new fields."""

    acp_session_id: str | None = Field(
        default=None,
        description="The ACP sub-agent session the call ran in; None for the root.",
    )
    meta: dict[str, Any] | None = Field(
        default=None,
        description="The call's latest ACP _meta; recorded with acp_subagents.",
    )
```

### A.5 Settings, conversation and agent-server

```python
class ACPAgentSettings(AgentSettingsBase):
    """Excerpt: the new field, forwarded by ``create_agent()``."""

    acp_subagents: bool = Field(
        default=False,
        description=(
            "Advertise ACP's unstable sub-agent sessions to the ACP server and "
            "persist the child sessions it exposes. Forwarded to "
            ":attr:`~openhands.sdk.agent.ACPAgent.acp_subagents`; off by default."
        ),
    )


# (v2, B2)
class ACPAgentProfile(AgentProfileBase):
    """Excerpt: the new field, forwarded by the resolver's ``_build_acp_settings``
    and carried back from settings by ``build_seed_profile``."""

    acp_subagents: bool = Field(
        default=False,
        description=(
            "Advertise ACP's unstable sub-agent sessions to the ACP server and "
            "persist the child sessions it exposes. Forwarded to "
            ":attr:`~openhands.sdk.settings.ACPAgentSettings.acp_subagents`."
        ),
    )


class LocalConversation(BaseConversation):
    """Excerpt: S1's method. S2's emitter, ``_emit_event_from_any_thread``, its
    executor and its wiring are S2's (its Appendix A.4)."""

    def cancel_acp_session(self, session_id: str) -> None:
        """Cancel one ACP sub-agent session's current work.

        Takes no state lock, so it works while ``run()`` holds the lock for a
        whole turn.

        Raises:
            ValueError: the conversation's agent is not an ``ACPAgent``.
            ACPSessionNotFoundError: as ``ACPAgent.cancel_acp_session``.
            ACPSessionNotCancellableError: as ``ACPAgent.cancel_acp_session``.
            TimeoutError: as ``ACPAgent.cancel_acp_session``.
        """
        ...


class EventService:
    """Excerpt: the new method."""

    async def cancel_acp_session(self, session_id: str) -> None:
        """Run ``LocalConversation.cancel_acp_session`` off the server's loop."""
        ...


# openhands/agent_server/acp_router.py (S2's module; S1's additions)
class CancelACPSessionResponse(BaseModel):
    """A cancel sent to an ACP sub-agent session; its outcome arrives later."""

    session_id: str = Field(description="The ACP session the cancel was sent for.")
    requested: bool = Field(
        default=True,
        description="Always true; the child's next state update confirms it.",
    )


@conversation_acp_router.post(
    "/sessions/{session_id}/cancel",
    responses={
        400: {"description": "The conversation's agent is not an ACP agent"},
        404: {"description": "Conversation or ACP sub-agent session not found"},
        409: {"description": "The ACP session does not accept cancel right now"},
        504: {"description": "The ACP server did not take the cancel in time"},
    },
)
async def cancel_conversation_acp_session(
    conversation_id: UUID,
    session_id: str,
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> CancelACPSessionResponse:
    """Cancel the current work of one ACP sub-agent session.

    Sends ``session/cancel`` for a child session the ACP agent announced with a
    ``cancel`` capability. The child's next ``ACPSubagentEvent`` (idle, stop
    reason ``cancelled``) confirms it.
    """
    ...
```

### A.6 TypeScript client

```typescript
// src/events/types.ts
export type ACPToolCallEvent = AgentServerAcpToolCallEvent & {
  /** The ACP sub-agent session the call ran in; absent for the root session. */
  acp_session_id?: string | null;
  /** The call's latest ACP `_meta`; recorded only for agents with `acp_subagents`. */
  meta?: Record<string, unknown> | null;
};

/** The latest association of an ACP sub-agent session with its parent. */
export interface ACPSubagentEvent extends BaseEvent {
  kind: 'ACPSubagentEvent';
  acp_session_id: string;
  parent_session_id?: string | null;
  parent_tool_call_id?: string | null;
  title?: string | null;
  description?: string | null;
  state?: string | null;
  stop_reason?: string | null;
  cancellable?: boolean;
  cost?: number | null;
  cost_currency?: string | null;
  meta?: Record<string, unknown> | null;
}

/** A message between ACP sessions, as one session's transcript shows it. */
export interface ACPSessionMessageEvent extends BaseEvent {
  kind: 'ACPSessionMessageEvent';
  acp_session_id?: string | null;
  message_id: string;
  sender_session_id?: string | null;
  recipient_session_id?: string | null;
  text?: string;
  meta?: Record<string, unknown> | null;
}

/** A run of a sub-agent session's own streamed text or reasoning. */
export interface ACPSessionTextEvent extends BaseEvent {
  kind: 'ACPSessionTextEvent';
  acp_session_id: string;
  thought?: boolean;
  text: string;
}

export interface CancelAcpSessionResponse {
  session_id: string;
  requested: boolean;
}

// ConversationEvent gains `| ACPSubagentEvent | ACPSessionMessageEvent | ACPSessionTextEvent`.
export function isACPSubagentEvent(event: BaseEvent): event is ACPSubagentEvent {
  return event.kind === 'ACPSubagentEvent';
}

export function isACPSessionMessageEvent(event: BaseEvent): event is ACPSessionMessageEvent {
  return event.kind === 'ACPSessionMessageEvent';
}

export function isACPSessionTextEvent(event: BaseEvent): event is ACPSessionTextEvent {
  return event.kind === 'ACPSessionTextEvent';
}

// src/client/conversation-client.ts (excerpt)
export class ConversationClient {
  /**
   * Cancel one ACP sub-agent session's current work. 409 when the child did not
   * advertise `cancel` (or no ACP connection is live); the child's next
   * `ACPSubagentEvent` (idle, `cancelled`) confirms it.
   */
  async cancelAcpSession(
    conversationId: string,
    sessionId: string
  ): Promise<CancelAcpSessionResponse> {
    const session = encodeURIComponent(sessionId);
    const response = await this.client.post<CancelAcpSessionResponse>(
      `/api/conversations/${conversationId}/acp/sessions/${session}/cancel`
    );
    return response.data;
  }
}

// src/conversation/remote-conversation.ts (excerpt)
export class RemoteConversation {
  async cancelAcpSession(sessionId: string): Promise<CancelAcpSessionResponse> {
    const session = encodeURIComponent(sessionId);
    const response = await this.client.post<CancelAcpSessionResponse>(
      `/api/conversations/${this.id}/acp/sessions/${session}/cancel`
    );
    return response.data;
  }
}

// src/models/acp.ts: ACP_SETTINGS_KEYS gains 'acp_subagents'.

// (v2, B2) src/models/agent-profile.ts (excerpt)
export interface ACPAgentProfile extends AgentProfileBase {
  /** Persist the ACP agent's sub-agent sessions; absent from older servers. */
  acp_subagents?: boolean;
}
```

### A.7 `tests/fixtures/acp/scripted_agent.py` (S1's additions to S2's script)

The command line S1 adds (S2's flags and `SCRIPTED_ACP_LOG` unchanged, S2 Appendix C):

| Flag | Default | Effect |
|---|---|---|
| `--subagents` | off | play §4.10's sub-agent run on each `session/prompt`, before S2's reply |
| `--cancel-wait SECONDS` | `0` | how long `child-b` waits for `session/cancel` (0: it does not wait) |
| `--transcript PATH` | — | play a JSONL transcript instead of every built-in behaviour |
| *(v2, B8)* `--transcript-interval-ms MS` | `0` | sleep `MS` before each `session/update` the transcript sends |
| `--wait-timeout SECONDS` | `30` | a transcript wait point's limit; past it the script exits non-zero |

*(v2)* As built, S1 adds the functions and classes below to S2's script; `serve` is S2's (B1), shown because S1
calls it for both modes. *(v2.3, V-6: and the eleven wire builders, which both sub-agent test files import; each
returns one ACP update, or for `text` one content block, as JSON. `CONTEXT_WINDOW` is S2's. At Gate C the first
four are in #10, the rest with `--subagents` in #12, and `plan_transcript` to `play_transcript` in #16.)*

```python
DEFAULT_WAIT_TIMEOUT_S: Final[float] = 30.0
ROOT_CELL = "cell-1"


def add_subagent_arguments(parser: argparse.ArgumentParser) -> None:
    """Add --subagents, --cancel-wait, --transcript, --transcript-interval-ms and
    --wait-timeout."""
    ...


async def serve(
    handler: MethodHandler,
    *,
    on_initialize: Callable[[dict[str, Any]], None],
) -> Connection:
    """Serve ``handler`` over stdio through ``acp.connection.Connection``.

    ``handler`` is ``build_agent_router(agent)`` for the built-in behaviours, or
    a ``TranscriptPlayer``'s ``handle``; a tap in front of it passes
    ``initialize``'s raw params to ``on_initialize`` and writes the request log.
    """
    ...


def advertises_subagents(initialize_params: dict[str, Any]) -> bool:
    """Whether the client's raw ``initialize`` params advertise ``subagents``."""
    ...


# (v2.3, V-6) Wire updates, as an ACP agent sends them.
def text(value: str) -> dict[str, Any]: ...


def subagent(
    child: str,
    **fields: Any,
) -> dict[str, Any]: ...


def announce(
    child: str,
    *,
    cell: str | None = ROOT_CELL,
    cancel: bool = True,
    **fields: Any,
) -> dict[str, Any]: ...


def idle(
    child: str,
    stop_reason: str = "end_turn",
) -> dict[str, Any]: ...


def tool_call(
    call_id: str,
    **fields: Any,
) -> dict[str, Any]: ...


def tool_done(
    call_id: str,
    status: str = "completed",
    **fields: Any,
) -> dict[str, Any]: ...


def thought(value: str) -> dict[str, Any]: ...


def said(value: str) -> dict[str, Any]: ...


def usage(
    cost: float | None = None,
    size: int = CONTEXT_WINDOW,
) -> dict[str, Any]: ...


def message(
    message_id: str,
    sender: str,
    recipient: str,
    value: str,
    **fields: Any,
) -> dict[str, Any]: ...


def message_chunk(
    message_id: str,
    sender: str,
    recipient: str,
    value: str,
) -> dict[str, Any]: ...


async def play_subagent_run(
    conn: Connection,
    root_session_id: str,
    *,
    advertised: bool,
    cancel_wait_s: float,
    cancelled: asyncio.Event,
) -> None:
    """Send §4.10's generic sub-agent run as raw session/update notifications;
    only the root's lines when the client did not advertise ``subagents``."""
    ...


@dataclass(frozen=True)
class _Wait:
    """Wait for the client's next ``method`` (for session/cancel, naming
    ``session_id``); ``recorded_id`` is the recorded request's id."""

    method: str
    session_id: str | None
    recorded_id: Any


@dataclass(frozen=True)
class _Respond:
    recorded_id: Any
    message: dict[str, Any]


@dataclass(frozen=True)
class _Notify:
    params: dict[str, Any]


def plan_transcript(
    lines: Sequence[dict[str, Any]],
) -> list[_Wait | _Respond | _Notify]:
    """Turn transcript lines into the player's steps (``TranscriptPlayer``)."""
    ...


class TranscriptPlayer:
    """Plays one JSONL transcript over one connection (§4.10's rules)."""

    advertised: bool

    def __init__(
        self,
        transcript: Sequence[dict[str, Any]],
        *,
        wait_timeout_s: float = DEFAULT_WAIT_TIMEOUT_S,
        interval_s: float = 0.0,
    ) -> None: ...

    def on_initialize(self, params: dict[str, Any]) -> None:
        """Record whether the client advertised ``subagents``."""
        ...

    async def handle(
        self,
        method: str,
        params: Any,
        is_notification: bool,
    ) -> Any:
        """The connection's handler: match a client message to a wait point."""
        ...

    async def play(self, conn: Connection) -> None:
        """Walk the transcript once; raise TimeoutError at a missed wait point."""
        ...


def load_transcript(path: Path) -> list[dict[str, Any]]: ...


async def play_transcript(args: argparse.Namespace) -> None:
    """Serve a ``TranscriptPlayer`` and play it until the client disconnects."""
    ...
```
