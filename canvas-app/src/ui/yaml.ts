// YAML 1.1, as PyYAML (and so dr) reads it: `on`, `yes`, `0777` and `1:30` mean here what they mean
// in a config file.

import { YAMLParseError, parse, stringify } from "yaml";

export class YamlSyntaxError extends Error {}

/** version "1.1", uniqueKeys false; a syntax error throws YamlSyntaxError with its message. */
export function parseYaml(text: string): unknown {
  try {
    return parse(text, { version: "1.1", uniqueKeys: false });
  } catch (error) {
    if (error instanceof YAMLParseError)
      throw new YamlSyntaxError(error.message);
    throw error;
  }
}

/** version "1.1", lineWidth 0, multi-line strings as literal blocks. */
export function stringifyYaml(value: unknown): string {
  return stringify(value, {
    version: "1.1",
    lineWidth: 0,
    blockQuote: "literal",
  });
}
