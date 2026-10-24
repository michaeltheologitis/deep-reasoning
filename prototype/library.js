// The Library panel: the decompositions, namespaces, tools and data every run draws on. Read-only, mock data.
const DATA_URL = "data/library.json";
const TABS = ["Decompositions", "Namespaces", "Tools", "Data"];
const MENU = "Every namespace's menu";
const PHONE = matchMedia("(max-width: 720px)");

const panel = document.getElementById("library");
const toggleButton = document.getElementById("library-toggle");
const opened = new Set();
let library = null;
let problem = null;
let tab = TABS[0];

function el(tag, props = {}, ...kids) {
  const node = document.createElement(tag);
  for (const [name, value] of Object.entries(props)) {
    if (value == null || value === false) continue;
    if (name.startsWith("on")) node.addEventListener(name.slice(2), value);
    else if (name === "class") node.className = value;
    else node.setAttribute(name, value);
  }
  node.append(...kids.flat(Infinity).filter((kid) => kid != null && kid !== false));
  return node;
}

const join = (items, separator) => items.flatMap((item, i) => (i ? [separator(), item] : [item]));
const dot = () => el("span", { class: "lib-dot", "aria-hidden": "true" }, "·");

// ── the panel's frame, built once ────────────────────────────────────────

const revision = el("span", { class: "lib-rev" });
const body = el("div", { class: "lib-body", id: "library-body", role: "tabpanel" });
const tabButtons = TABS.map((name) =>
  el("button", { type: "button", role: "tab", class: "lib-tab", id: `library-tab-${name.toLowerCase()}`, "aria-controls": body.id, onclick: () => selectTab(name) }, name),
);
panel.append(
  el(
    "header",
    { class: "lib-head" },
    el("h2", { class: "lib-title" }, "Library", revision),
    el("button", { type: "button", class: "lib-close", "aria-label": "Close the Library", onclick: () => setOpen(false) }, "×"),
  ),
  el("div", { class: "lib-tabs", role: "tablist", "aria-label": "Library", onkeydown: arrowTabs }, join(tabButtons, dot)),
  body,
);

// ── shared pieces ────────────────────────────────────────────────────────

function disclosure(key, head, content, tone = "") {
  const open = opened.has(key);
  return el(
    "div",
    { class: "lib-entry" },
    el(
      "button",
      { type: "button", class: `row ${tone}`, "aria-expanded": String(open), "data-key": key, onclick: () => flip(key) },
      el("span", { class: "caret" }, open ? "▾" : "▸"),
      head,
    ),
    open && el("div", { class: "children lib-open" }, content()),
  );
}

// one span, so a long row cuts the detail before the name
function rowHead(name, detail, meta) {
  return [el("span", { class: "lib-name" }, name, " ", el("span", { class: "lib-detail" }, detail)), el("span", { class: "meta" }, meta)];
}

function fields(rows) {
  return el("dl", { class: "lib-fields" }, rows.map(([label, value]) => [el("dt", {}, label), el("dd", {}, value)]));
}

function sourced(items) {
  if (!items.length) return "—";
  return items.map(({ value, source, here }) => {
    const label = el("span", { class: `lib-source ${here ? "here" : ""}` }, source);
    if (value.includes("\n")) return el("div", { class: "lib-item lib-block" }, el("pre", { class: "code lib-doc" }, value), label);
    return el("div", { class: "lib-item" }, value, " ", label);
  });
}

const group = (title, rows) => el("section", { class: "lib-group" }, el("h3", { class: "lib-label" }, title), el("div", { class: "lib-rows" }, rows));

// ── Decompositions: each one's worked example drawn as the chat draws a run ──

function renderStep(step, key) {
  if (step.kind === "task") return el("div", { class: "user" }, el("span", { class: "prompt" }, "> "), step.text);
  const open = opened.has(key);
  const toggle = { type: "button", "aria-expanded": String(open), "data-key": key, onclick: () => flip(key) };
  if (step.kind === "think") {
    return el("button", { ...toggle, class: `think ${open ? "open" : ""}` }, el("span", {}, "✻"), el("span", { class: "body" }, step.text));
  }
  const [first, ...rest] = step.code.split("\n");
  const label = step.code.startsWith("FinalAnswer(") ? "Final answer" : [el("b", {}, "Python"), `(${first}${rest.length ? " …" : ""})`];
  return el(
    "div",
    { class: "cell is-done" },
    el("button", { ...toggle, class: "line" }, el("span", { class: "glyph" }, "●"), el("span", { class: "head" }, label)),
    open && el("pre", { class: "code" }, step.code),
    step.output != null && renderOutput(step.output, open),
  );
}

function renderOutput(text, open) {
  const lines = text.split("\n");
  const more = !open && lines.length > 1 && el("span", { class: "more" }, ` … +${lines.length - 1} lines`);
  return el("div", { class: `out ${open ? "full" : ""}` }, el("span", {}, "⎿"), el("span", { class: "text" }, open ? text : lines[0], more));
}

function attachedTo(decomposition, groupTitle) {
  if (groupTitle === MENU) return "the run's own menu, offered first in every namespace";
  if (!decomposition.attached.length) return "no namespace";
  const everywhere = decomposition.attached.includes("root") ? ", so every namespace inherits it" : "";
  return decomposition.attached.join(", ") + everywhere;
}

function renderDecomposition(decomposition, key, groupTitle) {
  const yamlKey = `${key}:yaml`;
  const showYaml = opened.has(yamlKey);
  return [
    fields([
      ["Use when", decomposition.use_when ?? "—"],
      ["Hint", decomposition.hint ?? "—"],
      ["Attached to", attachedTo(decomposition, groupTitle)],
    ]),
    el("div", { class: "steps lib-example" }, decomposition.steps.map((step, i) => renderStep(step, `${key}:${i}`))),
    el(
      "div",
      { class: "lib-actions" },
      el("button", { type: "button", class: "lib-action", "aria-expanded": String(showYaml), "data-key": yamlKey, onclick: () => flip(yamlKey) }, "View YAML"),
      el("button", { type: "button", class: "lib-action lib-use", onclick: () => useInChat(decomposition.slug) }, "Use in chat"),
    ),
    showYaml && el("pre", { class: "code lib-pre" }, decomposition.yaml),
  ];
}

function renderDecompositions() {
  return library.groups.map((each, g) =>
    group(
      each.title,
      each.rows.map(({ slug, from }) => {
        const decomposition = library.decompositions[slug];
        const key = `d:${g}:${slug}`;
        const head = rowHead(decomposition.name, `/${slug}`, from ? `from ${from}` : `v${decomposition.version}`);
        return disclosure(key, head, () => renderDecomposition(decomposition, key, each.title), from ? "is-inherited" : "");
      }),
    ),
  );
}

// ── Namespaces, Tools, Data ──────────────────────────────────────────────

const namespaceFields = (list) => fields(list.map(({ label, items }) => [label, sourced(items)]));

function renderNamespaces() {
  const tree = library.namespaces.map((namespace) => {
    const star = namespace.name === library.default_namespace && el("span", { class: "lib-star" }, "★ new chats start here");
    const head = [el("span", { class: "lib-name" }, namespace.name), star];
    return el("div", { style: `--depth: ${namespace.depth}` }, disclosure(`n:${namespace.name}`, head, () => namespaceFields(namespace.fields)));
  });
  const run = disclosure("n:run", el("span", { class: "lib-name" }, "Run settings"), () => namespaceFields(library.run_settings));
  return [el("div", { class: "lib-rows lib-tree" }, run, tree)];
}

function renderTool(tool) {
  return [
    fields([
      ["Factory", tool.factory],
      ["File", tool.file],
      ["Defined in", tool.defined_in ?? "the deep_reasoner package"],
      ["Granted in", tool.granted_in.join(", ") || "no namespace"],
    ]),
    tool.config && el("pre", { class: "code lib-pre" }, tool.config),
    el("pre", { class: `code ${tool.description.includes("\n") ? "lib-pre" : "lib-doc"}` }, tool.description),
  ];
}

function renderTools() {
  const rows = library.tools.map((tool) => {
    const granted = tool.granted_in.length ? `granted in ${tool.granted_in.join(", ")}` : "not granted";
    return disclosure(`t:${tool.name}`, rowHead(tool.name, granted, tool.version ? `v${tool.version}` : "built-in"), () => renderTool(tool));
  });
  return [el("div", { class: "lib-rows" }, rows)];
}

function dataTable({ name, columns, rows }) {
  const cell = (tag, text) => el(tag, tag === "th" ? { scope: "col" } : {}, el("div", {}, text));
  return el(
    "div",
    { class: "lib-table", role: "region", tabindex: "0", "aria-label": `${name}, scrolls sideways` },
    el("table", {}, el("thead", {}, el("tr", {}, columns.map((column) => cell("th", column)))), el("tbody", {}, rows.map((row) => el("tr", {}, row.map((text) => cell("td", text)))))),
  );
}

function renderData() {
  return library.data.map((section, s) =>
    group(
      section.title,
      section.items.map((entry, i) =>
        disclosure(`v:${s}:${i}`, rowHead(entry.name, entry.where, entry.summary), () => (entry.rows ? dataTable(entry) : el("p", { class: "lib-note" }, entry.note))),
      ),
    ),
  );
}

const RENDERERS = { Decompositions: renderDecompositions, Namespaces: renderNamespaces, Tools: renderTools, Data: renderData };

// ── state and wiring ─────────────────────────────────────────────────────

function render() {
  for (const button of tabButtons) button.setAttribute("aria-selected", String(button.textContent === tab));
  body.setAttribute("aria-labelledby", `library-tab-${tab.toLowerCase()}`);
  const focused = document.activeElement?.dataset?.key;
  if (problem || !library) body.replaceChildren(el("p", { class: "lib-note" }, problem ?? "Loading the Library…"));
  else body.replaceChildren(...RENDERERS[tab]());
  if (focused) body.querySelector(`[data-key="${focused}"]`)?.focus();
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

function useInChat(slug) {
  const input = document.getElementById("input");
  input.value = `/${slug} `;
  input.dispatchEvent(new Event("input"));
  if (PHONE.matches) setOpen(false);
  input.focus();
  input.setSelectionRange(input.value.length, input.value.length);
}

async function load() {
  try {
    const response = await fetch(DATA_URL);
    if (!response.ok) throw new Error(`${DATA_URL} answered ${response.status}`);
    library = await response.json();
    revision.textContent = ` · rev ${library.revision}`;
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
// Elsewhere, Esc closes the panel only while no run is going; during a run it stops the run.
// Capture, to see whether a run is going before the chat's own Esc stops it.
document.addEventListener(
  "keydown",
  (e) => {
    if (e.key !== "Escape" || panel.hidden || panel.contains(e.target)) return;
    if (document.getElementById("stop").hidden) setOpen(false);
  },
  true,
);
load();
