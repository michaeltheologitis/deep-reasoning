import { afterEach, describe, expect, it, vi } from "vitest";

import * as api from "../src/ui/api";
import { BackendUnavailable, LibraryError } from "../src/ui/api";

interface Sent {
  url: string;
  method: string;
  contentType: string | null;
  body: unknown;
}

/** fetch answering status and body (an object is sent as JSON); every request is recorded. */
function stubFetch(status = 200, body: unknown = {}) {
  const sent: Sent[] = [];
  vi.stubGlobal("fetch", async (url: string, init: RequestInit = {}) => {
    const headers = new Headers(init.headers);
    sent.push({
      url,
      method: init.method ?? "GET",
      contentType: headers.get("Content-Type"),
      body: init.body === undefined ? undefined : JSON.parse(String(init.body)),
    });
    const text = typeof body === "string" ? body : JSON.stringify(body);
    return new Response(text, { status });
  });
  return sent;
}

afterEach(() => vi.unstubAllGlobals());

describe("the requests", () => {
  it.each<[string, () => Promise<unknown>, string, string]>([
    ["getHealth", () => api.getHealth(), "GET", "../health"],
    ["getProblems", () => api.getProblems(), "GET", "../problems"],
    ["getProfile", () => api.getProfile(), "GET", "../profile"],
    ["getNamespaces", () => api.getNamespaces(), "GET", "../namespaces"],
    [
      "getNamespace",
      () => api.getNamespace("router.archive"),
      "GET",
      "../namespaces/router.archive",
    ],
    ["getEffective", () => api.getEffective(), "GET", "../effective"],
    [
      "getNamespaceEffective",
      () => api.getNamespaceEffective("router"),
      "GET",
      "../namespaces/router/effective",
    ],
    [
      "getDecompositions",
      () => api.getDecompositions(),
      "GET",
      "../decompositions",
    ],
    [
      "getDecomposition",
      () => api.getDecomposition("a b"),
      "GET",
      "../decompositions/a%20b",
    ],
    ["getTools", () => api.getTools(), "GET", "../tools"],
    ["getTool", () => api.getTool("word_count"), "GET", "../tools/word_count"],
    ["getMcp", () => api.getMcp(), "GET", "../mcp"],
    [
      "toolVersions",
      () => api.toolVersions("word_count"),
      "GET",
      "../tools/word_count/versions",
    ],
    [
      "deleteNamespace",
      () => api.deleteNamespace("router.archive", 2),
      "DELETE",
      "../namespaces/router.archive?base_version=2",
    ],
    [
      "deleteDecomposition",
      () => api.deleteDecomposition("catalog-lookup", 3),
      "DELETE",
      "../decompositions/catalog-lookup?base_version=3",
    ],
    [
      "deleteTool",
      () => api.deleteTool("word_count", 1),
      "DELETE",
      "../tools/word_count?base_version=1",
    ],
  ])("%s is %s %s, relative to the frame", async (_, request, method, url) => {
    const sent = stubFetch();
    await request();
    expect(sent).toEqual([{ url, method, contentType: null, body: undefined }]);
  });

  it.each<[string, () => Promise<unknown>, string, string, string[]]>([
    [
      "validate",
      () => api.validate({ kind: "decomposition", yaml: "{}" }),
      "POST",
      "../validate",
      ["kind", "yaml"],
    ],
    [
      "putProfile",
      () => api.putProfile({ yaml: "{}", base_version: 2 }),
      "PUT",
      "../profile",
      ["yaml", "base_version"],
    ],
    [
      "putNamespace",
      () =>
        api.putNamespace("router", {
          yaml: "{}",
          decompositions: ["a"],
          base_version: 1,
        }),
      "PUT",
      "../namespaces/router",
      ["yaml", "decompositions", "base_version"],
    ],
    [
      "putDecomposition",
      () =>
        api.putDecomposition("rank", {
          yaml: "{}",
          use_when: null,
          hint: null,
          namespaces: ["router"],
          base_version: 0,
        }),
      "PUT",
      "../decompositions/rank",
      ["yaml", "use_when", "hint", "namespaces", "base_version"],
    ],
    [
      "putTool",
      () =>
        api.putTool("word_count", {
          yaml: "{}",
          source: null,
          granted_in: [],
          base_version: 1,
        }),
      "PUT",
      "../tools/word_count",
      ["yaml", "source", "granted_in", "base_version"],
    ],
    [
      "putTool, saving anyway",
      () =>
        api.putTool("word_count", {
          yaml: "{}",
          source: "def make(c, p): ...",
          granted_in: [],
          base_version: 0,
          accept_check_failure: true,
        }),
      "PUT",
      "../tools/word_count",
      ["yaml", "source", "granted_in", "base_version", "accept_check_failure"],
    ],
    [
      "checkTool",
      () =>
        api.checkTool("word count", {
          yaml: "factory: make",
          source: "",
          example: null,
        }),
      "POST",
      "../tools/word%20count/check",
      ["yaml", "source", "example"],
    ],
    [
      "putMcp",
      () =>
        api.putMcp("github", {
          server: "github",
          transport: "stdio",
          command: "npx",
          args: [],
          url: null,
          env: ["GITHUB_TOKEN"],
          headers: [],
          granted_in: ["router"],
          base_version: 0,
        }),
      "PUT",
      "../mcp/github",
      [
        "server",
        "transport",
        "command",
        "args",
        "url",
        "env",
        "headers",
        "granted_in",
        "base_version",
      ],
    ],
  ])(
    "%s sends JSON with exactly D2's fields",
    async (_, request, method, url, keys) => {
      const sent = stubFetch();
      await request();
      expect(sent).toHaveLength(1);
      expect(sent[0]).toMatchObject({
        url,
        method,
        contentType: "application/json",
      });
      expect(Object.keys(sent[0]!.body as object)).toEqual(keys);
    },
  );

  it.each([
    [201, true],
    [200, false],
  ])(
    "a write answered %s says whether it created the record",
    async (status, created) => {
      stubFetch(status, { name: "router", version: 1 });
      const written = await api.putNamespace("router", {
        yaml: "{}",
        base_version: 0,
      });
      expect(written).toEqual({
        record: { name: "router", version: 1 },
        created,
      });
    },
  );
});

describe("the answers", () => {
  it("a D2 error is a LibraryError with its code, errors and head", async () => {
    const head = { name: "catalog lookup", version: 2, namespaces: ["router"] };
    stubFetch(409, {
      error: "conflict",
      message: "Decomposition 'catalog lookup' already exists, at version 2.",
      head,
    });
    const error = await api
      .putDecomposition("catalog-lookup", {
        yaml: "{}",
        use_when: null,
        hint: null,
        base_version: 0,
      })
      .catch((e: unknown) => e);
    expect(error).toBeInstanceOf(LibraryError);
    expect(error).toMatchObject({
      status: 409,
      code: "conflict",
      message: "Decomposition 'catalog lookup' already exists, at version 2.",
      errors: [],
      head,
    });
  });

  it("a tool Check refused is a LibraryError carrying the report", async () => {
    const check = { ok: false, outcome: "not_func", can_save_anyway: false };
    stubFetch(422, {
      error: "check_failed",
      message: "'word_count' did not pass Check, so it was not saved.",
      check,
    });
    const error = await api
      .putTool("word_count", { yaml: "factory: make", base_version: 0 })
      .catch((e: unknown) => e);
    expect(error).toBeInstanceOf(LibraryError);
    expect(error).toMatchObject({ status: 422, code: "check_failed", check });
  });

  it("a D2 validation error carries its field errors", async () => {
    const errors = [{ loc: "messages.1.content", msg: "Field required" }];
    stubFetch(422, {
      error: "invalid",
      message: "'x' is not a valid deep_reasoner Decomposition:",
      errors,
    });
    const error = await api.getHealth().catch((e: unknown) => e);
    expect(error).toMatchObject({
      status: 422,
      code: "invalid",
      errors,
      head: null,
    });
  });

  it.each<[string, number, unknown]>([
    ["the bridge's detail", 503, { detail: "Canvas App backend is not ready" }],
    ["a session that ended", 401, { detail: "App backend session required" }],
    ["a page that is not JSON", 502, "<html>Bad Gateway</html>"],
  ])("%s is BackendUnavailable with its status", async (_, status, body) => {
    stubFetch(status, body);
    const error = await api.getHealth().catch((e: unknown) => e);
    expect(error).toBeInstanceOf(BackendUnavailable);
    expect((error as BackendUnavailable).status).toBe(status);
  });

  it("no answer at all is BackendUnavailable with status 0", async () => {
    vi.stubGlobal("fetch", async () => {
      throw new TypeError("Failed to fetch");
    });
    const error = await api.getHealth().catch((e: unknown) => e);
    expect(error).toBeInstanceOf(BackendUnavailable);
    expect((error as BackendUnavailable).status).toBe(0);
  });
});
