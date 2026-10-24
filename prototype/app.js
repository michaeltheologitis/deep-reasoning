// The Deep Reasoning chat prototype: mock data, no server, nothing saved.
const THINK_MS = 1100;
const CELL_MS = 550;
const ANSWER_TICK_MS = 40;
const WORDS_PER_TICK = 6;
const SPIN_MS = 120;
const STICK_PX = 80;
// ︎ keeps ✳ a text glyph where the system would draw it as an emoji
const SPIN = ["·", "✢", "✳︎", "✶", "✻", "✽", "✻", "✶", "✳︎", "✢"];
const STATUS = {
  running: ["running", ""],
  failed: ["failed", "err"],
  exhausted: ["out of turns", "warn"],
  stopped: ["stopped", ""],
};
const OUTCOME = {
  exhausted: ["ran out of turns", "warn"],
  failed: ["failed", "err"],
};

const $ = (id) => document.getElementById(id);
const state = { chats: [], current: null, live: null, template: null };
const ui = { renaming: null, deleting: null };
const opened = new WeakSet();
const keys = new WeakMap();
let nextId = 1;
let frame = 0;

function h(tag, props, ...kids) {
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
const keyOf = (node) => {
  if (!keys.has(node)) keys.set(node, String(nextId++));
  return keys.get(node);
};

function fmtCost(usd) {
  if (usd == null) return null;
  if (usd === 0) return "$0";
  return `$${usd.toFixed(usd >= 0.01 ? 2 : 4)}`;
}

function fmtSeconds(seconds) {
  if (seconds == null) return null;
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
}

const spinner = () => h("span", { class: "spin" }, SPIN[frame]);
const clock = (start) => h("span", { "data-since": start }, fmtSeconds(since(start)));

// ── steps ────────────────────────────────────────────────────────────────

function describe(step) {
  if (step.kind === "think") return { label: step.text };
  const count = step.agents.length;
  if (count) return { label: count === 1 ? "Delegated to a sub-agent" : `Delegated to ${count} sub-agents` };
  if (isFinal(step)) return { label: "Final answer" };
  const [first, ...rest] = step.code.split("\n");
  return { tool: "Python", label: `(${first}${rest.length ? " …" : ""})` };
}

function finalValue(output) {
  const value = output.replace(/^FinalAnswer: /, "");
  return /^(['"]).*\1$/s.test(value) ? value.slice(1, -1) : value;
}

function out(text, { tone = "", full = false, more = null } = {}) {
  return h(
    "div",
    { class: `out ${tone} ${full ? "full" : ""}` },
    h("span", {}, "⎿"),
    h("span", { class: "text" }, text, more && h("span", { class: "more" }, more)),
  );
}

function renderOutput(cell, open, root) {
  const tone = cell.status === "failed" ? "err" : "";
  if (cell.status === "stopped") return null;
  if (cell.output == null) return cell.agents.length ? null : out("Running…");
  if (open) return out(cell.output, { tone, full: true });
  const lines = cell.output.trimEnd().split("\n");
  if (cell.status === "failed") return out(lines.at(-1), { tone });
  // the rows above already show what the sub-agents answered, and the answer below shows the root's
  if (cell.agents.length || (root && isFinal(cell))) return null;
  if (isFinal(cell)) return out(finalValue(cell.output));
  const more = lines.length > 1 ? ` … +${lines.length - 1} lines` : null;
  return out(lines[0] || "(no output)", { more });
}

function renderThink(step) {
  const open = opened.has(step);
  return h(
    "button",
    { type: "button", class: `think ${open ? "open" : ""}`, "aria-expanded": String(open), "data-key": keyOf(step), onclick: () => toggle(step) },
    h("span", {}, "✻"),
    h("span", { class: "body" }, step.text),
  );
}

function renderCell(cell, root) {
  const open = opened.has(cell);
  const { tool, label } = describe(cell);
  return h(
    "div",
    { class: `cell is-${cell.status}` },
    h(
      "button",
      { type: "button", class: "line", "aria-expanded": String(open), "data-key": keyOf(cell), onclick: () => toggle(cell) },
      h("span", { class: "glyph" }, "●"),
      h("span", { class: "head" }, tool && h("b", {}, tool), label),
    ),
    open && h("pre", { class: "code" }, cell.code),
    cell.agents.length > 0 && h("div", { class: "rows" }, cell.agents.map(renderAgent)),
    renderOutput(cell, open, root),
  );
}

const renderStep = (step, root) => (step.kind === "think" ? renderThink(step) : renderCell(step, root));

// ── sub-agents ───────────────────────────────────────────────────────────

function renderUnder(agent) {
  const [, tone] = STATUS[agent.status] ?? [];
  if (agent.status === "running") {
    const last = agent.steps.at(-1);
    if (!last) return null;
    const { tool = "", label } = describe(last);
    return out(tool + label);
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
    word && h("span", { class: `word ${tone}` }, word),
    running ? clock(agent.started) : fmtSeconds(agent.seconds),
    fmtCost(agent.cost),
  ].filter(Boolean);
  return h(
    "div",
    { class: `agent is-${agent.status}` },
    h(
      "button",
      { type: "button", class: "row", "aria-expanded": String(open), "data-key": keyOf(agent), onclick: () => toggle(agent) },
      h("span", { class: "caret" }, open ? "▾" : "▸"),
      h("span", { class: "task" }, agent.task),
      tags.filter(Boolean).map((tag) => h("span", { class: "tag" }, tag)),
      h("span", { class: "meta" }, running && [spinner(), " "], join(meta, " · ")),
    ),
    open
      ? h("div", { class: "children" }, agent.steps.map((step) => renderStep(step, false)), agent.status !== "running" && renderUnder(agent))
      : renderUnder(agent),
  );
}

// ── turns ────────────────────────────────────────────────────────────────

function renderAnswer(text) {
  const el = h("div", { class: "answer" });
  if (window.marked) el.innerHTML = window.marked.parse(text);
  else Object.assign(el, { textContent: text, style: "white-space: pre-wrap" });
  return el;
}

function renderRunMeta(turn) {
  const [word, tone] = OUTCOME[turn.outcome] ?? [];
  const parts = [word && h("span", { class: `word ${tone}` }, word), fmtSeconds(turn.seconds), fmtCost(turn.cost)];
  return h("div", { class: "run-meta" }, join(parts.filter(Boolean), " · "));
}

function renderTurn(turn) {
  const live = state.live?.turn === turn;
  return h(
    "section",
    { class: "turn" },
    h("div", { class: "user" }, h("span", { class: "prompt" }, "> "), turn.prompt),
    turn.steps.length > 0 && h("div", { class: "steps" }, turn.steps.map((step) => renderStep(step, true))),
    live &&
      turn.answer == null &&
      h("div", { class: "working" }, spinner(), " Reasoning… ", h("span", { class: "dim" }, "(", clock(state.live.started), " · esc to interrupt)")),
    turn.outcome === "stopped" && h("div", { class: "interrupted" }, "⎿  Stopped by you"),
    turn.answer != null && renderAnswer(turn.answer),
    turn.outcome && renderRunMeta(turn),
  );
}

function renderWelcome() {
  return h(
    "div",
    { class: "welcome" },
    h("div", { class: "hi" }, "✻ Deep Reasoning"),
    h("p", {}, "Ask anything. Each run shows its sub-agents as a tree you can open and shut."),
    h("p", {}, "Prototype: every message plays back the same mock run, the sky one. Press esc to stop it."),
  );
}

// ── the page ─────────────────────────────────────────────────────────────

function renderList() {
  const items = state.chats.map((chat) => {
    if (ui.renaming === chat) {
      const input = h("input", {
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
      return h("li", { class: "chat current" }, input);
    }
    if (ui.deleting === chat) {
      return h(
        "li",
        { class: "chat confirm" },
        "Delete this chat?",
        h("button", { type: "button", class: "yes", onclick: () => remove(chat) }, "Delete"),
        h("button", { type: "button", class: "no", onclick: () => setUi({ deleting: null }) }, "Keep"),
      );
    }
    const current = chat === state.current;
    const live = state.live?.chat === chat;
    return h(
      "li",
      { class: `chat ${current ? "current" : ""}` },
      h(
        "button",
        { type: "button", class: "pick", onclick: () => select(chat), ondblclick: () => setUi({ renaming: chat }) },
        h("span", { class: "mark" }, live ? spinner() : current ? "●" : ""),
        h("span", { class: "name" }, chat.title),
      ),
      h("button", { type: "button", class: "icon", title: "Rename", "aria-label": "Rename", onclick: () => setUi({ renaming: chat }) }, "✎"),
      h("button", { type: "button", class: "icon", title: "Delete", "aria-label": "Delete", onclick: () => setUi({ deleting: chat }) }, "✕"),
    );
  });
  $("chats").replaceChildren(...items);
}

function renderLog(scroll) {
  const chat = state.current;
  const box = $("scroll");
  const nearBottom = box.scrollHeight - box.scrollTop - box.clientHeight < STICK_PX;
  const focused = document.activeElement?.dataset?.key;
  $("title").textContent = chat.title;
  $("log").replaceChildren(...(chat.turns.length ? chat.turns.map(renderTurn) : [renderWelcome()]));
  if (scroll === "bottom" || (scroll === "follow" && nearBottom)) box.scrollTop = box.scrollHeight;
  if (focused) document.querySelector(`[data-key="${focused}"]`)?.focus();
}

function renderComposer() {
  const live = state.live;
  const here = live?.chat === state.current;
  $("stop").hidden = !here;
  if (here) $("hint").textContent = "";
  else if (live) $("hint").textContent = `a run is going in “${live.chat.title}”`;
  else $("hint").textContent = "enter to send · shift+enter for a new line";
  const total = state.current.turns.reduce((sum, turn) => sum + (turn.cost ?? 0), 0);
  $("total").textContent = total ? `${fmtCost(total)} this chat` : "";
}

function render(scroll = "keep") {
  if (!ui.renaming) renderList();
  renderLog(scroll);
  renderComposer();
}

function toggle(node) {
  if (opened.has(node)) opened.delete(node);
  else opened.add(node);
  renderLog("keep");
}

// ── chats ────────────────────────────────────────────────────────────────

function setUi(change) {
  Object.assign(ui, { renaming: null, deleting: null }, change);
  renderList();
}

function select(chat) {
  state.current = chat;
  ui.deleting = null;
  $("app").classList.remove("list-open");
  render("bottom");
  $("input").focus();
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

// ── a live run: plays the template run back step by step ─────────────────

function* together(sources, cell) {
  const kids = sources.map((source) => {
    const row = { ...source, steps: [], status: "running", result: null, cost: null, started: Date.now() };
    cell.agents.push(row);
    return { source, row, steps: play(source, row) };
  });
  while (kids.length) {
    for (const kid of [...kids]) {
      const { value, done } = kid.steps.next();
      if (!done) {
        yield value / kids.length;
        continue;
      }
      const { status, result, cost, seconds } = kid.source;
      Object.assign(kid.row, { status, result, cost, seconds });
      kids.splice(kids.indexOf(kid), 1);
    }
  }
}

function* play(source, target) {
  for (const step of source.steps) {
    if (step.kind === "think") {
      yield THINK_MS;
      target.steps.push({ ...step });
      continue;
    }
    yield CELL_MS;
    const cell = { ...step, agents: [], output: null, status: "running" };
    target.steps.push(cell);
    if (step.agents.length) yield* together(step.agents, cell);
    yield CELL_MS;
    Object.assign(cell, { output: step.output, status: step.status });
  }
}

function* playTurn(source, turn) {
  yield* play(source, turn);
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
  if (live.chat === state.current) renderLog("follow");
}

function send() {
  const input = $("input");
  const text = input.value.trim();
  if (!text || state.live) return;
  const chat = state.current;
  if (!chat.turns.length) chat.title = text.split("\n")[0];
  const turn = { prompt: text, steps: [], answer: null, outcome: null, cost: null, seconds: null };
  chat.turns.push(turn);
  input.value = "";
  grow();
  state.live = { chat, turn, started: Date.now(), steps: playTurn(state.template, turn), timer: null };
  advance();
  render("bottom");
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

// ── wiring ───────────────────────────────────────────────────────────────

function grow() {
  const input = $("input");
  input.style.height = "auto";
  input.style.height = `${input.scrollHeight}px`;
}

function isDark() {
  const theme = document.documentElement.dataset.theme;
  return theme ? theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
}

function labelTheme() {
  const next = isDark() ? "light" : "dark";
  $("theme").textContent = next;
  $("theme").setAttribute("aria-label", `Switch to ${next}`);
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
  $("theme").addEventListener("click", toggleTheme);
  $("new-chat").addEventListener("click", newChat);
  $("stop").addEventListener("click", stop);
  $("menu").addEventListener("click", () => $("app").classList.toggle("list-open"));
  $("app").addEventListener("click", (e) => {
    if (!e.target.closest(".sidebar, .menu")) $("app").classList.remove("list-open");
  });
  $("composer").addEventListener("submit", (e) => {
    e.preventDefault();
    send();
  });
  $("input").addEventListener("input", grow);
  $("input").addEventListener("keydown", (e) => {
    if (e.key !== "Enter" || e.shiftKey || e.isComposing) return;
    e.preventDefault();
    send();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    if (ui.deleting) setUi({ deleting: null });
    else stop();
  });
  setInterval(() => {
    if (!state.live) return;
    frame = (frame + 1) % SPIN.length;
    for (const el of document.querySelectorAll(".spin")) el.textContent = SPIN[frame];
    for (const el of document.querySelectorAll("[data-since]")) el.textContent = fmtSeconds(since(Number(el.dataset.since)));
  }, SPIN_MS);
}

async function load() {
  const urls = ["data/showcase.json", "data/recordings.json"];
  try {
    const [showcase, recordings] = await Promise.all(
      urls.map(async (url) => {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`${url} answered ${response.status}`);
        return response.json();
      }),
    );
    state.template = showcase.chats[0].turns[0];
    state.chats = [...showcase.chats, ...recordings.chats];
    state.current = state.chats[0];
    render("bottom");
  } catch (error) {
    $("log").textContent = `Could not load the mock chats (${error.message}). Serve this folder: python3 -m http.server 8000 --directory prototype`;
  }
}

wire();
load();
