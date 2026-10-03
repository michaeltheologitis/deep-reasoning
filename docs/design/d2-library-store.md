# D2 · Library store — design

**TASK-5** · System Designer · branch `v1-library-store` · against the approved spec
[TASK-1](https://app.notion.com/p/3ed62fb22237814ab425c81b3844f012) (D2 in full, §2, the parts of
D3, D4 and §4 that use the store; save-a-run is out of v1) and D1's design v2
(`f281109:docs/design/d1-dr-acp.md`, §4.4 and §4.6, the seam this design implements).
**Pinned against:** deep_reasoner_beta `d7334ae6ea884617a377d9f1ce872530d898484c` (conflit 0.1.4,
pydantic 2.13.5 as its lock resolves them) · D1's committed `src/deep_reasoning/acp/catalog.py` at
`21c2c7a` (identical to D1 §4.6) · the SDK fork at `91430aa` (upstream `53a4bc5` plus the ASE commit;
the Canvas App backend manager and bridge line numbers below) · SQLite 3.45 (the stdlib's; `STRICT` tables need 3.37 or later).

**Matches the build at `90044f0`** (v2): D2's code (`8d24b56` … `5158693`), D1 at `21f4a8b` merged
under it (`da58a33`), and `dr-acp` serving the Library without `--config` (`90044f0`). Commits after
it on this branch change only `docs/`.

## Gate B: what to read

**About 50 minutes, in this order.** The codebase stays closed. The Gate B set is this doc, D2's
as-built document (`as_built/d2-library-store.md`, the Cartographer's; it also
reports E7's measured results) and the two runs below. Everything after §3 is kept whole as the
reference D3, D4 and D5 build against (Michael: don't force compression); Gate B does not need it.

| # | Read | What it gives you | Minutes |
|---|---|---|---|
| 1 | This section and the v2 revision line below it | where the proof is, and which sentences of v1 changed | 7 |
| 2 | §1 | what the Library is, and the decisions under it (K grew in v2) | 10 |
| 3 | §3.1 | where the design departs from the spec: unchanged since v1, accepted by Michael on 2026-10-02 | 4 |
| 4 | §3.2 | what the build changed, each with its reason and the test that pins it | 12 |
| 5 | §6.1 and §6.2 | the HTTP contract D3 and D4 build against | 5 |
| 6 | Open the two runs below | that they are green at `90044f0` | 2 |
| 7 | `as_built/d2-library-store.md` | what exists, its divergences, and E7 as measured | 10 |

**One thing to rule on: size.** Michael accepted D2 at "about 1.9k lines with tests" (spec,
"Rulings at design, 2026-10-02" (2), from §3.1 item 16's estimate). The build is **2,684 lines of
code and 2,576 of tests** at `90044f0` (2,239 and 2,203 non-blank), about 2.8 times that. The
breakdown by file is §3.2 B20. The build recorded no reason for the growth; the estimate was this
design's. The Scout and the Refactorer, after Gate B, are where it shrinks.

**The evidence.** Both runs are at `90044f0`, the branch's last commit that touches code.

- **CI**, [run 37085759535](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37085759535):
  `ruff check`, `ruff format --check` and the deterministic suite, **515 passed** (the 4 live tests
  deselected, nothing skipped), in 5 min 19 s. deep_reasoner_beta's configs are checked out at
  `d7334ae` (`DR_BETA_CHECKOUT`), so E7 runs in full. 285 of the 515 are D2's (`tests/library/`);
  no test calls a model.
- **Live tier**, [run 37085761405](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37085761405):
  **4 of 4 passed** on gpt-6-luna in 47 s, D2's
  `tests/library/test_live.py::test_an_edited_decomposition_reaches_a_real_run_at_its_saved_version`
  among them (the other three are D1's). It runs only on demand, as `.github/workflows/live.yml`.

**Which tests carry which property.** Each test's name states the property it pins. Files are under
`tests/library/`; `[…]` is a parametrization.

| Property | Tests |
|---|---|
| **E7 level 1.** Every config `dr` accepts round-trips: imported, materialized and loaded with `dr`'s own loader, the `V2Config`s are equal but for what materialize moves, every namespace resolves equal, tool files are byte-identical, and the copy re-imports to the same rows and makes no revision. **Measured at `d7334ae`: 39 YAML files; the 37 that load round-trip; the 2 namespace files `V2Config` refuses are asserted refused, with that reason; their directory is covered by a composed config the test writes.** | `test_roundtrip.py::test_every_config_dr_accepts_round_trips[39 files]`; `::test_the_example_namespaces_directory_round_trips`; the guard `::test_the_corpus_is_read_in_ci` (fails in CI without the corpus) |
| **E7 level 2.** `dr` gives the same exit code, last line of stdout and first model request on the original and on its copy, against a fake OpenAI, deep_reasoner's fake Claude CLI and no network. **Measured: equal on all 38 cases (the 37 configs and the composed one). 19 reach the fake's answer, `done`; the 2 Claude-backbone configs end at the fake CLI's end; both sets are pinned in the test, so a broken fake cannot pass by failing everywhere. The other 17 exit 1 identically on both sides; for them the test asserts equality only.** | `test_roundtrip.py::test_dr_answers_the_same_from_the_original_and_its_copy[38 cases]` |
| **D3's falsifier, at the store** (spec D3: a decomposition saved in Create decomposition is used, at its saved version, by the next conversation in that namespace, as our run log records). Saved, and saved then edited, each followed by a new conversation through `dr-acp` without `--config`, over stdio: the slash menu lists it with its use-when line; `run.start` records the namespace and the saved version; the model is sent that version's text and not the other's; the session index names the Library. | `test_acp.py::test_a_saved_decomposition_reaches_the_next_conversation_in_its_namespace[saved, edited]`; the same below `dr-acp`'s front (`LibraryCatalog` and `dr`, two runs, v1 then v2): `test_catalog.py::test_a_saved_decomposition_reaches_the_next_conversation_in_its_namespace` |
| **The HTTP contract** (§6): every route, its status and its JSON shape; errors carry code, message and details; a `PUT`'s path key must be the YAML's own; 201 on create, 200 on update | `test_api.py::test_every_read_answers_its_records[…]`, `::test_every_write_route`, `::test_creating_a_decomposition_answers_201_and_updating_200`, `::test_validate_answers_200_even_when_invalid`, `::test_errors_carry_code_message_and_details`, `::test_the_path_key_must_match_the_yaml[…]`, `::test_a_slug_with_spaces_in_the_name_round_trips`, `::test_records_carry_yaml_and_parsed_data`, `::test_health_reports_the_revision_and_default_namespace`, `::test_export_is_a_zip_of_a_materialized_directory` |
| **Who may call it** (decision K, §3.2 B1): another OS user's connection, a `Host` other than loopback at the backend's port, and a `PUT` or `POST` body not sent as JSON are refused; a real `dr-library serve` with only an App backend's six variables answers `/health` and refuses a rebound `Host` | `test_api.py::test_another_users_connection_is_refused`, `::test_same_user_peer_reads_the_client_sockets_owner[…]`, `::test_a_request_addressed_to_another_host_is_refused[…]`, `::test_a_body_that_is_not_sent_as_json_is_refused[…]`; `test_cli.py::test_serve_answers_health_on_loopback` |
| **Every save an immutable version** (decision A, L) | `test_store.py::test_versions_and_revisions_cannot_be_updated_or_deleted[…]`, `::test_a_save_that_changes_nothing_makes_no_revision`, `::test_two_processes_saving_at_once_both_land`; `test_library.py::test_every_save_is_a_new_version`, `::test_a_stale_base_version_is_a_conflict_carrying_the_head`, `::test_deleted_and_recreated_continues_its_version_numbers` |
| **Live tier**, on gpt-6-luna (spec §4 layer 5, "D2: import, edit, version, materialize and run") | `test_live.py::test_an_edited_decomposition_reaches_a_real_run_at_its_saved_version`: imports D1's advising config, saves `first course` and edits it (history v2, v1), refuses the spec's failure cell without making a revision, materializes (manifest `first course: 2`) and runs `dr`: exit 0, the answer names CS101, and the root's node log carries v2's example, not v1's or the refused one |

§7.2 maps every test file.

**Revisions** (newest first; the Gate B reader approved the previous one, so each line says which
sentences to stop trusting):
- 2026-10-03 · v2 · brought in line with the build at `90044f0`, after Proof Green. Stop trusting:
  §1.1 decision K (B1); §4.2's temporary file name, `connect`'s signature and the heads query's
  order (B8); §4.4's error classes and where `Kind` lives (B3, B8, B10); §4.5's `LIBRARY_FILE` and
  `library_path` (now §4.7, B6), `validate`'s signature (B7) and the error class of a broken
  invariant (B3); §4.6's `main.yaml` (B5) and the import's write order (B11); §4.8's endpoints and
  error mapping (B1, B2, B9); §4.10's table (B4); §6.1's status codes (B1–B3); §7.1's working
  folder and counts (B16, B17); §7.3's harness (B14); §7.4 (B18); §7.5 (B15, B19); §3.1 item 16's
  size (B20); §9 item 4 (resolved). Added without changing earlier sentences: the Gate B section;
  §3.2; §8's B6 (the bridge drops `Host`); §9 items 11–13. §3.1 (v1's §3) keeps every item as
  written, with marked v2 notes on items 12 and 16; Michael accepted it on 2026-10-02 (spec,
  "Rulings at design" (2)). Every change is listed, with its reason, in §3.2.
- 2026-10-02 · v1 · first full-depth version.

**Where this file lives, and why nothing trips over it.** `docs/design/` on the task branch. The
repo has no docs site; once D1's `pyproject.toml` is on the branch, pytest collects `tests/` only
(`testpaths = ["tests"]`), the wheel is built from `src/deep_reasoning` only, the sdist excludes
`docs/`, and ruff excludes `docs` (D1 §8.5). The PR split leaves it behind.

**Reading guide.** Gate B: the section above. D3 and D4 design against §6, which is their
contract, and §2, which says what the records mean. D1's Implementer reads §4.7. D5 reads §4.8 and
§4.6 (the command, the export). The Implementer and the Cartographer read everything; Appendix A
indexes every signature.

**What was verified for v1 (2026-10-02, in a scratch environment outside every repo):**
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
| I | **WAL mode, `BEGIN IMMEDIATE` per save, a fresh connection per operation.** | The App backend, every `dr-acp` and `dr-library import` share one file; writers serialize, readers see one consistent revision and never block a writer. The App backend runs each handler on Starlette's thread pool (§4.8), and a connection per call needs no locking of ours. | A long-lived connection with a lock; a server process owning the file (a second service, the thing spec §2 rejected). |
| J | **Validation is deep_reasoner's own models at every save, and again over every head at every materialize**, under the installed deep_reasoner. A head that stops validating after a pin bump is a named problem (`GET /problems`) and blocks materialize; it is never rewritten silently. | The spec's "stored YAML records the commit it was validated against and the importer migrates it": the record is kept per version; a migration can only be written once Dean's change exists, and E7 on the new pin is what shows one is needed. | Re-validating only at save (a pin bump would surface as a failed run). Silent best-effort rewriting. |
| K | **The HTTP API has no import, binds 127.0.0.1 only, and refuses every request that is not plainly the user's own** (v2, §3.2 B1): on Linux a TCP peer that belongs to another OS user; everywhere a `Host` other than `127.0.0.1:<port>` or `localhost:<port>`; and a `PUT` or `POST` body not sent as `application/json`. | A Canvas App backend is unauthenticated loopback HTTP: the agent-server's bridge authenticates the browser, but anything on the machine can reach the port directly. On a shared lab machine another user could otherwise write a tool (code that runs as you at your next conversation) or make the backend import a config whose `factory_from` names your private files. Import stays a command the user runs. The user's own browser is the other way in, as the user: a page on another site that rebinds its DNS name to 127.0.0.1 can read the answers, but its `Host` still names its site; a cross-site form or `text/plain` fetch can `POST` without a CORS preflight, and a JSON body cannot. The bridge's own requests pass, since it sends `Host: 127.0.0.1:<port>` (§8, B6). | Trusting loopback. A token we cannot deliver: the bridge sends the backend no credential (§8, B4). |
| L | **Optimistic concurrency.** Every write may carry `base_version`, the head version the edit started from (`0`: must not exist yet); a mismatch is a conflict that carries the current head. | Two conversations can have the panel open at once; D3's "'catalog lookup' is already in router (v2)" needs the head. Scripts and import omit it and write unconditionally. | Locks held by a panel. Last write wins silently. |
| M | **A new Library starts from a starter config shipped in the package**, imported through the same import path as any config: a `root` namespace with the `llm` tool and a profile with a model, a client and a short system prompt of our own. | Spec §1's first "done when" (install, ask) needs a Library that can run before the user has written anything. One code path: the starter is just the first import. | An empty Library (the first question fails with "LLM requires a model"). Seeding in D5's setup (every test and every `dr-acp --home` would need the same seeding). |

### 1.2 What D2 owns, and its seams

- **Owns:** the `deep_reasoning.library` package; the `dr-library` command (`serve`, `import`,
  `export`); the SQLite schema and its migrations; import; materialize and export; the HTTP API;
  `LibraryCatalog`; the effective (inherited) view D3's Namespaces tab shows; E7.
- **Seam to D1** (§4.7): implements D1's `Catalog` protocol unchanged. D1 §4.6 already says
  "nothing in D1 changes when D2 lands except the default in `cli.py`"; D2 makes that change
  (`dr-acp` without `--config` uses the Library at `--home`; built in `90044f0`, §3.2 B13). **No
  change to the Catalog seam is needed**, and none was made.
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
  every kind and every write. So a save that omits `use_when` or `hint` erases it, and D3 always
  resends both, from the record it opened (§3.2 B21).

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

## 3 · Departures from the spec, and what the build changed

§3.1 is where this design departs from the approved spec (v1, unchanged in v2). §3.2 is what the
build changed in this design (v2). None is a re-scope.

### 3.1 Where this design departs from, or adds to, the approved spec

Each is a refinement inside D2's scope, not a re-scope. **Accepted by Michael on 2026-10-02**
(spec, "Rulings at design, 2026-10-02" (2): "D2's departures from this spec, listed in its
design's §3 (555472b on v1-library-store), are accepted; the visible ones: imported YAML loses its
comments and _compose structure, a Library on a network filesystem is refused, a starter Library
ships, dr-acp reads the Library in-process, and D2 grows to about 1.9k lines with tests"). The
build kept every one; item 16's size did not hold (§3.2 B20).

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
12. **No HTTP import; a same-user check on Linux** (decision K; v2 adds the `Host` and media-type
    rules of §3.2 B1, which the spec does not touch: it says nothing of the backend's callers).
13. **The effective view, validation without saving, and the problem list are D2 endpoints**
    (§6). D3 needs them and has no Python; resolution must be deep_reasoner's own.
14. **A starter Library** (decision M), with a provisional model and provider (§9 item 2).
15. **`$DR_HOME` on a network filesystem is refused** (§4.2): SQLite's WAL mode is unsafe there,
    and Linux lab machines often mount home directories over NFS.
16. **Cost.** About 1.1k LOC of code and 0.8k of tests, roughly 6 h at Gate C, against the
    spec's ≈1.2k LOC with tests and ≈4 h. The growth is items 2, 3, 12 and 13 (the effective view
    and validation were nobody's: D3 has no Python), and the invariants of §2.5. *(v2: built at
    2.7k and 2.6k, §3.2 B20.)*

### 3.2 Changed by the build (v2)

Each was checked against the code at `90044f0` and folded into the section named. B1–B5 change
behaviour v1 specified; B6–B12 decide what v1 left open or move a name; B13 is D2's edit to D1's
files; B14–B19 are how the tests prove it and the wiring; B20 is the size; B21 restates one rule
for D3. Where the build recorded no reason, the reason given is marked as this design's reading.

**Behaviour**

- **B1. The request guard: `Host` and media type, beside the same-user check** (§1.1 K, §4.8,
  §6.1). Every request passes three checks, in this order, before it reaches a route: on Linux,
  the TCP peer is this OS user's (v1's `FORBIDDEN_PEER`, 403 `forbidden`); its `Host` is
  `127.0.0.1:<port>` or `localhost:<port>`, the port being the one the backend serves on, else 403
  `forbidden` with `FORBIDDEN_HOST`; and a `PUT` or `POST` carries `Content-Type:
  application/json` (a `charset` parameter is allowed), else 415 `unsupported_media_type` with
  `NOT_JSON`. The checks are ASGI middleware ahead of routing, so a refused request reaches no
  route, an unknown path included. *Why:* the same-user check cannot see an attack through the
  user's own browser, which connects as the user. A page on another site that rebinds its DNS name
  to 127.0.0.1 is same-origin with the backend and can read its answers, but its `Host` still
  names its own site. A cross-site form or `text/plain` fetch can `POST` without a CORS preflight
  (it cannot read the answer, but it can write); a JSON body always needs one, which the backend
  never grants. The only `POST` today is `/validate`, which writes nothing; the rule covers D4's
  `POST /tools/{name}/check` from the start. *Decided by:* the Conductor, during the build.
  **It does not block the bridge:** `proxy_app_backend_http` forwards through `proxy_http`, which
  drops the browser's `Host` as hop-by-hop (`docker_runtime/proxy.py:32–50`, "recomputed by
  httpx") and sends the request with httpx to `http://127.0.0.1:<port>` (`bridge.py:366–369, 467`;
  the address `backend.py:638–643` returns), so the backend sees `Host: 127.0.0.1:<port>`; the
  readiness probe uses the same address (`backend.py:420`), and `Content-Type` is forwarded (§8
  B6). D3's design measured the same against a replica of the bridge (`ab6f2ec` on `design/d3`).
  *Pinned by:* `test_api.py::test_a_request_addressed_to_another_host_is_refused[…]` (four
  foreign `Host`s, `[::1]:<port>` among them, then `localhost:<port>` answered),
  `::test_a_body_that_is_not_sent_as_json_is_refused[PUT, POST × text/plain, form, none]` (no
  revision made; the same body as JSON answered), `test_cli.py::test_serve_answers_health_on_loopback`.
- **B2. Request bodies are typed: an unknown field or a wrong type is 400** (§4.8, §6.1, §6.2).
  Each body is a pydantic model with `extra="forbid"`: `yaml` and `base_version` on every `PUT`,
  plus `decompositions` (profile, namespace); `use_when`, `hint`, `namespaces`, `top_level`
  (decomposition); `source`, `granted_in` (tool); and `kind`, `yaml`, `name`, `source` for
  `POST /validate`. A body that is not JSON, lacks `yaml`, carries a field the route does not
  know or a value of the wrong type is 400 `bad_request`, with `BAD_REQUEST` followed by pydantic's
  first message; so is a `?base_version=` that is not a whole number. v1 said only "a body that is
  not JSON or lacks `yaml`". *Why (this design's reading):* with §2.3's replace rule, an ignored,
  misspelt `use_whn` would erase the stored use-when line. *Pinned by:*
  `test_api.py::test_errors_carry_code_message_and_details` (`yml`, `base_version: "two"`,
  `?base_version=x`).
- **B3. Error classes v1 left open** (§4.4, §4.5, §6.1). v1's §5.1 said a broken invariant is
  "`LibraryValidationError` / `Refused`" without saying which. Built:
  - **422 `invalid`** (`LibraryValidationError`; `message` is the sentence itself, and `errors`
    holds one `FieldError` with it): `SLUG_TAKEN` (`loc` `name`), `PARENT_MISSING` (`name`),
    `DEFAULT_MISSING` (`entry_namespace`), `UNKNOWN_DECOMPOSITION` and `LISTED_TWICE`
    (`decompositions`), and a name in `namespaces` or `granted_in` that is not a live namespace
    (`NOT_FOUND`'s sentence; `loc` `namespaces` or `granted_in`).
  - At import, two names with one slug inside the imported config are found while reading it,
    before any transaction: `SLUG_TAKEN` as 422 `import_failed`, like every `IMPORT_*` sentence. A
    clash with a decomposition already in the Library is the invariant's 422 `invalid`.
  - **409 `refused`** (`LibraryRefused`): `DEST_NOT_EMPTY` (materialize, export), beside v1's
    `REFUSE_ROOT`, `REFUSE_DEFAULT` and `REFUSE_CHILDREN`. A save that left the profile or `root`
    not live would also be `REFUSE_ROOT`; none can, since `delete` refuses `root` first.
  - **YAML that does not parse, or is not a mapping**: 422 `invalid`, whose message is `this YAML
    is not a valid deep_reasoner {model}:` and then the parser's message (or `NOT_A_MAPPING`) on a
    line of its own (`loc` is empty).
  - 403, 415 and 400 as B1 and B2 say; 404 `NO_VERSION` and `NO_REVISION` as B4 says.

  *Why (this design's reading):* a broken invariant is a fault in what was sent, which D3 shows
  beside the field (`errors[].loc`) as it does a validation error; `refused` stays for a request
  that is well formed but forbidden by the Library's state. *Pinned by:*
  `test_library.py::test_a_namespace_needs_its_parent`,
  `::test_the_default_namespace_must_be_in_the_library`, `::test_two_names_with_one_slug_are_refused`,
  `::test_putting_a_namespace_sets_its_list_only_when_given` (unknown and listed twice),
  `test_materialize.py::test_a_non_empty_destination_is_refused`,
  `test_shapes.py::test_a_document_that_is_not_a_mapping_is_invalid[…]`. **Not pinned:** a name
  in `namespaces` or `granted_in` that is not a live namespace (§9 item 13).
- **B4. Five new sentences, and two renamed** (§4.10). `FORBIDDEN_HOST` (B1), `NOT_JSON` (B1),
  `BAD_REQUEST` (B2), `NO_VERSION` (404 for `GET …/versions/{n}` when the entity has no version
  `n`) and `NO_REVISION` (404 when `state(rev=)`, `materialize(rev=)` or `export --rev` names a
  revision outside 1 … now; v1 would have failed on an empty unpacking). v1's `METADATA_IN_YAML`
  is two constants, `METADATA_USE_WHEN` and `METADATA_HINT`; `INVALID`'s line for an error
  without a location is `  {msg}`. One sentence lives outside `texts.py`: `base_version must be a
  whole number; got {raw!r}.` in `api.py` (§9 item 13). *Pinned by:*
  `test_library.py::test_a_revision_the_library_has_not_reached_is_not_found[0, 3]`, B1's and
  B2's tests.
- **B5. `main.yaml` carries `entry_namespace` only when it differs from the profile's** (§4.6).
  v1 wrote `entry_namespace: <namespace>` into every `main.yaml`. Now `main.yaml` is the profile as
  stored, and gains an `entry_namespace` only when the namespace asked for is not the profile's
  default. *Why:* a profile that never set `entry_namespace` came back from its own export with it
  set, so re-importing an export made a revision: on 27 of E7's 38 level-1 cases (the 26 corpus
  configs that never set it, and the composed one; measured again on 2026-10-03 by restoring v1's
  rule). *Pinned by:* `test_roundtrip.py::test_every_config_dr_accepts_round_trips[…]` (the
  re-import makes no revision); `test_api.py::test_export_is_a_zip_of_a_materialized_directory`
  (`?namespace=courses` writes it).

**Where v1 was silent, or the build moved a name**

- **B6. `library_path` and `LIBRARY_FILE` live in `catalog.py`** (§4.1, §4.5, §4.7);
  `library.py` imports them from there. The package exports them, `LibraryCatalog`, the records
  and v1's errors eagerly, and `Library` and `Effective` lazily (a module `__getattr__`). *Why:*
  `dr-acp` must find its library before it serves, without importing deep_reasoner, and
  `library.py` imports deep_reasoner at module level. *Pinned by:*
  `test_catalog.py::test_building_a_catalog_imports_nothing_of_deep_reasoner`.
- **B7. `Library.validate` takes `source=`** (§4.5). `POST /validate` already carried `source`
  (§6.2); a tool whose block names `factory_from` validates only with its source
  (`TOOL_NO_SOURCE` otherwise). **Not pinned** by a test (§9 item 13).
- **B8. Store details** (§4.2). The temporary file is `library.sqlite.<pid>-<8 hex>.new`
  (`secrets.token_hex(4)`), and its `-wal` and `-shm` are removed with it. *Why (this design's
  reading):* a pid alone is not unique among creators: two threads of one process, or two
  processes in different PID namespaces sharing one home, would race for one name.
  `connect(path, *, mounts=MOUNTS)` takes the mounts file, so the network-filesystem refusal is
  testable; connections are opened with `isolation_level=None`
  (every transaction is an explicit `BEGIN`) and `check_same_thread=False`. New helpers:
  `read(path)`, one read transaction, which every read method of `Library` is;
  `decomposition_named(conn, slug)`, the name last saved under a slug, deleted or not (so
  `GET /decompositions/{slug}/versions` works after a delete); `filesystem_type(path, *, mounts)`
  and `refuse_network_filesystem(path, *, mounts)`. `migrate` runs each migration under `BEGIN
  IMMEDIATE` and re-reads `user_version` inside it, so two processes migrating at once apply it
  once. **Creation order is the row id of each entity's version 1**, not its revision: the heads
  query selects it as `created` and orders by it. *Why:* one import creates many entities in one
  revision, which `created_rev` cannot order; the row id keeps the order they were written. `Kind`
  is defined in `records.py`, and `store.py` re-exports it. *Pinned by:*
  `test_store.py::test_heads_are_in_creation_order_within_one_revision`,
  `::test_a_second_creator_loses_and_leaves_nothing_behind`,
  `::test_a_library_on_a_network_filesystem_is_refused`.
- **B9. Endpoints are `async` wrappers that run the sync handlers in Starlette's thread pool**
  (§4.8). v1: "plain `def` functions, which Starlette runs on its thread pool". Each route is an
  `async def` that reads the body (for `PUT` and `POST`), then `run_in_threadpool(handler, request,
  body)`. *Why (this design's reading):* a sync endpoint cannot await `request.body()`; reading the
  body on the event loop and doing the SQLite work in the pool keeps decision I (a connection per
  call, no locking of ours). Whether a `PUT` answers 201 or 200 is read before the write, outside
  its transaction.
- **B10. Three error classes** (§4.4): `LibraryForbidden` (403 `forbidden`, B1),
  `LibraryBadRequest` (400 `bad_request`, B2 and `NAME_MISMATCH`), `LibraryNotJson` (415
  `unsupported_media_type`, B1), all in `records.py`, so the API's one handler maps every error.
- **B11. Import writes namespaces in the config's order** (§4.6): root, then the
  `namespaces_dir`'s, then the inline ones; v1 said parents before children. The invariants are
  checked once, at the end of the transaction (§2.5), so the order inside it does not matter to
  them; it sets creation order, which for one import is then the config's order (§2.6). *Pinned
  by:* `test_import.py::test_import_creates_every_entity_in_one_revision`.
- **B12. Smaller details.** `slug` is D1's own function, re-exported by `shapes.py`.
  `Library.decomposition` and `history` take a name or a slug. A materialize into an existing empty
  folder that fails empties it again (v1 said only that a folder it made is removed). New public
  names that only serve the above: `shapes.load_mapping`, `shapes.tool_file`,
  `shapes.FINAL_ANSWER`; `effective.chain`, `effective.resolved` (the tests rebuild deep_reasoner's
  resolve from them); `configdir.MAIN`, `MANIFEST`, `NAMESPACES_DIR`; `api.PROC_NET`, `JSON_TYPE`,
  `BODY_METHODS`; `library.STARTER`, `ROOT`, `PROFILE`; `cli.EXIT_ERROR`, `HOST` (Appendix A).

**D2's edit to D1's files**

- **B13. `dr-acp` serves the Library without `--config`** (§4.7), in `90044f0`. `acp/cli.py`
  builds `LibraryCatalog(library_path(options.home))` when `--config` is absent (`cli.py:93–97`);
  D1's `NEEDS_CONFIG` sentence and exit 2 are gone. `acp/session.py` writes the session index's
  `source` as `{"kind": "library", "library": <path>}` when the `RunSource`'s versions name a
  library (`session.py:198–203`). D1's `test_without_a_config_dr_acp_exits_2_and_says_why` became
  `test_without_a_config_dr_acp_serves_the_library_at_its_home`, and D1's test harness starts
  `dr-acp` without `--config` when given `config=None`. *Pinned by:* that test, and B14's.

**Tests and wiring**

- **B14. §7.3 runs end to end through `dr-acp`** (`tests/library/test_acp.py`), with D1's
  harness (`dr_acp(None, home)`, stdio) and D1's own `FakeOpenAI`, as v1's §7.3 described. The
  build first tested it below `dr-acp`'s front (`test_catalog.py`, `LibraryCatalog` and `dr`);
  `90044f0` added the `dr-acp` case once the default existed. Both are kept. The two cases are
  separate conversations: saved (v1), and saved then edited before the session opens (v2).
- **B15. D2 keeps its own fake OpenAI** (`tests/library/fake_openai.py`, 84 lines: chat
  completions, `/v1/embeddings` with a fixed vector, each chat request recorded) instead of adding
  embeddings to D1's (§7.5). v1's §7.5 allowed either; this one leaves D1's test helper unchanged.
  E7 and `test_catalog.py` use it; `test_acp.py` uses D1's.
- **B16. E7 level 2 runs from a copy of the corpus folder, not a symlink, with
  `PYTHONDONTWRITEBYTECODE=1`** (§7.1). Also: every proxy variable points at a closed port
  (`127.0.0.1:9`, `NO_PROXY` loopback), so nothing but the fake is reachable, and the providers'
  keys are dummies (`DAYTONA_API_KEY` stays unset, so a Daytona REPL fails before the network).
  *Why:* whatever a tool writes beside its data (`rag`'s embeddings sidecar) would land in the
  checkout through a symlink; the original's `factory_from` file is imported in place, and Python
  would write `__pycache__` beside it, in the checkout.
- **B17. The corpus, counted** (§7.1). 39 YAML files at `d7334ae`, not 40; 37 load, not 38.
  Level 2 runs all 37 and the composed one (v1's prototype ran the 33 outside `namespaces/`).
  19 reach the fake's answer, not 17 (v1 expected the harness to raise the 17; which of its
  changes did is not recorded); the 2 Claude-backbone configs end at the fake CLI's
  end (`The Claude session ended without calling FinalAnswer, …`); 17 exit 1 identically on both
  sides. Measured in CI at `90044f0` (equality on all 38) and again locally on 2026-10-03 with the
  test's own helpers (the outcome of each). *Pinned by:* `ANSWERING` and `CLAUDE_BACKBONE` in
  `test_roundtrip.py`.
- **B18. The live tier asserts two more things** (§7.4): the spec's failure cell (a use-when line
  in the YAML) is refused with its exact message and makes no revision, and the root's node log
  carries neither v1's example nor the refused one. It opens the Library with the starter (the
  default), then imports the advising config over it.
- **B19. Wiring** (§7.5). No CI change was needed: D1's `ci.yml` already checks deep_reasoner_beta
  out at the pin into `${{ github.workspace }}/deep_reasoner_beta` (v1 said D2 adds the step, at
  `$RUNNER_TEMP`) and sets `DR_BETA_CHECKOUT`; ruff checks `src` and `tests` only, so the checkout
  is not linted. `pyproject.toml` declares `starlette>=0.40`, `uvicorn>=0.30`, `httpx` (dev) and
  the `dr-library` script, as v1 said. The live tier runs in D1's `live.yml`.

**Size**

- **B20. About 2.7k lines of code and 2.6k of tests, against v1's 1.1k and 0.8k** (§3.1 item 16)
  and the 1.9k with tests Michael accepted. At `90044f0`, all lines (non-blank in brackets): code
  2,684 (2,239), tests 2,576 (2,203). Code: `library.py` 748, `api.py` 379, `store.py` 334,
  `shapes.py` 236, `records.py` 228, `texts.py` 217, `configdir.py` 191, `effective.py` 124,
  `catalog.py` 83, `cli.py` 81, `__init__.py` 63 (and `starter.yaml`, 24). Tests, under
  `tests/library/` (B13's edits to D1's tests are not counted):
  `test_library.py` 384, `test_api.py` 378, `test_roundtrip.py` 238, `test_shapes.py` 220,
  `test_import.py` 215, `test_catalog.py` 171, `test_materialize.py` 170, `test_store.py` 144,
  `test_effective.py` 143, `test_cli.py` 131, `conftest.py` 104, `fake_openai.py` 84,
  `test_live.py` 82, `test_acp.py` 69, `corpus.py` 43. Michael rules on it at Gate B (§9 item 11).

**For D3 (no change; said again because D3 builds on it)**

- **B21. A `PUT` that omits `use_when` or `hint` erases it** (§2.3, as designed: absent, `null`
  and `""` all store no value). D3 always resends both, from the record it opened (D3's design,
  decision H). *Pinned by:* `test_library.py::test_use_when_and_hint_are_replaced_by_every_save`.

---

## 4 · Modules

### 4.1 Package layout

```text
src/deep_reasoning/library/
    __init__.py      re-exports: LibraryCatalog, library_path, LIBRARY_FILE, the records and v1's errors
                     eagerly; Library and Effective lazily, on first use (v2, §3.2 B6)
    store.py         SQLite: schema and migrations, connections, the writer, heads, history
    shapes.py        deep_reasoner's models, canonical YAML, name rules, slug, the build string
    records.py       Kind, ProfileRecord, NamespaceRecord, DecompositionRecord, ToolRecord,
                     HistoryEntry, LibraryState, ImportReport, Manifest, Problem, ValidationResult,
                     errors
    library.py       Library: the Python API (reads, writes, import, materialize, check)
    configdir.py     read_config (a dr config → parts) and write_config (a state → a directory)
    effective.py     inherited values and their sources (D3's Namespaces tab)
    catalog.py       LibraryCatalog: D1's Catalog over the Library; library_path, LIBRARY_FILE
    api.py           the Starlette app (§6), the request guard (same user, Host, JSON)
    cli.py           dr-library serve | import | export
    texts.py         every user-visible sentence (§4.10), in one place
    starter.yaml     a new Library's first import
tests/library/…      §7
```

deep_reasoner is imported at module level by `shapes.py`, `configdir.py`, `effective.py` and
`library.py`. `catalog.py` imports nothing of deep_reasoner or of the Library at module level (only
D1's `acp.catalog` and `acp.runlog`), and the package imports `library.py` only when `Library` is
first asked for, so
`dr-acp`'s start-up, which builds the catalog before it serves (D1 §4.2), stays as cheap as with
`ConfigCatalog`; the first `snapshot()` (in a thread) pays the import (≈1.4 s measured for
`deep_reasoner.v2.cli`). Importing deep_reasoner writes nothing to stdout (D1's R16).

### 4.2 `store.py`: the file

**Opening.** `connect(path, *, mounts=MOUNTS)` returns a `sqlite3.Connection` opened with
`isolation_level=None` (every transaction is an explicit `BEGIN`) and `check_same_thread=False`,
with `row_factory = sqlite3.Row`, `PRAGMA foreign_keys = ON`, `PRAGMA busy_timeout = 5000`,
`PRAGMA synchronous = FULL`. `migrate(conn)` applies `MIGRATIONS[user_version:]` in one
`BEGIN IMMEDIATE` transaction each, re-reading `user_version` inside it (two processes migrating at
once apply a migration once), and sets `user_version`; D4 appends to `MIGRATIONS` if it needs a
table. `read(path)` is one read transaction (`BEGIN` … `ROLLBACK`): every read method of `Library`
is one, so every query in it sees the same revision.

**Creating** a library is atomic, because the App backend and a `dr-acp` may both find the file
missing at the same moment. `create(path, seed)` makes the parent directory (mode 0700) if missing;
builds the whole file under a temporary name beside it (`library.sqlite.<pid>-<8 hex>.new`, v2,
§3.2 B8; created with `os.open(…, O_CREAT | O_EXCL | O_WRONLY, 0o600)` before SQLite touches it,
since SQLite gives `-wal` and `-shm` the database file's permissions): schema and
`PRAGMA journal_mode = WAL` (persistent in the file), then `seed(temporary)`, which writes revision
1 through the ordinary writer; once the last connection to it is closed (which checkpoints and
removes its `-wal`), it publishes it with `os.link(temporary, path)`, which fails if another
process published first, and removes the temporary name and any `-wal` or `-shm` beside it either
way. The loser opens the winner's file. No process ever sees a library without revision 1.

**Refused locations (Linux).** Before connecting, `refuse_network_filesystem` reads the
filesystem type of the file's directory from `/proc/self/mounts` (`filesystem_type`: the longest
mount point that is a prefix of the resolved path, octal escapes decoded); for `nfs`, `nfs4`,
`cifs`, `smb3`, `smbfs`, `9p`, `fuse.sshfs` `connect` raises `LibraryError` (`NETWORK_FS`). The
mounts file is a keyword argument, so a test passes a fake one. SQLite's WAL mode needs shared
memory that network filesystems do not provide (sqlite.org/wal.html, "WAL does not work over a
network filesystem"). No check on macOS, whose homes are local.

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

**Heads as of a revision** (`:rev` is the current revision when not given), **in creation order:
the row id of each entity's version 1** (v2, §3.2 B8; one import creates many entities in one
revision, so `created_rev` cannot order them):

```sql
SELECT v.*, r.at, r.action,
       (SELECT w.rev FROM versions AS w
         WHERE w.kind = v.kind AND w.name = v.name AND w.version = 1) AS created_rev,
       (SELECT w.rowid FROM versions AS w
         WHERE w.kind = v.kind AND w.name = v.name AND w.version = 1) AS created
  FROM versions AS v JOIN revisions AS r USING (rev)
 WHERE v.version = (SELECT MAX(w.version) FROM versions AS w
                     WHERE w.kind = v.kind AND w.name = v.name AND w.rev <= :rev)
   AND v.deleted = 0
 ORDER BY created
```

`history` is the same select without the `WHERE` on heads, for one `(kind, name)`, newest first.

**Writing.** A save is `with store.write(path, action, detail) as w:`, which opens a connection,
runs `BEGIN IMMEDIATE` (the busy timeout waits out another writer), and yields a `Writer`.
`Writer.add(...)` inserts a version at `head.version + 1` (or 1), creating the `revisions` row on
its first call, so a save that changes nothing makes no revision. On normal exit the library checks
the invariants of §2.5 against `w.heads()` (`Library._save`, once per save that wrote something)
and commits; any exception rolls back.

```python
# Kind is records.Kind (§4.4); store.py re-exports it.

SCHEMA_V1: str  # the schema above
MIGRATIONS: tuple[str, ...]  # MIGRATIONS[i] takes user_version i to i + 1; (SCHEMA_V1,)

NETWORK_FILESYSTEMS: frozenset[str] = frozenset(
    {"nfs", "nfs4", "cifs", "smb3", "smbfs", "9p", "fuse.sshfs"}
)
MOUNTS = Path("/proc/self/mounts")
BUSY_TIMEOUT_MS = 5000


@dataclass(frozen=True)
class Row:
    kind: Kind
    name: str
    version: int
    rev: int
    at: datetime  # the revision's time, UTC
    action: str  # the revision's action
    created_rev: int  # the revision of version 1 (creation order: its row id)
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


def filesystem_type(path: Path, *, mounts: Path = MOUNTS) -> str | None:
    """The type of the filesystem holding path: the longest mount point it is under."""


def refuse_network_filesystem(path: Path, *, mounts: Path = MOUNTS) -> None:
    """LibraryError NETWORK_FS for a path on NFS, SMB, 9p or sshfs (Linux only)."""


def connect(path: Path, *, mounts: Path = MOUNTS) -> sqlite3.Connection:
    """Refuses a network filesystem (Linux); migrates an older schema."""


def migrate(conn: sqlite3.Connection) -> None: ...


@contextmanager
def read(path: Path) -> Iterator[sqlite3.Connection]:
    """One read transaction: every query inside sees the same revision."""


def current_rev(conn: sqlite3.Connection) -> int: ...


def heads(conn: sqlite3.Connection, *, rev: int | None = None) -> list[Row]:
    """Every live entity's head as of rev (default: now), in creation order."""


def history(conn: sqlite3.Connection, kind: Kind, name: str) -> list[Row]:
    """Every version of one entity, newest first, tombstones included."""


def decomposition_named(conn: sqlite3.Connection, slug: str) -> str | None:
    """The name of the decomposition most recently saved with this slug, deleted or not."""


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

YAML is parsed with `yaml.safe_load` (no conflit tags: composition is not a Library concept) by
`load_mapping`; a document that does not parse is `INVALID` with the parser's message as its one,
location-less error, and one that is not a mapping is `NOT_A_MAPPING` the same way (v2, §3.2 B3:
`this YAML is not a valid deep_reasoner {model}:` and the message on the next line).

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
FINAL_ANSWER = "FinalAnswer("


def canonical_yaml(data: Mapping[str, Any]) -> str: ...


def slug(name: str) -> str:
    """D1's own function (acp/catalog.py), re-exported: lower case, runs of [^a-z0-9] -> "-",
    trimmed."""


def load_mapping(text: str, model: str) -> dict[str, Any]:
    """The YAML (or JSON) text as a mapping, or INVALID with one whole-document error."""


def tool_file(name: str) -> str:
    """Where a tool's source is written beside main.yaml, as factory_from names it."""


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
Kind = Literal["profile", "namespace", "decomposition", "tool"]


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


class LibraryForbidden(LibraryError):
    """A request from another user, or addressed to a host other than loopback."""

    code = "forbidden"
    status = 403


class LibraryBadRequest(LibraryError):
    code = "bad_request"
    status = 400


class LibraryNotJson(LibraryError):
    code = "unsupported_media_type"
    status = 415
```

**Which error each failure is** (v2, §3.2 B1–B4; v1 left the invariants' class open):

| Failure | Class, status, `error` | Sentence (§4.10) |
|---|---|---|
| YAML that fails its kind's model or the Library's name rules | `LibraryValidationError`, 422 `invalid` | `INVALID` with one line per error |
| YAML that does not parse, or is not a mapping | `LibraryValidationError`, 422 `invalid` | `INVALID` (`this YAML is not a valid …:`), the parser's message or `NOT_A_MAPPING` |
| A save that breaks an invariant (§2.5) | `LibraryValidationError`, 422 `invalid`, one `FieldError` | `SLUG_TAKEN`, `PARENT_MISSING`, `DEFAULT_MISSING`, `UNKNOWN_DECOMPOSITION`, `LISTED_TWICE`; a `namespaces` or `granted_in` name that is not live: `NOT_FOUND` |
| A head that no longer validates, at materialize | `LibraryValidationError`, 422 `invalid` | one `STALE_HEAD` per head |
| A config that cannot be imported | `LibraryImportError`, 422 `import_failed` | `IMPORT_LOAD`, `IMPORT_COLLISION`, `IMPORT_TOOL_FILE`, and `SLUG_TAKEN` inside one config |
| A `base_version` that is not the head's | `LibraryConflict`, 409 `conflict`, with `head` | `CONFLICT_EXISTS`, `CONFLICT_STALE` |
| A delete or a write the Library's state forbids | `LibraryRefused`, 409 `refused` | `REFUSE_ROOT`, `REFUSE_DEFAULT`, `REFUSE_CHILDREN`, `DEST_NOT_EMPTY` |
| Nothing at that key, version or revision | `LibraryNotFound`, 404 `not_found` | `NOT_FOUND`, `NO_VERSION`, `NO_REVISION` |
| A `PUT` whose path key is not the YAML's; a body that is not a JSON object of the route's fields; a `?base_version=` that is not a whole number | `LibraryBadRequest`, 400 `bad_request` | `NAME_MISMATCH`; `BAD_REQUEST` and pydantic's first message; the `api.py` sentence of §4.10 |
| Another user's socket; a foreign `Host` | `LibraryForbidden`, 403 `forbidden` | `FORBIDDEN_PEER`, `FORBIDDEN_HOST` |
| A `PUT` or `POST` not sent as JSON | `LibraryNotJson`, 415 `unsupported_media_type` | `NOT_JSON` |
| The library on a network filesystem | `LibraryError`, 400 `error` (at start-up: `dr-library` exits 1) | `NETWORK_FS` |

### 4.5 `library.py`: the Python API

`LIBRARY_FILE` and `library_path` are defined in `catalog.py` (§4.7; v2, §3.2 B6) and imported
here.

```python
class Library:
    path: Path

    @classmethod
    def open(cls, path: Path | None = None, *, starter: bool = True) -> "Library":
        """Open path (default library_path()), creating it when absent: revision 1 is the
        starter's import, or, with starter=False, an empty profile and a bare root."""

    # ── reads: each one read transaction ──────────────────────────────────────────

    def rev(self) -> int: ...

    def state(self, *, rev: int | None = None) -> LibraryState:
        """As of rev (default: now); LibraryNotFound NO_REVISION outside 1 … now."""

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
        """Newest first, tombstones included; works for deleted entities. A decomposition's
        key is its name or its slug."""

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
        source: str | None = None,
    ) -> ValidationResult:
        """Validate without saving. name is the tool's (a tool's YAML does not carry it);
        source is a tool's Python file, when it has one."""

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
        namespace (default: the profile's), written into main.yaml only when it is not the
        profile's."""
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
- **A save that breaks an invariant** (§2.5) is rolled back as `LibraryValidationError`, 422
  `invalid`, with the invariant's sentence as its message and its one error (v2, §3.2 B3; §4.4's
  table). A name in `namespaces` or `granted_in` that is not a live namespace is the same, with
  `NOT_FOUND`'s sentence.

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
   `SLUG_TAKEN`, as `LibraryImportError` like the rest of this list (v2, §3.2 B3).
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
one `store.write(path, "import", str(main))`: decompositions and tools first, then namespaces in
the config's order (root, the `namespaces_dir`'s, the inline ones; v2, §3.2 B11), then the
profile, each written only if it differs from its head (§4.5's "unchanged"). Nothing absent from
the config is touched (decision G). Then the invariants, once, over the whole transaction, so the
order inside it matters only for creation order.

**Writing a directory** (`write_config(state, dest, *, namespace) -> Manifest`):

```text
<dest>/
  main.yaml              the profile as stored; entry_namespace: <namespace> only when it is not the
                         profile's default (v2); namespaces_dir: namespaces;
                         decompositions: [the top-level list, bodies inlined]; tools: {name: block}
  namespaces/<name>.yaml one per live namespace: its YAML plus decompositions: [attached bodies, in order]
  tools/<name>.py        one per tool with a source
  library.yaml           the Manifest
```

- Every file is canonical YAML. `main.yaml` and `library.yaml` start with one comment line:
  `# Written by the deep-reasoning Library from <path> at revision <rev>. Edit the Library, not
  this file.` (`dr` ignores comments; the rows never hold them.)
- `main.yaml` is written last, so a directory with a `main.yaml` is complete.
- **`entry_namespace` is written only when the namespace asked for differs from the profile's**
  (v2, §3.2 B5): an export of a profile that never set it re-imports as the same profile, so
  re-importing an export makes no revision.
- `materialize` first re-validates every head it is about to write under the installed
  deep_reasoner (decision J) and raises `LibraryValidationError` listing each one that fails, before
  writing anything. It refuses a `dest` that exists and is not empty (`DEST_NOT_EMPTY`,
  `LibraryRefused`, 409); when a write fails it removes `dest` if it made it, and otherwise empties
  it again (v2).
- Export (`dr-library export DIR`, which D5's `dr-app export` calls) is `materialize(DIR)` with the
  profile's default namespace. `GET /export` zips a temporary materialization.

Paths inside tool blocks other than `factory_from` (a `rag` tool's `documents`, a `kg` tool's
`persist`, a Claude worker's `dirs`) are read by deep_reasoner relative to the **working
directory** (`tools/base.py:186–196`), so they mean under a materialized config what they mean under
the original: relative to the conversation's folder in `dr-acp` (D1's worker `cwd`), relative to
where the user runs `dr` on an export. The Library holds no data files.

```python
MAIN = "main.yaml"
MANIFEST = "library.yaml"
NAMESPACES_DIR = "namespaces"


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

`library_path` lives here, not in `library.py` (v2, §3.2 B6): `dr-acp` finds its library before it
serves, and this module imports nothing of deep_reasoner.

```python
LIBRARY_FILE = "library.sqlite"


def library_path(home: Path | None = None) -> Path:
    """Home.resolve(home).root / "library.sqlite": --home, else $DR_HOME, else
    ~/.deep-reasoning (D1's Home, acp/runlog.py)."""


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

**What D2 changes in D1's files, as D1 §4.6 anticipates** (built in `90044f0`, §3.2 B13).
`acp/cli.py`: without `--config`, the catalog is `LibraryCatalog(library_path(options.home))`
instead of exiting 2 (D1's `NEEDS_CONFIG` sentence and `EXIT_USAGE` are gone); the
`Options.config` comment reads "else the Library". `acp/session.py`: the session index's `source`
(D1 §4.4) is written as `{"kind": "library", "library": "<path>"}` when the `RunSource`'s versions
carry a `library` (`session.py:198–203`), else as before. D1's tests: the harness's `dr_acp` takes
`config=None`, and `test_without_a_config_dr_acp_exits_2_and_says_why` became
`test_without_a_config_dr_acp_serves_the_library_at_its_home`. Nothing in the `Catalog`,
`CatalogSnapshot`, `CommandEntry` or `RunSource` shapes changes.

**Freshness.** D1 takes the snapshot at `session/new` and materializes at the first prompt, so a
save in between is in the run but was not in the menu. A command whose decomposition was deleted
in between fails at the first prompt with deep_reasoner's own `unknown decomposition '…'; this
config defines: […]` (`find_decomposition`, `v2/decompositions.py:117–132`), which D1 answers as
`build_failed`.

### 4.8 `api.py` and `cli.py`: the App backend and the command

```python
Peer = tuple[str, int]
JSON_TYPE = "application/json"
BODY_METHODS = frozenset({"PUT", "POST"})
PROC_NET = Path("/proc/net")


def create_app(
    library: Library,
    *,
    same_user: Callable[[tuple[str, int], tuple[str, int]], bool] | None = None,
) -> Starlette:
    """The routes of §6, behind the request guard. same_user(client, server) is asked for
    every request; a False is 403 FORBIDDEN_PEER. Default: same_user_peer on Linux, no check
    elsewhere. Then a Host other than 127.0.0.1:<port> or localhost:<port> is 403
    FORBIDDEN_HOST, and a PUT or POST not sent as application/json is 415 NOT_JSON."""


def same_user_peer(
    client: tuple[str, int],
    server: tuple[str, int],
    *,
    proc_net: Path = PROC_NET,
) -> bool:
    """True when the TCP socket at client connected to server belongs to os.getuid().

    Reads proc_net/tcp and tcp6, finds the row whose local address is client and remote
    address is server (hex, little-endian per 32-bit word, as the kernel prints them), and
    compares its uid. No such row: False.
    """
```

**The request guard** (v2, §3.2 B1) is ASGI middleware ahead of routing, so a refused request
reaches no route: the same-user check, then the `Host` check, then, for `PUT` and `POST`, the media
type (`Content-Type`'s value before any `;`, lower-cased, must be `application/json`). Verified: on
Linux, the row for the client end of a loopback connection is present in `/proc/net/tcp` with the
client's uid; and the bridge's requests arrive with `Host: 127.0.0.1:<port>` (§8, B6).

**Endpoints** (v2, §3.2 B9) are `async` wrappers: each reads the body of a `PUT` or `POST`, then
runs a sync handler with `run_in_threadpool`; the handler calls one `Library` method and returns
its record's `model_dump(mode="json")` (and 201 or 200 for a `PUT`, decided by whether the key
existed just before). A body is parsed into a pydantic model with `extra="forbid"` per route
(§3.2 B2): one that is not JSON, lacks `yaml`, or has a field the route does not know or a value
of the wrong type is 400 `bad_request` (`BAD_REQUEST` and pydantic's first message). One exception
handler turns `LibraryError` into `JSONResponse(exc.payload(), status_code=exc.status)`; §4.4's
table is the whole mapping.

```python
EXIT_ERROR = 1
HOST = "127.0.0.1"


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


def chain(namespace: str) -> list[str]:
    """root, then each dotted prefix of namespace, as deep_reasoner walks it."""


def resolved(state: LibraryState, namespace: str) -> Any:
    """deep_reasoner's ResolvedNamespace for namespace, over the Library's live heads."""


def effective(state: LibraryState, namespace: str) -> Effective: ...
```

### 4.10 `texts.py`: every user-visible sentence (verbatim)

A sentence without fields is a constant; one with `{fields}` is a lower-case function of them
returning an f-string, as in D1's `texts.py`. D3 shows `message` from the API as it is. v2 adds
five sentences and splits one (§3.2 B4); they are marked (v2).

| Name | Text |
|---|---|
| `INVALID` | `'{name}' is not a valid deep_reasoner {model}:` then one line per error, `  {loc}: {msg}`, then the extra lines below that apply (the mock-up's failure cell). `{name}` is the YAML's `name` when it has one, else `this YAML`. An error without a location is the line `  {msg}` (v2). |
| `METADATA_USE_WHEN`, `METADATA_HINT` (v1's `METADATA_IN_YAML`, two constants in v2) | `Use-when text is stored beside the YAML: pass use_when=... instead.` (a `use_when` key; the mock-up's line) / `A hint is stored beside the YAML: pass hint=... instead.` (a `hint` key) |
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
| `NO_VERSION` (v2) | `There is no version {version} of {kind} '{name}' in the library.` (404, `GET …/versions/{n}`) |
| `NO_REVISION` (v2) | `There is no revision {rev}: the library is at revision {current}.` (404; `state`, `materialize` and `export --rev` outside 1 … now) |
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
| `FORBIDDEN_HOST` (v2) | `This library answers only requests addressed to 127.0.0.1:{port} or localhost:{port}.` (403) |
| `NOT_JSON` (v2) | `The body must be sent as application/json.` (415) |
| `BAD_REQUEST` (v2) | `The body must be a JSON object with a 'yaml' string.` (400; followed by a space and pydantic's first message) |
| `IMPORTED` | `imported {path} as revision {rev}: {new} new, {changed} changed, {unchanged} unchanged` |
| `NOTHING_IMPORTED` | `nothing changed: the library already holds {path}` |
| `EXPORTED` | `wrote {main}: {n} namespace(s), {m} decomposition(s), {k} tool(s)` (singular for 1, as D5's mock-up: `4 namespaces, 6 decompositions, 1 tool`) |

The two sentences quoting deep_reasoner are its own: pydantic's messages arrive unchanged (for an
empty `messages` list that is `List should have at least 1 item after validation, not 0`; D3's
mock-up shortened it), and `IMPORT_LOAD`'s `{detail}` is `f"{type(exc).__name__}: {exc}"`, D1's
form.

**One sentence is not in `texts.py`** (v2, §3.2 B4): `base_version must be a whole number; got
{raw!r}.` (400, a `?base_version=` that is not a whole number) is written inline in `api.py`.
Moving it is the Refactorer's (§9 item 13).

---

## 5 · Algorithms

### 5.1 One save, end to end

```text
validate the input outside any transaction (shapes.py)        → LibraryValidationError
with store.write(path, action, detail) as w:                   BEGIN IMMEDIATE (waits ≤ 5 s)
    head = w.head(kind, key);   check base_version              → LibraryConflict / NotFound
    compute the new rows: this entity, plus every namespace or profile list the save edits
    for each row that differs from its head: w.add(...)         (the first add makes the revision)
    check §2.5 against w.heads()                                → LibraryValidationError (§4.4)
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
- **Who may call** (v2, §3.2 B1). Every request must come from this OS user's socket (Linux), be
  addressed to `Host: 127.0.0.1:{port}` or `localhost:{port}`, and, for `PUT` and `POST`, carry
  `Content-Type: application/json` (a `charset` is allowed); otherwise 403 `forbidden` or 415
  `unsupported_media_type`, before any route. Requests through the bridge pass: it drops the
  browser's `Host` and sends `127.0.0.1:{port}` (§8, B6), and it forwards `Content-Type`.
- **Bodies** are JSON objects. YAML travels as a string field `yaml`; any YAML is accepted, JSON
  text included. Every record carries both `yaml` (canonical) and `data` (parsed). A body field
  the route does not list in §6.2, or a value of the wrong type, is 400 `bad_request` (v2, §3.2
  B2), never ignored.
- **Writes** are `PUT` (create or update) and `DELETE`; the bridge requires the ingress `Origin` on
  them (`bridge.py:454`), which the App's own fetches carry.
- **Concurrency**: `base_version` in a `PUT` body, or `?base_version=n` on a `DELETE`. Omitted:
  unconditional. D3 always sends it.
- **Status codes**: 200 read or updated; 201 created (version 1, or re-created after a delete);
  400 `bad_request`; 403 `forbidden`; 404 `not_found`; 409 `conflict` or `refused`; 415
  `unsupported_media_type`; 422 `invalid` (a broken invariant included, §4.4). `import_failed`
  (422) is never answered over HTTP, which has no import.
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
value (a `PUT` replaces them, §2.3), **so D3 always resends both** (§3.2 B21). `namespaces`,
`top_level`, `decompositions` and `granted_in` absent mean "leave as it is". A field not listed for
the route is 400 `bad_request`; `?base_version=` that is not a whole number is 400 too (v2).
`GET …/versions/{n}` for a version the entity never had is 404 `NO_VERSION` (v2).

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
| Open one in the card editor; attach it to more namespaces | `GET /decompositions/{slug}`; `PUT` with `base_version` = its version, `namespaces` = the new set, and the record's `use_when` and `hint` resent (omitted, they are erased) |
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
discovered at collection (39 files at `d7334ae`; v1 said 40), each its own parametrized case, so every failure
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

**Level 2, every config and the composed one (a fake model, no network).** Run `dr <config>
"Which course comes after CS101?" --no-progress --run-dir <tmp>` on the original and on the
materialized copy, against D2's own fake OpenAI (`tests/library/fake_openai.py`, v2 §3.2 B15)
answering every chat call `<think>ok</think>\n<repl>\nFinalAnswer("done")\n</repl>` and every
`/v1/embeddings` call with a fixed vector, with `--set client.base_url=<fake>` and, for each tool
block that has its own `client`, `--set tools.<name>.client.base_url=<fake>`; dummy provider keys
in the environment (`DAYTONA_API_KEY` left unset), every proxy variable pointed at a closed port
(`127.0.0.1:9`, `NO_PROXY` loopback) and `PYTHONDONTWRITEBYTECODE=1`; deep_reasoner's
`write_fake_claude_cli` first on `PATH`; and as working directory a temporary folder holding a
**copy** (v2, §3.2 B16; v1 said a symlink) named `configs` of the checkout's `configs/` for a file
under it, or of its `docs/configs/` for a file under that (deep_reasoner's docs pages run from
`docs/`), so relative data paths such as `configs/examples/experience/memory.yaml` resolve, and
`logs/`, `rag`'s embeddings sidecar and any `__pycache__` land in the temporary folder, never in
the checkout. Assert equal exit codes, equal last lines of stdout, and equal `messages` in the
first chat request. Two sets committed in the test guard against a broken fake making every case
"equal" by failing everywhere: the configs that answered at `d7334ae` must answer `done`, and the
two Claude-backbone configs must exit 0 with the fake CLI's `The Claude session ended without
calling FinalAnswer`.

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

**Measured by the build (v2; CI at `90044f0`, and each case's outcome again locally on
2026-10-03 with the test's own helpers):** 39 files; the 37 that load pass level 1, the 2
namespace files are refused as expected, and the composed one passes. Level 2 runs 38 cases (the
37 and the composed one) and all 38 are equal. **19** reach `done` on both sides
(`configs/example/` `main`, `rag`, `safe_url`, `v2_namespaces`; `docs/configs/catalog/` `advisors`,
`crossover`, `kg_agent`, `kg_query`, `llm`, `llm_tool`, `main`, `namespaces`, `namespaces_dir`,
`restricted`, `sandboxes`; `docs/configs/examples/` `cruncher`, `experience`, `research/assistant`,
`waitlist`); the **2** Claude-backbone configs end at the fake CLI's end; the other **17** exit 1
identically on both sides: the 16 corpus files that set no `model` (fragments, data files, and
the 4 loadable files under `namespaces/` directories), and the composed one.

**Null:** any case failing either level. Failures are listed (one case each), never skipped. In CI
`DR_BETA_CHECKOUT` is set (§7.5); outside CI, without it, the cases skip with that reason, and a
guard test fails when `CI=true` and it is unset.

### 7.2 Test files, named for what they pin

As built at `90044f0` (v2): every test v1 named exists under that name; the ones the build added
are marked +. `[…]` is a parametrization.

| File | Pins |
|---|---|
| `test_store.py` | `test_versions_and_revisions_cannot_be_updated_or_deleted[…]` (the triggers); `test_a_save_that_changes_nothing_makes_no_revision`; + `test_one_save_is_one_revision_however_many_versions_it_writes`; `test_heads_as_of_a_revision_ignore_later_versions`; + `test_heads_are_in_creation_order_within_one_revision`; + `test_an_exception_inside_a_save_writes_nothing`; `test_a_new_library_file_is_private_to_its_user` (0600); + `test_a_second_creator_loses_and_leaves_nothing_behind`; `test_two_processes_saving_at_once_both_land` (two subprocesses, `BEGIN IMMEDIATE`); `test_a_library_on_a_network_filesystem_is_refused` (a fake `/proc/self/mounts` passed in) |
| `test_shapes.py` | `test_canonical_yaml_is_the_same_for_every_spelling_of_one_model[…]` (flow, block, JSON, key order); `test_canonical_yaml_is_idempotent`; `test_multiline_strings_are_literal_blocks`; + `test_canonical_yaml_keeps_only_what_the_author_set`; `test_metadata_in_the_yaml_is_refused_with_deep_reasoners_message` (the spec's failure cell, verbatim); + `test_pydantic_locations_are_joined_with_dots`; `test_namespace_names[…]`; + `test_a_namespace_carries_no_inline_decompositions`; + `test_decomposition_names_must_make_a_slash_command[…]`; `test_tool_factory_from_must_be_its_own_file[…]`; + `test_a_tool_name_is_a_python_identifier[…]`; `test_profile_refuses_namespaces_decompositions_and_tools[…]`; + `test_a_profile_keeps_extras_and_drops_nothing_it_was_given`; `test_an_example_without_final_answer_warns`; + `test_a_document_that_is_not_a_mapping_is_invalid[…]`; + `test_the_build_names_the_pinned_commit`; + `test_namespace_config_inlines_decompositions_in_attachment_order` |
| `test_library.py` | + `test_a_new_library_starts_from_the_starter`; + `test_a_bare_library_holds_an_empty_profile_and_root`; + `test_opening_an_existing_library_changes_nothing`; `test_put_then_get_returns_the_canonical_record`; `test_every_save_is_a_new_version`; + `test_an_unchanged_save_returns_the_head_and_makes_no_revision`; + `test_use_when_and_hint_are_replaced_by_every_save`; `test_a_stale_base_version_is_a_conflict_carrying_the_head`; `test_base_version_zero_refuses_an_existing_entry`; + `test_a_base_version_on_something_that_is_not_there_is_not_found`; `test_attaching_versions_the_namespace_and_appends_in_order`; `test_namespaces_is_the_exact_set_after_a_save`; + `test_top_level_is_the_profiles_list`; + `test_putting_a_namespace_sets_its_list_only_when_given` (also `UNKNOWN_DECOMPOSITION`, `LISTED_TWICE`); `test_deleting_a_decomposition_detaches_it_everywhere`; `test_deleting_a_tool_ungrants_it_everywhere`; + `test_granted_in_is_the_exact_set_after_a_save`; `test_root_the_default_and_a_parent_cannot_be_deleted`; `test_a_namespace_needs_its_parent`; + `test_the_default_namespace_must_be_in_the_library`; `test_two_names_with_one_slug_are_refused`; `test_deleted_and_recreated_continues_its_version_numbers`; `test_history_lists_tombstones`; + `test_state_as_of_an_old_revision`; + `test_a_revision_the_library_has_not_reached_is_not_found[0, 3]`; `test_check_reports_ungranted_tools_and_missing_spawn_targets`; `test_a_head_that_stops_validating_is_a_problem_and_blocks_materialize` (monkeypatch the model to a stricter one); + `test_validate_reports_without_saving`; + `test_the_spec_mock_up_runs_as_written` |
| `test_import.py` | `test_import_creates_every_entity_in_one_revision`; `test_reimporting_the_same_config_changes_nothing`; `test_import_never_deletes`; `test_import_replaces_what_the_config_names`; `test_compose_is_flattened`; + `test_a_namespaces_dir_is_layered_under_the_inline_namespaces`; `test_one_name_with_two_bodies_is_refused_naming_both_places`; + `test_one_name_with_one_body_in_two_places_is_one_decomposition`; `test_factory_from_is_read_into_the_library`; `test_a_missing_factory_file_is_refused`; + `test_a_config_deep_reasoner_cannot_load_is_refused_with_its_message`; `test_an_exports_library_yaml_keeps_use_when_and_hint` |
| `test_materialize.py` | `test_materialized_directory_layout`; + `test_the_materialized_config_loads_and_resolves_like_the_library`; `test_decompositions_are_inlined_in_attachment_order`; + `test_top_level_decompositions_are_written_into_main`; `test_materialize_as_of_an_old_revision`; `test_the_manifest_records_every_version`; + `test_a_namespace_that_is_not_live_is_not_found`; `test_a_non_empty_destination_is_refused`; `test_a_failed_write_leaves_no_directory`; + `test_without_a_destination_it_writes_a_new_temporary_directory` |
| `test_effective.py` | `test_sources[…]` (each field rule of §4.9); + `test_a_repl_set_in_a_namespace_is_its_source`; + `test_the_sources_rebuild_deep_reasoners_resolve`; `test_effective_values_equal_deep_reasoners_resolve[37 corpus configs]` (with `DR_BETA_CHECKOUT`) |
| `test_catalog.py` | `test_snapshot_equals_config_catalog_over_the_materialized_config_plus_metadata`; `test_commands_carry_use_when_and_hint`; + `test_a_top_level_decomposition_is_offered_in_every_namespace`; `test_materialize_gives_d1_a_run_source_with_versions`; `test_an_unknown_namespace_is_not_found`; + `test_a_catalog_creates_its_library_from_the_starter_when_absent`; + `test_building_a_catalog_imports_nothing_of_deep_reasoner`; **`test_a_saved_decomposition_reaches_the_next_conversation_in_its_namespace`** (§7.3, below `dr-acp`'s front) |
| + `test_acp.py` | **`test_a_saved_decomposition_reaches_the_next_conversation_in_its_namespace[saved, edited]`** (§7.3, through `dr-acp` over stdio) |
| `test_api.py` | Starlette's `TestClient` (with `base_url` `http://127.0.0.1:8123`, so the `Host` check passes): + `test_health_reports_the_revision_and_default_namespace`; + `test_every_read_answers_its_records[…]`; + `test_records_carry_yaml_and_parsed_data`; + `test_creating_a_decomposition_answers_201_and_updating_200`; + `test_every_write_route`; + `test_validate_answers_200_even_when_invalid`; `test_errors_carry_code_message_and_details`; `test_a_slug_with_spaces_in_the_name_round_trips`; `test_the_path_key_must_match_the_yaml[…]`; `test_export_is_a_zip_of_a_materialized_directory`; + `test_a_request_addressed_to_another_host_is_refused[…]`; + `test_a_body_that_is_not_sent_as_json_is_refused[…]`; `test_another_users_connection_is_refused`; + `test_same_user_peer_reads_the_client_sockets_owner[…]` (a fake `/proc/net` passed to `same_user_peer`) |
| `test_cli.py` | `test_serve_answers_health_on_loopback` (a real `dr-library serve` subprocess with only the six variables an App backend gets; a rebound `Host` is 403); `test_import_and_export_print_their_lines`; + `test_export_at_an_old_revision`; + `test_a_library_error_exits_1_with_its_message_on_stderr`; + `test_usage_errors_exit_2` |
| `test_roundtrip.py` | E7, §7.1: `test_every_config_dr_accepts_round_trips[39 files]`; `test_the_example_namespaces_directory_round_trips`; `test_the_corpus_is_read_in_ci`; `test_dr_answers_the_same_from_the_original_and_its_copy[38 cases]` |
| `test_live.py` | §7.4: `test_an_edited_decomposition_reaches_a_real_run_at_its_saved_version` |
| helpers | `conftest.py` (`lib`, `router`, `example`, `text`, `write_config`, `run_dr`); `corpus.py` (the corpus, `NOT_CONFIGS`, the composed config); `fake_openai.py` (§3.2 B15) |

### 7.3 D3's falsifier, at the store

Spec D3: "a decomposition saved in Create decomposition is not used, at its saved version, by the
next conversation in that namespace, as our run log records". The UI half is D3's; everything
below the panel is tested here, deterministically, with D1's harness: start `dr-acp --home <tmp>`
(no `--config`, so `LibraryCatalog`) over stdio with D1's `ShimConnection`, and D1's `FakeOpenAI`
(`tests/library/test_acp.py`, built in `90044f0`; v2, §3.2 B14).

1. Import a router config of our own; `put_decomposition(…, namespaces=["router"],
   use_when="comparing many courses")` → v1.
2. `session/new` in `router` (the profile's default): the `available_commands_update` lists
   `summarize-then-rank` with description `comparing many courses`.
3. A prompt: the session index's `source` is `{"kind": "library", "library": <path>}`;
   `run.start.source.versions.decompositions["summarize then rank"] == 1`,
   `run.start.namespace == "router"`, the run answers, and the fake's first request carries the
   decomposition's first user message among the examples.
4. The `edited` case saves v2 over v1 (resending the use-when line) before its session opens; its
   run records 2, and its first request carries v2's text, not v1's.

The same falsifier also runs below `dr-acp`'s front, in `test_catalog.py`: `LibraryCatalog`'s
snapshot and two `materialize`s (v1, then v2 after an edit), each run with `dr`.

### 7.4 Live tier (Gate B; `@pytest.mark.live`, skipped without `OPENAI_API_KEY`)

Spec §4 layer 5, "D2: import, edit, version, materialize and run", on gpt-6-luna through a config of
our own (D1's `docs/configs/advising/main.yaml`, which uses `base_url
https://api.openai.com/v1` and `api_key_env OPENAI_API_KEY`):

1. `Library.open(tmp)` (with the starter), `import_config(advising)`.
2. Save a decomposition `first course` in `advising` (v1, `base_version=0`), then edit its worked
   example (v2, `base_version=1`); assert `history` shows v2 then v1.
3. (v2) Save it again with a `use_when` key in its YAML: refused with the spec's failure cell,
   verbatim, and the revision does not move.
4. `materialize(namespace="advising")`; assert the manifest records the revision and
   `first course: 2`.
5. `dr <dir>/main.yaml "Which course must a student finish before CS102?" --run-dir <tmp>`; assert
   exit 0, the answer names `CS101`, and the root agent's node log in the run directory carries
   v2's example text, and neither v1's nor the refused one's.

`tests/library/test_live.py::test_an_edited_decomposition_reaches_a_real_run_at_its_saved_version`;
passed in [run 37085761405](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37085761405)
at `90044f0`.

Cents per run.

### 7.5 Repository wiring D2 adds

- `pyproject.toml` (D1's): dependencies `starlette>=0.40` and `uvicorn>=0.30` (both already in
  deep_reasoner's resolved environment through chromadb, declared here because we import them);
  dev group `httpx` (Starlette's `TestClient`); script `dr-library =
  "deep_reasoning.library.cli:main"`. `starter.yaml` ships inside the package (hatch includes it, as
  D1's `prices.yaml`).
- **D2 keeps its own fake** (v2, §3.2 B15): `tests/library/fake_openai.py` (chat completions and
  `POST /v1/embeddings` with a fixed vector per input); D1's `testing/fake_model.FakeOpenAI` is
  unchanged. v1 offered either.
- **No CI change** (v2, §3.2 B19): D1's `.github/workflows/ci.yml` already checks out
  deep_reasoner_beta at the pin into `${{ github.workspace }}/deep_reasoner_beta`, with the read
  token D1 needs, and sets `DR_BETA_CHECKOUT`; ruff checks `src` and `tests` only.
- The live tier runs in D1's on-demand workflow (`live.yml`) with the same `OPENAI_API_KEY`
  secret.

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

**D1 (committed on `v1-dr-acp`, `21c2c7a`; merged under D2 at `21f4a8b`)**: `acp/catalog.py`'s
`Catalog`, `CatalogSnapshot`, `CommandEntry`, `RunSource`, `ConfigCatalog`, `load_dr_config`,
`slug`; `acp/runlog.py`'s `Home` and `SessionIndex`; `tests/conftest.py`; `tests/acp/harness.py`'s
`dr_acp`, `run` and `run_ids`, and `tests/acp/scenarios.py`'s `BASE_CONFIG` and `repl` (§7.3);
`testing/fake_model.FakeOpenAI` and `testing/client.ShimConnection` (§7.3); `run.start.source`
recording `RunSource.versions` (D1 §4.4). D2's own edits to D1's files are §3.2 B13.

**The agent-server (SDK fork `91430aa`)**

| # | Behaviour relied on | Their code |
|---|---|---|
| B1 | An App backend's argv may use only `{port}`, `{data_dir}`, `{artifact_dir}`; its executable must be inside `{artifact_dir}`; it inherits only `LANG`, `LC_ALL`, `LC_CTYPE`, `PATH`, `TMPDIR`, `TZ` | `canvas_extensions/manifest.py:121–160`, `backend.py:38–40, 340–352` |
| B2 | Readiness is `GET <health.path>` (default `/health`) on 127.0.0.1, 30 s by default | `manifest.py:112–117`, `backend.py:420` |
| B3 | The bridge strips `/app-backends/<name>`, decodes the path once, refuses `.`, `..` and `\`, and forwards to `/<path>` | `canvas_extensions/bridge.py:322–343, 448–468` |
| B4 | The bridge authenticates the browser with a cookie and requires the ingress `Origin` for unsafe methods; the backend receives no credential | `bridge.py:448–468`; `_BackendTarget.api_key` unused (`:58–62`) |
| B5 | A backend is started in its own session and stopped by process group | `backend.py:507, 545` |
| B6 | (v2) The bridge forwards to `http://127.0.0.1:<port>`, drops the browser's `Host` as hop-by-hop and lets httpx set it from that URL, and forwards `Content-Type`; the readiness probe uses `127.0.0.1:<port>` too. D2's `Host` check (§3.2 B1) relies on it | `bridge.py:366–369, 467`; `backend.py:420, 638–643`; `docker_runtime/proxy.py:32–50, 115–116` |

---

## 9 · Open items, for the Conductor

1. **Every Canvas App backend is unauthenticated loopback HTTP** (B4). D2 refuses other users'
   connections on Linux (decision K) and has no check on macOS. The generic fix is upstream-shaped
   and small: the backend manager passes a per-launch secret through a new `{token}` argv
   placeholder and the bridge sends it as a header on every forwarded request. Whether S2 takes it
   is the Conductor's call; D2 would then check the header everywhere and keep the Linux check as
   defence in depth. (v2: still open. The build added the `Host` and media-type rules of §3.2 B1,
   which close the browser's way in on every platform, not another user's.)
2. **The starter's model and provider** (decision M) are provisional: gpt-6-luna on OpenAI,
   `api_key_env: OPENAI_API_KEY`, matching §4's live tier and D1's advising config. D5's key proxy
   overrides `base_url` per run anyway. Michael or D5 picks the default.
3. **D1 §10 item 6, "offer only programs as slash commands"**, is not designed in: D2 offers every
   decomposition, as D1 §4.6 decided. If wanted, it is one `menu` column and one filter in
   `LibraryCatalog.snapshot`, with no change to D1's shapes.
4. **Branch base.** *(v2: resolved. D2 was built on D1, and D1 at `21f4a8b` is merged under it,
   `da58a33`; D2's only edits to D1's files are §3.2 B13's, and §7.5 needed none.)* D2's code needs
   D1's skeleton: `pyproject.toml`, `tests/conftest.py`, `acp/catalog.py`, `acp/runlog.py`'s `Home`
   (all on `v1-dr-acp` at `21c2c7a`). `v1-library-store` is at `29fb4df`, with none of them.
   Recommended: base the implementation on `v1-dr-acp` (or on `self-hosted-v1` once D1 merges);
   D2's only edits to D1's files are those listed in §4.7 and §7.5.
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
11. **(v2) Size, for Michael at Gate B** (§3.2 B20): about 5.3k lines against the 1.9k with tests
    accepted on 2026-10-02. The Scout and the Refactorer record `Lines After`.
12. **(v2) D3's UI is served by this backend** (the spec's scope addition of 2026-10-03: the UI is
    a frame the Library backend serves, C2's PR 3). D3's design (`ab6f2ec` on `design/d3`, §1.2 and
    §4.5) adds `library/ui.py` with `ui_routes()`, one line in `create_app` that appends them, and
    two sentences to `texts.py`; the request guard then covers `/ui/` too, and a `GET` needs no
    JSON. Nothing in D2's contract changes; D3's build makes that edit.
13. **(v2) Loose ends the build left, for the Refactorer and the Conductor.** Two behaviours no
    test pins: `Library.validate(…, source=)` (§3.2 B7), and a `namespaces` or `granted_in` name
    that is not a live namespace (422, §3.2 B3). One user-visible sentence outside `texts.py`: the
    `?base_version=` one in `api.py` (§4.10). A `PUT`'s 201 or 200 is decided by a read just before
    the write, outside its transaction, so two concurrent creates of one key can both answer 201
    (the second is a new version, as `base_version` absent allows).

---

## Appendix A · Signature index

Every public name, by module, with the section that gives it in full.

| Module | Names | § |
|---|---|---|
| `__init__.py` | re-exports: `LIBRARY_FILE`, `library_path`, `LibraryCatalog`, the records and the v1 errors eagerly; `Library` and `Effective` lazily | 4.1 |
| `store.py` | `Kind` (re-exported from `records.py`), `SCHEMA_V1`, `MIGRATIONS`, `NETWORK_FILESYSTEMS`, `MOUNTS`, `BUSY_TIMEOUT_MS`, `Row`, `filesystem_type`, `refuse_network_filesystem`, `create`, `connect`, `migrate`, `read`, `current_rev`, `heads`, `history`, `decomposition_named`, `Writer` (`rev`, `head`, `heads`, `add`), `write` | 4.2 |
| `shapes.py` | `NAMESPACE_NAME`, `SPLIT_KEYS`, `TOOL_DIR`, `YAML_WIDTH`, `FINAL_ANSWER`, `canonical_yaml`, `slug` (D1's), `load_mapping`, `tool_file`, `deep_reasoner_build`, `Shaped`, `validate_namespace`, `validate_decomposition`, `validate_tool`, `validate_profile`, `namespace_config` | 4.3 |
| `records.py` | `Kind`, `Saved`, `ProfileRecord`, `NamespaceRecord`, `DecompositionRecord`, `ToolRecord`, `HistoryEntry`, `LibraryState`, `Entry`, `Change`, `ImportReport`, `DecompositionMeta`, `Manifest`, `FieldError`, `Problem`, `ValidationResult`, `LibraryError`, `LibraryValidationError`, `LibraryNotFound`, `LibraryConflict`, `LibraryRefused`, `LibraryImportError`, `LibraryForbidden`, `LibraryBadRequest`, `LibraryNotJson` | 4.4 |
| `library.py` | `STARTER`, `ROOT`, `PROFILE`, `Library` (`open`, `rev`, `state`, `profile`, `namespaces`, `namespace`, `decompositions`, `decomposition`, `tools`, `tool`, `history`, `effective`, `check`, `validate`, `put_profile`, `put_namespace`, `put_decomposition`, `put_tool`, `delete`, `import_config`, `materialize`) | 4.5 |
| `configdir.py` | `MAIN`, `MANIFEST`, `NAMESPACES_DIR`, `ConfigParts`, `read_config`, `write_config` | 4.6 |
| `catalog.py` | `LIBRARY_FILE`, `library_path`, `LibraryCatalog` (`snapshot`, `materialize`) | 4.7 |
| `api.py` | `Peer`, `JSON_TYPE`, `BODY_METHODS`, `PROC_NET`, `create_app`, `same_user_peer` | 4.8 |
| `cli.py` | `EXIT_ERROR`, `HOST`, `main` | 4.8 |
| `effective.py` | `Sourced`, `SuffixPart`, `EffectiveTool`, `EffectiveDecomposition`, `Effective`, `chain`, `resolved`, `effective` | 4.9 |
| `texts.py` | every name in §4.10's table | 4.10 |
