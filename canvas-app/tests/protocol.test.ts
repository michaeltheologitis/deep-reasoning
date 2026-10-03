import { describe, expect, it } from "vitest";

import {
  type FrameParams,
  MAX_THEME_VALUE_LENGTH,
  frameSearch,
  isFrameMessage,
  readFrameParams,
} from "../src/shared/protocol";

const FULL: FrameParams = {
  tab: "create",
  parent: "http://localhost:8000",
  namespace: "course_advisor",
  started: true,
  cap: "7.5",
  focus: "rank-by-prerequisites",
  theme: {
    "--oh-surface": "#21252F",
    "font-family": '"SF Pro", sans-serif',
    "--oh-radius": "8px",
  },
};
const BARE: FrameParams = {
  tab: "browse",
  parent: null,
  namespace: null,
  started: false,
  cap: "5",
  focus: null,
  theme: {},
};

describe("the frame's URL", () => {
  it.each([
    ["every parameter", FULL],
    ["none but the defaults", BARE],
    ["a cap that is off", { ...FULL, cap: "off", started: false }],
  ])("round-trips %s", (_, params) => {
    expect(readFrameParams(frameSearch(params), false)).toEqual(params);
  });

  it("omits empty values", () => {
    expect(frameSearch(BARE)).toBe("?tab=browse&cap=5");
  });

  it.each([
    ["an unknown tab", "?tab=history", { tab: "browse" }],
    ["a cap that is not a number", "?cap=abc", { cap: "5" }],
    ["a theme that is not JSON", "?theme=%7Bnope", { theme: {} }],
    [
      "a theme that is a list",
      `?theme=${encodeURIComponent("[1]")}`,
      { theme: {} },
    ],
    [
      "a parent with a path",
      "?parent=http%3A%2F%2Flocalhost%3A8000%2Fx",
      { parent: null },
    ],
    [
      "a parent that is a script",
      "?parent=javascript%3Aalert(1)",
      { parent: null },
    ],
    ["started other than 1", "?started=yes", { started: false }],
  ])("falls back on %s", (_, search, expected) => {
    expect(readFrameParams(search, false)).toMatchObject(expected);
  });

  it("drops unsafe and unknown theme values and keeps the rest", () => {
    const theme = {
      "--oh-surface": "red; background: blue",
      "--oh-border": "url(http://evil.example/x.png)",
      "--oh-accent": "{}",
      "--oh-muted": "x".repeat(MAX_THEME_VALUE_LENGTH + 1),
      "--not-a-token": "#fff",
      "--oh-danger": "rgb(231, 106, 94)",
      "color-scheme": "dark",
    };
    const search = `?theme=${encodeURIComponent(JSON.stringify(theme))}`;
    expect(readFrameParams(search, false).theme).toEqual({
      "--oh-danger": "rgb(231, 106, 94)",
      "color-scheme": "dark",
    });
  });

  it("has no parent on the standalone page", () => {
    expect(readFrameParams(frameSearch(FULL), true).parent).toBeNull();
  });
});

describe("isFrameMessage", () => {
  it.each([
    [{ type: "dr-library/select-tab", tab: "browse", focus: null }, true],
    [
      { type: "dr-library/select-tab", tab: "browse", focus: "catalog-lookup" },
      true,
    ],
    [{ type: "dr-library/reload" }, true],
    [{ type: "dr-library/select-tab", tab: "history", focus: null }, false],
    [{ type: "dr-library/select-tab", tab: "browse" }, false],
    [{ type: "dr-library/reload", tab: "browse" }, false],
    [{ type: "dr-library/close" }, false],
    ["dr-library/reload", false],
    [null, false],
  ])("accepts the two shapes only: %j → %s", (value, accepted) => {
    expect(isFrameMessage(value)).toBe(accepted);
  });
});
