// What only Canvas can read, for the frame's URL: the conversation's namespace, the spend cap, the theme,
// and (D4) Canvas's MCP servers; and the one thing it writes, the spend cap (TASK-65 D7).

import {
  DEFAULT_SPEND_CAP,
  type McpServerInfo,
  type McpTransport,
  THEME_TOKENS,
  safeTheme,
} from "../shared/protocol";
import { errorDetail } from "./backend";
import type { AgentServerRequest } from "./host";
import { CAP_NOT_SAVED, CAP_NO_PROXY, CAP_PROFILE_MISSING } from "./texts";

export interface ConversationNamespace {
  namespace: string;
  started: boolean;
}

interface ConfigOption {
  id?: unknown;
  current_value?: unknown;
  options?: unknown;
}

const PROFILE_PATH = "/api/agent-profiles/deep_reasoner";
const SPEND_CAP_FLAG = "--spend-cap-usd";
const NO_KEY_PROXY_FLAG = "--no-key-proxy";
const NOT_FOUND = 404;
const SETTINGS_PATH = "/api/settings";
const DECIMAL = /^\d+(\.\d+)?$/;
/** The events search matches an event's module-qualified class name, not the kind in its JSON. */
const ACP_SESSION_CONTROLS_EVENT_KIND =
  "openhands.sdk.event.acp_session_controls.ACPSessionControlsEvent";

/** The newest ACPSessionControlsEvent's option "namespace": its current value, and started when it
 * offers exactly one value. No event, no such option, or any failure → null. */
export async function readConversationNamespace(
  request: AgentServerRequest,
  conversationId: string | null,
): Promise<ConversationNamespace | null> {
  if (conversationId === null) return null;
  const path =
    `/api/conversations/${encodeURIComponent(conversationId)}/events/search` +
    `?kind=${ACP_SESSION_CONTROLS_EVENT_KIND}&sort_order=TIMESTAMP_DESC&limit=1`;
  try {
    const page = await request<{
      items?: { config_options?: ConfigOption[] }[];
    }>({ path });
    const option = page.items?.[0]?.config_options?.find(
      (o) => o.id === "namespace",
    );
    if (
      typeof option?.current_value !== "string" ||
      !Array.isArray(option.options)
    )
      return null;
    return {
      namespace: option.current_value,
      started: option.options.length === 1,
    };
  } catch {
    return null;
  }
}

/** spendCapFromArgs of the deep_reasoner profile's acp_args; any failure → "5". */
export async function readSpendCap(
  request: AgentServerRequest,
): Promise<string> {
  try {
    const answer = await request<{ profile?: { acp_args?: unknown } }>({
      path: PROFILE_PATH,
    });
    const args = answer.profile?.acp_args;
    return spendCapFromArgs(
      Array.isArray(args) ? args.filter((a) => typeof a === "string") : null,
    );
  } catch {
    return DEFAULT_SPEND_CAP;
  }
}

/** "off" with --no-key-proxy; else the decimal after --spend-cap-usd (or in --spend-cap-usd=v);
 * else "5". */
export function spendCapFromArgs(
  args: readonly string[] | null | undefined,
): string {
  if (!args) return DEFAULT_SPEND_CAP;
  if (args.includes("--no-key-proxy")) return "off";
  const at = args.indexOf("--spend-cap-usd");
  const value =
    at >= 0
      ? args[at + 1]
      : args
          .find((a) => a.startsWith("--spend-cap-usd="))
          ?.slice("--spend-cap-usd=".length);
  return value !== undefined && DECIMAL.test(value) ? value : DEFAULT_SPEND_CAP;
}

/** args with the --spend-cap-usd pair set to cap: the value after "--spend-cap-usd" replaced, or a
 * "--spend-cap-usd=v" element replaced by the pair at its place, or the pair appended. Every other
 * element keeps its place. null when args hold --no-key-proxy. */
export function withSpendCap(
  args: readonly string[],
  cap: string,
): string[] | null {
  if (args.includes(NO_KEY_PROXY_FLAG)) return null;
  const at = args.indexOf(SPEND_CAP_FLAG);
  if (at >= 0)
    return [...args.slice(0, at), SPEND_CAP_FLAG, cap, ...args.slice(at + 2)];
  const joined = args.findIndex((a) => a.startsWith(`${SPEND_CAP_FLAG}=`));
  if (joined >= 0)
    return [
      ...args.slice(0, joined),
      SPEND_CAP_FLAG,
      cap,
      ...args.slice(joined + 1),
    ];
  return [...args, SPEND_CAP_FLAG, cap];
}

export type SpendCapWrite =
  | { ok: true; cap: string }
  | { ok: false; message: string };

type Profile = Record<string, unknown> & { acp_args?: unknown };

/** GET PROFILE_PATH; withSpendCap(profile.acp_args ?? [], cap); POST PROFILE_PATH with the profile and
 * the new acp_args. Never throws: a 404 is CAP_PROFILE_MISSING, null args CAP_NO_PROXY, any other
 * failure CAP_NOT_SAVED with the error's message. */
export async function writeSpendCap(
  request: AgentServerRequest,
  cap: string,
): Promise<SpendCapWrite> {
  try {
    const answer = await request<{ profile: Profile }>({ path: PROFILE_PATH });
    const args = Array.isArray(answer.profile.acp_args)
      ? answer.profile.acp_args.filter((a) => typeof a === "string")
      : [];
    const acp_args = withSpendCap(args, cap);
    if (acp_args === null) return { ok: false, message: CAP_NO_PROXY };
    await request({
      method: "POST",
      path: PROFILE_PATH,
      body: { ...answer.profile, acp_args },
    });
    return { ok: true, cap };
  } catch (error) {
    const status = (error as { status?: unknown } | null)?.status;
    return {
      ok: false,
      message:
        status === NOT_FOUND
          ? CAP_PROFILE_MISSING
          : CAP_NOT_SAVED(errorDetail(error)),
    };
  }
}

/** Each of THEME_TOKENS as computed on element, kept when safe. */
export function readTheme(element: Element): Record<string, string> {
  const style = getComputedStyle(element);
  return safeTheme(
    Object.fromEntries(
      THEME_TOKENS.map((token) => [
        token,
        style.getPropertyValue(token).trim(),
      ]),
    ),
  );
}

type Entry = Record<string, unknown>;

const isEntry = (value: unknown): value is Entry =>
  typeof value === "object" && value !== null && !Array.isArray(value);
const nonEmpty = (value: unknown): value is string =>
  typeof value === "string" && value !== "";

/** stdio with a command, sse with a URL and transport "sse", else http with a URL (the bridge's
 * own rule); null when it has neither. */
function transportOf(server: Entry): McpTransport | null {
  if (nonEmpty(server.command)) return "stdio";
  if (!nonEmpty(server.url)) return null;
  return server.transport === "sse" ? "sse" : "http";
}

/** The names of the headers the bridge sends for a server's auth (the SDK's to_http_headers):
 * none for "none" and OAuth, which it does not forward. */
function authHeaderNames(auth: unknown): string[] {
  if (!isEntry(auth)) return [];
  switch (auth.strategy) {
    case "bearer":
    case "basic":
      return ["Authorization"];
    case "api_key":
      return [nonEmpty(auth.header_name) ? auth.header_name : "Authorization"];
    case "header":
      return isEntry(auth.headers) ? Object.keys(auth.headers) : [];
    default:
      return [];
  }
}

/** Each server of Canvas's MCP settings: its target, and the names (never the values) of its
 * environment variables and of the headers it is sent, its auth's included; forwarded when
 * enabled and in refs (null: all). */
export function mcpServersFromSettings(
  mcpConfig: Readonly<Record<string, unknown>>,
  refs: readonly string[] | null,
): McpServerInfo[] {
  return Object.entries(mcpConfig).flatMap(([name, value]) => {
    const server = isEntry(value) ? value : {};
    const transport = transportOf(server);
    if (transport === null) return [];
    const why_not =
      server.enabled === false
        ? ("disabled" as const)
        : refs !== null && !refs.includes(name)
          ? ("not_in_profile" as const)
          : null;
    return [
      {
        name,
        transport,
        command: transport === "stdio" ? (server.command as string) : null,
        args: Array.isArray(server.args)
          ? server.args.filter((a): a is string => typeof a === "string")
          : [],
        url: transport === "stdio" ? null : (server.url as string),
        env: isEntry(server.env) ? Object.keys(server.env) : [],
        headers: [
          ...new Set([
            ...(isEntry(server.headers) ? Object.keys(server.headers) : []),
            ...authHeaderNames(server.auth),
          ]),
        ],
        forwarded: why_not === null,
        why_not,
      },
    ];
  });
}

/** Canvas's settings, read without X-Expose-Secrets (every secret comes back redacted), and the
 * deep_reasoner profile's mcp_server_refs; either request failing → null. */
export async function readMcpServers(
  request: AgentServerRequest,
): Promise<McpServerInfo[] | null> {
  try {
    const [settings, profile] = await Promise.all([
      request<{ agent_settings?: { mcp_config?: unknown } }>({
        path: SETTINGS_PATH,
      }),
      request<{ profile?: { mcp_server_refs?: unknown } }>({
        path: PROFILE_PATH,
      }),
    ]);
    const config = settings.agent_settings?.mcp_config;
    const refs = profile.profile?.mcp_server_refs;
    return mcpServersFromSettings(
      isEntry(config) ? config : {},
      Array.isArray(refs)
        ? refs.filter((r): r is string => typeof r === "string")
        : null,
    );
  } catch {
    return null;
  }
}
