// The Library panel: the decompositions, namespaces, tools and data every run draws on. Mock data; an added decomposition lives in memory.
// It draws with app.js's element(), caret() and fetchJson(), which load before this module.
const DATA_URL = "data/library.json";
const LIBRARY_FILE = "library.sqlite";
const TABS = ["Decompositions", "Namespaces", "Tools", "Data"];
const ROOT = "root";
const ROLES = ["user", "assistant", "system"];
const DECOMPOSITION_KEYS = ["name", "messages"];
const MESSAGE_KEYS = ["role", "content"];
const INDENT = "  ";
const CHECK_DELAY_MS = 300;
const MAX_FILE_BYTES = 1_000_000;
// the shape of the generated decompositions, small enough to edit in place
const TEMPLATE = `name: count the open tickets
messages:
- role: user
  content: How many tickets are still open?
- role: assistant
  content: |
    <think>Count the tickets whose status is open, and print the count to check it.</think>
    <repl>
    print(sum(t["status"] == "open" for t in tickets))
    </repl>
- role: user
  content: |
    <observation>
    12
    </observation>
- role: assistant
  content: |
    <think>12 tickets are open. Answer with the count.</think>
    <repl>
    FinalAnswer(12)
    </repl>
`;

const panel = document.getElementById("library");
const toggleButton = document.getElementById("library-toggle");
const opened = new Set();
let library = null;
let problem = null;
let tab = TABS[0];
let checkTimer = null;

const dot = () => element("span", { class: "lib-dot", "aria-hidden": "true" }, "·");
const namespaceNamed = (name) => library.namespaces.find((namespace) => namespace.name === name);
const decompositionKey = (namespace, name) => `d:${namespace}:${name}`;

const body = element("div", { class: "lib-body", id: "library-body", role: "tabpanel" });
const tabButtons = TABS.map((name) =>
  element("button", { type: "button", role: "tab", class: "lib-tab", id: `library-tab-${name.toLowerCase()}`, "aria-controls": body.id, onclick: () => selectTab(name) }, name),
);
panel.append(
  element(
    "header",
    { class: "lib-head" },
    element("h2", { class: "lib-title" }, "Library", element("span", { class: "lib-filename" }, ` · ${LIBRARY_FILE}`)),
    element("button", { type: "button", class: "lib-close", "aria-label": "Close the Library", onclick: () => setOpen(false) }, "×"),
  ),
  element("div", { class: "lib-tabs", role: "tablist", "aria-label": "Library", onkeydown: arrowTabs }, tabButtons.flatMap((button, i) => (i ? [dot(), button] : [button]))),
  body,
);

// the add form is built once, so a draft survives re-renders
const addToggle = element("button", { type: "button", class: "lib-action", "aria-expanded": "false", "aria-controls": "lib-add-form", onclick: () => (addForm.hidden ? openForm() : closeForm()) }, "+ Add decomposition");
const yamlInput = element(
  "textarea",
  { id: "lib-yaml", class: "lib-yaml", wrap: "off", spellcheck: "false", autocapitalize: "off", "aria-describedby": "lib-problems", oninput: edited, onkeydown: indentOnTab },
  TEMPLATE,
);
const fileInput = element("input", { type: "file", accept: ".yaml,.yml", onchange: readFile });
const picker = element("select", { id: "lib-namespace", onchange: check });
const problemList = element("div", { id: "lib-problems", class: "lib-problems", "aria-live": "polite" });
const addButton = element("button", { type: "submit", class: "lib-action lib-primary" }, "Add");
const addForm = element(
  "form",
  { id: "lib-add-form", class: "children lib-open lib-form", hidden: true, onsubmit: addDecomposition },
  element("div", { class: "lib-form-line" }, element("label", { for: yamlInput.id }, "YAML"), element("label", { class: "lib-action lib-file-pick" }, "or choose a .yaml file", fileInput)),
  yamlInput,
  element("div", { class: "lib-form-line" }, element("label", { for: picker.id }, "namespace"), picker),
  problemList,
  element("div", { class: "lib-actions" }, addButton, element("button", { type: "button", class: "lib-action", onclick: closeForm }, "Cancel")),
  element("p", { class: "lib-note" }, "the prototype doesn't save; a reload forgets it"),
);
const confirmation = element("p", { class: "lib-confirm", role: "status" });
const addSection = element("section", { class: "lib-add" }, addToggle, addForm, confirmation);

function openForm() {
  addForm.hidden = false;
  addToggle.setAttribute("aria-expanded", "true");
  confirmation.textContent = "";
  fitEditor();
  check();
  yamlInput.focus();
}

function closeForm() {
  clearTimeout(checkTimer);
  addForm.hidden = true;
  addToggle.setAttribute("aria-expanded", "false");
  addForm.reset();
  showProblems([]);
  addToggle.focus();
}

function edited() {
  fitEditor();
  clearTimeout(checkTimer);
  checkTimer = setTimeout(check, CHECK_DELAY_MS);
}

function fitEditor() {
  yamlInput.style.height = "auto";
  yamlInput.style.height = `${yamlInput.scrollHeight + yamlInput.offsetHeight - yamlInput.clientHeight}px`;
}

// Tab indents; Shift+Tab still leaves the editor, and Esc closes the panel with the draft kept.
function indentOnTab(e) {
  if (e.key !== "Tab" || e.shiftKey || e.altKey || e.ctrlKey || e.metaKey) return;
  e.preventDefault();
  document.execCommand("insertText", false, INDENT);
}

async function readFile() {
  const [file] = fileInput.files;
  fileInput.value = "";
  if (!file) return;
  if (file.size > MAX_FILE_BYTES) {
    showProblems([`${file.name} is too big to be a decomposition's YAML; choose its .yaml file.`]);
    return;
  }
  yamlInput.value = await file.text();
  fitEditor();
  check();
}

function check() {
  clearTimeout(checkTimer);
  const found = problems(yamlInput.value, namespaceNamed(picker.value));
  showProblems(found);
  addButton.disabled = found.length > 0;
  return found;
}

// unchanged problems are left alone, so the live region doesn't repeat them at every pause in typing
function showProblems(found) {
  if ([...problemList.children].map((line) => line.textContent).join("\n") === found.join("\n")) return;
  problemList.replaceChildren(...found.map((text) => element("p", {}, text)));
}

function addDecomposition(e) {
  e.preventDefault();
  if (check().length) return;
  const namespace = namespaceNamed(picker.value);
  const { name } = jsyaml.load(yamlInput.value);
  namespace.decompositions.push({ name, yaml: yamlInput.value.trimEnd() });
  const key = decompositionKey(namespace.name, name);
  opened.add(key);
  closeForm();
  render();
  const row = body.querySelector(`[data-key="${CSS.escape(key)}"]`);
  row.focus({ preventScroll: true });
  row.parentElement.scrollIntoView({ block: "nearest" });
  confirmation.textContent = `Added "${name}" to ${namespace.name}`;
}

// the YAML is checked as deep_reasoner's Decomposition model would: name, messages, nothing else
const isMapping = (value) => Object.prototype.toString.call(value) === "[object Object]";
const quoted = (keys) => keys.map((key) => `"${key}"`).join(", ");

function problems(text, namespace) {
  if (!window.jsyaml) return ["The YAML reader (js-yaml, from cdnjs) didn't load; check the connection and reload."];
  if (!text.trim()) return ["Write the decomposition's YAML above, or choose a .yaml file."];
  let parsed;
  try {
    parsed = jsyaml.load(text);
  } catch (error) {
    const where = error.mark ? `line ${error.mark.line + 1}: ` : "";
    return [`The YAML doesn't parse (${where}${error.reason ?? error.message}). Check the indentation and quoting on that line.`];
  }
  if (!isMapping(parsed)) return ["The YAML should be a mapping: a name: line, then messages:, as in the template."];
  const extra = Object.keys(parsed).filter((key) => !DECOMPOSITION_KEYS.includes(key));
  return [
    extra.length > 0 && `Remove ${quoted(extra)}: only name and messages go in the YAML; pick the namespace below.`,
    nameProblem(parsed.name, namespace),
    ...messageProblems(parsed.messages),
  ].filter(Boolean);
}

function nameProblem(name, namespace) {
  if (name === undefined) return 'Add a name: line, like "name: count the open tickets".';
  if (typeof name !== "string" || !name.trim()) return 'The name should be text, like "name: count the open tickets".';
  if (namespace.decompositions.some((each) => each.name === name)) return `${namespace.name} already has "${name}"; rename it, or pick another namespace.`;
  return null;
}

function messageProblems(messages) {
  if (messages === undefined) return ["Add messages: a list of turns, each with a role and content, as in the template."];
  if (!Array.isArray(messages) || !messages.length) return ['messages should be a list of at least one turn, each starting "- role:".'];
  return messages.flatMap((message, i) => turnProblems(message, `Message ${i + 1}`));
}

function turnProblems(message, label) {
  if (!isMapping(message)) return [`${label} should be a mapping with role and content.`];
  const extra = Object.keys(message).filter((key) => !MESSAGE_KEYS.includes(key));
  const { role, content } = message;
  return [
    extra.length > 0 && `${label}: remove ${quoted(extra)}; a message holds only role and content.`,
    !ROLES.includes(role) && `${label}: role should be user, assistant or system${role === undefined ? "" : `, not ${JSON.stringify(role)}`}.`,
    content === undefined && `${label} needs content: the turn's text.`,
    content !== undefined && typeof content !== "string" && `${label}: content should be text; quote it, or write "content: |" with the text indented below.`,
  ].filter(Boolean);
}

function disclosure(key, head, content) {
  const open = opened.has(key);
  return element(
    "div",
    { class: "lib-entry" },
    element("button", { type: "button", class: "row", "aria-expanded": String(open), "data-key": key, onclick: () => flip(key) }, caret(open), head),
    open && element("div", { class: "children lib-open" }, content()),
  );
}

// one span, so a long row cuts the detail before the name
function rowHead(name, detail, meta) {
  return [element("span", { class: "lib-name" }, name, " ", element("span", { class: "lib-detail" }, detail)), element("span", { class: "meta" }, meta)];
}

function fields(rows) {
  return element("dl", { class: "lib-fields" }, rows.map(([label, value]) => [element("dt", {}, label), element("dd", {}, value)]));
}

function sourced(items) {
  if (!items.length) return "—";
  return items.map(({ value, source, here }) => {
    const label = element("span", { class: `lib-source ${here ? "here" : ""}` }, source);
    if (value.includes("\n")) return element("div", { class: "lib-item lib-block" }, element("pre", { class: "code lib-doc" }, value), label);
    return element("div", { class: "lib-item" }, value, " ", label);
  });
}

const group = (title, rows) => element("section", { class: "lib-group" }, element("h3", { class: "lib-label" }, title), element("div", { class: "lib-rows" }, rows));

function decompositionRow(namespace, { name, yaml }) {
  return disclosure(decompositionKey(namespace, name), element("span", { class: "lib-name" }, name), () => element("pre", { class: "code lib-pre" }, yaml));
}

function renderDecompositions() {
  const groups = library.namespaces
    .filter((namespace) => namespace.decompositions.length)
    .map((namespace) => {
      const title = namespace.name === ROOT ? `${ROOT} · every namespace inherits these` : namespace.name;
      return group(title, namespace.decompositions.map((each) => decompositionRow(namespace.name, each)));
    });
  return [addSection, ...groups];
}

const namespaceFields = (list) => fields(list.map(({ label, items }) => [label, sourced(items)]));

function chain(name) {
  const parts = name === ROOT ? [] : name.split(".");
  return [ROOT, ...parts.map((_, i) => parts.slice(0, i + 1).join("."))];
}

// a namespace's decompositions and its ancestors', as deep_reasoner resolves them
function decompositionsField(name) {
  const levels = new Map();
  for (const level of chain(name)) {
    for (const each of namespaceNamed(level).decompositions) levels.set(each.name, level);
  }
  const items = [...levels].map(([value, level]) => ({ value, source: level === name ? "attached here" : `inherited from ${level}`, here: level === name }));
  return { label: "Decompositions", items };
}

function renderNamespaces() {
  const tree = library.namespaces.map((namespace) => {
    const star = namespace.name === library.default_namespace && element("span", { class: "lib-star" }, "★ new chats start here");
    const head = [element("span", { class: "lib-name" }, namespace.name), star];
    const content = () => namespaceFields([...namespace.fields, decompositionsField(namespace.name)]);
    return element("div", { style: `--depth: ${namespace.depth}` }, disclosure(`n:${namespace.name}`, head, content));
  });
  const run = disclosure("n:run", element("span", { class: "lib-name" }, "Run settings"), () => namespaceFields(library.run_settings));
  return [element("div", { class: "lib-rows lib-tree" }, run, tree)];
}

function renderTool(tool) {
  return [
    fields([
      ["Factory", tool.factory],
      ["File", tool.file],
      ["Defined in", tool.defined_in ?? "the deep_reasoner package"],
      ["Granted in", tool.granted_in.join(", ") || "no namespace"],
    ]),
    tool.config && element("pre", { class: "code lib-pre" }, tool.config),
    element("pre", { class: `code ${tool.description.includes("\n") ? "lib-pre" : "lib-doc"}` }, tool.description),
  ];
}

function renderTools() {
  const rows = library.tools.map((tool) => {
    const granted = tool.granted_in.length ? `granted in ${tool.granted_in.join(", ")}` : "not granted";
    return disclosure(`t:${tool.name}`, rowHead(tool.name, granted, tool.defined_in ? null : "built-in"), () => renderTool(tool));
  });
  return [element("div", { class: "lib-rows" }, rows)];
}

function dataTable({ name, columns, rows }) {
  const cell = (tag, text) => element(tag, tag === "th" ? { scope: "col" } : {}, element("div", {}, text));
  return element(
    "div",
    { class: "lib-table", role: "region", tabindex: "0", "aria-label": `${name}, scrolls sideways` },
    element("table", {}, element("thead", {}, element("tr", {}, columns.map((column) => cell("th", column)))), element("tbody", {}, rows.map((row) => element("tr", {}, row.map((text) => cell("td", text)))))),
  );
}

function renderData() {
  return library.data.map((section, sectionIndex) =>
    group(
      section.title,
      section.items.map((entry, entryIndex) =>
        disclosure(`v:${sectionIndex}:${entryIndex}`, rowHead(entry.name, entry.where, entry.summary), () => (entry.rows ? dataTable(entry) : element("p", { class: "lib-note" }, entry.note))),
      ),
    ),
  );
}

const RENDERERS = { Decompositions: renderDecompositions, Namespaces: renderNamespaces, Tools: renderTools, Data: renderData };

function render() {
  for (const button of tabButtons) button.setAttribute("aria-selected", String(button.textContent === tab));
  body.setAttribute("aria-labelledby", `library-tab-${tab.toLowerCase()}`);
  const focused = document.activeElement?.dataset?.key;
  if (problem || !library) body.replaceChildren(element("p", { class: "lib-note" }, problem ?? "Loading the Library…"));
  else body.replaceChildren(...RENDERERS[tab]());
  if (focused) body.querySelector(`[data-key="${CSS.escape(focused)}"]`)?.focus();
}

function flip(key) {
  if (opened.has(key)) opened.delete(key);
  else opened.add(key);
  render();
}

function selectTab(name) {
  tab = name;
  render();
  body.scrollTop = 0;
}

function arrowTabs(e) {
  const step = { ArrowRight: 1, ArrowLeft: -1 }[e.key];
  if (!step) return;
  selectTab(TABS[(TABS.indexOf(tab) + step + TABS.length) % TABS.length]);
  tabButtons[TABS.indexOf(tab)].focus();
}

function setOpen(open) {
  if (!open && panel.contains(document.activeElement)) toggleButton.focus();
  panel.hidden = !open;
  toggleButton.setAttribute("aria-expanded", String(open));
  if (!open) return;
  render();
  tabButtons[TABS.indexOf(tab)].focus();
}

async function load() {
  try {
    library = await fetchJson(DATA_URL);
    picker.append(...library.namespaces.map(({ name }) => element("option", { value: name, selected: name === ROOT }, name)));
  } catch (error) {
    problem = `Could not load the Library (${error.message}).`;
  }
  if (!panel.hidden) render();
}

toggleButton.addEventListener("click", () => setOpen(panel.hidden));
// Esc inside the panel closes it and stops there, so it never also stops a run.
panel.addEventListener("keydown", (e) => {
  if (e.key !== "Escape") return;
  e.stopPropagation();
  setOpen(false);
});
// Elsewhere, Esc closes the panel unless the chat used it, to stop its run or keep a chat; app.js's handler runs first.
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !e.defaultPrevented && !panel.hidden) setOpen(false);
});
load();
