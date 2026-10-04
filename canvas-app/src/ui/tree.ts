// The namespace tree from dotted names: a.b under a; a top-level name under root.

export const ROOT = "root";

/** The namespaces name inherits from: root, then each dotted prefix, as deep_reasoner walks it. */
export function ancestors(name: string): string[] {
  if (name === ROOT) return [];
  const parts = name.split(".");
  return [
    ROOT,
    ...parts.slice(0, -1).map((_, i) => parts.slice(0, i + 1).join(".")),
  ];
}
