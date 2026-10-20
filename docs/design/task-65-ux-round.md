# TASK-65 · UX round — design

**TASK-65** (closes TASK-42, 43, 44, 46, 50, 51) · System Designer · design branch `design/ux-round` in
[deep-reasoning](https://github.com/michaeltheologitis/deep-reasoning), cut from `main` at `9e8109e`; the task branch
is `ux-round` · against the approved spec
[UX round](https://app.notion.com/p/3fe62fb222378105a96bd0427574a15d) (Gate A, Michael, 2026-10-19: Q1 (a) with the
startup log's key line gone, Q2 (a), Q3 (b), Q4 (a); the 📝 amendment wins over the body).

**As refactored** (2026-10-19, at the literate refactor; the design below is left as approved, and these lines win
over it where they differ):
- **D1, the key check.** `dr-acp` no longer mirrors `build_client`'s rule: `missing_model_keys(clients) -> list[str]`
  validates each client block as deep_reasoner's `ClientConfig` and calls its `build_client` in `dr-acp`'s own
  environment, naming each refused `api_key_env` once, in order. A block that is not a valid `ClientConfig` is skipped,
  for the worker's build to report. `KEYLESS_BASE_URL_PREFIXES` and the move of the two key constants out of
  `proxy.py` are gone, and one test of names, order and dedup replaces the contract test. Changed: §1.1 D9, §4.3's
  `route.py` and `_start_run` bullets, §5.3's `route.py` block, §7.1's `test_route.py` line.
- **C1, the Canvas fork's test ids.** No `command-menu-item-<id>`: E12 step 3 finds command-menu entries by upstream's
  `#command-menu-option-<id>`. Changed: APL-006 (gone), §5.1's `CommandMenu` line, §7.1's `command-menu.test.tsx` case,
  §7.4 step 3's ids.
- **Tests, otherwise.** §7.2's test leaves `agentInfo.title` to `test_agent.py`, which pins it verbatim. Of §7.1's
  browser tests, `test_each_tab_opens_on_its_content_with_no_dialog` is gone, the refused-amount test drives one
  amount, and the Tools tab's first test is `test_the_tools_tab_opens_on_the_spend_cap_field_holding_the_cap`.
  §13.2's `test_the_title_the_build_writes_is_the_product_name` and TASK-66's cutoff twin are one test,
  `test_the_build_writes_the_product_name_as_the_title_and_the_pinned_cutoff`.

**Pinned against** (every `file:line` below is from these):
- deep-reasoning `main` `9e8109e`;
- Canvas fork `deep-reasoning` at tag `dr-3` = `4355a36`;
- SDK fork `deep-reasoning` at tag `dr-2` = `34c540c`;
- D5's design v3 (`docs/design/d5-desktop-app.md` on `v1-desktop`), whose decisions bind unless this round changes
  them; §10 lists each one it changes.

**Where this file lives, and why nothing trips over it.** `docs/design/task-65-ux-round.md`, on `design/ux-round` and
then on `ux-round`, never on `main` and never in a fork. `pyproject.toml` excludes `docs/` from the sdist
(`[tool.hatch.build.targets.sdist]`) and from ruff (`extend-exclude`), and pytest collects `testpaths = ["tests"]`
only. The PR split leaves the file behind.

**Revisions** (newest first):
- 2026-10-19 · v1.1 · Michael added the browser tab title to the round (§13). Stop trusting: `patch_defaults` "keeps its
  signature" (it gains `app_title`, §4.1, §5.3); check 5b and `fork_lacks_lock` (one loop over `FORK_NULL_KEYS`
  with `fork_lacks_setting`, §4.1, §5.3, §6.4); `test_a_canvas_fork_that_cannot_lock_the_agent_is_refused` and "five
  keys" (§7.1); §8 step 2's PR list; §9's `build.py` row; §11's total. Added: §13.
- 2026-10-19 · v1 · first full-depth version.

**Reading guide.**
- Gate B, about 20 minutes: §0 (what this design changes in the spec), §1 (the shape and the decisions), §8 (the
  release chain) and §10 (what goes stale).
- The Implementer: §1.2 first, then §2 to §4 per repo; §5 is the signature index, §6 every sentence verbatim, §7
  every test by name and E12 in order.
- The TASK-48 designer and the Conductor: §9.

---

## 0 · Findings that change or correct the spec (read first)

Each was run on 2026-10-19 with the scripts in this session's scratchpad (`q1probe/`, `probe46/`); *(verified)* marks
that. Nothing called a model: no key in any environment, and every outbound connection went to a loopback proxy that
records the host it was asked for and forwards nothing.

**F1 · What a question with no `OPENAI_API_KEY` shows today (verified).** On the starter Library (gpt-6-luna, client
`api_key_env: OPENAI_API_KEY`, `library/starter.yaml`), `dr-acp` at `9e8109e` with the key proxy on answers:

> Could not start the run: ValueError: Missing API key. Set \`OPENAI_API_KEY\` (preferred) or \`OPENAI_API_KEY\`.

- Run straight over ACP, it is the turn's `agent_message_chunk`.
- Behind the `dr-2` agent-server's ACP bridge, it is the conversation's `FinishAction` message, which Canvas shows as
  the agent's reply.
- No outbound connection is attempted.
- A run is created: the worker starts, and `runs/<run>/events.jsonl` records `prompt.end build_failed` and
  `run.end build_failed`.

The sentence is deep_reasoner's `build_client` ValueError (`deep_reasoner/config.py:255–266` at the pin), passed
through `texts.build_failed`. It names the variable twice and not where to put it. §4.3 replaces it with one sentence
naming **Settings → Secrets**. That sentence is the reminder, and it appears only when a question is asked without
the key.

**F2 · Canvas itself never reminds about a key here (read).** `useLlmConfigured` treats an ACP agent as configured:
`isConfigured: isAcpAgent || llmSettingsHidden || hasUsableLlm` (`src/hooks/use-llm-configured.ts:163`). It also
treats the LLM page hidden as configured (`:127–130`, "there is no place to finish setup"). So
`LlmNotConfiguredBanner` never shows for `deep_reasoner`, locked or not, and there is nothing of Canvas's to leave
alone.

**F3 · Setup already keeps a cap the user set (read).** The brief asks how setup "stops overwriting" a cap. It does
not overwrite one:
- `desired_profile` keeps every argument but the `--home` pair (`packages/dr-app/src/dr_app/profile.py:47–54`), as
  decision F says ("the spend cap included, is the user's after creation").
- `tests/app/test_profile.py::test_the_users_spend_cap_and_other_arguments_survive` pins it, through a write caused by
  a home move.
- The one cap setup writes is the creating one: a first launch, or after the user deleted the file.

So decision F's code stands. What changes is its text: the cap pair now has a writer, the Library panel's field (§1.1
D7). No change to `profile.py` beyond its docstring.

**F4 · The spec's TASK-46 "after" cell fails for its own reproduction shape (verified).** The approved credential
predicate is `_llm_has_real_config`, which counts a custom base URL as a credential (`agent_profiles_router.py:111–129`).
The reproduction gives its keyless profile `base_url` = a loopback stub, so the profile counts as having a credential.
Run against the guard of §3, the reproduction still publishes `Incorrect API key provided: None`, and the stub still
sees `Bearer None`.

A profile as Canvas's Settings → LLM saves it carries no `base_url`: the form drops it (`llm-settings-local-view.tsx:
319–349`, and `KNOWN_PROVIDER_DEFAULT_BASE_URLS` in `routes/llm-settings.tsx:73`). For that profile:
- on `dr-2`, the titler tries `api.openai.com:443` four times in 100 s, retrying, with no title set (verified);
- with the guard, it makes no outbound attempt, the title is "What is 2 + 2?", and nothing is published (verified).

So the cross-repo test (§7.3) uses Canvas's shape, with a recording proxy for "nothing was called". The predicate stays
as approved: a custom base URL is how a keyless local server (Ollama, vLLM) is reached.

**F5 · The lock needs a ninth gate, and its end-to-end proof is E12 (read).**
- *A ninth gate.* Application settings links to the hidden LLM page: "Manage LLM profiles", `routes/app-settings.tsx:
  267–272`. It is not in the spec's table; a locked build does not render it (§2.1 row 9). Two other links into hidden
  pages need no gate:
  - the ACP model affordance's link (`use-acp-model-context.ts:8`) renders only with a model to show, and `dr-acp`
    offers none (`chat-input-model.tsx:151–152`);
  - the LLM pill's "Manage" link exists only in an OpenHands conversation.
- *No mock-LLM Playwright spec.* The spec planned one, "run with the key set". `agent.lockedProfile` is compiled into
  the bundle, and the fork's mock-LLM suite serves the one build from the committed `defaults.json`
  (`playwright.mock-llm.config.ts`). It also runs only after pushes to `main` or by hand, never on a pull request
  (`.agents/skills/e2e-testing`). A locked spec would need a second build and would run on no PR. So the fork PR
  carries vitest beside every gate, and the locked bundle's end-to-end proof is E12, which drives exactly that bundle
  through every surface (§7.4 steps 1–5). This is a divergence from the spec, named here for the Conductor.

**F6 · `cross-repo.yml` would not run on this round's test changes (read).** Its `pull_request.paths` list `desktop/**`,
`packages/dr-app/**`, `pyproject.toml`, `uv.lock`, `src/deep_reasoning/acp/proxy.py` and the workflow itself. That
omits `tests/desktop/**` (E12) and `tests/crossrepo/**`, so a PR changing only E12 runs no E12. §7.5 adds both. This
round's pin bump triggers it anyway.

**F7 · The panel's tooltip is "Show Decompositions".** C2 renders `CONVERSATION$SHOW_APP_PANEL` = "Show {{title}}", with
the panel's title "Decompositions" (`canvas-extension.json`). The spec's TASK-44 table writes "Show decompositions". The
sentences here name the button as the user sees it: **Show Decompositions**.

---

## 1 · The round in one picture

```text
SDK fork     fix/title-llm-without-credentials   AutoTitleSubscriber._load_title_llm skips a title LLM with no
                                                 credential → agent.llm → truncation                 (TASK-46)
             → Michael tags dr-3; dr-release.yml publishes the TypeScript client tarball

Canvas fork  feat/agent-lock                     config/defaults.json "agent": {"lockedProfile": null}; set, it:
                                                 starts every conversation from that profile, by name; shows no
                                                 onboarding, no agent choice, no Agent / LLM / Model Router /
                                                 Condenser pages, nor their menu, checklist and link entries
                                                 (TASK-50, Q1, Q2)
             fix/subagent-costs-on-by-default    an unsaved "Show sub-agent costs" reads as on        (TASK-51)
             feat/app-title                      "branding": {"appTitle": null}; set, every title names it (§13)
             chore/wire-sdk-dr-3                 sources.agentServerGitRef and the client tarball → dr-3
             → Michael tags dr-4

deep-reasoning  ux-round                         patch_defaults writes "deep_reasoner" into agent.lockedProfile;
                                                 check 5 and check 5b;
                                                 no safety lines, no startup key line, Deep Reasoning in prose;
                                                 dr-acp's missing-key reminder; the Spend cap field in the panel;
                                                 a violet panel icon; E12; the README    (TASK-42, 43, 44, Q1, Q3, Q4)
             → desktop/pins.toml: Canvas dr-4 and SDK dr-3 together, once cross-repo.yml is green on them
```

The shape is the spec's §2. Each fork gets a generic behaviour that is off by default, our build turns it on, and
everything deep_reasoner-specific stays in deep-reasoning. TASK-48's browser build calls the same `patch_defaults`
(its design W11), so it inherits the lock and the title (§13) with no second edit. §9 covers the rest of its seams.

### 1.1 Decisions this design takes

| # | Decision | Why | Rejected |
|---|---|---|---|
| D1 | **The lock lives in one Canvas module, `src/utils/agent-profile-lock.ts`, read when called from the compiled `config/defaults.json`.** One selector, `selectLaunchAgentProfileId`, replaces every read of `active_agent_profile_id` (five places). `isAgentProfileLocked()` gates every surface. | One owner, one writer (the build), as the fork's "Shared Frontend Change Checklist" asks. Reading at call time lets vitest set the key on the imported JSON object and restore it, which mocks the boundary the build writes, not a hook. | A React context or provider: every gated component already renders without one, and the lock never changes while the page runs. |
| D2 | **The "current agent" is the locked profile, by name, everywhere the active pointer was read.** That covers the home preview, the model pill's ACP context, the launch, the ACP model switch and the picker state. | The model pill, the ACP preview and the launch must agree. If only the launch were locked, a user whose pointer still names another profile (an install from before this round) would see that profile's options on the home screen and then get `deep_reasoner`. | Locking only `useCreateConversation`. |
| D3 | **Onboarding's gate is `useOnboardingCompletion`: a locked build reads as completed.** `root.tsx`'s first-run screen and `OnboardingHost` both follow. The getting-started checklist then shows, as it does today after onboarding, minus its two hidden items. | One gate covers both entry points (`root.tsx:274–296`, `onboarding-host.tsx:43–58`). | Gating `root.tsx` and `OnboardingHost` separately (two gates that can drift). |
| D4 | **A hidden page is hidden by `isSettingsPageHidden`, the fork's existing seam** (`settings-utils.ts:52–58`). The nav, the loader's redirect and the landing page all read it. Command-menu entries and checklist items whose route is hidden are dropped by the same path test. | The seam already serves `hide_llm_settings`. Deriving menu and checklist entries from their routes means a hidden page cannot keep a door open. | A second list of hidden ids per surface. |
| D5 | **The title guard sits in `AutoTitleSubscriber._load_title_llm`** (agent-server). A profile LLM with no credential returns `None`, so the existing precedence takes over: profile → agent LLM → truncation. | The profile store and the predicate are the agent-server's. `generate_title_from_message` is public SDK code that `LocalConversation` and `RemoteConversation` also call. There an LLM with `api_key=None` often works through an environment key, and the SDK may not import the agent-server. | The guard beside the sentinel in `title_utils.py`. |
| D6 | **A provider connection's key counts because the guard tests the LLM as the store loads it.** `LLMProfileStore.load(..., resolve_provider=True)`, the default `_load_title_llm` already uses, applies the connection's `api_key` and `base_url` (`llm_profile_store.py:305–307, 328–…`), so `_has_api_key` sees the connection's key. | No second lookup like `_profile_api_key_set` (`profiles_router.py:108–127`). A dangling connection raises `ProviderConnectionNotFound`, a `ValueError`, which `_load_title_llm` already catches. | A Canvas-side filter on `api_key_set`, which would drop working subscription profiles (spec decision 2). |
| D7 | **The Spend cap field is in the Library panel's Tools tab, in place of the two warnings.** The frame asks the page by `postMessage`. The page writes the `deep_reasoner` profile through C2's `host.agentServer.request`, which is Canvas's own backend client with its session key. The page reads the profile, sets the `--spend-cap-usd` pair and posts the profile back whole, as setup does. | The frame never holds the session key: it talks only to `dr-library` through the bridge (D5 decision N). The page already reads the profile this way (`page/context.ts:63–77`). C2's request takes any root-relative path and method (`canvas-extensions-service.ts:247–263`). | The `dr-library` backend writing the profile: it gets six environment variables and no session key (`backend.py:38–40`). Reloading the frame after a write: that would drop an open tool editor. |
| D8 | **There is no "no cap" value.** The field takes a positive dollar amount: 1 to 6 digits, at most 2 decimals. A profile with `--no-key-proxy` shows a read-only "No cap" sentence and no input. The standalone page shows the cap read-only. | `dr-acp` has no unlimited cap (`--spend-cap-usd` is a float; `inf` would format as `$inf`). `--no-key-proxy` also hands the worker the real keys (D5 decision J), so it must not become the field's way to lift a cap. A very large amount is the honest "no limit". | Writing `--no-key-proxy` from the field; a new `dr-acp` value for "none". |
| D9 | **`dr-acp` checks a run's keys before it starts the worker.** It mirrors `build_client`'s rule exactly: a client fails when neither its `api_key_env` (default `NOVITA_API_KEY`) nor `OPENAI_API_KEY` holds a value, and its `base_url` is not `http://localhost…` or `http://127.0.0.1…`. It then answers with one sentence and starts no run. | The worker builds the main client for every run (`deep_reasoner/v2/cli.py:342`), and each tool's own client at build (`tools/base.py:152`). The worker never loads a `.env` (`load_dotenv` runs only on `dr`'s own command paths, `v2/cli.py:541, 692`). So the check's answer is the build's. No worker, no run log, nothing to replay. A contract test pins the mirror against the real `build_client`. | Matching the ValueError's text at `build_failed` (couples to deep_reasoner's wording). A setup-time check, which Michael ruled out. |
| D10 | **The build refuses a Canvas fork that cannot lock**, as check 5b. `defaults.json` must declare `agent.lockedProfile`, set to null. | Canvas `dr-3` ignores an unknown key. Without 5b, a build pinned to `dr-3` would write the lock and ship an unlocked app with every check green. | Relying on the pin bump's review. |

### 1.2 The deferred items, decided

**The lock's hook, and where each surface reads it.** `src/utils/agent-profile-lock.ts` (§5.1), read at call time.

| # | Surface (spec table) | Gate (Canvas `dr-3` lines) | Reads |
|---|---|---|---|
| 1 | Onboarding: Choose your agent, Set up LLM, Say hello | `use-onboarding-completion.ts:10–21`: completed when locked (D3) | `isAgentProfileLocked()` |
| 2 | "+" menu → Switch agent profile, Manage agent profiles | `chat-input-actions.tsx:76–81`: `showAgentProfileSwitch` false when locked | `isAgentProfileLocked()` |
| 3 | Settings → Agent (list and editor), `/settings/agent` and `/settings/agents` | `settings-utils.ts:52–58`: hidden (D4). The nav filters on it (`use-settings-nav-items.ts:28–31`), and the loader redirects (`routes/settings.tsx:32–37`) | `isAgentLockHiddenPath(path)` |
| 4 | Settings' landing page | `settings-utils.ts:60–78`: `getFirstAvailablePath` skips hidden paths and `/settings`, so it lands on `/settings/app` | `isAgentLockHiddenPath`, `isAgentProfileLocked()` |
| 5 | Command menu → Agent settings; Q2: LLM, Condenser | `command-menu-items.tsx:219–229`: an item whose `to` is hidden is dropped | `isAgentLockHiddenPath(item.to)` |
| 6 | Checklist → Customize agent; Q2: Configure LLM | `use-sidebar-onboarding-checklist.ts:115–127`: an item whose route is hidden is not listed, and counts and "all complete" are over the listed items | `isAgentLockHiddenPath(SIDEBAR_ONBOARDING_CHECKLIST_ROUTES[id])` |
| 7 | An automation's agent profile selector | `agent-profile-selector.tsx`: renders nothing when locked. `edit-automation-modal.tsx:232–236, 362–386` and `manifest-setup-dialog.tsx:169–175, 537–550` submit the locked id, and the model picker is hidden (a profile is set) | `useLockedAutomationProfileId()` |
| 8 | An ACP sign-in error's link to `/settings/agents` | `chat-interface.tsx:650–653`: `onReauth` undefined when locked | `isAgentProfileLocked()` |
| 9 | *(new, F5)* Application → Manage LLM profiles | `routes/app-settings.tsx:267–272`: not rendered when locked | `isAgentLockHiddenPath("/settings/llm")` |
| Q2 | LLM, Model Router, Condenser pages | as row 3: `/settings/llm`, `/settings/meta-llm`, `/settings/condenser` | `isAgentLockHiddenPath` |
| — | Launch: home, automations, every start | `use-create-conversation.ts:117–125`: the locked id always, whatever `agentProfileId` or the pointer says; no `agent_settings` fallback when locked; a missing profile throws | `selectLaunchAgentProfileId`, `getLockedAgentProfileName()` |
| — | "Current agent" reads (D2) | `use-active-agent-profile.ts:17`, `use-acp-session-preview.ts:49` (`resolveAcpLaunchProfile` returns null when the locked profile is missing), `use-chat-input-profile-state.ts:50–52`, `use-switch-acp-model.ts:74–78` | `selectLaunchAgentProfileId` |

**Where TASK-46's guard sits.** In `AutoTitleSubscriber._load_title_llm` (D5).

**How a provider connection's key counts.** Through the store's own resolution (D6).

**E12's order.** §7.4. Four constraints set it:
- the no-key reminder runs before the key is saved;
- the lock's launch test is the first conversation that answers, because `worker_environ` expects exactly one run;
- TASK-46's step comes after the key, so its first message is answered;
- the cap step comes before the MCP step, so the conversation it starts is the next one.

**Q3's three sub-questions.**
1. *The route and its auth:* D7. `GET` then `POST /api/agent-profiles/deep_reasoner`, sent by the page script through
   `host.agentServer.request`, with Canvas's session key (`X-Session-API-Key`). The server keeps the profile's id and
   bumps its revision (`agent_profiles_router.py:307–364`).
2. *Setup and a user's cap:* F3. No code change. Decision F's text changes (§10).
3. *"No cap":* D8.

---

## 2 · Canvas fork (`michaeltheologitis/OpenHands`, base `deep-reasoning`)

The fork's `AGENTS.md` binds both PRs:
- i18n through `npm run make-i18n` and `scripts/check-translation-completeness.cjs`, in all 15 locales;
- `// @spec` tags above each implementing block and test;
- specs under `specs/`;
- vitest beside or in the existing file;
- `npm run lint`, `npm test`, `npm run build`, `npm run build:lib` green;
- exact-pinned dependencies (no new ones here).

No new Agent Server endpoint or field is required, so `compatibility.minimumAgentServer` stays. With
`agent.lockedProfile` null, every existing vitest and Playwright test passes unchanged.

### 2.1 `feat/agent-lock` (TASK-50, Q1, Q2): one PR

**`config/defaults.json`**, a new top-level block after `setup`:

```json
"agent": {
  "_comment": "Optional agent profile name (not id) every conversation starts from. When set, Canvas shows no onboarding, no agent choice, no agent-profile editing, and no LLM, Model Router or Condenser settings; a start whose backend lacks the profile is refused. A build that ships its own agent sets it. null means unset: the active agent profile decides. Compiled into the frontend bundle, so never a secret.",
  "lockedProfile": null
}
```

Every reader of the file picks specific keys (`telemetry.ts:36`, `agent-server-compatibility.ts:14`, the launchers,
the Dockerfile's `defaults.env` generator, `Dockerfile:53–70`), so a new block changes nothing elsewhere.

**`src/utils/agent-profile-lock.ts`** (new), §5.1. `AGENT_LOCK_HIDDEN_SETTINGS_PATHS` is in
`src/constants/settings-nav.tsx`, beside `LOCKED_CLOUD_SETTINGS_NAV_PATHS`.

**The launch** (`use-create-conversation.ts`, `mutationFn`):
1. `lockedName = getLockedAgentProfileName()` and `launchId = selectLaunchAgentProfileId(agentProfiles)`, after the
   existing `ensureQueryData`.
2. If locked and `launchId === null`, throw `new LockedAgentProfileMissingError(lockedName)`. The global mutation toast
   shows its message (`query-client-config.ts:65–76`).
3. Otherwise `requestedAgentProfileId = locked ? launchId : (agentProfileId ?? launchId ?? undefined)`.
4. When locked, `prefersAgentSettingsFallback` is never set, so the profile path always runs. The fallbacks exist for
   the seeded OpenHands `default` (`:146–227`); a locked profile is a deliberate choice.

**Automations** (row 7). `useLockedAutomationProfileId()` (§5.1) returns `undefined` unlocked and the locked id when
locked (`null` while unknown or missing). Each form's effective profile is
`locked !== undefined ? locked : form.agentProfileId`, used both for hiding the model picker and in the submitted
body. A locked submit with `null` throws `LockedAgentProfileMissingError` through the forms' existing error paths.
Automations saved before this round keep what they name until they are next saved (no migration; §12 item 4).

**`specs/agent-profile-lock.md`** (new; IDs stable from here):
- **APL-001: Unset is upstream.** With `agent.lockedProfile` null, every surface and every launch shall behave as
  without this spec.
- **APL-002: Every start runs the locked profile.** Each conversation and automation shall start from the agent
  profile whose name is `agent.lockedProfile`, whatever the active profile, and never from the global agent settings.
- **APL-003: A missing locked profile starts nothing.** A start whose backend lists no profile by that name shall be
  refused with `AGENT_LOCK$PROFILE_MISSING`, and nothing shall be created.
- **APL-004: No agent choice.** No onboarding, no agent-profile switch, no automation agent-profile selector, and no
  link from an ACP sign-in error to agent settings shall be shown. A missing backend still gets upstream's backend
  recovery.
- **APL-005: No agent or LLM configuration.** The Agent, LLM, Model Router and Condenser settings pages shall be hidden
  and their paths redirected to the first available page. Command-menu entries, checklist items and links whose
  destination is one of them shall not be shown.
- **APL-006: Stable test ids.** `command-menu-item-<id>` on each command-menu entry (new, for end-to-end tests).

**i18n**: one key, `AGENT_LOCK$PROFILE_MISSING`, `en`: "This app runs only the agent profile '{{name}}', which this
backend does not have. Restart the app." (the spec's failure cell), in all 15 locales.

**vitest**: §7.1.

### 2.2 `fix/subagent-costs-on-by-default` (TASK-51): one PR

- `src/components/conversation-events/chat/subagents/subagent-cost-preference.ts`:
  - `readShowSubagentCosts` becomes `typeof window === "undefined" || localStorage.getItem(KEY) !== "false"`;
  - the server snapshot becomes `() => true`;
  - the doc line becomes "on until the user turns it off".
  - `writeShowSubagentCosts` is unchanged, so a saved `"false"` stays off and a saved `"true"` stays on.
- `specs/acp-subagent-sessions.md` SUB-006 becomes: "A sub-agent's cost shall be shown unless the user turns off the
  App setting "Show sub-agent costs", which this browser keeps across reloads; each sub-agent shall show its latest
  reported cost; costs shall never be added." Every `// @spec SUB-006 — …` line becomes "Costs show unless the
  setting is off; each sub-agent shows its latest reported cost, never a sum", in `subagent-cost-preference.ts:20`,
  `subagent-block.test.tsx:152`, `subagent-costs-switch.test.tsx:47, 62, 77`, `subagent-status.test.ts:126` and
  `mock-llm-acp-subagents.spec.ts:97`.
- Tests: §7.1.

### 2.3 `chore/wire-sdk-dr-3`: the wiring commit (not read at Gate C)

- `config/defaults.json`: `sources.agentServerGitRef` set to `dr-3`'s commit, and `_agentServerGitRefComment` set to
  "tag dr-3 of michaeltheologitis/software-agent-sdk".
- `package.json`: `@openhands/typescript-client` from `…/releases/download/dr-3/openhands-typescript-client-<v>.tgz`,
  with `package-lock.json` updated by `npm install <url>` (its integrity hash).

`build.py` checks 2 and 3 refuse anything else.

---

## 3 · SDK fork (`michaeltheologitis/software-agent-sdk`, base `deep-reasoning`): `fix/title-llm-without-credentials`

One PR, TASK-46. The SDK's `AGENTS.md` binds it:
- pre-commit per changed file;
- no `# type: ignore`;
- every commit carries "Co-authored-by: openhands <openhands@all-hands.dev>", besides this session's trailers;
- the PR template's `HUMAN:` section is left as the placeholder for Michael.

**`openhands-agent-server/openhands/agent_server/agent_profiles_router.py`**:
- `_llm_has_real_config` is renamed to `llm_has_real_config`, with its body unchanged. It now has a second caller in
  another module, so it is no longer private.
- Its docstring gains one sentence: "Also gates auto-titling's title LLM (`AutoTitleSubscriber`)."
- `_seed_default_llm_profile` calls the new name.

**`openhands-agent-server/openhands/agent_server/conversation_service.py`**:
- a module-level `from openhands.agent_server.agent_profiles_router import llm_has_real_config`. Verified free of
  cycles at `dr-2`: neither module loads the other;
- `AutoTitleSubscriber._load_title_llm` (`:2830–2854`), after the load:
  `if not llm_has_real_config(llm): logger.info(f"Title LLM profile '{profile_name}' has no credential; falling back to the agent's LLM."); return None`.
  The store import stays function-local, because the tests patch `openhands.agent_server.persistence.store.get_llm_profile_store`;
- the precedence comment in `__call__` (`:2792–2794`) becomes "title_llm_profile (configured, loads, and has a
  credential) → agent.llm → truncation".

For a profile-launched ACP agent, `agent.llm` is the `acp-managed` sentinel, which `generate_title_from_message`
already skips (`title_utils.py:209–212`). The title is then the first message cut to 50 characters, and nothing is
published.

**Tests** (`tests/agent_server/test_conversation_service.py`, class `TestAutoTitle`):
- new: `test_autotitle_skips_a_title_profile_without_a_credential` (a keyless `gpt-5.5` from the mocked store, no
  `base_url`; the agent LLM is the sentinel; `LLM.completion` patched to fail if called). It asserts the truncated
  title, `_publish_error_event_sync` not called, and no LLM call;
- new: `test_autotitle_still_surfaces_the_error_of_a_title_profile_with_a_key` (`api_key=SecretStr("sk-wrong")`,
  `LLM.completion` raising). It asserts one `_publish_error_event_sync` call, as #16686 intends;
- new: `test_autotitle_counts_a_provider_connections_key_as_a_credential`. A real `LLMProfileStore` with a
  `ProviderConnectionStore` holding a keyed connection, and the profile referencing it with no inline key, follows
  `test_autotitle_integration_routes_through_profile_store` (`:3487`). It asserts the title LLM is used;
- changed fixtures: `test_autotitle_uses_llm_profile_when_configured` (`:3330`) and
  `test_autotitle_uses_title_profile_for_settings_built_acp_agent` (`:3465`) give their profile LLMs
  `api_key=SecretStr("title-key")`. Their keyless LLMs were incidental, and their properties (the profile LLM wins)
  are unchanged;
- `tests/agent_server/test_agent_profiles_router.py::test_llm_has_real_config` (`:314–317`) follows the rename.

The ACP sentinel's behaviour stays pinned by the existing `test_autotitle_falls_back_for_acp_managed_llm`.

---

## 4 · deep-reasoning (branch `ux-round`)

### 4.1 `desktop/build.py` and `desktop/pins.toml`

**`patch_defaults`** gains one keyword, `app_title` (§13), and writes two more keys: `agent.lockedProfile` =
`LOCKED_PROFILE` and `branding.appTitle` = `app_title`. `LOCKED_PROFILE = "deep_reasoner"` mirrors `dr_app.profile.PROFILE_NAME`,
because `build.py` imports nothing of ours. A test pins the two equal.

**`check_pins`**:
- checks 5 and 5b (D10; v1.1, §13) are one loop over `FORK_NULL_KEYS`. A key the fork's `defaults.json` lacks appends
  `fork_lacks_setting(canvas_pin.tag, key)`, and one it sets appends `fork_sets_ours` (unchanged) (§6.4).

**`desktop/pins.toml`**, at the end of the round (§8):
- `[canvas_fork] commit = "<dr-4's 40 hex>"`, `tag = "dr-4"`;
- `[sdk_fork] commit = "<dr-3's 40 hex>"`, `tag = "dr-3"`.

Both pins move in one commit, as check 2 requires.

### 4.2 `dr-app`: setup's lines (TASK-42, Q1, TASK-44)

- `dr_app/texts.py`:
  - `safety` and `NO_MODEL_KEY` go;
  - `NO_GIT`, `PROFILE_CREATED`, `PROFILE_UPDATED`, `installing`, `install_failed` and `home_too_long` are reworded
    (§6.1).
- `desktop/bootstrap.sh:8` echoes the new `NO_GIT`, byte for byte; `tests/app/test_bootstrap.py:40` compares the two.
- `dr_app/cli.py`:
  - `install` loses `first` and its `say(texts.safety(...))` (`:126–127`), and `before_start` stops computing `first`
    (`:98–99`);
  - `SECRETS`, `MODEL_KEY`, `NOT_A_MODEL_KEY` and `model_key_missing` go, with after-ready's hint block (`:155–159`).
    Its docstring becomes "§4.5: the agent profile, the Library App";
  - the `DEFAULT_SPEND_CAP_USD` import goes if nothing else uses it.
- `dr_app/profile.py`: docstrings only, for decision F's new text (§10). `PROFILE_NAME` stays `deep_reasoner` (spec
  decision 3).

### 4.3 `dr-acp`: the reminder (Q1), the refusal (Q3), names (TASK-44)

- **`deep_reasoning/acp/route.py`**:
  - `OPENAI_FALLBACK_KEY_ENV` and `DEEP_REASONER_DEFAULT_KEY_ENV` move here from `proxy.py`, which imports them back;
  - `KEYLESS_BASE_URL_PREFIXES` and `missing_model_keys` (§5.3) are new.
- **`deep_reasoning/acp/session.py` `_start_run`** (`:188–219`): after `_materialize` succeeds and before
  `RunHandle.start`:
  - `if missing := missing_model_keys([source.client, *source.tool_clients.values()], os.environ): return await self._reply(texts.missing_model_key(missing), "build_failed")`.
  - `os.environ` is the environment `worker_env(os.environ, grant)` derives the worker's from (tokens keep a held key's
    name), so presence is the same with the proxy on or off.
  - `_reply` writes nothing to any run log, so nothing replays. The session stays un-run, and the next conversation,
    after the key is saved, starts normally. A conversation's `dr-acp` gets its secrets once, at its launch
    (`acp_agent.py:3306–3331`), so the sentence says to start a new one.
- **`deep_reasoning/acp/texts.py`**: `missing_model_key` (new); `cap_reached` names the panel field; `ROOT_STOPPED`
  says Deep Reasoning and drops "(ask A3)" (§6.2).
- **`deep_reasoning/acp/agent.py:104`**: `agentInfo.title` becomes "Deep Reasoning".

### 4.4 The Library panel (`canvas-app/`, rebuilt into `src/deep_reasoning/canvas_app/`)

**Goes (TASK-42):**
- `SAFETY`, `SAFETY_NO_CAP`, `UNDERSTAND` and `TOOLS_RISK` (`ui/texts.ts:3–7, 108`);
- `SafetyNotice` (`ui/components/notices.tsx:7–36`; `ProblemsBanner` stays);
- `app.tsx`'s acknowledgement gate (`:69–86`) and its imports;
- `SAFETY_ACK_KEY`, `safetyAcknowledged` and `acknowledgeSafety` (`ui/drafts.ts:4, 43–49`). A stored `1` is left
  behind, harmlessly;
- the Tools tab's two banners (`tabs/tools.tsx:74–78`).

**Stays (Q3 revises TASK-42):** `readSpendCap`, `spendCapFromArgs`, the frame's `cap=` (`protocol.ts:70, 125, 196–202`)
and `mount.ts:107–124`.

**New: the Spend cap field (Q3, D7, D8)**, at the top of the Tools tab, where the banners were:

```text
Spend cap
The most one conversation may spend on model calls through the key proxy. New conversations use it; a
conversation already started keeps its cap.
$ [ 5      ]  [Save]
✓ Saved: new conversations stop at $12.50.          ← dr-spend-cap-status, after a save

with --no-key-proxy:  No cap: the key proxy is off for Deep Reasoning (--no-key-proxy), so nothing caps what a
                      conversation spends.          (no input)
on the standalone page: $5 (read-only) · Change it in the app, under Show Decompositions → Tools.
```

The sequence:
1. Save checks the field locally with `isSpendCapInput`. An invalid amount shows `SPEND_CAP_INVALID` and sends nothing.
2. The frame posts `{type: "dr-library/set-spend-cap", cap}` to `params.parent` and shows `SPEND_CAP_SAVING`.
3. The page's `mountTab` accepts it only from its own frame (the existing `event.source` check, `mount.ts:75–82`) and
   only when `isFrameMessage` holds. It calls `writeSpendCap(host.agentServer.request, cap)`.
4. `writeSpendCap` runs `GET /api/agent-profiles/deep_reasoner`, then `withSpendCap(profile.acp_args ?? [], cap)`, then
   `POST` of `{...profile, acp_args}`. It refuses without sending a POST when `withSpendCap` returns null.
5. The page replies to `frame.contentWindow` with targetOrigin `new URL(frame.src, location.href).origin`:
   `dr-library/spend-cap-saved {cap}` or `dr-library/spend-cap-refused {message}`.
6. The frame accepts a reply only from `window.parent`, with `event.origin === params.parent` and `isPageMessage`. It
   then shows `SPEND_CAP_SAVED(cap)` and keeps the new value, or the message.

Other tabs never show the cap. A remount reads it again (`readSpendCap`).

**TASK-43:** `src/deep_reasoning/canvas_app/panel.svg`'s root `stroke="currentColor"` becomes `stroke="#A78BFA"`,
7.1:1 on `#0B0E14` and 5.63:1 on `#21252F` (computed). `canvas-app` ships the icon as committed (`stage_canvas_app`
stages it), so this is the one edit.

**TASK-44 in the panel**: `NOT_SET`, `MCP_NOT_IN_PROFILE`, `MCP_SHIM_OLD` and `TOOL_HELP`'s clause (§6.3); the
manifest's `description` (§6.3).

**Rebuilt:** `npm run build` writes `src/deep_reasoning/canvas_app/dist/index.js` and `ui/assets/*`.
`ci.yml`'s "The committed build is what a fresh build gives" step pins them. `panel.svg`, the manifest and
`dist/index.js` change the staged App's digest, so the next launch reinstalls and re-approves the App once
(`canvas_app.py:138–150`). No version bump is needed.

### 4.5 Library and tools texts (TASK-44)

`library/texts.py`'s `UI_NOT_BUILT`, `invalid` and `import_load`, and `tools/texts.py`'s `reserved_name`,
`ready_timeout` and `builtin` (§6.3).

Kept, as code, a version or a path:
- `stale_head`'s `deep_reasoner {build}`;
- the two docstrings that cite `deep_reasoner v2/cli.py`;
- `NEW_TOOL_SOURCE`'s `from deep_reasoner import Func`;
- `context.ts`'s `PROFILE_PATH`;
- `build.py`'s maintainer sentences.

### 4.6 README (Q4 (a), Q1, TASK-44)

- **The first launch**. The heading is kept: TASK-48 links to it.
  - The setup list loses step 3 (the safety line). Step 4 reads "installs Deep Reasoning and deep_reasoner, …". Step 5
    reads "makes Deep Reasoning's agent profile the default, and …".
  - "Then, in the window" becomes: "The window opens on the home screen. Before your first question, add
    `OPENAI_API_KEY` under **Settings → Secrets**, with your OpenAI API key as its value. If you ask first, Deep
    Reasoning answers with where the key goes. Then start a conversation and ask."
  - The Choose your agent, Say hello and Close steps, and "Until one is saved, every launch's setup says so", go.
- **What the app protects, and what it does not**: kept as reference.
  - Its opening sentence ("Setup says this … the first time it opens") and the quoted warning go.
  - Its last paragraph becomes: "The cap is $5 per conversation unless you change it under **Show Decompositions →
    Tools → Spend cap**. New conversations use the new cap, and setup keeps it."
  - The bullet "get past the cap: … raise the cap in the profile …" stays: it is still true of a cell.
- **Prose** follows TASK-44's rule. "Show decompositions" becomes **Show Decompositions** (F7). Dean's package keeps its
  name where the sentence is about the package.

---

## 5 · Signatures

### 5.1 Canvas fork

```ts
// src/utils/agent-profile-lock.ts
// @spec APL-001, APL-002

/** defaults.json's agent.lockedProfile, read when called: the name, trimmed; null when unset, empty
 * or not a string. */
export function getLockedAgentProfileName(): string | null;

export function isAgentProfileLocked(): boolean;

/** In a locked build: path is one of AGENT_LOCK_HIDDEN_SETTINGS_PATHS, or below one ("/x/…").
 * Unlocked: always false. */
export function isAgentLockHiddenPath(path: string): boolean;

/** The profile id a start launches from and every "current agent" reads. Locked: the id of the
 * profile whose name is the locked name, or null when the list has none. Unlocked:
 * active_agent_profile_id ?? null. */
export function selectLaunchAgentProfileId(
  list: Pick<AgentProfileListResponse, "profiles" | "active_agent_profile_id">,
): string | null;

/** A start or automation save in a locked build whose backend has no profile of that name. Its message is
 * i18n.t(AGENT_LOCK$PROFILE_MISSING, {name}), which the global mutation toast shows. */
export class LockedAgentProfileMissingError extends Error {
  readonly profileName: string;
  constructor(profileName: string);
}

// src/constants/settings-nav.tsx
export const AGENT_LOCK_HIDDEN_SETTINGS_PATHS: ReadonlySet<string>; // "/settings/agents", "/settings/agent",
// "/settings/llm", "/settings/meta-llm", "/settings/condenser"

// src/components/features/automations/agent-profile-selector.tsx
/** undefined in an unlocked build (the form's choice stands). Locked: the locked profile's id, or null while the
 * list loads or when it lacks the profile. */
export function useLockedAutomationProfileId(): string | null | undefined;
// AutomationAgentProfileSelector: returns null when isAgentProfileLocked().

// src/hooks/query/use-acp-session-preview.ts: the return type widens
export function resolveAcpLaunchProfile(
  profiles: AgentProfileListResponse, backendId: string, orgId: string | null,
): AcpLaunchProfile | null; // null: locked, and the profile is missing (the caller already takes null)
```

Unchanged signatures with new behaviour:
- `useActiveAgentProfile`, `useChatInputProfileState`, `useSwitchAcpModel` and `useCreateConversation` (§1.2);
- `isSettingsPageHidden(path, flags)`: also true for `isAgentLockHiddenPath(path)`;
- `getFirstAvailablePath(flags)`: also skips hidden paths and `/settings` when locked;
- `useOnboardingCompletion().isCompleted`: true when locked;
- `createCommandMenuItems` and `useSidebarOnboardingChecklist`: hidden destinations dropped;
- `CommandMenu`: each entry rendered with `data-testid={`command-menu-item-${item.id}`}`.

### 5.2 SDK fork

```python
# openhands-agent-server/openhands/agent_server/agent_profiles_router.py
def llm_has_real_config(llm: LLM) -> bool:
    """(was _llm_has_real_config; body unchanged) A real API key, subscription auth, or a custom endpoint. …
    Also gates auto-titling's title LLM (AutoTitleSubscriber)."""

# openhands-agent-server/openhands/agent_server/conversation_service.py
class AutoTitleSubscriber(Subscriber):
    def _load_title_llm(self) -> LLM | None:
        """The title LLM from title_llm_profile, as the profile store loads it (a provider connection's key and
        base URL applied). None when the profile is unset, fails to load, or has no credential
        (llm_has_real_config); the caller then falls back to the agent's LLM, then to truncation."""
```

### 5.3 deep-reasoning

```python
# desktop/build.py
# dr_app.profile.PROFILE_NAME, mirrored: this file imports nothing of deep-reasoning's.
LOCKED_PROFILE: Final = "deep_reasoner"

# The defaults.json keys this build writes that the Canvas fork must declare, as null (checks 5 and 5b).
FORK_NULL_KEYS: Final = ("paths.stateDir", "setup.command", "agent.lockedProfile", "branding.appTitle")

def fork_lacks_setting(canvas_tag: str, key: str) -> str: ...   # §6.4 (v1.1: was fork_lacks_lock)

def patch_defaults(
    defaults: Mapping[str, Any],
    *,
    state_dir: str,
    command: list[str],
    app_title: str,
) -> dict[str, Any]:
    """§4.2.3's four keys, agent.lockedProfile = LOCKED_PROFILE and branding.appTitle = app_title (the
    callers pass pins.app.product_name); every other key unchanged."""

# check_pins: signature unchanged; checks 5 and 5b one loop over FORK_NULL_KEYS (v1.1).

# packages/dr-app/src/dr_app/cli.py
def install(layout: AppLayout, repo: str, commit: str, *, env: Mapping[str, str]) -> RuntimeRecord: ...
# (no `first`; no safety line). Removed: SECRETS, MODEL_KEY, NOT_A_MODEL_KEY, model_key_missing.

# src/deep_reasoning/acp/route.py
OPENAI_FALLBACK_KEY_ENV: Final = "OPENAI_API_KEY"   # build_client's fallback (moved from proxy.py)
DEEP_REASONER_DEFAULT_KEY_ENV: Final = "NOVITA_API_KEY"  # ClientConfig.api_key_env's default (moved)
# build_client gives a client on these an "EMPTY" key instead of refusing.
KEYLESS_BASE_URL_PREFIXES: Final = ("http://localhost", "http://127.0.0.1")

def missing_model_keys(
    clients: Iterable[Mapping[str, Any]],
    env: Mapping[str, str],
) -> list[str]:
    """The key variables the clients would fail to build without, as deep_reasoner's build_client decides:
    a client's api_key_env (DEEP_REASONER_DEFAULT_KEY_ENV when unset) when neither it nor
    OPENAI_FALLBACK_KEY_ENV has a non-empty value in env, and its base_url does not start with one of
    KEYLESS_BASE_URL_PREFIXES. Each name once, in the clients' order; empty when every client builds."""

# src/deep_reasoning/acp/texts.py
def missing_model_key(names: Sequence[str]) -> str: ...      # §6.2
def cap_reached(spent: float, cap: float) -> str: ...        # §6.2, reworded
```

```ts
// canvas-app/src/shared/protocol.ts
export type FrameMessage =
  | { type: "dr-library/select-tab"; tab: TabId; focus: string | null }
  | { type: "dr-library/reload" }
  | { type: "dr-library/set-spend-cap"; cap: string }; // new: frame → page

/** new: page → frame, the answer to set-spend-cap */
export type PageMessage =
  | { type: "dr-library/spend-cap-saved"; cap: string }
  | { type: "dr-library/spend-cap-refused"; message: string };

/** 1 to 6 digits, then at most two decimals, and above 0: "5", "12.5", "12.50". */
export function isSpendCapInput(value: string): boolean;
/** As today, plus set-spend-cap: exactly {type, cap} with isSpendCapInput(cap). */
export function isFrameMessage(value: unknown): value is FrameMessage;
/** Exactly one of PageMessage's two shapes; the message a string. */
export function isPageMessage(value: unknown): value is PageMessage;

// canvas-app/src/page/context.ts
/** args with the --spend-cap-usd pair set to cap: the value after "--spend-cap-usd" replaced, or a
 * "--spend-cap-usd=v" element replaced by the pair at its place, or the pair appended. Every other
 * element keeps its place. null when args hold --no-key-proxy. */
export function withSpendCap(args: readonly string[], cap: string): string[] | null;

export type SpendCapWrite =
  | { ok: true; cap: string }
  | { ok: false; message: string }; // §6.3's CAP_PROFILE_MISSING, CAP_NO_PROXY or CAP_NOT_SAVED(detail)

/** GET PROFILE_PATH; withSpendCap(profile.acp_args ?? [], cap); POST PROFILE_PATH with the profile and
 * the new acp_args. Never throws: a 404 is CAP_PROFILE_MISSING, null args CAP_NO_PROXY, any other
 * failure CAP_NOT_SAVED with the error's message. */
export async function writeSpendCap(
  request: AgentServerRequest,
  cap: string,
): Promise<SpendCapWrite>;

// canvas-app/src/page/mount.ts: onMessage, for set-spend-cap, writeSpendCap then replies to the frame
// (§4.4 steps 3–5); no other change.

// canvas-app/src/ui/components/spend-cap.tsx (new)
export function SpendCapField(props: { params: FrameParams }): JSX.Element;
// test ids: dr-spend-cap (the section), dr-spend-cap-input, dr-spend-cap-save, dr-spend-cap-status
```

---

## 6 · Texts (verbatim; tests assert these)

### 6.1 `dr_app.texts`

| Name | Sentence |
|---|---|
| `NO_GIT` (and `bootstrap.sh:8`) | ✗ Deep Reasoning is installed with git, which was not found. On macOS run xcode-select --install; on Linux install git. |
| `PROFILE_CREATED` | Deep Reasoning's agent profile created and made the default |
| `PROFILE_UPDATED` | Deep Reasoning's agent profile updated |
| `installing(commit7, dr_commit7)` | installing Deep Reasoning {commit7} with deep_reasoner {dr_commit7} … (first launch, or after an update: a few minutes) |
| `install_failed(commit7, step, code)` | ✗ Installing Deep Reasoning {commit7} failed ({step} exited {code}); its output is above. After an update this needs the network once: connect and restart. |
| `home_too_long(home, length, limit)` | ✗ {home} is too long a path for your data: Deep Reasoning's Claude runs serve sockets under it up to {length} bytes long, and this system allows {limit}. Choose a shorter folder with dr-app home DIR. |
| `safety`, `NO_MODEL_KEY` | removed |

### 6.2 `deep_reasoning.acp.texts`

| Name | Sentence |
|---|---|
| `missing_model_key(["OPENAI_API_KEY"])` | Deep Reasoning needs OPENAI_API_KEY to answer: add it under Settings → Secrets, then start a new conversation. |
| `missing_model_key(["OPENAI_API_KEY", "NOVITA_API_KEY"])` | Deep Reasoning needs OPENAI_API_KEY and NOVITA_API_KEY to answer: add them under Settings → Secrets, then start a new conversation. (Three or more: "A, B and C".) |
| `cap_reached(spent, cap)` | The key proxy refused this model call: this conversation has spent ${spent:.2f} of its ${cap:.2f} cap. Start a new conversation, or raise the cap for new conversations under Show Decompositions → Tools → Spend cap. |
| `ROOT_STOPPED` | Stopped. The run was ended and its REPL state is gone: Deep Reasoning cannot cancel a running cell yet. Your next message starts a fresh run. |
| `agent.py` `agentInfo.title` | Deep Reasoning |

### 6.3 The panel, the Library, the tools

| Where · name | Sentence |
|---|---|
| `ui/texts.ts` `SPEND_CAP` | Spend cap |
| `SPEND_CAP_HELP` | The most one conversation may spend on model calls through the key proxy. New conversations use it; a conversation already started keeps its cap. |
| `SPEND_CAP_SAVE` · `SPEND_CAP_SAVING` | Save · Saving… |
| `SPEND_CAP_SAVED(cap)` | ✓ Saved: new conversations stop at ${cap}. |
| `SPEND_CAP_INVALID` | Enter an amount in dollars above 0, such as 5 or 12.50. |
| `SPEND_CAP_OFF` | No cap: the key proxy is off for Deep Reasoning (--no-key-proxy), so nothing caps what a conversation spends. |
| `SPEND_CAP_STANDALONE` | Change it in the app, under Show Decompositions → Tools. |
| `page/texts.ts` `CAP_PROFILE_MISSING` | Deep Reasoning's agent profile is missing. Restart Deep Reasoning, which creates it again. |
| `CAP_NO_PROXY` | The key proxy is off for Deep Reasoning (--no-key-proxy), so there is no cap to set. |
| `CAP_NOT_SAVED(detail)` | The cap was not saved: {detail} |
| `NOT_SET` | Not set: Deep Reasoning's default |
| `MCP_NOT_IN_PROFILE` | Not given to Deep Reasoning: its agent profile lists other MCP servers. |
| `MCP_SHIM_OLD` | Granted by an older Deep Reasoning. |
| `TOOL_HELP`'s clause | (Deep Reasoning passes no config_path to factory_from tools) |
| `canvas-extension.json` `description` | Deep Reasoning's decompositions, namespaces and tools, from Show Decompositions at the top right of a conversation. |
| `SAFETY`, `SAFETY_NO_CAP`, `UNDERSTAND`, `TOOLS_RISK` | removed |
| `library/texts.py` `UI_NOT_BUILT` | The panel's files are not in this installation: reinstall Deep Reasoning, or run npm run build in canvas-app/. |
| `invalid(name, model, errors)` heading | {subject} is not a valid Deep Reasoning {model}: |
| `import_load(path, detail)` | {path} is not a dr config Deep Reasoning can load: {detail} |
| `tools/texts.py` `reserved_name(name)` | '{name}' is one of Deep Reasoning's own names in the REPL (subagent, run_all, FinalAnswer, Var, Func, task); a tool by that name would hide it. Choose another name. |
| `ready_timeout(seconds)` | Check could not start Deep Reasoning within {seconds:g} s, so it did not build the tool. Try again. |
| `builtin(factory)` | '{factory}' is one of Deep Reasoning's own factories. It is built when a conversation starts, with your model and files, so Check does not build it here. |

### 6.4 `desktop/build.py`

| Name | Sentence |
|---|---|
| `fork_lacks_setting(canvas_tag, key)` (v1.1) | ✗ Canvas fork {canvas_tag}'s config/defaults.json has no {key}, so this build cannot set it: pin dr-4 or later. |

---

## 7 · Tests and CI

No test calls a model. Each name states the property it pins.

### 7.1 Unit and component tests, per repo

**SDK fork:** §3.

**Canvas fork, `feat/agent-lock`.** vitest sets the lock by assigning `agent.lockedProfile` on the imported
`config/defaults.json` object in `beforeEach` and restoring null in `afterEach`, through one helper,
`__tests__/helpers/agent-lock.ts` `lockAgentProfile(name)`. Every test tagged `// @spec APL-00n`; each file below gains
its cases:
- `__tests__/utils/agent-profile-lock.test.ts` (new): `reads no lock when the key is null, empty or not a string`;
  `selects the active profile when unlocked`; `selects the locked profile by name whatever the active pointer says`;
  `selects nothing when the locked profile is missing`; `hides the five pages and their sub-paths only when locked`.
- `__tests__/hooks/mutation/use-create-conversation.test.tsx`: `launches the locked profile even when another is
  active or requested`; `never launches from agent_settings when locked`; `refuses a start when the locked profile is
  missing, and creates nothing`.
- `__tests__/components/onboarding/use-onboarding-completion.test.tsx` and `__tests__/root.test.tsx`: `reads as
  completed in a locked build`; `shows no first-run onboarding in a locked build`.
- `__tests__/components/features/chat/components/chat-input-actions.test.tsx`: `offers no agent profile switch in a
  locked build`.
- `__tests__/utils/settings-utils.test.ts`, `__tests__/hooks/use-settings-nav-items.test.tsx` and
  `__tests__/routes/settings-index.test.tsx`: `lists only Agent Context, Verification, Application and Secrets when
  locked`; `redirects each hidden page to /settings/app`; `lands on /settings/app`.
- `__tests__/components/features/command-menu/command-menu-items.test.tsx`: `drops the Agent, LLM and Condenser
  entries when locked`; `command-menu.test.tsx`: `marks each entry with command-menu-item-<id>`.
- `__tests__/components/features/sidebar/sidebar-onboarding-checklist.test.tsx`: `lists no Configure LLM or Customize
  agent item when locked, and counts only what it lists`.
- `src/components/features/automations/agent-profile-selector.test.tsx`,
  `__tests__/components/automations/detail/edit-automation-modal.test.tsx` and
  `__tests__/components/manifest/manifest-setup-dialog.test.tsx`: `shows no agent profile selector when locked`; `saves
  an automation with the locked profile and no model`.
- `__tests__/components/chat/chat-interface.test.tsx`: `offers no agent-settings link on an ACP sign-in error when
  locked`.
- `__tests__/routes/app-settings.test.tsx`: `shows no Manage LLM profiles link when locked`.

Each "when locked" case has an unlocked twin wherever the file has none already.

**Canvas fork, `fix/subagent-costs-on-by-default`:**
- `subagent-costs-switch.test.tsx`: "is off by default …" becomes `is on by default and hides sub-agent costs while
  off`; "keeps sub-agent costs shown across a reload" becomes `keeps sub-agent costs hidden across a reload once
  turned off`; the other-tab case fires `newValue: "false"`.
- `subagent-block.test.tsx:152`: the `writeShowSubagentCosts(true)` line goes, since on is the default.
- Live 2 (`tests/e2e/mock-llm/conversations/mock-llm-acp-subagents.spec.ts:137–161`) asserts the cost before touching
  the setting, then turns it off and asserts none.
- `tests/e2e/mock-llm/utils/acp-subagents.ts` `showSubagentCosts` becomes `hideSubagentCosts`, which clicks the switch
  to unchecked.

**deep-reasoning, default suite:**
- `tests/desktop/test_build.py`:
  - `test_defaults_gain_only_d5s_four_keys` becomes `test_defaults_gain_only_the_keys_the_build_writes`, against
    `FORK_NULL_KEYS` plus `setup.phases` and `telemetry.posthogApiKey`, so a new key edits one constant (v1.1);
  - `test_a_fork_that_carries_our_values_is_refused` gains `agent.lockedProfile` and `branding.appTitle`;
  - new `test_a_canvas_fork_that_lacks_a_setting_the_build_writes_is_refused[agent.lockedProfile, branding.appTitle]`
    (v1.1);
  - new `test_the_locked_profile_is_the_one_setup_creates`;
  - the fake Canvas `defaults.json` gains `"agent": {"lockedProfile": null}` and `"branding": {"appTitle": null}`;
  - `test_the_committed_sdk_pin_is_34c540c_tagged_dr_2` becomes `…_<dr-3 short>_tagged_dr_3`, at the bump.
- `tests/app/test_texts.py`: the verbatim cases follow §6.1, and `safety` goes.
- `tests/app/test_runtime.py:79, 130`: the first install's lines are home, checks, installing, …, with no safety line.
- `tests/app/test_cli.py`:
  - `test_a_hand_run_does_both_phases_when_the_agent_server_is_up` drops `NO_MODEL_KEY`;
  - new `test_after_ready_reads_no_secrets_and_prints_no_key_line`. The fake agent-server records no
    `GET /api/settings/secrets`, and no line names a key.
- `tests/acp/test_texts.py`: `cap_reached`, `missing_model_key` and `ROOT_STOPPED` are verbatim.
- `tests/acp/test_route.py`: new `test_missing_model_keys_says_what_build_client_refuses[…]`. It is a contract test:
  for each of about 8 cases (key set or unset, the fallback set, `api_key_env` absent, `base_url` remote, localhost,
  127.0.0.1 or absent), the names are non-empty exactly when deep_reasoner's real `build_client` raises its ValueError
  under the same `monkeypatch`ed environment.
- `tests/acp/test_agent.py`: new `test_a_question_without_its_model_key_is_answered_with_where_the_key_goes_and_runs_nothing`.
  It drives `dr-acp` (the harness) on a config whose client is remote and keyless, in an environment without the key.
  It asserts the reply is `missing_model_key(["OPENAI_API_KEY"])`, the stop reason `end_turn`, no run under `runs/`
  and no worker.
- `tests/canvas_app/` (browser):
  - `test_notice.py` goes;
  - `conftest.py`'s `SAFETY_ACK` and `open_ui(notice=)` go, with their uses in `test_page_bundle.py:115`,
    `test_backend_loss.py:30` and `test_e8_next_conversation.py:33`;
  - `test_tools_tab.py`: `test_the_tools_tab_always_shows_the_safety_notice_with_the_cap` and `TOOLS_RISK` go. New:
    - `test_the_tools_tab_shows_the_cap_and_no_warning[5, 12.50]`;
    - `test_without_the_key_proxy_the_field_says_nothing_caps_spending`;
    - `test_on_the_standalone_page_the_cap_is_shown_and_not_editable`;
    - `test_an_amount_that_is_not_dollars_above_zero_is_refused_before_anything_is_sent[0, -1, 1.234, abc, empty]`;
  - `test_page_bundle.py`. The fake host's `answer` gains `POST /api/agent-profiles/deep_reasoner`, recording bodies. New:
    - `test_each_tab_opens_on_its_content_with_no_dialog[browse, create, namespaces, tools]`;
    - `test_the_spend_cap_field_writes_the_profiles_cap_and_keeps_its_other_arguments` (body `acp_args` `["--home",
      …, "--spend-cap-usd", "12.50"]` in place; the frame shows `SPEND_CAP_SAVED("12.50")`);
    - `test_a_cap_the_page_cannot_write_says_why_in_the_field` (a 404 gives `CAP_PROFILE_MISSING`);
  - `test_panel_icon.py` (new): `test_the_panel_icon_is_visible_on_canvas_header`. Every `stroke` and `fill` of
    `panel.svg` is `none` or a hex colour of at least 3:1 on `#0B0E14`; `currentColor` fails.
- `canvas-app/tests/` (vitest):
  - `drafts.test.ts` loses "the safety notice's acknowledgement";
  - `context.test.ts` gains `withSpendCap` (pair, `=` form, absent, `--no-key-proxy`) and `writeSpendCap`
    (`GET` then `POST` with the profile whole; 404; failure);
  - `protocol.test.ts` gains `isSpendCapInput`, `isFrameMessage`'s set-spend-cap and `isPageMessage`;
  - `mount.test.ts` gains `writes the cap a frame asks for and answers only that frame` and `ignores set-spend-cap from
    any window but its frame's`.
- `tests/desktop/test_readme.py`:
  - `test_the_key_is_the_one_setup_asks_for_where_setup_says` becomes `test_the_key_is_the_one_dr_acp_asks_for_where_it_says`.
    The README's plain text holds `add OPENAI_API_KEY under Settings → Secrets`. The key is `starter.yaml`'s
    `client.api_key_env`, and the place is `missing_model_key`'s;
  - `test_the_safety_section_quotes_setup_with_the_cap_setup_sets` becomes
    `test_the_cap_section_names_the_default_cap_and_the_field_the_refusal_names`. It checks
    `$`+`DEFAULT_SPEND_CAP_USD` and `cap_reached`'s "under …" clause.

### 7.2 TASK-44's allow-list test

`tests/test_names.py::test_prose_says_deep_reasoning` sits at the root, since it spans five packages. It reads:
- the string literals of `dr_app/texts.py`, `acp/texts.py`, `library/texts.py` and `tools/texts.py`, by `tokenize`:
  `STRING` and `FSTRING_MIDDLE` tokens, docstrings excluded;
- the literals of `canvas-app/src/ui/texts.ts` and `canvas-app/src/page/texts.ts`;
- the manifest's `display_name`, `description` and tab titles;
- `agent.py`'s `agentInfo` title;
- `bootstrap.sh`'s `echo` lines;
- the README with its code spans and fenced blocks removed.

It fails on any `deep_reasoner` or `deep-reasoning` that `ALLOWED` does not cover. `ALLOWED` is a tuple of compiled
patterns, each commented with why it is allowed:
- `from deep_reasoner import`;
- `deep_reasoner {`, a version or commit follows;
- `deep_reasoner_beta`;
- `/api/agent-profiles/deep_reasoner`;
- `~/.deep-reasoning`;
- `github.com/…/deep-reasoning`;
- `deep-reasoning-<version>`;
- in the README only, sentences about Dean's package and this repository, matched as whole phrases.

The module list is a constant, so TASK-48's `dr_web.texts` and `web.mjs` join with one line each (§9). The built panel
is not read: the committed build equals a fresh build of the sources this test reads (`ci.yml`). This narrows the
spec's mock-up.

### 7.3 Cross-repo: the title test (`crossrepo` marker, `bridge-replay` job)

- `tests/crossrepo/agent_server.py`:
  - `agent_server(checkout, root, *, outbound_proxy: str | None = None)`. When `outbound_proxy` is set, `HTTPS_PROXY`,
    `HTTP_PROXY` and their lower-case forms are set to it, `NO_PROXY` and `no_proxy` to `127.0.0.1,localhost`, and every
    `*_API_KEY` is removed from the inherited environment;
  - new `recording_proxy() -> Iterator[RecordingProxy]`, where `RecordingProxy` is `url: str` plus `attempts: list[str]`.
    It is a loopback server that records each request line's target (`api.openai.com:443` for a `CONNECT`), answers
    403 and forwards nothing.
- `tests/crossrepo/test_title.py::test_a_title_profile_without_a_key_is_never_called_and_the_first_message_titles_the_chat`.
  Through `recording_proxy()` and `agent_server(…, outbound_proxy=proxy.url)`:
  1. `POST /api/agent-profiles/deep_reasoner`, ACP `custom`, the checkout's `tests/fixtures/acp/scripted_agent.py
     --no-commands`, `acp_subagents` true; then activate it.
  2. `POST /api/profiles/gpt-5-5 {"llm": {"model": "gpt-5.5"}}`, as Canvas saves it, with no key and no `base_url`;
     then activate it.
  3. `POST /api/conversations` as Canvas does: `agent_profile_id`, `autotitle: true`, `title_llm_profile: "gpt-5-5"`,
     and "What is 2 + 2?".
  4. By 30 s, the title is "What is 2 + 2?" and the events hold no `ConversationErrorEvent`. `proxy.attempts` is `[]`,
     before and after.

On `dr-2` it fails: no title for minutes, and `api.openai.com:443` attempted (F4, verified). This is
`repro46.py`'s shape, corrected by F4.

### 7.4 E12, in order (`tests/desktop/test_e12.py`, one launch, file order)

New `PLAN` entries:
- `TITLE_QUESTION` (at most 50 characters) → `FinalAnswer(TITLE_ANSWER)`;
- `CAP_QUESTION` → `FinalAnswer(CAP_ANSWER)`.

The no-key question needs none: `dr-acp` answers before any run. The module docstring follows the new order.

1. `test_the_first_launch_installs_everything_and_opens_on_the_home_screen`. Setup's lines are `home_local`,
   `installed in`, `PROFILE_CREATED` and `app_ready`. No line holds "runs as you" or `OPENAI_API_KEY`. The window shows
   `chat-input`; `first-run-onboarding-screen` and `onboarding-modal` have count 0. `deep_reasoner` is the active
   profile, as today.
2. `test_the_first_launch_asks_for_no_telemetry_consent`: it waits on `chat-input` (was
   `onboarding-step-choose-agent`); otherwise as today.
3. `test_no_screen_offers_another_agent_or_edits_an_agent_profile` (TASK-50, Q2):
   - the "+" menu (`chat-plus-button`) has no `switch-agent-profile-button`;
   - `/settings` lands on `/settings/app`, and the settings navigation's links are exactly `agent-context`,
     `verification`, `app` and `secrets`;
   - `/settings/agents`, `/settings/agent`, `/settings/llm`, `/settings/meta-llm` and `/settings/condenser` each end on
     `/settings/app`;
   - Application has no link to `/settings/llm`;
   - in the command menu (ControlOrMeta+K), no `command-menu-item-agent-settings`, `-llm-settings` or
     `-condenser-settings`, while `command-menu-item-secrets-settings` is visible;
   - the checklist lists `start-conversation` and not `configure-llm` or `customize-agent`;
   - an automation template's setup dialog has no `automation-agent-profile`.
4. `test_a_question_with_no_model_key_saved_says_where_the_key_goes` (Q1). From the home screen, before any key is
   saved, a question is answered with `acp.texts.missing_model_key(["OPENAI_API_KEY"])`. No run is created and the fake
   is not called.
5. `test_every_conversation_starts_from_deep_reasoner_whatever_profile_is_active` (TASK-50 launch):
   - `point_the_library_at` (moved here from the onboarding test);
   - `POST /api/agent-profiles/e12-other` (ACP `custom`, command `false`), activated;
   - `start_conversation(QUESTION)`; `ANSWER` is shown, and `launched_agent_profile.agent_profile_id` is
     `deep_reasoner`'s id.
   The "other" profile stays active for the rest of E12, so every later conversation runs through the lock.
6. `test_a_conversation_in_the_window_runs_dr_acp_and_its_key_stays_out`: unchanged. Step 4 made no run, so
   `worker_environ`'s single run holds.
7. `test_a_new_chats_first_message_shows_no_title_error_with_a_keyless_llm_profile` (TASK-46):
   - `POST /api/profiles/gpt-5-5 {"llm": {"model": "gpt-5.5"}}`, activated;
   - `start_conversation(TITLE_QUESTION)`; `TITLE_ANSWER` is shown;
   - the conversation's title is `TITLE_QUESTION`, and its events hold no `ConversationErrorEvent`.
   On the old pins it fails after one refused, unpaid call to `api.openai.com` (spec §4).
8. `test_nothing_records_telemetry_consent_and_settings_offer_no_analytics_switch`: unchanged.
9. `test_d3s_frame_works_through_the_bridge_in_electrons_chromium`: no `dr-notice` or acknowledgement. The frame opens
   on the namespaces tab directly, and it asserts `dr-notice` has count 0.
10. `test_sub_agents_nest_under_the_cells_that_spawned_them_as_the_run_log_records`: unchanged.
11. `test_each_sub_agent_shows_its_latest_cost_by_default_and_none_once_turned_off` (TASK-51). Each of the three rows
    shows `subagent_cost(cost)` without the setting touched. Then `/settings/app`: the switch is checked; clicking it
    unchecks it; back on the conversation, `subagent-cost` has count 0.
12. `test_stop_on_one_sub_agent_stops_it_and_its_branch`: unchanged.
13. `test_the_home_screen_offers_the_namespaces_and_each_ones_decompositions`: unchanged. It now runs through the
    lock's preview (step 5's active profile is not `deep_reasoner`).
14. `test_create_decomposition_in_the_header_panel_saves_into_the_conversations_namespace`: `panel_tab` loses its
    notice branch.
15. `test_the_next_conversation_in_the_namespace_offers_the_decomposition_and_uses_it`: unchanged.
16. `test_the_spend_cap_set_in_the_tools_tab_caps_the_next_conversation` (Q3; replaces
    `test_the_tools_tab_shows_the_safety_notice_with_d4s_risk_line_under_it`):
    - the Tools tab shows `dr-spend-cap-input` = `5`, and no `dr-notice` or `dr-tools-risk`;
    - fill `7.50` and save; `dr-spend-cap-status` is `SPEND_CAP_SAVED("7.50")`;
    - the profile's `acp_args` end `--spend-cap-usd 7.50`, with `--home` kept;
    - `start_conversation(CAP_QUESTION)`; `CAP_ANSWER` is shown; the new `spend/<session>.json` has `cap_usd` 7.5.
17. `test_an_mcp_server_granted_in_the_tools_tab_is_called_by_the_next_conversation`: unchanged.
18. `test_the_header_panel_keeps_working_past_its_first_backend_session`: unchanged.
19. `test_closing_the_window_quits_the_app_and_leaves_nothing_running`: unchanged.
20. `test_setup_relaunches_offline_from_its_cache_and_installs_nothing`: its last line checks that no line starts with
    `texts.installing`'s prefix (was the literal "installing deep-reasoning").

New helpers in `tests/desktop/app.py`, or beside TASK-48's moved ones (§9):
- `conversation_events(app, conversation_id) -> list[dict]`;
- `spend_caps(app) -> dict[str, float]`, each session's `cap_usd` from `spend/*.json`.

**The live tier** (on demand, cents, the Implementer runs it at Proof Green): `tests/desktop/test_live.py`, markers
`desktop` and `live`. It runs in `desktop-e2e` after E12 only when the `cross-repo.yml` dispatch input `live` is true.
`OPENAI_API_KEY` comes from Actions secrets, into that one step's environment, and the test saves it as a Canvas secret
over REST; it never reaches the app's environment. One test, on the starter Library (gpt-6-luna through the key
proxy), with the keyless `gpt-5-5` profile active, asking "Use one sub-agent to add 2 and 2, then answer with its
result." It asserts:
- an answer arrives;
- no `ConversationErrorEvent`;
- the title is the question cut to 50 characters;
- the sub-agent's row shows a cost without the setting touched.

### 7.5 `cross-repo.yml`

- `pull_request.paths` gains `tests/desktop/**` and `tests/crossrepo/**` (F6);
- `bridge-replay`'s `pytest -m crossrepo tests/app/test_canvas_app.py tests/crossrepo` picks up `test_title.py`
  unchanged;
- `workflow_dispatch` gains `inputs.live` (boolean, default false) and the gated step of §7.4.

`ci.yml`, `desktop-release.yml` and `fork-live.yml` are unchanged.

---

## 8 · Release chain: what Michael pushes, and when

1. **SDK fork:** the Implementer opens `fix/title-llm-without-credentials` into `deep-reasoning`, and it merges after
   its CI. **Michael pushes tag `dr-3`** at the merge commit. `dr-release.yml` creates prerelease `dr-3` with
   `openhands-typescript-client-<v>.tgz`, once.
2. **Canvas fork:** `feat/agent-lock`, `fix/subagent-costs-on-by-default` and `feat/app-title` (§13) merge into
   `deep-reasoning`, in any order (`feat/agent-lock` and `feat/app-title` both add a block to `defaults.json`: a
   textual merge), then `chore/wire-sdk-dr-3`, which needs step 1's release. **Michael pushes tag
   `dr-4`** at the wiring merge. A tag at any earlier commit fails check 2 (another SDK) or check 5b (no lock or no title).
3. **deep-reasoning `ux-round`:** everything of §4 and §7 except the pins can be built and unit-tested from the start.
   `test_build.py` uses fake readers, and E12 waits. Then one commit moves both pins to `dr-4` and `dr-3` (§4.1), with
   the pin-restating test. `cross-repo.yml` must be green on that commit (`pins`, `desktop-e2e` with E12,
   `bridge-replay` with the title test, `canvas-replay`) before the PR merges. The live tier is dispatched once on it.

Nothing waits on Michael but the two tags, and only steps 2 and 3 wait on them.

---

## 9 · TASK-48: seams and merge order

TASK-48's design (`docs/design/task-48-browser.md` on `design/task-48`, its §8) and this one agree that the two are
independent, that whichever lands second rebases, and that nothing of this round lives in `electron/main.mjs` or
`desktop/electron-builder.dr.mjs`. The localhost build inherits every item:
- the lock, through `patch_defaults`, which its `prepare()` calls;
- the costs default, the panel field, the icon and the texts, through the shared bundle and runtime;
- the title fix, through the SDK pin in the wiring commit.

| Merge point | This round | TASK-48 | Who adjusts |
|---|---|---|---|
| `desktop/build.py` | `LOCKED_PROFILE`, `FORK_NULL_KEYS`, `fork_lacks_setting`, two more keys and the `app_title` keyword in `patch_defaults`, checks 5 and 5b as one loop (v1.1) | moves `build()` into `prepare()`, `package_desktop` and `package_web` | the second rebases. `prepare()` passes `app_title=pins.app.product_name` (v1.1, one argument); TASK-48's `verify_web` compares with `patch_defaults`'s output, so it needs no other edit |
| `tests/desktop/test_build.py` | the tests of §7.1 | `build.py web` tests | a textual merge |
| `tests/desktop/test_e12.py`, `tests/desktop/app.py` | §7.4: new steps, onboarding and notice gone, `panel_tab` without the notice | moves `setup_lines`, `point_the_library_at`, `example`, `run_ids`, `worker_environ`, `start_conversation`, `answer` and the frame flow (`library_frame`) into `app.py` | if TASK-48 lands first, this round's helpers go beside its moved ones and `library_frame` loses the notice. If this lands first, TASK-48 moves the helpers as they now are |
| `dr_app/texts.py` | removes `safety` and `NO_MODEL_KEY`; rewords six (§6.1) | rewords four "the app" sentences (its §5.3) | disjoint sentences: a textual merge |
| `tests/test_names.py` | the allow-list test (§7.2) | `dr_web/texts.py`, `desktop/web.mjs` | whichever lands second adds TASK-48's two sources to the test's module list |
| README | rewrites The first launch (heading kept) and the cap's paragraph | adds Run it in your browser, linking to The first launch | the heading is kept, so its link test holds |
| `cross-repo.yml` | two paths, the `live` input | `web-e2e`, and `desktop-e2e` building `linux web` | a textual merge. The pin bump's PR runs both E12 and E13 |
| The Canvas pin `dr-4` | this round's tag | needs none. Its W13 contract checks re-run on `dr-4`, and this round touches no launcher or Electron file | — |

**Two points for the Conductor:**
- *(v1.1: settled)* The browser tab's title is now this round's (§13). The launcher banner and the favicon stay
  upstream's; §13 says why.
- TASK-48's Q3 (a), the `Host` allowlist, is its own task "sharing a tag with the UX round if it needs one". If its
  fork PR is merged before step 2 of §8, `dr-4` carries it too.

---

## 10 · What this round makes stale

- **D5 design v3 §2.3**, "Where the user is told", and §2's "the app says the same to the user". The app now says
  nothing. The README's section is reference (Q4 (a)), and its quote goes.
- **D5 §6's tables**:
  - the `safety` row and `NO_MODEL_KEY` go;
  - D3's `SAFETY`, `SAFETY_NO_CAP` and `UNDERSTAND`, and D4's `TOOLS_RISK`, go;
  - `NO_GIT`, `PROFILE_CREATED`, `PROFILE_UPDATED`, `installing`, `install_failed`, `home_too_long`, `cap_reached` and
    `ROOT_STOPPED` change (§6).
- **D5 §4.5 step 2** (the model-key hint) goes; after-ready is the profile and the App.
- **D5 decision F**:
  - "A user who switches the default agent, or raises the cap in Canvas's profile editor, is not overruled" now reads:
    no screen switches the agent, and the cap's editor is the Library panel's field, which owns the
    `--spend-cap-usd` pair after creation;
  - the v3 note "Canvas `dr-3`'s onboarding keeps the active profile (#29) … and E12 pins that" is replaced by the
    lock. The active pointer no longer decides which agent runs, and E12 pins the lock instead (§7.4 step 5);
  - the code is unchanged (F3).
- **D5 §1.2's "The safety notice" row; §4.2.3** ("only D5's four keys", now five); **§4.2.2 check 5** (+
  `agent.lockedProfile`, + 5b).
- **§7.5's E12 list and the "Which tests carry which property" rows** naming `test_notice.py`,
  `test_the_tools_tab_shows_the_safety_notice_with_d4s_risk_line_under_it`,
  `test_onboarding_keeps_deep_reasoner_and_starts_the_first_conversation_with_it`,
  `test_each_sub_agent_shows_its_latest_cost_once_the_setting_is_on`,
  `test_the_safety_section_quotes_setup_with_the_cap_setup_sets` and
  `test_the_key_is_the_one_setup_asks_for_where_setup_says`.
- **C1's SUB-006** and C1's design "off by default"; D3's notice and its acknowledgement key; D4 §9.3's `TOOLS_RISK`.
- **The README's first-launch steps** (Choose your agent, Say hello, Close; "every launch's setup says so") and the
  safety section's quote and cap how-to.
- **The spec's TASK-46 "after" cell** for the reproduction's own shape (F4), and its §4 row "the stub sees nothing",
  which holds only without a `base_url`.
- *(found, not this round's)* The README links `docs/design/d5-desktop-app.md`, which is not on `main`. Design documents
  never are, so the link is dead there today.

---

## 11 · Size

Lines touched, added plus removed, tests included. Built assets, lockfiles and the wiring commit are not counted.

| Where | Code | Tests | Read at Gate C |
|---|---|---|---|
| SDK `fix/title-llm-without-credentials` | ≈ 15 | ≈ 100 | ≈ 0.4 h |
| Canvas `feat/agent-lock` (the module, 9 gates, launch, automations, spec, i18n) | ≈ 230 | ≈ 330 | ≈ 1.8 h |
| Canvas `fix/subagent-costs-on-by-default` | ≈ 15 | ≈ 40 | ≈ 0.2 h |
| deep-reasoning: build and pins | ≈ 25 | ≈ 40 | ≈ 0.2 h |
| deep-reasoning: dr-app texts and cli (mostly removed) | ≈ 60 | ≈ 50 | ≈ 0.3 h |
| deep-reasoning: dr-acp reminder, refusal, names | ≈ 50 | ≈ 90 | ≈ 0.4 h |
| deep-reasoning: the panel (warnings out, the field, protocol, icon) | ≈ 260 | ≈ 230 | ≈ 1.4 h |
| deep-reasoning: Library and tools texts, allow-list test, README | ≈ 60 | ≈ 110 | ≈ 0.5 h |
| deep-reasoning: E12, cross-repo title test, live test, workflow | ≈ 5 | ≈ 330 | ≈ 0.9 h |
| the tab title (§13): Canvas `feat/app-title`, `build.py`, E12 | ≈ 45 | ≈ 85 | ≈ 0.4 h |
| **Total** | **≈ 0.75k** | **≈ 1.4k** | **≈ 2.1k lines, about 6.5 h** |

That is about 0.1k more than the amended spec's 1.9k. The ninth gate, the automations' submit path, check 5b, the title
test's recording proxy and the live test account for it. About 0.5k of it is removals, which read faster, so 6 h is
an upper estimate.

---

## 12 · Open items, and what I was unsure about

1. **The fork's mock-LLM Playwright spec for the lock** is replaced by E12 (F5). If the Conductor wants it in the fork
   anyway, the cheapest form is a second Playwright project in `playwright.mock-llm.config.ts`. It would build into
   `build-locked/` with `defaults.json` patched, run by hand like the rest of mock-LLM, at ≈ 0.15k.
2. **"No cap"** (D8). If Michael wants a real "no limit", the honest form is a `dr-acp` value (`--spend-cap-usd none`)
   with the proxy still on, about 40 lines plus tests, and a third state in the field. Not designed here.
3. **The reminder's wording.** Michael asked for "a non intrusive reminder" and did not want "No model key is saved
   yet". The chat sentence (§6.2) names the product, the variable, the place and the next step, and appears only as the
   answer to a question asked without the key. If he wants it softer, only §6.2 changes.
4. **Existing automations** that name another agent profile keep it until next saved from the app (§2.1). Michael's VM
   install is the only one known, and nothing says it has automations.
5. **The live tier's sub-agent cost** depends on gpt-6-luna using a sub-agent when asked to. If it does not, the test
   fails on its cost assertion while the round's other properties hold. The Implementer may drop that assertion and
   name it.
6. **A keyless profile with a custom `base_url`** still calls its endpoint and publishes its refusal (F4). This is
   upstream's own definition of a configured LLM, kept as approved.
7. **`llm_has_real_config`'s rename** touches one existing upstream test's reference. The alternative is importing the
   private name across modules. I chose the rename as the smaller surprise for an upstream reviewer.
8. **The checklist** now shows from the first launch in a locked build (D3), as it does today once onboarding closes.
   Its remaining items include OpenHands' Slack and docs links, which the spec's out-of-scope list ("OpenHands in the
   rest of Canvas") leaves.

---

## 13 · Addendum, 2026-10-19 (v1.1): the browser tab title says "Deep Reasoning"

Michael added it to the round with "go with your recommendations". It is a Canvas fork setting, null upstream
(meaning "OpenHands"), that our builds set to "Deep Reasoning", shipping in `dr-4`.

**Where titles are made (read, Canvas `dr-3`):**
- `src/hooks/use-app-title.ts:6` `APP_TITLE = "OpenHands"`. `useAppTitle` composes "<app>", "<conversation> | <app>"
  and "<emoji> <conversation> | <app>" (`:17–31`), rendered as `<title>` by `routes/root-layout.tsx:129`;
- `src/root.tsx:228–231` `meta()`'s `{ title: "OpenHands" }`, which is what `routes/shared-conversation.tsx` shows,
  since it sits outside the layout.

No route has a `meta` of its own, and there is no `index.html` title. The transcript export's `<title>`
(`utils/transcript-export/index.ts:29`) is the conversation's own title, so it is out.

`electron/main.mjs` has no `page-title-updated` handler, so the desktop window's title follows `document.title` too.
It says "OpenHands" today, despite `product_name` (read, not seen on a desktop).

### 13.1 Canvas fork: `feat/app-title` (one PR, upstream-shaped)

`config/defaults.json`, a new top-level block:

```json
"branding": {
  "_comment": "Optional name the frontend shows as its title: the browser tab (or the desktop window), alone or after a conversation's title. A build that ships under its own name sets it. null means \"OpenHands\". Compiled into the frontend bundle, so never a secret.",
  "appTitle": null
}
```

```ts
// src/utils/app-branding.ts (new)
// @spec BRD-001
export const DEFAULT_APP_TITLE = "OpenHands";

/** defaults.json's branding.appTitle, read when called and trimmed; DEFAULT_APP_TITLE when unset, empty
 * or not a string. */
export function getAppTitle(): string;
```

- `use-app-title.ts`: `APP_TITLE` goes, and the hook reads `getAppTitle()` once per render.
- `root.tsx` `meta`: `{ title: getAppTitle() }`.
- Not translated: it is a product name, as the literal was.
- `specs/app-branding.md` (new), **BRD-001: The app's title.** "Every title the frontend sets (the document title
  alone, after a conversation's title, and after its status emoji) shall name `branding.appTitle`, or OpenHands when it
  is null."
- vitest sets the key on the imported `defaults.json` object and restores null, as `feat/agent-lock` does, through
  `__tests__/helpers/app-branding.ts` `setAppTitle(name)`:
  - `src/utils/app-branding.test.ts` (new): `is OpenHands when branding.appTitle is null, empty or not a string`; `is
    the configured name, trimmed`;
  - `src/hooks/use-app-title.test.tsx`: the existing cases stay as they are, which shows null keeps every current
    title. New `it.each` `names the configured app in every title it makes`, over outside a conversation ("Deep
    Reasoning"), a conversation ("My Conversation | Deep Reasoning"), a conversation still loading ("Deep Reasoning")
    and a known status (`${emoji} My Conversation | Deep Reasoning`);
  - `src/root.test.tsx`: `meta's title is OpenHands unset and the configured name when set`.
  - `__tests__/routes/root-layout.test.tsx` mocks `useAppTitle`, so it is unchanged.

### 13.2 deep-reasoning

- `desktop/build.py`:
  - `patch_defaults(defaults, *, state_dir, command, app_title)` writes `branding.appTitle = app_title`. The callers
    pass `pins.app.product_name` ("Deep Reasoning", `desktop/pins.toml`), so the window's product name and its title
    have one source;
  - checks 5 and 5b become one loop over `FORK_NULL_KEYS`, with `fork_lacks_setting` (§4.1, §5.3, §6.4 as revised).
- `tests/desktop/test_build.py`:
  - new `test_the_title_the_build_writes_is_the_product_name`;
  - the tests revised in §7.1 gain `branding.appTitle`.
- **E12**, a step inserted after §7.4 step 5 (that conversation is then open):
  `test_the_window_title_names_deep_reasoning_at_home_and_after_a_conversations_title`. It asserts
  `expect(page).to_have_title(re.compile(rf"{re.escape(QUESTION)} \| Deep Reasoning$"))`, then `page.goto(CANVAS_URL)`
  and `expect(page).to_have_title("Deep Reasoning")`. The name is `build.load_pins(build.PINS).app.product_name`, not a
  literal.
- The release chain (§8 step 2) adds `feat/app-title` before the wiring commit. A `dr-4` without the key fails check 5b.

### 13.3 Seams

- **TASK-48 (E13):** `package_web` ships `prepare()`'s `defaults.json`, which is `patch_defaults`' output, and
  `build:app` compiles it after the patch. So the browser tab says "Deep Reasoning" with no edit of its own. The one
  merge point is `prepare()` passing `app_title=pins.app.product_name`. E13 can assert
  `expect(page).to_have_title(product_name)` on `http://localhost:8000`. That closes the "OpenHands" tab title its spec
  left to TASK-44 (§9).
- **TASK-66** (`design/task-66`, not pushed yet when this was written) adds a third `defaults.json` setting that
  `patch_defaults` writes: a dependency cutoff date for the launcher's `uvx` starts. Both tasks change
  `patch_defaults`'s keywords and its callers. Whichever lands second adds its keyword at `build()` (or TASK-48's
  `prepare()`), and adds its key to the constants the tests read:
  - `FORK_NULL_KEYS`, if the fork declares the key null;
  - `test_defaults_gain_only_the_keys_the_build_writes`, which compares with constants, not a count.
  If TASK-66's key also needs a fork that knows it, it is one more entry in `FORK_NULL_KEYS`, and check 5b covers it.

### 13.4 In or out (recommended; not widened)

- **The favicon: out.** It needs an icon we don't have (D5 kept upstream's, §11 item 6). A later `branding.favicon`
  fits the same block.
- **The launcher banners: out.**
  - "Agent Canvas + Automation Stack" (`scripts/dev-with-automation.mjs:1710`) is terminal output, which TASK-48's
    entry follows with its own "Deep Reasoning is running at …" line.
  - "OpenHands Agent Canvas" (`electron/main.mjs:664`, the splash) is Electron-only, which TASK-48 must not depend on.
  - Neither is the tab.
- **The `description` meta, "Let's Start Building!": out.** No one sees it.

Size: Canvas ≈ 25 lines of code and ≈ 60 of tests; deep-reasoning ≈ 20 and ≈ 25. About 0.13k in all, ≈ 0.4 h at
Gate C (§11 as revised).

**Unsure:**
- That the desktop window takes the title rests on reading `electron/main.mjs`, not on a window. E12 asserts
  `document.title`, which Electron mirrors.
- `patch_defaults` gaining a required keyword is a merge point with both TASK-48 and TASK-66. A default value would
  avoid it, but would let a caller forget the title.
