// Tools (§2.5; D4 extends it): the safety banner, always first, and the Library's tools.

import { getTools } from "../api";
import { Banner } from "../components/fields";
import { SafetyNotice } from "../components/notices";
import { useLoaded } from "../load";
import { NO_TOOLS } from "../texts";
import type { ToolRecord } from "../types";
import type { TabProps } from "./props";

function factory(tool: ToolRecord): string {
  const name = String(tool.data.factory ?? tool.name);
  const from = tool.data.factory_from;
  return tool.source !== null && typeof from === "string"
    ? `factory ${name} · ${from}`
    : `factory ${name}`;
}

export function ToolsTab(props: TabProps) {
  const tools = useLoaded(getTools, [props.rev], props.onBackendLost);
  return (
    <section class="tools">
      <SafetyNotice cap={props.params.cap} variant="banner" />
      {tools.error && <Banner kind="error">{tools.error.message}</Banner>}
      {tools.data?.length === 0 && <p data-testid="dr-no-tools">{NO_TOOLS}</p>}
      {tools.data && tools.data.length > 0 && (
        <ul class="rows">
          {tools.data.map((tool) => (
            <li class="row" data-testid={`dr-tool-${tool.name}`}>
              <span class="name">{tool.name}</span>
              <span class="version">v{tool.version}</span>
              <span class="slash">{factory(tool)}</span>
              <span class="use-when">
                granted in {tool.granted_in.join(", ") || "—"}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
