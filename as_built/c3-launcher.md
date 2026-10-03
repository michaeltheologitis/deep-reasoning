# C3 · Desktop launcher: the agent-server's source and a first-launch setup, as built

**TASK-11** · Cartographer · the code at `22272d9`, head of `feat/launcher-agent-server-source` in the Canvas
fork [michaeltheologitis/OpenHands](https://github.com/michaeltheologitis/OpenHands) (draft PR #1 into the fork's
`deep-reasoning`; C3 is `02b7ac7..22272d9`) · checked against the design at `dca8b48`
(`docs/design/c3-launcher.md` v1, unchanged on this branch) · uv 0.8.17 and Node 22.22 in this sandbox, uv 0.12.22
in the live run · 2026-10-03.

**Where this file lives.** On deep-reasoning's branch `as-built/c3`, cut from `design/c3`: C3's code is in the
fork and the fork carries only upstream-shaped code plus marked fork-only commits, so no document of ours goes
there. This branch has no `pyproject.toml`, no docs site and no test runner, so nothing builds an sdist or collects
`as_built/`. Every deep-reasoning branch that has a `pyproject.toml` already excludes `as_built/` from its sdist
beside `docs/` (`[tool.hatch.build.targets.sdist] exclude`), except `wip/d2-on-d1`. [run: `git show
<branch>:pyproject.toml` on every local branch]

**Evidence marks.** Every claim carries one.
- **[run]**: executed in this sandbox at `22272d9`, in a copy of the tree (`git archive` plus the checkout's
  `node_modules`), never in the checkout: the four C3 test files (`npx vitest run` on
  `__tests__/scripts/{launcher-defaults,dev-safe,dev-with-automation,agent-server-relaunch.live}.test.ts`: 191
  passed, 1 skipped, 11.4 s), the full suite (§6.1), uncommitted probe scripts that import the modules or run
  the launcher from a packaged-layout copy with a stub `uvx`, and a local rerun of the live test (§6.3).
- **[CI]**: read from GitHub's records of CI run 37085250155 and live run 37109360172, both at `22272d9`, through
  the GitHub MCP tools (job steps and log tails; full log downloads are blocked here, §7).
- **[read]**: read in the code, **not executed**. Weaker than [run]; §7 lists the read claims that matter.

C3 calls no model, and nothing in this document ran a paid model or the `claude` CLI.

**Reading order.** §2 first (the divergences), then §1 and §3–§5 as the map, §4.5 for what D5 gets, §6 for the
measurements and tests, §7 for what I could not verify.

---

## 1 · What exists

C3 lets a build of Agent Canvas name, in `config/defaults.json`, where the agent-server comes from (any git
repository, at a ref), where its state lives, and a command to run as the user before the stack starts and again
once the agent-server answers. A full 40-hex commit is installed without `--reinstall`, so a relaunch of that
commit runs uv's cached build with no network. The file's values are environment fallbacks applied once at each
launcher's entry; everything downstream still reads only the environment. [read; each part run in §6]

```text
config/defaults.json ─ sources, paths.stateDir ─▶ launcher-defaults.applyLauncherDefaults ─▶ process.env (unset names only)
                     └ setup ──────────────────▶ launcher-defaults.readSetupConfig ──┐
dev-with-automation.main (desktop app, npm run dev, agent-canvas bin):              ▼
  parseArgs → fill env, log [defaults] → read setup → prereqs, ports, state dirs → runSetupCommand("before-start")
  → startAgentServer: dev-safe.buildAgentServerCommand(process.env) → uvx [--reinstall unless 40-hex] --from git+<repo>@<ref>…
  → waitForService(/server_info, proc): throws at once if proc exits → seed automation secret
  → runSetupCommand("after-ready", + AGENT_SERVER_URL, SESSION_API_KEY); on failure stopServices(), throw
  → automation, frontend, ingress
dev-safe.main (dev:minimal), dev-static.main, dev-extra-backend.main: the fill only
```

| Part | Lines at `22272d9` | Where |
|---|---|---|
| launcher code | +668 −35 | `scripts/launcher-defaults.mjs` (new, 220), `scripts/dev-with-automation.mjs` (+365 −21), `scripts/dev-safe.mjs` (+52 −9), `electron/main.mjs` (+13 −3), `config/defaults.json` (+14 −2), `scripts/dev-static.mjs`, `scripts/dev-extra-backend.mjs` (+2 each) |
| tests | +1,444 −2 | `__tests__/scripts/launcher-defaults.test.ts` (new, 320), `dev-with-automation.test.ts` (+797), `dev-safe.test.ts` (+128), `agent-server-relaunch.live.test.ts` (new, 199) |
| docs | +71 | `docs/DEVELOPMENT.md` (+68), `.agents/skills/local-stack-runtime/references/guide.md` (+3) |
| workflow | +94 | `.github/workflows/launcher-live.yml` (fork only) |

Eight commits, oldest first: `b90bfa3` (fail at once when the agent-server exits early), `0c77c6d` (repository
variable, no reinstall for a commit), `b652a20` (`defaults.json` fallbacks), `a45d619` (setup command, Electron
lines), `6a6a16b` (skill guide), `49db305` (App-backend ingress default), `9e36e07` (DEVELOPMENT.md), and the
fork-only `22272d9` (live test and its workflow). [run: `git log 02b7ac7..22272d9`]

---

## 2 · Divergences from the design (`dca8b48`)

The changelog has no `drift:` line for TASK-11, so every item below was found from the code. All eight commits
were made after `dca8b48`. "Design §x" cites `dca8b48`. [run: Notion query of the Changelog; `git log`]

### 2.1 Behaviour a user or D5 sees

**D-1 · The launcher fails at once when the agent-server exits before it is ready** (`b90bfa3`). Design §5.8
lists the readiness wait among the things deliberately left unchanged ("an upstream weakness this change neither
causes nor needs, worth its own small PR"). Built: `startAgentServer` returns its process and `waitForService`
takes it (`dev-with-automation.mjs:808`, `1936–1943`); `watchServiceExit` (`:762–783`) keeps the process's last
10 output lines, and if it closes before `/server_info` answers the wait throws
`agent-server exited before startup completed (code=N, signal=S). Last output:` plus those lines, or
`agent-server could not be started (<message>).` Consequences: `npm run dev` now exits 1 instead of running on
without an agent-server after 60 s; the desktop app shows its failure state at once instead of after 10 minutes,
and its summary carries the ports hint, since this is not a `SetupCommandError` (`electron/main.mjs:739–742`).
Reason (commit message): a `uvx` that fails at once (no network, a bad ref) left the launcher polling until its
timeout and then reported a timeout instead of the failure. [run: `fails at once, with the exit code and last
output, when the agent-server exits before answering`, 0.75 s against a 60 s timeout; the ports hint read]

**D-2 · Canvas App backends get a default ingress origin** (`49db305`). Not in the design. `buildAgentServerEnv`
sets `OH_APP_BACKEND_PUBLIC_URL` to `http://127.0.0.1:<agent-server port>` unless the environment sets it
(`dev-safe.mjs:885–886`), so all four launchers that use it pass it to the agent-server (`dev-safe.mjs:1071`,
`dev-with-automation.mjs:1041`, `dev-static.mjs:343`, `dev-extra-backend.mjs:185`); Docker builds its own
environment and is unchanged. Reason (commit message): the agent-server's App-backend bridge answers 503 ("Canvas
App backend ingress is not configured") until that origin is set, and it must differ from the origin Canvas is
served on, so in the desktop app and `npm run dev` every App backend was unreachable. Documented in
`DEVELOPMENT.md`. [run: two unit tests on the value. read: the bridge's 503 in the SDK fork at `ea51b3f`,
`canvas_extensions/bridge.py:230–243`. No App backend was reached through it here, §7]

**D-3 · The live test is fork-only, not part of the upstream-shaped PR.** Design §7.5: the test file is in the
PR, and only the workflow is a fork-only commit on `deep-reasoning`. Built: test and workflow are one commit,
`22272d9`, marked `[fork only]` at the head of the PR branch; a byte-identical copy of the workflow is `ba4d883` on
the fork's `deep-reasoning`, because GitHub starts a `workflow_dispatch` run only when the file also exists on
the default branch. The seven upstream-shaped commits carry no live test. Reason: the commit messages of
`22272d9` and `ba4d883`. [run: `git diff ba4d883 22272d9 -- .github/workflows/launcher-live.yml` is empty]

**D-4 · The live run measured upstream's commit, not the SDK fork's.** Design §7.5 runs the file "with the fork's
source". The workflow takes its inputs, else `config/defaults.json` `sources`; at `22272d9` both are empty (no
wiring commit yet), so run 37109360172 installed upstream's `software-agent-sdk` at `1e1390a` (v1.50.1), with uv
0.12.22. [CI: the "Resolve the agent-server source" step prints `repo 'upstream'; ref 'upstream v1.50.1'`] The
SDK fork's commit was run here instead, §6.3.

**D-5 · A malformed `setup.phases` fails every full-stack launch even when `setup.command` is null.**
`readSetupConfig` checks `phases` before it looks at `command` (`launcher-defaults.mjs:192–206`); design §6.1
returns `null` "when setup.command is null or absent". Upstream's file carries a valid `phases`, so this matters
only for a build that edits it. No reason recorded. [run: `{command: null, phases: ["x"]}` throws the
`setup.phases` message]

### 2.2 Signatures and small behaviours

None of these changes what §2.1 describes. [run unless marked]

| Design | Built |
|---|---|
| `launcher-defaults.mjs` imports `node:fs`, `os`, `path`, `url` only (§5.2) | also `node:process` (`:29`) [read] |
| "unset" environment variables (§2.1) | unset **or empty**: `""` counts as unset in the fill and in `buildAgentServerCommand`, as upstream's source checks already did (`if (localPath)`) |
| `sources.agentServerGitRef`: a non-empty string (§4.1) | also not whitespace only (`ref.trim() === ""`, `:131`) |
| `validateGitRepoUrl`: an `https://` or `ssh://` URL (§6.1) | as designed, through WHATWG `new URL`, which also accepts `https:///o/r` (it reads `o` as the host) |
| `waitForService(name, url, timeoutMs)`; `startAgentServer` returns nothing | `waitForService(name, url, timeoutMs, proc = null)`; `startAgentServer` returns the process (D-1) [read] |
| `shutdown()` "keeps its own flow … and may call" `stopServices()` (§6.2) | `shutdown()` is now `stopServices().then(hooks, exit 0)` (`:1389–1401`): it exits as soon as every child has exited, where upstream waited a fixed 3 s [read] |
| the `[defaults]` line lists repo, ref, state dir, keys (§3.3's example) | names sorted, as §6.1 specifies: `OH_AGENT_SERVER_GIT_REF, OH_AGENT_SERVER_GIT_REPO, OH_CANVAS_SAFE_STATE_DIR, OH_SECRET_KEY_PATH, OH_SESSION_API_KEY_PATH` (the design is inconsistent with itself here) |

### 2.3 Tests, proof and size

**D-6 · Size: about four times the estimate.** Design §8: ≈0.58 k lines (code ≈243, docs 35, tests 300). Built:
+2,277 −37 (code +668, tests +1,444 with the 199-line live test, docs +71, workflow +94; §1). The excess is in
the tests (of `dev-with-automation.test.ts`'s +797: the setup unit tests ≈205 lines, the packaged-layout
harness and its stubs ≈215, its seven launches ≈280) and in `dev-with-automation.mjs` (+365 against 100: the
setup command, its messages and `stopServices` +270, D-1's +67, the fill and its log line +22). [run: `git diff --numstat`]

**D-7 · Tests beyond §7.** Added: `a command killed by a signal rejects naming the signal`, the CLI early-exit
test (D-1), two `OH_APP_BACKEND_PUBLIC_URL` tests (D-2; placed under `describe("buildAgentServerTelemetryEnv")`),
and `a SHA one digit short` among the refs that still reinstall. Every test §7.1–7.5 names exists under its name or
as an `it.each` case. [run]

**D-8 · CI on Windows runs no tests.** Design §7.4 has upstream's full suite run on the PR. It does, on Ubuntu
only: the `test-and-build (windows)` job skips Lint and Test (`full_checks: false`, `ci.yml:37, 65–70`) and only
builds the app. The three desktop jobs build and check the package files; none launches the app. [CI: job steps]

Not divergences: everything else in design §2–§7 is built as written, including the exact message texts of
§3.3, the fill rules of §2.1, the precedence of §3.1, the launch order of §3.2, the two Electron lines of §2.6,
and §1.4's exclusions (no change to `docker/`, `electron-builder.config.mjs`, `scripts/logger.mjs` or the CLI
flags). [run for the messages, rules and order, except the `was stopped after 15 minutes` wording, read from
`formatTimeout`; read for the rest]

---

## 3 · The public surface, from the code

**`config/defaults.json`** at `22272d9` (upstream's values, each with a `_comment`): `sources.agentServerGitRepo:
null`, `sources.agentServerGitRef: null`, `paths.stateDir: null`, `setup.command: null`, `setup.phases:
["before-start", "after-ready"]`. With these, `launcherDefaultsEnv` returns `{}` and `readSetupConfig` returns
`null`. [run]

**Environment variables.** New: `OH_AGENT_SERVER_GIT_REPO` (used only with `OH_AGENT_SERVER_GIT_REF`; an
`https://` or `ssh://` URL; default `https://github.com/OpenHands/software-agent-sdk`). New default:
`OH_APP_BACKEND_PUBLIC_URL` (D-2). Filled from the file when unset: `OH_AGENT_SERVER_GIT_REPO`,
`OH_AGENT_SERVER_GIT_REF`, `OH_CANVAS_SAFE_STATE_DIR`, `OH_SECRET_KEY_PATH`, `OH_SESSION_API_KEY_PATH`. Given to the
setup command: §4.3. [run]

**Precedence of the agent-server's source** (E = environment, D = `defaults.json`), first that applies: E
`OH_AGENT_SERVER_LOCAL_PATH`; E `OH_AGENT_SERVER_GIT_REF`; E `OH_AGENT_SERVER_VERSION`; D `agentServerGitRef`; PyPI
at `versions.agentServer` (1.50.1). A git source takes its repository from E `OH_AGENT_SERVER_GIT_REPO`, else D
`agentServerGitRepo`, else upstream; a repository without a ref is ignored. [run: §6.4's precedence tests and the
packaged launches]

**JavaScript.** `scripts/launcher-defaults.mjs` exports `SETUP_PHASES`, `loadSharedDefaults`,
`expandHomePath(value, name, home?)`, `validateGitRepoUrl(value, name)`, `launcherDefaultsEnv(env, defaults,
home?)` (pure), `applyLauncherDefaults(env?, defaults?) → string[]` (sorted names) and `readSetupConfig(defaults)
→ {command, phases} | null`. `dev-safe.mjs` adds `DEFAULT_AGENT_SERVER_GIT_REPO`. `dev-with-automation.mjs` adds
`SETUP_COMMAND_TIMEOUT_MS` (900,000), `SetupCommandError` (`name`, `phase`, `command`, `reason` ∈ exit | signal |
spawn | timeout, `exitCode`, `signal`), `buildSetupEnv(config, phase)`, `runSetupCommand({command, phase, cwd, env,
timeoutMs?}) → {durationMs}`, re-exports `SETUP_PHASES`, and `main()` takes `setup` (undefined reads the file,
`null` disables, an object is validated like the file). [run: imported and called]

**What the user sees.** `[defaults] From config/defaults.json: <names>`; `[agent-server] Using git
(<owner/repo>@<ref>)` for a non-default repository (`https://github.com/` and `.git` dropped; an `ssh://` URL keeps
its scheme), `Using git (<ref>)` for upstream's; `[setup <phase>] Running <argv joined by spaces>`, the command's own
lines, `Done in <S>s` or `Done in <M>m <S>s`; `[setup after-ready] Skipping setup after-ready: agent-server not ready`.
The failure messages are design §3.3's to the letter, for example

```text
Setup command `example-app setup` failed (exit 2) after the agent-server started; the stack was stopped. Its output is in the startup log.
Setup command `example-app-not-installed setup` could not be started (spawn example-app-not-installed ENOENT) before the stack started.
```

The CLI prints `Fatal error: <message>` and the stack, and exits 1. `--help` lists `OH_AGENT_SERVER_GIT_REPO` and a
`SETUP:` paragraph, and exits 0 before `defaults.json` is checked. [run: tests, the probe launches, and `--help`
against a broken `defaults.json`]

---

## 4 · Structure and seams

### 4.1 The fill: `launcher-defaults.mjs`

`launcherDefaultsEnv` validates all three launcher keys first, whichever wins, then fills: the repository when
`OH_AGENT_SERVER_GIT_REPO` is unset; the ref only when none of `OH_AGENT_SERVER_LOCAL_PATH`, `_GIT_REF`, `_VERSION`
is set; the state directory (`~` and `~/…` expanded, else absolute) when `OH_CANVAS_SAFE_STATE_DIR` is unset, and
then each key file inside it unless its own variable is set. A state directory from the environment never moves
the key files. `applyLauncherDefaults` assigns the result into `process.env`. [run: 29 tests, and the probe]

Callers: `dev-with-automation.mjs:1779` (after `parseArgs`, so `--help` never reads the file), `dev-safe.mjs:998`,
`dev-static.mjs:583`, `dev-extra-backend.mjs:126`, each first in `main()`. Only the first logs what it filled. No
other function reads the file's launcher keys; `buildAgentServerCommand(env)` and `buildSafeDevConfig(cwd, env)`
see only their `env`, so upstream's tests calling `buildAgentServerCommand({})` stay independent of the file.
[read]

### 4.2 The source: `buildAgentServerCommand` (`dev-safe.mjs:440–558`)

In the git branch only: the repository is validated where it is used (`:487–492`), `--reinstall` is pushed unless
the ref matches `/^[0-9a-f]{40}$/i` (`:58`, `:494–496`), and the source label is built by `gitRepoLabel`
(`:561–563`). The four packages always come from the same `git+<repo>@<ref>`. The local-path and PyPI branches are
unchanged. [run]

### 4.3 The launch: `dev-with-automation.mjs` `main()` (where the complexity sits)

The order is design §3.2's. Three pieces carry the length:

- **`runSetupCommand`** (`:1296–1355`) runs the argv through `spawnService` (no shell, `stdin` ignored, a new
  process group on POSIX, `where.exe` resolution on Windows), under the service name `setup <phase>`, so its lines
  reach the terminal, the file log and the `onServiceLog` listener. It settles on `close` (every line logged),
  or on `error` when the process never got a pid. At the timeout the group gets SIGTERM, SIGKILL 3 s later, and
  the result is `timeout` once it has exited. Anything but exit 0 becomes a `SetupCommandError` built by
  `setupFailureMessage` (`:1255–1276`). [run: 9 unit tests; a TERM-trapping command at a 300 ms timeout is
  SIGKILLed and rejects after 3.31 s]
- **`stopServices`** (`:1368–1387`), extracted from `shutdown()`: SIGTERM to every running process group, SIGKILL
  to stragglers after 3 s, resolved when all have exited. `main()` awaits it before rethrowing an after-ready
  failure; `shutdown()` (SIGINT, SIGTERM, SIGHUP, and Electron's quit) awaits it, runs its hooks and exits 0. The
  setup command is a tracked service, so quitting during a phase stops its whole group. [run: SIGTERM to the
  launcher during a `before-start` that had backgrounded a `sleep 60`: both processes gone, launcher exit 0, no
  agent-server started]
- **The early-exit watch** of D-1 (`:754–836`).

Phases run only when `config.launchAgentServer` (`:1885`; not with `--frontend-only`) [read].
`before-start` runs after `ensureDirectories` and `extraPrereqs`; `after-ready` after `/server_info` answered and
the automation secret was seeded, before automation starts; if the agent-server timed out, after-ready is skipped
with its log line and `main()` goes on to return `agentServerReady: false`, which the desktop app turns into its
failure. [run: the ordered timestamps of `runs before-start before the agent-server and after-ready once it
answers`; the skip by a probe with a 3 s readiness timeout]

`buildSetupEnv` (`:1226–1241`) adds `OH_CANVAS_SETUP_PHASE`, the absolute state directory, `OH_PERSISTENCE_DIR`
(its parent), and in after-ready `AGENT_SERVER_URL` (`http://127.0.0.1:<port>`, from `getAgentServerBaseUrl`,
`:858`) and `SESSION_API_KEY` (`config.sessionApiKey`, the value the agent-server gets as
`OH_SESSION_API_KEYS_0`). The working directory is the state directory. [run]

### 4.4 The desktop app (`electron/main.mjs`)

`handleServiceLog` also puts any service whose name starts with `setup ` on the splash's one-line status
(`:629–636`); the startup-failure summary omits the ports hint when `err.name === "SetupCommandError"`
(`:736–742`). Everything else reaches Electron through `main()`, which `startStack` calls with no `setup` option,
so the packaged app reads its own `config/defaults.json`. [read; Electron was not run, §7]

### 4.5 What C3 offers D5, and what stays D5's

D5 starts the agent-server from a pinned SDK-fork commit and runs dr-acp's setup through this launcher. As built,
D5 can rely on:

- **The source.** With `sources.agentServerGitRepo` and a 40-hex `sources.agentServerGitRef`, and no
  `OH_AGENT_SERVER_*` in the app's environment, all four SDK packages come from that commit, without
  `--reinstall`. [run: packaged launch test] A relaunch of the agent-server process from uv's cache needs no
  network [CI on upstream's commit, uv 0.12.22; run on the SDK fork's commit, uv 0.8.17, §6.3]. A branch or tag
  refetches and rebuilds every launch.
- **The state.** `paths.stateDir = <P>/<name>` puts conversations, workspaces and both key files under
  `<P>/<name>`, and the agent-server's persistence root (settings, secrets, profiles, installed Apps) at `<P>`
  [run: with `~/.example-app/agent-canvas`, a probe launch created `api-key.txt`, `secret-key.txt`,
  `dev_conversations/`, `workspaces/`, `bash_events/` and `storage/` there and nothing else in `$HOME`; the packaged
  launch test's stub agent-server saw `OH_PERSISTENCE_DIR=$HOME/.example-app` and the session key from that
  `api-key.txt`]; the automation database at `<P>/automation/automations.db` [read].
- **The setup command.** Design §4.2's contract holds as written: argv without a shell, `argv[0]` on the
  launcher's `PATH` (in the packaged app, the bundled uv and Node directories first, `electron/main.mjs:140, 251`
  [read]), `stdin` closed, cwd the state directory, the environment of §4.3, both phases on every launch that
  starts the agent-server, 15 minutes per phase, a failure stopping the launch with nothing left running, quitting
  during a phase stopping its group. [run, except the 15-minute value, run only as a constant and at 300 ms]
- **Two things the design did not promise**: App backends are reachable through the agent-server's own origin
  (D-2), and a first launch whose `uvx` fails (no network, no access to a private repository) fails at once with
  the last output lines instead of after 10 minutes (D-1).

D5's, not C3's: the wiring commit (the SDK fork's repository and the `dr-N` commit in the fork's `defaults.json`,
design §4.5, not made at `22272d9`); the state directory's name with a parent of its own; the setup command itself,
including that it brings its own entry point (`uvx --from git+…@<commit> dr-app setup`), dispatches on
`OH_CANVAS_SETUP_PHASE`, is fast and offline-safe when it has nothing to do, keeps `SESSION_API_KEY` and secrets
out of its output, and sets `GIT_TERMINAL_PROMPT=0` for a private fetch; the product name that separates Electron's
`userData`; and the offline relaunch of the **whole** app, which C3 does not test: the live test starts only the
agent-server, and the automation backend (PyPI) and D5's own setup command have network needs C3 does not control.
[read: design §4.4–4.6 against the code]

### 4.6 What it relies on

uv: that a `git+…@<40-hex>` requirement without `--reinstall` is served from its cache without network, and is not
replaced by a cached PyPI wheel of the same version (design §2.3's measurement at 0.8.17; the live run re-checks the
first half at 0.12.22). The SDK's agent-server: `/server_info`, `OH_SESSION_API_KEYS_0`, `OH_PERSISTENCE_DIR`, and
the App-backend bridge reading `OH_APP_BACKEND_PUBLIC_URL`. Electron: `startStack` calling `main()` and the
`before-quit` → SIGTERM path into `shutdown()` (`electron/main.mjs:649–679, 786–803`). [read]

---

## 5 · Wiring

`config/defaults.json` ships the three blocks as `null`; the packaged app and the npm package already ship
`scripts/*.mjs` and `config/` (the CI package listing includes `scripts/launcher-defaults.mjs`). [CI: `npm pack
--dry-run` output] Docs: `docs/DEVELOPMENT.md` gains the two variables, the commit rule and a "Building from a fork:
`config/defaults.json`" section (keys, fill rules, persistence-root table, setup contract); the local-stack skill
guide gains three lines. [read]

PR #1 is a draft into the fork's `deep-reasoning` (base `ba4d883`), 8 commits, +2,277 −37 in 14 files. CI on the
PR: `CI` (`test-and-build` ubuntu: lint, `npm test`, app and library builds, package check; windows: app build
only), `Desktop (Linux)`, `Desktop (macOS)` x64 and arm64 (universal skipped), `Desktop (Windows)`, `Check SDK
version consistency`, `pr-title`: all green. `Validate PR description` fails with four errors, all upstream's
contributor policy: no human note under `HUMAN:`, no screenshot or video (frontend code, and "Bug fix" ticked), no
linked `ready-for-dev` issue. [CI] `.github/workflows/launcher-live.yml`: `workflow_dispatch` with optional
repository, commit and uv-version inputs; installs uv with `scripts/download-uv.mjs` (latest unless pinned), sets
`kernel.apparmor_restrict_unprivileged_userns=0`, runs the live file with `OH_AGENT_SERVER_LIVE=1`, and fails
unless exactly one test passed. [read]

---

## 6 · Measurements and tests, as measured

### 6.1 The runs

| Run | Commit | Conditions | Result |
|---|---|---|---|
| CI `CI` [37085250155](https://github.com/michaeltheologitis/OpenHands/actions/runs/37085250155) | `22272d9` | `pull_request`; ubuntu-24.04 full checks; windows-latest build only | green; ubuntu Test step 10 m 26 s [CI]; the pass count is not readable from the log tail (§7) |
| desktop builds 37085250118, 37085250100, 37085250132 | `22272d9` | Linux (AppImage, deb), macOS x64 and arm64 DMG, Windows installer | green; build and file checks only [CI] |
| live [37109360172](https://github.com/michaeltheologitis/OpenHands/actions/runs/37109360172) | `22272d9` | ubuntu-24.04, uv 0.12.22, upstream `software-agent-sdk` `1e1390a` (v1.50.1), fresh `UV_CACHE_DIR` | **1 passed**, 0 skipped, 23.6 s for both launches [CI] |
| live 37081094623 | `04c5024`, an earlier version of the fork-only commit | same workflow | passed [CI]; its tree differs from `22272d9`'s only by the 68 lines of `DEVELOPMENT.md` [run: `git diff --stat`] |
| this sandbox, C3's four test files | `22272d9` | Linux, Node 22.22, 4 CPUs | **191 passed, 1 skipped** (the live file), 11.4 s [run] |
| this sandbox, full suite (`npx vitest run`) | `22272d9` | the same | **765 files passed, 1 skipped** (the live file); **8,113 tests passed**, 1 skipped, 7 todo; 18 m 17 s [run] |
| this sandbox, live file (local variant, §6.3) | `22272d9` | uv 0.8.17; upstream `1e1390a`, SDK fork `ea51b3f`, and a `--reinstall` control | **passed, passed**; the control fails offline as it should [run] |

The Implementer's figure in the PR body, "8,113 tests passed, lint and typecheck green", matches the test count
above [run]. Upstream's suite had 764 files at `02b7ac7` (design §7.4); C3 adds two. [read]

### 6.2 Design §2.3's measurements (the System Designer's)

Measured with uv 0.8.17 and `unshare -n`, reported in design §2.3 and not repeated by me except the row §6.3
reruns: a tag or branch cannot run with the network cut, with or without `--offline`; a commit runs offline without
`--reinstall` and fails with it; the real agent-server at SDK-fork `91430aa` relaunched offline in 6.4 s (first
install online 25 s); without `--reinstall`, a cache holding PyPI's `openhands-*==1.50.1` still yields the git build
(`direct_url.json` names the commit). The code's comment cites the same measurement (`dev-safe.mjs:482–486`). [read]

### 6.3 The live test: relaunch with the network cut

`agent-server-relaunch.live.test.ts` (skipped unless `OH_AGENT_SERVER_LIVE=1` on Linux) builds the command with
the real `buildAgentServerCommand` for `OH_AGENT_SERVER_GIT_REPO`/`_GIT_REF` (default upstream `1e1390a`), asserts
it has no `--reinstall`, starts it with `buildAgentServerEnv`'s environment and a fresh `UV_CACHE_DIR` through a
Node probe until `/server_info` answers (10 min limit), stops it, then runs the same probe inside a network
namespace with only loopback (`unshare -n`, or `--map-root-user -n`, then `ip link set lo up`) and asserts that
`https://pypi.org/simple/` is unreachable from inside and that `/server_info` answers (3 min limit). If no
namespace can be created it skips, which the workflow turns into a failure. [read; CI and run below]

Rerun here, with one change to a copy of the file: this sandbox has no `ip`, so a five-line Python `ioctl`
brings the namespace's loopback up instead. uv 0.8.17, as root (`unshare -n`), a fresh cache per run. [run]

| Source | First launch, online, to `/server_info` | Relaunch, network cut | Result |
|---|---|---|---|
| upstream `1e1390a` (v1.50.1), the file's default | 32.9 s | 10.7 s | passed |
| SDK fork `ea51b3f` (head of `michaeltheologitis/software-agent-sdk` `deep-reasoning` today; not a `dr-N` tag, none exists) | 32.8 s | 10.3 s | passed |
| control: upstream `1e1390a`, the relaunch with `--reinstall` added | 35.4 s | `uvx` exits 2 after 8.3 s: `Failed to fetch: https://pypi.org/simple/posthog/` … `dns error` | not ready, as it should be |

The durations are the probe's whole run (its 2 s stop grace and the reachability check included), not the
agent-server's start alone. In every relaunch `https://pypi.org/simple/` was unreachable from inside the namespace.
In CI (run 37109360172) the whole test, both launches, took 23.6 s; its log does not split them. [CI]

### 6.4 The deterministic tests C3 adds (62, all passing) [run]

- **`launcher-defaults.test.ts`, 29.** The fill: repo and ref from defaults; each environment source wins over the
  defaults' ref; the defaults' repo applies to an environment ref; the environment's repo wins; `~/` expansion; both
  key files move into a defaults state directory; they stay when the environment names the state directory; key
  paths in the environment win; upstream's null shape fills nothing. Validation: a relative state directory; five
  bad repositories (`owner/repo`, scp-style, `git+https`, `http`, `file`); an empty ref; validation even when the
  environment wins. `applyLauncherDefaults` fills only unset names and returns them sorted. `readSetupConfig`:
  argv and default phases, phases reordered to launch order, null means no setup, three bad commands, three bad
  phases. `loadSharedDefaults` finds the file.
- **`dev-safe.test.ts`, 14.** All four packages from `OH_AGENT_SERVER_GIT_REPO`; the source line for three
  repository spellings; the repository ignored without a ref; a bad repository rejected with the design's message;
  a full SHA without `--reinstall`; a branch, a tag, an abbreviated SHA and a 39-digit SHA still reinstall; a local
  path still wins; `OH_APP_BACKEND_PUBLIC_URL` defaulted and overridable.
- **`dev-with-automation.test.ts`, 19.** `buildSetupEnv` per phase (2). `runSetupCommand` with real child
  processes (9): argv reaches the child as one literal argument (`$HOME; echo x`); lines stream under the phase
  name with `Running …` first and `Done in Ns` last; stdin is at end of input; cwd and variables arrive; exit 2 in
  each phase gives the exact message and fields; SIGKILL gives `was killed by SIGKILL`; a missing command gives
  `could not be started (spawn … ENOENT)`; a 200 ms timeout stops the process (its pid is gone). The CLI's early
  exit (D-1). Seven launches of a packaged-layout copy (`scripts/*.mjs`, `tools/`, a test-written
  `defaults.json`, a stub `uvx` that records argv and answers 200, outside the repository; skipped on Windows):
  the exact agent-server argv and source line from `defaults.json`; `OH_AGENT_SERVER_VERSION` still wins; the state
  directory and key files from `defaults.json` with nothing under `~/.openhands`; before-start before the
  agent-server starts and after-ready after its first `/server_info` and before automation, with the right cwd and
  variables; a failing before-start exits 1 with the message and the stub `uvx` never ran; a failing after-ready
  exits 1 with the message, the agent-server's port closed and automation never started; a string `setup.command`
  exits 1 before anything runs.

The design's three falsifiers map onto them as design §7.6 says: the packaged launch and the precedence tests
(first); the no-`--reinstall` unit test and the live test (second); the two failing launches and the timeout test
(third). All pass. [run; the live test CI and run]

---

## 7 · What I could not verify

1. **CI's test counts.** The GitHub tools return at most the last 5,000 lines of a job log, and the ubuntu job's
   22,253 lines end with 11,000 lines of `npm pack` listing; downloading the full log is blocked here. CI's
   Test step is green, but which C3 tests it ran, and how many, I read only from my own run (§6.1).
2. **Windows.** No test runs on Windows in CI (D-8), and the launch tests skip there. The setup command's Windows
   path (`where.exe` resolution, `taskkill /t /f` for the timeout and quit) is read only.
3. **The desktop app.** Electron was not run: the splash status line for `setup …` services, the summary without
   the ports hint, and quitting during a phase through `before-quit` are read. The desktop CI jobs build packages
   and do not launch them.
4. **`OH_APP_BACKEND_PUBLIC_URL` end to end** (D-2): only its value is tested; no App backend was reached through
   the agent-server here, and the claim that the origin must differ from Canvas's is the commit message's.
5. **The 15-minute timeout** ran only as a constant and as a 300 ms injected timeout.
6. **The macOS `PATH` from Finder** (`/usr/bin:/bin:/usr/sbin:/sbin`, design §4.2) is the design's, not checked.
7. **An offline relaunch of the whole app**, setup command and automation backend included: not tested by C3
   (§4.5).
8. **Lint and typecheck** at `22272d9`: CI's Lint step is green [CI]; I did not run either.
