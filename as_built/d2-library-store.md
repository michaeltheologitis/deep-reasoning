# D2 · Library store, as built

**TASK-5** · Cartographer · the code at `90044f0` (head of `v1-library-store`: D2's commits on D1's
code, merged with D1 `21f4a8b`, plus the `dr-acp` wiring; this file is on `as-built/d2`) · checked
against the design at `555472b` (`docs/design/d2-library-store.md`, unchanged at `90044f0`) ·
deep_reasoner_beta `d7334ae` · 2026-10-03.

D2's code is `src/deep_reasoning/library/` and `tests/library/`, plus 35 added and 32 removed lines
in D1's files (§5). D1's code is described only where D2 meets it: the `Catalog` seam (§4.6).

**Evidence marks.** Every claim carries one.
- **[run]**: executed in this sandbox at `90044f0`. That covers D2's suite plus D1's
  `tests/acp/test_cli.py` (`CI=true DR_BETA_CHECKOUT=<clone> uv run pytest tests/library
  tests/acp/test_cli.py`: 289 passed, 1 deselected, 262 s) and uncommitted probe scripts that call the
  public API, `dr-library` and `dr`. E7 and the probes read a clone of `/home/user/deep_reasoner_beta`
  at `d7334ae`; the original checkout's `git status` was empty before and after.
- **[CI]**: read from GitHub's logs of CI run 37085759535 and live run 37085761405, both at
  `90044f0`. I did not run a paid model or a real `claude` CLI.
- **[read]**: read in the code and **not executed**. This is weaker evidence than [run]; §7 lists
  the read claims that matter most.

**Reading order.** Start with §2 (the divergences). Then §1 and §3–§5 are the map, §6 gives the
experiments as measured, and §7 says what I could not verify.

---

## 1 · What exists

The Library is one SQLite file, `<home>/library.sqlite`, holding one profile and any number of
namespaces, decompositions and tools, each stored as canonical YAML in deep_reasoner's own shapes.
Every save appends immutable version rows under one library-wide revision number. Three kinds of
process open the file. Each opens a fresh connection per operation and shares nothing else:
- `dr-library serve` (the App backend's HTTP API);
- `dr-library import` and `dr-library export`;
- each `dr-acp`, in-process, through `LibraryCatalog`.

[read; each run end to end by the tests in §6]

```text
D3's panel ─HTTP─▶ dr-library serve: api.create_app ─┐
dr-library import | export: cli.main ────────────────┼─▶ Library (library.py) ─ store.write / store.read ─▶ library.sqlite (WAL, 0600)
dr-acp: LibraryCatalog (catalog.py) ─────────────────┘      ├ shapes.validate_*      deep_reasoner's models, canonical YAML
                                                            ├ configdir.read_config  a plain dr config ─▶ parts      (import)
                                                            ├ configdir.write_config state ─▶ main.yaml, namespaces/<ns>.yaml,
                                                            │                        tools/<t>.py, library.yaml   (materialize)
                                                            └ effective.effective    inherited values and their sources
```

| Part | Lines (non-blank) | Where |
|---|---|---|
| the package | 2,684 (2,239) of Python, plus the 24-line `starter.yaml` | `src/deep_reasoning/library/` |
| tests | 2,576 (2,203) | `tests/library/` |
| edits to D1's files | +35 −32 | `acp/cli.py`, `acp/session.py`, `acp/texts.py`, `tests/acp/harness.py`, `tests/acp/test_cli.py`, `pyproject.toml` |

The length sits in `library.py` (748 lines: the save semantics, §4.2) and `api.py` (379: the routes
and the request guards, §4.7). [read]

---

## 2 · Divergences from the design (`555472b`)

No changelog `drift:` line exists for TASK-5, so every divergence below was found from the code. Each
row gives what the design says, what is built, where, and the reason the code or its commit
message gives ("none recorded" when neither does).

### 2.1 Behaviour that D3, D4 or a user sees

| # | Design | Built | Where | Reason |
|---|---|---|---|---|
| 1 | The same-user peer check (Linux) is the API's only guard (§1.1 K, §4.8). §6.1's statuses are 200, 201, 400, 403, 404, 409 and 422. | Two more refusals come before any route, on every platform. A `Host` other than `127.0.0.1:<port>` or `localhost:<port>` gets 403 `forbidden` ("This library answers only requests addressed to …"). A `PUT` or `POST` without `Content-Type: application/json` gets **415** `unsupported_media_type`. [run: a real `dr-library serve` answered `Host: app.example:443` with 403; CI: `test_a_request_addressed_to_another_host_is_refused`, `test_a_body_that_is_not_sent_as_json_is_refused`] | `api.py:76-96`, `records.py:214-228`, `texts.py:20-21, 191-195` | DNS rebinding: a page that rebinds its name to 127.0.0.1 still sends its own `Host`. A cross-site form or `text/plain` POST needs no preflight (`api.py:89, 93`; commit `2ec10f4`). **Whether the agent-server's bridge and its health probe send an accepted `Host` is not verified (§7 item 1).** |
| 2 | A body that is not JSON or lacks `yaml` is 400 `bad_request`. | Bodies are pydantic models with `extra="forbid"`, so an unknown field is also 400. The message is `BAD_REQUEST` plus pydantic's first message. | `api.py:117-157` | none recorded |
| 3 | `main.yaml` always carries `entry_namespace: <namespace>` (§4.6). | It is written only when the namespace differs from the profile's default. For a profile that never set `entry_namespace` and a run in the default namespace, `main.yaml` has no `entry_namespace` and `dr`'s own default applies. [run] | `configdir.py:179-182` | "so a profile that never set it re-imports unchanged" (commit `8bea912`) |
| 4 | `Manifest.library` is the library file's absolute path (§4.4). | It is the path the Library was opened with, unresolved. D1's `Home.resolve` keeps a relative `--home` or `DR_HOME` relative, so a relative home gives a relative `library` in `library.yaml`, in `RunSource.versions` (the run log) and in the session index's `source`. [run: opening `rel/library.sqlite` gave `library: rel/library.sqlite`] | `configdir.py:164`, `library.py:276`; D1's `runlog.py:171-174` | none recorded |
| 5 | Out-of-range revisions and versions are not specified. | `state(rev=N)` outside `1..now` raises `LibraryNotFound` (404) with the new sentence `no_revision`, which `dr-library export --rev` reaches. A missing `GET …/versions/{n}` is 404 with the new sentence `no_version`. [CI: `test_a_revision_the_library_has_not_reached_is_not_found`] | `library.py:291-292`, `api.py:288-290`, `texts.py:104-109` | "instead of an empty unpacking" (commit `5e06d9e`) |
| 6 | Import writes namespaces "root first and parents before children" (§4.6). | Namespaces are written in the config's order: root, then `namespaces_dir`, then inline. A child listed before its parent is created first, and `namespaces()` lists it first. The invariants run at commit, so the import succeeds. [run: `{a.b, a}` imports as `['root', 'a.b', 'a']`] | `library.py:632-633` | none recorded |

### 2.2 Signatures and structure

| # | Design | Built | Where | Reason |
|---|---|---|---|---|
| 7 | `LIBRARY_FILE` and `library_path` are in `library.py` (§4.5). | They are in `catalog.py`; `library.py` imports them from there. | `catalog.py:15-22` | `dr-acp` finds its library before it serves, without importing deep_reasoner (commit `735abe4`) |
| 8 | `__init__.py` re-exports `Library` and the rest. | `Library` and `Effective` load lazily through a module `__getattr__`; the rest load eagerly. [CI: `test_building_a_catalog_imports_nothing_of_deep_reasoner`] | `__init__.py:32, 60-63` | Importing `…library.catalog` runs `__init__.py` first, and `library.py` imports deep_reasoner (`__init__.py:4-5`) |
| 9 | `Library.validate(kind, text, *, name=None)`. | It also takes `source=None`, which §6.2's `POST /validate` body already carries. | `library.py:365-374` | the route passes it |
| 10 | Errors: the six classes of §4.4. | Three more classes: `LibraryForbidden` (`forbidden`, 403), `LibraryBadRequest` (`bad_request`, 400) and `LibraryNotJson` (`unsupported_media_type`, 415). | `records.py:214-228` | "keep every error in records" (commit `5e06d9e`) |
| 11 | `store.connect(path)`; `Kind` is in `store.py`; Appendix A's names. | `connect(path, *, mounts=MOUNTS)` takes the mounts file so a test can pass a fake one. `store.py` also has `read`, `decomposition_named`, `filesystem_type`, `refuse_network_filesystem`, `BUSY_TIMEOUT_MS` and `MOUNTS`. `Kind` is defined in `records.py` and re-exported. | `store.py:69-70, 133-168, 238-256`; `records.py:11` | none recorded |
| 12 | The temporary file is `library.sqlite.<pid>.new` (§4.2). | It is `library.sqlite.<pid>-<8 hex>.new`. | `store.py:201` | none recorded |
| 13 | Heads are ordered by `created_rev`. | Heads are ordered by the rowid of each entity's version 1, so creation order also holds inside one revision. [CI: `test_heads_are_in_creation_order_within_one_revision`] | `store.py:72-89` | none recorded |
| 14 | Endpoints are plain `def` functions on Starlette's thread pool (§4.8). | Each route is an `async` endpoint that reads the body, then calls the handler through `run_in_threadpool`. The effect is the same. | `api.py:312-323` | none recorded |

### 2.3 Tests, experiments, wiring and size

| # | Design | Built | Where | Reason |
|---|---|---|---|---|
| 15 | E7 level 2's working folder holds a symlink `configs` pointing into the checkout (§7.1). | The working folder holds a **copy** of the corpus folder (`shutil.copytree`). | `test_roundtrip.py:170-177` | Whatever a tool writes beside its data (rag's embeddings sidecar) lands in the copy, never in the checkout (docstring) |
| 16 | D1's `FakeOpenAI` gains `/v1/embeddings`, or D2 keeps "its own ten-line fake" (§7.5). | D2 keeps its own: an 84-line threaded `http.server` serving chat and embeddings. The `dr-acp` falsifier uses D1's async `FakeOpenAI`. | `tests/library/fake_openai.py` | the design's own alternative |
| 17 | D2 adds a CI step that checks out deep_reasoner_beta at the pin and sets `DR_BETA_CHECKOUT` (§7.5). | D1's `ci.yml` already does both (lines 12-26). D2 changes no workflow. | `.github/workflows/ci.yml` | none needed |
| 18 | "40 files at `d7334ae`"; "all 38 loadable files pass level 1" (§7.1). | There are **39** `*.yaml` files at `d7334ae` [run: `find`; commit `8bea912` also says 39]. Of these, 37 are configs and 2 are the refused namespace files. Level 1 has 39 + 1 cases and level 2 has 37 + 1. | `tests/library/corpus.py` | the design's count |
| 19 | §7.3 is one sequence through `dr-acp`: save v1, open a session and prompt; then edit to v2, open a new session and prompt. | Through `dr-acp` there are two independent parametrized cases (`saved`, `edited`), each with its own Library and its own `dr-acp` process. The v1-then-v2 sequence on one Library is tested one layer down (`LibraryCatalog`, then `dr`). The hint is not asserted through `dr-acp`. | `tests/library/test_acp.py`; `tests/library/test_catalog.py:127-171` | none recorded |
| 20 | About 1.1k LOC of code and 0.8k of tests (§3 item 16). | 2,684 lines of code (2,239 non-blank) and 2,576 of tests (2,203 non-blank). | §1 | §4.2 and §4.7 hold most of the length |

---

## 3 · The public surface, from the code

### 3.1 Python

`deep_reasoning.library` exports `Library`, `LibraryCatalog`, `library_path`, `LIBRARY_FILE`,
`Effective`, the records (`ProfileRecord`, `NamespaceRecord`, `DecompositionRecord`, `ToolRecord`,
`HistoryEntry`, `LibraryState`, `ImportReport`, `Manifest`, `DecompositionMeta`, `Problem`,
`ValidationResult`) and the errors. [read: `__init__.py`]

`Library` (`library.py`) [read; each method exercised by `test_library.py` and the other test files, CI]:
- **`Library.open(path=None, *, starter=True)`** creates the file when it is absent, then connects
  (which migrates). With the starter, revision 1 imports `starter.yaml` under action `create`. With
  `starter=False`, revision 1 is profile `{}` and `root` = `name: root`. [run]
- **Reads**, one read transaction each: `rev()`, `state(*, rev=None)`, `profile()`, `namespaces()`
  (root first, then creation order), `namespace(name)`, `decompositions()` (by slug),
  `decomposition(name_or_slug)`, `tools()`, `tool(name)`, `history(kind, key)` (newest first,
  tombstones included; a decomposition's key may be a slug, even after deletion),
  `effective(namespace)`, `check()`, `validate(kind, text, *, name=None, source=None)`. Each
  single-entity read builds the whole `LibraryState` and picks from it (`library.py:296-320`).
- **Writes**, one revision each, or none when nothing changes: `put_profile(text, *, decompositions,
  base_version)`, `put_namespace(text, *, decompositions, base_version)`,
  `put_decomposition(text, *, use_when, hint, namespaces, top_level, base_version)`,
  `put_tool(name, text, *, source, granted_in, base_version)`, `delete(kind, key, *, base_version)`
  (which returns the tombstone) and `import_config(path)` (which returns an `ImportReport`). Every
  keyword defaults to `None`, meaning "leave as it is" for list arguments and "unconditional" for
  `base_version`.
- **`materialize(dest=None, *, namespace=None, rev=None) -> Path`**.

Records are frozen pydantic models. The four entity records carry `yaml` and a computed `data`
(the YAML parsed), so D3 needs no YAML parser, as in design §4.4. [read: `records.py`]

| Error | `error` | Status | Extra payload |
|---|---|---|---|
| `LibraryError` (also `NETWORK_FS`) | `error` | 400 | |
| `LibraryValidationError` | `invalid` | 422 | `errors: [{loc, msg}]` |
| `LibraryNotFound` | `not_found` | 404 | |
| `LibraryConflict` | `conflict` | 409 | `head`: the current record, or `null` |
| `LibraryRefused` (delete refusals, `DEST_NOT_EMPTY`, root or profile missing) | `refused` | 409 | |
| `LibraryImportError` | `import_failed` | 422 | |
| `LibraryForbidden` | `forbidden` | 403 | |
| `LibraryBadRequest` | `bad_request` | 400 | |
| `LibraryNotJson` | `unsupported_media_type` | 415 | |

[read: `records.py:158-228`]

### 3.2 `dr-library`

```text
dr-library serve  --port PORT [--home DIR] [--log-level LEVEL]   uvicorn on 127.0.0.1:PORT
dr-library import PATH [--home DIR]        imported PATH as revision N: A new, B changed, C unchanged
                                           | nothing changed: the library already holds PATH
dr-library export DIR [--home DIR] [--namespace NAME] [--rev N]
                                           wrote DIR/main.yaml: 1 namespace, 0 decompositions, 0 tools
```

Every subcommand opens the library first, creating it with the starter if it is absent. The exit
code is 0 on success; 1 for any `LibraryError`, with its sentence on stderr; 2 for a usage error.
[run: export of a fresh home printed the line above; a second export into the same folder exited 1
with `DEST_NOT_EMPTY`; CI: `test_cli.py`]

### 3.3 HTTP

The routes are design §6.2's table exactly, with no import route [read: `api.py:330-371`; CI:
`test_every_read_answers_its_records` (13 GETs), `test_every_write_route`]:

```text
GET /health  GET /problems  POST /validate  GET|PUT /profile  GET /effective  GET /export?namespace=
GET /namespaces       GET|PUT|DELETE /namespaces/{name}     GET /namespaces/{name}/effective
GET /decompositions   GET|PUT|DELETE /decompositions/{slug}
GET /tools            GET|PUT|DELETE /tools/{name}
GET …/versions  GET …/versions/{n}     for /profile, /namespaces/{name}, /decompositions/{slug}, /tools/{name}
```

Every request, `/health` included, passes the guard before it reaches a route. The guard checks, in
order: same-user (Linux default; another platform gets no peer check), then `Host`, then the JSON
content type for `PUT` and `POST`. [read: `api.py:76-114`]

### 3.4 `dr-acp`

Without `--config`, `dr-acp` builds `LibraryCatalog(library_path(--home))`; with `--config`, it
keeps D1's `ConfigCatalog`. When `RunSource.versions` has a `library` key, the session index's
`source` is `{"kind": "library", "library": <path>}`. [read: `acp/cli.py:93-97`,
`acp/session.py:198-203`; CI and run: `test_without_a_config_dr_acp_serves_the_library_at_its_home`,
`tests/library/test_acp.py`]

---

## 4 · Structure and seams

### 4.1 The file: `store.py`

- **Schema.** Version 1 is design §4.2's DDL verbatim: `revisions` and `versions` as `STRICT`
  tables, its `CHECK` constraints, and four triggers that abort any `UPDATE` or `DELETE` on either table.
  `MIGRATIONS = (SCHEMA_V1,)` is applied by `PRAGMA user_version`, one `BEGIN IMMEDIATE` per step.
  [read; CI: `test_versions_and_revisions_cannot_be_updated_or_deleted`]
- **`connect`.** On Linux, `connect` first reads `/proc/self/mounts`, finds the longest mount point
  that holds the path, and refuses `nfs`, `nfs4`, `cifs`, `smb3`, `smbfs`, `9p` and `fuse.sshfs` with
  `NETWORK_FS`. It then sets `foreign_keys`, `busy_timeout = 5000` and `synchronous = FULL`, uses
  autocommit mode with explicit `BEGIN`, and migrates. [read; CI with a fake mounts file]
- **`create`.** The file is created 0600 with `O_EXCL` under a temporary name, switched to WAL,
  seeded, and published with `os.link`. If another process publishes first, `create` returns False;
  the temporary file and its `-wal` and `-shm` are removed either way.
  [read; CI: `test_a_new_library_file_is_private_to_its_user`,
  `test_a_second_creator_loses_and_leaves_nothing_behind`]
- **Writing and reading.** `write()` is `BEGIN IMMEDIATE … COMMIT`, with `ROLLBACK` on any exception;
  `read()` is `BEGIN … ROLLBACK`. In a `Writer`, the first `add` creates the revision row (max + 1,
  UTC to the second). Each `add` inserts version head + 1, stamped with `deep_reasoner_build()`
  (`0.2.1+d7334ae` here [run]). [read; CI: `test_two_processes_saving_at_once_both_land`,
  `test_an_exception_inside_a_save_writes_nothing`]
- **`Row` crosses this seam.** It is one version joined to its revision's time and action. Heads as
  of revision N are the highest version with `rev <= N` that is not a tombstone.

### 4.2 One save: `library.py`, where the complexity sits

Every write method has the same shape [read: `library.py:400-498, 539-576`]:

1. Validate the input with `shapes`, outside any transaction.
2. `_save` opens `store.write`.
3. `_base` checks `base_version` against the live head: `0` means it must not be live
   (`CONFLICT_EXISTS`); `n` means it must be live at `n` (`CONFLICT_STALE`, or `LibraryNotFound`).
   A conflict carries the head's record.
4. `_add` writes the entity only if its `yaml`, `attached`, `slug`, `use_when`, `hint` or `source`
   differs from a live head. `""` and `None` both store no use-when line or hint.
5. The cascade (below).
6. `_read_back` reads the record inside the same transaction.
7. On leaving, if the save wrote anything, `_check_invariants` runs over every live head. Any raise
   rolls the whole save back.

**Cascades** [read; CI: `test_namespaces_is_the_exact_set_after_a_save`,
`test_granted_in_is_the_exact_set_after_a_save`, `test_deleting_a_decomposition_detaches_it_everywhere`,
`test_deleting_a_tool_ungrants_it_everywhere`, `test_root_the_default_and_a_parent_cannot_be_deleted`]:
- A decomposition's `namespaces=` is the exact set afterwards: the decomposition is appended to each
  newly named namespace's list and removed from each unnamed one. `top_level=` does the same on the
  profile's list.
- A tool's `granted_in=` rewrites the `tools` list of each namespace whose grant changes, and
  re-validates that namespace's YAML.
- Each namespace or profile whose list changes gets a version in the same revision. An omitted list
  keeps the head's.
- `delete` writes a tombstone, which keeps the slug. A decomposition's tombstone detaches it
  everywhere, and a tool's ungrants it everywhere. Deleting `root`, the default namespace or a
  namespace with live children is `LibraryRefused`.

**Invariants** (design §2.5 items 1 to 5) [read: `library.py:153-183`]:
- profile and `root` live (`LibraryRefused`, `REFUSE_ROOT`);
- every namespace's parent live (`PARENT_MISSING`);
- the default namespace live (`DEFAULT_MISSING`);
- slugs unique (`SLUG_TAKEN`);
- every attached name live and listed at most once (`UNKNOWN_DECOMPOSITION`, `LISTED_TWICE`).

The last four raise `LibraryValidationError`, which is 422. Item 6 is the `shapes` validation in
step 1.

**`check()` and stale heads.** `_stale` re-validates every live head under the installed
deep_reasoner. `check()` adds two more problems: a granted tool the Library does not define (`llm`
counts as defined while the profile has a `model`), and a `spawn` target that is not live.
`materialize` raises `LibraryValidationError`, listing every stale head, before it writes anything.
[read; CI: `test_a_head_that_stops_validating_is_a_problem_and_blocks_materialize` (a monkeypatched
stricter model), `test_check_reports_ungranted_tools_and_missing_spawn_targets`]

### 4.3 Import and materialize: `configdir.py`

**Reading a config** [read; CI: `test_import.py`]. `read_config` loads with D1's `load_dr_config`
(deep_reasoner's `load_cli_config`, plus `namespaces_dir` resolved against the config's folder):
- The profile is the dump without `SPLIT_KEYS`.
- Namespaces come in this order: `root`, which is always present (a bare `name: root` when the
  config authors none); then the `namespaces_dir` files; then inline namespaces. A later namespace
  replaces an earlier one with the same name.
- Decompositions are collected by name, top level first. Equal bodies under one name are one
  decomposition. Different bodies under one name are `IMPORT_COLLISION`, naming both places. Two
  names with one slug are `SLUG_TAKEN`.
- A tool's `factory_from` file is read relative to the main config's folder and renamed
  `tools/<name>.py`.
- A `library.yaml` beside the config supplies use-when lines and hints. If it does not parse, it is
  ignored without a message.
- Any load failure is `IMPORT_LOAD` with `Type: message`.

**Writing the import.** `_import` validates every part, then opens one revision. It writes the
decompositions (keeping the head's use-when line and hint unless the manifest supplies them), then
the tools, then the namespaces in config order (§2 #6), then the profile, each only if it changed.

[run] Every import names the profile and `root`, so it replaces both. Importing a config with no
`root` into the starter Library rewrote `root` from `{repl: {type: local}, tools: [llm]}` to
`name: root`. It also replaced the profile: the starter's `client` and `system_prompt` were gone,
because that config had none. This is design §4.6 step 3 as written.

**Writing a directory.** `write_config` writes, in order [run; CI: `test_materialize.py`]:
- `namespaces/<ns>.yaml` for every live namespace: its YAML with its attached bodies inlined, in
  order, validated as `NamespaceConfig`;
- `tools/<t>.py` for each tool with a source;
- `library.yaml`, the `Manifest`;
- `main.yaml`, last: the profile's data; `entry_namespace` when it differs (§2 #3);
  `namespaces_dir: namespaces`; the top-level bodies; and the tool blocks.

`main.yaml` and `library.yaml` start with the one-line `# Written by the deep-reasoning Library …`
comment. `Library.materialize` refuses a namespace that is not live, a stale head, and a `dest` that
exists and is not empty. When `dest` is not given, it uses a new temporary directory. When a write
fails, it removes a `dest` it made, or empties one it did not. [read; CI]

### 4.4 Validation and canonical YAML: `shapes.py`

`canonical_yaml` is `yaml.dump` with a `SafeDumper` subclass: strings holding a newline become
literal blocks, `sort_keys=False`, Unicode is kept, and the width is 100. It is applied to
`model_dump(mode="json", exclude_unset=True)`. [read; CI: `test_canonical_yaml_*`]

Each kind is validated against [read; CI: `test_shapes.py`]:
- namespace: deep_reasoner's `NamespaceConfig`, plus `NAMESPACE_NAME` and no `decompositions` key;
- decomposition: `Decomposition`, plus the name rules, a non-empty slug and the `METADATA_IN_YAML`
  lines;
- tool: a mapping with string keys (there is no model), an identifier name, and the `factory_from`
  rules;
- profile: `V2Config` with each `SPLIT_KEYS` key reported as an error.

The `NO_FINAL_ANSWER` warning uses deep_reasoner's `code()`, whose default delimiters are
`<repl>`/`</repl>`. `slug` is D1's function, imported, so a decomposition's slug is the slash command
D1 shows.

### 4.5 The effective view: `effective.py`

The values are deep_reasoner's: `build_namespace_registry(V2Config(profile + every live namespace
with its bodies inlined)).resolve(ns)`. The sources are the Library's, from a walk over the dotted
chain:
- `repl`: the last level that sets it, else `profile`;
- `reasoner` and `spawn`: the last level that sets them, else `None`;
- `system_suffix`: every level that sets one;
- `tools`: the first level that lists each;
- `vars`: the last level that sets each key;
- `decompositions`: the last level whose list has the name.

Top-level decompositions do not appear, because `resolve` does not return them.
`test_effective_values_equal_deep_reasoners_resolve` covers every namespace of each of the 37 corpus
configs. It checks that each value read back from the level its source names equals deep_reasoner's
`resolve`, and that no later level sets it.
[read; CI and run. Run: `course_advisor` after importing `advisors.yaml` gives repl `{type: local}`
from `profile`, `llm` from `root` (defined), `catalog` from `course_advisor`, and `catalog lookup`
from `course_advisor`, which is design §6.3's example.]

### 4.6 The seam to D1: `LibraryCatalog`

`LibraryCatalog` implements D1's `Catalog` protocol with D1's shapes unchanged. `acp/catalog.py` has
no commit after D1's `8cb3798`. [read: `git log`]

- **Construction** stores the path. The first call opens the Library, creating it with the starter.
  Building the catalog imports nothing of deep_reasoner. [run: 0.18 s, `deep_reasoner` not in
  `sys.modules`; CI: `test_building_a_catalog_imports_nothing_of_deep_reasoner`]
- **`snapshot()`** takes `state()`, materializes that revision into a temporary directory at the
  profile's default namespace, and returns D1's `ConfigCatalog(main).snapshot()`. On each
  `CommandEntry` it replaces `description` with the Library's use-when line and `hint` with its hint,
  where the Library has them. The namespaces, their order, the menus and the first-name-wins rule
  are therefore D1's own. [read; CI:
  `test_snapshot_equals_config_catalog_over_the_materialized_config_plus_metadata`]
- **`materialize(namespace, run_dir)`** writes `run_dir/config/` at that namespace, then returns
  `ConfigCatalog(main).materialize(...)` with `versions` replaced by the manifest's: `{v, library,
  rev, namespace, deep_reasoner, profile, namespaces, decompositions, tools}`. D1 records these in
  `run.start.source.versions`. [CI: `test_materialize_gives_d1_a_run_source_with_versions`; run and
  CI through `dr-acp` in §6.4]
- **What crosses the seam** is the materialized directory, which D1's worker loads as a plain `dr`
  config, and `RunSource.versions`. The menu and the run are materialized separately, at
  `session/new` and at the first prompt, so a save in between is in the run but not in the menu
  (design §4.7, "Freshness"). [read]
- **Cost.** Every `snapshot()` materializes the whole Library. The first `snapshot()` took 1.36 s,
  which includes creating the starter Library and importing deep_reasoner; the second took 0.016 s.
  [run]

### 4.7 The App backend: `api.py` and `cli.py`

- `create_app(library, *, same_user=None)` returns a Starlette app wrapped in `_Guard`, with one
  exception handler that maps every `LibraryError` to `payload()` and its status.
  `same_user_peer(client, server)` reads `/proc/net/tcp` and `tcp6`, finds the client-to-server row
  and compares its uid with `os.getuid()`. [read; CI with a fake `/proc/net`]
- A `PUT` checks that the path key is the YAML's own (the name, or the decomposition's slug); a
  mismatch is 400 `NAME_MISMATCH`. The check applies only when the YAML is valid; otherwise the
  write's 422 answers. 201 or 200 depends on whether the entity was live before the request, which
  is read before the save, outside its transaction (`api.py:240, 251, 264`). [read; CI:
  `test_creating_a_decomposition_answers_201_and_updating_200`]
- `GET /effective` calls `effective` once per namespace, each in its own read transaction, so the
  list is not taken at one revision (`api.py:347-351`). `GET /export` materializes the current
  revision into a temporary folder and zips it under `library/` as `library-rev<N>.zip`. [read; CI:
  `test_export_is_a_zip_of_a_materialized_directory`]
- `serve` runs uvicorn on 127.0.0.1. The package logs nothing of its own; the only log is uvicorn's,
  on stderr. [read] Started with only `LANG`, `LC_ALL`, `LC_CTYPE`, `PATH`, `TMPDIR` and `TZ`, it
  answered `/health` 1.74 s after launch:
  `{"ok":true,"rev":1,"path":…,"deep_reasoner":"0.2.1+d7334ae","default_namespace":"root"}`.
  [run; CI: `test_serve_answers_health_on_loopback`]

### 4.8 What it relies on

- **deep_reasoner** (`d7334ae`): `NamespaceConfig`, `Decomposition`, `V2Config`,
  `build_namespace_registry`, `load_namespaces_from_dir`, `ROOT`, `code` and `NoCodeBlock`, all in the
  package; `write_fake_claude_cli` in the tests. [read: imports]
- **D1**: `acp.catalog` (`CatalogSnapshot`, `CommandEntry`, `RunSource`, `ConfigCatalog`,
  `load_dr_config`, `slug`), `acp.runlog.Home`, `tests/conftest.py`, `tests/acp/harness.dr_acp` and
  `acp.testing.fake_model.FakeOpenAI`. [read]

These are design §8's L1–L11 and its D1 list. I did not re-check §8's deep_reasoner line numbers.

---

## 5 · Wiring

- **`pyproject.toml`** (D2's edit): `starlette>=0.40`, `uvicorn>=0.30`, `httpx` in the dev group, and
  the script `dr-library = "deep_reasoning.library.cli:main"`. The wheel ships `starter.yaml` because
  hatch packages `src/deep_reasoning`. [run: `uv build`; see the commit that adds this file]
- **D1's files.**
  - `acp/cli.py` builds `LibraryCatalog` without `--config`; `EXIT_USAGE` and `NEEDS_CONFIG` are
    gone.
  - `acp/session.py` writes the Library `source`.
  - `tests/acp/harness.dr_acp` takes `config=None`.
  - D1's "exits 2 without a config" test is now `test_without_a_config_dr_acp_serves_the_library_at_its_home`.

  [read: `git diff 21f4a8b..90044f0`]
- **`as_built/`.** This document's commit adds `as_built/` to the sdist's `exclude`, beside `docs/`.
  Pytest's `testpaths = ["tests"]` and the wheel's `packages` already leave it out, and CI's ruff
  checks only `src` and `tests`. The repo has no docs site. [run: `uv build`]
- **CI.** D1's `ci.yml` checks out the corpus and sets `DR_BETA_CHECKOUT`, so E7 runs in CI.
  `test_the_corpus_is_read_in_ci` fails if `CI=true` and the corpus is missing. D1's `live.yml` runs
  `pytest -m live`, which includes `tests/library/test_live.py`. [read; CI]

---

## 6 · Experiments, as measured

### 6.1 The runs

| Run | Conditions | Commit | Result |
|---|---|---|---|
| CI [37085759535](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37085759535) | ubuntu-latest, Python 3.12.3, corpus fetched at `d7334ae`, ruff check and format first | `90044f0` | 515 passed, 4 deselected, 319.57 s. D2's 285 cases passed with none skipped; `test_roundtrip.py`'s 79 cases took about 106 s [CI] |
| live [37085761405](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37085761405) | `workflow_dispatch`, `OPENAI_API_KEY` secret, `pytest -m live -v -rA` | `90044f0` | 4 passed, 387 deselected, 47.21 s, including `tests/library/test_live.py` [CI] |
| local | this sandbox, `CI=true`, a clone of the corpus at `d7334ae` | `90044f0` | `tests/library` + `tests/acp/test_cli.py`: 289 passed, 1 deselected, 261.73 s [run] |

To reproduce:
- E7, the falsifier and the rest of D2's deterministic suite:
  `DR_BETA_CHECKOUT=<deep_reasoner_beta at d7334ae> uv run pytest tests/library`.
- The live tier: `OPENAI_API_KEY=… uv run pytest -m live tests/library/test_live.py`.

### 6.2 E7 · round-trip, level 1 (no model)

**Conditions.** Each of the 39 corpus files, plus one config the test writes (`configs/example`'s
`main.yaml` composed with its `namespaces/` folder), goes through these steps: import into a fresh
Library (`starter=False`); materialize at the original's `entry_namespace`; load with
`load_dr_config`.

**Assertions:**
- the `V2Config`s are equal except `config_path`, `namespaces`, `namespaces_dir` and `factory_from`;
- the same namespace names exist, and `resolve` is equal for each;
- tool files are byte-identical;
- re-importing the copy into a second Library gives equal rows;
- re-importing it into the first Library makes no revision.

**Result.** 38 pass. The other 2 (`configs/example/namespaces/root.yaml` and
`docs/configs/catalog/namespaces/root.yaml`) are refused at import with `tools … Input should be a
valid dictionary`, as asserted. [CI; run]

### 6.3 E7 · round-trip, level 2 (a fake model)

**Conditions.** `dr <config> "Which course comes after CS101?" --no-progress --run-dir …` runs on the
original and on its materialized copy. The fake model answers every chat call with
`<think>ok</think>` and `FinalAnswer("done")`, and every embedding with a fixed 4-vector. The run
also has:
- `--set client.base_url=<fake>`, and the same for each tool block with its own `client`;
- dummy provider keys;
- deep_reasoner's fake Claude CLI first on `PATH`;
- `HTTP(S)_PROXY` pointed at 127.0.0.1:9, so no other host is reachable;
- as working folder, a copy of the corpus folder.

**Compared:** exit code, last line of stdout, and the first chat request's `messages`. Each original
is the baseline for its copy.

**Result: 38 of 38 equal** [CI; run]. Per config, from a probe that reuses the committed harness
[run]:

| Outcome on both sides | n | Configs |
|---|---|---|
| exit 0, last line `done`, a model request made | 19 | `configs/example/` main, rag, safe_url, v2_namespaces; `docs/configs/catalog/` advisors, crossover, kg_agent, kg_query, llm, llm_tool, main, namespaces, namespaces_dir, restricted, sandboxes; `docs/configs/examples/` cruncher, experience, research/assistant, waitlist |
| exit 0, last line `The Claude session ended without calling FinalAnswer, and this reasoner has no run left in its budget. ok`; no request to the fake | 2 | `docs/configs/catalog/claude.yaml`, `docs/configs/incidents/triage.yaml` (Claude backbone, fake CLI) |
| exit 1 before any model request; stderr `ValueError: LLM requires a model.` | 14 | `configs/example/` agent, claude, client, docs, rag_agent, namespaces/math, namespaces/math.geometry; `docs/configs/catalog/` client, courses, credits, namespaces/librarian, namespaces/librarian/archive; `docs/configs/examples/experience/memory.yaml`; `docs/configs/incidents/workers.yaml` |
| exit 1; stderr `ValueError: Unknown tool 'llm'` | 2 | `configs/example/namespaces-inline.yaml`, `docs/configs/catalog/agent.yaml` |
| exit 1; stderr `ValueError: Unknown tool 'Var'; known: 'llm'` | 1 | the composed `configs/example` + `namespaces/` |

The stderr lines are the original side's; the test does not compare stderr. The guard pins the 19
and the 2 (`ANSWERING`, `CLAUDE_BACKBONE` in `test_roundtrip.py`), so a broken fake cannot pass by
failing everywhere. The design's prototype had measured 17 answering, without the fake Claude CLI.

### 6.4 D3's falsifier, at the store (design §7.3)

**Through `dr-acp`** (`tests/library/test_acp.py`) [CI; run]. A Library holds our own router config
pointed at D1's `FakeOpenAI`. The test saves "summarize then rank" in `router` with use-when
"comparing many courses", and in the `edited` case saves it again with a different worked example.
It then starts `dr-acp --home <tmp>` with no `--config`, opens a session and asks one question.

| Assertion | `saved` | `edited` |
|---|---|---|
| menu `/summarize-then-rank` described "comparing many courses" | yes | yes |
| outcome `answered`, `run.start.namespace == "router"` | yes | yes |
| `run.start.source.versions.decompositions["summarize then rank"]` | 1 | 2 |
| first model request holds the saved version's user message, not the other's | v1 | v2 |
| session index `source == {"kind": "library", "library": <home>/library.sqlite}` | yes | yes |

**Below the front** (`test_catalog.py`) [CI; run]. On one Library: save v1, then
`LibraryCatalog.materialize` and `dr`; then edit to v2, materialize and run again. The runs record 1
then 2, and the second run's first request carries v2's text and not v1's.

### 6.5 Live tier (`tests/library/test_live.py`, gpt-6-luna)

**Conditions.** The test opens a Library with the starter and imports D1's
`docs/configs/advising/main.yaml` (OpenAI, `OPENAI_API_KEY`). It saves `first course` in `advising`
(`base_version=0`) and then edits its worked example (`base_version=1`). It then:
- asserts that `history` shows v2 then v1;
- asserts that a decomposition with `use_when:` inside the YAML is refused with the spec's failure
  cell verbatim, and that no revision is made;
- materializes `advising` and asserts that the manifest records the revision and `first course: 2`;
- runs `dr <dir>/main.yaml "Which course must a student finish before CS102?"`.

**Asserted:** exit 0; the last line names `CS101`; the root agent's node log carries v2's question
and neither v1's nor the refused one.

**Result: passed** in live run 37085761405 at `90044f0`, about 4.6 s between its PASSED line and the
previous one [CI]. The log does not record the run's token cost.

---

## 7 · What I could not verify

1. **The `Host` guard behind the agent-server.** `api.py:89-91` answers 403 to any `Host` other than
   `127.0.0.1:<port>` or `localhost:<port>`, on every route including `/health`. The design (B2, B3)
   does not say which `Host` the agent-server's bridge forwards, or which `Host` its readiness probe
   sends. I did not read the SDK fork: it is outside this brief, and the one attempt to read its
   `bridge.py` was refused in this session. If the bridge forwards the ingress `Host`, every D3
   request is 403. If the probe does, the backend never becomes ready. Nothing in the suite goes
   through the bridge.
2. **The same-user check against another real OS user.** Only a fake `/proc/net` is tested for
   refusal. The real-socket path is exercised only for the same user (`dr-library serve` in
   `test_cli.py` and in my probe, both answered 200).
3. **`NETWORK_FS` on a real network mount.** Only a fake mounts file is tested. macOS has no peer
   check and no mount check (both by design); nothing was run on macOS.
4. **Concurrency beyond two writers.** `test_two_processes_saving_at_once_both_land` is the only
   multi-process test. The 201/200 choice under a concurrent create (§4.7) and `GET /effective`'s
   per-namespace reads were read, not run.
5. **The freshness path** (design §4.7): a command whose decomposition is deleted between
   `session/new` and the first prompt should fail as D1's `build_failed`. There is no test, and I
   did not run it. [read]
6. **A real pin bump.** Stale-head detection is tested only with a monkeypatched stricter model.
7. **Design §8's deep_reasoner and agent-server line references** were not re-checked.
8. **The live tier's token cost** is not in the CI log.
