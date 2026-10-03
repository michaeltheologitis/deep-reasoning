// One namespace (Create decomposition) or some of them (Attached to, May spawn into).

import { LABELS } from "../texts";

export interface NamespacePickerProps {
  namespaces: readonly string[];
  value: string | null;
  onChange: (name: string) => void;
}

export function NamespacePicker(props: NamespacePickerProps) {
  return (
    <fieldset class="choices">
      <legend>{LABELS.namespace}</legend>
      {props.namespaces.map((name) => (
        <label>
          <input
            type="radio"
            name="namespace"
            checked={props.value === name}
            data-testid={`dr-namespace-${name}`}
            onChange={() => props.onChange(name)}
          />
          {name}
        </label>
      ))}
    </fieldset>
  );
}

export interface NamespaceChecklistProps {
  namespaces: readonly string[];
  checked: readonly string[];
  /** Shown checked and fixed, each with its note (where it comes from). */
  inherited?: Readonly<Record<string, string>>;
  onChange: (checked: string[]) => void;
  /** The legend; none when absent. */
  label?: string;
  /** dr-attached, dr-spawn: each box is <prefix>-<namespace>, the list <prefix>-list. */
  testIdPrefix?: string;
}

export function NamespaceChecklist(props: NamespaceChecklistProps) {
  const prefix = props.testIdPrefix ?? "dr-namespaces";
  const toggle = (name: string, on: boolean) => {
    const next = new Set(props.checked);
    if (on) next.add(name);
    else next.delete(name);
    props.onChange(props.namespaces.filter((n) => next.has(n)));
  };
  return (
    <fieldset class="choices" data-testid={`${prefix}-list`}>
      {props.label && <legend>{props.label}</legend>}
      {props.namespaces.map((name) => {
        const note = props.inherited?.[name];
        return (
          <label>
            <input
              type="checkbox"
              checked={note !== undefined || props.checked.includes(name)}
              disabled={note !== undefined}
              data-testid={`${prefix}-${name}`}
              onChange={(event) => toggle(name, event.currentTarget.checked)}
            />
            {name}
            {note !== undefined && <span class="note"> {note}</span>}
          </label>
        );
      })}
    </fieldset>
  );
}
