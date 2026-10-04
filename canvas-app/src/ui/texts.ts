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
  removeTurn: (turn: number) => `Remove turn ${turn}`,
  back: "← Decompositions",
  everyNamespace: "Every namespace's menu",
  notAttached: "Not attached",
} as const;

// D4's sentences (D4 §9.3), verbatim.
export const TOOLS_RISK =
  "Tools and MCP servers run as you, with your files and network: your tools inside the agent's process, a stdio MCP server as a program started for each conversation that can use it. Check runs your code too. Add only code and servers you trust.";
export const YOUR_TOOLS = "Your tools";
export const NEW_TOOL = "+ New tool";
export const MCP_SERVERS = "MCP servers (from Canvas's settings)";
export const CHECKING = "Checking… (building your tool in a separate process)";
export const SAVING_CHECKING = "Checking and saving…";
export const CHECK_BUILT = (seconds: string) =>
  `✓ builds (${seconds} s). The agent is told:`;
export const CANNOT_SAVE =
  "Fix this before saving: a tool that does not build stops every conversation from starting.";
export const SAVE_ANYWAY_NOTE =
  "Check could not build this tool here, where it has no secrets, no model and only its own folder. If it builds in a conversation, save it anyway; if it does not, no conversation will start until you fix it.";
export const SAVED_TOOL = (name: string, version: number) =>
  `✓ Saved '${name}' v${version}. New conversations build it; conversations already started keep the version they began with.`;
export const DELETE_TOOL_CONFIRM = (name: string) =>
  `Delete '${name}'? It is removed from every namespace; its versions stay in the Library's history.`;
export const TRY_LABEL =
  "Try (an expression Check evaluates with the tool bound)";
export const PRINTED = "It printed:";
export const NAME_FIXED =
  "how the agent calls it: a Python name, fixed once saved";
export const MCP_AS = (name: string) => `as ${name}`;
export const MCP_SEEN = (count: number, date: string) =>
  `${count} tools, as the conversation of ${date} saw them`;
export const MCP_NOT_SEEN =
  "Its tools are listed here after the first conversation that starts it.";
export const MCP_DISABLED =
  "Disabled in Canvas's MCP settings: not started until you enable it there.";
export const MCP_NOT_IN_PROFILE =
  "Not given to the deep_reasoner agent: its profile lists other MCP servers.";
export const MCP_GONE = "Granted, but no longer in Canvas's MCP settings.";
export const REMOVE = "Remove";
export const MCP_CHANGED =
  "Canvas's settings for this server changed since it was granted; an export still has the old ones.";
export const MCP_SHIM_OLD = "Granted by an older deep-reasoning.";
export const UPDATE = "Update";
export const MCP_SETTINGS_UNKNOWN =
  "Canvas's MCP settings could not be read; showing the servers already granted.";
export const MCP_NAME_TAKEN = (name: string) =>
  `A tool named '${name}' exists: choose another name.`;
export const MCP_EXPORT_NOTE =
  "An export keeps each server's command, arguments and URL, never its environment or header values: under dr each is read from an environment variable (env names as they are; a header from SERVER_HEADER).";
export const NEW_TOOL_SOURCE = `from deep_reasoner import Func


def make(client, params):
    def word_count(text: str) -> int:
        """Count the words in text."""
        return len(text.split())

    return Func(word_count, description="word_count(text) -> int: number of words in text.")
`;
export const TOOL_HELP =
  "A tool is a factory, make(client, params), that returns Func(value, description=…): the REPL binds value under the tool's name and the agent is told description. params are the block's other keys. Only this file is stored, so it cannot import a file beside it. Call models through client, the conversation's own, never with a key of your own. Read secrets and files when the tool is called, not when it is built: it is built at the start of every conversation and by Check, which has neither. The factory is not told where the config is (deep_reasoner passes no config_path to factory_from tools). A kg tool's saved layers record document paths against the config folder of the conversation that saved them.";
export const TOOL_LABELS = {
  name: "Name",
  block: "Block",
  blockNote:
    "YAML: the factory's name and its parameters (factory_from is the Library's)",
  source: "Source",
  check: "Check",
  grantedIn: "Granted in",
  help: "How tools work",
  tools: "Tools",
  back: "← Tools",
} as const;
