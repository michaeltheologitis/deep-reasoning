import { describe, expect, it } from "vitest";

import { type NamespaceNode, namespaceTree } from "../src/ui/tree";

const leaf = (name: string, ...children: NamespaceNode[]): NamespaceNode => ({
  name,
  children,
});

describe("namespaceTree", () => {
  it("puts top-level names under root and dotted names under their parent, in order", () => {
    expect(
      namespaceTree([
        "root",
        "router",
        "course_advisor",
        "router.archive",
        "router.archive.old",
        "router.next",
      ]),
    ).toEqual(
      leaf(
        "root",
        leaf(
          "router",
          leaf("router.archive", leaf("router.archive.old")),
          leaf("router.next"),
        ),
        leaf("course_advisor"),
      ),
    );
  });

  it("is rooted at root even when root is not listed", () => {
    expect(namespaceTree(["a"])).toEqual(leaf("root", leaf("a")));
  });

  it("puts a name whose parent is missing under root", () => {
    expect(namespaceTree(["root", "a.b"])).toEqual(leaf("root", leaf("a.b")));
  });
});
