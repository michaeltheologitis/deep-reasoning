// The decomposition editor of §2.2 and §2.3: Create decomposition (record null) and an opened one.

import type { Ref } from "preact";
import { useEffect, useRef, useState } from "preact/hooks";

import type { FrameParams, TabId } from "../../shared/protocol";
import {
  type DecompositionBody,
  type LibraryError,
  deleteDecomposition,
  putDecomposition,
  validate,
} from "../api";
import {
  type Card,
  type RawCard,
  addTurn,
  cardGroups,
  cardIndexForLoc,
  cardsToMessages,
  messagesToCards,
  newDecompositionCards,
  removeTurn,
  turnNumbers,
} from "../cards";
import { clearDraft, loadDraft, saveDraft } from "../drafts";
import { ancestors } from "../tree";
import { type OnBackendLost, attempt } from "../load";
import {
  type DecompositionDraft,
  createBody,
  draftYaml,
  saveAsNextBody,
  updateBody,
} from "../save";
import {
  CANCEL,
  DELETE_CONFIRM,
  DISCARD_DRAFT,
  EXISTS,
  LABELS,
  NAME_REQUIRED,
  RAW_NOTE,
  RELOAD_ENTRY,
  RENAME,
  SAVED,
  SAVED_EDIT,
  SAVED_STARTED,
  SAVE_ANYWAY,
  SAVE_AS_NEXT,
  SAVE_OVER,
  SHOW_IN_DECOMPOSITIONS,
  YAML_NOT_DECOMPOSITION,
  YAML_SYNTAX,
} from "../texts";
import type {
  ChatMessage,
  DecompositionRecord,
  FieldError,
  Health,
  NamespaceRecord,
  ValidationResult,
} from "../types";
import { YAMLParseError, parseYaml, stringifyYaml } from "../yaml";
import { CodeField, ConfirmRow, FieldErrors } from "./fields";
import { NamespaceChecklist, NamespacePicker } from "./pickers";

const VALIDATE_AFTER_MS = 400;
const ROLES: readonly ChatMessage["role"][] = ["system", "user", "assistant"];

export interface DecompositionEditorProps {
  record: DecompositionRecord | null; // null: Create decomposition
  namespaces: readonly NamespaceRecord[];
  params: FrameParams;
  health: Health;
  draftKey: string;
  onSaved: (record: DecompositionRecord, created: boolean) => void;
  onDeleted?: () => void;
  navigateTab: (tab: TabId, focus: string | null) => void;
  onBackendLost: OnBackendLost;
}

/** What is kept as the draft: the decomposition and, for an opened one, its Attached to;
 * in Create decomposition, the namespace the user picked. */
interface Stored {
  draft: DecompositionDraft;
  attached: string[];
  picked?: string;
}

type Outcome =
  | { kind: "saved"; line: string; slug: string }
  | { kind: "name-required" }
  | { kind: "warnings"; warnings: string[] }
  | { kind: "exists"; head: DecompositionRecord }
  | { kind: "stale"; message: string; head: DecompositionRecord }
  | { kind: "failed"; message: string; errors: readonly FieldError[] }
  | { kind: "confirm-delete" };

const failed = (error: LibraryError): Outcome => ({
  kind: "failed",
  message: error.message,
  errors: error.errors,
});

function fresh(record: DecompositionRecord | null): Stored {
  if (record === null) {
    return {
      draft: {
        mode: "cards",
        name: "",
        useWhen: "",
        hint: "",
        cards: newDecompositionCards(),
        yaml: "",
        baseVersion: 0,
      },
      attached: [],
    };
  }
  return {
    draft: {
      mode: "cards",
      name: record.name,
      useWhen: record.use_when ?? "",
      hint: record.hint ?? "",
      cards: messagesToCards(record.data.messages),
      yaml: "",
      baseVersion: record.version,
    },
    attached: [...record.namespaces],
  };
}

/** The name and messages of YAML a user wrote, if it can be edited as cards. */
function decompositionOf(
  text: string,
): { name: string; messages: ChatMessage[] } | string {
  let value: unknown;
  try {
    value = parseYaml(text);
  } catch (error) {
    if (error instanceof YAMLParseError) return YAML_SYNTAX(error.message);
    throw error;
  }
  const data = value as { name?: unknown; messages?: unknown } | null;
  const messages = data?.messages;
  const valid =
    typeof data?.name === "string" &&
    Array.isArray(messages) &&
    messages.every(
      (m) => typeof m?.role === "string" && typeof m?.content === "string",
    );
  return valid
    ? { name: data.name as string, messages: messages as ChatMessage[] }
    : YAML_NOT_DECOMPOSITION;
}

/** Namespaces offered the decomposition by an attached ancestor: "also used in … (inherited)". */
function inheritedNotes(
  names: readonly string[],
  attached: readonly string[],
): Record<string, string> {
  const notes: Record<string, string> = {};
  for (const name of names) {
    if (
      !attached.includes(name) &&
      ancestors(name).some((a) => attached.includes(a))
    ) {
      notes[name] = LABELS.alsoUsedIn(name);
    }
  }
  return notes;
}

function preselected(
  params: FrameParams,
  health: Health,
  names: readonly string[],
): string | null {
  if (params.namespace && names.includes(params.namespace))
    return params.namespace;
  if (names.includes(health.default_namespace)) return health.default_namespace;
  return names[0] ?? null;
}

export function DecompositionEditor(props: DecompositionEditorProps) {
  const { record, draftKey, onBackendLost } = props;
  const names = props.namespaces.map((n) => n.name);
  const [stored, setStored] = useState<Stored>(
    () => loadDraft<Stored>(draftKey) ?? fresh(record),
  );
  const [hasDraft, setHasDraft] = useState(
    () => loadDraft<Stored>(draftKey) !== null,
  );
  const [preselection] = useState(() =>
    preselected(props.params, props.health, names),
  );
  const picked =
    stored.picked !== undefined && names.includes(stored.picked)
      ? stored.picked
      : preselection;
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [outcome, setOutcome] = useState<Outcome | null>(null);
  const [yamlView, setYamlView] = useState<string | null>(null);
  const [yamlError, setYamlError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const nameField = useRef<HTMLInputElement>(null);
  const yamlField = useRef<HTMLDivElement>(null);
  const { draft } = stored;
  const text = draftYaml(draft);

  useEffect(() => {
    let current = true;
    const timer = setTimeout(async () => {
      const result = await attempt(
        () => validate({ kind: "decomposition", yaml: text }),
        onBackendLost,
      );
      if (current && result.ok) setValidation(result.value);
    }, VALIDATE_AFTER_MS);
    return () => {
      current = false;
      clearTimeout(timer);
    };
  }, [text]);

  function keep(next: Stored) {
    setStored(next);
    saveDraft(draftKey, next);
    setHasDraft(true);
    setOutcome(null);
  }

  const change = (fields: Partial<DecompositionDraft>) =>
    keep({ ...stored, draft: { ...draft, ...fields } });

  function restart(next: Stored) {
    clearDraft(draftKey);
    setHasDraft(false);
    setStored(next);
    setYamlView(null);
    setYamlError(null);
  }

  async function send(
    slug: string,
    body: DecompositionBody,
    namespace: string | null,
  ) {
    setBusy(true);
    const result = await attempt(
      () => putDecomposition(slug, body),
      onBackendLost,
    );
    setBusy(false);
    if (result.ok) {
      const saved = result.value.record;
      const line = record
        ? SAVED_EDIT(saved.name, saved.version)
        : props.params.started
          ? SAVED_STARTED(saved.name, saved.version, namespace ?? "")
          : SAVED(saved.name, saved.version, namespace ?? "", saved.slug);
      restart(fresh(record ? saved : null));
      setOutcome({ kind: "saved", line, slug: saved.slug });
      props.onSaved(saved, result.value.created);
      return;
    }
    const error = result.error;
    if (error === null) return;
    const head = error.head as DecompositionRecord | null;
    if (error.code === "conflict" && head) {
      setOutcome(
        record
          ? { kind: "stale", message: error.message, head }
          : { kind: "exists", head },
      );
    } else {
      setOutcome(failed(error));
    }
  }

  async function save(confirmed: boolean) {
    if (draft.mode === "cards" && draft.name.trim() === "")
      return setOutcome({ kind: "name-required" });
    setBusy(true);
    const result = await attempt(
      () => validate({ kind: "decomposition", yaml: text }),
      onBackendLost,
    );
    setBusy(false);
    if (!result.ok) {
      if (result.error) setOutcome(failed(result.error));
      return;
    }
    const checked = result.value;
    setValidation(checked);
    if (!checked.ok) {
      return setOutcome({
        kind: "failed",
        message: checked.message ?? "",
        errors: checked.errors,
      });
    }
    if (checked.warnings.length > 0 && !confirmed) {
      return setOutcome({ kind: "warnings", warnings: checked.warnings });
    }
    if (record)
      return send(record.slug, updateBody(draft, stored.attached), null);
    if (picked !== null && checked.slug)
      return send(checked.slug, createBody(draft, picked), picked);
  }

  async function remove() {
    if (!record) return;
    const result = await attempt(
      () => deleteDecomposition(record.slug, draft.baseVersion),
      onBackendLost,
    );
    if (result.ok) {
      clearDraft(draftKey);
      props.onDeleted?.();
    } else if (result.error) {
      setOutcome(failed(result.error));
    }
  }

  async function viewYaml() {
    if (yamlView !== null) return setYamlView(null);
    const result = await attempt(
      () => validate({ kind: "decomposition", yaml: text }),
      onBackendLost,
    );
    const canonical = result.ok ? result.value.yaml : null;
    setYamlView(
      canonical ??
        stringifyYaml({
          name: draft.name,
          messages: cardsToMessages(draft.cards),
        }),
    );
  }

  function editAsCards() {
    const parsed = decompositionOf(draft.yaml);
    if (typeof parsed === "string") return setYamlError(parsed);
    setYamlError(null);
    change({
      mode: "cards",
      name: parsed.name,
      cards: messagesToCards(parsed.messages),
    });
  }

  const errors =
    outcome?.kind === "failed" ? outcome.errors : (validation?.errors ?? []);
  const cardErrors = draft.cards.map((_, i) =>
    errors.filter((e) => cardIndexForLoc(e.loc) === i),
  );
  const nameErrors =
    outcome?.kind === "name-required"
      ? [{ loc: "name", msg: NAME_REQUIRED }]
      : draft.mode === "cards" && draft.name !== ""
        ? errors.filter((e) => e.loc === "name")
        : [];
  const placed = (e: FieldError) =>
    draft.mode === "cards" &&
    (cardIndexForLoc(e.loc) !== null || e.loc === "name");
  const others = errors.filter((e) => !placed(e));
  const slug = record?.slug ?? validation?.slug ?? null;

  return (
    <form class="editor" onSubmit={(event) => event.preventDefault()}>
      {draft.mode === "cards" && (
        <div class="field">
          <label for="dr-name">{LABELS.name}</label>
          <div class="name-row">
            <input
              id="dr-name"
              ref={nameField}
              value={draft.name}
              readOnly={record !== null}
              data-testid="dr-name"
              aria-describedby={
                nameErrors.length ? "dr-name-errors" : undefined
              }
              onInput={(event) => change({ name: event.currentTarget.value })}
            />
            <span class="slash" data-testid="dr-slash">
              {slug ? `/${slug}` : ""}
            </span>
          </div>
          <FieldErrors
            id="dr-name-errors"
            testId="dr-name-errors"
            errors={nameErrors}
          />
        </div>
      )}
      <div class="field">
        <label for="dr-use-when">{LABELS.useWhen}</label>
        <input
          id="dr-use-when"
          value={draft.useWhen}
          data-testid="dr-use-when"
          onInput={(event) => change({ useWhen: event.currentTarget.value })}
        />
      </div>
      <div class="field">
        <label for="dr-hint">
          {LABELS.hint} <span class="note">({LABELS.hintNote})</span>
        </label>
        <input
          id="dr-hint"
          value={draft.hint}
          data-testid="dr-hint"
          onInput={(event) => change({ hint: event.currentTarget.value })}
        />
      </div>
      {record ? (
        <NamespaceChecklist
          label={LABELS.attachedTo}
          namespaces={names}
          checked={stored.attached}
          inherited={inheritedNotes(names, stored.attached)}
          testIdPrefix="dr-attached"
          onChange={(attached) => keep({ ...stored, attached })}
        />
      ) : (
        <NamespacePicker
          namespaces={names}
          value={picked}
          onChange={(name) => keep({ ...stored, picked: name })}
        />
      )}
      {(outcome?.kind === "failed" || others.length > 0) && (
        <div class="banner error" role="alert" data-testid="dr-errors">
          {outcome?.kind === "failed" ? (
            <p class="message">{outcome.message}</p>
          ) : (
            <FieldErrors errors={others} located />
          )}
        </div>
      )}
      {draft.mode === "cards" ? (
        <CardList
          cards={draft.cards}
          errors={cardErrors}
          onChange={(cards) => change({ cards })}
        />
      ) : (
        <YamlField
          containerRef={yamlField}
          value={draft.yaml}
          error={yamlError}
          onChange={(yaml) => {
            setYamlError(null);
            change({ yaml });
          }}
          onEditCards={editAsCards}
        />
      )}
      {draft.mode === "cards" && yamlView !== null && (
        <div class="yaml-view">
          <CodeField
            label="YAML"
            language="yaml"
            value={yamlView}
            onChange={() => undefined}
            readOnly
            testId="dr-yaml"
          />
          <button
            type="button"
            data-testid="dr-edit-yaml"
            onClick={() => {
              change({ mode: "yaml", yaml: yamlView });
              setYamlView(null);
            }}
          >
            {LABELS.editYaml}
          </button>
        </div>
      )}
      <div class="actions">
        {draft.mode === "cards" && (
          <button
            type="button"
            data-testid="dr-add-turn"
            onClick={() => change({ cards: addTurn(draft.cards) })}
          >
            {LABELS.addTurn}
          </button>
        )}
        {draft.mode === "cards" && (
          <button
            type="button"
            data-testid="dr-view-yaml"
            aria-expanded={yamlView !== null}
            onClick={viewYaml}
          >
            {LABELS.viewYaml}
          </button>
        )}
        <button
          type="button"
          class="primary"
          data-testid="dr-save"
          disabled={busy}
          onClick={() => save(false)}
        >
          {record ? LABELS.save : LABELS.saveTo(picked ?? "")}
        </button>
        {record && (
          <button
            type="button"
            class="danger"
            data-testid="dr-delete"
            onClick={() => setOutcome({ kind: "confirm-delete" })}
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
              setOutcome(null);
            }}
          >
            {DISCARD_DRAFT}
          </button>
        )}
      </div>
      <OutcomeView
        outcome={outcome}
        record={record}
        draft={draft}
        picked={picked}
        onSaveAnyway={() => save(true)}
        onCancel={() => setOutcome(null)}
        onSaveAsNext={(head) =>
          picked !== null &&
          send(head.slug, saveAsNextBody(draft, head, picked), picked)
        }
        onRename={() => {
          setOutcome(null);
          // In YAML mode the name is the YAML's own (§2.3).
          if (draft.mode === "cards") nameField.current?.focus();
          else yamlField.current?.querySelector("textarea")?.focus();
        }}
        onReload={(head) => {
          restart(fresh(head));
          setOutcome(null);
        }}
        onSaveOver={(head) =>
          record &&
          send(
            record.slug,
            updateBody(
              { ...draft, baseVersion: head.version },
              stored.attached,
            ),
            null,
          )
        }
        onDelete={remove}
        onShow={(slugToShow) => props.navigateTab("browse", slugToShow)}
      />
    </form>
  );
}

function OutcomeView(props: {
  outcome: Outcome | null;
  record: DecompositionRecord | null;
  draft: DecompositionDraft;
  picked: string | null;
  onSaveAnyway: () => void;
  onCancel: () => void;
  onSaveAsNext: (head: DecompositionRecord) => void;
  onRename: () => void;
  onReload: (head: DecompositionRecord) => void;
  onSaveOver: (head: DecompositionRecord) => void;
  onDelete: () => void;
  onShow: (slug: string) => void;
}) {
  const { outcome } = props;
  return (
    <>
      <p
        class="result"
        role="status"
        aria-live="polite"
        data-testid="dr-result"
      >
        {outcome?.kind === "saved" ? outcome.line : ""}
      </p>
      {outcome?.kind === "saved" && props.record === null && (
        <button
          type="button"
          data-testid="dr-show-in-decompositions"
          onClick={() => props.onShow(outcome.slug)}
        >
          {SHOW_IN_DECOMPOSITIONS}
        </button>
      )}
      {outcome?.kind === "warnings" && (
        <div class="banner warning" role="alert" data-testid="dr-warnings">
          {outcome.warnings.map((warning) => (
            <p>{warning}</p>
          ))}
          <button
            type="button"
            data-testid="dr-save-anyway"
            onClick={props.onSaveAnyway}
          >
            {SAVE_ANYWAY}
          </button>
          <button
            type="button"
            data-testid="dr-cancel-save"
            onClick={props.onCancel}
          >
            {CANCEL}
          </button>
        </div>
      )}
      {outcome?.kind === "exists" && (
        <div class="banner warning" role="alert" data-testid="dr-conflict">
          <p>
            {EXISTS(
              outcome.head.name,
              outcome.head.version,
              outcome.head.namespaces,
            )}
          </p>
          <button
            type="button"
            data-testid="dr-save-as-next"
            onClick={() => props.onSaveAsNext(outcome.head)}
          >
            {SAVE_AS_NEXT(outcome.head.version + 1)}
          </button>
          <button
            type="button"
            data-testid="dr-rename"
            onClick={props.onRename}
          >
            {RENAME}
          </button>
        </div>
      )}
      {outcome?.kind === "stale" && (
        <div class="banner warning" role="alert" data-testid="dr-conflict">
          <p>{outcome.message}</p>
          <button
            type="button"
            data-testid="dr-reload-entry"
            onClick={() => props.onReload(outcome.head)}
          >
            {RELOAD_ENTRY}
          </button>
          <button
            type="button"
            data-testid="dr-save-over"
            onClick={() => props.onSaveOver(outcome.head)}
          >
            {SAVE_OVER}
          </button>
        </div>
      )}
      {outcome?.kind === "confirm-delete" && props.record && (
        <ConfirmRow
          sentence={DELETE_CONFIRM(props.record.name)}
          confirm={LABELS.delete}
          onConfirm={props.onDelete}
          onCancel={props.onCancel}
        />
      )}
    </>
  );
}

function YamlField(props: {
  value: string;
  error: string | null;
  onChange: (value: string) => void;
  onEditCards: () => void;
  containerRef: Ref<HTMLDivElement>;
}) {
  return (
    <div class="yaml-edit" ref={props.containerRef}>
      <CodeField
        label="YAML"
        language="yaml"
        value={props.value}
        onChange={props.onChange}
        testId="dr-yaml"
        describedBy={props.error ? "dr-yaml-error" : undefined}
      />
      {props.error && (
        <p
          class="errors"
          id="dr-yaml-error"
          role="alert"
          data-testid="dr-yaml-error"
        >
          {props.error}
        </p>
      )}
      <button
        type="button"
        data-testid="dr-edit-cards"
        onClick={props.onEditCards}
      >
        {LABELS.editCards}
      </button>
    </div>
  );
}

export interface CardListProps {
  cards: readonly Card[];
  /** D2's errors for each card, by index. */
  errors: readonly (readonly FieldError[])[];
  onChange: (cards: Card[]) => void;
}

/** The cards as an ordered list of groups (§5.1): each turn, a step or an output with the step
 * after it, is numbered once and has one ✕; the task and raw cards stand alone. */
export function CardList(props: CardListProps) {
  const numbers = turnNumbers(props.cards);
  const set = (index: number, card: Card) =>
    props.onChange(props.cards.map((c, i) => (i === index ? card : c)));
  return (
    <ol class="cards">
      {cardGroups(props.cards).map((group) => {
        const first = group[0]!;
        const turn = numbers[first] ?? null;
        return (
          <li
            class="card-group"
            data-testid={turn === null ? undefined : `dr-turn-${turn}`}
          >
            <span class="turn">{turn}</span>
            <div>
              {group.map((i) => (
                <CardFields
                  card={props.cards[i]!}
                  index={i}
                  errors={props.errors[i]}
                  onChange={(card) => set(i, card)}
                />
              ))}
            </div>
            {turn !== null && (
              <button
                type="button"
                class="remove"
                aria-label={LABELS.removeTurn(turn)}
                data-testid={`dr-remove-${first}`}
                onClick={() => props.onChange(removeTurn(props.cards, first))}
              >
                {LABELS.remove}
              </button>
            )}
          </li>
        );
      })}
    </ol>
  );
}

function CardFields(props: {
  card: Card;
  index: number;
  errors?: readonly FieldError[];
  onChange: (card: Card) => void;
}) {
  const { card, index } = props;
  const errorsId = `dr-card-${index}-errors`;
  const describedBy = props.errors?.length ? errorsId : undefined;
  const field = (name: string) => `dr-card-${index}-${name}`;
  return (
    <div class={`card ${card.kind}`} data-testid={`dr-card-${index}`}>
      {card.kind === "task" && (
        <CodeField
          label={LABELS.task}
          language="text"
          value={card.text}
          testId={field("task")}
          describedBy={describedBy}
          onChange={(text) => props.onChange({ ...card, text })}
        />
      )}
      {card.kind === "step" && (
        <>
          <CodeField
            label={LABELS.think}
            language="text"
            value={card.think}
            testId={field("think")}
            describedBy={describedBy}
            onChange={(think) =>
              props.onChange({
                ...card,
                think,
                thinkLayout: think.includes("\n") ? "block" : card.thinkLayout,
              })
            }
          />
          <CodeField
            label={LABELS.code}
            language="python"
            value={card.code}
            testId={field("code")}
            describedBy={describedBy}
            onChange={(code) => props.onChange({ ...card, code })}
          />
        </>
      )}
      {card.kind === "output" && (
        <CodeField
          label={LABELS.output}
          language="text"
          value={card.text}
          testId={field("output")}
          describedBy={describedBy}
          onChange={(text) => props.onChange({ ...card, text })}
        />
      )}
      {card.kind === "raw" && (
        <RawCardFields
          card={card}
          index={index}
          describedBy={describedBy}
          onChange={props.onChange}
        />
      )}
      <FieldErrors id={errorsId} testId={errorsId} errors={props.errors} />
    </div>
  );
}

function RawCardFields(props: {
  card: RawCard;
  index: number;
  describedBy?: string;
  onChange: (card: RawCard) => void;
}) {
  const { card } = props;
  const roles = ROLES.includes(card.role) ? ROLES : [...ROLES, card.role];
  return (
    <>
      <p class="note">{RAW_NOTE}</p>
      <label class="role">
        role{" "}
        <select
          value={card.role}
          data-testid={`dr-card-${props.index}-role`}
          onChange={(event) =>
            props.onChange({
              ...card,
              role: event.currentTarget.value as RawCard["role"],
            })
          }
        >
          {roles.map((role) => (
            <option value={role}>{role}</option>
          ))}
        </select>
      </label>
      <CodeField
        label={card.role}
        language="text"
        value={card.content}
        testId={`dr-card-${props.index}-raw`}
        describedBy={props.describedBy}
        onChange={(content) => props.onChange({ ...card, content })}
      />
    </>
  );
}
