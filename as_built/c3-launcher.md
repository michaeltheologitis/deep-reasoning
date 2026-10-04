# C3 · Desktop launcher: the agent-server's source and a first-launch setup, as built

**TASK-11** · Cartographer · **r2, 2026-10-04**: the code at `61d9217`, head of `feat/launcher-agent-server-source` in
the Canvas fork [michaeltheologitis/OpenHands](https://github.com/michaeltheologitis/OpenHands) (draft PR #1 into the
fork's `deep-reasoning` at `ba4d883`; C3 is `02b7ac7..61d9217`, 20 commits) · checked against the design at `d0ccacb`
(`docs/design/c3-launcher.md` v2, which describes `22272d9`) · Node 22.22, uv 0.8.17 here; uv 0.12.23 in the live run.

**Revisions.** r2 (this) describes `61d9217`: r1's `22272d9` plus six fixes to how a setup phase is stopped
(`79de56c`, `9bd50ea`, `63d6b10`, `32fc051`, `a75ad64`, `6cfb9b7`) and the literate refactor (`f462e2f`, `5ef127f`,
`c9478a1`, `78a94e5`, `a641a0b`, `61d9217`). r1 (2026-10-03) described `22272d9` against design v1 `dca8b48`; its
D-1 to D-8 are all absorbed into design v2 (B1, B2, B3, B3, B4, B10, B8, and the Gate B section), so §2 starts at
D-9. Stop trusting from r1: every line reference in `dev-with-automation.mjs`, `dev-safe.mjs` and
`launcher-defaults.mjs`; §3's export list; §4.3's account of the timeout and of `stopServices`; §6.4's test list;
the sizes.

**Where this file lives.** deep-reasoning's branch `as-built/c3-r2`, cut from `design/c3`; nothing on this branch
builds or collects `as_built/` (no `pyproject.toml`, docs site or test runner). No document of ours goes into the fork.

**Evidence marks.** **[run]**: executed here at `61d9217` (or at the commit named) in a detached worktree of the
fork or in copies of its `scripts/`, `config/`, `tools/`; never in anyone else's worktree. **[CI]**: read from
GitHub's records through the MCP tools, full job logs included. **[read]**: read in the code, **not executed**; §7
lists the read claims that matter. Nothing here ran a paid model, the `claude` CLI or a live workflow.

**Reading order.** §2 (divergences), §4.4 (the stop and quit design, where the build changed most), §6.4 (what the
refactor stopped testing), §5 (what others rely on), then the rest as a map.

---

## 1 · What exists

A build of Agent Canvas can name in `config/defaults.json` where the agent-server comes from (any https or ssh git
repository, at a ref), where its state lives, and a command run as the user before the stack starts and again once
the agent-server answers. A full 40-hex commit is installed without `--reinstall`, so a relaunch runs uv's cached
build offline. The file's values are environment fallbacks applied once at each launcher's entry. [run, §6]

```text
config/defaults.json ─ sources, paths.stateDir ─▶ applyLauncherDefaults(process.env, SHARED_DEFAULTS) ─▶ unset names only
                     └ setup ──────────────────▶ readSetupConfig ──┐
dev-with-automation.main (desktop app, npm run dev, agent-canvas bin):  ▼
  parseArgs → fill, log [defaults] → read setup → prereqs, ports, dirs → runSetupCommand("before-start")
  → startAgentServer → waitForService(/server_info, proc): throws at once if proc closes → seed secret
  → runSetupCommand("after-ready", + AGENT_SERVER_URL, SESSION_API_KEY); on failure stopServices(), rethrow
  → automation, frontend, ingress           quit (SIGINT/TERM/HUP) at any point → shutdown → stopServices → exit 0
dev-safe.main (dev:minimal), dev-static.main, dev-extra-backend.main: the fill only
```

| Part | Lines added/removed at `61d9217` | Where |
|---|---|---|
| launcher code | +722 −35 | `scripts/launcher-defaults.mjs` (new, 191), `scripts/dev-with-automation.mjs` (+433 −19), `scripts/dev-safe.mjs` (+51 −10), `scripts/dev-process-utils.mjs` (+15 −2), `electron/main.mjs` (+13 −3), `config/defaults.json` (+13 −1), `scripts/dev-static.mjs`, `scripts/dev-extra-backend.mjs` (+3 each) |
| tests | +1,406 −3 | `__tests__/scripts/launcher-defaults.test.ts` (new, 251), `dev-with-automation.test.ts` (+849 −3), `dev-safe.test.ts` (+107), `agent-server-relaunch.live.test.ts` (new, 199) |
| docs | +71 | `docs/DEVELOPMENT.md` (+68), `.agents/skills/local-stack-runtime/references/guide.md` (+3) |
| workflow | +94 | `.github/workflows/launcher-live.yml` (fork only) |

[run: `git diff --numstat 02b7ac7 61d9217`] Commit order, oldest first: the seven upstream-shaped commits of r1, the
fork-only `22272d9` (live test and workflow), then the twelve upstream-shaped commits of the fixes and the refactor.
[run: `git log`]

---

## 2 · Divergences from the design (`d0ccacb`, v2)

The changelog has no `drift:` line for TASK-11. All twelve commits after `22272d9` postdate v2. [run: Notion query;
`git log`] Each item names what v2 says, what is built, and the reason the commits give.

**D-9 · A setup phase lasts until the command's output closes, and its stop reaches the process group even after the
command has exited** (`63d6b10`, `32fc051`). v2 §4.2 and §6.2: at the limit "the command's process tree" gets SIGTERM
and SIGKILL, and the promise "rejects once it has exited"; a quit stops "the command's process tree". Built: the
command is a service that ends on `close`, not `exit`, so a background child that keeps its stdout or stderr keeps
the phase open (`sh -c "sleep 2 & exit 0"` resolves after 2.0 s, `… exit 2` rejects with exit 2 after 2.0 s); while
it is open, the timeout and a quit signal its process group whether or not its leader is alive. A child whose
output is redirected is not waited for, and after the phase has ended nothing signals its group. Reason (commits):
the limit did not stop a command that had exited leaving such a child (the phase ended only when the child did),
and quitting left the child running. [run: timeout and quit probes, §6.3]

**D-10 · The stop gives up 1 s after SIGKILL on a child no signal reaches** (`a75ad64`, `6cfb9b7`). v2 has no such
bound: the phase and `stopServices` wait until everything has exited. Built: `OUTPUT_CLOSE_WAIT_MS` (1 s) after the
SIGKILL, an output-tracked service is dropped with `Output still open after SIGKILL; not waiting` (terminal only, not
the service-log listener). So a phase at its limit with a `setsid` child rejects as a timeout after limit + 4.0 s,
and a quit during such a phase exits 0 after 4.0 s; in both cases the child survives the launcher. Reason (commits):
without it the splash waited until the child exited, and a quit fell to the desktop app's 6 s safety net. [run]

**D-11 · One escalation, `stopService`, for the timeout and for quitting; services are records, not processes**
(`5ef127f`). v2 §5.4, §6.2: `stopServices()` sends SIGTERM to every tree and SIGKILL 3 s later; `runSetupCommand`
has its own timeout and kill. Built: §4.4. `spawnService` (upstream's, exported) gains an `untilOutputCloses` option
and stores `{proc, untilOutputCloses, ended, whenEnded, end}` in `processes`; new internal helpers `isServiceRunning`,
`signalService`, `stopService`, `abandonService`. During a quit a setup phase never settles (`runSetupCommand`
returns a promise that never resolves), so nothing after it starts. Reason (commit): the same escalation was
written twice. Behaviour is unchanged by `5ef127f`: §6.3. [run, read]

**D-12 · `dev-process-utils.mjs` changes** (`63d6b10`). Not in v2 §5's module list. `signalProcessTree(proc, signal,
{evenIfLeaderExited = false} = {})` (`:92–99`) signals the group of an exited leader when asked; ignored on Windows,
where `taskkill /t` walks from the leader. Only `signalService` passes it, and only for the setup command. [read; the
POSIX path run through §6.3]

**D-13 · `defaults.json` is read by `dev-safe.mjs` and passed in; `loadSharedDefaults` is gone** (`f462e2f`). v2 §6.1:
`loadSharedDefaults()` exported, `applyLauncherDefaults(env?, defaults?)`, imports `node:fs`, `os`, `path`, `url`,
`process`. Built: `dev-safe.mjs` exports `SHARED_DEFAULTS` (`:37`); `applyLauncherDefaults(env, defaults)` takes both;
`launcher-defaults.mjs` imports `node:os` and `node:path` only and reads no file. `dev-with-automation.mjs` passes its
own `SHARED_DEFAULTS` (upstream's second parse of the same file, `:92`). Reason (commit): a third read of one file.
[read; each launcher run with a relative `paths.stateDir` refuses with its message, §6.4 P10]

**D-14 · Fewer exports** (`c9478a1`). v2 §6.1–6.2 exports `SETUP_PHASES`, `expandHomePath` (home optional),
`SETUP_COMMAND_TIMEOUT_MS`, `buildSetupEnv` and a re-export of `SETUP_PHASES`. Built: all internal; `expandHomePath`
requires `home`. Reason (commit): nothing imports them. [run: export lists]

**D-15 · The fork-only commit is no longer last.** v2 B3 and §7.5: `22272d9` is "the branch's last commit", left out
when the branch goes upstream. Built: twelve upstream-shaped commits follow it, so leaving it out means dropping a
middle commit. No reason recorded. [run: `git log`]

**D-16 · Tests: same count, different set** (`78a94e5`, `a641a0b`, `61d9217`, and the fixes' tests). v2 B8 and the
Gate B property table: 29 + 14 + 19 + 1. Built: 26 + 13 + 23 + 1 (§6.2). Nine of the names v2's table cites no
longer exist (mapped in §6.2), and two properties that tests in v2's falsifier-1 row pinned are no longer pinned
(§6.4, P1 and P2).

**D-17 · Three of v2 B4's "pinned by the tests" details are not pinned**, before or after the refactor: a
whitespace-only ref, a bare `~`, and the `was stopped after 15 minutes` wording. [run: probes P12–P14, §6.4]

**D-18 · Size**: +2,293 −38 against v2 §8's 2,277 at `22272d9`; the fixes took it to 2,604 and the refactor back
down (§6.5).

Small, behaviour-neutral: `validateGitRepoUrl` uses `URL.parse` (Node ≥ 22.1) instead of `new URL` in a try/catch,
and accepts exactly what it did (18 inputs, including `https:///o/r` and `https://user:pw@host/r`) [run];
`SetupCommandError` assigns its details with `Object.assign` [read]. Everything else in v2 §2–§7 holds as r1 found
it at `22272d9`, and the code it rests on is unchanged since (`git diff 22272d9 61d9217` touches only the files of
D-9 to D-14 and the tests). [run: the diff; the tests in §6.2]

---

## 3 · The public surface, from the code

**`config/defaults.json`**: `sources.agentServerGitRepo`, `sources.agentServerGitRef`, `paths.stateDir`,
`setup.command` all `null`, `setup.phases: ["before-start", "after-ready"]`, each block with a `_comment`; the
top-level `_comment` is upstream's again (`f462e2f`). With these the fill adds nothing and `readSetupConfig` returns
`null`. [run]

**Environment.** New: `OH_AGENT_SERVER_GIT_REPO` (https or ssh URL; used only with a git ref). New default:
`OH_APP_BACKEND_PUBLIC_URL = http://127.0.0.1:<agent-server port>` unless set (`dev-safe.mjs:883`). Filled from the
file where unset or empty: `OH_AGENT_SERVER_GIT_REPO`, `OH_AGENT_SERVER_GIT_REF` (only if none of
`OH_AGENT_SERVER_LOCAL_PATH`, `_GIT_REF`, `_VERSION` is set), `OH_CANVAS_SAFE_STATE_DIR`, and the two key paths when
the state directory came from the file. Setup environment: §4.3. [run]

**JavaScript**, all ES modules:

| Module | Exports C3 adds | Where |
|---|---|---|
| `launcher-defaults.mjs` | `launcherDefaultsEnv(env, defaults, home = homedir())` (pure), `applyLauncherDefaults(env, defaults) → string[]` (sorted names), `validateGitRepoUrl(value, name)`, `readSetupConfig(defaults) → {command, phases} \| null` | `:51`, `:103`, `:138`, `:163` |
| `dev-safe.mjs` | `SHARED_DEFAULTS`, `DEFAULT_AGENT_SERVER_GIT_REPO` | `:37`, `:54` |
| `dev-with-automation.mjs` | `SetupCommandError` (`name`, `phase`, `command`, `reason` ∈ exit\|signal\|spawn\|timeout, `exitCode`, `signal`), `runSetupCommand({command, phase, cwd, env, timeoutMs?}) → {durationMs}`; `main()` takes `setup` (undefined reads the file, `null` none, an object validated like the file); `spawnService` takes `untilOutputCloses` | `:1263`, `:1362`, `:1864`, `:687` |
| `dev-process-utils.mjs` | `signalProcessTree`'s third argument (D-12) | `:92` |

[run: imported and listed; `main` and `spawnService` read]

**What the user sees** is r1's, unchanged: `[defaults] From config/defaults.json: <sorted names>`; `[agent-server]
Using git (<owner/repo>@<ref>)`; `[setup <phase>] Running …`, the command's lines, `Done in …`; the failure messages
of v2 §3.3; `Fatal error: …` and exit 1 from the CLI. New at quit or timeout, terminal only: `Output still open after
SIGKILL; not waiting`. [run: tests and probes]

---

## 4 · Structure and seams

### 4.1 The fill and the source (`launcher-defaults.mjs`, `dev-safe.mjs`)

`launcherDefaultsEnv` (`:51–95`) validates every launcher key first, whichever wins, then fills by v2 §2.1's rules.
Each launcher calls `applyLauncherDefaults(process.env, SHARED_DEFAULTS)` first in `main()`: `dev-safe.mjs:996`,
`dev-static.mjs:584` (after `parseArgs`), `dev-extra-backend.mjs:127`, `dev-with-automation.mjs:1850` (after
`parseArgs`, so `--help` never reads the file). No other function reads the file's launcher keys.
`buildAgentServerCommand(env)` (`dev-safe.mjs:438`) validates `OH_AGENT_SERVER_GIT_REPO` where it uses it (`:486`),
pushes `--reinstall` unless the ref matches `FULL_COMMIT_SHA` (`:56`, `:492`), and labels the source with
`gitRepoLabel` (`:559`). [run: the tests and a 77-case old/new differential, §6.3]

### 4.2 The launch (`dev-with-automation.mjs` `main()`, `:1790`)

The order is v2 §3.2's. Phases run only when `config.launchAgentServer` (`:1956`). `before-start` (`:1969`) runs
after `ensureDirectories` and `extraPrereqs`. The agent-server's process goes to `waitForService` (`:2007–2013`),
whose `watchServiceExit` (`:831`) throws at once when the process closes before `/server_info` answers, quoting its
last 10 lines. `after-ready` (`:2036`) runs after the secret seeding; its failure awaits `stopServices()` (`:2038`)
and rethrows; after a readiness timeout it is skipped with a log line (`:2044`). [run: the packaged launches]

### 4.3 The setup command (`:1245–1436`)

`runSetupCommand` spawns the argv through `spawnService` (no shell, stdin ignored, its own process group on POSIX)
under the name `setup <phase>` with `untilOutputCloses`, then awaits the first of the service's end or a spawn error
(an `error` with no pid). If the launcher is shutting down by then, it never settles. Otherwise the outcome is read
from the process: spawn, timeout (if its timer fired), signal, or exit; anything but exit 0 throws a
`SetupCommandError` from `setupFailureMessage` (`:1316`). A timeout's error carries the leader's own exit code,
which may be 0. `buildSetupEnv` (`:1287`) gives `OH_CANVAS_SETUP_PHASE`, the absolute state directory, its parent as
`OH_PERSISTENCE_DIR`, and in after-ready `AGENT_SERVER_URL` and `SESSION_API_KEY`; the working directory is the state
directory. [run]

### 4.4 Stopping and quitting: one design (`:687–820`, `:1442–1472`)

A **service** is what `spawnService` records: a process, and whether it ends at `exit` (every service but the setup
command) or at output `close` (the setup command). `end()` marks it ended, removes it from `processes` and
resolves `whenEnded`; it runs on that event, or when the launcher gives up.

`stopService(name, service, {quiet})` (`:796–814`) is the one escalation: SIGTERM to the process tree now, SIGKILL
`FORCE_STOP_DELAY_MS` (3 s) later if it has not ended, and for an output-tracked service `false` after another
`OUTPUT_CLOSE_WAIT_MS` (1 s); `true` as soon as it ends. The tree is signalled with `signalProcessTree`; for the
setup command, the group even after its leader has exited (D-12). A plain service is waited for until it exits.

Two callers:

| | Setup timeout (`runSetupCommand`, `:1382–1388`) | Quit (`shutdown` → `stopServices`, `:1449–1472`) |
|---|---|---|
| when | `timeoutMs` (15 min) after the phase starts | SIGINT, SIGTERM, SIGHUP; Electron's quit sends SIGTERM |
| which | the setup service, `quiet` | every service still running |
| gave up (`false`) | `abandonService` (log, `end()`), unless a quit has begun | `abandonService` |
| then | the phase rejects as `timeout` | hooks run, `process.exit(0)` |

A failed after-ready awaits `stopServices()` too, without exiting. Measured on Linux, at a 300 ms injected limit or
by SIGTERM to the launcher, identical before and after the refactor [run, §6.3]:

| Case | Timeout: settles after | Quit: exits after | Child afterwards |
|---|---|---|---|
| command still running, obeys SIGTERM | 0.3 s (`signal=SIGTERM`) | at once | gone |
| command still running, ignores SIGTERM | 3.3 s (`signal=SIGKILL`) | not run | gone |
| command exited, child in its group obeys / ignores SIGTERM | 0.3 s / 3.3 s | at once / 3.0 s | gone |
| command exited, child left the group (`setsid`) | 4.3 s, with the "Output still open" line | 4.0 s | **alive** |
| child with output redirected, after the phase ended | (phase already done) | at once | **alive** (not signalled) |
| no setup, stack up (agent-server and automation stubs) | — | at once | — |
| spawn error | at once (`reason=spawn`) | (launch already failed) | — |

### 4.5 The desktop app (`electron/main.mjs`, unchanged since r1)

`setup …` lines reach the splash's status line (`:629–636`); a `SetupCommandError` summary omits the ports hint
(`:736–742`). `startStack` calls `main()` with no `setup` (`:663`), so the packaged app reads its own
`defaults.json`. Quit: `before-quit` sends SIGTERM (Windows: `process.emit("SIGTERM")`) with a 6 s force-exit
(`:786–808`); every stop above ends within 4 s. [read; Electron not run]

---

## 5 · What others rely on, and what C3 relies on

All three Canvas branches below are cut from `22272d9` and merge onto `61d9217` without conflict, and nothing they
use from C3 changed after `22272d9` [run: `git merge-tree --write-tree`; `git diff 22272d9 61d9217`]:

- **wiring/dr-1** (`9881d24`, 3 fork-only commits): sets `sources.agentServerGitRepo` to the SDK fork and
  `sources.agentServerGitRef` to `cef3b24…` (dr-1) with `_agentServerGitRefComment`. Relies on the fill and the
  commit rule (§4.1). [run: its diff]
- **C1** (`feat/acp-subagent-sessions`, `9d75806`): carries the wiring change; its `mock-llm-e2e.yml` reads
  `sources.agentServerGitRepo` and `…GitRef` with `node -p` to fetch the SDK fork's ACP fixtures, falling back to
  upstream's release tag when either is null. Relies on the two key names and null meaning unset. [read]
- **C2** (`feat/agent-surfaces`, `f4c7ae5`): carries the wiring change; its frontend mints App-backend sessions at
  `app_backend_ingress_url` from the agent-server's `/server_info`, which the agent-server fills from
  `app_backend_public_url`, i.e. `OH_APP_BACKEND_PUBLIC_URL` (SDK `server_details_router.py:148`). Relies at runtime
  on `buildAgentServerEnv`'s default (§3). [read]
- **D5** (design `8086afb` on `design/d5`, no code yet): relies on v2 §4 "as written" plus the ingress default (its
  §8.5, now built): `paths.stateDir = ~/.deep-reasoning/canvas/agent-canvas`, `setup.command = ["sh", "-c",
  <bootstrap>, …]` in both phases, `OH_CANVAS_SETUP_PHASE`, `AGENT_SERVER_URL`, `SESSION_API_KEY`, stdin closed, the
  15-minute limit. D-9 and D-10 apply to its command as to any: a phase ends only when every process holding the
  command's stdout or stderr has exited; a process the command leaves in its group with output redirected outlives
  the phase and is not stopped at quit; one that leaves the group (`setsid`) survives even a quit or timeout during
  the phase. [read: D5's design; the behaviour run, §4.4]

C3 relies on: uv serving a `git+…@<40-hex>` requirement from its cache without network and not substituting a cached
PyPI wheel (v2 §2.3; the live run re-checks the first half); the agent-server's `/server_info`,
`OH_SESSION_API_KEYS_0`, `OH_PERSISTENCE_DIR` and `OH_APP_BACKEND_PUBLIC_URL`; Electron's `startStack` and
`before-quit` path; POSIX process groups for the setup command's stop. [read]

---

## 6 · Proof, tests and size, as measured

### 6.1 The runs at `61d9217`

| Run | Conditions | Result |
|---|---|---|
| CI `CI` [37171405880](https://github.com/michaeltheologitis/OpenHands/actions/runs/37171405880) | `pull_request`; ubuntu: lint (`tsc`, then eslint and prettier over `src/`), `npm test`, both builds, package check; windows: build only | green; **765 files passed, 1 skipped; 8,113 tests passed, 1 skipped, 7 todo** in 601.7 s; C3's files: `dev-safe` 74, `dev-with-automation` 91, `launcher-defaults` 26, the live file skipped [CI: full log] |
| desktop builds and checks on PR #1 | Linux packages, macOS x64 and arm64 DMG (universal skipped), Windows installer, SDK version consistency, PR title | all green, 13 check runs [CI]; none launches the app |
| live `Launcher live` [37171406704](https://github.com/michaeltheologitis/OpenHands/actions/runs/37171406704) | ubuntu-24.04, **uv 0.12.23** (latest), upstream `software-agent-sdk` v1.50.1 (inputs and `sources` empty) | **1 passed**, 31.4 s for both launches; the job requires exactly one pass [CI: full log] |
| here, `__tests__/scripts/` | Node 22.22, 4 CPUs, load 9.7 | **443 passed, 1 skipped**, 38.8 s [run] |
| here, C3's four test files at four commits | the same | `02b7ac7` (two files) 129; `22272d9` 191 + 1 skipped; `6cfb9b7` 200 + 1; `61d9217` 191 + 1 [run] |

The PR body still reports CI at `6cfb9b7` (8,122 passed); 8,122 − 9 = 8,113, the nine tests the refactor removed.
[read: PR body] The live test and the code it exercises (`buildAgentServerCommand`'s git branch,
`buildAgentServerEnv`) are unchanged since `22272d9`, so r1's local rerun against the SDK fork's commit (passed, 10.3
s offline relaunch) still applies to them. [run: `git diff 22272d9 61d9217`]

### 6.2 C3's tests, counted

| File | `22272d9` (r1) | `6cfb9b7` (fixes) | `61d9217` |
|---|---|---|---|
| `launcher-defaults.test.ts` | 29 | 29 | 26 |
| `dev-safe.test.ts` (added to upstream's 61) | 14 | 14 | 13 |
| `dev-with-automation.test.ts` (added to upstream's 68) | 19 | 28 | 23 |
| `agent-server-relaunch.live.test.ts` | 1 | 1 | 1 |
| **C3's** | **63** | **72** | **63** (62 deterministic) |

[run: names diffed against `02b7ac7`; no upstream test lost or renamed] Of the 23 in `dev-with-automation.test.ts`,
18 skip on Windows (the 12 packaged launches, the signal test, the 5 timeout tests); CI runs no tests there anyway.

Names v2 cites that changed: `dev-with-automation CLI › fails at once …` is now under `a packaged build's launch`;
`buildSetupEnv` ×2 are gone (asserted by `runs before-start before the agent-server and after-ready once it
answers`); `runs argv without a shell`, `closes stdin …` and `runs in the given working directory …` are one, `runs
argv without a shell, stdin closed, in the given working directory with the given variables`; `a command still
running at its timeout is stopped and rejects` is `… is stopped, with its background children, and rejects`; `streams
each output line …` gains `, between Running and Done`; `applyLauncherDefaults › … names` gains `, sorted`; gone:
`validates the defaults even when the environment wins`, `a local path still wins over a git repository and ref`,
`loads config/defaults.json from beside the scripts directory`, and the `(OH_AGENT_SERVER_GIT_REF)` case. New since
v2: four timeout tests (SIGKILL 3 s later; a background child that obeys or ignores SIGTERM after the command
exited; a child that left the group holds the phase at most 1 s past the SIGKILL) and four quit tests (during
before-start and after-ready; after a phase, nothing signalled; a child that left the group, exit within 6 s). [run]

### 6.3 Behaviour unchanged by the refactor

Old (`6cfb9b7`) and new (`61d9217`) copies, each run in its own process, outputs diffed: [run]

- **Timeout**, `runSetupCommand` at 300 ms: obeys SIGTERM, ignores SIGTERM, exited leader with a child that obeys or
  ignores it, `setsid` child, spawn error, and exit 0 / exit 2 with a child holding output (10 s limit). Same lines,
  outcome, `exitCode`, `signal` and elapsed time to 0.1 s in all eight.
- **Quit**, the launcher from a packaged copy with a stub `uvx`, SIGTERM during before-start (child ignoring
  SIGTERM; `setsid` child; command still running), during after-ready (child obeying; ignoring), after a phase had
  ended, and after ready with no setup. Same sorted lines, exit 0, duration to 0.1 s, services started, and survivors
  in all seven.
- The Refactorer's own `probe-stop.mjs`, rerun on these copies: identical in its four cases. Its recorded files show
  4.0 s old against 3.5 s new for the exited leader; here both were 3.5 s.
- `launcher-defaults.mjs`: 77 calls of the validator, the fill (5 environments × 10 defaults), `readSetupConfig` and
  `applyLauncherDefaults` give identical results; only the export lists differ (D-14).

### 6.4 What the refactor removed from coverage

Fourteen test names went and five came (§6.2). Each probe below is one temporary edit in a clean worktree, the
named tests run, the edit reverted, the tree checked clean: 19 probes at `61d9217`, four of them repeated at
`6cfb9b7` (P5 is a read, below). [run]

| # | Edit | Result at `61d9217` |
|---|---|---|
| P1 | a branch of a non-default repository is installed without `--reinstall` | **survives** (191 pass). At `6cfb9b7` `installs all four packages from OH_AGENT_SERVER_GIT_REPO` failed: `a641a0b` cut its argv to the four git URLs |
| P2 | a local path loses to a git source once `OH_AGENT_SERVER_GIT_REPO` is set | **survives**. At `6cfb9b7` `a local path still wins over a git repository and ref` failed; upstream's precedence test sets no repository |
| P3, P3b | `OH_PERSISTENCE_DIR` = the state directory; the session key in before-start | caught by `runs before-start … once it answers` |
| P4, P4b | setup stdin left open; `cwd` dropped | caught by the merged contract test (P4 by its 30 s timeout) |
| P6 | the timeout signals the command, not its group | caught by `… stopped, with its background children, and rejects` (by timeout) |
| P7 | the repository validated only when it is filled | caught by the 5 rejection cases, which now run with the environment winning |
| P8 | names returned unsorted | caught by `… returns their names, sorted` (r1's test could not see it) |
| P9 | an environment `OH_AGENT_SERVER_GIT_REF` no longer counts as a source | caught by `the defaults' repo still applies to a ref from the environment` |
| P11 | the agent-server's process not passed to `waitForService` | caught by the moved B1 test (still running at 20 s) |
| P15 | `stopService` never gives up | caught twice: the timeout's `… at most 1 s past the SIGKILL` and the quit's `… exits within 6 s` |
| P17 | a phase settles during a quit | caught by both `quitting while … ends the launch there` |
| P18 | no SIGKILL | caught by two timeout tests and one quit test |

Also cut (P5): `streams each output line …` no longer prints a stderr line under the phase; upstream's `forwards
stdout, stderr, and exit lines to the listener` covers stderr for every `spawnService` service [read]. Not pinned before
the refactor either: P10 (`dev:minimal` skips the fill: 443 pass; each launcher does refuse a relative
`paths.stateDir` when run [run]), P12 (whitespace-only ref accepted), P13 (bare `~` not expanded), both confirmed
unpinned at `6cfb9b7` too, P14 (the timeout message never names minutes) and P16 (the timeout's stop prints
`Stopping...`).

### 6.5 Size before and after

| `git diff --numstat 02b7ac7..` | `22272d9` (r1) | `6cfb9b7` (fixes) | `61d9217` (refactor) |
|---|---|---|---|
| code | +668 −35 | +761 −39 | **+722 −35** |
| of which statements / comment lines (scripts, Electron) | 401 / 217 | 460 / 247 | 433 / 235 |
| tests (live test 199 included) | +1,444 −2 | +1,678 −3 | **+1,406 −3** |
| docs, workflow | 71, 94 | 71, 94 | 71, 94 |
| **total** | **+2,277 −37** | **+2,604 −42** | **+2,293 −38** |
| upstream-shaped (all but the live test and workflow) | 1,984 | 2,311 | 2,000 |

[run; the Refactorer's `count.sh` gives the same numbers] The fixes added 93 lines of code and 234 of tests; the
refactor removed 39 and 272. Against v2 §8's ≈0.58 k estimate the build is about four times larger.

---

## 7 · What I could not verify

1. **Windows**: no C3 test runs there (CI builds only, and 18 of C3's 23 `dev-with-automation` tests skip there).
   `taskkill /t`, the no-op `evenIfLeaderExited`, and therefore D-9/D-10 on Windows, are read only.
2. **The desktop app**: Electron was not run; the splash line, the summary without the ports hint, and the quit
   through `before-quit` within its 6 s net are read.
3. **The 15-minute limit** ran only as short injected limits; its wording is unpinned (P14) and was not run.
4. **`OH_APP_BACKEND_PUBLIC_URL` end to end**: only its value is tested; C2's use of it and the SDK line are read.
5. **The SDK fork's commit on the latest uv**: the live run at `61d9217` measured upstream's v1.50.1; wiring/dr-1's
   `cef3b24` was not run live by anyone at this head.
6. **`__tests__/scripts/` at `6cfb9b7`** (452, the Refactorer's figure) was not run as a folder; C3's four files there
   were (200 + 1 skipped), and 443 + 9 agrees.
7. **The Refactorer's other mutation checks**: I re-ran the cuts above, not each of its own probes.
8. **Lint and typecheck**: CI's Lint is green; it covers `src/` and the TypeScript tests, not the `.mjs` launcher
   scripts [read: `package.json`, `tsconfig.json`]. I did not run it.
9. **"Validate PR description"**, red at `22272d9`, is not among the 13 check runs at `61d9217`; why was not checked.
