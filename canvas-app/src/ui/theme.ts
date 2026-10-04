// Canvas's look in the frame: its tokens from the frame's URL, over Canvas's dark defaults.

import { DEFAULT_THEME } from "../shared/protocol";

export function applyTheme(
  theme: Readonly<Record<string, string>>,
  root: HTMLElement,
): void {
  for (const [token, value] of Object.entries({ ...DEFAULT_THEME, ...theme })) {
    root.style.setProperty(token, value);
  }
}
