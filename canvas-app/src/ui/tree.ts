// The namespace tree from dotted names: a.b under a; a top-level name under root.

export interface NamespaceNode {
  name: string;
  children: NamespaceNode[];
}

export const ROOT = "root";

/** Rooted at "root"; order kept. A name whose parent is not listed hangs under root. */
export function namespaceTree(names: readonly string[]): NamespaceNode {
  const nodes = new Map<string, NamespaceNode>([
    [ROOT, { name: ROOT, children: [] }],
  ]);
  for (const name of names) {
    if (!nodes.has(name)) nodes.set(name, { name, children: [] });
  }
  for (const name of names) {
    if (name === ROOT) continue;
    const parent =
      nodes.get(name.slice(0, Math.max(name.lastIndexOf("."), 0))) ??
      nodes.get(ROOT)!;
    parent.children.push(nodes.get(name)!);
  }
  return nodes.get(ROOT)!;
}

/** The namespaces name inherits from: root, then each dotted prefix, as deep_reasoner walks it. */
export function ancestors(name: string): string[] {
  if (name === ROOT) return [];
  const parts = name.split(".");
  return [
    ROOT,
    ...parts.slice(0, -1).map((_, i) => parts.slice(0, i + 1).join(".")),
  ];
}
