// Canvas's look in the frame: its tokens from the frame's URL, over Canvas's dark defaults.

export const DEFAULT_THEME: Readonly<Record<string, string>> = {
  "--oh-surface": "#21252F",
  "--oh-surface-raised": "#2C313F",
  "--oh-surface-deep": "#05070A",
  "--oh-foreground": "#EEF2F7",
  "--oh-muted": "#A3B0C4",
  "--oh-text-secondary": "#C3CDDC",
  "--oh-text-dim": "#7E8A9E",
  "--oh-border": "#4B5468",
  "--oh-border-subtle": "#383F50",
  "--oh-border-input": "#4B5468",
  "--oh-color-primary": "#c9b974",
  "--oh-accent": "#c9b974",
  "--oh-accent-foreground": "#0B0E14",
  "--oh-danger": "#e76a5e",
  "--oh-success": "#a5e75e",
  "--oh-warning": "#c9b974",
  "--oh-interactive-hover": "#4B5468",
  "--oh-interactive-active": "#383F50",
  "--oh-focus": "#ffffff",
  "--oh-radius": "8px",
  "--oh-field-radius": "8px",
  "color-scheme": "dark",
  "font-family":
    '-apple-system, "SF Pro", BlinkMacSystemFont, "Segoe UI", "Roboto", "Ubuntu", sans-serif',
};

export const POLL_MS = 3_000;

export function applyTheme(
  theme: Readonly<Record<string, string>>,
  root: HTMLElement,
): void {
  for (const [token, value] of Object.entries({ ...DEFAULT_THEME, ...theme })) {
    root.style.setProperty(token, value);
  }
}
