# D2 · Library store, as built

**TASK-5** · Cartographer · **r2, 2026-10-04** · the code at `0e0a394` (head of
`v1-library-store`; this file is on `as-built/d2-r2`) · checked against design v2 (`41416c7`,
`docs/design/d2-library-store.md`, unchanged at `0e0a394`) · deep_reasoner_beta `d7334ae`.
r1 (`90044f0`, 2026-10-03) is replaced; what changed since it is §2.1.

`0e0a394` is D2's code (`src/deep_reasoning/library/`, `tests/library/`) and D2's edits to D1's
files (§5), on D1's merged stack (main `32c7f61`, merged at `a7bbe41`; D1's as-built `f7a91f3`, at
`76d23b2`). D2's own commits since r1 are `cd0b60c` (the effective view's stale-head refusal, with
its failing test `802a639`) and the refactor `452db0e..0e0a394` (16 commits). "Before" in this
document is `76d23b2`, the commit under the refactor.

**Evidence marks.** Every claim carries one.
- **[run]**: executed in this sandbox at `0e0a394`: the full suite
  (`DR_BETA_CHECKOUT=/home/user/deep_reasoner_beta uv run pytest`), `ruff check`, `ruff format
  --check`, `uv lock --check`, the Refactorer's differential probe at `cd0b60c` and at `0e0a394`,
  66 one-line mutations (§9), and uncommitted probe scripts. The corpus checkout's `git status`
  was empty before and after.
- **[CI]**: read from GitHub's logs of CI run 37165314704 and live run 37166626513, both at
  `0e0a394`. I ran no paid model and no live test.
- **[read]**: read in the code and **not executed**. Weaker than [run]; §12 lists the read
  claims that matter.

**Reading order for Gate C.** §2 (divergences), §9 (what no test pins), §10 (what D3 and D4 rely
on), then §3–§5 as the map of the code.

---

## 1 · What exists

The Library is one SQLite file, `<home>/library.sqlite`, holding one profile and any number of
namespaces, decompositions and tools, each stored as canonical YAML in deep_reasoner's own shapes.
Every save appends immutable version rows under one library-wide revision number. Three kinds of
process open the file, each with a fresh connection per operation [read; each is run end to end by
the suite, §7]:
- `dr-library serve`, the App backend's HTTP API (D3's panel; D4's routes join it);
- `dr-library import` and `dr-library export`;
- each `dr-acp`, in-process, through `LibraryCatalog`.

```text
D3's panel ─HTTP─▶ dr-library serve: api.create_app ─┐
dr-library import | export: cli.main ────────────────┼─▶ Library (library.py) ─ store.write / store.read ─▶ library.sqlite (WAL, 0600)
dr-acp: LibraryCatalog (catalog.py) ─────────────────┘      ├ shapes.validate_*      deep_reasoner's models, canonical YAML
                                                            ├ configdir.read_config  a plain dr config ─▶ parts      (import)
                                                            ├ configdir.write_config state ─▶ main.yaml, namespaces/<ns>.yaml,
                                                            │                        tools/<t>.py, library.yaml   (materialize)
                                                            └ effective.effective    inherited values and their sources
```

| Part | Lines at `0e0a394` (non-blank) | Before the refactor, `76d23b2` | Where |
|---|---|---|---|
| the package | 2,598 (2,142), plus the 24-line `starter.yaml` | 2,696 (2,249) | `src/deep_reasoning/library/` |
| tests | 2,495 (2,138) | 2,597 (2,222) | `tests/library/` |
| edits to D1's files | +82 −41 over main | | §5 |

The length sits in `library.py` (702 lines: the save semantics, §4.2) and `api.py` (370: the routes
and the request guard, §4.7). [run: `wc -l`, `grep -cv '^\s*$'`]

---

## 2 · Divergences from design v2 (`41416c7`)

No changelog `drift:` line exists for TASK-5 [read: the Changelog database], so each row below was
found from the code. Design v2 describes `90044f0`; its header says "Commits after it on this branch
change only `docs/`", which no longer holds. Each row gives the reason the code or its commit
message gives.

### 2.1 Since r1: the stale-head fix and the refactor

| # | Design v2 | Built at `0e0a394` | Where | Reason |
|---|---|---|---|---|
| 1 | `Library.effective` and both effective routes name no error for a head that no longer validates (§4.5, §6.2); §4.4's table gives `STALE_HEAD` only "at materialize". | When deep_reasoner refuses the config the view builds, `effective` raises materialize's `LibraryValidationError`: one `STALE_HEAD` sentence per stale head, **422** `invalid`, as message and as `errors[].msg` with `loc` `""`. A stale tool, or a stale decomposition nothing attaches, does not enter that config, so the view still answers 200 [read: `effective.py:57-70`]. [run: `test_a_stale_head_makes_the_effective_view_answer_422_naming_it[/effective, /namespaces/router/effective]` passes at `0e0a394`; at `802a639` both cases fail with pydantic's `ValidationError` raised out of the route, which a server answers as 500] | `library.py:118-127, 664-670` | `cd0b60c`: "the pydantic ValidationError escapes as a 500" |
| 2 | `store.Row` is a frozen dataclass with `at`, `attached` and `created_rev` (§4.2). | `Row = HistoryEntry` (`records.py:72-86`): fields `saved_at`, `decompositions`, no `created_rev`. Every read of the store, `Writer.head` included, returns `HistoryEntry`. [run: `store.Row is HistoryEntry`] | `store.py:76-101` | `b8f14d1` |
| 3 | The heads query selects `created_rev` and `created` and orders by `created` (§4.2). | It selects the `HistoryEntry` columns and orders by a subquery for the rowid of each entity's version 1. Creation order is unchanged. [CI: `test_heads_are_in_creation_order_within_one_revision`] | `store.py:79-94` | `b8f14d1` |
| 4 | `connect` opens with `isolation_level=None` (§4.2, B8). | `sqlite3.connect(path, autocommit=True, check_same_thread=False)` (Python 3.12's PEP 249 mode; `requires-python = ">=3.12,<3.13"`); `migrate` runs each step as one `executescript` inside its `BEGIN IMMEDIATE`. [run: `conn.autocommit` is `True`; `test_a_migration_that_fails_halfway_leaves_the_file_unmigrated`; mutation St1, §9] | `store.py:133, 142-156` | `290899f`: under `isolation_level=None`, `executescript` commits the open transaction first |
| 5 | `store.py` re-exports `Kind` (§4.2, Appendix A). | `store.py` has no `__all__`; `Kind` is imported there for its own signatures, so `store.Kind` still resolves. [run] | `store.py:22` | `e5c5aed`: every module and test, D3's and D4's included, imports it from `records` |
| 6 | Appendix A lists no `effective.defined_tools`. | `defined_tools(state)`: the Library's tools, and `llm` while the profile has a `model`. `check()` and `effective` both use it. | `effective.py:73-75`; `library.py:133` | `00d7a69` |
| 7 | One sentence lives outside `texts.py`: `base_version must be a whole number; got {raw!r}.` in `api.py` (§4.10, B4, §9 item 13). | It is `texts.bad_base_version(raw)`. | `texts.py:123-124`; `api.py:168` | `0c94c1b` |
| 8 | A handler's record is sent as `model_dump(mode="json")` (§4.8). | Routes send `pydantic_core.to_jsonable_python(payload)`; `api._dump` is gone. The JSON is identical (§7, the probe). | `api.py:312` | `452db0e` |
| 9 | D2 keeps its own fake OpenAI, `tests/library/fake_openai.py`; D1's `FakeOpenAI` is unchanged (B15, §7.1, §7.5). | The file is deleted. D1's `FakeOpenAI` gains `POST /v1/embeddings` (every input gets `EMBEDDING = [0.5, 0.5, 0.5, 0.5]`) and a sync `with` beside its `async with`; E7, `test_catalog.py` and `test_acp.py` all use it. D1's test file gains `test_embeds_every_input_alike_and_records_only_chat_calls`. | `acp/testing/fake_model.py:20, 98-143` | `633a3a8` |
| 10 | Not pinned by a test: a `namespaces` or `granted_in` name that is not a live namespace (B3), and `Library.validate(…, source=)` (B7); §9 item 13. | Pinned: `test_library.py::test_a_namespace_that_is_not_there_cannot_be_attached_to_or_granted_in[namespaces, granted_in]` and `test_api.py::test_validate_judges_a_tool_with_the_source_it_is_sent`. Of §9 item 13's four loose ends, the 201-or-200 race is the one left (`api.py:231, 242, 255`). [CI; mutations S8 and A3 are caught, §9] | `library.py:452-458`; `api.py:216-218` | `ca8dfa0`, `0e0a394` |
| 11 | §7.2 and the Gate B table name `test_sources`, `test_namespace_names`, `test_commands_carry_use_when_and_hint`, `test_a_top_level_decomposition_is_offered_in_every_namespace`, `test_a_slug_with_spaces_in_the_name_round_trips` and `test_the_spec_mock_up_runs_as_written`. | The first two are renamed and the other four deleted; four tests v2 does not name are added, and `tests/library/` runs 287 cases, not v2's 285 (§6). | `tests/library/` | `c922a02`, `cd77904` |
| 12 | B20: 2,684 (2,239) lines of code and 2,576 (2,203) of tests, by file. | 2,598 (2,142) and 2,495 (2,138); §8. | §1 | the refactor |

### 2.2 Still open from r1

| # | Design v2 | Built | Where | Reason |
|---|---|---|---|---|
| 13 | `Manifest.library` is "the library file's absolute path" (§4.4). | It is the path the Library was opened with, unresolved, so a relative home gives a relative `library` in `library.yaml`, in `RunSource.versions` and in the session index's `source`. [run: `Library.open(Path("rel/library.sqlite"))` then `materialize` wrote `library: rel/library.sqlite`; the other two carry the manifest's value, `catalog.py:77-83`, `acp/session.py:199-204`, read] | `configdir.py:164`; `library.py:61` | none recorded (r1 §2 #4; v2 did not take it up) |

Every other divergence r1 named (#1–#3, #5–#20) is design v2's §3.2 B1–B20, and each still
holds at `0e0a394` [read: `configdir.py`, `cli.py` and `store.create` have no change since
`90044f0`; the rest is re-read in §3–§4].

---

## 3 · The public surface, from the code

### 3.1 Python

`deep_reasoning.library` (`__init__.py`) exports eagerly `LIBRARY_FILE`, `library_path`,
`LibraryCatalog`, the records (`DecompositionMeta`, `DecompositionRecord`, `HistoryEntry`,
`ImportReport`, `LibraryState`, `Manifest`, `NamespaceRecord`, `Problem`, `ProfileRecord`,
`ToolRecord`, `ValidationResult`) and v1's six errors; `Library` and `Effective` load on first use
through a module `__getattr__` (`__init__.py:32, 60-63`). [read; CI:
`test_building_a_catalog_imports_nothing_of_deep_reasoner`]

**`Library`** (`library.py:53-427`) [read; every method is called by the suite, CI and run]:
- `open(path=None, *, starter=True)` (`:58`) creates the file when absent: revision 1 imports
  `starter.yaml` under action `create`, or with `starter=False` is profile `{}` and `root` =
  `name: root` (`:693-702`).
- **Reads**, one read transaction each: `rev()` `:69`, `state(*, rev=None)` `:73` (`NO_REVISION`
  outside 1 … now), `profile()` `:81`, `namespaces()` `:84` (root first, then creation order),
  `namespace(name)` `:88`, `decompositions()` `:91` (by slug), `decomposition(key)` `:95` (name or
  slug), `tools()` `:101`, `tool(name)` `:104`, `history(kind, key)` `:107` (newest first,
  tombstones included; a decomposition's slug works after deletion), `effective(namespace)` `:118`
  (§2.1 #1), `check()` `:129`, `validate(kind, text, *, name=None, source=None)` `:150`. Each
  single-entity read builds the whole `LibraryState` and picks from it.
- **Writes**, one revision each, or none when nothing changes: `put_profile(text, *, decompositions,
  base_version)` `:185`, `put_namespace(text, *, decompositions, base_version)` `:200`,
  `put_decomposition(text, *, use_when, hint, namespaces, top_level, base_version)` `:216`,
  `put_tool(name, text, *, source, granted_in, base_version)` `:245`, `delete(kind, key, *,
  base_version)` `:262` (returns the tombstone), `import_config(path)` `:285`. Every keyword
  defaults to `None`: "leave as it is" for a list, "unconditional" for `base_version`.
- `materialize(dest=None, *, namespace=None, rev=None) -> Path` `:292`.
- Module constants `STARTER`, `ROOT`, `PROFILE` (`:48-50`).

**Records** (`records.py`) are frozen pydantic models; the four entity records carry `yaml` and a
computed `data` (`:23-69`), `HistoryEntry` is one stored version (`:72-86`), `Manifest.versions()`
drops `metadata` (`:136-138`). **Errors** (`records.py:162-232`), unchanged since r1 [read]:

| Error | `error` | Status | Extra payload |
|---|---|---|---|
| `LibraryError` (also `NETWORK_FS`) | `error` | 400 | |
| `LibraryValidationError` | `invalid` | 422 | `errors: [{loc, msg}]` |
| `LibraryNotFound` | `not_found` | 404 | |
| `LibraryConflict` | `conflict` | 409 | `head`: the current record, or `null` |
| `LibraryRefused` | `refused` | 409 | |
| `LibraryImportError` | `import_failed` | 422 | |
| `LibraryForbidden` | `forbidden` | 403 | |
| `LibraryBadRequest` | `bad_request` | 400 | |
| `LibraryNotJson` | `unsupported_media_type` | 415 | |

**The other modules' public names** [read]:
- `store.py`: `SCHEMA_V1` `:25`, `MIGRATIONS` `:66`, `NETWORK_FILESYSTEMS` `:70`, `MOUNTS` `:73`,
  `BUSY_TIMEOUT_MS` `:74`, `Row` `:77`, `filesystem_type` `:104`, `refuse_network_filesystem` `:121`,
  `connect(path, *, mounts)` `:130`, `migrate` `:142`, `create(path, seed)` `:159`, `current_rev`
  `:183`, `heads(conn, *, rev)` `:188`, `history` `:194`, `decomposition_named` `:200`, `read` `:211`,
  `Writer` (`rev`, `head`, `heads`, `add(kind, name, *, yaml, deleted, attached, slug, use_when,
  hint, source)`) `:221-283`, `write(path, action, detail)` `:287`.
- `shapes.py`: `NAMESPACE_NAME`, `SPLIT_KEYS`, `TOOL_DIR`, `YAML_WIDTH`, `FINAL_ANSWER` `:27-33`;
  `canonical_yaml` `:48`; `deep_reasoner_build` `:60`; `Shaped` `:70`; `load_mapping` `:77`;
  `validate_namespace` `:141`, `validate_decomposition` `:155`, `tool_file` `:180`, `validate_tool`
  `:185`, `validate_profile` `:208`; `namespace_config` `:220`; `slug`, D1's, re-exported `:20, 24`.
- `configdir.py`: `MAIN`, `MANIFEST`, `NAMESPACES_DIR` `:20-22`; `ConfigParts` `:26`; `read_config`
  `:113`; `write_config(state, dest, *, namespace)` `:142`.
- `effective.py`: `Sourced`, `SuffixPart`, `EffectiveTool`, `EffectiveDecomposition`, `Effective`
  `:14-47`; `chain` `:50`; `resolved` `:57`; `defined_tools` `:73`; `effective` `:83`.
- `catalog.py`: `LIBRARY_FILE` `:16`; `library_path(home=None)` `:19`; `LibraryCatalog(path)` with
  `snapshot()` `:41` and `materialize(namespace, *, run_dir)` `:67`.
- `api.py`: `Peer`, `JSON_TYPE`, `BODY_METHODS`, `PROC_NET` `:33-36`; `same_user_peer(client,
  server, *, proc_net)` `:50`; `create_app(library, *, same_user=None)` `:195`.
- `cli.py`: `EXIT_ERROR`, `HOST` `:11-12`; `main(argv=None)` `:34`.
- `texts.py`: every user-visible sentence, constants and lower-case functions; v2's table plus
  `bad_base_version` `:123`.

### 3.2 `dr-library`

```text
dr-library serve  --port PORT [--home DIR] [--log-level LEVEL]   uvicorn on 127.0.0.1:PORT
dr-library import PATH [--home DIR]        imported PATH as revision N: A new, B changed, C unchanged
                                           | nothing changed: the library already holds PATH
dr-library export DIR [--home DIR] [--namespace NAME] [--rev N]
                                           wrote DIR/main.yaml: 3 namespaces, 3 decompositions, 0 tools
```

Every subcommand opens the library first, creating it with the starter if it is absent. Exit 0 on
success; 1 for any `LibraryError`, its sentence on stderr; 2 for a usage error (`cli.py:34-81`).
[CI and run: `test_cli.py`'s five tests, among them a real `dr-library serve` with only the six
variables an App backend gets]

### 3.3 HTTP

The routes are design §6.2's table, with no import route (`api.py:321-362`) [read; CI:
`test_every_read_answers_its_records[13 GETs]`, `test_every_write_route`]:

```text
GET /health  GET /problems  POST /validate  GET|PUT /profile  GET /effective  GET /export?namespace=
GET /namespaces       GET|PUT|DELETE /namespaces/{name}     GET /namespaces/{name}/effective
GET /decompositions   GET|PUT|DELETE /decompositions/{slug}
GET /tools            GET|PUT|DELETE /tools/{name}
GET …/versions  GET …/versions/{n}     for /profile, /namespaces/{name}, /decompositions/{slug}, /tools/{name}
```

Every request, `/health` included, passes `_Guard` (`api.py:100-115`, added with
`app.add_middleware` at `:369`) before routing. `_refusal` (`:77-97`) checks, in order: same user
(the default on Linux is `same_user_peer`, `:202-203`; elsewhere no check), then `Host` is
`127.0.0.1:<port>` or `localhost:<port>`, then a `PUT` or `POST` carries `application/json` (a
parameter after `;` allowed). One exception handler maps every `LibraryError` to its payload and
status (`:364-366`). The effective routes answer 422 for a stale head (§2.1 #1).

### 3.4 `dr-acp`

Without `--config`, `dr-acp` builds `LibraryCatalog(library_path(--home))` (`acp/cli.py:87-95`);
with it, D1's `ConfigCatalog`. When `RunSource.versions` has a `library`, the session index's
`source` is `{"kind": "library", "library": <path>}` (`acp/session.py:199-204`). [read; CI and run:
`tests/acp/test_cli.py::test_without_a_config_dr_acp_serves_the_library_at_its_home`,
`tests/library/test_acp.py`]

---

## 4 · Structure and seams

### 4.1 The file: `store.py`

- **Schema.** `SCHEMA_V1` is design §4.2's DDL: `revisions` and `versions` as `STRICT` tables, its
  `CHECK`s, and four triggers that abort any `UPDATE` or `DELETE` (`store.py:25-64`).
  `MIGRATIONS = (SCHEMA_V1,)`; `migrate` reads `user_version`, then per step opens `BEGIN
  IMMEDIATE`, re-reads it, and runs the script plus `PRAGMA user_version` as one `executescript`
  (`:142-156`). [CI: `test_versions_and_revisions_cannot_be_updated_or_deleted[4]`,
  `test_a_migration_that_fails_halfway_leaves_the_file_unmigrated`]
- **`connect`** (`:130-139`) refuses `nfs`, `nfs4`, `cifs`, `smb3`, `smbfs`, `9p` and `fuse.sshfs`
  on Linux (the longest mount point in `/proc/self/mounts` holding the path), then opens in
  autocommit mode with `foreign_keys`, `busy_timeout = 5000`, `synchronous = FULL`, and migrates.
  [CI with a fake mounts file]
- **`create`** (`:159-180`) makes the file 0600 with `O_EXCL` under
  `library.sqlite.<pid>-<8 hex>.new`, switches it to WAL, seeds it and publishes it with `os.link`;
  `False` when another process published first; the temporary file and its `-wal`, `-shm` are
  removed either way. [CI: `test_a_new_library_file_is_private_to_its_user`,
  `test_a_second_creator_loses_and_leaves_nothing_behind`]
- **Writing and reading.** `write()` is `BEGIN IMMEDIATE … COMMIT`, `ROLLBACK` on any exception
  (`:286-296`); `read()` is `BEGIN … ROLLBACK` (`:210-218`). A `Writer`'s first `add` makes the
  revision row (max + 1, UTC to the second); each `add` inserts head + 1, stamped with
  `deep_reasoner_build()` (`0.2.1+d7334ae` here [run]). [CI:
  `test_two_processes_saving_at_once_both_land`, `test_an_exception_inside_a_save_writes_nothing`]
- **What crosses the seam** is `Row`, which is `HistoryEntry`: one version joined to its revision's
  time and action (§2.1 #2). Heads as of revision N are the highest version with `rev <= N` that is
  not a tombstone, in creation order.

### 4.2 One save: `library.py`, where the complexity sits

`library.py` reads in the order a save runs: `Library` (`:53-427`), then the save's helpers
(`:430-553`), the records built from heads (`:556-614`), validation and stale heads (`:617-675`),
and files (`:678-702`). Every write method has one shape [read; run through the suite]:

1. Validate the input with `shapes`, outside any transaction (`:192, 207, 226, 254`).
2. `_save` (`:320-326`) opens `store.write`.
3. `_base` (`:339-358`): `base_version` `0` means not live (`CONFLICT_EXISTS`); `n` means live at
   `n` (`CONFLICT_STALE`, or `LibraryNotFound`). A conflict carries the head's record.
4. `_add` (`:438-449`) writes only if `yaml`, `decompositions`, `slug`, `use_when`, `hint` or
   `source` differs from a live head. `put_decomposition` stores `""` and `None` alike as no
   use-when line or hint (`:236-237`).
5. The cascade. `_attached_set` (`:466-472`), `_top_level` (`:475-479`) and `_granted_set`
   (`:482-490`) share `_toggled` (`:461-463`): append at the end when wanted, remove when not. A
   namespace named in `namespaces=` or `granted_in=` that is not live is 422 with `NOT_FOUND`'s
   sentence at that `loc` (`_live_namespaces`, `:452-458`). Each namespace or profile whose list
   changes gets a version in the same revision; an omitted list keeps the head's.
6. `_read_back` (`:333-337`) builds the record inside the same transaction.
7. On leaving, if anything was written, `_check_invariants` (`:515-545`) runs over every live head:
   profile and `root` live (409 `REFUSE_ROOT`), parents (`PARENT_MISSING`), the default namespace
   (`DEFAULT_MISSING`), unique slugs (`SLUG_TAKEN`), every attached name live and listed once
   (`UNKNOWN_DECOMPOSITION`, `LISTED_TWICE`), the last five 422. Any raise rolls the save back.

`delete` (`:262-283`) resolves a decomposition's slug to its name by a read before the
transaction (`:270`), refuses `root`, the default namespace and a namespace with live children
(`:501-512`), writes a tombstone that keeps the slug, and detaches or ungrants everywhere.

**Stale heads.** `_stale` (`:644-661`) re-validates every live head under the installed
deep_reasoner. `check()` adds a granted tool the Library does not define (`defined_tools`) and a
`spawn` target that is not live. `materialize` refuses every stale head before writing (`:305`);
`effective` refuses them only when its own build fails (`:123-127`). [CI:
`test_a_head_that_stops_validating_is_a_problem_and_blocks_materialize`,
`test_check_reports_ungranted_tools_and_missing_spawn_targets`, and §2.1 #1's test]

### 4.3 Import and materialize: `configdir.py` (no change since `90044f0`)

`read_config` (`:113-135`) loads with D1's `load_dr_config`; the profile is the dump without
`SPLIT_KEYS`; namespaces are `root` (always), then `namespaces_dir`'s, then inline, a later one
replacing an earlier by name (`:45-51`); decompositions are collected by name, top level first, one
name with two bodies `IMPORT_COLLISION`, two names with one slug `SLUG_TAKEN` as `import_failed`
(`:54-81`); a `factory_from` file is read as bytes and renamed `tools/<name>.py` (`:84-100`); a
`library.yaml` beside the config gives use-when lines and hints, ignored silently if it does not
parse (`:103-110`). `Library._import` (`library.py:360-427`) validates every part, then in one
revision writes decompositions (keeping the head's metadata unless the manifest has it), tools,
namespaces in config order, then the profile. [CI: `test_import.py`]

`write_config` (`:142-191`) writes `namespaces/<ns>.yaml` (attached bodies inlined, validated),
`tools/<t>.py`, `library.yaml`, then `main.yaml` last: the profile's data, `entry_namespace` only
when it differs from the profile's default (`:181-182`), `namespaces_dir`, the top-level bodies
and the tool blocks. `Library.materialize` (`library.py:292-316`) refuses a namespace that is not
live, a stale head, and a non-empty `dest`, and undoes a failed write. [CI:
`test_materialize.py`, E7]

### 4.4 Validation and canonical YAML: `shapes.py`

`canonical_yaml` (`:48-56`) is `yaml.dump` with a `SafeDumper` subclass (multi-line strings as
literal blocks, `sort_keys=False`, Unicode kept, width 100) over `model_dump(mode="json",
exclude_unset=True)`. Each kind validates against deep_reasoner's model (`NamespaceConfig`,
`Decomposition`, `V2Config` minus `SPLIT_KEYS`) or, for a tool, a string-keyed mapping, plus the
Library's name and `factory_from` rules; `_shaped` (`:103-126`) turns pydantic's errors and the
rule errors into one `INVALID`. [CI: `test_shapes.py`]

### 4.5 The effective view: `effective.py`

Values are deep_reasoner's `build_namespace_registry(V2Config(profile + every live namespace with
its bodies inlined)).resolve(ns)` (`:57-70`); sources are the Library's walk over the dotted chain
(`:83-129`). [CI: `test_each_inherited_value_names_the_level_it_comes_from[9]`,
`test_effective_values_equal_deep_reasoners_resolve[37 corpus configs]`]

### 4.6 The seam to D1: `LibraryCatalog`

`LibraryCatalog` implements D1's `Catalog` with D1's shapes unchanged; `acp/catalog.py` has no D2
change over main [run: `git diff 32c7f61 0e0a394 -- src/deep_reasoning/acp/catalog.py` is empty].
- Construction stores the path; the first call opens the Library (starter if absent). Building it
  imports nothing of deep_reasoner. [CI: `test_building_a_catalog_imports_nothing_of_deep_reasoner`]
- `snapshot()` (`:41-65`) materializes `state()`'s revision into a temporary directory, takes
  D1's `ConfigCatalog(main).snapshot()`, and on each `CommandEntry` puts the Library's use-when
  line as `description` and its hint as `hint` where it has them. [CI:
  `test_snapshot_equals_config_catalog_over_the_materialized_config_plus_metadata`]
- `materialize(namespace, *, run_dir)` (`:67-83`) writes `run_dir/config/` and returns D1's
  `RunSource` with `versions` replaced by the manifest's. [CI:
  `test_materialize_gives_d1_a_run_source_with_versions`; through `dr-acp`, §11]
- What crosses: the materialized directory, which D1's worker loads as a plain `dr` config, and
  `RunSource.versions`. Menu and run are materialized separately, at `session/new` and at the first
  prompt (design §4.7, "Freshness"). [read]

### 4.7 The App backend: `api.py` and `cli.py`

- `create_app` (`:195-370`): each route is an `async` endpoint that reads the body of a `PUT` or
  `POST`, runs the handler in Starlette's thread pool and sends `to_jsonable_python` of what it
  returns, with 201 or 200 from a `(payload, status)` pair (`route`, `:303-314`). Bodies are
  pydantic models with `extra="forbid"` (`:118-149`), parsed by `_parse` (`:152-158`): 400
  `bad_request` otherwise.
- A `PUT` of a namespace or decomposition checks the path key against the YAML's (`NAME_MISMATCH`,
  400, only when the YAML is valid; `:179-184`); a tool's YAML carries no name, so tools are not
  checked. 201 or 200 is decided by a read before the save, outside its transaction (`:231, 242,
  255`).
- `GET /effective` calls `effective` once per namespace, each its own read (`:338-342`).
  `GET /export` materializes the current revision and zips it under `library/` (`:286-301`).
- `serve` runs uvicorn on 127.0.0.1 (`cli.py:42-52`); the package logs nothing of its own.
  [CI: `test_serve_answers_health_on_loopback`]

---

## 5 · Wiring

- **`pyproject.toml`**: `starlette>=0.40`, `uvicorn>=0.30`, `httpx` (dev), the script `dr-library`,
  and `as_built/` in the sdist's `exclude` beside `docs/`; `requires-python = ">=3.12,<3.13"`, which
  `autocommit=True` needs. [read]
- **D1's files**, +82 −41 over main [run: `git diff --numstat 32c7f61 0e0a394`]: `acp/cli.py` builds
  `LibraryCatalog` without `--config` (`EXIT_USAGE`, `NEEDS_CONFIG` gone); `acp/session.py` writes
  the Library `source`; `acp/texts.py` loses `NEEDS_CONFIG`; `acp/testing/fake_model.py` embeds and
  serves under a plain `with` (§2.1 #9); `tests/acp/harness.dr_acp` takes `config=None`;
  `tests/acp/test_cli.py`'s exit-2 test is now
  `test_without_a_config_dr_acp_serves_the_library_at_its_home`; `tests/acp/test_fake_model.py`
  gains one test.
- **`as_built/`** is outside every build: pytest collects `tests/` only, the wheel packages
  `src/deep_reasoning`, the sdist excludes it, and CI's ruff checks `src` and `tests`; the repo has
  no docs site. [read: `pyproject.toml`, `ci.yml`]
- **CI.** D1's `ci.yml` checks out deep_reasoner_beta at `d7334ae` and sets `DR_BETA_CHECKOUT`, so
  E7 runs; `test_the_corpus_is_read_in_ci` fails if `CI=true` and the corpus is missing. D1's
  `live.yml` runs `pytest -m live`, which includes `tests/library/test_live.py`. [CI]

---

## 6 · Tests, measured

[run: `pytest --collect-only` at `0e0a394` and, in a scratch checkout, at `76d23b2`; CI agrees]

| File | Cases at `0e0a394` | Before |
|---|---|---|
| `test_roundtrip.py` (E7) | 79 | 79 |
| `test_effective.py` | 48 | 48 |
| `test_api.py` | 40 | 40 |
| `test_shapes.py` | 40 | 40 |
| `test_library.py` | 31 | 30 |
| `test_store.py` | 14 | 13 |
| `test_import.py` | 12 | 12 |
| `test_materialize.py` | 10 | 10 |
| `test_catalog.py` | 6 | 8 |
| `test_cli.py` | 5 | 5 |
| `test_acp.py` | 2 | 2 |
| **`tests/library/`, deterministic** | **287** (115 functions) | **287** (116) |
| `test_live.py` (`-m live`) | 1 | 1 |
| D1's `tests/acp/test_fake_model.py` | 4 | 3 |

**What the refactor changed** [run: the test names at both commits, diffed]:
- **Removed (4):** `test_catalog.py::test_commands_carry_use_when_and_hint`,
  `::test_a_top_level_decomposition_is_offered_in_every_namespace`,
  `test_api.py::test_a_slug_with_spaces_in_the_name_round_trips`,
  `test_library.py::test_the_spec_mock_up_runs_as_written`. What still covers each is §9.A.
- **Renamed (2):** `test_effective.py::test_sources` →
  `::test_each_inherited_value_names_the_level_it_comes_from`; `test_shapes.py::test_namespace_names`
  → `::test_a_namespace_name_is_ascii_words_joined_by_single_dots`.
- **Added (4 functions, 5 cases):** `test_store.py::test_a_migration_that_fails_halfway_leaves_the_file_unmigrated`,
  `test_library.py::test_a_namespace_that_is_not_there_cannot_be_attached_to_or_granted_in[namespaces, granted_in]`,
  `test_api.py::test_validate_judges_a_tool_with_the_source_it_is_sent`, and D1's
  `test_fake_model.py::test_embeds_every_input_alike_and_records_only_chat_calls`.
  `test_api.py::test_validate_answers_200_even_when_invalid` now compares the response with
  `Library.validate`'s result instead of a literal.
- **Kept:** both of design §7.3's falsifiers, `test_acp.py::test_a_saved_decomposition_reaches_the_next_conversation_in_its_namespace[saved, edited]`
  (through `dr-acp`, design B14) and the same name in `test_catalog.py` (below its front).

---

## 7 · Proof

| Run | Conditions | Commit | Result |
|---|---|---|---|
| CI [37165314704](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37165314704) | ubuntu-latest, Python 3.12.3, `uv sync --locked`, corpus fetched at `d7334ae`; `ruff check` and `ruff format --check` first | `0e0a394` | 530 collected, 5 deselected, **525 passed** in 253.04 s; `tests/library/` 287 passed, none skipped [CI] |
| live [37166626513](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37166626513) | `workflow_dispatch`, model keys as secrets, `pytest -m live -v -rA` | `0e0a394` | **5 passed**, 397 deselected, 50.80 s: D1's four (three on gpt-6-luna, one Claude Code on Sonnet) and `tests/library/test_live.py::test_an_edited_decomposition_reaches_a_real_run_at_its_saved_version`, 4.0 s after the previous PASSED line [CI] |
| local | this sandbox, `DR_BETA_CHECKOUT=/home/user/deep_reasoner_beta uv run pytest`, load average about 16 from other agents' suites | `0e0a394` | **525 passed**, 5 deselected, 877.46 s; nothing failed, so nothing was rerun. `ruff check src tests`: all checks passed; `ruff format --check`: 79 files formatted; `uv lock --check`: 174 packages resolved, lock current [run] |
| differential probe | the Refactorer's script (`…/scratchpad/d2r/diffprobe.py`), rerun by me at `cd0b60c` (a scratch worktree) and at `0e0a394` (this one) | both | 182 records, 67 of them HTTP responses (every route, the guard, conflicts, refusals, both export zips, stale-head answers), plus Library calls, two materialized directories and every revision and version row of two Libraries: **identical but for one string**, the create revision's `detail`, which is the starter's path in each checkout [run]. The Refactorer's own outputs show the same single difference [read] |

**"Behaviour unchanged"** holds as far as the suite and the probe reach [run]; §9 measures how
much of the behaviour the suite pins. The one behaviour change since r1 is `cd0b60c`'s, before
the refactor (§2.1 #1).

**The Refactorer's claims, checked:**

| Claim | Verdict | Evidence |
|---|---|---|
| Behaviour unchanged | holds, as far as the suite and the probe reach | the probe above; the suite at both ends [run] |
| Non-blank lines added over main: `src/` 2,288 → 2,211, `tests/` 2,234 → 2,161 | holds | §8 [run] |
| 4 tests removed, 2 renamed, 5 added; the B14 falsifier kept | holds, counting cases: the added tests are 4 functions, one parametrized twice | §6 [run] |
| `store.Row` is an alias of `HistoryEntry` | holds | `store.py:77`; `store.Row is HistoryEntry` [run] |
| The store opens with autocommit; migrations use `executescript` | holds | `store.py:133, 152`; `conn.autocommit` is `True` [run]; mutation St1 (§9) |
| D2's fake OpenAI is folded into D1's `FakeOpenAI` | holds | `tests/library/fake_openai.py` is gone; E7, `test_catalog.py` and `test_acp.py` import D1's (§2.1 #9) [read; run through the suite] |
| `cd0b60c` makes the effective views answer 422 for a stale head | holds | its test fails at `802a639` and passes at `0e0a394` [run] |

---

## 8 · Size, before and after

| | r1, `90044f0` | before the refactor, `76d23b2` | `0e0a394` |
|---|---|---|---|
| package, all lines (non-blank) | 2,684 (2,239) | 2,696 (2,249) | **2,598 (2,142)** |
| `tests/library/`, all lines (non-blank) | 2,576 (2,203) | 2,597 (2,222) | **2,495 (2,138)** |
| non-blank lines added over main, `src/` | | 2,288 | **2,211** |
| non-blank lines added over main, `tests/` | | 2,234 | **2,161** |

[run: `git show <rev>:<file> | wc -l` and `grep -cv '^\s*$'` per file; added lines from `git diff
32c7f61 <rev> -- src|tests`. Main has moved to `ed65be6`, which changes only
`docs/deep-reasoner-contract.md`, so either base gives the same counts.] The Refactorer's
2,288 → 2,211 and 2,234 → 2,161 hold, and their sums are the task row's `Lines Before` 4,522 and
`Lines After` 4,372.

By file, before → after: `library.py` 760 → 702, `store.py` 334 → 296, `api.py` 379 → 370,
`shapes.py` 236 → 230, `effective.py` 124 → 129, `records.py` 228 → 232, `texts.py` 217 → 221, the
rest unchanged; `fake_openai.py` 84 → 0, `test_catalog.py` 171 → 144, `test_api.py` 399 → 385,
`test_acp.py` 69 → 65, `test_store.py` 144 → 157, `test_library.py` 384 → 391, `conftest.py`
104 → 109, `test_effective.py` 143 → 145; in D1's files, `fake_model.py` 117 → 143 and
`test_fake_model.py` 68 → 80. `library.py` grew from 748 to 760 between r1 and the refactor with
`cd0b60c`. [run]

---

## 9 · What no test pins: the mutation evidence

**Method** [run]. 66 one-line mutations of D2's code at `0e0a394`, each applied in this worktree,
run, and reverted with `git checkout -- <file>`; the worktree was clean before and after. Stage 1
runs `tests/library/` with `-x`, without E7, the 37-config effective test and `test_acp.py`; a
mutant that passes it then runs those three and D1's `test_cli.py` and `test_fake_model.py`. A
mutant **survives** when both stages pass: no test pins what it broke. The harness and its results
are scratch files, not committed. **53 caught, 13 survived.** None of the 13 breaks something
the four removed tests exercised [read: their bodies, in `c922a02`], so the refactor's cuts
opened none of these gaps.

### 9.A What the four removed tests pinned

| Removed test | Its property | What pins it now | Mutations of the code it pinned |
|---|---|---|---|
| `test_catalog::test_commands_carry_use_when_and_hint` | a menu entry carries the decomposition's use-when line and hint; one without them keeps D1's default description and `the task` | `test_snapshot_equals_config_catalog_over_the_materialized_config_plus_metadata`: the described `decline` entry, and every other entry equal to `ConfigCatalog`'s | R1 use-when dropped, R2 hint dropped, R3 D1's default description lost, R4 `the task` lost (`catalog.py:57-58`): **all caught** by the snapshot test |
| `test_catalog::test_a_top_level_decomposition_is_offered_in_every_namespace` | a top-level decomposition is on every namespace's menu | D1's `ConfigCatalog` test, the snapshot test (`LibraryCatalog`'s menus are `ConfigCatalog`'s over the materialized config), and `test_materialize::test_top_level_decompositions_are_written_into_main` | R5 top-level list not written into `main.yaml` (`configdir.py:184`): **caught** by the last |
| `test_api::test_a_slug_with_spaces_in_the_name_round_trips` | a decomposition whose name has spaces and capitals is written, read and listed at its slug | `test_creating_a_decomposition_answers_201_and_updating_200`, `test_every_read_answers_its_records[/decompositions/catalog-lookup, …/versions]`, `test_library::test_put_then_get_returns_the_canonical_record` | R6 no lookup by slug (`library.py:99`), R7 history not by slug (`:111`), R8 a `PUT`'s path compared with the name (`api.py:182`): **all caught**. Only the capital letters were unique to it, and lower-casing is D1's `slug` |
| `test_library::test_the_spec_mock_up_runs_as_written` | `namespaces()` is root first, then creation order; a save returns its namespaces; `materialize()` makes a new temporary directory | `test_api`'s `/namespaces` read after the same import, `test_put_then_get_returns_the_canonical_record`, `test_without_a_destination_it_writes_a_new_temporary_directory` | R9 namespaces sorted by name (`library.py:571`): **caught** by `test_deleting_a_tool_ungrants_it_everywhere` |

Nothing the four removed tests pinned is left unpinned, as far as R1–R9 reach.

### 9.B Survivors: what no test pins

The last column is read from the code, not run.

| # | Mutation | The property no test pins | What a caller would see |
|---|---|---|---|
| S4 | `hint=hint or None` → `hint=hint` (`library.py:237`) | a hint of `""` stores no hint (design §2.3, §6.2); `use_when`'s twin is pinned | a `PUT` with `"hint": ""` would store and answer `""`, and a later save sending `null` would write a version for nothing |
| S12 | `if head is None:` → `if False:` in `delete` (`library.py:273`) | deleting a namespace or tool that is not live is 404 `NOT_FOUND` | `DELETE /tools/{name}` or `/namespaces/{name}` of a missing one would answer 500 (`AttributeError` on `None.slug`); a decomposition's is resolved first and stays 404 |
| S22 | `decompositions = head.decompositions` → `[]` in `put_profile` (`library.py:196`) | a profile save that omits `decompositions` keeps the top-level list (design §2.3); the namespace's twin is pinned | a `PUT /profile` with only YAML, design §6.4's way to change the namespace new conversations start in, would detach every top-level decomposition |
| H7 | `if same_user is None and sys.platform == "linux":` → `if False:` (`api.py:202`) | the same-user check is on by default on Linux (decision K) | every test passes `same_user` explicitly, and the real `dr-library serve` test connects as the same user, so a server with no peer check passes |
| E2 | `if d.use_when is not None or d.hint is not None` → `if d.use_when is not None` (`configdir.py:175`) | the manifest keeps the hint of a decomposition that has no use-when line | export then import loses that hint; the tests' decompositions have both |
| E3 | `if other != name:` → `if False:` in `_decompositions` (`configdir.py:79`) | two names with one slug inside one imported config are 422 `import_failed`, refused while reading (B3) | the invariant still refuses the import, but as 422 `invalid` from inside the transaction |
| E4 | `rev=state.rev` dropped from the export in `cli.main` (`cli.py:69`) | `dr-library export --rev N` writes revision N | `test_export_at_an_old_revision` checks only the printed line, whose counts come from `state(rev=N)`; the files would be the current revision |
| St2 | `if current < target:` → `if True:` in `migrate` (`store.py:151`) | two processes migrating at once apply a step once | race-only; no test migrates concurrently |
| St7 | `ORDER BY rev DESC` → `ASC` in `decomposition_named` (`store.py:204`) | a slug that two names held, one after the other, finds the later name's history | only after a delete and a re-creation under another name with the same slug |
| A1 | `200 if existed else 201` → `201` in the tool `PUT` (`api.py:263`) | updating a tool answers 200 | no test updates a tool over HTTP; the namespace and decomposition twins are pinned |
| A2 | `if not found:` → `if False:` in the versions route (`api.py:280`) | `GET …/versions/{n}` for a version the entity never had is 404 `NO_VERSION` (B4) | it would answer 500 (`IndexError`) |
| X1 | `if not rows:` → `if False:` in `history` (`library.py:114`) | the history of something the Library never held is 404 `NOT_FOUND` | `GET /tools/nothing/versions` would answer 200 `[]` |
| X4 | `_empty(dest, remove=made)` → `remove=True` (`library.py:314`) | a failed write into a folder that already existed empties it and leaves it (B12) | the user's empty export folder would be removed; the test writes into a new folder only |

### 9.C Caught

| Area | Mutants (all caught) | The first test that failed |
|---|---|---|
| save semantics | S1 every save writes; S2 only the YAML compared; S3 a `""` use-when stored; S13 stale only when behind; S14 `base_version=0` ignored | `test_an_unchanged_save_returns_the_head_and_makes_no_revision`; `test_put_then_get_returns_the_canonical_record`; `test_use_when_and_hint_are_replaced_by_every_save`; `test_a_stale_base_version_is_a_conflict_carrying_the_head`; `test_base_version_zero_refuses_an_existing_entry` |
| cascades | S5 never detach; S6 prepend; S7 an empty `tools:` kept; S8 an unknown namespace ignored; S9 delete leaves the top-level list; S10 delete leaves grants; S11 a tombstone without its slug; S21 an omitted namespace list cleared | `test_namespaces_is_the_exact_set_after_a_save`; `test_attaching_versions_the_namespace_and_appends_in_order`; `test_deleting_a_tool_ungrants_it_everywhere` (S7, S10); `test_a_namespace_that_is_not_there_cannot_be_attached_to_or_granted_in`; `test_deleting_a_decomposition_detaches_it_everywhere` (S9, S11); `test_putting_a_namespace_sets_its_list_only_when_given` |
| invariants and refusals | S15 slugs; S16 listed twice; S17 no invariant check at all; S19 the default namespace deletable | `test_two_names_with_one_slug_are_refused`; `test_putting_a_namespace_sets_its_list_only_when_given` (S16, S17); `test_root_the_default_and_a_parent_cannot_be_deleted` |
| the request guard | H1 no `Host` check; H2 any port; H3 no media-type check; H4 a `charset` refused; H5 `POST` unchecked; H6 no peer check; H8 any uid; H9 the wrong byte order | `test_a_request_addressed_to_another_host_is_refused` (H1, H2); `test_a_body_that_is_not_sent_as_json_is_refused` (H3–H5); `test_another_users_connection_is_refused`; `test_same_user_peer_reads_the_client_sockets_owner` (H8, H9) |
| stale heads | T1 the effective view's refusal; T2 materialize's; T3 a tool's source ignored when re-validating; T4 missing spawn targets; T5 `llm` always defined | `test_a_stale_head_makes_the_effective_view_answer_422_naming_it`; `test_a_head_that_stops_validating_is_a_problem_and_blocks_materialize`; `test_materialized_directory_layout`; `test_check_reports_ungranted_tools_and_missing_spawn_targets` (T4, T5) |
| import and export | E1 v1's `entry_namespace` rule; E5 a tool file read as text; E6 an export's `library.yaml` ignored; E7 tool blocks left out of `main.yaml`; E8 a namespaces directory layered over inline; E9 the top-level list not imported; E10 D1's versions not replaced; S18 import erases use-when lines | **E1 only by E7** (`test_every_config_dr_accepts_round_trips`); `test_factory_from_is_read_into_the_library`; `test_an_exports_library_yaml_keeps_use_when_and_hint`; `test_materialized_directory_layout`; `test_a_new_library_starts_from_the_starter` (E8); `test_one_name_with_one_body_in_two_places_is_one_decomposition`; `test_materialize_gives_d1_a_run_source_with_versions`; `test_import_replaces_what_the_config_names` |
| the store | St1 `isolation_level=None` (`executescript` then commits `migrate`'s `BEGIN IMMEDIATE`, and its `COMMIT` fails with `cannot commit - no transaction is active` [run, in isolation]); St3 a deferred `BEGIN`; St4 no busy timeout; St5 a 0644 file | the first test that opens a library (St1); `test_two_processes_saving_at_once_both_land` (St3, St4); `test_a_new_library_file_is_private_to_its_user` |
| the effective view | F1 `repl`'s source always `profile` | `test_a_repl_set_in_a_namespace_is_its_source` |
| routes | A3 `POST /validate` drops `source` | `test_validate_judges_a_tool_with_the_source_it_is_sent`, as `0e0a394`'s message says |

---

## 10 · What D3 and D4 rely on from D2

Read from their branches' commits, not their worktrees: D3 is `v1-decompositions-panel` at
`a2a8ce3`, D4 is `v1-custom-tools` at `60f1d00` (D3 merged into it). **Both are cut from D2 at
`90044f0`**: neither holds `cd0b60c` or the refactor. References on our side are at `0e0a394`.
[read, all of this section]

**D3** (the Decompositions panel):
- The HTTP contract, every route of `api.py:321-362` and the guard `api.py:77-115`; D3 serves its UI
  from this backend and adds `*ui_routes()` to that route list and two sentences to `texts.py`.
- The effective views' 422 for a stale head: D3's `tests/canvas_app/test_browse.py:165-176` and
  `test_namespaces.py:335-341` plant a stale namespace head and expect its `STALE_HEAD` sentence on
  the page. D2 gives it from `cd0b60c` on (`library.py:118-127, 664-670`); at `90044f0` the route
  raised (§2.1 #1).
- `store.write` and `Writer.add(…, attached=)` to plant that head (D3's `tests/canvas_app/conftest.py:190-200`):
  `store.py:286-296, 241-283`, signatures unchanged by the refactor.
- `Library.open`, `import_config`, `profile`, `put_profile`, `namespace`, `decomposition(s)`,
  `put_decomposition` (`library.py:58, 285, 81, 185, 88, 91-99, 216`); a `PUT` erases an omitted
  use-when line or hint (`library.py:236-237`), so D3 resends both (its `test_browse.py:110, 122`);
  `library_path` (`catalog.py:19-22`); `tests/library/conftest.py`'s `example` and `text` (`:14, 33`).

**D4** (custom tools and MCP grants):
- `shapes.validate_tool` (`shapes.py:185-205`), `Shaped.yaml` and `.data` (`:69-74`), `TOOL_DIR`
  and `tool_file` (`:31, 180-182`), `canonical_yaml` (`:48-56`), `deep_reasoner_build` (`:59-66`).
- `records`: `FieldError`, `LibraryError`, `LibraryValidationError`, `LibraryRefused`,
  `LibraryBadRequest`, `ToolRecord` (`records.py:141, 162, 174, 206, 225, 60`).
- `Library.state().tools`, `tools()`, `put_tool(…, source=, granted_in=)` with its grant cascade
  (`library.py:73-79, 101, 245-260, 482-498`), and materialize writing `tools/<name>.py` beside
  `main.yaml` (`configdir.py:156-162`).
- **`api.py`'s insides, which D4 edits:** `_parse` (`api.py:152-158`; D4 adds a sentence
  parameter), `_ToolBody` (`:138-140`; D4 adds `accept_check_failure`), the `put_tool` handler
  (`:253-263`; D4 runs its Check before the save), and the route closure `route` (`:303-314`),
  which D4 lifts to a module-level `json_route` that calls `_dump`. **`452db0e` removed `_dump`**
  (§2.1 #8), so D4's edit and the refactor change the same lines of `api.py`.
- `tests/library/conftest.py`'s `ROUTER`, `write_config` and `run_dr` (`:54, 42, 91`).

---

## 11 · Experiments, as measured

- **E7, round-trip** (design §7.1; `test_roundtrip.py`). Level 1: 39 corpus files at `d7334ae`
  plus the composed `configs/example` + `namespaces/`; the 37 configs and the composed one
  round-trip, the 2 namespace files are refused as asserted. Level 2: `dr` on each original and its
  copy against `FakeOpenAI`, deep_reasoner's fake Claude CLI and no network gives equal exit codes,
  last lines and first requests on all 38; the guard sets pin 19 that answer `done` and the 2
  Claude-backbone configs. **79 of 79 passed** in CI 37165314704 and locally at `0e0a394` [CI;
  run]. The per-config breakdown (19 answer, 2 end at the fake CLI, 17 exit 1 alike on both
  sides) is r1's, measured at `90044f0`; I did not re-measure it.
- **D3's falsifier at the store** (design §7.3): through `dr-acp` with no `--config`, a saved
  decomposition is on the menu with its use-when line, `run.start` records the namespace and its
  saved version (1, or 2 after an edit), the model is sent that version's text and not the other's,
  and the session index names the Library; the same below the front with `LibraryCatalog` and `dr`.
  **Passed** [CI; run].
- **Live tier** (design §7.4; gpt-6-luna): import D1's advising config, save then edit `first
  course` (history v2, v1), refuse the spec's failure cell without a revision, materialize
  (`first course: 2`) and run `dr`: exit 0, the answer names CS101, the root's node log carries v2's
  example only. **Passed** in live run 37166626513 at `0e0a394` [CI]. The log does not record its
  token cost.

---

## 12 · What I could not verify

1. **The `Host` guard behind the agent-server.** Design v2 (B1, §8 B6) cites the SDK fork's bridge
   and D3's replica of it for `Host: 127.0.0.1:<port>`. I read neither and ran no bridge; nothing
   in this suite goes through one.
2. **The same-user check against another real OS user**: only a fake `/proc/net` refuses; and the
   default wiring on Linux, see §9.B (H7).
3. **`NETWORK_FS` on a real network mount**; nothing ran on macOS (no peer or mount check there, by
   design).
4. **Concurrency** beyond `test_two_processes_saving_at_once_both_land`: two processes migrating at
   once, two concurrent creates of one key (both can answer 201), and `GET /effective`'s
   per-namespace reads were read, not run.
5. **The freshness path** (design §4.7): a command whose decomposition is deleted between
   `session/new` and the first prompt has no test and was not run.
6. **A real pin bump.** Stale heads are tested with a monkeypatched stricter model and with a row
   written through the store, never with another deep_reasoner.
7. **D3's and D4's suites on `0e0a394`** were not run (§10); the `api.py` overlap with D4 is read.
8. **E7's per-config outcomes** at `0e0a394` (§11); and the live tier's token cost.
9. The Refactorer's "5 added" holds counting cases (one added test runs twice); counting
   functions it is 4 (§6).
