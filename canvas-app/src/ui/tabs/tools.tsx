// Tools (§2.5; D4 §2): the safety banner, always first, D4's risk line, and your own tools
// with their editor.

import { useState } from "preact/hooks";

import { getEffective, getMcp, getNamespaces, getTools } from "../api";
import { ToolEditor } from "../components/ToolEditor";
import { Banner } from "../components/fields";
import { SafetyNotice } from "../components/notices";
import { resolved, useLoaded } from "../load";
import {
  NEW_TOOL,
  NO_TOOLS,
  TOOLS_RISK,
  TOOL_LABELS,
  YOUR_TOOLS,
} from "../texts";
import { splitTools } from "../tools";
import type {
  Effective,
  McpGrant,
  NamespaceRecord,
  ToolRecord,
} from "../types";
import type { TabProps } from "./props";

interface ToolsData {
  tools: ToolRecord[];
  grants: McpGrant[];
  namespaces: NamespaceRecord[];
  effective: Effective[]; // empty when D2 could not resolve inheritance
}

async function loadTools(): Promise<ToolsData> {
  const [tools, grants, namespaces, effective] = await Promise.all([
    getTools(),
    getMcp(),
    getNamespaces(),
    resolved(getEffective),
  ]);
  return { tools, grants, namespaces, effective: effective.value ?? [] };
}

function factory(tool: ToolRecord): string {
  const name = String(tool.data.factory ?? tool.name);
  const from = tool.data.factory_from;
  return tool.source !== null && typeof from === "string"
    ? `factory ${name} · ${from}`
    : `factory ${name}`;
}

/** The open editor: its session (a new one each time an editor is opened, so a saved new
 * tool keeps its editor), and the tool, by name (null: + New tool); saved holds a record
 * the Library has answered with but the list has not caught up to. */
interface Open {
  session: number;
  name: string | null;
  saved: ToolRecord | null;
}

export function ToolsTab(props: TabProps) {
  const loaded = useLoaded(loadTools, [props.rev], props.onBackendLost);
  const [open, setOpen] = useState<Open | null>(null);
  const data = loaded.data;
  const show = (name: string | null) =>
    setOpen({ session: (open?.session ?? 0) + 1, name, saved: null });

  const header = (
    <>
      <SafetyNotice cap={props.params.cap} variant="banner" />
      <div class="banner warning" role="note" data-testid="dr-tools-risk">
        <span aria-hidden="true">⚠ </span>
        {TOOLS_RISK}
      </div>
      {loaded.error && <Banner kind="error">{loaded.error.message}</Banner>}
    </>
  );
  if (!data) return <section class="tools">{header}</section>;

  if (open !== null) {
    const record =
      open.name === null
        ? null
        : (data.tools.find((t) => t.name === open.name) ?? open.saved);
    return (
      <section class="tools">
        {header}
        <button
          type="button"
          class="link"
          data-testid="dr-back"
          onClick={() => setOpen(null)}
        >
          {TOOL_LABELS.back}
        </button>
        <ToolEditor
          key={open.session}
          record={record}
          namespaces={data.namespaces}
          effective={data.effective}
          onSaved={(saved) => {
            setOpen({ ...open, name: saved.name, saved });
            loaded.reload();
          }}
          onDeleted={() => {
            setOpen(null);
            loaded.reload();
          }}
          onBackendLost={props.onBackendLost}
        />
      </section>
    );
  }

  const own = splitTools(data.tools, data.grants);
  return (
    <section class="tools">
      {header}
      <h3>{YOUR_TOOLS}</h3>
      <button
        type="button"
        data-testid="dr-tool-new"
        onClick={() => show(null)}
      >
        {NEW_TOOL}
      </button>
      {own.length === 0 && <p data-testid="dr-no-tools">{NO_TOOLS}</p>}
      {own.length > 0 && (
        <ul class="rows">
          {own.map((tool) => (
            <li>
              <button
                type="button"
                class="row"
                data-testid={`dr-tool-${tool.name}`}
                onClick={() => show(tool.name)}
              >
                <span class="name">{tool.name}</span>
                <span class="version">v{tool.version}</span>
                <span class="slash">{factory(tool)}</span>
                <span class="use-when">
                  granted in {tool.granted_in.join(", ") || "—"}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
