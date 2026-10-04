# S2 · Agent commands, options and App panels in the agent-server: design

**TASK-6** · System Designer · task branch `feat/agent-surfaces` in
[michaeltheologitis/software-agent-sdk](https://github.com/michaeltheologitis/software-agent-sdk),
cut from its `deep-reasoning` branch · against the approved spec
[TASK-1](https://app.notion.com/p/3ed62fb22237814ab425c81b3844f012) (S2 in full; §2's decisions,
interfaces and pins; C2 and D3, which consume S2; D1's slash-command and namespace bullets; §4's E11
and testing layers).
**Pinned against:** SDK fork `deep-reasoning` at `91430aa` (upstream `main` at `53a4bc5` plus the ASE
commit, which touches only `AGENTS.md` and `CLAUDE.md`, so every line number below is upstream's) ·
`agent-client-protocol` 0.12.1 (the fork's lock) · D1's design at deep-reasoning `f281109`
(`docs/design/d1-dr-acp.md` §5, the ACP contract S2 forwards) · Canvas fork `deep-reasoning` at
`02b7ac7` (`1ff45c2` plus its ASE commit).

**Matches the code at `d938c90`** (v2.5): the head of `feat/agent-surfaces`, which is `7f03b56` plus
two commits that add only tests, `76533fc` and `d938c90` (the refactor section's v2.5 note). Its tree
is the tree of the Gate C stack's top, #9 (the Gate C section, next after the reading guide). The
draft pull request #1, which held the whole branch, was closed on 2026-10-04 as superseded by that
stack. v2.5 is committed on `design/s2` and changes only this file.

**The branch at `7f03b56`** (v2.4, after the literate refactor): `feat/agent-surfaces` in the
draft pull request [michaeltheologitis/software-agent-sdk#1](https://github.com/michaeltheologitis/software-agent-sdk/pull/1)
against the fork's `deep-reasoning` (head `1f2b52d`). The branch holds 38 commits that
`deep-reasoning` lacks. Sixteen are S2's build, grouped as the three PRs: PR 1 `28ca2e1`, `c3d1db8`,
`d0d3fe1`, `5252840`, `e2ec3a9`, `4027912`, `00a5310`, `5e3317f`; PR 2 `132db0f`, `8523177`,
`13e5904`; PR 3 `759ffb2`, `1d2627b`, `28e5654`, `0e24793`, `6f97bf3`. Twenty are the literate
refactor, `5236485` to `7f03b56`, which change no behaviour (the refactor section, below). The
other two merge `deep-reasoning`'s fork-only CI commits and bring nothing else: `aff05f6`
(`ea51b3f`, the runners, §3.2 B17) and `c12f7b4` (`1f2b52d`, upstream's main-only guards on pull
requests into the fork's branches, B25). So `git diff 1f2b52d..7f03b56` is S2 alone. Gate B
approved v2.3, which matched `5e3317f`, the head before the refactor. S1
(`feat/acp-subagent-sessions`, `a3279be`) contains `5e3317f`; S1's own refactor, in progress, is
on `7f03b56`. Line numbers cited from the built code are at `6f97bf3` unless a commit is named;
v1's are upstream's, as before.

**Revisions** (newest first; the Gate B reader approved the previous one, so each line says which
sentences to stop trusting):
- 2026-10-04 · v2.5 · read beside S2's Gate C stack, on the Conductor's request, so that the
  reviewer of each PR knows which sections to read. Since v2.4: two commits that add only tests,
  `76533fc` and `d938c90`, on code that is `7f03b56`'s; and the PR split, seven draft PRs, #3 to #9,
  whose top has `d938c90`'s tree; PR #1 is closed as superseded. No design decision changes. Stop
  trusting: the header's "matches the build at `7f03b56`" and PR #1 as S2's open draft (now
  `d938c90` and the stack); the reading guide's "a reading table for Gate C follows the PR split"
  (it is the Gate C section); "its three pull requests" where this file lives (seven levels); §1's
  "cherry-picked onto the fork's `main` as its own upstream PR", B18's reading that the drafts onto
  `main` come with the PR split, and §9 layer 3's per-PR drafts onto `main` (the stack is based on
  `deep-reasoning`, and nothing goes upstream); in the refactor section, the first and fourth items
  of "what no test asserts any more" (the agent's live refusal of `""` and `"model"`, the set
  route's 422 for `""`, a tab's default path and the three `min_length` rules are asserted again),
  the property tables' names `test_the_model_option_and_an_empty_id_are_refused_in_the_field` and
  `test_a_set_that_is_not_for_this_route_is_a_bad_request` and their *Gone* notes for those
  properties, and the counts (111 cases: PR 1 68, PR 2 29); the same names and counts in §4.5's
  v2.4 note and in §4.10's and §5.3's tables (`test_acp_router.py` 27 cases → 28, the panel
  manifest's 16 → 20, PR 1 68 → 69, PR 2 29 → 33, 111 → 116). Still unasserted:
  `LocalConversation.set_acp_config_option`'s refusal of `""`, pinned only by the field test,
  through the check both call. Added: the Gate C section (each PR's contents, lines and sections to
  read beside it, checked against this numbering, which v2.4 did not change; the refactor's R items
  per PR; the two places the PR Splitter flagged); the test commits and their evidence in the
  refactor section; notes in §1, §3.1 item 12, B18, §9 layer 3, §10 items 9 and 10, and the size
  paragraph. The Gate B section is unchanged; its test names are those of `5e3317f`.
- 2026-10-04 · v2.4 · brought in line with the literate refactor, `7f03b56`, on the Conductor's
  request, so that Gate C's reviewers read a design that names the code as it now is. Gate B
  approved v2.3; nothing the refactor did changes behaviour. Stop trusting: the header's commit list
  and `git diff` range; §1's and B16's "PR 3 applies only after PR 2" and their five shared files
  (four now, and each PR applies alone, R10); §4.4's "refused by the request's validator", the
  agent's "whose validator refuses" and the fold's "repeated explicitly" (R1); §4.10's, §5.3's and
  §6.3's test tables (now at `7f03b56`); A.3's and A.5's `_reject_model_config_option` (R1), A.3's
  bridge without `_store_session_controls` (R2), A.6's list of error codes, A.7's `_resolve_launch`
  docstring, A.8's `_validate_id` validators and `resolve_package_file` docstring (R5, R6), and
  A.9's `_is_loopback_host` (R8); and the Gate B section's evidence, property tables and size as an
  account of the code now (they describe `5e3317f`). Corrected: v2.1's and v2.2's count of
  `test_acp_router.py`'s tests, one too many (17 at `6f97bf3`, 21 at `5e3317f`; the case counts were
  right). Moved: these revision lines, the file's location and the reading guide, from the end of
  the Gate B section to above the refactor section; the guide's first sentence follows the move, and
  the guide gains a v2.4 note. Added: the refactor section (R1 to R10, the Scout's cuts as ruled,
  the evidence at `7f03b56`, what no test asserts any more, the property tables, the size before and
  after); the Gate B section's banner; notes in B1, B2, B6, B12, B15, B16, B19, §1, §3.1 item 12,
  §4.2, §4.4, §4.5, §4.9, §6.1, §8, §9, §10 items 9 and 10, Appendix A's preface and Appendix C. The
  Gate B section is otherwise as approved. Appendix A keeps one field and one parameter per line, so
  its layout differs from the code where R3 and R6 joined short signatures; every Python block
  parses and passes `ruff format --check` at 88 columns.
- 2026-10-03 · v2.3 · the REST breakage check re-run against `v1.50.1`, on the Conductor's request:
  Michael pushed upstream's tag to the fork, and attempt 2 of run 37146974332 on PR #1 at `5e3317f`
  ran oasdiff and passed. Stop trusting v2.2's "the REST breakage check ran without its oasdiff
  comparison" (the Gate B section, §4.9's REST row). Added: oasdiff's findings under §4.9's table;
  notes in B14, §6.4 and §10 items 5 and 11. The build and every reading of its code are unchanged.
- 2026-10-03 · v2.2 · brought in line with `5e3317f` (`13e5904`, `5e3317f`, and the fork-only
  `1f2b52d` merged as `c12f7b4`), on the Conductor's request; the Gate B evidence is now PR #1's CI
  and the live run at `5e3317f`. Stop trusting: the header's commit list and `git diff` range; the
  Gate B evidence, size and "not pinned" paragraphs (rewritten); v2's claim that the weak-schema
  ratchet runs in agent-server-tests (B23); §4.7's "`detail` names why" for a 502, and every 5xx body
  there (B26); §4.9's "Ran" column; §4.10's router row and counts; §10 items 11, 12, 14 and 16 (now
  resolved, ruled or pinned); Appendix A.8's icon route decorator; Appendix C's flags. Added: B23 to
  B26; notes in B4, B16, B18, B19, B20, §3.1 item 12, §5.2, §5.3, §7 item 2 and §9.
- 2026-10-03 · v2.1 · reconciled with S2's as-built document (`as_built/s2-agent-surfaces.md`,
  `3ad786c`), on the Conductor's request. Stop trusting v2's B4 and its note in §7 item 4 ("an event
  with empty lists means the agent offers nothing"): after a start or a resume the first event can
  carry an empty `available_commands` that the agent's menu then replaces, and nothing in the event
  says which it is (re-measured with the scripted agent; B4 rewritten; §10 item 14 for the
  Conductor). Added without changing other sentences: B3's note that the set route has no Docker
  check; B20 to B22, the as-built's findings v2 lacked (the -32603 500 carries the agent's message
  unmasked; a start value for a built-in provider's session mode is overwritten; and, correcting the
  as-built, the macOS failures behind B12 and B13 are in CI's history); the as-built's re-runs of the persisted-settings guard
  and the TypeScript suite, and every main-only workflow by name, in the Gate B evidence and B18;
  test counts as cases in §4.10, §5.3 and §6.3; notes in §4.4, §4.6, §7 item 6, §8 item 14 and §9;
  §10 items 14 to 16.
- 2026-10-03 · v2 · brought in line with the build at `6f97bf3`, after Proof Green. Stop trusting:
  §1's order-and-independence paragraph (built PR 1 first; five shared files; PR 3 applies only after
  PR 2, B16); §2 decision I's "no guard is weakened" (B14); §4.1's normalization rules (B1); §4.2's
  bare callback and §4.3's "created on first use" (B5, B6); §4.6's `shutil.rmtree` (B7); §4.7's
  events-search row and the preview's errors (B2, B3); §4.8's search query and the audit entry's
  tracking link (B2, B10); §4.10's, §5.3's and §6.3's test lists (now as built); §6.1's
  process-group paragraph and websockets item (B12, B15); §6.4 (B14); §7 items 2, 4 and 5 (B3, B2,
  B4); §9's built-in providers, the dr-acp job and layer 3 (B8, B18); Appendix A.1, A.3, A.4, A.6,
  A.7, A.8 and A.9 and Appendix B where a signature changed; Appendix C (B9). Added without changing
  earlier sentences: this Gate B section; §3.1's note that the ten items hold, and items 11 and 12;
  §3.2; §4.1's note on null fields (B2); §4.9's column of where each guard ran (B18); §8's
  confirmation from S1's head; §10's resolutions and items 9 to 13. Every signature block is valid
  code with one field and one parameter per line (checked: each Python block parses and passes
  `ruff format --check` at the fork's 88 columns; each TypeScript block parses). Every change is
  listed, with its reason, in §3.2.
- 2026-10-02 · v1 · first full-depth version.

**Where this file lives, and why nothing trips over it.** `docs/design/` on deep-reasoning's
`design/s2` branch. That branch holds only documents: no docs site, no `pyproject.toml`, no test
runner, no package, so nothing collects, builds or ships this file. No design document goes into the
fork: its three pull requests carry code and tests only, in upstream's layout. The PR split leaves
this file behind. *(v2.5: the split made seven pull requests, #3 to #9, and neither this file nor
the as-built document, `as_built/s2-agent-surfaces.md` on this same branch, is in any of them.)*

**Reading guide.** Gate B: the Gate B section, below the refactor section. §3.1 lists every
departure from the approved spec, §3.2 every change the build made. C2's designer: §7 is the
contract C2 builds against. S1's designer and the Conductor: §8 names every place S1 and S2 touch
the same code. The PR splitter: §1's order and independence, §3.2 B16 to B18. The Implementer, the
Cartographer and the Refactorer read everything; Appendix A (Python) and Appendix B (TypeScript) are
the signature reference, and Appendix C is the test agent's behaviour. *(v2.4)* Gate C's reviewers:
the refactor section below says what changed since Gate B and which tests carry each property now;
§4 to §6 and Appendix A name the code at `7f03b56`. The Gate B section is history. The PR splitter:
also R10. *(v2.5)* Gate C's reviewers start at the Gate C section, next: which PR holds what, and
which sections to read beside each.

## Gate C: reading beside the PRs (v2.5)

The code is read as a stack of seven semantic PRs, tests included; this doc is the reference beside
them. Where the two differ, that is a finding to raise, not a reading to choose. The stack is open in
michaeltheologitis/software-agent-sdk as draft PRs, bottom-up, each based on the one above it in the
table (2026-10-04). They are internal drafts inside the fork: the bottom one, #3, is based on the
fork's `deep-reasoning` (`1f2b52d`), and nothing in the stack goes to `main` or upstream. So the
fork-only merges `aff05f6` and `c12f7b4`, with `ea51b3f` and `1f2b52d`, stay behind (B17, B25), and
§1's "cherry-picked onto the fork's `main` as its own upstream PR" is a step not taken. Each level was
cut from the net diff `1f2b52d...7f03b56` as one commit; the two test commits that followed were
added on #4, #6 and #8 and merged upward, so the top, #9, has `d938c90`'s tree exactly. Every level's
checks are green (the only skips are upstream's "Validate PR description" on a draft; #4 needed one
re-run of upstream's stress test). This doc and the as-built document
(`as_built/s2-agent-surfaces.md`, the Cartographer's) are both on deep-reasoning's `design/s2`, and
neither is in any PR. Review comments and their status are in the Conductor's
[review ledger](https://app.notion.com/p/3ef62fb22237815b89a1cdb6470aef98).

**This doc's three PRs are the stack's three ideas.** PR 3 (App backends on macOS) is #3, PR 2
(header panels) is #4, and PR 1 (ACP session controls) is cut into five levels, #5 to #9. So the
stack runs in v1's order (§1), and wherever this doc says PR 1, read #5 to #9. "PR #1" in the Gate B
section and in the refactor section's evidence is the single draft, now closed.

| Level | PR | What it holds | Lines added (removed) | Read beside |
|---|---|---|---|---|
| 1 | [#3](https://github.com/michaeltheologitis/software-agent-sdk/pull/3) run App backends on macOS (PR 3) | `backend.py` (the platform tables, the loopback health probe, EPERM on macOS), `proxy.py` (loopback never proxied), `BackendPlatform`'s darwin keys, the REST check's pattern, the `macos-app-backend-tests` job; the backend, bridge and REST-check tests | 363 (29): 104 of code and CI, 259 of tests | §6 (6.1 to 6.4), decision G, §3.2 B12 to B15 and B22, A.9; *v2.5:* decision I (B14's narrowing), R8, R9 |
| 2 | [#4](https://github.com/michaeltheologitis/software-agent-sdk/pull/4) let an App declare conversation header panels (PR 2) | `manifest.py` (`ContributionId`, the panel and tab models, one id namespace, `resolve_package_file`, `resolve_panel_icon`), `installed.py`'s install check and icon path, the icon route, `canvas_conversation_panels_v1`; the manifest, containment, router and OpenAPI tests | 533 (19): 218, 315 | §5 (5.1 to 5.3), decisions F and H, B11, B23, A.8; *v2.5:* R5 to R7 |
| 3 | [#5](https://github.com/michaeltheologitis/software-agent-sdk/pull/5) persist the commands and options an ACP agent reports, as one event (PR 1) | the DTOs in `acp_models.py`, `ACPSessionControlsEvent`, the bridge's recording and the agent's publishing in `acp_agent.py`, `LocalConversation`'s out-of-turn emitter and `_replace_acp_agent`, the visualizer entry; the scripted ACP agent, the shared fixtures in `tests/conftest.py`, and the models, event, publishing and emitter tests | 1,346 (25): 449, 897 (310 the scripted agent, 63 the shared fixtures) | §4.1 to §4.3, decisions A and B, B1, B4 to B6, B9, B10, §8, A.1, A.2, A.3 and A.4 (their recording and publishing parts), Appendix C; *v2.5:* R2, R4 |
| 4 | [#6](https://github.com/michaeltheologitis/software-agent-sdk/pull/6) apply ACP config option values at the start or on a live session (PR 1) | `ACPConfigOptionValues`, `ACPAgent.acp_config_options` and their application after `session/new`, `ACPConfigOptionRejectedError` and its error code, `ACPAgent.set_acp_config_option` and `LocalConversation.set_acp_config_option`; their tests, the field test and the swap test among them | 480 (7): 169, 311 | §4.4 (the agent, applying, a refusal), §4.5 (the agent's and the conversation's calls), decisions C and E, B21, A.3 and A.4 (their option-value parts); *v2.5:* §4.3's agent swap, R1 |
| 5 | [#7](https://github.com/michaeltheologitis/software-agent-sdk/pull/7) preview what an ACP agent offers before a conversation exists (PR 1) | `acp_preview.py`, `ACPAgent.wait_for_available_commands` and `close_acp_session`, the bridge's commands-reported flag; the preview tests, the live tier and its line in `acp-live-tests` | 438: 130 of code, the job's 2, 306 of tests (172 the live tier) | §4.6 (the SDK's `preview_acp_session`), §9, decision D, B7, B8, A.6; *v2.5:* §4.2's commands-reported flag, A.3's preview parts (`_ACP_SESSION_CLOSE_TIMEOUT`, `_supports_session_close`, both `wait_for_available_commands`, `close_acp_session`), §8 item 4, R3 |
| 6 | [#8](https://github.com/michaeltheologitis/software-agent-sdk/pull/8) serve ACP session controls over REST (PR 1) | `acp_router.py` (the preview and set routes), `ConversationService._resolve_launch` (the start's block moved verbatim, plus the fold) and `preview_acp_session`, `EventService.set_acp_config_option`, `StartConversationRequest.acp_config_options`, `acp_session_controls_v1`; the router tests | 842 (86): 349 (84 the moved block, whose old 84 lines are the removed side), 493 | §4.7, §4.9, §7, §8, decisions C, D and H, B2, B3, B20, B24, B26, A.5, A.7; *v2.5:* §4.4's request and fold, §4.5's `EventService` and route, §4.6's shared resolution and `ConversationService.preview_acp_session`, R1, R3 |
| 7 | [#9](https://github.com/michaeltheologitis/software-agent-sdk/pull/9) preview, set and read ACP session controls in the TypeScript client (PR 1) | `src/models/acp-session-controls.ts`, the event type and its guard, `ConversationClient`'s and `RemoteConversation`'s calls, `CreateConversationPayload.acp_config_options`, the endpoint-audit entry; the client's tests | 346 (2): 200, 146 | §4.8, §7, Appendix B, B2, B10; *v2.5:* R4 (`1118139`) |

Lines are each PR's own diff against its base, split into tests (`tests/` and the TypeScript
`__tests__/`) and the rest. They sum to 4,348 added and 168 removed, about 14.5 h at ≈300 lines an
hour; the net diff `1f2b52d..d938c90` is 4,343 and 163, because #6 rewrites five lines of a test file
#5 adds. Code and CI are 1,621 lines, as at `7f03b56`.

The sections the PR Splitter listed for each PR were given against v2.3's numbering; they hold in
v2.4's and this one's, which renumber nothing (v2.4 added the refactor section, R1 to R10, beside
the numbered ones). The entries marked *v2.5* add the refactor's R items, which v2.3 did not have,
and sections that describe a level's code but were missing from its list. The levels cut PR 1
across §4.4 to §4.6 and Appendix A.3, so those sections are read in parts, as named.

**Two places to read with care** (both flagged by the PR Splitter):

- **`test_the_agent_swap_hands_publishing_to_the_copy` sits in #6, one level above the code it pins
  in #5.** #5 moves the agent swap into `_replace_acp_agent`, which now also rebinds publishing to
  the copy (§4.3, "The agent swap"); the test drives the swap through `set_acp_config_option`, which
  #6 adds, so it lands there. A reviewer of #5 reads the hand-over with no test beside it; the test
  is in #6's `test_local_conversation_acp_config_option.py`, and the property table lists it under
  decision B.
- **#5 is large**: 1,346 lines added, about 4.5 h, nearly a third of the stack. 449 are code; of the
  897 of tests, 310 are the scripted ACP agent (Appendix C, a real ACP process that also answers the
  `session/set_config_option` and `session/close` calls #6 and #7 use) and 63 the fixtures in
  `tests/conftest.py` that the later levels share. Read §4.1 to §4.3 first, in that order: the data,
  the recording, then publishing and its invariant.

**For any PR:** its tests, file by file, are §4.10 (PR 1), §5.3 (PR 2) and §6.3 (PR 3); which test
carries which property, each named for it, is the refactor section's property tables, at `d938c90`;
what changed since Gate B, each change with its reason, is the refactor section (R1 to R10, then the
two test commits).

| Module | Section |
|---|---|
| `canvas_extensions/backend.py`, `docker_runtime/proxy.py`, the REST check, the macOS job | §6.1, §6.4, A.9 |
| `canvas_extensions/manifest.py`, `installed.py`, `canvas_extensions_router.py` | §5.1, §5.2, A.8 (`BackendPlatform`, §6.1) |
| `sdk/agent/acp_models.py`, `sdk/event/acp_session_controls.py` | §4.1, A.1, A.2 |
| `sdk/agent/acp_agent.py` | the bridge §4.2, publishing §4.3, option values §4.4 and §4.5, the preview's waits §4.6; A.3 |
| `sdk/conversation/impl/local_conversation.py` | the emitter and the swap §4.3, the set §4.5; A.4 |
| `sdk/conversation/acp_preview.py` | §4.6, A.6 |
| `sdk/conversation/request.py`, `agent_server/acp_router.py`, `conversation_service.py`, `event_service.py`, `api.py`, `conversation_router.py`, `server_details_router.py` | §4.4 to §4.7, A.5, A.7; the capabilities, decision H; the contract C2 builds against, §7 |
| `clients/typescript/` | §4.8, Appendix B, §7 |
| `tests/fixtures/acp/scripted_agent.py` | Appendix C, B9 |

## The literate refactor, after Gate B (v2.4)

After Gate B approved v2.3, the Scout proposed four cuts and the Refactorer made the branch worth
reading, in twenty commits, `5236485` to `7f03b56`, in three units that follow the three PRs.
**None changes behaviour**: no route, status code, message, default or persisted shape changes, and
the agent-server's OpenAPI export at `7f03b56` is byte for byte the export at `5e3317f` (both
exported for this revision, where the weak-schema check also passes at both, 62 allowlisted
locations). The code commits merge duplicates, inline one helper and reword docstrings; the test
commits remove, merge or reshape tests. Sections 1 to 10 and the appendices now name the code at
`7f03b56`; where a symbol moved, the text says so, marked *(v2.4, Rn)*.

**The evidence at `7f03b56`.**

- **CI**, PR #1's checks: 28 check runs, all green but upstream's "Validate PR description"
  (skipped on a draft).
  - Upstream's `tests.yml`, [run 37161720972](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37161720972),
    attempt 2: **sdk-tests** 6,683 passed, 7 skipped, 12 xfailed; **agent-server-tests** 2,412
    passed; **cross-tests** 496 passed, 1 skipped; **macos-app-backend-tests** 164 passed;
    **acp-live-tests** 25 passed, 2 skipped; and windows-tests, tools-tests, workspace-tests,
    agent-server-stress-tests, Test directory allowlist and coverage-report. Against `5e3317f`
    (6,699, 2,431 and 178) the counts fall by exactly the cases the refactor removed: 16 in the SDK
    suite, 19 in the agent-server suite, 14 of those in the macOS job's directory. Attempt 1's
    agent-server-tests failed one test, upstream's
    `tests/agent_server/telemetry/test_telemetry_sink.py::test_emit_never_awaits_even_when_the_exporter_hangs`
    (`emit() blocked for 0.557s`, against a 0.05 s allowance), while another worker on the same
    2-core runner ran the canvas-extension bridge tests; the refactor touches nothing on that path,
    and the re-run passed
    ([the evidence, on PR #1](https://github.com/michaeltheologitis/software-agent-sdk/pull/1#issuecomment-5974774800)).
  - The guards upstream runs only for pull requests to `main` (B25), all at attempt 1: **TypeScript
    client CI** ([37161720995](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37161720995): lint with 7 warnings and no errors, 23 files and **354
    tests**, S2's 7 among them), its integration tests ([37161721026](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37161721026)), Persisted settings
    ([37161720978](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37161720978)), **REST API breakage** ([37161721016](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37161721016): oasdiff 1.19.1 against
    `v1.50.1` reports the same eight additive changes §4.9 lists, and passes) and the Version bump
    guard ([37161720984](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37161720984); its SDK API check still skipped, no version changed). Also green:
    Pre-commit ([37161720999](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37161720999)), Check Docstrings ([37161721012](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37161721012)), Deprecation deadlines
    ([37161721001](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37161721001)) and the endpoint audit ([37161720973](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37161720973)).
  - Not in CI (B23), run for this revision: the OpenAPI export and the weak-schema check, the two
    Python steps of `make test-server-schema`, at `5e3317f` and `7f03b56`, as above.
- **Live tier**, deep-reasoning's `fork-live.yml` on `ci/fork-live` (`a8154e2`),
  [run 37163413911](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37163413911), dispatched with `sdk_ref` `7f03b56`, S2's step only:
  `tests/sdk/agent/test_acp_session_controls_live.py`, **8 passed in 97 s**, the six provider
  previews and the two dr-acp tests (`{"namespace": "root"}`, the cleared-commands flag); three
  warnings, all `PytestUnraisableExceptionWarning` from a subprocess transport, as before.

**After the refactor: two test commits, `7f03b56..d938c90`** (v2.5). They assert again most of the
first item of "what no test asserts any more", below, and all of its fourth (the as-built r4's §5
items 1, 9 and 10, and the `min_length` part of its item 2), and change only test files. Each was
mutation-checked.

- `76533fc` pins `ACPAgent.set_acp_config_option`'s refusal of `""` and `"model"`, with its
  sentence, on a live session: the field test is now
  `test_the_model_option_and_an_empty_id_are_refused_in_the_field_and_by_a_live_set[model, '']`
  (in #6). It pins the set route's 422 for an empty `config_id` (`ACPConfigOptionSetRequest`'s
  `min_length=1`): the router's refusal table is now
  `test_a_set_that_is_not_for_this_route_is_refused[not-acp, model-option, empty-id]` (400, 400,
  422; in #8).
- `d938c90` adds four rows to `test_a_malformed_panel_makes_the_manifest_invalid` (in #4):
  `panel-title`, `no-tabs` and `tab-title` (the three `min_length` rules), and
  `duplicate-default-tab-path`, a tab with no path beside a tab at `/`, which collide only because the
  default is `/`, so it pins the default.
- Cases: `test_acp_router.py` 27 → 28, the panel manifest's 16 → 20; PR 1 68 → 69, PR 2 29 → 33,
  PR 3 14; 111 → 116 in all.
- **CI at `d938c90`**, upstream's `tests.yml` on PR #1 before it closed,
  [run 37167747319](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37167747319):
  sdk-tests 6,683 passed, 7 skipped, 12 xfailed (unchanged: the field test keeps its two cases);
  agent-server-tests 2,417 (2,412 and the five new cases); macos-app-backend-tests 168 (164 and the
  four manifest rows); cross-tests 496 passed, 1 skipped; acp-live-tests 25 passed, 2 skipped. The
  main-only guards ran on the same push, all green. The live tier was not re-run: neither commit
  touches the code or the live file, so run 37163413911 at `7f03b56` stands.

**Changed by the refactor.** Each item names its commits; none changes behaviour.

*Session controls (PR 1)*

- **R1** `5236485` · **`ACPConfigOptionValues`**, an annotated type in `acp_agent.py`
  (`dict[str, str | bool]` with an `AfterValidator` that runs `_check_config_option_id` on every
  key), types both `ACPAgent.acp_config_options` and `StartConversationRequest.acp_config_options`.
  It replaces the two `_reject_model_config_option` field validators, `request.py`'s import of the
  private `_check_config_option_id`, and the re-check in `_resolve_launch` after its `model_copy`:
  both dicts the fold merges were validated when their models were built, and nothing in between
  changes them. The validation error's location and message are unchanged (the commit). §4.4, A.3,
  A.5, A.7.
- **R2** `6907f85` · **`_OpenHandsACPBridge._store_session_controls(session_id, field, entries)`**
  holds the parse-mask-replace steps that `record_available_commands` and `record_config_options`
  repeated: it masks the entries as dumped and replaces the session's snapshot with a validated
  copy. Each record still sets its own state and notifies, in the same order, and the stored
  snapshots compare equal to before. §4.2, A.3.
- **R3** `aa7bcdd`, `f8304e3` · docstrings and comments say what a piece does, not who calls it
  (`ACPPreviewError` no longer lists the codes of `_classify_acp_init_error`, which would drift
  from it; `_resolve_launch` "Resolve[s] the request's agent as its launch will run it"); and the
  short signatures, fields and calls S2 added take ruff's one-line form. No docstring changed here
  reaches the OpenAPI schema. A.3, A.6, A.7.
- **R4** tests · `0d21d58` drops 19 cases whose property another test pins; `920b0e3` drops two
  more that the router tests cover end to end; `cd5db00` moves `wait_until`, `controls_events` and
  a `scripted_conversation` fixture into `tests/conftest.py`, replacing four, three and three
  copies; `f5628cc` answers the faked `session/set_config_option` with ACP's
  `SetSessionConfigOptionResponse` instead of `SimpleNamespace`; `d91a22c` trims the
  session-control harness; `1118139` moves the TypeScript client's empty-page assertion into the
  helper's own test; `671979a` formats. §4.10.

*Header panels (PR 2)*

- **R5** `0e8421c` · **`ContributionId`**,
  `Annotated[str, AfterValidator(_validate_contribution_id)]` in `manifest.py`, types the `id` of
  pages, panels and tabs, replacing three `_validate_id` validators, one of them upstream's own on
  `CanvasExtensionPage` (whose body S2 had already moved into `_validate_contribution_id`). So S2
  now removes 163 upstream lines, not 155: that validator's shell and the page's `id` line (five),
  and three import lines that R5 and R1 extend (two in `manifest.py`, one in `acp_agent.py`).
  Messages, locations and the OpenAPI export are unchanged. §5.1, A.8.
- **R6** `f29a3cc`, `547dfe7` · `resolve_package_file`'s docstring no longer lists its callers; the
  one-line form, as in R3. A.8.
- **R7** tests · `44dd4f4` drops six panel-manifest cases that assert a `Field` declaration, an
  upstream rule, or a dump the router test compares in full; `9e92cb2` folds the icon route's three
  404s into one table and drops `test_a_contained_panel_icon_resolves`; `7f03b56` formats. §5.3.

*App backends on macOS (PR 3)*

- **R8** `46664eb` · **`_is_loopback_host` is inlined** (A.9 in v2.3): `proxy_http` and
  `bridge_websocket` test `urlsplit(…).hostname` against `_LOOPBACK_HOSTS` themselves. §6.1, A.9.
- **R9** tests · `c4a246a` drops the manifest's two backend-platform tests, so PR 3 no longer
  touches `test_canvas_extensions_manifest.py` (R10); `79e77d0` adds a `_prepared_backend` helper
  for the three backend tests that repeated its steps, keeps seven platform rows of ten (one per
  mapping entry and per unknown branch), and merges the two EPERM tests into one that asserts both
  sides. §6.3.

**R10 · Each PR now applies alone** (§1, B16). Without the two platform tests, PR 3 shares no test
file with PR 2. Checked for this revision on the net diff, `1f2b52d..7f03b56`, split into the three
PRs hunk by hunk and applied with `git apply --check` to upstream's `main` (`53a4bc5`): each applies
alone, with 3,433, 523 and 363 lines added. PR 3 needs upstream's runner name,
`blacksmith-2vcpu-ubuntu-2404`, in one context line of its `tests.yml` hunk, where the fork has
`ubuntu-24.04` (`ea51b3f`, B17); a cherry-pick's three-way merge supplies it. The PRs still share
four files: `manifest.py` (PR 2's classes, PR 3's `BackendPlatform` line),
`server_details_router.py` (PR 1's and PR 2's capability strings), `tests.yml` (PR 1's line in
`acp-live-tests`, PR 3's macOS job) and `tests/agent_server/canvas_extensions/conftest.py` (PR 2's
`write_extension` argument, PR 3's `dead_http_proxy` and its `import socket`). This checks the net
diff, not the PR Splitter's commits, which are its own to check.

**The Scout's cuts, as the Conductor ruled.** Cut 1, shared `Annotated` validators: adopted, R1 and
R5. Cut 2, dropping the public `config_id` and `value` of `ACPConfigOptionRejectedError` and
`detail` of `ACPPreviewError`: rejected, as approved API; `0d21d58` now asserts `config_id` and
`value`, in `test_a_live_set_is_persisted_and_survives_a_reload`. Cut 3, serving the scripted agent
through `acp.run_agent`: rejected, because S1's fixture needs its `serve()` tap (Appendix C
unchanged). Cut 4, dropping tests another test or the framework already pins: adopted, as `0d21d58`,
`44dd4f4` and `c4a246a` (27 cases), and the Refactorer dropped or merged 8 more (`920b0e3`,
`9e92cb2`, `79e77d0`). One reading of the Scout's was wrong: `_session_config_options` keeps its
`getattr`, because six of upstream's own tests pass session responses without `config_options`
(spec-limited `MagicMock`s, `None`), not only S2's tests (`f5628cc`; B6 (d)).

**What no test asserts any more.** Each was asserted at Gate B; the code still does each. *(v2.5:
the two test commits above assert most of the first item and all of the fourth again, as marked.)*

- **The SDK-level refusals of `""` and `"model"`** by `ACPAgent.set_acp_config_option` and
  `LocalConversation.set_acp_config_option`. Both still refuse (each calls
  `_check_config_option_id`). *(v2.5: the agent's refusal of both is asserted again, with its
  sentence, in
  `test_the_model_option_and_an_empty_id_are_refused_in_the_field_and_by_a_live_set[model, '']`.)*
  The REST route's 400 for `model` is still asserted
  (`test_a_set_that_is_not_for_this_route_is_refused[model-option]`), and on that path it is
  `LocalConversation`'s check that refuses. The route refuses `""` before that, with a 422 from
  `ACPConfigOptionSetRequest`'s `min_length=1` *(v2.5: asserted again, `[empty-id]`)*. So
  `LocalConversation`'s refusal of `""` is still pinned only by the field test, through the check both
  call: no test calls the conversation with `""`. The type's refusal of both is asserted on
  `ACPAgent`, and the start route's 422 for `model`; the preview route's 422 for `model` is not (it
  takes the same model, `StartConversationRequest`).
- **That a start and a preview of one request resolve the same agent, field for field.**
  `test_resolve_launch_gives_the_start_and_the_preview_the_same_agent` compared `_resolve_launch`'s
  agent with the started conversation's `base_state.json`, for each way of naming the agent; it
  went in `0d21d58` as a test of a private method (the fork's AGENTS.md: assert observable
  behaviour, not private helpers). That sameness now rests on both routes calling `_resolve_launch`,
  read in the code; falsifier 2 is carried as the table below says.
- **That `set_acp_config_option`'s timeout names the option**: the router's 504 test asserts the
  status only.
- **A tab's default path `/`, and the `min_length` of a panel's title, of its tabs and of a tab's
  title**: `Field` declarations, untested. *(v2.5: all four asserted again, `d938c90`: the
  malformed-panel table's `duplicate-default-tab-path`, `panel-title`, `no-tabs` and `tab-title`
  rows.)*
- **An unknown backend platform key is refused**: the `BackendPlatform` `Literal` does it, untested.
- **The preview's error code for a process that cannot be spawned** (`ACPSpawnError`): the router's
  `spawn-error` case asserts the 502 it maps to.
- Left to upstream's code and tests: a page refused at `/` (upstream's
  `test_invalid_page_path_rejected` has `"/"` among its cases), and the resume transcript skipping
  the event (`render_resume_transcript` renders only message, ACP tool-call and action events).

**Which tests carry which property, at `7f03b56`.** Paths are under `tests/` in the fork; `[…]` is
a parametrization; `::` repeats the file named before it. *Gone* names a test the refactor removed,
and what now carries its property. *(v2.5: at `d938c90`, with the two test commits' names and cases;
each change is marked.)*

*PR 1 · ACP session controls*

| Property | Tests |
|---|---|
| **Falsifier 1.** An option set before the first message is the one the run uses | **Live:** `sdk/agent/test_acp_session_controls_live.py::test_the_first_prompt_runs_with_the_chosen_values` (dr-acp: after the first prompt the reported namespace is `root`). Against the scripted agent: `sdk/agent/test_acp_session_controls.py::test_start_values_reach_the_agent_after_session_new_and_before_the_prompt` (the agent's request log: `session/new`, then `session/set_config_option`, then `session/prompt`); `sdk/conversation/local/test_local_conversation_acp_config_option.py::test_a_set_before_the_start_is_persisted_and_applied_at_the_start`; `agent_server/test_acp_router.py::test_a_started_session_reports_the_chosen_value_and_cleared_commands`, `::test_the_start_folds_option_values_into_the_agent_only` (in `base_state.json`, never `meta.json`), `::test_a_set_before_the_start_is_kept_for_it` |
| **Falsifier 2.** The commands a preview lists are those the started session lists | **Live:** `…_live.py::test_the_preview_lists_what_the_started_session_lists` (dr-acp). Against the scripted agent: `sdk/conversation/test_acp_preview.py::test_the_preview_equals_the_started_session_before_its_first_prompt[{}, fast, thorough]` (the preview equals the controls a `LocalConversation` started from the same agent and values persists before its first prompt; it now builds that conversation with the shared `scripted_conversation` fixture); `agent_server/test_acp_router.py::test_the_preview_answers_for_each_way_of_naming_the_agent[agent, agent_settings, agent_profile_id]` (through the route, each way of naming the agent previews `thorough`'s commands and options, and leaves no `preview-*` directory). *Gone:* `agent_server/test_conversation_service.py::test_resolve_launch_gives_the_start_and_the_preview_the_same_agent[3]` (above) |
| **Any ACP agent can be previewed, and the preview leaves nothing behind** | **Live:** `…_live.py::test_a_built_in_provider_can_be_previewed[6 providers]`. `sdk/conversation/test_acp_preview.py::test_session_close_is_sent_when_the_agent_advertises_it`, `::test_session_close_is_not_sent_when_the_agent_does_not_advertise_it`, `::test_an_agent_that_never_reports_commands_is_previewed_after_the_wait`, `::test_the_agent_process_is_gone_afterwards[previewed, refused]`, `::test_a_missing_working_directory_is_previewed_from_an_empty_scratch_directory`; `agent_server/test_acp_router.py::test_the_preview_maps_each_failure_to_its_status[refused-value, startup-timeout, spawn-error, not-acp, values-not-acp]` (each also asserts no `preview-*` directory is left), `::test_the_preview_holds_a_run_slot`, `::test_the_preview_is_unavailable_in_the_docker_runtime`, `::test_the_preview_of_an_unknown_profile_is_not_found`, `::test_the_preview_answers_an_authentication_failure_with_502_not_401`, `::test_the_preview_of_a_profile_with_a_dangling_mcp_reference_is_refused`. *Gone:* the SDK's `test_an_agent_that_cannot_be_spawned_raises_a_spawn_error` (the router's `spawn-error` case, 502) |
| **A value the agent refuses stops the start with the agent's own sentence, and nothing is prompted** | `sdk/agent/test_acp_session_controls.py::test_a_refused_start_value_ends_the_start_and_no_prompt_is_sent` (`ConversationErrorEvent` code `ACPConfigOptionRejected`, the conversation in `ERROR`); `agent_server/test_acp_router.py::test_a_refusal_passes_the_agents_sentence_through` (422, verbatim), `::test_the_preview_maps_each_failure_to_its_status[refused-value]` (422, `unknown profile 'turbo'`); `sdk/conversation/local/test_local_conversation_acp_config_option.py::test_a_refused_live_set_writes_nothing`, `::test_a_live_set_is_persisted_and_survives_a_reload` (the agent's sentence, and the error's `config_id` and `value`). *Gone:* `test_a_refusal_raises_with_the_agents_own_sentence`, `test_a_refused_value_raises_with_its_code_and_the_agents_sentence` (the router's two 422s) |
| **The commands are gone after the first message, when the agent clears them** | **Live:** `…_live.py::test_the_first_prompt_runs_with_the_chosen_values` with `OPENHANDS_ACP_LIVE_EXPECT_COMMANDS_CLEARED=1` (dr-acp). `agent_server/test_acp_router.py::test_a_started_session_reports_the_chosen_value_and_cleared_commands`. *Gone:* `test_changes_during_a_prompt_are_published_in_order` (the router test reads the same newest event through the events search; the ordering tests below pin the order beneath it) |
| **The last persisted event is the newest state** (decision B, §4.3) | `sdk/agent/test_acp_session_controls.py::test_concurrent_publishes_keep_snapshot_order_and_end_on_the_newest` (one recorder and two publishers on three threads; its strictly increasing sequence also allows no repeat), `::test_nothing_is_published_while_a_session_is_starting`, `::test_controls_reported_while_the_session_starts_are_published_once_it_started`, `::test_commands_reported_after_session_new_answered_are_published`; `sdk/conversation/local/test_local_conversation_acp_config_option.py::test_events_from_other_threads_are_persisted_in_submission_order`, `::test_a_portal_thread_event_during_a_synchronous_run_lands_after_the_step` (no deadlock), `::test_events_emitted_after_close_are_dropped`, `::test_the_agent_swap_hands_publishing_to_the_copy`. *Gone:* `test_an_unchanged_snapshot_is_not_published_again` (the concurrency test), and the router's `test_the_events_search_returns_the_newest_controls_event` (every router test that reads the newest controls reads them through the search, by the module-qualified kind) |
| **Only the root session's controls are published, masked and normalized; ACP's two updates go no further than the record** | `sdk/agent/test_acp_session_controls.py::test_each_session_keeps_its_own_controls_and_only_the_root_is_published`, `::test_agent_supplied_text_is_masked_before_it_is_stored`, `::test_session_updates_of_both_kinds_are_recorded_and_not_routed_on`, `::test_entries_the_protocol_cannot_parse_are_dropped_not_raised` (also a nameless command, a command without input and a boolean option); `sdk/agent/test_acp_models.py` (4: the hint through 0.12.1's `RootModel`, grouped and ungrouped selects, a category ACP does not name); `sdk/event/test_acp_session_controls_event.py` (3: a JSON round trip as its own kind, one-line rendering, empty rendering). *Gone:* the models' no-input, nameless and boolean tests (the protocol-drop test); the event's resume-transcript test (upstream's) |
| **Resume:** nothing reapplied after `session/load`, everything after a fallback to `session/new`; a live set survives a reload | `sdk/agent/test_acp_session_controls.py::test_after_a_successful_load_no_value_is_reapplied`, `::test_after_a_fallback_to_a_fresh_session_every_value_is_reapplied`; `sdk/conversation/local/test_local_conversation_acp_config_option.py::test_a_live_set_is_persisted_and_survives_a_reload` |
| **Setting an option, live or before the start** (§4.5, §4.7) | `sdk/agent/test_acp_session_controls.py::test_a_live_set_returns_the_agents_new_controls`, `::test_a_set_before_any_session_is_refused`, `::test_values_are_set_in_order_and_every_response_is_recorded`; `agent_server/test_acp_router.py::test_a_live_set_answers_with_the_agents_controls`, `::test_a_set_the_agent_does_not_answer_times_out` (504), `::test_a_set_on_an_unknown_conversation_is_not_found`, `::test_a_set_that_is_not_for_this_route_is_refused[not-acp, model-option, empty-id]` (400, 400, and *v2.5* 422 for an empty `config_id`, the request's `min_length`; `76533fc` renamed it from `…_is_a_bad_request`), `::test_a_set_on_a_service_that_closed_after_its_lookup_is_a_bad_request` (400 `inactive_service`), `::test_an_internal_error_from_the_agent_is_a_500_carrying_its_message_unmasked` (B20). *Gone:* the SDK's timeout test (the router's 504), `test_an_internal_agent_error_propagates_unchanged` (the router's 500), `test_a_conversation_that_is_not_acp_refuses_config_options` (the router's `not-acp` 400) |
| **The model stays with `switch_acp_model`** (decision E) | `sdk/agent/test_acp_session_controls.py::test_the_model_option_and_an_empty_id_are_refused_in_the_field_and_by_a_live_set[model, '']` (`ACPConfigOptionValues`, on `ACPAgent`; *v2.5, `76533fc`:* and the agent's live `set_acp_config_option`, each with its sentence), `::test_a_model_switch_through_set_config_option_updates_the_published_model`; `agent_server/test_acp_router.py::test_the_start_refuses_option_values_it_cannot_apply[not-acp, model-option]` (422), `::test_a_set_that_is_not_for_this_route_is_refused[model-option]` (400). *Gone:* the set calls' refusals of `model` and `""` on `ACPAgent` and `LocalConversation` *(v2.5: the agent's are back, in the field test; the conversation's refusal of `""` is pinned only through the check it shares with them)*, and the preview's 422 for `model` (above) |
| **Feature detection** | `agent_server/test_acp_router.py::test_server_info_announces_acp_session_controls` |
| **The TypeScript client** (7, in TypeScript client CI) | `clients/typescript/src/__tests__/api-clients.test.ts › ACP session controls ›` 4 (the preview; a set; the newest event by the kind the search matches; `RemoteConversation`); `event-types.test.ts › ACPSessionControlsEvent › is recognised by its kind`, `› yields the lists of the first controls event, replacing rather than merging` (and, since `1118139`, empty lists for no events, which the client's own empty-page test asserted); `index.test.ts › should export the ACP session controls helpers from the package root` |

*PR 2 · Conversation header panels*

| Property | Tests |
|---|---|
| **C2's manifest validates, a tab at `/` among them** | `agent_server/canvas_extensions/test_canvas_extensions_manifest.py::test_a_header_panel_with_tabs_validates`. *Gone:* `test_a_tab_path_defaults_to_the_panel_root` (the `Field` default; *v2.5:* pinned again by the malformed-panel table's `duplicate-default-tab-path`, next row), `test_a_tab_may_sit_at_the_root_where_a_page_may_not` (C2's manifest has a tab at `/`; a page at `/` is upstream's `test_invalid_page_path_rejected`) |
| **A malformed panel makes the manifest invalid; page, panel and tab ids are one namespace** | `…/test_canvas_extensions_manifest.py::test_a_malformed_panel_makes_the_manifest_invalid[panel-id, panel-title, no-tabs, tab-id, tab-title, relative-tab-path, uppercase-tab-path, trailing-slash, duplicate-tab-path, duplicate-default-tab-path, absolute-icon, traversing-icon, icon-type]`, `::test_pages_panels_and_tabs_share_one_id_namespace[page-and-panel, page-and-tab, two-panels, panel-and-tab, tabs-in-two-panels]`. *Gone:* the `panel-title`, `no-tabs` and `tab-title` cases (a `Field`'s `min_length`). *(v2.5, `d938c90`: back, with `duplicate-default-tab-path`, a tab with no path beside a tab at `/`.)* |
| **A manifest without panels dumps byte for byte as before**, so no local App's backend needs re-approval | `…/test_canvas_extensions_manifest.py::test_a_manifest_without_panels_dumps_exactly_as_before`. *Gone:* `test_a_manifest_with_panels_dumps_them` (the router's list-and-get test compares the panels in full) |
| **An icon is a contained image, at install and on every serve** | `agent_server/canvas_extensions/test_canvas_extensions_entrypoint_containment.py::test_an_icon_that_is_not_a_contained_image_makes_the_install_invalid[symlink-outside, missing, directory, symlink-to-other-type]`; `agent_server/test_canvas_extensions_router.py::test_the_icon_route_rechecks_containment_on_every_request`. *Gone:* `test_a_contained_panel_icon_resolves` (the router's icon tests serve a contained icon and answer 404 for an unknown panel) |
| **Panels and icons are served, and the feature is announced** | `agent_server/test_canvas_extensions_router.py::test_list_and_get_return_the_conversation_panels`, `::test_the_icon_route_serves_the_icon_with_its_type_and_safe_headers[an .svg, a .png]`, `::test_the_icon_route_is_not_found_without_an_extension_panel_or_icon[unknown-extension, unknown-panel, no-icon]` (two tests merged, `9e92cb2`), `::test_server_info_announces_conversation_panels`; `agent_server/test_openapi_contract.py::test_panel_icon_route_is_documented_as_a_png_or_svg_image` (B23) |

*PR 3 · App backends on macOS*

| Property | Tests |
|---|---|
| **Falsifier 3.** An App backend starts on macOS as it does on Linux | **The macOS job** runs all of `tests/agent_server/canvas_extensions` on `macos-latest` (164 passed at `7f03b56`), among them upstream's real-backend lifecycle tests, `agent_server/canvas_extensions/test_canvas_extension_backend.py::test_prepare_start_logs_stop_and_preserve_data`, `::test_stop_kills_sigterm_ignoring_descendant` and `::test_backend_http_lifecycle_and_data_deletion`, against a test artifact declared for all four platforms; the Linux suite runs the same. The backend is a test script, not the Library's artifact (D3's; D5's macOS build starts the Library itself). |
| **Platform names** | `…/test_canvas_extension_backend.py::test_current_platform_names_the_artifact_for_each_system_and_machine[7 (system, machine) pairs]`; the darwin keys are accepted by every lifecycle test above. *Gone:* the rows `(Linux, arm64)`, `(FreeBSD, amd64)` and `(Darwin, ppc)` (`79e77d0`); `test_macos_backend_artifacts_are_accepted` and `test_an_unknown_backend_platform_is_still_refused` (`c4a246a`) |
| **Loopback traffic is never proxied** (decision G) | `…/test_canvas_extension_backend.py::test_a_backend_becomes_ready_with_a_proxy_configured`; `agent_server/canvas_extensions/test_canvas_extension_bridge.py::test_http_and_websocket_reach_a_loopback_backend_with_a_proxy_configured` (every proxy variable at a closed port, `NO_PROXY` unset) |
| **On macOS a refused signal to an exited group means it is gone; elsewhere it still fails** (§3.2 B12) | `…/test_canvas_extension_backend.py::test_a_refusal_to_signal_the_group_means_it_exited_on_macos_only[probe, signal]` (both sides in one test; two tests merged, `79e77d0`), `::test_stop_completes_when_macos_refuses_to_signal_the_exited_group` |
| **A slow first launch still becomes ready** (§3.2 B13) | `…/test_canvas_extension_backend.py::test_a_backend_slow_to_launch_becomes_ready_within_the_default_budget` |
| **The REST check accepts new platform keys, and nothing else** (§3.2 B14) | `cross/test_check_agent_server_rest_api_breakage.py::test_backend_artifact_platform_additions_are_downgraded_and_nothing_else` |

**Not pinned by any test**, at `7f03b56`: the Gate B section's list, unchanged (§7 item 5's order;
with dr-acp, that changing the namespace changes the menu; the empty first event after a start; a
start value for a built-in provider's session mode; the Library's own backend on a Mac), and what
the refactor left unasserted, above. §4.10, §5.3 and §6.3 map every test file: 111 deterministic
cases (PR 1 68, PR 2 29, PR 3 14), from 146 at `5e3317f`, and S2's 7 TypeScript tests. *(v2.5: 116
at `d938c90`, PR 1 69, PR 2 33, PR 3 14; the TypeScript tests unchanged.)*

**Size, before and after.** `git diff --numstat 1f2b52d..<commit>`, by the parts of §3.2 B19:

| Part | Spec | `5e3317f` (Gate B), added (removed) | `7f03b56`, added (removed) |
|---|---|---|---|
| Commands and options: `acp_models.py`, the event, `acp_agent.py`, `local_conversation.py`, `request.py`, the visualizer | ≈200 | 719 (27) | 663 (28) |
| Preview and routes: `acp_preview.py`, `acp_router.py`, `conversation_service.py`, `event_service.py`, `api.py`, `conversation_router.py`, one capability | ≈150 | 450 (85) | 434 (85) |
| Header panels: `manifest.py`, `installed.py`, `canvas_extensions_router.py`, one capability | ≈60 | 234 (12) | 218 (19) |
| macOS backends: `backend.py`, `proxy.py`, the platform names, the REST check, the macOS job | ≈30 | 109 (18) | 104 (18) |
| TypeScript client | ≈100 | 200 (1) | 200 (1) |
| The live file's line in `acp-live-tests` | — | 2 | 2 |
| **Code and CI** | ≈540 | **1,714 (143)** | **1,621 (151)** |
| Tests: Python | | 2,658 (11) | 2,242 (11) |
| Tests: the scripted ACP agent | | 310 | 310 |
| Tests: TypeScript | | 155 (1) | 146 (1) |
| **Tests** | ≈350 | **3,123 (12)** | **2,698 (12)** |
| **Total** | **≈0.9k, ≈3 h at Gate C** | **4,837 (155); 4,023 non-blank; about 16 h** | **4,319 (163); 3,618 non-blank; about 14.4 h** |

By PR: PR 1 3,839 → 3,433, PR 2 593 → 523, PR 3 405 → 363. The refactor took 518 lines out (93 of
code, 425 of tests) and added 8 to the upstream lines S2 removes (R1, R5). Against the spec, the
code is 3.0 times its estimate (was 3.2) and the tests 7.7 times (was 8.9); §3.2 B19's reading of
the growth stands. Python test functions: 99 → 74, plus the live file's 3; TypeScript tests 8 → 7.
*(v2.5: at `d938c90`, 4,343 added and 163 removed, 24 lines of tests more than `7f03b56`; PR 1 3,447,
PR 2 533, PR 3 363; test functions unchanged. The Gate C section gives each level's lines.)*

## Gate B: what to read (approved at v2.3, kept as history)

*(v2.4) Approved at Gate B at v2.3, for the build at `5e3317f`, and kept as it was then. For the
code at `7f03b56`, the refactor section above replaces its evidence, its property tables and its
size. The revision lines, the file's location and the reading guide, which closed this section,
now stand above the refactor section.*

**About 45 minutes, in this order.** The codebase stays closed. The Gate B set is this doc, S2's
as-built document (`as_built/s2-agent-surfaces.md` on deep-reasoning's branch `as-built/s2`, the
Cartographer's) and the runs below. Everything after §3 is kept whole as the reference C2, D3, D5 and
the PR split build against (Michael: don't force compression); Gate B does not need it, except §7.

| # | Read | What it gives you | Minutes |
|---|---|---|---|
| 1 | This section and the v2.3, v2.2, v2.1 and v2 revision lines below it | where the proof is, and which sentences of v1 changed | 10 |
| 2 | §1 | what S2 changes; v2 corrects its order-and-independence paragraph | 5 |
| 3 | §3.1 | the departures from the spec: the ten accepted on 2026-10-02, all still true; items 11 and 12 new | 4 |
| 4 | §3.2 | what the build changed, each with its reason and the test that pins it | 12 |
| 5 | §7 | the contract C2 builds against; items 2, 4, 5 and 6 changed (item 4 again in v2.1) | 4 |
| 6 | Open the runs below | that they are green | 2 |
| 7 | `as_built/s2-agent-surfaces.md` | what exists and its divergences, as the Cartographer read them (at `6f97bf3`; §3.2 B22 corrects one of its findings) | 8 |

**One thing to rule on: size.** The spec estimated S2 at ≈0.9k lines with tests and ≈3 h at Gate C
(S2's cost line: commands and options ≈200, preview ≈150, panels ≈60, macOS ≈30, TypeScript client
≈100, tests ≈350); v1 gave no estimate of its own. The build is **4,837 lines added and 155 removed**
at `5e3317f` (4,023 non-blank added): 1,714 of code and CI, 3,123 of tests (2,658 Python, the 310-line
scripted ACP agent, 155 TypeScript). PR 1 is 3,839 of them, PR 2 593, PR 3 405. At ≈300 lines an hour
Gate C reads it in about 16 h, against the spec's ≈3 h: tests 8.9 times the estimate, code 3.2 times.
The build recorded no reason for the growth; this design's reading is §3.2 B19. The Scout and the
Refactorer, after Gate B, are where it shrinks.

**The evidence.**

- **CI**, PR #1's checks at `5e3317f`, the branch's head: 28 check runs, every one green but upstream's
  "Validate PR description" (skipped on a draft). With the fork-only `1f2b52d` (B25), upstream's
  main-only guards ran on this pull request too.
  - Upstream's `tests.yml`, [run 37146974364](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37146974364): **sdk-tests** 6,699 passed, 7
    skipped, 12 xfailed; **agent-server-tests** 2,431 passed (B23's and B24's five new tests among
    them); **cross-tests** 496 passed, 1 skipped; **macos-app-backend-tests**, PR 3's job on
    `macos-latest`, 178 passed (all of `tests/agent_server/canvas_extensions`); **acp-live-tests** 25
    passed, 2 skipped (S2's six built-in provider previews passed at `5e3317f`; its two dr-acp tests
    skip without an agent command); and windows-tests, tools-tests, workspace-tests,
    agent-server-stress-tests, Test directory allowlist and coverage-report.
  - The guards upstream runs only for pull requests to `main`: **TypeScript client CI**
    ([37146974358](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37146974358): build, security, `test (22.12)` and `test (24.x)` with lint (7
    warnings, no errors), 23 files and **355 tests, S2's 8 among them**, format and coverage,
    public-type-budget, agent-server-api, validate-acp-providers); **TypeScript client integration
    tests** ([37146974428](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37146974428): smoke-test, integration-test); **Persisted settings
    compatibility checks** ([37146974370](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37146974370)); **REST API breakage checks**
    ([37146974332](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37146974332), attempt 2, against `v1.50.1`, below) and the **Version bump guard**
    ([37146974326](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37146974326)), green with the caveats below.
  - Also green: Pre-commit checks ([37146974316](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37146974316)), Check Docstrings
    ([37146974314](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37146974314)), Deprecation deadlines ([37146974368](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37146974368)),
    TypeScript client endpoint audit ([37146974355](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37146974355)).
- **The REST breakage check, against upstream's `v1.50.1`** (v2.3). Michael pushed the
  `v1.50.1` tag to the fork, and the check was re-run on PR #1 at `5e3317f`
  ([attempt 2 of run 37146974332](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37146974332/job/111276569669)): it fetched the tag, ran oasdiff 1.19.1 against it and
  passed (exit 0). It reports eight changes, and the script's policy allows every one, filing all
  eight under its notice "Additive oneOf/anyOf expansion or enum-value additions detected in response
  schemas": `ACPSessionControlsEvent` added to the event `oneOf` in two 200 responses, and
  `darwin-amd64` and `darwin-arm64` added to the backend `artifacts` keys in the three 200 responses
  that carry a manifest. §4.9 lists them. The platform keys are B14's fallback at work, in CI for the
  first time. The same check on PR #2 (S1's, at `a3279be`, [attempt 2 of run
  37146975811](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37146975811/job/111276572426)) reports the same eight plus S1's `ACPSessionMessageEvent`,
  `ACPSessionTextEvent` and `ACPSubagentEvent` in the same two `oneOf` lists, and passes.
- **What CI's green does not cover** (B25):
  - **The SDK API breakage check was skipped**: the version-bump guard runs "Check Python API
    compatibility" only when a package version changes, and none did. The Conductor ran it locally
    at S2's head: one error, upstream's (`ACPAgentSettings.llm` against PyPI 1.50.1), the same on
    `deep-reasoning`; S2 adds none.
  - **The OpenAPI weak-schema ratchet over S2's real schema did not run in CI.** It is `make
    test-server-schema`, a step of `server.yml`, which `1f2b52d` left on `main` only because the same
    workflow builds and pushes images; the agent-server suite tests only the ratchet's logic, on
    synthetic documents (`test_openapi_contract.py`), so v2's "the weak-schema ratchet among them"
    overstated it (B23). The Conductor ran it locally at `5e3317f`: passes, 62 allowlisted locations,
    after `13e5904` fixed the one it found.
- **Live tier**, deep-reasoning's `fork-live.yml` on branch `ci/fork-live` (`a8154e2`: D1's head plus
  the workflow, so D1's `dr-acp` is the agent behind the bridge),
  [run 37147707860](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37147707860), dispatched with `sdk_ref` `5e3317f` and `suites: s2`: the SDK
  checkout is **`5e3317f`, S2's own head**. Its step "S2, commands, options and the preview" ran
  `tests/sdk/agent/test_acp_session_controls_live.py`: **8 passed in 124 s.**
  - `test_a_built_in_provider_can_be_previewed[claude-code|codex|gemini-cli|kimi-code|pi|opencode]`:
    each starts that provider's ACP adapter (through `npx`, with a bogus key) and previews its
    commands and options. No prompt was sent to any of them.
  - `test_the_preview_lists_what_the_started_session_lists` and
    `test_the_first_prompt_runs_with_the_chosen_values`: `dr-acp --config
    docs/configs/advising/main.yaml` on gpt-6-luna, with the start value `{"namespace": "root"}` (the
    config's default namespace is `advising`) and the commands expected cleared by the first prompt.

  Four warnings, all `PytestUnraisableExceptionWarning` from a subprocess transport collected after
  its event loop closed; no assertion depends on them. Earlier runs of the same file, for the
  record: [37143895412](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37143895412) at `6f97bf3` (8 passed, 127 s) and
  [37141960911](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37141960911) inside S1's head `0cfb6a2` (8 passed, 100 s).

**Which tests carry which property.** Each test's name states the property it pins. Paths are under
`tests/` in the fork; `[…]` is a parametrization; `::` repeats the file named before it.

*PR 1 · ACP session controls*

| Property | Tests |
|---|---|
| **Falsifier 1.** An option set before the first message is the one the run uses | **Live:** `sdk/agent/test_acp_session_controls_live.py::test_the_first_prompt_runs_with_the_chosen_values` (dr-acp: after the first prompt the reported namespace is `root`). Against the scripted agent: `sdk/agent/test_acp_session_controls.py::test_start_values_reach_the_agent_after_session_new_and_before_the_prompt` (the agent's request log: `session/new`, then `session/set_config_option`, then `session/prompt`); `sdk/conversation/local/test_local_conversation_acp_config_option.py::test_a_set_before_the_start_is_persisted_and_applied_at_the_start`; `agent_server/test_acp_router.py::test_a_started_session_reports_the_chosen_value_and_cleared_commands`, `::test_the_start_folds_option_values_into_the_agent_only` (in `base_state.json`, never `meta.json`), `::test_a_set_before_the_start_is_kept_for_it` |
| **Falsifier 2.** The commands a preview lists are those the started session lists | **Live:** `sdk/agent/test_acp_session_controls_live.py::test_the_preview_lists_what_the_started_session_lists` (dr-acp). Against the scripted agent: `sdk/conversation/test_acp_preview.py::test_the_preview_equals_the_started_session_before_its_first_prompt[3 value sets]`; `agent_server/test_conversation_service.py::test_resolve_launch_gives_the_start_and_the_preview_the_same_agent[agent, agent_settings, agent_profile_id]`; `agent_server/test_acp_router.py::test_the_preview_answers_for_each_way_of_naming_the_agent[the same 3]` |
| **Any ACP agent can be previewed, and the preview leaves nothing behind** | **Live:** `sdk/agent/test_acp_session_controls_live.py::test_a_built_in_provider_can_be_previewed[6 providers]`, in both runs. `sdk/conversation/test_acp_preview.py::test_session_close_is_sent_when_the_agent_advertises_it`, `::test_session_close_is_not_sent_when_the_agent_does_not_advertise_it`, `::test_an_agent_that_never_reports_commands_is_previewed_after_the_wait`, `::test_the_agent_process_is_gone_afterwards[previewed, refused]`, `::test_a_missing_working_directory_is_previewed_from_an_empty_scratch_directory`, `::test_an_agent_that_cannot_be_spawned_raises_a_spawn_error`; `agent_server/test_acp_router.py::test_the_preview_maps_each_failure_to_its_status[refused-value, startup-timeout, spawn-error, not-acp, values-not-acp]` (each also asserts no `preview-*` directory is left), `::test_the_preview_holds_a_run_slot`, `::test_the_preview_is_unavailable_in_the_docker_runtime`, `::test_the_preview_of_an_unknown_profile_is_not_found`; *(v2.2)* `::test_the_preview_answers_an_authentication_failure_with_502_not_401` (and the 5xx body, B26), `::test_the_preview_of_a_profile_with_a_dangling_mcp_reference_is_refused` (422, the missing references named) |
| **A value the agent refuses stops the start with the agent's own sentence, and nothing is prompted** | `sdk/agent/test_acp_session_controls.py::test_a_refused_start_value_ends_the_start_and_no_prompt_is_sent` (`ConversationErrorEvent` code `ACPConfigOptionRejected`, the conversation in `ERROR`), `::test_a_refusal_raises_with_the_agents_own_sentence`; `sdk/conversation/test_acp_preview.py::test_a_refused_value_raises_with_its_code_and_the_agents_sentence`; `agent_server/test_acp_router.py::test_a_refusal_passes_the_agents_sentence_through` (422, verbatim); `sdk/conversation/local/test_local_conversation_acp_config_option.py::test_a_refused_live_set_writes_nothing` |
| **The commands are gone after the first message, when the agent clears them** | **Live:** `…_live.py::test_the_first_prompt_runs_with_the_chosen_values` with `OPENHANDS_ACP_LIVE_EXPECT_COMMANDS_CLEARED=1` (dr-acp). `sdk/agent/test_acp_session_controls.py::test_changes_during_a_prompt_are_published_in_order`; `agent_server/test_acp_router.py::test_a_started_session_reports_the_chosen_value_and_cleared_commands` |
| **The last persisted event is the newest state** (decision B, §4.3) | `sdk/agent/test_acp_session_controls.py::test_concurrent_publishes_keep_snapshot_order_and_end_on_the_newest` (one recorder and two publishers on three threads, 300 snapshots), `::test_nothing_is_published_while_a_session_is_starting`, `::test_controls_reported_while_the_session_starts_are_published_once_it_started`, `::test_commands_reported_after_session_new_answered_are_published`, `::test_an_unchanged_snapshot_is_not_published_again`; `sdk/conversation/local/test_local_conversation_acp_config_option.py::test_events_from_other_threads_are_persisted_in_submission_order`, `::test_a_portal_thread_event_during_a_synchronous_run_lands_after_the_step` (no deadlock), `::test_events_emitted_after_close_are_dropped`, `::test_the_agent_swap_hands_publishing_to_the_copy`; `agent_server/test_acp_router.py::test_the_events_search_returns_the_newest_controls_event` |
| **Only the root session's controls are published, masked and normalized; ACP's two updates go no further than the record** | `sdk/agent/test_acp_session_controls.py::test_each_session_keeps_its_own_controls_and_only_the_root_is_published`, `::test_agent_supplied_text_is_masked_before_it_is_stored`, `::test_session_updates_of_both_kinds_are_recorded_and_not_routed_on`, `::test_entries_the_protocol_cannot_parse_are_dropped_not_raised`; `sdk/agent/test_acp_models.py` (7: the hint through 0.12.1's `RootModel`, no input, nameless commands dropped, grouped and ungrouped selects, a boolean, a category ACP does not name); `sdk/event/test_acp_session_controls_event.py` (4: a JSON round trip as its own kind, one-line rendering, empty rendering, skipped by the resume transcript) |
| **Resume:** nothing reapplied after `session/load`, everything after a fallback to `session/new`; a live set survives a reload | `sdk/agent/test_acp_session_controls.py::test_after_a_successful_load_no_value_is_reapplied`, `::test_after_a_fallback_to_a_fresh_session_every_value_is_reapplied`; `sdk/conversation/local/test_local_conversation_acp_config_option.py::test_a_live_set_is_persisted_and_survives_a_reload` |
| **Setting an option, live or before the start** (§4.5, §4.7) | `sdk/agent/test_acp_session_controls.py::test_a_live_set_returns_the_agents_new_controls`, `::test_a_set_before_any_session_is_refused`, `::test_a_silent_agent_times_out_within_the_config_option_timeout`, `::test_values_are_set_in_order_and_every_response_is_recorded`, `::test_an_internal_agent_error_propagates_unchanged`; `agent_server/test_acp_router.py::test_a_live_set_answers_with_the_agents_controls`, `::test_a_set_the_agent_does_not_answer_times_out` (504), `::test_a_set_on_an_unknown_conversation_is_not_found`, `::test_a_set_that_is_not_for_this_route_is_a_bad_request[not-acp, model-option]`; *(v2.2)* `::test_a_set_on_a_service_that_closed_after_its_lookup_is_a_bad_request` (400 `inactive_service`), `::test_an_internal_error_from_the_agent_is_a_500_carrying_its_message_unmasked` (B20); `sdk/conversation/local/test_local_conversation_acp_config_option.py::test_a_conversation_that_is_not_acp_refuses_config_options` |
| **The model stays with `switch_acp_model`** (decision E) | `sdk/agent/test_acp_session_controls.py::test_the_model_option_and_an_empty_id_are_refused_in_the_field[model, '']`, `::test_the_model_option_and_an_empty_id_are_refused_by_the_set_call[model, '']`, `::test_a_model_switch_through_set_config_option_updates_the_published_model`; `sdk/conversation/local/test_local_conversation_acp_config_option.py::test_the_model_option_and_an_empty_id_are_refused[model, '']`; `agent_server/test_acp_router.py::test_the_preview_refuses_the_model_option`, `::test_the_start_refuses_option_values_it_cannot_apply[not-acp, model-option]` |
| **Feature detection** | `agent_server/test_acp_router.py::test_server_info_announces_acp_session_controls` |
| **The TypeScript client** (in CI at `5e3317f`, TypeScript client CI) | `clients/typescript/src/__tests__/api-clients.test.ts › ACP session controls ›` 5 tests (the preview; a set; the newest event by the kind the search matches; empty lists before anything is reported; `RemoteConversation`); `event-types.test.ts › ACPSessionControlsEvent › is recognised by its kind`, `› yields the lists of the first controls event, replacing rather than merging`; `index.test.ts › should export the ACP session controls helpers from the package root` |

*PR 2 · Conversation header panels*

| Property | Tests |
|---|---|
| **C2's manifest validates; a tab may sit at `/`, a page still may not** | `agent_server/canvas_extensions/test_canvas_extensions_manifest.py::test_a_header_panel_with_tabs_validates`, `::test_a_tab_path_defaults_to_the_panel_root`, `::test_a_tab_may_sit_at_the_root_where_a_page_may_not` |
| **A malformed panel makes the manifest invalid; page, panel and tab ids are one namespace** | `…/test_canvas_extensions_manifest.py::test_a_malformed_panel_makes_the_manifest_invalid[panel-id, panel-title, no-tabs, tab-id, tab-title, relative-tab-path, uppercase-tab-path, trailing-slash, duplicate-tab-path, absolute-icon, traversing-icon, icon-type]`, `::test_pages_panels_and_tabs_share_one_id_namespace[page-and-panel, page-and-tab, two-panels, panel-and-tab, tabs-in-two-panels]` |
| **A manifest without panels dumps byte for byte as before**, so no local App's backend needs re-approval | `…/test_canvas_extensions_manifest.py::test_a_manifest_without_panels_dumps_exactly_as_before`, `::test_a_manifest_with_panels_dumps_them` |
| **An icon is a contained image, at install and on every serve** | `agent_server/canvas_extensions/test_canvas_extensions_entrypoint_containment.py::test_a_contained_panel_icon_resolves`, `::test_an_icon_that_is_not_a_contained_image_makes_the_install_invalid[symlink-outside, missing, directory, symlink-to-other-type]`; `agent_server/test_canvas_extensions_router.py::test_the_icon_route_rechecks_containment_on_every_request` |
| **Panels and icons are served, and the feature is announced** | `agent_server/test_canvas_extensions_router.py::test_list_and_get_return_the_conversation_panels`, `::test_the_icon_route_serves_the_icon_with_its_type_and_safe_headers[an .svg, a .png]`, `::test_the_icon_route_is_not_found_for_unknown_names[unknown-extension, unknown-panel]`, `::test_the_icon_route_is_not_found_for_a_panel_without_an_icon`, `::test_server_info_announces_conversation_panels`; *(v2.2)* `agent_server/test_openapi_contract.py::test_panel_icon_route_is_documented_as_a_png_or_svg_image` (B23) |

*PR 3 · App backends on macOS*

| Property | Tests |
|---|---|
| **Falsifier 3.** An App backend starts on macOS as it does on Linux | **The macOS job** runs all of `tests/agent_server/canvas_extensions` on `macos-latest` (178 passed), among them upstream's real-backend lifecycle tests, `agent_server/canvas_extensions/test_canvas_extension_backend.py::test_prepare_start_logs_stop_and_preserve_data`, `::test_stop_kills_sigterm_ignoring_descendant` and `::test_backend_http_lifecycle_and_data_deletion`, now against a test artifact declared for all four platforms; the Linux suite runs the same. The backend is a test script, not the Library's artifact (D3's; D5's macOS build starts the Library itself). |
| **Platform names** | `…/test_canvas_extension_backend.py::test_current_platform_names_the_artifact_for_each_system_and_machine[10 (system, machine) pairs]`; `…/test_canvas_extensions_manifest.py::test_macos_backend_artifacts_are_accepted`, `::test_an_unknown_backend_platform_is_still_refused` |
| **Loopback traffic is never proxied** (decision G) | `…/test_canvas_extension_backend.py::test_a_backend_becomes_ready_with_a_proxy_configured`; `agent_server/canvas_extensions/test_canvas_extension_bridge.py::test_http_and_websocket_reach_a_loopback_backend_with_a_proxy_configured` (every proxy variable at a closed port, `NO_PROXY` unset) |
| **On macOS a refused signal to an exited group means it is gone; elsewhere it still fails** (§3.2 B12) | `…/test_canvas_extension_backend.py::test_a_refusal_to_signal_the_group_on_macos_means_it_exited[probe, signal]`, `::test_a_refusal_to_signal_the_group_elsewhere_still_fails[probe, signal]`, `::test_stop_completes_when_macos_refuses_to_signal_the_exited_group` |
| **A slow first launch still becomes ready** (§3.2 B13) | `…/test_canvas_extension_backend.py::test_a_backend_slow_to_launch_becomes_ready_within_the_default_budget` |
| **The REST check accepts new platform keys, and nothing else** (§3.2 B14) | `cross/test_check_agent_server_rest_api_breakage.py::test_backend_artifact_platform_additions_are_downgraded_and_nothing_else` |

**Not pinned by any test:** §7 item 5's order (the commands-cleared event against the run's output,
under the agent-server's `arun()`); with dr-acp, that changing the namespace changes the menu (the
live tier sets one value and does not assert which commands `root` offers; the scripted agent shows
it); the empty first event after a start (§3.2 B4: measured by probe, ruled as the contract, no
test); a start value for a built-in provider's session mode (B21); the Library's own backend on a Mac
(D3, D5). *(v2.2: the four status rows v2.1 listed here are pinned, B24.)* §4.10, §5.3 and §6.3 map
every test file: 146 deterministic cases.

**Ruled, for Michael to confirm:** the empty first controls event (§10 item 14): the Conductor ruled
to change nothing in S2; the contract is §7 item 4 as written, and C2 shows an empty slash menu
until the commands arrive. **Open for the Conductor:** §10 item 15 (a start value for a built-in
provider's session mode). §10 item 16 (the unmasked 500) is now pinned as it is.

---

## 1 · What S2 changes

Three generic, upstream-shaped changes to the agent-server, the SDK under it and its TypeScript
client. Each is its own pull request, cherry-picked onto the fork's `main` as its own upstream PR.
Nothing in them names deep_reasoner or reads `_meta`. *(v2.5: the PR split made them a stack of seven
internal drafts based on the fork's `deep-reasoning`, PR 1 cut into five, and nothing goes to `main`
or upstream; the Gate C section.)*

| PR | What it delivers | Who consumes it |
|---|---|---|
| **1 · ACP session controls** | The ACP bridge keeps the slash commands and config options the agent reports for the conversation's root session, and records each change as one persisted event. A client can set an option, on a live session or before the session starts. A start request may carry option values, which the bridge applies after `session/new` and before the first prompt. A preview runs the real start-up path in a throwaway session to answer "what would this agent offer?" before any conversation exists. | C2's slash menu and option picker, on the home screen (the preview) and in a conversation (the event). D1's decomposition commands and namespace option travel through it. |
| **2 · Conversation header panels** | A Canvas App manifest may declare `contributes.conversation_panels` (an id, a title, an optional icon, and tabs shaped like pages). The agent-server validates them, serves them in the manifest it already returns, and serves the icon. | C2's header-panel slot, and through it D3's Show decompositions. |
| **3 · App backends on macOS** | `darwin-arm64` and `darwin-amd64` backend artifacts; platform detection on macOS; loopback traffic to an App backend never goes through an HTTP proxy; a macOS CI job for the App-backend tests. *(v2: also macOS's EPERM from `killpg` read as "the group is gone" (§3.2 B12), and the REST check's allowlist for the new platform keys (B14).)* | D3's Library backend on a Mac; D5's macOS build. |

**Order and independence.** Build PR 3 first (smallest; D3 and D5 need it on a Mac), then PR 2 (C2's
slot and D3 need it), then PR 1 (the largest, and the one that meets S1). The three touch disjoint
files except two: `canvas_extensions/manifest.py`, where PR 2 adds its classes above
`CanvasExtensionContributes` and its new field and validator above that class's existing pages
validator, and PR 3 changes only `BackendPlatform` (line 88), so unchanged lines separate them; and `server_details_router.py`, where PR 1 extends the default capability list and PR 2
appends in `build_server_info`. So each PR's commits cherry-pick onto the fork's `main` without the
others, which the PR split checks.

*(v2, §3.2 B16.)* Built in the other order: PR 1, then PR 2, then PR 3. The three share five files:
the two above, and `.github/workflows/tests.yml` (PR 1's line in `acp-live-tests`, PR 3's macOS
job), `tests/agent_server/canvas_extensions/conftest.py` and `test_canvas_extensions_manifest.py` (PR
2's tests, then PR 3's appended after them). Cherry-picked alone onto the fork's `main` (`53a4bc5`),
PR 1 and PR 2 apply cleanly; PR 3 conflicts in `test_canvas_extensions_manifest.py` and applies
cleanly after PR 2. So the PR split cuts PR 3 after PR 2, or resolves that one hunk.

*(v2.4, R10.)* At `7f03b56` the order no longer binds. `c4a246a` dropped PR 3's two tests from
`test_canvas_extensions_manifest.py`, so the PRs share four files (`manifest.py`,
`server_details_router.py`, `tests.yml` and the canvas-extension tests' `conftest.py`), each in
hunks of its own, and each PR's part of the net diff applies alone onto `53a4bc5`.

PR 1, end to end, with D1's `dr-acp` behind the bridge:

```text
Canvas (C2)                         agent-server and SDK (S2)                              dr-acp (D1)
home screen
  POST /api/acp/preview  ─────────▶ resolve the agent exactly as a start would
   (the start payload               throwaway ConversationState, ACPAgent.init_state ─────▶ initialize, session/new
    + acp_config_options)             set_config_option for each chosen value ───────────▶ (commands for that value
                                      wait for the commands report (at most 2 s) ◀──────── before its response)
  ◀── ACPSessionControls              session/close, stop the process, delete the state
  POST /api/conversations ────────▶ fold acp_config_options into the ACPAgent
                                    first run: session/new → model → options → mode ─────▶
                                      record commands and options per ACP session ◀──────── available_commands_update
                                      ACPSessionControlsEvent: ordered, persisted, streamed ──▶ Canvas
                                    first prompt ──────────────────────────────────────────▶ commands [] and the
                                      ACPSessionControlsEvent (no commands) ◀───────────────  namespace narrowed
  POST /api/conversations/{id}/acp/config-options ─▶ session/set_config_option ──────────▶ refused once started
  ◀── 422 "namespace is fixed once a conversation has started (it is 'router')."
```

**What S2 does not change.** The prompt path: a slash command is a user message whose text starts
with `/<name>` (ACP's rule); the bridge already forwards the user's own content first, with per-turn
extensions and the first prompt's system-message suffix after it (`MessageEvent.to_llm_message`,
`event/llm_convertible/message.py:116–119`; `_build_acp_prompt`, `acp_agent.py:3572–3590`), and S2
leaves that alone. The `initialize` call: S2
advertises no new client capability (S1 owns that call, §8), so agents send only `select` options,
not `boolean` ones; S2 still models both. `_meta`: S2 forwards none of it, because nothing reads it.

---

## 2 · Decisions

The spec's seven expensive-to-reverse decisions in §2 stand. These are the next layer down.

| # | Decision | Why | Rejected |
|---|---|---|---|
| A | **One persisted event kind, latest wins: `ACPSessionControlsEvent` carries both lists in full, every time either changes.** | Commands and options are state, not a log: a client needs only the newest. One kind follows upstream's own precedent, `ACPToolCallEvent`, which folds ACP's `tool_call` and `tool_call_update` into one latest-wins event. The event log becomes the only store: serving the controls needs no new route (the events search by kind, newest first), and they survive an agent-server restart with nothing added. | Two kinds mirroring ACP's two updates (two lookups for one picture, two code paths). Keys in `state.agent_state` lifted onto `ConversationInfo`, as `available_models` is: the state-update event for `agent_state` carries the whole internal dict, and writing it from the bridge's thread needs the conversation lock. A `GET …/acp/controls` route: a second source of truth for the same data. |
| B | **Every controls event goes through one ordered, lock-taking emitter owned by `LocalConversation`.** | The bridge receives updates on the ACP portal thread. There, taking the conversation lock deadlocks the synchronous `run()` (the bridge's docstring, `acp_agent.py:1275–1279`), and a turn's `on_event` exists only while a prompt is in flight (`_clear_turn_callbacks`, `:3934`). D1 sends its commands right after `session/new`'s response, outside any turn, and any ACP agent may send updates between turns. So `ACPAgent` gets one sink, `_on_session_event`, which `LocalConversation` wires to a single-worker executor that takes the state lock and calls `_on_event`. Events persist in submission order; a lock in `ACPAgent` makes submission order equal snapshot order; so the last persisted event is always the newest state (§4.3). | The turn's `on_event` during a turn plus something else between turns: two paths, which can reorder at the boundary. The agent-server's `_emit_event_from_thread` (`event_service.py:1000`): a shared thread pool with no ordering, and agent-server only. **S1 needs the same primitive** for child traffic after the parent's turn has ended, which the spec says is "persisted, not dropped" (§8). |
| C | **Option values ride the start request, live on the agent, and apply only to a fresh `session/new`.** | `StartConversationRequest.acp_config_options` is launch-only, like `agent_profile_id`. It is folded into `ACPAgent.acp_config_options` after the agent is resolved, so it works whether the client sent `agent`, `agent_settings` or `agent_profile_id`. `_init` applies the values in order, after the model and before the session mode. A value the agent refuses fails the start, with the agent's own words, rather than running the first prompt in an option the user did not choose (S2's falsifier). The values are not reapplied after a successful `session/load` (the agent restored its own state, and D1 refuses any different value once started), but they are applied when a resume falls back to a fresh session. A live set also writes the value into the agent, as `switch_acp_model` does for the model, so a fresh fallback session comes back with the user's choices. | A field in `ACPAgentSettings`: it fires the persisted-settings guard (a v8 baseline), and no profile needs a stored default, since dr-acp takes its default namespace from the Library. Reapplying on every `session/load`: a resume would fail whenever the agent had moved a value itself. |
| D | **The preview is the real start-up path in a throwaway state, and its body is the start request.** | `POST /api/acp/preview` takes the JSON a client sends to `POST /api/conversations`, resolves the agent with the same code (extracted from `_create_conversation`, §4.6), builds a `ConversationState` under `conversations_dir/preview-<hex>`, and calls `ACPAgent.init_state`. That spawns the agent with the same environment, secrets, authentication, MCP servers and option values as a start; then the preview waits for the first commands report (at most 2 s), sends `session/close` if the agent advertises it, stops the process and deletes the directory. Same request and same code, so a preview can differ from the started session only if the agent itself answers differently. It holds a run slot while it runs, like any running agent. | A hand-written spawn-and-initialize probe: a second copy of environment building, secret injection, authentication, MCP translation and file credentials, which would drift. An agent looked up by name, as the spec's mock-up has it: the agent-server keeps no agents by name; agents are profiles and settings. A full throwaway `LocalConversation`: it runs hooks, opens observability spans and fetches plugins. |
| E | **The model stays with `switch_acp_model`.** | S2's set route refuses the option id `model` (400), and so does `acp_config_options`. The model path keeps `acp_model`, the sentinel LLM, the persisted model hint and cost attribution in step (`set_acp_model`, `acp_agent.py:4416`); a generic set would leave them stale. S2 does record the model path's `set_config_option` responses, so the controls it publishes stay current after a model switch. | Routing `model` through S2's route to `switch_acp_model`: two routes for one action. |
| F | **Panels share one contribution-id namespace with pages; the icon is a validated package file with its own route; an empty panel list is never serialized.** | Canvas mounts App pages by contribution id (`registerPage(contributionId, mount)`, Canvas `src/types/canvas-extension.ts:81`), so a tab id is the id an App registers that tab's page under, and must be unique across pages, panels and tabs. Canvas also keys the drawer's selected tab and pins by tab id (`conversation-tabs.tsx`), so ids are stable storage keys. The icon gets the entrypoint's containment check at install and on every serve. `exclude_if` keeps `"conversation_panels": []` out of `model_dump_json`, because a locally installed App's backend approval revision is the hash of that dump (`backend.py:121–129`); without it, every local App with a backend would need re-approval after an upgrade. | Icons as names from Canvas's icon set (couples the manifest to one client's icon library). Tabs keyed separately from pages (an App could not reuse one registered page in two places without ambiguity about where it mounts). |
| G | **macOS needs more than the two platform names.** | On macOS, Python's `urllib`, httpx and websockets all read the system proxy settings (`urllib.request.getproxies()` falls back to System Configuration there), and macOS's default proxy exceptions (`*.local`, `169.254/16`) do not include `127.0.0.1`. With a system HTTP proxy configured, common on managed networks, the backend's health probe and the bridge to it go to the proxy, and the backend never becomes ready. Linux reads only environment variables, and has the same bug when `HTTP_PROXY` is set without `NO_PROXY`. PR 3 sends loopback traffic direct. A `macos-latest` job runs the App-backend tests, mirroring upstream's `windows-tests` job (`tests.yml:252`). | Only the names, as the spec's evidence proposed: the falsifier ("the Library App's backend does not start on macOS as it does on Linux") would fail on any Mac with a system proxy. |
| H | **Features are detected through `ServerInfo.capabilities`.** | PR 1 adds `acp_session_controls_v1` and PR 2 adds `canvas_conversation_panels_v1`, upstream's existing mechanism (`server_details_router.py:63–70`). C2 can then tell "this App has no panels" from "this agent-server cannot show panels". PR 3 needs none: a backend's status already says `unsupported` and "does not support this platform". | A version comparison in Canvas (breaks on every fork tag). |
| I | **No guard is weakened.** | S2 adds no persisted-settings field (decision C). Every new public schema is fully typed, with no `dict[str, Any]`, so the weak-schema ratchet (`tests/agent_server/test_openapi_contract.py:248`) stays exact. The new event kind is an additive `oneOf` member, which the REST breakage check accepts (`check_agent_server_rest_api_breakage.py:570–583`). New routes and optional fields are additive. §4.9 and §6.4 name the one place a guard might still object. *(v2: it did object, and one guard is narrowed: the REST check now downgrades a new key of a backend's `artifacts` map, and only that, from breaking to additive, as §6.4 foresaw; §3.2 B14.)* | — |

---

## 3 · Where this design departs from the approved spec, and what the build changed

### 3.1 Departures from, and additions to, the approved spec

Each is a refinement inside S2's scope. If the Conductor reads any as a change of what was approved,
it goes back to Michael.

*(v2)* Items 1 to 10 were accepted on 2026-10-02 (spec, "Rulings at design, 2026-10-02" (3): "S1's
and S2's design departures (§3 of each) are accepted by the Conductor as refinements of our own
interfaces", approved by Michael). **All ten still hold at `6f97bf3`**, each checked against the
code; item 3 gains a correction about the search's `kind` (§3.2 B2). Items 11 and 12 are new in v2
and not yet ruled on.

1. **The preview's request and response differ from the mock-up.** The body is the start payload a
   client already builds for `POST /api/conversations` (plus `acp_config_options`), not
   `{"agent": "dr-acp", "cwd": …, "config": …}`; the response is
   `{"available_commands": […], "config_options": […]}` with each option value an object
   (`value`, `name`, …), not `"commands"` and bare strings. Why: the agent-server has no agent
   registry by name; the same body guarantees the same agent resolution (E11's "the commands a
   preview lists differ from those the started session lists"); `availableCommands` is ACP's name
   (the spec's decision 4); a picker needs each value's label.
2. **Setting an option takes the id in the body, and answers with the full set.**
   `POST /api/conversations/{id}/acp/config-options` with `{"config_id", "value"}`, not
   `…/config-options/{config_id}` with `{"value"}`; the answer is `{"applied", "controls"}`, not
   `{"id", "current_value"}`. Why: ACP config ids are arbitrary strings, and a path segment cannot
   carry one with a `/`; ACP's own response is the full option set, because setting one option may
   change others; `applied` says whether the value reached a live session or waits for the start.
3. **No GET route for the commands and options.** They are served as the newest
   `ACPSessionControlsEvent`, through the existing events search (decision A). The TypeScript client
   wraps that in one call (§4.8). *(v2: the search's `kind` filter takes the module-qualified class
   name, §3.2 B2.)*
4. **One event kind for commands and options together**, not a stream per ACP update (decision A).
5. **The preview does not load plugins attached to that one conversation, nor the per-conversation
   file-credential bindings the agent-server holds** (Codex's `auth.json`). An agent whose commands
   come from a plugin's MCP server shows them only after the start. Why: loading plugins means a git
   fetch and hooks on every preview. It does not affect dr-acp, whose commands come from the Library.
6. **A start-time value the agent refuses ends the start in an error**, with the agent's words, rather
   than continuing in the agent's default (decision C).
7. **macOS gets a loopback-proxy fix and a CI job**, beyond the two platform names the spec's
   evidence called sufficient (decision G).
8. **A dedicated route serves a panel's icon, and two capability strings announce the features**
   (decisions F and H). The spec named neither.
9. **A tab's `path` may be `/`**, which a page's may not: a tab has no route of its own; its path is
   where its page starts inside the panel (§5.1).
10. **The model option cannot be set through S2's route** (decision E).
11. *(v2)* **No preview in the Docker conversation runtime** (501, §3.2 B3). The spec's preview
    serves the home screen and says nothing of runtimes; in the Docker runtime a preview would start
    the agent on the agent-server's host, outside the conversation containers.
12. *(v2)* **Size.** The spec estimated ≈0.9k lines with tests and ≈3 h at Gate C; v1 gave no
    estimate. Built: 4,731 lines added, 155 removed, about 16 h at Gate C (§3.2 B19). *(v2.2: 4,837
    at `5e3317f`. v2.4: 4,319 added and 163 removed at `7f03b56`, after the refactor, about 14.4 h;
    the refactor section's size table. v2.5: 4,343 and 163 at `d938c90`; the stack's seven PRs add
    4,348 between them, about 14.5 h; the Gate C section.)*

### 3.2 Changed by the build (v2)

Each was checked against the code at `6f97bf3` and folded into the sections named. B1 to B10 are PR
1, B11 PR 2, B12 to B15 PR 3, B16 to B18 the branch and the PR split, B19 the size, B20 to B22 (v2.1)
what the as-built found, B23 to B26 (v2.2) what landed after it. Where the build
recorded no reason (in a commit message, a code comment or PR #1's description), the reason given is
marked as this design's reading.

**PR 1 · ACP session controls**

- **B1. Normalization leans on ACP 0.12.1's own lenient parser** (`c3d1db8`; §4.1, A.1). v1: a
  tolerant `from_protocol(raw: Any)` that unwraps `.root`, turns a missing description into `""` and
  drops-and-logs an unknown option type. Built: `from_protocol` takes ACP's typed objects
  (`AvailableCommand`; `SessionConfigOptionSelect | SessionConfigOptionBoolean`), and
  `ACPConfigOption.from_protocol` never returns `None`. What v1 did by hand, ACP does before S2 sees
  an update: its schema skips list items that fail validation (`acp/_deserialize.py`,
  `skip_invalid_items`), salvages a malformed `input` to `None` (`salvage_on_error`), and in 0.12.1
  lists the two option types directly, with no `RootModel` around them. So a command without a
  description is dropped (not kept with `""`); a non-string hint means no input; an option of an
  unknown type is dropped, silently, by ACP; a nameless command is still dropped by S2; a category
  that is not one of ACP's strings becomes `None`. *Why* (the docstrings): "Entries the protocol
  cannot parse (no description, say) never get here: ACP's own schema drops them from the update that
  carried them." An ACP release that wraps the options again would fail these tests, not pass
  silently (this design's reading). *Pinned by:* `test_entries_the_protocol_cannot_parse_are_dropped_not_raised`
  (through the bridge's `session_update`), and the seven tests of `test_acp_models.py`. *(v2.4:
  four of them now; the protocol-drop test carries the no-input, nameless and boolean cases, R4.)*
- **B2. The events search matches the module-qualified kind; events on the wire omit nulls**
  (`e2ec3a9`, `00a5310`; §3.1 item 3, §4.1, §4.7, §4.8, §7 item 4, Appendix B). v1 wrote
  `kind=ACPSessionControlsEvent`. Upstream's search compares `f"{module}.{name}"`
  (`event_service.py:550`), so the query is
  `kind=openhands.sdk.event.acp_session_controls.ACPSessionControlsEvent`; the event's own JSON
  `kind` stays `ACPSessionControlsEvent`. The TypeScript client carries the query value as
  `ACP_SESSION_CONTROLS_EVENT_KIND`, exported from the package root, and both of its readers go
  through one helper, `acpSessionControlsOf(events)` (the first controls event of a newest-first page,
  or empty lists; not exported from the package root, and C2 at `db3b4b9` uses the constant with its
  own search, as-built §4.8). Also found by the build: the events search and the WebSocket dump events with
  `exclude_none=True` (`event_router.py:134`, `sockets.py:490`), so in an event a `null` `input`,
  `description`, `category` or `group` is absent; the preview's and the set route's answers carry
  them as `null`. *Why* (`00a5310`): "the newest event, searched by the module-qualified kind the
  events search matches"; v1 had upstream's search wrong. The nulls: the router test's comment, "The
  events API leaves out null fields". *Pinned by:* `test_the_events_search_returns_the_newest_controls_event`;
  `api-clients.test.ts › ACP session controls › ConversationClient.getAcpSessionControls reads the
  newest event by the kind the search matches`. *(v2.4: the first is gone, `0d21d58`; every router
  test that reads the newest controls reads them through the search, by the module-qualified kind.)*
- **B3. The preview answers 501 in the Docker runtime** (`e2ec3a9`; §3.1 item 11, §4.6, §4.7, §7
  item 2, A.7). When the agent-server's `conversation_runtime` is `docker`, `POST /api/acp/preview`
  answers 501 "This operation is unavailable in Docker runtime mode" before resolving anything; the
  route takes the `Request` for it. The default runtime is `local` (`config.py:367`). *Why* (the
  code): "The Docker runtime runs agents in conversation containers; a preview on this server would
  run the agent outside them"; PR #1's Notes: "it would otherwise start the agent on the host".
  *Pinned by:* `test_the_preview_is_unavailable_in_the_docker_runtime`. *(v2.1)* The set route has no
  such check (as-built D-3).
- **B4. Every session start persists one controls event, and that event can precede the agent's
  menu** (`d0d3fe1`; §4.3, §7 item 4, §10 item 14). *(Rewritten in v2.1: v2 said an event with empty
  lists means the agent offers nothing, which the build does not do; as-built D-2.)* Not a change to
  v1's code but a consequence v1 did not state. An agent's first publish compares the snapshot with
  nothing, so the publish at the end of `_start_acp_server` always submits one event (PR #1's Notes:
  "Every ACP session start now persists one controls event, even when the agent reports nothing").
  That event carries what the new bridge has recorded by then: the options of the `session/new` or
  `session/load` response, and commands only if the agent's `available_commands_update` was handled
  before the start returned (`acp_agent.py:3119–3131, 4878–4894`). An agent that sends its menu after
  the response, as the scripted agent does (50 ms later) and as dr-acp does (from a task that follows
  the response, D1's as-built §4.1, read), is published first with `available_commands: []`, then
  with its menu. Measured with the scripted agent at `6f97bf3`, by a probe for this revision through
  `LocalConversation.run()` with no message (the as-built's D-2 agrees):

  | Start | Controls events persisted, in order |
  |---|---|
  | fresh, no option values (3 of 3) | `[]` with `profile=fast`, then `[summarize]` with `profile=fast` |
  | fresh, `profile=thorough` | `[summarize, compare]` with `profile=thorough`: one event, since the agent sends the commands before the set's response |
  | resume through `session/load` (`--sessions-file`) | `[]` with `profile=fast`, then `[summarize]` with `profile=fast` |
  | resume falling back to `session/new`, values reapplied | one event, equal to the last before the resume (the new agent object compares with nothing) |
  | an agent that never sends commands (`--no-commands`) | `[]` with `profile=fast`, and nothing after |

  A restart after a drain timeout builds a new bridge too, so it can publish the same empty first
  event (read). So right after a start or a resume an empty `available_commands` means either "not
  reported yet" or "none offered", and **nothing in the event says which**: the bridge knows (its
  per-session `_commands_reported` flag, which the preview waits on), but the event does not carry it.
  What holds: the newest event is the state, and a first empty event may be followed, on the agent's
  own timing, by the menu. *Why:* it follows from §4.3's algorithm as v1 wrote it; neither v1 nor the
  build recorded a reason, and v1's §7 did not say it. *Pinned by:* no test pins the empty first
  event; `test_commands_reported_after_session_new_answered_are_published` waits for the menu that
  follows it, and `test_controls_reported_while_the_session_starts_are_published_once_it_started`
  pins a single event when the menu came first. What C2 can do about it is §10 item 14. *(v2.2:
  ruled by the Conductor, for Michael to confirm at Gate B: no change in S2; C2 shows an empty slash
  menu until the commands arrive.)*
- **B5. The out-of-turn emitter, as built** (`d0d3fe1`; §4.3, A.4). Created in
  `LocalConversation.__init__` rather than on first use: `ThreadPoolExecutor` starts its one thread on
  the first submit anyway, so the attribute is never `None`. The job is upstream's existing
  `_on_event_with_state_lock`. `close()` shuts it down with `wait=False, cancel_futures=True`,
  guarded for a partly constructed instance. *Why* (the comment): "One worker, so events emitted from
  any thread are persisted in the order they were submitted. Its thread starts on the first submit";
  eager construction over a `None` check is this design's reading. *Pinned by:*
  `test_events_from_other_threads_are_persisted_in_submission_order`,
  `test_events_emitted_after_close_are_dropped`,
  `test_a_portal_thread_event_during_a_synchronous_run_lands_after_the_step`.
- **B6. Publishing, as built** (`d0d3fe1`; §4.2, §4.3, A.3). (a) `_start_acp_server` keeps v1's flag
  and post-start publish; the body it wrapped moved unchanged into a new `_launch_acp_session`, which
  also binds the publisher right after it creates the bridge. (b) `_bind_session_controls` holds the
  agent through a `weakref`. (c) The bridge calls the publisher through
  `_notify_session_controls_changed`, which logs a failure at warning and swallows it. (d)
  `_session_config_options(response)` reads a response's `configOptions` (empty when absent), and
  `_model_config_option` now uses it too. *Why:* (a) the docstring, "Nothing is published while the
  session starts, since its root id may still be the previous process's"; (b) the comment, "the
  portal loop keeps the bridge alive, and the bridge must not keep a dropped agent alive"; (c) and
  (d) this design's reading: v1's "a dropped entry never fails the update" extended to publishing,
  and one reader for the four response kinds. *Pinned by:*
  `test_the_agent_swap_hands_publishing_to_the_copy` (the replaced agent is collected, and the copy
  publishes), `test_nothing_is_published_while_a_session_is_starting`. *(v2.4: (d)'s reader keeps
  its `getattr` on `config_options`, which six of upstream's own tests need, since they pass
  responses without it; the Scout read it as S2's tests' alone, `f5628cc`. The bridge's two records
  now share `_store_session_controls`, R2.)*
- **B7. The preview, as built** (`5252840`, `e2ec3a9`; §4.6, A.6). `preview_acp_session` runs
  `init_state` holding the throwaway state's lock, as `LocalConversation._ensure_agent_ready` does for
  a start, and creates `persistence_dir` itself; the agent-server deletes the directory with upstream's
  `safe_rmtree`, not `shutil.rmtree(…, ignore_errors=True)`. *Why:* not recorded; this design's
  reading: the same locking a start has, and the repository's own deletion helper. *Pinned by:*
  `test_the_preview_answers_for_each_way_of_naming_the_agent[…]` and
  `test_the_preview_maps_each_failure_to_its_status[…]`, which each assert no `preview-*` directory is
  left.
- **B8. The live tier, as built** (`4027912`, and deep-reasoning's `a8154e2`; §9). (a) The built-in
  providers are every entry of `ACP_PROVIDERS`: six (claude-code, codex, gemini-cli, kimi-code, pi,
  opencode), not v1's three; a `model` option is required where the session reported that it selects
  its model through config options (`_model_via_config_option`), not where the registry says so. (b)
  The file joins upstream's `acp-live-tests` job (its changed-files list and its pytest line), so the
  six previews run on every pull request that touches the file, the registry or the workflow. (c) The
  two agent-named tests: `test_the_preview_lists_what_the_started_session_lists` compares a preview
  with a conversation started from the same command and values, after a `run()` with no message;
  `test_the_first_prompt_runs_with_the_chosen_values` sends one prompt ("Reply with the single word:
  ready."), tolerates a failed turn (the agent may need a model key), then asserts each chosen option
  at its value and, with `OPENHANDS_ACP_LIVE_EXPECT_COMMANDS_CLEARED=1`, that the last controls event
  after the prompt lists no commands. (d) The dr-acp job is deep-reasoning's
  `.github/workflows/fork-live.yml`, on branch `ci/fork-live` (D1's head plus the workflow): it takes
  an SDK ref, runs S1's and S2's live files (`suites`: both, s1 or s2) with `dr-acp --config
  docs/configs/advising/main.yaml --home <temp>`, `{"namespace": "root"}` and the cleared-commands
  flag, on gpt-6-luna through the repository's `OPENAI_API_KEY`. Its commit says D5's branch carries
  the same file later. *Why:* (b) to (d) the commits; (a) this design's reading: the registry, so a
  provider added upstream is previewed without editing the test, and the session's own report, which
  is what the preview returns. *Pinned by:* the runs in the Gate B section.
- **B9. The scripted test agent, as built** (`28ca2e1`; §4.10, Appendix C). Served through
  `acp.connection.Connection` and `build_agent_router` behind a tap, not `acp.run_agent`;
  `--sessions-file PATH` keeps sessions in a file, so a later process can `session/load` them (the
  restart path); its commands follow `session/new`'s answer by 50 ms, from a background task; its log
  records notifications as well as requests; `initialize` advertises `loadSession`. Shared helpers in
  `tests/conftest.py`: `SCRIPTED_ACP_AGENT`, `scripted_acp_command(*flags)` and the `acp_request_log`
  fixture. *Why* (the docstring and the commit): the tap, "so the script can send raw notifications
  and read initialize's raw params, which AgentSideConnection cannot", "so later modes can" (S1's
  `--subagents` and `--transcript` do, §8 item 13); `--sessions-file`, "session/load (across
  processes with --sessions-file)". The 50 ms: this design's reading, so commands arrive after the
  `session/new` response, as D1's do.
- **B10. Smaller additions** (§4.1, §4.8). The default visualizer gives the event an entry ("ACP
  Session Controls", in the system colour); the endpoint audit's client-ahead entry has no `tracking`
  link (v1: our fork's draft PR). *Why:* not recorded; this design's reading: the visualizer keys
  every event kind, and the audit's tracking links point at upstream pull requests, which ours are
  not.

**PR 2 · Conversation header panels**

- **B11. An icon must also resolve to a `.svg` or `.png`** (`132db0f`; §5.1, A.8). `resolve_panel_icon`
  refuses an icon whose resolved file (after symlinks) has another suffix, since the served media type
  is taken from the resolved file's suffix. The install-time check runs in
  `CanvasExtensionInstallationInterface`, beside the entrypoint's; tab-path uniqueness is a validator
  on `tabs`. *Why* (the docstring): "does not resolve to a regular .svg or .png file". *Pinned by:*
  `test_an_icon_that_is_not_a_contained_image_makes_the_install_invalid[symlink-to-other-type]`.

**PR 3 · App backends on macOS**

- **B12. On macOS, EPERM from `killpg` means the group is gone** (`0e24793`; §6.1, A.9, §10 item 6).
  v1 named this contingency; the macOS job met it: `_group_alive` raised `PermissionError` while
  `stop()` waited for the group to drain. Built, narrower than v1: `_group_exited(error)` is true for
  ESRCH everywhere and for EPERM only when `platform.system() == "Darwin"`; `_signal_group` and
  `_group_alive` catch `OSError` and re-raise anything else, so EPERM on Linux still surfaces. *Why*
  (the commit): "macOS answers EPERM, not ESRCH, from killpg on a process group whose remaining
  members are all zombies, such as a backend's descendants waiting for launchd to reap them after the
  backend exits … The group is ours and runs as our user, so on macOS that refusal means nothing of it
  is left … Elsewhere EPERM is still raised. Reaping the leader first would not help: asyncio's child
  watcher already reaps it on exit, and the zombies are its orphaned descendants." *Pinned by:*
  `test_a_refusal_to_signal_the_group_on_macos_means_it_exited[probe, signal]`,
  `test_a_refusal_to_signal_the_group_elsewhere_still_fails[probe, signal]`,
  `test_stop_completes_when_macos_refuses_to_signal_the_exited_group`, and the macOS job. *(v2.1: the
  failing run is in CI's history, run 1's macOS job, B22. v2.4: the first two are one test,
  `test_a_refusal_to_signal_the_group_means_it_exited_on_macos_only[probe, signal]`, R9.)*
- **B13. The App backend test fixture keeps the manifest's 30 s health budget** (`6f97bf3`; §6.3).
  v1: the fixture declares all four platforms, so the lifecycle tests run unchanged on macOS. Built so
  (`759ffb2`); then the fixture's own 3 s health timeout gave way to the manifest's default, 30 s
  (`timeout_seconds`, `manifest.py:230`), and only tests about the budget pass their own. Added with
  it: a `launch_delay` that holds a backend back before it runs, and a failure message
  (`_why_not_ready`) carrying the start's detail and the backend's output. No production code
  changed: 30 s is what a real App gets unless its manifest says otherwise. *Why* (the commit): "A
  fresh macOS runner takes about that long to bring up the first backend (a cold /usr/bin/python3), so
  the first start of the session raced the deadline: it passed on one run and timed out on the next
  (`unhealthy` at the concurrent start, before any stop)." *Pinned by:*
  `test_a_backend_slow_to_launch_becomes_ready_within_the_default_budget` (held back 3.5 s). *(v2.1:
  the failing run is in CI's history, run 2's macOS job, B22.)*
- **B14. The REST breakage check accepts new backend platform keys** (`28e5654`; §2 decision I, §6.4,
  §10 item 5). v1 expected oasdiff not to read `propertyNames`, and named the fallback. It does read
  it: the new keys were reported as `response-property-enum-value-added`. Built as the fallback, in
  the existing pattern rather than beside it: `_EXTENSIBLE_DISCRIMINATOR_PROPERTY_RE` gains the
  alternative `CanvasExtensionBackend\b.*\bartifacts/propertyNames\b`, so additions there are
  downgraded and every other response enum addition stays breaking. *Why* (the commit): "Platform keys
  are an extensible set, like the hook discriminator already allowlisted, so additions there are
  downgraded; every other response enum addition stays breaking." *Pinned by:*
  `test_backend_artifact_platform_additions_are_downgraded_and_nothing_else` (cross-tests, in CI).
  The oasdiff check itself runs only for pull requests to `main`; it passed in the Implementer's
  local run at `28e5654`. *(v2.3: and in CI, on PR #1 at `5e3317f` against `v1.50.1` (B25): oasdiff
  reported both keys in the three responses that carry a manifest, and the pattern downgraded all six
  entries; §4.9 lists them.)*
- **B15. websockets 15.0.1 has `proxy`, so the item stays** (`759ffb2`; §6.1, §10 item 6).
  `bridge_websocket` passes `proxy=None` for a loopback target and `proxy=True` (websockets' default,
  the system's proxies) otherwise; loopback is one constant, `_LOOPBACK_HOSTS`, shared with
  `proxy_http`. *Pinned by:* `test_http_and_websocket_reach_a_loopback_backend_with_a_proxy_configured`.
  *(v2.4: both test the host against `_LOOPBACK_HOSTS` directly; `_is_loopback_host` is gone, R8.)*

**The branch and the PR split**

- **B16. Built in the reverse order, and PR 3 applies only after PR 2** (§1). v1: PR 3, then PR 2,
  then PR 1; disjoint files but two; each PR cherry-picks onto `main` alone. Built: PR 1, PR 2, PR 3,
  sharing five files (§1). Checked for this revision by cherry-picking each PR's commits alone onto
  the fork's `main` (`53a4bc5`) in a scratch clone: PR 1 and PR 2 apply cleanly; PR 3 conflicts in
  `tests/agent_server/canvas_extensions/test_canvas_extensions_manifest.py`, where its two tests
  follow PR 2's at the end of the file, and applies cleanly after PR 2. *Why:* the build recorded
  none for the order or the shared test files. For the PR split: cut PR 3 after PR 2, or resolve the
  one hunk (§10 item 10). *(v2.1: the as-built's cherry-picks agree, and resolving that hunk by
  keeping PR 3's block lets its other four commits apply, D-6. PR #1's description still lists PR 3
  as three commits, `759ffb2..28e5654`; the branch has five.)* *(v2.2: with `5e3317f` in PR 1 and
  `13e5904` in PR 2, re-checked at `5e3317f` the same way: PR 1 and PR 2 apply alone, PR 3 still only
  after PR 2. The PR split also leaves `c12f7b4` and `1f2b52d` behind, B25.)* *(v2.4: at `7f03b56`
  PR 3 applies alone too, R10.)*
- **B17. The merge `aff05f6`** (the header). The fork's `deep-reasoning` gained `ea51b3f` after the
  branch was cut: upstream's `tests.yml` asks for `blacksmith-2vcpu-ubuntu-2404`, a runner this fork
  does not have, so those jobs would wait forever; `ea51b3f` moves eight jobs to `ubuntu-24.04`.
  `aff05f6` merges it into the task branch so PR #1's CI can run. Against its first parent it changes
  those eight `runs-on` lines and nothing else, and it resolves nothing by hand. It is fork-only, and
  the PR split leaves it and `ea51b3f` behind. *Why* (`ea51b3f`'s message): "this fork has none, so
  those jobs would wait forever. Not for upstream: upstream pull requests are cut from main with only
  the feature's own commits." That the merge exists to run PR #1's CI is this design's reading.
- **B18. No per-PR draft onto `main` yet** (§4.9, §9 layer 3). v1: each PR's commits, cherry-picked
  onto the fork's `main`, in a draft PR, so the guards that run only for pull requests to `main` run
  as upstream would. Built: one draft (#1) against `deep-reasoning`. The main-only workflows are
  `agent-server-rest-api-breakage.yml`, `persisted-settings-compat.yml`, `typescript-client-ci.yml`,
  `typescript-client-integration-tests.yml` and `version-bump-guard.yml` (the SDK API breakage check).
  Of their guards, REST breakage, persisted-settings compatibility and the TypeScript client CI (so
  S2's 8 TypeScript tests) ran in the Implementer's local run at `28e5654`, and the Cartographer
  re-ran the persisted-settings guard and the TypeScript suite at `6f97bf3` (both pass, as-built D-5);
  the SDK API breakage check has no recorded run, nor do the TypeScript integration tests. *Why*
  (PR #1's Notes): "Some
  upstream checks run only on pull requests to main; the REST breakage and TypeScript client checks
  were run locally (above)." That the drafts come with the PR split is this design's reading (§10 item
  11). *(v2.2: superseded for CI by B25: the main-only guards now run on PR #1, with the caveats the
  Gate B section names.)* *(v2.5: the PR split opened no drafts onto `main`. Its stack of seven drafts
  is based on `deep-reasoning`, and the main-only guards ran on every level through B25.)*

**Found by the as-built (v2.1)**

B20 and B21 came from the Cartographer's reading of the code and are checked against it here, not
run; B22 corrects the as-built from CI's records.

- **B20. The set route's 500 carries the agent's message unmasked** (as-built D-9; §4.7, §10 item
  16). As v1 specified, an `ACPRequestError` with -32603 leaves `_apply_config_options` unchanged
  (mirroring `set_acp_model`), and no `except` in the set route catches it, so upstream's
  unhandled-exception handler answers 500 with `{"detail": "Internal Server Error", "exception":
  str(exc), "error_id": …}` (`api.py:611–640`): the agent's own message, never passed through the
  conversation's secret masker, which the 422 refusal path applies. `switch_acp_model`'s route does
  the same upstream. *Why:* v1 specified the pass-through ("as for `switch_acp_model`") without
  considering masking; this design's reading. *Pinned by:* nothing. *(v2.2: pinned as it is by
  `test_an_internal_error_from_the_agent_is_a_500_carrying_its_message_unmasked`, B24: `detail` is
  "Internal Server Error" and `exception` the agent's sentence verbatim, a registered secret
  included.)*
- **B21. A start value for a built-in provider's session mode is overwritten** (as-built §4.2; §4.4,
  §7 item 6, §10 item 15). v1's order at the start, kept by the build, is model, then option values,
  then the existing `set_session_mode`. For a known provider that call sends `acp_session_mode` or the
  provider's default permission mode (`acp_agent.py:3554–3563`), so where the provider's `mode` config
  option is its session mode, a start value for `mode` does not survive; the claude-code preview
  reports `mode=bypassPermissions` (as-built §6.3, from CI's log). dr-acp is no known provider and gets
  no such call. *Why:* v1's order was written for the model; the interaction was not considered.
  *Pinned by:* nothing; not run.
- **B22. The macOS failures behind B12 and B13 are in CI's history, inside two runs that never
  finished** (correcting the as-built's §2.4 and §7 item 2, which read them as absent). The fork's
  `tests.yml` runs 1 and 2 still show `queued`, because their jobs on the Blacksmith runner never
  started (before `ea51b3f`); their GitHub-hosted jobs did run. Run 1
  ([37088961132](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37088961132),
  `28e5654`), job `macos-app-backend-tests`: 2 failed, 170 passed, both
  `test_prepare_start_logs_stop_and_preserve_data` and `test_failed_start_cleanup_and_unsupported_states`
  with `PermissionError: [Errno 1] Operation not permitted` from `os.killpg(pgid, 0)` in
  `_group_alive`, B12's account. Run 2
  ([37090131688](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37090131688),
  `0e24793`), the same job: 1 failed, 176 passed, `test_prepare_start_logs_stop_and_preserve_data`
  with `assert 'unhealthy' == 'ready'` at the concurrent start, B13's account; run 3 (`aff05f6`)
  passed with the 3 s budget unchanged, the flake the commit describes. Run 4 (`6f97bf3`) passed. Read
  through the GitHub MCP tools for this revision. `darwin-amd64` (Intel, Rosetta) never ran.

**Landed after the as-built (v2.2)**

- **B23. The panel icon route is documented as a PNG or SVG image** (`13e5904`; §5.2, A.8). The route
  returned a `FileResponse` without declaring it, so FastAPI documented its `200` as
  `application/json` with an empty schema, which the weak-schema ratchet (`make test-server-schema`)
  refuses as a new weak location. Built: `response_class=FileResponse`, and the `200` documented as
  `image/png` and `image/svg+xml`, each `{"type": "string", "format": "binary"}`. *Why* (the commit):
  "Declare the response class and the two image media types the route serves, each a binary string,
  instead of allowlisting the pointer." It also shows that v2 overstated where the ratchet runs: the
  agent-server suite tests the ratchet's logic only, on synthetic documents; the ratchet over the real
  schema is `server.yml`'s, main-only (Gate B evidence). *Pinned by:*
  `test_openapi_contract.py::test_panel_icon_route_is_documented_as_a_png_or_svg_image`, in CI.
- **B24. The four untested status rows are pinned** (`5e3317f`; §4.7, §4.10). In `test_acp_router.py`:
  the set route's 500 for -32603 (B20, as it is), its 400 `inactive_service` (reachable only in a
  race: the lookup restarts a closed service, so the test hands the route a service closed after its
  lookup), the preview's 422 for a dangling MCP reference (`detail.dangling_mcp_server_refs`), and its
  502 for an authentication failure, never 401. The scripted agent gains `--set-error SENTENCE`
  (every `session/set_config_option` answers -32603 with it) and `--auth-required` (`session/new`
  answers ACP's -32000), and the route harness answers an unhandled error with the 500 handler's body
  (`ASGITransport(raise_app_exceptions=False)`), as a deployed server does. *Why* (the commit): to pin
  the rows; no production code changed. *Pinned by:* the four tests, named in the Gate B section.
- **B25. Upstream's main-only guards run on the fork's pull requests** (`1f2b52d` on `deep-reasoning`,
  merged into the branch as `c12f7b4`; §4.9, §10 item 11). Fork-only: the `pull_request` branch
  filters of `agent-server-rest-api-breakage.yml`, `persisted-settings-compat.yml`,
  `typescript-client-ci.yml`, `typescript-client-integration-tests.yml` and `version-bump-guard.yml`
  now admit the fork's branches; nothing else changes. *Why* (its message): "This fork's feature pull
  requests target deep-reasoning, or a feat/* branch when stacked, so those guards never ran on them
  … Not for upstream." Left out: `server.yml`, whose schema check is the ratchet (B23), because the
  same workflow builds and pushes images (the Conductor's account). The merge `c12f7b4` changes those
  five lines against its first parent and nothing else; the PR split leaves both behind.
- **B26. Every 5xx answer's body is "Internal Server Error"** (§4.7, §7 item 2). v1 and v2 wrote that
  the preview's 502 `detail` names why. Upstream's handler for an `HTTPException` with status 500 or
  above (`api.py`, `_http_exception_handler`) answers `{"detail": "Internal Server Error",
  "exception": "<status>: <the route's detail>"}`; so the preview's 501, 502 and 504 and the set
  route's 504 carry their message under `exception`, for example `{"detail": "Internal Server Error",
  "exception": "502: [-32000] Authentication required"}`. An unhandled exception (the set route's 500)
  answers `{"detail": "Internal Server Error", "exception": str(exc), "error_id": …}`. C2 reads no
  `detail` on 501, 502 or 504 (§7 item 2), so nothing changes but the sentence. *Why:* upstream's
  handler, which v1 did not read; the Conductor's correction. *Pinned by:*
  `test_the_preview_answers_an_authentication_failure_with_502_not_401`.

**Size**

- **B19. Size** (§3.1 item 12). `git diff --numstat ea51b3f..6f97bf3` *(v2.2: at `5e3317f`, `git diff
  1f2b52d..5e3317f`, 4,837 added and 155 removed: B23 adds 22 lines to PR 2 and replaces 1, 10 of
  them code; B24 adds 87 to PR 1 and replaces 2, all tests and the scripted agent's two flags)*:

  | Part | Spec | Built, added (removed) |
  |---|---|---|
  | Commands and options: `acp_models.py`, the event, `acp_agent.py`, `local_conversation.py`, `request.py`, the visualizer | ≈200 | 719 (27) |
  | Preview and routes: `acp_preview.py`, `acp_router.py`, `conversation_service.py`, `event_service.py`, `api.py`, `conversation_router.py`, one capability | ≈150 | 450 (85, of which 84 moved into `_resolve_launch`) |
  | Header panels: `manifest.py`, `installed.py`, `canvas_extensions_router.py`, one capability | ≈60 | 225 (12) |
  | macOS backends: `backend.py`, `proxy.py`, the platform names, the REST check, the macOS job | ≈30 | 109 (18) |
  | TypeScript client | ≈100 | 200 (1) |
  | The live file's line in `acp-live-tests` | — | 2 |
  | Tests: Python | ≈350 in all | 2,572 (11) |
  | Tests: the scripted ACP agent | | 299 |
  | Tests: TypeScript | | 155 (1) |
  | **Total** | **≈0.9k, ≈3 h at Gate C** | **4,731 (155); 3,937 non-blank added; about 16 h at Gate C** |

  By PR: PR 1 3,754 (114), PR 2 572 (12), PR 3 405 (29). Tests are 97 new Python test functions (141
  cases) and 8 TypeScript ones. The build recorded no reason for the growth. This design's reading: the tests are
  8.6 times the estimate because every test that crosses the ACP boundary runs a real agent process
  (the 299-line scripted agent), many through a whole conversation or the agent-server's routes over
  HTTP, and the two macOS fixes brought four more backend tests and a fixture rewrite (`0e24793`,
  `6f97bf3`: 143 lines of tests added); the code is 3.2 times the estimate because v1 itself was
  larger than the spec and estimated nothing: the preview through the real start-up path
  (`_resolve_launch`), the ordered emitter and the agent-swap helper, the proxy fix, the macOS job
  and the REST allowlist (decision G, B14), the icon route and the two capability strings. The Scout
  and the Refactorer, after Gate B, are where it shrinks. *(v2.4: they took 518 lines out, to 4,319
  added and 163 removed at `7f03b56`: the refactor section's size table.)*

---

## 4 · PR 1: ACP session controls

### 4.1 The data

Three stable DTOs, added to `openhands/sdk/agent/acp_models.py`, the module that exists so the
agent-server can import ACP shapes without importing `ACPAgent` (its docstring): `ACPAvailableCommand`
(with `ACPCommandInput`), `ACPConfigOption` (with `ACPConfigOptionValue`), and `ACPSessionControls`,
which holds a list of each. One event, `ACPSessionControlsEvent`, in a new
`openhands/sdk/event/acp_session_controls.py`, exported from `openhands.sdk.event`. Full signatures:
Appendix A.1 and A.2. *(v2, §3.2 B10: the default visualizer gives the event an entry, "ACP Session
Controls".)*

What one event looks like, for D1's session in the namespace `router` before its first prompt:

```json
{"kind": "ACPSessionControlsEvent", "id": "5f0c…", "timestamp": "2026-10-02T14:22:31.120417",
 "source": "agent", "parent_id": null,
 "available_commands": [
   {"name": "summarize-then-rank", "description": "comparing many courses",
    "input": {"hint": "what to compare"}}],
 "config_options": [
   {"id": "namespace", "name": "Namespace", "type": "select", "current_value": "router",
    "description": "The namespace this conversation runs in. Fixed after the first message.",
    "category": null,
    "options": [{"value": "root", "name": "root", "description": null, "group": null},
                {"value": "router", "name": "router", "description": null, "group": null}]}]}
```

*(v2, §3.2 B2)* That is the model's full dump, which the preview's and the set route's answers
match. The events search and the WebSocket dump events with `exclude_none=True`, so there the
`null` fields (`parent_id`, `category`, each value's `description` and `group`, a command's absent
`input`) are left out; a client reads a missing one as `null`.

**Normalization at the boundary** *(v2, §3.2 B1; v1's rules, written for untyped input, are
replaced)*. `from_protocol` takes ACP 0.12.1's typed objects. Before S2 sees an update or a response,
ACP's own schema has already dropped every list item that fails validation (`skip_invalid_items`)
and turned a malformed command `input` into `None` (`salvage_on_error`); and 0.12.1 lists the two
option types directly, with no `RootModel` around them. So:

- A command without a `description`, or of any shape ACP rejects, never arrives. A command with an
  empty `name` is dropped by S2 (`ACPAvailableCommand.from_protocol` returns `None`). `input` is read
  through 0.12.1's `RootModel` (`raw.input.root.hint`); a non-string hint arrives as no input.
- An option of a type other than `select` or `boolean` never arrives, and nothing logs it. `select`:
  each `SessionConfigSelectOption` becomes an `ACPConfigOptionValue`; each `SessionConfigSelectGroup`
  contributes its options with `group` set to the group's `name`, so a client always gets one flat
  list. `boolean`: `options` is empty and `current_value` is the boolean. `category` keeps ACP's
  string categories (`mode`, `model`, `model_config`, `thought_level`) and is `None` for anything
  else.
- A dropped entry never fails the update that carried it.

### 4.2 Recording, in the bridge

`_OpenHandsACPBridge` keeps one `ACPSessionControls` per ACP session id, replaced on every change and
never mutated:

- **The first line of `session_update` after the idle-clock reset** is
  `if self._record_session_controls(session_id, update): return`. It handles
  `AvailableCommandsUpdate` (→ `record_available_commands`) and `ConfigOptionUpdate`
  (→ `record_config_options`) and returns `False` for anything else. Today both update types fall
  through to the final `else` and are logged at debug (`acp_agent.py:1547–1548`).
- **Responses are recorded too**: the `configOptions` of the `session/new` and `session/load`
  responses, and of every `session/set_config_option` response, S2's own and the model path's.
- **Per session id, not only the root's.** Two reasons. The root session id is not yet on the agent
  when D1's commands arrive: ACP Python 0.12.1 resolves `new_session` as soon as the response arrives,
  and the notification that follows may be handled before `_init` returns (D1 §5.4 rule 5). And with
  S1, child sessions may report commands of their own. Only the root's are published (§4.3).
- **Masked like tool calls.** Each record passes the agent-supplied text through `_mask_value` before
  it is stored, so a command description that echoes an injected credential never reaches the
  persisted event stream (the same rule as `_mask_tool_call_entry`, `:1406`). *(v2.4, R2: both
  records parse their entries, then hand them to one helper,
  `_store_session_controls(session_id, field, entries)`, which masks them as dumped and stores a
  validated copy of the session's snapshot with that one list replaced.)*
- **One writer.** Every record runs on the portal loop's thread: notifications are handled there, and
  so are `_init` and the coroutines that `set_acp_config_option` and the model path schedule. Readers
  on other threads read a snapshot reference, which is never mutated after it is stored.
- **A commands-reported flag per session** (a `threading.Event`), set by
  `record_available_commands`, is what the preview waits on (§4.6).
- After each record the bridge calls `on_session_controls_changed()`, which the agent binds (§4.3).
  *(v2, §3.2 B6: through `_notify_session_controls_changed`, which logs a failing publish at warning
  and swallows it, so a failing sink never fails the update; the agent binds a publisher that holds
  it through a `weakref`.)*

### 4.3 Publishing: the root session's controls, in order

`ACPAgent._publish_session_controls()` turns the root session's snapshot into an event:

```python
def _publish_session_controls(self) -> None:
    if self._on_session_event is None or self._session_id is None:
        return
    if self._starting_session:
        return
    with self._session_controls_lock:
        controls = self._client.session_controls(self._session_id)
        if controls == self._published_session_controls:
            return
        self._published_session_controls = controls
        self._on_session_event(ACPSessionControlsEvent.from_controls(controls))
```

It is called by the bridge after every record, and once by `_start_acp_server` itself, right after
`self._session_id` is assigned and `_starting_session` is cleared. Every start goes through
`_start_acp_server`: the first run, a resume after an agent-server restart, and the restart after a
drain timeout (`_restart_session_after_drain_timeout`, `:3524`), which keeps the old session id
while the new process starts. `_starting_session` is set at the top of `_start_acp_server` (and
cleared in a `finally`), so nothing is published from a half-started session, whose root id may
still be the previous process's. *(v2, §3.2 B6: the flag and the post-start publish stay in
`_start_acp_server`; the body it wraps moved unchanged into `_launch_acp_session`, which binds the
publisher, `_bind_session_controls`, right after it creates the bridge.)*

**Invariant: the last `ACPSessionControlsEvent` persisted for a conversation equals the root
session's newest snapshot, one emitter round-trip later.** Why it holds:

1. *Nothing is lost.* A record made while `_starting_session` is set (or before the root id is known)
   happens before the post-start publish reads the snapshot, so that publish includes it. A record
   made after the flag is cleared publishes itself.
2. *Nothing is reordered.* Under the lock, each publish reads the newest snapshot, compares and
   submits; so submissions happen in snapshot order. The emitter is first-in first-out (one worker).
   So the persisted order is the snapshot order, and event timestamps, taken at construction under
   the same lock, agree with it.
3. *No repeats.* A publish that finds the snapshot equal to the last one submitted submits nothing:
   for example the post-start publish after a start in which every record already published itself.
   *(v2, §3.2 B4: and an agent's first publish compares with nothing, so every start persists one
   event, empty lists included. v2.1: that event can carry no commands and be followed by the
   agent's menu in a second event; the invariant holds, the last event is the newest snapshot.)*

**The emitter.** `LocalConversation._ensure_agent_ready` sets
`self.agent._on_session_event = self._emit_event_from_any_thread` before it calls `init_state`, for
an `ACPAgent` only. `_emit_event_from_any_thread(event)` submits one job to a
`ThreadPoolExecutor(max_workers=1, thread_name_prefix="conversation-events")`, created on first use;
the job runs `with self._state: self._on_event(event)`, so the event is persisted and reaches every
callback (in the agent-server, the WebSocket publisher and the webhooks) exactly like any other. No
deadlock: the portal thread only submits; the worker waits for the lock, which the synchronous
`run()` releases between steps and `arun()` releases while it awaits a prompt (the `astep` docstring,
`:4119–4127`). `close()` shuts the executor down with `cancel_futures=True`; a submit after that is
dropped with a debug log, and the next session start publishes again. *(v2, §3.2 B5: the executor is
created in `__init__`, its thread on the first submit; the job is upstream's
`_on_event_with_state_lock`; `close()` passes `wait=False` too.)*

**Without a `LocalConversation`** (an `ACPAgent` driven by hand, the preview, upstream's conformance
probes) nothing is emitted, and `ACPAgent.session_controls` is always readable.

**The agent swap.** `switch_acp_model`, and now `set_acp_config_option`, replace the conversation's
agent with a shallow `model_copy` that shares the live runtime (`local_conversation.py:1721–1803`).
The swap is extracted into one helper, `_replace_acp_agent`, which both call. It already rebinds the
copy's atexit cleanup and file-credential masking (`:1782–1784`); it now also calls
`new_agent._bind_session_controls()`, so the shared
bridge publishes through the copy. The lock is shared by the shallow copy; the last published
snapshot is copied with it.

### 4.4 Option values at the start

- **The request.** `StartConversationRequest.acp_config_options: dict[str, str | bool]`, default `{}`.
  Launch-only: it is added to the explicit exclude set where `_create_conversation` builds the stored
  record (`exclude={"agent_profile_id", "agent_launch_additions", "acp_config_options"}`,
  `conversation_service.py:1845`), so it is never written to `meta.json`; it lives in
  `base_state.json`, inside the agent. A `"model"` key is refused by the request's validator (422 from
  FastAPI). *(v2.4, R1: by the field's type, `ACPConfigOptionValues`, the annotated type both models
  share, whose `AfterValidator` runs `_check_config_option_id` on every key; same location and
  message.)*
- **The fold.** In `ConversationService._resolve_launch` (§4.6), after the agent is resolved: a
  non-empty dict with an agent that is not an `ACPAgent` raises `InvalidACPConfigOptions`, which the
  start route gains an `except` for (422, beside its `InvalidParentConversation`,
  `conversation_router.py:284–287`) and the preview route maps the same way; otherwise the agent
  becomes
  `agent.model_copy(update={"acp_config_options": {**agent.acp_config_options, **values}})`.
  `model_copy` skips validators, so the `"model"` check is repeated explicitly
  (`_check_config_option_id`). *(v2.4, R1: not any more. Both dicts the fold merges were validated
  when their models were built, and nothing between changes them, so the merged dict holds only
  checked keys.)*
- **The agent.** `ACPAgent.acp_config_options: dict[str, str | bool]`, default `{}`, whose validator
  refuses `"model"`. Old `base_state.json` files load with the default. *(v2.4, R1: typed
  `ACPConfigOptionValues`, which refuses `""` and `"model"`.)*
- **Applying them.** In `_start_acp_server._init`, on the fresh-session path only, in this order:
  `new_session` → record the response's options → the existing model call (`_maybe_set_session_model`,
  now passed the bridge's recorder) → `_apply_config_options(conn, session_id,
  self.acp_config_options, …)` → the existing `set_session_mode`. On the `session/load` path: record the
  response's options, and apply nothing.
- **`_apply_config_options`** sets each value in the dict's order (JSON object order, which the
  request preserves), recording every response, because a set may change other options. An
  `ACPRequestError` with code -32603 propagates unchanged, as it does from `set_acp_model` (the
  retriable class, `_RETRIABLE_SERVER_ERROR_CODES`). Any other `ACPRequestError` becomes
  `ACPConfigOptionRejectedError(config_id, value, message)`, whose `str()` is the agent's own message,
  masked. That includes method-not-found: the user asked for an option the agent cannot take.
- **A refusal at the start.** `ACPConfigOptionRejectedError` leaves `_start_acp_server`; `init_state`'s
  existing handler (`:2312–2343`) emits `ConversationErrorEvent(code=…, detail=…)`, sets the
  conversation to ERROR, cleans up and re-raises. `_classify_acp_init_error` gains a first branch for
  it, returning `"ACPConfigOptionRejected"`, and `_acp_error_detail` already returns `str(exc)` for a
  non-ACP exception, so the detail is the agent's sentence, redacted and masked. The first message is
  persisted but never prompted.
- **Time.** All of this runs inside `_init`, under the existing `acp_startup_timeout` (90 s).
- *(v2.1, §3.2 B21)* For a known provider, the existing `set_session_mode` after the values sends the
  bridge's permission mode, so a start value for that provider's `mode` option, where it is the
  session mode, is overwritten (read, not run).

### 4.5 Setting an option

- **`ACPAgent.set_acp_config_option(config_id, value) -> ACPSessionControls`**, live sessions only,
  mirroring `set_acp_model`: `ValueError` for an empty id or `"model"`; `RuntimeError` before a session
  exists; runs `_apply_config_options` for the one value on the portal with
  `_ACP_CONFIG_OPTION_TIMEOUT` (30 s, overridable by the environment variable
  `ACP_CONFIG_OPTION_TIMEOUT`, like the module's other ACP timeouts); a timeout raises `TimeoutError`
  naming the option; a refusal raises `ACPConfigOptionRejectedError`; returns the root session's
  controls after the response is recorded (the record has already published them).
  Why 30 s and not `acp_prompt_timeout` (1,800 s), which `set_acp_model` uses: this call holds the
  conversation lock and answers a click in a picker.
- **`LocalConversation.set_acp_config_option(config_id, value) -> ACPSessionControls | None`**, mirroring
  `switch_acp_model`: `ValueError` if the agent is not an `ACPAgent`; `_check_config_option_id`; then,
  holding the state lock: if the session is live, the agent's call (a refusal propagates before
  anything is written); in every case `_replace_acp_agent({"acp_config_options": {…, config_id:
  value}}, live=live)`. Returns the controls when live, `None` when the value waits for the start.
- **`EventService.set_acp_config_option`** runs the conversation's call in the default executor, as
  `switch_acp_model` does (`event_service.py:2005–2025`), and raises `ValueError("inactive_service")`
  when the service has no conversation.
- **The route** answers `ACPConfigOptionSetResponse{applied, controls}` (§4.7).
- *(v2.4)* The code is as above at `7f03b56`, but no test now asserts the two set calls' refusals of
  `""` and `"model"`, nor the timeout's naming the option; the route's 400 for `model` (refused by
  `LocalConversation`'s check) and its 504 are asserted (the refactor section). *(v2.5, `76533fc`:
  the agent's refusals of both are asserted again, with the sentence, and the route's 422 for `""`;
  `LocalConversation`'s refusal of `""` is pinned only by the field test, through the check both call,
  and the timeout's wording stays unasserted.)*
- While a turn is running, a set still goes through (`arun` does not hold the lock across the prompt),
  and the agent decides: D1 refuses any change once its run has started; ACP allows others to accept.

### 4.6 The preview

**Shared resolution.** The steps of `_create_conversation` from reading `OH_RUNTIME_LAUNCHED_PROFILE`
through the deployment's system-message suffix (`conversation_service.py:1661–1744`: settings load,
profile resolution and its secret allow-list, `load_memory`, ACP skill sourcing, launch additions)
move unchanged into `ConversationService._resolve_launch(request) -> (request, launched_profile)`,
which also does S2's fold (§4.4). `_create_conversation` calls it first; the preview calls it too.
Worktree creation stays in `_create_conversation`: the preview uses the source workspace.

**`ConversationService.preview_acp_session(request) -> ACPSessionControls`:**

*(v2, §3.2 B3: before it, the route answers 501 when the agent-server's `conversation_runtime` is
`docker`.)*

1. `_resolve_launch(request)`; its errors map to statuses exactly as the start route maps them
   (`conversation_router.py:273–287`). A resolved agent that is not an `ACPAgent` raises
   `ValueError("preview needs an ACP agent")` (400).
2. Acquire a run slot (`RunSlot.acquire(self._run_semaphore)`); at the deployment's limit this raises
   `ConversationRunLimitExceeded`, which the app already answers with 429 (`api.py:564`).
3. In a worker thread, call the SDK's `preview_acp_session(agent, workspace, persistence_dir,
   secrets=request.secrets, cipher=self.cipher)` with
   `persistence_dir = self.conversations_dir / f"preview-{uuid4().hex}"`. That directory is a direct
   child of the conversations directory so the agent's npm cache resolves to the one every
   conversation shares (`_acp_npm_cache_dir`, `acp_agent.py:2527`: the persistence directory's
   parent), which keeps Claude Code's and Codex's previews warm. It never holds a `meta.json`, so the
   catalog loader skips it even if a crash leaves it behind (`_load_catalog_sync`, `:745–748`), and
   its name is not a UUID, so it can never collide with a conversation.
4. `finally`: delete the directory (`shutil.rmtree(…, ignore_errors=True)`) and release the slot.
   *(v2, §3.2 B7: with upstream's `safe_rmtree`, inside the slot.)*

**The SDK's `preview_acp_session`** (`openhands/sdk/conversation/acp_preview.py`, Appendix A.6):

1. The working directory is the request's `workspace.working_dir` when it exists, and otherwise an
   empty `persistence_dir / "workspace"`: what the agent would see in a fresh folder, without creating
   anything in the user's tree.
2. `ConversationState.create(id=uuid4(), agent=agent, workspace=…, persistence_dir=…, cipher=…)`;
   seed its secret registry the way `LocalConversation.__init__` does for a new conversation: the
   agent context's secrets, then `secrets` over them (`local_conversation.py:517–545`).
3. `agent.init_state(state, on_event=<discard>)`: the real start-up, option values included.
   *(v2, §3.2 B7: holding the state's lock, as a start does; step 1 also creates `persistence_dir`.)*
4. `agent.wait_for_available_commands(commands_wait_seconds)`: returns at once if the root session has
   reported commands at least once, otherwise after `PREVIEW_COMMANDS_WAIT_SECONDS` (2.0 s). Because
   D1 sends the commands for a newly chosen value before its `set_config_option` response (D1 §5.4
   rule 5), when option values were applied the right commands are already recorded by the time
   `init_state` returns. *(v2.1, as-built §4.7, read: an agent that sends a chosen value's commands
   after its `set_config_option` response is previewed with the commands it reported first.)*
5. Read `agent.session_controls`, then `agent.close_acp_session()` (sends `session/close` if the
   agent advertised `sessionCapabilities.close` in its `initialize` response, bounded by 2 s, errors
   logged and ignored), then `agent.close()`.
6. Any failure inside 3 becomes `ACPPreviewError(code, detail)`, with `code` from
   `_classify_acp_init_error` and `detail` from `_acp_error_detail` (redacted and masked). `close()`
   runs in every case.

**Cost.** One agent start-up per call, plus at most 2 s for an agent that never reports commands.
For dr-acp: its front process starts, reads the Library for the snapshot, and starts no worker (D1
§2 step 2); it writes no session index, since it writes that only at a first prompt (D1 §4.4).
Canvas should debounce previews (§7).

### 4.7 The REST surface

| Method and path | Body | Answer | Errors |
|---|---|---|---|
| `POST /api/acp/preview` (new `acp_router`) | `StartConversationRequest` (the start payload; fields that do not reach `session/new`, such as `initial_message`, are ignored) | `ACPSessionControls` | 400 not an ACP agent · 404 unknown profile · 422 invalid request, a dangling MCP reference (*v2.2:* tested; `detail.dangling_mcp_server_refs`), or a value the agent refused (`detail` is the agent's sentence) · 429 run limit · *(v2)* 501 the Docker runtime (§3.2 B3) · 502 the agent failed to start (`detail` names why; *v2.2, B26:* the body's `detail` is "Internal Server Error" and the reason is under `exception`, e.g. `502: [-32000] Authentication required`) · 504 start-up timed out (the same body shape) |
| `POST /api/conversations/{conversation_id}/acp/config-options` (new `conversation_acp_router`) | `ACPConfigOptionSetRequest{config_id, value}` | `ACPConfigOptionSetResponse{applied, controls}`: `applied: true` and the agent's resulting controls on a live session; `applied: false` and empty controls when the value waits for the session's start | 400 not an ACP conversation, the `model` option, or an inactive service (*v2.2:* tested, `detail` `inactive_service`) · 404 unknown conversation · 422 the agent refused (`detail` is its sentence verbatim, for example D1's `namespace is fixed once a conversation has started (it is 'router').`) · 504 no answer within 30 s (body as B26) · 500 the agent's internal error (-32603), as for `switch_acp_model` (*v2.2:* tested; the error is not caught, so upstream's handler answers 500 with `detail` "Internal Server Error" and the agent's sentence, unmasked, under `exception`, B20) |
| `POST /api/conversations` (existing) | gains `acp_config_options` | unchanged | 422 `acp_config_options` with an agent that is not ACP, or a `model` key |
| `GET /api/conversations/{id}/events/search?kind=openhands.sdk.event.acp_session_controls.ACPSessionControlsEvent&sort_order=TIMESTAMP_DESC&limit=1` (existing) *(v2: v1 wrote `kind=ACPSessionControlsEvent`; the filter takes the module-qualified class name, §3.2 B2)* | — | the newest controls event, if any, with its `null` fields left out | — |
| `GET /server_info` (existing) | — | `capabilities` gains `acp_session_controls_v1` | — |

Both new routers live in a new module, `openhands/agent_server/acp_router.py`, registered in
`api.py` after `conversation_router`. Keeping them out of `conversation_router.py` keeps S2 off the
lines S1's cancel route may add there (§8). *(v2: S1 put its cancel route in
`conversation_acp_router`, at `0cfb6a2`.)*

The preview's status codes come from the `ACPPreviewError.code`: `ACPConfigOptionRejected` → 422,
`ACPStartupTimeout` → 504, everything else (`ACPAuthRequired`, `ACPSpawnError`, `ACPInitError`) → 502.
The route never answers 401 for an agent's authentication failure, because Canvas reads 401 as its
own session to the agent-server having expired. *(v2.2, §3.2 B26: on a deployed server every one of
these 5xx answers has `detail` "Internal Server Error", with the route's message under `exception`.)*

### 4.8 The TypeScript client

Upstream's client takes its generated types from the pinned release's OpenAPI and checks in CI that
they are current (`scripts/check-agent-server-api.mjs`), so a PR cannot use types its server has not
released yet. It hand-writes them instead, as it does for client-ahead APIs (the meta-profiles client,
`endpoint-audit.config.json`'s `allowClientOnly`). Our fork's build regenerates the generated types
from our agent-server (`AGENT_SERVER_OPENAPI_PATH`, the spec's pins), where the same shapes then also
appear under their generated names.

- `src/models/acp-session-controls.ts` (new): the interfaces of Appendix B, field for field with the
  Python models.
- `src/events/types.ts`: `ACPSessionControlsEvent extends BaseEvent` with `kind:
  'ACPSessionControlsEvent'`, joined to the `ConversationEvent` union, and an
  `isACPSessionControlsEvent` guard, like the hand-written `ThinkEvent` there.
- `ConversationClient`: `previewAcpSession(payload)`, `setAcpConfigOption(conversationId, configId,
  value)`, and `getAcpSessionControls(conversationId)`, which calls `searchEvents` with
  `{kind: 'ACPSessionControlsEvent', sort_order: 'TIMESTAMP_DESC', limit: 1}` and returns that event's
  lists, or empty lists. `CreateConversationPayload` gains `acp_config_options?`. *(v2, §3.2 B2: the
  `kind` is `ACP_SESSION_CONTROLS_EVENT_KIND`, the module-qualified class name, exported from the
  package root; both readers return `acpSessionControlsOf(page.items)`, a helper in
  `src/events/types.ts`.)*
- `RemoteConversation`: `setAcpConfigOption(configId, value)` and `getAcpSessionControls()`, next to
  its `switchAcpModel`.
- `endpoint-audit.config.json`: an `allowClientOnly` entry for the two new routes, reason
  "client-ahead until the pinned release carries them", tracking our fork's draft PR. *(v2, §3.2 B10:
  without a `tracking` link.)*
- Tests beside the existing ones in `src/__tests__/api-clients.test.ts`, as for `switchAcpModel`.
  *(v2: and in `event-types.test.ts` and `index.test.ts`; they run in upstream's TypeScript client
  CI, which runs only for pull requests to `main`, §3.2 B18.)*

### 4.9 Upstream's guards, for PR 1

| Guard | What PR 1 does to it | Expected | Ran, at Gate B (v2) |
|---|---|---|---|
| REST breakage (oasdiff) | new routes; new optional request fields (`acp_config_options` on the start request and on `ACPAgent`); one new member of the event `oneOf` | additive routes and fields pass; the `oneOf` addition is downgraded to a notice by the script's own rule | oasdiff: locally at `28e5654`, passing. *v2.3:* CI on PR #1 at `5e3317f` against `v1.50.1` (attempt 2 of run 37146974332), passing, with the eight findings below. (v2.2's first attempt ran without oasdiff: the fork had no `v1.50.1` tag then.) |
| Weak-schema ratchet | eight new schemas, all fully typed | the allowlist stays exact | *v2.2:* not in CI (`server.yml`, main-only; B23); locally at `5e3317f` (the Conductor), passing, 62 allowlisted, after `13e5904` |
| Persisted settings | nothing in `ACPAgentSettings`, profiles or settings | untouched | *v2.2:* CI at `5e3317f` (B25) |
| SDK API breakage | additions only; `_apply_acp_model` and the other changed helpers are private | passes | *v2.2:* CI step skipped (no version change); locally at S2's head (the Conductor): one upstream error, none from S2 |
| Docstrings (MDX) | fenced code only in docstrings, no `>>>` | passes | CI, Check Docstrings |
| TypeScript client CI | hand-written types; generated file untouched | passes | *v2.2:* CI at `5e3317f`, 355 tests, and its integration tests (B25) |
| Endpoint audit | report-only; the two new routes are listed as client-ahead | report clean | CI |

*(v2.4)* At `7f03b56` every guard above ran again in CI on PR #1, with the same results: oasdiff's
eight findings below are unchanged, and the SDK API check is still skipped. The weak-schema ratchet
was run for this revision at `5e3317f` and `7f03b56` (its export and its quality check): it passes
at both, 62 allowlisted, and the two exports are identical.

**What oasdiff reported** (v2.3; [attempt 2 of run 37146974332](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37146974332/job/111276569669), S2 at `5e3317f` against
`v1.50.1`, oasdiff 1.19.1). Eight changes, all in 200 responses, all under the script's notice
"Additive oneOf/anyOf expansion or enum-value additions detected in response schemas. This is
expected for extensible discriminated-union APIs and does not break backward compatibility."; the
check exits 0. The log names schema paths, not routes; the routes here are read from S2's OpenAPI
document at `5e3317f`, where these are the only responses that reach `Event` or a manifest.

- `ACPSessionControlsEvent` added to the `oneOf` list of `Event`, twice (PR 1):
  - "the response body `oneOf` list": `GET /api/conversations/{conversation_id}/events/{event_id}`;
  - "the `items/anyOf[#/components/schemas/Event]/` response property `oneOf` list":
    `GET /api/conversations/{conversation_id}/events` (the batch read, a list of `Event | null`).
- `darwin-amd64` and `darwin-arm64` added as enum values of
  `backend/anyOf[subschema #1: CanvasExtensionBackend]/artifacts/propertyNames/` under the manifest,
  six entries (PR 3, downgraded by B14's pattern):
  - at `manifest/anyOf[subschema #1: CanvasExtensionManifest]/…`, twice each: the two routes that
    answer one `InstalledCanvasExtensionResponse`, `POST /api/canvas-extensions/install` and
    `GET /api/canvas-extensions/installed/{extension_name}`;
  - at `canvas_extensions/items/manifest/anyOf[subschema #1: CanvasExtensionManifest]/…`, once
    each: `GET /api/canvas-extensions/installed`.

Not reported, and nothing to report: the new routes and the new optional request fields, which are
not breaking. Not seen, either: the route C2 reads the controls from,
`GET /api/conversations/{conversation_id}/events/search`, declares no response schema (`{}`; it
answers a `JSONResponse`, as at `v1.50.1`), so oasdiff has nothing there to compare. That is
upstream's, and S2 does not change it.

On PR #2 (S1's, at `a3279be`; [attempt 2 of run 37146975811](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37146975811/job/111276572426)) the check reports the same
eight, except that each of the two `oneOf` entries also adds S1's `ACPSessionMessageEvent`,
`ACPSessionTextEvent` and `ACPSubagentEvent`, and passes.

### 4.10 Tests for PR 1

In upstream's layout. New files rather than additions to `tests/sdk/agent/test_acp_agent.py`
(10,258 lines, which S1 will edit): the tests stay out of S1's way. The outside world is the ACP agent
process, so tests that cross it run a real one: the scripted test agent of Appendix C, launched as
`acp_command=[sys.executable, <fixture>]`.

*(v2: as built at `6f97bf3`; the Gate B section maps them to properties. Every property v1 named
here is pinned, except two set-route rows of §4.7: the inactive service and -32603. v2.1: counts are
tests and, where they differ, cases after parametrization; PR 1 has 85 cases, PR 2 35, PR 3 21, 141
in all, every one passing in the Cartographer's run at `6f97bf3`. v2.2: with B23 and B24, PR 1 has 89
cases and PR 2 36, 146 in all, every one passing in CI at `5e3317f`; every row of §4.7 is pinned.)*

*(v2.4: at `7f03b56`, after the refactor (R4). Counted again for this revision, `test_acp_router.py`
had 17 tests at `6f97bf3` and 21 at `5e3317f`, not v2.1's 18 and v2.2's 22; the case counts were
right. Now PR 1 has 56 tests and 68 cases, PR 2 11 and 29, PR 3 7 and 14: 111 cases in all, every
one passing in CI at `7f03b56`. What each removed test's property rests on now is the refactor
section's property tables.)*

*(v2.5: at `d938c90`, PR 1 has 56 tests and 69 cases: `76533fc` renamed two tests and added the
router's `empty-id` case, as the table now names them. In the stack, the scripted agent and the
models, event, recording, publishing and emitter tests are in #5; the option-value and live-set
tests, the field test, the swap test and
`test_controls_reported_while_the_session_starts_are_published_once_it_started` (it needs a start
value) in #6; the preview and live files in #7; the router tests in #8; the TypeScript tests in
#9.)*

| File | Tests at `7f03b56` (v2.5: and `d938c90`) |
|---|---|
| `tests/fixtures/acp/scripted_agent.py` (new, 310 lines, with `--set-error` and `--auth-required`) and `tests/conftest.py` (`SCRIPTED_ACP_AGENT`, `scripted_acp_command`, `acp_request_log`; *v2.4, `cd5db00`:* `wait_until`, `controls_events` and the `scripted_conversation` fixture, which starts a `LocalConversation` on the scripted agent, or resumes one by `conversation_id`, and closes it after) | the scripted agent of Appendix C and its helpers (§3.2 B9) |
| `tests/sdk/agent/test_acp_models.py` (4) | `test_command_hint_is_read_through_the_root_model`, `test_grouped_select_is_flattened_with_each_value_keeping_its_group`, `test_ungrouped_select_keeps_values_in_order_without_a_group`, `test_a_category_that_is_not_an_acp_string_category_becomes_none` |
| `tests/sdk/event/test_acp_session_controls_event.py` (3) | `test_event_round_trips_through_json_as_its_own_kind`, `test_event_renders_as_one_line_of_command_names_and_option_values`, `test_an_empty_event_still_renders_one_line` |
| `tests/sdk/agent/test_acp_session_controls.py` (17 tests, 18 cases) | recording and publishing: `test_controls_reported_while_the_session_starts_are_published_once_it_started`, `test_commands_reported_after_session_new_answered_are_published`, `test_each_session_keeps_its_own_controls_and_only_the_root_is_published`, `test_entries_the_protocol_cannot_parse_are_dropped_not_raised`, `test_session_updates_of_both_kinds_are_recorded_and_not_routed_on`, `test_agent_supplied_text_is_masked_before_it_is_stored`, `test_concurrent_publishes_keep_snapshot_order_and_end_on_the_newest`, `test_nothing_is_published_while_a_session_is_starting`; values at the start: `test_start_values_reach_the_agent_after_session_new_and_before_the_prompt`, `test_values_are_set_in_order_and_every_response_is_recorded`, `test_a_refused_start_value_ends_the_start_and_no_prompt_is_sent`, `test_after_a_successful_load_no_value_is_reapplied`, `test_after_a_fallback_to_a_fresh_session_every_value_is_reapplied`; the model: `test_the_model_option_and_an_empty_id_are_refused_in_the_field_and_by_a_live_set[model, '']` (*v2.5:* renamed by `76533fc`, which adds the live call), `test_a_model_switch_through_set_config_option_updates_the_published_model`; live sets: `test_a_live_set_returns_the_agents_new_controls`, `test_a_set_before_any_session_is_refused` |
| `tests/sdk/conversation/local/test_local_conversation_acp_config_option.py` (7) | `test_a_set_before_the_start_is_persisted_and_applied_at_the_start`, `test_a_live_set_is_persisted_and_survives_a_reload`, `test_a_refused_live_set_writes_nothing`, `test_the_agent_swap_hands_publishing_to_the_copy`, `test_a_portal_thread_event_during_a_synchronous_run_lands_after_the_step`, `test_events_emitted_after_close_are_dropped`, `test_events_from_other_threads_are_persisted_in_submission_order` |
| `tests/sdk/conversation/test_acp_preview.py` (6 tests, 9 cases) | `test_the_preview_equals_the_started_session_before_its_first_prompt[{}, fast, thorough]`, `test_session_close_is_sent_when_the_agent_advertises_it`, `test_session_close_is_not_sent_when_the_agent_does_not_advertise_it`, `test_an_agent_that_never_reports_commands_is_previewed_after_the_wait`, `test_the_agent_process_is_gone_afterwards[previewed, refused]`, `test_a_missing_working_directory_is_previewed_from_an_empty_scratch_directory` |
| `tests/agent_server/test_acp_router.py` (19 tests, 27 cases; *v2.5:* 28) | the preview: `test_the_preview_answers_for_each_way_of_naming_the_agent[agent, agent_settings, agent_profile_id]`, `test_the_preview_maps_each_failure_to_its_status[refused-value, startup-timeout, spawn-error, not-acp, values-not-acp]`, `test_the_preview_answers_an_authentication_failure_with_502_not_401`, `test_the_preview_of_an_unknown_profile_is_not_found`, `test_the_preview_of_a_profile_with_a_dangling_mcp_reference_is_refused`, `test_the_preview_holds_a_run_slot`, `test_the_preview_is_unavailable_in_the_docker_runtime`; the start: `test_the_start_folds_option_values_into_the_agent_only`, `test_a_started_session_reports_the_chosen_value_and_cleared_commands`, `test_the_start_refuses_option_values_it_cannot_apply[not-acp, model-option]`; the set route: `test_a_set_before_the_start_is_kept_for_it`, `test_a_live_set_answers_with_the_agents_controls`, `test_a_refusal_passes_the_agents_sentence_through`, `test_a_set_that_is_not_for_this_route_is_refused[not-acp, model-option, empty-id]` (*v2.5:* renamed by `76533fc`, which adds `empty-id`), `test_a_set_on_a_service_that_closed_after_its_lookup_is_a_bad_request`, `test_a_set_on_an_unknown_conversation_is_not_found`, `test_an_internal_error_from_the_agent_is_a_500_carrying_its_message_unmasked`, `test_a_set_the_agent_does_not_answer_times_out`; `test_server_info_announces_acp_session_controls` |
| `tests/agent_server/test_conversation_service.py` | *v2.4:* none; S2 no longer touches the file (`0d21d58`) |
| `tests/sdk/agent/test_acp_session_controls_live.py` (`pytestmark = pytest.mark.acp_live`, 3) | §9's live tier: `test_a_built_in_provider_can_be_previewed[6 providers]`, `test_the_preview_lists_what_the_started_session_lists`, `test_the_first_prompt_runs_with_the_chosen_values` (its waits now the shared `wait_until`, with its 30 s budget) |
| `clients/typescript/src/__tests__/` (7) | `api-clients.test.ts › ACP session controls ›` 4; `event-types.test.ts › ACPSessionControlsEvent ›` 2; `index.test.ts`, 1 |

---

## 5 · PR 2: conversation header panels

### 5.1 The manifest

```json
{"schema_version": 1, "name": "dr-library", "display_name": "Library", "version": "1.0.0",
 "entrypoint": "dist/index.js",
 "contributes": {"conversation_panels": [
   {"id": "decompositions", "title": "Decompositions", "icon": "dist/panel.svg",
    "tabs": [{"id": "browse", "title": "Decompositions", "path": "/"},
             {"id": "create", "title": "Create decomposition", "path": "/create"},
             {"id": "namespaces", "title": "Namespaces", "path": "/namespaces"},
             {"id": "tools", "title": "Tools", "path": "/tools"}]}]}}
```

That is C2's mock-up with the two fields every manifest already requires (`display_name`, `version`)
added, and it validates. The rules (Appendix A.8):

- **Panel:** `id` kebab-case; `title` non-empty (the header button's tooltip reads "Show " plus it, and
  it heads the panel); `icon` optional, a package-relative `.svg` or `.png` path, refused if absolute
  or containing `..`, and, at install and on every serve, refused if it resolves (symlinks included)
  outside the package or to anything but a regular file; `tabs` at least one. *(v2, §3.2 B11: and
  refused if the resolved file is not a `.svg` or `.png`, since the served media type comes from it.)*
- **Tab:** `id` kebab-case; `title` non-empty; `path` defaults to `/` and is `/` or an absolute
  kebab-case path, unique within its panel.
- **One namespace of contribution ids** per extension: page ids, panel ids and tab ids are all
  distinct (decision F). Page ids and paths stay unique as before. *(v2.4, R5: one type checks
  every id's form, `ContributionId`, a `str` whose `AfterValidator` is `_validate_contribution_id`;
  it types the `id` of pages, panels and tabs, upstream's page included, in place of three
  `_validate_id` validators.)*
- **Serialization:** `conversation_panels` is omitted from every dump when empty (decision F), so a
  manifest without panels dumps exactly as it does today.
- Manifests are still strict: an invalid panel makes the whole manifest invalid, as an invalid page
  does. On an agent-server without PR 2, pydantic's default drops the unknown key and the App installs
  without panels (C2's failure cell).

What a tab's path means is C2's to define in the host API; S2 only fixes its form. The intent, which
C2's mock-up implies: when a tab is selected, Canvas mounts the page the App registered under the
tab's id, with the tab's path as the mount context's `path`.

### 5.2 Serving

- **The manifest:** unchanged route. `GET /api/canvas-extensions/installed` and
  `…/installed/{name}` already return the validated manifest (`InstalledCanvasExtensionResponse.manifest`,
  `canvas_extensions_router.py:113`), now with `contributes.conversation_panels`.
- **The icon:** `GET /api/canvas-extensions/installed/{extension_name}/panels/{panel_id}/icon`, a
  `FileResponse` mirroring the bundle route (`:416–439`): containment re-checked on every request;
  404 for an unknown extension, an unknown panel or a panel without an icon; media type
  `image/svg+xml` or `image/png` from the suffix; headers `Cache-Control: no-cache`,
  `X-Content-Type-Options: nosniff` and
  `Content-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; sandbox`, so an SVG opened
  directly cannot run script in the agent-server's origin. Like the bundle, it is served for an
  installed App whether or not it is enabled, and it needs the session key, so Canvas fetches it the
  way it fetches bundles (with the key, into a blob URL,
  `canvas-extension-module-loader.ts:26–36`), not with a bare `<img src>`.
- **The capability:** `canvas_conversation_panels_v1`, appended in `build_server_info`, a different
  hunk from PR 1's, so each PR cherry-picks onto `main` alone.
- *(v2.2, §3.2 B23)* The icon route declares `response_class=FileResponse` and documents its `200` as
  `image/png` or `image/svg+xml`, a binary string, so the published OpenAPI holds no weak schema
  for it.

### 5.3 Tests for PR 2

*(v2: as built at `6f97bf3`; every property v1 named here is pinned.)*

*(v2.4: at `7f03b56`, after the refactor (R7): 11 tests and 29 cases, from 16 and 36.)* *(v2.5: at
`d938c90`, 11 tests and 33 cases: `d938c90` adds four rows to the malformed-panel table. All of PR 2
is #4.)*

| File | Tests at `7f03b56` (v2.5: and `d938c90`) |
|---|---|
| `tests/agent_server/canvas_extensions/conftest.py` (change) | `write_extension` takes `conversation_panels` |
| `tests/agent_server/canvas_extensions/test_canvas_extensions_manifest.py` (additions, 4 tests, 16 cases; *v2.5:* 20) | `test_a_header_panel_with_tabs_validates` (C2's manifest above), `test_a_malformed_panel_makes_the_manifest_invalid[panel-id, panel-title, no-tabs, tab-id, tab-title, relative-tab-path, uppercase-tab-path, trailing-slash, duplicate-tab-path, duplicate-default-tab-path, absolute-icon, traversing-icon, icon-type]` (*v2.5:* `panel-title`, `no-tabs`, `tab-title` and `duplicate-default-tab-path` added by `d938c90`), `test_pages_panels_and_tabs_share_one_id_namespace[page-and-panel, page-and-tab, two-panels, panel-and-tab, tabs-in-two-panels]`, `test_a_manifest_without_panels_dumps_exactly_as_before` |
| `tests/agent_server/canvas_extensions/test_canvas_extensions_entrypoint_containment.py` (additions, 1 test, 4 cases) | `test_an_icon_that_is_not_a_contained_image_makes_the_install_invalid[symlink-outside, missing, directory, symlink-to-other-type]` |
| `tests/agent_server/test_openapi_contract.py` (additions, 1) | B23: `test_panel_icon_route_is_documented_as_a_png_or_svg_image` |
| `tests/agent_server/test_canvas_extensions_router.py` (additions, 5 tests, 8 cases) | `test_list_and_get_return_the_conversation_panels`, `test_the_icon_route_serves_the_icon_with_its_type_and_safe_headers[an .svg, a .png]`, `test_the_icon_route_is_not_found_without_an_extension_panel_or_icon[unknown-extension, unknown-panel, no-icon]`, `test_the_icon_route_rechecks_containment_on_every_request`, `test_server_info_announces_conversation_panels` |

---

## 6 · PR 3: App backends on macOS

### 6.1 The changes

- **`BackendPlatform`** gains `"darwin-amd64"` and `"darwin-arm64"` (`manifest.py:88`, still one line).
- **`CanvasExtensionBackendManager.current_platform()`** maps `platform.system()` (`Linux`, `Darwin`)
  and `platform.machine()` (`x86_64`/`amd64` → `amd64`, `aarch64`/`arm64` → `arm64`) through two
  constant tables to the four names, and anything else to `None` (`backend.py:134–142`). An x86-64
  Python under Rosetta reports `x86_64` and gets the `darwin-amd64` artifact, which runs under
  Rosetta too.
- **Loopback is never proxied** (decision G):
  - the health probe opens its URL through `urllib.request.build_opener(urllib.request.ProxyHandler({}))`
    (a module constant) instead of `urllib.request.urlopen` (`backend.py:401–406`);
  - `proxy_http` (`docker_runtime/proxy.py`, used by the App-backend bridge and the Docker runtime)
    builds its `httpx.AsyncClient` with `trust_env=False` when the target host is loopback
    (`127.0.0.1`, `::1`, `localhost`);
  - `bridge_websocket` passes `proxy=None` to `websockets.connect` for a loopback target. The lock
    holds websockets 15.0.1; the Implementer confirms that release has the `proxy` parameter (the
    releases from 15 on default it to the system's proxies); if it does not, that release does not
    proxy and this item is dropped and recorded. *(v2, §3.2 B15: it has it; the item stays, with
    `proxy=True`, websockets' default, for any other target. Loopback is one constant,
    `_LOOPBACK_HOSTS`, for both `proxy_http` and `bridge_websocket`. v2.4, R8: each tests
    `urlsplit(…).hostname` against it directly.)*
  Non-loopback targets keep today's behaviour, so the Docker runtime is unchanged unless it too
  targets loopback, where the same bug applies.
- **Process groups:** nothing changes unless the macOS job shows otherwise. A backend starts in a new
  session and is stopped by group (`start_new_session=True`, `os.killpg`, `backend.py:507, 543–556,
  566–586`), which is POSIX. If the existing stop tests fail on macOS with `PermissionError` from
  `os.killpg` (macOS may refuse to signal a group whose members are all zombies, which is unverified
  here), then `_signal_group` ignores and `_group_alive` treats `PermissionError` as "gone": the group
  is ours and runs as our user, so a refusal means nothing of ours is left to signal. Either way the
  as-built records what the job showed. *(v2, §3.2 B12: the job showed it. Built narrower:
  `_group_exited(error)` is true for ESRCH everywhere and for EPERM only on macOS
  (`platform.system() == "Darwin"`); `_signal_group` and `_group_alive` re-raise any other `OSError`,
  so EPERM on Linux still surfaces.)*
- **The macOS CI job**, `macos-app-backend-tests` in `.github/workflows/tests.yml`, a copy of the
  `windows-tests` job's shape (`:252–327`): `macos-latest`, gated by `tj-actions/changed-files` on
  `openhands-agent-server/openhands/agent_server/canvas_extensions/**`,
  `openhands-agent-server/openhands/agent_server/docker_runtime/proxy.py`,
  `tests/agent_server/canvas_extensions/**`, `pyproject.toml`, `uv.lock` and the workflow itself; it
  runs `uv run pytest tests/agent_server/canvas_extensions`. The workflow runs for pull requests to
  any branch (`tests.yml:3–8`), so it runs on the fork's draft PRs and on PRs into `deep-reasoning`;
  public repositories get macOS runners free. *(v2: built so (`1d2627b`), with a 30-minute timeout,
  Python 3.13 and `uv sync --frozen --group dev`; at `6f97bf3` it ran 178 tests, 20 s of pytest in
  a 53 s job.)*

### 6.2 What PR 3 cannot check, for D3 and D5

- **A native arm64 executable must be signed, at least ad hoc**, or macOS kills it at `exec`. Linkers
  sign ad hoc by default; a post-link edit (`strip`, `install_name_tool`) removes it. D3's artifact
  build owns this. A script with a shebang has no such issue.
- **Ship both darwin artifacts** (D3): the universal desktop app (D5) may run on either architecture.
- **The backend's environment is sanitized** (`_SAFE_INHERITED_ENV`); on macOS `TMPDIR` is per-user and
  is on the allowed list, so declare it if the backend needs a temporary directory.

### 6.3 Tests for PR 3

*(v2: as built at `6f97bf3`; every property v1 named here is pinned, and B12 to B14 added five tests.)*

*(v2.4: at `7f03b56`, after the refactor (R9): 7 tests and 14 cases, from 10 and 21; PR 3 no
longer touches `test_canvas_extensions_manifest.py`.)* *(v2.5: unchanged at `d938c90`; all of PR 3
is #3.)*

| File | Tests at `7f03b56` (v2.5: and `d938c90`) |
|---|---|
| `tests/agent_server/canvas_extensions/conftest.py` (change) | `dead_http_proxy`: every proxy variable, upper and lower case, at a closed loopback port, `NO_PROXY` unset |
| `tests/agent_server/canvas_extensions/test_canvas_extension_backend.py` (additions and a fixture change, 5 tests, 12 cases) | `test_current_platform_names_the_artifact_for_each_system_and_machine[7 (system, machine) pairs]` (`platform` faked with `monkeypatch`; one row per mapping entry and per unknown branch); `test_a_backend_becomes_ready_with_a_proxy_configured`; B12: `test_a_refusal_to_signal_the_group_means_it_exited_on_macos_only[probe, signal]` (gone on macOS, a failure elsewhere), `test_stop_completes_when_macos_refuses_to_signal_the_exited_group`; B13: `test_a_backend_slow_to_launch_becomes_ready_within_the_default_budget`. The fixture `_write_backend_extension` declares all four platforms, keeps the manifest's 30 s health budget unless a test passes `timeout`, and takes a `launch_delay`; *v2.4:* `_prepared_backend` installs and prepares it for the three backend tests that start one; upstream's lifecycle tests run unchanged on the macOS job, their `ready` assertions now reporting `_why_not_ready` |
| `tests/agent_server/canvas_extensions/test_canvas_extension_bridge.py` (additions, 1) | `test_http_and_websocket_reach_a_loopback_backend_with_a_proxy_configured` |
| `tests/cross/test_check_agent_server_rest_api_breakage.py` (additions, 1) | B14: `test_backend_artifact_platform_additions_are_downgraded_and_nothing_else` |

### 6.4 Upstream's guards, for PR 3

`BackendPlatform` sits in a response schema (the manifest's `backend.artifacts` keys), which pydantic
emits as `propertyNames: {"enum": […]}`. The REST check treats a new response enum value as breaking
(`check_agent_server_rest_api_breakage.py:745–757`), but oasdiff 1.19.1 is not expected to read
`propertyNames` (it is a JSON Schema 2020-12 keyword outside what oasdiff diffs). If it does flag
`response-property-enum-value-added` there, the PR keeps the change and adds a narrowly scoped
allowlist pattern for `backend/artifacts` keys, beside the existing `HookConfig` one, since a platform
list is extensible by nature. This is the one guard in S2 I could not settle without running it.

*(v2, §3.2 B14: settled. oasdiff does read `propertyNames` and reported the two new keys as
`response-property-enum-value-added`. The fallback is built, as one more alternative in the existing
`_EXTENSIBLE_DISCRIMINATOR_PROPERTY_RE` (`CanvasExtensionBackend\b.*\bartifacts/propertyNames\b`)
rather than a pattern beside it; a test pins that only those keys are downgraded. The check itself
runs only for pull requests to `main`; it passed in the Implementer's local run at `28e5654`.)*
*(v2.3: and in CI, on PR #1 at `5e3317f` against `v1.50.1`; the six entries it downgraded are listed
in §4.9.)*

---

## 7 · The contract C2 builds against

Everything below is generic: C2 never needs to know the agent is dr-acp, and must not read `_meta`.

**Feature detection.** `GET /server_info` → `capabilities` contains `acp_session_controls_v1`
(commands, options, preview) and `canvas_conversation_panels_v1` (panels). Absent means the
agent-server predates S2: hide the option picker and agent commands, and show an App's missing panel
as C2's failure cell says.

**Home screen (no conversation yet).**

1. Build the start payload exactly as for `POST /api/conversations` (the same
   `agent_settings` or `agent_profile_id`, workspace and secrets), add the chosen values as
   `acp_config_options: {<config_id>: <value>}`, and `POST /api/acp/preview`. The answer is
   `ACPSessionControls`. Each call starts the agent once; debounce, and call again when the user
   changes an option or the workspace. For dr-acp that is a Python start-up and a Library read (not yet
   measured); budget the agent's start-up plus 2 s.
2. On 422 show `detail` (the agent's sentence); on 429, 502 or 504 show no agent commands and no
   picker, and let the user start anyway. *(v2, §3.2 B3: 501 too, which an agent-server in the
   Docker conversation runtime answers to every preview. v2.2, §3.2 B26: a 5xx body's `detail` is
   always "Internal Server Error", with the reason under `exception`, so show no reason from it.)*
3. Start with the same payload plus the same `acp_config_options`. They are applied before the first
   message reaches the agent. If the agent refuses one, the conversation ends in `ERROR` with a
   `ConversationErrorEvent` whose `code` is `"ACPConfigOptionRejected"` and whose `detail` is the
   agent's sentence; the first message is not sent.

**In a conversation.**

4. The current commands and options are the newest `ACPSessionControlsEvent`: from the WebSocket as
   they change, and on opening a conversation from
   `GET /api/conversations/{id}/events/search?kind=ACPSessionControlsEvent&sort_order=TIMESTAMP_DESC&limit=1`
   (the client's `getAcpSessionControls`). No event means the agent has reported nothing yet: an
   empty menu and no picker. Every event carries both lists in full; replace, never merge.
   *(v2, §3.2 B2 and B4, replacing two sentences above.)* The search's `kind` is the module-qualified
   class name: `kind=openhands.sdk.event.acp_session_controls.ACPSessionControlsEvent` (the
   TypeScript client's `ACP_SESSION_CONTROLS_EVENT_KIND`); the event's own `kind` field stays
   `ACPSessionControlsEvent`. No event means the session has not started yet; every start persists
   one. *(v2.1, §3.2 B4, replacing v2's "so an event with empty lists means the agent offers
   nothing".)* The first event after a start or a resume can list no commands and be followed,
   moments later, by the agent's menu; an agent that offers no commands looks the same and is never
   followed. So: the newest event is the state; show it and replace it when the next arrives; and an
   empty `available_commands` does not tell C2 whether the menu is still to come or there is none.
   Nothing in S2 lets C2 tell them apart (§10 item 14). In an event, from the search or the
   WebSocket, a `null` field is absent: read a missing `input`, `description`, `category` or `group`
   as `null`.
5. **The slash menu** lists `available_commands`: `/` + `name`, `description`, and `input.hint` as the
   placeholder for the text after the name when `input` is present. Choosing one inserts
   `/<name> ` in the message box; the user's message is sent as usual and S2 passes its text through
   unchanged. An empty `available_commands` means the agent offers none now: dr-acp clears its
   commands when the first message is accepted, which reaches Canvas as an event before the run's
   output. *(v2: that order is expected, not pinned. The agent-server runs an ACP conversation with
   `arun()`, which releases the lock while the prompt is in flight, so the emitter can persist the
   event during the run; no test orders it against the run's output, and under a synchronous `run()`
   it lands after the step (`test_a_portal_thread_event_during_a_synchronous_run_lands_after_the_step`).
   Follow the newest event whenever it arrives.)*
6. **The option picker** shows `config_options` except the one whose `id` is `"model"` (the existing
   model picker owns it; S2 refuses to set it). A `select` shows `options` by `name` (grouped by
   `group` when present) with `current_value` selected; a `select` with a single value is fixed, which
   is how dr-acp says its namespace can no longer change; a `boolean` is a toggle (none arrive today,
   because the bridge does not advertise boolean support). *(v2.1, §3.2 B21: for the built-in
   providers a pre-start value for a `mode` option that is the session mode is overwritten by the
   bridge's own session mode, read, not run; §10 item 15.)*
7. **Changing an option:** `POST /api/conversations/{id}/acp/config-options` with
   `{"config_id", "value"}` → `{applied, controls}`. On a live session, `controls` is the agent's new
   state (the event follows too). Before the session starts, `applied` is `false` and the value is
   kept for the start. A 422's `detail` is the agent's sentence; show it as it is.

**Header panels.**

8. `GET /api/canvas-extensions/installed` → each `manifest.contributes.conversation_panels` (absent
   when the App has none, or on an agent-server without the capability). Each panel: `id`, `title`,
   `icon` (or `null`), `tabs[]` of `{id, title, path}`.
9. The icon is `GET /api/canvas-extensions/installed/{name}/panels/{panel_id}/icon`, fetched with the
   session key like the bundle; 404 means draw a default.
10. Tab ids are contribution ids: the App registers each tab's page with `host.registerPage(<tab id>,
    mount)`. Ids are unique across the App's pages, panels and tabs, and are stable, so they can key
    the selected tab and pins. A tab's `path` is `/` or an absolute kebab-case path, unique within its
    panel; what Canvas does with it is C2's host API (the mount context's `path`, by C2's mock-up).
11. Not in S2, and C2's own: the button and its "Show …" tooltip, one right-hand panel at a time,
    `conversationId` in the mount context, the narrow-window page.

---

## 8 · Where S2 and S1 touch the same code

S1 is being designed at the same time; these are the places its spec (S1 in TASK-1) and this design
both touch, and the rule that lets either land first. The single shared design point is item 6; the
rest are textual neighbours.

| # | Place | S1 (from its spec) | S2 | Either order |
|---|---|---|---|---|
| 1 | `acp_agent.py` imports from `acp.schema` | its shim's types | `AvailableCommandsUpdate`, `ConfigOptionUpdate` | adjacent lines in one import list; the second to land merges by hand |
| 2 | `_OpenHandsACPBridge.__init__` | per-session routing state | `_session_controls`, `_commands_reported`, `on_session_controls_changed` | appended attributes; no shared name |
| 3 | `_OpenHandsACPBridge.session_update` | routes every update by session, and handles the shim's three unstable types | one line, first after the idle-clock reset: `if self._record_session_controls(session_id, update): return` | S2's line handles only `AvailableCommandsUpdate` and `ConfigOptionUpdate`, for any session id, and returns before any routing; S1's routing below it never sees those two types. Whoever lands second keeps the line first. |
| 4 | `_start_acp_server._init` | builds the shim's connection class instead of `ClientSideConnection` (`:3070`) and calls `initialize` with client capabilities (`:3090`) | reads `init_response.agent_capabilities.session_capabilities.close` after `initialize`; records the `session/new` and `session/load` responses' options; applies option values after the model call | S2 reads the response object, not the call, so S1 can change the call freely; S2's options block sits after the model block, away from S1's lines |
| 5 | `ACPAgent` private attributes | possibly its own | `_on_session_event`, `_session_controls_lock`, `_published_session_controls`, `_supports_session_close`, `_starting_session` | appended; no shared name |
| 6 | **Emitting events outside a turn** | must persist child traffic that arrives after the parent's turn ended ("persisted, not dropped") | `ACPAgent._on_session_event` and `LocalConversation._emit_event_from_any_thread`: an ordered, lock-taking, single-worker emitter (decision B) | **One primitive, not two.** Whoever lands first builds it with these names and semantics (§4.3, Appendix A.3 and A.4); the other uses it. S1's events are a sequence, not latest-wins state, which the FIFO order serves too. For the Conductor to confirm with S1's designer. |
| 7 | `LocalConversation` | none expected | `_emit_event_from_any_thread`, its wiring in `_ensure_agent_ready`, `set_acp_config_option`, and `_replace_acp_agent` extracted from `switch_acp_model` | only S2 edits these lines, unless item 6 lands with S1 |
| 8 | `openhands/sdk/event/__init__.py` | its two event kinds | `ACPSessionControlsEvent` | adjacent import and `__all__` lines |
| 9 | Routes | `POST /api/conversations/{id}/acp/sessions/{session_id}/cancel` | `acp_router.py` with `acp_router` and `conversation_acp_router` (prefix `/conversations/{conversation_id}/acp`), registered in `api.py` | S1's route fits `conversation_acp_router`; if S1 puts it in `conversation_router.py` instead, nothing conflicts but one `include_router` line in `api.py` |
| 10 | `EventService` | `cancel_acp_session` (expected) | `set_acp_config_option` | adjacent methods |
| 11 | `ServerInfo.capabilities` | possibly one string | `acp_session_controls_v1` in the default list | adjacent list entries |
| 12 | TypeScript client | the cancel call, its event types | §4.8 | the same files (`conversation-client.ts`, `remote-conversation.ts`, `src/events/types.ts`, `endpoint-audit.config.json`, `api-clients.test.ts`); new types in their own files (`src/models/acp-session-controls.ts` for S2) |
| 13 | Test agent | the generic scripted ACP agent (spec §4, layer 3: "Built in S1, reused in C1, S2 and C2") | needs the behaviours of Appendix C | one script, `tests/fixtures/acp/scripted_agent.py` (`tests/fixtures` is on upstream's test-directory allowlist and is shared by the SDK and agent-server suites); whoever lands first creates it, the other extends it behind flags. Its path is for the Conductor to settle with S1's designer. |
| 14 | Upstream guards | its `meta` (ACP `_meta`) fields are untyped dicts, which the weak-schema ratchet refuses unless allowlisted; its new event kinds | one new event kind, fully typed | independent; S2 adds no allowlist entry *(v2: none in the weak-schema allowlist; the REST check's pattern gained one alternative, §3.2 B14)* |
| 15 | `tests/sdk/agent/test_acp_agent.py` | will edit | does not edit (new files, §4.10) | no overlap |

Not shared: `_record_usage`, `ACPToolCallEvent`, the cancel path, `_apply_acp_model` (only S2 changes
its signature), the manifest and backend code (only S2).

*(v2)* Read at S1's head, `0cfb6a2`, stacked on `6f97bf3`: item 3 holds (S2's line is still the first
after the idle-clock reset in `session_update`, S1's routing below it); item 6 is one primitive (S1's
bridge emits its child events through `ACPAgent._on_session_event`, which `LocalConversation` sets to
`_emit_event_from_any_thread`); item 9 took the first branch (S1's cancel route is in
`conversation_acp_router`, in `acp_router.py`); item 13 is one script (S1 extends
`tests/fixtures/acp/scripted_agent.py` with `--subagents` and `--transcript`). S2 lands first, so S2
built each with the names and semantics above, and S1 used them. Nothing here was re-checked by
running S1's tests; S1's own Gate B covers that.

*(v2.4)* Read at S1's branch, `a3279be` (which contains `5e3317f`), and at its refactor in progress
(`3fb8f8d`, on `7f03b56`). The refactor renames none of the names above. One shared file the table
lacks: S1 adds its cancel route's tests to S2's `tests/agent_server/test_acp_router.py` (134 lines),
where the refactor removed two tests and joined some lines, so S1's rebase onto `7f03b56` meets
those hunks. S1 does not edit `tests/conftest.py`; its tests import only `SCRIPTED_ACP_AGENT` and
`scripted_acp_command` from it, not the refactor's new helpers. Item 13 holds: the scripted agent
keeps its `serve()` tap, which S1's flags need (the Scout's cut 3, rejected).

---

## 9 · E11 and the testing layers

**E11 · Agent surfaces (S2, C2, D1).** What S2 proves, where, and what it leaves to C2, D1 and D5:

| E11 claim | Proven in S2 by | And elsewhere |
|---|---|---|
| On the home screen the preview lists the namespace's decompositions | `test_acp_preview.py` (the scripted agent's commands per value); the live tier with dr-acp | D1's `test_surfaces.py` (commands per namespace); C2's end-to-end |
| Changing the namespace changes them | previews with different `acp_config_options` give each value's commands; a pre-start set changes what the started session reports | C2's end-to-end |
| The started run uses the chosen namespace | the agent's request log shows `session/set_config_option` before the first `session/prompt`; after the first prompt the reported option equals the chosen value (live tier with dr-acp) | D1's run log, `run.start.namespace` (D1's `test_surfaces.py`, D5's cross-repo run) |
| Commands are gone after the first message | the event after the first prompt has no commands when the agent clears them (scripted agent; live tier with dr-acp) | D1 clears them (D1 §5.2); C2's menu |
| The panel mounts with the right conversation and never shares the right side with the drawer | — (manifest and icon only) | C2 |
| The Library App's backend starts on macOS and on Linux | the macOS job and the Linux suite start a real backend artifact (§6.3) | D3's artifacts; D5's macOS release build starts the Library itself |

*(v2)* Each claim's tests, by name, are in the Gate B section. The two dr-acp claims of the live tier
ran inside S1's head (`0cfb6a2`), not at `6f97bf3` (§10 item 12). *(v2.2: they have since run at
`6f97bf3` and at `5e3317f`, S2's head, run 37147707860, 8 of 8. v2.4: at `7f03b56`, the tests by
name are in the refactor section, and the live tier ran there, run 37163413911, 8 of 8. The first
two claims' scripted-agent test,
`test_the_preview_equals_the_started_session_before_its_first_prompt`, stays; the request-log test
of the third and the router test of the fourth stay too.)* *(v2.1, as-built §6.2)* With dr-acp the
live tier sets one value, so "changing the namespace changes them" is shown with the scripted
agent only, and which commands `root` offers is neither asserted nor printed.

**Layer 3 (inside the fork).** §4.10, §5.3 and §6.3, in upstream's folders and style, so they ship in
the upstream PRs. Upstream's full suites stay green on the task branch, and each PR's commits,
cherry-picked onto the fork's `main`, get a draft PR there that is never merged, so the guards that
run only for pull requests to `main` run as upstream would run them (the spec's §4, layer 3).
*(v2, §3.2 B18: the suites are green on the task branch, in PR #1 against `deep-reasoning`; the
per-PR drafts onto `main` are not opened yet, so the main-only guards ran only locally, and the SDK
API breakage check not at all.)* *(v2.5: no draft onto `main` is opened. The Gate C stack's seven
drafts are based on `deep-reasoning` and go nowhere upstream; upstream's test workflow (whose jobs
skip their steps when a level changes nothing on their paths) and its main-only guards are green on
every level, B25.)*

**The live tier.** `tests/sdk/agent/test_acp_session_controls_live.py`, marked `acp_live`, upstream's
existing marker for tests that launch real ACP agents (deselected by default, `pyproject.toml:102`;
upstream runs `-m acp_live` in a separate job):

- *Built-in providers* (Claude Code, Codex, Gemini, through `npx` with a bogus key, as
  `test_acp_conformance.py` does): a preview succeeds; every command has a name; where the registry
  says the provider selects its model through config options, the `model` option is present.
- *Any agent named by the environment*: when `OPENHANDS_ACP_LIVE_AGENT_COMMAND` (shell-split) and
  `OPENHANDS_ACP_LIVE_CONFIG_OPTIONS` (JSON object of start values) are set, it asserts S2's two
  falsifiers against that agent: the preview equals the started conversation's controls before its
  first prompt; after the first prompt, every chosen option is reported at its chosen value. With
  `OPENHANDS_ACP_LIVE_EXPECT_COMMANDS_CLEARED=1` it also asserts the first prompt leaves no commands.
  Skipped when unset. This is a generic hook, and it is how dr-acp runs behind the bridge.
- *Where it runs with dr-acp:* not in the public fork, because installing dr-acp installs
  deep_reasoner_beta, which needs a read token that must not sit on a public repository's workflows.
  It runs in deep-reasoning's CI: a `workflow_dispatch` job that checks out the fork at the task
  branch's head, installs its three packages and dr-acp, and runs the file with
  `OPENHANDS_ACP_LIVE_AGENT_COMMAND="dr-acp --config <test config>"`,
  `OPENHANDS_ACP_LIVE_CONFIG_OPTIONS='{"namespace": "<a non-default namespace>"}'` and
  `OPENHANDS_ACP_LIVE_EXPECT_COMMANDS_CLEARED=1`. dr-acp clears its commands and narrows the
  namespace when it accepts the first prompt, before it builds the run, so these assertions need no
  model key; with the live tier's `OPENAI_API_KEY` (gpt-6-luna) the run also completes. That job is
  D5's cross-repo CI to own, or a small workflow in deep-reasoning until it exists (§10).

*(v2, §3.2 B8.)* As built: the built-in providers are all six of `ACP_PROVIDERS` (claude-code, codex,
gemini-cli, kimi-code, pi, opencode), and the `model` option is required where the session reported
that it selects its model through config options; the file also runs in upstream's `acp-live-tests`
job, where the six previews ran at `6f97bf3`. The agent-named tests: the preview against a
conversation started from the same command and values after a `run()` with no message; then one
prompt, a failed turn tolerated, each chosen option at its value, and with the flag, no commands in
the last controls event after the prompt. The dr-acp job is deep-reasoning's `fork-live.yml` on
branch `ci/fork-live`, a `workflow_dispatch` taking `sdk_ref`, `suites`, `sdk_repo` and
`live_config`; it runs `dr-acp --config docs/configs/advising/main.yaml --home <temp>` with
`{"namespace": "root"}`, a non-default namespace (the config's default is `advising`). Run
37141960911 passed it, 8 of 8, with `sdk_ref` S1's branch.

---

## 10 · Open items and decisions for the Conductor

1. **The shared out-of-turn emitter (§8 item 6).** S1 needs it too. Confirm with S1's designer that
   S1 uses `ACPAgent._on_session_event` and `LocalConversation._emit_event_from_any_thread` as
   specified here, or bring the difference back. *(v2: resolved; S1 uses both at `0cfb6a2`, §8.)*
2. **The test agent's path (§8 item 13)**: `tests/fixtures/acp/scripted_agent.py`, to settle with S1.
   *(v2: resolved; S2 created it there and S1 extends it, §8.)*
3. **Where the live job with dr-acp runs (§9):** deep-reasoning's CI, because of the private
   dependency. D5 owns cross-repo CI; until D5 lands, a small `workflow_dispatch` workflow in
   deep-reasoning. *(v2: resolved; `fork-live.yml` on branch `ci/fork-live`, which D5's branch
   replaces, §3.2 B8.)*
4. **The macOS job is part of PR 3 itself** (upstream-shaped, like their Windows job), not a
   fork-only commit. If upstream would rather not run macOS, it is one job to drop from the PR.
   *(v2: built so, `1d2627b`.)*
5. **Possible guard objection (§6.4):** oasdiff on `BackendPlatform`'s new keys. Settled by running
   the check on PR 3's draft PR. *(v2: resolved, it objected, and the fallback is built, §3.2 B14;
   settled by a local run, not a draft PR, B18. v2.3: confirmed in CI at `5e3317f`, §4.9.)*
6. **Unverified on hardware:** `os.killpg` on a zombie-only group on macOS (§6.1), and websockets
   15.0.1's `proxy` parameter (§6.1). Both are settled by the macOS job and the lock, and recorded in
   the as-built. *(v2: resolved; macOS does answer EPERM, B12; 15.0.1 has `proxy`, B15.)*
7. **Noticed outside S2, for D1 (no action in S2):** an ACP agent's prompt carries, after the user's
   own text, any per-turn extensions (`extended_content`), and the first prompt also carries the
   conversation's system-message suffix (secret names, and skills where the deployment manages them),
   each as further text blocks (`message.py:116–119`, `acp_agent.py:3586–3590`). A slash command is
   still the first token of the first block, as D1 expects; but if `dr-acp` joins all text blocks into
   the task, those blocks become part of the task. D1's designer should know.
8. **No new persisted-settings baseline, no new allowlist entry** are expected for S2 (§4.9).
   *(v2: none in the persisted settings or the weak-schema allowlist; the REST check's
   extensible-property pattern gained one alternative, B14.)*
9. *(v2)* **Rule on the size** (§3.2 B19): 4,731 lines built against the spec's ≈0.9k; about 16 h at
   Gate C against ≈3 h. *(v2.4: after the refactor, 4,319 at `7f03b56`, about 14.4 h; the refactor
   section's size table. v2.5: 4,343 at `d938c90`; the stack's seven PRs add 4,348 between them,
   about 14.5 h, #5 alone 1,346; the Gate C section.)*
10. *(v2)* **The PR split** (§3.2 B16, B17): cut PR 3 after PR 2, or resolve its one hunk in
    `test_canvas_extensions_manifest.py`; leave `aff05f6` and `ea51b3f` behind. *(v2.4: the hunk is
    gone, and each PR applies alone, R10; the rest stands, with `c12f7b4` and `1f2b52d` left behind
    too, B25. v2.5: done. The stack is #3 to #9, in v1's order, PR 3, PR 2, then PR 1 in five levels,
    based on `deep-reasoning`, so all four fork-only commits stay behind; the Gate C section.)*
11. *(v2)* **The main-only guards** (§3.2 B18): the REST breakage check, persisted settings and the
    TypeScript client CI (with S2's 8 TypeScript tests) ran only locally, at `28e5654`; the SDK API
    breakage check has no recorded run. They run in CI once the PR split opens the per-PR drafts onto
    `main`, which is before Gate C, not before Gate B. *(v2.2: resolved for CI by `1f2b52d`, B25; what
    stays outside CI is the REST check's oasdiff (no `v1.50.1` tag in the fork), the SDK API check
    (skipped without a version change) and the schema ratchet (`server.yml`), each run locally.
    v2.3: the REST check's oasdiff now runs in CI too, against `v1.50.1`, §4.9; the other two stay
    outside.)*
12. *(v2)* **The live tier ran inside S1's head.** Run 37141960911 checked out `0cfb6a2`, which
    carries `6f97bf3` unchanged under S1's five commits; S1's changes to `acp_agent.py` route updates
    below S2's line (§8 item 3), so the result stands for S2 as stacked. The six provider previews
    also ran at `6f97bf3` itself, in PR #1's `acp-live-tests`. A run of the two dr-acp tests at S2's
    own head is one dispatch of `fork-live.yml` with `sdk_ref: feat/agent-surfaces` and `suites: s2`,
    if the Conductor wants the live tier at the branch's head exactly. *(v2.2: resolved; run
    37143895412 at `6f97bf3` and run 37147707860 at `5e3317f`, S2's head, each 8 of 8.)*
13. *(v2)* **§7 item 5's order is not pinned**: that the commands-cleared event reaches Canvas before
    the run's output, under the agent-server's `arun()`. C2 should follow the newest event whenever
    it arrives; a test belongs to C2's end-to-end or to a later S2 change, not to this gate.
14. *(v2.1; v2.2: ruled)* **"Not reported yet" or "none offered"** (§3.2 B4, as-built D-2). **The
    Conductor's ruling, for Michael to confirm at Gate B: (c), change nothing in S2.** The contract
    says the newest event is the state and a first empty event may be followed by the menu, and C2
    shows an empty slash menu until the commands arrive. As written in v2.1: After every start and
    resume the first event can carry an empty `available_commands` that the agent's menu replaces
    moments later, and an agent with no commands looks the same; the event gives C2 no way to tell.
    The ways out, with what each costs (not decided here):
    - (a) **No start event until the root session has reported commands.** `_start_acp_server`
      publishes only once the bridge's `_commands_reported` flag is set for the root; otherwise the
      menu's own record publishes when it arrives. S2: a few lines and a test. C2: no change; "no
      event" keeps meaning "nothing reported yet", and an empty list then means the agent cleared its
      commands or reported none. Costs: an agent that reports options in its `session/new` response
      but never sends `available_commands_update` has its options published only with its next
      update, so C2 shows it no picker until then (all six built-in providers send commands, by the
      live tier); after a resume the previous run's event stays newest until the agent reports; PR
      #1's "one event per start" no longer holds.
    - (b) **A field that says it**, for example `commands_reported: bool` on `ACPSessionControls`
      (so on the event and in the preview's answer), set from the bridge's flag. S2: one typed field
      in the DTO, the event and the TypeScript types, about ten lines and their tests; an additive
      response property for the REST check. C2: a third menu state ("loading") while it is `false`;
      the preview's answer then also says an agent did not report within the 2 s wait.
    - (c) **No change; the contract says it** (§7 item 4 as of v2.1). S2: nothing. C2: an empty menu
      for the moment between the two events at every start and resume (C2 at `db3b4b9` shows it, by
      the as-built's reading of its code), or a debounce of an empty event that follows a start,
      which has no signal to end it for an agent that offers none.
    - For completeness: waiting inside the start for the commands, as the preview does, costs up to
      2 s before the first prompt of every conversation whose agent sends no commands.
15. *(v2.1)* **A start value for a built-in provider's session mode is overwritten** (§3.2 B21; read,
    not run). Ways out: C2 hides a `mode` option for those providers; the bridge sends its session
    mode before the values; or it skips `set_session_mode` when a value for the mode option was
    given. For the Conductor; it does not affect dr-acp.
16. *(v2.1)* **The set route's 500 carries the agent's -32603 message unmasked** (§3.2 B20), as
    `switch_acp_model`'s does upstream. Masking it is one `except` in the route or one `mask()` in
    `_apply_config_options`; untested either way. *(v2.2: pinned as it is, B24; masking is not
    decided.)*

---

## Appendix A · Signature reference (Python)

Every block is valid Python, formatted as ruff would, one field per line. Bodies are `...` where the
behaviour is specified in the sections above; module paths are relative to the fork's root.
*(v2)* Every block matches the build at `6f97bf3`, with one field and one parameter per line; each
change from v1 is named in §3.2 and marked `# (v2)` where it sits. *(v2.4)* Every signature matches
the code at `7f03b56`; each refactor change is marked `# (v2.4, Rn)` where it sits, with the
docstrings R3 and R6 reworded. In layout the code now differs: R3 and R6 put short signatures and
fields on one line, as ruff does without a magic trailing comma, and this appendix keeps one per
line.

### A.1 `openhands-sdk/openhands/sdk/agent/acp_models.py` (additions)

```python
from collections.abc import Sequence
from typing import Literal

from acp.schema import (
    AvailableCommand,
    SessionConfigOptionBoolean,
    SessionConfigOptionSelect,
    SessionConfigSelectGroup,
    SessionConfigSelectOption,
)
from pydantic import BaseModel, Field


ACPConfigOptionType = Literal["select", "boolean"]


class ACPCommandInput(BaseModel):
    """The text a command takes after its name; ACP's ``UnstructuredCommandInput``."""

    hint: str = Field(
        description="Placeholder a client shows until the user types the input.",
    )


class ACPAvailableCommand(BaseModel):
    """One slash command an ACP session offers; ACP's ``AvailableCommand``.

    A client invokes it by sending a user message whose text starts with
    ``/<name>``; the bridge forwards that text unchanged.
    """

    name: str = Field(
        description="Command name, without the leading slash.",
    )
    description: str = Field(
        description="What the command does, in the agent's words.",
    )
    input: ACPCommandInput | None = Field(
        default=None,
        description="Present when the command takes text after its name.",
    )

    # (v2) Typed: ACP's own schema has already dropped what it cannot parse (§3.2 B1).
    @classmethod
    def from_protocol(cls, raw: AvailableCommand) -> "ACPAvailableCommand | None":
        """Build from an ACP ``AvailableCommand``; ``None`` without a name."""
        ...


class ACPConfigOptionValue(BaseModel):
    """One value of a select option; ACP's ``SessionConfigSelectOption``."""

    value: str = Field(
        description="The value to send back in session/set_config_option.",
    )
    name: str = Field(
        description="Human-readable label for the value.",
    )
    description: str | None = Field(
        default=None,
        description="Optional longer description supplied by the agent.",
    )
    group: str | None = Field(
        default=None,
        description="Label of the ACP option group the value came from, if any.",
    )


class ACPConfigOption(BaseModel):
    """One session config option; ACP's ``SessionConfigOptionSelect`` or ``…Boolean``.

    Select groups are flattened into ``options``, each value keeping its
    group's label in ``group``.
    """

    id: str = Field(
        description="The option's id, the configId of session/set_config_option.",
    )
    name: str = Field(
        description="Human-readable label for the option.",
    )
    type: ACPConfigOptionType = Field(
        description="'select' (one of options) or 'boolean'.",
    )
    current_value: str | bool = Field(
        description="The current value: a str for a select, a bool for a boolean.",
    )
    description: str | None = Field(
        default=None,
        description="Optional description for the client to display.",
    )
    category: str | None = Field(
        default=None,
        description="ACP's UX hint: mode, model, model_config or thought_level.",
    )
    options: list[ACPConfigOptionValue] = Field(
        default_factory=list,
        description="The selectable values of a select; empty for a boolean.",
    )

    # (v2) Typed, and never None: ACP drops other option types first (§3.2 B1).
    @classmethod
    def from_protocol(
        cls,
        raw: SessionConfigOptionSelect | SessionConfigOptionBoolean,
    ) -> "ACPConfigOption":
        """Build from an ACP select or boolean config option."""
        ...


# (v2) Module helpers behind ACPConfigOption.from_protocol.
def _select_value(
    raw: SessionConfigSelectOption,
    group: str | None = None,
) -> ACPConfigOptionValue: ...


def _flatten_select_values(
    entries: Sequence[SessionConfigSelectOption] | Sequence[SessionConfigSelectGroup],
) -> list[ACPConfigOptionValue]:
    """One flat list from a select's options, whether grouped or not."""
    ...


class ACPSessionControls(BaseModel):
    """The slash commands and config options an ACP session offers now."""

    available_commands: list[ACPAvailableCommand] = Field(
        default_factory=list,
        description="The agent's slash commands, in the agent's order.",
    )
    config_options: list[ACPConfigOption] = Field(
        default_factory=list,
        description="The agent's session config options, in the agent's order.",
    )

    @classmethod
    def parse_commands(
        cls,
        raw: Sequence[AvailableCommand],
    ) -> list[ACPAvailableCommand]:
        """Normalize ACP commands, dropping those without a name."""
        ...

    @classmethod
    def parse_config_options(
        cls,
        raw: Sequence[SessionConfigOptionSelect | SessionConfigOptionBoolean],
    ) -> list[ACPConfigOption]:
        """Normalize ACP config options."""
        ...
```

### A.2 `openhands-sdk/openhands/sdk/event/acp_session_controls.py` (new)

```python
from pydantic import Field
from rich.text import Text

from openhands.sdk.agent.acp_models import (
    ACPAvailableCommand,
    ACPConfigOption,
    ACPSessionControls,
)
from openhands.sdk.event.base import Event
from openhands.sdk.event.types import SourceType


class ACPSessionControlsEvent(Event):
    """The slash commands and config options an ACP session offers now.

    Latest wins: every event carries both lists in full, and the newest event
    of a conversation is its current state. Emitted when the session starts
    and whenever the agent reports a change.
    """

    source: SourceType = "agent"
    available_commands: list[ACPAvailableCommand] = Field(
        default_factory=list,
        description="The agent's slash commands.",
    )
    config_options: list[ACPConfigOption] = Field(
        default_factory=list,
        description="The agent's session config options.",
    )

    @classmethod
    def from_controls(cls, controls: ACPSessionControls) -> "ACPSessionControlsEvent":
        """Build the event for one snapshot."""
        ...

    @property
    def controls(self) -> ACPSessionControls:
        """The snapshot this event carries."""
        ...

    @property
    def visualize(self) -> Text:
        """One line: the command names, then each option's id and current value."""
        ...

    def __str__(self) -> str: ...
```

### A.3 `openhands-sdk/openhands/sdk/agent/acp_agent.py` (additions and changes)

```python
_ACP_CONFIG_OPTION_TIMEOUT: float = float(
    os.environ.get("ACP_CONFIG_OPTION_TIMEOUT", "30.0")
)
_ACP_SESSION_CLOSE_TIMEOUT: float = 2.0


class ACPConfigOptionRejectedError(ValueError):
    """The ACP server refused a session/set_config_option.

    ``str()`` is the server's own message, masked.
    """

    def __init__(
        self,
        config_id: str,
        value: str | bool,
        message: str,
    ) -> None:
        super().__init__(message)
        self.config_id = config_id
        self.value = value


def _check_config_option_id(config_id: str) -> None:
    """Refuse an empty id, and the model option, which switch_acp_model owns."""
    ...


# (v2.4, R1) New: the check every acp_config_options dict gets, through its type.
def _check_config_option_ids(
    values: dict[str, str | bool],
) -> dict[str, str | bool]: ...


# (v2.4, R1) New: types ACPAgent.acp_config_options and
# StartConversationRequest.acp_config_options, in place of two field validators.
ACPConfigOptionValues = Annotated[
    dict[str, str | bool], AfterValidator(_check_config_option_ids)
]


async def _apply_config_options(
    conn: ClientSideConnection,
    session_id: str,
    values: Mapping[str, str | bool],
    *,
    on_config_options: Callable[[str, Sequence[Any]], None],
    mask: Callable[[Any], Any],
) -> None:
    """Set each value in order, recording every response: one may change others.

    Raises:
        ACPConfigOptionRejectedError: The server refused a value (any
            ACPRequestError except -32603).
        ACPRequestError: The server's internal error (-32603), unchanged.
    """
    ...


# Changed: the three model helpers gain a recorder for set_config_option responses.
async def _apply_acp_model(
    conn: ClientSideConnection,
    session_id: str,
    model: str,
    *,
    agent_name: str | None = None,
    via_config_option: bool,
    on_config_options: Callable[[str, Sequence[Any]], None] | None = None,
) -> None: ...


async def _maybe_set_session_model(
    conn: ClientSideConnection,
    agent_name: str,
    session_id: str,
    acp_model: str | None,
    *,
    via_config_option: bool,
    on_config_options: Callable[[str, Sequence[Any]], None] | None = None,
) -> bool: ...


async def _reapply_session_model_on_resume(
    conn: ClientSideConnection,
    agent_name: str,
    session_id: str,
    acp_model: str | None,
    *,
    via_config_option: bool,
    on_config_options: Callable[[str, Sequence[Any]], None] | None = None,
) -> bool: ...


# Changed: first branch added.
def _classify_acp_init_error(exc: BaseException) -> str:
    """... ``ACPConfigOptionRejected``: the server refused a start-time option value."""
    ...


# (v2) One reader for the configOptions of session/new, session/load and every
# session/set_config_option response; _model_config_option uses it too (§3.2 B6).
# (v2.4) Its getattr stays: six of upstream's tests pass responses without
# config_options (f5628cc).
def _session_config_options(response: Any) -> list[Any]:
    """The ``configOptions`` of a session response; empty when absent."""
    ...


class _OpenHandsACPBridge:
    def __init__(self) -> None:
        # ... existing attributes ...
        self._session_controls: dict[str, ACPSessionControls] = {}
        self._commands_reported: dict[str, threading.Event] = {}
        self.on_session_controls_changed: Callable[[], None] | None = None

    def record_available_commands(
        self,
        session_id: str,
        commands: Sequence[Any],
    ) -> None:
        """Mask, normalize and store a session's commands; then notify."""
        ...

    def record_config_options(
        self,
        session_id: str,
        options: Sequence[Any],
    ) -> None:
        """Mask, normalize and store a session's config options; then notify."""
        ...

    # (v2.4, R2) New: the masking and storing both records repeated. Masks
    # the dumped entries and stores a validated copy of the snapshot.
    def _store_session_controls(
        self,
        session_id: str,
        field: Literal["available_commands", "config_options"],
        entries: Sequence[BaseModel],
    ) -> None:
        """Replace one list of the session's snapshot with ``entries``, masked."""
        ...

    def session_controls(self, session_id: str) -> ACPSessionControls:
        """The session's latest snapshot; empty if it has reported nothing."""
        ...

    def wait_for_available_commands(
        self,
        session_id: str,
        timeout: float,
    ) -> bool:
        """Block until the session has reported commands once, or the timeout."""
        ...

    def _record_session_controls(
        self,
        session_id: str,
        update: Any,
    ) -> bool:
        """Record an AvailableCommandsUpdate or ConfigOptionUpdate; else False."""
        ...

    # (v2) Calls on_session_controls_changed; logs a failure at warning and
    # swallows it, so a failing sink never fails the update (§3.2 B6).
    def _notify_session_controls_changed(self) -> None: ...


class ACPAgent(AgentBase):
    # ... existing fields ...
    # (v2.4, R1) Typed ACPConfigOptionValues; _reject_model_config_option is gone.
    acp_config_options: ACPConfigOptionValues = Field(
        default_factory=dict,
        description=(
            "Session config option values to set with session/set_config_option "
            "after session/new and before the first prompt, in order. Applied to "
            "a fresh session only, not after session/load. The model is set with "
            "acp_model, never here."
        ),
    )

    # ... existing private attributes ...
    _on_session_event: Callable[[Event], None] | None = PrivateAttr(default=None)
    _session_controls_lock: threading.Lock = PrivateAttr(default_factory=threading.Lock)
    _published_session_controls: ACPSessionControls | None = PrivateAttr(default=None)
    _supports_session_close: bool = PrivateAttr(default=False)
    _starting_session: bool = PrivateAttr(default=False)

    @property
    def session_controls(self) -> ACPSessionControls:
        """The root session's commands and options; empty before a session."""
        ...

    def set_acp_config_option(
        self,
        config_id: str,
        value: str | bool,
    ) -> ACPSessionControls:
        """Set one option on the live session; return the resulting controls.

        Only the session changes; ``acp_config_options`` keeps its values.

        Raises:
            ValueError: ``config_id`` is empty or ``"model"``.
            RuntimeError: There is no live session yet.
            ACPConfigOptionRejectedError: The server refused the value.
            TimeoutError: No answer within ``ACP_CONFIG_OPTION_TIMEOUT``.
        """
        ...

    def wait_for_available_commands(self, timeout: float) -> ACPSessionControls:
        """Wait until the root session has reported commands once, or the timeout."""
        ...

    def close_acp_session(self, timeout: float = _ACP_SESSION_CLOSE_TIMEOUT) -> None:
        """Send session/close if the server advertised it; log and ignore errors."""
        ...

    def _bind_session_controls(self) -> None:
        """Point the bridge's change callback at this agent's publisher.

        (v2) The callback holds the agent through a weakref (§3.2 B6).
        """
        ...

    def _publish_session_controls(self) -> None:
        """Emit the root session's snapshot through _on_session_event (§4.3)."""
        ...

    # (v2) Changed: sets and clears _starting_session around
    # _launch_acp_session, then publishes once (§4.3, §3.2 B6).
    def _start_acp_server(self, state: ConversationState) -> None: ...

    # (v2) New: the body _start_acp_server had, unchanged, plus binding the
    # publisher right after the bridge is created.
    def _launch_acp_session(self, state: ConversationState) -> None: ...
```

### A.4 `openhands-sdk/openhands/sdk/conversation/impl/local_conversation.py` (additions)

```python
from concurrent.futures import ThreadPoolExecutor


class LocalConversation(BaseConversation):
    # (v2) Created in __init__ (its one thread starts on the first submit);
    # shut down in close() with wait=False, cancel_futures=True (§3.2 B5).
    _event_emitter: ThreadPoolExecutor

    def set_acp_config_option(
        self,
        config_id: str,
        value: str | bool,
    ) -> ACPSessionControls | None:
        """Set an ACP session config option, live or for the session's start.

        Live: issues session/set_config_option and returns the resulting
        controls. Not yet started: returns None and the value is applied after
        session/new. Either way the value is persisted on the agent.

        Raises:
            ValueError: Not an ACP conversation, or ``config_id`` is empty or
                ``"model"``.
            ACPConfigOptionRejectedError: The server refused the value.
            TimeoutError: No answer within ``ACP_CONFIG_OPTION_TIMEOUT``.
        """
        ...

    def _replace_acp_agent(
        self,
        update: dict[str, Any],
        *,
        live: bool,
    ) -> None:
        """Swap in ``agent.model_copy(update=update)``, handing over the runtime.

        Extracted from switch_acp_model; rebinds atexit cleanup, file-credential
        masking and session-controls publishing on the copy, releases the old
        agent's runtime when live, and updates both self.agent and the state.
        """
        ...

    def _emit_event_from_any_thread(self, event: Event) -> None:
        """Persist and publish ``event`` from any thread, in submission order.

        One worker takes the state lock and calls _on_event; never blocks the
        caller. Dropped with a debug log after close().
        """
        ...
```

### A.5 `openhands-sdk/openhands/sdk/conversation/request.py` (addition)

```python
from openhands.sdk.agent.acp_agent import ACPAgent as ACPAgent, ACPConfigOptionValues


class StartConversationRequest(ConversationConfig):
    # ... existing fields ...
    # (v2.4, R1) Typed ACPConfigOptionValues; _reject_model_config_option and
    # the import of the private _check_config_option_id are gone.
    acp_config_options: ACPConfigOptionValues = Field(
        default_factory=dict,
        description=(
            "ACP session config option values to apply after session/new and "
            "before the first prompt, in order. Requires an ACP agent. Launch-only: "
            "folded into the agent, not stored with the conversation record."
        ),
    )
```

### A.6 `openhands-sdk/openhands/sdk/conversation/acp_preview.py` (new)

```python
from collections.abc import Mapping
from pathlib import Path
from typing import Final

from openhands.sdk.agent.acp_agent import ACPAgent
from openhands.sdk.agent.acp_models import ACPSessionControls
from openhands.sdk.secret import SecretValue
from openhands.sdk.utils.cipher import Cipher
from openhands.sdk.workspace import LocalWorkspace


PREVIEW_COMMANDS_WAIT_SECONDS: Final[float] = 2.0


# (v2.4, R3) The docstring no longer lists the codes, which are those of
# _classify_acp_init_error: today ACPConfigOptionRejected, ACPStartupTimeout,
# ACPAuthRequired, ACPSpawnError and ACPInitError.
class ACPPreviewError(RuntimeError):
    """The agent could not be previewed.

    ``code`` is the ConversationErrorEvent code a start would have reported;
    ``detail`` is redacted and masked.
    """

    def __init__(
        self,
        code: str,
        detail: str,
    ) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


def preview_acp_session(
    agent: ACPAgent,
    workspace: LocalWorkspace,
    persistence_dir: Path,
    *,
    secrets: Mapping[str, SecretValue] | None = None,
    cipher: Cipher | None = None,
    commands_wait_seconds: float = PREVIEW_COMMANDS_WAIT_SECONDS,
) -> ACPSessionControls:
    """Start ``agent``'s ACP session in a throwaway state, read what it offers, close it.

    Runs ACPAgent.init_state, so the agent starts exactly as a conversation's
    would, ``agent.acp_config_options`` included. Blocking; the caller deletes
    ``persistence_dir``. (v2) Creates ``persistence_dir``, and runs init_state
    holding the throwaway state's lock (§3.2 B7).

    Raises:
        ACPPreviewError: The agent failed to start or refused an option value.
    """
    ...
```

### A.7 `openhands-agent-server` (PR 1)

```python
# openhands/agent_server/acp_router.py (new)
from typing import Final
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from openhands.agent_server.conversation_service import ConversationService
from openhands.agent_server.dependencies import get_conversation_service
from openhands.agent_server.models import StartConversationRequest
from openhands.sdk.agent.acp_models import ACPSessionControls


acp_router = APIRouter(prefix="/acp", tags=["ACP"])
conversation_acp_router = APIRouter(
    prefix="/conversations/{conversation_id}/acp",
    tags=["ACP"],
)

_PREVIEW_ERROR_STATUS: Final[dict[str, int]] = {
    "ACPConfigOptionRejected": 422,
    "ACPStartupTimeout": 504,
}
_PREVIEW_ERROR_DEFAULT_STATUS: Final[int] = 502


class ACPConfigOptionSetRequest(BaseModel):
    """Set one ACP session config option."""

    config_id: str = Field(
        min_length=1,
        description="The option's id, as the agent reports it.",
    )
    value: str | bool = Field(
        description="A select option's value, or a boolean option's value.",
    )


class ACPConfigOptionSetResponse(BaseModel):
    """What setting an option did."""

    applied: bool = Field(
        description=(
            "True when a live session took the value; False when it is kept for "
            "the session's start."
        ),
    )
    controls: ACPSessionControls = Field(
        description="The session's controls after the set; empty when not applied.",
    )


@acp_router.post(
    "/preview",
    responses={
        400: {"description": "The resolved agent is not an ACP agent"},
        404: {"description": "Agent profile not found"},
        422: {"description": "Invalid request, or the agent refused an option value"},
        429: {"description": "Conversation run limit reached"},
        501: {"description": "Unavailable in Docker runtime mode"},  # (v2) §3.2 B3
        502: {"description": "The agent failed to start"},
        504: {"description": "The agent did not start in time"},
    },
)
async def preview_acp_session(
    request: StartConversationRequest,
    http_request: Request,  # (v2) to read app.state.config.conversation_runtime
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> ACPSessionControls:
    """What an ACP agent would offer for this start request, before it exists."""
    ...


@conversation_acp_router.post(
    "/config-options",
    responses={
        400: {"description": "Not an ACP conversation, or the model option"},
        404: {"description": "Conversation not found"},
        422: {"description": "The agent refused the value"},
        504: {"description": "The agent did not answer in time"},
    },
)
async def set_acp_config_option(
    conversation_id: UUID,
    request: ACPConfigOptionSetRequest,
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> ACPConfigOptionSetResponse:
    """Set an ACP session config option, live or for the session's start."""
    ...


# openhands/agent_server/conversation_service.py (additions)
class InvalidACPConfigOptions(ValueError):
    """acp_config_options sent with an agent that is not an ACP agent."""


class ConversationService:
    async def preview_acp_session(
        self,
        request: StartConversationRequest,
    ) -> ACPSessionControls:
        """Resolve the agent as a start would, then preview it (§4.6)."""
        ...

    # (v2.4, R1, R3) The fold no longer re-checks the merged ids; the docstring
    # states the contract instead of naming its two callers.
    async def _resolve_launch(
        self,
        request: StartConversationRequest,
    ) -> tuple[StartConversationRequest, LaunchedAgentProfile | None]:
        """Resolve the request's agent as its launch will run it.

        Settings, profile resolution and its secret allow-list, load_memory,
        ACP skill sourcing and launch additions, then the acp_config_options
        fold.

        Raises:
            ProfileNotFound: Unknown agent_profile_id.
            DanglingMcpServerRef: The profile references a missing MCP server.
            InvalidACPConfigOptions: Option values for a non-ACP agent.
        """
        ...


# openhands/agent_server/event_service.py (addition)
class EventService:
    async def set_acp_config_option(
        self,
        config_id: str,
        value: str | bool,
    ) -> ACPSessionControls | None:
        """Run LocalConversation.set_acp_config_option off the event loop."""
        ...
```

### A.8 `openhands-agent-server` (PR 2)

```python
# openhands/agent_server/canvas_extensions/manifest.py (additions and changes)
from typing import Annotated, Final

from pydantic import AfterValidator, BaseModel, Field, field_validator, model_validator


# "/" or an absolute kebab-case path; a tab's place inside its panel.
_TAB_PATH_PATTERN: re.Pattern[str] = re.compile(
    r"^/(?:[a-z0-9]+(?:-[a-z0-9]+)*(?:/[a-z0-9]+(?:-[a-z0-9]+)*)*)?$"
)
PANEL_ICON_MEDIA_TYPES: Final[dict[str, str]] = {
    ".png": "image/png",
    ".svg": "image/svg+xml",
}


def _validate_contribution_id(value: str) -> str:
    """Refuse an id that is not kebab-case, as validate_extension_name does."""
    ...


# (v2.4, R5) New: the one check of a contribution id's form, in place of three
# _validate_id validators (the page's, upstream's own, among them).
ContributionId = Annotated[str, AfterValidator(_validate_contribution_id)]


# (v2.4, R5) Changed, upstream's class: only the id's type.
class CanvasExtensionPage(BaseModel):
    """A single page contributed to the Canvas UI by an extension."""

    id: ContributionId = Field(
        description="Unique contribution id within the extension",
    )
    # ... title, path and _validate_path, unchanged ...


class CanvasExtensionPanelTab(BaseModel):
    """One tab of a conversation panel; its page mounts when the tab is selected."""

    id: ContributionId = Field(
        description="Contribution id; the id the App registers this tab's page under",
    )
    title: str = Field(
        min_length=1,
        description="Tab label in the panel's tab row",
    )
    path: str = Field(
        default="/",
        description="Where the tab's page starts inside the panel; '/' is its root",
    )

    @field_validator("path")
    @classmethod
    def _validate_path(cls, value: str) -> str:
        """'/' or an absolute kebab-case path (_TAB_PATH_PATTERN)."""
        ...


class CanvasExtensionConversationPanel(BaseModel):
    """A panel opened from a button in the conversation header."""

    id: ContributionId = Field(
        description="Contribution id of the panel",
    )
    title: str = Field(
        min_length=1,
        description="Panel title; the header button's tooltip is 'Show' and this",
    )
    icon: str | None = Field(
        default=None,
        description="Package-relative .svg or .png for the header button",
    )
    tabs: list[CanvasExtensionPanelTab] = Field(
        min_length=1,
        description="The panel's tabs, in tab-row order",
    )

    @field_validator("icon")
    @classmethod
    def _validate_icon(cls, value: str | None) -> str | None:
        """Refuse an absolute path, a '..' part, and a suffix but .svg or .png."""
        ...

    @field_validator("tabs")
    @classmethod
    def _validate_unique_tab_paths(
        cls,
        value: list[CanvasExtensionPanelTab],
    ) -> list[CanvasExtensionPanelTab]: ...


class CanvasExtensionContributes(BaseModel):
    """Contributions an extension makes to the Canvas UI."""

    pages: list[CanvasExtensionPage] = Field(
        default_factory=list,
        description="Pages contributed to Canvas navigation",
    )
    conversation_panels: list[CanvasExtensionConversationPanel] = Field(
        default_factory=list,
        exclude_if=lambda value: not value,
        description="Panels opened from buttons in the conversation header",
    )

    @model_validator(mode="after")
    def _validate_unique_contribution_ids(self) -> "CanvasExtensionContributes":
        """Page, panel and tab ids form one namespace per extension."""
        ...


def resolve_package_file(
    package_root: Path,
    relative: str,
    what: str,
) -> Path:
    """Resolve ``relative`` inside ``package_root`` to a contained regular file.

    Symlinks are resolved before containment is checked.

    Raises:
        ValueError: It escapes the package or is not a regular file.
    """
    ...


def resolve_panel_icon(
    manifest: CanvasExtensionManifest,
    panel_id: str,
    package_root: Path,
) -> Path | None:
    """The contained icon file of a panel; None for no such panel or no icon.

    Raises:
        ValueError: The declared icon escapes the package, or (v2, §3.2 B11)
            does not resolve to a regular .svg or .png file.
    """
    ...


# openhands/agent_server/canvas_extensions/installed.py (addition; v2: the
# install check, CanvasExtensionInstallationInterface, also calls
# resolve_panel_icon for every panel, beside resolve_entrypoint)
def get_canvas_extension_panel_icon_path(
    name: str,
    panel_id: str,
    installed_dir: Path | None = None,
) -> Path | None:
    """Re-validated icon path for a serve; None if anything is missing or invalid."""
    ...


# openhands/agent_server/canvas_extensions_router.py (addition)
CanvasExtensionContributionIdPath = Annotated[
    str,
    Path(
        min_length=1,
        max_length=255,
        pattern=CANVAS_EXTENSION_NAME_PATTERN,
        description="Contribution id (lowercase alphanumeric, hyphens)",
    ),
]
_PANEL_ICON_HEADERS: Final[dict[str, str]] = {
    "Cache-Control": "no-cache",
    "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; sandbox",
    "X-Content-Type-Options": "nosniff",
}


# (v2.2) Documented as an image, §3.2 B23.
@canvas_extensions_router.get(
    "/installed/{extension_name}/panels/{panel_id}/icon",
    response_class=FileResponse,
    responses={
        200: {
            "content": {
                media_type: {"schema": {"type": "string", "format": "binary"}}
                for media_type in PANEL_ICON_MEDIA_TYPES.values()
            }
        },
        404: {"description": "Canvas extension, panel or icon not found"},
    },
)
def get_canvas_extension_panel_icon_endpoint(
    extension_name: CanvasExtensionNamePath,
    panel_id: CanvasExtensionContributionIdPath,
) -> FileResponse:
    """Serve a conversation panel's icon, re-validating containment."""
    ...
```

### A.9 `openhands-agent-server` (PR 3)

```python
# openhands/agent_server/canvas_extensions/manifest.py (change)
BackendPlatform = Literal["linux-amd64", "linux-arm64", "darwin-amd64", "darwin-arm64"]


# openhands/agent_server/canvas_extensions/backend.py (additions and changes)
_PLATFORM_SYSTEMS: Final[dict[str, str]] = {
    "Darwin": "darwin",
    "Linux": "linux",
}
_PLATFORM_MACHINES: Final[dict[str, str]] = {
    "aarch64": "arm64",
    "amd64": "amd64",
    "arm64": "arm64",
    "x86_64": "amd64",
}
# Loopback health probes never go through an HTTP proxy (macOS system proxies).
_LOOPBACK_OPENER: Final[urllib.request.OpenerDirector] = urllib.request.build_opener(
    urllib.request.ProxyHandler({})
)


# (v2) New, §3.2 B12.
def _group_exited(error: OSError) -> bool:
    """Whether killpg failed because a backend's process group has exited.

    ESRCH everywhere; EPERM too on macOS, its answer for a group whose
    remaining members are all zombies. Elsewhere EPERM is a real failure.
    """
    ...


class CanvasExtensionBackendManager:
    @staticmethod
    def current_platform() -> BackendPlatform | None:
        """The running platform's artifact key, or None where backends do not run."""
        ...

    @staticmethod
    def _probe(url: str) -> bool:
        """GET ``url`` through _LOOPBACK_OPENER; True on a 2xx or 3xx answer."""
        ...

    # (v2) Changed: both catch OSError and re-raise it unless _group_exited.
    @staticmethod
    def _signal_group(
        pgid: int,
        sig: int,
    ) -> None: ...

    @staticmethod
    def _group_alive(pgid: int) -> bool: ...


# openhands/agent_server/docker_runtime/proxy.py (additions)
# Never proxied: an HTTP proxy from the environment (or, on macOS, the system
# settings) would otherwise receive traffic meant for this host.
_LOOPBACK_HOSTS: Final[frozenset[str]] = frozenset({"127.0.0.1", "::1", "localhost"})


# (v2) Changed: proxy_http builds its httpx.AsyncClient with
# trust_env=not _is_loopback_host(...); bridge_websocket passes
# proxy=None for a loopback target and proxy=True otherwise (§3.2 B15).
# (v2.4, R8) _is_loopback_host is gone; both test the host themselves:
# trust_env=urlsplit(url).hostname not in _LOOPBACK_HOSTS, and
# proxy=None if urlsplit(upstream_url).hostname in _LOOPBACK_HOSTS else True.


# .github/scripts/check_agent_server_rest_api_breakage.py (v2: change, §3.2 B14)
_EXTENSIBLE_DISCRIMINATOR_PROPERTY_RE = re.compile(
    r"HookConfig\b.*\bhooks/items/type\b"
    r"|CanvasExtensionBackend\b.*\bartifacts/propertyNames\b"
)
```

---

## Appendix B · Signature reference (TypeScript client)

```typescript
// clients/typescript/src/models/acp-session-controls.ts (new)
// Hand-written until the pinned agent-server release carries these schemas;
// field for field with openhands.sdk.agent.acp_models.

export type ACPConfigOptionType = 'select' | 'boolean';

export interface ACPCommandInput {
  hint: string;
}

export interface ACPAvailableCommand {
  name: string;
  description: string;
  input?: ACPCommandInput | null;
}

export interface ACPConfigOptionValue {
  value: string;
  name: string;
  description?: string | null;
  group?: string | null;
}

export interface ACPConfigOption {
  id: string;
  name: string;
  type: ACPConfigOptionType;
  current_value: string | boolean;
  description?: string | null;
  category?: string | null;
  options: ACPConfigOptionValue[];
}

export interface ACPSessionControls {
  available_commands: ACPAvailableCommand[];
  config_options: ACPConfigOption[];
}

export type ACPConfigOptionValues = Record<string, string | boolean>;

export interface ACPConfigOptionSetRequest {
  config_id: string;
  value: string | boolean;
}

export interface ACPConfigOptionSetResponse {
  applied: boolean;
  controls: ACPSessionControls;
}

// (v2, §3.2 B2) The `kind` the events search matches: the module-qualified class name.
export const ACP_SESSION_CONTROLS_EVENT_KIND =
  'openhands.sdk.event.acp_session_controls.ACPSessionControlsEvent';
```

```typescript
// clients/typescript/src/events/types.ts (additions)
export interface ACPSessionControlsEvent extends BaseEvent {
  kind: 'ACPSessionControlsEvent';
  available_commands: ACPAvailableCommand[];
  config_options: ACPConfigOption[];
}

export function isACPSessionControlsEvent(
  event: BaseEvent
): event is ACPSessionControlsEvent {
  return event.kind === 'ACPSessionControlsEvent';
}

// (v2, §3.2 B2) The lists of the first controls event in `events`, or empty lists;
// given a newest-first search page, the session's current state.
export function acpSessionControlsOf(events: readonly BaseEvent[]): ACPSessionControls {
  for (const event of events) {
    if (isACPSessionControlsEvent(event)) {
      return {
        available_commands: event.available_commands,
        config_options: event.config_options,
      };
    }
  }
  return { available_commands: [], config_options: [] };
}
```

```typescript
// clients/typescript/src/client/conversation-client.ts (additions)
export interface CreateConversationPayload {
  agent_profile_id?: string;
  agent?: unknown;
  agent_settings?: unknown;
  acp_config_options?: ACPConfigOptionValues;
  [key: string]: unknown;
}

export class ConversationClient {
  /** POST /api/acp/preview with the payload a start would send. */
  async previewAcpSession(payload: CreateConversationPayload): Promise<ACPSessionControls> {
    const response = await this.client.post<ACPSessionControls>('/api/acp/preview', payload);
    return response.data;
  }

  /** POST /api/conversations/{id}/acp/config-options. */
  async setAcpConfigOption(
    conversationId: string,
    configId: string,
    value: string | boolean
  ): Promise<ACPConfigOptionSetResponse> {
    const response = await this.client.post<ACPConfigOptionSetResponse>(
      `/api/conversations/${conversationId}/acp/config-options`,
      { config_id: configId, value }
    );
    return response.data;
  }

  /** The newest ACPSessionControlsEvent's lists, or empty lists. */
  async getAcpSessionControls(conversationId: string): Promise<ACPSessionControls> {
    const page = await this.searchEvents(conversationId, {
      kind: ACP_SESSION_CONTROLS_EVENT_KIND, // (v2) was 'ACPSessionControlsEvent'
      sort_order: 'TIMESTAMP_DESC',
      limit: 1,
    });
    return acpSessionControlsOf(page.items);
  }
}

// clients/typescript/src/conversation/remote-conversation.ts (additions)
export class RemoteConversation {
  async setAcpConfigOption(
    configId: string,
    value: string | boolean
  ): Promise<ACPConfigOptionSetResponse> {
    const response = await this.client.post<ACPConfigOptionSetResponse>(
      `/api/conversations/${this.id}/acp/config-options`,
      { config_id: configId, value }
    );
    return response.data;
  }

  async getAcpSessionControls(): Promise<ACPSessionControls> {
    const response = await this.client.get<EventPage>(
      `/api/conversations/${this.id}/events/search`,
      { params: { kind: ACP_SESSION_CONTROLS_EVENT_KIND, sort_order: 'TIMESTAMP_DESC', limit: 1 } }
    );
    return acpSessionControlsOf(response.data.items);
  }
}
```

The bodies above are written out because they are the whole of each method; the exact option names
of `searchEvents` and the item type of its page follow the client's existing
`ConversationEventSearchOptions` and `ConversationEventPage`, which the Implementer checks. *(v2: the
page type `RemoteConversation` reads is `EventPage`, from `src/types/base`; the package root also
exports `isACPSessionControlsEvent`, `ACP_SESSION_CONTROLS_EVENT_KIND` and every type above.)*

---

## Appendix C · The scripted test agent

A Python script run as `[sys.executable, "tests/fixtures/acp/scripted_agent.py", *flags]`, built on
ACP Python's own agent side (`acp.run_agent`), with generic names only. S2 needs it to behave as
follows; S1's sub-agent behaviour lives in the same script behind its own flags (§8 item 13).

*(v2, §3.2 B9: built as below, at `28ca2e1`, 299 lines, with three differences.)* It is served
through `acp.connection.Connection` and `build_agent_router(…, use_unstable_protocol=True)` behind a
tap that writes the log and keeps `initialize`'s raw params, not `acp.run_agent`, so it can send raw
notifications (S1's `--subagents` and `--transcript` do). `--sessions-file PATH` keeps its sessions
in a JSON file, so `session/load` works across processes. And its log records notifications as well
as requests. Tests build its command with `scripted_acp_command(*flags)` and read its log through
the `acp_request_log` fixture, both in `tests/conftest.py`.

*(v2.4)* Unchanged by the refactor, 310 lines at `7f03b56`. The Scout's cut 3 would have served it
through `acp.run_agent` and dropped the `serve()` tap; the Conductor rejected it, because S1's
fixture needs the tap. Beside its helpers, `tests/conftest.py` now holds the `scripted_conversation`
fixture, which starts a `LocalConversation` on this agent with the given flags and agent fields, or
resumes a persisted one by `conversation_id`, and closes each after the test (`cd5db00`).

- **`initialize`:** advertises `sessionCapabilities.close` unless `--no-close`. *(v2: and
  `loadSession`.)*
- **`session/new`:** answers with one `select` option `profile` (values `fast` and `thorough`, current
  `fast`), then sends `available_commands_update` for the current value: `fast` →
  `summarize` (description "Summarize the input", no input); `thorough` → `summarize` and `compare`
  (description "Compare two things", input hint "what to compare"). With `--no-commands` it never
  sends commands. *(v2: the commands follow the answer by 50 ms, from a background task.)*
- **`session/set_config_option`:** an unknown id → invalid params "unknown option '{id}'"; an unknown
  value → invalid params "unknown profile '{value}'"; after the first prompt, any value but the
  current one → invalid params "profile is fixed once the session has started (it is '{current}')";
  otherwise it sends the new value's `available_commands_update`, then answers with the full options.
  With `--slow-set SECONDS` it waits before answering (for the timeout test). *(v2: an unknown
  session id → invalid params "unknown session '{id}'", here, in `session/prompt` and in
  `session/load`. v2.2, `5e3317f`: with `--set-error SENTENCE` it answers every set with an internal
  error (-32603) whose message is `SENTENCE`, and with `--auth-required` it answers `session/new`
  with ACP's authentication-required error (-32000).)*
- **`session/prompt`:** on the first prompt it sends `available_commands_update` with no commands and
  a `config_option_update` whose `profile` lists only the current value, then one
  `agent_message_chunk` echoing the prompt's first text block, a `usage_update`, and `end_turn`.
- **`session/load`:** loads a session it created in this process (or answers invalid params), answers
  with its options, and sends its commands if it has not been prompted. *(v2: in this process, or in
  an earlier one given the same `--sessions-file`.)*
- **`session/close`:** answers `{}`.
- **Request log:** when `SCRIPTED_ACP_LOG` names a file, it appends one JSON line per request
  (`{"method", "params"}`) in arrival order, so tests assert what reached the agent and when.
  *(v2: notifications too, such as `session/cancel`.)*
