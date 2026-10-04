// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  readConversationNamespace,
  readSpendCap,
  readTheme,
  spendCapFromArgs,
} from "../src/page/context";
import {
  HttpError,
  controlsEvent,
  eventsSearch,
  fakeAgentServer,
  messageEvent,
} from "./fakes";

describe("spendCapFromArgs", () => {
  it.each([
    [["--home", "/h", "--spend-cap-usd", "7"], "7"],
    [["--spend-cap-usd=2.5"], "2.5"],
    [["--home", "/h"], "5"],
    [[], "5"],
    [null, "5"],
    [["--spend-cap-usd", "7", "--no-key-proxy"], "off"],
    [["--spend-cap-usd", "abc"], "5"],
    [["--spend-cap-usd"], "5"],
  ])("%j → %s", (args, cap) => {
    expect(spendCapFromArgs(args)).toBe(cap);
  });
});

describe("readSpendCap", () => {
  it("reads the deep_reasoner profile's arguments", async () => {
    const server = fakeAgentServer(() => ({
      name: "deep_reasoner",
      profile: { acp_args: ["--home", "/h", "--spend-cap-usd", "3"] },
    }));
    expect(await readSpendCap(server.request)).toBe("3");
    expect(server.calls).toEqual([
      { path: "/api/agent-profiles/deep_reasoner" },
    ]);
  });

  it("is the default when the profile cannot be read", async () => {
    const server = fakeAgentServer(() => {
      throw new HttpError(404, { detail: "Not Found" });
    });
    expect(await readSpendCap(server.request)).toBe("5");
  });
});

describe("readConversationNamespace", () => {
  const ALL = ["root", "router", "course_advisor"];

  it.each([
    [
      "started: the newest controls event offers one value",
      [
        controlsEvent("router", ALL),
        controlsEvent("router", ALL, ["summarize"]),
        messageEvent("Which course first?"),
        controlsEvent("router", ["router"]),
      ],
      { namespace: "router", started: true },
    ],
    [
      "not started: the first event after a start, before the agent's menu",
      [controlsEvent("router", ALL)],
      { namespace: "router", started: false },
    ],
    [
      "the newest event is the state: a namespace picked after the start",
      [
        controlsEvent("router", ALL, ["summarize"]),
        controlsEvent("course_advisor", ALL),
      ],
      { namespace: "course_advisor", started: false },
    ],
    ["no controls event", [messageEvent("hello")], null],
    [
      "another agent's options",
      [
        {
          kind: "ACPSessionControlsEvent",
          available_commands: [],
          config_options: [
            {
              id: "model",
              name: "Model",
              type: "select",
              current_value: "x",
              options: [],
            },
          ],
        },
      ],
      null,
    ],
  ])("%s", async (_, events, expected) => {
    const server = fakeAgentServer(eventsSearch({ "c 1": events }));
    expect(await readConversationNamespace(server.request, "c 1")).toEqual(
      expected,
    );
    expect(server.calls).toHaveLength(1);
  });

  it("is null for an answer of another shape", async () => {
    const server = fakeAgentServer(() => ({ detail: "?" }));
    expect(await readConversationNamespace(server.request, "c1")).toBeNull();
  });

  it("is null when the request fails", async () => {
    const server = fakeAgentServer(eventsSearch({}));
    expect(await readConversationNamespace(server.request, "c1")).toBeNull();
  });

  it("is null without a conversation, and asks nothing", async () => {
    const server = fakeAgentServer(
      eventsSearch({ c1: [controlsEvent("router", ["router"])] }),
    );
    expect(await readConversationNamespace(server.request, null)).toBeNull();
    expect(server.calls).toEqual([]);
  });
});

describe("readTheme", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("keeps the listed tokens and drops unsafe values", () => {
    const computed: Record<string, string> = {
      "--oh-surface": " #21252F",
      "--oh-border": "url(x)",
      "--oh-radius": "8px",
      "--unlisted": "#fff",
      "color-scheme": "dark",
      "font-family": '-apple-system, "SF Pro", sans-serif',
    };
    vi.stubGlobal("getComputedStyle", () => ({
      getPropertyValue: (name: string) => computed[name] ?? "",
    }));
    expect(readTheme(document.body)).toEqual({
      "--oh-surface": "#21252F",
      "--oh-radius": "8px",
      "color-scheme": "dark",
      "font-family": '-apple-system, "SF Pro", sans-serif',
    });
  });
});
