// The Tools tab's logic (D4 §2, §8.5, §8.6): pure functions over D2's tools, D4's grants and
// Canvas's MCP servers.

import type { McpServerInfo } from "../shared/protocol";
import type { McpGrantBody } from "./api";
import type { Effective, McpGrant, ToolRecord } from "./types";

/** deep_reasoner's own names in the REPL; a tool by one of them would hide it (D4 §3.2). */
export const RESERVED_NAMES: ReadonlySet<string> = new Set([
  "FinalAnswer",
  "Func",
  "Var",
  "run_all",
  "subagent",
  "task",
]);
const PYTHON_KEYWORDS: ReadonlySet<string> = new Set(
  (
    "False None True and as assert async await break class continue def del elif else " +
    "except finally for from global if import in is lambda nonlocal not or pass raise " +
    "return try while with yield"
  ).split(" "),
);

export type McpRowState = "given" | "disabled" | "not_in_profile" | "gone";

export interface McpRow {
  server: string;
  info: McpServerInfo | null; // null: gone from Canvas's settings, or its settings unread
  grant: McpGrant | null;
  state: McpRowState;
  changed: boolean;
  oldShim: boolean;
}

export interface ToolDraft {
  name: string;
  yaml: string;
  source: string;
  example: string;
  grantedIn: string[];
  baseVersion: number; // 0 for a new tool
}

export type McpSnapshot = Omit<McpGrantBody, "granted_in" | "base_version">;

/** The user's own tools, in GET /tools order: every tool that is not an MCP grant. */
export function splitTools(
  tools: readonly ToolRecord[],
  grants: readonly McpGrant[],
): ToolRecord[] {
  const granted = new Set(grants.map((g) => g.name));
  return tools.filter((tool) => !granted.has(tool.name));
}

/** A REPL name for a server (§8.5): lower case, [a-z0-9_], never a keyword, a reserved name
 * or a name taken, numbered from _2 until free. */
export function defaultToolName(
  server: string,
  taken: ReadonlySet<string>,
): string {
  let base = server
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
  if (/^[0-9]/.test(base)) base = `mcp_${base}`;
  if (base === "") base = "mcp_server";
  const free = (name: string) =>
    !PYTHON_KEYWORDS.has(name) && !RESERVED_NAMES.has(name) && !taken.has(name);
  if (free(base)) return base;
  let n = 2;
  while (!free(`${base}_${n}`)) n += 1;
  return `${base}_${n}`;
}

/** What a grant stores of a server: its target and its names, never a value. */
export function snapshotOf(info: McpServerInfo): McpSnapshot {
  return {
    server: info.name,
    transport: info.transport,
    command: info.command,
    args: [...info.args],
    url: info.url,
    env: [...info.env],
    headers: [...info.headers],
  };
}

/** The snapshot a grant holds, to resend unchanged. */
export function grantSnapshot(grant: McpGrant): McpSnapshot {
  return {
    server: grant.server,
    transport: grant.transport,
    command: grant.command,
    args: [...grant.args],
    url: grant.url,
    env: [...grant.env],
    headers: [...grant.headers],
  };
}

const same = (a: McpSnapshot, b: McpSnapshot) =>
  JSON.stringify(a) === JSON.stringify(b);

/** One row per server (§8.6): Canvas's, in its order, then the grants gone from it, by name.
 * Without Canvas's settings (null), the grants alone. */
export function mcpRows(
  servers: readonly McpServerInfo[] | null,
  grants: readonly McpGrant[],
): McpRow[] {
  const byServer = new Map(grants.map((g) => [g.server, g]));
  if (servers === null) {
    return grants.map((grant) => ({
      server: grant.server,
      info: null,
      grant,
      state: "given",
      changed: false,
      oldShim: !grant.shim_current,
    }));
  }
  const rows: McpRow[] = servers.map((info) => {
    const grant = byServer.get(info.name) ?? null;
    return {
      server: info.name,
      info,
      grant,
      state: info.why_not ?? "given",
      changed: grant !== null && !same(snapshotOf(info), grantSnapshot(grant)),
      oldShim: grant !== null && !grant.shim_current,
    };
  });
  const listed = new Set(servers.map((s) => s.name));
  const gone = grants
    .filter((g) => !listed.has(g.server))
    .sort((a, b) => a.server.localeCompare(b.server))
    .map((grant) => ({
      server: grant.server,
      info: null,
      grant,
      state: "gone" as const,
      changed: false,
      oldShim: !grant.shim_current,
    }));
  return [...rows, ...gone];
}

/** namespace → the ancestor it inherits tool's grant from, from GET /effective. */
export function inheritedGrants(
  tool: string,
  effective: readonly Effective[],
): Record<string, string> {
  const inherited: Record<string, string> = {};
  for (const view of effective) {
    const found = view.tools.find((t) => t.name === tool);
    if (found && found.source !== view.namespace)
      inherited[view.namespace] = found.source;
  }
  return inherited;
}

/** The draft's key under D3's drafts.ts prefix: dr-library.draft.tool.<name>, or .new. */
export function toolDraftKey(name: string | null): string {
  return `tool.${name ?? "new"}`;
}
