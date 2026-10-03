// Fakes of the outside world at its boundary: the agent-server behind host.agentServer.request,
// C2's host API, and the frame's fetch.

import type {
  AgentServerRequest,
  CanvasExtensionAgentServerRequest,
  CanvasExtensionAppBackendFrameOptions,
  CanvasExtensionHost,
  CanvasExtensionPageMount,
} from "../src/page/host";

export type Answer = (
  request: CanvasExtensionAgentServerRequest,
) => unknown | Promise<unknown>;

/** The typescript-client's HttpError, as host.agentServer.request rejects with it. */
export class HttpError extends Error {
  constructor(
    readonly status: number,
    readonly response: unknown,
  ) {
    super(`HTTP ${status}`);
  }
}

export interface FakeAgentServer {
  request: AgentServerRequest;
  calls: CanvasExtensionAgentServerRequest[];
}

export function fakeAgentServer(answer: Answer): FakeAgentServer {
  const calls: CanvasExtensionAgentServerRequest[] = [];
  const request = (async (call: CanvasExtensionAgentServerRequest) => {
    calls.push(call);
    return answer(call);
  }) as AgentServerRequest;
  return { request, calls };
}

/** An event as the events search returns it: null fields left out (S2 §3.2 B2). */
export interface WireEvent {
  kind: string;
  [field: string]: unknown;
}

/** What the events search's `kind` matches: the event's module-qualified class name
 * (event_service.py:550 in the SDK fork at dr-1), never the `kind` in its JSON. */
const QUALIFIED_KINDS: Record<string, string> = {
  ACPSessionControlsEvent:
    "openhands.sdk.event.acp_session_controls.ACPSessionControlsEvent",
  MessageEvent: "openhands.sdk.event.llm_convertible.message.MessageEvent",
};

/** dr-acp's controls: the namespace option offering values (one once the conversation started),
 * and the namespace's commands. */
export function controlsEvent(
  namespace: string,
  values: string[],
  commands: string[] = [],
): WireEvent {
  return {
    kind: "ACPSessionControlsEvent",
    source: "agent",
    available_commands: commands.map((name) => ({ name, description: name })),
    config_options: [
      {
        id: "namespace",
        name: "Namespace",
        type: "select",
        current_value: namespace,
        description: "The namespace this conversation runs in.",
        options: values.map((value) => ({ value, name: value })),
      },
    ],
  };
}

export function messageEvent(text: string): WireEvent {
  return {
    kind: "MessageEvent",
    source: "user",
    llm_message: { role: "user", content: [{ type: "text", text }] },
  };
}

/** The agent-server's GET /api/conversations/<id>/events/search over each conversation's events,
 * oldest first, as event_router.py and event_service.py answer it at dr-1: `kind` is matched
 * against the module-qualified class name; TIMESTAMP_DESC walks from the newest; `limit` caps
 * the page. Any other path, or an unknown conversation, is a 404. */
export function eventsSearch(conversations: Record<string, WireEvent[]>) {
  return ({ path }: CanvasExtensionAgentServerRequest) => {
    const url = new URL(path, "http://agent-server");
    const id = /^\/api\/conversations\/([^/]+)\/events\/search$/.exec(
      url.pathname,
    )?.[1];
    const events =
      id === undefined ? undefined : conversations[decodeURIComponent(id)];
    if (events === undefined) throw new HttpError(404, { detail: "Not Found" });
    const kind = url.searchParams.get("kind");
    const matching = events.filter(
      (event) => kind === null || QUALIFIED_KINDS[event.kind] === kind,
    );
    if (url.searchParams.get("sort_order") === "TIMESTAMP_DESC")
      matching.reverse();
    const limit = Number(url.searchParams.get("limit") ?? 100);
    return { items: matching.slice(0, limit), next_page_id: null };
  };
}

export interface MountedFrame {
  container: HTMLElement;
  options: CanvasExtensionAppBackendFrameOptions;
  iframe: HTMLIFrameElement;
  disposed: boolean;
}

export interface FakeHost {
  host: CanvasExtensionHost;
  pages: Map<string, CanvasExtensionPageMount>;
  frames: MountedFrame[];
  agentServer: FakeAgentServer;
}

/** C2's host API: registerPage, agentServer.request over answer, and (unless frames is false)
 * appBackend.mountFrame appending an iframe at the ingress, as C2 §6.2 step 3 does. */
export function fakeHost(answer: Answer, { frames = true } = {}): FakeHost {
  const pages = new Map<string, CanvasExtensionPageMount>();
  const mounted: MountedFrame[] = [];
  const agentServer = fakeAgentServer(answer);
  const host: CanvasExtensionHost = {
    apiVersion: "1",
    registerPage: (id, mount) => {
      pages.set(id, mount);
      return () => pages.delete(id);
    },
    agentServer: { request: agentServer.request },
    ...(frames && {
      appBackend: {
        mountFrame: (
          container: HTMLElement,
          options: CanvasExtensionAppBackendFrameOptions,
        ) => {
          const iframe = document.createElement("iframe");
          iframe.src = `http://127.0.0.1:18000/app-backends/dr-library/${(options.path ?? "").slice(1)}`;
          iframe.title = options.title;
          container.append(iframe);
          const frame: MountedFrame = {
            container,
            options,
            iframe,
            disposed: false,
          };
          mounted.push(frame);
          return () => {
            frame.disposed = true;
            iframe.remove();
          };
        },
      },
    }),
  };
  return { host, pages, frames: mounted, agentServer };
}

/** A promise and the functions that settle it. */
export function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<T>((yes, no) => {
    resolve = yes;
    reject = no;
  });
  return { promise, resolve, reject };
}
