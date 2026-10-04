// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type {
  CanvasExtensionAgentServerRequest,
  CanvasExtensionPageMountContext,
} from "../src/page/host";
import { BACKEND_PATH } from "../src/page/backend";
import { activate } from "../src/page/index";
import { mountTab } from "../src/page/mount";
import { LOADING, NOT_APPROVED, NO_FRAMES, TRY_AGAIN } from "../src/page/texts";
import {
  type TabId,
  TAB_IDS,
  TAB_TITLES,
  readFrameParams,
} from "../src/shared/protocol";
import {
  type Answer,
  controlsEvent,
  eventsSearch,
  fakeHost,
  messageEvent,
} from "./fakes";

const THEME = { "--oh-surface": "#21252F", "color-scheme": "dark" };
const ALL = ["root", "router", "course_advisor"];
/** Each conversation's events on the agent-server: c1 started in router, c2 has not started. */
const searchEvents = eventsSearch({
  c1: [
    controlsEvent("router", ALL, ["summarize"]),
    messageEvent("Which course first?"),
    controlsEvent("router", ["router"]),
  ],
  c2: [controlsEvent("course_advisor", ALL)],
});

function backend(state = "ready") {
  return {
    name: "dr-library",
    state,
    revision: "r1",
    prepared_revision: "r1",
    detail: null,
  };
}

/** The agent-server of a conversation panel: the backend ready, each conversation's controls,
 * and a profile capping spend at $7. */
const agentServer: Answer = (call: CanvasExtensionAgentServerRequest) => {
  if (call.path === BACKEND_PATH) return backend();
  if (call.path.startsWith("/api/agent-profiles/")) {
    return {
      name: "deep_reasoner",
      profile: { acp_args: ["--spend-cap-usd", "7"] },
    };
  }
  return searchEvents(call);
};

function context(conversationId: string, tab: TabId = "create") {
  const selectTab = vi.fn();
  const container = document.createElement("div");
  document.body.append(container);
  const mountContext: CanvasExtensionPageMountContext = {
    container,
    path: tab,
    navigate: vi.fn(),
    conversationId,
    surface: {
      kind: "conversation-panel",
      panelId: "decompositions",
      tabId: tab,
      selectTab,
    },
  };
  return { mountContext, container, selectTab };
}

function frameParams(src: string) {
  return readFrameParams(new URL(src).search, false);
}

function post(source: Window | null, data: unknown) {
  window.dispatchEvent(new MessageEvent("message", { data, source }));
}

async function settle() {
  for (let i = 0; i < 10; i++) await Promise.resolve();
  await new Promise((resolve) => setTimeout(resolve, 0));
}

beforeEach(() => {
  vi.stubGlobal("getComputedStyle", () => ({
    getPropertyValue: (name: string) =>
      (THEME as Record<string, string>)[name] ?? "",
  }));
});

afterEach(() => {
  vi.unstubAllGlobals();
  document.body.replaceChildren();
});

describe("activate", () => {
  it("registers exactly the four tabs, and its disposer removes them", () => {
    const fake = fakeHost(agentServer);
    const dispose = activate(fake.host);
    expect([...fake.pages.keys()]).toEqual([...TAB_IDS]);
    dispose();
    expect(fake.pages.size).toBe(0);
  });
});

describe("mountTab", () => {
  it("frames /ui/ with the conversation's namespace, the cap, the theme and Canvas's origin", async () => {
    const fake = fakeHost(agentServer);
    const { mountContext, container } = context("c1");
    mountTab(fake.host, "create", mountContext);
    expect(container.textContent).toBe(LOADING);
    await settle();
    const [frame] = fake.frames;
    expect(frame?.container).toBe(container);
    expect(frame?.options.title).toBe(TAB_TITLES.create);
    expect(frame?.options.path?.startsWith("/ui/?")).toBe(true);
    expect(frameParams(frame!.iframe.src)).toEqual({
      tab: "create",
      parent: window.location.origin,
      namespace: "router",
      started: true,
      cap: "7",
      focus: null,
      theme: THEME,
    });
    expect(container.textContent).toBe("");
  });

  it("mounts each conversation with its own namespace", async () => {
    const fake = fakeHost(agentServer);
    const first = mountTab(fake.host, "create", context("c1").mountContext);
    await settle();
    first();
    mountTab(fake.host, "create", context("c2").mountContext);
    await settle();
    const params = fake.frames.map((frame) => frameParams(frame.iframe.src));
    expect(params.map((p) => [p.namespace, p.started])).toEqual([
      ["router", true],
      ["course_advisor", false],
    ]);
  });

  it("selects the tab a frame asks for, and that tab's next mount takes the focus", async () => {
    const fake = fakeHost(agentServer);
    const create = context("c1");
    mountTab(fake.host, "create", create.mountContext);
    await settle();
    const frame = fake.frames[0]!;
    post(frame.iframe.contentWindow, {
      type: "dr-library/select-tab",
      tab: "browse",
      focus: "rank-by-x",
    });
    expect(create.selectTab).toHaveBeenCalledWith("browse");
    mountTab(fake.host, "browse", context("c1", "browse").mountContext);
    mountTab(fake.host, "browse", context("c1", "browse").mountContext);
    await settle();
    expect(
      fake.frames.slice(1).map((f) => frameParams(f.iframe.src).focus),
    ).toEqual(["rank-by-x", null]);
  });

  it("ignores a message from any window but its frame's", async () => {
    const fake = fakeHost(agentServer);
    const create = context("c1");
    mountTab(fake.host, "create", create.mountContext);
    const other = document.createElement("iframe");
    document.body.append(other);
    await settle();
    post(window, { type: "dr-library/select-tab", tab: "browse", focus: null });
    post(other.contentWindow, {
      type: "dr-library/select-tab",
      tab: "browse",
      focus: null,
    });
    post(other.contentWindow, { type: "dr-library/reload" });
    await settle();
    expect(create.selectTab).not.toHaveBeenCalled();
    expect(fake.frames).toHaveLength(1);
  });

  it("remounts on reload, checking the backend again", async () => {
    const fake = fakeHost(agentServer);
    mountTab(fake.host, "browse", context("c1", "browse").mountContext);
    await settle();
    post(fake.frames[0]!.iframe.contentWindow, { type: "dr-library/reload" });
    await settle();
    expect(fake.frames.map((f) => f.disposed)).toEqual([true, false]);
    expect(
      fake.agentServer.calls.filter((c) => c.path === BACKEND_PATH),
    ).toHaveLength(2);
  });

  it("remounts once when the frame's backend was not ready", async () => {
    const fake = fakeHost(agentServer);
    mountTab(fake.host, "browse", context("c1", "browse").mountContext);
    await settle();
    fake.frames[0]!.options.onError?.({
      reason: "not-ready",
      message: "not ready",
    });
    await settle();
    fake.frames[1]!.options.onError?.({
      reason: "not-ready",
      message: "not ready",
    });
    fake.frames[1]!.options.onError?.({
      reason: "session-refused",
      message: "refused",
    });
    await settle();
    expect(fake.frames).toHaveLength(2);
    expect(fake.frames[0]!.disposed).toBe(true);
  });

  it("leaves nothing behind when disposed during the backend check", async () => {
    const pending = Promise.withResolvers<unknown>();
    const fake = fakeHost((call) =>
      call.path === BACKEND_PATH ? pending.promise : agentServer(call),
    );
    const { mountContext, container } = context("c1");
    const dispose = mountTab(fake.host, "create", mountContext);
    await settle();
    dispose();
    pending.resolve(backend());
    await settle();
    expect(container.childNodes).toHaveLength(0);
    expect(fake.frames).toHaveLength(0);
  });

  it("says the backend is not approved, and Try again checks again", async () => {
    let state = "stopped";
    const fake = fakeHost((call) =>
      call.path === BACKEND_PATH
        ? {
            ...backend(state),
            prepared_revision: state === "ready" ? "r1" : null,
          }
        : agentServer(call),
    );
    const { mountContext, container } = context("c1");
    mountTab(fake.host, "create", mountContext);
    await settle();
    expect(
      container.querySelector('[data-testid="dr-library-error"]')?.textContent,
    ).toBe(NOT_APPROVED);
    state = "ready";
    const retry = container.querySelector<HTMLButtonElement>(
      '[data-testid="dr-library-retry"]',
    );
    expect(retry?.textContent).toBe(TRY_AGAIN);
    retry?.click();
    await settle();
    expect(fake.frames).toHaveLength(1);
  });

  it("says when Canvas cannot show an App's frames", async () => {
    const fake = fakeHost(agentServer, { frames: false });
    const { mountContext, container } = context("c1");
    mountTab(fake.host, "create", mountContext);
    await settle();
    expect(
      container.querySelector('[data-testid="dr-library-error"]')?.textContent,
    ).toBe(NO_FRAMES);
  });
});
