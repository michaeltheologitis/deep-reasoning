// The Spend cap field (TASK-65 D7, D8): the profile's --spend-cap-usd. The page writes it, since only
// the page holds Canvas's session; the frame asks it by postMessage and shows its answer.

import { useEffect, useId, useState } from "preact/hooks";

import {
  type FrameMessage,
  type FrameParams,
  isPageMessage,
  isSpendCapInput,
} from "../../shared/protocol";
import {
  SPEND_CAP,
  SPEND_CAP_HELP,
  SPEND_CAP_INVALID,
  SPEND_CAP_OFF,
  SPEND_CAP_SAVE,
  SPEND_CAP_SAVED,
  SPEND_CAP_SAVING,
  SPEND_CAP_STANDALONE,
} from "../texts";

type Status =
  | { kind: "saving" }
  | { kind: "saved"; cap: string }
  | { kind: "refused"; message: string };

function statusLine(status: Status | null): string {
  if (status === null) return "";
  if (status.kind === "saving") return SPEND_CAP_SAVING;
  return status.kind === "saved" ? SPEND_CAP_SAVED(status.cap) : status.message;
}

export function SpendCapField(props: { params: FrameParams }) {
  const { cap, parent } = props.params;
  const id = useId();
  const [value, setValue] = useState(cap);
  const [status, setStatus] = useState<Status | null>(null);

  useEffect(() => {
    if (parent === null) return;
    const onMessage = (event: MessageEvent) => {
      if (
        event.source !== window.parent ||
        event.origin !== parent ||
        !isPageMessage(event.data)
      )
        return;
      if (event.data.type === "dr-library/spend-cap-saved") {
        setValue(event.data.cap);
        setStatus({ kind: "saved", cap: event.data.cap });
      } else {
        setStatus({ kind: "refused", message: event.data.message });
      }
    };
    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, [parent]);

  const heading = <h3 id={`${id}-heading`}>{SPEND_CAP}</h3>;
  if (cap === "off") {
    return (
      <section class="spend-cap" data-testid="dr-spend-cap">
        {heading}
        <p>{SPEND_CAP_OFF}</p>
      </section>
    );
  }
  if (parent === null) {
    return (
      <section class="spend-cap" data-testid="dr-spend-cap">
        {heading}
        <p>
          <strong>${cap}</strong> · {SPEND_CAP_STANDALONE}
        </p>
      </section>
    );
  }

  const save = (event: Event) => {
    event.preventDefault();
    if (!isSpendCapInput(value)) {
      setStatus({ kind: "refused", message: SPEND_CAP_INVALID });
      return;
    }
    const message: FrameMessage = {
      type: "dr-library/set-spend-cap",
      cap: value,
    };
    window.parent.postMessage(message, parent);
    setStatus({ kind: "saving" });
  };

  return (
    <section class="spend-cap" data-testid="dr-spend-cap">
      {heading}
      <p class="note" id={`${id}-help`}>
        {SPEND_CAP_HELP}
      </p>
      <form class="name-row" onSubmit={save}>
        <span aria-hidden="true">$</span>
        <input
          id={id}
          inputMode="decimal"
          value={value}
          aria-labelledby={`${id}-heading`}
          aria-describedby={`${id}-help`}
          data-testid="dr-spend-cap-input"
          onInput={(event) => setValue(event.currentTarget.value)}
        />
        <button
          type="submit"
          disabled={status?.kind === "saving"}
          data-testid="dr-spend-cap-save"
        >
          {SPEND_CAP_SAVE}
        </button>
      </form>
      <p
        class={status?.kind === "refused" ? "errors" : "result"}
        role="status"
        aria-live="polite"
        data-testid="dr-spend-cap-status"
      >
        {statusLine(status)}
      </p>
    </section>
  );
}
