// A tool of your own (D4 §2.1): its name, block and source, Check, the namespaces it is
// granted to, and Save, which the backend checks again.

import { useEffect, useState } from "preact/hooks";

import {
  type LibraryError,
  type ToolBody,
  checkTool,
  deleteTool,
  putTool,
} from "../api";
import { clearDraft, loadDraft, saveDraft } from "../drafts";
import { type OnBackendLost, attempt } from "../load";
import {
  CHECKING,
  DELETE_TOOL_CONFIRM,
  DISCARD_DRAFT,
  LABELS,
  NAME_FIXED,
  NEW_TOOL_SOURCE,
  RELOAD_ENTRY,
  SAVED_TOOL,
  SAVE_OVER,
  SAVING_CHECKING,
  TOOL_HELP,
  TOOL_LABELS,
  TRY_LABEL,
} from "../texts";
import { type ToolDraft, inheritedNotes, toolDraftKey } from "../tools";
import type {
  CheckReport,
  Effective,
  NamespaceRecord,
  ToolRecord,
} from "../types";
import { stringifyYaml } from "../yaml";
import { CheckResult } from "./CheckResult";
import { CodeField, ConfirmRow } from "./fields";
import { NamespaceChecklist } from "./pickers";
import { PythonField } from "./python";

export interface ToolEditorProps {
  record: ToolRecord | null; // null: + New tool
  namespaces: readonly NamespaceRecord[];
  effective: readonly Effective[];
  onSaved: (record: ToolRecord, created: boolean) => void;
  onDeleted: (name: string) => void;
  onBackendLost: OnBackendLost;
}

type Status =
  | { kind: "checking" | "saving" }
  | { kind: "report"; report: CheckReport }
  | { kind: "saved"; line: string }
  | { kind: "failed"; message: string }
  | { kind: "stale"; message: string; head: ToolRecord }
  | { kind: "confirm-delete" };

/** The block as the user edits it: factory_from is the Library's, so it is not shown. */
function shownBlock(record: ToolRecord): string {
  const { factory_from: _, ...block } = record.data;
  return stringifyYaml(block);
}

function fresh(record: ToolRecord | null): ToolDraft {
  if (record === null) {
    return {
      name: "",
      yaml: "factory: make\n",
      source: NEW_TOOL_SOURCE,
      example: "",
      grantedIn: [],
      baseVersion: 0,
    };
  }
  return {
    name: record.name,
    yaml: shownBlock(record),
    source: record.source ?? "",
    example: "",
    grantedIn: [...record.granted_in],
    baseVersion: record.version,
  };
}

export function ToolEditor(props: ToolEditorProps) {
  const { record, onBackendLost } = props;
  const key = toolDraftKey(record?.name ?? null);
  const [draft, setDraft] = useState<ToolDraft>(
    () => loadDraft<ToolDraft>(key) ?? fresh(record),
  );
  const [hasDraft, setHasDraft] = useState(
    () => loadDraft<ToolDraft>(key) !== null,
  );
  const [status, setStatus] = useState<Status | null>(null);
  // Counts the times the draft was replaced, so the source's editor starts over with it.
  const [generation, setGeneration] = useState(0);
  // A saved tool's ticks from the moment they are made until the stored record shows them.
  const [ticking, setTicking] = useState<string[] | null>(null);
  const stored = record?.granted_in.join("\n");
  useEffect(() => setTicking(null), [stored]);
  const sourced = record === null || record.source !== null;
  const names = props.namespaces.map((n) => n.name);
  const busy = status?.kind === "checking" || status?.kind === "saving";

  function change(fields: Partial<ToolDraft>) {
    const next = { ...draft, ...fields };
    setDraft(next);
    saveDraft(key, next);
    setHasDraft(true);
  }

  function restart(next: ToolDraft) {
    clearDraft(key);
    setHasDraft(false);
    setDraft(next);
    setGeneration((n) => n + 1);
  }

  function refused(error: LibraryError) {
    const head = error.head as ToolRecord | null;
    if (error.check) setStatus({ kind: "report", report: error.check });
    else if (error.code === "conflict" && head && record)
      setStatus({ kind: "stale", message: error.message, head });
    else setStatus({ kind: "failed", message: error.message });
  }

  async function check() {
    setStatus({ kind: "checking" });
    const result = await attempt(
      () =>
        checkTool(draft.name, {
          yaml: draft.yaml,
          source: sourced ? draft.source : null,
          example: draft.example.trim() || null,
        }),
      onBackendLost,
    );
    if (result.ok) setStatus({ kind: "report", report: result.value });
    else if (result.error) refused(result.error);
    else setStatus(null);
  }

  /** keepDraft: a grant-only save, which runs no Check and leaves the draft as it is. */
  async function write(body: ToolBody, keepDraft = false): Promise<boolean> {
    setStatus(keepDraft ? null : { kind: "saving" });
    const result = await attempt(
      () => putTool(draft.name, body),
      onBackendLost,
    );
    if (!result.ok) {
      if (result.error) refused(result.error);
      else setStatus(null);
      return false;
    }
    const saved = result.value.record;
    if (!keepDraft) restart(fresh(saved));
    setStatus({ kind: "saved", line: SAVED_TOOL(saved.name, saved.version) });
    props.onSaved(saved, result.value.created);
    return true;
  }

  const save = (acceptFailure: boolean, baseVersion = draft.baseVersion) =>
    write({
      yaml: draft.yaml,
      source: sourced ? draft.source : null,
      granted_in: record ? record.granted_in : draft.grantedIn,
      base_version: baseVersion,
      ...(acceptFailure && { accept_check_failure: true }),
    });

  /** A saved tool's grants are saved at once, with the head's block and source: a grant never
   * carries unsaved, unchecked code. */
  async function grant(grantedIn: string[]) {
    if (!record) return change({ grantedIn });
    setTicking(grantedIn);
    const saved = await write(
      {
        yaml: record.yaml,
        source: record.source,
        granted_in: grantedIn,
        base_version: record.version,
      },
      true,
    );
    if (!saved) setTicking(null);
  }

  async function remove() {
    if (!record) return;
    const result = await attempt(
      () => deleteTool(record.name, record.version),
      onBackendLost,
    );
    if (result.ok) {
      clearDraft(key);
      props.onDeleted(record.name);
    } else if (result.error) {
      refused(result.error);
    }
  }

  const inherited = record ? inheritedNotes(record.name, props.effective) : {};

  return (
    <form class="editor tool" onSubmit={(event) => event.preventDefault()}>
      <h2>
        {TOOL_LABELS.tools} › {record?.name ?? draft.name}
        {record && <span class="version"> v{record.version}</span>}
      </h2>
      <div class="field">
        <label for="dr-tool-name">{TOOL_LABELS.name}</label>
        <input
          id="dr-tool-name"
          value={draft.name}
          readOnly={record !== null}
          data-testid="dr-tool-name"
          onInput={(event) => change({ name: event.currentTarget.value })}
        />
        <p class="note">{NAME_FIXED}</p>
      </div>
      <CodeField
        label={`${TOOL_LABELS.block} (${TOOL_LABELS.blockNote})`}
        language="yaml"
        value={draft.yaml}
        onChange={(yaml) => change({ yaml })}
        testId="dr-tool-yaml"
      />
      {sourced && (
        <PythonField
          key={generation}
          label={TOOL_LABELS.source}
          value={draft.source}
          onChange={(source) => change({ source })}
          testId="dr-tool-source"
        />
      )}
      <div class="field">
        <label for="dr-tool-example">{TRY_LABEL}</label>
        <input
          id="dr-tool-example"
          class="code"
          value={draft.example}
          data-testid="dr-tool-example"
          onInput={(event) => change({ example: event.currentTarget.value })}
        />
      </div>
      <div class="actions">
        <button
          type="button"
          data-testid="dr-check"
          disabled={busy || draft.name === ""}
          onClick={check}
        >
          {TOOL_LABELS.check}
        </button>
      </div>
      {busy && (
        <p class="note" role="status" data-testid="dr-check-status">
          {status?.kind === "checking" ? CHECKING : SAVING_CHECKING}
        </p>
      )}
      {status?.kind === "report" && (
        <CheckResult
          report={status.report}
          onSaveAnyway={busy ? undefined : () => save(true)}
        />
      )}
      <NamespaceChecklist
        label={TOOL_LABELS.grantedIn}
        namespaces={names}
        checked={ticking ?? (record ? record.granted_in : draft.grantedIn)}
        inherited={inherited}
        testIdPrefix="dr-tool-grant"
        onChange={grant}
      />
      <details class="help" data-testid="dr-tool-help">
        <summary>{TOOL_LABELS.help}</summary>
        <p>{TOOL_HELP}</p>
      </details>
      <div class="actions">
        <button
          type="button"
          class="primary"
          data-testid="dr-tool-save"
          disabled={busy || draft.name === ""}
          onClick={() => save(false)}
        >
          {LABELS.save}
        </button>
        {record && (
          <button
            type="button"
            class="danger"
            data-testid="dr-tool-delete"
            onClick={() => setStatus({ kind: "confirm-delete" })}
          >
            {LABELS.delete}
          </button>
        )}
        {hasDraft && (
          <button
            type="button"
            data-testid="dr-discard-draft"
            onClick={() => {
              restart(fresh(record));
              setStatus(null);
            }}
          >
            {DISCARD_DRAFT}
          </button>
        )}
      </div>
      <p class="result" role="status" data-testid="dr-tool-result">
        {status?.kind === "saved" ? status.line : ""}
      </p>
      {status?.kind === "failed" && (
        <div class="banner error" role="alert" data-testid="dr-errors">
          <p class="message">{status.message}</p>
        </div>
      )}
      {status?.kind === "stale" && (
        <div class="banner warning" role="alert" data-testid="dr-conflict">
          <p>{status.message}</p>
          <button
            type="button"
            data-testid="dr-reload-entry"
            onClick={() => {
              restart(fresh(status.head));
              setStatus(null);
            }}
          >
            {RELOAD_ENTRY}
          </button>
          <button
            type="button"
            data-testid="dr-save-over"
            onClick={() => save(false, status.head.version)}
          >
            {SAVE_OVER}
          </button>
        </div>
      )}
      {status?.kind === "confirm-delete" && record && (
        <ConfirmRow
          sentence={DELETE_TOOL_CONFIRM(record.name)}
          confirm={LABELS.delete}
          confirmTestId="dr-tool-delete-confirm"
          onConfirm={remove}
          onCancel={() => setStatus(null)}
        />
      )}
    </form>
  );
}
