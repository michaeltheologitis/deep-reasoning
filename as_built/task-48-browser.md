# TASK-48 · Run in the browser on localhost — as built

**TASK-48** · Cartographer · branch `as-built/task-48`, cut from `task-48-browser` at `1d4a1e9` (11 commits on
`main` `9e8109e`, +3885 / −184) · checked against the design
[`docs/design/task-48-browser.md`](https://github.com/michaeltheologitis/deep-reasoning/blob/e670b10/docs/design/task-48-browser.md)
at `e670b10` on `design/task-48`, as re-approved on 2026-10-19 (V1, V2, F4 → TASK-66).

**Evidence.** *(run)* means the claim was executed at `1d4a1e9`: by CI in the three proof runs (`ci` 39210085647,
`cross-repo` 39210088336, `desktop-release` 39210091299), whose logs I read, or by me in this sandbox. *(read)* means
I read it in the code and did not execute it. An unmarked sentence in a paragraph takes the paragraph's mark.

**Reading guide.** §0 is five minutes. §1–§2 are the map, §3 the divergences, §4 the measurements, §5 the defects,
§6 the other branches, §7 the limits of this check. About 15 minutes in all.

---

## 0 · What Michael gets, and what changed against what he approved

**What you get.** One line in a terminal starts Deep Reasoning, and the browser talks to it at
`http://localhost:8000`:

```text
uvx --from git+https://github.com/michaeltheologitis/deep-reasoning@<release commit>#subdirectory=packages/dr-web deep-reasoning [--port N] [--no-open]
```

It is the desktop app without its window: the same Canvas build, the same setup, the same `~/.deep-reasoning`. On
CI's Linux runner, a first start from an empty HOME took **38 s**. Conversations answer, the Library panel opens in
Chromium and Firefox, Ctrl+C stops everything, a second start (or the app) is refused while one runs and changes
nothing, and a restart with the network cut serves the page in under 30 s *(run, E13 and the coexistence test)*. The
design's decisions hold: the command names a commit, not a tag (V1), and `dr-web` is standard-library only and
installs Node itself (V2).

**What is different from what you approved:**

1. **Safari has no Library panel.** WebKit does not send the bridge's partitioned cookie with the panel's frame, so
   the bridge answers 401. Everything else works in it. The README names Chrome, Edge and Firefox. E13 drives
   Playwright's Chromium, Firefox and WebKit, so Chrome and Edge are inferred from Chromium, not tested. Filed as
   TASK-70 (at `Spec`).
2. **The offline restart has a ten-minute window,** as you approved (F4 → TASK-66). E13's claim 9 is a strict
   xfail until TASK-66 lands. The README's new section says so. **D5's older sentence stays as it was** (README
   line 97: "A later launch with nothing changed installs nothing and needs no network"), so the README now
   contradicts itself on this point until TASK-66.
3. **The release path has never run.** The tag check, the release notes carrying the command, and `release-smoke`
   (the real download on Linux and macOS) all need a `v*` tag, and none exists. The first tag is their first run.
4. **It is about 1.8× the designed size in production code and 2.7× in tests:** about 1.4k production lines and
   2.5k test lines, against the designed 0.77k and 0.92k. At 300 lines an hour, Gate C reads in about 13 h rather
   than 5 h (§4.3).
5. **Two small defects** (§5): a setup that cannot even be started prints a line of the bootstrap script instead
   of the reason; a full disk while unpacking is reported as "not a tar archive". There is also one open doubt:
   `dr-app setup` run by hand can delete a runtime that a racing stack still uses.
6. **Test-only changes** (§3): claims 2, 3 and 9 check less, or check differently, than the design wrote, and
   `web-e2e` is pinned to uv 0.8.17. On a current uv (0.13.1), the Mac smoke passes.

---

## 1 · The shape

Three layers, each a separate process image, handing over by `exec` or by import *(run: §4.2's sandbox run and the
Mac smoke's log)*:

```text
uvx (builds dr-web at the commit; no dependencies, so it runs from uv's cache offline)
 └─ dr-web (Python, stdlib): fetches Node and the tarball into ~/.deep-reasoning/web/, once each, then os.execve →
     └─ node <tree>/package/bin/deep-reasoning.mjs  (= desktop/web.mjs): checks, cleans env, picks ports, then
         import ../scripts/dev-with-automation.mjs; main({...Electron's options, staticDir})   ← the fork's launcher
           └─ setup before-start (dr-app) → agent-server :18000 → after-ready → automation :18001 → static :3001 → ingress :P
```

What crosses each seam:

| Seam | Data |
|---|---|
| uvx → dr-web | `argv`, `UV` (uv's own binary), `PATH` with uvx's tool environment first |
| dr-web → web.mjs | `argv` = `[node, entry, --port N?, --no-open?]`; the user's environment with `PATH` = Node's `bin`, the user's `PATH` minus uvx's tool `bin`, then uv's folder if no `uvx` is left on it |
| web.mjs → launcher | `process.argv` = `[node, entry, --port, P]`; `process.env` cleaned in place, plus moved ports as `OH_CANVAS_SAFE_VITE_PORT` / `OH_CANVAS_SAFE_AUTOMATION_PORT` and `DO_NOT_TRACK=1`; the options object |
| launcher → web.mjs | `main()`'s promise: `{agentServerReady}`, or a rejection (`SetupCommandError` with `phase`, `reason`, `exitCode`, `signal`) |
| build → user | the tarball `deep-reasoning-web-<version>.tgz`, whose `config/defaults.json` holds the setup command naming the build's commit, which in turn pins `dr-app` and everything after it |

Where the complexity sits: `dr_web.cache` (the install, the download and the unpacking, all crash-safe) and the
tests' harness (`tests/desktop/app.py`, +405 lines), not the entry.

---

## 2 · Modules

### 2.1 `dr-web` (`packages/dr-web`, distribution `deep-reasoning-web` 0.1.0, command `deep-reasoning`)

Outside the uv workspace (`exclude`), so the runtime's `uv sync --all-packages` does not install it. It is a dev
dependency by path, so tests import it *(read)*.

- **`dr_web.cli`** holds the surface: `command_for(commit) -> str`, the only place the line is formed. It raises
  `ValueError` for anything but 40 hex. Also here: `RELEASE = "1.0.0-rc.1"` (a test holds it equal to
  `pins.toml`'s), `find_uv(env)`, `stack_path(...)` and `main(argv)`. `main` runs `find_uv` →
  `~/.deep-reasoning` made `0700` → leftovers of dead pids removed → `ensure_node` → the tarball (`--tarball`, or
  the release's, downloaded once) → `unpacked` → `execve`. Exits: 2 (argparse's own message), 22 (`NO_UV`), 23
  (anything `FetchError`) *(run: tests; §4.2)*.
- **`dr_web.cache`** holds the layout (`WebLayout`: `node-22.12.0/`, `deep-reasoning-web-<v>.tgz`,
  `tree-<16 hex of SHA-256>/package/`) and the three fetches:
  - Node: `uv pip install --python <own interpreter> --target <tmp> --require-hashes --no-deps` of
    `nodejs-wheel-binaries==22.12.0`, with the Linux x86-64 and macOS arm64 hashes. Then `npm` and `npx` are
    relinked into `lib/node_modules/npm/bin/`, and `node --version` must print `v22.12.0`.
  - The download: `urllib` through `tls_context()`, which loads a system CA bundle when the default store is
    empty.
  - The unpacking: gzip magic, every member under `package/`, tarfile's `data` filter, then `package.json`'s name
    (and version, for a download) and the entry.

  Every write goes to `<name>.tmp-<pid>` and is renamed into place. Nothing is ever pruned *(run: tests; §4.2)*.
- **`dr_web.texts`** holds §5.1's six sentences.

### 2.2 `desktop/web.mjs` (shipped as the tarball's `bin/deep-reasoning.mjs`)

It uses Node built-ins only, and runs `run()` only when it is the main module. Its exports are what the tests
import: `ELECTRON_OPTIONS`, `MINIMUM`, `REMOVED_PREFIXES`/`REMOVED_NAMES` (W8's lists, exactly as designed), `EXIT`,
`texts`, `parseCommandLine`, `cleanEnvironment`, `versionAtLeast`, `requirementProblems`, `portIsFree`, `freePort`,
`choosePorts`, `failure`, `opener` and `run`.

`run()` does the following, in order *(run: `test_web_entry.py` against a stub launcher; E13 against the real
one)*:

1. It reads `../package.json` and `../config/defaults.json`'s `ports`.
2. It parses the options.
3. It checks Node, `uv --version`, `uvx --version` and `git --version`, then prints the ready line.
4. It cleans the environment, and prints `left_out` when it removed anything.
5. It picks the ports:
   - 18000 held → exit 20;
   - the ingress port held → exit 21, with a free port to use instead;
   - 3001 and 18001 move when they are busy.
6. It sets `process.argv`, and installs an `exit` listener so that a chosen failure code outlives the launcher's
   `process.exit(0)`.
7. It calls `main()`.
8. It waits up to 60 s for `/server_info` on the ingress port, opens the browser (W15), and prints the running line.

### 2.3 `desktop/build.py` (the `web` target)

`uv run desktop/build.py {linux|mac-arm64|web}... | check`.

- `build(targets)` checks the machine for every target (`wrong_machine` returns `None` for `web`), then runs
  `prepare()` once (checkout, pins, `patch_defaults`, `npm ci`, `build:app`), then `package_desktop` or
  `package_web` for each target.
- `package_web`:
  - runs `check_web_contract` (W13: the fork's `RUNTIME_PACKAGES` is `sirv`, `httpxy`, and Electron's `main()`
    call still holds the six copied options);
  - takes the `runtime_closure` of the fork's `package-lock.json`;
  - stages the package, runs `npm pack`, then `verify_web`.

The CI tarball at `1d4a1e9` *(run: taken from the `desktop-linux` artifact and inspected)*:

- 2,762,907 bytes, SHA-256 `9ccc26f1…`, 372 members;
- `node_modules/` = `sirv`, `httpxy`, `@polka/url`, `mrmime`, `totalist`;
- the entry is byte-identical to `desktop/web.mjs`, mode 0755;
- `package.json` is §3.3's object;
- no path holds `deep_reasoner`;
- the setup command in `config/defaults.json` names `1d4a1e9`.

Unpacked, the tree is 11 MB, and the Node folder 192 MB.

### 2.4 `dr_app` (W10, and four sentences)

- `install_runtime` reads `previous = readlink(runtime/current)` before the link moves. It keeps the new commit,
  `current`, the source and `previous`, and removes the rest.
- `prune_runtimes(layout, keep)` removes everything in `runtime/` but `keep` and `current`. `before_start` calls it
  on the cheap path (`runtime_is_current`), under `setup.lock`.
- `NOTHING_INSTALLED`, `NO_AGENT_SERVER`, `state_from_a_newer_app` and `state_unusable` now name both doors.

*(run: `tests/app/test_runtime.py`, `test_texts.py`)*

### 2.5 Workflows, README, `pyproject.toml` *(read; the jobs that ran are in §4)*

- **`cross-repo.yml`.** Its paths gain `packages/dr-web/**`. `pins` runs the README's `crossrepo` check (W14).
  `desktop-e2e` builds `linux web`, and runs the coexistence test as the step after E12. The new `web-e2e` job is
  E13 on ubuntu-24.04, with uv pinned to 0.8.17.
- **`desktop-release.yml`.**
  - `cross-repo-green` (tags only) refuses a tag other than `v` + `app.version`.
  - `linux` and `macos` also build `web`. `macos` then runs `test_web_smoke.py` on its tarball.
  - `release` writes the command into the notes with `command_for($GITHUB_SHA)`.
  - The new `release-smoke` runs the released command, which downloads the asset, on ubuntu-24.04 and
    macos-latest.
- **`README.md`** gains "Run it in your browser" (before the first release, the `--tarball` form at a built
  commit) and two rows in the data table.
- **`pyproject.toml`**: the dev group gains `deep-reasoning-web` and `nodejs-wheel-binaries==22.12.0`. The `web`
  marker is deselected by default.

### 2.6 Where the promises are written

| File | Suite | Pins |
|---|---|---|
| `tests/web/test_dr_web.py` | default, 21 cases | the command and its constants, cache once, refusals leave nothing, the Node install's argv and links, `stack_path`, `execve`'s argv, TLS fallback |
| `tests/desktop/test_web_entry.py` | default, 40 cases | the entry against a stub launcher: options, environment, ports, requirements, every failure line and code, Ctrl+C, the opener, sentences verbatim |
| `tests/desktop/test_build.py` | default, +6 tests | closure, bundle, W13, `verify_web`'s refusals, targets |
| `tests/app/test_runtime.py`, `test_texts.py`, `tests/desktop/test_readme.py` | default | W10; the four sentences; the README's command, flags, links, data row (+1 `crossrepo`) |
| `tests/desktop/test_e13.py` | `web`, 12 cases | the real command on the built tarball, three browsers, FakeOpenAI |
| `tests/desktop/test_coexistence.py` | `desktop`, 2 | app beside browser, both ways |
| `tests/desktop/test_web_smoke.py` | `web`, 2 | first start to a ready backend and a clean Ctrl+C; on macOS, the Python uvx picks reaching GitHub |

`tests/desktop/app.py` is the shared harness. It holds:

- E12's helpers, moved out of E12;
- `web_command`, `launch_web`, `interrupt`, `descendants`, `listening_sockets`, `environ`, `executable`, `snapshot`
  and `mark_onboarded`;
- `web_text`/`evaluate_web`, which read `web.mjs`'s own sentences from Python;
- `NETWORK_CUT`, `LaunchedApp.started_at` and `age_uv_index_answers`, under the names TASK-66 gives them.

### 2.7 Exit codes as built

| Code | When | Evidence |
|---|---|---|
| 0 | the launcher's shutdown on SIGINT or SIGTERM | run: E13 claim 7, the Mac smoke |
| 2 | dr-web's argparse (`deep-reasoning: error: …`, e.g. `--bogus`, `--port abc`); web.mjs's `usage` (`--port 0`, `--port 18000`) | run: mine |
| 10–19 | setup's own code, when `reason` is `exit` | run: `test_web_entry`, my `failure()` probe |
| 20 | 18000 held at the start, or held once `main()` rejected (`started_elsewhere`) | run: mine, E13 claim 6, coexistence |
| 21 | the ingress port held; the sentence offers a free port | run: mine |
| 22 | Node, uv, uvx or git missing or too old (a missing `uvx` gets `NO_UV`) | run: tests |
| 23 | dr-web could not install Node, download, or accept the tarball | run: tests, mine |
| 24 | setup outside 10–19, timeout, signal or `spawn`; agent-server not ready; any other rejection | run: my `failure()` probe |
| 1 | an uncaught exception | read |

---

## 3 · Divergences from the design

R = the Implementer reported it; **new** = it did not.

| # | Divergence | Reason | |
|---|---|---|---|
| 1 | E13 claim 5's WebKit case is `xfail(strict=True)`. The README names Chrome, Edge and Firefox, and says Safari opens no Library panel. | E13 run 39209373425 (per commit `c806559`): WebKit gets the bridge's 401 for the frame. Edge and Chrome are not tested by name (Playwright Chromium only). TASK-70. | R |
| 2 | Claim 9 **ages** uv's cached index answers in place (`age_uv_index_answers`, an hour back) instead of deleting `~/.cache/uv/simple-v*`. A new test before it, `test_aged_index_answers_send_uv_to_the_network_and_offline_uv_still_runs`, is its negative control, outside the xfail. The mark's reason names TASK-66 rather than P1. | Deleting the answers fails `--offline` too (TASK-66 design M8), so the claim as designed could never pass. | R as a helper; **new** as a change to claim 9 |
| 3 | `web-e2e` pins setup-uv to 0.8.17. `macos` and `release-smoke` do not pin it (the Mac smoke ran on 0.13.1). | `age_uv_index_answers` scans each answer's last 512 bytes for a recent u64 timestamp. On uv 0.13.1 (`simple-v26`) that leaves an answer even `--offline` treats as absent (commit `108fcff`; not run by me). | R |
| 4 | Claim 3 waits up to 180 s until 8000, 3001, 18000 and 18001 all listen, then requires every listening socket of the command and its descendants to be on 127.0.0.1. | The automation backend installs after the page first answers. | R |
| 5 | Claim 2 reads the environment of the launcher's **descendants** only, not the command's or the launcher Node's own. | No reason is given in the code. On Linux, `/proc/<pid>/environ` shows an exec-time environment, and W8 cleans the launcher's only in `process.env`. | R |
| 6 | The harness's failure marker for the command is `^✗ ` (`LaunchedApp.failed`, a field defaulting to `STARTUP_FAILED`). | The launcher echoes setup's script into the log, and the script holds `✗ ` mid-line (visible in the Mac smoke's log). | R |
| 7 | Signatures and texts:<br>• `library_frame(page, session_key) -> (frame, notice text or None)`;<br>• `point_the_library_at(app, base_url, directory, *, key, model, namespace, decomposition)`, where E12's was `(app, fake, directory)`;<br>• `build()` calls `wrong_machine` for every target, and it returns `None` for `web`;<br>• `not_a_tarball` gains `not a tar archive`, `no package.json` and `it cannot be read: <why>`;<br>• a missing `uvx` gets web.mjs's `NO_UV`. | The shared helpers serve E12 and E13 alike. A `--tarball` that cannot be read ended in a traceback (commit `1d4a1e9`). The design left the sentence for a missing `uvx` open. | R |
| 8 | Workflow details:<br>• the coexistence step runs only when E12 passed (a plain next step);<br>• `cross-repo-green` sparse-checks out `desktop/pins.toml`;<br>• the Mac smoke globs `dist/deep-reasoning-web-*.tgz`. | Mechanics the design did not fix. | R |
| 9 | Tests beyond §7, among them:<br>• dr-web: leftovers, no uv, a bad option;<br>• the entry: an old Node, other launch failures, version compare, sentences verbatim;<br>• the ageing helper's own test;<br>• claim 9's control;<br>• claim 4 also asserts that the worker's proxy key reached the run log (a positive control). | — | R |
| 10 | Size: ≈1.4k production and ≈2.5k test lines, against ≈0.77k and ≈0.92k (§4.3). | Mostly `dr_web.cache` (337 lines against ≈250 for all of dr-web), `build.py` (+314 against ≈130), and the harness. | R |
| 11 | D5's README sentence on offline relaunch (line 97) is unchanged. The new section says ten minutes. | The design (§11 item 2) left it to the Conductor; it waits for TASK-66. | R |
| 12 | `parseCommandLine` uses `parseArgs` non-strict, with tokens, raising its own `UsageError`s; `--` is refused as `Unknown option --`. `build.py` drops repeated targets. | Behaviour-preserving: the sentences are §5.2's. | **new** |

---

## 4 · Measured results

All at `1d4a1e9`. No run called a paid model: FakeOpenAI answers in E13, and the smokes start no conversation.

### 4.1 CI

| Run · job | Conditions | Result |
|---|---|---|
| `ci` · test | ubuntu, default suite | 946 passed, 132 deselected, 634 s |
| `cross-repo` · `web-e2e` (E13) | ubuntu-24.04, uv 0.8.17, Python 3.12. Fresh HOME and cold uv cache. The terminal holds four junk variables, and a `node` first on `PATH` exits 97. | **10 passed, 2 strict xfails, 164 s.** The cold first start took 38 s and the tarball is 2.8 MB (both printed by claim 1). Each claim's duration, from pytest's timestamps:<br>• claim 3: 9 s (waiting for the four ports);<br>• claim 4: 12 s;<br>• claim 5: Chromium 2 s, Firefox 4 s, WebKit 67 s to its xfail;<br>• claim 6: 4 s;<br>• claim 7: 0.4 s;<br>• claim 8: 9 s for the whole offline restart (served under 30 s, the exact time not printed);<br>• the control: 5 s;<br>• claim 9: 13 s to its xfail. |
| `cross-repo` · `desktop-e2e` | ubuntu, `.deb` and tarball from one build, Xvfb | E12 17 passed, 422 s; coexistence 2 passed, 65 s |
| `cross-repo` · `pins` | full history, no `v*` tag exists | the README check passed on its no-tag branch (vacuous) |
| `desktop-release` · `macos` | macos-latest, arm64, uv **0.13.1** | launch smoke 2 passed; web smoke 2 passed, 46 s. Node wheel 48.7 MiB; before-start 10 s; about 36 s from the step's start to the running line |
| `desktop-release` · `release`, `release-smoke` | — | skipped: they need a tag |

Baselines beside each arm:

- **The offline restart.** Fresh index answers (claim 8) pass. With the answers aged, the control's `uvx` fails
  online-first inside the cut and runs with `--offline`, and claim 9 fails as marked.
- **The browsers.** Chromium and Firefox pass, WebKit fails as marked.
- **The app.** E12 is green at the same commit, on the same build.

### 4.2 This sandbox (Linux x86-64, uv 0.8.17, no model)

Each step below uses the README's commit form, `uvx --from git+…@1d4a1e9…#subdirectory=packages/dr-web deep-reasoning`,
on the CI tarball:

1. **18000 held by a listener I started.** Node installed (`uv pip install`, `v22.12.0`), then the ready line and
   `left_out` naming the five variables my shell held, then `already_running(18000)`, exit 20, in 6.1 s. Nothing
   started.
2. **Again, inside `unshare -n`.** No `Installing`, the same `tree-9ccc26f11ccb8f1f` (the tarball's SHA-256
   prefix), exit 20. So V1/V2's premise holds here: the commit-pinned, dependency-free command restarts offline.
3. **8000 held, offline.** Exit 21, offering a free port.
4. **Bad options.** `--port 18000` and `--port 0` exit 2 with web.mjs's sentences; `--bogus` and `--port abc` exit 2
   with argparse's.
5. **The relinks.** The relinked `npm` and `npx` run, printing 10.9.0.
6. **The default suite.** Its tests in the seven changed files: 147 passed, 188 s.

Reproduce:

```sh
uv run desktop/build.py web && uv run playwright install --with-deps chromium firefox webkit
uv run pytest -m web tests/desktop/test_e13.py -v -rA       # needs the deep_reasoner_beta insteadOf line and unshare
xvfb-run -a uv run pytest -m desktop tests/desktop/test_coexistence.py -v -rA   # after building `linux web` and installing the .deb
```

### 4.3 Size

| Part | Lines added (gross) | Design §10 |
|---|---|---|
| dr-web (pyproject, four modules) | 504 | ≈250 |
| `desktop/web.mjs` | 342 | ≈200 |
| `desktop/build.py` | 314 (−18) | ≈130 |
| `dr_app` | 38 (−13) | ≈25 |
| README, workflows, `pyproject.toml` | 55 + 126 + 9 | ≈60 + 100 |
| Tests (with the harness; −137, mostly E12's moved helpers) | 2,473 | ≈920 |

---

## 5 · Defects and doubts

1. **A setup that cannot be spawned prints a line of the bootstrap script** *(run)*. `failure()` has no case for
   `reason: "spawn"`, so it falls through to `could_not_start(<first line>)`. The launcher's message begins with
   the whole setup command, `sh -c <bootstrap>`, which spans many lines. I fed the fork's own
   `setupFailureMessage` (`dr-3` `4355a36`, `dev-with-automation.mjs:1316`) a `spawn sh ENOENT` through
   `failure()`, and the user's one line came out as:

   ```text
   ✗ Deep Reasoning could not start: Setup command `sh -c # The setup command (C3 §4.2): explain the two failures that happen before dr-app exists, then run it.
   ```

   The exit code is 24, and the cause is not in the line. This is the Implementer's doubt, confirmed.
2. **Any OS error while unpacking reads as "not a tar archive"** *(run)*. `_unpack` catches `OSError` around the
   extraction as well as around the open. With `ENOSPC` injected into `TarFile.extract`, a valid tarball got
   `✗ … is not a Deep Reasoning browser tarball (not a tar archive). Nothing was changed.`, exit 23. Without the
   injected error, the same file unpacked.
3. **Doubt: `dr-app setup` by hand on the cheap path prunes without a port check** *(read)*. `prune_runtimes`'
   safety rests on "it passed the port check" (its docstring). A terminal `dr-app setup --repo … --commit <current>`
   passes no port check. The only stack it could hurt is one in the mixed run that design §3.4 and §11 item 3
   describe, still running the kept previous runtime. Not run.
4. **Behaviour to note, not a defect:** a Node that prints another version is refused with
   `✗ Installing Node failed (node --version exited 0); …` *(run: `test_a_failed_node_install_leaves_no_folder[another-node]`
   pins this sentence)*.

---

## 6 · Where the other branches meet this one

- **The UX round (TASK-65, `ux-round` `6d31d2c`)** shares 12 files with this branch:
  - `cross-repo.yml`, `README.md` and `desktop/build.py`;
  - `dr_app/cli.py` and `dr_app/texts.py`;
  - `tests/app/test_runtime.py` and `test_texts.py`;
  - `tests/desktop/app.py`, `test_app.py`, `test_build.py`, `test_e12.py` and `test_readme.py`.

  The design's §8 seams hold in the code. `package_web` takes `prepare()`'s defaults, and
  `test_the_web_tarballs_defaults_are_what_patch_defaults_writes` compares with `patch_defaults`, not literals.
  E13 asserts setup only through `dr_app.texts` functions, and never asserts `safety` or `NO_MODEL_KEY` (both still
  print on `dr-3`: the Mac smoke's log). The onboarding is skipped by its storage flag, and only `library_frame`
  clears the notice. E12's helpers now live in `app.py`, so the UX round's edits to them land there.
- **TASK-57 (`task-57-recap` `c44dcc4`)** shares no file.
- **TASK-66** (design only, on `design/task-66`) reuses this branch's `NETWORK_CUT`, `LaunchedApp.started_at` and
  `age_uv_index_answers`. The branch's claim 9 is already written in TASK-66's shape (its §5.5), so landing TASK-66
  removes the xfail mark; README line 97 changes there. W8 removes a terminal's `OH_UV_EXCLUDE_NEWER` with every
  `OH_*` *(read)*.

---

## 7 · What this check did not cover

- **The release path** (tag check, notes, the attached `.tgz`, `release-smoke`'s download): never run. I ran the
  notes' shell (indentation stripped as YAML does) with python3 3.11, and it prints the command under a 4-space
  indent.
- **Google Chrome, Edge and Safari** themselves (only Playwright's engines on Linux), and any Mac other than
  macos-latest's arm64 runner.
- **Other platforms.** The two wheel hashes cover Linux x86-64 and macOS arm64 only, so on any other platform
  `--require-hashes` fails the Node install with exit 23 *(read)*. These are the app's computers, which is what the
  README says.
- **Concurrency.** The W10 race itself (two stacks of different versions in one window) and two first starts at
  once (W5) were reasoned in the design and are unit-tested, not raced.
- **The claimed uv 0.13.1 breakage** of `age_uv_index_answers`: from commit `108fcff`'s message.
- **The spec.** It was not read; nothing here is measured against it.
