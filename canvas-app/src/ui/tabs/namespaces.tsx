// Namespaces (§2.4): the tree, each field's effective value and source, and the run settings.
// Every action changes one key of the namespace's (or the profile's) own YAML document and
// saves it at once, with the version it was read at (§5.3).

import { useRef, useState } from "preact/hooks";

import {
  deleteNamespace,
  getDecompositions,
  getNamespaceEffective,
  getNamespaces,
  getProfile,
  getTools,
  putNamespace,
  putProfile,
} from "../api";
import { Banner, ConfirmRow, ValueEditor } from "../components/fields";
import { NamespaceChecklist } from "../components/pickers";
import {
  ANY_NAMESPACE,
  ATTACHED_HERE,
  CANCEL,
  DEFAULT_BADGE,
  DELETE_NAMESPACE_CONFIRM,
  FROM_PROFILE,
  GRANTED_HERE,
  INHERITED,
  LABELS,
  MAKE_DEFAULT,
  NOT_SET,
  OVERRIDDEN,
  SET_HERE,
  UNDEFINED_TOOL,
} from "../texts";
import { type NamespaceNode, namespaceTree } from "../tree";
import type {
  DecompositionRecord,
  Effective,
  NamespaceRecord,
  ProfileRecord,
  ToolRecord,
} from "../types";
import { type Attempt, attempt, resolved, useLoaded } from "../load";
import { stringifyYaml } from "../yaml";
import type { TabProps } from "./props";

const RUN_SETTINGS = "run-settings";
const ROOT = "root";
const SETTINGS = [
  "model",
  "models",
  "reasoner",
  "system_prompt",
  "max_iter",
  "max_depth",
  "repl",
];
const TEXT_SETTINGS = new Set(["model", "system_prompt"]);

type Document = Record<string, unknown>;

interface Library {
  namespaces: NamespaceRecord[];
  profile: ProfileRecord;
  tools: ToolRecord[];
  decompositions: DecompositionRecord[];
}

async function loadLibrary(): Promise<Library> {
  const [namespaces, profile, tools, decompositions] = await Promise.all([
    getNamespaces(),
    getProfile(),
    getTools(),
    getDecompositions(),
  ]);
  return { namespaces, profile, tools, decompositions };
}

function without(document: Document, key: string): Document {
  const { [key]: _, ...rest } = document;
  return rest;
}

/** One line of YAML for a value; multi-line values keep their lines. */
function shown(value: unknown): string {
  return stringifyYaml(value).trimEnd();
}

function sourceOf(source: string | null, here: string): string {
  if (source === null) return NOT_SET;
  if (source === "profile") return FROM_PROFILE;
  if (source === here) return here === ROOT ? SET_HERE : OVERRIDDEN;
  return INHERITED(source);
}

export function NamespacesTab(props: TabProps) {
  const library = useLoaded(loadLibrary, [props.rev], props.onBackendLost);
  const [selected, setSelected] = useState<string | null>(
    props.params.focus ?? props.params.namespace,
  );
  const [message, setMessage] = useState<string | null>(null);
  const [adding, setAdding] = useState<string | null>(null);
  const selections = useRef(0);
  const data = library.data;
  if (!data)
    return library.error ? (
      <Banner kind="error">{library.error.message}</Banner>
    ) : null;
  const names = data.namespaces.map((n) => n.name);
  const defaultNamespace = data.profile.default_namespace;
  const current =
    selected === RUN_SETTINGS || (selected !== null && names.includes(selected))
      ? selected
      : names.includes(defaultNamespace)
        ? defaultNamespace
        : ROOT;

  const select = (name: string) => {
    selections.current += 1;
    setSelected(name);
    setMessage(null);
    setAdding(null);
  };

  /** A select for when a write is answered: dropped if another node was selected meanwhile. */
  const selectOnAnswer = () => {
    const since = selections.current;
    return (name: string) => {
      if (selections.current === since) select(name);
    };
  };

  /** A write, then the Library again; D2's refusal is shown as it comes. */
  async function write<T>(run: () => Promise<T>): Promise<Attempt<T>> {
    const result = await attempt(run, props.onBackendLost);
    if (result.ok) setMessage(null);
    else if (result.error) setMessage(result.error.message);
    library.reload();
    return result;
  }

  async function addNamespace(name: string) {
    const selectAdded = selectOnAnswer();
    const result = await write(() =>
      putNamespace(name, { yaml: JSON.stringify({ name }), base_version: 0 }),
    );
    if (result.ok) selectAdded(name);
  }

  const startAdding = () =>
    setAdding(
      current === RUN_SETTINGS || current === ROOT ? "" : `${current}.`,
    );

  return (
    <section class="namespaces">
      <nav class="tree" aria-label={LABELS.namespace}>
        <button
          type="button"
          class="node"
          aria-current={current === RUN_SETTINGS}
          data-testid="dr-node-run-settings"
          onClick={() => select(RUN_SETTINGS)}
        >
          {LABELS.runSettings}
        </button>
        <ul>
          <TreeNode
            node={namespaceTree(names)}
            current={current}
            defaultNamespace={defaultNamespace}
            onSelect={select}
          />
        </ul>
        {adding === null ? (
          <button
            type="button"
            data-testid="dr-add-namespace"
            onClick={startAdding}
          >
            + {LABELS.addNamespace}
          </button>
        ) : (
          <div class="add">
            <label for="dr-new-namespace">{LABELS.name}</label>
            <input
              id="dr-new-namespace"
              value={adding}
              data-testid="dr-new-namespace"
              onInput={(event) => setAdding(event.currentTarget.value)}
            />
            <button
              type="button"
              class="primary"
              data-testid="dr-create-namespace"
              onClick={() => addNamespace(adding)}
            >
              {LABELS.addNamespace}
            </button>
            <button type="button" onClick={() => setAdding(null)}>
              {CANCEL}
            </button>
          </div>
        )}
      </nav>
      <div class="detail">
        {message !== null && (
          <Banner kind="error" testId="dr-message">
            {message}
          </Banner>
        )}
        {current === RUN_SETTINGS ? (
          <RunSettings
            key="run-settings"
            profile={data.profile}
            write={write}
          />
        ) : (
          <NamespaceDetail
            key={current}
            name={current}
            library={data}
            rev={props.rev}
            write={write}
            onBackendLost={props.onBackendLost}
            onDeleted={selectOnAnswer()}
          />
        )}
      </div>
    </section>
  );
}

function TreeNode(props: {
  node: NamespaceNode;
  current: string;
  defaultNamespace: string;
  onSelect: (name: string) => void;
}) {
  const { node } = props;
  return (
    <li data-testid={`dr-tree-${node.name}`}>
      <button
        type="button"
        class="node"
        aria-current={props.current === node.name}
        data-testid={`dr-node-${node.name}`}
        onClick={() => props.onSelect(node.name)}
      >
        {node.name}
        {node.name === props.defaultNamespace && (
          <span title={DEFAULT_BADGE}> ★</span>
        )}
      </button>
      {node.children.length > 0 && (
        <ul>
          {node.children.map((child) => (
            <TreeNode {...props} node={child} />
          ))}
        </ul>
      )}
    </li>
  );
}

type Write = <T>(run: () => Promise<T>) => Promise<Attempt<T>>;

function NamespaceDetail(props: {
  name: string;
  library: Library;
  rev: number;
  write: Write;
  onBackendLost: TabProps["onBackendLost"];
  onDeleted: (parent: string) => void;
}) {
  const { name, library } = props;
  const effective = useLoaded(
    () => resolved(() => getNamespaceEffective(name)),
    [name, props.rev],
    props.onBackendLost,
  );
  const [editing, setEditing] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);
  const namespace = library.namespaces.find((n) => n.name === name)!;
  const document = namespace.data;
  const isDefault = library.profile.default_namespace === name;

  async function save(next: Document) {
    const result = await props.write(() =>
      putNamespace(name, {
        yaml: stringifyYaml(next),
        base_version: namespace.version,
      }),
    );
    if (result.ok) setEditing(null);
    effective.reload();
  }

  const set = (key: string, value: unknown) =>
    save({ ...document, [key]: value });
  const reset = (key: string) => save(without(document, key));

  async function attach(decompositions: string[]) {
    await props.write(() =>
      putNamespace(name, {
        yaml: namespace.yaml,
        decompositions,
        base_version: namespace.version,
      }),
    );
    setEditing(null);
    effective.reload();
  }

  async function makeDefault() {
    const profile = {
      ...library.profile.data,
      entry_namespace: name,
    };
    await props.write(() =>
      putProfile({
        yaml: stringifyYaml(profile),
        base_version: library.profile.version,
      }),
    );
  }

  async function remove() {
    setConfirming(false);
    const result = await props.write(() =>
      deleteNamespace(name, namespace.version),
    );
    if (result.ok)
      props.onDeleted(
        name.includes(".") ? name.slice(0, name.lastIndexOf(".")) : ROOT,
      );
  }

  const fieldProps = { here: name, document, editing, setEditing, set, reset };
  const view = effective.data?.value;
  const failure = effective.data?.failure;
  return (
    <div class="namespace">
      <h2 data-testid="dr-namespace-title">{name}</h2>
      {isDefault ? (
        <p class="badge" data-testid="dr-default-badge">
          ★ {DEFAULT_BADGE}
        </p>
      ) : (
        <button
          type="button"
          data-testid="dr-make-default"
          onClick={makeDefault}
        >
          {MAKE_DEFAULT}
        </button>
      )}
      {failure && (
        <Banner kind="error" testId="dr-effective-failed">
          {failure}
        </Banner>
      )}
      {effective.error && (
        <Banner kind="error">{effective.error.message}</Banner>
      )}
      {view && (
        <dl class="fields">
          <ValueField
            {...fieldProps}
            field="repl"
            label="REPL"
            sourced={view.repl}
          />
          <ValueField
            {...fieldProps}
            field="reasoner"
            label="Backbone"
            sourced={view.reasoner}
          />
          <SpawnField
            {...fieldProps}
            sourced={view.spawn}
            namespaces={library.namespaces.map((n) => n.name)}
          />
          <ToolsField {...fieldProps} view={view} library={library} />
          <VarsField {...fieldProps} view={view} />
          <SuffixField {...fieldProps} view={view} />
          <DecompositionsField
            view={view}
            namespace={namespace}
            library={library}
            editing={editing}
            setEditing={setEditing}
            attach={attach}
          />
        </dl>
      )}
      <button
        type="button"
        class="danger"
        data-testid="dr-delete-namespace"
        onClick={() => setConfirming(true)}
      >
        {LABELS.deleteNamespace}
      </button>
      {confirming && (
        <ConfirmRow
          sentence={DELETE_NAMESPACE_CONFIRM(name)}
          confirm={LABELS.deleteNamespace}
          onConfirm={remove}
          onCancel={() => setConfirming(false)}
        />
      )}
    </div>
  );
}

interface FieldProps {
  here: string;
  document: Document;
  editing: string | null;
  setEditing: (editor: string | null) => void;
  set: (key: string, value: unknown) => void;
  reset: (key: string) => void;
}

/** Override when the value comes from elsewhere; Edit and Reset when it is set here. */
function Actions(props: {
  id: string;
  setHere: boolean;
  onEdit: () => void;
  onReset: () => void;
}) {
  if (!props.setHere) {
    return (
      <button
        type="button"
        data-testid={`dr-override-${props.id}`}
        onClick={props.onEdit}
      >
        {LABELS.override}
      </button>
    );
  }
  return (
    <>
      <button
        type="button"
        data-testid={`dr-edit-${props.id}`}
        onClick={props.onEdit}
      >
        {LABELS.edit}
      </button>
      <button
        type="button"
        data-testid={`dr-reset-${props.id}`}
        onClick={props.onReset}
      >
        {LABELS.reset}
      </button>
    </>
  );
}

function ValueField(
  props: FieldProps & {
    field: string;
    label: string;
    sourced: { value: unknown; source: string | null };
  },
) {
  const { field, sourced } = props;
  return (
    <div class="field-row" data-testid={`dr-field-${field}`}>
      <dt>{props.label}</dt>
      <dd>
        <pre class="value">
          {sourced.source === null ? "—" : shown(sourced.value)}
        </pre>
        <span class="source" data-testid={`dr-source-${field}`}>
          {sourceOf(sourced.source, props.here)}
        </span>
        <Actions
          id={field}
          setHere={field in props.document}
          onEdit={() => props.setEditing(field)}
          onReset={() => props.reset(field)}
        />
        {props.editing === field && (
          <ValueEditor
            label={props.label}
            value={sourced.value}
            mode="yaml"
            testId={`dr-value-${field}`}
            onSave={(value) => props.set(field, value)}
            onCancel={() => props.setEditing(null)}
          />
        )}
      </dd>
    </div>
  );
}

function SpawnField(
  props: FieldProps & {
    sourced: { value: unknown; source: string | null };
    namespaces: string[];
  },
) {
  const targets = Array.isArray(props.sourced.value)
    ? (props.sourced.value as string[])
    : null;
  const [checked, setChecked] = useState<string[]>(targets ?? []);
  return (
    <div class="field-row" data-testid="dr-field-spawn">
      <dt>May spawn into</dt>
      <dd>
        <span class="value">
          {targets === null ? ANY_NAMESPACE : targets.join(", ") || "—"}
        </span>
        <span class="source" data-testid="dr-source-spawn">
          {sourceOf(props.sourced.source, props.here)}
        </span>
        <Actions
          id="spawn"
          setHere={"spawn" in props.document}
          onEdit={() => {
            setChecked(targets ?? []);
            props.setEditing("spawn");
          }}
          onReset={() => props.reset("spawn")}
        />
        {props.editing === "spawn" && (
          <div class="value-editor">
            <NamespaceChecklist
              label="May spawn into"
              namespaces={props.namespaces}
              checked={checked}
              testIdPrefix="dr-spawn"
              onChange={setChecked}
            />
            <button
              type="button"
              class="primary"
              data-testid="dr-value-save"
              onClick={() => props.set("spawn", checked)}
            >
              {LABELS.save}
            </button>
            <button
              type="button"
              data-testid="dr-value-cancel"
              onClick={() => props.setEditing(null)}
            >
              {CANCEL}
            </button>
          </div>
        )}
      </dd>
    </div>
  );
}

function ToolsField(props: FieldProps & { view: Effective; library: Library }) {
  const own = Array.isArray(props.document.tools)
    ? (props.document.tools as string[])
    : [];
  const offered = [
    ...props.library.tools.map((t) => t.name),
    ...(props.library.profile.data.model ? ["llm"] : []),
  ];
  const names = [
    ...new Set([...props.view.tools.map((t) => t.name), ...offered]),
  ];
  const grant = (tool: string, on: boolean) => {
    const next = on ? [...own, tool] : own.filter((t) => t !== tool);
    if (next.length) props.set("tools", next);
    else props.reset("tools");
  };
  return (
    <div class="field-row" data-testid="dr-field-tools">
      <dt>Tools</dt>
      <dd>
        <ul class="plain">
          {names.map((tool) => {
            const granted = props.view.tools.find((t) => t.name === tool);
            const inherited =
              granted !== undefined && granted.source !== props.here;
            return (
              <li>
                <label>
                  <input
                    type="checkbox"
                    checked={granted !== undefined}
                    disabled={inherited}
                    data-testid={`dr-grant-${tool}`}
                    onChange={(event) =>
                      grant(tool, event.currentTarget.checked)
                    }
                  />
                  {tool}
                </label>{" "}
                {granted && (
                  <span class="source" data-testid={`dr-tool-source-${tool}`}>
                    {inherited ? INHERITED(granted.source) : GRANTED_HERE}
                  </span>
                )}
                {granted && !granted.defined && (
                  <span class="warning"> {UNDEFINED_TOOL}</span>
                )}
              </li>
            );
          })}
        </ul>
      </dd>
    </div>
  );
}

function VarsField(props: FieldProps & { view: Effective }) {
  const [newName, setNewName] = useState("");
  const own = (props.document.vars ?? {}) as Document;
  const setVar = (key: string, value: unknown) =>
    props.set("vars", { ...own, [key]: value });
  const resetVar = (key: string) => {
    const rest = without(own, key);
    if (Object.keys(rest).length) props.set("vars", rest);
    else props.reset("vars");
  };
  return (
    <div class="field-row" data-testid="dr-field-vars">
      <dt>Variables</dt>
      <dd>
        <ul class="plain">
          {Object.entries(props.view.vars).map(([key, sourced]) => (
            <li data-testid={`dr-var-${key}`}>
              <code>{key}</code>{" "}
              <pre class="value inline">{shown(sourced.value)}</pre>{" "}
              <span class="source">{sourceOf(sourced.source, props.here)}</span>{" "}
              <Actions
                id={`var-${key}`}
                setHere={key in own}
                onEdit={() => props.setEditing(`var-${key}`)}
                onReset={() => resetVar(key)}
              />
              {props.editing === `var-${key}` && (
                <ValueEditor
                  label={key}
                  value={sourced.value}
                  mode="yaml"
                  testId={`dr-value-var-${key}`}
                  onSave={(value) => setVar(key, value)}
                  onCancel={() => props.setEditing(null)}
                />
              )}
            </li>
          ))}
        </ul>
        <button
          type="button"
          data-testid="dr-add-variable"
          onClick={() => props.setEditing("new-variable")}
        >
          + {LABELS.addVariable}
        </button>
        {props.editing === "new-variable" && (
          <div class="add">
            <label for="dr-new-variable">{LABELS.name}</label>
            <input
              id="dr-new-variable"
              value={newName}
              data-testid="dr-new-variable"
              onInput={(event) => setNewName(event.currentTarget.value)}
            />
            <ValueEditor
              label={newName}
              value={undefined}
              mode="yaml"
              testId="dr-value-new-variable"
              onSave={(value) => setVar(newName.trim(), value)}
              onCancel={() => props.setEditing(null)}
            />
          </div>
        )}
      </dd>
    </div>
  );
}

function SuffixField(props: FieldProps & { view: Effective }) {
  const own =
    typeof props.document.system_suffix === "string"
      ? props.document.system_suffix
      : null;
  return (
    <div class="field-row" data-testid="dr-field-system_suffix">
      <dt>System suffix</dt>
      <dd>
        <ul class="plain">
          {props.view.system_suffix.map((part) => (
            <li data-testid={`dr-suffix-${part.source}`}>
              <pre class="value">{part.text}</pre>{" "}
              <span class="source">{sourceOf(part.source, props.here)}</span>
            </li>
          ))}
        </ul>
        <Actions
          id="system_suffix"
          setHere={own !== null}
          onEdit={() => props.setEditing("system_suffix")}
          onReset={() => props.reset("system_suffix")}
        />
        {props.editing === "system_suffix" && (
          <ValueEditor
            label="System suffix"
            value={own ?? ""}
            mode="text"
            testId="dr-value-system_suffix"
            onSave={(text) =>
              text === ""
                ? props.reset("system_suffix")
                : props.set("system_suffix", text)
            }
            onCancel={() => props.setEditing(null)}
          />
        )}
      </dd>
    </div>
  );
}

function DecompositionsField(props: {
  view: Effective;
  namespace: NamespaceRecord;
  library: Library;
  editing: string | null;
  setEditing: (editor: string | null) => void;
  attach: (decompositions: string[]) => void;
}) {
  const attached = props.namespace.decompositions;
  const candidates = props.library.decompositions.filter(
    (d) => !attached.includes(d.name),
  );
  const [choice, setChoice] = useState<string>("");
  const here = props.namespace.name;
  return (
    <div class="field-row" data-testid="dr-field-decompositions">
      <dt>Decompositions</dt>
      <dd>
        <ul class="plain">
          {props.view.decompositions.map((d) => (
            <li data-testid={`dr-decomposition-${d.slug}`}>
              {d.name}{" "}
              <span class="source">
                {d.source === here ? ATTACHED_HERE : INHERITED(d.source)}
              </span>{" "}
              {d.source === here && (
                <button
                  type="button"
                  data-testid={`dr-detach-${d.slug}`}
                  onClick={() =>
                    props.attach(attached.filter((n) => n !== d.name))
                  }
                >
                  {LABELS.detach}
                </button>
              )}
            </li>
          ))}
        </ul>
        <button
          type="button"
          data-testid="dr-attach"
          onClick={() => {
            setChoice(candidates[0]?.name ?? "");
            props.setEditing("attach");
          }}
        >
          {LABELS.attach}
        </button>
        {props.editing === "attach" && (
          <div class="add">
            <select
              value={choice}
              aria-label={LABELS.attach}
              data-testid="dr-attach-choice"
              onChange={(event) => setChoice(event.currentTarget.value)}
            >
              {candidates.map((d) => (
                <option value={d.name}>{d.name}</option>
              ))}
            </select>
            <button
              type="button"
              class="primary"
              data-testid="dr-attach-confirm"
              disabled={choice === ""}
              onClick={() => props.attach([...attached, choice])}
            >
              {LABELS.attach.replace("…", "")}
            </button>
            <button type="button" onClick={() => props.setEditing(null)}>
              {CANCEL}
            </button>
          </div>
        )}
      </dd>
    </div>
  );
}

function RunSettings(props: { profile: ProfileRecord; write: Write }) {
  const [editing, setEditing] = useState<string | null>(null);
  const [newKey, setNewKey] = useState("");
  const document = props.profile.data;
  const keys = Object.keys(document).filter((key) => key !== "entry_namespace");
  const modeOf = (key: string) => (TEXT_SETTINGS.has(key) ? "text" : "yaml");

  async function save(next: Document) {
    const result = await props.write(() =>
      putProfile({
        yaml: stringifyYaml(next),
        base_version: props.profile.version,
      }),
    );
    if (result.ok) setEditing(null);
  }

  return (
    <div class="namespace">
      <h2 data-testid="dr-namespace-title">{LABELS.runSettings}</h2>
      <dl class="fields">
        {keys.map((key) => (
          <div class="field-row" data-testid={`dr-field-${key}`}>
            <dt>{key}</dt>
            <dd>
              <pre class="value">
                {modeOf(key) === "text"
                  ? String(document[key])
                  : shown(document[key])}
              </pre>
              <Actions
                id={key}
                setHere
                onEdit={() => setEditing(key)}
                onReset={() => save(without(document, key))}
              />
              {editing === key && (
                <ValueEditor
                  label={key}
                  value={document[key]}
                  mode={modeOf(key)}
                  testId={`dr-value-${key}`}
                  onSave={(value) => save({ ...document, [key]: value })}
                  onCancel={() => setEditing(null)}
                />
              )}
            </dd>
          </div>
        ))}
      </dl>
      <button
        type="button"
        data-testid="dr-add-setting"
        onClick={() => setEditing("new-setting")}
      >
        + {LABELS.addSetting}
      </button>
      {editing === "new-setting" && (
        <div class="add">
          <label for="dr-new-setting">{LABELS.name}</label>
          <input
            id="dr-new-setting"
            list="dr-settings"
            value={newKey}
            data-testid="dr-new-setting"
            onInput={(event) => setNewKey(event.currentTarget.value)}
          />
          <datalist id="dr-settings">
            {SETTINGS.map((setting) => (
              <option value={setting} />
            ))}
          </datalist>
          <ValueEditor
            key={modeOf(newKey.trim())}
            label={newKey}
            value={undefined}
            mode={modeOf(newKey.trim())}
            testId="dr-value-new-setting"
            onSave={(value) => save({ ...document, [newKey.trim()]: value })}
            onCancel={() => setEditing(null)}
          />
        </div>
      )}
    </div>
  );
}
