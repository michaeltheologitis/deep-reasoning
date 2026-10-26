// The Deep Reasoning chat: chats and their runs from the app's API, each run's events folded into its tree, live as they stream.
import { foldEvent, foldEvents, newFold } from "./fold.js";

const SPIN_MS = 120;
const STICK_PX = 80;
const FIRST_ROWS = 20;
const MORE_ROWS = 100;
const TRAIL_CHARS = 22;
const TRAIL_PARTS = 3;
const SECONDS_PER_MINUTE = 60;
const MS_PER_SECOND = 1000;
const CONFLICT = 409;
const NEW_TITLE = "New chat";
const NOT_ANSWERING = "the app isn't answering; is deep-reasoning still running?";
const RECONNECTING = "Lost the connection to the run; reconnecting…";
const PANEL_CLOSE = "panel-close";
const PANEL_OPEN = "panel-open";
const MENU_STEPS = { ArrowDown: 1, ArrowUp: -1 };
// ︎ keeps ✳ a text glyph where the system would draw it as an emoji
const SPIN = ["·", "✢", "✳︎", "✶", "✻", "✽", "✻", "✶", "✳︎", "✢"];
const STATUS = {
  done: ["done", ""],
  running: ["running", ""],
  exhausted: ["out of turns", "warn"],
  failed: ["failed", "err"],
  stopped: ["stopped", ""],
};
const OUTCOME = {
  exhausted: ["ran out of turns", "warn"],
  failed: ["failed", "err"],
  stopped: ["stopped by you", "err"],
};

const byId = (id) => document.getElementById(id);
const state = { chats: [], current: null, live: null, sending: false, problem: null };
const ui = { renaming: null, deleting: null };
const opened = new WeakSet();
const showingCode = new WeakSet();
const shown = new WeakMap();
const views = new WeakMap();
const keys = new WeakMap();
const counter = new Intl.NumberFormat();
const library = { namespaces: null, defaultNamespace: null };
const HOME_FOLDER = "~";
let popover = null;
// Each provider's models, as the server lists them with its key: read once per page load, and again after settings change.
let modelLists = null;
let nextId = 1;
let frame = 0;
let drawing = 0;

function element(tag, props = {}, ...kids) {
  const el = document.createElement(tag);
  for (const [name, value] of Object.entries(props)) {
    if (value == null || value === false) continue;
    if (name.startsWith("on")) el.addEventListener(name.slice(2), value);
    else if (name === "class") el.className = value;
    else el.setAttribute(name, value);
  }
  el.append(...kids.flat(Infinity).filter((kid) => kid != null && kid !== false));
  return el;
}

const join = (items, separator) => items.flatMap((item, i) => (i ? [separator, item] : [item]));
const since = (start) => Date.now() / MS_PER_SECOND - start;
const isFinal = (cell) => cell.code.startsWith("FinalAnswer(");
const formatCount = (count) => counter.format(count);
const plural = (count, noun) => `${formatCount(count)} ${noun}${count === 1 ? "" : "s"}`;
const clip = (text, chars) => (text.length > chars ? `${text.slice(0, chars - 1)}…` : text);
const keyOf = (node) => {
  if (!keys.has(node)) keys.set(node, String(nextId++));
  return keys.get(node);
};

function formatCost(usd) {
  if (usd == null) return null;
  if (usd === 0) return "$0";
  return `$${usd.toFixed(usd >= 0.01 ? 2 : 4)}`;
}

function formatSeconds(seconds) {
  if (seconds == null) return null;
  const tenths = seconds.toFixed(1);
  if (Number(tenths) < SECONDS_PER_MINUTE) return `${tenths}s`;
  const whole = Math.round(seconds);
  return `${Math.floor(whole / SECONDS_PER_MINUTE)}m ${whole % SECONDS_PER_MINUTE}s`;
}

const spinner = () => element("span", { class: "spin" }, SPIN[frame]);
const clock = (start) => element("span", { "data-since": start }, formatSeconds(since(start)));
const caret = (open) => element("span", { class: "caret" }, open ? "▾" : "▸");

function countAgents(holder, wanted = () => true) {
  let count = 0;
  for (const step of holder.steps) {
    for (const agent of step.agents ?? []) count += Number(wanted(agent)) + countAgents(agent, wanted);
  }
  return count;
}

// A toggle redraws only its own node, so a click stays quick with thousands of rows shown.
function remember(node, el, again) {
  views.set(node, { el, again });
  return el;
}

function refocus(...candidates) {
  const target = candidates.map((key) => key && document.querySelector(`[data-key="${key}"]`)).find(Boolean);
  target?.focus({ preventScroll: true });
}

function redraw(node, fallbackKey) {
  const { el, again } = views.get(node);
  const focused = document.activeElement?.dataset?.key;
  el.replaceWith(again());
  refocus(focused, fallbackKey);
}

function toggle(set, node) {
  if (set.has(node)) set.delete(node);
  else set.add(node);
  redraw(node);
}

function toggler(node, props, kids, set = opened, key = keyOf(node)) {
  const expanded = String(set.has(node));
  return element("button", { type: "button", "aria-expanded": expanded, "data-key": key, onclick: () => toggle(set, node), ...props }, kids);
}

function describe(step) {
  if (step.kind === "think") return { text: step.text };
  const count = step.agents.length;
  if (count) return { text: count === 1 ? "Delegated to a sub-agent" : `Delegated to ${plural(count, "sub-agent")}` };
  if (isFinal(step)) return { text: "Final answer" };
  const [first, ...rest] = step.code.split("\n");
  return { tool: "Python", text: first + (rest.length ? " …" : "") };
}

function stepLabel(step, chars = Infinity) {
  const { tool, text } = describe(step);
  return tool ? `${tool}(${clip(text, chars)})` : clip(text, chars);
}

function headline(step) {
  const { tool, text } = describe(step);
  return element("span", { class: "head" }, tool ? [element("b", {}, tool), `(${text})`] : text);
}

function finalValue(output) {
  const value = output.replace(/^FinalAnswer: /, "");
  return /^(['"]).*\1$/s.test(value) ? value.slice(1, -1) : value;
}

function out(text, { tone = "", full = false, more = null } = {}) {
  return element(
    "div",
    { class: `out ${tone} ${full ? "full" : ""}` },
    element("span", {}, "⎿"),
    element("span", { class: "text" }, text, more && element("span", { class: "more" }, more)),
  );
}

function renderOutput(cell, full, root) {
  const tone = cell.status === "failed" ? "err" : "";
  if (cell.status === "stopped") return null;
  if (cell.output == null) return cell.agents.length ? null : out("Running…");
  if (full) return out(cell.output, { tone, full: true });
  const lines = cell.output.trimEnd().split("\n");
  if (cell.status === "failed") return out(lines.at(-1), { tone });
  // each sub-agent's row opens onto its answer, and the answer below shows the root's
  if (cell.agents.length || (root && isFinal(cell))) return null;
  if (isFinal(cell)) return out(finalValue(cell.output));
  const more = lines.length > 1 ? ` … +${lines.length - 1} lines` : null;
  return out(lines[0] || "(no output)", { more });
}

const glyph = (cell) => element("span", { class: `glyph ${cell.status}` }, "●");

function renderThink(step) {
  const open = opened.has(step);
  return toggler(step, { class: `think ${open ? "open" : ""}` }, [
    element("span"),
    element("span", {}, "✻"),
    element("span", { class: "body" }, step.text),
  ]);
}

function renderCell(cell, root) {
  if (cell.agents.length) return renderDelegation(cell);
  const open = opened.has(cell);
  return element(
    "div",
    { class: "cell" },
    toggler(cell, { class: "line" }, [element("span"), glyph(cell), headline(cell)]),
    open && element("pre", { class: "code" }, cell.code),
    renderOutput(cell, open, root),
  );
}

function renderDelegation(cell) {
  const open = opened.has(cell);
  const code = showingCode.has(cell);
  return element(
    "div",
    { class: "cell" },
    element(
      "div",
      { class: "node" },
      toggler(cell, { class: "line" }, [caret(open), glyph(cell), headline(cell)]),
      toggler(cell, { class: "show-code", "aria-label": "code and output" }, "code", showingCode, `${keyOf(cell)}:code`),
      element("span", { class: "meta" }, delegationMeta(cell)),
    ),
    code && element("pre", { class: "code" }, cell.code),
    open && renderRows(cell),
    renderOutput(cell, code, false),
  );
}

function delegationMeta(cell) {
  const { agents } = cell;
  const counts = Object.entries(STATUS).map(([status, [word, tone]]) => {
    const count = agents.filter((agent) => agent.status === status).length;
    return count > 0 && element("span", { class: `word ${tone}` }, `${formatCount(count)} ${word}`);
  });
  const running = agents.filter((agent) => agent.status === "running");
  const longest = running.length
    ? clock(Math.min(...running.map((agent) => agent.started)))
    : formatSeconds(Math.max(...agents.map((agent) => agent.seconds ?? 0)));
  const costs = agents.map((agent) => agent.cost).filter((cost) => cost != null);
  const total = costs.length > 0 && formatCost(costs.reduce((sum, cost) => sum + cost, 0));
  return join([...counts, longest, total].filter(Boolean), " · ");
}

function renderRows(cell) {
  const count = Math.min(shown.get(cell) ?? FIRST_ROWS, cell.agents.length);
  const hidden = cell.agents.length - count;
  return element("div", { class: "rows" }, cell.agents.slice(0, count).map(renderAgent), hidden > 0 && renderMore(cell, count, hidden));
}

function renderMore(cell, count, hidden) {
  const key = keyOf(cell);
  const button = (label, rows, suffix) =>
    element("button", { type: "button", "data-key": `${key}:${suffix}`, onclick: () => showMore(cell, rows) }, label);
  return element(
    "div",
    { class: "more-rows" },
    `… ${formatCount(hidden)} more`,
    hidden > MORE_ROWS && [" · ", button(`show ${MORE_ROWS} more`, count + MORE_ROWS, "more")],
    " · ",
    button("show all", Infinity, "all"),
  );
}

function showMore(cell, count) {
  const first = cell.agents[shown.get(cell) ?? FIRST_ROWS];
  shown.set(cell, count);
  redraw(cell, keyOf(first));
}

function renderStep(step, root) {
  const el = step.kind === "think" ? renderThink(step) : renderCell(step, root);
  return remember(step, el, () => renderStep(step, root));
}

function renderUnder(agent) {
  const [, tone] = STATUS[agent.status] ?? [];
  if (agent.status === "running") {
    const last = agent.steps.at(-1);
    return last ? out(stepLabel(last)) : null;
  }
  if (!tone || !agent.result) return null;
  return out(agent.result.split("\n")[0], { tone });
}

function renderAgent(agent) {
  const open = opened.has(agent);
  const running = agent.status === "running";
  const [word, tone] = STATUS[agent.status] ?? [];
  const tags = [agent.namespace !== "root" && agent.namespace, agent.drive > 1 && `message ${agent.drive}`];
  const meta = [
    agent.status !== "done" && element("span", { class: `word ${tone}` }, word),
    running ? clock(agent.started) : formatSeconds(agent.seconds),
    formatCost(agent.cost),
  ].filter(Boolean);
  const el = element(
    "div",
    { class: "agent" },
    toggler(agent, { class: "row" }, [
      caret(open),
      element("span", { class: "task" }, agent.task),
      tags.filter(Boolean).map((tag) => element("span", { class: "tag" }, tag)),
      element("span", { class: "meta" }, running && [spinner(), " "], join(meta, " · ")),
    ]),
    open
      ? element("div", { class: "children" }, agent.steps.map((step) => renderStep(step, false)), !running && renderUnder(agent))
      : renderUnder(agent),
  );
  return remember(agent, el, () => renderAgent(agent));
}

function renderAnswer(text) {
  const el = element("div", { class: "answer" });
  // answers are model output, and marked passes raw HTML through
  if (window.marked && window.DOMPurify) el.innerHTML = window.DOMPurify.sanitize(window.marked.parse(text));
  else Object.assign(el, { textContent: text, style: "white-space: pre-wrap" });
  return el;
}

function summary(turn, switched) {
  const [word, tone] = OUTCOME[turn.outcome] ?? [];
  const seconds = formatSeconds(turn.seconds);
  const agents = countAgents(turn);
  const lead = word ? [element("span", { class: `word ${tone}` }, word), ` after ${seconds}`] : `Reasoned for ${seconds}`;
  return join([lead, agents > 0 && plural(agents, "sub-agent"), formatCost(turn.cost), turn.model, switched].filter(Boolean), " · ");
}

function liveSummary(turn, followed, switched) {
  const running = countAgents(turn, (agent) => agent.status === "running");
  const facts = [clock(turn.started), running > 0 && `${plural(running, "sub-agent")} running`, turn.model, switched, followed && "esc to interrupt"];
  return [element("span", { class: "working" }, "Reasoning… "), "(", join(facts.filter(Boolean), " · "), ")"];
}

function trailText({ tasks, step }) {
  const trail = [...tasks.map((task) => clip(task, TRAIL_CHARS)), stepLabel(step, TRAIL_CHARS)];
  const parts = trail.length > TRAIL_PARTS ? [trail[0], "…", ...trail.slice(1 - TRAIL_PARTS)] : trail;
  return parts.join(" › ");
}

// A turn names its namespace when it differs from the turn before's, so a chat that switched reads clearly.
function renderTurn(turn, previous) {
  const live = state.live?.turn === turn;
  // no turn.end yet: still going, though this page may not follow it (a run started in another tab)
  const going = turn.outcome == null;
  const open = opened.has(turn);
  const latest = live && state.live.fold.latest;
  const switched = previous && turn.namespace !== previous.namespace && turn.namespace;
  const el = element(
    "section",
    { class: "turn" },
    element("div", { class: "user" }, element("span", { class: "prompt" }, "> "), turn.prompt),
    toggler(turn, { class: "summary" }, [
      caret(open),
      going ? spinner() : element("span", {}, "✻"),
      element("span", { class: "text" }, going ? liveSummary(turn, live, switched) : summary(turn, switched)),
    ]),
    live && !open && latest && out(trailText(latest), { full: true }),
    open && element("div", { class: "steps" }, turn.steps.map((step) => renderStep(step, true))),
    turn.answer != null && renderAnswer(turn.answer),
    turn.outcome === "failed" && turn.detail && out(turn.detail, { tone: "err", full: true }),
  );
  return remember(turn, el, () => renderTurn(turn, previous));
}

function renderWelcome() {
  return element(
    "div",
    { class: "welcome" },
    element("div", { class: "hi" }, "✻ Deep Reasoning"),
    element("p", {}, "Ask anything. Each run shows how it got its answer as a tree you open level by level."),
  );
}

function renderRename(chat) {
  const input = element("input", {
    class: "rename",
    id: "rename",
    value: chat.title,
    "aria-label": "Chat name",
    onkeydown: (e) => {
      e.stopPropagation();
      if (e.key === "Enter") input.blur();
      if (e.key === "Escape") finishRename(chat, chat.title);
    },
    onblur: () => finishRename(chat, input.value),
  });
  requestAnimationFrame(() => {
    input.focus();
    input.select();
  });
  return element("li", { class: "chat current" }, input);
}

function renderConfirmDelete(chat) {
  return element(
    "li",
    { class: "chat confirm" },
    "Delete this chat?",
    element("button", { type: "button", class: "yes", onclick: () => remove(chat) }, "Delete"),
    element("button", { type: "button", class: "no", onclick: () => setUi({ deleting: null }) }, "Keep"),
  );
}

function renderChat(chat) {
  if (ui.renaming === chat) return renderRename(chat);
  if (ui.deleting === chat) return renderConfirmDelete(chat);
  const current = chat === state.current;
  const live = chat.live != null;
  return element(
    "li",
    { class: `chat ${current ? "current" : ""}` },
    element(
      "button",
      { type: "button", class: "pick", onclick: () => select(chat), ondblclick: () => setUi({ renaming: chat }) },
      element("span", { class: "mark" }, live ? spinner() : current ? "●" : ""),
      element("span", { class: "name" }, chat.title),
    ),
    element("button", { type: "button", class: "icon", title: "Rename", "aria-label": "Rename", onclick: () => setUi({ renaming: chat }) }, "✎"),
    element("button", { type: "button", class: "icon", title: "Delete", "aria-label": "Delete", onclick: () => setUi({ deleting: chat }) }, "✕"),
  );
}

function renderList() {
  byId("chats").replaceChildren(...state.chats.map(renderChat));
}

function keepScroll(scroll, draw) {
  const box = byId("scroll");
  const nearBottom = box.scrollHeight - box.scrollTop - box.clientHeight < STICK_PX;
  draw();
  if (scroll === "bottom" || (scroll === "follow" && nearBottom)) box.scrollTop = box.scrollHeight;
}

function logOf(chat) {
  if (!chat.turns) return [];
  return chat.turns.length ? chat.turns.map((turn, i) => renderTurn(turn, chat.turns[i - 1])) : [renderWelcome()];
}

function renderLog(scroll) {
  const chat = state.current;
  const focused = document.activeElement?.dataset?.key;
  byId("title").textContent = chat.title;
  renderFolder(chat);
  keepScroll(scroll, () => byId("log").replaceChildren(...logOf(chat)));
  refocus(focused);
}

function usualHint(live, here) {
  if (here) return live.stopping ? "stopping…" : "";
  if (live) return `a run is going in “${live.chat.title}”`;
  return "enter to send · shift+enter for a new line";
}

function renderComposer() {
  const live = state.live;
  const here = live?.chat === state.current;
  const hint = byId("hint");
  const text = state.problem ?? usualHint(live, here);
  byId("stop").hidden = !here;
  hint.classList.toggle("err", state.problem != null);
  // the hint is a live region: setting the same text again would announce it again
  if (hint.textContent !== text) hint.textContent = text;
  const total = (state.current?.turns ?? []).reduce((sum, turn) => sum + (turn.cost ?? 0), 0);
  byId("total").textContent = total ? `${formatCost(total)} this chat` : "";
  renderChoices(state.current);
}

// Updated in place, as the composer redraws with each frame of a live run. The server says what the chat's next message runs on.
function renderChoices(chat) {
  const ready = library.namespaces && chat?.turns;
  byId("choices").hidden = !ready;
  if (!ready) return;
  byId("namespace-name").textContent = chat.namespace;
  byId("model-name").textContent = chat.model?.name ?? "pick a model";
}

// A pick applies from the chat's next message; the server keeps it, so it survives a reload.
async function choose(chat, change) {
  let chosen;
  try {
    chosen = await request("PATCH", `api/chats/${chat.id}`, change);
  } catch (error) {
    report(`Not changed: ${error.message}`);
    return;
  }
  Object.assign(chat, { namespace: chosen.namespace, model: chosen.model });
  report(null);
}

// A chat with no folder of its own works in a scratch folder, which goes when the chat does.
function renderFolder(chat) {
  byId("folder-path").textContent = chat.folder ?? `${chat.scratch_folder}/`;
  byId("folder-note").textContent = chat.folder ? "" : "· deleted with the chat";
}

function pickFolder() {
  const chat = state.current;
  folderPicker(byId("folder"), byId("topbar"), {
    label: "This chat's working folder",
    current: chat.folder,
    empty: "its own scratch folder, deleted with the chat",
    note: "Its Python runs there and reads and writes files there, from the next message. A folder you choose is never deleted.",
    pick: async (folder) => {
      ({ folder: chat.folder } = await request("PATCH", `api/chats/${chat.id}`, { folder }));
      if (chat === state.current) renderFolder(chat);
    },
  });
}

function pickNamespace() {
  const chat = state.current;
  const star = element("span", { class: "lib-star" }, "★ new chats start here");
  const options = library.namespaces.map((name) => ({ value: name, label: [name, name === library.defaultNamespace && star] }));
  showMenu(byId("namespace"), byId("above"), {
    label: "Namespaces",
    groups: () => [{ options }],
    isCurrent: (name) => name === chat.namespace,
    pick: (name) => choose(chat, { namespace: name }),
  });
}

function loadModels() {
  modelLists ??= request("GET", "api/models").catch((error) => {
    modelLists = null;
    throw error;
  });
  return modelLists;
}

// The menu opens at once, saying the lists are loading while a provider is slow to answer.
async function pickModel() {
  const button = byId("model");
  const host = byId("above");
  if (isOpenFrom(button)) return closePopover(true);
  const chat = state.current;
  const loading = notePopover(button, host, "Loading the model lists…");
  let lists;
  try {
    lists = await loadModels();
  } catch (error) {
    loading.textContent = `No model lists: ${error.message}`;
    return;
  }
  if (!popover?.el.contains(loading)) return;
  closePopover(false);
  if (!lists.length) return noProviderMenu(button, host);
  showMenu(button, host, {
    label: "Models",
    filter: "filter, or type a model name",
    groups: (query) => modelGroups(lists, query),
    isCurrent: (model) => model.provider === chat.model?.provider && model.name === chat.model?.name,
    pick: (model) => choose(chat, { model }),
  });
}

// A popover with a line of text, and the button for what to do about it, if any.
function notePopover(button, host, text, action) {
  const note = element("p", { class: "menu-note" }, text);
  const el = element("div", { class: "menu-pop", role: "dialog", "aria-label": "Models", tabindex: "-1" }, note, action);
  openPopover(button, host, el, action ?? el);
  return note;
}

// With no key anywhere there is no model to list, so the menu points to settings.
function noProviderMenu(button, host) {
  const add = element("button", { type: "button", class: "lib-action lib-primary", onclick: openSettings }, "Add a key in settings");
  notePopover(button, host, "No provider has a key yet.", add);
}

function openSettings() {
  closePopover(false);
  byId("settings").dispatchEvent(new Event(PANEL_OPEN));
}

// Each provider that can answer, with its listed models, a typed name, and why its list is missing if it is.
function modelGroups(lists, query) {
  const typed = query.trim();
  return lists.map(({ provider, models, problem }) => {
    const matches = models.filter((name) => name.toLowerCase().includes(typed.toLowerCase()));
    const options = matches.map((name) => ({ value: { provider, name }, label: name }));
    if (typed && !models.includes(typed)) options.push({ value: { provider, name: typed }, label: `use “${typed}”` });
    if (!options.length) options.push({ value: null, label: "use model name…", hint: `type a model name for ${provider}` });
    return { name: provider, note: problem, options };
  });
}

// After a change in settings the lists are read again, and each chat's model too: one that never picked follows what new chats start on.
async function settingsChanged() {
  modelLists = null;
  let listed;
  try {
    listed = await request("GET", "api/chats");
  } catch {
    return;
  }
  for (const { id, model } of listed) {
    const chat = state.chats.find((each) => each.id === id);
    if (chat) chat.model = model;
  }
  renderComposer();
}

// A popover opened by its button into host. Esc closes it and stops there, so it never also stops a run or closes a panel;
// focus leaving it (a click elsewhere, Tab) closes it too. Its buttons keep focus in it on mousedown, so a click toggles it.
function openPopover(button, host, el, focus) {
  closePopover(false);
  popover = { button, el };
  el.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    e.preventDefault();
    e.stopPropagation();
    closePopover(true);
  });
  // checked a frame later, as redrawing a popover's insides drops focus for a moment
  el.addEventListener("focusout", () => requestAnimationFrame(() => closeIfLeft(el)));
  host.append(el);
  button.setAttribute("aria-expanded", "true");
  focus.focus();
}

function closeIfLeft(el) {
  if (popover?.el === el && !el.contains(document.activeElement)) closePopover(false);
}

function closePopover(refocus) {
  const open = popover;
  if (!open) return;
  popover = null;
  open.el.remove();
  open.button.setAttribute("aria-expanded", "false");
  if (refocus) open.button.focus();
}

const isOpenFrom = (button) => popover?.button === button;

// A menu of grouped options, with a filter field when it has one: arrows move, Enter picks.
function showMenu(button, host, spec) {
  if (isOpenFrom(button)) return closePopover(true);
  const list = element("div", { class: "menu-list", id: "menu-list", role: "listbox", "aria-label": spec.label, tabindex: spec.filter ? null : "-1", onmousedown: (e) => e.preventDefault() });
  const field = spec.filter && element("input", { class: "menu-filter", role: "combobox", "aria-label": `Filter the ${spec.label.toLowerCase()}`, "aria-controls": list.id, "aria-expanded": "true", "aria-autocomplete": "list", placeholder: spec.filter, autocomplete: "off", spellcheck: "false" });
  const el = element("div", { class: "menu-pop" }, field, list);
  const open = { spec, list, field, options: [], active: 0 };
  field?.addEventListener("input", () => fillMenu(open));
  el.addEventListener("keydown", (e) => menuKey(open, e));
  fillMenu(open);
  openPopover(button, host, el, field || list);
  markActive(open);
}

function fillMenu(open) {
  const groups = open.spec.groups(open.field?.value ?? "");
  open.options = groups.flatMap((group) => group.options);
  const current = open.options.findIndex((option) => isCurrentOption(open, option));
  open.active = open.field?.value ? 0 : Math.max(current, 0);
  open.list.replaceChildren(...groups.map((group, i) => menuGroup(open, group, i)));
  open.list.scrollTop = 0;
  markActive(open);
}

const isCurrentOption = (open, option) => option.value != null && open.spec.isCurrent(option.value);

function menuGroup(open, group, number) {
  const head = group.name && element("div", { class: "menu-head", id: `menu-group-${number}`, role: "presentation" }, group.name);
  const note = group.note && element("div", { class: "menu-note", id: `menu-note-${number}`, role: "presentation" }, group.note);
  return element(
    "div",
    { role: "group", "aria-labelledby": head?.id, "aria-describedby": note?.id },
    head,
    note,
    group.options.map((option) => {
      const current = isCurrentOption(open, option);
      const id = `menu-option-${open.options.indexOf(option)}`;
      const mark = element("span", { class: "mark" }, current ? "✓" : "");
      return element("div", { class: "menu-option", id, role: "option", "aria-selected": String(current), onclick: () => chooseOption(open, option) }, mark, option.label);
    }),
  );
}

function markActive(open) {
  const id = open.options.length ? `menu-option-${open.active}` : null;
  const owner = open.field || open.list;
  for (const el of open.list.querySelectorAll(".active")) el.classList.remove("active");
  if (!id) return owner.removeAttribute("aria-activedescendant");
  owner.setAttribute("aria-activedescendant", id);
  const el = open.list.querySelector(`[id="${id}"]`);
  el.classList.add("active");
  el.scrollIntoView({ block: "nearest" });
}

function menuKey(open, e) {
  const step = MENU_STEPS[e.key];
  if (step && open.options.length) {
    e.preventDefault();
    open.active = (open.active + step + open.options.length) % open.options.length;
    markActive(open);
  } else if (e.key === "Enter" || (e.key === " " && !open.field)) {
    // also keeps Enter in the filter from sending the composer's message
    e.preventDefault();
    if (open.options.length) chooseOption(open, open.options[open.active]);
  }
}

// "use model name…" picks nothing: the filter field takes the name.
function chooseOption(open, option) {
  if (option.value == null) {
    open.field.placeholder = option.hint;
    open.field.focus();
    return;
  }
  closePopover(true);
  open.spec.pick(option.value);
}

// A folder typed or pasted, or found in the browser under the field, which follows what the field holds; empty means the scratch folder.
// The server lists the folders and checks the one picked: spec.pick throws its refusal, which the picker shows.
function folderPicker(button, host, spec) {
  if (isOpenFrom(button)) return closePopover(true);
  const field = element("input", { id: "folder-field", class: "menu-filter", value: spec.current ?? "", placeholder: `empty: ${spec.empty}`, autocomplete: "off", spellcheck: "false", "aria-describedby": "folder-problem folder-pop-note" });
  const problem = element("div", { id: "folder-problem", class: "folder-problem", "aria-live": "polite" });
  const browser = element("div", { class: "folder-browser", role: "group", "aria-label": "Folders", onmousedown: (e) => e.preventDefault() });
  const use = element("button", { type: "submit", class: "lib-action lib-primary" });
  const picker = { button, spec, field, problem, browser, use, asked: null };
  const el = element(
    "form",
    { class: "menu-pop folder-pop", method: "dialog", role: "dialog", "aria-label": spec.label, onsubmit: (e) => useFolder(e, picker) },
    element("label", { class: "menu-head", for: field.id }, spec.label),
    field,
    problem,
    element("p", { class: "menu-note", id: "folder-pop-note" }, spec.note),
    browser,
    element("div", { class: "lib-actions" }, use),
  );
  field.addEventListener("input", () => {
    problem.textContent = "";
    fillBrowser(picker);
  });
  fillBrowser(picker);
  openPopover(button, host, el, field);
}

const cleanFolder = (path) => path.trim().replace(/(.)\/+$/, "$1");

// Each keystroke asks again; an answer to an older question is dropped.
async function fillBrowser(picker) {
  const here = cleanFolder(picker.field.value) || HOME_FOLDER;
  picker.use.textContent = picker.field.value.trim() ? "Use this folder" : "Use a scratch folder";
  picker.asked = here;
  let listing;
  try {
    listing = await request("GET", `api/folders?path=${encodeURIComponent(here)}`);
  } catch (error) {
    if (picker.asked === here) picker.browser.replaceChildren(element("div", { class: "folder-here" }, here), element("p", { class: "menu-note" }, error.message));
    return;
  }
  if (picker.asked !== here) return;
  const row = (label, path) => element("button", { type: "button", class: "row", onclick: () => goToFolder(picker, path) }, label);
  const up = listing.parent == null ? [] : [row("..", listing.parent)];
  const rows = listing.folders.length ? listing.folders.map(({ name, path }) => row(`${name}/`, path)) : [element("p", { class: "menu-note" }, "no folders in here")];
  picker.browser.replaceChildren(element("div", { class: "folder-here" }, listing.path), ...up, ...rows);
}

async function goToFolder(picker, path) {
  picker.field.value = path;
  picker.problem.textContent = "";
  const fromKeyboard = picker.browser.contains(document.activeElement);
  await fillBrowser(picker);
  // a folder that can't be listed leaves no row, and focus mustn't fall out of the picker
  if (fromKeyboard) (picker.browser.querySelector(".row") ?? picker.field).focus();
}

async function useFolder(e, picker) {
  e.preventDefault();
  const path = cleanFolder(picker.field.value);
  try {
    await picker.spec.pick(path || null);
  } catch (error) {
    // a browser note saying the same gives way to the refusal, so it reads once
    const note = picker.browser.querySelector(".menu-note");
    if (note?.textContent === error.message) note.remove();
    picker.problem.textContent = error.message;
    picker.field.focus();
    return;
  }
  if (isOpenFrom(picker.button)) closePopover(true);
}

// One side panel at a time: opening one asks the others to close.
function closeOtherPanels(panel) {
  for (const other of document.querySelectorAll(".library:not([hidden])")) {
    if (other !== panel) other.dispatchEvent(new Event(PANEL_CLOSE));
  }
}

function render(scroll = "keep") {
  if (!ui.renaming) renderList();
  renderLog(scroll);
  renderComposer();
}

function setUi(change) {
  Object.assign(ui, { renaming: null, deleting: null }, change);
  renderList();
}

function report(problem) {
  state.problem = problem;
  renderComposer();
}

async function request(method, url, body) {
  const options = body === undefined ? { method } : { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
  let response;
  try {
    response = await fetch(url, options);
  } catch {
    throw new Error(NOT_ANSWERING);
  }
  const answer = await response.json().catch(() => ({}));
  if (response.ok) return answer;
  const problem = typeof answer.detail === "string" ? answer.detail : `${url} answered ${response.status}`;
  throw Object.assign(new Error(problem), { status: response.status });
}

// A run still going in a chat is followed from where its turns end, unless the page follows another or the chat is gone.
async function readTurns(chat) {
  const { title, live, turns, namespace, model, folder } = await request("GET", `api/chats/${chat.id}`);
  const folds = turns.map((turn) => foldEvents(turn.events));
  Object.assign(chat, { title, live, namespace, model, folder, turns: folds.map((fold) => fold.turn) });
  if (live && !state.live && state.chats.includes(chat)) follow(chat, live, folds.at(-1));
}

async function select(chat) {
  state.current = chat;
  state.problem = null;
  ui.deleting = null;
  byId("app").classList.remove("list-open");
  render("bottom");
  byId("input").focus();
  // read once, or each time while its run goes on unfollowed, so its turn never stays half-folded
  if (chat.turns && (chat.live == null || state.live?.chat === chat)) return;
  chat.reading ??= readTurns(chat);
  try {
    await chat.reading;
  } catch (error) {
    if (state.current === chat) report(`Could not open this chat: ${error.message}`);
    return;
  } finally {
    chat.reading = null;
  }
  if (state.current === chat) render("bottom");
}

async function newChat() {
  let chat;
  try {
    chat = await request("POST", "api/chats");
  } catch (error) {
    report(`No new chat: ${error.message}`);
    return;
  }
  chat.turns = [];
  state.chats.unshift(chat);
  select(chat);
}

// The list drops the chat at once; the server may take a few seconds, stopping a run that is going first.
async function remove(chat) {
  const index = state.chats.indexOf(chat);
  if (state.live?.chat === chat) {
    state.live.source.close();
    state.live = null;
  }
  state.chats.splice(index, 1);
  ui.deleting = null;
  renderList();
  if (state.current !== chat) renderComposer();
  else if (state.chats.length) select(state.chats[Math.min(index, state.chats.length - 1)]);
  else newChat();
  try {
    await request("DELETE", `api/chats/${chat.id}`);
  } catch (error) {
    // back in the list, read afresh when next opened
    state.chats.splice(Math.min(index, state.chats.length), 0, Object.assign(chat, { turns: null }));
    state.problem = `Not deleted: ${error.message}`;
    render();
  }
}

async function finishRename(chat, typed) {
  if (ui.renaming !== chat) return;
  ui.renaming = null;
  const before = chat.title;
  const title = typed.trim();
  if (!title || title === before) return render();
  chat.title = title;
  render();
  try {
    await request("PATCH", `api/chats/${chat.id}`, { title });
  } catch (error) {
    chat.title = before;
    state.problem = `Not renamed: ${error.message}`;
    render();
  }
}

function follow(chat, run, fold) {
  const source = new EventSource(`api/runs/${run}/events?after=${fold.seq}`);
  const live = { chat, run, fold, turn: fold.turn, source, stopping: false };
  state.live = live;
  chat.live = run;
  source.onopen = () => {
    if (state.problem === RECONNECTING) report(null);
  };
  source.onmessage = (message) => receive(live, JSON.parse(message.data));
  source.onerror = () => lost(live);
}

function receive(live, event) {
  if (!foldEvent(live.fold, event)) return;
  if (event.kind === "turn.end") return finish(live);
  drawLive(live);
}

// Events come in bursts, as when catching up on a long run, so the live turn redraws at most once a frame.
function drawLive(live) {
  if (drawing) return;
  drawing = requestAnimationFrame(() => {
    drawing = 0;
    if (state.live !== live || live.chat !== state.current || !views.has(live.turn)) return;
    keepScroll("follow", () => redraw(live.turn));
    renderComposer();
  });
}

// The stream closes after turn.end; left open, EventSource would reconnect to it.
function finish(live) {
  live.source.close();
  live.chat.live = null;
  if (state.live === live) state.live = null;
  render("follow");
}

// EventSource retries a dropped stream itself; it gives up only when refused (a run deleted meanwhile), so the chat is read afresh.
function lost(live) {
  if (live.source.readyState !== EventSource.CLOSED) return report(RECONNECTING);
  if (state.live === live) state.live = null;
  if (state.problem === RECONNECTING) state.problem = null;
  Object.assign(live.chat, { live: null, turns: null });
  if (live.chat === state.current) select(live.chat);
  else render();
}

async function send() {
  const input = byId("input");
  const prompt = input.value.trim();
  const chat = state.current;
  if (!prompt || state.live || state.sending || !chat?.turns) return;
  state.sending = true;
  let run;
  try {
    ({ run } = await request("POST", `api/chats/${chat.id}/runs`, { prompt }));
  } catch (error) {
    report(`Not sent: ${error.status === CONFLICT ? "this chat already has a run going" : error.message}`);
    return;
  } finally {
    state.sending = false;
  }
  if (input.value.trim() === prompt) input.value = "";
  grow();
  // as the server titles it
  if (!chat.turns.length && chat.title === NEW_TITLE) chat.title = prompt.split("\n")[0].trim();
  const fold = newFold();
  Object.assign(fold.turn, { prompt, started: Date.now() / MS_PER_SECOND });
  chat.turns.push(fold.turn);
  state.problem = null;
  follow(chat, run, fold);
  render("bottom");
}

async function stop() {
  const live = state.live;
  if (!live || live.stopping) return;
  live.stopping = true;
  renderComposer();
  try {
    await request("POST", `api/runs/${live.run}/stop`);
  } catch (error) {
    // a conflict: the run has just ended, and its turn.end is on its way
    if (error.status === CONFLICT) return;
    live.stopping = false;
    report(`Not stopped: ${error.message}`);
  }
}

function grow() {
  const input = byId("input");
  input.style.height = "auto";
  input.style.height = `${input.scrollHeight}px`;
}

function isDark() {
  const theme = document.documentElement.dataset.theme;
  return theme ? theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
}

function labelTheme() {
  const next = isDark() ? "light" : "dark";
  byId("theme").textContent = next;
  byId("theme").setAttribute("aria-label", `Switch to ${next}`);
}

function toggleTheme() {
  const root = document.documentElement;
  root.dataset.theme = isDark() ? "light" : "dark";
  labelTheme();
  try {
    localStorage.setItem("theme", root.dataset.theme);
  } catch {
    // storage can be blocked; the choice then lasts this visit only
  }
}

function wire() {
  try {
    const theme = localStorage.getItem("theme");
    if (theme) document.documentElement.dataset.theme = theme;
  } catch {
    // no stored theme: follow the system's
  }
  labelTheme();
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", labelTheme);
  byId("theme").addEventListener("click", toggleTheme);
  byId("new-chat").addEventListener("click", newChat);
  byId("stop").addEventListener("click", stop);
  byId("namespace").addEventListener("click", pickNamespace);
  byId("model").addEventListener("click", pickModel);
  byId("folder").addEventListener("click", pickFolder);
  // a click on a popover's button leaves focus in the popover, so the click toggles it
  for (const id of ["namespace", "model", "folder"]) byId(id).addEventListener("mousedown", (e) => e.preventDefault());
  byId("menu").addEventListener("click", () => byId("app").classList.toggle("list-open"));
  byId("app").addEventListener("click", (e) => {
    if (!e.target.closest(".sidebar, .menu")) byId("app").classList.remove("list-open");
  });
  byId("composer").addEventListener("submit", (e) => {
    e.preventDefault();
    send();
  });
  byId("input").addEventListener("input", grow);
  byId("input").addEventListener("keydown", (e) => {
    if (e.key !== "Enter" || e.shiftKey || e.isComposing) return;
    e.preventDefault();
    send();
  });
  // Esc acts only on what this chat shows; the Library closes on an Esc left unused
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    const runHere = state.live?.chat === state.current;
    if (!ui.deleting && !runHere) return;
    e.preventDefault();
    if (ui.deleting) setUi({ deleting: null });
    else stop();
  });
  setInterval(() => {
    if (!state.live) return;
    frame = (frame + 1) % SPIN.length;
    for (const el of document.querySelectorAll(".spin")) el.textContent = SPIN[frame];
    for (const el of document.querySelectorAll("[data-since]")) el.textContent = formatSeconds(since(Number(el.dataset.since)));
  }, SPIN_MS);
}

// The namespaces a chat can pick, and the default one new chats start in.
async function loadLibrary() {
  let found;
  try {
    found = await request("GET", "api/library");
  } catch {
    // the pickers stay hidden; the Library panel says what went wrong
    return;
  }
  library.namespaces = found.namespaces.map(({ name }) => name);
  library.defaultNamespace = found.default_namespace;
  renderComposer();
}

// A run going in a chat is what the page was showing before a reload, so that chat opens first.
async function start() {
  try {
    state.chats = await request("GET", "api/chats");
  } catch (error) {
    byId("log").textContent = `Could not load the chats (${error.message}). Start the app with: uv run deep-reasoning`;
    return;
  }
  const first = state.chats.find((chat) => chat.live) ?? state.chats[0];
  if (first) select(first);
  else newChat();
}

export { PANEL_CLOSE, PANEL_OPEN, caret, closeOtherPanels, element, folderPicker, request, settingsChanged };

wire();
start();
loadLibrary();
// read ahead, so the model menu opens on its lists; a failure shows when the menu opens
loadModels().catch(() => {});
