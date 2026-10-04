// The tool source's field: CodeMirror from the "editor" chunk, or D3's textarea when the
// chunk cannot be loaded (D4 §7.4).

import { useEffect, useId, useRef, useState } from "preact/hooks";

import type { PythonEditor } from "../editor/python";
import { CodeField } from "./fields";

export interface PythonFieldProps {
  label: string;
  /** The text the editor starts with. The editor owns its text from then on: a caller that
   * replaces the text (a discarded draft) mounts a new field with a new key. */
  value: string;
  onChange: (value: string) => void;
  testId: string;
}

export function PythonField(props: PythonFieldProps) {
  const host = useRef<HTMLDivElement>(null);
  const onChange = useRef(props.onChange);
  const [failed, setFailed] = useState(false);
  const labelId = useId();
  onChange.current = props.onChange;

  useEffect(() => {
    let alive = true;
    let editor: PythonEditor | null = null;
    import("../editor/python")
      .then(({ createPythonEditor }) => {
        if (!alive || !host.current) return;
        editor = createPythonEditor(host.current, props.value, (next) =>
          onChange.current(next),
        );
      })
      .catch(() => alive && setFailed(true));
    return () => {
      alive = false;
      editor?.destroy();
    };
  }, []);

  if (failed) {
    return (
      <CodeField
        label={props.label}
        language="python"
        value={props.value}
        onChange={props.onChange}
        testId={props.testId}
      />
    );
  }
  return (
    <div class="field">
      <span class="label" id={labelId}>
        {props.label}
      </span>
      <div
        class="python-editor"
        ref={host}
        role="group"
        aria-labelledby={labelId}
        data-testid={props.testId}
      />
    </div>
  );
}
