import { describe, expect, it } from "vitest";

import { inheritedNotes, splitTools, toolDraftKey } from "../src/ui/tools";
import type { Effective, McpGrant, ToolRecord } from "../src/ui/types";

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
