# D5 · Desktop app: build, install and launch, as built

**TASK-10** · Cartographer · revision 1 · 2026-10-04 · the code at `3c923aa` (head of `v1-desktop`; this file is on
`as-built/d5`) · checked against design v2 (`docs/design/d5-desktop-app.md`, last changed in `9ee36f6`, unchanged at
`3c923aa`) · Canvas fork `dr-3` = `4355a36` and SDK fork `dr-2` = `34c540c`, read only.

**What D5 is, in git.** `v1-desktop` was cut from `main` at `1f9fe52` and has merged `main` three times (D4 `53c821b`,
`b2a74e0`, `f1ca641`); `main` (`f1ca641`) is an ancestor of `3c923aa`, so `git diff f1ca641 3c923aa` is D5 and
nothing else [run]. That is 34 commits: the design's two (`8086afb`, `9ee36f6`) and 32 of code and tests. Two more
are on `main`, through #34 and #35: the workflow copies decision M asked for.

**Evidence marks.** Every claim carries one.
- **[run]**: executed on this machine at `3c923aa`: the default suite, `build.py check` against the real forks, the
  probes of §5.4 (not committed), `git` and GitHub's REST API.
- **[CI]**: read from GitHub's logs of the runs in §5.1. I dispatched no workflow and made no model call.
- **[read]**: read in the code and **not executed**. This is weaker evidence than [run]. §7 lists the read claims
  that matter most.

**Reading order:** §1, the divergences (start here); §2–§4, the map, the surface and where the complexity is; §5,
the measured results; §6, the open items for Gate B; §7, what I could not verify.

---

## 1 · Divergences from design v2

The design has not changed since `9ee36f6`, written before any code. The Changelog's one entry for TASK-10 (2026-10-04
20:47, the Canvas fixes) has an empty Drift line [read: Notion], so everything below was found in the code, its
history or the runs.

### 1.1 Built otherwise than the design says

| # | Design says | Built | Where | Reason recorded |
|---|---|---|---|---|
| 1 | §1 item 1, §4.2.4 step 3, §5.8, §7.6: one universal `.dmg`; `build.py {linux\|mac\|mac-universal\|check}`; `ELECTRON_ARCH=universal` | **Apple silicon only.** Targets `linux` and `mac-arm64`; each refuses to run on any machine but Linux x86-64 or macOS arm64, because the fork packages uv and Node for the machine it builds on. `verify()` requires `deep-reasoning-<version>-arm64.dmg`, and `lipo -archs` = `arm64` for the `.app`'s Electron, uv and Node. `desktop-release.yml` has no Intel job; a tag's release needs `linux` and `macos`. [read; run: `test_build.py`; CI] | `desktop/build.py:50-67, 170-182, 405-453` | Michael, 2026-10-04: "lets drop the intel macs" (`bd6e170`). The Intel lock holds `2e883e7` and `a4a9336` are undone by `3500f87`: `uv.lock`, `runtime.lock.txt` and `pyproject.toml` equal `f32e152`'s [run: `git diff` is empty] |
| 2 | No macOS version is named | **macOS 14 or later, unenforced.** onnxruntime 1.30.0 (chromadb's, through deep_reasoner) ships `macosx_14_0_arm64` wheels and none older; a wheels-only dry run of the lock fails for macOS 13.0 on that package and passes for 14.0 [run, §5.4]. Neither the wrapper config nor the fork's `mac` block sets `minimumSystemVersion` [read]; the release notes say "macOS 14 or later" [read]. On macOS 13 the app would open and setup would stop at `uv pip sync` with `install_failed`, exit 11 [read: inferred, not run] | `desktop/electron-builder.dr.mjs`; `tests/app/test_runtime.py:211-252` | onnxruntime's wheels; open item, §6 |
| 3 | §4.4.3: `uv venv --managed-python --python 3.12 runtime/<commit>.tmp-<pid>`, then rename | `uv venv --relocatable --managed-python …`. Without it uv writes entry points with an absolute shebang to the temporary path, and after the rename every runtime command was dead: `dr-library` exited 127 as the App backend [read; CI: E12] | `runtime.py:224-238` | `622976b`, found by E12's first launch |
| 4 | §4.4.1: three rules for the data home | **A fourth.** `choose_home` and `dr-app home DIR` refuse, exit 13 with `home_too_long`, a home under which `runs/<run id>/children/<n>/repl.sock` (the home plus 52 bytes) would pass the Unix-socket limit: 107 bytes on Linux, 103 on macOS. The default homes fit (on macOS, user names up to 28 characters); a HOME under macOS's `$TMPDIR` is refused [read; run: `deepest_socket`, §5.4] | `layout.py:23-29, 111-155` | `b1e3df2`: deep_reasoner's Claude backbone serves its REPL socket under the run directory |
| 5 | §4.7.3: "no usage reported: the reservation stands" | Usage reported, at any status: charged. No usage on a 2xx: the reservation is charged. **No usage on a non-2xx: 0**, the reservation released. Upstream unreachable: 0 [read; run: `test_provider_errors_release_their_reservations`, `test_a_call_costs_its_reported_usage_else_its_reservation_unless_refused`] | `proxy.py:527-541, 568-574` | Michael's ruling, 2026-10-04 (`f385025`): the OpenAI client's four retries of a 500 had left five reservations standing as spend |
| 6 | §4.7.3's request path | Two additions. A body that is not a JSON object, or is over 32 MiB, is refused 400 `bad_body`, a sentence §6 lacks. `Accept-Encoding` is not forwarded and `Content-Encoding` not returned, so bodies pass uncompressed [read] | `proxy.py:54-77, 408-428` | none recorded |
| 7 | §4.3.1, §6, decision B: the fetch-failure line says deep-reasoning "is private: ask Michael for read access…" | "✗ Could not fetch github.com/michaeltheologitis/deep-reasoning: check that this computer is online, then restart. Nothing was installed." [read; run: `test_bootstrap.py`] | `desktop/bootstrap.sh:14` | deep-reasoning is public (`3c923aa`) |
| 8 | §3 item 2: users need read access to both repositories. §2.2: "Releases are assets of a private GitHub repository". §7.5: CI reads deep-reasoning through an `insteadOf` line | deep-reasoning is public [run: `gh api`]: only deep_reasoner_beta needs read access, release assets are public downloads, and no workflow adds an `insteadOf` for deep-reasoning (the one for DeanLight stays) [read] | `.github/workflows/` | Michael: "public downloads are fine" |
| 9 | §1.3 (D5 owns "the README's install section"), §2.3, §3 item 12, §4.2.6 (`xattr -dr com.apple.quarantine …`), §4.8.3 (uninstall) | **No README exists** at `3c923aa`; the only one is `docs/research/…/README.md` [run: `git ls-tree`]. The macOS quarantine command, the uninstall steps, the `PATH` hint and §2.2 in short are written nowhere a user reads | — | none recorded |
| 10 | §7.5: four jobs, `pins`, `desktop-e2e`, `bridge-replay`, `canvas-replay` | **Six.** `has-d5` first: the others run only when `desktop/pins.toml` exists, so `main`'s copy skips instead of failing. `library-app` runs §7.2's `crossrepo` test of the staged App as a job of its own. D4's forwarding test runs inside `bridge-replay` (§8.7 said "beside"). `desktop-release.yml` also starts with `has-d5` [read; CI] | `.github/workflows/cross-repo.yml` | `57c019d` |
| 11 | Decision M: `main` carries copies of the on-demand workflows | `main`'s copies (`f1ca641`) are older than `v1-desktop`'s. Its `desktop-release.yml` builds `mac-universal`, which `build.py` at `3c923aa` rejects, and adds the deep-reasoning `insteadOf`; its `cross-repo.yml` has only `has-d5`, `library-app` and `bridge-replay`. No run uses them while `main` lacks D5's code: there `has-d5` skips every job. Dispatched runs, and the nightly (`--ref v1-desktop`), use `v1-desktop`'s files, and a tag the tagged commit's [run: `git diff`; read] | `main`'s `.github/workflows/` | #34 and #35 placed them before the later commits |
| 12 | §7.5's seven steps and the final flow | **17 tests sharing one launch** (§5.2). Where they differ: the first conversation is onboarding's hello, not a dismissed onboarding; two tests the design does not list check that no consent dialog shows (a fixed 5 s wait) and that no consent is recorded and Settings has no analytics switch; the Library config is written by the test (there is no `e12/main.yaml`); Stop's plan spawns the done sibling first and holds the grandchild's model call until `dr-acp` logs `stop.accepted`; costs are compared with each sub-agent's cost in the run log at its end; the next conversation asks a plain question after the slash menu offers the command (the design asks for the offer and the recorded version, which hold); the cookie is read with `Storage.getCookies`; the MCP server is added through `POST /api/settings/mcp/echo` and the Tools tab reopened; the quit test asks that no process's command line names the fresh HOME [read; CI] | `tests/desktop/test_e12.py` | `c538fb3`, `1a90887`, `d39be70`, `8ce99b2`; Canvas `dr-3` (§1.2); TASK-38 |
| 13 | §7.6: the macOS job launches the app once and waits for `backend ready` | One launch, two tests: `app_ready(…, "installed")` in the log, the backend `ready`, the app quits with 0; and, on macOS, `lipo -archs` of the launched executable and of the bundled uv is `arm64` [read; CI] | `tests/desktop/test_launch_smoke.py` | `bd6e170` |
| 14 | §4.2.2's checks; §5.8 | Check 2 gives two sentences (the wired repository, the wired commit). Check 5 looks at `paths.stateDir` and `setup.command`, not all of `setup` (the fork sets `setup.phases`). Check 8 clones the fork's `deep-reasoning` branch bare and blobless and asks `git merge-base --is-ancestor <commit> refs/heads/deep-reasoning`, not `FETCH_HEAD` (see §1.3 #1). `build()` copies the artifacts to `<repo>/dist/` [read] | `build.py:222-288, 326-357, 522-527` | none recorded |
| 15 | §5.2 puts `SetupError` in `dr_app.runtime`; §6's table | `SetupError` lives in `dr_app.layout` and `runtime` re-exports it. Three sentences §6 lacks: `NO_AGENT_SERVER` (after-ready without the launcher's variables, exit 2), `home_refused` (`dr-app home` with a relative path or a network filesystem), `home_too_long` (#4) [read] | `layout.py:33-40`; `texts.py:31-34, 97-118` | none recorded |
| 16 | §8.7: an MCP server's environment holds "only its configured variables and `mcp`'s six" | The test also admits `LC_CTYPE`, which D4's stdio guard, a Python, adds when it coerces a C locale (PEP 538). It runs twice, with and without the model key named in the server's settings [read; run] | `tests/acp/test_e10_keys.py:220-288` | in the test's comment |
| 17 | §10: ≈1.45k lines of code, ≈1.24k of tests | **≈3.1k and ≈4.4k.** Code: 2,995 lines in D5's own files (428 of them workflows) and +133 net in D1's. Tests: 4,311 in D5's own files and +115 net in D1's and D3's. Largest: `test_e12.py` 727, `proxy.py` 703, `test_key_proxy.py` 657, `build.py` 552 [run: `wc -l`, `git diff --numstat`] | — | none recorded; §4 says where it went |

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

### 1.3 Behaviour the design does not state

1. **Check 8 on a reused `--work`.** `fork_cache` refetches with `git fetch --filter=blob:none origin deep-reasoning`
   into a bare clone that has no fetch refspec, so the fetch moves only `FETCH_HEAD`, and `refs/heads/deep-reasoning`
   stays as first cloned [run: §5.4's probe]. With the default `--work`, `<repo>/.desktop-work`, which persists, a pin
   to a commit merged into a fork's branch after the first local check is refused as "not on its deep-reasoning
   branch". CI starts each job with a fresh `--work`, so no CI run is affected. Not fixed (my brief).
2. **The default suite needs the network.** `test_the_runtime_lock_installs_on_every_platform_the_app_ships_for`
   (two cases: Linux x86-64, macOS 14 arm64) dry-runs the lock against PyPI's metadata, and carries no marker [read;
   run].
3. **Two default-suite tests restate the committed pins:** `test_the_committed_sdk_pin_is_34c540c_tagged_dr_2` (and
   `uv_version`) and `test_the_committed_pins_load` (both forks). A pin bump edits them [read].
4. **A `setup.json` whose `v` is not 1** raises `ValueError`, which `main()` does not catch: a traceback and exit 1,
   below the 10–19 band in which the bootstrap trusts `dr-app` to have explained itself, so the bootstrap also
   checks deep-reasoning's readability [read].
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
verbatim [run: each compared with the code]; the bootstrap's and the new ones are §1.1 #7 and #15. The wrapper config
is §4.2.4's byte for byte, and the bootstrap §4.3.1's but for its fetch line [run: `diff`]. Every test the design's
§7 names exists, but for two of the bootstrap's, renamed with §1.1 #7 [run].

---

## 2 · What exists

| Part | Files | Lines |
|---|---|---|
| The build | `desktop/build.py`, `pins.toml`, `bootstrap.sh`, `electron-builder.dr.mjs` | 610 |
| Setup | `packages/dr-app/` (`cli`, `layout`, `runtime`, `agent_server`, `profile`, `canvas_app`, `texts`; `runtime.lock.txt`) | 1,254 + a 176-line lock |
| The key proxy | `src/deep_reasoning/acp/proxy.py`, with `dr-acp`'s two options and the tool-client seam in D1's files | 703 + 133 net |
| CI | `cross-repo.yml`, `desktop-release.yml`, `nightly.yml` (on `main` only) | 428 |
| Tests | `tests/app/`, `tests/desktop/` (E12, the smoke), `tests/crossrepo/`, `tests/acp/test_key_proxy.py`, `test_e10_keys.py` | 4,311 + 115 net |

A build and a launch, as the code runs them [read; CI]:

```text
uv run desktop/build.py linux | mac-arm64            (on that machine only)
  pins.toml ─ check_pins, 8 checks ─ Canvas fork 4355a36 under --work
  defaults.json += paths.stateDir, setup.command (sh -c bootstrap … <commit>), setup.phases, telemetry key ""
  npm ci · VITE_DO_NOT_TRACK=1 npm run build:app · uv 0.12.23 and Node downloaded · electron-builder --config wrapper
  verify: the expected artifacts, no "deep_reasoner" in any payload path, arm64-only Mach-O ─ dist/

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

with the repository URL a constant (`DEEP_REASONING`) and the commit the checkout's `HEAD`. `pins.toml` holds the two forks' repositories, commits and tags
and the `[app]` values; deep_reasoner's pin is a line of `runtime.lock.txt` [read].

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

- **The build:** `tests/desktop/test_build.py`, 20 tests: each check's refusal, the defaults, the setup command, a
  `.deb` listing with spaces, the arm64 checks, the per-machine targets, the committed pins.
- **Setup:** `tests/app/`, 56 tests, against stub `uv`, `uvx` and `git` scripts and `fake_agent_server.py`, an
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
  needs; 13 the data home is unusable, too long, or nothing is installed for `export`; 2 usage, or after-ready without
  `AGENT_SERVER_URL` and `SESSION_API_KEY`. The bootstrap exits 10 without git and otherwise passes `uvx`'s status on.
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

### 5.1 The runs at `3c923aa`

| Workflow | Run | Result [CI] |
|---|---|---|
| `ci.yml` (push) | [37240441891](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37240441891) | `test`: ruff over `src tests packages desktop` clean; 833 passed, 115 deselected in 612 s. `canvas-app`: green |
| `cross-repo.yml` (dispatch) | [37240441432](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37240441432), attempt 2 | All six green. Attempt 1 failed only `canvas-replay`; attempt 2 re-ran that job alone |
| `desktop-release.yml` (dispatch) | [37240443237](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37240443237) | `linux`, `macos` green; `cross-repo-green` and `release` skipped (no tag) |
| `fork-live.yml` (dispatch, `sdk_ref` `dr-2`) | [37241495293](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37241495293) | S1 2 of 2, S2 8 of 8, on gpt-6-luna |

### 5.2 Each experiment

**pins** [CI]: "the pins belong together ✓" (all eight checks, real forks). The same check passes here in 5.9 s
[run].

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

**E12, the installed Linux app** (`desktop-e2e`, attempt 1 of 37240441432, `ubuntu-24.04`; reproduce: the job's steps)
[CI]: the build took 3 min 51 s (`.deb` 150 MB); **17 passed in 428.7 s**. The first launch, from a cold uv cache
under a fresh HOME through both setup phases to the window, passed 37 s after collection. The header-panel test, which
waits past the bridge's first session, took 320.5 s, most of E12's time. Proven inside the real app: the worker's
environment holds neither the key nor the session or secret key, and no stored file does; D3's frame works through the
bridge with a partitioned `Secure; SameSite=None` cookie whose partition is `http://localhost`, and is refused 401
after the session is deleted; C1's tree equals the run log's (3 sub-agents, 1 nested), costs match, and Stop stops a
child and its branch while its done sibling stays done; C2's picker, slash menu, header panel and Create
decomposition; D4's MCP server is bound and called; the app quits within 6 s; setup relaunches with the network cut
in under 5 s and installs nothing.

**E5's second half, `bridge-replay`** (`tests/crossrepo/`, SDK fork `34c540c`; reproduce: `DR_SDK_CHECKOUT=<checkout>
uv run pytest -m crossrepo tests/crossrepo`) [CI]: **11 passed in 34.8 s**: each of D1's ten native recordings is
stored by the agent-server as the tree it records, and D4's forwarding test passes. `library-app`: 1 passed in 13.7 s
(the staged App passes `prepare` and its backend answers `/health`).

**E6, `canvas-replay`** (C1's replay spec at Canvas `4355a36`) [CI]: attempt 2, **10 of 10**. Attempt 1 failed on
`fanout20.native.jsonl`: two rows (`n16`, `n17`) rendered with no tool calls yet, so the spec's one read differed
from the stored tree; five passed and four were skipped after it. TASK-40 records the race (two of the last ten runs
failed once; each passed again).

**The launch smoke** (`macos` of 37240443237, `macos-26-arm64` runner image) [CI]: the `.dmg` built in 3 min 21 s;
**2 passed in 54.2 s**: the backend ready after the first launch, the app quit with 0, and the launched executable
and its uv are arm64 only. Artifacts as uploaded (zip): macOS 178,483,286 B, Linux 345,945,959 B.

**The live tier** (`fork-live.yml`, `dr-acp` from `3c923aa` with the key proxy on, as no flag turns it off) [CI]:
S1's `test_live_agent_tree_is_well_formed` and `test_live_agent_stops_one_subagent_and_its_branch`, 2 passed in
38.4 s; S2's file, 8 passed in 103.7 s. The model was gpt-6-luna; I did not re-run it.

### 5.3 Earlier runs, for history [CI]

- `desktop-release` 37226929314 (`9ca1f70`): `macos` red. The launch smoke waited its limit on a keychain dialog
  under the fresh HOME (§1.3 #5); fixed in the test by `269c7af`, and failures made readable by `ae363b4`.
- `cross-repo` 37230954884 (`d39be70`), 37236303764 (`8ce99b2`), 37238261156 (`a4a9336`): all six jobs green.
- `desktop-release` 37231871112 (`d39be70`): green, with the universal `.dmg` of that time.
- `desktop-release` 37238259690 (`a4a9336`): `macos-intel` red, the job since dropped (§1.1 #1).

### 5.4 Run here, at `3c923aa`

- **The default suite** (`uv run pytest`, Python 3.12.15, no `DR_BETA_CHECKOUT`): 696 passed, 4 failed, 5 skipped,
  115 deselected, in 7 min 25 s. D5's own files and the D1 and D3 files it edits: **164 passed**, 1 skipped (D1's
  catalog test that needs `DR_BETA_CHECKOUT`), in 88 s. The four failures are D1's golden recordings `failing` and
  `unanswered`, both modes, which embed CPython's stdlib line numbers in a traceback (`asyncio/runners.py`, line 194,
  from CI's 3.12.3); this machine's 3.12.15 numbers them otherwise. They pass in CI, and D5 does not touch them. The
  smaller total than CI's 833 is the D2 corpus tests that `DR_BETA_CHECKOUT` parametrizes.
- **`build.py check`**: "the pins belong together ✓", 5.9 s, against the real forks, with `--work` in a scratch
  directory (removed).
- **Setup, for real, with uv 0.12.23** (a probe; removed). The bootstrap exactly as the launcher runs it, under a HOME
  in my scratch directory: `uvx` fetched and built `dr-app` from GitHub at `3c923aa` and `dr-app` refused the home,
  exit 13, `home_too_long` ("up to 146 bytes long, and this system allows 107"), passed through without the bootstrap's
  fetch line; 3.3 s cold, 0.12 s warm, 0.12 s again inside `unshare --map-root-user -n` (no network). Then
  before-start itself, with the socket limit patched out for that long HOME: a first install from a cold uv cache, the
  managed CPython 3.12.15 download included, printed `installed in 11s` (12.0 s in all; 173 packages). The runtime is
  473 MB, and the whole HOME 649 MB with uv's cache and the managed Python; the runtime's entry points start with
  `#!/bin/sh`, uv's relocatable form (§1.1 #3). A relaunch's before-start took 0.019–0.020 s (three runs).
- **macOS's minimum:** a wheels-only dry run of the lock's registry packages for `aarch64-apple-darwin`, Python
  3.12, uv 0.8.17: with `MACOSX_DEPLOYMENT_TARGET=13.0`, "onnxruntime==1.30.0 has no wheels with a matching platform
  tag (e.g., `macosx_13_0_arm64`)"; with 14.0, 170 packages resolve.
- **Check 8's cache:** a bare, blobless, single-branch clone of a local repository, a new commit on the source
  branch, then `git fetch --filter=blob:none origin deep-reasoning`: `FETCH_HEAD` moves, `refs/heads/deep-reasoning`
  does not, and `merge-base --is-ancestor <new> refs/heads/deep-reasoning` exits 1; the clone has no
  `remote.origin.fetch`.

### 5.5 What the design's §11 asked to be measured

- **Item 5, `uvx`'s start for `dr-app` on a relaunch:** 0.12 s warm, with or without a network, for `sh`, `uvx` and
  `dr-app` up to its home check; the cheap path after it, 0.02 s [run, §5.4]. E12 asserts the whole offline relaunch
  of before-start finishes in under 5 s [CI].
- **Item 5, the first install's time and disk use:** 11 s and 473 MB of runtime (649 MB with uv's cache and Python)
  here [run]; E12's whole first launch, both phases and the agent-server's own install, under 37 s on GitHub's
  runner [CI]. The design's mock-up figure of two minutes was not reached on either machine; a user's network sets it.
- **Item 5, the after-ready cost of starting the backend:** not measured separately. The launch smoke's first launch
  through after-ready, on macOS, fits in its 54.2 s, which includes the `.app`'s copy and the quit [CI].
- **Item 4, macOS on hardware:** the launch smoke ran on GitHub's `macos-26-arm64` image; nothing ran on macOS 14.
  The system-proxy handling (§4.7.2 step 5) has unit tests only.
- **Item 11, the cookie in Electron's Chromium:** holds (E12, §5.2). **Item 12, the `.mjs` wrapper config:** builds
  on both platforms. **Item 15, uv 0.12.23 for D5's own commands:** E12 and the smoke run them with the bundled uv
  0.12.23, and so did §5.4.

---

## 6 · Open items for Gate B

1. **The macOS minimum is not enforced** (§1.1 #2). One line in `desktop/electron-builder.dr.mjs`'s `mac` block,
   `minimumSystemVersion: "14.0"`, would make macOS refuse to open the app on an older system, instead of setup failing
   at `uv pip sync` with exit 11.
2. **There is no README** (§1.1 #9). The design's install section, including the macOS command to clear the quarantine
   flag on an unsigned app (§4.2.6) and how to uninstall (§4.8.3), does not exist. Gate B's own install has no
   written steps.
3. **TASK-39:** the splash says nothing while setup waits (on a credential prompt, or a slow first install).
4. **TASK-38:** E12's Stop saw a sibling spawned in the same `run_all` still running when Stop was pressed; whether
   that is the fake holding a call or real serialisation in D1 is open. E12 now spawns the done sibling first.
5. **TASK-40:** C1's replay spec reads the DOM once and fails about one nightly run in five; the fix is in the Canvas
   fork.
6. **Check 8 on a reused `--work`** (§1.3 #1): local `build.py` runs can refuse a valid pin; CI cannot.
7. **`main`'s workflow copies are behind `v1-desktop`'s** (§1.1 #11). Nothing runs them while `main` lacks D5's code;
   D5's PR stack replaces them.

## 7 · What I could not verify

- **Nothing ran on a Mac here.** Every macOS claim is [CI] (one runner image, macOS 26) or [read]: the arm64 checks,
  the Finder `PATH`, the system-proxy export, the quarantine flow.
- **I did not install or launch the app.** E12, the smoke and the cross-repo jobs are [CI]: I read their logs and did
  not re-run them. E12's assertions are as §5.2 states them, read from the test and its passing log.
- **The live tier** made model calls; I read its log and did not re-run it. That `dr-acp` there ran with the proxy is
  [read]: `fork-live.yml` passes no `--no-key-proxy`, and the proxy is on by default.
- **The after-ready phase against a real agent-server** (the profile, the App's install, `prepare` and `start`) is
  [CI] (E12, `library-app`, the smoke) and [run] only against `tests/app/fake_agent_server.py`.
- **The `.dmg`'s `Info.plist`** (what `LSMinimumSystemVersion` the packaged app declares): not read; §1.1 #2 rests on
  the configs.
- **TASK-38's cause**, and the Claude CLI behind the proxy (design §11 item 3): untested by D5's suite.
- **The design's §4.2.5** (strings that stay upstream's in the app): not checked.
