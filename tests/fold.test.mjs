// The fold on events recorded from real worker runs against the fake model (scripts/record_runs.py).
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { Worker } from "node:worker_threads";
import { foldEvent, foldEvents } from "../src/deep_reasoning/web/fold.js";

const FOLD_URL = new URL("../src/deep_reasoning/web/fold.js", import.meta.url).href;
const FOLD_TIMEOUT_MS = 5000;

const recorded = (name) => readFileSync(new URL(`runs/${name}.jsonl`, import.meta.url), "utf8").trim().split("\n").map(JSON.parse);
const ofKind = (events, kind) => events.filter((event) => event.kind === kind);
const last = (events) => events.at(-1);
const sum = (numbers) => numbers.reduce((total, number) => total + number, 0);
const costOf = (events, node) => sum(ofKind(events, "usage").filter((event) => event.node === node).map((event) => event.cost));
const cells = (holder) => holder.steps.filter((step) => step.kind === "cell");
const rowsOf = (holder) => cells(holder).flatMap((cell) => cell.agents);

function allRows(holder) {
  return rowsOf(holder).flatMap((row) => [row, ...allRows(row)]);
}

function allCells(holder) {
  return [...cells(holder), ...rowsOf(holder).flatMap(allCells)];
}

// Folds in a worker, so a fold that never returns fails its test instead of hanging the run: node:test's timeout can't stop a loop.
function foldInWorker(events) {
  const source = `
    const { parentPort, workerData } = require("node:worker_threads");
    import(workerData.url).then(({ foldEvents }) => {
      const { turn, latest } = foldEvents(workerData.events);
      parentPort.postMessage({ turn, latest });
    });`;
  const worker = new Worker(source, { eval: true, workerData: { url: FOLD_URL, events } });
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => worker.terminate().then(() => reject(new Error("the fold never returned"))), FOLD_TIMEOUT_MS);
    worker.once("message", (fold) => {
      clearTimeout(timer);
      worker.terminate().then(() => resolve(fold));
    });
    worker.once("error", (error) => {
      clearTimeout(timer);
      reject(error);
    });
  });
}

// What a crafted file may hold and no run writes: sub-agents 2 and 3 each named as the other's parent.
const parentCycle = [
  { seq: 1, t: 0, kind: "turn.start", prompt: "Loop." },
  { seq: 2, t: 0, kind: "agent.start", node: 1, parent: null, cell: null },
  { seq: 3, t: 1, kind: "cell.start", node: 1, cell: 1, code: "subagent('A.')" },
  { seq: 4, t: 2, kind: "agent.start", node: 2, parent: 3, cell: 1, task: "A.", drive: 1 },
  { seq: 5, t: 2, kind: "agent.start", node: 3, parent: 2, cell: 1, task: "B.", drive: 1 },
];

test("a saved turn has the prompt, the answer and the run's own totals", () => {
  const events = recorded("fanout");
  const { turn } = foldEvents(events);
  const end = last(events);
  assert.equal(turn.prompt, "Summarize two courses.");
  assert.deepEqual([turn.outcome, turn.answer, turn.cost, turn.seconds], [end.outcome, end.answer, end.cost, end.seconds]);
  assert.equal(turn.started, events[0].t);
});

test("a turn keeps the model and namespace its run started on", () => {
  const [start] = recorded("fanout");
  const { turn } = foldEvents([start]);
  assert.deepEqual([turn.model, turn.namespace], [start.model, start.namespace]);
  assert.deepEqual([turn.model, turn.namespace], ["gpt-6-luna", "root"]);
});

test("a fan-out puts every sub-agent as a row under the cell that started it", () => {
  const events = recorded("fanout");
  const { turn } = foldEvents(events);
  assert.deepEqual(
    turn.steps.map((step) => step.kind),
    ["think", "cell", "cell"],
  );
  const [fanOut] = cells(turn);
  assert.match(fanOut.code, /run_all/);
  assert.equal(fanOut.status, "done");
  assert.deepEqual(
    fanOut.agents.map((row) => [row.task, row.status, row.result, row.drive]),
    [
      ["Summarize C1.", "done", "C1: 3", 1],
      ["Summarize C2.", "done", "C2: 4", 1],
    ],
  );
  assert.equal(fanOut.agents[0].steps.length, 2);
});

test("a row's time runs from its agent's start to its end, and its cost is its calls'", () => {
  const events = recorded("fanout");
  const { turn } = foldEvents(events);
  const starts = ofKind(events, "agent.start").filter((event) => event.parent != null);
  const ends = new Map(ofKind(events, "agent.end").map((event) => [event.node, event]));
  for (const [row, start] of rowsOf(turn).map((row, i) => [row, starts[i]])) {
    assert.equal(row.seconds, ends.get(start.node).t - start.t);
    assert.equal(row.cost, costOf(events, start.node));
  }
});

test("a nested sub-agent's cost counts for every agent above it", () => {
  const events = recorded("nested");
  const { turn } = foldEvents(events);
  const [survey] = rowsOf(turn);
  const [read] = rowsOf(survey);
  assert.deepEqual([survey.task, read.task], ["Survey CS.", "Read CS101."]);
  const [, surveyNode, readNode] = ofKind(events, "agent.start").map((event) => event.node);
  assert.equal(read.cost, costOf(events, readNode));
  assert.ok(Math.abs(survey.cost - (costOf(events, surveyNode) + read.cost)) < 1e-12);
});

test("the newest step comes with the tasks of the sub-agents above it", () => {
  const events = recorded("nested");
  const upTo = events.findIndex((event) => event.kind === "cell.start" && event.code.startsWith("FinalAnswer('CS101"));
  const fold = foldEvents(events.slice(0, upTo + 1));
  assert.deepEqual(fold.latest.tasks, ["Survey CS.", "Read CS101."]);
  assert.equal(fold.latest.step.code, "FinalAnswer('CS101 is light')");
});

test("a second drive of one sub-agent is a row of its own", () => {
  const { turn } = foldEvents(recorded("drives"));
  const [cell] = cells(turn);
  assert.deepEqual(
    cell.agents.map((row) => [row.task, row.drive, row.result, row.steps.length]),
    [
      ["Note that the answer is 42.", 1, "42", 1],
      ["Say it again.", 2, "again 42", 1],
    ],
  );
});

test("a failed cell and a failed sub-agent keep their status, and the failure shows as the row's result", () => {
  const events = recorded("failing");
  const { turn } = foldEvents(events);
  const [divide, delegate] = cells(turn);
  assert.equal(divide.status, "failed");
  assert.match(divide.output, /ZeroDivisionError/);
  const [broken] = delegate.agents;
  assert.equal(broken.status, "failed");
  assert.equal(broken.result, ofKind(events, "agent.end")[0].detail);
  assert.equal(turn.outcome, "answered");
});

test("an exhausted sub-agent and turn keep their outcome", () => {
  const { turn } = foldEvents(recorded("exhausted"));
  assert.deepEqual(
    rowsOf(turn).map((row) => row.status),
    ["exhausted"],
  );
  assert.equal(turn.outcome, "exhausted");
  assert.match(turn.answer, /failed to produce a final answer/);
});

for (const name of ["stopped", "killed"]) {
  test(`a ${name} run leaves nothing running`, () => {
    const events = recorded(name);
    const { turn } = foldEvents(events);
    assert.equal(turn.outcome, "stopped");
    assert.equal(turn.answer, null);
    assert.ok(allRows(turn).length > 0);
    assert.ok(allRows(turn).every((row) => row.status === "stopped" && row.seconds > 0));
    assert.ok(allCells(turn).every((cell) => cell.status !== "running"));
  });
}

test("a row the run's end stopped is timed to that end", () => {
  const events = recorded("killed");
  const { turn } = foldEvents(events);
  const [sleeper] = rowsOf(turn);
  const start = ofKind(events, "agent.start")[1];
  assert.equal(sleeper.seconds, last(events).t - start.t);
  assert.ok(allCells(turn).every((cell) => cell.status === "stopped"));
});

test("one unpriced call makes every total above it unknown, not zero", () => {
  const { turn } = foldEvents(recorded("unpriced"));
  assert.equal(turn.cost, null);
  assert.ok(allRows(turn).every((row) => row.cost === null));
});

test("a running sub-agent is a running row, and it costs what its calls so far cost", () => {
  const events = recorded("fanout");
  const upTo = events.findIndex((event) => event.kind === "think" && event.text === "Easy.");
  const { turn } = foldEvents(events.slice(0, upTo + 1));
  const rows = rowsOf(turn);
  assert.deepEqual(
    rows.map((row) => row.status),
    ["running", "running"],
  );
  assert.equal(rows[0].started, ofKind(events, "agent.start")[1].t);
  assert.equal(rows[1].cost, costOf(events.slice(0, upTo + 1), 3));
  assert.equal(turn.outcome, null);
});

test("folding live, after catching up on the events so far, gives the saved turn", () => {
  const events = recorded("nested");
  const fold = foldEvents(events.slice(0, 9));
  for (const event of events.slice(9)) foldEvent(fold, event);
  assert.deepEqual(fold.turn, foldEvents(events).turn);
});

test("an event seen before, repeated or out of order, is ignored", () => {
  const events = recorded("fanout");
  const fold = foldEvents(events.slice(0, 10));
  assert.equal(foldEvent(fold, events[9]), false);
  assert.equal(foldEvent(fold, events[4]), false);
  const replayed = [...events.slice(0, 10), events[9], events[4], ...events.slice(5, 12), ...events.slice(10)];
  assert.deepEqual(foldEvents(replayed).turn, foldEvents(events).turn);
});

test("a call in a node named its own ancestor costs once for each agent in the cycle", async () => {
  const { turn } = await foldInWorker([...parentCycle, { seq: 6, t: 3, kind: "usage", node: 2, cost: 0.5 }]);
  assert.deepEqual(
    rowsOf(turn).map((row) => [row.task, row.cost]),
    [
      ["A.", 0.5],
      ["B.", 0.5],
    ],
  );
  assert.equal(turn.cost, null);
});

test("a step in a node named its own ancestor comes with each task above it once", async () => {
  const { turn, latest } = await foldInWorker([...parentCycle, { seq: 6, t: 3, kind: "think", node: 2, text: "Round." }]);
  assert.deepEqual(latest, { tasks: ["B.", "A."], step: { kind: "think", text: "Round." } });
  assert.deepEqual(rowsOf(turn)[0].steps, [latest.step]);
});
