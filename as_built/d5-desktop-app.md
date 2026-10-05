# D5 · Desktop app: build, install and launch, as built

**TASK-10** · Cartographer · revision 3 · 2026-10-05 · the code at **`3e9cee9`** (head of `v1-desktop`, after the
small fixes and the literate refactor; this file is on `as-built/d5`, which merges it at `926dd36`) · checked against
design v2 (`docs/design/d5-desktop-app.md`, last changed in `9ee36f6`, unchanged at `3e9cee9`) · Canvas fork `dr-3` =
`4355a36` and SDK fork `dr-2` = `34c540c`, read only.

**Revisions.** r1 (`81814f4`) read the code at `3c923aa`. r2 (`bbdeb5f`) read `c9bb7fe`, after r1's four fixes that
Michael approved. r3 reads `3e9cee9`: two small fixes, `3919e92` (the README's facts, r2's §6 #8) and `8125fa1` (every
unusable `setup.json`, r2's §6 #9), then the literate refactor, `d9b35f4` to `3e9cee9` (§8). Section and finding
numbers are kept since r1, which Gate B's reading may cite; a finding fixed since is marked **Closed in rN** where it
stood. New in r3: §1.1 #22–#25, §1.3 #6–#7, §6 #11–#13 and §8.

**What D5 is, in git.** `v1-desktop` was cut from `main` at `1f9fe52` and has merged `main` three times (D4 `53c821b`,
`b2a74e0`, `f1ca641`); `main` (`f1ca641`) is an ancestor of `3e9cee9`, so `git diff f1ca641 3e9cee9` is D5 and
nothing else [run]. That is 50 commits: the design's two (`8086afb`, `9ee36f6`) and 48 of code and tests. Two more
are on `main`, through #34 and #35: the workflow copies decision M asked for.

**Evidence marks.** Every claim carries one.
- **[run]**: executed on this machine at `3e9cee9` (§5.4): the default suite on Python 3.12.3, `build.py check` and
  check 8's GitHub reader against the forks, a real first install, setup's three failure cases on `3c923aa`'s and
  `3e9cee9`'s `dr-app`, `dr-app` against six `setup.json` files, `git` and GitHub's REST API.
- **[run at 3c923aa]**, **[run at c9bb7fe]**: r1's and r2's probes, not repeated, where what they ran is unchanged.
- **[CI]**: read from GitHub's logs of the runs in §5.1 and §5.3, and from the app logs the macOS jobs keep as
  artifacts. I dispatched no workflow and made no model call.
- **[read]**: read in the code and **not executed**. This is weaker evidence than [run]. §7 lists the read claims
  that matter most.

**Reading order:** §1, the divergences (start here); §2–§4, the map, the surface and where the complexity is; §5, the
measured results; §6, the open items, with what Gate C should know (§6 #11); §7, what I could not verify; §8, the
refactor.

---

## 1 · Divergences from design v2

The design has not changed since `9ee36f6`, written before any code. The Changelog's one entry for TASK-10 (2026-10-04
20:47, the Canvas fixes) has an empty Drift line [read: Notion], so everything below was found in the code, its
history or the runs.

### 1.1 Built otherwise than the design says

| # | Design says | Built | Where | Reason recorded |
|---|---|---|---|---|
| 1 | §1 item 1, §4.2.4 step 3, §5.8, §7.6: one universal `.dmg`; `build.py {linux\|mac\|mac-universal\|check}`; `ELECTRON_ARCH=universal` | **Apple silicon only.** Targets `linux` and `mac-arm64`; each refuses to run on any machine but Linux x86-64 or macOS arm64, because the fork packages uv and Node for the machine it builds on. `verify()` requires `deep-reasoning-<version>-arm64.dmg`, and `lipo -archs` = `arm64` for the `.app`'s Electron, uv and Node. `desktop-release.yml` has no Intel job; a tag's release needs `linux` and `macos`. [read; run: `test_build.py`; CI] | `desktop/build.py:45-65, 161-180, 462-507` | Michael: "lets drop the intel macs" (`bd6e170`). The Intel lock holds `2e883e7` and `a4a9336` were undone by `3500f87` [run at 3c923aa] |
| 2 | No macOS version is named | **macOS 14 or later, enforced. Closed in r2.** The locked packages install only from macOS 14: onnxruntime 1.30.0 (chromadb's, through deep_reasoner) ships `macosx_14_0_arm64` wheels and none older [run at 3c923aa, §5.4]. The wrapper config's `mac` block declares `minimumSystemVersion: "14.0"`, and `verify()` refuses a `.app` whose `Info.plist` declares any other `LSMinimumSystemVersion` (#19). Pinned by `test_a_mac_app_that_opens_before_macos_14_is_refused` [run]; the real `.app` passes on GitHub's macOS runner [CI]. That macOS 13 then refuses to open it is macOS's handling of the key, not run [read] | `desktop/electron-builder.dr.mjs:18-19`; `build.py:57-59, 503-506` | onnxruntime's wheels; `e5c8be2`, Michael's approval of r1's §6 |
| 3 | §4.4.3: `uv venv --managed-python --python 3.12 runtime/<commit>.tmp-<pid>`, then rename | `uv venv --relocatable --managed-python …`, then (since r3, #22) `uv sync` into it. Without `--relocatable`, uv writes entry points with an absolute shebang to the temporary path, and after the rename every runtime command was dead: `dr-library` exited 127 as the App backend [read; run: §5.4, the entry points start `#!/bin/sh`; CI: E12] | `runtime.py:157-165` | `622976b`, found by E12's first launch |
| 4 | §4.4.1: three rules for the data home | **A fourth.** `choose_home` and `dr-app home DIR` refuse, exit 13 with `home_too_long`, a home under which `runs/<run id>/children/<n>/repl.sock` (the home plus 52 bytes) would pass the Unix-socket limit: 107 bytes on Linux, 103 on macOS. The default homes fit (on macOS, user names up to 28 characters); a HOME under macOS's `$TMPDIR` is refused [read; run at 3c923aa: `deepest_socket`, the bootstrap's exit 13] | `layout.py:35-39, 117-161` | `b1e3df2`: deep_reasoner's Claude backbone serves its REPL socket under the run directory |
| 5 | §4.7.3: "no usage reported: the reservation stands" | Usage reported, at any status: charged. No usage on a 2xx: the reservation is charged. **No usage on a non-2xx: 0**, the reservation released. Upstream unreachable: 0 [read; run: `test_provider_errors_release_their_reservations`, `test_a_call_costs_its_reported_usage_else_its_reservation_unless_refused`] | `proxy.py:505-519, 546-552` | Michael's ruling (`f385025`): the OpenAI client's four retries of a 500 had left five reservations standing as spend |
| 6 | §4.7.3's request path | Two additions. A body that is not a JSON object, or is over 32 MiB, is refused 400 `bad_body`, a sentence §6 lacks. `Accept-Encoding` is not forwarded and `Content-Encoding` not returned, so bodies pass uncompressed [read] | `proxy.py:55-78, 386-406` | none recorded |
| 7 | §4.3.1, §6, decision B: the fetch-failure line says deep-reasoning "is private: ask Michael for read access…" | "✗ Could not fetch github.com/michaeltheologitis/deep-reasoning: check that this computer is online, then restart. Nothing was installed." [read; run: `test_bootstrap.py`] | `desktop/bootstrap.sh:14` | deep-reasoning is public (`3c923aa`) |
| 8 | §3 item 2: users need read access to both repositories. §2.2: "Releases are assets of a private GitHub repository". §7.5: CI reads deep-reasoning through an `insteadOf` line | deep-reasoning is public [run: `gh api`]: only deep_reasoner_beta needs read access, release assets are public downloads, and no workflow adds an `insteadOf` for deep-reasoning (the one for DeanLight stays) [read] | `.github/workflows/` | Michael: "public downloads are fine" |
| 9 | §1.3 (D5 owns "the README's install section"), §2.3, §3 item 12, §4.2.6 (`xattr -dr com.apple.quarantine …`), §4.8.3 (uninstall) | **A root `README.md`. Closed in r2.** It holds the install section the design asks for; how it differs is #18. `tests/desktop/test_readme.py`, 8 tests, pins its names and commands to the code's constants: the `.dmg`'s name and the macOS minimum, the quarantine command, the model key and where setup asks for it, setup's access check, the `PATH` line and the linked commands, the uninstall paths, the safety sentence with the default cap, and (since r3) the data table against `AppLayout`'s paths and `dr-app home`'s length limit against the socket constants [run] | `README.md`; `tests/desktop/test_readme.py` | `c9bb7fe`; Michael approved the fix |
| 10 | §7.5: four jobs, `pins`, `desktop-e2e`, `bridge-replay`, `canvas-replay`; decision M: a `nightly.yml` on `main` dispatches `cross-repo.yml` | **Closed in r3: the four jobs.** At `c9bb7fe` there were six (`has-d5` and `library-app` besides). Since `146bbbf` `cross-repo.yml` has §7.5's four; `library-app`'s `crossrepo` test runs in `bridge-replay`'s job, now 12 tests with D4's forwarding test; `desktop-release.yml` has no `has-d5` either. `cross-repo.yml` schedules itself (`17 6 * * *`) and `v1-desktop` deletes `nightly.yml`. GitHub runs a schedule only from the default branch, so until D5's stack merges, `main`'s own `nightly.yml` keeps dispatching `cross-repo.yml` on `v1-desktop`; once it merges, `nightly.yml` leaves `main` and the schedule runs there [read; CI] | `.github/workflows/cross-repo.yml` | `146bbbf`, Scout findings 1 and 2 |
| 11 | Decision M: `main` carries copies of the on-demand workflows | `main`'s copies (`f1ca641`) are older than `v1-desktop`'s: both have `has-d5`; its `desktop-release.yml` builds `mac-universal`, which `build.py` rejects; its `cross-repo.yml` has `has-d5`, `library-app` and `bridge-replay` only. No run uses them while `main` lacks `desktop/pins.toml`, since there `has-d5` skips every job. Dispatched runs and the nightly dispatch use `v1-desktop`'s files, and a tag the tagged commit's [run: `git diff`; read]. Without `has-d5` on `v1-desktop`, a pull request whose merged tree has the new `cross-repo.yml` but no `desktop/pins.toml` runs its jobs, which fail reading the pin [read]; §6 #12 | `main`'s `.github/workflows/` | #34 and #35 placed them before the later commits |
| 12 | §7.5's seven steps and the final flow | **17 tests sharing one launch** (§5.2). Where they differ: the first conversation is onboarding's hello, not a dismissed onboarding; two tests the design does not list check that no consent dialog shows (a fixed 5 s wait) and that no consent is recorded and Settings has no analytics switch; the Library config is written by the test (there is no `e12/main.yaml`); Stop's plan spawns the done sibling first and holds the grandchild's model call until `dr-acp` logs `stop.accepted`; costs are compared with each sub-agent's cost in the run log at its end; the next conversation asks a plain question after the slash menu offers the command (the design asks for the offer and the recorded version, which hold); the cookie is read with `Storage.getCookies`; the MCP server is added through `POST /api/settings/mcp/echo` and the Tools tab reopened; the quit test asks that no process's command line names the fresh HOME. Since `6ee106c` the harness calls the agent-server through `dr_app.agent_server.AgentServer` [read; CI] | `tests/desktop/test_e12.py`, `tests/desktop/app.py` | `c538fb3`, `1a90887`, `d39be70`, `8ce99b2`; Canvas `dr-3` (§1.2); TASK-38 |
| 13 | §7.6: the macOS job launches the app once and waits for `backend ready` | One launch, two tests: `app_ready(…, "installed")` in the log, the backend `ready`, the app quits with 0; and, on macOS, `lipo -archs` of the launched executable and of the bundled uv is `arm64` [read; CI] | `tests/desktop/test_launch_smoke.py` | `bd6e170` |
| 14 | §4.2.2's eight checks, check 8 through a blobless fetch; §5.8 | **Seven checks.** 1, each fork's tag (`git ls-remote`); 2, the wiring, as two sentences (repository, commit); 3, the TypeScript client; 4, one ACP Python, the SDK fork's `uv.lock` read from `raw.githubusercontent.com` at its commit; 5, the fork leaves `paths.stateDir` and `setup.command` null (not all of `setup`: the fork sets `setup.phases`); 6, a clean and pushed checkout; check 7 is gone with the file it checked (#22); 8, through GitHub's compare API, `repos/<fork>/compare/<commit>...deep-reasoning`: `ahead` or `identical` passes, any other status or a 404 refuses, and `GITHUB_TOKEN`, when set, authenticates (the `pins` job passes it). `--work` holds only the Canvas checkout. `build()` copies the artifacts to `<repo>/dist/` [read; run: §5.4] | `build.py:220-277, 309-336, 422-426` | `f28730d`, Scout finding 4 |
| 15 | §5.2 puts `SetupError` in `dr_app.runtime`; §4.3.2's exit codes; §6's table | `SetupError` lives in `dr_app.layout`, beside one table of the exit codes and what each means (2, 10–14). Five sentences §6 lacks: `NO_AGENT_SERVER` (after-ready without the launcher's variables, exit 2), `home_refused` (`dr-app home` with a relative path or a network filesystem), `home_too_long` (#4), `state_from_a_newer_app` and `state_unusable` (#20) [read] | `layout.py:18-23, 43-50`; `texts.py:31-34, 97-118, 136-150` | `0f1d0e0` |
| 16 | §8.7: an MCP server's environment holds "only its configured variables and `mcp`'s six" | The test also admits `LC_CTYPE`, which D4's stdio guard, a Python, adds when it coerces a C locale (PEP 538). It runs twice, with and without the model key named in the server's settings [read; run] | `tests/acp/test_e10_keys.py:220-288` | in the test's comment |
| 17 | §10: ≈1.45k lines of code, ≈1.24k of tests | **≈3.0k and ≈4.5k** [run: `wc -l`, `git diff --numstat`]. Code: 2,913 lines in D5's own files (339 of them workflows) and +128 net in D1's. Tests: 4,423 in D5's own files and +114 net in D1's and D3's. The README is 208. Largest: `test_e12.py` 727, `proxy.py` 681, `test_key_proxy.py` 657, `build.py` 532. Counted as the Gate C ledger counts (non-blank added lines, `uv.lock` and the design not counted), code went from 2,644 to 2,579 in the refactor and tests from 3,999 to 3,917 [read: the Refactorer's count] | — | §4 says where it went; §8 what the refactor took out |
| 18 | §2.3: the README's install section is "§2.2 in short, with how to uninstall"; §4.2.6, §4.8.3, §3 item 12 | The README follows the build where it and §2.2 differ: release assets are public downloads. It adds what the design lacks: setup's own access check to run in a terminal; that a credential helper named without a path must sit in `/opt/homebrew/bin` or `/usr/local/bin` on a Mac; the `.AppImage`'s steps; a hand-run build's artifacts, which need a GitHub sign-in; onboarding (keep **deep_reasoner**, press **Close** on **Say hello**, add `OPENAI_API_KEY` under Settings → Secrets before the first question); how to change the cap; Electron's own folders in uninstall. **Corrected in r3** (`3919e92`), r2's findings: the timing now reads "the install takes under 20 s, and setup's two phases … about a minute" on the macOS runner, which the runs bear out (12–16 s; 42–65 s, §5); "a `v*` tag gets a release …; until the first tag, take them from a build run by hand", and there is still no tag or release [run: `gh api`]; the data table names `canvas-app/` and `setup.lock`; `dr-app home DIR` is said to take at most 55 bytes on Linux and 51 on macOS; `pyproject.toml`'s `readme` is `README.md` [read; run: `test_readme.py`] | `README.md` | `c9bb7fe`, `3919e92` |
| 19 | §4.2.4: the wrapper config, whole; `verify()` checks names, payload paths and, since #1, Mach-O architectures | The wrapper config adds one key, `mac: { ...base.mac, minimumSystemVersion: "14.0" }`, so it is no longer §4.2.4's byte for byte. `verify()` reads the built `.app`'s `Info.plist` with `plistlib` and refuses an `LSMinimumSystemVersion` other than `MAC_MINIMUM` (`"14.0"`) with a sentence §6 lacks, `opens_too_early` [read; run: `test_build.py`; CI] | `electron-builder.dr.mjs:18-19`; `build.py:57-59, 176-180, 503-506` | `e5c8be2`: #2's fix |
| 20 | §4.3.2 and §6: exit codes 0, 10–13 and 2; `SetupState.load` "raises on v != 1" (§5.1) | **Exit 14: `setup.json` is unusable**, inside the bootstrap's trusted 10–19 band. An integer `v` above 1 gives `state_from_a_newer_app` ("✗ {path} was written by a newer Deep Reasoning (its version {version}; this one reads 1). Install the newer app again. …"). Since `8125fa1` every other unusable file gives `state_unusable(path, reason)` ("✗ {path} cannot be used: {reason}. Delete it and launch the app again: setup then installs as on a first launch, which needs the network. …"), with one of six reasons: it cannot be read, it is not JSON, it is not a JSON object, its version is …, it has no version, it holds a record this app does not write [read; run: five of the six, §5.4] | `layout.py:224-263`; `texts.py:136-150` | `930a0cf`, `8125fa1`: r1's §1.3 #4, r2's §6 #9 |
| 21 | §4.2.2 check 8: a blobless fetch into a cache, then `FETCH_HEAD` | **Closed in r3: superseded.** At `c9bb7fe` a cache that existed was refetched with an explicit refspec. Since `f28730d` there is no cache: check 8 asks GitHub (#14) | — | `24646d0`, then `f28730d` |
| 22 | Decision C, §3 item 4, §4.2.2 check 7, §4.4.2, §4.4.3, §5.2: a committed export of `uv.lock`, `runtime.lock.txt`, installed with `uv pip sync` beside two git lines; `RuntimeSpec`; the record compares commit and lock digest | **The runtime is `uv sync` of the commit's own tree.** `fetched_source` creates `runtime/<commit>.tmp-<pid>-source` (`git init`, `git fetch --depth 1 <repo> <commit>`, `git checkout FETCH_HEAD`); `deep_reasoner_pin` reads deep_reasoner's URL and commit from that tree's `uv.lock`; `install_runtime` runs `uv venv --relocatable --managed-python --python 3.12 <runtime>.tmp-<pid>`, then `UV_PROJECT_ENVIRONMENT=<that venv> uv sync --frozen --no-dev --no-editable --all-packages --project <tree>`, the import check, the rename and the link; the tree is removed. `runtime_is_current` compares the commit only, which fixes its `uv.lock`. `RuntimeRecord.lock_sha256` is still written (the tree's `uv.lock`'s digest) and no check reads it, so a `setup.json` written at `3c923aa` or `c9bb7fe` still loads. Gone: `runtime.lock.txt`, `RuntimeSpec`, `LOCK_RESOURCE`, `DEEP_REASONER_LINE`, check 7, `UV_EXPORT`, `RUNTIME_LOCK`, `lock_stale`. The installed set is the same 173 packages at the same versions as `3c923aa`'s lock gave; only deep-reasoning's and deep-reasoning-app's recorded source changes, from a git URL to a `file://` URL into the removed tree [read; run: §5.4] | `runtime.py:97-188` | `d9b35f4`, Scout finding 3 |
| 23 | §4.4 step 4, §4.4.2: git, deep_reasoner readable (from the packaged lock), `uv`, and nothing fetched before they pass | **The order is now** git's version, `uv` on `PATH`, the fetch of deep-reasoning's tree, then deep_reasoner's readability (its URL from the fetched `uv.lock`), then `checks_ok`, the safety line and `installing`. `install_failed` can now name `git init`, `git fetch`, `git checkout`, `uv venv`, `uv sync` or the import check. What a user sees changes on two error paths (§6 #11) [read; run: §5.4] | `cli.py:108-132`; `runtime.py:116-137` | `d9b35f4`: the readability check needs the URL in the fetched lock |
| 24 | §4.5.1 step 4: the profile's id from `GET /api/agent-profiles` (listing also runs upstream's one-time seeding, so ours is activated after it) | The id comes from `GET /api/agent-profiles/deep_reasoner`, read again after a write for the server's id; setup no longer lists. The seeding needs an empty store with no active pointer [read: SDK `34c540c`, `agent_profiles_router.py:256-282`], and setup has written `deep_reasoner` before any listing, so neither version ever seeded [read; run: `test_profile.py`; CI: E12's first test checks the active pointer] | `profile.py:64-98` | `9002014`, Scout finding 5 |
| 25 | §5.1: `AppLayout.state_dir`. §5.7: `proxy.DEFAULT_SPEND_CAP_USD`, and a frozen `Spend(session, cap_usd, …)` from `SpendLedger.spend` | `AppLayout.state_dir` is gone (nothing read it). The default cap is defined once, in `acp/cli.py` (`DEFAULT_SPEND_CAP_USD = 5.0`). `Spend` is the ledger's own per-session account (spent, reserved, calls, refused), `spend()` returns a copy, and the cap is `SpendLedger.cap_usd`. The refusal's body is built in `KeyProxy._refuse` [read] | `layout.py:53-88`; `acp/cli.py:16`; `proxy.py:109-180, 350-373` | `0f1d0e0`, `440e1ac` |

### 1.2 Stale lines in the design

Moved by collaborators, or by D5's own progress [read, except where marked]:
- **The header's "Expected", §1.2's skeleton and final split, §8.6, §9's rows W1, C1, C2 and D4, §11 items 1, 2, 13
  and 17:** all of it landed, and both parts are built and run (§5). The Canvas pin moved `dr-1` `fc87687`
  (`2f55b18`) → `dr-2` `9d050ab` (`5fc05eb`: C1, C2 and #27) → `dr-3` `4355a36` (`f32e152`: #28, #29). §4.2.1's
  placeholders are filled: Canvas `4355a36` tagged `dr-3`; the `.deb` maintainer is Michael's git identity (his
  ruling).
- **§8.4** cites C1 as Canvas PR #4 and C2 as PR #3. Both are closed unmerged; C1 merged as #13–#19 and C2 as
  #20–#26 [run: `gh api`, `git log`].
- **§11 item 10** (E12 dismisses onboarding's dialogs). `dr-3`'s #28 shows no consent dialog, no analytics switch, and
  records no consent in a build that cannot report (`isTelemetryAvailable()`: a PostHog key and no
  `VITE_DO_NOT_TRACK=1`). #29 makes onboarding's agent step offer the active profile first and chosen; keeping it
  writes nothing and skips the model setup. E12 goes through onboarding and pins both [CI].
- **Decision F** activates the profile once and never again. At `dr-2` onboarding preselected another agent on a
  first launch (`c538fb3`'s message), which setup would not undo; with #29 onboarding keeps `deep_reasoner`, and E12
  asserts that the profiles and `active_agent_profile_id` are the same after onboarding [CI].
- **Decision K's consequences** now include no consent prompt and no analytics switch (#28), besides no reports.
- **§7.4**'s "dispatched again on `v1-desktop` with `sdk_ref` `dr-2`": done, and again at each revision's head (§5).
- **§11 items 4, 5, 11, 12 and 15** were questions for the first runs; §5 answers them.
- *(r2)* **§4.2.4's wrapper listing, §4.3.2's exit codes, §5.1's `SetupState.load` docstring and §6's build
  sentences** no longer list everything the code has: §1.1 #19 and #20.
- *(r3)* **Decision C and §3 item 4, §4.2.2 check 7, §4.4.2's "parsed from `runtime.lock.txt`", §4.4.3's steps, §5.2's
  `RuntimeSpec`; §4.5.1 step 4; decision M's `nightly.yml` and §7.5's trigger list; §5.1's `state_dir`; §5.7's `Spend`
  and `DEFAULT_SPEND_CAP_USD`:** §1.1 #10 and #22–#25. Decision C's reason, that users run the set CI tested, holds
  through the commit's own `uv.lock` [run: §5.4].

### 1.3 Behaviour the design does not state

1. **Check 8 on a reused `--work`. Closed in r2; the mechanism is gone in r3.** At `3c923aa` the fork cache's refetch
   moved only `FETCH_HEAD`, so a local check with a kept `--work` could refuse a pin merged after the first clone
   [run at 3c923aa]. `24646d0` fixed the refetch [run at c9bb7fe]. `f28730d` removed the cache, and the test that
   pinned the fix with it: check 8 now asks GitHub (§1.1 #14), and `--work` keeps nothing it reads.
2. **The default suite needs the network.** `test_the_runtime_lock_installs_on_every_platform_the_app_ships_for`
   (Linux x86-64, macOS 14 arm64) now runs `uv export` of `uv.lock` and dry-runs the result against PyPI's metadata,
   and carries no marker [read; run].
3. **Two default-suite tests restate the committed pins:** `test_the_committed_sdk_pin_is_34c540c_tagged_dr_2` (and
   `uv_version`) and `test_the_committed_pins_load` (both forks). A pin bump edits them [read].
4. **A `setup.json` whose `v` is not 1. Closed in r2, and its residue in r3.** At `3c923aa` it was a traceback, exit
   1 [read at 3c923aa]. `930a0cf` made a version other than 1 exit 14 [run at c9bb7fe]; a file with no `v` was still
   called a newer app's, and one that was not JSON was still a traceback [run at c9bb7fe]. Since `8125fa1` each gets
   its own reason under exit 14 (§1.1 #20). Pinned by `test_setup_state_from_a_newer_app_is_explained_and_exits_14`,
   `test_a_setup_state_this_app_could_not_have_written_says_why` (seven files) and
   `test_a_setup_state_that_cannot_be_read_says_why` (a directory in its place) [run].
5. **Setup is silent while git waits on a credential dialog.** The macOS smoke's 15-minute hang (§5.3) was a keychain
   dialog under the test's fresh HOME; the fix (`269c7af`) is in the test, which gives that HOME an empty credential
   helper. The splash says nothing while setup waits (TASK-39) [read; CI].
6. *(r3)* **Checks 4 and 8 read GitHub, and no unit test covers those readers.** `check_pins` is tested with
   injected readers; `read_file_at` and `is_on_branch` run only in builds, the `pins` job and §5.4, where both forks'
   pins pass and three commits off the branch are refused [run]. An HTTP error other than check 8's 404 (a rate limit:
   GitHub allows 60 unauthenticated requests an hour) is not a sentence; it leaves `build.py` as a traceback [read].
7. *(r3)* **TASK-49's four failing golden tests come from Python's patch version, not the path.** D1's recordings
   `failing` and `unanswered`, both modes, embed a traceback with CPython 3.12.3's stdlib line numbers
   (`asyncio/runners.py`, line 194). On 3.12.3 they pass and on 3.12.15 they fail, from this worktree (34 bytes) and
   from a checkout under a 151-byte path alike [run, §5.4]. CI runs 3.12.3.

### 1.4 Where the design holds

Decisions A to P hold as written, apart from §1.1 [read; the runs of §5 exercise each]: pins by full commit with tags
beside them; an `sh` bootstrap around `uvx` of the standard-library-only `deep-reasoning-app` fetched by commit with
`#subdirectory=`; a runtime venv holding exactly the locked set (now by `uv sync` of the commit's tree, #22), swapped
in by the `runtime/current` link; one root `~/.deep-reasoning`, DR_HOME the root or `/var/tmp/deep-reasoning-<uid>`,
passed only as `--home`; an idempotent cheap path; the profile's four owned fields and the `--home` pair, activated
once; the Library App staged from three of D3's files and a generated one-script artifact, approved and started on
every launch; the key proxy on its own thread in `dr-acp`'s front, on by default; telemetry off at build time; the
wrapper electron-builder config; the ingress left to C3; texts as functions; `run_logged`. Every sentence in §6's two
tables is the code's, verbatim [run: each compared with the code]; the bootstrap's and the new ones are §1.1 #7, #15,
#19 and #20. The wrapper config is §4.2.4's but for its `mac` key, and the bootstrap §4.3.1's but for its fetch line
[run: `diff`]. Of the tests the design's §7 names, five carry other names or are gone: two of the bootstrap's (#7),
the first-install and reinstall tests (renamed for #22), and `test_the_runtime_lock_matches_uv_lock` (no lock) [run].

---

## 2 · What exists

| Part | Files | Lines |
|---|---|---|
| The build | `desktop/build.py`, `pins.toml`, `bootstrap.sh`, `electron-builder.dr.mjs` | 592 |
| Setup | `packages/dr-app/` (`cli`, `layout`, `runtime`, `agent_server`, `profile`, `canvas_app`, `texts`) | 1,301 |
| The key proxy | `src/deep_reasoning/acp/proxy.py`, with `dr-acp`'s two options and the tool-client seam in D1's files | 681 + 128 net |
| CI | `cross-repo.yml`, `desktop-release.yml` | 339 |
| Tests | `tests/app/`, `tests/desktop/` (E12, the smoke, the README), `tests/crossrepo/`, `tests/acp/test_key_proxy.py`, `test_e10_keys.py` | 4,423 + 114 net |
| The README | `README.md`: what deep-reasoning is, the install section, §2.2 in short | 208 |

A build and a launch, as the code runs them [read; CI]:

```text
uv run desktop/build.py linux | mac-arm64            (on that machine only)
  pins.toml ─ check_pins: 7 checks, the forks read by git and GitHub's API ─ Canvas fork 4355a36 under --work
  defaults.json += paths.stateDir, setup.command (sh -c bootstrap … <commit>), setup.phases, telemetry key ""
  npm ci · VITE_DO_NOT_TRACK=1 npm run build:app · uv 0.12.23 and Node downloaded · electron-builder --config wrapper
  verify: the expected artifacts, no "deep_reasoner" in a payload path, arm64-only Mach-O, macOS 14 minimum ─ dist/

the app's launcher (C3), every launch
  before-start  sh bootstrap.sh → uvx dr-app@<commit> setup → data home · runtime (for a new commit) · bin/ links
                the runtime: fetch the commit's tree → uv sync its uv.lock into a new venv → swap runtime/current
  agent-server  SDK fork 34c540c on 127.0.0.1:18000
  after-ready   the same command → profile deep_reasoner · model-key hint · Library App staged, installed, ready
  a conversation → ~/.deep-reasoning/runtime/current/bin/dr-acp --home <DR_HOME> --spend-cap-usd 5
                    front: KeyProxy on 127.0.0.1:<port> ── real key ──▶ provider;  worker: tokens only
```

### 2.1 The build: `desktop/`

`build.py` is standard library only and reads in order: constants and pins, the build's sentences, `check_pins`, the
defaults it writes, the forks' readers, the build, then `verify()`. `check_pins` takes its readers as arguments
(`ls_remote`, `read_sdk_file`, `is_on_branch`), so the tests run every check without a network; the build passes
`git ls-remote`, a `raw.githubusercontent.com` read and GitHub's compare API. Of the fork's files it changes only
`config/defaults.json`, in a detached checkout under `--work`, and it commits to neither fork. The setup command it
embeds is

```text
["sh", "-c", <bootstrap.sh>, "dr-app-bootstrap",
 "git+https://github.com/michaeltheologitis/deep-reasoning@<HEAD>#subdirectory=packages/dr-app",
 "https://github.com/michaeltheologitis/deep-reasoning", <HEAD>]
```

with the repository URL a constant (`DEEP_REASONING`) and the commit the checkout's `HEAD`. `pins.toml` holds the two
forks' repositories, commits and tags and the `[app]` values; deep_reasoner's pin is a line of deep-reasoning's own
`pyproject.toml` and `uv.lock` [read].

### 2.2 Setup: `dr-app`

`cli.main` dispatches `setup`, `export` and `home`; `setup` holds `setup.lock` (`fcntl.flock`) for its whole run. The
modules: `layout` (paths, the data home, `setup.json`, `SetupError` and the exit codes), `runtime` (top-down: whether
the runtime is current, the checks, deep_reasoner's pin, the fetched tree, the install, `run_logged`), `agent_server`
(a `urllib` client with no proxy handler), `profile`, `canvas_app` and `texts`. Their seams carry plain values: the
commit and repository into `fetched_source`, which yields the tree's path; a `Pin` (URL, commit) out of
`deep_reasoner_pin`; a `RuntimeRecord` out of `install_runtime`; `SetupState`'s records into `setup.json`; the
agent-server's JSON in and out. `dr_app` imports nothing of deep-reasoning's, since `uvx` runs it before deep-reasoning
is installed; D2's `NETWORK_FILESYSTEMS` and D3's `APP_NAME` are mirrored, and tests pin that they are equal [read].
§4.2 says where its complexity sits.

### 2.3 The key proxy, and D1's seam

D1's files gain a tool-client half of the route seam, additive, as §8.1 designed it [read; run: D1's suite]:
`RunSource.tool_clients` (filled by `ConfigCatalog.materialize` for every tool block with its own `client`),
`ModelRoute.grant(…, tool_upstreams=…)`, `RouteGrant.tool_client_overrides`, `Start.tool_client_overrides`, and the
worker's `run_config(start)`, which merges each over its tool's client. `DirectRoute` accepts and ignores it.
`dr-acp`'s `main()` builds `SpendLedger`, `KeyProxy` and `ProxyRoute(proxy, os.environ)` unless `--no-key-proxy`, and
stops the proxy with a 0.5 s budget when `serve()` returns; the default cap is `acp/cli.py`'s. `proxy.py` holds the
rest, in three parts: the ledger, the HTTP side (Starlette under uvicorn on a daemon thread, a socket bound to
`127.0.0.1:0` first) and the grant. §4.1 walks a request.

### 2.4 CI

| Workflow | Trigger | Jobs |
|---|---|---|
| `cross-repo.yml` | pull requests touching the app, `workflow_dispatch`, `17 6 * * *` (from the default branch only) | `pins` (`build.py check`, with `GITHUB_TOKEN`); `desktop-e2e` (Linux build, `.deb` installed, E12 under `xvfb-run`); `bridge-replay` (E5, D4's forwarding test and the staged App against the SDK fork's agent-server); `canvas-replay` (E6, C1's replay spec in the Canvas fork's mock-LLM stack) |
| `desktop-release.yml` | a `v*` tag, `workflow_dispatch` | `cross-repo-green` (tags only: a successful `cross-repo.yml` run on the commit); `linux`; `macos` (`mac-arm64`, then the launch smoke on the `.app` from the `.dmg`); `release` (tags only: create the release, upload with `--clobber`) |
| `nightly.yml` (`main` only; `v1-desktop` deletes it) | `17 6 * * *` | `gh workflow run cross-repo.yml --ref v1-desktop` |
| `fork-live.yml` (on `main` since `633a00d`, before this branch) | `workflow_dispatch` | S1's and S2's live files against `dr-acp` from the dispatched ref |

Every job that installs deep_reasoner reads deep_reasoner_beta through `DEEP_REASONER_TOKEN` in an `insteadOf` line;
no job calls a model but `fork-live.yml` [read].

### 2.5 Which tests carry what

- **The build:** `tests/desktop/test_build.py`, 20 tests: each check's refusal, the defaults, the setup command, a
  `.deb` listing with spaces, the arm64 and macOS-minimum checks, the per-machine targets, the committed pins.
  `tests/desktop/test_readme.py`, 8 tests: the README's names against the code's.
- **Setup:** `tests/app/`, 60 tests, against stub `uv`, `uvx` and `git` scripts (the stub `git` lays a copy of this
  repository's `uv.lock` into the "fetched" tree) and `fake_agent_server.py`, an in-test HTTP server answering like
  the agent-server; one `crossrepo` test against the SDK fork's real agent-server.
- **The proxy:** `tests/acp/test_key_proxy.py` (in process, `httpx.ASGITransport`), E10 in `test_e10_keys.py` (a real
  `dr-acp` over stdio), and D1's tests for the seam.
- **Across repositories:** `tests/crossrepo/` (E5's replay, D4's forwarding), `tests/desktop/test_e12.py` (E12 on the
  installed app), `test_launch_smoke.py`, and `tests/desktop/test_app.py` for the launch harness itself. The harnesses
  call the agent-server through `dr_app.agent_server.AgentServer`, and tests import `desktop.build` as a module.

---

## 3 · The public surface, from the code

```text
uv run desktop/build.py {linux|mac-arm64|check} [--work DIR]          default --work: <repo>/.desktop-work
dr-app setup [--phase before-start|after-ready] --repo URL --commit SHA
dr-app export DIR [--namespace NAME]                                   runtime's dr-library export … --home DR_HOME
dr-app home [DIR]
dr-acp … [--spend-cap-usd USD] [--no-key-proxy]                        default 5.0; the proxy is on
```

- **Exit codes** [read: `layout.py:18-23`]: `dr-app` 0; 10 a check before the install failed, nothing installed; 11 a
  step of the install failed, `runtime/current` unchanged; 12 the agent-server refused what setup needs; 13 the data
  home is unusable or too long, or nothing is installed for `export`; 14 `setup.json` is unusable; 2 usage, or
  after-ready without `AGENT_SERVER_URL` and `SESSION_API_KEY`. The bootstrap exits 10 without git and otherwise
  passes `uvx`'s status on.
- **On disk** [read; CI: E12]: `~/.deep-reasoning/` (0700) holds `canvas/` (the agent-server's root; C3's state
  directory `canvas/agent-canvas/`), `runtime/<commit>/` and the `runtime/current` link (and, while an install runs,
  `runtime/<commit>.tmp-<pid>` and its `-source` tree), `bin/dr-app` and `bin/dr`, `canvas-app/<digest>/`,
  `setup.json`, `setup.lock`, and, as DR_HOME on a local home, D1's and D2's files and `spend/<session>.json`.
- **What `defaults.json` gains** [read; run: `test_defaults_gain_only_d5s_four_keys`]: `paths.stateDir`
  `~/.deep-reasoning/canvas/agent-canvas`, `setup.command`, `setup.phases` (both), `telemetry.posthogApiKey` `""`.
- **The agent profile setup writes** [read; CI]: `deep_reasoner`, `agent_kind` `acp`, `acp_server` `custom`,
  `acp_command` the shell-quoted `runtime/current/bin/dr-acp`, `acp_subagents` true, `acp_args` `["--home", DR_HOME,
  "--spend-cap-usd", "5"]`, `secret_refs` and `mcp_server_refs` null.
- **The Library App's manifest** [read]: D3's `canvas-extension.json` plus a `backend` block naming one artifact,
  `backend/dr-library.tar.gz`, for `<os>-amd64` and `<os>-arm64`; argv `{artifact_dir}/bin/dr-library serve --port
  {port} --home <DR_HOME>`; the agent-server's six inherited variables.
- **The key proxy's HTTP** [read; run: `test_key_proxy.py`]: `POST /r/<route id>/<path>` on `127.0.0.1:<port>`.
  Paths: `chat/completions`, `completions`, `embeddings` (openai); `v1/messages`, and unmetered
  `v1/messages/count_tokens` (anthropic). Refusals in the dialect's error shape: 401 `bad_token`, 403
  `not_a_model_call`, 400 `bad_body`, 400 `unpriced`, 402 `cap_reached`, 502 `upstream_unreachable`.
- **Python** [read]: `deep_reasoning.acp.proxy`: `SpendLedger(home, cap_usd)` with `reserve`, `settle`, `spend` (a copy
  of the session's `Spend`) and `cap_usd`; `KeyProxy(ledger=, prices=, home=)` with `ensure_started`, `stop`,
  `base_url`, `add_route`, `drop_run`, `app`; `ProxyRoute(proxy, env)` with `grant` and `release`;
  `loopback_proxy_env`; `is_loopback`. D1's additions are named in §2.3. `dr_app.runtime`: `runtime_is_current(layout,
  record, commit)`, `check_git()`, `check_readable(url)`, `deep_reasoner_pin(tree) -> Pin`, `fetched_source(layout,
  repo, commit, log=)`, `install_runtime(layout, source, commit, uv=, log=) -> RuntimeRecord`, `run_logged`,
  `git_environment`.

---

## 4 · Where the complexity sits

After the refactor, as before it, two places hold most of it: the key proxy, and setup's before-start. The refactor
moved the second: the runtime now comes from a fetched tree, so before-start owns a temporary checkout as well as a
temporary venv.

### 4.1 The proxy: a grant, then a request

**A grant** (`ProxyRoute.grant`, `proxy.py:603-678`) [read; run: `test_key_proxy.py`, E10]. For the main client and
each tool's own client, the key's name is `api_key_env`, else `NOVITA_API_KEY`, falling back to `OPENAI_API_KEY` as
deep_reasoner's `build_client` does; a client whose key `dr-acp` lacks is left as configured. If nothing is held and
there is no `ANTHROPIC_API_KEY`, the grant is empty and the proxy never starts. Otherwise: one 256-bit token per key
name, one route per (upstream, key name), the overrides `{base_url: <route url>, api_key_env: <name>}`, and for a
held Anthropic key a route of its own exported as `ANTHROPIC_API_KEY` and `ANTHROPIC_BASE_URL`. The worker's
environment loses every variable whose value contains a held key, or a value of at least 16 characters held by a
variable D1's `ALWAYS_REMOVED` patterns name; then each key's own name comes back holding its token. `NO_PROXY` gains
the loopback hosts; on macOS, with no proxy in the environment, the system's HTTP and HTTPS proxies are exported too.

**A request** (`KeyProxy._handle` → `_metered` → `_forward`, `proxy.py:375-553`) [read; run: `test_key_proxy.py`]:
the token (`Authorization: Bearer`, else `x-api-key`) must hash to the route's, or 401 and nothing is forwarded; the
method must be POST and the path one of the dialect's, or 403; the body a JSON object of at most 32 MiB, or 400. A
model the price table cannot price is refused 400 unless the upstream is loopback. An openai stream gets
`stream_options.include_usage`. The reservation is the table's price for `ceil(len(body) / 4)` input tokens and
`max_completion_tokens`, `max_tokens` or 4,096 output (0 for embeddings); `SpendLedger.reserve` refuses with 402 when
spent, reserved and this estimate pass the cap. The call goes upstream with the real key and with `trust_env` off for
a loopback upstream. A successful event stream is relayed as it arrives and metered from it; anything else is read
whole, with the key replaced by `[redacted]` in a non-2xx body. Settlement is §1.1 #5. The ledger's file,
`<home>/spend/<session>.json`, is rewritten after each settle and each refusal and read at a session's first use, so
a restarted `dr-acp` continues the count. One `threading.Lock` guards the ledger, one the routes. Every refusal goes
through `_refuse`, which logs it without a key or a token and answers in the dialect's error shape.

### 4.2 Setup: the cheap path, and everything that is not

**before-start** (`cli.before_start` and `cli.install`, `cli.py:73-132`) [read; run: `tests/app/`, §5.4; CI: E12]:
choose the home (§1.1 #4 included) and say it when it changes; if `runtime_is_current` (the record's commit, the
`runtime/current` link resolving to the record's path, and one exec of its Python), skip to the links. Otherwise
`install`: git's version and `uv` on `PATH`; then, inside `fetched_source` (`runtime.py:116-137`), the commit's tree
under `runtime/`, from which `deep_reasoner_pin` reads deep_reasoner's URL for the readability check (`git ls-remote`,
output discarded); the `checks_ok`, safety (first install) and `installing` lines; `install_runtime`
(`runtime.py:140-188`): `uv venv --relocatable`, `uv sync` of the tree into it, the import check of `dr-acp`'s,
`dr-library`'s and deep_reasoner's entry modules, rename, swap the link, remove every other runtime. The tree is
removed when `fetched_source` exits, success or not, and anything an interrupted install left (`*.tmp-*`) is removed
before the next one starts. Every subprocess goes through `run_logged` (`runtime.py:208-245`): one pipe for stdout and
stderr, each line logged as it comes, and a return at the process's exit plus at most 1 s of draining, so a
grandchild that keeps the pipe cannot hold the launcher's phase.

**after-ready** (`cli.after_ready`, `cli.py:143-166`) [read; CI]: the profile (§3; a write only when an owned field or
the arguments differ, the id from its own GET; activated only when `setup.json` has no record of setup activating it,
so a profile the user deleted is recreated but not made the default again); the model-key hint; then the Library App
(`canvas_app.py:101-172`): find D3's files through the runtime's Python, build the artifact (a gzip, `mtime` 0, of a
one-member USTAR tar holding a `/bin/sh` script that `exec`s `runtime/current/bin/dr-library`), digest the manifest
and files, stage them under `canvas-app/<digest>/`, then install (forced, after a `stop`, when the digest changed),
enable once, `prepare` when the prepared revision is not the current one, and `start` unless ready. Every refusal there
is a warning and setup still exits 0.

### 4.3 E12: one launch, seventeen ordered tests

E12 (`tests/desktop/test_e12.py`) is where most of D5's test lines are. Its module fixtures launch the installed app
once with a fresh HOME under `/tmp` (short enough for §1.1 #4), the runner's git config with an empty credential
helper, and a DevTools port; Playwright attaches over CDP; `FakeOpenAI` runs in the test process with a scripted plan
per question. The tests run in file order and depend on it: the Library imported by the onboarding test serves every
later conversation. Two waits are deliberate: Stop's grandchild model call waits on an event set once the run log
shows `stop.accepted`, and the header-panel test waits out the bridge's five-minute session plus 20 s [read].
`tests/desktop/app.py` holds the launch harness (fresh HOME, the user's environment without the runner's uv and venv
variables, a log tail on a failed wait) and `e12/subagents.py` the Python copies of C1's two DOM reads.

---

## 5 · Experiments and measured results

No run here called a model. The live tier's model calls are the Implementer's run, attributed.

### 5.1 The runs at `3e9cee9`

All on attempt 1.

| Workflow | Run | Result [CI] |
|---|---|---|
| `ci.yml` (push) | [37256037218](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37256037218) | `test`: ruff over `src tests packages desktop` clean; 858 passed, 115 deselected in 622 s. `canvas-app`: green |
| `cross-repo.yml` (dispatch) | [37256036928](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37256036928) | `pins`, `desktop-e2e`, `bridge-replay`, `canvas-replay`: all green |
| `desktop-release.yml` (dispatch) | [37256038987](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37256038987) | `linux`, `macos` green, `verify()` and its `Info.plist` check included; `cross-repo-green` and `release` skipped (no tag) |
| `fork-live.yml` (dispatch, `sdk_ref` `dr-2`) | [37256842683](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37256842683) | S1 2 of 2, S2 8 of 8, on gpt-6-luna |

### 5.2 Each experiment

**pins** [CI]: "the pins belong together ✓" (all seven checks, real forks, through GitHub's API with the job's token).
The same check passes here [run, §5.4].

**E10, keys and the cap** (`tests/acp/test_e10_keys.py`, default suite, Linux only; reproduce: `uv run pytest
tests/acp/test_e10_keys.py`) [run; CI]. Four tests through a real `dr-acp` and `FakeOpenAI`:
- **#1:** `OPENAI_API_KEY`, a copy under `MY_KEY_COPY`, `ANTHROPIC_API_KEY` and four agent-server secrets in
  `dr-acp`'s environment; a cell prints `os.environ`, `/proc/self/environ` and `env`'s output. None of the secret
  values, nor their base64, is in the worker's `/proc/<pid>/environ`, the cell's output, the client's updates, or any
  file under the home (run log, `worker.log`, `dr-acp`'s stderr log). The worker's `OPENAI_API_KEY` is a token of at
  least 40 characters, which the cell did print. Every call the fake received, the main client's and the `rag`
  tool's embeddings, carried `Bearer <real key>`.
- **#2:** cap $0.01, $0.004 a call. All three prompts (the first, a second, one after `dr-acp` restarted and reloaded
  the session) end `failed` with the proxy's sentence; the fake saw exactly the calls the ledger counted and none
  after the first refusal; `spent_usd` ≤ $0.014; `refused` ≥ 3.
- **With D4's MCP server, ×2:** the server gets the model key only when its Canvas settings name it; its environment
  is its settings plus `mcp`'s six and `LC_CTYPE`; the worker's token and the agent-server's secrets never reach it.

**E12, the installed Linux app** (`desktop-e2e`, `ubuntu-24.04`; reproduce: the job's steps) [CI]: the build took 4 min
2 s (`.deb` 150 MB); **17 passed in 416.1 s**. The first launch, from a cold uv cache under a fresh HOME through both
setup phases to the window, now including the fetch of the commit's tree and `uv sync`, passed 32.3 s after
collection. The header-panel test, which waits past the bridge's first session, took 320.5 s, most of E12's time.
Proven inside the real app: the worker's environment holds neither the key nor the session or secret key, and no
stored file does; D3's frame works through the bridge with a partitioned `Secure; SameSite=None` cookie whose
partition is `http://localhost`, and is refused 401 after the session is deleted; C1's tree equals the run log's (3
sub-agents, 1 nested), costs match, and Stop stops a child and its branch while its done sibling stays done; C2's
picker, slash menu, header panel and Create decomposition; D4's MCP server is bound and called; the app quits within
6 s; setup relaunches with the network cut in under 5 s and installs nothing.

**E5's second half, `bridge-replay`** (`tests/app/test_canvas_app.py` and `tests/crossrepo/`, SDK fork `34c540c`;
reproduce: `DR_SDK_CHECKOUT=<checkout> uv run pytest -m crossrepo tests/app/test_canvas_app.py tests/crossrepo`) [CI]:
**12 passed in 53.1 s**: each of D1's ten native recordings is stored by the agent-server as the tree it records,
D4's forwarding test passes, and the staged App passes `prepare` and its backend answers `/health`.

**E6, `canvas-replay`** (C1's replay spec at Canvas `4355a36`) [CI]: **10 of 10** on attempt 1. TASK-40's race did not
show at `c9bb7fe` or `3e9cee9`; at `3c923aa` it failed attempt 1 (§5.3).

**The launch smoke** (`macos`, `macos-26-arm64` runner image) [CI]: the `.dmg` built in 2 min 39 s, its `.app` passing
`verify()`'s architecture and `Info.plist` checks; **2 passed in 56.7 s**: the backend ready after the first launch,
the app quit with 0, and the launched executable and its uv are arm64 only. The job's app log
(`desktop-macos-launch`) times the first launch on a Mac: before-start `installed in 12s` and `Done in 17s`, its
`readable ✓` line a second after the fetch began; 26 s for the agent-server's own install and start; after-ready
`backend ready` 2 s in and `Done in 2s`. Setup's two phases, and the agent-server between them, spanned 45 s.
Artifacts as uploaded (zip): macOS 178,485,675 B, Linux 345,946,154 B.

**The live tier** (`fork-live.yml`, `dr-acp` from `3e9cee9` with the key proxy on, as no flag turns it off) [CI]:
S1's `test_live_agent_tree_is_well_formed` and `test_live_agent_stops_one_subagent_and_its_branch`, 2 passed in
38.8 s; S2's file, 8 passed in 98.8 s. The model was gpt-6-luna; I did not re-run it.

### 5.3 Earlier runs, for history [CI]

- **At `c9bb7fe`, r2's evidence:** `ci` 37246565304, 845 passed. `cross-repo` 37246570008, all six jobs green on
  attempt 1; E12 17 passed in 419.7 s; `bridge-replay` 11 and `library-app` 1. `desktop-release` 37246572498: the
  smoke 2 passed in 83.5 s; `installed in 16s`, `Done in 21s`, 40 s for the agent-server, after-ready `Done in 4s`,
  65 s across both phases. `fork-live` 37247433818: S1 2 of 2, S2 8 of 8.
- **At `e5c8be2`**, the first proof of §1.1 #2's fix: `desktop-release` 37245365250, `linux` and `macos` green with
  the `Info.plist` check; the smoke 2 passed in 55.6 s, `installed in 14s`.
- **At `3c923aa`, r1's evidence:** `ci` 37240441891, 833 passed. `cross-repo` 37240441432, all six green on attempt 2;
  attempt 1 failed only `canvas-replay`, on `fanout20.native.jsonl`, whose rows `n16` and `n17` were read before their
  tool calls rendered (five passed, four skipped after it; TASK-40). E12 there: 17 passed in 428.7 s.
  `desktop-release` 37240443237: the smoke 2 passed in 54.2 s, `installed in 15s`, 42 s across both phases.
  `fork-live` 37241495293: S1 2 of 2, S2 8 of 8.
- `desktop-release` 37226929314 (`9ca1f70`): `macos` red. The launch smoke waited its limit on a keychain dialog
  under the fresh HOME (§1.3 #5); fixed in the test by `269c7af`, and failures made readable by `ae363b4`.
- `cross-repo` 37230954884 (`d39be70`), 37236303764 (`8ce99b2`), 37238261156 (`a4a9336`): all six jobs green.
- `desktop-release` 37231871112 (`d39be70`): green, with the universal `.dmg` of that time.
- `desktop-release` 37238259690 (`a4a9336`): `macos-intel` red, the job since dropped (§1.1 #1).

### 5.4 Run here

**At `3e9cee9`** [run]:
- **The default suite**, from this worktree (`/home/user/worktrees/dr-asbuilt-d5`), on CPython 3.12.3 as CI runs it
  and without `DR_BETA_CHECKOUT`: **725 passed**, 5 skipped, 115 deselected, in 8 min 7 s. D5's own files and the D1
  and D3 files it edits: 189 passed, 1 skipped (D1's catalog test that needs `DR_BETA_CHECKOUT`). The total is below
  CI's 858 by the D2 corpus tests that `DR_BETA_CHECKOUT` parametrizes.
- **The golden tests and TASK-49** (§1.3 #7): the four run on 3.12.3 pass and on 3.12.15 fail, both from this
  worktree and from a second checkout of `3e9cee9` under a 151-byte path (removed).
- **`build.py check`**: "the pins belong together ✓", 4.4 s, the forks read through GitHub's API. Check 8's reader
  directly: `True` for both pins, `False` for the Canvas fork's `9881d24` (`wiring/dr-1`), the SDK fork's `cef3b24`
  (its `dr-1`, on `dr/integration`) and a commit that does not exist; check 4's reader returns the SDK fork's
  `uv.lock` at `34c540c`.
- **A real first install with the bundled uv 0.12.23** (a probe that runs `dr-app setup --phase before-start` with
  the socket limit patched out for a scratch HOME; removed): `installed in 7s` from a cold uv cache, the managed
  CPython download included, 8.9 s in all. 173 packages, the same names and versions as `3c923aa`'s install; only
  deep-reasoning's and deep-reasoning-app's recorded sources differ. The runtime is 474 MB, the whole HOME 606 MB; the
  entry points start `#!/bin/sh`. A relaunch's before-start took 0.019–0.024 s.
- **Setup's three failure cases, `3c923aa`'s `dr-app` against `3e9cee9`'s** (the same probe, each a fresh scratch
  HOME): the outputs §6 #11 quotes. Offline was `unshare --map-root-user -n`; "deep-reasoning unreachable" was a
  repository URL that does not exist; "deep_reasoner unreadable" was a `GIT_CONFIG_*` rewrite of its URL to one that
  does not exist.
- **`dr-app home` against six `setup.json` files:** `{"v": 2}` gives `state_from_a_newer_app`; `{"x": 1}`, `{`,
  `[1]`, `{"v": "1"}` and a `runtime` record without its fields give `state_unusable` with "it has no version", "it
  is not JSON", "it is not a JSON object", "its version is \"1\"" and "it holds a record this app does not write";
  each exits 14. "It cannot be read" I did not probe (as root every file is readable); its test puts a directory in
  the file's place [run].
- **§6's sentences:** each of both tables compared with the code, all equal.

**At `c9bb7fe`, r2's probes** [run at c9bb7fe]: `build.py check` twice on one `--work` through the fixed refetch;
`dr-app home` against three `setup.json` files (§1.3 #4's residue, since closed).

**At `3c923aa`, r1's probes** [run at 3c923aa]: the bootstrap exactly as the launcher runs it, under a scratch HOME,
refused the home with exit 13 (`home_too_long`, "up to 146 bytes long, and this system allows 107"), passed through
without its fetch line, in 3.3 s cold and 0.12 s warm, also with no network; a first install by `uv pip sync` of the
packaged lock, `installed in 11s`, 473 MB; a wheels-only dry run of the lock for `aarch64-apple-darwin`, failing on
onnxruntime for macOS 13.0 and passing for 14.0.

### 5.5 What the design's §11 asked to be measured

- **Item 5, `uvx`'s start for `dr-app` on a relaunch:** 0.12 s warm, with or without a network, for `sh`, `uvx` and
  `dr-app` up to its home check [run at 3c923aa; the bootstrap and `uvx` are unchanged]; the cheap path after it,
  0.02 s [run]. E12 asserts the whole offline relaunch of before-start finishes in under 5 s [CI].
- **Item 5, the first install's time and disk use:** 7 s here and 474 MB of runtime (606 MB with uv's cache and
  Python) [run]; 12–16 s on GitHub's macOS runner across four release runs, and E12's whole first launch under 33 s
  on its Linux runner [CI]. The design's mock-up figure of two minutes was not reached; a user's network sets it.
- **Item 5, the after-ready cost of starting the backend:** after-ready took 2–4 s on the macOS runner, the App's
  `backend ready` 2–3 s after the phase began, the profile written within a second of it [CI: four launch logs].
  Between the phases, the agent-server's own install and start took 21–40 s.
- **Item 4, macOS on hardware:** the launch smoke ran on GitHub's `macos-26-arm64` image; nothing ran on macOS 14.
  The system-proxy handling (§4.7.2 step 5) has unit tests only.
- **Item 11, the cookie in Electron's Chromium:** holds (E12, §5.2). **Item 12, the `.mjs` wrapper config:** builds
  on both platforms. **Item 15, uv 0.12.23 for D5's own commands:** E12 and the smoke run them with the bundled uv
  0.12.23, and so did §5.4.

---

## 6 · Open items for Gate B and Gate C

r1's numbers kept; the closed ones struck through.

1. ~~**The macOS minimum is not enforced.**~~ Closed by `e5c8be2` (§1.1 #2).
2. ~~**There is no README.**~~ Closed by `c9bb7fe` (§1.1 #9); where it differs from the design is §1.1 #18.
3. **TASK-39:** the splash says nothing while setup waits (on a credential prompt, or a slow first install). The README
   tells the user to quit and run setup's access check in a terminal when setup stops moving.
4. **TASK-38:** E12's Stop saw a sibling spawned in the same `run_all` still running when Stop was pressed; whether
   that is the fake holding a call or real serialisation in D1 is open. E12 spawns the done sibling first.
5. **TASK-40:** C1's replay spec reads the DOM once and failed about one run in five; the fix is in the Canvas fork.
   It passed on attempt 1 at `c9bb7fe` and `3e9cee9`.
6. ~~**Check 8 on a reused `--work`.**~~ Closed by `24646d0`; the cache itself went in `f28730d` (§1.3 #1).
7. **`main`'s workflow copies are behind `v1-desktop`'s** (§1.1 #11), with `main`'s `nightly.yml`. Nothing runs them
   while `main` lacks `desktop/pins.toml`; D5's PR stack replaces them.
8. ~~*(r2)* **What the README says that is not exact.**~~ Closed by `3919e92` (§1.1 #18). There is still no `v*` tag,
   so an install comes from a hand-run build's artifacts, as the README now says.
9. ~~*(r2)* **Two `setup.json` cases outside exit 14.**~~ Closed by `8125fa1` (§1.1 #20).
10. *(r2)* **Gate B's install is the `3c923aa` build.** It differs from `3e9cee9`'s in everything since: its `.app` was
    built without the `minimumSystemVersion` key; its setup installs the runtime by `uv pip sync` of the packaged lock;
    a bad `setup.json` is a traceback there; and its error paths are §6 #11's "before" column. On macOS 26, with the
    network and deep_reasoner_beta readable, none of this changes what an install shows [read].
11. *(r3)* **For Gate C: two error paths of setup changed with the refactor (§1.1 #23).** This moves approved
    behaviour; Michael has not seen it. What each case shows now, beside what it showed at `3c923aa` [run: §5.4]:
    - **Offline, when `uvx` already has this `dr-app` and the runtime is not current** (an interrupted first launch,
      a deleted runtime). Before: exit 10, "✗ Could not read github.com/DeanLight/deep_reasoner_beta with your git
      credentials. It is private: ask Dean for read access, then sign git in … Nothing was installed." Now: exit 11,
      git's own "fatal: unable to access 'https://github.com/michaeltheologitis/deep-reasoning/': … Couldn't connect
      to server", then "✗ Installing deep-reasoning 3e9cee9 failed (git fetch exited 128); its output is above.
      After an update this needs the network once: connect and restart." A first launch offline with nothing cached
      is unchanged: `uvx` cannot fetch `dr-app`, and the bootstrap says to check the network [read].
    - **deep-reasoning unreachable** (a repository git cannot read). Before: exit 11 naming `uv pip sync`, after the
      `checks_ok` and safety lines had printed. Now: exit 11 naming `git fetch`, before any check line.
    - **deep_reasoner unreadable** (no access to deep_reasoner_beta). Before and now: exit 10, `no_access_dr`. Now it
      comes after a silent fetch of deep-reasoning's tree, which is removed; nothing is installed.
12. *(r3)* **For the PR split: the workflows without `has-d5`** (§1.1 #10, #11). A pull request whose merged tree holds
    the new `cross-repo.yml` and touches its paths, but has no `desktop/pins.toml`, fails its jobs; `cross-repo.yml`'s
    schedule takes effect only once it is on `main`, and `main`'s `nightly.yml` keeps dispatching `v1-desktop` until
    the stack deletes it [read].
13. *(r3)* **TASK-49's description** names a long path; the cause is CPython's patch version (§1.3 #7) [run].

## 7 · What I could not verify

- **Nothing ran on a Mac here.** Every macOS claim is [CI] (one runner image, macOS 26) or [read]: the arm64 and
  `Info.plist` checks (their CI passes are evidence), the Finder `PATH`, the system-proxy export, the quarantine flow,
  and the runtime's package set on macOS (§5.4 compared it on Linux only).
- **That macOS 13 refuses to open the app** [read]: `LSMinimumSystemVersion` is declared 14.0 and `verify()` checks it
  on the real `.app` [CI]; what macOS 13 then does is Apple's behaviour, not run.
- **The README's uninstall paths for Electron's folders** [read]: Canvas's `electron/main.mjs` sets no `userData`
  path, so Electron's default under the product name applies (`~/Library/Application Support/Deep Reasoning`,
  `~/.config/Deep Reasoning`); no run listed them.
- **A user's onboarding without a key** [read]: the **Say hello** step's **Close** button exists in Canvas `4355a36`
  (`say-hello-step.tsx`, `BUTTON$CLOSE`); E12 sends the hello with the key already saved, so pressing Close, and what
  a hello sent with no key does, never ran.
- **The failure cases through the bootstrap** (§6 #11): the probe ran `dr-app` directly; that the bootstrap passes 10
  and 11 through without its own line is [read] and its tests' [run].
- **A rate-limited GitHub API** (§1.3 #6): not run.
- **I did not install or launch the app.** E12, the smoke and the cross-repo jobs are [CI]: I read their logs and did
  not re-run them. E12's assertions are as §5.2 states them, read from the test and its passing log.
- **The live tier** made model calls; I read its log and did not re-run it. That `dr-acp` there ran with the proxy is
  [read]: `fork-live.yml` passes no `--no-key-proxy`, and the proxy is on by default.
- **The after-ready phase against a real agent-server** (the profile, the App's install, `prepare` and `start`) is
  [CI] (E12, `bridge-replay`, the smoke) and [run] only against `tests/app/fake_agent_server.py`.
- **TASK-38's cause**, and the Claude CLI behind the proxy (design §11 item 3): untested by D5's suite.
- **The design's §4.2.5** (strings that stay upstream's in the app): only seen in part. The macOS launch log prints
  upstream's "OpenHands Agent Canvas (Static)" banner [CI]; the rest is not checked.

---

## 8 · The literate refactor (`d9b35f4` to `3e9cee9`)

Ten commits after the two small fixes; the raw diff `8125fa1..3e9cee9` is 25 files, +550 −957 [run: `git diff
--shortstat`]. CI and the live tier are green at its head (§5.1).

**What it removed** [read; run: `git diff`]:
- **The exported lock and its machinery** (Scout finding 3, `d9b35f4`): `runtime.lock.txt` (176 lines), `RuntimeSpec`,
  `LOCK_RESOURCE`, `DEEP_REASONER_LINE`, `build.py`'s check 7 with `UV_EXPORT`, `RUNTIME_LOCK` and `lock_stale`, and
  the lock-digest comparison in `runtime_is_current`. The runtime syncs the commit's own `uv.lock` (§1.1 #22).
- **The fork clones** (finding 4, `f28730d`): `fork_cache`, `fork_has` and the bare, blobless clones under `--work`,
  with the class of bug r1 found in them (§1.3 #1). Checks 4 and 8 read GitHub (§1.1 #14).
- **The profile listing** (finding 5, `9002014`): one request fewer per launch (§1.1 #24).
- **`has-d5`, `library-app` and `nightly.yml`** (findings 1 and 2, `146bbbf`): the workflows match §7.5's four jobs
  (§1.1 #10).
- **Duplicates and leftovers** (`0f1d0e0`, `440e1ac`, `94683bd`, `6ee106c`, `9134faf`, `3e9cee9`): the exit codes
  scattered over five modules, now one table; `AppLayout.state_dir`; the second definition of the default cap; the
  frozen `Spend` copy and `_refusal`; two private HTTP clients in the test harnesses, which now use `dr-app`'s own;
  `importlib` loading of `build.py` in tests; `build.py` reordered to read top-down.

**What it did not remove** [read]:
- **The key proxy** (681 lines) keeps its three parts. Decision I's cap needs the ledger, the reservations and the
  dialects' metering; the refactor shortened it by 22 lines.
- **E12** (727 lines) and its five-minute wait, which the bridge's session length (the SDK fork's) sets.
- **`dr_app`'s mirrors** of D2's `NETWORK_FILESYSTEMS` and D3's `APP_NAME`: `dr_app` cannot import deep-reasoning,
  which is not installed when `uvx` runs it. The comments now say so.
- **`main`'s old workflow copies and `nightly.yml`**, which only D5's merge replaces (§6 #7, #12).

**The tests it changed** [read: `git diff 8125fa1 3e9cee9 -- tests`]. Each change follows a replaced mechanism, and I
found no behaviour assertion weakened:
- **Removed, with their mechanism:** `test_the_runtime_lock_matches_uv_lock` (no exported lock),
  `test_a_runtime_lock_that_is_not_uv_lock_is_refused` (no check 7),
  `test_check_8_on_a_reused_work_dir_sees_commits_merged_since_its_first_clone` (no cache), and the `lock` case of
  `test_a_new_commit_or_lock_reinstalls`, now `test_a_new_commit_reinstalls` (the commit fixes the lock).
- **Loosened by one condition:** `test_an_unreadable_deep_reasoner_installs_nothing` asserts `runtime/` is empty
  rather than absent, since the fetch creates it first.
- **Strengthened:** the failed-install test runs for `git fetch` and for `uv sync`; `test_git_never_prompts` covers
  every git and uv call; new tests pin that deep_reasoner's pin is read from `uv.lock` as `pyproject.toml` names it,
  and that no `.python-version` or `default-groups` can move `uv sync`'s set.
- **The gap:** the GitHub readers that replaced the fork clones have no unit test of their own (§1.3 #6).
