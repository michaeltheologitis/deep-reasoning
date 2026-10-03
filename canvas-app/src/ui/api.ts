// D2's HTTP API (D2 §6, as built), one function per endpoint, over relative URLs: from …/ui/,
// ../namespaces is the backend's /namespaces through the bridge, and on the standalone page.
// Bodies carry exactly D2's fields (D2 refuses others with 400) and are always JSON.

import type {
  DecompositionRecord,
  Effective,
  FieldError,
  Health,
  HistoryEntry,
  Kind,
  NamespaceRecord,
  Problem,
  ProfileRecord,
  ToolRecord,
  ValidationResult,
} from "./types";

export interface ValidateBody {
  kind: Kind;
  yaml: string;
  name?: string;
  source?: string;
}

export interface ProfileBody {
  yaml: string;
  decompositions?: string[];
  base_version: number;
}

export interface NamespaceBody {
  yaml: string;
  decompositions?: string[];
  base_version: number;
}

export interface DecompositionBody {
  yaml: string;
  use_when: string | null; // always sent: an absent one is erased
  hint: string | null; // always sent
  namespaces?: string[];
  base_version: number;
}

export interface ToolBody {
  yaml: string;
  source?: string | null;
  granted_in?: string[];
  base_version: number;
}

export interface Written<T> {
  record: T;
  created: boolean; // 201
}

/** D2's own refusal: {"error", "message", "errors"?, "head"?}. */
export class LibraryError extends Error {
  readonly status: number;
  readonly code: string; // D2's: invalid, conflict, refused, not_found, bad_request, forbidden, unsupported_media_type
  readonly errors: readonly FieldError[];
  readonly head: unknown; // conflict: the current record, or null

  constructor(
    status: number,
    body: {
      error: string;
      message: string;
      errors?: FieldError[];
      head?: unknown;
    },
  ) {
    super(body.message);
    this.status = status;
    this.code = body.error;
    this.errors = body.errors ?? [];
    this.head = body.head ?? null;
  }
}

/** Anything that is not D2 answering: the bridge's {"detail"}, a non-JSON 502, no answer at all. */
export class BackendUnavailable extends Error {
  readonly status: number; // 0: no answer; 401: session; 502, 503: the bridge

  constructor(status: number) {
    super(`The Library did not answer (${status}).`);
    this.status = status;
  }
}

type Method = "GET" | "POST" | "PUT" | "DELETE";

function isLibraryErrorBody(body: unknown): body is {
  error: string;
  message: string;
  errors?: FieldError[];
  head?: unknown;
} {
  const value = body as { error?: unknown; message?: unknown } | null;
  return typeof value?.error === "string" && typeof value.message === "string";
}

/** method path [body] → D2's JSON, or LibraryError, or BackendUnavailable. */
export async function call<T>(
  method: Method,
  path: string,
  body?: unknown,
): Promise<{ status: number; data: T }> {
  let response: Response;
  try {
    response = await fetch(path, {
      method,
      ...(body !== undefined && {
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }),
    });
  } catch {
    throw new BackendUnavailable(0);
  }
  let data: unknown;
  try {
    data = JSON.parse(await response.text());
  } catch {
    throw new BackendUnavailable(response.status);
  }
  if (response.ok) return { status: response.status, data: data as T };
  if (isLibraryErrorBody(data)) throw new LibraryError(response.status, data);
  throw new BackendUnavailable(response.status);
}

async function read<T>(path: string): Promise<T> {
  return (await call<T>("GET", path)).data;
}

async function write<T>(path: string, body: unknown): Promise<Written<T>> {
  const { status, data } = await call<T>("PUT", path, body);
  return { record: data, created: status === 201 };
}

async function remove(
  path: string,
  baseVersion: number,
): Promise<HistoryEntry> {
  return (
    await call<HistoryEntry>("DELETE", `${path}?base_version=${baseVersion}`)
  ).data;
}

const at = (collection: string, key: string) =>
  `../${collection}/${encodeURIComponent(key)}`;

export const getHealth = () => read<Health>("../health");
export const getProblems = () => read<Problem[]>("../problems");
export const validate = async (body: ValidateBody) =>
  (await call<ValidationResult>("POST", "../validate", body)).data;
export const getProfile = () => read<ProfileRecord>("../profile");
export const putProfile = async (body: ProfileBody) =>
  (await write<ProfileRecord>("../profile", body)).record;
export const getNamespaces = () => read<NamespaceRecord[]>("../namespaces");
export const getNamespace = (name: string) =>
  read<NamespaceRecord>(at("namespaces", name));
export const putNamespace = (name: string, body: NamespaceBody) =>
  write<NamespaceRecord>(at("namespaces", name), body);
export const deleteNamespace = (name: string, baseVersion: number) =>
  remove(at("namespaces", name), baseVersion);
export const getEffective = () => read<Effective[]>("../effective");
export const getNamespaceEffective = (name: string) =>
  read<Effective>(`${at("namespaces", name)}/effective`);
export const getDecompositions = () =>
  read<DecompositionRecord[]>("../decompositions");
export const getDecomposition = (slug: string) =>
  read<DecompositionRecord>(at("decompositions", slug));
export const putDecomposition = (slug: string, body: DecompositionBody) =>
  write<DecompositionRecord>(at("decompositions", slug), body);
export const deleteDecomposition = (slug: string, baseVersion: number) =>
  remove(at("decompositions", slug), baseVersion);
export const getTools = () => read<ToolRecord[]>("../tools");
export const getTool = (name: string) => read<ToolRecord>(at("tools", name));
export const putTool = (name: string, body: ToolBody) =>
  write<ToolRecord>(at("tools", name), body);
export const deleteTool = (name: string, baseVersion: number) =>
  remove(at("tools", name), baseVersion);
export const toolVersions = (name: string) =>
  read<HistoryEntry[]>(`${at("tools", name)}/versions`);
