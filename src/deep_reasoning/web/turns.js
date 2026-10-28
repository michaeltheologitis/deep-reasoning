// A decomposition's turns checked as a worked example, as library.py's turn_problems checks them, in its words.
const THINK = /<think>[\s\S]*?<\/think>/;
const REPL_BLOCK = /<repl>([\s\S]*?)<\/repl>/g;
const OBSERVATION = /<observation>[\s\S]*?<\/observation>/;
const FINAL_ANSWER = /\bFinalAnswer\s*\(/;
const BETWEEN = {
  user: "the assistant's turn goes between them",
  assistant: "the user turn with the <observation> goes between them",
};
const NO_TASK = "There is no task: add a user turn holding it.";

const blocksOf = (content) => [...content.matchAll(REPL_BLOCK)].map((match) => match[1]);

// whether the code of the last <repl> block, the one the engine runs, calls FinalAnswer
function answers(content) {
  const code = blocksOf(content).at(-1);
  return code !== undefined && FINAL_ANSWER.test(code);
}

function replyProblems(label, content) {
  const blocks = blocksOf(content).length;
  return [
    !THINK.test(content) && `${label} has no <think>…</think>.`,
    blocks === 0 && `${label} has no <repl>…</repl> block.`,
    blocks > 1 && `${label} has ${blocks} <repl> blocks; the engine runs only the last, so keep one.`,
  ].filter(Boolean);
}

// previous: the latest turn before this one but a system one, null for none
function problemsOfTurn({ number, role, content }, previous) {
  const label = `Turn ${number} (${role})`;
  if (role === "system") return previous ? [`${label} comes after the task; system turns go before it.`] : [];
  const problems = [
    !previous && role === "assistant" && `${label} should be the user's task; start with a user turn.`,
    previous?.role === role && `${label} follows another ${role} turn; ${BETWEEN[role]}.`,
  ];
  if (role === "assistant") return [...problems, ...replyProblems(label, content)].filter(Boolean);
  // what a cell printed follows it, unless it answered: then a new message may
  const owed = previous?.role === "assistant" && !answers(previous.content) && !OBSERVATION.test(content);
  problems.push(owed && `${label} should hold the <observation>…</observation> that turn ${previous.number}'s code printed.`);
  return problems.filter(Boolean);
}

// messages: a decomposition's turns, each with its role and content, as the shape check passed them
export function turnProblems(messages) {
  const problems = [];
  let previous = null;
  messages.forEach(({ role, content }, i) => {
    const turn = { number: i + 1, role, content };
    problems.push(...problemsOfTurn(turn, previous));
    if (role !== "system") previous = turn;
  });
  if (!previous) return [NO_TASK];
  const { number, role, content } = previous;
  if (role === "user") problems.push(`It ends on turn ${number} (user); end with the assistant's turn that calls FinalAnswer(...).`);
  else if (!answers(content)) problems.push(`Turn ${number} (assistant), the last, should call FinalAnswer(...) in its <repl>.`);
  return problems;
}
