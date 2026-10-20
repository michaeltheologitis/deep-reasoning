# TASK-66 · As built: the launcher's uvx starts, pinned to a PyPI time and offline from uv's cache

**TASK-66** · Cartographer · 2026-10-19 · branch `as-built/task-66`, cut from `main` `9e8109e`. The build is in
two places: the Canvas fork's `feat/uv-exclude-newer` at `1a6a28f` (5 commits on `dr-3` `4355a36`,
+1288/−174), and deep-reasoning's `ux-round` commits `c361467` and `b0fff97` (+308/−41; the branch head is
`b283be2`). It is checked against one document: the design, `docs/design/task-66-uv-pins.md` on
`design/task-66` at `1109837` (v1, its only revision). There is no spec.

**Evidence.** Every claim carries a mark. **[run]**: I ran it on this machine at the commits above; nothing
called a model. **[CI]**: a named run shows it; I opened its log. **[read]**: I read it in the code and did not
run it. The scripts behind the [run] marks are not committed.

**Reading guide.** §0 is the five-minute read. §3 lists every divergence from the design, and §4 the measured
results. §1–§2 are the map of the code.

---

## 0 · What Michael gets, and what changed against what he approved

**What he approved** (2026-10-19, in chat, no spec): "the Canvas launcher pins its PyPI dependencies to a date
and runs offline from the cache; fixes the app's offline relaunch after ten minutes; rides Canvas dr-4", then
"go with your recommendations" for the design.

**What he gets.**

- The app's agent-server and automation backend resolve their PyPI dependencies as PyPI was at
  **`2026-10-04T00:00:00Z`**: `desktop/pins.toml` `[app] uv_exclude_newer`, which the build writes into Canvas's
  `config/defaults.json` as `uv.excludeNewer` [run: build tests]. Every `uvx` the launcher runs gets
  `--exclude-newer <it>` first [run].
- A relaunch starts both services from uv's cache with `--offline` once an online start of the same requirement
  set has answered, however long since uv last asked PyPI. In E12 the installed app, relaunched inside a network
  cut with uv's index answers aged an hour, had its agent-server ready in 5.0, 6.0 and 8.0 s in three runs, and
  installed nothing [CI].
- The splash and log say so. The source line gains `, PyPI as of 2026-10-04T00:00:00Z`, and a start from the
  cache adds `[agent-server] Starting from uv's cache, offline` and `[automation] Starting from uv's cache,
  offline` [run]. A cutoff that is not a UTC time to the second fails the launch, naming the key [run].
- The README says a later launch "needs no network, however long since the last one", and that an index
  without upload times cannot install (design §4.3, verbatim) [read].
- With the key `null`, the fork's default, every command is upstream's, byte for byte [run].

**Against what he approved.** The design changed four things, all in its §2 and approved with it. The cutoff is
a UTC time to the second, not a date: uv reads a date in the user's own time zone. A pinned start runs from the
cache whenever it can, not only when offline. The pin also stops dependencies changing on later launches, not
only at first install. Three checks were added: E12 asks the automation backend, the fork's mock-LLM workflow
takes a cutoff, and `canvas-replay` runs at the cutoff.

**Against the design, the behaviour in the app is as designed.** The divergences (§3) are two sentences, the
tests, the docs and the size:

1. A dev-only automation source line names no cutoff.
2. Check 5c's refusal uses the shared sentence, not the design's own.
3. There are more tests than the design listed.
4. The build is about 2.3 times the size design §8 estimated, mostly in tests. Not reported by the Implementer.
5. `npm run dev:static`, a third launcher the design does not name, gets the cutoff and starts online. Not
   reported by the Implementer.

**Proof.** The fork's live test passed 2/2 on uv 0.13.1 and 0.8.17, including an expired-answers start with
the network cut and its negative control [CI]. deep-reasoning's cross-repo passed twice at `b283be2`, with E12
25/25 and the live tier [CI]. At the cutoff, the fork's mock-LLM suite clears 5 of the 10 failures it has
without one [CI].

**Points for Michael**, each a fact, detailed below:

- **E12's last test depends on uv's cache format.** Ageing uv's answers in place works on uv 0.8.17 and
  0.12.23, the app's uv. On uv 0.13.1, uv discards the aged answer, so `--offline` fails too [run]. If
  `pins.toml`'s `uv_version` moves to 0.13, that test fails at its negative control. The fork's live test does
  not depend on this, and passed on 0.13.1 [CI].
- **`ux-round` still pins Canvas `dr-3`**, so `build.py check` refuses it with three lines (5b twice, 5c)
  until the pin is `dr-4` [run]. The proof runs used the scratch commit `1a9e3c6` on `ux-round-integration`,
  whose TASK-66 files are identical to `1a6a28f` [run].
- **What an update reinstalls.** The README says "After an update, setup and the agent-server install once
  more". In the code, an update reinstalls a service only when it changes that service's requirement set: the
  SDK commit, the version or the cutoff. Otherwise the service starts from the cache [read].
- **The app's PyPI packages get no new releases**, security fixes included, until someone moves the cutoff
  (design K3) [read].
- **TASK-48 has two tests that assert the opposite of this task's outcome** (§5). Design §5.5 names one of them.

---

## 1 · The public surface

Copied from the code at `1a6a28f` and `b283be2`.

**Canvas fork.** `config/defaults.json` gains `"uv": {"_comment": …, "excludeNewer": null}` after `sources`.
`scripts/launcher-defaults.mjs` maps `uv.excludeNewer → OH_UV_EXCLUDE_NEWER` and exports:

```js
export function validateExcludeNewer(value, name)  // returns value, or throws
// `${name} must be a UTC time such as 2026-10-04T00:00:00Z, got: ${value}`
```

`buildAgentServerCommand(env)` (`dev-safe.mjs`) and `buildAutomationCommand(env)` (`dev-with-automation.mjs`)
return a `UvxCommand` `{ command, args, source, requirementArgs }`. `requirementArgs` holds the args before the
executable, or `null`. The new `scripts/uvx-start.mjs` (189 lines, Node built-ins only):

```js
export const RECORDS_DIR = "uvx-starts";
export const PROBE_TIMEOUT_MS = 120_000;
export const RECORD_DEADLINE_MS = 15 * 60_000;
export const STARTING_OFFLINE = "Starting from uv's cache, offline";
export function recordPath(stateDir, requirementArgs)              // <stateDir>/uvx-starts/<sha256 hex>
export function probeUvCache(requirementArgs, { env, cwd, timeoutMs = PROBE_TIMEOUT_MS })  // exit code | null
export async function planUvxStart(cmd, { stateDir, env, cwd, probe = probeUvCache })     // UvxStart
export function recordUvxStart(stateDir, requirementArgs, now = new Date())              // boolean
export async function recordOnceServing(stateDir, requirementArgs, url, proc,
  { intervalMs = 1000, deadlineMs = RECORD_DEADLINE_MS, fetchImpl = fetch } = {})          // boolean
```

`mock-llm-e2e.yml` gains the dispatch input `uv_exclude_newer` (default `""`), exported to the job as
`OH_UV_EXCLUDE_NEWER`.

**deep-reasoning.** `desktop/pins.toml` `[app] uv_exclude_newer = "2026-10-04T00:00:00Z"`. `desktop/build.py`:
`AppPin.uv_exclude_newer`, `is_utc_time(value)`, `load_pins` refusing a bad value, `"uv.excludeNewer"` in
`FORK_NULL_KEYS`, and a required `exclude_newer=` keyword on `patch_defaults`, which `build()` fills from the
pin. `tests/desktop/app.py`: `NETWORK_CUT`, `ANSWER_TAIL_BYTES`, `LaunchedApp.started_at`,
`launch(home, log, *, network=True)` and `age_uv_index_answers(cache, since, seconds) -> int`.

**Sentences** [run]:

| Where | Sentence |
|---|---|
| source line | `[agent-server] Using git (<owner>/<repo>@<commit>), PyPI as of 2026-10-04T00:00:00Z`; `[automation] Using PyPI (1.16.0, default), PyPI as of 2026-10-04T00:00:00Z` |
| a start from the cache | `[agent-server] Starting from uv's cache, offline`, and the same for `[automation]` |
| a bad value, launch | `uv.excludeNewer in config/defaults.json must be a UTC time such as 2026-10-04T00:00:00Z, got: 2026-10-04` (or `OH_UV_EXCLUDE_NEWER must be …`) |
| a bad value, build | `<path>: app.uv_exclude_newer must be a UTC time such as 2026-10-04T00:00:00Z, not '2026-10-04'` |
| check 5c | `✗ Canvas fork dr-3's config/defaults.json has no uv.excludeNewer, so this build cannot set it: pin dr-4 or later.` |

---

## 2 · The map: one value from `pins.toml` to a start from the cache

**The cutoff's path.** `load_pins` checks the value: the regex, then `datetime.fromisoformat`. `build()` passes it
to `patch_defaults`, which writes `uv.excludeNewer` into the packaged `defaults.json` [run]. At launch,
`dev-with-automation.mjs`'s `main()` calls `applyLauncherDefaults`, which fills `process.env.OH_UV_EXCLUDE_NEWER`
when the environment leaves it unset or empty. It logs `[defaults] From config/defaults.json: …` [run]. The
builders read only the `env` they are given; they validate the value and put `--exclude-newer <it>` first
[run]. The Python and JS checks agree on every value I tried, including 24:00:00, a leap second, 29 February
2026, lower-case `z` and a trailing newline. The one difference is year `0000`, which only JS accepts [run].

**Which commands may start from the cache** [run]. `requirementArgs` is non-null only for a fixed source:

| Command | `--exclude-newer` | `requirementArgs` |
|---|---|---|
| agent-server: PyPI default, `OH_AGENT_SERVER_VERSION`, a 40-hex `OH_AGENT_SERVER_GIT_REF` | yes | args before `agent-server` |
| agent-server: a branch, tag or short SHA (`--reinstall`), `OH_AGENT_SERVER_LOCAL_PATH` | yes | `null` |
| automation: default, `OH_AUTOMATION_VERSION` | yes | args before `uvicorn` |
| automation: `OH_AUTOMATION_GIT_REF` (`--refresh`) | yes | `null` |
| automation: `OH_AUTOMATION_LOCAL_PATH` (`uv run --project`) | no | `null` |

**The gate, the one place with real logic** (`planUvxStart`, 20 lines) [run with a stub, CI live]:

- A command with `requirementArgs: null` starts as built, and nothing is probed.
- If the record file exists **and** `uvx --offline <requirementArgs> python -c pass` exits 0 in the service's own
  env and cwd, the command starts with `--offline` first.
- Otherwise it starts as built, online, with `recordOnceServing`.

The probe runs in its own process group. Past 120 s it counts as "not cached" and its process tree is killed.
The record key hashes the requirement args, cutoff included. So a moved cutoff, SDK commit or automation
version has no record yet, and its first start is online.

**The starters** (`startAgentServer`, `startAutomationBackend`) are now `async`, and `main()` awaits both [read].
Each one logs its `Using …` line, then plans the start. A quit during the probe returns a promise that never
settles, as the setup phase already does, and `shutdown()` exits the process [read]. Then each spawns the
service. An online start of a pinned command then calls `recordOnceServing`, not awaited. It polls
`<agent-server>/server_info` or `http://127.0.0.1:<autoBackendPort>/health` every second, for up to 15
minutes. On the first 2xx it writes `{"requirementArgs": [...], "servedAt": "<ISO>"}`. If the process exits
first, nothing is written [run]. Most of `dev-with-automation.mjs`'s +160/−90 is the automation's env block,
moved out of the `spawnService` call into a variable so that the probe gets the same env (+97/−27 ignoring
whitespace) [run].

**Records** live in `<state dir>/uvx-starts/`, one small file per requirement set. The app's state dir is
`~/.deep-reasoning/canvas/agent-canvas`. Nothing deletes a record. A record that cannot be written means only
that the next start is online [run].

**Other launchers.** `dev-safe.mjs`, `dev-extra-backend.mjs` and `dev-static.mjs` call the same builders. With
the variable set, they get `--exclude-newer` and start online, and never probe or record [read].
`OH_UV_EXCLUDE_NEWER` also reaches the agent-server's environment, and so its conversations' terminals, as a
string no uv reads [read].

---

## 3 · Divergences from the design

| # | Design | Built | Why | Reported |
|---|---|---|---|---|
| 1 | §3.3: the source line gains `, PyPI as of <cutoff>` whenever the cutoff is set | The automation's local-checkout source line, `local (<path>)`, gets none [run] | Its `uv run` takes no flag (as §3.3's table says), so the line names no cutoff | yes |
| 2 | §3.7: DEVELOPMENT.md and one line of the local-stack guide | Also two claims that a full commit "relaunches offline" are qualified ("offline too when `uv.excludeNewer` is set"), in `sources._comment` and the local-stack guide's line 96. The guide gains a whole bullet on the mechanism, ending "Pass the cutoff as flags only" [read] | The old claims are true only with the key set | the qualifications yes; the bullet's length no |
| 3 | — | The e2e-testing guide gains a sentence on the `specs` and `uv_exclude_newer` dispatch inputs [read] | It documents the workflow | yes |
| 4 | §5.1's list of tests | Added: two packaged-launch tests (first launch online with the cutoff; relaunch offline, with the probe's argv), the empty-variable case, `recordOnceServing`'s deadline case, a "without it, upstream's command" case per source, and `launcher-live.yml` now requiring 2 passes. In deep-reasoning, `test_the_cutoff_the_build_writes_is_the_pinned_one`. The probe test's fake `uvx` is a `/bin/sh` script, not a Node script [run] | Coverage the design did not list | the fork's yes; the rest no |
| 5 | §5.1: "a read-only state dir" | A file where the state dir would be [run] | The sandbox runs as root, which can write a read-only directory | yes |
| 6 | §5.2: a second live case | Case 1 is refactored into shared helpers (`prepareRelaunch`, `skipUnlessTheNetworkCanBeCut`, `pinnedCommit`); its assertions are unchanged [read] | Both cases share the setup | yes |
| 7 | §4.1–4.2: check 5c with its own sentence, `fork_lacks_cutoff`; new test `test_a_canvas_fork_that_cannot_pin_pypi_is_refused` | 5c is the `FORK_NULL_KEYS` loop shared with 5b, using `fork_lacks_setting`'s sentence (§1). The test is the `[uv.excludeNewer]` case of `test_a_canvas_fork_that_lacks_a_setting_the_build_writes_is_refused`, which now drops the whole block for all three keys [run] | The Conductor asked for 5c through `FORK_NULL_KEYS` | yes |
| 8 | §9.2: the ageing is measured on 0.8.17 and 0.12.23, and "a uv bump that changes the layout fails loudly" | On uv 0.13.1 the helper ages the answer and raises nothing, but uv then discards the answer, so `--offline` fails as well (§4.4) [run]. E12 would fail loudly at its negative control, not in the helper | uv 0.13.1's answers hold three time-like u64s, at 140, 76 and 28 bytes from the end; the helper moves all three | yes (as "breaks on 0.13.1") |
| 9 | K4 names `dev-safe.mjs` and `dev-extra-backend.mjs` as the launchers that get the cutoff and start online | `dev-static.mjs` (`npm run dev:static`) also calls both builders, so it gets the cutoff and starts online too. No test covers it [read] | The file is unchanged; the builders carry the flag | **no** |
| 10 | §8: ≈220 production lines and ≈495 test lines, ≈0.7k in all | Fork: +431/−94 production, +831/−69 tests, +26/−11 docs and workflows. deep-reasoning: +54/−10 production, +254/−31 tests. ≈1.6k in all, mostly tests [run] | — | **no** |

`patch_defaults`' docstring, the README paragraphs (§4.3) and the `mock-llm-e2e.yml` input are as the design
wrote them [read]. The design's test name `…_six_keys` is `test_defaults_gain_only_the_keys_the_build_writes`,
the UX round's name, and it now covers seven keys [run].

---

## 4 · Measured results

### 4.1 The fork's live test (`launcher-live.yml`, a real agent-server install from the SDK pin `34c540c`)

| Run | Commit | uv | Case 1: install, then a relaunch with the network cut | Case 2: cutoff, answers expired (`max-age=1` index), cut |
|---|---|---|---|---|
| 39210878513 | `1a6a28f` | 0.13.1 (latest) | passed, 29.4 s | passed, 42.4 s |
| 39210881164 | `1a6a28f` | 0.8.17 | passed, 28.3 s | passed, 29.7 s |

In case 2, the command as built fails with the network cut (a non-zero exit, not a timeout): this is the
negative control. The plan's `--offline` command answers `/server_info` [CI]. Reproduce with
`gh workflow run launcher-live.yml --ref feat/uv-exclude-newer [-f uv_version=0.8.17]`.

### 4.2 The fork's mock-LLM suite (85 tests): at the cutoff against no cutoff

| Run | Commit | Cutoff | Result |
|---|---|---|---|
| 39210161845 | `c5ba6ee` | `2026-10-04T00:00:00Z` | 6 failed |
| 39212570324 | `1a6a28f` | `2026-10-04T00:00:00Z`, `specs`: the 2 specs that failed only here | 7 passed, 1 failed, 1 did not run |
| 39213707405 (control) | `1a6a28f` | none | 10 failed |

Per test [CI]:

- **Fail both ways (5):** automation lifecycle step 2; image upload; onboarding happy path; same-model profile
  identity; conversation step 3 (seen at the cutoff on the rerun).
- **Fail only without the cutoff (5):** the preset automation's slash command; both message-confirmation
  tests; files-and-git step 2; `/model` switch step 2.
- **Failed at the cutoff, then passed on the rerun at the cutoff (2):** App header panels; conversation step 1.

Design §9.1 expected four of the ten failures to be drift; five clear. Reproduce with
`gh workflow run mock-llm-e2e.yml --ref feat/uv-exclude-newer -f uv_exclude_newer=2026-10-04T00:00:00Z`.

### 4.3 deep-reasoning: cross-repo at `b283be2`, Canvas commit `1a9e3c6`

| Run | Jobs | E12 | Offline relaunch: agent-server ready | canvas-replay | Live tier |
|---|---|---|---|---|---|
| 39220656317 | 4/4 green | 25/25, 443.6 s | 5.0 s | 12 passed | not dispatched |
| 39221995995 | 4/4 green | 25/25, 456.9 s | 6.0 s | 12 passed | 1 passed |
| 39218978270 (`b0fff97`) | red | 24/25 | 8.0 s | — | — |

In 39218978270 the TASK-66 test passed; the one failure was the UX round's window-title step, which `b283be2`
moves [CI]. canvas-replay ran with `OH_UV_EXCLUDE_NEWER=2026-10-04T00:00:00Z` in its env, and with the venv
and pre-warm at the cutoff [CI]. `ci` 39220648479 at `b283be2` is green [CI]. E12 ran Electron inside the
cut on GitHub's runner, which design §9.3 had measured only as `nobody` [CI]. Reproduce with
`gh workflow run cross-repo.yml --ref ux-round -f canvas_commit=1a9e3c6f7f8823cbdc8c123299951c1d0172d695
[-f live=true]`.

### 4.4 My runs (no model, no paid call)

- The four touched vitest files at `1a6a28f`: 251/251, every TASK-66 case among them and both packaged-launch
  tests [run]. eslint and prettier on the touched files find nothing on TASK-66's lines [run].
- `tests/desktop/test_build.py` and `test_app.py` at `b283be2`: 59/59 [run].
- The `FORK_NULL_KEYS` loop on three Canvas `defaults.json` files [run]:
  - `dr-3`: three refusals (`agent.lockedProfile`, `branding.appTitle`, `uv.excludeNewer`);
  - `1a6a28f`: two (the UX round's keys);
  - `1a9e3c6`: none.
- `age_uv_index_answers`, at `b283be2`, on a fresh cache per uv version [run]:
  - Setup: one answer each, filled by
    `uv tool run --exclude-newer 2026-10-04T00:00:00Z --from six==1.16.0 python -c pass`.
  - The cut: `unshare -n` with the loopback up and no proxy.
  - Exit codes:

| uv | cache | fresh, cut, online-first | aged 1 h, cut, online-first | aged 1 h, cut, `--offline` |
|---|---|---|---|---|
| 0.8.17 | `simple-v17` | 0 | 2 | 0 |
| 0.12.23 | `simple-v25` | 0 | 2 | 0 |
| 0.13.1 | `simple-v26` | 0 | 2 | **1**: "six was not found in the cache"; the answer file is gone afterwards |

On 0.13.1, an unaged cache passes `--offline` (exit 0), so the failure is the ageing [run].

---

## 5 · Seams and merge order

- **Canvas.** `feat/uv-exclude-newer` merges into the fork's `deep-reasoning` branch before `dr-4`. Its only
  file shared with the UX round's branches is `config/defaults.json`, where the blocks are adjacent.
  `ux-round-integration` (`1a9e3c6`) merges all of them with TASK-66's files unchanged [run].
- **`ux-round`.** At `pins.toml`'s Canvas `dr-3`, `build.py check` refuses (§4.4) [run]. A Canvas commit that
  holds all of the round's branches, as `1a9e3c6` does, passes 5b and 5c together [run].
- **TASK-48 (`task-48-browser` `44bf931`).**
  - Its `NETWORK_CUT`, `ANSWER_TAIL_BYTES` and `age_uv_index_answers` are byte-identical to `ux-round`'s
    [run].
  - A trial merge with `ux-round` conflicts in the same nine files with or without TASK-66's commits
    [run: `git merge-tree`].
  - Its `prepare()` must then pass `exclude_newer` (design §6) [read].
  - Two of its tests go red once the Canvas pin is `dr-4` and the build writes the key. The first is
    `test_an_offline_restart_once_uvs_index_answers_have_expired` (`xfail(strict=True)`), which design §5.5
    names. The second is `test_readme.py`'s `test_no_section_promises_an_offline_restart_past_ten_minutes`,
    which requires "Within about ten minutes of the last start that had the network" and no "needs no
    network". `ux-round`'s README says "needs no network, however long since the last one". Design §6 does
    not name this test [read].

---

## 6 · What I could not verify

- The fork's full `npm test` (8447 passed), lint and both builds: these are the Implementer's local report.
  The fork's CI runs only on pull requests. I ran the four touched test files only.
- Windows and macOS: the probe and the cache start are unmeasured there, and E12 runs on Linux only [read].
- That `canvas-replay`'s stack printed `PyPI as of`. The job log shows the variable set, not the stack's
  output.
- Two launchers sharing one state directory or one uv cache at once.
- The live tier's model call, which I did not re-run.
