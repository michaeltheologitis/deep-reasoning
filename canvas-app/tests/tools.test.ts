import { describe, expect, it } from "vitest";

import type { McpServerInfo } from "../src/shared/protocol";
import {
  defaultToolName,
  inheritedNotes,
  mcpRows,
  snapshotOf,
  splitTools,
  toolDraftKey,
} from "../src/ui/tools";
import type {
  Effective,
  McpGrant,
  McpSnapshot,
  ToolRecord,
} from "../src/ui/types";

function server(
  name: string,
  fields: Partial<McpServerInfo> = {},
): McpServerInfo {
  return {
    name,
    transport: "stdio",
    command: "npx",
    args: ["-y", `@example/${name}`],
    url: null,
    env: ["TOKEN"],
    headers: [],
    forwarded: true,
    why_not: null,
    ...fields,
  };
}

function grant(name: string, fields: Partial<McpGrant> = {}): McpGrant {
  return {
    name,
    version: 1,
    server: name,
    transport: "stdio",
    command: "npx",
    args: ["-y", `@example/${name}`],
    url: null,
    env: ["TOKEN"],
    headers: [],
    granted_in: ["router"],
    shim_current: true,
    seen: null,
    ...fields,
  };
}

function tool(name: string): ToolRecord {
  return {
    name,
    version: 1,
    rev: 1,
    saved_at: "2026-10-03T00:00:00Z",
    yaml: "factory: make\n",
    source: "def make(client, params): ...\n",
    granted_in: [],
    data: { factory: "make" },
  };
}

function effective(namespace: string, tools: [string, string][]): Effective {
  return {
    namespace,
    chain: [],
    repl: { value: null, source: null },
    reasoner: { value: null, source: null },
    spawn: { value: null, source: null },
    system_suffix: [],
    tools: tools.map(([name, source]) => ({ name, source, defined: true })),
    vars: {},
    decompositions: [],
  };
}

describe("defaultToolName", () => {
  it.each<[string, string[], string]>([
    ["github", [], "github"],
    ["GitHub Enterprise", [], "github_enterprise"],
    ["--my.db--", [], "my_db"],
    ["1password", [], "mcp_1password"],
    ["!!!", [], "mcp_server"],
    ["class", [], "class_2"],
    ["run_all", [], "run_all_2"],
    ["github", ["github", "github_2"], "github_3"],
  ])("%s, with %j taken → %s", (name, taken, expected) => {
    expect(defaultToolName(name, new Set(taken))).toBe(expected);
  });
});

describe("mcpRows", () => {
  it("joins Canvas's servers with the grants, then the grants gone from Canvas", () => {
    const rows = mcpRows(
      [
        server("github"),
        server("slack", { forwarded: false, why_not: "disabled" }),
        server("postgres", { forwarded: false, why_not: "not_in_profile" }),
      ],
      [grant("old-wiki"), grant("gh", { server: "github" }), grant("a-gone")],
    );
    expect(
      rows.map((r) => [
        r.server,
        r.state,
        r.grant?.name ?? null,
        r.info !== null,
      ]),
    ).toEqual([
      ["github", "given", "gh", true],
      ["slack", "disabled", null, true],
      ["postgres", "not_in_profile", null, true],
      ["a-gone", "gone", "a-gone", false],
      ["old-wiki", "gone", "old-wiki", false],
    ]);
  });

  // A remote grant as GET /mcp answers it: its block keeps the URL and the headers.
  const remote: Omit<McpSnapshot, "server"> = {
    transport: "http",
    command: null,
    args: [],
    url: "https://x",
    env: [],
    headers: ["X-Trace"],
  };
  it.each<[string, boolean, Partial<McpServerInfo>, Partial<McpGrant>]>([
    ["server with the same settings", false, {}, {}],
    ["server with another command", true, { command: "uvx" }, {}],
    ["server with other arguments", true, { args: ["-y"] }, {}],
    ["server with another variable", true, { env: ["TOKEN", "ORG"] }, {}],
    [
      "server with another transport",
      true,
      { transport: "http", url: "https://x" },
      {},
    ],
    [
      "remote server with another header",
      true,
      { ...remote, headers: ["X-Trace", "Authorization"] },
      remote,
    ],
    [
      "stdio server with a header, which its block does not keep",
      false,
      { headers: ["Authorization"] },
      {},
    ],
    [
      "remote server with arguments and a variable, which its block does not keep",
      false,
      { ...remote, args: ["--quiet"], env: ["TOKEN"] },
      remote,
    ],
  ])("a granted %s is changed: %s", (_, changed, fields, granted) => {
    const [row] = mcpRows(
      [server("github", fields)],
      [grant("github", granted)],
    );
    expect(row?.changed).toBe(changed);
  });

  it("says when a grant's shim is older than this deep-reasoning's", () => {
    const rows = mcpRows(
      [server("github"), server("wiki")],
      [grant("github", { shim_current: false }), grant("wiki")],
    );
    expect(rows.map((r) => r.oldShim)).toEqual([true, false]);
  });

  it("without Canvas's settings, lists only the grants, none of them gone", () => {
    const rows = mcpRows(null, [grant("github")]);
    expect(rows.map((r) => [r.server, r.state, r.info])).toEqual([
      ["github", "given", null],
    ]);
  });
});

describe("snapshotOf", () => {
  it("is what a grant stores: names, never values", () => {
    expect(snapshotOf("github", server("github"))).toEqual({
      server: "github",
      transport: "stdio",
      command: "npx",
      args: ["-y", "@example/github"],
      url: null,
      env: ["TOKEN"],
      headers: [],
    });
  });
});

describe("splitTools", () => {
  it("keeps the user's own tools, in GET /tools order", () => {
    const tools = [tool("word_count"), tool("github"), tool("rag")];
    expect(splitTools(tools, [grant("github")]).map((t) => t.name)).toEqual([
      "word_count",
      "rag",
    ]);
  });
});

describe("inheritedNotes", () => {
  it("names the ancestor each namespace inherits a grant from", () => {
    const views = [
      effective("root", [["word_count", "root"]]),
      effective("router", [["word_count", "root"]]),
      effective("router.archive", [["word_count", "root"]]),
      effective("course_advisor", [["llm", "course_advisor"]]),
    ];
    expect(inheritedNotes("word_count", views)).toEqual({
      router: "inherited from root",
      "router.archive": "inherited from root",
    });
  });
});

describe("toolDraftKey", () => {
  it.each([
    ["word_count", "tool.word_count"],
    [null, "tool.new"],
  ])("%s → %s", (name, key) => {
    expect(toolDraftKey(name)).toBe(key);
  });
});
