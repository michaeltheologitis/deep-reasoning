import { afterEach, describe, expect, it, vi } from "vitest";

import * as api from "../src/ui/api";
import { attempt, resolved } from "../src/ui/load";

/** D2's answer to an exception it has no handler for: Starlette's plain-text 500. */
const internalServerError = async () =>
  new Response("Internal Server Error", { status: 500 });

/** An effective view loaded as the tabs load it (useLoaded runs attempt over resolved): what the
 * tab is given, and what the footer is given. */
async function loadAsATab<T>(view: () => Promise<T>) {
  const lost: api.BackendUnavailable[] = [];
  const result = await attempt(
    () => resolved(view),
    (error) => lost.push(error),
  );
  return { result, lost };
}

afterEach(() => vi.unstubAllGlobals());

describe("resolved", () => {
  it.each<[string, () => Promise<unknown>]>([
    ["/effective", () => api.getEffective()],
    [
      "/namespaces/<n>/effective",
      () => api.getNamespaceEffective("course_advisor"),
    ],
  ])(
    "a 500 from %s reaches the backend-loss footer and gives the tab no refusal",
    async (_, view) => {
      vi.stubGlobal("fetch", internalServerError);
      const { result, lost } = await loadAsATab(view);
      expect(lost.map((error) => error.status)).toEqual([500]);
      expect(result).toEqual({ ok: false, error: null });
    },
  );
});
