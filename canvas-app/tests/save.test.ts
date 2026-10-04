import { describe, expect, it } from "vitest";

import { cardsToMessages, newDecompositionCards } from "../src/ui/cards";
import {
  type DecompositionDraft,
  createBody,
  draftYaml,
  saveAsNextBody,
  updateBody,
} from "../src/ui/save";
import type { DecompositionRecord } from "../src/ui/types";

const DRAFT: DecompositionDraft = {
  mode: "cards",
  name: "rank by prerequisites",
  useWhen: "  ordering courses by what they need first ",
  hint: "the task",
  cards: newDecompositionCards(),
  yaml: "",
  baseVersion: 0,
};
const HEAD = {
  name: "rank by prerequisites",
  slug: "rank-by-prerequisites",
  version: 2,
  namespaces: ["router", "course_advisor"],
} as DecompositionRecord;
const KEYS = ["yaml", "use_when", "hint", "namespaces", "base_version"];

describe("decomposition bodies", () => {
  it("are the cards as JSON, or the YAML as written", () => {
    expect(JSON.parse(draftYaml(DRAFT))).toEqual({
      name: DRAFT.name,
      messages: cardsToMessages(DRAFT.cards),
    });
    expect(draftYaml({ ...DRAFT, mode: "yaml", yaml: "name: x\n" })).toBe(
      "name: x\n",
    );
  });

  it("create in the picked namespace at version 0", () => {
    expect(createBody(DRAFT, "course_advisor")).toEqual({
      yaml: draftYaml(DRAFT),
      use_when: "ordering courses by what they need first",
      hint: "the task",
      namespaces: ["course_advisor"],
      base_version: 0,
    });
  });

  it.each([
    ["a namespace it is not in", "root", ["router", "course_advisor", "root"]],
    ["a namespace it is already in", "router", ["router", "course_advisor"]],
  ])(
    "save the next version keeping the head's namespaces, adding %s once",
    (_, picked, namespaces) => {
      expect(saveAsNextBody(DRAFT, HEAD, picked)).toMatchObject({
        namespaces,
        base_version: 2,
      });
    },
  );

  it("update with exactly the checked namespaces from the version opened", () => {
    const body = updateBody({ ...DRAFT, baseVersion: 3 }, ["root"]);
    expect(body).toMatchObject({ namespaces: ["root"], base_version: 3 });
  });

  it("always carry use_when and hint, null when blank, and nothing D2 does not read", () => {
    const blank = { ...DRAFT, useWhen: " ", hint: "" };
    for (const body of [
      createBody(blank, "root"),
      saveAsNextBody(blank, HEAD, "root"),
      updateBody(blank, []),
    ]) {
      expect(Object.keys(body)).toEqual(KEYS);
      expect(body.use_when).toBeNull();
      expect(body.hint).toBeNull();
    }
  });
});
