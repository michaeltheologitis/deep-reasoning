// The Tools tab's logic (D4 §2): pure functions over D2's tools and D4's grants.

import { INHERITED_ROW } from "./texts";
import type { Effective, McpGrant, ToolRecord } from "./types";

export interface ToolDraft {
  name: string;
  yaml: string;
  source: string;
  example: string;
  grantedIn: string[];
  baseVersion: number; // 0 for a new tool
}

/** The user's own tools, in GET /tools order: every tool that is not an MCP grant. */
export function splitTools(
  tools: readonly ToolRecord[],
  grants: readonly McpGrant[],
): ToolRecord[] {
  const granted = new Set(grants.map((g) => g.name));
  return tools.filter((tool) => !granted.has(tool.name));
}

/** namespace → "inherited from <ancestor>", for each namespace that inherits tool's grant,
 * from GET /effective. */
export function inheritedNotes(
  tool: string,
  effective: readonly Effective[],
): Record<string, string> {
  const notes: Record<string, string> = {};
  for (const view of effective) {
    const found = view.tools.find((t) => t.name === tool);
    if (found && found.source !== view.namespace)
      notes[view.namespace] = INHERITED_ROW(found.source);
  }
  return notes;
}

/** The draft's key under D3's drafts.ts prefix: dr-library.draft.tool.<name>, or .new. */
export function toolDraftKey(name: string | null): string {
  return `tool.${name ?? "new"}`;
}
