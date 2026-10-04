// The frame's sentences (§4.7), verbatim; tests assert these.

export const SAFETY = (cap: string) =>
  `deep_reasoner runs as you. It can read and change any file you can, and code it writes can find your model keys on this computer if it tries. Spend through the key proxy stops at $${cap} per conversation.`;
export const SAFETY_NO_CAP =
  "deep_reasoner runs as you. It can read and change any file you can, and code it writes can find your model keys on this computer if it tries. The key proxy is off for this agent (--no-key-proxy), so nothing caps what a conversation spends.";
export const UNDERSTAND = "I understand";
export const PROBLEMS = (n: number) =>
  n === 1 ? `${n} problem in the Library` : `${n} problems in the Library`;
export const BACKEND_LOST = (status: number) =>
  `The Library stopped answering (${status}).`;
export const RESTART = "Restart";
export const SESSION_ENDED = "The panel's session with the Library ended.";
export const RELOAD = "Reload";
export const NO_TOOLS = "No tools in the Library.";
