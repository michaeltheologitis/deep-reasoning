// The Deep Reasoning chat prototype: mock data, no server, nothing saved.
const THINK_MS = 550;
const CELL_MS = 190;
const ANSWER_TICK_MS = 40;
const WORDS_PER_TICK = 6;
const SPIN_MS = 120;
const STICK_PX = 80;
const FIRST_ROWS = 20;
const MORE_ROWS = 100;
const TRAIL_CHARS = 22;
const TRAIL_PARTS = 3;
const TEMPLATE_CHAT = "degree";
const SECONDS_PER_MINUTE = 60;
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
const state = { chats: [], current: null, live: null, template: null };
const ui = { renaming: null, deleting: null };
const opened = new WeakSet();
const showingCode = new WeakSet();
const shown = new WeakMap();
const views = new WeakMap();
const keys = new WeakMap();
const counter = new Intl.NumberFormat();
let nextId = 1;
let frame = 0;

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
const since = (start) => (Date.now() - start) / 1000;
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

function summary(turn) {
  const [word, tone] = OUTCOME[turn.outcome] ?? [];
  const seconds = formatSeconds(turn.seconds);
  const agents = countAgents(turn);
  const lead = word ? [element("span", { class: `word ${tone}` }, word), ` after ${seconds}`] : `Reasoned for ${seconds}`;
  return join([lead, agents > 0 && plural(agents, "sub-agent"), formatCost(turn.cost)].filter(Boolean), " · ");
}

function liveSummary(turn) {
  const running = countAgents(turn, (agent) => agent.status === "running");
  const facts = [clock(state.live.started), running > 0 && `${plural(running, "sub-agent")} running`, "esc to interrupt"];
  return [element("span", { class: "working" }, "Reasoning… "), "(", join(facts.filter(Boolean), " · "), ")"];
}

function trailText(trail) {
  const parts = trail.length > TRAIL_PARTS ? [trail[0], "…", ...trail.slice(1 - TRAIL_PARTS)] : trail;
  return parts.join(" › ");
}

function renderTurn(turn) {
  const live = state.live?.turn === turn;
  const open = opened.has(turn);
  const el = element(
    "section",
    { class: "turn" },
    element("div", { class: "user" }, element("span", { class: "prompt" }, "> "), turn.prompt),
    toggler(turn, { class: "summary" }, [
      caret(open),
      live ? spinner() : element("span", {}, "✻"),
      element("span", { class: "text" }, live ? liveSummary(turn) : summary(turn)),
    ]),
    live && !open && state.live.trail.length > 0 && out(trailText(state.live.trail), { full: true }),
    open && element("div", { class: "steps" }, turn.steps.map((step) => renderStep(step, true))),
    turn.answer != null && renderAnswer(turn.answer),
  );
  return remember(turn, el, () => renderTurn(turn));
}

function renderWelcome() {
  return element(
    "div",
    { class: "welcome" },
    element("div", { class: "hi" }, "✻ Deep Reasoning"),
    element("p", {}, "Ask anything. Each run shows how it got its answer as a tree you open level by level."),
    element("p", {}, "Prototype: every message plays back the same mock run, the degree-planning one. Press esc to stop it."),
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
  const live = state.live?.chat === chat;
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

function renderLog(scroll) {
  const chat = state.current;
  const focused = document.activeElement?.dataset?.key;
  byId("title").textContent = chat.title;
  keepScroll(scroll, () => byId("log").replaceChildren(...(chat.turns.length ? chat.turns.map(renderTurn) : [renderWelcome()])));
  refocus(focused);
}

function renderComposer() {
  const live = state.live;
  const here = live?.chat === state.current;
  byId("stop").hidden = !here;
  if (here) byId("hint").textContent = "";
  else if (live) byId("hint").textContent = `a run is going in “${live.chat.title}”`;
  else byId("hint").textContent = "enter to send · shift+enter for a new line";
  const total = state.current.turns.reduce((sum, turn) => sum + (turn.cost ?? 0), 0);
  byId("total").textContent = total ? `${formatCost(total)} this chat` : "";
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

function select(chat) {
  state.current = chat;
  ui.deleting = null;
  byId("app").classList.remove("list-open");
  render("bottom");
  byId("input").focus();
}

function newChat() {
  const chat = { id: `new-${nextId++}`, title: "New chat", turns: [] };
  state.chats.unshift(chat);
  select(chat);
}

function remove(chat) {
  if (state.live?.chat === chat) stop();
  const index = state.chats.indexOf(chat);
  state.chats.splice(index, 1);
  ui.deleting = null;
  if (!state.chats.length) return newChat();
  if (state.current === chat) state.current = state.chats[Math.min(index, state.chats.length - 1)];
  render("bottom");
}

function finishRename(chat, title) {
  if (ui.renaming !== chat) return;
  ui.renaming = null;
  if (title.trim()) chat.title = title.trim();
  render();
}

// A live run plays the template run back step by step; sub-agents of one cell take turns.
function* together(sources, cell, path) {
  const kids = sources.map((source) => {
    const row = { ...source, steps: [], status: "running", result: null, cost: null, started: Date.now() };
    cell.agents.push(row);
    return playAgent(source, row, [...path, clip(source.task, TRAIL_CHARS)]);
  });
  while (kids.length) {
    for (const kid of [...kids]) {
      const { value, done } = kid.next();
      if (done) kids.splice(kids.indexOf(kid), 1);
      else yield value / kids.length;
    }
  }
}

function* playAgent(source, row, path) {
  yield* play(source, row, path);
  const { status, result, cost, seconds } = source;
  Object.assign(row, { status, result, cost, seconds });
}

function* play(source, target, path) {
  for (const step of source.steps) {
    yield step.kind === "think" ? THINK_MS : CELL_MS;
    state.live.trail = [...path, stepLabel(step, TRAIL_CHARS)];
    if (step.kind === "think") {
      target.steps.push({ ...step });
      continue;
    }
    const cell = { ...step, agents: [], output: null, status: "running" };
    target.steps.push(cell);
    if (step.agents.length) yield* together(step.agents, cell, path);
    yield CELL_MS;
    Object.assign(cell, { output: step.output, status: step.status });
  }
}

function* playTurn(source, turn) {
  yield* play(source, turn, []);
  const words = source.answer.split(/(\s+)/);
  for (let i = 1; i < words.length; i += WORDS_PER_TICK) {
    turn.answer = words.slice(0, i).join("");
    yield ANSWER_TICK_MS;
  }
  const { answer, outcome, cost, seconds } = source;
  Object.assign(turn, { answer, outcome, cost, seconds });
}

function advance() {
  const live = state.live;
  const { value, done } = live.steps.next();
  if (done) {
    state.live = null;
    render("follow");
    return;
  }
  live.timer = setTimeout(advance, value);
  // a tick changes only the live turn, so it leaves the rest of the log alone
  if (live.chat === state.current) keepScroll("follow", () => redraw(live.turn));
}

function send() {
  const input = byId("input");
  const text = input.value.trim();
  if (!text || state.live) return;
  const chat = state.current;
  if (!chat.turns.length) chat.title = text.split("\n")[0];
  const turn = { prompt: text, steps: [], answer: null, outcome: null, cost: null, seconds: null };
  chat.turns.push(turn);
  input.value = "";
  grow();
  state.live = { chat, turn, started: Date.now(), steps: playTurn(state.template, turn), timer: null, trail: [] };
  render("bottom");
  advance();
}

function markStopped(holder) {
  for (const step of holder.steps) {
    if (step.kind !== "cell") continue;
    if (step.status === "running") step.status = "stopped";
    for (const agent of step.agents) {
      if (agent.status === "running") Object.assign(agent, { status: "stopped", seconds: since(agent.started) });
      markStopped(agent);
    }
  }
}

function stop() {
  const live = state.live;
  if (!live) return;
  clearTimeout(live.timer);
  markStopped(live.turn);
  Object.assign(live.turn, { outcome: "stopped", seconds: since(live.started) });
  state.live = null;
  render("follow");
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

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${url} answered ${response.status}`);
  return response.json();
}

async function load() {
  const urls = ["data/showcase.json", "data/recordings.json"];
  try {
    const [showcase, recordings] = await Promise.all(urls.map(fetchJson));
    state.template = showcase.chats.find((chat) => chat.id === TEMPLATE_CHAT).turns[0];
    state.chats = [...showcase.chats, ...recordings.chats];
    state.current = state.chats[0];
    render("bottom");
  } catch (error) {
    byId("log").textContent = `Could not load the mock chats (${error.message}). Start the app with: uv run deep-reasoning`;
  }
}

wire();
load();
