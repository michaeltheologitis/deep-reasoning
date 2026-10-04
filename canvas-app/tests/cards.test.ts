import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative } from "node:path";

import { describe, expect, it } from "vitest";
import { parseAllDocuments } from "yaml";

import {
  type Card,
  type StepCard,
  addTurn,
  cardGroups,
  cardIndexForLoc,
  cardsToMessages,
  messagesToCards,
  newDecompositionCards,
  removeTurn,
  turnNumbers,
} from "../src/ui/cards";
import type { ChatMessage } from "../src/ui/types";

const user = (content: string): ChatMessage => ({ role: "user", content });
const assistant = (content: string): ChatMessage => ({
  role: "assistant",
  content,
});
const STEP = assistant(
  "<think>look it up</think>\n<repl>\nprint(1)\n</repl>\n",
);
const step = (over: Partial<StepCard> = {}): StepCard => ({
  kind: "step",
  think: "look it up",
  thinkLayout: "inline",
  code: "print(1)",
  end: "\n",
  ...over,
});

describe("messages ↔ cards", () => {
  it.each<[string, ChatMessage[], Card[]]>([
    [
      "a task",
      [user("Which comes first?")],
      [{ kind: "task", text: "Which comes first?" }],
    ],
    ["an inline think", [STEP], [step()]],
    [
      "a block think, no trailing newline",
      [
        assistant(
          "<think>\nfirst\nthen\n</think>\n<repl>\nx = 1\ny = 2\n</repl>",
        ),
      ],
      [
        step({
          think: "first\nthen",
          thinkLayout: "block",
          code: "x = 1\ny = 2",
          end: "",
        }),
      ],
    ],
    [
      "no think",
      [assistant("<repl>\nFinalAnswer(1)\n</repl>")],
      [step({ think: "", code: "FinalAnswer(1)", end: "" })],
    ],
    [
      "an inline think holding a newline",
      [assistant("<think>a\nb</think>\n<repl>\nc\n</repl>")],
      [step({ think: "a\nb", code: "c", end: "" })],
    ],
    [
      "an observation after a step",
      [STEP, user("<observation>\n1\n</observation>")],
      [step(), { kind: "output", text: "1", end: "" }],
    ],
    [
      "an observation with a trailing newline",
      [STEP, user("<observation>\n['CS201']\n</observation>\n")],
      [step(), { kind: "output", text: "['CS201']", end: "\n" }],
    ],
    [
      "an observation not after a step: a task",
      [user("<observation>\n1\n</observation>")],
      [{ kind: "task", text: "<observation>\n1\n</observation>" }],
    ],
    [
      "an empty think: raw, never rewritten",
      [assistant("<think></think>\n<repl>\nx\n</repl>")],
      [
        {
          kind: "raw",
          role: "assistant",
          content: "<think></think>\n<repl>\nx\n</repl>",
        },
      ],
    ],
    [
      "prose before the code: raw",
      [assistant("Let me look.\n<repl>\nx\n</repl>")],
      [
        {
          kind: "raw",
          role: "assistant",
          content: "Let me look.\n<repl>\nx\n</repl>",
        },
      ],
    ],
    [
      "prose after the code: raw",
      [assistant("<repl>\nx\n</repl>\nDone.")],
      [
        {
          kind: "raw",
          role: "assistant",
          content: "<repl>\nx\n</repl>\nDone.",
        },
      ],
    ],
    [
      "two trailing newlines: raw",
      [assistant("<repl>\nx\n</repl>\n\n")],
      [{ kind: "raw", role: "assistant", content: "<repl>\nx\n</repl>\n\n" }],
    ],
    [
      "a system message: raw",
      [{ role: "system", content: "Be brief." }],
      [{ kind: "raw", role: "system", content: "Be brief." }],
    ],
    [
      "a user message after a raw step: a task",
      [
        assistant("Hm.\n<repl>\nx\n</repl>"),
        user("<observation>\n1\n</observation>"),
      ],
      [
        { kind: "raw", role: "assistant", content: "Hm.\n<repl>\nx\n</repl>" },
        { kind: "task", text: "<observation>\n1\n</observation>" },
      ],
    ],
  ])("%s", (_, messages, cards) => {
    expect(messagesToCards(messages)).toEqual(cards);
    expect(cardsToMessages(cards)).toEqual(messages);
  });

  it("round trip is identity over generated messages", () => {
    let seed = 7;
    const random = () =>
      (seed = (seed * 1103515245 + 12345) % 2 ** 31) / 2 ** 31;
    const pick = <T>(items: readonly T[]): T =>
      items[Math.floor(random() * items.length)]!;
    const pieces = [
      "",
      "\n",
      "x",
      "print(1)\nprint(2)",
      "<think>",
      "</think>\n",
      "<think>t</think>\n",
      "<think>\nt\n</think>\n",
      "<repl>\n",
      "\n</repl>",
      "\n</repl>\n",
      "<observation>\n",
      "\n</observation>",
      " prose ",
    ];
    const roles = ["system", "user", "assistant"] as const;
    for (let n = 0; n < 2000; n++) {
      const messages = Array.from(
        { length: 1 + Math.floor(random() * 5) },
        () => ({
          role: pick(roles),
          content: Array.from({ length: Math.floor(random() * 6) }, () =>
            pick(pieces),
          ).join(""),
        }),
      );
      expect(cardsToMessages(messagesToCards(messages))).toEqual(messages);
    }
  });

  const beta = process.env.DR_BETA_CHECKOUT;

  it.runIf(!beta && process.env.CI)(
    "has deep_reasoner_beta's configs in CI",
    () => {
      expect(
        beta,
        "DR_BETA_CHECKOUT names no deep_reasoner_beta checkout",
      ).toBeTruthy();
    },
  );

  it.skipIf(!beta)(
    "round trip is identity over every decomposition in deep_reasoner_beta's configs",
    () => {
      const found = decompositionsIn(beta!, ["docs/configs", "configs"]);
      expect(found.length).toBeGreaterThan(30);
      for (const [where, messages] of found) {
        expect(cardsToMessages(messagesToCards(messages)), where).toEqual(
          messages,
        );
      }
    },
  );
});

describe("editing cards", () => {
  it("starts a decomposition with a task and a step that answers", () => {
    expect(newDecompositionCards()).toEqual([
      { kind: "task", text: "" },
      {
        kind: "step",
        think: "",
        thinkLayout: "inline",
        code: "FinalAnswer(...)",
        end: "\n",
      },
    ]);
  });

  it("adds a turn: an empty observation, then an empty step", () => {
    expect(addTurn(newDecompositionCards())).toEqual([
      ...newDecompositionCards(),
      { kind: "output", text: "", end: "" },
      { kind: "step", think: "", thinkLayout: "inline", code: "", end: "\n" },
    ]);
  });

  it.each<[string, string, string]>([
    ["after a step: an observation and a step", "t0 s1", "t0 s1 o s"],
    [
      "after a trailing observation: the step it lacks",
      "t0 s1 o2",
      "t0 s1 o2 s",
    ],
    ["after a task: a step", "t0", "t0 s"],
    ["always at the end", "t0 s1 t2", "t0 s1 t2 s"],
  ])("adds a turn %s", (_, before, after) => {
    expect(tokens(addTurn(deck(before)))).toBe(after);
  });

  it("groups an observation with the step after it; every other card stands alone", () => {
    expect(cardGroups(deck("r0 t1 s2 o3 s4 o5 t6 s7 s8"))).toEqual([
      [0],
      [1],
      [2],
      [3, 4],
      [5],
      [6],
      [7],
      [8],
    ]);
  });

  it.each<[string, string, (number | null)[]]>([
    ["the task is no turn; the first step is turn 1", "t0 s1", [null, 1]],
    [
      "an observation has the number of the step after it",
      "t0 s1 o2 s3 o4 s5",
      [null, 1, 2, 2, 3, 3],
    ],
    ["a trailing observation is the last turn", "t0 s1 o2", [null, 1, 2]],
    ["a step after a step is a turn", "t0 s1 s2", [null, 1, 2]],
    [
      "task and raw cards are no turn",
      "r0 t1 s2 o3 s4 t5 s6",
      [null, null, 1, 2, 2, null, 3],
    ],
  ])("numbers turns: %s", (_, cards, numbers) => {
    expect(turnNumbers(deck(cards))).toEqual(numbers);
  });

  it.each<[string, string, number, string]>([
    [
      "turn 1 with the observation after it, so the next step is turn 1",
      "t0 s1 o2 s3 o4 s5",
      1,
      "t0 s3 o4 s5",
    ],
    [
      "a middle turn: its observation and its step",
      "t0 s1 o2 s3 o4 s5",
      2,
      "t0 s1 o4 s5",
    ],
    ["a turn, from its step's index", "t0 s1 o2 s3 o4 s5", 3, "t0 s1 o4 s5"],
    ["the last turn", "t0 s1 o2 s3 o4 s5", 4, "t0 s1 o2 s3"],
    ["a trailing observation alone", "t0 s1 o2", 2, "t0 s1"],
    ["turn 1 with a trailing observation", "t0 s1 o2", 1, "t0"],
    [
      "a step after a step, keeping the next observation",
      "t0 s1 s2 o3 s4",
      2,
      "t0 s1 o3 s4",
    ],
    [
      "the first turn after a later task",
      "t0 s1 t2 s3 o4 s5",
      3,
      "t0 s1 t2 s5",
    ],
  ])("removes %s", (_, before, index, after) => {
    expect(tokens(removeTurn(deck(before), index))).toBe(after);
  });

  it("never leaves an observation that follows no step", () => {
    for (const cards of decks(6)) {
      turnNumbers(cards).forEach((turn, index) => {
        if (turn === null) return;
        const left = removeTurn(cards, index);
        const orphan = left.findIndex(
          (card, i) => card.kind === "output" && left[i - 1]?.kind !== "step",
        );
        expect(orphan, `${tokens(cards)} without card ${index}`).toBe(-1);
      });
    }
  });

  it.each([
    ["messages.3.content", 3],
    ["messages.0.role", 0],
    ["messages.12", 12],
    ["messages", null],
    ["name", null],
    ["", null],
  ])("finds the card of %s", (loc, index) => {
    expect(cardIndexForLoc(loc)).toBe(index);
  });
});

/** Cards from tokens such as "t0 s1 o2": the letter is the kind (task, step, observation, raw),
 * the rest its text. */
function deck(tokens: string): Card[] {
  return tokens.split(" ").map((token): Card => {
    const text = token.slice(1);
    switch (token[0]) {
      case "t":
        return { kind: "task", text };
      case "s":
        return step({ think: "", code: text });
      case "o":
        return { kind: "output", text, end: "" };
      default:
        return { kind: "raw", role: "system", content: text };
    }
  });
}

/** deck's inverse: an empty card is its letter alone. */
function tokens(cards: readonly Card[]): string {
  return cards
    .map((card) => {
      switch (card.kind) {
        case "task":
          return `t${card.text}`;
        case "step":
          return `s${card.code}`;
        case "output":
          return `o${card.text}`;
        case "raw":
          return `r${card.content}`;
      }
    })
    .join(" ");
}

/** Every deck of 1 to length cards the editor can hold: an observation always follows a step. */
function decks(length: number): Card[][] {
  let found: string[][] = [[]];
  const all: Card[][] = [];
  for (let n = 1; n <= length; n++) {
    found = found.flatMap((prefix) =>
      ["t", "s", "o", "r"]
        .filter((kind) => kind !== "o" || prefix.at(-1)?.startsWith("s"))
        .map((kind) => [...prefix, `${kind}${n}`]),
    );
    all.push(...found.map((prefix) => deck(prefix.join(" "))));
  }
  return all;
}

/** Every {name, messages: [{role, content}]} in the YAML files under folders, read in place. */
function decompositionsIn(
  root: string,
  folders: string[],
): [string, ChatMessage[]][] {
  const found: [string, ChatMessage[]][] = [];
  const visit = (value: unknown, where: string) => {
    if (Array.isArray(value))
      return value.forEach((item) => visit(item, where));
    if (!value || typeof value !== "object") return;
    const record = value as Record<string, unknown>;
    const messages = record.messages;
    if (
      typeof record.name === "string" &&
      Array.isArray(messages) &&
      messages.every(isMessage)
    ) {
      found.push([`${where}: ${record.name}`, messages]);
    }
    Object.values(record).forEach((item) => visit(item, where));
  };
  for (const file of folders.flatMap((folder) =>
    yamlFiles(join(root, folder)),
  )) {
    for (const document of parseAllDocuments(readFileSync(file, "utf8"), {
      version: "1.1",
    })) {
      visit(document.toJS({ maxAliasCount: -1 }), relative(root, file));
    }
  }
  return found;
}

function isMessage(value: unknown): value is ChatMessage {
  const message = value as Record<string, unknown> | null;
  return (
    typeof message?.role === "string" && typeof message.content === "string"
  );
}

function yamlFiles(directory: string): string[] {
  return readdirSync(directory).flatMap((name) => {
    const path = join(directory, name);
    if (statSync(path).isDirectory()) return yamlFiles(path);
    return name.endsWith(".yaml") ? [path] : [];
  });
}
