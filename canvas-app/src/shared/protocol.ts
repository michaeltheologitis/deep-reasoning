// The page ↔ frame contract (§4.3): the frame's URL parameters and the frame's two messages.

export const TAB_IDS = ["browse", "create", "namespaces", "tools"] as const;
export type TabId = (typeof TAB_IDS)[number];

export const TAB_TITLES: Readonly<Record<TabId, string>> = {
  browse: "Decompositions",
  create: "Create decomposition",
  namespaces: "Namespaces",
  tools: "Tools",
};

/** Every token the frame takes from Canvas, with Canvas's dark value, which the frame uses when
 * Canvas sends none (the standalone page). */
export const DEFAULT_THEME: Readonly<Record<string, string>> = {
  "--oh-surface": "#21252F",
  "--oh-surface-raised": "#2C313F",
  "--oh-surface-deep": "#05070A",
  "--oh-foreground": "#EEF2F7",
  "--oh-muted": "#A3B0C4",
  "--oh-text-secondary": "#C3CDDC",
  "--oh-text-dim": "#7E8A9E",
  "--oh-border": "#4B5468",
  "--oh-border-subtle": "#383F50",
  "--oh-border-input": "#4B5468",
  "--oh-color-primary": "#c9b974",
  "--oh-accent": "#c9b974",
  "--oh-accent-foreground": "#0B0E14",
  "--oh-danger": "#e76a5e",
  "--oh-success": "#a5e75e",
  "--oh-warning": "#c9b974",
  "--oh-interactive-hover": "#4B5468",
  "--oh-interactive-active": "#383F50",
  "--oh-focus": "#ffffff",
  "--oh-radius": "8px",
  "--oh-field-radius": "8px",
  "color-scheme": "dark",
  "font-family":
    '-apple-system, "SF Pro", BlinkMacSystemFont, "Segoe UI", "Roboto", "Ubuntu", sans-serif',
};
export const THEME_TOKENS: readonly string[] = Object.keys(DEFAULT_THEME);
export const MAX_THEME_VALUE_LENGTH = 200;
export const DEFAULT_SPEND_CAP = "5";

export type McpTransport = "stdio" | "http" | "sse";

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
