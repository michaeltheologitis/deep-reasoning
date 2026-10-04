// Unsaved edits, in the frame's localStorage: a storage that throws loses the draft and nothing else.

export const DRAFT_PREFIX = "dr-library.draft.";
export const SAFETY_ACK_KEY = "dr-library.safety-acknowledged";

// Reading or writing the storage throws in a private window, when it is full, or when the
// browser blocks site data for the frame; a draft is a convenience, so it is then dropped.
function read(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function write(key: string, value: string | null): void {
  try {
    if (value === null) localStorage.removeItem(key);
    else localStorage.setItem(key, value);
  } catch {
    return;
  }
}

export function loadDraft<T>(key: string): T | null {
  const stored = read(DRAFT_PREFIX + key);
  if (stored === null) return null;
  try {
    return JSON.parse(stored) as T;
  } catch {
    return null;
  }
}

export function saveDraft(key: string, value: unknown): void {
  write(DRAFT_PREFIX + key, JSON.stringify(value));
}

export function clearDraft(key: string): void {
  write(DRAFT_PREFIX + key, null);
}

export function safetyAcknowledged(): boolean {
  return read(SAFETY_ACK_KEY) === "1";
}

export function acknowledgeSafety(): void {
  write(SAFETY_ACK_KEY, "1");
}
