// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  DRAFT_PREFIX,
  clearDraft,
  loadDraft,
  saveDraft,
} from "../src/ui/drafts";

afterEach(() => {
  vi.unstubAllGlobals();
  localStorage.clear();
});

const BROKEN = {
  getItem: () => {
    throw new DOMException("denied", "SecurityError");
  },
  setItem: () => {
    throw new DOMException("full", "QuotaExceededError");
  },
  removeItem: () => {
    throw new DOMException("denied", "SecurityError");
  },
};

describe("drafts", () => {
  it("round-trip under their key", () => {
    saveDraft("create", { name: "rank", cards: [] });
    expect(localStorage.getItem(`${DRAFT_PREFIX}create`)).not.toBeNull();
    expect(loadDraft("create")).toEqual({ name: "rank", cards: [] });
    clearDraft("create");
    expect(loadDraft("create")).toBeNull();
  });

  it("are lost, and nothing else, when the storage throws", () => {
    vi.stubGlobal("localStorage", BROKEN);
    expect(() => saveDraft("create", { name: "rank" })).not.toThrow();
    expect(loadDraft("create")).toBeNull();
    expect(() => clearDraft("create")).not.toThrow();
  });

  it("are lost when what is stored is not JSON", () => {
    localStorage.setItem(`${DRAFT_PREFIX}create`, "{not json");
    expect(loadDraft("create")).toBeNull();
  });
});
