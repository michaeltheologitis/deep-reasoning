import { describe, expect, it } from "vitest";

import { ancestors } from "../src/ui/tree";

describe("ancestors", () => {
  it.each([
    ["root", []],
    ["router", ["root"]],
    ["router.archive.old", ["root", "router", "router.archive"]],
  ])("of %s are %j, as deep_reasoner chains them", (name, chain) => {
    expect(ancestors(name)).toEqual(chain);
  });
});
