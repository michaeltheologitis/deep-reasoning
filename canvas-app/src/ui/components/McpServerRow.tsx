// One MCP server of Canvas's settings, or one grant (D4 §2.2): its target, the REPL name it is
// granted under, the namespaces it is granted to, and what the last conversation saw.

import { useEffect, useState } from "preact/hooks";

import { type McpGrantBody, deleteTool, putMcp } from "../api";
import { type OnBackendLost, attempt } from "../load";
import {
  INHERITED_ROW,
  MCP_AS,
  MCP_CHANGED,
  MCP_DISABLED,
  MCP_GONE,
  MCP_NAME_TAKEN,
  MCP_NOT_IN_PROFILE,
  MCP_NOT_SEEN,
  MCP_SEEN,
  MCP_SHIM_OLD,
  REMOVE,
  UPDATE,
} from "../texts";
import {
  type McpRow,
  type McpSnapshot,
  defaultToolName,
  grantSnapshot,
  inheritedGrants,
  snapshotOf,
} from "../tools";
import type { Effective, NamespaceRecord } from "../types";
import { NamespaceChecklist } from "./pickers";

export interface McpServerRowProps {
  row: McpRow;
  namespaces: readonly NamespaceRecord[];
  effective: readonly Effective[];
  takenNames: ReadonlySet<string>;
  onChanged: () => void;
  onBackendLost: OnBackendLost;
}

const STATE_NOTES = {
  disabled: MCP_DISABLED,
  not_in_profile: MCP_NOT_IN_PROFILE,
  gone: MCP_GONE,
} as const;

/** The server's name with every character outside [A-Za-z0-9_-] as "_" (Appendix B). */
export const mcpTestId = (server: string) =>
  server.replace(/[^A-Za-z0-9_-]/g, "_");

function target(snapshot: McpSnapshot): string {
  return snapshot.transport === "stdio"
    ? [snapshot.command ?? "", ...snapshot.args].join(" ")
    : (snapshot.url ?? "");
}

export function McpServerRow(props: McpServerRowProps) {
  const { row } = props;
  const id = mcpTestId(row.server);
  const [name, setName] = useState(() =>
    defaultToolName(row.server, props.takenNames),
  );
  const [error, setError] = useState<string | null>(null);
  // The ticks from the moment they are made until the stored grant shows them.
  const [ticking, setTicking] = useState<string[] | null>(null);
  const stored = row.grant?.granted_in.join("\n");
  useEffect(() => setTicking(null), [stored]);
  const snapshot = row.info ? snapshotOf(row.info) : grantSnapshot(row.grant!);
  const toolName = row.grant?.name ?? name;

  async function send(body: McpGrantBody): Promise<boolean> {
    const result = await attempt(
      () => putMcp(toolName, body),
      props.onBackendLost,
    );
    if (result.ok) setError(null);
    else if (result.error)
      setError(
        result.error.code === "conflict" && row.grant === null
          ? MCP_NAME_TAKEN(toolName)
          : result.error.message,
      );
    props.onChanged();
    return result.ok;
  }

  /** A first tick sends Canvas's settings; later ones resend the stored snapshot. */
  async function grantTo(grantedIn: string[]) {
    setTicking(grantedIn);
    const sent = await send(
      row.grant
        ? {
            ...grantSnapshot(row.grant),
            granted_in: grantedIn,
            base_version: row.grant.version,
          }
        : { ...snapshot, granted_in: grantedIn, base_version: 0 },
    );
    if (!sent) setTicking(null);
  }

  async function remove() {
    if (!row.grant) return;
    const grant = row.grant;
    const result = await attempt(
      () => deleteTool(grant.name, grant.version),
      props.onBackendLost,
    );
    if (!result.ok && result.error) setError(result.error.message);
    props.onChanged();
  }

  const update = () =>
    row.grant &&
    send({
      ...snapshot,
      granted_in: row.grant.granted_in,
      base_version: row.grant.version,
    });

  const inherited = Object.fromEntries(
    Object.entries(
      row.grant ? inheritedGrants(row.grant.name, props.effective) : {},
    ).map(([namespace, source]) => [namespace, INHERITED_ROW(source)]),
  );
  const note = row.state === "given" ? null : STATE_NOTES[row.state];
  const seen = row.grant?.seen ?? null;

  return (
    <li class="mcp" data-testid={`dr-mcp-${id}`}>
      <div class="mcp-head">
        <span class="name">{row.server}</span>
        <span class="version">{snapshot.transport}</span>
        <code class="slash">{target(snapshot)}</code>
        {row.grant ? (
          <span class="use-when">{MCP_AS(row.grant.name)}</span>
        ) : (
          <label class="as">
            {MCP_AS("")}
            <input
              value={name}
              aria-label={MCP_AS(name)}
              data-testid={`dr-mcp-name-${id}`}
              onInput={(event) => setName(event.currentTarget.value)}
            />
          </label>
        )}
      </div>
      {(note || row.changed || row.oldShim) && (
        <p class="note" data-testid={`dr-mcp-state-${id}`}>
          {note}
          {row.state === "gone" && (
            <button
              type="button"
              data-testid={`dr-mcp-remove-${id}`}
              onClick={remove}
            >
              {REMOVE}
            </button>
          )}
          {row.state !== "gone" && (row.changed || row.oldShim) && (
            <>
              {row.changed ? MCP_CHANGED : MCP_SHIM_OLD}{" "}
              <button
                type="button"
                data-testid={`dr-mcp-update-${id}`}
                onClick={update}
              >
                {UPDATE}
              </button>
            </>
          )}
        </p>
      )}
      <NamespaceChecklist
        namespaces={props.namespaces.map((n) => n.name)}
        checked={ticking ?? row.grant?.granted_in ?? []}
        inherited={inherited}
        testIdPrefix={`dr-mcp-grant-${id}`}
        onChange={grantTo}
      />
      {row.grant &&
        (seen ? (
          <details class="seen" data-testid={`dr-mcp-seen-${id}`}>
            <summary>
              {MCP_SEEN(seen.count, new Date(seen.at).toLocaleString())}
            </summary>
            <pre>{seen.told}</pre>
          </details>
        ) : (
          <p class="note" data-testid={`dr-mcp-seen-${id}`}>
            {MCP_NOT_SEEN}
          </p>
        ))}
      {error && (
        <p class="errors" role="alert">
          {error}
        </p>
      )}
    </li>
  );
}
