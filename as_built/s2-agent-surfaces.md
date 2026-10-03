# S2 · Agent commands, options and App panels in the agent-server, as built

**TASK-6** · Cartographer · revision 2 · the code at `5e3317f`, head of `feat/agent-surfaces` in the SDK fork
[michaeltheologitis/software-agent-sdk](https://github.com/michaeltheologitis/software-agent-sdk) (draft PR #1 into
the fork's `deep-reasoning`, now `1f2b52d`; S2 is `git diff 1f2b52d..5e3317f`: 16 commits and two merges of
`deep-reasoning`) · divergences checked against the design at `9e32261` (v1, the design the build was made against;
see "The design moved" below) · agent-client-protocol 0.12.1 and websockets 15.0.1 (the fork's lock) · uv 0.12.23,
Python 3.13.14 and Node 22.22 in this sandbox · 2026-10-03.

**Revisions** (newest first).
- r2, code `5e3317f`: the three commits after `6f97bf3` verified (`c12f7b4` merges the fork-only `1f2b52d`; `13e5904`
  documents the icon route; `5e3317f` pins four status rows). D-5 rewritten: upstream's main-only guards now run on
  PR #1, but the REST check compares nothing. D-9 and D-10 now resolved. D-11 new: every 5xx answer's `detail` is
  "Internal Server Error". Two r1 claims were wrong and are corrected: that no failing macOS run existed (§2.4, §7),
  and that the weak-schema ratchet ran inside the agent-server suite (D-5). Counts, sizes, line numbers and the live
  run (37147707860, at `5e3317f` itself) updated.
- r1, code `6f97bf3`: `4f4bfc1`, carried on `design/s2` as `3ad786c`.

**The design moved.** This branch was reset to `design/s2` (`894ff3c`), which carries the System Designer's v2
(`4ad7f9c`) and v2.1 (`894ff3c`): they bring the design in line with the build at `6f97bf3` and with r1 of this
document. §2 still reports the divergences from v1 (`9e32261`), plus what the three new commits change. I did not
re-check the build against v2.1 in full: I read its Gate B section (its first 140 lines); a further read of the design
file was refused in this session, and I did not work around the refusal (§7). Two
statements in that section no longer hold at `5e3317f`: that upstream's main-only checks did not run in CI, and the
"Not run in CI" list under it (D-5).

**Where this file lives.** On deep-reasoning's branch `as-built/s2`, cut from `design/s2`: S2's code is in the SDK
fork, which carries only upstream-shaped code plus marked fork-only commits, so no document of ours goes there. This
branch holds only documents (no `pyproject.toml`, no docs site, no test runner), so nothing builds an sdist or
collects `as_built/`, and there is nothing to wire. Every other local deep-reasoning branch with a `pyproject.toml`
mentions `as_built` in it, except `wip/d2-on-d1`. [run: `git ls-tree` of this branch; `git show <branch>:pyproject.toml`
on every local branch]

**Evidence marks.** Every claim carries one.
- **[run]**: executed in this sandbox, never writing tracked files in the fork. At `5e3317f`: S2's 146 deterministic
  Python tests and their neighbours (§6.4), the OpenAPI type-quality check, and cherry-picks of each unit's commits
  onto the fork's `main` in a scratch clone. At `6f97bf3` (r1): the TypeScript client's suite and `tsc --noEmit` in a
  copy of `clients/typescript`, the persisted-settings guard, and uncommitted probe scripts that drive the scripted ACP
  agent through the real code (§6.6). Between the two commits nothing changed in the SDK, the TypeScript client or
  `acp_router.py`; the agent-server code changed only in the icon route's decorator [run: `git diff --stat 6f97bf3
  5e3317f`], so the r1 runs still describe that code.
- **[CI]**: read from GitHub's records through the GitHub MCP tools: the fork's runs at `5e3317f` (and earlier ones),
  and the live runs 37147707860 and 37141960911 in deep-reasoning (job steps and log tails; full log downloads are
  blocked here).
- **[read]**: read in the code, **not executed**. Weaker than [run]; §7 lists the read claims that matter.

Nothing here ran a paid model or the `claude` CLI. The claude-code previews in §6.3 are CI's (through `npx` with a
bogus key, no prompt).

**Reading order.** §2 first (the divergences), then §1 and §3–§4 as the map, §4.8 for what S1, C2 and D1 get, §6 for
E11 and the tests as measured, §7 for what I could not verify.

---

## 1 · What exists

S2 is three upstream-shaped units in one branch. Nothing in them names deep_reasoner or dr-acp or reads `_meta`.
[run: grep of the added lines]

1. **ACP session controls.** The ACP bridge records each ACP session's slash commands and config options; the agent
   publishes the root session's as one persisted, latest-wins `ACPSessionControlsEvent`; a start request can carry
   option values (`acp_config_options`), applied after `session/new` and before the first prompt; a route sets an
   option on a live session or keeps it for the start; `POST /api/acp/preview` runs the real start-up in a throwaway
   state and answers what the agent would offer. The TypeScript client gains the matching calls and types.
2. **Conversation header panels.** A Canvas App manifest may declare `contributes.conversation_panels`; the
   agent-server validates them, returns them in the manifest it already serves, and serves each panel's icon.
3. **App backends on macOS.** `darwin-amd64` and `darwin-arm64` backend platforms; loopback traffic to an App backend
   bypasses HTTP proxies; a `macos-app-backend-tests` CI job.

```text
Canvas (C2)                     agent-server (acp_router.py, conversation_service.py)        SDK (acp_agent.py …)                dr-acp
POST /api/acp/preview ───────▶ _resolve_launch (shared with POST /api/conversations)
  start payload + values        RunSlot → to_thread(preview_acp_session) ──────────────▶ throwaway ConversationState
                                                                                         ACPAgent.init_state: new → model ──▶ session/new …
                                                                                         → acp_config_options → mode ──────▶ set_config_option
◀── ACPSessionControls ◀─────── safe_rmtree(preview-<hex>), release slot ◀───────────── wait ≤ 2 s for commands, session/close, close()
POST /api/conversations ─────▶ fold values into ACPAgent.acp_config_options ──────────▶ LocalConversation._ensure_agent_ready
                                                                                         wires agent._on_session_event
updates ──────────────────────────────────────────────────────────────── bridge.session_update ◀── available_commands_update,
                                                                         _record_session_controls     config_option_update
WebSocket / events search ◀── persisted ◀── LocalConversation._emit_event_from_any_thread ◀── ACPAgent._publish_session_controls
POST …/{id}/acp/config-options ─▶ EventService → LocalConversation.set_acp_config_option ─▶ ACPAgent.set_acp_config_option ─▶ set_config_option
```

[read; each path run by the tests of §6.4]

| Unit | Commits (oldest first) | Code | Tests |
|---|---|---|---|
| 1 · session controls | `28ca2e1` scripted ACP agent · `c3d1db8` models and event · `d0d3fe1` record, publish, set · `5252840` preview · `e2ec3a9` agent-server routes · `4027912` live checks · `00a5310` TypeScript client · `5e3317f` four status rows pinned | +1,371 −113 | +2,470 −3 |
| 2 · header panels | `132db0f` manifest · `8523177` icon route and capability · `13e5904` icon route documented as PNG or SVG | +235 −13 | +359 |
| 3 · macOS | `759ffb2` platforms and loopback · `1d2627b` macOS job · `28e5654` REST-check allowlist · `0e24793` EPERM on macOS · `6f97bf3` fixture health budget | +109 −18 | +298 −13 |

In all (the net diff), +4,837 −155 in 48 files: SDK +818 −27, agent-server +647 −112, TypeScript client +200 −1, CI
+49 −3, Python tests +2,968 −11, TypeScript tests +155 −1. The per-commit figures above sum to 5 lines more, because
`13e5904` and `5e3317f` rewrite lines S2 itself added. The branch also holds two merges of the fork's
`deep-reasoning`: `aff05f6` brings in `ea51b3f` (fork-only: the test suites on GitHub-hosted runners) and `c12f7b4`
brings in `1f2b52d` (fork-only: upstream's main-only guards on pull requests into `deep-reasoning` and `feat/**`,
D-5). [run: `git log`, `git diff --numstat`, `git show --numstat`]

---

## 2 · Divergences from the design (`9e32261`)

The changelog held no `drift:` line for TASK-6 when r1 was written, so every item below was found from the code. All
of S2's commits came after `9e32261`. "Design §x" cites `9e32261` (v1). v2 and v2.1, written after r1, say they bring
the design in line with the build and with r1; which of D-1 to D-10 they absorb, and how, I did not check (§7). [run:
Notion query of the Changelog at r1; `git log`]

### 2.1 Behaviour a client or an agent sees

**D-1 · The events search finds the controls only by the module-qualified kind.** Design §4.7 (the fourth row), §7
item 4 and Appendix B read the newest controls with `GET …/events/search?kind=ACPSessionControlsEvent&…`. The search
compares `kind` with `f"{event.__class__.__module__}.{event.__class__.__name__}"` (`event_service.py:548–551`), so
`kind=ACPSessionControlsEvent` matches nothing; the value that works is
`openhands.sdk.event.acp_session_controls.ACPSessionControlsEvent`. The serialized event still carries
`"kind": "ACPSessionControlsEvent"`. The TypeScript client exports that string as `ACP_SESSION_CONTROLS_EVENT_KIND`
(`clients/typescript/src/models/acp-session-controls.ts:62–63`) and both `getAcpSessionControls` use it; C2 uses the
constant too (§4.8). Reason (commit `00a5310`): "searched by the module-qualified kind the events search matches".
[run: probe, short kind `False`, qualified `True`; the router test `test_the_events_search_returns_the_newest_controls_event`]

**D-2 · An empty `available_commands` can mean "not reported yet", not "none".** Design §7 item 4 says no event means
the agent has reported nothing, and item 5 that an empty `available_commands` means the agent offers none now. Built,
`_start_acp_server` publishes the root session's snapshot once the start returns (`acp_agent.py:3119–3131`), and the
agent's `_published_session_controls` starts at `None`, so every session start persists one event, even an empty
one. The bridge is new at each start, so that event carries whatever this connection has recorded so far; an agent
that sends its commands after the `session/new` (or `session/load`) response, as the scripted agent does and as
dr-acp does (its menu is sent from a task that follows the response, D1's as-built §4.1 [read]), has not been heard
yet. Measured with the scripted agent [run: probes, §6.6]:

| Start | Events persisted, in order |
|---|---|
| fresh, no option values (3 trials) | `[] / profile=fast`, then `[summarize] / profile=fast` |
| fresh, `profile=thorough` | `[summarize, compare] / profile=thorough` (the set's response follows the commands, so one event) |
| reload of that conversation (`session/load`) | `[] / profile=thorough`, then `[summarize, compare] / profile=thorough` |

So a client that reads the newest event between the two sees an empty menu for a moment after every start and every
resume (and after a drain-timeout restart, which also builds a new bridge [read]). The design's §4.3 algorithm
produces this; its §7 contract does not say it. The PR body records the first half: "Every ACP session start now
persists one controls event, even when the agent reports nothing." No reason recorded for the second.

**D-3 · The preview answers 501 in the Docker runtime.** `preview_acp_session` takes the HTTP request and refuses with
501 "This operation is unavailable in Docker runtime mode" (which reaches the client in `exception`, D-11) when
`app.state.config.conversation_runtime == "docker"` (`acp_router.py:85–91`). Design §4.7 has no such status. Reason
(the code's comment): "The Docker runtime runs agents in conversation containers; a preview on this server would run
the agent outside them." The set route has no such check. [run:
`test_the_preview_is_unavailable_in_the_docker_runtime`]

**D-4 · Unusable entries are dropped by ACP's own schema, before S2's code.** Design §4.1 has S2's normalizer drop
unknown option types (logged at debug), unwrap `.root`, read a hint through `RootModel` or directly, turn a missing
description into `""`, and `ACPConfigOption.from_protocol` return `None` for a type it lacks. Built, the parsers take
ACP 0.12.1's typed objects (`AvailableCommand`; `SessionConfigOptionSelect | SessionConfigOptionBoolean`) and have no
drop path except a nameless command (`acp_models.py:111–120, 166–185, 223–249`); `ACPConfigOption.from_protocol`
returns `ACPConfigOption`. Agent-client-protocol 0.12.1 itself drops, from the update or response that carries them,
a config option of another type, a command without a description, and a non-string hint (the command is kept without
input). Consequences: a description-less command is dropped, not kept with `""`; nothing is logged for a dropped
option. Reason (the docstrings): "ACP's own schema drops them". [run: REPL, `AvailableCommandsUpdate.model_validate`
of `{"hint": 3}` and description-less entries; `test_entries_the_protocol_cannot_parse_are_dropped_not_raised`]

**D-11 · Every 5xx answer carries "Internal Server Error" as its `detail`.** Design §4.7 gives the preview's 502 as
"the agent failed to start (`detail` names why)". Built, the routes raise `HTTPException(status, detail)`, and the
agent-server's handler (upstream's, `api.py:692–711`) answers any 5xx `HTTPException` with `{"detail": "Internal
Server Error", "exception": "<status>: <detail>"}` (a traceback only under `DEBUG`). The set route's -32603 is not an
`HTTPException` and reaches the unhandled-exception handler (`api.py:611–667`): `{"detail": "Internal Server Error",
"exception": "<the agent's message>", "error_id": …}`. So the preview's 501, 502 and 504 and the set route's 504 carry
their reason only in `exception`, prefixed by the status; every 4xx keeps it in `detail`. Reason (the handler's
comment): "Don't leak internal details to clients for 5xx errors in production." [run:
`test_the_preview_answers_an_authentication_failure_with_502_not_401` asserts `{"detail": "Internal Server Error",
"exception": "502: [-32000] Authentication required"}`; read: 501 and 504]

### 2.2 The fork's pull requests and upstream's guards

**D-5 · One draft PR into `deep-reasoning`, none into `main`; upstream's main-only guards now run on it, but the REST
check compares nothing.** Design §1 and §9 (layer 3): each unit's commits, cherry-picked onto the fork's `main`, get
a draft PR there, so the guards that run only for pull requests to `main` run as upstream would run them. Built: PR
#1 (`feat/agent-surfaces` → `deep-reasoning`) carries all three units, and the fork has no other PR but S1's #2,
stacked on it. [CI: PR list] Up to `6f97bf3` the main-only guards did not run on it (r1). The fork-only `1f2b52d`,
merged as `c12f7b4`, adds `deep-reasoning` and `feat/**` to the `pull_request` branch filters of five workflows (REST
API breakage, persisted settings, TypeScript client CI, TypeScript client integration tests, version bump guard), and
at `5e3317f` they ran on PR #1, all green [CI]:

- **Persisted settings** (run 37146974370): 17 fixtures and 8 payloads from PyPI 1.50.1 validated, as in my r1 run.
- **TypeScript client CI** (37146974358): lint (0 errors; 7 warnings, none in S2's files), build, 23 files and 355
  tests, format, public type budget, agent-server API, security, provider validation. **Integration tests**
  (37146974428): deterministic tests against an agent-server image built from the branch; the LLM-backed step took
  0 s.
- **Version bump guard** (37146974326): its SDK API compatibility step was skipped, because no package version
  changed. So the SDK API breakage check has still never run on S2.
- **REST API breakage** (37146974332): **green without comparing anything.** The script builds the baseline schema
  with `git archive v1.50.1`; the fork has no `v1.50.1` tag (its only tag is `dr-1`), so the step logs "Failed to
  extract source for v1.50.1 … not a valid object name" as a warning, and `main()` returns 0 after only its static
  policy checks (`.github/scripts/check_agent_server_rest_api_breakage.py:1024–1026`). oasdiff never compared S2's
  schema in CI; the only comparison on record is the Implementer's local run at `28e5654` (PR body). [CI: job log;
  read: the script; the fork's tag list]

The OpenAPI weak-schema ratchet (`make test-server-schema`, in `server.yml`) still runs only for pull requests into
`main`. r1 said it ran inside the agent-server suite, and that was wrong: `tests/agent_server/test_openapi_contract.py`
tests the detector on made-up findings, not the server's schema. At `6f97bf3` the icon route, a `FileResponse` the
route did not declare, was a new weak location that no CI caught (`13e5904`'s message); `13e5904` declares it. I ran
the ratchet's type-quality check at `5e3317f`: it passes, with 62 allowlisted weak locations; the export is
deterministic. [run; `swagger-cli validate`, the target's last step, not run]

**D-6 · Unit 3 does not cherry-pick onto `main` alone.** Design §1: the three touch disjoint files except two, "so
each PR's commits cherry-pick onto the fork's `main` without the others". Units 1 and 2 each cherry-pick onto `main`
(`53a4bc5`) cleanly, `5e3317f` and `13e5904` included. Unit 3 stops at `759ffb2` with a conflict in
`tests/agent_server/canvas_extensions/test_canvas_extensions_manifest.py`: its two platform tests are appended after
unit 2's panel tests. Resolved by keeping only unit 3's block, the other four commits apply cleanly. The two shared
source files (`manifest.py`, `server_details_router.py`) do not conflict. [run: scratch clone]

**D-7 · Build order.** Design §1: unit 3 first, then 2, then 1. Commit order is 1, 2, 3. [run: `git log`]

**D-8 · One REST-check allowlist entry.** Design §2 decision I, §8 item 14 and §10 item 8 expect no new allowlist
entry; §6.4 names this one as the fallback if oasdiff flags `BackendPlatform`'s new keys. Built:
`_EXTENSIBLE_DISCRIMINATOR_PROPERTY_RE` gains `CanvasExtensionBackend\b.*\bartifacts/propertyNames\b`
(`.github/scripts/check_agent_server_rest_api_breakage.py:646`) with a test that only that property is downgraded.
Reason (commit `28e5654`): "oasdiff reports a new key of CanvasExtensionBackend.artifacts (its propertyNames enum) as
a breaking response enum addition." [run: the test; the oasdiff result itself is the commit message's, and CI's REST
check has never compared schemas (D-5), §7]

### 2.3 Signatures and small behaviours

None of these changes what §2.1 describes. [read unless marked]

| Design | Built |
|---|---|
| `ACPAvailableCommand.from_protocol(raw: Any)`, `ACPConfigOption.from_protocol(raw: Any) -> ACPConfigOption \| None`, `parse_*(raw: Sequence[Any])` (A.1) | typed ACP arguments, non-optional return (D-4) |
| `LocalConversation._event_emitter: ThreadPoolExecutor \| None`, created on first use (§4.3, A.4) | created in `__init__` (`local_conversation.py:320–324`); its thread starts on the first submit |
| `_starting_session` set at the top of `_start_acp_server`, cleared in a `finally` (§4.3) | the body moved into a new `_launch_acp_session`; `_start_acp_server` wraps it (`acp_agent.py:3119–3135`) |
| preview directory removed with `shutil.rmtree(…, ignore_errors=True)` (§4.6) | the agent-server's `safe_rmtree(persistence_dir, "ACP preview directory")` in a thread (`conversation_service.py:1997–2000`) |
| route `preview_acp_session(request, conversation_service)` (A.7) | adds `http_request: Request` for D-3 |
| bridge methods of A.3 | adds `_notify_session_controls_changed`, which logs a publisher exception at warning and swallows it (`acp_agent.py:1587–1594`) |
| Appendix B: search with `kind: 'ACPSessionControlsEvent'`; `ConversationEventPage` | `ACP_SESSION_CONTROLS_EVENT_KIND` (exported), a helper `acpSessionControlsOf` (`src/events/types.ts:268`, not exported from the package root), `EventPage` in `RemoteConversation` |
| endpoint-audit entry "tracking our fork's draft PR" (§4.8) | no `tracking` field (`endpoint-audit.config.json:39–43`) |
| — | the default visualizer gains an "ACP Session Controls" entry (`visualizer/default.py:211–214`) |
| icon route `responses={404: …}` (A.8) | also `response_class=FileResponse` and a 200 whose content is `image/png` or `image/svg+xml`, each a binary string (`canvas_extensions_router.py:459–471`, `13e5904`) |
| Appendix C: the scripted agent on `acp.run_agent` | on `acp.connection.Connection` with `build_agent_router` behind a tap (so it can send raw notifications and read `initialize`'s raw params); adds `--sessions-file` (load across processes); logs notifications as well as requests (`tests/fixtures/acp/scripted_agent.py:258–289`); since `5e3317f` also `--set-error SENTENCE` (-32603 from every set) and `--auth-required` (-32000 from `session/new`) |
| live tier: Claude Code, Codex, Gemini; `model` asserted "where the registry says" (§9) | all six registry providers (adds kimi-code, pi, opencode); `model` asserted when `agent._model_via_config_option` is set after the preview (`test_acp_session_controls_live.py:115–137`); the file joins upstream's `acp-live-tests` job and its change filter (`tests.yml:161, 194`) |
| §6.3: the existing backend lifecycle tests run unchanged on macOS | the fixture drops its 3 s health timeout for the manifest's 30 s default and gains `launch_delay`; a slow-launch test pins it (`6f97bf3`, reason: a cold `/usr/bin/python3` on a fresh macOS runner took about 3 s) |

### 2.4 Tests and the proof

**D-9 · Rows of §4.7 that had no test at `6f97bf3`, pinned since `5e3317f`.** §4.10 asks for "the set route's
statuses for every row of §4.7". r1 found four untested; `5e3317f` adds a test for each [run]:
`test_a_set_on_a_service_that_closed_after_its_lookup_is_a_bad_request` (400, detail `inactive_service`),
`test_an_internal_error_from_the_agent_is_a_500_carrying_its_message_unmasked` (500; the agent's message in
`exception`, unmasked even though it holds the value of one of the conversation's secrets, while the refusal path
masks it, `acp_agent.py:631–640`), `test_the_preview_of_a_profile_with_a_dangling_mcp_reference_is_refused` (422,
`dangling_mcp_server_refs`), and `test_the_preview_answers_an_authentication_failure_with_502_not_401` (D-11). The
route harness now answers unhandled errors as a deployed server does (`httpx.ASGITransport(…,
raise_app_exceptions=False)`). CI's coverage of `acp_router.py` went from 98 % (line 97 unhit) to 100 %. [CI]

**D-10 · The dr-acp live tier ran at S1's head; since run 37147707860 it has run at S2's own.** Design §9: the
workflow "checks out the fork at the task branch's head". Run 37141960911 (r1) checked out
`feat/acp-subagent-sessions` at `0cfb6a2` (S1, which contains `6f97bf3` and five commits of its own touching
`acp_agent.py` +327, `local_conversation.py` +18, `acp_router.py` +69 and the scripted agent). Run 37147707860 checked
out `5e3317f` itself, with only the S2 step selected: 8 passed (§6.3). [CI: the checkout steps; run: `git diff
--stat 6f97bf3 0cfb6a2`]

**Resolved open items of design §10.** Item 2: the test agent is `tests/fixtures/acp/scripted_agent.py`, and S1
extends it. Item 1: S1 uses `_on_session_event` and the emitter (§4.8). Item 5: see D-8 and D-5. Item 3: the dr-acp
job is `fork-live.yml` on deep-reasoning's `ci/fork-live` (§6.3). Item 6: websockets 15.0.1 has the `proxy`
parameter, so the WebSocket item stays [run: `inspect.signature`]; and macOS answered `killpg` with EPERM, as the
macOS job showed twice before the fixes [CI]:

- Run 37088961132 at `28e5654`: the macOS job failed 2 of 172 tests, `test_prepare_start_logs_stop_and_preserve_data`
  and `test_failed_start_cleanup_and_unsupported_states`, each with `PermissionError: [Errno 1] Operation not
  permitted` from `os.killpg(pgid, 0)` in `_group_alive`. `0e24793` then treats `PermissionError` as "gone" on Darwin
  only (`_group_exited`, `backend.py:110–120`).
- Run 37090131688 at `0e24793`: 176 passed and `test_prepare_start_logs_stop_and_preserve_data` failed with `assert
  'unhealthy' == 'ready'`, under the fixture's 3 s health budget, which `6f97bf3` removes.

Both runs show `queued` overall, because their jobs on Blacksmith runners never started; the macOS and Windows jobs
ran on GitHub's. r1 read only the run-level status and wrongly said no failing run existed. [CI: the jobs and their
logs]

Not divergences: decisions A–I as written (one latest-wins event kind; one ordered, lock-taking emitter;
launch-only values folded into the agent and applied only to a fresh `session/new`, refused with
`ACPConfigOptionRejected`; the preview as the real start-up under `conversations_dir/preview-<hex>` holding a run
slot; `model` refused everywhere; one id namespace, a contained icon with its own route, `exclude_if` on an empty
panel list; the macOS loopback fix and job; the two capability strings), and design §3 items 1–3 (the REST shapes),
§4.4 (the order and the refusal path), §5.1 (the manifest rules), §6.1 (the platform tables) and §8 (the rules shared
with S1). [run for every behaviour the tests of §6.4 name; read for the rest]

---

## 3 · The public surface, from the code

**REST.** Every 5xx answer's body is `{"detail": "Internal Server Error", "exception": …}` (D-11); "reason" below means
`detail` for a 4xx and `exception` for a 5xx. [run: the router tests, except where marked]

| Route | Body | Answer | Statuses |
|---|---|---|---|
| `POST /api/acp/preview` (`acp_router`) | the start payload (`StartConversationRequest`), its `acp_config_options` applied | `ACPSessionControls` | 400 not an ACP agent · 404 unknown profile · 422 invalid request, a `model` value, values for a non-ACP agent, a dangling MCP reference, or a value the agent refused (reason: its sentence) · 429 run limit · 501 Docker runtime (D-3) [read: its body] · 502 any other start failure (spawn, authentication, init; reason e.g. `502: [-32000] Authentication required`) · 504 start-up timeout [read: its body] |
| `POST /api/conversations/{id}/acp/config-options` (`conversation_acp_router`) | `{"config_id": str (min 1), "value": str \| bool}` | `{"applied": bool, "controls": ACPSessionControls}`: live → `true` and the agent's controls; before the start → `false` and empty controls | 400 not ACP, `model`, inactive service · 404 unknown conversation · 422 refused (reason verbatim, e.g. `profile is fixed once the session has started (it is 'fast')`) · 504 no answer in 30 s [read: its body] · 500 the agent's -32603 (reason: its message, unmasked) |
| `POST /api/conversations` | gains `acp_config_options: {id: str \| bool}` | unchanged | 422 with a non-ACP agent or a `model` key |
| `GET /api/conversations/{id}/events/search?kind=openhands.sdk.event.acp_session_controls.ACPSessionControlsEvent&sort_order=TIMESTAMP_DESC&limit=1` | — | the newest controls event (D-1) | — |
| `GET /api/canvas-extensions/installed/{name}/panels/{panel_id}/icon` | — | the icon file, `image/svg+xml` or `image/png`, with `Cache-Control: no-cache`, `X-Content-Type-Options: nosniff`, `Content-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; sandbox` | 404 unknown App, unknown panel, no icon, or an icon no longer contained (re-checked per request). Documented in the OpenAPI as a 200 of `image/png` or `image/svg+xml` binary |
| `GET /server_info` | — | `capabilities` gains `acp_session_controls_v1` (default list) and `canvas_conversation_panels_v1` (appended in `build_server_info`) | — |

Both new routers live in `openhands/agent_server/acp_router.py`, registered in `api.py:457–458` after
`conversation_router`; the start route's `except` gains `InvalidACPConfigOptions` (`conversation_router.py:285`).
[read]

**The event and its DTOs** (`openhands/sdk/agent/acp_models.py`, `openhands/sdk/event/acp_session_controls.py`,
exported from `openhands.sdk.event`): `ACPSessionControlsEvent(available_commands, config_options)`, `source`
`"agent"`, `from_controls`, `.controls`, a one-line `visualize` (`Commands: /a /b | Options: id=value`);
`ACPSessionControls`, `ACPAvailableCommand(name, description, input: ACPCommandInput(hint) | None)`,
`ACPConfigOption(id, name, type: "select" | "boolean", current_value: str | bool, description, category, options)`,
`ACPConfigOptionValue(value, name, description, group)`. Grouped selects are flattened with `group` set to the
group's name; `category` keeps ACP's four string categories and is `None` for ACP's dict form. [run: tests]

**SDK.** `ACPAgent.acp_config_options: dict[str, str | bool]` (validator refuses `""` and `"model"`),
`ACPAgent.session_controls` (property), `set_acp_config_option(config_id, value) -> ACPSessionControls`,
`wait_for_available_commands(timeout)`, `close_acp_session(timeout=2.0)`; `ACPConfigOptionRejectedError(config_id,
value, message)` (a `ValueError`, `str()` the agent's message, masked); `_classify_acp_init_error` returns
`"ACPConfigOptionRejected"` for it first. `LocalConversation.set_acp_config_option(config_id, value) ->
ACPSessionControls | None`. `openhands.sdk.conversation.acp_preview`: `preview_acp_session(agent, workspace,
persistence_dir, *, secrets=None, cipher=None, commands_wait_seconds=2.0)`, `ACPPreviewError(code, detail)`,
`PREVIEW_COMMANDS_WAIT_SECONDS = 2.0`. `StartConversationRequest.acp_config_options` (same validator). The
environment variable `ACP_CONFIG_OPTION_TIMEOUT` (default 30 s) bounds one set. [run: tests; the variable read]

**Manifest** (`canvas_extensions/manifest.py`). `contributes.conversation_panels: [{id, title, icon?, tabs: [{id,
title, path="/"}]}]`: ids kebab-case and unique across pages, panels and tabs of one App; titles non-empty; at least
one tab; a tab path `/` or an absolute kebab-case path, unique within its panel; an icon a package-relative `.svg` or
`.png`, refused if absolute or with `..`, and at install and on every serve refused unless it resolves (symlinks
followed) to a regular `.svg`/`.png` file inside the package. An empty list is left out of every dump, so a manifest
without panels dumps byte for byte as before. `BackendPlatform` adds `darwin-amd64`, `darwin-arm64`. [run: tests]

**TypeScript client** (`clients/typescript`, version unchanged at 1.50.1). New module
`src/models/acp-session-controls.ts` (the DTOs field for field, `ACPConfigOptionValues`, the set request and
response, `ACP_SESSION_CONTROLS_EVENT_KIND`); `ACPSessionControlsEvent` joins the `ConversationEvent` union with
`isACPSessionControlsEvent`; `ConversationClient.previewAcpSession(payload)`, `setAcpConfigOption(conversationId,
configId, value)`, `getAcpSessionControls(conversationId)`; `RemoteConversation.setAcpConfigOption(configId, value)`,
`getAcpSessionControls()`; `CreateConversationPayload.acp_config_options?`. All re-exported from the package root,
except the helper `acpSessionControlsOf`. [run: tests; read: exports]

---

## 4 · Structure and seams

### 4.1 Recording and publishing (where the complexity sits)

**The bridge records per session id.** `_OpenHandsACPBridge.session_update` runs `_record_session_controls` first,
right after the idle-clock reset (`acp_agent.py:1611`); it consumes `AvailableCommandsUpdate` and
`ConfigOptionUpdate` for any session id and returns before any other routing. The responses of `session/new`,
`session/load` and every `session/set_config_option` (S2's and the model path's, through the new
`on_config_options` argument of `_apply_acp_model` and its two callers) are recorded too. Each record parses, masks
the whole dumped entry with the conversation's secret masker, rebuilds the models, and replaces that session's
`ACPSessionControls` snapshot (never mutated); `record_available_commands` also sets the session's
`threading.Event`, which `wait_for_available_commands` waits on. Then it notifies the agent. [read:
`acp_agent.py:1525–1594`; run: `test_agent_supplied_text_is_masked_before_it_is_stored`,
`test_each_session_keeps_its_own_controls_and_only_the_root_is_published`]

**The agent publishes the root's.** `_bind_session_controls` points the bridge's callback at a weak reference to the
agent; `_publish_session_controls` returns unless `_on_session_event` and `_session_id` are set and no start is in
progress, then, under `_session_controls_lock`, reads the root's snapshot, returns if it equals the last one
submitted, and otherwise builds the event and submits it. `_start_acp_server` sets `_starting_session` around
`_launch_acp_session` and publishes once after it (D-2). [read: `acp_agent.py:3119–3135, 4862–4894`; run:
`test_nothing_is_published_while_a_session_is_starting`, `test_an_unchanged_snapshot_is_not_published_again`]

**The emitter.** `LocalConversation._ensure_agent_ready` sets `agent._on_session_event =
self._emit_event_from_any_thread` for an `ACPAgent`, before `init_state` (`local_conversation.py:1577–1578`). The
emitter submits `_on_event_with_state_lock` (upstream's, it takes the state lock and calls `_on_event`) to a
one-worker `ThreadPoolExecutor`; a submit after `close()` (which shuts it down with `cancel_futures=True`) is
dropped with a debug log. So events persist and reach every callback (in the agent-server, the WebSocket and the
webhooks) in submission order, and submission order is snapshot order. [read; run:
`test_concurrent_publishes_keep_snapshot_order_and_end_on_the_newest`,
`test_a_portal_thread_event_during_a_synchronous_run_lands_after_the_step`,
`test_events_from_other_threads_are_persisted_in_submission_order`, `test_events_emitted_after_close_are_dropped`]

**The agent swap.** `switch_acp_model` and `set_acp_config_option` both go through `_replace_acp_agent(update, live=)`
(`local_conversation.py:1834–1863`): `model_copy(update=…)`; when live, the copy takes over atexit cleanup,
file-credential masking and the bridge's publish callback, and the old agent's runtime is released. The shallow copy
shares `_session_controls_lock` and carries `_published_session_controls` and `_on_session_event`. [run: probe;
`test_the_agent_swap_hands_publishing_to_the_copy`]

Without a `LocalConversation` (the preview, an agent driven by hand) `_on_session_event` is `None` and nothing is
emitted; `ACPAgent.session_controls` is always readable. [read]

### 4.2 Option values

At the start, in `_init`'s fresh-session branch only: `new_session` → record its options → the existing model call →
`_apply_config_options(conn, session_id, self.acp_config_options, …)` → the existing `set_session_mode`
(`acp_agent.py:3480–3531`). After a successful `session/load` the load response's options are recorded and nothing is
applied; a failed load falls through to the fresh branch, which applies everything. `_apply_config_options` sets
each value in dict order and records every response; -32603 is re-raised unchanged, any other `ACPRequestError`
becomes `ACPConfigOptionRejectedError` with the masked message. At the start that error leaves `init_state` through
its existing handler: `ConversationErrorEvent(code="ACPConfigOptionRejected", detail=<the sentence, redacted, masked,
≤ 500 chars>)`, status `ERROR`, cleanup, re-raise; the first message is persisted and never prompted. The
bridge's own `set_session_mode` comes after the values, so for an agent whose `mode` option is its session mode a
start value for `mode` is followed by the bridge's mode [read]; the claude-code preview reports
`mode=bypassPermissions` (§6.3) [CI]. [read; run: `test_start_values_reach_the_agent_after_session_new_and_before_the_prompt`,
`test_a_refused_start_value_ends_the_start_and_no_prompt_is_sent`, `test_after_a_successful_load_no_value_is_reapplied`,
`test_after_a_fallback_to_a_fresh_session_every_value_is_reapplied`; CI for the mode value]

A set, `LocalConversation.set_acp_config_option` (`:1795–1832`): non-ACP agent → `ValueError`; `""` or `model` →
`ValueError`; then under the state lock, if the session is live, the agent's call (on the portal, bounded by
`ACP_CONFIG_OPTION_TIMEOUT`; a refusal propagates before anything is written), and in every case
`_replace_acp_agent({"acp_config_options": {…, config_id: value}})`, which persists the value in `base_state.json`.
A pre-start set therefore reaches the agent at the start, and a live set survives a reload and is reapplied by a
fallback to a fresh session. `EventService.set_acp_config_option` runs it in the default executor and raises
`ValueError("inactive_service")` without a conversation. The state lock is the one `_ensure_agent_ready` holds during
`init_state`, so a set during a start waits for it. [read; run: the set tests of
`test_local_conversation_acp_config_option.py` and of the router]

### 4.3 The preview

`ConversationService.preview_acp_session` (`conversation_service.py:1966–2002`): `_resolve_launch(request)`; a
non-ACP agent → `ValueError("preview needs an ACP agent")`; `with await RunSlot.acquire(self._run_semaphore)`; in a
thread, the SDK's `preview_acp_session` with `persistence_dir = conversations_dir / f"preview-{uuid4().hex}"`; finally
`safe_rmtree`. The SDK function (`acp_preview.py:48–99`): an empty `persistence_dir/workspace` when the working
directory does not exist; `ConversationState.create`; the secret registry seeded from the agent context's secrets,
then the request's; `agent.init_state(state, on_event=<discard>)` under the state lock, any failure re-raised as
`ACPPreviewError(_classify_acp_init_error(e), _acp_error_detail(e, registry))`; `wait_for_available_commands(2.0)`
(returns at once once the root has reported commands); `close_acp_session()` (`session/close` only if `initialize`
advertised `sessionCapabilities.close`, 2 s, errors logged); `agent.close()` in a `finally`. No plugins and no
per-conversation file-credential bindings are loaded (design §3 item 5). [read; run: `test_acp_preview.py`, 11
tests, and the router's preview tests, which also check that no `preview-*` directory is left]

### 4.4 The agent-server's shared launch

`_resolve_launch` (`conversation_service.py:1848–1964`) is `_create_conversation`'s former block, moved verbatim
(settings, profile resolution and its secret allow-list, `load_memory`, ACP skill sourcing, the system-message
suffix), plus the fold: non-empty values with a non-ACP agent → `InvalidACPConfigOptions`; the `model` check repeated
(`model_copy` skips validators); `agent.model_copy(update={"acp_config_options": {**agent's, **request's}})`.
`_create_conversation` calls it first (`:1668`) and excludes `acp_config_options` from the stored record (`:1773`),
so the values live only inside the agent in `base_state.json`. [read: diff; run:
`test_resolve_launch_gives_the_start_and_the_preview_the_same_agent` ×3, `test_the_start_folds_option_values_into_the_agent_only`]

### 4.5 Panels

Validation sits in the manifest models (`manifest.py:77–186`); the filesystem check is
`resolve_package_file(package_root, relative, what)`, extracted from `resolve_entrypoint` and shared with
`resolve_panel_icon` (`:357–398`). The install path validates every panel's icon (`installed.py:62–63`);
`get_canvas_extension_panel_icon_path` re-resolves it per request against the live install and answers `None` on any
failure (`installed.py:254–271`); the route maps `None` to 404 and takes the media type from the resolved file's
suffix (`canvas_extensions_router.py:459–491`). The icon is served whether the App is enabled or not, and needs the
session key like every route. [read; run: the manifest, containment and router tests]

### 4.6 macOS

`current_platform()` maps `platform.system()` and `platform.machine().lower()` through two tables to the four names,
else `None` (`backend.py:162–173`). The health probe opens through `_LOOPBACK_OPENER` (`ProxyHandler({})`,
`:54–56, 431`); `proxy_http` builds its `httpx.AsyncClient` with `trust_env=False` and `bridge_websocket` passes
`proxy=None` when the target host is `127.0.0.1`, `::1` or `localhost` (`docker_runtime/proxy.py:79–84, 151, 227`);
other targets keep `trust_env=True` and `proxy=True` (websockets' default). `_signal_group` and `_group_alive` treat
`ProcessLookupError` as gone everywhere and `PermissionError` as gone on Darwin only (`_group_exited`,
`backend.py:110–120`). [read; run: platform table, dead-proxy probe, bridge and EPERM tests on Linux; CI: the macOS
job, §6.1]

### 4.7 What it relies on

- **agent-client-protocol 0.12.1**: that its schema drops unusable entries instead of failing the update (D-4)
  [run]; that `ClientSideConnection.close_session` exists [run: tests]; that a notification sent before a response
  is handled before the awaiting call resumes. Notifications run as tasks created before the response future is
  resolved, and the record happens before the handler's first suspension, so in the preview the commands sent for a
  chosen value precede the set's return [read: `acp/connection.py:152–164`].
- **The agent's order**: the preview's commands are those of the chosen value only if the agent sends them before
  its `set_config_option` response (D1 §5.4 rule 5; the scripted agent does the same). An agent that sends them
  later would be previewed with the commands it reported first. [read]
- **websockets 15.0.1** (`proxy` parameter) [run]; pydantic's `exclude_if` [run: the dump test]; upstream's
  `RunSlot` and `ConversationRunLimitExceeded` handler (429) [run: test]; `_on_event_with_state_lock` [read].

### 4.8 Who consumes S2, and what each relies on

- **S1** (`feat/acp-subagent-sessions`, now `a3279be`, 12 commits on `5e3317f`; draft PR #2 based on
  `feat/agent-surfaces`). It sets `client.on_session_event = self._on_session_event` at each launch, so every
  child-session event goes through S2's emitter: design §8 item 6's "one primitive" holds. It keeps S2's recording
  line first in `session_update`, adds its cancel route to `conversation_acp_router`, and extends the scripted agent
  (+463 lines). It does not change `_replace_acp_agent`, the preview or the panels. [read: `git diff 6f97bf3 0cfb6a2`
  at r1, and the same lines at `a3279be`]
- **C2** (Canvas fork `feat/agent-surfaces`, `db3b4b9`, read only). Through the TypeScript client:
  `ConversationClient.previewAcpSession` with the start payload plus `acp_config_options`, `setAcpConfigOption`,
  `ACP_SESSION_CONTROLS_EVENT_KIND` for its own newest-event search, and the types `ACPSessionControlsEvent`,
  `ACPSessionControls`, `ACPConfigOptionSetResponse` (`src/api/conversation-service/agent-server-conversation-service.api.ts:662–690`,
  `src/hooks/query/use-latest-acp-session-controls.ts:50`). It does not use the client's `getAcpSessionControls` or
  its guard; it keeps the newer by timestamp of the live store's and the search's newest event, so D-2's transient
  empty menu reaches it. Directly: both capability strings (`src/api/agent-server-compatibility.ts:161–162`),
  `manifest.contributes.conversation_panels`, the icon route fetched with the session key
  (`src/api/canvas-extensions-service.ts:202–210`), and the `ACPConfigOptionRejected` code
  (`src/utils/acp-error-codes.ts:10`). Its `package-lock.json` names npm's `@openhands/typescript-client` 1.50.1; its
  `node_modules` holds a build versioned 1.50.1 that carries S2's `acp-session-controls` module. [read]
- **D1's dr-acp** (deep-reasoning `c8d7fbb`). S2 forwards `session/set_config_option(namespace, …)` after
  `session/new` and before the first prompt, passes `/name …` text through unchanged, records dr-acp's menu and
  option updates, and returns its refusal sentences verbatim. S2 relies on dr-acp sending a new namespace's menu
  before the set's response (§4.7), and on its clearing the menu and narrowing the namespace when it accepts the
  first prompt (the live tier asserts both outcomes, §6.3). dr-acp's default namespace is the config's
  `entry_namespace` (`advising` in the live config), so the live tier's `root` is a non-default value. [read; CI]

---

## 5 · Wiring

CI (`.github/workflows/tests.yml`): `macos-app-backend-tests` on `macos-latest` (Python 3.13, `uv sync --frozen
--group dev`), gated by `tj-actions/changed-files` on `canvas_extensions/**`, `docker_runtime/proxy.py`,
`tests/agent_server/canvas_extensions/**`, `pyproject.toml`, `uv.lock` and the workflow, running `pytest -vvs
tests/agent_server/canvas_extensions`; the existing `acp-live-tests` job also runs S2's live file. The endpoint audit
lists the two new routes as client-ahead. [read] The fork-only `1f2b52d` (in the branch through `c12f7b4`) runs five
of upstream's main-only workflows on pull requests into `deep-reasoning` and `feat/**` (D-5). PR #1's body still
groups the units as 7, 2 and 3 commits (`28ca2e1..00a5310`, `132db0f..8523177`, `759ffb2..28e5654`); the branch has
8, 3 and 5. Since `5e3317f` the body also carries CI's generated REST contract summary, a diff of the public OpenAPI
against the base `1f2b52d` (not against `v1.50.1`): three operations, the icon route's PNG and SVG 200, the new
schemas, `acp_config_options` on `ACPAgent` and `StartConversationRequest`, and `ACPSessionControlsEvent` in the
`Event` `oneOf`. [CI: PR body]

The dr-acp live job is deep-reasoning's `.github/workflows/fork-live.yml` on branch `ci/fork-live` (`a8154e2`, D1's
head `c8d7fbb` plus this workflow): `workflow_dispatch` with `sdk_ref` (default `deep-reasoning`), `suites`,
`sdk_repo` and `live_config`; fails without the `OPENAI_API_KEY` secret; reads `deep_reasoner_beta` with
`DEEP_REASONER_TOKEN`; runs S2's file with `OPENHANDS_ACP_LIVE_AGENT_COMMAND="<dr-acp> --config
docs/configs/advising/main.yaml --home <tmp>"`, `OPENHANDS_ACP_LIVE_CONFIG_OPTIONS='{"namespace": "root"}'` and
`OPENHANDS_ACP_LIVE_EXPECT_COMMANDS_CLEARED=1`. [read]

---

## 6 · Experiments and tests, as measured

### 6.1 The runs

| Run | Commit | Conditions | Result |
|---|---|---|---|
| fork `Run tests` [37146974364](https://github.com/michaeltheologitis/software-agent-sdk/actions/runs/37146974364) | `5e3317f` | `pull_request` into `deep-reasoning`; ubuntu-24.04, Python 3.13 | all jobs green: sdk 6,699 passed, 7 skipped, 12 xfailed · agent-server 2,431 passed · cross 496 passed, 1 skipped · tools, workspace, stress, windows green · `macos-app-backend-tests` (arm64, macos-latest) 178 passed in 24.7 s · `acp-live-tests` 25 passed, 2 skipped (§6.3) [CI] |
| fork, the formerly main-only guards on PR #1 | `5e3317f` | REST API breakage 37146974332, persisted settings 37146974370, TypeScript client CI 37146974358, its integration tests 37146974428, version bump guard 37146974326 | all green; what each did is D-5 (the REST check compared nothing) [CI] |
| fork, other workflows on PR #1 | `5e3317f` | pre-commit, docstrings, endpoint audit, deprecation deadlines, test-directory allowlist | green; "Validate PR description" skipped; 28 check runs in all [CI] |
| fork `Run tests` 37099674559 (r1) | `6f97bf3` | the same | all jobs green; agent-server 2,426 passed; macOS 178 passed in 19.7 s [CI] |
| fork `Run tests` 37090190722 | `aff05f6` | the same | green, macOS job included [CI] |
| fork `Run tests` 37090131688 | `0e24793` | only the macOS, Windows and allowlist jobs ran (the rest stayed queued) | macOS **failed**: 1 failed, 176 passed (§2.4) [CI] |
| fork `Run tests` 37088961132 | `28e5654` | the same | macOS **failed**: 2 failed, 170 passed (§2.4) [CI] |
| deep-reasoning `fork-live` [37147707860](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37147707860) | SDK `5e3317f` (S2 alone), deep-reasoning `a8154e2` | ubuntu-latest, Python 3.12.3, uv 0.12.23, `OPENAI_API_KEY` (gpt-6-luna); S2 step only | S2's file: **8 passed** in 123.8 s, 4 warnings (§6.3) [CI] |
| deep-reasoning `fork-live` [37141960911](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37141960911) (r1) | SDK `0cfb6a2` (S1 on S2), deep-reasoning `a8154e2` | the same; both steps | S2's file: **8 passed** in 100.2 s (S1's file in the same job: 2 passed) [CI] |
| this sandbox, S2's files and neighbours | `5e3317f` | Linux, Python 3.13.14, serial, `--basetemp` outside `/tmp`: S2's test files, `tests/agent_server/canvas_extensions`, the canvas router, the cross breakage tests, all of `test_conversation_service.py` and `test_openapi_contract.py` | **493 passed**, 8 deselected (the live file); S2's 146 deterministic tests among them [run] |
| this sandbox, OpenAPI type-quality check | `5e3317f` | `export_agent_server_openapi.py` twice, then `check_agent_server_openapi_quality.py` | export deterministic; passed, 62 allowlisted weak locations [run] |
| this sandbox, TypeScript client (r1) | `6f97bf3` | a copy of `clients/typescript` with its `node_modules` | 23 files, **355 passed**; S2's three files 125 passed; `tsc --noEmit` clean [run]; the client is unchanged at `5e3317f` |
| this sandbox, persisted-settings guard (r1) | `6f97bf3` | `.github/scripts/check_persisted_settings_compat.py` | 17 fixtures and 8 PyPI-1.50.1 payloads validated, exit 0 [run] |

With the default temporary directory, one upstream test in that local run fails here,
`test_start_conversation_with_worktree_ignores_non_git_workspace`, because this sandbox's `/tmp` is itself a git
repository (r1); with `--basetemp` outside `/tmp` it passes. [run]

I did not run the whole SDK and agent-server suites, so I saw neither the 11 wsproto errors nor the cross-test
failure the brief says appear here under parallelism; CI is the record for the full suites.

Reproduce: `OPENHANDS_SUPPRESS_BANNER=1 uvx uv@latest run --frozen python -m pytest <files of §6.4>`; the live tier
by dispatching `fork-live.yml` with `sdk_ref` (a run costs one gpt-6-luna prompt and six provider start-ups).

### 6.2 E11 · agent surfaces, S2's part

| E11 claim (design §9) | In S2, measured | Result |
|---|---|---|
| The home-screen preview lists the namespace's commands | `test_the_preview_equals_the_started_session_before_its_first_prompt[{} / fast / thorough]`: the scripted agent's previews list `[summarize]`, `[summarize]`, `[summarize, compare]` and equal the started session's controls [run]. Live: dr-acp's preview with `namespace=root` equals the started session's controls in full [CI] | passed. Which commands `root` offers is neither asserted nor printed by the live tier |
| Changing the namespace changes them | the three previews above differ by value [run]; a pre-start set changes what the started session reports (`test_a_set_before_the_start_is_persisted_and_applied_at_the_start`, `test_a_set_before_the_start_is_kept_for_it`) [run]. Live: one value only | passed with the scripted agent; **not measured with dr-acp** |
| The started run uses the chosen namespace | the agent's request log has `session/set_config_option` after `session/new` and before the first `session/prompt` [run]; live: after the first prompt the reported `namespace` is `root` [CI] | passed |
| Commands are gone after the first message | scripted: the first prompt's events end with `[]` commands and a one-value option (`test_a_started_session_reports_the_chosen_value_and_cleared_commands`, probe) [run]; live: the last controls event after the prompt has no commands [CI] | passed |
| A refused value fails the start, in the agent's words (S2's falsifier) | `ConversationErrorEvent.code == "ACPConfigOptionRejected"`, detail `unknown profile 'turbo'`, no `session/prompt` sent; the preview's 422 with the same sentence [run] | passed |
| The panel mounts with the right conversation, not beside the drawer | — (S2 has only the manifest and icon) | C2's |
| The Library App's backend starts on macOS and Linux | the backend lifecycle tests start a real (Python) backend artifact on macOS and Linux [CI, run] | passed; D3's real artifact is not in S2 |

### 6.3 The live tier

`test_acp_session_controls_live.py` (`pytestmark = acp_live`). Run 37147707860, at `5e3317f` itself; durations from
log timestamps [CI]:

| Test | Asserts | Result |
|---|---|---|
| `test_a_built_in_provider_can_be_previewed[claude-code, codex, gemini-cli, kimi-code, pi, opencode]` | `npx` with a bogus key, isolated environment, no prompt: a preview succeeds; every command has a name; `model` is among the options when the session selects its model through config options | 6 passed, 13.0–21.6 s each (first `npx` use included). Commands/options seen: claude-code 40 / `mode, model, effort, fast`; codex 17 / `mode, collaboration_mode, model, reasoning_effort, fast-mode`; gemini-cli 20 / none; kimi-code 15 / `model, thinking, mode`; pi 8 / `model, thought_level`; opencode 3 / `model, mode`; all options `select` |
| `test_the_preview_lists_what_the_started_session_lists` | dr-acp, `namespace=root`: `preview_acp_session(...) == ` the started conversation's controls once its newest event is persisted, with no message sent | passed; 6.6 s for one preview and one start (dr-acp's two `initialize` answers logged 3.7 s apart) |
| `test_the_first_prompt_runs_with_the_chosen_values` | dr-acp: send `Reply with the single word: ready.`, run (a `ConversationRunError` is tolerated); the reported `namespace` is `root`; the last controls event after the user message has `available_commands == []` | passed; 8.2 s; the prompt returned in 6.3 s |

The four warnings are `PytestUnraisableExceptionWarning`s: a subprocess transport collected after its event loop
closed ("Event loop is closed"), in the gemini-cli, kimi-code and pi previews and in the dr-acp parity test; no
assertion depends on them. The commands and options listed are identical to r1's run 37141960911 at `0cfb6a2` (S1 on
S2), where the same 8 passed in 100.2 s (previews 12.8–18.4 s, the parity test 3.8 s, the prompt 5.1 s). The six
previews also pass in the fork's own `acp-live-tests` job, at `6f97bf3` and at `5e3317f`, where the two
environment-gated tests are skipped. [CI] No run prints its model spend.

### 6.4 The deterministic tests S2 adds (146, all passing) [run]

By unit and file (test cases after parametrization):

- **Unit 1, 89.** `test_acp_models.py` 7 (the hint through `RootModel`, no input, nameless commands dropped in order,
  grouped and ungrouped selects, booleans, a dict category becomes `None`). `test_acp_session_controls_event.py` 4
  (JSON round-trip as its own kind, the one-line render, an empty render, skipped by `render_resume_transcript`).
  `test_acp_session_controls.py` 25 (publishing after the start, during a prompt, per session, unchanged snapshots,
  protocol drops, masking, a concurrency stress test with a fake sink, nothing while starting; values after
  `session/new` and before the prompt, in order with every response recorded, -32603 unchanged, a refused start value,
  no reapplication after a load, reapplication after a fallback; `model` and `""` refused in the field and the set; a
  model switch updating the published `model` option; a live set, a refusal, no session, a timeout).
  `test_local_conversation_acp_config_option.py` 10 (pre-start and live sets persisted and applied, a refused set
  writes nothing, the swap hands over publishing, refusals, a portal-thread event during a synchronous `run()`,
  after-close drops, submission order). `test_acp_preview.py` 11 (preview equals start ×3, `session/close` sent or
  not, the 2 s wait, a refusal, a spawn error, no process left ×2, an empty scratch workspace). `test_acp_router.py`
  29 (the preview for `agent`, `agent_settings`, `agent_profile_id`; five failure statuses; an authentication failure
  answered 502, not 401; 404; a dangling MCP reference; `model`; the run slot; Docker 501; the start fold and the
  started session's state; the events search; two start refusals; nine set cases: before the start, live, a refusal,
  not for this route ×2, a service closed after its lookup, an unknown conversation, the agent's -32603 as an unmasked
  500, a timeout; `server_info`). `test_conversation_service.py` +3 (`_resolve_launch` per way of naming the agent).
- **Unit 2, 36.** Manifest +22 (C2's mock-up validates, tab defaults, a tab at `/` and a page not, twelve malformed
  panels, shared id namespace ×5, the dump without panels unchanged and with panels present); containment +5 (a
  contained icon; four uncontained or non-image icons); router +8 (list and get, the icon's type and headers ×2, three
  404 cases, re-checked containment, `server_info`); the OpenAPI contract +1 (the icon route documented as a PNG or
  SVG image).
- **Unit 3, 21.** Backend +17 (the platform table ×10, readiness through a dead proxy, a 3.5 s slow launch, EPERM
  on macOS and elsewhere ×4, a stop that completes through EPERM); bridge +1 (HTTP and WebSocket to a loopback backend
  through a dead proxy); manifest +2 (darwin keys accepted, an unknown key refused); the REST-check allowlist +1.

Plus the 8 live cases of §6.3 and TypeScript +7 cases in `api-clients.test.ts` and `event-types.test.ts` (and an
updated export list in `index.test.ts`). Every test of design §4.10, §5.3 and §6.3 exists under a name that states
its property; the four rows D-9 named have had theirs since `5e3317f`. [run: collection and runs; read: the mapping]

### 6.5 Upstream's guards (design §4.9, §6.4)

| Guard | Result |
|---|---|
| Weak-schema ratchet (`make test-server-schema`) | still main-only, not in CI; its type-quality check passes at `5e3317f` [run]; at `6f97bf3` the icon route was a new weak location (`13e5904`) [read] |
| Persisted settings | green in CI at `5e3317f` [CI]; passed locally at `6f97bf3` [run] |
| REST breakage (oasdiff 1.19.1 against v1.50.1) | green in CI at `5e3317f` without a comparison: no `v1.50.1` tag in the fork (D-5) [CI]; the Implementer's local run at `28e5654` passes after D-8's allowlist [read: PR body]; not run by me |
| SDK API breakage (`version-bump-guard.yml`) | the job runs at `5e3317f` but skips the check, no version having changed (D-5) [CI]; not run by me |
| Docstrings, pre-commit, endpoint audit | green [CI] |
| TypeScript client CI and integration tests | green in CI at `5e3317f`: lint, build, 355 tests, format and the rest (D-5) [CI]; suite and typecheck passed locally at `6f97bf3` [run] |

### 6.6 Measurements I made (uncommitted probes, scripted agent, this sandbox) [run]

- **Preview wall time**, three trials each: no values 1.79, 2.07, 1.86 s; `profile=thorough` 1.07, 1.55, 1.82 s; an
  agent that never reports commands (`--no-commands`) 2.85, 3.95, 4.71 s, its start-up plus the 2 s wait. The
  scripted agent is a Python process importing `acp`; dr-acp's own preview time is not separately measured (§6.3 has
  the CI timestamps).
- **Event sequences** of D-2.
- **The search filter, the swap's shared lock and the empty first publish** of D-1, §4.1 and D-2.

---

## 7 · What I could not verify

1. **The REST breakage comparison** (oasdiff on the new routes, the new event `oneOf` member and `BackendPlatform`'s
   keys) has run only in the Implementer's sandbox, at `28e5654`: CI's REST check now runs but finds no `v1.50.1`
   baseline in the fork and compares nothing (D-5). D-8's premise, that oasdiff flags `propertyNames`, is the commit
   message's. The SDK API breakage check has run nowhere (CI skips it without a version change). I ran neither
   (oasdiff and the v1.50.1 baseline build are not set up here).
2. **macOS.** The two failures behind `0e24793` and `6f97bf3` are in CI's history (§2.4); that the EPERM came from a
   group whose members were all zombies, and the 3 s from a cold `/usr/bin/python3`, are the commit messages'
   readings. macOS on Intel (`darwin-amd64`, Rosetta) is never run.
3. **The live tier and the namespace**: with one value only, it cannot show a menu that changes with the namespace,
   nor which menu `root` has.
4. **Ordering inside ACP Python** (§4.7): read in `acp/connection.py`, not stressed; the scripted-agent tests cannot
   expose a violation because the scripted agent never sends a stale menu before a set.
5. **Unit isolation**: I cherry-picked each unit onto `main` (D-6) but did not run any unit's tests in isolation.
6. **The 501 and 504 bodies** (D-11) are read from the handler, not run; the 502's is run.
7. **C2's use** is read from its code at `db3b4b9`; nothing of C2 was run, and how C2 renders D-2's transient empty
   menu was not checked.
8. **The live runs' cost**: not printed.
9. **The design at v2.1** (`894ff3c`): I read its Gate B section only; a further read of the design file was refused
   in this session, so I did not check the build at `5e3317f` against v2.1's §3–§10, nor which of D-1 to D-11 v2 and
   v2.1 absorb. Divergences here are from v1.

If this document resists shortening, the part that resists is §2: the code follows the design closely, and what
differs is spread across the contract C2 reads (D-1, D-2, D-11), the fork's PR shape and its guards (D-5 to D-8), and
the proof (D-9, D-10).
