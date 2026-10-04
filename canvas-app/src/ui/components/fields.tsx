// Shared fields: code and text areas, value editors, D2's field errors, confirmations, banners.

import type { ComponentChildren } from "preact";
import { useId } from "preact/hooks";

import { CANCEL } from "../texts";
import type { FieldError } from "../types";

export interface CodeFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  /** A hint only, for a later editor with highlighting. */
  language: "yaml" | "python" | "text";
  errors?: readonly FieldError[];
  testId?: string;
  readOnly?: boolean;
  /** The id of errors shown elsewhere that describe this field. */
  describedBy?: string;
}

/** A monospace textarea that grows with its text. */
export function CodeField(props: CodeFieldProps) {
  const id = useId();
  const errorsId = `${id}-errors`;
  const rows = Math.max(2, props.value.split("\n").length);
  const describedBy = props.errors?.length ? errorsId : props.describedBy;
  return (
    <div class="field">
      <label for={id}>{props.label}</label>
      <textarea
        id={id}
        class={`code ${props.language}`}
        rows={rows}
        spellcheck={false}
        value={props.value}
        readOnly={props.readOnly}
        aria-describedby={describedBy}
        data-testid={props.testId}
        onInput={(event) => props.onChange(event.currentTarget.value)}
      />
      <FieldErrors id={errorsId} errors={props.errors} />
    </div>
  );
}

export function FieldErrors(props: {
  errors?: readonly FieldError[];
  id?: string;
  testId?: string;
  /** Show each error's location before its message. */
  located?: boolean;
}) {
  if (!props.errors?.length) return null;
  return (
    <ul class="errors" id={props.id} data-testid={props.testId}>
      {props.errors.map((error) => (
        <li>
          {props.located && error.loc
            ? `${error.loc}: ${error.msg}`
            : error.msg}
        </li>
      ))}
    </ul>
  );
}

export function Banner(props: {
  kind: "error" | "warning" | "info" | "success";
  testId?: string;
  children: ComponentChildren;
}) {
  return (
    <div
      class={`banner ${props.kind}`}
      role={props.kind === "error" ? "alert" : "status"}
      data-testid={props.testId}
    >
      {props.children}
    </div>
  );
}

export function ConfirmRow(props: {
  sentence: string;
  confirm: string;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  return (
    <div class="confirm" role="alertdialog" data-testid="dr-confirm">
      <p>{props.sentence}</p>
      <button
        type="button"
        class="danger"
        data-testid="dr-confirm-yes"
        onClick={props.onConfirm}
      >
        {props.confirm}
      </button>
      <button
        type="button"
        data-testid="dr-confirm-no"
        onClick={props.onCancel}
      >
        {CANCEL}
      </button>
    </div>
  );
}
