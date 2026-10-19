// The Library's problems (D2's check).

import { getProblems } from "../api";
import { type OnBackendLost, useLoaded } from "../load";
import { PROBLEMS } from "../texts";

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
