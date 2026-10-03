// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  readConversationNamespace,
  readSpendCap,
  readTheme,
  spendCapFromArgs,
} from "../src/page/context";
import { HttpError, controlsEvent, fakeAgentServer } from "./fakes";

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
  const SEARCH =
    "/api/conversations/c%201/events/search?kind=ACPSessionControlsEvent&sort_order=TIMESTAMP_DESC&limit=1";

  it.each([
    [
      "one value: the first message was sent",
      controlsEvent("router", ["router"]),
      { namespace: "router", started: true },
    ],
    [
      "several values: not started",
      controlsEvent("router", ["root", "router", "course_advisor"]),
      { namespace: "router", started: false },
    ],
    ["no event", { items: [], next_page_id: null }, null],
    [
      "another agent's options",
      {
        items: [
          {
            config_options: [{ id: "model", current_value: "x", options: [] }],
          },
        ],
      },
      null,
    ],
    ["an answer of another shape", { detail: "?" }, null],
  ])("%s", async (_, answer, expected) => {
    const server = fakeAgentServer(() => answer);
    expect(await readConversationNamespace(server.request, "c 1")).toEqual(
      expected,
    );
    expect(server.calls).toEqual([{ path: SEARCH }]);
  });

  it("is null when the request fails", async () => {
    const server = fakeAgentServer(() =>
      Promise.reject(new HttpError(500, null)),
    );
    expect(await readConversationNamespace(server.request, "c1")).toBeNull();
  });

  it("is null without a conversation, and asks nothing", async () => {
    const server = fakeAgentServer(() => controlsEvent("router", ["router"]));
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
