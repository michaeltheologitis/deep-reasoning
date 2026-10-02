# D2 · Library store — design

**TASK-5** · System Designer · branch `v1-library-store` · against the approved spec
[TASK-1](https://app.notion.com/p/3ed62fb22237814ab425c81b3844f012) (D2 in full, §2, the parts of
D3, D4 and §4 that use the store; save-a-run is out of v1) and D1's design v2
(`f281109:docs/design/d1-dr-acp.md`, §4.4 and §4.6, the seam this design implements).
**Pinned against:** deep_reasoner_beta `d7334ae6ea884617a377d9f1ce872530d898484c` (conflit 0.1.4,
pydantic 2.13.5 as its lock resolves them) · D1's committed `src/deep_reasoning/acp/catalog.py` at
`21c2c7a` (identical to D1 §4.6) · the SDK fork at `91430aa` (upstream `53a4bc5` plus the ASE commit;
the Canvas App backend manager and bridge line numbers below) · SQLite 3.45 (the stdlib's; `STRICT` tables need 3.37 or later).

**Revisions** (newest first; each line says which sentences to stop trusting):
- 2026-10-02 · v1 · first full-depth version.

**Where this file lives, and why nothing trips over it.** `docs/design/` on the task branch. The
repo has no docs site; once D1's `pyproject.toml` is on the branch, pytest collects `tests/` only
(`testpaths = ["tests"]`), the wheel is built from `src/deep_reasoning` only, the sdist excludes
`docs/`, and ruff excludes `docs` (D1 §8.5). The PR split leaves it behind.

**Reading guide.** Gate B: §1 to §3 (what the Library is, what a row is, where this departs from
the spec). D3 and D4 design against §6, which is their contract, and §2, which says what the
records mean. D1's Implementer reads §4.7. D5 reads §4.8 and §4.6 (the command, the export).
The Implementer reads everything; Appendix A indexes every signature.

**What was verified for this design (2026-10-02, in a scratch environment outside every repo):**
a 150-line prototype of import, canonical YAML and materialize, run over every YAML file in
deep_reasoner_beta's `docs/configs` and `configs` at `d7334ae`: every file `dr` accepts as a config
round-trips (equal `V2Config`, equal `registry.resolve(ns)` for every namespace, idempotent
re-import), and `dr` run against a fake OpenAI endpoint behaves identically on each original and
its materialized copy (same exit code, same answer, same first model request). Details in §7.1.

---

## 1 · What the Library is

One SQLite file per user, `$DR_HOME/library.sqlite`, holding that user's **namespaces,
decompositions, tools and one profile** as canonical YAML in deep_reasoner's own shapes. Every save
is a new immutable **version** of each entity it changes, stamped with a library-wide
**revision** number. Two kinds of process use the file, and both treat it as the only state:

- **The App backend** (`dr-library serve`, started by the agent-server for the Decompositions
  panel, D3) serves the HTTP API of §6. It is the only process that writes during normal use.
- **Each `dr-acp`** (D1) reads it in-process through `LibraryCatalog`: the namespaces and their
  slash commands at `session/new`, and, at a conversation's first prompt, a **materialized** plain
  `dr` config directory in the run's own folder, which the worker loads with `load_cli_config`
  exactly as `dr` would.

Import reads any plain `dr` config into the Library; materialize writes the Library (or any past
revision of it) back out as one. Export is materialize into a folder the user names.

```text
Canvas (D3's panel) ──HTTP via the agent-server bridge── dr-library serve (App backend, D2)
                                                               │ writes (one revision per save)
dr-library import / export (the user, D5's dr-app) ────────────┤
                                                               ▼
                                        $DR_HOME/library.sqlite   (WAL, 0600)
                                                               ▲ reads (one revision, consistent)
dr-acp front (D1), per conversation ── LibraryCatalog ─────────┘
   session/new:   snapshot()  → namespaces, default, commands per namespace
   first prompt:  materialize(namespace, run_dir) → $DR_HOME/runs/<run>/config/
                                                     main.yaml
                                                     namespaces/<name>.yaml
                                                     tools/<name>.py
                                                     library.yaml   (manifest: rev and versions)
   worker:        load_cli_config(runs/<run>/config/main.yaml, schema=V2Config) → the run
```

### 1.1 Decisions this design takes (the spec's decision 6 stands; these are the next layer down)

| # | Decision | Why | Rejected |
|---|---|---|---|
| A | **One `versions` table for all four kinds, one `revisions` table as the clock.** A save opens one transaction, gets the next revision number, and inserts one version row per entity it changes. SQLite triggers refuse every `UPDATE` and `DELETE` on both tables. | "Every save an immutable version" is enforced by the database, not by our care. A run records one number (the revision) that reproduces exactly what it was built from; history, heads and "as of revision N" are one query each for every kind. | A table per kind (four copies of the version logic). Mutable rows plus an audit log (the log and the rows can disagree). |
| B | **Attachments are an ordered list of decomposition names on the namespace's version** (and, for top-level decompositions, on the profile's). A decomposition's `namespaces` is derived. | Order is part of what an agent sees: it is the order of the worked examples in its prompt and the order `resolve()` returns. A namespace's version then pins everything about the namespace except the decomposition bodies, which their own versions pin. | Attachments on the decomposition's version (no order; reproducing a run needs the attachment history of every decomposition). A free-standing link table (a third kind of versioned thing). |
| C | **A decomposition's identity is its deep_reasoner `name`, unique in the Library; its slug (D1's rule) must be unique too, and is its address in every URL.** | The name is what deep_reasoner resolves (child wins by name) and what `main_decomposition_turns` looks up. The slug is the slash command (D1 §4.6) and is the only key that crosses the agent-server bridge intact (§6.1). Making it unique means a Library decomposition always gets the slash command `/<slug>` with no collision suffix. | Library-generated ids (a second identity, and two same-named decompositions in one chain would silently shadow each other). Raw names in URLs (the bridge decodes the path and re-sends it; `?`, `#` and `%` break). |
| D | **The profile is the whole rest of a `dr` config**: every key except `namespaces`, `namespaces_dir`, `decompositions`, `tools` and `config_path`. `entry_namespace` in it is "the namespace new conversations start in". | E7 round-trips every config, so `client`, `llm_kwargs`, `prompt_template_variables`, `example_fence`, extras such as `description` all have to live somewhere. The spec's seven run settings are what D3 edits. | A profile with only the seven named settings (configs that set `client` or `llm_kwargs` stop round-tripping, which is every config in the corpus). |
| E | **Canonical YAML**: deep_reasoner's model, validated, dumped with `exclude_unset=True` in the model's own field order, block style, strings containing a newline as literal blocks (`\|`), Unicode kept, width 100. | Deterministic, so "unchanged" is text equality and a re-import makes no revision. It keeps exactly the keys the author set, never deep_reasoner's defaults (which may change with a pin bump). Code blocks in decompositions stay readable. | Storing the author's text verbatim (two spellings of one config are two versions; after a form edit the comments would be stale). JSON (unreadable code blocks; the spec says YAML). |
| F | **One writer for materialize and export**: `main.yaml` + `namespaces/<name>.yaml` (decompositions inlined in attachment order) + `tools/<name>.py` + `library.yaml` (a manifest `dr` never reads). | A per-namespace file reads well in an export; the layout is what `dr`'s own `namespaces_dir` loads; one writer cannot drift from itself. Verified to load and behave identically under `dr` (§7.1). | Everything inline in one `main.yaml` (an export nobody wants to read); a second writer for export. |
| G | **Import merges by name, in one revision, and never deletes.** Each entity whose canonical form differs from the head gets a version; equal ones are left alone; nothing absent from the imported config is touched. | Importing a second config must not destroy the first's namespaces. Re-importing the same config makes no revision. Anything an import overwrote is one version back. | Import as "replace the Library" (one wrong click loses everything). Import into a fresh file only (no way to bring a config into an existing Library). |
| H | **`dr-acp` reads the file in-process; `LibraryCatalog` materializes and then delegates to D1's own `ConfigCatalog`** for the snapshot and the `RunSource`, adding only the use-when line, the hint and the versions. | The menu is computed by D1's code from the very config the run will load, so the slash menu and the run cannot disagree, and D1's menu rules (order, slugs, first name wins) are not copied. The App backend's port is assigned by the agent-server and known to nothing else. | `dr-acp` calling the HTTP API (spec §2 draws it that way; it has no way to find the port). Re-implementing D1's menu over rows. |
| I | **WAL mode, `BEGIN IMMEDIATE` per save, a fresh connection per operation.** | The App backend, every `dr-acp` and `dr-library import` share one file; writers serialize, readers see one consistent revision and never block a writer. Starlette runs sync endpoints on a thread pool, and a connection per call needs no locking of ours. | A long-lived connection with a lock; a server process owning the file (a second service, the thing spec §2 rejected). |
| J | **Validation is deep_reasoner's own models at every save, and again over every head at every materialize**, under the installed deep_reasoner. A head that stops validating after a pin bump is a named problem (`GET /problems`) and blocks materialize; it is never rewritten silently. | The spec's "stored YAML records the commit it was validated against and the importer migrates it": the record is kept per version; a migration can only be written once Dean's change exists, and E7 on the new pin is what shows one is needed. | Re-validating only at save (a pin bump would surface as a failed run). Silent best-effort rewriting. |
| K | **The HTTP API has no import, and on Linux refuses a TCP peer that belongs to another OS user.** It binds 127.0.0.1 only. | A Canvas App backend is unauthenticated loopback HTTP: the agent-server's bridge authenticates the browser, but anything on the machine can reach the port directly. On a shared lab machine another user could otherwise write a tool (code that runs as you at your next conversation) or make the backend import a config whose `factory_from` names your private files. Import stays a command the user runs. | Trusting loopback. A token we cannot deliver: the bridge sends the backend no credential (§8, B4). |
| L | **Optimistic concurrency.** Every write may carry `base_version`, the head version the edit started from (`0`: must not exist yet); a mismatch is a conflict that carries the current head. | Two conversations can have the panel open at once; D3's "'catalog lookup' is already in router (v2)" needs the head. Scripts and import omit it and write unconditionally. | Locks held by a panel. Last write wins silently. |
| M | **A new Library starts from a starter config shipped in the package**, imported through the same import path as any config: a `root` namespace with the `llm` tool and a profile with a model, a client and a short system prompt of our own. | Spec §1's first "done when" (install, ask) needs a Library that can run before the user has written anything. One code path: the starter is just the first import. | An empty Library (the first question fails with "LLM requires a model"). Seeding in D5's setup (every test and every `dr-acp --home` would need the same seeding). |

### 1.2 What D2 owns, and its seams

- **Owns:** the `deep_reasoning.library` package; the `dr-library` command (`serve`, `import`,
  `export`); the SQLite schema and its migrations; import; materialize and export; the HTTP API;
  `LibraryCatalog`; the effective (inherited) view D3's Namespaces tab shows; E7.
- **Seam to D1** (§4.7): implements D1's `Catalog` protocol unchanged. D1 §4.6 already says
  "nothing in D1 changes when D2 lands except the default in `cli.py`"; D2 makes that change
  (`dr-acp` without `--config` uses the Library at `--home`). **No change to the Catalog seam is
  needed.**
- **Seam to D3** (§6): the HTTP API, including validation without saving and the effective view,
  because D3 has no Python (spec D3's cost: "No Python").
- **Seam to D4** (§6.5): tool rows (the `tools.<name>` block plus the Python source),
  `granted_in` on a tool save, materialized `tools/<name>.py`, and the migration list for any
  table D4 adds. Check (building a tool in a throwaway process) is D4's.
- **Seam to D5** (§4.8): `dr-library serve --port PORT --home DIR` is the App backend's command;
  `dr-library export DIR` prints the line D5's mock-up shows; the Library path is
  `<home>/library.sqlite` with D1's home resolution; the starter's model and provider are
  provisional (§9).

---

## 2 · The model: what a row is

### 2.1 Four kinds

| Kind | Key | Its canonical YAML is a valid… | Beside the YAML (columns, never YAML keys) |
|---|---|---|---|
| `profile` | the one row `profile` | `V2Config` with the split-out keys absent (decision D) | `attached`: the top-level decompositions, in order |
| `namespace` | its dotted name | `NamespaceConfig` without `decompositions` | `attached`: its decompositions, in prompt order |
| `decomposition` | its deep_reasoner `name` | `Decomposition` | `slug` (derived), `use_when`, `hint` |
| `tool` | its name (a Python identifier: it is bound in the REPL under it) | `tools.<name>` block: a mapping, as `make_tools` reads it | `source`: the Python file, for a tool with `factory_from` |

Every version row also records the revision that wrote it, whether it is a deletion (a tombstone:
no YAML), and the deep_reasoner build that validated it (`0.2.1+d7334ae`). Times live on the
revision.

**Why decompositions are their own rows.** The spec attaches one decomposition to several
namespaces and versions it on its own ("Saved 'rank by prerequisites' v1 in course_advisor"). A
namespace's YAML therefore carries no `decompositions:`; the materializer inlines the attached
bodies into each namespace's file, in the namespace's order, so the directory `dr` loads is plain.

**Top-level decompositions.** A `dr` config's own `decompositions:` list is not shown to any agent
as an example: with a namespace registry (which `dr` always builds), an agent's examples are its
resolved namespace's decompositions only (`v2/agent.py:673, 991`); the top-level list is only
searched, first, when a run opens with a decomposition (`build_reasoner`, `v2/cli.py:350–356`).
D1 offers those in every namespace's menu, ahead of the namespace's own (D1 §4.6). The Library keeps
the list on the profile (`attached`), so a decomposition can be top-level, attached to namespaces,
or both, and a config with a top-level list round-trips.

### 2.2 Canonical YAML

```python
canonical_yaml(model.model_dump(mode="json", exclude_unset=True))
```

where `canonical_yaml` is `yaml.dump` with a `SafeDumper` subclass that represents a string
containing `"\n"` in literal block style, `sort_keys=False`, `allow_unicode=True`,
`default_flow_style=False`, `width=100`. Properties the tests pin (§7.2): equal models give equal
text; `canonical(load(canonical(x))) == canonical(x)`; any YAML spelling of the same model gives the
same text (flow or block, quoted or plain, key order); and JSON text, which is YAML, is accepted, so
D3 can send `JSON.stringify(data)`.

The cost of this, said once: **comments, anchors and `_compose` structure are not kept.** An
imported config is stored as its composed result; an export is flat. deep_reasoner_beta's configs
are heavily commented; their exports will not be.

### 2.3 Attachments

- A namespace's `attached` list is the order its decompositions appear in its agents' prompts.
  `put_namespace(..., decompositions=[...])` sets it; saving a decomposition with `namespaces=[...]`
  appends it to each newly named namespace's list (at the end) and removes it from each namespace no
  longer named. Every namespace whose list changes gets a new version, in the same revision.
- The profile's `attached` list is the top-level list, set the same two ways (`top_level=True`).
- Deleting a decomposition removes it from every list (new versions of those namespaces and of the
  profile, same revision). Deleting a tool removes its name from every namespace's `tools`.
- **Attachment lists are left as they are when a save omits them; everything else a save sends
  replaces what was there** (the YAML, the use-when line, the hint, a tool's source). One rule for
  every kind and every write.

### 2.4 Versions and revisions

- A **revision** is one save: one transaction, one row in `revisions` (`rev`, time, action,
  detail), created only when the save actually changes something. Revisions number the whole
  Library, 1, 2, 3, …
- A **version** is one entity's state as of one revision: `(kind, name, version)` with `version`
  counting from 1 per entity and never reused, so a deleted and re-created decomposition continues
  at the next number.
- The **head** of an entity is its highest version; it is **live** unless that version is a
  tombstone. "The Library as of revision N" is every entity's highest version with `rev <= N`.
- Every materialized directory carries a manifest (`library.yaml`) with the revision and the
  version of every entity it contains; `LibraryCatalog` hands the same to D1 as
  `RunSource.versions`, which D1 records in `run.start.source.versions` (D1 §4.4). So "each run
  records the exact versions it used" holds, and `materialize(rev=N)` rebuilds that run's config.

### 2.5 Invariants (checked inside every write transaction; a write that breaks one is rolled back)

1. The profile and the `root` namespace are live.
2. Every live namespace's parent is live (`a.b` needs `a`; a top-level name needs `root`).
3. The profile's default namespace (`entry_namespace`, else `root`) is live.
4. Live decompositions have distinct names and distinct slugs.
5. Every name in an `attached` list is a live decomposition, at most once per list.
6. Every new version validates under the installed deep_reasoner (its kind's model, plus the name
   rules of §4.3).

What is **not** an invariant, because deep_reasoner decides it when an agent runs: a namespace
granting a tool the Library does not define, and a `spawn` naming a namespace that is not there.
Both are reported by `check()` as problems (§4.5).

### 2.6 A worked example

A fresh Library opened with `starter=False` holds revision 1: `profile` v1 (`{}`) and `root` v1
(`name: root`). Importing deep_reasoner_beta's `docs/configs/catalog/advisors.yaml` (verified shapes,
§7.1) makes revision 2:

| kind | name | v | rev | canonical YAML (abridged) | attached |
|---|---|---|---|---|---|
| profile | profile | 2 | 2 | `model: qwen/qwen3.6-flash` · `llm_kwargs: {stop: [</repl>]}` · `system_prompt: \|` … · `max_iter: 20` · `client: {base_url: …, api_key_env: …}` · `log_dir: logs` · `entry_namespace: router` | — |
| namespace | root | 2 | 2 | `name: root` · `tools: [llm]` | — |
| namespace | router | 1 | 2 | `name: router` · `spawn: [course_advisor, health_advisor]` | route a course question, route a wellbeing question, decline anything else |
| namespace | course_advisor | 1 | 2 | `name: course_advisor` · `vars: {catalog: …}` | catalog lookup |
| namespace | health_advisor | 1 | 2 | `name: health_advisor` | answer then sanitize |
| decomposition | catalog lookup (`catalog-lookup`) | 1 | 2 | `name: catalog lookup` · `messages:` … | — |
| … four more decompositions, v1 at rev 2 | | | | | |

`[ns.name for ns in lib.namespaces()]` is `['root', 'router', 'course_advisor', 'health_advisor']`:
root first, then in creation order, which for one import is the config's order (the spec's mock-up).

D3's Create decomposition then saves "summarize then rank" into `router`: revision 3 holds
`summarize then rank` v1 and `router` v2 (its list with the new name appended). The next
conversation in `router` materializes revision 3; its manifest says
`{rev: 3, profile: 2, namespaces: {root: 2, router: 2, course_advisor: 1, health_advisor: 1},
decompositions: {summarize then rank: 1, …}}`, and D1 records that in the run log.

---

## 3 · Where this design departs from, or adds to, the approved spec

Each is a refinement inside D2's scope, not a re-scope. If the Conductor reads any as a change of
what was approved, it goes back to Michael.

1. **The profile holds the whole rest of a config** (decision D), not only the seven settings the
   spec lists (`model`, `models`, `reasoner`, `system_prompt`, `max_iter`, `max_depth`, `repl`) and
   the default namespace. Without it E7 fails on every config (all of them set `client` or
   `llm_kwargs`). The seven are what D3 edits; the default namespace is the profile's
   `entry_namespace`.
2. **Top-level decompositions** are kept as the profile's ordered list (§2.1). The spec's model has
   only namespace attachments; configs with a top-level list (`configs/example/main.yaml`,
   `docs/configs/incidents/triage.yaml`, …) would not round-trip, and D1 offers that list in every
   namespace.
3. **Attachments are ordered lists on namespace versions** (decision B). The mock-up's
   `d.namespaces` exists, derived; saving a decomposition with `namespaces=` versions the
   namespaces it changes.
4. **Decompositions are addressed by slug in URLs, and slugs are unique** (decision C):
   `PUT /decompositions/{slug}`, not `/{name}`. A name whose slug another decomposition already has
   is refused with a sentence that says which.
5. **A `hint` column beside `use_when`.** S2's and C2's mock-ups show a per-decomposition hint
   (`‹what to compare›`); D1's `CommandEntry.hint` takes it, defaulting to "the task".
6. **HTTP bodies are JSON carrying the YAML as a string** (`{"yaml": "...", "use_when": "..."}`),
   not a YAML body with query parameters; a create answers 201 with the record, an update 200.
7. **`dr-acp` reads the Library in-process, not over HTTP** (decision H). Spec D2 says "an HTTP API
   serves the Library tab and `dr-acp`"; D1's design already fixed the in-process `Catalog`, and
   `dr-acp` cannot learn the App backend's port.
8. **"The importer migrates" becomes "every materialize re-validates, and a stale head is a named
   problem"** (decision J). Each version records the deep_reasoner build that validated it; the
   migration code for a given format change is written with the pin bump that needs it.
9. **A library-wide revision number** (decision A). Runs record the revision and every entity's
   version; every materialized directory carries the same as `library.yaml`.
10. **Comments and `_compose` structure are not kept** (§2.2): a consequence of the spec's
    decision 6 (canonical YAML), said here because a user exporting will notice.
11. **Import semantics: merge by name, never delete** (decision G), and it accepts an export's
    `library.yaml` so export then import keeps the use-when lines and hints.
12. **No HTTP import; a same-user check on Linux** (decision K).
13. **The effective view, validation without saving, and the problem list are D2 endpoints**
    (§6). D3 needs them and has no Python; resolution must be deep_reasoner's own.
14. **A starter Library** (decision M), with a provisional model and provider (§9 item 2).
15. **`$DR_HOME` on a network filesystem is refused** (§4.2): SQLite's WAL mode is unsafe there,
    and Linux lab machines often mount home directories over NFS.
16. **Cost.** About 1.1k LOC of code and 0.8k of tests, roughly 6 h at Gate C, against the
    spec's ≈1.2k LOC with tests and ≈4 h. The growth is items 2, 3, 12 and 13 (the effective view
    and validation were nobody's: D3 has no Python), and the invariants of §2.5.

---

## 4 · Modules

### 4.1 Package layout

```text
src/deep_reasoning/library/
    __init__.py      Library, LibraryCatalog, the records and errors (re-exports)
    store.py         SQLite: schema and migrations, connections, the writer, heads, history
    shapes.py        deep_reasoner's models, canonical YAML, name rules, slug, the build string
    records.py       ProfileRecord, NamespaceRecord, DecompositionRecord, ToolRecord, HistoryEntry,
                     LibraryState, ImportReport, Manifest, Problem, ValidationResult, errors
    library.py       Library: the Python API (reads, writes, import, materialize, check)
    configdir.py     read_config (a dr config → parts) and write_config (a state → a directory)
    effective.py     inherited values and their sources (D3's Namespaces tab)
    catalog.py       LibraryCatalog: D1's Catalog over the Library
    api.py           the Starlette app (§6), the same-user peer check
    cli.py           dr-library serve | import | export
    texts.py         every user-visible sentence (§4.10), in one place
    starter.yaml     a new Library's first import
tests/library/…      §7
```

deep_reasoner is imported at module level by `shapes.py`, `configdir.py`, `effective.py` and
`library.py`. `catalog.py` imports nothing of deep_reasoner or of the Library at module level, so
`dr-acp`'s start-up, which builds the catalog before it serves (D1 §4.2), stays as cheap as with
`ConfigCatalog`; the first `snapshot()` (in a thread) pays the import (≈1.4 s measured for
`deep_reasoner.v2.cli`). Importing deep_reasoner writes nothing to stdout (D1's R16).

### 4.2 `store.py`: the file

**Opening.** `connect(path)` returns a `sqlite3.Connection` with `row_factory = sqlite3.Row`,
`PRAGMA foreign_keys = ON`, `PRAGMA busy_timeout = 5000`, `PRAGMA synchronous = FULL`.
`migrate(conn)` applies `MIGRATIONS[user_version:]` in one transaction each and sets
`user_version`; D4 appends to `MIGRATIONS` if it needs a table.

**Creating** a library is atomic, because the App backend and a `dr-acp` may both find the file
missing at the same moment. `create(path, seed)` makes the parent directory (mode 0700) if missing;
builds the whole file under a temporary name beside it (`library.sqlite.<pid>.new`, created with
`os.open(…, O_CREAT | O_EXCL | O_WRONLY, 0o600)` before SQLite touches it, since SQLite gives
`-wal` and `-shm` the database file's permissions): schema and `PRAGMA journal_mode = WAL`
(persistent in the file), then `seed(temporary)`, which writes revision 1 through the ordinary
writer; once the last connection to it is closed (which checkpoints and removes its `-wal`), it
publishes it with `os.link(temporary, path)`, which fails if another
process published first, and removes the temporary name either way. The loser opens the winner's
file. No process ever sees a library without revision 1.

**Refused locations (Linux).** Before connecting, the filesystem type of the file's directory is
read from `/proc/self/mounts` (the longest mount point that is a prefix of the resolved path); for
`nfs`, `nfs4`, `cifs`, `smb3`, `smbfs`, `9p`, `fuse.sshfs` `open` raises `LibraryError`
(`NETWORK_FS`). SQLite's WAL mode needs shared memory that network filesystems do not provide
(sqlite.org/wal.html, "WAL does not work over a network filesystem"). No check on macOS, whose
homes are local.

**Schema, version 1:**

```sql
CREATE TABLE revisions (
    rev INTEGER PRIMARY KEY,
    at TEXT NOT NULL,                -- UTC, ISO 8601, "2026-10-02T14:22:31Z"
    action TEXT NOT NULL,            -- "create", "import", "put namespace", "delete tool", …
    detail TEXT                      -- the imported path, the decomposition's name, …
) STRICT;

CREATE TABLE versions (
    kind TEXT NOT NULL CHECK (kind IN ('profile', 'namespace', 'decomposition', 'tool')),
    name TEXT NOT NULL,              -- 'profile' for the profile
    version INTEGER NOT NULL CHECK (version >= 1),
    rev INTEGER NOT NULL REFERENCES revisions (rev),
    deleted INTEGER NOT NULL DEFAULT 0 CHECK (deleted IN (0, 1)),
    yaml TEXT,                       -- canonical YAML; NULL exactly when deleted
    attached TEXT,                   -- JSON array of decomposition names: profile, namespace
    slug TEXT,                       -- decomposition (kept on its tombstone)
    use_when TEXT,                   -- decomposition
    hint TEXT,                       -- decomposition
    source TEXT,                     -- tool: the factory_from file
    deep_reasoner TEXT NOT NULL,     -- the build that validated this version
    PRIMARY KEY (kind, name, version),
    CHECK ((deleted = 1) = (yaml IS NULL)),
    CHECK (kind <> 'profile' OR name = 'profile'),
    CHECK (kind IN ('profile', 'namespace') OR attached IS NULL),
    CHECK (kind = 'decomposition' OR (slug IS NULL AND use_when IS NULL AND hint IS NULL)),
    CHECK (kind = 'tool' OR source IS NULL)
) STRICT;

CREATE INDEX versions_rev ON versions (rev);

CREATE TRIGGER versions_no_update BEFORE UPDATE ON versions
BEGIN SELECT RAISE(ABORT, 'library versions are immutable'); END;
CREATE TRIGGER versions_no_delete BEFORE DELETE ON versions
BEGIN SELECT RAISE(ABORT, 'library versions are immutable'); END;
CREATE TRIGGER revisions_no_update BEFORE UPDATE ON revisions
BEGIN SELECT RAISE(ABORT, 'library revisions are immutable'); END;
CREATE TRIGGER revisions_no_delete BEFORE DELETE ON revisions
BEGIN SELECT RAISE(ABORT, 'library revisions are immutable'); END;
```

**Heads as of a revision** (`:rev` is the current revision when not given):

```sql
SELECT v.*, r.at, r.action,
       (SELECT w.rev FROM versions AS w
         WHERE w.kind = v.kind AND w.name = v.name AND w.version = 1) AS created_rev
  FROM versions AS v JOIN revisions AS r USING (rev)
 WHERE v.version = (SELECT MAX(w.version) FROM versions AS w
                     WHERE w.kind = v.kind AND w.name = v.name AND w.rev <= :rev)
   AND v.deleted = 0
```

**Writing.** A save is `with store.write(path, action, detail) as w:`, which opens a connection,
runs `BEGIN IMMEDIATE` (the busy timeout waits out another writer), and yields a `Writer`.
`Writer.add(...)` inserts a version at `head.version + 1` (or 1), creating the `revisions` row on
its first call, so a save that changes nothing makes no revision. On normal exit the library checks
the invariants of §2.5 against `w.heads()` and commits; any exception rolls back.

```python
Kind = Literal["profile", "namespace", "decomposition", "tool"]

MIGRATIONS: tuple[str, ...]  # MIGRATIONS[i] takes user_version i to i + 1; (SCHEMA_V1,)

NETWORK_FILESYSTEMS: frozenset[str] = frozenset(
    {"nfs", "nfs4", "cifs", "smb3", "smbfs", "9p", "fuse.sshfs"}
)


@dataclass(frozen=True)
class Row:
    kind: Kind
    name: str
    version: int
    rev: int
    at: datetime  # the revision's time, UTC
    action: str  # the revision's action
    created_rev: int  # the revision of version 1: creation order
    deleted: bool
    yaml: str | None
    attached: list[str] | None
    slug: str | None
    use_when: str | None
    hint: str | None
    source: str | None
    deep_reasoner: str


def create(path: Path, seed: Callable[[Path], None]) -> bool:
    """Build a library under a temporary name (0600, WAL, schema; seed(temporary) writes
    revision 1) and publish it at path with os.link. False: another process published first."""


def connect(path: Path) -> sqlite3.Connection:
    """Refuses a network filesystem (Linux); migrates an older schema."""


def migrate(conn: sqlite3.Connection) -> None: ...


def current_rev(conn: sqlite3.Connection) -> int: ...


def heads(conn: sqlite3.Connection, *, rev: int | None = None) -> list[Row]:
    """Every live entity's head as of rev (default: now), in one read transaction."""


def history(conn: sqlite3.Connection, kind: Kind, name: str) -> list[Row]:
    """Every version of one entity, newest first, tombstones included."""


class Writer:
    rev: int | None  # None until the first add

    def head(self, kind: Kind, name: str) -> Row | None:
        """The entity's highest version, tombstone or not, inside this transaction."""

    def heads(self) -> list[Row]:
        """Every live head inside this transaction, this save's versions included."""

    def add(
        self,
        kind: Kind,
        name: str,
        *,
        yaml: str | None,
        deleted: bool = False,
        attached: Sequence[str] | None = None,
        slug: str | None = None,
        use_when: str | None = None,
        hint: str | None = None,
        source: str | None = None,
    ) -> int:
        """Insert the next version (creating this save's revision first); return its number."""


@contextmanager
def write(path: Path, action: str, detail: str | None = None) -> Iterator[Writer]:
    """BEGIN IMMEDIATE … COMMIT, or ROLLBACK on any exception."""
```

### 4.3 `shapes.py`: deep_reasoner's models, canonical YAML, names

Each kind has one `validate_*` that takes YAML text and returns the canonical YAML and the parsed
model, or raises `LibraryValidationError` whose message is §4.10's `INVALID` (the mock-up's failure
cell, verbatim) and whose `errors` are pydantic's, one `FieldError` per error with `loc` joined by
dots (`messages.0.role`) and `msg` unchanged.

| Kind | Model | Extra rules (each a `FieldError`, sentence from §4.10) |
|---|---|---|
| namespace | `NamespaceConfig` | `name` matches `NAMESPACE_NAME`; no `decompositions` key (`INLINE_DECOMPOSITIONS`) |
| decomposition | `Decomposition` | name has no leading or trailing whitespace and no control characters (`DECOMPOSITION_NAME`); slug non-empty (`SLUG_EMPTY`); a `use_when` or `hint` key gets the extra line `METADATA_IN_YAML` |
| tool | the YAML is a mapping with string keys | name is an identifier and not a keyword (`TOOL_NAME`); `factory_from` absent, or equal to `tools/<name>.py` when a source is given (`TOOL_FILE`); a `factory_from` without a source (`TOOL_NO_SOURCE`) |
| profile | `V2Config` | none of `namespaces`, `namespaces_dir`, `decompositions`, `tools`, `config_path` (`PROFILE_PART`) |

YAML is parsed with `yaml.safe_load` (no conflit tags: composition is not a Library concept); a
document that is not a mapping is `NOT_A_MAPPING`.

A decomposition's validation also returns **warnings** (never errors): `NO_FINAL_ANSWER` when no
assistant message contains `FinalAnswer(` inside a `<repl>` … `</repl>` block (extracted with
deep_reasoner's `code(text, start=..., end=...)` and its `.source`, `v2/messages.py:288–307`, catching its `NoCodeBlock`). D3's
mock-up shows this warning at Save.

```python
# Matched with fullmatch.
NAMESPACE_NAME: re.Pattern[str] = re.compile(r"[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)*")
SPLIT_KEYS: frozenset[str] = frozenset(
    {"namespaces", "namespaces_dir", "decompositions", "tools", "config_path"}
)
TOOL_DIR = "tools"
YAML_WIDTH = 100


def canonical_yaml(data: Mapping[str, Any]) -> str: ...


def slug(name: str) -> str:
    """D1's rule (acp/catalog.py): lower case, runs of [^a-z0-9] -> "-", trimmed."""


def deep_reasoner_build() -> str:
    """'0.2.1+d7334ae' when deep-reasoner was installed from git (direct_url.json's
    commit_id, first 7), else its version alone."""


@dataclass(frozen=True)
class Shaped:
    yaml: str  # canonical
    data: dict[str, Any]  # the canonical YAML, parsed
    name: str  # the entity's key ("profile" for the profile)
    warnings: list[str]


def validate_namespace(text: str) -> Shaped: ...


def validate_decomposition(text: str) -> Shaped: ...


def validate_tool(name: str, text: str, source: str | None) -> Shaped:
    """With a source, factory_from is set to tools/<name>.py in the canonical block."""


def validate_profile(text: str) -> Shaped: ...


def namespace_config(
    namespace_yaml: str,
    decomposition_yamls: Sequence[str],
) -> NamespaceConfig:
    """A namespace head's canonical YAML with its attached decompositions' canonical YAML
    inlined as `decompositions`, in the given (attachment) order, validated. Used by
    materialize and by the effective view."""
```

### 4.4 `records.py`: what the API returns

Pydantic models, frozen; the HTTP API returns `model_dump(mode="json")` of these. `data` is the
canonical YAML parsed, so D3 needs no YAML parser to read a record.

```python
class Saved(BaseModel):
    model_config = ConfigDict(frozen=True)

    version: int
    rev: int  # the revision that wrote this version
    saved_at: datetime


class ProfileRecord(Saved):
    yaml: str
    decompositions: list[str]  # top level, in order
    default_namespace: str  # entry_namespace, else "root"

    @computed_field
    @property
    def data(self) -> dict[str, Any]: ...


class NamespaceRecord(Saved):
    name: str
    yaml: str
    decompositions: list[str]  # attached, in prompt order

    @computed_field
    @property
    def data(self) -> dict[str, Any]: ...


class DecompositionRecord(Saved):
    name: str
    slug: str
    yaml: str
    use_when: str | None
    hint: str | None
    namespaces: list[str]  # derived: live namespaces whose list names it, Library order
    top_level: bool  # derived: the profile's list names it

    @computed_field
    @property
    def data(self) -> dict[str, Any]: ...


class ToolRecord(Saved):
    name: str
    yaml: str
    source: str | None
    granted_in: list[str]  # derived: live namespaces whose tools list it

    @computed_field
    @property
    def data(self) -> dict[str, Any]: ...


class HistoryEntry(Saved):
    kind: Kind
    name: str
    action: str  # the revision's action
    deleted: bool
    yaml: str | None
    decompositions: list[str] | None  # profile, namespace
    slug: str | None
    use_when: str | None
    hint: str | None
    source: str | None
    deep_reasoner: str


class LibraryState(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: Path
    rev: int
    profile: ProfileRecord
    namespaces: dict[str, NamespaceRecord]  # root first, then creation order
    decompositions: dict[str, DecompositionRecord]  # keyed by name, in slug order
    tools: dict[str, ToolRecord]  # creation order


class Entry(BaseModel):
    kind: Kind
    name: str


class Change(Entry):
    version: int  # the version this save wrote
    created: bool  # the entity was not live before


class ImportReport(BaseModel):
    source: Path  # the main YAML read
    rev: int | None  # None: nothing changed
    changed: list[Change]
    unchanged: list[Entry]


class DecompositionMeta(BaseModel):
    use_when: str | None = None
    hint: str | None = None


class Manifest(BaseModel):
    """library.yaml in every materialized directory; dr never reads it."""

    v: Literal[1] = 1
    library: str  # the library file's absolute path
    rev: int
    namespace: str  # the entry namespace written into main.yaml
    deep_reasoner: str  # the build that validated what was written
    profile: int
    namespaces: dict[str, int]
    decompositions: dict[str, int]
    tools: dict[str, int]
    metadata: dict[str, DecompositionMeta]  # by name; import reads it back

    def versions(self) -> dict[str, Any]:
        """Everything but metadata: what D1 records as run.start.source.versions."""


class FieldError(BaseModel):
    loc: str  # "messages.0.role"; "name" for the Library's own rules; "" for the whole
    msg: str


class Problem(BaseModel):
    kind: Kind
    name: str
    message: str


class ValidationResult(BaseModel):
    ok: bool
    message: str | None  # INVALID's text when not ok
    errors: list[FieldError]
    warnings: list[str]
    name: str | None  # the entity's key, when the YAML got far enough to have one
    slug: str | None  # decompositions: the address to PUT to
    yaml: str | None  # the canonical form, when ok
```

**Errors.** One base class; each subclass knows its HTTP status and JSON `error` code, so the API's
error mapping is one handler.

```python
class LibraryError(Exception):
    code: ClassVar[str] = "error"
    status: ClassVar[int] = 400

    def __init__(self, message: str) -> None: ...

    def payload(self) -> dict[str, Any]:
        """{"error": code, "message": str(self), **extra}."""


class LibraryValidationError(LibraryError):
    code = "invalid"
    status = 422

    def __init__(self, message: str, errors: Sequence[FieldError]) -> None: ...


class LibraryNotFound(LibraryError):
    code = "not_found"
    status = 404


class LibraryConflict(LibraryError):
    """A base_version that is not the head's; carries the head (None: it does not exist)."""

    code = "conflict"
    status = 409

    def __init__(self, message: str, head: Saved | None) -> None: ...


class LibraryRefused(LibraryError):
    """A delete the invariants forbid: root, the default namespace, a parent."""

    code = "refused"
    status = 409


class LibraryImportError(LibraryError):
    code = "import_failed"
    status = 422
```

### 4.5 `library.py`: the Python API

```python
LIBRARY_FILE = "library.sqlite"


def library_path(home: Path | None = None) -> Path:
    """Home.resolve(home).root / "library.sqlite": --home, else $DR_HOME, else
    ~/.deep-reasoning (D1's Home, acp/runlog.py)."""


class Library:
    path: Path

    @classmethod
    def open(cls, path: Path | None = None, *, starter: bool = True) -> "Library":
        """Open path (default library_path()), creating it when absent: revision 1 is the
        starter's import, or, with starter=False, an empty profile and a bare root."""

    # ── reads: each one read transaction ──────────────────────────────────────────

    def rev(self) -> int: ...

    def state(self, *, rev: int | None = None) -> LibraryState: ...

    def profile(self) -> ProfileRecord: ...

    def namespaces(self) -> list[NamespaceRecord]:
        """Root first, then creation order."""

    def namespace(self, name: str) -> NamespaceRecord: ...

    def decompositions(self) -> list[DecompositionRecord]:
        """By slug."""

    def decomposition(self, key: str) -> DecompositionRecord:
        """key is a name or a slug: both are unique, and no name is another's slug."""

    def tools(self) -> list[ToolRecord]: ...

    def tool(self, name: str) -> ToolRecord: ...

    def history(self, kind: Kind, key: str) -> list[HistoryEntry]:
        """Newest first, tombstones included; works for deleted entities."""

    def effective(self, namespace: str) -> Effective: ...

    def check(self) -> list[Problem]:
        """Every live head re-validated under the installed deep_reasoner, plus granted
        tools the Library does not define and spawn targets it does not hold."""

    def validate(
        self,
        kind: Kind,
        text: str,
        *,
        name: str | None = None,
    ) -> ValidationResult:
        """Validate without saving. name is the tool's (a tool's YAML does not carry it)."""

    # ── writes: each one revision (or none, when nothing changes) ──────────────────

    def put_profile(
        self,
        text: str,
        *,
        decompositions: Sequence[str] | None = None,
        base_version: int | None = None,
    ) -> ProfileRecord: ...

    def put_namespace(
        self,
        text: str,
        *,
        decompositions: Sequence[str] | None = None,
        base_version: int | None = None,
    ) -> NamespaceRecord: ...

    def put_decomposition(
        self,
        text: str,
        *,
        use_when: str | None = None,
        hint: str | None = None,
        namespaces: Sequence[str] | None = None,
        top_level: bool | None = None,
        base_version: int | None = None,
    ) -> DecompositionRecord: ...

    def put_tool(
        self,
        name: str,
        text: str,
        *,
        source: str | None = None,
        granted_in: Sequence[str] | None = None,
        base_version: int | None = None,
    ) -> ToolRecord: ...

    def delete(
        self,
        kind: Literal["namespace", "decomposition", "tool"],
        key: str,
        *,
        base_version: int | None = None,
    ) -> HistoryEntry:
        """Write a tombstone; cascades as §2.3 says; returns the tombstone."""

    def import_config(self, path: str | Path) -> ImportReport:
        """A dr config (its main YAML, or a directory holding main.yaml), merged by name."""

    # ── files ───────────────────────────────────────────────────────────────────

    def materialize(
        self,
        dest: Path | None = None,
        *,
        namespace: str | None = None,
        rev: int | None = None,
    ) -> Path:
        """Write the Library (as of rev) as a plain dr config directory and return it.
        dest: absent or empty (default: a new temporary directory); namespace: the entry
        namespace written into main.yaml (default: the profile's)."""
```

**The starter** (`starter.yaml`, a plain `dr` config of our own; nothing copied from
deep_reasoner_beta, which has no license): `model: gpt-6-luna`; `client: {base_url:
https://api.openai.com/v1, api_key_env: OPENAI_API_KEY}`; a system prompt of a dozen lines in the
style of D1's `docs/configs/advising/prompt.yaml` but about no domain (reason in `<think>`, act in
one `<repl>` block, look at a result before relying on it, `FinalAnswer(value)` to answer, give
independent pieces of work to sub-agents with `run_all`); and `namespaces: {root: {repl: {type:
local}, tools: [llm]}}`. `Library.open` imports it as revision 1 (action `create`) when it creates
the file; `starter=False` seeds `profile` `{}` and `root` `name: root` instead.

The spec's mock-up runs as written:

```python
from deep_reasoning.library import Library

lib = Library.open()  # $DR_HOME/library.sqlite
lib.import_config("docs/configs/catalog/advisors.yaml")
# ['root', 'router', 'course_advisor', 'health_advisor']
[ns.name for ns in lib.namespaces()]
d = lib.put_decomposition(
    open("summarize_then_rank.yaml").read(),
    namespaces=["router"],
    use_when="comparing many courses",
)
# ('summarize then rank', 1, ['router'])
d.name, d.version, d.namespaces
run_dir = lib.materialize()  # a plain dr config directory; run_dir / "main.yaml"
```

**Semantics of each write**, in the order the code applies them, all inside one `store.write`:

- **`base_version`.** `None`: unconditional. `0`: the entity must not be live (`CONFLICT_EXISTS`,
  carrying the head). `n ≥ 1`: the head must be live at version `n` (`CONFLICT_STALE`, carrying the
  head; or `LibraryNotFound` if it is not live).
- **Unchanged is not a save.** If the canonical YAML, the metadata (or source) and the attachment
  list all equal the head's, no version is written; the call returns the head. A call that changes
  nothing anywhere makes no revision.
- **`put_profile`**: replaces the YAML; `decompositions` (the top-level list) is replaced when given.
- **`put_namespace`**: the key is the YAML's `name`; creating `a.b` needs `a` live; `decompositions`
  replaces the list when given.
- **`put_decomposition`**: the key is the YAML's `name`. YAML, `use_when` and `hint` are replaced
  (`None` and `""` both store no value). `namespaces`, when given, is the **exact set** of
  namespaces it is attached to afterwards: appended to the end of each newly named namespace's
  list, removed from each list no longer named. `top_level` likewise for the profile's list. So
  D3's "Save it as v3" after a conflict passes the head's `namespaces` plus the one picked, never
  the picked one alone.
- **`put_tool`**: YAML and source replaced; `granted_in` is the exact set of namespaces whose
  `NamespaceConfig.tools` lists the tool afterwards (appended at the end where added; each changed
  namespace gets a version).
- **`delete`**: refuses `root` (`REFUSE_ROOT`), the default namespace (`REFUSE_DEFAULT`) and a
  namespace with live children (`REFUSE_CHILDREN`). A decomposition's tombstone detaches it
  everywhere; a tool's removes it from every namespace's `tools`.
- **Renaming is not an operation.** A decomposition, namespace or tool saved under a new name is a
  new entity; the old one stays until deleted (§9 item 8).

### 4.6 `configdir.py`: import and materialize

**Reading a config** (`read_config(path) -> ConfigParts`) uses deep_reasoner's loader and nothing of
our own for composition:

1. `cfg = load_cli_config(path, schema=V2Config)` (conflit composes `_compose`, each entry relative
   to the file that names it; the result is validated and stamped with `config_path`). A relative
   `namespaces_dir` is resolved against `path`'s directory, as `dr` does (`v2/cli.py:696–697`; D1's
   `load_dr_config` does the same and is reused). A failure is `IMPORT_LOAD` with deep_reasoner's
   message.
2. **Profile** = `cfg.model_dump(mode="json", exclude_unset=True, exclude=SPLIT_KEYS)`. Extras
   (`description`, a data file's `documents`) are in it, because `V2Config` allows extras.
3. **Namespaces**: `load_namespaces_from_dir(cfg.namespaces_dir)` first, then `cfg.namespaces`
   (inline), a later one replacing an earlier one by name, as `build_registry` layers them
   (`namespaces.py:772–797`); `root` is added as `NamespaceConfig(name="root")` when the config
   authored none, so the import always says what root is. Order: root first, then dir files, then
   inline, each in its own order.
4. **Decompositions**: the top-level list, then each namespace's list in namespace order. A name met
   twice with equal bodies is one decomposition attached in both places; with different bodies it
   is `IMPORT_COLLISION`, naming both places (deep_reasoner allows a child to replace a parent's
   example by name; the Library keeps one body per name). Two names with one slug are
   `SLUG_TAKEN`.
5. **Tools**: `cfg.tools` in order. A block with `factory_from` has its file read (relative to
   `path`'s directory, as `load_tool_factory` resolves it against `config_path`,
   `tools/base.py:329–366`; missing is `IMPORT_TOOL_FILE`), and `factory_from` becomes
   `tools/<name>.py`. Only that file is captured (§9 item 7).
6. **Metadata**: if `library.yaml` sits beside `path` and parses as a `Manifest`, its `metadata`
   gives each decomposition's `use_when` and `hint` (an export re-imported keeps them). Otherwise a
   decomposition keeps its head's metadata, or has none. This is the one write that keeps
   something it was not given (§2.3's rule otherwise replaces it): a plain `dr` config cannot carry
   metadata, so importing one must not erase the user's use-when lines.

`import_config` reads and validates all of that **before** opening the write transaction, then, in
one `store.write(path, "import", str(main))`: decompositions and tools first, then namespaces root
first and parents before children, then the profile, each written only if it differs from its
head (§4.5's "unchanged"). Nothing absent from the config is touched (decision G). Then the
invariants.

**Writing a directory** (`write_config(state, dest, *, namespace) -> Manifest`):

```text
<dest>/
  main.yaml              the profile; then entry_namespace: <namespace>; namespaces_dir: namespaces;
                         decompositions: [the top-level list, bodies inlined]; tools: {name: block}
  namespaces/<name>.yaml one per live namespace: its YAML plus decompositions: [attached bodies, in order]
  tools/<name>.py        one per tool with a source
  library.yaml           the Manifest
```

- Every file is canonical YAML. `main.yaml` and `library.yaml` start with one comment line:
  `# Written by the deep-reasoning Library from <path> at revision <rev>. Edit the Library, not
  this file.` (`dr` ignores comments; the rows never hold them.)
- `main.yaml` is written last, so a directory with a `main.yaml` is complete.
- `materialize` first re-validates every head it is about to write under the installed
  deep_reasoner (decision J) and raises `LibraryValidationError` listing each one that fails, before
  writing anything. It refuses a `dest` that exists and is not empty (`DEST_NOT_EMPTY`); when it
  made `dest` itself and a write fails, it removes it.
- Export (`dr-library export DIR`, which D5's `dr-app export` calls) is `materialize(DIR)` with the
  profile's default namespace. `GET /export` zips a temporary materialization.

Paths inside tool blocks other than `factory_from` (a `rag` tool's `documents`, a `kg` tool's
`persist`, a Claude worker's `dirs`) are read by deep_reasoner relative to the **working
directory** (`tools/base.py:186–196`), so they mean under a materialized config what they mean under
the original: relative to the conversation's folder in `dr-acp` (D1's worker `cwd`), relative to
where the user runs `dr` on an export. The Library holds no data files.

```python
@dataclass(frozen=True)
class ConfigParts:
    main: Path  # the main YAML read
    profile: dict[str, Any]  # the V2Config remainder, as set
    top_level: list[str]  # top-level decomposition names, in order
    # (the NamespaceConfig dump without decompositions, its attached names), root first
    namespaces: list[tuple[dict[str, Any], list[str]]]
    decompositions: dict[str, dict[str, Any]]  # name -> its dump, as first seen
    tools: dict[str, tuple[dict[str, Any], str | None]]  # name -> (block, source)
    metadata: dict[str, DecompositionMeta]  # from library.yaml beside it, if any


def read_config(path: Path) -> ConfigParts: ...


def write_config(state: LibraryState, dest: Path, *, namespace: str) -> Manifest: ...
```

### 4.7 `catalog.py`: the seam to D1

```python
class LibraryCatalog:
    """D1's Catalog (deep_reasoning.acp.catalog) over the Library at path."""

    def __init__(self, path: Path) -> None:
        """Stores the path; opens nothing and imports nothing until first used, then
        Library.open(path), which creates the library with the starter if it is absent."""

    def snapshot(self) -> CatalogSnapshot:
        """Materialize into a temporary directory; take ConfigCatalog(main).snapshot();
        on each CommandEntry put the decomposition's use-when line (description) and
        hint where the Library has them (dataclasses.replace); delete the directory."""

    def materialize(self, namespace: str, *, run_dir: Path) -> RunSource:
        """Library.materialize(run_dir / "config", namespace=namespace) (LibraryNotFound for
        a namespace that is not live); then ConfigCatalog(main).materialize(namespace,
        run_dir=run_dir) with versions replaced by the manifest's versions()."""
```

What `dr-acp` gets, field by field:

| D1's field | From the Library |
|---|---|
| `CatalogSnapshot.namespaces` | `root`, then the other live namespaces by name (ConfigCatalog's rule) |
| `CatalogSnapshot.default_namespace` | the profile's `entry_namespace`, else `root` |
| `CatalogSnapshot.commands[ns]` | the top-level list, then `resolve(ns).decompositions`, first name wins (ConfigCatalog's rule); `name` = the slug, never suffixed (slugs are unique); `description` = `use_when`, else D1's default sentence; `hint` = `hint`, else `"the task"` |
| `RunSource.config_path` | `<run_dir>/config/main.yaml` |
| `RunSource.namespace` | the namespace asked for |
| `RunSource.client` | `cfg.client.model_dump(mode="json")` of what was written (ConfigCatalog's) |
| `RunSource.versions` | `{"v": 1, "library", "rev", "namespace", "deep_reasoner", "profile", "namespaces", "decompositions", "tools"}` |

**Every decomposition is offered**, as D1 §4.6 decided; D1's §10 item 6 (offer only "programs") is
not taken up here (§9 item 3).

**What D2 changes in D1's files, as D1 §4.6 anticipates.** `acp/cli.py`: without `--config`, the
catalog is `LibraryCatalog(library_path(options.home))` instead of exiting 2; the `Options.config`
comment loses "required until D2". The session index's `source` (D1 §4.4) is written as
`{"kind": "library", "library": "<path>"}` for a Library session. Nothing in the `Catalog`,
`CatalogSnapshot`, `CommandEntry` or `RunSource` shapes changes.

**Freshness.** D1 takes the snapshot at `session/new` and materializes at the first prompt, so a
save in between is in the run but was not in the menu. A command whose decomposition was deleted
in between fails at the first prompt with deep_reasoner's own `unknown decomposition '…'; this
config defines: […]` (`find_decomposition`, `v2/decompositions.py:117–132`), which D1 answers as
`build_failed`.

### 4.8 `api.py` and `cli.py`: the App backend and the command

```python
def create_app(
    library: Library,
    *,
    same_user: Callable[[tuple[str, int], tuple[str, int]], bool] | None = None,
) -> Starlette:
    """The routes of §6. same_user(client, server) is asked for every request; a False is
    403 FORBIDDEN_PEER. Default: same_user_peer on Linux, no check elsewhere."""


def same_user_peer(
    client: tuple[str, int],
    server: tuple[str, int],
    *,
    proc_net: Path = Path("/proc/net"),
) -> bool:
    """True when the TCP socket at client connected to server belongs to os.getuid().

    Reads proc_net/tcp and tcp6, finds the row whose local address is client and remote
    address is server (hex, little-endian per 32-bit word, as the kernel prints them), and
    compares its uid. No such row: False.
    """
```

Endpoints are plain `def` functions, which Starlette runs on its thread pool; each calls one
`Library` method and returns its record's `model_dump(mode="json")`. One exception handler turns
`LibraryError` into `JSONResponse(exc.payload(), status_code=exc.status)`; a body that is not JSON
or lacks `yaml` is `bad_request` (400). Verified: on Linux, the row for the client end of a
loopback connection is present in `/proc/net/tcp` with the client's uid.

```python
def main(argv: Sequence[str] | None = None) -> int:
    """dr-library serve | import | export (argparse; exit 0, 1 on LibraryError with its
    message on stderr, 2 on usage)."""
```

```text
dr-library serve --port PORT [--home DIR] [--log-level LEVEL]
    The App backend: uvicorn on 127.0.0.1:PORT, health at /health. Logs on stderr.
dr-library import PATH [--home DIR]
    "imported PATH as revision N: A new, B changed, C unchanged" or
    "nothing changed: the library already holds PATH"
dr-library export DIR [--home DIR] [--namespace NAME] [--rev N]
    "wrote DIR/main.yaml: 4 namespaces, 6 decompositions, 1 tool"   (D5's mock-up line)
```

**Why `--home` and not only `$DR_HOME`.** The agent-server starts an App backend with only `LANG`,
`LC_ALL`, `LC_CTYPE`, `PATH`, `TMPDIR` and `TZ` from its environment, and its argv may use only the
placeholders `{port}`, `{data_dir}` and `{artifact_dir}` (`manifest.py:136, 148`;
`backend.py:38–40`). So `$DR_HOME` never reaches the backend, and D5's setup, which writes the App's
manifest on the user's machine, puts the resolved home in the argv as a literal
(`["{artifact_dir}/bin/dr-library", "serve", "--port", "{port}", "--home", "/Users/u/.deep-reasoning"]`).
Without `--home` the backend falls back to `$DR_HOME`, then `~/.deep-reasoning`; `Path.home()`
works without `HOME` (it falls back to the password database; verified). Packaging the executable
inside `{artifact_dir}` is D3's and D5's (spec §2's deferred list).

**Start-up time.** The backend imports deep_reasoner at start (≈1.4 s measured), well inside the
health probe's 30 s default (`manifest.py:115–117`).

### 4.9 `effective.py`: what a namespace inherits, and from where

D3's Namespaces tab shows each field's effective value and its source ("Inherited from root",
"Overridden here"), and its Decompositions tab shows inherited decompositions with a badge. The
values come from deep_reasoner's own `resolve`; only the sources are ours.

1. Build `cfg = V2Config.model_validate({**profile.data, "namespaces": {each live namespace:
   namespace_config(head, attached bodies)}})` and `registry = build_namespace_registry(cfg)`, which
   seeds root's `repl` from the profile's `repl` (`v2/cli.py:289–306`); `resolved =
   registry.resolve(name)`; `registry.close()`.
2. `chain` = `root`, …, `name` (the dotted prefixes).
3. Sources, walking the chain's `NamespaceConfig`s with `resolve`'s own rules
   (`namespaces.py:272–320`):
   - `repl`: the last level that sets it; none: `"profile"`.
   - `reasoner`, `spawn`: the last level that sets it; none: `None` (the run's, deep_reasoner's
     default).
   - `system_suffix`: every level that sets one, in order, with its text.
   - `tools`: each of `resolved.tools` with the first level that lists it, and whether the Library
     defines it (a tool row, or `llm` while the profile has a `model`).
   - `vars`: each key of `resolved.vars` with the last level that sets it.
   - `decompositions`: each of `resolved.decompositions` with the last level whose list has that
     name, its version, slug and use-when line.

A test asserts that the walk's values equal `resolved`'s for every namespace of every corpus config
(§7.2), so a change in deep_reasoner's rules fails a test rather than mislabelling a badge.

```python
class Sourced(BaseModel):
    value: Any
    source: str | None  # a namespace, "profile", or None (unset everywhere)


class SuffixPart(BaseModel):
    source: str
    text: str


class EffectiveTool(BaseModel):
    name: str
    source: str
    defined: bool


class EffectiveDecomposition(BaseModel):
    name: str
    slug: str
    version: int
    use_when: str | None
    source: str


class Effective(BaseModel):
    namespace: str
    chain: list[str]  # root first
    repl: Sourced
    reasoner: Sourced
    spawn: Sourced
    system_suffix: list[SuffixPart]
    tools: list[EffectiveTool]
    vars: dict[str, Sourced]
    decompositions: list[EffectiveDecomposition]


def effective(state: LibraryState, namespace: str) -> Effective: ...
```

### 4.10 `texts.py`: every user-visible sentence (verbatim)

A sentence without fields is a constant; one with `{fields}` is a lower-case function of them
returning an f-string, as in D1's `texts.py`. D3 shows `message` from the API as it is.

| Name | Text |
|---|---|
| `INVALID` | `'{name}' is not a valid deep_reasoner {model}:` then one line per error, `  {loc}: {msg}`, then the extra lines below that apply (the mock-up's failure cell). `{name}` is the YAML's `name` when it has one, else `this YAML`. |
| `METADATA_IN_YAML` | `Use-when text is stored beside the YAML: pass use_when=... instead.` (a `use_when` key; the mock-up's line) / `A hint is stored beside the YAML: pass hint=... instead.` (a `hint` key) |
| `INLINE_DECOMPOSITIONS` | `A namespace's decompositions are attached by name, not written in its YAML: pass decompositions=[...] instead.` |
| `PROFILE_PART` | `'{key}' is not part of the profile: namespaces, decompositions and tools are stored as entries of their own.` |
| `NOT_A_MAPPING` | `The YAML must be a mapping of keys to values.` |
| `NAMESPACE_NAME` | `'{name}' is not a namespace name: use letters, digits, '_' and '-', with '.' between levels (for example math.geometry).` |
| `PARENT_MISSING` | `Namespace '{name}' needs its parent '{parent}', which is not in the library.` |
| `DECOMPOSITION_NAME` | `A decomposition's name must not start or end with a space or hold control characters; got {name!r}.` |
| `SLUG_EMPTY` | `'{name}' has no letters or digits, so it cannot be a slash command.` |
| `SLUG_TAKEN` | `'{name}' would be the slash command /{slug}, which '{other}' already is. Give it another name.` |
| `TOOL_NAME` | `'{name}' is not a tool name: a tool is bound in the REPL under its name, so it must be a Python identifier.` |
| `TOOL_FILE` | `Tool '{name}': factory_from must be tools/{name}.py, where the Library writes its source; got '{value}'.` |
| `TOOL_NO_SOURCE` | `Tool '{name}' names factory_from but no source was sent with it.` |
| `UNKNOWN_DECOMPOSITION` | `There is no decomposition '{name}' in the library to attach.` |
| `LISTED_TWICE` | `'{name}' is listed twice in {where}.` |
| `DEFAULT_MISSING` | `The default namespace '{name}' is not in the library.` |
| `NOT_FOUND` | `There is no {kind} '{name}' in the library.` |
| `CONFLICT_EXISTS` | `{kind} '{name}' already exists, at version {head}.` (capitalized kind) |
| `CONFLICT_STALE` | `{kind} '{name}' is at version {head}, not {base}: it changed after you opened it. Reload it, or save over it with base_version={head}.` |
| `REFUSE_ROOT` | `root cannot be deleted: every namespace inherits from it.` |
| `REFUSE_DEFAULT` | `'{name}' is the namespace new conversations start in; choose another one first.` |
| `REFUSE_CHILDREN` | `'{name}' has namespaces under it ({children}); delete them first.` |
| `NAME_MISMATCH` | `The YAML names '{yaml_name}', but this is the address of '{key}'. A new name is a new {kind}: save it at its own address.` |
| `IMPORT_LOAD` | `{path} is not a dr config deep_reasoner can load: {detail}` |
| `IMPORT_COLLISION` | `{path} defines two different decompositions named '{name}' (in {first} and in {second}). The library keeps one decomposition per name: rename one and import again.` (`{first}` is `the top level` or `namespace 'x'`) |
| `IMPORT_TOOL_FILE` | `Tool '{name}': factory_from '{value}' resolved to {resolved}, which does not exist.` |
| `DEST_NOT_EMPTY` | `{dest} is not empty; the library writes a config directory only into a new or empty folder.` |
| `NETWORK_FS` | `{path} is on a network filesystem ({fstype}), where SQLite cannot keep the library safe. Set DR_HOME to a folder on this computer's own disk.` |
| `STALE_HEAD` | `{kind} '{name}' version {version} no longer validates under deep_reasoner {build}: {first_error}` (a problem; also a line of materialize's error) |
| `UNKNOWN_TOOL` | `Namespace '{namespace}' grants '{tool}', which is not a tool in the library; an agent there will not start.` (a problem) |
| `UNKNOWN_SPAWN` | `Namespace '{namespace}' may spawn into '{target}', which is not in the library.` (a problem) |
| `NO_FINAL_ANSWER` | `This example never reaches FinalAnswer; the agent will imitate that.` (D3's mock-up; a warning) |
| `FORBIDDEN_PEER` | `This library belongs to another user on this computer.` |
| `IMPORTED` | `imported {path} as revision {rev}: {new} new, {changed} changed, {unchanged} unchanged` |
| `NOTHING_IMPORTED` | `nothing changed: the library already holds {path}` |
| `EXPORTED` | `wrote {main}: {n} namespace(s), {m} decomposition(s), {k} tool(s)` (singular for 1, as D5's mock-up: `4 namespaces, 6 decompositions, 1 tool`) |

The two sentences quoting deep_reasoner are its own: pydantic's messages arrive unchanged (for an
empty `messages` list that is `List should have at least 1 item after validation, not 0`; D3's
mock-up shortened it), and `IMPORT_LOAD`'s `{detail}` is `f"{type(exc).__name__}: {exc}"`, D1's
form.

---

## 5 · Algorithms

### 5.1 One save, end to end

```text
validate the input outside any transaction (shapes.py)        → LibraryValidationError
with store.write(path, action, detail) as w:                   BEGIN IMMEDIATE (waits ≤ 5 s)
    head = w.head(kind, key);   check base_version              → LibraryConflict / NotFound
    compute the new rows: this entity, plus every namespace or profile list the save edits
    for each row that differs from its head: w.add(...)         (the first add makes the revision)
    check §2.5 against w.heads()                                → LibraryValidationError / Refused
COMMIT; return the record read back inside the same transaction
```

### 5.2 Import

§4.6. The only judgement in it is the merge: the imported config wins for every entity it names,
and only for those. An import that changes the profile replaces the user's run settings; the
report says so (`changed: profile`), and the previous profile is one version back.

### 5.3 Materialize

`state(rev)` in one read transaction → re-validate every head → write the namespaces, the tool
files, `library.yaml`, then `main.yaml`. The state is one revision, so a concurrent save is either
wholly in it or wholly absent.

### 5.4 Several processes, one file

The App backend writes; `dr-library import` writes; each `dr-acp` reads; D4's Check may read.
`BEGIN IMMEDIATE` makes two writers queue (a save is milliseconds; the busy timeout is 5 s). A
reader in WAL mode reads the last committed revision and never waits for a writer. Nobody holds a
connection across calls. A crash mid-save leaves the previous revision, by SQLite's atomic commit.

---

## 6 · The HTTP contract (D3 and D4 build against this)

### 6.1 Transport

- **Where.** `dr-library serve` on `127.0.0.1:{port}`. The App's pages reach it through the
  agent-server's bridge at `<ingress>/app-backends/dr-library/<path>`; the bridge strips that
  prefix (`bridge.py:464`), so the paths below are what the backend sees and what the App calls
  relative to its ingress URL.
- **Keys in paths** are URL-safe by construction: namespace names match `NAMESPACE_NAME`, tool names
  are identifiers, decompositions are addressed by slug (`[a-z0-9-]+`). The bridge decodes the
  path once, refuses `.` and `..` segments and backslashes, and rebuilds the upstream URL from the
  decoded text (`bridge.py:322–343, 464`), which is why raw names cannot travel.
- **Bodies** are JSON. YAML travels as a string field `yaml`; any YAML is accepted, JSON text
  included. Every record carries both `yaml` (canonical) and `data` (parsed).
- **Writes** are `PUT` (create or update) and `DELETE`; the bridge requires the ingress `Origin` on
  them (`bridge.py:454`), which the App's own fetches carry.
- **Concurrency**: `base_version` in a `PUT` body, or `?base_version=n` on a `DELETE`. Omitted:
  unconditional. D3 always sends it.
- **Status codes**: 200 read or updated; 201 created (version 1, or re-created after a delete);
  400 `bad_request`; 403 `forbidden`; 404 `not_found`; 409 `conflict` or `refused`; 422 `invalid`.
- **Errors** are `{"error": code, "message": sentence, ...}`: `invalid` adds `errors: [{loc, msg}]`;
  `conflict` adds `head` (the current record, or `null`).
- **No push.** A panel polls `GET /health` for `rev` while it is visible and refetches when it
  moves.

### 6.2 Endpoints

| Method and path | Body or query | Answer |
|---|---|---|
| `GET /health` | | `{"ok": true, "rev", "path", "deep_reasoner", "default_namespace"}` |
| `GET /problems` | | `[Problem]` |
| `POST /validate` | `{"kind", "yaml", "name"?, "source"?}` | `ValidationResult`, always 200 |
| `GET /profile` | | `ProfileRecord` |
| `PUT /profile` | `{"yaml", "decompositions"?, "base_version"?}` | `ProfileRecord` |
| `GET /namespaces` | | `[NamespaceRecord]`, root first, then creation order |
| `GET /namespaces/{name}` | | `NamespaceRecord` |
| `PUT /namespaces/{name}` | `{"yaml", "decompositions"?, "base_version"?}` | `NamespaceRecord`, 201 or 200 |
| `DELETE /namespaces/{name}` | `?base_version=n` | `HistoryEntry` (the tombstone) |
| `GET /namespaces/{name}/effective` | | `Effective` |
| `GET /effective` | | `[Effective]`, one per namespace, in `GET /namespaces` order |
| `GET /decompositions` | | `[DecompositionRecord]`, by slug |
| `GET /decompositions/{slug}` | | `DecompositionRecord` |
| `PUT /decompositions/{slug}` | `{"yaml", "use_when"?, "hint"?, "namespaces"?, "top_level"?, "base_version"?}` | `DecompositionRecord`, 201 or 200 |
| `DELETE /decompositions/{slug}` | `?base_version=n` | `HistoryEntry` |
| `GET /tools` | | `[ToolRecord]` |
| `GET /tools/{name}` | | `ToolRecord` |
| `PUT /tools/{name}` | `{"yaml", "source"?, "granted_in"?, "base_version"?}` | `ToolRecord`, 201 or 200 |
| `DELETE /tools/{name}` | `?base_version=n` | `HistoryEntry` |
| `GET /{profile \| namespaces/{name} \| decompositions/{slug} \| tools/{name}}/versions` | | `[HistoryEntry]`, newest first |
| `GET …/versions/{n}` | | `HistoryEntry` |
| `GET /export` | `?namespace=` | `application/zip`, `Content-Disposition: attachment; filename="library-rev<N>.zip"`: the materialized directory under `library/` |

In a `PUT`, the key in the path must be the YAML's key (`name`, or the slug of the decomposition's
`name`); otherwise 400 `NAME_MISMATCH`. `use_when` and `hint` absent, `null` or `""` all store no
value (a `PUT` replaces them, §2.3). `namespaces`, `top_level`, `decompositions` and `granted_in`
absent mean "leave as it is".

There is **no import endpoint** (decision K): importing is `dr-library import`.

### 6.3 Examples

`PUT /decompositions/summarize-then-rank` creating one in `router`:

```json
{"yaml": "{\"name\": \"summarize then rank\", \"messages\": [{\"role\": \"user\", \"content\": \"Summarize each CS course, then rank them by workload.\"}, {\"role\": \"assistant\", \"content\": \"<think>…</think>\\n<repl>\\n…\\n</repl>\\n\"}]}",
 "use_when": "comparing many courses",
 "hint": "what to compare",
 "namespaces": ["router"],
 "base_version": 0}
```

→ `201`

```json
{"version": 1, "rev": 3, "saved_at": "2026-10-02T14:22:31Z",
 "name": "summarize then rank", "slug": "summarize-then-rank",
 "yaml": "name: summarize then rank\nmessages:\n- role: user\n  content: Summarize each CS course, then rank them by workload.\n- role: assistant\n  content: |\n    <think>…</think>\n    <repl>\n    …\n    </repl>\n",
 "use_when": "comparing many courses", "hint": "what to compare",
 "namespaces": ["router"], "top_level": false,
 "data": {"name": "summarize then rank", "messages": [{"role": "user", "content": "…"}, {"role": "assistant", "content": "…"}]}}
```

The same request again, after someone else saved v2 → `409`:

```json
{"error": "conflict",
 "message": "Decomposition 'summarize then rank' already exists, at version 2.",
 "head": {"version": 2, "rev": 5, "name": "summarize then rank", "slug": "summarize-then-rank", "namespaces": ["router"], "…": "…"}}
```

A use-when line written into the YAML → `422` (the spec's failure cell):

```json
{"error": "invalid",
 "message": "'x' is not a valid deep_reasoner Decomposition:\n  use_when: Extra inputs are not permitted\nUse-when text is stored beside the YAML: pass use_when=... instead.",
 "errors": [{"loc": "use_when", "msg": "Extra inputs are not permitted"}]}
```

`GET /namespaces/course_advisor/effective` after the advisors import:

```json
{"namespace": "course_advisor", "chain": ["root", "course_advisor"],
 "repl": {"value": {"type": "local"}, "source": "profile"},
 "reasoner": {"value": null, "source": null},
 "spawn": {"value": null, "source": null},
 "system_suffix": [],
 "tools": [{"name": "llm", "source": "root", "defined": true}],
 "vars": {"catalog": {"value": {"CS101": {"title": "Intro to Programming", "…": "…"}}, "source": "course_advisor"}},
 "decompositions": [{"name": "catalog lookup", "slug": "catalog-lookup", "version": 1, "use_when": null, "source": "course_advisor"}]}
```

`POST /validate` with `{"kind": "decomposition", "yaml": "name: x\nmessages: []"}` → `200`:

```json
{"ok": false,
 "message": "'x' is not a valid deep_reasoner Decomposition:\n  messages: List should have at least 1 item after validation, not 0",
 "errors": [{"loc": "messages", "msg": "List should have at least 1 item after validation, not 0"}],
 "warnings": [], "name": "x", "slug": "x", "yaml": null}
```

### 6.4 D3's flows on this contract

| D3 (spec) | Calls |
|---|---|
| Decompositions tab: by namespace, use-when, version, inherited badge | `GET /effective` (each namespace's decompositions with source and version); `GET /decompositions` for top-level ones and the hint |
| Create decomposition: write, pick a namespace from the existing ones, save | `GET /namespaces` (the picker); `POST /validate` while writing (View YAML, the `slug`, the FinalAnswer warning); `PUT /decompositions/{slug}` with `namespaces: [picked]`, `base_version: 0` → 201 "Saved … v1 in …" |
| "'catalog lookup' is already in router (v2). Save it as v3, or give it another name." | the 409's `head.version` and `head.namespaces`; "Save it as v3" re-sends with `base_version: 2` and `namespaces: head.namespaces ∪ {picked}` |
| Open one in the card editor; attach it to more namespaces | `GET /decompositions/{slug}`; `PUT` with `base_version` = its version and `namespaces` = the new set |
| Namespaces: tree, effective values, Override and Reset | `GET /namespaces` (dotted names make the tree); `GET /namespaces/{name}/effective`; Override = `PUT /namespaces/{name}` with the field added to `data`; Reset = the same with it removed |
| The namespace new conversations start in | `PUT /profile` with `entry_namespace` changed in `data` |
| Tools tab (D4) | §6.5 |
| History of an entry | `GET …/versions` |

### 6.5 What D4 gets, and what it adds

- **A tool written in the editor** is `PUT /tools/{name}` with `yaml` = its block (`factory: make`
  and its parameters; `factory_from` may be omitted, the Library sets `tools/<name>.py`), `source`
  = the Python file, `granted_in` = the namespaces whose checkboxes are ticked. At run time the file
  is `tools/<name>.py` beside the materialized `main.yaml`, which is what spec D4 says.
- **Grants are deep_reasoner's own**: a namespace's `NamespaceConfig.tools`. `granted_in` edits
  those lists; a grant inherited from `root` reaches every namespace (`tools` accumulates).
- **Check** is D4's: it can materialize the Library into a temporary directory and build the tool
  there with deep_reasoner's `make_tools` in a throwaway process. D4 adds its route
  (`POST /tools/{name}/check`) to `api.py`.
- **MCP servers**: the Library needs to hold, per namespace, which forwarded servers are granted.
  Two ways fit this store without changing it: (a) each granted server is a tool row whose source is
  D4's generated `factory_from` shim and whose parameters name the server, granted through
  `granted_in` like any tool (an export then runs under `dr` with the `mcp` package, as spec D4
  requires); or (b) a table of D4's own, added by appending a migration to `store.MIGRATIONS`. The
  choice is D4's; (a) needs no change to D2 or to D1's Catalog.

---

## 7 · Testing

Plain pytest under `tests/library/`, sharing D1's `tests/conftest.py` (which imports deep_reasoner
with pytest hidden, because `juplit.test()` is true in any process that imported pytest and
deep_reasoner's modules would otherwise run their notebook tests on import). deep_reasoner_beta's
configs are read in place from the checkout `DR_BETA_CHECKOUT` names, never copied (no license; D1
§10 item 2).

### 7.1 E7 · Round-trip

**Corpus.** Every `*.yaml` under `$DR_BETA_CHECKOUT/docs/configs` and `$DR_BETA_CHECKOUT/configs`,
discovered at collection (40 files at `d7334ae`), each its own parametrized case, so every failure
is listed by name and none stops the others. Two of them are not configs: `load_cli_config(…,
schema=V2Config)` rejects `configs/example/namespaces/root.yaml` and
`docs/configs/catalog/namespaces/root.yaml` (namespace files whose `tools:` is a list). The test
asserts that exactly these two are rejected, with that reason. Their directories are still covered:
`docs/configs/catalog/namespaces/` by `namespaces_dir.yaml`, which loads it, and
`configs/example/namespaces/` by one config the test writes to `tmp_path`
(`_compose: [<checkout>/configs/example/main.yaml]`, `namespaces_dir:
<checkout>/configs/example/namespaces`).

**Level 1, every config (no model, no network).** Import into a fresh Library (`starter=False`),
`materialize(namespace=cfg.entry_namespace)`, load the result with D1's `load_dr_config`, and
assert:

1. the two `V2Config`s are equal except `config_path`, `namespaces`, `namespaces_dir` and each tool
   block's `factory_from`;
2. the materialized registry holds exactly the original's namespaces, and `registry.resolve(ns)` is
   equal for every one;
3. each tool's materialized file is byte-identical to the original's `factory_from` file;
4. importing the materialized directory into a second fresh Library gives the same canonical rows,
   and importing it into the first makes no revision.

**Level 2, every config (a fake model, no network).** Run `dr <config> "Which course comes after
CS101?" --no-progress --run-dir <tmp>` on the original and on the materialized copy, against
D1's `FakeOpenAI` answering every chat call `<think>ok</think>\n<repl>\nFinalAnswer("done")\n</repl>`
and every `/v1/embeddings` call with a fixed vector (D2 adds that route; it is ten lines, §7.5),
with `--set client.base_url=<fake>` and, for each tool block that has its own `client`,
`--set tools.<name>.client.base_url=<fake>`; dummy keys in the environment; deep_reasoner's
`write_fake_claude_cli` first on `PATH`; and as working directory a temporary folder holding one
symlink named `configs`, pointing at the checkout's `configs/` for a file under it, or at its
`docs/configs/` for a file under that (deep_reasoner's docs pages run from `docs/`), so relative
data paths such as `configs/examples/experience/memory.yaml` resolve and `logs/` lands in the
temporary folder, never in the checkout. Assert equal exit codes, equal last
lines of stdout, and equal `messages` in the first chat request. A guard asserts that at least the
configs that answered at `d7334ae` still answer (the set is committed in the test), so a broken
fake cannot make every case "equal" by failing everywhere.

**Measured with the prototype (2026-10-02, a stand-in for `FakeOpenAI` that also served
embeddings, cwd at the checkout root, no Claude stub):** all 38 loadable files pass level 1. Of
the 33 outside `namespaces/` directories, 17 reach an answer on both sides with equal first
requests; the two Claude-backbone configs (`docs/configs/catalog/claude.yaml`,
`docs/configs/incidents/triage.yaml`) also reached an answer on both sides, because a real `claude`
CLI was on that machine's `PATH` (their answers differed, as a real model's do; the test uses the
fake CLI); the other 14 fail identically on both sides (fragments without a `model`, data files,
`rag.yaml`'s own embeddings client, `experience.yaml`'s path relative to `docs/`). The
Implementer's harness (fake Claude CLI, the tool-client override, the `docs/` working directory)
should raise the 17; the committed set is whatever it measures.

**Null:** any case failing either level. Failures are listed (one case each), never skipped. In CI
`DR_BETA_CHECKOUT` is set (§7.5); outside CI, without it, the cases skip with that reason, and a
guard test fails when `CI=true` and it is unset.

### 7.2 Test files, named for what they pin

| File | Pins |
|---|---|
| `test_store.py` | `test_versions_and_revisions_cannot_be_updated_or_deleted` (the triggers); `test_a_save_that_changes_nothing_makes_no_revision`; `test_heads_as_of_a_revision_ignore_later_versions`; `test_a_new_library_file_is_private_to_its_user` (0600); `test_two_processes_saving_at_once_both_land` (two subprocesses, `BEGIN IMMEDIATE`); `test_a_library_on_a_network_filesystem_is_refused` (a fake `/proc/self/mounts` passed in) |
| `test_shapes.py` | `test_canonical_yaml_is_the_same_for_every_spelling_of_one_model` (parametrized: flow, block, JSON, key order); `test_canonical_yaml_is_idempotent`; `test_multiline_strings_are_literal_blocks`; `test_metadata_in_the_yaml_is_refused_with_deep_reasoners_message` (the spec's failure cell, verbatim); `test_namespace_names`; `test_tool_factory_from_must_be_its_own_file`; `test_profile_refuses_namespaces_decompositions_and_tools`; `test_an_example_without_final_answer_warns` |
| `test_library.py` | `test_put_then_get_returns_the_canonical_record`; `test_every_save_is_a_new_version`; `test_a_stale_base_version_is_a_conflict_carrying_the_head`; `test_base_version_zero_refuses_an_existing_entry`; `test_attaching_versions_the_namespace_and_appends_in_order`; `test_namespaces_is_the_exact_set_after_a_save`; `test_deleting_a_decomposition_detaches_it_everywhere`; `test_deleting_a_tool_ungrants_it_everywhere`; `test_root_the_default_and_a_parent_cannot_be_deleted`; `test_a_namespace_needs_its_parent`; `test_two_names_with_one_slug_are_refused`; `test_deleted_and_recreated_continues_its_version_numbers`; `test_history_lists_tombstones`; `test_check_reports_ungranted_tools_and_missing_spawn_targets`; `test_a_head_that_stops_validating_is_a_problem_and_blocks_materialize` (monkeypatch the model to a stricter one) |
| `test_import.py` | `test_import_creates_every_entity_in_one_revision`; `test_reimporting_the_same_config_changes_nothing`; `test_import_never_deletes`; `test_import_replaces_what_the_config_names`; `test_compose_is_flattened`; `test_one_name_with_two_bodies_is_refused_naming_both_places`; `test_factory_from_is_read_into_the_library`; `test_a_missing_factory_file_is_refused`; `test_an_exports_library_yaml_keeps_use_when_and_hint` |
| `test_materialize.py` | `test_materialized_directory_layout`; `test_decompositions_are_inlined_in_attachment_order`; `test_materialize_as_of_an_old_revision`; `test_the_manifest_records_every_version`; `test_a_non_empty_destination_is_refused`; `test_a_failed_write_leaves_no_directory` |
| `test_effective.py` | `test_effective_values_equal_deep_reasoners_resolve` (every namespace of every corpus config, with `DR_BETA_CHECKOUT`); `test_sources` (parametrized over each field rule of §4.9) |
| `test_catalog.py` | `test_snapshot_equals_config_catalog_over_the_materialized_config_plus_metadata`; `test_commands_carry_use_when_and_hint`; `test_materialize_gives_d1_a_run_source_with_versions`; `test_an_unknown_namespace_is_not_found`; **`test_a_saved_decomposition_reaches_the_next_conversation_in_its_namespace`** (§7.3) |
| `test_api.py` | Starlette's `TestClient`: every route of §6.2, its status and JSON shape; `test_errors_carry_code_message_and_details`; `test_a_slug_with_spaces_in_the_name_round_trips`; `test_the_path_key_must_match_the_yaml`; `test_export_is_a_zip_of_a_materialized_directory`; `test_another_users_connection_is_refused` (a fake `/proc/net` passed to `same_user_peer`) |
| `test_cli.py` | `test_serve_answers_health_on_loopback` (a real `dr-library serve` subprocess with only the six variables an App backend gets); `test_import_and_export_print_their_lines` |
| `test_roundtrip.py` | E7, §7.1 |
| `test_live.py` | §7.4 |

### 7.3 D3's falsifier, at the store

Spec D3: "a decomposition saved in Create decomposition is not used, at its saved version, by the
next conversation in that namespace, as our run log records". The UI half is D3's; everything
below the panel is tested here, deterministically, with D1's harness: start `dr-acp --home <tmp>`
(no `--config`, so `LibraryCatalog`) over stdio with D1's `ShimConnection`, and `FakeOpenAI`.

1. `put_decomposition(…, namespaces=["router"], use_when="comparing many courses")` → v1.
2. `session/new`, set namespace `router`: the `available_commands_update` lists
   `summarize-then-rank` with description `comparing many courses`.
3. A prompt: `run.start.source.versions.decompositions["summarize then rank"] == 1`,
   `run.start.namespace == "router"`, and the fake's first request contains the decomposition's
   first user message among the examples.
4. Edit it (v2); a new session's run records 2, and its first request carries v2's text, not v1's.

### 7.4 Live tier (Gate B; `@pytest.mark.live`, skipped without `OPENAI_API_KEY`)

Spec §4 layer 5, "D2: import, edit, version, materialize and run", on gpt-6-luna through a config of
our own (D1's `docs/configs/advising/main.yaml`, which uses `base_url
https://api.openai.com/v1` and `api_key_env OPENAI_API_KEY`):

1. `Library.open(tmp)`, `import_config(advising)`.
2. Save a decomposition `first course` in `advising` (v1), then edit its worked example (v2);
   assert `history` shows v2 then v1.
3. `materialize(namespace="advising")`; assert the manifest records `first course: 2`.
4. `dr <dir>/main.yaml "Which course must a student finish before CS102?" --run-dir <tmp>`; assert
   exit 0, the answer names `CS101`, and the root agent's node log in the run directory carries
   v2's example text and not v1's.

Cents per run.

### 7.5 Repository wiring D2 adds

- `pyproject.toml` (D1's): dependencies `starlette>=0.40` and `uvicorn>=0.30` (both already in
  deep_reasoner's resolved environment through chromadb, declared here because we import them);
  dev group `httpx` (Starlette's `TestClient`); script `dr-library =
  "deep_reasoning.library.cli:main"`. `starter.yaml` ships inside the package (hatch includes it, as
  D1's `prices.yaml`).
- D1's `testing/fake_model.FakeOpenAI` gains `POST /v1/embeddings` (a fixed vector per input). This
  is D1's test helper, not a seam; if D1's Implementer prefers, D2 keeps its own ten-line fake.
- `.github/workflows/ci.yml` (D1's): a step that checks out deep_reasoner_beta at the pin into
  `$RUNNER_TEMP/deep_reasoner_beta` with the read token D1 already needs, and sets
  `DR_BETA_CHECKOUT`.
- The live tier runs in D1's on-demand workflow with the same `OPENAI_API_KEY` secret.

---

## 8 · What D2 relies on

The Conductor turns these into Expectation rows at merge, with the merged `file:line` on our side.

**deep_reasoner (`d7334ae`)**

| # | Behaviour relied on | Their code | Ours |
|---|---|---|---|
| L1 | `load_cli_config(path, schema=V2Config)` composes `_compose` (each entry relative to the file naming it), validates, and stamps `config_path` | `config.py:454–481`; conflit 0.1.4 `config.py:178–234` | `configdir.read_config` |
| L2 | `V2Config`/`MainConfig` fields, `extra="allow"`, and `model_dump(exclude_unset=True)` keeping extras | `config.py:355–440`, `v2/cli.py:80–93` | the profile |
| L3 | `NamespaceConfig`, `Decomposition`, `ChatMessage` with `extra="forbid"`; `Decomposition.messages` `min_length=1` | `namespaces.py:63–88`, `prompt_config.py:18–29` | `shapes.py` |
| L4 | `load_namespaces_from_dir` names a file by its `name:` or its dotted path; `build_registry` layers dir then inline by name; `build_namespace_registry` seeds root's `repl` from `cfg.repl` | `namespaces.py:754–797`, `v2/cli.py:289–306` | import, materialize, effective |
| L5 | `NamespaceRegistry.resolve`'s rules: `repl`, `reasoner`, `spawn` nearest wins; decompositions accumulate, child wins by name; `tools` ordered union; `vars` shallow merge; `system_suffix` joined root to leaf | `namespaces.py:272–320` | `effective.py` (sources); E7 |
| L6 | `dr` resolves a relative `namespaces_dir` against the config's directory; `factory_from` against `config_path`; every other path in a tool block against the working directory | `v2/cli.py:696–697`, `tools/base.py:329–366, 186–196` | materialize layout |
| L7 | `make_tools`: a tool block's `factory`, `factory_from` and parameters; a default `llm` tool when `model` is set | `v2/cli.py:125–180` | tools, `check()` |
| L8 | Top-level `decompositions` are searched only as the opening pool; agents' examples are their namespace's | `v2/cli.py:350–356`, `v2/agent.py:673, 991` | §2.1 |
| L9 | `find_decomposition`'s message for an unknown name | `v2/decompositions.py:117–132` | §4.7 freshness |
| L10 | `code(text, start=, end=)` extracts the last `<repl>` block into `.source`, raising `NoCodeBlock` | `v2/messages.py:288–307` | the FinalAnswer warning |
| L11 | `write_fake_claude_cli` | `mocks.py:357` | E7 level 2 |

**D1 (committed on `v1-dr-acp`, `21c2c7a`)**: `acp/catalog.py`'s `Catalog`, `CatalogSnapshot`,
`CommandEntry`, `RunSource`, `ConfigCatalog`, `load_dr_config`, `slug`; `acp/runlog.py`'s `Home`;
`tests/conftest.py`; `testing/fake_model.FakeOpenAI` and `testing/client.ShimConnection` (§7.3);
`run.start.source` recording `RunSource.versions` (D1 §4.4).

**The agent-server (SDK fork `91430aa`)**

| # | Behaviour relied on | Their code |
|---|---|---|
| B1 | An App backend's argv may use only `{port}`, `{data_dir}`, `{artifact_dir}`; its executable must be inside `{artifact_dir}`; it inherits only `LANG`, `LC_ALL`, `LC_CTYPE`, `PATH`, `TMPDIR`, `TZ` | `canvas_extensions/manifest.py:121–160`, `backend.py:38–40, 340–352` |
| B2 | Readiness is `GET <health.path>` (default `/health`) on 127.0.0.1, 30 s by default | `manifest.py:112–117`, `backend.py:420` |
| B3 | The bridge strips `/app-backends/<name>`, decodes the path once, refuses `.`, `..` and `\`, and forwards to `/<path>` | `canvas_extensions/bridge.py:322–343, 448–468` |
| B4 | The bridge authenticates the browser with a cookie and requires the ingress `Origin` for unsafe methods; the backend receives no credential | `bridge.py:448–468`; `_BackendTarget.api_key` unused (`:58–62`) |
| B5 | A backend is started in its own session and stopped by process group | `backend.py:507, 545` |

---

## 9 · Open items, for the Conductor

1. **Every Canvas App backend is unauthenticated loopback HTTP** (B4). D2 refuses other users'
   connections on Linux (decision K) and has no check on macOS. The generic fix is upstream-shaped
   and small: the backend manager passes a per-launch secret through a new `{token}` argv
   placeholder and the bridge sends it as a header on every forwarded request. Whether S2 takes it
   is the Conductor's call; D2 would then check the header everywhere and keep the Linux check as
   defence in depth.
2. **The starter's model and provider** (decision M) are provisional: gpt-6-luna on OpenAI,
   `api_key_env: OPENAI_API_KEY`, matching §4's live tier and D1's advising config. D5's key proxy
   overrides `base_url` per run anyway. Michael or D5 picks the default.
3. **D1 §10 item 6, "offer only programs as slash commands"**, is not designed in: D2 offers every
   decomposition, as D1 §4.6 decided. If wanted, it is one `menu` column and one filter in
   `LibraryCatalog.snapshot`, with no change to D1's shapes.
4. **Branch base.** D2's code needs D1's skeleton: `pyproject.toml`, `tests/conftest.py`,
   `acp/catalog.py`, `acp/runlog.py`'s `Home` (all on `v1-dr-acp` at `21c2c7a`). `v1-library-store`
   is at `29fb4df`, with none of them. Recommended: base the implementation on `v1-dr-acp` (or on
   `self-hosted-v1` once D1 merges); D2's only edits to D1's files are those listed in §4.7 and
   §7.5.
5. **`$DR_HOME` on NFS** (§4.2): a lab user whose home directory is NFS-mounted gets
   `NETWORK_FS` until `DR_HOME` points at local disk. D5's setup should choose a local home in that
   case and write it into the App backend's argv and `dr-acp`'s environment.
6. **Packaging `dr-library serve` inside `{artifact_dir}`** and writing the App manifest's argv
   with `--home` are D3's and D5's (spec §2's deferred list); D2 provides the command.
7. **Tool factory files are captured one by one.** A factory that imports a sibling module, or
   reads a file beside itself, loses it on import; two tools naming one file become two copies, so
   module-level state is no longer shared between them (`tools/base.py:318`). Nothing in the corpus
   does either. D4 may want to say so in its editor.
8. **Renaming** is not an operation in v1 (§4.5). D3 decides whether its editor lets the name
   change before the first save only.
9. **D3's mock-up text** "messages: List should have at least 1 item" is pydantic's message
   shortened; the API passes `List should have at least 1 item after validation, not 0` unchanged.
10. **`kg` tools anchor document paths written into a saved layer on `config_path`**
    (`tools/base.py:193–196, 215–216`); under `dr-acp` that is the run's own config directory, so a
    layer saved in one conversation and loaded in another resolves those document paths against a
    different directory. Data-file paths themselves are relative to the working directory and are
    unaffected. Worth a line in D4's docs; not worked around.

---

## Appendix A · Signature index

Every public name, by module, with the section that gives it in full.

| Module | Names | § |
|---|---|---|
| `store.py` | `Kind`, `MIGRATIONS`, `NETWORK_FILESYSTEMS`, `Row`, `create`, `connect`, `migrate`, `current_rev`, `heads`, `history`, `Writer` (`rev`, `head`, `heads`, `add`), `write` | 4.2 |
| `shapes.py` | `NAMESPACE_NAME`, `SPLIT_KEYS`, `TOOL_DIR`, `YAML_WIDTH`, `canonical_yaml`, `slug`, `deep_reasoner_build`, `Shaped`, `validate_namespace`, `validate_decomposition`, `validate_tool`, `validate_profile`, `namespace_config` | 4.3 |
| `records.py` | `Saved`, `ProfileRecord`, `NamespaceRecord`, `DecompositionRecord`, `ToolRecord`, `HistoryEntry`, `LibraryState`, `Entry`, `Change`, `ImportReport`, `DecompositionMeta`, `Manifest`, `FieldError`, `Problem`, `ValidationResult`, `LibraryError`, `LibraryValidationError`, `LibraryNotFound`, `LibraryConflict`, `LibraryRefused`, `LibraryImportError` | 4.4 |
| `library.py` | `LIBRARY_FILE`, `library_path`, `Library` (`open`, `rev`, `state`, `profile`, `namespaces`, `namespace`, `decompositions`, `decomposition`, `tools`, `tool`, `history`, `effective`, `check`, `validate`, `put_profile`, `put_namespace`, `put_decomposition`, `put_tool`, `delete`, `import_config`, `materialize`) | 4.5 |
| `configdir.py` | `ConfigParts`, `read_config`, `write_config` | 4.6 |
| `catalog.py` | `LibraryCatalog` (`snapshot`, `materialize`) | 4.7 |
| `api.py` | `create_app`, `same_user_peer` | 4.8 |
| `cli.py` | `main` | 4.8 |
| `effective.py` | `Sourced`, `SuffixPart`, `EffectiveTool`, `EffectiveDecomposition`, `Effective`, `effective` | 4.9 |
| `texts.py` | every name in §4.10's table | 4.10 |
