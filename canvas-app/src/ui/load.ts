// Reading and writing D2 from a tab: D2's refusals come back to the tab; a backend that does not
// answer goes to the app's footer (onBackendLost).

import { useEffect, useState } from "preact/hooks";

import { BackendUnavailable, LibraryError } from "./api";

export type OnBackendLost = (error: BackendUnavailable) => void;

export type Attempt<T> =
  | { ok: true; value: T }
  | { ok: false; error: LibraryError }
  | { ok: false; error: null }; // the backend did not answer; the footer says so

export async function attempt<T>(
  run: () => Promise<T>,
  onBackendLost: OnBackendLost,
): Promise<Attempt<T>> {
  try {
    return { ok: true, value: await run() };
  } catch (error) {
    if (error instanceof LibraryError) return { ok: false, error };
    if (error instanceof BackendUnavailable) {
      onBackendLost(error);
      return { ok: false, error: null };
    }
    throw error;
  }
}

export interface Loaded<T> {
  data: T | null;
  error: LibraryError | null;
  reload: () => void;
}

/** load() on mount, whenever deps change, and on reload(); a late answer to an older load is dropped. */
export function useLoaded<T>(
  load: () => Promise<T>,
  deps: readonly unknown[],
  onBackendLost: OnBackendLost,
): Loaded<T> {
  const [state, setState] = useState<{
    data: T | null;
    error: LibraryError | null;
  }>({
    data: null,
    error: null,
  });
  const [nonce, setNonce] = useState(0);
  useEffect(() => {
    let current = true;
    void attempt(load, onBackendLost).then((result) => {
      if (!current) return;
      if (result.ok) setState({ data: result.value, error: null });
      else if (result.error)
        setState((before) => ({ data: before.data, error: result.error }));
    });
    return () => {
      current = false;
    };
  }, [...deps, nonce]);
  return { ...state, reload: () => setNonce((n) => n + 1) };
}
