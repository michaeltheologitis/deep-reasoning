// Decompositions (§2.2): every decomposition by where it is offered, and the editor for one.

import { useState } from "preact/hooks";

import {
  BackendUnavailable,
  LibraryError,
  getDecompositions,
  getEffective,
  getNamespaces,
  getProblems,
  getProfile,
} from "../api";
import { DecompositionEditor } from "../components/editor";
import { Banner } from "../components/fields";
import { useLoaded } from "../load";
import {
  BACKEND_LOST,
  EFFECTIVE_FAILED,
  INHERITED_ROW,
  LABELS,
} from "../texts";
import type {
  DecompositionRecord,
  Effective,
  NamespaceRecord,
  ProfileRecord,
} from "../types";
import type { TabProps } from "./props";

interface BrowseData {
  namespaces: NamespaceRecord[];
  decompositions: DecompositionRecord[];
  profile: ProfileRecord;
  /** null when D2 could not resolve inheritance; failure says why. */
  effective: Effective[] | null;
  failure: string | null;
}

interface Row {
  name: string;
  slug: string;
  version: number;
  useWhen: string | null;
  inheritedFrom: string | null;
}

interface Group {
  id: string; // top-level, a namespace, unattached
  title: string;
  rows: Row[];
}

// D2 answers a bare 500 when a head no longer validates (its resolution raises); the reason
// is then D2's own sentence for that head, from /problems.
async function effectiveOrWhy(): Promise<[Effective[] | null, string | null]> {
  try {
    return [await getEffective(), null];
  } catch (error) {
    if (error instanceof LibraryError) return [null, error.message];
    if (!(error instanceof BackendUnavailable) || error.status !== 500)
      throw error;
    const problems = await getProblems();
    return [
      null,
      problems.map((p) => p.message).join(" ") || BACKEND_LOST(error.status),
    ];
  }
}

async function loadBrowse(): Promise<BrowseData> {
  const [namespaces, decompositions, profile, [effective, failure]] =
    await Promise.all([
      getNamespaces(),
      getDecompositions(),
      getProfile(),
      effectiveOrWhy(),
    ]);
  return { namespaces, decompositions, profile, effective, failure };
}

const rowOf = (record: DecompositionRecord): Row => ({
  name: record.name,
  slug: record.slug,
  version: record.version,
  useWhen: record.use_when,
  inheritedFrom: null,
});

function groups(data: BrowseData): Group[] {
  const byName = new Map(data.decompositions.map((d) => [d.name, d]));
  const records = (names: readonly string[]) =>
    names.flatMap((name) =>
      byName.has(name) ? [rowOf(byName.get(name)!)] : [],
    );
  const found: Group[] = [];
  const top = records(data.profile.decompositions);
  if (top.length)
    found.push({ id: "top-level", title: LABELS.everyNamespace, rows: top });
  for (const namespace of data.namespaces) {
    const effective = data.effective?.find(
      (e) => e.namespace === namespace.name,
    );
    const rows = effective
      ? effective.decompositions.map((d) => ({
          name: d.name,
          slug: d.slug,
          version: d.version,
          useWhen: d.use_when,
          inheritedFrom: d.source === namespace.name ? null : d.source,
        }))
      : records(namespace.decompositions);
    found.push({ id: namespace.name, title: namespace.name, rows });
  }
  const unattached = data.decompositions.filter(
    (d) => !d.namespaces.length && !d.top_level,
  );
  if (unattached.length) {
    found.push({
      id: "unattached",
      title: LABELS.notAttached,
      rows: unattached.map(rowOf),
    });
  }
  return found;
}

export function BrowseTab(props: TabProps) {
  const [open, setOpen] = useState<string | null>(props.params.focus);
  const loaded = useLoaded(loadBrowse, [props.rev], props.onBackendLost);
  const data = loaded.data;
  if (!data)
    return loaded.error ? (
      <Banner kind="error">{loaded.error.message}</Banner>
    ) : null;
  const record = open
    ? data.decompositions.find((d) => d.slug === open)
    : undefined;
  if (record) {
    return (
      <section class="browse">
        <button
          type="button"
          class="link"
          data-testid="dr-back"
          onClick={() => setOpen(null)}
        >
          {LABELS.back}
        </button>
        <DecompositionEditor
          key={record.slug}
          record={record}
          namespaces={data.namespaces}
          params={props.params}
          health={props.health}
          draftKey={`decomposition.${record.slug}`}
          onSaved={() => loaded.reload()}
          onDeleted={() => {
            setOpen(null);
            loaded.reload();
          }}
          navigateTab={props.navigateTab}
          onBackendLost={props.onBackendLost}
        />
      </section>
    );
  }
  return (
    <section class="browse">
      {data.failure !== null && (
        <Banner kind="warning" testId="dr-effective-failed">
          {EFFECTIVE_FAILED(data.failure)}
        </Banner>
      )}
      {groups(data).map((group) => (
        <details open class="group" data-testid={`dr-group-${group.id}`}>
          <summary>{group.title}</summary>
          <ul class="rows">
            {group.rows.map((row) => (
              <li>
                <button
                  type="button"
                  class="row"
                  data-testid={`dr-row-${group.id}-${row.slug}`}
                  onClick={() => setOpen(row.slug)}
                >
                  <span class="name">{row.name}</span>
                  <span class="version">v{row.version}</span>
                  <span class="slash">/{row.slug}</span>
                  <span class="use-when">{row.useWhen ?? ""}</span>
                  {row.inheritedFrom !== null && (
                    <span class="inherited">
                      {INHERITED_ROW(row.inheritedFrom)}
                    </span>
                  )}
                </button>
              </li>
            ))}
          </ul>
        </details>
      ))}
    </section>
  );
}
