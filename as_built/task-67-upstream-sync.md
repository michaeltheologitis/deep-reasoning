# TASK-67 · As built: both forks synced with upstream, and what the sync changed in the app

**TASK-67** · Cartographer · 2026-10-20 · on `design-docs`. The build is in three repos: the SDK fork's
`deep-reasoning` at `9d0becb` (tag `dr-4`, PR #22), the Canvas fork's `deep-reasoning` at `b7817c2` (tag `dr-5`,
PRs #38, #40, #41), and deep-reasoning's `task-67-upstream-sync` at `ef39952` (9 commits on `6b1d979`; not merged;
`main` is `2aa0b3f`, and the branch merges onto it cleanly [run]).

**The contract.** There is no spec and no design doc. Michael asked for the sync "(if possible) when done with all
this", and the Conductor ran it under his standing approval. The build is measured against the Conductor's decisions,
as §0 lists them, and nothing else.

**Evidence.** Every claim carries a mark. **[run]**: I ran it on this machine at the commits named; nothing called a
model. **[CI]**: a named run shows it, and I opened its log. **[read]**: I read it in the code and did not run it.
The scripts behind the [run] marks are not committed.

**Reading guide.** §0 is the five-minute read, §3 the divergences, §4 the runs. §1–§2 are the map of the code.

---

## 0 · What Michael gets, against what was decided

**What was decided** (the Conductor, under Michael's standing approval):

1. Merge upstream into both forks and keep every fork behaviour: SDK `OpenHands/software-agent-sdk` `33d8aa2`
   (v1.56.0), Canvas `OpenHands/OpenHands` `8d39305`. Tag SDK `dr-4` and Canvas `dr-5`, and pin both from
   deep-reasoning together.
2. Skip OpenHands/extensions' skills catalog. The built app points `EXTENSIONS_PATH` at an empty directory, because
   upstream's `resolve()` clones or fetches `OpenHands/extensions@main` on nearly every conversation start, and native
   skill sourcing then throws the skills away.
3. A locked build refuses preset automations (APL-007), because a preset can never run `deep_reasoner`.
4. Outside the lock's scope: `deep_reasoner`'s unrestricted local REPL, which runs as the user, and bundle
   automations, which are the user's code.

**What he gets.**

- The app runs agent-server 1.56.0 from SDK `dr-4`, with Canvas's frontend as upstream had it on 2026-10-19, plus
  every fork feature. PyPI is pinned at `2026-10-20T00:00:00Z` [run: `build.py check`, "the pins belong together ✓"].
- **No conversation start contacts github.com for skills.** E12 and E13 check three things: the agent-server's
  `EXTENSIONS_PATH` is the built directory, the directory stays empty, and no clone exists in the app's state [CI].
  Measured here with SDK `dr-4`'s loader: unset, it takes 1.62 s to clone and 0.81–1.01 s to fetch on each later
  call; with the empty directory set, it returns 0 skills in 0.00 s and clones nothing [run].
- **Preset automations are refused.** In the app, the automation setup page shows no agent or model pill. Pressing
  Create on its prompt preset shows "This app's agent can't run preset automations." and the page sends no create
  request [CI].
- **Every local launch now goes through one resolver.** Home, `/new` and a local child conversation all start the
  locked profile. At Canvas `dr-4`, `/new` and children sent no profile at all [read].

**Against the decisions**, the build does what was decided. §3 gives four places where the code's reach is narrower
than a decision's wording. None of them is a behaviour the decisions rule out.

**Proof.** At `ef39952`, deep-reasoning's ci (39508622242) is green. Cross-repo with the live tier (39508631119),
on the pinned forks with no overrides, is green on every job [CI]:

- E12 28/28 and coexistence 2/2.
- The live tier 1/1: a question to the real model is answered, titled and costed, with no error.
- E13 13 plus 1 strict xfail.
- bridge-replay 16/16, canvas-replay 12/12, and pins.

SDK #22's tests are green on all 11 jobs. Canvas #38's CI and its three desktop builds are green at `c59dccb`. #40
and #41 are green after their base merges [CI].

**Points for Michael.** Each is a fact, detailed below.

- **The empty directory covers only the loader that conversations use.** The agent-server's skills and plugins
  marketplace catalogs, and its skills sync, still clone `OpenHands/extensions` (TASK-75) [read].
- **The preset refusal is Canvas's alone.** The automation backend still accepts a preset from any other client.
  Nothing turns off a preset that is already on, so it keeps running on its trigger [read].
- **Red checks that come with a sync.** The SDK's version-bump guard fails because every package moves from 1.50.1 to
  1.56.0, which it allows only in release PRs [CI]. The fork's mock-LLM suite has one new failure, upstream's WN-001
  test, which expects the no-LLM banner [CI].

---

## 1 · The public surface

Copied from the code at `9d0becb`, `b7817c2` and `ef39952` [read].

**SDK `dr-4`.** One module, `acp_router.py`, holds two routers, and `api.py` registers each once:

- `/api/acp`: `POST /models`, upstream's; and `POST /preview`, ours.
- `/api/conversations/{id}/acp`: `POST /config-options` and `POST /sessions/{session_id}/cancel`, ours.

The other changes:

- `finalize(source, runtime, *, …, acp_config_options: Mapping[str, str | bool] | None = None) -> LaunchedAgent`.
- `AgentLaunchError.to_detail()` returns `{"code", "message"}`. `UnresolvedProfileReferences` adds the four
  `dangling_*` lists.
- `class _ACPSubagentClientConnection(SubagentClientSideConnection, _ACPClientConnection)` is used when
  `acp_subagents` is on.
- Release `dr-4` carries `openhands-typescript-client-1.56.0.tgz` [CI: release asset].

**Canvas `dr-5`.** `config/defaults.json` gains `"skills": {"_comment": …, "extensionsPath": null}`.
`scripts/launcher-defaults.mjs` maps `skills.extensionsPath → EXTENSIONS_PATH`, accepting an absolute path or a `~/`
path, which it expands; the environment wins. It exports `resolveExtensionsPath(env, home = homedir())`.
`buildAgentServerEnv` passes `EXTENSIONS_PATH`, and all four launchers `mkdir -p` it. The lock gains
`LockedPresetAutomationError` and the i18n key `AGENT_LOCK$PRESET_AUTOMATION_REFUSED`, in 16 locales. Spec APL-007
is in `specs/agent-profile-lock.md`. `package.json` takes the client from SDK release `dr-4`. Versions follow
upstream: agent-server 1.56.0, automation 1.22.0.

**deep-reasoning `ef39952`.**

- `desktop/pins.toml`: Canvas `dr-5` `b7817c2`, SDK `dr-4` `9d0becb`, `uv_exclude_newer = "2026-10-20T00:00:00Z"`.
- `desktop/build.py`:
  - `NO_PUBLIC_SKILLS = "~/.deep-reasoning/canvas/no-public-skills"`.
  - `"skills.extensionsPath"` is added to `FORK_NULL_KEYS`.
  - `FORK_NULL_KEYS_SINCE = "dr-5"`.
  - `WEB_RUNTIME_PACKAGES = ("sirv", "httpxy", "ws")`.
  - `patch_defaults(…, exclude_newer, extensions_path)`.
- Tests: `tests/desktop/app.py` gains `PUBLIC_SKILLS_CLONE` and `agent_server_environ(app)`.
  `tests/crossrepo/agent_server.py` gives its agent-server an empty `EXTENSIONS_PATH` inside its persistence root.

**Sentences.**

| Where | Sentence |
|---|---|
| check 5c [run] | `✗ Canvas fork 138d41f's config/defaults.json has no skills.extensionsPath, so this build cannot set it: pin dr-5 or later.` |
| W13 [CI, 39499503121] | `✗ The Canvas fork's electron-builder.config.mjs strips the app's node_modules to sirv, httpxy and ws, but desktop/build.py bundles sirv and httpxy for the browser: bundle the same.` (now names `WEB_RUNTIME_PACKAGES`) |
| APL-007, en [CI] | `This app's agent can't run preset automations.` |

---

## 2 · The map

### 2.1 SDK: where the two sides meet (merge `c77f1146`, 20 conflicted files [run])

| Seam | Upstream brought | The fork kept | Resolution |
|---|---|---|---|
| ACP routes | `acp_router.py` with `POST /acp/models` | the same file name: preview, config options, cancel | one module (add/add) |
| ACP connection | every agent starts on `_ACPClientConnection`, which restores `session/set_model` and legacy models (gemini-cli) | `SubagentClientSideConnection` when `acp_subagents` is on | `_ACPSubagentClientConnection` inherits both |
| Launch | `launch_source → finalize`, in `openhands/sdk/launch/`, replacing the inline resolution the fork had pulled out as `_resolve_launch` | the `acp_config_options` fold | a keyword on `finalize`, applied last; with a non-ACP agent it raises `AgentLaunchError` (422) |
| ACP preview | — | `/acp/preview` | the same `launch_source` and `finalize` as a start; errors map through `launch_http_exception` (404, 422 with `{code, message}`, 503, 500); `InvalidACPConfigOptions` is gone |
| Canvas extensions | `_resolve_contained_file` | `resolve_package_file`, and the panel icon route | upstream's resolver, both icon routes |

The real complexity is the launch seam. `finalize.py` is the only file the merge edited without a conflict, and the
edit is the fold [run: remerge-diff]. `finalize` has three callers in `conversation_service.py`: start, preview and
the sub-conversation [read]. Canvas reads `detail.message` from a structured detail (`getApiErrorMessage`), so the
preview's new 422 shape still shows the sentence [read].

The four follow-ups are on the merge's second parent: `git log --first-parent 9d0becb^1..9d0becb^2`.

- `7d942f5` and `51b830c` change tests only.
- `c31a619` is the one code fix: `_load_launch_settings` now looks up `persistence.get_settings_store` at call time.
- `7ff92b4` runs upstream's orphan-reaping test on Linux only, because it reads `/proc` (TASK-74).

### 2.2 Canvas: where the two sides meet (merge `6ddb7cd`, 56 conflicted files [run]), and the lock's new reach

- **Launch.** Upstream moved conversation launch into `src/hooks/mutation/resolve-conversation-launch.ts`
  (`resolveConversationLaunch`, `launchConversation`). Its callers are Home (`use-create-conversation`), `/new`
  (`use-new-conversation-command`) and local children (`child-conversation-launch`). The merge put APL-002 and
  APL-003 there, in 22 lines over upstream's file. When locked, a launch uses the id of the profile that
  `lockedProfile` names, and is refused with `LockedAgentProfileMissingError` when that profile is missing. It has no
  `agent_settings` fallback and no per-launch LLM override. At `dr-4`, `/new` and the local child called
  `createConversation` without a profile [read].
- **Automations.** Upstream's #18417 deleted `edit-automation-modal` and moved editing to `/automations/setup`, which
  has its own agent and model pills. `21892e1` hides both pills when locked, saves the locked id, and refuses when
  the profile is missing. E12 now walks that page [CI].
- **Two locks.** The Cloud-host lock (#17866) and ours share conditions where both hide the same link: the ACP
  sign-in link in `chat-interface.tsx` and the LLM link in `app-settings.tsx` [read].
- **Agent Context** is not in `AGENT_LOCK_HIDDEN_SETTINGS_PATHS`, so it stays visible, as UX-round design §7.1 and
  §7.4 list it [read].
- **Electron runtime packages.** Upstream added `ws` to `RUNTIME_PACKAGES` for Electron's MARS tunnel. `58dd1f5`
  bundles it in the browser tarball too, which W13 requires [CI].

### 2.3 The public-skills seam, end to end [read; E12, E13 CI]

1. `build.py prepare()` writes `skills.extensionsPath = "~/.deep-reasoning/canvas/no-public-skills"`. It sits beside
   `paths.stateDir`, in the agent-server's persistence root, which is the state directory's parent.
2. The launcher expands the path, creates the directory, and passes it as `EXTENSIONS_PATH`.
3. In the SDK, `_local_public_skills_path` reads the variable, and `load_public_skills` then reads `<dir>/skills`
   instead of cloning.
4. That directory is absent, so the loader returns `[]` and logs a warning. Empty results are never cached, so this
   happens on every call.

The callers are `resolve()` → `stores.skills()` = `discover_profile_skills` → `load_all_skills(load_public=True)`.
This runs on every start or preview that names an agent profile, which in the locked app is every one. It runs
before `_apply_acp_skill_sourcing` drops the skills for an ACP agent under native sourcing.

Without the variable, the clone goes to `<OH_PERSISTENCE_DIR>/cache/skills/public-skills`, the path E12 and E13 check
is absent. Its timeouts in `cached_repo.py` are 60 s for a fetch and 120 s for a clone. Three callers ignore the
variable and call `update_skills_repository` directly: `sync_public_skills`, `_fetch_catalog_entries` and
`_fetch_plugin_catalog_entries` (TASK-75).

### 2.4 APL-007: one choke point, `AutomationService` [read; vitest per method in CI]

| Method (locked build) | Refuses when | Knows by |
|---|---|---|
| `createAutomationDraft` | the endpoint is `/v1/preset/prompt` or `/v1/preset/plugin` | the endpoint |
| `createAutomation` (import) | always | an import always builds a prompt or plugin preset |
| `dispatchAutomation` (Run now, Test) | `preset_metadata.preset_type` is `prompt` or `plugin` | a GET of the automation first |
| `dispatchServerDraft` (Test a draft) | the draft's endpoint is a preset endpoint | a GET of the draft first |
| `updateAutomation`, and `toggleAutomation` through it | the body turns it on (`enabled: true` or `state: ACTIVE`) and it is a preset | a GET first |

Still allowed: turning a preset off, deleting, saving drafts, `validateDraft`, and bundles. A locked build's preset
drafts name no profile; a bundle's create names the locked one. The setup page refuses first (`refusesLockedPreset`),
before the form's checks and before any webhook registration. E12 therefore sees the page's refusal, and the service
layer's refusal is covered by `__tests__/api/automation-service.test.ts`.

The premise holds in the published automation 1.22.0 wheel [read]. `CreatePromptAutomationRequest` and
`CreatePluginAutomationRequest` are `extra="forbid"` and have no `agent_profile_id`, and both preset runners call
`get_default_agent`. The same wheel has a third kind, `POST /v1/plugin-spec` (`preset_type: "plugin_spec"`), whose
runs can carry a profile. Canvas has no client for that route, and `isPresetAutomation` does not count it [read].

---

## 3 · Divergences from the decisions

No code contradicts a decision. Four decisions are worded wider than the code reaches.

1. **"/new and child launches now run the locked profile."** This holds for local children only. A child with
   `target: "cloud"` is built by upstream's unchanged `launchCloudChild`, which reads no lock [read]. Two questions
   are unchecked: whether a locked app can connect a Cloud backend, and whether `deep_reasoner` is offered the
   child-launch tool.
2. **"Skip the skills-catalog fetch."** This covers the conversation-start loader and the preview. The marketplace
   catalogs and the skills sync still clone, which is already TASK-75 [read].
3. **"Refuse presets in a locked build."** The refusal happens in the frontend. Nothing disables an existing preset
   that is on: its trigger keeps running it with a default agent. The automation backend does not refuse presets,
   and `plugin_spec` automations are not classified as presets [read].
4. **"One /acp router."** The code has one module with two routers, as at `dr-3`. Config options and cancel are on
   the conversation-scoped one. The merge message's "one /acp router holding … config-options and sub-agent cancel"
   is looser than the code. Behaviour does not differ [read].

---

## 4 · Runs and measurements

| Run | Where, at | Result [CI] |
|---|---|---|
| 39339047358 Run tests | SDK #22 head `7ff92b4` (tree = `9d0becb`) | 11/11 jobs green, including `macos-app-backend-tests` and `acp-live-tests`. At the same SHA: version-bump guard red ("only allowed in release PRs", 1.50.1 → 1.56.0) and PR Description Check red; 12 other checks green, the macOS workflow skipped |
| 39492790415 CI, 39492790511/565/468 Desktop | Canvas #38 head `c59dccb` | green; Linux, Windows and macOS builds green. "release ready" has a startup_failure, as on #37's head (39321744173) |
| 39496742024 / 39496743578 CI | #40 `074c4ee` / #41 `54d5b5f`, after their base merges | green; #41's SDK Version Sync (39496743872) green |
| 39345182487 CI, 39345176609 Mock-LLM | probe #39 `99e5c7f` (= `c59dccb` ± 4 lines) | CI green. Mock-LLM: 3 failed, 89 passed. Two of the three also failed before the sync (39213707405, 10 failed); the third is WN-001's "home warning icon follows the host warning color" |
| 39360843637 / 39360843640 | probe #42 `7cc8be6` (#40 + #41 on the sync) | CI and version sync green |
| cross-repo 39339050695 | main `6b1d979`, SDK `7ff92b4` | bridge-replay red: `test_title` saw an outbound `github.com:443`, the public-skills clone. Other jobs green |
| cross-repo 39343192659 | `684a05b`, Canvas `cc30ef9` (before wiring), SDK `9d0becb` | red: `build:app` (no `ACPClient` in the `dr-3` client), canvas-replay (1.56.0 is past the 2026-10-04 cutoff), bridge-replay (`github.com:443`); pins green. Fixed by `c59dccb`, `472f346` and `fe5c717` |
| cross-repo 39499503121 | `ece0c48`, Canvas `b7817c2` | desktop-e2e and web-e2e red at W13 (`ws`). Fixed by `58dd1f5` |
| cross-repo 39500434659 | `58dd1f5`, Canvas `b7817c2` | every job green: E12 28/28, coexistence 2/2, E13 13 plus 1 strict xfail (WebKit, TASK-70), bridge-replay 16/16, canvas-replay 12/12, pins |
| cross-repo 39508631119, live | `ef39952`, pinned forks, no overrides | every job green: E12 28/28, coexistence 2/2, the live tier 1/1 (`test_a_question_to_the_real_model_is_answered_titled_and_costed_with_no_error`), E13 13 plus 1 strict xfail, bridge-replay 16/16, canvas-replay 12/12, pins |
| ci 39508622242 | `ef39952` | green |

**The live test's time** [CI]. `test_live.py`'s session took 279.28 s at the synced pins (39508631119). The last
pre-sync live run, cross-repo 39326468453 on `ux-round` `98ec948` with Canvas `dr-4` and SDK `dr-3`, took 57.13 s
for the same test. The cause is not known (§7).

**Run here, at `ef39952`** [run]:

- `tests/desktop/test_build.py`: 65 passed.
- `build.py check`: "the pins belong together ✓".
- `build.py check --canvas-commit 138d41f` (Canvas `dr-4`) refuses three times: the SDK wiring, the client release,
  and check 5c's "pin dr-5 or later".

**The skills loader** [run], measured with SDK `9d0becb`'s `openhands-sdk` in a throwaway uv environment.
`load_public_skills()` was timed in a fresh process, with `HOME` and `OH_PERSISTENCE_DIR` in a scratch directory,
over this sandbox's proxy, on 2026-10-20:

| `EXTENSIONS_PATH` | State | Skills | Seconds | Clone on disk |
|---|---|---|---|---|
| unset | fresh | 69 | 1.62 | yes |
| unset | clone present (fetch), three runs | 69 | 0.96, 0.81, 1.01 | yes |
| empty directory | fresh | 0 | 0.00 | no |

The Conductor measured "+0.4–1 s online, 60/120 s on a dead network". I did not re-run the dead-network case. Its
figures match the 60 s fetch and 120 s clone timeouts in the code [read].

---

## 5 · Known gaps, as they stand

- **TASK-74**: on macOS, App backends left by a crashed agent-server are not reaped. Upstream reads `/proc`, so the
  fork skips that test on macOS.
- **TASK-75**: the marketplace catalogs and the skills sync clone whatever `EXTENSIONS_PATH` says (§2.3).
- **TASK-70**: the Library panel does not open in WebKit. It is a strict xfail in E13.
- **WN-001**: upstream's mock-LLM test assumes no LLM is configured. It fails in the fork's mock suite, which
  configures one.
- **Version-bump guard**: red on every sync PR, since a sync moves the package versions.

---

## 6 · Size

These are non-blank added lines of our own code and tests, excluding what upstream merged in [run]. Merge
resolutions are counted from `git show --remerge-diff`: the lines that are in neither side.

| Repo | Part | Code | Tests | Other |
|---|---|---|---|---|
| SDK | merge resolutions (`c77f1146`, 21 files) | 295 | 93 | 4 |
| SDK | follow-ups (`c77f1146..7ff92b4`) | 3 | 11 | 0 |
| Canvas | merge resolutions (`6ddb7cd`, 59 files) | 133 | 107 | 105 (92 of them i18n) |
| Canvas | #38 follow-ups (`6ddb7cd..c59dccb`, 7 commits) | 43 | 152 | 8 |
| Canvas | #40 APL-007 (`eda9e35..77bd390`) | 93 | 300 | 20 |
| Canvas | #41 extensionsPath (`77bd390..b7817c2`) | 40 | 84 | 8 |
| deep-reasoning | `6b1d979...ef39952` | 24 | 156 | 5 |
| **Total** | | **631** | **903** | **150** |

Upstream brought in, not counted above:

- SDK: 190 commits, +75,978/−8,403 in 556 files (`dr-3` → `dr-4`).
- Canvas: 276 commits, +133,709/−17,644 in 1,098 files (`dr-4` → `c59dccb`).

---

## 7 · What I could not verify

- **The merge messages' other claims.** I read only the resolutions the decisions name. The others are unchecked
  beyond CI passing: the launcher's host check running before the MARS bridge, `waitForService`,
  `spawnUvxService`, `failStartup`, the conversation column, and the `id` locale.
- **The dead-network timing** (§4).
- **Why the live test took 279 s against 57 s before the sync** (§4). The run uploads its logs only on failure, so
  the app's log for this pass is not available, and a real model's latency varies from run to run. Nothing in it
  is a recorded defect.
- **Whether a locked app can reach a Cloud backend, and so a cloud child** (§3.1).
- **The vitest for APL-007 and the launcher's `EXTENSIONS_PATH`.** I read the test names and saw CI pass, but did
  not run them here.
