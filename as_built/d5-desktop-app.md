# D5 · Desktop app: build, install and launch, as built

**TASK-10** · Cartographer · revision 2 · 2026-10-05 · the code at `c9bb7fe` (head of `v1-desktop`; this file is on
`as-built/d5`, which merges it at `d8121e6`) · checked against design v2 (`docs/design/d5-desktop-app.md`, last changed
in `9ee36f6`, unchanged at `c9bb7fe`) · Canvas fork `dr-3` = `4355a36` and SDK fork `dr-2` = `34c540c`, read only.

**Since r1** (`81814f4`, the code at `3c923aa`), `v1-desktop` has gained four commits, each a fix r1's §6 proposed and
Michael approved ("yeah do the four u recommended!"): `24646d0` closes §1.3 #1, `930a0cf` §1.3 #4, `e5c8be2` §1.1 #2
and `c9bb7fe` §1.1 #9. `git diff 3c923aa c9bb7fe` touches nothing else [run]. This revision keeps r1's section and
finding numbers, which Gate B's reading may cite; what is new is numbered after r1's (§1.1 #18–#21, §6 #8–#10).

**What D5 is, in git.** `v1-desktop` was cut from `main` at `1f9fe52` and has merged `main` three times (D4 `53c821b`,
`b2a74e0`, `f1ca641`); `main` (`f1ca641`) is an ancestor of `c9bb7fe`, so `git diff f1ca641 c9bb7fe` is D5 and
nothing else [run]. That is 38 commits: the design's two (`8086afb`, `9ee36f6`) and 36 of code and tests. Two more
are on `main`, through #34 and #35: the workflow copies decision M asked for.

**Evidence marks.** Every claim carries one.
- **[run]**: executed on this machine at `c9bb7fe`: the default suite, `build.py check` twice on one `--work` against
  the real forks, `dr-app` against three broken `setup.json` files, `git` and GitHub's REST API.
- **[run at 3c923aa]**: r1's probes (§5.4), not repeated. What they ran is unchanged at `c9bb7fe`, but for check 8's
  refetch [run: `git diff`].
- **[CI]**: read from GitHub's logs of the runs in §5.1 and §5.3, and from the app logs the macOS jobs keep as
  artifacts. I dispatched no workflow and made no model call.
- **[read]**: read in the code and **not executed**. This is weaker evidence than [run]. §7 lists the read claims
  that matter most.

**Reading order:** §1, the divergences (start here); §2–§4, the map, the surface and where the complexity is; §5,
the measured results; §6, the open items for Gate B; §7, what I could not verify.

---

## 1 · Divergences from design v2

The design has not changed since `9ee36f6`, written before any code. The Changelog's one entry for TASK-10 (2026-10-04
20:47, the Canvas fixes) has an empty Drift line [read: Notion], so everything below was found in the code, its
history or the runs. Rows marked **Closed in r2** were r1's findings and are fixed; they keep their numbers.

### 1.1 Built otherwise than the design says

| # | Design says | Built | Where | Reason recorded |
|---|---|---|---|---|
| 1 | §1 item 1, §4.2.4 step 3, §5.8, §7.6: one universal `.dmg`; `build.py {linux\|mac\|mac-universal\|check}`; `ELECTRON_ARCH=universal` | **Apple silicon only.** Targets `linux` and `mac-arm64`; each refuses to run on any machine but Linux x86-64 or macOS arm64, because the fork packages uv and Node for the machine it builds on. `verify()` requires `deep-reasoning-<version>-arm64.dmg`, and `lipo -archs` = `arm64` for the `.app`'s Electron, uv and Node. `desktop-release.yml` has no Intel job; a tag's release needs `linux` and `macos`. [read; run: `test_build.py`; CI] | `desktop/build.py:51-72, 174-187, 418-470` | Michael, 2026-10-04: "lets drop the intel macs" (`bd6e170`). The Intel lock holds `2e883e7` and `a4a9336` are undone by `3500f87`: `uv.lock`, `runtime.lock.txt` and `pyproject.toml` equal `f32e152`'s [run: `git diff` is empty] |
| 2 | No macOS version is named | **macOS 14 or later, enforced. Closed in r2.** The runtime lock installs only from macOS 14: onnxruntime 1.30.0 (chromadb's, through deep_reasoner) ships `macosx_14_0_arm64` wheels and none older [run at 3c923aa, §5.4]. Since `e5c8be2` the wrapper config's `mac` block declares `minimumSystemVersion: "14.0"`, and `verify()` refuses a `.app` whose `Info.plist` declares any other `LSMinimumSystemVersion` (#19). Pinned by `test_a_mac_app_that_opens_before_macos_14_is_refused` (12.0, 13.0, absent) [run]; the real `.app` passed the check on GitHub's macOS runner [CI]. That macOS 13 then refuses to open the app is macOS's handling of that key, not run [read] | `desktop/electron-builder.dr.mjs:18-19`; `build.py:63-65, 465-469` | onnxruntime's wheels; the fix, Michael's approval of r1's §6 |
| 3 | §4.4.3: `uv venv --managed-python --python 3.12 runtime/<commit>.tmp-<pid>`, then rename | `uv venv --relocatable --managed-python …`. Without it uv writes entry points with an absolute shebang to the temporary path, and after the rename every runtime command was dead: `dr-library` exited 127 as the App backend [read; CI: E12] | `runtime.py:224-238` | `622976b`, found by E12's first launch |
| 4 | §4.4.1: three rules for the data home | **A fourth.** `choose_home` and `dr-app home DIR` refuse, exit 13 with `home_too_long`, a home under which `runs/<run id>/children/<n>/repl.sock` (the home plus 52 bytes) would pass the Unix-socket limit: 107 bytes on Linux, 103 on macOS. The default homes fit (on macOS, user names up to 28 characters); a HOME under macOS's `$TMPDIR` is refused [read; run: `deepest_socket`, §5.4] | `layout.py:23-28, 112-156` | `b1e3df2`: deep_reasoner's Claude backbone serves its REPL socket under the run directory |
| 5 | §4.7.3: "no usage reported: the reservation stands" | Usage reported, at any status: charged. No usage on a 2xx: the reservation is charged. **No usage on a non-2xx: 0**, the reservation released. Upstream unreachable: 0 [read; run: `test_provider_errors_release_their_reservations`, `test_a_call_costs_its_reported_usage_else_its_reservation_unless_refused`] | `proxy.py:527-541, 568-574` | Michael's ruling, 2026-10-04 (`f385025`): the OpenAI client's four retries of a 500 had left five reservations standing as spend |
| 6 | §4.7.3's request path | Two additions. A body that is not a JSON object, or is over 32 MiB, is refused 400 `bad_body`, a sentence §6 lacks. `Accept-Encoding` is not forwarded and `Content-Encoding` not returned, so bodies pass uncompressed [read] | `proxy.py:54-77, 408-428` | none recorded |
| 7 | §4.3.1, §6, decision B: the fetch-failure line says deep-reasoning "is private: ask Michael for read access…" | "✗ Could not fetch github.com/michaeltheologitis/deep-reasoning: check that this computer is online, then restart. Nothing was installed." [read; run: `test_bootstrap.py`] | `desktop/bootstrap.sh:14` | deep-reasoning is public (`3c923aa`) |
| 8 | §3 item 2: users need read access to both repositories. §2.2: "Releases are assets of a private GitHub repository". §7.5: CI reads deep-reasoning through an `insteadOf` line | deep-reasoning is public [run: `gh api`]: only deep_reasoner_beta needs read access, release assets are public downloads, and no workflow adds an `insteadOf` for deep-reasoning (the one for DeanLight stays) [read] | `.github/workflows/` | Michael: "public downloads are fine" |
| 9 | §1.3 (D5 owns "the README's install section"), §2.3, §3 item 12, §4.2.6 (`xattr -dr com.apple.quarantine …`), §4.8.3 (uninstall) | **A root `README.md` exists since `c9bb7fe`. Closed in r2.** At `3c923aa` there was none. It holds the install section the design asks for, with the quarantine command, the `PATH` line, uninstall and §2.2 in short; how it differs from the design is #18. `tests/desktop/test_readme.py` pins its names and commands to the code's constants: the `.dmg`'s name and the macOS minimum, the quarantine command, the model key and where setup asks for it, setup's access check, the `PATH` line and the linked commands, the uninstall paths, the safety sentence with the default cap [run] | `README.md`; `tests/desktop/test_readme.py` | r1's finding; Michael approved the fix |
| 10 | §7.5: four jobs, `pins`, `desktop-e2e`, `bridge-replay`, `canvas-replay` | **Six.** `has-d5` first: the others run only when `desktop/pins.toml` exists, so `main`'s copy skips instead of failing. `library-app` runs §7.2's `crossrepo` test of the staged App as a job of its own. D4's forwarding test runs inside `bridge-replay` (§8.7 said "beside"). `desktop-release.yml` also starts with `has-d5` [read; CI] | `.github/workflows/cross-repo.yml` | `57c019d` |
| 11 | Decision M: `main` carries copies of the on-demand workflows | `main`'s copies (`f1ca641`) are older than `v1-desktop`'s. Its `desktop-release.yml` builds `mac-universal`, which `build.py` at `3c923aa` rejects, and adds the deep-reasoning `insteadOf`; its `cross-repo.yml` has only `has-d5`, `library-app` and `bridge-replay`. No run uses them while `main` lacks D5's code: there `has-d5` skips every job. Dispatched runs, and the nightly (`--ref v1-desktop`), use `v1-desktop`'s files, and a tag the tagged commit's [run: `git diff`; read] | `main`'s `.github/workflows/` | #34 and #35 placed them before the later commits |
| 12 | §7.5's seven steps and the final flow | **17 tests sharing one launch** (§5.2). Where they differ: the first conversation is onboarding's hello, not a dismissed onboarding; two tests the design does not list check that no consent dialog shows (a fixed 5 s wait) and that no consent is recorded and Settings has no analytics switch; the Library config is written by the test (there is no `e12/main.yaml`); Stop's plan spawns the done sibling first and holds the grandchild's model call until `dr-acp` logs `stop.accepted`; costs are compared with each sub-agent's cost in the run log at its end; the next conversation asks a plain question after the slash menu offers the command (the design asks for the offer and the recorded version, which hold); the cookie is read with `Storage.getCookies`; the MCP server is added through `POST /api/settings/mcp/echo` and the Tools tab reopened; the quit test asks that no process's command line names the fresh HOME [read; CI] | `tests/desktop/test_e12.py` | `c538fb3`, `1a90887`, `d39be70`, `8ce99b2`; Canvas `dr-3` (§1.2); TASK-38 |
| 13 | §7.6: the macOS job launches the app once and waits for `backend ready` | One launch, two tests: `app_ready(…, "installed")` in the log, the backend `ready`, the app quits with 0; and, on macOS, `lipo -archs` of the launched executable and of the bundled uv is `arm64` [read; CI] | `tests/desktop/test_launch_smoke.py` | `bd6e170` |
| 14 | §4.2.2's checks; §5.8 | Check 2 gives two sentences (the wired repository, the wired commit). Check 5 looks at `paths.stateDir` and `setup.command`, not all of `setup` (the fork sets `setup.phases`). Check 8 clones the fork's `deep-reasoning` branch bare and blobless and asks `git merge-base --is-ancestor <commit> refs/heads/deep-reasoning`, not `FETCH_HEAD`; its refetch is #21. `build()` copies the artifacts to `<repo>/dist/` [read] | `build.py:233-299, 337-370, 539-544` | none recorded |
| 15 | §5.2 puts `SetupError` in `dr_app.runtime`; §6's table | `SetupError` lives in `dr_app.layout` and `runtime` re-exports it. Four sentences §6 lacks: `NO_AGENT_SERVER` (after-ready without the launcher's variables, exit 2), `home_refused` (`dr-app home` with a relative path or a network filesystem), `home_too_long` (#4) and, since `930a0cf`, `state_from_a_newer_app` (#20) [read] | `layout.py:34-41`; `texts.py:31-34, 97-118, 136-142` | none recorded |
| 16 | §8.7: an MCP server's environment holds "only its configured variables and `mcp`'s six" | The test also admits `LC_CTYPE`, which D4's stdio guard, a Python, adds when it coerces a C locale (PEP 538). It runs twice, with and without the model key named in the server's settings [read; run] | `tests/acp/test_e10_keys.py:220-288` | in the test's comment |
| 17 | §10: ≈1.45k lines of code, ≈1.24k of tests | **≈3.2k and ≈4.6k.** Code: 3,027 lines in D5's own files (428 of them workflows) and +133 net in D1's. Tests: 4,440 in D5's own files and +115 net in D1's and D3's. The README adds 203. Largest: `test_e12.py` 727, `proxy.py` 703, `test_key_proxy.py` 657, `build.py` 575. At `3c923aa` the two totals were 2,995 and 4,311 [run: `wc -l`, `git diff --numstat`] | — | none recorded; §4 says where it went |
| 18 | §2.3: the README's install section is "§2.2 in short, with how to uninstall"; §4.2.6, §4.8.3, §3 item 12 | The README follows the build, not §2.2, where they differ: release assets are public downloads. It adds what the design lacks: setup's own access check to run in a terminal (`GIT_TERMINAL_PROMPT=0 GIT_SSH_COMMAND='ssh -o BatchMode=yes' git ls-remote …`); that a credential helper named without a path must sit in `/opt/homebrew/bin` or `/usr/local/bin` on a Mac; the `.AppImage`'s steps; a hand-run build's artifacts, which need a GitHub sign-in; onboarding (keep **deep_reasoner**, press **Close** on **Say hello**, add `OPENAI_API_KEY` under Settings → Secrets before the first question); how to change the cap; and Electron's own folders in uninstall. Its timings are quoted from CI: "on GitHub's macOS runner it took 15 s, and the whole first launch under a minute", which is `3c923aa`'s release run; at `c9bb7fe` the same run took 16 s, and setup's two phases spanned 65 s (§5.2). It says each `v*` tag has a release; the repository has no tag and no release yet [run: `gh api`]. Its data table leaves out `canvas-app/` and `setup.lock`, and it does not say that `dr-app home DIR` refuses a folder too long for #4. `pyproject.toml`'s `readme` is still `AGENTS.md`, so the package's long description is not this README [read] | `README.md` | `c9bb7fe`'s message: "true for what is built" |
| 19 | §4.2.4: the wrapper config, whole; `verify()` checks names, payload paths and, since #1, Mach-O architectures | The wrapper config adds one key, `mac: { ...base.mac, minimumSystemVersion: "14.0" }`, so it is no longer §4.2.4's byte for byte. `verify()` reads the built `.app`'s `Info.plist` with `plistlib` and refuses an `LSMinimumSystemVersion` other than `MAC_MINIMUM` (`"14.0"`) with a sentence §6 lacks, `opens_too_early`: "✗ The app's Info.plist declares LSMinimumSystemVersion {declared}, not 14.0: desktop/electron-builder.dr.mjs's mac block sets it." [read; run: `test_build.py`; CI] | `electron-builder.dr.mjs:18-19`; `build.py:63-65, 189-193, 465-469` | `e5c8be2`: #2's fix |
| 20 | §4.3.2 and §6: exit codes 0, 10–13 and 2; `SetupState.load` "raises on v != 1" (§5.1) | **Exit 14** (`EXIT_STATE`): `load` raises `SetupError(14, texts.state_from_a_newer_app(path, version))`, which `main()` prints; the bootstrap passes 14 on, inside its trusted 10–19 band, without its fetch line. The sentence: "✗ {path} was written by a newer Deep Reasoning (its version {version}; this one reads 1). Install the newer app again. To set this one up from the start instead, delete {path}: your data stays, but a folder chosen with dr-app home is forgotten." [read; run: §1.3 #4] | `layout.py:30, 218-229`; `texts.py:136-142` | `930a0cf`: §1.3 #4's fix |
| 21 | §4.2.2 check 8: `git fetch --filter=blob:none <repo> deep-reasoning` into a cache, then `FETCH_HEAD` | A cache that exists is refetched with an explicit refspec, `git fetch --filter=blob:none origin +refs/heads/deep-reasoning:refs/heads/deep-reasoning`, so the branch ref the check reads follows the fork [read; run: §1.3 #1] | `build.py:337-356` | `24646d0`: §1.3 #1's fix |

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
- **§7.4**'s "dispatched again on `v1-desktop` with `sdk_ref` `dr-2`": done, run 37241495293 (§5.2).
- **§11 items 4, 5, 11, 12 and 15** were questions for the first runs; §5 answers them.
- *(r2)* **§4.2.4's wrapper listing, §4.3.2's exit codes, §5.1's `SetupState.load` docstring and §6's build
  sentences** no longer list everything the code has: §1.1 #19 and #20.

### 1.3 Behaviour the design does not state

1. **Check 8 on a reused `--work`. Closed in r2.** At `3c923aa`, `fork_cache` refetched with `git fetch
   --filter=blob:none origin deep-reasoning` into a bare clone that has no fetch refspec, so the fetch moved only
   `FETCH_HEAD`, and `refs/heads/deep-reasoning` stayed as first cloned [run at 3c923aa: §5.4's probe]. With the
   default `--work`, `<repo>/.desktop-work`, which persists, a pin to a commit merged into a fork's branch after that
   clone was refused; CI, with a fresh `--work` per job, was not affected. `24646d0` names the branch's ref in the
   refetch (§1.1 #21). Pinned by `test_check_8_on_a_reused_work_dir_sees_commits_merged_since_its_first_clone` (a
   local bare fork, a commit merged after the first clone) [run]; `build.py check` twice on one `--work` against the
   real forks passes both times, the cache's branch at the fork's head `4355a36` [run].
2. **The default suite needs the network.** `test_the_runtime_lock_installs_on_every_platform_the_app_ships_for`
   (two cases: Linux x86-64, macOS 14 arm64) dry-runs the lock against PyPI's metadata, and carries no marker [read;
   run].
3. **Two default-suite tests restate the committed pins:** `test_the_committed_sdk_pin_is_34c540c_tagged_dr_2` (and
   `uv_version`) and `test_the_committed_pins_load` (both forks). A pin bump edits them [read].
4. **A `setup.json` whose `v` is not 1. Closed in r2.** At `3c923aa` it raised `ValueError`, which `main()` did not
   catch: a traceback and exit 1, outside the 10–19 band in which the bootstrap trusts `dr-app` to have explained
   itself [read at 3c923aa]. Since `930a0cf` it is exit 14 with `state_from_a_newer_app` (§1.1 #20), for `setup`,
   `export` and `home` alike. Pinned by `test_setup_state_from_a_newer_app_is_explained_and_exits_14` (`setup` and
   `home`: the sentence, no traceback, no `uv` or `git` run) [run]. Two cases fit it less well [run: `dr-app home`
   against each file]: a `setup.json` with no `v` gets the same sentence, calling it a newer app's ("its version
   None"); one that is not JSON still ends in a `JSONDecodeError` traceback, exit 1. `SetupState.save` writes through
   a temporary file and a rename, so setup itself leaves neither [read].
5. **Setup is silent while git waits on a credential dialog.** The macOS smoke's 15-minute hang (§5.3) was a keychain
   dialog under the test's fresh HOME; the fix (`269c7af`) is in the test, which gives that HOME an empty credential
   helper. The splash says nothing while setup waits (TASK-39) [read; CI].

### 1.4 Where the design holds

Decisions A to P hold as written, apart from §1.1 [read; the runs of §5 exercise each]: pins by full commit with tags
beside them; an `sh` bootstrap around `uvx` of the standard-library-only `deep-reasoning-app` fetched by commit with
`#subdirectory=`; a runtime venv from the committed export of `uv.lock`, swapped in by the `runtime/current` link;
one root `~/.deep-reasoning`, DR_HOME the root or `/var/tmp/deep-reasoning-<uid>`, passed only as `--home`; an
idempotent cheap path; the profile's four owned fields and the `--home` pair, activated once; the Library App staged
from three of D3's files and a generated one-script artifact, approved and started on every launch; the key proxy on
its own thread in `dr-acp`'s front, on by default; telemetry off at build time; the wrapper electron-builder config;
the ingress left to C3; texts as functions; `run_logged`. Every sentence in §6's two tables is the code's,
verbatim [run: each compared with the code]; the bootstrap's and the new ones
are §1.1 #7, #15, #19 and #20. The wrapper config is §4.2.4's but for its `mac` key (§1.1 #19), and the bootstrap
§4.3.1's but for its fetch line [run: `diff`]. Every test the design's
§7 names exists, but for two of the bootstrap's, renamed with §1.1 #7 [run].

---

## 2 · What exists

| Part | Files | Lines |
|---|---|---|
| The build | `desktop/build.py`, `pins.toml`, `bootstrap.sh`, `electron-builder.dr.mjs` | 629 |
| Setup | `packages/dr-app/` (`cli`, `layout`, `runtime`, `agent_server`, `profile`, `canvas_app`, `texts`; `runtime.lock.txt`) | 1,267 + a 176-line lock |
| The key proxy | `src/deep_reasoning/acp/proxy.py`, with `dr-acp`'s two options and the tool-client seam in D1's files | 703 + 133 net |
| CI | `cross-repo.yml`, `desktop-release.yml`, `nightly.yml` (on `main` only) | 428 |
| Tests | `tests/app/`, `tests/desktop/` (E12, the smoke, the README), `tests/crossrepo/`, `tests/acp/test_key_proxy.py`, `test_e10_keys.py` | 4,440 + 115 net |
| The README | `README.md`: what deep-reasoning is, the install section, §2.2 in short | 203 |

A build and a launch, as the code runs them [read; CI]:

```text
uv run desktop/build.py linux | mac-arm64            (on that machine only)
  pins.toml ─ check_pins, 8 checks ─ Canvas fork 4355a36 under --work
  defaults.json += paths.stateDir, setup.command (sh -c bootstrap … <commit>), setup.phases, telemetry key ""
  npm ci · VITE_DO_NOT_TRACK=1 npm run build:app · uv 0.12.23 and Node downloaded · electron-builder --config wrapper
  verify: the expected artifacts, no "deep_reasoner" in a payload path, arm64-only Mach-O, macOS 14 minimum ─ dist/

the app's launcher (C3), every launch
  before-start  sh bootstrap.sh → uvx dr-app@<commit> setup → data home · runtime (when not current) · bin/ links
  agent-server  SDK fork 34c540c on 127.0.0.1:18000
  after-ready   the same command → profile deep_reasoner · model-key hint · Library App staged, installed, ready
  a conversation → ~/.deep-reasoning/runtime/current/bin/dr-acp --home <DR_HOME> --spend-cap-usd 5
                    front: KeyProxy on 127.0.0.1:<port> ── real key ──▶ provider;  worker: tokens only
```

### 2.1 The build: `desktop/`

`build.py` is standard library only. `check_pins` takes its readers as arguments (`ls_remote`, `read_sdk_file`,
`is_on_branch`), so the tests run every check without a network; `build()` passes git-backed ones. Of the fork's
files it changes only `config/defaults.json`, in a detached checkout under `--work`, and it commits to neither
fork. The setup command it embeds is

```text
["sh", "-c", <bootstrap.sh>, "dr-app-bootstrap",
 "git+https://github.com/michaeltheologitis/deep-reasoning@<HEAD>#subdirectory=packages/dr-app",
 "https://github.com/michaeltheologitis/deep-reasoning", <HEAD>]
```

with the repository URL a constant (`DEEP_REASONING`) and the commit the checkout's `HEAD`. `pins.toml` holds the two
forks' repositories, commits and tags and the `[app]` values; deep_reasoner's pin is a line of `runtime.lock.txt`
[read].

### 2.2 Setup: `dr-app`

`cli.main` dispatches `setup`, `export` and `home`; `setup` holds `setup.lock` (`fcntl.flock`) for its whole run.
The modules split as the design's §5 does: `layout` (paths, the data home, `setup.json`, `SetupError`), `runtime`
(the lock, the checks, `run_logged`, the install), `agent_server` (a `urllib` client with no proxy handler),
`profile`, `canvas_app` and `texts`. Their seams carry plain values: a `RuntimeSpec` (the lock, its digest, the
requirements text, deep_reasoner's URL and commit) into `install_runtime`; `SetupState`'s records out of each step
into `setup.json`; the agent-server's JSON in and out. §4.2 says where its complexity sits.

### 2.3 The key proxy, and D1's seam

D1's files gain a tool-client half of the route seam, additive, as §8.1 designed it [read; run: D1's suite]:
`RunSource.tool_clients` (filled by `ConfigCatalog.materialize` for every tool block with its own `client`),
`ModelRoute.grant(…, tool_upstreams=…)`, `RouteGrant.tool_client_overrides`, `Start.tool_client_overrides`, and the
worker's `run_config(start)`, which merges each over its tool's client. `DirectRoute` accepts and ignores it.
`dr-acp`'s `main()` builds `SpendLedger`, `KeyProxy` and `ProxyRoute(proxy, os.environ)` unless `--no-key-proxy`, and
stops the proxy with a 0.5 s budget when `serve()` returns. `proxy.py` holds the rest: the ledger, the HTTP side
(Starlette under uvicorn on a daemon thread, a socket bound to `127.0.0.1:0` first), and the grant. §4.1 walks a
request.

### 2.4 CI

| Workflow | Trigger | Jobs |
|---|---|---|
| `cross-repo.yml` | pull requests touching the app, `workflow_dispatch`, nightly | `has-d5`; `pins` (`build.py check`); `desktop-e2e` (Linux build, `.deb` installed, E12 under `xvfb-run`); `library-app`; `bridge-replay` (E5 and D4's forwarding test); `canvas-replay` (E6, C1's replay spec in the Canvas fork's mock-LLM stack) |
| `desktop-release.yml` | a `v*` tag, `workflow_dispatch` | `has-d5`; `cross-repo-green` (tags only: a successful `cross-repo.yml` run on the commit); `linux`; `macos` (`mac-arm64`, then the launch smoke on the `.app` from the `.dmg`); `release` (tags only: create the release, upload with `--clobber`) |
| `nightly.yml` (`main`) | `17 6 * * *` | `gh workflow run cross-repo.yml --ref v1-desktop` |
| `fork-live.yml` (on `main` since `633a00d`, before this branch) | `workflow_dispatch` | S1's and S2's live files against `dr-acp` from the dispatched ref |

Every job that installs deep_reasoner reads deep_reasoner_beta through `DEEP_REASONER_TOKEN` in an `insteadOf` line;
no job calls a model but `fork-live.yml` [read].

### 2.5 Which tests carry what

- **The build:** `tests/desktop/test_build.py`, 22 tests: each check's refusal, check 8 on a reused `--work`, the
  defaults, the setup command, a `.deb` listing with spaces, the arm64 and macOS-minimum checks, the per-machine
  targets, the committed pins. `tests/desktop/test_readme.py`, 6 tests: the README's names against the code's.
- **Setup:** `tests/app/`, 57 tests, against stub `uv`, `uvx` and `git` scripts and `fake_agent_server.py`, an
  in-test HTTP server answering like the agent-server; one `crossrepo` test against the SDK fork's real agent-server.
- **The proxy:** `tests/acp/test_key_proxy.py` (in process, `httpx.ASGITransport`), E10 in `test_e10_keys.py` (a real
  `dr-acp` over stdio), and D1's tests for the seam.
- **Across repositories:** `tests/crossrepo/` (E5's replay, D4's forwarding), `tests/desktop/test_e12.py` (E12 on the
  installed app), `test_launch_smoke.py`, and `tests/desktop/test_app.py` for the launch harness itself.

---

## 3 · The public surface, from the code

```text
uv run desktop/build.py {linux|mac-arm64|check} [--work DIR]          default --work: <repo>/.desktop-work
dr-app setup [--phase before-start|after-ready] --repo URL --commit SHA
dr-app export DIR [--namespace NAME]                                   runtime's dr-library export … --home DR_HOME
dr-app home [DIR]
dr-acp … [--spend-cap-usd USD] [--no-key-proxy]                        default 5.0; the proxy is on
```

- **Exit codes** [read]: `dr-app` 0; 10 a check failed; 11 the install failed; 12 the agent-server refused what setup
  needs; 13 the data home is unusable, too long, or nothing is installed for `export`; 14 `setup.json` has another
  version; 2 usage, or after-ready without `AGENT_SERVER_URL` and `SESSION_API_KEY`. The bootstrap exits 10 without
  git and otherwise passes `uvx`'s status on.
- **On disk** [read; CI: E12]: `~/.deep-reasoning/` (0700) holds `canvas/` (the agent-server's root; C3's state
  directory `canvas/agent-canvas/`), `runtime/<commit>/` and the `runtime/current` link, `bin/dr-app` and `bin/dr`,
  `canvas-app/<digest>/`, `setup.json`, `setup.lock`, and, as DR_HOME on a local home, D1's and D2's files and
  `spend/<session>.json`.
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
- **Python** [read]: `deep_reasoning.acp.proxy`: `SpendLedger(home, cap_usd)` with `reserve`, `settle`, `spend`;
  `KeyProxy(ledger=, prices=, home=)` with `ensure_started`, `stop`, `base_url`, `add_route`, `drop_run`, `app`;
  `ProxyRoute(proxy, env)` with `grant` and `release`; `loopback_proxy_env`; `is_loopback`. D1's additions are named
  in §2.3. `dr_app`'s functions keep §5's signatures, except where `SetupError` lives (§1.1 #15).

---

## 4 · Where the complexity sits

### 4.1 The proxy: a grant, then a request

**A grant** (`ProxyRoute.grant`, `proxy.py:625-684`) [read; run: `test_key_proxy.py`, E10]. For the main client and
each tool's own client, the key's name is `api_key_env`, else `NOVITA_API_KEY`, falling back to `OPENAI_API_KEY` as
deep_reasoner's `build_client` does; a client whose key `dr-acp` lacks is left as configured. If nothing is held and
there is no `ANTHROPIC_API_KEY`, the grant is empty and the proxy never starts. Otherwise: one 256-bit token per key
name, one route per (upstream, key name), the overrides `{base_url: <route url>, api_key_env: <name>}`, and for a
held Anthropic key a route of its own exported as `ANTHROPIC_API_KEY` and `ANTHROPIC_BASE_URL`. The worker's
environment loses every variable whose value contains a held key, or a value of at least 16 characters held by a
variable D1's `ALWAYS_REMOVED` patterns name; then each key's own name comes back holding its token. `NO_PROXY` gains
the loopback hosts; on macOS, with no proxy in the environment, the system's HTTP and HTTPS proxies are exported too.

**A request** (`KeyProxy._handle` → `_metered` → `_forward`, `proxy.py:397-575`) [read; run: `test_key_proxy.py`]:
the token (`Authorization: Bearer`, else `x-api-key`) must hash to the route's, or 401 and nothing is forwarded; the
method must be POST and the path one of the dialect's, or 403; the body a JSON object of at most 32 MiB, or 400. A
model the price table cannot price is refused 400 unless the upstream is loopback. An openai stream gets
`stream_options.include_usage`. The reservation is the table's price for `ceil(len(body) / 4)` input tokens and
`max_completion_tokens`, `max_tokens` or 4,096 output (0 for embeddings); `SpendLedger.reserve` refuses with 402 when
spent, reserved and this estimate pass the cap. The call goes upstream with the real key and with `trust_env` off for
a loopback upstream. A successful event stream is relayed as it arrives and metered from it; anything else is read
whole, with the key replaced by `[redacted]` in a non-2xx body. Settlement is §1.1 #5. The ledger's file,
`<home>/spend/<session>.json`, is rewritten after each settle and each refusal and read at a session's first use, so
a restarted `dr-acp` continues the count. One `threading.Lock` guards the ledger, one the routes.

### 4.2 Setup: the cheap path, and everything that is not

**before-start** (`cli.before_start`, `cli.py:72-113`) [read; run: `tests/app/`; CI: E12]: choose the home (§1.1 #4
included) and say it when it changes; if `runtime_is_current` (the record's commit and lock digest, `runtime/current`
resolving to the record's path, and one exec of its Python), skip to the links. Otherwise git, deep_reasoner's
readability (`git ls-remote`, output discarded) and `uv` on `PATH`, the safety sentence on a first install, then
`install_runtime`: remove `*.tmp-*`, `uv venv --relocatable`, `uv pip sync` of the lock plus the two git lines, an
import check of `dr-acp`'s, `dr-library`'s and deep_reasoner's entry modules, rename, swap the link, remove every
other runtime. Every subprocess goes through `run_logged` (`runtime.py:99-136`): one pipe for stdout and stderr, each
line logged as it comes, and a return at the process's exit plus at most 1 s of draining, so a grandchild that keeps
the pipe cannot hold the launcher's phase.

**after-ready** (`cli.after_ready`, `cli.py:124-147`) [read; CI]: the profile (§3; a write only when an owned field or
the arguments differ; activated only when `setup.json` has no record of setup activating it, so a profile the user
deleted is recreated but not made the default again); the model-key hint; then the Library App
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
later conversation. Two waits are deliberate: Stop's grandchild model call waits on an event set once the
run log shows `stop.accepted`, and the header-panel test waits out the bridge's five-minute session plus 20 s [read].
`tests/desktop/app.py` holds the launch harness (fresh HOME, the user's environment without the runner's uv and venv
variables, a log tail on a failed wait) and `e12/subagents.py` the Python copies of C1's two DOM reads.

---

## 5 · Experiments and measured results

No run here called a model. The live tier's model calls are the Implementer's run, attributed.

### 5.1 The runs at `c9bb7fe`

| Workflow | Run | Result [CI] |
|---|---|---|
| `ci.yml` (push) | [37246565304](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37246565304) | `test`: ruff over `src tests packages desktop` clean; 845 passed, 115 deselected in 589 s. `canvas-app`: green |
| `cross-repo.yml` (dispatch) | [37246570008](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37246570008) | All six green on attempt 1 |
| `desktop-release.yml` (dispatch) | [37246572498](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37246572498) | `linux`, `macos` green, `verify()` and its `Info.plist` check included; `cross-repo-green` and `release` skipped (no tag) |
| `fork-live.yml` (dispatch, `sdk_ref` `dr-2`) | [37247433818](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37247433818) | S1 2 of 2, S2 8 of 8, on gpt-6-luna |

### 5.2 Each experiment

**pins** [CI]: "the pins belong together ✓" (all eight checks, real forks). The same check passes here, twice on one
`--work` [run, §5.4].

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
3 s (`.deb` 150 MB); **17 passed in 419.7 s**. The first launch, from a cold uv cache under a fresh HOME through both
setup phases to the window, passed 36.9 s after collection. The header-panel test, which waits past the bridge's first
session, took 320.5 s, most of E12's time. Proven inside the real app: the worker's environment holds neither the key
nor the session or secret key, and no stored file does; D3's frame works through the bridge with a partitioned
`Secure; SameSite=None` cookie whose partition is `http://localhost`, and is refused 401 after the session is deleted;
C1's tree equals the run log's (3 sub-agents, 1 nested), costs match, and Stop stops a child and its branch while its
done sibling stays done; C2's picker, slash menu, header panel and Create decomposition; D4's MCP server is bound and
called; the app quits within 6 s; setup relaunches with the network cut in under 5 s and installs nothing.

**E5's second half, `bridge-replay`** (`tests/crossrepo/`, SDK fork `34c540c`; reproduce: `DR_SDK_CHECKOUT=<checkout>
uv run pytest -m crossrepo tests/crossrepo`) [CI]: **11 passed in 40.5 s**: each of D1's ten native recordings is
stored by the agent-server as the tree it records, and D4's forwarding test passes. `library-app`: 1 passed in 13.8 s
(the staged App passes `prepare` and its backend answers `/health`).

**E6, `canvas-replay`** (C1's replay spec at Canvas `4355a36`) [CI]: **10 of 10** on attempt 1. TASK-40's race did not
show this time; at `3c923aa` it failed attempt 1 (§5.3).

**The launch smoke** (`macos`, `macos-26-arm64` runner image) [CI]: the `.dmg` built in 3 min 34 s, its `.app`
passing `verify()`'s architecture and `Info.plist` checks; **2 passed in 83.5 s**: the backend ready after the first
launch, the app quit with 0, and the launched executable and its uv are arm64 only. The job keeps the app's log
(`desktop-macos-launch`), which times the first launch on a Mac: before-start `installed in 16s` and `Done in 21s`;
then 40 s for the agent-server's own install; after-ready `App dr-library 0.1.0 installed · backend ready` 3 s in,
`Done in 4s`. Setup's two phases, and the agent-server between them, spanned 65 s. Artifacts as uploaded (zip):
macOS 178,484,169 B, Linux 345,946,896 B.

**The live tier** (`fork-live.yml`, `dr-acp` from `c9bb7fe` with the key proxy on, as no flag turns it off) [CI]:
S1's `test_live_agent_tree_is_well_formed` and `test_live_agent_stops_one_subagent_and_its_branch`, 2 passed in
38.8 s; S2's file, 8 passed in 102.2 s. The model was gpt-6-luna; I did not re-run it.

### 5.3 Earlier runs, for history [CI]

- **At `3c923aa`, r1's evidence:** `ci` 37240441891, 833 passed. `cross-repo` 37240441432, all six green on attempt 2;
  attempt 1 failed only `canvas-replay`, on `fanout20.native.jsonl`, whose rows `n16` and `n17` were read before their
  tool calls rendered (five passed, four skipped after it; TASK-40). E12 there: 17 passed in 428.7 s, the first launch
  37 s after collection. `desktop-release` 37240443237: the smoke 2 passed in 54.2 s; its app log has before-start
  `installed in 15s` and `Done in 19s`, 21 s for the agent-server, after-ready `Done in 2s`, 42 s across both phases.
  `fork-live` 37241495293: S1 2 of 2, S2 8 of 8.
- **At `e5c8be2`**, the first proof of §1.1 #2's fix: `desktop-release` 37245365250, `linux` and `macos` green with
  the `Info.plist` check; the smoke 2 passed in 55.6 s, `installed in 14s`.
- `desktop-release` 37226929314 (`9ca1f70`): `macos` red. The launch smoke waited its limit on a keychain dialog
  under the fresh HOME (§1.3 #5); fixed in the test by `269c7af`, and failures made readable by `ae363b4`.
- `cross-repo` 37230954884 (`d39be70`), 37236303764 (`8ce99b2`), 37238261156 (`a4a9336`): all six jobs green.
- `desktop-release` 37231871112 (`d39be70`): green, with the universal `.dmg` of that time.
- `desktop-release` 37238259690 (`a4a9336`): `macos-intel` red, the job since dropped (§1.1 #1).

### 5.4 Run here

**At `c9bb7fe`** [run]:
- **The default suite** (`uv run pytest`, Python 3.12.15, no `DR_BETA_CHECKOUT`): 708 passed, 4 failed, 5 skipped,
  115 deselected, in 7 min 32 s. D5's own files and the D1 and D3 files it edits: **176 passed**, 1 skipped (D1's
  catalog test that needs `DR_BETA_CHECKOUT`), in 92 s; r1 had 164, and the twelve more are the fixes' tests and
  `test_readme.py`. The four failures are r1's: D1's golden recordings `failing` and `unanswered`, both modes, embed
  CPython's stdlib line numbers in a traceback (`asyncio/runners.py`, line 194, from CI's 3.12.3), which this
  machine's 3.12.15 numbers otherwise. They pass in CI, and D5 does not touch them. The smaller total than CI's 845 is
  the D2 corpus tests that `DR_BETA_CHECKOUT` parametrizes.
- **`build.py check` twice on one `--work`**, against the real forks: "the pins belong together ✓" both times, 6.2 s
  and then 3.7 s, the second through the refetch of §1.1 #21; the cache's `refs/heads/deep-reasoning` is the Canvas
  fork's head, `4355a36`. The `--work` was in a scratch directory, since removed.
- **`dr-app home` against three `setup.json` files** under a scratch HOME: `{"v": 2}` and `{"x": 1}` exit 14 with
  `state_from_a_newer_app`; `{` exits 1 with a `JSONDecodeError` traceback (§1.3 #4).
- **§6's sentences:** each of both tables compared with the code, all equal.

**At `3c923aa`, r1's probes** [run at 3c923aa; nothing they ran has changed since, but for §1.1 #21's refetch]:
- **Setup, for real, with uv 0.12.23.** The bootstrap exactly as the launcher runs it, under a HOME in my scratch
  directory: `uvx` fetched and built `dr-app` from GitHub at `3c923aa` and `dr-app` refused the home, exit 13,
  `home_too_long` ("up to 146 bytes long, and this system allows 107"), passed through without the bootstrap's fetch
  line; 3.3 s cold, 0.12 s warm, 0.12 s again inside `unshare --map-root-user -n` (no network). Then before-start
  itself, with the socket limit patched out for that long HOME: a first install from a cold uv cache, the managed
  CPython 3.12.15 download included, printed `installed in 11s` (12.0 s in all; 173 packages). The runtime is 473 MB,
  and the whole HOME 649 MB with uv's cache and the managed Python; the runtime's entry points start with
  `#!/bin/sh`, uv's relocatable form (§1.1 #3). A relaunch's before-start took 0.019–0.020 s (three runs).
- **macOS's minimum:** a wheels-only dry run of the lock's registry packages for `aarch64-apple-darwin`, Python
  3.12, uv 0.8.17: with `MACOSX_DEPLOYMENT_TARGET=13.0`, "onnxruntime==1.30.0 has no wheels with a matching platform
  tag (e.g., `macosx_13_0_arm64`)"; with 14.0, 170 packages resolve.
- **Check 8's cache, before the fix:** a bare, blobless, single-branch clone of a local repository, a new commit on
  the source branch, then `git fetch --filter=blob:none origin deep-reasoning`: `FETCH_HEAD` moved,
  `refs/heads/deep-reasoning` did not, and `merge-base --is-ancestor <new> refs/heads/deep-reasoning` exited 1.

### 5.5 What the design's §11 asked to be measured

- **Item 5, `uvx`'s start for `dr-app` on a relaunch:** 0.12 s warm, with or without a network, for `sh`, `uvx` and
  `dr-app` up to its home check; the cheap path after it, 0.02 s [run at 3c923aa]. E12 asserts the whole offline
  relaunch of before-start finishes in under 5 s [CI].
- **Item 5, the first install's time and disk use:** 11 s and 473 MB of runtime (649 MB with uv's cache and Python)
  here [run at 3c923aa]; 14–16 s on GitHub's macOS runner across three release runs, and E12's whole first launch
  under 37 s on its Linux runner [CI]. The design's mock-up figure of two minutes was not reached; a user's network
  sets it.
- **Item 5, the after-ready cost of starting the backend:** after-ready took 2–4 s on the macOS runner, the App's
  `backend ready` 2–3 s after the phase began, the profile written within a second of it [CI: three launch logs].
  Between the phases, the agent-server's own install and start took 21–40 s.
- **Item 4, macOS on hardware:** the launch smoke ran on GitHub's `macos-26-arm64` image; nothing ran on macOS 14.
  The system-proxy handling (§4.7.2 step 5) has unit tests only.
- **Item 11, the cookie in Electron's Chromium:** holds (E12, §5.2). **Item 12, the `.mjs` wrapper config:** builds
  on both platforms. **Item 15, uv 0.12.23 for D5's own commands:** E12 and the smoke run them with the bundled uv
  0.12.23, and so did §5.4.

---

## 6 · Open items for Gate B

r1's numbers kept; the closed ones struck through.

1. ~~**The macOS minimum is not enforced.**~~ Closed by `e5c8be2` (§1.1 #2).
2. ~~**There is no README.**~~ Closed by `c9bb7fe` (§1.1 #9); where it differs from the design is §1.1 #18.
3. **TASK-39:** the splash says nothing while setup waits (on a credential prompt, or a slow first install). The README
   now tells the user to quit and run setup's access check in a terminal when setup stops moving.
4. **TASK-38:** E12's Stop saw a sibling spawned in the same `run_all` still running when Stop was pressed; whether
   that is the fake holding a call or real serialisation in D1 is open. E12 spawns the done sibling first.
5. **TASK-40:** C1's replay spec reads the DOM once and fails about one nightly run in five; the fix is in the Canvas
   fork. At `c9bb7fe` it passed on attempt 1.
6. ~~**Check 8 on a reused `--work`.**~~ Closed by `24646d0` (§1.3 #1).
7. **`main`'s workflow copies are behind `v1-desktop`'s** (§1.1 #11). Nothing runs them while `main` lacks D5's code;
   D5's PR stack replaces them.
8. *(r2)* **What the README says that is not exact** (§1.1 #18): each `v*` tag "has a release", and there is no tag
   yet, so a Gate B install comes from a hand-run build's artifacts; "the whole first launch under a minute", where
   `c9bb7fe`'s macOS run spanned 65 s across setup's phases; and `pyproject.toml`'s `readme` is still `AGENTS.md`.
9. *(r2)* **Two `setup.json` cases outside exit 14** (§1.3 #4): one with no `v` is called a newer app's, and one that
   is not JSON still ends in a traceback.
10. *(r2)* **Gate B's install is the `3c923aa` build.** It differs from `c9bb7fe`'s in the four fixes only: its `.app`
    was built without the `minimumSystemVersion` key, and the setup command it embeds installs `dr-app` and the
    runtime at `3c923aa`, where a newer `setup.json` is a traceback. On macOS 26 none of this changes what an install
    shows [read].

## 7 · What I could not verify

- **Nothing ran on a Mac here.** Every macOS claim is [CI] (one runner image, macOS 26) or [read]: the arm64 and
  `Info.plist` checks (their CI passes are evidence), the Finder `PATH`, the system-proxy export, the quarantine flow.
- **That macOS 13 refuses to open the app** [read]: `LSMinimumSystemVersion` is declared 14.0 and `verify()` checks it
  on the real `.app` [CI]; what macOS 13 then does is Apple's behaviour, not run.
- **The README's uninstall paths for Electron's folders** [read]: Canvas's `electron/main.mjs` sets no `userData`
  path, so Electron's default under the product name applies (`~/Library/Application Support/Deep Reasoning`,
  `~/.config/Deep Reasoning`); no run listed them.
- **A user's onboarding without a key** [read]: the **Say hello** step's **Close** button exists in Canvas `4355a36`
  (`say-hello-step.tsx`, `BUTTON$CLOSE`); E12 sends the hello with the key already saved, so pressing Close, and what
  a hello sent with no key does, never ran.
- **I did not install or launch the app.** E12, the smoke and the cross-repo jobs are [CI]: I read their logs and did
  not re-run them. E12's assertions are as §5.2 states them, read from the test and its passing log.
- **The live tier** made model calls; I read its log and did not re-run it. That `dr-acp` there ran with the proxy is
  [read]: `fork-live.yml` passes no `--no-key-proxy`, and the proxy is on by default.
- **The after-ready phase against a real agent-server** (the profile, the App's install, `prepare` and `start`) is
  [CI] (E12, `library-app`, the smoke) and [run] only against `tests/app/fake_agent_server.py`.
- **TASK-38's cause**, and the Claude CLI behind the proxy (design §11 item 3): untested by D5's suite.
- **The design's §4.2.5** (strings that stay upstream's in the app): only seen in part. The macOS launch log prints
  upstream's "OpenHands Agent Canvas (Static)" banner [CI]; the rest is not checked.
