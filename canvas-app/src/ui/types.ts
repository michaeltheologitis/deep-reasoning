// D2's records (D2 §4.4, as built), as the HTTP API sends them.

export type Kind = "profile" | "namespace" | "decomposition" | "tool";

export interface Saved {
  version: number;
  rev: number;
  saved_at: string;
}

export interface ProfileRecord extends Saved {
  yaml: string;
  decompositions: string[];
  default_namespace: string;
  data: Record<string, unknown>;
}

export interface NamespaceRecord extends Saved {
  name: string;
  yaml: string;
  decompositions: string[];
  data: Record<string, unknown>;
}

export interface ChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

export interface DecompositionRecord extends Saved {
  name: string;
  slug: string;
  yaml: string;
  use_when: string | null;
  hint: string | null;
  namespaces: string[];
  top_level: boolean;
  data: {
    name: string;
    messages: ChatMessage[];
  };
}

export interface ToolRecord extends Saved {
  name: string;
  yaml: string;
  source: string | null;
  granted_in: string[];
  data: Record<string, unknown>;
}

export interface HistoryEntry extends Saved {
  kind: Kind;
  name: string;
  action: string;
  deleted: boolean;
  yaml: string | null;
  decompositions: string[] | null;
  slug: string | null;
  use_when: string | null;
  hint: string | null;
  source: string | null;
  deep_reasoner: string;
}

export interface Health {
  ok: boolean;
  rev: number;
  path: string;
  deep_reasoner: string;
  default_namespace: string;
}

export interface FieldError {
  loc: string;
  msg: string;
}

export interface Problem {
  kind: Kind;
  name: string;
  message: string;
}

export interface ValidationResult {
  ok: boolean;
  message: string | null;
  errors: FieldError[];
  warnings: string[];
  name: string | null;
  slug: string | null;
  yaml: string | null;
}

export interface Sourced {
  value: unknown;
  source: string | null;
}

export interface SuffixPart {
  source: string;
  text: string;
}

export interface EffectiveTool {
  name: string;
  source: string;
  defined: boolean;
}

export interface EffectiveDecomposition {
  name: string;
  slug: string;
  version: number;
  use_when: string | null;
  source: string;
}

export interface Effective {
  namespace: string;
  chain: string[];
  repl: Sourced;
  reasoner: Sourced;
  spawn: Sourced;
  system_suffix: SuffixPart[];
  tools: EffectiveTool[];
  vars: Record<string, Sourced>;
  decompositions: EffectiveDecomposition[];
}
