// The tool source's editor (D4 decision L): CodeMirror 6 with Python, in a chunk of its own
// ("editor") that only the tool editor loads.

import {
  defaultKeymap,
  history,
  historyKeymap,
  indentWithTab,
} from "@codemirror/commands";
import { pythonLanguage } from "@codemirror/lang-python";
import {
  LanguageSupport,
  bracketMatching,
  defaultHighlightStyle,
  indentOnInput,
  indentUnit,
  syntaxHighlighting,
} from "@codemirror/language";
import { EditorState } from "@codemirror/state";
import { EditorView, keymap, lineNumbers } from "@codemirror/view";

export interface PythonEditor {
  destroy(): void;
}

// Canvas's look, from the frame's theme tokens (the --oh-* variables).
const look = EditorView.theme({
  "&": {
    backgroundColor: "var(--oh-surface-deep)",
    color: "var(--oh-foreground)",
    border: "1px solid var(--oh-border-input)",
    borderRadius: "var(--oh-field-radius)",
  },
  "&.cm-focused": { outline: "2px solid var(--oh-focus)" },
  ".cm-content": {
    fontFamily:
      'source-code-pro, Menlo, Monaco, Consolas, "Courier New", monospace',
    caretColor: "var(--oh-foreground)",
  },
  ".cm-gutters": {
    backgroundColor: "var(--oh-surface-raised)",
    color: "var(--oh-muted)",
    border: "0",
  },
});

export function createPythonEditor(
  parent: HTMLElement,
  value: string,
  onChange: (value: string) => void,
): PythonEditor {
  const view = new EditorView({
    parent,
    state: EditorState.create({
      doc: value,
      extensions: [
        lineNumbers(),
        history(),
        indentOnInput(),
        bracketMatching(),
        syntaxHighlighting(defaultHighlightStyle),
        // The language alone: python() would bring autocompletion, and its size (§7.4's budget).
        new LanguageSupport(pythonLanguage),
        indentUnit.of("    "),
        keymap.of([indentWithTab, ...defaultKeymap, ...historyKeymap]),
        EditorView.updateListener.of((update) => {
          if (update.docChanged) onChange(update.state.doc.toString());
        }),
        look,
      ],
    }),
  });
  return { destroy: () => view.destroy() };
}
