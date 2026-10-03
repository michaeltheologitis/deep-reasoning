// The page ↔ frame contract (§4.3): the frame's URL parameters and the frame's two messages.

export const APP_NAME = "dr-library";
export const TAB_IDS = ["browse", "create", "namespaces", "tools"] as const;
export type TabId = (typeof TAB_IDS)[number];

export const TAB_TITLES: Readonly<Record<TabId, string>> = {
  browse: "Decompositions",
  create: "Create decomposition",
  namespaces: "Namespaces",
  tools: "Tools",
};

export const THEME_TOKENS: readonly string[] = [
  "--oh-surface",
  "--oh-surface-raised",
  "--oh-surface-deep",
  "--oh-foreground",
  "--oh-muted",
  "--oh-text-secondary",
  "--oh-text-dim",
  "--oh-border",
  "--oh-border-subtle",
  "--oh-border-input",
  "--oh-color-primary",
  "--oh-accent",
  "--oh-accent-foreground",
  "--oh-danger",
  "--oh-success",
  "--oh-warning",
  "--oh-interactive-hover",
  "--oh-interactive-active",
  "--oh-focus",
  "--oh-radius",
  "--oh-field-radius",
  "color-scheme",
  "font-family",
];
export const MAX_THEME_VALUE_LENGTH = 200;
export const DEFAULT_SPEND_CAP = "5";

export type McpTransport = "stdio" | "http" | "sse";
export const MCP_TRANSPORTS: readonly McpTransport[] = ["stdio", "http", "sse"];

/** One server of Canvas's MCP settings, as the Tools tab needs it: never a secret's value. */
export interface McpServerInfo {
  name: string; // the key in Canvas's MCP settings
  transport: McpTransport;
  command: string | null;
  args: string[];
  url: string | null;
  env: string[]; // names only
  headers: string[]; // names only
  forwarded: boolean; // enabled, and in the deep_reasoner profile's mcp_server_refs (or refs null)
  why_not: "disabled" | "not_in_profile" | null;
}

export interface FrameParams {
  tab: TabId;
  /** Canvas's origin; null on the standalone page. */
  parent: string | null;
  /** The open conversation's namespace, when its agent reported one. */
  namespace: string | null;
  /** The namespace is fixed: the conversation's first message was sent. */
  started: boolean;
  /** USD as the profile states it, or "off". */
  cap: string;
  /** A decomposition's slug (browse) or a namespace's name (namespaces). */
  focus: string | null;
  /** Token → value; only values that pass isSafeThemeValue. */
  theme: Readonly<Record<string, string>>;
  /** D4: Canvas's MCP servers, for the Tools tab; null when unread or unreadable. */
  mcp: readonly McpServerInfo[] | null;
}

export type FrameMessage =
  | {
      type: "dr-library/select-tab";
      tab: TabId;
      focus: string | null;
    }
  | {
      type: "dr-library/reload";
    };

const SAFE_THEME_VALUE = /^[#\w\s(),.%'"-]*$/;
const CAP = /^(off|\d+(\.\d+)?)$/;

export function isTabId(value: unknown): value is TabId {
  return (TAB_IDS as readonly unknown[]).includes(value);
}

/** At most MAX_THEME_VALUE_LENGTH characters of [#\w\s(),.%'"-], and no url(. */
export function isSafeThemeValue(value: string): boolean {
  return (
    value.length <= MAX_THEME_VALUE_LENGTH &&
    SAFE_THEME_VALUE.test(value) &&
    !/url\(/i.test(value)
  );
}

/** The listed tokens whose values are safe; everything else is dropped. */
export function safeTheme(
  theme: Readonly<Record<string, unknown>>,
): Record<string, string> {
  const kept: Record<string, string> = {};
  for (const token of THEME_TOKENS) {
    const value = theme[token];
    if (typeof value === "string" && value !== "" && isSafeThemeValue(value)) {
      kept[token] = value;
    }
  }
  return kept;
}

/** "?tab=…&…" in a fixed order; empty values omitted. */
export function frameSearch(params: FrameParams): string {
  const search = new URLSearchParams({ tab: params.tab });
  if (params.parent) search.set("parent", params.parent);
  if (params.namespace) search.set("namespace", params.namespace);
  if (params.started) search.set("started", "1");
  search.set("cap", params.cap);
  if (params.focus) search.set("focus", params.focus);
  if (Object.keys(params.theme).length > 0)
    search.set("theme", JSON.stringify(params.theme));
  if (params.mcp !== null) search.set("mcp", JSON.stringify(params.mcp));
  return `?${search.toString()}`;
}

function origin(value: string | null): string | null {
  if (!value) return null;
  try {
    const url = new URL(value);
    return /^https?:$/.test(url.protocol) && url.origin === value
      ? value
      : null;
  } catch {
    return null;
  }
}

function theme(value: string | null): Record<string, string> {
  if (!value) return {};
  try {
    const parsed: unknown = JSON.parse(value);
    return parsed && typeof parsed === "object" && !Array.isArray(parsed)
      ? safeTheme(parsed as Record<string, unknown>)
      : {};
  } catch {
    return {};
  }
}

const isStrings = (value: unknown): value is string[] =>
  Array.isArray(value) && value.every((v) => typeof v === "string");
const isText = (value: unknown): value is string | null =>
  value === null || typeof value === "string";

function isMcpServerInfo(value: unknown): value is McpServerInfo {
  const server = value as Record<string, unknown> | null;
  return (
    typeof server?.name === "string" &&
    (MCP_TRANSPORTS as readonly unknown[]).includes(server.transport) &&
    isText(server.command) &&
    isStrings(server.args) &&
    isText(server.url) &&
    isStrings(server.env) &&
    isStrings(server.headers) &&
    typeof server.forwarded === "boolean" &&
    [null, "disabled", "not_in_profile"].includes(server.why_not as string)
  );
}

/** A JSON list of servers; entries of another shape are dropped; anything else is null. */
function mcp(value: string | null): McpServerInfo[] | null {
  if (value === null) return null;
  try {
    const parsed: unknown = JSON.parse(value);
    return Array.isArray(parsed) ? parsed.filter(isMcpServerInfo) : null;
  } catch {
    return null;
  }
}

/** Tolerant: an unknown or missing value takes its default, so a bad URL still shows a page.
 * On the standalone page (no parent window) parent is always null. */
export function readFrameParams(
  search: string,
  standalone: boolean,
): FrameParams {
  const query = new URLSearchParams(search);
  const tab = query.get("tab");
  const cap = query.get("cap");
  return {
    tab: isTabId(tab) ? tab : "browse",
    parent: standalone ? null : origin(query.get("parent")),
    namespace: query.get("namespace") || null,
    started: query.get("started") === "1",
    cap: cap !== null && CAP.test(cap) ? cap : DEFAULT_SPEND_CAP,
    focus: query.get("focus") || null,
    theme: theme(query.get("theme")),
    mcp: mcp(query.get("mcp")),
  };
}

export function isFrameMessage(value: unknown): value is FrameMessage {
  if (!value || typeof value !== "object") return false;
  const message = value as Record<string, unknown>;
  if (message.type === "dr-library/reload")
    return Object.keys(message).length === 1;
  return (
    message.type === "dr-library/select-tab" &&
    isTabId(message.tab) &&
    (message.focus === null || typeof message.focus === "string")
  );
}
