# TASK-66 · The launcher's uvx starts: PyPI pinned to a time, and offline from uv's cache — design

**TASK-66** · System Designer · design branch `design/task-66` in
[deep-reasoning](https://github.com/michaeltheologitis/deep-reasoning), cut from `main` at `9e8109e`; this file is
the only change on it · approved in chat by Michael on 2026-10-19 ("go with your recommendations"), as one small
Canvas task; there is no spec page, so the task row and the Conductor's brief are what this design answers to.
It ships in Canvas tag `dr-4` with the UX round (TASK-65).

**Pinned against:** Canvas fork `dr-3` `4355a36` (every Canvas `file:line`) · deep-reasoning `main` `9e8109e` ·
SDK fork `dr-2` `34c540c` · uv 0.8.17 (the floor) and 0.12.23 (the app's, `pins.toml`) for every measurement.

**Revisions** (newest first):
- 2026-10-19 · v1 · first version.

**Where this file lives.** `docs/design/task-66-uv-pins.md`. At `9e8109e` pytest collects `tests/` only
(`testpaths`), ruff excludes `docs`, the sdist excludes `docs/`, and no wheel packages it. No pull request of the
task carries it.

**Reading guide.** Everyone: §1 (what was measured) and §2 (the decisions), about 8 minutes. The Implementer: all
of it; §3–§4 are the signatures and every sentence a user reads, §5 the tests. The Conductor and the UX round: §6.

---

## 1 · What was measured

Run on 2026-10-19 in this sandbox with the scripts in the System Designer's scratchpad
(`/tmp/claude-0/-home-user/f8e56d4d-b822-5c27-9bd1-fe1ab3886dee/scratchpad/task-66-design/scripts/`: `paths.sh`,
`automation.sh`, `aged.sh`, `expiry.sh`, `age.py`, `mirror.py`).
"Network cut" is `unshare -rn` with loopback up and no proxy, so DNS fails at once, as with Wi-Fi off. Times are
wall clock; the pair is uv 0.8.17 / 0.12.23. The command is the launcher's own: the agent-server at the SDK pin
(`buildAgentServerCommand`, git mode, full commit, plus `posthog>=6,<7`), and the automation backend
(`openhands-automation==1.16.0`), each with `--exclude-newer 2026-10-04T00:00:00Z`.

| # | Finding | Measured |
|---|---|---|
| M1 | **Only an RFC 3339 UTC time means the same instant everywhere.** uv reads a date as the end of that day in the user's own time zone, and a span relative to now. | `uv lock --exclude-newer` records: `2026-10-01` → `2026-10-02T00:00:00Z` (UTC), `…-01T10:00:00Z` (Kiritimati), `…-02T11:00:00Z` (Pago Pago), on both versions. `1 week`, `P7D`: refused by 0.8.17, a moving `exclude-newer-span` on 0.12.23. `2026-10-01T00:00:00Z` and `…T02:00:00+02:00`: `2026-10-01T00:00:00Z` everywhere. |
| M2 | **A cutoff alone does not restart offline once uv's index answers have expired; `--offline` does.** | Answers aged an hour (M8), network cut: online-first exits 2 (`dns error`) after 0.9 / 5.3 s (agent-server) and 2.8 / 4.2 s (automation); with `--offline`, exit 0. Same for a one-package environment on a local index serving `max-age=1` (TASK-48 F2's method): exit 2 after 5.6 / 8.6 s; `--offline` 0.4 s, exit 0. |
| M3 | **A network that hangs costs a minute or two before uv gives up.** | `HTTPS_PROXY` at a listener that accepts and never answers (a one-package environment; uv asks for packages in parallel): online-first exits 2 after 123 / 49 s; `--offline`: at once. |
| M4 | **An offline probe of a cold cache fails at once; the first install is half a minute.** | `uvx --offline … python -c ''` on an empty cache: exit 1 in 0.12–0.18 s. Online install: agent-server 40 / 34 s, automation 38 / 36 s. |
| M5 | **An offline probe of a warm cache costs half a second.** | 0.60 / 0.36 s (agent-server), 0.55 / 0.26 s (automation). For scale, `agent-server --help` itself takes 10–12 s. |
| M6 | **Offline-first alone never moves to a new cutoff.** Offline, uv resolves from whatever answers it cached; if they predate the new cutoff's releases, it resolves the old set and calls it satisfied. | Cache filled from PyPI as of Oct 4 (a mirror dropping later files), cutoff then moved to Oct 19: the `--offline` probe exits 0 and runs starlette 1.7.0; one online start runs 1.9.0; `--offline` afterwards runs 1.9.0. Both versions. |
| M7 | **Today, a later launch upgrades dependencies by itself.** The drift is not only at first install. | No cutoff, installed from PyPI as of Oct 4 (starlette 1.7.0); a relaunch once the answers expired, PyPI as of today: starlette 1.9.0. Both versions. |
| M8 | **Deleting `simple-v*` is not a stand-in for expiry; ageing the answers in place is.** uv stores each answer as an rkyv archive whose root, the HTTP cache policy, is at the end and holds the fetch time as u64 Unix seconds. | With `simple-v*` deleted, `--offline` exits 1 (`registry packages may only be read from the cache`) in 0.04 s. Moving every u64 in each answer's last 512 bytes that lies in the fetch window back by 3600 s: found in 196 of 196 answers (agent-server) and 211 of 211 (automation); then the restart inside the window passes online-first, the aged one fails online-first and passes with `--offline`, on both versions, against real PyPI. |
| M9 | **An index without upload times cannot satisfy any cutoff.** | A mirror that drops PEP 700's `upload-time`: with `--exclude-newer`, unsatisfiable on both versions (0.12.23 says `filtered by exclude-newer`); without, it installs. |
| M10 | **uvx's own flags reach neither server.** | Under `uvx --offline --exclude-newer …`, the child's environment holds `UV` and what uvx inherited: no `UV_OFFLINE`, no `UV_EXCLUDE_NEWER`. |
| M11 | **The app can be relaunched inside a network cut.** | Electron 43.3.0 (the fork's), as a non-root user, inside `unshare --map-root-user -n` with `--no-sandbox` under Xvfb: opens a window and loads a page it serves on 127.0.0.1 there. |
| M12 | **The cutoff resolves both commands.** | At `2026-10-04T00:00:00Z`: the agent-server gets litellm 1.104.0, pydantic 2.13.5, starlette 1.7.0, posthog 6.9.3, fastapi 0.142.2; `openhands-automation` 1.16.0 was uploaded 2026-09-30T20:43Z. |

So F4 of TASK-48 holds, and is wider than it said: past ten minutes, a launch either fails offline (M2) or, online,
installs whatever PyPI released since (M7). D5's README sentence is false both ways.

---

## 2 · Decisions

| # | Decision | Why | Rejected |
|---|---|---|---|
| K1 | **The cutoff is `uv.excludeNewer` in the Canvas fork's `config/defaults.json`, `null` there, filled into `OH_UV_EXCLUDE_NEWER` by `launcherDefaultsEnv` when the environment leaves it unset. Our build writes it from `desktop/pins.toml` `[app] uv_exclude_newer`.** | The rule: the fork behaves as upstream with the key `null`, and our build turns it on. `launcher-defaults.mjs`'s contract is that each key is a fallback for a variable and the builders read only the env they are given, so tests pass their own env (DEVELOPMENT.md, "Building from a fork"). A variable lets CI pin a run without patching the file (§4.4). An `OH_` name is read by no uv; it reaches conversations' terminals as a harmless string. | `UV_EXCLUDE_NEWER` in the stack's environment (the launcher passes its environment to the agent-server, so every terminal and a cell's own `uv pip install` would be pinned: TASK-48's warning). The value committed in the fork (a fork tag per date bump). The builders reading the file. |
| K2 | **Its form is RFC 3339 in UTC to the second, `YYYY-MM-DDTHH:MM:SSZ`, and a real instant.** Both repos refuse anything else, naming the key. | M1: a date shifts with the user's time zone by up to 25 h; a span moves with the clock and 0.8.17 refuses it. A Z time is read the same by both uv versions. | A date (the task row's word, kept as "the day, at 00:00:00Z"). An offset other than Z (same instant, but two spellings to compare). |
| K3 | **The cutoff moves with the pins, in the same commit, to 00:00:00Z of a day no later than that commit's; or alone, for a dependency fix. Either way only when `cross-repo.yml` is green on it and the fork's mock-LLM suite, dispatched at it (§4.4), fails no test it did not fail at the current cutoff.** Whoever moves the pins moves it. **The first value is `2026-10-04T00:00:00Z`**: the fork's mock-LLM suite failed only its long-known five or six tests in the runs of Oct 3–4 (37148195621 … 37228664565), and ten today. | E12 does not exercise the Canvas features behind the four mock-LLM tests that broke this month with no code change, while the stack re-resolved (the mock venv went litellm 1.103.3 → 1.106.0, pydantic 2.13.5 → 2.14.1, starlette 1.7.0 → 1.9.0; runs 39200977080 and 39202793031); a cutoff of "today" would pin that set in. Never past the bump's day: a later cutoff could admit packages nobody tested. | Moving it at every build (no pin at all). A bot that bumps it (no test of the new set). |
| K4 | **Every `uvx` the two builders return gets `--exclude-newer <cutoff>` first; starting from the cache applies only in `dev-with-automation.mjs`'s two starters, and only to commands with a fixed source:** a PyPI version, or a full 40-hex commit. | Those are the starts the app, the browser version and `npm run dev` make. A branch, a tag, an abbreviated SHA (`--reinstall`), the automation's git ref (`--refresh`) and a local checkout are fetched or rebuilt on purpose, so they stay online. `dev-safe.mjs`'s and `dev-extra-backend.mjs`'s own `main()` get the cutoff through the builder and start online, as today. | Applying the cache start to every launcher (two more call sites, for developer tools that never run in the app). |
| K5 | **Offline first, gated by a record:** a start runs `uvx --offline …` when an online start of the same requirement args has served before **and** `uvx --offline <requirement args> python -c pass` exits 0; otherwise it starts as built, online, exactly as today, and is recorded once it serves. | M5: a known start costs a 0.3–0.6 s probe and never touches the network, so it is immune to M3's hang. M6: without the record, a moved cutoff would never take effect on a machine whose cached answers predate it; the requirement args include `--exclude-newer <cutoff>`, so a new cutoff, SDK commit or automation version is a new record, and its first start is online. The probe notices a cleared or pruned cache and goes online instead of failing. | **Online first, retrying offline** (M2, M3: +1–5 s on every offline start, +49–123 s when the network hangs, and a retry that cannot tell uv's failure from the service's; the automation backend has no readiness wait to retry on). **Offline first, falling back online** (M6). An online install step before every start (M3's cost again). |
| K6 | **The record is a file, `<state dir>/uvx-starts/<sha256 hex of JSON.stringify(requirementArgs)>`, written when the service first answers after an online start** (agent-server `GET /server_info`, automation `GET /health`), by a poll the launcher does not wait on. One owner, `scripts/uvx-start.mjs`; the launcher never deletes one. | A start that served resolved online with answers at most ten minutes old, so its cached environment is the cutoff's resolution. A missing directory (first launch, an upgrade to this launcher, a deleted state dir) or an unwritable one means "start online": a valid state with no migration, as the fork's AGENTS.md checklist asks. One small file per requirement set, so a release adds two. | One JSON file (read-modify-write). Recording when the process spawns (it may fail resolving). |
| K7 | **What the user sees** is §3.6: one more line on a cache start, the cutoff on the existing source line, and nothing new on any other path. | The splash streams service lines (`onServiceLog`), so a start that skips the network should say so; the install path already speaks through uv's own output. | A line per probe outcome. |
| K8 | **Tests expire uv's answers by ageing them in place** (M8), in E12, in TASK-48's E13 claim 9, and (format-independent) through a `max-age=1` local index in the fork's live test; each ageing is checked by a negative control. | No ten-minute waits. Deleting `simple-v*` makes the offline path fail too (M8), so a test built on it can never pass. | Waiting 600 s. `faketime` (would reach Electron and every process). |
| K9 | **An index without upload times is a documented limit, with no fallback** (M9). | Retrying without the cutoff would bring back drift silently, for exactly the users who cannot see it. The README says so (§4.3). | A fallback to no cutoff. |

**Divergences from the task as approved.** (1) A pinned start runs from the cache whenever it can, not only when
offline (K5): online-first is what fails slowly. (2) The task row speaks of a fresh install; the cutoff also stops
the drift on every later launch (M7). (3) "A date" is a UTC time (K2). (4) Three additions the evidence called for:
E12 checks the automation backend (it never did, so a cutoff older than `versions.automation` would ship a broken
backend with E12 green), the fork's mock-LLM workflow takes the cutoff as a dispatch input, and deep-reasoning's
`canvas-replay` runs at the cutoff (§4.4).

---

## 3 · Canvas fork: branch `feat/uv-exclude-newer`, cut from `dr-3`

The fork's AGENTS.md binds it. Local backend only (the npm and desktop launchers); Docker ignores the key (it runs
no uvx) and Cloud is untouched. No agent-server contract changes, so `compatibility.minimumAgentServer` stays.

### 3.1 `config/defaults.json`

A block after `sources`:

```json
  "uv": {
    "_comment": "Optional, for the npm and desktop launchers (scripts/launcher-defaults.mjs; Docker ignores it). excludeNewer is a UTC time such as 2026-10-04T00:00:00Z. Set, every uvx the launchers run gets --exclude-newer with it, so the agent-server's and the automation backend's PyPI dependencies resolve as PyPI was then, and a start whose source is pinned (a PyPI version or a full commit) runs from uv's cache with --offline once an online start of it has served, so it needs no network however long since uv last asked the index. Fallback for OH_UV_EXCLUDE_NEWER. null means unset: the newest packages, resolved online on every launch, as upstream.",
    "excludeNewer": null
  },
```

### 3.2 `scripts/launcher-defaults.mjs`

The header's table gains `uv.excludeNewer -> OH_UV_EXCLUDE_NEWER`. `launcherDefaultsEnv` validates the key whether
or not the environment wins (as for the others) and fills `OH_UV_EXCLUDE_NEWER` only when `env` leaves it unset.

```js
/**
 * Accept a UTC time to the second that is a real instant (2026-10-04T00:00:00Z); reject anything else, a date or
 * a span among them: uv reads a date in the user's own time zone and a span relative to now.
 * @param {unknown} value
 * @param {string} name  "OH_UV_EXCLUDE_NEWER" or "uv.excludeNewer in config/defaults.json"
 * @returns {string} the value
 * @throws {Error} `${name} must be a UTC time such as 2026-10-04T00:00:00Z, got: ${value}`
 */
export function validateExcludeNewer(value, name)
// /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/ and new Date(value).toISOString() === value.replace("Z", ".000Z")
```

### 3.3 The builders

Both keep their names and arguments, and with `OH_UV_EXCLUDE_NEWER` unset return exactly what they return today,
plus `requirementArgs: null`. With it set (non-empty; validated with `validateExcludeNewer`, name
`OH_UV_EXCLUDE_NEWER`):

```js
/**
 * @typedef {object} UvxCommand
 * @property {string} command   "uvx"; "uv" for the automation's local checkout
 * @property {string[]} args    today's, with ["--exclude-newer", cutoff] first when a cutoff is set and command is "uvx"
 * @property {string} source    today's, with `, PyPI as of ${cutoff}` appended when it is set
 * @property {string[] | null} requirementArgs  args before the executable ("agent-server", "uvicorn"), so the uv
 *   options and every --from/--with, --exclude-newer included; null unless a cutoff is set and the source is
 *   fixed (K4)
 */
export function buildAgentServerCommand(env = process.env)   // scripts/dev-safe.mjs
function buildAutomationCommand(env = process.env)           // scripts/dev-with-automation.mjs, already exported
```

| Mode | `--exclude-newer` | `requirementArgs` |
|---|---|---|
| agent-server: PyPI default, `OH_AGENT_SERVER_VERSION`, a full-commit `OH_AGENT_SERVER_GIT_REF` | yes | `args.slice(0, args.indexOf("agent-server"))` |
| agent-server: any other ref (`--reinstall`), `OH_AGENT_SERVER_LOCAL_PATH` | yes | null |
| automation: default, `OH_AUTOMATION_VERSION` | yes | `args.slice(0, args.indexOf("uvicorn"))` |
| automation: `OH_AUTOMATION_GIT_REF` (`--refresh`) | yes | null |
| automation: `OH_AUTOMATION_LOCAL_PATH` (`uv run --project`) | no | null |

### 3.4 `scripts/uvx-start.mjs` (new, Node built-ins only, like `launcher-defaults.mjs`)

```js
export const RECORDS_DIR = "uvx-starts";          // under the state directory
export const PROBE_TIMEOUT_MS = 120_000;          // offline, so only a slow disk takes long
export const RECORD_DEADLINE_MS = 15 * 60_000;
export const STARTING_OFFLINE = "Starting from uv's cache, offline";

/**
 * @typedef {object} UvxStart
 * @property {string} command
 * @property {string[]} args             ["--offline", ...cmd.args] when offline, else cmd.args
 * @property {boolean} offline
 * @property {boolean} recordOnceServing  an online start of a pinned command: record it once it serves
 */

/** <stateDir>/uvx-starts/<sha256 hex of JSON.stringify(requirementArgs)>. */
export function recordPath(stateDir, requirementArgs)

/**
 * The exit code of `uvx --offline ...requirementArgs python -c pass`, spawned as services are
 * (resolveWindowsCommand, no shell) with env and cwd, output discarded; null when it could not spawn or ran past
 * timeoutMs, in which case it is killed.
 * @returns {Promise<number | null>}
 */
export function probeUvCache(requirementArgs, { env, cwd, timeoutMs = PROBE_TIMEOUT_MS })

/**
 * How to start cmd (K5): requirementArgs null → as built, nothing probed; a record and a probe exiting 0 →
 * offline; otherwise → as built with recordOnceServing. env and cwd are the service's own, since uv reads its
 * settings from both.
 * @param {import("./dev-safe.mjs").UvxCommand} cmd
 * @param {{ stateDir: string, env: Record<string, string | undefined>, cwd: string,
 *           probe?: typeof probeUvCache }} options
 * @returns {Promise<UvxStart>}
 */
export async function planUvxStart(cmd, { stateDir, env, cwd, probe = probeUvCache })

/** Writes the record, {"requirementArgs": [...], "servedAt": now.toISOString()}; false, and nothing logged, when it cannot. */
export function recordUvxStart(stateDir, requirementArgs, now = new Date())

/**
 * Polls url every intervalMs until it answers 2xx, then recordUvxStart; stops without a record when proc exits
 * first or after deadlineMs. Never rejects.
 * @returns {Promise<boolean>} whether it recorded
 */
export async function recordOnceServing(stateDir, requirementArgs, url, proc,
  { intervalMs = 1000, deadlineMs = RECORD_DEADLINE_MS, fetchImpl = fetch } = {})
```

### 3.5 `scripts/dev-with-automation.mjs`: the two starters

`startAgentServer(config)` and `startAutomationBackend(config)` become `async`; `main()` awaits both
(`await agentServerStarter(config)`, so the `startAgentServer` option may still return a process). Each, after its
`Using …` line:

1. `start = await planUvxStart(cmd, { stateDir: config.stateDir, env: { ...process.env, ...<the service's env> },
   cwd: <the service's cwd> })` (agent-server: `safeConfig.workspacesPath`; automation: `config.stateDir`);
2. `if (shuttingDown) return new Promise(() => {})`, the setup phase's idiom (`:1403`), so a quit during the probe
   spawns nothing;
3. `if (start.offline) logServiceEvent(name, STARTING_OFFLINE, c.dim)`;
4. `spawnService(name, start.command, [...start.args, "--host", …], …)` as today;
5. `if (start.recordOnceServing) recordOnceServing(config.stateDir, cmd.requirementArgs, url, proc)`, not awaited:
   `${getAgentServerBaseUrl(config)}/server_info`, or `http://127.0.0.1:${config.autoBackendPort}/health`.

A quit during the probe leaves the probe to finish by itself (offline, under a second).

### 3.6 What the user sees (verbatim; tests assert these)

| Start | Today | With the cutoff set |
|---|---|---|
| any | `[agent-server] Using git (michaeltheologitis/software-agent-sdk@<full ref>)` | the same, then `, PyPI as of 2026-10-04T00:00:00Z`; likewise the automation's `Using PyPI (1.16.0, default)` |
| first, or the first after an update or a cleared cache | uv's install output | the same |
| every later one | online: possibly an install of new releases (M7); offline past ten minutes: `exited before startup completed (code=2)` | `[agent-server] Starting from uv's cache, offline` and `[automation] Starting from uv's cache, offline`, then the services' own lines |
| a bad value | — | the launch fails, as for the other keys: `uv.excludeNewer in config/defaults.json must be a UTC time such as 2026-10-04T00:00:00Z, got: 2026-10-04` (or `OH_UV_EXCLUDE_NEWER must be …`) |

### 3.7 Docs

`docs/DEVELOPMENT.md` "Building from a fork": the example and the table gain `uv.excludeNewer` →
`OH_UV_EXCLUDE_NEWER` ("the variable is unset; a UTC time such as 2026-10-04T00:00:00Z"), and the sentence "Pin the
ref to a full commit SHA so relaunches need no network" gains ", and set `uv.excludeNewer`: without it uv asks
PyPI again ten minutes after it last did". `.agents/skills/local-stack-runtime/references/guide.md:97` lists the key.

---

## 4 · deep-reasoning: on `ux-round`, after the UX round's commits

### 4.1 `desktop/pins.toml` and `desktop/build.py`

```toml
[app]
# PyPI as of this UTC time, for the agent-server's and automation's uvx (TASK-66 K3): moved with the pins, or
# alone for a dependency fix, never past the day of the commit that moves it, and only on a green cross-repo.yml.
uv_exclude_newer = "2026-10-04T00:00:00Z"
```

```python
UTC_TIME: Final = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")

@dataclass(frozen=True)
class AppPin:            # + uv_exclude_newer: str
    ...

def load_pins(path: Path) -> Pins:
    """Raises ValueError naming the key for a commit that is not 40 hex, or an app.uv_exclude_newer that is not
    UTC_TIME and an instant datetime.fromisoformat accepts."""

def fork_lacks_cutoff(canvas_tag: str) -> str: ...                        # check 5c, §4.2

def patch_defaults(defaults: Mapping[str, Any], *, state_dir: str, command: list[str],
                   exclude_newer: str) -> dict[str, Any]:
    """§4.2.3's keys, the UX round's agent.lockedProfile, and uv.excludeNewer = exclude_newer; every other key
    unchanged."""

# check_pins: signature unchanged. Check 5: + "uv.excludeNewer" in the keys the fork must leave null
# (fork_sets_ours, unchanged). Check 5c (new): the Canvas checkout's defaults.json has a "uv" object holding the
# key "excludeNewer", else fork_lacks_cutoff(canvas_pin.tag): Canvas dr-3 ignores an unknown key, so without 5c a
# build pinned to it would write the cutoff and ship an unpinned app with every check green (the UX round's 5b
# reasoning).
# build() (TASK-48: prepare()): patch_defaults(..., exclude_newer=pins.app.uv_exclude_newer)
```

### 4.2 Sentences (verbatim)

| Name | Sentence |
|---|---|
| `fork_lacks_cutoff(canvas_tag)` | `✗ Canvas fork {canvas_tag}'s config/defaults.json has no uv.excludeNewer, so it cannot pin the app's PyPI packages or start them offline: pin dr-4 or later.` |
| `load_pins`' `ValueError` | `{path}: app.uv_exclude_newer must be a UTC time such as 2026-10-04T00:00:00Z, not {value!r}` |

### 4.3 The README (verbatim)

In "The first launch", D5's two sentences (README:97–98 at `9e8109e`, wherever the UX round's rewrite keeps them)
become:

> A later launch with nothing changed installs nothing and needs no network, however long since the last one: the
> agent-server and the automation service beside it start from uv's cache, offline. Their Python packages are the
> versions PyPI had on a date each release fixes, so a new release of one of them changes nothing you run. After an
> update, setup and the agent-server install once more.
>
> If your uv installs from an index other than PyPI (`index-url` in a `uv.toml`, or `UV_INDEX_URL`), that index
> must publish when each file was uploaded, as PyPI does; without that, the agent-server cannot install.

"What you need"'s "**The network**, on the first launch and the first launch after an update." stays: it is now true.

### 4.4 CI

- **deep-reasoning `cross-repo.yml` `canvas-replay`** (E6 runs the fork's mock-LLM stack): the pins step also
  writes `OH_UV_EXCLUDE_NEWER=<[app] uv_exclude_newer>` to `$GITHUB_ENV`; the mock LLM's venv and the automation
  pre-warm pass `--exclude-newer "$OH_UV_EXCLUDE_NEWER"`, so the pre-warm fills the very environment the launcher's
  start resolves. The stack picks the variable up once the Canvas pin is `dr-4`; at `dr-3` it is ignored.
- **Canvas fork `mock-llm-e2e.yml`**: `workflow_dispatch.inputs.uv_exclude_newer` (description "Resolve PyPI as of
  this UTC time, e.g. 2026-10-04T00:00:00Z; empty: the newest, as upstream", default `""`) → job env
  `OH_UV_EXCLUDE_NEWER`; the venv and pre-warm steps add `${OH_UV_EXCLUDE_NEWER:+--exclude-newer
  "$OH_UV_EXCLUDE_NEWER"}`. Empty is unset everywhere (`launcherDefaultsEnv` and the builders test truthiness).
  This is K3's instrument.

---

## 5 · Tests

No test calls a model. Each name states the property it pins.

### 5.1 Canvas fork (vitest, default suite)

- `__tests__/scripts/launcher-defaults.test.ts`:
  - `uv.excludeNewer fills OH_UV_EXCLUDE_NEWER when the environment leaves it unset`;
  - `an OH_UV_EXCLUDE_NEWER in the environment wins over uv.excludeNewer`;
  - `a uv.excludeNewer that is not a UTC time fails every launch, naming the key`, each of `2026-10-04`,
    `2026-10-04T00:00:00+02:00`, `1 week`, `2026-02-30T00:00:00Z`, `""`, `20261004`.
- `__tests__/scripts/dev-safe.test.ts` (`buildAgentServerCommand`):
  - every existing case unchanged, plus `requirementArgs` null (upstream's command is untouched);
  - `a cutoff goes first on the command in every mode, and on the source line` (the four modes);
  - `a pinned source can start from the cache: its requirement args are everything before agent-server` (PyPI
    default, version, full commit);
  - `a moving ref or a local checkout never starts from the cache` (branch, tag, short SHA, local path: null);
  - `rejects an OH_UV_EXCLUDE_NEWER that is not a UTC time`.
- `__tests__/scripts/dev-with-automation.test.ts` (`buildAutomationCommand`): the same four kinds of case; the
  local checkout's `uv run` gets no flag.
- `__tests__/scripts/uvx-start.test.ts` (new):
  - `a command that cannot start offline is started as built and nothing is probed` (the probe stub must not run);
  - `a command no online start has served is started as built, to be recorded once it serves`;
  - `a recorded command whose environment is in uv's cache starts with --offline first`;
  - `a recorded command uv's cache no longer holds is started as built` (probe stub exits 1);
  - `a new cutoff is a new record` (recorded at one cutoff, planned at another: as built);
  - `the probe runs uvx --offline with the requirement args and python -c pass, in the service's env and cwd`
    (a fake `uvx` on `PATH`, a Node script that writes its argv, cwd and one variable to a file; the real spawn);
  - `a probe that outlives its timeout counts as not cached, and is killed` (a fake `uvx` that sleeps; 200 ms);
  - `a start is recorded once its URL answers, and not when its process exits first` (a local HTTP server; an
    `EventEmitter` standing for the process);
  - `a record that cannot be written costs only an online start next time` (a read-only state dir: no throw).

### 5.2 Canvas fork, live (`agent-server-relaunch.live.test.ts`, `OH_AGENT_SERVER_LIVE=1`, `launcher-live.yml`)

A second case, `with a cutoff, a pinned commit starts with the network cut once uv's index answers have expired`:
a local index in the test (a Node HTTP server forwarding `/simple/<name>/` to PyPI with `Cache-Control: max-age=1`)
as `UV_DEFAULT_INDEX` in the probe's env, `OH_UV_EXCLUDE_NEWER` set; the first launch through `planUvxStart` (as
built, `recordOnceServing`) answers, and `recordUvxStart` runs as the starter would; 2 s later, with the network
cut, the command as built does **not** answer (the negative control: the answers have expired), and the plan's
`--offline` command does. Format-independent, so it holds for upstream's uv too.

### 5.3 deep-reasoning, default suite (`tests/desktop/test_build.py`)

- the fake Canvas `defaults.json` gains `"uv": {"excludeNewer": null}`;
- `test_defaults_gain_only_the_builds_five_keys` (the UX round's name) becomes `…_six_keys`, with `uv.excludeNewer`;
- `test_a_fork_that_carries_our_values_is_refused` gains `uv.excludeNewer`;
- new `test_a_canvas_fork_that_cannot_pin_pypi_is_refused` (no `uv` object: `fork_lacks_cutoff("dr-1")`);
- new `test_a_cutoff_that_is_not_a_utc_time_is_refused` (`load_pins`, K2's cases);
- `test_the_committed_pins_load` asserts `pins.app.uv_exclude_newer == "2026-10-04T00:00:00Z"`, so a typo must be
  made twice.

### 5.4 deep-reasoning, E12 (`tests/desktop/test_e12.py`, `desktop-e2e`)

`tests/desktop/app.py` gains:

```python
NETWORK_CUT: Final = ["unshare", "--map-root-user", "-n", "sh", "-c", 'ip link set lo up && exec "$@"', "offline"]
# moved from test_setup_relaunches_offline_from_its_cache_and_installs_nothing, which uses it unchanged

@dataclass
class LaunchedApp:       # + started_at: float, time.time() at the Popen
    ...

def launch(home: Path, log: Path, *, network: bool = True) -> LaunchedApp:
    """network=False runs the app inside NETWORK_CUT with --no-sandbox (Chromium refuses the mapped root
    otherwise; M11) and no DevTools port, which the cut would hide."""

def age_uv_index_answers(cache: Path, since: float, seconds: int) -> int:
    """Move every index answer under cache/simple-v* back by seconds, as if uv had fetched it then (M8): each u64 in
    an answer's last 512 bytes between since and now. The number aged; AssertionError naming the answers in which
    it found no such time, since then this uv keeps them otherwise and nothing was aged."""
```

Two tests:

- `test_the_automation_backend_answers_after_the_first_launch`, right after the first-launch test:
  `GET http://127.0.0.1:<defaults ports.automation>/health` is 200 within 120 s. *Falsified by* a cutoff older than
  `versions.automation`'s release, or any automation install failure, which nothing caught before.
- `test_the_app_relaunches_offline_an_hour_after_uv_last_asked_pypi`, last, after the offline setup test:
  1. `age_uv_index_answers(home/.cache/uv, app.started_at - 60, 3600)`;
  2. the negative control, with the app's own uv (`resources/bin/uvx`) inside `NETWORK_CUT`:
     `uvx --exclude-newer <defaults uv.excludeNewer> --from openhands-automation==<defaults versions.automation>
     python -c pass` exits non-zero, and the same with `--offline` exits 0;
  3. `launch(home, log, network=False)`; within 180 s the log has `[agent-server] Ready at`; it has
     `[agent-server] Starting from uv's cache, offline`, `[automation] Starting from uv's cache, offline` and an
     `[automation]` line holding `Application startup complete` (uvicorn's, in the backend's JSON log line; 17 s
     into an offline start here); no `installing deep-reasoning`, no `[desktop] Startup failed`. The ports are
     inside the cut, so the test reads the log, not `/health`;
  4. SIGTERM; it exits within `QUIT_S` and nothing names the HOME. The duration is printed for `-rA`.

  *Falsified by* the fork without TASK-66 (step 3 fails: the agent-server exits 2), a build that did not write the
  cutoff (no cache line), or an ageing that aged nothing (step 2 fails).

### 5.5 TASK-48's E13 claim 9: what flips

TASK-48 §7.4 claim 9 deletes `~/.cache/uv/simple-v*` "as if expired". M8 shows that makes the offline path fail
too, so the claim would stay XFAIL after this task and prove nothing. **It must age instead:**
`age_uv_index_answers(home / ".cache" / "uv", <first start's time> - 60, 3600)` (E13's HOME has no
`UV_CACHE_DIR`: `RUNNER_ONLY` removes it). With that change, `test_an_offline_restart_once_uvs_index_answers_have_
expired` XFAILs while the Canvas pin is `dr-3`, and XPASSes, which `strict=True` turns into a failure, at the first
commit whose Canvas pin is `dr-4` (or later) **and** whose `patch_defaults` writes `uv.excludeNewer`. That commit
deletes the mark. If TASK-48 lands after this task, it writes claim 9 with the ageing and without the mark.

---

## 6 · Seams and merge order

**Canvas fork.** `feat/uv-exclude-newer`, from `dr-3`, merges into `deep-reasoning` before Michael tags `dr-4`,
beside the UX round's `feat/agent-lock`, `fix/subagent-costs-on-by-default` and `chore/wire-sdk-dr-3`. The UX round
touches no launcher script, so the only shared files are `config/defaults.json` (its `agent` block, the designer's
`branding.appTitle`, our `uv` block: three adjacent blocks, a textual merge) and possibly `docs/DEVELOPMENT.md`'s
table. A `dr-4` cut without this branch fails check 5c.

**deep-reasoning `ux-round`**, after the UX round's commits:

| Touch point | The UX round | TASK-66 |
|---|---|---|
| `patch_defaults` | fifth key `agent.lockedProfile` (and `branding.appTitle`, if its designer writes it here) | a required `exclude_newer` keyword and one more key; its one call site (`build()`, or TASK-48's `prepare()`) and the tests' calls pass it |
| `check_pins` | check 5 + `agent.lockedProfile`; check 5b | check 5 + `uv.excludeNewer`; check 5c, beside 5b. Whoever writes second may fold 5b and 5c into one "the fork declares every key the build writes" check; not required |
| `pins.toml` | Canvas `dr-4`, SDK `dr-3`, in one commit | `uv_exclude_newer`, in that commit or the one after; E13's mark goes in whichever is second (§5.5) |
| `--canvas-commit` / `--sdk-commit`, the dispatch inputs | new build overrides | the cutoff is not overridden by them: a run at another cutoff edits `pins.toml` on a branch |
| `cross-repo.yml` | paths, the `live` input | `canvas-replay`'s pins step and two install lines: a textual merge |
| E12, `tests/desktop/app.py` | rewrites onboarding and notice steps | two tests (one after the first launch, one last), `NETWORK_CUT`, `launch(network=)`, `started_at`, `age_uv_index_answers` |
| README | rewrites "The first launch", heading kept | §4.3's paragraphs, in place of the two sentences wherever the rewrite left them |

**TASK-48 (`task-48-browser`).** `web.mjs`'s W8 removes a terminal's `OH_UV_EXCLUDE_NEWER` with every `OH_*`, so
`defaults.json`'s value rules, as in the app. Its `prepare()` passes `exclude_newer`. Its E13 claim 9 changes as
§5.5 says, using the helper here (it moves E12's helpers into `tests/desktop/app.py` too: a textual merge). Its §9
P1 is this task, offline-first rather than "retry once with `--offline`" (K5).

## 7 · What this makes stale

- **D5 design v3** §4.2.3 (the keys the build writes: + `uv.excludeNewer`), §4.2.2 check 5 (+ the key, + 5c), and
  the README sentence it wrote (§4.3).
- **TASK-48 design v1** F2/F4's "as if expired: uv then needs the index either way" (M8: not for `--offline`),
  §7.4 claim 9's simulation (§5.5), §9 P1's mechanism.
- **The UX round's design** §4.1 "a fifth key" (now six) and check 5's list.
- **The fork's** `docs/DEVELOPMENT.md` and the local-stack skill guide (§3.7, in this task).

## 8 · Size

| Part | Production | Tests |
|---|---|---|
| Fork: `defaults.json`, `launcher-defaults.mjs`, the builders | ≈ 50 | ≈ 120 |
| Fork: `uvx-start.mjs`, the starters | ≈ 110 | ≈ 150 |
| Fork: live test, `mock-llm-e2e.yml`, docs | ≈ 25 | ≈ 70 |
| deep-reasoning: `pins.toml`, `build.py`, README, `cross-repo.yml` | ≈ 35 | ≈ 45 |
| deep-reasoning: E12, `app.py` | — | ≈ 110 |
| **Total** | **≈ 220** | **≈ 495**, so **≈ 0.7k, about 2.5 h at Gate C** |

## 9 · Open items, and what I was unsure about

1. **The first cutoff** rests on the Conductor's reading that four of the ten failures are drift. The Implementer
   dispatches the fork's mock-LLM suite with `uv_exclude_newer=2026-10-04T00:00:00Z` on the fork branch: the
   long-known failures alone confirm it; the four as well mean they are not drift, and the value stays anyway (it
   still pins).
2. **Ageing depends on uv's cache layout** (u64 Unix seconds at the end of each answer), measured for 0.8.17 and
   0.12.23 only. The helper fails when it finds no fetch time, and E12's negative control fails when ageing has
   no effect, so a uv bump that changes the layout fails loudly, not silently.
3. **Electron inside the cut on the runner** (M11) was measured here as `nobody`, not as GitHub's `runner`; E12's
   existing offline test already needs the AppArmor sysctl the workflow sets.
4. **Mirrors without upload times** (M9): how many users have one is unknown; the README says what fails.
5. **Pinned dependencies get no security fixes** between cutoff moves; K3 allows a cutoff-only move for that.
6. The probe adds 0.3–0.6 s to every pinned start (M5); it is what notices a cleared cache.
7. A record is per state directory, uv's cache is per user: two apps sharing uv's cache each go online once, which
   is correct, only slower.
8. Windows: the probe spawns as services do (`resolveWindowsCommand`), unmeasured there; the fork supports it, our
   app does not.
