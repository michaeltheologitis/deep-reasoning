// Folds a run's events into the turn the chat draws: the root's steps, each sub-agent as a row under the cell that started it, and the totals.

export function newFold() {
  return {
    turn: { prompt: "", steps: [], answer: null, outcome: null, detail: null, cost: null, seconds: null, started: null, model: null, namespace: null },
    seq: 0,
    // node → its holder (the turn for the root, else its row) and its parent's node
    nodes: new Map(),
    cells: new Map(),
    unpriced: new Set(),
    // the newest step, and the tasks of the sub-agents above it
    latest: null,
  };
}

// Folds one event in; false when it was ignored, as one already folded.
export function foldEvent(fold, event) {
  if (event.seq <= fold.seq) return false;
  fold.seq = event.seq;
  FOLDS[event.kind]?.(fold, event);
  return true;
}

export function foldEvents(events) {
  const fold = newFold();
  for (const event of events) foldEvent(fold, event);
  return fold;
}

const FOLDS = {
  "turn.start": (fold, { prompt, t, model, namespace }) => Object.assign(fold.turn, { prompt, started: t, model, namespace }),
  "agent.start": startAgent,
  think: (fold, event) => addStep(fold, event.node, { kind: "think", text: event.text }),
  "cell.start": startCell,
  "cell.end": endCell,
  usage: addUsage,
  "agent.end": endAgent,
  "turn.end": endTurn,
};

function startAgent(fold, event) {
  if (event.parent == null) {
    fold.nodes.set(event.node, { holder: fold.turn, parent: null });
    return;
  }
  const cell = fold.cells.get(event.cell);
  if (!cell) return;
  const { task, namespace, drive, t } = event;
  const row = { task, namespace, drive, status: "running", result: null, cost: null, seconds: null, started: t, steps: [] };
  cell.agents.push(row);
  fold.nodes.set(event.node, { holder: row, parent: event.parent });
}

// The node's entry and each one above it, once each: a file from someone else may name a node its own ancestor.
function lineage(fold, node) {
  const entries = new Set();
  for (let entry = fold.nodes.get(node); entry && !entries.has(entry); entry = fold.nodes.get(entry.parent)) entries.add(entry);
  return entries;
}

function addStep(fold, node, step) {
  const holder = fold.nodes.get(node)?.holder;
  if (!holder) return;
  holder.steps.push(step);
  const tasks = [...lineage(fold, node)].filter((entry) => entry.parent != null).map((entry) => entry.holder.task);
  fold.latest = { tasks: tasks.reverse(), step };
}

function startCell(fold, event) {
  const cell = { kind: "cell", code: event.code, output: null, status: "running", agents: [] };
  fold.cells.set(event.cell, cell);
  addStep(fold, event.node, cell);
}

function endCell(fold, event) {
  const cell = fold.cells.get(event.cell);
  if (cell) Object.assign(cell, { code: event.code, output: event.output, status: event.status });
}

// A call's cost counts for its agent, every agent above it and the turn; once one call is unpriced, so is each of their totals.
function addUsage(fold, event) {
  for (const { holder } of lineage(fold, event.node)) {
    if (event.cost == null) fold.unpriced.add(holder);
    holder.cost = fold.unpriced.has(holder) ? null : (holder.cost ?? 0) + event.cost;
  }
}

function endAgent(fold, event) {
  const row = fold.nodes.get(event.node)?.holder;
  if (!row || row === fold.turn) return;
  Object.assign(row, { status: event.status, result: event.result ?? event.detail, seconds: event.t - row.started });
}

function endTurn(fold, event) {
  const { outcome, answer, detail, cost, seconds } = event;
  Object.assign(fold.turn, { outcome, answer, detail, cost, seconds });
  markStopped(fold.turn, event.t);
}

// What the run left going when it ended was stopped with it.
function markStopped(holder, t) {
  for (const step of holder.steps) {
    if (step.kind !== "cell") continue;
    if (step.status === "running") step.status = "stopped";
    for (const agent of step.agents) {
      if (agent.status === "running") Object.assign(agent, { status: "stopped", seconds: t - agent.started });
      markStopped(agent, t);
    }
  }
}
