// The page's turn check on the cases test_library.py checks library.py's on, so the add form warns in the server's words.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { turnProblems } from "../src/deep_reasoning/web/turns.js";

const CASES = JSON.parse(readFileSync(new URL("turn_cases.json", import.meta.url), "utf8"));

for (const { case: name, messages, problems } of CASES) {
  test(`the page finds what the server finds in ${name}`, () => {
    assert.deepEqual(turnProblems(messages), problems);
  });
}
