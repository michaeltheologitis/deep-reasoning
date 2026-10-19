# TASK-65 · As built: the UX round

**TASK-65** (closes TASK-42, 43, 44, 46, 50, 51, plus the spend cap field, the no-key reminder and the tab title) ·
Cartographer · 2026-10-19 · branch `as-built/task-65`, cut from `ux-round` `b283be2`. The build is in three repos:

- deep-reasoning `ux-round` `b283be2` (22 commits on `main` `9e8109e`; +3489/−503 in all, of which the design doc,
  TASK-64's `3531384` and TASK-66's `c361467`/`b0fff97` are not this round's);
- the Canvas fork: `feat/agent-lock` `ee7a150`, `fix/subagent-costs-on-by-default` `6df1472` and `feat/app-title`
  `2247009`, each cut from `dr-3` = `4355a36`;
- the SDK fork: `fix/title-llm-without-credentials` `1f1a381`, on `dr-2` = `34c540c`.

It is checked against one document, the design `docs/design/task-65-ux-round.md` **v1.1**, on `design/ux-round` at
`6880dcf`. It is not checked against the spec.

**Evidence.** Each claim carries a mark:
- **[run]**: I ran it in this sandbox, at `b283be2` or at the fork commits, with no model call;
- **[CI]**: a named CI run shows it, and I read its log;
- **[impl]**: an Implementer reports it in a commit message or the task row, and I did not repeat it;
- **[read]**: I read it in the code and did not run it.

E12's step numbers are design §7.4's; CI runs 25 steps, listed in §3.1.

**Reading guide.** §0 is the five-minute read. §1 is the map, §2 every divergence from the design, §3 the proof and
the paid runs, §4 the seams and the release chain, §5 what nobody ran. About twenty minutes in all.

---

## 0 · What Michael gets, and what changed against what he approved

**What he approved** (2026-10-19, times UTC, as the changelog records them).
- **Gate A, 02:05**: the spec, with:
  - Q1 (a), with the startup line about the key removed;
  - Q2 (a);
  - Q3 (b), a Spend cap field in the Library panel;
  - Q4 (a).
- **05:18**: the browser tab title "Deep Reasoning", a Canvas setting that is null upstream (design §13).
- **06:34**: a standing green light to merge the round once it is built, CI is green, this document is written and
  the PRs are cut. The fork tags stay his.

**What he gets**, once the tags and the pin bump land (§4.2):

| Item | In the app | Evidence |
|---|---|---|
| **One agent** (TASK-50, Q2) | Every conversation and automation starts from the agent profile named `deep_reasoner`, whatever profile is active. There is no onboarding and no "Switch agent profile". Settings lists exactly Agent Context, Verification, Application and Secrets. The Agent, Agents, LLM, Model Router and Condenser pages redirect to Application. These are gone: the command menu's Agent, LLM and Condenser entries; the checklist's Configure LLM and Customize agent items; Application's "Manage LLM profiles" link; the automation profile selector; and an ACP sign-in error's link to agent settings. A backend without the profile refuses the start: "This app runs only the agent profile 'deep_reasoner', which this backend does not have. Restart the app." | E12 steps 3 and 5 [CI]; the refusal [read] |
| **No title error** (TASK-46) | An LLM profile with no key, no subscription and no custom endpoint is never called for a title. The chat is titled by its first message: kept whole up to 50 characters, otherwise its first 47 and "...". No error event is added. | the cross-repo title test, E12 step 7 and the live tier [CI] |
| **No safety warnings** (TASK-42) | Setup prints no safety line and no line about the model key. The panel has no first-open notice and no banners on Tools. | E12 steps 1, 9 and 16 [CI]; unit tests [run] |
| **"Deep Reasoning" in prose** (TASK-44) | It names the product in setup's, `dr-acp`'s, the panel's, the Library's and Check's sentences, in `agentInfo.title`, the manifest, `bootstrap.sh`'s echo and the README. Code, paths and Dean's package keep their names. | `tests/test_names.py` [run] |
| **Sub-agent costs on** (TASK-51) | An unsaved "Show sub-agent costs" reads as on. A saved off stays off, and a saved on stays on. | E12 step 11 and the live tier [CI] |
| **Purple icon** (TASK-43) | The panel icon's stroke is `#A78BFA`: 7.1:1 on the header's `#0B0E14` and 5.63:1 on `#21252F` (black was 1.09:1). | contrast [run] |
| **Spend cap field** (Q3) | It is the first section of the Tools tab. It takes a dollar amount above 0, of up to 6 digits and 2 decimals, and writes the profile's `--spend-cap-usd`, keeping every other argument in place; new conversations use it. With `--no-key-proxy` it shows a read-only "No cap" sentence, and on the standalone page the cap is read-only. | E12 step 16 [CI]; vitest [run] |
| **No-key reminder** (Q1) | A question asked with no key saved is answered with "Deep Reasoning needs OPENAI_API_KEY to answer: add it under Settings → Secrets, then start a new conversation." No run is made, and the model is not called. | E12 step 4 [CI]; `tests/acp` [run] |
| **Tab title** (§13) | "Deep Reasoning", "‹conversation› \| Deep Reasoning", and the status emoji before it. | E12's title step [CI] |

Some things stay as they are [read]:
- Application keeps Canvas's "Conversation titles" selector. It lists the LLM profiles that exist, though no page
  creates one now.
- The getting-started checklist now shows from the first launch, with Canvas's other items (Slack, docs).

**What changed against what he approved.**

*In the design, before any code.* Its §0 names these as its changes to the spec:
- the Canvas fork has no Playwright spec for the lock, so the locked bundle's end-to-end proof is E12 (F5);
- a ninth gate, Application's "Manage LLM profiles" link (F5);
- a keyless profile with a custom base URL still counts as configured, so it is still called for a title and its
  refusal still shows (F4);
- there is no "no cap" value, and a large amount is how to lift the cap (D8);
- the button is named "Show Decompositions" (F7).

*In the build, against the design* (each one in §2):
- a build override for untagged fork commits;
- `dr-acp` deletes the run directory it had just created;
- the live tier asserts other things than §7.4 says;
- E12's title step runs later than §13.2 places it, and E12 opens the command menu by clicking it, not by shortcut;
- three files sit elsewhere than the design names;
- the round is about 4.1k lines touched, against the design's 2.1k.

**What is not yet true.**
- **The proof ran on no tag.** It ran on `ux-round` `b283be2`, built through the override with:
  - Canvas `ux-round-integration` `1a9e3c6`, a scratch merge for CI of this round's three branches with TASK-64's,
    TASK-66's and TASK-41's;
  - SDK `1f1a381`, an unmerged branch.
- **At the committed pins (Canvas `dr-3`, SDK `dr-2`), `build.py check` refuses to build.** Check 5b finds no
  `agent.lockedProfile` and no `branding.appTitle` in `dr-3`'s `defaults.json`, and check 5c (TASK-66's) no
  `uv.excludeNewer` [run]. So `cross-repo.yml` is red on a pull request until the pin bump, as design §8 intends.
- **No run included:**
  - SDK `dr-3`'s second change (TASK-69's fix);
  - Canvas `dr-4`'s wiring commit (SDK `dr-3` and its TypeScript client).
  Design §8 asks for `cross-repo.yml` green on the pin-bump commit, with one live dispatch there, before the PR merges.

---

## 1 · The map

Each fork gains a setting that does nothing upstream. Our build sets it, and every deep_reasoner-specific value stays
in deep-reasoning.

```text
deep-reasoning  desktop/build.py patch_defaults ──▶ the Canvas checkout's config/defaults.json, compiled into the bundle
                  agent.lockedProfile = LOCKED_PROFILE ("deep_reasoner")     ──▶ Canvas src/utils/agent-profile-lock.ts
                  branding.appTitle  = pins.app.product_name ("Deep Reasoning") ──▶ Canvas src/utils/app-branding.ts
                check_pins: the fork must declare every FORK_NULL_KEYS key, as null      (checks 5, 5b and TASK-66's 5c)

Canvas  ── POST /api/conversations {agent_profile_id: the locked id, title_llm_profile: the active LLM profile} ──▶
SDK agent-server   AutoTitleSubscriber._load_title_llm: None unless llm_has_real_config(llm) → agent.llm → truncation
        ── ACP, Canvas's secrets in the environment at launch ──▶
dr-acp  Session._start_run: missing_model_keys([client, *tool clients], os.environ) → reply, no run

panel frame ── postMessage dr-library/set-spend-cap ──▶ Canvas page (canvas-app/src/page/mount.ts)
            ◀── spend-cap-saved | spend-cap-refused ──   └ writeSpendCap: GET, then POST /api/agent-profiles/deep_reasoner
                                                           through C2's host.agentServer.request (Canvas's session key)
```

Most of the code sits in two places. The lock is spread over about a dozen Canvas call sites (§1.1), and the spend cap
is written in three hops (§1.4).

### 1.1 The lock: Canvas `feat/agent-lock` (5 commits, +1206/−43, of which 904 lines are tests)

One module, `src/utils/agent-profile-lock.ts`, reads `defaults.json` when called, never at import, so vitest can flip
it through `__tests__/helpers/agent-lock.ts` [read]. Its surface is the claim:

```ts
export const AGENT_LOCK_HIDDEN_SETTINGS_PATHS: ReadonlySet<string>; // agents, agent, llm, meta-llm, condenser
export function getLockedAgentProfileName(): string | null;         // trimmed; null if unset, empty or not a string
export function isAgentProfileLocked(): boolean;
export function isAgentLockHiddenPath(path: string): boolean;       // the path or below it, and only when locked
export function selectLaunchAgentProfileId(list): string | null;    // locked: that name's id or null; else the active id
export class LockedAgentProfileMissingError extends Error { readonly profileName: string }
// components/features/automations/agent-profile-selector.tsx
export function useLockedAutomationProfileId(): string | null | undefined; // undefined unlocked; null loading or missing
```

There are two kinds of gate [read]:
- **"Is it locked"** gates onboarding (`useOnboardingCompletion` reads as completed), the "+" menu's switch, the ACP
  sign-in error's link and the automation selector.
- **"Is this path hidden"** gates everything that leads to a page:
  - the settings nav and the loader's redirect, through the fork's own `isSettingsPageHidden`;
  - the landing page, through `getFirstAvailablePath`, which also skips `/settings` when locked;
  - command-menu items, by their `to`;
  - checklist items, by their href, with counts and "all complete" taken over the items listed;
  - Application's link.

**One selector, five readers.** `selectLaunchAgentProfileId` replaces `active_agent_profile_id` in
`useCreateConversation`, `useActiveAgentProfile`, `useChatInputProfileState`, `useSwitchAcpModel` and
`resolveAcpLaunchProfile`. The last now returns `null` when locked and the profile is missing. The one direct read
left is the Agents page's manager (`agent-profiles-manager.tsx:33`), on a hidden page [read].

**The launch** [read]:
- When locked, the launch always uses the locked id. It never takes `agent_settings`, since two `!isLocked` guards
  skip both fallbacks.
- A missing profile throws `LockedAgentProfileMissingError` before anything is created, and the global mutation toast
  shows it.

**Automations** [read]:
- The edit modal and the setup dialog submit the locked id and hide the model picker. The dialog keeps the draft
  separate from what it submits, and its preflight reads what it submits.
- A missing profile is refused: in the modal by a toast, in the dialog as a form error.
- `useLockedAutomationProfileId` is `null` both while the list loads and when the profile is missing. So a save made
  before the list has loaded is refused with the missing-profile sentence.

**The rest.**
- One i18n key, `AGENT_LOCK$PROFILE_MISSING`, in 15 locales.
- `specs/agent-profile-lock.md`, APL-001 to APL-006.
- `data-testid="command-menu-item-<id>"` on every command-menu entry.
- `minimumAgentServer` is unchanged.

### 1.2 Costs and the title: Canvas `fix/subagent-costs-on-by-default` (+39/−40) and `feat/app-title` (+138/−6)

- **Costs.** `readShowSubagentCosts` is `localStorage … !== "false"`, and the server snapshot is `true`.
  `writeShowSubagentCosts` is unchanged. SUB-006 and every `@spec SUB-006` line now read "unless the setting is off"
  [read].
- **The title.** `src/utils/app-branding.ts` `getAppTitle(): string` gives `branding.appTitle` trimmed, or
  `DEFAULT_APP_TITLE` ("OpenHands"). `useAppTitle` and `root.tsx`'s `meta` read it, so it also reaches the shared
  conversation page. It is not translated [read].

### 1.3 The title guard: SDK `fix/title-llm-without-credentials` (2 commits, +148/−15, of which 130 lines are tests)

- `_llm_has_real_config` becomes `llm_has_real_config` (`agent_profiles_router.py`), with its body unchanged.
- `AutoTitleSubscriber._load_title_llm` (`conversation_service.py`) returns `None` when the LLM loaded from the
  profile fails it, and logs an info line.
- The store's `load(..., resolve_provider=True)` default applies a provider connection's key before the test, so that
  key counts [read].
- For a profile-launched ACP agent the fallback `agent.llm` is the `acp-managed` sentinel, which
  `generate_title_from_message` skips. The title is then the first message, truncated [read].
- A profile with a key is still called, and its failure is still published (#16686) [read].

### 1.4 deep-reasoning `ux-round`

**`desktop/build.py`.** It mirrors `dr_app.profile.PROFILE_NAME` as `LOCKED_PROFILE`, because the file imports nothing
of ours; `test_the_locked_profile_is_the_one_setup_creates` pins the two equal. The signature is a merge point with
TASK-48 and TASK-66:

```python
FORK_NULL_KEYS = ("paths.stateDir", "setup.command", "agent.lockedProfile", "branding.appTitle", "uv.excludeNewer")
def patch_defaults(defaults, *, state_dir: str, command: list[str], app_title: str, exclude_newer: str) -> dict
def with_commits(pins: Pins, *, canvas: str | None = None, sdk: str | None = None) -> Pins   # the override
```

- Checks 5, 5b and 5c are one loop over `FORK_NULL_KEYS`:
  - a key the fork lacks gives `fork_lacks_setting`: "✗ Canvas fork {tag}'s config/defaults.json has no {key}, so this
    build cannot set it: pin dr-4 or later.";
  - a key the fork sets gives `fork_sets_ours`.
- **The override.** `--canvas-commit` and `--sdk-commit` replace pins in memory and name them in `Pins.replaced`:
  - checks 1 (the tag) and 8 (the fork branch) skip a replaced pin, and every other check runs;
  - a replaced SDK pin keeps its tag, which check 3's TypeScript client comes from, and `checkout_canvas` writes its
    commit into the checkout's `sources.agentServerGitRef`;
  - the run prints "⚠ This run builds the Canvas fork at … and the SDK fork at … in place of desktop/pins.toml's, without
    their tag and branch checks: never a release." [run, CI].

**Setup (`packages/dr-app`).**
- `install()` has no `first` and prints no safety line.
- `after_ready` no longer reads `/api/settings/secrets`.
- `texts.safety` and `NO_MODEL_KEY` are gone, and six sentences and `APP_DISABLED` name the product.
- `profile.py` changes only a docstring. Setup still keeps any `--spend-cap-usd` a user set (F3) [read; `tests/app`
  run].

**`dr-acp`.** `route.missing_model_keys(clients, env) -> list[str]` mirrors deep_reasoner's `build_client`:
- a client fails when neither its `api_key_env` (default `NOVITA_API_KEY`) nor `OPENAI_API_KEY` holds a value, and its
  `base_url` does not start with `http://localhost` or `http://127.0.0.1`;
- `test_missing_model_keys_says_what_build_client_refuses` pins the mirror against the real `build_client` [run].

`Session._start_run` calls it after `_materialize`, on the root client and every tool client, with `dr-acp`'s own
`os.environ`. When keys are missing it:
- removes `runs/<id>/`;
- replies `texts.missing_model_key(names)`, with stop reason `end_turn`;
- starts no worker.

The session stays un-run, so the same question asked again gets the same reply [run]. `cap_reached` names the field,
`ROOT_STOPPED` drops "(ask A3)", and `agentInfo.title` is "Deep Reasoning". The golden recordings change only in
`initialize`'s title [read].

**The panel (`canvas-app/`, rebuilt into `src/deep_reasoning/canvas_app/`).**
- `shared/protocol.ts`:
  - `FrameMessage` gains `{type: "dr-library/set-spend-cap", cap}`;
  - `PageMessage` is new: `spend-cap-saved {cap}` | `spend-cap-refused {message}`;
  - `isSpendCapInput` is `^\d{1,6}(\.\d{1,2})?$` and above 0;
  - `isFrameMessage` and `isPageMessage` accept exactly those keys.
- `page/context.ts`:
  - `withSpendCap(args, cap)` replaces the pair or the `=` form in place, appends otherwise, and returns `null` with
    `--no-key-proxy`;
  - `writeSpendCap(request, cap)` GETs the profile and POSTs it back whole with the new `acp_args`. It never throws: a
    404 is `CAP_PROFILE_MISSING`, `null` args are `CAP_NO_PROXY`, and any other failure is `CAP_NOT_SAVED(detail)`.
- **Who checks what.** The page answers `set-spend-cap` only from its own frame. The frame accepts an answer only from
  `window.parent` and `params.parent`'s origin.
- **Removed:** `SafetyNotice`, the acknowledgement gate, `SAFETY_ACK_KEY` (a stored `1` stays behind, unread), and the
  Tools tab's two banners.
- **Icon:** `panel.svg`'s stroke.
- **Rebuilt:** `dist/index.js` and `ui/assets/*`, which `ci.yml` pins to a fresh build [CI].

**Tests that state the round's properties.**
- `tests/test_names.py`: the allow-list for TASK-44.
- `tests/desktop/test_readme.py`: the README's key and cap sentences are the ones the code says.
- `tests/crossrepo/test_title.py`: through a loopback `recording_proxy()` that answers 403.
- E12: 21 of its 25 steps are this round's.
- `tests/desktop/test_live.py`.

---

## 2 · Divergences from the design (v1.1, `6880dcf`)

**Reported before this document**, each confirmed against the code:

1. **The build override** (design §4.1 and §8 offer no way to build an untagged fork commit).
   - Built: `--canvas-commit` and `--sdk-commit` in `build.py`; `cross-repo.yml` dispatch inputs `canvas_commit` and
     `sdk_commit`, which every job honours; and `DR_SDK_COMMIT` for the cross-repo tests.
   - Why: otherwise E12 and the live tier could run in CI only after both tags.
   - A release never passes them: `desktop-release.yml` names neither option, which
     `test_a_release_never_builds_from_replaced_pins` pins [run]. The inputs are validated as 40 hex before use [read].
   - Commits `148e500` and `0955bc2`.
2. **The hidden-path set lives in `agent-profile-lock.ts`** (design §2.1: `src/constants/settings-nav.tsx`), and
   `settings-nav.tsx` is untouched. No reason is recorded in the commit.
3. **`feat/app-title`'s tests are in `__tests__/utils/app-branding.test.ts` and `__tests__/root.test.tsx`** (design
   §13.1: `src/utils/…` and `src/root.test.tsx`). At `dr-3`, `__tests__/utils/` holds 86 of the fork's 91 util tests,
   and both root test files exist [read].
4. **The SDK tests patch `LLM.generate`** (design §3: `LLM.completion`). `generate` routes the GPT-5 and GPT-6 families
   to `responses()` (`llm.py:1685`, `RESPONSES_API_MODELS`), so a `completion` patch would never see the titler's call
   [read].
5. **E12's title step runs after step 6** (§13.2: after step 5). The step goes home, and step 6 reads step 5's answer in
   the window; run 39218978270 failed that way. Commit `b283be2`.
6. **Check 5c uses `fork_lacks_setting`.** This is TASK-66's divergence from its own design, which named
   `fork_lacks_cutoff`; it is listed here because it rides this round's loop. Commit `c361467`.
7. **Not a divergence from this design: no Playwright spec for the lock.** The design itself chose E12 (F5), and the
   fork adds no `tests/e2e` file.

**Not in the reported list.** Each is in its commit message:

8. **`dr-acp` creates the run directory, then deletes it.** The design puts the check after `_materialize` and says
   nothing reaches `runs/`. `_materialize` writes the run's config into `runs/<id>/` first, so
   `shutil.rmtree(run_dir, ignore_errors=True)` precedes the reply. Commit `3238cdf`.
9. **`APP_DISABLED` is reworded to "Show Decompositions"**, though it is outside §6.1's table. Commit `476e0fb`.
10. **The live tier asserts other things than §7.4 says.**
    - The title is `QUESTION[:47] + "..."`, the SDK's `generate_fallback_title` rule for 62 characters, not "cut to 50".
    - The answer is judged by `dr-acp`'s run log: the first prompt ends `answered`, within 600 s. The test no longer
      waits for "4" in the window.
    - A cost is asserted for each sub-agent the run log records, so with none the check passes vacuously, as §12 item 5
      allowed.
    - Before asking, it checks that the cost setting is unsaved.
    - Commits `2ba0bc8`, `7995d53` and `6d31d2c`.
11. **E12's `user_environment()` drops `XDG_CONFIG_HOME`, `XDG_CACHE_HOME`, `XDG_DATA_HOME` and `XDG_STATE_HOME`**, so
    every launch's per-user directories are under its own HOME; a test pins it. This was the third live run's root
    cause. Commit `6d31d2c`.
12. **E12 step 3 opens the command menu by clicking `command-menu-trigger`** (§7.4: ControlOrMeta+K). In Electron, the
    shortcut sent over CDP never reached Canvas's window listener. Commit `5b23129`.
13. **The cross-repo harness sets `LITELLM_LOCAL_MODEL_COST_MAP=True`**, so LiteLLM's start-up price fetch is not
    recorded as an outbound attempt. §7.3 lists only the proxy variables. Commit `7ddbaee`.
14. **`test_names.py` reads Python literals with `ast`**, docstrings by position (§7.2: `tokenize`) [read].
15. **The design file on `ux-round`, and so on this branch, is v1.0** (`008a358`). v1.1, with §13, exists only on
    `design/ux-round` [run: `git diff`].
16. **The size.** About 4.1k lines are touched, against §11's ≈ 2.1k:
    - code ≈ 1.0k (design ≈ 0.8k);
    - tests ≈ 2.9k (design ≈ 1.5k), mostly Canvas `feat/agent-lock`'s 0.9k (design ≈ 0.33k) and deep-reasoning's 1.7k
      (design ≈ 0.9k), which includes the override's seven tests and the live tier's fixes;
    - i18n, specs, CI and the README ≈ 0.2k.
    These are net lines added plus removed per repo, without built assets. In deep-reasoning, TASK-64's and TASK-66's
    commits are subtracted, which is approximate where they edit the same files [run].

---

## 3 · Proof and measured results

### 3.1 CI at `b283be2`, all green [CI]

| Run | What | Result |
|---|---|---|
| `ci` 39220648479 | ruff, the default suite, canvas-app (typecheck, format, vitest, build equal to the commit), the browser suite | 908 passed; browser 86 passed |
| `cross-repo` 39220656317, `live: false` | pins, bridge-replay, canvas-replay, desktop-e2e, built with Canvas `1a9e3c6` and SDK `1f1a381` through the override | bridge-replay 13 passed, the title test included; canvas-replay 12 passed (the ten recordings plus two guards); E12 25 passed in 444 s |
| `cross-repo` 39221995995, `live: true` | the same, and the live tier | E12 25 passed; live 1 passed in 79.6 s |

E12's 25 steps are §7.4's 20, §13's title step, TASK-64's host check (twice, ingress and frontend) and TASK-66's two
(`…automation_backend_answers…`, `…relaunches_offline_an_hour_after…`).

### 3.2 The live tier: paid, attributed, not re-run

The conditions:
- the Linux runner, with the installed `.deb` and a fresh HOME;
- `OPENAI_API_KEY` only in the step's environment, and saved as a Canvas secret;
- the starter Library's gpt-6-luna through the key proxy, with the keyless `gpt-5-5` LLM profile active;
- one question: "Use one sub-agent to add 2 and 2, then answer with its result."

There is no baseline arm: the old pins have no live tier. To reproduce:
`gh workflow run cross-repo.yml --ref ux-round -f live=true -f canvas_commit=<40 hex> -f sdk_commit=<40 hex>`.

| Run | `ux-round` | Canvas | Live | What it showed | Next |
|---|---|---|---|---|---|
| 39205387269 | `0955bc2` | `dd7bff9` | failed, 127 s | answered; the title was not the question's first 50 characters within 60 s | `2ba0bc8`: the SDK's 47 + "..." rule |
| 39207605784 | `2ba0bc8` | `dd7bff9` | failed, 336 s | no agent message containing "4" within 300 s | `7995d53` changed the check, not a cause |
| 39210357389 | `7995d53` | `dd7bff9` | failed, 148 s | answered '4', with the title and no error event; one sub-agent with no cost shown | `6d31d2c`: root cause found, below |
| 39213080236 | `6d31d2c` | `dd7bff9` | passed, 143 s | one sub-agent, with its cost shown; canvas-replay red on C1's replay race | TASK-41's fix joined the integration |
| 39221995995 | `b283be2` | `1a9e3c6` | passed, 80 s | answered '4'; one sub-agent ("Add 2 and 2.") with its cost shown | — |

All five used SDK `1f1a381`, and `dd7bff9` is the earlier integration (agent-lock and costs only). That is five paid
runs, three of them failed. I found no spend figure in their logs.

**The third run's root cause.** GitHub's runner sets `XDG_CONFIG_HOME`, so the live app shared E12's Electron profile,
in which E12 step 11 had turned costs off [impl, consistent with the log].

**The second run was never root-caused.** The test then waited only for an agent message containing "4", and printed
nothing else. The workflow's failure artifact covers E12's app log, not the live tier's (`live*/app.log`, by design),
so nothing of that app survives [CI]. These are not ruled out:
- the model's wording (no "4");
- a slow model past 300 s;
- the shared Electron profile found in run 3.

The current test fails naming the run log's events and the window's messages, so a repeat would say which.

### 3.3 The one A/B: the title test (`tests/crossrepo/test_title.py`)

| | SDK `dr-2` `34c540c` | SDK `1f1a381` |
|---|---|---|
| A keyless `gpt-5-5` profile, active and sent as `title_llm_profile` | fails: `api.openai.com:443` attempted three times, no title [impl]; the designer saw four attempts in 100 s (F4) | passes: no outbound attempt, title "What is 2 + 2?" within 30 s, no `ConversationErrorEvent` [CI, bridge-replay in both runs] |

### 3.4 The forks' own CI

- **The full Mock-LLM E2E suite** (85 tests) is red on both the `dr-3` baseline and the agent-lock branch [CI]:
  - `dr-3` `4355a36`, run 39199074579;
  - `feat/agent-lock` `ee7a150`, run 39197309566.

  The same ten tests fail in both: automation lifecycle step 2, preset automation, conversation step 3, image upload,
  message confirmation ×2, files and git step 2, onboarding happy path, the `/model` switch, and same-model profile
  identity. Both end on the 20-minute global timeout (exit 124). So `feat/agent-lock` adds no Mock-LLM failure over
  `dr-3`. The suite runs unlocked, and nothing runs it locked.
- **`fix/subagent-costs-on-by-default` `6df1472`**, run 39198761231: the sub-agents spec, Live 2 included, 5 passed
  [CI].
- **No other fork workflow ran on these four branches.**

### 3.5 Run here, at `b283be2`, with no model calls [run]

- `tests/acp/test_route.py`, `test_texts.py`, `test_session.py` and `test_agent.py` (all but the golden recordings);
  `tests/app/test_texts.py`, `test_cli.py` and `test_runtime.py`; `tests/test_names.py`; `tests/desktop/test_build.py`,
  `test_readme.py` and `test_app.py`; `tests/library` and `tests/tools` `test_texts.py`; and
  `tests/canvas_app/test_panel_icon.py`: 175 passed, every test in those files but the golden recordings.
- `canvas-app`'s vitest: 251 passed, 2 skipped.
- Probes of `FORK_NULL_KEYS` over `dr-3`, `feat/agent-lock` and `1a9e3c6`'s `defaults.json`, of `patch_defaults`' two
  keys and of `with_commits` (§0, §1.4).
- Four golden recordings (`failing` and `unanswered`, native and flat) fail in this sandbox at `b283be2` and at `main`
  `9e8109e` alike, and pass in CI. That is this sandbox, not the round.

---

## 4 · Seams and the release chain

### 4.1 What this round shares

- **TASK-64** (`3531384`, on `ux-round`): E12's host-check step and `get_with_host` in `tests/desktop/app.py`. It
  carries no xfail mark, which is TASK-64's own divergence.
- **TASK-66** (`c361467` and `b0fff97`): `uv.excludeNewer` is the fifth `FORK_NULL_KEYS` key, and `patch_defaults`
  gains `exclude_newer`. It also adds `pins.toml` `app.uv_exclude_newer`, validated by `load_pins`; `canvas-replay`'s
  installs at the cutoff; and E12's two steps.
- **TASK-41** (`fix/replay-spec-settles`) is only in `ux-round-integration`.
- **TASK-48** (design §9): its `prepare()` must pass `app_title` and `exclude_newer` to `patch_defaults`. Both are
  required keywords, so a call without them fails.
- **One hand-resolved conflict** [run, `git show --remerge-diff`]. `fix/subagent-costs-on-by-default`
  (`hideSubagentCosts`) and TASK-41's `1d6ea20` (`expectRenderedTreeToMatchStored`) each add an import to the same list
  in `tests/e2e/mock-llm/conversations/mock-llm-acp-subagents.spec.ts`. The integration keeps both. `dr-4`'s merge
  meets the same hunk; every other merge is clean.

### 4.2 The release chain

1. **SDK `dr-3`** is TASK-46's branch plus TASK-69's fix. Michael pushes the tag, and `dr-release.yml` publishes the
   TypeScript client.
2. **Canvas `dr-4`** is this round's three branches, TASK-64's, TASK-66's and TASK-41's, and then the wiring commit:
   `sources.agentServerGitRef` and `@openhands/typescript-client` moved to `dr-3`.
   - Michael tags it at or after the wiring merge.
   - Checks 2 and 3 refuse a Canvas wired to another SDK commit or client [read; tests [run]], and check 5b/5c refuses
     one without the round's keys [run].
3. **On `ux-round`**, one commit moves both pins in `desktop/pins.toml`, and
   `test_the_committed_sdk_pin_is_34c540c_tagged_dr_2` is renamed with it. `cross-repo.yml` must then be green there,
   with one live dispatch (design §8).

---

## 5 · What nobody ran, or I could not verify

- **The Canvas unit tests, lint and builds of `feat/agent-lock` and `fix/subagent-costs-on-by-default`: no result I
  could read.** The commit messages carry none. The TASK-65 row's note is cut at Notion's 2000 characters, and TASK-50's
  row is still at `Spec`, with no note on the build. Only `feat/app-title` has one: "local lint, 8,400 tests, both
  builds green; trial merge with feat/agent-lock clean" [impl]. `desktop-e2e`'s `npm run build:app` compiles the
  integration [CI]. I did not install the fork to run vitest.
- **The SDK's own unit tests: no result I could read.** The commit messages carry none. The run evidence for TASK-46 is
  the cross-repo title test, E12 step 7 and the live tier [CI], and the task row's "red on dr-2, green on 1f1a381"
  [impl].
- **macOS: nothing in this round ran there.** `desktop-e2e` is Linux. That the macOS window shows the title rests on
  §13's reading of `electron/main.mjs` [read].
- **An install from before this round** (Michael's VM) is read only:
  - the active pointer naming another profile is overruled by the lock;
  - an automation naming another profile keeps it until it is next saved;
  - a saved `"true"` or `"false"` cost setting stands;
  - a stored panel acknowledgement `1` is left unread;
  - the Library App's changed digest makes the next launch reinstall and re-approve it once (§4.4).
- **The shared conversation page's title** is covered by vitest [impl] and by no E12 step.

**For the Refactorer and the PR split** [read]:
- The fork's `.agents/skills/local-stack-runtime/references/guide.md` lists the null-upstream keys a build sets. It
  names `uv.excludeNewer` but neither `agent.lockedProfile` nor `branding.appTitle`.
- None of the three Canvas branches touches `.agents/skills/`, although the fork's `AGENTS.md` asks that the owning
  skill be updated when an invariant changes.
- `as_built/` is excluded from the sdist, as earlier as-builts are.
