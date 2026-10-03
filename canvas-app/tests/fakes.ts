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

export function controlsEvent(namespace: string, values: string[]) {
  return {
    items: [
      {
        kind: "ACPSessionControlsEvent",
        available_commands: [],
        config_options: [
          {
            id: "namespace",
            name: "Namespace",
            type: "select",
            current_value: namespace,
            options: values.map((value) => ({ value, name: value })),
          },
        ],
      },
    ],
    next_page_id: null,
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
