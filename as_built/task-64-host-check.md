# TASK-64 · As built: the launcher's page refuses other host names

**TASK-64** · Cartographer · 2026-10-19 · branch `as-built/task-64`, cut from `main` `9e8109e`. The build is in two
repos: the Canvas fork's `fix/launcher-host-check` at `0d925ea` (one commit on `dr-3` = `4355a36`, +519/−10) and
deep-reasoning's `ux-round` commit `3531384` (E12's step, +83/−11). It is checked against one document: the design,
`docs/design/task-64-host-check.md` on `design/task-64` at `1324d8c`. There is no spec.

**Evidence.** Every claim carries a mark. **[run]**: I ran it in this sandbox, at the fork's `0d925ea` or at `ux-round`
`b283be2`; nothing called a model. **[CI]**: a named CI run shows it. **[impl]**: the Implementer ran it on 2026-10-19;
I read its saved output and did not repeat it. **[read]**: I read it in the code and did not run it.

**Reading guide.** §0 is the five-minute read. §1 is the map, §2 every divergence from the design, §3 the proof, §4
what nobody ran. About ten minutes in all.

---

## 0 · What Michael gets, and what changed against what he approved

**What he approved** (2026-10-19, in chat, no spec): "Do them without the spec go with what you recommend", and later a
standing green light to merge this round. The design carried the scope: while a page carries the session key, the
listeners that serve it answer only to this machine's names.

**What he gets.** The check covers the desktop app, TASK-48's browser command, and `npx @openhands/agent-canvas`. It
covers `npm run dev`, `dev:static` and `dev:minimal` in local mode, and the Docker quickstart with its LAN opt-in. In
each, a request whose `Host` is not `localhost`, a name under `.localhost` or an IP address gets a 403 before any
routing (one exception on Vite's port: item 1). The page, `/api`, `/server_info` and static files get the same 403
[run]. Its body is one sentence that names
`--public`, and a WebSocket upgrade gets `HTTP/1.1 403 Forbidden` [run]. Under `localhost`, `127.0.0.1`, `[::1]`,
`app.localhost` or a LAN address, on any port, everything answers as before, key included [run]. Public mode,
off-loopback binds and Docker without the opt-in are unchanged: their pages carry no key, so nothing checks [run for
the static server; read for the launchers].

In the real Linux app, E12 asks both of the app's ports under `Host: rebound.example` and gets 403 without the key.
Under `localhost`, both answer 200 with the key. It passed in three `cross-repo` runs [CI]. In Chromium, a page served
as `rebound.example` (resolved to 127.0.0.1) gets the 403 page. Its `window.__AGENT_CANVAS_SESSION_API_KEY__` is
undefined, and its own `fetch("/")` and `fetch("/server_info")` get 403 [impl].

**Against the design, the static server and the ingress behave as designed.** Vite, the tests and the size diverge
(§2):

1. **Vite proxies a WebSocket under any `Host`.** Only `npm run dev` and `dev:minimal` run Vite; the app does not. On
   Vite's port, the page and proxied HTTP get Vite's 403 [run], and so do modules [impl], but a `/sockets` upgrade
   goes through [run].
   Without the key, the agent-server closes it with 4001 after 10 s [impl], so no key leaves. The design says such
   routes are refused. The Conductor's call: correct that wording, add no Vite plugin. The corrected sentence is in §2.
2. **Vite's rule differs from the other two** on five `Host` values a browser does not send. Three of them get Vite's
   page with the key [run]. That browsers never send them is [read].
3. **E12 has no `xfail` mark**, on the Conductor's direction. The design marks it strict-xfail while `pins.toml` pins
   `dr-3`, and `ux-round` still pins `dr-3`. So a `cross-repo` run at the pins fails E12's two host tests until the
   pins move to `dr-4`. The green runs give Canvas `1a9e3c6` in place of the pin [CI].
4. **Not reported: E13 has no host test.** Design §5.2 gives TASK-48's E13 the same test. `task-48-browser` has none,
   and the task row says it is folded in later.
5. **Not reported: the size.** Code is +146 lines against ≈60, and tests +456 against ≈200. Gate C reads in about 2 h
   rather than 1 h.
6. **Text.** Doc comments, the skill-guide bullet and one `bind-host.mjs` sentence differ from §3, and the tests add a
   few rows. The 403's text is §4's byte for byte [run].

**Not run by anyone:** the Docker image, Electron on macOS and Windows, and the fork's own CI (it runs on PRs only).
The Implementer's full `npm test` exited 1: two of 8,433 tests failed after a 32-minute run, in files TASK-64 does not
touch. Both files pass alone at `0d925ea` [run]. `README.windows.md` is unchanged. The design does not name it, and its
one sentence on the key (the Docker opt-in on host loopback) still holds [read].

**Defects:** none found.

**Ships in** Canvas `dr-4` (design §6); the tag is Michael's. The integration build `1a9e3c6` already carries it (§3).

---

## 1 · The map

**One predicate, three listeners.** `scripts/bind-host.mjs` holds the rule and the refusal. Copied from the code:

```js
export const FOREIGN_HOST_REFUSAL = "Blocked: this server answers only to … start Agent Canvas with --public.\n"; // 358 bytes
export const FOREIGN_HOST_UPGRADE_REFUSAL = "HTTP/1.1 403 Forbidden\r\n\r\n";
export function isRebindingSafeHost(hostHeader)   // string | undefined -> boolean
export function refuseForeignHost(res)            // 403; text/plain; charset=utf-8, no-store, Content-Length
```

`isRebindingSafeHost` parses `"http://" + host` with WHATWG `URL`. It refuses userinfo, a path, a query or a fragment.
It accepts `localhost`, a name ending `.localhost`, or anything `net.isIP` takes once brackets are stripped [read; run
on 16 values, §3].

| Listener | Checks when | Where | Refuses with |
|---|---|---|---|
| `scripts/static-server.mjs` | its own `applySessionKeyPolicy` keeps the key (`hostCheck = Boolean(policy.sessionApiKey)`); no flag | first statement of the request and upgrade handlers | the two constants |
| `scripts/ingress.mjs` | `--host-check`; no environment variable | the same | the same |
| Vite (`vite.config.ts`) | `VITE_SESSION_API_KEY` is set: `allowedHosts: []`, else `true` | Vite's own middleware and its HMR socket | Vite's 403 text |

Both Node servers print a line at start when the check is on [run]. Vite prints none.

**The seam that matters: the ingress hides `Host`.** The ingress proxies with `changeOrigin`, so the static server or
Vite behind it sees `127.0.0.1:<port>` and passes. `X-Forwarded-Host` reaches them, and nothing reads it [run]. Port
8000 is therefore protected only by the ingress's own flag, and the launcher must pass `--host-check` exactly when its
frontend's page carries the key.

- `getHostCheckArgs(config)` in `dev-with-automation.mjs` returns `["--host-check"]` when `launchFrontend &&
  launchAgentServer && !isPublic && isLoopbackBind(bindHost)`. That is the condition under which `startStaticFrontend`
  and `buildViteFrontendEnv` keep the key [read; its five cases run, §3].
- `dev-static.mjs` calls the same function. It has no `--public` and always starts the backends, so its flag follows
  the loopback bind, as its static server's key does [read].

**Who gets which listeners** [read unless marked]:

- The desktop app and `npx`: `main({ staticMode: true })`, so the ingress on 8000 and the static server on 3001. E12
  exercises the app [CI].
- `npm run dev`: the ingress, and Vite on 3001. `dev:minimal` (`dev-safe.mjs`): Vite alone, with the key when
  `VITE_BIND_HOST` is loopback.
- Docker: the static server alone, on `::`. Its page carries the key only with `AGENT_CANVAS_ALLOW_LAN_SESSION_KEY=true`.
  The image already copies `bind-host.mjs`, and the in-container `AUTOMATION_BASE_URL` defaults to `127.0.0.1`, which
  passes.
- `OH_CONVERSATION_RUNTIME=docker` (README Option 3) binds `0.0.0.0`, so there is no key and no check. Its
  `host.docker.internal` callbacks are untouched.

**deep-reasoning.** `get_with_host(url, host, timeout_s=10.0) -> tuple[int, str]` in `tests/desktop/app.py` is urllib
with the `Host` header set and the environment's proxies bypassed. E12's
`test_the_page_refuses_a_host_name_that_is_not_this_machine[ingress|frontend]` asks ports 8000 and 3001 [read; CI].

---

## 2 · Divergences from the design

### Reported by the Implementer, verified here

- **Vite's proxied WebSocket upgrades** (design §1.1, D6, §4).
  - Vite 8.0.16 checks `Host` in an HTTP middleware and in its HMR socket's `shouldHandle`. Its proxy's `upgrade`
    handler (`node_modules/vite/dist/node/chunks/node.js:17958`) has no check [read].
  - In my probe, Vite with `allowedHosts: []` handed a `/sockets` upgrade to the stub under every foreign name tried.
    The page got 403 and an HMR upgrade got 400 [run].
  - On the real stack, `evil.example:23001` got 101, then the agent-server's close 4001 "Authentication failed" at
    10.0 s [impl].
  - The editor prefix is proxied the same way (`ws: true`) when the launcher sets `VITE_VSCODE_*`. There, the editor's
    connection token is what refuses [read].
  - **Corrected wording** for §1.1 and D6: *Vite's check covers the page, modules, proxied HTTP routes and its HMR
    socket. It does not cover the WebSocket upgrades Vite proxies (`/sockets`, the editor prefix): those reach the
    agent-server or the editor under any `Host`, and are closed there without the key or the token.*
  - Reason: Vite has no host check on its proxy's upgrades, and the Conductor ruled out a plugin.
- **Vite's rule against `isRebindingSafeHost`** [run]:

  | `Host` | static server, ingress | Vite |
  |---|---|---|
  | `LOCALHOST:P`, `127.1:P` | pass | 403 |
  | `localhost:P/x`, `chrome-extension:abc` | 403 | 200, key in the page |
  | none (HTTP/1.0) | 403 | 200, key in the page |

  The other twelve values agree. Over HTTP/1.1, Node answers a missing `Host` with 400 on all three. A browser always
  sends `Host`, lowercase and canonical, never with a path or an extension scheme [read]. Reason: D6 takes Vite's own
  matcher as it is.
- **Text.**
  - The doc comments on the two constants and on `refuseForeignHost` are shorter than §3.1's. They drop "the tests
    compare with it" and the `mars-web-bridge.mjs` attribution.
  - `bind-host.mjs`'s header comment gains a sentence on rebinding.
  - The skill-guide bullet also names `isRebindingSafeHost`, `getHostCheckArgs` and "before routing".
  - The README sentence, the Vite comment and both `--help` texts are §3's [read]. The refusal is §4's [run].
  - D7 says each server announces the check, but Vite does not; §3 gave lines for the other two only.
- **Extra test rows.** The ingress's pass test adds `[::1]`. `get_with_host` bypasses environment proxies and has its
  own two-case test in `tests/desktop/test_app.py`. E12's ids are `ingress` and `frontend`.

### Reported only in `3531384`'s commit message

- **E12 has no `xfail(strict)` mark** (design §5.2).
  - Reason (the Conductor's): `ux-round`'s E12 runs against `ux-round-integration`, which carries the check, so a
    strict mark would fail it.
  - Consequence: `ux-round`'s `pins.toml` holds `dr-3` (`4355a36`) [read]. A `cross-repo` run there that does not
    override the Canvas commit fails both host tests until the pins move to `dr-4` [read].
  - The three runs since `3531384` were all dispatched with the override [CI].

### Not reported

- **E13 has no host test** (design §5.2, §6). `tests/desktop/test_e13.py` on `task-48-browser` has none [read]. The
  task row says E13's step is to be folded into `task-48-browser` later. Until then, no whole-stack test checks TASK-48's
  browser command.
- **Size** (design §8, which estimated ≈60 lines of code and ≈200 of tests, about 1 h at Gate C):

  | Part | Code | Tests |
  |---|---|---|
  | `bind-host.mjs` | +64/−1 | +28 |
  | `static-server.mjs` | +24/−1 | +160/−2 |
  | `ingress.mjs` | +29/−1 | +142/−2 |
  | the launchers | +23 | +16 |
  | `vite.config.ts` | +4/−1 | +27 |
  | README, skill guide | +2/−2 | — |
  | deep-reasoning | — | +83/−11 |
  | **Total** | **+146/−6** | **+456/−15** |

  Of the 144 lines added to `scripts/` and `vite.config.ts`, 32 are comments, 6 are blank and 8 are `--help` text. The
  tests grow where they spawn servers and write raw upgrades. At 300 lines an hour, Gate C reads in about 2 h.

---

## 3 · Proof

Nothing here costs money, and nothing calls a model.

- **The fork's tests touched by the commit** [run]: 5 files, 215 passed at `0d925ea`, in 60 s. Reproduce with
  `npx vitest run __tests__/scripts/{bind-host,vite-host-check,static-server,ingress,dev-with-automation}.test.ts`. The
  Vite test calls `vite.config.ts`'s factory itself, so §5.1's source-pin fallback was not needed.
- **The fork's gates** [impl]: lint, `build` and `build:lib` exit 0. `npm test` exited 1 after 1,926 s: 2 of 8,433
  failed, in `conversation-panel.test.tsx` and `automations-list-behavior.test.tsx`. Run alone at `0d925ea`, those two
  files pass, 105 of 105 [run]. There is no fork CI run, because the fork's CI runs on PRs.
- **The Implementer's real stack** [impl]: `dr-3` with this commit, in front of the `dr-2` agent-server, on ports 28080
  (ingress), 23001 (frontend) and 28000 (agent-server).
  - Static mode: every foreign name tried gets 403 on `/`, `/server_info`, `/api` and the `/sockets` upgrade, at the
    ingress and at the static server alike. A missing `Host` gets 403 too. Every local name gets 200 with the key, and
    101 on the socket. The agent-server itself answers any `Host`, as before.
  - Dynamic mode: the same at the ingress. Vite gives its 403 to the page, `/server_info` and `/api`, and 101 to the
    upgrade (§2).
  - Chromium loads both ports under `localhost` and `127.0.0.1` and opens the conversation's socket. Under
    `rebound.example` it gets the 403 page, no key global, 403 on its own `fetch`es, and a socket closed with 1006. Why
    the browser's socket closes with 1006 rather than with 4001 at 10 s is not established.
- **My probe** [run]. The script is not committed.
  - Setup: a recording stub backend, behind the fork's static server (with the key), an ingress with `--host-check`
    and one without, and Vite 8.0.16 with `allowedHosts: []` and the fork's `/api` and `/sockets` proxy shapes.
  - 16 `Host` values, each sent as a GET and as an upgrade. This produced §2's table, the refusal's headers and bytes,
    and the startup lines.
  - `X-Forwarded-Host: evil.example` under `Host: localhost` passes, and the stub receives it.
  - The ingress without `--host-check` serves the page with the key to `evil.example`, because the static server
    behind it sees `127.0.0.1`.
- **`cross-repo` 39220656317 and 39221995995** at `ux-round` `b283be2` [CI]. Each ran with Canvas `1a9e3c6`
  (`ux-round-integration`) and SDK `1f1a381` in place of the pins.
  - `desktop-e2e`: E12, 25 passed, both host tests included. `canvas-replay`: E6, 12 passed.
  - `1a9e3c6` merges `0d925ea`. Its TASK-64 files equal `0d925ea`'s, except `dev-with-automation.mjs`, where TASK-66's
    changes sit beside unchanged host-check lines [run, `git diff`].
  - The host tests also passed in 39218978270 at `b0fff97`. That run failed on an unrelated window-title step.
- **`ci` 39220648479** at `b283be2` is green [CI]. `get_with_host`'s own test passes locally, 2 of 2 [run].

---

## 4 · Not verified

- **The Docker image** is not built or run. §1's Docker claims are read from `docker/entrypoint.sh` and
  `docker/Dockerfile`.
- **Electron on macOS and Windows.** On Linux, the `.deb` ran in E12 [CI].
- **Vite through `react-router dev`.** I ran Vite directly with the fork's settings, not with the fork's config. That
  the fork's config yields `[]` is the unit test's claim [run], and the Implementer ran the real dynamic stack [impl].
- **Safari and `*.localhost`** (design §7 item 3): not tested.
- **The upstream PR's change to `mars-web-bridge.mjs`** (design §6) is not part of this build: the fork has no such
  file [run, `git ls-tree`].
