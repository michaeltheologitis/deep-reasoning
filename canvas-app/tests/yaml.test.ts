import { describe, expect, it } from "vitest";

import { YAMLParseError, parseYaml, stringifyYaml } from "../src/ui/yaml";

describe("parseYaml reads as PyYAML (YAML 1.1) reads", () => {
  it.each<[string, unknown]>([
    ["v: yes", { v: true }],
    ["v: on", { v: true }],
    ["v: off", { v: false }],
    ["v: 0777", { v: 511 }],
    ["v: 1:30", { v: 90 }],
    ["v: 0x1f", { v: 31 }],
    ["v: ~", { v: null }],
    ["v: 2024-01-02", { v: new Date(Date.UTC(2024, 0, 2)) }],
    ["v: 1\nv: 2", { v: 2 }],
    ["v: |\n  first\n  second\n", { v: "first\nsecond\n" }],
    ['v: "yes"', { v: "yes" }],
  ])("%j", (text, value) => {
    expect(parseYaml(text)).toEqual(value);
  });

  it("throws a syntax error with its message", () => {
    expect(() => parseYaml("v: [1, 2")).toThrow(YAMLParseError);
    expect(() => parseYaml("v: [1, 2")).toThrow(/flow sequence/i);
  });
});

describe("stringifyYaml writes what PyYAML reads back to the same value", () => {
  const VALUE = {
    flag: "yes",
    switch: "on",
    mode: "0777",
    time: "1:30",
    count: 511,
    on_time: true,
    nothing: null,
    day: new Date(Date.UTC(2024, 0, 2)),
    text: "first line\nsecond line\n",
    list: [1, "two", { three: 3 }],
  };

  it("reparses to the same value", () => {
    expect(parseYaml(stringifyYaml(VALUE))).toEqual(VALUE);
  });

  it("quotes strings YAML 1.1 would read as something else", () => {
    const text = stringifyYaml({ flag: "yes", switch: "on", mode: "0777" });
    expect(text).toBe('flag: "yes"\nswitch: "on"\nmode: "0777"\n');
  });

  it("writes a date as a date and a multi-line string as a literal block", () => {
    const text = stringifyYaml({ day: VALUE.day, text: VALUE.text });
    expect(text).toBe(
      "day: 2024-01-02\ntext: |\n  first line\n  second line\n",
    );
  });
});
