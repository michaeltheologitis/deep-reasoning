// The safety notice (D5 §2.3) and the Library's problems (D2's check).

import { getProblems } from "../api";
import { type OnBackendLost, useLoaded } from "../load";
import { PROBLEMS, SAFETY, SAFETY_NO_CAP, UNDERSTAND } from "../texts";

export interface SafetyNoticeProps {
  cap: string;
  variant: "first-open" | "banner";
  onUnderstood?: () => void;
}

export function SafetyNotice(props: SafetyNoticeProps) {
  const sentence = props.cap === "off" ? SAFETY_NO_CAP : SAFETY(props.cap);
  if (props.variant === "banner") {
    return (
      <div class="banner warning" role="note" data-testid="dr-notice">
        <span aria-hidden="true">⚠ </span>
        {sentence}
      </div>
    );
  }
  return (
    <div class="notice" role="dialog" aria-modal="true" data-testid="dr-notice">
      <p>{sentence}</p>
      <button
        type="button"
        class="primary"
        data-testid="dr-notice-ack"
        onClick={props.onUnderstood}
      >
        {UNDERSTAND}
      </button>
    </div>
  );
}

/** "⚠ 2 problems in the Library ▸", expanding to D2's sentences; nothing when there are none. */
export function ProblemsBanner(props: {
  rev: number;
  onBackendLost: OnBackendLost;
}) {
  const problems =
    useLoaded(getProblems, [props.rev], props.onBackendLost).data ?? [];
  if (problems.length === 0) return null;
  return (
    <details class="banner warning problems" data-testid="dr-problems">
      <summary>⚠ {PROBLEMS(problems.length)}</summary>
      <ul>
        {problems.map((problem) => (
          <li>{problem.message}</li>
        ))}
      </ul>
    </details>
  );
}
