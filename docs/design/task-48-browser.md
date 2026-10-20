# TASK-48 · Run in the browser on localhost — design

**TASK-48** · System Designer · design branch `design/task-48` in
[deep-reasoning](https://github.com/michaeltheologitis/deep-reasoning), cut from `main` at `9e8109e`; this file is
the only change on it · against the approved spec
[TASK-48 · Run in the browser](https://app.notion.com/p/3fe62fb222378125b1dcf996022b75ac) (Gate A, 2026-10-19:
Q1 (d), Q2 (a), Q3 (a), Q4 (a), with the Conductor's amendment for (d)).

**Pinned against:** deep-reasoning `main` `9e8109e` (every deep-reasoning `file:line` below) · Canvas fork `dr-3`
`4355a36` (every Canvas `file:line`) · SDK fork `dr-2` `34c540c` (the bridge cookie only) · uv 0.8.17 (the
spec's floor) for every measurement, and 0.9.30 and 0.12.23 where named. D5's design v3 (`74e1565` on
`design/d5-v3`) binds: decisions B, C, G, K, L and N are relied on, not reopened.

**Revisions** (newest first; each says which sentences to stop trusting):
- 2026-10-19 · v1 · first full-depth version, written with the UX round (TASK-65) at its Gate A: its answers
  Q1 (a) (no onboarding; `NO_MODEL_KEY` goes), Q2 (a) and Q3 (b) (the cap in the panel) are folded into §8.

**Where this file lives, and why nothing trips over it.** `docs/design/task-48-browser.md`, beside D5's
`docs/design/d5-desktop-app.md` on its own branch. At `9e8109e` pytest collects `tests/` only (`testpaths`), ruff
excludes `docs` (`extend-exclude`), the sdist excludes `docs/`, and each wheel packages only its own `src/`. No
pull request of the task's stack carries this file.

**Reading guide.** Gate B: §0 (four findings that change the approved spec) and §1 (the shape and the
decisions), about 12 minutes. The Implementer: §0, then everything; §4 is the signature index, §5 every sentence a
user reads, §6 the exit codes, §7 the tests. The UX round's designer and the Conductor: §8 (seams and merge order).

---

## 0 · Findings that change the approved spec (read first)

Each was run on 2026-10-19 in this sandbox, with the scripts in the System Designer's scratchpad; *(verified)*
below means that.

**F1 · A tag in the command cannot restart offline.** `uvx --from git+<repo>@<tag>#subdirectory=… <cmd>` asks the
remote to resolve the tag on every run, and fails without it, `--offline` included. A full commit runs from uv's
cache. Verified with uv 0.8.17, 0.9.30 and 0.12.23 over `file://`, and over https against deep-reasoning itself
(a branch name; a tag takes the same path in uv). The Canvas launcher's own comment says the same
(`scripts/dev-safe.mjs`, `buildAgentServerCommand`: "uv has to fetch to resolve such a name anyway"). Q1 (d)'s
literal command, `@v<ver>`, therefore breaks Q2 (a)'s "a restart needs no network". **This design puts the
release's full commit in the command** (decision W1, divergence V1): one command per release, the version printed
beside it and on its first line. **Michael's word is needed**, since Q1 (d) quoted the tag; §2 V1 says what flips
if he keeps the tag.

**F2 · A PyPI dependency of the command's package needs the network ten minutes after the last start that had
it.** uv asks the index again for every requirement of a `uvx` environment once its cached answer expires, and
PyPI's simple API answers `Cache-Control: max-age=600, public` (read 2026-10-19), with no `stale-if-error`.
Verified on a local index serving `max-age=1`: a commit-pinned git tool with one pinned PyPI dependency runs
offline while the answer is fresh and fails once it has expired, on uv 0.8.17 and 0.12.23; `--offline` (or
`UV_OFFLINE=1`) runs it from the cache. A commit-pinned package with **no** dependencies runs offline with no
index answer at all (`dr-app` itself, its index cache deleted, network cut): D5 decision B's reason. So the
amendment's "Node as a dependency of the Python package the command runs" breaks the offline restart after ten
minutes. **This design keeps `dr-web` standard-library only, like `dr-app`, and has it install the same pinned
Node wheel, once, into `~/.deep-reasoning/web/`** (W2, V2).

**F3 · The wheel's `npm` and `npx` do not run from its `bin/`.** `nodejs_wheel/bin/npm` and `npx` are copies of
npm's scripts that `require('../lib/cli.js')`, which is not beside them (verified: `MODULE_NOT_FOUND`). The app's
bundled Node is the official distribution, whose `npx` works, and stdio MCP servers are started with `npx -y`
(Canvas `electron-builder.config.mjs`'s note on `node/`). Relinked as Node's distribution lays them out
(`bin/npm → ../lib/node_modules/npm/bin/npm-cli.js`, likewise `npx`), both run (npm 10.9.0, verified). `dr-web`
relinks them at install (§3.1).

**F4 · The same expiry reaches the agent-server and the automation backend, in the app as in the browser.** The
launcher starts both with `uvx` of requirements that pull PyPI packages (`dev-safe.mjs` `buildAgentServerCommand`:
the SDK's commit plus `posthog>=6,<7`; `dev-with-automation.mjs` `buildAutomationCommand`:
`openhands-automation==<version>`). *(verified)* The launcher's agent-server command at the SDK pin
(`uvx --from git+…software-agent-sdk@34c540c#subdirectory=openhands-agent-server --with …sdk --with …tools --with
…workspace --with 'posthog>=6,<7' agent-server --help`, a fresh uv cache, uv 0.8.17): installed online at 02:20:22
(34 s); offline at once, exit 0; offline 640 s later, **exit 2** (`dns error`); offline with `UV_OFFLINE=1`, exit 0.
So a restart with the network gone works only within ten minutes of the last start that had it, **for the desktop
app too**: D5's README sentence "A later launch with nothing changed installs nothing and needs no network" holds
only in that window, and E12's offline test, which runs setup alone, does not see it. The fix is in the
Canvas fork's launcher, not here (§9, proposed task P1). This design does not set `UV_OFFLINE` for the stack:
the launcher passes its whole environment to the agent-server, so it would reach every conversation's terminal
and make a cell's own `uv pip install` run offline. E13 measures both sides of the window (§7.4 claims 8 and 9).

---

## 1 · What TASK-48 is

A user pastes one line and talks to Deep Reasoning at `http://localhost:8000` in their own browser. It is the
desktop app without Electron: the same Canvas build from the pinned fork, the same patched `config/defaults.json`,
the fork's launcher unchanged, called by an entry of ours exactly as the app's Electron main calls it. One build
makes both (spec decision 1). The command is a front door of three parts:

```text
uvx --from git+https://github.com/michaeltheologitis/deep-reasoning@<release commit>#subdirectory=packages/dr-web deep-reasoning [--port N] [--no-open]
  uv: builds dr-web at the commit (no dependencies: from uv's cache for good, offline included)   (F1, F2)
  dr-web (Python, standard library)                                                             §3.1
    Node 22.12.0      ~/.deep-reasoning/web/node-22.12.0/  ← uv pip install --target, two pinned hashes, once
    the tarball       ~/.deep-reasoning/web/deep-reasoning-web-<ver>.tgz ← the release, once
    its tree          ~/.deep-reasoning/web/tree-<sha256:16>/package/ ← unpacked once per content
    PATH              Node's bin first; uvx's own environment dropped; uv's folder kept
    exec node <tree>/bin/deep-reasoning.mjs [--port N] [--no-open]       (Python is gone; uv forwards signals)
  desktop/web.mjs, as bin/deep-reasoning.mjs (Node)                                             §3.2
    checks Node, uv, git · cleans the environment · ports: 18000 the lock, 8000 or --port, 3001/18001 movable
    process.argv = [node, entry, --port, P] · import ../scripts/dev-with-automation.mjs
    main({...Electron's options, staticDir: <tree>/build})                 (electron/main.mjs:663-672 at dr-3)
      ports → setup before-start (bootstrap.sh → dr-app) → agent-server 127.0.0.1:18000 → after-ready
        → automation 18001 → static 3001 → ingress 127.0.0.1:P                (D5, unchanged)
    waits for /server_info · opens http://localhost:P · prints one line · runs until Ctrl+C
```

What a user installs: uv 0.8.17 or later, and git signed in for deep_reasoner_beta (as for the app). uv brings
Python and Node; nothing else is cloned or built.

### 1.1 Where everything lives

Everything D5 lists (D5 §1, the README's data table) is shared with the app. New, under the same root:

| Path | What | Written by |
|---|---|---|
| `~/.deep-reasoning/web/node-22.12.0/` | `nodejs-wheel-binaries` 22.12.0 installed with `--target`; `nodejs_wheel/bin/node`, `npm`, `npx` | `dr-web` |
| `~/.deep-reasoning/web/deep-reasoning-web-<ver>.tgz` | the release's tarball, as downloaded | `dr-web` |
| `~/.deep-reasoning/web/tree-<16 hex>/package/` | a tarball unpacked, named by the first 16 hex of its SHA-256 | `dr-web` |
| `~/.deep-reasoning/runtime/<commit>/` (one more, for a while) | the runtime `current` pointed at before an install, kept until the next start that installs nothing (W10) | `dr-app` |

Nothing deletes a `web/` entry but the user (README: "Removing it"). A tree is about 10 MB, Node 192 MB, a
runtime 474 MB (D5 as-built r3).

### 1.2 Decisions this design takes

The spec's seven decisions stand, with V1–V8 (§2). These are the next layer down. Letters are W, so they do not
collide with D5's A–P.

| # | Decision | Why | Rejected |
|---|---|---|---|
| W1 | **The command names the release's full commit.** `dr_web.cli.command_for(commit)` is the one place it is formed; the release notes carry it, the README carries the newest release's. | F1: a tag needs the remote on every start. The commit pins dr-web, and through the tarball's setup command (D5 §4.2.3) everything else. | `@v<ver>` (Q1 (d)'s literal: no offline restart, ever). `uv tool install` then a second command (Q2 (a): one command). |
| W2 | **`dr-web` is standard-library only; it installs Node itself**, `uv pip install --python <its own interpreter> --target <tmp> --require-hashes --no-deps` of `nodejs-wheel-binaries==22.12.0` with the two wheels' SHA-256, then relinks `npm` and `npx`, checks `node --version`, and renames the folder into place. A later start finds the folder and asks uv nothing. | F2, F3. 22.12.0 is the Node the app bundles (`scripts/download-node.mjs:75`), so the launcher runs on the same Node in both. uv's client carries the user's proxy, mirror and CA settings, which it has just used to build dr-web. The hashes make the wheel the one we tested. | Node as a dependency (F2). Node's official tarball from nodejs.org (the app's own bytes, but a new host, and Python's TLS: W4). `uv tool install` (writes into the user's tool and `~/.local/bin` folders: D5 decision C's reason). |
| W3 | **The package is `packages/dr-web`, distribution `deep-reasoning-web`, module `dr_web`, command `deep-reasoning`.** Outside the uv workspace (`exclude`), a dev dependency by path, so tests import it; the dev group also pins `nodejs-wheel-binaries==22.12.0`, the Node `tests/desktop/test_web_entry.py` runs. | The amendment's likely shape. `dr-app` runs first in every desktop launch and must stay small. Outside the workspace, D5's runtime install (`uv sync … --all-packages`, `runtime.py:411`) is unchanged: no browser command in it. Both `uvx` forms work (verified: excluded, and neither member nor excluded). | A member (the runtime gains a `deep-reasoning` command it never runs). The command inside `dr-app` (Node beside every desktop launch). |
| W4 | **`dr-web` downloads the tarball with `urllib`, through a TLS context that falls back to a system CA bundle** when the interpreter's default store is empty. | Standard library only. `uvx` may run dr-web on a python.org interpreter, whose default store is empty until "Install Certificates" runs; macOS has `/etc/ssl/cert.pem`. `HTTPS_PROXY` and `SSL_CERT_FILE` are honoured by `urllib` and OpenSSL. | `curl` (not on every Linux). Node's `fetch` (no proxy support in 22). |
| W5 | **The cache is content-addressed and never pruned.** The downloaded tarball keeps its release name; a tree is named by its tarball's SHA-256; Node by its version. Writes go to `<name>.tmp-<pid>` and are renamed; a rename that finds the target already there keeps the target. | Q2 (a): one version per command, so a cached version never changes. `--tarball FILE` (V6) and the release share one path. Two first starts at once never see a half-written entry. Pruning would need to know what a running stack uses (the window, W10). | Keying trees by version (a hand-built tarball of the same version would collide). |
| W6 | **`dr-web` execs Node.** | uv forwards SIGTERM to its child, and a terminal's SIGINT reaches the group once (verified, 0.8.17), so Node is signalled as it would be run directly; the launcher's shutdown (`dev-with-automation.mjs:1460–1476`) stops the services; Node's exit code is the command's. | A Python parent that forwards signals and waits (more code, a second process to stop). |
| W7 | **`dr-web` only fetches; `web.mjs` does everything the spec gave the entry** (checks, environment, ports, `main()`, failures, opening). | The tarball keeps working through `npx -y <url>` or `npx deep-reasoning@<ver>` (Q1 (a), (b)) with nothing new: Michael's "the machinery will be there". | Checks in Python (the npm doors would lose them). |
| W8 | **The environment: remove by prefix `OH_`, `VITE_`, `AUTOMATION_`, `INGRESS_`, `OPENHANDS_`, `POSTHOG_`, and the names `PORT`, `LOCAL_BACKEND_API_KEY`, `SESSION_API_KEY`, `AGENT_SERVER_URL`, `PYTHONPATH`, `PYTHONHOME`, `VIRTUAL_ENV`, `UV_PYTHON`, `NODE_OPTIONS`, `NODE_PATH`; set `DO_NOT_TRACK=1`;** say which were removed, by name, never by value. Before the launcher is imported. | The prefixes cover every variable the fork's scripts read (grep of `scripts/*.mjs` at `dr-3`, §9) and the agent-server's own knobs; an app opened from Finder sees none, and D5 decisions D and K rest on that. `PYTHONPATH`/`PYTHONHOME` reach every Python we start (the agent-server, `dr-app`, `dr-acp`); `VIRTUAL_ENV` makes uv warn in `dr-app`'s sync; `UV_PYTHON` picks the agent-server's Python; `NODE_OPTIONS`/`NODE_PATH` change the Node the launcher runs on. `logger.mjs` reads `OH_CANVAS_SAFE_STATE_DIR` at import, hence the order. `DO_NOT_TRACK` turns the agent-server's telemetry off (`dev-safe.mjs` `buildAgentServerTelemetryEnv`). Kept: every `UV_*` but `UV_PYTHON` (cache, index and TLS settings a user needs to reach PyPI; the runtime installs `--frozen`), `GIT_*`, proxies, `AGENT_CANVAS_DISABLE_TELEMETRY` (it can only turn telemetry off). | A list of exact names only (misses the agent-server's own `OH_*`). Keeping `PYTHONPATH` (E13 sets it as junk). |
| W9 | **Ports: 18000 is checked first, and is the lock; then the ingress port (8000, or `--port`); 3001 and 18001 move to an OS-assigned port when busy or equal to the ingress port.** Each probe binds `127.0.0.1:<port>` and closes, as the launcher's `tryPort` does (`dev-safe.mjs:248`). A moved port goes to the launcher as `OH_CANVAS_SAFE_VITE_PORT` / `OH_CANVAS_SAFE_AUTOMATION_PORT`, after W8 removed the user's. A busy ingress port is refused with an OS-assigned free port to pass as `--port`. The agent-server and automation ports are read from the tree's `config/defaults.json` (`ports`), 3001 and 8000 from the launcher's constants (`dev-with-automation.mjs:458, 463`). | Spec decision 5. Ephemeral ports never land on 8000 or 18000 (Linux 32768–60999, macOS 49152–65535). | A scan from the default upwards (more code; no better). |
| W10 | **The version-race window: `install_runtime` keeps the runtime `runtime/current` pointed at before it, and a start that installs nothing removes every runtime but the current one.** In `dr_app.runtime`, so the app and every front door get it, whichever starts second. | §3.4 works the race through. Every install happens in a before-start, which passed the port check, so the only stack that can be running is one in its startup window, and its processes run the runtime that was current before. Keeping that one means no install deletes files under a running process. The next start that installs nothing is past every such window, since 18000 was free for it, so pruning there is safe and bounds the cost to one extra runtime (474 MB) between an update and the next plain start. | The entry refusing while `setup.lock` is held: Node has no `flock`, so the probe would live in `dr-web` and the npm doors would lack it; it covers only a browser started second, never the app; and it leaves the gap between the first stack's before-start ending and its agent-server binding 18000, up to 34 s on a cold uv cache, which is exactly when versions differ. Keeping the old runtime until the next install (the spec's wording; two runtimes forever after the first update). |
| W11 | **`build.py` takes several targets in one run** (`linux web`, `mac-arm64 web`); `prepare()` does the checkout, the pin checks, `patch_defaults`, `npm ci` and `build:app` once; `package_desktop` and `package_web` follow. `web` builds on any machine. | Spec decision 1: one build, two packagings, one `defaults.json`. The tarball is platform-free (static files, scripts, pure-JS modules). | A separate web build. |
| W12 | **The tarball is `npm pack` of a staged `package/`**: the checkout's `build/`, `config/`, `scripts/` (`*.mjs`, `*.cjs`), `tools/` and `LICENSE`; `node_modules/` holding the runtime closure of `sirv` and `httpxy` read from the fork's `package-lock.json`; `bin/deep-reasoning.mjs`, ours; and a `package.json` we write. | What the packaged app carries of the checkout (`electron-builder.config.mjs` `files`, and its `RUNTIME_PACKAGES` closure, `:83`). The fork's MIT licence travels with its code. `npm pack` keeps it a valid npm package for the other doors. | Our own tar writer (the npm doors would need checking separately). |
| W13 | **Two build checks on the fork, at every web build:** the fork's `RUNTIME_PACKAGES` is still `sirv` and `httpxy`, and Electron's `main()` call still holds each option the entry copies. | A pin bump that adds a bare import, or changes Electron's call, would otherwise reach the browser silently (spec decision 2 rests on "as Electron does"). | Relying on E13 (it would not see a changed timeout). |
| W14 | **The release: the tag must be `v<app.version>`; the Linux job builds `linux web`; the notes carry the command; the README is updated after the tag** (the tagged commit cannot name itself), and `cross-repo.yml`'s nightly `pins` job fails while the README names an older release's commit. | `dr-web` fetches `releases/download/v<RELEASE>/…`. | A workflow that pushes the README (a push to `main` from CI; a PR it opens runs no CI). |
| W15 | **The browser opens with `open` (macOS) or `xdg-open` (Linux), detached, only when the session can show one:** not when `SSH_CONNECTION` or `SSH_TTY` is set, not on Linux without `DISPLAY` or `WAYLAND_DISPLAY`. | Spec decision 6. `xdg-open` with no display may start a text browser in the user's own terminal. | Always opening. |

---

## 2 · Where this design departs from the approved spec

- **V1 · The command names a commit, not `v<ver>`** (F1, W1). If Michael keeps the tag: `command_for` takes the
  version; the README can carry the next command before tagging; W14's README check and post-release commit go;
  and every start needs the network to resolve the tag. Q2 (a)'s offline restart, E13 claim 8 and the README's
  restart sentence go with it, and an outage stops the browser version entirely. Everything else in this design
  is the same.
- **V2 · Node is installed by `dr-web`, not resolved as its dependency** (F2, W2). Same wheel, same pin; it lands
  in `~/.deep-reasoning/web/node-22.12.0/` instead of uv's tool environment.
- **V3 · E13 does not drive onboarding.** It marks the browser onboarded in storage (`openhands-onboarded`) and
  starts from the home screen. The UX round removes onboarding from our build (its Q1 (a)), so a test of it would
  be rewritten within weeks. The spec's "the browser shows onboarding once more" stays true on `dr-3`; nothing
  tests it.
- **V4 · The window's fix keeps one extra runtime until the next plain start**, not "until the next install"
  (W10). It changes D5's runtime rule (`runtime.py:440–442`: delete every other); the README's data table says so.
- **V5 · Four `dr-app` sentences change** so a browser user is not told to reinstall an app (§5.3). The spec
  deferred them here.
- **V6 · `dr-web` has a third option, `--tarball FILE`.** E13, the smokes, and anyone before the first release
  run a tarball they built. The launcher still sees only the tarball and the port (spec decision 4); `web.mjs`
  takes two flags.
- **V7 · Two more CI checks than the spec's:** a post-release smoke of the real download on both OSes, and a
  pre-release check, in the macOS job, that the Python `uvx` picks can reach GitHub's release downloads (W4).
  Nothing else exercises the download before users do.
- **V8 · Size: about 1.5k lines, not about 0.9k** (§10).

The spec's §3 mock-up holds with these changes: the command line (V1); a first start adds `Installing Node
22.12.0 …` and `Fetching Deep Reasoning … ` before the first line (§5.1); the "Left out of the environment" line
when the terminal held any of W8's variables; the "No model key is saved yet" line goes with the UX round, through
setup (§8).

---

## 3 · Modules

| File | Change |
|---|---|
| `packages/dr-web/pyproject.toml`, `src/dr_web/{__init__,cli,cache,texts}.py` | new (§3.1, §4.1) |
| `desktop/web.mjs` | new: the entry, shipped as the tarball's `bin/deep-reasoning.mjs` (§3.2, §4.2) |
| `desktop/build.py` | the `web` target, `prepare`/`package_*` split, several targets per run, the closure, W13's checks, `verify_web` (§3.3, §4.3) |
| `packages/dr-app/src/dr_app/runtime.py`, `cli.py` | W10: keep the previous runtime; prune on a plain start (§3.4, §4.4) |
| `packages/dr-app/src/dr_app/texts.py` | four sentences (§5.3) |
| `pyproject.toml` | `exclude = ["packages/dr-web"]`; the path source; dev group `deep-reasoning-web`, `nodejs-wheel-binaries==22.12.0`; marker `web`, deselected by default; ruff `src` gains `packages/dr-web/src` |
| `uv.lock` | relocked (not read at Gate C) |
| `.github/workflows/cross-repo.yml` | paths gain `packages/dr-web/**`; `desktop-e2e` builds `linux web` and runs the coexistence test; new `web-e2e` (E13); `pins` runs the README's release check (§3.6) |
| `.github/workflows/desktop-release.yml` | the tag check; `linux web` and `mac-arm64 web`; the macOS web smoke; notes with the command; new `release-smoke` (§3.6) |
| `README.md` | "Run it in your browser"; the data table gains `web/` and W10's sentence (§3.5) |
| `tests/…` | §7 |

### 3.1 `dr-web`, the command

`deep-reasoning [--port N] [--no-open] [--tarball FILE]`, run by `uvx`. In order:

1. **Parse** with `argparse`; a bad option exits 2 with argparse's message. `--port` is an int; its range is
   `web.mjs`'s to check (one place).
2. **Find uv**: `os.environ["UV"]`, which `uvx` sets to its own binary (verified, 0.8.17), else
   `shutil.which("uv")`; neither → `texts.NO_UV`, exit 22.
3. **Node** (`ensure_node`): when `web/node-22.12.0/nodejs_wheel/bin/node` exists, use it, with no exec of it or
   uv. Else say `texts.installing_node()`, write the requirement line with both hashes to a temporary file, run
   `uv pip install --python sys.executable --target web/node-22.12.0.tmp-<pid> --require-hashes --no-deps -r
   <file>` with its output passed through, replace `bin/npm` and `bin/npx` by the two symlinks (F3), run `node
   --version` and require `v22.12.0`, then rename. A non-zero step: `texts.node_failed(step, code)`, the temporary
   folder removed, exit 23.
4. **The tarball**: `--tarball FILE` as given; else `web/deep-reasoning-web-<RELEASE>.tgz` if present; else say
   `texts.fetching(RELEASE)` and download `release_url(RELEASE)` into it (W4, W5). A failure:
   `texts.fetch_failed(...)`, nothing kept, exit 23.
5. **The tree** (`unpacked`): SHA-256 of the file; if `web/tree-<16 hex>/package/bin/deep-reasoning.mjs` exists,
   done. Else open it with `tarfile`, require gzip, every member under `package/`, and extract with
   `filter="data"` (no absolute paths, no `..`, no links out, no devices) into `tree-<16 hex>.tmp-<pid>`; require
   `package/package.json` to name `deep-reasoning-web` (and, for a downloaded file, version `RELEASE`) and
   `package/bin/deep-reasoning.mjs` to exist; rename. Anything else: `texts.not_a_tarball(path, reason)`, the
   temporary folder removed, exit 23.
6. **The environment** (`stack_path`): `PATH` = Node's `bin`, then the user's `PATH` without the folder of
   `sys.executable` (uvx's tool environment, whose `python` would shadow the user's for every conversation), then
   uv's folder if `uvx` is not found on what is left. Nothing else changes here: W8 is `web.mjs`'s.
7. **Exec** `os.execve(node, [node, entry, *forward], env)`, `forward` being `--port N` and `--no-open` as given.

Leftovers: an entry `*.tmp-<pid>` whose pid is not alive (`os.kill(pid, 0)` raises `ProcessLookupError`) is
removed before step 3. `~/.deep-reasoning` is created `0700` if absent, as `setup_lock` does (`cli.py:66–67`).

### 3.2 `desktop/web.mjs`, the entry

Node built-ins only (the tarball's `node_modules` holds only the launcher's closure). Runs only when it is the
main module, so tests can import its pure parts.

1. **Parse** `--port N` (an integer 1–65535, not the agent-server's port) and `--no-open` (`node:util`
   `parseArgs`, strict). Anything else: `usage(what)`, exit 2.
2. **Read** `../package.json` (the version) and `../config/defaults.json` (`ports.agentServer`,
   `ports.automation`).
3. **Check** Node (`process.versions.node` ≥ 22.12.0), uv (`uv --version` ≥ 0.8.17, and `uvx` on `PATH`), git
   (`git --version`). Each problem is one sentence (§5.2); any → exit 22, nothing started. Else the first line,
   `ready_line(…)`.
4. **Clean** `process.env` (W8); if anything was removed, `left_out(names)`.
5. **Ports** (W9). Agent-server port held → `already_running`, exit 20. Ingress port held → `port_taken(port,
   free)`, exit 21. Then the two movable ones.
6. **Hand over**: `process.argv = [process.argv[0], process.argv[1], "--port", String(ingress)]`; `const { main } =
   await import(new URL("../scripts/dev-with-automation.mjs", import.meta.url))`; install `process.on("exit")`,
   which sets `process.exitCode` to a failure code once one is chosen (the launcher's shutdown calls
   `process.exit(0)`; Node 22.12 lets the listener change it, verified); `await main({...ELECTRON_OPTIONS,
   staticDir: <tree>/build})`.
7. **A rejection** → `failure(error, { agentServerHeldNow })` gives one line and a code (§6), printed, then
   `process.exit(code)`. Nothing is running by then: before-start fails with nothing started, after-ready stops the
   agent-server before it throws (`dev-with-automation.mjs:2035–2040`), and an agent-server that exits before it
   answers is the only process.
8. **`agentServerReady === false`** (`:2077`): `not_ready`, code 24, and `process.kill(process.pid, "SIGTERM")`,
   which runs the launcher's own shutdown, as the app's quit does.
9. **Ready**: wait for `http://127.0.0.1:<ingress>/server_info` to answer 200, up to 60 s, as Electron's
   `waitForAgentServer` (`electron/main.mjs:731`); on timeout, as 8. Then open `http://localhost:<ingress>` (W15)
   and print `running_opened(url)` or `running(url)`. Then nothing: the launcher's services keep Node alive until
   a signal.

The launcher prints its own banner after `main()` (`printBanner`, "Agent Canvas + Automation Stack" and "Press
Ctrl+C to stop"); our line follows it. Its banner and the browser tab's "OpenHands" are TASK-44's (spec §5).

### 3.3 `desktop/build.py web`

`uv run desktop/build.py web` (any machine); `uv run desktop/build.py linux web` on the Linux release runner and in
`desktop-e2e`; `mac-arm64 web` on the Mac. `check` stays alone.

1. `prepare` (all targets, once): `checkout_canvas`, `check_pins`, `patch_defaults(…)` written to the checkout,
   `npm ci`, `npm run build:app` with `VITE_DO_NOT_TRACK=1` (today's `build()` lines 379–393, moved). Returns the
   checkout and the defaults it wrote.
2. `package_desktop(target, …)`: today's `build()` from `download-uv.mjs` on (lines 394–427), unchanged.
3. `package_web(…)`:
   - `check_web_contract(canvas)`; any problem → `SystemExit` with the sentences.
   - Stage `work/web/package/`: W12's trees copied; `runtime_closure(lock, WEB_RUNTIME_PACKAGES)` copied from
     `canvas/<path>` to `package/<path>`, each path as the lock names it (nested ones included); `desktop/web.mjs`
     as `bin/deep-reasoning.mjs`, mode 0755; `package.json` = `web_package_json(version, closure)`.
   - `npm pack --pack-destination <repo>/dist` in `work/web/package/`: `dist/deep-reasoning-web-<version>.tgz`.
   - `verify_web(tarball, …)`, then return it.

The tarball's `package.json` (version and closure from the pins and the fork's lock):

```json
{
  "name": "deep-reasoning-web",
  "version": "1.0.0-rc.1",
  "description": "Deep Reasoning in your browser: the desktop app's Canvas build and launcher, started from a terminal",
  "private": true,
  "license": "SEE LICENSE IN LICENSE",
  "type": "module",
  "bin": { "deep-reasoning": "bin/deep-reasoning.mjs" },
  "engines": { "node": ">=22.12.0" },
  "files": ["bin", "build", "config", "scripts", "tools", "LICENSE"],
  "dependencies": { "sirv": "3.0.2", "httpxy": "0.5.5" },
  "bundleDependencies": ["sirv", "httpxy"]
}
```

`private` keeps an accidental `npm publish` from happening; front door (b) would flip it. Whether our own
`web.mjs` is MIT too is Michael's (§11 item 5).

`verify_web` refuses (`SystemExit`, one sentence each): a member outside `package/`; any path holding
`deep_reasoner` (D5's rule for the desktop payloads, `FORBIDDEN_IN_PAYLOAD`); `node_modules/` holding other than
the closure's paths; `config/defaults.json` other than what `prepare` wrote; `bin/deep-reasoning.mjs` other than
`desktop/web.mjs`'s bytes; a `package.json` other than `web_package_json`'s. Paths only, as for the desktop
packages: after the UX round `defaults.json` holds `"lockedProfile": "deep_reasoner"`, which a content check would
refuse.

### 3.4 `dr_app`: the window

What happens when stack B (version Y) starts while stack A (version X) is in its startup window, today and with
W10:

| Moment | Today | With W10 |
|---|---|---|
| A: port check, then before-start holds `setup.lock`, installs X | — | — |
| B: port check passes (nothing bound yet); its before-start waits on the lock | — | — |
| A's before-start ends; A's agent-server starts (seconds, 34 s cold) | | |
| B gets the lock first, installs Y: `current` → Y | **X deleted** | X kept |
| A's after-ready (waited on the lock) stages the App and starts its backend from `current` | Y's | Y's |
| B's agent-server cannot bind 18000; B fails (`already_running_elsewhere`, exit 20) | | |
| Or: A's after-ready ran before B got the lock, so A runs X's backend and maybe a conversation's `dr-acp` | **those lose their files** | they keep running on X |

Either way A then starts new processes from Y's runtime under X's Canvas and agent-server until it is restarted,
and its restart reinstalls X (which keeps Y). That mixed run is left, and named (§11 item 3); it needs three
starts within one window to delete anything (a second install keeps only its own previous one).

`install_runtime`: read `previous` = the name `runtime/current` links to (or `None`) before the link moves; after
it, remove every entry of `runtime/` but `commit`, `current`, the source tree and `previous`. `before_start`: on the
cheap path (`runtime_is_current`), `prune_runtimes(layout, state.runtime.commit)`, under the lock it already holds.

### 3.5 The README

A section **"Run it in your browser"** after "Install". What it says, in this order (the Implementer writes the
prose; `test_readme.py` pins the strings in brackets):

1. What you need: the same computers and the same read access to deep_reasoner_beta as the app (a link to
   "What you need", not a copy); **uv 0.8.17 or later** [`curl -LsSf https://astral.sh/uv/install.sh | sh`]; nothing
   else: uv brings Python and Node.
2. The command for the newest release, one line, with its version above it [`command_for(<commit>)`]; and where each
   release's own is (its release page). Before the first release: build the tarball (`uv run desktop/build.py
   web`) and add `--tarball dist/deep-reasoning-web-<version>.tgz` to the command at the commit you built.
3. The first start: what setup does is the app's first launch ([link to "The first launch"], not restated), its
   lines in the terminal; then `http://localhost:8000` opens.
4. Stopping [`Ctrl+C`]: Ctrl+C or closing the terminal stops everything; closing the tab stops nothing.
5. Restarting and updating: the same command again installs nothing; it needs no network within about ten minutes
   of a start that had it, and after that the agent-server's start asks PyPI again (F4; P1 lifts it) [`ten
   minutes`]; the next release's command updates once.
6. Ports [`--port`, `18000`]: the page on 8000 or `--port N`; 18000 is fixed and is why only one runs per computer;
   3001 and 18001 move on their own; [`--no-open`].
7. Beside the app: never both at once; the same data; onboarding's flag and the costs switch are per browser.
8. Browsers [the ones E13 passes, Q4 (a)].
9. Removing it: `rm -rf ~/.deep-reasoning/web` [`~/.deep-reasoning/web`]; all of it, as Uninstall says.

The data table gains `~/.deep-reasoning/web/` ("Node, and the browser version's files, from the command") and, on
the `runtime/` row, "after an update, the version before stays until the next start that installs nothing".

### 3.6 Workflows

**`cross-repo.yml`**
- `on.pull_request.paths` gains `packages/dr-web/**` (`desktop/web.mjs` is under `desktop/**`).
- `pins`: after `build.py check`, `uv run pytest -m crossrepo tests/desktop/test_readme.py` (W14's check; the
  job's checkout has the tags).
- `desktop-e2e`: `uv run desktop/build.py linux web`; after E12, `xvfb-run -a uv run pytest -m desktop
  tests/desktop/test_coexistence.py -v -rA`.
- `web-e2e` (new, ubuntu-24.04, 60 min): checkout at the head commit, `fetch-depth: 0`; setup-node 24 (the build
  only); setup-uv, Python 3.12; the `insteadOf` line; `uv sync --locked`; `uv run desktop/build.py web`; `uv run
  playwright install --with-deps chromium firefox webkit`; the AppArmor sysctl for `unshare` (as `desktop-e2e`);
  `uv run pytest -m web tests/desktop/test_e13.py -v -rA`; on failure, the command's log as an artifact.

**`desktop-release.yml`**
- `cross-repo-green` gains a step: on a tag, `$GITHUB_REF_NAME` must be `v` + `desktop/pins.toml`'s
  `app.version`, else `::error::` naming both.
- `linux`: `uv run desktop/build.py linux web`; the artifact gains `dist/*.tgz`.
- `macos`: `uv run desktop/build.py mac-arm64 web`; after the launch smoke, `uv run pytest -m web
  tests/desktop/test_web_smoke.py -v -rA` with `DR_WEB_TARBALL` set to the tarball; the uploads gain its log.
- `release`: the notes (`gh release create --notes`) gain the browser command, formed by `python3 -c` with
  `PYTHONPATH=packages/dr-web/src` (a sparse checkout of `packages/dr-web`; `dr_web` is standard library only).
  The `.tgz` is attached with the rest (`packages/*`).
- `release-smoke` (new; needs `release`; matrix ubuntu-24.04, macos-latest; no setup-node): `uv run pytest -m web
  tests/desktop/test_web_smoke.py` with `DR_WEB_COMMIT=$GITHUB_SHA` and no tarball, so the command downloads the
  release's asset as a user's would.

---

## 4 · Signatures

Each block is the module's public surface; private helpers are the Implementer's.

### 4.1 `dr_web` (`packages/dr-web/src/dr_web/`)

```python
# pyproject.toml: name "deep-reasoning-web", version "0.1.0", requires-python ">=3.12",
# dependencies = [], [project.scripts] deep-reasoning = "dr_web.cli:main", hatchling, packages ["src/dr_web"].

# dr_web/__init__.py
"""deep-reasoning: Deep Reasoning in the browser, from one uvx command (TASK-48).

Standard library only: uvx runs a commit-pinned package with no dependencies from its cache for good, while one
with a PyPI dependency asks the index again once its ten-minute answer has expired."""

# dr_web/cache.py
ROOT_DIRNAME: Final = ".deep-reasoning"            # dr_app.layout.ROOT_DIRNAME, mirrored; a test holds them equal
WEB_DIRNAME: Final = "web"
RELEASES: Final = "https://github.com/michaeltheologitis/deep-reasoning/releases"
PACKAGE_NAME: Final = "deep-reasoning-web"         # the tarball's package.json name; build.WEB_PACKAGE_NAME
ENTRY: Final = "package/bin/deep-reasoning.mjs"
NODE_VERSION: Final = "22.12.0"                    # the app's (download-node.mjs:75); the dev group's pin
NODE_WHEEL: Final = "nodejs-wheel-binaries"
NODE_WHEEL_SHA256: Final = (                       # PyPI, 2024-12-06
    "335176ffa5f753c4d447af83f70987f5f82becdf84fadf56d5c0036379826cff",  # manylinux2014 x86_64
    "8ed26eac5a96f3bfcd36f1eb9c397f07392e8b166895e0a65eb6033baefa0217",  # macosx_11_0 arm64
)
NPM_LINKS: Final = {"npm": "../lib/node_modules/npm/bin/npm-cli.js",
                    "npx": "../lib/node_modules/npm/bin/npx-cli.js"}
FALLBACK_CA_FILES: Final = ("/etc/ssl/cert.pem",                     # macOS
                            "/etc/ssl/certs/ca-certificates.crt",    # Debian, Ubuntu
                            "/etc/pki/tls/certs/ca-bundle.crt")      # Fedora, RHEL
DOWNLOAD_TIMEOUT_S: Final = 60.0

class FetchError(Exception):
    """A failure dr-web explains: message printed, exit_code returned (22 or 23)."""
    def __init__(self, exit_code: int, message: str) -> None: ...

@dataclass(frozen=True)
class WebLayout:
    root: Path                                     # ~/.deep-reasoning/web
    @classmethod
    def default(cls) -> "WebLayout": ...           # Path.home() / ROOT_DIRNAME / WEB_DIRNAME
    def downloaded(self, version: str) -> Path: ...   # root / tarball_name(version)
    def tree(self, sha256: str) -> Path: ...           # root / f"tree-{sha256[:16]}"
    @property
    def node_dir(self) -> Path: ...                    # root / f"node-{NODE_VERSION}"
    @property
    def node(self) -> Path: ...                        # node_dir / "nodejs_wheel" / "bin" / "node"

def tarball_name(version: str) -> str: ...         # f"deep-reasoning-web-{version}.tgz"; build.web_tarball_name
def release_url(version: str) -> str: ...          # f"{RELEASES}/download/v{version}/{tarball_name(version)}"
def tls_context(*, fallbacks: Sequence[str] = FALLBACK_CA_FILES) -> ssl.SSLContext:
    """ssl.create_default_context(); when its store holds no CA certificate (cert_store_stats()["x509_ca"] == 0),
    the first fallback that exists is loaded into it as well. An OpenSSL that reads a hashed capath lazily also
    reports 0; loading the bundle beside it then changes nothing."""
def download(url: str, dest: Path, *, timeout_s: float = DOWNLOAD_TIMEOUT_S) -> None:
    """dest, written whole or not at all (dest.tmp-<pid>, then rename). Raises FetchError(23,
    texts.fetch_failed(dest.name, <where>, <reason>)): an HTTP status, a refused or timed-out connection, TLS."""
def released_tarball(layout: WebLayout, version: str, *, log: Callable[[str], None]) -> Path:
    """layout.downloaded(version) if present (no network); else texts.fetching(version), then download()."""
def unpacked(layout: WebLayout, tarball: Path, *, expect_version: str | None) -> Path:
    """The tree's package/ folder, unpacked once per content (§3.1 step 5). expect_version is RELEASE for a
    download, None for --tarball. Raises FetchError(23, texts.not_a_tarball(str(tarball), <reason>)), leaving no
    tree."""
def ensure_node(layout: WebLayout, *, uv: str, python: str, log: Callable[[str], None]) -> Path:
    """layout.node; installed once (§3.1 step 3) with uv's output passed to log line by line. Raises
    FetchError(23, texts.node_failed(<step>, <code>)), leaving no node_dir."""
def remove_leftovers(layout: WebLayout) -> None:
    """Every <name>.tmp-<pid> under root whose pid is not alive."""

# dr_web/cli.py
RELEASE: Final = "1.0.0-rc.1"                      # desktop/pins.toml [app] version; a test holds them equal
REPOSITORY: Final = "https://github.com/michaeltheologitis/deep-reasoning"   # build.DEEP_REASONING
SUBDIRECTORY: Final = "packages/dr-web"
COMMAND: Final = "deep-reasoning"
EXIT_NEEDS: Final = 22                             # web.mjs's EXIT.needs
EXIT_FETCH: Final = 23

def command_for(commit: str) -> str:
    """The README's and the release notes' line. Raises ValueError for anything but 40 hex.
    f"uvx --from git+{REPOSITORY}@{commit}#subdirectory={SUBDIRECTORY} {COMMAND}" """
def find_uv(env: Mapping[str, str]) -> str:
    """env["UV"] (uvx sets it), else shutil.which("uv", path=env["PATH"]). Raises FetchError(22, texts.NO_UV)."""
def stack_path(path: str, *, node_bin: Path, tool_bin: Path, uv: str) -> str:
    """node_bin, then path without tool_bin, then uv's folder when no uvx is on what is left."""
def main(argv: Sequence[str] | None = None) -> int:
    """deep-reasoning [--port N] [--no-open] [--tarball FILE]. Execs Node on success, so returns only a
    failure's exit code (2, 22 or 23)."""

# dr_web/texts.py: §5.1. A constant is a sentence without fields; a function returns one with its fields
# (D1's, D2's and D5's rule, D5 decision O).
```

### 4.2 `desktop/web.mjs`

```js
// Exports for tests; the entry runs only as the main module.
export const ELECTRON_OPTIONS = Object.freeze({    // electron/main.mjs:663-672 at dr-3, but onServiceLog (the splash)
  bannerTitle: "OpenHands Agent Canvas",
  staticMode: true,
  mode: "agent-canvas",
  isPublic: false,
  skipNpmCheck: true,
  agentServerReadyTimeoutMs: 10 * 60_000,
});
export const MINIMUM = Object.freeze({ node: "22.12.0", uv: "0.8.17" });
export const INGRESS_PORT = 8000;                  // dev-with-automation.mjs:458
export const FRONTEND_PORT = 3001;                 // :463
export const REMOVED_PREFIXES = Object.freeze(["OH_", "VITE_", "AUTOMATION_", "INGRESS_", "OPENHANDS_", "POSTHOG_"]);
export const REMOVED_NAMES = Object.freeze(["PORT", "LOCAL_BACKEND_API_KEY", "SESSION_API_KEY", "AGENT_SERVER_URL",
  "PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV", "UV_PYTHON", "NODE_OPTIONS", "NODE_PATH"]);
export const EXIT = Object.freeze({ usage: 2, running: 20, port: 21, needs: 22, start: 24 });
export const READY_WAIT_MS = 60_000;               // electron/main.mjs:731

export class UsageError extends Error {}

/** {port: number | null, open: boolean}. Throws UsageError(what) (§5.2 usage). */
export function parseCommandLine(argv, { agentServerPort }) {}

/** Deletes W8's variables from env in place, sets DO_NOT_TRACK=1; the deleted names, sorted. */
export function cleanEnvironment(env) {}

/** "22.12.0" ≥ "22.9.1"; a leading "v" and any suffix after the third number ignored. */
export function versionAtLeast(found, minimum) {}

/** The §5.2 sentences for what is missing or too old; empty when all is well.
 *  found: {node: string, uv: string | null, uvx: boolean, git: string | null} */
export function requirementProblems(found) {}

/** Whether 127.0.0.1:port can be bound now (bound, then closed). */
export async function portIsFree(port) {}

/** A port the OS hands out on 127.0.0.1 (bound to 0, then closed). */
export async function freePort() {}

/** {ingress, frontend, automation, moved: {name: port}} | {refusal: {line, code}}. moved lists the env
 *  variables to set: OH_CANVAS_SAFE_VITE_PORT, OH_CANVAS_SAFE_AUTOMATION_PORT. */
export async function choosePorts({ agentServer, ingress, frontend, automation }) {}

/** {line, code} for a rejection of main() (§6): a SetupCommandError by its name, phase, reason and exitCode;
 *  anything else by agentServerHeldNow, then its first line. */
export function failure(error, { agentServerHeldNow }) {}

/** "open", "xdg-open", or null (W15). */
export function opener(platform, env) {}

/** The entry: §3.2 steps 1–9. */
export async function run(argv = process.argv.slice(2), env = process.env) {}
```

### 4.3 `desktop/build.py`

```python
# New and changed; everything else as at 9e8109e.
WEB_PACKAGE_NAME: Final = "deep-reasoning-web"
WEB_ENTRY: Final = REPO / "desktop" / "web.mjs"
WEB_TREES: Final = ("build", "config", "scripts", "tools")   # electron-builder.config.mjs `files`, less electron/
WEB_SCRIPT_SUFFIXES: Final = (".mjs", ".cjs")                 # its filter for scripts/
WEB_RUNTIME_PACKAGES: Final = ("sirv", "httpxy")             # its RUNTIME_PACKAGES (:83), mirrored and checked
# What web.mjs copies of Electron's main() call (electron/main.mjs:663-672), each as the fork writes it.
ELECTRON_CALL: Final = ('bannerTitle: "OpenHands Agent Canvas"', "staticMode: true", 'mode: "agent-canvas"',
                        "isPublic: false", "skipNpmCheck: true", "agentServerReadyTimeoutMs: 10 * 60_000")
Target = Literal["linux", "mac-arm64", "web"]
DesktopTarget = Literal["linux", "mac-arm64"]

def web_tarball_name(version: str) -> str: ...      # f"{WEB_PACKAGE_NAME}-{version}.tgz"
def runtime_closure(lock: Mapping[str, Any], roots: Sequence[str]) -> dict[str, str]:
    """package-lock.json (v3) paths and versions of roots and everything their "dependencies" and
    "optionalDependencies" resolve to, npm's way: the nearest node_modules/<name> from the dependent's own path
    upwards. {"node_modules/sirv": "3.0.2", "node_modules/@polka/url": "1.0.0-next.29", …}. Raises ValueError
    naming a dependency the lock does not hold."""
def web_package_json(version: str, closure: Mapping[str, str]) -> dict[str, Any]: ...   # §3.3's object
def check_web_contract(canvas: Path) -> list[str]:
    """W13's two checks against the checkout; the problems as sentences (§5.4)."""
def prepare(pins: Pins, *, repo: Path, work: Path) -> tuple[Path, dict[str, Any]]:
    """§3.3 step 1: the checkout and the defaults written. Raises SystemExit with check_pins's sentences."""
def package_desktop(target: DesktopTarget, *, pins: Pins, repo: Path, canvas: Path) -> list[Path]: ...
def package_web(*, pins: Pins, repo: Path, canvas: Path, defaults: Mapping[str, Any]) -> Path: ...
def verify_web(tarball: Path, *, version: str, defaults: Mapping[str, Any], closure: Mapping[str, str],
               entry: bytes) -> None:
    """§3.3's refusals, as SystemExit(sentence)."""
def build(targets: Sequence[Target], *, pins: Pins, repo: Path, work: Path) -> list[Path]:
    """wrong_machine for each desktop target first, then prepare once, then each target's packages."""
def main(argv: Sequence[str] | None = None) -> int:
    """uv run desktop/build.py {linux|mac-arm64|web}... | check [--work DIR]; check combines with nothing."""
```

### 4.4 `dr_app.runtime`, `dr_app.cli`

```python
def install_runtime(layout, source, commit, *, uv, log) -> RuntimeRecord:
    """… then the rename and the link. Keeps the runtime runtime/current pointed at before (a stack still
    starting may run it: TASK-48 W10) and removes every other. Raises SetupError(11, …) on any non-zero step,
    leaving runtime/current as it was."""

def prune_runtimes(layout: AppLayout, keep: str) -> None:
    """Every entry of runtime/ but keep and current removed, an interrupted install's included. before-start
    calls it, under setup.lock, only when the runtime is current."""

# dr_app.cli.before_start: `if runtime_is_current(...): prune_runtimes(layout, state.runtime.commit)` before
# the bin/ links; the install branch is unchanged.
```

---

## 5 · Texts (verbatim; tests assert these)

### 5.1 `dr_web.texts`

| Name | Sentence |
|---|---|
| `NO_UV` | `✗ uv was not found: run this command with uvx, which comes with uv (https://docs.astral.sh/uv/).` |
| `installing_node(version)` | `Installing Node {version} for Deep Reasoning, once (about 55 MB) …` |
| `node_failed(step, code)` | `✗ Installing Node failed ({step} exited {code}); its output is above. Check that this computer is online, then run the same command again.` |
| `fetching(version)` | `Fetching Deep Reasoning {version} for your browser, once (about 3 MB) …` |
| `fetch_failed(name, where, reason)` | `✗ Could not download {name} from {where} ({reason}): check that this computer is online, then run the same command again. Nothing was changed.` |
| `not_a_tarball(path, reason)` | `✗ {path} is not a Deep Reasoning browser tarball ({reason}). Nothing was changed.` |

`where` is `github.com/michaeltheologitis/deep-reasoning/releases/tag/v<version>`. `reason` is `HTTP 404`, `connection
refused`, `timed out`, or the TLS error's own words; for `not_a_tarball`, `not gzip`, `a member outside package/`,
`unsafe member <name>`, `its package.json names <name> <version>`, `no bin/deep-reasoning.mjs`.

### 5.2 `desktop/web.mjs`

| Name | Sentence |
|---|---|
| `ready_line(v, node, uv, git)` | `Deep Reasoning {v} · Node {node} ✓ · uv {uv} ✓ · git {git} ✓` |
| `left_out(names)` | `Left out of the environment, as the app runs without them: {names joined by ", "}` |
| `already_running(port)` | `✗ Deep Reasoning is already running on this computer: port {port} is in use (the app, another terminal, or an Agent Canvas). Stop it, then run this again. Nothing was changed.` |
| `started_elsewhere` | `✗ Deep Reasoning was started elsewhere while this one was starting (the app, or another terminal), so this one stopped. Use that one, or stop it and run this again.` |
| `port_taken(port, free)` | `✗ Port {port} is in use by another program. Start Deep Reasoning on another: add --port {free} to the command.` |
| `node_too_old(found)` | `✗ Deep Reasoning needs Node 22.12 or later, and this is {found}. Install it from https://nodejs.org, then run the same command.` |
| `NO_UV` | `✗ uv was not found on PATH. Install it with: curl -LsSf https://astral.sh/uv/install.sh \| sh  then open a new terminal and run the same command.` |
| `uv_too_old(found)` | `✗ Deep Reasoning needs uv 0.8.17 or later, and this is {found}. Update it (uv self update, or the way you installed it), then run the same command.` |
| `NO_GIT` | `✗ git was not found: Deep Reasoning installs deep_reasoner with it. On macOS run xcode-select --install; on Linux install git. Then run the same command.` |
| `setup_stopped_before(code)` | `✗ Setup stopped before anything started (exit {code}): its last line above says why.` |
| `setup_stopped_after(code)` | `✗ Setup stopped once the agent-server was up (exit {code}), so everything was stopped: its last line above says why.` |
| `SETUP_TIMED_OUT` | `✗ Setup was still running after 15 minutes, so it was stopped. Run the same command again: it goes on from what it already downloaded.` |
| `setup_killed(signal)` | `✗ Setup was stopped by {signal} before Deep Reasoning started.` |
| `NOT_READY` | `✗ The agent-server did not answer within 10 minutes, so everything was stopped. A first start downloads Python and its packages: check that this computer is online, then run the same command again.` |
| `could_not_start(first_line)` | `✗ Deep Reasoning could not start: {first_line}` |
| `running_opened(url)` | `Deep Reasoning is running at {url}, opened in your browser. Ctrl+C stops it.` |
| `running(url)` | `Deep Reasoning is running at {url}: open it in your browser. Ctrl+C stops it.` |
| `usage(what)` | `✗ {what}. The options are --port N and --no-open.` |

`usage`'s `what`: `Unknown option {o}`, `--port needs a number from 1 to 65535`, `--port cannot be {agentServer}: Deep
Reasoning's agent-server uses it`. The `\|` above is a table escape; the sentence has a plain `|`. None of these names
a model key: the UX round removes setup's key line, and this command adds none (§8).

### 5.3 `dr_app.texts`: the four that said "the app" (V5)

| Name | Sentence after |
|---|---|
| `NOTHING_INSTALLED` | `✗ Nothing is installed yet: start Deep Reasoning once (the app, or its browser command), then run this again.` |
| `NO_AGENT_SERVER` | `✗ The after-ready phase needs AGENT_SERVER_URL and SESSION_API_KEY, which Deep Reasoning's launcher sets.` |
| `state_from_a_newer_app(path, version)` | `✗ {path} was written by a newer Deep Reasoning (its version {version}; this one reads 1). Start the newer one again: the app, or its browser command. To set this one up from the start instead, delete {path}: your data stays, but a folder chosen with dr-app home is forgotten.` |
| `state_unusable(path, reason)` | `✗ {path} cannot be used: {reason}. Delete it and start Deep Reasoning again: setup then installs as on a first start, which needs the network. Your data stays, but a folder chosen with dr-app home must be chosen again.` |

`NO_UV` stays: the entry checks uv before setup runs, so a browser start never reaches it.

### 5.4 `desktop/build.py`

| Name | Sentence |
|---|---|
| `runtime_packages_changed(found)` | `✗ The Canvas fork's electron-builder.config.mjs strips the app's node_modules to {found}, but desktop/build.py bundles sirv and httpxy for the browser: bundle the same.` |
| `electron_call_changed(missing)` | `✗ The Canvas fork's electron/main.mjs no longer calls main() with {missing}, which desktop/web.mjs copies: make them agree.` |
| `web_tarball_wrong(name, why)` | `✗ {name} {why}.` (`why`: `carries deep_reasoner: <paths>`, `has a member outside package/: <path>`, `bundles <paths> beyond sirv's and httpxy's closure`, `carries other defaults than this build wrote`, `carries another bin/deep-reasoning.mjs than desktop/web.mjs`, `carries another package.json than the build writes`) |

---

## 6 · Exit codes

One table for the command; `dr-app`'s 10–14 (D5 B27) pass through unchanged, and 20–24 are the browser's.

| Code | Who | Meaning |
|---|---|---|
| 0 | the launcher | stopped by Ctrl+C, SIGTERM or the terminal closing |
| 2 | dr-web, web.mjs | a bad option |
| 10–14 | dr-app, through the launcher | setup explained itself (its last line); `web.mjs` exits with setup's own code when `reason` is `exit` and the code is 10–19 |
| 20 | web.mjs | already running: port 18000 held before the start, or taken during it (`started_elsewhere`) |
| 21 | web.mjs | the ingress port held by another program |
| 22 | dr-web, web.mjs | a requirement missing or too old (Node, uv, uvx, git) |
| 23 | dr-web | Node or the tarball could not be fetched, installed or trusted |
| 24 | web.mjs | the stack did not start: setup timed out, was killed or exited outside 10–19; the agent-server not ready or gone; any other rejection of `main()` |
| 1 | anyone | a bug: an exception nothing above names |

---

## 7 · Testing and CI

Every test runs with no paid model call; the model is FakeOpenAI where one answers (E12's). Markers: `web` is
new (pyproject's `addopts` deselects it with the others); E13 and the smokes carry it, the coexistence test carries
`desktop`.

### 7.1 `dr-web` (`tests/web/test_dr_web.py`, default suite)

A local `http.server` on 127.0.0.1 stands for the release; a stub `uv` on `PATH` stands for the Node install
(it records its argv and lays out a `nodejs_wheel/` tree with a `node` that prints `v22.12.0`).

- `test_the_command_is_dr_webs_at_a_commit_and_its_constants_are_the_builds`: `command_for` of 40 hex; `ValueError`
  for `v1.0.0`; `REPOSITORY == build.DEEP_REASONING`, `RELEASE == pins.app.version`, `PACKAGE_NAME ==
  build.WEB_PACKAGE_NAME`, `tarball_name == build.web_tarball_name`, `ROOT_DIRNAME == dr_app.layout.ROOT_DIRNAME`,
  `NODE_VERSION` equal to the dev group's `nodejs-wheel-binaries` pin.
- `test_a_release_tarball_downloads_once_and_a_restart_needs_no_server`: the second `released_tarball` and
  `unpacked` run with the server stopped and return the same tree.
- `test_a_file_that_is_not_the_tarball_is_refused_and_leaves_nothing` (parametrized: not gzip; `../x`; an absolute
  member; a symlink out; another package name; a download of another version): exit 23, the reason in the
  sentence, no `tree-*` left.
- `test_a_failed_download_names_the_file_and_keeps_nothing` (404; refused): no file at `downloaded(version)`.
- `test_node_installs_once_with_both_hashes_and_working_npm_links`: the stub's argv holds `--target`,
  `--require-hashes`, `--python sys.executable`, `--no-deps`, both hashes; `bin/npm`, `bin/npx` are the two
  links; a second `ensure_node` runs no uv.
- `test_a_failed_node_install_leaves_no_folder`.
- `test_the_stack_path_puts_node_first_and_drops_uvxs_environment` (with and without `uvx` on the rest).
- `test_main_execs_the_entry_with_the_flags_given` (`os.execve` replaced by a recorder): argv `[node, <tree>/bin/
  deep-reasoning.mjs, --port, 8765, --no-open]`; `PATH` as `stack_path`.
- `test_tls_falls_back_to_a_system_bundle_when_the_default_store_is_empty` (`fallbacks` passed in).

### 7.2 The entry (`tests/desktop/test_web_entry.py`, default suite)

Black-box: each test builds a tree (`bin/deep-reasoning.mjs` = `desktop/web.mjs`, a `package.json`,
`config/defaults.json` whose `ports` are free ports the test chose, and a **stub launcher**
`scripts/dev-with-automation.mjs`) and runs it with the dev group's Node (`nodejs_wheel`), stub `uv`, `uvx` and
`git` on `PATH`, `--port <free>`. The stub's `main(options)` writes `record.json` beside itself (`options`,
`process.argv`, `process.env`) and does what `stub.json` says: `ready` (serves `/server_info` 200 on the ingress
port), `not-ready` (returns `{agentServerReady: false}`), or throws an `Error` named `SetupCommandError` with
`phase`, `reason`, `exitCode`; like the real one it exits 0 on SIGINT and SIGTERM. Pure parts are imported with
`node --input-type=module -e`.

- `test_the_launcher_gets_electrons_options_one_port_and_a_clean_environment`: the terminal holds
  `OH_AGENT_SERVER_GIT_REF`, `VITE_POSTHOG_API_KEY`, `PORT`, `PYTHONPATH`, `VIRTUAL_ENV`,
  `NODE_OPTIONS=--max-old-space-size=512`, `UV_CACHE_DIR`; the record has `ELECTRON_OPTIONS` and `staticDir`, argv
  `[…, --port, P]`, none of the six, `UV_CACHE_DIR` kept, `DO_NOT_TRACK=1`; the output's `left_out` line names the
  six, sorted.
- `test_a_held_agent_server_port_is_refused_and_nothing_starts`: exit 20, `already_running`, no record.
- `test_a_held_ingress_port_is_refused_with_a_free_one_to_use`: exit 21; the suggested port binds.
- `test_a_held_automation_port_moves_to_a_free_one`: the record's `OH_CANVAS_SAFE_AUTOMATION_PORT` is set, free,
  and not the default.
- `test_a_missing_or_old_requirement_is_named_and_nothing_starts` (parametrized: uv 0.8.16; no uv; no uvx; no git):
  exit 22, the sentence, no record.
- `test_a_failed_setup_ends_in_one_line` (parametrized: before-start exit 10 → 10; after-ready exit 12 → 12;
  timeout → 24; exit 1 → 24): the line, the code, no launcher text after it.
- `test_an_agent_server_that_never_answers_stops_everything_and_exits_24`.
- `test_once_ready_it_says_where_and_ctrl_c_exits_0`: `running(url)` under `--no-open`; SIGINT; exit 0.
- `test_unknown_options_and_bad_ports_are_refused`: exit 2.
- `test_the_browser_opens_only_where_a_session_can_show_it`: `opener` over macOS, Linux with and without a
  display, and SSH.

### 7.3 The build, `dr-app`, the README

- `tests/desktop/test_build.py`:
  - `test_the_runtime_closure_is_what_sirv_and_httpxy_resolve_to`: a lock with a nested `node_modules`.
  - `test_the_web_package_bundles_exactly_its_closure`.
  - `test_a_fork_that_changed_its_runtime_packages_or_electrons_call_is_refused` (fixture files).
  - `test_a_web_tarball_is_refused_for_each_thing_it_must_not_carry` (crafted tarballs, one per §5.4 `why`).
  - `test_targets_combine_and_only_desktop_targets_check_the_machine`.
  - `test_the_web_tarballs_defaults_are_what_patch_defaults_writes`: compares with `patch_defaults(...)`'s output,
    never with literals, so the UX round's new key needs no edit here (§8).
- `tests/app/test_runtime.py` (W10; stub `uv` and `git`, as today):
  - `test_an_update_keeps_the_runtime_current_pointed_at`: install A, then B: `runtime/A` and `runtime/B`,
    `current` → B.
  - `test_the_next_start_that_installs_nothing_removes_the_previous_runtime`: then a cheap before-start:
    only B.
  - `test_a_second_update_removes_the_runtime_before_the_previous`: A, B, C: B and C.
  - `test_a_running_process_keeps_its_runtime_through_an_update`: a process started from `runtime/A/bin/python`
    (the stub's) imports a module of A's after B is installed.
  - `test_a_new_commit_reinstalls` (today's) stops asserting that A is gone.
- `tests/app/test_texts.py`: §5.3's four.
- `tests/desktop/test_readme.py`:
  - `test_the_browser_command_is_dr_webs_at_a_commit_or_the_checkout_form`: exactly one `command_for(<40 hex>)`
    line, or (before the first release) none and the `--tarball` form.
  - `test_the_browser_section_names_its_flags_ports_cache_and_uv`.
  - `test_the_browser_sections_links_to_other_headings_resolve` (the UX round may rename "The first launch").
  - `test_the_data_table_names_the_browser_cache` (`web/`).
  - `test_the_readmes_browser_command_is_the_newest_releases` (`crossrepo`): the commit of the newest `v*` tag
    (`git tag -l`, `git rev-list -n 1`); none before the first tag.

### 7.4 E13 (`tests/desktop/test_e13.py`, marker `web`, `cross-repo.yml` `web-e2e`)

One first start shared by the module, from a fresh HOME (`fresh_home`), in a new session (`start_new_session`) so a
test can signal the group as a terminal does. The command is `command_for(<head commit>) --tarball
dist/deep-reasoning-web-<version>.tgz --no-open` under `user_environment(home)` plus, as junk: `PYTHONPATH=/nonexistent/
e13`, `VIRTUAL_ENV=/nonexistent/e13-venv`, `OH_AGENT_SERVER_GIT_REF=main`, `VITE_POSTHOG_API_KEY=phc_e13`; and on
`PATH` first a folder whose `node`, `npm` and `npx` exit 97, so anything that reaches for a system Node fails. Its
output goes to `web.log`. Playwright launches its own browsers. Claims and their falsifiers, in run order:

1. `test_the_first_start_sets_up_as_the_app_does`: before-start has `texts.home_local(<data>)` and a line starting
   `installed in `; after-ready has `texts.PROFILE_CREATED` and `texts.app_ready(<App version>, "installed")`;
   `/server_info`'s `app_backend_ingress_url` is `http://127.0.0.1:18000`; `left_out` names the four junk
   variables. *Falsified by* a missing line or another ingress. Never `texts.safety` or `NO_MODEL_KEY` (§8).
2. `test_the_stack_runs_the_pinned_agent_server_on_the_wheels_node_with_nothing_of_the_terminal`: the
   agent-server's command line holds the SDK pin's commit and no `@main`; every Node process of the stack runs
   `web/node-22.12.0/nodejs_wheel/bin/node` (`/proc/<pid>/exe`); no process of the stack has `PYTHONPATH`,
   `VIRTUAL_ENV`, `VITE_POSTHOG_API_KEY` or `phc_e13` in its environment; the agent-server's and the automation
   backend's have `DO_NOT_TRACK=1`. *Falsified by* any of them, or a 97 anywhere in the log.
3. `test_every_socket_the_stack_listens_on_is_loopback`: the stack is the command's descendants by parent pid
   (services lead their own groups, `dev-process-utils.mjs:38`, but stay children); their listening sockets
   (`/proc/<pid>/fd` → `/proc/net/tcp`, `tcp6`) are all on 127.0.0.1. *Falsified by* `0.0.0.0`, `::` or any other.
4. `test_a_conversation_answers_and_the_key_stays_out` (Chromium): the storage flag set, the home screen,
   `point_the_library_at` and `start_conversation` (shared, §7.6); FakeOpenAI's answer on the page; no consent form;
   the key, the session key and the secret key absent from the worker's environment and the run log, as E12
   checks. *Falsified by* no answer, a consent form, or a key found.
5. `test_the_library_panel_works_through_the_bridge[chromium|firefox|webkit]`: the session `POST` with credentials
   from the page, the frame on `…/ui/?tab=namespaces&cap=5`, `library_frame` (shared, it clears the notice while
   there is one), `dr-node-<namespace>` visible; in Chromium also the cookie's `partitionKey.topLevelSite` is
   `http://localhost` (CDP, as E12). Predicted: Chromium and Firefox pass (the spec's reproduction), WebKit
   unknown. Chromium failing fails the task; a Firefox or WebKit failure becomes `xfail(strict=True)` naming the
   browser, and the README names only the passing ones (Q4 (a)).
6. `test_a_second_start_is_refused_and_changes_nothing`: snapshot `setup.json`'s bytes, `runtime/`'s names and
   `current`'s target, `bin/`, `canvas-app/`, and `canvas/`'s `settings.json`, `secrets.json` and
   `agent-profiles/`; the same command again exits 20 within 10 s with `already_running(18000)`, printing no `[setup`
   or `[agent-server]` line; the snapshot is unchanged. *Falsified by* any change. (The rest of `canvas/` is the
   running agent-server's to write.)
7. `test_ctrl_c_stops_everything_within_10_s`: SIGINT to the group; the command exits 0 within 10 s; 8000, 3001,
   18000 and 18001 bind; no process names the HOME. *Falsified by* a survivor.
8. `test_a_restart_offline_installs_nothing_and_serves_the_page_within_30_s`: inside `unshare --map-root-user -n`
   with loopback up (E12's), a small script starts the command, polls `http://127.0.0.1:8000/` until 200, prints
   `served`, and sends SIGINT. `served` within 30 s, no `installing` and no `Fetching` in the log, exit 0. Run
   right after claim 7, so uv's index answers are fresh. *Falsified by* a failure or a slower start.
9. `test_an_offline_restart_once_uvs_index_answers_have_expired` (F4): the same, with the HOME's
   `~/.cache/uv/simple-v*` removed first (as if expired: uv then needs the index either way). Marked
   `xfail(strict=True, reason="the launcher's uvx asks PyPI once its answers expire: P1")`, since F4 holds; when
   P1 lands it passes, the strict mark fails, and the mark goes.

Reported, not asserted (in the job's summary, `-rA` output): the cold first start's duration and the tarball's size.

### 7.5 Coexistence (`tests/desktop/test_coexistence.py`, marker `desktop`, `desktop-e2e` after E12)

With the `.deb` installed and the tarball built in the same job, so both carry the same setup command:

- `test_the_app_will_not_start_beside_the_browser_and_writes_nothing`: the browser command's first start, ready;
  §7.4's snapshot; the app launched with the same HOME reports its start failed (`STARTUP_FAILED`) naming 18000;
  the snapshot is unchanged; the app stopped, then the browser.
- `test_the_browser_will_not_start_beside_the_app_and_writes_nothing`: the app launched (it installs nothing:
  `installing deep-reasoning` absent), ready; the snapshot; the browser command exits 20 with `already_running`;
  unchanged; the app stopped.

### 7.6 Smokes, and what moves into `tests/desktop/app.py`

`tests/desktop/test_web_smoke.py` (marker `web`): `test_the_first_start_gets_the_library_backend_ready_and_ctrl_c_
leaves_nothing` (the command with `DR_WEB_TARBALL` when set, else downloading the release at `DR_WEB_COMMIT`; wait
for `[setup after-ready] Done in` and the backend `ready`; SIGINT; nothing named the HOME left, by `ps -axo
pid,command` on macOS); and, on macOS, `test_the_python_uvx_picks_reaches_githubs_release_downloads` (`uvx --from
<the command's source> python -I -c` calling `dr_web.cache.download` on the SDK fork's `dr-2` client tarball, the
one the Canvas pin's `package.json` names).

Into `tests/desktop/app.py`, from E12, so E12 and E13 share one copy each: `setup_lines`, `point_the_library_at`,
`example`, `run_ids`, `worker_environ`, `start_conversation`, `answer`, and the frame flow of
`test_d3s_frame_works_through_the_bridge_in_electrons_chromium` as `library_frame(page, session_key)`. New there:
`launch_web(home, log, *args, env=…) -> LaunchedApp` (a `LaunchedApp` whose failure marker is `✗ ` instead of
`STARTUP_FAILED`: a field with that default), `descendants(pid)`, `listening_sockets(pids)`, `snapshot(data)`,
`mark_onboarded(context)`.

---

## 8 · The UX round (TASK-65): seams and merge order

Its Gate A answers (2026-10-19) that touch this task: Q1 (a), no onboarding in a locked build, and `NO_MODEL_KEY`
leaves the startup log; Q2 (a), the OpenHands agent's Settings pages hidden by the same `agent.lockedProfile`;
Q3 (b), a Spend cap field in the Library panel, with setup no longer overwriting a user's cap; Q4 (a), the README's
safety section kept as reference. One seam each:

| Touch point | TASK-48's side | What the UX round does there | If the UX round lands first | If TASK-48 lands first |
|---|---|---|---|---|
| `patch_defaults` | no edit: `package_web` uses `prepare()`'s defaults, and the tests compare with the function's output | writes `agent.lockedProfile`; check 5 adds the key | nothing to do | nothing to do: the browser gets the lock with the next build |
| `dr_app.texts` | §5.3's four sentences only; the command prints no key reminder | removes `safety` and `NO_MODEL_KEY`, renames prose (TASK-44) | rebase §5.3 onto TASK-44's prose rule | TASK-44's allow-list test reads `dr_web.texts` and `web.mjs`'s sentences too; ours already say Deep Reasoning |
| The README | one new section that links to "The first launch" and says nothing of keys or the cap | rewrites the first-launch steps and the safety section | the link test (§7.3) catches a renamed heading | the UX round keeps the heading or updates the link |
| E12 / E13 | E12's helpers move to `tests/desktop/app.py`; E13 asserts setup through texts functions only, skips onboarding by its flag, and clears the notice only inside `library_frame` | E12's onboarding steps, the notice, the costs default | E13 is written against no onboarding and no notice; `library_frame` needs no notice branch | the UX round edits `library_frame` (drop the notice) and E12's onboarding test, not E13 |
| The Canvas pin `dr-4` | W13's checks run on every web build | bumps both pins | W13 re-runs on `dr-4`; a changed Electron call is fixed in `web.mjs` in the same PR | the pin bump's PR runs `web-e2e` too (`cross-repo.yml` on `desktop/**`) |

**Merge order:** independent; whichever is second rebases. TASK-48 needs no fork tag, so it is likely first. The
second runs both `desktop-e2e` and `web-e2e` before its pins move. Nothing of the UX round's may live in
`electron/main.mjs` or `desktop/electron-builder.dr.mjs` (spec §5): the browser would miss it. The cap's how-to is
the panel's field; this design mentions no other.

---

## 9 · What this relies on

| Id | Fact | Where | Checked by |
|---|---|---|---|
| L1 | `main()` takes Electron's options and `setup` from `defaults.json`; reads `process.argv` (`parseArgs`, `:178`, unknown flags ignored, `--port` honoured) and `process.env` at its call | `dev-with-automation.mjs:1790–2077` | W13, §7.2, E13 |
| L2 | The port check precedes setup (`:478` before `:1969`); nothing is written before it but by `logger.mjs`, which writes only with `winston`, absent from the tarball as from the app | `:478, 1969`; `logger.mjs` | E13 claim 6, §7.5 |
| L3 | `SetupCommandError` carries `name`, `phase`, `reason`, `exitCode`, `signal` | `:1263–1282` | §7.2 |
| L4 | `shutdown()` on SIGINT, SIGTERM, SIGHUP stops every service, then `process.exit(0)`; idempotent | `:1460–1476` | E13 claim 7 |
| L5 | Services lead their own process groups, children of the launcher | `dev-process-utils.mjs:34–40` | E13 claims 3, 7 |
| L6 | The static server writes the session key into the page on loopback | `static-server.mjs:381` | E13 claim 4 (through the page working) |
| L7 | The bridge's cookie is `Secure; HttpOnly; SameSite=None; Partitioned`, refused off a secure context; loopback counts | SDK `canvas_extensions/bridge.py:385–413` | E13 claim 5 |
| L8 | Every variable the fork's scripts read (grep of `scripts/*.mjs` at `dr-3`): `AGENT_CANVAS_DISABLE_TELEMETRY`, `AUTOMATION_*`, `DO_NOT_TRACK`, `INGRESS_*`, `LOCAL_BACKEND_API_KEY`, `OH_*` (26 names), `OPENHANDS_REMOTE_WS_READY_REQUIRED`, `PORT`, `SESSION_API_KEY`, `TMUX_TMPDIR`, `VITE_*`, and the build-only `ELECTRON_ARCH`, `GITHUB_TOKEN`, `NODE_VERSION`, `UV_VERSION`, `EXPECTED_SDK_VERSION` | — | W8 |
| U1 | uv: a tag needs the remote each run; a commit does not (F1) | measured | E13 claim 8 |
| U2 | uv: a PyPI requirement needs the index once its answer expires; a package with none does not (F2) | measured | E13 claims 8, 9 |
| U3 | uv sets `UV` and prepends its tool environment's `bin` to the child's `PATH` | measured, 0.8.17 | §7.1 |
| U4 | uv forwards SIGTERM to the child; a group SIGINT reaches the child once; SIGHUP twice | measured, 0.8.17 | E13 claim 7 |
| U5 | `uv pip install --target --require-hashes` installs the wheel into a plain folder | measured, 0.8.17 | §7.1 (stubbed), E13 |
| U6 | The launcher's own agent-server command at the SDK pin restarts offline at once, fails 640 s later, and runs with `UV_OFFLINE=1` (F4) | measured, 0.8.17 | E13 claim 9 |
| N1 | Node 22.12.0 honours `process.exitCode` set in an `exit` listener after `process.exit(0)` | measured | §7.2 |

**Proposed task P1 (Canvas fork, for the Conductor; F4 holds):** the launcher's `uvx` starts of the agent-server
and the automation backend retry once with `--offline` when the first attempt fails for want of the network, or try
`--offline` first and fall back. A flag on uvx's own command line reaches neither server's environment. It fixes
the app's offline relaunch and the browser's alike; E13 claim 9 and E12 then pin it.

---

## 10 · Size

| Part | Lines (production + tests) |
|---|---|
| `dr-web` (pyproject, four modules) | ≈ 250 + 140 |
| `desktop/web.mjs` | ≈ 200 + 170 (stub launcher included) |
| `desktop/build.py` (web target, split, checks) | ≈ 130 + 90 |
| `dr_app` (W10, four sentences) | ≈ 25 + 50 |
| E13, coexistence, smokes, `app.py` (net of what moves from E12) | ≈ 0 + 420 |
| `test_readme.py`, README | ≈ 60 + 50 |
| Workflows, `pyproject.toml` | ≈ 100 + 0 |
| **Total** | **≈ 765 + 920 ≈ 1.7k gross, ≈ 1.5k net of the moved E12 helpers; about 5 h at Gate C** |

Against the spec's ≈ 0.9k: the Python door is ≈ 0.4k, not ≈ 0.15k (Node through uv, TLS, verification, its
tests); `web.mjs` is tested black-box against a stub launcher; E13 runs three browsers and an expired-cache restart;
the coexistence test and two smokes are new; the build gains W13's checks.

---

## 11 · Open items, and what I was unsure about

1. **V1 needs Michael's word** (the commit in the command). Until he answers, nothing else in this design waits on
   it except `command_for`, W14 and the README.
2. **F4's scope.** D5's README sentence about offline relaunches is wrong today for the app as well (measured with
   the agent-server's own command), and P1 is the fix. The Conductor decides whether that sentence changes in this
   task (one line in D5's section) or with P1. A stale-cache answer that uv would accept offline without
   `--offline` (`stale-if-error`) is PyPI's to send, and it sends none.
3. **The mixed run after a race (W10).** A stack whose window another version's install fell into runs that
   version's `dr-acp` and Library backend under its own Canvas until restarted. Nothing is deleted, but an ACP or
   Library schema change between the two versions would show there first. Closing it needs a lock both launchers
   hold for the whole run, which is a fork change (the spec's null result for claim 6).
4. **Reusing a kept runtime.** With W10, switching between two versions could relink a kept `runtime/<commit>`
   instead of reinstalling it (no network, seconds). It would change the spec's "each start of the other
   reinstalls the runtime once"; not done.
5. **The licence of `web.mjs`.** deep-reasoning has no LICENSE file; the tarball carries the fork's MIT text for the
   fork's files. Michael decides whether ours is MIT too; `package.json` says `SEE LICENSE IN LICENSE` until then.
6. **Python's TLS on a Mac without certificates** (W4) is reasoned, not measured here: the fallback to
   `/etc/ssl/cert.pem` covers a python.org interpreter; V7's macOS check measures what `uvx` actually picks.
7. **WebKit** (claim 5): unknown until E13 runs, as the spec says; Q4 (a) settles what the README then says.
8. **The Node wheel is two years old** (22.12.0, 2024-12-06), the app's own. Moving both together is a pin bump
   in the fork (`download-node.mjs:75`) and here (`NODE_VERSION`, the hashes, the dev pin); W13 could check the
   fork's against ours, and does not, since E13 runs the launcher on ours either way.
</content>
</invoke>
