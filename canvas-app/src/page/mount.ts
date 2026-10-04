// mountTab: the sequence of §4.2, from "Opening the Library…" to the frame and its two messages.

import {
  type FrameParams,
  type TabId,
  TAB_TITLES,
  frameSearch,
  isFrameMessage,
} from "../shared/protocol";
import { ensureBackend } from "./backend";
import { readConversationNamespace, readSpendCap, readTheme } from "./context";
import type {
  CanvasExtensionAppBackendError,
  CanvasExtensionDispose,
  CanvasExtensionHost,
  CanvasExtensionPageMountContext,
} from "./host";
import { LOADING, NO_FRAMES, TRY_AGAIN } from "./texts";

const focusByTab = new Map<TabId, string | null>();

/** The focus the next mount of tab takes. */
export function putFocus(tab: TabId, focus: string | null): void {
  focusByTab.set(tab, focus);
}

/** Read once: a focus is meant for the very next mount of that tab. */
export function takeFocus(tab: TabId): string | null {
  const focus = focusByTab.get(tab) ?? null;
  focusByTab.delete(tab);
  return focus;
}

/** A sentence in Canvas's DOM while the frame is not there: progress, or an error (with Try again
 * when trying again can help). */
function show(
  container: HTMLElement,
  sentence: string,
  error = false,
  retry?: () => void,
): void {
  const line = document.createElement("p");
  line.dataset.testid = error ? "dr-library-error" : "dr-library-loading";
  line.textContent = sentence;
  line.style.cssText =
    "margin: 0; padding: 12px 16px; color: var(--oh-muted, inherit);";
  container.replaceChildren(line);
  if (!retry) return;
  const button = document.createElement("button");
  button.type = "button";
  button.dataset.testid = "dr-library-retry";
  button.textContent = TRY_AGAIN;
  button.style.cssText = "margin: 0 16px;";
  button.addEventListener("click", retry);
  container.append(button);
}

/** Returns its disposer synchronously; the work runs under an AbortController. */
export function mountTab(
  host: CanvasExtensionHost,
  tab: TabId,
  context: CanvasExtensionPageMountContext,
): CanvasExtensionDispose {
  const { container } = context;
  const controller = new AbortController();
  const focus = takeFocus(tab);
  let disposeFrame: CanvasExtensionDispose | null = null;
  let retriedNotReady = false;

  const onMessage = (event: MessageEvent) => {
    const frame = container.querySelector("iframe");
    if (
      !frame ||
      event.source !== frame.contentWindow ||
      !isFrameMessage(event.data)
    )
      return;
    if (event.data.type === "dr-library/reload") {
      void run();
    } else if (context.surface.kind === "conversation-panel") {
      putFocus(event.data.tab, event.data.focus);
      context.surface.selectTab(event.data.tab);
    }
  };

  const onError = (error: CanvasExtensionAppBackendError) => {
    if (error.reason !== "not-ready" || retriedNotReady) return;
    retriedNotReady = true;
    void run();
  };

  function closeFrame() {
    window.removeEventListener("message", onMessage);
    disposeFrame?.();
    disposeFrame = null;
  }

  async function run(): Promise<void> {
    closeFrame();
    show(container, LOADING);
    const request = host.agentServer.request;
    const [backend, conversation, cap] = await Promise.all([
      ensureBackend(request, controller.signal, (sentence) =>
        show(container, sentence),
      ),
      readConversationNamespace(request, context.conversationId),
      readSpendCap(request),
    ]).catch(() => [null, null, null] as const);
    if (controller.signal.aborted || backend === null || cap === null) return;
    if (!backend.ok)
      return show(container, backend.message, true, () => void run());
    if (!host.appBackend) return show(container, NO_FRAMES, true);
    const params: FrameParams = {
      tab,
      parent: window.location.origin,
      namespace: conversation?.namespace ?? null,
      started: conversation?.started ?? false,
      cap,
      focus,
      theme: readTheme(container),
    };
    container.replaceChildren();
    disposeFrame = host.appBackend.mountFrame(container, {
      path: `/ui/${frameSearch(params)}`,
      title: TAB_TITLES[tab],
      onError,
    });
    window.addEventListener("message", onMessage);
  }

  void run();
  return () => {
    controller.abort();
    closeFrame();
    container.replaceChildren();
  };
}
