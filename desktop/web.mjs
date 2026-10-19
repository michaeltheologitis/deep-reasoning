// deep-reasoning: the browser version's entry (TASK-48 §3.2), shipped as the tarball's bin/deep-reasoning.mjs.
// It checks Node, uv and git, cleans the environment, takes the ports, then calls the Canvas fork's launcher
// as the desktop app's Electron main does. Node built-ins only: the tarball bundles only the launcher's own
// two packages. It runs only as the main module, so tests can import its pure parts.
import { spawn, spawnSync } from "node:child_process";
import { readFileSync, realpathSync } from "node:fs";
import { createServer } from "node:net";
import process from "node:process";
import { setTimeout as delay } from "node:timers/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import { parseArgs } from "node:util";

/** electron/main.mjs's main() call at the Canvas pin, but onServiceLog (the splash). */
export const ELECTRON_OPTIONS = Object.freeze({
  bannerTitle: "OpenHands Agent Canvas",
  staticMode: true,
  mode: "agent-canvas",
  isPublic: false,
  skipNpmCheck: true,
  agentServerReadyTimeoutMs: 10 * 60_000,
});
export const MINIMUM = Object.freeze({ node: "22.12.0", uv: "0.8.17" });
export const INGRESS_PORT = 8000; // the launcher's default --port
export const FRONTEND_PORT = 3001; // the launcher's default OH_CANVAS_SAFE_VITE_PORT
export const REMOVED_PREFIXES = Object.freeze(["OH_", "VITE_", "AUTOMATION_", "INGRESS_", "OPENHANDS_", "POSTHOG_"]);
export const REMOVED_NAMES = Object.freeze([
  "PORT",
  "LOCAL_BACKEND_API_KEY",
  "SESSION_API_KEY",
  "AGENT_SERVER_URL",
  "PYTHONPATH",
  "PYTHONHOME",
  "VIRTUAL_ENV",
  "UV_PYTHON",
  "NODE_OPTIONS",
  "NODE_PATH",
]);
export const EXIT = Object.freeze({ usage: 2, running: 20, port: 21, needs: 22, start: 24 });
export const READY_WAIT_MS = 60_000; // Electron's wait for /server_info once main() returns
const OPTIONS = Object.freeze({ port: { type: "string" }, "no-open": { type: "boolean" } });
const MOVABLE = Object.freeze([
  ["frontend", "OH_CANVAS_SAFE_VITE_PORT"],
  ["automation", "OH_CANVAS_SAFE_AUTOMATION_PORT"],
]);
const SETUP_EXPLAINED = Object.freeze({ lowest: 10, highest: 19 }); // dr-app's own exit codes
const POLL_MS = 500;

/** Every sentence the entry prints, verbatim from TASK-48 §5.2. */
export const texts = Object.freeze({
  ready_line: (version, node, uv, git) => `Deep Reasoning ${version} · Node ${node} ✓ · uv ${uv} ✓ · git ${git} ✓`,
  left_out: (names) => `Left out of the environment, as the app runs without them: ${names.join(", ")}`,
  already_running: (port) =>
    `✗ Deep Reasoning is already running on this computer: port ${port} is in use (the app, another terminal, ` +
    "or an Agent Canvas). Stop it, then run this again. Nothing was changed.",
  started_elsewhere:
    "✗ Deep Reasoning was started elsewhere while this one was starting (the app, or another terminal), so " +
    "this one stopped. Use that one, or stop it and run this again.",
  port_taken: (port, free) =>
    `✗ Port ${port} is in use by another program. Start Deep Reasoning on another: add --port ${free} to the command.`,
  node_too_old: (found) =>
    `✗ Deep Reasoning needs Node 22.12 or later, and this is ${found}. Install it from https://nodejs.org, then ` +
    "run the same command.",
  NO_UV:
    "✗ uv was not found on PATH. Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh  then open a " +
    "new terminal and run the same command.",
  uv_too_old: (found) =>
    `✗ Deep Reasoning needs uv 0.8.17 or later, and this is ${found}. Update it (uv self update, or the way you ` +
    "installed it), then run the same command.",
  NO_GIT:
    "✗ git was not found: Deep Reasoning installs deep_reasoner with it. On macOS run xcode-select --install; on " +
    "Linux install git. Then run the same command.",
  setup_stopped_before: (code) =>
    `✗ Setup stopped before anything started (exit ${code}): its last line above says why.`,
  setup_stopped_after: (code) =>
    `✗ Setup stopped once the agent-server was up (exit ${code}), so everything was stopped: its last line ` +
    "above says why.",
  SETUP_TIMED_OUT:
    "✗ Setup was still running after 15 minutes, so it was stopped. Run the same command again: it goes on from " +
    "what it already downloaded.",
  setup_killed: (signal) => `✗ Setup was stopped by ${signal} before Deep Reasoning started.`,
  NOT_READY:
    "✗ The agent-server did not answer within 10 minutes, so everything was stopped. A first start downloads " +
    "Python and its packages: check that this computer is online, then run the same command again.",
  could_not_start: (firstLine) => `✗ Deep Reasoning could not start: ${firstLine}`,
  running_opened: (url) => `Deep Reasoning is running at ${url}, opened in your browser. Ctrl+C stops it.`,
  running: (url) => `Deep Reasoning is running at ${url}: open it in your browser. Ctrl+C stops it.`,
  usage: (what) => `✗ ${what}. The options are --port N and --no-open.`,
});

export class UsageError extends Error {}

/** {port: number | null, open: boolean}. Throws UsageError(what) for texts.usage. */
export function parseCommandLine(argv, { agentServerPort }) {
  const { tokens } = parseArgs({ args: argv, options: OPTIONS, strict: false, allowPositionals: true, tokens: true });
  const parsed = { port: null, open: true };
  for (const token of tokens) {
    if (token.kind === "option-terminator") throw new UsageError("Unknown option --");
    if (token.kind === "positional") throw new UsageError(`Unknown option ${token.value}`);
    if (token.name === "no-open" && token.value === undefined) {
      parsed.open = false;
    } else if (token.name === "port") {
      parsed.port = portOption(token.value, agentServerPort);
    } else {
      throw new UsageError(`Unknown option ${token.rawName}`);
    }
  }
  return parsed;
}

function portOption(value, agentServerPort) {
  const port = /^\d+$/.test(value ?? "") ? Number(value) : NaN;
  if (!(port >= 1 && port <= 65535)) throw new UsageError("--port needs a number from 1 to 65535");
  if (port === agentServerPort) {
    throw new UsageError(`--port cannot be ${agentServerPort}: Deep Reasoning's agent-server uses it`);
  }
  return port;
}

/** Deletes the variables a terminal may hold and the app never sees from env, in place, and sets
 *  DO_NOT_TRACK=1; the deleted names, sorted. */
export function cleanEnvironment(env) {
  const removed = Object.keys(env).filter(
    (name) => REMOVED_NAMES.includes(name) || REMOVED_PREFIXES.some((prefix) => name.startsWith(prefix)),
  );
  for (const name of removed) delete env[name];
  env.DO_NOT_TRACK = "1";
  return removed.sort();
}

/** "22.12.0" ≥ "22.9.1"; a leading "v" and anything after the third number ignored. */
export function versionAtLeast(found, minimum) {
  const numbers = (version) => /^v?(\d+)\.(\d+)\.(\d+)/.exec(version)?.slice(1).map(Number);
  const have = numbers(found);
  const want = numbers(minimum);
  if (!have) return false;
  const first = have.findIndex((part, index) => part !== want[index]);
  return first === -1 || have[first] > want[first];
}

/** The sentences for what is missing or too old; empty when all is well.
 *  found: {node: string, uv: string | null, uvx: boolean, git: string | null} */
export function requirementProblems(found) {
  const problems = [];
  if (!versionAtLeast(found.node, MINIMUM.node)) problems.push(texts.node_too_old(found.node));
  if (found.uv === null || !found.uvx) problems.push(texts.NO_UV);
  else if (!versionAtLeast(found.uv, MINIMUM.uv)) problems.push(texts.uv_too_old(found.uv));
  if (found.git === null) problems.push(texts.NO_GIT);
  return problems;
}

/** The second word of `command --version`'s first line ("uv 0.8.17 (…)", "git version 2.43.0" read as
 *  its last word), or null when it is missing or fails. */
function versionOf(command, env) {
  const done = spawnSync(command, ["--version"], { env, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] });
  if (done.error || done.status !== 0) return null;
  const words = done.stdout.split("\n")[0].trim().split(/\s+/);
  return command === "git" ? words.at(-1) : (words[1] ?? null);
}

function requirements(env) {
  return {
    node: process.versions.node,
    uv: versionOf("uv", env),
    uvx: versionOf("uvx", env) !== null,
    git: versionOf("git", env),
  };
}

/** Whether 127.0.0.1:port can be bound now (bound, then closed), as the launcher probes. */
export async function portIsFree(port) {
  return new Promise((resolve) => {
    const server = createServer();
    server.once("error", () => resolve(false));
    server.listen(port, "127.0.0.1", () => server.close(() => resolve(true)));
  });
}

/** A port the OS hands out on 127.0.0.1 (bound to 0, then closed). */
export async function freePort() {
  return new Promise((resolve, reject) => {
    const server = createServer();
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const { port } = server.address();
      server.close(() => resolve(port));
    });
  });
}

/** {ingress, frontend, automation, moved: {variable: port}} | {refusal: {line, code}}. The agent-server's port
 *  is the lock, then the page's; the frontend's and automation's move when busy or equal to the page's, through
 *  OH_CANVAS_SAFE_VITE_PORT and OH_CANVAS_SAFE_AUTOMATION_PORT. */
export async function choosePorts({ agentServer, ingress, frontend, automation }) {
  if (!(await portIsFree(agentServer))) {
    return { refusal: { line: texts.already_running(agentServer), code: EXIT.running } };
  }
  if (!(await portIsFree(ingress))) {
    return { refusal: { line: texts.port_taken(ingress, await freePort()), code: EXIT.port } };
  }
  const chosen = { ingress, frontend, automation, moved: {} };
  const taken = new Set([agentServer, ingress]);
  for (const [name, variable] of MOVABLE) {
    if (taken.has(chosen[name]) || !(await portIsFree(chosen[name]))) {
      let port;
      do port = await freePort();
      while (taken.has(port));
      chosen[name] = port;
      chosen.moved[variable] = port;
    }
    taken.add(chosen[name]);
  }
  return chosen;
}

/** {line, code} for a rejection of main(): a SetupCommandError by its phase, reason and exitCode (setup's own
 *  10–19 pass through); anything else by agentServerHeldNow, then its first line. */
export function failure(error, { agentServerHeldNow }) {
  if (error?.name === "SetupCommandError") {
    const { phase, reason, exitCode, signal } = error;
    const explained = reason === "exit" && exitCode >= SETUP_EXPLAINED.lowest && exitCode <= SETUP_EXPLAINED.highest;
    const code = explained ? exitCode : EXIT.start;
    if (reason === "timeout") return { line: texts.SETUP_TIMED_OUT, code };
    if (reason === "signal") return { line: texts.setup_killed(signal), code };
    if (reason === "exit") {
      const stopped = phase === "after-ready" ? texts.setup_stopped_after : texts.setup_stopped_before;
      return { line: stopped(exitCode), code };
    }
  }
  if (agentServerHeldNow) return { line: texts.started_elsewhere, code: EXIT.running };
  const firstLine = String(error?.message ?? error).split("\n")[0];
  return { line: texts.could_not_start(firstLine), code: EXIT.start };
}

/** "open", "xdg-open", or null where a session cannot show a browser (SSH, or Linux without a display). */
export function opener(platform, env) {
  if (env.SSH_CONNECTION || env.SSH_TTY) return null;
  if (platform === "darwin") return "open";
  if (platform === "linux" && (env.DISPLAY || env.WAYLAND_DISPLAY)) return "xdg-open";
  return null;
}

/** The entry: parse, check, clean, ports, the launcher's main(), then wait for the page and open it. Returns an
 *  exit code when it stops before the launcher; once the launcher runs, its services keep Node alive. */
export async function run(argv = process.argv.slice(2), env = process.env) {
  const read = (path) => JSON.parse(readFileSync(new URL(path, import.meta.url), "utf8"));
  const { version } = read("../package.json");
  const { ports } = read("../config/defaults.json");
  let options;
  try {
    options = parseCommandLine(argv, { agentServerPort: ports.agentServer });
  } catch (error) {
    if (!(error instanceof UsageError)) throw error;
    say(texts.usage(error.message));
    return EXIT.usage;
  }

  const found = requirements(env);
  const problems = requirementProblems(found);
  if (problems.length > 0) {
    problems.forEach(say);
    return EXIT.needs;
  }
  say(texts.ready_line(version, found.node, found.uv, found.git));
  const removed = cleanEnvironment(env);
  if (removed.length > 0) say(texts.left_out(removed));

  const chosen = await choosePorts({
    agentServer: ports.agentServer,
    ingress: options.port ?? INGRESS_PORT,
    frontend: FRONTEND_PORT,
    automation: ports.automation,
  });
  if (chosen.refusal) {
    say(chosen.refusal.line);
    return chosen.refusal.code;
  }
  for (const [variable, port] of Object.entries(chosen.moved)) env[variable] = String(port);

  // The launcher reads its flags from process.argv and exits 0 from its own shutdown; a failure chosen here
  // outlives that exit.
  process.argv = [process.argv[0], process.argv[1], "--port", String(chosen.ingress)];
  let failed = null;
  process.on("exit", () => {
    if (failed !== null) process.exitCode = failed;
  });
  const stopEverything = (line) => {
    say(line);
    failed = EXIT.start;
    process.kill(process.pid, "SIGTERM");
  };
  const { main } = await import(new URL("../scripts/dev-with-automation.mjs", import.meta.url));
  let started;
  try {
    started = await main({ ...ELECTRON_OPTIONS, staticDir: fileURLToPath(new URL("../build", import.meta.url)) });
  } catch (error) {
    const { line, code } = failure(error, { agentServerHeldNow: !(await portIsFree(ports.agentServer)) });
    say(line);
    failed = code;
    process.exit(code);
  }
  if (started?.agentServerReady === false) return stopEverything(texts.NOT_READY);
  if (!(await answers(`http://127.0.0.1:${chosen.ingress}/server_info`, READY_WAIT_MS))) {
    return stopEverything(texts.NOT_READY);
  }

  const url = `http://localhost:${chosen.ingress}`;
  const command = options.open ? opener(process.platform, env) : null;
  if (command === null) return say(texts.running(url));
  spawn(command, [url], { detached: true, stdio: "ignore" }).on("error", () => {}).unref();
  say(texts.running_opened(url));
}

/** Whether url answers 200 within timeoutMs. */
async function answers(url, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      if ((await fetch(url, { signal: AbortSignal.timeout(5000) })).ok) return true;
    } catch {
      // not up yet
    }
    await delay(POLL_MS);
  }
  return false;
}

function say(line) {
  console.log(line);
}

const isMain = process.argv[1] && import.meta.url === pathToFileURL(realpathSync(process.argv[1])).href;
if (isMain) {
  run().then(
    (code) => {
      if (code !== undefined) process.exitCode = code;
    },
    (error) => {
      console.error(error);
      process.exitCode = 1;
    },
  );
}
