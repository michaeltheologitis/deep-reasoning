# D5 · Desktop app: build, install and launch — design

**TASK-10** · System Designer · task branch `v1-desktop` in
[deep-reasoning](https://github.com/michaeltheologitis/deep-reasoning), cut from `main` (this file is written on
`design/d5`) · against the approved spec [TASK-1](https://app.notion.com/p/3ed62fb22237814ab425c81b3844f012) (D5 in
full, §2, C3, §4's E10, E12 and testing layers, the dated notes at its end through "Scope additions approved,
2026-10-03").

**Pinned against (v2): merged.**
- **deep-reasoning `main` at `1f9fe52`**: D1 (#1–#8), the interim stop-test fix (#10), D2 (#11–#18) and D3
  (#19–#26). Every deep-reasoning `file:line` below is from it. Their documents: D1's design v5 `a2632a2` and
  as-built `f7a91f3` (`v1-dr-acp`); D2's design v3 `0f16c67` (`v1-library-store`) and as-built r2 `9ccacd4`
  (`as-built/d2-r2`); D3's design v9 `acde27b` (`v1-decompositions-panel`) and as-built r4 `e60ac65`
  (`as-built/d3-r2`).
- **Canvas fork `deep-reasoning` at `7c12afb`**: upstream `1ff45c2`, the ASE commit, the fork-only
  `launcher-live.yml` (`ba4d883`) and C3's stack (#5–#11). Every Canvas `file:line` below is from it. C3's design
  v3 `873aa92` on `design/c3` (its §4 is D5's contract) and as-built r2 `8c8b8c6`.
- **SDK fork `deep-reasoning` at `34c540c`**: upstream `53a4bc5`, the ASE and fork-CI commits, S2 (#3–#9), a test
  fix (#17), S1 (#10–#16) and the fork-only `dr-release.yml` (#18). Every SDK `file:line` below is from it. S1's
  design v2.3 `4725ccc` and as-built r4 `18da6e1` (`design/s1`); S2's design v2.5 and as-built r5 (`design/s2`,
  `48e6baa`).
- deep_reasoner_beta `d7334ae` · uv 0.8.17 for v1's measurements, 0.12.23 as the build pins it (§4.2.1).

**Expected (not merged; the skeleton's pins and D5's final part wait on these):**
- **`dr-2`**, the SDK fork's tag, which Michael pushes at `34c540c`; `dr-release.yml` then publishes the TypeScript
  client tarball as release `dr-2`. The existing `dr-1` (`cef3b24`) was cut from `dr/integration` and is not on
  `deep-reasoning`.
- **The redone wiring** (§8.6) on the Canvas fork's `deep-reasoning`, in place of `wiring/dr-1` (`9881d24`, built on
  C3's pre-refactor head `22272d9` and pinning `dr-1`), and after it the Canvas fork's first tag.
- **C1**, Canvas fork PR #4 (`feat/acp-subagent-sessions`, `4db661f`, being refactored; design v3 `8772b90`,
  as-built `d16d3df`).
- **C2**, Canvas fork PR #3 (`feat/agent-surfaces`, `a1ec3d1`, ready to split; design v2 `6e489ea`, as-built r2
  `fbf4230`).
- **D4**, `v1-custom-tools` (`461c3b5`; design v5 `60f1d00`), being split onto `main`.

**Revisions** (newest first; each line says which sentences to stop trusting):
- 2026-10-04 · v2 · brought up to date with what merged since v1's pins, so an Implementer can build the skeleton
  now; the changes, each with its source, are listed next. Stop trusting: v1's pins; §1.2 (rewritten: the Library
  App, E5's bridge replay and the macOS smoke join the skeleton, and it has a build order); decision M and every
  `self-hosted-v1` (now `main`); decision N's "or setup's fallback" and all of §4.9's fallback
  (`ensure_ingress_config`, before-start step 7, its test, its size); §4.5.1 step 3's 422 fallback,
  `SUBAGENTS_UNSUPPORTED` and `desired_profile`'s `subagents`; `AGENT_SERVER_SECRETS` (§4.7.2, §5.7); §6's `{…}`
  templates (a sentence with fields is now a function); §7.4's YAML (the file is on `main`, and has run); §7.5's
  probe App and `unshare -rn`; §8.2, §8.3 and §8.5 as asks (each is met); §9's line numbers at `02b7ac7` and
  `91430aa`, and its row A6; §10; §11 items 1, 2, 8 and 11. Added: decisions O and P; pin check 8 (§4.2.2);
  `run_logged` (§5.2); §8.7 (D4); §11 items 13 to 18.
- 2026-10-02 · v1 · first full-depth version. Folded in before it: Michael's rulings that the SDK fork is pinned
  by full commit (the tag named in a comment) and that D2's departures stand (a Library on a network filesystem
  is refused; the starter Library is gpt-6-luna on OpenAI); S1's opt-in `acp_subagents`; GitHub's rule that an
  on-demand workflow's file must exist on the default branch and a scheduled one runs only from it; C2's finding
  (C2 `72aa49f` §11) that App backends answer only on a separately configured ingress origin, which no launcher
  sets (§4.9).

**Changed since v1** (v2; each with its source and the sections it touches):

1. **C3 is merged, and its v3 is the contract** (Canvas `7c12afb`; C3 v3 §4, §4.4, §4.6, B9's v3 note). The keys,
   the phases and their environment are as v1 read them. New: a phase ends when the command's stdout and stderr
   close, not when it exits; at a timeout or a quit the command's process group is signalled even after the
   command itself has exited, SIGKILL follows 3 s after SIGTERM, and the launcher gives up 1 s after that; a quit
   ends the launcher in about 4 s, a timeout stops the launch within the limit plus about 4 s; a child that left the
   group (`setsid`), or whose output is redirected, can survive. `SHARED_DEFAULTS` is now parsed once and passed in
   (D-13), which changes nothing for a build that edits the file; the `[defaults]` line lists its names sorted (B5).
   → decision P, §4.3, §4.4.3, §6's log, §7.5 step 6, §9 C3, §11 item 14.
2. **C3 built the App-backend ingress default** (#5, B2, `scripts/dev-safe.mjs:883–884`; Michael's scope addition
   of 2026-10-03): every launcher gives the agent-server `OH_APP_BACKEND_PUBLIC_URL=http://127.0.0.1:<its port>`.
   D5 sets nothing, and §4.9's fallback and §8.5's ask are gone. → decision N, §1, §3 item 16, §4.4 step 7, §4.9,
   §5.5, §7.2, §8.5, §10.
3. **C3's live test proved the offline relaunch on the uv the build bundles**: uv 0.12.22 and 0.12.23, for
   upstream's commit and, through `wiring/dr-1`, for the SDK fork's `cef3b24` (runs 37171406704, 37148193696). The
   build pins `uv_version = "0.12.23"`. The network cut is `unshare --map-root-user -n`, then `ip link set lo up`,
   after an AppArmor sysctl on Ubuntu 24.04 (C3 B3, §7.5). → §4.2.1, §7.5 step 6, §9 U1, §11 item 15.
4. **S1 is merged, with the opt-in on the agent profile** (SDK #13: `profiles/agent_profile.py:292`,
   `resolver.py:305`, `seed.py:58`; S1 §5.1 guarantee 8): §8.2's ask is met, so setup always writes
   `acp_subagents: true` and the flat fallback goes. The scripted agent's `--transcript` mode is merged (#16, S1
   §5.1 guarantee 9), so E5's bridge replay joins the skeleton. → §1.2, §4.5.1, §5.4, §6, §7.2, §7.5, §8.2.
5. **S2 is merged** (SDK #3–#9): conversation header panels in the manifest (#4), `darwin-*` App backends and
   loopback never proxied (#3). The Library App's install and the macOS launch smoke no longer wait on it. → §1.2,
   §4.6, §7.6.
6. **The SDK fork's release path** (#18, `.github/workflows/dr-release.yml`, fork-only): a pushed `dr-N` tag runs
   the client's tests, packs `clients/typescript` and creates prerelease `dr-N` with
   `openhands-typescript-client-<version>.tgz` (1.50.1 at `34c540c`), once; the asset is never replaced, since the
   Canvas fork's lockfile pins its hash. → the header, §4.2.1, §4.2.2 check 8, §8.6, §9 T1.
7. **D1 is merged** (D1 as-built §4.6): `ModelRoute`, `RouteGrant`, `worker_env` and `PriceTable` as v1 read them;
   `ALWAYS_REMOVED` already holds `OPENHANDS_AUTOMATION_API_KEY` (D1 B2), as one of four glob patterns; `Options`
   has D1's five fields; `FakeOpenAI` is `deep_reasoning.acp.testing.fake_model`. The tool-client half of §8.1 is
   still to build. D1's EXP-27: deep_reasoner's `claude_code.child_env` drops every `CLAUDE_CODE*` variable. → §2.1,
   §2.2, §4.7.2, §5.7, §7.1, §8.1, §11 item 3.
8. **D2 is merged** (#11–#18): `dr-acp` without `--config` reads the Library, `dr-library serve --port P --home DIR`,
   `export DIR --home DIR` and its sentence, `/health` and `NETWORK_FILESYSTEMS` are as v1 relied on. New to D5:
   D2's `Host` guard on every platform (D2 as-built §2 #1), which E12 is the first to run through the bridge. →
   §2.2, §9 D2, §11 item 11.
9. **D3 is merged** (#19–#26; D3 §8.4): the App package `deep_reasoning.canvas_app` ships in the wheel (a manifest
   without a `backend` block, `dist/index.js`, `panel.svg`, and `ui/`, which `dr-library serve` serves at `/ui/`).
   D3 accepted D5's four proposals and asks seven things: D5 stages three files, not `ui/`; the page restarts a dead
   backend by starting its prepared revision; the notice is `SAFETY`, or `SAFETY_NO_CAP` under `--no-key-proxy`;
   and D3's equality test assumed `SAFETY.format(cap=7)` (D3 B19). → decisions G and O, §1.2, §2.3, §4.6, §5.5, §6,
   §7.2, §7.5 step 5 (D3's frame replaces the probe App), §8.3.
10. **deep-reasoning integrates on `main`**: D1 to D3 merged there, and `fork-live.yml` is on `main` in full
    (`633a00d`) and has run (37147706623 on `ci/fork-live`: S1 2 of 2, S2 8 of 8, without the proxy). → decision M,
    §1.3, §3 item 14, §7.4, §7.5, §8.6, §11 item 8.
11. **C1's contract, expected** (C1 v3 §4.12, §6.4, §9.4, A.9; its branch since Gate B): `OH_ACP_REPLAY_TRANSCRIPTS`
    as D5 named it, the replay spec's path, SUB-011's test ids, `expandAllSubagents` and `readRenderedSubagentTree`,
    and a frontend-only "Show sub-agent costs" setting, off by default (`show-subagent-costs-switch` on
    `/settings/app`; `dfde47e`, `4db661f`). → §7.5's final flow, §8.4, §9.
12. **C2's contract, expected** (C2 v2 §3.2 B15): the CX-006 and ASC-005 test ids; App frames read the ingress from
    `/server_info`'s `app_backend_ingress_url`. → §7.5, §8.4.
13. **D4's asks, expected** (D4 v5 §5, §10.6, §11.4): E10 again with its `echo_server.py` bound; one exception to
    §2.1's first row; the profile's `mcp_server_refs: null`; an E12 step and a cross-repo forwarding test. → §2.1,
    §2.2, §7.1, §7.5, §8.7.
14. **Found while re-reading**: the proxy imports `httpx`, which today arrives only through deep_reasoner, so it
    becomes a direct dependency (§4.1); a pinned commit must be on its fork's `deep-reasoning`, which `dr-1` is not
    (§4.2.2 check 8); the bridge strips `ANTHROPIC_API_KEY` and `ANTHROPIC_BASE_URL` from `dr-acp`'s environment
    whenever `CLAUDE_CODE_OAUTH_TOKEN` is a secret (§2.2, §11 item 3); a forced App reinstall is refused while any
    App's backend runs (§4.6); E12 is Python, so it evaluates C1's two DOM reads rather than importing them (§7.5).

**Where this file lives, and why nothing trips over it.** `docs/design/d5-desktop-app.md`. The `design/d5`
branch holds only documents (no `pyproject.toml`, no test runner, no package). On `v1-desktop`, cut from `main`,
which carries D1's `pyproject.toml`, pytest collects `tests/` only, the wheel is built from `src/deep_reasoning`
(and the new `packages/dr-app` from its own `src/`), the sdist excludes `docs/`, and ruff excludes `docs` (D1
§8.5). No design document goes into either fork, or onto `main`. The PR split leaves it behind.

**Reading guide.** Gate B: §1 (what D5 is, its decisions, the skeleton, its build order and the final part), §2
(what the app protects and what it does not) and §3 (departures from the spec): about 20 minutes. The Implementer:
§1.2 first, then everything; §5 is the signature index, §6 every user-visible sentence, §7 the tests and workflows.
Whoever redoes the wiring: §8.6. C1's and C2's authors: §8.4. D3's: §8.3. D4's: §8.7. D1's next revision: §8.1.
The Conductor: §1.2, §8 and §11.

---

## 1 · What D5 is

v1 is a desktop app (Q7 (b)). D5 turns the pinned forks and this repo into one download per OS, and makes the
app's own launcher install the rest, as the user, on first launch. It is four things:

1. **The build** (`desktop/`). It checks that the pins belong together, checks out the Canvas fork at its pinned
   commit, writes D5's values into that checkout's `config/defaults.json` (the state directory, the setup
   command, telemetry off), builds the frontend, and packages it with electron-builder under our product name.
   Output: one universal `.dmg`, an `.AppImage` and a `.deb`, unsigned as upstream's are. Neither fork gets a
   commit from D5: every change is made to a build checkout.
2. **`dr-app`** (`packages/dr-app/`), the setup command C3's launcher runs as the user on every launch, before
   the stack starts and again once the agent-server answers. It installs deep-reasoning (and through it
   deep_reasoner) with the user's own git credentials into a private runtime, picks where the user's data lives,
   registers the `deep_reasoner` agent profile, and installs, approves and starts the Library App (D3's, which
   v1 left to the final part; v2: D3 and S2 are merged, so it is the skeleton's). On a launch where nothing changed
   it does almost nothing. It also offers `dr-app export` and `dr-app home`.
3. **The key proxy** (`src/deep_reasoning/acp/proxy.py`), inside `dr-acp`'s front process, implementing D1's
   `ModelRoute`. The worker gets a token instead of each provider key; the proxy swaps the key in, forwards only
   model calls, and refuses a call once the conversation's spend cap is reached.
4. **The cross-repo CI** (`.github/workflows/`): the shared live workflow for S1's and S2's live tiers with
   `dr-acp` behind the bridge (*v2:* built and on `main`, §7.4); E12 on the real Linux app, the golden replays into
   the pinned agent-server (E5) and Canvas (E6), and the pin checks, nightly and on every pin bump; the per-OS
   release build.

A launch of the installed app, end to end:

```text
Deep Reasoning.app  (Canvas fork's Electron shell at its pinned commit; D5's defaults.json; product name)
  electron/main.mjs → dev-with-automation.mjs main()                                        (C3 §3.2)
    1 defaults.json fills: OH_AGENT_SERVER_GIT_REPO / _REF  (the wiring commit: the SDK fork's commit)
                           OH_CANVAS_SAFE_STATE_DIR = ~/.deep-reasoning/canvas/agent-canvas  (D5), key files in it
    2 setup before-start:  sh bootstrap.sh → uvx --from git+…/deep-reasoning@<commit>#subdirectory=packages/dr-app
                             dr-app setup:  data home · runtime ~/.deep-reasoning/runtime/current (from the lock)
                           the phase ends when the command's output closes (C3 v3 §4.2; decision P)
    3 agent-server         uvx, SDK fork at its commit; persistence root ~/.deep-reasoning/canvas;
                           App-backend ingress OH_APP_BACKEND_PUBLIC_URL = http://127.0.0.1:18000   (C3 B2, §4.9)
    4 setup after-ready:   the same command, with AGENT_SERVER_URL and SESSION_API_KEY
                             agent profile deep_reasoner · Library App dr-library installed, approved, started
    5 automation, static frontend, ingress → window on http://localhost:8000
         the Library panel's frame: http://127.0.0.1:18000/app-backends/dr-library/ui/…  (a separate origin and site;
         its button and panel are C2's, final part)

  a conversation → the agent-server's ACP bridge → ~/.deep-reasoning/runtime/current/bin/dr-acp
                                                       --home <DR_HOME> --spend-cap-usd 5
     dr-acp front ── key proxy, 127.0.0.1:<port>, its own thread ──(real key)──▶ the provider
          │                         ▲
          └─ worker (D1) ───────────┘ model calls carry a token, never the key; the env holds no key
```

Where everything lives on the user's machine:

| Path | What | Written by |
|---|---|---|
| `~/.deep-reasoning/` | the app's root, mode 0700 | `dr-app` |
| `~/.deep-reasoning/canvas/` | the agent-server's persistence root (C3 §4.3): `settings.json`, `secrets.json`, `agent-profiles/`, `canvas-extensions/`, `automation/` | the agent-server, automation |
| `~/.deep-reasoning/canvas/agent-canvas/` | C3's state directory: conversations, workspaces, `secret-key.txt`, `api-key.txt` | the launcher, the agent-server |
| `~/.deep-reasoning/runtime/<commit>/`, `runtime/current` → it | the venv holding `dr-acp`, `dr-library`, `dr-app`, deep_reasoner's `dr` | `dr-app` |
| `~/.deep-reasoning/bin/` | `dr-app` and `dr`, linked to `runtime/current/bin/` | `dr-app` |
| `~/.deep-reasoning/canvas-app/<digest>/` | the Library App package staged for this machine: D3's manifest with D5's `backend` block, `dist/index.js`, `panel.svg`, the backend artifact | `dr-app` |
| `~/.deep-reasoning/setup.json`, `setup.lock` | what setup last did; a lock while it runs | `dr-app` |
| **DR_HOME**: `~/.deep-reasoning` itself, or `/var/tmp/deep-reasoning-<uid>` on a network home | D1's and D2's home: `library.sqlite`, `sessions/`, `runs/`, `prices.yaml`; D5's `spend/` | D1, D2, D5 |

The names never collide: D1's and D2's entries (`library.sqlite`, `sessions/`, `runs/`, `prices.yaml`) and
D5's (`canvas/`, `runtime/`, `bin/`, `canvas-app/`, `setup.json`, `setup.lock`, `spend/`) are disjoint, so
DR_HOME can be the root itself. A terminal `dr-acp` or `dr-library` with no `--home` uses `~/.deep-reasoning`
(D1's default), so on a local home the terminal and the app share one Library.

### 1.1 Decisions this design takes

The spec's seven decisions in §2 stand; these are the next layer down.

| # | Decision | Why | Rejected |
|---|---|---|---|
| A | **Every pin is a full commit; tags are recorded beside them for people.** `desktop/pins.toml` holds each fork's repository, commit and tag; the build records deep-reasoning's own commit (its `HEAD`) in the setup command. *(v2: and each pinned commit must be on its fork's `deep-reasoning` branch, §4.2.2 check 8.)* | Michael's ruling for the SDK fork; C3 §2.3 measured that uv reuses only a commit offline, and the same holds for D5's own `uvx` command (C3 §4.6). One rule for all three repos. *(v2: the spec pins each fork by a `dr-N` tag on its `deep-reasoning` branch, and the fork stacks merge there; `dr-1` was cut from `dr/integration`.)* | Tags in `defaults.json` (C3's tag-resolving variant, ≈170 lines; ruled out). |
| B | **The setup command is a ten-line `sh` bootstrap around `uvx` of a separate, standard-library-only package, `deep-reasoning-app`** (`packages/dr-app`), fetched by commit with `#subdirectory=`. | Whatever `uvx` installs must be fetched before anything of ours can speak. If the setup command were the main package, `uvx` would first fetch deep_reasoner and fail with uv's words, before any check could say "ask Dean for access". The small package needs nothing private but deep-reasoning itself, and the bootstrap explains a missing `git` or an unreadable deep-reasoning, the two failures that happen before `dr-app` exists. A commit-pinned `uvx` of a package with no dependencies starts from uv's cache, offline included (C3 §2.3). | `uvx --from git+…/deep-reasoning@<commit> dr-app setup` as C3 §4.6 sketches (the private fetch fails before our checks, so the spec's failure messages cannot be ours). A setup script bundled into the app's resources (it would need a path into the bundle, which differs per launch for an AppImage, and a file added inside the fork's `uv` resource directory). |
| C | **`dr-app` installs a runtime venv from a committed export of `uv.lock`** (`runtime.lock.txt`, exact versions, platform markers kept), on uv's managed Python 3.12, into `runtime/<commit>/`, then swaps the `runtime/current` link atomically. | Users run exactly the dependency set CI tested; a transitive release between our test and their first launch cannot break them. The link keeps every path that is written into a profile or an App stable across upgrades. A managed Python survives a system or Homebrew Python upgrade. | `uv tool install` (resolves afresh, ignoring the lock; writes into the user's global tool and `~/.local/bin` directories). The `uvx` environment itself (uv's cache can be pruned under it). |
| D | **One root, `~/.deep-reasoning`. The agent-server's persistence root is `~/.deep-reasoning/canvas`** (state directory `…/canvas/agent-canvas`). **DR_HOME is `~/.deep-reasoning`, or `/var/tmp/deep-reasoning-<uid>` when the home directory is on a network filesystem.** Every process is told the home with `--home`; DR_HOME is never set in any environment. | C3 §4.3: the state directory's parent holds everything the agent-server persists, so it must be ours, not `~/.openhands`. D2's ruling: the Library refuses a network filesystem, so setup picks local disk. deep_reasoner reads `DR_HOME` itself as the root of its Claude runs (`v2/claude_code.py:270`), so an exported DR_HOME would reach the worker with a second meaning. | `~/.openhands/deep-reasoning` (the spec's mock-up; shares settings, secrets, profiles and Apps with stock Agent Canvas, C3 §2.4). |
| E | **Setup is idempotent, and its cheap path is a JSON read, a few `stat`s and one exec of the runtime's Python**; it changes anything only when a pin, the data home or the App package changed, or something it installed is gone. | C3 §4.2: both phases run on every launch, and the command must be fast and offline-safe when nothing changed. Checking the installed thing (not only a record) repairs a deleted runtime or a removed managed Python. | A "first launch done" flag (misses a deleted install). |
| F | **Setup owns four fields of the `deep_reasoner` agent profile** (`agent_kind`, `acp_server`, `acp_command`, `acp_subagents`) **and the `--home` pair in its arguments; it activates the profile once, when it first creates it.** Everything else in the profile, the spend cap included, is the user's after creation. | The profile's command path is stable (`runtime/current`), so a launch rewrites nothing. A user who switches the default agent, or raises the cap in Canvas's profile editor, is not overruled on the next launch. | Rewriting the whole profile every launch. Making it the default every launch. |
| G | **The Library App is staged on the user's machine** (*v2:* skeleton, no longer final): three of D3's built files from the runtime (`canvas-extension.json`, `dist/index.js`, `panel.svg`; not `ui/`, which `dr-library serve` serves itself), plus a backend artifact D5 generates, a `.tar.gz` holding one `/bin/sh` launcher that `exec`s `runtime/current/bin/dr-library`. Setup installs it from that local path, enables it once, and approves (`prepare`) and starts its backend on every launch. A failure here warns and does not stop the launch. | The agent-server requires the backend's executable inside the unpacked artifact and gives it six environment variables (`manifest.py:217–255`, `backend.py:38–40, 395–412`); `dr-library` imports deep_reasoner, which nothing we publish may contain, so the artifact can only be built where deep_reasoner is installed. The launcher script is the same bytes on every launch and both architectures, so its checksum and the approval survive upgrades. Stock Canvas has no control that starts an App backend, and backends do not survive an agent-server restart, so setup starts it. Conversations work without the panel, so the panel's failure must not block them. *(v2: D3 accepted this, D3 §8.4; staging only the App's own files keeps a UI-only change from changing the digest, which would force a reinstall.)* | Shipping a frozen `dr-library` binary (it would contain deep_reasoner). Installing from a git URL (the backend artifact must be built per machine). Leaving the start to D3's panel (a backend is not ready until its first open, and every first open would wait on deep_reasoner's imports; *v2:* the panel, as built, restarts one that died by starting its prepared revision, never by approving one, D3 decision F). |
| H | **The key proxy runs in `dr-acp`'s front, on its own thread, as a Starlette app under uvicorn on 127.0.0.1.** Per run it mints one 256-bit token per provider key it holds, one route per configured upstream, and gives the worker the token under the key's own variable name; it scrubs the worker's environment of the key by name and by value, and of the agent-server's secrets. | The spec places it there (decision 7). Its own thread keeps a slow upstream from delaying ACP traffic, and uvicorn installs no signal handlers off the main thread (`uvicorn/server.py`, `capture_signals`), so D1's SIGTERM shutdown is untouched. Starlette and uvicorn are already dependencies (D2). Reusing the variable name means anything that reads the key, a user's own code in a cell included, gets a token that works only through the proxy. | LiteLLM (heavy for one user, spec §2). A hand-written HTTP/1.1 server on `asyncio` (chunked transfer and keep-alive by hand). |
| I | **The cap is enforced, not estimated afterwards:** the proxy forwards only metered model endpoints; it reserves an estimate of each call's cost before forwarding and settles the real one after; it refuses a model whose price is unknown unless the upstream is on loopback. The ledger is per conversation (root ACP session) and persisted. | A cap that a cell can step around through an unmetered endpoint (fine-tuning, batch, files), an unpriced model or twenty concurrent calls does not bound anything. A restarted `dr-acp` (the bridge restarts it after a slow Stop) must not reset the count. | Counting after the fact only (a `run_all` of 20 overshoots by 20 calls). Pricing unknown models at a fallback rate (a dearer model escapes the cap). |
| J | **The proxy is on by default in `dr-acp`** (`--no-key-proxy` turns it off); a client whose key `dr-acp` does not hold is left as configured. | Decision 7 says keys reach the worker only through the proxy. Keyless clients (a local vLLM, every one of D1's scripted tests) have nothing to protect, so D1's suite is unaffected. | Opt-in (a terminal `dr-acp` would leak by default). |
| K | **Telemetry is off in our builds**: the frontend is built with `VITE_DO_NOT_TRACK=1` and `telemetry.posthogApiKey` is emptied in the built `defaults.json`. | Canvas sends an install event to OpenHands' PostHog without consent (`src/services/telemetry.ts:7–12`, unchanged since v1's pin), and the agent-server and automation backends default to the same key (`scripts/dev-safe.mjs:752–790`, `buildAgentServerTelemetryEnv`; `dev-with-automation.mjs:1070–1084`, `buildAutomationTelemetryEnv`). A packaged app is started without our build's environment, so only build-time values reach it: the bundle's `VITE_DO_NOT_TRACK` and `defaults.json`'s empty key, which the launcher reads as its default. Our users did not agree to report to a third party. | Shipping upstream's default. |
| L | **Product identity comes from a wrapper electron-builder config in this repo** (`desktop/electron-builder.dr.mjs`) that imports the fork's and overrides the app id, product name, `extraMetadata` and artifact names. | No fork commit (the brief's rule); Electron's `userData` (the frontend's local storage) follows `extraMetadata.productName`, so it is separate from stock Agent Canvas (C3 §4.3). | A fork commit for our name. `-c.key=value` overrides on the command line (ambiguous beside `--config`). |
| M | **CI lives in this repo, and D5's workflows reach `main` with D5's PR stack, as D1's to D3's code did.** Until then `main` carries only what GitHub needs to start them: a copy of each on-demand workflow (`cross-repo.yml`, `desktop-release.yml`; `fork-live.yml` is there already, `633a00d`) and `nightly.yml`, a scheduled trigger that dispatches `cross-repo.yml` on `v1-desktop`, and on `main` once D5 has merged. | GitHub requires an on-demand workflow's file on the default branch and runs a scheduled workflow only from it. A dispatched run uses the file at the ref it is dispatched on. A run started by the workflow token through `workflow_dispatch` is allowed to start another workflow. *(v2: v1 sent the nightly run to `self-hosted-v1`, the spec's integration branch (§5); D1 to D3 merged into `main` (#1–#26), so `main` is where merged work and its workflows live.)* | The nightly job's full definition on `main` before D5 merges (it would drift from the branch it tests). |
| N | **The App-backend ingress is `http://127.0.0.1:<agent-server port>`, which C3's launcher sets as a generic default** (*v2:* built, C3 #5, B2, `scripts/dev-safe.mjs:883–884`; approved by Michael as a scope addition to C3 on 2026-10-03). D5 sets nothing; v1's fallback in setup is gone. | The bridge answers 503 until an ingress origin is configured, and requires it to be a different origin from Canvas's (`canvas_extensions/bridge.py:231–244, 304–314`). The window loads Canvas from `http://localhost:8000` (`electron/main.mjs:399`), and the launcher binds the agent-server to 127.0.0.1 (`dev-with-automation.mjs:1126–1132`), so the agent-server's own address is reachable, keeps its `Host`, and is another origin and another site: Canvas's own cookies never reach an App backend. What stays D5's: showing in Electron's own Chromium that the frame keeps the bridge's cookie (E12 step 5). | `http://localhost:18000` (another origin but the same site, so Canvas's `localhost` cookies would travel with every App request; and `localhost` may resolve to `::1` where the agent-server listens only on IPv4). A second ingress process (one more port and service for what the agent-server already serves). |
| O | *(v2)* **`dr_app.texts` follows D1's and D2's rule: a constant is a sentence without fields, a function returns a sentence with its fields** (`texts.safety(cap)`, §6). D3's equality test changes one line with it: `texts.safety("7")` for `texts.SAFETY.format(cap=7)`. | The Code Guide forbids `.format()`; `deep_reasoning.acp.texts` and `deep_reasoning.library.texts` already work this way; D3 said its test follows whatever D5 writes (D3 B19, §8.4 item 7). The test stops skipping as soon as `dr_app` is a dev dependency, so the line changes in the same commit. | A `str.format` template, which D3's test assumed. |
| P | *(v2)* **`dr-app` leaves nothing running and holds nothing open.** It starts no process in a session or group of its own, and no background process; it runs each subprocess (`uv`, `git`, the runtime's Python) with its output on a pipe of `dr-app`'s own, copies the lines into the startup log, and goes on at the subprocess's exit, not at the pipe's end. The Library backend is started by the agent-server (its child, its own log), never by `dr-app`. | C3 v3 §4.2: a phase ends only when the command's stdout and stderr close, so anything that keeps them (a credential helper that daemonizes, a stray grandchild) holds the phase, up to its 15 minutes, and then fails the launch. A quit signals the command's process group, so whatever `dr-app` started is stopped with it, unless it left the group. Every step is restartable (§4.4.3), so a quit or a timeout mid-install leaves nothing the next launch cannot repair. | Letting subprocesses inherit the launcher's output (any grandchild that keeps it holds the phase). `start_new_session` for the install (a quit could not stop it). |

### 1.2 The skeleton now, the final part after the rest

*(v2: rewritten.)* The task row says "skeleton first, final after the rest". Most of the rest has merged since v1, so
the skeleton is now everything that needs only merged code and the redone wiring, and the final part is only what
C1, C2 and D4 bring.

| Part | Skeleton (build now) | Final (waits on) |
|---|---|---|
| The build (§4.2) | all of it: pins and their checks, `build.py`, the wrapper config, the bootstrap, Linux and macOS packages | — |
| `dr-app setup`, before-start (§4.4) | all of it: the data home, the checks, the runtime install, the `bin/` links | — |
| `dr-app setup`, after-ready (§4.5) | the `deep_reasoner` profile with `acp_subagents: true` (S1, merged); the model-key hint; the Library App (§4.6; v1's final part: D3's package and S2's panels and macOS backends are merged) | — |
| The App-backend ingress (§4.9) | nothing to build (C3 B2); E12 shows the bridge's cookie in Electron's own Chromium with D3's frame (§7.5 step 5) | the panel in Canvas's header (**C2**) |
| The key proxy and spend cap (§4.7), E10's two tests (§7.1) | all of it, with the tool-client half of D1's seam (§8.1) | E10 again with **D4**'s `echo_server.py` bound in the worker (§8.7) |
| Export, `dr-app home` (§4.8) | all of it | — |
| The safety notice (§2.3) | the startup-log line at first install; the README; D3's frame shows it (merged), and E12 reads it in the real app | **D4**'s own sentence under it in the Tools tab |
| `fork-live.yml` (§7.4) | built and on `main`; dispatched again on `v1-desktop` once the proxy is in, with `sdk_ref` `dr-2` | — |
| `cross-repo.yml` (§7.5) | `pins`; `desktop-e2e`, E12's skeleton flow; `bridge-replay`, E5's second half (S1 merged) | `canvas-replay`, E6 (**C1**); E12's final steps: the nested tree and a Stop (**C1**); the namespace picker, the slash menu, Show decompositions, Create decomposition and the next conversation (**C2**); an MCP server (**D4**) |
| `desktop-release.yml` (§7.6) | the per-OS builds on demand, and the macOS launch smoke that waits for the Library backend (D3 and S2 merged) | the first release tag, once C1, C2 and D4 are in the pins |

**The skeleton's build order.** Steps 1 to 6 need only `main` at `1f9fe52` and the SDK fork at `34c540c`, so they
start now, in this order, each with its tests first. Step 7 is the first that waits, and only on what it must.

1. **D1's seam, its tool-client half** (§8.1), in D1's files: `RunSource.tool_clients`,
   `RouteGrant.tool_client_overrides`, `ModelRoute.grant(…, tool_upstreams=…)`, `Start.tool_client_overrides` and
   the worker's merge. The proxy's grant is written against it.
2. **The key proxy and spend cap** (§4.7, §5.7), `dr-acp`'s two options and `httpx` as a direct dependency, with
   `test_key_proxy.py` and E10's two tests (§7.1). Pure deep-reasoning.
3. **The `deep-reasoning-app` package** (§4.3 to §4.8, §5.1 to §5.6, §6): the workspace member and
   `runtime.lock.txt`, then layout and home, runtime, the agent-server client, the profile, the Library App, the CLI
   and texts, with §7.2's tests (stub `uv`, `uvx` and `git`; an in-test HTTP server answering like the
   agent-server). D3's one test line (decision O) changes in the commit that makes `dr_app` a dev dependency.
4. **`desktop/`** (§4.2, §5.8): `build.py` with every check behind injected readers, the bootstrap, the wrapper
   config, and `pins.toml` with `[sdk_fork]` filled (`34c540c`, tag `dr-2`) and `[canvas_fork]` a placeholder;
   §7.3's tests.
5. **Against the SDK fork's commit alone**, which needs no wiring (each test checks out `34c540c` and starts its
   agent-server directly): `test_canvas_app.py`'s `crossrepo` test (the staged artifact passes `prepare`, the
   backend answers `/health`) and E5's `bridge-replay` (§7.5), as `cross-repo.yml`'s first jobs.
6. **The files on `main`** (decision M): copies of `cross-repo.yml` and `desktop-release.yml`, and `nightly.yml`
   dispatching on `v1-desktop`; placed with Michael's yes, as `fork-live.yml` was.
7. **Waits on `dr-2`, the redone wiring (§8.6) and the Canvas fork's first tag**: fill `[canvas_fork]`;
   `build.py check` green (the `pins` job); the Linux packages; E12's skeleton flow (`desktop-e2e`);
   `desktop-release.yml` with its macOS smoke; `fork-live.yml` dispatched on `v1-desktop` with `sdk_ref` `dr-2`.

**The final part, in the order its pieces can land.** Each is a pin bump with the steps it enables, green in
`cross-repo.yml` before the pin moves (spec §2):
- **C1** merges into the Canvas fork's `deep-reasoning`, after merging the redone wiring, and the fork is tagged
  again: `canvas-replay` (E6) and E12's nested-tree step (§7.5, §8.4).
- **C2** likewise: E12's picker, slash-menu, header-panel and Create-decomposition steps (§7.5, §8.4).
- **D4** merges into `main`, and `v1-desktop` merges `main`: E10 with an MCP server bound, §2.1's exception, E12's
  MCP step and D4's forwarding test (§8.7).
- Then the first release tag (§7.6).

**What the skeleton needs from others** (v1's list, now settled): C3 merged with the ingress default (done,
`7c12afb`); D1, D2 and D3 merged (done, `1f9fe52`); S1 with the profile's opt-in (done, SDK #13); the SDK fork's
release step (done, #18). Still needed: `dr-2` pushed, so that its release carries the tarball; the redone wiring
merged into the Canvas fork's `deep-reasoning`; a Canvas tag at it. No pin runs a pre-S1 agent-server any more,
so v1's flat fallback is gone (§4.5.1).

### 1.3 What D5 owns, and its seams

- **Owns:** `desktop/` (pins, build, wrapper config, bootstrap); the `deep-reasoning-app` package and the
  `dr-app` command; `src/deep_reasoning/acp/proxy.py` and the two `dr-acp` options that use it; the workflows
  `fork-live.yml` (built), `cross-repo.yml`, `desktop-release.yml` and `nightly.yml`; E10, E12, and the
  cross-repo halves of E5 and E6; the README's install section.
- **Seam to C3** (C3 v3 §4): D5 writes `paths.stateDir` and `setup` into a build checkout's `defaults.json` and relies
  on §4 as v3 states it, the ingress default (B2) and the end of a phase (decision P) included. *(v2: v1's ask
  for the ingress default is built, §8.5.)*
- **Seam to D1** (§4.7, §8.1): `ProxyRoute` implements `ModelRoute`; D5 extends it additively so tool clients are
  routed too. *(v2: the name v1 asked for is already in `ALWAYS_REMOVED`.)*
- **Seam to D2**: `dr-library serve --port P --home DIR` (the backend's argv), `dr-library export DIR --home DIR`,
  `/health`, and D2's set of refused filesystems (mirrored, pinned by a test). No change to D2.
- **Seam to S1** (§8.2): the profile's `acp_subagents`; the scripted agent's `--transcript` mode for E5. Both merged.
- **Seam to D3** (§8.3): the three files D5 stages and the `backend` block it adds; `texts.safety`, which D3's
  test compares; the backend's start, which D3's page repeats for a backend that died.
- **Seam to C1, C2** (§8.4): C1's replay hook for E6; their stable test ids for E12. Adopted, not merged.
- **Seam to D4** (§8.7): E10 with an MCP server bound; the profile's `mcp_server_refs: null`.
- **Seam to the SDK fork's release** (§8.6): a `dr-N` tag on `deep-reasoning` and the tarball its release carries.

---

## 2 · Safety: what the app protects, and what it does not

The agent runs model-written Python as the user, with the whole disk and network reachable, as `dr` does today
(spec §2, decision 7). The key proxy runs as the same user. So the app has two kinds of protection: against
**accidents and opportunistic injected code** (a key that ends up in a log, a transcript, a cell's printout, an
`env` dump a model was talked into making; a loop that spends without end), which it holds; and against **a
cell that sets out to defeat it**, which it does not. This section says which is which, and the app says the
same to the user (§2.3).

### 2.1 What it protects

| Property | How | Proven by |
|---|---|---|
| A provider key `dr-acp` holds is not in the worker's environment, a cell's `os.environ` or `/proc/self/environ`, any process the worker starts, the transcript, or the run log. *(v2, from D4 §5 and §11.4, final part: one exception, by the user's configuration: a stdio MCP server whose Canvas settings name the key in its `env` gets it.)* | The worker gets a token under the key's name; every variable whose value contains a held key is removed (§4.7.2); upstream error bodies are redacted before they reach the worker; the proxy never logs headers | E10 #1 (§7.1), and again in the real app (E12); with an MCP server bound once D4 merges (§8.7) |
| The agent-server's own secrets (`OH_SECRET_KEY`, `OH_SESSION_API_KEYS_*`, `SESSION_API_KEY`, and `OPENHANDS_AUTOMATION_API_KEY`, which the launcher sets to the session key, `dev-with-automation.mjs:1066`) are not in the worker's environment | Removed by name (D1's `ALWAYS_REMOVED`, merged with all four, D1 B2) and, by D5, by value | E10 #1; D1's `test_route.py::test_the_agent_servers_secrets_never_reach_the_worker` |
| Spending through the proxy stops at the conversation's cap | Endpoint allow-list; unpriced models refused; reservations before forwarding; a persisted ledger per conversation (§4.7.3) | E10 #2 |
| A token is worth nothing outside its run | Tokens are 256-bit, bound to one run's routes, dropped when the run ends; a route forwards only to the upstream the config named, so a cell cannot send the key to a host of its choosing | §7.1 units |
| Other OS users on a shared machine cannot spend through the proxy | It listens on 127.0.0.1 and needs a token | §7.1 units |
| Canvas's own cookies and scripts do not reach an App's frame, nor the frame Canvas's | The App-backend ingress, C3's default, is another origin and another site than Canvas's (§4.9); the bridge admits a frame's request only with that App's five-minute HttpOnly session cookie (`bridge.py:33, 448–472`) | E12 step 5 (§7.5), with D3's frame |
| Nothing of deep_reasoner is in anything we build or publish, and no read token ships | deep_reasoner is installed on the user's machine with the user's credentials (§4.4); CI's token lives in Actions secrets | the build's artifact check (§4.2) |
| No usage reports go to a third party | Telemetry off at build time (decision K) | §7.3 |

### 2.2 What it does not protect

A cell runs as the user. Everything below is reachable by a cell that tries, and the cap and the token do not
change that.

- **Every Canvas secret, provider keys included.** `~/.deep-reasoning/canvas/secrets.json` is encrypted with
  `…/agent-canvas/secret-key.txt`, which the user (so the cell) can read.
- **The agent-server itself.** `…/agent-canvas/api-key.txt` is the session key. With it, any client may read
  every secret in plaintext (`X-Expose-Secrets: plaintext`, `settings_router.py:120–140`; `GET
  /api/settings/secrets/{name}`, `:492`), install and approve Apps, and change agent profiles, the spend cap
  included. The frontend's local storage holds the same key.
- **Other processes' environments.** On Linux `/proc/<pid>/environ` of `dr-acp` and of the agent-server is
  readable by the same user; both start with the keys in their environment (the bridge passes the conversation's
  secrets to `dr-acp`, `acp_agent.py:3306–3331`).
- **The cap, by a cell that attacks it:** it can edit `spend/<session>.json` and kill `dr-acp` (the bridge
  restarts it, and the ledger is read again), raise `--spend-cap-usd` in the profile for later conversations, or
  read a key and call the provider directly. The cap bounds what is spent through the proxy, by code that does
  not set out to defeat it.
- **The user's files.** The conversation's folder is only the worker's working directory, not a boundary: a cell
  can read and change any file the user can (SSH keys, cloud and `gh` credentials, `.env` files, other projects).
- **The network.** A cell can reach anything the user's machine can.
- **The user's other secrets reach the worker on purpose.** A Canvas secret that is not a provider key the proxy
  holds (a `DAYTONA_API_KEY` for a remote REPL, a `GITHUB_TOKEN` for a tool) stays in the worker's environment,
  because tools need them. The `deep_reasoner` profile's `secret_refs` is `null` (all of the user's secrets reach
  `dr-acp`); a user who wants fewer edits it.
- **A key a cell prints after reading it from disk** lands in our run log. (The agent-server's transcript masks
  the values of Canvas secrets in ACP output, `acp_agent.py:3299`; our run log does not; §11 item 9.)
- **Tools and MCP servers** (D4) are programs that run as the user (spec D4); D4 §5 says plainly what each can
  reach, and a stdio MCP server gets whatever its Canvas settings give it, a provider key included.
- *(v2)* **A Claude Code backbone on the machine's own login.** deep_reasoner starts `claude` with its own
  environment minus every `CLAUDE_CODE*` variable (`v2/claude_code.py:285–307`; D1's EXP-27), and the bridge removes
  `ANTHROPIC_API_KEY` and `ANTHROPIC_BASE_URL` from `dr-acp`'s environment whenever `CLAUDE_CODE_OAUTH_TOKEN` is a
  secret (`acp_agent.py:3035–3058`, `settings/acp_providers.py:537–542`: a `custom` server gets every provider's
  rule). Such a `claude` then calls Anthropic on the login stored in its own configuration, which neither the key
  proxy nor the cap sees (§11 item 3).
- **The Library's backend on macOS** is unauthenticated loopback HTTP that any local user could reach (D2
  decision K and its §9 item 1; on Linux D2 refuses other users' connections; on both, its `Host` check, D2
  as-built §2 #1, stops a rebinding web page, not a local process).
- **The download.** The app is unsigned; on macOS the user clears the quarantine flag by hand (§4.2.6), so they
  trust whatever they downloaded. Releases are assets of a private GitHub repository.

### 2.3 Where the user is told

- **The startup log, at the first install** (the splash shows it): §6's `safety(cap)`, with the cap in force.
- **The decompositions panel, the first time it opens, and its Tools tab** (spec D5): the same sentence, with an
  "I understand" button. *(v2: built by D3, merged: the cap read from the profile's `--spend-cap-usd`, 5 when
  absent, and `SAFETY_NO_CAP` when the profile has `--no-key-proxy`; D4 adds its `TOOLS_RISK` under it in the Tools
  tab, final part.)*
- **The README's install section**: §2.2 in short, with how to uninstall (§4.8.3).

---

## 3 · Where this design departs from, or adds to, the approved spec

Each is a refinement inside D5's scope unless it says otherwise. If the Conductor reads any as a change of what
was approved, it goes back to Michael.

1. **The setup command is an `sh` bootstrap around a separate small package** (decision B), not `dr-app` from
   the main package; the spec's three first-launch failure messages are kept, and the one for deep-reasoning
   itself is new (deep-reasoning is private too, spec D5's evidence).
2. **Who can install v1:** people with read access to **both** deep_reasoner_beta and deep-reasoning (the
   release assets and the setup's fetch), until Michael makes deep-reasoning public. The spec names only
   deep_reasoner_beta.
3. **The state directory is `~/.deep-reasoning/canvas/agent-canvas`,** not the mock-up's
   `~/.openhands/deep-reasoning` (C3 §2.4 and §4.3).
4. **The runtime is installed from a committed export of `uv.lock`** (decision C). The spec says "installs
   deep-reasoning at its pinned commit with uv"; this fixes every transitive version too.
5. **The data home moves to `/var/tmp/deep-reasoning-<uid>` on a network home directory,** with `dr-app home` to
   choose another (D2's ruling made concrete; §4.4.1).
6. **Telemetry is off** in our builds (decision K). The spec does not mention it.
7. **Setup builds the App's backend artifact on the user's machine and starts the backend on every launch**
   (decision G). The spec says setup "installs and enables the Library App"; approval and start were implied by
   its evidence ("starts its backend only once its revision is approved").
8. **The key proxy fails closed on an unpriced model, forwards only model endpoints, reserves before
   forwarding, and routes tool clients and the Claude CLI too** (decisions H and I). The spec gives the proxy
   ≈150 lines and leaves its Anthropic passthrough and cap to the System Designer.
9. **A refused call is HTTP 402,** which neither the OpenAI client nor the Claude CLI retries, so the agent fails
   at once with the proxy's sentence.
10. **`uv run desktop/build.py`**, not the mock-up's `make desktop` (no Makefile for one line).
11. **The build pins uv's version** (`UV_VERSION`), which upstream's download script otherwise takes as the latest
    release (C3 §4.4). *(v2: 0.12.23, the release C3's live test last proved the offline relaunch on, §4.2.1.)*
12. **`~/.deep-reasoning/bin` holds `dr-app` and `dr`;** setup does not edit the user's `PATH` or shell files, so
    the mock-up's `dr-app export …` is `~/.deep-reasoning/bin/dr-app export …` until the user adds that
    directory to their `PATH` (the README says how).
13. **E12 gains four checks** the spec does not list: E10's properties inside the real app, a relaunch of setup
    with the network cut, the App-backend bridge's cookie in Electron's Chromium (*v2:* with D3's own frame, which
    replaces v1's probe App), and *(v2)* a quit that leaves nothing of the setup command running.
14. **The CI is split across three workflows plus trigger files on `main`** (decision M), and owns the shared
    live workflow S1 and S2 asked for (S1 §7.4, S2 §9). *(v2: that workflow, `fork-live.yml`, is built, on `main`,
    and carried S1's and S2's live tiers, §7.4. D5's other workflows reach `main` with its PR stack; v1 said
    `self-hosted-v1`, the spec's §5 branch, which the merged work did not use.)*
15. **Size:** ≈2.7k lines with tests and about 8–9 h at Gate C, against the spec's ≈1.2k and ≈4 h (§10). *(v2:
    ≈2.6k, about 8.5 h; §10.)*
16. ~~**The App-backend ingress is configured** for the desktop app by a generic launcher default in the Canvas
    fork, beyond C3's approved scope.~~ *(v2: no longer a departure of D5's. Michael approved the default as a
    scope addition to C3 on 2026-10-03 (spec, "Scope additions approved" (2)), and C3 built it (#5, B2).)*

---

## 4 · Modules

### 4.1 Files in deep-reasoning

```text
desktop/
    pins.toml                      what one build is made of (§4.2.1)
    build.py                       the build: checks, defaults, frontend, packages (stdlib; `uv run desktop/build.py`)
    electron-builder.dr.mjs        the fork's electron-builder config under our name (§4.2.4)
    bootstrap.sh                   the setup command's sh wrapper, embedded into defaults.json (§4.3.1)
packages/dr-app/                   the deep-reasoning-app package (stdlib only; a uv workspace member)
    pyproject.toml                 requires-python ">=3.12,<3.13", script dr-app = "dr_app.cli:main"
    src/dr_app/
        __init__.py
        cli.py                     dr-app setup | export | home
        layout.py                  AppLayout, the data home, SetupState (setup.json)
        runtime.py                 RuntimeSpec, run_logged, the checks, install_runtime, runtime_is_current
        agent_server.py            AgentServer: a urllib client for the agent-server's REST API
        profile.py                 the deep_reasoner agent profile
        canvas_app.py              stage, install, approve and start the Library App (v2: skeleton)
        texts.py                   every user-visible sentence (§6)
        runtime.lock.txt           `uv export` of the root project's uv.lock (package data)
src/deep_reasoning/acp/
    proxy.py                       KeyProxy, ProxyRoute, SpendLedger (new)
    cli.py                         two options (D1's file)
    route.py, catalog.py, supervisor.py, worker/protocol.py, worker/runner.py   the seam extension (§8.1, D1's files)
    testing/fake_model.py          FakeCall gains the call's Authorization header (D1's test helper, §7.1)
tests/app/                         dr-app (§7.2)
tests/acp/test_key_proxy.py        the proxy's units; tests/acp/test_e10_keys.py  E10 (§7.1)
tests/canvas_app/test_notice.py    one line: texts.safety("7") (D3's file, decision O)
tests/desktop/                     build.py (§7.3); test_e12.py and e12/ (marker desktop, §7.5)
tests/crossrepo/                   E5's bridge replay (marker crossrepo; v2: skeleton)
.github/workflows/
    fork-live.yml                  S1's and S2's live tiers with dr-acp (§7.4; v2: built, on main)
    cross-repo.yml                 pins, E12, E5, E6 (§7.5)
    desktop-release.yml            per-OS builds (§7.6)
    nightly.yml                    on main only: dispatches cross-repo.yml (decision M)
```

Repository wiring, in `main`'s `pyproject.toml` (*v2:* re-read at `1f9fe52`): `[tool.uv.workspace] members =
["packages/dr-app"]`, `deep-reasoning-app` in the dev group with `[tool.uv.sources] deep-reasoning-app = {
workspace = true }`, so the tests import `dr_app`; `uv export --no-emit-workspace` keeps both workspace members out
of `runtime.lock.txt`. *(v2)* `httpx` moves from the dev group into `[project] dependencies`: the proxy imports it,
and today it reaches the runtime only as deep_reasoner's dependency (the lock already holds 0.28.1). Pytest's
`addopts` becomes `-m 'not live and not browser and not desktop and not crossrepo'` (D3 added `browser`), with
the two new markers declared. CI's ruff steps cover `src tests packages desktop`. The dev group already has
`playwright==1.56.0` (D3 added it; E12 drives the app over CDP with it). The hatch sdist already excludes `docs/`;
the dr-app wheel ships `runtime.lock.txt` as package data.

### 4.2 The build

#### 4.2.1 `desktop/pins.toml`

```toml
# What one desktop build is made of. A pin moves only when cross-repo.yml is green on the new set (spec §2).
# Commits are authoritative (Michael's ruling); tags are for people and for the TypeScript client check.

[canvas_fork]
repo = "https://github.com/michaeltheologitis/OpenHands"
commit = "<40 hex: the redone wiring's merge into deep-reasoning, §8.6>"
tag = "dr-1"

[sdk_fork]
repo = "https://github.com/michaeltheologitis/software-agent-sdk"
commit = "34c540ce0598b20ddf913d51968dd903c1c13b2e"
tag = "dr-2"

[app]
product_name = "Deep Reasoning"
app_id = "io.github.michaeltheologitis.deep-reasoning"
executable_name = "deep-reasoning"
version = "1.0.0-rc.1"
maintainer = "<name and email for the .deb; fpm requires an email>"
uv_version = "0.12.23"
```

*(v2)* The values are the skeleton's first set. The SDK fork's is `34c540c` with the tag Michael is pushing there
(`dr-1`, `cef3b24`, is on `dr/integration`, not `deep-reasoning`, so check 8 refuses it). The Canvas fork has no tag
yet: its first, `dr-1`, is cut at the redone wiring's merge (§8.6), and the two forks number their tags apart, as the
spec's mock-up does (its Canvas `dr-2` runs SDK `dr-3`), since a Canvas-only change (C1, C2) moves only the Canvas
tag. `uv_version` is the release C3's live test last proved the offline relaunch on, for the SDK fork's commit
(C3 v3 §9 item 6, run 37148193696); v1's 0.8.17 was the version C3 measured by hand (§11 item 15).

deep_reasoner's pin is not here: it is the root project's dependency (`pyproject.toml`, `uv.lock`) and so a
line of `runtime.lock.txt`. deep-reasoning's own commit is the checkout's `HEAD` at build time.

#### 4.2.2 The pin checks

`check_pins` runs before anything is built, in the build and as `cross-repo.yml`'s first job. Each failure is one
sentence (§6) and the build stops.

1. Each fork's tag resolves to its pinned commit (`git ls-remote <repo> refs/tags/<tag> refs/tags/<tag>^{}`;
   the peeled line wins for an annotated tag, C3 §2.3).
2. The Canvas checkout's `config/defaults.json` has `sources.agentServerGitRepo` equal to the SDK fork's repo and
   `sources.agentServerGitRef` equal to its commit (the Canvas fork's wiring commit, C3 §4.5; *v2:* the redone
   wiring, §8.6). This is the spec's "pins that do not belong together".
3. The Canvas checkout's `package.json` names `@openhands/typescript-client` by a URL containing
   `/releases/download/<sdk tag>/` (the tarball the SDK fork's release step publishes, Q2 (a)).
4. The SDK fork's `uv.lock` at its commit locks the same `agent-client-protocol` version as ours (spec §2: one
   ACP Python at both ends).
5. The Canvas checkout's `paths.stateDir` and `setup` are `null`: the fork carries no value of ours.
6. The deep-reasoning checkout is clean and its `HEAD` is on `origin` (`git branch -r --contains HEAD`), because
   every user's setup will fetch that commit.
7. `runtime.lock.txt` equals `uv export` of `uv.lock` (§7.2's test, run here too).
8. *(v2)* Each fork's pinned commit is on that fork's `deep-reasoning` branch: the history of
   `refs/heads/deep-reasoning`, fetched without blobs (`git fetch --filter=blob:none <repo> deep-reasoning`) into a
   cache under `--work`, contains it (`git merge-base --is-ancestor <commit> FETCH_HEAD`). The fork stacks merge
   into `deep-reasoning`, and the spec pins a `dr-N` tag there; a tag cut on another branch (`dr-1`, on
   `dr/integration`) would ship code no stack carried.

#### 4.2.3 What the build writes into the Canvas checkout

`config/defaults.json`, after the checks, and nothing else in the checkout:

| Key | Value |
|---|---|
| `paths.stateDir` | `"~/.deep-reasoning/canvas/agent-canvas"` |
| `setup.command` | `["sh", "-c", <bootstrap.sh, verbatim>, "dr-app-bootstrap", "git+https://github.com/michaeltheologitis/deep-reasoning@<commit>#subdirectory=packages/dr-app", "https://github.com/michaeltheologitis/deep-reasoning", "<commit>"]` |
| `setup.phases` | `["before-start", "after-ready"]` |
| `telemetry.posthogApiKey` | `""` |

The file is compiled into the frontend (C3 §4.1), so it holds nothing secret: a script, a URL and a commit.

#### 4.2.4 The packages

In the Canvas checkout, in order:

1. `npm ci` (the wiring commit's tarball URL brings our TypeScript client: *v2:* release `dr-2`'s, §8.6).
2. `VITE_DO_NOT_TRACK=1 npm run build:app`.
3. `UV_VERSION=<pins.app.uv_version> node scripts/download-uv.mjs` and `node scripts/download-node.mjs`, with
   `ELECTRON_ARCH=universal` for the macOS release, and `GITHUB_TOKEN` for the API lookup as upstream's workflows
   pass it.
4. `npx electron-builder --config <repo>/desktop/electron-builder.dr.mjs --projectDir <checkout> --publish never`
   (plus `--linux` or `--mac`), with `DR_CANVAS_DIR` and the `[app]` values in the environment.
5. Check the output: exactly the expected artifacts, named `deep-reasoning-<version>-<arch>.<ext>`; for the
   `.deb` and `.AppImage`, list the payload and fail if any path contains `deep_reasoner` (§2.1).

`desktop/electron-builder.dr.mjs`, whole:

```js
// The Canvas fork's electron-builder config under our name. No fork commit: the build points --config here.
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const env = process.env;
const fork = await import(pathToFileURL(join(env.DR_CANVAS_DIR, "electron-builder.config.mjs")).href);
const base = fork.default;
const productName = env.DR_APP_PRODUCT_NAME;
const executableName = env.DR_APP_EXECUTABLE_NAME;
const version = env.DR_APP_VERSION;
const artifactName = executableName + "-${version}-${arch}.${ext}"; // electron-builder macros, not JS

export default {
  ...base,
  appId: env.DR_APP_ID,
  productName,
  extraMetadata: { ...base.extraMetadata, name: executableName, productName, version },
  dmg: { ...base.dmg, title: productName, artifactName },
  linux: { ...base.linux, executableName, artifactName, maintainer: env.DR_APP_MAINTAINER },
  win: undefined,
  nsis: undefined,
};
```

Relative paths in the fork's config (`directories.app`, `extraResources`) resolve against `--projectDir`, and its
`afterPack` hook finds the checkout from its own module path, so both work unchanged.

#### 4.2.5 What stays upstream's in the app

Strings hard-coded in the fork's Electron code keep upstream's name: the splash banner (`bannerTitle`,
`electron/main.mjs:664`), the startup-failure dialog's title (`:755`) and the missing-`uv` dialog (`:708`); the
first-launch notice still says it installs the agent-server "from PyPI" (`:681`), which our build does from git. The
icon stays upstream's (§11 item 6). The menu, the dock, the window list and `userData` take our product name.

#### 4.2.6 Signing

None, as the spec decided: upstream's macOS builds are ad hoc signed by electron-builder and its Linux packages
unsigned (`.github/workflows/desktop-*.yml`). The README gives the macOS command after copying the app to
Applications: `xattr -dr com.apple.quarantine "/Applications/Deep Reasoning.app"`.

### 4.3 The setup command

#### 4.3.1 `desktop/bootstrap.sh`

Run by C3's launcher as `sh -c <script> dr-app-bootstrap SPEC REPO COMMIT`, with stdin closed and every line in
the startup log (C3 §4.2), so it prints nothing secret. Whole:

```sh
# The setup command (C3 §4.2): explain the two failures that happen before dr-app exists, then run it.
set -u
export GIT_TERMINAL_PROMPT=0
: "${GIT_SSH_COMMAND:=ssh -o BatchMode=yes}"
export GIT_SSH_COMMAND
case "$(uname -s)" in Darwin) PATH="$PATH:/opt/homebrew/bin:/usr/local/bin" ;; esac
if ! git --version >/dev/null 2>&1; then
  echo "✗ deep_reasoner is fetched with git, which was not found. On macOS run xcode-select --install; on Linux install git."
  exit 10
fi
uvx --from "$1" dr-app setup --repo "$2" --commit "$3"
status=$?
if [ "$status" -ne 0 ] && { [ "$status" -lt 10 ] || [ "$status" -gt 19 ]; } && ! git ls-remote "$2" HEAD >/dev/null 2>&1; then
  echo "✗ Could not fetch ${2#https://}: check that this computer is online, and that your git credentials can read it. It is private: ask Michael for read access, then sign git in for https (gh auth login, or an SSH key and git config --global url.\"git@github.com:\".insteadOf \"https://github.com/\") and restart. Nothing was installed."
fi
exit "$status"
```

- `GIT_TERMINAL_PROMPT=0` and SSH's batch mode keep git from prompting on a terminal (C3 §4.6); a run from Finder
  has no terminal anyway. The two Homebrew directories go at the end of `PATH` because a credential helper
  configured by bare name (`git-credential-manager`, `gh`) is not on a Finder-launched app's `PATH` (C3 §4.2).
- `dr-app` exits 0, or 10–19 after saying why (§5.2). Any other status means `uvx` failed before `dr-app` ran (or
  argparse refused its arguments); then, and only then, the bootstrap asks git whether the repository is
  readable. A relaunch never reaches that line: `uvx` starts from its cache.
- On macOS with no Command Line Tools, `/usr/bin/git --version` fails and opens Apple's install dialog, which is
  what the message tells the user to do.
- *(v2, C3 v3 §4.2)* `sh` is the command the launcher spawned, so it leads the process group, and `uvx` and
  `dr-app` stay in it: a timeout or a quit signals all three, even after `sh` itself has exited. Nothing here
  detaches. `uvx`'s own fetch of `dr-app` (a first launch, an update) inherits the launcher's output; a git
  credential helper that daemonizes while keeping it would hold the phase open (§11 item 14). Everything `dr-app`
  starts is on a pipe of its own (decision P).

#### 4.3.2 `dr-app setup`

`dr-app setup [--phase before-start|after-ready] --repo URL --commit SHA`. The phase defaults to
`$OH_CANVAS_SETUP_PHASE` (C3 §4.2); with neither, it runs before-start, then after-ready if `AGENT_SERVER_URL`
is set (a run by hand). The whole command holds an exclusive lock on `~/.deep-reasoning/setup.lock`
(`fcntl.flock`), so a terminal run and a launch cannot interleave. Every line goes to stdout, flushed; nothing
prints `SESSION_API_KEY`, a token, a key or a credential. Exit codes: 0; 10 a check failed; 11 the runtime
install failed; 12 the agent-server refused a call setup depends on; 13 the data home is unusable; 2 usage.

*(v2, decision P)* Every subprocess runs through `run_logged` (§5.2): its stdout and stderr on one pipe that
`dr-app` reads, each line copied to stdout as it comes, and the call returns at the subprocess's exit, whatever still
holds the pipe. So when `dr-app` exits, nothing it started keeps the launcher's output, and the phase ends as
`uvx` and `sh` return. A quit
mid-phase stops the whole group within about 4 s (C3 v3 §4.4); a phase still running at 15 minutes (a slow first
install) is stopped the same way and fails the launch with C3's timeout message. Either way the next launch finds a
`*.tmp-*` runtime to remove, the lock released with the process that held it, and `setup.json` as last saved, so it
simply installs again, with whatever uv already downloaded still in its cache.

### 4.4 before-start

1. Create `~/.deep-reasoning` (0700) and load `setup.json` (absent: a fresh `SetupState`).
2. Choose the data home (§4.4.1); when it differs from the recorded one, say so (`home_local` or `home_network`)
   and record it.
3. `spec = RuntimeSpec.for_commit(repo, commit)`. If `runtime_is_current(layout, state.runtime, spec)`, go to 6.
4. The checks (§4.4.2), then `checks_ok`; on a first install (`state.runtime is None`) the `safety` line; then
   `installing`.
5. `install_runtime` (§4.4.3); `installed`; record it.
6. Make `~/.deep-reasoning/bin/dr-app` and `bin/dr` links to `runtime/current/bin/` if missing.
7. *(v2: removed. v1's fallback that wrote the ingress into the agent-server's config file is not needed: C3's
   launcher sets it, §4.9. The number stays so that nothing citing step 8 moves.)*
8. Save `setup.json` (temporary file, then rename).

`runtime_is_current` is true when the record's commit and lock digest equal the spec's, `runtime/current`
resolves to the record's path, and `<path>/bin/python -I -c ""` exits 0 (one exec, about 20 ms: it catches a
deleted runtime and a removed managed Python). So a relaunch with nothing changed costs one JSON read, a few
`stat`s and that exec, plus `uvx`'s own start.

#### 4.4.1 The data home

`choose_home` takes the first that applies:

1. **A recorded home** (`setup.json`'s `dr_home`, written by an earlier launch or by `dr-app home`) that still
   exists, is a directory owned by the user, and is not on a network filesystem: keep it.
2. **`~/.deep-reasoning`,** unless (Linux only) its filesystem type is one of D2's `NETWORK_FILESYSTEMS`, read from
   `/proc/self/mounts` (the longest mount point that prefixes the resolved path), exactly as D2's store does
   (D2 §4.2). `dr_app` mirrors D2's set, and a test pins that the two are equal (§7.2).
3. **`/var/tmp/deep-reasoning-<uid>`** (Linux, on a network home): created with mode 0700 if absent. If it
   exists, `lstat` must show a real directory (not a link) owned by the user with no group or other permissions;
   otherwise exit 13 with `home_unsafe`, because `/var/tmp` is shared and another user could have made it first.

macOS homes are local and get no check (as in D2). `home_network` says that systemd may delete files in
`/var/tmp` unused for 30 days, and how to export or move the data. Nothing is ever moved by setup.

#### 4.4.2 The checks

Run only when the runtime must be installed, so an offline relaunch never runs them:

- `git --version` (the bootstrap already checked; `dr-app` reports the version in `checks_ok`).
- deep_reasoner is readable: `git ls-remote <url> HEAD`, with the bootstrap's git environment, where `<url>` is
  parsed from `runtime.lock.txt`'s `deep-reasoner @ git+<url>@<commit>` line. On failure: `no_access_dr`, exit 10.
  This is the spec's "Nothing was installed": it runs before any install step.
- `uv` is on `PATH` (the app's bundled one comes first): otherwise `NO_UV`, exit 10.

deep-reasoning's own readability needs no check: `dr-app` is running, so `uvx` fetched it.

#### 4.4.3 The runtime install

```text
remove runtime/*.tmp-* left by an interrupted install
uv venv --managed-python --python 3.12 runtime/<commit>.tmp-<pid>
uv pip sync --python runtime/<commit>.tmp-<pid>/bin/python <requirements>
    <requirements> = runtime.lock.txt
                   + "deep-reasoning @ git+<repo>@<commit>"
                   + "deep-reasoning-app @ git+<repo>@<commit>#subdirectory=packages/dr-app"
runtime/<commit>.tmp-<pid>/bin/python -c "import deep_reasoning.acp.cli, deep_reasoning.library.cli, deep_reasoner"
rename runtime/<commit>.tmp-<pid> → runtime/<commit>     (an existing runtime/<commit> is removed first)
link runtime/current.tmp → <commit>; rename over runtime/current
remove every other runtime/<…>
```

`uv pip sync` installs exactly the listed set and nothing it resolves itself; the export carries every transitive
dependency with platform markers, so one file serves macOS and Linux. The two git lines are built from source by
hatchling (fetched from PyPI the first time; cached after); deep-reasoning's wheel carries D3's committed App files
as package data. Every subprocess gets the bootstrap's git environment and runs through `run_logged`, so its output
streams into the startup log and nothing it leaves behind holds the phase (decision P). A non-zero exit is `install_failed`, exit 11; `current` still
points at the previous runtime, but the launch stops (an app update tested its pins together, so an older
`dr-acp` with newer forks is not a state to run in). The spec's mock-up measured the first install at about two
minutes; C3's 15-minute limit per phase bounds it.

### 4.5 after-ready

`AGENT_SERVER_URL` and `SESSION_API_KEY` come from the launcher (C3 §4.2). Every call sends the key as
`X-Session-API-Key` through a `urllib` opener with `ProxyHandler({})`, because on macOS Python would otherwise
send loopback traffic to a system HTTP proxy (S2 decision G).

1. **The agent profile** (§4.5.1). A failure is `agent_server_failed`, exit 12.
2. **The model-key hint.** `GET /api/settings/secrets` lists names; if none is `OPENAI_API_KEY` (the starter
   Library's key, D2 decision M) and none other than `OPENHANDS_AUTOMATION_API_KEY` ends in `_API_KEY`, print
   `NO_MODEL_KEY`. Never fails the launch.
3. **The Library App** (§4.6; *v2:* skeleton). Never fails the launch.
4. Save `setup.json`.

#### 4.5.1 The `deep_reasoner` agent profile

Canvas starts a conversation from the active agent profile (`use-create-conversation.ts:121`), so the profile is
how `dr-acp` becomes the app's agent. `ensure_profile`:

1. `existing` = the `profile` of `GET /api/agent-profiles/deep_reasoner` (404: none).
2. `want = desired_profile(existing, dr_acp=~/.deep-reasoning/runtime/current/bin/dr-acp, home=DR_HOME)`:

   | Field | Created as | On a later launch |
   |---|---|---|
   | `agent_kind` | `"acp"` | owned: reset |
   | `acp_server` | `"custom"` | owned: reset |
   | `acp_command` | `shlex.join([dr_acp])` (the resolver splits it with `shlex`, `profiles/resolver.py:286`; macOS paths can hold spaces) | owned: reset |
   | `acp_subagents` | `true` (S1 §4.6, guarantee 8; merged, §8.2) | owned: reset |
   | `acp_args` | `["--home", DR_HOME, "--spend-cap-usd", "5"]`, each a separate entry (D3 reads the cap from them, D3 §8.4 item 5) | the `--home` pair is owned (replaced or inserted at the front); every other argument is kept |
   | `secret_refs` | `null`: all of the user's secrets (§2.2) | kept |
   | `mcp_server_refs` | `null`: all servers; D4 grants per namespace, and relies on this (D4 §11.4) | kept |
   | everything else | the model's defaults | kept |

3. If `existing` is absent or differs from `want` in an owned field: `POST /api/agent-profiles/deep_reasoner`
   with `want` (the server keeps the profile's `id` and bumps its `revision`, `agent_profiles_router.py:307–364`).
   *(v2: v1's fallback for a 422 naming `acp_subagents` is gone. Every pin the build accepts carries S1's profile
   field (`profiles/agent_profile.py:292`), so a 422 is an agent-server refusing what setup depends on:
   `agent_server_failed`, exit 12.)*
4. Find its `id` in `GET /api/agent-profiles` (listing also triggers upstream's one-time seeding of a default
   profile on an empty store, `agent_profiles_router.py:256–282`, so ours is activated after it).
5. If `setup.json` does not record that setup activated it before: `POST /api/agent-profiles/{id}/activate` and
   record it. A profile the user deleted is created again on the next launch, but not made the default again.

### 4.6 The Library App

*(v2: skeleton; v1's final part. D3 and S2 are merged, and D3 §8.4 settled the split below.)* D3 builds the App and
ships its built files in the deep-reasoning wheel, under `deep_reasoning/canvas_app/`: `canvas-extension.json`
(name `dr-library`, `version` the package's, `0.1.0`; `entrypoint` `dist/index.js`; one conversation panel,
`decompositions`, icon `panel.svg`, four tabs; no `backend` block), `dist/index.js`, `panel.svg`, and `ui/`, which
`dr-library serve` serves at `/ui/` from the same runtime. D5 adds the backend and installs it.

1. **Find D3's files** in the runtime: `runtime/current/bin/python -c` printing
   `importlib.resources.files("deep_reasoning.canvas_app")`. Of them D5 stages exactly three, `STAGED_FILES`:
   `canvas-extension.json`, `dist/index.js` and `panel.svg`. Not `ui/`: a UI-only change must not change the
   digest, which would force a reinstall that stops the backend (D3 §8.4 item 1).
2. **Make the backend artifact**, deterministically (same bytes for the same home, so the same checksum and no
   new approval across launches and upgrades): a gzip (`mtime=0`) tar holding one member `bin/dr-library`, mode
   0755, owner 0, `mtime` 0, whose text is

   ```sh
   #!/bin/sh
   exec '<~/.deep-reasoning/runtime/current/bin/dr-library, shlex-quoted>' "$@"
   ```

   The agent-server checks that the resolved `argv[0]` is an executable regular file inside the unpacked artifact
   (`backend.py:395–412`; the manifest, that `argv[0]` names `{artifact_dir}`, `manifest.py:254–255`); the script
   is, and what it `exec`s is outside, which nothing checks. A `/bin/sh`
   script needs no code signature on Apple silicon (S2 §6.2).
3. **Write the manifest:** D3's `canvas-extension.json` (name `dr-library`) with a `backend` block:

   ```json
   {"schema_version": 1,
    "artifacts": {"<os>-amd64": {"path": "backend/dr-library.tar.gz", "sha256": "<hex>"},
                  "<os>-arm64": {"path": "backend/dr-library.tar.gz", "sha256": "<hex>"}},
    "argv": ["{artifact_dir}/bin/dr-library", "serve", "--port", "{port}", "--home", "<DR_HOME>"],
    "inherit_environment": ["LANG", "LC_ALL", "LC_CTYPE", "PATH", "TMPDIR", "TZ"]}
   ```

   `<os>` is `linux` or `darwin` (`darwin-*` since S2's #3); both architectures name the same script, which runs on
   either. The home is a literal because the backend gets no `DR_HOME` or `HOME` (D2 §4.8). `/health` is the default
   probe and D2's. `inherit_environment` is exactly the agent-server's allowed six (`backend.py:38–40`), which D4's
   Check also passes on to its child (D4 §3.3, `check_env`).
4. **Stage** the three files, the artifact and the manifest under `~/.deep-reasoning/canvas-app/<digest>/`, where
   `<digest>` is the SHA-256 over the manifest and every staged file's path and bytes; an existing directory of
   that name is reused.
5. **Install and start** (`ensure_canvas_app`):

   ```text
   info = GET /api/canvas-extensions/installed/dr-library           (404: none)
   if info is none or state.canvas_app.digest != staged.digest:
       if info: POST …/dr-library/backend/stop                      (a forced install refuses while any App's backend runs)
       POST /api/canvas-extensions/install {"source": <staged dir>, "force": info is not none}
       if info is none: PATCH …/dr-library {"enabled": true}        (a forced reinstall keeps the user's choice)
       record the digest
   if not enabled: print APP_DISABLED; stop here
   status = GET …/dr-library/backend
   unsupported → print APP_UNSUPPORTED; stop here                   (a platform no artifact names)
   if status.prepared_revision != status.revision: POST …/backend/prepare {"revision": status.revision}
   if status.state != "ready": status = POST …/backend/start {"revision": status.revision}
   ready → app_ready, else app_warning with the agent-server's detail
   ```

   Installed from a local path, the App's revision is the hash of its manifest (`backend.py:151–159`), so it
   changes only when the manifest does. Each failing call prints `app_warning` and setup still exits 0. *(v2)* A
   forced install is refused while **any** App's backend runs (`canvas_extensions_router.py:209–212`,
   `has_running_backends`). At after-ready none runs, since backends do not survive an agent-server restart, so the
   `stop` matters only for a hand run; another App's backend still running then gives `app_warning`.

   *(v2)* After launch, D3's page keeps the backend up: before every mount it reads the status and, for a backend
   that is stopped or unhealthy with its revision prepared, calls `start`; it never calls `prepare` (D3 decision F,
   D3 as-built §3.2). Approving stays setup's alone.

Setup approving its own App's backend is the spec's call (D5's evidence: "installing this app is the user's
choice to run it"); the Apps page lists it like any other, and the user can disable it there.

### 4.7 The key proxy and the spend cap

#### 4.7.1 Where it sits

`dr-acp`'s front gains two options (D1's `cli.py`): `--spend-cap-usd USD` (default 5.0, per conversation) and
`--no-key-proxy` (D1's `DirectRoute`, for debugging). With the proxy, `main()` builds a `SpendLedger` and a
`KeyProxy` over the same `PriceTable` the encoder uses, and passes `ProxyRoute(proxy, os.environ)` to
`DrAcpAgent` as its route. The proxy's thread starts on the first grant, so a preview session (S2) that never
prompts never starts it. At shutdown `main()` stops it with a 0.5 s budget inside D1's 1.4 s (D1 §4.2).

Each run, D1's `RunHandle.start` (`supervisor.py:133–143`) calls `route.grant(session=…, run=…,
upstream=source.client, tool_upstreams=source.tool_clients)` (the extension of §8.1), spawns the worker with
`worker_env(os.environ, grant)`, sends the overrides in `Start`, and calls `route.release(run)` when the run ends
(`supervisor.py:228`). The proxy forwards with `httpx`, a direct dependency from v2 on (§4.1).

#### 4.7.2 A grant

`ProxyRoute.grant`, for one run:

1. **The clients.** `"client"` (the main client) and `"tools.<name>.client"` for each tool block with its own
   client. For each: its key name is `api_key_env`, else deep_reasoner's default `NOVITA_API_KEY`
   (`config.py:95`); if `dr-acp` has no value for it but has `OPENAI_API_KEY`, the key is that one, as
   deep_reasoner's `build_client` would fall back (`config.py:256`). No value at all: the client is left as
   configured (nothing to protect; a keyless local server keeps working). Its upstream is `base_url`, else
   `$OPENAI_BASE_URL`, else `https://api.openai.com/v1`.
2. **Tokens and routes.** One token (`secrets.token_urlsafe(32)`) per key name held in this run; one route per
   distinct (upstream, key name), dialect `openai`, bound to that token. The client's overrides are
   `{"base_url": route.url, "api_key_env": <key name>}`.
3. **The Claude CLI.** If `dr-acp` holds `ANTHROPIC_API_KEY`, one more token and a route of dialect `anthropic`
   to `$ANTHROPIC_BASE_URL` or `https://api.anthropic.com`; the worker gets `ANTHROPIC_API_KEY=<token>` and
   `ANTHROPIC_BASE_URL=<route url>`, which a Claude-backbone agent's `claude` process inherits
   (`v2/claude_code.py:285–307`). Not verified against the real CLI (§11 item 3).
4. **The environment.** `env_add` maps each held key name to its token. `env_remove` is every variable whose value
   contains a held key, or the value of a variable that one of D1's `ALWAYS_REMOVED` patterns matches (values of at
   least 16 characters, so short accidental matches cannot remove `PATH`). *(v2: D1's `worker_env` already removes
   the `ALWAYS_REMOVED` names themselves, four glob patterns with `OPENHANDS_AUTOMATION_API_KEY` among them (D1 B2),
   so v1's `AGENT_SERVER_SECRETS` is gone; the proxy adds the copies under other names.)* `worker_env` removes, then
   adds, so each key's own name comes back holding the token.
5. **Loopback past system proxies.** `NO_PROXY` gains `127.0.0.1,localhost,::1`. On macOS, when the environment
   names no proxy but the system does (`urllib.request.getproxies()`), the system's HTTP and HTTPS proxies are
   exported as `HTTP_PROXY` and `HTTPS_PROXY` too: Python reads system proxies only when the environment names
   none, so `NO_PROXY` alone would switch them off for everything else the worker does (S2 decision G found the
   loopback half of this bug).

`release(run)` drops the run's routes and tokens; calls already in flight finish. A route's URL is
`http://127.0.0.1:<port>/r/<route id>`; route ids are 16 hex characters and appear only in that URL.

#### 4.7.3 A request

```text
POST /r/<route>/<rest>        (any other method on a metered path, or any other path: 403 not_a_model_call)
  route unknown, or the token (Authorization: Bearer … | x-api-key: …) not the route's → 401, nothing forwarded
  <rest> metered?   openai: chat/completions, completions, embeddings · anthropic: v1/messages
          free?     anthropic: v1/messages/count_tokens            → forwarded, not counted
  body: JSON, at most 32 MiB; model = body["model"]
  price unknown (estimate(model, {prompt_tokens: 1, completion_tokens: 1}).usd is None) and upstream not loopback → 400 unpriced
  stream requested (openai): body.stream_options.include_usage = true
  reserve = estimate(model, prompt_tokens = ceil(len(body) / 4),
                            completion_tokens = max_completion_tokens | max_tokens | 4096; 0 for embeddings)
  ledger.reserve(session, reserve) refuses → 402 cap_reached, in the dialect's error shape
  forward: the real key (Authorization: Bearer for openai, x-api-key for anthropic), the client's other headers
           minus hop-by-hop, Host, Cookie, Content-Length; httpx, trust_env off for a loopback upstream
  response: status passed through
     JSON  → usage = body.usage; a non-2xx body has every occurrence of the key replaced by "[redacted]"
     SSE   → streamed through as it arrives; usage read from the last openai chunk, or from anthropic's
             message_start (input) and message_delta (output)
  settle(reservation, estimate(model, usage).usd)     no usage reported: the reservation stands
                                                      upstream unreachable: 502 upstream_unreachable, settle 0
```

The price is the provider's when the response reports one, otherwise the table's (D1's `PriceTable`: the package's
`prices.yaml` under `$DR_HOME/prices.yaml`), and 0 for an unpriced model on a loopback upstream. Anthropic's cache
tokens are counted as input tokens. A 402 is not retried by the OpenAI client (it retries 408, 409, 429 and 5xx)
nor, as far as known, by the Claude CLI, so the agent fails at once and D1 shows the sentence as the failure's
detail. The proxy logs one line per refusal (reason, model, session) and never a header, a key or a token.

**The ledger.** Per root session: `spent_usd`, `reserved_usd` (in flight), `calls`, `refused`, and the cap in
force. `reserve` refuses when `spent + reserved + estimate > cap`. `settle` replaces the reservation by the cost.
After each settle the session's file `$DR_HOME/spend/<session>.json` is rewritten (temporary file, then rename);
a session's first reservation reads it, so a restarted `dr-acp` continues the count (the bridge reloads the same
session id, D1 §5.7). The overshoot is bounded by how far each call's real cost exceeds its reservation.

**Threads.** The server is `uvicorn.Server(Config(app, log_level="warning", lifespan="off"))` serving a socket the
caller bound to `127.0.0.1:0`, so the port is known before the thread starts. Routes and the ledger are shared
between the front's loop thread (grants, releases) and the proxy's thread (requests), under one
`threading.Lock`.

### 4.8 Export, the data home, and leaving

#### 4.8.1 `dr-app export DIR [--namespace NAME]`

Runs `runtime/current/bin/dr-library export DIR --home <DR_HOME>` (D2 §4.8), passing its output and exit code
through: `wrote DIR/main.yaml: 4 namespaces, 6 decompositions, 1 tool`. The result runs under `dr` unchanged
(E7 is D2's proof). With no runtime installed: `NOTHING_INSTALLED`, exit 13. It works while the app runs (WAL,
D2 §5.4).

#### 4.8.2 `dr-app home [DIR]`

Without `DIR`: prints the data home and, on Linux, its filesystem type. With `DIR`: it must be absolute, on a
local filesystem, and a directory the user owns (created 0700 if absent); setup records it, and the next launch
updates the profile's `--home` and the App's manifest (a new approval, which setup gives). Nothing is moved:
`home_set` says what to copy.

#### 4.8.3 Uninstall (README)

Delete the app; delete `~/.deep-reasoning` (and `/var/tmp/deep-reasoning-<uid>` if it was used). uv's cache and
managed Pythons are shared with any other uv use and are left alone.

### 4.9 The App-backend ingress

*(v2: shortened. C3 built the default v1 asked for (#5, B2), so D5 sets nothing, and v1's fallback in setup, its
signatures, its test and its size are gone. What remains D5's is the proof in Electron's own Chromium.)* The
Library panel is D3's App page; the data it shows comes from D2's backend through the agent-server's bridge.

**What the bridge requires** (`canvas_extensions/bridge.py`, `canvas_extensions_bridge_router.py`; unchanged
since v1's pin):
- Every `/app-backends/<app>/…` route answers 503 "Canvas App backend ingress is not configured" until
  `app_backend_public_url` (`OH_APP_BACKEND_PUBLIC_URL`, `config.py:350`) names an http(s) origin (`:231–244`).
  *(v2: every launcher now sets it, `scripts/dev-safe.mjs:883–884`: the environment's value, else
  `http://127.0.0.1:<agent-server port>`; `/server_info` reports it as `app_backend_ingress_url`,
  `server_details_router.py:150`, which C2's frames read.)*
- Every request must arrive on that origin, judged by its own `Host` (`:296–301`). The session bootstrap
  (`POST /app-backends/<app>/session`, with the session key) must carry a loopback or allowed `Origin` that is
  not the ingress's own (`:304–314`), and is answered 409 otherwise.
- The session is an HttpOnly cookie, `Secure`, `SameSite=None`, `Partitioned`, scoped to `/app-backends/<app>`,
  for five minutes (`:33, 392–413`); on plain http it is issued only to a loopback host (`:376–389`).

**The origin: `http://127.0.0.1:<agent-server port>`** (18000 in the desktop app), with Canvas in the window at
`http://localhost:8000` (`electron/main.mjs:399`). The launcher binds the agent-server to 127.0.0.1
(`dev-with-automation.mjs:1126–1132`), so the frame reaches it directly with `Host: 127.0.0.1:18000`. It is another
origin than Canvas's (no 409), and another site: the frame is a cross-site context, so its cookie must be
`SameSite=None; Secure; Partitioned`, which is what the bridge issues; the partition key is Canvas's site, so the
cookie the Canvas page's own `fetch` stored is the one the frame sends. Loopback hosts are secure contexts, so
`Secure` holds over http. The agent-server's CORS admits loopback origins with credentials (`middleware.py:34–60`).
The flow, which C2's host code and D3's frame own:

```text
Canvas page (http://localhost:8000)
  fetch("http://127.0.0.1:18000/app-backends/dr-library/session",
        {method: "POST", credentials: "include", headers: {"X-Session-API-Key": <key>}})
     → {ingress_url: "http://127.0.0.1:18000/app-backends/dr-library/", expires_at}  + the partitioned cookie
  <iframe src=ingress_url + "ui/?…">  → every request carries the cookie → the bridge → dr-library serve
  renew before expires_at
```

**What it exposes.** Nothing new listens: the agent-server already serves 127.0.0.1:18000. An App request needs
that App's session cookie, which only a holder of the session key can mint; Canvas's `localhost` cookies are never
sent to the ingress, because it is another site.

**The proof, in the skeleton** (§7.5 step 5). *(v2: v1's probe App is gone; D3's own frame is the probe.)* With
the Library App installed, approved and started by setup, in the app's window over CDP: the session `fetch`; an
iframe at `ingress_url + "ui/?tab=namespaces&cap=5"`, D3's frame UI standalone (without `parent` it shows its own
tab row and posts nothing, D3 as-built §3.3); the frame shows D3's notice, whose text is `texts.safety("5")`; after
`dr-notice-ack`, the Namespaces tab lists the Library's namespaces (`dr-node-<namespace>`), which only D2's API,
reached through the bridge past D2's `Host` guard, can give; the cookie is listed with a partition key
(`Network.getCookies`); and the frame's next request is answered 401 after `DELETE …/session`. The final part
repeats it through C2's header button and D3's page (§7.5).

---

## 5 · Signatures

Valid Python, one field per line, ruff-formatted. Bodies are `...`; docstrings say what tests pin.

### 5.1 `dr_app.layout`

```python
ROOT_DIRNAME: Final = ".deep-reasoning"
CANVAS_DIRNAME: Final = "canvas"  # the agent-server's persistence root
STATE_DIRNAME: Final = "agent-canvas"  # C3's state directory, inside it
NETWORK_HOME_TEMPLATE: Final = "/var/tmp/deep-reasoning-{uid}"
# D2's store.NETWORK_FILESYSTEMS; tests/app/test_layout.py pins that they are equal.
NETWORK_FILESYSTEMS: Final = frozenset(
    {"nfs", "nfs4", "cifs", "smb3", "smbfs", "9p", "fuse.sshfs"}
)


@dataclass(frozen=True)
class AppLayout:
    root: Path

    @classmethod
    def default(cls) -> "AppLayout":
        """Path.home() / ROOT_DIRNAME."""

    @property
    def canvas(self) -> Path: ...

    @property
    def state_dir(self) -> Path: ...

    @property
    def runtime_dir(self) -> Path: ...

    @property
    def current_runtime(self) -> Path: ...

    @property
    def bin_dir(self) -> Path: ...

    @property
    def canvas_app_dir(self) -> Path: ...

    @property
    def setup_file(self) -> Path: ...

    @property
    def lock_file(self) -> Path: ...


@dataclass(frozen=True)
class HomeChoice:
    path: Path
    reason: Literal["recorded", "default", "network-home"]
    filesystem: str | None  # Linux only


def filesystem_type(
    path: Path,
    *,
    mounts: Path = Path("/proc/self/mounts"),
) -> str | None:
    """The type of the longest mount point prefixing path.resolve(); None off Linux."""


def choose_home(
    layout: AppLayout,
    recorded: Path | None,
    *,
    system: str,
    uid: int,
    mounts: Path = Path("/proc/self/mounts"),
) -> HomeChoice:
    """§4.4.1. Raises SetupError(13, texts.home_unsafe(...)) for a /var/tmp directory that is not ours."""


@dataclass
class RuntimeRecord:
    commit: str
    lock_sha256: str
    path: str


@dataclass
class ProfileRecord:
    id: str
    activated_by_setup: bool


@dataclass
class CanvasAppRecord:
    digest: str
    version: str


@dataclass
class SetupState:
    v: int
    dr_home: str | None
    runtime: RuntimeRecord | None
    profile: ProfileRecord | None
    canvas_app: CanvasAppRecord | None

    @classmethod
    def load(
        cls,
        path: Path,
    ) -> "SetupState":
        """A fresh state when the file is absent; raises on v != 1."""

    def save(
        self,
        path: Path,
    ) -> None:
        """Atomic: a temporary file, then rename."""
```

### 5.2 `dr_app.runtime`

```python
PYTHON_VERSION: Final = "3.12"
LOCK_RESOURCE: Final = "runtime.lock.txt"


class SetupError(Exception):
    """A failure setup has explained; main() prints message and exits with exit_code."""

    def __init__(
        self,
        exit_code: int,
        message: str,
    ) -> None: ...


@dataclass(frozen=True)
class RuntimeSpec:
    repo: str  # https URL of deep-reasoning
    commit: str  # 40 hex
    lock_sha256: str
    requirements: str  # runtime.lock.txt plus the two git lines of §4.4.3
    deep_reasoner_url: str  # parsed from the lock's deep-reasoner line
    deep_reasoner_commit: str

    @classmethod
    def for_commit(
        cls,
        repo: str,
        commit: str,
    ) -> "RuntimeSpec":
        """Reads the packaged lock. Raises ValueError for a commit that is not 40 hex."""


def git_environment(
    base: Mapping[str, str],
) -> dict[str, str]:
    """base plus GIT_TERMINAL_PROMPT=0 and, unless set, GIT_SSH_COMMAND='ssh -o BatchMode=yes'."""


# (v2, decision P) How long the line pump may run on after its process has exited.
PUMP_DRAIN_S: Final = 1.0


def run_logged(
    argv: Sequence[str],
    *,
    env: Mapping[str, str],
    log: Callable[[str], None],
    cwd: Path | None = None,
) -> int:
    """argv's exit code. stdout and stderr share one pipe; each line goes to log as it arrives. Returns at the
    process's exit, after at most PUMP_DRAIN_S more of reading: a grandchild that keeps the pipe never holds it.
    Never starts a new session."""


def check_git(
    run: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> str:
    """git's version string. Raises SetupError(10, texts.NO_GIT)."""


def check_readable(
    url: str,
    run: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> None:
    """git ls-remote url HEAD. Raises SetupError(10, texts.no_access_dr(...))."""


def runtime_is_current(
    layout: AppLayout,
    record: RuntimeRecord | None,
    spec: RuntimeSpec,
) -> bool: ...


def install_runtime(
    layout: AppLayout,
    spec: RuntimeSpec,
    *,
    uv: str,
    log: Callable[[str], None],
) -> RuntimeRecord:
    """§4.4.3, every step through run_logged. Raises SetupError(11, texts.install_failed(...)) on any
    non-zero step."""
```

### 5.3 `dr_app.agent_server`

```python
class AgentServerError(Exception):
    def __init__(
        self,
        method: str,
        path: str,
        status: int,
        detail: Any,
    ) -> None: ...


class AgentServer:
    """The agent-server's REST API with the session key; never through an HTTP proxy."""

    def __init__(
        self,
        url: str,
        session_key: str,
        *,
        timeout_s: float = 60.0,
    ) -> None: ...

    def request(
        self,
        method: str,
        path: str,
        body: Any = None,
    ) -> Any:
        """JSON in and out; 404 returns None; any other non-2xx raises AgentServerError."""

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str],
    ) -> "AgentServer":
        """AGENT_SERVER_URL and SESSION_API_KEY (C3 §4.2). Raises SetupError(2, …) if either is missing."""
```

### 5.4 `dr_app.profile`

```python
PROFILE_NAME: Final = "deep_reasoner"
HOME_FLAG: Final = "--home"
SPEND_CAP_FLAG: Final = "--spend-cap-usd"
DEFAULT_SPEND_CAP_USD: Final = "5"
OWNED_FIELDS: Final = ("agent_kind", "acp_server", "acp_command", "acp_subagents")


def desired_profile(
    existing: Mapping[str, Any] | None,
    *,
    dr_acp: Path,
    home: Path,
) -> dict[str, Any]:
    """§4.5.1's table: the owned fields (acp_subagents always true, v2) and the --home pair set, everything else
    kept from existing."""


def needs_write(
    existing: Mapping[str, Any] | None,
    want: Mapping[str, Any],
) -> bool: ...


def ensure_profile(
    server: AgentServer,
    state: SetupState,
    *,
    dr_acp: Path,
    home: Path,
    log: Callable[[str], None],
) -> ProfileRecord:
    """§4.5.1, steps 1–5. Any refusal raises SetupError(12, texts.agent_server_failed(...)); v2 has no 422
    fallback."""
```

### 5.5 `dr_app.canvas_app` (*v2:* skeleton)

```python
# D3's deep_reasoning.canvas_app.APP_NAME; tests/app/test_canvas_app.py pins that they are equal.
APP_NAME: Final = "dr-library"
# D3's built files, in the runtime (§8.3)
APP_PACKAGE: Final = "deep_reasoning.canvas_app"
# (v2) The only files staged; ui/ is served by dr-library serve itself (D3 §8.4 item 1).
STAGED_FILES: Final = ("canvas-extension.json", "dist/index.js", "panel.svg")
ARTIFACT_PATH: Final = "backend/dr-library.tar.gz"


@dataclass(frozen=True)
class StagedApp:
    path: Path
    digest: str
    version: str
    manifest: Mapping[str, Any]


def backend_artifact(dr_library: Path) -> bytes:
    """The deterministic .tar.gz of §4.6 step 2: equal inputs give equal bytes."""


def backend_block(
    *,
    system: str,
    sha256: str,
    home: Path,
) -> dict[str, Any]: ...


def stage_canvas_app(
    layout: AppLayout,
    *,
    home: Path,
    system: str,
) -> StagedApp: ...


def ensure_canvas_app(
    server: AgentServer,
    staged: StagedApp,
    state: SetupState,
    *,
    log: Callable[[str], None],
) -> CanvasAppRecord | None:
    """§4.6 step 5. Never raises for the agent-server's refusals: they become texts.app_warning(...)."""
```

*(v2: `ensure_ingress_config`, `DESKTOP_AGENT_SERVER_PORT` and `AGENT_SERVER_CONFIG_RELATIVE` are gone with §4.9's
fallback; `ensure_canvas_app` no longer serves a probe App, so it uses `APP_NAME`.)*

### 5.6 `dr_app.cli`

```python
EXIT_CHECK: Final = 10
EXIT_INSTALL: Final = 11
EXIT_AGENT_SERVER: Final = 12
EXIT_HOME: Final = 13


def main(argv: Sequence[str] | None = None) -> int:
    """dr-app setup [--phase PHASE] --repo URL --commit SHA | export DIR [--namespace NAME] | home [DIR]."""


def before_start(
    layout: AppLayout,
    repo: str,
    commit: str,
    *,
    env: Mapping[str, str],
) -> None: ...


def after_ready(
    layout: AppLayout,
    *,
    env: Mapping[str, str],
) -> None: ...
```

### 5.7 `deep_reasoning.acp.proxy`

```python
DEFAULT_SPEND_CAP_USD: Final = 5.0
DEFAULT_RESERVED_OUTPUT_TOKENS: Final = 4096
MAX_BODY_BYTES: Final = 32 * 1024 * 1024
MIN_SECRET_LENGTH: Final = 16
OPENAI_DEFAULT_BASE_URL: Final = "https://api.openai.com/v1"
ANTHROPIC_DEFAULT_BASE_URL: Final = "https://api.anthropic.com"
ANTHROPIC_KEY_ENV: Final = "ANTHROPIC_API_KEY"
# build_client's fallback, config.py:256
OPENAI_FALLBACK_KEY_ENV: Final = "OPENAI_API_KEY"
# ClientConfig.api_key_env's default
DEEP_REASONER_DEFAULT_KEY_ENV: Final = "NOVITA_API_KEY"
# (v2) No AGENT_SERVER_SECRETS: the grant matches D1's route.ALWAYS_REMOVED (glob patterns, the launcher's
# OPENHANDS_AUTOMATION_API_KEY among them) with fnmatch to find the values it removes under other names.
LOOPBACK_HOSTS: Final = ("127.0.0.1", "::1", "localhost")

Dialect = Literal["openai", "anthropic"]

METERED_PATHS: Final[Mapping[Dialect, frozenset[str]]] = MappingProxyType(
    {
        "openai": frozenset({"chat/completions", "completions", "embeddings"}),
        "anthropic": frozenset({"v1/messages"}),
    }
)
FREE_PATHS: Final[Mapping[Dialect, frozenset[str]]] = MappingProxyType(
    {
        "openai": frozenset(),
        "anthropic": frozenset({"v1/messages/count_tokens"}),
    }
)


@dataclass(frozen=True)
class Route:
    id: str  # 16 hex, the URL's only identifier
    session: str
    run: str
    dialect: Dialect
    upstream: str  # base URL without a trailing slash
    key: str = field(repr=False)
    token_sha256: bytes = field(repr=False)


@dataclass(frozen=True)
class Reservation:
    session: str
    usd: float


@dataclass(frozen=True)
class Spend:
    session: str
    cap_usd: float
    spent_usd: float
    reserved_usd: float
    calls: int
    refused: int


class SpendLedger:
    """Per root session; persisted at <home>/spend/<session>.json; thread-safe."""

    def __init__(
        self,
        home: Home,
        cap_usd: float,
    ) -> None: ...

    def reserve(
        self,
        session: str,
        usd: float,
    ) -> Reservation | None:
        """None (and refused += 1) when spent + reserved + usd > cap."""

    def settle(
        self,
        reservation: Reservation,
        usd: float,
    ) -> None: ...

    def spend(
        self,
        session: str,
    ) -> Spend: ...


class KeyProxy:
    """The HTTP side: 127.0.0.1 only, its own thread, started on first use."""

    def __init__(
        self,
        *,
        ledger: SpendLedger,
        prices: PriceTable,
        home: Home,
    ) -> None: ...

    def ensure_started(self) -> None: ...

    def stop(
        self,
        timeout_s: float = 0.5,
    ) -> None: ...

    @property
    def base_url(self) -> str:
        """http://127.0.0.1:<port>; only after ensure_started()."""

    def add_route(
        self,
        *,
        session: str,
        run: str,
        dialect: Dialect,
        upstream: str,
        key: str,
        token: str,
    ) -> Route: ...

    def drop_run(
        self,
        run: str,
    ) -> None: ...

    def app(self) -> Starlette:
        """The ASGI app of §4.7.3; tests drive it with httpx.ASGITransport."""


class ProxyRoute:
    """D1's ModelRoute over a KeyProxy (§4.7.2)."""

    def __init__(
        self,
        proxy: KeyProxy,
        env: Mapping[str, str],
    ) -> None: ...

    def grant(
        self,
        *,
        session: str,
        run: str,
        upstream: Mapping[str, Any],
        tool_upstreams: Mapping[str, Mapping[str, Any]] = MappingProxyType({}),
    ) -> RouteGrant: ...

    def release(
        self,
        run: str,
    ) -> None: ...


def is_loopback(url: str) -> bool: ...


def loopback_proxy_env(
    env: Mapping[str, str],
    *,
    system: str,
    system_proxies: Callable[[], Mapping[str, str]] = urllib.request.getproxies,
) -> dict[str, str]:
    """§4.7.2 step 5: NO_PROXY with the loopback hosts appended; on macOS with no proxy in env, the
    system's http and https proxies as HTTP_PROXY and HTTPS_PROXY."""
```

`deep_reasoning.acp.cli.Options` gains two fields after D1's five:

```python
@dataclass(frozen=True)
class Options:
    ...  # D1's config, home, flat, heartbeat_s, log_level
    key_proxy: (
        bool  # --no-key-proxy: D1's DirectRoute, keys stay in the worker's environment
    )
    spend_cap_usd: (
        float  # --spend-cap-usd USD: per conversation, through the key proxy; default 5
    )
```

### 5.8 `desktop/build.py`

```python
@dataclass(frozen=True)
class ForkPin:
    repo: str
    commit: str
    tag: str


@dataclass(frozen=True)
class AppPin:
    product_name: str
    app_id: str
    executable_name: str
    version: str
    maintainer: str
    uv_version: str


@dataclass(frozen=True)
class Pins:
    canvas_fork: ForkPin
    sdk_fork: ForkPin
    app: AppPin


Target = Literal["linux", "mac", "mac-universal"]


def load_pins(path: Path) -> Pins:
    """Raises ValueError naming the key for a commit that is not 40 hex."""


# (v2) The branch every pinned fork commit must be on (§4.2.2 check 8).
FORK_BRANCH: Final = "deep-reasoning"


def check_pins(
    pins: Pins,
    *,
    canvas: Path,
    repo: Path,
    ls_remote: Callable[[str, Sequence[str]], Mapping[str, str]],
    read_sdk_file: Callable[[str], str],
    is_on_branch: Callable[[str, str, str], bool],
) -> list[str]:
    """§4.2.2's checks; the problems as sentences, empty when the pins belong together.
    is_on_branch(repo_url, branch, commit) answers check 8; build() passes one that fetches without blobs."""


def setup_command(
    repo_url: str,
    commit: str,
    bootstrap: str,
) -> list[str]: ...


def patch_defaults(
    defaults: Mapping[str, Any],
    *,
    state_dir: str,
    command: list[str],
) -> dict[str, Any]:
    """§4.2.3's four keys; every other key unchanged."""


def build(
    target: Target,
    *,
    pins: Pins,
    repo: Path,
    work: Path,
) -> list[Path]:
    """Check out the Canvas fork at its commit under work/, check, patch, build, verify; the artifacts."""


def main(argv: Sequence[str] | None = None) -> int:
    """uv run desktop/build.py {linux|mac|mac-universal|check} [--work DIR]."""
```

---

## 6 · Texts (verbatim; tests assert these)

`dr-app` (`dr_app.texts`). *(v2, decision O)* A name in capitals is a constant, a sentence without fields; a
name in lower case is a function that returns the sentence with its fields filled, its parameters the fields, in
order, as `str` (`safety(cap: str) -> str`), like D1's and D2's texts modules. `SUBAGENTS_UNSUPPORTED` is gone, and
the two profile sentences lose their `{on_off}`, with the flat fallback (§4.5.1).

| Name | Text |
|---|---|
| `NO_GIT` | `✗ deep_reasoner is fetched with git, which was not found. On macOS run xcode-select --install; on Linux install git.` |
| `NO_UV` | `✗ uv was not found on PATH. The app bundles it: reinstall the app. In a terminal, install uv from https://docs.astral.sh/uv/.` |
| `no_access_dr(host_path)` | `✗ Could not read {host_path} with your git credentials. It is private: ask Dean for read access, then sign git in for https (gh auth login, or an SSH key and git config --global url."git@github.com:".insteadOf "https://github.com/") and restart. Nothing was installed.` |
| `checks_ok(version, host_path)` | `git {version} ✓ · {host_path} readable ✓` |
| `safety(cap)` | `deep_reasoner runs as you. It can read and change any file you can, and code it writes can find your model keys on this computer if it tries. Spend through the key proxy stops at ${cap} per conversation.` |
| `installing(commit7, dr_commit7)` | `installing deep-reasoning {commit7} with deep_reasoner {dr_commit7} … (first launch, or after an update: a few minutes)` |
| `installed(duration)` | `installed in {duration}` |
| `install_failed(commit7, step, code)` | `✗ Installing deep-reasoning {commit7} failed ({step} exited {code}); its output is above. After an update this needs the network once: connect and restart.` |
| `home_local(home)` | `your data: {home}` |
| `home_network(fstype, home)` | `Your home directory is on a network filesystem ({fstype}), where the Library's database is unsafe, so your data is kept on this computer at {home}. The system may delete files there that go unused for 30 days: export your Library now and then (dr-app export DIR), or choose another folder with dr-app home DIR.` |
| `home_unsafe(path, owner, mode)` | `✗ {path} exists but is not a private folder of yours (owner {owner}, mode {mode}). Remove it, or choose another folder with dr-app home DIR.` |
| `home_set(home, old)` | `Your data will be kept in {home} from the next launch. Nothing was moved: copy library.sqlite, runs/, sessions/ and spend/ from {old} yourself, or export the Library and import it there.` |
| `PROFILE_CREATED` | `agent profile deep_reasoner created and made the default` |
| `PROFILE_UPDATED` | `agent profile deep_reasoner updated` |
| `NO_MODEL_KEY` | `No model key is saved yet: add OPENAI_API_KEY under Settings → Secrets before your first question.` |
| `agent_server_failed(method, path, status, detail)` | `✗ The agent-server refused {method} {path} ({status}): {detail}` |
| `app_ready(version, installed_or_current)` | `App dr-library {version} {installed_or_current} · backend ready` |
| `APP_DISABLED` | `App dr-library is disabled, so Show decompositions is hidden. Enable it under Apps to use it.` |
| `APP_UNSUPPORTED` | `⚠ This agent-server cannot run the Library panel's backend on this platform; conversations still work.` |
| `app_warning(detail)` | `⚠ The Library panel's backend did not start ({detail}); conversations still work. Its log is under Apps → dr-library.` |
| `NOTHING_INSTALLED` | `✗ Nothing is installed yet: launch the app once, then run this again.` |

The bootstrap's two lines are §4.3.1's. The key proxy (`deep_reasoning.acp.texts`, D1's module):

| Name | HTTP | Text |
|---|---|---|
| `cap_reached(spent, cap)` | 402 | `The key proxy refused this model call: this conversation has spent ${spent:.2f} of its ${cap:.2f} cap. Start a new conversation, or raise the cap (--spend-cap-usd in the deep_reasoner agent profile's arguments).` |
| `unpriced(model, home)` | 400 | `The key proxy refused a call to '{model}': its price is unknown, so the spend cap cannot bound it. Add it to {home}/prices.yaml (input and output USD per million tokens), then send your message again.` |
| `not_a_model_call(paths, method, rest)` | 403 | `The key proxy forwards only model calls ({paths}); {method} /{rest} was refused.` |
| `BAD_TOKEN` | 401 | `The key proxy does not know this token.` |
| `upstream_unreachable(host, error)` | 502 | `The key proxy could not reach {host}: {error}.` |

Error bodies take the dialect's shape: `{"error": {"message", "type", "code"}}` for `openai`,
`{"type": "error", "error": {"type", "message"}}` for `anthropic`, with `type` and `code` the name in lower case
(`cap_reached`, `bad_token`, …). `cap_reached` and `unpriced` take floats and a path where the table shows them
formatted (`{spent:.2f}`); the rest take `str`.

The build: `✗ Canvas fork {canvas_tag} runs the agent-server at {wired7} (its wiring commit), but desktop/pins.toml
pins the SDK fork at {sdk_tag} ({sdk7}). Bump both, or neither.`, and one sentence per other check of §4.2.2,
each naming the file and the two values that disagree.

What the startup log shows at a first launch (the splash prefixes each line with its service, C3 §3.3):

```text
[defaults]           From config/defaults.json: OH_AGENT_SERVER_GIT_REF, OH_AGENT_SERVER_GIT_REPO, OH_CANVAS_SAFE_STATE_DIR, OH_SECRET_KEY_PATH, OH_SESSION_API_KEY_PATH
[setup before-start] Running sh -c … dr-app-bootstrap …
[setup before-start] your data: /Users/u/.deep-reasoning
[setup before-start] git 2.39.5 ✓ · github.com/DeanLight/deep_reasoner_beta readable ✓
[setup before-start] deep_reasoner runs as you. It can read and change any file you can, … stops at $5 per conversation.
[setup before-start] installing deep-reasoning a1b2c3d with deep_reasoner d7334ae … (first launch, or after an update: a few minutes)
[setup before-start] … uv's own lines …
[setup before-start] installed in 1m 52s
[setup before-start] Done in 1m 58s
[agent-server]       Using git (michaeltheologitis/software-agent-sdk@34c540ce0598b20ddf913d51968dd903c1c13b2e)
[setup after-ready]  Running sh -c … dr-app-bootstrap …
[setup after-ready]  agent profile deep_reasoner created and made the default
[setup after-ready]  No model key is saved yet: add OPENAI_API_KEY under Settings → Secrets before your first question.
[setup after-ready]  App dr-library 0.1.0 installed · backend ready
[setup after-ready]  Done in 4s
```

*(v2)* The `[defaults]` names are sorted, and each phase is framed by the launcher's own `Running …` and `Done in …`
lines (C3 v3 §3.3, B5); the App's version is deep-reasoning's package version, `0.1.0` today (D3 B5).

---

## 7 · Testing and CI

Plain pytest, each test named for the property it pins; the outside world faked at its boundary (a stub `uv`,
`uvx` and `git` on `PATH` as small scripts that record their argv; an in-test HTTP server answering like the
agent-server; D1's `FakeOpenAI` as the provider). Layer 1 (every push) unless marked.

### 7.1 E10: keys and the spend cap (two automated tests, and the proxy's units)

`tests/acp/test_e10_keys.py`, through `dr-acp` over stdio with D1's harness (`ShimConnection`, `FakeOpenAI`):

- **`test_provider_keys_and_agent_server_secrets_never_reach_the_worker_a_cell_the_transcript_or_the_run_log`**
  (E10 #1). `dr-acp`'s environment holds `OPENAI_API_KEY=sk-e10-<random>`, an alias `MY_KEY_COPY` with the same
  value, `ANTHROPIC_API_KEY`, and random `OH_SECRET_KEY`, `OH_SESSION_API_KEYS_0`, `SESSION_API_KEY`,
  `OPENHANDS_AUTOMATION_API_KEY`. A config of our own points the client at `FakeOpenAI` (loopback) with
  `api_key_env: OPENAI_API_KEY`, a tool block `rag`-shaped with its own `client` naming the same key, and model
  `e10-model` priced in `<home>/prices.yaml`. The fake's responder writes a cell that prints `dict(os.environ)`,
  `open("/proc/self/environ", "rb").read()` and the environment of a child (`subprocess.run(["env"])`), then
  answers. Asserts: none of the secret values (nor their base64) appears in the worker's
  `/proc/<pid>/environ` (pid from the run log's `worker.ready`), in the cell's output, in any update the client
  received, in `events.jsonl`, `worker.log` or any other file under the run's directory, or in `dr-acp`'s stderr;
  the fake received `Authorization: Bearer sk-e10-…` on every call (the proxy swapped it in), for the main client
  and the tool's; the worker's `OPENAI_API_KEY` is a token. Linux only (`/proc`); skipped elsewhere with a reason.
  (D1's `FakeCall`, in `deep_reasoning.acp.testing.fake_model`, gains the call's `Authorization` header for this;
  a test helper, not a seam.)
- **`test_a_call_past_the_spend_cap_is_refused_and_never_forwarded`** (E10 #2). `--spend-cap-usd 0.01`; the config
  sets `max_iter: 50` and `llm_kwargs.max_tokens`, so the reservation is near the cost and the run outlasts the
  cap; the fake reports usage worth $0.004 per call and its responder never answers, so the agent keeps calling. Asserts: the
  run ends `failed` with `cap_reached` in its detail; the fake saw exactly the calls the ledger counted, and none
  after the first refusal; `spend/<session>.json` records `spent_usd ≤ 0.01 + one call's overshoot` and
  `refused ≥ 1`; a second prompt in the same conversation is refused at once, and so is one after `dr-acp` is
  killed and the session reloaded.

`tests/acp/test_key_proxy.py`, the proxy in process (`httpx.ASGITransport` in front, a fake upstream behind):

`test_the_token_is_swapped_for_the_key_and_the_call_forwarded` ·
`test_a_wrong_or_missing_token_is_refused_and_nothing_is_forwarded` ·
`test_only_model_endpoints_are_forwarded` (parametrized: `files`, `fine_tuning/jobs`, `batches`, `images`, a GET
on a metered path) · `test_a_route_forwards_only_to_its_configured_upstream` ·
`test_an_unpriced_model_is_refused_unless_the_upstream_is_loopback` ·
`test_concurrent_calls_overshoot_the_cap_by_at_most_their_reservations` (20 at once) ·
`test_a_streamed_openai_call_is_metered_from_its_last_chunk` (and `include_usage` is injected) ·
`test_a_streamed_anthropic_call_is_metered_from_message_start_and_delta` ·
`test_upstream_error_bodies_never_echo_the_key` · `test_a_released_runs_tokens_stop_working` ·
`test_the_ledger_continues_after_a_restart` · `test_a_client_without_a_held_key_is_left_as_configured` ·
`test_the_key_is_removed_from_the_worker_env_by_value_under_any_name` ·
`test_loopback_calls_bypass_macos_system_proxies_and_others_keep_them` (`system_proxies` faked) ·
`test_the_proxy_never_logs_a_key_or_a_token` · `test_no_key_proxy_keeps_d1s_direct_route`.

E10 runs again in the final part with D4's MCP servers bound in the worker (the same assertions; D4's
`echo_server.py` and its grant, §8.7), and inside the real app in E12.

### 7.2 `dr-app`

| File | Pins |
|---|---|
| `tests/app/test_layout.py` | `test_the_default_home_is_the_root_when_it_is_local`; `test_a_network_home_moves_the_data_to_var_tmp` (a fake `/proc/self/mounts`); `test_a_var_tmp_directory_not_ours_is_refused` (a link, another owner, mode 0755); `test_a_recorded_home_is_kept`; `test_our_network_filesystems_are_d2s`; `test_setup_state_round_trips_and_writes_atomically` |
| `tests/app/test_runtime.py` | `test_a_first_launch_checks_then_installs_from_the_lock`; `test_a_relaunch_with_nothing_changed_runs_no_uv_and_no_git`; `test_a_new_commit_or_lock_reinstalls`; `test_a_broken_runtime_python_reinstalls`; `test_an_unreadable_deep_reasoner_installs_nothing` (exit 10, `no_access_dr`); `test_a_failed_install_keeps_current_and_exits_11`; `test_an_interrupted_install_is_cleaned_up`; `test_git_never_prompts` (the environment); `test_the_runtime_lock_matches_uv_lock` (runs `uv export`); *(v2)* `test_a_background_child_that_keeps_the_output_never_holds_setup` (`run_logged` returns within `PUMP_DRAIN_S` of its process's exit while a `sh -c "sleep 30 &"` grandchild still holds the pipe); `test_nothing_setup_starts_leaves_the_process_group` |
| `tests/app/test_profile.py` | `test_the_profile_is_created_and_made_the_default_once`; `test_a_relaunch_writes_nothing`; `test_the_users_spend_cap_and_other_arguments_survive`; `test_the_profile_always_turns_sub_agent_sessions_on` (*v2*, in place of v1's flat-fallback test); `test_a_refused_profile_fails_setup_with_exit_12`; `test_a_deleted_profile_is_recreated_but_not_reactivated`; `test_a_command_path_with_spaces_is_shell_quoted` |
| `tests/app/test_canvas_app.py` (*v2:* skeleton) | `test_the_backend_artifact_is_byte_for_byte_stable`; `test_the_manifest_names_both_architectures_and_the_home`; *(v2)* `test_only_the_apps_own_files_are_staged` (a changed `ui/` file leaves the digest alone); *(v2)* `test_our_app_name_is_d3s`; `test_a_first_install_enables_approves_and_starts`; `test_a_relaunch_only_starts_the_backend`; `test_an_upgrade_stops_reinstalls_and_reapproves`; `test_a_disabled_app_is_left_alone`; `test_an_agent_server_refusal_warns_and_setup_succeeds`; and one test against a real agent-server from the SDK fork's pinned commit (marker `crossrepo`) that the staged App installs, its artifact passes `prepare` and the backend answers `/health`. v1's ingress-fallback test is gone (§4.9) |
| `tests/app/test_cli.py` | `test_the_phase_comes_from_the_launchers_variable`; `test_a_hand_run_does_both_phases_when_the_agent_server_is_up`; `test_two_setups_never_run_at_once` (the lock); `test_nothing_secret_is_printed` (the session key absent from stdout); `test_export_runs_the_runtimes_dr_library_with_the_home`; `test_home_records_a_local_folder_and_refuses_a_network_one` |
| `tests/canvas_app/test_notice.py` (D3's) | *(v2, decision O)* `test_the_notice_is_d5s_sentence_with_the_cap` compares with `texts.safety("7")`; it stops skipping once `dr_app` is a dev dependency, in the same commit |
| `tests/app/test_bootstrap.py` | `sh` with stub `git` and `uvx`: `test_no_git_says_how_to_install_it`; `test_an_unreadable_deep_reasoning_says_so_and_keeps_uvx_status`; `test_dr_apps_own_failure_passes_through_without_the_access_line`; `test_the_arguments_reach_dr_app_unchanged` (a path with a space) |

### 7.3 The build

`tests/desktop/test_build.py`: `test_pins_with_a_short_commit_are_refused`;
`test_a_canvas_fork_wired_to_another_sdk_commit_is_refused` (the sentence of §6);
*(v2)* `test_a_commit_off_the_forks_deep_reasoning_branch_is_refused` (check 8);
`test_a_typescript_client_from_another_tag_is_refused`; `test_a_different_acp_python_is_refused`;
`test_defaults_gain_only_d5s_four_keys`; `test_telemetry_is_off_in_the_built_defaults`;
`test_the_setup_command_embeds_the_bootstrap_and_the_commit`; `test_a_dirty_or_unpushed_checkout_is_refused`.
`ls_remote`, the SDK file reader and `is_on_branch` are passed in. The packaging itself is tested by building it, in §7.5 and
§7.6.

### 7.4 `fork-live.yml`: S1's and S2's live tiers with `dr-acp` (built)

*(v2: built as v1 wrote it, and on `main` since `633a00d`, so v1's copy of the YAML is dropped here; the file on
`main` is the reference.)* On demand only (it calls gpt-6-luna: cents per run). The run uses the dispatched
branch's copy, and `dr-acp` comes from that same checkout. Run 37147706623, dispatched on `ci/fork-live`
(`a8154e2`: D1's `dr-acp` plus this file) with `sdk_ref` `a3279be`, passed S1's file 2 of 2 and S2's 8 of 8: the
two tiers' Gate B evidence (S1 v2.3, S2 v2.5). The proxy did not exist then. Once step 2 of §1.2 lands, the
Implementer dispatches it on `v1-desktop` with `sdk_ref` `dr-2`, so both tiers run through the key proxy against
the real provider.

- **Inputs:** `sdk_ref` (required), `suites`, `sdk_repo`, `live_config`. deep-reasoning's ref is the ref the run
  is dispatched on (`gh workflow run fork-live.yml --ref v1-desktop -f sdk_ref=dr-2`).
- **Secrets:** `DEEP_REASONER_TOKEN` (the read token D1's CI already uses) and `OPENAI_API_KEY`.
- The two live files and their variables are S1's (§7.4, S1 §5.1 guarantee 10) and S2's (§9). `root` is the
  advising config's non-default namespace (its entry namespace is `advising`). That config offers a decomposition
  only in `advising`, so S2's "the preview equals the started session" check compares options, and an empty command
  list, in `root`; a second namespace with a decomposition in D1's live config would make it compare commands too
  (D1's file, D1's call). With the proxy on by default, the live tier also exercises it against the real provider
  (gpt-6-luna is priced: D1's live test asserts it).

### 7.5 `cross-repo.yml`: pins, E12, E5, E6

Triggers: `pull_request` touching `desktop/**`, `packages/dr-app/**`, `pyproject.toml`, `uv.lock`,
`src/deep_reasoning/acp/proxy.py` or the workflow (D5's own stack, and every pin bump after it, is such a pull
request into `main`; *v2:* v1 said `self-hosted-v1`); `workflow_dispatch` (the copy on `main` lets any branch
dispatch it; the Implementer runs it on `v1-desktop`); and nightly through `main`'s `.github/workflows/nightly.yml`,
which runs on a schedule (`cron: "17 6 * * *"`) with `permissions: actions: write` and does one step,
`gh workflow run cross-repo.yml --ref v1-desktop` (once D5 has merged, `--ref main`). No job calls a real model.
Private access as in D1's CI: `DEEP_REASONER_TOKEN` for DeanLight, and the workflow token, through an `insteadOf`
line, for deep-reasoning itself (the app's setup fetches it like a user's would).

| Job | Part | Does |
|---|---|---|
| `pins` | skeleton | `uv run desktop/build.py check` (§4.2.2) |
| `desktop-e2e` | skeleton, grows | E12 on the Linux app (below) |
| `bridge-replay` | skeleton (*v2:* S1 merged; v1 had it final) | E5's second half, `tests/crossrepo/test_bridge_replay.py`: the SDK fork checked out at its pinned commit and synced (`uv sync --frozen`); its agent-server started from that environment; for each of D1's ten `tests/acp/golden/*.native.jsonl`, a conversation whose ACP agent is S1's scripted agent (`[<sdk python>, <sdk>/tests/fixtures/acp/scripted_agent.py, --transcript, <recording>]`, `acp_subagents: true`; S1's player infers the wait points of an outgoing-only recording, S1 §4.10); one message; the stored events' tree (children, parents, spawning cells, cells per session; S1 §5.1 guarantee 2) equals `deep_reasoning.acp.testing.tree()` of the recording. S1's Cartographer replayed nine of them through the bridge in an uncommitted probe, nine equal trees (S1 design, Gate B section), and C1's `1135e87` reports all ten rendering as stored through `dr-1`; this job makes it evidence. |
| `canvas-replay` | final (**C1**) | E6, as C1 §6.4 specifies it: the Canvas fork and the SDK fork checked out at their pinned commits; from the Canvas checkout, `npx playwright test --config=playwright.mock-llm.config.ts tests/e2e/mock-llm/conversations/mock-llm-acp-replay.spec.ts` with `OH_ACP_REPLAY_TRANSCRIPTS` = D1's ten native recordings joined with `:`, `SCRIPTED_ACP_AGENT` = `<sdk>/tests/fixtures/acp/scripted_agent.py`, and what the mock-LLM config needs (`npm ci`, `npm run build:app`, Playwright's Chromium, `MOCK_LLM_PYTHON`), set up as the fork's `mock-llm-e2e.yml` does. Each transcript's rendered tree equals its stored tree. |

**E12, `tests/desktop/test_e12.py`** (marker `desktop`; `ubuntu-latest`, about 30 minutes): build with
`uv run desktop/build.py linux`; `sudo apt-get install ./dist/*.deb`; under `xvfb-run`, with `HOME` a fresh
directory (so the first launch is a real one: cold uv cache, nothing installed) holding the runner's `insteadOf`
lines, start `/opt/Deep Reasoning/deep-reasoning --remote-debugging-port=<p>` and attach Playwright over CDP
(`chromium.connect_over_cdp`) to the window on `localhost:8000`. `FakeOpenAI` runs in the test process.

Skeleton flow:
1. The first launch reaches the main window; its stdout (the launcher's log) shows both setup phases, the safety
   line and `agent profile deep_reasoner created and made the default`; `GET …/dr-library/backend` is `ready`
   (*v2:* moved here from the final flow), and `/server_info`'s `app_backend_ingress_url` is
   `http://127.0.0.1:18000` (C3 B2).
2. Set the Canvas secret `OPENAI_API_KEY=sk-e12-<random>` through the REST API (the session key from
   `…/agent-canvas/api-key.txt`); point the Library at the fake with
   `~/.deep-reasoning/runtime/current/bin/dr-library import tests/desktop/e12/main.yaml --home ~/.deep-reasoning`
   and price its model in `~/.deep-reasoning/prices.yaml`.
3. In the window, start a conversation (the default agent is `deep_reasoner`) and ask the scripted question; the
   answer appears.
4. E10 in the real app: the worker's `/proc/<pid>/environ` holds neither the key nor any agent-server secret; the
   fake saw the real key.
5. The App-backend bridge in Electron's own Chromium (§4.9's proof): *(v2)* D3's frame, not a probe App, at
   `ingress_url + "ui/?tab=namespaces&cap=5"` inside the window's `http://localhost:8000`; it shows the notice equal
   to `texts.safety("5")` (`dr-notice`), then, after `dr-notice-ack`, the namespaces step 2 imported
   (`dr-node-<namespace>`); its cookie is partitioned; and after the session is deleted the frame's next request is
   refused.
6. *(v2)* Quit: the app exits within 6 s (C3 v3 §4.4: the launcher in about 4 s, inside Electron's 6 s net), and no
   process of the setup command (`uvx`, `dr-app`, `uv`) is left.
7. Run the setup command's before-start phase alone with the network cut: *(v2, C3 B3)* `unshare --map-root-user
   -n`, then `ip link set lo up`, after `sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0` on Ubuntu
   24.04, as C3's `launcher-live.yml` does. It exits 0 within 5 s with no `installing` line (the bootstrap's `uvx`
   from its cache, `dr-app` on its cheap path).

Final flow, each part added with the pin bump that brings it (§1.2):
- **C1** (*v2:* C1 v3 §4.12, §9.4; its branch since Gate B): the scripted question spawns sub-agents with
  `run_all`. Each `subagent-row` sits under the `acp-tool-call` that spawned it, with its `subagent-status`. E12 reads
  the nesting with its own Python copy of C1's `expandAllSubagents` and `readRenderedSubagentTree` (A.9: the same
  in-page DOM reads, against SUB-011's ids; `tests/desktop/e12/subagents.py`, about 40 lines, since E12 is Python and
  C1's helpers are TypeScript), and the tree equals the run log's (`deep_reasoning.acp.testing.tree`). Costs are
  hidden by default, so E12 first asserts no `subagent-cost`, then turns on "Show sub-agent costs" on
  `/settings/app` (`show-subagent-costs-switch`, as C1's `showSubagentCosts` does), reloads, and asserts each row's
  latest cost. One `subagent-stop` with `data-subagent-stop="ready"` stops that child and its branch.
- **C2** (C2 v2 §3.2 B15, CX-006 and ASC-005): before the first message, the picker (`agent-options`,
  `agent-option-namespace-value-<namespace>`) and the slash menu (`slash-command-item`, `data-command`) list the
  namespace's decompositions; `conversation-app-panel-toggle-dr-library-decompositions` opens D3's panel at the top
  right, whose frame shows the Library's namespaces through the bridge; Create decomposition (D3's `dr-name`,
  `dr-use-when`, `dr-card-0-task`, `dr-namespace-<namespace>`, `dr-save`, `dr-result`) saves one into that
  namespace; the next conversation there offers it in the slash menu, and its run log's
  `run.start.source.versions` records it (D2, D3); the panel still loads after its first session's five minutes
  (C2's renewal).
- **D4** (D4 §11.4): an MCP server added through Canvas's settings API (D4's `echo_server.py`), ticked for the
  conversation's namespace in the Tools tab (D4 Appendix B's ids), is called by the next conversation's cell.

### 7.6 `desktop-release.yml`

`push` of a tag `v*` and `workflow_dispatch` (artifacts only). Jobs: `linux` (`ubuntu-latest`: `build.py
linux`, `.AppImage` and `.deb`) and `macos` (`macos-latest`: `build.py mac-universal`, one `.dmg`), each with
§4.2.4's output check. On a tag, a first step requires `cross-repo.yml` green on the tagged commit (`gh run list
--workflow cross-repo.yml --commit <sha> --status success`), and the last attaches the packages to the release
(private, like the repository). The macOS job launches the built app once with a fake model and waits for
`backend ready` in its log, which is S2 PR 3's falsifier on a real Mac ("the Library App's backend does not start
on macOS", S2 §9). *(v2: skeleton, no longer final: D3 and S2's #3 are merged. The first release tag stays final.)*

---

## 8 · What other designs must change, and what D5 asks of D3, C1 and C2

These are contract findings for the Conductor; none is settled sideways. *(v2: three of v1's asks are met (§8.2,
§8.3, §8.5), one is half met (§8.1), §8.4's are adopted but not merged, and §8.6 is now the redone wiring. §8.7 is
new.)*

### 8.1 D1: route tool clients through the seam

*(v2: D1 is merged, `main` at `1f9fe52`. v1's second ask, `OPENHANDS_AUTOMATION_API_KEY` in `ALWAYS_REMOVED`, is
built (D1 B2, `route.py:29–34`, pinned by `test_route.py::test_the_agent_servers_secrets_never_reach_the_worker`).
The tool-client half below is still to build. D5's Implementer builds it, first, in D1's files on `v1-desktop`
(§1.2 step 1), and D1's design names it when it next revises.)*

D1's `ModelRoute` routes the main client only (`RouteGrant.client_overrides` is "merged over `cfg.client`",
`worker/protocol.py:15`, `worker/runner.py:125`). A tool with its own `client` naming the same key (deep_reasoner's
`rag` example does, `configs/example/rag.yaml:25–27`) would then either keep the key in the worker or, once the
proxy removes it, fail. The change is additive; every default keeps D1's behaviour and tests:

```python
@dataclass(frozen=True)
class RunSource:
    config_path: Path
    namespace: str
    client: Mapping[str, Any]
    versions: Mapping[str, Any]
    # NEW: tool name -> its own client block as loaded, for tools that have one.
    tool_clients: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)


@dataclass(frozen=True)
class RouteGrant:
    client_overrides: Mapping[str, Any] = field(default_factory=dict)
    env_add: Mapping[str, str] = field(default_factory=dict)
    env_remove: frozenset[str] = frozenset()
    # NEW: tool name -> overrides merged over that tool's client block.
    tool_client_overrides: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)


class ModelRoute(Protocol):
    def grant(
        self,
        *,
        session: str,
        run: str,
        upstream: Mapping[str, Any],
        tool_upstreams: Mapping[str, Mapping[str, Any]] = ...,  # NEW
    ) -> RouteGrant: ...

    def release(
        self,
        run: str,
    ) -> None: ...


class Start(BaseModel):
    ...  # D1's fields
    tool_client_overrides: dict[str, dict[str, Any]] = {}  # NEW
```

- `ConfigCatalog.materialize` (`acp/catalog.py`) fills `tool_clients` (every `cfg.tools[name]["client"]` that is a
  mapping; `tools` is `dict[str, dict[str, Any]]`, deep_reasoner `config.py:426`). D2's `LibraryCatalog` gets it for
  free, since it delegates `RunSource` to `ConfigCatalog` (`library/catalog.py`, its `materialize`).
- `RunHandle.start` (`supervisor.py:133–143`) passes `tool_upstreams=source.tool_clients` and sends the overrides in
  `Start`; the worker merges each into `cfg.tools[name]["client"]` right after it merges `client_overrides`
  (`worker/runner.py:125`).
- `DirectRoute.grant` accepts and ignores `tool_upstreams`.
- `cli.py` gains §5.7's two options and builds the proxy (D5's Implementer edits D1's file, as D2's did).
- D4 adds its own field to `Start` (`mcp_servers`, D4 §11.1); the two are independent, and `v1-desktop` merges
  `main` once D4 is on it.

About 25 lines in D1's files, plus their tests.

### 8.2 S1: the opt-in on the agent profile (met)

*(v2: built as asked, SDK #13: `ACPAgentProfile.acp_subagents: bool = False` (`profiles/agent_profile.py:292`),
forwarded by the resolver (`resolver.py:305`) and carried back by the seed (`seed.py:58`), with a v2 profile
baseline (`tests/sdk/persisted_settings_baselines/v2/agent_profile_acp_subagents.json`); S1 §5.1 guarantee 8. So
setup always writes `acp_subagents: true`, a field it owns, and v1's fallback for an agent-server without it is
gone (§4.5.1).)* v1's text, for the record: Canvas starts every conversation from the active agent profile
(`use-create-conversation.ts:121`), the resolver builds the settings from `ACPAgentProfile`'s fields only, and
`ACPAgentProfile` forbids unknown keys, so without the field no profile could turn the opt-in on.

### 8.3 D3: settled, and what D5 owes it

*(v2: rewritten. v1 proposed four things before D3 was designed; D3 accepted all four (D3 §8.4) and they are
merged.)* The built App ships in the wheel under `deep_reasoning/canvas_app/` and a CI check (`ci.yml`'s
`canvas-app` job) fails if the committed build differs from a fresh one; the panel shows the safety notice the first
time it opens and permanently in its Tools tab, the cap read from the profile; the panel restarts a backend that
died, by `start` of the prepared revision only. What D5 owes D3, D3 §8.4's seven items, each with where D5 does it:

1. Stage only `canvas-extension.json` (with the `backend` block), `dist/index.js` and `panel.svg`: §4.6 step 1,
   `STAGED_FILES`, `test_only_the_apps_own_files_are_staged`.
2. Keep the backend's argv `serve --port {port} --home <DR_HOME>`: §4.6 step 3.
3. The App ingress configured: C3's default (§4.9); nothing of D5's.
4. Approve and start the backend at every launch: §4.6 step 5.
5. `--spend-cap-usd` and `--no-key-proxy` as separate entries of `acp_args`: §4.5.1's table.
6. E12's final flow through D3's selectors (D3 Appendix A.5): §7.5; *(v2)* the skeleton's step 5 already reads
   `dr-notice`, `dr-notice-ack` and `dr-node-<namespace>` in the real app.
7. D5's sentence and D3's stay equal: D3's `test_the_notice_is_d5s_sentence_with_the_cap` calls
   `texts.SAFETY.format(cap=7)`, which assumed a template (D3 B19). D5's `texts.safety(cap)` is a function
   (decision O), so D5's Implementer changes that one line to `texts.safety("7")` in the commit that makes `dr_app` a
   dev dependency, when the test stops skipping.

### 8.4 C1 and C2: adopted, not merged

*(v2: both adopted what v1 asked; neither is merged.)*
- **C1** (PR #4; C1 v3 §4.12, §6.4, §9.4, A.9): the replay spec
  `tests/e2e/mock-llm/conversations/mock-llm-acp-replay.spec.ts`, one test per path in `OH_ACP_REPLAY_TRANSCRIPTS`
  (D5's name, adopted; skipped when unset), comparing `readRenderedSubagentTree(page)` with
  `readStoredSubagentTree(request, id)`; the SUB-011 test ids (`acp-tool-call`, `subagent-block`, `subagent-row`,
  `subagent-status`, `subagent-cost`, `subagent-stop`, …, listed in the fork's `specs/acp-subagent-sessions.md`); the
  helpers `expandAllSubagents` and `readRenderedSubagentTree` (`tests/e2e/mock-llm/utils/acp-subagents.ts`), which
  E12 mirrors in Python (§7.5); and, since Gate B, "Show sub-agent costs" (frontend-only, in App settings, off by
  default; its switch `show-subagent-costs-switch` is in SUB-011), so E12 turns it on before it asserts a cost. D5
  needs these unchanged when C1 merges; a renamed id or helper is a finding for both.
- **C2** (PR #3; C2 v2 §3.2 B15): the CX-006 ids (`conversation-app-panel-toggle-<extension>-<panel>`,
  `conversation-app-panel-tab-<tab>`, `conversation-app-panel-content`) and the ASC-005 ids (`agent-options`,
  `agent-option-<id>`, `agent-option-<id>-value-<value>`, `slash-command-item` with `data-command`,
  `slash-command-hint`); `host.appBackend.mountFrame`, whose frames read the ingress from `/server_info`'s
  `app_backend_ingress_url`. D3's page runs inside C2's frame; D5's E12 drives both.
- Both are built on `wiring/dr-1` and merge the redone wiring (§8.6) before they merge into the Canvas fork's
  `deep-reasoning`; each merge is followed by a Canvas tag and a pin bump in D5 (§1.2).

### 8.5 The Canvas fork's launcher: a default App-backend ingress (met)

*(v2: built, as v1 proposed it, by C3's #5 (B2, `scripts/dev-safe.mjs:883–884`, pinned by `dev-safe.test.ts ›
buildAgentServerTelemetryEnv › gives Canvas App backends the agent-server's own loopback origin by default` and
`› an OH_APP_BACKEND_PUBLIC_URL in the environment wins`), after Michael approved it as a scope addition to C3 on
2026-10-03. It merged into the Canvas fork's `deep-reasoning` with C3's stack, not into the fork's `main` and not
upstream; v1's "an upstream-shaped PR of its own" is withdrawn. D5's fallback in setup is gone (§4.9).)* D5 relies
on C3 v3's §4 as written; the `sh -c` form is allowed by C3 §2.5.

D2 (§4.8, §6.1) and S2 (merged) need no change.

### 8.6 The redone wiring: not D5's, but the skeleton's pins wait on it

*(v2: rewritten.)* `wiring/dr-1` (`9881d24`) is three fork-only commits on C3's pre-refactor head `22272d9`,
pinning `dr-1`. It is redone on the Canvas fork's `deep-reasoning` at or after `7c12afb`, C3 merged, as fork-only
commits that merge there and nowhere else (not the fork's `main`, not upstream); C1 and C2 then merge it. **What it
must contain for D5:**

1. **`config/defaults.json` `sources`**: `agentServerGitRepo` = `https://github.com/michaeltheologitis/software-agent-sdk`;
   `agentServerGitRef` = the full commit `dr-2` peels to, `34c540ce0598b20ddf913d51968dd903c1c13b2e`;
   `_agentServerGitRefComment` = `tag dr-2 of michaeltheologitis/software-agent-sdk` (C3 v3 §4.5). D5's checks 1 and
   2 (§4.2.2) compare these with `pins.toml`; check 8 needs `34c540c` on the SDK fork's `deep-reasoning`, which it is.
2. **`package.json`** `@openhands/typescript-client` =
   `https://github.com/michaeltheologitis/software-agent-sdk/releases/download/dr-2/openhands-typescript-client-1.50.1.tgz`,
   with the `package-lock.json` npm writes for it (the tarball's hash). D5's check 3 looks for
   `/releases/download/dr-2/`. The release must exist first: `dr-release.yml` creates it when `dr-2` is pushed, once,
   and never replaces the asset.
3. **`scripts/check-sdk-version-sync.mjs` reading a tarball pin** as its locked version (`32bc76e`, with its test),
   so upstream's version-sync check stays green; `versions.agentServer` stays `1.50.1`, the client's version at
   `34c540c`.
4. **`paths.stateDir` and `setup` left `null`**: D5's check 5; D5's build writes them, the fork carries no value of
   ours. Nor does it set `OH_APP_BACKEND_PUBLIC_URL`: C3's default does.
5. Carried for C1's and C2's sake, not D5's: `9881d24`'s `specs` input on `mock-llm-e2e.yml`, and the `sources` keys
   that C1's `mock-llm-e2e.yml` reads to fetch the SDK fork's fixtures.

**And two things after it, which D5 relies on:**
- **C3's `launcher-live.yml` dispatched with no inputs at the wiring's head**, so it reads `sources`: the SDK fork's
  `34c540c` installs once and relaunches with the network cut on the uv the build bundles (C3 v3 §9 item 6, which asks
  for exactly this re-run); and the mock-LLM suite's 180 s web-server timeout re-checked (C3 v3 §4.5; `69d2a6a`
  measured 35–44 s for `cef3b24`).
- **The Canvas fork's first tag**, `dr-1`, on `deep-reasoning` at the wiring's merge commit (the fork has no tag yet;
  D5's check 1 resolves one, §4.2.1). Who pushes it is the Conductor's call, as `dr-2` is Michael's.

**Files on `main`** (decision M): copies of `cross-repo.yml` and `desktop-release.yml`, and `nightly.yml`, placed
the way `fork-live.yml` (`633a00d`) and `live.yml` were, with Michael's yes.

### 8.7 D4 (v2)

D4 (design v5 §11.4) asks four things of D5; none needs D5 to change before D4 merges into `main`:
- **E10 with an MCP server bound** (§7.1): D4's `echo_server.py`, granted to the conversation's namespace; the same
  assertions, plus the server's own environment holding only its configured variables and `mcp`'s six.
- **One exception to §2.1's first row**, stated there: a stdio MCP server whose Canvas settings name a provider key
  gets it, by the user's configuration.
- **The profile's `mcp_server_refs: null`** (§4.5.1), which D4 reads to say when a server is left out. Already so.
- **An E12 step** (§7.5's D4 part), and D4's cross-repo forwarding test (D4 §10.6), which runs in `cross-repo.yml`
  beside `bridge-replay` once D4 merges.

D4's optional "check every stored tool after an upgrade" in setup is not taken in v1 (§11 item 18).

---

## 9 · What D5 relies on

*(v2: re-pinned. Canvas lines at `7c12afb`, SDK lines at `34c540c`, deep-reasoning lines at `main`'s `1f9fe52`.
Row A6 is gone with §4.9's fallback; rows D3, T1, W1, C1, C2, D4, A7 and R5 are new.)*

| # | Behaviour relied on | Their code |
|---|---|---|
| C3 | `defaults.json` `paths.stateDir` and `setup` as in C3 v3 §4.1–§4.4: both phases every launch, cwd the state directory, stdin closed, the phase variable, `AGENT_SERVER_URL` and `SESSION_API_KEY` after ready, a non-zero exit stops the launch with the output shown, 15 minutes per phase, the key files beside the state directory; *(v2)* a phase ends when the command's output closes; at a timeout or a quit the command's group is signalled even after the command has exited, SIGKILL at 3 s, given up 1 s later; a quit in about 4 s; `OH_APP_BACKEND_PUBLIC_URL` defaulted (B2) | Canvas fork `deep-reasoning` at `7c12afb`: `scripts/dev-with-automation.mjs` (`runSetupCommand`, `stopService`), `scripts/launcher-defaults.mjs`, `scripts/dev-safe.mjs:883–884` |
| L1 | A packaged app puts the bundled `uv` and Node first on `PATH`, then the OS's (`/usr/bin:/bin:/usr/sbin:/sbin` from Finder) | `electron/main.mjs:103–253` |
| L2 | The ingress serves `http://localhost:8000` and the window loads it | `electron/main.mjs:399` |
| L3 | `electron-builder` resolves `directories.app` and `extraResources` against `--projectDir`; the fork's `afterPack` finds the checkout from its own path; `extraMetadata` reaches the packaged `package.json` | `electron-builder.config.mjs:92–96, 324, 332–336, 348, 398` (unchanged since v1's pin) |
| L4 | `VITE_DO_NOT_TRACK=1` at build time and an empty `telemetry.posthogApiKey` turn off the frontend's, agent-server's and automation's reports | `src/services/telemetry.ts:68–70, 361`; `scripts/dev-safe.mjs:752–790`; `dev-with-automation.mjs:102, 1070–1084` |
| A1 | Agent profiles: `POST /api/agent-profiles/{name}` saves (422 with `loc` for an unknown field), `GET` lists ids and the active pointer, `POST /{id}/activate` sets it; `acp_command` is a shell string split with `shlex`; `secret_refs` null passes every secret; *(v2)* `acp_subagents` on the profile | `agent_profiles_router.py:256–481`; `profiles/agent_profile.py:77–135, 223–300`; `profiles/resolver.py:265–306` |
| A2 | Canvas Apps: install from a local path, disabled; a forced reinstall keeps the enabled state and refuses while any App's backend runs; `prepare` checks the checksum and unpacks; `start` needs the prepared revision; the executable must resolve inside the artifact; the backend gets only the allowed variables and runs in the package directory; a local install's revision is the manifest's hash | `canvas_extensions_router.py:189–242, 299–321, 344–404`; `installed.py`; `backend.py:38–40, 151–159, 251–300, 395–412, 478–540`; `manifest.py:185–255` |
| A3 | The ACP bridge passes its environment and the conversation's secrets to the agent, and masks secrets in ACP output | `acp_agent.py:3299, 3306–3331` |
| A4 | `GET /api/settings/secrets` lists names | `settings_router.py:454` |
| A5 | The App-backend bridge: 503 until `app_backend_public_url` is set; requests judged by their `Host`; the session bootstrap from a loopback `Origin` other than the ingress's; a five-minute `Secure; SameSite=None; Partitioned` HttpOnly cookie, issued over http only to a loopback host; loopback origins allowed with credentials by CORS; *(v2)* `/server_info` reports the ingress | `canvas_extensions/bridge.py:33, 231–244, 296–314, 376–447`; `canvas_extensions_bridge_router.py:32–60`; `config.py:350`; `middleware.py:34–60`; `server_details_router.py:150` |
| A7 | *(v2)* For an ACP server no provider claims (`custom`), the bridge applies every provider's credential rule: `CLAUDE_CODE_OAUTH_TOKEN` present removes `ANTHROPIC_API_KEY` and `ANTHROPIC_BASE_URL` (§2.2) | `acp_agent.py:2988–2997, 3035–3058`; `settings/acp_providers.py:537–542` |
| L5 | The window loads Canvas from `http://localhost:8000`; the agent-server listens on 127.0.0.1 at the fixed port 18000 | `electron/main.mjs:399, 742`; `config/defaults.json` `ports.agentServer`; `dev-with-automation.mjs:1126–1132` |
| L6 | Electron's Chromium stores a partitioned third-party cookie set on a credentialed cross-site `fetch` from a loopback page, and sends it from a frame on that site (unverified: E12 step 5 is the proof) | Electron 43 (`package.json:154`) |
| D1 | `ModelRoute`, `RouteGrant`, `worker_env`, `ALWAYS_REMOVED` (four glob patterns), `PriceTable` (`estimate`, `$DR_HOME/prices.yaml`), `Home`, `FakeOpenAI`, the harness; `RunHandle.start` grants and `release` at run end; `--home`; `Options`' five fields | `main` at `1f9fe52`: `acp/route.py:9–58`, `acp/costs.py:61–99`, `acp/runlog.py:172–188`, `acp/supervisor.py:133–143, 228`, `acp/cli.py:18–27`, `acp/testing/fake_model.py`; D1 as-built §4.6 |
| D2 | `dr-library serve --port P --home DIR`, `dr-library export DIR --home DIR` and its output line, `/health`, `NETWORK_FILESYSTEMS`, `LibraryCatalog` as `dr-acp`'s default; *(v2)* the `Host` guard | `library/cli.py`, `library/texts.py:225–229`, `library/api.py:324`, `library/store.py:70–72`, `library/catalog.py`; D2 as-built r2 §2 #1, §4.7 |
| D3 | *(v2)* The App package `deep_reasoning.canvas_app` in the wheel (`canvas-extension.json` without a `backend` block, `dist/index.js`, `panel.svg`, `ui/`; `APP_NAME`); `dr-library serve` serves `/ui/`; the page restarts a dead backend by `start` of the prepared revision, never `prepare`; the notice compares with `texts.safety`; the frame's test ids (D3 Appendix A.5) | `src/deep_reasoning/canvas_app/`, `library/ui.py`, `canvas-app/src/page/backend.ts`, `tests/canvas_app/test_notice.py`; D3 §8.4, as-built r4 §3 |
| S1 | `acp_subagents` on the profile (§8.2); the scripted agent's `--transcript` with inferred wait points; the two live-test files and their variables | SDK `34c540c`; S1 v2.3 §5.1 guarantees 8, 9, 10 |
| S2 | Header panels in the manifest (#4); `darwin-*` backends and loopback never proxied (#3); the live-test file and its variables | SDK `34c540c`; S2 v2.5 §5, §6, §9 |
| T1 | *(v2)* A pushed `dr-N` tag on the SDK fork creates prerelease `dr-N` with `openhands-typescript-client-<version>.tgz`, once, never replaced | SDK `.github/workflows/dr-release.yml` (#18) |
| W1 | *(v2, expected)* The redone wiring's `sources`, client pin and version-sync reading (§8.6), and a Canvas tag at its merge | Canvas fork `deep-reasoning`, after `7c12afb` |
| C1 | *(v2, expected)* `OH_ACP_REPLAY_TRANSCRIPTS` and the replay spec; SUB-011's ids; `expandAllSubagents` and `readRenderedSubagentTree` as in-page DOM reads; `show-subagent-costs-switch`, off by default | Canvas PR #4; C1 v3 §4.12, §6.4, §9.4, A.9; `dfde47e`, `4db661f` |
| C2 | *(v2, expected)* CX-006 and ASC-005's ids; `host.appBackend.mountFrame` reading `app_backend_ingress_url` | Canvas PR #3; C2 v2 §3.2 B15, §6.4 |
| D4 | *(v2, expected)* `echo_server.py` and a grant for E10 with an MCP server; D4 Appendix B's ids; the profile's `mcp_server_refs: null` read | `v1-custom-tools` at `461c3b5`; D4 v5 §10.6, §11.4 |
| R1 | `build_client` reads `api_key_env`, falls back to `OPENAI_API_KEY`, uses `base_url` | deep_reasoner `config.py:90–102, 249–266` |
| R2 | A tool block's own `client` is built with `build_client` | `tools/base.py:150–152, 205–207` |
| R3 | A Claude agent's `claude` process inherits the worker's environment, minus `CLAUDE_CODE*` | `v2/claude_code.py:285–307` |
| R4 | `DR_HOME` means something else to deep_reasoner (its Claude run root), so D5 never sets it | `v2/claude_code.py:262–270` |
| R5 | *(v2)* That `claude` therefore never sees a `CLAUDE_CODE_OAUTH_TOKEN` and runs on the machine's own login (D1's EXP-27) | `v2/claude_code.py:285–307` |
| U1 | uv: a commit-pinned git requirement runs from cache offline; `uv pip sync` installs exactly the listed set; `uv export --no-emit-workspace --no-dev --no-hashes`; `uv venv --managed-python` | uv 0.8.17 (C3 §2.3 measured the first); *(v2)* the first re-proved on 0.12.22 and 0.12.23 by C3's live test; the rest not yet run on 0.12.23 (§11 item 15) |
| U2 | uvicorn does not install signal handlers off the main thread | `uvicorn/server.py`, `capture_signals` (*v2:* read again on 0.54.0, the lock's) |
| G1 | GitHub: an on-demand workflow's file must exist on the default branch and runs from the dispatched ref; a scheduled workflow runs from the default branch; a `workflow_dispatch` sent with the workflow token starts a run | GitHub Actions |

---

## 10 · Size

*(v2: re-estimated. Gone: `fork-live.yml` (built, 70), §4.9's fallback (50), the probe App (60), the flat
fallback (30). Added: `run_logged` (40 with its tests), check 8 (15), the staged-files and app-name pins (10),
E12's Python mirror of C1's two reads (40), E10 with an MCP server (30). The Library App moves into the skeleton.)*

| Part | Code | Tests | Skeleton or final |
|---|---|---|---|
| `desktop/` (pins, `build.py` with its eight checks, wrapper config, bootstrap) | 250 | 125 | skeleton |
| `dr-app`: layout and home 90, runtime with `run_logged` 130, agent-server client 50, profile 55, CLI and texts 100 | 425 | 310 | skeleton |
| `dr-app`: the Library App | 110 | 95 | skeleton (v1: final) |
| The key proxy (server and metering 200, routes and grant 85, ledger 60), `cli.py` 20, D1's seam 25 | 390 | 330 | skeleton |
| Workflows: `cross-repo` 150, `desktop-release` 90, the files on `main` 30 | 270 | — | skeleton, except `canvas-replay` (≈30) |
| E12's harness (skeleton 150, final 130 with the mirror of C1's reads), E5's comparator 70 | — | 350 | skeleton 220, final 130 |
| E10 with an MCP server bound | — | 30 | final |
| **Total** | **≈1.45k** | **≈1.24k** | **≈2.7k, about 9 h at Gate C** |

The spec estimated ≈1.2k with tests and ≈4 h. The difference: the key proxy (≈150 in the spec) covers two
dialects, tool clients, an endpoint allow-list, reservations, a price policy and a persisted ledger, because a cap
without them does not bound spending (decision I); the Library App's staging and approval, which the spec left to
the System Designer; the workflows and the E12 harness, which the spec costed at ≈100 together; and `dr-app`'s
own package. About 2.5k of it is the skeleton; the final part is about 0.2k, all of it tests and one CI job.

---

## 11 · Open items, and what I was unsure about

1. ~~**S1's profile field** (§8.2)~~ *(v2: met, SDK #13.)* **D1's seam extension** (§8.1): its second half
   (`ALWAYS_REMOVED`) is built; the tool-client half is D5's Implementer's first step, in D1's files (§1.2). The
   Conductor routes it, and D1's design names it when it next revises.
2. **The redone wiring and the Canvas tag** (§8.6) *(v2: replaces v1's "no owner")*: the Conductor's next step after
   `dr-2`. Skeleton step 7 waits on both, and on nothing else.
3. **The Claude CLI behind the proxy** is designed (§4.7.2 step 3) but not verified: I may not run the real
   `claude`, and I do not know every endpoint it calls with an API key (only `v1/messages` and its token count are
   allowed). Whether it matters waits on Dean's answer about the default backbone; so does whether setup installs
   the CLI. If it does: `npm install --prefix ~/.deep-reasoning/runtime/<commit>/node @anthropic-ai/claude-code@<pin>`
   with the bundled npm, linked into the runtime's `bin/` (deep_reasoner puts its interpreter's directory on the
   Claude process's `PATH`, `v2/claude_code.py:298–300`); about 30 lines and a live check. *(v2)* And a `claude`
   on a subscription login escapes the proxy and the cap entirely (§2.2: deep_reasoner drops `CLAUDE_CODE*`, and the
   bridge drops `ANTHROPIC_API_KEY` when `CLAUDE_CODE_OAUTH_TOKEN` is a secret); D5 does not try to route it.
4. **macOS is unverified on hardware:** the system-proxy handling (§4.7.2 step 5), the credential helpers on a
   Finder `PATH`, and the App backend through S2's #3. The release job's macOS smoke (§7.6; *v2:* now in the
   skeleton) is where they are first seen together.
5. **Measured later, in the as-built:** `uvx`'s start for `dr-app` on a relaunch (C3 measured 6.4 s for the
   agent-server's four packages; a package with no dependencies should be far less), the first install's time and
   disk use, and the after-ready cost of starting the backend (D2 measured ≈1.4 s of imports).
6. **The icon and the `.deb` maintainer** are Michael's: the app keeps upstream's OpenHands icon (replacing it is
   three files and one `directories.buildResources` line in the wrapper), and fpm needs a maintainer's email.
7. **`/var/tmp` on a network home** may be cleaned by systemd-tmpfiles after 30 days of disuse; the message says
   so, and `dr-app home` lets the user choose a local folder, but nothing stops the cleanup.
8. **The files on `main`** (decision M): copies of `cross-repo.yml` and `desktop-release.yml`, and `nightly.yml`,
   placed with Michael's yes as `fork-live.yml` was (`633a00d`).
9. **Masking held keys in our own run log** (§2.2): the front knows every value the proxy holds and could replace
   it in what it writes, as the agent-server does in its transcript. That is D1's encoder and run log, so it is a
   proposal, not part of this design; it protects only against a cell that prints a key it found, not one that
   encodes it.
10. **E12's first launch** may meet Canvas onboarding dialogs (an LLM setup prompt for the OpenHands agent, the
    telemetry consent); the harness dismisses whatever appears, and stable test ids (§8.4) would make that
    sturdier.
11. **The App-backend ingress in Electron's Chromium** (§4.9) *(v2: C3's part is settled, built and approved.)* That
    Electron's Chromium keeps the bridge's partitioned cookie for a frame on `127.0.0.1` under a `localhost` window
    is unverified until E12 step 5 runs; so are the bridge's forwarding past D2's `Host` guard (D2 as-built §7 item
    1) and D3's frame behind the real bridge (D3 as-built §9 item 1), which the same step is first to run. If the
    cookie fails, the candidates are the same site on another port (`http://localhost:18000`, weaker isolation,
    decision N) or an https ingress, and the choice comes back here and to C3.
12. **The wrapper config** relies on electron-builder accepting a `.mjs` config outside the project directory with a
    top-level `await import`; electron-builder loads ES module configs, but the build's first run is the check.
13. *(v2)* **The Canvas fork has no tag.** Its first, `dr-1`, is cut at the redone wiring's merge (§8.6), and the
    two forks number their tags apart (§4.2.1). If Michael prefers matched numbers (Canvas `dr-2` for SDK `dr-2`),
    only `pins.toml`'s value changes.
14. *(v2)* **A background process can hold a phase open** (C3 v3 §4.2). Everything `dr-app` starts goes through
    `run_logged` (decision P), but `uvx`'s own fetch of `dr-app` (a first launch, an update) inherits the launcher's
    output. A git credential helper that daemonizes and keeps stderr would hold before-start until the 15-minute
    limit and fail the launch. Git's own `cache` helper and ssh's `ControlPersist` master are, as far as I know, written
    to drop their output when they detach; I did not check either here. If a helper is found that keeps it, the
    bootstrap would need a pipe of its own around `uvx`, which `sh` cannot give without waiting on it.
15. *(v2)* **uv 0.12.23** is pinned for the build because C3's live test proved the offline relaunch on it; D5's own
    uv commands (`uv venv --managed-python`, `uv pip sync` of the export, `uv export --no-emit-workspace`) were read
    against 0.8.17 and are not yet run on 0.12.23. §7.2's runtime tests run the real `uv export`, and the first E12
    runs the rest.
16. *(v2)* **For Michael's Gate B: the departures from the spec**, all in §3: items 1 to 15 stand (13 to 15 with v2
    notes), and 16 is withdrawn (C3's scope addition). v2 adds no departure from the spec. It does make choices Gate
    B may want to see: the skeleton now holds the Library App, E5's replay and the macOS smoke (§1.2); the flat
    fallback is gone, so an agent-server without S1 fails setup (§4.5.1); a line of D3's test changes with
    `texts.safety` (decision O); the build refuses a pin off a fork's `deep-reasoning` (check 8); uv is pinned at
    0.12.23 (item 15); and the size is ≈2.7k, about 9 h at Gate C, against the spec's ≈1.2k and ≈4 h (§10).
17. *(v2)* **C1's and C2's ids may still move.** C1 is being refactored and C2 split; E12's final steps are written
    against SUB-011, CX-006 and ASC-005 as their designs list them, and follow whatever merges (§8.4).
18. *(v2)* **D4's "check every stored tool after an upgrade"** (D4 §14 item 4) is not taken: it would put
    deep_reasoner's imports and every tool's factory on setup's path after each update, and Check already runs
    when a tool is saved. The Conductor may route it to D4's next revision.
