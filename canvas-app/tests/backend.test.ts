import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  BACKEND_PATH,
  BACKEND_POLL_MS,
  BACKEND_START_TIMEOUT_MS,
  type BackendStatus,
  ensureBackend,
} from "../src/page/backend";
import {
  BACKEND_FAILED,
  BACKEND_UNSUPPORTED,
  NOT_APPROVED,
  STARTING,
  STILL_STARTING,
} from "../src/page/texts";
import { HttpError, fakeAgentServer } from "./fakes";

const START = `${BACKEND_PATH}/start`;

function status(
  state: BackendStatus["state"],
  extra: Partial<BackendStatus> = {},
): BackendStatus {
  return {
    name: "dr-library",
    state,
    revision: "r2",
    prepared_revision: "r2",
    detail: null,
    ...extra,
  };
}

/** The agent-server: each GET answers the next of statuses (the last repeats); start answers started. */
function agentServer(
  statuses: BackendStatus[],
  started?: BackendStatus | Error,
) {
  let next = 0;
  return fakeAgentServer((call) => {
    if (call.path === START) {
      if (started instanceof Error) throw started;
      return started;
    }
    return statuses[Math.min(next++, statuses.length - 1)];
  });
}

function check(
  server: ReturnType<typeof agentServer>,
  signal = new AbortController().signal,
) {
  const progress: string[] = [];
  const result = ensureBackend(server.request, signal, (sentence) =>
    progress.push(sentence),
  );
  return { result, progress };
}

describe("ensureBackend", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("asks once when the backend is ready", async () => {
    const server = agentServer([status("ready")]);
    expect(await check(server).result).toEqual({ ok: true });
    expect(server.calls).toEqual([{ path: BACKEND_PATH }]);
  });

  it.each(["stopped", "unhealthy"] as const)(
    "starts a %s backend prepared for this revision",
    async (state) => {
      const server = agentServer([status(state)], status("ready"));
      const { result, progress } = check(server);
      expect(await result).toEqual({ ok: true });
      expect(server.calls).toEqual([
        { path: BACKEND_PATH },
        { method: "POST", path: START, body: { revision: "r2" } },
      ]);
      expect(progress).toEqual([STARTING]);
    },
  );

  it.each([
    ["another revision", "r1"],
    ["no revision", null],
  ])(
    "never approves: prepared for %s is NOT_APPROVED with no start",
    async (_, prepared) => {
      const server = agentServer([
        status("stopped", { prepared_revision: prepared }),
      ]);
      expect(await check(server).result).toEqual({
        ok: false,
        message: NOT_APPROVED,
      });
      expect(server.calls.map((c) => c.path)).toEqual([BACKEND_PATH]);
      expect(server.calls.some((c) => c.path.endsWith("/prepare"))).toBe(false);
    },
  );

  it("polls a starting backend until it is ready", async () => {
    const server = agentServer([
      status("starting"),
      status("starting"),
      status("ready"),
    ]);
    const { result, progress } = check(server);
    await vi.advanceTimersByTimeAsync(2 * BACKEND_POLL_MS);
    expect(await result).toEqual({ ok: true });
    expect(server.calls.map((c) => c.path)).toEqual([
      BACKEND_PATH,
      BACKEND_PATH,
      BACKEND_PATH,
    ]);
    expect(progress[0]).toBe(STARTING);
  });

  it("gives up on a backend still starting after the timeout", async () => {
    const server = agentServer([status("starting")]);
    const { result } = check(server);
    await vi.advanceTimersByTimeAsync(
      BACKEND_START_TIMEOUT_MS + BACKEND_POLL_MS,
    );
    expect(await result).toEqual({
      ok: false,
      message: BACKEND_FAILED(STILL_STARTING),
    });
  });

  it.each([
    [
      "answers unhealthy",
      status("unhealthy", { detail: "Backend exited with code 1" }),
      "Backend exited with code 1",
    ],
    [
      "is refused",
      new HttpError(409, {
        detail: "backend revision must be prepared before start",
      }),
      "backend revision must be prepared before start",
    ],
  ])("says why when start %s", async (_, started, detail) => {
    const server = agentServer([status("stopped")], started);
    expect(await check(server).result).toEqual({
      ok: false,
      message: BACKEND_FAILED(detail),
    });
  });

  it.each(["missing", "unsupported"] as const)(
    "cannot run a %s backend",
    async (state) => {
      const detail = "Canvas App backend does not support this platform";
      const server = agentServer([status(state, { detail })]);
      expect(await check(server).result).toEqual({
        ok: false,
        message: BACKEND_UNSUPPORTED(detail),
      });
      expect(server.calls).toHaveLength(1);
    },
  );

  it("stops polling at once when aborted", async () => {
    const server = agentServer([status("starting")]);
    const controller = new AbortController();
    const { result } = check(server, controller.signal);
    const settled = result.catch((error: unknown) => error);
    await vi.advanceTimersByTimeAsync(BACKEND_POLL_MS);
    const asked = server.calls.length;
    controller.abort();
    expect(await settled).toBeInstanceOf(Error);
    await vi.advanceTimersByTimeAsync(10 * BACKEND_POLL_MS);
    expect(server.calls).toHaveLength(asked);
  });
});
