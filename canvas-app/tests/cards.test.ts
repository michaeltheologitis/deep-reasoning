import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative } from "node:path";

import { describe, expect, it } from "vitest";
import { parseAllDocuments } from "yaml";

import {
  type Card,
  type StepCard,
  addTurn,
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

  it("adds the missing output before the new step", () => {
    const cards = addTurn(newDecompositionCards());
    expect(cards.map((c) => c.kind)).toEqual([
      "task",
      "step",
      "output",
      "step",
    ]);
    expect(cards[2]).toEqual({ kind: "output", text: "", end: "" });
    expect(cards[3]).toEqual({
      kind: "step",
      think: "",
      thinkLayout: "inline",
      code: "",
      end: "\n",
    });
    expect(addTurn(cards).map((c) => c.kind)).toEqual([
      "task",
      "step",
      "output",
      "step",
      "output",
      "step",
    ]);
  });

  it("keeps an output the last step already has", () => {
    const cards = addTurn(addTurn(newDecompositionCards()).slice(0, 3));
    expect(cards.map((c) => c.kind)).toEqual([
      "task",
      "step",
      "output",
      "step",
    ]);
  });

  it("removes a step with its output, and an output alone", () => {
    const cards = addTurn(addTurn(newDecompositionCards()));
    expect(removeTurn(cards, 1).map((c) => c.kind)).toEqual([
      "task",
      "step",
      "output",
      "step",
    ]);
    expect(removeTurn(cards, 2).map((c) => c.kind)).toEqual([
      "task",
      "step",
      "step",
      "output",
      "step",
    ]);
  });

  it("numbers turns, an output sharing its step's number", () => {
    const cards = addTurn(addTurn(newDecompositionCards()));
    expect(turnNumbers(cards)).toEqual([1, 2, 2, 3, 3, 4]);
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
