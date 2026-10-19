// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  mcpServersFromSettings,
  readConversationNamespace,
  readMcpServers,
  readSpendCap,
  readTheme,
  spendCapFromArgs,
  withSpendCap,
  writeSpendCap,
} from "../src/page/context";
import {
  CAP_NOT_SAVED,
  CAP_NO_PROXY,
  CAP_PROFILE_MISSING,
} from "../src/page/texts";
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

describe("withSpendCap", () => {
  it.each([
    [
      ["--home", "/h", "--spend-cap-usd", "5", "--verbose"],
      ["--home", "/h", "--spend-cap-usd", "12.50", "--verbose"],
    ],
    [
      ["--home", "/h", "--spend-cap-usd=5", "--verbose"],
      ["--home", "/h", "--spend-cap-usd", "12.50", "--verbose"],
    ],
    [
      ["--home", "/h"],
      ["--home", "/h", "--spend-cap-usd", "12.50"],
    ],
    [[], ["--spend-cap-usd", "12.50"]],
    [["--home", "/h", "--no-key-proxy"], null],
  ])(
    "sets the pair and keeps every other argument in place: %j",
    (args, set) => {
      expect(withSpendCap(args, "12.50")).toEqual(set);
    },
  );
});

describe("writeSpendCap", () => {
  const PROFILE = {
    id: "p1",
    name: "deep_reasoner",
    agent_kind: "acp",
    acp_command: "/home/u/.deep-reasoning/runtime/current/bin/dr-acp",
    acp_args: ["--home", "/h", "--spend-cap-usd", "5"],
    mcp_server_refs: ["echo"],
  };
  const PATH = "/api/agent-profiles/deep_reasoner";

  it("reads the profile, then posts it whole with the new cap", async () => {
    const server = fakeAgentServer((call) =>
      call.method === "POST" ? { profile: call.body } : { profile: PROFILE },
    );
    expect(await writeSpendCap(server.request, "12.50")).toEqual({
      ok: true,
      cap: "12.50",
    });
    expect(server.calls).toEqual([
      { path: PATH },
      {
        method: "POST",
        path: PATH,
        body: {
          ...PROFILE,
          acp_args: ["--home", "/h", "--spend-cap-usd", "12.50"],
        },
      },
    ]);
  });

  it("says the profile is missing when there is none, and posts nothing", async () => {
    const server = fakeAgentServer(() => {
      throw new HttpError(404, { detail: "Not Found" });
    });
    expect(await writeSpendCap(server.request, "7")).toEqual({
      ok: false,
      message: CAP_PROFILE_MISSING,
    });
    expect(server.calls).toEqual([{ path: PATH }]);
  });

  it("refuses without posting when the key proxy is off", async () => {
    const server = fakeAgentServer(() => ({
      profile: { ...PROFILE, acp_args: ["--no-key-proxy"] },
    }));
    expect(await writeSpendCap(server.request, "7")).toEqual({
      ok: false,
      message: CAP_NO_PROXY,
    });
    expect(server.calls).toEqual([{ path: PATH }]);
  });

  it("says why the agent-server refused the write", async () => {
    const server = fakeAgentServer((call) => {
      if (call.method !== "POST") return { profile: PROFILE };
      throw new HttpError(422, { detail: "acp_args must be strings" });
    });
    expect(await writeSpendCap(server.request, "7")).toEqual({
      ok: false,
      message: CAP_NOT_SAVED("acp_args must be strings"),
    });
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

const REDACTED = "**********";
// Canvas's MCP settings as GET /api/settings sends them without X-Expose-Secrets.
const MCP_CONFIG = {
  github: {
    command: "npx",
    args: ["-y", "@modelcontextprotocol/server-github"],
    env: { GITHUB_PERSONAL_ACCESS_TOKEN: REDACTED },
  },
  postgres: {
    url: "https://db.lab.example/mcp",
    transport: "streamable-http",
    headers: { Authorization: REDACTED },
  },
  wiki: { url: "http://127.0.0.1:9000/sse", transport: "sse" },
  slack: { command: "slack-mcp", enabled: false },
  nothing: { description: "neither a command nor a URL" },
};

describe("mcpServersFromSettings", () => {
  const servers = mcpServersFromSettings(MCP_CONFIG, null);

  it("reads stdio, http and sse servers as the bridge does, and skips the rest", () => {
    expect(servers.map((s) => [s.name, s.transport])).toEqual([
      ["github", "stdio"],
      ["postgres", "http"],
      ["wiki", "sse"],
      ["slack", "stdio"],
    ]);
    expect(servers[0]).toEqual({
      name: "github",
      transport: "stdio",
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-github"],
      url: null,
      env: ["GITHUB_PERSONAL_ACCESS_TOKEN"],
      headers: [],
      forwarded: true,
      why_not: null,
    });
    expect(servers[1]).toMatchObject({
      command: null,
      url: "https://db.lab.example/mcp",
      headers: ["Authorization"],
    });
  });

  it("copies the names of environment variables and headers, never a value", () => {
    expect(JSON.stringify(servers)).not.toContain(REDACTED);
  });

  // auth as GET /api/settings sends it: the names are the headers the bridge sends for it,
  // after the server's own, each once.
  it.each<[string, Record<string, unknown>, string[]]>([
    [
      "bearer",
      { strategy: "bearer", value: REDACTED },
      ["X-Trace", "Authorization"],
    ],
    [
      "basic",
      { strategy: "basic", username: "ada", password: REDACTED },
      ["X-Trace", "Authorization"],
    ],
    [
      "an API key without a header name",
      { strategy: "api_key", value: REDACTED },
      ["X-Trace", "Authorization"],
    ],
    [
      "an API key with a header name",
      { strategy: "api_key", value: REDACTED, header_name: "X-Api-Key" },
      ["X-Trace", "X-Api-Key"],
    ],
    [
      "named headers",
      {
        strategy: "header",
        headers: { "X-Tenant": REDACTED, "X-Trace": REDACTED },
      },
      ["X-Trace", "X-Tenant"],
    ],
    ["none", { strategy: "none" }, ["X-Trace"]],
    [
      "OAuth",
      {
        strategy: "oauth2",
        authentication: {
          type: "oauth",
          client_id: "c",
          client_secret: REDACTED,
        },
      },
      ["X-Trace"],
    ],
  ])(
    "adds the header names a remote server's auth sends: %s",
    (_, auth, headers) => {
      const read = mcpServersFromSettings(
        {
          postgres: {
            url: "https://db.lab.example/mcp",
            headers: { "X-Trace": REDACTED },
            auth,
          },
        },
        null,
      );
      expect(read.map((s) => s.headers)).toEqual([headers]);
      expect(JSON.stringify(read)).not.toContain(REDACTED);
    },
  );

  it.each<[string[] | null, Record<string, string | null>]>([
    [null, { github: null, postgres: null, wiki: null, slack: "disabled" }],
    [
      ["github", "slack"],
      {
        github: null,
        postgres: "not_in_profile",
        wiki: "not_in_profile",
        slack: "disabled",
      },
    ],
  ])("with the profile's refs %j, says which are not given", (refs, whyNot) => {
    const read = mcpServersFromSettings(MCP_CONFIG, refs);
    expect(Object.fromEntries(read.map((s) => [s.name, s.why_not]))).toEqual(
      whyNot,
    );
    expect(read.filter((s) => s.forwarded).map((s) => s.name)).toEqual(
      Object.keys(whyNot).filter((name) => whyNot[name] === null),
    );
  });
});

describe("readMcpServers", () => {
  it("reads Canvas's settings without their secrets, and the profile's refs", async () => {
    const server = fakeAgentServer(({ path }) =>
      path === "/api/settings"
        ? { agent_settings: { mcp_config: MCP_CONFIG } }
        : { name: "deep_reasoner", profile: { mcp_server_refs: ["github"] } },
    );
    const read = await readMcpServers(server.request);
    expect(read?.map((s) => [s.name, s.forwarded])).toEqual([
      ["github", true],
      ["postgres", false],
      ["wiki", false],
      ["slack", false],
    ]);
    expect(server.calls).toEqual([
      { path: "/api/settings" },
      { path: "/api/agent-profiles/deep_reasoner" },
    ]);
  });

  it.each(["/api/settings", "/api/agent-profiles/deep_reasoner"])(
    "is null when %s fails",
    async (failing) => {
      const server = fakeAgentServer(({ path }) => {
        if (path === failing) throw new HttpError(500, null);
        return path === "/api/settings"
          ? { agent_settings: { mcp_config: MCP_CONFIG } }
          : { profile: {} };
      });
      expect(await readMcpServers(server.request)).toBeNull();
    },
  );
});
