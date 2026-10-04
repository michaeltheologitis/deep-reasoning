// YAML 1.1, as PyYAML (and so dr) reads it: `on`, `yes`, `0777` and `1:30` mean here what they mean
// in a config file.

import { parse, stringify } from "yaml";

export { YAMLParseError } from "yaml";

/** version "1.1", uniqueKeys false; a syntax error throws yaml's YAMLParseError. */
export function parseYaml(text: string): unknown {
  return parse(text, { version: "1.1", uniqueKeys: false });
}

/** version "1.1", lineWidth 0, multi-line strings as literal blocks. */
export function stringifyYaml(value: unknown): string {
  return stringify(value, {
    version: "1.1",
    lineWidth: 0,
    blockQuote: "literal",
  });
}
