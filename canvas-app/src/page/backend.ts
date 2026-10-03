// ensureBackend: the Library's backend is running before every mount (§2.1, §5.4, decision F).

import type { AgentServerRequest } from "./host";
import {
  BACKEND_FAILED,
  BACKEND_UNSUPPORTED,
  NOT_APPROVED,
  STARTING,
  STILL_STARTING,
} from "./texts";

export const BACKEND_PATH =
  "/api/canvas-extensions/installed/dr-library/backend";
export const BACKEND_POLL_MS = 500;
export const BACKEND_START_TIMEOUT_MS = 45_000;

export interface BackendStatus {
  name: string;
  state:
    | "missing"
    | "stopped"
    | "starting"
    | "ready"
    | "unhealthy"
    | "unsupported";
  revision: string | null;
  prepared_revision: string | null;
  detail: string | null;
}

export type BackendCheck =
  | {
      ok: true;
    }
  | {
      ok: false;
      message: string;
    };

/** §2.1's table over GET BACKEND_PATH and POST BACKEND_PATH/start {revision}; never prepare.
 * ready → ok; starting → poll every BACKEND_POLL_MS up to BACKEND_START_TIMEOUT_MS;
 * stopped or unhealthy and prepared for this revision → start once, polling as for starting
 * when start gets no answer; not prepared → NOT_APPROVED; missing or unsupported →
 * BACKEND_UNSUPPORTED. An abort rejects at once. */
export async function ensureBackend(
  request: AgentServerRequest,
  signal: AbortSignal,
  onProgress: (sentence: string) => void,
): Promise<BackendCheck> {
  const deadline = Date.now() + BACKEND_START_TIMEOUT_MS;
  const read = () => request<BackendStatus>({ path: BACKEND_PATH });
  let status: BackendStatus;
  try {
    status = await read();
    let started = false;
    for (;;) {
      signal.throwIfAborted();
      if (status.state === "ready") return { ok: true };
      if (status.state === "missing" || status.state === "unsupported") {
        return {
          ok: false,
          message: BACKEND_UNSUPPORTED(status.detail ?? status.state),
        };
      }
      if (status.state === "starting") {
        onProgress(STARTING);
        if (Date.now() >= deadline)
          return { ok: false, message: BACKEND_FAILED(STILL_STARTING) };
        await sleep(BACKEND_POLL_MS, signal);
        status = await read();
        continue;
      }
      if (started)
        return {
          ok: false,
          message: BACKEND_FAILED(status.detail ?? status.state),
        };
      if (
        status.revision === null ||
        status.prepared_revision !== status.revision
      ) {
        return { ok: false, message: NOT_APPROVED };
      }
      onProgress(STARTING);
      started = true;
      status = await request<BackendStatus>({
        method: "POST",
        path: `${BACKEND_PATH}/start`,
        body: { revision: status.revision },
      }).catch((error: unknown) => {
        // §11 item 6: start can outlast the client's timeout; the status then says how it went.
        if (answered(error)) throw error;
        return read();
      });
    }
  } catch (error) {
    signal.throwIfAborted();
    return { ok: false, message: BACKEND_FAILED(errorDetail(error)) };
  }
}

/** The agent-server answered: the client's HttpError carries the status it answered with. */
function answered(error: unknown): boolean {
  return typeof (error as { status?: unknown } | null)?.status === "number";
}

/** The agent-server's own words: an HttpError's {detail}, else the error's message. */
export function errorDetail(error: unknown): string {
  const response = (error as { response?: { detail?: unknown } } | null)
    ?.response;
  if (typeof response?.detail === "string") return response.detail;
  return error instanceof Error ? error.message : String(error);
}

function sleep(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      signal.removeEventListener("abort", abort);
      resolve();
    }, ms);
    const abort = () => {
      clearTimeout(timer);
      reject(signal.reason);
    };
    signal.addEventListener("abort", abort, { once: true });
  });
}
