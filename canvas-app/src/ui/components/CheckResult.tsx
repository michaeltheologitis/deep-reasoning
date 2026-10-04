// Check's report (D4 §2.1, §3.4): ✓ and what the agent is told, or ✗ and deep_reasoner's
// sentence, the tool's own frames, what it printed, and whether it can be saved anyway.

import {
  CANNOT_SAVE,
  CHECK_BUILT,
  PRINTED,
  SAVE_ANYWAY,
  SAVE_ANYWAY_NOTE,
} from "../texts";
import type { CheckReport } from "../types";

export interface CheckResultProps {
  report: CheckReport;
  /** Offered when Check's failure is one it cannot attribute (raised, timeout, unavailable). */
  onSaveAnyway?: () => void;
}

function headline(report: CheckReport): string {
  if (report.outcome === "built")
    return CHECK_BUILT((report.seconds ?? 0).toFixed(2));
  return `${report.ok ? "✓" : "✗"} ${report.message}`;
}

export function CheckResult(props: CheckResultProps) {
  const { report } = props;
  const example = report.example;
  return (
    <div
      class={`banner check ${report.ok ? "success" : "error"}`}
      role={report.ok ? "status" : "alert"}
      data-testid="dr-check-result"
      data-outcome={report.outcome}
    >
      <p class="message">{headline(report)}</p>
      {report.told !== null && (
        <pre data-testid="dr-check-told">{report.told}</pre>
      )}
      {report.traceback !== null && (
        <pre class="traceback">{report.traceback}</pre>
      )}
      {example !== null && (
        <p data-testid="dr-check-example">
          <code>{example.expression}</code> →{" "}
          <code class={example.ok ? "" : "errors"}>
            {example.ok ? example.value : example.error}
          </code>
        </p>
      )}
      {report.printed !== "" && (
        <>
          <p class="note">{PRINTED}</p>
          <pre data-testid="dr-check-printed">{report.printed}</pre>
        </>
      )}
      {!report.ok && !report.can_save_anyway && <p>{CANNOT_SAVE}</p>}
      {!report.ok && report.can_save_anyway && (
        <>
          <p>{SAVE_ANYWAY_NOTE}</p>
          {props.onSaveAnyway && (
            <button
              type="button"
              data-testid="dr-tool-save-anyway"
              onClick={props.onSaveAnyway}
            >
              {SAVE_ANYWAY}
            </button>
          )}
        </>
      )}
    </div>
  );
}
