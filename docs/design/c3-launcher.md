# C3 · Desktop launcher: the agent-server's source and a first-launch setup (design)

**TASK-11** · System Designer · code lands in the Canvas fork
[michaeltheologitis/OpenHands](https://github.com/michaeltheologitis/OpenHands), branch
`feat/launcher-agent-server-source`, one pull request · against the approved spec
[TASK-1](https://app.notion.com/p/3ed62fb22237814ab425c81b3844f012) (C3 in full; D5, §2 and §4 for what consumes it).
**Pinned against:** Canvas fork `deep-reasoning` at `02b7ac7` (upstream `1ff45c2` plus the ASE commit; every
`file:line` below is from it) · SDK fork `deep-reasoning` at `91430aa` (used in the measurements) · uv 0.8.17,
git 2.43, Node 22 (the measurements in §2.3).

**Revisions** (newest first; the Gate B reader approved the previous version, so each line says which sentences
to stop trusting):
- 2026-10-02 · v1 · first full-depth version.

**Where this file lives, and why nothing trips over it.** `docs/design/c3-launcher.md` on deep-reasoning's
branch `design/c3`, because no design doc goes into the fork (the fork carries only upstream-shaped code). This
branch has no docs site, no test runner and no package, so nothing collects the file. When the PR is opened in the
fork, upstream's own review aid for a non-trivial PR is a `.pr/` HTML page (`.agents/skills/pr-design-doc`) that
is deleted before merge; that page is the Implementer's, optional, and is not this document.

**Reading guide.** Gate B: §1 and §2 (about 15 minutes); §2.7 lists every departure from the approved spec.
D5 designs against §4, which is its contract. The wiring commit reads §4.5. The Implementer reads everything;
§6 is the signature index and §7 the tests.

---

## 1 · What C3 changes, and why

### 1.1 How the launcher chooses the agent-server today

Every npm and desktop launcher builds the agent-server's command with `buildAgentServerCommand(env)`
(`scripts/dev-safe.mjs:429–528`). It reads four sources from the environment, highest first:

| Source | Variable | Command | A relaunch needs the network |
| --- | --- | --- | --- |
| local checkout | `OH_AGENT_SERVER_LOCAL_PATH` | `uvx --reinstall --from <path>/openhands-agent-server --with-editable …` | rebuilds every launch (not measured offline) |
| git ref | `OH_AGENT_SERVER_GIT_REF` | `uvx --reinstall --from git+https://github.com/OpenHands/software-agent-sdk@<ref>#subdirectory=…` | **yes** (measured, §2.3) |
| PyPI version | `OH_AGENT_SERVER_VERSION` | `uvx --from openhands-agent-server==<v> --with …` | no, once cached (measured) |
| default | `config/defaults.json` `versions.agentServer` | the same, at `1.50.1` | no, once cached |

The git URL is the constant `AGENT_SERVER_GIT_REPO` (`dev-safe.mjs:49`). The automation backend beside it already
takes a repository, `OH_AUTOMATION_REPO` and `--automation-repo` (`scripts/dev-with-automation.mjs:197, 328,
406–407`). The desktop app (`electron/main.mjs`) puts its bundled `uv` and Node on `PATH` and calls `main()` of
`dev-with-automation.mjs` with options only (`startStack`, `electron/main.mjs:643–679`); started from Finder or a
desktop launcher it sees none of the user's shell variables.

State lives in `~/.openhands/agent-canvas` unless `OH_CANVAS_SAFE_STATE_DIR` is set (`dev-safe.mjs:643–647`,
`dev-with-automation.mjs:469–471`). The agent-server is told `OH_PERSISTENCE_DIR = dirname(stateDir)`
(`dev-safe.mjs:819`), so the state directory's **parent** holds everything the agent-server and SDK persist:
settings, secrets, workspaces, agent and LLM profiles, installed Canvas Apps and their backends, skills, plugins,
hooks (`openhands/sdk/utils/path.py:32`, `agent_server/persistence/store.py:802–821`,
`canvas_extensions/installed.py:47`). The automation database sits beside it at
`dirname(stateDir)/automation/automations.db`. The two key files stay at `~/.openhands/agent-canvas/{api-key,
secret-key}.txt` whatever the state directory is (`dev-safe.mjs:80–101`), unless `OH_SESSION_API_KEY_PATH` and
`OH_SECRET_KEY_PATH` move them.

### 1.2 What is wrong for a build that ships a fork of the SDK

1. **The repository is fixed.** A git ref can only name upstream's repository, so a build cannot run a fork.
2. **A packaged app reads no environment.** Even with a repository variable, a desktop build launched from Finder
   could not set it: the build needs a place in the app itself.
3. **Every git launch reinstalls.** `--reinstall` "implies `--refresh`" (uv's help), so each launch fetches and
   rebuilds the four packages: it needs the network and takes as long as a first install.
4. **No hook for a first-launch setup.** A build that must install something as the user (D5 installs deep-reasoning
   with the user's own GitHub access, then registers an App and an agent profile through the agent-server) has
   nowhere to run it, and nothing that stops the launch when it fails.

### 1.3 The change, in one paragraph

`OH_AGENT_SERVER_GIT_REPO` joins the agent-server's source variables, mirroring `OH_AUTOMATION_REPO`. A git ref
that is a full commit SHA is installed without `--reinstall`, so a later launch runs uv's cached build of that
commit and needs no network; any other ref behaves as today. `config/defaults.json` gains three optional blocks:
`sources` (the agent-server's repository and ref), `paths.stateDir`, and `setup` (an argv command and the phases
it runs in). They are applied once, at each launcher's entry, as fallbacks for the environment variables of the
same meaning, so environment variables still win and everything downstream sees one set of values. The setup
command runs as the user before the stack starts (`before-start`) and again once the agent-server answers
`/server_info` (`after-ready`, with `AGENT_SERVER_URL` and `SESSION_API_KEY` in its environment); a non-zero
exit, a failure to start or a timeout stops the launch with its output in the startup log. Upstream's
`defaults.json` carries the new keys as `null`, so upstream behaves exactly as before.

### 1.4 What C3 is not

- Nothing deep_reasoner-specific: no names, paths or commands of ours enter the fork in this PR. The fork's values
  arrive later, in the wiring commit (the SDK fork's repository and commit) and in D5's build (state directory and
  setup command); §4.5.
- No change to the Docker image: `docker/entrypoint.sh` keeps its own layout (`paths.stateSubdir`), and the new
  keys are not emitted into its generated `defaults.env` (`docker/Dockerfile:50–70`).
- No new CLI flag (§2.7, item 4), no new workflow in the PR (§7.5), no change to `electron-builder.config.mjs`.

---

## 2 · Decisions, with the reasoning

### 2.1 `config/defaults.json` is an environment fallback, applied once at each launcher's entry

**Decision.** A new dependency-free module, `scripts/launcher-defaults.mjs`, turns the new keys into environment
entries that are added to `process.env` only where the variable is unset. Each launcher's `main()` calls it once,
first: `dev-with-automation.mjs` (the desktop app, `npm run dev`, the `agent-canvas` npm bin), `dev-safe.mjs`
(`dev:minimal`), `dev-static.mjs` and `dev-extra-backend.mjs`. `buildAgentServerCommand(env)`,
`buildSafeDevConfig(cwd, env)` and every other function keep reading only the `env` they are given.

**Why.**
- *Environment variables still win, variable by variable*, as the spec requires, with no second precedence rule
  to read: after the fill, the existing precedence in `buildAgentServerCommand` decides.
- *Upstream's suite stays green in our fork after the wiring commit.* Upstream's tests call
  `buildAgentServerCommand({})` and expect PyPI 1.50.1 (`__tests__/scripts/dev-safe.test.ts:489`). If the function
  read `defaults.json` itself, the wiring commit, which sets our fork's repository and commit in that file, would
  turn those tests red on our `deep-reasoning` branch. As a fill at `main()`, the file's values never reach a
  function a test calls with an explicit `env`.
- *One mechanism for every consumer.* The children (agent-server, automation, setup command) inherit the same
  values; the session and secret key paths, the state directory and the agent-server source come out of one place.

**The fill rules** (`launcherDefaultsEnv`, §6.1):

| `defaults.json` key | Fills | Only when |
| --- | --- | --- |
| `sources.agentServerGitRepo` | `OH_AGENT_SERVER_GIT_REPO` | that variable is unset |
| `sources.agentServerGitRef` | `OH_AGENT_SERVER_GIT_REF` | none of `OH_AGENT_SERVER_LOCAL_PATH`, `OH_AGENT_SERVER_GIT_REF`, `OH_AGENT_SERVER_VERSION` is set |
| `paths.stateDir` | `OH_CANVAS_SAFE_STATE_DIR` | that variable is unset |
| `paths.stateDir` | `OH_SECRET_KEY_PATH` = `<stateDir>/secret-key.txt`, `OH_SESSION_API_KEY_PATH` = `<stateDir>/api-key.txt` | the state directory came from `defaults.json` (not from the environment), and each variable is unset |

The ref rule is the subtle one: a ref from `defaults.json` must not outrank a PyPI version or a local path the
user put in the environment, so it fills only when the environment names no source at all. The repository fills
independently: an environment ref with no environment repository uses the build's repository, which is what a
developer of the fork means by `OH_AGENT_SERVER_GIT_REF=my-branch npm run dev`.

Every value is validated whether or not the environment wins, so a broken `defaults.json` fails every launch,
loudly, with the key's name (§3.3).

### 2.2 `OH_AGENT_SERVER_GIT_REPO` mirrors `OH_AUTOMATION_REPO`

**Decision.** `buildAgentServerCommand` takes the repository from `OH_AGENT_SERVER_GIT_REPO`, defaulting to
upstream's `https://github.com/OpenHands/software-agent-sdk`. Like `OH_AUTOMATION_REPO`, it matters only with a
git ref; on its own it is ignored. It is checked when it is used: it must be an `https://` or `ssh://` URL (no
`git+` prefix; the launcher adds it). A local path still outranks a git source, and a git ref still outranks a PyPI
version.

**Why** these two schemes, as the spec's mock-up has it: they are what uv fetches from (`git+https`, `git+ssh`); an
scp-style `git@host:path` is not a valid URL in a requirement and a bare `owner/repo` is not a URL at all, so
rejecting them early gives the launcher's message instead of uv's. A local checkout already has its own variable,
`OH_AGENT_SERVER_LOCAL_PATH`.

**The source line** keeps upstream's wording for upstream's repository (`git (feature-branch)`, which upstream's
test pins) and names any other repository: `git (michaeltheologitis/software-agent-sdk@<ref>)`, with
`https://github.com/` and a trailing `.git` dropped from the label.

### 2.3 Reuse: a full commit SHA is never reinstalled

**Decision.** In the git branch of `buildAgentServerCommand`, `--reinstall` is passed unless the ref is a full,
40-hex-digit commit SHA. Nothing else changes: no state file, no extra subprocess, no `--offline`. Builds that
want offline relaunches (the desktop app) pin the commit; the wiring commit records the `dr-N` tag's commit
(§4.5).

**Why, from measurements** (uv 0.8.17; the network cut with `unshare -n`, which leaves only a dead loopback; a
control run with an uncached package failed with `dns error`, so the cut was real):

| Run (cache warmed by an earlier online run of the same command unless noted) | Result |
| --- | --- |
| `uvx --from git+…@<tag> …`, network cut | fails: `Updating … (v4.1.0)`, `Git operation failed` |
| `uvx --offline --from git+…@<tag> …`, network cut | fails the same way: uv fetches to resolve any name |
| `uvx --from git+…@<commit> …`, network cut, index cache past its 600 s lifetime | **runs** |
| `uvx --offline --from git+…@<commit> …`, network cut | runs |
| `uvx --reinstall --from git+…@<commit> …`, network cut | fails: it rebuilds, and rebuilding resolves `build-system.requires` |
| the real agent-server, `git+…/software-agent-sdk@91430aa…` for all four packages plus `posthog>=6,<7`, `agent-server --help`, network cut, without `--reinstall` | runs in 6.4 s (with `--offline`: 6.3 s); first install online: 25 s |
| a cache already holding PyPI's `openhands-sdk==1.50.1` and `openhands-agent-server==1.50.1`, then the same four packages from `git+…@91430aa…` **without** `--reinstall` | the environment holds the git build: `direct_url.json` names commit `91430aa…` for both |
| the same with the branch name `@deep-reasoning` instead of the commit | also the git build |

So the two facts that decide the design: (a) uv cannot run a branch or a tag without the network, even with
`--offline`, because it must fetch to resolve the name; (b) for a commit, `--reinstall` buys nothing (the URL
pins the code, and uv does not substitute a cached PyPI wheel of the same version, which is the reason upstream's
comment at `dev-safe.mjs:464–467` gives) and costs the network on every launch. A commit is the only ref uv can
reuse, and for a commit reuse is free.

Upstream's comment gains the commit exception and the measurement behind it. For every other ref (a branch, a tag,
an abbreviated SHA) `--reinstall` stays, as upstream has it: those launches need the network whatever the flags,
because uv fetches to resolve the name (measured), and changing their behaviour is not this change's business.

**What the user sees:** no launch from a pinned commit passes `--reinstall`. The first installs it (minutes, online);
every later launch of the same commit starts from uv's cache, online or not. A launch with a different commit installs that one. Online, uv
may still refresh index metadata for the unpinned transitive dependencies, exactly as the PyPI path does today;
offline it runs what it has (measured above with the index cache stale).

**Rejected, with cost:**
- *Keep tags, resolve them in the launcher* (`git ls-remote` with the patterns `refs/tags/<ref>^{}`,
  `refs/tags/<ref>`, `refs/heads/<ref>`, a record of the installed commit in the state directory, tags trusted
  without the network, branches re-resolved each launch, and a fallback to the recorded commit offline). It keeps
  `dr-3` readable in `defaults.json` and in the launch log, and it is what the spec's mock-up shows. Cost: about
  170 more lines with tests, a git subprocess before every git launch, a state file that can disagree with uv's
  cache (so a retry path when a reused install fails to start), and a peeled-tag subtlety (a plain
  `git ls-remote <repo> refs/tags/<tag>` returns the tag object, not the commit, for an annotated tag; measured).
  If Michael wants tag names in `defaults.json`, this is the design to switch to; nothing else in this document
  changes.
- *`--offline` for a commit.* Not needed (measured), and it would turn a partly pruned uv cache into a failed
  launch that needs a record of what was installed and a retry path, where uv online simply fetches what is missing.
- *A launcher-owned install (`uv tool install` into the state directory, then run the binary).* Deterministic, but
  it replaces upstream's `uvx` model with a second install path and a second process to supervise.

### 2.4 The state directory, and what its parent means

**Decision.** `paths.stateDir` is the fallback for `OH_CANVAS_SAFE_STATE_DIR`, with the same meaning: the
directory the launcher calls the state directory. It must be absolute or start with `~/` (expanded to the user's
home); a relative path has no meaning in a packaged app. When the state directory comes from `defaults.json`, the
two key files move into it too (§2.1's table); when it comes from the environment they stay where upstream keeps
them, as today.

**Why it is not a new "persistence root" key.** The variable already exists and every launcher already honours it;
a second concept would need its own precedence against it. The cost is a subtlety the contract must state plainly:
**the parent of the state directory is the persistence root** (§1.1). A build that wants its own state, not shared
with a stock Agent Canvas on the same machine, names a state directory whose parent is its own, for example
`~/.deep-reasoning/agent-canvas`. The value in the spec's mock-up, `~/.openhands/deep-reasoning`, moves only the
conversations: settings, secrets, agent profiles, installed Apps and their approval, and the automation database
would stay in `~/.openhands`, shared with stock Agent Canvas, which would then list D5's Library App and default to
the `deep_reasoner` agent profile (§2.7, item 5).

**Why the key files move with it.** A build that names its own state directory is a different app; sharing
`~/.openhands/agent-canvas/secret-key.txt` with stock Agent Canvas would tie the decryption of its secrets to
another app's file. The environment overrides stay as upstream uses them (its end-to-end tests set
`OH_CANVAS_SAFE_STATE_DIR` and `OH_SESSION_API_KEY_PATH` separately, `tests/e2e/mock-llm/backends/*.spec.ts`).

**Not moved:** the file logger (`scripts/logger.mjs`) reads `OH_CANVAS_SAFE_STATE_DIR` once, when it is imported,
before `main()` runs, so a dev run of a tree whose `defaults.json` names a state directory still writes its log
files under `~/.openhands/agent-canvas/logs`. In a packaged app the logger is a no-op (winston is stripped,
`logger.mjs:1–13`), so this touches no user; making it follow would mean a fourth reader of `defaults.json` for a
dev-only log. Named, not fixed.

### 2.5 The setup command

**Decision.**
- `setup.command` is an argv array, run **without a shell**, as the launcher's own user, with `stdin` closed
  (`/dev/null`) and `stdout`/`stderr` streamed line by line into the launcher's log under the service name
  `setup before-start` or `setup after-ready`. `argv[0]` is looked up on the launcher's `PATH`.
- `setup.phases` lists when it runs: `before-start`, `after-ready`, or both (the default when the key is absent).
- It runs on **every launch that starts the agent-server** (not with `--frontend-only`), in the launchers built on
  `dev-with-automation.mjs` `main()`: the desktop app, `npm run dev` and the `agent-canvas` bin. `dev:minimal`,
  `dev:static` and `dev:extra-backend` do not run it (§2.7, item 7).
- `before-start` runs after the port check and the state directories are created, before any service starts.
- `after-ready` runs once the agent-server answers `/server_info` and the launcher has seeded its own automation
  secret, before the automation backend, the frontend and the ingress start. If the agent-server never became
  ready, it is skipped with a log line (the launch is already failing: the desktop app throws on
  `agentServerReady === false`, `electron/main.mjs:671–678`).
- Its environment is the launcher's own, plus the entries in §4.2; its working directory is the state directory.
- Exit 0 continues the launch. A non-zero exit, a signal, a failure to start, or running past 15 minutes stops the
  launch: in `after-ready` the launcher first stops the services it started (only the agent-server is running then),
  then `main()` throws a `SetupCommandError`; the CLI prints it and exits 1; the desktop app shows its existing
  failure state (summary, the full startup log, Copy logs, Quit; `showStartupFailure`, `electron/main.mjs:527`).

**Why these choices.**
- *Every launch, not once.* The spec's wording is "runs as the user before the stack starts, and again once the
  agent-server is ready", and D5's is "later launches do nothing until a pin changes": the command decides that,
  because only it knows what it installed and whether it is still there. A launcher-side "already ran" record would
  not notice a deleted install and would need its own invalidation rule. The cost is one process start per phase
  per launch; §2.3's measurement is what makes a `uvx`-launched setup command cheap and offline-safe on later
  launches when it pins a commit (§4.6).
- *Argv, no shell.* No quoting rules, no injection through a path with a space or a `$`, the same behaviour on every
  platform (`spawnService`'s Windows `.cmd` resolution still applies). A build that needs a shell names
  `["sh", "-c", "…"]` itself.
- *`stdin` closed.* A command that prompts (git asking for a password in a terminal run) would otherwise hang the
  launch invisibly; with nothing to read it fails, and its failure stops the launch with its output.
- *The two phases in one command, told apart by `OH_CANVAS_SETUP_PHASE`*, as the spec's mock-up has it. A build
  that needs only one lists only one.
- *`after-ready` before the automation backend and the frontend*, because what the after-ready step registers
  (D5: an App and a default agent profile) should exist before the first screen asks for it, and because a failure
  then leaves only the agent-server to stop.
- *15 minutes*, a named constant, not a key: the agent-server's own first install is bounded at 10 minutes in the
  desktop app (`electron/main.mjs:664`), D5's first-launch install measured 1 m 52 s in the spec's mock-up, and a
  hung command must not leave the splash waiting forever. D5 can ask for a key if it needs one.
- *A thrown error, not a new return field.* The desktop app already turns a thrown error into its failure state;
  the CLI already prints and exits 1. The launcher's one addition is to stop what it started before throwing, so a
  failed setup leaves nothing running in either.

### 2.6 What changes in the desktop app

Two lines in `electron/main.mjs`, both about the setup command:
- `handleServiceLog` (`:621`) also puts setup lines on the splash's one-line status, as it does for `agent-server`
  and `automation` lines (`:628`), so a slow first-launch setup shows progress instead of a stalled headline.
- The startup-failure summary (`:730–732`) appends "Ensure ports 8000, 18000, and 18001 are free, then try again."
  to every error; for a `SetupCommandError` (`err.name === "SetupCommandError"`) it does not, because the ports are
  not the problem and the hint would send the user the wrong way.

Nothing else in Electron changes: it gets the new behaviour through `main()`.

### 2.7 Departures from the approved spec

1. **Reuse is for a commit, not any ref** (§2.3). The spec says "reuses the installed agent-server while the ref is
   unchanged", and its mock-up writes `"agentServerGitRef": "dr-3"`. uv cannot run a tag without the network
   (measured), so the wiring commit writes the commit of `dr-N` and names the tag in a `_comment`; the launch log
   shows the commit. The falsifier holds for the packaged build because its ref is a commit by contract. The
   tag-resolving alternative is costed in §2.3 if the readable tag matters more than about 170 lines.
2. **Size.** The spec estimated ≈0.35 k lines with tests, ≈1 h at Gate C; this design is ≈0.58 k (§8): the setup
   command's tests need a packaged-layout fixture, and there is a live test (§7.5). The reuse itself is smaller than
   the spec's ≈40 lines.
3. **A live test and a fork-only workflow to run it** (§7.5). The spec places C3's evidence in the fork's own tests
   (layer 3) and its live evidence in "end-to-end tests, Playwright" (layer 5); the network-cut relaunch can only be
   shown against real uv, GitHub and PyPI, and there is no page to drive, so it is an on-demand vitest file with its
   own job.
4. **No CLI flag** for the repository. The spec's cost line mentions "`OH_AGENT_SERVER_GIT_REPO` and its flag";
   the agent-server's source has never had flags (only automation has `--automation-ref`/`--automation-repo`), and a
   repository flag without a ref flag would be odd; adding both is outside this change.
5. **The state directory's example value.** The spec's mock-up `~/.openhands/deep-reasoning` would leave
   everything but conversations shared with stock Agent Canvas (§2.4). Not a change to C3, which takes any value; a
   finding for D5's design, stated in its contract (§4.3).
6. **The key files follow a state directory named in `defaults.json`** (§2.4); the spec does not mention them.
7. **The setup command runs only in the `dev-with-automation.mjs` launchers** (desktop app, `npm run dev`, the npm
   bin), not in `dev:minimal`, `dev:static` or `dev:extra-backend`, which still take the new source and
   state-directory defaults. The spec says "the launcher"; those three are developer conveniences with their own
   start sequences.
8. **Names the spec left open:** `OH_CANVAS_SETUP_PHASE`, `SESSION_API_KEY` (the SDK's client-side name,
   `openhands-workspace/…/cloud/workspace.py:245`), `OH_PERSISTENCE_DIR` and `OH_CANVAS_SAFE_STATE_DIR` in the
   setup's environment (§4.2); the service names `setup before-start` and `setup after-ready`, which reproduce the
   mock-up's `[setup before-start]` log prefix.

### 2.8 Other rejected alternatives

- *Read `defaults.json` inside `buildAgentServerCommand` and `buildSafeDevConfig`* (a `defaults` parameter):
  breaks upstream's tests on our branch once the wiring commit sets values (§2.1).
- *A generic `env` map in `defaults.json`* (any variable a build wants): smaller, but it cannot express "the ref
  fills only when the environment names no source", needs `~/` expansion for some values and not others, and
  documents nothing.
- *A separate overrides file* (`config/desktop.json`) instead of keys in `defaults.json`: a second file to
  package, read and keep in sync, for no gain; `defaults.json` already calls itself the single source of truth for
  pins and paths.
- *A setup command per phase* (`setup.beforeStart`, `setup.afterReady`): two keys for what is usually one program
  with two entry points; the phase variable covers it.
- *Running the setup only once per distinct setup configuration*: see §2.5.

---

## 3 · Behaviour

### 3.1 Precedence

Agent-server source (E = the environment after any user setting, D = `defaults.json`):

| First that applies | Source |
| --- | --- |
| E `OH_AGENT_SERVER_LOCAL_PATH` | local checkout (unchanged) |
| E `OH_AGENT_SERVER_GIT_REF` | git, from E `OH_AGENT_SERVER_GIT_REPO` ?? D `agentServerGitRepo` ?? upstream |
| E `OH_AGENT_SERVER_VERSION` | PyPI at that version (unchanged) |
| D `sources.agentServerGitRef` | git, from E `OH_AGENT_SERVER_GIT_REPO` ?? D `agentServerGitRepo` ?? upstream |
| — | PyPI at D `versions.agentServer` (unchanged) |

State directory: E `OH_CANVAS_SAFE_STATE_DIR` ?? D `paths.stateDir` (expanded) ?? `~/.openhands/agent-canvas`.
Secret-key file: E `OH_SECRET_KEY` (the key itself) ?? E `OH_SECRET_KEY_PATH` ?? `<D stateDir>/secret-key.txt` ??
`~/.openhands/agent-canvas/secret-key.txt`. Session-key file: E `LOCAL_BACKEND_API_KEY` (the key itself) ??
E `OH_SESSION_API_KEY_PATH` ?? `<D stateDir>/api-key.txt` ?? `~/.openhands/agent-canvas/api-key.txt`.

### 3.2 The launch, in `dev-with-automation.mjs` `main()`

New steps in bold; the rest is today's order (`dev-with-automation.mjs:1441–1663`).

1. Install the service-log listener; parse arguments (`--help` exits here, before any `defaults.json` check).
2. **Apply the `defaults.json` fallbacks to `process.env`** (§2.1); when any were filled, write one line naming them
   under the service name `defaults`, to the terminal and to the service-log listener (so the splash shows it too).
3. **Read the setup configuration** (`readSetupConfig`), so a malformed `setup` fails before anything runs.
4. Check prerequisites; validate a local agent-server or automation path; build the config (port check); create the
   state directories; run `extraPrereqs`.
5. **`before-start`**, if configured and the agent-server will be launched.
6. Build the static frontend if asked; check the static directory.
7. Start the agent-server (its command now from `OH_AGENT_SERVER_GIT_REPO`, and without `--reinstall` for a commit)
   and wait for `/server_info`.
8. Seed the automation secret, if automation runs and the agent-server is ready.
9. **`after-ready`**, if configured and the agent-server is ready; on failure stop the started services and throw.
   If configured but the agent-server is not ready: log `Skipping setup after-ready: agent-server not ready`.
10. Start automation, the frontend, the ingress; print the banner; return `{ config, agentServerReady }`.

The other three launchers do step 2 only, at the top of their `main()`.

### 3.3 What the user sees

The launch log, desktop splash and terminal alike (the splash's console prefixes each line with its service name):

```text
[defaults]          From config/defaults.json: OH_AGENT_SERVER_GIT_REPO, OH_AGENT_SERVER_GIT_REF, OH_CANVAS_SAFE_STATE_DIR, OH_SECRET_KEY_PATH, OH_SESSION_API_KEY_PATH
[setup before-start] Running dr-app setup
[setup before-start] … (the command's own lines)
[setup before-start] Done in 1m 52s
[agent-server]      Using git (michaeltheologitis/software-agent-sdk@91430aa551ca3deb88989685656837929b3c246b)
[setup after-ready] Running dr-app setup
[setup after-ready] Done in 3s
```

(The command line shown is `argv` joined with spaces; the mock-up's `dr-app setup` stands for whatever D5 writes.)

Failures, exact wording (tests assert these):

```text
OH_AGENT_SERVER_GIT_REPO must be an https or ssh git URL, got: michaeltheologitis/software-agent-sdk
sources.agentServerGitRepo in config/defaults.json must be an https or ssh git URL, got: michaeltheologitis/software-agent-sdk
sources.agentServerGitRef in config/defaults.json must be a non-empty string, got: ""
paths.stateDir in config/defaults.json must be an absolute path or start with ~/, got: state
setup.command in config/defaults.json must be a non-empty array of non-empty strings, got: "dr-app setup"
setup.phases in config/defaults.json may list only "before-start" and "after-ready", got: ["first-launch"]

Setup command `dr-app setup` failed (exit 2) before the stack started. Its output is in the startup log.
Setup command `dr-app setup` failed (exit 2) after the agent-server started; the stack was stopped. Its output is in the startup log.
Setup command `dr-app setup` was killed by SIGKILL before the stack started. Its output is in the startup log.
Setup command `dr-app setup` was stopped after 15 minutes before the stack started. Its output is in the startup log.
Setup command `dr-app setup` could not be started (spawn dr-app ENOENT) before the stack started.
```

Each setup message is built from three parts: the head (`failed (exit N)`, `was killed by SIGNAL`, `was stopped
after 15 minutes` naming the timeout in force, or `could not be started (<the spawn error's message>)`); the phase
clause (` before the stack started.` or ` after the agent-server started; the stack was stopped.`); and, except for
a spawn failure, which has no output, ` Its output is in the startup log.` In the desktop app the summary shows
above the expanded log with Copy logs and Quit, and without the ports hint (§2.6).

---

## 4 · The contract D5 builds against (and the wiring commit)

Stated as what the Canvas fork guarantees from its `dr-N` tag onward. D5 may rely on everything here and on
nothing else about the launcher.

### 4.1 `config/defaults.json`

Three optional blocks; `null` (or absent) means "not set". Upstream's file carries them as `null` with a
`_comment`, as it does for its other keys.

```json
{
  "sources": {
    "agentServerGitRepo": "https://github.com/michaeltheologitis/software-agent-sdk",
    "agentServerGitRef": "<the 40-hex commit of dr-N>"
  },
  "paths": {
    "stateDir": "~/.deep-reasoning/agent-canvas"
  },
  "setup": {
    "command": ["uvx", "--from", "git+https://github.com/michaeltheologitis/deep-reasoning@<commit>", "dr-app", "setup"],
    "phases": ["before-start", "after-ready"]
  }
}
```

(Values illustrate D5's case; the state directory's name and the setup command are D5's to choose.)

| Key | Type | Meaning |
| --- | --- | --- |
| `sources.agentServerGitRepo` | `https://` or `ssh://` URL, or `null` | Where the four SDK packages come from when the source is git. |
| `sources.agentServerGitRef` | non-empty string, or `null` | The git ref to install when the environment names no source. A full 40-hex commit is installed once and reused offline afterwards; any other ref is refetched and rebuilt on every launch (§2.3). |
| `paths.stateDir` | absolute path or `~/…`, or `null` | The launcher's state directory; its parent is the persistence root (§4.3). |
| `setup.command` | non-empty array of non-empty strings, or `null` | The setup command's argv. |
| `setup.phases` | array of `"before-start"`, `"after-ready"`; default both | When it runs. |

Whatever is in `defaults.json` is also compiled into the frontend bundle (`src/services/telemetry.ts:36` and
`src/api/agent-server-compatibility.ts:14` import the whole file), so it must never hold a secret.

### 4.2 The setup command

- **Invocation:** `spawn(command[0], command.slice(1))` without a shell, as the user running the app; `argv[0]`
  resolved on `PATH`. In a packaged app `PATH` is the bundled `uv` directory and the bundled Node `bin` directory
  (Electron prepends both), then whatever the OS gave the app: from Finder on macOS that is
  `/usr/bin:/bin:/usr/sbin:/sbin`, not the user's shell `PATH`. So `uvx`, `uv`, `node`, `npm`, `npx` and the system
  `git` are reachable; a command the setup itself installs is not, until it is installed.
- **Working directory:** the state directory (absolute; it exists).
- **stdin:** closed. **stdout, stderr:** each line goes to the launcher's log and the desktop splash's console under
  `setup before-start` / `setup after-ready`, and becomes the splash's status line. It is visible to the user and
  copied by Copy logs, so it must not print secrets.
- **Environment:** the launcher's environment (`HOME`, `PATH` as above, `SSH_AUTH_SOCK` and the rest of what the app
  was started with, plus the variables §2.1 filled), and:

  | Variable | `before-start` | `after-ready` |
  | --- | --- | --- |
  | `OH_CANVAS_SETUP_PHASE` | `before-start` | `after-ready` |
  | `OH_CANVAS_SAFE_STATE_DIR` | the state directory, absolute | the same |
  | `OH_PERSISTENCE_DIR` | its parent, the persistence root (what the agent-server is given) | the same |
  | `AGENT_SERVER_URL` | not set | `http://127.0.0.1:<agent-server port>` (direct, not through the ingress) |
  | `SESSION_API_KEY` | not set | the session key; send it as `X-Session-API-Key` |

- **Exit:** 0 continues the launch. Anything else stops it as §2.5 says; in `after-ready` the agent-server is
  stopped first. The message names the command, the phase and the exit code or signal (§3.3).
- **Time:** at most 15 minutes per phase, then the command's process tree gets `SIGTERM`, and `SIGKILL` 3 s later if
  it is still running, and the launch stops.
- **Frequency:** both configured phases run on every launch that starts the agent-server. The command is
  responsible for being fast, and offline-safe, when it has nothing to do.
- **Interruption:** if the user quits during a phase, the command's process tree is stopped with the other services.

### 4.3 The state directory and the persistence root

With `paths.stateDir = <P>/<name>`, everything the stack persists lives under `<P>`:

| Under | What |
| --- | --- |
| `<P>/<name>/` | conversations (`dev_conversations/`), workspaces, bash events, tmux sockets, automation file storage, `secret-key.txt`, `api-key.txt` |
| `<P>/` | the agent-server's and SDK's state: `settings.json`, `secrets.json` (encrypted with `secret-key.txt`), `workspaces.json`, `agent-profiles/`, `profiles/`, `canvas-extensions/` (installed Apps, their approvals and backends), `skills/`, `plugins/`, `hooks.json`, `SOUL.md`, caches |
| `<P>/automation/automations.db` | the automation backend's database |

So **D5 chooses a `<P>` of its own** (for example `~/.deep-reasoning`), not `~/.openhands`: otherwise the App it
installs, its approval and the default agent profile it sets would appear in a stock Agent Canvas on the same
machine (§2.7, item 5). The flip side: the user's existing `~/.openhands` skills, plugins, hooks and profiles are
not visible in D5's app.

Not isolated by the state directory: uv's cache (shared, harmless), the fixed ports 8000, 18000 and 18001 (D5's
app cannot run beside a stock Agent Canvas desktop, as the spec already says), and the dev-only file logger
(§2.4). Electron's own `userData` (local storage, including the frontend's backend list) is separate by product
name, which D5's build sets.

### 4.4 What the launcher guarantees, and what it does not

Guarantees:
- With no `OH_AGENT_SERVER_*` variable in its environment, the app starts the agent-server from
  `sources.agentServerGitRepo` at `sources.agentServerGitRef`, all four packages from that one commit.
- With that ref a full commit, no launch passes `--reinstall`: the first installs the commit, and every later launch
  runs uv's cached build of it, with or without the network (measured on uv 0.8.17; the live test in §7.5 re-checks
  it on the uv the build bundles, since `scripts/download-uv.mjs` takes the latest release unless `UV_VERSION` is
  set).
- `before-start` finishes before any service starts; `after-ready` starts only after `/server_info` answered and
  finishes before automation, the frontend and the ingress start.
- A failing setup leaves no service of this launch running, and its output in the startup log.
- Environment variables win over every `defaults.json` key, variable by variable (§3.1).

Not guaranteed:
- That a packaged app launched from a terminal ignores the user's shell: a Linux AppImage started from a shell that
  exports `OH_AGENT_SERVER_VERSION` runs PyPI. This is the spec's "environment variables still win".
- Anything about the agent-server's own network use at start (LiteLLM retries its model-price download, offline, for
  a few seconds; measured), or the automation backend's (PyPI, unchanged).
- An offline first launch after an app update: a newer bundled uv may keep its cache in a new layout, and a new
  release usually pins a new commit anyway; either way that launch installs, online.

### 4.5 Who writes what

| Change | Writes | Where |
| --- | --- | --- |
| C3 (this PR) | the mechanism; `null` defaults | Canvas fork, `feat/launcher-agent-server-source`, then `deep-reasoning` |
| The wiring commit (Q2 (a)) | `sources.agentServerGitRepo` = the SDK fork; `sources.agentServerGitRef` = the commit of its `dr-N` tag, with `"_agentServerGitRefComment": "tag dr-N of michaeltheologitis/software-agent-sdk"` | Canvas fork `deep-reasoning` only, never upstream |
| D5's build | `paths.stateDir`, `setup` | deep-reasoning's build, edited into the Canvas checkout's `config/defaults.json` before `npm run build:desktop` |

For the wiring commit: after it, every launcher in the fork (the mock-LLM end-to-end run included, which starts
`bin/agent-canvas.mjs`, `playwright.mock-llm.config.ts:138–154`) installs our agent-server from git. A cold uv
cache in CI builds four packages from source, which may push that run's 180 s web-server timeout
(`playwright.mock-llm.config.ts:164`); the wiring commit should check, and raise it if needed.

### 4.6 What D5 should know (measured, not decided here)

- `dr-app` is not on `PATH` at first launch, so the command must bring it: for example `uvx --from
  git+https://github.com/michaeltheologitis/deep-reasoning@<commit> dr-app setup`. Pinned to a full commit and
  without `--reinstall` or `--refresh`, uv serves it from its cache on every later launch, offline included (§2.3's
  table applies to any git requirement). With a branch or a tag, every launch needs the network.
- deep-reasoning and deep_reasoner are private: uv fetches them with git and the user's credentials. In the
  packaged app there is no terminal, so git cannot prompt there; in a terminal run `stdin` is closed, but git may
  still prompt on the terminal itself, so a command that fetches should set `GIT_TERMINAL_PROMPT=0` for its git.
- The command sees `SESSION_API_KEY` in `after-ready`; keep it out of anything it starts that outlives it.
- `before-start` and `after-ready` are the same argv; `dr-app setup` dispatches on `OH_CANVAS_SETUP_PHASE`.

---

## 5 · Modules and changes

All new code imports Node built-ins only: the packaged app strips `node_modules` and restores only `sirv` and
`httpxy` (`RUNTIME_PACKAGES`, `electron-builder.config.mjs:83`), so a bare import in a launcher script fails only in
the installed app (`.agents/skills/desktop-electron/references/guide.md`). The packaged app and the npm package
already ship every `scripts/*.mjs` and the whole `config/` (`electron-builder.config.mjs:365–367`;
`package.json` `files`), so no packaging change is needed.

### 5.1 `config/defaults.json`

Add, with `null` values and comments in the file's existing `_comment` style:
- a top-level `sources` block (`_comment`, `agentServerGitRepo`, `agentServerGitRef`);
- `paths.stateDir` and `paths._stateDirComment` ("npm and desktop launchers only; Docker uses `stateSubdir`; the
  parent of this directory is the agent-server's persistence root");
- a top-level `setup` block (`_comment`, `command`, `phases` = both).

### 5.2 `scripts/launcher-defaults.mjs` (new)

What a build's `defaults.json` may set for the launchers, the checks on those values, and the fill of §2.1. No
imports but `node:fs`, `node:os`, `node:path`, `node:url`. Functions: `loadSharedDefaults`, `expandHomePath`,
`validateGitRepoUrl`, `launcherDefaultsEnv`, `applyLauncherDefaults`, `readSetupConfig` (§6.1).

### 5.3 `scripts/dev-safe.mjs`

- `buildAgentServerCommand`: the repository from `OH_AGENT_SERVER_GIT_REPO` (validated with
  `validateGitRepoUrl`), the `--reinstall` rule of §2.3, the source label of §2.2; JSDoc and the comment at
  `:464–467` rewritten. The local-path and PyPI branches are untouched.
- `main()` (`dev:minimal`): `applyLauncherDefaults()` first.
- `AGENT_SERVER_GIT_REPO` is exported as `DEFAULT_AGENT_SERVER_GIT_REPO` (tests and the label use it).

### 5.4 `scripts/dev-with-automation.mjs`

- `main()`: the steps of §3.2, and a new `setup` option (default `readSetupConfig(SHARED_DEFAULTS)`) beside its
  existing options, so an embedder can pass or disable (`null`) a setup.
- New: `SetupCommandError`, `SETUP_PHASES` (re-exported), `SETUP_COMMAND_TIMEOUT_MS`, `buildSetupEnv`,
  `runSetupCommand` (§6.2); `stopServices()` extracted from `shutdown()` (`:1100`), which now calls it.
- `showHelp`: `OH_AGENT_SERVER_GIT_REPO` under ENVIRONMENT VARIABLES, and a SETUP paragraph naming
  `config/defaults.json` `setup`.
- The file's header comment lists `OH_AGENT_SERVER_GIT_REPO`.

### 5.5 `scripts/dev-static.mjs`, `scripts/dev-extra-backend.mjs`

`applyLauncherDefaults()` at the top of `main()` (`dev-static.mjs:580`, `dev-extra-backend.mjs:124`).

### 5.6 `electron/main.mjs`

The two lines of §2.6. No new module: both are one-line conditions on values the file already has.

### 5.7 Docs in the fork

- `docs/DEVELOPMENT.md`: `OH_AGENT_SERVER_GIT_REPO` in the Environment Variables table and in "Agent server version
  selection" (with the commit rule); a short "Building from a fork: `config/defaults.json`" section for `sources`,
  `paths.stateDir` and `setup`, including §4.2's environment table and §4.3's parent rule.
- `.agents/skills/local-stack-runtime/references/guide.md:91–98`: the same variable and rule, one line each.

### 5.8 Deliberately unchanged

`scripts/logger.mjs` (§2.4); `docker/` and `.github/workflows/` (§1.4); `bin/agent-canvas.mjs`, whose version
listing still prints `versions.agentServer` even when a git source is configured (cosmetic, outside this change);
the agent-server readiness wait, which does not notice an agent-server process that exited and so waits out its
timeout (10 minutes in the desktop app) when `uvx` fails at once: an upstream weakness this change neither causes
nor needs, worth its own small PR.

---

## 6 · Signatures

JavaScript with JSDoc types, in upstream's style (ES modules, double quotes, trailing commas, JSDoc on every
export). The names, parameters, return shapes and error messages here are the contract the tests are written
against.

### 6.1 `scripts/launcher-defaults.mjs`

```js
/** The phases a setup command can run in, in launch order. */
export const SETUP_PHASES = Object.freeze(["before-start", "after-ready"]);

/**
 * @typedef {object} SetupConfig
 * @property {string[]} command  argv; command[0] is resolved on PATH; run without a shell.
 * @property {("before-start" | "after-ready")[]} phases  non-empty, no duplicates, in SETUP_PHASES order.
 */

/**
 * Read config/defaults.json next to this module's scripts/ directory (the same layout in the repo, the npm
 * package and the packaged app).
 * @returns {Record<string, any>}
 */
export function loadSharedDefaults() {}

/**
 * Expand a leading "~" or "~/" to `home`; return the result if it is absolute.
 * @param {string} value
 * @param {string} name  how errors name the value, e.g. "paths.stateDir in config/defaults.json"
 * @param {string} [home] defaults to os.homedir()
 * @returns {string} an absolute path
 * @throws {Error} `${name} must be an absolute path or start with ~/, got: ${value}`
 */
export function expandHomePath(value, name, home) {}

/**
 * Accept an https:// or ssh:// URL with no whitespace; reject anything else (an scp-style git@host:path, a
 * bare owner/repo, a git+ prefix, http://, file://).
 * @param {unknown} value
 * @param {string} name  e.g. "OH_AGENT_SERVER_GIT_REPO" or "sources.agentServerGitRepo in config/defaults.json"
 * @returns {string} the value
 * @throws {Error} `${name} must be an https or ssh git URL, got: ${value}`
 */
export function validateGitRepoUrl(value, name) {}

/**
 * The environment entries config/defaults.json supplies, per §2.1's rules: only variables `env` leaves unset;
 * OH_AGENT_SERVER_GIT_REF only when env names no agent-server source; the key paths only when the state
 * directory comes from `defaults`. Validates every launcher key of `defaults` whether or not env wins.
 * Pure: reads nothing but its arguments.
 * @param {Record<string, string | undefined>} env
 * @param {Record<string, any>} defaults  the parsed config/defaults.json
 * @param {string} [home] defaults to os.homedir()
 * @returns {Record<string, string>} the entries to add (empty for upstream's defaults)
 * @throws {Error} with the messages of §3.3
 */
export function launcherDefaultsEnv(env, defaults, home) {}

/**
 * Add launcherDefaultsEnv(env, defaults) to `env` in place. Each launcher's main() calls this first.
 * @param {Record<string, string | undefined>} [env] defaults to process.env
 * @param {Record<string, any>} [defaults] defaults to loadSharedDefaults()
 * @returns {string[]} the names of the variables it filled, sorted
 */
export function applyLauncherDefaults(env, defaults) {}

/**
 * The setup command of `defaults`, validated, or null when setup.command is null or absent.
 * @param {Record<string, any>} defaults
 * @returns {SetupConfig | null}
 * @throws {Error} with the setup.command / setup.phases messages of §3.3
 */
export function readSetupConfig(defaults) {}
```

### 6.2 `scripts/dev-with-automation.mjs` (additions)

```js
/** How long one setup phase may run before it is stopped. */
export const SETUP_COMMAND_TIMEOUT_MS = 15 * 60_000;

/**
 * A setup command that did not exit 0. main() throws it; the desktop app shows its message without the
 * ports hint (it checks `error.name`, so it needs no import).
 */
export class SetupCommandError extends Error {
  /**
   * @param {string} message  one of §3.3's setup messages
   * @param {{
   *   phase: "before-start" | "after-ready",
   *   command: string[],
   *   reason: "exit" | "signal" | "spawn" | "timeout",
   *   exitCode: number | null,
   *   signal: string | null,
   * }} details
   */
  constructor(message, details) {}
  // name = "SetupCommandError"; the details are own properties of the same names.
}

/**
 * The variables the launcher adds to the setup command's environment (§4.2). Pure.
 * @param {{ stateDir: string, agentServerPort: number, sessionApiKey: string }} config  main()'s config
 * @param {"before-start" | "after-ready"} phase
 * @returns {Record<string, string>}
 */
export function buildSetupEnv(config, phase) {}

/**
 * Run one phase of the setup command through spawnService under the name `setup ${phase}`: stdin closed,
 * every output line to the service log, `env` added to process.env, cwd as given. Writes "Running <argv>"
 * first and "Done in <duration>" on success, each both to the terminal (logService) and to the service-log
 * listener (emitServiceLog, level "info"), so the desktop splash shows them; spawnService already sends the
 * command's own lines to both.
 * @param {{
 *   command: string[],
 *   phase: "before-start" | "after-ready",
 *   cwd: string,
 *   env: Record<string, string>,
 *   timeoutMs?: number,  // defaults to SETUP_COMMAND_TIMEOUT_MS; on expiry the process tree gets SIGTERM,
 *                        // SIGKILL 3 s later if still running; rejects once it has exited
 * }} options
 * @returns {Promise<{ durationMs: number }>}
 * @throws {SetupCommandError} on a non-zero exit, a signal, a spawn error or the timeout
 */
export async function runSetupCommand(options) {}

/**
 * main() gains one option; the others are unchanged.
 * @param {{ setup?: import("./launcher-defaults.mjs").SetupConfig | null, ...rest }} [options]
 *   setup: undefined reads config/defaults.json; null runs no setup; an object is used as given (validated
 *   with the same rules as readSetupConfig).
 * @returns {Promise<{ config: object, agentServerReady: boolean }>}
 * @throws {SetupCommandError} after stopping any service it started
 */
async function main(options) {}
```

`stopServices()` is internal and async: `SIGTERM` to every tracked process tree, `SIGKILL` to any still running
3 s later, resolved once all have exited; it does not exit the process. `main()` awaits it before throwing an
after-ready `SetupCommandError`. `shutdown()` keeps its own flow (the same signals, then its hooks and
`process.exit`) and may call it.

### 6.3 `scripts/dev-safe.mjs` (changed)

```js
/** Upstream's repository, used when OH_AGENT_SERVER_GIT_REPO is unset. */
export const DEFAULT_AGENT_SERVER_GIT_REPO = "https://github.com/OpenHands/software-agent-sdk";

/**
 * Unchanged signature. Changes in the git branch only:
 * - repository: env.OH_AGENT_SERVER_GIT_REPO (validated) ?? DEFAULT_AGENT_SERVER_GIT_REPO;
 * - "--reinstall" first unless the ref matches /^[0-9a-f]{40}$/i;
 * - source: `git (${ref})` for the default repository, else `git (${label}@${ref})`, where label drops a
 *   leading "https://github.com/" and a trailing ".git".
 * @param {Record<string, string | undefined>} [env]
 * @returns {{ command: string, args: string[], source: string }}
 */
export function buildAgentServerCommand(env) {}
```

---

## 7 · Tests

Vitest, in upstream's folders, node environment (`// @vitest-environment node` at the top, as the neighbouring
script tests have), each test named for the property it pins. No test asserts on the values of the new keys in the
repository's own `config/defaults.json`: the wiring commit changes them, and the suite must stay green on our branch
after it. Tests pass their own `defaults` object, or their own `defaults.json` in a fixture directory.

### 7.1 `__tests__/scripts/launcher-defaults.test.ts` (new)

- `fills the agent-server's git repo and ref from defaults when the environment names no source`
- `an agent-server source in the environment wins over the defaults' ref` (`it.each` over
  `OH_AGENT_SERVER_LOCAL_PATH`, `OH_AGENT_SERVER_GIT_REF`, `OH_AGENT_SERVER_VERSION`)
- `the defaults' repo still applies to a ref from the environment`
- `the environment's repo wins over the defaults' repo`
- `fills the state directory from defaults, expanding ~/ to the home directory`
- `moves both key files into a state directory named by defaults`
- `leaves the key files alone when the environment names the state directory`
- `key file paths in the environment win over the defaults' state directory`
- `returns nothing for defaults whose launcher keys are null` (upstream's shape, written in the test)
- `rejects a relative state directory, naming the key` · `rejects a repo that is not an https or ssh URL, naming
  the key` (`it.each`: `owner/repo`, `git@github.com:owner/repo`, `git+https://…`, `http://…`, `file:///…`) ·
  `rejects an empty ref`
- `validates the defaults even when the environment wins`
- `applyLauncherDefaults fills only unset variables and returns their names`
- `reads an argv setup command and runs it in both phases by default` · `a null setup command means no setup` ·
  `rejects a setup command given as a string` · `rejects an unknown or repeated phase`
- `loads config/defaults.json from beside the scripts directory` (shape only: the file parses and has `ports`)

### 7.2 `__tests__/scripts/dev-safe.test.ts` (additions under `describe("buildAgentServerCommand")`)

- `installs all four packages from OH_AGENT_SERVER_GIT_REPO when it is set`
- `names a non-default repository in the source line`
- `ignores OH_AGENT_SERVER_GIT_REPO without a git ref`
- `rejects an OH_AGENT_SERVER_GIT_REPO that is not an https or ssh URL` (the mock-up's message)
- `installs a full commit SHA without --reinstall, so a relaunch can run from uv's cache`
- `still reinstalls a branch, a tag or an abbreviated SHA on every launch` (`it.each`; upstream's
  `abc1234` case keeps passing unchanged)
- `a local path still wins over a git repository and ref`
- Upstream's existing cases stay as they are.

### 7.3 `__tests__/scripts/dev-with-automation.test.ts` (additions)

Unit level, with real child processes (`process.execPath` running `--eval` snippets), no network:
- `buildSetupEnv gives both phases the phase, the state directory and the persistence root`
- `buildSetupEnv gives the agent-server URL and session key only after the agent-server is ready`
- `runSetupCommand runs argv without a shell` (an argument `$HOME; echo x` arrives as one literal argument)
- `runSetupCommand streams each output line to the service log under its phase`
- `runSetupCommand closes stdin, so a command that reads it sees end of input`
- `runSetupCommand runs in the given working directory with the given variables`
- `a non-zero exit rejects with a SetupCommandError naming the command, phase and exit code`
- `a command that cannot be started rejects with a SetupCommandError`
- `a command still running at its timeout is stopped and rejects` (timeout injected at 200 ms)

Launch level, with a **packaged-layout fixture** (skipped on Windows, like the SIGHUP test at `:960`): a temp
directory outside the repository holding copies of `scripts/*.mjs`, `tools/` and a `config/defaults.json` the test
writes, which is exactly what the desktop app ships (`electron-builder.config.mjs:353–375`). Outside the repository,
a bare import in a new module would fail here as it would in the installed app. A stub `uvx` first on `PATH` (a
Node script) appends its argv and selected variables to a JSON-lines file and, for the agent-server and automation
commands, answers 200 on its `--port`; the setup command is a Node script that appends
`{ phase, cwd, env subset, time }` to another file and exits with a code the test chooses. The launcher runs as
`node <fixture>/scripts/dev-with-automation.mjs --backend-only` with free ports (`PORT`,
`OH_CANVAS_SAFE_BACKEND_PORT`, `OH_CANVAS_SAFE_AUTOMATION_PORT`), `HOME` set to a temp directory, and no
`OH_AGENT_SERVER_*` variable; the test stops it with `SIGTERM`. (Its ingress cannot resolve `httpxy` outside the
repository and logs that; no assertion depends on the ingress.)
- `a packaged build starts the agent-server its defaults.json names` — `--from
  git+https://github.com/example/agent-sdk-fork@<40-hex>#subdirectory=openhands-agent-server`, the same commit for
  the three `--with` packages, no `--reinstall`, and the source line `git (example/agent-sdk-fork@<40-hex>)`. (The
  spec's first falsifier.)
- `the environment still wins over defaults.json` — with `OH_AGENT_SERVER_VERSION=1.18.0`, PyPI.
- `the state directory and key files named by defaults.json are used` — the key files appear under the fixture's
  state directory, none under `$HOME/.openhands`.
- `runs before-start before the agent-server and after-ready once it answers` — the setup's records bracket the
  stub's first request; after-ready saw `AGENT_SERVER_URL` pointing at the stub's port and the session key.
- `a failing before-start setup stops the launch before any service starts` — exit 1, the §3.3 message, the stub
  `uvx` never ran. (The spec's third falsifier, first phase.)
- `a failing after-ready setup stops the agent-server and fails the launch` — exit 1, the message, the stub's port
  closed afterwards. (Third falsifier, second phase.)
- `a malformed setup in defaults.json fails the launch before anything runs`

### 7.4 `__tests__/scripts/` existing suites

Unchanged and green: `dev-safe.test.ts`, `dev-with-automation.test.ts` (help text gains lines; its assertions are
`toContain`), `electron-builder-config.test.ts`, `package-library.test.ts`, `docs-version-sync.test.ts`,
`docker-vscode-route-sync.test.ts`. Upstream's full suite (764 vitest files) runs on the PR, as for every fork
feature (§4 of the spec, layer 3). No mutation testing: Stryker mutates `src/` only (`stryker.config.mjs:6–15`).

### 7.5 The live test: a relaunch with the network cut

`__tests__/scripts/agent-server-relaunch.live.test.ts`, skipped unless `OH_AGENT_SERVER_LIVE=1`, Linux only,
real `uvx` and the real network. It builds the command with the real `buildAgentServerCommand` for the source the
environment names (default: upstream's repository at `1e1390acc8788346ba4804c34323284009bf3f5e`, the commit of
`v1.50.1`, so the test itself is generic; our fork sets `OH_AGENT_SERVER_GIT_REPO`/`OH_AGENT_SERVER_GIT_REF` to the
SDK fork's pinned commit), with a fresh `UV_CACHE_DIR` and the environment `buildAgentServerEnv` gives the
agent-server (it imports `canvas_ui_tool` from `tools/`):
- `a pinned commit installs once and then starts with the network cut` — run the agent-server online until
  `/server_info` answers, stop it; then start the same command inside a network namespace (`unshare -rn`, or
  `unshare -n` when already root) through a small Node probe that starts it and polls `/server_info` from inside the
  namespace, and assert the probe succeeds. Skips with a reason if no namespace can be created. This is the spec's
  second falsifier on real services and on the uv version the environment has.

It is run on demand by `.github/workflows/launcher-live.yml` (`workflow_dispatch`, `ubuntu-24.04`; a step allows
unprivileged user namespaces with `sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0`, installs uv as
the desktop build does (`scripts/download-uv.mjs`: the latest release unless `UV_VERSION` is set), and runs the file
with the fork's source). That workflow is a **fork-only commit
on `deep-reasoning`**, beside the ASE commit, not part of the upstream-shaped PR; the test file is in the PR.

### 7.6 The falsifiers, mapped

| Spec falsifier | Test |
| --- | --- |
| a packaged build starts any agent-server other than the one its `defaults.json` names | §7.3 `a packaged build starts the agent-server its defaults.json names`; §7.1 precedence cases |
| a second launch with the ref unchanged needs the network | §7.2 `installs a full commit SHA without --reinstall…`; §7.5 live |
| a failing setup command leaves the launch waiting instead of stopped with its output | §7.3 the two failing-setup launches and the timeout unit test |

---

## 8 · Size

| Part | Lines (estimate) |
| --- | --- |
| `config/defaults.json` | 15 |
| `scripts/launcher-defaults.mjs` | 95 (with JSDoc) |
| `scripts/dev-safe.mjs` | 25 |
| `scripts/dev-with-automation.mjs` | 100 |
| `scripts/dev-static.mjs`, `scripts/dev-extra-backend.mjs`, `electron/main.mjs` | 8 |
| docs (`DEVELOPMENT.md`, the skill guide) | 35 |
| tests (§7.1–7.3, the fixture, §7.5) | 300 |
| **total** | **≈0.58 k**, about 2 h at Gate C (spec: ≈0.35 k, ≈1 h; §2.7, item 2) |

Suggested commits inside the one PR, each with its tests: (1) `OH_AGENT_SERVER_GIT_REPO` and no reinstall for a
commit; (2) `config/defaults.json` fallbacks for the agent-server's source and the state directory; (3) the setup
command and its two phases, with the Electron lines; (4) docs; (5) the live test. The fork-only workflow (§7.5) and
the wiring commit (§4.5) follow on `deep-reasoning`, outside the PR.

---

## 9 · Open points for the Conductor

1. **Commit or tag in `defaults.json`** (§2.3, §2.7 item 1): this design pins a commit and saves about 170 lines;
   the tag-resolving variant is fully specified there if Michael prefers `dr-N` to appear in the file and the log.
2. **D5's state directory** must have a parent of its own (§4.3); the spec's example value does not.
3. **The wiring commit** may need the mock-LLM end-to-end timeout raised once it installs from git (§4.5).
4. **The live workflow** is a fork-only commit (§7.5); it needs Actions enabled on the fork, which the spec already
   assigns to Michael.
