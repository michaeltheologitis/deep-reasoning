// Messages ↔ cards (§5.1): one card per message; a message that does not render back to exactly its
// own text is a raw card, so cardsToMessages(messagesToCards(m)) is m for every m.

import type { ChatMessage } from "./types";

export interface TaskCard {
  kind: "task";
  text: string;
}

export interface StepCard {
  kind: "step";
  think: string; // "" renders no <think>
  thinkLayout: "inline" | "block";
  code: string;
  end: "\n" | "";
}

export interface OutputCard {
  kind: "output";
  text: string;
  end: "\n" | "";
}

export interface RawCard {
  kind: "raw";
  role: ChatMessage["role"];
  content: string;
}

export type Card = TaskCard | StepCard | OutputCard | RawCard;

const THINK = "<think>";
const THINK_END = "</think>\n";
const REPL = "<repl>\n";
const REPL_END = "\n</repl>";
const OBSERVATION = "<observation>\n";
const OBSERVATION_END = "\n</observation>";
const MESSAGES_LOC = /^messages\.(\d+)(\.|$)/;

/** body + end, where end is one optional trailing newline after the closing tag. */
function closed(
  text: string,
  closing: string,
): { inner: string; end: "\n" | "" } | null {
  if (text.endsWith(`${closing}\n`))
    return { inner: text.slice(0, -closing.length - 1), end: "\n" };
  if (text.endsWith(closing))
    return { inner: text.slice(0, -closing.length), end: "" };
  return null;
}

/** (<think>T</think>\n | <think>\nT\n</think>\n)? <repl>\nC\n</repl> (\n)?, kept only if it renders back. */
export function parseStep(content: string): StepCard | null {
  let rest = content;
  let think = "";
  let thinkLayout: StepCard["thinkLayout"] = "inline";
  if (rest.startsWith(THINK)) {
    const close = rest.indexOf(THINK_END);
    if (close < 0) return null;
    think = rest.slice(THINK.length, close);
    rest = rest.slice(close + THINK_END.length);
    if (think.length >= 2 && think.startsWith("\n") && think.endsWith("\n")) {
      think = think.slice(1, -1);
      thinkLayout = "block";
    }
  }
  if (!rest.startsWith(REPL)) return null;
  const code = closed(rest.slice(REPL.length), REPL_END);
  if (!code) return null;
  const card: StepCard = {
    kind: "step",
    think,
    thinkLayout,
    code: code.inner,
    end: code.end,
  };
  return renderStep(card) === content ? card : null;
}

export function renderStep(card: StepCard): string {
  const think =
    card.think === ""
      ? ""
      : card.thinkLayout === "inline"
        ? `${THINK}${card.think}${THINK_END}`
        : `${THINK}\n${card.think}\n${THINK_END}`;
  return `${think}${REPL}${card.code}${REPL_END}${card.end}`;
}

/** <observation>\nO\n</observation> (\n)?, kept only if it renders back. */
export function parseOutput(content: string): OutputCard | null {
  if (!content.startsWith(OBSERVATION)) return null;
  const text = closed(content.slice(OBSERVATION.length), OBSERVATION_END);
  if (!text) return null;
  const card: OutputCard = { kind: "output", text: text.inner, end: text.end };
  return renderOutput(card) === content ? card : null;
}

export function renderOutput(card: OutputCard): string {
  return `${OBSERVATION}${card.text}${OBSERVATION_END}${card.end}`;
}

/** user: an output directly after a step, else a task; assistant: a step; anything else raw. */
export function messagesToCards(messages: readonly ChatMessage[]): Card[] {
  const cards: Card[] = [];
  for (const { role, content } of messages) {
    const card: Card | null =
      role === "assistant"
        ? parseStep(content)
        : role === "user"
          ? (cards.at(-1)?.kind === "step" && parseOutput(content)) || {
              kind: "task",
              text: content,
            }
          : null;
    cards.push(card ?? { kind: "raw", role, content });
  }
  return cards;
}

export function cardsToMessages(cards: readonly Card[]): ChatMessage[] {
  return cards.map((card): ChatMessage => {
    switch (card.kind) {
      case "task":
        return { role: "user", content: card.text };
      case "step":
        return { role: "assistant", content: renderStep(card) };
      case "output":
        return { role: "user", content: renderOutput(card) };
      case "raw":
        return { role: card.role, content: card.content };
    }
  });
}

function emptyStep(code = ""): StepCard {
  return { kind: "step", think: "", thinkLayout: "inline", code, end: "\n" };
}

/** A task card and one step whose code is FinalAnswer(...). */
export function newDecompositionCards(): Card[] {
  return [{ kind: "task", text: "" }, emptyStep("FinalAnswer(...)")];
}

/** A new turn at the end: an empty output card if the last card is a step, then an empty step
 * (after a trailing output, the step that output lacks). */
export function addTurn(cards: readonly Card[]): Card[] {
  const output: Card[] =
    cards.at(-1)?.kind === "step"
      ? [{ kind: "output", text: "", end: "" }]
      : [];
  return [...cards, ...output, emptyStep()];
}

/** Card indices by group: an output and the step directly after it are one turn; every other
 * card is a group of its own. */
export function cardGroups(cards: readonly Card[]): number[][] {
  const groups: number[][] = [];
  cards.forEach((card, i) => {
    if (card.kind === "step" && cards[i - 1]?.kind === "output") {
      groups.at(-1)!.push(i);
    } else {
      groups.push([i]);
    }
  });
  return groups;
}

/** Removes the group holding card index, and the output after it if no step would precede that
 * output: an output always follows a step. */
export function removeTurn(cards: readonly Card[], index: number): Card[] {
  const group = cardGroups(cards).find((g) => g.includes(index));
  if (!group) return [...cards];
  const start = group[0]!;
  let end = group.at(-1)! + 1;
  if (cards[start - 1]?.kind !== "step" && cards[end]?.kind === "output") end++;
  return cards.filter((_, i) => i < start || i >= end);
}

/** Turns numbered 1, 2, 3… by group: a step, an output with the step after it, or an output with
 * no step after it. Task and raw cards are no turn (null). */
export function turnNumbers(cards: readonly Card[]): (number | null)[] {
  const numbers: (number | null)[] = cards.map(() => null);
  let turn = 0;
  for (const group of cardGroups(cards)) {
    const kind = cards[group[0]!]!.kind;
    if (kind !== "step" && kind !== "output") continue;
    turn++;
    for (const i of group) numbers[i] = turn;
  }
  return numbers;
}

/** "messages.3.content" → 3; null for any other location. */
export function cardIndexForLoc(loc: string): number | null {
  const found = MESSAGES_LOC.exec(loc);
  return found ? Number(found[1]) : null;
}
