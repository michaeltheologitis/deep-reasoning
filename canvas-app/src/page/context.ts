// What only Canvas can read, for the frame's URL: the conversation's namespace, the spend cap, the theme.

import { DEFAULT_SPEND_CAP, THEME_TOKENS, safeTheme } from "../shared/protocol";
import type { AgentServerRequest } from "./host";

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
const DECIMAL = /^\d+(\.\d+)?$/;

/** The newest ACPSessionControlsEvent's option "namespace": its current value, and started when it
 * offers exactly one value. No event, no such option, or any failure → null. */
export async function readConversationNamespace(
  request: AgentServerRequest,
  conversationId: string | null,
): Promise<ConversationNamespace | null> {
  if (conversationId === null) return null;
  const path =
    `/api/conversations/${encodeURIComponent(conversationId)}/events/search` +
    "?kind=ACPSessionControlsEvent&sort_order=TIMESTAMP_DESC&limit=1";
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
