// The frame's sentences (§4.7), verbatim; tests assert these.

export const SAFETY = (cap: string) =>
  `deep_reasoner runs as you. It can read and change any file you can, and code it writes can find your model keys on this computer if it tries. Spend through the key proxy stops at $${cap} per conversation.`;
export const SAFETY_NO_CAP =
  "deep_reasoner runs as you. It can read and change any file you can, and code it writes can find your model keys on this computer if it tries. The key proxy is off for this agent (--no-key-proxy), so nothing caps what a conversation spends.";
export const UNDERSTAND = "I understand";
export const SAVED_STARTED = (
  name: string,
  version: number,
  namespace: string,
) =>
  `✓ Saved '${name}' v${version} in ${namespace}. New conversations in ${namespace} use it; this conversation does not, because its run was built at its first message.`;
export const SAVED = (
  name: string,
  version: number,
  namespace: string,
  slug: string,
) =>
  `✓ Saved '${name}' v${version} in ${namespace}. New conversations in ${namespace} use it and offer it as /${slug}; a conversation that has already started keeps the run it began with.`;
export const SAVED_EDIT = (name: string, version: number) =>
  `✓ Saved '${name}' v${version}. New conversations use it; conversations already started keep the version they began with.`;
export const SHOW_IN_DECOMPOSITIONS = "Show in Decompositions";
export const EXISTS = (
  name: string,
  version: number,
  namespaces: readonly string[],
) =>
  `'${name}' already exists (v${version}, in ${namespaces.length ? namespaces.join(", ") : "no namespace"}).`;
export const SAVE_AS_NEXT = (next: number) => `Save mine as v${next}`;
export const RENAME = "Rename";
export const RELOAD_ENTRY = "Reload";
export const SAVE_OVER = "Save over it";
export const SAVE_ANYWAY = "Save anyway";
export const CANCEL = "Cancel";
export const NAME_REQUIRED = "Give the decomposition a name.";
export const OUTPUT_NOTE = "written by you, not run";
export const RAW_NOTE =
  "Shown as written: this message is not a task, a think-and-code step or an observation.";
export const YAML_SYNTAX = (message: string) =>
  `This is not valid YAML: ${message}`;
export const YAML_NOT_DECOMPOSITION =
  "To edit it as cards, the YAML must be a mapping with a name and a list of messages, each with a role and a content.";
export const DELETE_CONFIRM = (name: string) =>
  `Delete '${name}'? It is removed from every namespace; its versions stay in the Library's history.`;
export const DELETE_NAMESPACE_CONFIRM = (name: string) =>
  `Delete namespace '${name}'? Its decompositions stay in the Library.`;
export const INHERITED = (source: string) => `Inherited from ${source}`;
export const INHERITED_ROW = (source: string) => `inherited from ${source}`;
export const OVERRIDDEN = "Overridden here";
export const SET_HERE = "Set here";
export const GRANTED_HERE = "Granted here";
export const ATTACHED_HERE = "Attached here";
export const FROM_PROFILE = "From the run settings";
export const NOT_SET = "Not set: deep_reasoner's default";
export const ANY_NAMESPACE = "Any namespace";
export const UNDEFINED_TOOL = "not a tool in the Library";
export const DEFAULT_BADGE = "New conversations start here";
export const MAKE_DEFAULT = "Start new conversations here";
export const EFFECTIVE_FAILED = (message: string) =>
  `Inherited decompositions cannot be shown: ${message} Showing each decomposition where it is attached.`;
export const PROBLEMS = (n: number) =>
  n === 1 ? `${n} problem in the Library` : `${n} problems in the Library`;
export const BACKEND_LOST = (status: number) =>
  `The Library stopped answering (${status}).`;
export const RESTART = "Restart";
export const SESSION_ENDED = "The panel's session with the Library ended.";
export const RELOAD = "Reload";
export const NO_TOOLS = "No tools in the Library.";
export const DISCARD_DRAFT = "Discard draft";

export const LABELS = {
  name: "Name",
  useWhen: "Use when",
  hint: "Hint",
  hintNote: "what the slash command asks for; optional",
  namespace: "Namespace",
  task: "task",
  think: "think",
  code: "code",
  output: "observation",
  addTurn: "+ turn",
  viewYaml: "View YAML",
  editYaml: "Edit YAML",
  editCards: "Edit as cards",
  saveTo: (namespace: string) => `Save to ${namespace}`,
  save: "Save",
  delete: "Delete",
  attachedTo: "Attached to",
  alsoUsedIn: (namespace: string) => `also used in ${namespace} (inherited)`,
  override: "Override",
  edit: "Edit",
  reset: "Reset",
  addVariable: "Add variable",
  addNamespace: "Add namespace",
  deleteNamespace: "Delete namespace",
  runSettings: "Run settings",
  addSetting: "Add setting",
  attach: "Attach…",
  detach: "Detach",
  remove: "✕",
  back: "← Decompositions",
  everyNamespace: "Every namespace's menu",
  notAttached: "Not attached",
} as const;
