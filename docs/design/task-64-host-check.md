# TASK-64 · The launcher's page refuses other host names (DNS rebinding) — design

**TASK-64** · System Designer · design branch `design/task-64` in
[deep-reasoning](https://github.com/michaeltheologitis/deep-reasoning), cut from `main` at `9e8109e`; this file is
its only change. The code lands in the Canvas fork ([michaeltheologitis/OpenHands](https://github.com/michaeltheologitis/OpenHands)).

**There is no spec.** Michael, 2026-10-19: "Do them without the spec go with what you recommend". The scope comes
from TASK-48's spec, Q3 answer (a): a separate task, an upstream-shaped `Host` allowlist in the fork's
`static-server.mjs` and `ingress.mjs`, sharing Canvas tag `dr-4` with the UX round. So this doc also carries what a
spec would: what changes for a user (§1), what is out (§1.2), and the decisions that are costly to reverse (§2).
Where it departs from Q3 (a)'s wording: §2.1.

**Pinned against:** Canvas fork `dr-3` = `4355a36` (every Canvas `file:line`) · SDK fork `dr-2` = `34c540c` ·
deep-reasoning `main` `9e8109e` · upstream `OpenHands/OpenHands` `main` at `53ca2f6` (2026-10-18), for its MARS
bridge only · probes on Node 22.22.0, Vite 8.0.16 and httpxy 0.5.5 (the fork's lock).

**Revisions** (newest first):
- 2026-10-19 · v1 · first version.

**Where this file lives.** `docs/design/task-64-host-check.md`, on `design/task-64` only. At `9e8109e` pytest collects
`tests/` only (`testpaths`), ruff excludes `docs` (`extend-exclude`), the sdist excludes `docs/`, and the wheels
package `src/` only.

**Reading guide.** Gate B: §0 and §2, about 10 minutes. The Implementer: everything; §3 is the signatures, §4 the
refusal verbatim, §5 every test by name. The Conductor and the UX round: §6.

---

## 0 · Findings (measured 2026-10-19)

**The stack.** dr-3's `static-server.mjs` (with `--session-api-key`) and `ingress.mjs` (`--default` the static
server), each with the launcher's own route table (`dev-with-automation.mjs:912-922`), in front of the dr-2
agent-server. The agent-server ran from uv's cached build of `34c540c`, with `OH_APP_BACKEND_PUBLIC_URL` set as the
launcher sets it. The ports were not the defaults (28080, 23001, 28000), so as not to meet another session's stack;
nothing here depends on the port. Scripts and raw output are in the System Designer's scratchpad,
`task-64-design/measure-*.txt`.

- **F1 · Every listener that serves the page gives the key to any Host.**
  - `GET /` under `Host:` `localhost`, `127.0.0.1`, `[::1]`, `app.localhost`, `evil.example` and `127.0.0.1.nip.io`
    (each with its port) answered 200, with `window.__AGENT_CANVAS_SESSION_API_KEY__` set, on the ingress and on the
    static server alike.
  - Vite (dynamic mode: `npm run dev`, `dev:minimal`) does the same. The fork sets `allowedHosts: true`
    (`vite.config.ts:407`), and a minimal Vite 8.0.16 with that setting served the module holding
    `VITE_SESSION_API_KEY` under `Host: evil.example`.
- **F2 · Without the key, a rebound page reaches nothing useful, so the page is the only leak.**
  - The agent-server: every route in its OpenAPI, called without the key under `Host: evil.example`. 167 answered 401;
    `/`, `/alive`, `/health`, `/ready` and `/server_info` answered 200 (versions, usable tools, capabilities,
    `app_backend_ingress_url`); `/api/init` answered 404.
  - Its WebSockets authenticate on the first message (`sockets.py:131`). Without the key, through the ingress under a
    foreign Host, the socket closed with `4001 Authentication failed` at 10.0 s.
  - The Library bridge checks `Host` itself (SDK `canvas_extensions/bridge.py:296`). `POST
    /app-backends/dr-library/session` **with** the key, under `Host: evil.example`, answered `421 Canvas App request
    must use the configured ingress origin`, and so did its proxy. Its WebSocket checks `Host`, `Origin` and the
    cookie (`:481-482`), and the cookie is issued only to `127.0.0.1` (`:376`), so a rebound origin never holds one.
  - The automation backend wants the key or a Cloud `keycloak_auth` cookie (read in `openhands-automation` 1.16.0's
    `auth.py`; not started). The editor wants its connection token (read; it does not start outside Docker).
  - So the SDK fork needs no change for this task. The five open routes are an information leak (§7 item 1), not a
    task.
- **F3 · The ingress hides the browser's `Host` from what is behind it.**
  - An echo server behind the ingress saw `Host: 127.0.0.1:<its port>` (httpxy's `changeOrigin`,
    `proxy-utils.mjs:213`).
  - It also saw `X-Forwarded-Host: evil.example:…` on HTTP, and none on a WebSocket upgrade.
  - httpxy keeps a client's own `X-Forwarded-Host`, and a same-origin `fetch` from a rebound page may set one.
  - So **each listener a browser can reach checks `Host` itself, and nothing reads `X-Forwarded-Host`.**
- **F4 · "A loopback bind refuses foreign names" would break upstream's documented self-hosting, and miss its Docker
  quickstart.**
  - `docs/SELF_HOSTING.md:124, 187, 232` runs `npx @openhands/agent-canvas --public` on `127.0.0.1:8000` behind nginx
    with `proxy_set_header Host $host`, so the ingress sees `Host: canvas.example.com`.
  - `README.md:95-97`'s Docker quickstart injects the key on a `::` bind (`AGENT_CANVAS_ALLOW_LAN_SESSION_KEY=true`)
    and publishes it on host loopback, so rebinding reaches it as it reaches the app.
  - What the attack needs is the key in the page, not a loopback bind. So the condition is the key (D2).
- **F5 · Upstream already ships this check, privately.**
  - Upstream `main`'s new MARS bridge (`scripts/mars-web-bridge.mjs:193-238, 494-497, 536-537` at `53ca2f6`) refuses,
    on a loopback bind, a request whose `Host` hostname is neither a loopback name nor under `.localhost`. HTTP gets
    403 with `{"error":{"message":"cross-origin request refused"}}`; an upgrade gets `HTTP/1.1 403
    Forbidden\r\n\r\n`; the port is not compared.
  - Vite's own default (`allowedHosts: []`, measured on 8.0.16) admits `localhost`, `*.localhost` and every IP
    address on any port. Anything else gets `403 Blocked request. This host ("evil.example") is not allowed. …`.
  - This task takes that rule into `bind-host.mjs` and applies it wherever the key is.

---

## 1 · What changes for a user

**The rule** (the README's sentence, §3.6): *while a listener's page carries the session key, it answers only
requests addressed to `localhost`, a name under `.localhost`, or an IP address, on any port. Anything else gets a 403
that says why and names `--public`.*

| Who | Key in the page? | Today | After |
|---|---|---|---|
| The desktop app (Electron opens `http://localhost:8000`) | yes | key to any Host | the window unchanged; a rebound page gets 403 |
| TASK-48's browser command (opens `http://localhost:P`) | yes | the same | the same |
| `npx @openhands/agent-canvas`, `npm run dev`, `dev:static`, `dev:minimal` in local mode | yes | the same | the same. `ssh -L 9000:127.0.0.1:8000` still works (`Host: localhost:9000`) |
| The Docker quickstart (`-p 127.0.0.1:8000:8000`, the LAN opt-in) | yes | the same | the same: `localhost:8000` works, a rebound page gets 403 |
| The same opt-in, reached on the LAN by address (`192.168.1.5:8000`) | yes | works | works: IP addresses pass |
| The same opt-in, reached by a LAN name (`mybox.local`), against `README.md:144` | yes | works | **403** |
| Local mode behind a proxy or tunnel that keeps `Host` (nginx `$host`, Caddy, `tailscale serve`, ngrok without host rewrite) | yes | works, and gives the key to whoever reaches the proxy | **403**, naming `--public` |
| `--public` anywhere, SELF_HOSTING's nginx included | no | works | unchanged |
| `--host 0.0.0.0` or `OH_BIND_HOST`; `OH_CONVERSATION_RUNTIME=docker` (README Option 3); Helm | no | works | unchanged |

### 1.1 In scope

- **The listeners:** the ingress, the static server and Vite's dev server, the three that serve a page holding the
  key.
- **The routes behind them:** proxied `/api`, `/sockets` and `/server_info`, the editor prefix, and static files are
  refused too, because the check runs before routing.

### 1.2 Out of scope (each something someone could want)

- **An escape hatch** (`--allowed-host <name>`, like Vite's list). The setups it refuses are the ones that give the
  key to more than this machine, and `--public` is their path. A flag is cheap to add later and costly to remove. It
  is the first follow-up if upstream asks.
- **`Origin` checks** (a cross-site WebSocket or form post that carries a loopback `Host`). That is not rebinding: the
  browser keeps such a page in its own origin, so it cannot read the response. And every socket and API behind these
  listeners needs the key, the editor's token, or the bridge's cookie and `Origin` (F2).
- **A `Host` check in the agent-server on 18000.** Nothing there is open without the key (F2), and the bridge already
  checks.
- **The agent-server's five open routes** (F2): upstream SDK's design (§7 item 1).
- **The key on a LAN bind with the opt-in.** Anyone on that network can read it directly; that is upstream's
  documented trade.
- **Electron.** Nothing to change: its window is on `localhost`.

---

## 2 · Decisions

| # | Decision | Why | Rejected |
|---|---|---|---|
| D1 | **On by default, not a setting.** No `config/defaults.json` key, so nothing in `patch_defaults`, `FORK_NULL_KEYS` or checks 5 and 5b. The fork commit is upstream-shaped and not `[fork only]`. | It fixes a bug for every user of the launcher, upstream's included, and upstream already applies the same rule to its own bridge (F5). The "null upstream, our build turns it on" pattern is for features of ours (`agent.lockedProfile`, `branding.appTitle`). For a generic change the fork rule is "shaped as an upstream PR" (`docs/research/2026-10-02-frontend-and-hosting/README.md`, "Fork rules"). A setting null upstream would leave upstream's users, and any build without our patch, open. It would also cost a defaults key, a `FORK_NULL_KEYS` entry, a check and a seam with the UX round and TASK-66, for a behaviour nobody should turn off. Upstream would likely take the PR as is: it cites `mars-web-bridge.mjs`, and moves that file's private `isForeignHost` onto the new predicate. | A `security.hostCheck` key, null upstream (above). |
| D2 | **The condition: the listener's page carries the session key.** The static server derives it from its own `applySessionKeyPolicy` result, with no flag. Vite uses `VITE_SESSION_API_KEY` being set. The ingress cannot know, so it takes `--host-check`, which the launchers pass exactly when the frontend they start gets the key. | The key in the page is what a rebound page steals (F1, F2). A loopback bind is neither necessary (the Docker quickstart) nor sufficient (`--public` behind nginx) (F4). Deriving it in the static server covers every caller without a flag to forget. | A loopback bind (F4). Every request (breaks LAN and public deployments). A flag on the static server too (a caller could forget it). |
| D3 | **The allowlist: the hostname of `Host` is `localhost`, ends in `.localhost`, or is an IP address (v4 or v6), on any port.** It is parsed as WHATWG URL parses `"http://" + host`, so `LOCALHOST`, `127.1` and `[::1]` normalise. Refused: no `Host`, an unparsable one, userinfo (`a@localhost`), a path, and every other name (`localhost.`, `localhost.evil.example`, `127.0.0.1.nip.io`). | Rebinding needs a DNS name that the attacker's server answers. An IP address never goes to DNS. Browsers resolve `.localhost` names to loopback, and public DNS has no `.localhost` zone (RFC 6761). The port is not compared: tunnels and proxies change it, TASK-48's `--port N` then needs nothing, and what is foreign is the attacker's name, not its port. IP addresses pass so the documented LAN opt-in keeps working by address. It is Vite's default, so dynamic and static modes agree (F5). | Q3 (a)'s `localhost`, `127.0.0.1`, `[::1]` exactly: it refuses `127.0.0.2`, `*.localhost` and LAN addresses for no safety gain. Upstream's bridge, loopback addresses only: the same, and it checks only loopback binds, where the two agree. The served port only: breaks tunnels and `--port`. |
| D4 | **The refusal: 403, `text/plain`, one fixed text that echoes nothing (§4).** An upgrade gets upstream's bytes, `HTTP/1.1 403 Forbidden\r\n\r\n`, and the socket ends. The check is the first statement of both handlers. | Upstream's bridge and Vite both answer 403 for this check. A fixed text needs no escaping. Running first means proxied routes and static files are refused with the page. | 421 (the SDK bridge's answer, right in principle, but upstream Canvas says 403). Echoing the name, as Vite does: one more branch, and nothing gained. |
| D5 | **`Host` only: never `X-Forwarded-Host`, never `Origin`.** | F3: the ingress hides `Host` and keeps a client's `X-Forwarded-Host`. The browser sets `Host` from the URL, a page cannot change it, and a rebound socket carries the rebound name in `Host` like any other request. | Trusting `X-Forwarded-Host` (a rebound page can set it). |
| D6 | **Vite is in.** `allowedHosts: VITE_SESSION_API_KEY ? [] : true`: Vite's own check, exactly when its page carries the key. | Otherwise `npm run dev` and `dev:minimal` keep F1 on 3001, and an upstream reviewer would ask about it. It is one line; its refusal is Vite's own text. | Leaving `allowedHosts: true` (the same leak in dynamic mode). |
| D7 | **Each server says at start that the check is on.** | A user behind a proxy who gets a 403 looks at the terminal. | A log line per refusal (noise under attack). |

### 2.1 Where this departs from Q3 (a)'s wording

- **The allowlist is wider** (D3): `*.localhost`, all of 127.0.0.0/8, and every IP address.
- **The check is conditional** (D2), not on every request, since the nginx recipe and LAN binds would break otherwise
  (F4).
- **Vite is included** (D6), and the launchers pass the ingress one flag. Q3 named only the two scripts.
- **The size** is about 60 lines of code and 200 of tests, not about 40 in all (§8).

---

## 3 · Signatures (Canvas fork; branch `fix/launcher-host-check`, cut from `dr-3`)

### 3.1 `scripts/bind-host.mjs`: the new surface

```js
import { isIP } from "node:net";

/** What a refused request reads (§4, verbatim); the tests compare with it. */
export const FOREIGN_HOST_REFUSAL = "Blocked: this server answers only to …\n";

/** A refused WebSocket upgrade's whole response: upstream mars-web-bridge.mjs's bytes. */
export const FOREIGN_HOST_UPGRADE_REFUSAL = "HTTP/1.1 403 Forbidden\r\n\r\n";

/**
 * Whether a request's Host header cannot have come from a DNS-rebound page: its hostname
 * is `localhost`, a name under `.localhost`, or an IP address, on any port. False for a
 * missing or unparsable header, or one with userinfo or a path. Parsed as WHATWG URL does,
 * so `LOCALHOST`, `127.1` and `[::1]` pass.
 * @param {string | undefined} hostHeader  `req.headers.host`
 * @returns {boolean}
 */
export function isRebindingSafeHost(hostHeader) {}

/**
 * Answer 403 with FOREIGN_HOST_REFUSAL: `Content-Type: text/plain; charset=utf-8`,
 * `Cache-Control: no-store`, `Content-Length`. The caller returns after it.
 * @param {import("node:http").ServerResponse} res
 */
export function refuseForeignHost(res) {}
```

### 3.2 `scripts/static-server.mjs`

- `startStaticServer(config)`: its signature is unchanged and `config` gains nothing. After `policy` (`:661`):
  `const hostCheck = Boolean(policy.sessionApiKey);`.
- The request handler (`:683`), first statement:
  `if (hostCheck && !isRebindingSafeHost(req.headers.host)) { refuseForeignHost(res); return; }`.
- The upgrade handler (`:722`), first statement:
  `if (hostCheck && !isRebindingSafeHost(req.headers.host)) { socket.end(FOREIGN_HOST_UPGRADE_REFUSAL); return; }`.
- The startup listing, before `* (default)` (`:755`), when `hostCheck`:
  `  Host check: localhost, *.localhost and IP addresses only (the page carries the session key)`.
- `--help`, under `--session-api-key`: "Requests under a host name other than localhost, a name under .localhost or
  an IP address then get 403 (DNS rebinding)."

### 3.3 `scripts/ingress.mjs`

- `parseArgs()`: `hostCheck: false` in the defaults; `case "--host-check": config.hostCheck = true; break;`.
- `buildConfig(args, env)`: `hostCheck: Boolean(args.hostCheck)`. No environment variable, as for
  `--no-referrer-prefix`.
- `startIngress(config)`: the two guards of §3.2 on `config.hostCheck`, first in the request handler (`:180`) and the
  upgrade handler (`:210`).
- A banner line when it is on, padded like the others: `║  Host check: localhost, *.localhost, IP addresses only`.
- `--help`: `--host-check   Answer only requests whose Host is localhost, a name under .localhost or an IP address (any
  port); 403 otherwise. For an ingress in front of a page that carries the session key (DNS rebinding).`

### 3.4 `scripts/dev-with-automation.mjs` and `scripts/dev-static.mjs`

```js
/**
 * `["--host-check"]` when the frontend this launch starts puts the session key in its page:
 * local mode, with the agent-server and a frontend started, on a loopback bind. These are
 * the cases where startStaticFrontend and buildViteFrontendEnv keep the key; the launcher
 * never passes --allow-lan-session-key, so off loopback the page has no key. Otherwise [].
 * @param {{ launchFrontend: boolean, launchAgentServer: boolean, isPublic: boolean, bindHost: string }} config
 * @returns {string[]}
 */
export function getHostCheckArgs(config) {}
```

- It joins the `export {}` list (`:2153`).
- `startIngress` (`dev-with-automation.mjs:1478`) adds `...getHostCheckArgs(config)` after
  `...getNoReferrerPrefixArgs(config)` (`:1499`).
- `dev-static.mjs` imports it beside `getNoReferrerPrefixArgs` (`:62-73`), and its `startIngress` (`:473`) adds it at
  the same place (`:495`).

### 3.5 `vite.config.ts`

- Destructure `VITE_SESSION_API_KEY` from `loadEnv` (`:103-119`).
- `server.allowedHosts` (`:407`) becomes `VITE_SESSION_API_KEY ? [] : true`, with a one-line comment: "Vite's own Host
  check while the page carries the key (DNS rebinding); open otherwise, for LAN hosts and tunnels."

### 3.6 Docs (the fork's AGENTS.md: "update the owning skill whenever an invariant changes")

- `README.md:142`, appended to the loopback paragraph: "While the page carries that key, the listeners also answer
  only requests addressed to `localhost`, a name under `.localhost`, or an IP address, so a web page that points its
  own domain at 127.0.0.1 cannot read it. To reach the UI under another name (a reverse proxy, a tunnel), use
  `--public`."
- `.agents/skills/local-stack-runtime/references/guide.md:103`, the Security bullet: the rule, the three listeners,
  and "check `Host` only: the ingress rewrites it and keeps a client's `X-Forwarded-Host`".

**The commit:** `fix(launcher): refuse other host names while the page carries the session key`. Its body cites F1,
F4 and F5, and it carries no `[fork only]`.

---

## 4 · The refusal, verbatim

The ingress and the static server, over HTTP:

```text
HTTP/1.1 403 Forbidden
Content-Type: text/plain; charset=utf-8
Cache-Control: no-store
Content-Length: <bytes>

Blocked: this server answers only to localhost, names under .localhost and IP addresses, because its page carries the session key. A request under another host name may come from a web page that has pointed its own domain at this machine (DNS rebinding). To reach it under another name, such as a reverse proxy or a tunnel, start Agent Canvas with --public.
```

- `FOREIGN_HOST_REFUSAL` is the body's one line, followed by `\n`.
- A WebSocket upgrade gets `HTTP/1.1 403 Forbidden\r\n\r\n`, then the socket ends.
- Vite, in dynamic mode, answers with its own 403 text (F5).

---

## 5 · Tests

### 5.1 Canvas fork (vitest, in the files that already test each script)

**Setting `Host` in a test:** use `node:http`'s `request` with `headers: { host }`. Node's `fetch` drops a `Host`
header (measured: it sent `127.0.0.1:<port>`).

`__tests__/scripts/bind-host.test.ts`:
- `it.each` `accepts %s as a host a rebound page cannot send`: `localhost:8000`, `LOCALHOST:8000`, `localhost`,
  `127.0.0.1:9000`, `127.0.0.2:8000`, `127.1:8000`, `[::1]:8000`, `app.localhost:8000`, `192.168.1.5:8000`.
- `it.each` `refuses %s`: `evil.example:8000`, `localhost.evil.example:8000`, `127.0.0.1.nip.io:8000`,
  `localhost.:8000`, `evil@localhost:8000`, `localhost:8000/x`, `""`, `undefined`.

`__tests__/scripts/static-server.test.ts`, `describe("host check")`:
- `it.each(["/", "/conversations/abc", "/api/anything"])` `refuses %s under another host name while the page carries
  the key`. Set-up: `sessionApiKey` set, and a backend stub routed at `/api` that would answer 200. Under `Host:
  evil.example:<port>`: 403, the body is `FOREIGN_HOST_REFUSAL`, it holds no key, and the stub saw no request.
- `serves the page with the key under localhost, a .localhost name and an IP address, on any port`: `Host`
  `localhost:1`, `app.localhost:<port>` and `127.0.0.1:<port>` all get 200 with the key.
- `refuses a WebSocket upgrade under another host name`: a raw socket upgrade on a routed prefix. The response starts
  `HTTP/1.1 403 Forbidden`, and the stub saw no upgrade.
- `it.each` `answers any host name when the page carries no key (%s)`: `authRequired`, and `host: "0.0.0.0"` with a
  key and no opt-in. Both give 200 under `evil.example`.
- `checks a LAN bind whose page carries the key by --allow-lan-session-key`: `host: "0.0.0.0"`, a key, and
  `allowLanSessionKey`. `evil.example` gets 403; `192.168.1.5:<port>` gets 200.

`__tests__/scripts/ingress.test.ts`, `describe("ingress --host-check")`. Spawned like `--no-referrer-prefix`'s, with a
stub as the default backend and at `/api`:
- `refuses another host name before routing`: `/` and `/api/x` get 403 with `FOREIGN_HOST_REFUSAL`, and the stub saw
  nothing.
- `passes localhost, a .localhost name and an IP address through, on any port`.
- `refuses a WebSocket upgrade under another host name`.
- `answers any host name without --host-check`: a second ingress, one case.

`__tests__/scripts/dev-with-automation.test.ts`:
- `it.each` `asks the ingress for the host check only when its frontend's page carries the key (%s)`, through
  `buildConfig(args, envWithIsolatedKeyPath(…))` as the file's tests do. `{}` gives `["--host-check"]`. `{ public:
  true }` (with `LOCAL_BACKEND_API_KEY`), `{ host: "0.0.0.0" }`, `{ backendOnly: true }` and `{ frontendOnly: true }`
  each give `[]`.

`__tests__/scripts/vite-host-check.test.ts` (new):
- Call `vite.config.ts`'s factory under `vi.stubEnv`. With `VITE_SESSION_API_KEY` set, `server.allowedHosts` is `[]`;
  unset, it is `true`.
- If the factory cannot run under vitest (its plugins), fall back to a source pin like the one
  `vscode-base-path-opt-in.test.ts` already keeps on `vite.config.ts`, and say so in the PR.

The fork's gates stay `npm run lint`, `npm test`, `npm run build` and `npm run build:lib`.

### 5.2 deep-reasoning

- **`tests/desktop/app.py`:** `get_with_host(url: str, host: str, timeout_s: float = 10.0) -> tuple[int, str]`. It is
  urllib with the `Host` header set (measured: urllib sends it as given); an `HTTPError` gives its code and body. The
  helper is born in `app.py`, where TASK-48 moves E12's helpers.
- **E12**, after `test_the_first_launch_installs_everything_and_opens_the_window`:
  - `test_the_page_refuses_a_host_name_that_is_not_this_machine`, parametrized `[8000, 3001]`.
  - `Host: rebound.example:<port>` gets 403, with `app.session_key` absent from the body; `Host: localhost:<port>`
    gets 200, with the key present.
  - It is marked `xfail(strict=True, reason="Canvas dr-3 answers any Host name; TASK-64 ships in dr-4")` while
    `desktop/pins.toml` pins `dr-3`. The commit that pins `dr-4` drops the mark: without that, the test passes and the
    strict mark fails it.
- **E13 (TASK-48):** the same test, on the ingress port only, under the same rule for its mark. The mark is there if
  TASK-48 lands before `dr-4` is pinned, and absent after.
- Both assert the status and the key, never the fork's sentence, so a reworded refusal needs no edit here.

---

## 6 · Seams

- **Canvas `dr-4`.**
  - `fix/launcher-host-check` (from `dr-3`) merges into `deep-reasoning` at the UX round's §8 step 2, before its
    wiring commit and the tag. `dr-4` then carries it beside `feat/agent-lock`, `feat/app-title`,
    `fix/subagent-costs-on-by-default`, and TASK-66's and TASK-41's branches.
  - No file overlap with the three UX branches (`git diff --stat dr-3...<branch>`): they touch `src/`,
    `config/defaults.json`, `specs/` and `__tests__/`, but not `__tests__/scripts/`, `scripts/`, `vite.config.ts` or
    the README.
  - TASK-66 changes the launcher's `uvx` starts in `dev-safe.mjs` and `dev-with-automation.mjs` (its design was not
    pushed when this was written). `dev-with-automation.mjs` is the only shared file, in different functions, so
    whichever merges second rebases textually.
  - TASK-41 (a replay-spec race): no overlap expected (not read).
- **deep-reasoning.**
  - `patch_defaults`, `FORK_NULL_KEYS`, checks 5 and 5b, and the rest of `check_pins` are untouched (D1).
  - The pin bump to `dr-4` (the UX round's §8 step 3) is where E12's mark goes. E12 is then the gate that `dr-4`
    carries the check.
- **TASK-48.**
  - `--port N` needs nothing (D3: any port).
  - `web.mjs` probes `http://127.0.0.1:P/server_info` and opens `http://localhost:P`, and both pass.
  - Its W8 removes `OH_BIND_HOST`, so its stack is always a loopback bind with the key, and always checked.
  - E13 gains one test (§5.2).
- **Embedders of `main()`.** One that sets `automationApiHost` to a name would have its automation callbacks refused
  in local mode. None in the tree does (Electron and `bin/agent-canvas.mjs` do not), and `AUTOMATION_BASE_URL`
  defaults to `localhost`.
- **Upstream.**
  - The upstream PR also makes `mars-web-bridge.mjs`'s `isForeignHost` call `isRebindingSafeHost`, keeping its
    loopback-bind condition.
  - Worth one line in that PR: upstream's bridge refuses SELF_HOSTING's nginx `Host` on `/mars/*` today. That is
    upstream's to decide.

---

## 7 · Findings beyond the launcher, and what I was unsure about

1. **The agent-server answers five routes without the key** (`/`, `/alive`, `/health`, `/ready`, `/server_info`), so a
   rebound page on 18000 can read versions, tools and capabilities. That is upstream SDK's design; no task proposed.
2. **No escape hatch** (§1.2). A local-mode user behind a private tunnel (a tailnet) must switch to `--public`. If
   upstream asks, `--allowed-host` is the follow-up.
3. **Safari and `*.localhost`.** Safari may ask DNS for such names. That is harmless for safety, since there is no
   public `.localhost` zone, so allowing the names costs nothing.
4. **`Host: 0.0.0.0:8000` passes** (an IP address). A page that opens `http://0.0.0.0:8000` stays in that origin and
   cannot read it from its own; current Chrome blocks the address anyway.
5. **Measured with the launcher's servers and routes, not through `main()`.** E12 and E13 are the whole-stack checks.
   The agent-server ran from uv's cached build of `34c540c`, because one wheel was missing from the cache offline.
6. **Whether vitest can call `vite.config.ts`'s factory** (§5.1 names the fallback).
7. **The refusal is English only**, like every launcher message.

---

## 8 · Size

| Part | Code | Tests |
|---|---|---|
| `bind-host.mjs` | ≈ 25 | ≈ 25 |
| `static-server.mjs` | ≈ 8 | ≈ 60 |
| `ingress.mjs` | ≈ 12 | ≈ 50 |
| The launchers (`getHostCheckArgs`, two call sites) | ≈ 10 | ≈ 15 |
| `vite.config.ts` | ≈ 3 | ≈ 15 |
| README, the skill guide | ≈ 4 | — |
| deep-reasoning (`app.py`, E12, E13) | — | ≈ 35 |
| **Total** | **≈ 60** | **≈ 200**, about 1 h at Gate C |
