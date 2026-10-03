// The bodies of §5.2: every decomposition write carries use_when, hint and base_version.

import type { DecompositionBody } from "./api";
import { type Card, cardsToMessages } from "./cards";
import type { DecompositionRecord } from "./types";

export interface DecompositionDraft {
  mode: "cards" | "yaml";
  name: string;
  useWhen: string;
  hint: string;
  cards: Card[];
  yaml: string;
  baseVersion: number; // 0 for a new one
}

/** Card mode: JSON of {name, messages}; YAML mode: the text as written. */
export function draftYaml(draft: DecompositionDraft): string {
  if (draft.mode === "yaml") return draft.yaml;
  return JSON.stringify({
    name: draft.name,
    messages: cardsToMessages(draft.cards),
  });
}

function body(
  draft: DecompositionDraft,
  namespaces: readonly string[],
  baseVersion: number,
): DecompositionBody {
  return {
    yaml: draftYaml(draft),
    use_when: draft.useWhen.trim() || null,
    hint: draft.hint.trim() || null,
    namespaces: [...namespaces],
    base_version: baseVersion,
  };
}

/** {yaml, use_when, hint, namespaces: [picked], base_version: 0} */
export function createBody(
  draft: DecompositionDraft,
  picked: string,
): DecompositionBody {
  return body(draft, [picked], 0);
}

/** The head's namespaces first, the picked one once; base_version the head's. */
export function saveAsNextBody(
  draft: DecompositionDraft,
  head: DecompositionRecord,
  picked: string,
): DecompositionBody {
  const namespaces = head.namespaces.includes(picked)
    ? head.namespaces
    : [...head.namespaces, picked];
  return body(draft, namespaces, head.version);
}

/** namespaces: exactly the checked set; base_version the version opened. */
export function updateBody(
  draft: DecompositionDraft,
  namespaces: readonly string[],
): DecompositionBody {
  return body(draft, namespaces, draft.baseVersion);
}
