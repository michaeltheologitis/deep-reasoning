// Shared fields: code and text areas, value editors, D2's field errors, confirmations, banners.

import type { ComponentChildren } from "preact";

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
