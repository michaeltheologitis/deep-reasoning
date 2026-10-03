// The subset of C2's host API (C2 §7, Appendix A.1 and A.11) the Library App uses; types only.

export type CanvasExtensionDispose = () => void;

export interface CanvasExtensionPageSurface {
  kind: "page";
}

export interface CanvasExtensionConversationPanelSurface {
  kind: "conversation-panel";
  panelId: string;
  tabId: string;
  selectTab: (tabId: string) => void;
}

export interface CanvasExtensionPageMountContext {
  container: HTMLElement;
  path: string;
  navigate: (path: string) => void;
  conversationId: string | null;
  surface: CanvasExtensionPageSurface | CanvasExtensionConversationPanelSurface;
}

export type CanvasExtensionPageMount = (
  context: CanvasExtensionPageMountContext,
) => void | CanvasExtensionDispose | Promise<void | CanvasExtensionDispose>;

export interface CanvasExtensionAgentServerRequest {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  path: string;
  body?: unknown;
  headers?: Record<string, string>;
}

export type AgentServerRequest = <T = unknown>(
  request: CanvasExtensionAgentServerRequest,
) => Promise<T>;

export type CanvasExtensionAppBackendErrorReason =
  | "no-ingress"
  | "not-ready"
  | "session-refused"
  | "unsupported-backend";

export interface CanvasExtensionAppBackendError {
  reason: CanvasExtensionAppBackendErrorReason;
  message: string;
}

export interface CanvasExtensionAppBackendFrameOptions {
  path?: string;
  title: string;
  onError?: (error: CanvasExtensionAppBackendError) => void;
}

export interface CanvasExtensionHost {
  readonly apiVersion: "1";
  registerPage: (
    contributionId: string,
    mount: CanvasExtensionPageMount,
  ) => CanvasExtensionDispose;
  agentServer: {
    request: AgentServerRequest;
  };
  /** C2 PR 3; absent on a Canvas without it. */
  readonly appBackend?: {
    mountFrame: (
      container: HTMLElement,
      options: CanvasExtensionAppBackendFrameOptions,
    ) => CanvasExtensionDispose;
  };
}
